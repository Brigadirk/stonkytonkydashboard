# Korean memory analyst archive: round two

Research cutoff and collection date: **10 September 2026**. Requested history: 10 September 2021–10 September 2026. This batch fills missing broker-years and extracts previously retained company models. It does not establish an analyst accuracy ranking.

## Result

Saved **9 new PDF originals**, retained **3 originals already collected in round one** for new extraction, and recorded **2 unsuccessful Mirae PDF responses**. The 12 retained PDFs contain **238 physical pages** and occupy **22,213,848 bytes**. The manifest therefore has 14 records, not 14 downloaded reports. Newly downloaded documents range from 16 November 2021 to 13 May 2026.

Extracted **104 new annual EPS/revenue observations**: **64 individual-analyst forecasts**, **10 joint-team forecasts requiring attribution review**, and **30 report-embedded consensus observations**. None duplicates an observation in `korean_memory/observations.csv`; reused PDFs add new company-table extraction, not new source documents. Counts and checks are recorded in [validation_summary.json](../../data/collection/korean_round2/validation_summary.json).

Files: [manifest.csv](../../data/collection/korean_round2/manifest.csv), [observations.csv](../../data/collection/korean_round2/observations.csv), [sources.json](../../data/collection/korean_round2/sources.json), [failed extraction/source notes](../../data/collection/korean_round2/extraction_gaps.json). Every saved original has SHA-256, retrieval time, page-marked text and independent Poppler layout text. Company IDs are `sk_hynix` and `samsung_electronics`.

## Newly downloaded originals

Each page number below is the **physical PDF page**, beginning at 1; some sector reports print different page numbers.

