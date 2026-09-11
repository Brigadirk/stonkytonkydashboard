from pathlib import Path
import requests,concurrent.futures,csv,hashlib,subprocess
B=Path(__file__).parent
p=B/'attempts.csv';rs=list(csv.DictReader(p.open()))
def retry(m):
 if m['status']!='SSLError':return m
 try:
  r=requests.get(m['source_url'],timeout=20)
  if r.status_code==200 and r.content.startswith(b'%PDF-'):
   p=B/f'{m["company_id"]}_{m["filename_date"]}.pdf';p.write_bytes(r.content);subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True,stderr=subprocess.DEVNULL)
   m.update(status='downloaded_original_pdf',source_file=str(p),source_sha256=hashlib.sha256(r.content).hexdigest())
  else:m['status']=f'http_{r.status_code}'
 except Exception as e:m['status']=type(e).__name__
 return m
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rs=list(ex.map(retry,rs))
with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
for r in rs:print(r['company_id'],r['filename_date'],r['status'])
