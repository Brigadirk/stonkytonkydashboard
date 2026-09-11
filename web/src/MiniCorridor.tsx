import { bandValue } from './engine';
import { chartCalendar } from './chartCalendar';
import { projectedPrice } from './projection';
import type { OverviewView } from './overviewModel';

const levels=[-2,-1.5,-1,0,1,1.5,2];
export function corridorDomain(views:OverviewView[]):[number,number] {
  const values=views.flatMap(v=>[...v.history.flatMap(p=>[p.price,...levels.map(k=>bandValue(p,k,'price'))]),...v.curve.flatMap(p=>levels.map(k=>projectedPrice(p,k)))]).filter((v):v is number=>v!==null&&Number.isFinite(v));
  if(!values.length)return [0,1];
  const low=Math.min(...values),high=Math.max(...values),padding=(high-low||high||1)*0.08;
  return [Math.max(0,low-padding),high+padding];
}
export default function MiniCorridor({view,currency,sigma,domain}:{view:OverviewView;currency:string;sigma:number;domain:[number,number]}) {
  const p=view.projection;
  if(!p||!view.history.length)return <div className="mini-empty">No retained prices</div>;
  const calendar=chartCalendar(view.history),end=calendar.position(p.target),left=8,right=310,top=10,bottom=115;
  const x=(date:string)=>left+calendar.position(date)/(end||1)*(right-left);
  const y=(value:number)=>bottom-(value-domain[0])/(domain[1]-domain[0])*(bottom-top);
  const path=(values:{date:string;value:number|null}[])=>{
    let connected=false;
    return values.map(v=>{
      if(v.value===null||!Number.isFinite(v.value)){connected=false;return '';}
      const command=connected?'L':'M';connected=true;
      return `${command}${x(v.date).toFixed(2)},${y(v.value).toFixed(2)}`;
    }).join(' ');
  };
  const rangePath=(values:{date:string;low:number|null;high:number|null}[])=>{
    let run:{date:string;low:number;high:number}[]=[],result='';
    const flush=()=>{if(run.length>1)result+=path(run.map(p=>({date:p.date,value:p.high})))+' '+path([...run].reverse().map(p=>({date:p.date,value:p.low}))).replace(/^M/,'L')+' Z ';run=[];};
    for(const point of values){if(point.low===null||point.high===null)flush();else run.push({date:point.date,low:point.low,high:point.high});}
    flush();return result;
  };
  const visibleLevels=[...new Set([-2,0,2,sigma])];
  const target=projectedPrice(p,sigma);
  return <svg className="mini-corridor" viewBox="0 0 320 140" role="img" aria-label={`${view.window}-day entry reference: actual prices from ${view.history[0].date} through ${p.origin}, 365-day valuation reference for targets through ${p.target}. ${target===null?'One-year target unavailable':`Selected target ${target.toFixed(2)} ${currency}`}`}>
    <title>Observed prices and historical valuation bands from {view.history[0].date} through {p.origin}. Projected valuation bands use the frozen earnings forecasts and a 365-day P/E reference through {p.target}. Open for forecasts and all valuation bands.</title>
    <rect x={x(p.origin)} y={top} width={right-x(p.origin)} height={bottom-top} fill="#805bb208"/>
    <line x1={left} x2={right} y1={bottom} y2={bottom} stroke="#dce2d6"/>
    <line x1={x(p.origin)} x2={x(p.origin)} y1={top} y2={bottom} stroke="#8c8198" strokeDasharray="2 3"/>
    <path d={rangePath(view.history.map(point=>({date:point.date,low:bandValue(point,-2,'price'),high:bandValue(point,2,'price')})))} fill="#44887e12"/>
    <path d={rangePath(view.curve.map(point=>({date:point.target,low:projectedPrice(point,-2),high:projectedPrice(point,2)})))} fill="#44887e12" data-projected-band="2"/>
    {visibleLevels.map(k=><g key={k} stroke={k===sigma?'#346a59':'#9bb5a7'} strokeWidth={k===sigma?1.8:0.7} fill="none">
      <path d={path(view.history.map(point=>({date:point.date,value:bandValue(point,k,'price')})))}/>
      <path d={path(view.curve.map(point=>({date:point.target,value:projectedPrice(point,k)})))} strokeDasharray="3 2" data-projected-sigma={k}/>
    </g>)}
    <path d={path(view.history.map(point=>({date:point.date,value:point.price})))} stroke="#ba5834" strokeWidth="1.7" fill="none" data-actual-through={p.origin}/>
    {visibleLevels.map(k=>{const value=projectedPrice(p,k);return value===null?null:<circle key={k} cx={x(p.target)} cy={y(value)} r={k===sigma?3:2} fill={k===sigma?'#346a59':'#9bb5a7'} data-target-date={p.target} data-sigma={k}/>;})}
    <text x={left} y="135" textAnchor="start">{new Date(view.history[0].date+'T12:00:00Z').toLocaleDateString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'})}</text><text x={x(p.origin)} y="135" textAnchor="middle">{p.origin.slice(0,4)}</text><text x={right} y="135" textAnchor="end">+1y</text>
  </svg>;
}
