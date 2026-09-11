import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('availability',Path(__file__).resolve().parents[1]/'scripts/availability.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class AvailabilityTests(unittest.TestCase):
    def fixture(self,root):
        content=b'%PDF-1.4 test source';sha=hashlib.sha256(content).hexdigest()
        (root/'source.pdf').write_bytes(content);(root/'archived.pdf').write_bytes(content)
        digest=base64.b32encode(hashlib.sha1(content).digest()).decode().rstrip('=')
        cdx=[['timestamp','original','statuscode','digest'],['20240115123000','http://example.test/source.pdf','200',digest]]
        (root/'cdx.json').write_text(json.dumps(cdx));(root/'data/market').mkdir(parents=True)
        rule={'source_file':'source.pdf','source_sha256':sha,'archived_pdf_file':'archived.pdf','archived_pdf_sha256':sha,'cdx_evidence_file':'cdx.json','cdx_evidence_sha256':hashlib.sha256((root/'cdx.json').read_bytes()).hexdigest(),'captured_at':'2024-01-15T12:30:00Z','original_url':'https://example.test/source.pdf','replay_url':'https://web.archive.org/web/20240115123000id_/http://example.test/source.pdf'}
        self.save(root,rule);return rule
    def save(self,root,rule):
        (root/'data/market/availability_evidence.json').write_text(json.dumps([rule]))
    def test_exact_bytes_and_index_prove_only_next_day_availability_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rule=self.fixture(root);result=module.load_evidence(root)[rule['source_sha256']]
            self.assertEqual(result['verified_available_date'],'2024-01-16')
            self.assertEqual(result['verification_kind'],'verified_available_by_archive')
    def test_changed_pdf_and_forged_capture_date_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rule=self.fixture(root)
            self.save(root,{**rule,'captured_at':'2024-01-14T12:30:00Z'})
            with self.assertRaisesRegex(ValueError,'not bound'):module.load_evidence(root)
            self.save(root,rule);(root/'archived.pdf').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):module.load_evidence(root)
    def test_wrong_original_url_and_index_digest_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rule=self.fixture(root)
            self.save(root,{**rule,'original_url':'https://example.test/another.pdf'})
            with self.assertRaisesRegex(ValueError,'not bound'):module.load_evidence(root)
            cdx=json.loads((root/'cdx.json').read_text());cdx[1][3]='WRONG'
            (root/'cdx.json').write_text(json.dumps(cdx));rule['cdx_evidence_sha256']=hashlib.sha256((root/'cdx.json').read_bytes()).hexdigest();self.save(root,rule)
            with self.assertRaisesRegex(ValueError,'not bound'):module.load_evidence(root)

if __name__=='__main__':unittest.main()
