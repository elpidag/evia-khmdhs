# -*- coding: utf-8 -*-
"""Build data/processed/evia_works_zones.geojson from the curated digitised
zones (khmdhs/data/evia_works_zones_digitised.json).

The curated file holds the hand-corrected zone polygons of the Β. Εύβοια
Master-Plan works maps (sheets 4.1 Λίμνης / 4.2 Ιστιαίας) in each sheet's
full-resolution pixel space. This script georeferences them through the
sheets' ΕΓΣΑ87 grid (anchors + 721.75 px per 5 km, verified against the
printed grid to ±1 px), clips to the Εύβοια coastline (the Kallikratis
high-res Π.Ε. layer), converts to WGS84 and writes a FeatureCollection
with per-zone provenance and area validation against the sheets' tables.

Needs: pyproj, shapely (pip install pyproj shapely).
Run:   python scripts/build_evia_zones.py
"""
import json
from pathlib import Path

import numpy as np
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import transform as shp_transform
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "khmdhs/data/evia_works_zones_digitised.json"
PE_HIRES = ROOT / "webui/static/greek_pe_hires.geojson"
OUT = ROOT / "data/processed/evia_works_zones.geojson"
# duplicated into the Atlas static assets, like the Π.Ε. layers
OUT_ATLAS = ROOT / "atlas/static/geo/evia_works_zones.geojson"


def main() -> None:
    cur = json.loads(CURATED.read_text(encoding="utf-8"))
    step = cur["georef"]["px_per_5km"]
    anchors = cur["georef"]["anchors"]
    meta = cur["zones_meta"]

    tr = Transformer.from_crs(2100, 4326, always_xy=True)
    tr_inv = Transformer.from_crs(4326, 2100, always_xy=True)
    pe = json.loads(PE_HIRES.read_text(encoding="utf-8"))
    evia = unary_union([
        shape(f["geometry"]) for f in pe["features"]
        if "Ευβοίας" in json.dumps(f["properties"], ensure_ascii=False)])
    evia_2100 = shp_transform(lambda x, y: tr_inv.transform(x, y), evia).buffer(150)

    features = []
    for sheet_tag, zones in cur["sheets"].items():
        a = anchors[sheet_tag]
        for zone, parts in zones.items():
            polys = []
            for pts in parts:
                pts = np.asarray(pts, float)
                east = a["ax_val"] + (pts[:, 0] - a["ax"]) * 5000 / step
                north = a["ay_val"] - (pts[:, 1] - a["ay"]) * 5000 / step
                p = Polygon(np.column_stack([east, north]))
                if not p.is_valid:
                    p = p.buffer(0)
                if p.is_empty:
                    continue
                polys.extend(p.geoms if isinstance(p, MultiPolygon) else [p])
            if not polys:
                print(f"{zone:13} — no geometry, skipped")
                continue
            geom = unary_union(polys).intersection(evia_2100)
            if geom.is_empty:
                continue
            area_str = geom.area / 1000.0

            def to_wgs(g):
                if isinstance(g, Polygon):
                    ext = [tr.transform(x, y) for x, y in g.exterior.coords]
                    ints = [[tr.transform(x, y) for x, y in r.coords]
                            for r in g.interiors]
                    return Polygon(ext, ints)
                return MultiPolygon([to_wgs(gg) for gg in g.geoms])

            wgs = to_wgs(geom).simplify(0.00015, preserve_topology=True)
            rep = wgs.representative_point()
            m = meta[zone]
            features.append({
                "type": "Feature",
                "properties": {
                    "zone": zone,
                    "name": m["name"],
                    "basin": m["basin"],
                    "sheet": cur["source_sheets"][sheet_tag],
                    "table_stremmata": m["table_stremmata"],
                    "extracted_stremmata": round(area_str),
                    "centroid": [round(rep.x, 5), round(rep.y, 5)],
                    "digitised": cur["digitised"],
                },
                "geometry": mapping(wgs),
            })
            print(f"{zone:13} {area_str:9.0f} στρ. "
                  f"(table {m['table_stremmata']:9.0f}, "
                  f"{area_str / m['table_stremmata'] * 100:5.1f}%)")

    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         ensure_ascii=False)
    OUT.write_text(payload, encoding="utf-8")
    OUT_ATLAS.write_text(payload, encoding="utf-8")
    print(f"→ {OUT.relative_to(ROOT)} + {OUT_ATLAS.relative_to(ROOT)} "
          f"({len(features)} zones)")


if __name__ == "__main__":
    main()
