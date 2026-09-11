# Samsung: KB–Mirae EPS compatibility review

**Decision: no cross-firm compatibility group is supported by the retained reports.** Both brokers identify consolidated parent-attributable profit, but the reports do not define the EPS calculation sufficiently to establish a common numerator policy and share denominator. Matching historical numbers are useful diagnostics, not a definition bridge. This review recommends no basis aliases and enables no additional forecast-to-issuer comparisons.

## Scope and retained evidence

This bounded review covers eight original Samsung reports already retained in the project: seven KB reports dated 2022-10-21, 2024-05-02, 2024-12-26, 2025-09-23, 2026-01-23, 2026-02-23 and 2026-06-10; and Mirae's 2026-09-07 report. The original files were not changed. The full original URLs, paths and SHA256 values are in [source_manifest.json](../../data/discovery/samsung_ensemble_basis/source_manifest.json). Physical PDF pages are used throughout.

The detailed tables and available footnotes were reviewed, including English and Korean terminology for EPS, dilution, weighted shares and parent profit. There is only one retained Mirae Samsung model in this review, so no third cross-firm historical year is claimed. The result is limited to these originals; it does not claim that broker methodology exists nowhere else.

## What the reports define

KB's June 10 report identifies consolidated reporting and parent-attributable net profit. Its separate adjusted-net-profit row equals parent profit for every FY2023–FY2027 column. Its EPS row does not state whether EPS uses that unmodified numerator or an allocation to common shareholders, nor does it define basic/diluted shares or the averaging policy. The cover bylines both Jeff Kim and Changmin Lee; the existing registry keys the model to Jeff Kim, and this review makes no attribution changes. [KB original, pp. 1 and 5](https://rdata.kbsec.com/pdf_data/20260609193955660E.pdf).

Mirae's September 7 cover explicitly identifies consolidated K-IFRS and parent-attributable NP. Its detailed statement distinguishes parent net profit from parent comprehensive income; the latter must not be used as an EPS numerator. Neither that table nor the cover supplies an EPS formula. A label for adjusted operating profit does not establish an adjusted EPS definition. [Mirae original, pp. 1 and 7](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119).

Mirae does explicitly use **6,649 million common plus preferred shares** on p. 2, but that divisor belongs to its sum-of-the-parts fair-value calculation. The table does not identify it as the EPS denominator. The retained [page image](../../data/discovery/samsung_ensemble_basis/mirae_20260907_p2.png) preserves that context. Applying the valuation divisor to the EPS row would be an unsupported inference. [Mirae original, p. 2](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119).

## Historical and forecast diagnostics

The diagnostic below divides printed parent net profit in KRW billions by printed EPS in KRW and multiplies by 1,000. The result has units of million shares, but it is **not a broker-defined denominator**. Any profit allocation or adjustment omitted from the numerator would change its interpretation.

| Report | Fiscal period | Parent NP, KRW bn | EPS, KRW | Diagnostic shares, million |
|---|---|---:|---:|---:|
| KB May 2, 2024 | FY2021 historical | 39,244 | 5,777 | 6,793.145 |
| KB May 2, 2024 | FY2022 historical | 54,730 | 8,057 | 6,792.851 |
| KB June 10, 2026 | FY2023 historical | 14,473 | 2,131 | 6,791.647 |
| KB June 10 / Mirae September 7, 2026 | FY2024 historical, both | 33,621 | 4,950 | 6,792.121 |
| KB June 10 / Mirae September 7, 2026 | FY2025 historical, both | 44,261 | 6,564 | 6,742.992 |
| KB June 10, 2026 | FY2026 forecast | 300,401 | 45,182 | 6,648.688 |
| Mirae September 7, 2026 | FY2026 forecast | 291,087 | 43,637 | 6,670.646 |
| KB June 10, 2026 | FY2027 forecast | 438,614 | 65,970 | 6,648.689 |
| Mirae September 7, 2026 | FY2027 forecast | 424,487 | 63,846 | 6,648.608 |
| Mirae September 7, 2026 | FY2028 forecast | 416,133 | 62,589 | 6,648.660 |

