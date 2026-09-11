import { describe, expect, it } from 'vitest';
import { bandValue, priceVsMedian } from '../src/engine';
import { buildCompanyCoverage, gapCsv, monthsBetween } from '../src/coverage';
import type { Company, Series, Snapshot, ValuationPoint } from '../src/types';

const snapshot:Snapshot={id:'feb',kind:'ntm',report_date:'2026-02-01',model_date:'2026-02-01',available_date:'2026-02-02',availability_basis:'printed_report_date_assumption',share_basis_date:'2026-02-01',source_url:'https://example.test/feb',source_file:'fixture',source_sha256:'fixture',estimates:[{observation_id:'eps',fiscal_period:'NTM',fiscal_period_start:'',fiscal_period_end:'',eps:10,source_page:'1'}]};
const series:Series={id:'selected',label:'Selected analyst',analyst:'A',firm:'Firm',currency:'USD',accounting_basis:'reported_diluted',coverage_note:'',snapshots:[snapshot]};
const company:Company={id:'fixture',name:'Fixture',symbol:'FIX',exchange:'TEST',currency:'USD',splits:[],gaps:[],forecast_count:2,series:[series,{...series,id:'other',analyst:'B',label:'Other analyst',snapshots:[{...snapshot,id:'jan',model_date:'2026-01-01',report_date:'2026-01-01',available_date:'2026-01-02'}]}],prices:['2026-01-30','2026-01-31','2026-02-01','2026-02-02','2026-02-03','2026-02-04','2026-02-05'].map(date=>({date,close:100,currency:'USD',adjustment_basis:'split_adjusted_to_cutoff',source_url:'fixture',source_sha256:'fixture'}))};
const options={asOf:'2026-02-05',window:365,maxAge:180,strict:false};

describe('monthly collection gaps',()=>{
  it('counts the selected series separately from alternatives and respects report availability',()=>{
    const result=buildCompanyCoverage(company,series,options,'2026-01-30');
    expect(result.months).toEqual([
      {month:'2026-01',sessions:2,eps_days:0,band_days:0,other_series_days:2,reasons:{no_forecast:2},new_models:0},
      {month:'2026-02',sessions:5,eps_days:4,band_days:0,other_series_days:1,reasons:{no_forecast:1},new_models:1}
    ]);
    expect(gapCsv([result])).toContain('other_series_only_sessions');
  });
  it('shows staleness, nonpositive EPS and strict availability as gaps',()=>{
    const stale=buildCompanyCoverage(company,series,{...options,maxAge:1},'2026-02-01').months[0];
    expect(stale.eps_days).toBe(1);expect(stale.reasons.stale_model).toBe(3);
    const loss={...series,snapshots:[{...snapshot,estimates:[{...snapshot.estimates[0],eps:-2}]}]};
    expect(buildCompanyCoverage(company,loss,options,'2026-02-01').months[0].reasons.nonpositive_eps).toBe(4);
    expect(buildCompanyCoverage(company,series,{...options,strict:true},'2026-02-01').months[0].eps_days).toBe(0);
  });
  it('limits sessions and newly available models to the as-of date',()=>{
    const result=buildCompanyCoverage(company,series,{...options,asOf:'2026-02-01'},'2026-01-30');
    expect(result.months[1].sessions).toBe(1);expect(result.months[1].new_models).toBe(0);
    expect(monthsBetween('2025-12-20','2026-02-01')).toEqual(['2025-12','2026-01','2026-02']);
  });
});

it('puts actual price and valuation-band prices on the same currency scale',()=>{
  // Price 300 at 18x gives EPS 16.6667. A 20x–35x two-sigma range
  // therefore implies prices 333.33–583.33, not PE values on the price axis.
  const point={price:300,eps:300/18,multiple:18,median:27.5,std:3.75} as ValuationPoint;
  expect(bandValue(point,-2,'price')).toBeCloseTo(333.333333);
  expect(bandValue(point,2,'price')).toBeCloseTo(583.333333);
  expect(priceVsMedian(point)).toBeCloseTo(-34.5454545);
});
