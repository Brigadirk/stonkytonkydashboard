import { describe,expect,it } from 'vitest';
import { readFileSync } from 'node:fs';
import { bestSeries,shiftDate } from '../src/engine';
import { priceCorridor,priceVolatility,corridorPrice,corridorCsv,CORRIDOR_LEVELS } from '../src/corridor';
import { projectedPrice,projectValuation,targetReference,type Projection } from '../src/projection';
import type { Company,DashboardData } from '../src/types';

const origin='2024-06-30';
const fixture=():Company=>({id:'fixture',symbol:'TEST',name:'Isolated test fixture',currency:'USD',exchange:'TEST',splits:[],series:[],gaps:[],forecast_count:0,
  prices:Array.from({length:181},(_,i)=>({date:shiftDate(origin,i-180),close:100*Math.exp(.0004*i+(i%2?.01:0)),currency:'USD',adjustment_basis:'split_adjusted_to_cutoff',source_url:'https://example.test/price',source_sha256:'fixture-only'}))});
const target=(c:Company):Projection=>({id:'fixture',label:'Fixture',origin,target:'2025-06-30',earningsStart:'2025-07-01',earningsEnd:'2026-06-30',currentPrice:c.prices.at(-1)!.close,currentEps:5,eps:10,median:30,std:5,window:365,count:100,possible:125,strict:false,maxAge:180,method:'single',members:[],exclusions:[],disagreementStd:null,reason:null});

describe('anchored future price corridor',()=>{
  it('starts every level at the actual price and reaches the exact existing annual target',()=>{
    const c=fixture(),p=target(c),path=priceCorridor(c,p);
    for(const k of CORRIDOR_LEVELS){
      expect(corridorPrice(path,origin,k)).toBe(p.currentPrice);
      expect(corridorPrice(path,p.target,k)).toBe(projectedPrice(p,k));
    }
    expect(corridorPrice(path,shiftDate(origin,-1),0)).toBeNull();
    expect(corridorPrice(path,shiftDate(p.target,1),0)).toBeNull();
    expect(corridorPrice(path,shiftDate(origin,3),2)!).toBeLessThan(p.currentPrice*1.15);
    expect(projectedPrice(p,2)!).toBeGreaterThan(p.currentPrice*2);
  });
  it('uses measured return variation near the origin while preserving positive, ordered scenarios',()=>{
    const c=fixture(),p=target(c),path=priceCorridor(c,p);
    const wider=priceCorridor({...c,prices:c.prices.map((x,i)=>({...x,close:x.close*Math.exp(i%2?.03:0)}))},p);
    expect(corridorPrice(wider,shiftDate(origin,3),2)!).toBeGreaterThan(corridorPrice(path,shiftDate(origin,3),2)!);
    expect(corridorPrice(wider,shiftDate(origin,3),-2)!).toBeLessThan(corridorPrice(path,shiftDate(origin,3),-2)!);
    for(const date of path.dates){
      const values=CORRIDOR_LEVELS.map(k=>corridorPrice(path,date,k)!);
      expect(values.every(v=>Number.isFinite(v)&&v>0)).toBe(true);
      expect(values).toEqual([...values].sort((a,b)=>a-b));
    }
  });
  it('ignores later prices and retains dated source evidence for the volatility sample',()=>{
    const c=fixture(),before=priceVolatility(c,origin);
    const changed={...c,prices:[...c.prices,{...c.prices.at(-1)!,date:shiftDate(origin,1),close:1e9}]};
    expect(priceVolatility(changed,origin)).toEqual(before);
    expect(before.observations).toHaveLength(180);
    expect(before.annualStd).toBeCloseTo(before.dailyStd!*Math.sqrt(252));
    expect(before.observations.every(r=>r.to<=origin&&r.toPrice.source_sha256==='fixture-only')).toBe(true);
  });
  it('does not splice across invalid closes, duplicate dates or long missing-price intervals',()=>{
    const c=fixture(),bad=c.prices[90];
    const invalid=priceVolatility({...c,prices:c.prices.map(p=>p===bad?{...p,close:0}:p)},origin);
    expect(invalid.observations.some(r=>r.from===bad.date||r.to===bad.date)).toBe(false);
    expect(invalid.exclusions).toHaveLength(2);
    const duplicate=priceVolatility({...c,prices:[...c.prices,bad]},origin);
    expect(duplicate.observations.some(r=>r.from===bad.date||r.to===bad.date)).toBe(false);
    const gap=priceVolatility({...c,prices:c.prices.filter((_,i)=>i<70||i>90)},origin);
    expect(gap.exclusions.some(x=>x.reason.includes('7 calendar days'))).toBe(true);
  });
  it('leaves unsupported paths missing while preserving valid standalone endpoint targets',()=>{
    const c=fixture(),p=target(c),sparse=priceCorridor({...c,prices:c.prices.slice(-30)},p);
    expect(sparse.reason).toContain('60 valid');
    expect(corridorPrice(sparse,shiftDate(origin,3),2)).toBeNull();
    expect(corridorPrice(sparse,p.target,2)).toBe(projectedPrice(p,2));
    const missing=priceCorridor(c,{...p,eps:null,reason:'Missing future earnings'});
    expect(corridorPrice(missing,origin,0)).toBe(p.currentPrice);
    expect(missing.dates.slice(1).every(date=>corridorPrice(missing,date,0)===null)).toBe(true);
    const nonpositive=priceCorridor(c,{...p,median:1,std:1});
    expect(corridorPrice(nonpositive,shiftDate(origin,3),-2)).toBeNull();
  });
  it('keeps every real stock endpoint fixed and avoids NVIDIA instant repricing',()=>{
    const data:DashboardData=JSON.parse(readFileSync(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
    for(const c of data.companies){
      const s=bestSeries(c,data.cutoff),options={window:365,maxAge:180,strict:false,asOf:data.cutoff};
      const p=projectValuation(c,targetReference(c,s,options),s,options)!,path=priceCorridor(c,p);
      expect(path.reason).toBeNull();
      for(const k of CORRIDOR_LEVELS)expect(corridorPrice(path,p.target,k)).toBe(projectedPrice(p,k));
      if(c.id==='nvidia'){
        expect(corridorPrice(path,shiftDate(p.origin,3),2)!).toBeLessThan(p.currentPrice*1.25);
        expect(corridorPrice(path,shiftDate(p.origin,3),2)!).toBeGreaterThan(p.currentPrice);
      }
    }
  });
  it('exports paths as scenarios with their method, volatility inputs and price provenance',()=>{
    const c=fixture(),csv=corridorCsv(c,[priceCorridor(c,target(c))]);
    expect(csv).toContain('"illustrative_price_path"');
    expect(csv).toContain('"anchored_log_scenarios_v1"');
    expect(csv).toContain('"return_evidence_json"');
    expect(csv).toContain('https://example.test/price');
    expect(csv).toContain('"2024-07-03"');
  });
});
