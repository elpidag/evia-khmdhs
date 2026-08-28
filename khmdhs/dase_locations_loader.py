# -*- coding: utf-8 -*-
"""Load the curated ΔΑΣΕ co-operative registered offices into dase.sqlite's
`contractor_locations` table (DATA_DECISIONS 2026-08-24).

The ΔΑΣΕ DB shares the khmdhs schema, so the same table the Anti-nero
contractor seats live in is used here — empty until now. Column semantics
are kept identical so any reader works on either DB:

  address        the register's own address line (a co-op's is its village)
  city           the reference town of the register record
  region_pe      the Π.Ε. of the REGISTERED OFFICE — the regional unit the
                 geocoded point falls in (the coarse Π.Ε. layer, a ray
                 cast), else the one the registered postcode / town
                 implies. Until 2026-08-28 this column held the Π.Ε. of the
                 co-op's FIRST CONTRACT: the seat choropleth and the actors
                 map read it as the seat and credited 17 travelling co-ops
                 to where they worked (DATA_DECISIONS). The contracts' Π.Ε.
                 now ride in `notes`, for the audit only
  lat/lon        OSM Nominatim, accepted only through the shared gate
  geo_precision  address | municipality | failed — for co-ops it is almost
                 always `municipality`: the centre of the named settlement,
                 because a village seat has no street to place
  seat_source    vies | name_inference — where the seat itself came from
  seat_ref       the ΑΔΑΜ of a contract whose party clause states a seat
  seat_excerpt   that clause, verbatim — from the co-op's LATEST contract
                 that states a seat (a seat can be restated over the years)
  seat_note      why a seat needed explaining: an inference's reasoning, a
                 documented restatement, and the earlier wording verbatim
  source         'vies' / 'name_inference' (the seat's provenance, short)

Validation refuses: an entry with a point but no precision (or the reverse),
a co-op that is not in the dataset's live population, and a `name_inference`
without its note — the inference must always carry its reasoning.

Usage: python -m khmdhs.dase_locations_loader [--db data/processed/dase.sqlite]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import date
from pathlib import Path

from . import db as db_mod
from khmdhs.greek_regions import resolve_pe

DATA_FILE = Path(__file__).parent / "data" / "dase_coop_locations.json"
DEFAULT_DB = (Path(__file__).resolve().parents[1] / "data" / "processed" / "dase.sqlite")


_PE_LAYER = Path(__file__).resolve().parents[1] / "webui" / "static" / "greek_pe.geojson"
_PE_POLYS: list[tuple[str, list]] | None = None


def _pe_polys() -> list[tuple[str, list]]:
    """The 74 Π.Ε. polygons of the coarse display layer, as (pe, rings)."""
    global _PE_POLYS
    if _PE_POLYS is None:
        polys: list[tuple[str, list]] = []
        if _PE_LAYER.exists():
            gj = json.loads(_PE_LAYER.read_text(encoding="utf-8"))
            for f in gj["features"]:
                g = f["geometry"]
                parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
                for part in parts:
                    polys.append((f["properties"]["pe"], part))
        _PE_POLYS = polys
    return _PE_POLYS


def _inside(x: float, y: float, ring: list) -> bool:
    ok, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            ok = not ok
        j = i
    return ok


def seat_pe(lat: float | None, lon: float | None, city: str | None,
            postal: str | None) -> tuple[str | None, str]:
    """The Π.Ε. of a registered office: the unit the point lies in, else
    the one the postcode / town implies. Returns (pe, how)."""
    if lat is not None and lon is not None:
        for pe, rings in _pe_polys():
            if _inside(lon, lat, rings[0]) and not any(_inside(lon, lat, h) for h in rings[1:]):
                return pe, "point"
    pe, how = resolve_pe(city, postal)
    return pe, how


def load(conn: sqlite3.Connection, data_file: Path = DATA_FILE) -> int:
    doc = json.loads(data_file.read_text(encoding="utf-8"))
    coops: dict[str, dict] = doc["coops"]
    today = date.today().isoformat()
    n = 0
    for vat, e in sorted(coops.items()):
        reg = e.get("register") or {}
        cur = e.get("curated") or {}
        seat_source = "name_inference" if cur.get("settlement") else (
            "vies" if reg.get("settlement") or reg.get("city") else None)
        if seat_source == "name_inference" and not cur.get("note"):
            raise ValueError(f"{vat}: a name_inference seat must carry its note")
        lat, lon = e.get("lat"), e.get("lon")
        prec = e.get("geo_precision")
        if (lat is None) != (lon is None):
            raise ValueError(f"{vat}: half a coordinate pair")
        if lat is not None and prec in (None, "failed"):
            raise ValueError(f"{vat}: a point without a precision")
        if lat is None and prec not in (None, "failed"):
            raise ValueError(f"{vat}: precision {prec!r} without a point")

        settlement = cur.get("settlement") or reg.get("settlement")
        city = cur.get("city") or reg.get("city")
        postal = cur.get("postal_code") or reg.get("postal_code")
        seat = e.get("contract_seat") or {}
        # the seat note carries, in order: a curated inference's reasoning, a
        # per-entry note explaining a restatement, and the earlier wording the
        # co-op's own older contract used (2 cases, 2026-08-24) — a seat that
        # changed must never look like a single unchanging fact
        older = e.get("earlier_seat") or {}
        note = " ".join(x for x in (
            cur.get("note"), e.get("seat_note"),
            (f"Earlier, contract {older['ref']} ({older.get('date') or 'undated'}) "
             f"stated: «{older['excerpt']}»." if older else None)) if x) or None
        pe, how = seat_pe(lat, lon, city, postal)
        contract_pes = ", ".join(e.get("contract_pes") or []) or "none"
        conn.execute(
            """INSERT OR REPLACE INTO contractor_locations
               (vat_number, legal_name, address, postal_code, city, region_pe,
                lat, lon, geo_precision, source, source_url, notes, curated_at,
                seat_source, seat_ref, seat_excerpt, seat_note, geo_level)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (vat, reg.get("name") or (e.get("registry_names") or [None])[0],
             settlement, postal, city, pe, lat, lon, prec,
             seat_source, reg.get("source_url"),
             (f"region_pe is the Π.Ε. of the registered office (by {how}); "
              f"this co-operative's contracts sit in: {contract_pes}"),
             today, seat_source, seat.get("ref"), seat.get("excerpt"), note,
             "settlement" if prec == "municipality" else (
                 "street" if prec == "address" else None)))
        n += 1
    conn.commit()
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--file", type=Path, default=DATA_FILE)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.file.exists():
        logging.warning("no %s — nothing to load", args.file.name)
        return 0
    conn = db_mod.init_db(args.db)   # takes the PATH and returns the connection
    n = load(conn, args.file)
    located = conn.execute(
        "SELECT COUNT(*) FROM contractor_locations WHERE lat IS NOT NULL").fetchone()[0]
    inferred = conn.execute(
        "SELECT COUNT(*) FROM contractor_locations WHERE seat_source = 'name_inference'"
    ).fetchone()[0]
    conn.close()
    logging.info("Wrote %d co-op locations (%d located, %d seats inferred from the "
                 "co-op's own name).", n, located, inferred)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
