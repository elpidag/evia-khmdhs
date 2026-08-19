"""Load the two curated document-read layers into the DB.

Sources of truth (DATA_DECISIONS 2026-08-19):

* `khmdhs/data/contract_work_themes.json` — what the works ARE, multi-label,
  from the descriptive project title in each contract's own signed PDF, with
  the verbatim clause per theme; plus the CPV codes that name work the title
  does not, kept as NOTES because the CPV list belongs to the call and is
  shared by all its lots.
* `khmdhs/data/contract_durations.json` — the deadline the contract states
  and the clock it starts on, read through the chain, with the ΚΗΜΔΗΣ figure
  beside it as the cross-check. Three contracts state a fire season instead
  of a duration; Greece's runs 1 May – 31 October, so their deadline is the
  31 October of the year they name (user, 2026-08-19).

Both files carry an `_overrides` block for per-ΑΔΑΜ hand corrections; the
extractor merges it on regeneration, so a correction survives a re-run.

Validates every entry and refuses to load on failure; WARNs (never fails)
when an in-scope contract carries neither. Re-run after any contract
refetch — CASCADE wipes these rows like every other child table.

Usage:  .venv/bin/python -m khmdhs.details_loader [--db path]
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

THEMES_FILE = Path(__file__).parent / "data" / "contract_work_themes.json"
DURATIONS_FILE = Path(__file__).parent / "data" / "contract_durations.json"

log = logging.getLogger(__name__)

_UNITS = {"months", "days", "years"}
_BASES = {"signature", "works_start", "publication", "protocol"}


def _entries(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _validate_themes(data: dict) -> None:
    vocab = data.get("_themes") or {}
    if not vocab:
        raise SystemExit("contract_work_themes.json: no _themes block")
    for key, m in vocab.items():
        if not (m.get("el") and m.get("en")):
            raise SystemExit(f"contract_work_themes.json: {key} lacks a label")
    for ref, e in _entries(data).items():
        for t in e.get("themes", []):
            if t.get("key") not in vocab:
                raise SystemExit(f"contract_work_themes.json: {ref} has unknown "
                                 f"theme {t.get('key')!r}")
            if not t.get("excerpt"):
                raise SystemExit(f"contract_work_themes.json: {ref}/{t['key']} "
                                 f"has no evidence excerpt")
        for c in e.get("cpv_notes", []):
            if c.get("theme") not in vocab or not c.get("cpv"):
                raise SystemExit(f"contract_work_themes.json: {ref} has a bad "
                                 f"cpv note {c!r}")
        if e.get("themes") and not e.get("source"):
            raise SystemExit(f"contract_work_themes.json: {ref} has no source")


def _validate_durations(data: dict) -> None:
    for ref, e in _entries(data).items():
        if e.get("unit") and e["unit"] not in _UNITS:
            raise SystemExit(f"contract_durations.json: {ref} unit {e['unit']!r}")
        if e.get("basis") and e["basis"] not in _BASES:
            raise SystemExit(f"contract_durations.json: {ref} basis {e['basis']!r}")
        if not (e.get("n") or e.get("fire_season")):
            raise SystemExit(f"contract_durations.json: {ref} states neither a "
                             f"number nor a season")
        if e.get("n") and not e.get("excerpt"):
            raise SystemExit(f"contract_durations.json: {ref} has no evidence")
        if not e.get("source_ref"):
            raise SystemExit(f"contract_durations.json: {ref} names no document")


def load_curated() -> tuple[dict, dict]:
    themes = json.loads(THEMES_FILE.read_text(encoding="utf-8"))
    durations = json.loads(DURATIONS_FILE.read_text(encoding="utf-8"))
    _validate_themes(themes)
    _validate_durations(durations)
    return themes, durations


def write_db(conn: sqlite3.Connection, themes: dict, durations: dict) -> tuple[int, int]:
    _validate_themes(themes)
    _validate_durations(durations)
    known = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    unknown = sorted((set(_entries(themes)) | set(_entries(durations))) - known)
    if unknown:
        raise SystemExit(f"curated details refer to refs not in the DB: {unknown}")

    today = date.today().isoformat()
    conn.execute("DELETE FROM contract_work_themes")
    conn.execute("DELETE FROM contract_cpv_notes")
    conn.execute("DELETE FROM work_theme_labels")
    conn.executemany(
        "INSERT INTO work_theme_labels (theme, label_el, label_en) VALUES (?,?,?)",
        [(k, m["el"], m["en"]) for k, m in themes["_themes"].items()])
    rows_t = [(ref, i, t["key"], t["excerpt"], e.get("source", "pdf"), today)
              for ref, e in _entries(themes).items()
              for i, t in enumerate(e.get("themes", []))]
    conn.executemany(
        "INSERT INTO contract_work_themes (reference_number, seq, theme, "
        "excerpt, source, curated_at) VALUES (?,?,?,?,?,?)", rows_t)
    conn.executemany(
        "INSERT OR IGNORE INTO contract_cpv_notes (reference_number, cpv_code, theme)"
        " VALUES (?,?,?)",
        [(ref, c["cpv"], c["theme"]) for ref, e in _entries(themes).items()
         for c in e.get("cpv_notes", [])])

    conn.execute("DELETE FROM contract_durations")
    conn.executemany(
        "INSERT INTO contract_durations (reference_number, n, unit, days, basis,"
        " fire_season, anchor, excerpt, source_ref, registry_n, registry_unit,"
        " curated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(ref, e.get("n"), e.get("unit"), e.get("days"), e.get("basis"),
          e.get("fire_season"), e.get("anchor", ""), e.get("excerpt", ""),
          e["source_ref"], (e.get("registry") or {}).get("n"),
          (e.get("registry") or {}).get("unit"), today)
         for ref, e in _entries(durations).items()])
    conn.commit()

    has_scope = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_scope'"
    ).fetchone()
    if has_scope:
        for (ref,) in conn.execute(
                "SELECT reference_number FROM contract_scope WHERE in_scope = 1"):
            if ref not in _entries(durations):
                log.warning("%s: in scope but no curated duration", ref)
    return len(rows_t), len(_entries(durations))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    conn = db.init_db(args.db)
    themes, durations = load_curated()
    n_t, n_d = write_db(conn, themes, durations)
    n_c = conn.execute("SELECT COUNT(*) FROM contract_work_themes").fetchone()[0]
    multi = conn.execute(
        "SELECT COUNT(*) FROM (SELECT reference_number FROM contract_work_themes"
        " GROUP BY 1 HAVING COUNT(*) > 1)").fetchone()[0]
    notes = conn.execute("SELECT COUNT(DISTINCT reference_number) FROM"
                         " contract_cpv_notes").fetchone()[0]
    seasons = conn.execute("SELECT COUNT(*) FROM contract_durations"
                           " WHERE fire_season IS NOT NULL").fetchone()[0]
    log.info("work themes: %d links over %d contracts (%d with more than one); "
             "%d contracts carry a CPV note", n_c,
             conn.execute("SELECT COUNT(DISTINCT reference_number) FROM"
                          " contract_work_themes").fetchone()[0], multi, notes)
    log.info("durations: %d contracts (%d state a fire season instead)", n_d, seasons)
    conn.close()


if __name__ == "__main__":
    main()
