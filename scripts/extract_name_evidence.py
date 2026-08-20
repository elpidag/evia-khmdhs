"""How the SIGNED DOCUMENTS write each contractor's name.

The display-name layer proposes one canonical name per ΑΦΜ, and the two
registers disagree about many of them — but neither is what a reader sees on
the contract. The documents are: they name the party in the preamble, in the
case the sentence needs («τον ΞΑΝΘΟΠΟΥΛΟ ΒΑΣΙΛΕΙΟ του ΙΩΣΗΦ»), and a
patronymic they print in the genitive is a spelling a human typed — worth more
than one this pipeline declines by rule.

One pass over every cached text (contracts, awards, προσκλήσεις, payment
orders): find every nine-digit run, and where it is an ΑΦΜ we care about, keep
the words around it. Digit runs split by pdftotext («09027 3987») are joined
before matching, and excerpts are cut from the ORIGINAL text, so phase-II
accent mangling stays visible instead of being tidied away.

    .venv/Scripts/python scripts/extract_name_evidence.py [--vats a,b,c]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from khmdhs.config import DEFAULT_DB

CACHES = (ROOT / "data" / "processed" / "pdf_cache",)
OUT = ROOT / "data" / "processed" / "name_evidence.json"

NINE = re.compile(r"(?<!\d)(?:\d[ ]?){9}(?!\d)")
# «23PROC012517133» ends in nine digits that belong to no one
ADAM_TAIL = re.compile(r"(SYMV|PROC|AWRD|PAY|REQ|NOTICE|DIAB)[ ]?$", re.I)
BEFORE, AFTER = 230, 30


def all_vats(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    vats = {(r[0] or "").strip() for r in conn.execute(
        "SELECT DISTINCT vat_number FROM contractors")}
    vats |= {(r[0] or "").strip() for r in conn.execute(
        "SELECT DISTINCT member_vat FROM consortium_members")}
    conn.close()
    return {v for v in vats if re.fullmatch(r"\d{9}", v)}


def sweep(vats: set[str]) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {v: [] for v in vats}
    for cache in CACHES:
        for f in sorted(cache.glob("*.txt")):
            raw = " ".join(f.read_text(encoding="utf-8", errors="replace").split())
            for m in NINE.finditer(raw):
                vat = m.group(0).replace(" ", "")
                if vat not in found or ADAM_TAIL.search(raw[max(0, m.start() - 8):m.start()]):
                    continue
                found[vat].append({
                    "source": f.stem,
                    "excerpt": raw[max(0, m.start() - BEFORE):m.end() + AFTER],
                })
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--vats", help="comma-separated ΑΦΜ; default: all contractors")
    args = ap.parse_args(argv)

    vats = ({v.strip() for v in args.vats.split(",")} if args.vats
            else all_vats(args.db))
    found = sweep(vats)
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    named = sum(1 for v in found.values() if v)
    print(f"{len(vats)} ΑΦΜ · {named} appear in a cached document · "
          f"{sum(len(v) for v in found.values())} mentions")
    print(f"written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
