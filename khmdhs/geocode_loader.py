"""Geocode contractor addresses once via OSM Nominatim (anonymous, no key).

Policy (DATA_DECISIONS.md 2026-07-25): a hit is accepted only when its
postcode agrees with the stored postal code (3-digit prefix) or its
postcode resolves to the entry's curated Π.Ε. — otherwise we'd rather show
nothing than a wrong pin. Tiers:

  1. structured street + postalcode + city  → geo_precision "address"
  2. freeform  "street, postal city"        → geo_precision "address"
  3. city + postalcode only (no street)     → geo_precision "municipality"

Entries that fail all tiers get `geo_precision: "failed"` (kept so they are
not re-queried; re-run with --retry-failed after fixing the address) and NO
coordinates — honest misses, counted by the UI. Results are cached in
contractor_locations.json; push to the DB with khmdhs.contractor_loader.

Nominatim usage policy: ≤1 req/s (we sleep 1.2 s), identifying User-Agent,
one-off batch of ~180 queries.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import time
from pathlib import Path

import requests

from khmdhs.greek_regions import resolve_pe

DATA_FILE = Path(__file__).parent / "data" / "contractor_locations.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "evia-khmdhs-osint/1.0 (contractor HQ mapping; batch of ~180)"
RATE_SLEEP = 1.2
CHECKPOINT_EVERY = 10


def _save_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


_TRANSLIT = {
    "Α": "a", "Β": "v", "Γ": "g", "Δ": "d", "Ε": "e", "Ζ": "z", "Η": "i",
    "Θ": "th", "Ι": "i", "Κ": "k", "Λ": "l", "Μ": "m", "Ν": "n", "Ξ": "x",
    "Ο": "o", "Π": "p", "Ρ": "r", "Σ": "s", "Τ": "t", "Υ": "y", "Φ": "f",
    "Χ": "ch", "Ψ": "ps", "Ω": "o", "Ϊ": "i", "Ϋ": "y",
}


def _translit(s: str) -> str:
    """Rough ISO-843 Greek→Latin — the public Nominatim frequently matches
    the transliterated street name when the Greek-script query returns
    nothing (verified live: «ΚΟΡΝΑΡΟΥ 13, ΘΕΣΣΑΛΟΝΙΚΗ» → 0 hits,
    "Kornarou 13, Thessaloniki" → the street)."""
    import unicodedata
    decomposed = unicodedata.normalize("NFD", s.upper())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    out = "".join(_TRANSLIT.get(ch, ch.lower()) for ch in stripped)
    return out.replace("oy", "ou").replace("ay", "av").replace("ey", "ev")


def _query(session: requests.Session, params: dict) -> list[dict] | None:
    base = {"format": "jsonv2", "addressdetails": 1, "limit": 3,
            "countrycodes": "gr"}
    try:
        resp = session.get(NOMINATIM_URL, params={**base, **params},
                           headers={"User-Agent": USER_AGENT}, timeout=30)
    except requests.RequestException as e:
        logging.warning("nominatim network error: %s", e)
        return None
    if resp.status_code != 200:
        logging.warning("nominatim http %s", resp.status_code)
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def _fold(s: str) -> str:
    import unicodedata
    d = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(ch for ch in d if not unicodedata.combining(ch))


def _acceptable(hit: dict, postal: str | None, region_pe: str | None) -> bool:
    """Postcode prefix agreement, the hit's postcode resolving to the
    curated Π.Ε., or the hit's county/state naming that Π.Ε. — never
    accept a hit we cannot validate against something we already know."""
    addr = hit.get("address") or {}
    hit_pc = (addr.get("postcode") or "").replace(" ", "")
    if postal and hit_pc:
        return hit_pc[:3] == postal.replace(" ", "")[:3]
    if region_pe and hit_pc:
        pe, _method = resolve_pe(None, hit_pc)
        if pe == region_pe:
            return True
    if region_pe:
        # e.g. county "Περιφερειακή Ενότητα Τρικάλων" vs "Π.Ε. Τρικάλων".
        want = _fold(region_pe.replace("Π.Ε.", "").strip())
        for key in ("county", "state_district", "state"):
            if want and want in _fold(addr.get(key) or ""):
                return True
    return False


def geocode_entry(entry: dict, session: requests.Session,
                  sleep: float = RATE_SLEEP) -> tuple[float, float, str] | None:
    """Return (lat, lon, precision) for a curated entry, or None."""
    street = (entry.get("address") or "").strip()
    postal = (entry.get("postal_code") or "").strip() or None
    city = (entry.get("city") or "").strip() or None
    pe = entry.get("region_pe")

    tiers: list[tuple[dict, str]] = []
    if street:
        # VIES abbreviates street prefixes («Β ΚΟΡΝΑΡΟΥ 13», «Λ ΣΤΑΜΑΤΑΣ 5»
        # = Λεωφόρος) — try cleaned variants when the raw form finds nothing.
        variants = [street]
        import re as _re
        m = _re.match(r"^([Α-ΩΪΫA-Z])\.?\s+(\S.*)$", street)
        if m:
            if m.group(1) in ("Λ", "L"):
                variants.append(f"ΛΕΩΦΟΡΟΣ {m.group(2)}")
            variants.append(m.group(2))
        for v in variants:
            p: dict = {"street": v}
            if postal:
                p["postalcode"] = postal
            if city:
                p["city"] = city.split("/")[0].strip()
            tiers.append((p, "address"))
        freeform = ", ".join(x for x in (street, f"{postal or ''} {city or ''}".strip()) if x)
        tiers.append(({"q": freeform}, "address"))
        best = variants[-1]  # cleaned form transliterates best
        lat_q = _translit(best) + (f", {_translit(city.split('/')[0].strip())}" if city else "")
        tiers.append(({"q": lat_q}, "address"))
    if city:
        p = {"city": city.split("/")[0].strip()}
        if postal:
            p["postalcode"] = postal
        tiers.append((p, "municipality"))
        # q may not be combined with structured params — embed the postal.
        tiers.append(({"q": " ".join(x for x in
                       (_translit(city.split("/")[0].strip()), postal or "") if x)},
                      "municipality"))
    if postal:
        # Last resort: the postcode's own centroid (validates trivially) —
        # rescues truncated/misspelled city names («ΚΑΜ ΒΟΥΡΛΑ», «ΩΡΑΙΟΙ»).
        tiers.append(({"postalcode": postal}, "municipality"))

    for i, (params, precision) in enumerate(tiers):
        hits = _query(session, params) or []
        for hit in hits:
            if _acceptable(hit, postal, pe):
                return float(hit["lat"]), float(hit["lon"]), precision
        if i < len(tiers) - 1:
            time.sleep(sleep)
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m khmdhs.geocode_loader")
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--rate-sleep", type=float, default=RATE_SLEEP)
    p.add_argument("--retry-failed", action="store_true",
                   help='re-query entries previously marked geo_precision "failed"')
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with args.data.open(encoding="utf-8") as f:
        curation: dict = json.load(f)

    todo = []
    for vat, e in curation.items():
        if e.get("lat") is not None:
            continue
        if e.get("geo_precision") == "failed" and not args.retry_failed:
            continue
        if not (e.get("address") or e.get("city")):
            continue  # nothing to geocode — stays an honest miss
        todo.append(vat)
    if args.limit is not None:
        todo = todo[: args.limit]
    logging.info("geocode sweep: %d candidates", len(todo))

    today = dt.date.today().isoformat()
    session = requests.Session()
    counts = {"address": 0, "municipality": 0, "failed": 0}
    for i, vat in enumerate(todo, start=1):
        entry = curation[vat]
        logging.info("[%d/%d] %s — %s | %s %s", i, len(todo), vat.strip(),
                     (entry.get("legal_name") or "?")[:45],
                     entry.get("address") or "—", entry.get("city") or "")
        res = geocode_entry(entry, session, args.rate_sleep)
        if res:
            lat, lon, precision = res
            counts[precision] += 1
            update = {**entry, "lat": round(lat, 5), "lon": round(lon, 5),
                      "geo_precision": precision, "geocoded_at": today}
            logging.info("  → %.5f, %.5f (%s)", lat, lon, precision)
        else:
            counts["failed"] += 1
            update = {**entry, "geo_precision": "failed", "geocoded_at": today}
            logging.info("  → no validated hit")
        if not args.dry_run:
            curation[vat] = update
            if i % CHECKPOINT_EVERY == 0:
                _save_atomic(args.data, curation)
        if i < len(todo):
            time.sleep(args.rate_sleep)

    if not args.dry_run:
        _save_atomic(args.data, curation)
    print()
    print("=" * 60)
    print(f"Geocode sweep — {len(todo)} tried: "
          f"{counts['address']} address-level, {counts['municipality']} "
          f"municipality-level, {counts['failed']} failed")
    print("Next: .venv/bin/python -m khmdhs.contractor_loader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
