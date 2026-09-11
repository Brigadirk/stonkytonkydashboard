# US and Europe public forecast history — round 9

Collected September 10, 2026. This bounded pass retains **16 original broker PDFs** and **111 annual forecast rows**: **102 verified source rows and 9 quarantined rows**. These are extractions and earlier documented appearances, not 111 independent predictions. Morningstar contributes 75 rows; Guosen 24; Southwest 6; Raiffeisen 6. The corpus includes 64 EPS rows and 47 revenue rows. No new issuer outcomes or Morningstar accounting aliases were added.

The source files, SHA-256 hashes, download logs, extraction code, physical-page renderings and CSVs are in `data/collection/us_europe_round9/`. `finalize.py` reproduces the extraction offline and asserts complete target-year vectors against retained text. `validation.json` records the checks. No shared datasets, app code or existing collection sources were edited.

## Earlier Morningstar appearances and newly recovered models

All links below are original Morningstar-authored reports served by Firstrade. Dates are the **printed report date** and **numerical model date**, not the filename date. EPS values retain the source's currency and share units. Revenue vectors are also extracted, in printed USD/EUR millions. Physical PDF page numbers are one-based.

| Company | Printed report | Model | Analyst | Target EPS | Physical page / original |
|---|---|---|---|---|---|
| Broadcom | 2025-06-06 02:44 UTC | 2025-06-05 | William Kerwin | FY2025–29 plain 4.37 / 5.85 / 8.55 / 10.60 / 12.33; adjusted 6.68 / 8.41 / 11.38 / 13.59 / 15.44 | [p14](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250605_RT.pdf) |
| Apple | 2024-05-07 16:21 UTC | 2024-05-06 | William Kerwin | FY2024–26 diluted 6.56 / 7.74 / 8.75 | [p16](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000000GY_20240507_RT.pdf) |
| Alphabet | 2023-04-26 12:44 UTC | 2023-02-02 | Ali Mogharabi | FY2023–25 diluted 4.36 / 5.51 / 6.36 | [p17](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000002HD_20230426_RT.pdf) |
| Alphabet | 2024-01-31 05:29 UTC | 2024-01-30 | Ali Mogharabi | FY2024–26 diluted 6.23 / 7.38 / 8.48 | [p16 header/revenue; p17 EPS](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000002HD_20240130_RT.pdf) |
| Alphabet | 2024-03-18 20:51 UTC | 2024-03-04 | Michael Hodel | FY2024–26 diluted 6.67 / 7.48 / 8.15 | [p14](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000002HD_20240318_RT.pdf) |
| ASML | 2024-11-15 11:49 UTC | 2024-11-06 | Javier Correonero | FY2024–26 diluted EUR 18.86 / 23.75 / 29.84 | [p15](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20241115_RT.pdf) |
| Alphabet | 2025-05-08 02:42 UTC | 2025-04-24 | Malik Ahmed Khan | FY2025–29 plain and adjusted both 10.34 / 11.19 / 12.61 / 13.96 / 15.47 | [p19](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000002HD_20250507_RT.pdf) |
| Micron | 2025-04-03 23:43 UTC | 2025-03-20 | William Kerwin | FY2025–29 plain 5.76 / 5.71 / 6.65 / 7.78 / 9.52; adjusted 6.28 / 6.66 / 7.68 / 8.89 / 10.72 | [p13](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250403_RT.pdf) |

The final two originals were already retained in `us_evaluation_round5` as definition evidence but had no observations extracted from their current models. Round 9 copies their identical hashed originals and adds their forecasts. This moves the documented appearance of Alphabet's April 2025 model and Micron's March 2025 model earlier in the collected history. Broadcom's June 2025 model supplies a closer original plain-diluted forecast before the FY2025 result; shared evaluation should determine its eligible horizon. No historical availability timestamp has been invented for any of these reports.

Two further originals have identical full revenue/EPS vectors and model dates and are retained only as corroboration: [Broadcom June 6, 2025 22:31 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250606_RT.pdf), and [Alphabet February 1, 2024 00:46 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000002HD_20240131_RT.pdf). The earlier originals supply the observations.

