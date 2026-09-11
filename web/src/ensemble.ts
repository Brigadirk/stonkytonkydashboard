import { calculateFromEarnings, daysBetween, epoch, forwardEps, latestSnapshot, median, sampleStd, splitFactor, verifiedFrom, DAY } from './engine.ts';
import type { CombineMethod, Company, Contribution, EnsembleDetail, Exclusion, Series, Settings, Snapshot, ValuationPoint } from './types';

const clean=(s:string)=>s.trim().toLowerCase().replace(/\s+/g,' ');
export function isIndividual(series: Series): boolean {
  return !!series.analyst.trim() && (!series.series_type || ['individual_analyst_forecast','named_analyst_team'].includes(series.series_type));
}
export interface Compatibility { key: string; label: string; note: string; eligible: boolean }
export function compatibility(company: Company, series: Series): Compatibility {
  const alone={key:`alone:${series.id}`,label:series.label,note:'The earnings definition is unresolved. This series can be used alone; cross-estimator compatibility is not established.',eligible:true};
  if (!isIndividual(series)) return {...alone,eligible:false,note:'Published consensus or unidentified contributors. View independently; excluded from analyst ensembles.'};
  if (series.currency!==company.currency) return {...alone,eligible:false,note:'Price and earnings currencies differ.'};
  if(series.compatibility_group)return {key:`reviewed:${company.id}:${series.compatibility_group.id}`,label:series.compatibility_group.label,note:series.compatibility_group.note,eligible:true};
  const kinds=[...new Set(series.snapshots.map(s=>s.kind))].sort().join(',');
  const prefix=`${company.id}:${series.currency}:${kinds}:`;
  if (series.accounting_basis==='morningstar_unadjusted_diluted') return {...alone,note:'Historical broker share denominators differ from issuer reported diluted shares. Cross-author compatibility is unproven; this series remains separate.'};
  if (series.accounting_basis==='reported_diluted') return {key:prefix+'reported_diluted',label:'Reported diluted EPS',note:'Same issuer, reported diluted earnings. Fiscal periods and split normalization are checked on every date.',eligible:true};
  if (['adjusted_diluted','non_gaap_diluted'].includes(series.accounting_basis)) return {key:prefix+clean(series.firm)+':'+series.accounting_basis,label:`${series.firm} · ${series.accounting_basis.replaceAll('_',' ')} EPS`,note:'This adjusted definition is specific to the research firm. Other firms require an explicit definition match.',eligible:true};
  return alone;
}
export function compatibleSeries(company: Company, anchor: Series | undefined): Series[] {
  if (!anchor) return [];
  const group=compatibility(company,anchor);
  return group.eligible?company.series.filter(s=>{const other=compatibility(company,s);return other.eligible&&other.key===group.key}):[];
}
export function selectedEstimators(company: Company, anchor: Series | undefined, settings: Pick<Settings,'mode'|'estimatorIds'>): Series[] {
  if (settings.mode==='single'||!settings.mode) return anchor?[anchor]:[];
  if (settings.estimatorIds!==undefined) return company.series.filter(s=>settings.estimatorIds!.includes(s.id));
  return settings.mode==='ensemble'?compatibleSeries(company,anchor):anchor?[anchor]:[];
}
// Fiscal periods that actually contribute to the same next-twelve-month interval.
// NTM exports remain separate from day-weighted annual models.
export function periodKey(snapshot: Snapshot, date: string): string {
  if (snapshot.kind==='ntm') return 'provider_ntm';
  const start=epoch(date)+DAY, current=new Date(epoch(date));
  const endDay=new Date(Date.UTC(current.getUTCFullYear()+1,current.getUTCMonth()+1,0)).getUTCDate();
  const end=Date.UTC(current.getUTCFullYear()+1,current.getUTCMonth(),Math.min(current.getUTCDate(),endDay))+DAY;
  return snapshot.estimates.filter(e=>epoch(e.fiscal_period_start)<end&&epoch(e.fiscal_period_end)+DAY>start)
    .map(e=>`${e.fiscal_period_start}/${e.fiscal_period_end}`).sort().join('|');
}
function modelFingerprint(company:Company,snapshot:Snapshot):string {
  const factor=splitFactor(company,snapshot.share_basis_date);
  // Deduplicate the same firm's identical dated model, including split-adjusted
  // reprints attributed to a successor. Coincidental values at other firms stay independent.
  return JSON.stringify([snapshot.model_date||snapshot.report_date,snapshot.kind,snapshot.estimates.map(e=>[e.fiscal_period_start,e.fiscal_period_end,Number((e.eps/factor).toPrecision(12))]).sort()]);
}
export function calculateEnsemble(company: Company, anchor: Series | undefined, selected: Series[], options: Pick<Settings,'window'|'maxAge'|'strict'|'asOf'>, method: CombineMethod='median'): ValuationPoint[] {
  const group=anchor?compatibility(company,anchor):null;
  const requested=new Set(selected.map(s=>s.id));
  let previous:string[]=[];
  return calculateFromEarnings(company,options,date=>{
    const exclusions:Exclusion[]=[], candidates:Contribution[]=[];
    for (const series of company.series) {
      const comp=compatibility(company,series);
      let reason:string|null=!comp.eligible?comp.note:!group?.eligible||comp.key!==group.key?'Different or unproven earnings definition':!requested.has(series.id)?'Not selected':null;
      const snapshot=latestSnapshot(series,date,options.strict);
      if(!reason&&options.strict&&!snapshot)reason='Original availability has not been verified by this date';
      if(!reason&&snapshot&&series.compatibility_group&&!series.compatibility_group.approved_snapshot_ids.includes(snapshot.id))reason='This numerical model is outside the reviewed compatibility scope';
      if (!reason&&snapshot) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(snapshot.share_basis_date)||!Number.isFinite(epoch(snapshot.share_basis_date))||snapshot.share_basis_date>snapshot.report_date) reason='Share basis date is missing or invalid';
        if ((snapshot.model_date||snapshot.report_date)>date) reason='Numerical model is dated after this observation';
      }
      const result=reason?{eps:null,reason}:forwardEps(company,snapshot,date,options.maxAge,options.strict);
      // A negative estimate is still a valid analyst contribution. Excluding it
      // would bias the combined forecast upward. The combined EPS gates P/E.
      if (reason||result.eps===null||!snapshot) exclusions.push({seriesId:series.id,label:series.label,reason:reason||result.reason||'No eligible forecast',snapshot});
      else candidates.push({seriesId:series.id,label:series.label,analyst:series.analyst,firm:series.firm,eps:result.eps,age:daysBetween(date,snapshot.model_date||snapshot.report_date),ageBasis:snapshot.model_date?'model':'report',snapshot});
    }
    // One vote per named analyst. Pick the latest numerical model, with a stable
    // tie-break; duplicate source series never provide extra weight.
    candidates.sort((a,b)=>(b.snapshot.model_date||b.snapshot.report_date).localeCompare(a.snapshot.model_date||a.snapshot.report_date)||b.snapshot.available_date.localeCompare(a.snapshot.available_date)||a.seriesId.localeCompare(b.seriesId));
    const byAnalyst=new Map<string,Contribution>(), byFirm=new Set<string>(), fingerprints=new Set<string>();
    for (const member of candidates) {
      const identity=clean(member.analyst), firm=clean(member.firm), fingerprint=member.snapshot.source_sha256+':'+modelFingerprint(company,member.snapshot);
      if (byAnalyst.has(identity)||byFirm.has(firm)||fingerprints.has(fingerprint)) exclusions.push({seriesId:member.seriesId,label:member.label,reason:byAnalyst.has(identity)?'Duplicate analyst; latest eligible model has one vote':byFirm.has(firm)?'Same research firm; its latest eligible model has one vote to avoid counting coauthors or analyst handovers twice':'Duplicate source and numerical model',snapshot:member.snapshot});
      else {byAnalyst.set(identity,member);byFirm.add(firm);fingerprints.add(fingerprint)}
    }
    let contributors=[...byAnalyst.values()];
    // A disagreement in fiscal calendars cannot be settled by the order of rows.
    // Exclude the whole candidate set until its periods are reconciled.
    if (new Set(contributors.map(c=>periodKey(c.snapshot,date))).size>1) {
      contributors.forEach(c=>exclusions.push({seriesId:c.seriesId,label:c.label,reason:'Selected models use different forward fiscal periods',snapshot:c.snapshot}));
      contributors=[];
    }
    contributors.sort((a,b)=>a.seriesId.localeCompare(b.seriesId));
    const values=contributors.map(c=>c.eps), ages=contributors.map(c=>c.age), ids=contributors.map(c=>c.seriesId);
    const added=ids.filter(id=>!previous.includes(id)),removed=previous.filter(id=>!ids.includes(id));
    const ensemble:EnsembleDetail={strict:options.strict,method,group:group?.label||'No compatible group',contributors,exclusions,minAge:ages.length?Math.min(...ages):null,maxAge:ages.length?Math.max(...ages):null,minEps:values.length?Math.min(...values):null,maxEps:values.length?Math.max(...values):null,disagreementStd:values.length>1?sampleStd(values):null,added,removed,compositionChanged:added.length>0||removed.length>0};
    previous=ids;
    const eps=values.length?(method==='mean'?values.reduce((a,b)=>a+b,0)/values.length:median(values)):null;
    const reason=eps===null?'No eligible selected contributors on this date':eps<=0?'Combined forward earnings are zero or negative':eps<=(company.currency==='KRW'?1:0.01)?'Combined forward earnings are too close to zero for a stable P/E':null;
    return {eps,reason,snapshot:null,ensemble};
  });
}

