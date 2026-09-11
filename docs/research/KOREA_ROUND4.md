# Korean EPS collection, round 4

Date: 2026-09-10. This pass adds 12 broker-authored original PDFs (210 physical pages) and 39 annual EPS observations: 26 SK hynix and 13 Samsung Electronics. Eleven reports are Meritz/Sunwoo Kim and one is a jointly signed Hana report. All 12 contents are new relative to earlier collection manifests. The 37 individually attributed Meritz rows remain unscored; the two Hana rows retain joint-team attribution and are quarantined from individual rankings. The [manifest](../../data/collection/korea_round4/manifest.csv) and [observations](../../data/collection/korea_round4/observations.csv) preserve URLs, hashes, printed dates, physical pages, values and original EPS labels.

## New vintages

| Company | Printed date | Analyst | EPS fiscal years | Original source / physical pages |
|---|---|---|---|---|
| Samsung and SK hynix | 2022-05-31 | Sunwoo Kim, Meritz | 2022–2023 | [Sector report](https://home.imeritz.com/include/resource/research/WorkFlow/20220530190742393K_02.pdf), date p3, Samsung p66, SK hynix p70 |
| Samsung | 2022-07-29 | Sunwoo Kim, Meritz | 2022–2024 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20220728192634069K_02.pdf), p1 |
| Samsung and SK hynix | 2023-05-30 | Sunwoo Kim, Meritz | 2023–2025 | [Sector excerpt](https://home.imeritz.com/include/resource/research/WorkFlow/20230529224232774K_02.pdf), date p2, Samsung p6, SK hynix p10 |
| SK hynix | 2023-07-27 | Sunwoo Kim, Meritz | 2023–2025 | [Broker-authored PDF distributed by Naver](https://ssl.pstatic.net/imgstock/upload/research/company/1690498890846.pdf), p1 |
| SK hynix | 2023-10-26 | Sunwoo Kim, Meritz | 2023–2025 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20231026165054435K_02.pdf), p1 |
| Samsung | 2024-01-02 | Sunwoo Kim, Meritz | 2023–2025 | [Broker-authored PDF distributed by Paxnet](https://www.paxnet.co.kr/WWW/data/researchCenter/attach/20240102104338102.pdf), p1 |
| SK hynix | 2024-01-02 | Sunwoo Kim, Meritz | 2023–2025 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20240102061827993K_02.pdf), p1 |
| Samsung | 2024-05-02 | Rok-ho Kim and Hyun-soo Kim, Hana | 2024–2025 | [Jointly signed report](https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2024/05/01/240502_SEC.pdf), p1 |
| SK hynix | 2024-06-10 | Sunwoo Kim, Meritz | 2024–2026 | [Computex excerpt](https://home.imeritz.com/include/resource/research/WorkFlow/20240609204233312K_02.pdf), date from own latest disclosure entry p11, EPS physical p6 (printed p64) |
| SK hynix | 2024-07-26 | Sunwoo Kim, Meritz | 2024–2026 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20240725210909855K_02.pdf), p1 |
| SK hynix | 2024-10-24 | Sunwoo Kim, Meritz | 2024–2026 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20241024185749922K_02.pdf), p1 |
| SK hynix | 2025-04-25 | Sunwoo Kim, Meritz | 2025–2027 | [Company report](https://home.imeritz.com/include/resource/research/WorkFlow/20250425063811209K_02.pdf), p1 |

Only explicit annual E/F forecast columns were extracted. Early-January previous-year estimates remain marked as estimates preceding final annual earnings, rather than current-year forecasts. The Hana report has both an embedded consensus table and its own model; only its own 4,680/6,428 won EPS forecasts were extracted. The document has two analyst bylines and a separate RA, so neither forecast is assigned exclusively to Rok-ho Kim. This distinction was visually checked on physical page 1 of the original.

Ordinary `curl` succeeded on Meritz after Python requests connections were closed by the server. No ScrapingBee, paid service or provider contact was used. Meritz's June excerpt emits PDF stream/font warnings but its selected company table renders correctly; that physical page was visually checked. The printed-date provenance is retained without claiming the retrieved copy was available at an exact historical timestamp.

## Evidence for consolidating duplicate basis descriptions

The [machine-readable recommendations](../../data/collection/korea_round4/basis_alias_recommendations.json) contain original labels and source hashes. These are aliases for the collector's different English descriptions of the same broker model. They must be scoped to the same company, firm and forecaster; original accounting-basis fields should remain intact. They do not reconcile statutory diluted EPS or justify merging different brokers.

### Meritz / Sunwoo Kim

The existing descriptions `EPS labelled parent-attributable; basic/diluted and share denominator not established` and `Meritz consolidated company model; EPS explicitly parent-attributable; detailed financial table uses KRW billion` can share one broker-model identity.

In the [2023-01-10 original](https://home.imeritz.com/include/resource/research/WorkFlow/20230109194247370K_02.pdf), Samsung's summary p7 shows FY2022/23/24 EPS 5,117 / 2,531 / 5,454, exactly matching detailed p11. SK hynix's summary p12 shows 8,866 / -7,165 / 7,685, exactly matching detailed p15. Both layouts explicitly label EPS as parent-attributable (지배주주). The detailed tables' KRW-billion label belongs to company financial totals; EPS remains won per share.

The [2024-03-14 Samsung report](https://home.imeritz.com/include/resource/research/WorkFlow/20240314073613317K_02.pdf): physical p1 and p8 match FY2024/25/26 EPS 4,270 / 5,756 / 6,597. Do not infer that historical actual columns and future EPS use identical share denominators merely because both are labelled parent-attributable.

### Hyundai / Roh Geun-chang

The existing descriptions `Consolidated K-IFRS EPS as printed; basic/diluted/share denominator unresolved` and `Consolidated K-IFRS annual summary as printed; EPS denominator unresolved` describe the same parent-income EPS rows in the examined originals.

The [2021-11-16 original](https://www.hmsec.com/documents/research/20211115181205523_ko.pdf) has Samsung summary EPS 6,475 / 7,084 / 7,339 on physical p43, exactly matching detailed p47's `EPS(지배순이익 기준)`. SK hynix p49 has 13,102 / 12,787 / 16,437, exactly matching p52's parent-EPS row. In the [2024-04-25 original](https://www.hmsec.com/documents/research/20240424174227063_ko.pdf), Samsung p39's 5,517 / 6,839 / 7,071 matches p42; SK hynix p43's 8,736 / 11,259 / 9,227 matches p46.

The detailed Hyundai tables separately print total-net-income EPS, with different numbers. That row must not be substituted for the parent-income EPS used in the summaries. The same-vintage numerical matches provide stronger evidence than the broad K-IFRS label alone.

### KB / Jeff Kim

The existing descriptions `Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS` and `KB consolidated forecast table; EPS appears beneath parent-attributable net income, denominator unresolved` can be aliased within Jeff Kim's KB model.

In Samsung's [English 2022-10-21 original](https://rdata.kbsec.com/pdf_data/20221020190159790E.pdf), physical p1 places EPS below net income attributable to controlling interests; FY2022/23 EPS 5,307 / 3,728 exactly matches detailed p7. The [Korean 2024-05-02 original](https://rdata.kbsec.com/pdf_data/20240430143822903K.pdf) p1 places EPS below 지배주주순이익 (parent-attributable income); FY2024/25 EPS 5,042 / 7,185 matches detailed p15. In SK hynix's [English 2023-02-01 original](https://rdata.kbsec.com/pdf_data/20230201163453690E.pdf), -8,307 / 2,511 matches p1 and p6; the [Korean 2024-06-13 original](https://rdata.kbsec.com/pdf_data/20240612150416600K.pdf)'s 20,648 / 30,803 matches p1 and p7. Exact source URLs, hashes and physical pages are in the alias JSON. The bilingual description does not establish the share denominator or statutory diluted definition.

## Verification and remaining gaps

`extract_reviewed.py` checks each PDF hash, printed-date text, company byline and every EPS token against its physical-page extraction. It keeps Hana's consensus numbers out of the individual model. All 39 report-company-period keys are new relative to earlier observations. No analyst ranking is created.

This pass improves one continuous forecaster's historical coverage rather than adding isolated new analysts. Gaps remain between collected vintages, and 2025 Hynix coverage remains especially thin. Exact historical availability and forecast-to-actual EPS accounting reconciliation remain unproven. An annual EPS curve built from these reports is an explicitly labelled report-date reconstruction, not a licensed daily point-in-time estimates history.
