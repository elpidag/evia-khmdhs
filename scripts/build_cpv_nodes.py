# -*- coding: utf-8 -*-
"""Build khmdhs/data/cpv_nodes.json — the official EU CPV 2008 names (EN +
EL) for exactly the nodes the in-scope Anti-nero contracts AND the live
ΔΑΣΕ contracts touch, at every level of the vocabulary's tree
(DATA_DECISIONS 2026-08-23; ΔΑΣΕ codes added 2026-08-24 for the /dase
CPV CODES frame).

Source: the TED/SIMAP workbook «cpv_2008_ver_2013.xlsx» (sheet «CPV codes»,
one row per code with its name in every EU language), downloaded from
https://ted.europa.eu/documents/d/ted/cpv_2008_xls and kept in data/raw/.

The CPV (Regulation (EC) 2195/2002 as amended by 213/2008) is a tree: the
first two digits are the DIVISION, three the GROUP, four the CLASS, five
the CATEGORY, the 8-digit code the leaf. A prefix's own code is the prefix
padded with zeros (77 → 77000000, 772 → 77200000, …), so every ancestor of
a declared code is itself a CPV code with an official name — which is what
lets the front page roll the 145 declared codes up into 13 divisions.

Usage: python scripts/build_cpv_nodes.py [--xlsx PATH] [--db PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "raw" / "cpv_2008_ver_2013.xlsx"
DB = ROOT / "data" / "processed" / "khmdhs.sqlite"
DASE_DB = ROOT / "data" / "processed" / "dase.sqlite"
OUT = ROOT / "khmdhs" / "data" / "cpv_nodes.json"
SOURCE_URL = "https://ted.europa.eu/documents/d/ted/cpv_2008_xls"

LEVELS = {2: "division", 3: "group", 4: "class", 5: "category", 8: "code"}


def prefix_code(code8: str, n: int) -> str:
    """the CPV code of a code's n-digit prefix: the prefix padded with zeros"""
    return code8[:n].ljust(8, "0")


CHAIN = (2, 3, 4, 5, 8)


def true_level(code8: str) -> int:
    """a code's own level: a code that IS a padded prefix (77200000) is a
    group, not a leaf — declared codes sit at every level of the tree"""
    for n in (2, 3, 4, 5):
        if prefix_code(code8, n) == code8:
            return n
    return 8


def parent_of(code8: str) -> str | None:
    lvl = true_level(code8)
    i = CHAIN.index(lvl)
    return prefix_code(code8, CHAIN[i - 1]) if i > 0 else None


def load_vocab(path: Path) -> dict[str, dict[str, str]]:
    import openpyxl  # local import: the script is a one-off builder

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["CPV codes"]
    rows = ws.iter_rows(values_only=True)
    hdr = [str(h).strip() for h in next(rows)]
    i_code, i_en, i_el = hdr.index("CODE"), hdr.index("EN"), hdr.index("EL")
    vocab: dict[str, dict[str, str]] = {}
    for r in rows:
        code = (r[i_code] or "").strip()
        if not code:
            continue
        vocab[code.split("-")[0]] = {"code": code, "en": (r[i_en] or "").strip(),
                                     "el": (r[i_el] or "").strip()}
    return vocab


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", type=Path, default=XLSX)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--dase-db", type=Path, default=DASE_DB)
    args = ap.parse_args()

    vocab = load_vocab(args.xlsx)
    kh = sqlite3.connect(args.db)
    declared = [r[0] for r in kh.execute(
        """SELECT DISTINCT c.cpv_code FROM contract_cpvs c
           JOIN contract_scope s ON s.reference_number = c.reference_number
                                AND s.in_scope = 1""")]
    # the ΔΑΣΕ dataset's live population (cancelled=0, not superseded
    # in-DB — dase_queries.live_filter's condition, restated here so the
    # one-off builder needs no webui import)
    if args.dase_db.exists():
        dase = sqlite3.connect(args.dase_db)
        declared += [r[0] for r in dase.execute(
            """SELECT DISTINCT c.cpv_code FROM contract_cpvs c
               JOIN contracts co ON co.reference_number = c.reference_number
               WHERE co.cancelled = 0 AND NOT EXISTS (
                     SELECT 1 FROM contracts nx
                     WHERE nx.reference_number = co.next_reference_no)""")]
        dase.close()
    nodes: dict[str, dict] = {}
    missing: list[str] = []
    for raw in declared:
        code8 = raw.split("-")[0]
        # the code itself and every ancestor up to its division, each at its
        # TRUE level (a declared 77200000 is the group, not a leaf under it)
        keys = {code8} | {prefix_code(code8, n) for n in (2, 3, 4, 5) if n < true_level(code8)}
        for key in keys:
            v = vocab.get(key)
            if v is None:
                missing.append(key)
                continue
            nodes[key] = {"code": v["code"], "level": LEVELS[true_level(key)],
                          "name_en": v["en"], "name_el": v["el"],
                          "parent": parent_of(key)}
    out = {
        "_doc": ("Official EU CPV 2008 names, EN + EL, for every node the in-scope "
                 "Anti-nero contracts and the live ΔΑΣΕ contracts touch (leaf "
                 "codes and their division/group/class/category ancestors). Built "
                 "by scripts/build_cpv_nodes.py from the TED workbook in data/raw/ "
                 "— names are the vocabulary's, never typed."),
        "_source": {"url": SOURCE_URL, "file": args.xlsx.name, "built": date.today().isoformat()},
        "_missing": sorted(set(missing)),
        "nodes": dict(sorted(nodes.items())),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    by_level = {}
    for v in nodes.values():
        by_level[v["level"]] = by_level.get(v["level"], 0) + 1
    print(f"{len(declared)} declared codes -> {len(nodes)} nodes {by_level}; "
          f"missing {len(set(missing))} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
