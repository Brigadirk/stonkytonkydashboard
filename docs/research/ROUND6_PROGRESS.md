# Round 6: older models, repeatable refresh and backtest readiness

Completed 10 September 2026. All nine stocks retain current price bands. The main chart still compares actual share price with prices implied by median and ±1, ±1.5 and ±2 standard deviations of historical forward P/E. Desktop sizing remains unchanged from the 125% adjustment.

## What changed

| Measure | Before | After |
| --- | ---: | ---: |
| Unique relevant broker PDFs | 244 | 270 |
| Raw forecast/consensus observations | 1,669 | 1,802 |
| Eligible annual EPS observations | 850 | 889 |
| Separate analyst/basis/consensus series | 54 | 54 |
| Model snapshots | 246 | 257 |
| Daily closing prices | 12,386 | 12,387 |
| Initial issuer EPS outcomes | 40 | 40 |
| Eligible EPS forecast/result pairs | 3 | 3 |

The price refresh added ASML's September 10 close. The other eight feeds still end on September 9. Newly retained reports contain 69 raw EPS observations; unchanged reprints and duplicate model rows explain why the chart panel grows by fewer observations.

## Historical coverage

Using identical 365-day reference windows and 180-day maximum model age:

| Company | EPS observations before → after | Dates with usable bands before → after | Model snapshots before → after |
| --- | --- | --- | --- |
| Broadcom | 111 → 120 | 930 → 1,023 | 29 → 32 |
| NVIDIA | 115 → 121 | 1,155 → 1,159 | 31 → 33 |
| Micron | 82 → 106 | 1,007 → 1,087 | 22 → 28 |

These date counts are the union of usable dates across separate series, not a stitched analyst history or one tradable model. The three collection targets gained 177 company/date observations with drawable bands. ASML gained one more date from its new close. [Machine-readable comparison](../../data/market/round6_coverage_comparison.json) preserves per-series counts and the prior baseline.

Broadcom's first usable EPS date moves from September 6 to May 31, 2022. New models and earlier originals improve 2022–2024 coverage. NVIDIA adds February 2022 and March 2024 models, although most of their dates already had coverage elsewhere in the archive. Micron adds older model vintages and a September 2024 definition bridge; its current adjusted series now supports price bands from October 25, 2024.

## Evidence and exclusions

- [Broadcom research](BROADCOM_ROUND6.md): nine original reports, 48 observations. The July 2024 report mixes post-split historical figures with pre-split forecasts. Original model values and forecast share counts establish the forecast units. The existing December 2024 alias is extended only to exact matching reprint rows.
- [NVIDIA research](NVIDIA_ROUND6.md): five reports, 30 observations. The June 2024 reprint also retains pre-split forecast units. Its explicit share-basis date prevents a tenfold EPS error. Older adjustment definitions remain unresolved.
- [Micron research](MICRON_ROUND6.md): twelve broker reports plus an issuer filing, 55 observations. A March 2025 report explicitly distinguishes reported and adjusted EPS and reproduces the September and December 2024 models. Exact model, fiscal-period, value and source-hash checks support the aliases; other vintages remain separate.

Equal historical EPS is insufficient evidence of equivalent forecasting definitions. The Broadcom and Micron notes document cases where Morningstar and the issuer print the same rounded adjusted EPS but different underlying income and share counts. Accordingly, no new forecast-to-issuer scoring compatibility was inferred. The EPS pilot remains at three pairs and 117 excluded company/year/basis/horizon combinations. No analyst ranking is assigned.

## Refresh and study preparation

The [refresh command](../REFRESH.md) archives prior and resulting generated data, collection metadata and calculation sources. It validates consistent cutoffs and split units, rejects truncated price histories, stages the production build and restores prior generated files on a handled failure. Original downloads stay retained under their source hashes.

The first full run exposed the indexer's derived SQLite catalog write as an input mutation. Publication stopped and prior generated files were restored. Refresh now indexes CSV outputs without changing the input database. The successful retry reused the retained price downloads and completed the full pipeline. The run and logs are in [the successful archive](../../data/refresh/20260910T170318.537646Z/run.json).

The new public-report discovery command made 49 bounded requests covering seven Morningstar IDs over September 4–10. There were no request failures and no new uncollected PDFs on this route. Discovered PDFs go to a review inbox and cannot update EPS until reviewed. Korean sources continue to use their separate broker collection routes. The public seed register now contains 410 URLs.

The new Data coverage panel and export assess backtest readiness separately for every series. They distinguish drawable bands, complete 180/365-day reference windows, and complete windows with verified original availability. No current series passes the availability requirement. A [fixed initial strategy-study protocol](../BACKTEST_PROTOCOL.md) records candidate rules before returns are examined. No performance result has been manufactured from the sparse reconstruction.

## Validation and remaining work

All 42 automated checks passed: 21 frontend/unit/dataset tests, 19 Python tests and two browser tests covering desktop and mobile. Production build passed. New tests cover failed-refresh restoration, preservation of forecast vintages, truncated price rejection, PDF validation, evaluation cutoffs and splits, and the difference between drawable and fully supported band windows. Source-specific alias evidence is hash-checked and its exact EPS values are enforced. Screenshots: [Micron price view](../screenshots/round6-micron-price.png) and [backtest readiness](../screenshots/round6-backtest-readiness.png).

Remaining collection priorities are intermediate models within a consistent analyst/basis history, older explicit EPS definitions, early-January 2026 Korean forecasts, and broader comparable fixed-horizon forecast/result observations. Original availability timestamps and a contemporaneous consensus benchmark remain missing. Public sourcing is still productive; this pass required no ScrapingBee credits, paid subscription or provider contact.
