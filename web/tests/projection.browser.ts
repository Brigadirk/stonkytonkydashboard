import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('dated targets use a later earnings horizon while actual quotes stop at origin',async({page})=>{
  await page.goto('/?company=broadcom&window=365&asOf=2026-09-11');
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  const panel=page.getByTestId('projection-panel');
  await expect(panel).toContainText('One year ahead · 2027-09-11');
  await expect(panel).toContainText('2027-09-12 to 2028-09-11');
  await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
    const plot=el as unknown as {data:{name:string;x:string[];y:(number|null)[]}[];layout:{xaxis:{range:string[]}}};
    const actual=plot.data?.find(t=>t.name==='Share price'),future=plot.data?.find(t=>t.name.endsWith('12-month selected target'));
    return actual&&future?{actual:actual.x.at(-1),future:future.x.at(-1),targetAvailable:future.y.at(-1)!>0,extendsBeyondOrigin:plot.layout.xaxis.range[1]>'2027-09-11'}:null;
  })).toEqual({actual:'2026-09-11',future:'2027-09-11',targetAvailable:true,extendsBeyondOrigin:true});
  const median=await panel.locator('.metric strong').nth(1).innerText();
  await page.getByLabel('Target valuation scenario').selectOption('1.5');
  await expect(panel).toContainText('1-YEAR +1.5σ TARGET');
  expect(await panel.locator('.metric strong').nth(1).innerText()).not.toBe(median);
  await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
    const plot=el as unknown as {data:{name:string;x:string[];y:(number|null)[];customdata?:unknown[][]}[]};
    const marker=plot.data?.find(t=>t.name.endsWith('12-month selected target'));
    const targets=plot.data?.find(t=>t.name==='All 12-month targets');
    const now=plot.data?.find(t=>t.name==='Observed close at origin');
    return marker&&targets&&now?{targetDate:marker.x[0],sameAsFutureEndpoint:marker.y[0]===targets.y[5],sigma:marker.customdata?.[0][0],observedDate:now.x[0]}:null;
  })).toEqual({targetDate:'2027-09-11',sameAsFutureEndpoint:true,sigma:1.5,observedDate:'2026-09-11'});
  await page.reload();await page.getByRole('button',{name:'Advanced',exact:true}).click();await expect(page.getByLabel('Target valuation scenario')).toHaveValue('1.5');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export projection data'}).click();
  const csv=await readFile((await (await download).path())!,'utf8');
  expect(csv).toContain('"2027-09-12"');expect(csv).toContain('"12_month_valuation_scenario"');expect(csv).toContain('"origin_price_source_sha256"');
});

