import { useEffect, useRef } from 'react';
import * as Plotly from 'plotly.js-basic-dist-min';
import type { Data, Layout, PlotMouseEvent } from 'plotly.js';
import { bandValue, DAY, shiftDate } from './engine';
import { chartCalendar } from './chartCalendar';
import { projectedPrice, type Projection } from './projection';
import { attachDateCursor, type CursorReadout } from './chartDateCursor';
import type { Settings, ValuationPoint } from './types';

export const ESTIMATOR_COLORS=['#267c72','#805bb2','#287cac','#ac7432','#a54e75','#667f36','#6e6ca3','#8b6152'];
export interface Overlay { id:string; label:string; points:ValuationPoint[] }
export interface ProjectionOverlay {id:string;label:string;points:Projection[]}
export default function Chart({points,metric,bands,currency,onInspect,chartKey,overlays,projections,targetSigma=0,simple=false}:{points:ValuationPoint[];metric:Settings['metric']|'earnings';bands:number[];currency:string;onInspect?:(p:ValuationPoint)=>void;chartKey:string;overlays?:Overlay[];projections?:ProjectionOverlay[];targetSigma?:number;simple?:boolean}) {
  const ref=useRef<HTMLDivElement>(null);
  const cursorRef=useRef<HTMLDivElement>(null),cursorLineRef=useRef<HTMLDivElement>(null),cursorDateRef=useRef<HTMLTimeElement>(null);
  const cursorValueRef=useRef<HTMLDivElement>(null);
  const height=metric==='earnings'?290:metric==='price'?640:520;
  const callback=useRef(onInspect); callback.current=onInspect;
  useEffect(()=>{
    const el=ref.current!;
    const calendar=chartCalendar(points);
    const traces:Data[]=[];
    if(metric!=='earnings'&&overlays===undefined) {
      // Separate polygons for each continuous run. A missing estimate never
      // becomes a coloured bridge across an unsupported historical interval.
      for(const sigma of [...bands].sort((a,b)=>b-a)) {
        let run:ValuationPoint[]=[];
        const flush=()=>{
          if(run.length>1) traces.push({type:'scatter',mode:'lines',x:[...run.map(p=>p.date),...run.map(p=>p.date).reverse()],y:[...run.map(p=>bandValue(p,-sigma,metric)),...run.map(p=>bandValue(p,sigma,metric)).reverse()],fill:'toself',fillcolor:sigma===2?'rgba(68,136,126,0.08)':sigma===1.5?'rgba(68,136,126,0.12)':'rgba(68,136,126,0.18)',line:{width:0},hoverinfo:'skip',showlegend:false,name:`±${sigma}σ`});
          run=[];
        };
        for(const point of points) {
          if(bandValue(point,-sigma,metric)===null||bandValue(point,sigma,metric)===null) flush(); else run.push(point);
        }
        flush();
        for(const sign of [-1,1]) traces.push({type:'scatter',mode:'lines',x:points.map(p=>p.date),y:points.map(p=>bandValue(p,sigma*sign,metric)),line:{color:simple&&sigma*sign===targetSigma?'#17594f':'rgba(39,113,105,0.38)',width:simple&&sigma*sign===targetSigma?2.2:0.7,dash:sigma===1.5?'dot':'solid'},hoverinfo:'skip',connectgaps:false,showlegend:false,name:`${sign<0?'−':'+'}${sigma}σ`});
      }
      traces.push({type:'scatter',mode:'lines',x:points.map(p=>p.date),y:points.map(p=>bandValue(p,0,metric)),line:{color:'#267c72',width:!simple||targetSigma===0?2.2:1,dash:'dash'},name:'Rolling median',hovertemplate:'Median '+'%{y:,.2f} '+currency+'<extra></extra>',connectgaps:false,showlegend:false});
    }
    if(overlays)overlays.forEach((overlay,index)=>{
      const color=ESTIMATOR_COLORS[index%ESTIMATOR_COLORS.length];
      const levels=metric==='earnings'?[0]:[...bands.flatMap(k=>[-k,k]),0];
      levels.forEach(k=>traces.push({type:'scatter',mode:'lines',x:overlay.points.map(p=>p.date),y:overlay.points.map(p=>metric==='earnings'?p.eps:bandValue(p,k,metric)),line:{color,width:k===0?2:0.8,dash:k===0?'solid':Math.abs(k)===1.5?'dot':'dash'},name:`${overlay.label} · ${metric==='earnings'?'EPS':k===0?'Median price':`${k>0?'+':''}${k}σ price`}`,hovertemplate:'%{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<extra>%{fullData.name}</extra>',connectgaps:false,showlegend:false}));
    });
    if(metric!=='earnings'||overlays===undefined)traces.push({type:'scatter',mode:'lines',x:points.map(p=>p.date),y:points.map(p=>metric==='price'?p.price:metric==='multiple'?p.multiple:p.eps),line:{color:metric==='earnings'?'#267c72':'#ba5834',width:2.2},name:metric==='price'?'Share price':metric==='multiple'?'Forward P/E':'Forward EPS',customdata:points.map(p=>[p.eps,p.multiple,p.count,p.possible,p.ensemble?.contributors.length??'',p.ensemble?.minAge??'',p.ensemble?.maxAge??'']),hovertemplate:simple?'%{x|%d %b %Y}<br>Price %{y:,.2f} '+currency+'<extra></extra>':metric==='price'?'%{x|%d %b %Y}<br>Price %{y:,.2f} '+currency+`<br>${overlays?'Primary forward EPS':'Forward EPS'} %{customdata[0]:,.2f}<br>Forward P/E %{customdata[1]:.2f}×<br>Window observations %{customdata[2]} / %{customdata[3]}`+(points.some(p=>p.ensemble)?'<br>Contributors %{customdata[4]} · ages %{customdata[5]}–%{customdata[6]} days':'')+'<extra></extra>':'%{x|%d %b %Y}<br>%{y:,.2f}'+(metric==='multiple'?'×':' '+currency)+'<extra></extra>',connectgaps:false,showlegend:false});
    if(!simple&&metric==='price'&&points.some(p=>p.ensemble)) {
      const changes=points.filter(p=>p.ensemble?.compositionChanged);
      traces.push({type:'scatter',mode:'markers',x:changes.map(p=>p.date),y:changes.map(p=>p.price),marker:{color:'#805bb2',size:7,symbol:'diamond-open'},name:'Contributor change',customdata:changes.map(p=>[p.ensemble!.contributors.length]),hovertemplate:'%{x|%d %b %Y}<br>Composition changed · %{customdata[0]} contributors<br>Click to inspect<extra></extra>',showlegend:false});
    }
    const future=metric==='price'?projections?.flatMap(p=>p.points)||[]:[];
    const priceLabel=(value:number|null)=>value===null?'Unavailable':new Intl.NumberFormat('en-US',{maximumFractionDigits:currency==='KRW'?0:2}).format(value)+' '+currency;
    const closes=new Map(points.map(p=>[p.date,p]));
    const futureDates=(projections||[]).map(p=>new Map(p.points.map(point=>[point.target,point])));
    const peLabel=(multiple:number|null)=>multiple!==null&&Number.isFinite(multiple)?`${multiple.toFixed(1)}×`:'unavailable';
    const cursorReadout=(date:string):CursorReadout|null=>{
      if(metric!=='price')return null;
      const close=closes.get(date);
      if(close&&Number.isFinite(close.price))return {text:`Close · ${priceLabel(close.price)} · ${overlays?'Primary forward P/E':'Forward P/E'} ${peLabel(close.multiple)}`,kind:'close'};
      if(!points.length||date<=points.at(-1)!.date)return {text:'No recorded close',kind:'missing'};
      const datedTargets=futureDates.map(dates=>dates.get(date)).filter((p):p is Projection=>p!==undefined);
      if(!datedTargets.length)return {text:'No forecast for this date',kind:'missing'};
      const values=datedTargets.map(p=>projectedPrice(p,targetSigma)).filter((v):v is number=>v!==null);
      const atTarget=date===projections?.[0]?.points.at(-1)?.target;
      if(!values.length)return {text:atTarget?'1-year target unavailable':'Projected valuation unavailable',kind:'missing'};
      const low=Math.min(...values),high=Math.max(...values);
      const level=targetSigma===0?'Median':`${targetSigma>0?'+':'−'}${Math.abs(targetSigma)}σ`;
      const range=low===high?priceLabel(low):`${priceLabel(low)} – ${priceLabel(high)}`;
      const detail=projections!.length>1?`${values.length} of ${projections!.length} estimators`:`Forward P/E ${peLabel(datedTargets[0].median!+targetSigma*datedTargets[0].std!)}`;
      return {text:`${level} ${atTarget?'1-year target':'projected valuation'} · ${range} · ${detail}`,kind:'scenario'};
    };
    if(metric==='price')projections?.forEach((projection,index)=>{
      const color=overlays?ESTIMATOR_COLORS[index%ESTIMATOR_COLORS.length]:'#267c72';
      const end=projection.points.at(-1);
      // Extend valuation levels with the frozen forecast's rolling NTM EPS.
      // These do not start at the market close or assume a route for its price.
      if(!overlays)for(const sigma of [...bands].sort((a,b)=>b-a)){
        let run:Projection[]=[];
        const flush=()=>{
          if(run.length>1)traces.push({type:'scatter',mode:'lines',x:[...run.map(p=>p.target),...run.map(p=>p.target).reverse()],y:[...run.map(p=>projectedPrice(p,-sigma)),...run.map(p=>projectedPrice(p,sigma)).reverse()],fill:'toself',fillcolor:sigma===2?'rgba(68,136,126,0.06)':sigma===1.5?'rgba(68,136,126,0.09)':'rgba(68,136,126,0.13)',line:{width:0},hoverinfo:'skip',showlegend:false,name:`Projected ±${sigma}σ band`});
          run=[];
        };
        for(const point of projection.points){
          if(projectedPrice(point,-sigma)===null||projectedPrice(point,sigma)===null)flush();else run.push(point);
        }
        flush();
      }
      for(const k of [...new Set([...bands.flatMap(k=>[-k,k]),0])].sort((a,b)=>a-b)){
        const level=k===0?'Median':`${k>0?'+':'−'}${Math.abs(k)}σ`;
        traces.push({type:'scatter',mode:'lines',x:projection.points.map(p=>p.target),y:projection.points.map(p=>projectedPrice(p,k)),line:{color,width:k===targetSigma?2.2:k===0?1.3:0.8,dash:'dash'},name:`${projection.label} · Projected ${level} valuation`,customdata:projection.points.map(p=>[p.eps,p.median===null||p.std===null?null:p.median+k*p.std]),hovertemplate:'Valuation · %{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<br>Forward P/E %{customdata[1]:.1f}×<extra>'+level+'</extra>',connectgaps:false,showlegend:false});
      }
      if(end){
        const levels=[...new Set([...bands.flatMap(k=>[-k,k]),0])].sort((a,b)=>a-b);
        traces.push({type:'scatter',mode:'markers',x:levels.map(()=>end.target),y:levels.map(k=>projectedPrice(end,k)),marker:{symbol:'diamond',color,size:6},name:'All 12-month targets',customdata:levels.map(k=>[k===0?'Median':`${k>0?'+':'−'}${Math.abs(k)}σ`]),hovertemplate:'%{customdata[0]} target · %{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<extra></extra>',showlegend:false});
      }
      if(end)traces.push({type:'scatter',mode:!simple&&projections.length===1?'text+markers':'markers',x:[end.target],y:[projectedPrice(end,targetSigma)],text:[`12-month target<br>${priceLabel(projectedPrice(end,targetSigma))}`],textposition:'top left',textfont:{size:14,color},cliponaxis:false,marker:{symbol:'diamond',color,size:10},name:`${projection.label} · 12-month selected target`,customdata:[[targetSigma,end.origin]],hovertemplate:simple?'1-year target · %{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<extra></extra>':'Target at %{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<br>Selected historical P/E scenario: %{customdata[0]}σ<br>Forecast origin: %{customdata[1]}<extra>%{fullData.name}</extra>',showlegend:false});
    });
    const origin=future[0]?.origin, target=future.at(-1)?.target;
    if(origin&&points.length){
      const latest=points.at(-1)!;
      traces.push({type:'scatter',mode:simple?'markers':'text+markers',x:[latest.date],y:[latest.price],text:[`Close ${priceLabel(latest.price)}`],textposition:'bottom left',textfont:{size:12,color:'#ba5834'},marker:{color:'#ba5834',size:7},name:'Observed close at origin',hovertemplate:'Observed close · %{x|%d %b %Y}<br>%{y:,.2f} '+currency+'<extra></extra>',showlegend:false});
    }
    const layout:Partial<Layout>={height,margin:{l:simple?60:76,r:simple?18:28,t:35,b:simple?42:58},paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Inter, -apple-system, BlinkMacSystemFont, sans-serif',size:14,color:'#59675e'},xaxis:{type:'date',rangebreaks:calendar.missing.length?[{values:calendar.missing,dvalue:DAY}]:[],showgrid:false,zeroline:false,linecolor:'#dce1d9',tickformat:'%b %Y',nticks:7,automargin:true,range:points.length?[points[0].date,target?shiftDate(target,14):points[points.length-1].date]:undefined},yaxis:{gridcolor:'#e5e8e0',zeroline:false,tickformat:currency==='KRW'&&metric!=='multiple'?'~s':',.2~f',ticksuffix:metric==='multiple'?'×':'',rangemode:metric==='price'?'normal':'tozero',autorangeoptions:metric==='price'?{clipmin:0}:undefined,automargin:true},hoverlabel:{font:{size:14}},hovermode:'closest',dragmode:'zoom',uirevision:chartKey,
      ...(origin&&target?{shapes:[{type:'rect',xref:'x',yref:'paper',x0:origin,x1:shiftDate(target,14),y0:0,y1:1,fillcolor:'rgba(128,91,178,0.035)',line:{width:0},layer:'below'},{type:'line',xref:'x',yref:'paper',x0:origin,x1:origin,y0:0,y1:1,line:{color:'#8c8198',width:1,dash:'dot'}},{type:'line',xref:'x',yref:'paper',x0:target,x1:target,y0:0,y1:1,line:{color:'#b6c4b9',width:1,dash:'dot'},layer:'below'}],annotations:[...(simple?[{xref:'x' as const,yref:'paper' as const,x:origin,y:1.04,xanchor:'right' as const,xshift:-10,text:'Last close',showarrow:false,font:{size:13,color:'#756784'}}]:[]),{xref:'x',yref:'paper',x:target,y:1.04,xanchor:'right',text:simple?'In 1 year':`12-month target · ${target}`,showarrow:false,font:{size:simple?13:12,color:'#756784'}}]}:{})};
    let disposed=false,disposeCursor=()=>{};
    void Plotly.react(el,traces,layout,{responsive:true,displaylogo:false,displayModeBar:simple?false:undefined,scrollZoom:false,modeBarButtonsToRemove:['select2d','lasso2d'],toImageButtonOptions:{filename:`forward-${metric}`,format:'png',scale:2}}).then(()=>{
      if(disposed)return;
      const plot=el as unknown as Plotly.PlotlyHTMLElement;
      disposeCursor=attachDateCursor(plot,cursorRef.current!,cursorLineRef.current!,cursorDateRef.current!,cursorValueRef.current!,cursorReadout,calendar.cursorDate);
      plot.removeAllListeners('plotly_click');
      plot.on('plotly_click',(event:PlotMouseEvent)=>{
        const date=String(event.points[0]?.x).slice(0,10), point=points.find(p=>p.date===date);
        if(point)callback.current?.(point);
      });
    });
    const observer=new ResizeObserver(()=>{if(!disposed)void Plotly.Plots.resize(el)}); observer.observe(el);
    return ()=>{disposed=true;observer.disconnect();disposeCursor()};
  },[points,metric,bands,currency,chartKey,overlays,projections,targetSigma,simple,height]);
  useEffect(()=>()=>{if(ref.current)Plotly.purge(ref.current)},[]);
  return <div className="chart-frame">
    <div ref={ref} className="chart" style={{height}} data-testid={`chart-${metric}`} aria-label={`${metric} history chart. Historical dates without a closing price are hidden. Move across the chart to see the date${metric==='price'?', its closing price and then-available forward P/E, or a projected valuation in the future bands':''}. Drag to zoom; double-click to reset.`}/>
    <div ref={cursorRef} className="chart-date-cursor" hidden aria-hidden="true"><div ref={cursorLineRef} className="chart-cursor-line"/><time ref={cursorDateRef} className="chart-cursor-date"/><div ref={cursorValueRef} className="chart-cursor-value" hidden/></div>
  </div>;
}
