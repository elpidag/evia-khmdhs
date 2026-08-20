# -*- coding: utf-8 -*-
"""Load the curated Anti-nero contractor display names into khmdhs.sqlite.

`khmdhs/data/contractor_display_names.json` (DATA_DECISIONS 2026-08-20) maps
each contractor ΑΦΜ to ONE canonical name — a presentation layer on top of the
registry spellings, which are NEVER rewritten and stay searchable. The same
pattern as the ΔΑΣΕ co-op names, one dataset over.

The name comes from the documents wherever the documents say it: a person is
written ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ only where a signed act holds the
patronymic or a document's initial and the register together prove it, and a
company is written under the δ.τ. its own contracts declare. Each row keeps the
ΑΔΑΜ it was read from, the register's name and every registry spelling, so the
page can show its own evidence.

Run standalone or from `khmdhs.refresh` (hooked there):
  .venv/Scripts/python -m khmdhs.contractor_names_loader
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
from pathlib import Path

from .config import DEFAULT_DB

log = logging.getLogger(__name__)

NAMES_FILE = Path(__file__).parent / "data" / "contractor_display_names.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contractor_display_names (
    vat        TEXT PRIMARY KEY,
    display_el TEXT NOT NULL,
    display_en TEXT,             -- only where a body has an official one
    kind       TEXT,             -- person / company / venture / unknown
    basis      TEXT,             -- how the name was decided
    source     TEXT,             -- the ΑΔΑΜ it was read from, where one exists
    registered TEXT,             -- the ΓΕΜΗ/VIES name, for the page's evidence
    note       TEXT
)
"""


def _entries(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def validate(data: dict) -> None:
    for vat, e in _entries(data).items():
        if not re.fullmatch(r"\d{9}", vat):
            raise SystemExit(f"contractor_display_names.json: {vat!r} is not an ΑΦΜ")
        name = (e.get("name") or "").strip()
        if not name:
            raise SystemExit(f"contractor_display_names.json: {vat} has no name")
        if name.isdigit():
            raise SystemExit(f"contractor_display_names.json: {vat} is named "
                             f"{name!r} — a number is not a name")
        # a display name must be findable from the registry too: the layer adds
        # a spelling, it never replaces the population
        if not e.get("spellings"):
            log.warning("%s (%s) carries no registry spelling", vat, name)


def load(db_path: Path = DEFAULT_DB, path: Path = NAMES_FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    entries = _entries(data)
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(SCHEMA)
        conn.execute("DELETE FROM contractor_display_names")
        conn.executemany(
            "INSERT INTO contractor_display_names (vat, display_el, display_en, "
            "kind, basis, source, registered, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(vat, e["name"].strip(), e.get("name_en"), e.get("kind"),
              e.get("basis"), e.get("source"), e.get("registered"),
              e.get("note")) for vat, e in entries.items()])
    # a contractor the curation has not reached shows its registry spelling —
    # honest, but the layer exists to stop that, so say it out loud
    missing = [r[0] for r in conn.execute(
        "SELECT DISTINCT co.vat_number FROM contractors co "
        "JOIN contract_scope s USING (reference_number) "
        "WHERE s.in_scope = 1 AND co.vat_number NOT IN "
        "(SELECT vat FROM contractor_display_names)")]
    conn.close()
    for vat in missing:
        log.warning("in-scope contractor %s has no curated display name", vat)
    log.info("Loaded %d display names (%d in-scope contractors uncovered)",
             len(entries), len(missing))
    return {"names": len(entries), "uncovered": len(missing)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m khmdhs.contractor_names_loader")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--curated", type=Path, default=NAMES_FILE)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, args.curated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
