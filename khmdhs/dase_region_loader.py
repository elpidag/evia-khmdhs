"""Derive a Π.Ε. for every ΔΑΣΕ contract from its awarding unit.

`units_operator_name` (the awarding Δασαρχείο / Δ/νση Δασών / municipal
unit) is 100% filled and has only ~100 distinct values, so it is the
region signal for the standalone ΔΑΣΕ dataset (DATA_DECISIONS
2026-07-27). Resolution order per contract:

1. registry — fold + strip the ΔΑΣΑΡΧΕΙΟ/Δ(/)ΝΣΗ ΔΑΣΩΝ trigger prefix,
   then EXACT alias lookup in the curated forest_authorities.json
   (structured field → no windowed matching needed);
2. curated — khmdhs/data/dase_units.json, keyed org→unit (generic unit
   names like «ΓΡΑΦΕΙΟ ΔΗΜΑΡΧΟΥ» recur across municipalities). The one
   registry gap, ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ, lives here too — deliberately NOT in
   forest_authorities.json, which feeds the Anti-nero matcher;
3. otherwise the contract gets NO row — honestly unresolved, listed as
   a curation TODO.

Every emitted region is validated against the Π.Ε. vocabulary and
cross-checked against the row's own nuts_code (warning only — several
NUTS-3 codes span two Π.Ε., the header code is often coarse).

Results land in `dase_contract_regions` inside dase.sqlite. Rerunnable;
nothing here touches khmdhs.sqlite.

Usage:
  .venv/bin/python -m khmdhs.dase_region_loader [--db PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

from khmdhs.config import DASE_DB
from khmdhs.forest_loader import fold, load_registry
from khmdhs.greek_regions import REGIONAL_UNITS, canonical_pe

UNITS_FILE = Path(__file__).parent / "data" / "dase_units.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dase_contract_regions (
    reference_number TEXT PRIMARY KEY
        REFERENCES contracts(reference_number) ON DELETE CASCADE,
    region_pe  TEXT NOT NULL,
    source     TEXT NOT NULL,   -- 'registry:<authority>' | 'curated' | 'override'
    basis      TEXT,
    curated_at TEXT NOT NULL
);
"""

# Trigger prefixes on the FOLDED unit string (fold maps Greek→Latin
# homoglyphs, so the literals must be folded too). Longest first.
_DX_TRIGGERS = [fold(t) for t in
                ("ΔΑΣΑΡΧΕΙΟΥ", "ΔΑΣΑΡΧΕΙΟΝ", "ΔΑΣΑΡΧΕΙΟ")]
_DD_TRIGGERS = [fold(t) for t in
                ("ΔΙΕΥΘΥΝΣΗΣ ΔΑΣΩΝ", "ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ",
                 "Δ/ΝΣΗΣ ΔΑΣΩΝ", "Δ/ΝΣΗ ΔΑΣΩΝ", "ΔΝΣΗ ΔΑΣΩΝ")]

_WS = re.compile(r"\s+")


def _norm(s: str | None) -> str:
    """Collapse whitespace (curation-file keys and DB values must meet)."""
    return _WS.sub(" ", (s or "").strip())


def split_unit(unit: str) -> tuple[str | None, str]:
    """Fold a unit name and strip its authority-kind trigger prefix.

    Returns (kind, tail): kind 'dx' | 'dd' | None when no trigger leads.
    """
    f = _norm(fold(unit))
    for kind, triggers in (("dx", _DX_TRIGGERS), ("dd", _DD_TRIGGERS)):
        for t in triggers:
            if f == t:
                return kind, ""
            if f.startswith(t + " "):
                return kind, f[len(t) + 1:].strip()
    return None, f


def build_alias_map(registry: dict) -> dict[tuple[str, str], tuple[str, str]]:
    """(kind, folded alias) -> (authority name, region_pe)."""
    out: dict[tuple[str, str], tuple[str, str]] = {}
    for name, a in registry["authorities"].items():
        for alias in a["aliases"]:
            out[(a["kind"], _norm(fold(alias)))] = (name, a["region_pe"])
    return out


