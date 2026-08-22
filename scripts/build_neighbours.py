"""Build the CONTEXT LAND layer: Greece's neighbours + Mount Athos.

Every map on the site draws Greece alone, which leaves the country floating
in an empty sea (user, 2026-08-22). This script builds one small, inert
layer of the land AROUND the frame — Albania, North Macedonia, Bulgaria,
Türkiye, Italy's heel and the little that shows of Serbia, Kosovo and
Montenegro — plus the **Athos peninsula**, which is missing from every
administrative layer we draw because Άγιον Όρος is not a municipality:
it is a self-governed monastic state outside the Kallikratis δήμοι, so
neither the geodata.gov.gr layer our Π.Ε. are dissolved from nor Eurostat's
own NUTS-3 «Chalkidiki» (verified: it stops at lon 24.021) contains it.
Drawn as context land, it is honest — no Anti-nero contract can be there.

Sources
  * neighbours — Eurostat GISCO countries 1:1M, EPSG:4326, per country
    (`gisco-services.ec.europa.eu/distribution/v2/countries/distribution/`).
    Attribution required and carried in the maps' caveats:
    «© EuroGeographics for the administrative boundaries».
  * Athos — the official «Άθως» polygon of the Kallikratis layer
    (geodata.gov.gr, CC-BY — the same source as every Greek boundary we
    draw) for its EXTENT, refined with OpenStreetMap's `natural=coastline`
    for its SHAPE, since the official outline is a 63-point generalisation
    up to 734 m from the shore. «© OpenStreetMap contributors» rides beside
    the geodata.gov.gr line. (OSM's admin relation 2135921 of the monastic
    state is the sanity net only: alone it covers 1 340 km², four times the
    peninsula, because it includes the territorial waters.)

Method: clip to the frame's box, simplify in the metric EPSG:3035 plane,
then buffer OUTWARD by a little so the neighbour land tucks UNDER the
Greek layer — drawn first, it can only be hidden by Greece, never leave a
sliver of sea along a land border. Coordinates are rounded to 4 decimals
(~11 m), which is far finer than the layer is ever drawn.

    .venv/Scripts/python.exe scripts/build_neighbours.py [--refresh]

Writes atlas/static/geo/neighbours.geojson (one feature per country plus
Athos; `kind` = neighbour | athos). The downloads are cached in
data/processed/geo_cache/ (gitignored).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests
import shapely
from pyproj import Transformer
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import (linemerge, polygonize, split, transform as shp_transform,
                         unary_union)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "processed" / "geo_cache"
OUT = ROOT / "atlas" / "static" / "geo" / "neighbours.geojson"
# the official Kallikratis layer's own «Άθως» feature (geodata.gov.gr, CC-BY)
OFFICIAL_MUNIS = ROOT / "data" / "raw" / "firewatch_municipalities.geojson"

# what shows around a map of Greece; Türkiye and Italy are clipped hard by
# the frame, the Balkan three barely appear at the top edge
# XK (Kosovo) has no 2024 file on GISCO and never reaches the frame anyway
COUNTRIES = ("AL", "MK", "BG", "TR", "IT", "RS", "ME")
GISCO = ("https://gisco-services.ec.europa.eu/distribution/v2/countries/"
         "distribution/{c}-region-01m-4326-2024.geojson")
ATHOS_REL = 2135921
ATHOS_BOX = (40.00, 23.85, 40.60, 24.60)   # S, W, N, E — the peninsula
ATHOS_ON_LAND = ((24.2462, 40.2561),       # Καρυές
                 (24.3548, 40.1690),       # Μεγίστη Λαύρα
                 (23.9830, 40.3310))       # Ουρανούπολη, at the neck
OVERPASS = "https://overpass-api.de/api/interpreter"

FRAME = box(18.2, 33.8, 29.6, 43.2)   # lon/lat around the Greek frame
SIMPLIFY_M = 500                       # scenery: sub-pixel at the country view
# Athos is drawn AS Greek land beside Greek land, so it carries the Greek
# layers' own accuracy: the hi-res tolerance of build_pe_geojson.py (user,
# 2026-08-22 — «the same level of accuracy as the rest of Greece»); 16 KB
ATHOS_SIMPLIFY_M = 30
PRECISION_ATHOS = 5                    # decimals ≈ 1 m, as the Greek layers
TUCK_M = 400                           # under the Greek coastline
LAND_NEIGHBOURS = ("AL", "MK", "BG", "TR")   # the four sharing a land border
PE_LAYER = ROOT / "webui" / "static" / "greek_pe.geojson"   # the same coarse layer the Atlas ships as pe.topo.json
PRECISION = 4                          # decimals ≈ 11 m
MIN_ISLAND_KM2 = 4                     # scenery: a smaller islet is a dot

to_m = Transformer.from_crs(4326, 3035, always_xy=True).transform
to_ll = Transformer.from_crs(3035, 4326, always_xy=True).transform


def fetch(url: str, path: Path, refresh: bool, **kw) -> str:
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    r = requests.get(url, timeout=180, **kw) if "data" not in kw else \
        requests.post(url, timeout=180, **kw)
    r.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(r.text, encoding="utf-8")
    return r.text


def _official_athos():
    """The «Άθως» feature of the Kallikratis layer — the official extent."""
    fc = json.loads(OFFICIAL_MUNIS.read_text(encoding="utf-8"))
    hits = [f for f in fc["features"] if (f.get("properties") or {}).get("name") == "Άθως"]
    if not hits:
        raise SystemExit(f"Athos: «Άθως» not found in {OFFICIAL_MUNIS.name}")
    return shape(hits[0]["geometry"])


def _extend(p, q, d: float = 3000.0):
    """The point d metres beyond q on the ray p→q (in the metric plane)."""
    import math
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1.0
    return (q[0] + dx / L * d, q[1] + dy / L * d)


def clean(geom_ll, simplify_m: float = SIMPLIFY_M, tuck_m: float = TUCK_M,
          precision: int = PRECISION):
    """Clip to the frame, tuck under Greece and simplify — in metres."""
    g = geom_ll.intersection(FRAME)
    if g.is_empty:
        return None
    # tuck first (mitred, so the buffer adds no arc points), simplify after
    m = shp_transform(to_m, g).buffer(tuck_m, quad_segs=1, join_style="mitre",
                                      mitre_limit=2.0)
    m = m.simplify(simplify_m, preserve_topology=True)
    if m.is_empty:
        return None
    # scenery, not a gazetteer: drop islets too small to read, they cost
    # more points than they carry
    parts = list(getattr(m, "geoms", [m]))
    keep = [q for q in parts if q.area >= MIN_ISLAND_KM2 * 1e6]
    if keep:
        m = shapely.union_all(keep)
    return shapely.set_precision(shp_transform(to_ll, m), 10 ** -precision)


def athos(refresh: bool):
    """The Athos peninsula: the OFFICIAL extent, the OSM coastline.

    Two sources, each for what it is good at (user, 2026-08-22):

    * WHERE it ends — the **official** «Άθως» polygon of the Kallikratis
      layer (geodata.gov.gr, CC-BY; the FireWatch copy in `data/raw/
      firewatch_municipalities.geojson` carries it as feature 326, with no
      ΥΠΕΣ code — which is exactly why our municipality→Π.Ε. curation never
      saw it and the third leg went missing). Its land border at the neck,
      a 676 m line, cuts the peninsula from Chalkidiki.
    * WHAT it looks like — the OSM `natural=coastline` ways: the official
      polygon is a 63-point generalisation whose outline wanders up to
      734 m from the shore, far coarser than the 30 m the Greek layers are
      drawn at, so the coast comes from OSM, closed against the peninsula's
      box into land polygons and taken as the one holding Καρυές.

    The result is 334.1 km²; the published figure is 335.6 and the official
    polygon as shipped measures 337.1 — a spread of ±0.5 % between three
    honest measurements of the same peninsula, and the cut sits inside it.
    """
    txt = fetch(OVERPASS, CACHE / "athos_rel.json", refresh,
                data={"data": f"[out:json][timeout:150];rel({ATHOS_REL});out geom;"})
    rel = json.loads(txt)["elements"][0]
    admin_lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                   for m in rel.get("members", [])
                   if m.get("type") == "way" and m.get("role") == "outer" and m.get("geometry")]
    if not admin_lines:
        raise SystemExit("Athos: the relation carries no outer way geometry")
    admin = shapely.union_all(list(polygonize(linemerge(admin_lines))))
    official = _official_athos()

    s, w, n, e = ATHOS_BOX
    coast_txt = fetch(OVERPASS, CACHE / "athos_coast.json", refresh,
                      data={"data": f'[out:json][timeout:200];way["natural"="coastline"]'
                                    f'({s},{w},{n},{e});out geom;'})
    bb = box(w, s, e, n)
    lines = []
    for el in json.loads(coast_txt)["elements"]:
        g = el.get("geometry", [])
        if len(g) > 1:
            piece = LineString([(p["lon"], p["lat"]) for p in g]).intersection(bb)
            if not piece.is_empty:
                lines.append(piece)
    land = [poly for poly in polygonize(unary_union(lines + [bb.boundary]))
            if any(poly.contains(Point(*q)) for q in ATHOS_ON_LAND)]
    if not land:
        raise SystemExit("Athos: no land polygon holds the test points")
    # the monastic state's own area first — it keeps the mainland out of the
    # way; the official border then places the cut inside it
    coast_land = shapely.union_all(land).intersection(admin)
    off_m = shp_transform(to_m, official)
    coast_m = shp_transform(to_m, coast_land)
    necks = [g for g in getattr(off_m.boundary.difference(coast_m.boundary.buffer(500)),
                                "geoms", [off_m.boundary]) if g.length > 200]
    if not necks:
        raise SystemExit("Athos: the official polygon has no land border to cut on")
    neck = max(necks, key=lambda g: g.length)
    cut = LineString([_extend(neck.coords[1], neck.coords[0])] + list(neck.coords) +
                     [_extend(neck.coords[-2], neck.coords[-1])])
    pieces = list(split(coast_m, cut).geoms)
    keep = [q for q in pieces if q.contains(shp_transform(to_m, Point(*ATHOS_ON_LAND[0])))]
    if not keep:
        raise SystemExit("Athos: the official border does not cut the peninsula")
    peninsula = shp_transform(to_ll, keep[0])
    # the admin relation stays the sanity net — loosely: the two borders at
    # the neck are drawn a few hundred metres apart, so the piece may poke
    # out of the monastic state's own line by about a square kilometre, no
    # more (the earlier blob was four times the peninsula)
    stray = shp_transform(to_m, peninsula.difference(admin)).area / 1e6
    if stray > 3:
        raise SystemExit(f"Athos: {stray:.1f} km² of the cut piece lies outside "
                         "the monastic state's area — check the borders")
    km2 = shp_transform(to_m, peninsula).area / 1e6
    if not 320 < km2 < 350:
        raise SystemExit(f"Athos: {km2:.0f} km² is not the peninsula (334–337 km², "
                         "depending on which of the three boundaries is measured)")
    print(f"  Athos land: {km2:.1f} km²")
    # land beside Greek land: fine tolerance, and no tuck (nothing of ours
    # to hide under)
    return clean(peninsula, ATHOS_SIMPLIFY_M, 0, PRECISION_ATHOS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true", help="re-download the sources")
    args = ap.parse_args(argv)

    feats = []
    raws = {}
    for c in COUNTRIES:
        raw = fetch(GISCO.format(c=c), CACHE / f"{c}.geojson", args.refresh)
        fc = json.loads(raw)
        geoms = [shape(f["geometry"]) for f in fc.get("features", []) if f.get("geometry")]
        if not geoms:
            print(f"  {c}: no geometry, skipped", file=sys.stderr)
            continue
        raws[c] = shapely.union_all(geoms)
        g = clean(raws[c])
        if g is None:
            print(f"  {c}: outside the frame, skipped", file=sys.stderr)
            continue
        feats.append({"type": "Feature", "properties": {"kind": "neighbour", "id": c},
                      "geometry": mapping(g)})
        print(f"  {c}: {len(json.dumps(mapping(g))) // 1024} KB")

    # the Greek LAND BORDER, for the dashed line drawn over the maps: the
    # part of the dissolved Π.Ε. outline that runs along a neighbour rather
    # than along the sea (user, 2026-08-22 — with the neighbours in white,
    # a dashed black border is what says where Greece ends). Taken from OUR
    # OWN coarse layer so the dashes hug the drawn polygons exactly; the
    # GISCO countries only say WHICH stretch of that outline is the border
    # (buffered 1 km — 1:1M generalisation drifts from Kallikratis).
    pe_fc = json.loads(PE_LAYER.read_text(encoding="utf-8"))
    gr = shapely.union_all([shape(f["geometry"]) for f in pe_fc["features"]])
    near_m = shp_transform(to_m, shapely.union_all(
        [raws[c] for c in LAND_NEIGHBOURS if c in raws])).buffer(1000, quad_segs=2)
    border_m = shp_transform(to_m, gr.boundary).intersection(near_m)
    km = border_m.length / 1000
    if not 900 < km < 1500:
        raise SystemExit(f"land border: {km:.0f} km is not Greece's (~1.180 km)")
    border = shapely.set_precision(shp_transform(to_ll, border_m), 10 ** -PRECISION)
    feats.append({"type": "Feature", "properties": {"kind": "border", "id": "GR-LAND"},
                  "geometry": mapping(border)})
    print(f"  land border: {km:.0f} km, {len(json.dumps(mapping(border))) // 1024} KB")

    a = athos(args.refresh)
    feats.append({"type": "Feature", "properties": {"kind": "athos", "id": "ATHOS"},
                  "geometry": mapping(a)})
    print(f"  Athos: {len(json.dumps(mapping(a))) // 1024} KB")

    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                              ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {OUT.stat().st_size // 1024} KB, "
          f"{len(feats)} features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
