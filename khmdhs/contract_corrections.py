"""Apply curated stated-value corrections to contracts.

Mirror of payment_loader.apply_corrections for the contracts table: the
registry occasionally keys a contract's stated value wrong (the flagship
case is a ×10-scale digit glitch, DATA_DECISIONS 2026-08-14); the true
figures, documented from the signed PDF, live in
khmdhs/data/dase_contract_corrections.json and are re-stamped here.

Must run AFTER any pass that upserts contracts (harvest_dase.py `load`
calls it last): INSERT OR REPLACE restores the registry values and nulls
correction_note.

Usage:
  .venv/bin/python -m khmdhs.contract_corrections --db data/processed/dase.sqlite
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from pathlib import Path

from khmdhs.config import DASE_DB
from khmdhs.db import init_db

CORRECTIONS_FILE = Path(__file__).parent / "data" / "dase_contract_corrections.json"
PAYMENT_CORRECTIONS_FILE = Path(__file__).parent / "data" / "dase_payment_corrections.json"
# the khmdhs (Anti-nero) DB's own corrections file, same format — applied by
# khmdhs.refresh after the refetch/upsert phase (DATA_DECISIONS 2026-08-14)
KHMDHS_CORRECTIONS_FILE = Path(__file__).parent / "data" / "contract_corrections.json"


def apply_contract_corrections(conn: sqlite3.Connection,
                               path: Path = CORRECTIONS_FILE) -> int:
    """UPDATE stored contracts (and their objects rows) from the curated
    corrections file. Two entry forms: amount overrides, and
    `exclude: true` + `duplicate_of` for registry double-postings (sets
    cancelled = 1 so every aggregate drops the twin, while the row and its
    page stay reachable and cross-linked). Idempotent; returns the number
    of corrected contracts."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_comment", None)
    n = 0
    with conn:
        for ref, fix in data.items():
            if fix.get("exclude"):
                cur = conn.execute(
                    """UPDATE contracts SET cancelled = 1,
                           duplicate_of = ?, correction_note = ?
                       WHERE reference_number = ?""",
                    (fix.get("duplicate_of"), fix.get("reason"), ref))
            else:
                cur = conn.execute(
                    """UPDATE contracts SET
                           total_cost_with_vat = COALESCE(?, total_cost_with_vat),
                           total_cost_without_vat = COALESCE(?, total_cost_without_vat),
                           correction_note = ?
                       WHERE reference_number = ?""",
                    (fix.get("total_cost_with_vat"),
                     fix.get("total_cost_without_vat"),
                     fix.get("reason"), ref))
            if cur.rowcount == 0:
                logging.warning("correction for %s matched no stored contract", ref)
                continue
            n += 1
            for seq, eur in (fix.get("objects") or {}).items():
                cur = conn.execute(
                    "UPDATE contract_objects SET cost_without_vat = ? "
                    "WHERE reference_number = ? AND seq = ?",
                    (eur, ref, int(seq)))
                if cur.rowcount == 0:
                    logging.warning("objects correction for %s seq %s matched no row",
                                    ref, seq)
    return n


def apply_all(conn: sqlite3.Connection,
              contracts_path: Path = CORRECTIONS_FILE,
              payments_path: Path = PAYMENT_CORRECTIONS_FILE) -> tuple[int, int]:
    """Contracts + payments corrections in one pass (the harvest-load hook
    and the CLI both use this). Payment entries reuse the tested
    payment_loader.apply_corrections verbatim."""
    n_c = apply_contract_corrections(conn, contracts_path)
    from khmdhs.payment_loader import apply_corrections as apply_payment_corrections
    n_p = apply_payment_corrections(conn, payments_path)
    return n_c, n_p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.contract_corrections")
    parser.add_argument("--db", type=Path, default=DASE_DB)
    parser.add_argument("--corrections", type=Path, default=CORRECTIONS_FILE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = init_db(args.db)  # runs the ALTER guard so correction_note exists
    n, n_p = apply_all(conn, args.corrections)
    print(f"applied {n} contract + {n_p} payment curated corrections to {args.db}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
