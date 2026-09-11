"""Download only the explicitly enumerated public report URLs in sources.csv."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import re
import subprocess
import time
import requests

BASE = Path(__file__).resolve().parent
FIELDS = ['source_url', 'local_file', 'company_ids', 'firm', 'analyst_name',
          'report_date', 'retrieved_at', 'sha256', 'status', 'notes',
          'text_file', 'report_timestamp', 'model_dates', 'http_status']

def collect():
    session = requests.Session()
    rows = list(csv.DictReader((BASE / 'sources.csv').open()))
    output = []
    for source in rows:
        row = dict.fromkeys(FIELDS, '')
        row.update(source)
        row['retrieved_at'] = datetime.now(timezone.utc).isoformat()
        filename = source['file_name']
        row.pop('file_name', None)
        path = BASE / 'pdfs' / filename
        txt = BASE / 'text' / (path.stem + '.txt')
        try:
            if path.exists():
                data = path.read_bytes()
                row['http_status'] = 'cached'
            else:
                response = session.get(source['source_url'], timeout=30)
                row['http_status'] = str(response.status_code)
                response.raise_for_status()
                data = response.content
                if not data.startswith(b'%PDF'):
                    raise ValueError('Response is not a PDF')
                path.write_bytes(data)
                time.sleep(0.4)
            subprocess.run(['pdftotext', '-layout', str(path), str(txt)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            text = txt.read_text(errors='replace')
            row['local_file'] = str(path.relative_to(BASE.parents[2]))
            row['text_file'] = str(txt.relative_to(BASE.parents[2]))
            row['sha256'] = hashlib.sha256(data).hexdigest()
            row['status'] = 'downloaded_pending_content_review'
            first = text.split('\f')[0]
            match = re.search(r'Report as of\s+(\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}), UTC', first)
            if match:
                parsed = datetime.strptime(match.group(1), '%d %b %Y %H:%M').replace(tzinfo=timezone.utc)
                row['report_timestamp'] = parsed.isoformat()
                row['report_date'] = parsed.date().isoformat()
            elif source['firm'] == 'BOCOM International':
                match = re.search(r'\b(\d{1,2} [A-Za-z]+ 20\d{2})\b', first)
                if match:
                    try:
                        row['report_date'] = datetime.strptime(match.group(1), '%d %B %Y').date().isoformat()
                    except ValueError:
                        pass
            model = re.findall(r'(?:Forecast Revisions as of|Data as of|data as of)\s+(\d{1,2} [A-Za-z]+ \d{4})', text)
            row['model_dates'] = ';'.join(dict.fromkeys(model))
            print(filename, row['report_date'], len(data), flush=True)
        except Exception as exc:
            row['status'] = 'download_failed'
            row['notes'] += '; ' + type(exc).__name__ + ': ' + str(exc)
            print(filename, row['status'], row['http_status'], flush=True)
        output.append(row)
        with (BASE / 'download_log.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(output)

if __name__ == '__main__':
    collect()
