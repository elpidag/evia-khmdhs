"""Load the curated Anti-nero work-type categories into the DB.

Source of truth: khmdhs/data/contract_categories.json —
    {"_categories": {key: {"label": …, "note": …}},
     ADAM: {"category": key, "title": "<descriptive PDF project title>",
            "source": "pdf" | "short_description" | "inherited:<ref>"}}
One category per in-scope contract so aggregates reconcile to the
programme total; the verbatim title is the evidence
(DATA_DECISIONS 2026-08-14; proposals from
scripts/extract_contract_categories.py, every verdict human-reviewed).

Validates every entry and refuses to load on failure; WARNs (does not
fail) when an in-scope contract has no curated category — new chain
members surface there and in khmdhs.refresh's TODO list. Re-run after any
contract refetch (CASCADE wipes the table's rows).

Usage:  .venv/bin/python -m khmdhs.categories_loader [--db path]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import date
from pathlib import Path

from khmdhs import db
from khmdhs.config import DEFAULT_DB

CATEGORIES_FILE = Path(__file__).parent / "data" / "contract_categories.json"

log = logging.getLogger(__name__)


def _validate(data: dict) -> None:
    cats = data.get("_categories") or {}
    if not cats:
        raise SystemExit("contract_categories.json: no _categories block")
    for key, m in cats.items():
        if not m.get("label"):
            raise SystemExit(f"contract_categories.json: {key} has no label")
    for ref, e in data.items():
        if ref == "_categories":
            continue
        if e.get("category") not in cats:
            raise SystemExit(
                f"contract_categories.json: {ref} has unknown category "
                f"{e.get('category')!r}")
        if not e.get("title"):
            raise SystemExit(f"contract_categories.json: {ref} has no title")
        if not e.get("source"):
            raise SystemExit(f"contract_categories.json: {ref} has no source")


def load_curated(path: Path = CATEGORIES_FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    _validate(data)
    return data


def write_db(conn: sqlite3.Connection, curated: dict) -> int:
    _validate(curated)
    cats = curated["_categories"]
    entries = {r: e for r, e in curated.items() if r != "_categories"}
    known = {r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts")}
    missing = sorted(set(entries) - known)
    if missing:
        raise SystemExit(f"contract_categories.json refs not in DB: {missing}")

    today = date.today().isoformat()
    conn.execute("DELETE FROM contract_categories")
    conn.executemany(
        "INSERT INTO contract_categories "
        "(reference_number, category, title, source, curated_at) "
        "VALUES (?,?,?,?,?)",
        [(ref, e["category"], e["title"], e["source"], today)
         for ref, e in entries.items()])
    conn.execute("DELETE FROM category_labels")
    conn.executemany(
        "INSERT INTO category_labels (category, label, note) VALUES (?,?,?)",
        [(key, m["label"], m.get("note")) for key, m in cats.items()])
    conn.commit()

    has_scope = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='contract_scope'").fetchone()
    if has_scope:
        uncovered = [r[0] for r in conn.execute(
            "SELECT reference_number FROM contract_scope WHERE in_scope = 1")
            if r[0] not in entries]
        for ref in uncovered:
            log.warning("%s: in scope but no curated category "
                        "(contract_categories.json)", ref)
    return len(entries)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    conn = db.init_db(args.db)
    n = write_db(conn, load_curated())
    mix = conn.execute(
        "SELECT category, COUNT(*) FROM contract_categories "
        "GROUP BY category ORDER BY COUNT(*) DESC").fetchall()
    logging.info("categories: %d contracts — %s", n,
                 ", ".join(f"{c} {k}" for k, c in mix))
    conn.close()


if __name__ == "__main__":
    main()
