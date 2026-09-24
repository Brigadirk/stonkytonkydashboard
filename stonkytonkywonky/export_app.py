#!/usr/bin/env python3
"""Collect the latest forward_screen --all output into JSON for the web app.

    app/public/data/ranking.json        one row per ticker
    app/public/data/series/TICKER.json  chart series, daily for the last
                                        ~18 months and weekly before that

The same files are copied into app/dist/data when a build exists, so the
running preview picks up tonight's numbers without a rebuild.
"""

from __future__ import annotations

import csv
import gzip
import json
import shutil
from statistics import NormalDist
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# The nightly run screens into its own folder so ad-hoc forward_screen runs cannot change the app.
SCREEN_OUT = ROOT / "data" / "screen"
APP = ROOT / "app"
DAILY_DAYS = 550


def num(v) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def ttm_reported(ticker: str, today: date) -> float | None:
    """Last year of reported EPS on the estimates' own (adjusted) basis, in estimate currency.

    Yahoo's trailingPE uses GAAP EPS, which against adjusted forward estimates
    turns amortisation and stock comp into fake "growth".
    """
    path = ROOT / "data" / "history" / "earnings" / f"{ticker}.csv"
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [(date.fromisoformat(r["report"]), num(r["reported"]), num(r["estimate"]))
                for r in csv.DictReader(fh)]
    # Yahoo can lag weeks behind a report (AVGO 2026-09-02 had no actual on 09-24);
    # for a recent report with no actual yet, its pre-report consensus stands in.
    done = [(d, v if v is not None else e) for d, v, e in rows
            if d <= today and (v is not None or (e is not None and (today - d).days <= 120))]
    if len(done) < 2:
        return None
    recent = [(b[0] - a[0]).days for a, b in zip(done, done[1:])][-8:]
    gaps = sorted(recent)
    per_year = 2 if gaps and gaps[len(gaps) // 2] > 150 else 4
    last = done[-per_year:]
    if len(last) < per_year or (today - last[0][0]).days > 365 + 120:
        return None  # a missing report would understate the year
    return sum(v for _, v in last)


CORRIDOR_DAYS = {"90d": 90, "180d": 180, "1Y": 365, "2Y": 730, "3Y": 1095, "4Y": 1461, "5Y": 1826}
# Levels in σ-equivalents, read off the window's own percentiles (−1σ = 15.9th, +2σ = 97.7th)
# so a spell of near-zero EPS cannot drag them the way a mean ± σ would.
SIGMAS = (-2.0, -1.5, -1.0, 0.0, 1.0, 1.5, 2.0)
NORMAL = NormalDist()


def quantile(ordered: list[float], q: float) -> float:
    pos = (len(ordered) - 1) * q
    i = int(pos)
    j = min(i + 1, len(ordered) - 1)
    return ordered[i] + (ordered[j] - ordered[i]) * (pos - i)


def corridors(series: dict) -> dict:
    """16th/50th/84th P/E percentiles per window, from the full daily series.

    Computed here, not in the browser: the app's chart series is thinned to
    weekly points before ~18 months, which would overweight recent days.
    """
    dates = [date.fromisoformat(d) for d in series["dates"]]
    if not dates:
        return {}
    last = dates[-1]
    current = next((p for p in reversed(series["pe"]) if p is not None and p > 0), None)
    out = {}
    for key, days in CORRIDOR_DAYS.items():
        window = sorted(p for d, p in zip(dates, series["pe"])
                        if p is not None and p > 0 and d >= last - timedelta(days=days))
        if len(window) < max(15, days // 8) or current is None:
            continue
        below = sum(1 for p in window if p < current)
        equal = sum(1 for p in window if p == current)
        share = (below + 0.5 * equal) / len(window)
        clipped = min(max(share, 0.5 / len(window)), 1 - 0.5 / len(window))
        out[key] = {
            "levels": {f"{k:g}": quantile(window, NORMAL.cdf(k)) for k in SIGMAS},
            "pct": 100.0 * share,
            # Today's position on the same σ-equivalent scale, for the gauge.
            "sigma": NORMAL.inv_cdf(clipped),
        }
    return out


TREND_STEPS = ("90daysAgo", "60daysAgo", "30daysAgo", "7daysAgo", "current")


def latest_raw() -> dict[str, dict]:
    files = sorted((ROOT / "data" / "raw").glob("*.jsonl.gz"))
    if not files:
        return {}
    with gzip.open(files[-1], "rt", encoding="utf-8") as fh:
        return {d["ticker"]: d for d in map(json.loads, fh)}


def revision_trend(raw: dict | None) -> dict | None:
    """Next-fiscal-year consensus over the last 90 days, and a category for its direction.

    Categories rest on the estimate's own path; Yahoo's up/down analyst counts are
    inconsistent (7-day counts can exceed 30-day ones), so they are shown, not used.
    """
    trend = ((raw or {}).get("eps_trend") or {}).get("+1y") or {}
    values = [num(trend.get(k)) for k in TREND_STEPS]
    if any(v is None for v in values) or values[0] == 0:
        return None
    change = lambda a, b: (b - a) / abs(a) if a else 0.0
    steps = [change(a, b) for a, b in zip(values, values[1:])]
    total = change(values[0], values[-1])
    ups = sum(1 for x in steps if x > 0.001)
    downs = sum(1 for x in steps if x < -0.001)
    if total >= 0.03 and downs == 0 and ups >= 2:
        cat = "up2"
    elif total >= 0.02:
        cat = "up1"
    elif total <= -0.03 and ups == 0 and downs >= 2:
        cat = "down2"
    elif total <= -0.02:
        cat = "down1"
    else:
        cat = "flat"
    counts = ((raw or {}).get("eps_revisions") or {}).get("+1y") or {}
    return {
        "category": cat,
        "change_90d": total,
        "points": [{"days_ago": d, "eps": v} for d, v in zip((90, 60, 30, 7, 0), values)],
        "up_30d": num(counts.get("upLast30days")),
        "down_30d": num(counts.get("downLast30days")),
    }


def thin(series: dict) -> dict:
    """Keep daily points recently and every fifth trading day further back."""
    dates = series["dates"]
    if not dates:
        return series
    cutoff = (date.fromisoformat(dates[-1]) - timedelta(days=DAILY_DAYS)).isoformat()
    keep = [i for i, d in enumerate(dates) if d >= cutoff or i % 5 == 0]
    return {k: [v[i] for i in keep] for k, v in series.items()}


def main() -> int:
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        listed = list(csv.DictReader(fh))
    tickers = [r["ticker"] for r in listed]
    # Share classes of one company: a class names its main line in estimates_from.
    company = {r["ticker"]: (r.get("estimates_from") or "").strip() or r["ticker"] for r in listed}
    grades = {}
    vpath = ROOT / "data" / "history" / "validation.csv"
    if vpath.exists():
        with open(vpath, newline="", encoding="utf-8") as fh:
            grades = {r["ticker"]: r for r in csv.DictReader(fh)}

    latest: dict[str, dict] = {}
    snap_path = ROOT / "data" / "snapshots.csv"
    if snap_path.exists():
        with open(snap_path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                latest[r["ticker"]] = r  # later dates overwrite earlier ones

    raws = latest_raw()
    data = APP / "public" / "data"
    (data / "series").mkdir(parents=True, exist_ok=True)
    rows, as_of = [], None
    for t in tickers:
        folder = SCREEN_OUT / t.replace("/", "-")
        summary_path, series_path = folder / "summary.json", folder / "series.json"
        if not summary_path.exists():
            rows.append({"ticker": t, "missing": True})
            continue
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        as_of = max(as_of or s["as_of"], s["as_of"])
        sig = s.get("signal") or {}
        g = grades.get(t) or {}
        pe = s["forward_pe"]["current"]
        snap = latest.get(t) or {}
        ttm = ttm_reported(t, date.fromisoformat(s["as_of"]))
        fx = num(snap.get("fx")) or 1.0
        price = s.get("price")
        trailing = price / (ttm * fx) if ttm and ttm > 0 and price else None
        # NTM EPS over TTM EPS; equals trailing P/E over forward P/E at the same price.
        growth = trailing / pe - 1 if trailing and trailing > 0 and pe and pe > 0 else None
        rows.append({
            "ticker": t,
            "company": company.get(t, t),
            "name": s.get("name"),
            "currency": s.get("currency"),
            "as_of": s["as_of"],
            "price": s.get("price"),
            "pe": pe,
            "trailing_pe": trailing,
            "growth": growth,
            "eps": s["forward_eps"]["current"],
            # Next fiscal year consensus, quote currency: where the corridor's EPS path heads.
            "fy1_eps": num(snap.get("fy1_eps")),
            "fy1_end": (
                (date.fromisoformat(snap["fy0_end"]) + timedelta(days=365)).isoformat()
                if snap.get("fy0_end") else None
            ),
            "pe_pct": sig.get("pe_pct"),
            "pe_median": sig.get("pe_median"),
            "pe_p16": sig.get("pe_p16"),
            "pe_p84": sig.get("pe_p84"),
            "lookback_days": sig.get("lookback_days"),
            "fy1_revision_90d": sig.get("fy1_revision_90d"),
            "signal": sig.get("label"),
            "b_grade": sig.get("b_grade"),
            "b_wander": g.get("yahoo_wander") or None,
            "eps_source": s["coverage"].get("eps_source"),
            "warnings": s["coverage"].get("warnings") or [],
            "past": s.get("past_screen"),
            "revisions": revision_trend(raws.get(t)),
        })
        if series_path.exists():
            series = json.loads(series_path.read_text(encoding="utf-8"))
            rows[-1]["corridors"] = corridors(series)
            (data / "series" / f"{t}.json").write_text(json.dumps(thin(series)), encoding="utf-8")

    (data / "ranking.json").write_text(
        json.dumps({"as_of": as_of, "rows": rows}, default=str), encoding="utf-8"
    )
    dist = APP / "dist"
    if dist.exists():
        shutil.copytree(data, dist / "data", dirs_exist_ok=True)
    print(f"exported {sum(1 for r in rows if not r.get('missing'))}/{len(rows)} tickers as of {as_of}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
