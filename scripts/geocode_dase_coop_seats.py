# -*- coding: utf-8 -*-
"""Geocode the ΔΑΣΕ co-operatives' registered offices (DATA_DECISIONS
2026-08-24) — the Anti-nero contractor-office pipeline one dataset over.

Reuses `khmdhs.geocode_loader.geocode_entry` verbatim: OSM Nominatim with
the same tiers (structured → freeform → Greek→Latin transliteration →
settlement centre → postcode centroid) and the same acceptance gate — a hit
is kept ONLY when its postcode agrees with the register's (3-digit prefix)
or it resolves into the Π.Ε. we already know from the co-op's contracts.

Co-op seats are villages with no street («ΣΤΑΥΡΟΣ 0»), so the honest
precision here is `municipality` — the centre of the named settlement — and
`address` appears only where the register really states a street.

Usage:
    python scripts/geocode_dase_coop_seats.py            # the whole file
    python scripts/geocode_dase_coop_seats.py --limit 20
    python scripts/geocode_dase_coop_seats.py --redo     # re-geocode all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import requests                                            # noqa: E402

from khmdhs.geocode_loader import geocode_entry            # noqa: E402

FILE = ROOT / "khmdhs" / "data" / "dase_coop_locations.json"
UA = "khmdhs-osint/1.0 (forest co-op seats; contact via repo)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, default=FILE)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--redo", action="store_true", help="re-geocode entries that have a point")
    ap.add_argument("--sleep", type=float, default=1.1)
    args = ap.parse_args(argv)

    doc = json.loads(args.file.read_text(encoding="utf-8"))
    coops: dict[str, dict] = doc["coops"]

    todo = [v for v, e in coops.items()
            if (args.redo or "lat" not in e)
            and (e.get("register", {}).get("settlement") or e.get("register", {}).get("city")
                 or e.get("curated", {}).get("settlement"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} co-ops to geocode", flush=True)

    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})
    ok = fail = 0
    for i, vat in enumerate(todo, 1):
        e = coops[vat]
        reg = e.get("register") or {}
        cur = e.get("curated") or {}
        settlement = cur.get("settlement") or reg.get("settlement")
        postal = cur.get("postal_code") or reg.get("postal_code")
        city = cur.get("city") or reg.get("city")
        pe = (e.get("contract_pes") or [None])[0]

        # the register's «street» IS the village for a co-op; hand it to the
        # geocoder as the CITY (a village is not a street) and keep the
        # reference town as the fallback tier
        entry = {"address": "", "postal_code": postal or "",
                 "city": settlement or city or "", "region_pe": pe}
        hit = geocode_entry(entry, sess, sleep=args.sleep)
        if hit is None and city and settlement and city != settlement:
            entry["city"] = city                 # fall back to the reference town
            hit = geocode_entry(entry, sess, sleep=args.sleep)
            if hit:
                hit = (hit[0], hit[1], "municipality")
        if hit:
            e["lat"], e["lon"], e["geo_precision"] = round(hit[0], 6), round(hit[1], 6), hit[2]
            ok += 1
        else:
            e.pop("lat", None); e.pop("lon", None); e.pop("geo_precision", None)
            e["geo_precision"] = "failed"
            fail += 1
        if i % 20 == 0 or i == len(todo):
            args.file.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {i}/{len(todo)} · located {ok} · failed {fail}", flush=True)
        time.sleep(args.sleep)

    args.file.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"located {ok}, failed {fail} → {args.file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
