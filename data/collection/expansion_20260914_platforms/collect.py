from pathlib import Path
import requests, hashlib,json,subprocess
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
BASE=Path(__file__).resolve().parent
IDS={'MSFT':'0P000003MH','AMZN':'0P000000B7','META':'0P0000W3KZ','PLTR':'0P0001KOSE','TSM':'0P000005AR'}
DATES={'MSFT':['20260911','20260729','20260730','20260429','20260128','20251029','20250730'], 'AMZN':['20260911','20260730','20260731','20260429','20260205','20251030','20250731'], 'META':['20260911','20260826','20260729','20260730','20260429','20260128','20251029','20250730'], 'PLTR':['20260911','20260803','20260804','20260504','20260202','20251103','20250804'], 'TSM':['20260911','20260716','20260416','20260115','20251016','20250717']}
def fetch(job):
    t,d=job;u=f'https://invest.firstrade.com/ms/equity_reports/sr/{d[:4]}/{IDS[t]}_{d}_RT.pdf'
    row=dict(ticker=t,url_date=d,source_url=u,retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(u,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0 (personal research archive)'})
        row.update(http_status=r.status_code,size=len(r.content))
        if r.status_code==200 and r.content.startswith(b'%PDF-'):
            sha=hashlib.sha256(r.content).hexdigest();p=BASE/f'{t}_{d}_{sha[:12]}.pdf';p.write_bytes(r.content)
            tx=p.with_suffix('.txt');subprocess.run(['pdftotext','-layout',str(p),str(tx)],check=True)
            row.update(status='retained',sha256=sha,local_file=str(p),text_file=str(tx))
        else: row.update(status='unavailable')
    except Exception as e:row.update(status='failed',error=str(e))
    return row
if __name__=='__main__':
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as p:
        for row in p.map(fetch,[(t,d) for t,ds in DATES.items() for d in ds]):
            rows.append(row);print(row['ticker'],row['url_date'],row['status'],flush=True)
    (BASE/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
