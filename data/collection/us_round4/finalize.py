"""Reproduce reviewed public broker forecasts without network access."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
FIELDS = ['observation_id','company_id','firm','analyst_name','metric','fiscal_period',
          'value','currency','unit','basis','model_date','forecast_revision_as_of',
          'report_date','available_at','printed_report_timestamp','original_available_at',
          'availability_basis','source_url','local_file','page','status','notes',
          'source_period_label','share_basis_date','source_artifact_sha256']
MANIFEST = ['source_url','local_file','company_ids','firm','analyst_name','report_date',
            'retrieved_at','sha256','status','notes','text_file','report_timestamp',
            'model_dates','http_status','report_month','report_date_precision','artifact_type']
COMPANIES = {'AVGO':'broadcom','GOOGL':'alphabet','NVDA':'nvidia','MU':'micron'}
NAME_PAT = r'\s+([^\n]+?),(?: CFA,| CPA,)?\s*(?:Senior Equity Analyst|Equity Analyst|Analyst|Sector Strategist|Sector Director|Strategist|Director)'
SPLITS = {'AVGO':'2024-07-15','NVDA':'2024-06-10','GOOGL':'2022-07-18'}
SHIFTS = {'NVDA_20220216':1,'NVDA_20230223':1,'NVDA_20230524':1,
          'NVDA_20230823':1,'NVDA_20231121':1,'GOOGL_20230202':-1,'MU_20230328':-1,'MU_20211220':-1}

def day(s):
    return datetime.strptime(s, '%d %b %Y').date().isoformat()

def write_csv(path, fields, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    logs=json.loads((BASE/'download_log.json').read_text())
    manifests=[]; observations=[]
    for log in logs:
        row=dict.fromkeys(MANIFEST,'')
        row.update({k:log[k] for k in ('source_url','local_file','retrieved_at','sha256','http_status') if k in log})
        row['notes']=log.get('discovery','Original BOCOM PDF and embedded broker download link.')
        if not row['local_file']:
            row['status']='public_url_not_found_or_download_failed';row['notes']+=' '+log.get('error','')
            manifests.append(row);continue
        p=ROOT/row['local_file']; assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        text_path=BASE/'text'/f'{p.stem}.txt'; text=text_path.read_text()
        row.update(text_file=str(text_path.relative_to(ROOT)),artifact_type='pdf')
        if not p.stem.startswith('morningstar_'):
            row.update(firm='BOCOM International',company_ids='broadcom' if '260608' in p.stem else '',
                       analyst_name='Dawei Wang' if 'mexp_260608' in p.stem else '',
                       status='retained_corroborating_original' if '260608' in p.stem else 'excluded_no_target_forecast_identified')
            if '260608' in p.stem:row.update(report_date='2026-06-08',report_month='2026-06',report_date_precision='day')
            if p.stem=='bocom_mexp_260608':
                row['status']='downloaded_forecast_values_verified'
                page=text.split('\f')[0]
                for metric,vals,unit,basis in [('eps',['12.02','18.95','24.59'],'USD_per_share','non_gaap_diluted'),
                                              ('revenue',['106.8','164.3','213.3'],'USD_billion','total_revenue')]:
                    for year,value in zip(range(2026,2029),vals):
                        assert value in page
                        obs=dict.fromkeys(FIELDS,'')
                        obs.update(company_id='broadcom',firm=row['firm'],analyst_name='Dawei Wang',metric=metric,
                                   fiscal_period=f'FY{year}',source_period_label=f'FY{year}',value=value,currency='USD',unit=unit,basis=basis,
                                   report_date=row['report_date'],availability_basis='printed_report_timestamp_not_independently_verified',
                                   source_url=row['source_url'],local_file=row['local_file'],page='1',status='extracted_sample_pending_basis_match',
                                   share_basis_date=row['report_date'],source_artifact_sha256=row['sha256'],
                                   notes='English broker summary attributed to Dawei Wang. Full original Chinese model retained separately; page 3 confirms diluted EPS. Revenue is rounded as printed in summary; exact full-model revenue is not counted as a second forecast. Original dissemination time and independent model timestamp unverified.')
                        obs['observation_id']=hashlib.sha256(f'{row["sha256"]}|{metric}|{year}'.encode()).hexdigest()[:20]
                        observations.append(obs)
            manifests.append(row);continue
        _,ticker,date_hint=p.stem.split('_')
        label=f'{ticker}_{date_hint}'
        report=re.search(r'Report as of\s+(\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC',text)
        assert report, label
        dt=datetime.strptime(report.group(1),'%d %b %Y %H:%M').replace(tzinfo=timezone.utc)
        assert dt.date().isoformat()<='2026-09-10'
        author=None
        for heading in ('Analyst Note','Fair Value and Profit Drivers','Business Strategy & Outlook'):
            author=re.search(heading+NAME_PAT,text)
            if author:break
        assert author, label
        row.update(company_ids=COMPANIES[ticker],firm='Morningstar',analyst_name=author.group(1).strip(),
                   report_date=dt.date().isoformat(),report_timestamp=dt.isoformat(),report_month=dt.strftime('%Y-%m'),
                   report_date_precision='day',status='retained_no_numerical_model_table')
        for page_no,page in enumerate(text.split('\f'),1):
            modern=re.search(r'Financials as of\s+(\d+ [A-Za-z]+ \d{4})\s+Actual\s+Forecast',page)
            legacy=re.search(r'Morningstar Analyst Historical/Forecast Summary as of\s+(\d+ [A-Za-z]+ \d{4})',page)
            marker=modern or legacy
            if not marker:continue
            block=page[marker.start():];lines=block.splitlines()
            year_line=next(l for l in lines if l.startswith('Fiscal Year,'))
            years=re.findall(r'\b20\d{2}\b',year_line)[- (5 if legacy else 8):]
            start=2 if legacy else 3
            model_date=day(marker.group(1)); assert model_date<=row['report_date'],label
            row['model_dates']=model_date
            notes='Printed report timestamp is not independently verified original availability. Numerical model date is taken from the financial table, not the current analyst note. Printed share units retained; no split adjustment in this CSV.'
            if ticker=='NVDA' and row['report_date']>='2026-02-25':
                notes+=' NVIDIA began including stock-based compensation in its non-GAAP measures in FY2027 Q1. Morningstar labels adjusted EPS without a separate SBC definition here; cross-vintage accounting comparability remains unverified.'
            status='extracted_table_pending_basis_match'
            if label in ('AVGO_20211209','AVGO_20220303'):
                status='quarantined_internal_conflict_fiscal_year_and_eps_vector'
                notes+=' December 2021 model has inconsistent historical-year labels and repeated EPS across different years; not eligible for plotted bands pending reconciliation.'
            if label in SHIFTS:
                shift=SHIFTS[label]
                notes+=f' Fiscal labels mapped by {shift:+d} year after comparing the two historical revenue columns with the same report company financials and issuer fiscal calendar; source labels retained. See US_ROUND4.md for reconciliation evidence.'
            if ticker=='MU' and 'Oct' in year_line:
                notes+=' Printed month-end header says October in error. Historical revenue columns identify FY2023=15540 USDm (and FY2024=25111 USDm where actual); fiscal year labels are retained and issuer August calendar governs period ends.'
            if ticker=='GOOGL' and '31 Mar' in year_line:
                notes+=' Printed header says March in error. Historical revenue columns identify FY2022=282836 USDm and FY2023=307394 USDm; annual year labels retained and issuer December calendar governs period ends.'
            if ticker in SPLITS and model_date<SPLITS[ticker]<=row['report_date']:
                status='quarantined_share_basis_crosses_split'
                notes+=' Report/model interval crosses a stock split; share basis not assumed.'
            if label=='AVGO_20230602':
                notes+=' Current analyst note is signed William Kerwin; business-strategy/fair-value sections dated May25 remain signed Brian Colello. June1 numerical model author not independently named.'
                status='quarantined_attribution_review_model_author_transition'
            row['status']='downloaded_forecast_tables_verified' if not status.startswith('quarantined') else 'downloaded_tables_quarantined'
            patterns=[('revenue',r'^Revenue \(USD Mil\)','USD_million','total_revenue'),
                      ('revenue',r'^Revenue \(USD Bil\)','USD_billion','total_revenue'),
                      ('eps_diluted',r'^Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','reported_diluted'),
                      ('eps_adjusted_diluted',r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)','USD_per_share','adjusted_diluted'),
                      ('eps_diluted_basis_unresolved',r'^Diluted Earnings Per Share\(USD\)','USD_per_share','diluted_adjustment_basis_unresolved')]
            for metric,pattern,unit,basis in patterns:
                line=next((l for l in lines if re.match(pattern,l)),None)
                if line is None:continue
                vals=re.findall(r'-?\d[\d,]*(?:\.\d+)?',re.sub(pattern,'',line))[:len(years)]
                assert len(vals)==len(years),(label,line)
                for y,value in list(zip(years,vals))[start:]:
                    obs=dict.fromkeys(FIELDS,'')
                    obs.update(company_id=row['company_ids'],firm='Morningstar',analyst_name=row['analyst_name'],metric=metric,
                               fiscal_period=f'FY{int(y)+SHIFTS.get(label,0)}',source_period_label=f'FY{y}',value=value.replace(',',''),
                               currency='USD',unit=unit,basis=basis,model_date=model_date,forecast_revision_as_of=model_date,
                               report_date=row['report_date'],printed_report_timestamp=row['report_timestamp'],
                               availability_basis='printed_report_timestamp_not_independently_verified',source_url=row['source_url'],
                               local_file=row['local_file'],page=str(page_no),status=status,notes=notes,
                               share_basis_date=model_date,source_artifact_sha256=row['sha256'])
                    obs['observation_id']=hashlib.sha256(f'{row["sha256"]}|{page_no}|{metric}|{y}'.encode()).hexdigest()[:20]
                    observations.append(obs)
        manifests.append(row)
    assert len({r['observation_id'] for r in observations})==len(observations)
    write_csv(BASE/'manifest.csv',MANIFEST,manifests)
    write_csv(BASE/'observations.csv',FIELDS,observations)
    stats={'attempts':len(manifests),'retained_pdfs':sum(bool(r['local_file']) for r in manifests),
           'observations':len(observations),'quarantined':sum(r['status'].startswith('quarantined') for r in observations),
           'by_company':dict(Counter(r['company_id'] for r in observations)),
           'eps_observations':sum(r['metric'].startswith('eps') for r in observations)}
    (BASE/'summary.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))

if __name__=='__main__':main()
