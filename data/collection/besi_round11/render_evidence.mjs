import { chromium } from '../../../web/node_modules/@playwright/test/index.mjs';
import { fileURLToPath } from 'node:url';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1000, height: 1300 } });
await page.goto(new URL('./evidence/dividendinfo_table.html', import.meta.url).href);
await page.screenshot({ path: fileURLToPath(new URL('./evidence/dividendinfo_table.png', import.meta.url)), fullPage: true });
await browser.close();
