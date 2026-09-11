"""Retain exact public broker PDF leads; no search-snippet observations."""
import requests,json,hashlib,subprocess,datetime
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SOURCES={
'raiffeisen_asml':'https://www.raiffeisen.at/resources/sbg/microsites/internetwertpapiere/pdfs/firmenanalysen-international/ASML.pdf',
'guosen_nvidia_20260227':'https://pdf.dfcfw.com/pdf/H3_AP202602271820103939_1.pdf?1772214464000.pdf',
'asml_chinese_20260203':'https://pdf.dfcfw.com/pdf/H3_AP202602031819644752_1.pdf',
'guosen_nvidia_20250228':'https://pdf.dfcfw.com/pdf/H3_AP202502281643606379_1.pdf',
'guosen_nvidia_20250530':'https://pdf.dfcfw.com/pdf/H3_AP202505301681759010_1.pdf',
'guosen_nvidia_20241122':'https://pdf.dfcfw.com/pdf/H3_AP202411221641021029_1.pdf',
}
rows=[]
for f in ['raiffeisen_discovery.json','grok_originals_log.json','non_morningstar_download_log.json']:
 if (BASE/f).exists():
  d=json.loads((BASE/f).read_text());rows.extend(d if isinstance(d,list) else [dict(d,name='raiffeisen_asml')])
byname={r['name']:r for r in rows}
for name,url in SOURCES.items():
 if name in byname and (ROOT/byname[name].get('local_file','_missing')).is_file():continue
 r=requests.get(url,timeout=30);p=BASE/'originals'/f'{name}.pdf';t=BASE/'text'/f'{name}.txt'
 d=dict(name=name,source_url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),http_status=r.status_code)
 if r.ok and r.content.startswith(b'%PDF'):
  p.write_bytes(r.content);subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
  d.update(local_file=str(p.relative_to(ROOT)),text_file=str(t.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest())
 byname[name]=d
(BASE/'non_morningstar_download_log.json').write_text(json.dumps(list(byname.values()),indent=2)+'\n')
for name,d in byname.items():print(name,d['http_status'])
