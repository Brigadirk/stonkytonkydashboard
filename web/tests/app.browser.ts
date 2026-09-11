import { test, expect } from '@playwright/test';
test('ten-stock workspace, bands, date controls, strict gaps and exports',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByRole('heading',{name:'SK hynix.'})).toBeVisible();
  await expect(page.locator('nav[aria-label="Company selection"] button')).toHaveCount(10);
  await expect(page.locator('[data-testid="chart-price"] .main-svg').first()).toBeVisible();
  const bandBox=page.getByLabel('±1.5σ',{exact:true});
  await bandBox.uncheck();await expect(bandBox).not.toBeChecked();await bandBox.check();
  await page.getByRole('button',{name:'180D',exact:true}).click();
  await expect(page.getByLabel('Window in days')).toHaveValue('180');
  await page.getByLabel('Window in days').fill('270');
  await expect(page.getByRole('heading',{name:'Share price & implied valuation bands'})).toBeVisible();
  await expect(page.getByRole('button',{name:'P/E',exact:true})).toHaveCount(0);
  await expect(page.locator('[data-testid="chart-price"] .main-svg').first()).toBeVisible();
  await page.getByLabel('As of date').fill('2025-06-30');
  await expect(page.getByLabel('As of date')).toHaveValue('2025-06-30');
  await page.getByText('Calculation settings', {exact:true}).click();
  await page.getByLabel('Require verified availability').check();
  await expect(page.getByText('Verified availability only.',{exact:false})).toBeVisible();
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export chart data'}).click();
  expect((await download).suggestedFilename()).toContain('270d');
  await page.getByRole('tab',{name:'Forecast archive'}).click();
  await expect(page.getByRole('heading',{name:'Original forecast models'})).toBeVisible();
  await page.getByRole('tab',{name:'Forecast vs. actual'}).click();
  await expect(page.getByRole('heading',{name:'Forecasts compared with results',exact:true})).toBeVisible();
  await page.getByRole('tab',{name:'Data coverage'}).click();
  await expect(page.locator('.gap-table tbody tr')).toHaveCount(10);
  await expect(page.getByRole('heading',{name:'Backtest readiness'})).toBeVisible();
  const readinessDownload=page.waitForEvent('download');
  await page.getByRole('button',{name:'Export every series'}).click();
  expect((await readinessDownload).suggestedFilename()).toBe('backtest-readiness.json');
  for(const symbol of ['AVGO','GOOGL','NVDA','005930','MU','SNDK','ASML','AAPL','BESI']) {
    await page.locator('nav button').filter({has:page.locator('.stock-symbol',{hasText:new RegExp(`^${symbol}$`)})}).click();
    await expect(page.locator('[data-testid="chart-price"] .main-svg').first()).toBeVisible();
  }
  await page.getByLabel('As of date').fill('2026-09-10');
  await page.getByText('Calculation settings', {exact:true}).click();
  await page.getByLabel('Require verified availability').uncheck();
  for(const symbol of ['ASML','SNDK','AAPL']) {
    await page.locator('nav button').filter({has:page.locator('.stock-symbol',{hasText:new RegExp(`^${symbol}$`)})}).click();
    await expect.poll(()=>page.locator('[data-testid="chart-price"]').evaluate(el=>{
      const data=(el as unknown as {data?:{name:string;y:(number|null)[]}[]}).data||[];
      return data.find(trace=>trace.name==='Rolling median')?.y.filter(value=>value!==null).length||0;
    })).toBeGreaterThan(20);
  }
  await page.getByRole('tab',{name:'Data coverage'}).click();
  await page.getByRole('button',{name:/AAPL 2026-08:/}).click();
  await expect(page.locator('.gap-inspector')).toContainText('AAPL');
  const gapDownload=page.waitForEvent('download');
  await page.getByRole('button',{name:'Export gap map'}).click();
  expect((await gapDownload).suggestedFilename()).toBe('monthly-forecast-gaps.csv');
  await page.getByRole('tab',{name:'All stocks'}).click();
  await expect(page.locator('.overview-table tbody tr')).toHaveCount(10);
  await page.locator('.overview-table tbody tr').filter({hasText:'AAPL'}).locator('button').first().click();
  await expect(page.getByRole('heading',{name:'Apple.'})).toBeVisible();
  await expect(page.getByLabel('Window in days')).toHaveValue('270');
  await page.getByRole('tab',{name:'Forecast vs. actual'}).click();
  await expect(page.getByRole('heading',{name:'Annual EPS forecasts compared with results'})).toBeVisible();
  await expect(page.locator('.eps-evaluation .archive-summary')).toContainText('comparable pairs for Apple');
  expect(errors).toEqual([]);
});
test('mobile layout stays inside viewport and settings survive reload',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/?company=broadcom&window=730&metric=multiple');
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Broadcom.'})).toBeVisible();
  await expect(page.getByLabel('Window in days')).toHaveValue('730');
  await page.reload();await page.getByRole('button',{name:'Advanced',exact:true}).click();await expect(page.getByLabel('Window in days')).toHaveValue('730');
  await expect(page.locator('[data-testid="chart-price"] .main-svg').first()).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  for(const tab of ['Data coverage','All stocks','Forecast vs. actual']) {
    await page.getByRole('tab',{name:tab}).click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  }
});

test('BESI opens its EUR valuation bands and exports dated forecasts',async({page})=>{
  await page.goto('/?company=besi&window=365&asOf=2026-09-10');
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await expect(page.getByRole('heading',{name:'BE Semiconductor Industries.'})).toBeVisible();
  await expect(page.locator('.price-heading')).toContainText('EUR');
  await expect.poll(()=>page.locator('[data-testid="chart-price"]').evaluate(el=>{
    const data=(el as unknown as {data?:{name:string;y:(number|null)[]}[]}).data||[];
    return data.find(trace=>trace.name==='Rolling median')?.y.filter(value=>value!==null).length||0;
  })).toBeGreaterThan(20);
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Export chart data'}).click();
  expect((await download).suggestedFilename()).toContain('BESI-');
  await page.getByRole('tab',{name:'Forecast archive'}).click();
  await expect(page.locator('.archive-summary')).not.toContainText('No eligible series');
  await expect(page.locator('.tab-card tbody tr').first()).toContainText('EUR');
});