export function contributionCsv(points:ValuationPoint[]):string {
  const fields=['date','method','group','status','series_id','estimator','forward_eps','mean_weight','age_days','age_basis','model_date','report_date','available_date','availability_basis','source_url','source_sha256','exclusion_reason','require_verified_availability','effective_used_from','verified_available_by','availability_evidence_url'];
  const rows:unknown[][]=[fields];
  for(const p of points) {
    const e=p.ensemble;if(!e)continue;
    for(const c of e.contributors)rows.push([p.date,e.method,e.group,'included',c.seriesId,c.label,c.eps,e.method==='mean'?1/e.contributors.length:'',c.age,c.ageBasis,c.snapshot.model_date,c.snapshot.report_date,c.snapshot.available_date,c.snapshot.availability_basis,c.snapshot.source_url,c.snapshot.source_sha256,'',e.strict,e.strict?verifiedFrom(c.snapshot):c.snapshot.available_date,c.snapshot.verified_available_at,c.snapshot.availability_evidence_url]);
    for(const x of e.exclusions)rows.push([p.date,e.method,e.group,'excluded',x.seriesId,x.label,'','','','',x.snapshot?.model_date,x.snapshot?.report_date,x.snapshot?.available_date,x.snapshot?.availability_basis,x.snapshot?.source_url,x.snapshot?.source_sha256,x.reason,e.strict,x.snapshot?(e.strict?verifiedFrom(x.snapshot):x.snapshot.available_date):null,x.snapshot?.verified_available_at,x.snapshot?.availability_evidence_url]);
  }
  return rows.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\n');
}
