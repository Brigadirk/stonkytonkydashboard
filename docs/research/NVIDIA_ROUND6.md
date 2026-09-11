# NVIDIA historical forecast collection, round 6

Reviewed 10 September 2026. This pass retains five additional original Morningstar PDFs, with 30 observations: 15 annual EPS and 15 annual revenue values. Two numerical model dates are new: **16 February 2022** and **18 March 2024**. Three reports reprint models already collected. No new accounting-basis alias is justified, and this pass does not expand comparable EPS accuracy scores.

## Retained numerical tables

Values below are USD per share **after the July 2021 four-for-one split and before the June 2024 ten-for-one split**. They remain unadjusted in the source observations; an explicit `share_basis_date` supports later normalization. All five EPS rows say diluted EPS but leave the adjustment definition unresolved.

| Printed report date | Numerical model date | Physical page | Fiscal years | EPS vector as printed | Contribution |
| --- | --- | --- | --- | --- | --- |
| [8 Feb 2022, 20:57 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003RE_20220208_RT.pdf) | 8 Feb 2022 | 15 | FY2023–FY2025 | 5.04 / 6.00 / 7.23 | Earlier publication of existing model; prior retained report was 17 February. |
| [15 May 2022, 23:41 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003RE_20220515_RT.pdf) | 16 Feb 2022 | 15 | FY2023–FY2025 | 5.12 / 6.10 / 7.30 | New model vintage. Its revenue estimates are 33 / 38 / 45 billion, rounded as printed. |
| [12 Jan 2024, 19:58 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240112_RT.pdf) | 21 Nov 2023 | 17 | FY2024–FY2026 | 12.24 / 18.27 / 20.60 | Reprint; corrected fiscal headers corroborate the prior original's mapping. |
| [19 Mar 2024, 03:04 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240318_RT.pdf) | 18 Mar 2024 | 17 | FY2025–FY2027 | 26.11 / 34.44 / 40.43 | New model vintage. Revenue: 116,338 / 152,084 / 178,435 million. Filename date is not report date. |
| [10 Jun 2024, 14:54 UTC](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240610_RT.pdf) | 22 May 2024 | 15 | FY2025–FY2027 | 28.04 / 39.33 / 45.56 | Exact reprint of the pre-split May model inside a partly updated report. |

The 2022 reports name Abhinav Davuluri; the 2024 reports name Brian Colello. Report dates are retained separately from model dates. Printed timestamps are not independently verified dissemination timestamps, and reprints do not refresh model age.

## Fiscal and split reconciliation

