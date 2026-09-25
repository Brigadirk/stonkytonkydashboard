#!/usr/bin/env python3
"""Map US-listed tickers to Morningstar security IDs (0P...), for the Firstrade collector.

A stock's public quote page on morningstar.com (allowed by its robots.txt;
/api and /search are not) names the stock's own ID three times and unrelated
IDs once each, so the most frequent ID with at least three mentions wins.

    analysts/morningstar_ids.csv   ticker, exchange, morningstar_id
"""

from __future__ import annotations

import collections
import csv
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "morningstar_ids.csv"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
EXCHANGES = ("xnas", "xnys")
# Morningstar answers 202 (a bot challenge) to bursts; one page every ~50s gets through.
PAUSE = 50
BLOCKED_WAIT = 900


class Blocked(Exception):
    pass


def lookup(ticker: str) -> tuple[str, str] | None:
    for ex in EXCHANGES:
        url = f"https://www.morningstar.com/stocks/{ex}/{ticker.lower()}/quote"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                if r.status == 202:
                    raise Blocked()
                page = r.read().decode("utf-8", "replace")
        except Blocked:
            raise
        except Exception:  # noqa: BLE001 — a missing page just means "not on this exchange"
            time.sleep(PAUSE)
            continue
        counts = collections.Counter(re.findall(r"0P0000[A-Z0-9]{4}", page))
        if counts:
            best, n = counts.most_common(1)[0]
            if n >= 3:
                return ex, best
        time.sleep(PAUSE)
    return None


def main(argv: list[str]) -> int:
    known = {}
    if OUT.exists():
        with open(OUT, newline="", encoding="utf-8") as fh:
            known = {r["ticker"]: r for r in csv.DictReader(fh)}
    with open(ROOT.parent / "tickers.csv", newline="", encoding="utf-8") as fh:
        us = [r["ticker"] for r in csv.DictReader(fh) if "." not in r["ticker"]]
    todo = [t for t in (argv or us) if t not in known]
    for t in todo:
        try:
            hit = lookup(t)
        except Blocked:
            print(f"{t}: Morningstar answered 202; waiting {BLOCKED_WAIT}s", flush=True)
            time.sleep(BLOCKED_WAIT)
            continue  # retried on the next run
        known[t] = {"ticker": t, "exchange": hit[0] if hit else "", "morningstar_id": hit[1] if hit else ""}
        print(f"{t:<6} {known[t]['exchange']:<5} {known[t]['morningstar_id'] or 'not found'}", flush=True)
        write(known)  # save as we go: a run takes hours
        time.sleep(PAUSE)
    return 0


def write(known: dict) -> None:
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["ticker", "exchange", "morningstar_id"])
        w.writeheader()
        for t in sorted(known):
            w.writerow(known[t])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
