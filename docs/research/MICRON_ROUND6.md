# Micron historical models and accounting bridges — round 6

Collected and reviewed on 10 September 2026. This pass retains **12 original Morningstar/Firstrade PDFs and one official Micron 10-K**, following 73 bounded broker URL checks. Eight selected reports supply **55 annual forecast observations: 30 EPS and 25 revenue**. Four redundant reprints remain in the source manifest without duplicating forecast rows. Every retained PDF has a SHA-256 hash and extracted text; numerical rows cite physical PDF pages. `data/collection/micron_round6/finalize.py` reproduces the reviewed CSVs and asserts the accounting bridges against both originals.

The useful extension is a newly recovered **21 March 2025 report**. Its current model remains dated **18 December 2024**, while its revision panel preserves the **25 September 2024** model. Explicit adjusted diluted EPS and revenue vectors match the older originals exactly for **FY2025–FY2027**, supporting source- and model-specific aliases for both vintages. This extends the earlier round's December bridge through FY2027 and adds the September vintage. [March report, physical pages 13–14](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250321_RT.pdf).

## Source-backed forecast history added

All EPS below is USD per share, retained as printed. “Legacy unresolved” means the table says diluted EPS without establishing reported versus adjusted accounting. It does not become issuer non-GAAP merely because historical actuals resemble Micron's non-GAAP outcomes.

| Printed report date | Numerical model date | Author | Targets and EPS | Source and physical page |
|---|---|---|---|---|
| 13 May 2022 | 12 May 2022 | Abhinav Davuluri | FY2022/23/24: 9.13 / 8.24 / 8.55; legacy unresolved | [Original, p14](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003MC_20220513_RT.pdf) |
| 22 December 2022 | 29 September 2022 | Abhinav Davuluri | FY2023/24: 1.05 / 2.82; legacy unresolved | [Original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003MC_20221222_RT.pdf) |
| 30 March 2023 | 28 March 2023 | Abhinav Davuluri | FY2023/24/25: −4.45 / 1.84 / 4.50; legacy unresolved | [Original, p14](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003MC_20230329_RT.pdf) |
| 25 May 2023 | 25 May 2023 | William Kerwin | FY2023/24/25: −4.43 / 1.83 / 4.48; legacy unresolved | [Original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003MC_20230525_RT.pdf) |
| 22 December 2023 | 20 December 2023 | William Kerwin | FY2024/25/26: 0.03 / 5.73 / 6.91; legacy unresolved | [Original, p14](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003MC_20231221_RT.pdf) |
| 15 August 2024 | 1 July 2024 | William Kerwin | FY2024/25/26: 1.18 / 8.61 / 11.29; legacy unresolved | [Original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240815_RT.pdf) |
| 26 September 2024 | 25 September 2024 | William Kerwin | FY2025/26/27: 8.47 / 11.03 / 10.58; adjusted diluted proven by later revision panel | [Original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240926_RT.pdf) |
| 21 March 2025 | 18 December 2024 | William Kerwin | FY2025–29 reported: 5.25 / 6.23 / 7.74 / 8.72 / 9.57; adjusted: 5.79 / 7.14 / 8.75 / 9.81 / 10.74 | [Original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250321_RT.pdf) |

The May 2022 and May 2023 originals establish earlier report dates than the July 2022 and June 2023 reprints already retained. The August 2024 original similarly precedes the September reprints of the July model. More recent cover commentary does not change an old model's date. [May 2022](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003MC_20220513_RT.pdf), [May 2023](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003MC_20230525_RT.pdf), [August 2024](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240815_RT.pdf).

