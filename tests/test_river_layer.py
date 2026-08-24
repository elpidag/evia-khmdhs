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


# each curated river, the project(s) its act names it for, and the window
# its label anchor must fall in — the bbox is what pins the RIGHT namesake
RIVERS = {
    "Καλαμάς": ("6Φ454653Π8-Ξ1Ζ", (19.5, 21.5, 38.8, 40.5)),
    "Αχέροντας": ("6Φ454653Π8-Ξ1Ζ", (19.5, 21.5, 38.8, 40.5)),
    # ΨΖ3Ψ4653Π8-5Β2 is scoped «στην περιοχή του Σπερχειού ποταμού»
    # (user, 2026-08-24)
    "Σπερχειός": ("ΨΖ3Ψ4653Π8-5Β2", (21.7, 22.8, 38.6, 39.2)),
}


def test_layer_shape():
    fc = json.loads(MAIN.read_text(encoding="utf-8"))
    assert "OpenStreetMap" in fc["attribution"]
    names = {f["properties"]["name"] for f in fc["features"]}
    assert names == set(RIVERS)
    for f in fc["features"]:
        p = f["properties"]
        want_ada, (w, e, s, n) = RIVERS[p["name"]]
        assert want_ada in p["projects"]
        lon, lat = p["label_pt"]
        assert w < lon < e and s < lat < n, (p["name"], p["label_pt"])
        assert f["geometry"]["type"] == "MultiLineString"
        assert sum(len(part) for part in f["geometry"]["coordinates"]) > 50


def test_sperchios_passes_the_projects_work_sites():
    """The river is drawn because it IS the project's extent: its course
    must run past the localities the act names (Κομποτάδες, Ζηλευτό) — a
    namesake elsewhere in Greece would not."""
    import math

    fc = json.loads(MAIN.read_text(encoding="utf-8"))
    sp = next(f for f in fc["features"] if f["properties"]["name"] == "Σπερχειός")
    pts = [c for part in sp["geometry"]["coordinates"] for c in part]
    for name, lat, lon in (("Κομποτάδες", 38.86764, 22.34881),
                           ("Ζηλευτό", 38.8944, 22.2686)):
        km = min(math.hypot((c[0] - lon) * 88, (c[1] - lat) * 111) for c in pts)
        assert km < 5, f"{name} is {km:.1f} km from the drawn course"


def test_sperchios_course_is_continuous():
    """The drawn course must not break visibly (user, 2026-08-24).

    Two causes were found and fixed in the builder: OSM tags a 4,1 km
    stretch of the upper Σπερχειός `waterway=stream` while still naming it
    (a river-only filter dropped it, leaving a 3,5 km hole), and it leaves
    two connecting stretches unnamed (now curated by way id). What remains
    is ONE ~1,1 km discontinuity west of Λαμία, where OSM's own two named
    ways do not meet — data, not our query. This pins both: the total
    length, and that nothing bigger than that reopens.
    """
    import math

    fc = json.loads(MAIN.read_text(encoding="utf-8"))
    sp = next(f for f in fc["features"] if f["properties"]["name"] == "Σπερχειός")
    parts = sp["geometry"]["coordinates"]

    def km(a, b):
        return math.hypot((a[0] - b[0]) * 88, (a[1] - b[1]) * 111)

    total = sum(sum(km(p[i], p[i + 1]) for i in range(len(p) - 1)) for p in parts)
    assert total > 84, f"the course lost length: {total:.1f} km"
    ends = [(p[0], p[-1]) for p in parts]
    gaps = sorted(
        min(km(a1, b0), km(a0, b1), km(a0, b0), km(a1, b1))
        for i, (a0, a1) in enumerate(ends)
        for j, (b0, b1) in enumerate(ends)
        if i < j
    )
    # every part must sit within the known Λαμία gap of a neighbour
    assert gaps[: len(parts) - 1] == sorted(gaps)[: len(parts) - 1]
    assert max(gaps[: len(parts) - 1]) < 1.5, f"a new hole opened: {gaps[:3]}"
