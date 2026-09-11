# Local valuation dashboard

Implemented 10 September 2026 in `web/`. The app uses the ten-stock universe, retained daily prices and eligible original earnings models. It runs locally at http://127.0.0.1:5178. The browser makes no live market-data requests and contains no API credentials.

## Run it

From the project root:

```sh
./scripts/run_dashboard.sh
```

This validates and bundles the existing data, installs the locked frontend dependencies if needed, builds the app and starts a server bound to localhost. Stop it with Ctrl-C. Requirements: Python 3.12 and Node 22.12 or newer within a supported Vite version. To develop with live reload, use `npm run dev --prefix web` after building the dataset. Preview and development use the same port; stop one before starting the other.

The initial implementation uses React, TypeScript, Vite and Plotly. Plotly supplies zoom, reset and PNG export. Its [filled-area documentation](https://plotly.com/javascript/filled-area-plots/) and [configuration reference](https://plotly.com/javascript/configuration-options/) informed the chart. The [Vite guide](https://vite.dev/guide/) documents the build workflow. Public source collection remains Python and CSV, with originals retained separately.

## Simple stock view

Every visit starts in the simple view, including when previous research settings are saved. Each stock shows the last retained closing price, a dated one-year target and percentage change, and one price chart. The main price chart is 640 pixels tall and fits the vertical axis to the displayed prices, bands and targets instead of forcing a zero baseline. Move horizontally anywhere in the plot to see a vertical guide, an exact calendar-date label, that date's closing price and its forward P/E using the estimate eligible then. Historical dates without a recorded closing price are removed from the horizontal axis, including weekends, local holidays and missing price sessions. The historical cursor moves through recorded closes only. A day with a close but missing earnings remains visible and shows "Forward P/E unavailable". Future projection dates remain on the chart. Future dates show the selected projected valuation and its forward P/E, with the anniversary labelled as the one-year target. On touch screens, tap the chart to show the date and value. Chart history selects 6 months, 1, 2, 3 or 5 years of historical prices and their available valuation bands, with projected valuation bands extending to the one-year target markers. This display setting is shared with All stocks and Advanced and persists across reload. It does not change the entry comparison or future target calculation. Missing historical estimates leave gaps in the bands while retained prices remain visible. The 90/180/365-day buttons change only the entry comparison: historical bands and today's price premium or discount to usual valuation. Future targets use a separate 365-day valuation reference and stay unchanged when those buttons are clicked. The median and every ±1, ±1.5 and ±2 standard-deviation target appear together in a seven-target strip. Every level shows a price and percentage change, and all seven dated target markers remain on the chart. Clicking a deviation changes the highlighted future band and target. The deviation is measured from historical forward P/E. These scenarios do not imply probabilities or a predicted market path.

Advanced opens the full workspace described below. Simple view returns to the current stock (or stays on All stocks) without resetting calculation settings. In single or overlay mode the simple stock page shows the primary model; in combined mode it shows the selected ensemble. A custom window retained from Advanced is shown in days. The highlighted deviation stays in sync with Advanced and survives reload. Missing targets remain unavailable, with exact causes and original evidence in Advanced. Overlay choices, forecast-age limits, date, sources and ensemble settings remain saved; opening research controls is a separate, temporary interface choice.

Only This stock and All stocks are tabs in the simple workspace. Research tabs, source selectors, chart settings, extra charts, audit tables and exports are in Advanced. The All stocks comparison also stays at one window in simple mode, preserving the saved second-window preference for Advanced.

## What works

- All ten stocks have local daily price charts in their listing currencies.
- Editable rolling window from 20 to 2,192 calendar days; presets for 90, 180, 365, 730, 1,095 and 1,826 days.
- Median and independently toggleable ±1, ±1.5 and ±2 standard-deviation bands, on the share-price chart.
- Separate display ranges, historical as-of date, zoom, date inspection and chart-data CSV export.
- One-year-ahead price targets use the earnings expected during months 13–24 from the selected origin. Forecasts and historical reference multiples stay frozen at that origin. Daily projected valuation bands extend to the exact one-year target markers, rolling the earnings horizon forward while keeping the origin models and 365-day reference multiples fixed. Target earnings, model evidence and valuation inputs can be inspected and exported in Advanced.
- All stocks shows one row per company, switchable 90/180/365-day or custom reference windows, Low/Typical/High scenarios, targets, percentage changes and mini charts. Advanced contains side-by-side comparisons, exact sigma levels, sorting, model evidence and exports. See [projection calculations and tracking design](PROJECTIONS.md).
- An interactive company/month gap map distinguishes missing, stale, incomplete and nonpositive earnings from dates usable only in another selected author or accounting series. Row source selection, month inspection, recent/history navigation and CSV export are available.
- An EPS forecast/actual pilot uses initial issuer results and explicitly compatible reported diluted definitions at 90, 180 and 365 days before release. Excluded combinations and source links remain visible; no analyst ranking is claimed.
- Individual analyst, published-consensus and accounting-basis selection. Consensus is explicitly labelled and has no individual author. The default favors currently usable observations, then historical coverage, with adjusted diluted EPS as a tie-breaker. This is a usability rule, not an analyst ranking. Changing the chart window does not automatically switch the selected source.
- EPS history using the same model series, an original forecast table with citations, the existing revenue forecast-versus-actual pilot, and a ten-name coverage view.
- Model-age limits and a mode requiring verified availability. Retained provider timestamps and exact-byte archived copies can establish conservative availability bounds. Other printed-report assumptions remain excluded in this mode. Original publication instants are not inferred from archive captures.
- View preferences survive reload. View links include company, series, estimator mode, selected contributors, combination method, window, date, enabled bands, target sigma and overview comparison/sort settings.
- A validated import route for licensed NTM EPS exports, preserving the original CSV and optional named analyst/firm identity. Unnamed consensus cannot become an individual contributor.

No synthetic price or EPS series is shown in the app. Test fixtures live in the test files only.

## Estimator views

One estimator keeps the original single-series chart. Overlay estimators draws each selected estimator's EPS and price bands independently, with distinct colors. Headline cards and date details identify the primary series. The combined view first constructs the median or equal-weighted mean of compatible forward EPS on every historical date, then calculates historical P/E and price bands from that combined series. It does not average finished bands.

Select all compatible estimators or a subset. Reported diluted EPS, firm-specific adjusted definitions and unresolved definitions have separate compatibility groups. The app checks currency, fiscal periods and share normalization. It permits at most one contribution per analyst and per research firm on each date, using the latest eligible model to avoid double-counting coauthors and author handovers. Published consensus is available as its own overlay but is excluded from analyst ensembles.

The combined audit shows each included model and original source, model/report ages, exclusions, EPS disagreement and membership entry/exit dates. Purple diamonds mark membership changes on the price chart. Analyst EPS disagreement is not the historical P/E standard deviation used for valuation bands. A single eligible contributor is labelled explicitly; no dispersion claim follows from it. CSV exports preserve the composition and sources, including a separate contributor/exclusion export.

The simplified All stocks table shows observed closes, one-year targets, percentage changes and charts. Advanced contains selected model dates, ages and reference counts. Sorting by projected upside compares scenario price changes; it is unrelated to analyst accuracy. The EPS outcome view summarizes errors separately by analyst, definition and horizon, with independent fiscal-year counts and no accuracy ranking.

## Calculation definition

For trading date t, take the newest eligible snapshot in the selected series that was available by t. Public report snapshots enter on the calendar day after the printed report date. This is a reconstruction assumption, not proof of first historical publication. Estimate age starts at the model date when one is printed, otherwise the report date. Reprints do not reset model age or roll the selected numerical model backwards. Mutable public pages captured for the first time have a separate collection timestamp and unknown numerical revision date; their age limit measures time since capture and they are never backdated. Strict mode instead selects only models whose verified availability bound has been reached, preserving a still-fresh verified model while newer unverified reports remain excluded.

The annual-model NTM proxy allocates the next twelve calendar months across exact fiscal years. A fiscal year's contribution is its EPS multiplied by the number of overlapping forecast days divided by that fiscal year's total days. This assumes earnings accrue uniformly within each fiscal year. Leap years and 53-week years use their actual lengths. The next twelve months begin the day after t; a February 29 anniversary ends on February 28 of the next year. Missing or overlapping fiscal periods produce a gap. All required targets come from the same model snapshot.

Provider NTM imports already contain a forward twelve-month EPS measure. The app uses the supplied snapshot and its estimate date, without relabelling a current estimate as historical. Users must confirm the provider's horizon and accounting method before importing.

Prices use split-adjusted close, excluding cash-dividend adjustment. EPS is divided by the product of subsequent split ratios through the dataset cutoff. The raw forecast table retains EPS as printed. The expanded U.S. archive includes models before and after the relevant splits. Original table values and model dates establish their share basis; a reprint crossing a split is excluded unless an explicit share-basis date resolves it. Korean share-denominator questions remain explicitly unresolved. Future imports must supply the actual share-basis date, rather than assume that the publication date always establishes it.

For each day, forward P/E = price / forward EPS. A non-positive EPS remains visible in the earnings series but has no P/E. Positive EPS of at most 0.01 USD/EUR or 1 KRW is also retained but excluded from P/E as a near-zero denominator; this is an explicit display stability threshold, not an analyst filter. An unavailable, stale or currency-incompatible estimate also produces a gap. The P/E reference distribution consists only of valid daily multiples in `[t − window, t)`. Today is excluded. At least 20 valid prior observations are required; the usable count and total observed prior sessions are shown. Missing provider price bars are omitted and documented separately, rather than counted as exchange trading sessions.

The main graph shows historical and one-year-ahead scenario prices in the listing currency. Its headline cards now show one-year targets; historical date details retain the contemporaneous valuation. Saved settings or old links requesting a multiple-axis view now open the price view. For example, price 300 at 18× implies EPS 16.6667; historical multiples of 20× and 35× imply prices 333.33 and 583.33. Each past date uses its own available earnings snapshot, so a later revision does not rewrite the original forecast.

The center is the median historical P/E. Sample standard deviation uses the ordinary mean and n−1 denominator. Price-band edges are:

```text
forward_EPS(t) × [median_prior_PE(t) ± k × sample_std_prior_PE(t)]
k = 1, 1.5, 2
```

Negative or zero band edges are omitted. Each shaded polygon ends at a gap. The percentile gives half weight to ties; distance from the median divides by sample standard deviation and is unavailable when it is zero. Daily multiples are correlated and their distribution need not be normal. These bands are descriptive ranges, not confidence intervals or probabilities of a future price.

The NTM curve moves as the horizon rolls as well as when forecasts change. It is not labelled a pure analyst-revision series. The app makes no stock recommendations, analyst accuracy ranks or backtested trading-return claims.

## Rebuild and refresh

Rebuild reviewed inputs and preserve dated before/after archives:

```sh
python3 scripts/refresh_dashboard.py
```

Add `--prices` to download current public closes, or `--replay-prices` to reuse the latest retained downloads. Add `--discover-days 7` to check recent public report URLs; newly discovered PDFs await review before any EPS enters the chart. See [the refresh guide](REFRESH.md) for cutoff handling, archives, rollback and logs.

The current dataset cutoff is 10 September 2026. Refreshing prices does not create missing historical EPS. No scheduler is installed.

The Data coverage tab includes a [backtest-readiness report](BACKTEST_PROTOCOL.md) for each analyst/basis series. It separates drawable bands, complete 180/365-day reference windows and verified availability by each historical date. Every series can be exported. The initial strategy protocol is fixed in the document; no historical trading returns are claimed.

## Import licensed NTM estimates

Use [ntm_import_template.csv](../data/market/ntm_import_template.csv). Required fields:

| Field | Meaning |
| --- | --- |
| `company_id` | A canonical ID from `data/universe.csv` |
| `series_id`, `label` | Stable provider/consensus or analyst series identity and display name |
| `available_at` | Provider's actual availability timestamp with explicit timezone |
| `estimate_date` | Original estimate date, used for staleness |
| `eps`, `currency` | Finite NTM EPS and the selected listing's currency |
| `accounting_basis` | Consistent adjusted/reported and diluted/basic definition |
| `share_basis_date` | Date identifying the actual split basis of the imported EPS |
| `source_url`, `source_reference` | Provider source and a traceable original record ID |

Validate the provider's historical-availability promise before importing. The parser checks structure, currency, timestamp ordering, finite values, duplicates and constant series metadata. It cannot establish a provider's historical methodology from numbers alone. Supplied provider timestamps are trusted as `verified_available_at`; they become usable the following UTC calendar day, conservatively excluding same-day closes. Negative EPS is retained.

```sh
python3 scripts/import_ntm.py /absolute/path/to/licensed-export.csv
python3 scripts/refresh_dashboard.py
```

Each import preserves its original and validated JSON under `data/market/imports/<sha256>/`. `imported_ntm.json` selects the active imported dataset, so a subsequent import replaces the active selection while preserving old archives. Include the complete desired imported history in each file. Imports remain separate from the public broker series. An API adapter can supply this same contract once a provider and entitlement are known.

## Verification

```sh
python3 -m unittest discover -s tests -v
npm run test --prefix web
npm run build --prefix web
npm run test:browser --prefix web
```

The frontend tests cover median/sample deviation, calendar windows, exclusion of the current day, model staleness, split consistency, negative EPS, dividend/currency rejection, leap years, 53-week fiscal years, incomplete new snapshots, as-of cutoffs and resistance to later forecasts. A real-data replay records coverage in [dashboard_validation.json](../data/market/dashboard_validation.json). Browser checks exercise all ten stocks, controls, tabs, strict-mode gaps, export, saved settings and a 390-pixel viewport. Python tests cover archive integrity, cutoff selection, imported estimates, consensus attribution, fiscal calendars, scoped EPS-basis aliases and reprints crossing splits.

Browser tests require Chromium installed for Playwright. If absent, run `npm exec --prefix web -- playwright install chromium`. No browser extension, market account or scraping credit is required to run the retained dataset.

## Expanded public archive

The [round 4 collection](research/ROUND4_PROGRESS.md) adds earlier and fresh models across the universe. Individual analyst histories remain separate across author changes. Matching Korean summary and detailed tables justify a small set of aliases within the same broker, author and company; original labels and evidence remain in the data. Legacy Morningstar diluted EPS with unresolved adjustments stays separate from explicit reported and adjusted diluted EPS. NVIDIA adjusted-model views display the documented FY2027 accounting-comparability issue.

## Gap-map and evaluation methods

The monthly map counts observed price dates in a selected series. The five-year interval and as-of cutoff limit the first and last months. “Other series only” means a usable positive EPS estimate exists elsewhere in the archive; it is not silently joined to the selected analyst or accounting definition. A usable EPS date can still lack bands if fewer than 20 valid prior multiples exist. The gap map exports all monthly counts and reasons. `scripts/build_gap_map.mjs` also records collection targets in `data/market/collection_targets.json`.

The EPS pilot uses the newest compatible forecast published before each fixed cutoff, and excludes models older than 90 calendar days at that cutoff. It normalizes both forecast and initial actual EPS for subsequent splits through the data cutoff. Forecast and actual must have the same issuer fiscal-year end, currency and explicit reported diluted definition. Percentage errors divide by the absolute actual EPS; when actual EPS is within 0.01 of zero, the absolute currency error remains while percentage error is unavailable. Non-GAAP issuer actuals are retained for reconciliation but are not assumed equivalent to Morningstar adjusted EPS.

Apple uses NASDAQ AAPL in USD, with a fiscal year ending the last Saturday of September. Its 2020 split predates the retained price window. Adding Apple preserves the previous eight companies' price rows. Use `python3 scripts/collect_prices.py --companies apple` for a targeted refresh at the existing start and cutoff; an incompatible partial-refresh date range is rejected.

## BESI

BESI uses ordinary shares listed in Amsterdam, EUR prices and forecasts, and fiscal years ending December31. The default current earnings series is Hildo Laman at IEX, published April23,2026, with FY2026–28 forecasts. Morningstar models and LSEG/Bloomberg consensus remain separate. [Coverage, original sources and exclusions](research/BESI_ADDITION.md) explain the partial history and unspecified EPS adjustment/dilution policies.
