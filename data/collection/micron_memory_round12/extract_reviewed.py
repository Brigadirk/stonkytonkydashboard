#!/usr/bin/env python3
"""Reproduce four visually reviewed original models; exclude reprints and actuals."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
retrievals = json.loads((BASE / 'retrieval.json').read_text())
sources = {r['url_date']: r for r in retrievals if r.get('local_file')}
# Each vector is an exact row in the retained physical page, under Forecast/Estimates.
REVIEWED = {
    '20230815': dict(page=14, model='2023-06-28', years=[2023, 2024, 2025],
                     revenue=['15429', '19333', '26474'], legacy=['-4.55', '1.83', '4.47']),
    '20250811': dict(page=13, model='2025-08-11', years=list(range(2025, 2030)),
                     revenue=['37301', '44482', '47570', '47674', '50350'],
                     reported=['7.39', '9.56', '9.67', '8.76', '10.06'],
                     adjusted=['8.05', '10.25', '10.48', '9.59', '10.94']),
    '20251219': dict(page=13, model='2025-12-17', years=list(range(2026, 2031)),
                     revenue=['77467', '98573', '99496', '71329', '72325'],
                     reported=['33.68', '45.67', '42.58', '17.66', '17.33'],
                     adjusted=['34.37', '46.66', '44.01', '19.61', '19.46']),
    '20260312': dict(page=13, model='2026-03-12', years=list(range(2026, 2031)),
                     revenue=['82851', '116185', '112014', '77875', '78356'],
                     reported=['36.48', '56.09', '47.14', '18.65', '20.40'],
                     adjusted=['37.00', '56.93', '48.39', '20.57', '22.48']),
}
labels = {
    'revenue': ('Revenue (USD Mil)', 'revenue', 'total_revenue', 'USD_million'),
    'legacy': ('Diluted Earnings Per Share(USD)', 'eps_diluted', 'diluted_adjustment_basis_unresolved', 'USD_per_share'),
    'reported': ('Earnings Per Share (Diluted) (USD)', 'eps_diluted', 'reported_diluted', 'USD_per_share'),
    'adjusted': ('Adjusted Earnings Per Share (Diluted) (USD)', 'eps_adjusted_diluted', 'adjusted_diluted', 'USD_per_share'),
}
rows, manifests, evidence = [], [], []
for key, source in sources.items():
    pdf = ROOT / source['local_file']
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source['sha256']
    text = (ROOT / source['text_file']).read_text()
    printed = re.search(r'Report as of (\d{1,2} \w{3} \d{4} \d{2}:\d{2}), UTC', text)[1]
    stamp = datetime.strptime(printed, '%d %b %Y %H:%M').isoformat() + '+00:00'
    spec = REVIEWED.get(key)
    note = ('Original Morningstar report distributed publicly by Firstrade. Printed availability is an assumption, '
            'not independently proven historical dissemination. Reprints do not refresh model age. ')
    if spec:
        page = text.split('\f')[spec['page'] - 1]
        model_label = datetime.strptime(spec['model'], '%Y-%m-%d').strftime('%d %b %Y')
        assert 'as of ' + model_label in page
        assert 'William Kerwin' in text and 'Micron Technology' in page
        note += ('Model date taken from the annual forecast table, never the URL or article date. '
                 'Exact fiscal-year labels retained; issuer August fiscal calendar used. '
                 'Only forward annual columns imported. Source page visually reviewed. ')
        if 'legacy' in spec:
            note += ('Legacy diluted EPS adjustment basis remains unresolved and separate from modern reported/adjusted series. '
                     'June28 model first retained in August15 report; no backdating to June. ')
        if key == '20251219':
            note += ('December18 report still prints September23 model. Updated December17 model first retained in '
                     'December20 00:33 UTC report, so the forecast is unavailable before that report. ')
        for kind, (label, metric, basis, unit) in labels.items():
            if kind not in spec:
                continue
            line = next(l.strip() for l in page.splitlines() if l.strip().startswith(label))
            numbers = re.findall(r'-?\d+(?:\.\d+)?', line[len(label):].replace(',', ''))
            if 'legacy' in spec:
                numbers = numbers[:5]  # Five left-hand fiscal columns; right panel is valuation ratios.
            assert numbers[-len(spec['years']):] == spec[kind], (key, kind, numbers)
            evidence.append(dict(source_url=source['source_url'], source_sha256=source['sha256'],
                                 physical_page=spec['page'], model_date=spec['model'], printed_report_timestamp=stamp,
                                 row_label=label, row_text=line, fiscal_years=spec['years'], values=spec[kind]))
            for year, value in zip(spec['years'], spec[kind]):
                rows.append(dict(
                    observation_id=hashlib.sha256(f'{source["sha256"]}|{metric}|FY{year}|{value}'.encode()).hexdigest()[:24],
                    company_id='micron', firm='Morningstar', analyst_name='William Kerwin',
                    source_type='individual_analyst_forecast', forecast_type='analyst_forecast',
                    metric=metric, fiscal_period=f'FY{year}', value=value, currency='USD', unit=unit, basis=basis,
                    model_date=spec['model'], report_date=stamp[:10], printed_report_timestamp=stamp,
                    original_available_at='', available_at='', share_basis_date=spec['model'],
                    availability_basis='printed_report_timestamp_not_independently_verified',
                    source_url=source['source_url'], local_file=source['local_file'], page=spec['page'],
                    status='extracted_original_table_unscored', notes=note,
                    source_period_label=f'{year} Forecast', source_artifact_sha256=source['sha256']))
        status = 'downloaded_forecast_tables_verified'
    else:
        status = 'retained_not_imported'
        note += ('No new observations admitted: table absent or existing-model/reprint candidate. '
                 'Retained for extraction audit; raw retrieval log records failed public routes too.')
    manifests.append(dict(source_url=source['source_url'], local_file=source['local_file'],
                          company_ids='micron', firm='Morningstar', analyst_name='William Kerwin' if spec else '',
                          report_date=stamp[:10], retrieved_at=source['retrieved_at'], sha256=source['sha256'],
                          text_file=source['text_file'], report_timestamp=stamp, model_dates=spec['model'] if spec else '',
                          report_date_precision='minute', artifact_type='pdf', http_status=source['http_status'],
                          status=status, notes=note))

for filename, data in [('observations.csv', rows), ('manifest.csv', manifests)]:
    with (BASE / filename).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
(BASE / 'extraction_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
validation = dict(requests=len(retrievals), retained_pdfs=len(sources), reviewed_models=len(REVIEWED),
                  observations=len(rows), eps_observations=sum(r['metric'].startswith('eps') for r in rows),
                  default_adjusted_models_added=3, unresolved_basis_models_added=1,
                  no_reprint_observations=True, numerical_claims_checked_against_original_row=True)
(BASE / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation))
