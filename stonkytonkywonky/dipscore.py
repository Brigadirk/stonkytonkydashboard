"""Dip-buying scores for the S&P 500 and its sectors, with what each reading was worth since 1993.

Called by highlow.py, which has the member prices already. The score is how washed out
the market (or a sector) is: the average percentile of a few oversold measures, each
ranked against its own history up to that day only, so the past scores carry no hindsight.

Market measures (the breadth-thrust and capitulation literature, VIX spikes):
  share of stocks above their 50-day and 200-day average (low = washed out),
  most new 52-week lows on one day over 10 sessions, VIX against its one-year median,
  S&P 500 below its 20-day average.
A falling knife is the S&P 500 under its 200-day average while the Baa corporate spread
widened more than 0.25 points in three months: in 2000–02 and 2008 dips bought in that state
kept falling. Faber (2007) on the 200-day trend; credit leads equities in Gilchrist and
Zakrajšek (2012).

Sector measures: the same breadth measures within the sector, and its equal-weighted index
below its 20-day average. Sector returns are the SPDR ETFs (SMH for semiconductors), total
return. Industries trend (Moskowitz and Grinblatt 1999), so a sector that sells off alone
tends to keep lagging; one washed out after a year of losses tends to rebound more than the
market (long-horizon reversal, De Bondt and Thaler 1985). The backtest below checks both.
"""

from __future__ import annotations

import io
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SECTOR_ETF = {
    "Information Technology": "XLK", "Semiconductors": "SMH", "Communication Services": "XLC",
    "Consumer Discretionary": "XLY", "Financials": "XLF", "Health Care": "XLV", "Industrials": "XLI",
    "Energy": "XLE", "Materials": "XLB", "Consumer Staples": "XLP", "Utilities": "XLU", "Real Estate": "XLRE",
}
HORIZONS = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}
MIN_HISTORY = 504  # two years of readings before a percentile counts
LEVELS = [(90, "washout"), (80, "deep"), (60, "dip"), (0, "none")]
KNIFE_WIDEN = 0.25  # Baa–Treasury spread points over 63 sessions
SECTOR_HISTORY_DAYS = 1830


def _get(url: str, ua: str = "Mozilla/5.0") -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=40) as r:
        return r.read()


def etf_prices(index: pd.DatetimeIndex, store: Path) -> pd.DataFrame:
    """Dividend-adjusted closes for SPY and the sector ETFs; the stored copy covers a failed fetch."""
    old = pd.read_parquet(store) if store.exists() else pd.DataFrame()
    cols = {}
    for s in ["SPY", *SECTOR_ETF.values()]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1=631152000&period2={int(time.time())}&interval=1d&events=div"
        try:
            res = json.loads(_get(url))["chart"]["result"][0]
            tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
            px = res["indicators"]["adjclose"][0]["adjclose"]
            ser = pd.Series(px, index=pd.to_datetime([datetime.fromtimestamp(t, tz).date() for t in res["timestamp"]]), dtype="float64")
            cols[s] = ser[~ser.index.duplicated(keep="last")]
        except Exception:  # noqa: BLE001 — keep the stored series for this one
            if s in old.columns:
                cols[s] = old[s].dropna()
        time.sleep(0.3)
    df = pd.DataFrame(cols)
    df.to_parquet(store)
    return df.reindex(index)


def baa_spread(index: pd.DatetimeIndex, store: Path) -> pd.Series:
    """Moody's Baa corporate yield minus the 10-year Treasury (FRED BAA10Y), daily since 1986."""
    try:
        raw = _get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAA10Y&cosd=1986-01-01", ua="curl/8")
        s = pd.read_csv(io.BytesIO(raw), index_col=0, parse_dates=True).iloc[:, 0].apply(pd.to_numeric, errors="coerce")
        s.to_frame("baa10y").to_parquet(store)
    except Exception:  # noqa: BLE001
        s = pd.read_parquet(store)["baa10y"]
    return s.reindex(index.union(s.index)).ffill().reindex(index)


