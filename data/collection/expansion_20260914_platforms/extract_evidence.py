from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,re,hashlib,calendar
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parent
PREFIX='data/collection/expansion_20260914_platforms/'
AUTHORS={'MSFT':'Dan Romanoff','AMZN':'Dan Romanoff','META':'Malik Ahmed Khan','ORCL':'Luke Yang','PLTR':'Mark Giarelli','TSM':'Phelix Lee'}
D=lambda s:datetime.strptime(s,'%d %b %Y').date().isoformat()
NEXT=lambda s:(datetime.fromisoformat(s)+timedelta(days=1)).date().isoformat()
CIDS={'MSFT':'microsoft','AMZN':'amazon','META':'meta','ORCL':'oracle','PLTR':'palantir','TSM':'tsmc'}
companies={t:{'company_id':CIDS[t],'series':[]} for t in AUTHORS}
sources=[];evidence=[];quarantine=[]
for r in json.loads((B/'manifest.json').read_text()):
 if r['status']!='retained':continue
 t=r['ticker'];p=Path(r['local_file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 txt=Path(r['text_file']).read_text();stamp=re.search(r'Report as of ([^|]+)',txt)[1].strip();rd=D(' '.join(stamp.split()[:3]));author=AUTHORS[t]
 assert author in txt[:16000],(t,author)
 pages=[(i+1,pg) for i,pg in enumerate(txt.split('\f')) if 'Financials as of' in pg]
 assert len(pages)==1,(p,len(pages))
 page,pg=pages[0];md=D(re.search(r'Financials as of (\d+ \w+ \d+)',pg)[1]);fiscal=re.search(r'Fiscal Year, ends (\d+ \w+)\s+(.+)',pg)
 endlabel=fiscal[1];years=[int(x) for x in re.findall(r'\b20\d{2}\b',fiscal[2])];assert len(years)==8,(p,years)
 rows=re.findall(r'^(Adjusted )?Earnings Per Share \(Diluted\) \((USD|TWD)\)\s+(.+)$',pg,re.M);assert len(rows)==2,(p,rows)
 source_id='morningstar-'+t.lower()+'-'+r['sha256'][:12]
 sources.append({'id':source_id,'company_id':CIDS[t],'firm':'Morningstar','analyst':author,'source_url':r['source_url'],'source_file':PREFIX+p.name,'source_sha256':r['sha256'],'text_file':PREFIX+Path(r['text_file']).name,'report_date':rd,'printed_report_timestamp':stamp,'model_date':md,'url_date':r['url_date'],'retrieved_at':r['retrieved_at'],'page':str(page),'original_available_at':None,'availability_basis':'report_date_plus_one_calendar_day_assumption','status':'retained_original_distributor_pdf'})
 for adj,cur,nums in rows:
  vals=[float(x.replace(',','')) for x in nums.split()];assert len(vals)==8,(p,vals)
  basis='adjusted_diluted' if adj else 'morningstar_unadjusted_diluted';sid=f'{t.lower()}-morningstar-'+('adjusted' if adj else 'unadjusted')
  series=next((s for s in companies[t]['series'] if s['id']==sid),None)
  if series is None:
   series={'id':sid,'label':'Morningstar / '+author+(' (adjusted diluted)' if adj else ' (unadjusted diluted)'),'analyst':author,'firm':'Morningstar','accounting_basis':basis,'currency':cur,'series_type':'individual_analyst_forecast','coverage_note':'Numerical annual forecasts printed in the Morningstar Valuation Model Summary. Model date is the Financials as of date; report date is the publication header. Report-date plus one calendar day is an assumed availability date, not verified historical access. '+('TWD per ordinary share; excluded from USD-per-ADS dashboard series. No explicit report FX conversion suitable for EPS was found.' if t=='TSM' else 'USD per listed common share. Morningstar unadjusted EPS is not asserted equivalent to issuer GAAP EPS. Reported and adjusted series stay separate.'),'snapshots':[]}
   companies[t]['series'].append(series)
  snap={'id':source_id+('-adj' if adj else '-unadj'),'report_date':rd,'model_date':md,'available_date':NEXT(rd),'availability_basis':'report_date_plus_one_calendar_day_assumption','share_basis_date':rd,'source_url':r['source_url'],'source_file':PREFIX+p.name,'source_sha256':r['sha256'],'kind':'annual','estimates':[],'retrieved_at':r['retrieved_at'],'printed_report_timestamp':stamp,'url_date':r['url_date']}
  for y,v in zip(years[3:],vals[3:]):
   end=datetime.strptime(f'{y} {endlabel}','%Y %d %b').date();start=end.replace(year=end.year-1)+timedelta(days=1)
   notes=f'Printed row: {adj}Earnings Per Share (Diluted) ({cur}). First three columns are Actual; last five are Forecast. Financials as of {md}.'
   if t=='TSM':notes+=' TWD per ordinary share, not USD per ADR. No conversion applied.'
   e={'observation_id':snap['id']+f'-fy{y}','fiscal_period':f'FY{y}','fiscal_period_start':start.isoformat(),'fiscal_period_end':end.isoformat(),'eps':v,'source_page':str(page),'notes':notes}
   snap['estimates'].append(e);evidence.append(dict(e,company_id=CIDS[t],source_id=source_id,report_date=rd,model_date=md,available_date=NEXT(rd),printed_report_timestamp=stamp,analyst=author,firm='Morningstar',currency=cur,unit='TWD_per_ordinary_share' if t=='TSM' else 'USD_per_listed_share',accounting_basis=basis,source_url=r['source_url'],source_file=PREFIX+p.name,source_sha256=r['sha256']))
  series['snapshots'].append(snap)
# Original iFAST public article API holds the publisher's HTML and publication metadata.
ifast={'id':'tsm-ifast-bloomberg-composite','label':'iFAST / Bloomberg compilation (basis unspecified)','analyst':'iFAST Research Team','firm':'iFAST / Bloomberg compilation','accounting_basis':'unspecified','currency':'USD','series_type':'publisher_composite','coverage_note':'Published EPS in USD for TSM ADR, attributed to Bloomberg and iFAST Compilation. No named individual analyst, contributor count, basic/diluted definition, or adjusted/reported basis is given. Do not combine with named Morningstar estimates or issuer GAAP EPS. Table data date is a printed data-as-of date; publication date plus one calendar day is assumed availability. Retained original public article API JSON includes content HTML and exact publication timestamp.','snapshots':[]}
for r in json.loads((B/'ifast_api_manifest.json').read_text()):
 p=Path(r['file']);j=json.loads(p.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];soup=BeautifulSoup(j['content'],'html.parser')
 table=next(tb for tb in soup.find_all('table') if 'TSM ADR' in tb.get_text());tx=' '.join(table.get_text(' ',strip=True).split());model=re.search(r'Data as of (\d+ \w+ 20\d{2})',tx)[1];md=datetime.strptime(model,'%d %B %Y').date().isoformat();pub=datetime.strptime(j['publishedDate'],'%b %d, %Y %I:%M:%S %p');rd=pub.date().isoformat();url='https://fsm.global/sg/article/rcms'+r['id'];sid='ifast-tsm-'+r['id']
 vals=[float(x) for x in re.search(r'EPS \(USD\)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',tx).groups()];assert re.search('2025A 2026E 2027E 2028E',tx)
 snap={'id':sid,'report_date':rd,'model_date':md,'available_date':NEXT(rd),'availability_basis':'report_date_plus_one_calendar_day_assumption','share_basis_date':rd,'source_url':url,'source_file':PREFIX+p.name,'source_sha256':r['sha256'],'kind':'annual','estimates':[],'retrieved_at':r['retrieved_at'],'printed_report_timestamp':j['publishedDate'],'printed_timestamp_timezone':'not stated','table_data_as_of':md}
 for y,v in zip([2026,2027,2028],vals[1:]):
  e={'observation_id':sid+f'-fy{y}','fiscal_period':f'FY{y}','fiscal_period_start':f'{y}-01-01','fiscal_period_end':f'{y}-12-31','eps':v,'source_page':'Table 4, EPS (USD) row, TSM ADR columns','notes':'Native USD per TSM ADR. Accounting basis unspecified. Table attribution: Bloomberg and iFAST Compilation. Fiscal periods interpreted as calendar years, consistent with TSMC fiscal year end. No currency conversion.'}
  snap['estimates'].append(e);evidence.append(dict(e,company_id='tsmc',source_id=sid,report_date=rd,model_date=md,available_date=NEXT(rd),printed_report_timestamp=j['publishedDate'],analyst=j['authorName'],firm=ifast['firm'],currency='USD',unit='USD_per_ADR',accounting_basis='unspecified',source_url=url,source_file=PREFIX+p.name,source_sha256=r['sha256']))
 ifast['snapshots'].append(snap);sources.append({'id':sid,'company_id':'tsmc','title':j['title'],'source_url':url,'retrieval_url':r['url'],'retrieval_method':'POST to public article-read API used by the publisher website','source_file':PREFIX+p.name,'source_sha256':r['sha256'],'analyst':j['authorName'],'firm':ifast['firm'],'report_date':rd,'printed_report_timestamp':j['publishedDate'],'printed_timestamp_timezone':'not stated','model_date':md,'model_date_kind':'printed table data-as-of','retrieved_at':r['retrieved_at'],'page':'Table 4, EPS (USD), TSM ADR','original_available_at':None,'availability_basis':'report_date_plus_one_calendar_day_assumption','status':'retained_original_publisher_json_with_html'})
companies['TSM']['series'].append(ifast)
for c in companies.values():
 for s in c['series']:s['snapshots'].sort(key=lambda x:(x['report_date'],x['printed_report_timestamp']))
export={'captured_at':datetime.now(timezone.utc).isoformat(),'cutoff':'2026-09-11','companies':[dict(c,series=[s for s in c['series'] if s['currency']=='USD']) for c in companies.values()],'sources':sources,'notes':['Dated original reports were retrieved after cutoff. Historical availability is not verified; next-calendar-day after printed report date is a transparent assumption. No current forecast values were backfilled into older snapshots.','Preserve original model dates even when a more recent report repeats a stale model. ORCL report printed 2026-09-11 is assumed available 2026-09-12 and cannot affect a 2026-09-11 chart.','Both Morningstar EPS bases are separate series; same forecast numbers in the two rows do not establish accounting equivalence.','TSM Morningstar TWD series is retained only in all_eps_evidence.json. Native USD/ADR iFAST/Bloomberg series has unspecified accounting basis.']}
(B/'dashboard_additions.json').write_text(json.dumps(export,indent=2)+'\n')
(B/'all_eps_evidence.json').write_text(json.dumps({'sources':sources,'evidence':evidence,'companies':list(companies.values())},indent=2)+'\n')
print('PDF sources',len(sources)-2,'all forecast rows',len(evidence),'USD series',sum(len(c['series']) for c in export['companies']))
for c in export['companies']:
 print(c['company_id'],[(s['id'],len(s['snapshots']),s['snapshots'][-1]['model_date']) for s in c['series']])
