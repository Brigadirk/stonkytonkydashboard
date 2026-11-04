#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Is this dip buyable? A verdict from every past dip since 1990, written to app/public/data/dipjudge.json.

Reads data/dip/panel.parquet (dippanel.py). A dip day: the index at least 7% (Nasdaq-100) or 10%
(SOX, which swings more) below its 52-week high. Each brake is a condition under which past dips
were worse buys; the thresholds are round numbers set by hand from the first backtest (October 2026),
not fitted, but they were chosen on this same history, so the tables flatter them somewhat.
Fear itself is not a brake: the VXN level barely separated good dips from bad ones.

Outcomes: higher three months and a year later; "fell 10% more": the lowest close in the next
three months at least 10% under that day's. Days inside one episode (gaps under 30 days) overlap.
Analogs: the past dip days closest to today on standardized features, one per episode.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "data" / "dip" / "panel.parquet"
APP = ROOT / "app"
OUT = APP / "public" / "data" / "dipjudge.json"

TARGETS = {"ndx": ("Nasdaq-100", -0.07), "sox": ("Semiconductors (SOX)", -0.10)}
# key: (label, feature, test that means the brake is ON, how today's value is shown)
BRAKES = [
    ("estimates", "Estimates not rising", "est3m", lambda v: v <= 3, "Nasdaq-100 estimates {v:+.1f}% in 3 months (brake: +3% or less)"),
    ("bonds", "Bond market volatile", "move", lambda v: v >= 110, "MOVE {v:.0f} (brake: 110 or more)"),
    ("bear", "Bear-market depth", "dd", lambda v: v <= -0.20, "{v:+.0%} from the 52-week high (brake: 20% or more down)"),
    ("credit", "Credit widening", "baa3m", lambda v: v >= 0.30, "Baa spread {v:+.2f} points in 3 months (brake: +0.30 or more)"),
    ("oil", "Oil shock", "oil3m", lambda v: v >= 0.25, "Oil {v:+.0%} in 3 months (brake: +25% or more)"),
    ("rates", "Rates surging", "tnx3m", lambda v: v >= 0.50, "10-year yield {v:+.2f} points in 3 months (brake: +0.50 or more)"),
    ("recession", "Jobless claims rising", "claims_up", lambda v: v >= 0.20, "Claims {v:+.0%} above their 1-year low (brake: +20% or more)"),
]
# Tailwinds: conditions under which past dips were better buys; shown with their record, not counted as brakes.
SUPPORTS = [
    ("value", "Tech names cheap with estimates holding", "cheap_hold", lambda v: v >= 0.34,
     "{v:.0%} of the coverage list's tech names cheap against their own 3 years with estimates holding (tailwind: 34% or more)"),
]
ANALOG = ["dd", "ma", "rsi", "vxn", "est3m", "fwd_pe", "move", "tnx3m", "baa3m", "oil3m", "nfci", "claims_up", "breadth200", "margin_yoy", "sbcorr"]


def num(v, d=3):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) or pd.isna(v) else round(float(v), d)


def stats(x: pd.DataFrame, t: str) -> dict:
    y3 = x[f"{t}_3m"].dropna()
    y12 = x[f"{t}_12m"].dropna()
    lo = x.loc[y3.index, f"{t}_low3m"]
    return {"days": int(len(y3)), "episodes": int(x.loc[y3.index, "ep"].nunique()) if len(y3) else 0,
            "up3m": num((y3 > 0).mean()) if len(y3) else None, "med3m": num(y3.median()) if len(y3) else None,
            "up12m": num((y12 > 0).mean()) if len(y12) else None, "bad10": num((lo < -0.10).mean()) if len(y3) else None}


