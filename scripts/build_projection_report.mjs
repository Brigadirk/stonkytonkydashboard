#!/usr/bin/env node
// Reproduce current target availability without fetching prices or estimates.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { bestSeries } from '../web/src/engine.ts';
import { calculateEnsemble, compatibleSeries } from '../web/src/ensemble.ts';
import { projectValuation, projectedPrice, projectionCsv, targetReference, TARGET_REFERENCE_DAYS } from '../web/src/projection.ts';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bundlePath='web/public/data/dashboard.json';
const bytes=fs.readFileSync(path.join(root,bundlePath));
const data=JSON.parse(bytes);
const windows=[90,180,365];
const rows=[],defaults=[],csv=[];
for(const company of data.companies){
  const preferred=bestSeries(company,data.cutoff);
  for(const series of company.series){
    for(const window of windows){
      const options={asOf:data.cutoff,window,maxAge:180,strict:false};
      const reference=targetReference(company,series,options);
      const projection=projectValuation(company,reference,series,{...options,window:TARGET_REFERENCE_DAYS});
      rows.push({company_id:company.id,symbol:company.symbol,series_id:series.id,default_series:series.id===preferred?.id,window_days:window,projection});
      if(series.id===preferred?.id){
        defaults.push({symbol:company.symbol,series:series.id,window,origin:projection?.origin,target:projection?.target,median_target:projectedPrice(projection,0),reason:projection?.reason||null});
        if(projection&&window===365)csv.push(projectionCsv(company,[projection]));
      }
    }
  }
  const selected=compatibleSeries(company,preferred);
  if(selected.length){
    const options={asOf:data.cutoff,window:365,maxAge:180,strict:false};
    const projection=projectValuation(company,calculateEnsemble(company,preferred,selected,options).at(-1),preferred,options);
    rows.push({company_id:company.id,symbol:company.symbol,series_id:'all_compatible_median',default_series:false,window_days:365,projection});
  }
}
const generatedAt=new Date().toISOString();
const archivePath=`data/projections/${generatedAt.replaceAll(':','').replaceAll('.','-')}`;
const report={generated_at:generatedAt,archive_path:archivePath,data_cutoff:data.cutoff,bundle_path:bundlePath,bundle_sha256:createHash('sha256').update(bytes).digest('hex'),entry_windows_days:windows,target_reference_window_days:TARGET_REFERENCE_DAYS,window_role:'Entry comparison; target reference stays fixed at365days',horizon:'one_calendar_year_from_latest_retained_close',freshness_days_at_origin:180,strict:false,defaults,rows};
const output=path.join(root,'data/market');
fs.writeFileSync(path.join(output,'projection_report.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(output,'projection_defaults.csv'),csv.map((s,i)=>i?s.split('\n').slice(1).join('\n'):s).join('\n')+'\n');
const gaps=[['company','series','window_days','origin','target','earnings_start','earnings_end','reason','member_id','model_date','report_date','missing_start','missing_end','source_url','source_sha256']];
for(const row of rows){
  const p=row.projection;if(!p?.reason)continue;
  const members=p.members.length?p.members:[null];
  for(const member of members){
    const intervals=member?.missingIntervals.length?member.missingIntervals:[null];
    for(const interval of intervals)gaps.push([row.symbol,row.series_id,row.window_days,p.origin,p.target,p.earningsStart,p.earningsEnd,member?.reason||p.reason,member?.seriesId,member?.snapshot.model_date,member?.snapshot.report_date,interval?.start,interval?.end,member?.snapshot.source_url,member?.snapshot.source_sha256]);
  }
}
fs.writeFileSync(path.join(output,'projection_gaps.csv'),gaps.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\n')+'\n');
const archive=path.join(root,archivePath);
fs.mkdirSync(archive,{recursive:true});
for(const filename of ['projection_report.json','projection_defaults.csv','projection_gaps.csv'])fs.copyFileSync(path.join(output,filename),path.join(archive,filename));
fs.writeFileSync(path.join(archive,'dashboard.json'),bytes);
const inputs=['scripts/build_projection_report.mjs','web/src/projection.ts','web/src/engine.ts','web/src/ensemble.ts','web/src/types.ts'];
for(const filename of inputs){const destination=path.join(archive,filename);fs.mkdirSync(path.dirname(destination),{recursive:true});fs.copyFileSync(path.join(root,filename),destination);}
fs.writeFileSync(path.join(archive,'inputs.json'),JSON.stringify(inputs.map(filename=>({path:filename,sha256:createHash('sha256').update(fs.readFileSync(path.join(root,filename))).digest('hex')})),null,2)+'\n');
console.log(JSON.stringify({archive_path:archivePath,default_targets:defaults.filter(p=>p.median_target!==null).length,default_comparisons:defaults.length,all_views:rows.length,views_with_gaps:rows.filter(r=>r.projection?.reason).length,report:'data/market/projection_report.json'}));
