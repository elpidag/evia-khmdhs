"""Fetch signed PDFs into the shared attachment cache.

By default sweeps all `contracts.reference_number` rows; `--acts KIND`
sweeps the upstream procurement acts of `linked_acts` instead (auction =
the κατακύρωση/κατανομή award decisions, which carry the per-assignment
tables: assignee, δαπάνη, συστάδα, δάσος, λήμμα). Downloads any missing
`<ADAM>.pdf` and extracts `<ADAM>.txt` via pdftotext (UTF-8; see
`payment_validator.pdf_text`). `--refetch-text` re-extracts the sidecar
of every already-cached PDF without re-downloading — used to repair the
pre-2026-08-17 sidecars that were written without `-enc UTF-8` and so
contain no Greek at all.

Resumable: existing files are skipped, so re-running after a rate-limit
abort continues where it stopped. Honours Retry-After on 429 and aborts
after 3 consecutive 429s (khmdhs.payment_validator.ensure_pdf machinery).

Usage:
  .venv/bin/python scripts/fetch_contract_pdfs.py [--sleep 1.0]
  .venv/bin/python scripts/fetch_contract_pdfs.py --db data/processed/dase.sqlite \
      --cache data/processed/dase_pdf_cache --acts auction
  .venv/bin/python scripts/fetch_contract_pdfs.py --cache <dir> --refetch-text
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# help text and log lines carry Greek; a cp1252 console would crash on
# --help before argparse ever returns
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:                      # pragma: no cover
    pass

import requests

from khmdhs.config import (AUCTION_PDF_URL, CONTRACT_PDF_URL, DEFAULT_DB,
                           NOTICE_PDF_URL, PDF_CACHE_DIR, REQUEST_PDF_URL)
from khmdhs.payment_validator import RateLimited, ensure_pdf, pdf_text

ACT_URLS = {
    "auction": AUCTION_PDF_URL,
    "notice": NOTICE_PDF_URL,
    "request": REQUEST_PDF_URL,
    "approved_request": REQUEST_PDF_URL,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--acts", choices=sorted(ACT_URLS),
                    help="sweep linked_acts of this kind instead of contracts")
    ap.add_argument("--refetch-text", action="store_true",
                    help="re-extract .txt for already-cached PDFs (no downloads)")
    ap.add_argument("--adams", type=Path,
                    help="fetch exactly the ΑΔΑΜ listed in this file (one per "
                         "line) with --acts' URL template, instead of sweeping "
                         "the DB. For acts a contract's TEXT cites but the "
                         "registry never declared: 102 of the 128 προσκλήσεις "
                         "the Anti-nero contracts quote are unknown to "
                         "contract_linked_acts (DATA_DECISIONS 2026-08-18).")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.refetch_text:
        pdfs = sorted(args.cache.glob("*.pdf"))
        n_ok = n_bad = 0
        for i, p in enumerate(pdfs, 1):
            if pdf_text(args.cache, p.stem, refetch=True) is None:
                n_bad += 1
            else:
                n_ok += 1
            if i % 250 == 0:
                logging.info("re-extracted %d/%d", i, len(pdfs))
        logging.info("re-extracted %d sidecars (%d unreadable) in %s",
                     n_ok, n_bad, args.cache)
        return

    url_template = ACT_URLS[args.acts] if args.acts else CONTRACT_PDF_URL
    if args.adams:
        refs = [ln.strip() for ln in
                args.adams.read_text(encoding="utf-8").splitlines() if ln.strip()]
        logging.info("fetching %d listed ΑΔΑΜ as kind=%s", len(refs), args.acts)
        conn = None
    else:
        conn = sqlite3.connect(args.db)
    if args.adams:
        pass
    elif args.acts:
        refs = [r[0] for r in conn.execute(
            "SELECT DISTINCT adam FROM linked_acts WHERE kind = ? ORDER BY adam",
            (args.acts,))]
    else:
        refs = [r[0] for r in conn.execute(
            "SELECT reference_number FROM contracts ORDER BY reference_number")]
    if conn is not None:
        conn.close()

    session = requests.Session()
    state: dict = {}
    stats = {"cached": 0, "fetched": 0, "no_pdf": 0, "no_text": 0}
    try:
        for i, ref in enumerate(refs, 1):
            had = (args.cache / f"{ref}.pdf").exists()
            try:
                path = ensure_pdf(session, args.cache, ref, args.sleep, state,
                                  url_template=url_template)
            except requests.exceptions.RequestException as exc:
                # one unreachable document must not end the sweep: the
                # registry occasionally stalls on a single attachment, and
                # the run is resumable anyway (skipped refs stay uncached)
                logging.warning("%s: %s — skipped", ref, type(exc).__name__)
                stats["no_pdf"] += 1
                continue
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
        logging.info("done: %s of %d %s", stats, len(refs),
                     args.acts or "contracts")


if __name__ == "__main__":
    main()
