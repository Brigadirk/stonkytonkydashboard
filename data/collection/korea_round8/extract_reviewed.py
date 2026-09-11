"""Offline extraction of reviewed Meritz annual EPS summaries. No consensus or implied EPS."""
from pathlib import Path
from decimal import Decimal
import csv,json,hashlib,re,subprocess,collections
BASE=Path(__file__).resolve().parent
FIELDS=['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
MAN=['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window','document_kind']
BASIS='EPS labelled parent-attributable; basic/diluted and share denominator not established'
# report key -> physical summary page, company, first annual forecast, exact printed EPS vector.
REVIEWED={
'meritz_sector_20250912':[(71,'sk_hynix',2025,['45551','63309','60752']),(75,'samsung_electronics',2025,['4430','6105','7166'])],
'meritz_sector_20260727':[(66,'samsung_electronics',2026,['44657','64649','76525']),(72,'sk_hynix',2026,['354962','497883','576371'])],
'meritz_hynix_20210728':[(1,'sk_hynix',2021,['12371','20529','23447'])],
'meritz_sector_20211111':[(7,'sk_hynix',2021,['12840','10593','21138']),(12,'samsung_electronics',2021,['5828','5814','7535'])],
'meritz_sector_20240215':[(6,'sk_hynix',2024,['11133','18883'])],
'meritz_hynix_20240422':[(1,'sk_hynix',2024,['13380','21539','24499'])],
'meritz_hynix_20240426':[(1,'sk_hynix',2024,['14335','22243','25603'])],
'meritz_sector_20240612':[(11,'samsung_electronics',2024,['4492','5967','6156'])],
'meritz_hynix_20250123':[(1,'sk_hynix',2025,['37123.6','43405.9'])],
'meritz_samsung_20250131':[(1,'samsung_electronics',2025,['4252','5837'])],
'meritz_hynix_20250724':[(1,'sk_hynix',2025,['44187.6','56661.7','51434.2'])],
'meritz_samsung_20250731':[(1,'samsung_electronics',2025,['4100','5864','6726'])],
'meritz_hynix_20251029':[(1,'sk_hynix',2025,['52329','75984','71751'])],
'meritz_samsung_20251030':[(1,'samsung_electronics',2025,['4978','7103','7467'])],
'meritz_samsung_20260403':[(1,'samsung_electronics',2026,['37419','52719','59006'])],
'meritz_hynix_20260423':[(1,'sk_hynix',2026,['297777','452505','528426'])],
'meritz_samsung_20260430':[(8,'samsung_electronics',2026,['41668','60970','68166'])],
'meritz_samsung_20260706':[(7,'samsung_electronics',2026,['45181','66179','78330'])],
'meritz_hynix_20260729':[(5,'sk_hynix',2026,['360873','501841','581191'])],
'meritz_samsung_20260730':[(8,'samsung_electronics',2026,['44700','64634','76477'])],
}
EXCLUDED={'meritz_strategy_20260907':'Soowook Hwang investment-strategy note on Astra and AI demand, not Sunwoo Kim company earnings model. No annual EPS forecast table.','meritz_hynix_20260325':'ADR/capital-return issue comment, no annual EPS table.', 'meritz_hynix_20260506':'GDR/ADR issue comment, no annual EPS table.', 'meritz_hynix_20260819':'Capital-return announcement comment, no annual EPS table.', 'meritz_sector_20250526':'Retained Computex excerpt repeats the existing April25 2025 SK hynix EPS vector 43086.3/45491.2/39174.1; not introduced as a fresh model.'}
def write(path,fields,rows):
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 logs=json.loads((BASE/'download_log.json').read_text())+json.loads((BASE/'download_log_direct.json').read_text());obs=[];man=[];checks=[]
 for log in logs:
  key=log['key'];m={k:'' for k in MAN};m.update({k:log.get(k,'') for k in ['source_url','local_file','text_file','sha256','retrieved_at','discovery_url','page_count']});m.update(report_id=key,firm='meritz',analyst_name='Sunwoo Kim',collection_window='same_author_history_and_fresh_models_2021_2026',document_kind='broker_research_report')
  if not log.get('sha256'):m.update(status='public_retrieval_failed',notes=log.get('error',''));man.append(m);continue
  assert hashlib.sha256((BASE/log['local_file']).read_bytes()).hexdigest()==log['sha256'],key
  text=(BASE/log['text_file']).read_text();pages=text.split('\f');date=re.search(r'(202\d)\.\s*(\d{1,2})\.\s*(\d{1,2})',text)
  m['report_date']='-'.join([date[1],date[2].zfill(2),date[3].zfill(2)]) if date else ''
  if key in ['meritz_sector_20250912','meritz_sector_20260727']:
   m['report_date']='2025-09-12' if key.endswith('20250912') else '2026-07-27';m['report_date_reliability']='printed_date_visually_verified_physical_page_1_image_cover'
  elif key=='meritz_sector_20250526':m['report_date']='2025-05-26';m['report_date_reliability']='channel_date_and_filename_supporting_source_only'
  else:m['report_date_reliability']='printed_date_verified_physical_page_2' if key.startswith('meritz_sector') else 'printed_date_verified_physical_page_1'
  if key=='meritz_strategy_20260907':m['analyst_name']='Soowook Hwang'
  m['notes']='Original public broker PDF. Original availability timestamp unverified. Model date follows printed report date; no earlier distinct current-model date is printed. EPS is explicitly parent-attributable; basic/diluted, treasury-share and preferred-share allocation rules remain unresolved.'
  if key not in REVIEWED:
   m['status']='retained_supporting_source_no_new_annual_eps';m['notes']=EXCLUDED.get(key,'Pending review; no observations emitted.');m['company_ids']='sk_hynix' if 'hynix' in key else 'sk_hynix;samsung_electronics';man.append(m);continue
  assert '김선우' in text,key
  expected_date=key[-8:];expected_date=f'{expected_date[:4]}-{expected_date[4:6]}-{expected_date[6:]}'
  assert m['report_date']==expected_date,(key,m['report_date'],expected_date)
  m['company_ids']=';'.join(c for _,c,_,_ in REVIEWED[key]);m['status']='downloaded_text_extracted'
  if key=='meritz_sector_20240612':m['notes']+=' SK hynix p6 exactly repeats June10 model; only the distinct Samsung model is extracted.'
  for page,company,year,eps in REVIEWED[key]:
   pg=pages[page-1];assert 'EPS' in pg and '(지배주주)' in pg,(key,page)
   if key.startswith('meritz_sector'):
    author_page={( 'meritz_sector_20260727',66):63,('meritz_sector_20260727',72):68}.get((key,page),page)
    assert 'Analyst 김선우' in pages[author_page-1],(key,page)
    if author_page!=page:m['notes']+=f' This company section is individually bylined to Sunwoo Kim on physical page {author_page}; the annual summary follows on physical page {page}.'
   for y,expected in zip(range(year,year+len(eps)),eps):
    line=next(l for l in pg.splitlines() if re.search(rf'\b{y}E\s+[-\d]',l));tail=re.split(rf'\b{y}E\s+',line,1)[1];values=re.findall(r'-?\d[\d,]*(?:\.\d+)?',tail)
    assert values[3].replace(',','')==expected,(key,y,values,expected)
    for metric,value,unit,basis in [('eps',values[3],'KRW per share',BASIS),('revenue',values[0],'KRW trillion' if company=='samsung_electronics' else 'KRW billion','Consolidated total revenue as printed')]:
     out={k:'' for k in FIELDS};out.update({k:m[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']})
     number=Decimal(value.replace(',',''))*(Decimal(1) if metric=='eps' else Decimal(10)**(12 if company=='samsung_electronics' else 9))
     out.update(company_id=company,ticker='005930.KS' if company=='samsung_electronics' else '000660.KS',source_type='individual_analyst_forecast',target_period=f'FY{y}',target_period_end=f'{y}-12-31',metric=metric,currency='KRW',value=format(number,'f'),original_value=value,original_unit=unit,basis=basis,pdf_page=page,extraction_status='parsed_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=line.strip(),notes=m['notes']);obs.append(out)
   checks.append({'report_id':key,'company_id':company,'pdf_page':page,'fiscal_years':list(range(year,year+len(eps))),'exact_eps_vector':eps,'source_hash_verified':True,'parent_attributable_label_verified':True})
  man.append(m)
 write(BASE/'manifest.csv',MAN,man);write(BASE/'observations.csv',FIELDS,obs)
 summary={'retained_originals':sum(bool(m['sha256']) for m in man),'model_reports':sum(m['status']=='downloaded_text_extracted' for m in man),'eps_observations':sum(o['metric']=='eps' for o in obs),'total_observations':len(obs),'physical_pages':sum(int(m['page_count'] or 0) for m in man),'eps_by_company':dict(collections.Counter(o['company_id'] for o in obs if o['metric']=='eps')),'cross_broker_compatibility_groups_proven':0,'original_availability_verified':False}
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(BASE/'validation.json').write_text(json.dumps({'checks':checks,'summary':summary},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