def load_units_file() -> tuple[dict, dict]:
    """Curated units file → (units, contract_overrides), validated.

    Shape: {"units": {org: {unit: {region_pe, note}}},
            "contract_overrides": {ref: {region_pe, note}}} — overrides are
    for supra-regional units (ΟΣΕ, ΕΠΙΘΕΩΡΗΣΗ Μ-Θ, …) where only the
    individual contract pins a Π.Ε.
    """
    if not UNITS_FILE.exists():
        return {}, {}
    data = json.loads(UNITS_FILE.read_text(encoding="utf-8"))
    units = data.get("units", {})
    overrides = data.get("contract_overrides", {})
    errors = []
    for org, by_unit in units.items():
        for unit, entry in by_unit.items():
            pe = entry.get("region_pe")
            if canonical_pe(pe) not in REGIONAL_UNITS:
                errors.append(f"{org!r} / {unit!r}: unknown region_pe {pe!r}")
    for ref, entry in overrides.items():
        pe = entry.get("region_pe")
        if canonical_pe(pe) not in REGIONAL_UNITS:
            errors.append(f"override {ref}: unknown region_pe {pe!r}")
        if not entry.get("note"):
            errors.append(f"override {ref}: evidence note required")
    if errors:
        raise SystemExit("dase_units.json: " + "; ".join(errors))
    return units, overrides


def resolve(unit: str, org: str, alias_map: dict, curated: dict
            ) -> tuple[str, str, str] | None:
    """Return (region_pe, source, basis) or None (honestly unresolved)."""
    kind, tail = split_unit(unit)
    kinds = (kind,) if kind else ("dx", "dd")
    if tail:
        for k in kinds:
            hit = alias_map.get((k, tail))
            if hit:
                name, pe = hit
                return pe, f"registry:{name}", f"unit:{_norm(unit)}"
    entry = curated.get(_norm(org), {}).get(_norm(unit))
    if entry:
        return entry["region_pe"], "curated", f"org:{_norm(org)}"
    return None


def run(db_path: Path = DASE_DB, dry_run: bool = False) -> dict:
    registry, _ = load_registry()
    alias_map = build_alias_map(registry)
    curated, overrides = load_units_file()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    rows = conn.execute("""
        SELECT reference_number, units_operator_name, organization_name,
               nuts_code, total_cost_with_vat
        FROM contracts
    """).fetchall()

    # Reverse NUTS-3 map for the cross-check (several Π.Ε. share a code).
    nuts_to_pes: dict[str, set[str]] = {}
    for pe, code in REGIONAL_UNITS.items():
        nuts_to_pes.setdefault(code, set()).add(canonical_pe(pe))

    resolved: list[tuple[str, str, str, str]] = []
    todo: dict[tuple[str, str], dict] = {}
    warnings = 0
    for r in rows:
        ov = overrides.get(r["reference_number"])
        if ov:
            hit = (ov["region_pe"], "override", ov["note"])
        else:
            hit = resolve(r["units_operator_name"], r["organization_name"],
                          alias_map, curated)
        if hit is None:
            key = (_norm(r["organization_name"]),
                   _norm(r["units_operator_name"]))
            d = todo.setdefault(key, {"n": 0, "eur": 0.0,
                                      "nuts": r["nuts_code"]})
            d["n"] += 1
            d["eur"] += r["total_cost_with_vat"] or 0.0
            continue
        pe, source, basis = hit
        pe = canonical_pe(pe)
        if pe not in REGIONAL_UNITS:          # never fabricate
            raise SystemExit(f"{r['reference_number']}: bad Π.Ε. {pe!r}")
        expected = nuts_to_pes.get(r["nuts_code"])
        if expected and pe not in expected:
            warnings += 1
            print(f"WARN nuts mismatch {r['reference_number']}: "
                  f"{pe} vs {r['nuts_code']} "
                  f"({r['units_operator_name']!r})")
        resolved.append((r["reference_number"], pe, source, basis))

    if not dry_run:
        conn.execute("DELETE FROM dase_contract_regions")
        conn.executemany(
            "INSERT INTO dase_contract_regions VALUES (?,?,?,?,?)",
            [(ref, pe, src, basis, date.today().isoformat())
             for ref, pe, src, basis in resolved])
        conn.commit()
    conn.close()

    n_total = len(rows)
    n_res = len(resolved)
    print(f"-- {n_res}/{n_total} contracts resolved "
          f"({100 * n_res / n_total:.1f}%), {warnings} nuts warnings, "
          f"{len(todo)} (org, unit) pairs unresolved"
          f"{' [dry-run: nothing written]' if dry_run else ''}")
    for (org, unit), d in sorted(todo.items(), key=lambda kv: -kv[1]["eur"]):
        print(f"   TODO curate: {unit!r} @ {org!r} "
              f"({d['n']} contracts, €{d['eur']:,.0f}, nuts {d['nuts']})")
    return {"total": n_total, "resolved": n_res, "todo": todo}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DASE_DB)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    run(args.db, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
