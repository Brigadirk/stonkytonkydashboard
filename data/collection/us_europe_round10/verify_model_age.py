"""Verify one unchanged Guosen model against two retained original PDFs.

Read-only with respect to both collections' CSVs and all central policies.
Writes only this round's source-scoped model-age recommendation.
"""
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
EARLY = ROOT / 'data/collection/us_europe_round10'
LATER = ROOT / 'data/collection/us_europe_round9'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_row(page, label):
    line = next(line for line in page.splitlines() if label in line)
    return [value.replace(',', '') for value in re.findall(r'\d[\d,]*(?:\.\d+)?', line.split(label, 1)[1])][-3:]


early_file = EARLY / 'originals/guosen_nvidia_20240830.pdf'
later_file = LATER / 'originals/guosen_nvidia_20241122.pdf'
assert sha(early_file) == 'c9ec4666215fd6101f89be44958756c78579b3f41f58ca042b8a1d1b47b27962'
assert sha(later_file) == '64958bcbaf1d640082912327591a9ec6e44f3849f01b2cbff46fabeb61190834'
early = (EARLY / 'text/guosen_nvidia_20240830.txt').read_text().split('\f')
later = (LATER / 'text/guosen_nvidia_20241122.txt').read_text().split('\f')
assert '2024年08月30日' in re.sub(r'\s+', '', early[0])
assert '2024年11月22日' in re.sub(r'\s+', '', later[0])
assert re.search(r'我们维持盈利[^\n]*\n\s*预测', later[0])
assert early[4] == later[4], 'Complete physical-page5 model text differs'
vectors = {'eps': ('EPS（美元）', ['2.73', '3.64', '4.19']),
           'revenue': ('营业收入(百万美元)', ['123659', '164228', '184586']),
           'parent_net_profit': ('归母净利润(百万美元)', ['66997', '89375', '102903'])}
for label, values in vectors.values():
    assert numeric_row(early[0], label) == numeric_row(later[0], label) == values
review = dict(
    company_id='nvidia', firm='Guosen Securities', analyst_name='Zhang Lunke (张伦可)',
    later_source_url='https://pdf.dfcfw.com/pdf/H3_AP202411221641021029_1.pdf',
    later_source_file=str(later_file.relative_to(ROOT)), later_source_sha256=sha(later_file),
    later_report_date='2024-11-22', later_printed_numerical_model_date='',
    earlier_source_url='https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf',
    earlier_source_file=str(early_file.relative_to(ROOT)), earlier_source_sha256=sha(early_file),
    earlier_report_date='2024-08-30', earlier_printed_numerical_model_date='',
    recommended_model_age_basis_date='2024-08-30',
    fiscal_periods=['FY2025', 'FY2026', 'FY2027'],
    metrics=[dict(metric='eps', accounting_basis='guosen_latest_total_shares_eps', unit='USD_per_share', values=vectors['eps'][1]),
             dict(metric='revenue', accounting_basis='total_revenue', unit='USD_million', values=vectors['revenue'][1])],
    parent_net_profit_usd_million=vectors['parent_net_profit'][1],
    physical_pages_compared=[1, 5], complete_page5_text_identical=True,
    identical_page5_extracted_text_sha256=hashlib.sha256(early[4].encode()).hexdigest(),
    later_report_explicitly_maintains_forecasts=True,
    unchanged_report_date_and_original_availability=True,
    earlier_unprinted_model_date_not_inferred=True,
    evidence='November22 is a new quarterly commentary explicitly maintaining earnings forecasts and referencing August30. Current cover EPS/revenue/parent-profit vectors match in every target. The full physical-page5 financial-model extraction is identical, including all financial rows. Neither table prints a separate newer numerical-model date. Use August30 as the first evidenced age of this exact retained model; do not relabel the November report or backdate its historical dissemination.',
    recommendation='Apply only to the exact later source hash/company/firm/analyst/FY/metric/basis/value scope after central validation. Preserve all frozen raw observations and document the model-age override separately.')
(BASE / 'model_age_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(verified=True, complete_page5_text_identical=True, recommended_model_age_basis_date='2024-08-30', source_sha256=sha(later_file)), indent=2))
