"""Rule-based readers for the report formats we see most, so the model is only a fallback.

Each parser takes the full pdftotext -layout text (pages split by form feeds)
and returns the same dict the Claude extraction returns, or None when the
report isn't its format. Forecast years are only those the report marks as
forecasts (Morningstar: fiscal year ends after the report date; Korean
brokers: years suffixed E or F).
"""

from __future__ import annotations

import re
from datetime import date, datetime

NUM = r"\(?-?[\d,]+(?:\.\d+)?\)?"
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def to_float(tok: str) -> float:
    neg = tok.startswith("(") and tok.endswith(")")
    v = float(tok.strip("()").replace(",", ""))
    return -v if neg else v


# ---------- Morningstar equity analyst reports ----------

def morningstar(text: str, tickers: set[str], hint: str = "") -> dict | None:
    if not text.startswith("Morningstar Equity Analyst Report"):
        return None
    head = re.search(r"Report as of (\d{1,2}) (\w{3}) (\d{4})", text)
    if not head:
        return None
    report = date(int(head.group(3)), MONTHS[head.group(2)], int(head.group(1)))

    ticker = hint
    if not ticker:
        for line in text.splitlines()[:8]:
            hit = [t for t in line.split() if t in tickers]
            if hit:
                ticker = hit[0]
                break
    analyst = re.search(r"Analyst Note ([A-Z][^,\n]+?),", text)

    # "Fiscal Year, ends 30 Jun   2024  2025 ..." followed by the EPS rows.
    fy = re.search(r"Fiscal Year, ends (\d{1,2}) (\w{3})\s+((?:\d{4}\s+){2,}\d{4})", text)
    if not fy:
        return None
    end_day, end_mon = int(fy.group(1)), MONTHS[fy.group(2)]
    years = [int(y) for y in fy.group(3).split()]
    tail = text[fy.end():fy.end() + 4000]
    row = None
    basis = ""
    for label, b in (("Adjusted Earnings Per Share (Diluted)", "adjusted diluted"),
                     ("Earnings Per Share (Diluted)", "GAAP diluted")):
        m = re.search(rf"^{re.escape(label)} \((\w{{3}})\)\s+((?:{NUM}\s+)*{NUM})\s*$", tail, re.M)
        if m:
            row, basis, ccy = m, b, m.group(1)
            break
    if not row:
        return None
    values = row.group(2).split()
    if len(values) != len(years):
        return None
    estimates = []
    for y, v in zip(years, values):
        try:
            fy_end = date(y, end_mon, end_day)
        except ValueError:  # 29 Feb and friends: use the month's last valid day
            fy_end = date(y, end_mon, 28)
        if fy_end > report:
            estimates.append({"fiscal_year": y, "fiscal_year_end": fy_end.isoformat(),
                              "eps": to_float(v), "eps_as_printed": v, "page": ""})
    if not estimates:
        return None
    return {"is_company_report": True, "ticker": ticker, "company": "", "firm": "Morningstar",
            "analysts": [analyst.group(1).strip()] if analyst else [], "report_date": report.isoformat(),
            "currency": ccy, "eps_basis": basis, "estimates": estimates, "parser": "morningstar"}


# ---------- Korean broker reports ----------

KOREAN_FIRMS = {
    "메리츠": "Meritz Securities", "Meritz": "Meritz Securities", "하나증권": "Hana Securities",
    "Hana Securities": "Hana Securities", "KB증권": "KB Securities", "미래에셋": "Mirae Asset",
    "NH투자": "NH Investment", "현대차증권": "Hyundai Motor Securities", "삼성증권": "Samsung Securities",
    "키움": "Kiwoom", "대신증권": "Daishin", "신한투자": "Shinhan Investment", "한국투자": "Korea Investment",
    "유진투자": "Eugene Investment", "SK증권": "SK Securities", "교보증권": "Kyobo Securities",
    "IBK투자": "IBK Investment", "DB금융": "DB Financial", "유안타": "Yuanta", "iM증권": "iM Securities",
}
EPS_LABEL = re.compile(r"(?:수정\s*)?EPS\s*(?:\(지배주주\)|\(원\)|\(KRW\))?|주당순이익")
YEAR = re.compile(r"\b(20\d{2})([EFP]?)\b")


def korean(text: str, tickers: set[str], hint: str = "") -> dict | None:
    first = text.split("\f")[0]
    code = hint
    if not code:
        for m in re.finditer(r"\(\s*(\d{6})\s*\)|\b(\d{6})\b", first):
            c = m.group(1) or m.group(2)
            hit = next((t for t in tickers if t.startswith(c + ".")), None)
            if hit:
                code = hit
                break
    if not code or not code.endswith((".KS", ".KQ")):
        return None
    when = re.search(r"(20\d{2})\.\s?(\d{1,2})\.\s?(\d{1,2})", first)
    firm = next((name for key, name in KOREAN_FIRMS.items() if key in text[:20000]), "")
    analyst = re.search(r"Analyst\s+([가-힣]{2,4})", first)

    estimates = eps_row(text)
    if not estimates or not when:
        return None
    return {"is_company_report": True, "ticker": code, "company": "", "firm": firm,
            "analysts": [analyst.group(1)] if analyst else [],
            "report_date": date(int(when.group(1)), int(when.group(2)), int(when.group(3))).isoformat(),
            "currency": "KRW", "eps_basis": "controlling-shareholder EPS as printed",
            "estimates": estimates, "parser": "korean"}


def eps_row(text: str) -> list[dict] | None:
    """A horizontal EPS row under a year header. Tables often sit two to a line,
    so the row's figures pair with the LAST len(figures) years of the header above."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = EPS_LABEL.search(line)
        if not m:
            continue
        figures = re.findall(NUM, line[m.end():])
        figures = [f for f in figures if re.search(r"\d", f)]
        if len(figures) < 3:
            continue
        for back in range(1, 40):  # nearest header above with enough year columns
            hdr = lines[i - back] if i - back >= 0 else ""
            years = YEAR.findall(hdr)
            if len(years) >= len(figures):
                years = years[-len(figures):]
                out = [{"fiscal_year": int(y), "fiscal_year_end": f"{y}-12-31", "eps": to_float(v),
                        "eps_as_printed": v, "page": ""}
                       for (y, flag), v in zip(years, figures) if flag in ("E", "F")]
                if out:
                    return out
                break
    return None


PARSERS = (morningstar, korean)


def parse(text: str, tickers: set[str], hint: str = "") -> dict | None:
    for p in PARSERS:
        try:
            got = p(text, tickers, hint)
        except Exception:  # noqa: BLE001 — an odd layout just means "not this parser"
            got = None
        if got and got.get("ticker"):
            return got
    return None
