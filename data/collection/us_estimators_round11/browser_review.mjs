// Repeat ordinary public-page review; no signed-in session or access-control changes.
import { chromium } from '../../../web/node_modules/@playwright/test/index.mjs';
import fs from 'node:fs';
import path from 'node:path';

const destination = process.argv[2];
if (!destination) throw new Error('Pass a fresh output directory.');
fs.mkdirSync(destination, { recursive: false });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1800, height: 1300 }, deviceScaleFactor: 2 });
try {
  await page.goto('https://www.scribd.com/document/1072698702/Bernstein-Global-Semiconductors-Global-Semis-the-CPU-Renaissance-Beneficiaries-of-a-223bn-TAM-260617', { waitUntil: 'domcontentloaded' });
  const reject = page.getByRole('button', { name: 'Reject Non-Essential', exact: true });
  if (await reject.count()) await reject.click();
  for (const n of [1, 32, 35]) {
    const documentPage = page.locator('#outer_page_' + n);
    await documentPage.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await documentPage.screenshot({ path: path.join(destination, 'page' + n + '.png') });
    fs.writeFileSync(path.join(destination, 'page' + n + '.txt'), await documentPage.innerText());
  }
} finally {
  await browser.close();
}
