"""Load curated contractor home locations into contractor_locations table.

The JSON file is the source of truth — manually curated from anonymous
public sources (vrisko.gr, company websites, ΣΑΤΕ catalogues). This loader
attaches the NUTS-3 code via khmdhs.greek_regions and INSERT-OR-REPLACEs
into the DB. Idempotent.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db
from khmdhs.greek_regions import nuts3_for

DATA_FILE = Path(__file__).parent / "data" / "contractor_locations.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.contractor_loader")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with args.data.open(encoding="utf-8") as f:
        curation: dict = json.load(f)

    # Validate region_pe values that ARE set (null is allowed for pending rows)
    unknown: set[str] = set()
    for entry in curation.values():
        pe = entry.get("region_pe")
        if pe and nuts3_for(pe) is None:
            unknown.add(pe)
    if unknown:
        logging.error("Unknown Π.Ε. names in %s: %s", args.data, sorted(unknown))
        return 2

    n = len(curation)
    n_resolved = sum(1 for d in curation.values() if d.get("region_pe"))
    logging.info("Loaded %d contractors from %s (%d resolved, %d pending)",
                 n, args.data, n_resolved, n - n_resolved)

    by_source = {}
    for d in curation.values():
        by_source[d.get("source", "?")] = by_source.get(d.get("source", "?"), 0) + 1
    logging.info("By source: %s", sorted(by_source.items(), key=lambda x: -x[1]))

    if args.dry_run:
        return 0

    conn = init_db(args.db)
    with conn:
        for vat, d in curation.items():
            pe = d.get("region_pe")
            nuts3 = nuts3_for(pe) if pe else None
            conn.execute(
                """INSERT OR REPLACE INTO contractor_locations
                   (vat_number, legal_name, address, postal_code, city, region_pe,
                    nuts3_code, source, source_url, notes, curated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (vat, d.get("legal_name"), d.get("address"), d.get("postal_code"),
                 d.get("city"), pe, nuts3, d.get("source"), d.get("source_url"),
                 d.get("notes"), d.get("curated_at")),
            )
    logging.info("Done. Wrote %d contractor_locations rows.", n)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
