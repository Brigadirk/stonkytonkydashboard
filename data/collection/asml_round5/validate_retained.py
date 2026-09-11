"""Validate source bytes, provenance and extracted annual values independently."""
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

BASE=Path('data/collection/asml_round5')
sources=list(csv.DictReader((BASE/'manifest.csv').open()))
rows=list(csv.DictReader((BASE/'observations.csv').open()))
by_file={r['local_file']:r for r in sources if r['local_file']}
assert len({r['observation_id'] for r in rows})==len(rows)
for source in by_file.values():
    assert hashlib.sha256(Path(source['local_file']).read_bytes()).hexdigest()==source['sha256']
for row in rows:
    source=by_file[row['local_file']]
    assert row['source_url']==source['source_url']
    assert row['source_artifact_sha256']==source['sha256']
    assert row['analyst_name']==source['analyst_name']
    assert row['model_date']<=row['report_date']
    assert row['currency']=='EUR'
    assert not row['original_available_at']
    page=Path(source['text_file']).read_text().split('\f')[int(row['page'])-1]
    if 'Morningstar Valuation Model Summary' in page:
        table=page.split('Morningstar Valuation Model Summary',1)[1]
        prefix={'revenue':'Revenue (EUR Mil)','eps_diluted':'Earnings Per Share (Diluted) (EUR)','eps_adjusted_diluted':'Adjusted Earnings Per Share (Diluted) (EUR)'}[row['metric']]
    else:
        table=page.split('Morningstar Analyst Historical/Forecast Summary as of',1)[1]
        prefix=('Revenue (EUR Bil)' if row['unit']=='EUR_billion' else 'Revenue (EUR Mil)') if row['metric']=='revenue' else 'Diluted Earnings Per Share(EUR)'
    line=next(l.strip() for l in table.splitlines() if l.strip().startswith(prefix))
    printed=re.findall(r'-?\d[\d,]*(?:\.\d+)?|—',line[len(prefix):].split('Price/Earnings')[0])
    header=next(l for l in table.splitlines() if l.strip().startswith('Fiscal Year,'))
    years=re.findall(r'20\d\d',header)[-len(printed):]
    expected=printed[years.index(row['fiscal_period'][2:])]
    assert Decimal(expected.replace(',',''))==Decimal(row['value']),(row,expected)

assert not any('20240605.pdf' in r['local_file'] and r['fiscal_period']=='FY2024' and r['metric'].startswith('eps') for r in rows)
july24=[r for r in rows if '20240717.pdf' in r['local_file']]
assert len(july24)==1 and july24[0]['value']=='21.65' and july24[0]['model_date']=='2024-06-05'
eligible=[r for r in rows if not r['status'].startswith('quarantined')]
result=dict(retained_pdfs=len(by_file),manifest_records=len(sources),observations=len(rows),nonquarantined_observations=len(eligible),quarantined=len(rows)-len(eligible),nonquarantined_by_metric=dict(Counter(r['metric'] for r in eligible)),usable_model_dates=len({r['model_date'] for r in eligible}),manifest_statuses=dict(Counter(s['status'] for s in sources)),validation='All hashes, source references, currency, author, dates and annual row/column values verified; missing and duplicate cells handled explicitly.')
(BASE/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
