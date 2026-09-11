"""Reproduce visually reviewed native KRW EPS/revenue; never infer or smooth forecasts."""
from pathlib import Path
from decimal import Decimal
import csv,json,re,hashlib,collections
B=Path(__file__).resolve().parent
FIELDS=['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','model_date','share_basis_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
MAN=['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window','document_kind']
BASIS='EPS labelled parent-attributable; basic/diluted and share denominator not established'
REVIEWED={
'meritz_sector_20210601':[(7,'samsung_electronics',2021,['5490','6624','8094']),(11,'sk_hynix',2021,['15312','24156','27996'])],
'meritz_samsung_20210729':[(1,'samsung_electronics',2021,['5759','6837','7684'])],
'meritz_samsung_20211029':[(1,'samsung_electronics',2021,['5828','5814','7535'])],
'meritz_samsung_20221028':[(1,'samsung_electronics',2022,['5644','4273','5260'])],
'meritz_hynix_20230201':[(1,'sk_hynix',2023,['-7788','9198'])],
'meritz_hynix_20230427':[(1,'sk_hynix',2023,['-12701','2613','11270'])],
'meritz_sector_20240115':[(7,'sk_hynix',2023,['-10653','9885','18607']),(11,'samsung_electronics',2024,['4288','5361'])],
'meritz_samsung_20240502':[(1,'samsung_electronics',2024,['4398','5716','5817'])],
'meritz_samsung_20241101':[(1,'samsung_electronics',2024,['4604','6326','6682'])],
}
EXCLUDED={
'meritz_samsung_20241118':'Share-buyback issue comment; no annual EPS forecast table.',
'meritz_samsung_20250108':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_samsung_20250408':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_samsung_20250708':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_samsung_20251014':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_samsung_20260407':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_samsung_20260707':'Preliminary-quarter comment; no annual EPS forecast table.',
'meritz_sector_20260818':'Industry supply issue comment; no annual EPS forecast table.',
'meritz_sector_20260112':'Public CES excerpt contains Hyundai/Gaon earnings tables, no SK hynix or Samsung annual EPS model.',
'meritz_sector_20260401':'Public SEMICON excerpt contains equipment/company models and third-party industry statistics, no SK hynix or Samsung annual EPS model.',
}
def write(path,fields,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 logs=json.loads((B/'download_log.json').read_text());obs=[];man=[];checks=[]
 for log in logs:
  key=log['report_id'];m={k:'' for k in MAN};m.update({k:log.get(k,'') for k in MAN});m.update(firm='meritz',analyst_name='Sunwoo Kim',collection_window='memory_same_author_intervening_models_2021_2026',document_kind='broker_research_report')
  stamp=key[-8:];m['report_date']=f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}'
  m['company_ids']='samsung_electronics' if 'samsung' in key else 'sk_hynix' if 'hynix' in key else 'sk_hynix;samsung_electronics'
  if not log.get('sha256'):m.update(status='public_retrieval_failed',notes=log.get('error',''));man.append(m);continue
  assert hashlib.sha256((B/log['local_file']).read_bytes()).hexdigest()==log['sha256'],key
  pages=(B/log['text_file']).read_text().split('\f')
  m['notes']='Original public Meritz PDF. Printed current-model date retained; original publication instant unverified. No share conversion. EPS parent-attributable label retained; basic/diluted and share denominator unresolved. The channel only located the PDF and is not proof of historical availability.'
  if key not in REVIEWED:
   m.update(status='retained_supporting_source_no_new_annual_eps',notes=EXCLUDED[key]);man.append(m);continue
  m['report_date_reliability']='printed_date_visually_verified_physical_page_1'
  if key=='meritz_sector_20210601':
   m['report_date_reliability']='printed_date_verified_physical_page_2'
   assert 'Meritz Research 2021. 6. 1' in pages[1]
  elif key=='meritz_sector_20240115':
   m['report_date_reliability']='printed_date_visually_verified_physical_page_1_image_cover'
   assert (B/'review'/f'{key}_p1.png').exists()
  else:
   match=re.search(r'(202\d)\.\s*(\d{1,2})\.\s*(\d{1,2})',pages[0]);assert match,key
   assert m['report_date']==f'{match[1]}-{match[2].zfill(2)}-{match[3].zfill(2)}',key
  m['status']='downloaded_text_extracted'
  if key=='meritz_samsung_20211029':m['notes']+=' Complete FY21-23 EPS and revenue vector repeats in November 11 2021 sector original; October29 is earlier proven model date. Separate recommendation packet preserves the later source without refreshing its model age.'
  if key=='meritz_sector_20240115':m['notes']+=' FY2023P Samsung provisional outcome excluded; only explicitly E-marked forward years admitted. Physical PDF pages differ from printed slide numbers.'
  for page,company,year,expected in REVIEWED[key]:
   pg=pages[page-1];assert 'EPS' in pg and '(지배주주)' in pg and '김선우' in pg,(key,page)
   assert (B/'review'/f'{key}_p{page}.png').exists(),key
   for y,eps in zip(range(year,year+len(expected)),expected):
    line=next(l for l in pg.splitlines() if re.search(rf'\b{y}E\s+[-\d]',l));values=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.split(rf'\b{y}E\s+',line,1)[1]);assert values[3].replace(',','')==eps,(key,y,values,eps)
    for metric,value,unit,basis in [('eps',values[3],'KRW per share',BASIS),('revenue',values[0],'KRW trillion' if company=='samsung_electronics' else 'KRW billion','Consolidated total revenue as printed')]:
     r={k:'' for k in FIELDS};r.update({k:m[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']})
     number=Decimal(value.replace(',',''))*(1 if metric=='eps' else Decimal(10)**(12 if company=='samsung_electronics' else 9))
     r.update(company_id=company,ticker='005930.KS' if company=='samsung_electronics' else '000660.KS',source_type='individual_analyst_forecast',model_date=m['report_date'],share_basis_date=m['report_date'],target_period=f'FY{y}',target_period_end=f'{y}-12-31',metric=metric,currency='KRW',value=format(number,'f'),original_value=value,original_unit=unit,basis=basis,pdf_page=page,extraction_status='manually_verified_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=line.strip(),notes=m['notes'])
     if r['target_period_end'] < r['report_date']:
      r.update(extraction_status='quarantined_completed_fiscal_period',time_relation='completed_fiscal_period_before_publication',notes=r['notes']+' Retained extraction evidence only: fiscal year ended before this report was published; E-marking does not make it a forward forecast. Excluded from forecast scoring and admission.')
     obs.append(r)
   checks.append(dict(report_id=key,company_id=company,physical_page=page,fiscal_years=list(range(year,year+len(expected))),exact_eps_vector=expected,source_hash_verified=True,parent_attributable_label_verified=True,byline_verified=True,review_image=f'review/{key}_p{page}.png'))
  man.append(m)
 write(B/'manifest.csv',MAN,man);write(B/'observations.csv',FIELDS,obs)
 summary=dict(retained_originals=sum(bool(m['sha256']) for m in man),model_reports=len(REVIEWED),company_model_tables=len(checks),eps_observations=sum(o['metric']=='eps' for o in obs),total_observations=len(obs),quarantined_observations=sum('quarantin' in o['extraction_status'] for o in obs),eligible_eps_observations=sum(o['metric']=='eps' and 'quarantin' not in o['extraction_status'] for o in obs),eps_by_company=dict(collections.Counter(o['company_id'] for o in obs if o['metric']=='eps')),new_distinct_model_vintages=10,earlier_proven_reprint_vintages=1,cross_broker_compatibility_groups_proven=0,original_publication_instants_verified=0)
 (B/'validation.json').write_text(json.dumps(dict(checks=checks,summary=summary),indent=2)+'\n');(B/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
