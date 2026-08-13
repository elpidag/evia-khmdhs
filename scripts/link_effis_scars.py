# -*- coding: utf-8 -*-
"""Link each anadohoi project to its EFFIS burn scar(s).

Semantics (DATA_DECISIONS 2026-08-13): candidate scars are the RAW EFFIS
features whose initialdat year matches the project's fire_event year(s);
a scar links when it CONTAINS one of the project's anchors (coordinated
work_sites; zone centroids for the Εύβοια zone projects) or lies ≤ NEAR_KM
from one. Anchor-less regional projects link via the hand-reviewed
REGIONAL table (scar admin-name + year). «εκτός πυρκαγιάς» projects link
nothing. Results land in anadohoi_projects.json as `effis_scars`
[{id, yr, ha, name, basis, km}] and a full per-project report is printed
for review. Needs shapely + pyproj (run with SYSTEM python3).

Run: python3 scripts/link_effis_scars.py [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/BurtScars_EFFIS_2008-2025.geojson"
PROJECTS = ROOT / "khmdhs/data/anadohoi_projects.json"
ZONES = ROOT / "data/processed/evia_works_zones.geojson"

NEAR_KM = 2.0

# region-year fallback (anchor-less regional projects, plus projects whose
# only anchors are municipality centroids too far from the scar) →
# (scar admin-name substring, year). Keeps scars ≥ REGION_MIN_HA — the
# named disaster, not every small homonymous-region fire of that year.
REGIONAL = {
    "964Ρ4653Π8-ΨΘΗ": ("Χίος", 2025),          # νήσος Χίος (two 2025 fires)
    "6ΩΜ04653Π8-31Ι": ("Ρόδος", 2023),          # Ρόδος Ζώνη 4
    "971Χ4653Π8-222": ("Ρόδος", 2023),          # Ρόδος Ζώνη 5
    "ΨΧΟ24653Π8-82Χ": ("Εύβοια", 2021),         # Β. Εύβοια region μελέτη
    "ΨΦΠ24653Π8-5Θ3": ("Έβρος", 2023),          # Έβρος region μελέτη
    "Ρ5ΖΦ4653Π8-ΥΕ8": ("Κορινθία", 2025),       # Φενεός — Δ.Ε. centroids far
}
REGION_MIN_HA = 500


def main() -> None:
    dry = "--dry-run" in sys.argv
    to3035 = Transformer.from_crs(4326, 3035, always_xy=True)

    raw = json.loads(RAW.read_text(encoding="utf-8"))
    scars = []
    for f in raw["features"]:
        p = f["properties"]
        yr = int(str(p.get("initialdat", "0"))[:4] or 0)
        if not yr:
            continue
        scars.append({
            "id": int(p["id"]), "yr": yr,
            "ha": round(float(p.get("area_ha") or 0)),
            "name": str(p.get("admlvl3") or p.get("admlvl2") or "")
                    .replace("\xa0", " ").strip(),
            "geom": shape(f["geometry"]),
        })
    by_year = {}
    for s in scars:
        by_year.setdefault(s["yr"], []).append(s)

    zone_cent = {}
    if ZONES.exists():
        zj = json.loads(ZONES.read_text(encoding="utf-8"))
        for f in zj["features"]:
            zone_cent[f["properties"]["zone"]] = f["properties"]["centroid"]

    data = json.loads(PROJECTS.read_text(encoding="utf-8"))
    n_linked = n_empty = 0
    for p in data["projects"]:
        root = p["root_ada"]
        fire = p.get("fire_event") or ""
        years = sorted({int(y) for y in re.findall(r"20\d\d", fire)})
        if not years or "εκτός" in fire:
            p.pop("effis_scars", None)
            print(f"{root[:4]} | {fire or '—':<40} | skipped (no fire year)")
            continue

        anchors = []          # (label, Point in 3035)
        for s in p.get("work_sites") or []:
            if s.get("lat") is not None:
                anchors.append((s["name"][:24],
                                Point(*to3035.transform(s["lon"], s["lat"]))))
        for z in p.get("works_zones") or []:
            c = zone_cent.get(z)
            if c:
                anchors.append((f"zone:{z}",
                                Point(*to3035.transform(c[0], c[1]))))

        links = {}
        if anchors:
            for yr in years:
                for s in by_year.get(yr, []):
                    best = None
                    for label, pt in anchors:
                        d_km = s["geom"].distance(pt) / 1000.0
                        if best is None or d_km < best[1]:
                            best = (label, d_km)
                    if best and best[1] <= NEAR_KM:
                        basis = "contains" if best[1] == 0 else "near"
                        links[s["id"]] = {
                            "id": s["id"], "yr": s["yr"], "ha": s["ha"],
                            "name": s["name"], "basis": basis,
                            "km": round(best[1], 2),
                        }
        if not links and root in REGIONAL:
            sub, yr = REGIONAL[root]
            for s in by_year.get(yr, []):
                if sub in s["name"] and s["ha"] >= REGION_MIN_HA:
                    links[s["id"]] = {
                        "id": s["id"], "yr": s["yr"], "ha": s["ha"],
                        "name": s["name"], "basis": "region-year", "km": None,
                    }

        out = sorted(links.values(), key=lambda x: -x["ha"])
        if out:
            p["effis_scars"] = out
            n_linked += 1
        else:
            p.pop("effis_scars", None)
            n_empty += 1
        def fmt(x):
            km = "" if x["km"] is None else f",{x['km']}km"
            return f"{x['id']}({x['yr']},{x['ha']}ha,{x['basis']}{km})"
        det = ", ".join(fmt(x) for x in out) or "NO MATCH"
        print(f"{root[:4]} | {fire[:38]:<38} | anchors={len(anchors):>2} | {det}")

    print(f"\nlinked: {n_linked}  no-match/empty: {n_empty}")
    if not dry:
        PROJECTS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        print("wrote", PROJECTS)


if __name__ == "__main__":
    main()
