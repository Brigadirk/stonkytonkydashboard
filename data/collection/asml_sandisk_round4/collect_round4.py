import requests, csv, hashlib, subprocess
from datetime import datetime, timezone
from pathlib import Path
BASE=Path('data/collection/asml_sandisk_round4')
URLS={
'hana_asml_20240718':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2024/07/18/ASML_240718.pdf',
'hana_asml_20241017':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2024/10/17/ASML_241017.pdf',
'hana_asml_20211001':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2021/09/30/Global_ASML_2021.09.30.pdf',
'hana_asml_20251017':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2025/10/16/ASML_251017.pdf',
'hana_asml_20260416':'https://file.hanaw.com/download/research/FileServer/WEB/global/company/2026/04/16/ASML_260416.pdf',
'hana_global_20260109':'https://www.hanaw.com/download/research/FileServer/WEB/global/industry/2026/01/09/2026guide.pdf',
'hana_asml_20210722':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2021/07/21/Global_ASML_2021.07.22.pdf',
'hana_daily_20241018':'https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2024/10/17/Daily_241018.pdf',
'hana_asml_20220120':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2022/01/19/Global_ASML_Hana.pdf',
'hana_asml_20230425':'https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2206&bbsId=&bbsSeq=1274459&dbType=',
'hana_global_20240111':'https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2024/01/11/2024Global_100.pdf',
'mirae_daily_20220121':'https://securities.miraeasset.com/public/mw/blog/20220121080513/20220121_Daily.pdf',
'cantor_asml_202301':'https://cantorfitzgerald.ie/wp-content/uploads/2023/12/ASML-Research-Note-Jan-23-1.pdf',
'zacks_sandisk_retrieved':'https://advisortools.zacks.com/Research/Stocks/SNDK/Overview/PDF/2015-11-27/2025-12-02',
'oneil_asml_20240902':'https://ebooks.williamoneil.com/pdfs/charts/comments/20240902/ASML.NL.pdf',
'hana_asml_20260129':'https://www.hanaw.com/download/research/FileServer/WEB/global/company/2026/01/29/ASML_260129.pdf',
}
for day in ['20250815','20251106','20251107','20260130','20260430','20260819']:
 URLS[f'morningstar_sandisk_{day}']=f'https://invest.firstrade.com/ms/equity_reports/sr/{day[:4]}/0P0001U8JM_{day}_RT.pdf'
previous={}
if (BASE/'downloaded_sources.csv').exists():
 with (BASE/'downloaded_sources.csv').open() as f: previous={r['key']:r for r in csv.DictReader(f)}
rows=[]
for key,url in URLS.items():
 p=BASE/'pdfs'/f'{key}.pdf'; t=BASE/'text'/f'{key}.txt'
 try:
  if p.exists(): body=p.read_bytes();status='cached'
  else:
   r=requests.get(url,timeout=30); r.raise_for_status();body=r.content;status=str(r.status_code)
   if not body.startswith(b'%PDF'): raise ValueError(f'Non PDF: {body[:50]!r}')
   p.write_bytes(body)
  subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
  # Retain the first observed retrieval time when registering existing bytes.
  retrieved=previous.get(key,{}).get('retrieved_at') or datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()
  rows.append(dict(key=key,source_url=url,local_file=str(p),text_file=str(t),sha256=hashlib.sha256(body).hexdigest(),retrieved_at=retrieved,http_status=previous.get(key,{}).get('http_status') or status))
  print(key,status,len(body),flush=True)
 except Exception as e: print(key,type(e).__name__,str(e)[:200],flush=True)
with (BASE/'downloaded_sources.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
