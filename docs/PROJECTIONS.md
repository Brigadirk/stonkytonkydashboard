# One-year projections and the overview

Implemented 10 September 2026, following the functional layout in `Untitled.jpg`. The existing visual theme and larger interface sizing remain in place.

## Entry window, target reference and target date

The entry comparison and future target now use separate valuation references:

- **90 days, 180 days, one year, or a custom entry window:** compare today's price with its usual valuation over this period, using current forward EPS. This changes historical entry bands and the current discount or premium.
- **365-day target reference:** the prior year's forward-P/E median and sample standard deviation determine all future target levels. It is independent of the entry selector. Switching an entry window does not change the target price, EPS, median, standard deviation or contributors.
- **One year ahead:** on which future date is the share-price scenario being valued?

Let `t` be the latest retained close on or before the selected as-of date. The target date `T` is the calendar anniversary of `t`. For US stocks in the current September 10 dataset, the latest close is September 9, so the target is September 9, 2027. Local Korea and Amsterdam closes use September 10, 2027. A February 29 origin has a February 28 anniversary.

Today's NTM EPS covers the next twelve months. A share price one year ahead, valued on forward earnings at that future date, instead needs the earnings expected during months 13–24 from the origin:

```text
E(T | t) = annual earnings forecasts known at t,
           allocated across (T, T + one calendar year]

M(t, W) = median of valid then-available forward P/E in [t − W, t)
S(t, W) = sample standard deviation of those historical multiples

entry_usual_price(t, W) = current_forward_EPS(t) × M(t, W)
entry_discount_or_premium = observed_price(t) / entry_usual_price(t, W) − 1

scenario_price(T, k) = E(T | t) × [M(t, 365) + k × S(t, 365)]
k = −2, −1.5, −1, 0, +1, +1.5, +2

scenario_change = scenario_price / origin_close − 1
```

Annual EPS is allocated by overlapping calendar days divided by the exact fiscal year's days. Leap years and 53-week fiscal years retain their actual lengths. Every required annual target comes from the same frozen snapshot. This is an annual-model proxy, not a quarterly seasonality model. A forward price target from this app is a calculated valuation scenario, not a broker's published price target.

Both reference distributions exclude the origin day and require at least 20 valid prior observations. The target's 365-day median and standard deviation stay fixed during the future projection and when the entry window changes. Higher sigma still selects a higher target valuation multiple; sigma does not assign an event probability or predict a future multiple. The displayed percentage is a price change, excluding dividends and any currency conversion for the investor. Neither reference fills missing observations or claims a full year's coverage when only a partial reference is retained.

## Frozen forecasts and contributors

`targetReference` rebuilds the historical EPS/P/E series with the independent 365-day target window, using the same single/combined selection and eligibility rules. `projectValuation` consumes the exact models at that origin. It does not query the archive at the future target date. Availability, strict verification and model freshness are checked at the origin, so a valid model is not made artificially stale by projecting a year ahead. Reports published after the origin cannot alter the projection. Reprints do not renew model age.

For a combined view, the historical EPS series is combined before calculating historical P/E. The future EPS is the median or equal-weighted mean of the same origin contributors' future EPS. All origin contributors must supply compatible, complete future fiscal coverage. If one member cannot do so, the combined projection has a gap. It does not silently discard that member or substitute an older model. The user can change the selected contributors, which recomputes the full historical comparison as well.

Negative individual estimates remain in the combination. Non-positive or near-zero combined EPS prevents P/E-based prices. Non-positive scenario multiples are omitted. Currencies, earnings definitions, fiscal periods and share bases retain the existing compatibility rules. Published consensus remains outside analyst ensembles.

An imported NTM-only value cannot be rolled forward into months 13–24. It needs dated annual or explicitly horizon-matched earnings estimates. Missing future intervals are listed as exact calendar dates. Missing earnings stay missing. The same rules apply on every projected date, so bands stop as soon as the frozen models no longer cover the required earnings interval.

## Views and exports

