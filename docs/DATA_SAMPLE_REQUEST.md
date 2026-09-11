# Analyst-history sample specification

Prepared 10 September 2026 for evaluating a licensed export or feed. This is a technical requirements document, not a sent message or purchasing commitment.

## Requested coverage

| Company | Reference listing | Forecast currency |
|---|---|---|
| Broadcom | NASDAQ AVGO | USD |
| Alphabet | NASDAQ GOOGL, with company-level linkage to GOOG | USD |
| NVIDIA | NASDAQ NVDA | USD |
| SK hynix | KRX 000660 common | KRW |
| Samsung Electronics | KRX 005930 common | KRW |
| Micron | NASDAQ MU | USD |
| Sandisk | NASDAQ SNDK, current post-separation entity | USD |
| ASML | Euronext Amsterdam ASML | EUR |
| Apple | NASDAQ AAPL | USD |
| BE Semiconductor Industries | Euronext Amsterdam BESI | EUR |

Outcomes announced from 2021-09-10 through 2026-09-10. Estimate and consensus history from 2020-09-10 through 2026-09-10 to allow one-year lead times. Include annual and quarterly EPS and revenue. Sandisk coverage starts when the current entity's estimates first became available; identify any pre-separation pro forma forecasts separately.

Include all historical contributors, not only current active coverage. Detail means individual broker/analyst forecasts and revisions, not a consensus time series labelled "analyst estimates".

## Required fields

- Stable company/security identity, listing, corporate-action history and fiscal period end dates.
- Stable analyst/person ID and name when entitled, broker ID and name, team/coauthor information where available, and dated affiliation/coverage changes.
- Metric, estimate value, unit, currency, fiscal target, accounting definition, EPS share basis and source/report identifier.
- Original analyst publication time, provider entry/availability time, subsequent update/correction timestamps, stopped/excluded flags and every retrievable revision.
- Comparable actuals, their announcement times, restatement history and any broker-adjusted actuals with definitions.
- Consensus at historical cutoffs, contributor count, mean/median, dispersion, source methodology and the underlying constituent panel where available.
- Any historical stock-specific earnings-estimate accuracy score, its original publication time, window, methodology and coverage. Keep this distinct from recommendation-return scores.

For a supplier demonstration, provide a small sample for all ten companies and a more detailed series for Broadcom and SK hynix spanning an earnings release and forecast revision. Include examples covering a stock split, a fiscal-year rollover, negative EPS and Sandisk's separation where supported. Demonstrate that subsequent corrections are distinguishable from the data available at an earlier cutoff.

## Access and cost questions to resolve

One-time historical export versus recurring feed, exact ten-company coverage, any broker-specific readership restrictions, local storage and API/export rights, permitted users for a private Dirk/Edwin project, historical-score availability, initial and recurring cost, and any minimum contract term.

A one-time licensed export could be sufficient for the first historical ranking if available on suitable terms. Availability and pricing have not been established. Do not buy a general charting subscription assuming it contains this dataset.

## Local import contract

`scripts/import_ntm.py` accepts the documented NTM CSV fields and now supports optional `analyst`, `firm` and `series_type` columns. Use `individual_analyst_forecast` only with both a named analyst and firm. `published_consensus` has no individual author and is excluded from analyst ensembles. Contributor identity, definition, currency and label must remain constant within an imported series. Use separate series IDs when any of these changes.

The app combines declared `reported_diluted` estimates within an issuer and currency after fiscal/NTM and split checks. `adjusted_diluted` and `non_gaap_diluted` remain firm-specific. Other definitions stay separate until a source-backed compatibility policy is recorded. Provider NTM values remain separate from day-weighted annual proxies. Import validation cannot independently prove the supplier's semantic or historical availability claims; those require the sample evidence above.
