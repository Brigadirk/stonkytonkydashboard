#!/usr/bin/env python3
"""Extract reviewed U.S. consensus tables from the retained Hana 2026 guide."""
import csv
import hashlib
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
with (ROOT/'data/collection/asml_sandisk_round4/downloaded_sources.csv').open() as f:
    source=next(r for r in csv.DictReader(f) if r['key']=='hana_global_20260109')
assert hashlib.sha256((ROOT/source['local_file']).read_bytes()).hexdigest()==source['sha256']
pages=(ROOT/source['text_file']).read_text().split('\f')
with (ROOT/'data/collection/us_asml/manifest.csv').open() as f:
    manifest_fields=csv.DictReader(f).fieldnames
manifest={k:'' for k in manifest_fields}
manifest.update({k:source[k] for k in ['source_url','local_file','text_file','sha256','retrieved_at','http_status']})
manifest.update(company_ids='nvidia;broadcom;micron;alphabet',firm='Hana Securities (Bloomberg consensus)',report_date='2026-01-12',status='downloaded_tables_reviewed',notes='Reused original 2026 US stock guide. Printed cover date is January12; filename January09 is not publication evidence. Physical pages53/57/71 are explicit Bloomberg market consensus; Alphabet page145 is quarantined for inconsistent company metadata and fiscal headers.',report_month='2026-01',report_date_precision='day',artifact_type='pdf')
with (OUT/'manifest.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=manifest_fields);w.writeheader();w.writerow(manifest)
with (ROOT/'data/collection/us_asml/observations.csv').open() as f:
    fields=csv.DictReader(f).fieldnames+['source_type','forecast_type']
rows=[]
targets=[('nvidia',53,[2026,2027],['4.68','7.71'],['213,293','327,047'],False),('broadcom',57,[2026,2027],['9.86','13.86'],['95,260','130,431'],False),('micron',71,[2026,2027],['30.33','38.45'],['71,016','88,320'],False),('alphabet',145,[2025,2026],['10.91','11.84'],['340,481','389,433'],True)]
for company,page,years,eps,revenue,quarantine in targets:
    text=pages[page-1]
    assert 'Bloomberg 시장 컨센서스' in text
    eps_line=next(line for line in text.splitlines() if line.strip().startswith('EPS(USD)'))
    rev_line=next(line for line in text.splitlines() if line.strip().startswith('매출 '))
    assert re.findall(r'-?\d[\d,]*(?:\.\d+)?',eps_line)[-2:]==eps
    assert re.findall(r'-?\d[\d,]*(?:\.\d+)?',rev_line)[:4][-2:]==revenue
    for metric,values,unit,basis in [('eps',eps,'USD_per_share','Bloomberg_EPS_adjustment_unstated'),('revenue',revenue,'USD_million','Bloomberg_consensus_revenue')]:
        for year,value in zip(years,values):
            row={k:'' for k in fields}
            row.update(observation_id=hashlib.sha256(f'{company}-{page}-{metric}-{year}-{value}'.encode()).hexdigest()[:20],company_id=company,firm=manifest['firm'],metric=metric,fiscal_period=f'FY{year}',value=value.replace(',',''),currency='USD',unit=unit,basis=basis,report_date='2026-01-12',availability_basis='printed_report_date_assumption',source_url=source['source_url'],local_file=source['local_file'],page=str(page),status='quarantined_inconsistent_company_metadata_and_fiscal_headers' if quarantine else 'original_table_checked_unscored',source_type='report_embedded_consensus',forecast_type='consensus_reported_by_analyst',notes='Explicit Bloomberg market consensus, published by Hana Securities. EPS adjustment and dilution are not specified, so this remains a separate basis from explicitly adjusted EPS. The printed guide cover is dated12January2026; exact original availability unverified. No analyst attributed. '+('Alphabet page mixes Amazon key-data and questionable fiscal-header values; retained for review only.' if quarantine else 'Only columns explicitly marked (E) extracted.'))
            rows.append(row)
with (OUT/'observations.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print(f'Saved {len(rows)} source observations:12 reviewed,4 quarantined;6 usable EPS values.')
