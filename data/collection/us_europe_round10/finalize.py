"""Reproduce round10 CSVs from manually reviewed original report tables.

The image records below are manual transcriptions, not OCR or inferred EPS.
Every primary artifact and linked review image is hash checked. The complete
PDF is additionally checked against pdftotext -layout. No network is used.
"""
import csv
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OBS_FIELDS = 'observation_id,company_id,firm,analyst_name,source_type,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MAN_FIELDS = 'source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type'.split(',')

SPECS = [
    dict(date='2024-08-30', name='guosen_nvidia_20240830.pdf',
         sha256='c9ec4666215fd6101f89be44958756c78579b3f41f58ca042b8a1d1b47b27962',
         authors='Zhang Lunke (张伦可)',
         years=[2025, 2026, 2027], raw=['2024E', '2025E', '2026E'],
         revenue=['123659', '164228', '184586'], eps=['2.73', '3.64', '4.19'],
         parent_profit=['66997', '89375', '102903'], income_statement_parent_profit=['66997', '89375', '102903'],
         model_page=5, historical_labels=['2022', '2023'], historical_revenue=['26974', '60922'],
         historical_parent_profit=['4368', '29760'], historical_eps=['0.18', '1.21'],
         mapping='Raw model labels lag issuer fiscal years by one. Same-page investment recommendation explicitly identifies FY2025–FY2027 and revenues1237/1642/1846 hundred-millionUSD, matching the annual model123659/164228/184586 millionUSD. Historical26974/60922 also match issuerFY2023/24. The report title itself says24FYQ2, while its narrative correctly discussesFY25Q2; retain the typo without changing annual targets.',
         extra='Liu Zitan is printed only as contact, not a licensed coauthor. This is the earlier source of the same complete EPS/revenue vector subsequently printed on November22,2024; no earlier numerical model date is invented.'),
    dict(date='2025-08-29', name='guosen_nvidia_20250829_cover.png',
         sha256='5e7ede40567264b2033f3cec65c8ea85f3c58b4f61cb43d5ac49a0f2f1927bd5',
         authors='Zhang Lunke (张伦可); Liu Zitan (刘子谭)', doc_id='5027955',
         years=[2026, 2027, 2028], raw=['FY2026E', 'FY2027E', 'FY2028E'],
         revenue=['205569', '271353', '306613'], eps=['4.23', '6.05', '6.93'],
         parent_profit=['102706', '146897', '168317'], income_statement_parent_profit=None,
         historical_labels=['FY2024', 'FY2025'], historical_revenue=['60922', '130497'],
         historical_parent_profit=['29760', '72880'], historical_eps=['1.22', '3.00'],
         mapping='Annual model explicitly labelsFY2026E/FY2027E/FY2028E. The footnote says issuer fiscal labels differ from natural-calendar years; its approximate January26 illustration is not used as the fiscal-period end.',
         extra='Both authors are printed as licensed securities analysts. The original cover fills the gap after the May2025 conflicted EPS model without repairing or backdating that model.'),
    dict(date='2025-11-24', name='guosen_nvidia_20251124_cover.png',
         sha256='ec06796a0630cf006857e8fe954dd60d780db31408ae2dd618bcbc8b981283b7',
         authors='Zhang Lunke (张伦可); Liu Zitan (刘子谭); Zhang Haochen (张昊晨)', doc_id='5163387',
         years=[2026, 2027, 2028], raw=['2025E', '2026E', '2027E'],
         revenue=['213035', '333499', '427880'], eps=['4.70', '7.72', '9.68'],
         parent_profit=['114121', '187596', '235224'], income_statement_parent_profit=None,
         historical_labels=['2023', '2024'], historical_revenue=['60922', '130497'],
         historical_parent_profit=['29760', '72880'], historical_eps=['1.22', '3.00'],
         mapping='Raw model labels lag issuer fiscal years by one. Same-page investment recommendation explicitly names FY2026–FY2028 with revenues2130/3335/4279 hundred-millionUSD, matching213035/333499/427880 millionUSD. Historical60922/130497 correspond to issuerFY2024/25. Preserve raw labels and use the independently registered issuer calendar.',
         extra='All three authors are printed as licensed securities analysts. Public catalog uploader Good Luck is not an author.'),
    dict(date='2026-08-31', name='guosen_nvidia_20260831_cover.png',
         sha256='fbc87b25f6a7202ba876b4dbf22ffc12b73c13c3b1fb748cfdd3cc0e611b3631',
         authors='Zhang Lunke (张伦可); Liu Zitan (刘子谭)', doc_id='5665920',
         years=[2027, 2028, 2029], raw=['2026E', '2027E', '2028E'],
         revenue=['408886', '681431', '840944'], eps=['10.66', '16.34', '19.70'],
         parent_profit=['256831', '393724', '474858'], income_statement_parent_profit=None,
         historical_labels=['2024', '2025'], historical_revenue=['130497', '215938'],
         historical_parent_profit=['72880', '120067'], historical_eps=['3.02', '4.98'],
         mapping='Raw model labels lag issuer fiscal years by one. Same-page investment recommendation explicitly names FY2027–FY2029 with revenues4089/6814/8409 hundred-millionUSD, matching408886/681431/840944 millionUSD. Historical130497/215938 correspond to issuerFY2025/26. Footnote January26 example is approximate; use independently registered issuer annual ends.',
         extra='Both authors are printed as licensed securities analysts. The report explicitly revises the February27,2026 revenue/profit model; no separate May2026 vintage is established. Public catalog uploader and September2 indexing date are not report authorship or historical dissemination.'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(name, fields, rows):
    with (BASE / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def json_write(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def row_values(page, label):
    for line in page.splitlines():
        if label in line:
            return [x.replace(',', '') for x in re.findall(r'\d[\d,]*(?:\.\d+)?', line.split(label, 1)[1])]
    raise AssertionError(label)


log = json.loads((BASE / 'download_log.json').read_text())
by_name = {x.get('name'): x for x in log if x.get('name')}
observations, manifest, transcriptions, scopes, limited = [], [], [], [], []

for spec in SPECS:
    src = by_name[spec['name']]
    assert src['http_status'] == 200
    assert sha(ROOT / src['local_file']) == spec['sha256'] == src['sha256']
    is_image = spec['name'].endswith('.png')
    note = ('Original Guosen Securities annual forecast table, physically reviewed on report page1. '
            'Current research-team forecast; Wind/Guosen source footer does not mean analyst consensus. '
            'No separate numerical model date or independently verified original dissemination timestamp is printed. '
            'Keep report date distinct from retrieval date; both availability fields remain blank. '
            'EPS is printed inUSD and footnote explicitly states diluted EPS is calculated using latest total share capital '
            '(摊薄每股收益按最新总股本计算). All values are post-June2024 NVIDIA10-for-1 split units. '
            'Latest total share capital is not issuer weighted-average diluted shares; no issuer GAAP or non-GAAP compatibility is claimed. '
            + spec['mapping'] + ' ' + spec['extra'] + ' ')
    text_file = ''
    review_images = []
    if is_image:
        jpg = by_name[spec['name'].replace('.png', '.jpg')]
        assert sha(ROOT / jpg['local_file']) == jpg['sha256']
        review_images.append(jpg)
        api = next(x for x in log if x.get('name') == 'capture_' + spec['doc_id'] + '_preview_api.txt')
        assert sha(ROOT / api['local_file']) == api['sha256']
        response = json.loads((ROOT / api['local_file']).read_text())
        linked = 'report-image/' + spec['date'].replace('-', '/') + '/' + spec['doc_id'] + '-1.png'
        assert linked in response['data']
        assert src['source_url'] == 'https://public.fxbaogao.com/' + linked
        note += ('Original report-page image retained from public FXBaogao preview API linkage; third-party mirror, not an official distributor. '
                 'Raw PNG is the cited artifact; its linked server-generated JPEG rendition was visually reviewed because PNG transparency can render dark. '
                 'Only original page1 was extracted; full PDF and income-statement cross-check unavailable. '
                 'Parent-net-income row and EPS share convention are legible, but matching cover/full-model numerator vectors is unverified. '
                 'Keep this explicitly limited basis separate from the fully cross-checked Guosen group pending source-scoped review. '
                 'Joint authors constitute one Guosen forecast stream, never independent votes. ')
        basis = 'guosen_latest_total_shares_eps_numerator_not_crosschecked'
        status = 'verified_original_report_page_image'
    else:
        text_file = str((BASE / 'text' / spec['name'].replace('.pdf', '.txt')).relative_to(ROOT))
        pages = (ROOT / text_file).read_text().split('\f')
        compact = re.sub(r'\s+', '', pages[0])
        assert '2024年08月30日' in compact and '摊薄每股收益按最新总股本计算' in compact
        assert row_values(pages[0], 'EPS（美元）')[-3:] == spec['eps']
        assert row_values(pages[0], '营业收入(百万美元)')[-3:] == spec['revenue']
        assert row_values(pages[0], '归母净利润(百万美元)')[-3:] == spec['parent_profit']
        for label in ['归属于母公司净利润', '归母净利润']:
            assert row_values(pages[4], label)[-3:] == spec['income_statement_parent_profit']
        note += ('Complete original PDF retained from public East Money PDF host. Physicalp5 income statement has two parent-net-income labels; '
                 'both exact three-year vectors match the cover numerator66997/89375/102903USDmillion. '
                 'Source-scoped addition to the fully cross-checked Guosen latest-total-share EPS stream is supported. ')
        basis = 'guosen_latest_total_shares_eps'
        status = 'verified_original_table'

    for metric, row_basis, values in [('eps', basis, spec['eps']), ('revenue', 'total_revenue', spec['revenue'])]:
        for year, raw, value in zip(spec['years'], spec['raw'], values):
            obs = dict.fromkeys(OBS_FIELDS, '')
            obs.update(observation_id=hashlib.sha256('|'.join([src['sha256'], metric, str(year), value]).encode()).hexdigest()[:24],
                       company_id='nvidia', firm='Guosen Securities', analyst_name=spec['authors'],
                       source_type='individual_analyst_forecast', metric=metric, fiscal_period=f'FY{year}', value=value,
                       currency='USD', unit='USD_per_share' if metric == 'eps' else 'USD_million', basis=row_basis,
                       report_date=spec['date'], availability_basis='printed_report_date_not_independently_verified',
                       source_url=src['source_url'], local_file=src['local_file'], page=1, status=status,
                       notes=note, source_period_label=raw, share_basis_date=spec['date'], source_artifact_sha256=src['sha256'])
            observations.append(obs)
    manifest.append(dict(source_url=src['source_url'], local_file=src['local_file'], company_ids='nvidia',
                         firm='Guosen Securities', analyst_name=spec['authors'], report_date=spec['date'],
                         retrieved_at=src['retrieved_at'], sha256=src['sha256'], status=status, notes=note,
                         text_file=text_file, report_timestamp='', model_dates='', http_status=200,
                         report_month=spec['date'][:7], report_date_precision='day',
                         artifact_type='report_page_image' if is_image else 'pdf'))
    transcription = {**spec, 'source_url': src['source_url'], 'source_file': src['local_file'],
                     'source_page': 1, 'transcription_method': 'manual_visual_review_of_original_table',
                     'eps_row_label': 'EPS（美元）', 'revenue_row_label': '营业收入(百万美元)',
                     'parent_profit_row_label': '归母净利润(百万美元)',
                     'printed_share_footnote': '摊薄每股收益按最新总股本计算',
                     'review_images': review_images, 'notes': note}
    transcriptions.append(transcription)
    D = Decimal
    # Diagnostic only: does rounding permit one latest-share denominator for the
    # printed cover profit/EPS vector? Never use this to generate observations.
    low = max((D(n) - D('.5')) / (D(e) + D('.005')) for n, e in zip(spec['parent_profit'], spec['eps']))
    high = min((D(n) + D('.5')) / (D(e) - D('.005')) for n, e in zip(spec['parent_profit'], spec['eps']))
    assert low <= high
    review = dict(source_url=src['source_url'], source_file=src['local_file'], source_sha256=src['sha256'],
                  report_date=spec['date'], model_date='', authors=spec['authors'],
                  source_pages=[1] if is_image else [1, 5], fiscal_periods=[f'FY{x}' for x in spec['years']],
                  printed_eps=spec['eps'], raw_basis=basis, cover_parent_net_profit_usd_million=spec['parent_profit'],
                  income_statement_parent_net_profit_usd_million=spec['income_statement_parent_profit'],
                  independent_latest_total_share_footnote_verified=True,
                  full_model_numerator_crosscheck_verified=not is_image,
                  cover_constant_share_rounding_interval_million=[str(low), str(high)],
                  arithmetic_diagnostic_not_definition_proof=True,
                  issuer_gaap_compatibility=False, cross_firm_compatibility=False,
                  recommendation='Retain source-specific partial-image basis; no promotion into the full-model-verified group.' if is_image else 'Add only this source/report/FY scope to guosen_latest_total_shares_eps.',
                  evidence=note)
    (limited if is_image else scopes).append(review)

assert len(observations) == 24 and len(manifest) == 4
assert len({x['observation_id'] for x in observations}) == 24
assert all(not x['model_date'] and not x['available_at'] and not x['original_available_at'] for x in observations)
write_csv('observations.csv', OBS_FIELDS, observations)
write_csv('manifest.csv', MAN_FIELDS, manifest)
json_write('verified_transcriptions.json', transcriptions)
json_write('guosen_definition_review.json', dict(review_date='2026-09-10', company_id='nvidia', firm='Guosen Securities',
           one_firm_stream=True, issuer_gaap_compatibility=False, cross_firm_compatibility=False,
           fully_crosschecked_additional_scopes=scopes, image_only_scopes=limited,
           existing_may2025_conflict_unchanged=True,
           policy='At most one firm/team contribution per date. Individual image rows are verified observations, but missing full-model evidence is not manufactured by carrying forward another report definition.'))
validation = dict(observations=24, eps_rows=12, revenue_rows=12, verified_rows=24, new_quarantined_rows=0,
                  report_vintages=4, complete_original_pdfs=1, original_cover_page_images=3,
                  full_model_verified_eps_rows=3, image_only_eps_rows=9,
                  exact_full_model_compatibility_scopes=1, scoped_fiscal_targets=3,
                  new_issuer_outcomes=0, historical_availability_assumed=False,
                  all_artifact_hashes_verified=True, manual_physical_page_review=True,
                  observations_sha256=sha(BASE / 'observations.csv'), manifest_sha256=sha(BASE / 'manifest.csv'))
json_write('validation.json', validation)
print(json.dumps(validation, indent=2))