The 8 February 2022 model prints forecast headers FY2022–FY2024, one year below their reconciled fiscal identity. On the same page, historical revenue of 16.68 billion is FY2021; the model rounds that amount to 17 billion under FY2020. The EPS and revenue forecast vectors exactly match the previously retained 17 February report and its already reviewed +1 fiscal mapping. `source_period_label` preserves the erroneous printed headers. This is a model-specific reconciliation, not a general rule for Morningstar reports. [8 February original, p15](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003RE_20220208_RT.pdf), [17 February reprint, p15](https://invest.firstrade.com/ms/equity_reports/sr/2022/0P000003RE_20220216_RT.pdf).

The January 2024 reprint prints FY2024–FY2026 against the same November model's EPS vector and revenue vector of 59,126 / 85,940 / 96,894 million. The original November report printed FY2023–FY2025. This independently corroborates the existing fiscal mapping without assigning a new January model date. `fiscal_reconciliation.json` records exact values, source hashes, source pages and matched observation IDs. [January original, p17](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240112_RT.pdf), [November original, p17](https://invest.firstrade.com/ms/equity_reports/sr/2023/0P000003RE_20231121_RT.pdf).

The June report mixes share bases. Its historical EPS/shares and fair-value estimate reflect the ten-for-one split, while its last closing price remains the pre-split June 7 close. The forecast table retains 2,489 million diluted shares and the exact May EPS and revenue vectors. Thus its forecast `share_basis_date` is **2024-05-22**, not its report date. The forecast values require division by ten when compared with post-split stock quotes. `share_basis_reconciliation.json` scopes this finding to the exact matching rows. A rendered physical page is retained in `evidence/`. [June original, p15](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240610_RT.pdf), [May original, p16](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20240522_RT.pdf).

## Definition and accuracy limits

`basis_alias_recommendations.json` deliberately contains no new recommendation. The old tables' diluted EPS label does not state the adjustment definition. Matching historical values to issuer non-GAAP earnings is suggestive but does not establish the treatment of future forecasts. Approximate valuation multiples are not a substitute for EPS observations or exact definition evidence.

The public [March 19 Morningstar article](https://www.morningstar.ca/ca/news/247410/morningstar-raises-nvidia-stock-fair-value-to-us%24910.aspx) calls its annual assumptions adjusted EPS but does not directly label the numerical vector. A [May publisher discussion](https://www.morningstar.com/markets/5-stocks-buy-while-theyre-trading-big-discounts) repeats 26.11 and 34.44 without resolving the numerical row's definition. A [February 23 publisher article](https://www.morningstar.com/stocks/markets-brief-5-ways-nvidia-is-living-up-ai-hype) gives only roughly 26.50 for the next year in accessible text, with an inconsistent historical fiscal-year reference. These leads were reviewed, not promoted into exact basis bridges or newly extracted EPS rows. Direct page downloads returned HTTP 403; search-index text supplied discovery evidence only.

The previously proven November 20, 2024 Morningstar adjustment bridge remains in `us_evaluation_round5`; it is not duplicated here. Neither that bridge nor these new originals proves equivalence between Morningstar adjusted EPS and NVIDIA's issuer non-GAAP measure. NVIDIA's FY2027 stock-compensation definition change remains a separate comparability issue.

The new models can extend the series explicitly labelled **diluted EPS, adjustment basis unresolved**. They do not automatically extend today's differently defined adjusted series. Revenue values may be useful for separate forecast evaluation once issuer outcomes and period identities are matched; EPS scoring remains excluded pending a comparable outcome definition.

## Search routes and remaining gaps

- **Firstrade original distribution:** 24 date candidates were requested using verified NVIDIA identifier `0P000003RE`, focusing on independently known analyst-note/report dates and adjacent US/UTC dates. Five originals were recovered; 19 returned 404. Exact requests, status codes, retrieval dates and hashes are in `discovery_round1.json` through `discovery_round4.json`. Previously tested earnings-date failures from round 4 were largely avoided. No new 2021 original was recovered.
- **Public Morningstar analysis:** searched the publisher's dated discussions for exact EPS/definition links. The accessible evidence above did not support a new accounting alias. No EPS was calculated from a price/earnings multiple.
- **Phillip original archive:** the publisher's public [search page](https://www.stocksbnb.com/?s=nvidia) exposed eight relevant 2023–2024 articles, including [May 2023](https://www.stocksbnb.com/reports/nvidia-corporation-ai-turbocharged-guidance/), [November 2023](https://www.stocksbnb.com/reports/nvidia-corporation-uncertainty-over-china-but-demand-still-robust/) and [February 2024](https://www.stocksbnb.com/reports/nvidia-corp-more-upside-from-ai-demand/). Original HTML and publicly displayed image previews were retained. Seven known-date PDF requests returned 403/access denied and one returned 404. The pages require login for the full reports. Public previews mainly show quarterly results or historical charts and did not supply a reviewed annual EPS pair, so no Phillip observations enter the CSV.
- **BOCOM and DBS discovery:** older sector reports surfaced contextual NVIDIA discussion but not an original attributed annual EPS pair suitable for the requested historical comparison. No rows were reconstructed from their valuation multiples.

No paid access, proxy credits or external messages were used. The outstanding 2021–2024 gaps require further genuine dated originals or a licensed historical estimates source; the absence of a successful archive URL is not evidence that a model never existed.

## Files and validation

All work is confined to `data/collection/nvidia_round6/` and this note. `manifest.csv` and `observations.csv` follow the existing collection schema. The manifest covers the five numerical PDF originals; discovery previews and failed requests are recorded separately. The offline `finalize.py` reproduces both CSVs and `validation.json`, verifies SHA-256 hashes, physical page locations, model dates, fiscal labels, and exact EPS/revenue vectors, and checks unique observation IDs. It produces 30 observations with no asserted accounting reclassification.
