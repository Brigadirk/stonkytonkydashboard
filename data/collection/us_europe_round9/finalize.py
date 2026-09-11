"""Offline extraction of visually reviewed original broker annual forecast tables.

No forecasts are inferred from prices, P/E ratios, historical actuals, or snippets.
Rerun against retained originals and pdftotext -layout files to reproduce the CSVs.
"""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OBS_FIELDS='observation_id,company_id,firm,analyst_name,source_type,metric,fiscal_period,value,currency,unit,basis,model_date,forecast_revision_as_of,report_date,available_at,printed_report_timestamp,original_available_at,availability_basis,source_url,local_file,page,status,notes,source_period_label,share_basis_date,source_artifact_sha256'.split(',')
MAN_FIELDS='source_url,local_file,company_ids,firm,analyst_name,report_date,retrieved_at,sha256,status,notes,text_file,report_timestamp,model_dates,http_status,report_month,report_date_precision,artifact_type'.split(',')

def write_csv(name,fields,rows):
    with (BASE/name).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)

def read_source(src):
    assert hashlib.sha256((ROOT/src['local_file']).read_bytes()).hexdigest()==src['sha256']
    return (ROOT/src['text_file']).read_text().split('\f')

# Keep whitespace between columns for numeric extraction: compact only the label.
def row_values(table,label):
    prefix=re.sub(r'\s+','',label)
    for line in table.splitlines():
        cursor=0;seen=''
        for i,char in enumerate(line):
            if not char.isspace():seen+=char
            if seen==prefix:cursor=i+1;break
        if seen==prefix:
            return [x.replace(',','') for x in re.findall(r'[-−]?\d[\d,]*(?:\.\d+)?',line[cursor:])]
    raise AssertionError(f'No row {label}')

observations=[];manifest=[]
def append_row(src,company,firm,author,metric,year,value,currency,basis,report,model,page,notes,raw_label,timestamp='',status='verified_original_table',source_type='individual_analyst_forecast'):
    row=dict.fromkeys(OBS_FIELDS,'')
    row.update(observation_id=hashlib.sha256('|'.join([src['sha256'],metric,str(year),value]).encode()).hexdigest()[:24],company_id=company,firm=firm,analyst_name=author,source_type=source_type,metric=metric,fiscal_period=f'FY{year}',value=value,currency=currency,unit=currency+('_million' if metric=='revenue' else '_per_share'),basis=basis,model_date=model,forecast_revision_as_of=model,report_date=report,printed_report_timestamp=timestamp,availability_basis='printed_report_timestamp_not_independently_verified' if timestamp else 'printed_report_date_not_independently_verified',source_url=src['source_url'],local_file=src['local_file'],page=page,status=status,notes=notes,source_period_label=raw_label,share_basis_date=model or report,source_artifact_sha256=src['sha256'])
    observations.append(row)

def append_manifest(src,company,firm,author,report,model,timestamp,status,notes):
    manifest.append(dict(source_url=src['source_url'],local_file=src['local_file'],company_ids=company,firm=firm,analyst_name=author,report_date=report,retrieved_at=src['retrieved_at'],sha256=src['sha256'],status=status,notes=notes,text_file=src['text_file'],report_timestamp=timestamp,model_dates=model,http_status=src['http_status'],report_month=report[:7],report_date_precision='day',artifact_type='pdf'))

