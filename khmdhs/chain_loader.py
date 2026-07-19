"""Complete amendment chains: fetch missing prev/next contract versions.

KHMDHS links contract versions via `prevReferenceNo` (string) and
`nextRefNo` (string) — an amendment is a full ##SYMV######### record whose
prev points at the version it supersedes. Some chain members were never in
the source xlsx or the curated supplement, so aggregates could double- or
mis-count. This loader:

  1. repairs the `prev_reference_no` / `next_reference_no` columns from the
     stored raw payloads (an earlier extractor bug truncated nextRefNo);
  2. collects every SYMV ADAM referenced by any stored contract's links,
     fetches the ones missing from the DB and upserts them;
  3. repeats until closure (a fetched amendment may reference further
     versions).

Run `python -m khmdhs.scope_loader` and `python -m khmdhs.payment_loader`
afterwards so supersede chains, scopes and payment attribution pick up the
new versions.

Usage:
  .venv/bin/python -m khmdhs.chain_loader [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path

import requests

from khmdhs.api import fetch_contract
from khmdhs.config import DEFAULT_DB, THROTTLE_SECONDS
from khmdhs.db import init_db, record_failure, upsert_contract
from khmdhs.extract import parent_row


def repair_link_columns(conn: sqlite3.Connection) -> int:
    """Recompute prev/next columns from raw_json for every stored contract."""
    fixes = []
    for ref, raw in conn.execute(
        "SELECT reference_number, raw_json FROM contracts WHERE raw_json IS NOT NULL"
    ):
        p = parent_row(json.loads(raw))
        fixes.append((p["prev_reference_no"], p["next_reference_no"], ref))
    with conn:
        n = 0
        for prev, nxt, ref in fixes:
            cur = conn.execute(
                "UPDATE contracts SET prev_reference_no = ?, next_reference_no = ? "
                "WHERE reference_number = ? AND (prev_reference_no IS NOT ? OR next_reference_no IS NOT ?)",
                (prev, nxt, ref, prev, nxt),
            )
            n += cur.rowcount
    return n


def linked_symv_adams(conn: sqlite3.Connection) -> set[str]:
    """Every SYMV ADAM referenced by any stored contract's version links."""
    refs: set[str] = set()
    for prev, nxt in conn.execute(
        "SELECT prev_reference_no, next_reference_no FROM contracts"
    ):
        for cand in (prev, nxt):
            cand = (cand or "").strip()
            if "SYMV" in cand:
                refs.add(cand)
    return refs


def missing_chain_members(conn: sqlite3.Connection) -> set[str]:
    have = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    return linked_symv_adams(conn) - have


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.chain_loader")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sleep", type=float, default=THROTTLE_SECONDS)
    parser.add_argument("--max-rounds", type=int, default=10)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = init_db(args.db)
    n_repaired = repair_link_columns(conn)
    print(f"link columns repaired on {n_repaired} contracts")

    session = requests.Session()
    n_ok = n_fail = 0
    fetched: list[str] = []
    failed: set[str] = set()
    for round_no in range(1, args.max_rounds + 1):
        missing = missing_chain_members(conn) - failed
        if not missing:
            break
        print(f"round {round_no}: {len(missing)} missing chain member(s)")
        if args.dry_run:
            for adam in sorted(missing):
                print(f"  {adam}")
            break
        for adam in sorted(missing):
            status, item, http, err = fetch_contract(session, adam)
            if status == "ok" and item is not None:
                if item.get("referenceNumber") != adam:
                    record_failure(conn, adam, "mismatch", http,
                                   f"API returned {item.get('referenceNumber')!r}")
                    failed.add(adam)
                    n_fail += 1
                else:
                    upsert_contract(conn, item)
                    fetched.append(adam)
                    n_ok += 1
            else:
                record_failure(conn, adam, status, http, err)
                logging.error("FAILED %s: %s %s", adam, status, err or http)
                failed.add(adam)
                n_fail += 1
            time.sleep(args.sleep)

    print()
    print("=" * 60)
    print(f"Chain loader — {n_ok} fetched, {n_fail} failed")
    for adam in fetched:
        row = conn.execute(
            "SELECT prev_reference_no, total_cost_with_vat FROM contracts WHERE reference_number = ?",
            (adam,)).fetchone()
        print(f"  {adam}  prev={row[0]}  €{(row[1] or 0):,.2f}")
    if n_ok:
        print("\nNow re-run: python -m khmdhs.scope_loader && python -m khmdhs.payment_loader")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
