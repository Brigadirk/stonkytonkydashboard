"""Offline extraction of reviewed forecasts and initial issuer EPS outcomes."""
import csv
import hashlib
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OBS_FIELDS='observation_id,company_id,firm,analyst_name,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MAN_FIELDS='source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type'.split(',')
OUT_FIELDS='outcome_id,company_id,fiscal_period,fiscal_period_end,metric,accounting_basis,value,currency,unit,initial_release_date,actual_available_at,share_basis_date,source_url,source_file,source_sha256,source_page,source_locator,definition,definition_id,definition_source_locator,result_version,validation_status,raw_source_row,notes'.split(',')

def write_csv(name,fields,rows):
    with (BASE/name).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)

def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def numbers(line):return re.findall(r'(?<![A-Za-z])[-−]?\d[\d,]*(?:\.\d+)?',line)
def row_values(text,label):
    line=next(x for x in text.splitlines() if x.strip().startswith(label))
    return [x.replace(',','') for x in numbers(line[len(line)-len(line.lstrip())+len(label):])]

broker=[x for x in json.loads((BASE/'broker_download_log.json').read_text()) if x.get('local_file')]
spec={
 'alphabet':dict(report_date='2025-09-03',timestamp='2025-09-03T23:21:00+00:00',model='2025-07-23',printed_model='23 Jul 2025',page=19,author='Malik Ahmed Khan',currency='USD',rev=['392807','434714','478274','523437','570357'],eps=['10.18','10.94','12.19','13.52','15.00'],plain_basis='reported_diluted'),
 'asml':dict(report_date='2025-04-03',timestamp='2025-04-03T15:27:00+00:00',model='2025-01-29',printed_model='29 Jan 2025',page=15,author='Javier Correonero',currency='EUR',rev=['34201','38258','42868','46615','50409'],eps=['24.69','30.87','35.84','40.88','46.09'],plain_basis='morningstar_unadjusted_diluted'),
}
observations=[];manifest=[]
for src in broker:
    company=src['company_id'];s=spec[company]
    assert sha(src['local_file'])==src['sha256']
    pages=(ROOT/src['text_file']).read_text().split('\f');table=pages[s['page']-1]
    assert 'Financials as of '+s['printed_model'] in table
    assert s['author'] in pages[0]
    assert row_values(table,f"Revenue ({s['currency']} Mil)")[-5:]==s['rev']
    assert row_values(table,f"Earnings Per Share (Diluted) ({s['currency']})")[-5:]==s['eps']
    assert row_values(table,f"Adjusted Earnings Per Share (Diluted) ({s['currency']})")[-5:]==s['eps']
    for metric,basis,values in [('revenue','total_revenue',s['rev']),('eps_diluted',s['plain_basis'],s['eps']),('eps_adjusted_diluted','adjusted_diluted',s['eps'])]:
        for year,value in zip(range(2025,2030),values):
            note='Current financial-model rows only; prior revision values are supporting evidence, never backdated forecasts. Original printed report/model dates remain distinct and original dissemination time is unverified. Annual December31 fiscal years. Values and currency retained as printed; no split transformation. '
            if company=='asml':note+='ASML ADR report uses EUR financial statements; these EUR per-ordinary-share forecasts require no FX conversion for Amsterdam. Plain diluted EPS is a broker model series, not proven identical to issuer US-GAAP diluted EPS: exact historical net incomes match, but FY2022/23/25 share counts and EPS disagree. Keep it out of issuer scoring and cross-author GAAP ensembles pending denominator reconciliation. '
            else:note+='Alphabet Class A, USD, post-July2022 split units. Plain and adjusted rows happen to agree; both labels remain separate. '
            row=dict.fromkeys(OBS_FIELDS,'')
            row.update(observation_id=hashlib.sha256('|'.join([src['sha256'],metric,str(year),value]).encode()).hexdigest()[:24],company_id=company,firm='Morningstar',analyst_name=s['author'],metric=metric,fiscal_period=f'FY{year}',value=value,currency=s['currency'],unit=s['currency']+('_million' if metric=='revenue' else '_per_share'),basis=basis,model_date=s['model'],forecast_revision_as_of=s['model'],report_date=s['report_date'],printed_report_timestamp=s['timestamp'],availability_basis='printed_report_timestamp_not_independently_verified',source_url=src['source_url'],local_file=src['local_file'],page=s['page'],status='verified_original_table',notes=note,source_period_label=str(year),share_basis_date=s['model'],source_artifact_sha256=src['sha256'])
            observations.append(row)
    manifest.append(dict(source_url=src['source_url'],local_file=src['local_file'],company_ids=company,firm='Morningstar',analyst_name=s['author'],report_date=s['report_date'],retrieved_at=src['retrieved_at'],sha256=src['sha256'],status='verified_original_current_forecast_table',notes='Original Morningstar report distributed by Firstrade; retained current model only. See research for accounting limits.',text_file=src['text_file'],report_timestamp=s['timestamp'],model_dates=s['model'],http_status=200,report_month=s['report_date'][:7],report_date_precision='day',artifact_type='pdf'))