broker=[x for x in json.loads((BASE/'broker_download_log.json').read_text()) if x.get('local_file')]
broker+=json.loads((BASE/'retained_originals_log.json').read_text())
SPECS={
'broadcom_20250605':dict(company='broadcom',report='2025-06-06',time='02:44',model='2025-06-05',model_print='05 Jun 2025',page=14,author='William Kerwin',currency='USD',years=range(2025,2030),rev=['63023','77892','99192','115055','127336'],eps=['4.37','5.85','8.55','10.60','12.33'],adj=['6.68','8.41','11.38','13.59','15.44'],note='Post-July2024 10-for-1 split units. Printed fiscal header is nominal October31; issuer annual year ends Sunday closest to October31. Broadcom FY2025 initial reported outcome can be compared only to the plain diluted row, not Morningstar adjusted.'),
'broadcom_20250606':dict(duplicate='broadcom_20250605',report='2025-06-06',time='22:31'),
'apple_20240507':dict(company='apple',report='2024-05-07',time='16:21',model='2024-05-06',model_print='06 May 2024',page=16,author='William Kerwin',currency='USD',years=range(2024,2027),rev=['383874','419450','449094'],eps=['6.56','7.74','8.75'],note='Post-August2020 split units. Nominal September30 printed header; Apple fiscal year ends last Saturday in September. Legacy diluted label does not establish reported-versus-adjusted definition.'),
'alphabet_20230426':dict(company='alphabet',report='2023-04-26',time='12:44',model='2023-02-02',model_print='02 Feb 2023',page=17,author='Ali Mogharabi',currency='USD',years=range(2023,2026),rev=['304111','339114','378563'],eps=['4.36','5.51','6.36'],note='Post-July2022 20-for-1 split units, Class A. December31 fiscal year. Legacy diluted label alone does not establish reported-versus-adjusted definition. February model is first evidenced here by an April report; no availability backdating.'),
'alphabet_20240130':dict(company='alphabet',report='2024-01-31',time='05:29',model='2024-01-30',model_print='30 Jan 2024',page=16,eps_page=17,author='Ali Mogharabi',currency='USD',years=range(2024,2027),rev=['339629','376709','416422'],eps=['6.23','7.38','8.48'],note='Post-July2022 split units, Class A. December31 fiscal year. Header and revenue on physical page16; EPS continues on physical page17 in the same table. Legacy diluted adjustment basis unresolved.'),
'alphabet_20240131':dict(duplicate='alphabet_20240130',report='2024-02-01',time='00:46',page=16,eps_page=16),
'alphabet_20240318':dict(company='alphabet',report='2024-03-18',time='20:51',model='2024-03-04',model_print='04 Mar 2024',page=14,author='Michael Hodel',currency='USD',years=range(2024,2027),rev=['342046','374673','404282'],eps=['6.67','7.48','8.15'],note='Current March4 strategy, fair-value sections and peer analyst identify Michael Hodel; old Ali Mogharabi archived notes are not model authorship. Post-July2022 split units. The source forecast header incorrectly says Fiscal Year, ends31Mar2023, while historical summary says December31 and FY2022/23 revenues282836/307394 match issuer December years. Preserve raw year labels, use verified issuer December31 calendar, no year shift. Legacy diluted basis unresolved; model historical FY2022 EPS4.55 differs issuer4.56.'),
'asml_20241115':dict(company='asml',report='2024-11-15',time='11:49',model='2024-11-06',model_print='06 Nov 2024',page=15,author='Javier Correonero',currency='EUR',years=range(2024,2027),rev=['28041','32567','36480'],eps=['18.86','23.75','29.84'],note='December31 fiscal years. USD-traded ADR report with explicitly EUR reporting and EUR per-share financial forecasts; no FX conversion for Amsterdam ordinary EPS. Existing original share mapping applies. Model remains November6 although report is November15; later prior-panel November15 date does not prove an exact model-date bridge. Legacy diluted adjustment basis unresolved. Its historical EPS also differs issuer weighted-average diluted outcomes.'),
'alphabet_20250507':dict(company='alphabet',report='2025-05-08',time='02:42',model='2025-04-24',model_print='24 Apr 2025',page=19,author='Malik Ahmed Khan',currency='USD',years=range(2025,2030),rev=['389792','431394','474644','519493','566095'],eps=['10.34','11.19','12.61','13.96','15.47'],adj=['10.34','11.19','12.61','13.96','15.47'],note='Previously retained solely for basis evidence in us_evaluation_round5; current April24 model now extracted from its earlier May8 original. December31 fiscal years, Class A, post-July2022 split units. Plain and adjusted rows agree numerically but labels remain separate.'),
'micron_20250403':dict(company='micron',report='2025-04-03',time='23:43',model='2025-03-20',model_print='20 Mar 2025',page=13,author='William Kerwin',currency='USD',years=range(2025,2030),rev=['34306','37552','40981','44287','47576'],eps=['5.76','5.71','6.65','7.78','9.52'],adj=['6.28','6.66','7.68','8.89','10.72'],note='Previously retained solely for basis evidence in us_evaluation_round5. Current March20 model now extracted from earlier April3 original. Source nominal August31 year-end; issuer FY ends Thursday closest to August31. No split transformation. Morningstar adjusted is not assumed identical to Micron issuer non-GAAP.'),
}
for src in broker:
    name=Path(src['local_file']).stem;s=SPECS[name]
    duplicate=s.get('duplicate')
    if duplicate:s={**SPECS[duplicate],**s}
    pages=read_source(src);assert s['author'] in pages[0]
    table=pages[s['page']-1]
    if 'adj' in s:
        assert 'Financials as of '+s['model_print'] in table
        eps_label=f'Earnings Per Share (Diluted) ({s["currency"]})'
        adj_label=f'Adjusted Earnings Per Share (Diluted) ({s["currency"]})'
        assert row_values(table,adj_label)[-len(s['years']):]==s['adj']
    else:
        assert 'Morningstar Analyst Historical/Forecast Summary as of '+s['model_print'] in table
        table=table.split('Morningstar Analyst Historical/Forecast Summary',1)[1]
        if s.get('eps_page',s['page'])!=s['page']:table+='\n'+pages[s['eps_page']-1]
        eps_label=f'Diluted Earnings Per Share({s["currency"]})'
    assert row_values(table,f'Revenue ({s["currency"]} Mil)')[:(8 if 'adj' in s else 5)][-len(s['years']):]==s['rev'],name
    assert row_values(table,eps_label)[:(8 if 'adj' in s else 5)][-len(s['years']):]==s['eps'],name
    stamp=s['report']+'T'+s['time']+':00+00:00'
    notes='Original Morningstar report distributed by Firstrade. Current numerical-model rows only. Report date and model date are distinct; original historical dissemination is unverified. '+s['note']
    if duplicate:
        append_manifest(src,s['company'],'Morningstar',s['author'],s['report'],s['model'],stamp,'verified_duplicate_model_corroboration','Same full EPS/revenue vector and model date as '+duplicate+'; earliest retained original supplies observations. '+notes)
        continue
    metrics=[('revenue','total_revenue',s['rev']),('eps_diluted','reported_diluted' if 'adj' in s else 'diluted_adjustment_basis_unresolved',s['eps'])]
    if 'adj' in s:metrics.append(('eps_adjusted_diluted','adjusted_diluted',s['adj']))
    for metric,basis,values in metrics:
        for year,value in zip(s['years'],values):
            pg=s.get('eps_page',s['page']) if metric.startswith('eps') else s['page']
            append_row(src,s['company'],'Morningstar',s['author'],metric,year,value,s['currency'],basis,s['report'],s['model'],pg,notes,str(year),stamp)
    append_manifest(src,s['company'],'Morningstar',s['author'],s['report'],s['model'],stamp,'verified_original_current_forecast_table',notes)

