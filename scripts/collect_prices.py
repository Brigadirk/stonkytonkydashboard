#!/usr/bin/env python3
"""Retain Yahoo daily Close (split adjusted, never dividend adjusted).

The original JSON and content hashes are retained under data/market. This is a
public, undocumented Yahoo chart endpoint, not a contracted market-data feed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from datetime import date, datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
MARKET = ROOT / "data" / "market"
UTC = timezone.utc
SYMBOLS = {
    "broadcom": ("AVGO", "USD"),
    "alphabet": ("GOOGL", "USD"),
    "nvidia": ("NVDA", "USD"),
    "sk_hynix": ("000660.KS", "KRW"),
    "samsung_electronics": ("005930.KS", "KRW"),
    "micron": ("MU", "USD"),
    "sandisk": ("SNDK", "USD"),
    "asml": ("ASML.AS", "EUR"),
    "apple": ("AAPL", "USD"),
    "besi": ("BESI.AS", "EUR"),
    "amd": ("AMD", "USD"),
    "cerebras": ("CBRS", "USD"),
    "marvell": ("MRVL", "USD"),
    "tsmc": ("TSM", "USD"),
    "arista": ("ANET", "USD"),
    "vertiv": ("VRT", "USD"),
    "nebius": ("NBIS", "USD"),
    "oracle": ("ORCL", "USD"),
    "microsoft": ("MSFT", "USD"),
    "amazon": ("AMZN", "USD"),
    "meta": ("META", "USD"),
    "spacex": ("SPCX", "USD"),
    "palantir": ("PLTR", "USD"),
}
# Identity boundaries: do not join earlier issuers or pre-listing observations.
# Sources are recorded in docs/research/EXPANSION_20260914.md.
FIRST_ALLOWED = {
    "sandisk": date(2025, 2, 24),
    "nebius": date(2024, 10, 21),
    "cerebras": date(2026, 5, 14),
    "spacex": date(2026, 6, 12),
    "palantir": date(2020, 9, 30),
}
KNOWN_SPLITS = [
    ("apple", "2020-08-31", 4,
     "https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/"),
    ("nvidia", "2021-07-20", 4,
     "https://investor.nvidia.com/files/doc_downloads/doc_faq/06/21/NVIDIA-2021-Stock-Split-FAQ.pdf"),
    ("alphabet", "2022-07-18", 20,
     "https://www.sec.gov/Archives/edgar/data/1652044/000119312522167375/d294315d8k.htm"),
    ("nvidia", "2024-06-10", 10,
     "https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf"),
    ("broadcom", "2024-07-15", 10,
     "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2024-financial"),
]
PRICE_FIELDS = ["company_id", "date", "close", "currency", "adjustment_basis",
                "source_url", "source_sha256"]


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def retain(body: bytes, suffix: str) -> tuple[str, str]:
    digest = hashlib.sha256(body).hexdigest()
    path = MARKET / "raw" / f"{digest}.{suffix}"
    if not path.exists():
        path.write_bytes(body)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Retained file has changed: {path}")
    return digest, str(path.relative_to(ROOT))


def download(session: requests.Session, url: str, kind: str) -> tuple[bytes | None, dict]:
    record = {"source_url": url, "kind": kind,
              "downloaded_at": datetime.now(UTC).isoformat()}
    try:
        response = session.get(url, timeout=25)
        suffix = "json" if "json" in response.headers.get("Content-Type", "") else "html"
        if response.content.startswith(b"%PDF"):
            suffix = "pdf"
        digest, path = retain(response.content, suffix)
        record.update(status=response.status_code, source_sha256=digest,
                      source_file=path, content_type=response.headers.get("Content-Type", ""),
                      final_url=response.url)
        if not response.ok:
            record["error"] = f"HTTP {response.status_code}"
            return None, record
        return response.content, record
    except requests.RequestException as error:
        record["error"] = f"{type(error).__name__}: {error}"
        return None, record


def session_completed(trading_day: date, meta: dict, downloaded_at: datetime) -> bool:
    """Do not use a live bar as a daily close; allow 20 minutes for publication."""
    zone = ZoneInfo(meta["exchangeTimezoneName"])
    local_today = downloaded_at.astimezone(zone).date()
    if trading_day < local_today:
        return True
    if trading_day > local_today:
        return False
    regular = meta.get("currentTradingPeriod", {}).get("regular", {})
    if not regular.get("end") or not regular.get("start"):
        return False
    start_day = datetime.fromtimestamp(regular["start"], zone).date()
    return start_day == trading_day and downloaded_at.timestamp() >= regular["end"] + 1200


def parse_chart(company: str, payload: dict, record: dict, start: date, cutoff: date,
                basis_verified: bool) -> tuple[list[dict], list[dict], dict]:
    chart = payload.get("chart", {})
    if chart.get("error") or not chart.get("result"):
        raise ValueError(f"Yahoo chart error: {chart.get('error')}")
    result = chart["result"][0]
    meta = result["meta"]
    symbol, currency = SYMBOLS[company]
    if meta["symbol"] != symbol or meta["currency"] != currency:
        raise ValueError(f"Unexpected listing or currency for {company}")
    zone = ZoneInfo(meta["exchangeTimezoneName"])
    downloaded_at = datetime.fromisoformat(record["downloaded_at"])
    first_allowed = max(start, FIRST_ALLOWED.get(company, start))
    splits = []
    later_split_factor = 1.0
    for event in result.get("events", {}).get("splits", {}).values():
        effective = datetime.fromtimestamp(event["date"], zone).date()
        ratio = float(event["numerator"]) / float(event["denominator"])
        if ratio <= 0 or not math.isfinite(ratio):
            raise ValueError("Invalid split ratio")
        if effective > cutoff:
            # Yahoo adjusts old closes for all splits known at retrieval. For a
            # past cutoff, undo subsequent splits to preserve cutoff share units.
            later_split_factor *= ratio
        elif effective >= first_allowed:
            source = next((item[3] for item in KNOWN_SPLITS
                           if item[:3] == (company, effective.isoformat(), ratio)), record["source_url"])
            splits.append({"company_id": company, "effective_date": effective.isoformat(),
                           "ratio": ratio, "source_url": source})
    expected = {(day, float(ratio)) for name, day, ratio, _ in KNOWN_SPLITS
                if name == company and first_allowed <= date.fromisoformat(day) <= cutoff}
    found = {(row["effective_date"], row["ratio"]) for row in splits}
    if not expected.issubset(found):
        raise ValueError(f"Known split missing or conflicting: {expected - found}")
    timestamps = result.get("timestamp", [])
    closes = result["indicators"]["quote"][0].get("close", [])
    if len(timestamps) != len(closes):
        raise ValueError("Timestamp and close arrays differ in length")
    rows, missing, incomplete = [], [], []
    for timestamp, value in zip(timestamps, closes):
        trading_day = datetime.fromtimestamp(timestamp, zone).date()
        if not first_allowed <= trading_day <= cutoff:
            continue
        if not session_completed(trading_day, meta, downloaded_at):
            incomplete.append(trading_day.isoformat())
            continue
        if value is None or not math.isfinite(float(value)) or value <= 0:
            missing.append(trading_day.isoformat())
            continue
        rows.append({"company_id": company, "date": trading_day.isoformat(),
                     "close": float(value) * (later_split_factor if basis_verified else 1.0),
                     "currency": currency,
                     "adjustment_basis": "split_adjusted_to_cutoff" if basis_verified else "raw",
                     "source_url": record["source_url"], "source_sha256": record["source_sha256"]})
    if len({row["date"] for row in rows}) != len(rows):
        raise ValueError(f"Duplicate daily price in {company}")
    if not rows:
        raise ValueError("No completed daily closes returned")
    rows.sort(key=lambda row: row["date"])
    coverage = {"company_id": company, "symbol": symbol, "currency": currency,
                "rows": len(rows), "first_date": rows[0]["date"], "last_date": rows[-1]["date"],
                "missing_provider_bars": missing, "excluded_incomplete_sessions": incomplete,
                "adjustment_basis": rows[0]["adjustment_basis"],
                "post_cutoff_split_factor_undone": later_split_factor,
                "exchange_timezone": meta["exchangeTimezoneName"],
                "source_sha256": record["source_sha256"],
                "regular_market_quote_not_used": meta.get("regularMarketPrice"),
                "status": "available"}
    return rows, splits, coverage


def main() -> None:
    global MARKET
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2020-09-10")
    parser.add_argument("--cutoff", default="2026-09-10")
    parser.add_argument("--offline", action="store_true", help="Rebuild retained collection without network")
    parser.add_argument("--output-directory", type=Path,
                        help="Stage a collection under the app directory before importing it")
    parser.add_argument("--companies", nargs="+", choices=sorted(SYMBOLS), help="Collect selected companies, preserving the others at the same cutoff")
    args = parser.parse_args()
    if args.output_directory:
        MARKET = (ROOT / args.output_directory).resolve()
        MARKET.relative_to(ROOT)
    start, cutoff = date.fromisoformat(args.start), date.fromisoformat(args.cutoff)
    if start > cutoff or cutoff > datetime.now(UTC).date():
        parser.error("Require start <= cutoff <= today's UTC date")
    (MARKET / "raw").mkdir(parents=True, exist_ok=True)
    manifest_path = MARKET / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    previous_summary_path = MARKET / "summary.json"
    previous_summary = json.loads(previous_summary_path.read_text()) if previous_summary_path.exists() else {}
    selected = set(args.companies or SYMBOLS)
    if args.companies and previous_summary and (previous_summary["cutoff"] != args.cutoff or previous_summary["requested_start"] != args.start):
        parser.error("A partial collection must keep the existing start and cutoff dates")
    records = []
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (AI valuation dashboard personal research)"

    def get(url: str, kind: str) -> tuple[bytes | None, dict]:
        if args.offline:
            candidates = [r for r in previous if r["source_url"] == url and r.get("status") == 200]
            if not candidates:
                raise ValueError(f"No retained successful source: {url}")
            record = candidates[-1]
            body = (ROOT / record["source_file"]).read_bytes()
            if hashlib.sha256(body).hexdigest() != record["source_sha256"]:
                raise ValueError("Source hash mismatch")
            records.append(record)
            return body, record
        body, record = download(session, url, kind)
        records.append(record)
        return body, record

    # Yahoo labels Close as split adjusted and Adj Close as split + distributions.
    basis_verified = False
    for definition_url in ["https://ca.finance.yahoo.com/quote/NVDA/history/",
                           "https://finance.yahoo.com/quote/PLTR/history/",
                           "https://uk.finance.yahoo.com/quote/NVDA/history/"]:
        try:
            definition, definition_record = get(definition_url, "adjustment_definition")
        except ValueError:
            if not args.offline:
                raise
            continue
        basis_verified = bool(definition and
                              (b"Close price adjusted for splits" in definition or
                               b"Closing price adjusted for splits" in definition) and
                              b"dividend and/or capital gain distributions" in definition)
        if basis_verified:
            break
    prices, all_splits, coverage = [], [], []
    if args.companies:
        for filename, target in [("prices.csv", prices), ("splits.csv", all_splits)]:
            path = MARKET / filename
            if path.exists():
                with path.open() as handle:
                    target.extend(row for row in csv.DictReader(handle) if row["company_id"] not in selected)
        coverage.extend(row for row in previous_summary.get("coverage", []) if row["company_id"] not in selected)
    # Retrieve events through collection date for correct old-cutoff share basis.
    retrieval_end = datetime.now(UTC).date() + timedelta(days=1)
    if args.offline:
        chart_records = [r for r in previous if r.get("kind") == "daily_chart"]
        retrieval_end = date.fromisoformat(chart_records[-1]["retrieval_end"])
    params = {"period1": int(datetime.combine(start, clock_time(), UTC).timestamp()),
              "period2": int(datetime.combine(retrieval_end, clock_time(), UTC).timestamp()),
              "interval": "1d", "events": "div,splits", "includeAdjustedClose": "true"}
    for company, (symbol, _) in SYMBOLS.items():
        if company not in selected:
            continue
        errors = []
        hosts = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
        for host in hosts:
            url = requests.Request("GET", f"https://{host}/v8/finance/chart/{symbol}", params=params).prepare().url
            try:
                body, record = get(url, "daily_chart")
                record["retrieval_end"] = retrieval_end.isoformat()
                if body is None:
                    errors.append(record.get("error", "Failed download"))
                    continue
                rows, splits, result = parse_chart(company, json.loads(body), record, start, cutoff, basis_verified)
                prices.extend(rows)
                all_splits.extend(splits)
                coverage.append(result)
                print(f"{symbol}: {len(rows)} closes {rows[0]['date']} to {rows[-1]['date']}", flush=True)
                break
            except (ValueError, KeyError, TypeError) as error:
                errors.append(str(error))
        else:
            coverage.append({"company_id": company, "symbol": symbol, "rows": 0,
                             "status": "unavailable", "errors": errors})
        if not args.offline:
            time.sleep(0.25)
    if not args.offline:
        for url in dict.fromkeys([row[3] for row in KNOWN_SPLITS if row[0] in selected] + [
            "https://help.yahoo.com/kb/SLN28256.html",
            "https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation",
        ]):
            get(url, "corporate_action_or_methodology")
    prices.sort(key=lambda row: (row["company_id"], row["date"]))
    write_csv(MARKET / "prices.csv", PRICE_FIELDS, prices)
    write_csv(MARKET / "splits.csv", ["company_id", "effective_date", "ratio", "source_url"], all_splits)
    summary = {"generated_at": datetime.now(UTC).isoformat(), "requested_start": start.isoformat(),
               "cutoff": cutoff.isoformat(), "total_prices": len(prices), "split_events": len(all_splits),
               "price_field": "indicators.quote[0].close", "dividend_adjusted": False,
               "adjustment_definition_verified": basis_verified, "adjustment_definition_url": definition_url,
               "coverage": coverage, "subscription_needed_for_prices": any(c["status"] != "available" for c in coverage),
               "completeness_note": "Provider bars only; missing bars are not filled. No independent exchange-calendar completeness audit.",
               "replay_note": "Current revisions of historical prices; raw retrievals retained. These are not original daily snapshots."}
    (MARKET / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not args.offline:
        manifest_path.write_text(json.dumps(previous + records, indent=2) + "\n")
    print(json.dumps({"total_prices": len(prices), "split_events": len(all_splits),
                      "basis_verified": basis_verified}))


if __name__ == "__main__":
    main()
