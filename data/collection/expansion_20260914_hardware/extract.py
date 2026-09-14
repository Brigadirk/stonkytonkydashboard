"""Extract reviewed Morningstar annual EPS tables. Originals remain in raw/."""
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
import re,json,hashlib
B=Path(__file__).resolve().parent
APP=B.parents[2]
analysts={'amd':'Brian Colello','marvell':'William Kerwin','arista':'William Kerwin','vertiv':'Nicholas Lieb','nebius':'Javier Correonero','spacex':'Nicolas Owens'}
ids={'amd':'0P0000006A','marvell':'0P000003H5','arista':'0P0001354B','vertiv':'0P0001E1XR','nebius':'0P0000TDA0','spacex':'0P0002DZNH'}
bases=[('adjusted_diluted','Adjusted Earnings Per Share (Diluted) (USD)','Adjusted diluted EPS'),('morningstar_unadjusted_diluted','Earnings Per Share (Diluted) (USD)','Diluted EPS')]
def fiscal_end(company, year):
 if company=='amd':
  anchor=date(year,12,31); return anchor-timedelta(days=(anchor.weekday()-5)%7)
 if company=='marvell':
  anchor=date(year,1,31); return min((anchor+timedelta(days=n) for n in range(-3,4)),key=lambda d:0 if d.weekday()==5 else 1)
 return date(year,12,31)
