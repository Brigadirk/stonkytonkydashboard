# Valuation strategy study protocol

Status: data preparation. No strategy returns, accuracy rankings or evidence of an investable edge have been published.

## Readiness first

The Data coverage tab and `data/market/backtest_readiness.json` assess each analyst/basis series separately over the five calendar years ending at the dataset cutoff. The diagnostic uses 180- and 365-calendar-day reference windows and a maximum model age of 180 days.

The report distinguishes sessions where both bands can be drawn, sessions with EPS on every retained price date in both reference windows, and sessions where those full windows also have verified forecast availability by each date. The latter requires at least a year of preceding prices. Calendar completeness remains unverified because the public price feed has not been checked against an independent exchange calendar.

The UI displays each company's series with the most drawable band sessions. This is a collection diagnostic. It must not become an ex-post analyst selection rule in a trading simulation. The export retains every series, including sparse and unusable ones. Sandisk's February 2025 standalone listing cannot supply a five-year history.

## Fixed first experiment

The following rules define a first candidate experiment before inspecting its returns. These are research choices, not recommended trades. Record the chosen series IDs and evaluation dates in a versioned configuration before running it. Run the same rules separately for each chosen series; do not select whichever analyst produces the best historical return.

1. Use the same dated EPS and currency-denominated price-band calculations as the app. At date t, use forecasts available by t and P/E observations strictly before t. Never apply today's EPS retrospectively.
2. Use the 180- and 365-day windows together, with median-centered sample-standard-deviation bands and the existing 180-day maximum forecast age. Require a complete reference window against independently audited price sessions for the principal study.
3. A candidate entry occurs when the closing share price is below the minus-one-standard-deviation implied price for both windows. A candidate exit occurs when it is above the plus-one-standard-deviation implied price for both windows. An omitted, non-positive lower band cannot generate an entry. Hold either the stock or cash, without leverage or shorting.
4. Determine the signal after the close and execute at the next verified trading session's close. Never fill at the same close that supplied the signal. Cancel a pending entry if the required data becomes invalid before execution.
5. Do not invent signals during missing or stale EPS periods. Keep marking an existing holding with observed prices, record each gap, and exclude intervals without a defensible price/execution record from the principal result. Disclose unresolved open positions at the endpoint.
6. Predeclare trading costs and report sensitivity at several fixed cost levels. Use a documented dividend and cash-return policy. The current price feed is split-adjusted and excludes dividends, so it cannot support a total-return claim by itself.
7. Compare against buy-and-hold over the identical dates and listing, with the identical dividend and cost conventions. Report trade count, exposure, drawdown and returns together. Do not equate a handful of trades with a reliable effect.

The user-facing chart remains freely configurable. Changing chart windows does not silently change this experiment's fixed configuration.

## Evidence still required

Most original public availability times are unverified. Exact-byte archived copies can establish conservative available-by bounds for individual reports; they do not prove the original publication instant. Strict calculations admit those reports only after the archive bound. Reconstructed report-date studies can be labelled exploratory, but cannot validate a point-in-time performance claim. The current universe was selected with present knowledge; any historical result must disclose that selection. Hold back future observations for a prospective check once the series and rules are fixed.

Analyst forecast accuracy is a separate question. It requires matching EPS definitions, exact fiscal periods, split units, fixed forecast horizons and sufficient independent issuer outcomes. A contemporaneous consensus benchmark is needed to assess whether an analyst improves on the market's estimate. More report pages and more chart coverage do not establish that result.

## Combined-view boundary

The interactive ensemble is a dated reconstruction of the selected compatible estimators. It records changes in membership and applies one vote per research firm. This UI does not replace the preregistered individual-series experiment above. A future ensemble strategy needs a fixed contributor/entry/exit policy and sufficient verified reference history before any returns are examined.
