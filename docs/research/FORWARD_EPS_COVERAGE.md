# Forward EPS coverage for the dashboard

Historical implementation audit, before round 4. Counts and exclusions below describe the earlier 491-row dataset. The current dataset, new consensus series, supported Korean basis aliases and additional fiscal evidence are documented in [ROUND4_PROGRESS.md](ROUND4_PROGRESS.md).

Audit date: 10 September 2026. Input: the 491 observations in `data/collected_forecasts.csv`. Reproduce with `python3 scripts/build_forecast_panel.py`.

The chart dataset contains **198 EPS observations in 27 separate analyst, firm and accounting-basis series**. Six companies have sparse original reports that can support a dated-report reconstruction. ASML and Sandisk have no eligible named-analyst EPS series in the retained archive. None of these histories is verified as a complete point-in-time feed.

## Coverage

| Company | Retained EPS observations | Separate series | Earliest retained report | Latest retained report |
| --- | ---: | ---: | --- | --- |
| Broadcom | 26 | 3 | 2025-06-26 | 2026-03-09 |
| Alphabet | 20 | 2 | 2025-05-08 | 2025-11-25 |
| Nvidia | 13 | 2 | 2024-10-10 | 2026-03-19 |
| SK hynix | 69 | 9 | 2021-01-08 | 2026-09-07 |
| Samsung Electronics | 50 | 9 | 2020-07-31 | 2026-09-07 |
| Micron | 20 | 2 | 2025-04-03 | 2025-09-24 |
| Sandisk | 0 | 0 | — | — |
| ASML | 0 | 0 | — | — |

Dates in this table mark collected reports, not uninterrupted coverage between the endpoints. The Korean histories contain long gaps. Reports before the five-year chart window can serve only as warmup inputs, subject to the same estimate-age limit. Different accounting-basis descriptions remain separate even when the analyst and firm match. No accuracy ranking or consensus weighting is implied.

The builder excludes 225 observations that are not EPS, 33 quarantined EPS observations, 22 consensus or otherwise non-individual EPS observations, two Broadcom EPS observations with no restated accounting definition, one rounded Nvidia team forecast, and ten unchanged Micron reprint observations. The raw archive retains all 491 observations.

## Availability and model age

Each panel row preserves its original observation ID, numerical EPS, report date, source URL, local PDF, SHA-256 hash and physical page. The builder verifies every retained source hash before writing output.

`available_date` is the calendar day after the printed report date. This is an explicit reconstruction assumption because the original first-publication timestamp has not been independently verified. It does not convert a retrieved PDF into a verified contemporaneous observation. A chart must not use a row before `available_date`.

