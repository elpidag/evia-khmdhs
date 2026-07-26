"""Pins for the Π.Ε. map layer: curation, geojson artefacts, canonicalizer.

The Π.Ε. polygons are dissolved from the Kallikratis municipality layer via
the hand-curated municipality→Π.Ε. assignment (DATA_DECISIONS 2026-07-26);
these tests keep the committed artefacts and the curation consistent.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from khmdhs.greek_regions import (
    CANONICAL_PE_ALIASES, CANONICAL_PES, PE_CENTROIDS, canonical_pe,
)

ROOT = Path(__file__).resolve().parent.parent
GAZETTEER = ROOT / "khmdhs" / "data" / "greek_municipalities.json"
AUTHORITIES = ROOT / "khmdhs" / "data" / "forest_authorities.json"
PE_GEOJSON = ROOT / "webui" / "static" / "greek_pe.geojson"
PE_HIRES_GEOJSON = ROOT / "webui" / "static" / "greek_pe_hires.geojson"
MUNI_BORDERS_GEOJSON = ROOT / "webui" / "static" / "greek_muni_borders.geojson"
REAL_DB = ROOT / "data" / "processed" / "khmdhs.sqlite"


# ---------------------------------------------------------------------------
# canonical_pe
# ---------------------------------------------------------------------------

def test_canonical_pe_identity_and_aliases():
    assert canonical_pe("Π.Ε. Ευβοίας") == "Π.Ε. Ευβοίας"
    assert canonical_pe("Π.Ε. Εύβοιας") == "Π.Ε. Ευβοίας"
    assert canonical_pe("Π.Ε. Πρεβέζης") == "Π.Ε. Πρέβεζας"
    assert canonical_pe("Π.Ε. Ρεθύμνης") == "Π.Ε. Ρεθύμνου"
    assert canonical_pe("Π.Ε. Άγνωστη") is None
    assert canonical_pe(None) is None
    assert canonical_pe("") is None


def test_canonical_vocabulary_is_the_74_kallikratis_units():
    assert len(CANONICAL_PES) == 74
    # no alias maps onto another alias
    assert all(v in CANONICAL_PES for v in CANONICAL_PE_ALIASES.values())


# ---------------------------------------------------------------------------
# municipality gazetteer curation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gazetteer():
    return json.loads(GAZETTEER.read_text(encoding="utf-8"))


def test_gazetteer_pe_coverage_and_canonicality(gazetteer):
    assert len(gazetteer) == 325
    pes = {m["pe"] for m in gazetteer.values()}
    assert all(pe in CANONICAL_PES for pe in pes)
    assert len(pes) == 74


def test_gazetteer_pe_blocks_are_contiguous(gazetteer):
    runs, last = [], None
    for code in sorted(gazetteer, key=int):
        pe = gazetteer[code]["pe"]
        if pe != last:
            runs.append(pe)
            last = pe
    assert len(runs) == len(set(runs)) == 74


def test_gazetteer_agrees_with_forest_authority_anchors(gazetteer):
    fa = json.loads(AUTHORITIES.read_text(encoding="utf-8"))
    checked = 0
    for name, a in fa["authorities"].items():
        code, pe = a.get("municipality_code"), a.get("region_pe")
        if not (code and pe):
            continue
        checked += 1
        assert canonical_pe(gazetteer[code]["pe"]) == canonical_pe(pe), name
    assert checked >= 97


# ---------------------------------------------------------------------------
# built artefacts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", [PE_GEOJSON, PE_HIRES_GEOJSON])
def test_pe_geojson_features_match_curated_pes(gazetteer, path):
    geo = json.loads(path.read_text(encoding="utf-8"))
    feature_pes = {f["properties"]["pe"] for f in geo["features"]}
    assert feature_pes == {m["pe"] for m in gazetteer.values()}
    for f in geo["features"]:
        assert f["properties"]["name"] == f["properties"]["pe"].removeprefix("Π.Ε. ")


def test_hires_layer_is_finer_than_coarse():
    # The drill-zoom layer must actually carry more detail than the eager
    # country-view layer (this is the whole point of shipping both).
    assert PE_HIRES_GEOJSON.stat().st_size > 2 * PE_GEOJSON.stat().st_size


def test_muni_borders_are_interior_lines_of_multi_municipality_pes(gazetteer):
    geo = json.loads(MUNI_BORDERS_GEOJSON.read_text(encoding="utf-8"))
    border_pes = {f["properties"]["pe"] for f in geo["features"]}
    from collections import Counter
    counts = Counter(m["pe"] for m in gazetteer.values())
    multi = {pe for pe, n in counts.items() if n > 1}
    # Only multi-municipality Π.Ε. can have interior borders — but island
    # Π.Ε. whose municipalities sit on separate islands (Κέρκυρα+Παξοί,
    # Κως+Νίσυρος, the Κυκλάδες groups…) legitimately have none.
    assert border_pes <= multi
    for pe in ("Π.Ε. Αρκαδίας", "Π.Ε. Ευβοίας", "Π.Ε. Πειραιώς",
               "Π.Ε. Κεντρικού Τομέα Αθηνών", "Π.Ε. Θεσσαλονίκης"):
        assert pe in border_pes
    for f in geo["features"]:
        assert f["geometry"]["type"] in ("LineString", "MultiLineString",
                                         "GeometryCollection")


def test_pe_centroid_stores_are_identical_and_complete():
    web = json.loads((ROOT / "webui" / "static" / "pe_centroids.json")
                     .read_text(encoding="utf-8"))
    pkg = json.loads((ROOT / "khmdhs" / "data" / "pe_centroids.json")
                     .read_text(encoding="utf-8"))
    assert web == pkg
    assert set(web) == set(CANONICAL_PES)
    assert set(PE_CENTROIDS) == set(CANONICAL_PES)


def test_merged_nuts3_groups_now_have_distinct_centroids():
    for a, b in [("Π.Ε. Άρτας", "Π.Ε. Πρέβεζας"),
                 ("Π.Ε. Αργολίδας", "Π.Ε. Αρκαδίας"),
                 ("Π.Ε. Λακωνίας", "Π.Ε. Μεσσηνίας"),
                 ("Π.Ε. Καβάλας", "Π.Ε. Θάσου")]:
        assert PE_CENTROIDS[a] != PE_CENTROIDS[b]


# ---------------------------------------------------------------------------
# real-DB pin: every stored Π.Ε. lands on a polygon
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_DB.exists(), reason="committed DB not present")
def test_real_db_every_region_pe_canonicalizes_to_a_polygon():
    conn = sqlite3.connect(REAL_DB)
    pes = set()
    for tbl in ("contract_project_regions", "contractor_locations",
                "forest_authorities", "contract_sites"):
        pes |= {r[0] for r in conn.execute(
            f"SELECT DISTINCT region_pe FROM {tbl} "
            f"WHERE region_pe IS NOT NULL")}
    conn.close()
    unresolved = {pe for pe in pes if canonical_pe(pe) not in PE_CENTROIDS}
    assert not unresolved, unresolved
