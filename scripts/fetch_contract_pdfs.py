"""Fetch every contract's signed PDF into the shared attachment cache.

Sweeps all `contracts.reference_number` rows, downloading any missing
`<ADAM>.pdf` into data/processed/pdf_cache/ (the same cache the web UI
proxy fills incidentally) and extracting `<ADAM>.txt` via pdftotext.
Resumable: existing files are skipped, so re-running after a rate-limit
abort continues where it stopped. Honours Retry-After on 429 and aborts
after 3 consecutive 429s (khmdhs.payment_validator.ensure_pdf machinery).

Usage:  .venv/bin/python scripts/fetch_contract_pdfs.py [--sleep 1.0]
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from khmdhs.config import CONTRACT_PDF_URL, DEFAULT_DB, PDF_CACHE_DIR
from khmdhs.payment_validator import RateLimited, ensure_pdf, pdf_text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    conn = sqlite3.connect(args.db)
    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts ORDER BY reference_number")]
    conn.close()

    session = requests.Session()
    state: dict = {}
    stats = {"cached": 0, "fetched": 0, "no_pdf": 0, "no_text": 0}
    try:
        for i, ref in enumerate(refs, 1):
            had = (args.cache / f"{ref}.pdf").exists()
            path = ensure_pdf(session, args.cache, ref, args.sleep, state,
                              url_template=CONTRACT_PDF_URL)
            if path is None:
                stats["no_pdf"] += 1
                continue
            stats["cached" if had else "fetched"] += 1
            if pdf_text(args.cache, ref) is None:
                stats["no_text"] += 1
            if i % 25 == 0:
                logging.info("progress %d/%d  %s", i, len(refs), stats)
    except RateLimited as e:
        logging.error("aborting sweep (%s) — re-run to resume", e)
        raise SystemExit(3)
    finally:
        logging.info("done: %s of %d contracts", stats, len(refs))


if __name__ == "__main__":
    main()
