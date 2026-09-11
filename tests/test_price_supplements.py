import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('price_supplements',Path(__file__).resolve().parents[1]/'scripts/apply_price_supplements.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PriceSupplementTests(unittest.TestCase):
    def test_dated_original_close_split_conversion_and_conflict_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);body="[['날짜','시가','고가','저가','종가'],['20260910',101,110,90,100]]"
            (root/'source.txt').write_text(body)
            rule=dict(company_id='fixture',date='2026-09-10',currency='KRW',native_close=100,native_basis_date='2026-09-10',source_file='source.txt',source_sha256=hashlib.sha256(body.encode()).hexdigest(),source_url='https://example.test/daily',format='naver_daily')
            self.assertEqual(module.supplement([], [rule], [], '2026-09-09',root),[])
            row=module.supplement([], [rule], [], '2026-09-10',root)[0]
            self.assertEqual(row['close'],100)
            self.assertEqual(len(module.supplement([row],[rule],[],'2026-09-10',root)),1)
            splits=[dict(company_id='fixture',effective_date='2026-09-12',ratio=2)]
            self.assertEqual(module.supplement([], [rule], splits, '2026-09-13',root)[0]['close'],50)
            with self.assertRaisesRegex(ValueError,'disagree'):
                module.supplement([{**row,'close':99}],[rule],[],'2026-09-10',root)
            with self.assertRaisesRegex(ValueError,'original dated'):
                module.supplement([],[{**rule,'native_close':99}],[],'2026-09-10',root)
            (root/'source.txt').write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                module.supplement([],[rule],[],'2026-09-10',root)