The main chart extends one year beyond the latest retained close. Historical bands use the selected entry window and each historical date's available forecasts. All seven future valuation bands extend to the exact one-year anniversary, with the selected level emphasized along its curve and at its target marker. On each future calendar day d, the band is E(d | t) × [M(t, 365) + k × S(t, 365)]. The earnings interval rolls forward; the origin models, contributors and valuation multiples remain fixed. These are calculated valuation levels, not a simulated market-price trajectory. Their origin values are contemporaneous valuations rather than the observed close. Historical entry bands can differ at the origin when the entry window is not 365 days; the legend identifies the separate references. Lines and fills break at unsupported dates. The actual-price trace ends at the origin. Selecting a deviation changes the headline one-year target without changing the other bands.

The cursor shows historical closing price and forward P/E from that historical point's eligible EPS, never today's EPS applied backward. A missing or unusable denominator is labelled unavailable while the close remains visible. Overlay mode labels this as the primary estimator's P/E; combined mode uses the historical ensemble EPS. Historical dates without a retained close are collapsed on the horizontal axis, using each listing's retained records rather than a generic weekday calendar. This also applies to the earnings chart and overview mini charts. Dates with a close but missing EPS remain visible. At a collapsed interval, cursor date conversion resolves floating-point rounding to the next recorded date, so it cannot show a hidden holiday. Future calendar dates remain visible for the projections. This changes display spacing only: lookback windows, forecast ages, fiscal-day allocation, source prices and target dates retain their original calendar meanings. Future dates show the selected projected valuation and its P/E; overlays show the range across available estimators and the available/selected count. Daily projection calculations provide exact calendar-date readouts without interpolating missing estimates.

The stock chart is 640 pixels tall, 60% taller than the original 400-pixel chart. Its vertical scale fits the visible prices, bands and targets with padding, without forcing a zero baseline.

The original contemporaneous valuation remains in the historical date inspector and the Advanced timing note. `projectionCurve` calculates all calendar dates from the origin through its anniversary, using the existing annual-model day allocation. The terminal target calculation and its CSV are unchanged. Return volatility is not calculated by the app or required to display the bands or targets.

All stocks defaults to a simple overview. Its primary controls are the entry window, with 90 days, 180 days and one year, and the target valuation level, with Low, Typical and High. Typical uses the 365-day median; Low and High use that reference's −2σ and +2σ. Each row shows the company, observed close and entry premium/discount, one dated future target, percentage change and compact price chart. Advanced can compare two entry windows without duplicating the same future target. Mini charts share the projected bands and target while their historical bands differ. Their shared price scale includes all historical and projected values, including intermediate valuation peaks. Chart history selects 6 months, 1, 2, 3 or 5 years of retained prices and their available historical bands, independently of both valuation references. The stock page and overview share this display setting with Advanced, including persistence and view links. Existing saved choices are respected; a new session defaults to five years. The stock page shows all seven future target levels. Clicking any target highlights its projected band and marker and enlarges that target in the headline. All seven levels remain visible, including ±1 and ±1.5σ.

“Advanced” at the top of the page opens the research workspace and contains the custom window, exact sigma selector, second-window comparison, sorting, source/model dates and ages, reference coverage, precise gap reasons and exports. The main view has no ranking column or methodological paragraphs. Missing targets show “Unavailable”; opening the stock or the evidence table explains the precise reason. Clicking a stock, target or chart opens that stock with the same calculation settings and the current simple/Advanced display choice.

Existing saved preferences and old comparison links start with a single window after this layout update. Choices subsequently made in the overview persist and travel in new view links. The simple workspace always shows one window; Advanced restores the saved comparison preference. The app starts in the simple workspace on reload without resetting calculation settings. Sorting by projected upside compares the selected scenario's percentage price change, not analyst accuracy or expected return. The same earnings series remains in use across reference windows.

In combined mode, the currently selected stock retains its chosen contributors, and other stocks use all compatible contributors of their default group. In overlay mode, the overview uses each stock's primary series. Model ages, report-date fallbacks and reference counts remain available under Advanced. Projection details expose source reports, printed annual targets, missing dates, included contributors and exclusions. EPS disagreement remains separate from historical P/E variation.

