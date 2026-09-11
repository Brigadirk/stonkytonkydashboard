"""Offline validation of original PDFs, extracted rows and exact archive captures."""
from pathlib import Path
import csv, json, hashlib, base64
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, unquote
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=list(csv.DictReader((BASE/'manifest.csv').open()))
observations=list(csv.DictReader((BASE/'observations.csv').open()))
by_id={r['report_id']:r for r in manifest}
for row in manifest:
 if row['sha256']:
  assert (BASE/row['local_file']).read_bytes().startswith(b'%PDF')
  assert sha(BASE/row['local_file'])==row['sha256']
for row in observations:
 assert row['sha256']==by_id[row['report_id']]['sha256']
 assert 1<=int(row['pdf_page'])<=int(by_id[row['report_id']]['page_count'])
 assert row['historical_availability_verified']=='false'
 assert row['report_date']==row['model_date']
 assert row['report_date']<=row['target_period_end']
 assert row['original_value'].replace(',','')==row['value'] or row['metric']=='revenue'
archive=[]
for r in json.loads((BASE/'availability_evidence_recommendations.json').read_text())['recommendations']:
 original=ROOT/r['source_file'];archived=ROOT/r['archived_pdf_file'];cdx=ROOT/r['cdx_evidence_file']
 assert sha(original)==sha(archived)==r['source_sha256']==r['archived_pdf_sha256']
 assert sha(cdx)==r['cdx_evidence_sha256']
 sha1=base64.b32encode(hashlib.sha1(original.read_bytes()).digest()).decode().rstrip('=')
 assert sha1==r['cdx_digest']
 timestamp=datetime.fromisoformat(r['captured_at'].replace('Z','+00:00'))
 stamp=timestamp.strftime('%Y%m%d%H%M%S')
 assert timestamp.date().isoformat()==r['capture_date']
 table=json.loads(cdx.read_text());rows=[dict(zip(table[0],row)) for row in table[1:]]
 found=[row for row in rows if row['timestamp']==stamp and row['digest']==sha1]
 assert found,(r['source_sha256'],'capture missing from CDX')
 replay_original=r['replay_url'].split('id_/',1)[1]
 assert replay_original in [row['original'] for row in found]
 def identity(url):
  parts=urlsplit(url);return parts.netloc.lower(),unquote(parts.path),parts.query
 assert identity(replay_original)==identity(r['original_url'])
 archive.append(dict(source_sha256=r['source_sha256'],captured_at=r['captured_at'],conservative_available_date=(timestamp.date()+timedelta(days=1)).isoformat(),original_archived_bytes_equal=True,cdx_timestamp_url_digest_verified=True))
result=dict(originals_verified=sum(bool(r['sha256']) for r in manifest),observations_verified=len(observations),archive_captures_verified=len(archive),archive=archive)
(BASE/'evidence_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='archive'},indent=2))
