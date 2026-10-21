#!/usr/bin/env python3
"""Third-year EPS forecasts that Yahoo and Nasdaq lack, for the app's FY2028 and 24-month growth.

    data/extra_forecasts.json   {ticker: {"source": ..., "eps": {"2026": .., "2027": .., "2028": ..}}}

Eastmoney publishes the broker consensus for Shanghai and Shenzhen listings three
years out. Only the year-on-year ratios are used downstream, chained onto Yahoo.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "extra_forecasts.json"
EASTMONEY = ("https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_WEB_RESPREDICT"
             "&columns=ALL&filter=(SECURITY_CODE%3D%22{code}%22)")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


def eastmoney(ticker: str) -> dict | None:
    code = ticker.split(".")[0]
    with urllib.request.urlopen(urllib.request.Request(EASTMONEY.format(code=code), headers={"User-Agent": UA}),
                                timeout=30) as r:
        data = json.load(r)
    rows = ((data.get("result") or {}).get("data") or [])
    if not rows:
        return None
    d = rows[0]
    eps = {str(d[f"YEAR{i}"]): d[f"EPS{i}"] for i in range(1, 5)
           if d.get(f"YEAR{i}") and d.get(f"YEAR_MARK{i}") == "E" and d.get(f"EPS{i}") is not None}
    return {"source": f"Eastmoney consensus, {d.get('RATING_ORG_NUM') or '?'} brokers", "eps": eps} if eps else None


def main() -> None:
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as fh:
        tickers = [r["ticker"] for r in csv.DictReader(fh)]
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for t in tickers:
        if not t.endswith((".SS", ".SZ")):
            continue
        try:
            got = eastmoney(t)
        except Exception as e:  # keep the last good figures
            print(f"{t}: {e}")
            continue
        if got:
            out[t] = got
            print(t, got["eps"])
        time.sleep(0.5)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
