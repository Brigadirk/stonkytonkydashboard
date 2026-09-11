"""Reproduce this round's manually reviewed observations; no network calls."""
import csv
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent

with (BASE / 'manifest.csv').open() as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    manifest = list(reader)

for source in manifest:
    name = Path(source['local_file']).name
    if name == 'itau_nvidia_20231121.pdf':
        source.update(analyst_name='Thiago Alves Kapulskis; Gabriela Moraes; Cristian Faria', report_date='2023-11-21', report_timestamp='2023-11-21', report_month='2023-11', report_date_precision='day', artifact_type='original_pdf', status='downloaded_reviewed', notes='Named Tech Team on p1 and certification list on p5. P3 labels 2023/2024/2025 conflict with fiscal-year narrative on p1; preserve labels and quarantine table observations. Old rows are retrospective prior estimates with no independently dated earlier vintage. PDF creation timestamp is not original dissemination.')
    elif name == 'phillip_alphabet_20231027.html':
        source.update(analyst_name='Jonathan Woo', report_date='2023-10-27', report_timestamp='2023-10-27', report_month='2023-10', report_date_precision='day', artifact_type='original_html', status='downloaded_reviewed', notes='Author box identifies Jonathan Woo. Public article contains own Q4 2023 total-revenue growth forecast. Full PDF requires login; no login attempted. Original public availability not independently established.')
    elif name == 'phillip_nvidia_20230321.html':
        source.update(analyst_name='Maximilian Koeswoyo', report_timestamp='2023-03-21', status='downloaded_reviewed', notes='Author box identifies Maximilian Koeswoyo. Public initiation article contains own FY24 revenue forecast. Full PDF requires login; no login attempted. Original public availability not independently established.')
    elif name == 'x2_asml_20230426.pdf':
        source.update(status='downloaded_reviewed_date_caveat', notes='Public ASML sample linked by publisher homepage; signed download URL preserved. Printed date 26 April 2023, but PDF CreationDate/ModDate both 2 December 2023 14:39:02 UTC. April original availability and model immutability are not established. P7 base case kept separate from consensus and high/low scenarios. Author named on p1. Website author biography confirms firm relationship.')
    elif not source['local_file']:
        source['notes'] += '; Indexed report filename suggests 29 May 2023, but first page not retrieved, so report_date stays blank. Related publisher pages require login for full PDFs; no bypass attempted.'
