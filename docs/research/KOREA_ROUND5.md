# Korean memory gap collection — round 5

Collected September 10, 2026 in response to the new stock/month gap map. Files are stable for shared import.

## Result

Retained six original broker PDFs (38 pages), including five usable annual model reports. Extracted **10 annual EPS estimates and 10 annual revenue estimates**, all FY2026/27 pairs: three Samsung models and two SK hynix models. This supplies January 2026 model anchors and better February coverage without a subscription or proxy service.

| Company | Analyst | Printed report date | FY2026 EPS, KRW | FY2027 EPS, KRW | Source, physical page 1 |
|---|---|---|---:|---:|---|
| sk_hynix | Jeff Kim / kb | 2026-01-14 | 133,432 | 156,841 | [Original PDF](https://rdata.kbsec.com/pdf_data/20260113194310367E.pdf) |
| samsung_electronics | Jeff Kim / kb | 2026-01-23 | 18,299 | 20,650 | [Original PDF](https://rdata.kbsec.com/pdf_data/20260122215610647E.pdf) |
| samsung_electronics | Sunwoo Kim / meritz | 2026-01-29 | 16,501 | 19,663 | [Original PDF](http://home.imeritz.com/include/resource/research/WorkFlow/20260129193040830K_02.pdf) |
| sk_hynix | Sunwoo Kim / meritz | 2026-01-29 | 166,534 | 197,095 | [Original PDF](http://home.imeritz.com/include/resource/research/WorkFlow/20260129211553879K_02.pdf) |
| samsung_electronics | Jeff Kim / kb | 2026-02-23 | 20,934 | 23,283 | [Original PDF](https://rdata.kbsec.com/pdf_data/20260220140952410E.pdf) |

## Discovery and dating

Meritz originals were located through the analyst team’s public Telegram channel, using [Samsung’s January 29 post](https://t.me/merITz_tech/15459) and [SK hynix’s January 29 post](https://t.me/merITz_tech/15460). Their short links resolve directly to original Meritz PDF files. Both physical reports are dated **January 29, 2026** even though subsequent press coverage and the initial discovery keys use January 30. The printed original date governs the CSV. Public discovery HTML is retained under `discovery/`; no account, posting or messaging was used.

The [January 8 Samsung issue comment](https://home.imeritz.com/include/resource/research/WorkFlow/20260108094413584K_02.pdf) was also recovered from Meritz after identifying its exact filename in a public distributor result. It discusses operating-profit projections but has **no annual EPS model**, so it contributes no forecast rows. Its original short link failed with a transport/TLS error; the directly addressed public original downloaded successfully.

## Basis rules

Meritz EPS is explicitly labelled parent-attributable in the original first-page summary. It uses the existing scoped basis label `EPS labelled parent-attributable; basic/diluted and share denominator not established`. The table does not establish a fully normalized statutory basic/diluted or preferred-share allocation basis; none is inferred. The new Samsung summary’s historical and forecast EPS denominators should not be assumed identical without further reconciliation.

KB EPS follows net profit to controlling interests in the first-page earnings table and uses the existing scoped KB basis label `Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS`. KB, Meritz, Samsung and Hynix retain their separate models; target-price consensus is not used as earnings consensus. Only the FY2026E and FY2027E columns are extracted. Completed FY2025 columns are excluded from this targeted collection.

Revenue `value` fields are normalized to base KRW as required by the project’s Korean collection schema. `original_value` and `original_unit` preserve the printed KRW trillion (Meritz Samsung) or KRW billion (Meritz Hynix / KB) units. EPS values remain as printed, in KRW per share.

Report dates are established from physical originals; original dissemination timestamps remain unverified. The collection does not claim that Telegram’s currently displayed post time proves the historical contents of the linked PDF. No availability timestamp is manufactured.

## Remaining gap

These originals improve the second half of January and February. They do not establish fresh EPS models for the opening days of January; late-2025 or earlier-January originals remain a useful next target. The January 8 issue comment cannot fill that gap because it contains no annual EPS.

## Reproduction and verification

`python3 data/collection/korea_round5/extract_reviewed.py` reproduces `manifest.csv`, `observations.csv` and `summary.json` offline. It checks source hashes, exact report dates and EPS vectors, bylines, controlling-interest labels, fiscal columns and printed units. All five extracted physical tables were rendered and visually verified; images are retained beside the CSVs. `validation.json` records the checks.

No shared scripts, merged datasets or UI files were modified by this collection task.
