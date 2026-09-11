#!/usr/bin/env node
// Reproduce and freeze the displayed paths without fetching or altering inputs.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { bestSeries, shiftDate } from '../web/src/engine.ts';
import { targetReference, projectValuation, projectedPrice } from '../web/src/projection.ts';
import { priceCorridor, corridorPrice, corridorCsv, CORRIDOR_LEVELS, CORRIDOR_METHOD } from '../web/src/corridor.ts';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bytes=fs.readFileSync(path.join(root,'web/public/data/dashboard.json')),data=JSON.parse(bytes);
const options={window:365,maxAge:180,strict:false,asOf:data.cutoff};
const rows=data.companies.map(company=>{
  const series=bestSeries(company,data.cutoff);
  const target=projectValuation(company,targetReference(company,series,options),series,options);
  const corridor=priceCorridor(company,target);
  const checkpoints=[0,1,3,7,30,90,180,365].map(days=>{
    const date=days===365?target.target:shiftDate(target.origin,days);
    return {days,date,prices:CORRIDOR_LEVELS.map(k=>corridorPrice(corridor,date,k))};
  });
  return {company_id:company.id,symbol:company.symbol,series_id:series?.id,terminal_prices:CORRIDOR_LEVELS.map(k=>projectedPrice(target,k)),corridor,checkpoints};
});
const generatedAt=new Date().toISOString(),archivePath=`data/corridors/${generatedAt.replaceAll(':','').replaceAll('.','-')}`;
const report={generated_at:generatedAt,archive_path:archivePath,bundle_sha256:createHash('sha256').update(bytes).digest('hex'),data_cutoff:data.cutoff,method:CORRIDOR_METHOD,
  interpretation:'Illustrative paths conditioned on unchanged annual valuation scenarios. Near-term width uses past return volatility. Not calibrated confidence bounds.',
  sigma_levels:CORRIDOR_LEVELS,rows};
const output=path.join(root,'data/market'),archive=path.join(root,archivePath);
fs.mkdirSync(archive,{recursive:true});
const csv=data.companies.map((company,i)=>corridorCsv(company,[rows[i].corridor])).map((csv,i)=>i?csv.split('\n').slice(1).join('\n'):csv).join('\n');
fs.writeFileSync(path.join(output,'corridor_report.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(output,'corridor_defaults.csv'),csv+'\n');
for(const name of ['corridor_report.json','corridor_defaults.csv'])fs.copyFileSync(path.join(output,name),path.join(archive,name));
fs.writeFileSync(path.join(archive,'dashboard.json'),bytes);
const inputs=['scripts/build_corridor_report.mjs','web/src/corridor.ts','web/src/projection.ts','web/src/engine.ts','web/src/ensemble.ts','web/src/types.ts'];
for(const name of inputs){const dest=path.join(archive,name);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(path.join(root,name),dest);}
fs.writeFileSync(path.join(archive,'inputs.json'),JSON.stringify(inputs.map(name=>({path:name,sha256:createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex')})),null,2)+'\n');
console.log(JSON.stringify({archive_path:archivePath,usable_corridors:rows.filter(r=>!r.corridor.reason).length,
  nvidia:rows.filter(r=>r.company_id==='nvidia').map(r=>({close:r.corridor.target.currentPrice,daily_return_std:r.corridor.volatility.dailyStd,return_count:r.corridor.volatility.observations.length,checkpoints:r.checkpoints}))}));
