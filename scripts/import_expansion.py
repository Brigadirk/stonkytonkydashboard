#!/usr/bin/env python3
"""Merge reviewed additions into an imported dashboard without rebuilding absent archives.

Inputs are a preserved base snapshot, a staged price collection and reviewed
forecast/actual evidence. The output stays in the run directory until checked.
"""
import argparse
from collections import defaultdict
import copy
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA_NOTES = {
    "nebius": ["The August 2026 report changes EPS values but still prints a 13 May model date. The chart uses the new values only after 12 August and keeps the May date for age checks. The conflicting model date remains unresolved."],
    "palantir": ["The latest retained Palantir model is dated 4 May 2026, although the report was printed in August. It is 130 days old at the 11 September cutoff. A shorter forecast age limit can remove its target."],
    "tsmc": ["TSMC forecasts are stated in USD per depositary share by iFAST, using a Bloomberg compilation. The source does not state whether EPS is adjusted or unadjusted. This series stays separate from named analyst estimates."],
    "spacex": ["SpaceX has a short listed price history. The June analyst reports revise historical earnings as well as forecasts. Their accounting scope has not been fully reconciled."],
    "cerebras": ["Prices and reported annual EPS are available. No usable dated annual forecast history was retained, so valuation targets remain unavailable."],
}


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source(record, root, checked):
    path = (root / record["source_file"]).resolve()
    path.relative_to(root.resolve())
    digest = record["source_sha256"]
    if not record["source_url"].startswith(("https://", "http://")):
        raise ValueError("Source URL is missing")
    if (path, digest) not in checked:
        if sha(path) != digest:
            raise ValueError(f"Source hash mismatch: {path}")
        checked.add((path, digest))


def validate_series(series, company, cutoff, root, checked):
    if series["currency"] != company["currency"]:
        raise ValueError(f"EPS currency differs from listing: {company['id']}")
    if not series.get("accounting_basis") or not series.get("firm"):
        raise ValueError("Missing EPS definition or publisher")
    if series["series_type"] == "individual_analyst_forecast" and not series["analyst"]:
        raise ValueError("Named analyst missing")
    seen = set()
    for snapshot in series["snapshots"]:
        if snapshot["id"] in seen:
            raise ValueError("Duplicate snapshot")
        seen.add(snapshot["id"])
        report = date.fromisoformat(snapshot["report_date"])
        available = date.fromisoformat(snapshot["available_date"])
        model = date.fromisoformat(snapshot.get("model_date") or snapshot["report_date"])
        basis = date.fromisoformat(snapshot["share_basis_date"])
        if report.isoformat() > cutoff or model > report or basis > report:
            raise ValueError("Forecast dates are inconsistent or after cutoff")
        if available <= report:
            raise ValueError("Dated reports cannot enter their own report-day close")
        if snapshot.get("verified_available_date") or snapshot["availability_basis"] == "verified_available_at":
            raise ValueError("This importer only admits unverified report-date reconstructions")
        check_source(snapshot, root, checked)
        if snapshot["kind"] != "annual":
            raise ValueError("This collection requires explicit annual fiscal periods")
        periods = sorted(snapshot["estimates"], key=lambda e: e["fiscal_period_start"])
        previous_end = None
        for estimate in periods:
            start = date.fromisoformat(estimate["fiscal_period_start"])
            end = date.fromisoformat(estimate["fiscal_period_end"])
            if not 350 <= (end - start).days + 1 <= 380:
                raise ValueError("Invalid annual fiscal period")
            if previous_end and start <= previous_end:
                raise ValueError("Overlapping fiscal periods")
            previous_end = end
            if not math.isfinite(estimate["eps"]) or not estimate.get("source_page"):
                raise ValueError("Invalid EPS or missing source locator")
    series["snapshots"].sort(key=lambda s: (s["available_date"], s["report_date"]))


