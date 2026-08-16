# -*- coding: utf-8 -*-
"""Geocode the forest authorities' curated office addresses (the `office`
blocks in forest_authorities.json) via OSM Nominatim, with the project's
validation gates (DATA_DECISIONS 2026-08-17):

tiers: street+Τ.Κ.+city (structured) → Τ.Κ.+city → city; each tier also
retried with a Greek→Latin transliteration (the public Nominatim often
misses Greek-script queries — institutional memory #16). A hit is
ACCEPTED only if its postcode shares the office Τ.Κ.'s 3-digit prefix,
or it lies ≤35 km from the seat municipality's centroid. Results land in
the office block as lat/lon + geo_precision (street|postcode|city);
failures store nothing — the loader keeps the municipality centroid.

Resumable: entries with lat already set are skipped (--force redoes all).
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FA = ROOT / "khmdhs" / "data" / "forest_authorities.json"
MUNI = ROOT / "khmdhs" / "data" / "greek_municipalities.json"

S = requests.Session()
S.headers["User-Agent"] = "khmdhs-osint forest-office geocoder (contact: local research)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

TR = {"ΑΙ": "AI", "ΕΙ": "EI", "ΟΙ": "OI", "ΟΥ": "OU", "ΑΥ": "AV", "ΕΥ": "EV",
      "ΓΓ": "NG", "ΓΚ": "GK", "ΜΠ": "B", "ΝΤ": "NT", "ΤΣ": "TS", "ΤΖ": "TZ",
      "Θ": "TH", "Χ": "CH", "Ψ": "PS", "Α": "A", "Β": "V", "Γ": "G", "Δ": "D",
      "Ε": "E", "Ζ": "Z", "Η": "I", "Ι": "I", "Κ": "K", "Λ": "L", "Μ": "M",
      "Ν": "N", "Ξ": "X", "Ο": "O", "Π": "P", "Ρ": "R", "Σ": "S", "Τ": "T",
      "Υ": "Y", "Φ": "F", "Ω": "O", "Ϊ": "I", "Ϋ": "Y"}


def translit(s: str) -> str:
    import unicodedata
    up = "".join(c for c in unicodedata.normalize("NFD", (s or "").upper())
                 if not unicodedata.combining(c))
    out, i = "", 0
    while i < len(up):
        two = up[i:i + 2]
        if two in TR:
            out += TR[two]; i += 2; continue
        out += TR.get(up[i], up[i]); i += 1
    return out.title()


def dist_km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


def query(params: dict) -> list[dict]:
    p = {"format": "jsonv2", "addressdetails": 1, "limit": 3,
         "countrycodes": "gr", **params}
    r = S.get(NOMINATIM, params=p, timeout=40)
    time.sleep(1.1)
    if r.status_code != 200:
        return []
    return r.json()


def accept(hit: dict, tk: str | None, cent) -> bool:
    pc = (hit.get("address") or {}).get("postcode", "").replace(" ", "")
    if tk and pc and pc[:3] == tk[:3]:
        return True
    if cent:
        return dist_km((float(hit["lat"]), float(hit["lon"])), cent) <= 35
    return False


def geocode(office: dict, cent) -> tuple[float, float, str] | None:
    street, tk, city = office.get("street"), office.get("tk"), office.get("city")
    tiers: list[tuple[str, dict]] = []
    if street and city:
        tiers.append(("street", {"street": street, "city": city,
                                 **({"postalcode": tk} if tk else {})}))
        tiers.append(("street", {"street": translit(street), "city": translit(city),
                                 **({"postalcode": tk} if tk else {})}))
    if tk and city:
        tiers.append(("postcode", {"postalcode": tk, "city": city}))
        tiers.append(("postcode", {"postalcode": tk, "city": translit(city)}))
    if city:
        tiers.append(("city", {"city": city}))
        tiers.append(("city", {"city": translit(city)}))
    for precision, params in tiers:
        for hit in query(params):
            if accept(hit, tk, cent):
                return float(hit["lat"]), float(hit["lon"]), precision
    return None


def main(argv=None) -> int:
    force = bool(argv and "--force" in argv)
    fa = json.loads(FA.read_text(encoding="utf-8"))
    munis = json.loads(MUNI.read_text(encoding="utf-8"))
    cent_of = {code: (m["lat"], m["lon"]) for code, m in munis.items()
               if isinstance(m, dict) and m.get("lat")}
    n_ok = n_skip = n_fail = 0
    for name, entry in fa["authorities"].items():
        office = entry.get("office") or {}
        if not office or (office.get("lat") and not force):
            n_skip += bool(office.get("lat"))
            continue
        if not (office.get("street") or office.get("tk") or office.get("city")):
            continue
        cent = cent_of.get(entry.get("municipality_code"))
        got = geocode(office, cent)
        if got:
            office["lat"], office["lon"], office["geo_precision"] = got
            n_ok += 1
            print(f"OK  {name}: {got[2]} {got[0]:.5f},{got[1]:.5f}")
        else:
            n_fail += 1
            print(f"--  {name}: no validated hit (falls back to municipality centroid)")
        FA.write_text(json.dumps(fa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"geocoded {n_ok}, failed {n_fail}, already had {n_skip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