`model_date` records the older financial-model timestamp where the PDF prints one. Estimate age starts from `model_date`, or from `report_date` when there is no separate model timestamp. A reprinted report must not renew estimate freshness. For example, the [Micron report generated on 18 December 2025](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20251217_RT.pdf), page 13, repeats the financial model dated 23 September 2025 in the [September report](https://invest.firstrade.com/ms/equity_reports/sr/2025/0P000003MC_20250923_RT.pdf). The panel retains the earlier available copy and omits the ten repeated EPS rows.

`snapshot_id` groups annual forecasts from one artifact, analyst and accounting basis. FY1 and FY2 must come from one snapshot. Combining FY1 from a newer report with FY2 from an older model would invent a forecast vintage that no analyst published. When a newer eligible snapshot lacks a required annual period, show a gap rather than silently fill it from an older snapshot.

## Accounting and share basis

Reported diluted EPS and adjusted diluted EPS remain distinct series for Morningstar's Broadcom, Alphabet and Micron forecasts. BOCOM's non-GAAP forecasts remain separate from Morningstar and from differently described BOCOM EPS. Nvidia's 2024 Morningstar table explicitly labels diluted EPS but does not resolve all adjustments, so its series retains that limitation. See the [original Nvidia model](https://invest.firstrade.com/ms/equity_reports/sr/2024/0P000003RE_20241010_RT.pdf), physical page 16.

Korean broker tables use consolidated, parent-attributable or K-IFRS descriptions. Their basic-versus-diluted denominator has not been fully reconciled. The panel preserves each recorded basis separately and labels the figures as broker EPS. This is sufficient to display the broker's own printed estimates as a clearly labelled reconstruction. It does not justify comparison with statutory diluted EPS, cross-broker consensus, or analyst accuracy scores.

`eps` is in the row's currency per share, exactly as printed. `share_basis_date` is the printed model date, or report date if there is no model date. It is the reference date for corporate-action review, not an assertion that every broker applies adjustments on that date. The panel applies no split or currency adjustment. The chart must put price and EPS on the same share basis. It must not divide dividend-adjusted total-return prices by unadjusted EPS.

Loss estimates remain in the panel because a negative earnings forecast is data. A P/E chart should suppress nonpositive forward EPS, show the earnings value separately, and explain the missing multiple. Removing losses from the archive would hide the memory companies' cycles.

## Exact fiscal calendars

The broker templates often print a month-end shorthand. The panel calculates fiscal period starts and ends under issuer rules, and records the rule and source on every row. Future period dates are projections under the published calendar rule, not separately announced dates.

| Company | Calendar rule | Example | Primary evidence |
| --- | --- | --- | --- |
| Nvidia | Last Sunday in January | FY2026 ends 2026-01-25; FY2027 ends 2027-01-31 and has 53 weeks | [Nvidia FY2027 Q2 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm) |
| Broadcom | Sunday closest to October 31 | FY2025 ends 2025-11-02; FY2026 ends 2026-11-01 | [Broadcom 2025 Form 10-K](https://investors.broadcom.com/static-files/752e631c-b5f3-46af-9d67-bdeb658f5fa2), [2026 interim statement](https://www.sec.gov/Archives/edgar/data/1730168/000173016826000054/R8.htm) |
| Micron | Thursday closest to August 31 | FY2025 ends 2025-08-28; FY2026 ends 2026-09-03 and has 53 weeks | [Micron fiscal-period accounting policy](https://www.sec.gov/Archives/edgar/data/723125/000072312526000006/R26.htm) |
| Alphabet | Calendar year ending December 31 | FY2025 ends 2025-12-31 | [Alphabet 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) |
| Samsung Electronics | Calendar year ending December 31 | FY2025 ends 2025-12-31 | [Samsung 2025 consolidated statements](https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_con_quarter04_all.pdf) |
| SK hynix | Calendar year ending December 31 | FY2025 ends 2025-12-31 | [SK hynix 2025 results](https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/) |

For a forward twelve-month proxy, select the current and following fiscal year from the latest eligible snapshot. One defensible approximation assumes uniform daily earnings within each fiscal year, summing each EPS value multiplied by the share of its fiscal days that fall within the next twelve calendar months. Exact calendar boundaries handle leap years and 53-week years. This is an annual-model interpolation, not an analyst's published quarterly NTM estimate. The dashboard must name the method it implements and preserve gaps where the required annual forecasts are absent or stale.

## Bounded new-source search

Targeted searches covered BOCOM, Phillip, DBS and Websim originals for ASML or the new standalone Sandisk. They did not add eligible EPS observations in this pass.

The [Websim ASML attachment](https://www.websim.it/static/upload/asm/asml-holding-06-06-24.pdf) contains a one-page financial model. The numerical table is useful discovery evidence, but the file does not print a named analyst or report date. A date embedded in its URL is insufficient. It remains a lead pending its signed, dated cover or an original publisher page establishing attribution and timing.

The [DBS equities weekly dated 17 September 2025](https://www.dbs.com/content/article/pdf/CIO/2025/202509/250917EquitiesWeekly.pdf) includes a signed ASML note by Lee Keng Ling on physical page 5. Its summary gives a forward multiple with mixed Bloomberg/DBS sourcing, without a dated annual EPS model. Inferring EPS by dividing that rounded multiple into the share price would not produce an attributable FY1/FY2 forecast.

Previously retained ASML evidence remains excluded: the x2 sample has conflicting print and PDF creation dates, while the Morningstar excerpt does not supply a complete validated model. Sandisk's retained Morningstar search excerpt lacks the original signed report. Standalone Sandisk history must begin with its 2025 listing, not be spliced to the old acquired SanDisk business or Western Digital's earlier EPS.

## Subscription boundary

The missing ingredient for complete five-year bands is a dated EPS estimate history with revisions and availability, not additional price history or faster text extraction. The required sample has FY1/FY2 or quarterly NTM EPS for all eight securities, analyst and broker identifiers, fiscal period ends, EPS accounting definitions, currency, corporate-action basis, estimate activation and withdrawal timestamps, and comparable actuals. Consensus must remain a separate selectable series.

[FactSet's estimates product description](https://insight.factset.com/resources/factset-consensus-estimates-datafeed) distinguishes historical analyst/broker detail from consensus. Its [point-in-time documentation](https://www.insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf) describes daily historical consensus snapshots, including annual periods and statistics. [LSEG's quant data brochure](https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/lseg-data-for-quant-research-brochure.pdf) separately describes I/B/E/S historical, daily means and point-in-time products. These documents establish relevant product categories; they do not verify our entitlement, exact eight-name coverage, usable extraction limits or a price.

No subscription was bought and no provider was contacted. ScrapingBee was not used. Public PDFs retrieved directly do not establish that proxy credits would obtain the missing historical reports or any subscription entitlement. A subscription sample or a user's licensed export is the concrete next input for complete histories; the app can already expose the current gaps.
