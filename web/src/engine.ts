import type { Company, Price, Series, Settings, Snapshot, ValuationPoint } from './types';
export const DAY = 86_400_000;
export const epoch = (date: string) => Date.parse(date + 'T00:00:00Z');
export const daysBetween = (a: string, b: string) => Math.round((epoch(a) - epoch(b)) / DAY);
export const shiftDate = (date: string, days: number) => new Date(epoch(date) + days * DAY).toISOString().slice(0, 10);
export function nextYear(date: string): string {
  const current = new Date(epoch(date));
  const lastDay = new Date(Date.UTC(current.getUTCFullYear()+1,current.getUTCMonth()+1,0)).getUTCDate();
  return new Date(Date.UTC(current.getUTCFullYear()+1,current.getUTCMonth(),Math.min(current.getUTCDate(),lastDay))).toISOString().slice(0,10);
}
export const forwardInterval = (date: string) => ({start:shiftDate(date,1),end:nextYear(date)});
export function median(values: number[]): number {
  const sorted = [...values].sort((a,b) => a-b), n = sorted.length;
  return n ? (sorted[Math.floor((n-1)/2)] + sorted[Math.floor(n/2)])/2 : NaN;
}
export function sampleStd(values: number[]): number {
  if (values.length < 2) return NaN;
  const mean = values.reduce((a,b) => a+b, 0)/values.length;
  return Math.sqrt(values.reduce((a,b) => a + (b-mean)**2, 0)/(values.length-1));
}
export function splitFactor(company: Company, shareBasisDate: string): number {
  return company.splits.filter(s => s.effective_date > shareBasisDate).reduce((a,s) => a*s.ratio, 1);
}
export function verifiedFrom(snapshot: Snapshot): string | null {
  if(snapshot.availability_basis==='verified_available_at')return snapshot.available_date;
  if(snapshot.verification_kind==='verified_available_by_archive'&&snapshot.verified_available_date&&snapshot.availability_evidence_url)
    return snapshot.verified_available_date>snapshot.available_date?snapshot.verified_available_date:snapshot.available_date;
  return null;
}
// `date` controls information eligibility and freshness. `earningsDate` controls
// the start of the forward earnings horizon; projecting never advances knowledge.
export function forwardEps(company: Company, snapshot: Snapshot | null, date: string, maxAge: number, strict: boolean, earningsDate=date): {eps: number|null; reason: string|null} {
  if (!snapshot) return {eps:null, reason:'No forecast available on this date'};
  if (snapshot.available_date > date) return {eps:null, reason:'Forecast not yet available'};
  if (strict && !verifiedFrom(snapshot)) return {eps:null, reason:'Original availability has not been verified'};
  if (strict && verifiedFrom(snapshot)! > date) return {eps:null, reason:'Verified availability begins after this date'};
  const ageDate = snapshot.model_date || snapshot.report_date;
  if (ageDate > date) return {eps:null, reason:'Numerical model is dated after this observation'};
  if (daysBetween(date, ageDate) > maxAge) return {eps:null, reason:`Forecast older than ${maxAge} days`};
  const factor = splitFactor(company, snapshot.share_basis_date);
  let eps: number;
  if (snapshot.kind === 'ntm') {
    if (earningsDate !== date) return {eps:null, reason:'An NTM-only snapshot does not contain earnings for a later forward horizon; dated annual forecasts are required'};
    eps = snapshot.estimates[0]?.eps / factor;
  } else {
    // Allocate the next 12 calendar months over exact issuer fiscal years.
    // Each annual model assumes uniform earnings per day within its fiscal year.
    const interval = forwardInterval(earningsDate);
    const start = epoch(interval.start), end = epoch(interval.end) + DAY;
    let covered = 0, total = 0, previousEnd: number | null = null;
    for (const target of [...snapshot.estimates].sort((a,b)=>a.fiscal_period_start.localeCompare(b.fiscal_period_start))) {
      const fiscalStart=epoch(target.fiscal_period_start), fiscalEnd=epoch(target.fiscal_period_end)+DAY;
      const overlapStart=Math.max(start,fiscalStart), overlapEnd=Math.min(end,fiscalEnd);
      if (overlapEnd<=overlapStart) continue;
      if (previousEnd !== null && overlapStart !== previousEnd) return {eps:null,reason:'Fiscal periods overlap or leave a gap'};
      const overlap=overlapEnd-overlapStart;
      covered+=overlap;
      total+=target.eps*overlap/(fiscalEnd-fiscalStart);
      previousEnd=overlapEnd;
    }
    if (covered !== end-start) return {eps:null,reason:'Consecutive forward fiscal years are missing'};
    eps=total/factor;
  }
  if (!Number.isFinite(eps)) return {eps:null, reason:'Forward earnings are invalid'};
  if (eps <= 0) return {eps, reason:'Forward earnings are zero or negative'};
  if (eps <= (company.currency === 'KRW' ? 1 : 0.01)) return {eps, reason:'Forward earnings are too close to zero for a stable P/E'};
  return {eps, reason:null};
}
// Publication of an old model cannot roll the selected forecast backwards.
export function latestSnapshot(series: Series | undefined, date: string, strict=false): Snapshot | null {
  return [...(series?.snapshots || [])].filter(s=>s.available_date<=date&&(!strict||verifiedFrom(s)!==null&&verifiedFrom(s)!<=date)).sort((a,b)=>
    (b.model_date||b.report_date).localeCompare(a.model_date||a.report_date) ||
    b.available_date.localeCompare(a.available_date) || b.report_date.localeCompare(a.report_date) || a.id.localeCompare(b.id))[0] || null;
}
type CalculationOptions = Pick<Settings, 'window'|'maxAge'|'strict'|'asOf'>;
type EarningsInput = Pick<ValuationPoint, 'eps'|'reason'|'snapshot'|'ensemble'>;
export function calculate(company: Company, series: Series | undefined, options: Pick<Settings, 'window'|'maxAge'|'strict'|'asOf'>): ValuationPoint[] {
  return calculateFromEarnings(company,options,date=>{
    const snapshot=latestSnapshot(series,date,options.strict);
    const result=series?.currency !== company.currency ? {eps:null, reason:series ? 'Price and forecast currencies differ' : 'No usable earnings series collected'} : options.strict&&!snapshot?{eps:null,reason:'No forecast with verified availability by this date'}:forwardEps(company,snapshot,date,options.maxAge,options.strict);
    return {...result,snapshot};
  });
}
// Both individual and combined estimates enter the same rolling calculation.
export function calculateFromEarnings(company: Company, options: CalculationOptions, resolve: (date: string)=>EarningsInput): ValuationPoint[] {
  const prices = company.prices.filter(p => !options.asOf || p.date <= options.asOf);
  const points: ValuationPoint[] = [];
  let left=0;
  for (const price of prices) {
    const result=resolve(price.date);
    const priceValid = price.adjustment_basis === 'split_adjusted_to_cutoff' && price.currency === company.currency;
    const eps = priceValid ? result.eps : null;
    const ratio = eps !== null && !result.reason ? price.close/eps : null;
    const multiple = ratio !== null && Number.isFinite(ratio) ? ratio : null;
    while (left < points.length && daysBetween(price.date, points[left].date) > options.window) left++;
    const history = points.slice(left).flatMap(p => p.multiple === null ? [] : [p.multiple]);
    const count = history.length, center = count >= 20 ? median(history) : null, std = count >= 20 ? sampleStd(history) : null;
    points.push({date:price.date,price:price.close,eps,multiple,median:center,std,count,possible:points.length-left,
      percentile:multiple !== null && count >= 20 ? 100*(history.filter(v => v < multiple).length + 0.5*history.filter(v => v === multiple).length)/count : null,
      z:multiple !== null && center !== null && std !== null && std > 0 ? (multiple-center)/std : null,
      snapshot:result.snapshot,reason:priceValid ? result.reason : 'Price split adjustment or currency is unverified',...(result.ensemble?{ensemble:result.ensemble}:{})});
  }
  return points;
}
export function bandValue(point: ValuationPoint, sigma: number, metric: Settings['metric']): number|null {
  if (point.multiple === null || point.median === null || point.std === null) return null;
  const multiple = point.median + sigma*point.std;
  return multiple > 0 ? multiple*(metric === 'price' ? point.eps! : 1) : null;
}
export function csvExport(points: ValuationPoint[], company: Company, series: Series|undefined, settings: Settings): string {
  const pricesByDate = new Map(company.prices.map(p=>[p.date,p]));
  const fields = ['company','series','date','price','currency','forward_eps','forward_pe','window_days','reference_count','possible_sessions','median_pe','sample_std_pe','minus_2_price','minus_1_5_price','minus_1_price','median_price','plus_1_price','plus_1_5_price','plus_2_price','percentile','report_date','model_date','availability_basis','source_url','gap_reason','view_mode','combine_method','contributor_count','min_age_days','max_age_days','min_contributor_eps','max_contributor_eps','analyst_eps_sample_std','contributor_series_ids','contributor_source_urls','composition_changed','entered_series_ids','left_series_ids','selected_series_ids','require_verified_availability','effective_used_from','verified_available_by','availability_evidence_url','first_observed_at','price_source_url','price_source_sha256','price_adjustment_basis'];
  const quote = (v: unknown) => '"'+String(v ?? '').replaceAll('"','""')+'"';
  return [fields, ...points.map(p => [company.symbol,p.ensemble?`${p.ensemble.method} · ${p.ensemble.group}`:series?.label,p.date,p.price,company.currency,p.eps,p.multiple,settings.window,p.count,p.possible,p.median,p.std,...[-2,-1.5,-1,0,1,1.5,2].map(k=>bandValue(p,k,'price')),p.percentile,p.snapshot?.report_date,p.snapshot?.model_date,p.snapshot?.availability_basis,p.snapshot?.source_url,p.reason,settings.mode||'single',p.ensemble?.method,p.ensemble?.contributors.length,p.ensemble?.minAge,p.ensemble?.maxAge,p.ensemble?.minEps,p.ensemble?.maxEps,p.ensemble?.disagreementStd,p.ensemble?JSON.stringify(p.ensemble.contributors.map(c=>c.seriesId)):'',p.ensemble?JSON.stringify(p.ensemble.contributors.map(c=>c.snapshot.source_url)):'',p.ensemble?.compositionChanged,p.ensemble?JSON.stringify(p.ensemble.added):'',p.ensemble?JSON.stringify(p.ensemble.removed):'',settings.estimatorIds===undefined?'auto':JSON.stringify(settings.estimatorIds),settings.strict,p.snapshot?(settings.strict?verifiedFrom(p.snapshot):p.snapshot.available_date):null,p.snapshot?.verified_available_at,p.snapshot?.availability_evidence_url,p.snapshot?.first_observed_at,pricesByDate.get(p.date)?.source_url,pricesByDate.get(p.date)?.source_sha256,pricesByDate.get(p.date)?.adjustment_basis])].map(row=>row.map(quote).join(',')).join('\n');
}
export function visiblePrices(prices: Price[], asOf: string, days: number): Price[] {
  return prices.filter(p => p.date <= asOf && (!days || daysBetween(asOf,p.date) <= days));
}

// Choose one series for the view, using only data available by the as-of date.
// Changing the lookback window does not splice or select different analysts.
export function bestSeries(company: Company, asOf: string): Series|undefined {
  return company.series.map(series => {
    const points=calculate(company,series,{window:365,maxAge:180,strict:false,asOf}), last=points.at(-1);
    return {series,current:last?.multiple!=null?(last.median!=null?2:1):0,coverage:points.filter(p=>p.multiple!==null).length};
  }).sort((a,b)=>b.current-a.current||b.coverage-a.coverage||Number(b.series.accounting_basis==='adjusted_diluted')-Number(a.series.accounting_basis==='adjusted_diluted'))[0]?.series;
}

export function priceVsMedian(point: ValuationPoint|undefined): number|null {
  if (!point) return null;
  const implied=bandValue(point,0,'price');
  return implied===null?null:100*(point.price/implied-1);
}
