// Recover the two reviewed public reports without subscription or form submission.
// Existing sources are immutable. Changed download bytes are saved as candidates
// and require another source review, including publisher-added metadata/pages.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {chromium} from '../../../web/node_modules/@playwright/test/index.mjs';

const base=path.dirname(fileURLToPath(import.meta.url));
const sources=JSON.parse(await fs.readFile(path.join(base,'source_recipe.json'),'utf8'));
const logs=[];
let browser;
try {
  for(const source of sources){
    const target=path.join(base,source.local_file);
    let bytes;
    try { bytes=await fs.readFile(target); } catch(error){if(error.code!=='ENOENT')throw error;}
    if(bytes){
      if(createHash('sha256').update(bytes).digest('hex')!==source.sha256)throw Error(`Retained source hash mismatch: ${source.report_id}`);
      logs.push({report_id:source.report_id,status:'retained_hash_verified'});
      continue;
    }
    await fs.mkdir(path.dirname(target),{recursive:true});
    const candidate=target+'.candidate';
    if(source.download_method==='public_browser_download_button'){
      browser ||= await chromium.launch({headless:true});
      const page=await browser.newPage();
      await page.goto(source.source_url,{waitUntil:'networkidle',timeout:45000});
      const pending=page.waitForEvent('download',{timeout:20000});
      await page.getByTitle('Download',{exact:true}).click();
      const download=await pending;
      await download.saveAs(candidate);
      await page.close();
      bytes=await fs.readFile(candidate);
    }else{
      const response=await fetch(source.source_url,{signal:AbortSignal.timeout(45000)});
      if(!response.ok)throw Error(`Public source HTTP${response.status}: ${source.report_id}`);
      bytes=Buffer.from(await response.arrayBuffer());
      await fs.writeFile(candidate,bytes);
    }
    const sha256=createHash('sha256').update(bytes).digest('hex');
    logs.push({report_id:source.report_id,source_url:source.source_url,retrieved_at:new Date().toISOString(),sha256,status:sha256===source.sha256?'restored_exact_original':'candidate_hash_changed_requires_review'});
    if(sha256!==source.sha256)throw Error(`New delivery bytes require review: ${candidate}`);
    await fs.rename(candidate,target);
  }
}finally{
  await browser?.close();
  await fs.writeFile(path.join(base,'reproduction_download_log.json'),JSON.stringify(logs,null,2)+'\n');
}
console.log(JSON.stringify(logs));
