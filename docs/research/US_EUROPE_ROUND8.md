# U.S./European forecast and outcome research, round 8

Reviewed 10 September 2026. Owned files are confined to `data/collection/us_europe_round8/` and this note. This pass adds **30 annual forecasts: 20 EPS and 10 revenue**, plus **8 initial issuer GAAP diluted EPS outcomes**. Two original Morningstar reports and thirteen original issuer documents support those additions. A separate BMO original is retained as rejected discovery evidence.

The useful improvements are a missing July 2025 Alphabet model, an earlier explicit January 2025 ASML model, new NVIDIA/Sandisk annual outcomes, and a concrete ASML denominator discrepancy that must be resolved before claiming issuer-compatible scores or combining authors. No broad earnings-definition equivalence was inferred.

## Priorities and search boundary

The current `data/market/collection_targets.json` and rounds 4–6 were reviewed first. The Alphabet October 2025 gap arose from a stale April model. ASML July 2025 reports also reprinted April models. Sandisk lacked the early portion of its new 2025 listing. Previous Broadcom/Micron/NVIDIA passes had already tested many 2021–24 archive dates and rejected generic adjusted-EPS equivalence.

`collect.py` checks candidate URLs against prior CSV/JSON discovery logs before requesting them. Of **33 bounded candidates**, three were skipped because they had already been attempted; thirty were requested, yielding two original PDFs and twenty-eight 404 responses. Successful security identifiers remain the previously verified IDs: Alphabet `0P000002HD`, ASML ADR `0P0000002X`, Apple `0P000000GY`, and new Sandisk `0P0001U8JM`. Existing Broadcom/NVIDIA/Micron report-history searches were not repeated merely to inflate the attempt count.

## New original forecasts

| Report date | Numerical model date | Analyst | Annual targets | EPS and revenue |
|---|---|---|---|---|
| [3 Sep 2025, 23:21 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000002HD_20250903_RT.pdf) | 23 Jul 2025 | Malik Ahmed Khan | Alphabet FY2025–29 | Plain and adjusted diluted EPS: **10.18 / 10.94 / 12.19 / 13.52 / 15.00 USD**. Revenue: **392,807 / 434,714 / 478,274 / 523,437 / 570,357 USD million**. Physical page 19. |
| [3 Apr 2025, 15:27 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250403_RT.pdf) | 29 Jan 2025 | Javier Correonero | ASML FY2025–29 | Plain and adjusted diluted EPS: **24.69 / 30.87 / 35.84 / 40.88 / 46.09 EUR**. Revenue: **34,201 / 38,258 / 42,868 / 46,615 / 50,409 EUR million**. Physical page 15. |

Both full tables and their original labels were visually checked. Only current forecast columns were extracted. The September Alphabet report establishes a July numerical model at a September report date; no July availability is invented. It supplies a fresh numerical vintage before the October staleness gap. Alphabet's separate plain and adjusted labels remain separate even though their numbers agree. Its historical plain EPS and net income agree with the issuer's GAAP outcomes.

The ASML report uses EUR reporting currency and USD trading currency. Its annual EUR financial forecasts can support the Amsterdam ordinary-share earnings series without currency conversion. The original security/share mapping was established in round 5. No split transformation is necessary for these 2025 models. However, the plain ASML row is recorded here as **`morningstar_unadjusted_diluted`**, because its identity with the issuer's reported diluted measure is not established by the evidence below.

## ASML issuer comparability: a denominator problem

The modern table prints a weighted-average diluted-share row and separate plain/adjusted diluted EPS. Its historical net income agrees with rounded issuer US-GAAP net income, but historical EPS is not consistently the issuer's annual diluted EPS:

| Historical fiscal year | Broker net income, EUR m | Issuer net income, EUR m | Broker diluted shares, m | Issuer annual diluted shares, m | Broker EPS | Issuer diluted EPS |
|---|---:|---:|---:|---:|---:|---:|
| FY2022 | 5,624 | 5,624.2 | 395 | 398.1 | 14.23 | 14.13 |
| FY2023 | 7,839 | 7,839.0 | 394 | 394.1 | 19.91 | 19.89 |
| FY2025 | 9,609 | 9,609.4 | 392 | 388.9 | 24.48 | 24.71 |

