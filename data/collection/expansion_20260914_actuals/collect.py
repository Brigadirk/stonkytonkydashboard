#!/usr/bin/env python3
"""Collect issuer SEC reported EPS facts; preserve all filing vintages."""
from datetime import datetime, timezone, date
from pathlib import Path
import csv
import hashlib
import json
import os
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
SINCE, CUTOFF = '2020-09-10', '2026-09-11'
COMPANIES = [('AMD',2488), ('CBRS',2021728), ('MRVL',1835632), ('TSM',1046179), ('ANET',1596532), ('VRT',1674101), ('NBIS',1513845), ('ORCL',1341439), ('MSFT',789019), ('AMZN',1018724), ('META',1326801), ('SPCX',1181412), ('PLTR',1321655)]
METRICS = {'us-gaap': {'EarningsPerShareDiluted':'eps_diluted','EarningsPerShareBasic':'eps_basic'}, 'ifrs-full': {'DilutedEarningsLossPerShare':'eps_diluted','BasicEarningsLossPerShare':'eps_basic'}}
def fetch(url, path):
    if path.exists():
        raw = path.read_bytes()
    else:
        request=urllib.request.Request(url, headers={'User-Agent':os.environ['SEC_USER_AGENT'],'Accept':'application/json'})
        raw=urllib.request.urlopen(request,timeout=60).read()
        path.write_bytes(raw)
        time.sleep(.25)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()

def main():
    if not os.environ.get("SEC_USER_AGENT"):
        raise SystemExit("Set SEC_USER_AGENT to your application name and contact email before SEC collection.")
    manifest, rows = [], []
    for symbol,cik in COMPANIES:
        src = {'symbol':symbol, 'cik':cik, 'retrieved_at':datetime.now(timezone.utc).isoformat(), 'cutoff':CUTOFF}
        url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'
        path=ROOT/f'{symbol}_companyfacts.json'
        src.update(source_url=url, source_file=str(path.relative_to(ROOT)), status='downloaded')
        try:
            payload,sha=fetch(url,path)
            src.update(sha256=sha,entity_name=payload['entityName'])
            for taxonomy,tags in METRICS.items():
                for tag,metric in tags.items():
                    for unit,facts in payload.get('facts',{}).get(taxonomy,{}).get(tag,{}).get('units',{}).items():
                        for fact in facts:
                            start,end,filed=fact.get('start'),fact.get('end'),fact.get('filed')
                            if not (start and end and filed and SINCE<=end<=CUTOFF and filed<=CUTOFF):
                                continue
                            days=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
                            bucket='quarter' if 75<=days<=105 else 'annual' if 350<=days<=380 else 'other_duration'
                            rows.append(dict(symbol=symbol,cik=cik,entity_name=payload['entityName'],metric=metric,taxonomy=taxonomy,tag=tag,value=fact['val'],unit=unit,period_start=start,period_end=end,duration_days=days,duration_bucket=bucket,filed=filed,earnings_release_date=None,accession=fact.get('accn'),form=fact.get('form'),filing_fiscal_year=fact.get('fy'),filing_fiscal_period=fact.get('fp'),frame=fact.get('frame'),source_url=url,source_file=path.name,source_sha256=sha,retrieved_at=src['retrieved_at'],validation_status='raw_sec_fact_unreconciled'))
            subpath=ROOT/f'{symbol}_submissions.json'
            suburl=f'https://data.sec.gov/submissions/CIK{cik:010d}.json'
            try:
                sub,subsha=fetch(suburl,subpath)
                src.update(submissions_url=suburl,submissions_file=subpath.name,submissions_sha256=subsha,submissions_name=sub['name'],tickers=sub.get('tickers'),exchanges=sub.get('exchanges'),fiscal_year_end=sub.get('fiscalYearEnd'),former_names=sub.get('formerNames'))
            except Exception as exc:
                src['submissions_error']=str(exc)
            src['extracted_fact_count']=sum(r['symbol']==symbol for r in rows)
        except Exception as exc:
            src.update(status='failed',error=str(exc))
        manifest.append(src)
        print(json.dumps(src),flush=True)
    dedup={json.dumps(row,sort_keys=True):row for row in rows}
    rows=list(dedup.values())
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'eps_all_vintages.json').write_text(json.dumps(rows,indent=2)+'\n')
    if rows:
        with (ROOT/'eps_all_vintages.csv').open('w',newline='') as handle:
            w=csv.DictWriter(handle,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
    annual={}
    for row in rows:
        if row['metric']!='eps_diluted' or row['duration_bucket']!='annual':continue
        key=(row['symbol'],row['period_start'],row['period_end'],row['unit'])
        existing=annual.get(key)
        if existing is None or (row['filed'],row['accession'])>(existing['filed'],existing['accession']):annual[key]=row
    annual_rows=sorted(annual.values(),key=lambda r:(r['symbol'],r['period_end'],r['unit']))
    (ROOT/'annual_latest_vintage.json').write_text(json.dumps(annual_rows,indent=2)+'\n')
    quarterly={}
    for row in rows:
        if row['metric']!='eps_diluted' or row['duration_bucket']!='quarter':continue
        key=(row['symbol'],row['period_start'],row['period_end'],row['unit'])
        existing=quarterly.get(key)
        if existing is None or (row['filed'],row['accession'])>(existing['filed'],existing['accession']):quarterly[key]=row
    (ROOT/'quarterly_latest_vintage.json').write_text(json.dumps(sorted(quarterly.values(),key=lambda r:(r['symbol'],r['period_end'],r['unit'])),indent=2)+'\n')
    print(json.dumps({'total':len(rows),'annual_latest_vintages':len(annual)}))

if __name__=='__main__':main()
