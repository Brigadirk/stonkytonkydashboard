#!/usr/bin/env python3
"""Rebuild the BESI broker collection from retained, reviewed originals only."""
import csv
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST_FIELDS = 'source_url local_file company_ids firm analyst_name report_date retrieved_at sha256 status notes text_file report_timestamp model_dates http_status report_month report_date_precision artifact_type'.split()
OBS_FIELDS = 'observation_id company_id firm analyst_name metric fiscal_period value currency unit basis model_date forecast_revision_as_of report_date available_at printed_report_timestamp original_available_at availability_basis source_url local_file page status notes forecast_type source_type source_period_label share_basis_date source_artifact_sha256'.split()

sources = {}
for discovery in sorted(HERE.glob('discovery_*.json')):
    records = json.loads(discovery.read_text())
    for record in records if isinstance(records, list) else [records]:
        key = record.get('key', record.get('name', Path(record['local_file']).stem))
        if key == 'kasikorn_besi_20260605' and record['local_file'].endswith('.jpg'):
            key += '_image'
        record['source_url'] = record.get('source_url', record.get('url'))
        record['http_status'] = record.get('http_status', record.get('status'))
        assert hashlib.sha256((ROOT / record['local_file']).read_bytes()).hexdigest() == record['sha256']
        sources[key] = record

observations = []
manifests = []
CONSENSUS = 'report_embedded_consensus'
INDIVIDUAL = 'individual_analyst_forecast'
GOOD = 'extracted_original_table_unscored'

def manifest(key, date, firm, analyst, status, notes, model=''):
    s = sources[key]
    row = {field: '' for field in MANIFEST_FIELDS}
    row.update({field: s.get(field, '') for field in ('source_url', 'local_file', 'retrieved_at', 'sha256', 'text_file', 'http_status')})
    row.update(company_ids='besi', firm=firm, analyst_name=analyst, report_date=date,
               status=status, notes=notes, model_dates=model, report_month=date[:7],
               report_date_precision='day' if date else 'not_dated',
               artifact_type=Path(s['local_file']).suffix.lstrip('.'))
    manifests.append(row)

def observation(key, date, firm, analyst, source_type, year, value, metric, basis,
                notes, page='HTML table 1', status=GOOD, currency='EUR', model='', label=None):
    s = sources[key]
    row = {field: '' for field in OBS_FIELDS}
    row.update(company_id='besi', firm=firm, analyst_name=analyst, metric=metric,
               fiscal_period=f'FY{year}', value=str(value), currency=currency,
               unit=f'{currency}_per_share' if metric == 'eps' else f'{currency}_million',
               basis=basis, model_date=model, forecast_revision_as_of=model, report_date=date,
               availability_basis='publisher_stated_report_date_not_independently_verified',
               source_url=s['source_url'], local_file=s['local_file'], page=page, status=status,
               notes=notes, forecast_type='consensus_reported_by_analyst' if source_type == CONSENSUS else 'analyst_forecast',
               source_type=source_type, source_period_label=label or f'{year}E',
               source_artifact_sha256=s['sha256'])
    row['observation_id'] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:24]
    observations.append(row)

