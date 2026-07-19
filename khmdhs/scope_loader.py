"""Build the contract_scope table: Anti-nero relevance for every contract.

For each row in `contracts`, khmdhs.scope.classify() decides a scope
(antinero_i…antinero_2026, umbrella, support, non_antinero). Curated
phases from khmdhs/data/antinero_supplement.json override the rules.

On top of the scope, a supersede pass walks prevReferenceNo links: when a
contract has a later (non-cancelled) version in the DB, the older version
is taken out of scope so modification chains count once, not twice.

The web UI aggregates only rows with in_scope = 1; detail pages remain
reachable for everything.

Usage:
  .venv/bin/python -m khmdhs.scope_loader [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db
from khmdhs.scope import IN_SCOPE, _strip_accents, classify

SUPPLEMENT_FILE = Path(__file__).parent / "data" / "antinero_supplement.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contract_scope (
    reference_number TEXT PRIMARY KEY,
    scope            TEXT NOT NULL,
    in_scope         INTEGER NOT NULL,
    superseded_by    TEXT,
    basis            TEXT,
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_scope_in_scope ON contract_scope(in_scope);
"""


def load_overrides(path: Path = SUPPLEMENT_FILE) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_comment", None)
    return {adam: meta["phase"] for adam, meta in data.items()}


def build_scopes(conn, overrides: dict[str, str]) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """Classify all contracts; return ({ref: (scope, basis)}, {ref: superseded_by})."""
    rows = conn.execute("""
        SELECT k.reference_number, k.title, k.public_funding_ref,
               k.public_funding_ref_num, k.prev_reference_no, k.cancelled,
               k.total_cost_with_vat,
               GROUP_CONCAT(c.vat_number) AS vats
        FROM contracts k
        LEFT JOIN contractors c USING (reference_number)
        GROUP BY k.reference_number
    """).fetchall()

    scopes: dict[str, tuple[str, str]] = {}
    prev_of: dict[str, str] = {}   # older-ref -> newest successor ref
    prev_map: dict[str, str] = {}  # ref -> its predecessor ref
    cancelled: set[str] = set()
    titles: dict[str, str] = {}
    values: dict[str, float] = {}
    for r in rows:
        ref = r["reference_number"]
        titles[ref] = r["title"] or ""
        values[ref] = r["total_cost_with_vat"] or 0.0
        result = classify(
            {
                "reference_number": ref,
                "title": r["title"],
                "public_funding_ref": r["public_funding_ref"],
                "public_funding_ref_num": r["public_funding_ref_num"],
                "contractor_vats": (r["vats"] or "").split(","),
            },
            overrides,
        )
        scopes[ref] = (result.scope, result.basis)
        if r["cancelled"]:
            cancelled.add(ref)
        prev = (r["prev_reference_no"] or "").strip()
        if prev:
            prev_of[prev] = ref
            prev_map[ref] = prev

    # Amendments often carry weaker evidence than the version they modify —
    # either none at all (titles like «1η ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΜΒΑΣΗΣ …») or just
    # the fund code without a phase. Inherit the predecessor's (better)
    # scope, iterating so amendment-of-amendment chains resolve too.
    changed = True
    while changed:
        changed = False
        for ref, prev in prev_map.items():
            scope, basis = scopes[ref]
            weak = basis == "no_antinero_evidence" or scope == "antinero_unknown_phase"
            if not weak or prev not in scopes:
                continue
            prev_scope, _ = scopes[prev]
            inheritable = prev_scope in IN_SCOPE and prev_scope != "antinero_unknown_phase"
            if inheritable and prev_scope != scope:
                scopes[ref] = (prev_scope, f"inherited_from_prev:{prev}")
                changed = True

    # A contract is superseded when a non-cancelled successor exists in the
    # DB — unless the successor is a supplementary contract (ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ
    # ΣΥΜΒΑΣΗ) adding new money on top of the original, in which case both
    # versions stay countable. A «συμπληρωματική» that restates roughly the
    # parent's full value (ΑΠΕ recapitulations) still supersedes it.
    superseded: dict[str, str] = {}
    for old_ref, new_ref in prev_of.items():
        if old_ref not in scopes or new_ref in cancelled:
            continue
        succ_title = _strip_accents(titles.get(new_ref, "").upper())
        additive = ("ΣΥΜΠΛΗΡΩΜΑΤΙΚ" in succ_title
                    and values.get(new_ref, 0) < 0.9 * values.get(old_ref, 0))
        if not additive:
            superseded[old_ref] = new_ref
    return scopes, superseded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.scope_loader")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--supplement", type=Path, default=SUPPLEMENT_FILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    overrides = load_overrides(args.supplement)
    conn = init_db(args.db)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    scopes, superseded = build_scopes(conn, overrides)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts: dict[str, int] = {}
    n_super = 0
    with conn:
        if not args.dry_run:
            conn.execute("DELETE FROM contract_scope")
        for ref, (scope, basis) in scopes.items():
            counts[scope] = counts.get(scope, 0) + 1
            sup = superseded.get(ref)
            in_scope = 1 if (scope in IN_SCOPE and sup is None) else 0
            if sup is not None and scope in IN_SCOPE:
                n_super += 1
                basis = f"{basis}; superseded_by:{sup}"
            if not args.dry_run:
                conn.execute(
                    """INSERT INTO contract_scope
                       (reference_number, scope, in_scope, superseded_by, basis, curated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ref, scope, in_scope, sup, basis, now),
                )

    in_scope_n, in_scope_eur = conn.execute("""
        SELECT COUNT(*), ROUND(SUM(k.total_cost_with_vat) / 1e6, 2)
        FROM contracts k JOIN contract_scope s USING (reference_number)
        WHERE s.in_scope = 1
    """).fetchone() if not args.dry_run else (None, None)

    print()
    print("=" * 60)
    print(f"Scope loader — {len(scopes)} contracts classified{' (dry-run)' if args.dry_run else ''}")
    for scope in sorted(counts, key=counts.get, reverse=True):
        print(f"  {scope:24s} {counts[scope]:4d}")
    print(f"  superseded by later version: {n_super}")
    if in_scope_n is not None:
        print(f"  IN SCOPE for analytics: {in_scope_n} contracts, €{in_scope_eur} M")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
