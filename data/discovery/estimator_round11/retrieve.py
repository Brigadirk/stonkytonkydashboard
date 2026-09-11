#!/usr/bin/env python3
"""Retain exact public discovery URLs; no extracted forecast enters the app here."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent

def retrieve(name, url):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = HERE / 'retrievals' / stamp
    folder.mkdir(parents=True)
    row = {'name': name, 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=40, headers={'User-Agent': 'Mozilla/5.0'})
        body = response.content
        mime = response.headers.get('Content-Type', '')
        suffix = '.pdf' if body.startswith(b'%PDF') else '.jpg' if 'image/jpeg' in mime else '.png' if 'image/png' in mime else '.webp' if 'image/webp' in mime else '.json' if 'json' in mime else '.html'
        path = folder / (name + suffix)
        path.write_bytes(body)
        row.update(status=response.status_code, final_url=response.url, content_type=response.headers.get('Content-Type'), file=str(path.relative_to(HERE)), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    except requests.RequestException as error:
        row['error'] = str(error)
    (folder / 'request.json').write_text(json.dumps(row, indent=2)+'\n')
    print(json.dumps(row))
    return row

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('url')
    args = parser.parse_args()
    if not args.name.replace('_', '').replace('-', '').isalnum():
        parser.error('Name must contain only letters, digits, underscores or hyphens')
    retrieve(args.name, args.url)
