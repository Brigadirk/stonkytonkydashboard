import importlib.util
from pathlib import Path
import tempfile
import hashlib
import json
from datetime import date
import unittest

spec=importlib.util.spec_from_file_location('forecast_panel',Path(__file__).resolve().parents[1]/'scripts/build_forecast_panel.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ForecastPanelTests(unittest.TestCase):
    def row(self,**kwargs):
        data=dict(observation_id='fixture',company_id='asml',forecaster='Named analyst',firm='Publisher',observation_type='individual_analyst_forecast',metric='eps',ranking_status='unscored',accounting_basis='reported_diluted',fiscal_period='FY2026',report_date='2026-01-10',model_date='',source_file='report.pdf',source_sha256=hashlib.sha256(b'fixture').hexdigest(),unit='EUR_per_share',currency='EUR',value='20',notes='',source_url='https://example.test/report',source_page='1')
        data.update(kwargs)
        return data
    def test_exact_fiscal_calendars(self):
        self.assertEqual(module.fiscal_end('sandisk',2025)[0],date(2025,6,27))
        self.assertEqual(module.fiscal_end('sandisk',2026)[0],date(2026,7,3))
        self.assertEqual(module.fiscal_end('asml',2026)[0],date(2026,12,31))
        self.assertEqual(module.fiscal_end('besi',2026)[0],date(2026,12,31))
        self.assertEqual(module.fiscal_end('apple',2023)[0],date(2023,9,30))
        self.assertEqual(module.fiscal_end('apple',2024)[0],date(2024,9,28))
    def test_published_consensus_does_not_require_or_inherit_an_analyst(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'report.pdf').write_bytes(b'fixture')
            rows=[self.row(),self.row(observation_id='consensus',observation_type='published_consensus',value='21')]
            panel,series,gaps=module.build_panel(rows,root=root)
            self.assertEqual(len(series),2)
            consensus=next(s for s in series if s['series_type']=='published_consensus')
            self.assertEqual(consensus['analyst'],'')
            self.assertIn('Published consensus',consensus['label'])
            self.assertEqual(len({r['series_id'] for r in panel}),2)
    def test_quarantine_and_unknown_publishers_stay_excluded(self):
        self.assertEqual(module.eligibility(self.row(ranking_status='quarantined',observation_type='published_consensus'),module.AS_OF),'quarantined')
        self.assertEqual(module.eligibility(self.row(firm='',forecaster='',observation_type='published_consensus'),module.AS_OF),'unattributed')
        self.assertEqual(module.eligibility(self.row(forecaster=''),module.AS_OF),'unattributed')

    def test_joint_authors_remain_one_attributed_team_series(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'report.pdf').write_bytes(b'fixture')
            panel,series,_=module.build_panel([self.row(forecaster='Author A; Author B')],root=root)
            self.assertEqual(len(series),1)
            self.assertEqual(series[0]['series_type'],'named_analyst_team')
            self.assertEqual(panel[0]['analyst'],'Author A; Author B')

    def test_captured_public_snapshot_does_not_claim_a_printed_report_or_model_date(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'report.pdf').write_bytes(b'fixture')
            row=self.row(observation_type='published_consensus',report_date='2026-09-10',first_observed_at='2026-09-10T17:53:52+00:00')
            panel,_,_=module.build_panel([row],root=root)
            self.assertEqual(panel[0]['available_date'],'2026-09-11')
            self.assertEqual(panel[0]['availability_basis'],'first_observed_public_snapshot')
            self.assertEqual(panel[0]['model_date'],'')
            with self.assertRaisesRegex(ValueError,'actual UTC capture date'):
                module.build_panel([{**row,'report_date':'2026-09-09'}],root=root)
            with self.assertRaisesRegex(ValueError,'invented model date'):
                module.build_panel([{**row,'model_date':'2026-09-10'}],root=root)

    def test_basis_alias_is_scoped_and_conflicting_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'report.pdf').write_bytes(b'fixture')
            (root/'data/market').mkdir(parents=True)
            rule=dict(company_ids=['asml'],firm='Publisher',analyst='Named analyst',original_basis='Equivalent wording',canonical_basis='reported_diluted',evidence={'source_url':'https://example.test/evidence'})
            (root/'data/market/basis_aliases.json').write_text(json.dumps([rule]))
            alias=self.row(observation_id='alias',accounting_basis='Equivalent wording')
            panel,series,gaps=module.build_panel([self.row(),alias],root=root)
            self.assertEqual(len(panel),1)
            self.assertEqual(gaps['exclusions']['same_source_same_value_after_basis_alias'],1)
            self.assertEqual(module.normalize_basis({**alias,'forecaster':'Someone else'},[rule]),('Equivalent wording',''))
            self.assertEqual(module.normalize_basis({**alias,'firm':'Other publisher'},[rule]),('Equivalent wording',''))
            scoped={**rule,'model_dates':['2025-11-01']}
            self.assertEqual(module.normalize_basis(alias,[scoped]),('Equivalent wording',''))
            self.assertEqual(module.normalize_basis({**alias,'model_date':'2025-11-01'},[scoped]),('reported_diluted','https://example.test/evidence'))
            hashed={**rule,'source_hashes':['different']}
            self.assertEqual(module.normalize_basis(alias,[hashed]),('Equivalent wording',''))
            limited={**rule,'fiscal_periods':['FY2025']}
            self.assertEqual(module.normalize_basis(alias,[limited]),('Equivalent wording',''))
            with self.assertRaisesRegex(ValueError,'exact value'):
                module.normalize_basis(alias,[{**rule,'matched_values':{'FY2026':'21'}}])
            with self.assertRaisesRegex(ValueError,'Conflicting EPS'):
                module.build_panel([self.row(),{**alias,'value':'21'}],root=root)
            panel,_,_=module.build_panel([alias],root=root)
            self.assertEqual(panel[0]['original_accounting_basis'],'Equivalent wording')
            self.assertEqual(panel[0]['basis_alias_evidence'],'https://example.test/evidence')

    def test_reprint_crossing_split_requires_an_explicit_share_basis(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'report.pdf').write_bytes(b'fixture')
            (root/'data/market').mkdir(parents=True)
            (root/'data/market/splits.csv').write_text('company_id,effective_date,ratio\nnvidia,2024-06-10,10\n')
            row=self.row(company_id='nvidia',currency='USD',unit='USD_per_share',model_date='2024-05-22',report_date='2024-06-11')
            panel,_,gaps=module.build_panel([row],root=root)
            self.assertEqual(panel,[])
            self.assertEqual(gaps['exclusions']['share_basis_crosses_split_unresolved'],1)
            panel,_,_=module.build_panel([{**row,'share_basis_date':'2024-06-11'}],root=root)
            self.assertEqual(panel[0]['share_basis_date'],'2024-06-11')

if __name__=='__main__':unittest.main()
