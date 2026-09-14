import { calculate, daysBetween, epoch, forwardEps, forwardInterval, median, nextYear, sampleStd, shiftDate, splitFactor, DAY } from './engine.ts';
import { calculateEnsemble, periodKey, selectedEstimators } from './ensemble.ts';
import type { Company, Contribution, Exclusion, Series, Settings, Snapshot, ValuationPoint } from './types';

export const TARGET_REFERENCE_DAYS = 365;

// Entry timing uses the selected lookback. Future targets have a separate,
// fixed one-year valuation reference with the same models and eligibility rules.
export function targetReference(company: Company, series: Series | undefined, options: Pick<Settings,'window'|'maxAge'|'strict'|'asOf'|'mode'|'combine'|'estimatorIds'>): ValuationPoint | undefined {
  const targetOptions={...options,window:TARGET_REFERENCE_DAYS};
  return (options.mode==='ensemble'
    ? calculateEnsemble(company,series,selectedEstimators(company,series,options),targetOptions,options.combine)
    : calculate(company,series,targetOptions)).at(-1);
}

export interface ProjectionMember {
  seriesId: string;
  label: string;
  snapshot: Snapshot;
  age: number;
  ageBasis: 'model' | 'report';
  splitFactor: number;
  eps: number | null;
  reason: string | null;
  missingIntervals: {start:string;end:string}[];
}
export interface Projection {
  id: string;
  label: string;
  origin: string;
  target: string;
  earningsStart: string;
  earningsEnd: string;
  currentPrice: number;
  currentEps: number | null;
  eps: number | null;
  median: number | null;
  std: number | null;
  window: number;
  count: number;
  possible: number;
  strict: boolean;
  maxAge: number;
  method: 'single' | 'median' | 'mean';
  members: ProjectionMember[];
  exclusions: Exclusion[];
  disagreementStd: number | null;
  reason: string | null;
}

// Calendar dates with no annual forecast in the frozen snapshot. This is an
// evidence diagnostic only: it never supplies EPS or infers a missing fiscal year.
export function missingIntervals(snapshot: Snapshot, target: string): {start:string;end:string}[] {
  const interval=forwardInterval(target), end=epoch(interval.end)+DAY;
  let cursor=epoch(interval.start);
  const gaps:{start:string;end:string}[]=[];
  const iso=(ms:number)=>new Date(ms).toISOString().slice(0,10);
  for(const estimate of [...snapshot.estimates].sort((a,b)=>a.fiscal_period_start.localeCompare(b.fiscal_period_start))) {
    const start=Math.max(cursor,epoch(estimate.fiscal_period_start));
    const stop=Math.min(end,epoch(estimate.fiscal_period_end)+DAY);
    if(!Number.isFinite(start)||!Number.isFinite(stop)||stop<=cursor||start>=end)continue;
    if(start>cursor)gaps.push({start:iso(cursor),end:iso(start-DAY)});
    cursor=Math.max(cursor,stop);
  }
  if(cursor<end)gaps.push({start:iso(cursor),end:interval.end});
  return gaps;
}

