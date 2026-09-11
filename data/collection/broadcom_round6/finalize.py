"""Offline reproduction of reviewed Broadcom originals and scoped evidence."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,re
B=Path(__file__).resolve().parent;ROOT=B.parents[2]
F=['observation_id','company_id','firm','analyst_name','metric','fiscal_period','value','currency','unit','basis','model_date','forecast_revision_as_of','report_date','available_at','printed_report_timestamp','original_available_at','availability_basis','source_url','local_file','page','status','notes','source_period_label','share_basis_date','source_artifact_sha256']
M=['source_url','local_file','company_ids','firm','analyst_name','report_date','retrieved_at','sha256','status','notes','text_file','report_timestamp','model_dates','http_status','report_month','report_date_precision','artifact_type','document_kind']
REVIEW={
 '20220527':('2022-05-26','Abhinav Davuluri',15,['34.95','38.86','41.06']),
 '20230706':('2023-06-01','William Kerwin',15,['42.66','44.16','47.11']),
 '20231122':('2023-08-31','William Kerwin',14,['42.95','45.19','49.41']),
 '20240321':('2024-03-07','William Kerwin',14,['48.03','64.66','76.82']),
 '20240715':('2024-06-24','William Kerwin',15,['53.37','73.48','88.29']),
 '20250127':('2024-12-12','William Kerwin',14,['6.28','7.98','10.34']),
 '20250128':('2024-12-12','William Kerwin',14,['6.28','7.98','10.34']),
 '20250130':('2024-12-12','William Kerwin',14,['6.28','7.98','10.34']),
}
obs=[];ms=[];checks=[]
for log in json.loads((B/'download_log.json').read_text()):
 if log['status']!='downloaded_original_pdf':continue
 p=ROOT/log['local_file'];text_path=ROOT/log['text_file'];text=text_path.read_text();digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==log['sha256']
 stamp=re.search(r'Report as of (\d+ \w+ \d{4}) (\d\d:\d\d), UTC',text);dt=datetime.strptime(' '.join(stamp.groups()),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc);ts=dt.isoformat()
 m=dict.fromkeys(M,'');m.update(source_url=log['source_url'],local_file=log['local_file'],company_ids='broadcom',firm='Morningstar',report_date=ts[:10],retrieved_at=log['retrieved_at'],sha256=digest,status='retained_supporting_no_annual_forecast_table',notes='Original Morningstar report, publicly distributed by Firstrade. Historical dissemination is unverified; printed report timestamp is retained separately from model date.',text_file=log['text_file'],report_timestamp=ts,http_status=200,report_month=ts[:7],report_date_precision='day',artifact_type='pdf',document_kind='broker_research_report')
 label=log['filename_date'];review=REVIEW.get(label)
 if not review:
  assert label=='20240531' and 'Analyst Historical/Forecast Summary' not in text
  m.update(analyst_name='William Kerwin',notes=m['notes']+' May31 valuation commentary and historical financials are present, but no annual forecast table was identified. No EPS forecast inferred from its P/E discussion.')
  ms.append(m);continue
 model,analyst,page,expected=review;assert analyst in text
 body=text.split('\f')[page-1];marker=re.search(r'Morningstar Analyst Historical/Forecast Summary as of\s+(\d+ \w+ \d{4})',body);assert marker
 printed_model=datetime.strptime(marker[1],'%d %b %Y').date().isoformat();assert printed_model==model<=ts[:10]
 block=body[marker.start():];lines=block.splitlines();yl=next(l for l in lines if l.startswith('Fiscal Year,'));years=re.findall(r'\b20\d{2}\b',yl)[-5:];assert len(years)==5
 notes=m['notes']+' Fiscal periods follow the original model header. EPS retains its printed split basis. The legacy EPS row does not identify the adjustment policy; no issuer GAAP or non-GAAP equivalence is assumed.'
 if label=='20220527':notes+=' Revenue is printed in whole USD billions and remains at that precision. The May26 model predates the June3 model label in the later September reprint despite matching EPS values; no dates are backdated or overwritten.'
 if label=='20230706':notes+=' Current July6 analyst note and Fair Value and Profit Drivers section are both signed William Kerwin, whose report republishes the June1 model. This is evidence for the July6 published snapshot, not a retrospective resolution of authorship in the mixed-byline June2 original.'
 if label=='20231122':notes+=' Current commentary covers VMware closing, but the numerical table is still the August31 model. Do not treat its publication as a new November numerical revision.'
 if label=='20240715':
  notes+=' Explicit split-basis proof: the forecast summary retains FY2022/FY2023 EPS37.64/42.25 with shares423m/427m; historical section on the same page already shows split-adjusted shares4230m/4270m and EPS2.65/3.30. Forecast shares441m/450m/442m and EPS53.37/73.48/88.29 are therefore pre-July2024 10:1 split. share_basis_date=2024-06-24 is proven by the model table rather than assumed from report date. The report mixes split epochs across sections.'
  assert re.search(r'Diluted Shares Outstanding \(Mil\)\s+423\s+427\s+441\s+450\s+442',block)
  assert re.search(r'Diluted Earnings Per Share\(USD\)\s+37\.64\s+42\.25\s+53\.37\s+73\.48\s+88\.29',block)
  assert '4,230' in body and '4,270' in body
 m.update(analyst_name=analyst,model_dates=model,status='downloaded_forecast_tables_verified',notes=notes)
 for metric,pat,unit,basis in [('revenue',r'^Revenue \(USD Mil\)','USD_million','total_revenue'),('revenue',r'^Revenue \(USD Bil\)','USD_billion','total_revenue'),('eps_diluted_basis_unresolved',r'^Diluted Earnings Per Share\(USD\)','USD_per_share','diluted_adjustment_basis_unresolved')]:
  line=next((l for l in lines if re.match(pat,l)),None)
  if line is None:continue
  values=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.sub(pat,'',line))[:5];assert len(values)==5
  if metric.startswith('eps'):assert values[2:]==expected
  for y,v in list(zip(years,values))[2:]:
   row=dict.fromkeys(F,'');row.update(observation_id=hashlib.sha256(f'{digest}|{page}|{metric}|{y}'.encode()).hexdigest()[:20],company_id='broadcom',firm='Morningstar',analyst_name=analyst,metric=metric,fiscal_period=f'FY{y}',value=v.replace(',',''),currency='USD',unit=unit,basis=basis,model_date=model,forecast_revision_as_of=model,report_date=ts[:10],printed_report_timestamp=ts,availability_basis='printed_report_timestamp_not_independently_verified',source_url=m['source_url'],local_file=m['local_file'],page=page,status='extracted_original_table_unscored',notes=notes,source_period_label=f'FY{y}',share_basis_date=model,source_artifact_sha256=digest);obs.append(row)
 ms.append(m);checks.append(dict(filename_date=label,model_date=model,physical_page=page,forecast_eps_verified=expected,original_hash_verified=True))
for path,fields,rows in [(B/'manifest.csv',M,ms),(B/'observations.csv',F,obs)]:
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
# Extend only the already proven December model to these exact new source copies.
previous=json.loads((ROOT/'data/collection/us_evaluation_round5/basis_alias_recommendations.json').read_text())['recommendations']
base=next(r for r in previous if r['company_id']=='broadcom' and r['model_dates']==['2024-12-12'])
selected=[m for m in ms if m['model_dates']=='2024-12-12']
new=dict(base);new.update(source_hashes=[m['sha256'] for m in selected],original_observation_ids=[r['observation_id'] for r in obs if r['model_date']=='2024-12-12' and r['fiscal_period'] in ['FY2025','FY2026'] and r['metric'].startswith('eps')],original_sources=[dict(source_url=m['source_url'],source_file=m['local_file'],source_sha256=m['sha256'],physical_page=14,report_date=m['report_date']) for m in selected])
new['status']='supported_model_period_and_source_scoped_alias'
new['limits']='Exact January2025 reprints only; FY2025/FY2026 only. Original legacy label, original model date and report timestamp stay unchanged. FY2027 remains unresolved. The later April source establishes Morningstar adjusted, not issuer non-GAAP equivalence.'
for m in selected:
 body=(ROOT/m['text_file']).read_text().split('\f')[13]
 for v in ['6.28','7.98','62,340','75,219']:assert v in body
(B/'basis_alias_recommendations.json').write_text(json.dumps({'review_date':'2026-09-10','recommendations':[new],'new_pre_2024_basis_equivalences_proven':0,'unproven':'Earlier models retain unresolved adjustment basis. Rounded narrative P/E ratios and historical actual EPS matches alone do not establish exact forecast definitions.'},indent=2)+'\n')
summary={'url_candidates':len(json.loads((B/'download_log.json').read_text())),'retained_broker_pdfs':len(ms),'originals_with_forecast_tables':len(REVIEW),'annual_observations':len(obs),'eps_observations':sum(r['metric'].startswith('eps') for r in obs),'distinct_model_dates':sorted(set(r['model_date'] for r in obs)),'model_period_source_scoped_aliases':1,'additional_supported_reprint_eps_rows':len(new['original_observation_ids']),'new_forecast_to_issuer_basis_compatibilities':0,'checks':checks}
(B/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');assert len(obs)==48 and len({r['observation_id'] for r in obs})==48
print(json.dumps({k:v for k,v in summary.items() if k!='checks'}))
