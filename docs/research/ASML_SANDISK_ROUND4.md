# ASML and standalone Sandisk: fourth collection pass

Researched 10 September 2026. Scope: original dated annual EPS forecasts, with FY1/FY2 pairs where available, for ASML in EUR and the Sandisk equity listed after its 2025 separation. This collection supplies forecast history; it does not establish which analyst is most accurate.

## Result

The pass retained **21 original report PDFs** and extracted **135 observations**. Of these, **127 are not quarantined: 76 annual EPS forecasts and 51 annual revenue forecasts**. Eight observations remain quarantined. The two companies now have dated annual models with which the app can build separate series, subject to its availability and staleness rules.

| Company | Nonquarantined observations | Evidence added |
|---|---:|---|
| ASML | 44 | Seven dates of Bloomberg-adjusted consensus in EUR, plus one separately labelled consensus snapshot with unspecified EPS adjustment |
| Sandisk | 83 | Five William Kerwin/Morningstar models, each with five forecast years of reported diluted EPS, adjusted diluted EPS and revenue; two separately labelled consensus snapshots |

Files: [manifest](../../data/collection/asml_sandisk_round4/manifest.csv), [observations](../../data/collection/asml_sandisk_round4/observations.csv), [validation results](../../data/collection/asml_sandisk_round4/validation.json). The manifest also records a failed Cantor request, so it contains 22 records. Original PDFs, extracted text, screenshots used in review and reproducible collection/extraction scripts are retained in the same collection directory.

## Sandisk: original named models

Morningstar's listing identifier for the new Sandisk is **0P0001U8JM**. Its [company-report index](https://www.morningstar.com/company-reports?listing=0P0001U8JM) supplied company identity and publication-date leads; those dates were used to find original Morningstar PDFs in Firstrade's public distribution archive. The archived reports name **William Kerwin**. They explicitly separate diluted EPS from adjusted diluted EPS; these are stored as different metrics and bases.

| Printed report date, UTC | Model date printed in financial summary | Forecast years | FY1 / FY2 adjusted diluted EPS, USD | Original and physical page |
|---|---|---|---|---|
| 2025-08-15 23:14 | 2025-08-14 | FY2026–FY2030 | 4.77 / 6.70 | [Morningstar/Firstrade](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0001U8JM_20250815_RT.pdf), p9 |
| 2025-11-07 02:59 | 2025-11-06 | FY2026–FY2030 | 12.94 / 18.51 | [Morningstar/Firstrade](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0001U8JM_20251106_RT.pdf), p10 |
| 2026-01-30 06:04 | 2026-01-29 | FY2026–FY2030 | 50.81 / 139.90 | [Morningstar/Firstrade](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260130_RT.pdf), p10 |
| 2026-05-01 03:05 | 2026-04-30 | FY2026–FY2030 | 72.22 / 203.19 | [Morningstar/Firstrade](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260430_RT.pdf), p11 |
| 2026-08-19 18:04 | 2026-08-19 | FY2027–FY2031 | 231.79 / 320.21 | [Morningstar/Firstrade](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260819_RT.pdf), p12 |

Report dates follow the printed UTC cover timestamp, not the URL's US calendar date. The [November 8 report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0001U8JM_20251107_RT.pdf) retains the November 6 model with identical forecasts. It is preserved in the manifest but contributes no duplicate model observations.

**August fiscal-header correction.** The August report's financial summary incorrectly says the fiscal year ends in December. Its FY2025 actual revenue of USD7,355m, reported diluted EPS of -11.32 and adjusted diluted EPS of 2.99 refer to Sandisk's year ended June 27, 2025. The issuer's [August 14, 2025 results](https://investor.sandisk.com/news-releases/news-release-details/sandisk-reports-fiscal-fourth-quarter-2025-financial-results) corroborate those historical figures and period. November's correctly June-labelled model also reproduces the August FY2026–FY2028 revenue and both EPS forecasts exactly in its prior-model columns, p11. The extraction therefore preserves the printed FY numbers and records the header error explicitly; it does not reinterpret the forecasts as December calendar years. The app's issuer fiscal calendar should supply the actual Friday nearest June 30.

