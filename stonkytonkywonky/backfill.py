#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance", "lxml", "pandas"]
# ///
"""Reconstruct daily NTM EPS history from pre-report consensus ("method B").

For every trading day, NTM EPS is the sum of the next four unreported fiscal
quarters, each valued at the consensus Yahoo recorded just before that quarter
was reported. Quarters that have no report row yet are filled from today's
fiscal-year consensus (data/snapshots.csv), split evenly over the quarters
of that year that are still unknown.

This carries look-ahead: an estimate measured just before a report was formed
up to a year after the day it is used for. The size of that bias is graded per
ticker in data/history/validation.csv from recent surprise sizes and 90-day
estimate revisions. Recorded snapshots replace B wherever they exist.

    data/history/earnings/TICKER.csv   Yahoo earnings dates (cache)
    data/history/ntm_b/TICKER.csv      date, close, ntm_eps_b, ntm_pe_b, filled
    data/history/validation.csv        per-ticker bias grade
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
HIST = DATA / "history"
START = "2005-01-01"


def num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def latest_snapshot() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with open(DATA / "snapshots.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["ticker"]] = r  # later dates overwrite earlier ones
    return rows


def fetch_earnings(ticker: str, source: str = "") -> pd.DataFrame:
    """Earnings rows for `source` (default: the ticker itself), cached under `ticker`."""
    path = HIST / "earnings" / f"{ticker}.csv"
    df = yf.Ticker(source or ticker).get_earnings_dates(limit=100)
    if df is None or df.empty:
        raise RuntimeError("no earnings dates")
    df = df.reset_index().rename(
        columns={"Earnings Date": "report", "EPS Estimate": "estimate", "Reported EPS": "reported"}
    )
    df["report"] = pd.to_datetime(df["report"], utc=True).dt.tz_convert(None).dt.date
    df = df[["report", "estimate", "reported"]].sort_values("report").drop_duplicates("report")
    df.to_csv(path, index=False)
    return df


def fetch_close(ticker: str) -> pd.Series:
    h = yf.Ticker(ticker).history(start=START, auto_adjust=False)
    if h.empty:
        raise RuntimeError("no price history")
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).date
    return s


def fetch_fx(src: str, dst: str) -> pd.Series:
    h = yf.Ticker(f"{src}{dst}=X").history(start=START)
    if h.empty:
        raise RuntimeError(f"no FX history {src}{dst}")
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).date
    return s


def reports_per_year(reports: pd.DataFrame) -> int:
    days = pd.Series(pd.to_datetime(reports["report"])).diff().dt.days.dropna()
    gap = float(days.tail(12).median()) if len(days) else 91.0
    return 2 if gap > 150 else 4


def build_series(ticker: str, snap: dict, today: date, estimates_from: str = "") -> tuple[pd.DataFrame, pd.DataFrame]:
    reports = fetch_earnings(ticker, estimates_from)
    close = fetch_close(ticker)
    per_year = reports_per_year(reports)
    gap = timedelta(days=365 // per_year)

    eps_ccy, quote_ccy = snap.get("eps_currency") or "", snap.get("currency") or ""
    fx_now = num(snap.get("fx")) or 1.0
    fx = None if eps_ccy == quote_ccy else fetch_fx(eps_ccy, quote_ccy)

    # One row per reported (or scheduled) period, in estimate currency.
    periods = [{"report": r.report, "estimate": num(r.estimate), "filled": False}
               for r in reports.itertuples()]
    # Periods past the last scheduled report take an even share of whatever of
    # today's NTM consensus the scheduled-but-unreported periods do not explain.
    ntm_now = num(snap.get("ntm_eps"))
    upcoming = [p for p in periods if p["report"] > today][:per_year]
    known = [p["estimate"] for p in upcoming if p["estimate"] is not None]
    missing = per_year - len(known)
    if ntm_now is not None and missing > 0:
        share = (ntm_now / fx_now - sum(known)) / missing
        last = periods[-1]["report"]
        for i in range(missing + per_year):
            periods.append({"report": last + gap * (i + 1), "estimate": share, "filled": True})

    rows = []
    reps = [p["report"] for p in periods]
    for day, px in close.items():
        i = next((k for k, r in enumerate(reps) if r > day), None)
        if i is None:
            continue
        window = periods[i:i + per_year]
        if len(window) < per_year or any(p["estimate"] is None for p in window):
            continue
        if window[-1]["report"] - day > timedelta(days=365 + 75):
            continue  # a period is missing from Yahoo's rows
        rate = 1.0 if fx is None else (num(fx[:day].iloc[-1]) if len(fx[:day]) else None)
        if rate is None:
            continue
        eps = sum(p["estimate"] for p in window) * rate
        rows.append({
            "date": day.isoformat(),
            "close": round(float(px), 4),
            "ntm_eps_b": round(eps, 6),
            "ntm_pe_b": round(px / eps, 4) if eps > 0 else None,
            "filled": sum(1 for p in window if p["filled"]),
        })
    return pd.DataFrame(rows), reports


def yahoo_forward_points(ticker: str) -> list[tuple[date, float]]:
    """Yahoo's sparse genuine forward P/E history; roughly next-fiscal-year based."""
    url = (
        "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
        f"{urllib.parse.quote(ticker)}?symbol={urllib.parse.quote(ticker)}&type=trailingForwardPeRatio"
        "&period1=1451606400&period2=" + str(int(time.time()))
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)["timeseries"]["result"]
    out = []
    for block in result:
        for row in block.get("trailingForwardPeRatio") or []:
            pe = num((row.get("reportedValue") or {}).get("raw"))
            if pe and pe > 0:
                out.append((date.fromisoformat(row["asOfDate"]), pe))
    return out


