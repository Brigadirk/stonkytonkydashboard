# Data access and remaining gaps

Updated 10 September 2026. The requested ten-stock app is implemented with individual, overlay and compatible median/mean ensemble views. It has 13,928 daily closes, 1,066 eligible annual EPS observations, 319 model snapshots and 66 earnings series. All ten stocks have current price bands. [Complete delivery and tests](research/ENSEMBLE_COLLECTION_DELIVERY.md).

## What requires more evidence

The app supports multiple independent contributors, but no reviewed real group currently establishes more than one independent firm at a time. Unresolved definitions, different share denominators and accounting adjustments remain separate. A named team is one estimator; published consensus is not another analyst. [Samsung KB/Mirae check](research/SAMSUNG_ENSEMBLE_BASIS.md).

BESI's latest eligible Hildo model remains April 23, 2026. We recovered the February 27 magazine and retained a September 10 S&P consensus snapshot, but the latter has only one annual EPS target and an unknown numerical revision date; it cannot supply an invented FY2027. Newer June 19 and July 23 IEX originals require publisher access. Nvidia, SK hynix and Samsung now have newer source-backed alternatives; exact current dates/ages are in the delivery report.

The EPS evaluation has eight matched horizon pairs across five distinct company-years from 48 initial issuer EPS outcomes. It still needs more exact-basis forecasts and completed outcomes, plus a contemporaneous consensus benchmark at each cutoff. No analyst rank is justified. The fixed backtest has zero series with complete verified 180/365-day reference history; its [prerequisites and rules](BACKTEST_PROTOCOL.md) remain explicit.

## Exactly which dates and fields are missing

[Missing field/date CSV](../data/market/missing_data_dates.csv) lists each affected retained price session, relevant fiscal targets, model/report date, reference coverage, alternative-series coverage and availability status. [Delivery JSON](../data/market/delivery_report.json) includes every default-series and any-series missing interval, all compatibility groups and each blocked fixed-horizon actual comparison. The fiscal targets need a then-available, sufficiently fresh numerical model; a daily list of unsupported dates is not a request to invent a new analyst revision each day.

The following table isolates dates when even the union of collected series cannot supply eligible EPS. This union is diagnostic; the app never splices incompatible series. Default author/basis series often have larger gaps, detailed in the JSON.

| Stock | Dates with no eligible EPS in any collected series |
|---|---|
| AVGO | 2021-09-10 to 2022-05-27; 2022-12-01 to 2022-12-09; 2023-03-01 to 2023-03-03 |
| GOOGL | 2021-09-10 to 2021-12-14; 2023-01-17 to 2023-02-03; 2023-04-24 to 2023-04-26; 2024-01-22 to 2024-01-31; 2024-10-23 to 2024-10-30 |
| NVDA | 2021-09-10 to 2021-12-06; 2023-02-06 to 2023-02-24 |
| 000660 | None in the requested five years (P/E can still be unavailable with losses) |
| 005930 | 2021-09-10 to 2021-11-11 |
| MU | 2021-09-10 to 2021-12-21; 2022-03-28 to 2022-03-30; 2022-11-09 to 2022-12-22; 2023-03-29 |
| SNDK | 2025-02-24 to 2025-08-15 |
| ASML | 2023-01-17 to 2023-04-19; 2024-06-06 to 2024-07-18; 2025-10-14 to 2025-10-15 |
| AAPL | 2021-10-26 to 2022-01-28; 2022-07-27 to 2022-07-29; 2022-10-26 to 2023-02-03; 2025-05-01 to 2025-05-02 |
| BESI | 2021-09-10 to 2023-10-16; 2024-01-02 to 2024-05-03; 2024-10-23 to 2024-12-30; 2025-01-02 to 2025-10-06 |

Across the broader 2021-09-10 to 2026-09-10 study, missing fields include analyst/firm identity through time, complete annual EPS revision vectors, exact earnings numerator and share denominator, currency, fiscal period boundaries, split bases, original publication/provider-availability times and historical consensus constituents. Request history from 2020-09-10 for a one-year warm-up. Sandisk's current standalone listing starts 2025-02-24; earlier predecessor prices cannot supply its missing standalone record.

Original availability is generally unverified outside the 11 exact-byte archived reports; the JSON records the precise remaining dates even where ordinary report-date bands can be drawn. The two Korean September 19, 2025 closing prices are retained as source-native observations, but their historical adjustment convention is not independently established. They remain unfilled in valuation prices. No proxy purchase is needed merely to retrieve them. [Price evidence](research/PRICE_SUPPLEMENTS.md).