The current standalone security began regular trading on February 24, 2025. The historical Western Digital business figures printed in these models are context, not a reconstructed five-year trading history for the new equity. No estimates for the Sandisk acquired in 2016 were admitted. [Issuer separation announcement](https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation)

## ASML: separate Bloomberg consensus series

Hana's originals explicitly attribute the forecasts to Bloomberg market consensus. The estimates belong to that consensus, not to an individual Hana analyst. All rows therefore leave `analyst_name` blank and use the stable firm label `Hana Securities (Bloomberg consensus)` and `report_embedded_consensus` source type.

| Printed date | Forecast years retained | First two annual EPS values, EUR | Original and physical page |
|---|---|---|---|
| 2021-07-22 | FY2021–FY2022 | 12.56 / 15.24 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2021/07/21/Global_ASML_2021.07.22.pdf), p2; adjusted label p4 |
| 2021-10-01 | FY2021–FY2025 | 13.50 / 16.57 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2021/09/30/Global_ASML_2021.09.30.pdf), p2; adjusted label p5 |
| 2022-01-20 | FY2022–FY2026 | 16.98 / 19.23 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2022/01/19/Global_ASML_Hana.pdf), p2; adjusted label p5 |
| 2023-04-25 | FY2023–FY2024 | 18.8 / 22.7 | [Hana daily](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2206&bbsId=&bbsSeq=1274459&dbType=), p11; adjustment unspecified |
| 2024-07-18 | FY2024–FY2025 | 18.8 / 29.9 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2024/07/18/ASML_240718.pdf), p4 |
| 2024-10-17 | FY2024–FY2025 | 18.8 / 28.9 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2024/10/17/ASML_241017.pdf), p5 |
| 2025-10-17 | FY2025–FY2026 | 24.5 / 25.7 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2025/10/16/ASML_251017.pdf), p5 |
| 2026-01-30 | FY2026–FY2027 | 28.4 / 36.5 | [Hana](https://www.hanaw.com/download/research/FileServer/WEB/global/company/2026/01/29/ASML_260129.pdf), p5 |

The July 2021 report is a warmup snapshot for the September 2021 chart start. These are sparse snapshots, with substantial gaps in 2022–2025. The July 2024 and later reports have an erroneous USD label on the cover EPS row; the detailed table explicitly labels EUR per-share figures and Bloomberg-adjusted EPS. Detailed-table currency controls extraction. Basic versus diluted denominator is not stated, so this series must remain separate from explicitly diluted models. The April 2023 snapshot also remains separate because its EPS adjustment basis is unspecified.

The [April 16, 2026 report](https://file.hanaw.com/download/research/FileServer/WEB/global/company/2026/04/16/ASML_260416.pdf) repeats the January annual table, including both years' revenue and EPS. It is retained without new observations so a copied model cannot extend apparent revision freshness. The January source was found through Hana analysts' [public January 29 post](https://t.me/ITforYouFromHana/10306), whose short link resolves to the original PDF. The [October 18, 2024 daily](https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2024/10/17/Daily_241018.pdf) similarly reprints the October 17 model and contributes no duplicate rows.

## Additional Sandisk consensus anchors

Hana's [2026 global guide](https://www.hanaw.com/download/research/FileServer/WEB/global/industry/2026/01/09/2026guide.pdf), physical p73/printed p72, contains a Sandisk FY2026/FY2027 Bloomberg consensus pair: EPS USD12.61/21.84 and revenue USD10,618m/12,991m. The printed cover image dates publication **January 12, 2026**, despite January 9 in the URL and PDF creation metadata. Adjustment and dilution basis are not specified. The ASML guide section is in USD and was not admitted to this collection's EUR series.

The [Zacks overview](https://advisortools.zacks.com/Research/Stocks/SNDK/Overview/PDF/2015-11-27/2025-12-02) is a mutable current endpoint. Its retained September 10, 2026 PDF forecasts FY2027/FY2028 EPS USD208.92/252.16 and revenue USD49,248m/58,456m. URL dates do not date the contents. Search indexing showed an older, materially different June snapshot; those indexed numbers were not extracted. The retained row date is the retrieval day, its observed-availability timestamp is recorded, and its EPS basis remains unspecified. This is a current published-consensus anchor, not historical backfill.

## Exclusions and search routes

- [Mirae's January 21, 2022 daily](https://securities.miraeasset.com/public/mw/blog/20220121080513/20220121_Daily.pdf), p7, includes a January 20 ASML table and analyst Young Ryu. Its source line combines ASML, Bloomberg and Mirae without explicitly assigning forecast ownership. Six revenue/EPS rows are quarantined pending attribution; the source revenue unit is EUR billion.
- [William O'Neil's ASML chart](https://ebooks.williamoneil.com/pdfs/charts/comments/20240902/ASML.NL.pdf) prints a weekly August 30, 2024 date, while the filename and creation date suggest September 2. Estimate ownership and publication timing are unresolved. Two EPS rows remain quarantined.
- [Hana's 2024 guide](https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2024/01/11/2024Global_100.pdf) was retained but its publication date was not reviewed and its ASML section supplies only FY2023/FY2024. No observations were admitted.
- [Cantor's January 2023 ASML lead](https://cantorfitzgerald.ie/wp-content/uploads/2023/12/ASML-Research-Note-Jan-23-1.pdf) returned HTTP403; no numbers were extracted. Existing Websim and x2 leads retain date/basis conflicts. An FSM page returned only a JavaScript shell. Meritz's sector excerpt contained ASML peer references but no newly usable annual model.
- Morningstar discovery first returned a Micron identifier because Sandisk appeared in a peer panel. That false identity was rejected. After verifying the correct Sandisk listing, known publication-date requests for February 26/27 and May 7/8, 2025, and May 1/June 25, 2026 returned 404. The April 30 US-date filename succeeded for the May 1 UTC report. No old Sandisk identifier was reused.
- Hana archive searches and the analysts' public Telegram report links supplied original PDFs. Telegram search pagination exposed no additional earlier annual models during this bounded pass. No messages were sent, paid account used, or provider contacted. ScrapingBee and Grok were not needed for these discoveries.

## Validation and remaining limits

`validate_retained.py` verified all retained PDF SHA-256 hashes, observation references, duplicate observation IDs, consensus attribution, and the absence of fabricated historical availability timestamps. It independently reparsed the five forecast columns of every extracted Morningstar revenue and EPS row and matched all 75 named-model observations. Visual review checked the Sandisk fiscal-header discrepancy and November corroboration, the latest Sandisk model, Hana's guide cover and Sandisk page, and ASML detailed currency/basis tables.

Historical printed dates and timestamps are preserved but are **not independently verified first dissemination times**. `original_available_at` is blank for historical reports. The current Zacks download alone has an observed retrieval-time availability. These sources support illustrative dated-model charts, not a claim of audit-grade point-in-time backtesting or a complete five-year revision history. EPS bases and named versus consensus contributors must remain separate; no EPS was inferred from a valuation multiple.

### Final bounded search for current ASML estimates

After integration, a separate search targeted July 2026 or later ASML models. Hana's public research channel linked original [July 13 sector weekly](https://file.hanaw.com/download/research/FileServer/WEB/industry/industry/2026/07/12/Weekly_Roko_260713.pdf) and [July 20 sector weekly](https://file.hanaw.com/download/research/FileServer/WEB/industry/industry/2026/07/19/Weekly_Roko_260720.pdf). Both were retained as research candidates outside the merged manifest, with hashes in [candidate provenance](../../data/collection/asml_sandisk_round4/current_asml_candidate_sources.json). Their ASML tables show valuation multiples and EPS growth percentages, not annual EPS amounts, so they cannot refresh the EUR earnings model. A July 16 Tech & Stock report link from [Hana's own channel](https://t.me/HanaResearch/19927) timed out at its `buly.kr` shortener. No new eligible observations resulted, and the merged CSVs were not changed.
