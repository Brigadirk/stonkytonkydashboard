"""Reproduce manually reviewed forecast facts; preserve source units and provenance."""
import csv, hashlib, json, re
from pathlib import Path
BASE=Path('data/collection/asml_sandisk_round4')
with (BASE/'downloaded_sources.csv').open() as f: sources={r['key']:r for r in csv.DictReader(f)}
HANAFIRM='Hana Securities (Bloomberg consensus)'
ADJ='Bloomberg-adjusted EPS; basic/diluted denominator unspecified'
UNSPEC='Bloomberg consensus EPS; adjustment and dilution unspecified'
META={
 'hana_asml_20210722':('asml',HANAFIRM,'2021-07-22','day','downloaded_forecast_tables_verified','Printed date on page 1. July 2021 source is warmup for September 2021 start. Precise EPS on p2; adjusted label on p4.'),
 'hana_asml_20211001':('asml',HANAFIRM,'2021-10-01','day','downloaded_forecast_tables_verified','Printed date 1 October; URL includes September30. EPS precise annual table p2; adjusted label p5.'),
 'hana_asml_20220120':('asml',HANAFIRM,'2022-01-20','day','downloaded_forecast_tables_verified','Printed date January20; URLJanuary19. EUR p2 and USD p3 tables coexist. Only EUR extracted. p5 labels adjusted EPS.'),
 'hana_asml_20230425':('asml',HANAFIRM,'2023-04-25','day','downloaded_forecast_tables_verified','Daily original. ASML table physicalp11 / printedp10 explicitly Bloomberg market consensus. Exact adjustment/dilution unspecified.'),
 'hana_asml_20240718':('asml',HANAFIRM,'2024-07-18','day','downloaded_forecast_tables_verified','Detailed p4 explicitly EUR per-share and Bloomberg-adjusted consensus. Cover EPS(USD) and BE Semiconductor footer are template inconsistencies; detailed model identifies ASML throughout.'),
 'hana_asml_20241017':('asml',HANAFIRM,'2024-10-17','day','downloaded_forecast_tables_verified','Detailed p5 explicitly EUR per-share and Bloomberg-adjusted consensus. Cover EPS(USD) conflicts with this detailed currency header; use detailed model.'),
 'hana_asml_20251017':('asml',HANAFIRM,'2025-10-17','day','downloaded_forecast_tables_verified','Detailed p5 explicitly EUR and Bloomberg-adjusted consensus. Historical EPS cells repeat 19.3; those historical cells are not extracted. ForwardFY2025/26 headers and values are retained exactly.'),
 'hana_asml_20260416':('asml',HANAFIRM,'2026-04-16','day','downloaded_reprint_not_reextracted','Detailed p5 repeats the complete annual table from January30 original, including identical forward EPS/revenue. No new model observations extracted. Cover EPS(USD) conflicts with detailed EUR header.'),
 'hana_asml_20260129':('asml',HANAFIRM,'2026-01-30','day','downloaded_forecast_tables_verified','Printed date January30; URL January29. Original linked by Hana analyst public Telegram post ITforYouFromHana/10306 on January29. Detailed p5 EUR Bloomberg-adjusted consensus. April16 report repeats this same table and is not counted as a fresh model revision.'),
 'hana_global_20260109':('asml;sandisk',HANAFIRM,'2026-01-12','day','downloaded_forecast_tables_verified','Cover image states 2026.1.12; PDF creationJanuary9 and URL are not publication dates. Sandisk physicalp73/printed72 explicitly standalone2025 spin-off and Bloomberg consensus. ASML section is USD, not admitted to EUR model.'),
 'zacks_sandisk_retrieved':('sandisk','Zacks Investment Research','2026-09-10','retrieval_day','downloaded_current_consensus_snapshot','Mutable PDF generated on retrieval Sept10; original URLdates2015/2025 do not date contents. No historical backfill. Search-index June snapshot differs from retrieved bytes.'),
 'mirae_daily_20220121':('asml','Mirae Asset Securities','2022-01-21','day','downloaded_attribution_requires_review','Outer daily dateJan21; embedded ASML note Jan20. Table statesGAAP with ASML/Bloomberg/Mirae sources; does not explicitly identify forecast ownership. Quarantined.'),
 'oneil_asml_20240902':('asml',"William O'Neil + Co.",'','unknown','downloaded_availability_and_attribution_require_review','Chart says weekly asofAug30,2024; file createdSep2,2024. Exact publication and estimate contributor/methodology not established; quarantined.'),
 'hana_global_20240111':('asml',HANAFIRM,'','unknown','downloaded_report_date_requires_review','ASML physicalp44 / printed74 provides onlyFY2023/FY2024 estimates. Exact publication date not reviewed; no rows admitted.'),
 'hana_daily_20241018':('asml',HANAFIRM,'2024-10-18','day','downloaded_reprint_not_reextracted','Daily reprints standalone October17 ASML model, now retained directly. Not counted as a new model revision.'),
}
MS_META={
 '20250815':('2025-08-15T23:14:00+00:00','2025-08-14',9),
 '20251106':('2025-11-07T02:59:00+00:00','2025-11-06',10),
 '20251107':('2025-11-08T00:46:00+00:00','2025-11-06',10),
 '20260130':('2026-01-30T06:04:00+00:00','2026-01-29',10),
 '20260430':('2026-05-01T03:05:00+00:00','2026-04-30',11),
 '20260819':('2026-08-19T18:04:00+00:00','2026-08-19',12),
}
for day,(stamp,model,page) in MS_META.items():
 notes='Original Morningstar report distributed by Firstrade; named model author William Kerwin. Standalone post-February2025 Sandisk. Printed summary distinguishes reported diluted EPS from adjusted diluted EPS, in USD. Fiscal years mapped to issuer June-ending years.'
 status='downloaded_forecast_tables_verified'
 if day=='20250815':
  notes+=' Summary says fiscal year ends31Dec, a source header error: June2025 actual revenue7355 and both EPS values match Sandisk fiscal2025, and November7 p11 reproduces the August model FY2026-28 revenue/EPS exactly under its corrected June-year context. Original year numbers preserved; fiscal end corrected from issuer calendar, not shifted to calendar years.'
 if day=='20251107':
  status='downloaded_reprint_not_reextracted'; notes+=' November8 report retains November6 model already retained in November7 report; no additional observations.'
 META['morningstar_sandisk_'+day]=('sandisk','Morningstar',stamp[:10],'minute',status,notes)