def _pct(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.apply(lambda s: s.expanding(min_periods=MIN_HISTORY).rank(pct=True))


def _breadth(C: pd.DataFrame, Ll: pd.DataFrame) -> pd.DataFrame:
    ma50, ma200 = C.rolling(50, min_periods=50).mean(), C.rolling(200, min_periods=200).mean()
    prior_lo = Ll.shift(1).rolling(251, min_periods=251).min()
    valid = prior_lo.notna() & C.notna()
    return pd.DataFrame({
        "above50": ((C > ma50) & ma50.notna()).sum(axis=1) / ma50.notna().sum(axis=1).replace(0, np.nan),
        "above200": ((C > ma200) & ma200.notna()).sum(axis=1) / ma200.notna().sum(axis=1).replace(0, np.nan),
        "lows10": (((Ll < prior_lo) & valid).sum(axis=1) / valid.sum(axis=1).replace(0, np.nan)).rolling(10).max(),
        "members": valid.sum(axis=1),
    })


def level(score: float | None) -> str | None:
    if score is None or not np.isfinite(score):
        return None
    return next(name for floor, name in LEVELS if score >= floor)


def _fwd(px: pd.Series) -> dict[str, pd.Series]:
    return {k: px.shift(-n) / px - 1 for k, n in HORIZONS.items()}


def _rnd(v, k=4):
    return None if v is None or not np.isfinite(v) else round(float(v), k)


def _stats(x: pd.DataFrame, rel: bool = False) -> dict:
    out = {"days": int(len(x))}
    for k in HORIZONS:
        v = x["f" + k].dropna()
        out["med_" + k], out["up_" + k] = (_rnd(v.median()), _rnd((v > 0).mean(), 3)) if len(v) >= 20 else (None, None)
        if rel:
            r = x["x" + k].dropna()
            out["rel_" + k], out["beat_" + k] = (_rnd(r.median()), _rnd((r > 0).mean(), 3)) if len(r) >= 20 else (None, None)
    key = "x12m" if rel else "f12m"
    for era, sl in (("early", slice(None, "2008")), ("late", slice("2009", None))):
        v = x.loc[sl, key].dropna()
        out[f"{era}_12m"] = _rnd(v.median()) if len(v) >= 20 else None
    if "pain" in x:
        out["pain3m"] = _rnd(x.pain.median())
    return out


def build(c: pd.DataFrame, l: pd.DataFrame, uni: pd.DataFrame, store: Path) -> dict:
    idx = c.index
    stocks = [s for s in uni.symbol if s in c.columns]
    etf = etf_prices(idx, store / "etf.parquet")
    baa = baa_spread(idx, store / "baa10y.parquet")
    spx, vix, spy = c["^GSPC"], c["^VIX"], etf["SPY"]

    # ---- market ----
    b = _breadth(c[stocks], l[stocks].fillna(c[stocks]))
    comp = pd.DataFrame({
        "above50": -b.above50, "above200": -b.above200, "lows10": b.lows10,
        "fear": vix / vix.rolling(252, min_periods=126).median(),
        "stretch": -(spx / spx.rolling(20).mean() - 1),
    })[b.members >= 300]
    P = _pct(comp)
    score = P.mean(axis=1, skipna=False) * 100
    downtrend = spx < spx.rolling(200).mean()
    widen = baa - baa.shift(63)
    regime = pd.Series(np.where(downtrend & (widen > KNIFE_WIDEN), "knife", np.where(downtrend, "down", "up")), index=idx)
    m = pd.DataFrame({"score": score, "regime": regime.reindex(score.index), **{"f" + k: v.reindex(score.index) for k, v in _fwd(spy).items()}})
    m["pain"] = (spy[::-1].rolling(63, min_periods=1).min()[::-1].shift(-1) / spy - 1).reindex(score.index)
    m = m.dropna(subset=["score"])
    m["level"] = m.score.map(level)
    cells = []
    for reg in ("up", "down", "knife"):
        for _, lv in LEVELS:
            x = m[(m.regime == reg) & (m.level == lv)]
            if len(x):
                cells.append({"regime": reg, "level": lv, **_stats(x)})
    allm = _stats(m)
    last = m.index[-1]
    mkt_score = _rnd(m.score.iloc[-1], 1)
    hist = m.loc[m.index >= m.index[-1] - pd.Timedelta(days=365 * 34)]
    market = {
        "score": mkt_score, "level": m.level.iloc[-1], "regime": m.regime.iloc[-1],
        "components": {k: {"value": _rnd(comp[k].iloc[-1]), "pct": _rnd(100 * P[k].iloc[-1], 1)} for k in comp.columns},
        "spx_vs_200": _rnd(spx.iloc[-1] / spx.rolling(200).mean().iloc[-1] - 1),
        "baa": _rnd(baa.iloc[-1], 2), "baa_chg_3m": _rnd(widen.iloc[-1], 2),
        "cells": cells, "all": allm,
        "history": {"dates": [t.date().isoformat() for t in hist.index], "score": [_rnd(v, 1) for v in hist.score],
                    "spx": [_rnd(v, 1) for v in spx.reindex(hist.index)]},
    }

    # ---- sectors ----
    rows, sectors = [], []
    for sec, tk in SECTOR_ETF.items():
        mem = uni[uni.industry.str.startswith("Semiconductor")].symbol if sec == "Semiconductors" else uni[uni.sector == sec].symbol
        mem = [s for s in mem if s in c.columns]
        C = c[mem]
        sb = _breadth(C, l[mem].fillna(C))
        ew = (1 + C.pct_change(fill_method=None).clip(-0.5, 1).mean(axis=1).fillna(0)).cumprod()
        sc = pd.DataFrame({"above50": -sb.above50, "above200": -sb.above200, "lows10": sb.lows10,
                           "stretch": -(ew / ew.rolling(20).mean() - 1)})[sb.members >= 15]
        SP = _pct(sc)
        s_score = SP.mean(axis=1, skipna=False) * 100
        px = etf[tk]
        mom12 = px / px.shift(252) - 1
        mom12 = mom12.fillna(ew / ew.shift(252) - 1)  # XLC and XLRE are young; the members' index fills in
        d = pd.DataFrame({"score": s_score, "mkt": score.reindex(s_score.index), "mom12": mom12.reindex(s_score.index)})
        for k, v in _fwd(px).items():
            d["f" + k] = v.reindex(d.index)
            d["x" + k] = d["f" + k] - _fwd(spy)[k].reindex(d.index)
        d = d.dropna(subset=["score"])
        d["verdict"] = np.select(
            [(d.score >= 85) & (d.mom12 <= -0.20), (d.score >= 85) & (d.mkt >= 80), d.score >= 85, d.score >= 60],
            ["beaten", "with_market", "alone", "dip"], "none")
        d["sector"] = sec
        rows.append(d)
        L = d.iloc[-1]
        h = d.loc[d.index >= d.index[-1] - pd.Timedelta(days=SECTOR_HISTORY_DAYS)]
        sectors.append({
            "sector": sec, "etf": tk, "members": int(sb.members.iloc[-1]), "score": _rnd(L.score, 1), "verdict": L.verdict,
            "above50": _rnd(sb.above50.iloc[-1]), "above200": _rnd(sb.above200.iloc[-1]), "lows10": _rnd(sb.lows10.iloc[-1]),
            "mom12": _rnd(L.mom12), "chg_1m": _rnd(px.iloc[-1] / px.iloc[-22] - 1),
            "history": {"dates": [t.date().isoformat() for t in h.index], "score": [_rnd(v, 1) for v in h.score],
                        "price": [_rnd(v, 2) for v in px.reindex(h.index)]},
        })
    D = pd.concat(rows).sort_index()
    verdicts = [{"verdict": v, **_stats(D[D.verdict == v], rel=True)} for v in ("beaten", "with_market", "alone", "dip", "none")]
    return {"as_of": last.date().isoformat(), "market": market, "sectors": sectors, "sector_verdicts": verdicts}