// The latest retained close is the projection origin. Reuse its exact eligible
// models and its prior-only P/E distribution. Never look up a future snapshot,
// refresh a reprint, or silently drop a member whose later targets are missing.
export function projectValuation(company: Company, reference: ValuationPoint | undefined, series: Series | undefined, options: Pick<Settings,'window'|'maxAge'|'strict'>, targetDate?: string): Projection | null {
  if(!reference)return null;
  const origin=reference.date, target=targetDate||nextYear(origin), interval=forwardInterval(target);
  const ensemble=reference.ensemble;
  const frozen:Pick<Contribution,'seriesId'|'label'|'snapshot'|'age'|'ageBasis'>[]=ensemble?ensemble.contributors:reference.snapshot&&series?[{
    seriesId:series.id,label:series.label,snapshot:reference.snapshot,
    age:daysBetween(origin,reference.snapshot.model_date||reference.snapshot.report_date),ageBasis:reference.snapshot.model_date?'model':'report'
  }]:[];
  const members:ProjectionMember[]=frozen.map(c=>{
    const result=!ensemble&&series?.currency!==company.currency?{eps:null,reason:'Price and forecast currencies differ'}:forwardEps(company,c.snapshot,origin,options.maxAge,options.strict,target);
    const shareBasisInvalid=!/^\d{4}-\d{2}-\d{2}$/.test(c.snapshot.share_basis_date)||!Number.isFinite(epoch(c.snapshot.share_basis_date))||c.snapshot.share_basis_date>c.snapshot.report_date;
    return {...c,splitFactor:splitFactor(company,c.snapshot.share_basis_date),...(shareBasisInvalid?{eps:null,reason:'Share basis date is missing or invalid'}:result),missingIntervals:missingIntervals(c.snapshot,target)};
  });
  const values=members.flatMap(c=>c.eps===null?[]:[c.eps]);
  const complete=members.length>0&&values.length===members.length;
  const compatible=new Set(members.filter(m=>m.eps!==null).map(m=>periodKey(m.snapshot,target))).size<=1;
  const eps=complete&&compatible?(ensemble?.method==='mean'?values.reduce((a,b)=>a+b,0)/values.length:median(values)):null;
  const price=company.prices.find(p=>p.date===origin);
  const priceValid=price?.currency===company.currency&&price.adjustment_basis==='split_adjusted_to_cutoff';
  const reason=!priceValid?'Price split adjustment or currency is unverified'
    :!ensemble&&!series?'No usable earnings series collected'
    :!ensemble&&series?.currency!==company.currency?'Price and forecast currencies differ'
    :!members.length?reference.reason||'No eligible forecast at the projection origin'
    :!complete?ensemble?'Projection unavailable: every origin contributor must cover the future earnings interval. Missing members have not been dropped.':members[0].reason
    :!compatible?'Origin contributors use different fiscal periods for the future earnings interval'
    :eps!==null&&eps<=0?'Projected forward earnings are zero or negative'
    :eps!==null&&eps<=(company.currency==='KRW'?1:0.01)?'Projected forward earnings are too close to zero for a stable P/E'
    :reference.median===null||reference.std===null?'Needs 20 valid prior P/E observations at the projection origin':null;
  return {id:ensemble?'ensemble':series?.id||'none',label:ensemble?`${ensemble.method==='mean'?'Equal-weighted mean':'Median'} · ${ensemble.group}`:series?.label||'No earnings series',origin,target,earningsStart:interval.start,earningsEnd:interval.end,currentPrice:reference.price,currentEps:reference.eps,eps,median:reference.median,std:reference.std,window:options.window,count:reference.count,possible:reference.possible,strict:options.strict,maxAge:options.maxAge,method:ensemble?.method||'single',members,exclusions:ensemble?.exclusions||[],disagreementStd:complete&&compatible&&values.length>1?sampleStd(values):null,reason:reason||null};
}

// Calculate each calendar day's valuation as the earnings horizon rolls. The models, member
// set and reference multiples stay fixed; these are not an assumed market path.
export function projectionCurve(company: Company, reference: ValuationPoint | undefined, series: Series | undefined, options: Pick<Settings,'window'|'maxAge'|'strict'>): Projection[] {
  if(!reference)return [];
  const target=nextYear(reference.date), dates:string[]=[];
  for(let date=reference.date;date<target;date=shiftDate(date,1))dates.push(date);
  dates.push(target);
  return dates.map(date=>projectValuation(company,reference,series,options,date)!);
}

export function projectedPrice(projection: Projection | null, sigma: number): number | null {
  if(!projection||projection.reason||projection.eps===null||projection.median===null||projection.std===null)return null;
  const multiple=projection.median+sigma*projection.std;
  const value=multiple*projection.eps;
  return multiple>0&&Number.isFinite(value)?value:null;
}
export function projectedChange(projection: Projection | null, sigma=0): number | null {
  const price=projectedPrice(projection,sigma);
  return price!==null&&projection!.currentPrice>0?100*(price/projection!.currentPrice-1):null;
}

export function projectionCsv(company: Company, projections: Projection[]): string {
  const fields=['company','series','row_kind','origin_date','target_date','earnings_start','earnings_end','currency','origin_close','origin_forward_eps','target_forward_eps','reference_window_days','reference_start_inclusive','reference_end_exclusive','reference_count','possible_sessions','historical_median_pe','historical_sample_std_pe','minus_2_price','minus_1_5_price','minus_1_price','median_price','plus_1_price','plus_1_5_price','plus_2_price','median_change_pct','method','origin_member_count','members_with_future_eps','analyst_eps_sample_std','require_verified_availability','max_model_age_at_origin_days','members_json','origin_exclusions_json','gap_reason','origin_price_source_url','origin_price_source_sha256','origin_price_adjustment_basis'];
  const rows:unknown[][]=[fields,...projections.map(p=>{
    const price=company.prices.find(x=>x.date===p.origin);
    return [company.symbol,p.label,'12_month_valuation_scenario',p.origin,p.target,p.earningsStart,p.earningsEnd,company.currency,p.currentPrice,p.currentEps,p.eps,p.window,shiftDate(p.origin,-p.window),p.origin,p.count,p.possible,p.median,p.std,...[-2,-1.5,-1,0,1,1.5,2].map(k=>projectedPrice(p,k)),projectedChange(p),p.method,p.members.length,p.members.filter(m=>m.eps!==null).length,p.disagreementStd,p.strict,p.maxAge,JSON.stringify(p.members),JSON.stringify(p.exclusions),p.reason,price?.source_url,price?.source_sha256,price?.adjustment_basis];
  })];
  return rows.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\n');
}
