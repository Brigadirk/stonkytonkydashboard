"""Build scoped basis evidence and current forecasts from retained bridge originals."""
from pathlib import Path
from datetime import datetime, timezone
import csv,hashlib,json,re
B=Path(__file__).resolve().parent;ROOT=B.parents[2]
A=list(csv.DictReader((B/'basis_bridge/attempts.csv').open()))
F=['observation_id','company_id','firm','analyst_name','metric','fiscal_period','value','currency','unit','basis','model_date','forecast_revision_as_of','report_date','available_at','printed_report_timestamp','original_available_at','availability_basis','source_url','local_file','page','status','notes','source_period_label','share_basis_date','source_artifact_sha256']
M=['source_url','local_file','company_ids','firm','analyst_name','report_date','retrieved_at','sha256','status','notes','text_file','report_timestamp','model_dates','http_status','report_month','report_date_precision','artifact_type','document_kind']
names={'broadcom':'William Kerwin','nvidia':'Brian Colello','alphabet':'Malik Ahmed Khan','micron':'William Kerwin'}
manifest=[];obs=[];sources={}
for a in A:
 if a['status']!='downloaded_original_pdf':continue
 p=ROOT/a['source_file'] if not a['source_file'].startswith('/') else Path(a['source_file']);txt=p.with_suffix('.txt').read_text();digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==a['source_sha256']
 mt=re.search(r'Report as of (\d+ \w+ \d{4}) (\d\d:\d\d), UTC',txt);ts=datetime.strptime(' '.join(mt.groups()),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc).isoformat();c=a['company_id']
 model=re.search(r'Financials as of\s+(\d+ \w+ \d{4})\s+Actual\s+Forecast',txt)
 modeldate=datetime.strptime(model[1],'%d %b %Y').date().isoformat() if model else ''
 m=dict.fromkeys(M,'');m.update(source_url=a['source_url'],local_file=str(p.relative_to(ROOT)),company_ids=c,firm='Morningstar',analyst_name=names[c],report_date=ts[:10],retrieved_at=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),sha256=digest,status='retained_supporting_basis_evidence',notes='Original Morningstar report distributed by Firstrade, retained for exact-vector EPS basis reconciliation. Printed report time does not independently establish historical dissemination.',text_file=str(p.with_suffix('.txt').relative_to(ROOT)),report_timestamp=ts,model_dates=modeldate,http_status=200,report_month=ts[:7],report_date_precision='day',artifact_type='pdf',document_kind='broker_research_report')
 sources[f'{c}_{a["filename_date"]}']=m
 if c in ['broadcom','nvidia'] and a['filename_date']=='20250403':
  assert names[c] in txt
  m['status']='downloaded_forecast_tables_verified';m['notes']+=' Current model adds a previously absent explicit reported/adjusted EPS vintage. Revision-panel prior values are evidence only; never backdated forecasts.'
  for page,t in enumerate(txt.split('\f'),1):
   mark=re.search(r'Financials as of\s+(\d+ \w+ \d{4})\s+Actual\s+Forecast',t)
   if not mark:continue
   block=t[mark.start():];lines=block.splitlines();yearline=next(l for l in lines if l.startswith('Fiscal Year,'));years=re.findall(r'\b20\d{2}\b',yearline);assert len(years)==8
   for metric,pat,unit,basis in [('revenue',r'^Revenue \(USD Mil\)','USD_million','total_revenue'),('eps_diluted',r'^Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','reported_diluted'),('eps_adjusted_diluted',r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','adjusted_diluted')]:
    line=next(l for l in lines if re.match(pat,l));vals=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.sub(pat,'',line))[:8];assert len(vals)==8
    for y,v in list(zip(years,vals))[3:]:
     row=dict.fromkeys(F,'');row.update(observation_id=hashlib.sha256(f'{digest}|{page}|{metric}|{y}'.encode()).hexdigest()[:20],company_id=c,firm='Morningstar',analyst_name=names[c],metric=metric,fiscal_period=f'FY{y}',value=v.replace(',',''),currency='USD',unit=unit,basis=basis,model_date=modeldate,forecast_revision_as_of=modeldate,report_date=ts[:10],printed_report_timestamp=ts,availability_basis='printed_report_timestamp_not_independently_verified',source_url=a['source_url'],local_file=m['local_file'],page=page,status='extracted_original_table_unscored',notes=m['notes']+' EPS retains the printed post-2024-split share basis. Analyst-specific adjusted EPS is not assumed equivalent to issuer non-GAAP EPS.',source_period_label=f'FY{y}',share_basis_date=modeldate,source_artifact_sha256=digest);obs.append(row)
 if c=='alphabet' and a['filename_date']=='20250204':
  assert names[c] in txt
  pp=txt.split('\f');assert 'Summary as of 04 Feb 2025' in pp[18]
  assert '2023' in pp[18] and '2027' in pp[18]
  modeldate='2025-02-04';m.update(status='downloaded_forecast_tables_verified',model_dates=modeldate)
  m['notes']+=' Original legacy model spans physical pages 19-20; exact later prior vector proves this particular model reported diluted as well as adjusted diluted. Preserve original unresolved label and apply separately documented model-and-period alias.'
  for metric,basis,unit,page,values in [('revenue','total_revenue','USD_million',19,['389843','431552','474382']),('eps_diluted_basis_unresolved','diluted_adjustment_basis_unresolved','USD_per_share',20,['9.17','10.09','11.45'])]:
   for y,v in zip([2025,2026,2027],values):
    assert (f'{int(v):,}' if metric=='revenue' else v) in pp[page-1]
    row=dict.fromkeys(F,'');row.update(observation_id=hashlib.sha256(f'{digest}|{page}|{metric}|{y}'.encode()).hexdigest()[:20],company_id=c,firm='Morningstar',analyst_name=names[c],metric=metric,fiscal_period=f'FY{y}',value=v,currency='USD',unit=unit,basis=basis,model_date=modeldate,forecast_revision_as_of=modeldate,report_date=ts[:10],printed_report_timestamp=ts,availability_basis='printed_report_timestamp_not_independently_verified',source_url=a['source_url'],local_file=m['local_file'],page=page,status='extracted_original_table_unscored',notes=m['notes'],source_period_label=f'FY{y}',share_basis_date=modeldate,source_artifact_sha256=digest);obs.append(row)
 manifest.append(m)
for path,fields,rows in [(B/'manifest.csv',M,manifest),(B/'observations.csv',F,obs)]:
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
old=list(csv.DictReader((B/'basis_bridge/reference_forecasts.csv').open()))
old += [dict(company_id=r['company_id'],firm=r['firm'],forecaster=r['analyst_name'],model_date=r['model_date'],accounting_basis=r['basis'],fiscal_period=r['fiscal_period'],metric=r['metric'],value=r['value'],unit=r['unit'],source_sha256=r['source_artifact_sha256'],source_url=r['source_url'],source_file=r['local_file'],source_page=str(r['page']),report_date=r['report_date'],observation_id=r['observation_id']) for r in obs if r['company_id']=='alphabet']
configs=[
 {'company_id':'broadcom','analyst':'William Kerwin','model_dates':['2025-03-06'],'fiscal_periods':['FY2025','FY2026','FY2027'],'values':['6.39','8.05','10.77'],'revenue_values':['62567','76531','96538'],'bridge':'broadcom_20250403','page':14,'locator':'Current model 6 Mar 2025; Adjusted Earnings Per Share (Diluted) row, FY2025-FY2027.','fiscal_mapping':'Identical current and original fiscal years; no relabeling.'},
 {'company_id':'broadcom','analyst':'William Kerwin','model_dates':['2024-12-12'],'fiscal_periods':['FY2025','FY2026'],'values':['6.28','7.98'],'revenue_values':['62340','75219'],'bridge':'broadcom_20250403','page':15,'locator':'Forecast Revisions; Prior data as of 12 Dec 2024; adjusted diluted EPS prior columns 2 and 3.','fiscal_mapping':'Prior columns roll forward under current headers: printed FY2026/FY2027 contain original FY2025/FY2026 values. Earlier original supplies fiscal identity. Prior column 1 is actual FY2024 4.87, not a new FY2025 forecast. FY2027 old forecast is outside directly matched scope.'},
 {'company_id':'nvidia','analyst':'Brian Colello','model_dates':['2024-11-20'],'fiscal_periods':['FY2025','FY2026','FY2027'],'values':['2.96','4.35','5.18'],'revenue_values':['130232','195506','235623'],'bridge':'nvidia_20250403','page':17,'locator':'Forecast Revisions; Prior data as of 20 Nov 2024; all three adjusted diluted EPS prior columns.','fiscal_mapping':'Prior columns roll forward under current FY2026/FY2027/FY2028 headers but match original FY2025/FY2026/FY2027 revenue and EPS exactly. Earlier original supplies fiscal identity.'},
 {'company_id':'micron','analyst':'William Kerwin','model_dates':['2024-12-18'],'fiscal_periods':['FY2025','FY2026'],'values':['5.79','7.14'],'revenue_values':['32759','36101'],'bridge':'micron_20250403','page':14,'locator':'Forecast Revisions; Prior data as of 18 Dec 2024; adjusted diluted EPS prior columns 2 and 3.','fiscal_mapping':'Prior columns roll forward under current FY2026/FY2027 headers but contain original FY2025/FY2026. Earlier original supplies fiscal identity. Prior column 1 is FY2024 actual 1.30. FY2027 old forecast is outside directly matched scope.'},
]
configs.append({'company_id':'alphabet','analyst':'Malik Ahmed Khan','model_dates':['2025-02-04'],'fiscal_periods':['FY2025','FY2026','FY2027'],'values':['9.17','10.09','11.45'],'revenue_values':['389843','431552','474382'],'bridge':'alphabet_20250507','page':20,'locator':'Forecast Revisions; Prior data as of 4 Feb 2025; reported and adjusted diluted EPS prior rows both equal the original full forecast vector.','fiscal_mapping':'Fiscal years align directly. Original revenue/year/model-date header is on p19 and its EPS continuation is on p20. Both explicit prior EPS rows equal the old original, so reported_diluted is supported for this model only.','canonical_basis':'reported_diluted'})
recommendations=[]
for cfg in configs:
 ev=sources[cfg['bridge']];page=cfg['page'];body=(ROOT/ev['text_file']).read_text().split('\f')[page-1];line=next(l for l in body.splitlines() if l.strip().startswith('Adjusted Earnings Per Share (Diluted)'))
 matches=[r for r in old if r['company_id']==cfg['company_id'] and r['firm']=='Morningstar' and r['forecaster']==cfg['analyst'] and r['model_date'] in cfg['model_dates'] and r['accounting_basis']=='diluted_adjustment_basis_unresolved' and r['fiscal_period'] in cfg['fiscal_periods'] and r['metric'].startswith('eps')]
 assert matches,cfg
 for y,value,rev in zip(cfg['fiscal_periods'],cfg['values'],cfg['revenue_values']):
  assert value in line
  candidates=[r for r in matches if r['fiscal_period']==y];assert candidates and all(float(r['value'])==float(value) for r in candidates),(cfg,candidates)
  assert f'{int(rev):,}' in body
  assert any(r['company_id']==cfg['company_id'] and r['model_date'] in cfg['model_dates'] and r['fiscal_period']==y and r['metric']=='revenue' and float(r['value'])==(float(rev)*1000000 if r['unit']=='USD' else float(rev)) for r in old)
 orig={r['source_sha256']:{'source_url':r['source_url'],'source_file':r['source_file'],'source_sha256':r['source_sha256'],'physical_page':r['source_page'],'report_date':r['report_date']} for r in matches}
 recommendations.append({'company_id':cfg['company_id'],'firm':'Morningstar','analyst':cfg['analyst'],'original_basis':'diluted_adjustment_basis_unresolved','canonical_basis':cfg.get('canonical_basis','adjusted_diluted'),'model_dates':cfg['model_dates'],'fiscal_periods':cfg['fiscal_periods'],'status':'supported_model_and_period_scoped_alias','issuer_non_gaap_equivalence':'not_proven_do_not_score_against_issuer_non_gaap','matched_values':dict(zip(cfg['fiscal_periods'],cfg['values'])),'matched_revenue_values_usd_million':dict(zip(cfg['fiscal_periods'],cfg['revenue_values'])),'original_observation_ids':[r['observation_id'] for r in matches],'original_sources':list(orig.values()),'evidence':{'source_url':ev['source_url'],'source_file':ev['local_file'],'source_sha256':ev['sha256'],'physical_page':page,'report_date':ev['report_date'],'locator':cfg['locator'],'explicit_label_row':' '.join(line.split())},'fiscal_mapping':cfg['fiscal_mapping'],'limits':'Keep original basis and model/report dates. Do not backdate the new source or reconstruct prior reported EPS. No extension to other analysts, companies, model dates or unmatched fiscal periods.'})
(B/'basis_alias_recommendations.json').write_text(json.dumps({'review_date':'2026-09-10','recommendations':recommendations,'unproven':'Other older Morningstar model definitions remain unresolved; historical actual matches alone are not sufficient. Morningstar adjusted is not an issuer non-GAAP definition.'},indent=2)+'\n')
print(json.dumps({'retained_bridge_pdfs':len(manifest),'new_current_observations':len(obs),'new_current_eps':sum(r['metric'].startswith('eps') for r in obs),'model_scoped_basis_recommendations':len(recommendations),'existing_rows_supported':sum(len(r['original_observation_ids']) for r in recommendations)}))
