# Estimator app and collection delivery

Completed 10 September 2026 at the documented access checkpoint. Local app: http://127.0.0.1:5178. No subscription, proxy credits, account or provider contact was purchased or initiated.

## Delivered behavior

The app supports one estimator, independent overlays, and selected compatible ensembles with a median default or equal-weighted mean. “All compatible estimators” selects the reviewed group. Published consensus stays independent. Named coauthor teams and author handovers cannot supply multiple votes from one research firm.

Every historical date uses the latest eligible numerical model then available, with the existing freshness limit. Reprints cannot reset its age. Each contributor's complete day-weighted annual forward-EPS series is normalized for splits before aggregation. The combined EPS series supplies historical P/E; its trailing median and sample standard deviation produce share-price bands at ±1, ±1.5 and ±2σ. The current date is excluded from the reference window. Negative/tiny combined earnings and missing fiscal targets leave visible gaps.

Contributor counts, model/report ages, age ranges, source links, membership entries/exits, exclusions and EPS disagreement are inspectable and exportable. Disagreement between analysts is explicitly separate from the chart's historical P/E variation. The All stocks table includes model date, age and reference coverage. Settings and selections survive reload and shareable links. The existing larger sizing remains: 16px base text, 44px primary controls and a 520px price chart; the 390px mobile view has no page overflow.

## Data delivered

| Measure | Before this goal | Delivered |
|---|---:|---:|
| Daily closes | 13,924 | 13,928 |
| Eligible annual EPS observations | 912 | 1,066 |
| Separate estimator/definition or consensus series | 59 | 66 |
| Model snapshots after EPS reprint deduplication | 266 | 319 |
| Original broker PDFs | 276 | 349 |
| Raw extracted forecast/consensus observations | 1,864 | 2,219 |
| Initial issuer EPS outcomes | 40 | 48 |
| Comparable fixed-horizon EPS/result pairs | 3 | 8 |
| Korean revenue forecast/result pairs | 13 | 19 |

All ten names have usable current price bands. European and Korean prices end September 10; US prices end September 9 because the September 10 US session was still open. No live US quote was substituted for a daily close. The [exchange/Naver checks](PRICE_SUPPLEMENTS.md) repaired two Amsterdam price gaps and independently verified the newly returned Korean closes. Two September 19, 2025 Korean bars remain absent from the valuation price series; their source-native closes are retained separately with an unresolved historical adjustment convention.

| Stock | EPS rows / models | Latest default model or report | Age at close | 365-day reference sessions |
|---|---:|---|---:|---:|
| AVGO | 120 / 32 | 2026-09-02 | 7 days | 251 / 251 |
| GOOGL | 99 / 25 | 2026-07-22 | 49 days | 251 / 251 |
| NVDA | 140 / 40 | 2026-08-26 | 14 days | 251 / 251 |
| 000660 | 166 / 63 | 2026-07-29 (report fallback) | 43 days | 242 / 242 |
| 005930 | 122 / 47 | 2026-07-30 (report fallback) | 42 days | 242 / 242 |
| MU | 106 / 28 | 2026-06-24 | 77 days | 251 / 251 |
| SNDK | 54 / 12 | 2026-08-19 | 21 days | 251 / 251 |
| ASML | 118 / 33 | 2026-07-15 | 57 days | 253 / 255 |
| AAPL | 115 / 28 | 2026-07-30 | 41 days | 251 / 251 |
| BESI | 26 / 11 | 2026-04-23 | 140 days | 236 / 255 |

Coverage means the available prior sessions inside the selected window, not an independently audited exchange calendar. A current 100% reference window does not establish five years of history or verified original availability.

The updated SK hynix collection includes Meritz's July29 model and the original Mirae July14 revision underlying a July29 reprint. Samsung has the July30 Meritz model. Both companies also retain September7 Mirae models as separate alternatives; the default favors usable history rather than simply choosing the newest report. A February27 original magazine supplies additional BESI history; the latest eligible Hildo model remains April23 because later original articles are gated. Nvidia adds an August31 Guosen cover-page model, kept separate from models with a full financial-statement cross-check. [Korean round8](KOREA_ROUND8.md), [round9](KOREA_ROUND9.md), [Mirae July14 original](KOREA_ROUND10.md), [BESI round8](BESI_ROUND8.md), [round9](BESI_ROUND9.md), [US/Europe round8](US_EUROPE_ROUND8.md), [round9](US_EUROPE_ROUND9.md), [round10](US_EUROPE_ROUND10.md).

