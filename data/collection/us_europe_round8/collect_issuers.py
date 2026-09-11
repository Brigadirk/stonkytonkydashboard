"""Retain initial issuer annual release materials from public primary URLs."""
import concurrent.futures
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
items=[]
for row in json.loads((BASE/'issuer_discovery.json').read_text()):
    for link in row['links']:
        if ('Financial statements US GAAP' in link['text'] or 'Press release quarterly' in link['text'] or 'Press Release Quarterly' in link['text']) and link['url'].endswith('.pdf'):
            kind='statements' if 'Financial statements' in link['text'] else 'release'
            items.append(dict(company_id='asml',fiscal_year=row['fiscal_year'],source_url=link['url'],name=f"asml_fy{row['fiscal_year']}_{kind}",kind=kind))
items += [
    dict(company_id='nvidia',fiscal_year=2026,source_url='https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026',name='nvidia_fy2026_release',kind='release'),
    dict(company_id='sandisk',fiscal_year=2026,source_url='https://investor.sandisk.com/node/8136/pdf',name='sandisk_fy2026_release',kind='release'),
    dict(company_id='sandisk',fiscal_year=2025,source_url='https://investor.sandisk.com/static-files/d96ed014-e75d-4c57-b63a-c304d6410c64',name='sandisk_fy2025_release',kind='release'),
    dict(company_id='sandisk',fiscal_year=2026,source_url='https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-05-sandisk-reports-fiscal-fourth-quarter-2026-financial-results',name='sandisk_fy2026_release',kind='release'),
    dict(company_id='sandisk',fiscal_year=2025,source_url='https://www.sandisk.com/company/newsroom/press-releases/2025/2025-08-14-sandisk-reports-fiscal-fourth-quarter-2025-financial-results',name='sandisk_fy2025_release',kind='release'),
]

def fetch(item):
    row=dict(item,retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(item['source_url'],timeout=25)
        row['http_status']=r.status_code
        if r.status_code != 200:
            row['status']='request_failed';return row
        pdf=r.content.startswith(b'%PDF')
        ext='pdf' if pdf else 'html'
        p=BASE/'originals'/f"{item['name']}.{ext}";p.write_bytes(r.content)
        t=BASE/'text'/f"{item['name']}.txt"
        if pdf:subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
        else:t.write_text(BeautifulSoup(r.text,'html.parser').get_text('\n',strip=True))
        row.update(status='retained_pending_review',local_file=str(p.relative_to(ROOT)),text_file=str(t.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest(),artifact_type=ext)
    except Exception as exc:row.update(status='request_error',error=str(exc))
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,items))
(BASE/'issuer_download_log.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows: print(row['name'],row['status'],row.get('http_status',''))
