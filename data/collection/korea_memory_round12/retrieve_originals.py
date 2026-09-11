"""Re-download reviewed original URLs into a separate verification folder; verify expected hashes.

Existing extraction packet remains immutable. Run extract_reviewed.py for offline reproduction.
"""
from pathlib import Path
import json,subprocess,hashlib
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
B=Path(__file__).resolve().parent;D=B/'reproduction';D.mkdir(exist_ok=True)
def one(row):
 p=D/(row['report_id']+'.pdf');out=dict(report_id=row['report_id'],source_url=row['source_url'],retrieved_at=datetime.now(timezone.utc).isoformat())
 try:
  subprocess.run(['curl','-LfsS','--max-time','30',row['source_url'],'-o',str(p)],check=True,capture_output=True)
  assert p.read_bytes().startswith(b'%PDF'),'Not a PDF'
  sha=hashlib.sha256(p.read_bytes()).hexdigest();out.update(sha256=sha,matches_reviewed_original=sha==row['sha256']);assert sha==row['sha256'],'Original changed; re-review required'
 except Exception as e:out['error']=str(e)
 return out
rows=list(ThreadPoolExecutor(max_workers=4).map(one,json.loads((B/'source_recipe.json').read_text())));(D/'download_log.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'verified':sum(x.get('matches_reviewed_original',False) for x in rows),'failed':sum('error' in x for x in rows)},indent=2))
if any('error' in x for x in rows):raise SystemExit(1)
