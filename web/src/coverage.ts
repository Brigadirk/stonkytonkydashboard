import { bandValue, bestSeries, calculate, shiftDate } from './engine.ts';
import type { Company, DashboardData, Series, Settings, ValuationPoint } from './types';

export type GapReason = 'no_forecast'|'stale_model'|'missing_years'|'nonpositive_eps'|'unverified'|'other';
export interface MonthCoverage {
  month:string; sessions:number; eps_days:number; band_days:number; other_series_days:number;
  reasons:Partial<Record<GapReason,number>>; new_models:number;
}
export interface CoverageRow { company_id:string; symbol:string; company_name:string; series_id:string; series_label:string; accounting_basis:string; months:MonthCoverage[] }
export const reasonLabels:Record<GapReason,string>={no_forecast:'No forecast available',stale_model:'Model too old',missing_years:'Missing consecutive fiscal years',nonpositive_eps:'EPS is zero, negative or near zero',unverified:'Availability not verified',other:'Unusable price or earnings basis'};
export function reasonCode(point:ValuationPoint):GapReason {
  const reason=point.reason||'';
  if(reason.includes('older than'))return 'stale_model';
  if(reason.includes('fiscal')||reason.includes('Fiscal'))return 'missing_years';
  if(reason.includes('zero')||reason.includes('negative'))return 'nonpositive_eps';
  if(reason.includes('verified'))return 'unverified';
  if(!point.snapshot||reason.includes('No forecast')||reason.includes('No usable earnings'))return 'no_forecast';
  return 'other';
}
export function monthsBetween(start:string,end:string):string[] {
  const result:string[]=[];
  let month=start.slice(0,7);
  while(month<=end.slice(0,7)) {
    result.push(month);
    const [year,m]=month.split('-').map(Number);
    month=`${year+(m===12?1:0)}-${String(m===12?1:m+1).padStart(2,'0')}`;
  }
  return result;
}
export function buildCompanyCoverage(company:Company,series:Series|undefined,options:Pick<Settings,'window'|'maxAge'|'strict'|'asOf'>,start=shiftDate(options.asOf,-1826)):CoverageRow {
  const points=calculate(company,series,options).filter(p=>p.date>=start);
  const alternatives=new Set<string>();
  for(const other of company.series.filter(s=>s.id!==series?.id)) {
    for(const p of calculate(company,other,options))if(p.multiple!==null)alternatives.add(p.date);
  }
  const months=monthsBetween(start,options.asOf).map(month=>{
    const rows=points.filter(p=>p.date.startsWith(month));
    const reasons:MonthCoverage['reasons']={};
    for(const p of rows.filter(p=>p.multiple===null)) {const reason=reasonCode(p);reasons[reason]=(reasons[reason]||0)+1;}
    return {month,sessions:rows.length,eps_days:rows.filter(p=>p.multiple!==null).length,band_days:rows.filter(p=>bandValue(p,0,'price')!==null).length,other_series_days:rows.filter(p=>p.multiple===null&&alternatives.has(p.date)).length,reasons,new_models:new Set((series?.snapshots||[]).filter(s=>s.available_date.startsWith(month)&&s.available_date>=start&&s.available_date<=options.asOf).map(s=>s.model_date||s.report_date)).size};
  });
  return {company_id:company.id,symbol:company.symbol,company_name:company.name,series_id:series?.id||'',series_label:series?.label||'No earnings series',accounting_basis:series?.accounting_basis||'',months};
}
export function buildGapMap(data:DashboardData,options:Pick<Settings,'window'|'maxAge'|'strict'|'asOf'>,overrides:Record<string,string>={}):CoverageRow[] {
  return data.companies.map(c=>buildCompanyCoverage(c,c.series.find(s=>s.id===overrides[c.id])||bestSeries(c,options.asOf),options));
}
export function gapCsv(rows:CoverageRow[]):string {
  const fields=['company','series','basis','month','price_sessions','usable_eps_sessions','price_band_sessions','other_series_only_sessions','new_models',...Object.keys(reasonLabels)];
  const quote=(value:unknown)=>`"${String(value??'').replaceAll('"','""')}"`;
  return [fields,...rows.flatMap(row=>row.months.map(m=>[row.symbol,row.series_label,row.accounting_basis,m.month,m.sessions,m.eps_days,m.band_days,m.other_series_days,m.new_models,...Object.keys(reasonLabels).map(reason=>m.reasons[reason as GapReason]||0)]))].map(row=>row.map(quote).join(',')).join('\n');
}
