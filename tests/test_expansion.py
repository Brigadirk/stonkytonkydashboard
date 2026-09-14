import copy
from datetime import date, datetime, timezone
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


def script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


imp = script('import_expansion')
prices = script('collect_prices')


class ExpansionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'report.pdf').write_bytes(b'retained test source')
        self.company = dict(id='test', currency='USD')
        self.series = dict(currency='USD', accounting_basis='adjusted_diluted', firm='Test research',
            series_type='individual_analyst_forecast', analyst='Test analyst', snapshots=[dict(
                id='snapshot', report_date='2026-08-12', model_date='2026-05-13',
                available_date='2026-08-13', availability_basis='report_date_plus_one_day_unverified',
                share_basis_date='2026-08-12', source_url='https://example.test/report.pdf',
                source_file='report.pdf', source_sha256=hashlib.sha256(b'retained test source').hexdigest(),
                kind='annual', estimates=[dict(fiscal_period_start='2026-01-01',
                    fiscal_period_end='2026-12-31', eps=-4.42, source_page='14')])])

    def validate(self, series=None):
        imp.validate_series(series or self.series, self.company, '2026-09-11', self.root, set())

    def test_negative_earnings_and_old_model_date_are_preserved(self):
        self.validate()
        snapshot = self.series['snapshots'][0]
        self.assertEqual(snapshot['estimates'][0]['eps'], -4.42)
        self.assertEqual(snapshot['model_date'], '2026-05-13')
        self.assertEqual(snapshot['available_date'], '2026-08-13')

    def test_currency_mismatch_and_changed_source_are_rejected(self):
        changed = copy.deepcopy(self.series)
        changed['currency'] = 'TWD'
        with self.assertRaisesRegex(ValueError, 'currency differs'):
            self.validate(changed)
        (self.root / 'report.pdf').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.validate()

    def test_backdating_and_false_verified_availability_are_rejected(self):
        for values, reason in [
            ({'available_date': '2026-05-14'}, 'own report-day'),
            ({'verified_available_date': '2026-08-13'}, 'unverified'),
            ({'report_date': '2026-09-14'}, 'after cutoff'),
        ]:
            changed = copy.deepcopy(self.series)
            changed['snapshots'][0].update(values)
            with self.assertRaisesRegex(ValueError, reason):
                self.validate(changed)

    def test_overlapping_annual_periods_are_rejected(self):
        snapshot = self.series['snapshots'][0]
        snapshot['estimates'].append(dict(fiscal_period_start='2026-12-31',
            fiscal_period_end='2027-12-30', eps=6.74, source_page='14'))
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            self.validate()

    def test_nebius_history_excludes_yandex_predecessor(self):
        dates = ['2024-10-18', '2024-10-21']
        timestamps = [int(datetime.fromisoformat(d + 'T15:00:00+00:00').timestamp()) for d in dates]
        payload = {'chart': {'result': [{'meta': {'symbol': 'NBIS', 'currency': 'USD',
            'exchangeTimezoneName': 'America/New_York'}, 'timestamp': timestamps,
            'indicators': {'quote': [{'close': [999, 20]}]}}]}}
        record = dict(downloaded_at='2026-09-13T22:00:00+00:00', source_url='https://example.test/prices', source_sha256='test')
        rows, _, _ = prices.parse_chart('nebius', payload, record,
            date(2020, 9, 10), date(2026, 9, 11), True)
        self.assertEqual([(r['date'], r['close']) for r in rows], [('2024-10-21', 20)])


if __name__ == '__main__':
    unittest.main()
