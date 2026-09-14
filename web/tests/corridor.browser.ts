import {test,expect,type Page} from '@playwright/test';
import {readFile} from 'node:fs/promises';

async function cursorAt(page:Page,date:string){
  const chart=page.getByTestId('chart-price');
  await chart.scrollIntoViewIfNeeded();
  const position=await chart.evaluate((el,date)=>{
    const box=el.getBoundingClientRect();
    const a=(el as unknown as {_fullLayout:{xaxis:{_offset:number;d2p:(d:string)=>number};yaxis:{_offset:number}}})._fullLayout;
    return {x:box.left+a.xaxis._offset+a.xaxis.d2p(date+' 12:00:00'),y:box.top+a.yaxis._offset+30};
  },date);
  await page.mouse.move(position.x,position.y);
  const frame=chart.locator('..');
  await expect(frame.locator('.chart-cursor-date')).toHaveAttribute('datetime',date);
  return frame.locator('.chart-cursor-value');
}

test('future bands roll frozen earnings to the dated targets in stock and overview charts',async({page})=>{
  await page.goto('/?company=nvidia&window=90&display=180&targetSigma=2');
  const chart=page.getByTestId('chart-price');
  await expect.poll(()=>chart.evaluate(el=>{
    const plot=el as unknown as {data?:{name:string;mode:string;x:string[];y:(number|null)[];customdata:number[][];connectgaps?:boolean}[];_fullLayout:{height:number}};
    const actual=plot.data?.find(t=>t.name==='Share price');
    if(!actual)return null;
    const curves=plot.data!.filter(t=>t.name.includes(' · Projected '));
    const targets=plot.data!.find(t=>t.name==='All 12-month targets');
    return {height:plot._fullLayout.height,targets:targets?.y.length,curves:curves.length,
      daily:curves.every(t=>t.x.length===366&&t.x[0]===actual.x.at(-1)&&t.x.at(-1)==='2027-09-11'),
      formula:curves.every(t=>t.y.every((v,i)=>v!==null&&Math.abs(v-t.customdata[i][0]*t.customdata[i][1])<1e-8)),
      fixedMultiples:curves.every(t=>new Set(t.customdata.map(v=>v[1])).size===1),
      noMarketAnchor:curves.every(t=>t.y[0]!==actual.y.at(-1)),
      endpointMatch:curves.every((t,i)=>t.y.at(-1)===targets?.y[i]),
      preservesGaps:curves.every(t=>t.connectgaps===false)};
  })).toEqual({height:640,targets:7,curves:7,daily:true,formula:true,fixedMultiples:true,noMarketAnchor:true,endpointMatch:true,preservesGaps:true});
  for(const date of ['2026-09-12','2027-09-11']){
    const value=await cursorAt(page,date);
    await expect(value).toHaveAttribute('data-kind','scenario');
    await expect(value).toContainText(date==='2026-09-12'?'+2σ projected valuation':'+2σ 1-year target');
    await expect(value).toContainText('Forward P/E');
    await expect(value).not.toContainText('Close');
  }
  const target=await page.getByTestId('simple-target').innerText();
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByTestId('projection-panel').locator('.metric strong').nth(1)).toHaveText(target);
  await expect(page.getByText('How the future corridor works',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Export corridor and price evidence'})).toHaveCount(0);
  await page.getByRole('tab',{name:'All stocks',exact:true}).click();
  await expect(page.locator('.mini-corridor')).toHaveCount(23);
  for(const mini of await page.locator('[data-company]:not([data-company="cerebras"]) .mini-corridor').all()){
    expect(await mini.evaluate(el=>{
      const actual=el.querySelector('path[data-actual-through]') as SVGPathElement;
      const end=actual.getPointAtLength(actual.getTotalLength());
      const projected=[...el.querySelectorAll<SVGPathElement>('path[data-projected-sigma]')];
      return projected.length===3&&projected.every(p=>{
        const marker=el.querySelector(`circle[data-sigma="${p.dataset.projectedSigma}"]`);
        if(!p.getAttribute('d')?.trim())return marker===null;
        const start=p.getPointAtLength(0),finish=p.getPointAtLength(p.getTotalLength());
        return marker!==null&&Math.abs(start.x-end.x)<.1&&finish.x>end.x+5;
      })&&el.querySelectorAll('circle[data-target-date]').length>=2;
    })).toBe(true);
  }
});

test('historical cursor shows the close divided by then-available earnings and preserves missing data',async({page})=>{
  await page.goto('/?company=nvidia&window=90&display=1826');
  const chart=page.getByTestId('chart-price');
  await expect.poll(()=>chart.evaluate(el=>(el as unknown as {data?:unknown[]}).data?.length||0)).toBeGreaterThan(1);
  const samples=await chart.evaluate(el=>{
    const actual=(el as unknown as {data:{name:string;x:string[];y:number[];customdata:(number|null)[][]}[]}).data.find(t=>t.name==='Share price')!;
    const latestEps=actual.customdata.at(-1)![0];
    const valid=actual.customdata.findIndex(v=>v[0]!==null&&v[1]!==null&&v[0]!==latestEps);
    const missing=actual.customdata.findIndex(v=>v[1]===null);
    return [valid,missing].map(i=>({date:actual.x[i],price:actual.y[i],eps:actual.customdata[i][0],multiple:actual.customdata[i][1]}));
  });
  expect(samples[0].multiple).toBeCloseTo(samples[0].price/samples[0].eps!,8);
  for(const point of samples){
    const value=await cursorAt(page,point.date);
    const price=new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(point.price);
    await expect(value).toHaveText(`Close · ${price} USD · Forward P/E ${point.multiple===null?'unavailable':point.multiple.toFixed(1)+'×'}`);
  }
  expect(await chart.evaluate(el=>(el as unknown as {layout:{xaxis:{rangebreaks:{values:string[]}[]}}}).layout.xaxis.rangebreaks.flatMap(b=>b.values))).toContain('2026-09-05');
});

test('valuation bands need no daily price prediction or volatility sample',async({page})=>{
  const source=JSON.parse(await readFile(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
  const company=source.companies.find((c:{id:string})=>c.id==='nvidia');
  company.prices=company.prices.slice(-30);
  await page.route('**/data/dashboard.json',route=>route.fulfill({json:source}));
  await page.goto('/?company=nvidia&window=90&display=180');
  await expect(page.getByTestId('simple-target')).not.toContainText('—');
  await expect(page.getByText(/Needs 60 valid close-to-close returns/)).toHaveCount(0);
  await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
    const data=(el as unknown as {data?:{name:string;mode:string;x:string[];y:(number|null)[]}[]}).data;
    const marker=data?.find(t=>t.name.endsWith('12-month selected target'));
    const actual=data?.find(t=>t.name==='Share price');
    return marker&&actual?{targetAvailable:marker.y[0]!>0,hasFutureBands:data!.some(t=>t.name.includes(' · Projected ')&&t.y.every(v=>v!==null)),observedCount:actual.x.length}:null;
  })).toEqual({targetAvailable:true,hasFutureBands:true,observedCount:30});
});
