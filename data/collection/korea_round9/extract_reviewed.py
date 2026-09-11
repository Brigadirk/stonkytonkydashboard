"""Offline extraction from reviewed original broker annual models.

No implied EPS, no consensus substitution, and no availability inferred from a
Telegram date. Separate archive evidence can establish an available-by bound.
"""
from pathlib import Path
from decimal import Decimal
import csv, json, hashlib, re, collections

BASE = Path(__file__).resolve().parent
FIELDS = ['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','model_date','share_basis_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
MAN = ['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window','document_kind']
MERITZ_BASIS = 'EPS labelled parent-attributable; basic/diluted and share denominator not established'
MIRAE_BASIS = 'Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS'
# Physical PDF page, company, first annual forecast, exact printed EPS vector.
REVIEWED = {
 'meritz_samsung_20220128': [(1,'samsung_electronics',2022,['6465','8417'])],
 'meritz_hynix_20220203': [(1,'sk_hynix',2022,['14971','25264'])],
 'meritz_hynix_20220428': [(1,'sk_hynix',2022,['16603','21878'])],
 'meritz_samsung_20220429': [(1,'samsung_electronics',2022,['7065','8364'])],
 'meritz_samsung_20230131': [(1,'samsung_electronics',2023,['2097','4861'])],
 'meritz_samsung_20230427': [(1,'samsung_electronics',2023,['1461','5225','7417'])],
 'meritz_sector_20231108': [(10,'sk_hynix',2023,['-10838','10048','16251'])],
 'meritz_hynix_20240126': [(1,'sk_hynix',2024,['10624','18030'])],
 'meritz_sector_20240910': [(7,'sk_hynix',2024,['24291.0','39680.7','44195.8']),(11,'samsung_electronics',2024,['5378','7413','7942'])],
 'meritz_hynix_20251111': [(6,'sk_hynix',2025,['53084','78132','88662'])],
 'meritz_sector_20251114': [(11,'samsung_electronics',2025,['5043','7613','8041'])],
 'mirae_hynix_20260609': [(1,'sk_hynix',2026,['329362','466282','497630'])],
}
EXCLUDED = {
 'meritz_hynix_20210201':'Issue comment on earnings, no explicit annual EPS forecast table.',
 'meritz_hynix_review_20210428':'Earnings conference Q&A, no explicit annual EPS forecast table.',
 'meritz_samsung_20210430':'Issue comment printed April29 2021, no explicit annual EPS forecast table.',
 'meritz_sector_20250305':'Sector excerpt has no annual SK hynix or Samsung EPS model; global company tables are outside this collection.',
 'meritz_sector_20251117':'Pentabooking industry issue comment, no annual EPS model.',
 'meritz_sector_20251205':'Industry financing/regulation issue comment, no annual EPS model.',
 'mirae_hynix_20260729':'Original says earnings estimates are unchanged. FY26-28 EPS 295026/415482/442513 differ from June9. The intervening original model date is unknown; June25 target-price history is not evidence of the EPS model date. Supporting source only; not introduced as a fresh July29 earnings model.',
}
DATE_OVERRIDE = {'meritz_hynix_20240126':'2024-01-25','meritz_samsung_20210430':'2021-04-29'}
IMAGE_COVERS = {'meritz_sector_20231108','meritz_sector_20240910','meritz_sector_20250305','meritz_hynix_20251111','meritz_sector_20251114'}

def write(path, fields, rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def nums(s):
 return re.findall(r'-?\d[\d,]*(?:\.\d+)?',s)

def main():
 logs=[]
 for name in ['download_log.json','download_log_company.json','download_log_alternatives.json']:
  logs += json.loads((BASE/name).read_text())
 obs=[];man=[];checks=[]
 for log in logs:
  key=log['key'];m={k:'' for k in MAN}
  m.update({k:log.get(k,'') for k in ['source_url','local_file','text_file','sha256','retrieved_at','discovery_url','page_count']})
  mirae=key.startswith('mirae_')
  m.update(report_id=key,firm='mirae' if mirae else 'meritz',analyst_name='Young-gun Kim' if mirae else 'Sunwoo Kim',collection_window='same_author_public_history_and_archive_availability_2021_2026',document_kind='broker_research_report')
  if not log.get('sha256'):
   m.update(status='non_pdf_destination' if key=='meritz_sector_20251210' else 'public_retrieval_failed',notes=log.get('error',''));man.append(m);continue
  assert hashlib.sha256((BASE/log['local_file']).read_bytes()).hexdigest()==log['sha256'],key
  text=(BASE/log['text_file']).read_text();pages=text.split('\f')
  stamp=key[-8:];date=f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}'
  m['report_date']=DATE_OVERRIDE.get(key,date)
  if key in IMAGE_COVERS:
   m['report_date_reliability']='printed_date_visually_verified_physical_page_1_image_cover'
  elif mirae:
   assert ('June 9, 2026' if key.endswith('20260609') else 'July 29, 2026') in pages[0]
   m['report_date_reliability']='printed_date_verified_physical_page_1'
  else:
   found=re.search(r'(202\d)\.\s*(\d{1,2})\.\s*(\d{1,2})',text)
   assert found,key
   actual=f'{found[1]}-{found[2].zfill(2)}-{found[3].zfill(2)}'
   assert actual==m['report_date'],(key,actual,m['report_date'])
   m['report_date_reliability']='printed_date_verified_physical_page_1'
  m['notes']='Original public broker PDF; original publication instant unverified. Model date follows the printed current-model report date where no earlier model date is established. No share-basis conversion applied; original KRW per-share units retained. Basic/diluted, treasury-share and preferred-share allocation rules remain unresolved.'
  if key not in REVIEWED:
   m.update(status='retained_supporting_source_no_new_annual_eps',notes=EXCLUDED.get(key,'No observations emitted.'),company_ids='sk_hynix' if 'hynix' in key else 'sk_hynix;samsung_electronics');man.append(m);continue
  assert ('Young-gun Kim' if mirae else '김선우') in text,key
  m['company_ids']=';'.join(c for _,c,_,_ in REVIEWED[key]);m['status']='downloaded_text_extracted'
  if key=='meritz_sector_20231108':m['notes']+=' Samsung p6 exactly repeats the already-retained Nov1 2023 EPS and revenue vector, so only the distinct Hynix model is extracted.'
  if key=='meritz_sector_20251114':m['notes']+=' Hynix p6 exactly repeats the Nov11 detailed model, so only the distinct Samsung model is extracted.'
  if key=='meritz_hynix_20251111':m['notes']+=' Detailed parent-attributable annual EPS on physical p6 is used. The p4 valuation/peer panel prints FY2026 EPS 78176, which conflicts with detailed EPS 78132; no substitution or averaging.'
  if key=='meritz_hynix_20220428':m['notes']+=' Earlier original has the same FY22/23 EPS as the already-retained May31 2022 sector model; April28 is the earlier proven model vintage.'
  if mirae:m['notes']+=' First-page footnote: consolidated K-IFRS; NP attributable to owners of parent. June9 explicitly changes earnings forecasts. The footnote does not define the EPS denominator.'
  for page,company,year,expected_eps in REVIEWED[key]:
   pg=pages[page-1];assert 'EPS' in pg,(key,page)
   if not mirae:assert '(지배주주)' in pg,(key,page)
   if key.startswith('meritz_sector'):assert 'Analyst 김선우' in pg,(key,page)
   if key=='meritz_hynix_20251111':
    epsline=next(l for l in pg.splitlines() if 'EPS(지배주주)' in l)
    revline=next(l for l in pg.splitlines() if l.startswith('매출액 '))
    eps_values=nums(epsline.split('EPS(지배주주)',1)[1])[-3:]
    rev_values=nums(revline)[2:5]
   elif mirae:
    epsline=next(l for l in pg.splitlines() if 'EPS (W)' in l)
    revline=next(l for l in pg.splitlines() if 'Revenue (Wbn)' in l)
    eps_values=nums(epsline)[-3:];rev_values=nums(revline)[-3:]
   for offset,(y,expected) in enumerate(zip(range(year,year+len(expected_eps)),expected_eps)):
    if key=='meritz_hynix_20251111' or mirae:
     eps=eps_values[offset];revenue=rev_values[offset];raw_eps=epsline;raw_revenue=revline
    else:
     line=next(l for l in pg.splitlines() if re.search(rf'\b{y}E\s+[-\d]',l) and len(nums(re.split(rf'\b{y}E\s+',l,1)[1]))>=8)
     values=nums(re.split(rf'\b{y}E\s+',line,1)[1]);eps=values[3];revenue=values[0];raw_eps=raw_revenue=line
    assert eps.replace(',','')==expected,(key,y,eps,expected)
    for metric,value,unit,basis,raw in [('eps',eps,'KRW per share',MIRAE_BASIS if mirae else MERITZ_BASIS,raw_eps),('revenue',revenue,'KRW trillion' if company=='samsung_electronics' else 'KRW billion','Consolidated total revenue as printed',raw_revenue)]:
     out={k:'' for k in FIELDS};out.update({k:m[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']})
     number=Decimal(value.replace(',',''))*(Decimal(1) if metric=='eps' else Decimal(10)**(12 if company=='samsung_electronics' else 9))
     out.update(company_id=company,ticker='005930.KS' if company=='samsung_electronics' else '000660.KS',source_type='individual_analyst_forecast',model_date=m['report_date'],share_basis_date=m['report_date'],target_period=f'FY{y}',target_period_end=f'{y}-12-31',metric=metric,currency='KRW',value=format(number,'f'),original_value=value,original_unit=unit,basis=basis,pdf_page=page,extraction_status='parsed_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=raw.strip(),notes=m['notes']);obs.append(out)
   checks.append(dict(report_id=key,company_id=company,pdf_page=page,fiscal_years=list(range(year,year+len(expected_eps))),exact_eps_vector=expected_eps,source_hash_verified=True,parent_attributable_eps_label_verified=not mirae))
  man.append(m)
 write(BASE/'manifest.csv',MAN,man);write(BASE/'observations.csv',FIELDS,obs)
 summary=dict(retained_originals=sum(bool(m['sha256']) for m in man),model_reports=sum(m['status']=='downloaded_text_extracted' for m in man),eps_observations=sum(o['metric']=='eps' for o in obs),total_observations=len(obs),physical_pages=sum(int(m['page_count'] or 0) for m in man),eps_by_company=dict(collections.Counter(o['company_id'] for o in obs if o['metric']=='eps')),cross_broker_compatibility_groups_proven=0,original_publication_instants_verified=0)
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 (BASE/'validation.json').write_text(json.dumps(dict(checks=checks,summary=summary),indent=2)+'\n')
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
