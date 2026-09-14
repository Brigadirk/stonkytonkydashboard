import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

// Use the frozen first collection, so future dashboard refreshes do not change
// the dates and values used to exercise chart controls and missing-data states.
const fixture = JSON.parse(readFileSync(new URL('./fixtures/ornn/2026-09-14T10-14-34-988Z-0e4464cb/manifest.json', import.meta.url), 'utf8'));

test.beforeEach(async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-09-14T12:00:00Z'));
  await page.route('**/data/gpu-prices.json', route => route.fulfill({ json: fixture }));
});

test('GPU prices show exact weekly changes, filter charts and export data', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto('/?view=gpu');
  await expect(page.getByRole('tab', { name: 'GPU prices' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.locator('.gpu-price-card')).toHaveCount(5);
  await expect(page.getByRole('button', { name: 'Compare A100 SXM4', exact: true })).toContainText('$0.990');
  await expect(page.getByRole('button', { name: 'Compare A100 SXM4', exact: true })).toContainText('-6.6%');
  await expect.poll(() => page.getByTestId('gpu-chart').evaluate(el => (el as unknown as { data?: unknown[] }).data?.length)).toBe(5);
  await page.getByRole('button', { name: 'Older GPUs only', exact: true }).click();
  await expect.poll(() => page.getByTestId('gpu-chart').evaluate(el => (el as unknown as { data: { name: string }[] }).data.map(trace => trace.name))).toEqual(['A100 SXM4', 'H100 SXM']);
  await page.getByRole('button', { name: 'Weekly change', exact: true }).click();
  await expect.poll(() => page.getByTestId('gpu-chart').evaluate(el => {
    const trace = (el as unknown as { data: { type: string; x: string[]; y: number[] }[] }).data[0];
    return { type: trace.type, end: trace.x.at(-1), change: trace.y.at(-1)?.toFixed(1) };
  })).toEqual({ type: 'bar', end: '2026-09-11', change: '-6.6' });
  await page.getByRole('button', { name: '4 weeks', exact: true }).click();
  await expect.poll(() => page.getByTestId('gpu-chart').evaluate(el => (el as unknown as { data: { x: string[] }[] }).data[0].x.length)).toBe(4);
  await page.getByLabel('GPU week ending').selectOption('2026-09-04');
  await expect(page.getByRole('button', { name: 'Compare A100 SXM4', exact: true })).toContainText('$1.060');
  await page.getByRole('button', { name: 'View week ending 11 Sept 2026' }).click();
  await expect(page.getByLabel('GPU week ending')).toHaveValue('2026-09-11');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export weekly CSV' }).click();
  expect((await downloadPromise).suggestedFilename()).toBe('ornn-gpu-weekly-2026-09-11.csv');
  await page.getByRole('button', { name: 'Advanced', exact: true }).click();
  await page.getByRole('button', { name: 'Simple view', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'GPU prices' })).toHaveAttribute('aria-selected', 'true');
  await page.getByRole('tab', { name: 'This stock', exact: true }).click();
  await expect(page.getByTestId('simple-stock')).toBeVisible();
  await expect(page).not.toHaveURL(/view=gpu/);
  expect(errors).toEqual([]);
});

test('GPU charts fit a narrow screen and expose source details', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/?view=gpu');
  await expect(page.getByTestId('gpu-chart')).toBeVisible();
  await expect.poll(() => page.getByTestId('gpu-chart').evaluate(el => Math.abs(((el as unknown as { _fullLayout?: { width: number } })._fullLayout?.width || 0) - el.clientWidth))).toBeLessThan(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await page.getByRole('button', { name: 'About H200', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('heading', { name: 'H200.' })).toBeVisible();
  await expect(dialog).toContainText('2023');
  await expect(dialog).toContainText('second quarter of 2024');
  expect(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await dialog.getByRole('button', { name: 'Back to prices' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'About H200', exact: true })).toBeFocused();
  await page.locator('#gpu-data-method summary').click();
  await expect(page.getByRole('link', { name: 'A100 SXM4 history' })).toHaveAttribute('href', 'https://api.ornnai.com/api/gpu/A100%20SXM4/index-history');
  await expect(page.getByText('This view uses a saved dataset', { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('every model has a sourced profile and closing it preserves chart selection', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto('/?view=gpu');
  for (const [gpu, year] of [['A100 SXM4', '2020'], ['H100 SXM', '2022'], ['H200', '2023'], ['B200', '2024'], ['RTX 5090', '2025']]) {
    const opener = page.getByRole('button', { name: `About ${gpu}`, exact: true });
    await opener.click();
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByRole('heading', { name: `${gpu}.`, exact: true })).toBeVisible();
    await expect(dialog.locator('.gpu-profile-facts')).toContainText(year);
    await expect(dialog).toContainText('Hardware retirement date: unknown.');
    await expect(dialog.getByRole('link', { name: 'NVIDIA announcement & model context' })).toHaveAttribute('href', /^https:\/\/nvidianews.nvidia.com\/news\//);
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    await expect(opener).toBeFocused();
    await expect(page.getByRole('button', { name: `Compare ${gpu}`, exact: true })).toHaveAttribute('aria-pressed', 'true');
  }
  expect(errors).toEqual([]);
});

test('missing Friday data stays blank and stale data is marked', async ({ page }) => {
  await page.route('**/data/gpu-prices.json', async route => {
    const data = structuredClone(fixture);
    data.series[0].observations = data.series[0].observations.filter((row: { date: string }) => row.date < '2026-09-11');
    await route.fulfill({ json: data });
  });
  await page.goto('/?view=gpu');
  await expect(page.getByRole('button', { name: 'Compare A100 SXM4' })).toContainText('—');
  await expect(page.getByText('A Friday comparison is missing', { exact: false })).toBeVisible();
  await expect(page.getByText('Saved data is more than three days old', { exact: false })).toBeVisible();
});

test('failed GPU data does not break the stock views', async ({ page }) => {
  await page.route('**/data/gpu-prices.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  await page.goto('/?view=gpu');
  await expect(page.getByRole('heading', { name: 'GPU prices are unavailable' })).toBeVisible();
  await page.getByRole('tab', { name: 'All stocks' }).click();
  await expect(page.locator('.simple-overview')).toBeVisible();
});
