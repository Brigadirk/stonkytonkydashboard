# Mirae Hynix July 14, 2026: original model underlying July 29 reprint

Completed 10 September 2026. This bounded follow-up recovered **one original, nine-page Mirae report**, adding three annual EPS forecasts and three revenues. It resolves the model-date ambiguity recorded in round9. No new accounting equivalence or forecast/actual score is asserted.

## Original and discovery

Mirae's official SmartMoney channel published a [July 17 report-summary video](https://www.youtube.com/watch?v=qoonkDY0s6U). Its description directly links the [July 14 Korean Hynix original](https://securities.miraeasset.com/bbs/download/2145830.pdf?attachmentId=2145830), titled “시선을 약간만 아래로.” The exact attachment link was taken from the retained YouTube HTML's `shortDescription`; it was not guessed from neighbouring attachment IDs. A secondary article supplied a title/date search locator only. All numerical evidence comes from the original broker PDF.

The PDF is largely image-based. Its first-page printed date **2026.7.14**, **김영건 / Young-gun Kim** byline, December fiscal-year columns, KRW units and footnote were visually inspected. The detailed financial tables on physical p7 confirm the annual values. `pdftotext` alone misses those tables; the collection retains both its sparse output and full nine-page Korean/English OCR, along with page renders. OCR supplied search/check assistance; visual inspection establishes the selected labels and column placement.

Original SHA256: `418e9cff7d4cd9632ebfb74e818922c575d76fa975ac0fa39108635136e46926`.

## Exact current model

The first-page discussion explicitly lowers earnings estimates by about 11% and lowers the second-quarter operating-profit estimate. It therefore identifies an active earnings revision, rather than merely a target-price update. Its current model is dated July 14. [Original, physical pp1 and 7](https://securities.miraeasset.com/bbs/download/2145830.pdf?attachmentId=2145830).

| Metric | FY2026 | FY2027 | FY2028 |
|---|---:|---:|---:|
| EPS, KRW/share | 295,026 | 415,482 | 442,513 |
| Revenue, KRW billion | 347,518 | 507,945 | 544,121 |
| Parent-attributable net profit, KRW billion | 210,755 | 296,115 | 315,380 |

EPS and revenue are emitted; the net-profit vector is retained as supporting repeat evidence. Actual FY2024 and FY2025 columns are excluded from the forecast observations. Native model units and a July14 share-basis date are retained without a split conversion.

The [July 29 English original](https://securities.miraeasset.com/bbs/download/2146182.pdf?attachmentId=2146182), retained in round9, prints exactly the same three annual vectors on physical p1 and explicitly leaves earnings unchanged while lowering its target multiple. `repeat_model_evidence.json` records both source hashes, pages, fiscal targets and exact matching values. July29 remains supporting-only; if those rows are extracted later, the July14 model date must be retained for freshness. The June25 target-price date is no longer needed to guess this intervening model.

## Definition and availability limits

The first-page footnote identifies consolidated K-IFRS and parent-attributable net profit. Neither that footnote nor the reviewed detailed EPS table defines basic versus diluted shares, weighted-average shares, or treasury-share policy. The p1 headline issued-share figure is not an explicit EPS denominator. The existing Mirae unresolved basis is therefore preserved. No cross-broker grouping or issuer-outcome match follows from this evidence. [Original, physical pp1 and 7](https://securities.miraeasset.com/bbs/download/2145830.pdf?attachmentId=2145830).

The report's printed date, PDF creation metadata and today's retrieved YouTube description do not prove its first public availability instant. YouTube descriptions are editable; the displayed historical video date is discovery metadata, not independent proof that today's attachment bytes were linked then. `historical_availability_verified=false` remains in all observations. This pass supplies no archive-availability recommendation.

## Files and validation

All artifacts are under `data/collection/korea_round10/`. Work remained under `staging/` until root confirmed the preceding refresh had completed, then standard manifests were published. `manifest.csv`, `observations.csv`, `source_recipe.json`, `download_log.json`, `repeat_model_evidence.json`, page renders and OCR preserve the original and its provenance. `basis_alias_recommendations.json` is empty.

`extract_reviewed.py` restores a missing PDF only if its SHA256 still matches, regenerates missing OCR with Poppler/Tesseract (`kor+eng`), validates both source hashes and the exact July29 vectors, then emits the six rows. Run:

```sh
python3 data/collection/korea_round10/extract_reviewed.py
```

Validation passed for one original, nine physical pages, three EPS forecasts and three revenues. The bounded route is complete: the requested original model was recovered, and further June25 searches are unnecessary for establishing this July revision. The source files are frozen for integration.
