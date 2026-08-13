"""Geocode the curated anadohoi work sites (θέση-level) via Nominatim.

Reads khmdhs/data/anadohoi_projects.json, geocodes every work_sites entry
that has no lat/lon yet, and writes verified coordinates BACK into the
curated file (single source of truth). Tiers per site, first VALIDATED
hit wins (DATA_DECISIONS 2026-08-13):

  1. «<θέση>, <δήμος>» Greek, then transliterated      -> geo_precision site
     (settlement-class hits demote to locality)
  2. municipality centroid (offline,
     khmdhs/data/greek_municipalities.json)            -> municipality
  3. nothing — the site stays coordinate-free (the map falls back to the
     Π.Ε. centroid client-side).

Validation gates before a pin ships (rather show nothing than a wrong pin):
  - the hit's address must agree with the site's Π.Ε. (geocode_loader
    `_acceptable` doctrine, Π.Ε.-name branch),
  - ≤ MAX_MUNI_KM from the stated municipality's centroid when one exists,
  - a report of every accept/reject is printed for review; the EFFIS
    burn-scar cross-check runs separately (--effis) and only reports.

Resumable: sites that already carry lat/lon or geo_precision are skipped
(delete the fields to re-geocode). Manual pins (geo_source web:/curator)
are never touched.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from khmdhs.geocode_loader import (NOMINATIM_URL, RATE_SLEEP, _acceptable,
                                   _query, _translit)

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_JSON = ROOT / "khmdhs/data/anadohoi_projects.json"
MUNIS_JSON = ROOT / "khmdhs/data/greek_municipalities.json"
MAX_MUNI_KM = 15.0

# settlement-ish OSM classes: a hit on the village itself is 'locality',
# a named place/peak/stream/forest is 'site'
_LOCALITY_TYPES = {"village", "hamlet", "town", "suburb", "neighbourhood",
                   "quarter", "city"}


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _muni_centroid(munis: dict, genitive: str | None):
    if not genitive:
        return None
    g = genitive.strip()
    for m in munis.values():
        if m["name"] == g:
            return m
    return None


def _clean_query_name(name: str) -> str:
    """The toponym alone: strip θέση/Τμήμα labels and «» quotes."""
    s = name
    for pre in ("θέση", "Θέση", "περιοχή", "Περιοχή", "Τμήμα", "ρέμα", "Ρέμα",
                "Δάσος", "δάσος", "οικισμός", "Οικισμός"):
        if s.startswith(pre + " "):
            s = s[len(pre) + 1:]
    return s.strip("«»\"' ").strip()


def geocode_site(session: requests.Session, site: dict, munis: dict,
                 project_pe: str | None) -> tuple[str, str] | None:
    """Try the tiers; mutates site in place on success. Returns
    (geo_precision, message) or None."""
    pe = site.get("pe") or project_pe
    name = _clean_query_name(site["name"])
    muni = site.get("municipality")
    mrec = _muni_centroid(munis, muni)
    queries = []
    base = f"{name}, {muni}" if muni else name
    queries.append(base)
    if muni:
        queries.append(f"{name}, Δήμος {muni}")
    queries.append(f"{_translit(name)}, {_translit(muni)}" if muni
                   else _translit(name))
    for q in queries:
        hits = _query(session, {"q": q, "format": "jsonv2",
                                "addressdetails": 1, "limit": 3,
                                "countrycodes": "gr"})
        time.sleep(RATE_SLEEP)
        if not hits:
            continue
        for hit in hits:
            if not _acceptable(hit, None, pe):
                continue
            lat, lon = float(hit["lat"]), float(hit["lon"])
            if mrec is not None and _km(lat, lon, mrec["lat"],
                                        mrec["lon"]) > MAX_MUNI_KM:
                print(f"    reject {q!r}: {_km(lat, lon, mrec['lat'], mrec['lon']):.1f} km "
                      f"from Δ. {muni} centroid")
                continue
            prec = ("locality" if hit.get("type") in _LOCALITY_TYPES
                    else "site")
            site["lat"] = round(lat, 5)
            site["lon"] = round(lon, 5)
            site["geo_precision"] = prec
            site["geo_source"] = "nominatim"
            return prec, f"{q!r} -> {hit.get('display_name', '')[:70]}"
    # tier: municipality centroid, offline
    if site.get("kind") == "municipality" or mrec is not None:
        if mrec is not None:
            site["lat"] = round(mrec["lat"], 5)
            site["lon"] = round(mrec["lon"], 5)
            site["geo_precision"] = "municipality"
            site["geo_source"] = "municipality-centroid"
            return "municipality", f"centroid of Δ. {muni}"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="limit to one root ΑΔΑ")
    args = ap.parse_args()

    data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    munis = json.loads(MUNIS_JSON.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers["User-Agent"] = \
        "evia-khmdhs-osint/1.0 (work-site geocoding; batch of ~60)"

    stats = {"pinned": 0, "municipality": 0, "skipped": 0, "unresolved": 0}
    for p in data["projects"]:
        if args.only and p["root_ada"] != args.only:
            continue
        for site in p.get("work_sites") or []:
            if site.get("lat") is not None or site.get("geo_precision"):
                stats["skipped"] += 1
                continue
            print(f"{p['root_ada']} · {site['name']}")
            got = geocode_site(session, site, munis, p.get("pe"))
            if got:
                prec, msg = got
                stats["municipality" if prec == "municipality"
                      else "pinned"] += 1
                print(f"    {prec}: {msg}")
            else:
                stats["unresolved"] += 1
                print("    UNRESOLVED (candidate for manual web research)")

    print(json.dumps(stats))
    if not args.dry_run:
        PROJECTS_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"wrote {PROJECTS_JSON}")


if __name__ == "__main__":
    main()
