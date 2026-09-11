from pathlib import Path
from datetime import datetime,timezone
import requests,hashlib,subprocess,json
BASE=Path(__file__).resolve().parent
SOURCES=[('meritz_samsung_20260108','https://buly.kr/HSYel4n'),('meritz_samsung_20260130','https://vo.la/YgZyEi7'),('meritz_hynix_20260130','https://vo.la/c83UJdZ'),('kb_samsung_20260123','https://rdata.kbsec.com/pdf_data/20260122215610647E.pdf'),('kb_hynix_20260114','https://rdata.kbsec.com/pdf_data/20260113194310367E.pdf'),('kb_samsung_20260223','https://rdata.kbsec.com/pdf_data/20260220140952410E.pdf')]
if __name__=='__main__':
 logs=[]
 for key,url in SOURCES:
  rec=dict(key=key,discovery_url=url,retrieved_at=datetime.now(timezone.utc).isoformat())
  try:
   p=BASE/'pdfs'/f'{key}.pdf'
   res=subprocess.run(['curl','--location','--fail','--silent','--show-error','--max-time','45','--write-out','%{url_effective}',url,'-o',str(p)],check=True,text=True,capture_output=True)
   rec['source_url']=res.stdout;data=p.read_bytes();assert data.startswith(b'%PDF'),data[:100]
   subprocess.run(['pdftotext','-layout',str(p),str(BASE/'text'/f'{key}.txt')],check=True)
   rec.update(local_file='pdfs/'+p.name,sha256=hashlib.sha256(data).hexdigest(),status='downloaded_original_pdf')
   print(key,rec['source_url'],len(data),flush=True)
  except Exception as e:rec['error']=str(e);print(key,rec.get('source_url'),str(e),flush=True)
  logs.append(rec)
 (BASE/'download_log.json').write_text(json.dumps(logs,indent=2)+'\n')
