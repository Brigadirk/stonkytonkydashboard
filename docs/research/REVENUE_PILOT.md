# First revenue comparison

September 10, 2026. This is an extraction and matching pilot, not a five-year analyst ranking or a trading backtest.

## Outcome sources

[issuer_outcomes.csv](../../data/issuer_outcomes.csv) contains 20 source-checked records. Ten are annual consolidated revenues for Samsung Electronics and SK hynix, FY2021–FY2025. Ten are Samsung basic/diluted EPS values retained for later accounting reconciliation.

Samsung figures come from physical PDF page 9 of each year's audited consolidated financial statements. Values are stored in base KRW, with EPS in KRW per share. Earnings announcement dates were checked on Samsung's official newsroom. The audited statement may have been issued later than the earnings announcement, so the data does not claim that the exact audited value was known on that announcement date. [Samsung FY2022 statement](https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2022_con_quarter04_all.pdf), [FY2022 earnings release](https://news.samsung.com/global/samsung-electronics-announces-fourth-quarter-and-fy-2022-results).

Hynix figures come from its original annual-results press releases, preserving the stated precision and initial-result status. FY2023 revenue is explicit in the issuer's Chinese newsroom copy. The event date follows the Seoul dateline because some page headers show the preceding UTC date. [Hynix FY2023 release](https://news.skhynix.com/cn/sk-hynix-reports-fourth-quarter-2023-financial-results/), [FY2024 release](https://news.skhynix.com/en/sk-hynix-announces-4q24-financial-results/).

This difference in result versions is explicit. Hynix initial revenue must not silently become a later audited/revised value. EPS remains unused in this comparison because broker denominators and accounting definitions are not reconciled. For example, the Samsung FY2022 audited statement reports basic/diluted EPS of KRW8,057; some broker tables describe a different per-share basis.

## Selection rule

For each company/year and analyst, take the latest collected revenue forecast printed strictly before a cutoff 180 or 365 days ahead of the detailed earnings release. Exclude same-day publications because exact availability is unverified. The printed report must be no more than 90 days old at the cutoff; this is a proposed pilot freshness rule, not a fitted threshold.

Exclude consensus, joint-team forecasts, unattributed forecasts and quarantined rows. Require the same company, fiscal target, currency and unit. Preserve the age of the report at the cutoff. Fail rather than select arbitrarily if two same-day records for one analyst/firm have conflicting values.

The script reports predicted revenue, issuer revenue, signed error and absolute percentage error. It does not average the errors into a leaderboard or assign portfolio weights. Source publication dates are assumptions supported by printed reports, not independently established historical availability.

## Result and limits

[revenue_pilot.csv](../../data/revenue_pilot.csv) contains 13 comparisons across eight company-years. Only some horizons have competing analysts, and the set of fiscal outcomes differs by analyst. Thirteen comparisons do not mean thirteen independent quarterly outcomes.

No contemporaneous consensus baseline has been matched to these pairs. Acquisition scope, historical publication evidence and other accounting issues remain to be checked. A small error on one memory-cycle outcome does not establish persistent analyst skill. These limitations prevent using the pilot to name a best analyst or claim a tradable forecasting advantage.

## Reproduce

```sh
python3 scripts/merge_forecasts.py
python3 scripts/build_korean_outcomes.py
python3 scripts/compare_revenue_pilot.py
```

The outcome builder verifies source hashes and the reviewed numbers against retained source text. Tests check that late, same-day, stale, consensus and joint-team records cannot enter the individual-forecast selection.
