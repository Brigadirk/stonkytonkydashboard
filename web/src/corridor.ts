import { daysBetween, epoch, sampleStd, shiftDate } from './engine.ts';
import { projectedPrice, type Projection } from './projection.ts';
import type { Company, Price } from './types';

export const CORRIDOR_LEVELS = [-2,-1.5,-1,0,1,1.5,2];
export const VOLATILITY_LOOKBACK_DAYS = 365;
export const MIN_VOLATILITY_RETURNS = 60;
export const SESSIONS_PER_YEAR = 252;
export const CORRIDOR_METHOD = 'anchored_log_scenarios_v1';

export interface ReturnObservation {
  from: string;
  to: string;
  logReturn: number;
  fromPrice: Price;
  toPrice: Price;
}
export interface PriceVolatility {
  start: string;
  end: string;
  observations: ReturnObservation[];
  exclusions: {from:string;to:string;reason:string}[];
  dailyStd: number|null;
  annualStd: number|null;
  reason: string|null;
}
export interface PriceCorridor {
  method: typeof CORRIDOR_METHOD;
  target: Projection|null;
  dates: string[];
  volatility: PriceVolatility|null;
  originPriceValid: boolean;
  reason: string|null;
}

// Fixed trailing year, through the origin close. Never use future prices,
// splice across invalid closes, or trim genuine large returns as outliers.
export function priceVolatility(company:Company, origin:string):PriceVolatility {
  const start=shiftDate(origin,-VOLATILITY_LOOKBACK_DAYS);
  const prices=company.prices.filter(p=>p.date>=start&&p.date<=origin).sort((a,b)=>a.date.localeCompare(b.date));
  const counts=new Map<string,number>();
  for(const p of prices)counts.set(p.date,(counts.get(p.date)||0)+1);
  const valid=(p:Price)=>Number.isFinite(epoch(p.date))&&Number.isFinite(p.close)&&p.close>0&&p.currency===company.currency&&p.adjustment_basis==='split_adjusted_to_cutoff'&&counts.get(p.date)===1;
  const observations:ReturnObservation[]=[],exclusions:PriceVolatility['exclusions']=[];
  for(let i=1;i<prices.length;i++){
    const previous=prices[i-1],current=prices[i],gap=daysBetween(current.date,previous.date);
    const reason=!valid(previous)||!valid(current)?'Invalid, duplicate or incompatible close'
      :gap<=0||gap>7?'Close interval is not between 1 and 7 calendar days':null;
    if(reason)exclusions.push({from:previous.date,to:current.date,reason});
    else observations.push({from:previous.date,to:current.date,logReturn:Math.log(current.close/previous.close),fromPrice:previous,toPrice:current});
  }
  const reason=observations.length<MIN_VOLATILITY_RETURNS?`Needs ${MIN_VOLATILITY_RETURNS} valid close-to-close returns in the past year; found ${observations.length}`:null;
  const dailyStd=reason?null:sampleStd(observations.map(p=>p.logReturn));
  return {start,end:origin,observations,exclusions,dailyStd,annualStd:dailyStd===null?null:dailyStd*Math.sqrt(SESSIONS_PER_YEAR),reason};
}

export function priceCorridor(company:Company,target:Projection|null):PriceCorridor {
  if(!target)return {method:CORRIDOR_METHOD,target,dates:[],volatility:null,originPriceValid:false,reason:'No projection origin'};
  const volatility=priceVolatility(company,target.origin),dates:string[]=[];
  for(let date=target.origin;date<=target.target;date=shiftDate(date,1))dates.push(date);
  const origin=company.prices.find(p=>p.date===target.origin);
  const originPriceValid=!!origin&&origin.close===target.currentPrice&&Number.isFinite(origin.close)&&origin.close>0&&origin.currency===company.currency&&origin.adjustment_basis==='split_adjusted_to_cutoff';
  return {method:CORRIDOR_METHOD,target,dates,volatility,originPriceValid,
    reason:!originPriceValid?'Origin price basis is invalid':target.reason||volatility.reason};
}

// Illustrative, endpoint-conditioned paths, not calibrated probability bands.
// In log prices the centre moves gradually to the terminal median. Short-run
// width uses observed return volatility; terminal width uses valuation scenarios.
// Quadrature preserves ordered levels and both endpoints without instant repricing.
export function corridorPrice(corridor:PriceCorridor,date:string,sigma:number):number|null {
  const p=corridor.target;
  if(!p||!corridor.originPriceValid||!Number.isFinite(epoch(date))||date<p.origin||date>p.target||!CORRIDOR_LEVELS.includes(sigma))return null;
  if(date===p.origin)return p.currentPrice;
  const terminal=projectedPrice(p,sigma),median=projectedPrice(p,0);
  if(terminal===null||median===null||terminal<=0||median<=0)return null;
  if(date===p.target)return terminal;
  if(corridor.reason||corridor.volatility?.annualStd==null)return null;
  const u=daysBetween(date,p.origin)/daysBetween(p.target,p.origin);
  const centre=Math.log(p.currentPrice)+u*Math.log(median/p.currentPrice);
  const terminalOffset=Math.log(terminal/median);
  const spread=Math.sqrt(u*(1-u)*(sigma*corridor.volatility.annualStd)**2+u*u*terminalOffset**2);
  const price=Math.exp(centre+Math.sign(sigma)*spread);
  return Number.isFinite(price)&&price>0?price:null;
}

export function corridorCsv(company:Company,corridors:PriceCorridor[]):string {
  const fields=['company','series','row_kind','method','origin','date','terminal_date','currency','origin_close',...CORRIDOR_LEVELS.map(k=>`path_to_${k}_sigma_target`),'volatility_start','volatility_end','return_count','daily_log_return_std','annual_log_return_std','sessions_per_year_assumption','gap_reason','return_evidence_json'];
  const rows:unknown[][]=[fields];
  for(const c of corridors){
    const p=c.target;if(!p)continue;
    for(const date of c.dates)rows.push([company.symbol,p.label,'illustrative_price_path',c.method,p.origin,date,p.target,company.currency,p.currentPrice,...CORRIDOR_LEVELS.map(k=>corridorPrice(c,date,k)),c.volatility?.start,c.volatility?.end,c.volatility?.observations.length,c.volatility?.dailyStd,c.volatility?.annualStd,SESSIONS_PER_YEAR,c.reason,
      date===p.origin?JSON.stringify({observations:c.volatility?.observations,exclusions:c.volatility?.exclusions}):'']);
  }
  return rows.map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(',')).join('\n');
}
