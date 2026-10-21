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
import re
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
ANALYST_MAX_AGE_DAYS = 730  # older reports say little about today's forecasts


# One name per broker, whichever way a source spelled it (the earlier project used short keys).
FIRMS = {
    "meritz": "Meritz Securities", "메리츠": "Meritz Securities", "hana": "Hana Securities",
    "kb": "KB Securities", "mirae": "Mirae Asset", "nh": "NH Investment",
    "hyundai": "Hyundai Motor Securities", "samsung": "Samsung Securities", "kiwoom": "Kiwoom",
    "daishin": "Daishin", "shinhan": "Shinhan Investment",
}


def firm_name(raw: str) -> str:
    key = (raw or "").strip().lower()
    for k, v in FIRMS.items():
        if key == k or key.startswith(k + " ") or k in raw:
            return v
    return raw.strip()


def basis_rank(basis: str) -> int:
    """Consensus is on an adjusted (non-GAAP) basis, so prefer that when a report prints both."""
    b = (basis or "").lower()
    return 0 if "adjust" in b or "non-gaap" in b or "non_gaap" in b else 1


def value_ratios(f: dict | None, price: float | None) -> dict:
    """EV/FCF and price-to-book at today's price, everything in the quote currency.

    fundamentals.csv holds statement figures in the reporting currency with the rate
    to the quote currency, and the company-wide share count. Negative free cash flow
    or book value has no meaningful multiple; the sign is kept so the app can say so.
    """
    out = {"ev_fcf": None, "pb": None, "fcf_yield": None, "fcf_negative": False, "fcf_basis": None, "fcf_end": None}
    if not f or not price or f.get("error"):
        return out
    fx, shares = num(f.get("fx")), num(f.get("shares"))
    fcf, equity = num(f.get("fcf")), num(f.get("equity"))
    if not fx or not shares:
        return out
    mcap = shares * price
    ev = mcap + ((num(f.get("debt")) or 0.0) - (num(f.get("cash")) or 0.0)) * fx
    if fcf is not None:
        out.update(fcf_basis=f.get("fcf_basis") or None, fcf_end=f.get("fcf_end") or None, fcf_negative=fcf <= 0,
                   fcf_yield=fcf * fx / mcap)
        if fcf > 0 and ev > 0:
            out["ev_fcf"] = ev / (fcf * fx)
    if equity and equity > 0:
        out["pb"] = mcap / (equity * fx)
    return out


def load_fundamentals() -> dict[str, dict]:
    path = ROOT / "data" / "fundamentals.csv"
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["ticker"]: r for r in csv.DictReader(fh)}


def load_analysts() -> dict[str, list[dict]]:
    path = ROOT / "analysts" / "observations.csv"
    out: dict[str, list[dict]] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out.setdefault(r["ticker"], []).append(r)
    return out


def load_targets() -> dict[str, list[dict]]:
    """Named analysts' price targets (analysts/targets.csv), entered by hand from press reports."""
    path = ROOT / "analysts" / "targets.csv"
    out: dict[str, list[dict]] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out.setdefault(r["ticker"], []).append(r)
    return out


def targets_view(rows: list[dict], price: float | None, as_of: date) -> dict | None:
    """Each firm's latest price target from the last year, and the upside to their median."""
    latest: dict[str, dict] = {}
    for r in rows:
        age = (as_of - date.fromisoformat(r["date"])).days
        if age > 365 or age < 0 or not num(r["target"]):
            continue
        if r["firm"] not in latest or r["date"] > latest[r["firm"]]["date"]:
            latest[r["firm"]] = {"date": r["date"], "age_days": age, "firm": r["firm"], "analyst": r["analyst"],
                                 "action": r["action"], "rating": r["rating"], "target": num(r["target"]),
                                 "prev_target": num(r["prev_target"]), "source_url": r["source_url"]}
    if not latest:
        return None
    items = sorted(latest.values(), key=lambda x: x["date"], reverse=True)
    vals = sorted(x["target"] for x in items)
    mid = len(vals) // 2
    median = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return {"items": items, "median": median, "low": vals[0], "high": vals[-1],
            "upside": median / price - 1 if price else None}


FY_SHOWN = (2027, 2028)


