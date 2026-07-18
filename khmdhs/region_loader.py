"""Load curated project regions from data/contract_regions.json into the DB.

The JSON file is the source of truth — manually curated by reading each
contract's title + short_description. This loader just translates region
names into NUTS-3 codes (via khmdhs.greek_regions) and replaces rows in
the contract_project_regions table. Idempotent — re-running wipes and
rewrites per ADAM.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db
from khmdhs.greek_regions import nuts3_for

DATA_FILE = Path(__file__).parent / "data" / "contract_regions.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.region_loader")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with args.data.open(encoding="utf-8") as f:
        curation: dict = json.load(f)

    # Validate every Π.Ε. name resolves to a NUTS-3 code before touching the DB
    unknown: set[str] = set()
    for entry in curation.values():
        for r in entry.get("regions", []):
            if nuts3_for(r["pe"]) is None:
                unknown.add(r["pe"])
    if unknown:
        logging.error("Unknown Π.Ε. names in %s: %s", args.data, sorted(unknown))
        logging.error("Add them to khmdhs/greek_regions.REGIONAL_UNITS or fix the JSON.")
        return 2

    n_contracts = len(curation)
    n_rows = sum(len(e.get("regions", [])) for e in curation.values())
    n_pan = sum(1 for e in curation.values() if not e.get("regions"))
    logging.info("Loaded %d contracts from %s (%d region rows, %d pan-Greek)",
                 n_contracts, args.data, n_rows, n_pan)

    if args.dry_run:
        for adam, entry in list(curation.items())[:5]:
            logging.info("DRY %s -> %s", adam, [r["pe"] for r in entry["regions"]])
        logging.info("DRY ... (truncated)")
        return 0

    conn = init_db(args.db)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn:
        for adam, entry in curation.items():
            conn.execute("DELETE FROM contract_project_regions WHERE reference_number = ?", (adam,))
            for seq, r in enumerate(entry.get("regions", [])):
                conn.execute(
                    """INSERT INTO contract_project_regions
                       (reference_number, seq, region_pe, nuts3_code, note, source, curated_at)
                       VALUES (?, ?, ?, ?, ?, 'manual', ?)""",
                    (adam, seq, r["pe"], nuts3_for(r["pe"]), r.get("note"),
                     entry.get("curated_at") or now),
                )
    logging.info("Done. Wrote project-region rows for %d contracts.", n_contracts)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
