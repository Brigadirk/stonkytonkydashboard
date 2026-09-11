import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


collector = module("collect_sources")
actuals = module("extract_sec_actuals")
pilot = module("compare_revenue_pilot")


class Response:
    status_code = 200
    url = "https://example.org/report.json"
    headers = {"Content-Type": "application/json"}

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        yield self.body


class ArchiveIntegrityTests(unittest.TestCase):
    def test_pilot_excludes_late_stale_and_consensus_rows(self):
        base = dict(company_id="sk_hynix", fiscal_period="FY2023", metric="revenue", observation_type="individual_analyst_forecast", ranking_status="unscored_availability_and_actuals_unreconciled", forecaster="Example", firm="Broker", currency="KRW", unit="KRW", value="100")
        outcome = dict(company_id="sk_hynix", fiscal_period="FY2023", currency="KRW", unit="KRW", earnings_release_date="2024-01-25")
        from datetime import date, timedelta
        cutoff = date(2024, 1, 25) - timedelta(days=180)
        rows = [dict(base, report_date=(cutoff-timedelta(days=20)).isoformat()),
                dict(base, report_date=cutoff.isoformat(), value="101"),
                dict(base, forecaster="Stale", report_date=(cutoff-timedelta(days=91)).isoformat()),
                dict(base, forecaster="Consensus", observation_type="report_embedded_consensus", report_date=(cutoff-timedelta(days=10)).isoformat()),
                dict(base, forecaster="Joint", observation_type="joint_team_forecast", report_date=(cutoff-timedelta(days=10)).isoformat())]
        _, chosen = pilot.select_at_cutoff(rows, outcome, 180)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["value"], "100")

    def test_refresh_keeps_old_vintage_and_resume_makes_no_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = collector.connect(root)
            seed = dict(source_id="test", company_ids="nvidia", source_kind="test", source_url=Response.url, expected_format="json", report_date="2021-01-01")
            with patch.object(collector.requests, "get", return_value=Response(b'{"eps":1}')) as get:
                self.assertEqual(collector.fetch_one(db, root, seed), "downloaded")
                self.assertEqual(collector.fetch_one(db, root, seed), "cached")
                self.assertEqual(get.call_count, 1)
            with patch.object(collector.requests, "get", return_value=Response(b'{"eps":2}')):
                self.assertEqual(collector.fetch_one(db, root, seed, refresh=True), "downloaded")
            rows = db.execute("SELECT * FROM downloads ORDER BY id").fetchall()
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]["local_file"], rows[1]["local_file"])
            self.assertEqual((root / rows[0]["local_file"]).read_bytes(), b'{"eps":1}')
            self.assertEqual((root / rows[1]["local_file"]).read_bytes(), b'{"eps":2}')
            self.assertEqual(rows[0]["report_date"], "2021-01-01")
            self.assertEqual(rows[1]["report_date"], "")
            db.close()

    def test_http_200_service_notice_is_not_saved_as_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = collector.connect(root)
            seed = dict(source_id="test", company_ids="sk_hynix", source_kind="analyst_report", source_url="https://example.org/report.pdf", expected_format="pdf")
            response = Response(b'<html><title>Service notice</title></html>')
            response.headers = {"Content-Type": "text/html"}
            with patch.object(collector.requests, "get", return_value=response):
                self.assertEqual(collector.fetch_one(db, root, seed), "failed")
            row = db.execute("SELECT * FROM downloads").fetchone()
            self.assertIsNone(row["local_file"])
            self.assertIn("Expected pdf", row["error"])
            db.close()

    def test_later_filings_excluded_and_comparative_period_preserved(self):
        source = dict(company_ids="nvidia", source_url="https://example.org/facts", local_file="facts.json", sha256="abc", retrieved_at="2026-09-10")
        facts = [dict(start="2021-01-01", end="2021-12-31", val=4, filed="2022-02-01", accn="first", fy=2021, fp="FY"),
                 dict(start="2021-01-01", end="2021-12-31", val=2, filed="2024-02-01", accn="split", fy=2023, fp="FY"),
                 dict(start="2021-01-01", end="2021-12-31", val=1, filed="2027-02-01", accn="future", fy=2026, fp="FY")]
        payload = {"facts": {"us-gaap": {"EarningsPerShareDiluted": {"units": {"USD/shares": facts}}}}}
        rows = list(actuals.extract(payload, source, "2020-09-10", "2026-09-10"))
        self.assertEqual([r["accession"] for r in rows], ["first", "split"])
        self.assertEqual([r["value"] for r in rows], [4, 2])
        self.assertEqual(rows[1]["period_end"], "2021-12-31")
        self.assertEqual(rows[1]["filing_fiscal_year"], 2023)


if __name__ == "__main__":
    unittest.main()
