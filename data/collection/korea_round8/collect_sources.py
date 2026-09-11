"""Retrieve bounded analyst-channel leads; retain original bytes and retrieval provenance."""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent
POSTS={'13920':'sector_20250912','17779':'sector_20260727','18529':'strategy_20260907','7857':'sector_20240215','11248':'samsung_20250131','13324':'samsung_20250731','14413':'samsung_20251030','16250':'samsung_20260403','16664':'samsung_20260430','17518':'samsung_20260706','17880':'samsung_20260730','8397':'hynix_20240422','8454':'hynix_20240426','11191':'hynix_20250123','13235':'hynix_20250724','14393':'hynix_20251029','16580':'hynix_20260423','17841':'hynix_20260729','18286':'hynix_20260819','16174':'hynix_20260325','16735':'hynix_20260506','12571':'sector_20250526','8954':'sector_20240612'}
def main():
 posts=json.loads((BASE/'discovery/meritz_posts.json').read_text());lp=BASE/'download_log.json';logs=json.loads(lp.read_text()) if lp.exists() else []
 for post,key in POSTS.items():
  key='meritz_'+key
  if any(x['key']==key and x.get('sha256') for x in logs):continue
  v=posts['merITz_tech/'+post];url=v['links'][0] if post=='18529' else v['links'][-1];p=BASE/'pdfs'/f'{key}.pdf'
  log={'key':key,'discovery_url':'https://t.me/merITz_tech/'+post,'redirect_url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_channel_post_timestamp':v['date']}
  try:
   result=subprocess.run(['curl','-LfsS','--max-time','30','--write-out','%{url_effective}',url,'-o',str(p)],capture_output=True,text=True,check=True);log['source_url']=result.stdout
   if not p.read_bytes().startswith(b'%PDF'):raise ValueError('Response is not a PDF')
   log['local_file']='pdfs/'+p.name;log['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();log['text_file']='text/'+key+'.txt'
   subprocess.run(['pdftotext','-layout',str(p),str(BASE/log['text_file'])],capture_output=True,check=True)
   log['page_count']=len((BASE/log['text_file']).read_text().split('\f'))-1
   print(key,log['source_url'],log['page_count'],flush=True)
  except Exception as e:log['error']=str(e);print(key,'ERROR',str(e),flush=True)
  logs.append(log);lp.write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
