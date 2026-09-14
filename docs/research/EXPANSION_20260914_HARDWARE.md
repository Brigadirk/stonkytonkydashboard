# Annual EPS evidence for the AI dashboard expansion

This note records the September 2026 collection. Original downloads remain in the separate research archive; the reviewed values are included in `data/reviewed/expansion_20260914/`.

Research date: 14 September 2026, Europe/Amsterdam. UTC capture date: 13 September 2026. Price and forecast cutoff requested by the parent task: 11 September 2026.

The collection contains 33 original Morningstar analyst PDFs from its public Firstrade distributor. These provide 330 annual EPS entries across six companies, with five forecast fiscal years per report and two separately labelled EPS rows. A retained issuer release explains the remaining Cerebras forecast gap. `evidence.json` contains dashboard-shaped companies, series and snapshots, source records, flat evidence entries and the Cerebras gap. `extract.py` reproduces these values from the retained originals. Sources include page numbers, printed dates, model dates, original URLs, local paths and SHA-256 hashes.

The numbers below are each source's adjusted diluted EPS row, in USD per listed share. They are forecasts from Morningstar, not company guidance, consensus or reported earnings. No equivalence with each issuer's own adjusted earnings definition has been established.

| Company | Latest retained report date | Printed model date | FY2026 | FY2027 | FY2028 | Latest original |
|---|---|---|---:|---:|---:|---|
| AMD | 5 August 2026 | 24 July 2026 | 6.60 | 13.98 | 19.91 | [Morningstar, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000006A_20260804_RT.pdf) |
| Arista | 5 August 2026 | 4 August 2026 | 4.22 | 5.34 | 6.60 | [Morningstar, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001354B_20260804_RT.pdf) |
| Marvell | 28 August 2026 | 27 August 2026 | Actual period; not imported as a forecast | 4.28 | 7.38 | [Morningstar, p. 14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000003H5_20260827_RT.pdf) |
| Vertiv | 29 July 2026 | 29 July 2026 | 6.72 | 8.28 | 10.89 | [Morningstar, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001E1XR_20260729_RT.pdf) |
| Nebius | 12 August 2026 | 13 May 2026; conflicting header | -4.42 | 4.85 | 6.74 | [Morningstar, p. 14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000TDA0_20260812_RT.pdf) |
| SpaceX | 5 August 2026 | 16 June 2026 | 0.04 | 0.47 | 0.58 | [Morningstar, p. 15](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0002DZNH_20260804_RT.pdf) |

Marvell's FY2029 adjusted diluted EPS is 12.67. Its source fiscal year ends on 31 January, so FY2028 covers most of calendar 2027. All other source tables use a 31 December year-end. AMD and Marvell use issuer calendars of 52 or 53 weeks. The supplied start/end dates apply the verified issuer calendar rules: AMD ends on the last Saturday in December; Marvell ends on the Saturday nearest January 31. The source table nominal month-end is retained in the source metadata. Future dates are calculated from those rules. The official filing originals are retained, with hashes in `fiscal_calendar_sources.json`. [Marvell, p. 14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P000003H5_20260827_RT.pdf), [AMD, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000006A_20260804_RT.pdf)

The named analysts are Brian Colello for AMD, William Kerwin for Marvell and Arista, Nicholas Lieb for Vertiv, Javier Correonero for Nebius, and Nicolas Owens for SpaceX. Each retained original identifies the analyst in its analyst note and company analysis.

## Dates, losses and changes

