import { describe, expect, it } from 'vitest';
import { bandValue, calculate, forwardEps, forwardInterval, nextYear, shiftDate } from '../src/engine';
import { calculateEnsemble } from '../src/ensemble';
import { missingIntervals, projectedPrice, projectValuation, projectionCsv, projectionCurve, targetReference, TARGET_REFERENCE_DAYS } from '../src/projection';
import { readFileSync } from 'node:fs';
import { overviewRows, scenarioRanks } from '../src/overviewModel';
import type { Company, DashboardData, Series, Settings, Snapshot } from '../src/types';

const model=(id:string,values=[10,20,40],date='2024-03-01'):Snapshot=>({id,kind:'annual',report_date:date,model_date:date,available_date:shiftDate(date,1),availability_basis:'printed_report_date_assumption',share_basis_date:date,source_url:`https://example.test/${id}`,source_sha256:id,source_file:id,estimates:values.map((eps,i)=>({observation_id:`${id}-${i}`,fiscal_period:`FY${2024+i}`,fiscal_period_start:`${2024+i}-01-01`,fiscal_period_end:`${2024+i}-12-31`,eps,source_page:'1'}))});
const series=(id='A',values=[10,20,40]):Series=>({id,label:id,analyst:id,firm:`Firm ${id}`,accounting_basis:'reported_diluted',currency:'USD',coverage_note:'Isolated test fixture',snapshots:[model(`${id}-old`,values,'2024-01-01'),model(id,values)]});
const company=(ss=[series()]):Company=>({id:'test',name:'Test fixture',symbol:'TEST',exchange:'TEST',currency:'USD',splits:[],series:ss,gaps:[],forecast_count:0,prices:Array.from({length:181},(_,i)=>({date:shiftDate('2024-01-02',i),close:100+i/2,currency:'USD',adjustment_basis:'split_adjusted_to_cutoff',source_url:'https://example.test/price',source_sha256:'price'}))});
const settings:Settings={company:'test',series:'A',window:365,maxAge:180,strict:false,asOf:'2024-06-30',display:1826,metric:'price',bands:[1,1.5,2],mode:'single',combine:'median'};
const project=(c=company(),options=settings)=>projectValuation(c,calculate(c,c.series[0],options).at(-1),c.series[0],options)!;