calendar_sources=json.loads((B/'fiscal_calendar_sources.json').read_text())
calendar_urls={r['company_id']:r['source_url'] for r in calendar_sources}
result={'as_of_cutoff':'2026-09-11','captured_at':datetime.now(timezone.utc).isoformat(),'companies':[],'sources':[],'evidence_entries':[],'gaps':[],'fiscal_calendar_sources':calendar_sources}
for company,analyst in analysts.items():
 series={basis:{'id':f'{company}_morningstar_{basis}_expansion_20260914','label':f'Morningstar - {analyst} - {label}','analyst':analyst,'firm':'Morningstar','accounting_basis':basis,'currency':'USD','series_type':'individual_analyst_forecast','coverage_note':'Retained public Morningstar annual forecasts, distributed by Firstrade. Report date plus one day is an availability assumption; original publication timing is not verified. Reprints are retained, not independent revisions.','comparability_note':'Source labels are retained. No equivalence with issuer GAAP or issuer non-GAAP EPS is established.','comparability_source_url':'','snapshots':[]} for basis,_,label in bases}
 for pdf in sorted((B/'raw').glob(company+'_*.pdf')):
  raw=pdf.read_bytes();sha=hashlib.sha256(raw).hexdigest();text=pdf.with_suffix('.txt').read_text()
  ts=datetime.strptime(re.search(r'Report as of (\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC',text).group(1),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc)
  assert ts.date().isoformat()<='2026-09-11'
  pn,page=next((i,p) for i,p in enumerate(text.split('\f'),1) if 'Morningstar Valuation Model Summary' in p)
  block=page.split('Morningstar Valuation Model Summary',1)[1]
  model=datetime.strptime(re.search(r'Financials as of (\d{2} [A-Za-z]{3} \d{4})',block).group(1),'%d %b %Y').date().isoformat()
  yearline=next(line for line in block.splitlines() if line.startswith('Fiscal Year, ends'))
  years=list(map(int,re.findall(r'\b20\d{2}\b',yearline)));assert len(years)==8
  end='01-31' if company=='marvell' else '12-31'; assert ('31 Jan' if company=='marvell' else '31 Dec') in yearline
  day=pdf.stem.split('_')[-1];url=f'https://invest.firstrade.com/ms/equity_reports/sr/{day[:4]}/{ids[company]}_{day}_RT.pdf'
  notes=['Five forecast columns follow three actual columns in the source table. Fiscal date boundaries follow issuer calendars for AMD and Marvell, and the printed calendar year-end for the other companies. Source does not supply a detailed adjustment reconciliation.']
  if company in ['amd','marvell']: notes.append('Fiscal boundaries are derived from the verified issuer rule: last Saturday in December for AMD; Saturday nearest January 31 for Marvell. The source table nominal month-end is retained separately. Rule source: '+calendar_urls[company])
  if company=='arista':notes.append('All retained forecasts are after the December 2024 four-for-one stock split. Do not divide these EPS values again.')
  if company=='nebius' and day=='20260812':notes.append('DATE CONFLICT: the source header prints 13 May 2026, but EPS differs from the retained 14 May report. The printed model date is retained as a source claim. These revised values must not be treated as known in May; first retained report appearance is 12 August 2026.')
  if company=='spacex':notes.append('The 16 June model changes historical net income and future EPS relative to the 12 June model. The source model-revision table confirms replacement values. Historical financial scope and adjustment comparability are not independently reconciled. Equal reported and adjusted EPS rows remain separate source labels.')
  note=' '.join(notes)
  source_file=str(pdf.relative_to(APP))
  source={'company_id':company,'firm':'Morningstar','analyst':analyst,'source_url':url,'source_file':source_file,'text_file':str(pdf.with_suffix('.txt').relative_to(APP)),'source_sha256':sha,'report_date':ts.date().isoformat(),'printed_report_timestamp':ts.isoformat(),'model_date':model,'source_page':str(pn),'table':'Morningstar Valuation Model Summary / Financials','nominal_fiscal_year_end':end,'notes':note,'retrieved_at':datetime.fromtimestamp(pdf.stat().st_mtime,timezone.utc).isoformat(),'source_type':'original_analyst_report_on_distributor','visually_reviewed':pdf.stem in ['amd_20260804','arista_20260804','marvell_20260827','vertiv_20260729','nebius_20260812','spacex_20260804']}
  result['sources'].append(source)
  for basis,label,_ in bases:
   line=next(line for line in block.splitlines() if line.startswith(label))
   values=re.findall(r'-?\d+\.\d+',line[len(label):]);assert len(values)==8,(pdf.name,values)
   sid=hashlib.sha256(f'{sha}|{basis}'.encode()).hexdigest()[:24]
   snapshot={'id':sid,'report_date':ts.date().isoformat(),'model_date':model,'available_date':(ts.date()+timedelta(days=1)).isoformat(),'availability_basis':'printed_report_date_plus_one_day_unverified','retrieved_at':datetime.fromtimestamp(pdf.stat().st_mtime,timezone.utc).isoformat(),'share_basis_date':model,'source_url':url,'source_file':source_file,'source_sha256':sha,'kind':'annual','estimates':[]}
   for year,value in zip(years[3:],values[3:]):
    oid=hashlib.sha256(f'{sha}|{basis}|{year}'.encode()).hexdigest()[:24]
    start=(fiscal_end(company,year-1)+timedelta(days=1)).isoformat();finish=fiscal_end(company,year).isoformat()
    estimate={'observation_id':oid,'fiscal_period':f'FY{year}','fiscal_period_start':start,'fiscal_period_end':finish,'eps':float(value),'source_page':str(pn),'notes':note,'original_accounting_basis':label,'basis_alias_evidence':''}
    snapshot['estimates'].append(estimate)
    result['evidence_entries'].append({**source,**estimate,'series_id':series[basis]['id'],'metric':'eps','unit':'USD_per_listed_share','currency':'USD','accounting_basis':basis,'available_date':snapshot['available_date'],'availability_basis':snapshot['availability_basis'],'value_as_printed':value})
   series[basis]['snapshots'].append(snapshot)
 result['companies'].append({'company_id':company,'series':list(series.values())})
result['gaps'].append({'company_id':'cerebras','status':'annual_eps_forecast_not_retained','details':'No dated original annual analyst EPS forecast located. Fifteen Firstrade candidate URLs returned 404. Morningstar quote page direct retrieval returned 403. Issuer Q2 release exists, but guidance covers core revenue and margins, not annual EPS for FY2027 and FY2028. Current third-party consensus cannot establish a pre-cutoff forecast vintage.','issuer_source_url':'https://investors.cerebras.ai/node/7286/pdf'})
(B/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
summary={'original_pdfs':len(result['sources']),'companies_with_annual_eps':len(result['companies']),'series':sum(len(c['series']) for c in result['companies']),'annual_eps_entries':len(result['evidence_entries']),'source_hashes_verified':True,'latest_tables_visually_verified':6,'availability_independently_verified':False,'date_conflicts':['Nebius August 12 2026 printed financial model date May13 2026 conflicts with revised values.']}
(B/'validation.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
