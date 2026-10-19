#!/usr/bin/env bash
# Nightly: record consensus, re-screen the list, refresh the web app's data.
set -euo pipefail
cd "$(dirname "$0")"
./record.py || echo "record.py: some tickers failed; screening what we have"
# Weekly: pull new earnings reports (trailing EPS) and refresh reconstruction B.
if [ "$(date +%u)" = 5 ]; then
    ./backfill.py > data/history/backfill.log 2>&1 || echo "backfill.py failed; keeping last week's history"
fi
# Loss-makers are valued on sales: refresh their trailing P/S history.
./sales_history.py > data/history/sales_history.log 2>&1 || echo "sales_history.py failed; keeping earlier P/S history"
# Analyst reports: fetch new ones (Morningstar via Firstrade, Korean brokers via
# Telegram), then extract anything dropped into analysts/inbox/.
(cd analysts && ./collect.py) || echo "collect.py failed; keeping earlier analyst data"
(cd analysts && ./extract.py) || echo "extract.py: some inbox PDFs failed; see analysts/failed/"
# Market breadth: NYSE McClellan Summation Index for the app's breadth view.
./breadth.py || echo "breadth.py failed; keeping earlier breadth data"
# Horizon: dated catalysts and event probabilities for the app's horizon view.
./horizon.py || echo "horizon.py failed; keeping earlier horizon data"
# Positioning: PositioningLab collects the free sources, then exports the app's positioning view.
# collect-public exits 2 when one source fails; the export still uses everything that arrived.
(cd ../PositioningLab && /home/dirk/.local/bin/uv run --quiet positioning collect-public --days 10 > data/collect.log 2>&1 || true;
 /home/dirk/.local/bin/uv run --quiet positioning export-app --out "$OLDPWD/app/public/data/positioning.json") || echo "positioning export failed; keeping earlier positioning data"
python3 "$HOME/.codex/skills/stock-research/scripts/forward_screen.py" --all --allow-biased --out "$PWD/data/screen" || true
./export_app.py
