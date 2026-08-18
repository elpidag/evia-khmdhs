"""Derive each contract's procurement FAMILY from its own signed text.

The ΚΗΜΔΗΣ chain (`contract_linked_acts`) knows an upstream act for only
40 of the 245 in-scope Anti-nero contracts, because most were posted
without declaring one. The documents themselves are far more forthcoming:
200 quote their πρόσκληση by ΑΔΑΜ and 125 their κατακύρωση, giving 128
procurement families — 102 of whose προσκλήσεις the registry metadata
never mentions at all (DATA_DECISIONS 2026-08-18).

What this loader will NOT do: group by the lot labels in titles
(«ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 11Α»). 21 of 59 such labels repeat across
programme years, so grouping on them invents families no document
asserts. Only a cited ΑΔΑΜ — an actual document we hold — counts, and
every row stores the sentence that cites it.

Contracts citing nothing are left empty on purpose: they are direct
awards (άρθρο 118/328) or negotiations without publication, procedures
that publish no call. Amendments inherit their predecessor's family.

Usage:
  .venv/bin/python -m khmdhs.families_loader [--db …] [--cache …] [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import sys
import unicodedata
from datetime import date
from pathlib import Path

from khmdhs.config import DEFAULT_DB, PDF_CACHE_DIR
from khmdhs.db import init_db

# ΑΔΑΜ formats are strict, so these patterns cannot drift onto other text
PROC = re.compile(r"\b\d{2}PROC\d{9}\b")
AWRD = re.compile(r"\b\d{2}AWRD\d{9}\b")
WS = re.compile(r"\s+")
# «…όπως τροποποιήθηκε με την … Απόφαση Τροποποίησης της ως άνω Πρόσκλησης».
# Accents are stripped before the test: «Τροποποίησης» carries an accented
# ί, so a plain «τροποποι» pattern silently never matches (the same trap
# scope.py documents for Greek keyword matching).
AMEND = re.compile(r"τροποποι", re.I)


def _unaccent(s: str) -> str:
    nfd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfd if not unicodedata.combining(ch))
WINDOW = 240


def _excerpt(text: str, at: int, end: int) -> str:
    """The citing sentence, whitespace-collapsed — evidence for the row."""
    return WS.sub(" ", text[max(0, at - WINDOW):end + 60]).strip()


def citations(text: str) -> list[tuple[str, str, str, str]]:
    """(adam, kind, role, excerpt) for every act this contract cites.

    The first πρόσκληση is the procurement; a later one whose citing
    sentence says «τροποποι…» is that call's own amendment, not a rival
    family — the only ambiguity the corpus contains, and it resolves the
    same way in all four contracts that show it.
    """
    out: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for rx, kind in ((PROC, "notice"), (AWRD, "auction")):
        first = True
        for m in rx.finditer(text):
            adam = m.group(0)
            if adam in seen:
                continue
            seen.add(adam)
            ex = _excerpt(text, m.start(), m.end())
            if kind == "auction":
                role = "award"
            elif first:
                role = "procurement"
            else:
                role = "amendment" if AMEND.search(_unaccent(ex)) else "procurement"
            out.append((adam, kind, role, ex))
            first = False
    return out


def load(conn: sqlite3.Connection, cache: Path, dry_run: bool = False) -> dict:
    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts ORDER BY reference_number")]
    prev_of = {r[0]: r[1] for r in conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts")}
    texts: dict[str, str] = {}
    for ref in refs:
        p = cache / f"{ref}.txt"
        if p.exists():
            texts[ref] = p.read_text(encoding="utf-8", errors="replace")

    direct = {ref: citations(t) for ref, t in texts.items()}
    stats = {"contracts": len(refs), "no_text": len(refs) - len(texts),
             "direct": 0, "inherited": 0, "none": 0, "rows": 0}
    rows: list[tuple] = []
    today = date.today().isoformat()
    for ref in refs:
        cites = direct.get(ref) or []
        source = "text"
        if not any(k == "notice" for _, k, _, _ in cites):
            # an amendment stands in its predecessor's family (the same
            # convention regions, scope and categories already use)
            walked, cur = set(), prev_of.get(ref)
            while cur and cur not in walked:
                walked.add(cur)
                parent = [c for c in (direct.get(cur) or []) if c[1] == "notice"]
                if parent:
                    cites = cites + parent
                    source = f"inherited:{cur}"
                    stats["inherited"] += 1
                    break
                cur = prev_of.get(cur)
        if not cites:
            stats["none"] += 1
            continue
        if source == "text":
            stats["direct"] += 1
        for seq, (adam, kind, role, ex) in enumerate(cites):
            # a row is only ever written with the sentence that proves it
            assert ex, (ref, adam)
            rows.append((ref, seq, adam, kind, role,
                         source if kind == "notice" else "text", ex, today))
    stats["rows"] = len(rows)
    if dry_run:
        return stats
    with conn:
        conn.execute("DELETE FROM contract_families")
        conn.executemany(
            "INSERT INTO contract_families (reference_number, seq, adam, kind,"
            " role, source, excerpt, loaded_at) VALUES (?,?,?,?,?,?,?,?)", rows)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m khmdhs.families_loader")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:                      # pragma: no cover
        pass
    conn = init_db(args.db)
    s = load(conn, args.cache, args.dry_run)
    conn.close()
    print(f"families: {s['rows']} rows for {s['direct']} contracts citing their own "
          f"acts + {s['inherited']} inheriting from a predecessor; "
          f"{s['none']} without any (direct awards publish no call); "
          f"{s['no_text']} without cached text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
