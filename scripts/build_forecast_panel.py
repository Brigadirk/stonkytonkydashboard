#!/usr/bin/env python3
"""Prepare isolated, source-backed EPS series for dated-report reconstruction.

This does not produce a verified point-in-time dataset or combine analysts into
consensus. All raw observations remain in collected_forecasts.csv.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from availability import load_evidence

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 9, 10)
COMPANIES = (
    "broadcom", "alphabet", "nvidia", "sk_hynix", "samsung_electronics",
    "micron", "sandisk", "asml", "apple", "besi",
)
PANEL_FIELDS = (
    "observation_id", "company_id", "series_id", "analyst", "firm", "metric",
    "accounting_basis", "currency", "fiscal_period", "fiscal_period_end",
    "report_date", "available_date", "availability_basis", "eps",
    "share_basis_date", "source_url", "source_file", "source_sha256", "source_page",
    "model_date", "snapshot_id", "fiscal_period_start", "fiscal_calendar_basis", "series_type", "original_accounting_basis", "basis_alias_evidence",
    "fiscal_calendar_source_url", "source_metric", "notes",
    "first_observed_at",
    "verified_available_date", "verified_available_at", "availability_evidence_url", "verification_kind",
)
SERIES_FIELDS = (
    "series_id", "company_id", "label", "analyst", "firm", "accounting_basis",
    "currency", "coverage_note", "series_type", "comparability_note", "comparability_source_url",
)
CONSENSUS_TYPES = {"report_embedded_consensus", "published_consensus"}
CALENDAR_SOURCES = {
    "besi": "https://www.besi.com/fileadmin/data/Investor_Relations/_Semi__Annual_Reports/Annual_Report_2025.pdf",
    "apple": "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm",
    "asml": "https://ourbrand.asml.com/m/79d325b168e0fd7e/original/2024-Annual-Report-based-on-US-GAAP.pdf",
    "sandisk": "https://investor.sandisk.com/ir-resources/investor-faqs",
    "broadcom": "https://investors.broadcom.com/static-files/752e631c-b5f3-46af-9d67-bdeb658f5fa2",
    "micron": "https://www.sec.gov/Archives/edgar/data/723125/000072312526000006/R26.htm",
    "nvidia": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm",
    "alphabet": "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm",
    "samsung_electronics": "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_con_quarter04_all.pdf",
    "sk_hynix": "https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/",
}


def stable_id(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def fiscal_end(company_id: str, year: int) -> tuple[date, str]:
    """Apply the issuer's fiscal calendar, not broker month-end shorthand.

    Dates in future years are rule-derived projections, not announced dates.
    See FORWARD_EPS_COVERAGE.md for the primary-source evidence.
    """
    if company_id in {"alphabet", "sk_hynix", "samsung_electronics", "asml", "besi"}:
        return date(year, 12, 31), "issuer_calendar_year_december_31"
    if company_id == "nvidia":
        last = date(year, 1, 31)
        return last - timedelta(days=(last.weekday() - 6) % 7), "issuer_rule_last_sunday_january"
    if company_id == "apple":
        last = date(year, 9, 30)
        return last - timedelta(days=(last.weekday() - 5) % 7), "issuer_rule_last_saturday_september"
    if company_id == "broadcom":
        anchor, weekday = date(year, 10, 31), 6
    elif company_id == "micron":
        anchor, weekday = date(year, 8, 31), 3
    elif company_id == "sandisk":
        anchor, weekday = date(year, 6, 30), 4
    else:
        raise ValueError(f"No verified fiscal calendar for {company_id}")
    offset = (weekday - anchor.weekday() + 3) % 7 - 3
    name = {"broadcom": "closest_sunday_october_31", "micron": "closest_thursday_august_31", "sandisk": "closest_friday_june_30"}[company_id]
    return anchor + timedelta(days=offset), "issuer_rule_" + name


def eligibility(row: dict[str, str], as_of: date) -> str | None:
    if not row["metric"].startswith("eps"):
        return "not_eps"
    if row["ranking_status"] == "quarantined":
        return "quarantined"
    consensus = row["observation_type"] in CONSENSUS_TYPES
    if not consensus and row["observation_type"] != "individual_analyst_forecast":
        return "unsupported_forecast_type"
    if not row["firm"].strip() or (not consensus and not row["forecaster"].strip()):
        return "unattributed"
    if row["accounting_basis"] == "eps_basis_not_restated":
        return "accounting_basis_not_stated"
    if not re.fullmatch(r"FY\d{4}", row["fiscal_period"]):
        return "fiscal_period_unresolved"
    if row["company_id"] not in CALENDAR_SOURCES:
        return "fiscal_calendar_unverified"
    if not row["report_date"]:
        return "report_date_missing"
    if date.fromisoformat(row["report_date"]) > as_of:
        return "future_report"
    if row["model_date"] and date.fromisoformat(row["model_date"]) > date.fromisoformat(row["report_date"]):
        return "model_postdates_report"
    if not row["source_file"] or not row["source_sha256"]:
        return "original_artifact_missing"
    if row["unit"] != row["currency"] + "_per_share":
        return "eps_unit_unresolved"
    if not row["accounting_basis"]:
        return "accounting_basis_missing"
    if not math.isfinite(float(row["value"])):
        return "non_finite_eps"
    return None


def normalize_basis(row, rules):
    for rule in rules:
        if (row["company_id"] in rule["company_ids"] and row["firm"] == rule["firm"]
                and row["forecaster"] == rule["analyst"] and row["accounting_basis"] == rule["original_basis"]
                and (not rule.get("model_dates") or (row["model_date"] or row["report_date"]) in rule["model_dates"])
                and (not rule.get("fiscal_periods") or row["fiscal_period"] in rule["fiscal_periods"])
                and (not rule.get("source_hashes") or row["source_sha256"] in rule["source_hashes"])):
            matched = rule.get("matched_values", {}).get(row["fiscal_period"])
            if matched is not None and float(row["value"]) != float(matched):
                raise ValueError('EPS extraction differs from the exact value supporting its basis alias')
            return rule["canonical_basis"], rule["evidence"]["source_url"]
    return row["accounting_basis"], ""


def build_panel(rows: list[dict[str, str]], root: Path = ROOT, as_of: date = AS_OF):
    availability = load_evidence(root)
    alias_file = root / "data/market/basis_aliases.json"
    alias_rules = json.loads(alias_file.read_text()) if alias_file.exists() else []
    for rule in alias_rules:
        evidence = rule.get('evidence', {})
        if evidence.get('source_file') and evidence.get('source_sha256'):
            artifact = root / evidence['source_file']
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != evidence['source_sha256']:
                raise ValueError(f'Basis-alias evidence hash mismatch: {artifact}')
    split_file = root / "data/market/splits.csv"
    if split_file.exists():
        with split_file.open() as handle:
            splits = list(csv.DictReader(handle))
    else:
        splits = []
    exclusions = Counter()
    company_exclusions = defaultdict(Counter)
    groups = defaultdict(list)
    verified_paths = set()
    for row in rows:
        reason = eligibility(row, as_of)
        if not reason and row["model_date"] and not row.get("share_basis_date"):
            if any(split["company_id"] == row["company_id"] and row["model_date"] < split["effective_date"] <= row["report_date"] for split in splits):
                reason = "share_basis_crosses_split_unresolved"
        if reason:
            exclusions[reason] += 1
            if row["metric"].startswith("eps"):
                company_exclusions[row["company_id"]][reason] += 1
            continue
        source = root / row["source_file"]
        path_key = (str(source), row["source_sha256"])
        if path_key not in verified_paths:
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != row["source_sha256"]:
                raise ValueError(f"Missing or changed source: {source}")
            verified_paths.add(path_key)
        # Consensus has no individual author and never shares an analyst series.
        analyst = "" if row["observation_type"] in CONSENSUS_TYPES else row["forecaster"]
        basis, alias_evidence = normalize_basis(row, alias_rules)
        row = {**row, "basis_alias_evidence": alias_evidence}
        key = (row["company_id"], analyst, row["firm"], basis, row["currency"])
        groups[(key, row["source_sha256"], row["report_date"], row["model_date"])].append(row)

    panel = []
    signatures = set()
    for (key, source_hash, report_day, model_day), snapshot_rows in sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][1])):
        company_id, analyst, firm, basis, currency = key
        series_type = "published_consensus" if not analyst else "named_analyst_team" if ';' in analyst else "individual_analyst_forecast"
        series_id = company_id + "_" + stable_id(*key)
        by_period = {}
        for record in snapshot_rows:
            period = record["fiscal_period"]
            if period in by_period:
                if float(by_period[period]["value"]) != float(record["value"]):
                    raise ValueError(f"Conflicting EPS after basis reconciliation: {source_hash} / {period}")
                exclusions["same_source_same_value_after_basis_alias"] += 1
                company_exclusions[company_id]["same_source_same_value_after_basis_alias"] += 1
                continue
            by_period[period] = record
        snapshot_rows = list(by_period.values())
        fiscal_values = sorted((r["fiscal_period"], float(r["value"])) for r in snapshot_rows)
        if len({period for period, value in fiscal_values}) != len(fiscal_values):
            raise ValueError(f"Duplicate EPS periods in source {source_hash} / {basis}")
        signature = (key, model_day or report_day, tuple(fiscal_values))
        if signature in signatures:
            exclusions["unchanged_model_reprint"] += len(snapshot_rows)
            company_exclusions[company_id]["unchanged_model_reprint"] += len(snapshot_rows)
            continue
        signatures.add(signature)
        snapshot_id = stable_id(series_id, source_hash, report_day, model_day, fiscal_values)
        available_day = date.fromisoformat(report_day) + timedelta(days=1)
        for row in snapshot_rows:
            observed_at = row.get("first_observed_at", "")
            if observed_at:
                captured = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
                if captured.tzinfo is None or captured.astimezone(timezone.utc).date().isoformat() != report_day or model_day:
                    raise ValueError('First-observed snapshot requires its actual UTC capture date and no invented model date')
            year = int(row["fiscal_period"][2:])
            end, calendar_basis = fiscal_end(company_id, year)
            prior_end, _ = fiscal_end(company_id, year - 1)
            note = "EPS retained exactly as printed; no share adjustment applied here. "
            note += "Original historical availability is unverified; use only on/after available_date. "
            if observed_at:
                note += "First-observed mutable public snapshot; numerical revision date unknown. Age limit measures time since capture. "
            elif model_day:
                note += "Estimate age starts at model_date; later report generation does not reset it. "
            else:
                note += "Separate model date absent; report_date is the assumed age origin. "
            note += row["notes"]
            panel.append({
                "observation_id": row["observation_id"], "company_id": company_id,
                "series_id": series_id, "analyst": analyst, "firm": firm, "metric": "eps", "series_type": series_type,
                "accounting_basis": basis, "currency": currency,
                "original_accounting_basis": row["accounting_basis"], "basis_alias_evidence": row["basis_alias_evidence"],
                "fiscal_period": row["fiscal_period"], "fiscal_period_end": end.isoformat(),
                "report_date": report_day, "available_date": available_day.isoformat(),
                "availability_basis": "first_observed_public_snapshot" if observed_at else "printed_report_date_assumption", "eps": row["value"],
                "first_observed_at": observed_at,
                **{k: availability.get(source_hash, {}).get(k, '') for k in ['verified_available_date', 'verified_available_at', 'availability_evidence_url', 'verification_kind']},
                "share_basis_date": row.get("share_basis_date") or model_day or report_day, "source_url": row["source_url"],
                "source_file": row["source_file"], "source_sha256": source_hash,
                "source_page": row["source_page"], "model_date": model_day,
                "snapshot_id": snapshot_id, "fiscal_period_start": (prior_end + timedelta(days=1)).isoformat(),
                "fiscal_calendar_basis": calendar_basis,
                "fiscal_calendar_source_url": CALENDAR_SOURCES[company_id],
                "source_metric": row["metric"], "notes": note,
            })
    panel.sort(key=lambda r: (r["company_id"], r["series_id"], r["available_date"], r["fiscal_period_end"]))
    grouped_series = defaultdict(list)
    for row in panel:
        grouped_series[row["series_id"]].append(row)
    series = []
    for series_id, rs in grouped_series.items():
        first = rs[0]
        dates = sorted({r["report_date"] for r in rs})
        basis = first["accounting_basis"]
        short_basis = {
            "reported_diluted": "Reported diluted EPS",
            "adjusted_diluted": "Adjusted diluted EPS",
            "morningstar_unadjusted_diluted": "Morningstar unadjusted diluted EPS, issuer denominator unproven",
            "guosen_latest_total_shares_eps": "Parent-profit EPS, latest total shares",
            "guosen_latest_total_shares_eps_numerator_not_crosschecked": "Cover EPS, latest total shares",
            "swsc_eps_definition_unresolved": "Southwest EPS, denominator unresolved",
            "sp_global_non_gaap_adjusted_eps_dilution_unspecified": "S&P adjusted EPS, dilution unspecified",
            "non_gaap_diluted": "Non-GAAP diluted EPS",
            "non_gaap_dilution_unspecified": "Non-GAAP EPS, dilution unspecified",
            "diluted_adjustment_basis_unresolved": "Diluted EPS, adjustment basis unresolved",
            "eps_basis_unresolved": "EPS, adjustment and dilution unresolved",
            "iex_eps_adjustment_and_dilution_unspecified": "EPS, adjustment and dilution unspecified",
            "lseg_consensus_eps_adjustment_and_dilution_unspecified": "LSEG EPS, basis unspecified",
            "bloomberg_consensus_eps_adjustment_and_dilution_unspecified": "Bloomberg EPS, basis unspecified",
            "Consolidated broker estimate; EPS definition retained as printed, not normalized to statutory diluted EPS": "Consolidated broker EPS",
            "Hana Financial Data forecast table; EPS definition not normalized": "Financial Data EPS",
            "EPS labelled parent-attributable; basic/diluted and share denominator not established": "Parent-attributable EPS",
            "Consolidated K-IFRS EPS as printed; basic/diluted/share denominator unresolved": "Consolidated K-IFRS EPS",
            "KB consolidated forecast table; EPS appears beneath parent-attributable net income, denominator unresolved": "Consolidated parent-profit model EPS",
            "Hana Financial Data forecast table; consolidated company revenue; EPS definition retained as printed, not normalized": "Company Financial Data EPS",
            "Consolidated K-IFRS annual summary as printed; EPS denominator unresolved": "K-IFRS annual-summary EPS",
            "Meritz consolidated company model; EPS explicitly parent-attributable; detailed financial table uses KRW billion": "Detailed parent-profit model EPS",
            "Bloomberg-adjusted EPS; basic/diluted denominator unspecified": "Bloomberg adjusted EPS, dilution unspecified",
            "Bloomberg consensus EPS; adjustment and dilution unspecified": "Bloomberg EPS, basis unspecified",
            "Zacks consensus EPS; adjustment and dilution unspecified": "Zacks EPS, basis unspecified",
            "Bloomberg_EPS_adjustment_unstated": "Bloomberg EPS, basis unspecified",
        }.get(basis, "Broker EPS as printed")
        comparability_note = ""
        comparability_source_url = ""
        if first["company_id"] == "asml" and basis == "morningstar_unadjusted_diluted":
            comparability_note = "These Morningstar plain diluted EPS models use historical share denominators that do not consistently match ASML's annual reported diluted shares. Kept as a broker-specific valuation series; excluded from issuer-reported accuracy scoring and cross-author ensembles."
            comparability_source_url = "https://invest.firstrade.com/ms/equity_reports/sr/2025/0P0000002X_20250403_RT.pdf"
        if first["company_id"] == "nvidia" and basis in {"adjusted_diluted", "diluted_adjustment_basis_unresolved"}:
            comparability_note = "NVIDIA began including stock-based compensation in its non-GAAP measures in FY2027. These analyst tables do not establish whether every model uses that definition; multiples across the change may not be comparable."
            comparability_source_url = "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/"
        series.append({
            "series_id": series_id, "company_id": first["company_id"],
            "label": (f"{first['firm']} · Published consensus · {short_basis}" if not first["analyst"] else f"{first['analyst']} · {first['firm']} · {short_basis}"),
            "series_type": first["series_type"],
            "analyst": first["analyst"], "firm": first["firm"], "accounting_basis": basis,
            "currency": first["currency"],
            "comparability_note": comparability_note, "comparability_source_url": comparability_source_url,
            "coverage_note": f"{len(dates)} retained report dates, {dates[0]} to {dates[-1]}; sparse dated-report reconstruction, not verified point-in-time history. EPS basis: {basis}. Ensemble eligibility requires a compatible definition; no analyst accuracy rank assigned.",
        })
    gaps = {
        "as_of": as_of.isoformat(),
        "input_observations": len(rows), "eligible_eps_observations": len(panel),
        "retained_series": len(series), "exclusions": dict(exclusions),
        "availability_verified": False,
        "status": "public_report_reconstruction_incomplete",
        "companies": [],
        "subscription_needed_for": "Complete dated FY1/FY2 or NTM EPS histories and revisions for 2021-09-10 through 2026-09-10, with point-in-time availability, analyst/broker identifiers, comparable accounting basis, fiscal periods and share adjustments. Historical consensus is a separate series and must not be substituted for an analyst.",
        "provider_documentation": [
            "https://insight.factset.com/resources/factset-consensus-estimates-datafeed",
            "https://www.insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf",
            "https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/lseg-data-for-quant-research-brochure.pdf",
        ],
        "scrapingbee_status": "Not used. Retrieved sources do not establish that proxy credits would supply missing historical access or subscription entitlements.",
    }
    for company_id in COMPANIES:
        rs = [r for r in panel if r["company_id"] == company_id]
        dates = sorted({r["report_date"] for r in rs})
        gaps["companies"].append({
            "company_id": company_id, "eps_observations": len(rs),
            "series_count": len({r["series_id"] for r in rs}), "report_dates": dates,
            "first_report_date": dates[0] if dates else None,
            "latest_report_date": dates[-1] if dates else None,
            "status": "sparse_reports_only" if rs else "no_eligible_earnings_series",
            "excluded_eps": dict(company_exclusions[company_id]),
            "needed": "Dated original analyst or published consensus EPS models with consecutive forward fiscal years, explicit accounting/share basis and verified publication history; all revisions needed for continuous coverage.",
        })
    return panel, series, gaps


def write_csv(path: Path, rows: list[dict[str, str]], fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=AS_OF.isoformat())
    args = parser.parse_args()
    with (ROOT / "data/collected_forecasts.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    panel, series, gaps = build_panel(rows, as_of=date.fromisoformat(args.as_of))
    output = ROOT / "data/market"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "forecast_panel.csv", panel, PANEL_FIELDS)
    write_csv(output / "forecast_series.csv", series, SERIES_FIELDS)
    (output / "forecast_gaps.json").write_text(json.dumps(gaps, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"eps_observations": len(panel), "series": len(series), "exclusions": gaps["exclusions"]}))


if __name__ == "__main__":
    main()
