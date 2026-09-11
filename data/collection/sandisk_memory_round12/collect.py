"""Probe dated public distributor originals around independently dated Sandisk notes."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
for folder in ['pdfs', 'text', 'review']:
    (BASE/folder).mkdir(exist_ok=True)

# Dates are discovery hints from Morningstar's public report archive, not model dates.
ANCHORS = ['2025-02-27', '2025-05-08', '2025-07-22', '2025-08-04',
           '2026-07-02', '2026-07-29', '2026-08-06']
DATES = sorted({(date.fromisoformat(anchor)+timedelta(days=n)).strftime('%Y%m%d')
                for anchor in ANCHORS for n in range(-1, 9)})
DATES = sorted(set(DATES) | {'20250731','20250801','20250802','20250813'} |
               {(date(2025,5,16)+timedelta(weeks=n)).strftime('%Y%m%d') for n in range(11)})

def prior_urls():
    prior = set()
    for folder in (ROOT/'data/collection').iterdir():
        if folder == BASE or not folder.is_dir(): continue
        for p in folder.rglob('*'):
            if p.suffix not in ['.json', '.csv'] or p.stat().st_size > 20_000_000: continue
            prior.update(re.findall(r'https://invest\.firstrade\.com/ms/equity_reports/sr/\d{4}/0P0001U8JM_\d{8}_RT\.pdf', p.read_text(errors='ignore')))
    return prior

def fetch(day, prior):
    url=f'https://invest.firstrade.com/ms/equity_reports/sr/{day[:4]}/0P0001U8JM_{day}_RT.pdf'
    row=dict(company_id='sandisk', candidate_date=day, source_url=url,
             retrieved_at=datetime.now(timezone.utc).isoformat())
    if url in prior:
        row['status']='skipped_prior_attempt'; return row
    try:
        r=requests.get(url, timeout=(8,20), headers={'User-Agent':'Mozilla/5.0 (personal research archive)'})
        row['http_status']=r.status_code
        if r.status_code == 200 and r.content.startswith(b'%PDF-'):
            digest=hashlib.sha256(r.content).hexdigest()
            p=BASE/'pdfs'/f'sandisk_{day}_{digest[:12]}.pdf'
            if p.exists(): assert p.read_bytes()==r.content
            else: p.write_bytes(r.content)
            t=BASE/'text'/f'{p.stem}.txt'
            subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
            row.update(status='retained_pending_review',local_file=str(p.relative_to(ROOT)),
                       text_file=str(t.relative_to(ROOT)),sha256=digest)
        else: row['status']='no_original_pdf'
    except Exception as exc:
        row.update(status='request_error',error=str(exc))
    return row

if __name__=='__main__':
    log=BASE/'download_log.json'
    previous=json.loads(log.read_text()) if log.exists() else []
    attempted={r['candidate_date'] for r in previous}
    prior=prior_urls()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda d:fetch(d,prior),[d for d in DATES if d not in attempted]))
    log.write_text(json.dumps(previous+rows,indent=2)+'\n')
    for r in rows: print(r['candidate_date'],r['status'],r.get('http_status',''))
