# Korean memory analyst archive collection

Collected on September 10, 2026. Requested publication window: September 10, 2021 through September 10, 2026, with earlier warm-up material retained separately. This is a downloaded research collection, not a complete archive or an analyst ranking.

## Result

**37 public broker PDFs are saved locally**, totaling **979 PDF pages and approximately 92.13 MB**. Every PDF has a SHA-256 hash, page-marked text extracted with pypdf, and a separate Poppler `pdftotext -layout` version. There are **188 numerical observations from 31 reports**: **180 individual analyst estimates** and **eight report-embedded consensus values**. These are revenue/EPS rows across forecast years, not 188 independent outcomes.

Of the saved PDFs, **33 have verified printed dates inside the requested window**, three are warm-up reports, and one has an unresolved publication date. The warm-up reports are Hyundai's Samsung note dated July 31, 2020 and Hynix notes dated January 8 and April 29, 2021.

No ScrapingBee credits, paid credentials, subscriptions or provider contact were used. Direct broker PDF endpoints supplied the collection. Mirae returned service-notice HTML during this batch, so three previously downloaded Mirae PDFs from the same research session were preserved with their original URLs and file timestamps. Four other Mirae PDFs remain unavailable in the collection. Two Hyundai downloads that initially timed out succeeded with one longer transport allowance.

## Files

All collection paths below are relative to [data/collection/korean_memory](../../data/collection/korean_memory/).

| Artifact | Contents |
|---|---|
| [manifest.csv](../../data/collection/korean_memory/manifest.csv) | 41 discovered PDF sources, including 37 saved reports and four unresolved retrievals. Source URL, local paths, company IDs, verified analyst, printed date/reliability, retrieval timestamp, SHA-256, status, page count and notes. |
| [observations.csv](../../data/collection/korean_memory/observations.csv) | 188 annual revenue/EPS observations with source, physical PDF page, accounting caveat, original units/value, normalized KRW value, target period and extraction status. |
| [pdfs/](../../data/collection/korean_memory/pdfs/) | Original retrieved PDFs, named with firm and a stable hash of the discovered URL. |
| [text/](../../data/collection/korean_memory/text/) | pypdf text with explicit physical PDF page markers. These are the text sources used for this extraction. |
| [layout_text/](../../data/collection/korean_memory/layout_text/) | Poppler layout-preserving text for subsequent manual review and extraction. Form-feed characters mark PDF page breaks. |
| [sources.json](../../data/collection/korean_memory/sources.json) | Discovered source URLs and expected identity/date metadata. Expected dates are discovery hints; the manifest controls verification status. |
| [initial_download_attempts.csv](../../data/collection/korean_memory/initial_download_attempts.csv) | Original 34-source batch outcomes before preserving earlier Mirae files and retrying Hyundai transport failures. |
| [timeout_retry_results.json](../../data/collection/korean_memory/timeout_retry_results.json) | Results of the two Hyundai timeout retries. |
| [extraction_gaps.json](../../data/collection/korean_memory/extraction_gaps.json) | Six saved reports without observation rows yet, including sector reports and notes without a first-page model. |
| [discovery_gaps.json](../../data/collection/korean_memory/discovery_gaps.json) | Mirae listing failure and unresolved Hyundai research-channel short links. |
| [validation_summary.json](../../data/collection/korean_memory/validation_summary.json) | Final file counts, hash/provenance checks and transcription checks against independently extracted Poppler text. |
| [responses/mirae_service_notice.html](../../data/collection/korean_memory/responses/mirae_service_notice.html) | Actual archive-listing response, referencing the broker's `return_notice.jpg` image. |

`local_file`, `text_file` and `layout_text_file` in the manifest are relative to the collection directory. An unavailable source may have a planned local path but no corresponding file; check `status` before opening it.

## Coverage obtained

| Firm / verified principal analyst | Saved PDFs | Verified publication years collected | Observation rows |
|---|---:|---|---:|
| Meritz / Sunwoo Kim | 11 | 2021, 2022, 2023, 2024, 2025, 2026; one additional report undated | 54 |
| Hyundai Motor Securities / Roh Geun-chang | 9 | 2020, 2021, 2022, 2023, 2024, 2025 | 66 |
| KB / Jeff Kim | 9 | 2021, 2022, 2023, 2025, 2026 | 30 |
| Hana / Rok-ho Kim | 5 | 2022, 2024, 2025, 2026 | 22 |
| Mirae Asset / Young-gun Kim | 3 | 2021, 2026 | 16 |

Company coverage includes ordinary-share **SK Hynix 000660 KRX** and **Samsung Electronics 005930 KRX**. Some PDFs are combined morning-meeting or sector reports. Their page count includes other companies, while observations are restricted to these two issuers and the identified memory analyst. Coauthors remain in the original report/text; they have not been turned into additional independent forecasts.

