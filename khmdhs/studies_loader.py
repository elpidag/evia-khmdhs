"""Load curated per-contract μελέτη (study/planning) costs into the DB.

Source of truth: khmdhs/data/study_costs.json —
    {ADAM: {"eur": <net-of-ΦΠΑ €>, "page": n, "excerpt": "..."}}
extracted from the signed PDFs' «Κόστος εκπόνησης μελετών (ΣΑΥ-ΦΑΥ)» line
by scripts/extract_study_costs.py and reviewed before committing
(DATA_DECISIONS 2026-07-26).

Validates every entry (contract exists; amount below the contract's stated
gross total when one is recorded) and refuses to load on failure. Re-run
after any contract refetch (CASCADE wipes the table's rows).

Usage:  .venv/bin/python -m khmdhs.studies_loader [--db path]
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

STUDY_COSTS_FILE = Path(__file__).parent / "data" / "study_costs.json"


def load_curated(path: Path = STUDY_COSTS_FILE) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for ref, e in data.items():
        if not isinstance(e.get("eur"), (int, float)) or e["eur"] <= 0:
            raise SystemExit(f"study_costs.json: bad eur for {ref}: {e!r}")
        if not e.get("excerpt"):
            raise SystemExit(f"study_costs.json: {ref} has no excerpt evidence")
    return data


def write_db(conn: sqlite3.Connection, curated: dict[str, dict]) -> int:
    known = {r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts")}
    missing = sorted(set(curated) - known)
    if missing:
        raise SystemExit(f"study_costs.json refs not in DB: {missing}")
    for ref, e in curated.items():
        stated = conn.execute(
            "SELECT total_cost_with_vat FROM contracts WHERE reference_number=?",
            (ref,)).fetchone()[0]
        if stated and e["eur"] >= stated:
            raise SystemExit(
                f"{ref}: study cost {e['eur']} >= stated total {stated}")
    conn.execute("DELETE FROM contract_study_costs")
    conn.executemany(
        "INSERT INTO contract_study_costs "
        "(reference_number, eur, page, excerpt, curated_at) VALUES (?,?,?,?,?)",
        [(ref, e["eur"], e.get("page"), e["excerpt"], date.today().isoformat())
         for ref, e in curated.items()])
    conn.commit()
    return len(curated)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    conn = db.init_db(args.db)
    n = write_db(conn, load_curated())
    total = conn.execute(
        "SELECT ROUND(SUM(eur), 2) FROM contract_study_costs").fetchone()[0]
    logging.info("study costs: %d contracts, %.2f € net total", n, total or 0)
    conn.close()


if __name__ == "__main__":
    main()
