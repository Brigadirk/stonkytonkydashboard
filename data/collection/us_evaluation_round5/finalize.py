"""Reproduce reviewed first-release EPS outcomes from the retained originals (offline)."""
from pathlib import Path
from datetime import date
import csv, hashlib, json, re
from bs4 import BeautifulSoup

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
# Fiscal end, first annual release date, GAAP diluted EPS, issuer non-GAAP diluted EPS.
REVIEW = {
 'broadcom': {
 2021: ('2021-10-31','2021-12-09','15.00','28.01'),
 2022: ('2022-10-30','2022-12-08','26.53','37.64'),
 2023: ('2023-10-29','2023-12-07','32.98','42.25'),
 2024: ('2024-11-03','2024-12-12','1.23','4.87'),
 2025: ('2025-11-02','2025-12-11','4.77','6.82')},
 'alphabet': {
 2021: ('2021-12-31','2022-02-01','112.20',None),
 2022: ('2022-12-31','2023-02-02','4.56',None),
 2023: ('2023-12-31','2024-01-30','5.80',None),
 2024: ('2024-12-31','2025-02-04','8.04',None),
 2025: ('2025-12-31','2026-02-04','10.81',None)},
 'nvidia': {
 2021: ('2021-01-31','2021-02-24','6.90','10.00'),
 2022: ('2022-01-30','2022-02-16','3.85','4.44'),
 2023: ('2023-01-29','2023-02-22','1.74','3.34'),
 2024: ('2024-01-28','2024-02-21','11.93','12.96'),
 2025: ('2025-01-26','2025-02-26','2.94','2.99')},
 'micron': {
 2021: ('2021-09-02','2021-09-28','5.14','6.06'),
 2022: ('2022-09-01','2022-09-29','7.75','8.35'),
 2023: ('2023-08-31','2023-09-27','-5.34','-4.45'),
 2024: ('2024-08-29','2024-09-25','0.70','1.30'),
 2025: ('2025-08-28','2025-09-23','7.59','8.29')},
}
# Describes only the particular annual reconciliation; no cross-vintage equivalence is implied.
NG_ITEMS = {
 'broadcom': {
 2021: 'Acquisition-related intangible amortization; stock-based compensation; restructuring, impairment and disposal charges; litigation settlements; acquisition-related costs; debt-extinguishment losses; investment gains/losses; business-sale gains; non-GAAP tax adjustments.',
 2022: 'Acquisition-related intangible amortization; stock-based compensation; restructuring, impairment and disposal charges; acquisition-related costs; debt-extinguishment losses; investment gains/losses; non-GAAP tax adjustments.',
 2023: 'Acquisition-related intangible amortization; stock-based compensation; restructuring and other charges; acquisition-related costs; investment gains/losses; non-GAAP tax adjustments.',
 2024: 'Acquisition-related intangible amortization; stock-based compensation; restructuring and other charges; acquisition-related costs; debt-extinguishment losses; investment gains/losses; non-GAAP tax adjustments including the IP-transfer tax provision; discontinued operations.',
 2025: 'Acquisition-related intangible amortization; stock-based compensation; restructuring and other charges; acquisition-related costs; debt-extinguishment losses; investment gains/losses; business-sale gain; non-GAAP tax adjustments.'},
 'nvidia': {
 2021: 'Acquisition-related and other costs; stock-based compensation; investment gains/losses; debt-discount amortization; income-tax impact of non-GAAP adjustments.',
 2022: 'Acquisition-related and other costs; stock-based compensation; investment gains/losses; debt-discount amortization; income-tax impact of non-GAAP adjustments; domestication tax adjustments; foreign tax benefit.',
 2023: 'Acquisition-related and other costs; stock-based compensation; restructuring and other costs; acquisition-termination cost; investment gains/losses; debt-discount amortization; income-tax impact of non-GAAP adjustments.',
 2024: 'Acquisition-related and other costs; stock-based compensation; other adjustments; investment gains/losses; debt-discount amortization; income-tax impact of non-GAAP adjustments.',
 2025: 'Acquisition-related and other costs; stock-based compensation; other adjustments; gains on non-marketable and publicly held equity securities; debt-discount amortization; income-tax impact of non-GAAP adjustments.'},
 'micron': {
 2021: 'Stock-based compensation; FIFO accounting-policy change; inventory cost-absorption change; 3D XPoint inventory write-down; restructuring and asset impairments; patent-license charges; debt-discount amortization and other costs; debt repurchases/conversions; other; estimated tax effects and other tax adjustments.',
 2022: 'Stock-based compensation; restructuring and asset impairments; debt-discount amortization; debt repurchases/conversions; other; Idaho tax reform; estimated tax effects and other tax adjustments.',
 2023: 'Stock-based compensation; restructuring and asset impairments; goodwill impairment; litigation settlement; other; estimated tax effects and other tax adjustments.',
 2024: 'Stock-based compensation; restructuring and asset impairments; patent cross-license agreement gain; estimated tax effects and other tax adjustments.',
 2025: 'Stock-based compensation; restructuring and asset impairments; debt-prepayment losses; patent-license charges; other; estimated tax effects and other tax adjustments.'},
}
F = ['outcome_id','company_id','fiscal_period','fiscal_period_end','metric','accounting_basis','value','currency','unit','initial_release_date','actual_available_at','share_basis_date','source_url','source_file','source_sha256','source_page','source_locator','definition','definition_id','definition_source_locator','result_version','validation_status','raw_source_row','notes']
manifest = {m['source_id']:m for m in csv.DictReader((B/'issuer_manifest.csv').open())}
rows, definitions, validations = [], [], []

