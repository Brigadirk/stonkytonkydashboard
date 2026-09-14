#!/usr/bin/env python3
"""Build a display-only annual EPS list. Never score adjusted forecasts."""
from pathlib import Path
import csv
import json
import re

ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[2]
manifest=json.loads((ROOT/'manifest.json').read_text())
filings=json.loads((ROOT/'filing_downloads.json').read_text())
allrows=json.loads((ROOT/'annual_latest_vintage.json').read_text())
ids={r['listing_symbol']:r['company_id'] for r in csv.DictReader((APP/'data/universe.csv').open())}

NOTES={
 'CBRS':['Annual results are from before the May 2026 IPO. Share counts and participating preferred shares differ from the listed capital structure.','The 2025 diluted EPS is USD 1.38 under GAAP. The prospectus also gives USD 0.42 pro forma diluted EPS; that different measure is excluded.','The 2022 and 2023 results are from the 2024 S-1. The 2024 and 2025 results are from the final 2026 prospectus.'],
 'SPCX':['Annual results cover fiscal periods before the June 2026 IPO. They include xAI and X on the common-control accounting basis stated in the final prospectus.','The prospectus adjusts all share figures for the five-for-one stock split effective May 4, 2026. Preferred-share participation and IPO conversions affect EPS comparability.','The reported 2024 diluted EPS rounds to USD 0.00; this is not a missing value.'],
 'TSM':['Each value is USD per ADS, directly reported in a Form 20-F. Each ADS represents five ordinary shares.','These are IFRS results as issued by the IASB. TSMC also issues Taiwan IFRS results with different EPS.','The issuer converts each year’s amounts at its stated year-end exchange rate for reader convenience. These USD/ADS figures are not the sum of quarterly press-release USD/ADS figures. Original TWD and ordinary-share facts remain in the raw files.'],
 'NBIS':['Only the 2024 and 2025 annual results are shown here. Earlier Yandex history remains in the raw files and is not a continuous history of the current AI cloud business.','The figures are total GAAP diluted EPS, including discontinued operations. In 2025, USD 0.33 total EPS includes USD 0.04 from continuing operations and USD 0.29 from discontinued operations.','The 2024 divestment and later business changes limit year-to-year comparison.'],
 'ANET':['Figures retain the share basis in each cited filing. The latest available 2020 and 2021 facts predate the December 2024 four-for-one stock split; those EPS values are not directly comparable with the 2022–2025 figures.'],
 'MRVL':['Fiscal years end in late January or early February. Period end dates, not filing fiscal-year metadata, identify these results.'],
 'MSFT':['The fiscal year ends June 30. These are total GAAP diluted earnings, including investment and other reported gains or losses.'],
 'ORCL':['The fiscal year ends May 31. These are GAAP diluted earnings; adjusted issuer guidance is a different measure.'],
 'AMZN':['These are total GAAP diluted earnings, including investment gains or losses. The cited later annual reports restate older comparative EPS for the 2022 stock split.'],
}

def manual(symbol,year,value,file,filing_date,accession,locator,unit='USD/shares',basis='US GAAP diluted EPS',share_basis='as reported in cited filing'):
 src=next(s for s in filings if s['file']==file)
 return dict(period_start=f'{year}-01-01',period_end=f'{year}-12-31',value=value,unit=unit,accounting_basis=basis,share_basis=share_basis,filing_date=filing_date,earnings_release_date=None,accession=accession,source_url=src['url'],source_file=str((ROOT/file).relative_to(APP)),source_sha256=src['sha256'],source_locator=locator,retrieved_at=src['retrieved_at'],validation_status='reported_annual_eps_manual_filing_extraction')

