# -*- coding: utf-8 -*-
"""Load the curated public-bodies registry (DATA_DECISIONS 2026-08-16).

khmdhs/data/public_bodies.json → tables `public_bodies` (key, canonical
name, kind, scope, ΑΦΜ, municipality link, note) and `public_body_aliases`
(verbatim registry spelling → body key). One registry file, loaded into
BOTH contract DBs (khmdhs + dase); hooked at the end of harvest_dase.py
load and in the khmdhs.refresh chain.

Validation is strict and refuses to load:
  - kind/scope outside the closed vocabularies (incl. any 'review' left);
  - municipal-scope bodies without a municipality_code, or codes unknown
    to greek_municipalities.json;
  - ΑΦΜ that is not exactly 9 digits;
  - an alias claimed by two bodies.

After loading it WARNs (never fails) about organization strings present
in the target DB but absent from the registry — new awarding bodies
surface here first and go through the curator, never auto-classified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
BODIES_FILE = DATA_DIR / "public_bodies.json"
MUNI_FILE = DATA_DIR / "greek_municipalities.json"
DEFAULT_DB = Path(__file__).resolve().parents[1] / "data/processed/khmdhs.sqlite"

KINDS = {
    "ministry", "decentralized_administration", "region", "municipality",
    "municipal_entity", "state_vehicle", "other_public",
}
SCOPES = {"municipal", "regional", "national", "seat"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS public_bodies (
    key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    scope TEXT NOT NULL,
    afm TEXT,
    municipality_code TEXT,
    note TEXT
);
CREATE TABLE IF NOT EXISTS public_body_aliases (
    alias TEXT PRIMARY KEY,
    body_key TEXT NOT NULL REFERENCES public_bodies(key)
);
"""


def load_bodies(conn: sqlite3.Connection, path: Path = BODIES_FILE) -> int:
    doc = json.loads(path.read_text(encoding="utf-8"))
    munis = json.loads(MUNI_FILE.read_text(encoding="utf-8"))
    bodies = doc["bodies"]

    seen_alias: dict[str, str] = {}
    for b in bodies:
        key = b["key"]
        if b["kind"] not in KINDS:
            raise ValueError(f"{key}: kind '{b['kind']}' outside the closed vocabulary")
        if b["scope"] not in SCOPES:
            raise ValueError(f"{key}: scope '{b['scope']}' outside the closed vocabulary")
        if b["scope"] == "municipal":
            code = b.get("municipality_code")
            if not code:
                raise ValueError(f"{key}: municipal scope without municipality_code")
            if code not in munis:
                raise ValueError(f"{key}: municipality_code {code} unknown to greek_municipalities")
        afm = b.get("afm")
        if afm is not None and not (len(afm) == 9 and afm.isdigit()):
            raise ValueError(f"{key}: ΑΦΜ '{afm}' is not 9 digits")
        for alias in b["aliases"]:
            if alias in seen_alias and seen_alias[alias] != key:
                raise ValueError(f"alias '{alias}' claimed by both {seen_alias[alias]} and {key}")
            seen_alias[alias] = key

    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM public_body_aliases")
    conn.execute("DELETE FROM public_bodies")
    for b in bodies:
        conn.execute(
            "INSERT INTO public_bodies(key, name, kind, scope, afm, municipality_code, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (b["key"], b["name"], b["kind"], b["scope"], b.get("afm"),
             b.get("municipality_code"), b.get("note")))
        for alias in b["aliases"]:
            conn.execute(
                "INSERT INTO public_body_aliases(alias, body_key) VALUES (?, ?)",
                (alias, b["key"]))
    conn.commit()

    # coverage warning: org strings in this DB the registry does not know
    try:
        uncovered = [r[0] for r in conn.execute(
            """SELECT DISTINCT organization_name FROM contracts
               WHERE organization_name IS NOT NULL
                 AND organization_name NOT IN (SELECT alias FROM public_body_aliases)""")]
    except sqlite3.OperationalError:
        uncovered = []
    for name in uncovered:
        print(f"WARN: awarding body not in the public-bodies registry: {name!r}")

    return len(bodies)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--bodies", default=str(BODIES_FILE))
    args = ap.parse_args(argv)
    conn = sqlite3.connect(args.db)
    n = load_bodies(conn, Path(args.bodies))
    n_alias = conn.execute("SELECT COUNT(*) FROM public_body_aliases").fetchone()[0]
    print(f"loaded {n} public bodies ({n_alias} aliases) into {args.db}")
    conn.close()


if __name__ == "__main__":
    main()
