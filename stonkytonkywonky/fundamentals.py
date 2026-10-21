#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance"]
# ///
"""Balance sheet and cash flow for the value ratios: EV/FCF and price-to-book.

Yahoo's own enterpriseValue and priceToBook mix currencies for ADRs and foreign
listings (TSM: a dollar price over Taiwan-dollar book gives a P/B of 80), so this
stores the statement figures in the reporting currency with the rate to the quote
currency, and export_app.py does the division at the current price.

    data/fundamentals.csv   one row per ticker, refreshed when older than a week

Free cash flow is operating cash flow minus capex over the last four reported quarters,
or the last fiscal year where quarters are missing (Hong Kong and China report half-yearly).
Cash includes short-term investments; debt includes leases, as Yahoo reports Total Debt.

    ./fundamentals.py            refresh stale tickers
    ./fundamentals.py MU TSM     refresh these now
"""

from __future__ import annotations

import csv
import math
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "fundamentals.csv"
FIELDS = ["ticker", "fetched", "quote_ccy", "fin_ccy", "fx", "shares", "fcf", "fcf_basis", "fcf_end",
          "debt", "cash", "equity", "bs_end", "error"]
STALE_DAYS = 7


def num(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def row_of(frame, *names):
    """First matching statement line as {period_end: value}, newest first."""
    for n in names:
        if frame is not None and not frame.empty and n in frame.index:
            return {c.date(): num(v) for c, v in frame.loc[n].items()}
    return {}


def ttm_fcf(tk) -> tuple[float | None, str, date | None]:
    q = tk.quarterly_cashflow
    ocf, capex = row_of(q, "Operating Cash Flow"), row_of(q, "Capital Expenditure")
    ends = sorted((d for d in ocf if ocf[d] is not None and capex.get(d) is not None), reverse=True)[:4]
    # Four consecutive quarters: newest and oldest no more than ~10 months apart.
    if len(ends) == 4 and (ends[0] - ends[3]).days <= 300:
        return sum(ocf[d] + capex[d] for d in ends), "4 quarters", ends[0]
    a = tk.cashflow
    ocf, capex = row_of(a, "Operating Cash Flow"), row_of(a, "Capital Expenditure")
    ends = sorted((d for d in ocf if ocf[d] is not None and capex.get(d) is not None), reverse=True)
    if ends:
        return ocf[ends[0]] + capex[ends[0]], "fiscal year", ends[0]
    return None, "", None


def balance(tk) -> tuple[float | None, float | None, float | None, date | None]:
    for frame in (tk.quarterly_balance_sheet, tk.balance_sheet):
        equity = row_of(frame, "Common Stock Equity", "Stockholders Equity")
        ends = sorted((d for d, v in equity.items() if v is not None), reverse=True)
        if ends:
            d = ends[0]
            debt = row_of(frame, "Total Debt").get(d) or 0.0
            cash = (row_of(frame, "Cash Cash Equivalents And Short Term Investments").get(d)
                    or row_of(frame, "Cash And Cash Equivalents").get(d) or 0.0)
            return debt, cash, equity[d], d
    return None, None, None, None


def fx_rate(src: str, dst: str, cache: dict) -> float | None:
    if not src or not dst or src == dst:
        return 1.0
    key = f"{src}{dst}=X"
    if key not in cache:
        hist = yf.Ticker(key).history(period="5d")
        cache[key] = num(hist["Close"].iloc[-1]) if not hist.empty else None
    return cache[key]


def fetch(ticker: str, fx_cache: dict) -> dict:
    tk = yf.Ticker(ticker)
    info = tk.info
    quote, fin = info.get("currency"), info.get("financialCurrency") or info.get("currency")
    price = num(info.get("regularMarketPrice") or info.get("currentPrice"))
    mcap = num(info.get("marketCap"))
    fcf, basis, fcf_end = ttm_fcf(tk)
    debt, cash, equity, bs_end = balance(tk)
    return {
        "ticker": ticker, "fetched": date.today().isoformat(), "quote_ccy": quote, "fin_ccy": fin,
        "fx": fx_rate(fin, quote, fx_cache),
        # Company-wide share count implied by Yahoo's market cap, so share classes
        # (GOOGL) and ADRs (TSM) are valued as the whole company at the current price.
        "shares": mcap / price if mcap and price else None,
        "fcf": fcf, "fcf_basis": basis, "fcf_end": fcf_end, "debt": debt, "cash": cash,
        "equity": equity, "bs_end": bs_end, "error": None,
    }


def main(argv: list[str]) -> int:
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        tickers = [r["ticker"] for r in csv.DictReader(fh)]
    known: dict[str, dict] = {}
    if OUT.exists():
        with open(OUT, newline="", encoding="utf-8") as fh:
            known = {r["ticker"]: r for r in csv.DictReader(fh)}
    cutoff = (date.today() - timedelta(days=STALE_DAYS)).isoformat()
    todo = argv or [t for t in tickers if (known.get(t) or {}).get("fetched", "") < cutoff]
    fx_cache: dict = {}
    for i, t in enumerate(todo, 1):
        try:
            known[t] = fetch(t, fx_cache)
        except Exception as e:  # noqa: BLE001 — keep last week's figures, note the failure
            known[t] = {**known.get(t, {"ticker": t}), "error": f"{type(e).__name__}: {e}"[:200]}
        r = known[t]
        print(f"{i}/{len(todo)} {t}: fcf {r.get('fcf')} ({r.get('fcf_basis')}) equity {r.get('equity')} {r.get('fin_ccy')}→{r.get('quote_ccy')} {r.get('error') or ''}", flush=True)
        time.sleep(0.5)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(known[t] for t in sorted(known))
    tmp.replace(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
