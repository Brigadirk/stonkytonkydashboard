"""Reproduce reviewed Bernstein annual forecasts from retained original pages.

No network requests. This checks original English page text, the public page
linkage, exact artifact hashes, and arithmetic consistency. Values are the
printed forecasts, never EPS inferred from share prices or valuation multiples.
"""
import csv
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OBS_FIELDS = 'observation_id,company_id,firm,analyst_name,source_type,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MAN_FIELDS = 'source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type'.split(',')
AUTHORS = 'David Dai; Stacy A. Rasgon; Qingyuan Lin; Mark Li; Juho Hwang; Jack Lin; Carmine Milano; Alrick Shaw; Arpad von Nemes; Francis Ma'
YEARS = [2027, 2028, 2029]
GAAP_EPS = ['9.69', '12.48', '14.74']
NONGAAP_EPS = ['9.19', '12.52', '14.81']
REVENUE = ['398818', '539563', '622987']
GAAP_INCOME = ['235657', '301562', '353883']
GAAP_SHARES = ['24331', '24171', '24011']
NONGAAP_INCOME = ['223376', '301914', '354235']
NONGAAP_SHARES = ['24316', '24116', '23916']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(name, fields, rows):
    with (BASE / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    records = json.loads((BASE / 'download_log.json').read_text())
    src = next(x for x in records if x['name'] == 'bernstein_scribd_p32')
    catalog = next(x for x in records if x['name'] == 'bernstein_public_catalog')
    assert src['status'] == catalog['status'] == 200
    assert digest(ROOT / src['file']) == src['sha256'] == 'd0de2f2d90851b727a8552535eaa93297b4d9083768d88352c8165e2000c412a'
    assert digest(ROOT / catalog['file']) == catalog['sha256']
    catalog_html = (ROOT / catalog['file']).read_text()
    linkage = re.search(r'pageNum:\s+32\s*,.*?blur:\s*(\w+)\s*,.*?contentUrl: "([^"]+)"', catalog_html, re.S)
    assert linkage and linkage.group(1) == 'false' and linkage.group(2) == src['url']
    catalog_text = re.sub(r'\s+', '', BeautifulSoup(catalog_html, 'html.parser').get_text())
    assert 'FirstPublished:16Jun202620:30UTC' in catalog_text
    assert '17June2026' in catalog_text
    raw = (ROOT / src['file']).read_text()
    assert raw.startswith('window.page32_callback(')
    html = json.loads(raw[raw.index('(') + 1:raw.rindex(')')])[0]
    text = BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)
    compact = re.sub(r'\s+', '', text)
    # Preserve original table column order and fiscal/calendar distinction.
    for expected in [
        'EXHIBIT47:BernsteinNVDAIncomeStatement',
        'CalendarQuarter20252026E2027E2028E',
        'FiscalQuarter20262027E2028E2029E',
        'GAAPRevenue215,938398,818539,563622,987',
        'NetIncome120,067235,657301,562353,883',
        'GAAPDilutedShareCount24,51524,33124,17124,011',
        'Non-GAAPDilutedShareCount24,51524,31624,11623,916',
        'GAAPDilutedEPS$4.90$9.69$12.48$14.74',
        'Non-GAAPDilutedEPS$4.77$9.19$12.52$14.81',
        'Source:Companyreports,Bernsteinestimatesandanalysis',
    ]:
        assert expected in compact, expected
    revenue_source = next(x for x in records if x['name'] == 'bernstein_original_p35')
    assert digest(ROOT / revenue_source['file']) == revenue_source['sha256']
    revenue_text = re.sub(r'\s+', '', (BASE / 'text/bernstein_20260617_original_p35.txt').read_text())
    assert 'NVDA:RevenueModel($M)' in revenue_text
    assert 'FiscalYearendsJanuary' in revenue_text
    assert 'TotalRevenues215,938398,818539,563622,987' in revenue_text
    for income, shares, eps in [(GAAP_INCOME, GAAP_SHARES, GAAP_EPS), (NONGAAP_INCOME, NONGAAP_SHARES, NONGAAP_EPS)]:
        for n, d, value in zip(income, shares, eps):
            assert abs(Decimal(n) / Decimal(d) - Decimal(value)) < Decimal('0.0051')
    # Quarterly diluted-share forecasts average to the printed annual shares.
    assert sum([24391, 24351, 24311, 24271]) / 4 == int(GAAP_SHARES[0])
    assert sum([24231, 24191, 24151, 24111]) / 4 == int(GAAP_SHARES[1])
    (BASE / 'originals/bernstein_20260617_original_p32.html').write_text(html)
    (BASE / 'text/bernstein_20260617_original_p32.txt').write_text(text + '\n')
    note = (
        'Original English Bernstein report, physical page32 Exhibit47; annual FY2027/FY2028/FY2029 '
        'forecasts, distinct from the calendar-year row. Page1 prints report date17June2026 and '
        'First Published16June2026 20:30UTC; that is a publisher-printed timestamp, not independently '
        'verified original dissemination. Separate numerical-model date is absent and remains blank. '
        'Full document byline retained as one Bernstein team contribution; no author is counted as '
        'an independent vote within this jointly authored model. Original page publicly visible in '
        'ordinary unauthenticated Scribd browser; exact page payload is advertised by its public '
        'catalog with blur:false and returned200 without credentials or token changes. This is a '
        'third-party-hosted original, not claimed official broker distribution. GAAP income and GAAP '
        'diluted-share rows are separately printed and reproduce GAAP EPS within rounding. FY2027/28 '
        'quarterly share averages match annual denominators. All units are post-June2024 split. '
        'Non-GAAP has different numerator and share counts and is retained in its own Bernstein '
        'basis; no cross-firm adjusted-EPS equivalence is asserted. Machine-translated East Money '
        'mirror is discovery only and supplies no accepted numerical observations.'
    )
    observations = []
    for metric, basis, unit, values in [
        ('eps', 'reported_diluted', 'USD_per_share', GAAP_EPS),
        ('eps', 'bernstein_non_gaap_diluted', 'USD_per_share', NONGAAP_EPS),
        ('revenue', 'revenue_as_printed', 'USD_million', REVENUE),
    ]:
        for year, value in zip(YEARS, values):
            identity = '|'.join([src['sha256'], 'nvidia', 'Bernstein', '2026-06-17', metric, basis, str(year), value])
            observations.append(dict.fromkeys(OBS_FIELDS, '') | dict(
                observation_id=hashlib.sha256(identity.encode()).hexdigest()[:24],
                company_id='nvidia', firm='Bernstein', analyst_name=AUTHORS,
                source_type='individual_analyst_forecast', metric=metric,
                fiscal_period=f'FY{year}', value=value, currency='USD', unit=unit, basis=basis,
                report_date='2026-06-17', printed_report_timestamp='2026-06-16T20:30:00Z',
                availability_basis='printed_report_timestamp_not_independently_verified',
                source_url=catalog['url'], local_file=src['file'], page='32',
                status='verified_original_report_page_html', notes=note,
                source_period_label=f'Fiscal Quarter {year}E (annual column)',
                share_basis_date='2026-06-17', source_artifact_sha256=src['sha256'],
            ))
    manifest = [dict.fromkeys(MAN_FIELDS, '') | dict(
        source_url=catalog['url'], local_file=src['file'], company_ids='nvidia',
        firm='Bernstein', analyst_name=AUTHORS, report_date='2026-06-17',
        retrieved_at=src['retrieved_at'], sha256=src['sha256'], status='verified_original_report_page_html',
        notes=note, text_file=str((BASE / 'text/bernstein_20260617_original_p32.txt').relative_to(ROOT)),
        report_timestamp='2026-06-16T20:30:00Z', http_status=200,
        report_month='2026-06', report_date_precision='day', artifact_type='report_page_html_payload',
    )]
    write_csv('observations.csv', OBS_FIELDS, observations)
    write_csv('manifest.csv', MAN_FIELDS, manifest)
    review = dict(
        company_id='nvidia', firm='Bernstein', report_date='2026-06-17',
        source_url=catalog['url'], payload_url=src['url'], source_file=src['file'], source_sha256=src['sha256'],
        original_page=32, fiscal_periods=[f'FY{x}' for x in YEARS],
        gaap_eps=GAAP_EPS, gaap_net_income_usd_million=GAAP_INCOME, gaap_diluted_shares_million=GAAP_SHARES,
        non_gaap_eps=NONGAAP_EPS, non_gaap_net_income_usd_million=NONGAAP_INCOME,
        non_gaap_diluted_shares_million=NONGAAP_SHARES, revenue_usd_million=REVENUE,
        gaap_status='source supports reported_diluted; compare only to verified US-GAAP diluted series',
        non_gaap_status='firm-specific; exact adjustment bridge to other firms not established',
        freshness_note='report is85days old at2026-09-10; unprinted numerical-model age may be older',
        history_note='One dated new Bernstein model, no retrospective reconstruction or best-predictor label',
        screenshot_files=['data/collection/us_estimators_round11/review/bernstein_original_p1.png',
                          'data/collection/us_estimators_round11/review/bernstein_original_p32.png'],
    )
    (BASE / 'compatibility_review.json').write_text(json.dumps(review, indent=2) + '\n')
    validation = dict(observations=len(observations), eps=6, revenue=3, original_models=1,
                      new_firms=1, gaap_diluted_forecasts=3, non_gaap_separate_forecasts=3,
                      retained_numerical_model_date=False, verified_original_dissemination=False,
                      five_year_bernstein_history_obtained=False,
                      observations_sha256=digest(BASE / 'observations.csv'), manifest_sha256=digest(BASE / 'manifest.csv'))
    (BASE / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
