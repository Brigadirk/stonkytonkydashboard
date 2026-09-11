"""Restore missing retained originals only; refuse changed public bytes; never overwrite originals."""
from pathlib import Path
import json,hashlib,subprocess
BASE=Path(__file__).resolve().parent
for r in json.loads((BASE/'source_recipe.json').read_text()):
 p=BASE/r['local_file']
 if p.exists():
  assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['report_id']
  continue
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.download')
 subprocess.run(['curl','-LfsS','--max-time','45',r['source_url'],'-o',str(tmp)],check=True)
 assert hashlib.sha256(tmp.read_bytes()).hexdigest()==r['sha256'],f"Public bytes changed for {r['report_id']}; retained hash required"
 tmp.replace(p)
 subprocess.run(['pdftotext','-layout',str(p),str(BASE/r['text_file'])],check=True)
print('All retained originals match source_recipe.json')
