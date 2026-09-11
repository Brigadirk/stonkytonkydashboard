"""Fetch bounded public dated BESI/Firstrade originals; preserve attempts and hashes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,re,subprocess,requests,sys
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent

def fetch(d):
 url=f'https://invest.firstrade.com/ms/equity_reports/sr/{d[:4]}/0P0000A65M_{d}_RT.pdf'
 row={'source_url':url,'date_hint':d,'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  r=requests.get(url,timeout=25);row['http_status']=r.status_code
  if r.status_code==200 and r.content.startswith(b'%PDF'):
   p=BASE/'originals'/f'besi_{d}.pdf';p.write_bytes(r.content)
   t=BASE/'text'/f'besi_{d}.txt';subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
   content=t.read_text()
   row.update(local_file=str(p.relative_to(ROOT)),text_file=str(t.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content),models=re.findall(r'(?:Summary as of|Financials as of) +([0-9A-Za-z ]+)',content),report=(re.search(r'Report as of ([^|]+)',content).group(1).strip() if 'Report as of' in content else ''))
  else:row['error']='No original PDF at this dated public URL'
 except Exception as exc:row['error']=str(exc)
 return row
if __name__=='__main__':
 path=BASE/'download_log.json';rows=json.loads(path.read_text()) if path.exists() else []
 seen={r['date_hint'] for r in rows};dates=[d for d in sys.argv[1:] if d not in seen]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for row in pool.map(fetch,dates):
   rows.append(row);path.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