companies=[]
for src in manifest:
 s=src['symbol'];rows=[]
 for r in allrows:
  if r['symbol']!=s or s in ('TSM','CBRS','SPCX'):continue
  if s=='NBIS' and (r['period_end']<'2024-01-01' or r['unit']!='USD/shares'):continue
  rows.append(dict(period_start=r['period_start'],period_end=r['period_end'],value=r['value'],unit=r['unit'],accounting_basis='US GAAP diluted EPS',share_basis='as reported in cited filing',filing_date=r['filed'],earnings_release_date=None,accession=r['accession'],source_url=r['source_url'],source_file=str((ROOT/r['source_file']).relative_to(APP)),source_sha256=r['source_sha256'],source_locator=f"facts/{r['taxonomy']}/{r['tag']}/units/{r['unit']}; start={r['period_start']}; end={r['period_end']}; accession={r['accession']}",retrieved_at=r['retrieved_at'],validation_status='reported_sec_fact_latest_available_vintage'))
 if s=='CBRS':
  for year,value in [(2022,-4.28),(2023,-2.92)]:rows.append(manual(s,year,value,'CBRS_000162828024041596.html','2024-09-30','0001628280-24-041596','Note 7, Net Loss Per Share; annual basic and diluted EPS table'))
  for year,value in [(2024,-9.90),(2025,1.38)]:rows.append(manual(s,year,value,'CBRS_000162828026035214.html','2026-05-14','0001628280-26-035214','Consolidated Statements of Operations and Note 7, Net Income (Loss) Per Share; annual diluted row'))
 if s=='SPCX':
  for year,value in [(2023,-1.68),(2024,0.0),(2025,-1.69)]:rows.append(manual(s,year,value,'SPCX_000162828026042639.html','2026-06-12','0001628280-26-042639','Consolidated Statements of Operations, page F-6; Note 14, Earnings per Share, pages F-44–F-45',share_basis='five-for-one May 4, 2026 split reflected; pre-IPO participating preferred shares'))
 if s=='TSM':
  vals=[(2020,3.51,'0001193125-21-118512','2021-04-16'),(2021,4.12,'0001193125-22-104891','2022-04-14'),(2022,6.23,'0001193125-23-107214','2023-04-20'),(2023,5.36,'0001193125-24-099840','2024-04-18'),(2024,6.81,'0001193125-25-083423','2025-04-17'),(2025,10.43,'0001628280-26-025362','2026-04-16')]
  for year,value,acc,filed in vals:
   locator='Selected financial data, page 3; Basic/Diluted earnings per ADS equivalent, US$ column' if year==2020 else 'Consolidated Statements of Comprehensive Income, page F-7; Earnings per equivalent ADS, diluted row, US$ column'
   if year==2025:locator+='; Inline XBRL fact f-397, context c-9 (AmericanDepositarySharesMember), unit usdPerShare'
   rows.append(manual(s,year,value,f'TSM_{acc.replace("-","")}.html',filed,acc,locator,unit='USD/ADS',basis='IFRS (IASB) diluted EPS; issuer year-end FX translation',share_basis='one ADS represents five ordinary shares'))
 rows.sort(key=lambda r:r['period_end'])
 companies.append(dict(company_id=ids[s],symbol=s,entity_name=src['entity_name'],cik=src['cik'],notes=NOTES.get(s,[]),annual_eps=rows))

output=dict(cutoff='2026-09-11',since='2020-09-10',availability_basis='SEC filing dates only; no earnings-release dates inferred',purpose='Display reported annual diluted EPS separately from adjusted forecasts. These rows do not score forecasts or calculate valuation targets.',companies=companies)
(ROOT/'annual_latest.json').write_text(json.dumps(output,indent=2)+'\n')
for company in companies:
 assert company['annual_eps'],company['symbol']
 for row in company['annual_eps']:
  assert row['filing_date']<=output['cutoff']
  assert (APP/row['source_file']).is_file(),row['source_file']
print(json.dumps({'companies':len(companies),'annual_rows':sum(len(c['annual_eps']) for c in companies),'latest':[{c['symbol']:c['annual_eps'][-1]['value']} for c in companies]}))
