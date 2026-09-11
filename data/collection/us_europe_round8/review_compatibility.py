"""Reproduce exact-source ASML basis recommendations from frozen references."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
refs=list(csv.DictReader((BASE/'asml_reference_forecasts.csv').open()))
broker=json.loads((BASE/'broker_download_log.json').read_text())
current=next(r for r in broker if r['company_id']=='asml' and r.get('local_file'))
issuers=json.loads((BASE/'issuer_download_log.json').read_text())
groups=defaultdict(list)
for r in refs:
    if r['basis']=='reported_diluted':groups[(r['local_file'],r['model_date'])].append(r)
scopes=[]
for (path,model),rows in sorted(groups.items()):
    raw=(ROOT/path).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    expected=rows[0].get('source_artifact_sha256')
    assert not expected or expected==digest
    scopes.append(dict(company_id='asml',firm='Morningstar',analyst='Javier Correonero',model_date=model,source_file=path,source_url=rows[0]['source_url'],source_sha256=digest,physical_page=rows[0]['page'],report_date=rows[0]['report_date'],fiscal_periods=sorted({r['fiscal_period'] for r in rows}),observation_ids=[r['observation_id'] for r in rows],original_basis='reported_diluted',recommended_basis='morningstar_unadjusted_diluted',issuer_us_gaap_compatibility='unproven_historical_denominator_mismatch',recommended_treatment='Keep broker series available for valuation; exclude from issuer-reported scoring and cross-author GAAP ensembles until denominator policy is reconciled. Preserve original printed label.'))
review=dict(review_date='2026-09-10',company_id='asml',conclusion='The plain diluted row uses US-GAAP-like net-income inputs but its historical denominator is not consistently the issuer annual diluted denominator. Historical discrepancies do not prove future forecasts wrong; they prevent an unsupported equivalence assertion.',printed_label='Earnings Per Share (Diluted) (EUR)',new_collection_basis='morningstar_unadjusted_diluted',scope=scopes,historical_checks=[
    dict(fiscal_period='FY2022',broker_net_income_eur_million=5624,issuer_net_income_eur_million=5624.2,broker_shares_million=395,issuer_annual_diluted_shares_million=398.1,broker_eps=14.23,issuer_diluted_eps=14.13,issuer_basic_eps=14.14,broker_source_file=current['local_file'],broker_source_sha256=current['sha256'],broker_physical_page=15,issuer_source_name='asml_fy2022_statements',issuer_physical_page=1),
    dict(fiscal_period='FY2023',broker_net_income_eur_million=7839,issuer_net_income_eur_million=7839,broker_shares_million=394,issuer_annual_diluted_shares_million=394.1,broker_eps=19.91,issuer_diluted_eps=19.89,issuer_basic_eps=19.91,broker_source_file=current['local_file'],broker_source_sha256=current['sha256'],broker_physical_page=15,issuer_source_name='asml_fy2023_statements',issuer_physical_page=1),
    dict(fiscal_period='FY2025',broker_net_income_eur_million=9609,issuer_net_income_eur_million=9609.4,broker_shares_million=392,issuer_annual_diluted_shares_million=388.9,broker_eps=24.48,issuer_diluted_eps=24.71,issuer_basic_eps=24.73,broker_source_file='data/collection/asml_round5/pdfs/morningstar_asml_20260715.pdf',broker_physical_page=15,issuer_source_name='asml_fy2025_statements',issuer_physical_page=3)
],limits='This source-specific historical review does not prove that every future denominator is wrong. It supplies no correction factor, new EPS forecast or blanket alias for other companies. Adjusted rows remain Morningstar-specific and are not issuer-adjusted equivalents.')
for check in review['historical_checks']:
    issuer_name=check.pop('issuer_source_name')
    issuer=next(x for x in issuers if x['name']==issuer_name and x.get('local_file'))
    check.update(issuer_source_url=issuer['source_url'],issuer_source_file=issuer['local_file'],issuer_source_sha256=issuer['sha256'])
    if not check.get('broker_source_sha256'):check['broker_source_sha256']=hashlib.sha256((ROOT/check['broker_source_file']).read_bytes()).hexdigest()
(BASE/'asml_issuer_comparability_review.json').write_text(json.dumps(review,indent=2)+'\n')
legacy=[r for r in refs if r['basis']=='diluted_adjustment_basis_unresolved']
values={'FY2025':'24.69','FY2026':'30.87','FY2027':'35.84'}
assert len(legacy)==3
for r in legacy:assert r['value']==values[r['fiscal_period']] and r['model_date']=='2025-01-29'
alias=dict(review_date='2026-09-10',recommendations=[dict(company_id='asml',firm='Morningstar',analyst='Javier Correonero',original_basis='diluted_adjustment_basis_unresolved',canonical_basis='adjusted_diluted',model_dates=['2025-01-29'],fiscal_periods=list(values),matched_values=values,matched_revenue_values_eur_million={'FY2025':'34201','FY2026':'38258','FY2027':'42868'},original_observation_ids=[r['observation_id'] for r in legacy],original_sources=[dict(source_url=legacy[0]['source_url'],source_file=legacy[0]['local_file'],source_sha256=hashlib.sha256((ROOT/legacy[0]['local_file']).read_bytes()).hexdigest(),physical_page=int(legacy[0]['page']),report_date=legacy[0]['report_date'])],evidence=dict(source_url=current['source_url'],source_file=current['local_file'],source_sha256=current['sha256'],physical_page=15,report_date='2025-04-03',locator='Current model29Jan2025; explicit adjusted diluted EPS and revenue rows match the Jan30 original exactly for FY2025–FY2027.'),status='supported_model_and_period_scoped_alias',issuer_non_gaap_equivalence='not_proven_do_not_score_against_issuer_non_gaap',limits='Only exact dated model, named analyst, original hashes and fiscal targets. No prior-panel values become backdated observations. Plain EPS also agrees, but issuer-GAAP denominator equivalence remains unproven; canonical adjusted keeps a broker-specific valuation series.')],rejected_prior_bridge=dict(original_model_date='2024-11-06',revision_panel_prior_date='2024-11-15',matched_eps=['18.86','23.75','29.84'],reason='Dates disagree despite equal vectors; no alias or historical reconstruction without original model-date reconciliation.'))
(BASE/'basis_alias_recommendations.json').write_text(json.dumps(alias,indent=2)+'\n')
print('Existing ASML modern source/model scopes',len(scopes),'reported rows',sum(len(s['observation_ids']) for s in scopes),'legacy alias rows',len(legacy))