| Broker and attributed author | Printed report date | Company | Model pages | Primary authored original / local copy | New observations |
|---|---|---|---|---|---:|
| KB — Jeff Kim | 2024-05-02 | Samsung | 1 | [Broker-hosted original](https://rdata.kbsec.com/pdf_data/20240430143822903K.pdf) · [PDF](../../data/collection/korean_round2/pdfs/kb_23a228dfd35f.pdf) | 4 |
| KB — Jeff Kim | 2024-06-13 | SK hynix | 1 | [Broker-hosted original](https://rdata.kbsec.com/pdf_data/20240612150416600K.pdf) · [PDF](../../data/collection/korean_round2/pdfs/kb_1629498bdcd5.pdf) | 4 |
| KB — Jeff Kim | 2024-09-13 | SK hynix | 1 | [Broker-hosted original](https://rdata.kbsec.com/pdf_data/20240912141419303K.pdf) · [PDF](../../data/collection/korean_round2/pdfs/kb_4e02e7ab2cc3.pdf) | 4 |
| KB — Jeff Kim | 2024-12-26 | Samsung | 1 | [Broker-hosted original](https://rdata.kbsec.com/pdf_data/20241226141409780K.pdf) · [PDF](../../data/collection/korean_round2/pdfs/kb_60cf6fbdbdd5.pdf) | 4 |
| Hana — Rok-ho Kim | 2023-01-13 | SK hynix | 1 | [Broker-hosted original](https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2023/01/12/SKHynix_0113.pdf) · [PDF](../../data/collection/korean_round2/pdfs/hana_b522033f41d4.pdf) | 10 |
| Hana — Rok-ho Kim; 변운지 | 2023-07-27 | SK hynix | 1 | [Broker-hosted original](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2224&bbsId=&bbsSeq=1275503&dbType=) · [PDF](../../data/collection/korean_round2/pdfs/hana_ab82a6bd0339.pdf) | 8 |
| Hana — Kim Kyung-min; Rok-ho Kim; Hyun-soo Kim | 2021-12-08 | Samsung | 6 | [Broker-hosted original](https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2021/12/07/Daily_211208_.pdf) · [PDF](../../data/collection/korean_round2/pdfs/hana_5168582676aa.pdf) | 10 |
| Hyundai — Roh Geun-chang | 2021-11-16 | SK hynix; Samsung | 43, 49 | [Broker-hosted original](https://www.hmsec.com/documents/research/20211115181205523_ko.pdf) · [PDF](../../data/collection/korean_round2/pdfs/hyundai_6967efeebf6d.pdf) | 16 |
| Hyundai — Roh Geun-chang | 2026-05-13 | SK hynix | 1 | [MK-hosted original](https://stock.mk.co.kr/uploads/20260527/1779859669_e42736598c32d9eff905.pdf) · [PDF](../../data/collection/korean_round2/pdfs/hyundai_dc1cc7c3f73c.pdf) | 8 |

All eight broker-hosted new originals were retrieved from the broker’s own domain. The Hyundai 13 May 2026 document is an original Hyundai Company Note, with Roh’s byline and broker email, publicly hosted by MK. **Its host is a third party**; the URL’s `20260527` upload segment was not used as the report date. The printed report date is on PDF page 1. This source is kept distinguishable in its manifest notes, and a broker-hosted duplicate remains desirable. [Hyundai original, PDF p. 1](https://stock.mk.co.kr/uploads/20260527/1779859669_e42736598c32d9eff905.pdf).

## Previously retained models now extracted

| Original | Publication-date evidence | Company model pages | Newly extracted observations |
|---|---|---|---:|
| [Meritz original](https://home.imeritz.com/include/resource/research/WorkFlow/20230109194247370K_02.pdf) · [PDF](../../data/collection/korean_round2/pdfs/meritz_9c6076c1bc15.pdf) | 2023-01-10, printed on physical p. 2 | Samsung p. 11; SK hynix p. 15 | 12 |
| [Hana original](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2206&bbsId=&bbsSeq=1284695&dbType=) · [PDF](../../data/collection/korean_round2/pdfs/hana_43c8d0a3cb24.pdf) | 2025-10-30, daily cover and model p. 6 | SK hynix p. 6 | 8 |
| [Hana original](https://www.hanaw.com/download/research/FileServer/WEB/industry/industry/2026/02/23/Semi_260224.pdf) · [PDF](../../data/collection/korean_round2/pdfs/hana_682666e476f1.pdf) | 2026-02-24, dated company sections | Samsung p. 31; SK hynix p. 39 | 16 |

The Meritz source is a selected sector-report extract whose printed page numbers run into the 80s/90s. Samsung’s company section identifies Sunwoo Kim on physical page 7, and SK hynix’s identifies him on page 12. Their detailed financial models on physical pages 11 and 15 use **KRW billion** and label EPS as parent-attributable. These more precise tables were used instead of also collecting rounded KRW-trillion company summaries. [Meritz original, PDF pp. 2, 7, 11, 12, 15](https://home.imeritz.com/include/resource/research/WorkFlow/20230109194247370K_02.pdf).

## Gap closures and attribution

- **KB 2024 is now represented for both companies**, with two report vintages each. The Korean byline 김동원 is linked to Jeff Kim by the same `jeff.kim@kbfg.com` email on the originals. This is an identity cross-reference, not a claim that he was the best forecaster. [Samsung, May 2024](https://rdata.kbsec.com/pdf_data/20240430143822903K.pdf), [SK hynix, June 2024](https://rdata.kbsec.com/pdf_data/20240612150416600K.pdf).
- **Hana 2023 has an individual Hynix model from 13 January**, signed by Rok-ho Kim, with 변운지 labelled researcher. The July report instead labels both people Analyst, so its four author-forecast observations are stored as `joint_team_forecast`. [January original, p. 1](https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2023/01/12/SKHynix_0113.pdf), [July original, p. 1](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2224&bbsId=&bbsSeq=1275503&dbType=).
- **Hana 2021 now has a Samsung model, with unresolved individual attribution.** The daily contents page credits Kim Kyung-min; the company model on physical page 6 carries three analyst signatures: Kim Kyung-min, Rok-ho Kim and Hyun-soo Kim. Its six author-forecast observations are therefore a joint team, not six observations credited exclusively to Rok-ho. All 10 joint-team observations in this batch use `extraction_status=attribution_review_joint_model_unscored`. [Hana December 2021 daily, pp. 1 and 6](https://www.hanaw.com/download/research/FileServer/WEB/info/daily/2021/12/07/Daily_211208_.pdf).
- The July 2023 Hynix disclosure records an **analyst change on 6 May 2022**. An old target or estimate shown in a current analyst’s recommendation-history table is not enough to assign that historical forecast to the current analyst. [Hana July 2023 disclosure](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2224&bbsId=&bbsSeq=1275503&dbType=).
- **Hyundai now has both company models within late 2021** and a Hynix model in 2026. Both 2021 company sections print 16 November 2021; the filename’s 15 November timestamp is not substituted for publication. The 2026 gap closure relies on the clearly identified MK-hosted original described above. [Hyundai 2021, pp. 43 and 49](https://www.hmsec.com/documents/research/20211115181205523_ko.pdf), [Hyundai 2026, p. 1](https://stock.mk.co.kr/uploads/20260527/1779859669_e42736598c32d9eff905.pdf).

## Sample extracted forecasts

Revenue values below retain the source unit **KRW billion**; EPS is **KRW per share**. These are forecasts printed at the stated date, not current forecasts or actual results.

| Author/source | Report date | Company / target year | Revenue | EPS | PDF page |
|---|---|---|---:|---:|---:|
| Jeff Kim / KB | 2024-05-02 | Samsung FY2025E | 354,271 | 7,185 | 1 |
| Jeff Kim / KB | 2024-12-26 | Samsung FY2025E | 307,471 | 5,095 | 1 |
| Rok-ho Kim / Hana | 2023-01-13 | SK hynix FY2023F | 23,672.8 | -7,360 | 1 |
| Sunwoo Kim / Meritz | 2023-01-10 | SK hynix FY2023E | 30,023.2 | -7,165 | 15 |
| Roh Geun-chang / Hyundai | 2021-11-16 | Samsung FY2022F | 316,423 | 7,084 | 43 |
| Roh Geun-chang / Hyundai | 2021-11-16 | SK hynix FY2022F | 51,829 | 12,787 | 49 |

The first two rows provide a preserved 2024 revision history for the same company and target fiscal year. The January 2023 Hynix rows provide nearby, separately attributable forecasts. These examples can support later comparisons only after aligning the forecast horizon and accounting definitions. Sources: [KB May](https://rdata.kbsec.com/pdf_data/20240430143822903K.pdf), [KB December](https://rdata.kbsec.com/pdf_data/20241226141409780K.pdf), [Hana January](https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2023/01/12/SKHynix_0113.pdf), [Meritz January](https://home.imeritz.com/include/resource/research/WorkFlow/20230109194247370K_02.pdf), [Hyundai November](https://www.hmsec.com/documents/research/20211115181205523_ko.pdf).

## Discovery and remaining gaps

The successful KB route was **KB Think’s own company pages → explicit document ID → KB research PDF endpoint**. The four first-party discovery pages are recorded in `sources.json`: [Samsung, May](https://kbthink.com/securities-view.html?docId=20240430143822903K), [Hynix, June](https://kbthink.com/securities-view.html?docId=20240612150416600K), [Hynix, September](https://kbthink.com/collect-view/securities-view.html?docId=20240912141419303K), [Samsung, December](https://kbthink.com/securities-view.html?docId=20241226141409780K). Requests used identifiers actually disclosed by those pages; no blind identifier scanning was used.

Hana discovery used broker-domain searches combining the company, missing year and byline; the 2021 Samsung daily was found through its company-note title. Hyundai 2021 was discovered using the exact sector title `친환경 저전력 반도체에 집중하자`. The Hyundai 2026 first-party searches included `site.hmsec.com/documents/research/ "2026" "추론을 위한"` and `site.hmsec.com/documents/research/ "2026" "SK하이닉스" "05.13"`; the usable original was the MK-hosted result. Original download URLs and the source-discovery route remain in the manifest.

Two Mirae attachment URLs were tried once again in this batch: [Samsung, expected 1 November 2023](https://securities.miraeasset.com/bbs/download/2116359.pdf?attachmentId=2116359) and [Samsung, expected 1 February 2024](https://securities.miraeasset.com/bbs/download/2121600.pdf?attachmentId=2121600). Both returned HTML containing a `return_notice.jpg` image rather than a PDF. The HTML bodies are retained in `responses/`. Their manifest publication-date fields remain blank: a discovery lead is not a successfully inspected original. No estimate was transcribed from a search snippet. This response does not by itself establish a paywall or a particular access restriction.

Mirae’s missing **2022–2025 downloaded archive coverage remains unresolved**. Coverage also remains uneven by company: a report-year represented for Hynix does not imply Samsung coverage in that year. Hana’s 2021 addition is a joint Samsung model, not a sole-author Rok-ho Hynix forecast. This batch supplies selected missing-year evidence, not a complete quarterly publication archive or an unbiased analyst sample.

No ScrapingBee credits, scraping-service key, account, login or payment was used. Downloads used ordinary public requests, with at most two concurrent requests in the initial batch. Failed sources were recorded without bypass attempts.

## Verification and comparison limits

All 12 saved PDFs passed SHA-256 verification; all dated documents fall within the requested window. Every one of the 104 extracted numbers was found independently on its cited physical page in Poppler’s layout extraction. Annual headers and row positions were inspected before extraction; column-count assertions passed. Revenue is normalized to base KRW in `value` while `original_value` and `original_unit` retain the printed quantity. Parentheses denoting negative EPS become a negative normalized value. The old observation file was read only for a canonicalized duplicate check; it was not edited.

Only explicit E/F forecast columns were imported as author estimates. Historical actual columns, target prices and the Before revision values were omitted. Eight observations relate to a just-ended fiscal year still labelled an estimate in a January report; they are explicitly marked `past_fiscal_year_estimate`. Report-embedded consensus remains a separate source type, with no analyst credited and no claim about its contributor set or original timestamp.

Every row retains `historical_availability_verified=false`. A printed date and a currently downloadable original do not prove an immutable publication timestamp. EPS has not been reconciled across parent-attributable earnings, basic versus diluted shares, Samsung preferred/common share treatment, or broker-specific denominators. The batch is suitable for source review and carefully qualified comparisons, not for an asserted five-year best-analyst ranking.
