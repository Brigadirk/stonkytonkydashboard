# Public collection and chart coverage, round 4

Collected and integrated on 10 September 2026. This pass increased the retained archive from **77 to 180 relevant broker PDFs**, raw extracted forecast/consensus observations from **491 to 1,239**, and usable annual EPS observations from **198 to 619**. The dashboard now has **184 model snapshots in 44 separate series**. Of the EPS observations, 565 are individual forecasts and 54 are published consensus; the 44 series divide into 33 individual and 11 consensus series. These counts include distinct accounting definitions and fiscal targets, not independent predictions.

All eight companies support partial historical bands. Seven have current usable bands at the latest price date, 9 September 2026, under the default 180-calendar-day age limit. ASML has historical coverage but its latest verified numerical model remains too old for a current valuation. Its April 2026 publication repeats January figures and does not renew their age.

## Before and after

The following replay uses the same 365-calendar-day reference window, 180-day model-age limit and report-date availability assumptions on both datasets. Band-day counts are the union of usable dates across each company's separate series. They are **archive coverage counts**, not the coverage of one pooled analyst history or a continuous series. Changing the source can change the dates available. The app defaults to five displayed years; this audit includes retained warmup price dates too.

| Company | Usable annual EPS observations | Unique price dates with bands | Current bands in at least one series |
|---|---:|---:|---|
| Broadcom | 26 → 101 | 272 → 950 | Yes |
| Alphabet | 20 → 77 | 197 → 938 | Yes |
| NVIDIA | 13 → 105 | 414 → 1155 | Yes |
| SK hynix | 69 → 109 | 1032 → 1140 | Yes |
| Samsung Electronics | 50 → 69 | 998 → 1130 | Yes |
| Micron Technology | 20 → 82 | 215 → 1027 | Yes |
| Sandisk | 0 → 54 | 0 → 247 | Yes |
| ASML | 0 → 22 | 0 → 615 | No: latest model is stale |

The unchanged price archive contains 10,880 observed daily closes. Sandisk begins at its February 2025 standalone listing. EPS bands begin only when a dated model and enough prior valuation observations exist. Missing forecasts, stale models, negative earnings and unresolved definitions remain visible as gaps.

Reproduce the comparison with `node scripts/compare_round4_coverage.mjs`. [Machine-readable before/after results](../../data/market/round4_coverage_comparison.json), [current series replay](../../data/market/dashboard_validation.json).

## New original evidence

- [U.S. collection](US_ROUND4.md): 72 retained new PDFs, including two excluded from relevant-model coverage; 558 observations, 324 EPS. Fresh Morningstar models through September for Broadcom, July for Alphabet, August for NVIDIA and June for Micron. Earlier original reports extend into 2021–2024. Eighteen rows remain quarantined. Model dates and publication dates are distinct; multiple later PDFs reprint an older model.
- [ASML and Sandisk collection](ASML_SANDISK_ROUND4.md): 21 retained PDFs and 135 observations. ASML contributes EUR-denominated Bloomberg consensus reported in Hana originals. Sandisk contributes five William Kerwin models, August 2025–August 2026, with separate reported and adjusted diluted EPS. The current Zacks retrieval is retained only as a September 10 observation, never backdated from a mutable URL or search cache.
- [Korean collection](KOREA_ROUND4.md): 12 originals and 39 EPS observations, 37 individual and two joint-author observations quarantined. These add Meritz/Sunwoo vintages in 2022–2025.
- [Shared Hana guide extraction](HANA_GUIDE_ROUND4.md): 16 additional observations from an already-counted original, including six usable consensus EPS observations for NVIDIA, Broadcom and Micron. Four Alphabet observations remain quarantined because the source mixes company metadata and questionable fiscal labels.

The public URL seed list expanded from 188 to 291 unique URLs. Each retained original has a local artifact, SHA-256 hash and physical-page citation. Source URL, printed report/model date and unverified historical availability remain separate fields. The source catalog also retains failures and exclusions.

## Reconciliation needed to use the records

Published consensus is now selectable as its own series, with a blank individual-author field. It is not attached to the analyst who distributed the report, nor blended with an individual analyst model. Earlier consensus observations already in the archive are now eligible under the same rules, where their basis, periods, publisher and original artifact are resolved.

Korean EPS labels were sometimes different descriptions of the same table definition. Exact matches between summary and detailed tables support three narrowly scoped aliases within company, broker and named analyst: Meritz/Sunwoo, Hyundai/Roh and KB/Jeff. [Alias evidence and hashes](../../data/market/basis_aliases.json). Every panel row retains the original label and alias evidence URL. The aliases do not establish basic/diluted compatibility across brokers or with statutory actuals.

Legacy Morningstar diluted EPS with unresolved adjustments remains separate from explicitly reported or adjusted diluted EPS. Author changes remain separate individual histories. NVIDIA's adjusted-model views display an accounting-comparability note because the issuer changed its non-GAAP stock-compensation treatment from FY2027, and every analyst model's adoption has not been established. [Issuer announcement](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/).

Incorrect legacy fiscal labels were corrected only where historical columns, issuer results and later reprints identified the same periods. Literal labels remain in the raw collection, with the evidence in row notes. ASML uses calendar years ([annual report](https://ourbrand.asml.com/m/79d325b168e0fd7e/original/2024-Annual-Report-based-on-US-GAAP.pdf)); Sandisk uses the Friday closest to June 30, including FY2026's 53-week year ending July 3 ([issuer FAQ](https://investor.sandisk.com/ir-resources/investor-faqs)). A Sandisk template's December header was resolved from the issuer's June results and an exact later reprint, as documented in its collection note.

The EPS panel now includes pre-split U.S. models. Explicit share-basis dates preserve their printed denominator; the chart normalizes EPS by subsequent split ratios. A model whose publication crosses a split is rejected without an explicit share-basis date. Source inconsistencies, unresolved attribution and conflicting values are excluded or fail validation; no EPS values are guessed.

## Validation and remaining collection work

All retained catalog hashes and eligible EPS sources passed validation. The 15 frontend calculation/dataset tests, 11 Python tests and two browser tests pass. Browser checks include actual ASML and Sandisk median traces, all eight stocks, saved settings, export, strict-availability gaps and mobile width. The production build succeeds. [Sandisk screenshot](../screenshots/round4-sandisk.png), [ASML screenshot](../screenshots/round4-asml.png).

The revenue comparison pilot remains 13 pairs across eight company-years. The larger forecast archive does not by itself produce matched EPS actuals or an analyst accuracy ranking.

Public archives remain productive; no ScrapingBee credits, proxy, account or paid market subscription was needed for this pass. Remaining priorities are a fresher ASML numerical model, intermediate historical vintages, reconciled accounting definitions, verified original availability and matched actuals. A licensed historical estimates sample remains an option for systematic completeness, not a demonstrated prerequisite for further public collection. See [current access status](../ACCESS_CHECKPOINT.md).