def grade(ticker: str, reports: pd.DataFrame, snap: dict, series: pd.DataFrame) -> dict:
    done = reports.dropna(subset=["estimate", "reported"]).tail(12)
    surprises = [
        abs(r.reported - r.estimate) / abs(r.estimate)
        for r in done.itertuples() if r.estimate and abs(r.estimate) > 1e-9
    ]
    med_surprise = statistics.median(surprises) if surprises else None
    now, ago = num(snap.get("fy1_eps")), num(snap.get("fy1_eps_90d_ago"))
    rev90 = abs(now / ago - 1) if now and ago and ago > 0 else None

    # Direct check: B's EPS against the EPS implied by Yahoo's genuine points.
    # Yahoo's definition differs (next FY, not NTM), so a steady offset is fine;
    # what B gets wrong shows up as the ratio wandering from point to point.
    try:
        points = yahoo_forward_points(ticker)
    except Exception:  # noqa: BLE001
        points = []
    by_day = dict(zip(series["date"], zip(series["close"], series["ntm_eps_b"])))
    logs = []
    for day, pe in points:
        hit = next((by_day[d.isoformat()] for d in (day - timedelta(days=k) for k in range(5))
                    if d.isoformat() in by_day), None)
        if hit and hit[1] > 0:
            logs.append(math.log(hit[1] / (hit[0] / pe)))
    mid = statistics.median(logs) if logs else None
    # Yahoo's series carries split artifacts (AVGO 2024-07-12 reads 2.8 for ~28); those
    # are ~10x off, far beyond any estimate revision, so drop points past 8x.
    logs = [v for v in logs if abs(v - mid) < math.log(8)] if logs else logs
    mid = statistics.median(logs) if logs else None
    wander = max(abs(v - mid) for v in logs) if len(logs) >= 3 else None

    if wander is not None:
        band = "good" if wander < 0.15 else "caution" if wander < 0.35 else "biased"
    else:
        worst = max((v for v in (med_surprise, rev90) if v is not None), default=None)
        band = None if worst is None else "good" if worst < 0.05 else "caution" if worst < 0.15 else "biased"
    return {
        "ticker": ticker,
        "grade": band,
        "yahoo_points": len(logs),
        "yahoo_wander": None if wander is None else round(wander, 4),
        "yahoo_offset": None if mid is None else round(mid, 4),
        "quarters_scored": len(surprises),
        "median_abs_surprise": None if med_surprise is None else round(med_surprise, 4),
        "fy1_revision_90d": None if rev90 is None else round(rev90, 4),
    }


def main(argv: list[str]) -> int:
    today = date.today()
    snaps = latest_snapshot()
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tickers = [r["ticker"] for r in rows]
    alias = {r["ticker"]: (r.get("estimates_from") or "").strip() for r in rows}
    if argv:
        tickers = [t for t in tickers if t in set(argv)]
    for sub in ("earnings", "ntm_b"):
        (HIST / sub).mkdir(parents=True, exist_ok=True)

    cols = ["ticker", "grade", "yahoo_points", "yahoo_wander", "yahoo_offset",
            "median_abs_surprise", "fy1_revision_90d", "quarters_scored", "first", "days", "error"]
    vpath = HIST / "validation.csv"
    previous: dict[str, dict] = {}
    if vpath.exists():
        with open(vpath, newline="", encoding="utf-8") as fh:
            previous = {r["ticker"]: r for r in csv.DictReader(fh)}

    grades = []
    graded: dict[str, dict] = {}
    for t in tickers:
        snap = snaps.get(t)
        try:
            if not snap or not snap.get("ntm_eps"):
                raise RuntimeError("no NTM consensus in today's snapshot")
            series, reports = build_series(t, snap, today, alias.get(t, ""))
            if series.empty:
                raise RuntimeError("no day with a full year of estimated periods")
            series.to_csv(HIST / "ntm_b" / f"{t}.csv", index=False)
            src = alias.get(t, "")
            # A share class shares its main line's estimates, so it shares its grade;
            # Yahoo's own forward P/E points for the class rest on its thin coverage.
            base = graded.get(src) or previous.get(src) if src else None
            g = ({k: base.get(k) for k in cols} | {"ticker": t} if base else grade(t, reports, snap, series)) | {
                "first": series["date"].iloc[0], "days": len(series), "error": None,
            }
        except Exception as exc:  # noqa: BLE001 — one ticker must not stop the backfill
            g = {"ticker": t, "error": repr(exc)[:200]}
        grades.append(g)
        graded[t] = g
        print(f"{t:<11} {g.get('grade') or '-':<8} pts={g.get('yahoo_points')} wander={g.get('yahoo_wander')} "
              f"surprise={g.get('median_abs_surprise')} from {g.get('first') or '-'}  {g.get('error') or ''}", flush=True)
        time.sleep(1.0)

    # A subset run updates its own rows and keeps everyone else's.
    merged = previous | {g["ticker"]: g for g in grades} if argv else {g["ticker"]: g for g in grades}
    with open(vpath, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for g in merged.values():
            w.writerow({k: g.get(k) for k in cols})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
