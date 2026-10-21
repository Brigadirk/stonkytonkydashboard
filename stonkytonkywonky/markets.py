#!/usr/bin/env python3
"""Reference markets for the app's markets view: indexes, rates, credit, FX, commodities, crypto.

Prices come from Yahoo's chart API, rates and credit spreads from FRED's public
CSV download (no key). The watch list is markets.json.

    app/public/data/markets.json   latest level, changes, 1- and 5-year percentiles, 5-year daily history

Prices change in percent; yields and spreads change in percentage points, since a
move from 4.0% to 4.4% is what bond people call +40 basis points, not +10%.
"""

from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
UA = "Mozilla/5.0"  # Yahoo answers 429 to a full browser string from this box
FRED_UA = "curl/8.5.0"  # FRED's firewall drops browser-like and custom agents; curl's gets through
YEARS = 5


def get(url: str, attempts: int = 3, ua: str = UA) -> bytes:
    for k in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=30) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == attempts - 1:
                raise
            time.sleep(3 * (k + 1))
    raise RuntimeError("unreachable")


def yahoo(symbol: str) -> list[tuple[str, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}?range={YEARS}y&interval=1d"
    res = json.loads(get(url))["chart"]["result"][0]
    tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
    closes = res["indicators"]["quote"][0]["close"]
    out: dict[str, float] = {}
    for ts, c in zip(res["timestamp"], closes):
        if c is not None:
            out[datetime.fromtimestamp(ts, tz).date().isoformat()] = c  # the last bar of a day wins
    return sorted(out.items())


def fred(series_id: str) -> list[tuple[str, float]]:
    start = (date.today() - timedelta(days=365 * YEARS + 40)).isoformat()
    text = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}", ua=FRED_UA).decode()
    rows = csv.reader(io.StringIO(text))
    next(rows)
    return [(d, float(v)) for d, v in rows if v not in ("", ".")]


def at_or_before(points: list[tuple[str, float]], day: str) -> float | None:
    """Value on the last date not after `day`."""
    best = None
    for d, v in points:
        if d > day:
            break
        best = v
    return best


def percentile(values: list[float], v: float) -> float | None:
    return 100 * sum(x <= v for x in values) / len(values) if len(values) > 1 else None


def summarize(cfg: dict, points: list[tuple[str, float]]) -> dict:
    last_d, last = points[-1]
    yields = cfg.get("unit") == "%"
    end = date.fromisoformat(last_d)

    def change(days: int | None = None, since: str | None = None) -> float | None:
        ref = since or (end - timedelta(days=days)).isoformat()
        before = at_or_before(points, ref)
        if before is None or (not yields and before <= 0):
            return None
        return last - before if yields else last / before - 1

    year = [v for d, v in points if d > (end - timedelta(days=365)).isoformat()]
    prev = points[-2][1] if len(points) > 1 else None
    return {
        "id": cfg["id"], "name": cfg["name"], "group": cfg["group"], "note": cfg.get("note"),
        "unit": cfg.get("unit"), "source": cfg.get("source", "yahoo"),
        "date": last_d, "last": last,
        "chg": {
            "1d": (last - prev if yields else last / prev - 1) if prev else None,
            "1w": change(7), "1m": change(30), "3m": change(91),
            "ytd": change(since=f"{end.year - 1}-12-31"), "1y": change(365),
        },
        "high_1y": max(year), "low_1y": min(year),
        "from_high": None if yields else last / max(year) - 1,
        "pct_1y": percentile(year, last),
        "pct_5y": percentile([v for _, v in points], last),
        "history": {"dates": [d for d, _ in points], "values": [round(v, 4) for _, v in points]},
    }


def main() -> int:
    cfg = json.loads((ROOT / "markets.json").read_text(encoding="utf-8"))
    out, failed = [], []
    for s in cfg["series"]:
        try:
            points = fred(s["id"]) if s.get("source") == "fred" else yahoo(s["id"])
            if not points:
                raise ValueError("no data")
            out.append(summarize(s, points))
            print(f"{s['id']:<18} {points[-1][0]}  {points[-1][1]:.4g}", flush=True)
        except Exception as exc:  # noqa: BLE001 — one dead symbol must not lose the rest
            failed.append(s["id"])
            print(f"{s['id']:<18} FAILED {exc!r}"[:160], flush=True)
        time.sleep(0.5)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": max(r["date"] for r in out) if out else None,
        "groups": cfg["groups"], "series": out, "failed": failed,
    }
    data = APP / "public" / "data"
    tmp = data / "markets.json.tmp"
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    tmp.replace(data / "markets.json")
    if (APP / "dist" / "data").exists():
        shutil.copy2(data / "markets.json", APP / "dist" / "data" / "markets.json")
    print(f"{len(out)}/{len(cfg['series'])} series")
    return 1 if failed and not out else 0


if __name__ == "__main__":
    sys.exit(main())
