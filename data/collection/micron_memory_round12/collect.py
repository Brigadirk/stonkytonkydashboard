#!/usr/bin/env python3
"""Bounded public distributor retrieval. URL dates are discovery hints only."""
import concurrent.futures, datetime, hashlib, json, subprocess, sys
from pathlib import Path
import requests
BASE=Path(__file__).resolve().parent
LOG=BASE/'retrieval.json'
old=json.loads(LOG.read_text()) if LOG.exists() else []
seen={r['url_date'] for r in old}
dates=[d for d in sys.argv[1:] if d not in seen]
def fetch(day):
 url=f'https://invest.firstrade.com/ms/equity_reports/sr/{day[:4]}/0P000003MC_{day}_RT.pdf'
 r={'url_date':day,'source_url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  response=requests.get(url,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0'})
  r['http_status']=response.status_code
  if response.status_code==200 and response.content.startswith(b'%PDF-'):
   path=BASE/'pdfs'/f'micron_{day}.pdf'; text=BASE/'text'/f'micron_{day}.txt'
   if path.exists() and path.read_bytes()!=response.content: raise ValueError('Existing artifact changed')
   path.write_bytes(response.content)
   subprocess.run(['pdftotext','-layout',str(path),str(text)],check=True)
   r.update(status='awaiting_review',local_file=str(path.relative_to(BASE.parents[2])),text_file=str(text.relative_to(BASE.parents[2])),sha256=hashlib.sha256(response.content).hexdigest())
  else:r['status']='no_public_pdf'
 except Exception as e:r.update(status='retrieval_error',error=str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for r in pool.map(fetch,dates):
  old.append(r);LOG.write_text(json.dumps(old,indent=2)+'\n')
  print(r['url_date'],r['status'],r.get('http_status'),flush=True)
