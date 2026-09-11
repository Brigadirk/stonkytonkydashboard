#!/usr/bin/env python3
"""Retain the primary provider descriptions used for the access handoff."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
URLS={
'factset_detail':'https://insight.factset.com/resources/factset-consensus-estimates-datafeed',
'lseg_estimates':'https://www.lseg.com/en/data-analytics/financial-data/company-data/ibes-estimates',
'lseg_quant':'https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/lseg-data-for-quant-research-brochure.pdf',
'scrapingbee_pricing':'https://www.scrapingbee.com/pricing/',
'scrapingbee_documentation':'https://www.scrapingbee.com/documentation/'}
def collect(item):
 name,url=item;target=HERE/(name+('.pdf' if url.endswith('.pdf') else '.html'))
 record={'name':name,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  if target.exists():content=target.read_bytes();record['status']='retained'
  else:
   response=subprocess.run(['curl','-LfsS','--max-time','30',url],capture_output=True,check=True)
   content=response.stdout
   target.write_bytes(content);record['status']='downloaded'
  record.update(file=str(target.relative_to(HERE)),sha256=hashlib.sha256(content).hexdigest(),bytes=len(content))
 except Exception as error:record.update(status='failed',error=str(error))
 return record
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(collect,URLS.items()))
 (HERE/'manifest.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps([{k:r.get(k) for k in ['name','status','bytes','error']} for r in results]))
