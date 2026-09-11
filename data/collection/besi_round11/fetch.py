#!/usr/bin/env python3
"""Retain public BESI leads without replacing prior captures; no authenticated routes."""
import datetime, hashlib, json, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
if sys.argv[1:] == ['--refresh']:
    recipe = json.loads((BASE / 'download_log.json').read_text())
    pairs = [(r['name'], r['source_url']) for r in recipe]
    BASE = BASE / 'retrieval' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
else:
    if len(sys.argv[1:]) % 2:
        raise SystemExit('Use --refresh or NAME URL pairs.')
    pairs = list(zip(sys.argv[1::2], sys.argv[2::2]))
(BASE / 'originals').mkdir(parents=True, exist_ok=True)
(BASE / 'text').mkdir(parents=True, exist_ok=True)
log_path = BASE / 'download_log.json'
log = json.loads(log_path.read_text()) if log_path.exists() else []
for name, url in pairs:
    if any(x['name'] == name for x in log):
        print(json.dumps({'name': name, 'status': 'retained capture exists; skipped'}))
        continue
    record = {'name': name, 'source_url': url, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r = requests.get(url, timeout=45, headers={'User-Agent': 'Mozilla/5.0 (compatible; public research)'})
        ext = '.pdf' if r.content.startswith(b'%PDF') else '.jpg' if r.content.startswith(b'\xff\xd8') else '.png' if r.content.startswith(b'\x89PNG') else '.html'
        path = BASE / 'originals' / (name + ext)
        path.write_bytes(r.content)
        record.update(http_status=r.status_code, final_url=r.url, local_file=str(path.relative_to(ROOT)), sha256=hashlib.sha256(r.content).hexdigest(), content_type=r.headers.get('Content-Type'), byte_count=len(r.content))
        if ext == '.html':
            soup = BeautifulSoup(r.content, 'xml' if 'xml' in r.headers.get('Content-Type', '') else 'html.parser')
            for tag in soup(['script', 'style', 'noscript']): tag.decompose()
            txt = BASE / 'text' / (name + '.txt')
            txt.write_text(soup.get_text('\n', strip=True))
            record['text_file'] = str(txt.relative_to(ROOT))
    except Exception as exc:
        record['error'] = str(exc)
    log.append(record)
    log_path.write_text(json.dumps(log, indent=2) + '\n')
    print(json.dumps(record))
