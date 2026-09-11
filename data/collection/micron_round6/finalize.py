"""Reproduce reviewed Micron sources and model-scoped accounting bridges offline."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
FIELDS=['observation_id','company_id','firm','analyst_name','metric','fiscal_period','value','currency','unit','basis','model_date','forecast_revision_as_of','report_date','available_at','printed_report_timestamp','original_available_at','availability_basis','source_url','local_file','page','status','notes','source_period_label','share_basis_date','source_artifact_sha256']
MANIFEST=['source_url','local_file','company_ids','firm','analyst_name','report_date','retrieved_at','sha256','status','notes','text_file','report_timestamp','model_dates','http_status','report_month','report_date_precision','artifact_type']
SELECTED={'20220513','20221222','20230329','20230525','20231221','20240815','20240926','20250321'}
NAME=r'\s+([^\n]+?),(?: CFA,)?\s*(?:Sector Strategist|Senior Equity Analyst|Equity Analyst|Strategist|Analyst)'
def day(s):return datetime.strptime(s,'%d %b %Y').date().isoformat()
def write_csv(path,fields,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def parse_value_line(block,pattern,n):
 line=next((l for l in block.splitlines() if re.match(pattern,l)),None)
 if line is None:return None
 values=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.sub(pattern,'',line))[:n]
 assert len(values)==n,(line,values,n)
 return [v.replace(',','') for v in values]
def main():
 manifests=[];observations=[];excluded=[];by_hint={}
 for log in json.loads((BASE/'download_log.json').read_text()):
  r=dict.fromkeys(MANIFEST,'');r.update({k:log[k] for k in MANIFEST if k in log});r.update(company_ids='micron',firm='Morningstar',notes='Bounded public dated URL; filename date is only a discovery hint.')
  if not r['local_file']:
   r.update(status='public_url_not_found_or_download_failed',notes=r['notes']+' '+log.get('error',''));manifests.append(r);continue
  p=ROOT/r['local_file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
  text=(ROOT/r['text_file']).read_text();assert 'Micron Technology Inc MU' in text
  m=re.search(r'Report as of (\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC',text)
  dt=datetime.strptime(m.group(1),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc)
  author=None
  for heading in ('Analyst Note','Business Strategy & Outlook','Fair Value and Profit Drivers'):
   author=re.search(heading+NAME,text)
   if author:break
  assert author
  r.update(analyst_name=author.group(1).strip(),report_date=dt.date().isoformat(),report_timestamp=dt.isoformat(),report_month=dt.strftime('%Y-%m'),report_date_precision='day',artifact_type='pdf',status='retained_corrob_reprint_no_additional_forecast_rows')
  hint=log['date_hint'];by_hint[hint]=r
  for page_no,page in enumerate(text.split('\f'),1):
   modern=re.search(r'Financials as of\s+(\d+ [A-Za-z]+ \d{4})\s+Actual\s+Forecast',page)
   legacy=re.search(r'Morningstar Analyst Historical/Forecast Summary as of\s+(\d+ [A-Za-z]+ \d{4})',page)
   marker=modern or legacy
   if not marker:continue
   block=page[marker.start():];n=5 if legacy else 8;start=2 if legacy else 3
   year_line=next(l for l in block.splitlines() if l.startswith('Fiscal Year,'))
   years=re.findall(r'\b20\d{2}\b',year_line)[-n:];assert len(years)==n
   model=day(marker.group(1));r['model_dates']=model
   if hint not in SELECTED:continue
   notes='Values and share units retained as printed; no split transformation. Numerical model date comes from the financial table. Printed report timestamp is not independently verified original availability; no reprint is backdated to its model date. Legacy EPS is not assumed GAAP or issuer non-GAAP. Fiscal years refer to Micron fiscal years ending on the Thursday closest to August 31.'
   if hint=='20220513':notes+=' Revenue rounds to whole USD billions in this source; the June30 reprint reports more precise revenue but does not establish that precision was available on May13. The nominal 2 Sep header is not an exact FY2022 period end.'
   if 'Oct' in year_line:notes+=' Printed October fiscal month is erroneous; FY2023 revenue15540 and FY2024 revenue25111 USDm anchor the year identities, and the issuer annual report supplies the August calendar. No year shift applied.'
   if hint=='20221222':notes+=' The stale estimate bracket includes FY2022 actual revenue30758/EPS8.35, already released September29; that completed-period column is excluded from observations.'
   if hint=='20250321':notes+=' Modern table explicitly separates reported and adjusted diluted EPS, but its numerical model remains December18,2024. New reported EPS and FY2028/29 targets are first evidenced by this March21,2025 artifact, not the December19,2024 legacy original. Prior-model revision panel is accounting-definition evidence only and is not exported as a newly backdated forecast.'
   patterns=[('revenue',r'^Revenue \(USD Mil\)','USD_million','total_revenue'),('revenue',r'^Revenue \(USD Bil\)','USD_billion','total_revenue'),('eps_diluted_basis_unresolved',r'^Diluted Earnings Per Share\s*\(USD\)','USD_per_share','diluted_adjustment_basis_unresolved'),('eps_diluted',r'^Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','reported_diluted'),('eps_adjusted_diluted',r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','adjusted_diluted')]
   count=0
   for metric,pat,unit,basis in patterns:
    values=parse_value_line(block,pat,n)
    if values is None:continue
    for y,v in list(zip(years,values))[start:]:
     if hint=='20221222' and y=='2022':
      excluded.append({'source_url':r['source_url'],'source_file':r['local_file'],'source_sha256':r['sha256'],'physical_page':page_no,'model_date':model,'report_date':r['report_date'],'metric':metric,'fiscal_period':'FY2022','value':v,'reason':'Already-released FY2022 actual under stale estimate bracket; not a forecast.'});continue
     obs=dict.fromkeys(FIELDS,'')
     obs.update(company_id='micron',firm='Morningstar',analyst_name=r['analyst_name'],metric=metric,fiscal_period='FY'+y,value=v,currency='USD',unit=unit,basis=basis,model_date=model,forecast_revision_as_of=model,report_date=r['report_date'],printed_report_timestamp=r['report_timestamp'],availability_basis='printed_report_timestamp_not_independently_verified',source_url=r['source_url'],local_file=r['local_file'],page=str(page_no),status='extracted_table_pending_basis_match',notes=notes,source_period_label='FY'+y,share_basis_date=model,source_artifact_sha256=r['sha256'])
     obs['observation_id']=hashlib.sha256(f'{r["sha256"]}|{page_no}|{metric}|{y}'.encode()).hexdigest()[:24]
     observations.append(obs);count+=1
   r.update(status='downloaded_forecast_tables_verified',notes=notes)
   assert count in (4,6,15),(hint,count)
  manifests.append(r)
 issuer=json.loads((BASE/'issuer_definition_manifest.json').read_text());p=ROOT/issuer['source_file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==issuer['source_sha256']
 r=dict.fromkeys(MANIFEST,'');r.update(source_url=issuer['source_url'],local_file=issuer['source_file'],company_ids='micron',firm='Micron Technology (issuer)',report_date=issuer['report_date'],retrieved_at=issuer['retrieved_at'],sha256=issuer['source_sha256'],status='retained_issuer_fiscal_definition',notes=issuer['notes']+' Physical page5 supplies the fiscal calendar. Annual report is definition evidence, not an initial EPS outcome source.',text_file='data/collection/micron_round6/text/micron_fy2024_10k.txt',http_status=200,report_month='2024-10',report_date_precision='day',artifact_type='pdf');manifests.append(r)
 assert len({r['observation_id'] for r in observations})==len(observations)
 assert all(not r['available_at'] and not r['original_available_at'] for r in observations)
 write_csv(BASE/'manifest.csv',MANIFEST,manifests);write_csv(BASE/'observations.csv',FIELDS,observations)
 (BASE/'excluded_completed_period_columns.json').write_text(json.dumps(excluded,indent=2)+'\n')
 # Exact source-model-period accounting definition bridges. No estimated values derived.
 evidence=by_hint['20250321'];etext=(ROOT/evidence['text_file']).read_text();pages=etext.split('\f')
 recs=[]
 for model,eps,rev,older,page_no,locator in [
  ('2024-09-25',['8.47','11.03','10.58'],['37466','42370','44161'],[by_hint['20240926']],14,'Forecast Revisions; Prior data as of25Sep2024; adjusted diluted EPS prior columns FY2025/26/27.'),
  ('2024-12-18',['5.79','7.14','8.75'],['32759','36101','39669'],[x for x in csv.DictReader((ROOT/'data/collection/us_round4/manifest.csv').open()) if x.get('local_file')=='data/collection/us_round4/pdfs/morningstar_MU_20241218.pdf']+[by_hint['20250127'],by_hint['20250128']],13,'Current Financials as of18Dec2024; Adjusted Earnings Per Share (Diluted), FY2025/26/27.')]:
  assert older
  matched=[];sources=[]
  for original in older:
   pp=ROOT/original['local_file'];sha=hashlib.sha256(pp.read_bytes()).hexdigest();assert sha==original['sha256']
   txt=ROOT/original['text_file'];opages=txt.read_text().split('\f');blocks=[(n,p[p.index('Morningstar Analyst Historical/Forecast Summary'):]) for n,p in enumerate(opages,1) if 'Morningstar Analyst Historical/Forecast Summary' in p]
   assert len(blocks)==1
   pn,block=blocks[0];assert day(re.search(r'Summary as of\s+(\d+ [A-Za-z]+ \d{4})',block).group(1))==model
   assert parse_value_line(block,r'^Diluted Earnings Per Share\s*\(USD\)',5)[2:]==eps
   assert parse_value_line(block,r'^Revenue \(USD Mil\)',5)[2:]==rev
   sources.append({'source_url':original['source_url'],'source_file':original['local_file'],'source_sha256':sha,'physical_page':pn,'report_date':original['report_date']})
  if model=='2024-09-25':
   p=pages[13];assert 'Prior data as of 25 Sep 2024' in p
   e=parse_value_line(p,r'^ Adjusted Earnings Per Share \(Diluted\) \(USD\)',6);v=parse_value_line(p,r'^ Revenue \(USD Mil\)',6)
   assert e[1::2]==eps and v[1::2]==rev
  else:
   p=pages[12];assert 'Financials as of 18 Dec 2024' in p
   e=parse_value_line(p,r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)',8);v=parse_value_line(p,r'^Revenue \(USD Mil\)',8)
   assert e[3:6]==eps and v[3:6]==rev
  raw=list(csv.DictReader((ROOT/'data/collection/us_round4/observations.csv').open()))+observations
  for obs in raw:
   if obs.get('company_id')=='micron' and obs.get('model_date')==model and obs.get('basis')=='diluted_adjustment_basis_unresolved' and obs['fiscal_period'] in ['FY2025','FY2026','FY2027'] and obs['source_artifact_sha256'] in [s['source_sha256'] for s in sources]:matched.append(obs['observation_id'])
  recs.append({'company_id':'micron','firm':'Morningstar','analyst':'William Kerwin','original_basis':'diluted_adjustment_basis_unresolved','canonical_basis':'adjusted_diluted','model_dates':[model],'fiscal_periods':['FY2025','FY2026','FY2027'],'status':'supported_model_and_period_scoped_alias','issuer_non_gaap_equivalence':'not_proven_do_not_score_against_issuer_non_gaap','matched_values':dict(zip(['FY2025','FY2026','FY2027'],eps)),'matched_revenue_values_usd_million':dict(zip(['FY2025','FY2026','FY2027'],rev)),'original_observation_ids':matched,'original_sources':sources,'evidence':{'source_url':evidence['source_url'],'source_file':evidence['local_file'],'source_sha256':evidence['sha256'],'physical_page':page_no,'report_date':evidence['report_date'],'locator':locator,'explicit_label_row':next(l.strip() for l in pages[page_no-1].splitlines() if 'Adjusted Earnings Per Share (Diluted) (USD)' in l)},'fiscal_mapping':'Exact fiscal year alignment FY2025/26/27; no rolled-header shift in this earlier March21 source. Original source printed October month corrected using revenue-year anchors and issuer August calendar.','limits':'Preserve raw basis, analyst, model date, report date and availability. Restrict alias to listed original source hashes, model and fiscal periods. No promotion of earlier models, no inference of reported EPS from old adjusted EPS, and no issuer non-GAAP equivalence.'})
 (BASE/'basis_alias_recommendations.json').write_text(json.dumps({'review_date':'2026-09-10','recommendations':recs,'unproven':'Models before25Sep2024 retain diluted_adjustment_basis_unresolved. Historical actual matches, adjusted P/E narrative and generic normalization definitions do not prove a forecast definition.'},indent=2)+'\n')
 stats={'public_url_attempts':len(manifests)-1,'retained_broker_pdfs':len(by_hint),'issuer_definition_pdfs':1,'forecast_reports':len(SELECTED),'model_dates':sorted({r['model_date'] for r in observations}),'observations':len(observations),'eps_observations':sum(r['metric'].startswith('eps') for r in observations),'negative_eps_observations':sum(r['metric'].startswith('eps') and float(r['value'])<0 for r in observations),'by_basis':dict(Counter(r['basis'] for r in observations)),'excluded_completed_period_columns':len(excluded),'supported_alias_models':2,'supported_original_eps_cells':sum(len(r['original_observation_ids']) for r in recs),'hashes_verified':True,'exact_eps_and_revenue_bridge_vectors_verified':True,'availability_fields_blank':True}
 (BASE/'validation.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
