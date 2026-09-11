import {expect,it} from 'vitest';
import {assessSeries} from '../src/readiness';
import {shiftDate} from '../src/engine';
import type {Company,Series,Snapshot} from '../src/types';

const day=(offset:number)=>shiftDate('2024-01-01',offset);
function fixture(verified=false) {
  const snapshots:Snapshot[]=[0,90,180,270,360,450].map(offset=>({id:String(offset),kind:'ntm',report_date:day(offset-1),model_date:day(offset-1),available_date:day(offset),share_basis_date:day(offset),availability_basis:verified?'verified_available_at':'printed_report_date_assumption',source_url:'fixture',source_file:'fixture',source_sha256:'fixture',estimates:[{observation_id:String(offset),fiscal_period:'NTM',fiscal_period_start:'',fiscal_period_end:'',eps:10,source_page:'1'}]}));
  const series:Series={id:'analyst',label:'Analyst',analyst:'A',firm:'Broker',accounting_basis:'reported_diluted',currency:'USD',coverage_note:'',snapshots};
  const company:Company={id:'fixture',name:'Fixture',symbol:'FIX',exchange:'TEST',currency:'USD',splits:[],gaps:[],forecast_count:6,series:[series],prices:Array.from({length:500},(_,i)=>({date:day(i),close:100+i/10,currency:'USD',adjustment_basis:'split_adjusted_to_cutoff',source_url:'fixture',source_sha256:'fixture'}))};
  return {company,series};
}

it('separates drawable bands, complete references and verified availability',()=>{
  const {company,series}=fixture();
  const partial=assessSeries(company,series,day(20),day(40));
  expect(partial.reconstructed_band_sessions).toBe(21);
  expect(partial.full_reference_sessions).toBe(0);
  const full=assessSeries(company,series,day(365),day(499));
  expect(full.full_reference_sessions).toBe(135);
  expect(full.verified_full_reference_sessions).toBe(0);
  const verified=fixture(true);
  expect(assessSeries(verified.company,verified.series,day(365),day(499)).verified_full_reference_sessions).toBe(135);
});

it('does not fill a selected series from alternatives or future reports',()=>{
  const {company,series}=fixture();
  const sparse={...series,snapshots:[series.snapshots[0],series.snapshots[5]]};
  const result=assessSeries(company,sparse,day(365),day(449));
  expect(result.reconstructed_band_sessions).toBe(0);
  expect(result.longest_gap_sessions).toBe(85);
  expect(result.full_reference_sessions).toBe(0);
});
