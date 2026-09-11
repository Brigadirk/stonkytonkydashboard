"""Reproduce the supplementary candidate ledger; never promotes it to model rows."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
records = json.loads((BASE / 'download_log.json').read_text())
source = next(x for x in records if x['name'] == 'firstshanghai_newforce_20260909')
assert hashlib.sha256((ROOT / source['file']).read_bytes()).hexdigest() == source['sha256']
text = (BASE / 'text/firstshanghai_newforce_20260909.txt').read_text()
assert '2026 年 9 月 9 日' in text and '曹淩霽' in text and '韓嘯宇' in text
linkage = (BASE / 'staging/first_shanghai_daily_search.html').read_text()
assert '/UploadFiles/2026/09/09112431C51C9320.pdf' in linkage
review = dict(
    status='original_forecasts_verified_but_cross_firm_diluted_compatibility_unproven',
    company_id='broadcom', firm='First Shanghai', authors=['Rita Cao (曹淩霽)', 'Peter Han (韓嘯宇)'],
    report_date='2026-09-09', model_date=None,
    source_url=source['url'], local_file=source['file'], sha256=source['sha256'],
    public_linkage_url='https://www.mystockhk.com/searchInfo.aspx?NodeId=81&StartDate=2026-09-09&EndDate=2026-09-09',
    physical_page=3, raw_period_labels=['26年预测', '27年预测', '28年预测'],
    normalized_fiscal_periods=['FY2026', 'FY2027', 'FY2028'],
    eps_usd=['9.8', '17.2', '28.7'], revenue_usd_million=['105485', '175886', '287982'],
    net_income_usd_million=['46097', '81259', '135351'],
    historical_revenue_usd_million={'FY2024': '51574', 'FY2025': '63887'},
    historical_net_income_usd_million={'FY2024': '5895', 'FY2025': '23126'},
    historical_eps_usd={'FY2024': '1.3', 'FY2025': '4.9'},
    fiscal_issue='Printed header says fiscal year ended31December, inconsistent with Broadcom issuer calendar. Historical revenue anchors and narrative annual FY labels support issuerFY2024–FY2028 mapping; preserve the raw header conflict.',
    basis_issue='Annual row says EPS only. No diluted/basic denominator or future share count appears. Do not import as reported_diluted or combine with Morningstar. Do not infer denominator convention from rounded EPS/net-income arithmetic.',
    reproduction_note='Forecast table is an embedded image, manually read from retained physical-page3 render. Cover independently prints9.800/17.200 for2026/27. Old columns and printed change percentages are not separate observations.',
    screenshot='data/collection/us_estimators_round11/review/firstshanghai_newforce_20260909-3.png',
    incorporation='Held outside primary observations.csv to keep the verified Bernstein packet stable; integration owner may create explicitly limited firm-specific series after reviewing fiscal mapping and basis exclusions.',
)
(BASE / 'firstshanghai_candidate_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
print('First Shanghai source/hash/linkage checked; six manually reviewed forecast values retained as candidates.')
