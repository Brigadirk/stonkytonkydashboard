import { chromium } from '../../../web/node_modules/@playwright/test/index.mjs';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root=fileURLToPath(new URL('../../../',import.meta.url));
const report=JSON.parse(fs.readFileSync(path.join(root,'data/market/estimator_comparison_report.json')));
const group=report.groups.find(g=>g.symbol==='NVDA'&&g.window_days===365&&g.current_contributors.length===2);
assert(group,'Expected the source-reviewed NVIDIA group');
assert.equal(group.reference_sessions_with_multiple_firms,56);
assert.equal(group.first_multi_firm_reference_date,'2026-06-18');
const archive=`data/deliveries/${new Date().toISOString().replaceAll(':','').replaceAll('.','-')}-estimator-round11`;
fs.mkdirSync(path.join(root,archive),{recursive:true});
const browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1500,height:1000}});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
  await page.goto(group.local_view_url);
  await page.getByTestId('simple-target').waitFor();
  assert.equal(await page.locator('.target-level').count(),7);
  const target=await page.getByTestId('simple-target').innerText();
  assert.equal(target,new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(group.median_target)+' USD');
  await page.getByTestId('chart-price').waitFor();
  await page.waitForFunction(()=>document.querySelector('[data-testid="chart-price"]')?.data?.some(t=>t.name==='All 12-month targets'));
  await page.screenshot({path:path.join(root,archive,'nvidia-combined-simple.png'),fullPage:true});
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  await page.getByRole('heading',{name:'Combined estimate contributors',exact:true}).waitFor();
  const stats=await page.locator('.ensemble-stats').innerText();
  const audit=await page.locator('.ensemble-audit').innerText();
  assert.match(audit,/Bernstein/);assert.match(audit,/Morningstar/);
  assert.match(await page.locator('.ensemble-stats>div').first().innerText(),/2/);
  await page.screenshot({path:path.join(root,archive,'nvidia-combined-advanced.png'),fullPage:true});
  const exported=page.waitForEvent('download');
  await page.getByRole('button',{name:'Export contributors and exclusions'}).click();
  const download=await exported;
  await download.saveAs(path.join(root,archive,'nvidia-contributors.csv'));
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>document.documentElement.scrollWidth===390);
  await page.screenshot({path:path.join(root,archive,'nvidia-combined-mobile-advanced.png'),fullPage:true});
  await page.getByRole('button',{name:'Simple view',exact:true}).click();
  assert.equal(await page.locator('.target-level').count(),7);
  assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
  await page.screenshot({path:path.join(root,archive,'nvidia-combined-mobile.png'),fullPage:true});
  const before=new URL(group.local_view_url);before.searchParams.set('asOf','2026-06-17');
  await page.goto(before.toString());
  await page.getByRole('button',{name:'Advanced',exact:true}).click();
  assert.match(await page.locator('.ensemble-stats>div').first().innerText(),/1/);
  await page.screenshot({path:path.join(root,archive,'nvidia-before-bernstein.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  const review={generated_at:new Date().toISOString(),archive_path:archive,bundle_sha256:report.bundle_sha256,
    real_contributors:['Morningstar','Bernstein'],current_contributor_count:2,prior_date:'2026-06-17',prior_contributor_count:1,
    first_multi_firm_date:group.first_multi_firm_reference_date,multi_firm_reference_sessions:56,
    total_reference_sessions:251,median_target:group.median_target,displayed_target:target,
    target_date:group.target,seven_target_cards:true,mobile_width:390,mobile_horizontal_overflow:false,
    base_font_px:16,source_ages_basis:'At origin close; unknown numerical model dates use report age explicitly',
    stats,page_errors:errors};
  for(const name of ['data/market/estimator_browser_review.json',`${archive}/estimator_browser_review.json`])
    fs.writeFileSync(path.join(root,name),JSON.stringify(review,null,2)+'\n');
  console.log(JSON.stringify(review));
} finally {await browser.close();}
