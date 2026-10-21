#!/usr/bin/env python3
"""AI compute demand for the app's AI demand view: tokens, lab revenue, hyperscaler capex and backlog.

No single source measures all AI usage, so this puts several partial ones side by side:

  OpenRouter      weekly tokens by model maker on OpenRouter's API router (public rankings data).
                  A developer-heavy slice that leans to cheap open models; most Claude and
                  ChatGPT use goes direct and never shows here. Good for growth and for who
                  wins the price-sensitive developer, not for total market share.
  SEC filings     quarterly capex and remaining performance obligations (contracted, not yet
                  billed revenue: mostly multi-year cloud and AI compute deals) from XBRL.
  Disclosed       figures companies stated themselves (tokens processed, revenue run-rates),
                  curated with sources in compute_disclosed.json.

    data/compute/openrouter_authors.csv   week, author, tokens (kept forever; the API serves one year)
    data/compute/sec.json                 last good SEC pull
    app/public/data/compute.json          everything the view needs
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "compute"
APP = ROOT / "app"
OPENROUTER = "https://openrouter.ai/api/frontend/v1/rankings/"
SEC_UA = "StonkyTonkyWonky research tool"  # SEC asks for a declared agent; no personal contact sent
SEC = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/{tag}.json"
# ticker: (CIK, capex tag); every one reports remaining performance obligations except Meta,
# and Amazon stopped tagging its backlog in 2020.
COMPANIES = {
    "MSFT": (789019, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "GOOGL": (1652044, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "AMZN": (1018724, "PaymentsToAcquireProductiveAssets"),
    "META": (1326801, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "ORCL": (1341439, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "CRWV": (1769628, "PaymentsToAcquirePropertyPlantAndEquipment"),
}
RPO_TAG = "RevenueRemainingPerformanceObligation"


def get_json(url: str, ua: str = "Mozilla/5.0"):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 + 3 * k)
        except Exception:  # noqa: BLE001
            time.sleep(2 + 3 * k)
    raise RuntimeError(f"failed: {url}")


# ---------- OpenRouter ----------

def openrouter() -> dict:
    path = OUT / "openrouter_authors.csv"
    rows: dict[tuple[str, str], int] = {}
    if path.exists():
        with open(path, newline="") as fh:
            rows = {(r["week"], r["author"]): int(r["tokens"]) for r in csv.DictReader(fh)}
    try:
        weeks = get_json(OPENROUTER + "author-market-share")["data"]["data"]
        # Each fetch restates the whole year; the newest week replaces what we had for it.
        for w in weeks:
            for author, tok in w["ys"].items():
                rows[(w["x"], author)] = int(tok)
        oc = get_json(OPENROUTER + "open-closed")["data"]
    except Exception as e:  # noqa: BLE001
        print(f"openrouter failed ({e}); using stored weeks")
        oc = []
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["week", "author", "tokens"])
        for (wk, a), t in sorted(rows.items()):
            w.writerow([wk, a, t])
    by_week: dict[str, dict[str, int]] = defaultdict(dict)
    for (wk, a), t in rows.items():
        by_week[wk][a] = t
    weeks = sorted(by_week)
    # The API names the top ten makers each week and lumps the rest: keep the makers that
    # were ever in a top four, everyone else goes to Others.
    top = set()
    for wk in weeks:
        top |= {a for a, _ in sorted(by_week[wk].items(), key=lambda kv: -kv[1])[:4] if a != "Others"}
    top |= {"anthropic", "openai", "google"}
    makers = sorted(top)
    series = {m: [by_week[wk].get(m, 0) for wk in weeks] for m in makers}
    totals = [sum(by_week[wk].values()) for wk in weeks]
    series["Others"] = [t - sum(series[m][i] for m in makers) for i, t in enumerate(totals)]
    # The newest week is still running; flag it so the view can leave it out of growth figures.
    partial = (date.today() - date.fromisoformat(weeks[-1])).days < 7 if weeks else False
    return {"weeks": weeks, "total": totals, "by_maker": series, "last_week_partial": partial,
            "open_closed": {"weeks": [r["x"] for r in oc], "open": [r["ys"].get("open") for r in oc],
                            "closed": [r["ys"].get("closed") for r in oc]}}


# ---------- SEC ----------

def quarters_from_ytd(facts: list[dict]) -> dict[str, float]:
    """Quarterly flows from 10-Q/10-K facts, which report year-to-date sums: Q = YTD − prior YTD."""
    best: dict[tuple[str, str], float] = {}
    for f in facts:
        if f.get("form") not in ("10-Q", "10-K", "10-Q/A", "10-K/A") or "start" not in f:
            continue
        best[(f["start"], f["end"])] = f["val"]  # later filings restate; keep the last seen
    by_start: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (s, e), v in best.items():
        by_start[s].append((e, v))
    out: dict[str, float] = {}
    for s, items in by_start.items():
        items.sort()
        prev_end, prev_val = None, 0.0
        for e, v in items:
            days = (date.fromisoformat(e) - date.fromisoformat(s)).days
            if days > 380:
                continue
            q = v - prev_val if prev_end else v
            n_q = round(((date.fromisoformat(e) - date.fromisoformat(prev_end)).days if prev_end else days) / 91)
            if n_q == 1:
                out[e] = q
            prev_end, prev_val = e, v
    return out


def sec() -> dict:
    store = OUT / "sec.json"
    try:
        data = {}
        for t, (cik, capex_tag) in COMPANIES.items():
            capex = (get_json(SEC.format(cik=cik, tag=capex_tag), SEC_UA) or {}).get("units", {}).get("USD", [])
            time.sleep(0.2)
            rpo = (get_json(SEC.format(cik=cik, tag=RPO_TAG), SEC_UA) or {}).get("units", {}).get("USD", [])
            time.sleep(0.2)
            q = quarters_from_ytd(capex)
            r = {}
            for f in rpo:
                if f.get("form", "").startswith(("10-Q", "10-K")):
                    r[f["end"]] = f["val"]
            data[t] = {"capex": dict(sorted(q.items())), "rpo": dict(sorted(r.items()))}
        store.write_text(json.dumps(data))
    except Exception as e:  # noqa: BLE001
        print(f"SEC failed ({e}); using the stored pull")
        data = json.loads(store.read_text())
    return data


def quarter_label(end: str) -> str:
    d = date.fromisoformat(end)
    # Calendar quarter the period mostly falls in (Oracle and Microsoft have odd fiscal years).
    m = d.month - 1 if d.day < 15 else d.month
    m = 12 if m == 0 else m
    y = d.year if d.month != 1 or d.day >= 15 else d.year - 1
    return f"{y}Q{(m - 1) // 3 + 1}"


def sec_view(data: dict) -> dict:
    labels = sorted({quarter_label(e) for v in data.values() for e in v["capex"]})
    labels = [q for q in labels if q >= "2019Q1"]
    capex = {}
    for t, v in data.items():
        by_q = {quarter_label(e): x for e, x in v["capex"].items()}
        capex[t] = [None if q not in by_q else round(by_q[q] / 1e9, 2) for q in labels]
    # The sum is only meaningful where all the big five reported (CoreWeave is small and young).
    big = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]
    total = [round(sum(capex[t][i] for t in big), 1) if all(capex[t][i] is not None for t in big) else None for i in range(len(labels))]
    rpo = {}
    stale = (date.today().replace(year=date.today().year - 1)).isoformat()
    for t, v in data.items():
        if v["rpo"] and max(v["rpo"]) >= stale:  # Amazon's tagged backlog stops in 2020
            rpo[t] = {"dates": list(v["rpo"]), "bn": [round(x / 1e9, 1) for x in v["rpo"].values()]}
    return {"quarters": labels, "capex_bn": capex, "capex_total_bn": total, "rpo": rpo}


# Series for the one-chart view: (key, label, group, series id in compute_disclosed.json)
DISCLOSED_LINES = [
    ("google_tokens", "Google tokens a month (all products)", "tokens", "google_tokens_month"),
    ("google_api", "Google API tokens a minute", "tokens", "google_api_tokens_min"),
    ("bytedance", "ByteDance tokens a day", "tokens", "bytedance_tokens_day"),
    ("anthropic_rr", "Anthropic revenue run-rate", "revenue", "anthropic_revenue_runrate"),
    ("openai_rr", "OpenAI revenue run-rate", "revenue", "openai_revenue_runrate"),
    ("chatgpt_users", "ChatGPT weekly users", "users", "openai_weekly_users"),
    ("gemini_users", "Gemini monthly users", "users", "google_gemini_mau"),
]


def combined(payload: dict, sec_raw: dict) -> list[dict]:
    """Every demand series as dated values, for one log chart."""
    lines = []
    o = payload["openrouter"]
    n = len(o["weeks"]) - (1 if o["last_week_partial"] else 0)
    lines.append({"key": "openrouter", "label": "OpenRouter tokens a week", "group": "tokens", "unit": "tokens",
                  "dates": o["weeks"][:n], "values": o["total"][:n]})
    s = payload["sec"]
    qn = [i for i, v in enumerate(s["capex_total_bn"]) if v is not None]
    q_end = lambda q: f"{q[:4]}-{int(q[5]) * 3:02d}-{30 if q[5] in '23' else 31}"  # noqa: E731
    lines.append({"key": "capex", "label": "Big-five capex a quarter", "group": "spend", "unit": "$bn",
                  "dates": [q_end(s["quarters"][i]) for i in qn], "values": [s["capex_total_bn"][i] for i in qn]})
    # Backlog: Microsoft + Alphabet + Oracle, by calendar quarter, where all three reported.
    by_q: dict[str, dict[str, float]] = defaultdict(dict)
    for t in ("MSFT", "GOOGL", "ORCL"):
        for end, v in sec_raw[t]["rpo"].items():
            by_q[quarter_label(end)][t] = v / 1e9
    qs = [q for q in sorted(by_q) if len(by_q[q]) == 3 and q >= "2019Q1"]
    lines.append({"key": "backlog", "label": "Cloud backlog (MSFT + GOOGL + ORCL)", "group": "spend", "unit": "$bn",
                  "dates": [q_end(q) for q in qs], "values": [round(sum(by_q[q].values()), 1) for q in qs]})
    pts = payload["disclosed"].get("points", [])
    for key, label, group, series in DISCLOSED_LINES:
        xs = sorted((p["date"], p["value"], p["unit"]) for p in pts if p["series"] == series)
        if len(xs) >= 3 and len({u for _, _, u in xs}) == 1:
            lines.append({"key": key, "label": label, "group": group, "unit": xs[0][2],
                          "dates": [d for d, _, _ in xs], "values": [v for _, v, _ in xs]})
    dxi = ROOT / "data" / "industry" / "dxi.csv"
    if dxi.exists():
        with open(dxi, newline="") as fh:
            rows = [(r["date"], float(r["dxi"])) for r in csv.DictReader(fh) if r["date"] >= "2019-01-01"]
        lines.append({"key": "dram", "label": "DRAM spot prices (DXI index)", "group": "memory", "unit": "index",
                      "dates": [d for d, _ in rows], "values": [round(v, 1) for _, v in rows]})
    return lines


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "openrouter": openrouter()}
    sec_raw = sec()
    payload["sec"] = sec_view(sec_raw)
    disclosed = ROOT / "compute_disclosed.json"
    payload["disclosed"] = json.loads(disclosed.read_text()) if disclosed.exists() else {"points": []}
    payload["combined"] = combined(payload, sec_raw)
    out = APP / "public" / "data" / "compute.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")))
    tmp.replace(out)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(out, APP / "dist" / "data" / out.name)
    o = payload["openrouter"]
    s = payload["sec"]
    i = -2 if o["last_week_partial"] else -1
    print(f"compute: OpenRouter week {o['weeks'][i]} {o['total'][i] / 1e12:.1f}T tokens, anthropic "
          f"{o['by_maker']['anthropic'][i] / o['total'][i]:.1%}; capex {s['quarters'][-1]} "
          f"{[(t, v[-1]) for t, v in s['capex_bn'].items()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
