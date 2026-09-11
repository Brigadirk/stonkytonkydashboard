"""Check four retained Naver daily closes without editing the central price file."""
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import csv,json,hashlib,ast
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
logs=json.loads((BASE/'retrieval_log.json').read_text())+json.loads((BASE/'html_verification_retrieval_log.json').read_text());bykey={r['key']:r for r in logs};rows=[]
for code,company in [('000660','sk_hynix'),('005930','samsung_electronics')]:
 for date in ['20250919','20260910']:
  api=bykey[code+'_'+date];data=ast.literal_eval((ROOT/api['local_file']).read_text().strip());assert data[0][4]=='종가'
  values=next(r for r in data[1:] if r[0]==date);close=values[4]
  html=bykey[code+('_daily_p24' if date=='20250919' else '_daily')];p=ROOT/html['local_file'];doc=BeautifulSoup(p.read_bytes().decode('euc-kr'),'html.parser');formatted=f'{date[:4]}.{date[4:6]}.{date[6:]}'
  tr=next(tr for tr in doc.select('tr') if tr.find('td') and tr.find('td').get_text(strip=True)==formatted);cells=[td.get_text(' ',strip=True) for td in tr.find_all('td')]
  assert int(cells[1].replace(',',''))==close;assert '종가' in doc.get_text()
  assert datetime.fromisoformat(api['recorded_at'])>datetime.fromisoformat(f'{date[:4]}-{date[4:6]}-{date[6:]}T06:30:00+00:00')
  rows.append(dict(company_id=company,ticker=code+'.KS',date=f'{date[:4]}-{date[4:6]}-{date[6:]}',currency='KRW',close=close,price_field='종가 (dated daily close)',status='dated_close_verified_against_original_html_and_chart_response',split_adjustment_policy='not_explicitly_documented_in_retained_source',share_basis='native_source_daily_close_no_conversion_applied',source_url=html['url'],source_file=html['local_file'],source_sha256=html['sha256'],api_url=api['url'],api_source_file=api['local_file'],api_source_sha256=api['sha256'],retrieved_at=api['recorded_at'],source_row=' | '.join(cells),notes='Specific historical row under dated daily close heading; no undated regularMarketPrice. Naver current stock page labels daily prices KRX-provided. Retrieval after completed regular session. No claim of dividend/split adjustment policy. Sep10 native close has no later normalization interval at Sep10 cutoff. No central price mutation.'))
for r in logs:
 if r.get('local_file'):assert hashlib.sha256((ROOT/r['local_file']).read_bytes()).hexdigest()==r['sha256']
with (BASE/'verified_dated_closes.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(BASE/'verified_dated_closes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
(BASE/'validation.json').write_text(json.dumps(dict(rows_verified=4,html_and_chart_close_matches=4,source_hashes_verified=True,split_adjustment_policy_verified=False,full_corporate_action_calendar_audited=False,central_prices_changed=False),indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['ticker','date','close']} for r in rows],indent=2))
