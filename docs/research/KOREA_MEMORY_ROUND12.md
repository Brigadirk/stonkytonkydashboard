# Korean memory coverage, round 12

Collected original Meritz/Sunwoo Kim reports to fill intervening revisions in the existing parent-attributable EPS series. No estimator, definition or denominator was changed. The packet adds 30 eligible annual EPS cells and 30 matching revenue cells across 11 company tables in nine model-bearing PDFs. Ten tables establish previously missing model vintages; the remaining table moves a known Samsung model's earliest proven date from November 11 to October 29, 2021. Nineteen original PDFs were retained, including ten documents without a usable memory-company annual EPS table.

The default SK hynix series gains four vintages: June 1, 2021; February 1 and April 27, 2023; January 15, 2024. Samsung gains six distinct vintages: June 1 and July 29, 2021; October 28, 2022; January 15, May 2 and November 1, 2024. Its already-retained November 11, 2021 vector was present on October 29. The June/July 2021 reports also improve the reference-window warm-up before the five-year chart starts.

| Original report | Company | Eligible fiscal years | Exact native KRW EPS |
|---|---|---|---|
| [June 1, 2021, physical p7](https://home.imeritz.com/include/resource/research/WorkFlow/20210601064826437K_02.pdf) | Samsung | FY2021–23 | 5,490 / 6,624 / 8,094 |
| [June 1, 2021, physical p11](https://home.imeritz.com/include/resource/research/WorkFlow/20210601064826437K_02.pdf) | SK hynix | FY2021–23 | 15,312 / 24,156 / 27,996 |
| [July 29, 2021, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20210729194438147K_02.pdf) | Samsung | FY2021–23 | 5,759 / 6,837 / 7,684 |
| [October 29, 2021, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20211029000610157K_02.pdf) | Samsung | FY2021–23 | 5,828 / 5,814 / 7,535 |
| [October 28, 2022, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20221027190836834K_02.pdf) | Samsung | FY2022–24 | 5,644 / 4,273 / 5,260 |
| [February 1, 2023, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20230201183425074K_02.pdf) | SK hynix | FY2023–24 | −7,788 / 9,198 |
| [April 27, 2023, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20230426220436550K_02.pdf) | SK hynix | FY2023–25 | −12,701 / 2,613 / 11,270 |
| [January 15, 2024, physical p7](https://home.imeritz.com/include/resource/research/WorkFlow/20240114211203981K_02.pdf) | SK hynix | FY2024–25 | 9,885 / 18,607 |
| [January 15, 2024, physical p11](https://home.imeritz.com/include/resource/research/WorkFlow/20240114211203981K_02.pdf) | Samsung | FY2024–25 | 4,288 / 5,361 |
| [May 2, 2024, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20240502070521257K_02.pdf) | Samsung | FY2024–26 | 4,398 / 5,716 / 5,817 |
| [November 1, 2024, p1](https://home.imeritz.com/include/resource/research/WorkFlow/20241101073743282K_02.pdf) | Samsung | FY2024–26 | 4,604 / 6,326 / 6,682 |

The October 29 Samsung table exactly matches the full FY2021–23 EPS and revenue vectors in the previously retained November 11 sector report. `model_date_evidence_recommendations.json` contains two source-hash-scoped rules, one for EPS and one for revenue. These establish the earlier date without creating a new analyst vote or refreshing age on November 11. `repeat_check.json` records this as the only complete same-author EPS-vector match against the pre-refresh served dataset.

The January 15 SK hynix table also prints FY2023E EPS −10,653 and revenue KRW32,561.7 billion. FY2023 ended before the January 15 report. Both cells remain in the raw extraction packet with `quarantined_completed_fiscal_period`, and must not enter the forecast model or scoring. A general report-date/period-end guard enforces this. Samsung's FY2023P provisional result is omitted from forecast extraction. These exclusions do not reduce January 2024 forward earnings coverage, which needs FY2024 and FY2025.

## Why the recent jumps remain

The recent Meritz revisions are often large actual changes to the broker's annual model. A public-channel review recovered many intervening comments but no eligible annual memory EPS table between the retained January and April 2026 models. That is a result of the reviewed routes, not proof that no such report exists.

The January 12 [CES excerpt](https://home.imeritz.com/include/resource/research/WorkFlow/20260112080308638K_02.pdf) has Hyundai/Gaon earnings models; the April 1 [SEMICON excerpt](https://home.imeritz.com/include/resource/research/WorkFlow/20260401075745052K_02.pdf) has equipment-company models. Neither supplies Samsung/SK hynix annual EPS. Samsung's April 7 and July 7 preliminary earnings comments and the August 18 industry supply note similarly contain no annual EPS model. Exact URLs, downloaded originals and reasons are retained in the packet manifest.

Earlier collection packets were checked before reusing leads. The May 26, 2025 Computex excerpt repeats SK hynix's April 25 vector. March 25, May 6 and August 19, 2026 capital-return notes have no annual EPS model. November 17 and December 5, 2025 industry comments also lack one. None was turned into a fresh forecast observation.

No interpolation was applied. The 2023 loss cycle can produce large changes or gaps in positive forward P/E even after additional forecasts are collected. Additional actual models improve what was known when; they cannot make each genuine earnings revision small.

## Retrieval and remaining routes

Public broker-channel search pages and ordinary historical channel pages were used as locators. Their HTML, message text, links and hashes are retained. Current channel dates do not prove the original publication instant: posts can be edited. Model dates come from printed PDFs (June 2021 date on physical p2; January 2024 date visually verified on the cover). No new strict historical-availability evidence was established.

The old Samsung July 27, 2023 company-report link `https://zrr.kr/76qk` still fails. Exact-title and date searches located public report references but not its original PDF. The former Naver research URL now redirects to the new stock research app and discarded the old date query. This remains a public retrieval problem, not a demonstrated subscription gate. Samsung's January 8, 2026 short link `https://buly.kr/HSYel4n` also failed; channel contents indicate a preliminary-quarter comment, but without the original no numerical cells were extracted.

The most useful unresolved Korean fields are same-author, explicitly defined annual EPS for FY2026/27 (and FY2028 when published) at any genuine revisions in November 2025–January 2026, February–April 2026 and May–July 2026. The reviewed public channel did not supply additional eligible models for those spans. Original publication timestamps and the broker's full EPS denominator policy remain unverified. No paid product or ScrapingBee purchase has been demonstrated to unlock these specific missing reports; neither is recommended on this evidence alone.

## Reproduction and validation

Packet: `data/collection/korea_memory_round12/`.

- `discover.py` and `discover_unfiltered.py` retain public locator pages. Channel results are discovery only.
- `collect_public.py` resolves selected links and retains exact original bytes. `source_recipe.json` pins the resolved broker URLs, hashes and paths.
- `retrieve_originals.py` re-downloads those pinned URLs into a separate verification folder and checks their reviewed hashes, preserving the working packet.
- `extract_reviewed.py` reproduces 62 raw observations: 60 eligible and two quarantined. It verifies original hashes, printed dates, named analyst, parent-attributable EPS labels, exact reviewed annual vectors and review-image presence.
- `review/` retains the visually checked date/table pages. `validation.json` gives the exact vectors and physical pages. `model_date_evidence_recommendations.json` was checked against both earlier and later source hashes and complete EPS/revenue vectors.

No central dataset, market policy or app files were changed by this collection task. Central integration should apply the two model-date recommendations, run the normal refresh and compare the default-series coverage before and after.
