#!/usr/bin/env python3
"""Horizon scanner: what the market is waiting for, how likely it is, and how far it has run ahead.

Three kinds of catalyst go into app/public/data/horizon.json:

    scheduled   dated events that will happen (CPI, FOMC, jobs, earnings). The question is
                the outcome, so each carries the market's expectation where one is traded
                (Kalshi ladders), the options-implied move to the first expiry after it, and
                how far the exposed asset has run into it.
    markets     things that may or may not happen (a ceasefire, Hormuz reopening, a Fed hike),
                priced as probabilities on Polymarket, with 1/7/30-day drift.
    tags        plain-language reads: priced in, crowding toward an outcome, tail risk,
                frontrun into the date. These are heuristics, not forecasts.

Probabilities are snapshotted to data/horizon/snapshots.csv every run, so the drift of
anything we watch can be studied later even where the source keeps no history.

Sources: Polymarket gamma and CLOB price history, Kalshi trade API, Nasdaq earnings
calendar, Cboe delayed option chains, Yahoo daily closes. All public, no keys.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import shutil
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "horizon.json"
OUT = ROOT / "data" / "horizon"
APP = ROOT / "app"
NY = ZoneInfo("America/New_York")
UA = "Mozilla/5.0"  # Yahoo answers 429 to a full browser string from this box

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
NASDAQ_EARNINGS = "https://api.nasdaq.com/api/calendar/earnings?date={}"
CBOE = "https://cdn.cboe.com/api/global/delayed_quotes/options/{}.json"
SPARK = "https://query1.finance.yahoo.com/v7/finance/spark"


def get(url: str, timeout: int = 40, accept: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept-Encoding": "gzip"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return gzip.decompress(body) if r.headers.get("Content-Encoding") == "gzip" else body


def get_json(url: str, tries: int = 3, **kw):
    for attempt in range(tries):
        try:
            return json.loads(get(url, **kw))
        except Exception as e:
            if attempt == tries - 1:
                print(f"horizon.py: {url[:90]} failed ({e})")
                return None
            time.sleep(1.5 + 2 * attempt)


def today_ny() -> date:
    return datetime.now(NY).date()


def fnum(v) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


# ---------- Polymarket ----------

def pm_history(token: str) -> list[tuple[str, float]]:
    data = get_json(f"{CLOB}/prices-history?market={token}&interval=max&fidelity=1440")
    out: dict[str, float] = {}
    for p in (data or {}).get("history", []):
        out[datetime.fromtimestamp(p["t"], timezone.utc).date().isoformat()] = float(p["p"])
    return sorted(out.items())


def ago(hist: list[tuple[str, float]], days: int, now: date) -> float | None:
    cut = (now - timedelta(days=days)).isoformat()
    past = [p for d, p in hist if d <= cut]
    return past[-1] if past else None


def pm_event(cfg: dict, now: date) -> dict | None:
    ev = get_json(f"{GAMMA}/events/slug/{cfg['slug']}")
    if not ev:
        return None
    rows = []
    for m in ev.get("markets", []):
        if m.get("closed") or not m.get("active", True):
            continue
        try:
            p = float(json.loads(m["outcomePrices"])[0])
            token = json.loads(m["clobTokenIds"])[0]
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        end = (m.get("endDate") or "")[:10]
        if end and end < now.isoformat():
            continue  # past its date but not yet settled
        rows.append({"label": m.get("groupItemTitle") or m.get("question") or ev.get("title"), "question": m.get("question"),
                     "p": p, "end": end, "token": token, "threshold": fnum(m.get("groupItemThreshold")),
                     "volume": fnum(m.get("volumeNum")) or 0.0})
    if not rows:
        return None
    # Keep what can still move: a sure thing or a dead one says little. Ladders keep their nearest rungs.
    live = [r for r in rows if 0.01 <= r["p"] <= 0.99] or rows
    live.sort(key=lambda r: (r["end"] or "9999", r["threshold"] if r["threshold"] is not None else 0))
    live = live[: cfg.get("max", 8)]
    if len(rows) == 1:
        live[0]["label"] = "Yes"  # a lone question is already the card's title
    for r in live:
        hist = pm_history(r.pop("token"))
        recent = [x for x in hist if x[0] >= (now - timedelta(days=90)).isoformat()]
        r["hist"] = [[d, round(p, 4)] for d, p in recent]
        for k, n in (("p1", 1), ("p7", 7), ("p30", 30)):
            past = ago(hist, n, now)
            r[k] = round(past, 4) if past is not None else None
        g = cfg.get("good_if")
        r["good_if"] = g.get(r["label"]) if isinstance(g, dict) else g
        r["tags"] = market_tags(r, single=len(live) == 1)
    return {"id": cfg["slug"], "title": cfg.get("label") or ev.get("title"), "theme": cfg.get("theme"), "impact": cfg.get("impact", 1),
            "note": cfg.get("note"), "url": f"https://polymarket.com/event/{cfg['slug']}", "end": (ev.get("endDate") or "")[:10],
            "volume": fnum(ev.get("volume")) or 0.0, "outcomes": live}


def market_tags(r: dict, single: bool) -> list[dict]:
    """Plain reads of one yes/no price. Heuristics on purpose: they say where the surprise sits.

    In a ladder or a pick-one market most rungs are long shots by design, so only a rung the
    market is sure of counts as priced in there; a lone yes/no question is read both ways."""
    p, p30 = r["p"], r.get("p30")
    tags = []
    lean = max(p, 1 - p) if single else p
    if lean >= 0.85:
        tags.append({"key": "priced", "text": f"Priced in: {lean:.0%} {'yes' if p >= 0.5 else 'no'}. The move comes if it doesn't happen."})
    elif 0.35 <= p <= 0.65:
        tags.append({"key": "coin", "text": "Close to a coin flip: either answer moves prices."})
    if p30 is not None:
        d = p - p30
        if abs(d) >= 0.15:
            toward = "yes" if d > 0 else "no"
            tags.append({"key": "crowd", "text": f"Moved {abs(d) * 100:.0f} points toward {toward} in 30 days: the market has been front-running it."})
    if p <= 0.15 and r.get("good_if") in ("yes", "no"):
        good = r["good_if"] == "yes"
        tags.append({"key": "tail-good" if good else "tail-bad",
                     "text": f"{'Cheap upside' if good else 'Tail risk'}: {p:.0%} chance, and the book {'gains' if good else 'loses'} if it happens."})
    return tags


# ---------- Kalshi: macro dates and what the market expects ----------

def mid(m: dict) -> float | None:
    b, a = fnum(m.get("yes_bid_dollars")), fnum(m.get("yes_ask_dollars"))
    if b is not None and a is not None and a > 0 and a - b <= 0.15:
        return (a + b) / 2
    return fnum(m.get("last_price_dollars"))


def ladder_median(points: list[tuple[float, float]]) -> float | None:
    """P(above x) at each strike -> the strike where it crosses one half."""
    pts = sorted(points)
    if len(pts) < 3:
        return None
    best = 1.0
    mono = []
    for x, p in pts:  # quotes are noisy; force the ladder to fall
        best = min(best, p)
        mono.append((x, best))
    for (x0, p0), (x1, p1) in zip(mono, mono[1:]):
        if p0 >= 0.5 >= p1 and p0 != p1:
            return x0 + (p0 - 0.5) / (p0 - p1) * (x1 - x0)
    return None


def kalshi_events(cfg: dict, now: date, horizon: date) -> list[dict]:
    data = get_json(f"{KALSHI}/events?series_ticker={cfg['series']}&status=open&limit=6")
    out = []
    for ev in (data or {}).get("events", []):
        mk = get_json(f"{KALSHI}/markets?event_ticker={ev['event_ticker']}&limit=100")
        ms = (mk or {}).get("markets", [])
        when = sorted(m.get("occurrence_datetime") or m.get("expected_expiration_time") or "" for m in ms if m.get("occurrence_datetime") or m.get("expected_expiration_time"))
        if not when:
            continue
        at = datetime.fromisoformat(when[0].replace("Z", "+00:00")).astimezone(NY)
        if not now <= at.date() <= horizon:
            continue
        item = {"date": at.date().isoformat(), "time": at.strftime("%H:%M"), "series": cfg["series"],
                "period": ev.get("sub_title") or ev.get("title")}
        ladder = [(fnum(m.get("floor_strike")), mid(m)) for m in ms if m.get("strike_type") in ("greater", "greater_or_equal")]
        ladder = [(x, p) for x, p in ladder if x is not None and p is not None]
        if ladder:
            med = ladder_median(ladder)
            scale = cfg.get("scale", 1)
            if med is not None:
                item["expect"] = {"median": round(med * scale, 3), "unit": cfg.get("unit", ""), "signed": cfg.get("signed", True),
                                  "ladder": [[round(x * scale, 3), round(p, 3)] for x, p in sorted(ladder)]}
        else:
            cats = [(m.get("yes_sub_title") or m["ticker"], mid(m)) for m in ms]
            cats = sorted(((t, p) for t, p in cats if p is not None), key=lambda c: -c[1])
            if cats:
                item["expect"] = {"outcomes": [[t, round(p, 3)] for t, p in cats[:4]]}
        out.append(item)
    return out


def macro_calendar(conf: dict, now: date, horizon: date) -> list[dict]:
    series = conf["kalshi_series"]
    by_series = {}
    with ThreadPoolExecutor(4) as ex:
        for cfg, items in zip(series, ex.map(lambda c: kalshi_events(c, now, horizon), series)):
            by_series[cfg["series"]] = (cfg, items)
    events = []
    for cfg, items in by_series.values():
        if cfg.get("merge_into"):
            continue
        for it in items:
            ev = {"date": it["date"], "time": it["time"], "name": cfg["name"], "kind": cfg["kind"], "impact": cfg["impact"],
                  "asset": cfg["asset"], "period": it["period"], "expect": [], "source": "Kalshi"}
            if "expect" in it:
                ev["expect"].append({"name": cfg["name"], **it["expect"]})
            for other, extra in by_series.values():  # core CPI rides with CPI, unemployment with payrolls
                if other.get("merge_into") == cfg["series"]:
                    for x in extra:
                        if x["date"] == it["date"] and "expect" in x:
                            ev["expect"].append({"name": other["name"], **x["expect"]})
            events.append(ev)
    return events


# ---------- earnings ----------

def earnings_calendar(conf: dict, now: date, horizon: date) -> list[dict]:
    key = set(conf["key_earnings"])
    universe = set()
    ranking = APP / "public" / "data" / "ranking.json"
    if ranking.exists():
        universe = {r["ticker"] for r in json.loads(ranking.read_text())["rows"]}
    days = [now + timedelta(days=i) for i in range((horizon - now).days + 1)]
    days = [d for d in days if d.weekday() < 5]

    def one(d: date):
        data = get_json(NASDAQ_EARNINGS.format(d.isoformat()), accept="application/json", tries=2)
        return d, ((data or {}).get("data") or {}).get("rows") or []

    events = []
    with ThreadPoolExecutor(4) as ex:
        for d, rows in ex.map(one, days):
            for r in rows:
                sym = r.get("symbol")
                if sym not in key and sym not in universe:
                    continue
                t = {"time-after-hours": "after close", "time-pre-market": "before open"}.get(r.get("time"), "time n/a")
                events.append({"date": d.isoformat(), "time": t, "name": f"{sym} results", "ticker": sym, "kind": "earnings",
                               "impact": 3 if sym in ("NVDA", "MSFT", "GOOGL", "META", "AMZN", "MU") else 2 if sym in key else 1,
                               "asset": sym, "key": sym in key, "company": r.get("name"),
                               "expect": [{"name": "EPS forecast", "text": r.get("epsForecast")}] if r.get("epsForecast") else [],
                               "source": "Nasdaq"})
    return events


# ---------- prices: run-up into the date, options-implied move ----------

def closes(symbols: list[str]) -> dict[str, list[tuple[date, float]]]:
    out = {}
    for i in range(0, len(symbols), 20):
        batch = symbols[i:i + 20]
        q = urllib.parse.urlencode({"symbols": ",".join(batch), "range": "1y", "interval": "1d"})
        data = get_json(f"{SPARK}?{q}")
        for item in ((data or {}).get("spark") or {}).get("result") or []:
            try:
                x = item["response"][0]
                pts = [(datetime.fromtimestamp(t, NY).date(), c) for t, c in zip(x["timestamp"], x["indicators"]["quote"][0]["close"]) if c]
                out[item["symbol"]] = pts
            except (KeyError, IndexError, TypeError):
                pass
    return out


def runup(pts: list[tuple[date, float]]) -> dict | None:
    """Return over 20 and 60 sessions, and the 20-session move in units of the stock's own volatility."""
    if len(pts) < 80:
        return None
    px = [c for _, c in pts]
    rets = [math.log(b / a) for a, b in zip(px[-121:], px[-120:])]
    sd = (sum(r * r for r in rets) / len(rets) - (sum(rets) / len(rets)) ** 2) ** 0.5
    r20 = px[-1] / px[-21] - 1
    r60 = px[-1] / px[-61] - 1
    z20 = math.log(px[-1] / px[-21]) / (sd * math.sqrt(20)) if sd else None
    hi = max(px[-250:])
    return {"r20": round(r20, 4), "r60": round(r60, 4), "z20": round(z20, 2) if z20 is not None else None,
            "from_high": round(px[-1] / hi - 1, 4), "vol": round(sd * math.sqrt(252), 3)}


