# Daily price history collected through 10 September 2026

All ten selected listings have public daily closing-price history. The collection contains **13,924 daily closes**, beginning on 10 September 2020 for nine listings and 24 February 2025 for the current Sandisk. ASML and BESI currently end on **10 September 2026**; the other eight series end on **9 September 2026**. No subscription or scraping proxy was required for this collection.

| Company | Yahoo listing | Currency | Daily closes | First date | Last date |
| --- | --- | --- | ---: | --- | --- |
| Broadcom | AVGO | USD | 1,506 | 2020-09-10 | 2026-09-09 |
| Alphabet Class A | GOOGL | USD | 1,506 | 2020-09-10 | 2026-09-09 |
| NVIDIA | NVDA | USD | 1,506 | 2020-09-10 | 2026-09-09 |
| SK hynix | 000660.KS | KRW | 1,466 | 2020-09-10 | 2026-09-09 |
| Samsung Electronics common | 005930.KS | KRW | 1,466 | 2020-09-10 | 2026-09-09 |
| Micron | MU | USD | 1,506 | 2020-09-10 | 2026-09-09 |
| Sandisk | SNDK | USD | 388 | 2025-02-24 | 2026-09-09 |
| ASML Amsterdam ordinary | ASML.AS | EUR | 1,537 | 2020-09-10 | 2026-09-10 |
| Apple | AAPL | USD | 1,506 | 2020-09-10 | 2026-09-09 |
| BE Semiconductor Industries | BESI.AS | EUR | 1,537 | 2020-09-10 | 2026-09-10 |

These are provider histories, not a separately audited exchange-session calendar. Missing bars remain missing. The complete listing/currency metadata, null bars and omitted live sessions are recorded in [summary.json](../../data/market/summary.json). Source URLs, download times, HTTP failures and SHA-256 hashes are in [manifest.json](../../data/market/manifest.json).

## Price and share basis

