#!/usr/bin/env python3
"""Retain recent public Morningstar reports in a review inbox, without importing EPS."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT_IDS = {
    'broadcom': '0P0000KU35', 'alphabet': '0P000002HD',
    'nvidia': '0P000003RE', 'micron': '0P000003MC',
    'sandisk': '0P0001U8JM', 'asml': '0P0000002X', 'apple': '0P000000GY',
}


def retain_pdf(body, inbox):
    if not body.startswith(b'%PDF-'):
        raise ValueError('Response is not a PDF')
    digest = hashlib.sha256(body).hexdigest()
    path = inbox / 'raw' / (digest + '.pdf')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Content-addressed artifacts are never overwritten, including a changed URL.
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError('Retained artifact does not match its hash')
    else:
        with path.open('xb') as handle:
            handle.write(body)
    return path, digest


def discover(as_of, days, root=ROOT):
    if not 1 <= days <= 31 or as_of > datetime.now(timezone.utc).date():
        raise ValueError('Use 1–31 days ending no later than today')
    inbox = root / 'data/inbox/morningstar'
    inbox.mkdir(parents=True, exist_ok=True)
    manifest = inbox / 'manifest.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else []
    catalog = root / 'data/source_catalog.csv'
    with catalog.open() as handle:
        known = {r['sha256'] for r in csv.DictReader(handle) if r.get('sha256')}
    known.update(r['source_sha256'] for r in previous if r.get('source_sha256'))
    jobs = []
    for company, report_id in REPORT_IDS.items():
        for offset in range(days):
            day = as_of - timedelta(days=offset)
            url = f'https://invest.firstrade.com/ms/equity_reports/sr/{day.year}/{report_id}_{day:%Y%m%d}_RT.pdf'
            jobs.append((company, day.isoformat(), url))

    def fetch(job):
        company, url_date, url = job
        row = dict(company_id=company, url_date=url_date, source_url=url,
                   retrieved_at=datetime.now(timezone.utc).isoformat())
        try:
            with requests.get(url, timeout=(8, 20), stream=True,
                              headers={'User-Agent': 'Mozilla/5.0 (personal research archive)'}) as response:
                row['http_status'] = response.status_code
                if response.status_code != 200:
                    row['status'] = 'not_found' if response.status_code == 404 else 'request_failed'
                    return row
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 20_000_000:
                        raise ValueError('Report exceeds the 20 MB download limit')
                if not body.startswith(b'%PDF-'):
                    raise ValueError('Response is not a PDF')
                row['_body'] = bytes(body)
        except (requests.RequestException, ValueError) as error:
            row.update(status='request_failed', error=str(error))
        return row

    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(fetch, jobs):
            body = row.pop('_body', None)
            if body is not None:
                digest = hashlib.sha256(body).hexdigest()
                if digest in known:
                    row.update(status='already_retained', source_sha256=digest)
                else:
                    path, digest = retain_pdf(body, inbox)
                    row.update(status='awaiting_eps_review', source_file=str(path.relative_to(root)), source_sha256=digest)
                    known.add(digest)
            rows.append(row)
    temporary = manifest.with_suffix('.tmp')
    temporary.write_text(json.dumps(previous + rows, indent=2) + '\n')
    temporary.replace(manifest)
    result = {'requests': len(rows), 'new_reports_awaiting_review': sum(r['status'] == 'awaiting_eps_review' for r in rows),
              'request_failures': sum(r['status'] == 'request_failed' for r in rows),
              'coverage': 'Seven Morningstar distributor IDs; Korean brokers require separate collection',
              'notice': 'URL dates are discovery hints. Printed dates, model vintages, author, EPS basis, fiscal periods and splits require review before import.'}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()
    print(json.dumps(discover(args.as_of, args.days)))