rows=[]

def add(key,company,metric,period,number,page,basis,*,status='extracted_original_table_unscored',currency='EUR',model_date='',current=False):
 s=sources[key];firm=META[key][1];report_date=META[key][2]
 unit=(currency+'_million') if metric=='revenue' else currency+'_per_share'
 p=Path(s['text_file']).read_text().split('\f')[page-1]
 assert re.sub(r'[,\s]','',str(number)) in re.sub(r'[,\s]','',p), (key,number,page)
 is_consensus=key!='oneil_asml_20240902'
 row=dict(observation_id=hashlib.sha256(f'{key}|{company}|{metric}|{period}|{number}|{page}'.encode()).hexdigest()[:20],company_id=company,firm=firm,analyst_name='',metric=metric,fiscal_period=f'FY{period}',value=str(number),currency=currency,unit=unit,basis=basis,model_date=model_date,forecast_revision_as_of='',report_date=report_date,available_at='',printed_report_timestamp='',original_available_at=s['retrieved_at'] if current else '',availability_basis='current_snapshot_retrieved_at' if current else 'printed_report_date_not_independently_verified',source_url=s['source_url'],local_file=s['local_file'],page=page,status=status,notes=META[key][5]+' Original historical dissemination time remains unverified.' if not current else META[key][5]+' Retrieval timestamp records observed availability, not model revision time.',forecast_type='consensus_reported_by_analyst' if is_consensus and key!='zacks_sandisk_retrieved' else '',source_type='published_consensus' if key=='zacks_sandisk_retrieved' else ('report_embedded_consensus' if is_consensus else 'publisher_forecast_unattributed'),source_period_label=f'FY{period} forecast',source_artifact_sha256=s['sha256'])
 if key in ['hana_asml_20210722','hana_asml_20211001','hana_asml_20220120']:
  row['source_period_label']=f'FY {period} 예상'
 elif key=='hana_global_20260109': row['source_period_label']=f'FY {period}(E)'
 elif key.startswith('hana_asml_'): row['source_period_label']=f'{period}F'
 elif key=='zacks_sandisk_retrieved': row['source_period_label']=('Current Year' if period==2027 else 'Next Year')+f' (06/{period})'
 rows.append(row)

# Exact EUR tables, preserving adjusted label corroborated in the same report.
for key,years,eps,revenue,page in [
 ('hana_asml_20210722',[2021,2022],['12.56','15.24'],['18125','20666'],2),
 ('hana_asml_20211001',[2021,2022,2023,2024,2025],['13.50','16.57','18.75','20.97','23.29'],['18908','21766','23607','25261','27679'],2),
 ('hana_asml_20220120',[2022,2023,2024,2025,2026],['16.98','19.23','21.48','25.12','22.25'],['22105','23441','25807','28660','28556'],2),
 ('hana_asml_20240718',[2024,2025],['18.8','29.9'],['27216','36040'],4),
 ('hana_asml_20241017',[2024,2025],['18.8','28.9'],['27752','35951'],5),
 ('hana_asml_20251017',[2025,2026],['24.5','25.7'],['32454','33821'],5),
 ('hana_asml_20260129',[2026,2027],['28.4','36.5'],['36236','42620'],5),
]:
 for year,e,r in zip(years,eps,revenue):
  add(key,'asml','eps_adjusted',year,e,page,ADJ)
  add(key,'asml','revenue',year,r,page,'total_revenue')
for year,e,r in [(2023,'18.8','26496'),(2024,'22.7','29543')]:
 add('hana_asml_20230425','asml','eps_unspecified',year,e,11,UNSPEC)
 add('hana_asml_20230425','asml','revenue',year,r,11,'total_revenue')