def chain(symbol: str) -> dict | None:
    data = get_json(CBOE.format(symbol), tries=2)
    return (data or {}).get("data")


def implied_move(ch: dict, after: date) -> dict | None:
    """At-the-money straddle for the first expiry on or after `after`, as a share of the price."""
    spot = fnum(ch.get("current_price"))
    if not spot:
        return None
    by_exp: dict[date, dict[float, dict]] = {}
    for o in ch.get("options", []):
        code = o["option"]
        tail = code[-15:]  # YYMMDD + C/P + strike*1000
        try:
            exp = datetime.strptime(tail[:6], "%y%m%d").date()
            kind, strike = tail[6], int(tail[7:]) / 1000
        except ValueError:
            continue
        b, a = fnum(o.get("bid")), fnum(o.get("ask"))
        if not b or not a or a < b:
            continue
        by_exp.setdefault(exp, {}).setdefault(strike, {})[kind] = (a + b) / 2
    exps = sorted(e for e in by_exp if e >= after)
    if not exps:
        return None
    exp = exps[0]
    pairs = [(abs(k - spot), k, v) for k, v in by_exp[exp].items() if "C" in v and "P" in v]
    if not pairs:
        return None
    _, k, v = min(pairs)
    return {"move": round((v["C"] + v["P"]) / spot, 4), "expiry": exp.isoformat(), "strike": k}