def year_ratio(raw: dict | None, obs: list[dict], extra: dict | None, y: int, as_of: date) -> tuple[float, str] | None:
    """Growth from fiscal year y to y+1 from a second source, to extend Yahoo's two years.

    Nasdaq (Zacks) and named analysts are on other bases than Yahoo's consensus, so only
    their year-on-year ratio is used, chained onto Yahoo's figure for year y.
    """
    rows = (((raw or {}).get("nasdaq_forecast") or {}).get("yearlyForecast") or {}).get("rows") or []
    by_year = {}
    for r in rows:
        m = re.search(r"(\d{4})$", r.get("fiscalEnd") or "")
        if m:
            by_year[int(m.group(1))] = r
    a, b = by_year.get(y), by_year.get(y + 1)
    if a and b and num(a.get("consensusEPSForecast")) and num(b.get("consensusEPSForecast")):
        va, vb = num(a["consensusEPSForecast"]), num(b["consensusEPSForecast"])
        if va > 0 and vb > 0:
            n = int(num(b.get("noOfEstimates")) or 0)
            return vb / va, f"Nasdaq/Zacks growth FY{y}→FY{y + 1}, {n} estimate{'s' if n != 1 else ''}"
    # Eastmoney's broker consensus (data/extra_forecasts.json, Shanghai and Shenzhen listings).
    eps = (extra or {}).get("eps") or {}
    va, vb = num(eps.get(str(y))), num(eps.get(str(y + 1)))
    if va and vb and va > 0 and vb > 0:
        return vb / va, f"{extra['source']} growth FY{y}→FY{y + 1}"
    # Named analysts who forecast both years in the same report (Korean and European names).
    reports: dict[tuple, dict] = {}
    for r in obs:
        if r["kind"] != "analyst" or not r["report_date"]:
            continue
        if (as_of - date.fromisoformat(r["report_date"][:10])).days > 365:
            continue
        reports.setdefault((r["firm"], r["report_date"][:10]), {})[r["fiscal_period"]] = num(r["eps"])
    ratios = sorted(e[f"FY{y + 1}"] / e[f"FY{y}"] for e in reports.values()
                    if (e.get(f"FY{y}") or 0) > 0 and (e.get(f"FY{y + 1}") or 0) > 0)
    if ratios:
        mid = len(ratios) // 2
        ratio = ratios[mid] if len(ratios) % 2 else (ratios[mid - 1] + ratios[mid]) / 2
        return ratio, f"median growth FY{y}→FY{y + 1} of {len(ratios)} analyst report{'s' if len(ratios) > 1 else ''}"
    return None


def forward_years(snap: dict, raw: dict | None, obs: list[dict], extra: dict | None,
                  ttm_quote: float | None, as_of: date) -> dict:
    """Consensus EPS for FY2027 and FY2028, and expected growth over the next 24 months.

    Fiscal years are named by the calendar year they end in (Nvidia's to January 2027 is
    FY2027). Yahoo gives the current and next fiscal year; the year after that is chained
    from another source's growth rate; with no source, it grows at half the rate of the
    year before (marked extrapolated). Growth over 24 months compares profit in months
    13-24 from now, blended from fiscal years the way the forward EPS is, with the last 12.
    """
    out = {"fy_eps": {}, "growth_24m": None, "eps_24m": None, "extrapolated_24m": False}
    fy0_end, fy0, fy1 = snap.get("fy0_end"), num(snap.get("fy0_eps")), num(snap.get("fy1_eps"))
    if not fy0_end or fy1 is None:
        return out
    y0 = int(fy0_end[:4])
    years = {y0: (fy0, "Yahoo consensus"), y0 + 1: (fy1, "Yahoo consensus")}
    if fy0 is None:
        del years[y0]
    y, v = y0 + 1, fy1
    prev_growth = fy1 / fy0 - 1 if fy0 and fy0 > 0 and fy1 > 0 else None
    extrapolated = set()
    while y < max(FY_SHOWN[-1], y0 + 2) and v is not None and v > 0:
        got = year_ratio(raw, obs, extra, y, as_of)
        if got:
            prev_growth = got[0] - 1
            v, y = v * got[0], y + 1
            years[y] = (v, f"Yahoo FY{y0 + 1} consensus × {got[1]}")
        elif prev_growth is not None:
            # No source for this year: assume growth slows to half of the year before.
            prev_growth /= 2
            v, y = v * (1 + prev_growth), y + 1
            years[y] = (v, f"extrapolated: no forecast found, so FY{y - 1} grown at half its own growth rate ({prev_growth * 100:+.0f}%)")
            extrapolated.add(y)
        else:
            break
    if y < FY_SHOWN[-1] and v is not None and v <= 0:
        # Loss-making: a growth ratio means nothing, so take Nasdaq's own figures as they are.
        rows = (((raw or {}).get("nasdaq_forecast") or {}).get("yearlyForecast") or {}).get("rows") or []
        fx = num(snap.get("fx")) or 1.0
        for r in rows:
            m = re.search(r"(\d{4})$", r.get("fiscalEnd") or "")
            val = num(r.get("consensusEPSForecast"))
            if m and val is not None and y < int(m.group(1)) <= FY_SHOWN[-1] and snap.get("currency") == "USD":
                n = int(num(r.get("noOfEstimates")) or 0)
                years[int(m.group(1))] = (val, f"Nasdaq/Zacks consensus, {n} estimate{'s' if n != 1 else ''} (loss-making, so not chained to Yahoo)")
    for fy in FY_SHOWN:
        if fy in years and years[fy][0] is not None:
            out["fy_eps"][f"FY{fy}"] = {"eps": years[fy][0], "source": years[fy][1], "extrapolated": fy in extrapolated}
    w0 = num(snap.get("fy0_weight"))
    nxt, after = years.get(y0 + 1, (None,))[0], years.get(y0 + 2, (None,))[0]
    if w0 is not None and nxt is not None and (after is not None or w0 >= 0.999):
        eps24 = w0 * nxt + (1 - w0) * (after or 0)
        out["eps_24m"] = eps24
        out["extrapolated_24m"] = (y0 + 2) in extrapolated and w0 < 0.999
        if ttm_quote and ttm_quote > 0:
            out["growth_24m"] = eps24 / ttm_quote - 1
    return out


