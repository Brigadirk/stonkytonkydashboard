# BESI addition

Completed 10 September 2026. BESI is the tenth stock in the dashboard, with EUR prices, dated annual earnings forecasts, current price bands, the multiwindow overview, source archive, monthly gap map and exports.

## Listing and prices

The selected security is BE Semiconductor Industries ordinary shares on Euronext Amsterdam, symbol BESI, ISIN NL0012866412. The issuer identifies the ordinary listing separately from its OTC ADR. Its consolidated financial year ends on December 31 and its financial statements use EUR. [Issuer annual report 2025](https://www.besi.com/fileadmin/data/Investor_Relations/_Semi__Annual_Reports/Annual_Report_2025.pdf), physical pages 159 and 196; [share information](https://www.besi.com/investor-relations/share-information/).

The targeted `BESI.AS` collection retained 1,537 split-adjusted daily closes from September 10, 2020 through September 10, 2026. Cash dividends are excluded. No split event appears in this retained window. All price rows and earnings series for the previous nine companies are unchanged, verified against the saved pre-addition bundle. [Validation](../../data/market/besi_addition_validation.json) and [issuer source manifest](../../data/collection/besi_issuer/manifest.csv) retain the evidence. The annual-report publication date is left blank because its historical availability was not established.

## Earnings coverage

The addition contains 62 raw forecast observations, including revenue and quarantined candidates. There are 23 eligible annual EPS observations across nine dated snapshots and five separate earnings series.

| Series | EPS observations | Snapshots | Dates with bands | Current bands |
| --- | ---: | ---: | ---: | --- |
| Hildo Laman, IEX; EPS basis unspecified | 10 | 3 | 214 | Yes |
| StockWatch, LSEG consensus; EPS basis unspecified | 6 | 2 | 137 | No; latest model exceeds 180 days |
| Eugene Investment, Bloomberg consensus; EPS basis unspecified | 2 | 1 | 32 | No |
| Javier Correonero, Morningstar; diluted EPS, adjustment unresolved | 3 | 1 | 102 | No |
| Javier Correonero, Morningstar; isolated EPS statements, basis unresolved | 2 | 2 | 0 | No; consecutive fiscal targets missing |

Counts use a 365-calendar-day valuation window and a 180-day maximum model age. The union across separate series covers 350 distinct price dates with bands. Those dates are not pooled into a single analyst or consensus history. The default IEX series starts drawing bands on November 4, 2025 and supports the current close. Earlier price history remains visible without invented earnings bands.

The latest eligible IEX model was published April 23, 2026 and estimates FY2026–28 EPS of €4.18, €5.62 and€6.33. Its first-person forecast discussion and author disclosure support attribution to Hildo Laman, with his full name verified in the earlier IEX articles. The completed FY2025 column was excluded despite being labelled E in the table. [Original licensed IEX article on Saxo](https://www.home.saxo/nl-nl/content/articles/iex-analysis/iex-analyse---besi-23042026).

The February 19, 2026 LSEG table estimates FY2026–28 EPS of €3.35, €4.93 and€6.15. It remains a separate consensus series with no individual analyst assigned. [Original StockWatch publication on Saxo](https://www.home.saxo/nl-nl/content/articles/equities/stockwatch-besi-jaarcijfers-19022026).

## Provenance and exclusions

[BESI broker research](BESI_BROKERS.md) records the IEX, LSEG and Bloomberg sources and 14 quarantined rows. Hana's EPS rows conflict with the currency labels. A July 2025 StockWatch table lacks adequate forecast attribution, and the Kasikorn source has both attribution and period conflicts. These rows cannot enter the chart.

[Morningstar research](BESI_MORNINGSTAR.md) records the intact May 2024 report obtained from a third-party forum mirror, an August 2024 original distributor report containing a BESI peer forecast, and a July 2025 publisher excerpt. The last item is explicitly an excerpt artifact, not a retained original HTML/PDF. The isolated statements cannot supply a complete next-twelve-month model. Report dates are known, but original dissemination times remain unverified.

Morningstar's Amsterdam security ID was verified, but 25 Firstrade URL checks returned 404. BESI has therefore not been added to the Firstrade discovery list. Its price feed participates in normal refreshes; the documented IEX, LSEG and Morningstar routes require further collection and review for new EPS vintages. No subscription, ScrapingBee credits or provider contact was needed.

No adjustment or dilution equivalence was inferred for the new sources. Their labelled series remain separate from each other and from issuer-reported outcomes. No BESI analyst-accuracy ranking or trading backtest is claimed.

## App and validation

The ten-stock dataset now contains 13,924 closes, 912 eligible annual EPS observations, 266 snapshots and 59 earnings series. The source catalog contains 276 unique relevant broker PDFs and 1,864 raw forecast observations. The public seed register contains 431 URLs. Hildo Laman and Javier Correonero were added to the candidate register without accuracy ranks.

The refresh completed with before/after archives and input hashes in [the successful run](../../data/refresh/20260910T172908.012748Z/run.json). All 43 checks passed: 21 frontend/unit/dataset tests, 19 Python tests and three browser tests. These include BESI's EUR chart, source archive and CSV export, the ten-stock navigation/overview/gap map, and mobile layout. The production build passed. [Desktop](../screenshots/besi-price.png), [overview](../screenshots/besi-overview.png) and [mobile](../screenshots/besi-mobile.png) screenshots were inspected.

The price-axis calculation is unchanged: each date's available forward-EPS proxy multiplies the historical median P/E and its ±1, ±1.5 and ±2 sample-standard-deviation levels. The window remains editable in calendar days. Historical EPS gaps stay visible.
