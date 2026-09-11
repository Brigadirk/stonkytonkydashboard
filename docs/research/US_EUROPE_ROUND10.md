# US / Europe round10: Guosen NVIDIA continuity and current forecasts

Research date and cutoff: **2026-09-10**. Collection: `data/collection/us_europe_round10/`. This bounded pass followed the related-report dates in the retained Guosen originals. It adds **24 printed annual forecasts: 12 EPS and12 revenue, across four report dates**. No issuer outcomes, historical availability timestamps, or values derived from valuation ratios were added.

## Verified models

Values below are current annual forecasts, as printed on original physical page1. Revenue is USDmillion; EPS is USD per ordinary share, in post-June2024 split units. A missing distinct numerical-model date is left blank. The day printed on each original is a report date, not a verified dissemination timestamp.

| Report date | Licensed research authors | Normalized issuer FY targets | Printed EPS | Printed revenue | Evidence retained |
|---|---|---|---|---|---|
|2024-08-30|Zhang Lunke|FY2025 / FY2026 / FY2027|2.73 /3.64 /4.19|123659 /164228 /184586|Complete original PDF, p1 andp5 visually checked|
|2025-08-29|Zhang Lunke; Liu Zitan|FY2026 / FY2027 / FY2028|4.23 /6.05 /6.93|205569 /271353 /306613|Original cover-page image; full model unavailable|
|2025-11-24|Zhang Lunke; Liu Zitan; Zhang Haochen|FY2026 / FY2027 / FY2028|4.70 /7.72 /9.68|213035 /333499 /427880|Original cover-page image; full model unavailable|
|2026-08-31|Zhang Lunke; Liu Zitan|FY2027 / FY2028 / FY2029|10.66 /16.34 /19.70|408886 /681431 /840944|Original cover-page image; full model unavailable|

