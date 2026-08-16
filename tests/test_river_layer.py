# -*- coding: utf-8 -*-
"""Context-rivers display layer (DATA_DECISIONS 2026-08-16): the two
copies stay byte-identical, features are the curated rivers with their
project application and label anchors, attribution is present."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "data/processed/context_rivers.geojson"
ATLAS = ROOT / "atlas/static/geo/context_rivers.geojson"


def test_copies_byte_identical():
    assert MAIN.read_bytes() == ATLAS.read_bytes()


def test_layer_shape():
    fc = json.loads(MAIN.read_text(encoding="utf-8"))
    assert "OpenStreetMap" in fc["attribution"]
    names = {f["properties"]["name"] for f in fc["features"]}
    assert names == {"Καλαμάς", "Αχέροντας"}
    for f in fc["features"]:
        p = f["properties"]
        assert "6Φ454653Π8-Ξ1Ζ" in p["projects"]
        lon, lat = p["label_pt"]
        assert 19.5 < lon < 21.5 and 38.8 < lat < 40.5
        assert f["geometry"]["type"] == "MultiLineString"
        assert sum(len(part) for part in f["geometry"]["coordinates"]) > 50
