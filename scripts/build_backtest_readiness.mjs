import {readFileSync,writeFileSync} from 'node:fs';
import {assessSeries} from '../web/src/readiness.ts';
const root=new URL('../',import.meta.url);
const bundlePath=new URL('web/public/data/dashboard.json',root);
const data=JSON.parse(readFileSync(bundlePath,'utf8'));
const startDate=new Date(data.cutoff+'T00:00:00Z');
startDate.setUTCFullYear(startDate.getUTCFullYear()-5);
const start=startDate.toISOString().slice(0,10);
const series=data.companies.flatMap(company=>company.series.map(series=>assessSeries(company,series,start,data.cutoff)));
const report={as_of:data.cutoff,start,windows:[180,365],max_age_days:180,
  status:series.some(s=>s.verified_full_reference_sessions>0)?'requires_study_design':'not_ready',series,
  limitations:[
    'Public report-date assumptions remain distinct from exact-byte archive evidence. Strict history begins after the proven archive bound or supplied provider timestamp; archive captures do not establish the original publication instant.',
    'Each analyst and accounting basis is assessed separately. Counts are never pooled across series.',
    'Chart bands require 20 observations; full-reference counts additionally require usable EPS on every retained price session in both windows and a year of warm-up.',
    'Missing exchange sessions have not been independently audited. Full reference means complete against retained prices only.',
    'Prices exclude cash dividends. A strategy study needs an explicit execution, transaction-cost and dividend policy.',
    'The universe was selected today. Any historical study must disclose that selection and fix the analyst series before examining returns.'
  ]};
writeFileSync(new URL('data/market/backtest_readiness.json',root),JSON.stringify(report,null,2)+'\n');
data.backtest_readiness=report;
writeFileSync(bundlePath,JSON.stringify(data)+'\n');
console.log(JSON.stringify({status:report.status,series:series.length,series_with_verified_full_reference_sessions:series.filter(s=>s.verified_full_reference_sessions>0).length}));