other={r['name']:r for r in json.loads((BASE/'non_morningstar_download_log.json').read_text())}
GUOSEN={
'guosen_nvidia_20241122':dict(report='2024-11-22',years=range(2025,2028),raw=['2024E','2025E','2026E'],rev=['123659','164228','184586'],eps=['2.73','3.64','4.19'],net=['66997','89375','102903'],model_net=['66997','89375','102903'],model_page=5,authors='Zhang Lunke (张伦可)',shift=True),
'guosen_nvidia_20250228':dict(report='2025-02-28',years=range(2026,2029),raw=['2025E','2026E','2027E'],rev=['200746','249646','281038'],eps=['4.21','5.42','6.26'],net=['102722','132155','152779'],model_net=['102722','132155','152779'],model_page=5,authors='Zhang Lunke (张伦可)',shift=True),
'guosen_nvidia_20250530':dict(report='2025-05-30',years=range(2026,2029),raw=['2025E','2026E','2027E'],rev=['199250','243719','271504'],eps=['4.15','5.54','6.33'],net=['100283','131184','146780'],model_net=['101341','135182','154473'],model_page=5,authors='Zhang Lunke (张伦可)',shift=True),
'guosen_nvidia_20260227':dict(report='2026-02-27',years=range(2027,2030),raw=['FY2027E','FY2028E','FY2029E'],rev=['344874','430448','513505'],eps=['8.72','10.71','12.60'],net=['211996','260299','306089'],model_net=['211996','260299','306089'],model_page=4,authors='Zhang Lunke (张伦可); Liu Zitan (刘子谭); Zhang Haochen (张昊晨)',shift=False),
}
for name,s in GUOSEN.items():
    src=other[name];pages=read_source(src);p=pages[0];compact=re.sub(r'\s+','',p)
    assert '国信证券' in p and '证券分析师：张伦可' in p and '摊薄每股收益按最新总股本计算' in compact
    assert s['report'].replace('-','年',1).replace('-','月',1)+'日' in compact
    assert row_values(p,'营业收入(百万美元)')[-3:]==s['rev']
    assert row_values(p,'EPS（美元）')[-3:]==s['eps']
    assert row_values(p,'归母净利润(百万美元)')[-3:]==s['net']
    model_page=pages[s['model_page']-1]
    income_line=next(x.split('归属于母公司净利润',1)[1] for x in model_page.splitlines() if '归属于母公司净利润' in x)
    assert [x.replace(',','') for x in re.findall(r'\d[\d,]*(?:\.\d+)?',income_line)][-3:]==s['model_net']
    numerator_conflict=s['net']!=s['model_net']
    for label in s['raw']:assert label in p
    notes='Original Guosen Securities research PDF retained from public East Money PDF host; document date, analyst registration and firm identity printed on p1. Current forecasts, not consensus: table source credits Guosen Economic Research Institute forecasts. Report has no separate numerical model date or verified original dissemination timestamp. EPS footnote explicitly says diluted per-share earnings calculated using latest total share capital. Keep Guosen EPS convention separate from issuer GAAP weighted-average diluted and from Morningstar; no denominator restatement is inferred. All printed values are post-June2024 NVIDIA split units. '
    if s['shift']:
        notes+='NVIDIA issuer fiscal years are one above raw front-table year labels: same-page forecast narrative explicitly identifies issuer fiscal years and corresponding rounded revenue vector, while historical60922/130497 (or26974/60922) revenues match issuer FY2024/25 (orFY2023/24). Raw labels retained; normalized targets follow these exact in-document links. Liu Zitan is printed as contact, not licensed analyst, so not counted as a second forecaster. '
    else:
        notes+='FY labels are explicit. Joint three-author model counts as one forecast team, not three independent forecasts. The printed example January26 end is approximate and is not substituted for the verified Sunday-near-January31 issuer calendar. Historical FY2026 EPS4.94 differs initial issuer diluted4.90, confirming incompatibility. '
    if name=='guosen_nvidia_20250228':notes+='Narrative FY2027 net profit1232 hundred-million USD conflicts with table132155million; no net-profit observations are extracted. Revenue and EPS are retained as printed in the current table. '
    if numerator_conflict:notes+='EPS QUARANTINED: physical p5 contains conflicting parent-attributable net-profit vectors101341/135182/154473 and100283/131184/146780. Cover uses the latter; no source text explains an adjustment or selects the EPS numerator. All three EPS values remain as printed but cannot enter the common Guosen stream until reconciled. Revenue vector agrees across cover and model and remains verified. '
    for metric,basis,values in [('revenue','total_revenue',s['rev']),('eps','guosen_latest_total_shares_eps',s['eps'])]:
        for year,label,value in zip(s['years'],s['raw'],values):
            status='quarantined_internal_model_numerator_conflict' if numerator_conflict and metric=='eps' else 'verified_original_table'
            row_basis='guosen_eps_internal_model_numerator_conflict' if numerator_conflict and metric=='eps' else basis
            append_row(src,'nvidia','Guosen Securities',s['authors'],metric,year,value,'USD',row_basis,s['report'],'',1,notes,label,status=status)
    append_manifest(src,'nvidia','Guosen Securities',s['authors'],s['report'],'','','verified_revenue_eps_quarantined_internal_model_numerator_conflict' if numerator_conflict else 'verified_original_current_forecast_table',notes)