## Public routes tried

Morningstar originals were collected from publicly distributed dated Firstrade PDFs, existing publisher mirrors and retained historical files. Older tables were checked against exact original report pages to distinguish adjusted, issuer-reported and broker-specific EPS. Korean work used Meritz, Mirae, KB and Hana originals, broker archive links, exact-byte Wayback/CDX captures and official channel descriptions linking originals. The missing Mirae July 14 model was recovered through its official channel's link. Telegram/video dates alone were not treated as immutable availability evidence.

BESI routes included original IEX public excerpts, Saxo/StockWatch republications and sitemaps, public IEX magazine PDFs, the issuer research directory, New Street report listings, Bolero/KBC, UBS disclosures, S&P/StockAnalysis, TwelveData, Add Value Fund reports and original publisher searches. Attribution, currency and EPS-definition failures remain documented exclusions. The newer IEX/New Street reports show entitlement gates. MarketScreener/AlphaValue failures are retrieval issues with unproven report entitlement, not proof a proxy unlocks a full model.

Guosen and Southwest original reports came through public broker-report distribution. Original Guosen cover-page images recovered from a public preview supplied verified observations with explicit full-model limits; the missing complete PDFs were not reconstructed. Grok supplied discovery leads only. Public Euronext pages rendered locally supplied both Amsterdam September 7 closes. Detailed sources, failed candidates, retained files and reproducible helpers are linked from the [delivery report](research/ENSEMBLE_COLLECTION_DELIVERY.md).

## Smallest evidenced access steps

| Need | Proven access route | Purchase boundary |
|---|---|---|
| Read the identified newer BESI IEX originals | IEX Premium's shortest advertised term is €17.95/month; Premium includes online articles | This is recurring article access. The unseen annual tables and EPS definitions are not guaranteed. Plus is not required for ordinary Premium articles |
| Complete named-analyst revision history and matched actuals for all ten names | FactSet Estimates detail or LSEG I/B/E/S detail are relevant product categories | Exact package, export rights, universe coverage, minimum term and price remain unverified. Validate a sample before choosing anything |
| Render or retrieve a genuinely public blocked page | Local HTTP/browser retrieval succeeded for the numerical additions | No critical URL has been demonstrated to require ScrapingBee. No purchase is justified now |

The IEX price and entitlement are verified on its [subscription selector](https://premium.iex.nl/marktplaats/abonnement.aspx?type=digitaal) and [one-month order page](https://premium.iex.nl/marktplaats/order.aspx?id=421). The precise targets are the [June 19 article](https://www.iex.nl/Premium/Adviezen/868324/Koersdoelverhoging-voor-Besi.aspx) and [July 23 article](https://www.iex.nl/Premium/Adviezen/871925/Orders-Besi-overtuigen-resultaten-net-niet.aspx). Review renewal/cancellation terms; this is not a verified one-off €17.95 total purchase. [Full BESI access check](research/BESI_ACCESS_OPTIONS.md).

For the ten-name archive, the smallest requested deliverable is a historical detail export covering these securities, matched actuals and historical consensus. A one-time export has not been confirmed as an available package. The [exact sample specification](DATA_SAMPLE_REQUEST.md) is ready, but no provider has been contacted. [FactSet capabilities](https://insight.factset.com/resources/factset-consensus-estimates-datafeed), [LSEG I/B/E/S](https://www.lseg.com/en/data-analytics/financial-data/company-data/ibes-estimates), [access audit](research/MARKET_DATA_ACCESS_ROUND8.md).

A cheap retail screen has not been demonstrated to meet this requirement: TIKR explicitly lacks individual analyst/bank estimates, Koyfin restricts equity-estimates exports, and Fiscal.ai's inspected API did not document the required revision endpoint. [Primary-source retail comparison](research/RETAIL_ESTIMATES_ACCESS.md). ScrapingBee's cheapest listed paid plan is $19/month, but spending it has no demonstrated benefit for the remaining required fields. [Pricing](https://www.scrapingbee.com/pricing/).

The implemented app and verified public collection are delivered at this access checkpoint. Public originals may still surface; this is not a claim that none exist outside the tested routes. Subscription-only information, unverified data semantics and public retrieval limitations are recorded separately. Nothing has been bought.