with (BASE / 'manifest.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(manifest)

sources = {Path(row['local_file']).stem: row for row in manifest if row['local_file']}
observation_fields = ['observation_id','company_id','firm','analyst_name','metric','fiscal_period','value','currency','unit','basis','model_date','forecast_revision_as_of','report_date','available_at','printed_report_timestamp','original_available_at','availability_basis','source_url','local_file','page','status','notes','forecast_type','source_period_label','source_artifact_sha256']
observations = []

def add(key, metric, period, value, currency, unit, basis, page, status, notes, forecast_type='analyst_forecast', source_period_label='', analyst_name=None):
    source = sources[key]
    row = dict.fromkeys(observation_fields, '')
    row.update(company_id=source['company_ids'], firm=source['firm'], analyst_name=source['analyst_name'] if analyst_name is None else analyst_name, metric=metric, fiscal_period=period, value=str(value), currency=currency, unit=unit, basis=basis, report_date=source['report_date'], printed_report_timestamp=source['report_timestamp'], availability_basis='printed_report_date_not_independently_verified', source_url=source['source_url'], local_file=source['local_file'], page=str(page), status=status, notes=notes, forecast_type=forecast_type, source_period_label=source_period_label or period, source_artifact_sha256=source['sha256'])
    row['observation_id'] = hashlib.sha256('|'.join(str(row[x]) for x in ['company_id','firm','analyst_name','metric','fiscal_period','value','source_url','page','forecast_type']).encode()).hexdigest()[:18]
    observations.append(row)

key = 'phillip_nvidia_20230321'
add(key, 'revenue', 'FY2024', 29, 'USD', 'USD_billion', 'total_revenue', '', 'extracted_public_html_unscored', 'Public Revenue Growth paragraph explicitly forecasts FY24e revenue of USD29bn (rounded). Publication date from article header; separate model date and original dissemination not established.', source_period_label='FY24e')

key = 'phillip_alphabet_20231027'
add(key, 'revenue_growth_yoy', 'Q4FY2023', 13, '', 'percent', 'total_revenue_growth_yoy', '', 'extracted_public_html_unscored', 'Own forecast in The Positives / Rebound in Search and YouTube ad revenue paragraph. Growth percentage is not a revenue level and cannot be used as forward earnings. No annual total inferred from rounded forecast-completion percentages.', source_period_label='4Q23e')

key = 'itau_nvidia_20231121'
add(key, 'eps', 'FY2026', 20, 'USD', 'USD_per_share', 'EPS_accounting_basis_unresolved_pre_2024_stock_split', 1, 'extracted_narrative_unscored_basis_pending', 'Page1 explicitly says new FY26E EPS USD20, rounded. Same underlying final-year forecast appears as EPS20.12 under table header 2025 on p3; do not treat these as independent forecasts. Named team attribution, not individual accuracy. Units retained as printed before the 2024 split.', source_period_label='FY26E')
for metric, values, unit, basis in [('revenue', [58897,94547,113860], 'USD_million','net_revenue'), ('eps',[11.21,17.82,20.12],'USD_per_share','EPS_accounting_basis_unresolved_pre_2024_stock_split')]:
    for year,value in zip([2023,2024,2025],values):
        add(key, metric, 'UNRESOLVED_SOURCE_YEAR_'+str(year), value, 'USD',unit,basis,3,'quarantine_fiscal_period_mapping','Visually checked p3 New row. Printed headers 2023/2024/2025 do not match the FY24/FY25/FY26 narrative on p1; retain source label and withhold canonical fiscal mapping. Old estimates not ingested as earlier vintage. All share values kept as printed before 2024 split.',source_period_label=str(year))

key = 'x2_asml_20230426'
date_note = 'Printed report date 26 April 2023; PDF metadata creation/modification 2 December 2023. No proof of original April availability or model immutability; do not backdate this retrieved sample for backtesting. P7 visually checked, base-case table; company high/low scenarios excluded.'
for metric, values, unit, basis in [('revenue',[26784,30534,35419,39315,43247,47139,49967,52390],'EUR_million','total_revenue_base_case'),('eps',[18.98,23.81,30.46,34.00,37.69,41.87,45.18,48.57],'EUR_per_share','diluted_EPS_model_accounting_basis_pending_base_case')]:
    for year,value in zip(range(2023,2031),values):
        add(key,metric,'FY'+str(year),value,'EUR',unit,basis,7,'quarantine_recreated_pdf_availability',date_note,source_period_label=str(year))
for metric, values, unit, basis in [('revenue',[26471,29848,34895],'EUR_million','reported_consensus_total_revenue'),('eps',[18.80,22.95,29.56],'EUR_per_share','reported_consensus_EPS_basis_unresolved')]:
    for year,value in zip(range(2023,2026),values):
        add(key,metric,'FY'+str(year),value,'EUR',unit,basis,7,'quarantine_recreated_pdf_consensus_source',date_note+' Consensus provider and individual contributors unspecified; these are not Tim Green forecasts.','consensus_reported_by_analyst',str(year),analyst_name='')

with (BASE / 'observations.csv').open('w') as f:
    writer = csv.DictWriter(f,fieldnames=observation_fields)
    writer.writeheader()
    writer.writerows(observations)

metadata = {}
for name, source in sources.items():
    if source['artifact_type'] == 'original_pdf':
        reader = PdfReader(ROOT / source['local_file'])
        metadata[name] = {'page_count':len(reader.pages),'pdf_metadata':dict(reader.metadata),'warning':'PDF metadata is not independent publication or availability evidence.'}
(BASE / 'pdf_metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n')

coverage = []
for company in ['broadcom','alphabet','nvidia','micron','asml','sandisk']:
    for year in [2021,2022,2023]:
        reports = [r for r in manifest if r['company_ids']==company and r['local_file'] and r['report_date'].startswith(str(year))]
        rows = [r for r in observations if r['company_id']==company and r['report_date'].startswith(str(year))]
        coverage.append(dict(company_id=company,report_year=year,original_reports=len(reports),raw_observations=len(rows),analyst_forecast_rows=sum(r['forecast_type']=='analyst_forecast' for r in rows),consensus_rows=sum(r['forecast_type']!='analyst_forecast' for r in rows),scored_rows=0,notes='Printed report dates only; ASML PDF recreated in Dec2023. Alphabet only revenue growth. No 2021/2022 report obtained.'))
with (BASE / 'coverage_by_company_year.csv').open('w') as f:
    writer = csv.DictWriter(f,fieldnames=list(coverage[0]));writer.writeheader();writer.writerows(coverage)

for source in manifest:
    if source['local_file']:
        assert hashlib.sha256((ROOT / source['local_file']).read_bytes()).hexdigest()==source['sha256']
        assert (ROOT / source['text_file']).exists()
for row in observations:
    assert not row['available_at'] and not row['original_available_at']
    assert row['report_date'] <= '2026-09-10'
assert len(set(row['observation_id'] for row in observations))==len(observations)
print(json.dumps({'original_reports':len(sources),'observations':len(observations),'analyst_forecast_rows':sum(r['forecast_type']=='analyst_forecast' for r in observations),'consensus_rows':sum(r['forecast_type']!='analyst_forecast' for r in observations),'scored_rows':0,'verified_hashes':len(sources)}))
