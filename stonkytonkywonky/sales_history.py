#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance", "pandas"]
# ///
"""Daily trailing price-to-sales history for companies without profits.

Loss-makers have no P/E, so the app values them on sales. Forward revenue
estimates have no free history, so the history here is trailing: each day's
market cap over the last twelve months of *reported* revenue known by then.

    revenue  SEC XBRL annual revenue (10-K/20-F) plus Yahoo's last quarters;
             a period counts only from its end + REPORT_LAG days (no look-ahead)
    shares   Yahoo's share-count history, smoothed with a three-quarter median
             (it has one-quarter glitches) and scaled so today's count matches
             the tickers.csv override when there is one
    FX       daily, when revenue and price currencies differ (XPEV: CNY vs USD)

    data/history/ps/TICKER.csv   date, close, ttm_rev_ps (per share, quote ccy), ttm_ps

    ./sales_history.py            every ticker with negative NTM EPS today
    ./sales_history.py XPEV       named tickers
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "history" / "ps"
START = "2019-01-01"
REPORT_LAG = timedelta(days=75)
SEC_UA = "StonkyTonkyWonky research tool"
SEC_CONCEPTS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet")


def num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def latest_snapshot() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with open(ROOT / "data" / "snapshots.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["ticker"]] = r
    return rows


def sec_cik(ticker: str) -> str | None:
    req = urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": SEC_UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    hit = next((v for v in data.values() if v["ticker"].upper() == ticker.upper()), None)
    return f"{hit['cik_str']:010d}" if hit else None


def sec_annual_revenue(ticker: str) -> dict[date, float]:
    """Fiscal-year revenue by year end, from 10-K/20-F XBRL (foreign issuers file annual only)."""
    cik = sec_cik(ticker)
    if not cik:
        return {}
    out: dict[date, float] = {}
    for concept in SEC_CONCEPTS:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": SEC_UA}), timeout=30) as r:
                units = json.load(r)["units"]
        except Exception:  # noqa: BLE001 — concept not used by this filer
            continue
        for ccy, facts in units.items():
            for f in facts:
                if f.get("form") not in ("10-K", "20-F") or not f.get("start"):
                    continue
                start, end = date.fromisoformat(f["start"]), date.fromisoformat(f["end"])
                if 350 <= (end - start).days <= 380:
                    out[end] = (float(f["val"]), ccy)
        time.sleep(0.2)
    return out


def ttm_points(ticker: str) -> list[tuple[date, float, str]]:
    """(known-from date, trailing-twelve-month revenue, currency), oldest first."""
    points: dict[date, tuple[float, str]] = {}
    for end, (val, ccy) in sec_annual_revenue(ticker).items():
        points[end] = (val, ccy)
    t = yf.Ticker(ticker)
    q = t.quarterly_income_stmt
    ccy = (t.info or {}).get("financialCurrency") or ""
    if q is not None and "Total Revenue" in q.index:
        rev = q.loc["Total Revenue"].dropna().sort_index()
        for i in range(3, len(rev)):
            window = rev.iloc[i - 3:i + 1]
            if (window.index[-1] - window.index[0]).days <= 300:  # four consecutive quarters
                points[window.index[-1].date()] = (float(window.sum()), ccy)
    return sorted((end + REPORT_LAG, v, c) for end, (v, c) in points.items())


def share_history(ticker: str, today_count: float | None) -> pd.Series:
    s = yf.Ticker(ticker).get_shares_full(start=START)
    s = s[~s.index.duplicated()]
    s.index = s.index.tz_localize(None)
    q = s.resample("QE").last().dropna().rolling(3, center=True, min_periods=1).median()
    if today_count and len(q):
        q = q * (today_count / float(q.iloc[-1]))
    return q


def override_shares(ticker: str) -> float | None:
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        return next((num(r.get("shares")) for r in csv.DictReader(fh) if r["ticker"] == ticker), None)


def fx_history(src: str, dst: str) -> pd.Series | None:
    if not src or src == dst:
        return None
    h = yf.Ticker(f"{src}{dst}=X").history(start=START)["Close"].dropna()
    h.index = h.index.tz_localize(None)
    return h


def build(ticker: str, snap: dict) -> pd.DataFrame:
    quote_ccy = snap.get("currency") or ""
    ttm = ttm_points(ticker)
    if not ttm:
        raise RuntimeError("no revenue history")
    close = yf.Ticker(ticker).history(start=START, auto_adjust=False)["Close"].dropna()
    close.index = close.index.tz_localize(None)
    shares = share_history(ticker, num(snap.get("shares")) or override_shares(ticker))
    fx = fx_history(ttm[-1][2], quote_ccy)

    rows = []
    for ts, px in close.items():
        day = ts.date()
        known = [p for p in ttm if p[0] <= day]
        if not known:
            continue
        _, rev, _ = known[-1]
        sh = shares[shares.index <= ts]
        if sh.empty:
            continue
        rate = 1.0 if fx is None else (float(fx[fx.index <= ts].iloc[-1]) if (fx.index <= ts).any() else None)
        if rate is None:
            continue
        per_share = rev * rate / float(sh.iloc[-1])
        rows.append({"date": day.isoformat(), "close": round(float(px), 4),
                     "ttm_rev_ps": round(per_share, 6), "ttm_ps": round(px / per_share, 4)})
    return pd.DataFrame(rows)


def main(argv: list[str]) -> int:
    snaps = latest_snapshot()
    tickers = argv or [t for t, s in snaps.items()
                       if num(s.get("ntm_eps")) is not None and num(s.get("ntm_eps")) <= 0]
    OUT.mkdir(parents=True, exist_ok=True)
    for t in tickers:
        try:
            df = build(t, snaps.get(t) or {})
            df.to_csv(OUT / f"{t}.csv", index=False)
            last = df.iloc[-1]
            print(f"{t:<7} {len(df)} days from {df['date'].iloc[0]}; today TTM P/S {last['ttm_ps']:.2f}", flush=True)
        except Exception as exc:  # noqa: BLE001 — one ticker must not stop the rest
            print(f"{t:<7} FAILED {exc}", flush=True)
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
