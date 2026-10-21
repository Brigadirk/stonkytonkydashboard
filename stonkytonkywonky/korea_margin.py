#!/usr/bin/env python3
"""Korean retail leverage for the app's positioning view: margin loans and customer deposits.

Margin loans (신용거래융자) on KOSPI and KOSDAQ and investor deposits (투자자예탁금) come
from KOFIA FreeSIS, daily, about one business day behind, by settlement date. No login or key.
The index closes come from Yahoo.

    data/korea/margin.csv              date, kospi_margin, kosdaq_margin, deposits (KRW billions)
    app/public/data/korea_margin.json  history since 2023 in KRW trillions, with the Kospi and Kosdaq

Margin per index point (KOSPI margin in billions ÷ the Kospi) shows leverage against the
size of the market: when prices fall and loans don't, it rises, and the holders left are
more leveraged than before.
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
OUT = ROOT / "data" / "korea"
KOFIA = "https://freesis.kofia.or.kr/meta/getMetaDataList.do"
MARGIN_SERVICE = "STATSCU0100000070BO"  # 신용공여 잔고 추이: TMPV3 KOSPI, TMPV4 KOSDAQ (million KRW)
DEPOSIT_SERVICE = "STATSCU0100000060BO"  # 증시자금추이: TMPV2 투자자예탁금 (million KRW)
START_YEAR = 2023


def kofia(service: str, start: str, end: str) -> list[dict]:
    body = {"dmSearch": {"tmpV40": "1000000", "tmpV41": "1", "tmpV1": "D", "tmpV45": start, "tmpV46": end, "OBJ_NM": service}}
    req = urllib.request.Request(KOFIA, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Referer": "https://freesis.kofia.or.kr/"})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["ds1"]
        except Exception:  # noqa: BLE001 — the server sometimes cuts a long answer off; retry
            if k == 2:
                raise
            time.sleep(3)
    raise RuntimeError("unreachable")


def yahoo(symbol: str) -> dict[str, float]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}?range=5y&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
        res = json.load(r)["chart"]["result"][0]
    tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
    return {datetime.fromtimestamp(ts, tz).date().isoformat(): c
            for ts, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None}


def collect() -> dict[str, dict]:
    """Stored rows plus fresh ones; a full fetch the first time, then just this year."""
    path = OUT / "margin.csv"
    rows: dict[str, dict] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            rows = {r["date"]: r for r in csv.DictReader(fh)}
    today = date.today()
    years = [today.year] if rows else range(START_YEAR, today.year + 1)
    for y in years:
        span = (f"{y}0101", today.strftime("%Y%m%d") if y == today.year else f"{y}1231")
        margin = kofia(MARGIN_SERVICE, *span)
        time.sleep(1.1)
        deposits = {r["TMPV1"]: r["TMPV2"] for r in kofia(DEPOSIT_SERVICE, *span)}
        time.sleep(1.1)
        for m in margin:
            d = m["TMPV1"]
            dep = deposits.get(d)
            rows[f"{d[:4]}-{d[4:6]}-{d[6:]}"] = {
                "date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "kospi_margin": f"{m['TMPV3'] / 1000:.3f}",
                "kosdaq_margin": f"{m['TMPV4'] / 1000:.3f}", "deposits": "" if dep is None else f"{dep / 1000:.3f}"}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "kospi_margin", "kosdaq_margin", "deposits"])
        w.writeheader()
        w.writerows(rows[d] for d in sorted(rows))
    return rows


def at_or_before(dates: list[str], values: list, day: str):
    for d, v in zip(reversed(dates), reversed(values)):
        if d <= day and v is not None:
            return v
    return None


def main() -> int:
    rows = collect()
    kospi, kosdaq = yahoo("^KS11"), yahoo("^KQ11")
    dates = sorted(rows)
    num = lambda s: float(s) if s not in ("", None) else None  # noqa: E731
    km = [num(rows[d]["kospi_margin"]) for d in dates]
    qm = [num(rows[d]["kosdaq_margin"]) for d in dates]
    dep = [num(rows[d]["deposits"]) for d in dates]
    ki = [kospi.get(d) for d in dates]
    qi = [kosdaq.get(d) for d in dates]
    raw = [m / k if m and k else None for m, k in zip(km, ki)]
    # Loans are by settlement date and the index by trade date: a 5-day average evens out the mismatch.
    ratio = []
    for i in range(len(raw)):
        win = [r for r in raw[max(0, i - 4):i + 1] if r is not None]
        ratio.append(sum(win) / len(win) if win else None)
    last = dates[-1]
    peak_i = max(range(len(km)), key=lambda i: km[i] or 0)

    def chg(vals: list, days: int) -> float | None:
        then = at_or_before(dates, vals, (date.fromisoformat(last) - timedelta(days=days)).isoformat())
        return vals[-1] / then - 1 if then and vals[-1] is not None else None

    ratios = sorted(r for r in ratio if r is not None)
    cur_ratio = next((r for r in reversed(ratio) if r is not None), None)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": last,
        "latest": {
            "kospi_margin_tn": round(km[-1] / 1000, 2), "kosdaq_margin_tn": round(qm[-1] / 1000, 2),
            "deposits_tn": None if dep[-1] is None else round(dep[-1] / 1000, 1),
            "ratio": None if cur_ratio is None else round(cur_ratio, 2),
            "ratio_pct": None if cur_ratio is None else round(100 * sum(r <= cur_ratio for r in ratios) / len(ratios), 1),
            "margin_chg_1w": chg(km, 7), "margin_chg_1m": chg(km, 30), "deposits_chg_1m": chg(dep, 30),
            "peak_date": dates[peak_i], "peak_tn": round(km[peak_i] / 1000, 2), "from_peak": km[-1] / km[peak_i] - 1,
            "kospi": None if ki[-1] is None else round(ki[-1], 1), "kospi_from_peak_date": None if not ki[-1] or not ki[peak_i] else ki[-1] / ki[peak_i] - 1,
        },
        "history": {
            "dates": dates,
            "kospi_margin_tn": [None if v is None else round(v / 1000, 3) for v in km],
            "kosdaq_margin_tn": [None if v is None else round(v / 1000, 3) for v in qm],
            "deposits_tn": [None if v is None else round(v / 1000, 2) for v in dep],
            "kospi": [None if v is None else round(v, 1) for v in ki],
            "kosdaq": [None if v is None else round(v, 1) for v in qi],
            "ratio": [None if v is None else round(v, 3) for v in ratio],
        },
    }
    out = APP / "public" / "data" / "korea_margin.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")))
    tmp.replace(out)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(out, APP / "dist" / "data" / out.name)
    L = payload["latest"]
    print(f"korea margin {last}: KOSPI {L['kospi_margin_tn']} tn ({L['from_peak']:+.1%} from {L['peak_date']}), "
          f"KOSDAQ {L['kosdaq_margin_tn']} tn, deposits {L['deposits_tn']} tn, per Kospi point {L['ratio']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
