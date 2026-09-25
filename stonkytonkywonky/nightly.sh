#!/usr/bin/env bash
# Nightly: record consensus, re-screen the list, refresh the web app's data.
set -euo pipefail
cd "$(dirname "$0")"
./record.py || echo "record.py: some tickers failed; screening what we have"
# Weekly: pull new earnings reports (trailing EPS) and refresh reconstruction B.
if [ "$(date +%u)" = 5 ]; then
    ./backfill.py > data/history/backfill.log 2>&1 || echo "backfill.py failed; keeping last week's history"
fi
# Analyst reports: fetch new ones (Morningstar via Firstrade, Korean brokers via
# Telegram), then extract anything dropped into analysts/inbox/.
(cd analysts && ./collect.py) || echo "collect.py failed; keeping earlier analyst data"
(cd analysts && ./extract.py) || echo "extract.py: some inbox PDFs failed; see analysts/failed/"
python3 "$HOME/.codex/skills/stock-research/scripts/forward_screen.py" --all --allow-biased --out "$PWD/data/screen" || true
./export_app.py
