#!/usr/bin/env python3
"""Combine extracted tables without claiming historical availability or accuracy."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from index_collection import ALIASES, path_in_project
from model_dates import apply_model_dates

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["observation_id", "forecast_version_key", "company_id", "forecaster", "firm", "observation_type", "metric", "value", "unit", "currency", "fiscal_period", "fiscal_period_end", "report_date", "model_date", "printed_report_timestamp", "original_available_at", "share_basis_date", "accounting_basis", "source_url", "source_file", "source_sha256", "source_page", "extraction_status", "ranking_status", "original_value", "original_unit", "notes"]
FIELDS.append("first_observed_at")
FIELDS.append("original_extraction_status")
FIELDS.extend(["original_model_date", "model_date_evidence"])


def normalize_number(value, unit, metric, currency, already_base=False):
    number = Decimal(value.replace(",", ""))
    if metric == "revenue":
        if not already_base:
            factors = {"USD_million": Decimal(1000000), "EUR_million": Decimal(1000000), "USD_billion": Decimal(1000000000), "EUR_billion": Decimal(1000000000)}
            if unit not in factors:
                raise ValueError(f"Unrecognized revenue unit: {unit}")
            number *= factors[unit]
        target_unit = currency
    elif metric.startswith("eps"):
        target_unit = currency + "_per_share"
    elif unit == "percent":
        target_unit = "percent"
    else:
        raise ValueError(f"Unrecognized metric/unit combination: {metric}/{unit}")
    return format(number, "f"), target_unit


def main():
    rows = []
    exclusions_path = ROOT / 'data/market/observation_exclusions.json'
    exclusions = json.loads(exclusions_path.read_text()) if exclusions_path.exists() else []
    for path in sorted((ROOT / "data/collection").glob("*/observations.csv")):
        with path.open(newline="") as f:
            observations = list(csv.DictReader(f))
        for obs in observations:
            row = {key: "" for key in FIELDS}
            korean = "target_period" in obs and "original_unit" in obs and "pdf_page" in obs
            row.update(company_id=ALIASES.get(obs["company_id"], obs["company_id"]), forecaster=obs["analyst_name"], firm=obs["firm"],
                       observation_type=obs.get("source_type", "individual_analyst_forecast"), metric=obs["metric"], currency=obs["currency"],
                       fiscal_period=obs.get("target_period", obs.get("fiscal_period", "")), fiscal_period_end=obs.get("target_period_end", ""),
                       report_date=obs["report_date"], model_date=obs.get("model_date", ""), printed_report_timestamp=obs.get("printed_report_timestamp", ""),
                       original_available_at=obs.get("original_available_at", ""), share_basis_date=obs.get("share_basis_date", ""), accounting_basis=obs["basis"], source_url=obs["source_url"],
                       source_file=path_in_project(obs["local_file"], path), source_page=obs.get("pdf_page", obs.get("page", "")),
                       extraction_status=obs.get("extraction_status", obs.get("status", "")), original_value=obs.get("original_value", obs["value"]),
                       original_unit=obs.get("original_unit", obs.get("unit", "")), notes=obs.get("notes", ""))
            if obs.get("availability_basis", "").startswith("first_observed_"):
                row["first_observed_at"] = obs.get("available_at", "")
                if not row["first_observed_at"]:
                    raise ValueError("First-observed public snapshots require the retained capture timestamp")
            row["value"], row["unit"] = normalize_number(obs["value"], row["original_unit"], row["metric"], row["currency"], already_base=korean)
            if row["unit"] == "percent":
                row["currency"] = ""
            if obs.get("forecast_type") == "consensus_reported_by_analyst":
                row["observation_type"] = "report_embedded_consensus"
                row["forecaster"] = ""
            row["source_sha256"] = hashlib.sha256((ROOT / row["source_file"]).read_bytes()).hexdigest()
            row['original_extraction_status'] = row['extraction_status']
            for rule in exclusions:
                if row['source_sha256'] == rule['source_sha256'] and row['company_id'] == rule['company_id'] and row['firm'] == rule['firm']:
                    row['extraction_status'] = 'quarantined_' + rule['reason_code']
                    row['notes'] += ' Review exclusion: ' + rule['reason']
            uncertain = any(token in row["extraction_status"] for token in ("quarantin", "internal_conflict", "search_extract", "attribution_review"))
            row["ranking_status"] = "quarantined" if uncertain else "unscored_availability_and_actuals_unreconciled"
            if row["extraction_status"] == "search_extract_pending_period_basis_and_author":
                row["observation_type"] = "publisher_forecast_unattributed"
            if row["observation_type"] in ("report_embedded_consensus", "published_consensus"):
                row["forecaster"] = ""
            if row["observation_type"] in ("report_embedded_consensus", "published_consensus") and not uncertain:
                row["ranking_status"] = "consensus_not_individual_analyst"
            # Preserve repeated appearances, but identify identical numerical model
            # versions so a reprinted table need not count as another prediction.
            version = [row[key] for key in ("company_id", "forecaster", "firm", "observation_type", "metric", "fiscal_period", "value", "unit", "accounting_basis")]
            version.append(row["model_date"] or row["report_date"])
            row["forecast_version_key"] = hashlib.sha256(json.dumps(version).encode()).hexdigest()[:24]
            provenance = [row["forecast_version_key"], row["source_sha256"], row["source_page"]]
            row["observation_id"] = hashlib.sha256(json.dumps(provenance).encode()).hexdigest()[:24]
            rows.append(row)
    apply_model_dates(rows, ROOT)
    for row in rows:
        if row['model_date_evidence']:
            version = [row[key] for key in ("company_id", "forecaster", "firm", "observation_type", "metric", "fiscal_period", "value", "unit", "accounting_basis")]
            version.append(row['model_date'])
            row['forecast_version_key'] = hashlib.sha256(json.dumps(version).encode()).hexdigest()[:24]
            row['observation_id'] = hashlib.sha256(json.dumps([row['forecast_version_key'], row['source_sha256'], row['source_page']]).encode()).hexdigest()[:24]
    unique = {row["observation_id"]: row for row in rows}
    with (ROOT / "data/collected_forecasts.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(unique.values())
    print(json.dumps({"extracted_observations": len(unique), "distinct_forecast_version_keys": len({r["forecast_version_key"] for r in unique.values()}), "quarantined": sum(r["ranking_status"] == "quarantined" for r in unique.values()), "consensus_observations": sum(r["observation_type"] in ("report_embedded_consensus", "published_consensus") for r in unique.values())}, sort_keys=True))


if __name__ == "__main__":
    main()
