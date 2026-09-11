"""Bounded public-original discovery, skipping URLs already attempted in collections."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
for name in ['originals', 'text', 'review']:
    (BASE/name).mkdir(exist_ok=True)

IDS = {'alphabet':'0P000002HD', 'asml':'0P0000002X', 'sandisk':'0P0001U8JM', 'apple':'0P000000GY'}
CANDIDATES = {
    'alphabet':['20250321','20250324','20250425','20250508','20250725','20250728','20250804','20250805','20250903'],
    'asml':['20250321','20250324','20250403','20250717','20250718','20250724','20250805','20251013'],
    'sandisk':['20250228','20250303','20250321','20250324','20250509','20250512','20250515','20250701','20250724','20250805','20250814'],
    'apple':['20250321','20250324','20250403','20250501','20250505'],
}
prior = set()
for folder in (ROOT/'data/collection').iterdir():
    if folder == BASE or not folder.is_dir(): continue
    for p in folder.rglob('*'):
        if p.suffix not in ['.json','.csv'] or p.stat().st_size > 20_000_000: continue
        prior.update(re.findall(r'https://invest\.firstrade\.com/ms/equity_reports/sr/\d{4}/0P\w+_\d{8}_RT\.pdf', p.read_text(errors='ignore')))

def fetch(item):
    company, day = item
    url=f'https://invest.firstrade.com/ms/equity_reports/sr/{day[:4]}/{IDS[company]}_{day}_RT.pdf'
    row={'company_id':company,'candidate_date':day,'source_url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
    if url in prior:
        row['status']='skipped_previous_attempt'; return row
    try:
        response=requests.get(url,timeout=20)
        row['http_status']=response.status_code
        if response.status_code==200 and response.content.startswith(b'%PDF'):
            p=BASE/'originals'/f'{company}_{day}.pdf';p.write_bytes(response.content)
            t=BASE/'text'/f'{company}_{day}.txt'
            subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
            row.update(status='retained_pending_review',local_file=str(p.relative_to(ROOT)),text_file=str(t.relative_to(ROOT)),sha256=hashlib.sha256(response.content).hexdigest())
        else: row['status']='no_original_pdf'
    except Exception as exc: row['status']='request_error';row['error']=str(exc)
    return row

if __name__=='__main__':
    pairs=[(c,d) for c,dates in CANDIDATES.items() for d in dates]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(fetch,pairs))
    (BASE/'broker_download_log.json').write_text(json.dumps(rows,indent=2)+'\n')
    for row in rows:
        print(row['company_id'],row['candidate_date'],row['status'],row.get('http_status',''))
