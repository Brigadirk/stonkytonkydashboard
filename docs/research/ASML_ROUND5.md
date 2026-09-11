# ASML: fresh EUR models and historical gaps

Collected 10 September 2026. The highest-priority gap is resolved at source level: an original Morningstar model dated **15 July 2026** supplies annual EPS forecasts in **EUR**, including FY2026 **37.12** and FY2027 **51.67**. The financial summary explicitly prints both diluted EPS and adjusted diluted EPS; their values happen to agree, but the two definitions remain separately stored. [Original report, p15](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260715_RT.pdf)

## Delivered collection

Retained **26 original PDFs**. The new [observations](../../data/collection/asml_round5/observations.csv) contain **147 rows**, of which **141 are not quarantined: 83 EPS forecasts and 58 revenue forecasts**. These cover **16 model dates**. Six rows with a shifted fiscal header remain quarantined. The [manifest](../../data/collection/asml_round5/manifest.csv) also records 15 failed archive-date probes, for 41 records total.

The source is the original Morningstar report distributed by Firstrade, not a third-party paraphrase. Morningstar's [ASML ADR report index](https://www.morningstar.com/company-reports?listing=0P0000002X) verifies identifier **0P0000002X**; the [Amsterdam index](https://www.morningstar.com/company-reports?listing=0P0000ALDL) separately verifies **0P0000ALDL**. The retrieved US-distributed PDFs explicitly use **EUR reporting currency** and **USD trading currency**. Their annual EPS and revenue tables are in EUR, so they can supply the Amsterdam earnings series without inventing an FX conversion. USD price targets and market prices printed elsewhere in the reports are not extracted as earnings.

## Explicitly defined recent EPS models

Each model below supplies five annual forecast years, plus revenue. All are attributed to **Javier Correonero**. Both `reported_diluted` and `adjusted_diluted` are retained; equal values do not collapse their distinct definitions.

| Model and printed report date | Forecast years | First two annual EPS values, EUR | Original, physical page |
|---|---|---|---|
| 2025-04-16 | FY2025–FY2029 | 24.11 / 30.08 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250416_RT.pdf), p15 |
| 2025-10-15 | FY2025–FY2029 | 23.72 / 25.51 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20251015_RT.pdf), p15 |
| 2026-01-07 | FY2026–FY2030 | 26.21 / 34.10 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260107_RT.pdf), p15 |
| 2026-04-15 | FY2026–FY2030 | 29.10 / 38.20 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260415_RT.pdf), p15 |
| 2026-07-15 | FY2026–FY2030 | 37.12 / 51.67 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260715_RT.pdf), p15 |

These are named analyst forecasts. They must not be merged into Hana's Bloomberg consensus series from the previous collection. Their full printed UTC report timestamps are preserved, as are the separate model dates.

## Historical models with less specific EPS definitions

Older Morningstar summaries explicitly label diluted EPS but do not separately define adjustments. These use `eps_diluted_basis_unresolved` and `diluted_adjustment_basis_unresolved`. They can support a separately labelled history; they cannot silently become the same basis as the later explicitly reported or adjusted EPS rows. Their revenue can be compared independently, provided units and source precision are respected.

