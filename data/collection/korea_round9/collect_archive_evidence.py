"""Bounded Wayback checks. Capture date is an availability upper bound, not publication date."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import csv,json,hashlib,base64,subprocess,urllib.parse
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];D=BASE/'archive';D.mkdir(exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(candidate):
 h=candidate['source_sha256'];key=h[:16];cdx=D/(key+'_cdx.json');log=dict(candidate);log['checked_at']=datetime.now(timezone.utc).isoformat()
 try:
  url='https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':candidate['original_url'],'output':'json','filter':'statuscode:200','collapse':'digest','to':'20260910'})
  log['cdx_url']=url
  if not cdx.exists():subprocess.run(['curl','-LfsS','--max-time','25',url,'-o',str(cdx)],check=True,capture_output=True)
  log.update(cdx_evidence_file=str(cdx.relative_to(ROOT)),cdx_evidence_sha256=digest(cdx))
  table=json.loads(cdx.read_text());raw=(ROOT/candidate['source_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==h
  sha1=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
  captures=[dict(zip(table[0],r)) for r in table[1:]] if table else [];matches=[x for x in captures if x.get('digest')==sha1]
  log.update(capture_count=len(captures),matching_digest_capture_count=len(matches))
  if not matches:log['status']='no_matching_archived_digest';return log
  capture=min(matches,key=lambda x:x['timestamp']);stamp=capture['timestamp'];replay='https://web.archive.org/web/'+stamp+'id_/'+capture['original'];out=D/(key+'_'+stamp+'.pdf')
  if not out.exists():subprocess.run(['curl','-LfsS','--max-time','35',replay,'-o',str(out)],check=True,capture_output=True)
  archived_hash=digest(out);assert archived_hash==h,'Archived bytes differ from original'
  log.update(status='exact_archived_bytes_verified',captured_at=datetime.strptime(stamp,'%Y%m%d%H%M%S').replace(tzinfo=timezone.utc).isoformat().replace('+00:00','Z'),capture_date=stamp[:4]+'-'+stamp[4:6]+'-'+stamp[6:8],archived_pdf_file=str(out.relative_to(ROOT)),archived_pdf_sha256=archived_hash,replay_url=replay,cdx_digest=sha1)
 except Exception as e:log.update(status='public_archive_retrieval_failed',error=str(e))
 return log
if __name__=='__main__':
 cp=BASE/'archive_candidates.json'
 if not cp.exists():
  candidates={}
  for row in csv.DictReader((ROOT/'data/collected_forecasts.csv').open()):
   if row['firm']=='meritz' and row['company_id'] in ['sk_hynix','samsung_electronics'] and row['metric']=='eps' and row['report_date']<'2026-01-01' and 'home.imeritz.com' in row['source_url']:
    candidates.setdefault(row['source_sha256'],{'source_sha256':row['source_sha256'],'source_file':row['source_file'],'original_url':row['source_url'],'report_dates':[row['report_date']]})
  # Include missing late-2025 source families, then oldest retained models.
  for r in json.loads((BASE/'download_log.json').read_text()):
   if r.get('sha256') and any(x in r['key'] for x in ['202511','202409','202503']):candidates.setdefault(r['sha256'],{'source_sha256':r['sha256'],'source_file':str((BASE/r['local_file']).relative_to(ROOT)),'original_url':r['source_url'],'report_dates':[]})
  new=[x for x in candidates.values() if not x['report_dates']];old=sorted([x for x in candidates.values() if x['report_dates']],key=lambda x:x['report_dates'])
  chosen=new+old[:24-len(new)]
  cp.write_text(json.dumps(chosen,indent=2)+'\n')
 candidates=json.loads(cp.read_text());lp=BASE/'archive_check_log.json';oldlogs=json.loads(lp.read_text()) if lp.exists() else [];done={x['source_sha256'] for x in oldlogs};results=oldlogs[:]
 for row in ThreadPoolExecutor(max_workers=3).map(run,[x for x in candidates if x['source_sha256'] not in done]):
  results.append(row);lp.write_text(json.dumps(results,indent=2)+'\n');print(row['source_sha256'][:12],row['status'],row.get('captured_at',''),flush=True)
 recommended=[x for x in results if x['status']=='exact_archived_bytes_verified']
 (BASE/'availability_evidence_recommendations.json').write_text(json.dumps({'semantics':'Exact archived bytes establish available-by capture time only; original publication instant remains unknown. Root applies next UTC day conservatively.','recommendations':recommended},indent=2)+'\n')
 print('Archive checks',len(results),'verified',len(recommended))
