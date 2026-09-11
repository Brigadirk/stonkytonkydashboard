#!/usr/bin/env node
// Compare retained forecast coverage without changing calculation or eligibility rules.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { bestSeries, calculate, daysBetween, shiftDate } from '../web/src/engine.ts';
import { targetReference, projectValuation, projectedPrice } from '../web/src/projection.ts';

const beforePath=process.argv[2]||'data/deliveries/20260911-memory-coverage/before/dashboard.json';
const afterPath=process.argv[3]||'web/public/data/dashboard.json';
const output=process.argv[4]||'data/market/memory_coverage_report.json';
const read=path=>JSON.parse(fs.readFileSync(path));
const before=read(beforePath),after=read(afterPath);
const memory=['micron','sandisk','sk_hynix','samsung_electronics'];
assert.equal(after.cutoff,before.cutoff,'Collection must preserve the price cutoff');
for(const c of after.companies){
  const old=before.companies.find(x=>x.id===c.id);
  assert.deepEqual(c.prices,old.prices,`${c.id}: collection changed prices`);
  if(!memory.includes(c.id))assert.deepEqual(c,old,`${c.id}: unrelated company changed`);
}
function describe(data,id){
  const c=data.companies.find(x=>x.id===id),s=bestSeries(c,data.cutoff);
  const options={window:365,maxAge:180,strict:false,asOf:data.cutoff};
  const points=calculate(c,s,options),recent=points.filter(p=>p.date>=shiftDate(data.cutoff,-365));
  const jumps=[];
  for(let i=1;i<recent.length;i++){
    const previous=recent[i-1],current=recent[i];
    if(previous.eps>0&&current.eps>0&&previous.snapshot?.id!==current.snapshot?.id){
      jumps.push({date:current.date,previous_eps:previous.eps,eps:current.eps,
        change_pct:100*(current.eps/previous.eps-1),previous_model:previous.snapshot?.model_date,
        model:current.snapshot?.model_date||current.snapshot?.report_date,report_date:current.snapshot?.report_date});
    }
  }
  const p=projectValuation(c,targetReference(c,s,options),s,options);
  const models=s.snapshots.map(m=>({model_date:m.model_date||m.report_date,
    date_basis:m.model_date?'printed_model_date':'report_date_proxy',report_date:m.report_date,
    available_date:m.available_date,source_url:m.source_url,source_sha256:m.source_sha256,
    fiscal_periods:m.estimates.map(e=>e.fiscal_period),eps:m.estimates.map(e=>e.eps)}));
  const modelDates=[...new Set(models.map(m=>m.model_date))].sort();
  const gaps=modelDates.slice(1).map((d,i)=>({start:modelDates[i],end:d,days:daysBetween(d,modelDates[i])}));
  return {default_series:s.id,default_label:s.label,default_snapshots:models.length,
    default_unique_effective_model_dates:modelDates.length,
    total_eps:c.series.reduce((n,s)=>n+s.snapshots.reduce((n,m)=>n+m.estimates.length,0),0),
    raw_forecast_observations:c.forecast_count,
    total_snapshots:c.series.reduce((n,s)=>n+s.snapshots.length,0),models,
    longest_interval_between_default_models:gaps.sort((a,b)=>b.days-a.days)[0]||null,
    last_year_usable_eps_sessions:recent.filter(p=>p.eps!==null).length,last_year_sessions:recent.length,
    recent_model_changes:jumps,largest_recent_positive_eps_jump:jumps.sort((a,b)=>Math.abs(b.change_pct)-Math.abs(a.change_pct))[0]||null,
    current_reference:{count:p.count,possible:p.possible,median_pe:p.median,std_pe:p.std},
    current_model:p.members[0]?.snapshot.model_date||p.members[0]?.snapshot.report_date,current_eps:p.currentEps,target_eps:p.eps,
    target_date:p.target,median_target:projectedPrice(p,0)};
}
const rows=memory.map(company_id=>{
  const old=describe(before,company_id),now=describe(after,company_id);
  assert.equal(old.default_series,now.default_series,`${company_id}: default estimator changed`);
  const existing=new Set(old.models.map(m=>m.model_date));
  return {company_id,before:old,after:now,added_default_model_dates:now.models.filter(m=>!existing.has(m.model_date)),
    added_eps:now.total_eps-old.total_eps,added_snapshots:now.total_snapshots-old.total_snapshots};
});
const report={generated_at:new Date().toISOString(),before_path:beforePath,after_path:afterPath,
  before_sha256:createHash('sha256').update(fs.readFileSync(beforePath)).digest('hex'),
  after_sha256:createHash('sha256').update(fs.readFileSync(afterPath)).digest('hex'),
  cutoff:after.cutoff,prices_and_non_memory_companies_unchanged:true,default_estimators_preserved:true,
  interpretation:'Published revisions remain discrete. No interpolation, hindsight backfill or new estimator weighting. Effective model dates use report dates when the numerical model date is unprinted, with the basis recorded for every snapshot. Jump percentages compare positive forward EPS across consecutive recorded sessions and can be large near cyclical loss periods; they are not forecast accuracy scores.',rows};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(rows.map(r=>({company:r.company_id,default_models:[r.before.default_unique_effective_model_dates,r.after.default_unique_effective_model_dates],
  added_eps:r.added_eps,reference_coverage:[r.before.current_reference.count,r.after.current_reference.count],
  median_target:[r.before.median_target,r.after.median_target],largest_jump_pct:[r.before.largest_recent_positive_eps_jump?.change_pct,r.after.largest_recent_positive_eps_jump?.change_pct]}))));
