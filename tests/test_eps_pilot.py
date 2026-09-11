import importlib.util
from pathlib import Path
import unittest
from datetime import date

spec=importlib.util.spec_from_file_location('eps_pilot',Path(__file__).resolve().parents[1]/'scripts/compare_eps_pilot.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class EpsPilotTests(unittest.TestCase):
    def forecast(self,**changes):
        row=dict(company_id='fixture',fiscal_period='FY2024',fiscal_period_end='2024-07-01',currency='USD',series_type='individual_analyst_forecast',accounting_basis='reported_diluted',report_date='2024-01-01',available_date='2024-01-02',model_date='2024-01-01',series_id='analyst',eps='20',share_basis_date='2024-01-01',analyst='A',firm='Broker',observation_id='obs',source_url='https://example.test/forecast')
        row.update(changes);return row
    def outcome(self):
        return dict(company_id='fixture',fiscal_period='FY2024',fiscal_period_end='2024-07-01',currency='USD',accounting_basis='reported_diluted',initial_release_date='2024-08-01',value='11',share_basis_date='2024-08-01',outcome_id='actual',source_url='https://example.test/actual',definition='GAAP diluted EPS')
    def test_fixed_horizon_excludes_later_reports_and_normalizes_both_share_bases(self):
        forecasts=[self.forecast(),self.forecast(report_date='2024-03-01',available_date='2024-03-02',model_date='2024-03-01',eps='40')]
        pairs,blocked=module.compare(forecasts,[self.outcome()],[dict(company_id='fixture',effective_date='2024-06-10',ratio='2')])
        self.assertEqual(len(pairs),2)
        by_horizon={p['horizon_days']:p for p in pairs}
        self.assertEqual(by_horizon[180]['forecast_eps'],10)
        self.assertEqual(by_horizon[180]['actual_eps'],11)
        self.assertEqual(by_horizon[180]['signed_error_eps'],-1)
        self.assertEqual(by_horizon[180]['consensus_benchmark'],None)
        self.assertEqual(by_horizon[90]['forecast_eps'],20)
    def test_stale_reprint_unresolved_basis_and_consensus_are_not_scored(self):
        forecasts=[self.forecast(model_date='2023-01-01'),self.forecast(series_id='unresolved',accounting_basis='diluted_adjustment_basis_unresolved'),self.forecast(series_id='consensus',series_type='published_consensus')]
        pairs,blocked=module.compare(forecasts,[self.outcome()],[])
        self.assertEqual(pairs,[])
        self.assertEqual(len(blocked),3)

    def test_recent_reprint_cannot_replace_a_newer_numerical_model(self):
        fresh=self.forecast(report_date='2024-03-01',available_date='2024-03-02',model_date='2024-03-01',eps='40')
        reprint=self.forecast(report_date='2024-04-01',available_date='2024-04-02',model_date='2024-02-10',eps='20')
        pairs,_=module.compare([fresh,reprint],[self.outcome()],[])
        pair=next(p for p in pairs if p['horizon_days']==90)
        self.assertEqual(pair['forecast_eps'],40)
        self.assertEqual(pair['model_date'],'2024-03-01')
    def test_zero_actual_preserves_absolute_error_without_percentage_division(self):
        actual={**self.outcome(),'value':'0'}
        pairs,_=module.compare([self.forecast()],[actual],[])
        self.assertEqual(pairs[0]['absolute_error_eps'],20)
        self.assertEqual(pairs[0]['absolute_error_pct'],None)

    def test_dataset_cutoff_excludes_future_results_and_future_splits(self):
        actual=self.outcome()
        splits=[dict(company_id='fixture',effective_date='2025-01-01',ratio='2')]
        pairs,_=module.compare([self.forecast()],[actual],splits,as_of=date(2024,7,31))
        self.assertEqual(pairs,[])
        pairs,_=module.compare([self.forecast()],[actual],splits,as_of=date(2024,8,1))
        self.assertEqual(pairs[0]['forecast_eps'],20)
        self.assertEqual(pairs[0]['actual_eps'],11)

if __name__=='__main__':unittest.main()
