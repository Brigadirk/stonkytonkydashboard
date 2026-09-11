import { test, expect } from '@playwright/test';

test('simple stock keeps all deviation targets in one chart and the same calculation as Advanced',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/?company=broadcom');
  await expect(page.getByTestId('simple-stock')).toBeVisible();
  await expect(page.getByRole('tab')).toHaveCount(2);
  await expect(page.locator('main input, main select')).toHaveCount(1);
  await expect(page.getByLabel('Chart history',{exact:true})).toBeVisible();
  await expect(page.locator('.chart')).toHaveCount(1);
  await expect(page.locator('.simple-stock-controls button')).toHaveCount(3);
  await expect(page.locator('.target-level')).toHaveCount(7);
  await expect(page.getByTestId('simple-current')).toHaveText('364.38 USD');
  await expect(page.getByTestId('simple-target')).toHaveText('819.15 USD');
  for(const level of [-2,-1.5,-1,0,1,1.5,2]){
    const card=page.locator(`.target-level[data-sigma="${level}"]`);
    await card.click();
    await expect(card).toHaveAttribute('aria-pressed','true');
    await expect(page.getByTestId('simple-target')).toHaveText((await card.locator('.target-level-price').innerText())+' USD');
    await expect(page.locator('.target-level')).toHaveCount(7);
    await expect.poll(()=>page.getByTestId('chart-price').evaluate((el,level)=>{
      const data=(el as unknown as {data?:{name:string;y:(number|null)[];marker?:{size:number};customdata?:unknown[][]}[]}).data;
      const marker=data?.find(t=>t.name.endsWith('12-month selected target'));
      const targets=data?.find(t=>t.name==='All 12-month targets');
      return marker&&targets?marker.customdata?.[0][0]===level&&marker.y[0]===targets.y[[-2,-1.5,-1,0,1,1.5,2].indexOf(level)]&&marker.marker!.size>targets.marker!.size:false;
    },level)).toBe(true);
  }
  const fixedTargets=await page.locator('.target-level-price').allTextContents(),entryComparisons:string[]=[];
  for(const window of ['90 days','180 days','1 year']){
    await page.getByRole('button',{name:window,exact:true}).click();
    await expect(page.locator('.simple-price-target')).toContainText('9 Sept 2027');
    const prices=await page.locator('.target-level-price').allTextContents();
    expect(prices).toEqual(fixedTargets);
    entryComparisons.push(await page.getByTestId('entry-comparison').innerText());
    await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
      const plot=el as unknown as {data?:{name:string;x:string[];y:(number|null)[]}[]};
      return plot.data?.find(t=>t.name==='All 12-month targets')?.y.map(v=>v===null?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(v));
    })).toEqual(prices);
  }
  expect(new Set(entryComparisons).size).toBeGreaterThan(1);
  const target=await page.getByTestId('simple-target').innerText();
  await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
    const plot=el as unknown as {data?:{name:string;x:string[];y:(number|null)[];hovertemplate?:string}[]};
    const marker=plot.data?.find(t=>t.name.endsWith('12-month selected target'));
    const targets=plot.data?.find(t=>t.name==='All 12-month targets');
    const actual=plot.data?.find(t=>t.name==='Share price');
    return marker&&targets&&actual?{date:marker.x[0],sameEndpoint:marker.y[0]===targets.y.at(-1),actualEnd:actual.x.at(-1),plainHover:!actual.hovertemplate?.includes('EPS')}:null;
  })).toEqual({date:'2027-09-09',sameEndpoint:true,actualEnd:'2026-09-09',plainHover:true});
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByTestId('projection-panel').locator('.metric strong').nth(1)).toHaveText(target);
  await expect(page.getByLabel('Target valuation scenario')).toHaveValue('2');
  await page.getByRole('tab',{name:'Data coverage'}).click();
  await page.getByRole('button',{name:'Simple view',exact:true}).click();
  await expect(page.getByTestId('simple-target')).toHaveText(target);
  await page.reload();
  await expect(page.getByTestId('simple-target')).toHaveText(target);
  await expect(page.getByRole('button',{name:'Highlight +2σ target',exact:true})).toHaveAttribute('aria-pressed','true');
  await expect(page.getByRole('tab')).toHaveCount(2);
  expect(errors).toEqual([]);
});

test('all ten stocks work in the simple mobile view, including returning from All stocks',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  for(const symbol of ['AVGO','GOOGL','NVDA','000660','005930','MU','SNDK','ASML','AAPL','BESI']){
    await page.locator('nav button').filter({has:page.locator('.stock-symbol',{hasText:new RegExp(`^${symbol}$`)})}).click();
    await expect(page.getByTestId('simple-target')).not.toContainText('—');
    await expect(page.locator('.chart')).toHaveCount(1);
    await expect(page.locator('.target-level')).toHaveCount(7);
    await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
      const plot=el as unknown as {_fullLayout?:{width:number};data?:{name:string;x:string[];y:(number|null)[]}[]};
      const marker=plot.data?.find(t=>t.name.endsWith('12-month selected target'));
      return !!marker&&marker.x[0].startsWith('2027-09-')&&marker.y[0]!>0&&Math.abs((plot._fullLayout?.width||0)-el.clientWidth)<2;
    })).toBe(true);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(390);
  }
  await page.getByRole('tab',{name:'All stocks'}).click();
  await expect(page.locator('.mini-corridor')).toHaveCount(10);
  await expect(page.getByLabel('Target valuation scenario')).toHaveCount(0);
  await page.locator('[data-company="apple"]').getByRole('button',{name:'Open AAPL target',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Apple.'})).toBeVisible();
  await expect(page.getByTestId('simple-stock')).toBeVisible();
  expect(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize)).toBe('16px');
  for(const button of await page.locator('.simple-stock-controls button, .target-level').all())expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  expect(errors).toEqual([]);
});
