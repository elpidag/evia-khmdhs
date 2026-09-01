# -*- coding: utf-8 -*-
"""Pins for the daily burnt-area increments of August 2021
(scripts/build_alerts_burn.py from NASA VIIRS VNP64A1 tile h19v05) drawn by
the story's Figure 04."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "data/processed/alerts_burn_2021.geojson"
ATLAS = ROOT / "atlas/static/geo/alerts_burn_2021.geojson"
BOX = (19.5, 34.7, 28.6, 41.8)
PIXEL_KM2 = 463.3127 ** 2 / 1e6


@pytest.fixture(scope="module")
def fc():
    if not MAIN.exists():
        pytest.skip("alerts_burn_2021.geojson not built")
    return json.loads(MAIN.read_text(encoding="utf-8"))


def _shoelace(ring):
    """Trapezoid-form shoelace sum in the lon/lat plane: positive = clockwise."""
    return sum((x2 - x1) * (y2 + y1)
               for (x1, y1), (x2, y2) in zip(ring, ring[1:])) / 2.0


def test_copies_byte_identical():
    if not MAIN.exists():
        pytest.skip("not built")
    assert MAIN.read_bytes() == ATLAS.read_bytes()


def test_one_feature_per_day_in_order(fc):
    days = [f["properties"]["day"] for f in fc["features"]]
    assert days == sorted(days) and len(days) == len(set(days))
    assert all(d.startswith("2021-08-") and 1 <= int(d[-2:]) <= 23 for d in days)
    assert len(days) >= 15
    for f in fc["features"]:
        p = f["properties"]
        assert p["doy"] == 212 + int(p["day"][-2:])


def test_areas_follow_the_pixel_count(fc):
    total_px = 0
    for f in fc["features"]:
        p = f["properties"]
        assert p["px"] > 0
        assert abs(p["km2"] - p["px"] * PIXEL_KM2) < 0.1 + p["px"] * PIXEL_KM2 * 0.01
        total_px += p["px"]
    # every mainland fire region of the alerts lies on the tile: the month's
    # burnt ground is in the hundreds of km², not a handful of pixels
    assert total_px * PIXEL_KM2 > 500


def test_rings_wound_for_d3_and_inside_the_frame(fc):
    for f in fc["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            assert _shoelace(poly[0]) > 0, f["properties"]["day"]
            for hole in poly[1:]:
                assert _shoelace(hole) < 0, f["properties"]["day"]
            for ring in poly:
                for lon, lat in ring:
                    assert BOX[0] <= lon <= BOX[2] and BOX[1] <= lat <= BOX[3]


def test_attribution_and_coverage_caveat_travel_with_the_layer(fc):
    assert "VNP64A1" in fc["attribution"]
    assert "Rhodes" in fc["attribution"]
    assert fc["source"]["tile"] == "h19v05"
