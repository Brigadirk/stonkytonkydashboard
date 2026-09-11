import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
refresh = module('refresh_dashboard')
discovery = module('discover_reports')


class RefreshTests(unittest.TestCase):
    def test_failed_run_restores_files_and_app_and_removes_new_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'data').mkdir(); (root/'web/dist').mkdir(parents=True)
            (root/'data/prices.csv').write_text('original prices')
            (root/'web/dist/index.html').write_text('working app')
            paths = ['data/prices.csv', 'data/new.json', 'web/dist']
            with self.assertRaises(RuntimeError):
                with refresh.Rollback(root, root/'run', paths):
                    (root/'data/prices.csv').write_text('truncated download')
                    (root/'data/new.json').write_text('partial result')
                    (root/'web/dist/index.html').write_text('broken app')
                    raise RuntimeError('build failed')
            self.assertEqual((root/'data/prices.csv').read_text(), 'original prices')
            self.assertEqual((root/'web/dist/index.html').read_text(), 'working app')
            self.assertFalse((root/'data/new.json').exists())
            self.assertEqual((root/'run/before/data/prices.csv').read_text(), 'original prices')

    def test_success_keeps_new_output_and_archives_old_vintage(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'forecast.csv').write_text('old model')
            with refresh.Rollback(root, root/'run', ['forecast.csv']):
                (root/'forecast.csv').write_text('new model')
            self.assertEqual((root/'forecast.csv').read_text(), 'new model')
            self.assertEqual((root/'run/before/forecast.csv').read_text(), 'old model')

    def test_price_validation_rejects_silent_historical_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data/market').mkdir(parents=True)
            (root/'data/universe.csv').write_text('company_id\nfixture\n')
            (root/'data/market/summary.json').write_text(json.dumps(dict(cutoff='2026-09-10',adjustment_definition_verified=True,coverage=[dict(company_id='fixture',status='available')])))
            (root/'before.csv').write_text('company_id,date\nfixture,2026-09-08\nfixture,2026-09-09\n')
            (root/'data/market/prices.csv').write_text('company_id,date\nfixture,2026-09-09\n')
            with self.assertRaisesRegex(ValueError, 'lost 1'):
                refresh.validate_prices(root, root/'before.csv', '2026-09-10')

    def test_downloaded_reports_are_content_addressed_and_html_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            inbox=Path(folder)
            first,digest=discovery.retain_pdf(b'%PDF-1.4 first vintage',inbox)
            second,other=discovery.retain_pdf(b'%PDF-1.4 revised vintage',inbox)
            self.assertNotEqual(digest,other)
            self.assertEqual(first.read_bytes(),b'%PDF-1.4 first vintage')
            self.assertTrue(second.exists())
            with self.assertRaisesRegex(ValueError,'not a PDF'):
                discovery.retain_pdf(b'<html>Access denied</html>',inbox)

if __name__=='__main__': unittest.main()
