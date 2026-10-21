#!/usr/bin/env python3
"""Industry data for the app's industry view: memory spot prices, GPU rental prices, oil shipping.

    memory    DRAMeXchange's public homepage: daily DRAM chip spot prices, weekly NAND
              wafer, NAND chip, module and GDDR spot prices, and the DXI index. There is
              no free history, so it is recorded nightly; `--backfill-memory` rebuilds the
              past from the Wayback Machine's copies of the homepage (roughly weekly).
    gpu       vast.ai marketplace: on-demand offers per GPU type, priced per GPU-hour.
              A spot market of mostly smaller hosts, so cheaper than the big clouds; what
              matters is the trend. No history exists; recorded nightly.
    shipping  IMF PortWatch: daily transits through the main chokepoints from AIS ship
              positions, by vessel type, 2019 onward. It runs about a week behind.

    data/industry/memory.csv     date, section, item, high, low, avg, change (one row per price per day)
    data/industry/dxi.csv        date, dxi
    data/industry/gpu.csv        date, gpu, offers, gpus, median, p25, min ($ per GPU-hour)
    app/public/data/industry.json
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import statistics
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "industry"
APP = ROOT / "app"
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

DRAMEXCHANGE = "https://www.dramexchange.com/"
# Section titles on the homepage, and the names the app shows.
SECTIONS = {
    "DRAM Spot Price": "DRAM chips",
    "Module Spot Price": "DRAM modules",
    "Flash Spot Price": "NAND chips",
    "GDDR Spot Price": "GDDR",
    "Wafer Spot Price": "NAND wafers",
    "eMMC Spot Price": "Memory cards",  # the homepage's eMMC tab holds the memory-card table
}
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

VAST = "https://console.vast.ai/api/v0/bundles/"
GPUS = ["B200", "H200", "H200 NVL", "H100 SXM", "H100 NVL", "H100 PCIE", "A100 SXM4", "A100 PCIE", "L40S",
        "RTX PRO 6000 S", "RTX 5090", "RTX 4090"]

PORTWATCH = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
CHOKEPOINTS = ["Strait of Hormuz", "Bab el-Mandeb Strait", "Suez Canal", "Cape of Good Hope", "Malacca Strait", "Panama Canal"]
# Hormuz traffic fell from ~60 tankers a day to almost none on 1 March 2026. "Before" is the year up to it.
WAR_START = "2026-03-01"


def get(url: str, ua: str = BROWSER, attempts: int = 3, timeout: int = 60) -> bytes:
    for k in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=timeout) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == attempts - 1:
                raise
            time.sleep(5 * (k + 1))
    raise RuntimeError("unreachable")


def at_or_before(dates: list[str], values: list[float], day: str) -> float | None:
    best = None
    for d, v in zip(dates, values):
        if d > day:
            break
        best = v
    return best


def changes(dates: list[str], values: list[float], spans: dict[str, int]) -> dict:
    end = date.fromisoformat(dates[-1])
    out = {}
    for k, days in spans.items():
        before = at_or_before(dates, values, (end - timedelta(days=days)).isoformat())
        out[k] = values[-1] / before - 1 if before else None
    return out


# ---------- memory ----------

def page_text(h: str) -> str:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    return re.sub(r"\s*\|[\s|]*", " | ", html.unescape(re.sub(r"<[^>]+>", "|", h)))


def item_name(item: str, section: str) -> tuple[str, str]:
    """One section and name per product: DRAMeXchange has written the same chip several ways over the years."""
    item = re.sub(r"\s+", " ", item.replace("*", "x")).strip()
    if re.match(r"(GDDR|LPDDR)", item):  # older pages run the graphics/mobile table into the NAND one
        return "GDDR", re.sub(r"\b(\d+)G[Bb]?$", r"\1Gb", item)
    item = re.sub(r"\s*(Mbps|MHz)$", "", item)
    item = re.sub(r"\)(?=\d)", ") ", item)
    if section == "DRAM chips":
        item = re.sub(r"\b(\d+)G (?=\()", r"\1Gb ", item)
    if section == "DRAM modules":
        item = re.sub(r"\b(\d+)Gb\b", r"\1GB", item)
    return section, item


def parse_dramexchange(page: str, fallback_year: int) -> tuple[list[dict], tuple[str, float] | None]:
    """Spot-price rows and the DXI from one copy of the homepage."""
    titles = [(m.start(), m.group(1)) for m in re.finditer(r">\s*(?:&nbsp;)?\s*((?:DRAM|Module|NAND Flash|Flash|GDDR|Wafer|eMMC) Spot Price)\s*(?:&nbsp;)?\s*<", page)]
    # The tab strip near the top repeats the titles; the tables come after the last repeat of the first one.
    firsts = [p for p, t in titles if t == "DRAM Spot Price"]
    if not firsts:
        return [], None
    titles = [(p, t.replace("NAND ", "")) for p, t in titles if p >= firsts[-1]]
    rows = []
    for i, (pos, title) in enumerate(titles):
        if title not in SECTIONS:
            continue
        end = titles[i + 1][0] if i + 1 < len(titles) else pos + 15000
        seg = page_text(page[pos:end])
        upd = re.search(r"Last Update\s*:?\s*([A-Z][a-z]{2})\.?\s*(\d{1,2}),?\s*(\d{4})?", seg)
        if not upd:
            continue
        day = date(int(upd.group(3) or fallback_year), MONTHS[upd.group(1)], int(upd.group(2))).isoformat()
        for item, hi, lo, _shi, _slo, avg, chg in re.findall(
                r"\| ([^|]+?) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| (-?[\d.]+) ?%", seg):
            item = re.sub(r"\s+", " ", item).strip()
            section = "Memory cards" if item.startswith("MicroSD") else SECTIONS[title]
            section, item = item_name(item, section)
            rows.append({"date": day, "section": section, "item": item, "high": hi, "low": lo, "avg": avg, "change": chg})
    dxi = None
    m = re.search(r"DXI\s*\|\s*([A-Z][a-z]{2})\.?\s*(\d{1,2}),?\s*(\d{4})?[^|]*\|\s*([\d,]+\.\d+)", page_text(page[:60000]))
    if m:
        d = date(int(m.group(3) or fallback_year), MONTHS[m.group(1)], int(m.group(2))).isoformat()
        dxi = (d, float(m.group(4).replace(",", "")))
    return rows, dxi


def store_memory(rows: list[dict], dxis: list[tuple[str, float]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "memory.csv"
    known: dict[tuple, dict] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                r["section"], r["item"] = item_name(r["item"], r["section"])
                known[(r["date"], r["section"], r["item"])] = r
    for r in rows:
        known[(r["date"], r["section"], r["item"])] = r
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "section", "item", "high", "low", "avg", "change"])
        w.writeheader()
        w.writerows(known[k] for k in sorted(known))
    dpath = OUT / "dxi.csv"
    dx: dict[str, str] = {}
    if dpath.exists():
        with open(dpath, newline="", encoding="utf-8") as fh:
            dx = {r["date"]: r["dxi"] for r in csv.DictReader(fh)}
    for d, v in dxis:
        dx[d] = f"{v:.2f}"
    with open(dpath, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "dxi"])
        w.writerows(sorted(dx.items()))


def collect_memory() -> None:
    rows, dxi = parse_dramexchange(get(DRAMEXCHANGE).decode("utf-8", "replace"), date.today().year)
    if not rows:
        raise ValueError("no spot tables found on the DRAMeXchange homepage")
    store_memory(rows, [dxi] if dxi else [])
    print(f"memory: {len(rows)} prices, DXI {dxi}", flush=True)


def backfill_memory(since: str = "2021") -> None:
    """Rebuild history from the Wayback Machine's copies of the homepage, one per day at most."""
    cdx = json.loads(get(f"http://web.archive.org/cdx/search/cdx?url=dramexchange.com/&from={since}"
                         "&output=json&filter=statuscode:200&collapse=timestamp:8", timeout=120))[1:]
    print(f"wayback: {len(cdx)} copies since {since}", flush=True)
    for k, snap in enumerate(cdx):
        ts = snap[1]
        try:
            page = get(f"http://web.archive.org/web/{ts}id_/https://www.dramexchange.com/", timeout=90).decode("utf-8", "replace")
            rows, dxi = parse_dramexchange(page, int(ts[:4]))
            # A copy only tells us the prices on the dates it shows; never let an old page move into another year.
            rows = [r for r in rows if r["date"] <= f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"]
            store_memory(rows, [dxi] if dxi else [])
            print(f"  {k + 1}/{len(cdx)} {ts[:8]} {len(rows)} prices", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"  {k + 1}/{len(cdx)} {ts[:8]} failed {exc!r}"[:160], flush=True)
        time.sleep(2)


def memory_view() -> dict:
    series: dict[tuple, list] = {}
    with open(OUT / "memory.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            series.setdefault((r["section"], r["item"]), []).append((r["date"], float(r["avg"])))
    items = []
    for (section, item), pts in series.items():
        pts.sort()
        dates, values = [d for d, _ in pts], [v for _, v in pts]
        items.append({
            "section": section, "item": item, "date": dates[-1], "last": values[-1],
            "chg": changes(dates, values, {"1w": 7, "1m": 30, "3m": 91, "1y": 365}),
            "stale": dates[-1] < (date.today() - timedelta(days=21)).isoformat(),
            "history": {"dates": dates, "values": values},
        })
    dxi = []
    if (OUT / "dxi.csv").exists():
        with open(OUT / "dxi.csv", newline="", encoding="utf-8") as fh:
            dxi = [(r["date"], float(r["dxi"])) for r in csv.DictReader(fh)]
    return {"items": [i for i in items if not i["stale"]], "dxi": {"dates": [d for d, _ in dxi], "values": [v for _, v in dxi]}}


# ---------- GPU rental ----------

def collect_gpu() -> None:
    today = date.today().isoformat()
    out = []
    for name in GPUS:
        q = {"gpu_name": {"eq": name}, "rentable": {"eq": True}, "type": "on-demand", "limit": 2000}
        offers = json.loads(get(f"{VAST}?q={urllib.parse.quote(json.dumps(q))}")).get("offers", [])
        per_gpu = sorted(o["dph_total"] / o["num_gpus"] for o in offers if o.get("num_gpus") and o.get("dph_total"))
        if per_gpu:
            out.append({"date": today, "gpu": name, "offers": len(offers), "gpus": sum(o["num_gpus"] for o in offers),
                        "median": round(statistics.median(per_gpu), 4),
                        "p25": round(per_gpu[len(per_gpu) // 4], 4), "min": round(per_gpu[0], 4)})
        time.sleep(1)
    path = OUT / "gpu.csv"
    known: dict[tuple, dict] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            known = {(r["date"], r["gpu"]): r for r in csv.DictReader(fh)}
    for r in out:
        known[(r["date"], r["gpu"])] = r
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "gpu", "offers", "gpus", "median", "p25", "min"])
        w.writeheader()
        w.writerows(known[k] for k in sorted(known))
    print(f"gpu: {len(out)} types", flush=True)


def gpu_view() -> list[dict]:
    by: dict[str, list] = {}
    with open(OUT / "gpu.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by.setdefault(r["gpu"], []).append(r)
    out = []
    for name in GPUS:
        rows = sorted(by.get(name, []), key=lambda r: r["date"])
        if not rows:
            continue
        dates, med = [r["date"] for r in rows], [float(r["median"]) for r in rows]
        last = rows[-1]
        out.append({"gpu": name, "date": last["date"], "median": med[-1], "p25": float(last["p25"]), "min": float(last["min"]),
                    "offers": int(last["offers"]), "gpus": int(last["gpus"]),
                    "chg": changes(dates, med, {"1w": 7, "1m": 30, "3m": 91}),
                    "history": {"dates": dates, "values": med}})
    return out


# ---------- oil shipping ----------

def portwatch(name: str) -> list[dict]:
    rows, offset = [], 0
    while True:
        params = {"where": f"portname='{name}'", "outFields": "date,n_tanker,n_total,capacity_tanker",
                  "orderByFields": "date", "resultOffset": offset, "resultRecordCount": 2000, "f": "json"}
        d = json.loads(get(f"{PORTWATCH}?{urllib.parse.urlencode(params)}"))
        feats = [f["attributes"] for f in d.get("features", [])]
        rows += feats
        offset += len(feats)
        if not feats or (len(feats) < 2000 and not d.get("exceededTransferLimit")):
            return rows


def shipping_view() -> list[dict]:
    war = date.fromisoformat(WAR_START)
    base_from = (war - timedelta(days=365)).isoformat()
    out = []
    for name in CHOKEPOINTS:
        rows = portwatch(name)
        dates = [r["date"][:10] for r in rows]
        cols = {k: [float(r[k] or 0) for r in rows] for k in ("n_tanker", "n_total", "capacity_tanker")}

        def mean(vals, lo, hi):
            xs = [v for d, v in zip(dates, vals) if lo <= d < hi]
            return sum(xs) / len(xs) if xs else None

        def avg7(vals):
            return [round(sum(vals[max(0, i - 6):i + 1]) / len(vals[max(0, i - 6):i + 1]), 2) for i in range(len(vals))]

        last7_from = (date.fromisoformat(dates[-1]) - timedelta(days=6)).isoformat()
        keep = next(i for i, d in enumerate(dates) if d >= "2023-01-01")
        out.append({
            "name": name, "date": dates[-1],
            "before": {k: mean(v, base_from, WAR_START) for k, v in cols.items()},
            "now": {k: mean(v, last7_from, "9999") for k, v in cols.items()},
            "history": {"dates": dates[keep:], "tankers": avg7(cols["n_tanker"])[keep:], "ships": avg7(cols["n_total"])[keep:],
                        "tanker_capacity": [round(v / 1000) for v in avg7(cols["capacity_tanker"])[keep:]]},
        })
        print(f"shipping: {name} {dates[-1]} tankers/day now {out[-1]['now']['n_tanker']:.1f} before {out[-1]['before']['n_tanker']:.1f}", flush=True)
        time.sleep(1)
    return out


def main(argv: list[str]) -> int:
    if argv[:1] == ["--backfill-memory"]:
        backfill_memory(*(argv[1:2] or []))
    failed = []
    for label, fn in (("memory", collect_memory), ("gpu", collect_gpu)):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — each source stands alone
            failed.append(label)
            print(f"{label} FAILED {exc!r}"[:200], flush=True)
    payload: dict = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "war_start": WAR_START}
    for label, fn in (("memory", memory_view), ("gpu", gpu_view), ("shipping", shipping_view)):
        try:
            payload[label] = fn()
        except Exception as exc:  # noqa: BLE001
            failed.append(label)
            print(f"{label} view FAILED {exc!r}"[:200], flush=True)
    previous = APP / "public" / "data" / "industry.json"
    if previous.exists():  # keep the last good view of a source that failed tonight
        old = json.loads(previous.read_text(encoding="utf-8"))
        for label in ("memory", "gpu", "shipping"):
            payload.setdefault(label, old.get(label))
    payload["failed"] = sorted(set(failed))
    tmp = previous.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    tmp.replace(previous)
    if (APP / "dist" / "data").exists():
        shutil.copy2(previous, APP / "dist" / "data" / "industry.json")
    return 1 if len(failed) == 5 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
