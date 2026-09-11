"""Resolve selected public broker-channel links and retain original PDFs + redirect evidence."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import requests,json,hashlib,subprocess
B=Path(__file__).resolve().parent
LEADS={'8535':'meritz_samsung_20240502','10288':'meritz_samsung_20241101','10533':'meritz_samsung_20241118','11011':'meritz_samsung_20250108','12016':'meritz_samsung_20250408','13034':'meritz_samsung_20250708','14226':'meritz_samsung_20251014','15173':'meritz_samsung_20260108','16283':'meritz_samsung_20260407','17545':'meritz_samsung_20260707','18261':'meritz_sector_20260818','6046':'meritz_samsung_20230727','15263':'meritz_sector_20260112','16199':'meritz_sector_20260401','2854':'meritz_samsung_20210729','3902':'meritz_samsung_20221028','4547':'meritz_hynix_20230201','5168':'meritz_hynix_20230427','2666':'meritz_sector_20210601','3041':'meritz_samsung_20211029'}
posts=json.loads((B/'discovery/posts.json').read_text());posts.update(json.loads((B.parent/'korea_round9/discovery/meritz_posts.json').read_text()));posts.update(json.loads((B/'discovery/meritz_posts.json').read_text()))
def get(pair):
 post,key=pair;v=posts['merITz_tech/'+post];url=v['links'][-1];out=B/'pdfs'/(key+'.pdf');log={'report_id':key,'discovery_url':'https://t.me/merITz_tech/'+post,'redirect_url':url,'displayed_post_timestamp':v['date'],'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  r=subprocess.run(['curl','-LfsS','--max-time','30','--write-out','%{url_effective}',url,'-o',str(out)],capture_output=True,text=True,check=True);log['source_url']=r.stdout
  raw=out.read_bytes()
  if not raw.startswith(b'%PDF'):
   (B/'discovery'/f'{key}_nonpdf.html').write_bytes(raw);out.unlink();raise ValueError('Resolved response is not a PDF')
  log.update(local_file='pdfs/'+out.name,text_file='text/'+key+'.txt',sha256=hashlib.sha256(raw).hexdigest());subprocess.run(['pdftotext','-layout',str(out),str(B/log['text_file'])],capture_output=True,check=True);log['page_count']=len((B/log['text_file']).read_text().split('\f'))-1
 except Exception as e:log['error']=str(e)
 print(key,log.get('source_url'),log.get('page_count'),log.get('error'),flush=True);return log
old=json.loads((B/'download_log.json').read_text()) if (B/'download_log.json').exists() else []; done={x['report_id'] for x in old if x.get('sha256')}; logs=[x for x in old if x['report_id'] in done]+list(ThreadPoolExecutor(max_workers=4).map(get,[(k,v) for k,v in LEADS.items() if v not in done]));(B/'download_log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')
