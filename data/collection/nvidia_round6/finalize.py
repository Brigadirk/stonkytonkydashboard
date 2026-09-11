"""Reproduce manually reviewed NVIDIA observations from retained originals."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
FIELDS = ['observation_id','company_id','firm','analyst_name','metric','fiscal_period',
          'value','currency','unit','basis','model_date','forecast_revision_as_of',
          'report_date','available_at','printed_report_timestamp','original_available_at',
          'availability_basis','source_url','local_file','page','status','notes',
          'forecast_type','source_type','source_period_label','share_basis_date','source_artifact_sha256']
MANIFEST = ['source_url','local_file','company_ids','firm','analyst_name','report_date',
            'retrieved_at','sha256','status','notes','text_file','report_timestamp',
            'model_dates','http_status','report_month','report_date_precision','artifact_type']

# Values retain printed share units. Only the February 8 template's fiscal labels
# are shifted, as independently reconciled in the same model's prior collection.
REVIEWED = {
    '20220208': dict(page=15, model='2022-02-08', analyst='Abhinav Davuluri',
                     years=[2023,2024,2025], raw=[2022,2023,2024],
                     eps=['5.04','6.00','7.23'], revenue=['32','38','44'], unit='USD_billion',
                     note='Earlier printed publication of the existing 8 Feb model. Source fiscal labels are one year low: historical USD17bn revenue is issuer FY2021, not printed FY2020. Fiscal identity agrees with the already reviewed 17 Feb reprint. Source labels retained; see fiscal_reconciliation.json.'),
    '20220515': dict(page=15, model='2022-02-16', analyst='Abhinav Davuluri',
                     years=[2023,2024,2025], raw=[2023,2024,2025],
                     eps=['5.12','6.10','7.30'], revenue=['33','38','45'], unit='USD_billion',
                     note='New retained model vintage. Model was already almost three months old when this report was printed. Revenue is rounded to whole USD billions as printed; do not infer more precision.'),
    '20240112': dict(page=17, model='2023-11-21', analyst='Brian Colello',
                     years=[2024,2025,2026], raw=[2024,2025,2026],
                     eps=['12.24','18.27','20.60'], revenue=['59126','85940','96894'], unit='USD_million',
                     note='Reprint of existing 21 Nov 2023 model; not a January forecast revision. Correct printed fiscal labels corroborate the fiscal mapping of the earlier November original with the exact same EPS and revenue vectors.'),
    '20240318': dict(page=17, model='2024-03-18', analyst='Brian Colello',
                     years=[2025,2026,2027], raw=[2025,2026,2027],
                     eps=['26.11','34.44','40.43'], revenue=['116338','152084','178435'], unit='USD_million',
                     note='New retained March model. Filename is 18 March, but printed report is 19 March UTC. Valuation narrative discusses adjusted EPS without explicitly relabelling this numerical row; no accounting-basis alias applied.'),
    '20240610': dict(page=15, model='2024-05-22', analyst='Brian Colello',
                     years=[2025,2026,2027], raw=[2025,2026,2027],
                     eps=['28.04','39.33','45.56'], revenue=['126173','172946','200331'], unit='USD_million',
                     note='June split trap: historical summary and fair-value estimate are post-split, but the retained May model is pre-10:1-split. Its exact EPS/revenue vector and 2489m diluted shares match the 23 May original. share_basis_date is explicitly 22 May; never use June report date to normalize these EPS values.'),
}

def write_csv(path, fields, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    logs = {}
    for file in sorted(BASE.glob('discovery_round*.json')):
        for row in json.loads(file.read_text()):
            if row.get('local_file'):
                logs[row['key'].rsplit('_',1)[-1]] = row
    manifests, observations = [], []
    for day, config in REVIEWED.items():
        log = logs[day]
        raw = (ROOT / log['local_file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == log['sha256']
        source_text = (ROOT / log['text_file']).read_text()
        printed = re.search(r'Report as of\s+(\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC', source_text).group(1)
        timestamp = datetime.strptime(printed,'%d %b %Y %H:%M').replace(tzinfo=timezone.utc)
        page = source_text.split('\f')[config['page']-1]
        block = page.split('Morningstar Analyst Historical/Forecast Summary as of ')[1]
        assert datetime.strptime(block.splitlines()[0],'%d %b %Y').date().isoformat() == config['model']
        lines = block.splitlines()
        eps_line = next(line for line in lines if line.startswith('Diluted Earnings Per Share'))
        revenue_line = next(line for line in lines if line.startswith('Revenue ('))
        year_line = next(line for line in lines if line.startswith('Fiscal Year,'))
        assert list(map(int,re.findall(r'\b20\d{2}\b',year_line)[-3:])) == config['raw']
        assert re.findall(r'-?\d[\d,]*\.\d+', eps_line)[-3:] == config['eps']
        values = re.findall(r'-?\d[\d,]*(?:\.\d+)?',revenue_line.split(')')[1].split('Price/')[0])[-3:]
        assert [value.replace(',','') for value in values] == config['revenue']
        note = ('Printed report timestamp is not independently verified original availability. '
                'EPS adjustment definition remains unresolved; no issuer non-GAAP equivalence asserted. '
                'All EPS values are post-July-2021 four-for-one and pre-June-2024 ten-for-one. ' + config['note'])
        manifest = dict.fromkeys(MANIFEST,'')
        manifest.update({key: log[key] for key in ['source_url','local_file','retrieved_at','sha256','http_status','text_file']})
        manifest.update(company_ids='nvidia',firm='Morningstar',analyst_name=config['analyst'],
                        report_date=timestamp.date().isoformat(),report_timestamp=timestamp.isoformat(),
                        report_month=timestamp.strftime('%Y-%m'),report_date_precision='day',
                        model_dates=config['model'],status='extracted_table_pending_basis_match',artifact_type='pdf',notes=note)
        manifests.append(manifest)
        for metric, vals, unit, basis in [
                ('eps_diluted_basis_unresolved',config['eps'],'USD_per_share','diluted_adjustment_basis_unresolved'),
                ('revenue',config['revenue'],config['unit'],'total_revenue')]:
            for year, raw_year, value in zip(config['years'],config['raw'],vals):
                row = dict.fromkeys(FIELDS,'')
                row.update(company_id='nvidia',firm='Morningstar',analyst_name=config['analyst'],
                           metric=metric,fiscal_period=f'FY{year}',source_period_label=f'FY{raw_year}',
                           value=value,currency='USD',unit=unit,basis=basis,model_date=config['model'],
                           forecast_revision_as_of=config['model'],share_basis_date=config['model'],
                           report_date=manifest['report_date'],printed_report_timestamp=timestamp.isoformat(),
                           availability_basis='printed_report_timestamp_not_independently_verified',
                           source_url=log['source_url'],local_file=log['local_file'],page=str(config['page']),
                           source_artifact_sha256=log['sha256'],status='extracted_table_pending_basis_match',notes=note,
                           forecast_type='analyst_forecast',source_type='individual_analyst_forecast')
                row['observation_id'] = hashlib.sha256(f"{log['sha256']}|{metric}|{year}".encode()).hexdigest()[:24]
                observations.append(row)
    write_csv(BASE/'manifest.csv',MANIFEST,manifests)
    write_csv(BASE/'observations.csv',FIELDS,observations)
    assert len({row['observation_id'] for row in observations}) == 30
    summary = dict(original_pdfs=len(manifests),observations=len(observations),eps_observations=15,
                   revenue_observations=15,distinct_model_dates=5,new_model_dates=['2022-02-16','2024-03-18'],
                   newly_proven_basis_aliases=0,independently_verified_original_availability=False,
                   source_hashes_and_exact_table_vectors_verified=True)
    (BASE/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
