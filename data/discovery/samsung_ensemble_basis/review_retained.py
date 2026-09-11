#!/usr/bin/env python3
"""Validate retained Samsung originals and reproduce diagnostic ratios, offline.

These ratios are not an extraction of defined EPS denominators. Reviewed printed
parent-profit and EPS figures are divided to test numerical consistency only.
No collection/merged datasets are changed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sources = json.loads((BASE / "source_manifest.json").read_text())
    index = {(s["firm"], s["report_date"]): s for s in sources}
    for source in sources:
        assert sha256(ROOT / source["source_file"]) == source["source_sha256"]
        assert sha256(ROOT / source["review_text_file"]) == source["review_text_sha256"]

    # The page checks preserve the complete reviewed row sequence, not just the
    # presence of each number somewhere on the page.
    checks = [
        ("kb", "2024-05-02", 15, "지배주주순이익", [39244, 54730, 14473, 34245, 48803]),
        ("kb", "2024-05-02", 15, "수정순이익", [39244, 54730, 14473, 34245, 48803]),
        ("kb", "2024-05-02", 15, "EPS", [5777, 8057, 2131, 5042, 7185]),
        ("kb", "2026-06-10", 5, "NP attributable to controlling interests", [14473, 33621, 44261, 300401, 438614]),
        ("kb", "2026-06-10", 5, "Adj. net profit", [14473, 33621, 44261, 300401, 438614]),
        ("kb", "2026-06-10", 5, "EPS", [2131, 4950, 6564, 45182, 65970]),
        ("mirae", "2026-09-07", 1, "NP (Wbn)", [33621, 44261, 291087, 424487, 416133]),
        ("mirae", "2026-09-07", 1, "EPS (W)", [4950, 6564, 43637, 63846, 62589]),
        ("mirae", "2026-09-07", 7, "Attributable to owners", [44261, 291087, 424487, 416133]),
        ("mirae", "2026-09-07", 7, "EPS (W)", [6564, 43637, 63846, 62589]),
        ("kb", "2025-09-23", 5, "EPS", [2198, 2735, 5421, 6024, 3166, 3841, 5777, 8057, 2131, 4976, 4433]),
        ("kb", "2025-09-23", 6, "EPS", [8057, 2131, 4950, 4926, 7596]),
    ]
    table_evidence = []
    for firm, report_date, page, label, vector in checks:
        source = index[firm, report_date]
        page_text = (ROOT / source["review_text_file"]).read_text().split("\f")[page - 1]
        pattern = r"\s+".join(re.escape(f"{v:,}") for v in vector)
        matches = [line for line in page_text.splitlines() if label in line and re.search(pattern, line)]
        assert len(matches) == 1, (firm, report_date, page, label, matches)
        table_evidence.append({
            "firm": firm, "report_date": report_date, "source_page": page,
            "source_sha256": source["source_sha256"], "row_label": label,
            "reviewed_vector": vector, "retained_text_line": matches[0].strip(),
        })

    values = [
        ("kb", "2024-05-02", 15, 2021, "2021A", 39244, 5777),
        ("kb", "2024-05-02", 15, 2022, "2022A", 54730, 8057),
        ("kb", "2024-05-02", 15, 2023, "2023A", 14473, 2131),
        ("kb", "2026-06-10", 5, 2023, "2023A", 14473, 2131),
        ("kb", "2026-06-10", 5, 2024, "2024A", 33621, 4950),
        ("kb", "2026-06-10", 5, 2025, "2025A", 44261, 6564),
        ("kb", "2026-06-10", 5, 2026, "2026E", 300401, 45182),
        ("kb", "2026-06-10", 5, 2027, "2027E", 438614, 65970),
        ("mirae", "2026-09-07", 1, 2024, "2024", 33621, 4950),
        ("mirae", "2026-09-07", 1, 2025, "2025", 44261, 6564),
        ("mirae", "2026-09-07", 7, 2026, "2026F", 291087, 43637),
        ("mirae", "2026-09-07", 7, 2027, "2027F", 424487, 63846),
        ("mirae", "2026-09-07", 7, 2028, "2028F", 416133, 62589),
    ]
    rows = []
    for firm, date, page, year, column, profit, eps in values:
        source = index[firm, date]
        rows.append({
            "company_id": "samsung", "firm": firm,
            "forecaster_registry_key": source["forecaster"], "report_date": date,
            "fiscal_period": f"FY{year}", "fiscal_period_end": f"{year}-12-31",
            "printed_column": column,
            "printed_status": "estimate" if column.endswith(("E", "F")) else "historical",
            "parent_net_profit_krw_billion": profit, "eps_krw": eps,
            "diagnostic_implied_shares_million": round(profit * 1000 / eps, 6),
            "illustrative_rounding_low_million": round((profit - .5) * 1000 / (eps + .5), 6),
            "illustrative_rounding_high_million": round((profit + .5) * 1000 / (eps - .5), 6),
            "defined_eps_denominator": False,
            "source_file": source["source_file"], "source_url": source["source_url"],
            "source_sha256": source["source_sha256"], "source_page": page,
        })

    with (BASE / "diagnostics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (BASE / "diagnostics.json").write_text(json.dumps({
        "schema_version": 1,
        "purpose": "Numerical diagnostics only; no EPS denominator is established by inversion.",
        "formula": "parent_net_profit_krw_billion * 1000 / eps_krw",
        "rounding_assumption": "Illustrative nearest-integer rounding of printed KRWbn net profit and KRW EPS; not a broker-documented precision policy.",
        "rows": rows,
    }, indent=2) + "\n")
    (BASE / "table_evidence.json").write_text(json.dumps(table_evidence, indent=2, ensure_ascii=False) + "\n")
    print(f"Validated {len(sources)} original hashes and {len(checks)} page-scoped row vectors; wrote {len(rows)} diagnostic rows.")


if __name__ == "__main__":
    main()