def load_notes() -> dict[str, list[dict]]:
    """Hand-written context per ticker (analysts/notes.json), e.g. what a guidance change really was."""
    path = ROOT / "analysts" / "notes.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def analyst_view(rows: list[dict], snap: dict, as_of: date) -> dict | None:
    """Each analyst's latest report: next two fiscal years' EPS in the quote currency, vs consensus."""
    fy0_end = snap.get("fy0_end")
    if not rows or not fy0_end:
        return None
    y0 = int(fy0_end[:4])
    labels = (f"FY{y0}", f"FY{y0 + 1}")
    quote_ccy, eps_ccy, fx = snap.get("currency"), snap.get("eps_currency"), num(snap.get("fx")) or 1.0

    def to_quote(value: float, ccy: str) -> float | None:
        if not ccy or ccy == quote_ccy:
            return value
        if ccy == eps_ccy:
            return value * fx
        return None  # a currency we have no rate for

    latest: dict[tuple, dict] = {}
    for r in rows:
        if not r["report_date"] or r["fiscal_period"] not in labels:
            continue
        age = (as_of - date.fromisoformat(r["report_date"][:10])).days
        if age > ANALYST_MAX_AGE_DAYS or age < 0:
            continue
        # Group by broker, not by how its analyst's name was written (Korean or romanised).
        key = (firm_name(r["firm"]), r["kind"])
        cur = latest.get(key)
        if cur is None or r["report_date"][:10] > cur["date"]:
            latest[key] = cur = {"firm": key[0], "analyst": r["analyst"], "kind": r["kind"],
                                 "date": r["report_date"][:10], "age_days": age, "status": r["status"],
                                 "basis": r["basis"], "source_url": r["source_url"], "eps": {}, "_rank": {}}
        if cur["date"] == r["report_date"][:10]:
            v = to_quote(float(r["eps"]), r["currency"])
            rank = basis_rank(r["basis"])
            if v is not None and rank <= cur["_rank"].get(r["fiscal_period"], 9):
                cur["eps"][r["fiscal_period"]] = v
                cur["_rank"][r["fiscal_period"]] = rank
                cur["basis"] = r["basis"]  # describe the figures actually shown
    consensus = {labels[0]: num(snap.get("fy0_eps")), labels[1]: num(snap.get("fy1_eps"))}
    for x in latest.values():
        # Flag GAAP/reported figures: consensus is adjusted, so the gap overstates the difference.
        x["gaap"] = any(v == 1 for v in x.pop("_rank", {}).values()) and bool(
            re.search(r"reported|gaap", x["basis"], re.I)) and not re.search(r"non.?gaap", x["basis"], re.I)
    reports = sorted((x for x in latest.values() if x["eps"]), key=lambda x: x["date"], reverse=True)
    for x in reports:
        c = consensus.get(labels[1])
        v = x["eps"].get(labels[1])
        x["vs_consensus"] = v / c - 1 if v is not None and c else None
    return {"years": list(labels), "consensus": consensus,
            "consensus_analysts": num(snap.get("fy1_analysts")), "reports": reports} if reports else None


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


