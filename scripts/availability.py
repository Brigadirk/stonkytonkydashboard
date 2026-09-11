"""Validate archived bytes and the capture record before admitting availability evidence."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from urllib.parse import urlparse

def load_evidence(root):
    path=root/'data/market/availability_evidence.json'
    if not path.exists():
        return {}
    records=json.loads(path.read_text())
    result={}
    for rule in records:
        artifacts={}
        for file_key,hash_key in [('source_file','source_sha256'),('archived_pdf_file','archived_pdf_sha256'),('cdx_evidence_file','cdx_evidence_sha256')]:
            content=(root/rule[file_key]).read_bytes()
            if hashlib.sha256(content).hexdigest()!=rule[hash_key]:
                raise ValueError('Availability evidence hash mismatch: '+rule[file_key])
            artifacts[file_key]=content
        if artifacts['source_file']!=artifacts['archived_pdf_file']:
            raise ValueError('Archived PDF differs from the forecast source')
        captured=datetime.fromisoformat(rule['captured_at'].replace('Z','+00:00'))
        if captured.tzinfo is None:
            raise ValueError('Archive capture requires an explicit timezone')
        captured=captured.astimezone(timezone.utc)
        stamp=captured.strftime('%Y%m%d%H%M%S')
        digest=base64.b32encode(hashlib.sha1(artifacts['source_file']).digest()).decode().rstrip('=')
        cdx=json.loads(artifacts['cdx_evidence_file'])
        if not cdx or not all(k in cdx[0] for k in ['timestamp','original','statuscode','digest']):
            raise ValueError('Archive index lacks capture fields')
        def same_url(url):
            a,b=urlparse(url),urlparse(rule['original_url'])
            return (a.netloc.lower(),a.path,a.query)==(b.netloc.lower(),b.path,b.query)
        matches=[dict(zip(cdx[0],row)) for row in cdx[1:]]
        if not any(r['timestamp']==stamp and r['statuscode']=='200' and r['digest']==digest and same_url(r['original']) for r in matches):
            raise ValueError('Archive timestamp, original URL and content digest are not bound by the retained index')
        replay=urlparse(rule['replay_url'])
        if replay.netloc!='web.archive.org' or not replay.path.startswith('/web/'+stamp+'id_/'):
            raise ValueError('Replay URL does not match the archive capture')
        entry={'verified_available_date':(captured.date()+timedelta(days=1)).isoformat(),
               'verified_available_at':captured.isoformat(),'availability_evidence_url':rule['replay_url'],
               'verification_kind':'verified_available_by_archive'}
        old=result.get(rule['source_sha256'])
        if old is None or entry['verified_available_at']<old['verified_available_at']:
            result[rule['source_sha256']]=entry
    return result
