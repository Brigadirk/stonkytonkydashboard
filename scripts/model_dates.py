"""Apply exact-source evidence that a later EPS table repeats an earlier model."""
from decimal import Decimal
import hashlib
import json


def apply_model_dates(rows, root):
    path = root / 'data/market/model_date_evidence.json'
    rules = json.loads(path.read_text()) if path.exists() else []
    for rule in rules:
        for prefix in ['earlier', 'later']:
            if hashlib.sha256((root / rule[prefix + '_source_file']).read_bytes()).hexdigest() != rule[prefix + '_source_sha256']:
                raise ValueError('Repeated-model evidence hash mismatch')
        def matches(row, prefix):
            return (row['company_id'], row['firm'], row['forecaster'], row['metric'], row['source_sha256']) == (rule['company_id'], rule['firm'], rule['analyst'], rule['metric'], rule[prefix + '_source_sha256'])
        expected = dict(zip(rule['fiscal_periods'], map(Decimal, rule.get('exact_matched_values', rule.get('exact_matched_eps', [])))))
        earlier = [r for r in rows if matches(r, 'earlier')]
        later = [r for r in rows if matches(r, 'later')]
        # Require the complete extracted EPS vector on both originals. Partial
        # overlap must never backdate additional targets from a newer model.
        for records in [earlier, later]:
            if not records or {r['fiscal_period']: Decimal(r['value']) for r in records} != expected:
                raise ValueError('Repeated-model evidence requires an exact complete ' + ('EPS' if rule['metric']=='eps' else rule['metric']) + ' vector')
        model_date = rule['earliest_verified_matching_model_date']
        if any((r['model_date'] or r['report_date']) != model_date for r in earlier):
            raise ValueError('Earlier model does not establish the reviewed date')
        for row in later:
            if row['report_date'] != rule['later_report_date'] or model_date >= row['report_date']:
                raise ValueError('Repeated-model dates are inconsistent')
            row['original_model_date'] = row['model_date']
            row['model_date'] = model_date
            row['model_date_evidence'] = rule['earlier_source_url']
            row['notes'] += ' Identical complete ' + rule['metric'] + ' vector retained in the earlier original dated ' + model_date + '; later publication does not refresh this model. ' + rule['earlier_source_url']
    return rows
