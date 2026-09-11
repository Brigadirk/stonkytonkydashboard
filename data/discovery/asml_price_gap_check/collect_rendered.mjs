import {chromium} from '../../../web/node_modules/@playwright/test/index.mjs';
import fs from 'node:fs';import crypto from 'node:crypto';
const company=process.argv[2]||'asml',isin={asml:'NL0010273215',besi:'NL0012866412'}[company];
if(!isin)throw new Error('Expected asml or besi');
const directory=new URL('./',import.meta.url),url=`https://live.euronext.com/fr/product/equities/${isin}-XAMS`;
const browser=await chromium.launch(),page=await browser.newPage();
try {
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:30000});
 await page.locator('#awl-historical-price-container table').waitFor({timeout:25000});
 const html=await page.locator('#awl-historical-price-container').evaluate(el=>el.outerHTML),sha=crypto.createHash('sha256').update(html).digest('hex');
 fs.writeFileSync(new URL(`${sha}.html`,directory),html);
 const record={url,source_file:`data/discovery/asml_price_gap_check/${sha}.html`,sha256:sha,retrieved_at:new Date().toISOString(),extraction:'Original exchange page DOM after its own public JavaScript renders the historical daily table. Raw AJAX responses retained separately; these are encrypted transport and are not parsed as plaintext.'};
 fs.writeFileSync(new URL(company==='asml'?'rendered_source.json':'besi_rendered_source.json',directory),JSON.stringify(record,null,2));
 console.log(JSON.stringify(record));
 console.log(await page.locator('#awl-historical-price-container table').innerText());
} finally {await browser.close()}
