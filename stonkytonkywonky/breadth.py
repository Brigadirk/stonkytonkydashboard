#!/usr/bin/env python3
"""NYSE breadth: McClellan Summation Index (NYSI) with its RSI and MACD.

The official advance/decline feed isn't free, so the advances and declines are
counted from Yahoo closes of every NYSE-listed issue (nasdaqtrader's symbol
directory, ETFs and test issues left out). StockCharts' official $NYSI close is
recorded alongside and used to put our line on the same level; the daily moves
come from our own counts and track the official ones closely.

    data/breadth/ad.csv         advances and declines per session (kept forever)
    data/breadth/official.csv   StockCharts' $NYSI close and RSI, one row per session
    app/public/data/breadth.json   chart series for the web app

Ratio-adjusted, as StockCharts does it: net advances per 1000 issues traded.
The summation index is the running sum of the oscillator, which works out to
20 × EMA39 − 10 × EMA19 of that ratio, plus a constant fixed by the official close.
"""

from __future__ import annotations

import csv
import gzip
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "breadth"
APP = ROOT / "app"
NY = ZoneInfo("America/New_York")
UA = "Mozilla/5.0"  # Yahoo answers 429 to a full browser string from this box
SYMBOLS_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
SPARK_URL = "https://query1.finance.yahoo.com/v7/finance/spark"
OFFICIAL_URL = "https://stockcharts.com/j-sum/sum?cmd=symsum&symbol=$NYSI"
REFETCH_DAYS = 10  # recent sessions are recounted each night in case Yahoo filled late closes
FIRST_RANGE = "2y"


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return gzip.decompress(body) if r.headers.get("Content-Encoding") == "gzip" else body


def nyse_symbols() -> list[str]:
    syms = []
    for line in get(SYMBOLS_URL).decode().splitlines()[1:]:
        c = line.split("|")
        # ACT symbol | name | exchange | CQS | ETF | lot | test issue | NASDAQ symbol
        if len(c) < 8 or c[2] != "N" or c[4] != "N" or c[6] != "N":
            continue
        syms.append(c[0].replace(".", "-").replace("$", "-P"))  # Yahoo spelling: BRK-B, BAC-PK
    return syms


def spark(batch: list[str], rng: str) -> dict[str, tuple[list[int], list[float | None]]]:
    q = urllib.parse.urlencode({"symbols": ",".join(batch), "range": rng, "interval": "1d"})
    for attempt in range(3):
        try:
            data = json.loads(get(f"{SPARK_URL}?{q}"))
            out = {}
            for item in data["spark"]["result"] or []:
                try:
                    x = item["response"][0]
                    out[item["symbol"]] = (x["timestamp"], x["indicators"]["quote"][0]["close"])
                except (KeyError, IndexError, TypeError):
                    pass
            return out
        except Exception:
            time.sleep(2 + 3 * attempt)
    return {}


def count(closes: dict, last_complete: date) -> dict[date, tuple[int, int, int]]:
    adv, dec, unch = defaultdict(int), defaultdict(int), defaultdict(int)
    for ts, cl in closes.values():
        prev = None
        for t, c in zip(ts, cl):
            if c is None:
                continue
            day = datetime.fromtimestamp(t, NY).date()
            if day > last_complete:
                break
            if prev is not None:
                if c > prev:
                    adv[day] += 1
                elif c < prev:
                    dec[day] += 1
                else:
                    unch[day] += 1
            prev = c
    return {d: (adv[d], dec[d], unch[d]) for d in set(adv) | set(dec) | set(unch)}


def last_complete_session() -> date:
    now = datetime.now(NY)
    # Yahoo's close settles a little after 16:00; before then today's bar is still moving.
    if now.hour * 60 + now.minute < 16 * 60 + 30:
        return date.fromordinal(now.date().toordinal() - 1)
    return now.date()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def update_counts() -> list[dict]:
    path = OUT / "ad.csv"
    have = {r["date"]: r for r in read_csv(path)}
    syms = nyse_symbols()
    rng = "1mo" if len(have) > 60 else FIRST_RANGE
    closes: dict = {}
    with ThreadPoolExecutor(4) as ex:
        for part in ex.map(lambda b: spark(b, rng), [syms[i:i + 20] for i in range(0, len(syms), 20)]):
            closes.update(part)
    if len(closes) < len(syms) * 0.8:
        raise SystemExit(f"breadth.py: only {len(closes)} of {len(syms)} NYSE issues came back; keeping yesterday's data")
    counts = count(closes, last_complete_session())
    recent = sorted(counts)[-REFETCH_DAYS:] if have else sorted(counts)[1:]  # the first day has no previous close
    for d in recent:
        a, dn, u = counts[d]
        have[d.isoformat()] = {"date": d.isoformat(), "advances": a, "declines": dn, "unchanged": u}
    rows = [have[k] for k in sorted(have)]
    write_csv(path, rows, ["date", "advances", "declines", "unchanged"])
    print(f"breadth.py: {len(closes)}/{len(syms)} issues, {len(rows)} sessions, last {rows[-1]['date']}")
    return rows


