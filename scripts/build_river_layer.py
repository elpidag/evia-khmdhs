# -*- coding: utf-8 -*-
"""Build the context-rivers display layer (DATA_DECISIONS 2026-08-16).

For sponsored projects whose designation act names RIVERS, the named
watercourses are drawn on the card map. Geometries come from
OpenStreetMap (Overpass: named `waterway=river` ways inside a curated
bbox — the bbox pins the RIGHT namesake), merged and simplified to
~50 m, written to data/processed/ and duplicated byte-identically into
atlas/static/geo/. Each feature carries the project ΑΔΑs it applies to —
the application is curated HERE, never name-matched at runtime.

Attribution duty (on every surface that draws the layer):
«© OpenStreetMap contributors», marked approximate.

Needs: requests, shapely. Run: python scripts/build_river_layer.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests
from shapely.geometry import LineString, MultiLineString, mapping
from shapely.ops import linemerge

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/context_rivers.geojson"
OUT_ATLAS = ROOT / "atlas/static/geo/context_rivers.geojson"

OVERPASS = "https://overpass-api.de/api/interpreter"
# public mirrors tried in order — overpass-api.de 406s some default UAs
MIRRORS = [OVERPASS, "https://overpass.kumi.systems/api/interpreter"]
HEADERS = {"User-Agent": "khmdhs-osint/1.0 (public-interest research tool)"}
SIMPLIFY_DEG = 0.0005  # ≈ 50 m

# curated river set: OSM name + a bbox that pins the right namesake
# (south, west, north, east) + the projects the river belongs to
RIVERS = [
    {
        "name": "Καλαμάς",
        "en": "Kalamas",
        "bbox": (39.20, 19.90, 40.25, 20.95),
        "projects": ["6Φ454653Π8-Ξ1Ζ"],
    },
    {
        "name": "Αχέροντας",
        "en": "Acheron",
        # OSM names the course «Αχέρων»/«Αχέροντας» in stretches — regex
        "name_re": "Αχέρ",
        "bbox": (39.00, 20.20, 39.65, 20.90),
        "projects": ["6Φ454653Π8-Ξ1Ζ"],
    },
    {
        # ΨΖ3Ψ4653Π8-5Β2 (ALFA WOOD, plane-disease sanitation) is scoped
        # «στην περιοχή του Σπερχειού ποταμού (Κομποτάδες, Ζηλευτό κ.α.)»
        # — the river IS the project's extent, so the card must draw it
        # (user, 2026-08-24). The bbox is the Φθιώτιδα valley, from the
        # Τυμφρηστός headwaters to the Μαλιακός delta.
        "name": "Σπερχειός",
        "en": "Sperchios",
        "name_re": "Σπερχει",
        "bbox": (38.70, 21.75, 39.10, 22.75),
        # the two UNNAMED OSM river ways that carry the course between
        # named stretches — each verified to meet its neighbours (0,00 and
        # 0,13 km; 0,24 km). Without them the line broke at Μακρακώμη and
        # again west of Λαμία.
        "extra_ways": (27105313, 265629822),
        "projects": ["ΨΖ3Ψ4653Π8-5Β2"],
    },
]


def fetch_river(name: str, bbox: tuple, name_re: str | None = None,
                extra_ways: tuple[int, ...] = ()) -> MultiLineString:
    """The named course inside the bbox, plus any curated bridging ways.

    Two traps, both found on the Σπερχειός (user, 2026-08-24):

    * **`waterway=river` alone is not the river.** OSM tags a 4,1 km stretch
      of the upper Σπερχειός as `waterway=stream` while still NAMING it, so
      a river-only filter dropped it and left a 3,5 km hole in the drawn
      course. The filter now takes river OR stream — the NAME is what pins
      the watercourse, not the size class.
    * **OSM leaves connecting stretches of the same course unnamed**, so a
      name-filtered query can never be continuous. `extra_ways` names those
      OSM way ids explicitly, each verified to join two NAMED stretches end
      to end — curation by id, in the open, like every other judgment here.
    """
    s, w, n, e = bbox
    name_filter = f'["name"~"{name_re}"]' if name_re else f'["name"="{name}"]'
    extra = f"way(id:{','.join(str(i) for i in extra_ways)});" if extra_ways else ""
    query = f"""[out:json][timeout:120];
(way["waterway"~"^(river|stream)$"]{name_filter}({s},{w},{n},{e});
{extra});
out geom;"""
    # the public mirrors 500/504 at random under load — try each of them a
    # few times before giving up, or a rebuild fails on a passing cloud
    r = None
    for attempt in range(4):
        for url in MIRRORS:
            try:
                r = requests.post(url, data={"data": query},
                                  headers=HEADERS, timeout=180)
            except requests.RequestException as exc:
                print(f"  {url}: {type(exc).__name__}, trying next")
                r = None
                time.sleep(5)
                continue
            if r.status_code == 200:
                break
            print(f"  {url}: HTTP {r.status_code}, trying next")
            time.sleep(5)
        if r is not None and r.status_code == 200:
            break
    if r is None:
        raise SystemExit(f"{name}: every Overpass mirror refused the query")
    r.raise_for_status()
    lines = []
    for el in r.json().get("elements", []):
        pts = [(g["lon"], g["lat"]) for g in el.get("geometry", [])]
        if len(pts) >= 2:
            lines.append(LineString(pts))
    if not lines:
        raise SystemExit(f"{name}: no OSM ways found in bbox {bbox}")
    merged = linemerge(MultiLineString(lines))
    if isinstance(merged, LineString):
        merged = MultiLineString([merged])
    return merged


def label_point(geom: MultiLineString) -> list[float]:
    """midpoint of the longest branch — a stable spot for the name label"""
    longest = max(geom.geoms, key=lambda g: g.length)
    p = longest.interpolate(0.5, normalized=True)
    return [round(p.x, 5), round(p.y, 5)]


def main() -> None:
    feats = []
    for spec in RIVERS:
        geom = fetch_river(spec["name"], spec["bbox"], spec.get("name_re"),
                           spec.get("extra_ways", ()))
        simplified = geom.simplify(SIMPLIFY_DEG)
        if isinstance(simplified, LineString):
            simplified = MultiLineString([simplified])
        gj = mapping(simplified)
        gj["coordinates"] = [
            [[round(x, 5), round(y, 5)] for x, y in part] for part in gj["coordinates"]
        ]
        feats.append({
            "type": "Feature",
            "properties": {
                "name": spec["name"],
                "en": spec["en"],
                "projects": spec["projects"],
                "label_pt": label_point(simplified),
            },
            "geometry": gj,
        })
        n_pts = sum(len(p) for p in gj["coordinates"])
        print(f"{spec['name']}: {len(gj['coordinates'])} parts, {n_pts} points")
        time.sleep(2)

    payload = json.dumps(
        {"type": "FeatureCollection",
         "attribution": "© OpenStreetMap contributors",
         "features": feats},
        ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(payload, encoding="utf-8")
    OUT_ATLAS.write_text(payload, encoding="utf-8")
    print(f"{len(payload) / 1e3:.0f} KB → {OUT.relative_to(ROOT)} + atlas/static/geo/")


if __name__ == "__main__":
    main()
