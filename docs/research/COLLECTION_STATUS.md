# Public collection status

Updated September 10, 2026. The requested companies are Broadcom, Alphabet, Nvidia, SK hynix, Samsung Electronics, Micron, Sandisk and ASML. The target outcome window is September 2021 through September 2026; earlier warm-up documents are retained separately.

This document preserves the first-pass baseline. The [second-pass report](ROUND2_PROGRESS.md) has the latest collection counts and comparison work.

## What is saved

| Material | Count | Meaning |
|---|---:|---|
| Relevant broker PDFs | 66 | 37 Korean reports and 29 U.S./ASML reports. Some are multi-company sector reports or commentary. |
| Labelled public publisher-text extracts | 3 | Search-retrieved facts where the full article could not be archived directly. |
| Issuer/regulator source files | 90 | 26 Samsung earnings decks, 26 Samsung financial statements, 21 Hynix results pages, 12 SEC JSON files, five issuer archive pages. |
| Extracted forecast/consensus observations | 356 | Fiscal-year/metric/source appearances, not independent outcomes or a complete analyst history. |
| Raw SEC financial facts | 2,190 | Six issuers, with original filing vintages and unresolved accounting/share-basis reconciliation. |

The catalog contains 159 unique retained source contents across those categories. One additional downloaded PDF was an unrelated BESI search match and is explicitly excluded. The four original pilot PDFs remain separately retained; copies already represented in the collection do not increase these unique-content counts.

The forecast file contains 322 unscored analyst observations, eight embedded consensus observations and 26 quarantined observations. The quarantine includes conflicting fiscal headers, source-internal EPS conflicts and search-only estimates. Eight Sandisk observations have unresolved underlying author and fiscal-period interpretation. No analyst is assigned an accuracy rank.

## Company coverage

| Company | Extracted rows | Main public evidence | Largest gap |
|---|---:|---|---|
| Broadcom | 43 | Morningstar 2025 models; BOCOM 2025–2026 models | Original shortlist's institutional models and 2021–2024 forecasts |
| Alphabet | 33 | Morningstar 2025 models | Original shortlist's institutional models and earlier years |
| Nvidia | 24 | Morningstar 2024 model; BOCOM 2024–2026 material | Original shortlist's institutional models and 2021–2023 forecasts |
| SK hynix | 102 | Five Korean brokers; dated report coverage across 2021–2026 | Complete sequences, Mirae gaps, consistent historical consensus |
| Samsung Electronics | 86 | Five Korean brokers; dated report coverage across 2021–2026 plus warm-up | Complete sequences, Mirae gaps, consistent historical consensus |
| Micron | 57 | Morningstar 2024–2025 models | Institutional peer histories and 2021–2023 forecasts |
| Sandisk | 8 | Quarantined Morningstar publisher-text extract from 2026 | Attributed original standalone models since the 2025 separation |
| ASML | 3 | Quarantined Morningstar publisher-text extracts; additional reports retained | Original analyst models and a multi-year sequence in EUR |

These row counts include quarantined and consensus observations. The [document coverage matrix](../../data/document_coverage.csv) shows report calendar years, including warm-up years. A report-year cell is not evidence of continuous coverage or an EPS table in every report. Exact dated coverage, source authors and exclusions are in the [Korean collection report](KOREAN_ARCHIVE_COLLECTION.md) and [U.S./ASML collection report](US_ARCHIVE_COLLECTION.md).

## Data files

- [Combined forecast observations](../../data/collected_forecasts.csv)
- [Source catalog and local paths](../../data/source_catalog.csv)
- [Raw SEC facts](../../data/sec_actuals_raw.csv)
- [Reviewed URLs for repeat collection](../../data/public_source_seeds.csv)
- [Collection commands and checks](../COLLECTING_DATA.md)

Every retained source is checksum-verified. Numerical extraction retains the report, physical page, original units and accounting caveats. Independent source-text spot checks covered Korean billion/trillion units and U.S. model tables. Tests verify that later content does not replace old files, service-notice HTML cannot pass as a PDF, and future filings do not enter the frozen actuals dataset. A live cache check confirmed that an existing broker PDF is reused without downloading it again.

## What remains

This pass collected the publicly obtainable sources located during the research. It did not obtain every report published by every candidate. Most of the U.S. institutional analysts on the original shortlist still have no collected numerical history. Public Morningstar and BOCOM models add a different, accessible cohort; they do not establish those firms as better forecasters.

Four Mirae PDFs remain unavailable, several public articles return 403, and some saved sector reports still require model extraction. Historical forecast availability, contemporaneous consensus, comparable actuals and adjusted EPS/share definitions must be reconciled before evaluation. Printed model dates have not been promoted to independently verified publication timestamps.

The most useful access upgrade would be a demonstrable historical individual-analyst sample from FactSet or LSEG, with the fields in the [prepared specification](../DATA_SAMPLE_REQUEST.md). FactSet documents individual analyst/broker history, consensus and actuals; we have not verified account access or a project-specific price. [FactSet estimates overview](https://insight.factset.com/resources/factset-consensus-estimates-datafeed)

No ScrapingBee credits were needed or used. They may help retrieve particular public pages, but will not fill a proprietary research archive by themselves. The [collection guide](../COLLECTING_DATA.md) records the tested access failures and relevant ScrapingBee capabilities.