The first two broker rows are in the [new April 2025 report, p15](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250403_RT.pdf); FY2025 appears in the [July 2026 original, p15](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000002X_20260715_RT.pdf). The issuer values come from the initial annual US-GAAP statements: [FY2022, p1](https://media.asml.com/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/files/investors/financial-results/q-results/2022/q4/financial-statements-us-gaap-q4-2022-fgu23.pdf), [FY2023, p1](https://media.asml.com/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/files/investors/financial-results/q-results/2023/q4/financial-statements-us-gaap-q4-2023-h92dd2.pdf), [FY2025, physical p3](https://ourbrand.asml.com/m/fded19d66e819e4b/original/Financial-statements-US-GAAP-Q4-2025.pdf). FY2023 broker EPS equals issuer **basic** EPS, while FY2022 broker EPS equals neither issuer basic nor diluted EPS. Thus a blanket basic-EPS relabel would also be unsupported.

This is not evidence that every future forecast is erroneous. The future denominator is itself forecast. It is evidence that a generic plain-diluted label does not establish an invariant issuer measure here. The report does not explain these historical share adjustments. No correction factor is proposed. The unadjusted broker series can remain available for valuation while issuer scoring and cross-author GAAP pooling stay excluded pending reconciliation.

`asml_issuer_comparability_review.json` supplies exact hashes, model dates, fiscal targets and observation IDs for **25 existing modern plain-EPS observations across five source/model scopes**. It recommends `morningstar_unadjusted_diluted` rather than a universally issuer-compatible `reported_diluted` label. The new January model already uses that narrower basis. Raw source observations are not changed by this research. The adjusted ASML row remains Morningstar-specific; identical plain/adjusted values do not establish issuer equivalence.

## Narrow ASML model-definition bridge

The new April original labels the **29 January 2025** current model explicitly and repeats the legacy [30 January original](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250130_RT.pdf) exactly: FY2025–27 EPS **24.69 / 30.87 / 35.84**, and revenue **34,201 / 38,258 / 42,868 EUR million**. `basis_alias_recommendations.json` recommends a source/model/analyst/fiscal-scoped alias for the three legacy observations to **Morningstar adjusted diluted EPS**. This can extend the existing broker valuation series; it creates no issuer-compatible outcome pair by assumption.

The same source's prior panel is dated **15 November 2024**, whereas the earlier retained model is dated **6 November 2024**. Its equal EPS vector does not repair that date discrepancy. No alias, revision reconstruction or availability claim is made for this prior panel.

## Initial issuer outcomes

| Company/year | Actual fiscal end | Initial release date | Initial GAAP diluted EPS | Original source/locator |
|---|---|---|---:|---|
| ASML FY2021 | 2021-12-31 | 2022-01-19 | EUR14.34 | [US-GAAP statements, p1](https://media.asml.com/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/files/investors/financial-results/q-results/2021/q4/financial-statements-us-gaap-q4-2021-tr45sc.pdf) |
| ASML FY2022 | 2022-12-31 | 2023-01-25 | EUR14.13 | [US-GAAP statements, p1](https://media.asml.com/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/files/investors/financial-results/q-results/2022/q4/financial-statements-us-gaap-q4-2022-fgu23.pdf) |
| ASML FY2023 | 2023-12-31 | 2024-01-24 | EUR19.89 | [US-GAAP statements, p1](https://media.asml.com/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/files/investors/financial-results/q-results/2023/q4/financial-statements-us-gaap-q4-2023-h92dd2.pdf) |
| ASML FY2024 | 2024-12-31 | 2025-01-29 | EUR19.24 | [US-GAAP statements, p1](https://ourbrand.asml.com/m/52891a783efb65cf/original/Financial-statements-US-GAAP-Q4-2024.pdf) |
| ASML FY2025 | 2025-12-31 | 2026-01-28 | EUR24.71 | [US-GAAP statements, physical p3](https://ourbrand.asml.com/m/fded19d66e819e4b/original/Financial-statements-US-GAAP-Q4-2025.pdf) |
| NVIDIA FY2026 | 2026-01-25 | 2026-02-25 | USD4.90 | [Initial release, HTML table 3](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026) |
| Sandisk FY2025 | 2025-06-27 | 2025-08-14 | USD−11.32 | [Initial release, HTML table 8](https://www.sandisk.com/company/newsroom/press-releases/2025/2025-08-14-sandisk-reports-fiscal-fourth-quarter-2025-financial-results) |
| Sandisk FY2026 | 2026-07-03 | 2026-08-05 | USD73.76 | [Initial release, HTML table 9](https://www.sandisk.com/company/newsroom/press-releases/2026/2026-08-05-sandisk-reports-fiscal-fourth-quarter-2026-financial-results) |

The five ASML results pages, initial statement PDFs and companion dated press-release PDFs are retained. ASML's headlines frequently show **basic** EPS; the extracted diluted outcomes come from the financial statements. All annual current-year columns were verified. Sandisk's FY2026 year ends **3 July**, as its release explicitly states; it is not silently mapped to June30. Its FY2025 loss is preserved, and its pre-separation business history does not become a five-year history of the new listed security. NVIDIA uses the January-ending issuer fiscal year. No source value was updated from a later comparative column, and all historical availability timestamps remain blank.

These outcomes let the root-owned evaluator test existing NVIDIA/Sandisk reported forecasts. ASML outcomes should be retained while the incompatible broker-denominator comparisons remain excluded. This collection does not implement a parallel ranking or promise a particular post-integration score count.

## Ensemble discovery and concrete access needs

No new verified compatible second named analyst was recovered in this bounded pass. Two leads were investigated and kept outside observations:

- An [original BMO Nesbitt Burns Alphabet brief](https://nesbittburns.bmo.com/documents/86996/568991/Alphabet%2B%28GOOG-US%29.pdf/f803369b-8caa-436e-b913-b5c17d1be0ab) discusses JPMorgan's valuation and a GAAP multiple, but the one-page PDF prints no report date or individual analyst. Its EPS table is not unambiguously a named JPMorgan model. The retained PDF and `bmo_discovery.json` do not authorize historical or individual-analyst observations.
- Search discovery exposed [purported Bernstein/Mark Li original report text on Scribd](https://www.scribd.com/document/978013624/Bernstein-Global-Memory-AI-HBM-Driving-Another-Record-High-Next-Year), including a separately labeled Micron GAAP statement dated 23 June2025. An intact original PDF from a public authorized source was not recovered. This is an access lead, not validated EPS data or ensemble compatibility. A lawful original Bernstein global-memory model could be valuable because it appears to distinguish GAAP diluted EPS explicitly; its date, authorship, fiscal mapping and definition still need artifact-level verification.

Further useful access would be dated original analyst models with explicit GAAP diluted definitions, or a licensed historical estimates feed containing contributor IDs, accounting definitions, share bases and contemporaneous availability timestamps. Existing Morningstar unadjusted/adjusted distinctions and identical historical rounded EPS cannot substitute for those fields. No paid subscription, scraping credits, access bypass, external messages or provider contact was used. Grok was not needed for the completed work.

## Reproduction and checks

`collect.py` preserves bounded broker attempts; `collect_issuers.py` retains official release artifacts. `issuer_discovery.json` retains ASML's official download links. `finalize.py` reproduces both compatible broker CSVs, issuer outcomes/manifest and `validation.json` offline, asserting hashes, annual table columns, exact forecast vectors, numerical dates, distinct IDs, cutoff and blank availability timestamps. `review_compatibility.py` reproduces the scoped ASML recommendations from `asml_reference_forecasts.csv` and hash-checked originals. Rendered review pages are retained under `review/`. The unproven model-date bridge and rejected BMO/ensemble leads remain documented rather than silently imported.
