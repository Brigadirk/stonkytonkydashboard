# Public forecast archive collection: US stocks and ASML

Collection cutoff: **10 September 2026**. Requested window: September 2021–September 2026. Companies: Broadcom, Alphabet, Nvidia, ASML, Micron and Sandisk.

## Collected

The collection contains **30 downloaded PDFs with extracted text**, approximately **31.6 MB**, and **three clearly labelled publisher fact extracts retrieved through web search**. One PDF was rejected because it covers BESI rather than ASML. The remaining PDFs include company models, sector reports, commentary and an index; they are not 29 independent forecasting records.

The [manifest](../../data/collection/us_asml/manifest.csv) has 36 source records, including three unresolved downloads. Each saved artifact has a SHA-256 hash, source URL, retrieval timestamp and local path. Document status distinguishes forecast tables, quarantined tables, consensus, sector research, commentary, index-only evidence, search extracts and the rejected company match.

The [observations CSV](../../data/collection/us_asml/observations.csv) contains **168 unscored EPS/revenue observations**: 126 from Morningstar tables, 31 from BOCOM summaries and 11 from publisher search extracts. Values retain their printed units and accounting labels. Company identifiers are ticker-style collection identifiers; Alphabet uses `ALPHABET`. No price target was substituted for an earnings estimate.

| Company | 2021–2023 | 2024 | 2025 | 2026 | Extracted observations |
| --- | --- | --- | --- | --- | ---: |
| Broadcom / AVGO | No original company forecast retrieved | Sector context | Two Morningstar company PDFs and two BOCOM forecast summaries | One BOCOM forecast summary; one quarantined DBS PDF; one index-only PDF | 43 |
| Alphabet | No original company forecast retrieved | None | Three Morningstar company PDFs and one publisher report reproducing its model | None | 33 |
| Nvidia / NVDA | No original company forecast retrieved | One Morningstar company PDF; BOCOM initiation commentary | Three BOCOM forecast summaries | Two BOCOM forecast summaries | 24 |
| Micron / MU | No original company forecast retrieved | Two Morningstar PDFs with a fiscal-header mismatch | Three Morningstar company PDFs; December repeats September's numerical model | None | 57 |
| ASML | No original company forecast retrieved | Sector context and Evercore commentary | One publisher search extract and a substantive section in the October WFE sector report | One publisher search extract and a DBS report with a consensus table | 3 |
| Sandisk / SNDK | No standalone historical forecast retrieved | None | No company model retrieved | One publisher search extract with model author and accounting basis unresolved | 8 |

The machine-readable [coverage matrix](../../data/collection/us_asml/coverage_by_company_year.csv) also counts ancillary sector artifacts by company. Its totals therefore differ from the company-model counts above. Multiple company rows can reference the same sector PDF.

## Most useful original material

**Firstrade's public Morningstar archive works with ordinary HTTP downloads.** Eleven company reports were downloaded without a login or paid proxy. They cover Nvidia, Broadcom, Alphabet and Micron. The Broadcom December report includes annual revenue, diluted EPS, adjusted diluted EPS and a separate current/prior revision table; the Alphabet May report has the same useful structure. [Broadcom December 2025 report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20251211_RT.pdf), [Alphabet May 2025 report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000002HD_20250507_RT.pdf).

