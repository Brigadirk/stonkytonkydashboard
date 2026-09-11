# Micron memory coverage, round 12

Collected September 11, 2026. Prices and the application cutoff remain September 10. Four additional numerical models were recovered from original Morningstar reports distributed publicly by Firstrade. Three extend both existing modern EPS series; one extends the separate legacy series. This adds 33 EPS observations and 18 revenue observations.

| Retained report timestamp (UTC) | Table model date | Forward fiscal years | Adjusted diluted EPS (USD) |
| --- | --- | --- | --- |
| August 11, 2025, 19:00 | August 11, 2025 | 2025–2029 | 8.05, 10.25, 10.48, 9.59, 10.94 |
| December 20, 2025, 00:33 | December 17, 2025 | 2026–2030 | 34.37, 46.66, 44.01, 19.61, 19.46 |
| March 13, 2026, 04:52 | March 12, 2026 | 2026–2030 | 37.00, 56.93, 48.39, 20.57, 22.48 |

Each model has separately labelled reported diluted EPS, adjusted diluted EPS and revenue rows on physical page 13. Values were checked against those rows and the rendered pages. The primary sources are the [August report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250811_RT.pdf), [December report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20251219_RT.pdf) and [March report](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000003MC_20260312_RT.pdf). These fill genuine missing revisions between the already-collected quarterly models. The modern default series gains three dated models without changing its analyst, definition, or weighting.

The additional legacy model is dated June 28, 2023 but first retained in an August 15, 2023 report, 22:51 UTC. Its FY2023–25 EPS values are −4.55, 1.83 and 4.47. Page 14 labels the row diluted EPS but does not establish the adjustment definition, so it stays in `diluted_adjustment_basis_unresolved`. It is never inserted into June's history or joined to modern adjusted EPS. [Original August 15 report](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003MC_20230815_RT.pdf).

## Publication lag and excluded reprints

The December 18 report already has the new earnings commentary and fair value, but its annual financial table still carries the September 23 EPS vector. Using the article date for the new EPS would leak information into the reconstruction. The December 20 retained copy is the earliest successful retrieval containing the revised table; the existing conservative next-session availability rule applies. [December 18 original with stale table](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20251217_RT.pdf).

The September 11, 2025 report repeats August 11's model. March 14 and March 17, 2026 reports repeat March 12. The May 20, 2026 report repeats March 18. These sources are retained without new observations. Other older successful downloads repeat already-collected models or lack an annual table. The June 29, 2023 report still contains May 25's model; the August report is the first retained evidence of the June revision. Report dates, numerical model dates and original availability evidence remain separate fields.

The public [March 12 analyst note](https://www.morningstar.com/company-reports/1456930-micron-valuation-higher-heading-into-earnings-but-long-term-cyclicality-keeps-us-on-the-sidelines) helped locate the intervening revision. Search snippets and analyst prose supplied discovery dates only; numerical observations all come from retained original tables.

## Remaining gaps and access

The retained default adjusted series begins in September 2024. Earlier models have an unresolved adjustment definition. A contemporaneous explicitly labelled table or an exact model/period-scoped reconciliation is needed to extend that same basis earlier; a general assertion that all old EPS was adjusted would be insufficient.

Earlier contemporaneous distribution remains missing for the June 28, 2023 model and some other retained reprints. The March 20, 2025 revision is still first retained in April's report. The public archive was searched, and the request log records bounded probes around earnings dates, known analyst-note dates and intervening sessions. Across this pass, 108 direct URL candidates yielded 19 PDFs; the remaining responses were 404. A URL date was never treated as its publication date.

These were working public PDF routes. ScrapingBee cannot be shown to resolve the missing-file responses or supply missing EPS definitions. A paid route must demonstrate historical annual-model tables, named analyst, precise EPS definition and publication/model timestamps for the specific missing vintages before purchase. No paid tier was verified to supply those fields, and nothing was purchased.

## Reproduction and evidence

`data/collection/micron_memory_round12/collect.py` accepts explicit candidate dates in YYYYMMDD form and records every requested URL and result in `retrieval.json`. It preserves source hashes and refuses to overwrite changed bytes. Existing requests are skipped. Example: `python3 data/collection/micron_memory_round12/collect.py 20250811 20251219 20260312 20230815`.

Run `python3 data/collection/micron_memory_round12/extract_reviewed.py` from the project root to regenerate observations, the source manifest, extraction evidence and validation without network access. It checks hashes, printed timestamps, table model dates and complete ordered forecast rows. Reviewed images live in the packet's `review/` folder. `scripts/compare_memory_coverage.mjs` compares the frozen before dataset with the rebuilt dataset, preserving prices, estimator selection and unrelated companies.
