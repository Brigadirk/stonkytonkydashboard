from pathlib import Path
from decimal import Decimal
import hashlib
import importlib.util
import json
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('model_dates', Path(__file__).resolve().parents[1] / 'scripts/model_dates.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ModelDateTests(unittest.TestCase):
    def test_complete_reprint_keeps_earlier_age_and_partial_match_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'data/market').mkdir(parents=True)
            rule = dict(company_id='test', firm='Firm', analyst='Author', metric='eps', later_report_date='2026-05-01', earliest_verified_matching_model_date='2026-04-01', fiscal_periods=['FY2026', 'FY2027'], exact_matched_eps=['2', '3'], earlier_source_url='https://example.test/old')
            rows = []
            for prefix, day in [('earlier', '2026-04-01'), ('later', '2026-05-01')]:
                (root / prefix).write_text(prefix)
                rule[prefix + '_source_file'] = prefix
                rule[prefix + '_source_sha256'] = hashlib.sha256(prefix.encode()).hexdigest()
                for period, value in zip(rule['fiscal_periods'], rule['exact_matched_eps']):
                    rows.append(dict(company_id='test', firm='Firm', forecaster='Author', metric='eps', source_sha256=rule[prefix + '_source_sha256'], fiscal_period=period, value=value, report_date=day, model_date='', notes=''))
            (root / 'data/market/model_date_evidence.json').write_text(json.dumps([rule]))
            result = module.apply_model_dates([dict(r) for r in rows], root)
            self.assertEqual(result[-1]['model_date'], '2026-04-01')
            self.assertEqual(result[-1]['original_model_date'], '')
            self.assertEqual(result[-1]['model_date_evidence'], rule['earlier_source_url'])
            changed = [dict(r) for r in rows]
            changed[-1]['value'] = '4'
            with self.assertRaisesRegex(ValueError, 'complete EPS vector'):
                module.apply_model_dates(changed, root)
            with self.assertRaisesRegex(ValueError, 'complete EPS vector'):
                module.apply_model_dates(rows + [{**rows[-1], 'fiscal_period':'FY2028'}], root)
            (root / 'earlier').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                module.apply_model_dates(rows, root)
