#!/usr/bin/env python3
"""Fetch new broker reports automatically, then extract them (extract.process).

Two sources, both allowed by the sites' robots.txt:

  firstrade   Morningstar equity reports Firstrade hosts at
              /ms/equity_reports/sr/<year>/<morningstar id>_<yyyymmdd>_RT.pdf.
              There is no index, so each night probes the days since the last
              check. A ticker's first run searches back up to BACKFILL_DAYS for
              its latest report only.
  telegram    Public broker Telegram channels (telegram_channels.csv), searched
              for each Korean ticker's six-digit code; linked PDFs are kept.
              Naver Finance and the Hana, Hyundai and Mirae sites disallow
              crawlers, so they are left to the inbox.

    ./collect.py                 both sources
    ./collect.py firstrade AVGO  one source, optionally some tickers

State lives in state/*.json so a night only looks at what's new.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import extract

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
DOWNLOADS = ROOT / "downloads"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
FIRSTRADE = "https://invest.firstrade.com/ms/equity_reports/sr/{year}/{msid}_{ymd}_RT.pdf"
BACKFILL_DAYS = 120
MAX_FORWARD_DAYS = 14
TELEGRAM_FIRST_RUN_DAYS = 90
PAUSE = 0.4


def load_state(name: str) -> dict:
    path = STATE / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(name: str, state: dict) -> None:
    STATE.mkdir(exist_ok=True)
    (STATE / f"{name}.json").write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")


def head_ok(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200 and "pdf" in (r.headers.get("Content-Type") or "")
    except Exception:  # noqa: BLE001 — 404 is the normal "no report that day"
        return False


def download(url: str, name: str) -> Path:
    DOWNLOADS.mkdir(exist_ok=True)
    path = DOWNLOADS / name
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
        path.write_bytes(r.read())
    return path


def run_extract(path: Path, url: str, origin: str, hint: str = "") -> None:
    try:
        print("   ", extract.process(path, source_url=url, origin=origin, hint=hint), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"    {path.name}: extraction FAILED {exc}", flush=True)
    finally:
        path.unlink(missing_ok=True)  # the PDF itself is archived by sha in pdfs/


def firstrade(only: set[str]) -> None:
    ids_path = ROOT / "morningstar_ids.csv"
    if not ids_path.exists():
        print("firstrade: run morningstar_ids.py first")
        return
    with open(ids_path, newline="", encoding="utf-8") as fh:
        ids = {r["ticker"]: r["morningstar_id"] for r in csv.DictReader(fh) if r["morningstar_id"]}
    state = load_state("firstrade")
    today = date.today()
    for ticker, msid in sorted(ids.items()):
        if only and ticker not in only:
            continue
        seen = state.get(ticker, {})
        found = []
        if "checked_through" in seen:
            start = date.fromisoformat(seen["checked_through"]) + timedelta(days=1)
            days = [start + timedelta(days=k) for k in range((today - start).days + 1)][-MAX_FORWARD_DAYS:]
        else:
            days = [today - timedelta(days=k) for k in range(BACKFILL_DAYS)]  # newest first
        for d in days:
            if d.weekday() >= 5 and "checked_through" not in seen:
                continue  # backfill skips weekends; nightly checks every day
            url = FIRSTRADE.format(year=d.year, msid=msid, ymd=d.strftime("%Y%m%d"))
            if head_ok(url):
                found.append((d, url))
                if "checked_through" not in seen:
                    break  # backfill wants the latest report only
            time.sleep(PAUSE)
        for d, url in found:
            print(f"firstrade {ticker} {d}", flush=True)
            run_extract(download(url, f"{ticker}_{d:%Y%m%d}_ms.pdf"), url, "firstrade", ticker)
        state[ticker] = {"checked_through": today.isoformat(),
                         "last_report": found[-1][0].isoformat() if found else seen.get("last_report", "")}
        save_state("firstrade", state)


def telegram_posts(channel: str, query: str) -> list[dict]:
    url = f"https://t.me/s/{channel}?q={urllib.parse.quote(query)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    posts = []
    for block in page.split('<div class="tgme_widget_message_wrap')[1:]:
        post = re.search(r'data-post="([^"]+)"', block)
        when = re.search(r'datetime="([^"]+)"', block)
        body = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        if not (post and when and body):
            continue
        links = [html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', body.group(1)) if "t.me/" not in u]
        posts.append({"id": post.group(1), "date": when.group(1)[:10], "links": links,
                      "text": html.unescape(re.sub(r"<[^>]+>", " ", body.group(1)))[:200]})
    return posts


def resolve_pdf(url: str) -> str | None:
    """Follow a (shortened) link; return the final URL if it serves a PDF."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.geturl() if "pdf" in (r.headers.get("Content-Type") or "") else None
    except Exception:  # noqa: BLE001
        return None


def telegram(only: set[str]) -> None:
    channels_path = ROOT / "telegram_channels.csv"
    with open(channels_path, newline="", encoding="utf-8") as fh:
        channels = [r for r in csv.DictReader(fh) if r["channel"].strip()]
    with open(ROOT.parent / "tickers.csv", newline="", encoding="utf-8") as fh:
        korean = [r["ticker"] for r in csv.DictReader(fh) if r["ticker"].endswith((".KS", ".KQ"))
                  and not (r.get("estimates_from") or "").strip()]
    state = load_state("telegram")
    cutoff = (date.today() - timedelta(days=TELEGRAM_FIRST_RUN_DAYS)).isoformat()
    for ch in channels:
        seen = set(state.get(ch["channel"], []))
        for ticker in korean:
            if only and ticker not in only:
                continue
            try:
                posts = telegram_posts(ch["channel"], ticker.split(".")[0])
            except Exception as exc:  # noqa: BLE001
                print(f"telegram {ch['channel']} {ticker}: {exc}")
                continue
            code = ticker.split(".")[0]
            for p in posts:
                if p["id"] in seen or p["date"] < cutoff:
                    continue
                seen.add(p["id"])
                # Company reports open with "Company (code)"; daily notes mention codes further down.
                if not re.search(rf"\(\s*{code}\s*\)", p["text"][:120]):
                    continue
                for link in p["links"]:
                    pdf_url = resolve_pdf(link)
                    if not pdf_url:
                        continue
                    print(f"telegram {ch['channel']} {ticker} {p['date']} {p['text'][:60]!r}", flush=True)
                    run_extract(download(pdf_url, f"{ticker}_{p['id'].replace('/', '_')}.pdf"), pdf_url, "telegram", ticker)
                    time.sleep(PAUSE)
            time.sleep(PAUSE)
        state[ch["channel"]] = sorted(seen)
        save_state("telegram", state)


def main(argv: list[str]) -> int:
    sources = {"firstrade": firstrade, "telegram": telegram}
    picked = [a for a in argv if a in sources] or list(sources)
    only = {a for a in argv if a not in sources}
    print(f"collect {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC: {', '.join(picked)}", flush=True)
    for name in picked:
        sources[name](only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
