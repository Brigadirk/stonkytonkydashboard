import { useMemo } from 'react';
import MiniCorridor, { corridorDomain } from './MiniCorridor';
import HistoryControl from './HistoryControl';
import { overviewRows, scenarioChange, scenarioRanks } from './overviewModel';
import { priceVsMedian } from './engine';
import { projectedPrice, projectionCsv } from './projection';
import type { DashboardData, Settings } from './types';

const format=(v:number|null|undefined,digits=2)=>v==null?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:digits}).format(v);
const date=(v:string|undefined)=>v?new Date(v+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'—';
const scenario=(k:number)=>k===0?'Typical':`${k>0?'+':'−'}${Math.abs(k)}σ`;
export default function Overview({data,settings,onOpen,onChange,onExport,advanced=false}:{advanced?:boolean;data:DashboardData;settings:Settings;onOpen:(company:string,series:string,window:number)=>void;onChange:(patch:Partial<Settings>)=>void;onExport:(filename:string,contents:string)=>void}) {
  const compare=settings.compareWindows===true,second=settings.compareWindow||90,sort=settings.overviewSort||'universe';
  const primary=settings.window, secondary=second===primary?(primary===90?180:90):second;
  const windows=useMemo(()=>compare?[primary,secondary]:[primary],[compare,primary,secondary]);
  const sigma=settings.targetSigma||0;
  const rows=useMemo(()=>overviewRows(data,settings,windows),[data,settings.asOf,settings.maxAge,settings.strict,settings.company,settings.series,settings.mode,settings.combine,settings.estimatorIds,settings.display,windows]);
  const ranks=scenarioRanks(rows,0,sigma);
  const sorted=[...rows].sort((a,b)=>sort==='name'?a.company.name.localeCompare(b.company.name):sort==='upside'?(ranks.get(a.company.id)??Infinity)-(ranks.get(b.company.id)??Infinity):0);
  const exportOverview=()=>{
    const files=rows.filter(row=>row.views[0].projection).map(row=>projectionCsv(row.company,row.views[0].projection?[row.views[0].projection]:[]));
    onExport(`one-year-scenarios-${settings.asOf}.csv`,files.map((file,i)=>i?file.split('\n').slice(1).join('\n'):file).join('\n'));
  };
  return <section className="card tab-card overview-panel simple-overview">
    <div className="overview-bar">
      <HistoryControl value={settings.display} onChange={display=>onChange({display})}/>
      <div><span className="control-label">Entry comparison{![90,180,365].includes(primary)&&` · ${primary} days`}</span><div className="segmented" aria-label="Historical window">{[90,180,365].map(w=><button key={w} aria-pressed={primary===w} className={primary===w?'selected':''} onClick={()=>onChange({window:w})}>{w===365?'1 year':`${w} days`}</button>)}</div></div>
      <div><span className="control-label">Valuation{![-2,0,2].includes(sigma)&&` · ${scenario(sigma)}`}</span><div className="segmented" aria-label="Valuation scenario">{[[-2,'Low'],[0,'Typical'],[2,'High']].map(([k,label])=><button key={k} aria-pressed={sigma===k} className={sigma===k?'selected':''} title={k===0?'Historical median multiple':`${k} standard deviations from the historical median multiple`} onClick={()=>onChange({targetSigma:Number(k)})}>{label}</button>)}</div></div>
    </div>
    <div className="overview-legend"><span><i className="legend-price"/>Price</span><span><i className="legend-median"/>Entry bands</span><span><i className="legend-projected"/>Projected bands · 1-year reference</span></div>
    <div className="table-scroll"><table className="overview-table projection-overview simple-overview-table"><thead><tr><th>Company</th><th>Now / entry comparison</th><th>In 12 months</th><th>Change</th><th>Price &amp; range</th></tr></thead><tbody>{sorted.map(row=>{
      const primaryProjection=row.views[0].projection,change=scenarioChange(primaryProjection,sigma),digits=row.company.currency==='KRW'?0:2;
      const open=(window=primary)=>onOpen(row.company.id,row.series?.id||'',window);
      const domain=corridorDomain(row.views);
      return <tr key={row.company.id} data-company={row.company.id}>
        <td className="overview-stock"><button onClick={()=>open()}><strong>{row.company.name}</strong><small>{row.company.symbol} · {row.company.currency}</small></button></td>
        <td className="overview-current"><span className="cell-label">Now</span><span className="current-price" title={`Close ${primaryProjection?.origin||'unavailable'}`}>{format(primaryProjection?.currentPrice,digits)}</span>{row.views.map(view=>{
          const entry=priceVsMedian(view.history.at(-1));
          return <small key={view.window} className="overview-entry" data-entry-window={view.window}>{entry===null?'Entry comparison unavailable':`${format(Math.abs(entry),1)}% ${entry<0?'below':'above'} usual`}<span> · {view.window}d</span></small>;
        })}</td>
        {row.views.slice(0,1).map((view,i)=>{
          const p=view.projection,target=projectedPrice(p,sigma);
          return <td key={i} className="overview-future"><span className="cell-label">In 12 months</span><button className="overview-target" onClick={()=>open(view.window)} aria-label={`Open ${row.company.symbol} target`} title={p?.reason||(target===null?'This valuation level has no positive price target':`Target for ${p?.target||'unknown date'} using 1-year valuation history`)}><strong className="target-price">{format(target,digits)}</strong><small className="target-date">{p?.target?date(p.target):'No target date'}</small>{target===null&&<small className="overview-gap">Unavailable</small>}</button></td>;
        })}
        <td className="overview-change"><span className="cell-label">Change</span><span className={`target-change ${change===null?'unavailable':change<0?'negative':'positive'}`}>{change===null?'—':`${change>0?'+':''}${format(change,1)}%`}</span></td>
        <td className="overview-plot">{row.views.map((view,i)=><button key={i} className="corridor-button" onClick={()=>open(view.window)} aria-label={`Open ${row.company.symbol} ${view.window}-day chart`}>{compare&&<small>{view.window===365?'1-year':`${view.window}-day`} window</small>}<MiniCorridor view={view} currency={row.company.currency} sigma={sigma} domain={domain}/></button>)}</td>
      </tr>;
    })}</tbody></table></div>
    <div className="overview-footer"><span>Closing prices · {date(settings.asOf)}</span><span>Click a stock for details.</span></div>
    {advanced&&<section className="overview-options"><h2>Research settings</h2>
      <div className="overview-advanced-controls">
        <label>Custom entry window<input aria-label="Overview window in days" type="number" min={20} max={2192} value={primary} onChange={e=>{const n=Number(e.target.value);if(n>=20&&n<=2192)onChange({window:n})}}/></label>
        <label>Exact valuation level<select aria-label="Target valuation scenario" value={sigma} onChange={e=>onChange({targetSigma:Number(e.target.value)})}>{[-2,-1.5,-1,0,1,1.5,2].map(k=><option key={k} value={k}>{k===0?'Median multiple':`${k>0?'+':'−'}${Math.abs(k)}σ multiple`}</option>)}</select></label>
        <div><label className="check-label"><input type="checkbox" checked={compare} onChange={e=>onChange({compareWindows:e.target.checked})}/> Compare two windows</label>{compare&&<label>Second window<select aria-label="Second reference window" value={secondary} onChange={e=>onChange({compareWindow:Number(e.target.value)})}>{[90,180,365].filter(w=>w!==primary).map(w=><option key={w} value={w}>{w===365?'1 year':`${w} days`}</option>)}</select></label>}</div>
        <label>Sort by<select aria-label="Sort overview" value={sort} onChange={e=>onChange({overviewSort:e.target.value as Settings['overviewSort']})}><option value="universe">Our universe</option><option value="name">Company name</option><option value="upside">Projected upside</option></select></label>
      </div>
      <p>Entry comparisons use each selected window. Every future target uses the same 365-day valuation reference. Typical uses its median P/E; Low and High use two standard deviations below and above it. These are valuation scenarios, with no assigned probability.</p>
      <p>{settings.mode==='ensemble'?`${settings.combine==='mean'?'Equal-weighted mean':'Median'} of compatible estimators. Your current stock keeps its selected contributors; other stocks use all compatible estimators.`:'One primary earnings series per stock, held constant across windows.'} {settings.maxAge}-day age limit. {settings.strict?'Verified availability only.':'Report-date reconstruction assumptions.'} Prices are retained closes; no live feed is connected.</p>
      <div className="table-scroll"><table className="overview-evidence"><thead><tr><th>Stock / model</th><th>Model date / age</th><th>Reference coverage</th><th>Target coverage</th></tr></thead><tbody>{rows.map(row=>{
        const p=row.views[0].projection,members=p?.members||[],ages=members.map(m=>m.age),dates=[...new Set(members.map(m=>m.snapshot.model_date||m.snapshot.report_date))].sort();
        return <tr key={row.company.id}><td>{row.company.symbol}<small>{p?.label||'No model'}</small>{p?.method!=='single'&&<small>{members.length} contributors</small>}</td><td>{dates.length?dates.join(' / '):'—'}<small>{ages.length?`${Math.min(...ages)}–${Math.max(...ages)} days old`:'No eligible model'}{members.some(m=>m.snapshot.first_observed_at)?' · since capture; revision age unknown':members.some(m=>m.ageBasis==='report')?' · report date fallback':''}</small></td><td>{row.views.map(v=><small key={v.window}>Entry {v.window} days: {v.history.at(-1)?.count||0} / {v.history.at(-1)?.possible||0} sessions</small>)}<small>Target 365 days: {p?.count||0} / {p?.possible||0} sessions</small></td><td>{p?.reason||'Available'}<small>Latest close {p?.origin||'—'} · target {p?.target||'—'}</small></td></tr>;
      })}</tbody></table></div>
      <button className="text-button" onClick={exportOverview}>Export all price scenarios ↓</button>
    </section>}
  </section>;
}
