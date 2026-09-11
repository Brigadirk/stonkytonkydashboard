"""Bounded read-only public-channel page capture; metadata is retrieval evidence, not vintage proof."""
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import subprocess,json,hashlib,sys
BASE=Path(__file__).resolve().parent;B=BASE/'discovery';P=B/'meritz_posts.json'
def get(before):
 p=B/f'before_{before}.html';url=f'https://t.me/s/merITz_tech?before={before}';captured=datetime.now(timezone.utc).isoformat()
 if not p.exists():subprocess.run(['curl','-LfsS','--max-time','30',url,'-o',str(p)],check=True)
 captured=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()
 items=[]
 for d in BeautifulSoup(p.read_text(),'html.parser').select('.tgme_widget_message'):
  m=d.select_one('.tgme_widget_message_text');tm=d.select_one('time')
  if m:items.append((d.get('data-post'),{'date':tm.get('datetime') if tm else '', 'text':m.get_text(' ',strip=True),'links':[a.get('href') for a in m.select('a') if a.get('href','').startswith('http')],'discovery_url':url,'discovery_file':'discovery/'+p.name,'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'html_file_recorded_at':captured,'edited_visible':'edited' in str(d.select_one('.tgme_widget_message_meta')),'original_availability_verified':False}))
 return before,items
if __name__=='__main__':
 posts=json.loads(P.read_text()) if P.exists() else {}
 for before,items in ThreadPoolExecutor(max_workers=4).map(get,map(int,sys.argv[1:])):
  if len(sys.argv)<12:print('BEFORE',before,items[0][1]['date'] if items else '',items[-1][1]['date'] if items else '')
  for k,v in items:
   posts.setdefault(k,v)
   if '김선우' in v['text'] and 'Overnight' not in v['text'] and any(any(h in u for h in ['vo.la','han.gl','imeritz','tinyurl']) for u in v['links']):print(k,v['date'],v['text'][:150],v['links'])
 P.write_text(json.dumps(posts,ensure_ascii=False,indent=2)+'\n')
