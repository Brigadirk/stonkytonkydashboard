from pathlib import Path
from decimal import Decimal
import csv,re,json,hashlib,collections
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'korean_memory'
rows=list(csv.DictReader((ROOT/'manifest.csv').open()))
extra=json.loads((ROOT/'extra_manifest.json').read_text())
rows=[r for r in rows if r['report_id']!=extra['report_id']]+[extra]
manifestfields=list(rows[0])
byid={r['report_id']:r for r in rows}
for r in rows:
 if not r['status'].endswith('text_extracted'):continue
 rid=r['report_id']
 p=43 if rid=='hyundai_6967efeebf6d' else 2 if rid=='meritz_9c6076c1bc15' else 1
 r['report_date_reliability']=f'printed_date_manually_verified_pdf_page_{p}'
 if r['firm']=='kb':r['notes']+=' Korean byline 김동원 and email jeff.kim@kbfg.com establish identity with Jeff Kim; fiscal forecasts labelled E, historical A excluded.'
 if rid=='meritz_9c6076c1bc15':r['company_ids']='samsung_electronics;sk_hynix';r['notes']+=' Extracted company-specific models at physical PDF pages 11 and 15; section author Sunwoo Kim shown at pages 7 and 12; cover publication date page 2.'
 if rid=='hyundai_6967efeebf6d':r['notes']+=' Both company sections explicitly dated 2021.11.16, physical PDF pages 43 and 49; original printed pages 41 and 47. Cover lacks extractable date; filename not used as date.'
 if rid=='hana_5168582676aa':
  r['analyst_name']='Kim Kyung-min; Rok-ho Kim; Hyun-soo Kim'
  r['notes']+=' Samsung model physical page 6 is jointly signed by 김경민, 김록호 and 김현수; contents page credits Kim Kyung-min. Joint attribution review required; do not assign whole model exclusively to Rok-ho Kim.'
 if rid=='hana_ab82a6bd0339':
  r['analyst_name']='Rok-ho Kim; 변운지'
  r['notes']+=' Physical page 1 signs both 김록호 and 변운지 as Analyst, rather than RA; joint attribution review required. Recommendation disclosure records 담당자 변경 on 2022-05-06; earlier forecasts cannot be assigned by current byline alone.'

obs=[]
num=r'\(?-?\d[\d,]*(?:\.\d+)?\)?'
def vals(s):return re.findall(num,s)
def decimal(s):return Decimal(s.replace(',','').replace('(','-').replace(')',''))
def pages(r):
 s=(ROOT/r['text_file']).read_text();a=re.split(r'=== PDF PAGE (\d+) ===\n',s)
 return {int(a[i]):a[i+1] for i in range(1,len(a),2)}
