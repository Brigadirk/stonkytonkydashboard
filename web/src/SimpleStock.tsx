import { useMemo } from 'react';
import Chart from './Chart';
import HistoryControl from './HistoryControl';
import { daysBetween, priceVsMedian } from './engine';
import { projectedChange, projectedPrice, type Projection } from './projection';
import type { Company, Settings, ValuationPoint } from './types';

const format=(value:number|null|undefined,digits=2)=>value==null?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:digits}).format(value);
const date=(value:string|undefined)=>value?new Date(value+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'No price available';
const levels=[-2,-1.5,-1,0,1,1.5,2];
const bands=[1,1.5,2];
const levelLabel=(sigma:number)=>sigma===0?'Median':`${sigma>0?'+':'−'}${Math.abs(sigma)}σ`;

export default function SimpleStock({company,points,curve,settings,onChange}:{company:Company;points:ValuationPoint[];curve:Projection[];settings:Settings;onChange:(patch:Partial<Settings>)=>void}) {
  const current=points.at(-1),target=curve.at(-1)||null,sigma=settings.targetSigma||0;
  const price=projectedPrice(target,sigma),change=projectedChange(target,sigma),digits=company.currency==='KRW'?0:2;
  const entry=priceVsMedian(current);
  // Display history independently of entry and target valuation references.
  // Missing historical forecasts stay missing even when more prices are shown.
  const history=useMemo(()=>points.filter(p=>current&&(!settings.display||daysBetween(current.date,p.date)<=settings.display)),[points,current,settings.display]);
  const projections=useMemo(()=>[{id:target?.id||'primary',label:target?.label||'',points:curve}],[curve,target]);
  return <section className="simple-stock" data-testid="simple-stock">
    <div className="simple-prices">
      <div className="simple-price-now"><span>Price now</span><strong data-testid="simple-current">{format(current?.price,digits)} <small>{company.currency}</small></strong><p>Last close · {date(current?.date)}</p></div>
      <div className="simple-price-target"><span>1-year target · {levelLabel(sigma)}</span><strong data-testid="simple-target">{format(price,digits)} <small>{company.currency}</small></strong><p>{target?date(target.target):'Target unavailable'}{change!==null&&<> <span className={`simple-change ${change<0?'negative':''}`} data-testid="simple-change">{change>0?'+':''}{format(change,1)}%</span></>}</p><p>Based on 1-year valuation history</p></div>
    </div>
    <div className="simple-stock-controls">
      <div><span className="control-label">Entry comparison{![90,180,365].includes(settings.window)&&` · ${settings.window} days`}</span><div className="segmented" role="group" aria-label="Historical window">{[90,180,365].map(window=><button key={window} className={settings.window===window?'selected':''} aria-pressed={settings.window===window} onClick={()=>onChange({window})}>{window===365?'1 year':`${window} days`}</button>)}</div></div>
      <div className="entry-position"><span className="control-label">Today vs the {settings.window}-day median valuation</span><strong data-testid="entry-comparison">{entry===null?'Comparison unavailable':Math.abs(entry)<0.05?'At usual valuation':`${format(Math.abs(entry),1)}% ${entry<0?'below':'above'} usual`}</strong></div>
    </div>
    <div className="target-levels" role="group" aria-label={`All 1-year targets in ${company.currency}`}>
      {levels.map(level=>{
        const value=projectedPrice(target,level),change=projectedChange(target,level);
        return <button key={level} className={`target-level ${level===sigma?'selected':''}`} data-sigma={level} aria-pressed={level===sigma} aria-label={`Highlight ${levelLabel(level)} target`} title={value===null?target?.reason||'This valuation level has no positive price target':`${levelLabel(level)} target for ${date(target?.target)} · ${company.currency}`} onClick={()=>onChange({targetSigma:level})}>
          <span className="target-level-label">{levelLabel(level)}</span>
          <strong className="target-level-price">{format(value,digits)}</strong>
          <span className={`target-level-change ${change!==null&&change<0?'negative':''}`}>{change===null?'Unavailable':`${change>0?'+':''}${format(change,1)}%`}</span>
        </button>;
      })}
    </div>
    {price===null&&<p className="simple-gap" role="status">{!current?'There are no saved prices for this date.':target?.reason?'There isn’t enough usable forecast data for this target.':'No positive price target is available at this deviation.'} Advanced shows the details.</p>}
    <section className="card simple-chart-card" aria-label="Price and possible future values">
      <div className="simple-history-toolbar"><HistoryControl value={settings.display} onChange={display=>onChange({display})}/></div>
      <div className="simple-chart-legend"><span><i className="legend-price"/>Actual price</span><span><i className="simple-range"/>{settings.window}-day entry bands</span><span><i className="legend-median"/>Projected bands · 1-year reference</span></div>
      {history.length?<Chart simple points={history} metric="price" bands={bands} currency={company.currency} chartKey={`simple-${company.id}-${target?.id}-${current?.date}-${settings.display}`} projections={projections} targetSigma={sigma}/>:<div className="empty-chart">No saved prices for this date.</div>}
    </section>
  </section>;
}
