import { bestSeries, calculate, daysBetween } from './engine.ts';
import { calculateEnsemble, compatibility, selectedEstimators } from './ensemble.ts';
import { projectedPrice, projectionCurve, targetReference, TARGET_REFERENCE_DAYS, type Projection } from './projection.ts';
import type { Company, DashboardData, Series, Settings, ValuationPoint } from './types';

export interface OverviewView { window:number; history:ValuationPoint[]; curve:Projection[]; projection:Projection|null }
export interface OverviewRow {company:Company;series:Series|undefined;views:OverviewView[]}
export function overviewRows(data: DashboardData, settings: Settings, windows: number[]): OverviewRow[] {
  return data.companies.map(company=>{
    const combined=settings.mode==='ensemble';
    const eligibleCompany=combined?{...company,series:company.series.filter(s=>compatibility(company,s).eligible)}:company;
    const chosen=company.id===settings.company?eligibleCompany.series.find(s=>s.id===settings.series):undefined;
    const series=chosen||bestSeries(eligibleCompany,settings.asOf);
    const estimators=selectedEstimators(company,series,{mode:combined?'ensemble':'single',estimatorIds:company.id===settings.company?settings.estimatorIds:undefined});
    const targetOptions={...settings,mode:combined?'ensemble' as const:'single' as const,estimatorIds:estimators.map(s=>s.id),window:TARGET_REFERENCE_DAYS};
    const curve=projectionCurve(company,targetReference(company,series,targetOptions),series,targetOptions);
    const views=windows.map(window=>{
      const options={...settings,window};
      const points=combined?calculateEnsemble(company,series,estimators,options,settings.combine):calculate(company,series,options);
      const reference=points.at(-1);
      const history=points.filter(p=>reference&&(!settings.display||daysBetween(reference.date,p.date)<=settings.display));
      return {window,history,curve,projection:curve.at(-1)||null};
    });
    return {company,series,views};
  });
}
export function scenarioChange(p: Projection|null, sigma: number): number|null {
  const target=projectedPrice(p,sigma);
  return target!==null&&p!.currentPrice>0?100*(target/p!.currentPrice-1):null;
}
// These ranks compare valuation scenarios within the selected universe; they
// are neither analyst-accuracy scores nor forecasts of expected returns.
export function scenarioRanks(rows: OverviewRow[], index: number, sigma: number): Map<string,number> {
  const values=rows.flatMap(row=>{
    const change=scenarioChange(row.views[index]?.projection||null,sigma);
    return change===null?[]:[{id:row.company.id,change}];
  });
  return new Map(values.map(v=>[v.id,1+values.filter(other=>other.change>v.change).length]));
}
