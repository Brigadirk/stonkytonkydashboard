"""Validate retained broker originals and emit only visually checked forecasts.

No network requests, model interpolation, denominator inference or consensus rows.
Run from anywhere. Re-fetch missing sources with collect_public.mjs first.
"""
from pathlib import Path
from decimal import Decimal
from datetime import date
import csv
import hashlib
import json
import re
import subprocess

BASE = Path(__file__).resolve().parent
FIELDS = ['report_id','company_id','ticker','firm','analyst_name','source_type','report_date','model_date','share_basis_date','report_date_reliability','target_period','target_period_end','metric','currency','value','original_value','original_unit','basis','pdf_page','source_url','local_file','text_file','sha256','retrieved_at','extraction_status','time_relation','historical_availability_verified','raw_table_row','notes']
MANIFEST_FIELDS = ['report_id','source_url','local_file','text_file','company_ids','firm','analyst_name','report_date','report_date_reliability','retrieved_at','sha256','status','notes','page_count','discovery_url','collection_window','document_kind']
COMMON = 'Original report date, byline, fiscal columns, units and forecast values visually reviewed. No split conversion applied. Original publication instant and historical availability unverified. Basic/diluted, weighted-average and treasury-share denominator policies remain unresolved. No cross-firm EPS equivalence or issuer-outcome comparability is established.'
NOTES = {
    'hana_hynix_20260730': 'Hana July30 current model explicitly revises FY2026/27 operating forecasts. Use Financial Data on p1 and detailed statements on p5; do not use the separate Consensus Data panel. Printed EPS 376719/463912 and revenue352234.2/507904.6 KRWbn agree across both tables. The public channel locator was dated July29 UTC; the printed July30 date controls this observation. No FY2028 estimate appears, so this model cannot cover the full September2027–September2028 target earnings interval. ',
    'nh_sector_20260526': 'NH sector report delivered by the public Feat Paper Download button. Full PDF has14 broker pages plus one blank final page; all selected values come from original broker pages10/11. The cover byline is 류영호, transliterated Young-ho Ryu. EPS is explicitly parent-attributable under consolidated IFRS. Share denominator is not defined, including preferred-share allocation for Samsung. May26 printed report date is the current-model date proxy; May22 in target-price history is not evidence for backdating this EPS model. Provider delivery metadata is not historical availability evidence. ',
}

def write_csv(path, fields, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    sources = json.loads((BASE/'source_recipe.json').read_text())
    transcriptions = json.loads((BASE/'verified_transcriptions.json').read_text())
    source_map = {s['report_id']:s for s in sources}
    texts = {}
    manifests = []
    for source in sources:
        pdf = BASE/source['local_file']
        assert pdf.read_bytes().startswith(b'%PDF'), pdf
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source['sha256'], pdf
        metadata = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        assert int(re.search(r'^Pages:\s+(\d+)',metadata,re.M)[1]) == source['page_count']
        # Regenerate text from the retained bytes so a stale transcript cannot validate itself.
        subprocess.run(['pdftotext','-layout',str(pdf),str(BASE/source['text_file'])],check=True)
        text = (BASE/source['text_file']).read_text()
        texts[source['report_id']] = text.split('\f')
        first = texts[source['report_id']][0]
        if source['firm'] == 'hana':
            assert '2026년 7월 30일' in first and '김록호' in first
            assert '376,719' in first and '463,912' in first
            assert '352,234.2' in first and '507,904.6' in first
            assert '2028F' not in text
        else:
            assert '2026. 5. 26' in first and '류영호' in first
            for page in [10,11]:
                assert 'EPS, PER, PBR, ROE는 지배지분 기준' in texts[source['report_id']][page-1]
                assert 'IFRS연결' in texts[source['report_id']][page-1]
        row = {field:source.get(field,'') for field in MANIFEST_FIELDS}
        row.update(company_ids=';'.join(source['company_ids']),report_date_reliability='printed_date_visually_verified_physical_page_1',status='downloaded_text_extracted_visually_verified',notes=NOTES[source['report_id']]+COMMON,collection_window='fresh_hana_and_independent_nh_forecasts',document_kind='broker_research_report')
        manifests.append(row)
    rows = []
    for table in transcriptions:
        source = source_map[table['report_id']]
        page = texts[table['report_id']][table['physical_page']-1]
        assert table['visually_verified'] is True
        assert (BASE/table['review_image']).exists()
        for metric, field in [('eps','eps_krw'),('revenue','revenue_krw_billion')]:
            raw_row = table['raw_rows'][metric]
            assert raw_row in page, (table['report_id'], metric)
            assert all(value in raw_row for value in table[field])
            for year, value in zip(table['fiscal_years'], table[field], strict=True):
                assert f'{year}F' in page or f'{year}E' in page
                number = Decimal(value.replace(',',''))
                if metric == 'revenue':
                    number *= Decimal(10)**9
                row = {field:source.get(field,'') for field in FIELDS}
                row.update(company_id=table['company_id'],ticker='000660.KS' if table['company_id']=='sk_hynix' else '005930.KS',source_type='individual_analyst_forecast',report_date_reliability='printed_date_visually_verified_physical_page_1',target_period=f'FY{year}',target_period_end=f'{year}-12-31',metric=metric,currency='KRW',value=format(number,'f'),original_value=value,original_unit='KRW per share' if metric=='eps' else 'KRW billion',basis=('Hana Financial Data forecast table; EPS definition not normalized' if source['firm']=='hana' else 'NH consolidated IFRS parent-attributable EPS; basic/diluted and share denominator unresolved') if metric=='eps' else 'Consolidated total revenue as printed',pdf_page=table['physical_page'],extraction_status='manually_verified_explicit_forecast_table_unscored',time_relation='current_or_future_fiscal_year_estimate',historical_availability_verified='false',raw_table_row=raw_row,notes=NOTES[source['report_id']]+COMMON)
                rows.append(row)
    assert len(rows)==16 and sum(r['metric']=='eps' for r in rows)==8
    write_csv(BASE/'manifest.csv',MANIFEST_FIELDS,manifests)
    write_csv(BASE/'observations.csv',FIELDS,rows)
    summary = dict(retained_reports=2,physical_pdf_pages=21,broker_content_pages=20,company_models=3,eps_observations=8,revenue_observations=8,total_observations=16,new_research_firms=['nh'],cross_firm_compatibility_groups_proven=0,historical_availability_instants_proven=0,model_ages_at_cutoff={s['report_id']:(date(2026,9,10)-date.fromisoformat(s['model_date'])).days for s in sources},source_sha256_verified=True,page_rows_verified=True)
    (BASE/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__ == '__main__':
    main()