def judge(P: pd.DataFrame, t: str) -> dict:
    label, cut = TARGETS[t]
    c = P[t].dropna()
    df = P.loc[c.index].copy()
    df["dd"] = c / c.rolling(252, min_periods=60).max() - 1
    df["ma"] = c / c.rolling(200).mean() - 1
    d = c.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    df["rsi"] = 100 - 100 / (1 + up / dn)
    for k, _, f, test, _ in BRAKES:
        df[f"b_{k}"] = df[f].map(lambda v, test=test: np.nan if pd.isna(v) else float(test(v)))
    dip = df[df.dd <= cut].copy()
    dip["ep"] = (dip.index.to_series().diff().dt.days > 30).cumsum()

    brakes = []
    today = df.iloc[-1]
    for k, name, f, test, fmt_ in BRAKES:
        x = dip.dropna(subset=[f"b_{k}"])
        v = today[f]
        on, off = stats(x[x[f"b_{k}"] == 1], t), stats(x[x[f"b_{k}"] == 0], t)
        # A brake counts only if past dips with it on did clearly worse over three months (5 points or more).
        counted = on["up3m"] is not None and off["up3m"] is not None and on["episodes"] >= 5 and on["up3m"] <= off["up3m"] - 0.05
        brakes.append({"key": k, "name": name, "since": int(x.index[0].year) if len(x) else None, "counted": bool(counted),
                       "on": None if pd.isna(v) else bool(test(v)), "now": None if pd.isna(v) else fmt_.format(v=v),
                       "when_on": on, "when_off": off})
    supports = []
    for k, name, f, test, fmt_ in SUPPORTS:
        x = dip.dropna(subset=[f])
        v = today[f]
        on_m = x[f].map(test)
        on, off = stats(x[on_m], t), stats(x[~on_m], t)
        works = on["up3m"] is not None and off["up3m"] is not None and on["episodes"] >= 5 and on["up3m"] >= off["up3m"] + 0.05
        supports.append({"key": k, "name": name, "since": int(x.index[0].year) if len(x) else None, "counted": bool(works),
                         "on": None if pd.isna(v) else bool(test(v)), "now": None if pd.isna(v) else fmt_.format(v=v),
                         "when_on": on, "when_off": off})
    keys = [f"b_{b['key']}" for b in brakes if b["counted"]]
    df["fails"] = df[keys].sum(axis=1, min_count=1)
    dip["fails"] = df.loc[dip.index, "fails"]
    combo = []
    for lab, m in (("none", dip.fails == 0), ("one", dip.fails == 1), ("two or more", dip.fails >= 2)):
        row = {"brakes": lab, **stats(dip[m], t)}
        for era, em in (("before 2010", dip.index.year < 2010), ("2010 on", dip.index.year >= 2010)):
            row[era] = stats(dip[m & em], t)
        combo.append(row)
    base = stats(dip, t)

    # Analogs: nearest past dip days on standardized features, one per episode, finished outcomes only.
    past = dip[dip.index < df.index[-1] - pd.Timedelta(days=95)].dropna(subset=[f"{t}_3m"])
    use = [f for f in ANALOG if pd.notna(today[f])]
    Z = past[use]
    mu, sd = Z.mean(), Z.std().replace(0, 1)
    dist = (((Z - mu) / sd - (today[use] - mu) / sd) ** 2).mean(axis=1, skipna=True) ** 0.5
    dist = dist.where(Z.notna().mean(axis=1) >= 0.6)
    near = past.assign(dist=dist).dropna(subset=["dist"]).sort_values("dist").groupby("ep").head(1).head(10)
    analogs = [{"date": i.strftime("%Y-%m-%d"), "dist": num(r.dist, 2), "dd": num(r.dd), "vxn": num(r.vxn, 1), "est3m": num(r.est3m, 1),
                "fails": None if pd.isna(r.fails) else int(r.fails), "r1m": num(r[f"{t}_1m"]), "r3m": num(r[f"{t}_3m"]), "r12m": num(r[f"{t}_12m"]),
                "low3m": num(r[f"{t}_low3m"])} for i, r in near.iterrows()]
    a3 = [a["r3m"] for a in analogs if a["r3m"] is not None]

    tail_on = [s for s in supports if s["on"] and s["counted"]]
    # Dips in today's brake state with and without the tailwind, so the verdict can say what it adds.
    nf = len([b for b in brakes if b["on"] and b["counted"]])
    same = dip[(dip.fails == nf) if nf < 2 else (dip.fails >= 2)].dropna(subset=["cheap_hold"])
    tail_split = {"with": stats(same[same.cheap_hold >= 0.34], t), "without": stats(same[same.cheap_hold < 0.34], t)} if len(same) else None
    in_dip = bool(today.dd <= cut)
    fails = [b for b in brakes if b["on"] and b["counted"]]
    # The verdict is only as good as the brakes' record: dips with none on should have beaten dips with two or more.
    gap = None if combo[0]["up3m"] is None or combo[2]["up3m"] is None else combo[0]["up3m"] - combo[2]["up3m"]
    reliable = gap is not None and gap >= 0.10
    row = combo[0 if not fails else 1 if len(fails) == 1 else 2]
    if not in_dip:
        verdict, level = f"No dip: {label} is {today.dd:+.0%} from its high (a dip here starts at {cut:.0%}).", "none"
    elif not fails:
        verdict, level = "Buyable: a dip with none of the brakes on.", "buy"
    elif len(fails) == 1:
        verdict, level = f"Buyable with care: one brake on ({fails[0]['name'].lower()}).", "care"
    else:
        verdict, level = f"Not buyable yet: {len(fails)} brakes on ({', '.join(b['name'].lower() for b in fails)}).", "wait"
    if in_dip and tail_on:
        verdict += f" Tailwind: {tail_on[0]['name'].lower()}."
    return {"label": label, "cut": cut, "date": df.index[-1].strftime("%Y-%m-%d"), "dd": num(today.dd), "in_dip": in_dip,
            "level": level, "verdict": verdict, "reliable": reliable, "supports": supports, "tail_split": tail_split, "separation": num(gap), "row": row, "base": base, "brakes": brakes, "combo": combo,
            "analogs": analogs, "analogs_up3m": num(np.mean([v > 0 for v in a3])) if a3 else None,
            "analogs_med3m": num(float(np.median(a3))) if a3 else None, "analog_features": use}


def main() -> int:
    P = pd.read_parquet(PANEL)
    payload = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "as_of": P.index[-1].strftime("%Y-%m-%d")}
    for t in TARGETS:
        payload[t] = judge(P, t)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    tmp.replace(OUT)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(OUT, APP / "dist" / "data" / OUT.name)
    for t in TARGETS:
        j = payload[t]
        print(j["label"], j["verdict"], j["row"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
