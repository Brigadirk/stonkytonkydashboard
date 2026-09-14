import type { Company } from './types';

export default function ReportedEarnings({company}:{company:Company}) {
  const records=company.reported_earnings;
  if(!records?.annual_eps.length)return null;
  return <section className="card tab-card" data-testid="reported-earnings">
    <h2>Reported annual earnings</h2>
    <p>Annual diluted EPS from company filings. Values use the share units and accounting basis in each source. These results are separate from analyst forecasts.</p>
    {records.notes.map((note,i)=><p className="fine-print" key={i}>{note}</p>)}
    <div className="table-scroll"><table><thead><tr><th>Period ending</th><th className="numeric">Diluted EPS</th><th>Unit</th><th>Filed</th><th>Source</th></tr></thead><tbody>
      {[...records.annual_eps].sort((a,b)=>b.period_end.localeCompare(a.period_end)).map((row,i)=><tr key={`${row.period_end}-${i}`}>
        <td>{row.period_end}<small>{row.period_start} to {row.period_end}</small></td>
        <td className="numeric">{new Intl.NumberFormat('en-US',{maximumFractionDigits:4}).format(row.value)}</td>
        <td>{row.unit}<small>{row.accounting_basis.replaceAll('_',' ')}</small></td>
        <td>{row.filing_date}</td>
        <td><a href={row.source_url} target="_blank" rel="noreferrer" title={row.source_locator}>Company filing ↗</a></td>
      </tr>)}
    </tbody></table></div>
    <p className="fine-print">Filing dates are not earnings announcement dates. Later filings can restate earlier results. Values have not been adjusted for stock splits after the source filing.</p>
  </section>;
}
