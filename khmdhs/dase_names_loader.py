# -*- coding: utf-8 -*-
"""Load the curated bilingual ΔΑΣΕ display names into dase.sqlite.

`khmdhs/data/dase_display_names.json` (DATA_DECISIONS 2026-08-15) maps each
canonical co-op ΑΦΜ to its user-curated Greek + English display name — a
presentation layer on top of the registry spellings, which are NEVER
rewritten. This loader mirrors the other curated layers: full-replace into
`dase_display_names`, refusing malformed entries (non-canonical key, empty
name, cross-script homoglyphs — the exact error class the curation
normalized away), and WARNing when the file and the live co-op population
drift apart (a re-harvest can add a co-op faster than the curation).

Run after any harvest_dase.py load (hooked there) or standalone:
  python -m khmdhs.dase_names_loader --db data/processed/dase.sqlite
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import unicodedata
from pathlib import Path

from .config import DASE_DB

log = logging.getLogger(__name__)

NAMES_FILE = Path(__file__).parent / "data" / "dase_display_names.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dase_display_names (
    vat        TEXT PRIMARY KEY,   -- canonical ΑΦΜ (dase_queries.canonical_vat)
    display_el TEXT NOT NULL,
    display_en TEXT NOT NULL
)
"""


def _script_clean(el: str, en: str) -> bool:
    """True iff the Greek name has no Latin letters and vice versa."""
    for ch in el:
        if "LATIN" in unicodedata.name(ch, ""):
            return False
    for ch in en:
        if "GREEK" in unicodedata.name(ch, ""):
            return False
    return True


def load_names(conn: sqlite3.Connection, path: Path = NAMES_FILE) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = {k: v for k, v in data.items() if not k.startswith("_")}
    rows = []
    for vat, v in sorted(entries.items()):
        el = (v.get("el") or "").strip()
        en = (v.get("en") or "").strip()
        if not (len(vat) == 9 and vat.isdigit()):
            raise ValueError(f"non-canonical ΑΦΜ key in {path.name}: {vat!r}")
        if not el or not en:
            raise ValueError(f"empty display name for ΑΦΜ {vat}")
        if not _script_clean(el, en):
            raise ValueError(f"cross-script characters in ΑΦΜ {vat}: {el!r} / {en!r}")
        rows.append((vat, el, en))

    conn.execute(SCHEMA)
    conn.execute("DELETE FROM dase_display_names")
    conn.executemany(
        "INSERT INTO dase_display_names (vat, display_el, display_en) VALUES (?, ?, ?)",
        rows)
    conn.commit()

    # drift check vs the live co-op population (WARN only — a fresh harvest
    # may legitimately add a co-op before the user names it)
    from webui.dase_queries import canonical_vat, live_filter
    curated = {canonical_vat(r[0]) for r in conn.execute(
        "SELECT vat_number FROM dase_contractors")}
    live = set()
    for r in conn.execute(f"""
        SELECT DISTINCT c.vat_number FROM contractors c
        JOIN contracts co ON co.reference_number = c.reference_number
        WHERE {live_filter('co')}"""):
        cv = canonical_vat(r[0])
        if cv in curated:
            live.add(cv)
    named = {r[0] for r in rows}
    for vat in sorted(live - named):
        log.warning("live co-op %s has no curated display name", vat)
    for vat in sorted(named - live):
        log.warning("display name for %s matches no live co-op", vat)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="python -m khmdhs.dase_names_loader")
    parser.add_argument("--db", type=Path, default=DASE_DB)
    parser.add_argument("--names", type=Path, default=NAMES_FILE)
    args = parser.parse_args(argv)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        n = load_names(conn, args.names)
    finally:
        conn.close()
    print(f"loaded {n} display names into {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
