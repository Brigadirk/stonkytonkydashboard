import type { PlotlyHTMLElement } from 'plotly.js';

// Read the rendered axis conversion so cursor dates respect zoom and resize.
// Plotly's date conversion also respects hidden dates with no historical close.
type DatePlot = PlotlyHTMLElement & {
  _fullLayout?: {
    xaxis: {_offset:number;_length:number;p2d:(pixel:number)=>string};
    yaxis: {_offset:number;_length:number};
  };
  removeListener:(event:string,listener:()=>void)=>void;
};
export interface CursorReadout {text:string;kind:'close'|'scenario'|'missing'}
export function attachDateCursor(element:PlotlyHTMLElement,overlay:HTMLDivElement,line:HTMLDivElement,label:HTMLTimeElement,valueLabel:HTMLDivElement,readout:(date:string)=>CursorReadout|null,resolveDate:(date:string)=>string|null):()=>void {
  const plot=element as DatePlot;
  type Position=Pick<PointerEvent,'clientX'|'clientY'>;
  let lastPosition:Position|null=null;
  const hide=()=>{overlay.hidden=true;lastPosition=null;};
  const move=(event:Position)=>{
    const axes=plot._fullLayout;if(!axes)return;
    const box=plot.getBoundingClientRect(),x=event.clientX-box.left,y=event.clientY-box.top;
    const xa=axes.xaxis,ya=axes.yaxis;
    if(x<xa._offset||x>xa._offset+xa._length||y<ya._offset||y>ya._offset+ya._length){hide();return;}
    const rawDate=String(xa.p2d(x-xa._offset)).slice(0,10);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(rawDate)){hide();return;}
    const date=resolveDate(rawDate);
    if(date===null){hide();return;}
    lastPosition={clientX:event.clientX,clientY:event.clientY};
    overlay.hidden=false;
    line.style.left=`${x}px`;line.style.top=`${ya._offset}px`;line.style.height=`${ya._length}px`;
    label.dateTime=date;
    label.textContent=new Date(date+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
    label.style.left=`${Math.max(4,Math.min(box.width-label.offsetWidth-4,x-label.offsetWidth/2))}px`;
    label.style.top=`${Math.min(box.height-label.offsetHeight,ya._offset+ya._length+5)}px`;
    const value=readout(date);
    valueLabel.hidden=value===null;
    if(value){
      valueLabel.textContent=value.text;valueLabel.dataset.kind=value.kind;valueLabel.dataset.date=date;
      valueLabel.style.maxWidth=`${Math.max(0,xa._length-16)}px`;
      const width=valueLabel.offsetWidth;
      const preferred=x+12+width<=xa._offset+xa._length?x+12:x-width-12;
      valueLabel.style.left=`${Math.max(xa._offset+8,Math.min(xa._offset+xa._length-width-8,preferred))}px`;
      valueLabel.style.top=`${ya._offset+8}px`;
    }
  };
  const refresh=()=>{if(lastPosition)move(lastPosition);};
  const leave=(event:PointerEvent)=>{if(event.pointerType!=='touch')hide();};
  plot.addEventListener('pointermove',move,{passive:true,capture:true});
  plot.addEventListener('pointerdown',move,{passive:true,capture:true});
  plot.addEventListener('pointerleave',leave);
  plot.addEventListener('pointercancel',hide);
  plot.on('plotly_relayout',refresh);
  plot.on('plotly_afterplot',refresh);
  return ()=>{
    hide();
    plot.removeEventListener('pointermove',move,true);
    plot.removeEventListener('pointerdown',move,true);
    plot.removeEventListener('pointerleave',leave);
    plot.removeEventListener('pointercancel',hide);
    plot.removeListener('plotly_relayout',refresh);
    plot.removeListener('plotly_afterplot',refresh);
  };
}
