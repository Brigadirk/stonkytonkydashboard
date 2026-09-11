# US estimator research, round11

Cutoff: 2026-09-10. Files: `data/collection/us_estimators_round11/`. The accepted packet adds one independent Bernstein NVIDIA model, with nine annual observations. Three EPS observations have an explicit GAAP diluted definition; the three non-GAAP EPS observations remain a separate firm-specific stream. Three revenue forecasts accompany them. No five-year Bernstein history or accuracy ranking was created.

## NVIDIA: current second-firm candidate verified

The June17,2026 Bernstein report prints the following forecasts on original physical page32, Exhibit47:

| Issuer fiscal year | GAAP diluted EPS, USD | Separate non-GAAP diluted EPS, USD | Revenue, USDmillion |
|---|---:|---:|---:|
| FY2027 | 9.69 | 9.19 | 398818 |
| FY2028 | 12.48 | 12.52 | 539563 |
| FY2029 | 14.74 | 14.81 | 622987 |

The original separates GAAP income, GAAP diluted shares and non-GAAP measures. Recalculation agrees within displayed rounding; the FY2027/28 annual diluted-share counts equal the averages of the corresponding quarterly forecasts. Page35 independently confirms USDmillion, January fiscal ends and the revenue vector. This supports comparison with verified US-GAAP diluted forecasts. It does not establish equivalence between firms' adjusted EPS. [Original English report, pp32/35](https://www.scribd.com/document/1072698702/Bernstein-Global-Semiconductors-Global-Semis-the-CPU-Renaissance-Beneficiaries-of-a-223bn-TAM-260617).

The joint byline remains one Bernstein contribution. Page1 prints a June17 report date and a June16,20:30UTC publication timestamp. A distinct numerical-model date and independently verified original dissemination time are unavailable. Historical availability is not backfilled. The report is85days old at cutoff; that is not proof that every model input was updated then. [Original p1](https://www.scribd.com/document/1072698702/Bernstein-Global-Semiconductors-Global-Semis-the-CPU-Renaissance-Beneficiaries-of-a-223bn-TAM-260617).

This supplies the annual coverage needed for a one-year-ahead earnings window, subject to the app's compatibility and freshness checks. Historical ensemble membership can only include it from its eligible source date onward. Earlier Bernstein revisions, original publication verification and future outcomes remain missing.

## Public original retrieval

An East Money [machine-translated mirror](https://pdf.dfcfw.com/pdf/H3_AP202606241823792017_1.pdf) exposed a lead, but includes obvious translation corruption. No accepted value comes from it. The ordinary anonymous Scribd viewer displays the original English page32 completely, as documented in `review/bernstein_public_view_p32.png`. Its public HTML explicitly advertises unblurred page32/35 payloads. Those exact URLs returned200 without credentials or token modification. Raw catalog HTML, original payloads, extraction text and browser screenshots are retained. No subscription download endpoint, blur removal or guessed page path was used.

This is a third-party-hosted original; official broker distribution is not claimed. The discovery lesson is specific: public readable report pages may remain available even when PDF downloading requires an account. ScrapingBee was unnecessary for these pages.

## Broadcom: refreshed original recovered, dilution unresolved

The September9 First Shanghai issue was publicly linked by its ordinary [date-filter search](https://www.mystockhk.com/searchInfo.aspx?NodeId=81&StartDate=2026-09-09&EndDate=2026-09-09), although the homepage's individual-report download points to login. The complete original was retrieved from the advertised URL. Physicalp3 names Rita Cao and Peter Han and prints FY2026/27/28 EPS9.8/17.2/28.7USD, revenue105485/175886/287982USDmillion and income46097/81259/135351USDmillion. [Original issue5099, p3](https://www.mystockhk.com/UploadFiles/2026/09/09112431C51C9320.pdf).

The annual EPS row does not say diluted and gives no forecast share denominator. The table also prints an inconsistent December31 fiscal header; its historical revenue anchors51574/63887 and narrative identify Broadcom issuerFY2024/25. These issues are explicit in `firstshanghai_candidate_review.json`. The source is useful evidence of a new independent model, but is not promoted into the US-GAAP diluted ensemble. The table is an embedded image; original-page review, cover cross-check and manual transcription are retained. [Original pp1/3](https://www.mystockhk.com/UploadFiles/2026/09/09112431C51C9320.pdf).

## Other routes and exact next gaps

- DBS's [May25 NVIDIA original](https://www.dbs.com/content/article/pdf/US_clover/Nvdia.pdf) is public but only prints one forecast year and no EPS row. Rounded P/E was not inverted to manufacture earnings. Full original and text retained.
- KGI's original [August11,2025](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/us-daily/nvidia_20250811c.pdf) and [February26,2026](https://www.kgi.com.hk/zh-hk/-/media/files/kgishk/research-reports/us-daily/nvidia_26022026c.pdf) NVIDIA models were recovered. The latter has annual forecasts throughFY2028, but lacks an explicit annual diluted-denominator policy, a fresh current model andFY2029. They remain discovery evidence, not claimed compatible contributors.
- Bernstein's June17 report has no Broadcom income statement; Broadcom appears in Arm supply-chain discussion. A separate [December12,2025 AVGO original](https://www.scribd.com/document/974007743/Bernstein-Broadcom-Inc-AVGO-us-FQ425-Recap-the-Fickle-Heart-s-Desire-251212) is a historical lead. Its EPS definitions have not been reviewed; it is older than180days at cutoff. No rows extracted.
- The precise next NVIDIA requirements are additional dated Bernstein models beforeJune2026, an update afterAugust2026 results, and source release verification for strict historical testing. For Broadcom, obtain First Shanghai's explicit forecast numerator/share denominator and correct fiscal labels, or another fresh complete broker GAAP diluted model. None of this pass proves that a paid plan is necessary or that any particular subscription includes these items.

## Reproduction

`python3 data/collection/us_estimators_round11/finalize.py` validates the source linkage, hashes, original row strings, unit evidence and EPS arithmetic, then reproduces nine rows and one manifest entry. `review_candidates.py` reproduces the separate First Shanghai evidence ledger. `retrieve.py --destination NEW_DIRECTORY` performs fresh exact-URL retrieval without replacing frozen files and stops if public unblurred linkage changes. `browser_review.mjs NEW_DIRECTORY` repeats ordinary anonymous original-page inspection. Python syntax checks and the offline finalizer passed. No central policy, app or refresh script was changed.