def merge(base, universe, price_dir, evidence_files, actuals_file=None, root=ROOT):
    data = copy.deepcopy(base)
    summary = json.loads((price_dir / "summary.json").read_text())
    cutoff = summary["cutoff"]
    if cutoff < base["cutoff"] or not summary["adjustment_definition_verified"]:
        raise ValueError("Invalid price cutoff or unverified split basis")
    manifest = json.loads((price_dir / "manifest.json").read_text())
    sources = {r["source_sha256"]: r for r in manifest if r.get("status") == 200}
    checked = set()
    prices, splits = defaultdict(list), defaultdict(list)
    for row in read_csv(price_dir / "prices.csv"):
        cid = row.pop("company_id")
        row["close"] = float(row["close"])
        if not math.isfinite(row["close"]) or row["close"] <= 0 or row["date"] > cutoff:
            raise ValueError("Invalid daily close")
        if row["adjustment_basis"] != "split_adjusted_to_cutoff":
            raise ValueError("Unsupported price adjustment basis")
        check_source(sources[row["source_sha256"]], root, checked)
        prices[cid].append(row)
    for row in read_csv(price_dir / "splits.csv"):
        cid = row.pop("company_id")
        row["ratio"] = float(row["ratio"])
        splits[cid].append(row)
    existing = {c["id"]: c for c in data["companies"]}
    companies, carried = [], []
    for identity in universe:
        cid = identity["company_id"]
        company = existing.get(cid, {"id": cid, "series": [], "gaps": [], "forecast_count": 0})
        if not company["series"]:
            company["gaps"] = ["Price history is collected. Annual EPS forecast coverage is still being checked."]
        company.update(name=identity["company_name"], symbol=identity["listing_symbol"],
                       exchange=identity["exchange"], currency=identity["price_currency"])
        if cid in DATA_NOTES:
            company["data_notes"] = DATA_NOTES[cid]
        if not prices[cid] or any(p["currency"] != company["currency"] for p in prices[cid]):
            raise ValueError(f"Missing prices or mismatched currency: {cid}")
        by_date = {p["date"]: p for p in prices[cid]}
        if len(by_date) != len(prices[cid]):
            raise ValueError("Duplicate price dates")
        # Retain reviewed closes absent from the new provider response. Require
        # unchanged share units between the old and new cutoff.
        for old in company.get("prices", []):
            if old["date"] not in by_date:
                if any(base["cutoff"] < s["effective_date"] <= cutoff for s in splits[cid]):
                    raise ValueError("Cannot carry an old close across a new split")
                by_date[old["date"]] = old
                carried.append({"company_id": cid, "date": old["date"], "source_url": old["source_url"]})
        company["prices"] = sorted(by_date.values(), key=lambda p: p["date"])
        company["splits"] = sorted(splits[cid], key=lambda s: s["effective_date"])
        companies.append(company)
    data["companies"] = companies
    by_id = {c["id"]: c for c in companies}
    if len(by_id) != len(companies):
        raise ValueError("Duplicate company identity")
    new_sources, added_estimates = set(), 0
    for path in evidence_files:
        evidence = json.loads(path.read_text())
        for addition in evidence["companies"]:
            company = by_id[addition["company_id"]]
            if company["series"]:
                raise ValueError("Expansion cannot replace existing forecast series")
            for series in addition["series"]:
                validate_series(series, company, cutoff, root, checked)
                company["series"].append(series)
                for snapshot in series["snapshots"]:
                    added_estimates += len(snapshot["estimates"])
                    company["forecast_count"] += len(snapshot["estimates"])
                    if snapshot["source_file"].endswith(".pdf"):
                        new_sources.add(snapshot["source_sha256"])
            company["gaps"] = addition.get("gaps", []) + company.get("data_notes", []) + [
                "Newly retained reports use printed-date reconstruction. Original historical availability is unverified.",
                "Forecast coverage is partial. No current model is backfilled before its report date."]
            if not company["series"]:
                company["gaps"].append("No usable annual EPS forecast series was found; valuation targets remain unavailable.")
        for gap in evidence.get("gaps", []):
            if isinstance(gap, dict) and gap.get("company_id") in by_id:
                by_id[gap["company_id"]]["gaps"] = [gap["details"]]
    if actuals_file:
        actuals = json.loads(actuals_file.read_text())
        for record in actuals["companies"]:
            company = by_id[record["company_id"]]
            annual = record["annual_eps"]
            for row in annual:
                if row["filing_date"] > cutoff or not math.isfinite(float(row["value"])):
                    raise ValueError("Invalid reported earnings value or filing date")
                check_source(row, root, checked)
            company["reported_earnings"] = {"annual_eps": annual, "notes": record.get("notes", [])}
    data["cutoff"] = cutoff
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["totals"]["forecast_observations"] += added_estimates
    data["totals"]["broker_pdfs"] += len(new_sources)
    data.pop("backtest_readiness", None)  # Recomputed after import against all prices and series.
    data["access_notes"] = [
        "Prices were collected through 11 September 2026. Original downloads and hashes are retained locally.",
        "The original 10 forecast archives are preserved. New companies have separate dated reports; coverage remains partial.",
        "Printed report dates support reconstruction only. Strict historical availability requires separate evidence.",
        "TSMC's US depositary listing uses USD-per-ADS forecasts. Original TWD-per-ordinary forecasts stay outside its valuation series.",
        "Reported earnings stay separate from forecasts and are not automatically matched to analyst-adjusted EPS.",
    ]
    data["collection_update"] = {"collected_on": "2026-09-14", "cutoff": cutoff,
        "added_forecast_observations": added_estimates, "added_broker_pdfs": len(new_sources),
        "carried_reviewed_closes": carried,
        "evidence_files": [str(p.relative_to(root)) for p in evidence_files],
        "price_directory": str(price_dir.relative_to(root))}
    return data


