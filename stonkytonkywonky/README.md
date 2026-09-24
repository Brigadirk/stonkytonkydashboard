# StonkyTonkyWonky

A cheap-to-self screen for 164 stocks: the 89 names from the Protocol v2 research library plus the Nasdaq-100. It runs separately from the ten-stock dashboard in `web/` and uses consensus estimates instead of individual broker reports.

For each stock, the app shows:

- forward P/E against the stock's own history over windows from 90 days to 5 years, as seven zones from extremely cheap to extremely expensive (levels at −2, −1.5, −1, median, +1, +1.5 and +2σ, read off each window's percentiles);
- a price chart with those valuation bands, projected one year ahead on next fiscal year's consensus;
- whether analysts are raising or cutting next year's forecast (90-day path);
- trailing P/E and expected growth on the same adjusted basis as the forecasts;
- a combined score ranking every stock on low forward P/E, growth, forecast revisions and return to its typical valuation.

## Pipeline

`nightly.sh` runs on weekdays at 23:30 through the systemd user timer in `systemd/`:

1. `record.py` records each ticker's consensus (yfinance, plus Nasdaq for US names) as point-in-time history. This is the only genuine estimate history; it starts on 2026-09-24.
2. On Fridays, `backfill.py` reconstructs older history ("method B"): each future quarter valued at its pre-report consensus. This carries look-ahead. Each ticker is graded good, caution or biased against Yahoo's sparse genuine forward P/E points, and the app says how far to trust it.
3. `screen/forward_screen.py --all --allow-biased` computes the percentile signals and walk-forward tests. This is a copy of the `stock-research` skill's script, and the skill's copy is the source of truth.
4. `export_app.py` writes the app's JSON, including per-window percentile levels from the full daily series.

`tickers.csv` lists the universe. The `estimates_from` column points one share class at another's consensus (Samsung preferred uses the common's).

## Running the app

```sh
cd app
npm install
npm run build
npm run preview
```

The app reads `app/public/data/`, which `export_app.py` generates. Recorded data (`data/`), the generated app data, `node_modules` and `dist` are not in Git.
