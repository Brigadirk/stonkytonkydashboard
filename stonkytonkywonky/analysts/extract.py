#!/usr/bin/env python3
"""Extract analyst EPS forecasts from broker PDFs dropped into analysts/inbox/.

For each new PDF: archive it under pdfs/<sha256>.pdf, pull the text of its
first pages with pdftotext, and ask Claude (headless CLI) for the report's
company, analysts, firm, date, currency and annual EPS forecasts as JSON.
Every EPS number must then appear in the report text; if one doesn't, the
report's rows are kept but marked needs_review instead of verified.

    ./extract.py            process everything in inbox/
    ./extract.py FILE.pdf   process one file (also used by the collectors)

Processed files leave the inbox; a failed one moves to failed/ with a
.error.txt next to it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from parsers import parse
from store import load, obs_id, upsert

ROOT = Path(__file__).resolve().parent
INBOX = ROOT / "inbox"
PDFS = ROOT / "pdfs"
TEXT = ROOT / "text"
PAGES = 8
MODEL = "sonnet"
# The model is a fallback for layouts the parsers don't know; cap its use per run.
MAX_MODEL_CALLS = 5
model_calls = 0
TICKERS_CSV = ROOT.parent / "tickers.csv"

PROMPT = """You extract sell-side analyst forecasts from one broker research report (text on stdin).

Return ONLY a JSON object, no prose:
{
  "is_company_report": true/false,       // false for sector notes, strategy pieces, anything without a company EPS forecast table
  "ticker": "...",                       // pick from the ticker list below, or "" if the company isn't in it
  "company": "...",
  "firm": "...",                         // the broker or research house
  "analysts": ["..."],                   // named authors, romanised as printed
  "report_date": "YYYY-MM-DD",           // the report's printed publication date
  "currency": "USD/KRW/EUR/...",         // currency of the EPS figures
  "eps_basis": "...",                    // e.g. "adjusted diluted", "GAAP diluted", "K-IFRS consolidated", as the report states
  "estimates": [                         // ANNUAL EPS forecasts only (estimate columns, usually marked E/F), not actual/historical years
    {"fiscal_year": 2026, "fiscal_year_end": "YYYY-MM-DD or \\"\\"", "eps": 12.34, "eps_as_printed": "12.34", "page": 1}
  ]
}

Rules: copy eps_as_printed exactly as it appears in the text (same digits, commas, decimals).
If a figure is in a different unit (e.g. won vs thousands), convert eps to per-share in the stated currency but keep eps_as_printed verbatim.
Never invent a number. Omit a year rather than guess.

