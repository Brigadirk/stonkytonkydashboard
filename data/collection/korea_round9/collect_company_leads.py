from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib
B=Path(__file__).resolve().parent
LEADS={'6955':'meritz_sector_20231108','2587':'meritz_samsung_20210430','6046':'meritz_samsung_20230727','2284':'meritz_hynix_20210201','3220':'meritz_samsung_20220128','3389':'meritz_hynix_20220428','3234':'meritz_hynix_20220203','3395':'meritz_samsung_20220429','4510':'meritz_samsung_20230131','5188':'meritz_samsung_20230427','7651':'meritz_hynix_20240126','2562':'meritz_hynix_review_20210428'}
posts=json.loads((B/'discovery/meritz_posts.json').read_text());p=B/'download_log_company.json';logs=json.loads(p.read_text()) if p.exists() else []
for post,key in LEADS.items():
 if any(r['key']==key for r in logs):continue
 v=posts['merITz_tech/'+post];url=v['links'][0];out=B/'pdfs'/(key+'.pdf');log={'key':key,'discovery_url':'https://t.me/merITz_tech/'+post,'redirect_url':url,'displayed_post_timestamp':v['date'],'retrieved_at':datetime.now(timezone.utc).isoformat()}
 try:
  r=subprocess.run(['curl','-LfsS','--max-time','30','--write-out','%{url_effective}',url,'-o',str(out)],capture_output=True,text=True,check=True);log['source_url']=r.stdout
  if not out.read_bytes().startswith(b'%PDF'):raise ValueError('Resolved response is not a PDF')
  log.update(local_file='pdfs/'+out.name,text_file='text/'+key+'.txt',sha256=hashlib.sha256(out.read_bytes()).hexdigest());subprocess.run(['pdftotext','-layout',str(out),str(B/log['text_file'])],capture_output=True,check=True);log['page_count']=len((B/log['text_file']).read_text().split('\f'))-1;print(key,log['source_url'],log['page_count'],flush=True)
 except Exception as e:log['error']=str(e);print(key,'ERROR',str(e),flush=True)
 logs.append(log);p.write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')
