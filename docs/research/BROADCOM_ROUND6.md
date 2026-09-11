# Broadcom history and EPS-basis review, round 6

Collected on 10 September 2026. This pass recovered **nine original Morningstar reports** from 73 bounded public archive candidates. Eight contain annual forecast tables, contributing **48 annual observations, including 24 EPS observations**. The ninth contains valuation commentary and historical financials but no annual forecast table, so it contributes no invented EPS forecast.

The useful additions are an earlier May 2022 model, a June 2024 numerical model absent from the prior collection, and additional original publication dates for existing models. The pass also preserves a July 2023 report whose current analyst note and valuation discussion are both signed William Kerwin. It does not retrospectively resolve the mixed authorship of the earlier June 2023 original.

Only the already proved December 2024 EPS definition could be extended to the three new January reprints. No new equivalence between an older Morningstar EPS forecast and issuer GAAP or issuer non-GAAP was established. These files improve the recorded history; they do not create additional valid accuracy comparisons by relaxing the accounting tests.

## Original models retained

Values are USD per share on the **printed** split basis. A later report date does not refresh an older numerical model.

| Printed report date | Numerical model date | Analyst | Fiscal periods | EPS vector | Physical table page |
|---|---|---|---|---|---|
| [27 May 2022](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P0000KU35_20220527_RT.pdf) | 26 May 2022 | Abhinav Davuluri | FY2022–FY2024 | 34.95 / 38.86 / 41.06 | 15 |
| [6 July 2023](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000KU35_20230706_RT.pdf) | 1 June 2023 | William Kerwin | FY2023–FY2025 | 42.66 / 44.16 / 47.11 | 15 |
| [22 November 2023](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000KU35_20231122_RT.pdf) | 31 August 2023 | William Kerwin | FY2023–FY2025 | 42.95 / 45.19 / 49.41 | 14 |
| [21 March 2024](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000KU35_20240321_RT.pdf) | 7 March 2024 | William Kerwin | FY2024–FY2026 | 48.03 / 64.66 / 76.82 | 14 |
| [15 July 2024](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000KU35_20240715_RT.pdf) | 24 June 2024 | William Kerwin | FY2024–FY2026 | 53.37 / 73.48 / 88.29 | 15 |
| [27 January 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250127_RT.pdf) | 12 December 2024 | William Kerwin | FY2025–FY2027 | 6.28 / 7.98 / 10.34 | 14 |
| [28 January 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250128_RT.pdf) | 12 December 2024 | William Kerwin | FY2025–FY2027 | 6.28 / 7.98 / 10.34 | 14 |
| [30 January 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250130_RT.pdf) | 12 December 2024 | William Kerwin | FY2025–FY2027 | 6.28 / 7.98 / 10.34 | 14 |

The [31 May 2024 original](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000KU35_20240531_RT.pdf) is supporting evidence only. Its new valuation discussion is not a substitute for an absent annual EPS table. Likewise, the November report discusses VMware's closing, while its annual table still prints the August model. The May 2022 report gives revenue in whole USD billions; those rounded values stay at the source's precision.

The eight forecast reports contain six distinct numerical model dates. The three January publications are reprints of one December model, not three earnings revisions. Earlier public archive checks around 2021 earnings dates did not recover usable originals. The existing December 2021 model remains quarantined: its revenue-year vector indicates a likely label shift, but its historical FY2021 EPS is also inconsistent. No speculative repair was imported.

## The July split-day report

The 15 July 2024 report mixes share bases across sections. On physical page 15, the historical financial table already shows FY2022/FY2023 diluted shares of 4,230m / 4,270m and reported EPS of 2.65 / 3.30. The forecast summary below it still shows historical shares of 423m / 427m, historical EPS of 37.64 / 42.25, forecast shares of 441m / 450m / 442m, and forecast EPS of 53.37 / 73.48 / 88.29. The forecast block is consequently on the pre-split basis; its original model date is 24 June. [Original, p15](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000KU35_20240715_RT.pdf).

`share_basis_date=2024-06-24` is retained with this table evidence, rather than inferred from the report date. The original values remain unchanged in the observations CSV. The application's existing split action can normalize them by 10, producing 5.337 / 7.348 / 8.829 on the post-split basis. The source table was visually reviewed and its rendering retained as `july_split_table_p15.png`. Broadcom's [issuer split announcement](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2024-financial) supplies the corporate-action context.

## Supported definition scope