The May 2022 source rounds revenue to whole USD billions: 33 / 32 / 34. Its later reprint has finer precision. That later precision is not silently imported into the earlier report's observations. The September 2022 model still puts FY2022 revenue 30,758 million and EPS 8.35 under a stale “Estimates” bracket, despite those annual results having already been released. Those two completed-period cells are documented in `excluded_completed_period_columns.json` and excluded from forecasts. [May source, p14](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003MC_20220513_RT.pdf), [December source, p13](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003MC_20221222_RT.pdf), [Micron's initial FY2022 results](https://investors.micron.com/news/press-release/2022/Micron-Technology-Inc--Reports-Results-for-the-Fourth-Quarter-and-Full-Year-of-Fiscal-2022-09-29-2022/default.aspx).

## Exact accounting-definition bridges

`basis_alias_recommendations.json` restricts every recommendation by company, firm, analyst, original source hash, model date and fiscal target. The raw legacy labels remain in `observations.csv`.

| Original model | Original EPS FY2025 / FY2026 / FY2027 | Original revenue, USD millions | Explicit supporting table |
|---|---|---|---|
| 25 September 2024 | 8.47 / 11.03 / 10.58 | 37,466 / 42,370 / 44,161 | 21 March 2025, p14: prior model dated 25 September 2024, adjusted diluted EPS row |
| 18 December 2024 | 5.79 / 7.14 / 8.75 | 32,759 / 36,101 / 39,669 | 21 March 2025, p13: current model dated 18 December 2024, adjusted diluted EPS row |

All three fiscal headings align directly in this earlier evidence artifact. Unlike the April 2025 revision panel used in round 5, there is no rolled-header correction here. The September legacy original's October month label is wrong, but its annual year identities are clear from the historical revenue anchors; the issuer's August fiscal calendar governs. [September original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240926_RT.pdf), [December original, p13](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20241218_RT.pdf), [March evidence, pp13–14](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250321_RT.pdf).

Two January 2025 originals reprint the same December model and are included in the recommendation's source scope, without adding redundant observations. [27 January](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250127_RT.pdf), [28 January](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250128_RT.pdf).

**Availability remains separate from definition.** The new explicit reported EPS and FY2028/29 targets first appear in this retained March 2025 artifact. They are not reconstructed as December 2024 observations. The prior revision panel is evidence for the meaning of already retained older forecasts; it is not exported as a new forecast with assumed September availability. `available_at` and `original_available_at` remain blank throughout. Printed report timestamps are retained separately.

## Issuer comparability and fiscal identity

The evidence supports **Morningstar adjusted diluted**, not issuer non-GAAP equivalence. There is a concrete reason to keep them distinct: Morningstar's FY2024 adjusted historical net income is **1,453 million**, with a single printed diluted share count of **1,118 million**; Micron's initial FY2024 release reports **1,472 million non-GAAP net income** and **1,134 million non-GAAP diluted shares**, including 16 million shares from its stock-compensation adjustment. Both nevertheless display EPS of **1.30**. Matching rounded historical EPS therefore does not establish identical numerator or denominator definitions. [Morningstar model, p13](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250321_RT.pdf), [Micron's initial FY2024 release, GAAP-to-non-GAAP reconciliation](https://investors.micron.com/news/press-release/2024/Micron-Technology-Inc--Reports-Results-for-the-Fourth-Quarter-and-Full-Year-of-Fiscal-2024-09-25-2024/default.aspx).

Micron's fiscal year ends on the Thursday closest to August 31. The official FY2024 10-K, physical page 5, states this 52/53-week convention. The September 2024 broker table's historical revenues identify FY2023 at 15,540 million and FY2024 at 25,111 million; those exact year labels are retained even though its month heading says October. No year shift is applied to any newly extracted model in this pass. Values remain in their printed share basis and no split conversion is performed. [Official 10-K, p5](https://s25.q4cdn.com/621799436/files/doc_financials/2024/ar/2024-10K.pdf), [broker table, p13](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240926_RT.pdf).

## Remaining public-source gaps

No new 2021 original was recovered. The known September 2021 model remains evidenced by the December 2021 reprint from round 4. Bounded checks around the 2021 report dates returned 404; the Morningstar report on Yahoo identifies the September 29, 2021 publication but requires an upgrade for its full report. It was used only to identify the boundary, with no subscription or access bypass. [Existing December original](https://invest.firstrade.com/ms/equity_reports/sr/2021/0P000003MC_20211220_RT.pdf), [Yahoo's dated Morningstar report listing](https://finance.yahoo.com/research/reports/MS_0P000003MC_AnalystReport_1632887028000).

Models before 25 September 2024 still lack source-specific accounting evidence. Historical actual matches, adjusted-P/E narrative and generic normalization definitions cannot resolve those model definitions. Consequently this pass extends the verified adjusted series only to the September 2024 vintage; the additional 2022–2024 legacy models remain available for research while their accounting labels are unresolved. Negative EPS is preserved, and the loss values must not be forced into a positive P/E calculation.

## Retained validation

The offline finalizer verifies every retained source hash, model date, fiscal heading, selected numerical row, exact bridge vector and blank availability field. Critical original pages were rendered and visually reviewed: the March 2025 current and revision tables, September 2024 legacy table, September 2022 stale bracket, May 2022 rounded revenue, March 2023 loss and December 2023 near-zero EPS. Renderings are under `data/collection/micron_round6/review/`. `validation.json` records the collection totals; `download_log.json` records successful and failed public URL attempts. No paid service, account or external message was used.
