"""Extract reviewed table shapes; preserve source dates, units, and duplicates."""
from pathlib import Path
from datetime import datetime
import csv
import hashlib
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
FIELDS = ['observation_id','company_id','firm','analyst_name','metric','fiscal_period',
          'value','currency','unit','basis','model_date','forecast_revision_as_of',
          'report_date','available_at','printed_report_timestamp','original_available_at',
          'availability_basis','source_url','local_file','page','status','notes']

def day(s):
    for fmt in ('%d %b %Y','%d %B %Y'):
        try:
            return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:
            pass
    return ''

def main():
    manifest = list(csv.DictReader((BASE/'manifest.csv').open()))
    observations = []
    for row in manifest:
        filename = Path(row['local_file']).name if row['local_file'] else ''
        if not filename.startswith('morningstar_') or row['firm'] != 'Morningstar':
            continue
        if not row['text_file'] or not filename.startswith(('morningstar_AVGO_', 'morningstar_MU_', 'morningstar_NVDA_', 'morningstar_GOOG_','morningstar_GOOGL_')):
            continue
        text = (ROOT/row['text_file']).read_text()
        for page_number, page in enumerate(text.split('\f'),1):
            modern = re.search(r'Financials as of\s+(\d+ [A-Za-z]+ \d{4})\s+Actual\s+Forecast',page)
            legacy = re.search(r'Morningstar Analyst Historical/Forecast Summary as of\s+(\d+ [A-Za-z]+ \d{4})',page)
            if not (modern or legacy):
                continue
            marker = modern or legacy
            block = page[marker.start():]
            year_line = next(line for line in block.splitlines() if line.startswith('Fiscal Year,'))
            years = re.findall(r'\b20\d{2}\b',year_line)
            if legacy:
                years = years[-5:]
                start = 2
            else:
                years = years[-8:]
                start = 3
            patterns = [('revenue', r'^Revenue \(USD Mil\)', 'USD_million', 'total_revenue'),
                        ('eps_diluted', r'^Earnings Per Share \(Diluted\) \(USD\)', 'USD_per_share', 'reported_diluted'),
                        ('eps_adjusted_diluted', r'^Adjusted Earnings Per Share \(Diluted\) \(USD\)', 'USD_per_share', 'adjusted_diluted'),
                        ('eps_diluted_basis_unresolved', r'^Diluted Earnings Per Share\(USD\)', 'USD_per_share', 'diluted_adjustment_basis_unresolved')]
            for metric, pattern, unit, basis in patterns:
                line = next((line for line in block.splitlines() if re.match(pattern,line)),None)
                if line is None:
                    continue
                tail = re.sub(pattern,'',line)
                values = re.findall(r'-?\d[\d,]*(?:\.\d+)?',tail)[:len(years)]
                if len(values) != len(years):
                    raise ValueError(f'Unexpected table width: {filename}: {line}')
                for year, value in list(zip(years,values))[start:]:
                    status = 'extracted_table_pending_basis_match'
                    notes = 'Printed report timestamp is not independently verified original public availability. Values remain in printed units.'
                    if 'MU_202409' in filename:
                        status = 'quarantined_fiscal_header_mismatch'
                        notes += ' Source forecast summary says fiscal year ends 31 Oct; Micron fiscal-year mapping requires reconciliation.'
                    observations.append(dict(
                        observation_id=hashlib.sha256(f'{filename}|{metric}|{year}'.encode()).hexdigest()[:20],
                        company_id=row['company_ids'],firm=row['firm'],analyst_name=row['analyst_name'],
                        metric=metric,fiscal_period='FY'+year,value=value.replace(',',''),currency='USD',unit=unit,basis=basis,
                        model_date=day(marker.group(1)),forecast_revision_as_of=row['model_dates'],report_date=row['report_date'],
                        available_at='',printed_report_timestamp=row['report_timestamp'],original_available_at='',
                        availability_basis='printed_report_timestamp_not_independently_verified',source_url=row['source_url'],local_file=row['local_file'],
                        page=page_number,status=status,notes=notes))
    with (BASE/'observations.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader();writer.writerows(observations)
    print('Extracted table observations:',len(observations))

if __name__ == '__main__':
    main()
