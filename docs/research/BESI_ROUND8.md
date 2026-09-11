# BESI round 8: public forecast freshness and definition checks

Research and capture date: 10 September 2026. This collection is confined to `data/collection/besi_round8/`; previous BESI collections and app outputs are unchanged.

## Result

The collection adds 12 reviewed observations from 22 retained source or discovery artifacts. Six observations are clean extractions of currently visible consensus, comprising three annual EPS and three annual revenue estimates. Six dated IEX magazine observations remain quarantined because the forecast provider is not identified for the table.

There is **no newly recovered named-analyst annual model after the existing 23 April 2026 IEX model**, and no defensible new bridge between the unresolved BESI EPS definitions. The public consensus pair supplies a new first-observed snapshot, without proving when the underlying estimates last changed.

| Source | Proven observation/publication date | Annual EPS in EUR | Treatment |
|---|---|---|---|
| Twelve Data, public BESI analysis page | First observed 2026-09-10 17:53:52.338647 UTC | FY2026 4.38; FY2027 6.50 | Separate published consensus; revision age unknown |
| Stock Analysis, S&P Global financial forecasts | First observed 2026-09-10 17:52:42.127515 UTC | FY2026 4.38 | Separate adjusted consensus; only one public year |
| IEX Expert issue 39/2024 | Printed cover 2024-10-25 | FY2024 2.38; FY2025 3.89; FY2026 5.55 | Quarantined, table-level attribution unresolved |

The two current-page snapshots cannot fill earlier historical gaps. They are available no earlier than the retained UTC capture. Under the app's current annual-row day-after-date convention, their first usable daily date is **11 September 2026**, beyond the current 10 September price cutoff. They must not be described as new current-day bands. The `report_date` field contains observation date for these two sources, explicitly distinguished in `availability_basis` and notes from an original publication or model date.

## Current public consensus

