# Older US and ASML forecast collection — round 2

Collected on 10 September 2026. Scope: original public numerical forecasts with report dates in 2021–2023 for Broadcom, Alphabet, Nvidia, Micron and ASML. Discovery stopped after 15 targeted searches. This is a bounded search result, not proof that missing archives do not exist.

Four original sources were saved: two PDFs and two public HTML articles. They produce **31 raw, unscored observations: 25 analyst/team forecast rows and six reported-consensus rows**. Only one distinct printed vintage per source is counted. These samples do not establish which analyst is best.

## What was obtained

| Company | Printed/public article date | Source and attributable author | Numerical evidence | Qualification |
|---|---|---|---|---|
| Nvidia | 21 March 2023 | Phillip Securities, Maximilian Koeswoyo | FY2024 revenue USD29bn | Original public HTML; rounded forecast; separate model timestamp and original dissemination unverified |
| Nvidia | 21 November 2023 | Itaú BBA, Thiago Alves Kapulskis / Gabriela Moraes / Cristian Faria | FY2026 EPS USD20 in narrative; a three-year revenue/EPS revision table | Original five-page PDF; team attribution. Table fiscal labels conflict with narrative, so six table rows are quarantined |
| Alphabet | 27 October 2023 | Phillip Securities, Jonathan Woo | Q4 2023 total-revenue growth of 13% YoY | Original public HTML; growth forecast only, not a dollar revenue forecast or EPS |
| ASML | 26 April 2023 printed; file created 2 December 2023 | x2 investors, Tim Green | Base-case FY2023–2030 revenue/EPS model; e.g. FY2023 EUR26,784m / EUR18.98 and FY2025 EUR35,419m / EUR30.46 | Original eleven-page public sample. All 22 extracted rows quarantined pending date/basis review; six are consensus rather than Green's own estimates |

Sources: [Phillip Nvidia initiation](https://www.stocksbnb.com/reports/nvidia-corporation-ai-is-the-future/), [Itaú Nvidia original report](https://mindassets.cloud.itau.com.br/attachments/1d4e2e1e-db49-4c23-9f1c-8bf779cb9800/NVDA_ER_20231121.pdf), [Phillip Alphabet report](https://www.stocksbnb.com/reports/alphabet-inc-advertising-rebound-but-cloud-lags/), [x2 publisher homepage with ASML sample link](https://www.x2investors.com/), [x2 author biography](https://www.x2investors.com/about-us).

The x2 PDF's first page and repeated footers say 26 April 2023, while embedded creation and modification fields say 2 December 2023 at 14:39:02 UTC. The signed URL was obtained by following the publisher's current public sample link, and is preserved exactly in the manifest and `x2_source.json`. Its filename, which contains “dec”, is not substituted for the printed report date. This retrieval does not prove that today's model was available unchanged in April. Page 7 separates the author's base case from consensus. Other pages contain high/low scenarios and are not treated as extra central forecasts.

Itaú page 1 explicitly labels rounded EPS of USD20 as FY26E, while page 3 places USD20.12 under “2025” beside “2023” and “2024”. The table is preserved under `UNRESOLVED_SOURCE_YEAR_…`, rather than silently shifting fiscal years. Its net-revenue New rows are USD58,897m / USD94,547m / USD113,860m and EPS New rows USD11.21 / USD17.82 / USD20.12. The narrative and last table row represent the same underlying forecast family; they must not be counted as independent evidence. Old rows have no separately verified earlier publication date. EPS remains on its printed share basis, before Nvidia's 2024 split. The report's PDF metadata is consistent with creation late on 21 November 2023, but is not independent dissemination evidence.

## Files and review status

All files are under `data/collection/us_history_round2/`:

- `manifest.csv`: five attempted sources, four original artifacts retained, SHA-256 hashes, report dates, and source URLs.
- `observations.csv`: canonical company IDs; original units, page numbers and source labels; printed report timestamps separate from blank `available_at` and `original_available_at`.
- `pdfs/`, `html/`, `text/`: original downloads and text extractions. Two PNGs retain the visually checked model tables.
- `pdf_metadata.json`: creation/modification fields and page counts, explicitly not publication evidence.
- `coverage_by_company_year.csv`: counts by report year, including zeros for 2021 and 2022.
- `discovery_queries.csv`: all 15 search queries and outcomes. Query strings normalize quotation/case punctuation for legibility.
- `finalize_review.py`: reproduces the reviewed CSVs without network access and verifies the four artifact hashes, source paths, unique observation IDs and date bounds.

No accuracy scores or completed point-in-time backtest inputs result from this round. As well as the 28 quarantined rows, the three remaining narrative/HTML observations require period, rounding, accounting and original-availability reconciliation before use in analyst comparisons. Model date is left blank where the source does not separately establish it.

## Gaps and archive routes

No 2021 or 2022 original company model was obtained. Broadcom and Micron have no qualifying original report from this round. None of the new models is from the principal US institutional shortlist; the search did not recover a Harlan Sur Broadcom model. Sandisk was not pursued after the bounded search allowance was consumed by older-year leads.

The [Phillip indexed May 2023 Nvidia PDF](https://www.stocksbnb.com/wp-content/uploads/pdf/NVDA20230529.pdf) returned HTTP403. The public article pages explicitly require login for full PDFs, so collection stops at public HTML. ScrapingBee would not provide permission to cross that access requirement. Technical-price notes and current consensus pages were excluded from earnings-estimator evidence.

x2's raw homepage request returned HTTP403, but the ordinary web tool could read the public homepage and follow its sample link; the resulting PDF downloaded normally. No ScrapingBee credits were needed. The homepage is a documented sample endpoint, not a five-year model archive. The Itaú PDF resides at an indexed first-party UUID attachment URL; a complete public dated report listing was not established, and no UUID or filename brute force was attempted.

A [2022 Broadcom/VMware transaction filing](https://www.sec.gov/Archives/edgar/data/1730168/000114036122033631/ny20004409x19_s4a.htm) surfaced VMware-approved Broadcom projections. They are a separate transaction/management baseline, not an attributable Harlan Sur or other individual analyst forecast, and were not added to this analyst collection. University reports and 2024 ASML reports also surfaced, but the professional 2023 sample was prioritized.

The next useful acquisition is a licensed historical analyst-level estimate panel or original entitled institutional report archive, with analyst identities, revision dates, fiscal periods and accounting definitions. More public search volume alone should not be mistaken for coverage of the strongest forecasters.
