"""One table of individual analyst EPS forecasts, whatever their source.

    analysts/observations.csv   one row per (report, fiscal year) EPS forecast

Rows keep EPS as printed plus a split-adjusted value on today's share basis,
the report and availability dates, and where the number came from. `status`
says how far to trust it: `imported` (reviewed in the earlier dashboard
project), `verified` (extracted and every number found in the report text),
or `needs_review` (extracted, but a number could not be matched in the text).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBSERVATIONS = ROOT / "observations.csv"
FIELDS = [
    "obs_id", "ticker", "analyst", "firm", "kind", "report_date", "available_date",
    "fiscal_period", "fiscal_period_end", "eps_printed", "split_factor", "eps",
    "currency", "basis", "source_url", "source_sha256", "source_page",
    "origin", "status", "extracted_at", "note",
]


def obs_id(*parts: object) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:20]


def load() -> list[dict]:
    if not OBSERVATIONS.exists():
        return []
    with open(OBSERVATIONS, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save(rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: (r["ticker"], r["report_date"], r["firm"], r["fiscal_period"]))
    tmp = OBSERVATIONS.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    tmp.replace(OBSERVATIONS)


def upsert(new_rows: list[dict]) -> tuple[int, int]:
    """Add rows by obs_id; an existing id is replaced. Returns (added, replaced)."""
    rows = {r["obs_id"]: r for r in load()}
    added = sum(1 for r in new_rows if r["obs_id"] not in rows)
    for r in new_rows:
        rows[r["obs_id"]] = r
    save(list(rows.values()))
    return added, len(new_rows) - added