issuer_sources=[x for x in json.loads((BASE/'issuer_download_log.json').read_text()) if x.get('local_file')]
issuer_by_name={x['name']:x for x in issuer_sources}
actual_specs=[
 ('asml',2021,'2021-12-31','2022-01-19','14.34','EUR',1,None),
 ('asml',2022,'2022-12-31','2023-01-25','14.13','EUR',1,None),
 ('asml',2023,'2023-12-31','2024-01-24','19.89','EUR',1,None),
 ('asml',2024,'2024-12-31','2025-01-29','19.24','EUR',1,None),
 ('asml',2025,'2025-12-31','2026-01-28','24.71','EUR',3,None),
 ('nvidia',2026,'2026-01-25','2026-02-25','4.90','USD',None,3),
 ('sandisk',2025,'2025-06-27','2025-08-14','-11.32','USD',None,8),
 ('sandisk',2026,'2026-07-03','2026-08-05','73.76','USD',None,9),
]
outcomes=[]
for company,year,end,release,value,currency,page,table_no in actual_specs:
    source=issuer_by_name[f"{company}_fy{year}_{'statements' if company=='asml' else 'release'}"]
    assert sha(source['local_file'])==source['sha256']
    if company=='asml':
        table=(ROOT/source['text_file']).read_text().split('\f')[page-1]
        raw=next(x.strip() for x in table.splitlines() if x.startswith('Diluted net income per ordinary share'))
        assert numbers(raw)[-1]==value
        loc=f'Physical page{page}; US-GAAP consolidated statements of operations; twelve-month current-year {year} column; Diluted net income per ordinary share.'
        extra='Initial annual results financial statements linked by the issuer results page; companion same-day press release is also retained. This outcome is US-GAAP diluted, not basic or IFRS. Morningstar model EPS must remain separately scoped until historical denominator discrepancies are reconciled.'
    else:
        soup=BeautifulSoup((ROOT/source['local_file']).read_text(),'html.parser')
        t=soup.find_all('table')[table_no-1];table=t.get_text(' ',strip=True)
        if company=='sandisk' and year==2025:
            raw=next(x.get_text(' ',strip=True) for x in t.find_all('tr') if 'Basic and diluted' in x.get_text(' ',strip=True))
            assert '(11.32)' in raw and 'Year Ended' in table
        else:
            raw=next(x.get_text(' ',strip=True) for x in t.find_all('tr') if x.get_text(' ',strip=True).startswith('Diluted'))
            assert value in raw
        loc=f'HTML table{table_no} (1-based document order); consolidated statements of income/operations; current full-year {year} column; diluted EPS.'
        extra='Original issuer newsroom HTML, initial annual release. Retained current full-year column, not a later comparative restatement. '
        if company=='sandisk':extra+='Standalone security began trading in2025; pre-separation comparative history does not create a pre-IPO forecast or price history. '
        if company=='nvidia':extra+='Post-June2024 split units. FY2026 ends January25,2026, not calendar December2026. '
    oid=f'{company}_fy{year}_reported_diluted_initial_release'
    row=dict.fromkeys(OUT_FIELDS,'')
    row.update(outcome_id=oid,company_id=company,fiscal_period=f'FY{year}',fiscal_period_end=end,metric='eps_diluted',accounting_basis='reported_diluted',value=value,currency=currency,unit=currency+'_per_share',initial_release_date=release,share_basis_date=release,source_url=source['source_url'],source_file=source['local_file'],source_sha256=source['sha256'],source_page=page or '',source_locator=loc,definition='Annual U.S. GAAP diluted earnings per ordinary/common share in the initial annual earnings release, including all recognized GAAP items and the issuer diluted denominator.',definition_id=oid,definition_source_locator=loc,result_version='initial_annual_earnings_release',validation_status='verified_original_initial_release',raw_source_row=raw,notes=extra+' Exact historical dissemination time is not independently established; actual_available_at is blank.')
    outcomes.append(row)

write_csv('observations.csv',OBS_FIELDS,observations)
write_csv('manifest.csv',MAN_FIELDS,manifest)
write_csv('issuer_eps_outcomes.csv',OUT_FIELDS,outcomes)
issuer_fields=['company_id','fiscal_year','kind','source_url','local_file','text_file','sha256','retrieved_at','artifact_type','status']
write_csv('issuer_manifest.csv',issuer_fields,[{k:s.get(k,'') for k in issuer_fields} for s in issuer_sources])
assert len(observations)==30 and len(outcomes)==8
assert len({r['observation_id'] for r in observations})==30
assert len({r['outcome_id'] for r in outcomes})==8
assert all(not r['original_available_at'] and r['report_date']<='2026-09-10' for r in observations)
assert all(not r['actual_available_at'] and r['initial_release_date']<='2026-09-10' for r in outcomes)
(BASE/'validation.json').write_text(json.dumps(dict(forecast_rows=30,eps_forecasts=20,revenue_forecasts=10,issuer_eps_outcomes=8,broker_originals=2,issuer_originals=len(issuer_sources),source_hashes_verified=True,annual_columns_verified=True,availability_timestamps_assumed=False),indent=2)+'\n')
print((BASE/'validation.json').read_text())
