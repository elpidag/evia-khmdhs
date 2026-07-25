"""Incremental refresh: keep open contracts and their payments current.

The Anti-nero III/IV/2026 phases are still disbursing, so stored payment
links and amendment chains go stale. This command refetches the in-scope
contracts that can still change (no end date, or ended within the last 90
days), upserts only the ones whose payload actually changed, and then runs
the standard loader chain — a contract upsert CASCADE-deletes its scope and
region rows, so the loaders are NOT optional after any change:

    chain_loader → scope_loader → region_loader → payment_loader

Fetched payloads are appended to data/processed/refresh_backup_<date>.json
BEFORE anything is written to the DB (crash safety net), and a run summary
lands in data/processed/refresh_state.json. Contracts that changed but lack
curated regions — or classify without clear Anti-nero evidence — are
printed as an explicit manual-curation TODO list.

Usage:
  .venv/bin/python -m khmdhs.refresh [--all] [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from khmdhs import chain_loader, forest_loader, payment_loader, region_loader, scope_loader
from khmdhs.api import fetch_contract
from khmdhs.config import DATA_PROCESSED, DEFAULT_DB, THROTTLE_SECONDS
from khmdhs.db import init_db, upsert_contract

STATE_FILE = DATA_PROCESSED / "refresh_state.json"


def contract_changed(old: dict, new: dict) -> bool:
    """True when a refetched payload differs in a way we care about."""
    if (old.get("lastUpdateDate") or "") != (new.get("lastUpdateDate") or ""):
        return True
    if set(old.get("paymentRefNo") or []) != set(new.get("paymentRefNo") or []):
        return True
    if (old.get("nextRefNo") or "") != (new.get("nextRefNo") or ""):
        return True
    if bool(old.get("cancelled")) != bool(new.get("cancelled")):
        return True
    return False


def candidates(conn: sqlite3.Connection, include_all: bool) -> list[str]:
    """In-scope chain tips that can still change (or all of them)."""
    where = "" if include_all else (
        "AND (k.end_date IS NULL OR k.end_date >= date('now', '-90 days'))"
    )
    return [r[0] for r in conn.execute(f"""
        SELECT k.reference_number
        FROM contracts k JOIN contract_scope s USING (reference_number)
        WHERE s.in_scope = 1 {where}
        ORDER BY k.reference_number
    """)]


def curation_todos(conn: sqlite3.Connection, refs: list[str] | None = None) -> list[str]:
    """Human follow-ups: missing regions or unreviewed scope.

    Scans every in-scope contract (not just the refetched ones): the chain
    loader may have pulled brand-new chain members that were never in the
    candidate list but still need curated regions.
    """
    if refs is None:
        refs = [r[0] for r in conn.execute(
            "SELECT reference_number FROM contract_scope WHERE in_scope = 1")]
    todos = []
    for ref in refs:
        n_regions = conn.execute(
            "SELECT COUNT(*) FROM contract_project_regions WHERE reference_number = ?",
            (ref,)).fetchone()[0]
        row = conn.execute(
            "SELECT scope, basis, in_scope FROM contract_scope WHERE reference_number = ?",
            (ref,)).fetchone()
        scope, basis, in_scope = row if row else ("?", "?", 0)
        if in_scope and n_regions == 0:
            todos.append(f"{ref}: in scope but no curated regions (contract_regions.json)")
        if scope in ("antinero_unknown_phase",) or basis == "no_antinero_evidence":
            todos.append(f"{ref}: scope needs review ({scope}; {basis})")
        if in_scope and _has_forest_tables(conn):
            n_auth = conn.execute(
                "SELECT COUNT(*) FROM contract_forest_authorities WHERE reference_number = ?",
                (ref,)).fetchone()[0]
            if n_auth == 0 and not _forest_no_authority(conn, ref):
                todos.append(f"{ref}: in scope but no forest authority "
                             f"(forest_authorities.json aliases/overrides)")
    return todos


def _has_forest_tables(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name='contract_forest_authorities'").fetchone() is not None


def _forest_no_authority(conn: sqlite3.Connection, ref: str) -> bool:
    """True when the registry documents the contract as genuinely
    authority-less — directly or inherited through its prev-link chain."""
    try:
        registry, _ = forest_loader.load_registry()
    except SystemExit:
        return False
    documented = set(registry.get("no_authority", {}))
    seen: set[str] = set()
    cur: str | None = ref
    while cur and cur not in seen:
        if cur in documented:
            return True
        seen.add(cur)
        row = conn.execute(
            "SELECT prev_reference_no FROM contracts WHERE reference_number = ?",
            (cur,)).fetchone()
        cur = row[0] if row else None
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.refresh")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--all", action="store_true",
                        help="refresh every in-scope contract, not just open ones")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=THROTTLE_SECONDS)
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch + diff, write nothing, skip the loader chain")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = init_db(args.db)
    todo = candidates(conn, args.all)
    if args.limit is not None:
        todo = todo[: args.limit]
    logging.info("Refresh: %d candidate contract(s)%s", len(todo),
                 " (all in-scope)" if args.all else " (open or recently ended)")

    session = requests.Session()
    backup_path = DATA_PROCESSED / f"refresh_backup_{datetime.now(timezone.utc):%Y%m%d}.json"
    backup: list[dict] = (
        json.loads(backup_path.read_text(encoding="utf-8")) if backup_path.exists() else []
    )
    changed: list[str] = []
    n_unchanged = n_failed = 0
    for i, ref in enumerate(todo, start=1):
        status, item, http, err = fetch_contract(session, ref)
        if status != "ok" or item is None or item.get("referenceNumber") != ref:
            logging.error("[%d/%d] %s fetch failed: %s %s", i, len(todo), ref, status, err or http)
            n_failed += 1
            continue
        old_raw = conn.execute(
            "SELECT raw_json FROM contracts WHERE reference_number = ?", (ref,)
        ).fetchone()[0]
        if not contract_changed(json.loads(old_raw), item):
            n_unchanged += 1
        else:
            logging.info("[%d/%d] %s CHANGED", i, len(todo), ref)
            changed.append(ref)
            if not args.dry_run:
                backup.append(item)
                backup_path.write_text(
                    json.dumps(backup, ensure_ascii=False), encoding="utf-8")
                upsert_contract(conn, item)
        if i % 25 == 0:
            logging.info("… %d/%d checked (%d changed)", i, len(todo), len(changed))
        if args.sleep and i < len(todo):
            time.sleep(args.sleep)
    conn.close()

    if changed and not args.dry_run:
        # Any upsert wiped the FK-linked scope/region rows — rebuild everything.
        db_argv = ["--db", str(args.db)]
        print("\n-- chain_loader ------------------------------------------------")
        chain_loader.main(db_argv)
        print("\n-- scope_loader ------------------------------------------------")
        scope_loader.main(db_argv)
        print("\n-- region_loader -----------------------------------------------")
        region_loader.main(db_argv)
        print("\n-- forest_loader -----------------------------------------------")
        forest_loader.main(db_argv)
        print("\n-- payment_loader ----------------------------------------------")
        payment_loader.main(db_argv)

    conn = sqlite3.connect(args.db)
    todos = curation_todos(conn) if changed else []
    conn.close()

    summary = {
        "ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidates": len(todo), "changed": changed,
        "unchanged": n_unchanged, "failed": n_failed,
        "dry_run": args.dry_run, "curation_todos": todos,
    }
    if not args.dry_run:
        STATE_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")

    print()
    print("=" * 60)
    print(f"Refresh — {len(todo)} checked: {len(changed)} changed, "
          f"{n_unchanged} unchanged, {n_failed} failed"
          f"{' (dry-run, nothing written)' if args.dry_run else ''}")
    for ref in changed:
        print(f"  changed: {ref}")
    if todos:
        print("\n  MANUAL CURATION NEEDED:")
        for t in todos:
            print(f"    - {t}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
