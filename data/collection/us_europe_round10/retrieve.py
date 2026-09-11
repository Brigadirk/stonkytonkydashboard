"""Re-fetch the exact retained public sources into a fresh staging directory.

Run only when a new retrieval is wanted. Does not change originals or CSVs, use
accounts, enumerate image pages, or invoke a paid/download API. Preview links
are revalidated against the public getReportPreviewImages response. Expected
hash mismatches are reported rather than silently replacing frozen evidence.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=base / 'staging' / 'redownload')
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    sources = json.loads((base / 'download_log.json').read_text())
    selected = [s for s in sources if s.get('http_status') == 200 and
                (s.get('name', '').startswith('guosen_nvidia_') or s.get('name', '').startswith('capture_'))]
    records = []
    for source in selected:
        response = requests.get(source['source_url'], timeout=40)
        name = Path(source['local_file']).name
        path = args.destination / name
        path.write_bytes(response.content)
        digest = hashlib.sha256(response.content).hexdigest()
        records.append(dict(source_url=source['source_url'], retrieved_at=datetime.now(timezone.utc).isoformat(),
                            http_status=response.status_code, content_type=response.headers.get('Content-Type'),
                            local_file=str(path), sha256=digest, expected_sha256=source['sha256'],
                            matches_frozen_artifact=digest == source['sha256']))
        print(name, response.status_code, 'matches' if digest == source['sha256'] else 'changed')
    for doc, day in [('5027955', '2025/08/29'), ('5163387', '2025/11/24'), ('5665920', '2026/08/31')]:
        response = json.loads((args.destination / f'capture_{doc}_preview_api.txt').read_text())
        expected = f'report-image/{day}/{doc}-1.png'
        assert expected in response['data'], f'Public preview linkage changed for{doc}'
    (args.destination / 'retrieval_records.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
