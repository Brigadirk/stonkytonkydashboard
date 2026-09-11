from pathlib import Path
import requests,concurrent.futures,csv,hashlib,subprocess
B=Path(__file__).parent
ids={'broadcom':'0P0000KU35','alphabet':'0P000002HD','nvidia':'0P000003RE','micron':'0P000003MC'}
targets=[(c,d) for c in ids for d in ['20250205','20250403','20250507']]
def work(t):
 c,d=t;url=f'https://invest.firstrade.com/ms/equity_reports/sr/2025/{ids[c]}_{d}_RT.pdf';m=dict(company_id=c,filename_date=d,source_url=url,status='',source_file='',source_sha256='')
 try:
  r=requests.get(url,timeout=20)
  if r.status_code==200 and r.content.startswith(b'%PDF-'):
   p=B/f'{c}_{d}.pdf';p.write_bytes(r.content);subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True,stderr=subprocess.DEVNULL)
   m.update(status='downloaded_original_pdf',source_file=str(p),source_sha256=hashlib.sha256(r.content).hexdigest())
  else:m['status']=f'http_{r.status_code}'
 except Exception as e:m['status']=type(e).__name__
 return m
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rs=list(ex.map(work,targets))
with (B/'attempts.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
for r in rs:print(r['company_id'],r['filename_date'],r['status'])
