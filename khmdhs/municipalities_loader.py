"""Load the curated per-contract δήμοι into the DB.

Source of truth: `khmdhs/data/contract_municipalities.json` — which δήμος
each in-scope Anti-nero contract worked in, read from its own placement
sentence or from the πρόσκληση it cites, with that sentence kept verbatim
(DATA_DECISIONS 2026-08-19). Attribution verdicts — which forest service a
δήμος is filed under where the contract assigns it to one that does not
serve it — stay in `municipality_overrides.json` and reach this file
through the extractor.

The rules the data follows (user-approved, 2026-08-19):
  * the call counts as evidence, and the row says which document said it;
  * a δήμος outside the contract's curated Π.Ε. is recorded and FLAGGED —
    the region layer is deliberately untouched;
  * pre-Καλλικράτης names and settlements resolve onto the δήμος that
    contains them today, keeping the document's wording as the quote.

Validates every entry and refuses to load on failure; WARNs (never fails)
for an in-scope contract with none, which is the honest majority (93).
Re-run after any contract refetch — CASCADE wipes these rows.

Usage:  .venv/bin/python -m khmdhs.municipalities_loader [--db path]
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

CURATED_FILE = Path(__file__).parent / "data" / "contract_municipalities.json"
GAZETTEER = Path(__file__).parent / "data" / "greek_municipalities.json"

log = logging.getLogger(__name__)


def _entries(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _validate(data: dict, gaz: dict) -> None:
    for ref, e in _entries(data).items():
        rows = e.get("municipalities")
        if not rows:
            raise SystemExit(f"contract_municipalities.json: {ref} has no rows")
        for m in rows:
            if m.get("code") not in gaz:
                raise SystemExit(f"contract_municipalities.json: {ref} names "
                                 f"unknown ΥΠΕΣ code {m.get('code')!r}")
            if not m.get("excerpt"):
                raise SystemExit(f"contract_municipalities.json: {ref}/"
                                 f"{m.get('code')} has no evidence excerpt")
            if gaz[m["code"]]["name"] != m.get("name"):
                raise SystemExit(
                    f"contract_municipalities.json: {ref}/{m['code']} is named "
                    f"{m.get('name')!r}, the gazetteer says "
                    f"{gaz[m['code']]['name']!r}")


def load_curated() -> tuple[dict, dict]:
    data = json.loads(CURATED_FILE.read_text(encoding="utf-8"))
    raw = json.loads(GAZETTEER.read_text(encoding="utf-8"))
    gaz = raw.get("municipalities", raw)
    _validate(data, gaz)
    return data, gaz


def write_db(conn: sqlite3.Connection, data: dict, gaz: dict) -> int:
    _validate(data, gaz)
    known = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    unknown = sorted(set(_entries(data)) - known)
    if unknown:
        raise SystemExit(f"contract_municipalities.json refs not in DB: {unknown}")

    today = date.today().isoformat()
    conn.execute("DELETE FROM contract_municipalities")
    conn.executemany(
        "INSERT INTO contract_municipalities (reference_number, municipality_code,"
        " name, region_pe, authority, source_ref, from_call, excerpt,"
        " outside_region, outside_pe_explained, note, curated_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(ref, m["code"], m["name"], m.get("pe"), m.get("authority"),
          m.get("source_ref"), m.get("from_call"), m["excerpt"],
          1 if m.get("outside_region") else 0, m.get("outside_pe_explained"),
          m.get("note") or (m.get("override") or {}).get("note")
          if isinstance(m.get("override"), dict) else m.get("note"), today)
         for ref, e in _entries(data).items() for m in e["municipalities"]])
    conn.commit()

    has_scope = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_scope'"
    ).fetchone()
    n_missing = 0
    if has_scope:
        for (ref,) in conn.execute(
                "SELECT reference_number FROM contract_scope WHERE in_scope = 1"):
            if ref not in _entries(data):
                n_missing += 1
    return n_missing


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    conn = db.init_db(args.db)
    data, gaz = load_curated()
    n_missing = write_db(conn, data, gaz)
    n, c, flagged, call = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT reference_number),"
        " SUM(outside_region), SUM(from_call IS NOT NULL)"
        " FROM contract_municipalities").fetchone()
    log.info("municipalities: %d rows over %d contracts (%d distinct δήμοι); "
             "%d read from the call, %d outside the contract's curated Π.Ε.; "
             "%d in-scope contracts name none",
             n, c, conn.execute("SELECT COUNT(DISTINCT municipality_code)"
                                " FROM contract_municipalities").fetchone()[0],
             call, flagged, n_missing)
    conn.close()


if __name__ == "__main__":
    main()