for year,e,r in [(2026,'12.61','10618'),(2027,'21.84','12991')]:
 add('hana_global_20260109','sandisk','eps_unspecified',year,e,73,UNSPEC,currency='USD')
 add('hana_global_20260109','sandisk','revenue',year,r,73,'total_revenue',currency='USD')
for year,e,r in [(2027,'208.92','49248'),(2028,'252.16','58456')]:
 add('zacks_sandisk_retrieved','sandisk','eps_unspecified',year,e,1,'Zacks consensus EPS; adjustment and dilution unspecified',currency='USD',current=True)
 add('zacks_sandisk_retrieved','sandisk','revenue',year,r,1,'total_revenue',currency='USD',current=True)
for year,e,r in [(2022,'16.9','22.1'),(2023,'19.4','24.5'),(2024,'22.0','26.4')]:
 add('mirae_daily_20220121','asml','eps_unspecified',year,e,7,'GAAP EPS; basic/diluted denominator unspecified',status='quarantined_forecast_attribution_not_explicit',model_date='2022-01-20')
 # Revenue is inEURbillion; add handlesEPS directly, then set sourceunit after append.
 add('mirae_daily_20220121','asml','revenue',year,r,7,'total_revenue',status='quarantined_forecast_attribution_not_explicit',model_date='2022-01-20')
 rows[-1]['unit']='EUR_billion'
for year,e in [(2024,'18.88'),(2025,'29.87')]:
 add('oneil_asml_20240902','asml','eps_unspecified',year,e,1,'EPS definition and contributor unspecified',status='quarantined_publication_date_and_attribution',model_date='2024-08-30')

# The annual forecast columns are transcribed directly, never inferred from P/E.
for day,years,revenue,diluted,adjusted in [
 ('20250815',range(2026,2031),['8318','8828','8334','9001','9397'],['3.35','5.03','2.78','4.14','4.59'],['4.77','6.70','4.54','6.07','6.53']),
 ('20251106',range(2026,2031),['10504','12669','11402','11903','12427'],['11.26','17.19','9.40','10.14','10.93'],['12.94','18.51','11.15','12.06','12.85']),
 ('20260130',range(2026,2031),['16807','36206','34757','22940','22022'],['48.56','138.52','114.75','44.50','43.20'],['50.81','139.90','116.52','46.43','45.13']),
 ('20260430',range(2026,2031),['19735','45933','46461','24880','23885'],['69.87','201.80','192.58','71.35','63.90'],['72.22','203.19','194.38','73.34','65.88']),
 ('20260819',range(2027,2032),['51719','68996','45050','27030','27570'],['230.49','318.49','179.39','71.75','69.43'],['231.79','320.21','181.44','74.18','72.22']),
]:
 key='morningstar_sandisk_'+day;stamp,model,page=MS_META[day]
 for year,r,e,a in zip(years,revenue,diluted,adjusted):
  for metric,value,basis in [('revenue',r,'total_revenue'),('eps_diluted',e,'reported_diluted'),('eps_adjusted_diluted',a,'adjusted_diluted')]:
   add(key,'sandisk',metric,year,value,page,basis,currency='USD',model_date=model)
   rows[-1].update(analyst_name='William Kerwin',forecast_type='analyst_forecast',source_type='individual_analyst_forecast',printed_report_timestamp=stamp,forecast_revision_as_of=model,availability_basis='printed_report_timestamp_not_independently_verified',source_period_label=f'{year} Forecast')

fields=['source_url','local_file','company_ids','firm','analyst_name','report_date','retrieved_at','sha256','status','notes','text_file','report_timestamp','model_dates','http_status','report_month','report_date_precision','artifact_type']
manifest=[]
for key,s in sources.items():
 company,firm,day,precision,status,notes=META[key]
 ms=MS_META.get(key.removeprefix('morningstar_sandisk_')) if key.startswith('morningstar_sandisk_') else None
 manifest.append(dict(source_url=s['source_url'],local_file=s['local_file'],company_ids=company,firm=firm,analyst_name='William Kerwin' if ms else '',report_date=day,retrieved_at=s['retrieved_at'],sha256=s['sha256'],status=status,notes=notes,text_file=s['text_file'],report_timestamp=ms[0] if ms else '',model_dates=ms[1] if ms else '',http_status=s['http_status'],report_month=day[:7],report_date_precision=precision,artifact_type='pdf'))
# Record a bounded failed source route rather than dropping the failure.
manifest.append(dict(source_url='https://cantorfitzgerald.ie/wp-content/uploads/2023/12/ASML-Research-Note-Jan-23-1.pdf',local_file='',company_ids='asml',firm='Cantor Fitzgerald',analyst_name='',report_date='',retrieved_at='',sha256='',status='download_failed_http403',notes='Direct source fetch403; no PDF or numbers retained, no date inferred from URL.',text_file='',report_timestamp='',model_dates='',http_status='403',report_month='',report_date_precision='unknown',artifact_type='unavailable'))
with (BASE/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(manifest)
with (BASE/'observations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(dict(retained_pdfs=len(sources),observations=len(rows),quarantined=sum(r['status'].startswith('quarantined') for r in rows),annual_eps=sum(r['metric'].startswith('eps') for r in rows)),indent=2))
