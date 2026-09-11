# Second sourcing pass

Completed September 10, 2026 under the [sourcing plan](../SOURCING_PLAN.md). This pass targeted missing years and began matching forecasts to issuer outcomes.

## Collection changes

| Measure | First pass | After this pass |
|---|---:|---:|
| Unique relevant broker PDFs | 66 | 77 |
| Extracted forecast/consensus observations | 356 | 491 |
| Unique retained source contents in the catalog | 159 | 174 |
| Curated Korean annual issuer outcomes | 0 | 20 |
| Illustrative revenue comparisons | 0 | 13 |

The new research contains nine new Korean PDFs, three reused sector reports with newly extracted tables, two early U.S./ASML PDFs and two original broker HTML publications. Reused PDFs do not increase the unique-document count. Two additional issuer HTML pages were retained. Grok output is discovery material and is not counted as a broker source.

The combined observations contain 389 unscored individual analyst rows, 38 unscored consensus rows and 64 quarantined rows. Total consensus observations are 44 because six also have source problems and are quarantined. These are source/metric/fiscal-period appearances, not independent outcomes.

## Gaps filled

- KB's own 2024 company pages led to four original Samsung/Hynix PDFs.
- Two Hana 2023 Hynix reports and a December 2021 Samsung daily were retrieved. Six forecast rows from the 2021 model and four from the July 2023 model have joint signatures and remain excluded from individual comparisons pending attribution review.
- A Hyundai Hynix report dated May 2026 was found with explicit third-party hosting provenance.
- Relevant tables were extracted from three previously saved sector reports.
- Original 2023 Nvidia research from Itaú BBA and Phillip Securities was collected. The Itaú fiscal labels require reconciliation; the Phillip article explicitly gives a FY2024 revenue forecast.
- A Tim Green ASML sample prints an April 2023 date, but PDF creation metadata is December 2023. Its model and embedded consensus remain quarantined for historical availability.
- An original 2023 Alphabet broker article adds a revenue-growth forecast. Growth percentages retain percentage units and are not treated as EPS or revenue amounts.

Source URLs, dates, authors, numbers and access limitations are in the [Korean round-two report](KOREAN_ROUND2.md) and [early U.S. history report](US_HISTORY_ROUND2.md). The combined [catalog](../../data/source_catalog.csv) and [forecast file](../../data/collected_forecasts.csv) include the new records.

## Grok result

The installed Grok CLI used the existing sign-in for a bounded discovery job and a short continuation. Six targeted web searches and three final page fetches were requested. The CLI exposed web search/fetch, with no native X search tool. An x.com web result therefore does not count as native X retrieval.

Grok supplied an early Alphabet media lead that was independently verified through the browser. A July 14, 2022 TipRanks article syndicated by Nasdaq attributes a FY2023 gross-revenue forecast of USD335.5bn and operating-income forecast of USD101.1bn to Mark Mahaney. The original Evercore note and full accounting definitions remain missing. The article is retained as a media-attribution lead outside the forecast dataset. [Nasdaq article](https://www.nasdaq.com/articles/googl-is-still-a-buy-amid-volatility-says-analyst)

Other leads were price targets, issuer guidance, unverified recaps or later-period research. No Grok-generated number was admitted directly as a forecast. [Prompt/results and usage](../../data/collection/grok_discovery), [reviewed lead register](../../data/collection/grok_discovery/verified_leads.csv).

The CLI reported USD0.08008234 in model usage across the two runs. This is its usage report, not an independently reconciled invoice. No new API key, account or subscription was created. Native X sourcing would require an interface that actually exposes `x_search`; the API documentation alone does not give this CLI that capability. [xAI X Search documentation](https://docs.x.ai/developers/tools/x-search)

## First comparison

[issuer_outcomes.csv](../../data/issuer_outcomes.csv) contains annual revenue for Samsung and Hynix from FY2021 through FY2025, plus Samsung's basic and diluted EPS from its audited consolidated statements. The [revenue pilot](REVENUE_PILOT.md) uses the ten revenue outcomes and has 13 matched comparisons across eight company-years. It preserves reported-result versions and does not compare broker EPS with statutory EPS automatically.

## Next work

Original 2021–2022 U.S. institutional models remain missing. So do complete sequences for each candidate, historical publication evidence and sufficiently broad contemporaneous consensus. Mirae continues to return service notices. ASML/Sandisk and the original U.S. institutional shortlist remain priorities.

The next productive step is to source common fiscal targets for competing analysts at the same horizons, reconcile the quarantined original tables, and obtain a demonstrable historical detail-data sample if public originals remain unavailable. The current data supports a reproducible pilot and a clearer access request; no five-year analyst winner has been established.
