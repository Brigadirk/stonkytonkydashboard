"""Check retained artifacts and independently reparse Morningstar forecast columns."""
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

BASE = Path('data/collection/asml_sandisk_round4')
manifest = list(csv.DictReader((BASE / 'manifest.csv').open()))
rows = list(csv.DictReader((BASE / 'observations.csv').open()))
by_file = {r['local_file']: r for r in manifest if r['local_file']}
assert len({r['observation_id'] for r in rows}) == len(rows)
for source in by_file.values():
    assert hashlib.sha256(Path(source['local_file']).read_bytes()).hexdigest() == source['sha256']
for row in rows:
    source = by_file[row['local_file']]
    assert row['source_artifact_sha256'] == source['sha256']
    assert row['source_url'] == source['source_url']
    if 'consensus' in row['source_type']:
        assert not row['analyst_name']
    if row['availability_basis'] != 'current_snapshot_retrieved_at':
        assert not row['original_available_at']
    if row['firm'] != 'Morningstar':
        continue
    page = Path(source['text_file']).read_text().split('\f')[int(row['page']) - 1]
    prefix = {
        'revenue': 'Revenue (USD Mil)',
        'eps_diluted': 'Earnings Per Share (Diluted) (USD)',
        'eps_adjusted_diluted': 'Adjusted Earnings Per Share (Diluted) (USD)',
    }[row['metric']]
    line = next(line.strip() for line in page.splitlines() if line.strip().startswith(prefix))
    values = re.findall(r'-?\d[\d,]*\.?\d*', line[len(prefix):])[-5:]
    years_line = next(line for line in page.splitlines() if line.strip().startswith('Fiscal Year,'))
    years = re.findall(r'20\d\d', years_line)[-5:]
    value = values[years.index(row['fiscal_period'][2:])]
    assert Decimal(value.replace(',', '')) == Decimal(row['value']), row
    assert row['model_date'] <= row['report_date']
    assert row['analyst_name'] == 'William Kerwin'

eligible = [r for r in rows if not r['status'].startswith('quarantined')]
result = dict(
    retained_pdfs=len(by_file),
    manifest_records=len(manifest),
    observations=len(rows),
    nonquarantined_observations=len(eligible),
    nonquarantined_by_metric=dict(Counter(r['metric'] for r in eligible)),
    nonquarantined_by_company=dict(Counter(r['company_id'] for r in eligible)),
    quarantined=len(rows)-len(eligible),
    validation='all artifact hashes, row provenance, attribution and Morningstar annual columns passed',
)
(BASE / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
