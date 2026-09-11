import { median } from './engine';
import type { EpsPair } from './types';
export function summarizeAccuracy(pairs:EpsPair[]) {
  const groups=new Map<string,EpsPair[]>();
  for(const p of pairs) {
    const key=JSON.stringify([p.company_id,p.analyst,p.firm,p.accounting_basis,p.currency,p.horizon_days]);
    groups.set(key,[...(groups.get(key)||[]),p]);
  }
  return [...groups.values()].map(rows=>{
    // One outcome per issuer fiscal year in a fixed estimator/basis/horizon.
    // Reprints must not increase the apparent number of independent outcomes.
    const distinct=[...new Map(rows.map(p=>[p.fiscal_period,p])).values()],first=distinct[0];
    const apes=distinct.flatMap(p=>p.absolute_error_pct===null?[]:[p.absolute_error_pct]);
    return {analyst:first.analyst,firm:first.firm,basis:first.accounting_basis,currency:first.currency,horizon:first.horizon_days,years:distinct.length,periods:distinct.map(p=>p.fiscal_period).sort(),mae:distinct.reduce((n,p)=>n+p.absolute_error_eps,0)/distinct.length,bias:distinct.reduce((n,p)=>n+p.signed_error_eps,0)/distinct.length,medianApe:apes.length?median(apes):null,apeCount:apes.length};
  }).sort((a,b)=>a.analyst.localeCompare(b.analyst)||a.firm.localeCompare(b.firm)||a.basis.localeCompare(b.basis)||a.horizon-b.horizon);
}
