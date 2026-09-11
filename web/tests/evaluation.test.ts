import { expect,it } from 'vitest';
import { summarizeAccuracy } from '../src/evaluation';
import type { EpsPair } from '../src/types';
const base:EpsPair={company_id:'test',fiscal_period:'FY2024',analyst:'A',firm:'B',accounting_basis:'reported_diluted',currency:'USD',horizon_days:90,cutoff_date:'2024-10-01',report_date:'2024-09-01',model_date:'2024-09-01',initial_release_date:'2024-12-30',forecast_eps:3,actual_eps:2,signed_error_eps:1,absolute_error_eps:1,absolute_error_pct:50,forecast_source_url:'https://example.test/forecast',actual_source_url:'https://example.test/actual'};
it('keeps horizons and bases separate, counts fiscal years once, and excludes undefined percentage errors',()=>{
  const zero={...base,fiscal_period:'FY2025',actual_eps:0,forecast_eps:-2,signed_error_eps:-2,absolute_error_eps:2,absolute_error_pct:null};
  const rows=summarizeAccuracy([base,base,zero,{...base,horizon_days:180},{...base,accounting_basis:'adjusted_diluted'}]);
  expect(rows).toHaveLength(3);
  const summary=rows.find(s=>s.basis==='reported_diluted'&&s.horizon===90)!;
  expect(summary.years).toBe(2);expect(summary.mae).toBe(1.5);expect(summary.bias).toBe(-0.5);expect(summary.medianApe).toBe(50);expect(summary.apeCount).toBe(1);
});
