import importlib.util
from pathlib import Path
import unittest
import csv
import io

spec=importlib.util.spec_from_file_location('import_ntm',Path(__file__).resolve().parents[1]/'scripts/import_ntm.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class NtmImportTests(unittest.TestCase):
    def text(self,**changes):
        row=dict(company_id='broadcom',series_id='provider_adjusted',label='Provider consensus',available_at='2026-09-08T21:15:00Z',estimate_date='2026-09-08',eps='-2',currency='USD',accounting_basis='Adjusted diluted',share_basis_date='2026-09-08',source_url='https://example.test/provider',source_reference='record-123')
        row.update(changes)
        return ','.join(module.FIELDS)+'\n'+','.join(row[k] for k in module.FIELDS)+'\n'
    def test_after_close_availability_and_negative_earnings_preserved(self):
        result=module.parse_import(self.text(),{'broadcom':'USD'},'2026-09-10')
        snap=result['series'][0]['snapshots'][0]
        self.assertEqual(snap['available_date'],'2026-09-09')
        self.assertEqual(snap['estimates'][0]['eps'],-2)
    def test_rejects_wrong_currency_missing_timezone_future_and_nonfinite(self):
        for change in [{'currency':'EUR'},{'available_at':'2026-09-08T21:15:00'},{'available_at':'2026-09-11T00:00:00Z'},{'eps':'nan'},{'estimate_date':'2026-09-09'}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                module.parse_import(self.text(**change),{'broadcom':'USD'},'2026-09-10')

    def test_named_estimates_preserve_identity_and_consensus_cannot_claim_an_author(self):
        base=next(csv.DictReader(io.StringIO(self.text())))
        def make(**extra):
            output=io.StringIO();row={**base,**extra}
            writer=csv.DictWriter(output,fieldnames=list(row));writer.writeheader();writer.writerow(row)
            return output.getvalue()
        result=module.parse_import(make(analyst='A',firm='Broker',series_type='individual_analyst_forecast'),{'broadcom':'USD'},'2026-09-10')
        self.assertEqual(result['series'][0]['analyst'],'A')
        self.assertEqual(result['series'][0]['firm'],'Broker')
        for extra in ({'analyst':'A'}, {'analyst':'A','firm':'Broker','series_type':'published_consensus'}):
            with self.assertRaises(ValueError):module.parse_import(make(**extra),{'broadcom':'USD'},'2026-09-10')
        self.assertEqual(module.parse_import(self.text(),{'broadcom':'USD'},'2026-09-10')['series'][0]['series_type'],'published_consensus')

if __name__=='__main__':unittest.main()