| First retained report date | Model date | Author | Forecast years | First two EPS values, EUR | Original, page |
|---|---|---|---|---|---|
| 2022-04-20 | 2022-01-19 | Abhinav Davuluri | FY2022–FY2024 | 17.64 / 20.20 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P0000002X_20220420_RT.pdf), p15 |
| 2022-05-15 | 2022-04-20 | Abhinav Davuluri | FY2022–FY2024 | 16.58 / 19.31 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P0000002X_20220515_RT.pdf), p15 |
| 2022-07-20 | 2022-07-20 | Abhinav Davuluri | FY2022–FY2024 | 13.49 / 18.18 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P0000002X_20220720_RT.pdf), p15 |
| 2023-04-19 | 2023-02-15 | Abhinav Davuluri | FY2023–FY2025 | 18.32 / 21.57 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000002X_20230419_RT.pdf), p15 |
| 2023-05-26 | 2023-05-25 | William Kerwin | FY2023–FY2025 | 18.54 / 21.60 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000002X_20230525_RT.pdf), p14 |
| 2023-11-20 | 2023-11-20 | Javier Correonero | FY2023–FY2025 | 18.67 / 22.16 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000002X_20231120_RT.pdf), p15 |
| 2024-04-17 | 2024-04-17 | Javier Correonero | FY2024–FY2026 | 21.70 / 28.83 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20240417_RT.pdf), p15 |
| 2024-06-05 | 2024-06-05 | Javier Correonero | FY2024–FY2026 | missing / 28.62 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20240605_RT.pdf), p16 |
| 2024-07-17, new cell only | 2024-06-05 | Javier Correonero | FY2024 EPS only | 21.65 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20240717_RT.pdf), p16 |
| 2024-10-16 | 2024-10-15 | Javier Correonero | FY2024–FY2026 | 18.83 / 23.38 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20241015_RT.pdf), p15 |
| 2025-01-03 | 2024-11-06 | Javier Correonero | FY2024–FY2026 | 18.86 / 23.75 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250103_RT.pdf), p15 |
| 2025-01-30 | 2025-01-29 | Javier Correonero | FY2025–FY2027 | 24.69 / 30.87 | [Report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250130_RT.pdf), p15 |

The first three reports print annual revenue rounded to whole **EUR billions**. That unit and precision are preserved. Later summaries use **EUR millions**. Revenue values were not silently assigned extra precision, and EPS was never reconstructed from P/E or net income divided by rounded shares.

## Copied tables, missing values and quarantines

Seven fully repeated tables produce no additional observations. Examples include July 2025 retaining April 2025's model and January 28, 2026 retaining January 7's model. A new commentary or report date is not evidence of a new earnings model. Later revision tables mention additional changes, but those mentions do not prove that the earlier retained PDF contained the revised forecast. [July 2025 report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250716_RT.pdf), [January 2026 report](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260128_RT.pdf)

June 5, 2024 prints a dash for FY2024 EPS. July 17 prints 21.65 under the same June 5 model date. Only that newly visible cell is added from July 17. Its first retained report timestamp remains July 17; the value is not filled into the earlier June report. This allows the app to preserve both model age and observed report vintage.

The [January 25, 2023 report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P0000002X_20230125_RT.pdf), p15, has a shifted forecast-table header. It labels historical revenue 13,979/18,611 and EPS 8.48/14.34 as 2021/2022, while the historical table on that same page identifies them as 2020/2021. Its model date is October 19, 2022. All six forecast cells are quarantined with the printed fiscal labels preserved. This pass does not repair those years by inference. The original October 19 report was also retained but contains no annual model summary.

## Discovery and verification

The correct Morningstar identifier unlocked Firstrade's public report archive. Initial requests followed dates on the publisher's report index. Follow-ups used explicit historical note/model dates in retained reports and the immediately adjacent US/UTC archive date where publication crossed midnight. Failed probes are retained in the manifest. No credentials, subscription, ScrapingBee credits or external messages were needed. Prior ASML/Sandisk collection files were not edited.

[Validation](../../data/collection/asml_round5/validation.json) checks all 26 PDF hashes, source references, named attribution, EUR units, date order, unique observation IDs and every annual source-table value/column. Visual checks covered the recent July model, older billion-unit table, shifted January 2023 header, and June 2024 missing cell. The extractor and retained [reviewed models](../../data/collection/asml_round5/reviewed_models.json) preserve the exact source lines for inspection.

Historical `original_available_at` remains blank. Printed timestamps are evidence about the reports' stated dates, not independently verified first dissemination times. A model first retained in a later report cannot be made available on its earlier model date. These additions improve coverage and enable further evaluation, but do not establish a complete monthly revision history or an analyst accuracy ranking. Scoring must keep the three named contributors and the EPS bases separate, and compare forecasts with an explicitly matched outcome definition.
