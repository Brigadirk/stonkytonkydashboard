#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance"]
# ///
"""Record today's consensus forward EPS for every ticker in tickers.csv.

Point-in-time history cannot be bought back later for free, so this runs daily
and keeps both the raw payloads and a flat CSV row per ticker per day.

    data/raw/YYYY-MM-DD.jsonl.gz   everything fetched, for recomputation
    data/daily/YYYY-MM-DD.csv      one row per ticker
    data/snapshots.csv             all daily files concatenated

Rerunning on the same day overwrites that day's files.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
NASDAQ_FORECAST = "https://api.nasdaq.com/api/analyst/{symbol}/earnings-forecast"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
FIELDS = [
    "date", "ticker", "name", "currency", "price", "price_time", "eps_currency", "fx",
    "fy0_end", "fy0_eps", "fy1_eps", "fy0_weight", "ntm_eps", "ntm_pe",
    "fy0_analysts", "fy1_analysts", "q0_eps", "q1_eps",
    "fy1_eps_30d_ago", "fy1_eps_90d_ago", "fy1_up_30d", "fy1_down_30d",
    "yahoo_forward_eps", "yahoo_forward_pe",
    "nasdaq_ntm_eps", "nasdaq_ntm_pe", "error", "ntm_method",
    "trailing_eps", "trailing_pe",
]
INFO_KEYS = [
    "currency", "financialCurrency", "regularMarketPrice", "currentPrice",
    "regularMarketTime", "forwardEps", "forwardPE", "trailingEps", "trailingPE",
    "lastFiscalYearEnd", "nextFiscalYearEnd", "mostRecentQuarter",
    "sharesOutstanding", "numberOfAnalystOpinions", "longName", "quoteType",
]


def num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def frame_to_dict(df) -> dict | None:
    if df is None or getattr(df, "empty", True):
        return None
    return json.loads(df.to_json(orient="index"))


def cell(table: dict | None, period: str, col: str) -> float | None:
    if not table:
        return None
    return num((table.get(period) or {}).get(col))


def retry(fn, attempts: int = 3, pause: float = 5.0):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(pause * (i + 1))


def fetch_nasdaq(ticker: str) -> dict | None:
    if "." in ticker:
        return None
    req = urllib.request.Request(
        NASDAQ_FORECAST.format(symbol=ticker.lower()),
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return (json.load(resp) or {}).get("data")
    except Exception:
        return None


def nasdaq_ntm(data: dict | None) -> float | None:
    rows = ((data or {}).get("quarterlyForecast") or {}).get("rows") or []
    eps = [num(r.get("consensusEPSForecast")) for r in rows[:4]]
    if len(eps) < 4 or any(v is None for v in eps):
        return None
    return sum(eps)  # type: ignore[arg-type]


def blend_ntm(today: date, fy0_end: date | None, fy0: float | None, fy1: float | None):
    """Time-weighted blend of the current and next fiscal year, the usual NTM proxy."""
    if fy0 is None or fy1 is None or fy0_end is None:
        return None, None
    w0 = max(0.0, min(1.0, (fy0_end - today).days / 365.25))
    return w0 * fy0 + (1 - w0) * fy1, w0


def estimate_currency(trend: dict | None) -> str | None:
    found = {v.get("currency") for v in (trend or {}).values()} - {None}
    return found.pop() if len(found) == 1 else None


def fx_rate(src: str, dst: str) -> float:
    """Spot rate to turn an estimate in src into the quote currency dst."""
    hist = retry(lambda: yf.Ticker(f"{src}{dst}=X").history(period="5d"))
    rate = num(hist["Close"].dropna().iloc[-1]) if not hist.empty else None
    if not rate:
        raise RuntimeError(f"no FX rate {src}{dst}")
    return rate


def record_one(ticker: str, name: str, today: date, estimates_from: str = "") -> tuple[dict, dict]:
    """`estimates_from` points a share class at its main line's consensus (Samsung pref
    uses the common's: same company, same profit per share, only the price differs)."""
    t = yf.Ticker(ticker)
    info = retry(lambda: t.info) or {}
    src = yf.Ticker(estimates_from) if estimates_from else t
    src_info = (retry(lambda: src.info) or {}) if estimates_from else info
    estimate = frame_to_dict(retry(lambda: src.earnings_estimate))
    trend = frame_to_dict(retry(lambda: src.eps_trend))
    revisions = frame_to_dict(retry(lambda: src.eps_revisions))
    nasdaq = fetch_nasdaq(estimates_from or ticker)

    raw = {
        "ticker": ticker,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "info": {k: info.get(k) for k in INFO_KEYS},
        "earnings_estimate": estimate,
        "eps_trend": trend,
        "eps_revisions": revisions,
        "nasdaq_forecast": nasdaq,
        "estimates_from": estimates_from or None,
    }

    price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice"))
    quote_ccy = info.get("currency")
    eps_ccy = estimate_currency(trend) or quote_ccy
    # ADRs and cross-listings can quote in one currency and estimate in another.
    fx = 1.0 if eps_ccy == quote_ccy else fx_rate(eps_ccy, quote_ccy)
    raw["fx"] = {"eps_currency": eps_ccy, "quote_currency": quote_ccy, "rate": fx}

    def conv(v: float | None) -> float | None:
        return None if v is None else v * fx

    fy0_ts = src_info.get("nextFiscalYearEnd")
    fy0_end = datetime.fromtimestamp(fy0_ts, timezone.utc).date() if fy0_ts else None
    fy0 = conv(cell(estimate, "0y", "avg"))
    fy1 = conv(cell(estimate, "+1y", "avg"))
    ntm, w0 = blend_ntm(today, fy0_end, fy0, fy1)
    method = "blend" if ntm is not None else None
    if ntm is None and fy0 is None and fy1 is not None:
        # Yahoo sometimes leaves the current year empty just after a fiscal year end.
        ntm, method = fy1, "fy1_only"
    n_ntm = nasdaq_ntm(nasdaq)
    mkt_ts = info.get("regularMarketTime")

    row = {
        "date": today.isoformat(),
        "ticker": ticker,
        "name": name,
        "currency": quote_ccy,
        "price": price,
        "eps_currency": eps_ccy,
        "fx": fx,
        "price_time": (
            datetime.fromtimestamp(mkt_ts, timezone.utc).isoformat(timespec="minutes")
            if isinstance(mkt_ts, (int, float)) else None
        ),
        "fy0_end": fy0_end.isoformat() if fy0_end else None,
        "fy0_eps": fy0,
        "fy1_eps": fy1,
        "fy0_weight": None if w0 is None else round(w0, 4),
        "ntm_eps": ntm,
        "ntm_pe": price / ntm if price and ntm and ntm > 0 else None,
        "fy0_analysts": cell(estimate, "0y", "numberOfAnalysts"),
        "fy1_analysts": cell(estimate, "+1y", "numberOfAnalysts"),
        "q0_eps": conv(cell(estimate, "0q", "avg")),
        "q1_eps": conv(cell(estimate, "+1q", "avg")),
        "fy1_eps_30d_ago": conv(cell(trend, "+1y", "30daysAgo")),
        "fy1_eps_90d_ago": conv(cell(trend, "+1y", "90daysAgo")),
        "fy1_up_30d": cell(revisions, "+1y", "upLast30days"),
        "fy1_down_30d": cell(revisions, "+1y", "downLast30days"),
        "yahoo_forward_eps": num(info.get("forwardEps")),
        "yahoo_forward_pe": num(info.get("forwardPE")),
        "nasdaq_ntm_eps": n_ntm,
        "nasdaq_ntm_pe": price / n_ntm if price and n_ntm and n_ntm > 0 else None,
        "error": None if ntm is not None else "no NTM: missing FY estimates or fiscal year end",
        "ntm_method": method,
        # Yahoo's own trailing figures; trailingPE is absent when TTM EPS is negative.
        "trailing_eps": num(info.get("trailingEps")),
        "trailing_pe": num(info.get("trailingPE")),
    }
    return row, raw


