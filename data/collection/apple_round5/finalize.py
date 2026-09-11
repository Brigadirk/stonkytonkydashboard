"""Reproduce reviewed Apple model observations and issuer outcomes from retained originals."""
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from collections import Counter
import csv, hashlib, json, re, subprocess
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
FIELDS=['observation_id','company_id','firm','analyst_name','metric','fiscal_period','value','currency','unit','basis','model_date','forecast_revision_as_of','report_date','available_at','printed_report_timestamp','original_available_at','availability_basis','source_url','local_file','page','status','notes','source_period_label','share_basis_date','source_artifact_sha256']
MANIFEST=['source_url','local_file','company_ids','firm','analyst_name','report_date','retrieved_at','sha256','status','notes','text_file','report_timestamp','model_dates','http_status','report_month','report_date_precision','artifact_type']
EVAL_OUTCOME=['outcome_id','company_id','fiscal_period','fiscal_period_end','metric','accounting_basis','value','currency','unit','initial_release_date','actual_available_at','share_basis_date','source_url','source_file','source_sha256','source_page','source_locator','definition','result_version','validation_status','notes']
OUTCOME=['company_id','fiscal_period','period_end','metric','value','currency','unit','accounting_basis','release_date','source_url','release_url','local_file','page','source_artifact_sha256','retrieved_at','status','notes']
NAME_PAT=r'\s+([^\n]+?),(?: CFA,| CPA,)?\s*(?:Senior Equity Analyst|Equity Analyst|Analyst|Sector Strategist|Sector Director|Strategist|Director)'
RELEASES={2021:('2021-10-28','2021-09-25','365817','5.61'),2022:('2022-10-27','2022-09-24','394328','6.11'),2023:('2023-11-02','2023-09-30','383285','6.13'),2024:('2024-10-31','2024-09-28','391035','6.08'),2025:('2025-10-30','2025-09-27','416161','7.46')}
def write(path,fields,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 manifests=[];observations=[];outcomes=[];reviews=[]
 for log in json.loads((BASE/'download_log.json').read_text()):
  row=dict.fromkeys(MANIFEST,'');row.update({k:log[k] for k in ('source_url','local_file','retrieved_at','sha256','http_status') if k in log})
  row.update(company_ids='apple',notes='Public original retained; printed dates and numerical model tables reviewed independently of path date.')
  if not row['local_file']:
   row['status']='public_url_not_found_or_download_failed';row['notes']+=' '+log.get('error','');manifests.append(row);continue
  p=ROOT/row['local_file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
  tp=BASE/'text'/f'{p.stem}.txt';text=tp.read_text();pages=text.split('\f')
  row.update(text_file=str(tp.relative_to(ROOT)),artifact_type='pdf')
  if p.stem.startswith('apple_FY'):
   y=int(p.stem[8:12]);release,end,rev,eps=RELEASES[y]
   row.update(firm='Apple Inc.',report_date=release,report_month=release[:7],report_date_precision='day',status='retained_issuer_initial_annual_results')
   # Select the third numerical value: current twelve-month period, not current quarter or prior year.
   lines=pages[0].splitlines()
   for metric,pattern,expected,unit,basis in [('revenue',r'^\s*Total net sales(?: \(1\))?\s+',rev,'USD_million','reported_total_revenue'),('eps_diluted',r'^\s*Diluted\s+',eps,'USD_per_share','reported_diluted')]:
    candidates=[l for l in lines if re.match(pattern,l)];line=next(l for l in candidates if len(re.findall(r'\d[\d,]*(?:\.\d+)?',re.sub(pattern,'',l)))>=4);vals=re.findall(r'\d[\d,]*(?:\.\d+)?',re.sub(pattern,'',line));value=vals[2].replace(',','');assert value==expected,(y,metric,value,expected)
    outcomes.append(dict(company_id='apple',fiscal_period=f'FY{y}',period_end=end,metric=metric,value=value,currency='USD',unit=unit,accounting_basis=basis,release_date=release,source_url=row['source_url'],release_url=f'https://www.apple.com/newsroom/{release[:4]}/{release[5:7]}/apple-reports-fourth-quarter-results/',local_file=row['local_file'],page='1',source_artifact_sha256=row['sha256'],retrieved_at=row['retrieved_at'],status='verified_initial_issuer_release',notes='Initial unaudited annual results issued with Q4 release. Reported GAAP diluted EPS; no analyst-adjusted figure substituted.'))
   manifests.append(row);continue
  report=re.search(r'Report as of\s+(\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC',text);assert report,p.name
  dt=datetime.strptime(report.group(1),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc);assert dt.date().isoformat()<='2026-09-10'
  author=None
  for heading in ('Analyst Note','Fair Value and Profit Drivers','Business Strategy & Outlook'):
   author=re.search(heading+NAME_PAT,text)
   if author:break
  assert author,p.name
  row.update(firm='Morningstar',analyst_name=author.group(1).strip(),report_date=dt.date().isoformat(),report_timestamp=dt.isoformat(),report_month=dt.strftime('%Y-%m'),report_date_precision='day',status='retained_no_numerical_model_table')
  for pn,page in enumerate(pages,1):
   modern=re.search(r'Financials as of\s+(\d+ [A-Za-z]+ \d{4})\s+Actual\s+Forecast',page)
   legacy=re.search(r'Morningstar Analyst Historical/Forecast Summary as of\s+(\d+ [A-Za-z]+ \d{4})',page)
   marker=modern or legacy
   if not marker:continue
   block=page[marker.start():];lines=block.splitlines();year_line=next(l for l in lines if l.startswith('Fiscal Year,'))
   years=re.findall(r'\b20\d{2}\b',year_line)[-(5 if legacy else 8):];start=2 if legacy else 3
   md=datetime.strptime(marker.group(1),'%d %b %Y').date().isoformat();assert md<=row['report_date']
   row.update(model_dates=md,status='downloaded_forecast_tables_verified')
   notes='Printed report timestamp is not independently verified original availability. Model age is measured from the numerical table date, not the current analyst note. USD per-share values are already after the August 2020 split. Fiscal years match issuer annual revenue anchors; nominal Sep 26/30 headers do not override the last-Saturday fiscal calendar.'
   obs_author=row['analyst_name'];status='extracted_table_pending_basis_match'
   if p.stem.endswith('20231130'):
    obs_author='Brian Colello'
    notes+=' Current report sections are signed William Kerwin, but this is an unchanged reprint of Brian Colello\'s Nov 2 model, retained in the Nov 3 report. Attribution follows the original numerical model, not the later cover author.'
   if legacy:
    notes+=' Legacy table prints diluted EPS without explicitly establishing adjustment basis; kept separate from modern reported and adjusted diluted series.'
   reviews.append(dict(local_file=row['local_file'],report_date=row['report_date'],model_date=md,report_author=row['analyst_name'],model_author=obs_author,page=pn,year_header=year_line.strip(),source_sha256=row['sha256']))
   patterns=[('revenue',r'^Revenue \(USD Mil\)','USD_million','total_revenue'),('revenue',r'^Revenue \(USD Bil\)','USD_billion','total_revenue'),('eps_diluted',r'^Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','reported_diluted'),('eps_adjusted_diluted',r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','adjusted_diluted'),('eps_diluted_basis_unresolved',r'^Diluted Earnings Per Share\s*\(USD\)','USD_per_share','diluted_adjustment_basis_unresolved')]
   for metric,pattern,unit,basis in patterns:
    line=next((l for l in lines if re.match(pattern,l)),None)
    if line is None:continue
    vals=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.sub(pattern,'',line))[:len(years)];assert len(vals)==len(years),(p.name,line)
    for y,value in list(zip(years,vals))[start:]:
     fiscal_end=date(int(y),9,30);fiscal_end-=timedelta(days=(fiscal_end.weekday()-5)%7)
     if fiscal_end.isoformat()<=md:
      continue # Do not recast a just-completed annual result as a future forecast.
     obs=dict.fromkeys(FIELDS,'');obs.update(company_id='apple',firm='Morningstar',analyst_name=obs_author,metric=metric,fiscal_period=f'FY{y}',source_period_label=f'FY{y}',value=value.replace(',',''),currency='USD',unit=unit,basis=basis,model_date=md,forecast_revision_as_of=md,report_date=row['report_date'],printed_report_timestamp=row['report_timestamp'],availability_basis='printed_report_timestamp_not_independently_verified',source_url=row['source_url'],local_file=row['local_file'],page=str(pn),status=status,notes=notes,share_basis_date=md,source_artifact_sha256=row['sha256'])
     obs['observation_id']=hashlib.sha256(f'{row["sha256"]}|{pn}|{metric}|{y}'.encode()).hexdigest()[:20];observations.append(obs)
  manifests.append(row)
 assert len({r['observation_id'] for r in observations})==len(observations)
 # The November 30 cover-author transition must not manufacture a new author's model.
 a=[(r['metric'],r['fiscal_period'],r['value']) for r in observations if '20231103' in r['local_file']]
 b=[(r['metric'],r['fiscal_period'],r['value']) for r in observations if '20231130' in r['local_file']]
 assert a==b
 write(BASE/'manifest.csv',MANIFEST,manifests);write(BASE/'observations.csv',FIELDS,observations);write(BASE/'issuer_outcomes.csv',OUTCOME,outcomes)
 eps_outcomes=[]
 for r in outcomes:
  if r['metric']!='eps_diluted':continue
  e=dict.fromkeys(EVAL_OUTCOME,'');e.update(outcome_id=hashlib.sha256(f'{r["source_artifact_sha256"]}|{r["fiscal_period"]}|reported_diluted'.encode()).hexdigest()[:20],company_id='apple',fiscal_period=r['fiscal_period'],fiscal_period_end=r['period_end'],metric='eps_diluted',accounting_basis='reported_diluted',value=r['value'],currency='USD',unit='USD_per_share',initial_release_date=r['release_date'],actual_available_at='',share_basis_date=r['release_date'],source_url=r['source_url'],source_file=r['local_file'],source_sha256=r['source_artifact_sha256'],source_page='1',source_locator='Condensed Consolidated Statements of Operations; Twelve Months Ended current fiscal year; Earnings per share: Diluted',definition='Initial issuer-reported annual GAAP diluted earnings per share',result_version='initial_release',validation_status='verified_initial_issuer_release',notes=r['notes']+' Release date is verified from the linked Apple newsroom release; actual_available_at is blank because intraday first dissemination is not independently established; the UI may use a separately labelled next-day convention. All outcomes are after the August 31, 2020 split-adjusted trading date.')
  eps_outcomes.append(e)
 write(BASE/'issuer_eps_outcomes.csv',EVAL_OUTCOME,eps_outcomes)
 (BASE/'model_review.json').write_text(json.dumps(reviews,indent=2)+'\n')
 summary={'attempts':len(manifests),'retained_pdfs':sum(bool(r['local_file']) for r in manifests),'morningstar_pdfs':sum(r['firm']=='Morningstar' for r in manifests),'numerical_model_reports':len(reviews),'observations':len(observations),'eps_observations':sum(r['metric'].startswith('eps') for r in observations),'unique_model_dates':len(set(r['model_date'] for r in observations)),'authors':dict(Counter(r['analyst_name'] for r in observations)),'basis_counts':dict(Counter(r['basis'] for r in observations)),'initial_issuer_outcomes':len(outcomes),'quarantined':sum(r['status'].startswith('quarantined') for r in observations)}
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
