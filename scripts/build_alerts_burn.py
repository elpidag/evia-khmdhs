#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The burnt ground of August 2021, day by day, for the story's Figure 04
(DATA_DECISIONS 2026-09-02): NASA VIIRS/NPP VNP64A1 burned area, Collection
2 (500 m, sinusoidal tile h19v05, the August 2021 product), read from the
raw HDF4 tile under data/raw/burned_area/ — the same product the sibling
implementation drew — and written as ONE GeoJSON of daily INCREMENTS: for
every day 1–23 August, the pixels whose product burn date is that day,
dissolved, simplified (150 m), reprojected to WGS84, clipped to the figure's
frame and to Greek land, rings clockwise for d3-geo. The client draws the
increments up to the clock's day, so the union appears without duplicating
geometry across days.

Coverage caveat (say it wherever the layer shows): tile h19v05 ends at
40.0 °N and ~25.6 °E — every mainland fire region of the alerts is inside,
Rhodes and Grevena are NOT (a second tile, h20v05, would add Rhodes).

Attribution: NASA VIIRS VNP64A1 v002 burned area — NASA EOSDIS Land
Processes DAAC; satellite estimates at 500 m, not official οριοθετήσεις.

Run with SYSTEM python3 (pyhdf, numpy, rasterio, shapely, pyproj):
    python3 scripts/build_alerts_burn.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import numpy as np
import rasterio.features
import shapely
from pyhdf.SD import SD, SDC
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform as shp_transform
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
HDF = ROOT / "data/raw/burned_area/VNP64A1.A2021213.h19v05.002.2023198172838.hdf"
PE = ROOT / "webui/static/greek_pe.geojson"
OUT = ROOT / "data/processed/alerts_burn_2021.geojson"
SITE = ROOT / "atlas/static/geo/alerts_burn_2021.geojson"

# the figure's frame box (atlas/src/lib/transforms/alertsFrame.ts)
BOX = (19.5, 34.7, 28.6, 41.8)
YEAR = 2021
DOY0, DOY1 = 213, 235                    # 1–23 August 2021

# the MODIS/VIIRS sinusoidal grid: 18 × 18 tiles of 2400 × 2400 pixels
TILE_H, TILE_V, N = 19, 5, 2400
TILE_M = 20015109.354 / 18               # 1 111 950.52 m
PX_M = TILE_M / N                        # 463.3127 m
UL_X, UL_Y = (TILE_H - 18) * TILE_M, (9 - TILE_V) * TILE_M
SINU = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext +units=m +no_defs"
SIMPLIFY_M = 150.0
LAND_BUFFER_DEG = 0.01

ATTRIBUTION = ("NASA VIIRS/NPP VNP64A1 v002 burned area (500 m, tile h19v05, "
               "August 2021), courtesy of NASA EOSDIS LP DAAC — satellite "
               "estimates, not official οριοθετήσεις; mainland tile only, "
               "Rhodes and Grevena not covered")


def read_burn_dates() -> np.ndarray:
    sd = SD(str(HDF), SDC.READ)
    meta = sd.attributes().get("StructMetadata.0", "")
    m = re.search(r"UpperLeftPointMtrs=\(([-\d.]+),([-\d.]+)\)", meta)
    if m:
        ulx, uly = float(m.group(1)), float(m.group(2))
        assert abs(ulx - UL_X) < 1 and abs(uly - UL_Y) < 1, (ulx, uly, UL_X, UL_Y)
    bd = sd.select("Burn Date")[:]
    assert bd.shape == (N, N), bd.shape
    return np.asarray(bd, dtype=np.int32)


def greek_land() -> shapely.Geometry:
    fc = json.loads(PE.read_text(encoding="utf-8"))
    land = unary_union([shape(f["geometry"]) for f in fc["features"]])
    return land.buffer(LAND_BUFFER_DEG)


def orient_cw(geom):
    """exterior rings clockwise — d3-geo inverts CCW spherical polygons
    (the build_effis_layer.py rule)"""
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    if isinstance(geom, MultiPolygon):
        return MultiPolygon([orient(g, sign=-1.0) for g in geom.geoms])
    raise TypeError(geom.geom_type)


def rounded(coords, nd=5):
    if isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (int, float)):
        return [round(float(c), nd) for c in coords]
    return [rounded(c, nd) for c in coords]


def main() -> None:
    bd = read_burn_dates()
    affine = from_origin(UL_X, UL_Y, PX_M, PX_M)
    to_wgs = Transformer.from_crs(SINU, "EPSG:4326", always_xy=True)
    clip = box(*BOX).intersection(greek_land())
    features = []
    rows = []
    cum_px = 0
    for doy in range(DOY0, DOY1 + 1):
        day_mask = bd == doy
        if not day_mask.any():
            continue
        shapes = rasterio.features.shapes(day_mask.astype("uint8"), mask=day_mask,
                                          transform=affine)
        geom = unary_union([shape(g) for g, _ in shapes])
        geom = geom.simplify(SIMPLIFY_M, preserve_topology=True)
        geom = shp_transform(to_wgs.transform, geom)
        geom = geom.intersection(clip)
        # only polygonal parts survive a clip
        if geom.geom_type == "GeometryCollection":
            geom = unary_union([g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")])
        if geom.is_empty:
            continue
        # the pixels of the day whose centres fall inside the clip
        rows_i, cols_i = np.nonzero(day_mask)
        cx = UL_X + (cols_i + 0.5) * PX_M
        cy = UL_Y - (rows_i + 0.5) * PX_M
        lon, lat = to_wgs.transform(cx, cy)
        inside = shapely.contains_xy(clip, lon, lat)
        px = int(inside.sum())
        if px == 0:
            continue
        km2 = round(px * PX_M * PX_M / 1e6, 1)
        cum_px += px
        day = (dt.date(YEAR, 1, 1) + dt.timedelta(days=doy - 1)).isoformat()
        g = mapping(orient_cw(geom))
        g["coordinates"] = rounded(g["coordinates"])
        features.append({"type": "Feature",
                         "properties": {"day": day, "doy": doy, "px": px, "km2": km2},
                         "geometry": g})
        rows.append((day, doy, px, km2, round(cum_px * PX_M * PX_M / 1e6, 1)))
    fc = {"type": "FeatureCollection",
          "attribution": ATTRIBUTION,
          "source": {"product": "VNP64A1.002", "tile": "h19v05",
                     "file": HDF.name, "pixel_m": round(PX_M, 4),
                     "days": [DOY0, DOY1], "year": YEAR,
                     "clip": "frame box ∩ Greek land (webui/static/greek_pe.geojson, "
                             f"buffered {LAND_BUFFER_DEG}°)",
                     "simplify_m": SIMPLIFY_M, "winding": "exterior rings clockwise"},
          "features": features}
    data = json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n"
    OUT.write_text(data, encoding="utf-8")
    SITE.write_text(data, encoding="utf-8")
    print(f"{'day':10s} {'doy':>3s} {'pixels':>6s} {'km²':>7s} {'cum km²':>8s}")
    for day, doy, px, km2, cum in rows:
        print(f"{day:10s} {doy:3d} {px:6d} {km2:7.1f} {cum:8.1f}")
    print(f"{len(features)} days with burnt ground; {cum_px} pixels; "
          f"{OUT.stat().st_size / 1024:.0f} KB → {OUT.relative_to(ROOT)} + {SITE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
