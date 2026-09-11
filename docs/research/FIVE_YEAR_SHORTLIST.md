# Five-year analyst shortlist

Updated 10 September 2026. This is the entry point for Dirk's request to identify the best earnings forecasters for eight companies over roughly five years.

The subsequent [public collection pass](COLLECTION_STATUS.md) saved the report archive and 356 extracted forecast/consensus observations. This document remains the candidate-selection record; the collection report has the latest retrieval counts and gaps.

## Result so far

The research has produced a candidate pool, dated coverage evidence, several firm transitions and public forecast samples extending back to October 2021. It has not produced a defensible five-year earnings-accuracy ranking. All candidates remain unranked until the historical forecasts, comparable actuals and contemporaneous consensus are assembled and evaluated.

The target outcome window is September 2021 through September 2026. Retain earlier estimates as needed to measure a full year of forecast lead time. Sandisk has a shorter standalone history beginning in February 2025.

## Candidate pool

Names are not ordered by measured accuracy. The pool helps inspect and collect data; a complete vendor export should include all historical contributors, including departed analysts.

| Company | Candidates | Reason to include |
|---|---|---|
| Broadcom | Harlan Sur, J.P. Morgan; Vivek Arya, BofA; Stacy Rasgon, Bernstein | Issuer-verified coverage, with dated 2022/2023 observations for Arya/Rasgon. |
| Alphabet | Mark Mahaney, Evercore; Brian Nowak, Morgan Stanley; Douglas Anmuth, J.P. Morgan; Eric Sheridan, Goldman Sachs | Issuer-verified coverage. Mahaney also has a 2022 issuer-call observation. |
| NVIDIA | Stacy Rasgon, Bernstein; Vivek Arya, BofA; Mark Lipacis, Evercore/previously Jefferies; Joseph Moore, Morgan Stanley | Current issuer coverage and research-history evidence. Include former contributors such as Toshiya Hari when acquiring the historical panel. |
| SK hynix | Sunwoo Kim, Meritz; Roh Geun-chang, Hyundai; Young-gun Kim, Mirae; Jeff Kim, KB; Rok-ho Kim, Hana | Two quantitative sector-award leads plus competing public models. Hynix forecasts from 2021 and 2026 are retrievable for Sunwoo and Young-gun Kim. |
| Samsung Electronics | Sunwoo Kim, Meritz; Roh Geun-chang, Hyundai; Young-gun Kim, Mirae; Jeff Kim, KB; Rok-ho Kim, Hana | Relevant Korean sector coverage and model sources. A full five-year Samsung forecast sequence has not been assembled. |
| Micron | C. J. Muse, Cantor/previously Evercore; Vijay Rakesh, Mizuho; Matthew Bryson, Wedbush; William Kerwin, Morningstar | Documented memory coverage and dated research. Morningstar models provide a public archive lead; complete individual histories remain missing. |
| Sandisk | C. J. Muse, Cantor; Vijay Rakesh, Mizuho; Matthew Bryson, Wedbush; William Kerwin, Morningstar | Issuer-verified standalone coverage. Evaluate SNDK separately from earlier WDC flash research. |
| ASML | Didier Scemama, BofA; Sandeep Deshpande, J.P. Morgan; Francois-Xavier Bouvignies, UBS; Mark Lipacis, Evercore | Issuer coverage list and a dated 2024 Evercore report. Original EPS histories in EUR remain needed. |

Every name and affiliation is supported, with dated evidence and limitations, in the [U.S./ASML audit](FIVE_YEAR_US_ASML_ANALYSTS.md) and [memory audit](FIVE_YEAR_MEMORY_ANALYSTS.md). "Verified coverage" does not mean continuous coverage for every year in the target window.

The [analyst candidate register](../../data/analyst_candidates.csv) stores these 33 company–analyst pairs across 21 people. Every accuracy rank is blank, and every row records that an evaluated five-year history is still incomplete.

## Findings that change the data collection

- BOCOM's NVIDIA initiation was December 2024 and Broadcom's was November 2025. Keep those accessible models as shorter records; they do not supply a five-year history at that firm. [NVIDIA initiation index](https://files.bocomgroup.com/download/mexp-241220e.pdf), [Broadcom initiation index](https://files.bocomgroup.com/download/mexp-260128e.pdf).
- Mark Lipacis moved from Jefferies to Evercore in April 2024. C. J. Muse moved from Evercore to Cantor in December 2023. Preserve person identity across those firm changes. [Evercore announcement](https://investors.evercore.com/node/22046/pdf), [Cantor announcement](https://www.prnewswire.com/news-releases/cantor-fitzgerald-bolsters-technology-vertical-with-two-senior-hires-in-investment-banking-and-research-302013631.html).
- Roh Geun-chang's 2026 Korean semiconductor/display award evaluates 2025 data and combines earnings estimates with target-price accuracy. Sunwoo Kim won the 2022 sector award, whose exact metric weights were not retrieved. These are useful selection signals, not stock-specific five-year EPS scores. [Organizer methodology](https://v.daum.net/v/20260618080206602), [organizer winners](https://v.daum.net/v/20260618103608353), [Meritz award record](https://www.imeritz.com/main/ir/pr_0200.html).
- LSEG's November 2025 NVIDIA note refers to two analysts with five-star earnings-estimate ratings but does not name them or expose their histories. Do not assign that rating to anyone in our shortlist. [LSEG NVIDIA Spotlight](https://lipperalpha.refinitiv.com/2025/11/starmine-spotlight-002-starmine-flags-strong-analyst-sentiment-ahead-of-nvidia-earnings/).
- Sandisk's current standalone trading started on 24 February 2025. Earlier sector experience is useful context, but cannot create a five-year record for the current equity. [Issuer announcement](https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation).

## Data already saved

[forecast_samples.csv](../../data/forecast_samples.csv) contains 16 EPS/revenue observations, checked against four original reports. These include two same-day SK hynix forecasts from October 2021 and recent September 2026 reports. [source_manifest.csv](../../data/source_manifest.csv) records the retained files and checksums. EPS denominator differences are flagged; original availability timestamps are left blank where unknown. No row is assigned a forecast-accuracy score.

The company audits contain additional historical numbers and source links, including BOCOM, KB and Morningstar. These have not all been normalized into the sample CSV. Public Morningstar reports distributed by Firstrade provide further archive leads for [Micron in September 2024](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003MC_20240903_RT.pdf), [Micron in September 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250923_RT.pdf), and [Broadcom in June 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000KU35_20250626_RT.pdf). A recent report's table of old actuals is not an old forecast vintage.

## What remains to finish

Acquire and evaluate the analyst-level history using the [proposed research definitions](../ANALYST_EVALUATION.md). The [sample specification](../DATA_SAMPLE_REQUEST.md) states the exact securities, dates, fields and access questions. The strongest verified supplier candidates are LSEG's I/B/E/S/estimate analytics and FactSet's detail estimates. Neither account access nor a project-specific price has been established. A one-time licensed export may be enough for the initial study if a supplier offers suitable terms.

Public reports allow continued collection and spot checks. They currently do not support naming eight five-year winners or computing a complete historical ranking. The source audit and candidate pool are complete for this pass; the requested accuracy result remains outstanding.