SAXO = [
    ('saxo_iex_20251006', '2025-10-06', [2025, 2026, 2027], ['1.71', '4.72', '6.18'], ['585.0', '1014.0', '1292.9'], INDIVIDUAL),
    ('saxo_iex_20251023', '2025-10-23', [2025, 2026, 2027, 2028], ['1.71', '4.72', '6.28', '6.89'], ['585.0', '1012.1', '1341.0', '1475.1'], INDIVIDUAL),
    ('saxo_iex_20260423', '2026-04-23', [2026, 2027, 2028], ['4.18', '5.62', '6.33'], ['964.9', '1264.0', '1434.7'], INDIVIDUAL),
    ('saxo_stockwatch_20260106', '2026-01-06', [2025, 2026, 2027], ['1.65', '3.33', '4.83'], ['589.7', '832.5', '1086'], CONSENSUS),
    ('saxo_stockwatch_20260219', '2026-02-19', [2026, 2027, 2028], ['3.35', '4.93', '6.15'], ['853.5', '1108', '1282'], CONSENSUS),
    ('saxo_stockwatch_20250724', '2025-07-24', [2025, 2026, 2027], ['2.12', '3.76', '5.05'], ['629.6', '880.6', '1085'], 'publisher_forecast_unattributed'),
]
for key, date, years, eps, revenue, kind in SAXO:
    soup = BeautifulSoup((ROOT / sources[key]['local_file']).read_bytes(), 'html.parser')
    text = soup.get_text(' ', strip=True)
    table = soup.select_one('table')
    rows = [[cell.get_text(' ', strip=True) for cell in row.find_all(['th', 'td'])] for row in table.select('tr')]
    headers = rows[0]
    eps_row = next(row for row in rows if row[0].startswith('Winst per aandeel'))
    revenue_row = next(row for row in rows if row[0].startswith('Omzet'))
    named = kind == INDIVIDUAL
    normalize = lambda value: value.replace(',', '.') if named else value.replace(',', '')
    for year, ev, rv in zip(years, eps, revenue):
        column = headers.index(f'{year}E')
        assert float(normalize(eps_row[column])) == float(ev), (key, year, eps_row)
        assert float(normalize(revenue_row[column])) == float(rv), (key, year, revenue_row)
    firm = 'IEX' if named else 'StockWatch (LSEG consensus)' if kind == CONSENSUS else 'StockWatch'
    analyst = 'Hildo Laman' if named else ''
    status = GOOD if named or kind == CONSENSUS else 'quarantined_annual_table_forecast_attribution_unresolved'
    notes = ('Original research article distributed by Saxo, whose article explicitly identifies the original publisher and publication date. '
             'Annual EPS is transcribed directly, not inferred from valuation multiples. EUR per ordinary share; no FX conversion. '
             'EPS adjustment and basic/diluted denominator are unspecified; keep this publisher/source series apart from issuer reported diluted EPS. '
             'No independently verified historical dissemination timestamp; mutable navigation and current related articles are not used as model dates. ')
    model = ''
    if named:
        assert 'taxaties IEX' in text or 'taxaties Analistenteam' in text
        notes += 'The annual forecasts are IEX own estimates, distinct from the Bloomberg quarterly-consensus image. '
        if key == 'saxo_iex_20260423':
            assert 'Mijn taxaties gaan omhoog' in text and 'Laman heeft' in text
            notes += ('Surname Laman is printed in the disclosure; normalized to Hildo Laman using the full-name attribution in the retained October 2025 IEX articles. '
                      'FY2025 is incorrectly labelled 2025E although its values are already released FY2025 actuals; those cells are excluded. '
                      'The article explicitly raises its numerical forecasts on the April 23 outlook; model date uses this contemporaneous revision statement, not a separate printed model timestamp. ')
            model = date
        elif key == 'saxo_iex_20251006':
            assert 'Hildo Laman' in text and 'Ik laat de taxaties op dit moment ongemoeid' in text
            notes += ('Original-publication notice says October 6; the Saxo URL contains October 7. Separate redistribution timing is unverified. '
                      'Author explicitly leaves existing forecasts unchanged; their earlier origin is unknown and no model/revision date is assigned. ')
        else:
            assert 'Hildo Laman' in text
            notes += 'No separate model timestamp printed. FY2027 differs from the October 6 appearance and FY2028 is added. '
        basis = 'iex_eps_adjustment_and_dilution_unspecified'
    elif kind == CONSENSUS:
        assert 'Taxaties LSEG consensus' in text
        notes += 'Annual table explicitly attributes estimates to LSEG consensus. StockWatch writer is not the forecast author; analyst attribution is blank. '
        basis = 'lseg_consensus_eps_adjustment_and_dilution_unspecified'
    else:
        assert 'LSEG' not in text
        notes += ('The July annual table has no provider/consensus caption. References to the writer own long-term valuation model do not establish who owns each tabulated forecast. '
                  'Later LSEG-labelled articles cannot establish this earlier table provenance; quarantined. ')
        basis = 'eps_forecast_attribution_unresolved'
    manifest(key, date, firm, analyst, status, notes, model)
    for year, ev, rv in zip(years, eps, revenue):
        observation(key, date, firm, analyst, kind, year, ev, 'eps', basis, notes, status=status, model=model)
        observation(key, date, firm, analyst, kind, year, rv, 'revenue', 'total_revenue', notes, status=status, model=model)

key = 'eugene_sector_20231016'
page = (ROOT / sources[key]['text_file']).read_text().split('\f')[153]
for token in ['2023.10.16', '2021A 2022A 2023E 2024E', 'EPS(유로)', '3.70', '3.03', '2.15', '3.41', '블룸버그 컨센서스']:
    assert token in page, token
notes = ('Original Eugene Investment sector report, physical PDF page 154, visually reviewed. '
         'The BESI annual December-ending table explicitly labels EPS in euro and attributes figures to Bloomberg consensus. '
         'Report author Sophie Yim is not attributed these consensus estimates. EPS adjustment/dilution is unspecified. '
         'No separate model date or independently verified publication timestamp. No USD peer-table amounts or EPS derived from PE are used.')