Projection CSVs include every scenario level, origin and target dates, the future earnings interval, the 365-day target reference bounds/counts, source snapshots and hashes, contributor exclusions, age/verification settings, each model’s split-normalization factor and origin-price provenance. The overview exports one target row per stock, including when comparing two entry windows. Historical chart exports retain the chosen entry window and observed dates only. Entry window, sigma, comparison and sort settings persist and travel in view links. Existing saved 90-day views migrate automatically because their window now controls entry timing only.

## Retired illustrative paths

The illustrative future price paths were removed from the stock chart, All stocks and Advanced on September 11, 2026. They are also absent from cursor values and app exports. The replacement projected bands use rolling forward earnings at fixed historical valuation multiples. They do not use the retired volatility blend, collapse the bands onto the observed close, or assume a route for the market price.

The prior `anchored_log_scenarios_v1` research implementation and `scripts/build_corridor_report.mjs` remain solely to reproduce earlier archived experiments under `data/corridors/`. No active app component imports the corridor model. Existing archived outputs and their hashes are preserved as historical records and do not describe the current interface.

## Reproduce the target coverage report

```sh
node scripts/build_projection_report.mjs
```

This uses the retained bundle without network requests. It writes `data/market/projection_report.json`, `projection_defaults.csv`, and `projection_gaps.csv`, covering every series at 90/180/365-day entry settings and the default compatible ensemble. Targets always use 365 days. The defaults CSV contains one row per stock. The report retains the three entry cases to verify target invariance. A dated directory under `data/projections/` contains the reports, input dataset and calculation source files with hashes. Earlier archives keep their original formula and are not rewritten.

At this cutoff all ten default series support a one-year target for each of the three reference windows (30 comparisons). Other selected models may be stale, lack future fiscal years, or lack a sufficient historical reference. Exact gaps remain in the report; the 30 default comparisons do not imply complete forecast history.

## Later market-data integration

No live feed is connected by this change. Current quotes remain retained daily closes. There is no simulated live price and no subscription purchase.

To compare later actual prices with a saved valuation target:

1. Save a dated projection run with its origin, full forecast snapshots, contributors, reference window, median/SD, normalization basis and dated target values. The current exports retain the model evidence needed to reproduce it.
2. Append observed market prices with exchange/listing identity, currency, exchange timestamp, time zone, session, latency/delay status, provider identity and split convention.
3. Plot observed prices against the saved valuation bands and target markers on their dates. Keep the tracked origin fixed; recomputing targets on each tick would replace the forecast being tracked.
4. Offer a separate refreshed projection using newly available earnings models. Make its new origin and changed inputs visible.

A quote feed can supply price movement. It cannot supply missing historical named-analyst estimates or future annual earnings targets. Provider entitlements must cover the actual listings: Nasdaq, Korea Exchange and Euronext Amsterdam. Feed selection and current subscription pricing remain a later task; no claim of a particular provider's coverage or price is made here.

## Verification

Calculation tests cover months 13–24, anniversaries, frozen information/freshness, missing intervals, NTM-only rejection, complete ensemble membership, aggregation order, splits, losses and exports. New checks verify identical future targets across entry windows for all ten real stocks, while entry valuations change. Browser checks cover single, overlay and combined target markers, seven-card invariance, entry readouts, old saved views, overview comparison, exports and mobile sizing. Browser checks also verify daily valuation curves, fixed multiples, all seven unchanged endpoints, historical P/E readouts, missing close/earnings handling, and band availability without a volatility sample. Calendar-day unit assertions verify the exact missing-coverage boundary. Entry-window checks cover complete projected curves in single, overlay and combined views. Calendar tests cover missing weekday prices, listing-specific records, historical cursor behavior after zoom and resize, touch, and unchanged future dates. Legacy corridor unit tests remain for archived research reproducibility. See the current delivery record for the latest test counts.
