# Four Korean daily price gaps

Checked 10 September 2026. All four requested closes are available in original public Naver daily-history tables, independently cross-checked against Naver's dated chart response. These are source-native **종가 (daily close)** observations, not undated `regularMarketPrice` values. No central price file was changed.

| Korean common-share ticker | Session date | Close, KRW | Original daily-history page |
|---|---|---:|---|
| 000660.KS, SK hynix | 2025-09-19 | 353,000 | [Naver, page 24](https://finance.naver.com/item/sise_day.naver?code=000660&page=24) |
| 005930.KS, Samsung Electronics | 2025-09-19 | 79,700 | [Naver, page 24](https://finance.naver.com/item/sise_day.naver?code=005930&page=24) |
| 000660.KS, SK hynix | 2026-09-10 | 1,853,000 | [Naver, page 1](https://finance.naver.com/item/sise_day.naver?code=000660&page=1) |
| 005930.KS, Samsung Electronics | 2026-09-10 | 269,000 | [Naver, page 1](https://finance.naver.com/item/sise_day.naver?code=005930&page=1) |

Page numbers can move as new sessions are added; retained HTML, exact rows and SHA256s preserve what was checked. `verified_dated_closes.csv` and `.json` record each exact source and its independently retained `api.finance.naver.com/siseJson.naver` response, requested with the identical start/end date. Both source presentations explicitly label the closing-price column **종가**, and all four match exactly.

## Completed session and market label

Naver's current [Hynix](https://finance.naver.com/item/main.naver?code=000660) and [Samsung](https://finance.naver.com/item/main.naver?code=005930) stock pages label the daily price section **KRX 제공**, meaning supplied by KRX. The retained daily-history rows carry explicit dates, OHLC values and positive volume. KRX's primary [KOSPI trading procedures](https://global.krx.co.kr/contents/GLB/06/0602/0602010201/GLB0602010201T1.jsp) specify the regular session as 09:00–15:30 Korea time. Retrieval timestamps are after 15:30 KST on September10, and the older session is in historical daily records. This establishes completed dated-close evidence for these four rows, without claiming an independent full-calendar audit.

The attempted read-only KRX daily-data endpoint (`MDCSTAT01501`) returned HTTP400 for both requested dates. Those failed requests are recorded in `krx_retrieval_log.json`; no direct KRX price response was obtained. Naver remains the original publicly retrieved price source, with KRX attribution shown by its own interface.

## Split convention and the narrow corporate-action check

Neither retained Naver response explicitly documents its split/dividend-adjustment policy. The data are therefore labelled source-native closes with **no conversion applied**. At the September10 cutoff, that day's native common-share close has no later normalization interval. The September2025 rows require more care if a pipeline demands independently verified adjustment conventions.

A bounded issuer/broker check supports continuity of the common-share units and identifies buybacks/cancellations, but does not establish a complete corporate-action history through September10:

- Samsung's [September2025 consolidated statements](https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_con_quarter03_all.pdf), physical p45 / printed p43, report 5,919,637,922 issued ordinary shares and KRW100 par value. The [March31, 2026 cancellation notice](https://www.samsung.com/global/ir/reports-disclosures/public-disclosure-view.84615/) identifies cancellation of 73,359,314 common shares, again with KRW100 par value. Subtraction gives **5,846,278,608** shares. The [August21 issuer disclosure](https://www.samsung.com/global/ir/reports-disclosures/public-disclosure-view.84756/) reports the same cancellation in its 2026 treasury-share roll-forward and a 1%-of-issued-shares figure of 58,462,786 (rounded). The retained September7 Mirae original reports 5,846m common shares on p1. The identified reduction is a cancellation, not a split. This supports no split through the checked records; it is not an exhaustive event audit through September10.
- Hynix's [January28 results release](https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/) announces cancellation of 15.3m treasury shares. Its [March31 ownership record](https://www.skhynix.com/ir/UI-FR-IR04/) states **712,702,365** listed common shares. The [August19 repurchase notice](https://news.skhynix.com/en/share-buyback-and-retirement/) states **730,492,365** issued shares and describes the new buyback/cancellation program. The increase is 17,790,000 shares, consistent with the July ADR capital issuance identified during original-report research. A separately attempted issuer-press-release mirror for the exact ADS issuance returned HTTP403, so that issuance's detailed original was not independently recovered in this bounded check. The retained July14 Mirae model reports 730m common shares. These records show ordinary capital-management changes; they do not independently rule out every split event over the entire requested interval.

The Hynix ADS/common-share ratio must not be applied as a Korean stock split. These four rows are for the local common shares, 000660 and 005930. No statement here establishes an accounting EPS denominator or a cross-broker EPS match.

## Retained evidence and outcome

Sources and logs are under `data/discovery/korean_price_gap_check/`. `verified_dated_closes.csv` contains exactly four rows with native-close and split-policy fields. `corporate_action_sources.json` identifies the retrieved issuer originals and hashes; the Samsung PDF's extracted text preserves its physical page mapping. `verify_closes.py` reproduces the HTML/chart comparison, validates all price-source hashes and checks that retrieval followed the regular-session close.

```sh
python3 data/discovery/korean_price_gap_check/verify_closes.py
```

All four dated-close checks passed. The precise remaining limit is the absence of an explicit Naver adjustment policy or a complete independently verified no-split history for September19, 2025 through September10, 2026. No price normalization or central price mutation was performed. Files are frozen for the root agent's integration decision.