Examples demonstrating actual multi-year collection include Meritz's [October 27, 2021 Hynix report](https://home.imeritz.com/include/resource/research/WorkFlow/20211026201826942K_02.pdf), [October 27, 2022 Hynix report](https://home.imeritz.com/include/resource/research/WorkFlow/20221026234503941K_02.pdf), [November 1, 2023 Samsung report](https://home.imeritz.com/include/resource/research/WorkFlow/20231031222356797K_02.pdf), [March 14, 2024 Samsung report](https://home.imeritz.com/include/resource/research/WorkFlow/20240314073613317K_02.pdf), [July 4, 2025 Samsung report](https://home.imeritz.com/include/resource/research/WorkFlow/20250704070204288K_02.pdf), and [April 18, 2026 Hynix report](https://home.imeritz.com/include/resource/research/WorkFlow/20260418170453824K_02.pdf). The manifest provides every collected URL and local counterpart.

Other model examples are [KB's October 21, 2022 Samsung report](https://rdata.kbsec.com/pdf_data/20221020190159790E.pdf), [Hana's January 26, 2024 Hynix report](https://www.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2024/01/25/240126_SKH.pdf), and [Hyundai's March 21, 2025 ESG report](https://www.hmsec.com/documents/research/20250320172859373_ko.pdf), which contains separate Samsung and Hynix annual forecasts.

## Extraction and checks

Revenue is stored in **KRW base units**. The original numeric string and its billion/trillion unit are retained beside it. EPS is stored in **KRW per share**, preserving the broker's description rather than assuming statutory diluted EPS. Annual target dates are December 31 for both issuers. Actual historical columns were excluded; columns explicitly labeled `E` or `F` were retained.

Eight rows concern a fiscal year preceding the report's calendar year and are labeled `past_fiscal_year_estimate`. A broker may still print an `E` or `F` after year-end or around the earnings announcement. These rows must be checked against the actual release timestamp before treating them as predictions.

The eight consensus observations come from clearly separated Hana consensus boxes. They have `source_type=report_embedded_consensus` and no analyst attribution. Their original contributor set and consensus timestamp are unknown. They should never be mixed into the author's forecast history or presented as live consensus.

One source conflict is explicit. Hyundai's March 2025 Samsung summary table gives FY2025/FY2026 EPS of **4,738 / 5,677**, while its same-page revision box gives **4,736 / 5,676**. The annual-summary values were transcribed, and all three Samsung EPS rows from that model carry `source_internal_conflict_review_required`. The original is physical PDF page 35. Hynix's separate table is physical page 39. [Original Hyundai report](https://www.hmsec.com/documents/research/20250320172859373_ko.pdf)

Checks completed: saved-PDF hashes match the manifest; observation keys contain no duplicates; source companies are restricted to the two requested Korean issuers; reported publication dates do not exceed the research cutoff; and straightforward table columns/units were checked against extracted source text. Every original numeric observation also appears on its cited physical page in the independently generated Poppler text. Hyundai observation pages were checked for the relevant report date. No issues remained in these checks. Numeric presence does not establish correct accounting comparability, original historical availability or analyst accuracy.

Every observation has `historical_availability_verified=false`. A printed date on a PDF downloaded today does not prove an unchanged file was disseminated then. Original availability timestamps, replacement history and independently archived snapshots remain to be established before a rigorous historical simulation.

## Remaining gaps

- **Archive completeness:** no firm/year is certified complete. Meritz has the widest publication-year spread here, but only selected reports were discovered and downloaded. This must not be described as five years of all forecasts.
- **Mirae:** current HTML responses prevented collection of four previously identified PDFs and discovery through the live 2022 listing. The listing is indexed with June 7, 2022 Hynix/Samsung reports, but those complete PDFs were not obtained in this batch. The three preserved PDFs cover October 2021 and September 2026 only.
- **Hyundai:** 2026 reports remain a gap. Two short links from its own research channel did not resolve within the transport limit. The collected 2021 Hyundai reports are warm-up material, so Hyundai still lacks an in-window 2021 report here.
- **KB:** 2024 remains missing. Two saved commentary notes contain no first-page annual forecast table and have no observations yet.
- **Hana:** 2021 and 2023 remain missing. Its October 2025 and February 2026 PDFs are saved, but their relevant model sections still need extraction.
- **Meritz sector reports:** the January 2023 report is dated on physical page 2. Its company sections remain unextracted. The September 2025 sector PDF's current recommendation disclosure rows suggest September 12, but its cover publication date was not verified; the manifest leaves the date blank and no observations were admitted from it.
- **Evaluation:** actuals, consensus matching, forecast horizons, share denominators, adjusted/statutory definitions and analyst identity changes must be reconciled before scoring. No “best analyst” conclusion follows from these download counts.

Discovery used known broker links, broker-domain searches and an indexed broker archive listing. Requests used low concurrency, no blind attachment-ID scans, no login/proxy bypass and no paid services. Ordinary public PDF access was sufficient for this batch; proxy credits would not fill the remaining historical or accounting gaps by themselves.
