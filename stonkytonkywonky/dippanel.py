#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "pyarrow", "duckdb", "numpy", "yfinance"]
# ///
"""Daily panel for judging dips: every feature known on day t, and what happened after.

One row per trading day since 1990 for the Nasdaq-100 (the target), with S&P 500 and SOX outcomes.
Features use only information available on the day (FRED weekly and FINRA monthly series are lagged
to their publication). Writes data/dip/panel.parquet, and raw downloads to data/dip/raw/ (refreshed with --refresh, nightly).

Sources: Yahoo chart API (indexes, ETFs, volatility indices, futures), FRED public CSV (rates,
credit, financial conditions, jobless claims), ForwardEstimates data (S&P 1500 member closes for
breadth; reconstruction B for Nasdaq-100 estimates), PositioningLab (FINRA margin debt).
"""

from __future__ import annotations

import io
import json
import time
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "dip" / "raw"
FE = HERE
PL = HERE.parent / "PositioningLab"
OUT = HERE / "data" / "dip" / "panel.parquet"

YAHOO = ["^NDX", "^GSPC", "^SOX", "QQQ", "SPY", "SMH", "^VIX", "^VXN", "^VIX3M", "^VVIX", "^SKEW", "^MOVE",
         "^TNX", "^IRX", "CL=F", "DX-Y.NYB", "HYG", "TLT", "MTUM", "XHB", "XRT", "XLV", "XLU", "XLF", "KRE", "XLP", "^RUT"]
# id: (description, publication lag in days)
FRED = {"BAA10Y": ("Baa corporate minus 10-year Treasury", 1), "DFF": ("Fed funds effective", 1),
        "DFII10": ("10-year TIPS real yield", 1), "T10Y3M": ("10-year minus 3-month", 1),
        "NFCI": ("Chicago Fed financial conditions, weekly", 5), "ICSA": ("Initial jobless claims, weekly", 5),
        "BAMLH0A0HYM2": ("ICE BofA high-yield spread", 1)}


def yahoo(sym: str) -> pd.DataFrame:
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=631152000&period2={int(time.time())}&interval=1d"
    r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    adj = r["indicators"].get("adjclose", [{}])[0].get("adjclose")
    idx = pd.to_datetime(r["timestamp"], unit="s").normalize()
    df = pd.DataFrame({"c": q["close"], "v": q["volume"], "adj": adj if adj else q["close"]}, index=idx)
    return df[~df.index.duplicated(keep="last")].dropna(subset=["c"])


def fred(sid: str) -> pd.Series:
    u = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=1985-01-01"
    t = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=90).read().decode()
    df = pd.read_csv(io.StringIO(t))
    df.columns = ["date", sid]
    df["date"] = pd.to_datetime(df.date)
    return pd.to_numeric(df.set_index("date")[sid], errors="coerce").dropna()


def fetch(refresh: bool) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for s in YAHOO:
        f = RAW / f"y_{s.replace('^', '').replace('=', '').replace('.', '')}.parquet"
        if refresh or not f.exists():
            try:
                yahoo(s).to_parquet(f)
                print("yahoo", s, "ok")
            except Exception as e:  # noqa: BLE001
                print("yahoo", s, "FAILED", e)
            time.sleep(0.5)
    for s in FRED:
        f = RAW / f"f_{s}.parquet"
        if refresh or not f.exists():
            try:
                fred(s).to_frame().to_parquet(f)
                print("fred", s, "ok")
            except Exception as e:  # noqa: BLE001
                print("fred", s, "FAILED", e)


def y(sym: str, col: str = "c") -> pd.Series:
    f = RAW / f"y_{sym.replace('^', '').replace('=', '').replace('.', '')}.parquet"
    return pd.read_parquet(f)[col] if f.exists() else pd.Series(dtype=float)


def fr(sid: str) -> pd.Series:
    f = RAW / f"f_{sid}.parquet"
    if not f.exists():
        return pd.Series(dtype=float)
    s = pd.read_parquet(f)[sid]
    s.index = s.index + pd.Timedelta(days=FRED[sid][1])  # known only after publication
    return s


