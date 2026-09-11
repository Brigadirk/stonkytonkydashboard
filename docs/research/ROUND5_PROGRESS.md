# Gap map, price-band views and Apple: round 5

Delivered 10 September 2026. The user requested a company/month gap map, targeted source collection, earnings-definition reconciliation and a forecast-evaluation pilot, and added Apple to the universe. During implementation, the user clarified that the main chart should compare actual share prices with prices implied by historical forward-P/E levels. The graph and headline cards now use the listing currency throughout.

## Delivered application

- Apple is registered as NASDAQ AAPL in USD, with 1,506 daily closes. The previous eight stocks' 10,880 price rows were checked byte-for-value equivalent after the targeted collection. Total prices: **12,386**.
- The main chart plots actual price against `forward EPS(t) × [historical median P/E(t) ± k × historical P/E standard deviation(t)]`, for k = 1, 1.5 and 2. The headline cards show −2σ, median and +2σ prices and the actual price's percentage difference from the median-implied price. Old saved P/E-axis preferences now open the price view. Negative implied lower prices are explicitly omitted.
- The All stocks tab compares price versus median-implied price across 90, 180, 365, 730, 1,095 and 1,826-day windows. Each stock keeps one source across windows. Tooltips give −2σ, median and +2σ price levels; clicks open the corresponding stock/window. Reference counts disclose sparse long-window history.
- The interactive monthly gap map allows source selection per stock, starts at recent months, supports navigation back through the five-year interval, and exports CSV. A month inspector separates no forecast, stale model, missing fiscal targets, nonpositive EPS and unverified availability. Dates usable only in another analyst or accounting series are marked separately and never pooled silently.
- The EPS comparison tab displays eligible fixed-horizon forecast/result pairs with original sources, split-normalized values and explicit exclusions. The existing Korean revenue pilot remains available below it.

All nine names have usable current price bands at the latest price date, **9 September 2026**, under the default 180-day model-age limit. The data cutoff is September 10. Histories remain incomplete, and the public reconstruction's original first-publication timestamps remain unverified.

## Source collection and coverage

The archive grew from **180 to 244 relevant broker PDFs**, from **1,239 to 1,669 raw forecast/consensus observations**, and from **619 to 850 eligible annual EPS observations**. There are **246 model snapshots in 54 separate series**. These are fiscal-target and accounting-series counts, not independent predictions. The public seed register now contains **380 URLs**.

| Company | Eligible annual EPS observations | Unique retained price dates with bands |
|---|---:|---:|
| Broadcom | 101 → 111 | 950 → 930 |
| Alphabet | 77 → 80 | 938 → 967 |
| NVIDIA | 105 → 115 | 1155 → 1155 |
| SK hynix | 109 → 113 | 1140 → 1155 |
| Samsung Electronics | 69 → 75 | 1130 → 1169 |
| Micron Technology | 82 → 82 | 1027 → 1007 |
| Sandisk | 54 → 54 | 247 → 247 |
| ASML | 22 → 105 | 615 → 1157 |
| Apple | 0 → 115 | 0 → 1103 |

The band counts are unions of usable dates across separate series, including retained warmup prices. They are not a pooled or uninterrupted analyst history. Moving a proven model into an explicit accounting series can remove its old series' inherited reference distribution: Broadcom and Micron each lose 20 union band dates at such a boundary while the new series builds its first 20 valid prior observations. The forecasts remain retained; a basis change does not justify carrying an unverified valuation distribution across the boundary. The same-series histories used by current default views improve.

Reproduce with `node scripts/compare_round5_coverage.mjs`. [Coverage comparison](../../data/market/round5_coverage_comparison.json), [monthly gap map](../../data/market/monthly_gap_map.csv), [targeted collection backlog](../../data/market/collection_targets.json).

### Apple

[Apple collection and issuer evidence](APPLE_ROUND5.md): 29 original Morningstar reports, 20 numerical model dates through September 9, 2026, 227 extracted forecasts, and five initial annual issuer releases. Reprints preserve older model dates. The September 9 model becomes usable September 10; it does not enter September 9's closing-price calculation. Apple follows the last Saturday in September fiscal calendar. Its most recent split predates the retained price window. The new universe entry is also accepted by the existing validated NTM import route.

