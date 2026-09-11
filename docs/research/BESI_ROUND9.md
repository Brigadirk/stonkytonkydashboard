# BESI round 9: verified February IEX annual model

Retrieved 10 September 2026. The exact PDF lead supplied after the access handoff is valid. It adds four clean observations: Hildo Laman's FY2026/27 EUR EPS and revenue forecasts, retained in `data/collection/besi_round9/`. Previous collections remain unchanged.

The [original IEX Expert issue 04/2026 PDF](https://s202.q4cdn.com/886546970/files/doc_news/2026/IEX04_2026_compressed.pdf) has 52 pages and a printed cover date of 27 February 2026. Physical and printed page 15 contains the BESI article *Nieuwe fase*, by Hildo Laman. Its annual table explicitly labels EUR and attributes the estimates to IEX.

| Metric | FY2026* | FY2027* |
|---|---:|---:|
| EPS, EUR/share | 4.16 | 5.78 |
| Revenue, EUR million | 860 | 1153 |

The preceding FY2025 column is still starred, but contains already released annual actuals, EPS €1.66 and revenue €591m. Those cells are excluded. The article's stock-quote card is dated 20 February; that is not a verified model-revision date. Observation `report_date` is the magazine cover date, 27 February, with unknown model and historical dissemination timestamps left blank. No numerical availability is backdated to the separately identified, subscription-only February 19 web article.

EPS adjustments and basic versus diluted denominator remain unspecified. These rows use the existing `iex_eps_adjustment_and_dilution_unspecified` basis because both the author and own-model attribution are explicit. No equivalence to issuer actuals, Morningstar or another forecaster is established, and no accuracy-scoring alias is proposed.

The PDF resides on the CDN account used by [KPN's official investor-relations website](https://ir.kpn.com/). The retained homepage loads scripts from the same `s202.q4cdn.com/886546970` account. The issue includes a cover interview with KPN's CFO. This establishes the distribution context; the original date KPN uploaded it remains unknown. The PDF metadata records creation on February 23 and modification on February 26, consistent with its later printed cover date, without proving historical public availability.

Retained PDF SHA-256: `be953fdcb9ca93a842f0d28f190d6b3e896feea85871be03c949be5ecba4e927`. Physical page 15 was rendered and visually checked, including the author, euro heading, period labels and IEX attribution. The cover render, extracted evidence and hosting provenance are retained with the original.

Run `python3 data/collection/besi_round9/collect.py` to reproduce the two-source manifest and four observations. The offline collector verifies both source hashes, the table's exact values, attribution, currency and cover date. It writes only this collection.

This source supersedes the access note's earlier outcome for Grok's unverified February PDF lead. The earlier exact-filename searches had produced no identifiable file; the subsequent full URL did. The June and July subscription-article contents remain unverified. This discovery improves February history and does not make a stale model newly revised.
