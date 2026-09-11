"""Restore a missing original from the reviewed manifest without replacing retained evidence.

Offline validation/reproduction: python3 finalize.py
This downloader skips existing files and rejects changed bytes; the reviewed manifest is immutable here.
"""
from pathlib import Path
import csv,hashlib,requests
B=Path(__file__).resolve().parent
for m in csv.DictReader((B/'issuer_manifest.csv').open()):
 p=B/m['source_file']
 if p.exists():
  assert hashlib.sha256(p.read_bytes()).hexdigest()==m['source_sha256'],p
  continue
 r=requests.get(m['source_url'],timeout=30);r.raise_for_status()
 if hashlib.sha256(r.content).hexdigest()!=m['source_sha256']:
  raise ValueError(f'Source bytes changed for {m["source_id"]}; do not replace reviewed evidence automatically.')
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r.content)
print('Original files present and hash-verified; no manifest changes.')
