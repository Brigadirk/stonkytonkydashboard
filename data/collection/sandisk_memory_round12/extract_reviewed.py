"""Reproduce Sandisk annual EPS/revenue transcriptions reviewed against original PDF pages."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
LOG = json.loads((BASE/'download_log.json').read_text())
SOURCES = {r['candidate_date']:r for r in LOG if r.get('local_file')}

MODELS = {
    '20250808': {
        'stamp':'2025-08-08T23:04:00+00:00', 'model_date':'2025-05-08', 'page':9,
        'years':[2025,2026,2027,2028,2029],
        'revenue':['7251','8152','8510','8536','8707'],
        'reported_diluted':['-11.61','3.56','4.53','3.63','4.20'],
        'adjusted_diluted':['2.74','5.11','6.22','5.41','6.14'],
        'notes': 'Original Morningstar Sandisk report distributed by Firstrade. Model revision explicitly dated 8 May 2025 on p10; p9 financials-as-of label says 7 May. July22 narrative revision is not a fresh numerical model. Availability is no earlier than retained August8 report, with existing next-session rules; no May historical backfill. Printed December fiscal-year header is the existing Sandisk template error: historical FY2022/23/24 revenue9754/6086/6663 and later August15 prior-model FY2026/27/28 EPS columns match the June-ending issuer years. Year numbers retained; issuer fiscal calendar supplies exact period ends. FY2025 ended June27 before this retained publication, so its printed forecast column is preserved only as quarantined extraction evidence. Only FY2026-29 are eligible forward observations.'
    },
    '20260806': {
        'stamp':'2026-08-06T07:08:00+00:00', 'model_date':'2026-08-06', 'page':11,
        'years':[2027,2028,2029,2030,2031],
        'revenue':['51719','68996','45050','27030','27570'],
        'reported_diluted':['230.38','318.06','179.01','71.56','69.22'],
        'adjusted_diluted':['231.68','319.77','181.06','73.98','72.00'],
        'notes': 'Original Morningstar Sandisk report distributed by Firstrade. Forecast Revisions explicitly dated 6 August2026 on p12 and Fair Value and Profit Drivers byline dated August6. P11 financials-as-of April30 is a stale header; p12 current/prior comparison confirms the August6 numerical revision. P11 separates actual FY2026 from forecastFY2027-31. Explicit USD reported diluted and adjusted diluted EPS rows remain separate. This vector differs from the August19 model already retained; August7/12 reprints are not additional models.'
    },
}
REPRINTS = {
    '20260707':('2026-07-07T23:00:00+00:00','2026-04-30',11),
    '20260709':('2026-07-09T23:23:00+00:00','2026-04-30',11),
    '20260728':('2026-07-28T22:59:00+00:00','2026-04-30',11),
    '20260804':('2026-08-04T23:02:00+00:00','2026-04-30',11),
    '20260807':('2026-08-07T23:08:00+00:00','2026-08-06',12),
    '20260812':('2026-08-12T23:22:00+00:00','2026-08-06',12),
}
LABELS = {'revenue':'Revenue (USD Mil)',
          'reported_diluted':'Earnings Per Share (Diluted) (USD)',
          'adjusted_diluted':'Adjusted Earnings Per Share (Diluted) (USD)'}

def page_values(source, page, label, count):
    text=(ROOT/source['text_file']).read_text().split('\f')[page-1]
    line=next(line.strip() for line in text.splitlines() if line.strip().startswith(label))
    values=re.findall(r'-?\d+(?:,\d{3})*(?:\.\d+)?',line[len(label):])
    return [v.replace(',','') for v in values[-count:]]

rows=[]
for key,model in MODELS.items():
    source=SOURCES[key]
    assert hashlib.sha256((ROOT/source['local_file']).read_bytes()).hexdigest()==source['sha256']
    text=(ROOT/source['text_file']).read_text()
    expected_stamp=__import__('datetime').datetime.fromisoformat(model['stamp']).strftime('%-d %b %Y %H:%M')
    assert f'Report as of {expected_stamp}, UTC' in text
    assert 'William Kerwin' in text
    for kind,label in LABELS.items():
        assert page_values(source,model['page'],label,5)==model[kind],(key,kind)
        metric={'revenue':'revenue','reported_diluted':'eps_diluted','adjusted_diluted':'eps_adjusted_diluted'}[kind]
        for year,value in zip(model['years'],model[kind]):
            completed_period = key == '20250808' and year == 2025
            status = 'quarantined_completed_fiscal_period_before_retained_publication' if completed_period else 'extracted_original_table_unscored'
            rows.append(dict(observation_id=hashlib.sha256(f'{key}|{metric}|{year}|{value}'.encode()).hexdigest()[:20],
                company_id='sandisk',firm='Morningstar',analyst_name='William Kerwin',metric=metric,
                fiscal_period=f'FY{year}',value=value,currency='USD',unit='USD_million' if kind=='revenue' else 'USD_per_share',
                basis='total_revenue' if kind=='revenue' else kind,model_date=model['model_date'],
                forecast_revision_as_of=model['model_date'],report_date=model['stamp'][:10],available_at='',
                printed_report_timestamp=model['stamp'],original_available_at='',
                availability_basis='printed_report_timestamp_not_independently_verified',source_url=source['source_url'],
                local_file=source['local_file'],page=model['page'],status=status,
                notes=model['notes']+' Original historical dissemination timestamp remains unverified.',
                forecast_type='analyst_forecast',source_type='individual_analyst_forecast',
                source_period_label=f'{year} Forecast',source_artifact_sha256=source['sha256']))

old={'revenue':['19735','45933','46461','24880','23885'],
     'reported_diluted':['69.87','201.80','192.58','71.35','63.90'],
     'adjusted_diluted':['72.22','203.19','194.38','73.34','65.88']}
for key,(stamp,model,page) in REPRINTS.items():
    source=SOURCES[key]
    text=(ROOT/source['text_file']).read_text()
    expected_stamp=__import__('datetime').datetime.fromisoformat(stamp).strftime('%-d %b %Y %H:%M')
    assert f'Report as of {expected_stamp}, UTC' in text,(key,text.splitlines()[0],expected_stamp)
    expected=old if model=='2026-04-30' else MODELS['20260806']
    for kind,label in LABELS.items():
        assert page_values(source,page,label,5)==expected[kind],(key,kind)

manifest=[]
for key,source in SOURCES.items():
    if key in MODELS:
        model=MODELS[key];stamp=model['stamp'];day=model['model_date'];notes=model['notes']
        status='downloaded_forecast_tables_verified'
    else:
        stamp,day,page=REPRINTS[key]
        notes=f'Exact complete annual EPS and revenue vectors repeat the {day} model. Retained for source audit; no observations extracted and model freshness is not advanced.'
        status='downloaded_reprint_not_reextracted'
    manifest.append(dict(source_url=source['source_url'],local_file=source['local_file'],company_ids='sandisk',
        firm='Morningstar',analyst_name='William Kerwin',report_date=stamp[:10],retrieved_at=source['retrieved_at'],
        sha256=source['sha256'],status=status,notes=notes,text_file=source['text_file'],report_timestamp=stamp,
        model_dates=day,http_status=source['http_status'],report_month=stamp[:7],report_date_precision='minute',artifact_type='pdf'))
with (BASE/'observations.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
with (BASE/'manifest.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(manifest[0]));writer.writeheader();writer.writerows(manifest)
eligible=[r for r in rows if not r['status'].startswith('quarantined_')]
quarantined=[r for r in rows if r['status'].startswith('quarantined_')]
assert len(quarantined)==3 and all(r['fiscal_period']=='FY2025' for r in quarantined)
validation=dict(original_pdfs=len(SOURCES),new_model_vectors=len(MODELS),reprints_excluded=len(REPRINTS),
                eligible_annual_eps=len([r for r in eligible if r['metric'].startswith('eps')]),
                eligible_revenue_rows=len([r for r in eligible if r['metric']=='revenue']),
                raw_observations=len(rows),quarantined_completed_period_rows=len(quarantined),complete_row_transcriptions_checked=True)
(BASE/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))
