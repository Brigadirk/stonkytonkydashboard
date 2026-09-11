import { projectedChange, projectedPrice, type Projection } from './projection';
import { verifiedFrom } from './engine';
import type { Company } from './types';

const number=(v:number|null|undefined,digits=2)=>v==null?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:digits}).format(v);
export default function ProjectionPanel({company,projection,originProjection,onExport,sigma,onSigma}:{company:Company;projection:Projection|null;originProjection:Projection|null;onExport:()=>void;sigma:number;onSigma:(sigma:number)=>void}) {
  if(!projection)return null;
  const p=projection, change=projectedChange(p,sigma), digits=company.currency==='KRW'?0:2;
  const ages=p.members.map(m=>m.age);
  return <section className="projection-panel" data-testid="projection-panel">
    <div className="section-heading"><h2>One year ahead · {p.target}</h2><button className="text-button" onClick={onExport}>Export projection data ↓</button></div>
    <p className="view-caption">Forecasts available at the {p.origin} close · earnings expected from {p.earningsStart} to {p.earningsEnd} · {p.label}</p>
    <p className="view-caption">Target valuation uses {p.window} days of history. Changing the entry window only changes the historical entry comparison.</p>
    <p className="projection-timing">Observed close: {number(p.currentPrice,digits)} {company.currency}. Median valuation at that same date: {number(projectedPrice(originProjection,0),digits)} {company.currency}. The targets below are for <strong>{p.target}</strong>, twelve months later.</p>
    <label className="scenario-select">Target valuation scenario<select aria-label="Target valuation scenario" value={sigma} onChange={e=>onSigma(Number(e.target.value))}>{[-2,-1.5,-1,0,1,1.5,2].map(k=><option key={k} value={k}>{k===0?'Median multiple':`${k>0?'+':'−'}${Math.abs(k)}σ multiple`}</option>)}</select></label>
    <div className="metrics-grid">
      {[-2,0,2].map(k=><div className="metric" key={k}><span>{k===0?`1-YEAR ${sigma===0?'MEDIAN':`${sigma>0?'+':'−'}${Math.abs(sigma)}σ`} TARGET`:`1-YEAR PRICE AT ${k>0?'+':'−'}2σ`}</span><strong>{number(projectedPrice(p,k===0?sigma:k),digits)} <small>{company.currency}</small></strong><p>{k===0?`${p.count} usable / ${p.possible} prior sessions`:`Future forward EPS × (historical median P/E ${k>0?'+':'−'} 2σ)`}{!p.reason&&projectedPrice(p,k===0?sigma:k)===null?' · Non-positive multiple omitted':''}</p></div>)}
      <div className="metric"><span>PROJECTED CHANGE</span><strong>{change===null?'—':`${change>0?'+':''}${number(change,1)}%`}</strong><p>Selected target versus the {p.origin} close of {number(p.currentPrice,digits)} {company.currency}</p></div>
    </div>
    {p.reason&&<p className="gap-text" role="status">{p.reason}</p>}
    <details className="projection-evidence"><summary>Projection earnings, models and missing targets</summary>
      <p>Current forward EPS: {number(p.currentEps)} {company.currency}. Forward EPS at the target date, estimated at the origin: {number(p.eps)} {company.currency}. Historical median P/E: {number(p.median)}×; sample SD: {number(p.std)}×. The {p.window}-day reference ends before the origin close and stays fixed throughout the projection.</p>
      <p>{p.members.filter(m=>m.eps!==null).length} / {p.members.length} origin contributors cover the future interval. {ages.length>0&&`Model ages at origin: ${Math.min(...ages)}–${Math.max(...ages)} days.`} {p.method!=='single'&&'The combined projection requires every origin contributor; change your selection to recompute the entire comparison with a different membership.'}</p>
      {p.method!=='single'&&<p>Disagreement between future EPS estimates: {number(p.disagreementStd)} {company.currency} sample SD. This is separate from the historical P/E variation shown by the price bands.</p>}
      <div className="table-scroll"><table><thead><tr><th>Estimator / basis</th><th>Future forward EPS</th><th>Model / age at origin</th><th>Forecast coverage / evidence</th></tr></thead><tbody>{p.members.map(m=><tr key={m.seriesId}><td>{m.label}<small>{company.series.find(s=>s.id===m.seriesId)?.accounting_basis.replaceAll('_',' ')}</small></td><td>{number(m.eps)} {company.currency}{m.reason&&<small className="gap-text">{m.reason}</small>}</td><td>{m.snapshot.model_date||'Model date not supplied'}<small>Report {m.snapshot.report_date} · {m.age} days from {m.ageBasis} date</small><small>Eligible from {p.strict?verifiedFrom(m.snapshot):m.snapshot.available_date}</small></td><td>{m.missingIntervals.length?m.missingIntervals.map(g=><small className="gap-text" key={g.start}>Missing {g.start} through {g.end}</small>):<small>Complete target interval</small>}<a href={m.snapshot.source_url} target="_blank" rel="noreferrer">Original model ↗</a><small>Retained targets: {m.snapshot.estimates.map(e=>e.fiscal_period).join(', ')}</small></td></tr>)}</tbody></table></div>
      {p.exclusions.length>0&&<details><summary>{p.exclusions.length} series excluded at the origin</summary><ul>{p.exclusions.map(x=><li key={x.seriesId}>{x.label}: {x.reason}</li>)}</ul></details>}
    </details>
  </section>;
}