The collector reads `indicators.quote[0].close` from Yahoo's public chart response. It never substitutes `indicators.adjclose[0].adjclose`. Yahoo's own historical-price table identifies **Close as adjusted for stock splits**, and identifies Adjusted Close as additionally adjusted for dividends and capital-gain distributions. The former is the appropriate denominator-compatible price series for historical P/E work. The exact first-party definition page is retained and its wording checked by the collector. [Yahoo historical-price table](https://ca.finance.yahoo.com/quote/NVDA/history/), [Yahoo adjustment methodology](https://help.yahoo.com/kb/SLN28256.html).

Exported prices are labelled `split_adjusted_to_cutoff` only when that provider definition has been verified. Otherwise the collector labels the provider value `raw`, preventing the app from assuming a verified adjustment basis. Prices are current revisions of history, not copies of what Yahoo published on each historical day. Raw downloads preserve the version obtained in this collection.

For a historical cutoff earlier than the collection date, the collector requests split events through collection time and undoes splits occurring after the requested cutoff. This makes exported closes refer to shares as of the cutoff. It does not undo ordinary dividends because the Close field does not apply their adjustment. Forecast EPS must independently be put on that same share basis before calculating a multiple; a report issued before a split can still contain an explicitly restated EPS figure, so report date alone is not sufficient to determine its units.

The following events were matched against Yahoo's split records and issuer or regulatory sources. Here `effective_date` means **the first trading day on the new share basis**, which can differ from the legal or after-hours distribution date.

| Company | Effective trading date | New shares per old share | Primary source |
| --- | --- | ---: | --- |
| NVIDIA | 2021-07-20 | 4 | [Issuer 2021 split FAQ](https://investor.nvidia.com/files/doc_downloads/doc_faq/06/21/NVIDIA-2021-Stock-Split-FAQ.pdf) |
| Alphabet | 2022-07-18 | 20 | [Alphabet 8-K](https://www.sec.gov/Archives/edgar/data/1652044/000119312522167375/d294315d8k.htm) |
| NVIDIA | 2024-06-10 | 10 | [Issuer 2024 split FAQ](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf) |
| Broadcom | 2024-07-15 | 10 | [Issuer announcement](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2024-financial) |

No other split events were returned for these nine listings in the requested history. This is a statement about the downloaded event series, not an independent exhaustive corporate-action audit.

The current Sandisk is restricted to regular-way trading after its separation. Its issuer announced that the independent company would begin Nasdaq trading on **24 February 2025**. Any earlier when-issued bars returned under SNDK are excluded; the former pre-acquisition Sandisk is not joined to this series. [Sandisk separation announcement](https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation).

## Session completion and missing bars

Daily timestamps are interpreted in each listing's exchange timezone. Historical days are admitted; a same-day bar requires Yahoo's regular session end plus a 20-minute publication allowance to have elapsed. Bars dated after the cutoff, bars from a future local date, null closes, nonfinite values and nonpositive values are rejected. A live `regularMarketPrice` is retained only as diagnostic metadata and is never substituted for a missing daily close.

At collection time, 10 September's New York and Amsterdam sessions had not completed. Korea's session had completed, but its 10 September daily Close values were null in the history response. Those values are left absent. Both Korean series also contain a null bar on **19 September 2025**; ASML contains one on **7 September 2026**. Separate short-range requests to Yahoo's second chart host returned the same five null bars, and those responses are retained. There is no interpolation or forward fill in the exported price file.

The successful price sources and Yahoo adjustment definition were archived. NVIDIA's split FAQs were also retained. The direct download of Alphabet's SEC split filing returned HTTP 403, while the Broadcom and Sandisk issuer pages timed out; the cited contents were verified through web retrieval instead. These failed supplementary downloads do not affect the eight successful daily-price downloads.

## Files and reproduction

- [prices.csv](../../data/market/prices.csv): `company_id,date,close,currency,adjustment_basis,source_url,source_sha256`.
- [splits.csv](../../data/market/splits.csv): `company_id,effective_date,ratio,source_url`.
- [manifest.json](../../data/market/manifest.json): request/response provenance and immutable raw-file locations.
- [summary.json](../../data/market/summary.json): coverage, missing bars and adjustment status.
- [validation.json](../../data/market/validation.json): source-hash, cutoff, session-completion, split-normalization and offline-rebuild checks.
- [collect_prices.py](../../scripts/collect_prices.py): bounded public collection and offline rebuild.

Run from the project root:

```sh
python3 scripts/collect_prices.py --start 2020-09-10 --cutoff 2026-09-10
python3 scripts/collect_prices.py --start 2020-09-10 --cutoff 2026-09-10 --offline
```

The chart endpoint is a first-party public service, but it is not a documented, contracted data API with an availability guarantee. Yahoo separately says CSV downloading through its website requires a Gold subscription. This collector successfully obtained the public chart JSON; it did not use that paid download feature or bypass a paywall. A future endpoint failure would be an access problem to investigate, not proof that a particular subscription fixes it. [Yahoo historical-data download help](https://in.help.yahoo.com/kb/finance/download-historical-data-yahoo-finance-sln2311.html).

The remaining market-data barrier for the full forward-valuation app is historical forecast/consensus availability and quality, not the daily prices obtained here. Prices alone cannot establish contemporaneous forward P/E or analyst accuracy.

## Apple addition in round 5

The targeted AAPL collection added 1,506 split-adjusted daily closes and preserved the original 10,880 rows for the other eight stocks. The retained Yahoo definition again passed verification. Apple’s four-for-one split began adjusted trading on August 31, 2020, before this price window; no split event occurs within the retained Apple window. [Issuer announcement](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/), [Apple research and fiscal evidence](APPLE_ROUND5.md). Reproduce a targeted collection with `python3 scripts/collect_prices.py --companies apple`, using the same start and cutoff as the existing dataset.

BESI’s targeted collection added 1,537 EUR daily closes while preserving all previous nine-stock price rows exactly. No split event occurs in the retained BESI price window. Listing and fiscal evidence are recorded in [BESI_ADDITION.md](BESI_ADDITION.md).
