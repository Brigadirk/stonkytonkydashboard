# Apple forecast history — round 5

Collected 10 September 2026. Files are stable and ready for the shared import.

## Result

Retained 29 original Morningstar PDFs and 5 Apple earnings-release statement PDFs. The broker originals contain 25 numerical-model reports spanning 20 distinct model dates; the extraction retains 227 forecast observations: 136 annual EPS values and 91 annual revenue values. Repeated models remain in the source archive for provenance and must be deduplicated by the shared panel builder. Four October/November 2022 originals contain narrative analysis but no numerical forecast table. The separate `issuer_outcomes.csv` archive contains 10 initial annual results (reported diluted EPS and revenue for FY2021–2025). `issuer_eps_outcomes.csv` contains only the five reported diluted EPS outcomes in the evaluation schema; verified release dates are retained, while actual availability timestamps remain blank because no intraday dissemination evidence was established. No paid account, proxy service or subscription was used.

## Identity, calendar and split basis

- [Morningstar company reports](https://www.morningstar.com/company-reports?listing=0P000000GY) identifies Apple Inc., AAPL, with listing `0P000000GY`; dated Firstrade distributor paths were tested only after verifying this identity.
- [Apple’s official fiscal-calendar accounting note](https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm) states that its fiscal year ends on the last Saturday of September. Apply this rule, including 53-week years such as FY2023. Broker tables use nominal September 26/30 headers; annual years match issuer revenue anchors, so no year shift was applied.
- [Apple’s split announcement](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/) says split-adjusted trading began August 31, 2020 for the four-for-one split. All retained models are after that event; no additional split transformation is needed for this collection.

## Accounting and availability

The legacy model table labels only diluted earnings per share. Its adjustment definition is not fully established and remains `diluted_adjustment_basis_unresolved`. Modern models explicitly print separate `reported_diluted` and `adjusted_diluted` EPS rows, which remain separate even when their future estimates coincide. No EPS was backed out of a target price, valuation multiple, broker headline or current estimate.

The model date comes from the numerical financial table, often months before the report date. Printed report timestamps are retained but historical first-publication availability is unverified; use the project’s conservative next-day convention, not the path date or current analyst-note date. The direct [Morningstar-hosted July 2021 report](https://advisor.morningstar.com/Enterprise/VTC/MorningstarEquityAnalystReport.pdf) contains an April 28, 2021 numerical model; it does not establish April availability.

The November 30, 2023 report cover and sections are signed William Kerwin, but its numerical table is an exact reprint of Brian Colello’s November 2 model in the [November 3 original](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20231103_RT.pdf). The raw forecast rows retain Colello as model author and explicitly document this cover/model distinction. The extraction asserts that all EPS and revenue vectors match. A new author is not credited with an old model. Other retained report/model author pairs are consistent across signed report sections.

Fiscal periods already completed by the numerical model date are excluded from forecast rows. In particular, the November 2023 legacy table still places FY2023 below an “Estimates” heading although its values equal the newly released actuals. Those values are not recast as future forecasts.

## Model inventory

| Printed report date | Numerical model date | Model author | Physical page | Original |
|---|---|---|---:|---|
| 2021-07-15 | 2021-04-28 | Abhinav Davuluri | 15 | [PDF](https://advisor.morningstar.com/Enterprise/VTC/MorningstarEquityAnalystReport.pdf) |
| 2022-01-28 | 2022-01-27 | Abhinav Davuluri | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000000GY_20220128_RT.pdf) |
| 2022-04-29 | 2022-01-27 | Abhinav Davuluri | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000000GY_20220428_RT.pdf) |
| 2022-07-29 | 2022-04-28 | Abhinav Davuluri | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000000GY_20220728_RT.pdf) |
| 2023-02-03 | 2023-02-02 | Abhinav Davuluri | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20230202_RT.pdf) |
| 2023-05-05 | 2023-03-04 | Abhinav Davuluri | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20230504_RT.pdf) |
| 2023-08-04 | 2023-08-03 | Brian Colello | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20230803_RT.pdf) |
| 2023-08-04 | 2023-08-03 | Brian Colello | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20230804_RT.pdf) |
| 2023-11-03 | 2023-08-03 | Brian Colello | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20231102_RT.pdf) |
| 2023-11-03 | 2023-11-02 | Brian Colello | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20231103_RT.pdf) |
| 2023-11-30 | 2023-11-02 | Brian Colello | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000000GY_20231130_RT.pdf) |
| 2024-02-02 | 2023-11-30 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000000GY_20240201_RT.pdf) |
| 2024-06-10 | 2024-05-06 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000000GY_20240610_RT.pdf) |
| 2024-08-02 | 2024-06-28 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000000GY_20240801_RT.pdf) |
| 2024-11-01 | 2024-10-31 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000000GY_20241031_RT.pdf) |
| 2025-01-31 | 2024-11-01 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000000GY_20250130_RT.pdf) |
| 2025-05-02 | 2025-02-03 | William Kerwin | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000000GY_20250502_RT.pdf) |
| 2025-08-01 | 2025-07-31 | William Kerwin | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000000GY_20250801_RT.pdf) |
| 2025-10-31 | 2025-10-30 | William Kerwin | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000000GY_20251030_RT.pdf) |
| 2026-01-30 | 2026-01-29 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260129_RT.pdf) |
| 2026-05-01 | 2026-04-30 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260430_RT.pdf) |
| 2026-06-18 | 2026-06-18 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260618_RT.pdf) |
| 2026-07-08 | 2026-06-18 | William Kerwin | 16 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260708_RT.pdf) |
| 2026-08-04 | 2026-07-30 | William Kerwin | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260804_RT.pdf) |
| 2026-09-09 | 2026-09-09 | William Kerwin | 15 | [PDF](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000000GY_20260909_RT.pdf) |