- Each snapshot becomes available on the calendar day after its printed report date. This is the requested conservative dashboard convention. It is not independent proof of original publication availability. `retrieved_at` records this research pass, not the printed date. Dated report snapshots do not use `first_observed_at`.
- Reprints retain the earlier financial model date. Their publication is not counted as a new independent forecast revision. AMD's August report, for example, contains a model dated 24 July. SpaceX's August report repeats its June model.
- Nebius's August report prints a May model date while its values materially differ from the retained May report. The source date claim is preserved. The values cannot be backdated into May. The August values are only supported from the August report appearance; a strict model-age filter can still regard the date as old. The parent must keep this warning visible or quarantine this snapshot until the model date is reconciled. [May original, p. 12](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000TDA0_20260514_RT.pdf), [August original, p. 14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000TDA0_20260812_RT.pdf)
- Negative EPS values remain negative. Nebius's May model has adjusted FY2026 EPS of -5.20 and FY2027 EPS of -1.24. Its August table has adjusted FY2026 EPS of -4.42. Do not use zero or a positive substitute. [May original, p. 12](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000TDA0_20260514_RT.pdf), [August original, p. 14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0000TDA0_20260812_RT.pdf)
- SpaceX's June 16 model changes historical net income and future EPS relative to June 12. Its model-revision table confirms replacement values. The precise historical consolidation scope and accounting comparability have not been independently reconciled. Both source versions remain dated evidence. [June 12 original, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0002DZNH_20260612_RT.pdf), [June 16 original, pp. 13-14](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0002DZNH_20260616_RT.pdf)
- Arista's retained values are on the share units shown in reports published after its December 2024 split. They are not values to divide by four again. The latest report shows FY2024 diluted EPS of 2.23 and FY2025 diluted EPS of 2.75. [Arista, p. 13](https://invest.firstrade.com/ms/equity_reports/sr/2026/0P0001354B_20260804_RT.pdf)

## Historical coverage and limits

| Company | Retained analyst PDFs | Earliest retained printed report | Distinct later report appearances |
|---|---:|---|---|
| AMD | 7 | 6 August 2025 | October/November 2025, February/May/August 2026 |
| Marvell | 6 | 29 August 2025 | December 2025, March/May/August 2026 |
| Arista | 7 | 6 August 2025 | November 2025, February/May/August 2026 |
| Vertiv | 6 | 30 July 2025 | October 2025, February/April/July 2026 |
| Nebius | 3 | 17 March 2026 | May/August 2026 |
| SpaceX | 4 | 12 June 2026 | June 16/June 29/August 5 2026 |

These are irregular retained model appearances. They do not supply a complete daily forecast history. All 33 PDFs were parsed with exact table headings, year columns and two EPS row labels checked. The six latest model pages were rendered and visually checked. The older appearances were text-checked. Original hashes are in `evidence.json`; request status records are in `amd_retrieval.json`, `retrieval.json` and `spacex_extra_retrieval.json`.

## Cerebras

No dated original annual analyst EPS forecast was retained. Fifteen candidate Morningstar/Firstrade report URLs returned HTTP 404. Direct retrieval of Morningstar quote pages returned HTTP 403. These failed attempts establish an access or coverage gap, not an absence of all analyst coverage.

The retained [Cerebras Q2 2026 issuer release](https://investors.cerebras.ai/node/7286/pdf), dated 12 August, gives full-year core revenue and margin guidance. It does not provide annual EPS guidance for FY2027 and FY2028. Revenue, operating margin and annual EPS are different metrics. I did not calculate an EPS estimate from the guidance or import current consensus as a historical estimate.

The release is retained as `raw/cerebras_issuer_q2_2026.pdf`; `cerebras_issuer_source.json` records its original URL, capture time and SHA-256 hash. Reported earnings can be added separately from issuer/SEC data by the parent task.

## Fiscal calendar evidence

[AMD's August 2026 10-Q](https://ir.amd.com/financial-information/sec-filings/content/0000002488-26-000123/amd-20260627.htm), Note 2, states the last-Saturday-in-December rule and confirms FY2026 ends on 26 December 2026. [Marvell's FY2026 10-K](https://investor.marvell.com/sec-filings/all-sec-filings/content/0001835632-26-000011/mrvl-20260131.htm), Business and fiscal-year sections, states the nearest-Saturday-to-January-31 rule. Applying these rules gives AMD FY2027: 27 December 2026 to 25 December 2027; AMD FY2028: 26 December 2027 to 30 December 2028. Marvell FY2027: 1 February 2026 to 30 January 2027; Marvell FY2028: 31 January 2027 to 29 January 2028; Marvell FY2029: 30 January 2028 to 3 February 2029. These dates are calculated calendar boundaries, not separately issued forecasts.

The unadjusted source EPS series uses `morningstar_unadjusted_diluted`. This avoids implying equivalence with issuer-reported EPS. The separately labelled adjusted row uses `adjusted_diluted`.
