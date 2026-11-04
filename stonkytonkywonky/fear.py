#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance", "pandas"]
# ///
"""Fear, flows and rates: four views for the app, written to app/public/data/fear.json.

nasdaq    Days when Nasdaq volatility (VXN) is above 30 and the Nasdaq-100 ETF is at least 10%
          below its six-month high, split by whether forward earnings estimates were rising,
          with what QQQ did 1, 3 and 12 months later. Estimates are the Nasdaq-100's current
          members summed from reconstruction B (data/history/ntm_b) at today's share counts:
          today's members carry survivorship bias before about 2015, and B moves once a quarter,
          so it reacts late to a sudden shock (it still showed rising estimates in March 2020).
rotation  The unloved sectors (homebuilders, retail, health care, utilities, financials,
          regional banks, staples) against chips and the Nasdaq over 10 days, and the momentum
          factor (MTUM) against the S&P 500: pods de-grossing look like this.
rates     Bond volatility (MOVE), the 10-year yield, the stock-bond correlation (SPY against TLT)
          and how much QQQ moves per 10 bp on the 10-year.
plumbing  Overnight funding: SOFR against interest on reserves, the Fed's reverse repo and standing
          repo facilities (NY Fed), bank reserves (Fed H.4.1) and the Treasury's cash (TGA).
          IORB is taken as the top of the fed funds range less 10 bp, the Fed's setting since 2023.

Each view stands alone; one that fails tonight keeps last night's version.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STORE = DATA / "fear"
APP = ROOT / "app"
OUT = APP / "public" / "data" / "fear.json"
UA = "StonkyTonkyWonky research tool"

NOBODY = ["XHB", "XRT", "XLV", "XLU", "XLF", "KRE", "XLP"]
AI = ["SMH", "QQQ"]
TICKERS = NOBODY + AI + ["^VXN", "MTUM", "SPY", "TLT", "^TNX", "^MOVE"]
H = {"1m": 21, "3m": 63, "12m": 252}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def num(v, d=2):
    return None if v is None or not np.isfinite(v) else round(float(v), d)


def series(s: pd.Series, d=2) -> dict:
    s = s.dropna()
    return {"dates": [x.strftime("%Y-%m-%d") for x in s.index], "values": [num(v, d) for v in s]}


def prices() -> pd.DataFrame:
    px = yf.download(TICKERS, start="2000-01-01", progress=False, auto_adjust=True)["Close"]
    return px.dropna(how="all")


# ---------- nasdaq: fear with rising estimates ----------

def members() -> list[str]:
    cache = STORE / "ndx_members.json"
    try:
        rows = json.loads(get("https://api.nasdaq.com/api/quote/list-type/nasdaq100"))["data"]["data"]["rows"]
        syms = sorted(r["symbol"] for r in rows)
        if len(syms) > 90:
            cache.write_text(json.dumps(syms))
            return syms
    except Exception as e:  # noqa: BLE001
        print(f"members fetch failed ({e}); using cache")
    return json.loads(cache.read_text())


def ndx_estimates(mem: list[str]):
    """Aggregate forward P/E and NTM earnings of today's members (earnings at today's share counts)."""
    daily = sorted((DATA / "daily").glob("*.csv"))[-1]
    day = pd.read_csv(daily)
    day = day[day.ticker.isin(mem) & (day.currency == "USD")].dropna(subset=["market_cap", "ntm_pe", "shares"])
    live_pe = day.market_cap.sum() / (day.market_cap / day.ntm_pe).sum()
    E, M = {}, {}
    for t, sh in day.set_index("ticker").shares.items():
        f = DATA / "history" / "ntm_b" / f"{t}.csv"
        if not f.exists():
            continue
        h = pd.read_csv(f, parse_dates=["date"]).set_index("date")
        E[t], M[t] = h.ntm_eps_b * sh, h.close * sh
    E, M = pd.DataFrame(E).sort_index(), pd.DataFrame(M).sort_index()
    both = E.notna() & M.notna()
    pe = M.where(both).sum(axis=1) / E.where(both).sum(axis=1)
    # Estimate change over 63 trading days, among names present at both ends.
    Eb = E.shift(63)
    ok = E.notna() & Eb.notna()
    rev = (E.where(ok).sum(axis=1) / Eb.where(ok).sum(axis=1) - 1) * 100
    return {"live_pe": float(live_pe), "date": daily.stem, "n": int(len(day)), "members": len(mem)}, pe, rev


def nasdaq_view(px: pd.DataFrame) -> dict:
    est, pe, rev = ndx_estimates(members())
    v, q = px["^VXN"].dropna(), px.QQQ.dropna()
    idx = v.index.intersection(q.index)
    v, q = v[idx], q[idx]
    dd = (q / q.rolling(126, min_periods=1).max() - 1) * 100
    pe, rev = pe.reindex(idx, method="pad"), rev.reindex(idx, method="pad")
    fwd = {k: (q.shift(-n) / q - 1) * 100 for k, n in H.items()}
    low = pd.Series([(q.iloc[i:i + 63].min() / q.iloc[i] - 1) * 100 for i in range(len(q))], index=idx)
    state = (v > 30) & (dd <= -10) & (idx >= "2006-06-01")
    df = pd.DataFrame({"vxn": v, "dd": dd, "pe": pe, "rev": rev, "low": low, **fwd})[state]
    df["ep"] = (df.index.to_series().diff().dt.days > 30).cumsum()

    def stats(x: pd.DataFrame) -> dict:
        out = {"days": int(len(x)), "episodes": int(x.ep.nunique())}
        for k in H:
            y = x[k].dropna()
            out[k] = {"n": int(len(y)), "up": num((y > 0).mean(), 3) if len(y) else None, "median": num(y.median(), 1) if len(y) else None}
        y = x.dropna(subset=["3m"])
        out["further_drop"] = {"median": num(y.low.median(), 1), "worst": num(y.low.min(), 1)} if len(y) else None
        return out

    yr = df.index.year
    periods = [("2010 to now, excluding 2022", (yr >= 2010) & (yr != 2022)), ("2006 to 2009", yr < 2010), ("2022", yr == 2022)]
    groups = []
    for label, m in periods:
        for trend, t in (("rising", df.rev > 3), ("flat or falling", df.rev <= 3)):
            x = df[m & t]
            if len(x):
                groups.append({"period": label, "estimates": trend, **stats(x)})
    episodes = []
    for _, g in df.groupby("ep"):
        episodes.append({"start": g.index[0].strftime("%Y-%m-%d"), "end": g.index[-1].strftime("%Y-%m-%d"), "days": int(len(g)),
                         "pe": num(g.pe.median(), 1), "rev": num(g.rev.median(), 1),
                         **{k: num(g[k].median(), 1) for k in H}, "further_drop": num(g.low.median(), 1)})
    last = idx[-1]
    cur = {"date": last.strftime("%Y-%m-%d"), "vxn": num(v.iloc[-1], 1), "dd": num(dd.iloc[-1], 1),
           "pe": num(est["live_pe"], 1), "pe_date": est["date"], "rev": num(rev.dropna().iloc[-1], 1),
           "coverage": f"{est['n']} of {est['members']}"}
    cur["checks"] = {"vxn": cur["vxn"] > 30, "dd": cur["dd"] <= -10, "rev": cur["rev"] > 3}
    tail = idx[-756:]
    chart = {"dates": [x.strftime("%Y-%m-%d") for x in tail], "vxn": [num(x, 1) for x in v[tail]],
             "dd": [num(x, 1) for x in dd[tail]], "rev": [num(x, 1) for x in rev.reindex(tail)]}
    return {"current": cur, "groups": groups, "episodes": episodes, "chart": chart}


# ---------- rotation: unloved sectors against AI, momentum unwinds ----------

def rotation_view(px: pd.DataFrame) -> dict:
    p = px[NOBODY + AI + ["MTUM", "SPY"]].dropna(subset=AI)
    r = p.pct_change(10, fill_method=None)
    rest = r[NOBODY].mean(axis=1) * 100
    gap = rest - r[AI].mean(axis=1) * 100
    mom = (r.MTUM - r.SPY) * 100
    smh = r.SMH * 100
    df = pd.DataFrame({"gap": gap, "rest": rest, "smh": smh, "mom": mom}).dropna(subset=["gap"])
    hit = df[(df.gap > 6) & (df.rest > 0)]
    S = p.SMH
    episodes, cur_ep = [], []
    for d in hit.index:
        if cur_ep and (d - cur_ep[-1]).days > 25:
            episodes.append(cur_ep)
            cur_ep = []
        cur_ep.append(d)
    if cur_ep:
        episodes.append(cur_ep)
    rows = []
    for g in episodes:
        pk = df.loc[g].gap.idxmax()
        i = S.index.get_loc(pk)
        after = {k: num((S.iloc[i + n] / S.iloc[i] - 1) * 100, 0) if i + n < len(S) else None for k, n in H.items()}
        rows.append({"start": g[0].strftime("%Y-%m-%d"), "end": g[-1].strftime("%Y-%m-%d"), "peak": pk.strftime("%Y-%m-%d"),
                     "rest": num(df.rest[pk], 1), "smh": num(df.smh[pk], 1), "mom": num(df.mom[pk], 1),
                     "further_drop": num((S.iloc[i:i + 21].min() / S.iloc[i] - 1) * 100, 0), **after})
    per_year = {int(k): int(n) for k, n in hit.groupby(hit.index.year).size().items()}
    last = df.iloc[-1]
    tail = df.index[-504:]
    return {"current": {"date": df.index[-1].strftime("%Y-%m-%d"), "gap": num(last.gap, 1), "rest": num(last.rest, 1),
                        "smh": num(last.smh, 1), "mom": num(last.mom, 1)},
            "per_year": per_year, "episodes": rows[-14:],
            "chart": {"dates": [x.strftime("%Y-%m-%d") for x in tail], "gap": [num(x, 1) for x in df.gap[tail]], "mom": [num(x, 1) for x in df.mom[tail]]}}


# ---------- rates as a source of volatility ----------

def rates_view(px: pd.DataFrame) -> dict:
    out = {}
    for k, t in (("move", "^MOVE"), ("ten", "^TNX")):
        s = px[t].dropna()
        yr = s.iloc[-252:]
        out[k] = {"value": num(s.iloc[-1], 2), "ago_3m": num(s.iloc[-64], 2), "pct_1y": num((yr < s.iloc[-1]).mean() * 100, 0)}
    ret = pd.DataFrame({"spy": px.SPY.pct_change(fill_method=None), "tlt": px.TLT.pct_change(fill_method=None)}).dropna()
    by_year = ret.groupby(ret.index.year).apply(lambda x: x.spy.corr(x.tlt))
    roll = ret.spy.rolling(63).corr(ret.tlt)
    out["corr"] = {"by_year": {int(k): num(v, 2) for k, v in by_year.items()}, "now_3m": num(roll.iloc[-1], 2),
                   "chart": series(roll.iloc[-756:], 2)}
    qy = pd.DataFrame({"q": px.QQQ.pct_change(fill_method=None) * 100, "y": px["^TNX"].diff() * 100}).dropna()
    cov = qy.q.rolling(126).cov(qy.y)
    beta10 = cov / qy.y.rolling(126).var() * 10
    yb = {}
    for y, x in qy.groupby(qy.index.year):
        if len(x) > 50 and y >= 2010:
            yb[int(y)] = num(np.polyfit(x.y, x.q, 1)[0] * 10, 2)
    out["beta"] = {"now_6m": num(beta10.iloc[-1], 2), "by_year": yb, "chart": series(beta10.iloc[-756:], 2)}
    return out


# ---------- plumbing ----------

NYFED = "https://markets.newyorkfed.org/api"


def plumbing_view() -> dict:
    sofr = json.loads(get(f"{NYFED}/rates/secured/sofr/last/260.json"))["refRates"]
    effr = json.loads(get(f"{NYFED}/rates/unsecured/effr/last/1.json"))["refRates"][0]
    top, bottom = effr["targetRateTo"], effr["targetRateFrom"]
    iorb = round(top - 0.10, 2)
    sofr = sorted(sofr, key=lambda r: r["effectiveDate"])
    start = (date.today() - timedelta(days=370)).isoformat()
    rrp = json.loads(get(f"{NYFED}/rp/reverserepo/propositions/search.json?startDate={start}"))["repo"]["operations"]
    rrp_day: dict[str, float] = {}
    for o in rrp:
        rrp_day[o["operationDate"]] = rrp_day.get(o["operationDate"], 0) + o.get("totalAmtAccepted", 0) / 1e9
    srf = json.loads(get(f"{NYFED}/rp/repo/all/results/last/120.json"))["repo"]["operations"]
    srf_day: dict[str, float] = {}
    for o in srf:
        srf_day[o["operationDate"]] = srf_day.get(o["operationDate"], 0) + o.get("totalAmtAccepted", 0) / 1e9
    srf_days = sorted(srf_day)[-30:]
    out = {"range": [bottom, top], "iorb": iorb,
           "sofr": {"date": sofr[-1]["effectiveDate"], "value": sofr[-1]["percentRate"], "p99": sofr[-1]["percentPercentile99"],
                    "volume_bn": sofr[-1]["volumeInBillions"], "spread_bp": round((sofr[-1]["percentRate"] - iorb) * 100)},
           "sofr_chart": {"dates": [r["effectiveDate"] for r in sofr], "spread": [round((r["percentRate"] - iorb) * 100) for r in sofr],
                          "p99": [round((r["percentPercentile99"] - iorb) * 100) if r.get("percentPercentile99") is not None else None for r in sofr]},
           "rrp": {"date": max(rrp_day), "value_bn": round(rrp_day[max(rrp_day)], 1),
                   "chart": {"dates": sorted(rrp_day), "values": [round(rrp_day[d], 1) for d in sorted(rrp_day)]}},
           "srf": {"max_30_bn": round(max(srf_day[d] for d in srf_days), 2), "last_bn": round(srf_day[srf_days[-1]], 2), "last_date": srf_days[-1]}}
    # The iorb shortcut only holds while SOFR trades inside the range; flag it if not.
    out["iorb_note"] = "IORB taken as the top of the range less 10 bp."
    # Fed H.4.1: reserves and the TGA, weekly; history accumulates from the first run.
    try:
        t = unescape(re.sub(r"<[^>]+>", " ", get("https://www.federalreserve.gov/releases/h41/current/h41.htm").decode("utf-8", "ignore")))
        t = re.sub(r"\s+", " ", t)
        week = re.search(r"Week ended ([A-Z][a-z]{2} \d{1,2}, \d{4})", t).group(1)
        week = datetime.strptime(week, "%b %d, %Y").strftime("%Y-%m-%d")
        reserves = float(re.search(r"Reserve balances with Federal Reserve Banks ([\d,]+)", t).group(1).replace(",", "")) / 1000
        hist_f = STORE / "h41.json"
        hist = json.loads(hist_f.read_text()) if hist_f.exists() else {}
        hist[week] = {"reserves_bn": round(reserves, 1)}
        hist_f.write_text(json.dumps(dict(sorted(hist.items())), indent=1))
        weeks = sorted(hist)
        prev = hist[weeks[-2]]["reserves_bn"] if len(weeks) > 1 else None
        out["reserves"] = {"week": week, "value_bn": round(reserves, 1), "change_bn": None if prev is None else round(reserves - prev, 1)}
    except Exception as e:  # noqa: BLE001
        print(f"h41 failed ({e})")
    try:
        flt = urllib.parse.quote("account_type:eq:Treasury General Account (TGA) Closing Balance", safe=":,")
        url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"
               f"?fields=record_date,open_today_bal&filter={flt},record_date:gte:{start}&sort=record_date&page%5Bsize%5D=400")
        rows = json.loads(get(url))["data"]
        dates = [r["record_date"] for r in rows]
        vals = [round(float(r["open_today_bal"]) / 1000, 1) for r in rows]
        out["tga"] = {"date": dates[-1], "value_bn": vals[-1], "chart": {"dates": dates, "values": vals}}
    except Exception as e:  # noqa: BLE001
        print(f"tga failed ({e})")
    return out


def main() -> int:
    STORE.mkdir(parents=True, exist_ok=True)
    payload: dict = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    failed = []
    try:
        px = prices()
    except Exception as e:  # noqa: BLE001
        print(f"prices failed ({e})")
        px = None
    views = [("plumbing", plumbing_view)]
    if px is not None:
        views = [("nasdaq", lambda: nasdaq_view(px)), ("rotation", lambda: rotation_view(px)), ("rates", lambda: rates_view(px))] + views
    for label, fn in views:
        try:
            payload[label] = fn()
        except Exception as e:  # noqa: BLE001
            failed.append(label)
            print(f"{label} failed ({e!r})"[:300], flush=True)
    if OUT.exists():  # keep last night's view of anything that failed
        old = json.loads(OUT.read_text(encoding="utf-8"))
        for label in ("nasdaq", "rotation", "rates", "plumbing"):
            payload.setdefault(label, old.get(label))
    payload["failed"] = failed
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    tmp.replace(OUT)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(OUT, APP / "dist" / "data" / OUT.name)
    print(f"fear.json written; failed: {failed or 'none'}")
    return 1 if len(failed) == 4 else 0


if __name__ == "__main__":
    sys.exit(main())