Primary originals: [August2024 PDF](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf), [August2025 page1](https://public.fxbaogao.com/report-image/2025/08/29/5027955-1.png), [November2025 page1](https://public.fxbaogao.com/report-image/2025/11/24/5163387-1.png), [August2026 page1](https://public.fxbaogao.com/report-image/2026/08/31/5665920-1.png). These are Guosen-authored original artifacts hosted by third parties; the report-page mirror is not represented as an official broker distributor.

The August2026 source independently supplies a recent consecutive annual pair and explicitly revises February2026 revenue/profit forecasts. Its related-report list moves directly from February2026 to November2025; this source establishes no missing May2026 model. The August2024 PDF moves the first retained appearance of its complete vector earlier than the November2024 reprint. No older model date is manufactured from that matching vector. [August2026 original](https://public.fxbaogao.com/report-image/2026/08/31/5665920-1.png), [August2024 original](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf).

The November22,2024 report is new quarterly commentary carrying the unchanged August30 annual model. Its p1 explicitly says it maintains earnings forecasts and cites the August report. The complete physical-page5 financial-model text is identical between the two originals, in addition to the exact three-year EPS, revenue and parent-profit vectors. Neither prints a distinct newer numerical-model date. `model_age_review.json` recommends August30 as the first evidenced age for that exact November source/hash/author/FY/value scope; it preserves November's actual report date and makes no historical availability claim. `verify_model_age.py` reproduces this comparison without editing frozen observations or central policies. [November2024 p1/p5](https://pdf.dfcfw.com/pdf/H3_AP202411221641021029_1.pdf), [August2024 p1/p5](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf).

## EPS definition and narrowly scoped compatibility

Every new original independently prints the footnote **“摊薄每股收益按最新总股本计算”**: diluted EPS uses latest total share capital. This is not the issuer's weighted-average diluted-share denominator. The originals credit Guosen research for their forecasts and print licensed analyst registrations; the accompanying Wind source credit does not turn the annual models into consensus. Byline changes remain one firm/team forecast contribution, never independent votes. [Originals cited above](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf).

Two levels of evidence are retained in `guosen_definition_review.json`:

1. **Full PDF checked:** August30,2024, hash `c9ec4666215fd6101f89be44958756c78579b3f41f58ca042b8a1d1b47b27962`, report date2024-08-30, author `Zhang Lunke (张伦可)`, targets FY2025–FY2027, EPS2.73/3.64/4.19. Cover parent profit66997/89375/102903USDmillion matches both parent-profit rows on physicalp5 exactly. This exact source/report/FY scope supports adding to `guosen_latest_total_shares_eps`. Liu Zitan is a contact in this source, not a licensed coauthor. [PDF p1 andp5](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf).
2. **Cover only:** the other three sources have attributable original forecasts and independently stated latest-share EPS, but no full income statement available for matching the numerator. They use raw basis `guosen_latest_total_shares_eps_numerator_not_crosschecked`. Their exact scopes, authors, raw labels, EPS and parent-profit vectors are recorded separately under `image_only_scopes`. Do not promote these to full-model-verified or issuer-compatible status by borrowing the definition from an earlier report. The integration owner can retain an explicitly limited firm-specific series after its own review. [August2025](https://public.fxbaogao.com/report-image/2025/08/29/5027955-1.png), [November2025](https://public.fxbaogao.com/report-image/2025/11/24/5163387-1.png), [August2026](https://public.fxbaogao.com/report-image/2026/08/31/5665920-1.png).

The cover-only parent-profit vectors are respectively102706/146897/168317,114121/187596/235224, and256831/393724/474858USDmillion. Within displayed rounding, each cover permits one constant latest-share denominator for its three annual EPS values. The diagnostic intervals are retained; this arithmetic neither creates EPS nor proves a missing full-model numerator match. The prior May2025 conflicting numerator remains quarantined in round9 and is not repaired here. [August2025 original](https://public.fxbaogao.com/report-image/2025/08/29/5027955-1.png), [November2025 original](https://public.fxbaogao.com/report-image/2025/11/24/5163387-1.png), [August2026 original](https://public.fxbaogao.com/report-image/2026/08/31/5665920-1.png), [May2025 conflicting original p1/p5](https://pdf.dfcfw.com/pdf/H3_AP202505301681759010_1.pdf).

There is **no new proof of cross-firm or issuer GAAP/non-GAAP EPS equivalence**, and these additions do not create comparable issuer-outcome pairs by relabeling them.

## Fiscal-label and share-unit evidence

August2025 explicitly labels FY2026E/FY2027E/FY2028E. The other three sources use one-year-lower raw labels; each same-page forecast recommendation explicitly names the issuer fiscal years and a corresponding rounded revenue vector. Historical revenue columns also identify the issuer year:26974/60922 for FY2023/24,60922/130497 for FY2024/25, or130497/215938 for FY2025/26. Both the raw labels and normalized targets are retained. The approximate January26 fiscal illustrations in the image sources are not substituted for the already verified NVIDIA Sunday-near-January31 calendar. [August2024](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf), [August2025](https://public.fxbaogao.com/report-image/2025/08/29/5027955-1.png), [November2025](https://public.fxbaogao.com/report-image/2025/11/24/5163387-1.png), [August2026](https://public.fxbaogao.com/report-image/2026/08/31/5665920-1.png).

All four originals postdate the June2024 split and show post-split EPS units. No new split conversion is applied. The August2024 report title itself says24FYQ2 while its narrative discussesFY25Q2; the annual targets use the proven table/narrative mapping rather than the title typo. [August2024 PDF p1](https://pdf.dfcfw.com/pdf/H3_AP202408311639669704_1.pdf).

## Image provenance and public-access limits

The exact public catalog pages are [5027955](https://www.fxbaogao.com/detail/5027955), [5163387](https://www.fxbaogao.com/detail/5163387), and [5665920](https://www.fxbaogao.com/detail/5665920). Their public preview API explicitly advertises the original page1/page2 image paths: [August2025 preview linkage](https://api.fxbaogao.com/mofoun/report/report/getReportPreviewImages?reportId=5027955), [November2025 linkage](https://api.fxbaogao.com/mofoun/report/report/getReportPreviewImages?reportId=5163387), [August2026 linkage](https://api.fxbaogao.com/mofoun/report/report/getReportPreviewImages?reportId=5665920). Catalog HTML, API responses, capture times, hashes, PNG originals and server-generated JPEG renditions are retained. The PNG transparency can appear dark in a viewer; the JPEG uses the same advertised image URL with the host's `x-oss-process=image/format,jpg` parameter. It is a review aid, not an additional independent source.

No guessed later page paths or paid/download APIs were used. Public FXBaogao unauthenticated search recovered the exact August2025 catalog ID from its report title; its returned metadata and the request payload are retained in staging. A publicly advertised PDF path resolved against the public asset host returned404. The public read-report route returned a parameter error. NXNY's matching August2026 catalog described an encrypted, membership-only PDF. Those routes were stopped without accounts or purchases.

Exact-title web searches and East Money's official public report APIs did not recover full PDFs for the three image-only dates. East Money's ordinary company/org report endpoint returned other Guosen research but not these foreign-stock models. The known February2026 official metadata page verifies company code80000007 and the original NVDA report identity; that code did not make the missing foreign reports discoverable through the ordinary list endpoint. Relevant public responses and client JavaScript are retained under `staging/`. This is a bounded route result, not a claim that no public copy exists anywhere.

The concrete remaining access need is the **complete original Guosen NVIDIA PDFs for2025-08-29,2025-11-24 and2026-08-31**, especially each annual income statement and EPS/share definitions. Public page1 forecasts are already recovered. A subscription would only be useful here if it demonstrably supplies those dated originals; no purchase was made or requested.

## Reproduction and validation

- `python3 data/collection/us_europe_round10/finalize.py` verifies retained artifact hashes, validates the PDF text/table, and reproduces24 observations,4 manifest rows, the manual image transcription ledger and exact definition-review scopes. It performs no network requests.
- `retrieve.py` can re-fetch only the exact successful public URLs into a new nested staging directory. It records new hashes and identifies changed artifacts without replacing frozen originals or fabricating old retrieval times.
- `verified_transcriptions.json` makes the manual extraction explicit: raw annual labels, complete EPS/revenue/parent-profit vectors, physical page, source URL/hash and linked JPEG review provenance.
- `download_log.json` retains actual retrieval timestamps. Both historical availability fields and all unprinted numerical-model dates remain blank.
- No central policy, shared merger, price dataset, app code or prior collection was edited.

Frozen forecast hashes:

| File | SHA256 |
|---|---|
|`observations.csv`|`8799fb702e247efa76bce5b55d9943092885f395f801aad259b5789b66a47611`|
|`manifest.csv`|`d8addb5d0d4d3a0fb984e0b9011fdcd809b76f4d9b335c13ebfe7292444ff674`|