def add(r,company,page,year,metric,v,basis,raw,source='individual_analyst_forecast',note=''):
 joint=r['report_id'] in ('hana_5168582676aa','hana_ab82a6bd0339') and source=='individual_analyst_forecast'
 if joint:source='joint_team_forecast';note+=' Jointly signed company model; attribution review required before individual analyst comparisons. '+r['notes']
 scale=10**9 if metric=='revenue' else 1
 if metric=='eps':note+=' Basic/diluted, preferred/common and share-count denominator must be reconciled before accuracy scoring.'
 o=dict(report_id=r['report_id'],company_id=company,ticker={'sk_hynix':'000660.KS','samsung_electronics':'005930.KS'}[company],firm=r['firm'],analyst_name=r['analyst_name'] if source!='report_embedded_consensus' else '',source_type=source,report_date=r['report_date'],report_date_reliability=r['report_date_reliability'],target_period=f'FY{year}',target_period_end=f'{year}-12-31',metric=metric,currency='KRW',value=str(decimal(v)*scale),original_value=v,original_unit='KRW billion' if metric=='revenue' else 'KRW per share',basis=basis,pdf_page=page,source_url=r['source_url'],local_file=r['local_file'],text_file=r['text_file'],sha256=r['sha256'],retrieved_at=r['retrieved_at'],extraction_status='attribution_review_joint_model_unscored' if joint else 'parsed_explicit_forecast_table_unscored',time_relation='past_fiscal_year_estimate' if int(year)<int(r['report_date'][:4]) else 'current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=raw.strip(),notes=note.strip())
 obs.append(o)
def columnmodel(r,company,page,t,header_pattern,rev_pattern,eps_pattern,basis):
 h=re.search(header_pattern,t,re.M);assert h,(r['report_id'],page,'header')
 years=re.findall(r'\b(20\d{2})([AEF]?)\b',h[1]);assert len(years)>=2,(r['report_id'],'years',h[0])
 for metric,pattern in [('revenue',rev_pattern),('eps',eps_pattern)]:
  m=re.search(pattern,t,re.M);assert m,(r['report_id'],metric)
  ns=vals(m[1]);assert len(ns)==len(years),(r['report_id'],metric,ns,years)
  for (year,flag),v in zip(years,ns):
   if flag in 'EF' and flag:add(r,company,page,year,metric,v,basis,m[0],note='Explicit '+flag+' forecast column; actual columns omitted.')
def hanamodel(r,company,page,t):
 financial=t.split('Financial Data',1)[1]
 columnmodel(r,company,page,financial,r'^\s*투자지표\s+([^\n]+)',r'^\s*매출액\s+(?:십억원\s+)?([^\n]+)',r'^\s*EPS\s+(?:원\s+)?([^\n]+)','Hana Financial Data forecast table; consolidated company revenue; EPS definition retained as printed, not normalized')
 consensus=t.split('Consensus Data',1)[1].split('Stock Price',1)[0].split('Financial Data',1)[0]
 # In older reports the annual consensus header shares the line with KOSPI data.
 h=re.search(r'(20\d{2})\s+(20\d{2})\s*$',consensus,re.M);assert h,(r['report_id'],'consensusheader')
 years=list(h.groups())
 for metric,pattern in [('revenue',r'매출액\(십억원\)\s+([^\n]+)'),('eps',r'EPS\(원\)\s+([^\n]+)')]:
  m=re.search(pattern,consensus);assert m,(r['report_id'],'consensus',metric)
  ns=vals(m[1]);assert len(ns)==2,(r['report_id'],'consensuscols',ns)
  for year,v in zip(years,ns):add(r,company,page,year,metric,v,'Report-embedded consensus; contributor set, original timestamp and comparable EPS definition unknown',m[0],'report_embedded_consensus','Separate consensus baseline printed within broker report; not the author forecast or a live consensus observation.')

for r in rows:
 if not r['status'].endswith('text_extracted'):continue
 pp=pages(r);rid=r['report_id']
 if r['firm']=='kb':
  t=pp[1].split('Earnings Forecast & Valuation',1)[1]
  columnmodel(r,r['company_ids'],1,t,r'^\s*결산기말\s+([^\n]+)',r'^\s*매출액\s*\(십억원\)\s+([^\n]+)',r'^\s*EPS\s*\(원\)\s+([^\n]+)','KB consolidated forecast table; EPS appears beneath parent-attributable net income, denominator unresolved')
 elif r['firm']=='hana':
  sections={
   'hana_b522033f41d4':[(1,'sk_hynix')],
   'hana_ab82a6bd0339':[(1,'sk_hynix')],
   'hana_5168582676aa':[(6,'samsung_electronics')],
   'hana_43c8d0a3cb24':[(6,'sk_hynix')],
   'hana_682666e476f1':[(31,'samsung_electronics'),(39,'sk_hynix')],
  }[rid]
  for pg,company in sections:hanamodel(r,company,pg,pp[pg])
 elif r['firm']=='meritz':
  for pg,company in [(11,'samsung_electronics'),(15,'sk_hynix')]:
   columnmodel(r,company,pg,pp[pg],r'^\s*\(십억원\)\s+([^\n]+)',r'^\s*매출액\s+([^\n]+)',r'^\s*EPS\(지배주주\)\s+([^\n]+)','Meritz consolidated company model; EPS explicitly parent-attributable; detailed financial table uses KRW billion')
 elif r['firm']=='hyundai':
  sections=[(43,'samsung_electronics'),(49,'sk_hynix')] if rid=='hyundai_6967efeebf6d' else [(1,'sk_hynix')]
  for pg,company in sections:
   t=pp[pg]
   for line in t.splitlines():
    m=re.match(r'^\s*(20\d{2})F\s+(.+)$',line)
    if not m:continue
    ns=vals(m[2]);assert len(ns)>=5,(rid,pg,'hyundaivals')
    for metric,pos in [('revenue',0),('eps',4)]:add(r,company,pg,m[1],metric,ns[pos],'Consolidated K-IFRS annual summary as printed; EPS denominator unresolved',line,note='Explicit F annual row; historical rows and Before revision values omitted. Annual EPS agrees with same-page After revision box for its two overlapping years.')
   h=re.search(r'EPS\((\d{2})F\)\s+EPS\((\d{2})F\)',t);assert h,(rid,'hyundaiconsheader')
   m=re.search(r'^\s*Consensus\s+([^\n]+)',t,re.M);assert m,(rid,'hyundaicons')
   ns=vals(m[1]);assert len(ns)==3,(rid,'hyundaiconsvals',ns)
   for y,v in zip(h.groups(),ns[:2]):add(r,company,pg,'20'+y,'eps',v,'Report-embedded FnGuide consensus EPS; accounting definition/contributor set/original timestamp unknown',m[0],'report_embedded_consensus','Same-page revision box labels these values Consensus; target price column excluded.')

# Canonicalized provenance keys must not duplicate the prior round.
def key(o):
 c={'000660':'sk_hynix','005930':'samsung_electronics'}.get(o['company_id'],o['company_id'])
 return (o['source_url'],c,o['target_period'],o['metric'],o['source_type'])
oldkeys={key(o) for o in csv.DictReader((OLD/'observations.csv').open())}
assert len({key(o) for o in obs})==len(obs),'round-two duplicates'
assert not oldkeys.intersection(key(o) for o in obs),'duplicate prior observations'
# Every value must independently appear on the physical page in Poppler layout text.
issues=[]
for r in rows:
 if not r['status'].endswith('text_extracted'):continue
 assert hashlib.sha256((ROOT/r['local_file']).read_bytes()).hexdigest()==r['sha256']
 assert '2021-09-10'<=r['report_date']<='2026-09-10'
for o in obs:
 r=byid[o['report_id']]
 lp=(ROOT/r['layout_text_file']).read_text().split('\f')[int(o['pdf_page'])-1]
 if o['original_value'] not in lp:issues.append({'report_id':o['report_id'],'page':o['pdf_page'],'value':o['original_value'],'metric':o['metric']})
assert not issues,issues
with (ROOT/'manifest.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=manifestfields);w.writeheader();w.writerows(rows)
fields=next(csv.reader((OLD/'observations.csv').open()))
with (ROOT/'observations.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(obs)
summary=dict(manifest_records=len(rows),new_downloaded_pdfs=sum(r['status']=='downloaded_text_extracted' for r in rows),reused_original_pdfs=sum(r['status']=='preserved_prior_download_text_extracted' for r in rows),failed_or_non_pdf=sum(not r['status'].endswith('text_extracted') for r in rows),total_pdf_pages=sum(int(r['page_count']) for r in rows if r['page_count']),observations=len(obs),observations_by_source_type=dict(collections.Counter(o['source_type'] for o in obs)),observations_by_firm=dict(collections.Counter(o['firm'] for o in obs)),observations_by_publication_year=dict(sorted(collections.Counter(o['report_date'][:4] for o in obs).items())),observations_by_status=dict(collections.Counter(o['extraction_status'] for o in obs)),past_fiscal_year_estimates=sum(o['time_relation']=='past_fiscal_year_estimate' for o in obs),earliest_report=min(o['report_date'] for o in obs),latest_report=max(o['report_date'] for o in obs),prior_observation_overlap=0,duplicate_observations=0,hash_verification='all_saved_pdfs_passed',independent_poppler_value_checks=len(obs),issues=issues)
(ROOT/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(ROOT/'extraction_gaps.json').write_text(json.dumps([{'report_id':r['report_id'],'reason':r['notes']} for r in rows if not r['status'].endswith('text_extracted')],ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
