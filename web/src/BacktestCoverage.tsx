import type { BacktestReadiness } from './readiness';

export default function BacktestCoverage({report,onExport}:{report?:BacktestReadiness;onExport:(filename:string,contents:string,type:string)=>void}) {
  if(!report)return null;
  // This selects the most covered series for a coverage table only. It is not
  // an analyst selection rule for simulated trades.
  const companies=[...new Set(report.series.map(s=>s.company_id))].map(id=>report.series.filter(s=>s.company_id===id).sort((a,b)=>b.reconstructed_band_sessions-a.reconstructed_band_sessions)[0]);
  return <section className="card tab-card">
    <h2>Backtest readiness</h2>
    <p>{report.status==='not_ready'?'The archive does not yet support a verified historical trading test.':'Some verified history is present; the study design still needs review.'} The table shows the most covered individual series for each company from {report.start} to {report.as_of}, using both 180- and 365-day bands.</p>
    <div className="table-scroll"><table><thead><tr><th>Company / series</th><th className="numeric">Sessions with both bands</th><th className="numeric">Full reference windows</th><th className="numeric">Verified full windows</th><th className="numeric">Longest band gap</th></tr></thead><tbody>{companies.map(s=><tr key={s.company_id}><td>{s.company_name}<small>{s.series_label}</small></td><td className="numeric">{s.reconstructed_band_sessions} / {s.sessions}</td><td className="numeric">{s.full_reference_sessions}</td><td className="numeric">{s.verified_full_reference_sessions}</td><td className="numeric">{s.longest_gap_sessions} sessions</td></tr>)}</tbody></table></div>
    <p className="fine-print">Full reference windows require EPS on every retained price session in each window. Verified windows also require availability evidence reached by each historical date. The table selects by coverage only; no returns or analyst accuracy are ranked.</p>
    <details><summary>What the performance test still needs</summary><ul>{report.limitations.map(item=><li key={item}>{item}</li>)}</ul></details>
    <button className="text-button" onClick={()=>onExport('backtest-readiness.json',JSON.stringify(report,null,2),'application/json')}>Export every series ↓</button>
  </section>;
}
