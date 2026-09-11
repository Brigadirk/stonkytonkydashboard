#!/usr/bin/env python3
"""Download reviewed source URLs and retain immutable content plus an audit log.

No discovery, authentication, paid proxy, or analyst ranking is performed here.
Uses requests with certificate verification; pdftotext is optional for PDF text.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
from urllib.parse import urlsplit
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 40 * 1024 * 1024


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(root):
    (root / "data").mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "data/archive.sqlite")
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY, source_id TEXT NOT NULL,
            company_ids TEXT NOT NULL, source_kind TEXT NOT NULL,
            source_url TEXT NOT NULL, final_url TEXT, report_date TEXT,
            firm TEXT, analyst_name TEXT, discovered_from TEXT,
            retrieved_at TEXT NOT NULL, status TEXT NOT NULL,
            http_status INTEGER, content_type TEXT, byte_count INTEGER,
            sha256 TEXT, local_file TEXT, text_file TEXT, error TEXT
        );
        CREATE INDEX IF NOT EXISTS downloads_url ON downloads(source_url);
    """)
    return db


def classify(body, content_type):
    """Check the body, so an HTML error page cannot masquerade as a PDF."""
    if body[:1024].lstrip().startswith(b"%PDF-"):
        return "pdf"
    if "json" in content_type or body.lstrip().startswith((b"{", b"[")):
        json.loads(body)
        return "json"
    if "html" in content_type or b"<html" in body[:4096].lower():
        return "html"
    raise ValueError("Unrecognized response format")


def store_blob(root, body, extension):
    digest = hashlib.sha256(body).hexdigest()
    relative = Path("data/raw") / digest[:2] / f"{digest}.{extension}"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Existing archive file failed checksum: {relative}")
    else:
        with path.open("xb") as f:
            f.write(body)
    return digest, relative.as_posix()


def record(db, row):
    keys = list(row)
    db.execute(f"INSERT INTO downloads ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", list(row.values()))
    db.commit()


def fetch_one(db, root, seed, refresh=False, timeout=25):
    url = seed["source_url"]
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Expected a public HTTP(S) source URL without credentials")
    previous = db.execute("SELECT * FROM downloads WHERE source_url=? AND status='downloaded' ORDER BY id DESC LIMIT 1", (url,)).fetchone()
    if not previous and db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_catalog'").fetchone():
        previous = db.execute("SELECT * FROM source_catalog WHERE source_url=? AND local_file != '' AND document_kind NOT IN ('excluded','web_extract') LIMIT 1", (url,)).fetchone()
    if previous and not refresh:
        path = root / previous["local_file"]
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != previous["sha256"]:
            raise ValueError(f"Cached file missing or corrupt: {previous['local_file']}")
        return "cached"
    row = {key: seed.get(key, "") for key in ("source_id", "company_ids", "source_kind", "source_url", "report_date", "firm", "analyst_name", "discovered_from")}
    row.update(retrieved_at=utc_now(), status="failed")
    try:
        headers = {"User-Agent": os.environ.get("ARCHIVE_USER_AGENT", "AIValuationDashboard/0.1 private research (Dirk)"), "Accept": "application/json,application/pdf,text/html;q=0.9,*/*;q=0.5"}
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as response:
            row.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get("Content-Type", ""))
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Response exceeds 40 MiB archive limit")
            body = b"".join(chunks)
        if len(body) > MAX_BYTES:
            raise ValueError("Response exceeds 40 MiB archive limit")
        extension = classify(body, row["content_type"])
        expected = seed.get("expected_format", "")
        if expected and extension != expected:
            raise ValueError(f"Expected {expected}; received {extension}")
        # Do not mark a HTTP-200 challenge or sign-in page as useful source content.
        if extension == "html":
            title = body[:16000].lower()
            if any(token in title for token in (b"<title>just a moment", b"<title>access denied", b"<title>sign in", b"<title>login")):
                raise ValueError("Access challenge or login page")
        digest, local_file = store_blob(root, body, extension)
        row.update(status="downloaded", byte_count=len(body), sha256=digest, local_file=local_file)
        if previous and previous["sha256"] != digest:
            row["report_date"] = ""
            row["error"] = "New content at known URL; printed report date needs review"
        if extension == "pdf" and shutil.which("pdftotext"):
            text_file = str(Path(local_file).with_suffix(".txt"))
            result = subprocess.run(["pdftotext", "-layout", str(root / local_file), str(root / text_file)], capture_output=True, timeout=30)
            if result.returncode == 0:
                row["text_file"] = text_file
            else:
                row["error"] = "PDF retained; text extraction failed"
    except (requests.RequestException, TimeoutError, ValueError, OSError, subprocess.TimeoutExpired) as e:
        row["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    record(db, row)
    return row["status"]


def export_log(db, root):
    rows = db.execute("SELECT * FROM downloads ORDER BY id").fetchall()
    if rows:
        with (root / "data/download_log.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(dict(row) for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100, help="Maximum source rows processed this run")
    parser.add_argument("--refresh", action="store_true", help="Fetch again while preserving all prior versions")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests to the same host; minimum 0.2")
    args = parser.parse_args()
    if args.limit < 1 or args.delay < 0.2:
        parser.error("limit must be positive and delay at least 0.2 seconds")
    with args.seeds.open(newline="") as f:
        seeds = list(csv.DictReader(f))
    db = connect(ROOT)
    counts = {}
    last_by_host = {}
    try:
        for seed in seeds[:args.limit]:
            host = urlsplit(seed["source_url"]).hostname
            wait = args.delay - (time.monotonic() - last_by_host.get(host, 0))
            if wait > 0:
                time.sleep(wait)
            status = fetch_one(db, ROOT, seed, refresh=args.refresh)
            last_by_host[host] = time.monotonic()
            counts[status] = counts.get(status, 0) + 1
            print(f"{seed['source_id']}: {status}", flush=True)
    finally:
        export_log(db, ROOT)
        db.close()
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
