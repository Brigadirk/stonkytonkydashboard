"""Extract reviewed annual EPS rows; preserve physical-page and byline provenance."""
from pathlib import Path
import csv,re,hashlib
BASE=Path(__file__).parent
manifest=list(csv.DictReader((BASE/'manifest.csv').open()))
# report filename suffix: date, date physical page, printed date evidence, company pages and explicit EPS values
review={
'1f05f6c6dbfd':('2022-07-29',1,'2022. 7. 29',{'samsung_electronics':(1,{2022:'6,143',2023:'6,131',2024:'7,867'})}),
'4916792f14db':('2024-01-02',1,'2024. 1. 2',{'samsung_electronics':(1,{2023:'1,765',2024:'4,634',2025:'5,627'})}),
'ed658c9c8fb4':('2024-05-02',1,'2024년 05월 02일',{'samsung_electronics':(1,{2024:'4,680',2025:'6,428'})}),
'ddfa515d543d':('2024-06-10',11,'2024.06.10',{'sk_hynix':(6,{2024:'18,140.7',2025:'28,287.9',2026:'32,771.3'})}),
'1fe52d2c3bed':('2025-04-25',1,'2025. 4. 25',{'sk_hynix':(1,{2025:'43,086.3',2026:'45,491.2',2027:'39,174.1'})}),
'30846fca2a70':('2024-10-24',1,'2024. 10. 24',{'sk_hynix':(1,{2024:'23,100.6',2025:'40,037.9',2026:'42,139.9'})}),
'cfc735a588f6':('2024-07-26',1,'2024. 7. 26',{'sk_hynix':(1,{2024:'21,382.2',2025:'37,810.7',2026:'42,075.0'})}),
'1f47bf801dca':('2023-10-26',1,'2023. 10. 26',{'sk_hynix':(1,{2023:'-10,838',2024:'10,096',2025:'16,414'})}),
'92e4ee56f064':('2022-05-31',3,'2022. 5. 31',{'samsung_electronics':(66,{2022:'7,215',2023:'8,512'}),'sk_hynix':(70,{2022:'16,603',2023:'21,878'})}),
'a193c6a47325':('2023-05-30',2,'2023. 5. 30',{'samsung_electronics':(6,{2023:'1,267',2024:'4,606',2025:'6,282'}),'sk_hynix':(10,{2023:'-12,655',2024:'3,064',2025:'9,720'})}),
'c37de50c0800':('2024-01-02',1,'2024. 1. 2',{'sk_hynix':(1,{2023:'-11,099',2024:'10,056',2025:'19,317'})}),
'fd1fa953f941':('2023-07-27',1,'2023. 7. 27',{'sk_hynix':(1,{2023:'-11,111',2024:'7,888',2025:'14,239'})}),
}
fields=list(next(csv.reader((BASE.parent/'korean_memory'/'observations.csv').open())))
observations=[]
for m in manifest:
 suffix=m['report_id'].split('_')[1];date,datepage,dateproof,companies=review[suffix]
 hana='hanaw.com' in m['source_url']
 if hana:
  old=m['report_id'];new='hana_'+suffix
  for key,folder,ext in [('local_file','pdfs','pdf'),('text_file','text','txt'),('layout_text_file','layout_text','txt')]:
   dest=f'{folder}/{new}.{ext}'
   if m[key]!=dest:

    if (BASE/m[key]).exists(): (BASE/m[key]).rename(BASE/dest)
    assert (BASE/dest).exists()
    m[key]=dest
  m.update(report_id=new,firm='hana',analyst_name='Rok-ho Kim; Hyun-soo Kim',candidate_name='Rok-ho Kim; Hyun-soo Kim')
 pages=(BASE/m['layout_text_file']).read_text().split('\f')
 assert hashlib.sha256((BASE/m['local_file']).read_bytes()).hexdigest()==m['sha256']
 assert dateproof in pages[datepage-1]
 m.update(company_ids=';'.join(companies),report_date=date,report_date_reliability=f'printed_date_manually_verified_pdf_page_{datepage}',notes=f'Printed date evidence on physical page {datepage}; original historical availability unverified. '+('Original Hana report; jointly signed analysts retained as a team, not assigned to one individual.' if hana else 'Original Meritz report. Company section explicitly attributed to Sunwoo Kim (김선우).'))
 if suffix=='ddfa515d543d':m['notes']+=' Broker-hosted 11-page excerpt; full-report printed page 64 is physical page 6. Report date from latest own disclosure-history entry; PDF emits stream/font warnings but selected table extracts and renders.'
 if 'pstatic.net' in m['source_url'] or 'paxnet.co.kr' in m['source_url']:m['notes']+=' Broker-authored original PDF hosted by a distributor; broker-hosted copy not retrieved.'
 for company,(page,values) in companies.items():
  txt=pages[page-1]
  if not hana:assert '김선우' in txt
  for year,value in values.items():
   if hana:
    row=next(l.strip() for l in txt.splitlines() if l.strip().startswith('EPS '))
    assert re.findall(r'[0-9]+,[0-9]+',row)[:4]==['8,057','2,131','4,680','6,428'],repr(row)
   else:
    row=next(l.strip() for l in txt.splitlines() if re.search(rf'\b{year}E\s+[-\d,.]+\s+[-\d,.]+\s+[-\d,.]+\s',l))
    nums=re.split(r'\s+',re.search(rf'\b{year}E\s+(.+)',row).group(1))
    assert nums[3]==value,(m['report_id'],company,year,nums)
   observations.append(dict(report_id=m['report_id'],company_id=company,ticker='005930.KS' if company=='samsung_electronics' else '000660.KS',firm=m['firm'],analyst_name=m['analyst_name'],source_type='joint_team_forecast' if hana else 'individual_analyst_forecast',report_date=date,report_date_reliability=m['report_date_reliability'],target_period=f'FY{year}',target_period_end=f'{year}-12-31',metric='eps',currency='KRW',value=value.replace(',',''),original_value=value,original_unit='KRW per share',basis='Hana Financial Data forecast table; EPS definition not normalized' if hana else 'EPS labelled parent-attributable; basic/diluted and share denominator not established',pdf_page=page,source_url=m['source_url'],local_file=m['local_file'],text_file=m['text_file'],sha256=m['sha256'],retrieved_at=m['retrieved_at'],extraction_status='attribution_review_joint_model_unscored' if hana else 'parsed_explicit_forecast_table_unscored',time_relation='past_fiscal_year_estimate_before_final_earnings' if year<int(date[:4]) else 'current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=row,notes='Only explicit annual forecast E/F columns extracted; historical actuals omitted. '+('Two analyst bylines; RA not treated as lead analyst.' if hana else 'Printed parent-attributable EPS retained without statutory/basic/diluted normalization.')))
with (BASE/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=manifest[0].keys());w.writeheader();w.writerows(manifest)
with (BASE/'observations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(observations)
print(f'{len(manifest)} reports, {sum(int(m["page_count"]) for m in manifest)} physical pages, {len(observations)} EPS observations')
