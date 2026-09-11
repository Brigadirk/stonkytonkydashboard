# Korean forecasts, round 9: missing originals and independently archived bytes

Research completed 10 September 2026. This collection adds **33 annual EPS forecasts and 33 revenues**: 18 EPS for SK hynix and 15 for Samsung, from 12 dated model originals. Nineteen original broker PDFs (289 physical pages) are retained. Seven originals are supporting material, and two additional discovery leads failed or resolved to a non-PDF destination. All source hashes and 66 extracted observations pass the offline checks. No shared dataset, existing collection or application file was edited.

The consequential addition is **11 exact-byte archive captures**. These prove that a particular original PDF was available by its archive capture, while preserving the distinction between that upper bound and its first publication. In particular, the November 2025 models and their capture evidence support opening-January 2026 work without borrowing a later 2026 model. The root application decides eligibility using its normal model-age, fiscal-target and positive-EPS rules; an old archived PDF can remain too stale to use.

## Extracted annual models

Amounts below are original KRW per share, in fiscal-year order. December year ends are retained. Physical PDF pages are counted from the downloaded file, including image covers. Only explicit forecasts are extracted; columns marked actual or provisional (P) are excluded.

| Printed model date | Company / analyst | Fiscal years | EPS vector | Physical page / original |
|---|---|---|---|---|
| 2022-01-28 | samsung_electronics / Sunwoo Kim (meritz) | FY2022–FY2023 | 6,465 / 8,417 | [1](https://home.imeritz.com/include/resource/research/WorkFlow/20220127212517385K_02.pdf) |
| 2022-02-03 | sk_hynix / Sunwoo Kim (meritz) | FY2022–FY2023 | 14,971 / 25,264 | [1](https://home.imeritz.com/include/resource/research/WorkFlow/20220202134110047K_02.pdf) |
| 2022-04-28 | sk_hynix / Sunwoo Kim (meritz) | FY2022–FY2023 | 16,603 / 21,878 | [1](http://home.imeritz.com/include/resource/research/WorkFlow/20220427202048860K_02.pdf) |
| 2022-04-29 | samsung_electronics / Sunwoo Kim (meritz) | FY2022–FY2023 | 7,065 / 8,364 | [1](https://home.imeritz.com/include/resource/research/WorkFlow/20220428211607397K_02.pdf) |
| 2023-01-31 | samsung_electronics / Sunwoo Kim (meritz) | FY2023–FY2024 | 2,097 / 4,861 | [1](http://home.imeritz.com/include/resource/research/WorkFlow/20230131184545227K_02.pdf) |
| 2023-04-27 | samsung_electronics / Sunwoo Kim (meritz) | FY2023–FY2025 | 1,461 / 5,225 / 7,417 | [1](http://home.imeritz.com/include/resource/research/WorkFlow/20230427193945515K_02.pdf) |
| 2023-11-08 | sk_hynix / Sunwoo Kim (meritz) | FY2023–FY2025 | -10,838 / 10,048 / 16,251 | [10](https://home.imeritz.com/include/resource/research/WorkFlow/20231107231237585K_02.pdf) |
| 2024-01-25 | sk_hynix / Sunwoo Kim (meritz) | FY2024–FY2025 | 10,624 / 18,030 | [1](https://home.imeritz.com/include/resource/research/WorkFlow/20240125184528008K_02.pdf) |
| 2024-09-10 | samsung_electronics / Sunwoo Kim (meritz) | FY2024–FY2026 | 5,378 / 7,413 / 7,942 | [11](http://home.imeritz.com/include/resource/research/WorkFlow/20240909210641095K_02.pdf) |
| 2024-09-10 | sk_hynix / Sunwoo Kim (meritz) | FY2024–FY2026 | 24,291.0 / 39,680.7 / 44,195.8 | [7](http://home.imeritz.com/include/resource/research/WorkFlow/20240909210641095K_02.pdf) |
| 2025-11-11 | sk_hynix / Sunwoo Kim (meritz) | FY2025–FY2027 | 53,084 / 78,132 / 88,662 | [6](http://home.imeritz.com/include/resource/research/WorkFlow/20251111001937695K_02.pdf) |
| 2025-11-14 | samsung_electronics / Sunwoo Kim (meritz) | FY2025–FY2027 | 5,043 / 7,613 / 8,041 | [11](http://home.imeritz.com/include/resource/research/WorkFlow/20251114010257413K_02.pdf) |
| 2026-06-09 | sk_hynix / Young-gun Kim (mirae) | FY2026–FY2028 | 329,362 / 466,282 / 497,630 | [1](https://securities.miraeasset.com/bbs/download/2145136.pdf?attachmentId=2145136) |

Model dates follow the printed current report date except that repeated models are excluded. The file key `meritz_hynix_20240126` follows its discovery lead; the **printed original is January 25, 2024**, and the CSV correctly uses January 25. Report and share-basis dates preserve original model units; neither company has been given an inferred statutory EPS normalization.

## Reprints and conflicting panels

- The [November 14, 2025 sector original](http://home.imeritz.com/include/resource/research/WorkFlow/20251114010257413K_02.pdf), physical p6, repeats Hynix's November 11 EPS 53,084 / 78,132 / 88,662. Only the distinct Samsung model on p11 is emitted.
- The [November 8, 2023 sector original](https://home.imeritz.com/include/resource/research/WorkFlow/20231107231237585K_02.pdf), p6, repeats the Samsung November 1 EPS 1,781 / 4,552 / 5,514 and revenues 265.6 / 312.1 / 342.4 trillion. Its Hynix p10 vector is distinct and is emitted. Compare the [November 1 company original](https://home.imeritz.com/include/resource/research/WorkFlow/20231031222356797K_02.pdf), p1.
- The new [April 28, 2022 Hynix original](http://home.imeritz.com/include/resource/research/WorkFlow/20220427202048860K_02.pdf), p1, has the same FY22/23 EPS 16,603 / 21,878 as the already-retained [May 31 sector original](https://home.imeritz.com/include/resource/research/WorkFlow/20220530190742393K_02.pdf), p70. `repeat_model_evidence.json` records both hashes and narrowly scoped evidence. This establishes an earlier identical model; it does not establish when that model was first created. A later report date alone should not rejuvenate that unchanged EPS vector.
- In the [November 11, 2025 Hynix original](http://home.imeritz.com/include/resource/research/WorkFlow/20251111001937695K_02.pdf), p4's valuation/peer panel shows FY2026 EPS **78,176**, while the detailed model on p6 explicitly labels parent-attributable EPS **78,132**. The collection uses the explicit detailed model and retains this discrepancy; no averaging or substitution is performed.
- The [June 9, 2026 Mirae original](https://securities.miraeasset.com/bbs/download/2145136.pdf?attachmentId=2145136), p1, explicitly revises earnings forecasts. Its model is extracted. The [July 29 Mirae original](https://securities.miraeasset.com/bbs/download/2146182.pdf?attachmentId=2146182), p1, states earnings estimates are unchanged, despite a different EPS vector (295,026 / 415,482 / 442,513). It is retained as supporting material only. Its p6 target-price history lists June 25; a target-price revision does **not** prove the date of the earnings model. A possible July 14 original is a concrete follow-up locator, unverified in this collection.

## Historical availability: what is and is not proved

Public Telegram posts successfully supplied original broker URLs, including the November 2023 sector report and early 2022 company models. Today’s retained HTML, SHA256 and displayed timestamp are reproducible discovery evidence. They do not prove the same text or link appeared on that historical date. Telegram's primary [message constructor documentation](https://core.telegram.org/constructor/message) separately defines `date`, `edit_date` and `edit_hide`; the latter can suppress the edited indicator. Its [channel-message update documentation](https://core.telegram.org/constructor/updateEditChannelMessage) explicitly supports edited channel posts. Those primary HTML documents are retained under `discovery/`. No original-date promotion is made from Telegram metadata, the absence of an edited label, a broker filename, or today's download time.

For archive verification, the retained CDX timestamp and SHA1 digest must match a downloaded replay; the replay's **SHA256 must equal the retained original's SHA256**. All eleven recommendations satisfy that test. `availability_evidence_recommendations.json` supplies exact source/replay/CDX paths, hashes, capture timestamp, replay URL and original URL. The next UTC calendar day is the conservative daily availability date. The original publication instant remains unknown. Source CSV rows therefore retain `historical_availability_verified=false`; the separate root integration applies the verified archive upper bound while preserving labelled report-date reconstruction.

| Printed report date | Source hash prefix | Archive capture (UTC) | Conservative available date |
|---|---|---|---|
| 2021-10-27 | `688f08cf2a1d` | [2022-04-26T07:02:39Z](https://web.archive.org/web/20220426070239id_/http://home.imeritz.com/include/resource/research/WorkFlow/20211026201826942K_02.pdf) | 2022-04-27 |
| 2023-01-10 | `cefa1dcce558` | [2023-01-16T08:26:12Z](https://web.archive.org/web/20230116082612id_/https://home.imeritz.com/include/resource/research/WorkFlow/20230109194247370K_02.pdf) | 2023-01-17 |
| 2023-01-31 | `fc73cb2a6ceb` | [2023-03-13T18:14:58Z](https://web.archive.org/web/20230313181458id_/http://home.imeritz.com/include/resource/research/WorkFlow/20230131184545227K_02.pdf) | 2023-03-14 |
| 2023-04-27 | `061da175ab0a` | [2023-05-10T03:15:42Z](https://web.archive.org/web/20230510031542id_/http://home.imeritz.com/include/resource/research/WorkFlow/20230427193945515K_02.pdf) | 2023-05-11 |
| 2023-05-30 | `412a8cd05542` | [2023-05-31T10:56:29Z](https://web.archive.org/web/20230531105629id_/http://home.imeritz.com/include/resource/research/WorkFlow/20230529224232774K_02.pdf) | 2023-06-01 |
| 2023-11-01 | `a1ebe900882a` | [2024-01-01T08:49:45Z](https://web.archive.org/web/20240101084945id_/https://home.imeritz.com/include/resource/research/WorkFlow/20231031222356797K_02.pdf) | 2024-01-02 |
| 2024-01-02 | `3813607384f2` | [2024-01-02T08:46:11Z](https://web.archive.org/web/20240102084611id_/https://home.imeritz.com/include/resource/research/WorkFlow/20240102061827993K_02.pdf) | 2024-01-03 |
| 2024-03-14 | `49eb3364ddf8` | [2024-05-09T06:31:23Z](https://web.archive.org/web/20240509063123id_/https://home.imeritz.com/include/resource/research/WorkFlow/20240314073613317K_02.pdf) | 2024-05-10 |
| 2024-09-10 | `07abc04b70f9` | [2024-11-12T14:25:29Z](https://web.archive.org/web/20241112142529id_/https://home.imeritz.com/include/resource/research/WorkFlow/20240909210641095K_02.pdf) | 2024-11-13 |
| 2025-10-29 | `443d9998601a` | [2025-11-02T17:59:15Z](https://web.archive.org/web/20251102175915id_/http://home.imeritz.com/include/resource/research/WorkFlow/20251029174936346K_02.pdf) | 2025-11-03 |
| 2025-11-14 | `4a2425b2a035` | [2025-11-28T12:08:17Z](https://web.archive.org/web/20251128120817id_/http://home.imeritz.com/include/resource/research/WorkFlow/20251114010257413K_02.pdf) | 2025-11-29 |

The bounded archive pass checked 32 source candidates: 16 public_archive_retrieval_failed, 11 exact_archived_bytes_verified, 5 no_matching_archived_digest. A CDX digest without a successfully downloaded equal-byte replay is insufficient and is not recommended. Failures are retrieval failures or absence of matching archive evidence, not evidence of a subscription requirement.

## Accounting definition and evaluation limits

Meritz's extracted EPS explicitly refers to parent-attributable earnings, but the reviewed footnotes do not establish basic versus diluted shares, treatment of treasury shares, or allocation to preferred shares. Mirae's June 9 p1 footnote establishes consolidated K-IFRS and parent-attributable net profit, not its EPS denominator. Neither generic consolidated wording nor dividing net profit by EPS proves an accounting policy. Existing firm-specific unresolved basis labels are preserved, and `basis_alias_recommendations.json` is empty.

The round8 cross-broker incompatibility evidence remains material: later Meritz Samsung tables restate a historical EPS figure without the same change in printed parent profit, and implied Hynix share denominators differ across models. This pass does not resolve those differences. No new Korean issuer-outcome match, analyst accuracy score, or cross-broker ensemble compatibility group is asserted. See [KOREA_ROUND8.md](KOREA_ROUND8.md) and its retained original page evidence.

## Remaining routes and rejected material

The February 1, 2021 Hynix issue comment, April 28 Hynix earnings Q&A and April 29 Samsung comment were retrieved but lack annual EPS models. November 17 and December 5, 2025 issue comments also contain no annual EPS model. The March 5, 2025 sector excerpt lacks annual Hynix/Samsung models. These are concrete source limitations, not missing parsers or paid-access barriers; their manifest entries identify them as supporting material.

The July 27, 2023 Samsung short link `https://zrr.kr/76qk` failed initial retrieval and returned HTTP 404 on a bounded HTTP/1.1 retry. Its broker-channel post remains discovery evidence only. The December 10, 2025 `vo.la` link resolved to a YouTube page; the HTML is retained as `discovery/dec10_youtube_response.html`, not counted as a PDF. No EPS is inferred from post summaries or target prices. Mirae July 14, 2026 is a useful next original-PDF locator because it may identify the intervening model repeated July 29; this collection does not claim to have verified that model.

## Files and reproduction

`manifest.csv` and `observations.csv` use the existing Korean collection schema, adding explicit `model_date` and `share_basis_date`. Source hashes, physical pages, printed model/publication dates, native units, bylines and exact table rows are retained. `source_recipe.json` has the 19 original download URLs and required hashes. `restore_sources.py` restores missing originals, refusing changed public bytes. `extract_reviewed.py` regenerates the CSVs offline and checks the manually reviewed vectors. `discover_pages.py`, `collect_company_leads.py` and `collect_archive_evidence.py` retain the bounded public discovery and archive workflow. Re-running discovery would be a new collection observation; it does not rewrite historical availability.

Run from the repository root:

```sh
python3 data/collection/korea_round9/restore_sources.py
python3 data/collection/korea_round9/extract_reviewed.py
python3 data/collection/korea_round9/validate_evidence.py
```

The final checks verified 19 originals, 66 observations and 11 archive captures. `validation.json` records exact EPS vectors; `evidence_validation.json` records the archive checks. All owned files are frozen for root integration after this validation. Further source work belongs in a new collection folder.
