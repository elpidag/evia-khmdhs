"""Build the municipality POLYGON layer the contract maps outline.

The Π.Ε. layers are built from the Kallikratis shapefile by
`scripts/build_pe_geojson.py`, which needs geopandas and a shapely with
GEOS `coverage_simplify`. Neither is needed here: the two committed
artefacts already contain the municipality geometry between them —

  * `greek_pe_hires.geojson`      the Π.Ε. outlines at 30 m, topologically
                                  clean (shared edges identical);
  * `greek_muni_borders.geojson`  the INTERIOR municipality borders of each
                                  Π.Ε., built from the same snapped
                                  coverage, so their vertices coincide with
                                  the outline's.

Polygonising a Π.Ε.'s outline together with its interior borders therefore
reproduces its municipalities exactly, with no new source data and no
sliver risk. Each polygon is named by the ΥΠΕΣ representative point that
falls inside it (`greek_municipalities.json`), and the few parts holding no
representative point — the islands of a mainland δήμος — go to the nearest
one within the same Π.Ε.

Output: `greek_muni.geojson` in BOTH static dirs (webui and atlas), like
the other geo layers. It is fetched lazily, and only by the contract pages
that outline a δήμος.

    .venv/Scripts/python -m scripts.build_muni_polygons
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import shapely
from shapely.geometry import shape, mapping
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PE_HIRES = ROOT / "webui" / "static" / "greek_pe_hires.geojson"
BORDERS = ROOT / "webui" / "static" / "greek_muni_borders.geojson"
GAZETTEER = ROOT / "khmdhs" / "data" / "greek_municipalities.json"
OUT = ROOT / "webui" / "static" / "greek_muni.geojson"
OUT2 = ROOT / "atlas" / "static" / "geo" / "greek_muni.geojson"

# ~250 m in degrees, and coordinates rounded to 4 decimals (~11 m). The
# layer is drawn inside ONE regional unit on a ~460 px detail map: a whole
# Π.Ε. is ~100 km across there, so 250 m is about one pixel. Full precision
# cost 2 MB for a lazily-loaded file nobody can see the difference in.
TOL = 0.0027
PRECISION = 4


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def main() -> int:
    pe_feats = load(PE_HIRES)
    border_feats = load(BORDERS)
    raw = json.loads(GAZETTEER.read_text(encoding="utf-8"))
    gaz = raw.get("municipalities", raw)

    borders_by_pe: dict[str, list] = {}
    for f in border_feats:
        borders_by_pe.setdefault(f["properties"]["pe"], []).append(shape(f["geometry"]))

    # representative points, grouped by Π.Ε. so a lookup never crosses one
    points: dict[str, list[tuple[str, dict, shapely.Point]]] = {}
    for code, m in gaz.items():
        lat, lon = m["lat"], m["lon"]
        points.setdefault(m["pe"], []).append((code, m, shapely.Point(lon, lat)))

    out: list[dict] = []
    unassigned = 0
    for f in pe_feats:
        pe = f["properties"]["pe"]
        outline = shape(f["geometry"])
        lines = [shapely.boundary(outline)] + borders_by_pe.get(pe, [])
        parts = list(polygonize(unary_union(lines)))
        if not parts:
            parts = [outline]
        here = points.get(pe, [])
        claimed: dict[str, list] = {}
        leftovers = []
        for poly in parts:
            hit = next((c for c, _m, p in here if poly.contains(p)), None)
            if hit is None:
                leftovers.append(poly)
            else:
                claimed.setdefault(hit, []).append(poly)
        for poly in leftovers:                 # islands of a mainland δήμος
            if not here:
                unassigned += 1
                continue
            code = min(here, key=lambda t: poly.distance(t[2]))[0]
            claimed.setdefault(code, []).append(poly)
        for code, polys in claimed.items():
            geom = unary_union(polys)
            geom = shapely.simplify(geom, TOL, preserve_topology=True)
            geom = shapely.set_precision(geom, 10 ** -PRECISION)
            if geom.is_empty:
                continue
            out.append({
                "type": "Feature",
                "properties": {"code": code, "name": gaz[code]["name"], "pe": pe},
                "geometry": mapping(geom),
            })

    fc = {"type": "FeatureCollection", "features": out}
    body = json.dumps(fc, ensure_ascii=False, separators=(",", ":"))
    for path in (OUT, OUT2):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    covered = {f["properties"]["code"] for f in out}
    print(f"{len(out)} municipality polygons over {len(covered)} of {len(gaz)} δήμοι "
          f"({len(body) / 1024:.0f} KB)")
    if unassigned:
        print(f"  {unassigned} polygon(s) fell in a Π.Ε. with no representative point")
    missing = sorted(set(gaz) - covered)
    if missing:
        print(f"  no polygon for {len(missing)} δήμοι: "
              f"{', '.join(gaz[c]['name'] for c in missing[:6])}"
              f"{' …' if len(missing) > 6 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
