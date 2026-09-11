#!/usr/bin/env python3
"""Rebuild reviewed BESI observations from immutable retained originals.

Default is offline. --fetch captures fresh copies in a new UTC-stamped directory;
it never overwrites reviewed originals or assigns a historical date to new data.
Dependencies: beautifulsoup4, requests (fetch only), pdftotext (PDF evidence).
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
LOGS = ["initial_routes.json", "sitemap_route.json", "download_log1.json",
        "discovery_log2.json", "magazine_download.json", "current_snapshot_log.json",
        "current_snapshot_log2.json", "twelvedata_docs_log.json"]
MANIFEST_FIELDS = "source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type".split(",")
OBS_FIELDS = "observation_id,company_id,firm,analyst_name,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,forecast_type,source_type,source_period_label,share_basis_date,source_artifact_sha256".split(",")
CLEAN = "extracted_original_table_unscored"
QUARANTINE = "quarantined_forecast_attribution_unresolved"
CURRENT_NOTE = (
    "Mutable public page captured at the recorded UTC retrieval time. This is a first-observed "
    "snapshot, not a dated model revision. Earlier numerical revision and original publication "
    "times are unknown. report_date records observation date only; model_date and "
    "forecast_revision_as_of are intentionally blank. No availability before capture; the "
    "current daily pipeline conservatively makes these annual rows available on 2026-09-11. "
    "Do not interpret capture date as evidence that the underlying model was updated that day. "
)
MAGAZINE_NOTE = (
    "Publisher-hosted magazine, cover dated 25 October 2024. Physical PDF page 33, printed "
    "pages 64-65, BESI row under EUR annual revenue and EPS. Asterisks mean expected. "
    "Physical page 37 defines EPS generically as net income divided by average shares "
    "outstanding during the year; basic/diluted and reported/adjusted are not specified. "
    "Colophon credits Refinitiv, Infront, Bloomberg and IEX collectively for statistics, "
    "without identifying the provider or forecast author of this table. Not attributed to "
    "Hildo Laman or treated as verified consensus. Quarantined pending table-specific attribution."
)


def sources():
    result = []
    for filename in LOGS:
        rows = json.loads((BASE / filename).read_text())
        for raw in rows if isinstance(rows, list) else [rows]:
            local = raw.get("local_file", raw.get("file"))
            source = dict(raw, local_file=local,
                          source_url=raw.get("source_url", raw.get("url")),
                          http_status=raw.get("http_status", raw.get("status")))
            source["key"] = raw.get("key", Path(local).stem)
            actual_hash = hashlib.sha256((ROOT / local).read_bytes()).hexdigest()
            assert actual_hash == raw["sha256"], f"Changed original: {local}"
            result.append(source)
    return result


def tables(source):
    soup = BeautifulSoup((ROOT / source["local_file"]).read_text(), "html.parser")
    return soup, [[[cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
                   for row in table.find_all("tr")] for table in soup.find_all("table")]


def write_csv(filename, fields, rows):
    with (BASE / filename).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def extract(records):
    by_key = {row["key"]: row for row in records}
    observations = []
    meta = {}
    evidence = {}

    def add(key, firm, metric, year, value, basis, page, label, notes, quarantine=False):
        source = by_key[key]
        observed = not quarantine
        report_date = source["retrieved_at"][:10] if observed else "2024-10-25"
        identity = "|".join([source["sha256"], "besi", metric, str(year), basis, str(value)])
        row = {field: "" for field in OBS_FIELDS}
        row.update(observation_id=hashlib.sha256(identity.encode()).hexdigest()[:24],
                   company_id="besi", firm=firm, metric=metric, fiscal_period=f"FY{year}",
                   value=value, currency="EUR", unit="EUR_per_share" if metric == "eps" else "EUR_billion",
                   basis=basis, report_date=report_date,
                   available_at=source["retrieved_at"] if observed else "",
                   availability_basis="first_observed_public_page_at_retrieval_original_release_time_unknown" if observed else "printed_magazine_cover_date_original_dissemination_time_unknown",
                   source_url=source["source_url"], local_file=source["local_file"], page=page,
                   status=QUARANTINE if quarantine else CLEAN, notes=notes,
                   forecast_type="publisher_forecast_unattributed" if quarantine else "published_consensus",
                   source_type="publisher_forecast_unattributed" if quarantine else "published_consensus",
                   source_period_label=label, source_artifact_sha256=source["sha256"])
        observations.append(row)
        meta[key] = dict(firm=firm, report_date=report_date, status=row["status"], notes=notes)

    key = "twelvedata_20260910"
    soup, matrix = tables(by_key[key])
    assert "EUR" in soup.get_text(" ", strip=True)
    assert matrix[0][0][3:] == ["Current year (Dec 2026)", "Next year (Dec 2027)"]
    assert matrix[0][2][3:] == ["4.38", "6.50"]
    assert matrix[1][2][3:] == ["1.00B", "1.35B"]
    notes = CURRENT_NOTE + (
        "Provider's BESI Euronext EUR page: annual mean EPS estimates from 21 analysts for "
        "2026 and 23 for 2027. EPS adjustment and dilution unspecified. No equivalence to IEX, "
        "Morningstar or S&P adjusted EPS established. Revenue is rounded to displayed billions. "
        "Relative 7/30/60/90-day trend columns lack an independently verified date anchor and "
        "are excluded from historical observations. Financial currency follows the EUR listing "
        "page; Twelve Data does not print a separate financial-currency footnote."
    )
    for offset, year in enumerate([2026, 2027], 3):
        add(key, "Twelve Data", "eps", year, matrix[0][2][offset],
            "twelve_data_consensus_eps_adjustment_and_dilution_unspecified", "HTML table 1", matrix[0][0][offset], notes)
        add(key, "Twelve Data", "revenue", year, matrix[1][2][offset][:-1],
            "twelve_data_consensus_revenue", "HTML table 2", matrix[1][0][offset], notes)
    evidence[key] = dict(retrieved_at=by_key[key]["retrieved_at"], sha256=by_key[key]["sha256"],
                         earnings_table=matrix[0], revenue_table=matrix[1],
                         excluded_relative_trend_table=matrix[2],
                         exclusion_reason="No verified exact historical anchor; never subtract relative offsets from retrieval date.")

    key = "stockanalysis_20260910"
    soup, matrix = tables(by_key[key])
    body = soup.get_text(" ", strip=True)
    assert "EPS and Forward PE are based on non-GAAP adjusted numbers." in body
    assert "Financial currency is EUR." in body
    assert "Price targets, consensus ratings and financial forecasts are provided by S&P Global Market Intelligence" in body
    annual = next(table for table in matrix if table[0][0] == "Fiscal Year")
    column = annual[0].index("FY 2026")
    values = {row[0]: row[column] for row in annual[1:]}
    assert values["EPS"] == "4.38" and values["Revenue"] == "1.00B"
    assert annual[0][column + 1:] == ["FY 2027", "FY 2028"]
    notes = CURRENT_NOTE + (
        "Page explicitly labels financial currency EUR and EPS non-GAAP adjusted, but does "
        "not identify basic/diluted denominator or the adjustment policy. Financial forecasts "
        "are supplied by S&P Global Market Intelligence; TipRanks individual ratings are not "
        "these forecasts. The August 4 footer date does not establish the current financial "
        "table's original model date. Only FY2026 is public; FY2027/28 require Pro. "
        "Matching one EPS value to Twelve Data does not establish independent data or basis equivalence."
    )
    add(key, "Stock Analysis (S&P Global consensus)", "eps", 2026, values["EPS"],
        "sp_global_non_gaap_adjusted_eps_dilution_unspecified", "HTML table 4", "FY 2026 / Dec 31, 2026", notes)
    add(key, "Stock Analysis (S&P Global consensus)", "revenue", 2026, values["Revenue"][:-1],
        "sp_global_consensus_revenue", "HTML table 4", "FY 2026 / Dec 31, 2026", notes)
    evidence[key] = dict(retrieved_at=by_key[key]["retrieved_at"], sha256=by_key[key]["sha256"],
                         annual_table=annual, model_revision_time="unknown", page_footer_date="2026-08-04",
                         financial_currency="EUR", eps_basis="non-GAAP adjusted; dilution unspecified")

    key = "iex_magazine_2024_39"
    pdf = ROOT / by_key[key]["local_file"]
    pdf_text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    pages = pdf_text.split("\f")
    assert re.search(r"2024\s+25\s+oktober", pages[0], re.I)
    besi = next(line for line in pages[32].splitlines() if re.match(r"BESI\s", line))
    nums = besi.split()
    # Columns: company, price, market cap, EV, YTD, week, high, low,
    # revenue FY22..26, MC/revenue, EBITDA, EV/EBITDA, EPS FY22..26.
    assert nums[10:13] == ["0,64", "0,91", "1,20"]
    assert nums[18:21] == ["2,38", "3,89", "5,55"]
    assert "Refinitiv" in pdf_text and "Infront" in pdf_text and "Bloomberg" in pdf_text
    for year, revenue, eps in zip([2024, 2025, 2026], nums[10:13], nums[18:21]):
        for metric, value in [("revenue", revenue), ("eps", eps)]:
            add(key, "IEX", metric, year, value.replace(",", "."),
                "publisher_eps_forecast_attribution_unresolved" if metric == "eps" else "publisher_revenue_forecast_attribution_unresolved",
                "33 (printed 64-65); definitions 37 (printed 72-73)", f"{year}*", MAGAZINE_NOTE, True)
    evidence[key] = dict(sha256=by_key[key]["sha256"], report_date="2024-10-25", besi_table_row=besi,
                         physical_page=33, definition_physical_page=37, forecast_attribution="unresolved",
                         visual_review=["evidence/iex_magazine_2024_39_p33.png", "evidence/iex_magazine_2024_39_p37.png"])

    manifest = []
    for source in records:
        key = source["key"]
        row = {field: "" for field in MANIFEST_FIELDS}
        row.update({field: source.get(field, "") for field in MANIFEST_FIELDS})
        row.update(company_ids="besi", status="discovery_no_forecast_observations",
                   artifact_type="pdf" if source["local_file"].endswith(".pdf") else "html",
                   notes="Retained discovery/access evidence; not used as a numerical forecast source.")
        row.update(meta.get(key, {}))
        if key.startswith("iex_2026") or key.startswith("stockwatch_2026"):
            soup = BeautifulSoup((ROOT / source["local_file"]).read_text(), "html.parser")
            for element in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(element.get_text())
                except json.JSONDecodeError:
                    continue
                entities = data.get("@graph", [data]) if isinstance(data, dict) else data
                article = next((item for item in entities if "datePublished" in item), None)
                if article:
                    row["report_timestamp"] = article["datePublished"]
                    row["report_date"] = article["datePublished"][:10]
                    break
            row.update(firm="IEX" if key.startswith("iex") else "StockWatch",
                       analyst_name="Hildo Laman" if key.startswith("iex") else "Paul Weeteling",
                       status="subscription_excerpt_no_annual_eps_table",
                       notes="Original dated research identified, but public excerpt does not disclose annual EPS forecasts. Requires publisher subscription for full article; this is not a JavaScript rendering failure.")
        elif key in {"saxo_20260723", "saxo_20250613"}:
            row.update(firm="Saxo", report_date="2026-07-23" if key.endswith("20260723") else "2025-06-13",
                       status="public_article_no_annual_eps_forecast_table",
                       notes="Public full article contains results/strategic outlook and/or rating, without consecutive annual EPS forecasts. For June 2025 the visible original date takes precedence over February 2026 CMS metadata.")
        elif key.startswith("marketscreener"):
            row.update(firm="MarketScreener", status="http_403_access_denied",
                       notes="Direct original-page retrieval returned HTTP 403. No numerical extraction from this retained artifact; cached search/browser values are not backdated or promoted.")
        elif key.startswith("chartmill"):
            row.update(firm="Chartmill", status="javascript_shell_no_forecast_table",
                       notes="HTTP 200 returns a JavaScript application shell only. No verified public annual table or values. Rendering is a possible retrieval lead, not proof of data availability or a subscription requirement.")
        elif key.startswith("finvaulta"):
            row.update(firm="Finvaulta", status="secondary_summary_no_original_annual_eps_model",
                       notes="Secondary Goldman Sachs summary includes a price target, no original linked annual EPS model. Not an original broker source.")
        if row["report_date"]:
            row.update(report_month=row["report_date"][:7], report_date_precision="day")
        if key == "iex_magazine_2024_39":
            row["text_file"] = str((BASE / "text/iex_magazine_2024_39.txt").relative_to(ROOT))
        manifest.append(row)
    write_csv("manifest.csv", MANIFEST_FIELDS, manifest)
    write_csv("observations.csv", OBS_FIELDS, observations)
    (BASE / "evidence/extraction.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"manifest_sources": len(manifest), "observations": len(observations),
                      "clean": sum(row["status"] == CLEAN for row in observations),
                      "quarantined": sum(row["status"] == QUARANTINE for row in observations),
                      "first_eligible_daily_date_current_snapshots": "2026-09-11"}))


def fetch(records):
    import requests
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = BASE / "retrievals" / stamp
    target.mkdir(parents=True, exist_ok=False)
    log = []
    for source in records:
        try:
            response = requests.get(source["source_url"], timeout=35)
            now = datetime.now(timezone.utc).isoformat()
            suffix = Path(source["local_file"]).suffix
            path = target / (source["key"] + suffix)
            path.write_bytes(response.content)
            log.append(dict(key=source["key"], source_url=source["source_url"],
                            local_file=str(path.relative_to(ROOT)), retrieved_at=now,
                            http_status=response.status_code,
                            sha256=hashlib.sha256(response.content).hexdigest()))
        except requests.RequestException as error:
            log.append(dict(key=source["key"], source_url=source["source_url"], error=str(error)))
    (target / "download_log.json").write_text(json.dumps(log, indent=2) + "\n")
    print(f"Fresh artifacts retained at {target}; manual review required before new observations.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    reviewed = sources()
    fetch(reviewed) if args.fetch else extract(reviewed)