def load_tickers() -> list[tuple[str, str, str]]:
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        return [
            (r["ticker"].strip(), r["name"].strip(), (r.get("estimates_from") or "").strip())
            for r in csv.DictReader(fh) if r["ticker"].strip()
        ]


def rebuild_snapshots() -> None:
    daily = sorted((DATA / "daily").glob("*.csv"))
    with open(DATA / "snapshots.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        for path in daily:
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    writer.writerow({k: r.get(k) for k in FIELDS})


def main(argv: list[str]) -> int:
    today = date.today()
    only = {a.upper() for a in argv}
    tickers = [(t, n, e) for t, n, e in load_tickers() if not only or t.upper() in only]
    (DATA / "raw").mkdir(parents=True, exist_ok=True)
    (DATA / "daily").mkdir(parents=True, exist_ok=True)

    rows, raws, failed = [], [], 0
    for ticker, name, estimates_from in tickers:
        try:
            row, raw = record_one(ticker, name, today, estimates_from)
        except Exception as exc:  # noqa: BLE001 — one bad ticker must not lose the day
            row = {k: None for k in FIELDS} | {
                "date": today.isoformat(), "ticker": ticker, "name": name, "error": repr(exc)[:300],
            }
            raw = {"ticker": ticker, "error": repr(exc)}
        if row["error"]:
            failed += 1
        rows.append(row)
        raws.append(raw)
        print(f"{ticker:<11} ntm_pe={row['ntm_pe'] and round(row['ntm_pe'], 1)}  {row['error'] or ''}", flush=True)
        time.sleep(1.0)

    stamp = today.isoformat()
    if only:
        # A subset run patches today's files in place; with no full run yet today there is nothing to patch.
        daily = DATA / "daily" / f"{stamp}.csv"
        if not daily.exists():
            print("subset run: no full run today yet, not written")
            return 1 if failed else 0
        with open(daily, newline="", encoding="utf-8") as fh:
            kept = [r for r in csv.DictReader(fh) if r["ticker"].upper() not in only]
        with gzip.open(DATA / "raw" / f"{stamp}.jsonl.gz", "rt", encoding="utf-8") as fh:
            kept_raw = [d for d in map(json.loads, fh) if d.get("ticker", "").upper() not in only]
        rows, raws = kept + rows, kept_raw + raws

    with gzip.open(DATA / "raw" / f"{stamp}.jsonl.gz", "wt", encoding="utf-8") as fh:
        for raw in raws:
            fh.write(json.dumps(raw, default=str) + "\n")
    with open(DATA / "daily" / f"{stamp}.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    rebuild_snapshots()
    print(f"{stamp}: {len(rows) - failed}/{len(rows)} tickers with NTM EPS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
