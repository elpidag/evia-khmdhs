"""Fetch the curated Anti-nero supplement contracts into the DB.

Reads khmdhs/data/antinero_supplement.json (ADAMs discovered via Diavgeia,
verified by hand — see the file's _comment), fetches each contract from the
KHMDHS open-data API, RE-VERIFIES its relevance basis against the live
payload, and upserts it through the same khmdhs.db path as the main CLI.

An entry whose verification fails is NOT loaded and is reported loudly —
this is the guard that keeps non-Anti-nero contracts out of the DB even if
the curation file is edited carelessly.

Usage:
  .venv/bin/python -m khmdhs.antinero_loader --dry-run
  .venv/bin/python -m khmdhs.antinero_loader
Then rebuild scopes:
  .venv/bin/python -m khmdhs.scope_loader
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import requests

from khmdhs.api import fetch_contract
from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db, upsert_contract
from khmdhs.scope import FUND_ANTINERO_I, normalize_title

DATA_FILE = Path(__file__).parent / "data" / "antinero_supplement.json"


def verify_relevance(phase: str, basis: str, item: dict) -> str | None:
    """Check the fetched KHMDHS payload against the curated basis.

    Returns None when the contract is confirmed relevant, else a
    human-readable reason for refusing it.
    """
    funding = item.get("fundingDetails") or {}
    fund_num = (funding.get("publicFundingRefNum") or "").strip()
    norm_title = normalize_title(item.get("title"))
    org_vat = ((item.get("organizationVatNumber") or "")).strip()

    if org_vat and org_vat.replace(",", "") not in ("090273987", "90273987"):
        return f"unexpected contracting authority VAT {org_vat!r} (want ΥΠΕΝ)"

    if basis.startswith("fund:"):
        want = basis.split(":", 1)[1]
        if not fund_num.startswith(want):
            return f"funding {fund_num!r} does not match basis {want!r}"
        return None

    if basis.startswith("title:"):
        if phase == "antinero_ii" and "TOY II" in norm_title:
            return None
        if "ANTINERO" in norm_title:
            return None
        return f"title {item.get('title')!r} lacks the phase marker for basis {basis!r}"

    return f"unknown basis {basis!r}"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.antinero_loader")
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--sleep", type=float, default=0.3)
    p.add_argument("--refetch", action="store_true",
                   help="Re-fetch entries already in the contracts table")
    p.add_argument("--dry-run", action="store_true",
                   help="Fetch + verify but write nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    supplement: dict = json.loads(args.data.read_text(encoding="utf-8"))
    supplement.pop("_comment", None)

    conn = init_db(args.db)
    have = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}

    todo = [(adam, meta) for adam, meta in supplement.items()
            if args.refetch or adam not in have]
    if args.limit is not None:
        todo = todo[: args.limit]
    logging.info("%d supplement entries, %d already in DB, %d to fetch",
                 len(supplement), len(supplement) - len(todo), len(todo))

    session = requests.Session()
    n_loaded = n_refused = n_failed = 0
    refused: list[tuple[str, str]] = []
    for i, (adam, meta) in enumerate(todo, start=1):
        status, item, http_status, err = fetch_contract(session, adam)
        if status != "ok" or item is None:
            logging.error("[%d/%d] %s fetch failed: %s (%s)", i, len(todo), adam, status, err)
            n_failed += 1
            continue

        reason = verify_relevance(meta["phase"], meta["basis"], item)
        if reason is not None:
            logging.error("[%d/%d] %s REFUSED: %s", i, len(todo), adam, reason)
            refused.append((adam, reason))
            n_refused += 1
            continue

        if args.dry_run:
            logging.info("[%d/%d] DRY %s ok (%s, %s) — %s", i, len(todo), adam,
                         meta["phase"], meta["lot"], (item.get("title") or "")[:60])
        else:
            upsert_contract(conn, item)
            logging.info("[%d/%d] loaded %s (%s, %s)", i, len(todo), adam,
                         meta["phase"], meta["lot"])
        n_loaded += 1
        if args.sleep and i < len(todo):
            time.sleep(args.sleep)

    print()
    print("=" * 60)
    print(f"Anti-nero supplement loader — {len(todo)} entries processed")
    print(f"  verified {'(dry-run, not written)' if args.dry_run else 'and loaded'}: {n_loaded}")
    print(f"  refused (failed relevance check):  {n_refused}")
    print(f"  fetch failures:                    {n_failed}")
    for adam, reason in refused:
        print(f"    REFUSED {adam}: {reason}")
    print()
    print("Next: .venv/bin/python -m khmdhs.scope_loader")
    conn.close()
    return 1 if (n_refused or n_failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
