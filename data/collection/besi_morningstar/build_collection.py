"""Materialize the manually verified, source-scoped BESI collection."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "data/collection/besi_morningstar"
NOW = datetime.now(timezone.utc).isoformat()
OBS_FIELDS = "observation_id,company_id,firm,analyst_name,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256,source_value,source_unit".split(",")
MAN_FIELDS = "source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type".split(",")

def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def write_csv(name, fields, rows):
    with (BASE / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

evidence = {
    "source_url": "https://global.morningstar.com/en-gb/stocks/besi-earnings-quiet-quarter-loud-outlook-order-book-ramping-up",
    "title": "Besi Earnings: Quiet Quarter, but Loud Outlook; Order Book Ramping Up",
    "publisher": "Morningstar",
    "author": "Javier Correonero",
    "printed_publication_date": "2025-07-24",
    "retrieved_at": NOW,
    "artifact_type": "primary_publisher_excerpt_from_browser_search_rendering",
    "is_original_html_or_pdf": False,
    "retrieval_method": "web search result returned the publisher article text, including its byline, date and explicit forecast sentence; direct requests returned HTTP403 for both en-eu and en-gb variants",
    "exact_forecast_excerpt": "EPS more than doubling to EUR 5.5 in 2028 if our forecasts materialize.",
    "source_locator": "The bottom line; first bullet; explicit EPS forecast, not derived from P/E",
    "limitations": "Numerical model date, basic/diluted status, adjustment basis and original availability timestamp are not established. This retained evidence is an excerpt of the publisher's article, not a retained original document."
}
epath = "data/collection/besi_morningstar/discovery/besi_note_20250724_publisher_excerpt.json"
(ROOT / epath).write_text(json.dumps(evidence, indent=2) + "\n")

source_log = json.loads((BASE / "source_log.json").read_text())
sources = {row["local_file"].rsplit("/", 1)[-1]: row for row in source_log if row.get("local_file")}
table = sources["besi_20240504.pdf"]
peer = sources["asml_peer_besi_20240805.pdf"]
manifests = []
for source, date, timestamp, model, status, note in [
    (table, "2024-05-04", "2024-05-04T04:17:00+00:00", "2024-04-25", "verified_original_publisher_pdf_on_third_party_mirror", "Intact 21-page Morningstar report, third-party Eurobench forum mirror, not an official distributor. Amsterdam BESI identity, dates, author and model table visually checked. Attachment post is dated May7,2024. The original publication/availability time is unverified."),
    (peer, "2024-08-05", "2024-08-05T13:30:00+00:00", "", "verified_original_distributor_pdf_peer_forecast", "24-page ASML report contains an explicitly attributed BESI FY2025 EPS forecast in the same-day Javier Correonero note, physical page1. Only that BESI value is extracted; ASML's model date is not assigned to BESI.")
]:
    manifests.append(dict(source_url=source["source_url"], local_file=source["local_file"], company_ids="besi", firm="Morningstar", analyst_name="Javier Correonero", report_date=date, retrieved_at=source["retrieved_at"], sha256=source["sha256"], status=status, notes=note, text_file=source["text_file"], report_timestamp=timestamp, model_dates=model, http_status=200, report_month=date[:7], report_date_precision="day", artifact_type="pdf"))
manifests.append(dict(source_url=evidence["source_url"], local_file=epath, company_ids="besi", firm="Morningstar", analyst_name="Javier Correonero", report_date="2025-07-24", retrieved_at=NOW, sha256=digest(epath), status="verified_publisher_excerpt_original_document_not_retained", notes=evidence["limitations"], text_file="", report_timestamp="", model_dates="", http_status="", report_month="2025-07", report_date_precision="day", artifact_type=evidence["artifact_type"]))
for item in json.loads((BASE / "discovery_manifest.json").read_text()):
    manifests.append(dict(source_url=item["source_url"], local_file=item["local_file"], company_ids="besi", firm="Morningstar", analyst_name="", report_date="", retrieved_at=item["retrieved_at"], sha256=item["sha256"], status=item["status"], notes="Security identity discovery only; never forecast evidence.", text_file="", report_timestamp="", model_dates="", http_status=item["http_status"], report_month="", report_date_precision="", artifact_type="html_discovery"))

rows = []
def observation(source, metric, fiscal, value, basis, model_date, report_date, timestamp, page, notes, raw_value=None, raw_unit=None, status="extracted_table_pending_basis_match"):
    row = dict.fromkeys(OBS_FIELDS, "")
    unit = "EUR_million" if metric == "revenue" else "EUR_per_share"
    key = "|".join([source["sha256"], metric, str(fiscal), str(value), basis])
    row.update(observation_id=hashlib.sha256(key.encode()).hexdigest()[:24], company_id="besi", firm="Morningstar", analyst_name="Javier Correonero", metric=metric, fiscal_period=f"FY{fiscal}", value=str(value), currency="EUR", unit=unit, basis=basis, model_date=model_date, forecast_revision_as_of=model_date, report_date=report_date, printed_report_timestamp=timestamp, availability_basis="printed_report_date_not_independently_verified", source_url=source["source_url"], local_file=source["local_file"], page=page, status=status, notes=notes, source_period_label=str(fiscal), share_basis_date=model_date or report_date, source_artifact_sha256=source["sha256"], source_value=str(value if raw_value is None else raw_value), source_unit=unit if raw_unit is None else raw_unit)
    rows.append(row)

common = "Amsterdam ordinary BESI shares, EUR, annual December31 fiscal years; retained as printed without split adjustment. The issuer's last identified split was May4,2018, before this model. Physical page13 distinguishes historical FY2022/23 from estimated FY2024/25/26. Printed report date is May4,2024 and numerical model date is April25,2024; original availability remains unverified. Source is a Morningstar-authored original on a third-party forum mirror, not an official distributor. "
for fiscal, eps, revenue in [(2024, "2.86", 760865), (2025, "4.18", 1036990), (2026, "5.18", 1336402)]:
    observation(table, "eps_diluted", fiscal, eps, "diluted_adjustment_basis_unresolved", "2024-04-25", "2024-05-04", "2024-05-04T04:17:00+00:00", 13, common + "Printed row: Diluted Earnings Per Share(EUR). No GAAP/IFRS/reported/adjusted equivalence is established; the model's historical EPS differs from the upper historical-summary table.")
    observation(table, "revenue", fiscal, f"{revenue / 1000:.3f}", "total_revenue", "2024-04-25", "2024-05-04", "2024-05-04T04:17:00+00:00", 13, common + f"Printed Revenue (EUR K): {revenue:,}; converted arithmetically to EUR million by dividing by1000 for schema compatibility. source_value/source_unit preserve the printed amount/unit.", revenue, "EUR_thousand")
observation(peer, "eps", 2025, "3.90", "eps_basis_unresolved", "", "2024-08-05", "2024-08-05T13:30:00+00:00", 1, "Javier Correonero's same-day note explicitly prints BESI 2025 EUR3.90 EPS. The value is not reverse-engineered from the adjacent P/E multiple. The report concerns ASML, but this sentence explicitly concerns BESI; ASML numerical model dates and accounting labels do not define BESI's EPS. Basic/diluted and adjustment basis are unresolved. Amsterdam ordinary EUR per-share basis retained; no split transformation. Single annual target only, insufficient on its own for NTM interpolation. Original publication availability unverified.", status="verified_original_peer_note_eps_basis_unresolved")
note_source = dict(source_url=evidence["source_url"], local_file=epath, sha256=digest(epath))
observation(note_source, "eps", 2028, "5.5", "eps_basis_unresolved", "", "2025-07-24", "", "HTML: The bottom line, first bullet", "Explicit Morningstar/Javier Correonero FY2028 EPS EUR5.5 in the July24,2025 publisher article. Evidence retained as a short publisher excerpt from browser search rendering; original HTML/PDF was not retained because direct requests returned403. This is not an original-document artifact. Basic/diluted and adjustment basis, numerical model date and original availability remain unverified. No P/E inference. Single distant annual target is insufficient for NTM interpolation; do not stitch into the legacy diluted series. Amsterdam ordinary EUR per-share basis retained; no split transformation.", status="verified_publisher_excerpt_eps_basis_unresolved")
write_csv("manifest.csv", MAN_FIELDS, manifests)
write_csv("observations.csv", OBS_FIELDS, rows)
assert len(rows) == 8
assert len({r["observation_id"] for r in rows}) == 8
for row in rows:
    assert row["source_artifact_sha256"] == digest(row["local_file"])
    assert row["report_date"] <= "2026-09-10"
    assert not row["available_at"] and not row["original_available_at"]
print(json.dumps({"observations":len(rows), "eps":sum(r["metric"].startswith("eps") for r in rows), "revenue":sum(r["metric"]=="revenue" for r in rows), "manifest_rows":len(manifests)}, indent=2))
