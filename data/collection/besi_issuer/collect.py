"""Retain the issuer evidence for BESI's listing and fiscal calendar."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess
import requests

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
SOURCES=[
    ('share_information','https://www.besi.com/investor-relations/share-information/','issuer_listing',''),
    ('annual_report_2025','https://www.besi.com/fileadmin/data/Investor_Relations/_Semi__Annual_Reports/Annual_Report_2025.pdf','issuer_annual_report',''),
    ('financial_reports','https://www.besi.com/investor-relations/financial-reports-and-publications/financial-reports/','issuer_report_index',''),
]

def collect(source):
    name,url,kind,report_date=source
    response=requests.get(url,timeout=30)
    response.raise_for_status()
    pdf=response.content.startswith(b'%PDF')
    if name=='annual_report_2025' and not pdf:
        raise ValueError('Annual report response is not a PDF')
    digest=hashlib.sha256(response.content).hexdigest()
    path=BASE/'originals'/(name+'_'+digest[:12]+('.pdf' if pdf else '.html'))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        assert path.read_bytes()==response.content
    else:
        path.write_bytes(response.content)
    text_file=''
    if pdf:
        target=path.with_suffix('.txt')
        subprocess.run(['pdftotext','-layout',str(path),str(target)],check=True,capture_output=True)
        text_file=str(target.relative_to(ROOT))
    return dict(company_ids='besi',source_url=url,document_kind=kind,firm='BE Semiconductor Industries',analyst_name='',
                report_date=report_date,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=digest,
                local_file=str(path.relative_to(ROOT)),text_file=text_file,status='retained_issuer_source',
                notes='Primary issuer evidence for Amsterdam ordinary shares and December31 fiscal year. Original historical availability is not asserted.')

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(collect,SOURCES))
    with (BASE/'manifest.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    print(f'Retained {len(rows)} BESI issuer sources')