src=other['asml_chinese_20260203'];pages=read_source(src);p=pages[0]
assert '西南证券' in p and '王湘杰' in p and '杨镇宇' in p
assert '2026年01月30日' in re.sub(r'\s+','',p)
rev=['38790.87','45019.46','48310.08'];eps=['30.94','37.46','41.29']
assert row_values(p,'营业收入(百万欧元)')[-3:]==rev
assert row_values(p,'每股收益 EPS(欧元)')[-3:]==eps
notes='Original Southwest Securities Jan30,2026 report retained from East Money PDF host; URL contains February3, but printed report date governs. Joint model by Wang Xiangjie and Yang Zhenyu counts as one forecast team. p6 states these are our2026–2028 forecasts; p1 and p8 repeat current EPS and EUR revenue. No separate model timestamp. EPS row does not specify basic/diluted denominator or adjusted treatment. FY2025 historical net income9609.40 matches issuer US-GAAP but EPS24.80 differs issuer diluted24.71; no GAAP-diluted compatibility claimed. USD share-price/target fields do not change explicitly EUR EPS; no FX conversion. December31 fiscal years, raw E labels preserved.'
for metric,basis,values in [('revenue','total_revenue',rev),('eps','swsc_eps_definition_unresolved',eps)]:
    for year,value in zip(range(2026,2029),values):append_row(src,'asml','Southwest Securities','Wang Xiangjie (王湘杰); Yang Zhenyu (杨镇宇)',metric,year,value,'EUR',basis,'2026-01-30','',1,notes,f'{year}E')
append_manifest(src,'asml','Southwest Securities','Wang Xiangjie (王湘杰); Yang Zhenyu (杨镇宇)','2026-01-30','','','verified_original_current_forecast_table',notes)