def event_tags(ev: dict) -> list[dict]:
    tags = []
    ru = ev.get("runup")
    if ru and ru.get("z20") is not None:
        z = ru["z20"]
        if z >= 1.5:
            tags.append({"key": "frontrun-up", "text": f"{ev['asset']} ran up {ru['r20']:+.0%} in 20 sessions ({z:.1f}σ): good news may be priced in, sell-the-news risk."})
        elif z <= -1.5:
            tags.append({"key": "frontrun-down", "text": f"{ev['asset']} fell {ru['r20']:+.0%} in 20 sessions ({z:.1f}σ): fear is priced in, room for relief if it passes."})
    im = ev.get("implied")
    if im and ru and ru.get("vol"):
        days = max((date.fromisoformat(im["expiry"]) - date.fromisoformat(ev["as_of"])).days, 1)
        normal = ru["vol"] * math.sqrt(days / 365) * 0.8  # a straddle is worth about 0.8 sigma of the move
        if normal and im["move"] > 1.5 * normal:
            tags.append({"key": "event-premium", "text": f"Options price a {im['move']:.1%} move to {im['expiry']}, about {im['move'] / normal:.1f}× a normal stretch: the market expects this one to matter."})
    return tags


# ---------- snapshots ----------

def snapshot(markets: list[dict], now: date) -> None:
    path = OUT / "snapshots.csv"
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            rows = [r for r in csv.DictReader(fh) if r["date"] != now.isoformat()]
    for m in markets:
        for o in m["outcomes"]:
            rows.append({"date": now.isoformat(), "source": "polymarket", "event": m["id"], "outcome": o["label"], "p": o["p"]})
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "source", "event", "outcome", "p"])
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def main() -> int:
    conf = json.loads(CONFIG.read_text())
    now = today_ny()
    horizon = now + timedelta(days=conf.get("horizon_days", 75))

    with ThreadPoolExecutor(4) as ex:
        markets = [m for m in ex.map(lambda c: pm_event(c, now), conf["markets"]) if m]
    by_slug = {m["id"]: m for m in markets}

    scheduled = macro_calendar(conf, now, horizon) + earnings_calendar(conf, now, horizon)
    for s in conf.get("scheduled", []):
        if now.isoformat() <= s["date"] <= horizon.isoformat():
            scheduled.append({"time": "", "expect": [], "source": "manual", **s})
    for ev in scheduled:
        ev["as_of"] = now.isoformat()
        if ev.get("market") in by_slug:
            ev["market_title"] = by_slug[ev["market"]]["title"]

    assets = sorted({ev["asset"] for ev in scheduled if ev.get("asset")} | {"SPY", "QQQ", "SMH"})
    px = closes(assets)
    chains = {}
    wanted = sorted({ev["asset"] for ev in scheduled if ev.get("key", True) and ev["impact"] >= 2})
    with ThreadPoolExecutor(4) as ex:
        for sym, ch in zip(wanted, ex.map(chain, wanted)):
            if ch:
                chains[sym] = ch
    for ev in scheduled:
        a = ev.get("asset")
        if a in px:
            ev["runup"] = runup(px[a])
        if a in chains:
            d = date.fromisoformat(ev["date"])
            # After-close earnings react the next session; anything else trades on the day.
            after = d + timedelta(days=1) if ev.get("time") == "after close" else d
            if ev["kind"] != "earnings" and ev.get("time", "") >= "16:00":
                after = d + timedelta(days=1)
            ev["implied"] = implied_move(chains[a], after)
        ev["tags"] = event_tags(ev)
    scheduled.sort(key=lambda e: (e["date"], -e["impact"]))

    snapshot(markets, now)
    markets.sort(key=lambda m: (-m["impact"], m["theme"] or "", m["title"]))
    payload = {"as_of": now.isoformat(), "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "horizon": horizon.isoformat(), "scheduled": scheduled, "markets": markets,
               "assets": {a: runup(px[a]) for a in ("SPY", "QQQ", "SMH") if a in px}}
    data = APP / "public" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "horizon.json").write_text(json.dumps(payload, separators=(",", ":")))
    if (APP / "dist" / "data").exists():
        shutil.copy2(data / "horizon.json", APP / "dist" / "data" / "horizon.json")
    n_out = sum(len(m["outcomes"]) for m in markets)
    print(f"horizon.py: {len(scheduled)} dated events to {horizon}, {len(markets)} probability markets ({n_out} outcomes), "
          f"{len(chains)} option chains")
    return 0


if __name__ == "__main__":
    sys.exit(main())