Eleven exact-byte archived originals establish conservative historical available-by bounds. Strict mode begins only after those bounds, never retrospectively at the printed report date. The November2024 Guosen report repeats the complete August financial model, and the May2022 Korean table repeats an April model. Both retain the older EPS age. ASML's broker-specific unadjusted figures are separated from issuer-reported diluted EPS after denominator evidence; unproven TwelveData financial-currency rows are quarantined.

## What remains data-limited

The real reviewed compatibility groups currently have at most one independent firm at a time. The ensemble machinery works with multiple contributors, but the public evidence does not yet justify a multi-firm combination. It can already join compatible author/team succession within a firm, without manufacturing extra votes. Multi-contributor behavior is tested with explicitly isolated fixtures that never enter production data. The final [Samsung KB/Mirae definition audit](SAMSUNG_ENSEMBLE_BASIS.md) records why matching one historical EPS number is insufficient.

The eight EPS pairs cover only five distinct company-years. The accuracy view separates company, analyst, earnings basis and forecast horizon, with sample sizes and error measures. Historical consensus benchmarks are missing. It presents no best-predictor label. There are no verified complete 180/365-day backtest reference windows among the 66 series; the fixed [backtest protocol](../BACKTEST_PROTOCOL.md) remains unexecuted. Missing prerequisites are exact availability history, complete compatible estimates, audited trading sessions, dividends/cash returns, costs and a fixed study selection. A period of negative earnings is a legitimate P/E limitation, not missing data a subscription can fill.

## Exact handoff and retrieval boundary

[Delivery diagnostic](../../data/market/delivery_report.json) contains company/model counts, current ages, every missing-date range, all compatibility groups and all blocked fixed-horizon outcome targets. [Field/date CSV](../../data/market/missing_data_dates.csv) lists each affected retained session, fiscal targets, missing fields, default model date, alternative-series coverage and verification status. The [monthly gap map](../../data/market/monthly_gap_map.csv) and [collection targets](../../data/market/collection_targets.json) remain reproducible. Alternative series are diagnostic; they are never silently spliced together.

The documented [access checkpoint](../ACCESS_CHECKPOINT.md) distinguishes publisher subscription gates, incomplete historical data products and public retrieval failures. It specifies the smallest evidenced BESI article entitlement, the exact data sample needed for the full ten-name revision history, and why no ScrapingBee purchase is justified. Public originals can still surface; absence from tested routes is not proof that all other public routes are exhausted. The broad remaining archive cannot be presented as a complete, verified point-in-time panel from the retained material.

Grok was used through available local access for discovery and linked original-source leads. Its text and search snippets did not supply production estimates. X-specific retrieval was not established and is not claimed. Its bounded attempts and the distinction between claimed and verified access are retained in `data/discovery/round8_grok/`.

## Verification and reproducibility

The final build passes. Calculation/unit/data checks: 35. Python pipeline checks: 28. Browser workflows: five. These cover aggregation order, point-in-time membership, reprints, negative EPS, splits, fiscal mismatch, consensus exclusion, exact review scopes, source tampering, price conflicts, exports and persistence. Browser inspection covers desktop and 390px mobile with no page errors or horizontal page overflow. Screenshots are in `docs/screenshots/`; numeric browser observations are in `data/market/browser_delivery_review.json`.

The [refresh command](../REFRESH.md) archives input metadata, review policies, calculation code, previous/resulting datasets and build logs, and restores generated artifacts on failure. Originals retain source URLs, hashes, extraction evidence and reproducible helpers in their collection directories. Named-estimator NTM exports can be imported under the [sample contract](../DATA_SAMPLE_REQUEST.md) once their semantic and timing claims are verified.

Final successful archived refresh: `data/refresh/20260910T190635.287219Z`. Delivery metrics and test counts: `data/app_delivery.json`.