def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def breadth(idx: pd.DatetimeIndex) -> pd.Series:
    """Share of S&P 1500 members above their 200-day average (today's members: survivorship bias)."""
    c = pd.read_parquet(FE / "data" / "highlow" / "close.parquet")
    ma = c.rolling(200, min_periods=150).mean()
    have = ma.notna() & c.notna()
    return ((c > ma) & have).sum(axis=1).div(have.sum(axis=1)).where(have.sum(axis=1) > 200).reindex(idx, method="pad")


def margin(idx: pd.DatetimeIndex) -> pd.Series:
    con = duckdb.connect(str(PL / "data" / "positioning.duckdb"), read_only=True)
    m = con.execute("select * from margin_stats order by 1").df()
    dcol = [c for c in m.columns if "date" in c or c == "month"][0]
    vcol = [c for c in m.columns if "debit" in c.lower()][0]
    s = m.set_index(pd.to_datetime(m[dcol]))[vcol].astype(float)
    s.index = s.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=21)  # FINRA publishes about three weeks after month-end
    return (s / s.shift(12) - 1).reindex(idx, method="pad")


def estimates(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Nasdaq-100 aggregate forward P/E and three-month estimate change (today's members, method B)."""
    import sys
    sys.path.insert(0, str(FE))
    mem = json.loads((FE / "data" / "fear" / "ndx_members.json").read_text())
    from fear import ndx_estimates  # noqa: PLC0415
    _, pe, rev = ndx_estimates(mem)
    return pd.DataFrame({"fwd_pe": pe.reindex(idx, method="pad"), "est3m": rev.reindex(idx, method="pad")})


def valuation_breadth(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Share of the coverage list's tech names whose forward P/E sits in the bottom 16% of its own trailing
    three years (needs one year), and of those with NTM estimates not lower than three months earlier:
    the screen's "cheap, estimates holding" across tech. Today's names and sectors, reconstruction B."""
    day = pd.read_csv(sorted((FE / "data" / "daily").glob("*.csv"))[-1])
    tech = day[day.sector.isin(["Technology", "Communication Services"])].ticker
    pe, eps = {}, {}
    for tk in tech:
        f = FE / "data" / "history" / "ntm_b" / f"{tk}.csv"
        if f.exists():
            h = pd.read_csv(f, parse_dates=["date"]).set_index("date")
            pe[tk], eps[tk] = h.ntm_pe_b.where(h.ntm_pe_b > 0), h.ntm_eps_b
    PE, EPS = pd.DataFrame(pe).sort_index(), pd.DataFrame(eps).sort_index()
    pct = PE.rolling(756, min_periods=252).rank(pct=True)
    hold = (EPS / EPS.shift(63) - 1) >= 0
    n = pct.notna().sum(axis=1)
    out = pd.DataFrame({"cheap": (pct <= 0.16).sum(axis=1) / n, "cheap_hold": ((pct <= 0.16) & hold).sum(axis=1) / n,
                        "tech_n": n}).where(n >= 20)
    return out.reindex(idx, method="pad")


def build() -> pd.DataFrame:
    c = y("^NDX")
    idx = c.index
    df = pd.DataFrame(index=idx)
    df["ndx"] = c
    df["spx"] = y("^GSPC").reindex(idx).ffill()
    df["sox"] = y("^SOX").reindex(idx).ffill()
    r = c.pct_change()
    hi52 = c.rolling(252, min_periods=60).max()
    df["dd52"] = c / hi52 - 1
    df["dd6m"] = c / c.rolling(126, min_periods=60).max() - 1
    df["ma200"] = c / c.rolling(200).mean() - 1
    df["rsi"] = rsi(c)
    df["since_hi"] = c.groupby((c >= hi52).cumsum()).cumcount()
    df["ret5"], df["ret20"] = c.pct_change(5), c.pct_change(20)
    z = r / r.rolling(252).std()
    vol = y("QQQ", "v").reindex(idx)
    df["cap"] = ((z.rolling(5).min() <= -1.5) & ((vol / vol.rolling(50).mean().shift(1)).rolling(5).max() >= 1.5)).astype(float)
    df["rv20"] = r.rolling(20).std() * np.sqrt(252)
    vxn = y("^VXN").reindex(idx).ffill()
    vix = y("^VIX").reindex(idx).ffill()
    fear = vxn.where(vxn.notna(), vix * 1.25)  # before 2001 VXN does not exist: VIX scaled to its usual ratio
    df["vxn"] = fear
    df["vxn_rel"] = fear / fear.rolling(252).median()
    df["vxn_chg5"] = fear.diff(5)
    df["term"] = (vix / y("^VIX3M").reindex(idx).ffill())
    df["vvix"] = y("^VVIX").reindex(idx).ffill()
    df["skew"] = y("^SKEW").reindex(idx).ffill()
    df["move"] = y("^MOVE").reindex(idx).ffill()
    tnx = y("^TNX").reindex(idx).ffill()
    df["tnx"], df["tnx3m"] = tnx, tnx.diff(63)
    df["oil3m"] = y("CL=F").reindex(idx).ffill().pct_change(63)
    df["dxy3m"] = y("DX-Y.NYB").reindex(idx).ffill().pct_change(63)
    hyg = y("HYG", "adj").reindex(idx).ffill()
    df["hyg_dd"] = hyg / hyg.rolling(63).max() - 1
    tlt = y("TLT", "adj").reindex(idx)
    df["sbcorr"] = r.rolling(63).corr(-tnx.diff())  # long history: Nasdaq returns against falling yields
    df["rate_beta"] = (r * 100).rolling(126).cov(tnx.diff() * 100) / (tnx.diff() * 100).rolling(126).var() * 10
    nob = pd.concat([y(s, "adj").reindex(idx).pct_change(10) for s in ["XHB", "XRT", "XLV", "XLU", "XLF", "KRE", "XLP"]], axis=1).mean(axis=1)
    ai = pd.concat([y(s, "adj").reindex(idx).pct_change(10) for s in ["SMH", "QQQ"]], axis=1).mean(axis=1)
    df["rot_gap"] = (nob - ai) * 100
    df["mom10"] = (y("MTUM", "adj").reindex(idx).pct_change(10) - y("SPY", "adj").reindex(idx).pct_change(10)) * 100
    for sid, name in [("BAA10Y", "baa"), ("DFII10", "real10"), ("T10Y3M", "curve"), ("NFCI", "nfci"), ("DFF", "ff"), ("BAMLH0A0HYM2", "hy")]:
        s = fr(sid).reindex(idx, method="pad")
        df[name] = s
    df["baa3m"] = df.baa.diff(63)
    df["real3m"] = df.real10.diff(63)
    df["ff3m"] = df.ff.diff(63)
    df["hy3m"] = df.hy.diff(63)
    icsa = fr("ICSA").reindex(idx, method="pad")
    df["claims_up"] = icsa.rolling(20).mean() / icsa.rolling(252).min() - 1  # claims off their low: recession risk
    df["breadth200"] = breadth(idx)
    df["margin_yoy"] = margin(idx)
    df = df.join(estimates(idx))
    df = df.join(valuation_breadth(idx))
    # Outcomes
    for name, s in [("ndx", c), ("spx", y("^GSPC").reindex(idx).ffill()), ("sox", y("^SOX").reindex(idx).ffill())]:
        for h, n in (("1m", 21), ("3m", 63), ("12m", 252)):
            df[f"{name}_{h}"] = s.shift(-n) / s - 1
        df[f"{name}_low3m"] = s[::-1].rolling(63, min_periods=1).min()[::-1] / s - 1
    return df


if __name__ == "__main__":
    import sys
    fetch(refresh="--refresh" in sys.argv)
    p = build()
    p.to_parquet(OUT)
    print(p.shape, p.index[0].date(), p.index[-1].date())
    print(p.notna().idxmax().to_string())
