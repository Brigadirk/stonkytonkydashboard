import { compatibility, compatibleSeries, selectedEstimators } from './ensemble';
import type { Company, Series, Settings } from './types';

export default function EstimatorControls({company,anchor,settings,onChange}:{company:Company;anchor:Series|undefined;settings:Settings;onChange:(patch:Partial<Settings>)=>void}) {
  const mode=settings.mode||'single', selected=selectedEstimators(company,anchor,settings), group=anchor?compatibility(company,anchor):null;
  const groups=[...new Map(company.series.filter(s=>compatibility(company,s).eligible).map(s=>[compatibility(company,s).key,s])).values()];
  return <section className="card estimator-controls" aria-label="Estimator selection">
    <div className="estimator-heading"><div><h2>Estimators</h2><p>Follow one model, compare independent curves, or combine compatible forecasts.</p></div><div className="segmented" aria-label="Estimator view">{[['single','One estimator'],['overlay','Overlay estimators'],['ensemble','Combined estimates']].map(([id,label])=><button key={id} className={mode===id?'selected':''} aria-pressed={mode===id} onClick={()=>{
      const fallback=id==='ensemble'&&anchor&&!compatibility(company,anchor).eligible?groups[0]:anchor;
      onChange({mode:id as Settings['mode'],series:fallback?.id||'',estimatorIds:undefined});
    }}>{label}</button>)}</div></div>
    {mode!=='single'&&<>
      {mode==='ensemble'&&<div className="ensemble-options"><label>Compatible earnings group<select aria-label="Compatible earnings group" value={group?.key||''} onChange={e=>{const s=groups.find(s=>compatibility(company,s).key===e.target.value);onChange({series:s?.id||'',estimatorIds:undefined})}}>{groups.map(s=><option key={s.id} value={compatibility(company,s).key}>{compatibility(company,s).label}</option>)}</select></label><label>Combine forecasts using<select aria-label="Combine forecasts using" value={settings.combine||'median'} onChange={e=>onChange({combine:e.target.value as Settings['combine']})}><option value="median">Median</option><option value="mean">Equal-weighted mean</option></select></label></div>}
      <p className="fine-print">{mode==='ensemble'?group?.note:'Each selected curve retains its own earnings definition, history and bands. The headline cards describe the primary series selected below.'}</p>
      {mode==='ensemble'&&<p className="fine-print">Each analyst and research firm contributes at most one model per date. The latest eligible model takes precedence, so coauthors and analyst handovers cannot give one firm extra weight.</p>}
      <div className="selection-actions"><button onClick={()=>onChange({estimatorIds:(mode==='ensemble'?compatibleSeries(company,anchor):company.series).map(s=>s.id)})}>{mode==='ensemble'?'All compatible estimators':'Select all estimators'}</button><button onClick={()=>onChange({estimatorIds:[]})}>Clear selection</button><span>{selected.filter(s=>mode!=='ensemble'||compatibleSeries(company,anchor).some(c=>c.id===s.id)).length} selected</span></div>
      <details className="estimator-list"><summary>Choose estimators and inspect compatibility</summary>{company.series.map(s=>{
        const comp=compatibility(company,s), allowed=mode==='overlay'||comp.eligible&&comp.key===group?.key;
        return <label key={s.id} className={`estimator-choice ${allowed?'':'unavailable'}`}><input type="checkbox" aria-label={`Include ${s.label}`} disabled={!allowed} checked={allowed&&selected.some(x=>x.id===s.id)} onChange={e=>onChange({estimatorIds:e.target.checked?[...selected.map(x=>x.id),s.id]:selected.filter(x=>x.id!==s.id).map(x=>x.id)})}/><span>{s.label}<small>{allowed?(mode==='overlay'?s.accounting_basis:comp.note):comp.eligible?'Different or unproven earnings definition':comp.note}</small></span></label>;
      })}</details>
    </>}
  </section>;
}