## Initial issuer outcomes

| Fiscal year | Period end | First annual-results release | Revenue, USD million | Reported diluted EPS, USD | Source |
|---|---|---|---:|---:|---|
| FY2021 | 2021-09-25 | 2021-10-28 | 365817 | 5.61 | [Release](https://www.apple.com/newsroom/2021/10/apple-reports-fourth-quarter-results/), [statements p.1](https://www.apple.com/newsroom/pdfs/FY21_Q4_Consolidated_Financial_Statements.pdf) |
| FY2022 | 2022-09-24 | 2022-10-27 | 394328 | 6.11 | [Release](https://www.apple.com/newsroom/2022/10/apple-reports-fourth-quarter-results/), [statements p.1](https://www.apple.com/newsroom/pdfs/FY22_Q4_Consolidated_Financial_Statements.pdf) |
| FY2023 | 2023-09-30 | 2023-11-02 | 383285 | 6.13 | [Release](https://www.apple.com/newsroom/2023/11/apple-reports-fourth-quarter-results/), [statements p.1](https://www.apple.com/newsroom/pdfs/fy2023-q4/FY23_Q4_Consolidated_Financial_Statements.pdf) |
| FY2024 | 2024-09-28 | 2024-10-31 | 391035 | 6.08 | [Release](https://www.apple.com/newsroom/2024/10/apple-reports-fourth-quarter-results/), [statements p.1](https://www.apple.com/newsroom/pdfs/fy2024-q4/FY24_Q4_Consolidated_Financial_Statements.pdf) |
| FY2025 | 2025-09-27 | 2025-10-30 | 416161 | 7.46 | [Release](https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/), [statements p.1](https://www.apple.com/newsroom/pdfs/fy2025-q4/FY25_Q4_Consolidated_Financial_Statements.pdf) |

The [FY2025 issuer statement](https://www.apple.com/newsroom/pdfs/fy2025-q4/FY25_Q4_Consolidated_Financial_Statements.pdf) prints annual diluted EPS **7.46**, while Morningstar’s later historical model rows print **7.47**. The issuer value governs the outcome file; do not substitute broker historical EPS. FY2024 reported diluted EPS is **6.08** and differs from the company’s adjusted **6.75** after the one-time tax charge. The outcome file deliberately contains reported EPS, so adjusted forecasts require a separately verified comparison basis.

## Remaining gaps and next searches

- The earliest recovered report is July 2021 but its model is April 2021; a fresh September/October 2021 model was not recovered from the bounded public paths. January 2022 is the next verified model.
- Missing late-2022 numerical tables are a real archive gap: four recovered reports have no model section. Further dated originals around July/October 2022 would improve continuity.
- Some 2024/early-2025 reports reprint stale models. The raw model dates preserve those gaps rather than resetting forecast age to the new cover date.
- The September 9, 2026 model is retained, but its conservative next-day availability is September 10; a chart whose price cutoff is September 9 should still use the earlier July 30 model.
- Legacy/modern adjustment reconciliation and author comparison require explicit basis evidence. This collection does not establish a “best analyst” ranking.

## Reproduction and checks

`python3 data/collection/apple_round5/finalize.py` rebuilds `manifest.csv`, `observations.csv`, `issuer_outcomes.csv`, `issuer_eps_outcomes.csv`, `model_review.json` and `summary.json` offline from retained PDFs/text and download metadata. The script verifies every source hash, report/model chronology, fiscal target validity, exact initial-outcome row values, observation uniqueness and the author-transition duplicate vectors. `validation.json` records physical-page bounds and representative visual checks. `download_log.json` records all successful and unsuccessful bounded public requests; 404s are not treated as paywalls.