### ASML

[ASML collection](ASML_ROUND5.md): 26 original PDFs, 141 nonquarantined observations and 16 usable model dates. July 2026 provides fresh explicit reported/adjusted diluted EUR EPS, with earlier explicit vintages in January and April. The report's U.S. trading-currency header does not change its explicitly EUR-denominated financial model. Older 2022–2025 originals extend the archive; ambiguous legacy adjustment definitions stay separate. Six observations with shifted fiscal labels remain quarantined.

### Korean January 2026 gaps

The first monthly export identified a shared January/early-February gap. [Targeted Korean collection](KOREA_ROUND5.md) added five usable Meritz/Sunwoo and KB/Jeff models, 10 annual EPS forecasts and 10 revenues from January and February 2026. An additional January 8 report was retained but supplied no annual EPS. Opening-January gaps remain; later January models are not backdated to fill them.

At default series selections, the current backlog has only two company/month gaps in 2026, both opening-January Korean coverage. This compares with 16 in the previous eight-stock baseline. Older gaps and alternate-series histories remain visible. Default series can change when valid additional history is admitted, so this is a usability measure, not a controlled estimate of archive completeness.

## Reconciliation and EPS evaluation

[U.S. evaluation and exact-table evidence](US_EVALUATION_ROUND5.md) adds 20 original initial annual results releases for Broadcom, Alphabet, NVIDIA and Micron, with 35 EPS actuals. Apple's five compatible issuer outcomes bring the independent EPS outcome archive to **40**. Initial issuer values are used, including Apple's FY2025 diluted EPS of 7.46 rather than Morningstar's later historical table value of 7.47.

Five exact-vector bridges establish the basis of particular older Morningstar models: Broadcom March 2025 and December 2024, NVIDIA November 2024, Micron December 2024, and Alphabet February 2025. Rules are restricted to company, analyst, publisher, original basis, model date, proven fiscal periods and original source hash. Both EPS and revenue corroborate the fiscal mapping where later revision templates shift headers. [Scoped aliases and source evidence](../../data/market/basis_aliases.json). Unmatched later fiscal targets and other model vintages remain unresolved. New supporting originals also add 36 actual source observations; prior revision columns are evidence only and are not backdated as new forecasts.

The EPS pilot admits **three comparable reported diluted pairs**: Apple FY2025 at 180 days, and Broadcom/Alphabet FY2025 at 90 days before the initial annual release. It also evaluates 365-day cutoffs; no pair qualifies at that horizon yet. Each selected forecast must be published before its cutoff and have a model at most 90 days old. For example, Broadcom's April 3 reprint is excluded at the 180-day cutoff because its March 6 model is 100 days old, even though the PDF itself is newer. Both forecast and actual EPS are normalized for subsequent splits to the data cutoff.

[EPS pairs and exclusions](../../data/eps_pilot.json) records 117 excluded company/year/basis/horizon combinations. The 90-day horizon makes a short-horizon exploratory comparison available; no analyst rank is inferred. Old historical EPS matching a GAAP or non-GAAP actual is insufficient proof that the forecast itself uses that definition. Morningstar adjusted EPS is not assumed equivalent to issuer non-GAAP EPS. Contemporaneous consensus benchmarks and broader comparable outcomes remain necessary to evaluate the best forecasters.

## Verification

The production build passes. **19 frontend calculation/data tests, 14 Python tests and two browser tests pass.** Coverage includes all nine stocks, current bands, as-of restrictions, the user's price300/18× example, split normalization, stale reprints, model/period/source-scoped aliases, nonpositive EPS, monthly gap categories, exports, source selection, old multiple-view preferences, and mobile width across the new tabs. Browser checks render real median traces for Apple, ASML and Sandisk.

[Apple price view](../screenshots/round5-apple-price.png), [overview](../screenshots/round5-overview.png), [gap map](../screenshots/round5-gaps.png), [EPS evaluation](../screenshots/round5-eps-evaluation.png).

No ScrapingBee credits, market subscription or external messages were needed. Public sourcing can continue from the exported backlog. Complete historical availability, unresolved definitions and comparable forecast evaluation remain data work; no unsupported figures are filled in to make a continuous chart.
