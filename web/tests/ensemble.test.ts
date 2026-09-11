import { describe, expect, it } from 'vitest';
import { bandValue, calculate, csvExport, median, sampleStd, shiftDate } from '../src/engine';
import { calculateEnsemble, compatibility, compatibleSeries, contributionCsv } from '../src/ensemble';
import type { Company, Series, Settings, Snapshot } from '../src/types';
const model=(id:string,eps:number,date='2024-01-01'):Snapshot=>({id,kind:'ntm',report_date:date,model_date:date,available_date:shiftDate(date,1),availability_basis:'printed_report_date_assumption',share_basis_date:date,source_url:`https://example.test/${id}`,source_file:id,source_sha256:id,estimates:[{observation_id:id,fiscal_period:'NTM',fiscal_period_start:'',fiscal_period_end:'',eps,source_page:'1'}]});
const makeSeries=(id:string,eps:number):Series=>({id,label:id,analyst:id,firm:'Research '+id,accounting_basis:'reported_diluted',series_type:'individual_analyst_forecast',currency:'USD',coverage_note:'Test only',snapshots:[model(id,eps)]});
const a=makeSeries('A',1),b=makeSeries('B',3),c=makeSeries('C',10);
const company=(series:Series[]=[a,b,c]):Company=>({id:'fixture',symbol:'FIX',name:'Test only',exchange:'TEST',currency:'USD',prices:Array.from({length:60},(_,i)=>({date:shiftDate('2024-01-02',i),close:30+i,currency:'USD',adjustment_basis:'split_adjusted_to_cutoff',source_url:'https://example.test/price',source_sha256:'test'})),splits:[],series,gaps:[],forecast_count:0});
const options={asOf:'2024-03-31',window:365,maxAge:180,strict:false};
describe('compatible forecast ensembles',()=>{
  it('aggregates forecasts before calculating historical P/E and price bands',()=>{
    const co=company(),points=calculateEnsemble(co,a,co.series,options),p=points[25];
    expect(p.eps).toBe(3);expect(p.multiple).toBe(55/3);
    const ratios=co.prices.slice(0,25).map(p=>p.close/3);
    expect(p.median).toBe(median(ratios));expect(p.std).toBe(sampleStd(ratios));
    expect(bandValue(p,2,'price')).toBeCloseTo(3*(median(ratios)+2*sampleStd(ratios)));
    expect(p.ensemble?.disagreementStd).toBeCloseTo(sampleStd([1,3,10]));
    expect(p.ensemble?.contributors).toHaveLength(3);
    expect(calculateEnsemble(co,a,co.series,options,'mean')[25].eps).toBeCloseTo(14/3);
  });
  it('uses only then-available members, records entry/exit and excludes today from references',()=>{
    const later={...b,snapshots:[model('b-later',3,'2024-01-20')]},co=company([a,later]);
    const points=calculateEnsemble(co,a,co.series,{...options,maxAge:30});
    expect(points[18].eps).toBe(1);expect(points[18].ensemble?.contributors).toHaveLength(1);
    expect(points[19].eps).toBe(2);expect(points[19].ensemble?.added).toEqual(['B']);
    expect(points[20].median).toBe(median(co.prices.slice(0,20).map((p,i)=>p.close/(i<19?1:2))));
    expect(points[30].ensemble?.removed).toEqual(['A']);expect(points[30].eps).toBe(3);
    expect(points[48].eps).toBe(3);expect(points[49].eps).toBeNull();
  });
  it('is unchanged by adding a future model or future analyst',()=>{
    const co=company([a,b]);const original=calculateEnsemble(co,a,co.series,{...options,asOf:'2024-01-15'});
    const future={...c,snapshots:[model('future',999,'2024-02-01')]};
    const changed=calculateEnsemble(company([a,{...b,snapshots:[...b.snapshots,model('b-future',100,'2024-02-01')]},future]),a,[a,b,future],{...options,asOf:'2024-01-15'});
    expect(changed.map(p=>[p.eps,p.multiple,p.median,p.ensemble?.contributors])).toEqual(original.map(p=>[p.eps,p.multiple,p.median,p.ensemble?.contributors]));
  });
  it('does not roll back a newer model when an old numerical model is reprinted',()=>{
    const fresh=model('fresh',4,'2024-01-10'),reprint={...a.snapshots[0],id:'reprint',report_date:'2024-01-20',available_date:'2024-01-21'};
    const s={...a,snapshots:[a.snapshots[0],fresh,reprint]},co=company([s]);
    expect(calculateEnsemble(co,s,[s],options)[25].eps).toBe(4);
    expect(calculate(co,s,options)[25].snapshot?.id).toBe('fresh');
  });
  it('gives each analyst and same-firm reprinted model only one vote',()=>{
    const duplicate={...b,id:'A-copy',analyst:' a ',snapshots:[model('new-a',5,'2024-01-03')]};
    const coauthor={...b,id:'coauthor',firm:a.firm,snapshots:[{...a.snapshots[0],id:'reprint-copy',source_sha256:'another-pdf'}]};
    const co=company([a,duplicate,coauthor,c]),p=calculateEnsemble(co,a,co.series,options)[10];
    expect(p.ensemble?.contributors.filter(c=>c.analyst.trim().toLowerCase()==='a')).toHaveLength(1);
    expect(p.ensemble?.exclusions.some(x=>x.reason.includes('Duplicate analyst'))).toBeTruthy();
    const printed=company([a,coauthor]);
    expect(calculateEnsemble(printed,a,printed.series,options)[5].ensemble?.contributors).toHaveLength(1);
    const successor={...coauthor,snapshots:[model('successor',8,'2024-01-03')]},handover=company([a,successor]);
    const latest=calculateEnsemble(handover,a,handover.series,options)[5];
    expect(latest.ensemble?.contributors).toHaveLength(1);expect(latest.eps).toBe(8);
    const team={...successor,series_type:'named_analyst_team',analyst:'A; Successor'},joint=company([a,team]);
    const joined=calculateEnsemble(joint,a,joint.series,options)[5];
    expect(joined.ensemble?.contributors).toHaveLength(1);expect(joined.eps).toBe(8);
  });
  it('excludes consensus, mismatched currency and unresolved cross-series definitions',()=>{
    const consensus={...b,series_type:'published_consensus'},foreign={...c,currency:'EUR'},unknown={...makeSeries('unknown',4),accounting_basis:'diluted_adjustment_basis_unresolved'};
    const co=company([a,consensus,foreign,unknown]);
    expect(compatibleSeries(co,a)).toEqual([a]);
    expect(calculateEnsemble(co,a,co.series,options)[5].ensemble?.contributors).toHaveLength(1);
    expect(compatibility(co,unknown).key).not.toBe(compatibility(co,{...unknown,id:'other-unknown'}).key);
    expect(compatibility(co,{...a,accounting_basis:'adjusted_diluted'}).key).not.toBe(compatibility(co,{...b,accounting_basis:'adjusted_diluted'}).key);
  });
  it('normalizes each split basis before averaging and retains negative contributions',()=>{
    const before={...a,snapshots:[model('before',40)]},after={...b,snapshots:[model('after',-2,'2024-01-10')]};
    const co={...company([before,after]),splits:[{effective_date:'2024-01-10',ratio:10,source_url:'https://example.test/split'}]};
    const p=calculateEnsemble(co,before,co.series,options)[20];
    expect(p.ensemble?.contributors.map(c=>c.eps)).toEqual([4,-2]);expect(p.eps).toBe(1);expect(p.multiple).toBe(50);
    const negative={...after,snapshots:[model('negative',-20,'2024-01-10')]};
    const loss=calculateEnsemble({...co,series:[before,negative]},before,[before,negative],options)[20];
    expect(loss.eps).toBe(-8);expect(loss.multiple).toBeNull();expect(loss.reason).toContain('negative');
  });
  it('leaves empty selections and strict unverified availability as explicit gaps',()=>{
    const co=company();expect(calculateEnsemble(co,a,[],options)[25].eps).toBeNull();
    const strict=calculateEnsemble(co,a,co.series,{...options,strict:true})[25];
    expect(strict.eps).toBeNull();expect(strict.ensemble?.exclusions.every(x=>x.reason.includes('not been verified'))).toBeTruthy();
  });
  it('admits only the exact model snapshots approved by a reviewed compatibility rule',()=>{
    const group={id:'reviewed',label:'Reviewed test group',note:'Test evidence',evidence_url:'https://example.test/proof',approved_snapshot_ids:['A','B']};
    const first={...a,accounting_basis:'unresolved',compatibility_group:group};
    const second={...b,accounting_basis:'other wording',compatibility_group:group,snapshots:[b.snapshots[0],model('not-reviewed',9,'2024-01-20')]};
    const co=company([first,second]);
    expect(compatibleSeries(co,first)).toHaveLength(2);
    const points=calculateEnsemble(co,first,co.series,options);
    expect(points[10].eps).toBe(2);expect(points[25].eps).toBe(1);
    expect(points[25].ensemble?.exclusions[0].reason).toContain('outside the reviewed compatibility scope');
  });
  it('rejects incompatible fiscal calendars without choosing one by row order',()=>{
    const annual=(id:string,offset:boolean):Series=>({...makeSeries(id,1),snapshots:[{...model(id,1),kind:'annual',estimates:offset?[{observation_id:'x',eps:1,fiscal_period:'FY24',fiscal_period_start:'2023-07-01',fiscal_period_end:'2024-06-30',source_page:'1'},{observation_id:'y',eps:2,fiscal_period:'FY25',fiscal_period_start:'2024-07-01',fiscal_period_end:'2025-06-30',source_page:'1'}]:[{observation_id:'x',eps:1,fiscal_period:'FY24',fiscal_period_start:'2024-01-01',fiscal_period_end:'2024-12-31',source_page:'1'},{observation_id:'y',eps:2,fiscal_period:'FY25',fiscal_period_start:'2025-01-01',fiscal_period_end:'2025-12-31',source_page:'1'}]}]});
    const x=annual('x',false),y=annual('y',true),co=company([x,y]);
    const p=calculateEnsemble(co,x,[x,y],options)[5];expect(p.eps).toBeNull();expect(p.ensemble?.exclusions.every(x=>x.reason.includes('fiscal periods'))).toBeTruthy();
  });
  it('never splices incomplete annual models or falls back to an older complete snapshot',()=>{
    const complete:Snapshot={...model('complete',1),kind:'annual',estimates:[{observation_id:'x',eps:1,fiscal_period:'FY24',fiscal_period_start:'2024-01-01',fiscal_period_end:'2024-12-31',source_page:'1'},{observation_id:'y',eps:2,fiscal_period:'FY25',fiscal_period_start:'2025-01-01',fiscal_period_end:'2025-12-31',source_page:'1'}]};
    const incomplete={...complete,id:'incomplete',model_date:'2024-01-20',report_date:'2024-01-20',available_date:'2024-01-21',estimates:complete.estimates.slice(0,1)};
    const s={...a,snapshots:[complete,incomplete]},co=company([s]);
    expect(calculateEnsemble(co,s,[s],options)[25].eps).toBeNull();
  });
  it('exports membership, exclusions, model ages and sources without a fabricated single source',()=>{
    const co=company(),points=calculateEnsemble(co,a,co.series,options);
    const settings:Settings={...options,company:'fixture',series:'A',display:0,metric:'price',bands:[1,1.5,2],mode:'ensemble',combine:'median'};
    expect(points[25].snapshot).toBeNull();
    expect(csvExport(points,co,a,settings)).toContain('"contributor_source_urls"');
    const csv=contributionCsv(points);expect(csv).toContain('"mean_weight"');expect(csv).toContain('https://example.test/B');expect(csv).toContain('"model"');
  });
});
