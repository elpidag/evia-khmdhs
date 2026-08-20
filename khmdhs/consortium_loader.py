"""Load the curated joint-venture membership into the DB.

Source of truth: `khmdhs/data/consortium_members.json` (DATA_DECISIONS
2026-08-20). 54 in-scope contractors are joint ventures holding 67 contracts
— €189,4M, 30,4% of the programme — and each signs as ONE entity with its own
ΑΦΜ, so the firms behind them are invisible in every per-contractor view.
This layer records who they are made of; the venture itself stays the
CONTRACTOR of its contracts, because that is what signed them.

Every entry was confirmed by the user, most of them one at a time, and each
member carries the document it was read from and the verbatim sentence. 22
ventures are recorded with NO members and `members_documented = 0`: the firms
in their titles are identifiable, but no document states them to be members,
and a venture's name is not evidence of its membership.

Validation refuses to load on anything that would corrupt the second view:

* a member ΑΦΜ that is not nine digits, or equals its own venture;
* a member that is itself a curated venture (a κοινοπραξία is not a member of
  a κοινοπραξία — the machine proposed exactly that for ΛΙΑΧΤΙΔΑ and ΜΠΟΜΠΟΤΗ
  before review);
* a venture that is not an in-scope contractor;
* a venture with `members_documented = 1` and no members, or the reverse.

Usage:  .venv/bin/python -m khmdhs.consortium_loader [--db path]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
from pathlib import Path

from khmdhs import db
from khmdhs.config import DEFAULT_DB

CURATED = Path(__file__).parent / "data" / "consortium_members.json"

log = logging.getLogger(__name__)


def _entries(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def validate(data: dict, conn: sqlite3.Connection) -> None:
    entries = _entries(data)
    ventures = set(entries)
    contractors = {r[0] for r in conn.execute(
        "SELECT DISTINCT co.vat_number FROM contractors co "
        "JOIN contract_scope s USING (reference_number) WHERE s.in_scope = 1")}
    for vat, e in entries.items():
        if not re.fullmatch(r"\d{9}", vat):
            raise SystemExit(f"consortium_members.json: {vat!r} is not an ΑΦΜ")
        if vat not in contractors:
            raise SystemExit(f"consortium_members.json: {vat} holds no in-scope "
                             f"contract — it cannot be a venture of this dataset")
        members = e.get("members") or []
        documented = e.get("members_documented", True)
        if documented and not members:
            raise SystemExit(f"consortium_members.json: {vat} claims documented "
                             f"members but lists none")
        if members and not documented:
            raise SystemExit(f"consortium_members.json: {vat} lists members but "
                             f"is flagged undocumented")
        seen: set[str] = set()
        for m in members:
            mv = str(m.get("vat", "")).strip()
            if not re.fullmatch(r"\d{9}", mv):
                raise SystemExit(f"consortium_members.json: {vat} has member "
                                 f"{mv!r}, which is not an ΑΦΜ")
            if mv == vat:
                raise SystemExit(f"consortium_members.json: {vat} lists itself")
            if mv in ventures:
                raise SystemExit(f"consortium_members.json: {vat} lists {mv}, "
                                 f"which is itself a joint venture")
            if mv in seen:
                raise SystemExit(f"consortium_members.json: {vat} lists {mv} twice")
            seen.add(mv)
        if len(members) == 1:
            log.warning("%s has a single member — a venture of one is a "
                        "contradiction, check the curation", vat)


def load(db_path: Path = DEFAULT_DB, path: Path = CURATED) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    conn = db.init_db(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    validate(data, conn)
    entries = _entries(data)
    with conn:
        conn.execute("DELETE FROM consortium_members")
        conn.execute("DELETE FROM consortiums")
        for vat, e in entries.items():
            members = e.get("members") or []
            conn.execute(
                "INSERT INTO consortiums (vat_number, name, legal_type, gemi, "
                "basis, members_documented, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (vat, e.get("name") or vat, e.get("legal_type"), e.get("gemi"),
                 e.get("basis"), 0 if e.get("members_documented") is False else 1,
                 e.get("note")))
            for i, m in enumerate(members):
                conn.execute(
                    "INSERT INTO consortium_members (venture_vat, seq, "
                    "member_vat, member_name, source, excerpt) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (vat, i, str(m["vat"]).strip(), m.get("name"),
                     m.get("source"), m.get("excerpt")))
    n_links = sum(len(e.get("members") or []) for e in entries.values())
    n_doc = sum(1 for e in entries.values() if e.get("members"))
    firms = {m["vat"] for e in entries.values() for m in (e.get("members") or [])}
    # a joint venture the programme holds but nobody has curated is invisible
    # to the member view — warn, never fail
    known = {r[0] for r in conn.execute("SELECT vat_number FROM consortiums")}
    for r in conn.execute(
            "SELECT DISTINCT co.vat_number, MIN(co.name) FROM contractors co "
            "JOIN contract_scope s USING (reference_number) "
            "LEFT JOIN contractor_locations l ON l.vat_number = co.vat_number "
            "WHERE s.in_scope = 1 AND l.gemi_legal_type = 'Κοινοπραξία' "
            "GROUP BY co.vat_number"):
        if r[0] not in known:
            log.warning("joint venture %s (%s) is not curated", r[0], r[1])
    conn.close()
    log.info("Loaded %d joint ventures (%d with members, %d undocumented), "
             "%d member links over %d distinct firms",
             len(entries), n_doc, len(entries) - n_doc, n_links, len(firms))
    return {"ventures": len(entries), "with_members": n_doc,
            "links": n_links, "firms": len(firms)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m khmdhs.consortium_loader")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--curated", type=Path, default=CURATED)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, args.curated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
