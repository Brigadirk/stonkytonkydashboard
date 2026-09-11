"""Download bounded public Morningstar distributor paths; printed contents govern report dates."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import requests, hashlib, json, subprocess
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
DATES="20210727 20211028 20220127 20220428 20220728 20221027 20230202 20230504 20230803 20231102 20240201 20240502 20240801 20241031 20250130 20250501 20250731 20251030 20260129 20260430 20260730".split()
def get(d):
 url=f"https://invest.firstrade.com/ms/equity_reports/sr/{d[:4]}/0P000000GY_{d}_RT.pdf"
 rec={"source_url":url,"date_hint":d,"retrieved_at":datetime.now(timezone.utc).isoformat()}
 try:
  r=requests.get(url,timeout=30);rec["http_status"]=r.status_code
  if r.status_code==200 and r.content.startswith(b"%PDF"):
   p=BASE/"pdfs"/f"morningstar_AAPL_{d}.pdf";p.write_bytes(r.content)
   tp=BASE/"text"/f"{p.stem}.txt"
   subprocess.run(["pdftotext","-layout",str(p),str(tp)],check=True)
   rec.update(local_file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest())
 except Exception as e:rec["error"]=str(e)
 print(d,rec.get("http_status"),"retained" if rec.get("local_file") else "missing",flush=True)
 return rec
if __name__=="__main__":
 logs=list(ThreadPoolExecutor(max_workers=4).map(get,DATES))
 (BASE/"download_log.json").write_text(json.dumps(logs,indent=2)+"\n")
