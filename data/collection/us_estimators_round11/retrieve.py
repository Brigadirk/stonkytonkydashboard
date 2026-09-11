"""Re-fetch exact publicly observed sources into a new folder; never replace evidence.

Scribd is an original-page host here. No login, subscription download endpoint,
blur removal, guessed page paths, token edits or alternate access controls are
used. Page32/35 URLs must remain explicitly advertised as unblurred in the
ordinary anonymous catalog before retrieval. Stop when that condition changes.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    frozen = json.loads((BASE / 'download_log.json').read_text())
    results = []

    def fetch(source):
        response = requests.get(source['url'], timeout=40)
        filename = Path(source['file']).name
        path = args.destination / filename
        path.write_bytes(response.content)
        digest = hashlib.sha256(response.content).hexdigest()
        results.append(dict(source_url=source['url'], local_file=str(path),
                            retrieved_at=datetime.now(timezone.utc).isoformat(),
                            http_status=response.status_code, sha256=digest,
                            matches_frozen_artifact=digest == source['sha256']))
        (args.destination / 'retrieval_log.json').write_text(json.dumps(results, indent=2) + '\n')
        response.raise_for_status()
        return response

    catalog = next(x for x in frozen if x['name'] == 'bernstein_public_catalog')
    html = fetch(catalog).text
    for name, page in [('bernstein_scribd_p32', 32), ('bernstein_original_p35', 35)]:
        source = next(x for x in frozen if x['name'] == name)
        link = re.search(rf'pageNum:\s+{page}\s*,.*?blur:\s*(\w+)\s*,.*?contentUrl: "([^"]+)"', html, re.S)
        if not link or link.group(1) != 'false' or link.group(2) != source['url']:
            raise RuntimeError(f'Public unblurred page{page} linkage changed; stop and review access.')
        fetch(source)
    for source in frozen:
        if source['name'] in ['dbs_nvidia_current', 'kgi_nvidia_20260226', 'kgi_nvidia_20250811', 'firstshanghai_newforce_20260909']:
            fetch(source)
    print(f'Retained {len(results)} public source responses; frozen originals and CSVs unchanged.')


if __name__ == '__main__':
    main()