def record_official() -> list[dict]:
    """StockCharts' own $NYSI close, so our line sits on the official level."""
    path = OUT / "official.csv"
    rows = {r["date"]: r for r in read_csv(path)}
    try:
        d = json.loads(get(OFFICIAL_URL))
        day = datetime.strptime(d["latestTrade"], "%d %b %Y").date().isoformat()
        rows[day] = {"date": day, "nysi": d["close"], "rsi": d.get("rsi", "")}
        write_csv(path, [rows[k] for k in sorted(rows)], ["date", "nysi", "rsi"])
    except Exception as e:  # the app still works on our own counts
        print(f"breadth.py: official $NYSI not recorded ({e})")
    return [rows[k] for k in sorted(rows)]


def ema(xs: list[float], n: int) -> list[float]:
    a, e, out = 2 / (n + 1), None, []
    for x in xs:
        e = x if e is None else e + a * (x - e)
        out.append(e)
    return out


def wilder_rsi(xs: list[float], n: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(xs)
    if len(xs) <= n:
        return out
    ch = [b - a for a, b in zip(xs, xs[1:])]
    ag = sum(max(c, 0) for c in ch[:n]) / n
    al = sum(max(-c, 0) for c in ch[:n]) / n
    for i in range(n, len(ch) + 1):
        if i > n:
            c = ch[i - 1]
            ag = (ag * (n - 1) + max(c, 0)) / n
            al = (al * (n - 1) + max(-c, 0)) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def last_cross(macd: list[float], sig: list[float], dates: list[str]) -> dict | None:
    for i in range(len(macd) - 1, 0, -1):
        before, now = macd[i - 1] - sig[i - 1], macd[i] - sig[i]
        if before <= 0 < now or before >= 0 > now:
            return {"date": dates[i], "dir": "bull" if now > 0 else "bear"}
    return None


def main() -> int:
    counts = update_counts()
    official = record_official()
    dates = [r["date"] for r in counts]
    adv = [int(r["advances"]) for r in counts]
    dec = [int(r["declines"]) for r in counts]
    unch = [int(r["unchanged"]) for r in counts]
    rana = [1000 * (a - d) / (a + d) if a + d else 0.0 for a, d in zip(adv, dec)]
    e19, e39 = ema(rana, 19), ema(rana, 39)
    osc = [a - b for a, b in zip(e19, e39)]
    raw = [20 * b - 10 * a for a, b in zip(e19, e39)]

    at = {d: i for i, d in enumerate(dates)}
    gaps = [float(r["nysi"]) - raw[at[r["date"]]] for r in official if r["date"] in at and r["nysi"]][-20:]
    offset = median(gaps) if gaps else 0.0
    nysi = [v + offset for v in raw]
    rsi = wilder_rsi(nysi)
    macd = [a - b for a, b in zip(ema(nysi, 12), ema(nysi, 26))]
    sig = ema(macd, 9)

    # The EMAs need a couple of months to forget their starting point.
    warm = min(60, len(dates))
    r2 = lambda xs: [None if v is None else round(v, 2) for v in xs[warm:]]
    last_off = next((r for r in reversed(official) if r["nysi"]), None)
    payload = {
        "as_of": dates[-1],
        "dates": dates[warm:],
        "nysi": r2(nysi),
        "osc": r2(osc),
        "rsi": r2(rsi),
        "macd": r2(macd),
        "signal": r2(sig),
        "advances": adv[warm:],
        "declines": dec[warm:],
        "unchanged": unch[warm:],
        "offset": round(offset, 1),
        "calibrated_days": len(gaps),
        "official": {"date": last_off["date"], "nysi": float(last_off["nysi"]),
                     "rsi": float(last_off["rsi"]) if last_off.get("rsi") else None} if last_off else None,
        "last_cross": last_cross(macd, sig, dates),
    }
    data = APP / "public" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "breadth.json").write_text(json.dumps(payload, separators=(",", ":")))
    if (APP / "dist" / "data").exists():
        shutil.copy2(data / "breadth.json", APP / "dist" / "data" / "breadth.json")
    print(f"breadth.py: NYSI {nysi[-1]:.1f} (offset {offset:+.1f} from {len(gaps)} official closes), "
          f"RSI {rsi[-1]:.1f}, MACD−signal {macd[-1] - sig[-1]:+.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