def clean(s): return ' '.join(s.split())
def nums(s):
 return [float(x.replace(' ','').replace('(','-').replace(')','')) for x in re.findall(r'\(\s*\d+\.\d+\s*\)|\d+\.\d+',s)]

def split_note(c,y):
 if c=='broadcom':return 'As initially printed: pre-July 2024 10:1 split.' if y<2024 else 'As initially printed: reflects July 2024 10:1 split.'
 if c=='alphabet':return 'As initially printed: pre-July 2022 20:1 split.' if y==2021 else 'As initially printed: reflects July 2022 20:1 split.'
 if c=='nvidia':return 'As initially printed: before July 2021 4:1 and June 2024 10:1 splits.' if y==2021 else 'As initially printed: after July 2021 4:1, before June 2024 10:1 split.' if y<2025 else 'As initially printed: after July 2021 4:1 and June 2024 10:1 splits.'
 return 'As initially printed; no split in the collected 2021-2025 period.'

for c,years in REVIEW.items():
 for y,(end,released,gaap,ng) in years.items():
  sid=f'{c}_fy{y}';m=manifest[sid];p=B/m['source_file'];digest=hashlib.sha256(p.read_bytes()).hexdigest()
  assert digest==m['source_sha256'] and m['status']=='downloaded_text_extracted', sid
  assert end<released<='2026-09-10'
  txt=(B/m['text_file']).read_text();raws={};locs={};page=''
  if c=='alphabet':
   p1=txt.split('\f')[0];page='1'
   epsline=next(l for l in p1.splitlines() if re.search(r'Diluted (?:(?:earnings|net income) per share|EPS)',l,re.I))
   assert nums(epsline)[-1]==float(gaap),(sid,epsline)
   raw=clean(epsline);raws['reported_diluted']=raw
   locs['reported_diluted']=f'Physical PDF page 1; annual {y} column in financial highlights; {raw.split("$")[0].strip()} row.'
   release_dt=date.fromisoformat(released)
   assert re.search(rf'{release_dt.strftime("%B")}\s+0?{release_dt.day},?\s+{release_dt.year}',p1), sid
  else:
   s=BeautifulSoup(p.read_bytes(),'html.parser');tables=s.find_all('table')
   for basis,value in [('reported_diluted',gaap),('non_gaap_diluted',ng)]:
    tn=(4 if y<2024 else 5) if c=='broadcom' else (3 if basis=='reported_diluted' else 4) if c=='nvidia' else 2
    table=tables[tn-1];tt=clean(table.get_text(' ',strip=True));assert re.search(rf'FY[ -]?{str(y)[2:]}',tt),sid
    tr=next(r for r in table.find_all('tr') if re.match(r'(?:Earnings per common share - diluted|Diluted earnings(?: \(loss\))? per share)',r.get_text(' ',strip=True)))
    raw=clean(tr.get_text(' ',strip=True));values=nums(raw)
    pos=0 if basis=='reported_diluted' or c=='nvidia' else (3 if c=='broadcom' and y<2025 else 2)
    assert values[pos]==float(value),(sid,basis,raw,values,pos,value)
    raws[basis]=raw
    locs[basis]=f'HTML table {tn} (1-based document order); FY{y} {"GAAP" if basis=="reported_diluted" else "Non-GAAP"} current-year column; diluted EPS row.'
  for basis,value in [('reported_diluted',gaap),('non_gaap_diluted',ng)]:
   if value is None: continue
   did=f'{c}_fy{y}_{basis}_initial_release'
   if basis=='reported_diluted':
    definition='Annual U.S. GAAP diluted earnings per common share, as reported in the initial annual earnings release, including all items recognized under GAAP in that release.'
    dloc=locs[basis]
    exact_reconciliation=''
   else:
    rt=9 if c=='broadcom' else 8 if c=='nvidia' else {2021:8,2022:7,2023:9,2024:9,2025:9}[y]
    exact_reconciliation=clean(tables[rt-1].get_text(' ',strip=True))
    assert 'non-gaap' in exact_reconciliation.lower() and 'net income' in exact_reconciliation.lower(),sid
    denominator = ('Uses the separately reconciled non-GAAP diluted share count, which reverses the GAAP treasury-stock-method treatment of unrecognized future stock compensation.' if c=='broadcom' else 'Uses the diluted weighted-average share count shown in the reconciliation.' if c=='nvidia' else 'Uses the separately reconciled non-GAAP diluted share count, including the stated stock-compensation adjustment'+(' and capped-call adjustment.' if y==2021 else ' (zero for the FY2023 loss).' if y==2023 else '.'))
    definition=f'Issuer-defined annual non-GAAP diluted EPS. Current-year net-income reconciling items: {NG_ITEMS[c][y]} {denominator} Exact amounts, signs, footnotes and comparative-year items remain in the cited original reconciliation. This definition is specific to this release; it is not a broker-adjusted EPS equivalence.'
    dloc=f'HTML table {rt}; GAAP-to-non-GAAP reconciliation, annual current-year column, net-income and diluted-EPS/share-count rows and footnotes.'
   row=dict(zip(F,['']*len(F)))
   row.update(outcome_id=did,company_id=c,fiscal_period=f'FY{y}',fiscal_period_end=end,metric='eps_diluted' if basis=='reported_diluted' else 'eps_non_gaap_diluted',accounting_basis=basis,value=value,currency='USD',unit='USD_per_share',initial_release_date=released,share_basis_date=released,source_url=m['source_url'],source_file=str(p.relative_to(ROOT)),source_sha256=digest,source_page=page,source_locator=locs[basis],definition=definition,definition_id=did,definition_source_locator=dloc,result_version='initial_annual_earnings_release',validation_status='verified_original_initial_release',raw_source_row=raws[basis],notes=split_note(c,y)+' Share-basis date identifies the printed split epoch, not historical dissemination time. Exact availability time unproven. '+m['notes'])
   if c=='alphabet':row['notes']+=' No issuer non-GAAP EPS was identified in this release; do not manufacture one from GAAP EPS.'
   rows.append(row)
   definitions.append({'definition_id':did,'company_id':c,'accounting_basis':basis,'fiscal_period':f'FY{y}','definition':definition,'source_url':m['source_url'],'source_sha256':digest,'source_locator':dloc,'retained_reconciliation_text':exact_reconciliation})
  validations.append({'source_id':sid,'hash_verified':True,'annual_eps_row_verified':True,'values':{'reported_diluted':gaap,'non_gaap_diluted':ng},'initial_release_date':released,'fiscal_period_end':end})
with (B/'issuer_eps_outcomes.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=F);w.writeheader();w.writerows(rows)
(B/'issuer_eps_definitions.json').write_text(json.dumps(definitions,indent=2)+'\n')
(B/'validation.json').write_text(json.dumps({'original_releases':len(manifest),'eps_outcomes':len(rows),'issuer_gaap_outcomes':20,'issuer_non_gaap_outcomes':15,'exact_actual_availability_timestamps_proven':0,'checks':validations},indent=2)+'\n')
assert len(rows)==35 and len({r['outcome_id'] for r in rows})==35
print(f'Validated {len(manifest)} originals; wrote {len(rows)} EPS actuals and release-specific definitions.')
