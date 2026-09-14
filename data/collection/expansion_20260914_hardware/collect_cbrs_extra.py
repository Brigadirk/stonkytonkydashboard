from pathlib import Path
from datetime import datetime,timezone
import requests,json,hashlib,subprocess
from concurrent.futures import ThreadPoolExecutor
B=Path(__file__).resolve().parent;D=B/'cbrs_extra';D.mkdir(exist_ok=True)
jobs=[('firstrade_'+d,f'https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001TTTC_{d}_RT.pdf') for d in ['20260623','20260624','20260910']]
jobs += [('zacks_www','https://www.zacks.com/stock/quote/CBRS/detailed-earning-estimates'),('zacks_stage','https://stage.zacks.com/stock/quote/CBRS/detailed-earning-estimates')]
def get(j):
 key,url=j;row={'key':key,'source_url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  r=requests.get(url,timeout=(8,25));row['http_status']=r.status_code;body=r.content;ext='.pdf' if body.startswith(b'%PDF') else '.html';p=D/(key+ext);p.write_bytes(body);row.update(source_file=str(p.relative_to(B.parents[2])),source_sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),content_type=r.headers.get('content-type',''))
  if ext=='.pdf':subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))])
 except Exception as e:row['error']=str(e)
 return row
with ThreadPoolExecutor(max_workers=4) as p:rows=list(p.map(get,jobs))
(D/'retrieval.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