def sales_mode(row: dict, ticker: str, snap: dict, data: Path) -> None:
    """Value a loss-maker on sales: without profits there is no P/E to compare.

    The app's valuation fields are reused, with `metric` = "ps": `pe` holds trailing
    P/S (compared with its own trailing history from sales_history.py), `eps` holds
    trailing revenue per share and `fy1_eps` next-twelve-month revenue per share,
    so corridors project to the price that the same multiple of NTM sales implies.
    """
    ntm_eps = num(snap.get("ntm_eps"))
    path = ROOT / "data" / "history" / "ps" / f"{ticker}.csv"
    if (ntm_eps is not None and ntm_eps > 0) or not path.exists() or snap.get("ntm_eps") in (None, ""):
        return
    with open(path, newline="", encoding="utf-8") as fh:
        hist = list(csv.DictReader(fh))
    if len(hist) < 60:
        return
    series = {
        "dates": [h["date"] for h in hist],
        "price": [num(h["close"]) for h in hist],
        "eps": [num(h["ttm_rev_ps"]) for h in hist],
        "pe": [num(h["ttm_ps"]) for h in hist],
    }
    shares, ntm_rev = num(snap.get("shares")), num(snap.get("ntm_rev"))
    row.update({
        "metric": "ps",
        "pe": series["pe"][-1],
        "eps": series["eps"][-1],
        "fy1_eps": ntm_rev / shares if ntm_rev and shares else None,
        "ps_forward": num(snap.get("ntm_ps")),
        "rev_analysts": num(snap.get("rev_analysts")),
        "shares_source": snap.get("shares_source") or "",
        "trailing_pe": None,
        "growth": None,
        "corridors": corridors(series),
        "b_grade": None,  # the P/S history rests on reported revenue, not reconstructed estimates
    })
    main = row["corridors"].get("3Y") or {}
    row["pe_pct"] = main.get("pct")
    (data / "series" / f"{ticker}.json").write_text(json.dumps(thin(series)), encoding="utf-8")


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
    analysts = load_analysts()
    targets = load_targets()
    notes = load_notes()
    extra_path = ROOT / "data" / "extra_forecasts.json"
    extra = json.loads(extra_path.read_text(encoding="utf-8")) if extra_path.exists() else {}
    funds = load_fundamentals()
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
        ttm_basis = "adjusted"
        if ttm is None:
            # No report history on the estimates' basis: Yahoo's trailing (GAAP) EPS stands in,
            # read off its trailing P/E so it is in the quote currency whatever Yahoo reports in.
            y_pe, y_eps, px = num(snap.get("trailing_pe")), num(snap.get("trailing_eps")), num(snap.get("price"))
            if y_pe and y_pe > 0 and px:
                ttm, ttm_basis = px / y_pe / fx, "GAAP (Yahoo)"
            elif y_eps is not None and y_eps <= 0:
                ttm, ttm_basis = y_eps, "GAAP (Yahoo)"  # a loss: only its sign is used
        price = s.get("price")
        trailing = price / (ttm * fx) if ttm and ttm > 0 and price else None
        # NTM EPS over TTM EPS; equals trailing P/E over forward P/E at the same price.
        growth = trailing / pe - 1 if trailing and trailing > 0 and pe and pe > 0 else None
        rows.append({
            "ticker": t,
            "company": company.get(t, t),
            "sector": snap.get("sector") or None,
            "industry": snap.get("industry") or None,
            "name": s.get("name"),
            "currency": s.get("currency"),
            "as_of": s["as_of"],
            "price": s.get("price"),
            "pe": pe,
            "trailing_pe": trailing,
            "growth": growth,
            "ttm_basis": ttm_basis if ttm is not None else None,
            "ttm_loss": ttm is not None and ttm <= 0,
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
            "analysts": analyst_view(analysts.get(t, []), snap, date.fromisoformat(s["as_of"])),
            "targets": targets_view(targets.get(t, []), price, date.fromisoformat(s["as_of"])),
            **forward_years(snap, raws.get(t), analysts.get(t) or analysts.get(company.get(t), []), extra.get(t),
                            ttm * fx if ttm else None,
                            date.fromisoformat(s["as_of"])),
            # Notes older than half a year have usually been overtaken by events.
            "notes": [n for n in notes.get(t, [])
                      if (date.fromisoformat(s["as_of"]) - date.fromisoformat(n["date"])).days <= 182] or None,
            **value_ratios(funds.get(t), price),
        })
        if series_path.exists():
            series = json.loads(series_path.read_text(encoding="utf-8"))
            rows[-1]["corridors"] = corridors(series)
            (data / "series" / f"{t}.json").write_text(json.dumps(thin(series)), encoding="utf-8")
        sales_mode(rows[-1], t, snap, data)

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
