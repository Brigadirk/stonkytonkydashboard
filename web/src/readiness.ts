import { bandValue, calculate, daysBetween } from './engine.ts';
import type { Company, Series } from './types';

export interface SeriesReadiness {
  company_id:string; company_name:string; series_id:string; series_label:string;
  sessions:number; reconstructed_band_sessions:number; full_reference_sessions:number;
  verified_full_reference_sessions:number; longest_gap_sessions:number;
  first_supported_date:string|null; last_supported_date:string|null;
}
export interface BacktestReadiness {
  as_of:string; start:string; windows:number[]; max_age_days:number;
  status:'not_ready'|'requires_study_design'; series:SeriesReadiness[];
  limitations:string[];
}

export function assessSeries(company:Company, series:Series, start:string, asOf:string):SeriesReadiness {
  const options={asOf,maxAge:180,strict:false};
  const short=calculate(company,series,{...options,window:180});
  const long=calculate(company,series,{...options,window:365});
  const strictShort=calculate(company,series,{...options,strict:true,window:180});
  const strictLong=calculate(company,series,{...options,strict:true,window:365});
  const result:SeriesReadiness={company_id:company.id,company_name:company.name,series_id:series.id,series_label:series.label,
    sessions:0,reconstructed_band_sessions:0,full_reference_sessions:0,verified_full_reference_sessions:0,
    longest_gap_sessions:0,first_supported_date:null,last_supported_date:null};
  let gap=0;
  for(let i=0;i<long.length;i++) {
    const point=long[i];
    if(point.date<start)continue;
    result.sessions++;
    const usable=bandValue(point,0,'price')!==null&&bandValue(short[i],0,'price')!==null;
    // A chart can draw with 20 references. Study coverage separately requires
    // every retained price session in both windows and a full year of warm-up.
    const full=usable&&point.count===point.possible&&short[i].count===short[i].possible&&daysBetween(point.date,long[0].date)>=365;
    if(usable) {
      result.reconstructed_band_sessions++;
      result.first_supported_date??=point.date;
      result.last_supported_date=point.date;
      gap=0;
    } else {
      gap++;
      result.longest_gap_sessions=Math.max(result.longest_gap_sessions,gap);
    }
    if(full)result.full_reference_sessions++;
    if(full&&bandValue(strictLong[i],0,'price')!==null&&bandValue(strictShort[i],0,'price')!==null&&
       strictLong[i].count===strictLong[i].possible&&strictShort[i].count===strictShort[i].possible)result.verified_full_reference_sessions++;
  }
  return result;
}
