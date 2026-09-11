from pathlib import Path
import requests,hashlib,subprocess,csv,datetime,time
BASE=Path(__file__).parent
urls=[
'https://home.imeritz.com/include/resource/research/WorkFlow/20220728192634069K_02.pdf',
'https://www.paxnet.co.kr/WWW/data/researchCenter/attach/20240102104338102.pdf',
'https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2024/05/01/240502_SEC.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20240609204233312K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20250425063811209K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20241024185749922K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20240725210909855K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20231026165054435K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20220530190742393K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20230529224232774K_02.pdf',
'https://home.imeritz.com/include/resource/research/WorkFlow/20240102061827993K_02.pdf',
'https://ssl.pstatic.net/imgstock/upload/research/company/1690498890846.pdf',
]
rows=[]
for url in urls:
 firm='hana' if 'hanaw.com' in url else 'meritz'
 rid=firm+'_'+hashlib.sha256(url.encode()).hexdigest()[:12]
 p=BASE/'pdfs'/f'{rid}.pdf'
 try:
  if not p.exists():
   subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30',url,'-o',str(p)],check=True);assert p.read_bytes().startswith(b'%PDF-'),p.read_bytes()[:40]
  text=BASE/'text'/f'{rid}.txt';layout=BASE/'layout_text'/f'{rid}.txt'
  subprocess.run(['pdftotext','-raw',str(p),str(text)],check=True,stderr=subprocess.DEVNULL)
  subprocess.run(['pdftotext','-layout',str(p),str(layout)],check=True,stderr=subprocess.DEVNULL)
  info=subprocess.check_output(['pdfinfo',str(p)],text=True)
  pages=next(l.split(':')[1].strip() for l in info.splitlines() if l.startswith('Pages:'))
  rows.append(dict(report_id=rid,source_url=url,local_file=f'pdfs/{rid}.pdf',text_file=f'text/{rid}.txt',layout_text_file=f'layout_text/{rid}.txt',company_ids='',firm=firm,analyst_name='Sunwoo Kim',report_date='',report_date_reliability='',retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='downloaded_text_extracted',notes='',page_count=pages,candidate_name='Sunwoo Kim',collection_window='requested_window'))
  print(rid,pages,flush=True)
 except Exception as e:print(url,type(e).__name__,str(e)[:150],flush=True)
 time.sleep(.2)
with (BASE/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
