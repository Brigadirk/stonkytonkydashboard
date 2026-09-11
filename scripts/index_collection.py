#!/usr/bin/env python3
"""Validate retained sources and build a catalog and document-coverage matrix."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {"BESI": "besi", "BESI.AS": "besi", "AAPL": "apple", "AVGO": "broadcom", "ALPHABET": "alphabet", "GOOGL": "alphabet", "GOOG": "alphabet", "NVDA": "nvidia", "MU": "micron", "SNDK": "sandisk", "ASML": "asml", "000660": "sk_hynix", "005930": "samsung_electronics"}
FIELDS = ["collection", "source_url", "company_ids", "document_kind", "firm", "analyst_name", "report_date", "retrieved_at", "sha256", "local_file", "text_file", "status", "notes"]


def company_ids(value):
    return ";".join(dict.fromkeys(ALIASES.get(v.strip(), v.strip()) for v in re.split(r"[;,|]", value) if v.strip()))


def path_in_project(value, manifest):
    if not value:
        return ""
    path = ROOT / value
    if not path.is_file():
        path = manifest.parent / value
    if not path.is_file():
        raise ValueError(f"Missing source file: {value} from {manifest}")
    return path.resolve().relative_to(ROOT).as_posix()


def main(update_database=True):
    db = sqlite3.connect(ROOT / "data/archive.sqlite")
    db.row_factory = sqlite3.Row
    rows = []
    latest = db.execute("SELECT * FROM downloads WHERE id IN (SELECT MAX(id) FROM downloads GROUP BY source_url)").fetchall()
    for source in latest:
        row = {key: source[key] or "" for key in FIELDS if key in source.keys()}
        collection = "issuer" if source["source_kind"].startswith(("issuer_", "sec_")) else "direct_collection"
        row.update(collection=collection, document_kind=source["source_kind"], notes=source["error"] or "")
        rows.append(row)
    manifests = list((ROOT / "data/collection").glob("*/manifest.csv")) + list((ROOT / "data/collection").glob("*/issuer_manifest.csv"))
    for manifest in sorted(manifests):
        issuer_dates = {}
        outcomes = manifest.parent / "issuer_eps_outcomes.csv"
        if outcomes.exists():
            with outcomes.open() as handle:
                issuer_dates = {r["source_sha256"]: r["initial_release_date"] for r in csv.DictReader(handle)}
        with manifest.open(newline="") as f:
            for source in csv.DictReader(f):
                if manifest.name == "issuer_manifest.csv":
                    source = {**source, "company_ids": source.get("company_ids", source.get("company_id", "")), "local_file": source.get("local_file", source.get("source_file", "")), "sha256": source.get("sha256", source.get("source_sha256", "")), "report_date": source.get("report_date") or issuer_dates.get(source.get("source_sha256", ""), "")}
                row = {key: source.get(key, "") for key in FIELDS}
                row.update(collection=manifest.parent.name, company_ids=company_ids(source["company_ids"]), document_kind="broker_report")
                is_issuer = source.get("document_kind", "").startswith("issuer_") or source.get("status", "").startswith("retained_issuer_")
                if is_issuer:
                    row["document_kind"] = source.get("document_kind") or "issuer_earnings_release"
                if source.get("local_file") and source.get("sha256"):
                    row["local_file"] = path_in_project(source["local_file"], manifest)
                    row["text_file"] = path_in_project(source.get("text_file", ""), manifest)
                    if Path(row["local_file"]).suffix.lower() != ".pdf" and not is_issuer:
                        row["document_kind"] = "web_extract" if "extract" in source["status"] else "broker_article"
                else:
                    # Some collectors retain an intended path after a failed fetch.
                    row["local_file"] = ""
                    row["text_file"] = ""
                if source["status"].startswith("excluded"):
                    row["document_kind"] = "excluded"
                    row["company_ids"] = ""
                rows.append(row)
    for row in rows:
        if row["local_file"]:
            digest = hashlib.sha256((ROOT / row["local_file"]).read_bytes()).hexdigest()
            if digest != row["sha256"]:
                raise ValueError(f"Checksum mismatch: {row['local_file']}")
    with (ROOT / "data/source_catalog.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    if update_database:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS source_catalog (" + ",".join(f"{key} TEXT" for key in FIELDS) + ")")
            db.execute("DELETE FROM source_catalog")
            db.executemany("INSERT INTO source_catalog VALUES (" + ",".join("?" for _ in FIELDS) + ")", [[row[key] for key in FIELDS] for row in rows])
    with (ROOT / "data/universe.csv").open(newline="") as f:
        universe = list(csv.DictReader(f))
    coverage = []
    for company in universe:
        identifier = company["company_id"]
        for year in range(2020, 2027):
            relevant = [row for row in rows if row["document_kind"] in ("broker_report", "broker_article", "web_extract") and identifier in row["company_ids"].split(";") and row["report_date"].startswith(str(year)) and row["local_file"]]
            coverage.append(dict(company_id=identifier, report_year=year, broker_documents=len({row["sha256"] for row in relevant}), authors=";".join(sorted({row["analyst_name"] for row in relevant if row["analyst_name"]})), coverage_status="partial_documents_only" if relevant else "no_dated_document_collected"))
    with (ROOT / "data/document_coverage.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=coverage[0])
        writer.writeheader()
        writer.writerows(coverage)
    retained = [row for row in rows if row["local_file"] and row["document_kind"] != "excluded"]
    summary = dict(unique_retained_documents=len({row["sha256"] for row in retained}), unique_broker_pdfs=len({row["sha256"] for row in retained if row["document_kind"] == "broker_report"}), issuer_sources=len({row["sha256"] for row in retained if row["collection"] == "issuer" or row["document_kind"].startswith("issuer_")}), missing_source_files=sum(not row["local_file"] for row in rows), catalog_records=len(rows))
    (ROOT / "data/collection_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-db-update', action='store_true', help='Write the CSV catalog without mutating the input archive database')
    main(update_database=not parser.parse_args().no_db_update)
