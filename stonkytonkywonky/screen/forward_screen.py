#!/usr/bin/env python3
"""Cheap-to-self forward-earnings screen. Standard library only.

Forward EPS history comes from ForwardEstimates (recorded consensus, plus
reconstruction B where it validated) when present, else from Yahoo/Nasdaq.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
CACHE_DIR = Path.home() / ".cache" / "stock-research" / "yahoo-fundamentals"
DEFAULT_OUT = Path.home() / ".cache" / "stock-research" / "out"
CACHE_MAX_AGE_DAYS = 14
YAHOO_CHART = "https://query{n}.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_TS = (
    "https://query{n}.finance.yahoo.com/ws/fundamentals-timeseries/"
    "v1/finance/timeseries/{symbol}"
)
NASDAQ_FORECAST = "https://api.nasdaq.com/api/analyst/{symbol}/earnings-forecast"
NASDAQ_SURPRISE = "https://api.nasdaq.com/api/company/{symbol}/earnings-surprise"
NASDAQ_HIST = (
    "https://api.nasdaq.com/api/quote/{symbol}/historical"
    "?assetclass=stocks&fromdate={start}&todate={end}&limit=5000&offset=0"
)
NASDAQ_INFO = "https://api.nasdaq.com/api/quote/{symbol}/info?assetclass=stocks"
WINDOWS = (90, 180, 365)
DEFAULT_LOOKBACK = 1095
HORIZONS = (63, 126, 252)  # trading days: ~3, 6 and 12 months
REVISION_HOLD = -0.02
CHEAP_PCT, RICH_PCT = 16, 84  # P/E percentiles of the lookback window; ±1σ coverage without the mean  # next-year EPS may slip 2% in 90 days and still count as holding
ESTIMATES_DIR = Path(
    os.environ.get(
        "FORWARD_ESTIMATES_DIR",
        Path.home() / "TheLab" / "Documents" / "Trading" / "ForwardEstimates",
    )
)
COUNTRY_SUFFIXES = {
    "KS", "KQ", "T", "TW", "HK", "L", "PA", "DE", "SW", "TO", "AX",
    "SI", "NS", "BO", "SA", "MX", "F", "MI", "AS", "ST", "CO", "HE",
    "OL", "IR", "SS", "MC", "BR", "VI",
}


def http_json(url: str, extra_headers: dict[str, str] | None = None, retries: int = 4) -> dict:
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise
    raise RuntimeError(f"request failed: {url}") from last_err


def yahoo_json(template: str, symbol: str, query: dict[str, str] | None = None) -> dict:
    q = f"?{urllib.parse.urlencode(query)}" if query else ""
    errors = []
    for n in (2, 1):
        url = template.format(n=n, symbol=urllib.parse.quote(symbol)) + q
        try:
            return http_json(url, retries=2)
        except Exception as exc:  # noqa: BLE001 — fallback host is the recovery
            errors.append(f"query{n}: {exc}")
    raise RuntimeError(f"Yahoo failed for {symbol}: {'; '.join(errors)}")


def nasdaq_json(url: str) -> dict | None:
    headers = {
        "Origin": "https://www.nasdaq.com",
        "Referer": "https://www.nasdaq.com/",
    }
    try:
        return http_json(url, extra_headers=headers)
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 400}:
            return None
        raise


def yahoo_symbol(ticker: str) -> str:
    t = ticker.strip().upper()
    if "." in t:
        base, suffix = t.rsplit(".", 1)
        if suffix not in COUNTRY_SUFFIXES and len(suffix) <= 2:
            return f"{base}-{suffix}"
        return t
    return t.replace(".", "-")


def nasdaq_symbol(ticker: str) -> str | None:
    t = ticker.strip().upper()
    if "." in t:
        base, suffix = t.rsplit(".", 1)
        if suffix in COUNTRY_SUFFIXES:
            return None
        return f"{base}.{suffix}"
    return t.replace("-", ".")


def parse_day(ts: int) -> date:
    return datetime.fromtimestamp(ts, timezone.utc).date()


def _parse_money(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = str(text).replace("$", "").replace(",", "").strip()
    if cleaned in {"", "N/A", "n/a", "--"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch_nasdaq_prices(symbol: str) -> tuple[list[date], list[float], dict] | None:
    today = date.today()
    try:
        start = today.replace(year=today.year - 10)
    except ValueError:
        start = today.replace(year=today.year - 10, day=28)
    payload = nasdaq_json(
        NASDAQ_HIST.format(symbol=symbol, start=start.isoformat(), end=today.isoformat())
    )
    rows = (((payload or {}).get("data") or {}).get("tradesTable") or {}).get("rows") or []
    points: list[tuple[date, float]] = []
    for row in rows:
        raw_day = row.get("date")
        px = _parse_money(row.get("close"))
        if not raw_day or px is None or px <= 0:
            continue
        try:
            day = datetime.strptime(raw_day, "%m/%d/%Y").date()
        except ValueError:
            continue
        points.append((day, px))
    points.sort()
    if len(points) < 30:
        return None
    info = nasdaq_json(NASDAQ_INFO.format(symbol=symbol)) or {}
    info_data = info.get("data") or {}
    primary = info_data.get("primaryData") or {}
    last_px = _parse_money(primary.get("lastSalePrice"))
    last_day = today
    if last_px and (not points or points[-1][1] != last_px):
        # Include the live last sale when it is newer than the daily table.
        if not points or points[-1][0] < today:
            points.append((last_day, last_px))
            points.sort()
    dates = [p[0] for p in points]
    values = [p[1] for p in points]
    meta = {
        "source": "nasdaq",
        "currency": "USD",
        "longName": info_data.get("companyName") or symbol,
    }
    return dates, values, meta


def fetch_yahoo_chart(symbol: str, rang: str = "5y") -> tuple[list[date], list[float], dict]:
    data = yahoo_json(
        YAHOO_CHART,
        symbol,
        {"range": rang, "interval": "1d", "events": "div,split"},
    )
    result = (data.get("chart") or {}).get("result") or []
    if not result:
        err = (data.get("chart") or {}).get("error")
        raise RuntimeError(f"no Yahoo chart for {symbol}: {err}")
    row = result[0]
    meta = row.get("meta") or {}
    stamps = row.get("timestamp") or []
    indicators = row.get("indicators") or {}
    adj = ((indicators.get("adjclose") or [{}])[0].get("adjclose")) or []
    close = ((indicators.get("quote") or [{}])[0].get("close")) or []
    prices = adj if adj and any(v is not None for v in adj) else close
    dates: list[date] = []
    values: list[float] = []
    for ts, px in zip(stamps, prices):
        if px is None or not math.isfinite(px):
            continue
        dates.append(parse_day(ts))
        values.append(float(px))
    if len(dates) < 30:
        raise RuntimeError(f"Yahoo chart for {symbol} has only {len(dates)} days")
    meta = dict(meta)
    meta["source"] = "yahoo"
    return dates, values, meta


def fetch_prices(ticker: str, ysym: str, nsym: str | None) -> tuple[list[date], list[float], dict]:
    errors: list[str] = []
    if nsym:
        try:
            got = fetch_nasdaq_prices(nsym)
            if got:
                return got
            errors.append("Nasdaq history too short")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Nasdaq: {exc}")
    try:
        return fetch_yahoo_chart(ysym)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Yahoo: {exc}")
    raise RuntimeError(f"no price history for {ticker}: {'; '.join(errors)}")


def _ts_points(payload: dict, key: str) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    for item in (payload.get("timeseries") or {}).get("result") or []:
        series = item.get(key) or []
        for point in series:
            if not point:
                continue
            raw = (point.get("reportedValue") or {}).get("raw")
            as_of = point.get("asOfDate")
            if raw is None or not as_of:
                continue
            out.append((date.fromisoformat(as_of), float(raw)))
    out.sort()
    return out


def _empty_fundamentals() -> dict[str, list[tuple[date, float]]]:
    return {"fwd_pe": [], "trail_pe": [], "q_eps": [], "a_eps": []}


def _cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol}.json"


def _load_fundamentals_cache(symbol: str) -> dict[str, list[tuple[date, float]]] | None:
    path = _cache_path(symbol)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fetched = payload.get("fetched_at")
    try:
        fetched_day = date.fromisoformat(fetched)
    except (TypeError, ValueError):
        return None
    if date.today() - fetched_day > timedelta(days=CACHE_MAX_AGE_DAYS):
        return None
    out = _empty_fundamentals()
    for key in out:
        out[key] = [(date.fromisoformat(d), float(v)) for d, v in payload.get(key) or []]
    out["_cached_at"] = fetched  # type: ignore[index]
    return out


def _save_fundamentals_cache(symbol: str, data: dict[str, list[tuple[date, float]]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    blob = {
        "fetched_at": date.today().isoformat(),
        **{key: [[d.isoformat(), v] for d, v in data[key]] for key in ("fwd_pe", "trail_pe", "q_eps", "a_eps")},
    }
    _cache_path(symbol).write_text(json.dumps(blob), encoding="utf-8")


def fetch_fundamentals(symbol: str) -> dict[str, list[tuple[date, float]]]:
    period1 = int(datetime(2016, 1, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.now(timezone.utc).timestamp())
    types = ",".join(
        [
            "trailingForwardPeRatio",
            "trailingPeRatio",
            "quarterlyDilutedEPS",
            "annualDilutedEPS",
        ]
    )
    try:
        payload = yahoo_json(
            YAHOO_TS,
            symbol,
            {
                "symbol": symbol,
                "type": types,
                "period1": str(period1),
                "period2": str(period2),
            },
        )
        live = {
            "fwd_pe": _ts_points(payload, "trailingForwardPeRatio"),
            "trail_pe": _ts_points(payload, "trailingPeRatio"),
            "q_eps": _ts_points(payload, "quarterlyDilutedEPS"),
            "a_eps": _ts_points(payload, "annualDilutedEPS"),
        }
        if live["fwd_pe"]:
            _save_fundamentals_cache(symbol, live)
            live["source"] = "yahoo"  # type: ignore[index]
            return live
    except Exception:
        pass
    cached = _load_fundamentals_cache(symbol)
    if cached:
        cached["source"] = f"yahoo-cache {cached.pop('_cached_at', '')}".strip()  # type: ignore[index]
        return cached
    empty = _empty_fundamentals()
    empty["source"] = "unavailable"  # type: ignore[index]
    return empty


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def local_history(ticker: str, allow_biased: bool = False) -> dict | None:
    """Daily NTM EPS from ForwardEstimates: recorded snapshots, else reconstruction B.

    Recorded snapshots are genuine point-in-time consensus. B (backfill.py) values
    each future quarter at its pre-report consensus, so it carries look-ahead;
    it is only used where validation graded it good or caution.
    """
    recorded = [r for r in _read_rows(ESTIMATES_DIR / "data" / "snapshots.csv") if r["ticker"] == ticker]
    grades = {r["ticker"]: r for r in _read_rows(ESTIMATES_DIR / "data" / "history" / "validation.csv")}
    grade = (grades.get(ticker) or {}).get("grade") or None
    b_rows = _read_rows(ESTIMATES_DIR / "data" / "history" / "ntm_b" / f"{ticker}.csv")
    if not recorded and not b_rows:
        return None
    use_b = bool(b_rows) and (grade in {"good", "caution"} or allow_biased)
    first_rec = min((date.fromisoformat(r["date"]) for r in recorded), default=None)
    points: dict[date, tuple[float | None, float | None]] = {}
    if use_b:
        for r in b_rows:
            day = date.fromisoformat(r["date"])
            if first_rec is None or day < first_rec:
                points[day] = (_num(r["close"]), _num(r["ntm_eps_b"]))
    for r in recorded:
        points[date.fromisoformat(r["date"])] = (_num(r["price"]), _num(r["ntm_eps"]))
    latest = max(recorded, key=lambda r: r["date"]) if recorded else None
    return {
        "points": sorted(points.items()),
        "grade": grade,
        "b_used": use_b,
        "b_first": b_rows[0]["date"] if use_b else None,
        "recorded_days": len(recorded),
        "recorded_first": None if first_rec is None else first_rec.isoformat(),
        "latest": latest,
    }


def revision_90d(latest: dict | None) -> float | None:
    """Change in next-fiscal-year consensus over 90 days, from the recorded snapshot."""
    if not latest:
        return None
    now, ago = _num(latest.get("fy1_eps")), _num(latest.get("fy1_eps_90d_ago"))
    if now is None or ago is None or ago <= 0:
        return None
    return now / ago - 1.0


def classify(pct: float | None, rev: float | None) -> str:
    """Percentiles, not mean ± σ: a spell of near-zero EPS sends P/E past 200× and drags a mean."""
    if pct is None:
        return "n/a"
    if pct <= CHEAP_PCT:
        if rev is None:
            return "cheap, revisions unknown"
        return "CHEAP, estimates holding" if rev >= REVISION_HOLD else "cheap, estimates falling"
    if pct >= RICH_PCT:
        return "expensive"
    return "fair"


def _forecast_rows(block: dict | None) -> list[dict]:
    if not block:
        return []
    return list(block.get("rows") or [])


def fetch_nasdaq(symbol: str | None) -> dict:
    empty = {"forecast": None, "surprise": None}
    if not symbol:
        return empty
    forecast = nasdaq_json(NASDAQ_FORECAST.format(symbol=symbol))
    surprise = nasdaq_json(NASDAQ_SURPRISE.format(symbol=symbol))
    return {
        "forecast": None if not forecast else forecast.get("data"),
        "surprise": None if not surprise else surprise.get("data"),
    }


def close_on_or_before(dates: list[date], prices: list[float], day: date) -> float | None:
    lo, hi = 0, len(dates) - 1
    ans = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if dates[mid] <= day:
            ans = prices[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def implied_eps_snapshots(
    dates: list[date], prices: list[float], fwd_pe: list[tuple[date, float]]
) -> list[tuple[date, float, float]]:
    snaps: list[tuple[date, float, float]] = []
    for day, pe in fwd_pe:
        if pe <= 0 or not math.isfinite(pe):
            continue
        px = close_on_or_before(dates, prices, day)
        if px is None or px <= 0:
            continue
        snaps.append((day, px / pe, pe))
    return snaps


def carry_series(
    dates: list[date], snaps: list[tuple[date, float, float]]
) -> list[float | None]:
    carried: list[float | None] = []
    j = -1
    for day in dates:
        while j + 1 < len(snaps) and snaps[j + 1][0] <= day:
            j += 1
        carried.append(None if j < 0 else snaps[j][1])
    return carried


def _quantile(ordered: list[float], q: float) -> float:
    pos = (len(ordered) - 1) * q
    i = int(pos)
    j = min(i + 1, len(ordered) - 1)
    return ordered[i] + (ordered[j] - ordered[i]) * (pos - i)


def window_stats(dates: list[date], values: list[float | None], last: date, days: int) -> dict:
    start = last - timedelta(days=days)
    window = [
        v
        for d, v in zip(dates, values)
        if start <= d <= last and v is not None and math.isfinite(v)
    ]
    current = None
    for d, v in zip(reversed(dates), reversed(values)):
        if d <= last and v is not None and math.isfinite(v):
            current = v
            break
    out = {
        "window_days": days,
        "n": len(window),
        "current": current,
        "mean": None,
        "stdev": None,
        "z": None,
        "median": None,
        "p16": None,
        "p84": None,
        "pct": None,
    }
    if current is None or len(window) < max(15, days // 8):
        return out
    ordered = sorted(window)
    out["median"] = _quantile(ordered, 0.5)
    out["p16"] = _quantile(ordered, CHEAP_PCT / 100)
    out["p84"] = _quantile(ordered, RICH_PCT / 100)
    out["pct"] = 100.0 * bisect.bisect_left(ordered, current) / len(ordered)
    mean = statistics.fmean(window)
    stdev = statistics.stdev(window) if len(window) > 1 else 0.0
    out["mean"] = mean
    out["stdev"] = stdev
    if stdev > 1e-12:
        out["z"] = (current - mean) / stdev
    return out


def next_return(prices: list[float], i: int, horizon: int) -> float | None:
    j = i + horizon
    if j >= len(prices) or prices[i] <= 0:
        return None
    return prices[j] / prices[i] - 1.0


def walkforward_pe(
    dates: list[date],
    prices: list[float],
    pe: list[float | None],
    lookback: int = DEFAULT_LOOKBACK,
    horizons: tuple[int, ...] = HORIZONS,
) -> dict:
    """Each day, the P/E percentile within the prior `lookback` calendar days; returns what followed."""
    every: dict[int, list[float]] = {h: [] for h in horizons}
    cheap: dict[int, list[float]] = {h: [] for h in horizons}
    rich: dict[int, list[float]] = {h: [] for h in horizons}
    cheap_days = rich_days = scored = 0
    need = max(15, lookback // 8)
    lo = 0
    window: list[float] = []  # kept sorted
    for i, (day, multiple) in enumerate(zip(dates, pe)):
        if multiple is not None and multiple > 0:
            bisect.insort(window, multiple)
        while dates[lo] < day - timedelta(days=lookback):
            old = pe[lo]
            if old is not None and old > 0:
                del window[bisect.bisect_left(window, old)]
            lo += 1
        if multiple is None or multiple <= 0 or len(window) < need:
            continue
        pct = 100.0 * bisect.bisect_left(window, multiple) / len(window)
        scored += 1
        for h in horizons:
            nxt = next_return(prices, i, h)
            if nxt is not None:
                every[h].append(nxt)
        if pct <= CHEAP_PCT:
            cheap_days += 1
            bucket = cheap
        elif pct >= RICH_PCT:
            rich_days += 1
            bucket = rich
        else:
            continue
        for h in horizons:
            nxt = next_return(prices, i, h)
            if nxt is not None:
                bucket[h].append(nxt)

    def _avg(xs: list[float]) -> float | None:
        return None if not xs else statistics.fmean(xs)

    return {
        "lookback_days": lookback,
        "scored_days": scored,
        "cheap_days": cheap_days,
        "expensive_days": rich_days,
        "horizons": {
            h: {
                "all_avg": _avg(every[h]),
                "all_n": len(every[h]),
                "cheap_avg": _avg(cheap[h]),
                "cheap_n": len(cheap[h]),
                "expensive_avg": _avg(rich[h]),
                "expensive_n": len(rich[h]),
            }
            for h in horizons
        },
    }


def ntm_from_quarters(rows: list[dict], as_of: date) -> dict | None:
    future = []
    for row in rows:
        label = row.get("fiscalEnd") or ""
        try:
            end = datetime.strptime(label, "%b %Y").date()
        except ValueError:
            continue
        # Fiscal-end month is the quarter's last month; keep quarters not yet reported.
        if end < as_of.replace(day=1) - timedelta(days=40):
            continue
        eps = row.get("consensusEPSForecast")
        if eps is None:
            continue
        future.append((end, float(eps), row))
    future.sort()
    picked = future[:4]
    if len(picked) < 3:
        return None
    return {
        "eps": sum(p[1] for p in picked),
        "quarters": [
            {"fiscal_end": p[0].isoformat(), "eps": p[1], "estimates": p[2].get("noOfEstimates")}
            for p in picked
        ],
    }


def yearly_growth(rows: list[dict]) -> list[dict]:
    years = []
    for row in rows:
        eps = row.get("consensusEPSForecast")
        if eps is None:
            continue
        years.append(
            {
                "fiscal_end": row.get("fiscalEnd"),
                "eps": float(eps),
                "high": row.get("highEPSForecast"),
                "low": row.get("lowEPSForecast"),
                "estimates": row.get("noOfEstimates"),
                "rev_up_4w": row.get("up"),
                "rev_down_4w": row.get("down"),
            }
        )
    for i, year in enumerate(years):
        if i == 0:
            year["growth_vs_prev"] = None
            continue
        prev = years[i - 1]["eps"]
        year["growth_vs_prev"] = None if prev in (None, 0) else year["eps"] / prev - 1.0
    return years


def _month_end(label: str) -> date | None:
    try:
        start = datetime.strptime(label, "%b %Y").date()
    except (TypeError, ValueError):
        return None
    if start.month == 12:
        return date(start.year, 12, 31)
    return date(start.year, start.month + 1, 1) - timedelta(days=1)


def surprise_table(data: dict | None) -> list[dict]:
    if not data:
        return []
    rows = ((data.get("earningsSurpriseTable") or {}).get("rows")) or []
    out = []
    for row in rows:
        out.append(
            {
                "fiscal_end": row.get("fiscalQtrEnd"),
                "reported": row.get("dateReported"),
                "eps": row.get("eps"),
                "consensus": row.get("consensusForecast"),
                "surprise_pct": row.get("percentageSurprise"),
            }
        )
    return out


def surprise_actuals(rows: list[dict]) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    for row in rows:
        day = _month_end(str(row.get("fiscal_end") or ""))
        try:
            eps = float(row.get("eps"))
        except (TypeError, ValueError):
            continue
        if day:
            out.append((day, eps))
    out.sort()
    return out


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _segments(xs: list[float], ys: list[float | None]) -> list[list[tuple[float, float]]]:
    segs: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    for x, y in zip(xs, ys):
        if y is None or not math.isfinite(y):
            if cur:
                segs.append(cur)
                cur = []
            continue
        cur.append((x, y))
    if cur:
        segs.append(cur)
    return segs


def _line_path(seg: list[tuple[float, float]], sx, sy) -> str:
    parts = [f"M {sx(x):.1f},{sy(y):.1f}" for x, y in seg[:1]]
    parts += [f"L {sx(x):.1f},{sy(y):.1f}" for x, y in seg[1:]]
    return " ".join(parts)


def render_svg(
    title: str,
    dates: list[date],
    eps: list[float | None],
    pe: list[float | None],
    actual_q: list[tuple[date, float]],
    pe_mid: float | None,
    pe_band: tuple[float | None, float | None],
    lookback: int = 365,
) -> str:
    width, height = 920, 640
    pad_l, pad_r, pad_t, pad_b = 64, 24, 40, 36
    gap = 28
    plot_w = width - pad_l - pad_r
    plot_h = (height - pad_t - pad_b - gap) / 2
    xs = [(d - dates[0]).days for d in dates]
    x0, x1 = 0, max(xs[-1], 1)

    def panel_y(values: list[float | None], extras: list[float]) -> tuple[float, float]:
        nums = [v for v in values if v is not None and math.isfinite(v)] + extras
        if not nums:
            return 0.0, 1.0
        lo, hi = min(nums), max(nums)
        if lo == hi:
            lo -= abs(lo) * 0.05 + 0.1
            hi += abs(hi) * 0.05 + 0.1
        pad = (hi - lo) * 0.08
        return lo - pad, hi + pad

    def axis(y_top: float, y0: float, y1: float, ylabel: str, series, extras, color: str, mid=None, band=None, markers=None) -> str:
        def sx(x: float) -> float:
            return pad_l + (x - x0) / (x1 - x0) * plot_w

        def sy(y: float) -> float:
            return y_top + plot_h - (y - y0) / (y1 - y0) * plot_h

        parts = [
            f'<rect x="{pad_l}" y="{y_top}" width="{plot_w}" height="{plot_h}" fill="#0f1419" stroke="#2a333c"/>',
            f'<text x="16" y="{y_top + 16}" fill="#9aa7b2" font-size="12" font-family="sans-serif">{svg_escape(ylabel)}</text>',
        ]
        if mid is not None and band and None not in band:
            band_top = sy(band[1])
            band_h = sy(band[0]) - band_top
            parts.append(
                f'<rect x="{pad_l}" y="{band_top:.1f}" width="{plot_w}" height="{max(band_h, 0):.1f}" fill="#1d4e3c" fill-opacity="0.35"/>'
            )
            parts.append(
                f'<line x1="{pad_l}" y1="{sy(mid):.1f}" x2="{pad_l + plot_w}" y2="{sy(mid):.1f}" stroke="#3dd68c" stroke-dasharray="4 4" stroke-width="1"/>'
            )
        for seg in _segments(xs, series):
            parts.append(
                f'<path d="{_line_path(seg, sx, sy)}" fill="none" stroke="{color}" stroke-width="2"/>'
            )
        if markers:
            for day, val in markers:
                if day < dates[0] or day > dates[-1]:
                    continue
                x = sx((day - dates[0]).days)
                y = sy(val)
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#e8c547"/>')
        # y ticks
        for i in range(5):
            yv = y0 + (y1 - y0) * i / 4
            y = sy(yv)
            parts.append(
                f'<text x="{pad_l - 8}" y="{y + 4:.1f}" fill="#7d8b96" font-size="10" font-family="sans-serif" text-anchor="end">{yv:.2f}</text>'
            )
        return "\n".join(parts)

    eps_lo, eps_hi = panel_y(eps, [v for _, v in actual_q])
    pe_extras = []
    if pe_mid is not None:
        pe_extras.append(pe_mid)
        pe_extras.extend(v for v in pe_band if v is not None)
    pe_lo, pe_hi = panel_y(pe, pe_extras)
    y1_top = pad_t
    y2_top = pad_t + plot_h + gap
    # x labels
    labels = []
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        idx = min(int(frac * (len(dates) - 1)), len(dates) - 1)
        x = pad_l + frac * plot_w
        labels.append(
            f'<text x="{x:.1f}" y="{height - 12}" fill="#7d8b96" font-size="10" font-family="sans-serif" text-anchor="middle">{dates[idx].isoformat()}</text>'
        )
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0b0f14"/>',
        f'<text x="{pad_l}" y="26" fill="#e8eef2" font-size="16" font-family="sans-serif">{svg_escape(title)}</text>',
        axis(y1_top, eps_lo, eps_hi, "Forward EPS (carried)", eps, [], "#6cb6ff", markers=actual_q),
        axis(y2_top, pe_lo, pe_hi, "Forward P/E", pe, [], "#f2a65a", mid=pe_mid, band=pe_band),
        *labels,
        f'<text x="64" y="622" fill="#7d8b96" font-size="10" font-family="sans-serif">Blue: NTM EPS. Gold: reported quarterly EPS. Orange: daily forward P/E. Green band: {lookback}-day 16th–84th percentile, dashed median.</text>',
        "</svg>",
    ]
    return "\n".join(body)


def fmt(v, digits=2, pct=False) -> str:
    if v is None:
        return "n/a"
    if pct:
        return f"{v * 100:.{digits}f}%"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def fmt_pct_rank(v) -> str:
    return "n/a" if v is None else f"{v:.0f}th pct"


def fmt_z(v) -> str:
    if v is None:
        return "n/a"
    return f"{v:+.2f}σ"


def spark(values: list[float | None], width: int = 24) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    nums = [v for v in values if v is not None and math.isfinite(v)]
    if len(nums) < 2:
        return ""
    lo, hi = min(nums), max(nums)
    span = hi - lo or 1.0
    step = max(1, len(values) // width)
    sampled = values[::step][:width]
    chars = []
    for v in sampled:
        if v is None or not math.isfinite(v):
            chars.append(" ")
            continue
        idx = int((v - lo) / span * (len(blocks) - 1))
        chars.append(blocks[idx])
    return "".join(chars)


def screen_one(
    ticker: str,
    out_root: Path,
    lookback: int = DEFAULT_LOOKBACK,
    allow_biased: bool = False,
    light: bool = False,
) -> dict:
    """`light` skips the Nasdaq growth block, which only the single-ticker report prints."""
    windows = tuple(sorted({90, 365, lookback}))
    ysym = yahoo_symbol(ticker)
    nsym = nasdaq_symbol(ticker)
    local = local_history(ticker, allow_biased)
    use_local = bool(local) and any(eps is not None for _, (_, eps) in local["points"])
    if use_local:
        # B closes plus nightly recorded prices cover every day that has EPS, so
        # skip the price download (Yahoo rate-limits a full --all run).
        closes = {d: px for d, (px, _) in local["points"] if px}
        dates = sorted(closes)
        prices = [closes[d] for d in dates]
        latest = local["latest"] or {}
        meta = {"source": "ForwardEstimates", "currency": latest.get("currency"), "longName": latest.get("name")}
    else:
        dates, prices, meta = fetch_prices(ticker, ysym, nsym)
    nasdaq = {"forecast": None, "surprise": None} if light else fetch_nasdaq(nsym)
    q_rows = _forecast_rows(((nasdaq.get("forecast") or {}) or {}).get("quarterlyForecast"))
    y_rows = _forecast_rows(((nasdaq.get("forecast") or {}) or {}).get("yearlyForecast"))
    ntm = ntm_from_quarters(q_rows, dates[-1])
    years = yearly_growth(y_rows)
    surprises = surprise_table(nasdaq.get("surprise"))
    warnings: list[str] = []
    snaps: list = []
    if use_local:
        snaps = [(d, eps, None) for d, (_, eps) in local["points"] if eps is not None]
        fundamentals = {"fwd_pe": [], "q_eps": []}
        eps_source = (
            ("B reconstruction + " if local["b_used"] else "")
            + f"recorded consensus ({local['recorded_days']} days)"
        )
        if local["b_used"]:
            warnings.append(
                f"history before {local['recorded_first']} is reconstruction B "
                f"(validation grade: {local['grade']}); it carries look-ahead, "
                "so past-screen returns flatter the rule"
            )
            if local["grade"] not in {"good", "caution"}:
                warnings.append("B was graded biased for this ticker and forced in with --allow-biased")
        elif local["grade"]:
            warnings.append(
                f"reconstruction B graded {local['grade']}; only recorded consensus is used, "
                "so percentiles need months of recording before they mean anything"
            )
    else:
        fundamentals = fetch_fundamentals(ysym)
        snaps = implied_eps_snapshots(dates, prices, fundamentals.get("fwd_pe") or [])
        eps_source = str(fundamentals.get("source") or "yahoo")
    if not snaps:
        freeze = None if not ntm else ntm["eps"]
        if freeze is None and years:
            freeze = years[0]["eps"]
        if freeze is None or freeze <= 0:
            raise RuntimeError(
                f"no forward EPS for {ticker}: Yahoo PE history unavailable and no Nasdaq consensus"
            )
        # Frozen current NTM must not be carried across a decade of prices.
        keep = 420
        if len(dates) > keep:
            dates = dates[-keep:]
            prices = prices[-keep:]
        snaps = [(dates[0], float(freeze), None)]  # type: ignore[list-item]
        eps_source = "nasdaq_ntm_frozen"
        warnings.append(
            "Yahoo point-in-time forward PE was unavailable. "
            "Forward EPS is today's Nasdaq NTM held constant, so EPS z-scores are n/a "
            "and PE z-scores are cheap-to-self at frozen earnings over the last ~18 months."
        )
    carried_eps = carry_series(dates, snaps)
    pe: list[float | None] = []
    for px, eps in zip(prices, carried_eps):
        if eps is None or eps <= 0:
            pe.append(None)
        else:
            pe.append(px / eps)
    last = dates[-1]
    price = prices[-1]
    eps_now = carried_eps[-1]
    pe_now = pe[-1]
    eps_z = {w: window_stats(dates, carried_eps, last, w) for w in windows}
    pe_z = {w: window_stats(dates, pe, last, w) for w in windows}
    past = walkforward_pe(dates, prices, pe, lookback)
    rev = revision_90d(local["latest"] if local else None)
    signal = classify(pe_z[lookback]["pct"], rev)
    ttm = None
    q_eps = fundamentals.get("q_eps") or surprise_actuals(surprises)
    if len(q_eps) >= 4:
        ttm = sum(v for _, v in q_eps[-4:])
    coverage = {
        "yahoo_symbol": ysym,
        "nasdaq_symbol": nsym,
        "price_source": meta.get("source"),
        "eps_source": eps_source,
        "price_start": dates[0].isoformat(),
        "price_end": last.isoformat(),
        "price_days": len(dates),
        "fwd_pe_snapshots": len(fundamentals.get("fwd_pe") or []),
        "fwd_pe_first": None if not (fundamentals.get("fwd_pe") or []) else fundamentals["fwd_pe"][0][0].isoformat(),
        "fwd_pe_last": None if not (fundamentals.get("fwd_pe") or []) else fundamentals["fwd_pe"][-1][0].isoformat(),
        "days_since_eps_snapshot": (
            0 if eps_source == "nasdaq_ntm_frozen" else None if not snaps else (last - snaps[-1][0]).days
        ),
        "nasdaq_forecast": bool(nasdaq.get("forecast")),
        "warnings": warnings,
    }
    currency = meta.get("currency") or ""
    name = meta.get("longName") or meta.get("shortName") or ticker
    out_dir = out_root / ticker.replace("/", "-")
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = render_svg(
        f"{ticker}  {name}  forward earnings vs cheap-to-self",
        dates,
        carried_eps,
        pe,
        q_eps,
        pe_z[lookback]["median"],
        (pe_z[lookback]["p16"], pe_z[lookback]["p84"]),
        lookback,
    )
    svg_path = out_dir / "forward_screen.svg"
    svg_path.write_text(svg, encoding="utf-8")
    payload = {
        "ticker": ticker,
        "name": name,
        "currency": currency,
        "as_of": last.isoformat(),
        "price": price,
        "forward_eps": {
            "current": eps_now,
            "spark": spark(carried_eps),
            "windows": eps_z,
            "source": eps_source,
        },
        "forward_pe": {
            "current": pe_now,
            "spark": spark(pe),
            "windows": pe_z,
            "source": "daily close / carried forward EPS",
        },
        "growth": {
            "nasdaq_ntm": None if not ntm else ntm["eps"],
            "nasdaq_ntm_quarters": None if not ntm else ntm["quarters"],
            "ttm_eps": ttm,
            "ntm_vs_ttm": None if not ntm or not ttm or ttm == 0 else ntm["eps"] / ttm - 1.0,
            "fiscal_years": years,
            "surprises": surprises,
        },
        "signal": {
            "label": signal,
            "lookback_days": lookback,
            "pe_pct": pe_z[lookback]["pct"],
            "pe_median": pe_z[lookback]["median"],
            "pe_p16": pe_z[lookback]["p16"],
            "pe_p84": pe_z[lookback]["p84"],
            "fy1_revision_90d": rev,
            "b_grade": None if not local else local["grade"],
        },
        "windows": list(windows),
        "past_screen": past,
        "coverage": coverage,
        "plot": str(svg_path),
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    series = {
        "dates": [d.isoformat() for d in dates],
        "price": [round(v, 4) for v in prices],
        "eps": [None if v is None else round(v, 6) for v in carried_eps],
        "pe": [None if v is None else round(v, 4) for v in pe],
    }
    (out_dir / "series.json").write_text(json.dumps(series), encoding="utf-8")
    return payload


def print_report(row: dict) -> None:
    g = row["growth"]
    years = g["fiscal_years"]
    print(f"{row['ticker']}  {row['name']}")
    print(f"as-of {row['as_of']}  price {fmt(row['price'])} {row['currency']}")
    sig = row["signal"]
    print(
        f"SIGNAL  {sig['label']}  (P/E at {fmt_pct_rank(sig['pe_pct'])} of its {sig['lookback_days']}d range, "
        f"next-FY EPS {fmt(sig['fy1_revision_90d'], pct=True)} over 90d)"
    )
    print()
    print("Forward EPS  (revision extremity, not cheapness)")
    print(f"  now {fmt(row['forward_eps']['current'])}  {row['forward_eps']['spark']}")
    for w in row["windows"]:
        s = row["forward_eps"]["windows"][w]
        print(
            f"  {w:>3}d  mean {fmt(s['mean'])}  stdev {fmt(s['stdev'])}  "
            f"z {fmt_z(s['z'])}  n={s['n']}"
        )
    print()
    print(f"Forward P/E  (cheap-to-self: ≤{CHEAP_PCT}th percentile of own history is cheap)")
    print(f"  now {fmt(row['forward_pe']['current'])}x  {row['forward_pe']['spark']}")
    for w in row["windows"]:
        s = row["forward_pe"]["windows"][w]
        print(
            f"  {w:>3}d  median {fmt(s['median'])}  16–84th {fmt(s['p16'])}–{fmt(s['p84'])}  "
            f"now {fmt_pct_rank(s['pct'])}  n={s['n']}"
        )
    print()
    print("Growth")
    if years:
        bits = []
        for year in years:
            label = year["fiscal_end"]
            chunk = f"{label} {fmt(year['eps'])}"
            if year["growth_vs_prev"] is not None:
                chunk += f" ({fmt(year['growth_vs_prev'], pct=True)} vs prior)"
            revs = f"{year['rev_up_4w']} up / {year['rev_down_4w']} down 4w"
            bits.append(f"  {chunk}  {revs}")
        print("\n".join(bits))
    else:
        print("  no Nasdaq yearly consensus")
    print(f"  Nasdaq NTM {fmt(g['nasdaq_ntm'])}  TTM {fmt(g['ttm_eps'])}  NTM/TTM {fmt(g['ntm_vs_ttm'], pct=True)}")
    if g["surprises"]:
        print("  recent surprises:")
        for item in g["surprises"][:4]:
            print(
                f"    {item['fiscal_end']}  actual {item['eps']}  "
                f"est {item['consensus']}  surprise {item['surprise_pct']}%"
            )
    print()
    past = row["past_screen"]
    print(f"Past screen  (walk-forward {past['lookback_days']}d P/E percentile; avg return after the signal)")
    print(f"  cheap (≤{CHEAP_PCT}th) {past['cheap_days']} days, expensive (≥{RICH_PCT}th) {past['expensive_days']} days, of {past['scored_days']} scored")
    for h, stats in past["horizons"].items():
        print(
            f"  +{h:>3} trading days  all days {fmt(stats['all_avg'], pct=True)}  "
            f"cheap {fmt(stats['cheap_avg'], pct=True)} (n={stats['cheap_n']})  "
            f"expensive {fmt(stats['expensive_avg'], pct=True)} (n={stats['expensive_n']})"
        )
    print()
    cov = row["coverage"]
    print("Coverage")
    print(
        f"  prices {cov['price_start']} → {cov['price_end']}  "
        f"({cov['price_days']} days, {cov.get('price_source') or 'unknown'})"
    )
    if str(cov.get("eps_source")).startswith("yahoo"):
        print(
            f"  Yahoo forward PE snapshots {cov['fwd_pe_snapshots']}  "
            f"{cov['fwd_pe_first']} → {cov['fwd_pe_last']}  "
            f"age {cov['days_since_eps_snapshot']}d"
        )
    print(f"  EPS source {cov.get('eps_source')}")
    if cov["fwd_pe_snapshots"] < 6 and str(cov.get("eps_source")).startswith("yahoo"):
        print("  warning: snapshot count is thin; z-scores are weakly identified")
    if (
        str(cov.get("eps_source")).startswith("yahoo")
        and cov["days_since_eps_snapshot"] is not None
        and cov["days_since_eps_snapshot"] > 90
    ):
        print("  warning: implied EPS is stale relative to the 90-day window")
    if not cov["nasdaq_forecast"]:
        print("  warning: no Nasdaq consensus (typical for non-US listings)")
    for note in cov.get("warnings") or []:
        print(f"  warning: {note}")
    print(f"  plot {row['plot']}")
    print()


def print_ranking(rows: list[dict], lookback: int) -> None:
    order = sorted(rows, key=lambda r: (r["signal"]["pe_pct"] is None, r["signal"]["pe_pct"] or 0))
    print(f"Ranking by forward P/E percentile within own {lookback}-day history (most cheap first)")
    print(f"{'ticker':<11}{'P/E':>8}{'pct':>9}{'FY1 rev90':>11}  {'B grade':<9}signal")
    for r in order:
        sig = r["signal"]
        print(
            f"{r['ticker']:<11}{fmt(r['forward_pe']['current'], 1):>8}{fmt_pct_rank(sig['pe_pct']):>9}"
            f"{fmt(sig['fy1_revision_90d'], 1, pct=True):>11}  {sig['b_grade'] or '-':<9}{sig['label']}"
        )


def write_ranking(rows: list[dict], out_root: Path) -> Path:
    path = out_root / f"ranking-{date.today().isoformat()}.csv"
    cols = ["ticker", "name", "price", "currency", "pe", "pe_pct", "fy1_revision_90d",
            "signal", "b_grade", "eps_source"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({
                "ticker": r["ticker"], "name": r["name"], "price": r["price"], "currency": r["currency"],
                "pe": r["forward_pe"]["current"], "pe_pct": r["signal"]["pe_pct"],
                "fy1_revision_90d": r["signal"]["fy1_revision_90d"], "signal": r["signal"]["label"],
                "b_grade": r["signal"]["b_grade"], "eps_source": r["coverage"]["eps_source"],
            })
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cheap-to-self forward earnings screen")
    parser.add_argument("tickers", nargs="*", help="Yahoo tickers, e.g. AVGO MU 000660.KS")
    parser.add_argument(
        "--all", action="store_true",
        help=f"screen every ticker in {ESTIMATES_DIR / 'tickers.csv'} and print a ranking",
    )
    parser.add_argument(
        "--lookback", type=int, default=DEFAULT_LOOKBACK,
        help=f"calendar days of own history the signal compares against (default {DEFAULT_LOOKBACK})",
    )
    parser.add_argument(
        "--allow-biased", action="store_true",
        help="also use reconstruction B where validation graded it biased",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help=f"directory for SVG and JSON (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)
    tickers = list(args.tickers)
    if args.all:
        tickers += [r["ticker"] for r in _read_rows(ESTIMATES_DIR / "tickers.csv")]
    if not tickers:
        parser.error("name tickers or pass --all")
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    failed = 0
    rows = []
    for raw in dict.fromkeys(tickers):
        ticker = raw.strip().upper()
        try:
            row = screen_one(ticker, out_root, args.lookback, args.allow_biased, light=args.all)
        except Exception as exc:  # noqa: BLE001 — per-ticker isolation
            failed += 1
            print(f"{ticker}  ERROR  {exc}", file=sys.stderr)
            if not args.all:
                print(f"{ticker} failed: {exc}")
                print()
            continue
        rows.append(row)
        if not args.all:
            print_report(row)
    if args.all:
        print_ranking(rows, args.lookback)
        print(f"\nranking CSV {write_ranking(rows, out_root)}  ({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
