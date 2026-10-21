#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance"]
# ///
"""Discounts of stocks that are mostly a claim on another stock, over time.

    holding     market value of the holding company ÷ market value of its listed stake
                (SK Square owns 146.1m SK hynix shares, about 20%)
    preferred   preferred share price ÷ common share price (Samsung Electronics)

Discount = 1 − ratio, so 40% means the market pays 60 for 100 of underlying value.
Holding company share counts come from Yahoo's share history; stakes are fixed
counts set in PAIRS, so update them when a company buys or sells.

    app/public/data/discounts.json
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "app" / "public" / "data" / "discounts.json"
UA = "Mozilla/5.0"
# range=max silently switches to monthly bars; explicit periods keep daily ones.
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=946684800&period2={now}&interval=1d"

PAIRS = [
    {
        "key": "sksquare", "kind": "holding", "name": "SK Square vs its SK hynix stake",
        "holdco": "402340.KS", "holdco_name": "SK Square",
        "stakes": [{"ticker": "000660.KS", "name": "SK hynix", "shares": 146_100_000}],
        "note": "Only the SK hynix stake is counted. SK Square's other holdings (11st, Tmap, SK Planet and others) and its cash are small next to it, so the true discount to everything it owns is a few points wider.",
    },
    {
        "key": "samsung_pref", "kind": "preferred", "name": "Samsung Electronics preferred vs common",
        "pref": "005935.KS", "common": "005930.KS",
        "note": "Preferred shares have no vote and get ₩1 more dividend a year per share; otherwise the same claim on the company.",
    },
]


def closes(t: str) -> dict[str, float]:
    with urllib.request.urlopen(urllib.request.Request(CHART.format(t=t, now=int(time.time())), headers={"User-Agent": UA}), timeout=60) as r:
        res = json.load(r)["chart"]["result"][0]
    out = {}
    for ts, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None:
            out[datetime.fromtimestamp(ts + res["meta"].get("gmtoffset", 0), timezone.utc).date().isoformat()] = c
    return out


def shares_history(t: str) -> list[tuple[str, float]]:
    s = yf.Ticker(t).get_shares_full(start="2015-01-01")
    pts = sorted((ts.date().isoformat(), float(v)) for ts, v in s.items())
    # Yahoo's history has one-day glitches (Samsung common showed 9.2bn for a day); keep a value
    # only when the next one agrees with it within 5%, or it is the last.
    clean = [p for i, p in enumerate(pts) if i == len(pts) - 1 or abs(pts[i + 1][1] / p[1] - 1) < 0.05
             or (i > 0 and abs(pts[i - 1][1] / p[1] - 1) < 0.05)]
    return clean


def step(points: list[tuple[str, float]], d: str) -> float | None:
    v = None
    for pd, pv in points:
        if pd > d:
            break
        v = pv
    return v if v is not None else (points[0][1] if points else None)


def stats(dates: list[str], values: list[float]) -> dict:
    last, d_last = values[-1], date.fromisoformat(dates[-1])

    def window(days: int) -> list[float]:
        return [v for d, v in zip(dates, values) if (d_last - date.fromisoformat(d)).days <= days]

    def median(xs: list[float]) -> float:
        s = sorted(xs)
        m = len(s) // 2
        return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2

    out = {"last": last, "date": dates[-1], "min": min(values), "max": max(values), "median_all": median(values)}
    for label, days in (("1y", 365), ("3y", 1095)):
        w = window(days)
        out[f"median_{label}"] = median(w)
        out[f"pct_{label}"] = sum(v <= last for v in w) / len(w) * 100  # high = wide discount
    for label, days in (("1m", 30), ("3m", 91), ("1y", 365)):
        past = [v for d, v in zip(dates, values) if (d_last - date.fromisoformat(d)).days >= days]
        out[f"chg_{label}"] = last - past[-1] if past else None  # in discount points
    return out


def build(p: dict) -> dict:
    if p["kind"] == "holding":
        hc = closes(p["holdco"])
        hc_sh = shares_history(p["holdco"])
        legs = [(closes(s["ticker"]), s) for s in p["stakes"]]
        dates = sorted(d for d in hc if all(d in c for c, _ in legs))
        disc, mcap, nav = [], [], []
        for d in dates:
            m = hc[d] * step(hc_sh, d)
            v = sum(c[d] * s["shares"] for c, s in legs)
            mcap.append(m)
            nav.append(v)
            disc.append(1 - m / v)
        latest = {"holdco_cap": mcap[-1], "stake_value": nav[-1], "holdco_price": hc[dates[-1]],
                  "holdco_shares": step(hc_sh, dates[-1])}
    else:
        pr, cm = closes(p["pref"]), closes(p["common"])
        dates = sorted(d for d in pr if d in cm)
        disc = [1 - pr[d] / cm[d] for d in dates]
        latest = {"pref_price": pr[dates[-1]], "common_price": cm[dates[-1]]}
    item = {k: v for k, v in p.items()}
    item.update(latest=latest, stats=stats(dates, disc),
                history={"dates": dates, "values": [round(v, 4) for v in disc]})
    return item


def main() -> None:
    items = []
    for p in PAIRS:
        try:
            items.append(build(p))
            s = items[-1]["stats"]
            print(f"{p['key']}: {s['last']:.1%} on {s['date']} (3y median {s['median_3y']:.1%}, range {s['min']:.1%}–{s['max']:.1%})")
        except Exception as e:
            print(f"{p['key']}: failed: {e}")
        time.sleep(0.5)
    if not items:
        raise SystemExit("no discounts computed; keeping the earlier file")
    OUT.write_text(json.dumps({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "items": items}), encoding="utf-8")


if __name__ == "__main__":
    main()