[Twelve Data's provider-hosted BESI analysis page](https://twelvedata.com/markets/715834/stock/euronext/besi/analysis) displays current-year December 2026 and next-year December 2027 columns. The retained HTML reports annual mean EPS of 4.38 and 6.50, with 21 and 23 analysts respectively. Revenue estimates are EUR 1.00 billion and 1.35 billion at the source's displayed precision. These are consensus estimates, with no named analyst attribution. The page identifies the EUR Euronext listing but does not print a separate financial-currency footnote or explain EPS adjustments and dilution. Keep `twelve_data_consensus_eps_adjustment_and_dilution_unspecified` separate from the existing IEX, Morningstar and LSEG series.

The same page's relative 7/30/60/90-day EPS table is preserved only in `evidence/extraction.json`. There is no independently established exact date anchor for these relative labels. A cached browser representation also differed numerically from the separately retained direct response. No relative column has been turned into a historical observation or combined across captures. [Twelve Data's API documentation](https://twelvedata.com/docs) describes dated estimate objects, but the public HTML does not expose an exact model-revision timestamp. Its metadata currency describes instrument currency, not an EPS accounting definition.

[Stock Analysis's BESI forecast page](https://stockanalysis.com/quote/ams/BESI/forecast/) explicitly states financial currency EUR and identifies EPS as non-GAAP adjusted. It credits S&P Global Market Intelligence for financial forecasts and TipRanks for individual ratings. The latter are not individual EPS models. FY2026 EPS 4.38 and revenue 1.00 billion are public; the FY2027 and FY2028 cells display Upgrade/Pro. Basic versus diluted denominator and adjustment policy remain unknown. The page's August 4 footer does not establish the current numerical table's revision date, so the observations use capture date only. A shared FY2026 EPS value with Twelve Data establishes neither common definitions nor independent underlying contributors.

Current capture hashes:

| Artifact | SHA-256 |
|---|---|
| `originals/twelvedata_20260910.html` | `4bd0547a81cd1cc58b861c36d17cbb3a07400585019d40d857be11580ec253cf` |
| `originals/stockanalysis_20260910.html` | `b8a741356f10d2f4a3b0188c8e15f17176f9444e3120a72857907aa272d1d3b5` |

## Dated public IEX magazine and denominator evidence

The publisher's [advertiser sample IEX Expert 39/2024](https://img.iex.nl/IEXMedia/Adverteren/IEX-2024-39_small.pdf) has a 25 October 2024 cover date. Physical PDF page 33, printed pages 64–65, contains the BESI annual table. Expected revenue for 2024/25/26 is EUR 0.64/0.91/1.20 billion; EPS is 2.38/3.89/5.55. Physical page 37 explains EPS as net income divided by average outstanding shares in a year. It does not establish basic versus diluted or reported versus adjusted earnings.

The colophon credits Refinitiv, Infront, Bloomberg and IEX collectively for statistics. That does not identify the source of the BESI row. The six observations therefore remain `quarantined_forecast_attribution_unresolved`, not Hildo Laman forecasts or verified consensus. The original PDF hash is `ae63c46a7562bff401dfa475d1ef6f86f9a9d93b40ed0001ae53b9a0907bbe71`. Rendered physical pages 33 and 37 were visually checked and retained under `evidence/`.

No definition alias is recommended. In particular, a magazine-wide EPS explanation does not establish the accounting policy of Hildo Laman's later online model or make it equivalent to Morningstar adjusted or issuer reported diluted EPS.

## Tested access and history routes

| Route | Concrete finding | Limit |
|---|---|---|
| [IEX June analysis](https://www.iex.nl/Premium/Adviezen/868324/Koersdoelverhoging-voor-Besi.aspx) | Original printed date 19 June 2026; JSON-LD publication 09:45 UTC; Hildo Laman byline | Public excerpt ends before annual EPS; subscription article |
| [IEX July analysis](https://www.iex.nl/Premium/Adviezen/871925/Orders-Besi-overtuigen-resultaten-net-niet.aspx) | Original dated 23 July 2026 | Subscription excerpt; no annual EPS table |
| [StockWatch April analysis](https://stockwatch.nl/posts/16747/besi-versnelt-met-hybrid-bonding) | Paul Weeteling; original metadata 23 April 2026, 12:00:21 UTC | Subscription excerpt; initial lead filename says April 24 but manifest uses actual publication date |
| [StockWatch June analysis](https://stockwatch.nl/posts/16896/outlookverhoging-besi-houdt-de-koers-niet-bij) | Paul Weeteling; 18 June 2026 | Subscription excerpt; no public annual model |
| [StockWatch July analysis](https://stockwatch.nl/posts/16985/daling-en-nieuwe-kansen-maken-besi-weer-koopwaardig) | Paul Weeteling; 23 July 2026 | Subscription excerpt; no public annual model |
| [Saxo full Dutch article sitemap](https://www.home.saxo/nl-nl/article-sitemap-nl-nl-1.xml) | Checked BESI article locations; latest full syndicated IEX model remains 23 April 2026 | No newer full IEX table found in this distribution route |
| [Saxo July results article](https://www.home.saxo/nl-nl/content/articles/equities/besi-q2-cijfers-ai-vraag-neemt-toe-opent-lager-23072026) | Public 23 July 2026 issuer-results summary | No annual EPS forecast pair |
| [Saxo June 2025 outlook article](https://www.home.saxo/nl-nl/content/articles/equities/besi-verhoogt-outlook-scherp-op-investor-day-13062025) | Original visible time is 13 June 2025; StockWatch Paul Weeteling analysis | No annual EPS model. February 2026 CMS metadata is not a new model date |
| [IEX magazine archive](https://www.iex.nl/Premium/Magazines.aspx) | Public issue index and subscription download interface checked; advertiser sample retrieved separately | Full newer issues require subscription; index is not numerical evidence |
| [IEX Hildo Laman author page](https://www.iex.nl/Artikelen/Auteur/786/Hildo-Laman.aspx) | IEX tenure begins July 2023; previous work was at Beleggers Belangen | Earlier IEX dates cannot be assumed to be his models |
| [Beleggers Belangen January 2022 Hildo article](https://www.beleggersbelangen.nl/2022/01/19/optietip-257-een-nieuwe-positie-op-aperam/) | Earlier original includes a BESI options-position update | Option-premium values are not EPS; no annual forecasts extracted |
| [MarketScreener BESI page](https://www.marketscreener.com/quote/stock/BE-SEMICONDUCTOR-INDUSTRI-6318/calendar/) | Direct retrieval returned HTTP 403; denial retained | Retrieval problem. Cached browser values do not supply a retained original model |
| [Chartmill analyst page](https://www.chartmill.com/stock/quote/BESI.AS/analyst-ratings) | HTTP 200 original is a JavaScript shell | Possible rendering route; public annual table availability remains unverified |
| [Finvaulta Goldman Sachs summary](https://finvaulta.com/research/goldman-sachs/be-semiconductor-industries-update-2026-06-29) | Secondary summary gives a price target | No original linked broker annual EPS model; excluded |

Searches for older Hildo BESI annual earnings estimates also reached Beleggers Belangen portfolio and option updates without usable annual EPS. This bounded pass does not establish that no historical models exist. It establishes which public primary distribution routes were checked and what they actually exposed. No subscription purchase, paid API call, provider contact or external message was made.

ScrapingBee could be evaluated for a public page that demonstrably contains a table after rendering. Chartmill remains an unverified candidate, and MarketScreener has a concrete retrieval denial. Neither is evidence that a renderer can unlock the IEX/StockWatch subscription articles. A publisher subscription would address those articles' content-access limit; it would still require review of their EPS basis and historical revision dates.

## Reproduction and integration

Run from the project root:

```sh
python3 data/collection/besi_round8/collect.py
```

The offline collector verifies every retained source hash, asserts table headers and reviewed EPS/revenue values against the originals, rechecks the PDF table, and writes compatible `manifest.csv`, `observations.csv` and `evidence/extraction.json`. Its expected output is 22 sources, 12 observations, six clean and six quarantined. It preserves source-period labels and leaves unknown model dates blank. `--fetch` writes new timestamped originals to a separate retrieval directory and requires manual review before numerical integration; it never silently replaces an older capture.

The source model does not yet provide known compatible EPS definitions for a BESI analyst ensemble. All new consensus remains distinct, blank analyst attribution is intentional, and no forecast-accuracy evaluation should be expanded using the quarantined magazine data.