The new January reports reproduce the exact December 12 model: FY2025/FY2026 EPS of 6.28 / 7.98, paired with revenue of USD62,340m / 75,219m. The already retained [3 April 2025 original, p15](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250403_RT.pdf) identifies its prior model date as 12 December 2024 and explicitly labels that matched vector adjusted diluted EPS. Its prior columns have rolled forward under current-year headers; fiscal identity comes from the earlier originals, not those shifted headings.

`basis_alias_recommendations.json` extends that evidence only to the three new January source hashes, William Kerwin at Morningstar, model date 2024-12-12, and FY2025/FY2026. It supports six EPS observations. FY2027 remains unresolved because its 10.34 value is outside the directly matched prior panel. The original legacy labels and all report/model dates are preserved. This is an extension of an established model definition to exact reprints; it is not a new proof for 2021–2023 or a blanket change to every legacy Broadcom row.

Several older valuation paragraphs describe a rounded non-GAAP or adjusted P/E multiple. They provide useful context but do not supply an exact dated EPS vector or exclusion definition. Some valuation paragraphs also have different dates from the numerical model. No automatic alias was created from rounded P/E arithmetic. In particular, the [March 2023 report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000KU35_20230302_RT.pdf) calls its standalone valuation a non-GAAP P/E, while the table's EPS row does not separately document its adjustment policy. That evidence cannot be stretched into issuer non-GAAP compatibility for every annual forecast.

## Why equal historical EPS is insufficient

There is a concrete denominator discrepancy. Broadcom's initial FY2024 release reports issuer non-GAAP EPS of 4.87, non-GAAP net income of USD23,733m and non-GAAP diluted shares of 4,877m; GAAP diluted shares are 4,778m. The Morningstar December model also shows historical FY2024 EPS of 4.87, but its net-income figure is USD23,251m and its diluted-share count is 4,778m. The matching EPS therefore does not establish that the forecast calculation uses the issuer's non-GAAP numerator and denominator. [Issuer release, reconciliation table 9](https://www.prnewswire.com/news-releases/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2024-financial-results-and-quarterly-dividend-302330736.html), [Morningstar January original, p14](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250130_RT.pdf).

This does not prove every forecast will differ; it proves that identical definitions have not been demonstrated. `issuer_compatibility_review.json` retains the exact figures, source hashes and locators. Morningstar-adjusted versus issuer non-GAAP comparisons should stay excluded from analyst accuracy scoring until a forecast-specific definition or reconciliation is available.

Two primary methodology documents were also retained. Morningstar's [2020 global equity definitions](https://advisor.morningstar.com/Enterprise/VTC/DataDefinitionsEquityandExecutive2020.09.08.pdf), physical p98, describes normalized EPS; p131 separately describes reported and adjusted consensus estimate fields. Its [2018 product training manual](https://advisor.morningstar.com/AWSOE/Training/WMCloud/MarketsMonitoring.pdf), physical p29, demonstrates a Morningstar EPS estimate line. Neither explicitly maps each old proprietary analyst PDF field to an invariant Broadcom calculation. They are retained as methodology, not counted as broker forecasts or used to authorize broad aliases.

## Limits and files

This pass did not establish additional issuer-compatible forecast/actual pairs. It improved publication coverage and preserved the evidence needed to identify unresolved gaps. Five-year analyst scoring and trading backtests still require original availability evidence, sufficient comparable annual forecasts, and accounting definitions. A public report's printed date is not an independently verified historical distribution log; all `original_available_at` fields remain blank. Reprints preserve their older numerical model date, so they cannot evade the application's 90-day model-age limit.

All additions are in [data/collection/broadcom_round6](../../data/collection/broadcom_round6). `manifest.csv` and `observations.csv` use the existing collection schemas, with repo-relative files, original SHA-256 hashes, exact printed report timestamps, model dates, fiscal labels, source pages and printed share bases. `download_log.json` records all 73 bounded archive candidates. `finalize.py` reproduces the CSVs and source-scoped alias recommendation offline, checking all reviewed EPS vectors, fiscal labels and original hashes. `validation.json` records counts and checks; `issuer_compatibility_review.json` and `rejected_basis_candidates.json` preserve both the positive evidence and rejected extrapolations. The two methodology PDFs have a separate supporting-source manifest.

Searches also encountered a user-translated CFRA attachment and SureDividend reports offering a current-year EPS estimate plus a distant five-year target. Neither supplied the original adjacent-year history sought here. No machine translation, distant-target interpolation, secondary quotation or current consensus estimate was substituted for a missing historical analyst model. No paid subscription, scraping credit, provider contact or external message was used.
