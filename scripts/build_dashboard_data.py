#!/usr/bin/env python3
"""Validate and bundle retained public research into the local browser app."""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = '2026-09-10'


def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def build(cutoff=CUTOFF):
    datetime.strptime(cutoff, '%Y-%m-%d')
    universe = read_csv(ROOT / 'data/universe.csv')
    panel = read_csv(ROOT / 'data/market/forecast_panel.csv')
    series_rows = read_csv(ROOT / 'data/market/forecast_series.csv')
    prices = read_csv(ROOT / 'data/market/prices.csv')
    splits = read_csv(ROOT / 'data/market/splits.csv')
    forecast_gaps = json.loads((ROOT / 'data/market/forecast_gaps.json').read_text())
    market_summary = json.loads((ROOT / 'data/market/summary.json').read_text())
    if market_summary['cutoff'] != cutoff or forecast_gaps['as_of'] != cutoff:
        raise ValueError('Prices, forecasts and dashboard must use the same cutoff')
    raw_counts = Counter(r['company_id'] for r in read_csv(ROOT / 'data/collected_forecasts.csv'))
    summary = json.loads((ROOT / 'data/collection_summary.json').read_text())
    compatibility_path = ROOT / 'data/market/ensemble_compatibility.json'
    compatibility_rules = json.loads(compatibility_path.read_text()) if compatibility_path.exists() else []
    for rule in compatibility_rules:
        if hashlib.sha256((ROOT / rule['evidence_file']).read_bytes()).hexdigest() != rule['evidence_sha256']:
            raise ValueError('Ensemble compatibility review hash mismatch')
        for evidence in rule.get('supporting_evidence', []):
            if hashlib.sha256((ROOT / evidence['source_file']).read_bytes()).hexdigest() != evidence['source_sha256']:
                raise ValueError('Supporting ensemble compatibility review hash mismatch')
    checked = set()
    companies = []
    for security in universe:
        cid = security['company_id']
        company_prices = []
        seen_dates = set()
        for row in sorted((r for r in prices if r['company_id'] == cid), key=lambda r: r['date']):
            assert row['currency'] == security['price_currency'], row
            assert row['date'] <= cutoff and row['date'] not in seen_dates, row
            assert math.isfinite(float(row['close'])) and float(row['close']) > 0, row
            assert row['adjustment_basis'] == 'split_adjusted_to_cutoff', row
            if cid == 'sandisk':
                assert row['date'] >= '2025-02-24', row
            seen_dates.add(row['date'])
            company_prices.append({k: float(v) if k == 'close' else v for k, v in row.items() if k != 'company_id'})
        company_series = []
        for series in (r for r in series_rows if r['company_id'] == cid):
            snapshots = {}
            for row in (r for r in panel if r['series_id'] == series['series_id']):
                assert row['currency'] == security['forecast_currency'] == series['currency'], row
                assert row['report_date'] <= cutoff and row['available_date'] > row['report_date'], row
                assert not row['model_date'] or row['model_date'] <= row['report_date'], row
                assert row['fiscal_period_start'] <= row['fiscal_period_end'], row
                path = ROOT / row['source_file']
                if (path, row['source_sha256']) not in checked:
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['source_sha256'], path
                    checked.add((path, row['source_sha256']))
                if row['snapshot_id'] not in snapshots:
                    snapshots[row['snapshot_id']] = {**{k: row[k] for k in ['report_date', 'model_date', 'available_date', 'availability_basis', 'share_basis_date', 'source_url', 'source_file', 'source_sha256']}, 'first_observed_at': row.get('first_observed_at', ''), 'id': row['snapshot_id'], 'kind': 'annual', 'estimates': []}
                    snapshots[row['snapshot_id']].update({k:row.get(k, '') for k in ['verified_available_date','verified_available_at','availability_evidence_url','verification_kind']})
                snapshot = snapshots[row['snapshot_id']]
                assert snapshot['source_sha256'] == row['source_sha256'], row
                assert not any(e['fiscal_period'] == row['fiscal_period'] for e in snapshot['estimates']), row
                eps = float(row['eps'])
                assert math.isfinite(eps), row
                snapshot['estimates'].append({**{k: row[k] for k in ['observation_id', 'fiscal_period', 'fiscal_period_start', 'fiscal_period_end', 'source_page', 'notes', 'original_accounting_basis', 'basis_alias_evidence']}, 'eps': eps})
            company_series.append({**{k: series[k] for k in ['label', 'analyst', 'firm', 'accounting_basis', 'currency', 'coverage_note', 'series_type', 'comparability_note', 'comparability_source_url']}, 'id': series['series_id'], 'snapshots': sorted(snapshots.values(), key=lambda r: (r['available_date'], r['report_date']))})
        gap = next(g for g in forecast_gaps['companies'] if g['company_id'] == cid)
        for series in company_series:
            for rule in compatibility_rules:
                if (cid, series['firm'], series['accounting_basis']) != (rule['company_id'], rule['firm'], rule['accounting_basis']):
                    continue
                approved = []
                for snapshot in series['snapshots']:
                    for scope in rule['scopes']:
                        if (snapshot['source_sha256'], snapshot['report_date'], snapshot['model_date'], series['analyst']) != (scope['source_sha256'], scope['report_date'], scope['model_date'], scope['authors']):
                            continue
                        expected = dict(zip(scope['fiscal_periods'], map(float, scope['printed_eps'])))
                        if {e['fiscal_period']:e['eps'] for e in snapshot['estimates']} != expected:
                            raise ValueError('EPS differs from the exact model supporting ensemble compatibility')
                        approved.append(snapshot['id'])
                series['compatibility_group'] = {**{k:rule[k] for k in ['id','label','note','evidence_url']}, 'approved_snapshot_ids':approved}
        gaps = [gap['needed'], 'Printed report dates are known; first publication timestamps have not been independently verified.', 'Analyst ranking requires broader comparable outcomes and historical consensus benchmarks; the EPS pilot includes only eligible reported diluted EPS pairs.']
        if cid in ('sk_hynix', 'samsung_electronics'):
            gaps.append('Broker EPS denominators require reconciliation before comparing analysts or statutory EPS.')
        if cid == 'sandisk':
            gaps.append('This standalone company begins trading on 24 February 2025. Its predecessor is a different security.')
        companies.append({'id': cid, 'name': security['company_name'], 'symbol': security['listing_symbol'], 'exchange': security['exchange'], 'currency': security['price_currency'], 'prices': company_prices, 'splits': [{k: float(v) if k == 'ratio' else v for k, v in s.items() if k != 'company_id'} for s in splits if s['company_id'] == cid], 'series': company_series, 'gaps': gaps, 'forecast_count': raw_counts[cid]})
    # Optional, validated licensed NTM imports are kept separate from original
    # public analyst models. No credentials or live provider calls in the browser.
    import_path = ROOT / 'data/market/imported_ntm.json'
    if import_path.exists():
        imported = json.loads(import_path.read_text())
        for series in imported['series']:
            company = next(c for c in companies if c['id'] == series['company_id'])
            assert series['currency'] == company['currency']
            assert not any(s['id'] == series['id'] for s in company['series'])
            company['series'].append({k: v for k, v in series.items() if k != 'company_id'})
    data = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(), 'cutoff': cutoff, 'companies': companies, 'outcomes': read_csv(ROOT / 'data/issuer_outcomes.csv'), 'revenue_pilot': read_csv(ROOT / 'data/revenue_pilot.csv'), 'totals': {'broker_pdfs': summary['unique_broker_pdfs'], 'forecast_observations': sum(raw_counts.values())}, 'access_notes': ['The public collection is still expanding. Complete five-year bands require more dated EPS snapshots and revisions; long gaps and incomplete recent coverage remain.', 'FactSet Estimates or LSEG I/B/E/S are relevant sources to request a sample from. Exact universe coverage, export entitlement and price remain unverified.', 'Public daily price downloads succeeded across the current universe. ScrapingBee has not been needed; proxy credits do not supply institutional estimate archives.']}
    if market_summary.get('reviewed_daily_close_supplements'):
        data['access_notes'].append('Reviewed daily closes from Naver and Euronext independently check or fill explicit base-feed gaps. Price source URLs and hashes are included in the chart CSV. The two September 2025 Korean bars remain unresolved; retained source-native closes have not been silently assigned a historical adjustment convention.')
    pilot_path = ROOT / 'data/eps_pilot.json'
    if pilot_path.exists():
        data['eps_pilot'] = json.loads(pilot_path.read_text())
        if data['eps_pilot']['as_of'] != cutoff:
            raise ValueError('EPS evaluation must use the dashboard cutoff')
    output = ROOT / 'web/public/data/dashboard.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False) + '\n')
    print(f'Bundled {len(companies)} companies, {sum(len(c["prices"]) for c in companies)} prices, {sum(len(c["series"]) for c in companies)} earnings series: {output.relative_to(ROOT)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', default=CUTOFF)
    build(parser.parse_args().as_of)
