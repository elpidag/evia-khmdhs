"""Build the Π.Ε. (regional-unit) map layers from the Kallikratis municipalities.

Greece publishes no Π.Ε. boundary file, so the Π.Ε. polygons are dissolved
from the geodata.gov.gr «Όρια Δήμων Καλλικράτη» municipality layer (CC-BY;
the untouched full-resolution EPSG:2100 shapefile lives at
data/raw/oria_dhmwn_kallikraths/, re-fetched from FireWatch's in-tree copy)
using the hand-curated municipality→Π.Ε. assignment in
khmdhs/data/greek_municipalities.json ("pe" field — see DATA_DECISIONS.md
2026-07-26).

Simplification is done with GEOS **coverage_simplify** (shapely ≥2.1 /
GEOS ≥3.12) in the metric EPSG:2100 plane: it treats the layer as a
polygonal coverage, so shared borders are simplified identically on both
sides — no slivers between neighbours, and the Π.Ε. outlines (dissolved
FROM the simplified municipalities) coincide exactly with the municipality
borders drawn on drill. Two detail levels ship:

  webui/static/greek_pe.geojson            74 Π.Ε., COARSE (country view)
  webui/static/greek_pe_hires.geojson      74 Π.Ε., FINE (drill zoom, lazy —
                                           the client renders only in-view
                                           features)
  webui/static/greek_muni_borders.geojson  74 MultiLineStrings: INTERIOR
                                           municipality borders per Π.Ε.
                                           (coastline excluded — it is
                                           already the Π.Ε. outline)
  webui/static/pe_centroids.json           {pe: [lat, lon]} representative
  khmdhs/data/pe_centroids.json            same content (Python-side copy)

Refuses to build unless the curation passes four validations: canonical
Π.Ε. keys, forest-authority anchor agreement, ΥΠΕΣ-code contiguity, and a
centroid-inside-NUTS-3 cross-check against the retired Eurostat layer.

Run with the SYSTEM python (geopandas/shapely live in the user
site-packages, not the project venv):  python3 scripts/build_pe_geojson.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / "data" / "raw" / "oria_dhmwn_kallikraths" / "oria_dhmwn_kallikraths.shp"
GAZETTEER = ROOT / "khmdhs" / "data" / "greek_municipalities.json"
AUTHORITIES = ROOT / "khmdhs" / "data" / "forest_authorities.json"
NUTS3_CANDIDATES = [ROOT / "data" / "raw" / "greek_nuts3.geojson",
                    ROOT / "webui" / "static" / "greek_nuts3.geojson"]
OUT_PE = ROOT / "webui" / "static" / "greek_pe.geojson"
OUT_PE_HIRES = ROOT / "webui" / "static" / "greek_pe_hires.geojson"
OUT_MUNI_BORDERS = ROOT / "webui" / "static" / "greek_muni_borders.geojson"
OUT_CENTROIDS = [ROOT / "webui" / "static" / "pe_centroids.json",
                 ROOT / "khmdhs" / "data" / "pe_centroids.json"]

# ~2 px error at the deepest drill zoom (Πειραιώς ≈ 15 m/px) vs the km-scale
# blockiness of the per-feature-simplified FireWatch conversion.
FINE_TOL_M = 30.0
COARSE_TOL_M = 220.0  # country view: light payload, invisible at that scale

# Alias spellings tolerated in inputs; outputs always use the canonical key.
CANON_ALIASES = {
    "Π.Ε. Αχαίας": "Π.Ε. Αχαΐας", "Π.Ε. Εύβοιας": "Π.Ε. Ευβοίας",
    "Π.Ε. Κεφαλονιάς": "Π.Ε. Κεφαλληνίας", "Π.Ε. Λαρίσης": "Π.Ε. Λάρισας",
    "Π.Ε. Πρεβέζης": "Π.Ε. Πρέβεζας", "Π.Ε. Ρεθύμνης": "Π.Ε. Ρεθύμνου",
}


def canon(pe: str) -> str:
    return CANON_ALIASES.get(pe, pe)


def _point_in_ring(lon: float, lat: float, ring) -> bool:
    n, j, ok = len(ring), len(ring) - 1, False
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            ok = not ok
        j = i
    return ok


def validate(gaz: dict) -> None:
    sys.path.insert(0, str(ROOT))
    from khmdhs.greek_regions import REGIONAL_UNITS, nuts3_for

    errs: list[str] = []
    canonical_keys = set(REGIONAL_UNITS) - set(CANON_ALIASES)
    for code, m in gaz.items():
        if m.get("pe") not in canonical_keys:
            errs.append(f"non-canonical pe on {code} {m['name']}: {m.get('pe')!r}")

    fa = json.loads(AUTHORITIES.read_text())
    for name, a in fa["authorities"].items():
        code, pe = a.get("municipality_code"), a.get("region_pe")
        if code and pe and canon(gaz[code]["pe"]) != canon(pe):
            errs.append(f"anchor mismatch {name}: gazetteer {gaz[code]['pe']} vs registry {pe}")

    runs, last = [], None
    for code in sorted(gaz, key=int):
        pe = gaz[code]["pe"]
        if pe != last:
            runs.append(pe)
            last = pe
    for pe in {p for p in runs if runs.count(p) > 1}:
        errs.append(f"ΥΠΕΣ codes for {pe} are not contiguous")

    nuts_path = next((p for p in NUTS3_CANDIDATES if p.exists()), None)
    if nuts_path is None:
        print("WARN: greek_nuts3.geojson not found — skipping cross-check 4")
    else:
        polys: dict[str, list] = {}
        for f in json.loads(nuts_path.read_text())["features"]:
            g = f["geometry"]
            parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            polys[f["properties"]["NUTS_ID"]] = [p[0] for p in parts]
        for code, m in gaz.items():
            rings = polys.get(nuts3_for(m["pe"]) or "")
            if not rings:
                errs.append(f"no NUTS-3 polygon for {m['pe']} ({code})")
                continue
            if any(_point_in_ring(m["lon"], m["lat"], r) for r in rings):
                continue
            clat = math.cos(math.radians(m["lat"]))
            d = min(math.hypot((m["lon"] - x) * clat, m["lat"] - y)
                    for r in rings for x, y in r) * 111.0
            if d > 2.0:
                errs.append(f"{code} {m['name']} centroid {d:.1f} km outside "
                            f"NUTS-3 of {m['pe']}")
    if errs:
        for e in errs:
            print("ERROR:", e)
        raise SystemExit(2)
    print(f"validation OK: {len(gaz)} municipalities, "
          f"{len({m['pe'] for m in gaz.values()})} Π.Ε.")


def _round_coords(obj, nd=5):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, (list, tuple)):
        return [_round_coords(x, nd) for x in obj]
    return obj


def main() -> None:
    try:
        import geopandas as gpd
        import shapely
        from shapely.geometry import MultiPolygon, Polygon
    except ImportError:
        raise SystemExit("geopandas/shapely required — run with the system "
                         "python3, not the project venv")
    if not hasattr(shapely, "coverage_simplify"):
        raise SystemExit("shapely.coverage_simplify missing (needs shapely "
                         "≥2.1 on GEOS ≥3.12)")

    gaz = json.loads(GAZETTEER.read_text())
    validate(gaz)

    gdf = gpd.read_file(SHP, encoding="cp1253")
    assert gdf.crs is not None and gdf.crs.to_epsg() == 2100, gdf.crs
    gdf = gdf[gdf["KWD_YPES"].notna() & (gdf["KWD_YPES"].str.strip() != "")]
    gdf["code"] = gdf["KWD_YPES"].str.strip()
    assert len(gdf) == len(gaz), (len(gdf), len(gaz))
    gdf["pe"] = gdf["code"].map(lambda c: gaz[c]["pe"])
    assert not gdf["pe"].isna().any()

    # Metric plane: heal invalidity, snap to a 10 cm grid so near-miss
    # borders become exact, then simplify as a COVERAGE — shared edges are
    # kept identical on both sides (no slivers, municipality borders match
    # the dissolved Π.Ε. outlines exactly).
    geoms = shapely.make_valid(gdf.geometry.values)
    geoms = shapely.set_precision(geoms, 0.1)
    area_before = shapely.area(geoms).sum()

    fine = shapely.coverage_simplify(geoms, FINE_TOL_M)
    area_fine = shapely.area(shapely.make_valid(fine)).sum()
    drift = abs(area_fine - area_before) / area_before
    assert drift < 0.005, f"fine simplification moved {drift:.2%} of total area"

    def drop_holes(geom):
        # After an exact-coverage dissolve holes should not exist; drop any
        # residual micro-holes (no Π.Ε. legitimately contains an enclave).
        if isinstance(geom, Polygon):
            return Polygon(geom.exterior)
        if isinstance(geom, MultiPolygon):
            return MultiPolygon([Polygon(p.exterior) for p in geom.geoms])
        return geom

    def dissolve_by_pe(gdf2100):
        out = gdf2100.dissolve(by="pe")
        out.geometry = [drop_holes(shapely.make_valid(g)) for g in out.geometry]
        return out

    def to_features(gdf2100, props_of):
        wgs = gdf2100.to_crs(4326)
        feats = []
        for key, row in wgs.iterrows():
            feats.append({
                "type": "Feature",
                "properties": props_of(key, row),
                "geometry": _round_coords(
                    json.loads(gpd.GeoSeries([row.geometry]).to_json())
                    ["features"][0]["geometry"]),
            })
        return {"type": "FeatureCollection", "features": feats}

    def write(path, fc):
        path.write_text(json.dumps(fc, ensure_ascii=False,
                                   separators=(",", ":")) + "\n")
        print(f"wrote {path.name}: {len(fc['features'])} features, "
              f"{path.stat().st_size // 1024} KB")

    muni_fine = gdf.copy()
    muni_fine.geometry = fine

    # --- FINE Π.Ε. layer (drill zoom, lazy-loaded) ------------------------
    pe_fine = dissolve_by_pe(muni_fine[["pe", "geometry"]])
    write(OUT_PE_HIRES, to_features(
        pe_fine, lambda pe, _row: {"pe": pe, "name": pe.removeprefix("Π.Ε. ")}))

    # --- interior municipality borders per Π.Ε. (drill overlay) -----------
    # Only the borders BETWEEN municipalities: the coastline and the Π.Ε.
    # outline are already drawn by the hires layer, and duplicating the
    # (huge) coastline linework would triple the payload. Exact vertex
    # sharing (snapped coverage) makes the boundary difference clean.
    border_rows = []
    for pe, row in pe_fine.iterrows():
        members = muni_fine[muni_fine["pe"] == pe].geometry.values
        if len(members) < 2:
            continue   # single-municipality Π.Ε. has no interior borders
        lines = shapely.union_all(shapely.boundary(members))
        interior = shapely.difference(
            shapely.set_precision(lines, 0.1),
            shapely.set_precision(shapely.boundary(row.geometry), 0.1))
        if not interior.is_empty:
            border_rows.append({"pe": pe, "geometry": interior})
    borders = gpd.GeoDataFrame(border_rows, crs=2100).set_index("pe")
    write(OUT_MUNI_BORDERS, to_features(
        borders, lambda pe, _row: {"pe": pe}))

    # Representative points from the fine dissolve.
    pe_fine_wgs = pe_fine.to_crs(4326)
    centroids = {pe: [round(row.geometry.representative_point().y, 5),
                      round(row.geometry.representative_point().x, 5)]
                 for pe, row in pe_fine_wgs.iterrows()}
    for path in OUT_CENTROIDS:
        path.write_text(json.dumps(centroids, ensure_ascii=False, indent=1,
                                   sort_keys=True) + "\n")
    print(f"wrote pe_centroids.json: {len(centroids)} entries")

    # --- COARSE Π.Ε. layer (country view, loaded eagerly) -----------------
    # Simplify the dissolved 74-polygon coverage further; shared Π.Ε.
    # borders again stay coincident.
    coarse_geoms = shapely.coverage_simplify(pe_fine.geometry.values, COARSE_TOL_M)
    pe_coarse = pe_fine.copy()
    pe_coarse.geometry = [drop_holes(shapely.make_valid(g)) for g in coarse_geoms]
    write(OUT_PE, to_features(
        pe_coarse, lambda pe, _row: {"pe": pe, "name": pe.removeprefix("Π.Ε. ")}))


if __name__ == "__main__":
    main()
