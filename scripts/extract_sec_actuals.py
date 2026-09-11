#!/usr/bin/env python3
"""Export selected SEC facts with every filing vintage, without scoring forecasts."""
import argparse
import csv
from datetime import date
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
TAGS = {
    "us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
        "RevenueFromContractWithCustomerIncludingAssessedTax": "revenue",
        "SalesRevenueNet": "revenue", "Revenues": "revenue",
        "EarningsPerShareBasic": "eps_basic",
        "EarningsPerShareDiluted": "eps_diluted",
        "NetIncomeLoss": "net_income",
        "NetIncomeLossAvailableToCommonStockholdersBasic": "net_income_common",
        "OperatingIncomeLoss": "operating_income",
        "WeightedAverageNumberOfSharesOutstandingBasic": "shares_basic",
        "WeightedAverageNumberOfDilutedSharesOutstanding": "shares_diluted",
    },
    "ifrs-full": {
        "Revenue": "revenue", "BasicEarningsLossPerShare": "eps_basic",
        "DilutedEarningsLossPerShare": "eps_diluted",
        "ProfitLossAttributableToOwnersOfParent": "net_income_parent",
        "WeightedAverageShares": "shares_basic",
        "AdjustedWeightedAverageShares": "shares_diluted",
    },
}
FIELDS = ["company_id", "metric", "taxonomy", "tag", "value", "unit", "period_start", "period_end", "duration_days", "duration_bucket", "filed", "accession", "form", "filing_fiscal_year", "filing_fiscal_period", "frame", "source_url", "source_file", "source_sha256", "retrieved_at", "validation_status"]


def extract(payload, source, since, cutoff):
    for taxonomy, tags in TAGS.items():
        for tag, metric in tags.items():
            concept = payload.get("facts", {}).get(taxonomy, {}).get(tag, {})
            for unit, facts in concept.get("units", {}).items():
                for fact in facts:
                    start, end, filed = fact.get("start", ""), fact.get("end", ""), fact.get("filed", "")
                    if not filed or filed > cutoff or not end or not since <= end <= cutoff:
                        continue
                    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1 if start else ""
                    bucket = "instant_or_unknown"
                    if days:
                        bucket = "quarter" if 75 <= days <= 105 else "annual" if 350 <= days <= 380 else "other_duration"
                    yield dict(company_id=source["company_ids"], metric=metric, taxonomy=taxonomy, tag=tag, value=fact["val"], unit=unit,
                               period_start=start, period_end=end, duration_days=days, duration_bucket=bucket,
                               filed=filed, accession=fact.get("accn", ""), form=fact.get("form", ""),
                               filing_fiscal_year=fact.get("fy", ""), filing_fiscal_period=fact.get("fp", ""), frame=fact.get("frame", ""),
                               source_url=source["source_url"], source_file=source["local_file"], source_sha256=source["sha256"], retrieved_at=source["retrieved_at"],
                               validation_status="raw_sec_fact_unreconciled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default="2020-09-10")
    parser.add_argument("--cutoff", default="2026-09-10")
    args = parser.parse_args()
    date.fromisoformat(args.since)
    date.fromisoformat(args.cutoff)
    if args.since > args.cutoff:
        parser.error("since must precede cutoff")
    db = sqlite3.connect(ROOT / "data/archive.sqlite")
    db.row_factory = sqlite3.Row
    sources = db.execute("SELECT * FROM downloads WHERE id IN (SELECT MAX(id) FROM downloads WHERE source_kind='sec_companyfacts' AND status='downloaded' GROUP BY source_url)").fetchall()
    rows, counts = [], {}
    for source in sources:
        payload = json.loads((ROOT / source["local_file"]).read_text())
        company_rows = list(extract(payload, source, args.since, args.cutoff))
        rows.extend(company_rows)
        counts[source["company_ids"]] = len(company_rows)
    # A repeated identical context is not a new observation. Distinct filings,
    # units and values remain separate, including restatements and split changes.
    unique = {tuple(str(row[key]) for key in FIELDS): row for row in rows}
    with (ROOT / "data/sec_actuals_raw.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(unique.values())
    print(json.dumps({"rows": len(unique), "by_company": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