test('simple overview keeps one window visible and retains exact controls behind Advanced',async({page})=>{
  // Upgrade an existing user's old comparison preference to the simpler default.
  await page.addInitScript(()=>{if(!localStorage.getItem('forward-settings'))localStorage.setItem('forward-settings',JSON.stringify({compareWindows:true,overviewSort:'upside'}));});
  await page.goto('/?company=broadcom&window=365&asOf=2026-09-11&compareWindows=true&overviewSort=upside');
  await page.getByRole('tab',{name:'All stocks'}).click();
  await expect(page.locator('.projection-overview tbody tr')).toHaveCount(23);
  await expect(page.locator('.mini-corridor')).toHaveCount(23);
  await expect(page.getByLabel('Sort overview')).toBeHidden();
  await expect(page.getByLabel('Target valuation scenario')).toBeHidden();
  const avgo=page.locator('[data-company="broadcom"]');
  await expect(avgo.locator('.target-date').first()).toHaveText('11 Sept 2027');
  const fixedTarget=await avgo.locator('.target-price').innerText(),entryComparisons:string[]=[];
  for(const label of ['90 days','180 days','1 year']){
    await page.getByRole('button',{name:label,exact:true}).click();
    await expect(page.getByRole('button',{name:label,exact:true})).toHaveAttribute('aria-pressed','true');
    await expect(avgo.locator('.target-date').first()).toHaveText('11 Sept 2027');
    await expect(avgo.locator('.target-price')).toHaveText(fixedTarget);
    entryComparisons.push(await avgo.locator('.overview-entry').innerText());
  }
  expect(new Set(entryComparisons).size).toBeGreaterThan(1);
  const baseline=await avgo.locator('.target-price').first().innerText();
  await page.getByRole('button',{name:'High',exact:true}).click();
  expect(await avgo.locator('.target-price').first().innerText()).not.toBe(baseline);
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByLabel('Target valuation scenario')).toHaveValue('2');
  await page.getByLabel('Compare two windows').check();
  await expect(page.locator('.mini-corridor')).toHaveCount(46);
  await page.getByLabel('Second reference window').selectOption('180');
  await expect(avgo.locator('.target-price')).toHaveCount(1);
  await expect(avgo.locator('[data-entry-window="180"]')).toBeVisible();
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export all price scenarios'}).click();
  const csv=await readFile((await (await download).path())!,'utf8');expect(csv.split('\n')).toHaveLength(24);
  await page.getByLabel('Compare two windows').uncheck();
  await page.getByLabel('Sort overview').selectOption('upside');
  await page.reload();await page.getByRole('tab',{name:'All stocks'}).click();
  await expect(page.locator('.mini-corridor')).toHaveCount(23);
  await expect(page.getByRole('button',{name:'High',exact:true})).toHaveAttribute('aria-pressed','true');
  await expect(page.getByLabel('Sort overview')).toBeHidden();
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByLabel('Sort overview')).toHaveValue('upside');
  await avgo.getByRole('button',{name:'Open AVGO target',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Broadcom.'})).toBeVisible();
  await expect(page.getByLabel('Target valuation scenario')).toHaveValue('2');
  await expect(page.getByLabel('Window in days')).toHaveValue('365');
});

test('missing later fiscal years leave explicit target gaps',async({page})=>{
  const source=JSON.parse(await readFile(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
  const co=source.companies.find((c:{id:string})=>c.id==='broadcom');
  // Only this intercepted test dataset is trimmed. Production evidence stays intact.
  for(const s of co.series)for(const m of s.snapshots)m.estimates=m.estimates.filter((e:{fiscal_period_start:string})=>e.fiscal_period_start<'2027-01-01');
  await page.route('**/data/dashboard.json',route=>route.fulfill({json:source}));
  await page.goto('/?company=broadcom&window=365&asOf=2026-09-11');
  await expect(page.getByTestId('simple-target')).toHaveText('— USD');
  await expect(page.locator('.simple-gap')).toContainText('There isn’t enough usable forecast data');
  await expect(page.locator('.target-level-price')).toHaveText(Array(7).fill('—'));
  await expect(page.locator('.target-level-change')).toHaveText(Array(7).fill('Unavailable'));
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  const panel=page.getByTestId('projection-panel');
  await expect(panel).toContainText('Consecutive forward fiscal years are missing');
  await expect(panel.locator('.metric strong').nth(1)).toContainText('—');
  await page.getByText('Projection earnings, models and missing targets',{exact:true}).click();
  await expect(panel).toContainText('Missing 2027-');
  await expect.poll(()=>page.getByTestId('chart-price').evaluate(el=>{
    const traces=(el as unknown as {data?:{name:string;y:(number|null)[]}[]}).data;
    const target=traces?.find(t=>t.name.endsWith('12-month selected target'));
    const actual=traces?.find(t=>t.name==='Observed close at origin');
    return target&&actual?{actualAvailable:actual.y[0]!>0,target:target.y[0]}:null;
  })).toEqual({actualAvailable:true,target:null});
  await page.getByRole('tab',{name:'All stocks'}).click();
  const row=page.locator('[data-company="broadcom"]');
  await expect(row.locator('.target-price').first()).toHaveText('—');
  await expect(row).toContainText('Unavailable');
  await expect(page.locator('.overview-evidence')).toContainText('Consecutive forward fiscal years are missing');
});
