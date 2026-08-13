# -*- coding: utf-8 -*-
"""Pins for the digitised Β. Εύβοια works zones (evia_works_zones.geojson,
built by scripts/build_evia_zones.py from the curated hand-digitised
polygons)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / "data/processed/evia_works_zones.geojson"
CURATED = ROOT / "khmdhs/data/evia_works_zones_digitised.json"

ZONES = {"limni_i", "limni_ii", "limni_iii", "limni_iv", "limni_v",
         "istiaia_i", "istiaia_ii", "istiaia_iii", "istiaia_iv"}


@pytest.fixture(scope="module")
def fc():
    if not GEOJSON.exists():
        pytest.skip("evia_works_zones.geojson not built")
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


def test_all_nine_zones_present(fc):
    assert {f["properties"]["zone"] for f in fc["features"]} == ZONES


def test_curated_source_covers_all_zones():
    cur = json.loads(CURATED.read_text(encoding="utf-8"))
    have = {z for zones in cur["sheets"].values() for z, parts in zones.items()
            if parts}
    assert have == ZONES


def test_areas_within_reason_of_sheet_tables(fc):
    """Digitised area vs the sheet's own table — generous band; the drawn
    zones legitimately differ from the tabulated basin areas in places."""
    for f in fc["features"]:
        p = f["properties"]
        ratio = p["extracted_stremmata"] / p["table_stremmata"]
        assert 0.6 < ratio < 1.4, (p["zone"], ratio)


def test_geometry_inside_north_evia(fc):
    for f in fc["features"]:
        g = f["geometry"]
        rings = (g["coordinates"] if g["type"] == "MultiPolygon"
                 else [g["coordinates"]])
        for poly in rings:
            for ring in poly:
                for lon, lat in ring:
                    assert 22.9 < lon < 23.8 and 38.5 < lat < 39.15, \
                        (f["properties"]["zone"], lon, lat)


def _shoelace(ring):
    """Trapezoid-form shoelace sum in the lon/lat plane: positive = clockwise."""
    return sum((x2 - x1) * (y2 + y1)
               for (x1, y1), (x2, y2) in zip(ring, ring[1:])) / 2.0


def test_exterior_rings_wind_clockwise(fc):
    """d3-geo reads GeoJSON polygons spherically: a CCW exterior in lon/lat
    is the complement of the zone (the whole sphere minus it) — the exact
    bug fixed in c2f3c0e. Pin the CW convention so it can't regress."""
    for f in fc["features"]:
        g = f["geometry"]
        polys = (g["coordinates"] if g["type"] == "MultiPolygon"
                 else [g["coordinates"]])
        for poly in polys:
            exterior, *holes = poly
            assert _shoelace(exterior) > 0, \
                (f["properties"]["zone"], "exterior must be clockwise")
            for hole in holes:
                assert _shoelace(hole) < 0, \
                    (f["properties"]["zone"], "holes must wind counter-clockwise")


def test_site_copy_identical_to_processed():
    """build_evia_zones.py writes the geojson twice (data/processed + the
    Atlas static asset); a partial run or hand edit must not desync them."""
    site = ROOT / "atlas/static/geo/evia_works_zones.geojson"
    if not site.exists():
        pytest.skip("atlas static copy not present")
    assert site.read_bytes() == GEOJSON.read_bytes()
