# Collecting the research data

Run commands from the project root. Python dependencies are in [requirements.txt](../requirements.txt). PDF text extraction also uses the installed `pdftotext` command. Existing source files remain useful without rerunning collection.

## Resume reviewed source URLs

```sh
python3 scripts/collect_sources.py --seeds data/public_source_seeds.csv
```

The seed file contains 188 reviewed URLs, including unavailable sources. The default run processes at most 100 rows. Use `--limit 250` to process the full current list. A run skips files already retained and checksum-verified, including files imported through the source catalog. It tries unresolved URLs directly, with no paid proxy or credentials. It does not crawl for new URLs or fill missing years automatically.

The collector stores downloads under `data/raw/`, named by their SHA-256 hash. It records retrieval attempts in `data/archive.sqlite` and exports [download_log.csv](../data/download_log.csv). The broker collection directories also retain original PDFs, text and manifests from the research pass. Their separate manifests preserve discovery and extraction notes.

Use `--refresh` only when deliberately checking for new content at an existing URL. A changed body is saved alongside the old version. The printed report date is cleared on a changed response pending review. Neither a seed date nor an HTTP download timestamp establishes historical availability.

The initial standard-library transport encountered a local certificate-chain error. Switching to requests with certificate verification enabled resolved it. Those failed attempts remain in the log. One initially incorrect Samsung archive URL was corrected using a link on Samsung's own page; the failed attempt remains historical evidence, not an active access requirement.

## Rebuild derived files

```sh
python3 scripts/index_collection.py
python3 scripts/merge_forecasts.py
python3 scripts/extract_sec_actuals.py --since 2020-09-10 --cutoff 2026-09-10
python3 scripts/build_korean_outcomes.py
python3 scripts/compare_revenue_pilot.py
python3 -m unittest discover -s tests -v
```

The indexer checks retained files against source hashes, writes [source_catalog.csv](../data/source_catalog.csv) and [document_coverage.csv](../data/document_coverage.csv), and refreshes the SQLite source catalog. Document counts include reports with commentary or unextracted tables. They do not certify a complete forecast history.

The forecast merger discovers `observations.csv` in every immediate collection subdirectory and combines compatible schemas into [collected_forecasts.csv](../data/collected_forecasts.csv). It converts revenue to base currency units while retaining original values and units. Growth percentages retain percentage units. Accounting definitions remain separate. Repeated model values retain their source appearances and share a version key where the identity, fiscal target, metric, model date, units and values match. This key does not prove an independently published revision.

Rows with conflicting headers, conflicting source values, unresolved joint attribution or search-only evidence are quarantined. Report-embedded consensus has its own observation type. Sandisk figures presented by a speaker whose underlying model author is unverified are labelled `publisher_forecast_unattributed`. All remaining rows are unscored. Publication timing and comparable actuals still require reconciliation.

The SEC exporter keeps each filing vintage, accession, original taxonomy/tag and fact period. Its `filing_fiscal_year` is the fiscal year of the filing, which can differ from the comparative period the fact describes. It excludes facts filed after the research cutoff and does not join GAAP facts to adjusted broker EPS automatically. SEC financial facts are reported results, not analyst forecasts. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## ScrapingBee

No ScrapingBee credits were needed or used in this pass. Most original broker PDFs, Samsung statements and SEC JSON downloaded directly. Several Morningstar/Evercore pages returned HTTP 403, and Mirae returned a service notice. Some public Morningstar text was retrievable only as labelled search extracts.

ScrapingBee can retrieve public PDFs with JavaScript disabled and can render dynamic public pages. Its documentation lists one credit for a basic request without JavaScript, five with JavaScript, and higher costs for other proxy tiers. It also states a 2 MB file limit in the HTML API documentation, which makes it unsuitable as the default route for many large sector PDFs in this collection. [ScrapingBee documentation](https://www.scrapingbee.com/documentation/), [PDF retrieval instructions](https://help.scrapingbee.com/en/article/can-i-scrapedownload-pdf-with-scrapingbee-148vggh/)

A proxy can help test a specific blocked public page. It does not supply institutional research subscriptions, missing historical reports or analyst identities. The remaining five-year detail-history requirement is documented in the [provider sample specification](DATA_SAMPLE_REQUEST.md). No provider message has been sent and no subscription has been purchased.
