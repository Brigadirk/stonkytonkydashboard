#!/usr/bin/env python3
"""Reproduce reviewed First Shanghai tables from immutable public originals.

Run offline. Text cells are checked against retained PDF extraction. The Micron
table is a raster image: its transcription was visually reviewed and its exact
source PDF and rendered page hashes are checked, without inventing OCR evidence.
"""
import csv
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OBS_FIELDS = 'observation_id,company_id,firm,analyst_name,source_type,metric,fiscal_period,value,currency,unit,basis,model_date,report_date,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MAN_FIELDS = 'collection,source_url,company_ids,document_kind,firm,analyst_name,report_date,retrieved_at,sha256,local_file,text_file,status,notes'.split(',')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    models = json.loads((BASE / 'verified_transcriptions.json').read_text())
    observations, manifest = [], []
    for model in models:
        source = ROOT / model['local_file']
        assert digest(source) == model['sha256']
        image = ROOT / model['review_image']
        assert digest(image) == model['review_image_sha256']
        text = (ROOT / model['text_file']).read_text()
        compact = re.sub(r'\s+', '', text.split('\f')[model['page'] - 1])
        if model['extraction'] == 'pdf_text_and_visual_review':
            for fragment in model['exact_table_fragments']:
                assert re.sub(r'\s+', '', fragment) in compact, fragment
        else:
            assert model['extraction'] == 'manual_visual_review_of_raster_table'
        for metric, values, basis, unit in [
            ('eps', model['eps'], model['basis'], 'USD_per_share'),
            ('revenue', model['revenue'], 'revenue_as_printed', 'USD_million'),
        ]:
            for year, value in zip(model['years'], values):
                identity = '|'.join([model['sha256'], model['company_id'], metric, str(year), str(value)])
                observations.append(dict.fromkeys(OBS_FIELDS, '') | dict(
                    observation_id=hashlib.sha256(identity.encode()).hexdigest()[:24],
                    company_id=model['company_id'], firm='First Shanghai Securities',
                    analyst_name=model['analyst_name'], source_type='individual_analyst_forecast',
                    metric=metric, fiscal_period=f'FY{year}', value=value, currency='USD', unit=unit,
                    basis=basis, report_date=model['report_date'],
                    availability_basis='printed_report_date_assumption', source_url=model['source_url'],
                    local_file=model['local_file'], page=model['page'],
                    status='verified_original_table', notes=model['notes'],
                    source_period_label=f'{year} forecast, annual table',
                    share_basis_date=model['report_date'], source_artifact_sha256=model['sha256'],
                ))
        manifest.append(dict.fromkeys(MAN_FIELDS, '') | dict(
            collection='firstshanghai_round11', source_url=model['source_url'],
            company_ids=model['company_id'], document_kind='broker_pdf',
            firm='First Shanghai Securities', analyst_name=model['analyst_name'],
            report_date=model['report_date'], retrieved_at=model['retrieved_at'],
            sha256=model['sha256'], local_file=model['local_file'], text_file=model['text_file'],
            status='verified_original_table', notes=model['notes'],
        ))
    for filename, fields, rows in [('observations.csv', OBS_FIELDS, observations), ('manifest.csv', MAN_FIELDS, manifest)]:
        with (BASE / filename).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    result = dict(company_models=len(models), observations=len(observations),
                  eps=sum(r['metric']=='eps' for r in observations),
                  revenue=sum(r['metric']=='revenue' for r in observations),
                  unique_originals=len({m['sha256'] for m in models}),
                  new_cross_firm_compatibility_bridges=0,
                  independently_verified_original_dissemination=False,
                  model_dates_retained=False)
    (BASE / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
