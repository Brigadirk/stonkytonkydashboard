#!/usr/bin/env node
// Audit every compatible group, including groups that are not the default view.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { calculateEnsemble, compatibility, compatibleSeries } from '../web/src/ensemble.ts';
import { daysBetween } from '../web/src/engine.ts';
import { projectValuation, projectedPrice, targetReference, TARGET_REFERENCE_DAYS } from '../web/src/projection.ts';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bytes=fs.readFileSync(path.join(root,'web/public/data/dashboard.json'));
const data=JSON.parse(bytes), groups=[];
for(const company of data.companies){
  const seen=new Set();
  for(const anchor of company.series){
    const group=compatibility(company,anchor);
    if(!group.eligible||seen.has(group.key))continue;
    seen.add(group.key);
    const selected=compatibleSeries(company,anchor);
    for(const window of [90,180,365]){
      const options={asOf:data.cutoff,window,maxAge:180,strict:false};
      const points=calculateEnsemble(company,anchor,selected,options), current=points.at(-1);
      if(!current)continue;
      const history=points.filter(p=>p.date<current.date&&daysBetween(current.date,p.date)<=window&&p.multiple!==null);
      const multiple=history.filter(p=>(p.ensemble?.contributors.length||0)>1);
      const target=targetReference(company,anchor,{...options,mode:'ensemble',combine:'median'});
      const projection=projectValuation(company,target,anchor,{...options,window:TARGET_REFERENCE_DAYS});
      const query=new URLSearchParams({company:company.id,series:anchor.id,mode:'ensemble',combine:'median',window:String(window),estimatorIds:'auto',asOf:data.cutoff});
      groups.push({company_id:company.id,symbol:company.symbol,group_key:group.key,group_label:group.label,
        anchor_series:anchor.id,window_days:window,origin:current.date,target:projection?.target,
        local_view_url:`http://127.0.0.1:5178/?${query}`,
        current_contributors:current.ensemble?.contributors,
        current_exclusions:current.ensemble?.exclusions.map(x=>({series_id:x.seriesId,label:x.label,reason:x.reason})),
        age_range_days:[current.ensemble?.minAge,current.ensemble?.maxAge],
        reference_observations:current.count,reference_possible:current.possible,
        target_reference_window_days:TARGET_REFERENCE_DAYS,target_reference_observations:target?.count,target_reference_possible:target?.possible,
        reference_sessions_with_multiple_firms:multiple.length,
        first_multi_firm_reference_date:multiple[0]?.date||null,
        composition_changes:points.filter(p=>daysBetween(current.date,p.date)<=window&&p.ensemble?.compositionChanged)
          .map(p=>({date:p.date,added:p.ensemble.added,removed:p.ensemble.removed,count:p.ensemble.contributors.length})),
        median_target:projectedPrice(projection,0),target_reason:projection?.reason||null,
        target_earnings_start:projection?.earningsStart,target_earnings_end:projection?.earningsEnd,
        target_members:projection?.members,
      });
    }
  }
}
const report={generated_at:new Date().toISOString(),data_cutoff:data.cutoff,
  window_role:'Entry comparison; every future target uses an independent365-day valuation reference',
  bundle_sha256:createHash('sha256').update(bytes).digest('hex'),
  availability:'Dated-report reconstruction; historical dissemination unverified. Strict mode remains available.',
  interpretation:'Reference bands describe historical valuation variation. Contributor EPS disagreement is a different quantity. Multiple-firm coverage is counted explicitly; earlier single-firm observations are not described as ensemble history.',groups};
fs.writeFileSync(path.join(root,'data/market/estimator_comparison_report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({groups:groups.length/3,current_multi_firm_groups:groups.filter(g=>g.window_days===365&&g.current_contributors.length>1).map(g=>({symbol:g.symbol,group:g.group_label,contributors:g.current_contributors.length,history_sessions:g.reference_sessions_with_multiple_firms,median_target:g.median_target}))}));
