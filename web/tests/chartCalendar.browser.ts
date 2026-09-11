import {test,expect,type Locator,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';

const dataset=JSON.parse(readFileSync(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
async function axisAudit(chart:Locator){
  return chart.evaluate(el=>{
    const plot=el as unknown as {
      data:{name:string;x:string[];y:(number|null)[];customdata:(number|null)[][]}[];
      layout:{xaxis:{rangebreaks:{values:string[];dvalue:number}[]}};
      _fullLayout:{xaxis:{_length:number;range:string[];p2d:(p:number)=>string;d2p:(date:string)=>number}};
    };
    const a=plot._fullLayout.xaxis,actual=plot.data.find(t=>t.name==='Share price')!;
    const observed=new Set(actual.x),last=actual.x.at(-1)!;
    const invalid=new Set<string>(),box=el.getBoundingClientRect();
    const axes=(el as unknown as {_fullLayout:{xaxis:{_offset:number};yaxis:{_offset:number}}})._fullLayout;
    for(let x=.1;x<a._length;x+=7.3){
      const date=a.p2d(x).slice(0,10);
      if(date>=actual.x[0]&&date<=last){
        el.dispatchEvent(new PointerEvent('pointermove',{clientX:box.left+axes.xaxis._offset+x,clientY:box.top+axes.yaxis._offset+30}));
        const shown=el.parentElement!.querySelector<HTMLDivElement>('.chart-cursor-value')!.dataset.date;
        if(!shown||!observed.has(shown))invalid.add(shown||'Missing cursor');
      }
    }
    const positions=actual.x.map(d=>a.d2p(d));
    const steps=positions.slice(1).map((x,i)=>x-positions[i]);
    const targets=plot.data.find(t=>t.name==='All 12-month targets')!;
    return {dates:actual.x,prices:actual.y,missing:plot.layout.xaxis.rangebreaks.flatMap(b=>b.values),invalidCursorDates:[...invalid],minStep:Math.min(...steps),maxStep:Math.max(...steps),range:a.range,width:a._length,targets:{x:targets.x,y:targets.y}};
  });
}
async function moveToFraction(page:Page,chart:Locator,fraction:number){
  await chart.scrollIntoViewIfNeeded();
  const at=await chart.evaluate((el,fraction)=>{
    const box=el.getBoundingClientRect();
    const axes=(el as unknown as {_fullLayout:{xaxis:{_offset:number;_length:number;p2d:(p:number)=>string};yaxis:{_offset:number}}})._fullLayout;
    const pixel=axes.xaxis._length*fraction;
    const raw=axes.xaxis.p2d(pixel).slice(0,10);
    const dates=(el as unknown as {data:{name:string;x:string[]}[]}).data.find(t=>t.name==='Share price')!.x;
    const date=raw<=dates.at(-1)!?dates.find(d=>d>=raw)!:raw;
    return {x:box.left+axes.xaxis._offset+pixel,y:box.top+axes.yaxis._offset+30,date};
  },fraction);
  await page.mouse.move(at.x,at.y);
  await expect(chart.locator('..').locator('.chart-cursor-date')).toHaveAttribute('datetime',at.date);
  return at.date;
}

test('each listing skips every missing historical close and preserves calendar-based forecasts after zoom and resize',async({page})=>{
  await page.setViewportSize({width:1500,height:1100});
  for(const companyId of ['nvidia','sk_hynix','asml']){
    await page.goto(`/?company=${companyId}&window=90&display=1826`);
    const chart=page.getByTestId('chart-price');
    await chart.locator('.main-svg').first().waitFor();
    const state=await axisAudit(chart),company=dataset.companies.find((c:{id:string})=>c.id===companyId);
    const retained=company.prices.filter((p:{date:string})=>p.date>=state.dates[0]);
    expect(state.dates).toEqual(retained.map((p:{date:string})=>p.date));
    expect(state.prices).toEqual(retained.map((p:{close:number})=>p.close));
    expect(state.missing.length).toBeGreaterThan(500);
    expect(state.invalidCursorDates).toEqual([]);
    // Plotly rounds data-to-pixel output to hundredths of a pixel.
    expect(state.maxStep-state.minStep).toBeLessThan(.011);
    expect(state.missing.every(d=>d<state.dates.at(-1)!&&!state.dates.includes(d))).toBe(true);
    const date=await moveToFraction(page,chart,.3);
    expect(state.dates).toContain(date);
    await expect(chart.locator('..').locator('.chart-cursor-value')).toContainText('Close ·');
    await expect(chart.locator('..').locator('.chart-cursor-value')).toContainText('Forward P/E');
    await page.getByRole('button',{name:'Advanced',exact:true}).click();
    await expect.poll(()=>page.getByTestId('chart-earnings').evaluate(el=>(el as unknown as {layout?:{xaxis:{rangebreaks:{values:string[]}[]}}}).layout?.xaxis.rangebreaks.flatMap(b=>b.values))).toEqual(state.missing);
    await page.getByRole('button',{name:'Simple view',exact:true}).click();
    await chart.scrollIntoViewIfNeeded();
    const box=await chart.boundingBox();
    await page.mouse.move(box!.x+box!.width*.2,box!.y+180);await page.mouse.down();
    await page.mouse.move(box!.x+box!.width*.8,box!.y+400,{steps:10});await page.mouse.up();
    await expect.poll(async()=>(await axisAudit(chart)).range).not.toEqual(state.range);
    expect((await axisAudit(chart)).invalidCursorDates).toEqual([]);
    await moveToFraction(page,chart,.4);
    await page.setViewportSize({width:1100,height:950});
    await expect.poll(async()=>(await axisAudit(chart)).width).toBeLessThan(state.width);
    expect((await axisAudit(chart)).invalidCursorDates).toEqual([]);
    expect((await axisAudit(chart)).targets).toEqual(state.targets);
    await moveToFraction(page,chart,.6);
    await page.setViewportSize({width:1500,height:1100});
  }
});

test('touch cursor crosses a removed weekend directly to the next recorded close',async({browser})=>{
  const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  try{
    await page.goto('/?company=nvidia&window=90&display=180');
    const chart=page.getByTestId('chart-price');await chart.locator('.main-svg').first().waitFor();
    for(const date of ['2026-09-04','2026-09-08','2026-09-12']){
      await chart.scrollIntoViewIfNeeded();
      // Avoid invoking Plotly's separate double-tap zoom gesture.
      await page.waitForTimeout(450);
      const at=await chart.evaluate((el,date)=>{
        const box=el.getBoundingClientRect();
        const axes=(el as unknown as {_fullLayout:{xaxis:{_offset:number;d2p:(date:string)=>number};yaxis:{_offset:number}}})._fullLayout;
        return {x:box.left+axes.xaxis._offset+axes.xaxis.d2p(date+' 12:00:00'),y:box.top+axes.yaxis._offset+30};
      },date);
      await page.touchscreen.tap(at.x,at.y);
      const frame=chart.locator('..');
      await expect(frame.locator('.chart-cursor-date')).toHaveAttribute('datetime',date);
      await expect(frame.locator('.chart-cursor-value')).toHaveAttribute('data-kind',date==='2026-09-12'?'scenario':'close');
      await expect(frame.locator('.chart-cursor-value')).toContainText('Forward P/E');
    }
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(390);
  }finally{await page.close();}
});
