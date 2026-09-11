# Korea round11: independent NH estimates and a fresh Hana Hynix model

Completed 10 September 2026. Two public broker reports supply **three company models, eight annual EPS estimates and eight annual revenues**. NH is a newly collected research firm. These observations improve independent comparisons, but **no cross-firm EPS definition bridge was established**. Both recommendation files remain empty; central policies and application files were not edited.

## Usable forecasts

| Company / analyst | Printed report date | Age at September10 | FY2026 EPS | FY2027 EPS | FY2028 EPS |
|---|---|---:|---:|---:|---:|
| SK hynix / Hana, Rok-ho Kim | 2026-07-30 | 42 days | 376,719 | 463,912 | Missing |
| SK hynix / NH, Young-ho Ryu | 2026-05-26 | 107 days | 293,767 | 452,340 | 505,785 |
| Samsung / NH, Young-ho Ryu | 2026-05-26 | 107 days | 46,772 | 49,897 | 53,087 |

All EPS values are native KRW per share as printed; denominator methodology remains unresolved. NH's Korean byline is 류영호, transliterated here. Hana's own Financial Data and detailed statement agree on both forecast years; its nearby consensus panel was excluded. The report describes an active revision. [Hana original, physical pp1 and5](https://file.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2026/07/29/SKH_260729.pdf).

NH's annual forecasts cover FY2027 andFY2028, the fiscal years needed for the September2027–September2028 earnings underlying the app's one-year target. The report labels EPS as parent-attributable and consolidated IFRS. [NH broker report, physical pp10–11, public viewer](https://feat.page/nhsec/semiconductor-2026-h2).

Hana lacks FY2028, so its new model cannot independently supply the full future target interval. No extrapolation fills that gap. NH's printed May26 date is retained as the report-date proxy for its current model. May22 appears in price-target history and does not establish an earlier EPS-model date. [Hana, pp1–6](https://file.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2026/07/29/SKH_260729.pdf), [NH, pp12–13](https://feat.page/nhsec/semiconductor-2026-h2).

## Definition decision

The exact missing evidence is each broker's EPS numerator policy and any adjustments, basic versus diluted shares, weighted-average versus period-end counts, treasury-share treatment and, for Samsung, allocation between ordinary and preferred holders. The complete Hana and NH reports do not establish a shared denominator policy. Parent-profit labels alone are insufficient. No profit/EPS division was used as proof.

NH prints FY2025 Samsung EPS7,241, while retained Mirae prints6,564. This is another reason to preserve separate definitions; the difference is not a conversion factor. [NH p11](https://feat.page/nhsec/semiconductor-2026-h2), [Mirae September7 p1](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119). See the earlier [Samsung definition review](SAMSUNG_ENSEMBLE_BASIS.md) and the [ensemble contract](../ENSEMBLE_BUILD.md).

[compatibility_review.json](../../data/collection/korea_round11/compatibility_review.json) records exact source hashes, authors, report/model dates, fiscal scopes and exclusions. There are zero approved cross-firm scopes. Neither report proves an original public-availability instant, so strict historical availability stays unverified and no accuracy scores are added.

## Retrieval and reproducibility

Hana's [public research-channel post](https://t.me/HanaResearch/20053) supplied a short link to its broker-hosted PDF. The channel was discovery evidence only. NH's public viewer exposed the complete report; its raw S3 URL returned403, but clicking its ordinary **Download** button delivered the PDF without a login, form submission or payment. This was a retrieval issue that needed no ScrapingBee. The delivered file contains14 broker pages and a blank final page; provider-added PDF modification metadata is not a historic publication timestamp.

Retained SHA256 values:

| Report | SHA256 |
|---|---|
| Hana July30 | `ef11c3359b1dd9b8467f21529cb5f2a1ccbdd9b3fc6eb5d6d0b1322c96afde98` |
| NH May26 delivery | `ef01e796875c7d1cf9e52446b9c7a7f925bc532231811cb9e8500383f1350340` |

All artifacts are in `data/collection/korea_round11/`: source recipes, downloads and retrieval failures, originals, regenerated full text, page renders, exact reviewed row vectors, manifests and observations. [Search routes](../../data/collection/korea_round11/discovery/search_routes.json) also record methodology searches and excluded discoveries. September7 Mirae Hynix was already retained and was not counted again. Old DBS/Daiwa results and unverified third-party Bernstein excerpts supplied no observations.

```sh
node data/collection/korea_round11/collect_public.mjs
python3 data/collection/korea_round11/extract_reviewed.py
```

Both scripts passed against retained sources. The extractor verifies hashes and page counts, regenerates text from the PDFs, and checks exact page-scoped rows before writing16 observations. The collector preserves existing sources; a newly generated PDF with changed bytes becomes a review candidate rather than silently replacing evidence. No central refresh was run.

The remaining useful acquisition is an explicit method document applicable to named broker models, plus Hana FY2028 and further dated NH revisions. This pass demonstrated no paid product or ScrapingBee purchase that supplies those missing definitions. It therefore recommends no purchase.
