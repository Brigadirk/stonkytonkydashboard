#!/usr/bin/env python3
"""Validate a licensed, dated NTM EPS export and preserve an immutable import."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['company_id','series_id','label','available_at','estimate_date','eps','currency','accounting_basis','share_basis_date','source_url','source_reference']


def parse_import(contents, universe, cutoff):
    reader = csv.DictReader(io.StringIO(contents))
    if reader.fieldnames is None or set(FIELDS) - set(reader.fieldnames):
        raise ValueError('Missing required columns: ' + ', '.join(sorted(set(FIELDS)-set(reader.fieldnames or []))))
    series = {}
    seen = set()
    for i, row in enumerate(reader, 2):
        if any(not row.get(k, '').strip() for k in FIELDS):
            raise ValueError(f'Row {i}: every required field must be filled')
        cid = row['company_id']
        if cid not in universe or row['currency'] != universe[cid]:
            raise ValueError(f'Row {i}: unknown company or mismatched currency')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', row['series_id']):
            raise ValueError(f'Row {i}: series_id must use letters, digits, underscores or hyphens')
        available = datetime.fromisoformat(row['available_at'].replace('Z', '+00:00'))
        if available.tzinfo is None:
            raise ValueError(f'Row {i}: available_at needs an explicit timezone')
        available = available.astimezone(timezone.utc)
        estimate_date = datetime.strptime(row['estimate_date'], '%Y-%m-%d').date()
        share_date = datetime.strptime(row['share_basis_date'], '%Y-%m-%d').date()
        if estimate_date > available.date() or available.date().isoformat() > cutoff or share_date.isoformat() > cutoff:
            raise ValueError(f'Row {i}: inconsistent or future dates')
        if not row['source_url'].startswith(('https://','http://')):
            raise ValueError(f'Row {i}: source_url must identify the provider or original source')
        eps = float(row['eps'])
        if not math.isfinite(eps):
            raise ValueError(f'Row {i}: EPS must be finite; negative EPS is permitted')
        identity = (cid,row['series_id'],available.isoformat())
        if identity in seen:
            raise ValueError(f'Row {i}: duplicate company/series/availability timestamp')
        seen.add(identity)
        sid = 'import_' + cid + '_' + row['series_id']
        analyst, firm = row.get('analyst', '').strip(), row.get('firm', '').strip()
        source_type = row.get('series_type', '').strip() or ('individual_analyst_forecast' if analyst else 'published_consensus')
        if source_type not in {'individual_analyst_forecast', 'published_consensus'}:
            raise ValueError(f'Row {i}: series_type must identify an individual analyst or published consensus')
        if source_type == 'individual_analyst_forecast' and (not analyst or not firm):
            raise ValueError(f'Row {i}: named estimates require both analyst and firm')
        if source_type == 'published_consensus' and analyst:
            raise ValueError(f'Row {i}: consensus must not be attributed to an individual analyst')
        metadata = {**{k: row[k] for k in ['label','accounting_basis','currency']}, 'analyst': analyst,
                    'firm': firm or 'Imported provider export', 'series_type': source_type}
        if sid in series and any(series[sid][k] != v for k,v in metadata.items()):
            raise ValueError(f'Row {i}: series changes accounting basis, label, currency or contributor identity')
        series.setdefault(sid, {'id':sid,'company_id':cid,**metadata,'coverage_note':'Provider NTM snapshot; availability timestamps and accounting conventions supplied by the licensed export. Used from the next UTC calendar day.','snapshots':[]})
        digest = hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
        series[sid]['snapshots'].append({'id':digest[:24], 'kind':'ntm', 'report_date':estimate_date.isoformat(), 'model_date':estimate_date.isoformat(), 'available_date':(available.date()+timedelta(days=1)).isoformat(), 'available_at':available.isoformat(), 'availability_basis':'verified_available_at', 'share_basis_date':share_date.isoformat(), 'source_url':row['source_url'], 'source_file':'', 'source_sha256':digest, 'source_reference':row['source_reference'], 'estimates':[{'observation_id':digest[:24], 'fiscal_period':'NTM', 'fiscal_period_start':'', 'fiscal_period_end':'', 'eps':eps, 'source_page':''}]})
    if not series:
        raise ValueError('The file has no estimate rows')
    for s in series.values():
        s['snapshots'].sort(key=lambda x: (x['available_date'],x['available_at']))
    return {'schema_version':1,'series':list(series.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file',type=Path)
    parser.add_argument('--cutoff',default='2026-09-10')
    args = parser.parse_args()
    raw = args.file.read_bytes()
    with (ROOT/'data/universe.csv').open() as f:
        universe = {r['company_id']:r['forecast_currency'] for r in csv.DictReader(f)}
    imported = parse_import(raw.decode('utf-8-sig'),universe,args.cutoff)
    digest = hashlib.sha256(raw).hexdigest()
    archive = ROOT/'data/market/imports'/digest
    archive.mkdir(parents=True,exist_ok=True)
    (archive/'original.csv').write_bytes(raw)
    for series in imported['series']:
        for snapshot in series['snapshots']:
            snapshot['source_row_sha256'] = snapshot['source_sha256']
            snapshot['source_sha256'] = digest
            snapshot['source_file'] = str((archive/'original.csv').relative_to(ROOT))
    imported['import_sha256'] = digest
    imported['imported_at'] = datetime.now(timezone.utc).isoformat()
    (archive/'validated.json').write_text(json.dumps(imported,indent=2,allow_nan=False)+'\n')
    (ROOT/'data/market/imported_ntm.json').write_text(json.dumps(imported,indent=2,allow_nan=False)+'\n')
    print(f'Validated {sum(len(s["snapshots"]) for s in imported["series"])} snapshots in {len(imported["series"])} series. Original preserved: {archive.relative_to(ROOT)}')
    print('Run python3 scripts/build_dashboard_data.py, then rebuild the app.')


if __name__=='__main__':
    main()