def atomic_write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(body)
    temporary.replace(path)


def publish(data, price_dir, run_directory, root=ROOT):
    """Publish checked inputs and preserve the prior files for this collection run."""
    market = root / "data/market"
    summary = json.loads((price_dir / "summary.json").read_text())
    summary["total_prices"] = sum(len(c["prices"]) for c in data["companies"])
    summary["carried_reviewed_closes"] = data["collection_update"]["carried_reviewed_closes"]
    by_id = {c["id"]: c for c in data["companies"]}
    for row in summary["coverage"]:
        prices = by_id[row["company_id"]]["prices"]
        row.update(rows=len(prices), first_date=prices[0]["date"], last_date=prices[-1]["date"])
    old_manifest_path = market / "manifest.json"
    old_manifest = json.loads(old_manifest_path.read_text()) if old_manifest_path.exists() else []
    new_manifest = json.loads((price_dir / "manifest.json").read_text())
    manifest = list({(r.get("source_url"), r.get("source_sha256")): r
                     for r in old_manifest + new_manifest}.values())
    def csv_body(fields, rows):
        handle = io.StringIO(newline="")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        return handle.getvalue()
    prices = [dict(company_id=c["id"], **p) for c in data["companies"] for p in c["prices"]]
    bodies = {
        root / "web/public/data/dashboard.json": json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n",
        market / "summary.json": json.dumps(summary, indent=2) + "\n",
        market / "manifest.json": json.dumps(manifest, indent=2) + "\n",
        market / "prices.csv": csv_body(["company_id", "date", "close", "currency", "adjustment_basis", "source_url", "source_sha256"], prices),
        market / "splits.csv": (price_dir / "splits.csv").read_text(),
    }
    for path in bodies:
        backup = run_directory / "before" / path.relative_to(root)
        if path.exists() and not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
    for path, body in bodies.items():
        atomic_write(path, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--price-directory", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, nargs="+", required=True)
    parser.add_argument("--actuals", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publish", action="store_true", help="Also update the browser dataset and market files after all input checks pass")
    args = parser.parse_args()
    data = merge(json.loads(args.base.read_text()), read_csv(ROOT / "data/universe.csv"),
                 args.price_directory.resolve(), [p.resolve() for p in args.evidence],
                 args.actuals.resolve() if args.actuals else None)
    atomic_write(args.output, json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n")
    if args.publish:
        publish(data, args.price_directory.resolve(), args.output.resolve().parent)
    print(json.dumps({"companies": len(data["companies"]),
        "prices": sum(len(c["prices"]) for c in data["companies"]),
        "series": sum(len(c["series"]) for c in data["companies"]),
        "cutoff": data["cutoff"], **data["collection_update"]}, indent=2))


if __name__ == "__main__":
    main()