manifest(key, '2023-10-16', 'Eugene Investment (Bloomberg consensus)', '', GOOD, notes)
for year, ev, rv in [(2023, '2.15', '579'), (2024, '3.41', '788')]:
    observation(key, '2023-10-16', 'Eugene Investment (Bloomberg consensus)', '', CONSENSUS, year, ev, 'eps', 'bloomberg_consensus_eps_adjustment_and_dilution_unspecified', notes, page=154)
    observation(key, '2023-10-16', 'Eugene Investment (Bloomberg consensus)', '', CONSENSUS, year, rv, 'revenue', 'total_revenue', notes, page=154)

for key, date, eps, revenue, physical_page in [
        ('hana_besi_20240621', '2024-06-21', ['2.7', '4.5'], ['702', '1005'], 4),
        ('hana_besi_20241028', '2024-10-28', ['2.3', '3.7'], ['627', '873'], 3)]:
    text = (ROOT / sources[key]['text_file']).read_text()
    assert 'EPS(USD)' in text and 'Bloomberg' in text
    notes = ('Original Hana report: annual financial table on page 1 and detailed financials on physical page '
             f'{physical_page}. Detailed footnote explicitly identifies Bloomberg-adjusted EPS and Bloomberg market consensus. '
             'Forecasts are not attributed to report author Kim Min-kyung. Revenue is explicitly EUR million. '
             'EPS row and per-share table are explicitly labelled USD despite the EUR statements/listing. '
             'Keep printed EPS as USD in quarantine; do not relabel or convert to EUR without source evidence. '
             'Revenue currency is unambiguous and is retained separately. No independently verified release timestamp.')
    manifest(key, date, 'Hana Securities (Bloomberg consensus)', '', 'partially_extracted_eps_currency_label_quarantined', notes)
    for year, ev, rv in zip([2024, 2025], eps, revenue):
        observation(key, date, 'Hana Securities (Bloomberg consensus)', '', CONSENSUS, year, ev, 'eps', 'bloomberg_adjusted_eps_usd_label_conflict', notes,
                    page=physical_page, status='quarantined_eps_currency_label_conflict', currency='USD', label=f'{year}F')
        observation(key, date, 'Hana Securities (Bloomberg consensus)', '', CONSENSUS, year, rv, 'revenue', 'total_revenue', notes, page=1, label=f'{year}F')

key = 'kasikorn_besi_20260605_image'
notes = ('Original Kasikorn infographic on the June 5, 2026 broker article, visibly dated data-as-of June 3, 2026. '
         'Explicit annual EUR EPS table was visually transcribed. Source credits KS Research, Bloomberg and Company collectively without identifying the owner of each forecast. '
         'Its Q1 2026 summary incorrectly presents Q4 2025 revenue 166.4m; issuer Q1 2026 revenue is 184.9m. '
         'All forecasts quarantined pending ownership and period-consistency review. No analyst or consensus provider is inferred.')
manifest(key, '2026-06-05', 'Kasikorn Securities', '', 'quarantined_forecast_attribution_and_source_period_conflict', notes, '2026-06-03')
for year, ev, rv in [(2026, '3.79', '920.61'), (2027, '5.62', '1206.57')]:
    for metric, value, basis in [('eps', ev, 'eps_forecast_attribution_unresolved'), ('revenue', rv, 'total_revenue')]:
        observation(key, '2026-06-05', 'Kasikorn Securities', '', 'publisher_forecast_unattributed', year, value, metric, basis, notes,
                    page='infographic annual actual and estimated table', status='quarantined_forecast_attribution_and_source_period_conflict', model='2026-06-03')

manifest('kasikorn_besi_20260605', '2026-06-05', 'Kasikorn Securities', '', 'context_for_quarantined_original_infographic', notes)
manifest('besi_coverage', '', 'BE Semiconductor Industries', '', 'reviewed_coverage_directory_no_forecast_table',
         'Issuer research-coverage directory lists covering analysts, but supplies no dated annual EPS consensus table. No forecasts extracted.')
manifest('hana_packaging_20221220', '2022-12-20', 'Hana Securities', '', 'reviewed_no_usable_besi_annual_eps_model',
         'Original sector report contains BESI peer/index material, but no direct comparable annual EPS table was recovered. No EPS inferred from PE.')

for filename, fields, rows in [('manifest.csv', MANIFEST_FIELDS, manifests), ('observations.csv', OBS_FIELDS, observations)]:
    with (HERE / filename).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
summary = {
    'original_artifacts': len(manifests), 'observations': len(observations),
    'non_quarantined_observations': sum('quarantin' not in row['status'] for row in observations),
    'non_quarantined_eps': sum(row['metric'] == 'eps' and 'quarantin' not in row['status'] for row in observations),
    'quarantined_observations': sum('quarantin' in row['status'] for row in observations),
    'latest_usable_report': max(row['report_date'] for row in observations if row['metric'] == 'eps' and 'quarantin' not in row['status']),
}
(HERE / 'extraction_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