describe('one-year-ahead valuation scenarios',()=>{
  it('uses months 13–24 and the origin historical P/E distribution, not current forward EPS',()=>{
    const c=company(),reference=calculate(c,c.series[0],settings).at(-1)!,p=project(c);
    expect(p.origin).toBe('2024-06-30');expect(p.target).toBe('2025-06-30');
    expect([p.earningsStart,p.earningsEnd]).toEqual(['2025-07-01','2026-06-30']);
    expect(p.eps).toBeCloseTo(184/365*20+181/365*40);
    expect(p.eps).not.toBeCloseTo(p.currentEps!);
    expect(p.median).toBe(reference.median);expect(p.std).toBe(reference.std);
    expect(projectedPrice(p,1.5)).toBeCloseTo(p.eps!*(reference.median!+1.5*reference.std!));
  });
  it('measures freshness and verified availability at origin, never at the future target',()=>{
    const c=company(),p=project(c);
    expect(p.members[0].age).toBe(121);expect(p.reason).toBeNull();
    expect(forwardEps(c,c.series[0].snapshots[1],p.target,180,false).eps).toBeNull();
    expect(project(c,{...settings,maxAge:90}).reason).toContain('older than 90');
    expect(project(c,{...settings,strict:true}).eps).toBeNull();
    const verified={...c,series:c.series.map(s=>({...s,snapshots:s.snapshots.map(m=>({...m,verification_kind:'verified_available_by_archive',verified_available_date:'2024-07-01',availability_evidence_url:'https://example.test/proof'}))}))};
    expect(project(verified,{...settings,strict:true}).eps).toBeNull();
  });
  it('freezes the model vintage and ignores reports released after the origin',()=>{
    const c=company(),before=project(c),later=model('future',[999,999,999],'2025-03-01');
    const changed={...c,series:[{...c.series[0],snapshots:[...c.series[0].snapshots,later]}]};
    expect(project(changed)).toEqual(before);
    const curve=projectionCurve(c,calculate(c,c.series[0],settings).at(-1),c.series[0],settings);
    expect(curve.at(-1)).toEqual(before);
    expect(new Set(curve.map(p=>p.members[0].snapshot.id))).toEqual(new Set(['A']));
    expect(new Set(curve.map(p=>p.median)).size).toBe(1);
    expect(curve.every(p=>p.members[0].age===121)).toBe(true);
  });
  it('joins the contemporaneous valuation at origin and uses later earnings only at the later endpoint',()=>{
    const c=company(),reference=calculate(c,c.series[0],settings).at(-1)!;
    const curve=projectionCurve(c,reference,c.series[0],settings),first=curve[0],last=curve.at(-1)!;
    for(const sigma of [-2,-1.5,-1,0,1,1.5,2])expect(projectedPrice(first,sigma)).toBe(bandValue(reference,sigma,'price'));
    expect(first.target).toBe(reference.date);expect(last.target).toBe(nextYear(reference.date));
    expect(first.eps).toBe(reference.eps);
    expect(curve).toHaveLength(366);
    expect(curve.every((p,i)=>p.target===shiftDate(reference.date,i))).toBe(true);
    expect(projectedPrice(last,0)).not.toBe(projectedPrice(first,0));
    expect(projectedPrice(first,0)).not.toBe(reference.price);
  });
  it('reports exact missing future dates without falling back to an older complete model',()=>{
    const s=series(),incomplete=model('latest',[10,20],'2024-04-01'),c=company([{...s,snapshots:[...s.snapshots,incomplete]}]),p=project(c);
    expect(p.members[0].snapshot.id).toBe('latest');expect(p.eps).toBeNull();
    expect(p.members[0].missingIntervals).toEqual([{start:'2026-01-01',end:'2026-06-30'}]);
    expect(projectedPrice(p,0)).toBeNull();
    const curve=projectionCurve(c,calculate(c,c.series[0],settings).at(-1),c.series[0],settings);
    expect(curve[0].eps).not.toBeNull();expect(curve.at(-1)?.eps).toBeNull();
    expect(projectedPrice(curve.find(p=>p.target==='2024-12-31')!,0)).not.toBeNull();
    expect(projectedPrice(curve.find(p=>p.target==='2025-01-01')!,0)).toBeNull();
    expect(missingIntervals({...incomplete,estimates:[incomplete.estimates[0]]},'2025-06-30')).toEqual([{start:'2025-07-01',end:'2026-06-30'}]);
  });
  it('rejects recycling a provider NTM-only value into a later earnings horizon',()=>{
    const s=series(),snap={...model('ntm',[10]),kind:'ntm' as const},c=company([{...s,snapshots:[snap]}]);
    expect(project(c).reason).toContain('NTM-only');expect(project(c).eps).toBeNull();
  });
  it('combines future earnings before applying the combined historical multiple and keeps all origin members',()=>{
    const ss=[series('A',[10,20,40]),series('B',[20,40,80]),series('C',[50,100,200])],c=company(ss);
    const median=projectValuation(c,calculateEnsemble(c,ss[0],ss,settings,'median').at(-1),ss[0],settings)!;
    const mean=projectValuation(c,calculateEnsemble(c,ss[0],ss,settings,'mean').at(-1),ss[0],settings)!;
    expect(median.members).toHaveLength(3);expect(median.eps).toBeCloseTo(project(company()).eps!*2);
    expect(mean.eps).toBeCloseTo(project(company()).eps!*8/3);
    expect(projectedPrice(mean,0)).toBeCloseTo(mean.eps!*mean.median!);
    expect(mean.disagreementStd).not.toBe(mean.std);
    const incomplete={...ss[1],snapshots:ss[1].snapshots.map(s=>({...s,estimates:s.estimates.slice(0,2)}))},partial=company([ss[0],incomplete]);
    const p=projectValuation(partial,calculateEnsemble(partial,ss[0],partial.series,settings).at(-1),ss[0],settings)!;
    expect(p.members).toHaveLength(2);expect(p.members.filter(m=>m.eps!==null)).toHaveLength(1);
    expect(p.eps).toBeNull();expect(p.reason).toContain('have not been dropped');
  });
  it('normalizes future EPS to the same split basis, retaining losses without inventing P/E',()=>{
    const c=company(),split={...c,splits:[{effective_date:'2024-05-01',ratio:10,source_url:'https://example.test/split'}]};
    expect(project(split).eps).toBeCloseTo(project(c).eps!/10);
    expect(project(split).members[0].splitFactor).toBe(10);
    const loss=project(company([series('A',[10,-20,-40])]));
    expect(loss.eps).toBeLessThan(0);expect(projectedPrice(loss,2)).toBeNull();
    expect(projectedPrice({...project(c),median:1,std:1},-2)).toBeNull();
  });
  it('uses calendar anniversaries and keeps leap-day horizon boundaries reproducible',()=>{
    expect(nextYear('2024-02-29')).toBe('2025-02-28');
    expect(forwardInterval(nextYear('2024-02-29'))).toEqual({start:'2025-03-01',end:'2026-02-28'});
  });
  it('rejects unverified price adjustment, currency mismatches and invalid forecast share bases',()=>{
    const c=company();
    const currency=project(company([{...series(),currency:'EUR'}]));
    expect(currency.eps).toBeNull();expect(currency.reason).toContain('currencies differ');
    const badPrice=project({...c,prices:c.prices.map(p=>({...p,adjustment_basis:'total_return'}))});
    expect(projectedPrice(badPrice,2)).toBeNull();expect(badPrice.reason).toContain('Price split adjustment');
    const shares=project(company([{...series(),snapshots:[{...model('bad'),share_basis_date:''}]}]));
    expect(shares.eps).toBeNull();expect(shares.reason).toContain('Share basis date');
  });
  it('exports origin, future horizon, frozen source evidence, price provenance and all scenario levels',()=>{
    const c=company(),p=project(c),csv=projectionCsv(c,[p]);
    expect(csv).toContain('"12_month_valuation_scenario"');expect(csv).toContain('"2025-07-01"');
    expect(csv).toContain('"plus_1_5_price"');expect(csv).toContain('https://example.test/A');
    expect(csv).toContain('"origin_price_source_sha256"');expect(csv).toContain('"2023-07-01"');
    expect(csv).toContain('"max_model_age_at_origin_days"');
  });
  it('changes entry windows without changing future targets and ranks only supported targets',()=>{
    const c=company(),missing=company([series('A',[10,20])]);missing.id='missing';
    const data={companies:[c,missing]} as DashboardData;
    const rows=overviewRows(data,settings,[90,180,365]);
    expect(new Set(rows[0].views.map(v=>v.projection!.target))).toEqual(new Set(['2025-06-30']));
    expect(new Set(rows[0].views.map(v=>v.projection!.eps)).size).toBe(1);
    expect(rows[0].views[0].history.at(-1)!.median).not.toBe(rows[0].views[1].history.at(-1)!.median);
    expect(rows[0].views[0].projection).toEqual(rows[0].views[1].projection);
    expect(scenarioRanks(rows,0,0)).toEqual(new Map([['test',1]]));
    expect(rows[0].views[0].history.at(-1)?.date).toBe('2024-06-30');
  });
  it('uses an independent one-year reference in single and combined modes, preserving empty selections',()=>{
    const c=company([series(),series('B',[12,26,45])]);
    for(const mode of ['single','ensemble'] as const){
      const options={...settings,mode};
      const references=[90,180,365].map(window=>targetReference(c,c.series[0],{...options,window})!);
      expect(references[0]).toEqual(references[1]);expect(references[1]).toEqual(references[2]);
      const p=projectValuation(c,references[0],c.series[0],{...options,window:TARGET_REFERENCE_DAYS})!;
      expect(p.window).toBe(365);expect(p.members).toHaveLength(mode==='ensemble'?2:1);
      expect(p.median).not.toBe(calculate(c,c.series[0],{...settings,window:90}).at(-1)!.median);
    }
    const empty=targetReference(c,c.series[0],{...settings,window:90,mode:'ensemble',estimatorIds:[]})!;
    expect(empty.ensemble!.contributors).toHaveLength(0);
    expect(projectValuation(c,empty,c.series[0],{...settings,window:365})!.eps).toBeNull();
  });
  it('keeps all real stock targets and exported target references fixed across entry windows',()=>{
    const data:DashboardData=JSON.parse(readFileSync(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
    const rows=overviewRows(data,{...settings,company:'',series:'',asOf:data.cutoff},[90,180,365]);
    expect(rows).toHaveLength(23);
    const pricedRows=rows.filter(row=>row.company.prices.length);
    expect(pricedRows).toHaveLength(23);
    expect(rows.filter(row=>projectedPrice(row.views[0].projection,0)!==null)).toHaveLength(22);
    for(const row of pricedRows){
      for(const view of row.views){
        expect(view.projection).toEqual(row.views[0].projection);
        expect(view.projection!.window).toBe(365);
        if(row.company.id==='cerebras') {
          expect(projectedPrice(view.projection,0)).toBeNull();
          expect(view.projection!.reason).toBe('No usable earnings series collected');
          expect(view.projection!.currentPrice).toBeGreaterThan(0);
        } else expect(projectedPrice(view.projection,0)).not.toBeNull();
      }
      expect(projectionCsv(row.company,[row.views[0].projection!])).toBe(projectionCsv(row.company,[row.views[2].projection!]));
    }
    expect(pricedRows.filter(row=>row.views[0].history.at(-1)!.median!==row.views[2].history.at(-1)!.median).length).toBeGreaterThan(0);
  });
});
