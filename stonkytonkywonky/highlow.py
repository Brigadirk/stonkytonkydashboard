#!/usr/bin/env -S /home/dirk/.local/bin/uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "pyarrow", "lxml"]
# ///
"""New 52-week highs and lows across the S&P 1500, and what followed such readings since 1991.

The universe is today's S&P 500, 400 and 600 members with their GICS sector and
sub-industry (Wikipedia's lists, refreshed weekly). Daily highs, lows and closes come
from Yahoo; the first run takes each stock's full history, later runs the last month.

    data/highlow/universe.csv               symbol, name, sector, industry, index
    data/highlow/{close,high,low}.parquet   daily, one column per symbol, plus ^GSPC ^VIX ^NDX ^RUT
    app/public/data/highlow.json            today's highs and lows by sector, daily history, signal study

Dip-buying scores for the market and its sectors come from dipscore.py.

A new high is a day whose high beats every high of the previous 251 sessions; a new low
likewise. The share of highs is highs ÷ (highs + lows), summed over 10 sessions.

Caveat: these are today's members, so the past has no delisted losers. Against the
official NYSE + Nasdaq counts (2005–2020) the 10-day share of highs correlates 0.95,
but it runs about 10 points higher, so read levels as percentiles, not absolutes.
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import dipscore

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "highlow"
APP = ROOT / "app"
UA = "Mozilla/5.0"
INDEXES = ["^GSPC", "^VIX", "^NDX", "^RUT"]
WIKI = {"500": "List_of_S%26P_500_companies", "400": "List_of_S%26P_400_companies", "600": "List_of_S%26P_600_companies"}
WINDOW = 252
COOLDOWN = 60  # sessions between two events of the same signal
HORIZONS = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}


def get(url: str, timeout: int = 40) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        return r.read()


def universe() -> pd.DataFrame:
    path = OUT / "universe.csv"
    if path.exists() and date.fromtimestamp(path.stat().st_mtime) > date.today() - timedelta(days=7):
        return pd.read_csv(path)
    rows = []
    try:
        for idx, page in WIKI.items():
            tabs = pd.read_html(io.StringIO(get(f"https://en.wikipedia.org/wiki/{page}").decode()))
            t = next(t for t in tabs if "Symbol" in t.columns)
            for _, r in t.iterrows():
                rows.append({"symbol": str(r["Symbol"]).replace(".", "-"), "name": r["Security"],
                             "sector": r["GICS Sector"], "industry": r["GICS Sub-Industry"], "index": idx})
    except Exception as e:  # noqa: BLE001 — keep last week's list
        if path.exists():
            print(f"universe refresh failed ({e}); keeping the stored list")
            return pd.read_csv(path)
        raise
    df = pd.DataFrame(rows).drop_duplicates("symbol")
    df.to_csv(path, index=False)
    return df


def chart(symbol: str, full: bool) -> pd.DataFrame | None:
    span = "period1=631152000&period2=%d" % time.time() if full else "range=1mo"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}?{span}&interval=1d"
    for k in range(3):
        try:
            res = json.loads(get(url))["chart"]["result"][0]
            tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
            q = res["indicators"]["quote"][0]
            idx = pd.to_datetime([datetime.fromtimestamp(t, tz).date() for t in res["timestamp"]])
            df = pd.DataFrame({"c": q["close"], "h": q["high"], "l": q["low"]}, index=idx, dtype="float64")
            return df[~df.index.duplicated(keep="last")]
        except Exception:  # noqa: BLE001 — rate limits and delisted symbols; retry, then skip
            time.sleep(2 + 4 * k)
    return None


def update_prices(symbols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = {}
    for k in ("close", "high", "low"):
        p = OUT / f"{k}.parquet"
        frames[k] = pd.read_parquet(p) if p.exists() else pd.DataFrame()
    known = set(frames["close"].columns)
    fails = 0

    def one(s):
        return s, chart(s, full=s not in known)

    with ThreadPoolExecutor(4) as ex:
        for s, df in ex.map(one, symbols):
            if df is None:
                fails += 1
                continue
            for k, col in (("close", "c"), ("high", "h"), ("low", "l")):
                f = frames[k]
                new = df[col].dropna()
                f = f.reindex(f.index.union(new.index))
                f.loc[new.index, s] = new.values
                frames[k] = f
    print(f"prices: {len(symbols) - fails}/{len(symbols)} symbols updated")
    for k, f in frames.items():
        f = f.sort_index()
        f = f[f.index.dayofweek < 5]
        frames[k] = f
        f.to_parquet(OUT / f"{k}.parquet")
    return frames["close"], frames["high"], frames["low"]


def events(mask: pd.Series) -> list[int]:
    """Positions where the signal fires, at most one per COOLDOWN sessions."""
    out, last = [], -10**9
    for i in np.flatnonzero(mask.fillna(False).to_numpy()):
        if i - last > COOLDOWN:
            out.append(int(i))
            last = i
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    uni = universe()
    c, h, l = update_prices(list(uni.symbol) + INDEXES)
    c = c[c["^GSPC"].notna()]
    h, l = h.reindex(c.index), l.reindex(c.index)
    stocks = [s for s in uni.symbol if s in c.columns]
    C = c[stocks]
    Hh, Ll = h[stocks].fillna(C), l[stocks].fillna(C)
    prior_hi = Hh.shift(1).rolling(WINDOW - 1, min_periods=WINDOW - 1).max()
    prior_lo = Ll.shift(1).rolling(WINDOW - 1, min_periods=WINDOW - 1).min()
    valid = prior_hi.notna() & C.notna()
    is_hi, is_lo = (Hh > prior_hi) & valid, (Ll < prior_lo) & valid
    ma200 = C.rolling(200, min_periods=200).mean()

    d = pd.DataFrame({
        "n": valid.sum(axis=1), "nh": is_hi.sum(axis=1), "nl": is_lo.sum(axis=1),
        "above200": ((C > ma200) & ma200.notna()).sum(axis=1) / ma200.notna().sum(axis=1).replace(0, np.nan),
        "spx": c["^GSPC"], "vix": c["^VIX"],
    })
    d = d[d.n >= 300]  # from 1991, when enough of today's members had a year of history
    d["hp10"] = d.nh.rolling(10).sum() / (d.nh + d.nl).rolling(10).sum()
    d["nl_pct"], d["nh_pct"] = d.nl / d.n, d.nh / d.n
    d["dd"] = d.spx / d.spx.cummax() - 1
    for k, n in HORIZONS.items():
        d["f" + k] = d.spx.shift(-n) / d.spx - 1
    # Worst close within the next 3 months, from the signal day.
    d["pain3m"] = d.spx[::-1].rolling(63, min_periods=1).min()[::-1].shift(-1) / d.spx - 1

    vix_peak20 = d.vix.rolling(20).max()
    low_recent = (d.hp10 < 0.10).rolling(40).max() > 0
    signals = [
        ("washout30", "Washout: 30% or more of stocks at a new low on one day", d.nl_pct >= 0.30),
        ("washout15", "15% or more of stocks at a new low on one day", d.nl_pct >= 0.15),
        ("hp10_10", "Share of highs under 10% over 10 sessions", d.hp10 < 0.10),
        ("above200_20", "Under 20% of stocks above their 200-day average", d.above200 < 0.20),
        ("vix35", "VIX above 35", d.vix > 35),
        ("vix_fading", "Fear fading: VIX was above 35 within 20 sessions, now under 30, and under 30% of stocks above their 200-day", (vix_peak20 > 35) & (d.vix < 30) & (d.above200 < 0.30)),
        ("recovery", "Recovery: share of highs back above 50% within 40 sessions of being under 10%", low_recent & (d.hp10 > 0.5) & (d.hp10.shift(1) <= 0.5)),
        ("dd10_20", "S&P 500 10–20% below its high", d.dd.between(-0.20, -0.10)),
        ("narrow200", "Narrow market: S&P 500 within 3% of its high, under 50% of stocks above their 200-day", (d.dd > -0.03) & (d.above200 < 0.50)),
        ("narrow_hp", "Narrow highs: S&P 500 within 3% of its high, share of highs under 50%", (d.dd > -0.03) & (d.hp10 < 0.50)),
        ("broad", "Broad strength: S&P 500 within 3% of its high, share of highs over 80%", (d.dd > -0.03) & (d.hp10 > 0.80)),
    ]
    rnd = lambda v, k=4: None if v is None or not np.isfinite(v) else round(float(v), k)  # noqa: E731
    study = []
    base = {k: rnd(d["f" + k].median()) for k in HORIZONS}
    for key, label, mask in signals:
        ev = events(mask)
        x = d.iloc[ev]
        row = {"key": key, "label": label, "events": len(ev), "days": int(mask.fillna(False).sum()),
               "now": bool(mask.fillna(False).iloc[-1]),
               "last": None if not ev else d.index[np.flatnonzero(mask.fillna(False).to_numpy())[-1]].date().isoformat(),
               "dates": [d.index[i].date().isoformat() for i in ev],
               "pain3m": rnd(x.pain3m.median())}
        for k in HORIZONS:
            v = x["f" + k].dropna()
            row["med_" + k] = rnd(v.median()) if len(v) else None
            row["up_" + k] = rnd((v > 0).mean(), 3) if len(v) else None
        study.append(row)

    # Today's highs and lows by sector; "hits" counts new highs (lows) over the last 21 sessions.
    last = C.index[-1]
    hits_hi = is_hi.iloc[-21:].sum()
    hits_lo = is_lo.iloc[-21:].sum()
    chg = C.iloc[-1] / C.iloc[-2] - 1
    meta = uni.set_index("symbol")
    today = {"highs": [], "lows": []}
    for side, mask, hits in (("highs", is_hi.iloc[-1], hits_hi), ("lows", is_lo.iloc[-1], hits_lo)):
        for s in mask[mask].index:
            today[side].append({"s": s, "name": meta.at[s, "name"], "sector": meta.at[s, "sector"],
                                "industry": meta.at[s, "industry"], "hits": int(hits[s]), "chg": rnd(chg[s])})
    L = d.iloc[-1]
    pctile = lambda col: rnd(100 * (d[col] <= d[col].iloc[-1]).mean(), 1)  # noqa: E731
    keep = ["nh", "nl", "n", "hp10", "above200", "spx", "vix", "dd"]
    hist = d[keep]
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": last.date().isoformat(),
        "latest": {"n": int(L.n), "nh": int(L.nh), "nl": int(L.nl), "hp10": rnd(L.hp10), "hp10_pct": pctile("hp10"),
                   "above200": rnd(L.above200), "above200_pct": pctile("above200"), "dd": rnd(L.dd), "vix": rnd(L.vix, 2),
                   "spx": rnd(L.spx, 2)},
        "today": today,
        "baseline": {**{"med_" + k: v for k, v in base.items()},
                     **{"up_" + k: rnd((d["f" + k].dropna() > 0).mean(), 3) for k in HORIZONS},
                     "pain3m": rnd(d.pain3m.median())},
        "study": study,
        "dip": dipscore.build(c, l, uni, OUT),
        "history": {"dates": [t.date().isoformat() for t in hist.index],
                    **{k: [rnd(v, 4 if k in ("hp10", "above200", "dd") else 2) for v in hist[k]] for k in keep}},
    }
    out = APP / "public" / "data" / "highlow.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    tmp.replace(out)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(out, APP / "dist" / "data" / out.name)
    on = [r["key"] for r in study if r["now"]]
    mk = payload["dip"]["market"]
    print(f"dip score {mk['score']} ({mk['level']}, {mk['regime']}); sectors: "
          + ", ".join(f"{x['etf']} {x['score']}" for x in payload["dip"]["sectors"]))
    print(f"highlow {payload['as_of']}: {int(L.nh)} highs, {int(L.nl)} lows of {int(L.n)}; "
          f"10-day share of highs {L.hp10:.0%}; {L.above200:.0%} above 200-day; active: {', '.join(on) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
