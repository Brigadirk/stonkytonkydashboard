const ranges=[[180,'6 months'],[365,'1 year'],[730,'2 years'],[1095,'3 years'],[1826,'5 years']] as const;

export default function HistoryControl({value,onChange,allowAll=false}:{value:number;onChange:(days:number)=>void;allowAll?:boolean}) {
  return <label className="history-control">Chart history<select aria-label="Chart history" value={value} onChange={e=>onChange(Number(e.target.value))}>
    {ranges.map(([days,label])=><option key={days} value={days}>{label}</option>)}
    {(allowAll||value===0)&&<option value={0}>All retained history</option>}
    {value!==0&&!ranges.some(([days])=>days===value)&&<option value={value}>{value} days</option>}
  </select></label>;
}