Sources: [KB May 2024, p. 15](https://rdata.kbsec.com/pdf_data/20240430143822903K.pdf), [KB June 2026, p. 5](https://rdata.kbsec.com/pdf_data/20260609193955660E.pdf), [Mirae September 2026, pp. 1 and 7](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119). Full precision and row-specific source hashes are retained in [diagnostics.csv](../../data/discovery/samsung_ensemble_basis/diagnostics.csv).

FY2024 and FY2025 match exactly on both printed inputs. KB additionally supplies FY2021–FY2023 historical checks. These establish numerical continuity and agreement for those printed columns; they do not establish matching future EPS policies.

For FY2026, the inferred counts differ by about **21.96 million shares, or 0.33%**. Assuming illustrative nearest-integer rounding of both printed quantities, KB's interval is 6,648.603–6,648.772 million and Mirae's is 6,670.559–6,670.734 million. These intervals do not overlap. The brokers have different report vintages, so legitimate changes in forecast share counts or timing could explain the difference; it does not prove that their formal accounting definitions differ. Conversely, FY2027's nearly matching ratios and overlapping rounding intervals do not prove the definitions are the same. The rounding assumption is a diagnostic convention, not a documented broker precision policy.

One additional warning against treating any historical vector as a definition: KB's September 23, 2025 report prints FY2024 EPS **4,976** in its historical valuation panel on p. 5, but **4,950** in the detailed financial model on p. 6. This review found no explanation of that within-report difference. Table scope must therefore be preserved. [KB original, pp. 5–6](https://rdata.kbsec.com/pdf_data/20250922152803713E.pdf).

## Exact integration limit

The missing evidence is an explicit broker EPS formula covering the profit numerator and any adjustments, allocation to common/preferred holders, basic versus diluted shares, weighted-average versus period-end counts, and treasury-share treatment. Evidence must apply to both named models and the proposed fiscal/report scopes. Neither a consolidated reporting label nor the SOTP share divisor fills those gaps.

Keep the Samsung KB and Mirae models in separate unresolved-definition groups. The FY2027 numerical agreement does not justify even a one-year compatibility alias. These are unproven definitions, not a finding that the brokers are inherently incompatible.

The strongest reviewed source scopes are:

| Firm / report | Physical pages | SHA256 |
|---|---|---|
| KB / 2026-06-10 | 1, 5 | `ac7f68a4df9216bf8fbf798bcd7d3263d3d23cbd33a18dc9fc662e8447d78fe8` |
| Mirae / 2026-09-07 | 1, 2, 7 | `5adee6606318fd0fd843ef1866e664b2442d1077e8c8fa65fb92cf9c5e9fefe4` |
| KB / 2024-05-02 | 15 | `6210f6fba0ecc06d6ad1d13547149eb3b694804b6939e1eb8b3140567a47ebe8` |
| KB / 2025-09-23 | 5, 6 | `8876412d2b603e2d80c1e0cc54ee9f146153d91bc282cc6d0102f157cdc472dc` |

## Reproduction and artifacts

Run `python3 data/discovery/samsung_ensemble_basis/review_retained.py` from the repository. It validates all eight original hashes and twelve exact page-scoped row vectors, then writes thirteen diagnostic rows. It uses retained text and originals without a network request. The two full-page review images preserve the most relevant visual contexts.

[definition_review.json](../../data/discovery/samsung_ensemble_basis/definition_review.json) contains the scoped decision and missing definitions. [table_evidence.json](../../data/discovery/samsung_ensemble_basis/table_evidence.json) records reviewed vectors. Both [compatibility_recommendations.json](../../data/discovery/samsung_ensemble_basis/compatibility_recommendations.json) and [basis_alias_recommendations.json](../../data/discovery/samsung_ensemble_basis/basis_alias_recommendations.json) are empty by design. No central datasets or application files were edited.