src=other['raiffeisen_asml'];pages=read_source(src);p=pages[0]
assert '17. Juni 2026 14:26 MESZ' in p and 'LSEG, RBI/Raiffeisen Research' in p and 'Manuel STAHL' in p
assert '31,17' in p and '41,93' in p and '31,42' in p and '42,39' in p and '38.910' in p and '47.769' in p
notes='Original Raiffeisen Research report on its public Raiffeisen host; mutable URL, retained dated PDF. p1 jointly credits LSEG and RBI/Raiffeisen Research. Manuel Stahl is Analyst Editor; individual ownership of the forecast table is not established. Consensus attribution is also not explicit enough to assert. Unadjusted EPS label Gewinn je Aktie and adjusted label Gewinn je Aktie bereinigt do not specify basic/diluted denominator or adjustment definition. Retain raw FY2026e/2027e forecasts quarantined from named analyst ranking and valuation until attribution/definition are resolved. FY2025 is historical actual and excluded. EUR financial reporting, ISIN NL0010273215, December31 year-end. Printed14:26MESZ converts to12:26UTC but is not independently verified dissemination.'
for metric,basis,values in [('revenue','total_revenue',['38910','47769']),('eps','raiffeisen_eps_definition_unresolved',['31.17','41.93']),('eps_adjusted','raiffeisen_adjusted_eps_definition_unresolved',['31.42','42.39'])]:
    for year,value in zip(range(2026,2028),values):append_row(src,'asml','Raiffeisen Research','',metric,year,value,'EUR',basis,'2026-06-17','',1,notes,f'{year}e','2026-06-17T12:26:00+00:00','quarantined_attribution_and_eps_definition_unresolved','publisher_forecast_unattributed')
append_manifest(src,'asml','Raiffeisen Research','','2026-06-17','','2026-06-17T12:26:00+00:00','quarantined_attribution_and_eps_definition_unresolved',notes)

write_csv('observations.csv',OBS_FIELDS,observations)
write_csv('manifest.csv',MAN_FIELDS,manifest)
assert len(observations)==111 and len(manifest)==16
assert len({r['observation_id'] for r in observations})==111
assert len({r['sha256'] for r in manifest})==16
assert all(not r['available_at'] and not r['original_available_at'] and r['report_date']<='2026-09-10' for r in observations)
assert all(not r['model_date'] or r['model_date']<=r['report_date'] for r in observations)
validation=dict(total_raw_forecasts=len(observations),verified_forecasts=sum(not r['status'].startswith('quarantined') for r in observations),quarantined_forecasts=sum(r['status'].startswith('quarantined') for r in observations),morningstar_forecasts=sum(r['firm']=='Morningstar' for r in observations),guosen_forecasts=sum(r['firm']=='Guosen Securities' for r in observations),southwest_forecasts=sum(r['firm']=='Southwest Securities' for r in observations),eps_rows=sum(r['metric'].startswith('eps') for r in observations),revenue_rows=sum(r['metric']=='revenue' for r in observations),retained_originals=len(manifest),retained_duplicate_models=2,forecast_rows_by_company=dict(Counter(r['company_id'] for r in observations)),source_hashes_verified=True,physical_pages_visually_reviewed=True,annual_columns_verified=True,historical_availability_assumed=False,new_issuer_outcomes=0,new_basis_aliases=0)
(BASE/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))

# Exact source/report/FY scopes for a single Guosen research stream. This is not
# an alias to issuer EPS and must not produce independent votes for coauthors.
review=dict(review_date='2026-09-10',common_basis='guosen_latest_total_shares_eps',company_id='nvidia',firm='Guosen Securities',definition='Guosen parent-attributable net-profit EPS under the report-stated latest-total-share-capital convention; USD per ordinary share, post-June2024 split.',issuer_gaap_compatibility=False,cross_firm_compatibility=False,one_firm_stream=True,scopes=[],excluded=[])
for name,s in GUOSEN.items():
    src=other[name]
    item=dict(source_url=src['source_url'],source_file=src['local_file'],source_sha256=src['sha256'],report_date=s['report'],model_date='',authors=s['authors'],source_pages=[1,s['model_page']],fiscal_periods=[f'FY{x}' for x in s['years']],printed_eps=s['eps'],cover_parent_net_profit_usd_million=s['net'],income_statement_parent_net_profit_usd_million=s['model_net'],evidence='p1 explicitly labels Guosen forecasts and latest-total-share EPS; full income statement parent-profit row matches the same target years and complete cover numerator vector.' if s['net']==s['model_net'] else 'p5 has two different parent-profit vectors; EPS numerator selection unresolved.')
    if s['net']==s['model_net']:review['scopes'].append(item)
    else:review['excluded'].append(item)
(BASE/'guosen_definition_review.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
