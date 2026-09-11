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

IDS = {'broadcom':'0P0000KU35','alphabet':'0P000002HD', 'asml':'0P0000002X', 'sandisk':'0P0001U8JM', 'apple':'0P000000GY'}
CANDIDATES = {
    'broadcom':['20210304','20210305','20210603','20210604','20210902','20210903','20211209','20211210','20220303','20220304','20220526','20250605','20250606','20250609','20250610','20250612'],
    'apple':['20240503','20240506','20240507','20240508','20240610','20240611','20240612'],
    'alphabet':['20230425','20230426','20230427','20230510','20230511','20230512','20230717','20230718','20240130','20240131','20240201','20240202','20240205','20240206','20240318','20240319','20240320'],
    'asml':['20241106','20241115','20241118','20241204'],
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
