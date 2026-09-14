import requests,re,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
b=Path(__file__).resolve().parent
(b/'raw').mkdir(parents=True,exist_ok=True)
items={
'marvell':('0P000003H5',['20260827','20260828','20260527','20260528','20260305','20260306','20251202','20251203','20250828','20250829']),
'arista':('0P0001354B',['20260804','20260805','20260505','20260506','20260507','20260212','20260213','20251104','20251105','20250805','20250806']),
'vertiv':('0P0001E1XR',['20260729','20260730','20260422','20260423','20260211','20260212','20251022','20251023','20250730','20250731']),
'nebius':('0P0000TDA0',['20260812','20260813','20260513','20260514','20260317','20260212','20251208']),
'cerebras':('0P0001TTTC',['20260811','20260812','20260813','20260814','20260817','20260818','20260819','20260820','20260821','20260824','20260825','20260826','20260827','20260828','20260911']),
'spacex':('0P0002DZNH',['20260813','20260814','20260817','20260818','20260819','20260820','20260821','20260629','20260612','20260611'])
}
jobs=[(c,i,d) for c,(i,days) in items.items() for d in days]
def get(x):
 c,i,d=x; u=f'https://invest.firstrade.com/ms/equity_reports/sr/{d[:4]}/{i}_{d}_RT.pdf'; row={'company_id':c,'source_url':u,'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  r=requests.get(u,timeout=(8,20)); row['http_status']=r.status_code
  if r.content.startswith(b'%PDF'):
   p=b/'raw'/f'{c}_{d}.pdf'; p.write_bytes(r.content); subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))]); row.update(local_file=str(p),text_file=str(p.with_suffix('.txt')),sha256=hashlib.sha256(r.content).hexdigest()); print(c,d,'retained',flush=True)
 except Exception as e:row['error']=str(e)
 return row
with ThreadPoolExecutor(max_workers=6) as p:rows=list(p.map(get,jobs))
(b/'retrieval.json').write_text(json.dumps(rows,indent=2)+'\n'); print('DONE',sum('local_file' in r for r in rows),len(rows),flush=True)
