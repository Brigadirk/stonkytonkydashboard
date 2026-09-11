"""Bounded checks of publisher originals hosted by its public distributor."""
from pathlib import Path
from datetime import datetime,timezone
import concurrent.futures,requests,hashlib,json,subprocess
B=Path(__file__).parent
DATES='20210304 20210305 20210308 20210607 20210608 20210610 20210615 20210907 20210908 20210910 20210915 20211210 20211213 20211214 20220113 20220304 20220307 20220309 20220526 20220527 20220606 20220607 20220902 20220906 20220907 20221209 20221212 20230605 20230706 20230707 20230901 20231122 20231124 20240516 20240517 20240614 20240618 20240712 20240715 20241216 20250130 20250206 20250207 20250303 20250305 20240531 20240603 20240604 20240624 20240625 20240716 20240321 20240322 20211206 20211207 20220224 20220225 20220310 20221103 20221104 20221215 20221216 20230126 20230127 20230403 20230608 20230609 20230710 20231127 20231128 20231130 20250127 20250128'.split()
logpath=B/'download_log.json';old=json.loads(logpath.read_text()) if logpath.exists() else [];seen={m['filename_date'] for m in old}
def get(d):
 u=f'https://invest.firstrade.com/ms/equity_reports/sr/{d[:4]}/0P0000KU35_{d}_RT.pdf';m=dict(filename_date=d,source_url=u,status='',retrieved_at=datetime.now(timezone.utc).isoformat())
 try:
  r=requests.get(u,timeout=18);m['http_status']=r.status_code
  if r.status_code==200 and r.content.startswith(b'%PDF-'):
   p=B/'pdfs'/f'morningstar_AVGO_{d}.pdf';p.write_bytes(r.content);q=B/'text'/f'{p.stem}.txt';subprocess.run(['pdftotext','-layout',str(p),str(q)],check=True,stderr=subprocess.DEVNULL)
   m.update(status='downloaded_original_pdf',local_file=str(p),text_file=str(q),sha256=hashlib.sha256(r.content).hexdigest())
  else:m['status']=f'http_{r.status_code}'
 except Exception as e:m.update(status=type(e).__name__,error=str(e)[:180])
 return m
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for m in ex.map(get,[d for d in DATES if d not in seen]):old.append(m);logpath.write_text(json.dumps(old,indent=2)+'\n');print(m['filename_date'],m['status'],flush=True)
print('Total',len(old),'PDFs',sum(m['status']=='downloaded_original_pdf' for m in old))
