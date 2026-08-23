"""Load the curated ΔΑΣΕ work-type categories, fire contexts and
document-stated deadlines into the ΔΑΣΕ DB (DATA_DECISIONS 2026-08-23).

Sources of truth:
  khmdhs/data/dase_categories.json
      {"_categories": {key: {label, label_en, note}},
       "_contexts":   {key: {label, label_en}},
       "_overrides":  {ADAM: {...}}            (merged by the extractor's --curate)
       ADAM: {"category", "title" (the verbatim evidence), "source"
              (pdf:heading | pdf:quoted | pdf:work | eye | inherited:<ref> |
               pdf:review), "context", "context_excerpt", "review", "note"}}
  khmdhs/data/dase_durations.json
      {ADAM: {"kind": date | duration | open_ended, "deadline_date", "n",
              "unit", "days", "basis", "anchor", "excerpt", "source_ref",
              "flags", "registry", "note"}}

Tables: contract_categories + category_labels (the Anti-nero shape),
contract_fire_context + fire_context_labels, contract_durations (with
deadline_date / kind). Validates every entry and refuses to load on
failure; WARNs on a live contract with no category. Hooked at the end of
`scripts/harvest_dase.py load` and runnable on its own:

    .venv/bin/python -m khmdhs.dase_details_loader [--db path]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path

from khmdhs import db
from khmdhs.config import DASE_DB

CAT_FILE = Path(__file__).parent / "data" / "dase_categories.json"
DUR_FILE = Path(__file__).parent / "data" / "dase_durations.json"

log = logging.getLogger(__name__)


def _entries(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _validate(cats: dict, durs: dict) -> None:
    keys = cats.get("_categories") or {}
    ctxs = cats.get("_contexts") or {}
    if not keys or not ctxs:
        raise SystemExit("dase_categories.json: _categories / _contexts missing")
    for k, m in {**keys}.items():
        if not m.get("label") or not m.get("label_en"):
            raise SystemExit(f"dase_categories.json: {k} lacks label/label_en")
    for ref, e in _entries(cats).items():
        if e.get("category") not in keys:
            raise SystemExit(f"dase_categories.json: {ref} has unknown category {e.get('category')!r}")
        if not e.get("title"):
            raise SystemExit(f"dase_categories.json: {ref} has no evidence title")
        if not e.get("source"):
            raise SystemExit(f"dase_categories.json: {ref} has no source")
        if e.get("context") and e["context"] not in ctxs:
            raise SystemExit(f"dase_categories.json: {ref} has unknown context {e['context']!r}")
    for ref, e in _entries(durs).items():
        if e.get("kind") not in ("date", "duration", "open_ended"):
            raise SystemExit(f"dase_durations.json: {ref} has unknown kind {e.get('kind')!r}")
        if e["kind"] == "date" and not e.get("deadline_date"):
            raise SystemExit(f"dase_durations.json: {ref} is a date with no deadline_date")
        if e["kind"] == "duration" and not (e.get("n") and e.get("unit")):
            raise SystemExit(f"dase_durations.json: {ref} is a duration with no n/unit")
        if not e.get("excerpt"):
            raise SystemExit(f"dase_durations.json: {ref} has no excerpt")


def load_curated() -> tuple[dict, dict]:
    cats = json.loads(CAT_FILE.read_text(encoding="utf-8"))
    durs = json.loads(DUR_FILE.read_text(encoding="utf-8")) if DUR_FILE.exists() else {}
    _validate(cats, durs)
    return cats, durs


def write_db(conn: sqlite3.Connection, cats: dict, durs: dict) -> tuple[int, int, int]:
    known = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    unknown = sorted((set(_entries(cats)) | set(_entries(durs))) - known)
    if unknown:
        raise SystemExit(f"curated ΔΑΣΕ details refer to refs not in the DB: {unknown[:10]}")
    today = date.today().isoformat()

    conn.execute("DELETE FROM category_labels")
    conn.executemany(
        "INSERT INTO category_labels (category, label, note, label_en) VALUES (?,?,?,?)",
        [(k, m["label"], m.get("note"), m["label_en"]) for k, m in cats["_categories"].items()])
    conn.execute("DELETE FROM fire_context_labels")
    conn.executemany(
        "INSERT INTO fire_context_labels (context, label, label_en) VALUES (?,?,?)",
        [(k, m["label"], m["label_en"]) for k, m in cats["_contexts"].items()])

    conn.execute("DELETE FROM contract_categories")
    conn.executemany(
        "INSERT INTO contract_categories (reference_number, category, title, source, curated_at)"
        " VALUES (?,?,?,?,?)",
        [(ref, e["category"], e["title"], e["source"], today) for ref, e in _entries(cats).items()])
    conn.execute("DELETE FROM contract_fire_context")
    rows_ctx = [(ref, e["context"], e.get("context_excerpt"), e["source"], today)
                for ref, e in _entries(cats).items() if e.get("context")]
    conn.executemany(
        "INSERT INTO contract_fire_context (reference_number, context, excerpt, source, curated_at)"
        " VALUES (?,?,?,?,?)", rows_ctx)

    conn.execute("DELETE FROM contract_durations")
    conn.executemany(
        "INSERT INTO contract_durations (reference_number, n, unit, days, basis, fire_season,"
        " anchor, excerpt, source_ref, registry_n, registry_unit, curated_at, deadline_date,"
        " kind, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(ref, e.get("n"), e.get("unit"), e.get("days"), e.get("basis"), None,
          e.get("anchor") or "", e["excerpt"], e.get("source_ref") or ref,
          (e.get("registry") or {}).get("duration"), (e.get("registry") or {}).get("unit"),
          today, e.get("deadline_date"), e["kind"], e.get("note"))
         for ref, e in _entries(durs).items()])
    conn.commit()

    live = {r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts c WHERE cancelled = 0 AND NOT EXISTS"
        " (SELECT 1 FROM contracts n WHERE n.reference_number = c.next_reference_no)")}
    for ref in sorted(live - set(_entries(cats))):
        log.warning("%s: live ΔΑΣΕ contract with no curated category", ref)
    log.info("categories: %s", dict(Counter(e["category"] for e in _entries(cats).values())))
    log.info("contexts: %s", dict(Counter(e["context"] for e in _entries(cats).values() if e.get("context"))))
    log.info("deadlines: %s", dict(Counter(e["kind"] for e in _entries(durs).values())))
    return len(_entries(cats)), len(rows_ctx), len(_entries(durs))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DASE_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cats, durs = load_curated()
    conn = db.init_db(args.db)
    n_c, n_x, n_d = write_db(conn, cats, durs)
    log.info("loaded %d categories, %d fire contexts, %d deadlines into %s", n_c, n_x, n_d, args.db)


if __name__ == "__main__":
    main()