Ticker list (ticker,name):
"""


def ticker_list() -> str:
    with open(TICKERS_CSV, newline="", encoding="utf-8") as fh:
        return "\n".join(f"{r['ticker']},{r['name']}" for r in csv.DictReader(fh))


EPS_WORDS = re.compile(r"EPS|per share|주당순이익|주당\s*이익", re.I)


def pdf_text(pdf: Path) -> str:
    """Pages 1–2 (company, date, analysts) plus the pages that mention EPS, at most PAGES.

    Forecast tables sit anywhere from page 1 (Korean notes) to page 17
    (Morningstar), so pick pages by content rather than position.
    """
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, timeout=180)
    if out.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {out.stderr.strip()[:200]}")
    pages = out.stdout.split("\f")
    hits = sorted(
        (i for i in range(2, len(pages)) if EPS_WORDS.search(pages[i])),
        key=lambda i: -len(EPS_WORDS.findall(pages[i])),
    )[: PAGES - 2]
    chosen = sorted({0, 1, *hits} & set(range(len(pages))))
    return "\n".join(f"=== page {i + 1} ===\n{pages[i]}" for i in chosen if pages[i].strip())


def ask_claude(text: str) -> dict:
    out = subprocess.run(
        ["claude", "-p", "--model", MODEL, "--output-format", "json", PROMPT + ticker_list()],
        input=text, capture_output=True, text=True, timeout=600,
    )
    if out.returncode != 0:
        raise RuntimeError(f"claude failed: {(out.stderr or out.stdout).strip()[:300]}")
    envelope = json.loads(out.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(f"claude error: {str(envelope.get('result'))[:300]}")
    body = envelope.get("result") or ""
    match = re.search(r"\{.*\}", body, re.S)
    if not match:
        raise RuntimeError(f"no JSON in reply: {body[:200]}")
    return json.loads(match.group(0))


def digits(s: str) -> str:
    return re.sub(r"[^\d.\-]", "", s)


def in_text(printed: str, text: str) -> bool:
    """Is this printed figure really in the report? Compare on digits, ignoring thousands separators."""
    want = digits(printed)
    if not want or want in ("-", "."):
        return False
    # Tokens never span whitespace: table columns sit side by side ("11.80   13.64").
    return want in {digits(tok) for tok in re.findall(r"\d[\d,.]*\d|\d", text)}


def process(pdf: Path, source_url: str = "", origin: str = "inbox", hint: str = "") -> str:
    """`hint` is the ticker a collector already knows the report is about."""
    global model_calls
    data = pdf.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    PDFS.mkdir(exist_ok=True)
    TEXT.mkdir(exist_ok=True)
    kept = PDFS / f"{sha}.pdf"
    if not kept.exists():
        kept.write_bytes(data)
    if any(r["source_sha256"] == sha for r in load()):
        return f"{pdf.name}: already extracted"

    full = subprocess.run(["pdftotext", "-layout", str(kept), "-"], capture_output=True, text=True, timeout=180).stdout
    tickers = {line.split(",")[0] for line in TICKERS_CSV.read_text(encoding="utf-8").splitlines()[1:]}
    got = parse(full, tickers, hint)
    if got:
        text = full
    elif not EPS_WORDS.search(full):
        return f"{pdf.name}: no EPS figures anywhere (commentary or sector note), archived"
    elif model_calls >= MAX_MODEL_CALLS:
        raise RuntimeError(f"unrecognised layout and the model cap ({MAX_MODEL_CALLS}/run) is used up; retry next run")
    else:
        text = pdf_text(kept)
        model_calls += 1
        got = ask_claude(text)
        got["parser"] = "model"
    (TEXT / f"{sha}.txt").write_text(text, encoding="utf-8")
    if not got.get("is_company_report") or not got.get("estimates"):
        return f"{pdf.name}: no company EPS forecasts (sector note or similar), archived"
    ticker = (got.get("ticker") or hint or "").strip()
    if not ticker:
        return f"{pdf.name}: company '{got.get('company')}' is not in tickers.csv, archived"

    checks = [in_text(str(e.get("eps_as_printed", "")), text) for e in got["estimates"]]
    status = "verified" if all(checks) else "needs_review"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    analysts = "; ".join(got.get("analysts") or [])
    rows = []
    for e, ok in zip(got["estimates"], checks):
        fy = f"FY{int(e['fiscal_year'])}"
        rows.append({
            "obs_id": obs_id("pdf", sha, fy),
            "ticker": ticker,
            "analyst": analysts,
            "firm": got.get("firm") or "",
            "kind": "analyst",
            "report_date": got.get("report_date") or "",
            "available_date": got.get("report_date") or "",
            "fiscal_period": fy,
            "fiscal_period_end": e.get("fiscal_year_end") or "",
            "eps_printed": e.get("eps_as_printed") or "",
            "split_factor": 1.0,
            "eps": e.get("eps"),
            "currency": got.get("currency") or "",
            "basis": got.get("eps_basis") or "",
            "source_url": source_url,
            "source_sha256": sha,
            "source_page": e.get("page") or "",
            "origin": f"{origin}/{got.get('parser', 'model')}",
            "status": status,
            "extracted_at": now,
            "note": "" if ok else "EPS figure not found verbatim in report text",
        })
    upsert(rows)
    return f"{pdf.name}: {ticker} {got.get('firm')} {got.get('report_date')} · {len(rows)} years · {status}"


def reverify() -> int:
    """Re-check needs_review rows against their saved text; returns how many now pass."""
    rows = load()
    fixed = 0
    for r in rows:
        if r["status"] != "needs_review":
            continue
        txt = TEXT / f"{r['source_sha256']}.txt"
        if txt.exists() and in_text(r["eps_printed"], txt.read_text(encoding="utf-8")):
            r["status"], r["note"] = "verified", ""
            fixed += 1
    if fixed:
        upsert(rows)
    return fixed


def main(argv: list[str]) -> int:
    INBOX.mkdir(exist_ok=True)
    fixed = reverify()
    if fixed:
        print(f"{fixed} earlier rows now verified against their report text")
    files = [Path(a) for a in argv] if argv else sorted(p for p in INBOX.iterdir() if p.suffix.lower() == ".pdf")
    failed = 0
    for pdf in files:
        try:
            print(process(pdf), flush=True)
            if pdf.parent == INBOX:
                pdf.unlink()
        except Exception as exc:  # noqa: BLE001 — one bad PDF must not block the rest
            failed += 1
            print(f"{pdf.name}: FAILED {exc}", flush=True)
            if pdf.parent == INBOX:
                bad = ROOT / "failed"  # outside the inbox, or the inbox watcher would loop
                bad.mkdir(exist_ok=True)
                shutil.move(str(pdf), bad / pdf.name)
                (bad / f"{pdf.name}.error.txt").write_text(str(exc), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
