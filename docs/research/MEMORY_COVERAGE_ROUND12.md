# Memory estimate coverage, round 12

The September 11 collection adds missing dated forecasts for Micron, Sandisk, SK hynix and Samsung. The price cutoff stays September 10, 2026. No chart calculation, estimator selection, earnings definition, currency, share basis, interface size or price observation was changed.

| Default estimator history | Before snapshots | After snapshots | Newly recovered evidence |
| --- | ---: | ---: | --- |
| Micron — William Kerwin, Morningstar adjusted diluted | 8 | 11 | August 11 and December 17, 2025; March 12, 2026 numerical models |
| Sandisk — William Kerwin, Morningstar adjusted diluted | 5 | 7 | May 8, 2025 model first retained August 8; August 6, 2026 revision |
| SK hynix — Sunwoo Kim, Meritz parent-attributable | 32 | 36 | June 1, 2021; February 1 and April 27, 2023; January 15, 2024 |
| Samsung — Sunwoo Kim, Meritz parent-attributable | 28 | 34 | June 1 and July 29, 2021; October 28, 2022; January 15, May 2 and November 1, 2024; existing November 2021 vector proven in an October 29 original |

Snapshots are retained dated model records, not independent analysts. Micron's original eight snapshots contain seven numerical model dates because an old revision appears with additional fiscal targets in a later report. New modern Micron and Sandisk models supply separate reported and adjusted diluted EPS series. The legacy June 28, 2023 Micron model was also recovered, first retained in August, and stays in its unresolved-adjustment series.

## Effect on the chart

The missing Micron revisions had left September's earnings forecast active until March. Filling August/December 2025 and March 2026 reduces its largest positive-forward-EPS jump during the last year from 480.41% to 135.86%. This measures changes in the reconstructed next-twelve-month EPS at successive recorded sessions; it is not price movement or a forecast-accuracy score. Large published earnings revisions remain discrete.

The corrected historical P/E distribution changes Micron's default one-year median valuation scenario from $2,919.76 to $2,374.05. Its current price and latest forecast are unchanged. Sandisk's corresponding scenario changes from $2,547.87 to $2,539.19. The Korean additions improve older history and leave their current one-year targets unchanged. Sandisk's and the Korean companies' largest recent forecast jumps remain; reviewed intervening reports either repeat existing tables or contain no new annual EPS model.

The reproduction report retains all model dates, source hashes, before/after histories, current reference counts, target earnings and target prices: [memory_coverage_report.json](../../data/market/memory_coverage_report.json). Its checks assert unchanged price arrays, default estimators and complete company records for all six non-memory names. The [full missing-fields/date map](../../data/market/missing_data_dates.csv) was regenerated.

## Data integrity and totals

The three source packets contain 143 raw observations, of which five completed-period cells are quarantined. They contribute 81 eligible annual EPS observations before the Samsung reprint reconciliation. Removing the three previously duplicated Samsung EPS cells leaves a net addition of 78 retained EPS observations and 21 model snapshots. Two exact-source rules preserve October 29 as the numerical vintage of the repeated November 11 Samsung EPS and revenue vectors.

The complete app now has 1,173 eligible EPS observations, 350 model snapshots, 74 earnings series, 396 unique original broker PDFs and 2,420 raw observations. It retains 13,928 actual closes. All ten stocks still have current bands and one-year targets. The 48 initial issuer EPS outcomes and eight fixed-horizon EPS comparison pairs are unchanged. The additional Samsung history adds three revenue comparison pairs, increasing that separate pilot from 19 to 22; the new pairs cover FY2021 at a 180-day horizon and FY2024/FY2025 at 365 days. This collection does not establish an analyst ranking or unlock the backtest protocol.

Report publication dates remain assumptions unless separately verified. A later report containing an old model never supplies historical availability for that earlier date. No reprint receives a new analyst vote or a freshness reset. Previously completed fiscal-year columns stay as quarantined extraction evidence, even where the original source labels them forecasts.

## Sources and remaining gaps

The detailed packets retain original PDFs, physical page images, exact extraction rows, hashes, publication/model dates, request logs and reproducible scripts:

- [Micron source review and missing vintages](MICRON_MEMORY_ROUND12.md).
- [Sandisk source review and missing early-2025 publications](SANDISK_MEMORY_ROUND12.md).
- [Korean source review, original report links and 2026 routes tried](KOREA_MEMORY_ROUND12.md).

Micron still needs an explicit definition/reconciliation to join pre-September-2024 EPS to the modern adjusted series, plus contemporaneous originals for some old reprints. Sandisk still lacks contemporaneous annual tables for February/May 2025. Its standalone stock history begins in February 2025. For SK hynix and Samsung, the public 2026 intervening notes reviewed did not contain additional annual EPS models; cross-broker denominator and adjustment equivalence remain unproven.

Further smoothing from more observations would require additional genuine revisions, potentially from a historical named-analyst EPS feed with compatible definitions and publication timestamps. Public price-target summaries and consensus headlines do not supply those fields. Direct public PDF retrieval worked. Missing distributor files returned 404, so no ScrapingBee purchase has been demonstrated to recover them. No specific subscription tier was verified to deliver all required historical fields, and none is recommended as a guaranteed unlock. Nothing was purchased. The [earlier all-stock access handoff](ESTIMATOR_ROUND11.md) remains relevant outside this memory-focused pass.

## Verification and reproduction

The normal offline refresh completed, with an immutable before/input/after archive at `data/refresh/20260910T221831.167246Z`. Projection, estimator-comparison and corridor reports were regenerated. Source extractors verify ordered values, printed dates and retained hashes. Validation passed: 28 Python tests, 56 frontend/data tests and 13 browser tests.

The additional browser review checked every rendered historical close, forward EPS value and median-band point across all four memory charts against the refreshed calculation, preserved five-year history and the 640-pixel chart, checked cursor values, and inspected the mobile layout. Screenshots and the served bundle hash are in `data/deliveries/20260911-memory-coverage/`.

Run `node scripts/compare_memory_coverage.mjs` to reproduce the collection comparison. Run `node data/deliveries/20260911-memory-coverage/review.mjs` against the local app to repeat the rendered-data checks. The calculation code is unchanged; new source packets are included by the existing offline refresh pipeline.
