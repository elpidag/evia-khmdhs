# -*- coding: utf-8 -*-
"""Build the display copy of the EFFIS burnt-scars layer.

data/raw/BurtScars_EFFIS_2008-2025.geojson (Copernicus EMS EFFIS export,
EPSG:3035, 1,969 features — provenance in DATA_DECISIONS 2026-08-13) is
reprojected to WGS84, simplified (in metres, before reprojection), rings
oriented CLOCKWISE for d3-geo's spherical winding, and trimmed to the
properties the map needs: year, hectares, admin name. Output goes to
data/processed/ and is duplicated into atlas/static/geo/ like the other
map layers. Display REQUIRES the attribution «© European Union,
Copernicus Emergency Management Service — EFFIS».

Needs: pyproj, shapely. Run: python scripts/build_effis_layer.py
"""
import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/BurtScars_EFFIS_2008-2025.geojson"
OUT = ROOT / "data/processed/effis_fires.geojson"
OUT_ATLAS = ROOT / "atlas/static/geo/effis_fires.geojson"

SIMPLIFY_M = 120  # metres, in the source LAEA projection


def cw(geom):
    """exterior rings clockwise — d3-geo inverts CCW spherical polygons"""
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    return MultiPolygon([orient(g, sign=-1.0) for g in geom.geoms])


def main() -> None:
    fc = json.loads(RAW.read_text(encoding="utf-8"))
    tr = Transformer.from_crs(3035, 4326, always_xy=True)
    feats = []
    skipped = 0
    for f in fc["features"]:
        props = f["properties"]
        year = int(str(props.get("initialdat", "0"))[:4] or 0)
        if not year:
            skipped += 1
            continue
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = geom.simplify(SIMPLIFY_M, preserve_topology=True)
        if geom.is_empty:
            skipped += 1
            continue
        wgs = shp_transform(lambda x, y: tr.transform(x, y), geom)
        if not isinstance(wgs, (Polygon, MultiPolygon)):
            skipped += 1
            continue
        feats.append({
            "type": "Feature",
            "properties": {
                # stable EFFIS feature id — the anadohoi effis_scars
                # links resolve against it
                "id": int(props["id"]),
                "yr": year,
                "ha": round(float(props.get("area_ha") or 0)),
                # admin name, NBSP noise stripped
                "name": str(props.get("admlvl3") or props.get("admlvl2") or "").replace("\xa0", " ").strip(),
            },
            "geometry": mapping(cw(wgs)),
        })
    payload = json.dumps(
        {"type": "FeatureCollection",
         "attribution": "© European Union, Copernicus Emergency Management Service — EFFIS",
         "features": feats},
        ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(payload, encoding="utf-8")
    OUT_ATLAS.write_text(payload, encoding="utf-8")
    years = sorted({f["properties"]["yr"] for f in feats})
    print(f"{len(feats)} fires ({skipped} skipped), years {years[0]}–{years[-1]}, "
          f"{len(payload) / 1e6:.1f} MB → {OUT.relative_to(ROOT)} + atlas/static/geo/")


if __name__ == "__main__":
    main()
