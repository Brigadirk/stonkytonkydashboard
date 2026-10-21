#!/usr/bin/env python3
"""Import the reviewed analyst EPS series from the stonkytonkydashboard project.

Reads web/public/data/dashboard.json from a clone of Brigadirk/stonkytonkydashboard
(default ~/Code/stonkytonkydashboard) and upserts its annual EPS forecasts into
analysts/observations.csv. Printed EPS is kept; `eps` is divided by every stock
split that took effect after the report date, so all rows share today's basis.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from store import obs_id, upsert

DASHBOARD = Path.home() / "Code" / "stonkytonkydashboard" / "web" / "public" / "data" / "dashboard.json"
TICKERS = {
    "broadcom": "AVGO", "alphabet": "GOOGL", "nvidia": "NVDA", "sk_hynix": "000660.KS",
    "samsung_electronics": "005930.KS", "micron": "MU", "sandisk": "SNDK",
    "asml": "ASML", "apple": "AAPL", "besi": "BESI.AS",
}
KIND = {
    "individual_analyst_forecast": "analyst",
    "named_analyst_team": "analyst",
    "published_consensus": "consensus",
}


def split_factor(splits: list[dict], report_date: str) -> float:
    factor = 1.0
    for s in splits:
        if report_date < s["effective_date"]:
            factor *= float(s["ratio"])
    return factor


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else DASHBOARD
    data = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for company in data["companies"]:
        ticker = TICKERS.get(company["id"])
        if not ticker:
            continue
        for series in company["series"]:
            for snap in series["snapshots"]:
                factor = split_factor(company.get("splits") or [], snap["report_date"])
                for e in snap["estimates"]:
                    if e.get("eps") is None:
                        continue
                    rows.append({
                        "obs_id": obs_id("dashboard", e["observation_id"]),
                        "ticker": ticker,
                        "analyst": series.get("analyst") or "",
                        "firm": series.get("firm") or "",
                        "kind": KIND.get(series.get("series_type"), "analyst"),
                        "report_date": snap["report_date"],
                        "available_date": snap.get("available_date") or snap["report_date"],
                        "fiscal_period": e["fiscal_period"],
                        "fiscal_period_end": e.get("fiscal_period_end") or "",
                        "eps_printed": e["eps"],
                        "split_factor": factor,
                        "eps": float(e["eps"]) / factor,
                        "currency": series.get("currency") or company.get("currency") or "",
                        "basis": series.get("accounting_basis") or "",
                        "source_url": snap.get("source_url") or "",
                        "source_sha256": snap.get("source_sha256") or "",
                        "source_page": e.get("source_page") or "",
                        "origin": "import_dashboard",
                        "status": "imported",
                        "extracted_at": now,
                        "note": f"dashboard cutoff {data.get('cutoff', '')}",
                    })
    added, replaced = upsert(rows)
    print(f"{len(rows)} EPS forecasts from {path.name}: {added} new, {replaced} refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