The five legacy models retain `diluted_adjustment_basis_unresolved`. The three modern US models have separate printed plain and adjusted rows; they retain `reported_diluted` and Morningstar-specific `adjusted_diluted`, respectively. No adjusted row is equated to issuer non-GAAP earnings.

## New named non-Morningstar models

These are intact original broker documents on East Money's public PDF host. The PDFs identify their originating firm, report date, authors and analyst registration numbers. East Money is the retained host, not the author. Download dates and filename dates are not used as historical publication evidence.

| Originating broker | Printed report | Named analyst(s) | Normalized fiscal years and EPS | Original |
|---|---|---|---|---|
| Guosen Securities | 2024-11-22 | Zhang Lunke (张伦可) | FY2025–27 USD 2.73 / 3.64 / 4.19 | [p1, full model p5](https://pdf.dfcfw.com/pdf/H3_AP202411221641021029_1.pdf) |
| Guosen Securities | 2025-02-28 | Zhang Lunke (张伦可) | FY2026–28 USD 4.21 / 5.42 / 6.26 | [p1, full model p5](https://pdf.dfcfw.com/pdf/H3_AP202502281643606379_1.pdf) |
| Guosen Securities | 2025-05-30 | Zhang Lunke (张伦可) | FY2026–28 USD 4.15 / 5.54 / 6.33; **EPS quarantined** | [p1, conflicting model p5](https://pdf.dfcfw.com/pdf/H3_AP202505301681759010_1.pdf) |
| Guosen Securities | 2026-02-27 | Zhang Lunke; Liu Zitan (刘子谭); Zhang Haochen (张昊晨) | FY2027–29 USD 8.72 / 10.71 / 12.60 | [p1, full model p4](https://pdf.dfcfw.com/pdf/H3_AP202602271820103939_1.pdf?1772214464000.pdf) |
| Southwest Securities | 2026-01-30 | Wang Xiangjie (王湘杰); Yang Zhenyu (杨镇宇) | FY2026–28 EUR 30.94 / 37.46 / 41.29 | [p1, full model p8](https://pdf.dfcfw.com/pdf/H3_AP202602031819644752_1.pdf) |

Guosen identifies the annual table as its own research institute's forecasts and states that EPS uses latest total share capital. Liu Zitan is only a **contact** in the 2024–25 reports; he is a registered coauthor in February 2026. The joint 2026 model is one research team's forecast, not three independent votes. Changes in byline must not create multiple contributors from the same Guosen research stream.

The three unconflicted Guosen reports consistently use parent-attributable net profit in both the cover forecast table and full income statement. Exact forecast numerator vectors, USD millions, are 66,997 / 89,375 / 102,903; 102,722 / 132,155 / 152,779; and 211,996 / 260,299 / 306,089. Together with the repeated latest-total-share EPS definition, this supports the **narrow company/firm/source-scoped `guosen_latest_total_shares_eps` stream** across the sole and joint authors. `guosen_definition_review.json` contains the three source hashes, report dates, authors, fiscal periods, EPS vectors, numerator vectors and physical pages. This is not a broad equivalence rule for all Guosen publications, all parent-profit measures, or other firms.

Guosen's historical FY2026 EPS is 4.94, whereas NVIDIA's [initial issuer release reports diluted EPS of 4.90](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026). The latest-share denominator therefore cannot be scored against issuer weighted-average diluted EPS or pooled with Morningstar's reported-diluted series. Historical net-income agreement alone does not remove that denominator difference.

**May 30, 2025 exception:** p5 has two parent-profit rows with different FY2026–28 vectors: 101,341 / 135,182 / 154,473 versus 100,283 / 131,184 / 146,780. The cover repeats the latter. No text reconciles the difference or explicitly chooses the EPS numerator. The three printed EPS values are retained as `guosen_eps_internal_model_numerator_conflict` with quarantine status. Revenue agrees between cover and full model and remains verified. Arithmetic may suggest which numerator produced EPS; it cannot replace the missing explanation.

Southwest's EPS label does not specify a basic/diluted denominator or adjustment policy. Its historical FY2025 net profit matches ASML's US-GAAP result, but the printed EPS 24.80 differs from [issuer diluted EPS 24.71](https://www.asml.com/en/news/press-releases/2026/q4-2025-financial-results). Its forecasts therefore retain `swsc_eps_definition_unresolved`, separately from both Morningstar and issuer reported diluted. EUR EPS is explicit even though the report discusses a USD share price and target.

## Raiffeisen lead: retained, attribution unresolved

The root's Grok discovery supplied a genuine [Raiffeisen-hosted ASML report](https://www.raiffeisen.at/resources/sbg/microsites/internetwertpapiere/pdfs/firmenanalysen-international/ASML.pdf), printed June 17, 2026 14:26 MESZ. Physical p1 gives FY2026e/FY2027e revenue EUR 38,910m / 47,769m, EPS 31.17 / 41.93, and adjusted EPS 31.42 / 42.39. The table jointly credits LSEG and RBI/Raiffeisen Research; Manuel Stahl is listed as Analyst Editor. That does not establish individual ownership of these forecasts, and the table does not explicitly establish consensus attribution either. EPS dilution and adjustment definitions are absent. All six rows remain quarantined. The original is retained with its hash and printed date despite the mutable URL.

## Fiscal labels, source dates and share basis

- Guosen's 2024–25 front-table year labels lag NVIDIA issuer fiscal names by one. The same-page narrative explicitly identifies the forecast fiscal years and corresponding revenue vectors; historical 60,922 / 130,497 revenues identify issuer FY2024/25. Raw year labels remain in `source_period_label`; normalized targets follow this internal evidence. No EPS is inferred or rescaled. The February 2026 report already uses explicit FY names. Its approximate January 26 calendar example is not substituted for the verified issuer fiscal calendar.
- Alphabet's March 2024 forecast table incorrectly says March year-end. The same page's historical summary says December, and historical annual revenues 282,836 / 307,394 match the [issuer's 2023 annual release](https://s206.q4cdn.com/479360582/files/doc_financials/2023/q4/2023q4-alphabet-earnings-release.pdf). The years are preserved; the known December 31 calendar controls their period ends.
- Apple, Broadcom and Micron print nominal month-end headers. The already verified issuer calendars control exact fiscal period ends; no calendar is changed here. All new US EPS observations are after the relevant split epochs. ASML's EPS is explicitly EUR per share; the established ADR-to-ordinary mapping applies without FX conversion.
- `available_at` and `original_available_at` are blank. Printed timestamps are separately recorded for Morningstar and Raiffeisen. Chinese reports establish a printed date but no independent numerical model date or dissemination timestamp, so those fields remain blank. Search crawl dates, URL dates and later revision panels never become earlier availability.

## Cross-author Morningstar review and remaining routes

The read-only `series_authorship_readonly_snapshot.json` confirms that each of the seven companies still has only one named author in its current Morningstar reported/adjusted definition groups. Multiple older authors occur mainly under legacy unresolved labels. More names in that category do not prove compatible earnings definitions.

No additional legacy bridge was justified. Apple's [May 2, 2025 revision panel](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000000GY_20250502_RT.pdf), p16, identifies January 30, 2025 prior values 7.36 / 8.33 / 9.43; it does not match the older November 2024 vectors. Alphabet's new Ali Mogharabi and Michael Hodel models have no exact dated modern revision bridge to Malik Ahmed Khan's reported-diluted group. ASML's recovered November 15 report still prints **November 6** as model date; the [April 2025 prior panel](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250403_RT.pdf) instead says November 15. Equal vectors do not resolve that date discrepancy. Existing round 8 accounting safeguards remain applicable.

Morningstar discovery considered 44 exact-date candidates, skipped 17 URLs already attempted, and made 27 new requests: eight original PDFs and nineteen HTTP 404s. The unchanged failed routes were not rerun. The new Guosen route remains productive: its own related-report lists identify August 29 and November 24, 2025, and August 30 / May 24 / February 23, 2024, plus older 2023 reports. This pass searched for the late-2025 items but did not locate exact originals; the earlier named dates are concrete next-pass leads. They should be recovered and checked for the same numerator/denominator policy, not assumed compatible. No subscription or scraping credits were required for this pass, and no claim is made that all public routes are exhausted.
