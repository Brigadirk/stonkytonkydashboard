"""Capture public Meritz channel search pages only as discovery, never vintage proof."""
from pathlib import Path
import requests,bs4,json,hashlib,datetime
from concurrent.futures import ThreadPoolExecutor
BASE=Path(__file__).resolve().parent
QUERIES=['SK하이닉스(000660)','삼성전자(005930)','김선우 적정주가','김선우 전망']
def run(q):
 posts={};url='https://t.me/s/merITz_tech';params={'q':q}
 for n in range(10):
  r=requests.get(url,params=params,timeout=30);r.raise_for_status();s=bs4.BeautifulSoup(r.text,'html.parser');key=hashlib.sha256(r.url.encode()).hexdigest()[:16];p=BASE/'discovery'/f'{key}.html';p.write_text(r.text)
  dates=[]
  for d in s.select('.tgme_widget_message'):
   tm=d.select_one('time');t=d.select_one('.tgme_widget_message_text')
   if not tm or not t:continue
   date=tm.get('datetime');dates.append(date)
   posts[d.get('data-post')]={'date':date,'text':t.get_text(' ',strip=True),'links':[a.get('href') for a in t.select('a') if a.get('href','').startswith('http')],'discovery_url':r.url,'discovery_file':str(p.relative_to(BASE)),'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_availability_verified':False}
  more=next((a for a in s.select('.tme_messages_more') if 'before=' in a.get('href','')),None)
  if not dates or max(dates)<'2021-01-01':break
  before=min(int(k.split('/')[-1]) for k in posts)
  url='https://t.me/s/merITz_tech';params={'q':q,'before':before}
 return posts
allposts={}
for posts in ThreadPoolExecutor(max_workers=4).map(run,QUERIES):allposts.update(posts)
(BASE/'discovery/posts.json').write_text(json.dumps(allposts,ensure_ascii=False,indent=2)+'\n')
print('posts',len(allposts))
for k,v in sorted(allposts.items(),key=lambda kv:kv[1]['date']):
 if v['date']>='2021' and '김선우' in v['text'] and 'Overnight' not in v['text'] and v['links']: print(k,v['date'],v['text'][:130],v['links'])
