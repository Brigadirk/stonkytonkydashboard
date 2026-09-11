#!/usr/bin/env python3
"""Export reviewed issuer outcomes; preserve the distinction between result versions."""
import csv
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SAMSUNG = {
    2021: ("279,604,799", "5,777", "5,777", "2022-01-27"),
    2022: ("302,231,360", "8,057", "8,057", "2023-01-31"),
    2023: ("258,935,494", "2,131", "2,131", "2024-01-31"),
    2024: ("300,870,903", "4,950", "4,950", "2025-01-31"),
    2025: ("333,605,938", "6,605", "6,603", "2026-01-29"),
}
HYNIX = {
    2021: ("42.998", "2022-01-28", "https://news.skhynix.com/en/sk-hynix-inc-reports-fiscal-year-2021-and-fourth-quarter-results/"),
    2022: ("44.648", "2023-02-01", "https://news.skhynix.com/en/sk-hynix-reports-2022-and-fourth-quarter-financial-results/"),
    2023: ("32.7657", "2024-01-25", "https://news.skhynix.com/cn/sk-hynix-reports-fourth-quarter-2023-financial-results/"),
    2024: ("66.1930", "2025-01-23", "https://news.skhynix.com/en/sk-hynix-announces-4q24-financial-results/"),
    2025: ("97.1467", "2026-01-28", "https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/"),
}


def source_for(db, url):
    row = db.execute("SELECT * FROM downloads WHERE source_url=? AND status='downloaded' ORDER BY id DESC LIMIT 1", (url,)).fetchone()
    if not row:
        raise ValueError(f"Missing retained issuer source: {url}")
    if hashlib.sha256((ROOT / row["local_file"]).read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError("Issuer source checksum mismatch")
    return row


def outcome(company, year, metric, value, event_date, release_url, source, page, version, notes):
    return dict(outcome_id=f"{company}_FY{year}_{metric}_{version}", company_id=company, fiscal_period=f"FY{year}", fiscal_period_end=f"{year}-12-31",
                metric=metric, value=str(value), unit="KRW" if metric == "revenue" else "KRW_per_share", currency="KRW",
                earnings_release_date=event_date, release_date_source_url=release_url, actual_available_at="",
                source_url=source["source_url"], source_file=source["local_file"], source_sha256=source["sha256"], source_page=page,
                result_version=version, validation_status="issuer_value_checked_comparability_pending", notes=notes)


def main():
    db = sqlite3.connect(ROOT / "data/archive.sqlite")
    db.row_factory = sqlite3.Row
    rows = []
    for year, (revenue, basic, diluted, event_date) in SAMSUNG.items():
        url = f"https://images.samsung.com/is/content/samsung/assets/global/ir/docs/{year}_con_quarter04_all.pdf"
        source = source_for(db, url)
        page = (ROOT / source["text_file"]).read_text().split("\f")[8]
        assert "CONSOLIDATED STATEMENTS OF PROFIT OR LOSS" in page and "In millions of Korean won" in page
        for value in (revenue, basic, diluted):
            assert value in page, (url, value)
        release_url = f"https://news.samsung.com/global/samsung-electronics-announces-fourth-quarter-and-fy-{year}-results"
        for metric, value in [("revenue", Decimal(revenue.replace(",", "")) * 1000000), ("eps_basic", basic.replace(",", "")), ("eps_diluted", diluted.replace(",", ""))]:
            rows.append(outcome("samsung_electronics", year, metric, value, event_date, release_url, source, "9", "audited_annual_statement",
                                "Audited consolidated K-IFRS value. Earnings date is the issuer's detailed-results release, verified on its newsroom page. The audited statement may have been issued later; no claim this exact value was available on the earnings date. EPS is not yet comparable to broker EPS."))
    for year, (revenue, event_date, url) in HYNIX.items():
        source = source_for(db, url)
        assert revenue in (ROOT / source["local_file"]).read_text(), (year, revenue)
        rows.append(outcome("sk_hynix", year, "revenue", Decimal(revenue) * 1000000000000, event_date, url, source, "HTML annual-results paragraph", "initial_earnings_release",
                            "Consolidated annual revenue in original press-release precision. Date follows the Seoul dateline; some page headers show the preceding UTC date. Keep separate from subsequent audited revisions. Acquisition-scope comparability with each forecast remains to be reviewed."))
    with (ROOT / "data/issuer_outcomes.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} issuer outcome records: 10 annual revenues and 10 Samsung basic/diluted EPS values.")


if __name__ == "__main__":
    main()
