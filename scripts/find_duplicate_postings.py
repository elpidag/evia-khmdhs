# -*- coding: utf-8 -*-
"""Find registry double-postings: the same signed document uploaded twice
under two ΑΔΑΜ (DATA_DECISIONS 2026-08-14 — 9 confirmed in the ΔΑΣΕ set;
plus a 10th on 2026-08-15 that hid behind a mis-keyed contractor ΑΦΜ).

Method: group LIVE contracts sharing (canonical contractor VAT, signed
date, stated net); within each group compare the cached PDF texts after
stripping the registry's own ΑΔΑΜ stamps — identical (or ≥97% similar)
normalized text marks a pair for human review. A second CROSS-VAT pass
groups by (date, amount) alone, so a twin whose contractor ΑΦΜ was
keyed wrong (the Κουρκουλών phantom «0310003799») cannot escape the
sweep; such pairs carry same_vat=False and need extra scrutiny —
sibling lots of one πρόσκληση can be legitimately near-identical.
Excluded duplicates (contracts.duplicate_of set) never re-trip.
Suspects are CANDIDATES: verify Αριθ. Πρωτ. / ΑΔΑ in the PDFs before
curating an exclusion into dase_contract_corrections.json.

Usage:
  .venv/bin/python scripts/find_duplicate_postings.py \
      [--db data/processed/dase.sqlite] [--cache data/processed/dase_pdf_cache]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from khmdhs.config import DASE_DB  # noqa: E402

ADAM_RE = re.compile(r"\d{2}\s*S\s*Y\s*M\s*V\s*[\d\s]{9,12}")


def normalized_text(cache: Path, ref: str) -> str | None:
    p = cache / f"{ref}.txt"
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-8", errors="replace")
    t = ADAM_RE.sub(" ", t)
    return re.sub(r"\s+", "", t)


def find_pairs(conn, cache: Path, sim_threshold: float = 0.97) -> list[dict]:
    """Suspect pairs among live, not-already-excluded contracts."""
    from webui.dase_queries import canonical_vat, live_filter
    rows = conn.execute(f"""
        SELECT co.reference_number ref, co.contract_signed_date dt,
               co.total_cost_without_vat n,
               (SELECT c.vat_number FROM contractors c
                WHERE c.reference_number = co.reference_number LIMIT 1) vat
        FROM contracts co
        WHERE {live_filter('co')} AND co.duplicate_of IS NULL
    """).fetchall()
    vat_of, groups, xgroups = {}, defaultdict(list), defaultdict(list)
    for r in rows:
        if not r["n"]:
            continue
        vat_of[r["ref"]] = canonical_vat(r["vat"] or "")
        groups[(vat_of[r["ref"]], r["dt"], round(r["n"], 2))].append(r["ref"])
        xgroups[(r["dt"], round(r["n"], 2))].append(r["ref"])

    out, seen = [], set()

    def compare(refs, dt, amt):
        texts = {ref: normalized_text(cache, ref) for ref in refs}
        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                a, b = sorted((refs[i], refs[j]))
                if (a, b) in seen:
                    continue
                ta, tb = texts[a], texts[b]
                if ta is None or tb is None:
                    continue
                if abs(len(ta) - len(tb)) > 400:
                    continue
                sim = SequenceMatcher(None, ta, tb).ratio()
                if sim >= sim_threshold:
                    seen.add((a, b))
                    out.append({"a": a, "b": b, "date": dt, "eur": amt,
                                "similarity": round(sim, 4),
                                "identical": ta == tb,
                                "same_vat": vat_of[a] == vat_of[b]})

    for (vat, dt, amt), refs in sorted(groups.items()):
        if len(refs) >= 2:
            compare(refs, dt, amt)
    # Cross-VAT pass: a mis-keyed contractor ΑΦΜ must not hide a twin
    # (the Κουρκουλών phantom-ΑΦΜ pair, DATA_DECISIONS 2026-08-15).
    for (dt, amt), refs in sorted(xgroups.items()):
        if len(refs) >= 2:
            compare(refs, dt, amt)
    return out


def main(argv: list[str] | None = None) -> int:
    import sqlite3
    parser = argparse.ArgumentParser(prog="find_duplicate_postings.py")
    parser.add_argument("--db", type=Path, default=DASE_DB)
    parser.add_argument("--cache", type=Path,
                        default=Path("data/processed/dase_pdf_cache"))
    args = parser.parse_args(argv)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    pairs = find_pairs(conn, args.cache)
    for p in pairs:
        tag = "IDENTICAL" if p["identical"] else f"sim={p['similarity']}"
        if not p["same_vat"]:
            tag += "  [CROSS-VAT — check for a mis-keyed ΑΦΜ]"
        print(f"{p['a']} ↔ {p['b']}  {p['date']}  {p['eur']:,.2f} €  {tag}")
    print(f"\n{len(pairs)} suspect pair(s)")
    conn.close()
    return 1 if pairs else 0


if __name__ == "__main__":
    raise SystemExit(main())
