import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('real estimator overlays and combined selection survive reload and export membership',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/?company=besi');
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await page.getByRole('button',{name:'Overlay estimators',exact:true}).click();
  await page.getByRole('button',{name:'Select all estimators',exact:true}).click();
  await expect.poll(()=>page.locator('[data-testid="chart-price"]').evaluate(el=>{
    const traces=(el as unknown as {data?:{name:string}[]}).data||[];
    return traces.filter(t=>t.name.endsWith('Median price')).length;
  })).toBeGreaterThan(1);
  await page.reload();await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByRole('button',{name:'Overlay estimators',exact:true})).toHaveAttribute('aria-pressed','true');
  const overlayDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Export chart data'}).click();
  const overlayCsv=await readFile((await (await overlayDownload).path())!,'utf8');
  expect(overlayCsv).toContain('"overlay"');expect(overlayCsv).toContain('Javier');expect(overlayCsv).toContain('Hildo');
  await page.getByRole('button',{name:'Combined estimates',exact:true}).click();
  await page.getByRole('button',{name:'All compatible estimators',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Combined estimate contributors'})).toBeVisible();
  await page.getByLabel('Combine forecasts using').selectOption('mean');
  await page.reload();await page.getByRole('button',{name:'Advanced',exact:true}).click();await expect(page.getByLabel('Combine forecasts using')).toHaveValue('mean');
  await page.getByRole('button',{name:'Clear selection',exact:true}).click();
  await expect(page.locator('.ensemble-audit')).toContainText('No eligible contributors on this date');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export contributors and exclusions'}).click();
  const csv=await readFile((await (await download).path())!,'utf8');expect(csv).toContain('"excluded"');expect(csv).toContain('Not selected');
  await page.getByRole('button',{name:'All compatible estimators',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.getByText('Choose estimators and inspect compatibility',{exact:true}).click();
  await expect(page.locator('.estimator-list input[disabled]').first()).toBeDisabled();
  expect(errors).toEqual([]);
});

test('multiple compatible test estimators produce a combined forecast and shareable selection',async({page,context})=>{
  // An explicitly labelled test-only second contributor exercises the aggregation
  // UI without admitting fabricated analyst evidence to the production dataset.
  const source=JSON.parse(await readFile(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
  const co=source.companies.find((c:{id:string})=>c.id==='alphabet');
  const original=co.series.find((s:{accounting_basis:string})=>s.accounting_basis==='reported_diluted');
  const second=structuredClone(original);second.id='test-only-second';second.analyst='Test contributor';second.firm='Test firm';second.label='Test contributor · reported diluted EPS';
  for(const snapshot of second.snapshots){snapshot.id+='-test';for(const e of snapshot.estimates)e.eps*=2;}
  co.series.push(second);
  await page.route('**/data/dashboard.json',route=>route.fulfill({json:source}));
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  await page.goto(`/?company=alphabet&series=${original.id}`);
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await page.getByRole('button',{name:'Combined estimates',exact:true}).click();
  await expect(page.locator('.ensemble-stats>div').first()).toContainText('2');
  await expect(page.locator('.ensemble-audit')).toContainText('Test contributor');
  await page.getByLabel('Combine forecasts using').selectOption('mean');
  await expect(page.locator('.ensemble-audit')).toContainText('50%');
  await page.getByRole('button',{name:'Copy view link'}).click();
  const copied=await page.evaluate(()=>navigator.clipboard.readText());
  expect(copied).toContain('mode=ensemble');expect(copied).toContain('combine=mean');
  await page.goto(copied);
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByLabel('Combine forecasts using')).toHaveValue('mean');
  await page.getByText('Calculation settings',{exact:true}).click();
  await page.getByLabel('Require verified availability').check();
  await expect(page.locator('.ensemble-audit')).toContainText('No eligible contributors on this date');
});
