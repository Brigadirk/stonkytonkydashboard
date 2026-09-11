"""Add reviewed, originally sourced daily closes where the base feed has a gap."""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def supplement(rows, rules, splits, cutoff, root=ROOT):
    result = {(r['company_id'], r['date']): dict(r) for r in rows}
    for rule in rules:
        if rule['date'] > cutoff:
            continue
        for evidence in [rule, *rule.get('supporting_evidence', [])]:
            if hashlib.sha256((root / evidence['source_file']).read_bytes()).hexdigest() != evidence['source_sha256']:
                raise ValueError('Price supplement source hash mismatch')
        content = (root / rule['source_file']).read_text()
        if rule['format'] == 'naver_daily':
            table = ast.literal_eval(content.strip())
            if table[0][4] != '종가':
                raise ValueError('Naver source is not the dated daily close field')
            extracted = [r[4] for r in table[1:] if r[0] == rule['date'].replace('-', '')]
        elif rule['format'] == 'euronext_daily':
            doc = BeautifulSoup(content, 'html.parser')
            day = '/'.join(reversed(rule['date'].split('-')))
            extracted = []
            for tr in doc.select('tr'):
                cells = [x.get_text(' ', strip=True) for x in tr.select('td')]
                if cells and cells[0] == day:
                    extracted.append(float(cells[4].replace(' ', '').replace('\xa0', '').replace(',', '.')))
        else:
            raise ValueError('Unknown price supplement parser')
        if len(extracted) != 1 or float(extracted[0]) != float(rule['native_close']):
            raise ValueError('Reviewed close differs from the original dated source row')
        if rule['native_basis_date'] != rule['date'] or rule['currency'] not in {'KRW', 'EUR', 'USD'}:
            raise ValueError('Native daily close requires its observation-date share basis and currency')
        factor = math.prod(float(s['ratio']) for s in splits if s['company_id'] == rule['company_id'] and rule['date'] < s['effective_date'] <= cutoff)
        close = float(rule['native_close']) / factor
        key = (rule['company_id'], rule['date'])
        existing = result.get(key)
        if existing:
            if existing['currency'] != rule['currency'] or not math.isclose(float(existing['close']), close, rel_tol=1e-6):
                raise ValueError('Base feed and reviewed daily close disagree; manual review required')
            continue
        result[key] = dict(company_id=rule['company_id'], date=rule['date'], close=close, currency=rule['currency'], adjustment_basis='split_adjusted_to_cutoff', source_url=rule['source_url'], source_sha256=rule['source_sha256'])
    return sorted(result.values(), key=lambda r: (r['company_id'], r['date']))


def main():
    policy = ROOT / 'data/market/price_supplements.json'
    if not policy.exists():
        return
    rules = json.loads(policy.read_text())
    path = ROOT / 'data/market/prices.csv'
    with path.open() as handle:
        reader = csv.DictReader(handle); fields = reader.fieldnames; rows = list(reader)
    with (ROOT / 'data/market/splits.csv').open() as handle:
        splits = list(csv.DictReader(handle))
    summary_path = ROOT / 'data/market/summary.json'
    summary = json.loads(summary_path.read_text())
    output = supplement(rows, rules, splits, summary['cutoff'])
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(output)
    for coverage in summary['coverage']:
        company = [r for r in output if r['company_id'] == coverage['company_id']]
        coverage.update(rows=len(company), first_date=company[0]['date'], last_date=company[-1]['date'])
        coverage['supplemented_dates'] = [r['date'] for r in company if any(r['source_sha256'] == rule['source_sha256'] for rule in rules)]
        coverage['remaining_missing_provider_bars'] = [d for d in coverage['missing_provider_bars'] if d not in coverage['supplemented_dates']]
    summary['total_prices'] = len(output)
    summary['reviewed_daily_close_supplements'] = rules
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'prices':len(output),'added_this_run':len(output)-len(rows),'reviewed_source_rows':len(rules)}))


if __name__ == '__main__':
    main()
