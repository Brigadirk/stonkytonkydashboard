"""Extract reviewed ASML annual models from retained original Morningstar PDFs."""
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path('data/collection/asml_round5')
sources = []
for path in sorted(BASE.glob('discovery_round*.json')):
    sources.extend(json.loads(path.read_text()))

NUMBER = re.compile(r'(?<!\w)(?:-?\d[\d,]*(?:\.\d+)?|—)(?!\w)')
ROWS = []
MANIFEST = []
SEEN = set()
MODELS = []

def parse_date(value):
    return datetime.strptime(value.strip(), '%d %b %Y').date().isoformat()

def values_after(line, prefix, count):
    body = line.strip()[len(prefix):].split('Price/Earnings')[0]
    values = NUMBER.findall(body)
    assert len(values) == count, (prefix, line, values)
    return [v.replace(',', '') for v in values]

for source in sorted(sources, key=lambda x: x['key']):
    key = source['key']
    common = dict(source_url=source['source_url'], local_file=source.get('local_file',''), company_ids='asml', firm='Morningstar', analyst_name='', report_date='', retrieved_at=source.get('retrieved_at',''), sha256=source.get('sha256',''), status='download_failed', notes='', text_file=source.get('text_file',''), report_timestamp='', model_dates='', http_status=str(source.get('http_status','')), report_month='', report_date_precision='unknown', artifact_type='unavailable')
    if not source.get('local_file'):
        common['notes'] = source.get('error') or 'Known publisher/earnings-date archive probe returned no original PDF.'
        MANIFEST.append(common)
        continue
    text = Path(source['text_file']).read_text()
    stamp_text = re.search(r'Report as of (\d+ \w+ \d{4} \d\d:\d\d), UTC', text).group(1)
    stamp = datetime.strptime(stamp_text, '%d %b %Y %H:%M').isoformat()+'+00:00'
    report_day = stamp[:10]
    assert 'Reporting Currency: EUR' in text.splitlines()[0]
    assert 'ASML Holding NV ADR' in text[:4000]
    names = [n for n in ['Abhinav Davuluri','William Kerwin','Javier Correonero'] if n in text[:16000]]
    assert len(names) == 1, (key,names)
    name = names[0]
    common.update(analyst_name=name,report_date=report_day,report_timestamp=stamp,report_month=report_day[:7],report_date_precision='minute',artifact_type='pdf')
    model = None
    for page_number, page in enumerate(text.split('\f'),1):
        modern = 'Morningstar Valuation Model Summary' in page
        marker = 'Morningstar Analyst Historical/Forecast Summary as of'
        if modern:
            table = page.split('Morningstar Valuation Model Summary',1)[1]
            model_day = parse_date(re.search(r'Financials as of (\d+ \w+ \d{4})',table).group(1))
            forecast_count=5
            years_line=next(l for l in table.splitlines() if l.strip().startswith('Fiscal Year,'))
            years=re.findall(r'20\d\d',years_line)[-8:]
            assert len(years)==8,(key,years_line)
            metrics=[('revenue','Revenue (EUR Mil)','total_revenue','EUR_million'),('eps_diluted','Earnings Per Share (Diluted) (EUR)','reported_diluted','EUR_per_share'),('eps_adjusted_diluted','Adjusted Earnings Per Share (Diluted) (EUR)','adjusted_diluted','EUR_per_share')]
        elif marker in page:
            table=page.split(marker,1)[1]
            model_day=parse_date(table.splitlines()[0])
            forecast_count=3
            years_line=next(l for l in table.splitlines() if l.strip().startswith('Fiscal Year,'))
            years=re.findall(r'20\d\d',years_line)[-5:]
            assert len(years)==5,(key,years_line)
            revenue_line=next(l for l in table.splitlines() if l.strip().startswith('Revenue (EUR'))
            revenue_prefix=re.match(r'Revenue \(EUR (?:Bil|Mil)\)',revenue_line.strip()).group()
            unit='EUR_billion' if 'Bil' in revenue_prefix else 'EUR_million'
            metrics=[('revenue',revenue_prefix,'total_revenue',unit),('eps_diluted_basis_unresolved','Diluted Earnings Per Share(EUR)','diluted_adjustment_basis_unresolved','EUR_per_share')]
        else:
            continue
        model=dict(key=key,analyst=name,report_date=report_day,model_date=model_day,page=page_number,format='modern' if modern else 'legacy',period_header=years_line.strip(),years=years[-forecast_count:],metrics=[])
        for metric,prefix,basis,unit in metrics:
            line=next(l for l in table.splitlines() if l.strip().startswith(prefix))
            values=values_after(line,prefix,len(years))[-forecast_count:]
            model['metrics'].append(dict(metric=metric,basis=basis,unit=unit,values=values,original_line=line.strip()))
        break
    if model is None:
        common.update(status='downloaded_no_annual_model_table',notes='Original report retained; no annual analyst forecast summary or valuation-model summary found.')
        MANIFEST.append(common)
        continue
    assert model['model_date'] <= report_day,(key,model)
    MODELS.append(model)
    common['model_dates']=model['model_date']
    notes='Original Morningstar report distributed by Firstrade. Reporting/model currency EUR; USD trading currency is not used to translate forecasts. Annual December-ending ASML periods. Printed UTC report timestamp is not independently verified historical dissemination. Model date is the explicit financial-model date, not the commentary date.'
    if model['format']=='legacy':
        notes+=' Legacy summary labels diluted EPS but does not separately establish the adjustment basis; keep apart from reported/adjusted diluted series. Revenue retains printed precision and units.'
    if key=='morningstar_asml_20230125':
        notes+=' QUARANTINE: column years are shifted against historical rows: source labels2021/2022 for revenue13979/18611 and EPS8.48/14.34, actually2020/2021 figures. The model itself is datedOctober19,2022. Printed year labels are retained without silently correcting them.'
    if key=='morningstar_asml_20240605':
        notes+=' FY2024 diluted EPS is a printed dash; it is omitted, not inferred from P/E. July17 report later prints that value under the same June5 model date.'
    if key=='morningstar_asml_20240717':
        notes+=' Repeats June5 model; only the newly visible FY2024 EPS cell is extracted with this July17 report timestamp. It is not backdated into the June5 report.'
    start=len(ROWS)
    for metric in model['metrics']:
        for year,value in zip(model['years'],metric['values']):
            if value=='—':
                continue
            signature=(name,model['model_date'],metric['metric'],year,value,metric['unit'])
            if signature in SEEN:
                continue
            SEEN.add(signature)
            status='quarantined_fiscal_header_mismatch' if key=='morningstar_asml_20230125' else 'extracted_original_table_unscored'
            ROWS.append(dict(observation_id=hashlib.sha256(f'{key}|asml|{metric["metric"]}|{year}|{value}|{model["page"]}'.encode()).hexdigest()[:20],company_id='asml',firm='Morningstar',analyst_name=name,metric=metric['metric'],fiscal_period='FY'+year,value=value,currency='EUR',unit=metric['unit'],basis=metric['basis'],model_date=model['model_date'],forecast_revision_as_of=model['model_date'],report_date=report_day,available_at='',printed_report_timestamp=stamp,original_available_at='',availability_basis='printed_report_timestamp_not_independently_verified',source_url=source['source_url'],local_file=source['local_file'],page=model['page'],status=status,notes=notes,forecast_type='analyst_forecast',source_type='individual_analyst_forecast',source_period_label=year+(' Forecast' if model['format']=='modern' else ' Estimates'),source_artifact_sha256=source['sha256']))
    common.update(status='downloaded_forecast_tables_verified' if len(ROWS)>start else 'downloaded_reprint_not_reextracted',notes=notes)
    if key=='morningstar_asml_20230125':common['status']='downloaded_fiscal_header_mismatch_quarantined'
    if len(ROWS)==start: common['notes']+=' No new model observations; retained table repeats an earlier captured model.'
    MANIFEST.append(common)

with (BASE/'manifest.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(MANIFEST[0]));w.writeheader();w.writerows(MANIFEST)
with (BASE/'observations.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(ROWS[0]));w.writeheader();w.writerows(ROWS)
(BASE/'reviewed_models.json').write_text(json.dumps(MODELS,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(dict(manifest_records=len(MANIFEST),retained_pdfs=sum(bool(m['local_file']) for m in MANIFEST),observations=len(ROWS),quarantined=sum(r['status'].startswith('quarantined') for r in ROWS),models_with_new_observations=len(set(r['model_date'] for r in ROWS))),indent=2))
