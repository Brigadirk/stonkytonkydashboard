#!/usr/bin/env bash
# Nightly: record consensus, re-screen the list, refresh the web app's data.
set -euo pipefail
cd "$(dirname "$0")"
./record.py || echo "record.py: some tickers failed; screening what we have"
# Weekly: pull new earnings reports (trailing EPS) and refresh reconstruction B.
if [ "$(date +%u)" = 5 ]; then
    ./backfill.py > data/history/backfill.log 2>&1 || echo "backfill.py failed; keeping last week's history"
else
    # Tickers added since the last Friday get their history tonight instead of waiting.
    new=$(tail -n +2 tickers.csv | cut -d, -f1 | while read -r t; do [ -f "data/history/ntm_b/$t.csv" ] || echo "$t"; done)
    [ -z "$new" ] || ./backfill.py $new > data/history/backfill_new.log 2>&1 || echo "backfill.py failed for new tickers"
fi
# Loss-makers are valued on sales: refresh their trailing P/S history.
./sales_history.py > data/history/sales_history.log 2>&1 || echo "sales_history.py failed; keeping earlier P/S history"
# Analyst reports: fetch new ones (Morningstar via Firstrade, Korean brokers via
# Telegram), then extract anything dropped into analysts/inbox/.
(cd analysts && ./collect.py) || echo "collect.py failed; keeping earlier analyst data"
(cd analysts && ./extract.py) || echo "extract.py: some inbox PDFs failed; see analysts/failed/"
# Market breadth: NYSE McClellan Summation Index for the app's breadth view.
./breadth.py || echo "breadth.py failed; keeping earlier breadth data"
# New 52-week highs and lows across the S&P 1500, with the since-1991 buy-signal study.
./highlow.py > data/highlow/highlow.log 2>&1 || echo "highlow.py failed; keeping earlier highs and lows data"
# Horizon: dated catalysts and event probabilities for the app's horizon view.
./horizon.py || echo "horizon.py failed; keeping earlier horizon data"
# Markets: indexes, rates, credit, FX, commodities and crypto for the app's markets view.
./markets.py > data/markets.log 2>&1 || echo "markets.py failed; keeping earlier market data"
# Industry: oil shipping through the chokepoints, memory spot prices, GPU rental prices.
./industry.py > data/industry/industry.log 2>&1 || echo "industry.py failed; keeping earlier industry data"
# AI demand: OpenRouter tokens by model maker, hyperscaler capex and backlog (SEC), disclosed figures.
./compute.py > data/compute/compute.log 2>&1 || echo "compute.py failed; keeping earlier AI demand data"
# Discounts: holding companies against their stakes, preferred against common shares.
./discounts.py > data/discounts.log 2>&1 || echo "discounts.py failed; keeping earlier discount data"
# Korean retail margin loans and deposits (KOFIA) for the positioning view.
./korea_margin.py > data/korea/korea_margin.log 2>&1 || echo "korea_margin.py failed; keeping earlier Korean margin data"
# Positioning: PositioningLab collects the free sources, then exports the app's positioning view.
# collect-public exits 2 when one source fails; the export still uses everything that arrived.
(cd ../PositioningLab && /home/dirk/.local/bin/uv run --quiet positioning collect-public --days 10 > data/collect.log 2>&1 || true;
 /home/dirk/.local/bin/uv run --quiet positioning export-app --out "$OLDPWD/app/public/data/positioning.json") || echo "positioning export failed; keeping earlier positioning data"
python3 "$HOME/.codex/skills/stock-research/scripts/forward_screen.py" --all --allow-biased --out "$PWD/data/screen" || true
# Balance sheet and cash flow for EV/FCF and P/B; each ticker is refreshed once a week.
./fundamentals.py > data/fundamentals.log 2>&1 || echo "fundamentals.py failed; keeping earlier statement data"
# Third-year EPS forecasts Yahoo and Nasdaq lack (Eastmoney for Shanghai/Shenzhen listings).
./extra_forecasts.py > data/extra_forecasts.log 2>&1 || echo "extra_forecasts.py failed; keeping earlier forecasts"
./export_app.py
