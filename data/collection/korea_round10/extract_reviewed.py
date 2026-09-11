"""Recover/check the original image-based PDF and emit reviewed annual forecasts.

OCR is a locating/checking aid. The first-page date, author, units, footnote,
fiscal columns and values were visually verified against retained page renders.
"""
from pathlib import Path
from decimal import Decimal
import csv, json, hashlib, re, subprocess
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
FIELDS=['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','model_date','share_basis_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
MAN=['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window','document_kind']
def write(path,fields,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 log=json.loads((BASE/'download_log.json').read_text())[0];pdf=BASE/log['local_file'];ocr=BASE/log['text_file']
 if not pdf.exists():
  temp=pdf.with_suffix('.download');subprocess.run(['curl','-LfsS','--max-time','45',log['source_url'],'-o',str(temp)],check=True)
  assert hashlib.sha256(temp.read_bytes()).hexdigest()==log['sha256'];temp.replace(pdf)
 assert hashlib.sha256(pdf.read_bytes()).hexdigest()==log['sha256']
 if not ocr.exists():
  subprocess.run(['pdftoppm','-scale-to','2000','-png',str(pdf),str(BASE/'review/ocr_page')],check=True)
  pages=[]
  for n in range(1,10):
   out=BASE/f'text/ocr_page-{n}'
   subprocess.run(['tesseract',str(BASE/f'review/ocr_page-{n}.png'),str(out),'-l','kor+eng','--psm','6'],check=True)
   pages.append(out.with_suffix('.txt').read_text())
  ocr.write_text('\f'.join(pages)+'\f')
 pages=ocr.read_text().split('\f');assert '2026.7.14' in pages[0]
 eps=['295026','415482','442513'];rev=['347518','507945','544121']
 epsline=next(l for l in pages[0].splitlines() if all(v in l.replace(',','') for v in eps))
 revline=next(l for l in pages[0].splitlines() if all(v in l.replace(',','') for v in rev))
 assert all(v in pages[6].replace(',','').replace('.','') for v in eps+rev)
 note='Original image-based Mirae Korean PDF. July14 current report explicitly cuts earnings around 11%; date, Young-gun Kim byline, December fiscal columns and native KRW EPS visually verified on physical p1. Detailed p7 confirms EPS/revenue. K-IFRS consolidated, net profit attributable to parent; EPS basic/diluted and weighted-average/treasury-share denominator remain undefined. No split conversion applied. Original publication instant and historical availability unverified. Exact FY26-28 EPS/revenue vector repeats in the already-retained July29 note, which explicitly leaves earnings unchanged.'
 m={k:'' for k in MAN};m.update({k:log[k] for k in ['source_url','local_file','text_file','retrieved_at','sha256','page_count','discovery_url']});m.update(report_id=log['key'],company_ids='sk_hynix',firm='mirae',analyst_name='Young-gun Kim',report_date='2026-07-14',report_date_reliability='printed_date_visually_verified_physical_page_1',status='downloaded_ocr_visually_verified',notes=note,collection_window='july14_current_model_underlying_july29_reprint',document_kind='broker_research_report')
 obs=[]
 for year,e,r in zip([2026,2027,2028],eps,rev):
  for metric,value,unit,basis,line in [('eps',e,'KRW per share','Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS',epsline),('revenue',r,'KRW billion','Consolidated total revenue as printed',revline)]:
   o={k:'' for k in FIELDS};o.update({k:m[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']})
   o.update(company_id='sk_hynix',ticker='000660.KS',source_type='individual_analyst_forecast',model_date='2026-07-14',share_basis_date='2026-07-14',target_period=f'FY{year}',target_period_end=f'{year}-12-31',metric=metric,currency='KRW',value=str(int(value)*(1 if metric=='eps' else 10**9)),original_value=f'{int(value):,}',original_unit=unit,basis=basis,pdf_page=1,extraction_status='manually_verified_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=line.strip(),notes=note);obs.append(o)
 write(BASE/'manifest.csv',MAN,[m]);write(BASE/'observations.csv',FIELDS,obs)
 older=json.loads((ROOT/'data/collection/korea_round9/download_log_alternatives.json').read_text());later=next(r for r in older if r['key']=='mirae_hynix_20260729')
 assert hashlib.sha256((ROOT/'data/collection/korea_round9'/later['local_file']).read_bytes()).hexdigest()==later['sha256']
 latertext=(ROOT/'data/collection/korea_round9'/later['text_file']).read_text().split('\f')[0]
 assert 'leaving our earnings estimates unchanged' in latertext
 for label,vector in [('EPS (W)',eps),('Revenue (Wbn)',rev),('NP (Wbn)',['210755','296115','315380'])]:
  row=next(l for l in latertext.splitlines() if label in l);assert all(v in row.replace(',','') for v in vector)
 repeat=dict(company_id='sk_hynix',firm='mirae',analyst='Young-gun Kim',fiscal_periods=['FY2026','FY2027','FY2028'],model_date='2026-07-14',original_source_sha256=log['sha256'],original_source_file='data/collection/korea_round10/'+log['local_file'],original_source_url=log['source_url'],original_source_pages=[1,7],later_report_date='2026-07-29',later_source_sha256=later['sha256'],later_source_file='data/collection/korea_round9/'+later['local_file'],later_source_url=later['source_url'],later_source_page=1,exact_eps=eps,exact_revenue_krw_billion=rev,exact_parent_net_profit_krw_billion=['210755','296115','315380'],recommendation='Use the July14 original as the current model. Any later extraction of these exact July29 targets must retain July14 model age; July29 only changes valuation multiple/target price. No accounting basis alias follows from this repeat evidence.')
 (BASE/'repeat_model_evidence.json').write_text(json.dumps({'recommendations':[repeat]},indent=2)+'\n')
 (BASE/'basis_alias_recommendations.json').write_text('[]\n')
 summary=dict(retained_originals=1,physical_pages=9,model_reports=1,eps_observations=3,total_observations=6,source_sha256_verified=True,eps_revenue_physically_verified_pages=[1,7],july29_exact_vector_and_unchanged_statement_verified=True,original_publication_instants_verified=0,cross_broker_compatibility_groups_proven=0)
 (BASE/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');(BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
