#!/usr/bin/env python3
"""Verify retained public BESI captures and rebuild this collection offline."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OBS_FIELDS = 'observation_id,company_id,firm,analyst_name,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,forecast_type,source_type,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MANIFEST_FIELDS = 'source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,http_status,artifact_type'.split(',')
sources = json.loads((BASE / 'download_log.json').read_text())
reviews = json.loads((BASE / 'reviews.json').read_text())
manifest = []
for source in sources:
    if 'local_file' not in source:
        continue
    path = ROOT / source['local_file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], path
    review = reviews[source['name']]
    row = {key: source.get(key, '') for key in MANIFEST_FIELDS}
    row.update(company_ids='besi', artifact_type=path.suffix.lstrip('.'), **review)
    if path.suffix == '.pdf':
        text_path = BASE / 'text' / (path.stem + '.txt')
        subprocess.run(['pdftotext', '-layout', str(path), str(text_path)], check=True)
        row['text_file'] = str(text_path.relative_to(ROOT))
    manifest.append(row)

source = next(s for s in sources if s['name'] == 'dividendinfo_besi')
soup = BeautifulSoup((ROOT / source['local_file']).read_bytes(), 'html.parser')
plain = soup.get_text(' ', strip=True)
assert 'dividendinfo.nl gaat voorlopig uit van een winst per aandeel van 3,85 euro per aandeel' in plain
table = next(t for t in soup.find_all('table') if '2028' in t.get_text())
assert 'WINST PER AANDEEL' in table.get_text() and 'PAYOUT RATIO' in table.get_text()
expected = {'2026': ('3.85', '€ 3,85 TAX'), '2027': ('5.00', '€ 5,00 TAX'), '2028': ('5.80', '€ 5,80 TAX')}
actual = {}
for tr in table.find_all('tr'):
    cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
    if cells and cells[0] in expected:
        assert cells[1] == expected[cells[0]][1], cells
        actual[cells[0]] = cells
assert set(actual) == set(expected)

notes = ('Public Dividendinfo editorial forecast: the source explicitly says dividendinfo.nl makes the EPS assumption, '
         'then points to this annual EPS/dividend table. Not an identified individual analyst and not labelled consensus. '
         'No named author found on the retained page, FAQ, contact or disclaimer. Keep the publisher source type; '
         'do not invent a person or count as a named analyst. EPS adjustment and basic/diluted denominator remain unspecified. '
         'report_date is first-observed capture date, not a verified publication/model date. Old dated news paragraphs '
         'do not date this mutable forecast table. No historical use before the capture; current engine rejects '
         'this unsupported publisher forecast type, and even a supported capture would be daily-eligible no earlier '
         'than 11 September 2026. No earlier forecasts or reference-window coverage are reconstructed.')
rows = []
for year, (value, label) in expected.items():
    row = {key: '' for key in OBS_FIELDS}
    row.update(observation_id=hashlib.sha256(f"{source['sha256']}|besi|eps|{year}|{value}".encode()).hexdigest()[:24],
               company_id='besi', firm='Dividendinfo.nl', metric='eps', fiscal_period='FY'+year, value=value,
               currency='EUR', unit='EUR_per_share', basis='dividendinfo_eps_adjustment_and_dilution_unspecified',
               report_date=source['retrieved_at'][:10], available_at=source['retrieved_at'],
               availability_basis='first_observed_public_snapshot_model_revision_unknown',
               source_url=source['source_url'], local_file=source['local_file'], page='HTML: TAXATIE WPA & DIVIDEND, annual table',
               status='extracted_original_table_unscored', notes=notes, forecast_type='publisher_forecast',
               source_type='publisher_forecast_unattributed', source_period_label=year+' TAX',
               source_artifact_sha256=source['sha256'])
    rows.append(row)

for filename, fields, values in [('observations.csv', OBS_FIELDS, rows), ('manifest.csv', MANIFEST_FIELDS, manifest)]:
    with (BASE / filename).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(values)

(BASE / 'evidence/dividendinfo_table.html').write_text('<!doctype html><meta charset="utf-8"><title>Retained Dividendinfo BESI table</title><style>body{font:18px sans-serif;padding:30px}table{border-collapse:collapse}td,th{padding:10px 20px;border:1px solid #bbb}</style><h1>Retained Dividendinfo BESI table</h1><p>Source captured '+source['retrieved_at']+'</p>'+str(table))
evidence = {'source_sha256': source['sha256'], 'first_observed_at': source['retrieved_at'], 'model_date': None,
            'forecast_owner': 'Dividendinfo.nl', 'analyst_name': None, 'currency': 'EUR',
            'eps': {'FY'+year: value[0] for year, value in expected.items()}, 'source_rows': actual,
            'compatibility_alias': None, 'historical_coverage_added': 0, 'app_eligible_added': 0,
            'app_exclusion_reason': 'unsupported_forecast_type', 'named_analyst_refresh_succeeded': False,
            'evidence_render': 'evidence/dividendinfo_table.png', 'render_is_from_retained_html': True}
(BASE / 'evidence/extraction.json').write_text(json.dumps(evidence, indent=2)+'\n')
validation = {'sources_verified': len(manifest), 'extracted_publisher_eps_observations': len(rows),
              'new_named_analyst_models': 0, 'new_compatible_ensemble_members': 0,
              'new_price_band_eligible_forecasts': 0, 'prior_collections_modified': False,
              'paid_access_used': False, 'shared_refresh_run': False}
(BASE / 'validation.json').write_text(json.dumps(validation, indent=2)+'\n')
print(json.dumps(validation))
