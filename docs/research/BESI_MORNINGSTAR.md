# BESI: Morningstar forecast collection

Cutoff: 10 September2026. Collection: `data/collection/besi_morningstar/`. No shared datasets, scripts or UI were edited. The collection contains **8 observations: 5 EPS and 3 revenue**, supported by two retained original PDFs and one explicitly weaker publisher-excerpt artifact.

## Security identity and collection boundary

The correct Amsterdam ordinary-share Morningstar security ID is **`0P0000A65M`**. The [Morningstar stock report identity page](https://lt.morningstar.com/1c6qh1t6k9/stockreport/default.aspx?BaseCurrencyId=EUR&CurrencyId=EUR&SecurityToken=0P0000A65M%5D3%5D0%5DE0EXG%24XAMS&externalidmic=XAMS&source=HS) identifies BE Semiconductor Industries, ISIN **NL0012866412**, EUR and the Amsterdam listing. Its original HTML is retained at `discovery/identity.html`, SHA256 `20c945f075920fac363c044207aa5ab900f99979545e5d64a253e3c65078742f`. The older [Morningstar Netherlands route](https://tools.morningstar.nl/nl/stockreport/default.aspx?SecurityToken=0P0000A65M%5D3%5D0%5DE0WWE%24%24ALL) also identifies this security. The root agent verified the issuer's ordinary listing, December31 annual calendar and May4,2018 2:1 split against issuer materials, including the [2025 annual report](https://www.besi.com/fileadmin/data/Investor_Relations/_Semi__Annual_Reports/Annual_Report_2025.pdf). Values below remain on their printed post-2018 share basis; no split conversion was applied.

The original May2024 report's archived notes record **coverage initiation on 27 June2023**, by Javier Correonero, physical page9. Earlier historical financial figures in the report are actuals, not evidence of 2021–22 analyst forecasts. This pass recovered no original 2023 model or additional full 2025–26 Morningstar model.

## Retained forecast evidence

| Original report / note date | Numerical model date | Fiscal forecasts | Definition and provenance |
|---|---|---|---|
| 4 May2024, 04:17 UTC | 25 April2024 | FY2024/25/26 EPS **EUR2.86/4.18/5.18**; revenue **EUR760.865m/1,036.990m/1,336.402m** | Original 21-page Morningstar report, Javier Correonero, mirrored on Eurobench; physical page13. Diluted EPS is explicit; adjustment basis is unresolved. |
| 5 August2024, 13:30 UTC | Not printed for BESI | FY2025 EPS **EUR3.90** | Same-day Javier Correonero note inside an original Firstrade-distributed ASML report, physical page1. Explicit BESI EPS statement; basic/diluted and adjustment basis unresolved. |
| 24 July2025 | Not printed | FY2028 EPS **EUR5.5** | Public Morningstar UK article, Javier Correonero. Only a short browser-rendered publisher excerpt was retained; direct HTML returned403. Basic/diluted and adjustment basis unresolved. |

### May2024 full model

Original URL: [Eurobench mirrored Morningstar PDF](https://www.eurobench.com/Forum/Upload/2024/15284468.pdf). Retained `originals/besi_20240504.pdf`, SHA256 **`0bf1f9f483933249cfdef7255079cbd9fd21fe71de5a2fb69e654aa31a7cec5e`**. The intact report identifies Amsterdam BESI, EUR, its analyst, timestamp, dated model, financial tables and publisher disclosures. The [forum attachment post](https://www.iex.nl/Forum/Post/15284468.aspx), retained as discovery HTML, is dated 7 May2024 and describes a BESI MS analysis. Eurobench/IEX is a **third-party forum mirror, not an official Morningstar distributor**. The source was accepted as the publisher's original document with explicit mirror provenance; the historical availability timestamp remains unverified.

Physical page13 was rendered and visually checked; the retained review image is `review/besi_20240504_p13.png`. Only the three columns explicitly headed Estimates were extracted. The raw labels are FY2024/2025/2026, December31 fiscal years, `Diluted Earnings Per Share(EUR)` and `Revenue (EUR K)`. Revenue was converted from thousands to millions solely for the existing ingestion schema; `source_value` and `source_unit` preserve the printed amounts. The model header's `Fiscal Year, ends31Dec2023` is the historical anchor, not a claim that every forecast ends in2023.

No accounting alias is proposed. The lower analyst model's historical FY2022/23 EPS is2.81/2.14, while the upper historical-summary EPS is2.90/2.23. This difference itself cautions against treating the legacy model as issuer reported EPS. All three forecasts retain `diluted_adjustment_basis_unresolved`; no GAAP/IFRS or issuer-adjusted equivalence is inferred.

### August2024 explicit peer forecast

Original URL: [Firstrade-distributed 5 August2024 Morningstar ASML report](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P0000002X_20240805_RT.pdf). Retained `originals/asml_peer_besi_20240805.pdf`, SHA256 **`29f0a4cd2cfbfc842a717f7bb09505402423f7fe76c67ac76b13db8ec7fe0611`**. Physical page1 was rendered and visually checked. The note explicitly assigns FY2025 EUR3.90 EPS to BESI; the EPS is printed independently of the adjacent P/E multiple and is not derived from it. The byline and report timestamp are both 5 August2024, avoiding the later-reprint issue found in the October ASML archive. The [publisher's report landing page](https://www.morningstar.com/company-reports/1236461-every-cloud-has-a-silver-lining-we-recommend-investors-buy-shares-of-asml-and-besi) independently identifies the joint ASML/BESI note.

ASML's numerical model date and accounting labels do not establish the peer BESI forecast's definition. The BESI numerical model date remains blank. This single fiscal target cannot independently supply a consecutive-year NTM pair.

### July2025 publisher excerpt

The [Morningstar UK article](https://global.morningstar.com/en-gb/stocks/besi-earnings-quiet-quarter-loud-outlook-order-book-ramping-up) explicitly forecasts FY2028 EUR5.5 EPS under its dated Javier Correonero byline. The [Morningstar company-report landing page](https://www.morningstar.com/company-reports/1314489-besi-earnings-quiet-quarter-but-loud-outlook-order-book-ramping-up) corroborates author and date. Browser search rendering exposed the first-party article and forecast; direct requests to both English regional versions returned403. `discovery/besi_note_20250724_publisher_excerpt.json` preserves a short exact EPS excerpt, locator, source URL and retrieval limitations. This is **an evidence excerpt, not retained original HTML/PDF**, and its manifest and observation status make that distinction explicit. The annual statement is retained because it is an explicit attributed forecast; it does not supply a usable NTM pair or establish a bridge to the 2024 diluted model.

## Unsuccessful discovery and remaining gaps

`download_log.json` retains 25 exact public Firstrade URL attempts for Amsterdam ID`0P0000A65M`, across relevant 2024–26 dates; all returned404. The correct security identity does **not** prove this listing is served by Firstrade. **Keep automated Firstrade discovery for BESI disabled** pending a successful original report for that ID. The successful ASML ID`0P0000002X` is only the host report for the separately attributed peer note.

Bounded forum discovery retained the May2024 attachment page, the uploader's public profile and three relevant 2025 thread pages. It recovered no further usable original BESI Morningstar financial tables. Forum posts and current dynamic quote figures were not treated as dated analyst models. No estimates were reconstructed from fair values, target prices or P/E ratios. No paid subscription, account or external messages were used.

## Reproducibility and validation

`build_collection.py` materializes the compatible `manifest.csv` and `observations.csv` from the manually verified evidence. It validates the8 unique observation IDs, source-file hashes, cutoff and blank historical-availability fields. Original report dates, original model dates, printed timestamps and retrieval dates remain distinct. `available_at` and `original_available_at` are blank throughout. The collection supports report-date reconstruction subject to its explicit provenance limits, not independently verified point-in-time availability.

The root agent may integrate these rows alongside the other agent's newer licensed consensus tables. No cross-broker or cross-basis stitching is recommended. EPS definitions remain unresolved in this Morningstar pass; retain that gap rather than converting an explicit but undefined EPS value into a reported or adjusted series.
