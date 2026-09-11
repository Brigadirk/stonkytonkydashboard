import { DAY, epoch, shiftDate } from './engine';

// Compress only the retained history. Future calendar dates still carry
// projected valuations, even though they have no observed closing prices yet.
export function chartCalendar(points:readonly {date:string;price:number}[]) {
  const observed=new Set(points.filter(p=>Number.isFinite(p.price)).map(p=>p.date));
  const dates=[...observed].sort(),first=dates[0],last=dates.at(-1);
  const missing:string[]=[];
  if(first&&last)for(let date=first;date<last;date=shiftDate(date,1)) {
    if(!observed.has(date))missing.push(date);
  }
  const position=(date:string)=>{
    // Count omitted dates strictly before this one. Valid historical closes
    // become equally spaced; future dates retain their calendar-day spacing.
    let lo=0,hi=missing.length;
    while(lo<hi){const mid=(lo+hi)>>>1;if(missing[mid]<date)lo=mid+1;else hi=mid;}
    return (epoch(date)-epoch(first||date))/DAY-lo;
  };
  const cursorDate=(date:string):string|null=>{
    if(!first||date<first)return null;
    if(date>last!||observed.has(date))return date;
    // At a collapsed interval, Plotly can round the inverse pixel conversion
    // to its final hidden day. Resolve that boundary to the next actual close.
    let lo=0,hi=dates.length;
    while(lo<hi){const mid=(lo+hi)>>>1;if(dates[mid]<date)lo=mid+1;else hi=mid;}
    return dates[lo]||null;
  };
  return {missing,position,cursorDate};
}
