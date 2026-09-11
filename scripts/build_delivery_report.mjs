// Exact observed-session gaps and model coverage for the access handoff.
// This report diagnoses collection; it never fills gaps or selects a strategy.
import {readFileSync,writeFileSync} from 'node:fs';
import {bandValue,bestSeries,calculate,daysBetween} from '../web/src/engine.ts';
import {calculateEnsemble,compatibility,compatibleSeries,isIndividual} from '../web/src/ensemble.ts';
const root=new URL('../',import.meta.url), read=p=>JSON.parse(readFileSync(new URL(p,root),'utf8'));
const data=read('web/public/data/dashboard.json');
const startDate=new Date(data.cutoff+'T00:00:00Z');startDate.setUTCFullYear(startDate.getUTCFullYear()-5);
const start=startDate.toISOString().slice(0,10),options={asOf:data.cutoff,window:365,maxAge:180,strict:false};
const rows=[],companies=[];
function ranges(points,key){
  const out=[];let active=null;
  for(const p of points){const reason=key(p);if(!reason){active=null;continue}
    if(active?.reason===reason){active.end=p.date;active.sessions++}
    else {active={start:p.date,end:p.date,sessions:1,reason};out.push(active)}
  }
  return out;
}
for(const c of data.companies){
  const chosen=bestSeries(c,data.cutoff), all=c.series.map(s=>({series:s,points:calculate(c,s,options),strict:calculate(c,s,{...options,strict:true})}));
  const selected=all.find(s=>s.series.id===chosen?.id), points=selected?.points||calculate(c,undefined,options),last=points.at(-1);
  const periodMap=new Map(c.series.flatMap(s=>s.snapshots.flatMap(m=>m.estimates)).filter(e=>e.fiscal_period.startsWith('FY')).map(e=>[e.fiscal_period,{period:e.fiscal_period,start:e.fiscal_period_start,end:e.fiscal_period_end}]));
  const eligible=points.map((p,i)=>({...p,anyEps:all.some(s=>s.points[i].eps!==null),anyVerifiedEps:all.some(s=>s.strict[i].eps!==null)})).filter(p=>p.date>=start);
  for(const p of eligible){
    const next=new Date(p.date+'T00:00:00Z');next.setUTCFullYear(next.getUTCFullYear()+1);
    const periods=[...periodMap.values()].filter(t=>t.end>p.date&&t.start<=next.toISOString().slice(0,10)).sort((a,b)=>a.start.localeCompare(b.start)).map(t=>t.period);
    if(p.eps===null||!p.anyVerifiedEps||p.count<p.possible||bandValue(p,0,'price')===null)rows.push({company_id:c.id,symbol:c.symbol,date:p.date,default_series_id:chosen?.id,default_model_date:p.snapshot?.model_date,default_report_date:p.snapshot?.report_date,default_gap:p.reason||'',forward_fiscal_targets:periods.join(';'),any_other_series_has_eps:p.anyEps,any_verified_series_has_eps:p.anyVerifiedEps,reference_usable:p.count,reference_possible:p.possible,missing_fields:p.eps!==null&&p.reason?`Observed EPS limitation (${p.reason}); this is not a missing estimate`:p.eps===null?'dated consecutive-year EPS; original availability; exact definition and share basis':!p.anyVerifiedEps?'original publication timestamp or exact-byte historical availability evidence':p.count<p.possible?'earlier eligible EPS for reference sessions':'at least 20 prior usable P/E observations'});
  }
  const seen=new Set(),groups=[];
  for(const s of c.series){const group=compatibility(c,s);if(!group.eligible||seen.has(group.key))continue;seen.add(group.key);
    const members=compatibleSeries(c,s),history=calculateEnsemble(c,s,members,options),current=history.at(-1);
    groups.push({key:group.key,label:group.label,note:group.note,series_ids:members.map(s=>s.id),maximum_contributors:Math.max(0,...history.filter(p=>p.date>=start).map(p=>p.ensemble.contributors.length)),current_contributors:current?.ensemble.contributors.map(c=>({analyst:c.analyst,firm:c.firm,age_days:c.age,model_date:c.snapshot.model_date,report_date:c.snapshot.report_date}))||[],composition_changes:history.filter(p=>p.date>=start&&p.ensemble.compositionChanged).length});
  }
  companies.push({company_id:c.id,symbol:c.symbol,price_start:c.prices[0]?.date,price_end:last?.date,requested_history_start:c.id==='sandisk'?'2025-02-24':start,default_series:chosen?.label,series:c.series.length,named_estimator_series:c.series.filter(isIndividual).length,models:c.series.reduce((n,s)=>n+s.snapshots.length,0),eps_observations:c.series.reduce((n,s)=>n+s.snapshots.reduce((m,x)=>m+x.estimates.length,0),0),current_model_date:last?.snapshot?.model_date||null,current_report_date:last?.snapshot?.report_date||null,current_age_days:last?.snapshot?daysBetween(last.date,last.snapshot.model_date||last.snapshot.report_date):null,current_reference_usable:last?.count,current_reference_possible:last?.possible,current_bands:!!last&&bandValue(last,0,'price')!==null,default_missing_eps_ranges:ranges(eligible,p=>p.eps===null?p.reason||'Missing EPS':null),no_series_eps_ranges:ranges(eligible,p=>!p.anyEps?'No collected series supplies eligible EPS':null),no_verified_eps_ranges:ranges(eligible,p=>!p.anyVerifiedEps?'No estimate with proven availability by this date':null),compatibility_groups:groups});
}
const report={as_of:data.cutoff,generated_at:new Date().toISOString(),settings:options,requested_start:start,interpretation:'Ranges span consecutive retained price sessions, not every calendar day. Other-series coverage is diagnostic and is never spliced into the default or ensemble. Original report dates remain assumptions unless the exact source has historical evidence. Fiscal targets are drawn from retained issuer-calendar mappings; this is a field/date request, not an inferred estimate.',totals:{...data.totals,prices:data.companies.reduce((n,c)=>n+c.prices.length,0),series:companies.reduce((n,c)=>n+c.series,0),models:companies.reduce((n,c)=>n+c.models,0),eps:companies.reduce((n,c)=>n+c.eps_observations,0),initial_eps_outcomes:data.eps_pilot.outcomes.length,comparable_eps_pairs:data.eps_pilot.pairs.length,companies_with_current_bands:companies.filter(c=>c.current_bands).length,archive_evidence_sources:read('data/market/availability_evidence.json').length,backtest_status:data.backtest_readiness.status},companies,accuracy_missing_prerequisites:{blocked_fixed_horizon_targets:data.eps_pilot.blocked,matched_historical_consensus:'Missing for all current comparable EPS pairs; same target, horizon, definition, currency and share basis required',independent_outcomes:'Pairs at different horizons can repeat the same company year; evaluate distinct fiscal outcomes per analyst and horizon',adjusted_eps:'Company and broker-specific adjustment reconciliation required; Korean share denominators and ASML broker denominator differences remain unresolved'},backtest_missing_prerequisites:data.backtest_readiness.limitations};
writeFileSync(new URL('data/market/delivery_report.json',root),JSON.stringify(report,null,2)+'\n');
const fields=['company_id','symbol','date','default_series_id','default_model_date','default_report_date','default_gap','forward_fiscal_targets','any_other_series_has_eps','any_verified_series_has_eps','reference_usable','reference_possible','missing_fields'];
const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
writeFileSync(new URL('data/market/missing_data_dates.csv',root),[fields,...rows.map(r=>fields.map(k=>r[k]))].map(r=>r.map(quote).join(',')).join('\n')+'\n');
console.log(JSON.stringify(report.totals));
