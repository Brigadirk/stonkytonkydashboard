#!/usr/bin/env python3
"""Offline extraction of reviewed IEX BESI table; writes only this collection."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
MANIFEST_FIELDS = "source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type".split(",")
OBS_FIELDS = "observation_id,company_id,firm,analyst_name,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,forecast_type,source_type,source_period_label,share_basis_date,source_artifact_sha256".split(",")
source = json.loads((BASE / "download_log.json").read_text())[0]
pdf = ROOT / source["local_file"]
assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source["sha256"]
assert source["sha256"] == "be953fdcb9ca93a842f0d28f190d6b3e896feea85871be03c949be5ecba4e927"
content = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
pages = content.split("\f")
assert "27 FEBRUARI 2026" in pages[0]
page = pages[14]
for required in ["Door Hildo Laman", "KERNGEGEVENS (IN €)", "20-02-26", "* = taxatie IEX", "2025*", "2026*", "2027*"]:
    assert required in page, required
assert re.search(r"Winst p/a\s+1,66\s+4,16\s+5,78", page)
assert re.search(r"Omzet \(mln\)\s+591\s+860\s+1\.153", page)
notes = (
    "Original IEX Expert issue 04/2026, cover dated 27 February 2026; public intact PDF "
    "distributed on KPN's Q4 CDN. Physical/printed page 15, Nieuwe fase, explicitly by Hildo "
    "Laman. Annual table says KERNGEGEVENS (IN EUR) and '* = taxatie IEX'. Named IEX model, "
    "not the issue's separate broad-market statistics or consensus. EPS adjustment and "
    "basic/diluted denominator are unspecified; retain the existing unresolved IEX basis "
    "without aliasing to issuer actuals or another analyst. The 20-02-26 date is printed next "
    "to the stock quote and is not treated as a model revision timestamp. report_date is the "
    "magazine's printed cover date; model_date and forecast_revision_as_of remain blank. "
    "No independent historical dissemination timestamp is verified. The separately identified "
    "19 February online article has no public table, so no numerical availability is backdated "
    "to that page. FY2025 is still marked with an asterisk but EUR1.66 EPS and EUR591m revenue "
    "are completed annual actuals already released; both are excluded from forecasts. "
    "FY2027 revenue is displayed as 1.153 in Dutch thousands notation, meaning EUR1153m."
)

rows = []
for year, eps, revenue in [(2026, "4.16", "860"), (2027, "5.78", "1153")]:
    for metric, value, unit, basis in [
        ("eps", eps, "EUR_per_share", "iex_eps_adjustment_and_dilution_unspecified"),
        ("revenue", revenue, "EUR_million", "company_revenue"),
    ]:
        row = {field: "" for field in OBS_FIELDS}
        key = "|".join([source["sha256"], "besi", metric, str(year), value])
        row.update(observation_id=hashlib.sha256(key.encode()).hexdigest()[:24],
                   company_id="besi", firm="IEX", analyst_name="Hildo Laman", metric=metric,
                   fiscal_period=f"FY{year}", value=value, currency="EUR", unit=unit, basis=basis,
                   report_date="2026-02-27", availability_basis="printed_magazine_cover_date_original_dissemination_time_unknown",
                   source_url=source["source_url"], local_file=source["local_file"], page="15",
                   status="extracted_original_table_unscored", notes=notes,
                   forecast_type="analyst_forecast", source_type="individual_analyst_forecast",
                   source_period_label=f"{year}*", source_artifact_sha256=source["sha256"])
        rows.append(row)

manifest = [{field: "" for field in MANIFEST_FIELDS}]
manifest[0].update({field: source.get(field, "") for field in MANIFEST_FIELDS})
manifest[0].update(company_ids="besi", firm="IEX", analyst_name="Hildo Laman", report_date="2026-02-27",
                   status="extracted_original_table_unscored", notes=notes,
                   text_file=str((BASE / "text/IEX04_2026_compressed.txt").relative_to(ROOT)),
                   report_month="2026-02", report_date_precision="day", artifact_type="pdf")
hosting = json.loads((BASE / "hosting_provenance.json").read_text())
home = ROOT / hosting["local_file"]
assert hashlib.sha256(home.read_bytes()).hexdigest() == hosting["sha256"]
assert "s202.q4cdn.com/886546970/files/js/" in home.read_text()
host_row = {field: hosting.get(field, "") for field in MANIFEST_FIELDS}
host_row.update(company_ids="besi", firm="KPN", status="hosting_provenance_only",
                text_file=str((BASE / "text/kpn_ir_home.txt").relative_to(ROOT)), artifact_type="html",
                notes="Official KPN investor-relations page loads JavaScript from s202.q4cdn.com/886546970, independently establishing the CDN account owner. Does not establish original magazine posting time or numerical model date.")
manifest.append(host_row)
for filename, fields, values in [("observations.csv", OBS_FIELDS, rows), ("manifest.csv", MANIFEST_FIELDS, manifest)]:
    with (BASE / filename).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)
evidence = dict(source_sha256=source["sha256"], report_date="2026-02-27", physical_page=15,
                analyst="Hildo Laman", firm="IEX", source_currency="EUR",
                table_attribution="* = taxatie IEX", eps={"FY2026": "4.16", "FY2027": "5.78"},
                revenue_eur_million={"FY2026": "860", "FY2027": "1153"},
                quote_card_date="2026-02-20", quote_card_date_is_model_date=False,
                excluded_actuals={"FY2025_EPS": "1.66", "FY2025_revenue_EUR_million": "591"},
                model_date=None, original_dissemination_timestamp=None,
                compatible_basis_alias_recommendation=None,
                visual_review="evidence/IEX04_2026_p15.png")
(BASE / "evidence/extraction.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"sources": len(manifest), "observations": len(rows), "annual_eps_forecasts": 2,
                  "report_date": "2026-02-27", "model_revision_date": None}))
