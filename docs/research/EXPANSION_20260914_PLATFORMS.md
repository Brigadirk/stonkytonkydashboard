# Platform EPS evidence collected on 14 September 2026

This note records the September 2026 collection. Original downloads remain in the separate research archive; the reviewed values are included in `data/reviewed/expansion_20260914/`.

The collection contains 33 original Morningstar PDFs from Firstrade and two original iFAST article responses. It provides 11 USD series for MSFT, AMZN, META, ORCL, PLTR, and TSM. `dashboard_additions.json` is the proposed import. `all_eps_evidence.json` also holds TSMC's TWD forecasts, which must stay outside the USD-per-ADS dashboard.

The sources were retrieved on 13 September UTC / 14 September local time. The chart cutoff is 11 September 2026. The printed report dates are historical evidence dates, but historical public access has not been proved. Each snapshot uses the printed report date plus one calendar day as an explicit availability assumption. No capture date has been backdated, and no present estimate has been inserted into an older snapshot.

## Current numerical evidence

| Company | Printed report date | Printed model/table date | Current annual EPS forecasts | Basis and limits |
|---|---|---|---|---|
| Microsoft | 31 Jul 2026 | 29 Jul 2026 | FY27 19.74; FY28 23.42; FY29 26.90 | USD per share; diluted unadjusted and adjusted rows both show these values. Fiscal year ends 30 June. Page 16. |
| Amazon | 4 Aug 2026 | 30 Jul 2026 | FY26 12.37; FY27 8.73; FY28 10.13 | USD per share; both EPS rows show these values. Calendar year. Page 16. The printed decline in FY27 has been kept. |
| Meta | 26 Aug 2026 | 29 Jul 2026 | FY26 32.71; FY27 33.74; FY28 44.42 | USD per share; both forecast EPS rows show these values. Calendar year. Page 15. |
| Oracle | 11 Jun 2026 | 10 Jun 2026 | FY27 5.42 / 8.11; FY28 8.57 / 11.98; FY29 11.50 / 15.81 | USD per share; unadjusted / adjusted diluted. Fiscal year ends 31 May. Page 14. |
| Palantir | 4 Aug 2026 | 4 May 2026 | FY26 1.11 / 1.29; FY27 1.40 / 1.59; FY28 2.04 / 2.24 | USD per share; unadjusted / adjusted diluted. Calendar year. Page 15. The model is stale despite the August report date. |
| TSM ADS | 22 Jul 2026 | 17 Jul 2026 | FY26 16.1; FY27 20.6; FY28 25.2 | Native USD per ADR; iFAST / Bloomberg compilation; basic/diluted and adjusted/reported basis not stated. Table 4. |

The Oracle PDF printed on 11 September 2026 repeats a model dated 10 June. It is retained, but the assumed availability date is 12 September. It must not enter the 11 September chart. The June report supplies the earlier snapshot. Palantir's latest retrieved model is 130 days old at the cutoff. A 120-day age rule will exclude it. Failed attempts for newer reports are recorded in `manifest.json`.

The Morningstar authors are Dan Romanoff (Microsoft and Amazon), Malik Ahmed Khan (Meta), Luke Yang (Oracle), Mark Giarelli (Palantir), and Phelix Lee (TSMC). Each name was checked against the report's analyst note. Both EPS rows are kept as separate series. The unadjusted row uses the established `morningstar_unadjusted_diluted` basis. It is not declared equivalent to issuer GAAP EPS.

## Earlier snapshots and retained sources

The Morningstar history starts in July/August 2025 for Microsoft, Amazon, Meta, Palantir, and TSMC, and September 2025 for Oracle. It includes five or six report appearances per company through 2026. All five forecast columns are extracted from each report, with exact fiscal dates. Repeated or stale models have not been relabelled with a newer model date. Exact report timestamps, model dates, URL dates, SHA256 hashes, and page numbers are in the JSON. `manifest.json` includes failed access attempts.

TSMC's earlier native USD source is the [iFAST article dated 27 April 2026](https://fsm.global/sg/article/rcms365740). Table 4, dated 20 April, prints FY26/27/28 EPS of 14.3/18.1/21.7. The [22 July 2026 article](https://fsm.global/sg/article/rcms381560) prints the later series above. Both articles name iFAST Research Team. The tables name Bloomberg and iFAST Compilation; neither specifies a consensus contributor count or an accounting basis. Treat this as a publisher composite, separate from named analyst series. No earlier native USD snapshot was found in the bounded search, so the USD history starts in April 2026.

The normal article URL returns an app shell through direct HTTP. The full original content was obtained from the public read-only article API used by the publisher's JavaScript: `/sg/rest/article/get-rcms-article-details`, with `paramArticleId`, `paramPlatformId=SGFSM`, and `paramLocaleId=en_us`. The raw JSON contains the article HTML, title, named author, and exact publication timestamp. It is retained with SHA256 in `ifast_api_manifest.json`; the extracted HTML and text are adjacent. The publication timestamp has no stated timezone. No login or private endpoint was used.

TSMC's Morningstar reports print TWD per ordinary share, including FY26/27/28 101.38/129.90/157.97 in the July report. No explicit EPS conversion rate suitable for a report-date USD/ADS conversion was found. No conversion was inferred from rounded fair values. These 50 TWD forecast rows remain in `all_eps_evidence.json` only.

## Checks and limits

The retained PDF hashes were checked against the manifest. The extractor requires exactly one financial summary table, eight fiscal columns, and two EPS rows per PDF. It selects the five forecast columns, not the three actual columns. The six current Morningstar financial-summary pages were rendered and checked visually; the PNG files are retained. The two iFAST forecasts were checked against the original HTML tables and publication metadata.

Some reports use older model dates than their article dates. Those dates are retained. The collection proves what each retained report prints. It does not prove the date on which that exact PDF first became accessible, the correctness of the analyst model, or equality between different EPS accounting bases. The six companies all have at least one numerical forecast source; Palantir's age and TSMC's unspecified basis remain material limits.

Only this collection directory was written. Shared dataset and scripts were not edited.
