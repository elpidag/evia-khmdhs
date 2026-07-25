"""Build the committed municipality gazetteer from the Kallikratis layer.

Source: geodata.gov.gr open dataset «Όρια Δήμων Καλλικράτη»
(oria_dhmwn_kallikraths, CC-BY, ΥΠΕΣ codes KWD_YPES 9001–9325) — the same
ground truth and join key the FireWatch project uses. We keep only a
representative centroid per municipality (no polygons are committed).

Usage:
  python scripts/build_municipalities.py                 # try the WFS portal
  python scripts/build_municipalities.py <path.geojson>  # local WGS84 GeoJSON
                                                         # (features must carry
                                                         # name + municipality
                                                         # code properties)

The portal is frequently offline; the 2026-07-25 build used the FireWatch
repo's in-tree copy of the identical shapefile, reprojected to WGS84 (see
DATA_DECISIONS.md). Pure stdlib — no GDAL/geopandas required.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "khmdhs" / "data" / "greek_municipalities.json"
WFS_URL = (
    "https://geodata.gov.gr/geoserver/ows?service=WFS&version=2.0.0"
    "&request=GetFeature&typeName=geodata.gov.gr:oria_dhmwn_kallikraths"
    "&outputFormat=application/json&srsName=EPSG:4326"
)


def _rings(geom: dict) -> list[list[list[float]]]:
    """Outer rings of a (Multi)Polygon as [[ [lon,lat], ... ], ...]."""
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        return [poly[0] for poly in geom["coordinates"]]
    raise ValueError(f"unsupported geometry {geom['type']}")


def _ring_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Planar shoelace (area, centroid) with lon scaled by cos(mean lat)."""
    mean_lat = sum(p[1] for p in ring) / len(ring)
    k = math.cos(math.radians(mean_lat))
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        x1, x2 = x1 * k, x2 * k
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(a) < 1e-12:
        return 0.0, ring[0][0], ring[0][1]
    a *= 0.5
    return abs(a), cx / (6 * a) / k, cy / (6 * a)


def _inside(ring: list[list[float]], lon: float, lat: float) -> bool:
    ok = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            ok = not ok
    return ok


def representative_point(geom: dict) -> tuple[float, float]:
    """Centroid of the largest outer ring; if it falls outside (concave or
    coastal shapes), pick the inside point of a coarse grid nearest to it."""
    ring = max(_rings(geom), key=lambda r: _ring_area_centroid(r)[0])
    _, lon, lat = _ring_area_centroid(ring)
    if _inside(ring, lon, lat):
        return lat, lon
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    best, best_d = None, None
    steps = 24
    for i in range(1, steps):
        for j in range(1, steps):
            gx = min(xs) + (max(xs) - min(xs)) * i / steps
            gy = min(ys) + (max(ys) - min(ys)) * j / steps
            if _inside(ring, gx, gy):
                d = (gx - lon) ** 2 + (gy - lat) ** 2
                if best_d is None or d < best_d:
                    best, best_d = (gy, gx), d
    return best if best else (lat, lon)


def _feature_props(props: dict) -> tuple[str | None, str | None]:
    """(code, name) from either the raw portal fields or derived files."""
    code = props.get("KWD_YPES") or props.get("municipality_code") or props.get("code")
    name = props.get("NAME") or props.get("name")
    if code is not None:
        code = str(code).strip()
        if code.endswith(".0"):
            code = code[:-2]
    return (code or None), (name or None)


def load_features(source: str | None) -> list[dict]:
    if source:
        with open(source, encoding="utf-8") as f:
            return json.load(f)["features"]
    import requests

    r = requests.get(WFS_URL, timeout=120,
                     headers={"User-Agent": "evia-khmdhs OSINT gazetteer build"})
    r.raise_for_status()
    return r.json()["features"]


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else None
    feats = load_features(source)
    out: dict[str, dict] = {}
    skipped = []
    for f in feats:
        code, name = _feature_props(f.get("properties") or {})
        if not code or not code.isdigit():
            skipped.append(name)
            continue
        lat, lon = representative_point(f["geometry"])
        out[code] = {"name": name, "lat": round(lat, 5), "lon": round(lon, 5)}
    body = json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=2)
    OUT.write_text(body + "\n", encoding="utf-8")
    print(f"{len(out)} municipalities -> {OUT}")
    if skipped:
        print(f"skipped (no ΥΠΕΣ code): {', '.join(str(s) for s in skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