**BOCOM supplies an original, dated Nvidia sequence in 2025.** The February report gives FY2026/FY2027 revenue of USD 211.8/270.5 billion and non-GAAP EPS of USD 4.74/6.28. April cuts EPS to 4.34/5.78. August changes revenue to 207/269.1 billion and EPS to 4.44/6.19. Those are extracted as different published report observations; their underlying model-update timestamps and original distribution times remain unverified. [February](https://files.bocomgroup.com/download/mexp-250228e.pdf), [April](https://files.bocomgroup.com/download/mexp-250424e.pdf), [August](https://files.bocomgroup.com/download/mexp-250829e.pdf).

**ASML has a substantial original publisher report to inspect further.** Morningstar's 98-page October 2025 wafer-fabrication report discusses ASML on pages 75–77 and forecasts 9% annualized revenue growth over the next decade on page 76. It does not supply a complete annual ASML EPS table identified in this pass. The date printed on the cover is month-level; a stray September 2014 template line was not treated as the report date. [Original Morningstar report](https://www.morningstar.com/content/cs-assets/v3/assets/blt9415ea4cc4157833/blte1f66c91c1ee6729/68f1167869003d43430d65fd/Technology_Observer_-_Wafer_Fabrication_Equipment.pdf).

## Timing and content findings

- **PDF filename dates are not report timestamps.** Broadcom's `20251211` file prints 12 December 2025 at 03:31 UTC. Alphabet's `20250507` file prints 8 May at 02:42 UTC. The manifest retains the printed values separately from retrieval time.
- **Printed report time is not independently verified historical availability.** Observation fields `available_at` and `original_available_at` are blank. `printed_report_timestamp` and `availability_basis` make the weaker evidence explicit. Model dates are never silently used as availability dates.
- **New prose can accompany an old model.** Micron's December 18, 2025 report contains a new analyst note but financial tables dated September 23. It reproduces September's numbers. Its two September 2024 reports similarly reproduce a July 1 model. These repeated observations must not count as independent successful forecasts. [December PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20251217_RT.pdf), [September 2025 PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250923_RT.pdf).
- **Accounting and fiscal definitions need reconciliation.** Twelve Micron observations from the 2024 PDFs are quarantined because the forecast summary labels the fiscal year as ending October 31. Several older Morningstar summaries label EPS only as diluted even when historical values differ from reported EPS. Those observations retain an unresolved adjustment basis. [September 2024 example](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240903_RT.pdf).
- **Source errors remain quarantined.** The March 2026 BOCOM Broadcom revenue units are inconsistent; only its explicit EPS values were extracted. The mutable DBS Broadcom document contains fiscal/date inconsistencies and remains quarantined. The apparent ASML forum PDF identified BESI on its first page and throughout the model; it is preserved as rejected evidence and excluded from coverage.
- **Publications that reproduce older models do not establish earlier access.** The December 2025 Morningstar quantum report labels its Alphabet model data October 30. The November 25 Firstrade Alphabet report independently reproduces the same annual numbers with a financial-table date of October 29. These dates are retained as printed rather than forced into one assumed original timestamp. [November Alphabet PDF](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P00012BBI_20251125_RT.pdf).

## Search extracts and remaining access gaps

Direct HTTP and `web.open` both returned 403 for several public Morningstar articles. Web search exposed their publisher text. Three short, paraphrased fact extracts were saved as JSON/text with retrieval provenance; **they are not original HTML archives or PDFs**.

Sandisk's article is dated **3 June 2026**, discussing the **1 June podcast**. David Sekera presents Morningstar's forecasts, including 2026 revenue of USD 19.7 billion and EPS of USD 72.22. The source does not establish Sekera as the model author or specify the EPS accounting basis. Observation attribution is therefore blank, with presenter information in the notes. Approximate 2028/2030 revenue values are identified as approximate and must not be scored as exact estimates. [Publisher article](https://www.morningstar.com/stocks/sandisk-stock-can-you-say-bubble).

ASML's July 2025 search extract supplies EUR 34.4 billion forecast revenue for 2026. Its July 2026 extract supplies approximate 2028 revenue near EUR 70 billion and EPS of EUR 69, without a resolved EPS basis. The latter was retained from the publisher's French version. [July 2025 source](https://global.morningstar.com/en-gb/stocks/asml-reset-expectations-sends-shares-lower-fair-value-estimate-trimmed), [July 2026 source](https://global.morningstar.com/fr/actions/rsultats-de-asml-les-perspectives-long-terme-se-sont-considrablement-amliores).

No ScrapingBee credits were used. One Firstrade connection failure succeeded on a normal retry. The [Evercore February 27, 2025 PDF](https://www.evercore.com/wp-content/uploads/2025/03/Research-Insights-2-27-25.pdf) remains blocked with 403. A proxy is not needed to use the PDFs already collected; whether it helps these particular public-page failures remains untested.

The largest gap is still the original historical models of the institutional shortlist—Sur, Arya, Rasgon, Mahaney, Nowak, Anmuth, Sheridan, Lipacis, Moore, Scemama, Deshpande and Bouvignies. This collection supports extraction work and a public-source cohort. It does **not** provide five years of their forecasts or justify ranking them. All observations remain unscored.

## Files and verification

All source artifacts and intermediate files are confined to [data/collection/us_asml](../../data/collection/us_asml). The PDF batch script writes a raw `download_log.csv` on subsequent runs so it does not overwrite the reviewed manifest. The extraction script reproduces the 126 Morningstar table rows; the checked BOCOM and web-search additions are retained in the final observations CSV. Full original report content was not copied into this Markdown summary.

Verification checked that every manifest artifact and text path exists, every artifact hash matches, CSV row identifiers are unique, printed dates do not exceed the cutoff, and all observations resolve to a manifest source. These checks establish collection integrity, not forecast accuracy, historical access timing or complete accounting comparability.
