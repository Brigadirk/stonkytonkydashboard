import { expect,it } from 'vitest';
import { readFileSync,writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { calculate, bandValue, verifiedFrom } from '../src/engine';
import type { DashboardData } from '../src/types';
it('replays the retained real dataset with no fabricated coverage',()=>{
 const data:DashboardData=JSON.parse(readFileSync(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
 const coverage=data.companies.map(c=>{
  const series=c.series.map(s=>{
   const points=calculate(c,s,{asOf:data.cutoff,window:365,maxAge:180,strict:false});
   const strict=calculate(c,s,{asOf:data.cutoff,window:365,maxAge:180,strict:true});
   expect(strict.every(p=>p.multiple===null||p.snapshot!==null&&verifiedFrom(p.snapshot)!==null&&verifiedFrom(p.snapshot)!<=p.date)).toBeTruthy();
   expect(points.every(p=>p.multiple===null||p.snapshot!.available_date<=p.date)).toBeTruthy();
   expect(points.every(p=>p.multiple===null||p.eps!>0)).toBeTruthy();
   return {id:s.id,label:s.label,valid_pe_days:points.filter(p=>p.multiple!==null).length,band_days:points.filter(p=>bandValue(p,0,'price')!==null).length,latest_pe:points.at(-1)?.multiple??null,latest_median:points.at(-1)?.median??null};
  });
  return {company:c.name,price_days:c.prices.length,series};
 });
 expect(coverage).toHaveLength(23);
 expect(data.companies.every(c=>c.prices.at(-1)?.date===data.cutoff)).toBeTruthy();
 expect(data.companies.filter(c=>!c.series.length).map(c=>c.id)).toEqual(['cerebras']);
 expect(coverage.filter(c=>c.series.some(s=>s.band_days>0)).length).toBe(22);
 expect(data.companies.filter(c=>c.reported_earnings?.annual_eps.length)).toHaveLength(13);
 expect(data.companies.flatMap(c=>c.reported_earnings?.annual_eps||[])).toHaveLength(69);
 const before:{companies:{id:string;series_sha256:string;price_dates:string[]}[]}=JSON.parse(readFileSync(new URL('./fixtures/imported-forecast-baseline.json',import.meta.url),'utf8'));
 for(const original of before.companies) {
   const current=data.companies.find(c=>c.id===original.id)!;
   expect(createHash('sha256').update(JSON.stringify(current.series)).digest('hex')).toBe(original.series_sha256);
   expect(original.price_dates.every(date=>current.prices.some(q=>q.date===date))).toBeTruthy();
 }
 const market=JSON.parse(readFileSync(new URL('../../data/market/summary.json',import.meta.url),'utf8'));
 expect(coverage.reduce((n,c)=>n+c.price_days,0)).toBe(market.total_prices);
 expect(data.cutoff).toBe(market.cutoff);
 const besi=data.companies.find(c=>c.id==='besi')!;
 expect(besi.symbol).toBe('BESI');
 expect(besi.currency).toBe('EUR');
 expect(besi.prices.every(p=>p.currency==='EUR')).toBeTruthy();
 expect(besi.series.every(s=>s.currency==='EUR')).toBeTruthy();
 writeFileSync(new URL('../../data/market/dashboard_validation.json',import.meta.url),JSON.stringify({as_of:data.cutoff,window_days:365,max_age_days:180,coverage},null,2)+'\n');
});
