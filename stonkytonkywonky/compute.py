#!/usr/bin/env python3
"""AI compute demand for the app's AI demand view: tokens, lab revenue, hyperscaler capex and backlog.

No single source measures all AI usage, so this puts several partial ones side by side:

  OpenRouter      weekly tokens by model maker on OpenRouter's API router (public rankings data).
                  A developer-heavy slice that leans to cheap open models; most Claude and
                  ChatGPT use goes direct and never shows here. Good for growth and for who
                  wins the price-sensitive developer, not for total market share.
  SEC filings     quarterly capex and remaining performance obligations (contracted, not yet
                  billed revenue: mostly multi-year cloud and AI compute deals) from XBRL.
  Disclosed       figures companies stated themselves (tokens processed, revenue run-rates),
                  curated with sources in compute_disclosed.json.
  Does it pay     whether the spending earns money: company-level cash flow, depreciation and
                  operating return on property and equipment (SEC XBRL), plus cloud segment
                  profit from the companies' own earnings releases (Google Cloud, AWS, Microsoft).
                  sec.gov's filing archive wants a contact email, so segments come from IR pages.

    data/compute/openrouter_authors.csv   week, author, tokens (kept forever; the API serves one year)
    data/compute/sec.json                 last good SEC pull
    data/compute/financials.json          last good pull of the company-level figures
    data/compute/segments.json            cloud segment figures per quarter, parsed once and kept
    app/public/data/compute.json          everything the view needs
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "compute"
APP = ROOT / "app"
OPENROUTER = "https://openrouter.ai/api/frontend/v1/rankings/"
SEC_UA = "StonkyTonkyWonky research tool"  # SEC asks for a declared agent; no personal contact sent
SEC = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/{tag}.json"
# ticker: (CIK, capex tag); every one reports remaining performance obligations except Meta,
# and Amazon stopped tagging its backlog in 2020.
COMPANIES = {
    "MSFT": (789019, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "GOOGL": (1652044, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "AMZN": (1018724, "PaymentsToAcquireProductiveAssets"),
    "META": (1326801, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "ORCL": (1341439, "PaymentsToAcquirePropertyPlantAndEquipment"),
    "CRWV": (1769628, "PaymentsToAcquirePropertyPlantAndEquipment"),
}
RPO_TAG = "RevenueRemainingPerformanceObligation"


def get_json(url: str, ua: str = "Mozilla/5.0"):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 + 3 * k)
        except Exception:  # noqa: BLE001
            time.sleep(2 + 3 * k)
    raise RuntimeError(f"failed: {url}")


# ---------- OpenRouter ----------

def openrouter() -> dict:
    path = OUT / "openrouter_authors.csv"
    rows: dict[tuple[str, str], int] = {}
    if path.exists():
        with open(path, newline="") as fh:
            rows = {(r["week"], r["author"]): int(r["tokens"]) for r in csv.DictReader(fh)}
    try:
        weeks = get_json(OPENROUTER + "author-market-share")["data"]["data"]
        # Each fetch restates the whole year; the newest week replaces what we had for it.
        for w in weeks:
            for author, tok in w["ys"].items():
                rows[(w["x"], author)] = int(tok)
        oc = get_json(OPENROUTER + "open-closed")["data"]
    except Exception as e:  # noqa: BLE001
        print(f"openrouter failed ({e}); using stored weeks")
        oc = []
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["week", "author", "tokens"])
        for (wk, a), t in sorted(rows.items()):
            w.writerow([wk, a, t])
    by_week: dict[str, dict[str, int]] = defaultdict(dict)
    for (wk, a), t in rows.items():
        by_week[wk][a] = t
    weeks = sorted(by_week)
    # The API names the top ten makers each week and lumps the rest: keep the makers that
    # were ever in a top four, everyone else goes to Others.
    top = set()
    for wk in weeks:
        top |= {a for a, _ in sorted(by_week[wk].items(), key=lambda kv: -kv[1])[:4] if a != "Others"}
    top |= {"anthropic", "openai", "google"}
    makers = sorted(top)
    series = {m: [by_week[wk].get(m, 0) for wk in weeks] for m in makers}
    totals = [sum(by_week[wk].values()) for wk in weeks]
    series["Others"] = [t - sum(series[m][i] for m in makers) for i, t in enumerate(totals)]
    # The newest week is still running; flag it so the view can leave it out of growth figures.
    partial = (date.today() - date.fromisoformat(weeks[-1])).days < 7 if weeks else False
    return {"weeks": weeks, "total": totals, "by_maker": series, "last_week_partial": partial,
            "open_closed": {"weeks": [r["x"] for r in oc], "open": [r["ys"].get("open") for r in oc],
                            "closed": [r["ys"].get("closed") for r in oc]}}


# ---------- SEC ----------

def quarters_from_ytd(facts: list[dict]) -> dict[str, float]:
    """Quarterly flows from 10-Q/10-K facts, which report year-to-date sums: Q = YTD − prior YTD."""
    best: dict[tuple[str, str], float] = {}
    for f in facts:
        if f.get("form") not in ("10-Q", "10-K", "10-Q/A", "10-K/A") or "start" not in f:
            continue
        best[(f["start"], f["end"])] = f["val"]  # later filings restate; keep the last seen
    by_start: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (s, e), v in best.items():
        by_start[s].append((e, v))
    out: dict[str, float] = {}
    for s, items in by_start.items():
        items.sort()
        prev_end, prev_val = None, 0.0
        for e, v in items:
            days = (date.fromisoformat(e) - date.fromisoformat(s)).days
            if days > 380:
                continue
            q = v - prev_val if prev_end else v
            n_q = round(((date.fromisoformat(e) - date.fromisoformat(prev_end)).days if prev_end else days) / 91)
            if n_q == 1:
                out[e] = q
            prev_end, prev_val = e, v
    return out


def sec() -> dict:
    store = OUT / "sec.json"
    try:
        data = {}
        for t, (cik, capex_tag) in COMPANIES.items():
            capex = (get_json(SEC.format(cik=cik, tag=capex_tag), SEC_UA) or {}).get("units", {}).get("USD", [])
            time.sleep(0.2)
            rpo = (get_json(SEC.format(cik=cik, tag=RPO_TAG), SEC_UA) or {}).get("units", {}).get("USD", [])
            time.sleep(0.2)
            q = quarters_from_ytd(capex)
            r = {}
            for f in rpo:
                if f.get("form", "").startswith(("10-Q", "10-K")):
                    r[f["end"]] = f["val"]
            data[t] = {"capex": dict(sorted(q.items())), "rpo": dict(sorted(r.items()))}
        store.write_text(json.dumps(data))
    except Exception as e:  # noqa: BLE001
        print(f"SEC failed ({e}); using the stored pull")
        data = json.loads(store.read_text())
    return data


def quarter_label(end: str) -> str:
    d = date.fromisoformat(end)
    # Calendar quarter the period mostly falls in (Oracle and Microsoft have odd fiscal years).
    m = d.month - 1 if d.day < 15 else d.month
    m = 12 if m == 0 else m
    y = d.year if d.month != 1 or d.day >= 15 else d.year - 1
    return f"{y}Q{(m - 1) // 3 + 1}"


def sec_view(data: dict) -> dict:
    labels = sorted({quarter_label(e) for v in data.values() for e in v["capex"]})
    labels = [q for q in labels if q >= "2019Q1"]
    capex = {}
    for t, v in data.items():
        by_q = {quarter_label(e): x for e, x in v["capex"].items()}
        capex[t] = [None if q not in by_q else round(by_q[q] / 1e9, 2) for q in labels]
    # The sum is only meaningful where all the big five reported (CoreWeave is small and young).
    big = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]
    total = [round(sum(capex[t][i] for t in big), 1) if all(capex[t][i] is not None for t in big) else None for i in range(len(labels))]
    rpo = {}
    stale = (date.today().replace(year=date.today().year - 1)).isoformat()
    for t, v in data.items():
        if v["rpo"] and max(v["rpo"]) >= stale:  # Amazon's tagged backlog stops in 2020
            rpo[t] = {"dates": list(v["rpo"]), "bn": [round(x / 1e9, 1) for x in v["rpo"].values()]}
    return {"quarters": labels, "capex_bn": capex, "capex_total_bn": total, "rpo": rpo}


# ---------- Does it pay ----------

BIG = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]
# Company-level XBRL concepts; where a company switched tags, later entries win for the dates they cover.
FIN_TAGS = {
    "ocf": ["NetCashProvidedByUsedInOperatingActivities"],
    "oi": ["OperatingIncomeLoss"],
    "rev": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "da": ["Depreciation", "DepreciationDepletionAndAmortization"],
    # Instant values. The second tag includes finance-lease assets (Amazon, Alphabet and Meta
    # moved to it), so each company keeps one definition over the years the view shows.
    "ppe": ["PropertyPlantAndEquipmentNet",
            "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"],
}
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
GOOGL_RELEASE = "https://s206.q4cdn.com/479360582/files/doc_financials/{y}/q{q}/{y}q{q}-alphabet-earnings-release.pdf"
AMZN_REPORTS = ("https://ir.aboutamazon.com/feed/FinancialReport.svc/GetFinancialReportList?"
                "apiKey=BF185719B0464B3CB809D23926182246&LanguageId=1&pageSize=200&pageNumber=0&year=-1")
MSFT_RELEASE = "https://www.microsoft.com/en-us/investor/earnings/fy-{fy}-q{q}/press-release-webcast"


def financials() -> dict:
    """Quarterly flows and quarter-end PP&E per company, in dollars, keyed by period end."""
    store = OUT / "financials.json"
    try:
        data = {}
        for t in BIG:
            cik = COMPANIES[t][0]
            data[t] = {}
            for key, tags in FIN_TAGS.items():
                merged: dict[str, float] = {}
                for tag in tags:
                    facts = (get_json(SEC.format(cik=cik, tag=tag), SEC_UA) or {}).get("units", {}).get("USD", [])
                    time.sleep(0.2)
                    if key == "ppe":
                        vals = {f["end"]: f["val"] for f in facts if f.get("form", "").startswith(("10-Q", "10-K"))}
                    else:
                        vals = quarters_from_ytd(facts)
                    merged.update(vals)
                data[t][key] = dict(sorted(merged.items()))
        store.write_text(json.dumps(data))
    except Exception as e:  # noqa: BLE001
        print(f"SEC financials failed ({e}); using the stored pull")
        data = json.loads(store.read_text())
    return data


def get_text(url: str, ua: str = "Mozilla/5.0") -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/pdf,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def pdf_text(blob: bytes, layout: bool = True) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as fh:
        fh.write(blob)
        fh.flush()
        args = ["pdftotext", "-layout", fh.name, "-"] if layout else ["pdftotext", fh.name, "-"]
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def num_m(s: str) -> float:
    """'(1,234)' or '1,234' in $ millions → dollars."""
    neg = s.startswith("(")
    v = float(s.strip("()$ ").replace(",", "")) * 1e6
    return -v if neg else v


def parse_googl(text: str) -> tuple[dict, dict] | None:
    """Google Cloud revenue and operating income: (this year's quarter, the year-earlier one)."""
    nums = r"\$?\s*(\(?[\d,]+\)?)\s+\$?\s*(\(?[\d,]+\)?)"
    rev = oi = None
    in_oi = False
    for ln in text.splitlines():
        s = ln.strip()
        if s.lower().startswith("operating income (loss):"):
            in_oi = True
        m = re.match(r"Google Cloud\s+" + nums, s)
        if m:
            if in_oi and oi is None:
                oi = (num_m(m.group(2)), num_m(m.group(1)))
            elif not in_oi and rev is None:
                rev = (num_m(m.group(2)), num_m(m.group(1)))
    if not (rev and oi):
        return None
    return {"rev": rev[0], "oi": oi[0]}, {"rev": rev[1], "oi": oi[1]}


def parse_amzn(text: str) -> dict | None:
    t = re.sub(r"\s+", " ", text)
    rev = re.search(r"AWS segment sales increased [\d.]+% year-over-year to \$([\d.]+) billion", t)
    oi = re.search(r"AWS segment operating income (?:\(loss\) )?was \$([\d.]+) billion", t)
    if not (rev and oi):
        return None
    return {"rev": float(rev.group(1)) * 1e9, "oi": float(oi.group(1)) * 1e9}


def parse_msft(page: str) -> dict:
    """Intelligent Cloud (the cloud segment through June 2026) or, from fiscal 2027, the
    broader Agents and Infra segment plus Azure revenue, whichever the release reports."""
    s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    out = {}
    for seg, key in (("Intelligent Cloud", "msft_ic"), ("Agents and Infra", "msft_ai")):
        # Newer layout: "<segment> Revenue $x $y Cost of revenue … Operating income $x $y".
        m = re.search(seg + r" Revenue \$([\d,]+) \$[\d,]+ .{0,200}?Operating income \$([\d,]+)", s)
        if not m:
            # Older layout: a revenue table and an operating income table, one row per segment.
            r = re.search(r"Revenue Productivity.{0,200}?" + seg + r" \$?([\d,]+)", s)
            o = re.search(r"Operating Income Productivity.{0,200}?" + seg + r" \$?([\d,]+)", s)
            m = (r.group(1), o.group(1)) if r and o else None
        else:
            m = m.groups()
        if m:
            out[key] = {"rev": num_m(m[0]), "oi": num_m(m[1])}
    az = re.search(r"Azure \$([\d,]+) \$[\d,]+", s)
    if az:
        out["msft_azure"] = {"rev": num_m(az.group(1))}
    return out


def quarter_end(y: int, q: int) -> str:
    return f"{y}-{q * 3:02d}-{30 if q in (2, 3) else 31}"


def segments() -> dict:
    """{series: {quarter end: {rev, oi}}}. Parsed releases are kept, so each night only asks
    for quarters not yet stored."""
    store = OUT / "segments.json"
    seg: dict[str, dict] = json.loads(store.read_text()) if store.exists() else {}
    for k in ("googl_cloud", "amzn_aws", "msft_ic", "msft_ai", "msft_azure"):
        seg.setdefault(k, {})
    today = date.today()
    quarters = [(y, q) for y in range(2022, today.year + 1) for q in range(1, 5)
                if quarter_end(y, q) < today.isoformat()]

    def keep(name: str, end: str, val: dict | None):
        if val:
            seg[name][end] = val

    for y, q in quarters:
        end = quarter_end(y, q)
        try:
            if end not in seg["googl_cloud"]:
                blob = get_text(GOOGL_RELEASE.format(y=y, q=q))
                both = parse_googl(pdf_text(blob)) if blob else None
                if both:
                    keep("googl_cloud", end, both[0])
                    # A release whose year-earlier quarter is missing (2024Q1 has no PDF at the usual path).
                    seg["googl_cloud"].setdefault(quarter_end(y - 1, q), both[1])
            # Microsoft's fiscal year ends in June: calendar Q3 is fiscal Q1 of the next year.
            fy, fq = (y + 1, q - 2) if q >= 3 else (y, q + 2)
            if end not in seg["msft_ic"] and end not in seg["msft_ai"]:
                page = get_text(MSFT_RELEASE.format(fy=fy, q=fq), BROWSER_UA)
                for name, val in (parse_msft(page.decode("utf-8", "ignore")) if page else {}).items():
                    keep(name, end, val)
        except Exception as e:  # noqa: BLE001
            print(f"segments {y}Q{q} failed ({e})")
    try:
        reports = (get_json(AMZN_REPORTS) or {}).get("GetFinancialReportList" + "Result") or []
        names = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
        for r in reports:
            q = names.get(r["ReportSubType"].split()[0])
            if not q or int(r["ReportYear"]) < 2022:
                continue
            end = quarter_end(int(r["ReportYear"]), q)
            if end in seg["amzn_aws"]:
                continue
            pdf = next((d["DocumentPath"] for d in r["Documents"] if d["DocumentPath"].endswith("Earnings-Release.pdf")), None)
            blob = get_text(pdf) if pdf else None
            keep("amzn_aws", end, parse_amzn(pdf_text(blob)) if blob else None)
    except Exception as e:  # noqa: BLE001
        print(f"segments AWS failed ({e})")
    for k in seg:
        seg[k] = dict(sorted(seg[k].items()))
    store.write_text(json.dumps(seg, indent=1))
    return seg


def ttm(by_q: dict[str, float], labels: list[str], i: int) -> float | None:
    """Sum of the four quarters ending at labels[i], when all four are there."""
    if i < 3:
        return None
    vals = [by_q.get(labels[j]) for j in range(i - 3, i + 1)]
    return None if any(v is None for v in vals) else sum(vals)


def returns_view(fin: dict, seg: dict) -> dict:
    """Per company and quarter (trailing twelve months): free cash flow, capex as a share of
    operating cash flow, depreciation as a share of revenue, operating return on PP&E, and
    the incremental return: extra operating profit over the year against the PP&E added the
    year before (new data centres take about a year to earn)."""
    labels = sorted({quarter_label(e) for t in BIG for e in fin[t]["oi"]})
    labels = [q for q in labels if q >= "2018Q1"]
    show = [i for i, q in enumerate(labels) if q >= "2021Q1"]
    r1 = lambda x: None if x is None else round(x, 3)  # noqa: E731
    bn = lambda x: None if x is None else round(x / 1e9, 1)  # noqa: E731
    out = {"quarters": [labels[i] for i in show], "companies": {}}
    for t in BIG:
        f = {k: {quarter_label(e): v for e, v in fin[t][k].items()} for k in FIN_TAGS}
        capex = {quarter_label(e): v for e, v in fin[t]["_capex"].items()}
        rows = {k: [] for k in ("fcf_bn", "capex_ocf", "da_rev", "ret_ppe", "inc_ret", "ppe_bn", "oi_ttm_bn", "capex_ttm_bn")}
        for i in show:
            ocf, cx, oi, rev, da = (ttm(s, labels, i) for s in (f["ocf"], capex, f["oi"], f["rev"], f["da"]))
            ppe = f["ppe"].get(labels[i])
            ppe_1y = f["ppe"].get(labels[i - 4]) if i >= 4 else None
            ppe_2y = f["ppe"].get(labels[i - 8]) if i >= 8 else None
            oi_1y = ttm(f["oi"], labels, i - 4) if i >= 7 else None
            rows["fcf_bn"].append(bn(ocf - cx) if ocf is not None and cx is not None else None)
            rows["capex_ocf"].append(r1(cx / ocf) if cx is not None and ocf else None)
            rows["da_rev"].append(r1(da / rev) if da is not None and rev else None)
            rows["ret_ppe"].append(r1(oi / ((ppe + ppe_1y) / 2)) if oi is not None and ppe and ppe_1y else None)
            added = ppe_1y - ppe_2y if ppe_1y is not None and ppe_2y is not None else None
            rows["inc_ret"].append(r1((oi - oi_1y) / added) if oi is not None and oi_1y is not None and added and added > 0 else None)
            rows["ppe_bn"].append(bn(ppe))
            rows["oi_ttm_bn"].append(bn(oi))
            rows["capex_ttm_bn"].append(bn(cx))
        out["companies"][t] = rows
    # Cloud segments: quarterly revenue, operating income and margin, plus trailing operating
    # income against the parent's capex of the year before.
    cloud = {}
    names = {"googl_cloud": ("Google Cloud", "GOOGL"), "amzn_aws": ("AWS", "AMZN"),
             "msft_ic": ("Microsoft Intelligent Cloud (old segment)", "MSFT"),
             "msft_ai": ("Microsoft Agents and Infra (from fiscal 2027)", "MSFT")}
    for key, (label, parent) in names.items():
        by_q = {quarter_label(e): v for e, v in seg.get(key, {}).items()}
        if not by_q:
            continue
        capex = {quarter_label(e): v for e, v in fin[parent]["_capex"].items()}
        oi_q = {q: v["oi"] for q, v in by_q.items()}
        series = {"label": label, "parent": parent, "rev_bn": [], "oi_bn": [], "margin": [], "oi_per_capex": []}
        for i in show:
            q = labels[i]
            v = by_q.get(q)
            series["rev_bn"].append(bn(v["rev"]) if v else None)
            series["oi_bn"].append(bn(v["oi"]) if v else None)
            series["margin"].append(r1(v["oi"] / v["rev"]) if v and v["rev"] else None)
            o, c = ttm(oi_q, labels, i), ttm(capex, labels, i - 4) if i >= 7 else None
            series["oi_per_capex"].append(r1(o / c) if o is not None and c else None)
        cloud[key] = series
    out["cloud"] = cloud
    az = {quarter_label(e): v["rev"] for e, v in seg.get("msft_azure", {}).items()}
    out["azure_rev_bn"] = [bn(az.get(labels[i])) for i in show]
    return out


# ---------- Who buys ----------

NVDA_REPORTS = ("https://investor.nvidia.com/feed/FinancialReport.svc/GetFinancialReportList?"
                "apiKey=BF185719B0464B3CB809D23926182246&LanguageId=1&pageSize=60&pageNumber=0&year=-1")
FINMIND = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockMonthRevenue&data_id={sid}&start_date=2019-01-01"
# Taiwanese contract manufacturers that build servers mostly for the hyperscalers, sold direct.
# Hon Hai is left out: its server business is large but drowned by phones in monthly revenue.
ODMS = {"2382": "Quanta", "6669": "Wiwynn", "3231": "Wistron"}
# Companies buying outside the hyperscaler channel, with revenue tagged in their SEC filings.
OTHER_BUYERS = {"SMCI": (1375365, "Supermicro: servers for neoclouds, enterprises and sovereigns"),
                "CRWV": (1769628, "CoreWeave: the largest neocloud")}


def nvda_quarter_end(fy: int, q: int) -> str:
    """Nvidia's fiscal year ends in late January: fiscal Q1 of FY27 ends in April 2026."""
    return f"{fy}-01-31" if q == 4 else f"{fy - 1}-{3 * q + 1:02d}-30"


def parse_nvda(text: str, fy: int, q: int) -> dict:
    """Hyperscale and ACIE revenue (from fiscal 2027, with the two comparison quarters the
    table carries), else the approximate share of large cloud providers stated in prose."""
    t = re.sub(r"\s+", " ", text)
    out = {}
    hy = re.search(r"Hyperscale \$?([\d,]+) \$?([\d,]+) \$?([\d,]+)", t)
    ac = re.search(r"AI Clouds, Industrial, & Enterprise \$?([\d,]+) \$?([\d,]+) \$?([\d,]+)", t)
    if hy and ac:
        prev = (fy, q - 1) if q > 1 else (fy - 1, 4)
        for k, (yy, qq) in enumerate(((fy, q), prev, (fy - 1, q))):
            out[nvda_quarter_end(yy, qq)] = {"hyperscale": num_m(hy.group(k + 1)), "acie": num_m(ac.group(k + 1)),
                                             "exact": True, "report": nvda_quarter_end(fy, q)}
        return out
    dc = re.search(r"Data Center \$?([\d,]+) \$?([\d,]+) \$?([\d,]+)", t)
    for m in re.finditer(r"([^.]{0,200}?)(mid-|just under |slightly over )?(\d+)% of (?:our )?Data Center revenue", t):
        if dc and re.search(r"cloud|hyperscal", m.group(1), re.I):
            share = int(m.group(3)) / 100 + {"mid-": 0.05, "just under ": -0.01, "slightly over ": 0.01}.get(m.group(2) or "", 0)
            total = num_m(dc.group(1))
            out[nvda_quarter_end(fy, q)] = {"hyperscale": total * share, "acie": total * (1 - share), "exact": False,
                                            "report": nvda_quarter_end(fy, q)}
            break
    return out


def nvidia_split() -> dict:
    """{quarter end: {hyperscale, acie, exact}}; exact figures overwrite approximations and
    the latest report overwrites recast quarters."""
    store = OUT / "nvidia_split.json"
    have = json.loads(store.read_text()) if store.exists() else {}
    try:
        reports = (get_json(NVDA_REPORTS) or {}).get("GetFinancialReportListResult") or []
        names = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
        found: dict[str, dict] = {}
        for r in sorted(reports, key=lambda r: (r["ReportYear"], names.get(r["ReportSubType"].split()[0], 0))):
            q = names.get(r["ReportSubType"].split()[0])
            if not q or int(r["ReportYear"]) < 2025:
                continue
            end = nvda_quarter_end(int(r["ReportYear"]), q)
            # Old quarters are parsed once; the newest two are re-read for recasts.
            if end in have and end < max(have, default="") and have[end].get("exact"):
                continue
            pdf = next((d["DocumentPath"] for d in r["Documents"] if "CFO" in d["DocumentTitle"]), None)
            blob = get_text(pdf) if pdf else None
            if blob:
                for e, v in parse_nvda(pdf_text(blob, layout=False), int(r["ReportYear"]), q).items():
                    if v["exact"] or not found.get(e, {}).get("exact"):
                        found[e] = v
        for e, v in found.items():
            if v["exact"] or not have.get(e, {}).get("exact"):
                have[e] = v
        store.write_text(json.dumps(dict(sorted(have.items())), indent=1))
    except Exception as e:  # noqa: BLE001
        print(f"nvidia split failed ({e}); using stored figures")
    return dict(sorted(have.items()))


def odm_monthly() -> dict:
    """Monthly revenue (NT$) of the hyperscaler server builders; kept on disk, refreshed nightly."""
    store = OUT / "odm_monthly.json"
    data = json.loads(store.read_text()) if store.exists() else {}
    for sid in ODMS:
        try:
            rows = (get_json(FINMIND.format(sid=sid)) or {}).get("data") or []
            got = {f"{r['revenue_year']}-{r['revenue_month']:02d}": r["revenue"] for r in rows}
            if got:
                data[sid] = dict(sorted({**data.get(sid, {}), **got}.items()))
        except Exception as e:  # noqa: BLE001
            print(f"ODM {sid} failed ({e}); keeping stored months")
        time.sleep(1)
    store.write_text(json.dumps(data))
    return data


def other_buyers() -> dict:
    out = {}
    for t, (cik, _) in OTHER_BUYERS.items():
        merged: dict[str, float] = {}
        for tag in FIN_TAGS["rev"]:
            facts = (get_json(SEC.format(cik=cik, tag=tag), SEC_UA) or {}).get("units", {}).get("USD", [])
            merged.update(quarters_from_ytd(facts))
            time.sleep(0.2)
        out[t] = dict(sorted(merged.items()))
    return out


def buyers_view(split: dict, odm: dict, others: dict) -> dict:
    # Nvidia's quarters end a month after the calendar's (February to April is its Q1).
    nv = [{"end": e, "label": quarter_label((date.fromisoformat(e) - timedelta(days=31)).isoformat()), "hyperscale_bn": round(v["hyperscale"] / 1e9, 1),
           "acie_bn": round(v["acie"] / 1e9, 1), "acie_share": round(v["acie"] / (v["hyperscale"] + v["acie"]), 3),
           "exact": v["exact"],
           # Nvidia recasts only the quarters in its newest table when it moves a customer between
           # the two groups (it did in fiscal Q2 2027); quarters from older reports are on the old basis.
           "current_basis": v.get("report") == max(x.get("report", "") for x in split.values())}
          for e, v in split.items()]
    months = sorted(set.intersection(*(set(v) for v in odm.values()))) if odm else []
    total = [sum(odm[s][m] for s in odm) for m in months]
    # Growth of the latest three months against the same three a year earlier: smooths lumpy shipments.
    yoy3 = [None if i < 14 else round(sum(total[i - 2:i + 1]) / sum(total[i - 14:i - 11]) - 1, 3) for i in range(len(total))]
    odm_v = {"months": months, "total_bn_twd": [round(x / 1e9, 1) for x in total], "yoy3": yoy3,
             "by_company": {ODMS[s]: [round(odm[s][m] / 1e9, 1) for m in months] for s in odm}}
    oth = {}
    for t, by_end in others.items():
        ends = [e for e in by_end if e >= "2023-01-01"]
        oth[t] = {"label": OTHER_BUYERS[t][1], "quarters": [quarter_label(e) for e in ends],
                  "rev_bn": [round(by_end[e] / 1e9, 2) for e in ends]}
    return {"nvidia": nv, "odm": odm_v, "others": oth}


# Series for the one-chart view: (key, label, group, series id in compute_disclosed.json)
DISCLOSED_LINES = [
    ("google_tokens", "Google tokens a month (all products)", "tokens", "google_tokens_month"),
    ("google_api", "Google API tokens a minute", "tokens", "google_api_tokens_min"),
    ("bytedance", "ByteDance tokens a day", "tokens", "bytedance_tokens_day"),
    ("anthropic_rr", "Anthropic revenue run-rate", "revenue", "anthropic_revenue_runrate"),
    ("openai_rr", "OpenAI revenue run-rate", "revenue", "openai_revenue_runrate"),
    ("chatgpt_users", "ChatGPT weekly users", "users", "openai_weekly_users"),
    ("gemini_users", "Gemini monthly users", "users", "google_gemini_mau"),
]


def combined(payload: dict, sec_raw: dict) -> list[dict]:
    """Every demand series as dated values, for one log chart."""
    lines = []
    o = payload["openrouter"]
    n = len(o["weeks"]) - (1 if o["last_week_partial"] else 0)
    lines.append({"key": "openrouter", "label": "OpenRouter tokens a week", "group": "tokens", "unit": "tokens",
                  "dates": o["weeks"][:n], "values": o["total"][:n]})
    s = payload["sec"]
    qn = [i for i, v in enumerate(s["capex_total_bn"]) if v is not None]
    q_end = lambda q: f"{q[:4]}-{int(q[5]) * 3:02d}-{30 if q[5] in '23' else 31}"  # noqa: E731
    lines.append({"key": "capex", "label": "Big-five capex a quarter", "group": "spend", "unit": "$bn",
                  "dates": [q_end(s["quarters"][i]) for i in qn], "values": [s["capex_total_bn"][i] for i in qn]})
    # Backlog: Microsoft + Alphabet + Oracle, by calendar quarter, where all three reported.
    by_q: dict[str, dict[str, float]] = defaultdict(dict)
    for t in ("MSFT", "GOOGL", "ORCL"):
        for end, v in sec_raw[t]["rpo"].items():
            by_q[quarter_label(end)][t] = v / 1e9
    qs = [q for q in sorted(by_q) if len(by_q[q]) == 3 and q >= "2019Q1"]
    lines.append({"key": "backlog", "label": "Cloud backlog (MSFT + GOOGL + ORCL)", "group": "spend", "unit": "$bn",
                  "dates": [q_end(q) for q in qs], "values": [round(sum(by_q[q].values()), 1) for q in qs]})
    pts = payload["disclosed"].get("points", [])
    for key, label, group, series in DISCLOSED_LINES:
        xs = sorted((p["date"], p["value"], p["unit"]) for p in pts if p["series"] == series)
        if len(xs) >= 3 and len({u for _, _, u in xs}) == 1:
            lines.append({"key": key, "label": label, "group": group, "unit": xs[0][2],
                          "dates": [d for d, _, _ in xs], "values": [v for _, v, _ in xs]})
    dxi = ROOT / "data" / "industry" / "dxi.csv"
    if dxi.exists():
        with open(dxi, newline="") as fh:
            rows = [(r["date"], float(r["dxi"])) for r in csv.DictReader(fh) if r["date"] >= "2019-01-01"]
        lines.append({"key": "dram", "label": "DRAM spot prices (DXI index)", "group": "memory", "unit": "index",
                      "dates": [d for d, _ in rows], "values": [round(v, 1) for _, v in rows]})
    return lines


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "openrouter": openrouter()}
    sec_raw = sec()
    payload["sec"] = sec_view(sec_raw)
    disclosed = ROOT / "compute_disclosed.json"
    payload["disclosed"] = json.loads(disclosed.read_text()) if disclosed.exists() else {"points": []}
    payload["combined"] = combined(payload, sec_raw)
    fin = financials()
    for t in BIG:
        fin[t]["_capex"] = sec_raw[t]["capex"]
    payload["returns"] = returns_view(fin, segments())
    try:
        payload["buyers"] = buyers_view(nvidia_split(), odm_monthly(), other_buyers())
    except Exception as e:  # noqa: BLE001 — the rest of the view still ships
        print(f"buyers failed ({e})")
    out = APP / "public" / "data" / "compute.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")))
    tmp.replace(out)
    if (APP / "dist" / "data").is_dir():
        shutil.copy(out, APP / "dist" / "data" / out.name)
    o = payload["openrouter"]
    s = payload["sec"]
    i = -2 if o["last_week_partial"] else -1
    print(f"compute: OpenRouter week {o['weeks'][i]} {o['total'][i] / 1e12:.1f}T tokens, anthropic "
          f"{o['by_maker']['anthropic'][i] / o['total'][i]:.1%}; capex {s['quarters'][-1]} "
          f"{[(t, v[-1]) for t, v in s['capex_bn'].items()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
