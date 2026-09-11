# Sandisk memory coverage, round 12

Collected on September 11, 2026; application cutoff remains September 10. Eight original Morningstar PDFs were retained. Two previously missing numerical models contribute 18 eligible annual EPS observations and 9 eligible revenue observations. Three completed-period cells are preserved as quarantined extraction evidence, bringing the raw transcription count to 30. Six reprints contribute no observations. The existing adjusted-diluted and reported-diluted series each gain two snapshots after integration.

| Retained publication | Numerical model date | Forecast fiscal years | Adjusted diluted EPS, USD |
| --- | --- | --- | --- |
| August 8, 2025, 23:04 UTC | May 8, 2025 | 2026–2029 | 5.11, 6.22, 5.41, 6.14 |
| August 6, 2026, 07:08 UTC | August 6, 2026 | 2027–2031 | 231.68, 319.77, 181.06, 73.98, 72.00 |

The first vector comes from the [August 8 original, page 9](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0001U8JM_20250808_RT.pdf). Its revision table on page 10 dates the numerical model to May 8. A July 22 narrative update does not refresh that model. The historical chart must begin using these observations only at the retained August publication, subject to the existing next-session rule. The data must not be backfilled to May. FY2025 ended June 27 before that publication. Its revenue and both EPS cells remain transcribed but are quarantined as completed-period estimates, despite the report's stale Forecast label. Only FY2026–2029 are admitted. The report's December fiscal-year header repeats the previously documented Sandisk template error. Its historical revenue and the [August 15 report's prior-model columns](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0001U8JM_20250815_RT.pdf) identify the same June-ending issuer fiscal years. Exact period ends continue to use the existing issuer calendar.

The second vector comes from the [August 6 original, page 11](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260806_RT.pdf). Page 12 explicitly dates the forecast revision to August 6. The April 30 financial-summary label is stale. FY2026 is displayed as actual, so only FY2027–2031 forecast columns were extracted. This fills the quarterly revision before the already-retained August 19 model. The two vectors differ slightly, so they are separate revisions.

## Why some jumps remain

The retained July 7, July 9, July 28 and August 4, 2026 reports reproduce April 30's entire EPS and revenue vectors. August 7 and August 12 reproduce August 6. Counting those documents as new forecasts would increase the apparent coverage without adding information and would incorrectly reset freshness. The original current/prior tables show that the large quarterly changes are genuine model revisions. More repeated PDFs cannot turn those changes into a daily series. [July 7 original](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260707_RT.pdf), [August 4 original](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260804_RT.pdf), [August 7 original](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001U8JM_20260807_RT.pdf).

The remaining early gap is a contemporaneous original carrying the February 27 or May 8, 2025 annual EPS model. Morningstar's [public company-report archive](https://www.morningstar.com/company-reports?listing=0P0001U8JM) identifies those notes and a July 22 report. Anchored distributor requests around these dates and weekly May–July checks returned 404. An August 8 PDF was the earliest successful discovery. Its prior-model column supplies some February numbers retrospectively, but those were not extracted or assigned historical availability.

A [public January 17, 2026 Morningstar reprint on Scribd](https://www.scribd.com/document/987296485/SanDisk-Report) was inspected for intervening revisions. It still contains November 2025's model. No observation was taken from its AI summary or from secondary earnings recaps. The public Morningstar note archive is a discovery aid; the imported numbers all come from original Morningstar PDF tables.

## Retrieval and remaining access questions

The reproducible request log records each candidate URL, HTTP result and retrieval timestamp. Successful documents retain their original bytes, SHA-256, layout-extracted text, reviewed table images and printed timestamps. Previously attempted URLs were skipped. Direct original PDFs worked; this was not a rendering or anti-bot failure. ScrapingBee would not demonstrably recover the 404 files.

The unresolved purchase question is whether a Morningstar historical-report entitlement supplies downloadable annual model tables for the February 27, May 8 and July 22, 2025 vintages. The public archive establishes the reports' existence, but this pass did not establish which paid tier exports those exact historical tables. No subscription recommendation is claimed to unlock them without that confirmation. The separate requirement for a denser cross-analyst series is named-analyst annual EPS revisions with accounting and dilution definitions, fiscal periods and original publication timestamps. Published consensus and price-target news alone cannot fill those fields.

The standalone security has no five-year listed-equity history. It began regular trading on February 24, 2025, and the old Sandisk security and Western Digital were not joined to it. [Issuer separation announcement](https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation).

## Reproduction

Run from the project root:

```sh
python3 data/collection/sandisk_memory_round12/collect.py
python3 data/collection/sandisk_memory_round12/extract_reviewed.py
```

The extractor asserts the complete ordered table rows, printed report timestamps and all duplicate vectors. Validation is retained in [validation.json](../../data/collection/sandisk_memory_round12/validation.json). The [manifest](../../data/collection/sandisk_memory_round12/manifest.csv) and [observations](../../data/collection/sandisk_memory_round12/observations.csv) are ready for the existing central refresh. This packet does not mutate the dashboard bundle or central policy files.
