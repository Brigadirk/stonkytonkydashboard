"""Offline extraction of reviewed January/February 2026 Korean memory models."""
from pathlib import Path
from datetime import datetime
from collections import Counter
from decimal import Decimal
import csv,hashlib,json,re,subprocess
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
MAN=['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window']
FIELDS=['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
BASIS={'meritz':'EPS labelled parent-attributable; basic/diluted and share denominator not established','kb':'Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS'}
EXPECTED={'meritz_samsung_20260130':('2026-01-29',['16501','19663']),'meritz_hynix_20260130':('2026-01-29',['166534','197095']),'kb_samsung_20260123':('2026-01-23',['18299','20650']),'kb_hynix_20260114':('2026-01-14',['133432','156841']),'kb_samsung_20260223':('2026-02-23',['20934','23283'])}
def write(p,fields,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 obs=[];man=[]
 for log in json.loads((BASE/'download_log.json').read_text()):
  key=log['key'];row=dict.fromkeys(MAN,'');row.update({k:log[k] for k in ['source_url','local_file','sha256','retrieved_at','discovery_url'] if k in log});row['report_id']=key
  company='sk_hynix' if 'hynix' in key else 'samsung_electronics';firm=key.split('_')[0]
  row.update(company_ids=company,firm=firm,analyst_name='Sunwoo Kim' if firm=='meritz' else 'Jeff Kim',collection_window='targeted_January_February_2026_gap')
  if not log.get('local_file'):
   row['source_url']=log.get('source_url') or log.get('discovery_url','')
   row['status']='public_redirect_download_failed';row['notes']=log.get('error','');man.append(row);continue
  p=BASE/row['local_file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
  tp=BASE/'text'/f'{key}.txt';text=tp.read_text();first=text.split('\f')[0];lines=first.splitlines()
  row['text_file']='text/'+tp.name;row['page_count']=re.search(r'Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(p)],text=True)).group(1)
  if firm=='meritz':
   dm=re.search(r'Meritz Research\s+(2026)\.\s*(\d+)\.\s*(\d+)',first);assert dm,key
   row['report_date']='-'.join([dm.group(1),dm.group(2).zfill(2),dm.group(3).zfill(2)]);assert 'Analyst 김선우' in first
  else:
   dm=re.search(r'(January|February) \d+, 2026',first);assert dm,key;row['report_date']=datetime.strptime(dm.group(),'%B %d, %Y').date().isoformat();assert 'Jeff Kim' in first
  row['report_date_reliability']='printed_date_manually_verified_pdf_page_1'
  row['notes']='Original dated broker PDF; first dissemination timestamp unverified. Research assistants are not assigned as model authors.'
  if key not in EXPECTED:
   assert 'EPS' not in text,key
   row['status']='retained_no_annual_eps_table';row['notes']+=' January 8 Samsung issue comment gives operating-profit discussion but no annual EPS model; excluded from band inputs.';man.append(row);continue
  assert row['report_date']==EXPECTED[key][0]
  row['status']='downloaded_text_extracted'
  if firm=='meritz':
   assert '(지배주주)' in first
   row['notes']+=' EPS is explicitly parent-attributable. Basic/diluted and preferred-share denominator are not inferred from the summary.'
   if key.endswith('20260130'):row['notes']+=' File key/discovery press coverage suggested January 30, but physical report is dated January 29; the printed date governs.'
   for y,expected in zip([2026,2027],EXPECTED[key][1]):
    line=next(l for l in lines if re.match(rf'^{y}E\s',l));vals=re.findall(r'-?\d[\d,]*(?:\.\d+)?',line.split('E',1)[1]);assert vals[3].replace(',','')==expected
    units='KRW trillion' if company=='samsung_electronics' else 'KRW billion'
    pairs=[('eps',vals[3],'KRW per share',BASIS[firm]),('revenue',vals[0],units,'Consolidated total revenue as printed')]
    for metric,value,unit,basis in pairs:
     o=dict.fromkeys(FIELDS,'');o.update({k:row[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']});o.update(company_id=company,ticker='000660.KS' if company=='sk_hynix' else '005930.KS',source_type='individual_analyst_forecast',target_period=f'FY{y}',target_period_end=f'{y}-12-31',metric=metric,currency='KRW',value=value.replace(',',''),original_value=value,original_unit=unit,basis=basis,pdf_page='1',extraction_status='parsed_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=line.strip(),notes=row['notes']);obs.append(o)
  else:
   assert 'NP to control. int.' in first
   eps_line=next(l for l in lines if l.startswith('EPS (KRW)'));eps=re.findall(r'\d[\d,]*(?:\.\d+)?',eps_line[len('EPS (KRW)'):])[:4]
   rev_line=next(l for l in lines if l.startswith('Revenue (KRWbn)'));rev=re.findall(r'\d[\d,]*(?:\.\d+)?',rev_line[len('Revenue (KRWbn)'):])[:4]
   years=re.findall(r'20\d{2}[AE]',next(l for l in lines if l.startswith('Fiscal year-end')))[:4];assert years==['2024A','2025E','2026E','2027E']
   assert [v.replace(',','') for v in eps[2:]]==EXPECTED[key][1]
   for idx,y in [(2,2026),(3,2027)]:
    for metric,value,unit,basis,line in [('eps',eps[idx],'KRW per share',BASIS[firm],eps_line),('revenue',rev[idx],'KRW billion','Consolidated total revenue as printed',rev_line)]:
     o=dict.fromkeys(FIELDS,'');o.update({k:row[k] for k in ['report_id','firm','analyst_name','report_date','report_date_reliability','source_url','local_file','text_file','sha256','retrieved_at']});o.update(company_id=company,ticker='000660.KS' if company=='sk_hynix' else '005930.KS',source_type='individual_analyst_forecast',target_period=f'FY{y}',target_period_end=f'{y}-12-31',metric=metric,currency='KRW',value=value.replace(',',''),original_value=value,original_unit=unit,basis=basis,pdf_page='1',extraction_status='parsed_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=line.strip(),notes=row['notes']+' EPS row follows net profit to controlling interests; the exact statutory diluted denominator is unresolved. Only FY2026/27 forecast columns extracted; the completed FY2025 column is excluded.');obs.append(o)
  man.append(row)
 for r in obs:
  if r['metric']=='revenue':
   factor={'KRW trillion':Decimal(10)**12,'KRW billion':Decimal(10)**9}[r['original_unit']]
   r['value']=format(Decimal(r['original_value'].replace(',',''))*factor,'f')
   r['notes']+=' Value is normalized to base KRW for the Korean collection schema; original_value and original_unit retain the printed table.'
 write(BASE/'manifest.csv',MAN,man);write(BASE/'observations.csv',FIELDS,obs)
 summary=dict(retained_pdfs=sum(bool(r['local_file']) for r in man),model_reports=sum(r['status']=='downloaded_text_extracted' for r in man),observations=len(obs),eps_observations=sum(r['metric']=='eps' for r in obs),physical_pages=sum(int(r['page_count'] or 0) for r in man),by_company=dict(Counter(r['company_id'] for r in obs)),original_availability_verified=False)
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
