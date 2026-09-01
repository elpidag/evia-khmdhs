#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bootstrap, re-geocode and audit the curated «112» alerts of August 2021 —
the data of the story's Figure 04 (DATA_DECISIONS 2026-09-02).

    --init       write atlas/src/lib/data/alerts_112_2021.json ONCE from the
                 raw inputs under data/raw/112/ (the sibling implementation's
                 parsed file supplies the proposal, the raw tweets the
                 verbatim text). A reviewed file is never overwritten.
    --overpass   fetch, ONCE per fire region, every named OSM place node inside
                 the region's regional units (one Overpass query per region,
                 cached in data/processed/alerts_cache/overpass_places.json).
    --match      print, for every place the audit doubts (outside its
                 region's units, or typed in with ≤3 decimals), the OSM place
                 nodes whose name matches one of its NAME_FORMS — accent- and
                 case-folded, exact first, then loose — with node ids, so a
                 verdict can be written by hand with its evidence.
    --audit      print the review sheet: places outside their region's units,
                 long edges, coincident coordinates under different names,
                 two-sentence messages, rows with no placed point, Greek
                 script in nameEn, unsorted timestamps. Exit 1 on flags.

Stdlib only (the project venv has no geo libraries): the point-in-unit test
is a ray cast over webui/static/greek_pe.geojson. Every verdict — a moved or
unplaced point, which sentence sends whom where, a prose destination, a
gloss — is taken BY HAND in the curated file with its evidence in `note`
(the OSM node id and name for a moved point). A Nominatim pass with region
qualifiers was tried first and set aside: 39 answers of 193, one of them a
shop for Mantoudi.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/112/alerts_112_aug_2021_all.json"
GEN = ROOT / "data/raw/112/alerts-112.generated.json"
OUT = ROOT / "atlas/src/lib/data/alerts_112_2021.json"
PE = ROOT / "webui/static/greek_pe.geojson"
PLACES = ROOT / "data/processed/alerts_cache/overpass_places.json"

SRC_GAZ = "gazetteer:evia-wildfire-timeline"
PLACE_SOURCES = (SRC_GAZ, "hand", "prose", "unplaced")
TYPES = ("evacuation", "shelter_in_place", "fire_danger", "general")
BOX = (19.5, 34.7, 28.6, 41.8)          # the figure's frame (alertsFrame.ts)
LONG_EDGE_KM = 60.0                   # Tropaia→Tripoli, a stated order, is 49 km

# the regional units a fire region's places may lie in (the alerts'
# fireRegion vocabulary → Π.Ε. of greek_pe.geojson); «other» is unchecked
REGION_PE: dict[str, tuple[str, ...]] = {
    "attica_north": ("Π.Ε. Ανατολικής Αττικής", "Π.Ε. Βορείου Τομέα Αθηνών",
                     "Π.Ε. Κεντρικού Τομέα Αθηνών", "Π.Ε. Δυτικού Τομέα Αθηνών",
                     "Π.Ε. Δυτικής Αττικής"),
    "attica_west": ("Π.Ε. Δυτικής Αττικής", "Π.Ε. Δυτικού Τομέα Αθηνών"),
    "attica_south": ("Π.Ε. Ανατολικής Αττικής",),
    "evia": ("Π.Ε. Ευβοίας",),
    "ilia": ("Π.Ε. Ηλείας",),
    "messinia": ("Π.Ε. Μεσσηνίας",),
    "rhodes": ("Π.Ε. Ρόδου",),
    "fokida": ("Π.Ε. Φωκίδας",),
    "arcadia": ("Π.Ε. Αρκαδίας",),
    "corinthia": ("Π.Ε. Κορινθίας",),
    "grevena": ("Π.Ε. Γρεβενών",),
}
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
UA = "evia-khmdhs bootstrap_alerts_112.py (research site; one query per region)"

# the Greek NOMINATIVE forms behind the messages' hashtags (which inflect —
# «#Πύργο», «#Κρυονερίου») and OSM's own spellings, hand-written for the
# places the audit doubted; a tag not listed is matched on its own letters
NAME_FORMS: dict[str, list[str]] = {
    "Πύργο": ["Πύργος"], "Λάλα": ["Λάλας", "Λάλα"], "Μηλιές": ["Μηλιές"],
    "Πλάτανο": ["Πλάτανος"], "Κοσκινά": ["Κοσκινάς", "Κοσκινά"], "Μάγειρα": ["Μάγειρας"],
    "Ξηρόκαμπο": ["Ξηρόκαμπος"], "Αμπάρι": ["Αμπάριον", "Αμπάρι"], "Λάσδικα": ["Λάσδικας"],
    "Πανόπουλο": ["Πανόπουλος"], "Σέκουλα": ["Σέκουλας"], "Καμμένα": ["Κάμενα", "Καμμένα"],
    "Λινάρια": ["Λιναριά", "Λινάρια"], "Άνω_Κάτω_Λούβρο": ["Λούβρο", "Άνω Λούβρο", "Κάτω Λούβρο"],
    "ΆσπραΣπίτια": ["Άσπρα Σπίτια"], "Ερυθραίας": ["Ερυθρές"], "Θεολόγο": ["Θεολόγος"],
    "Λουτρών_Αιδηψού": ["Λουτρά Αιδηψού"], "Αιδηψού": ["Αιδηψός"], "Σολομό": ["Σολομός"],
    "Ελαία": ["Ελιά", "Ελαία"], "Άγιο_Σπυρίδωνα": ["Άγιος Σπυρίδων"], "Καρνάσι": ["Καρνάσιο"],
    "Δεσύλλα": ["Δεσύλλας"], "Ζευγολατειό": ["Ζευγολατιό"], "Αγίους_Θεοδώρους": ["Άγιοι Θεόδωροι"],
    "Αετοράχη": ["Αετορράχη"], "ΆγιοςΙωάννης": ["Άγιος Ιωάννης Αρχαίας Ηραίας"],
    "ΙαματικέςΠηγές": ["Λουτρά Ηραίας"], "Λουτρά": ["Λουτρά Ηραίας"], "Κάλαμο": ["Κάλαμος"],
    "Ωρωπό": ["Ωρωπός"], "Ψίνθο": ["Ψίνθος"], "Προφήτη_Ηλία_Βιλίων": ["Προφήτης Ηλίας"],
    "Κέντρο": ["Κέντρο"], "Αθήνα": ["Αθήνα"], "Άθήνα": ["Αθήνα"], "ΝέαΣτύρα": ["Νέα Στύρα"],
}


# ── helpers ─────────────────────────────────────────────────────────────────

def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """great-circle distance between (lon, lat) pairs"""
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def placed(p: dict) -> bool:
    return p.get("lat") is not None and p.get("lon") is not None


def has_greek(s: str) -> bool:
    return any("GREEK" in unicodedata.name(ch, "") for ch in s)


def places_of(a: dict) -> list[dict]:
    return [p for o in a["orders"] for p in o["from"] + o["to"]]


class Units:
    """point → regional unit, by ray casting over the coarse Π.Ε. layer"""

    def __init__(self) -> None:
        fc = json.loads(PE.read_text(encoding="utf-8"))
        self.polys: list[tuple[str, list, tuple]] = []
        for f in fc["features"]:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                xs = [x for x, _ in poly[0]]
                ys = [y for _, y in poly[0]]
                self.polys.append((f["properties"]["pe"], poly,
                                   (min(xs), min(ys), max(xs), max(ys))))

    @staticmethod
    def _inside(ring: list, x: float, y: float) -> bool:
        inside = False
        n = len(ring)
        for i in range(n - 1):
            x1, y1 = ring[i]
            x2, y2 = ring[i + 1]
            if (y1 > y) != (y2 > y):
                xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xi > x:
                    inside = not inside
        return inside

    def _unit_at(self, lon: float, lat: float) -> str | None:
        for pe, poly, (x0, y0, x1, y1) in self.polys:
            if not (x0 <= lon <= x1 and y0 <= lat <= y1):
                continue
            if self._inside(poly[0], lon, lat) and not any(
                    self._inside(hole, lon, lat) for hole in poly[1:]):
                return pe
        return None

    def unit_of(self, lon: float, lat: float, tol: float = 0.012) -> str | None:
        """the unit under the point — or, for a point the coarse coastline
        leaves a hair offshore (a seaside village), the unit within ~1 km"""
        hit = self._unit_at(lon, lat)
        if hit or not tol:
            return hit
        for dx, dy in ((tol, 0), (-tol, 0), (0, tol), (0, -tol),
                       (tol, tol), (-tol, tol), (tol, -tol), (-tol, -tol)):
            hit = self._unit_at(lon + dx, lat + dy)
            if hit:
                return hit
        return None


# ── init ────────────────────────────────────────────────────────────────────

def init() -> None:
    if OUT.exists():
        sys.exit(f"{OUT.relative_to(ROOT)} exists — it is reviewed by hand and "
                 "is never overwritten; delete it yourself if you mean to")
    raw = {r["tweet_id"]: r for r in json.loads(RAW.read_text(encoding="utf-8"))}
    gen = json.loads(GEN.read_text(encoding="utf-8"))
    gen.sort(key=lambda a: a["timestamp"])
    alerts = []
    for a in gen:
        r = raw[a["tweetId"]]
        row = {
            "tweetId": a["tweetId"],
            "timestamp": a["timestamp"],
            "type": a["alertType"],
            "region": a["fireRegion"],
            "orders": [{"from": [_place(p) for p in a["fromLocations"]],
                        "to": [_place(p) for p in a["toLocations"]]}],
            "text": r["text"],
            "url": a["sourceUrl"],
        }
        if not any(placed(p) for p in places_of(row)):
            row["title"] = ""       # the English gloss the card prints — by hand
        alerts.append(row)
    doc = {
        "_meta": {
            "source": "@112Greece (Γενική Γραμματεία Πολιτικής Προστασίας) "
                      "tweets, 1–23 August 2021; raw copy "
                      "data/raw/112/alerts_112_aug_2021_all.json",
            "bootstrap": "scripts/bootstrap_alerts_112.py --init from the "
                         "evia-wildfire-timeline implementation's parsed file "
                         "(data/raw/112/alerts-112.generated.json), re-geocoded "
                         "checked against OSM with --overpass/--match, then reviewed by hand — "
                         "DATA_DECISIONS 2026-09-02",
            "timezone": "+03:00 (EEST) throughout the window",
            "types": list(TYPES),
            "place_sources": list(PLACE_SOURCES),
            "rules": [
                "an alert holds one ORDER per instruction sentence: the places "
                "told to leave (from) and the places they were sent to (to); a "
                "two-sentence message has two orders, never a cartesian product",
                "a place that cannot be placed keeps lat/lon null and source "
                "'unplaced' — never invented; the card still names it",
                "a destination the message gives in prose (no hashtag) is a "
                "'to' entry with source 'prose'",
                "every hand correction carries source 'hand' and a note "
                "quoting the evidence",
                "the tweet text is verbatim and byte-equal to the raw record",
            ],
        },
        "alerts": alerts,
    }
    _write(doc)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(alerts)} alerts")


def _place(p: dict) -> dict:
    return {"tag": p["tag"], "nameEn": p["nameEn"], "lat": p["lat"],
            "lon": p["lon"], "source": SRC_GAZ}


def _write(doc: dict) -> None:
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")


# ── overpass / match ────────────────────────────────────────────────────────

def _pe_bbox() -> dict[str, tuple[float, float, float, float]]:
    fc = json.loads(PE.read_text(encoding="utf-8"))
    out = {}
    for f in fc["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        xs = [x for poly in polys for x, _ in poly[0]]
        ys = [y for poly in polys for _, y in poly[0]]
        out[f["properties"]["pe"]] = (min(ys), min(xs), max(ys), max(xs))
    return out


def _overpass(q: str) -> dict:
    data = urllib.parse.urlencode({"data": q}).encode()
    for _ in range(4):
        for url in OVERPASS:
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=180) as r:
                    res = json.loads(r.read().decode("utf-8"))
                if res.get("elements") is not None:
                    return res
            except Exception as e:      # noqa: BLE001 — the public mirrors 429/5xx
                print(f"  {url}: {str(e)[:60]}; retrying")
                time.sleep(5)
    return {"elements": []}


def overpass() -> None:
    """every named place node inside each fire region's units, cached"""
    bbox = _pe_bbox()
    units = Units()
    PLACES.parent.mkdir(parents=True, exist_ok=True)
    dump = json.loads(PLACES.read_text(encoding="utf-8")) if PLACES.exists() else {}
    for region, pes in REGION_PE.items():
        if region in dump:
            continue
        s_, w_ = min(bbox[pe][0] for pe in pes) - 0.03, min(bbox[pe][1] for pe in pes) - 0.03
        n_, e_ = max(bbox[pe][2] for pe in pes) + 0.03, max(bbox[pe][3] for pe in pes) + 0.03
        res = _overpass(f'[out:json][timeout:180];node["place"]["name"]({s_},{w_},{n_},{e_});out;')
        rows = []
        for el in res["elements"]:
            pe = units.unit_of(el["lon"], el["lat"], tol=0)
            if pe not in pes:
                continue
            t = el["tags"]
            rows.append({"id": el["id"], "name": t.get("name"), "name_el": t.get("name:el"),
                         "alt": t.get("alt_name"), "place": t.get("place"),
                         "lat": el["lat"], "lon": el["lon"], "pe": pe})
        dump[region] = rows
        PLACES.write_text(json.dumps(dump, ensure_ascii=False), encoding="utf-8")
        print(f"{region:14s} {len(rows)} named place nodes")
        time.sleep(2)
    print(f"→ {PLACES.relative_to(ROOT)}")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.casefold().replace("ς", "σ").strip()


def _decimals(v: float) -> int:
    t = repr(v)
    return len(t.split(".")[1]) if "." in t else 0


def match() -> None:
    """candidates for every doubted place, from the cached dump"""
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    dump = json.loads(PLACES.read_text(encoding="utf-8"))
    units = Units()
    seen: set[tuple[str, str]] = set()
    for a in doc["alerts"]:
        region = "messinia" if a["region"] == "other" else a["region"]
        allowed = REGION_PE.get(region)
        for p in places_of(a):
            key = (p["tag"], region)
            if key in seen or p["source"] == "prose" or allowed is None:
                continue
            doubted = (not placed(p) or units.unit_of(p["lon"], p["lat"]) not in allowed
                       or _decimals(p["lat"]) <= 3 or _decimals(p["lon"]) <= 3)
            if not doubted:
                continue
            seen.add(key)
            forms = [_fold(f) for f in NAME_FORMS.get(p["tag"], [p["tag"].replace("_", " ")])]
            hits = []
            for r in dump.get(region, []):
                names = [_fold(n) for n in (r["name"], r["name_el"], r["alt"]) if n]
                exact = any(n in forms for n in names)
                loose = any(any(f in n for f in forms) for n in names)
                if exact or loose:
                    d = km((p["lon"], p["lat"]), (r["lon"], r["lat"])) if placed(p) else None
                    hits.append((0 if exact else 1, d if d is not None else 9e9, r, d))
            hits.sort(key=lambda h: (h[0], h[1]))
            state = (f"{p['lat']:.4f},{p['lon']:.4f} {units.unit_of(p['lon'], p['lat']) or 'no unit'}"
                     if placed(p) else "unplaced")
            print(f"{p['tag']}@{region} [{p['source']}] {state} — {len(hits)} candidate(s)")
            for ex, _, r, d in hits[:4]:
                print(f"    {'=' if ex == 0 else '~'} {r['name']:26s} {str(r['place']):10s} "
                      f"{r['lat']:.5f},{r['lon']:.5f} {r['pe']}"
                      f"{'' if d is None else f'  {d:.1f} km'}  node {r['id']}")


# ── audit ───────────────────────────────────────────────────────────────────

def audit() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    raw = {r["tweet_id"]: r for r in json.loads(RAW.read_text(encoding="utf-8"))}
    units = Units()
    alerts = doc["alerts"]
    flags: list[str] = []
    print(f"{len(alerts)} alerts · raw tweets {len(raw)}")
    if len(alerts) != len(raw):
        flags.append(f"row count {len(alerts)} != raw {len(raw)}")
    ts = [a["timestamp"] for a in alerts]
    if ts != sorted(ts):
        flags.append("timestamps not sorted")
    seen_ids: set[str] = set()
    for i, a in enumerate(alerts):
        pre = f"#{i:02d} {a['timestamp'][:16]} {a['region']:12s} {a['type']:16s}"
        if a["tweetId"] in seen_ids:
            flags.append(f"{pre} duplicate tweetId")
        seen_ids.add(a["tweetId"])
        if not a["timestamp"].endswith("+03:00"):
            flags.append(f"{pre} timestamp not +03:00")
        if a["type"] not in TYPES:
            flags.append(f"{pre} unknown type {a['type']}")
        if a["tweetId"] in raw and raw[a["tweetId"]]["text"] != a["text"]:
            flags.append(f"{pre} text differs from the raw tweet")
        allowed = REGION_PE.get(a["region"])
        pts = places_of(a)
        for p in pts:
            if p["source"] not in PLACE_SOURCES:
                flags.append(f"{pre} place {p['tag']} bad source {p['source']}")
            # an unplaced entry has no point; a prose destination may have none
            if (p["source"] == "unplaced" and placed(p)) or (
                    not placed(p) and p["source"] not in ("unplaced", "prose")):
                flags.append(f"{pre} {p['nameEn']}: source/coordinates disagree")
            if placed(p):
                if not (BOX[0] <= p["lon"] <= BOX[2] and BOX[1] <= p["lat"] <= BOX[3]):
                    flags.append(f"{pre} {p['nameEn']} outside the frame box")
                pe = units.unit_of(p["lon"], p["lat"])
                if allowed is not None and pe not in allowed:
                    flags.append(f"{pre} {p['nameEn']} lies in {pe or 'no unit'}")
            if has_greek(p["nameEn"]):
                flags.append(f"{pre} nameEn has Greek script: {p['nameEn']}")
        worst = 0.0
        for o in a["orders"]:
            for f in o["from"]:
                for t in o["to"]:
                    if placed(f) and placed(t):
                        worst = max(worst, km((f["lon"], f["lat"]), (t["lon"], t["lat"])))
        if worst > LONG_EDGE_KM:
            flags.append(f"{pre} edge {worst:.0f} km")
        by_xy: dict[tuple[float, float], set[str]] = {}
        for p in pts:
            if placed(p):
                by_xy.setdefault((p["lat"], p["lon"]), set()).add(p["nameEn"])
        for xy, names in by_xy.items():
            if len(names) > 1:
                flags.append(f"{pre} coincident {sorted(names)} at {xy}")
        n_pros = len(re.findall(r"προς", a["text"]))
        if n_pros > len(a["orders"]) and "note" not in a:
            flags.append(f"{pre} {n_pros}× «προς» but {len(a['orders'])} order(s) — "
                         "check the split")
        if n_pros and not any(o["to"] for o in a["orders"]) and "note" not in a:
            flags.append(f"{pre} «προς» in the text but no destination and no note")
        if a["type"] == "shelter_in_place" and any(o["to"] for o in a["orders"]):
            flags.append(f"{pre} shelter-in-place row with a destination")
        if not any(placed(p) for p in pts) and not a.get("title"):
            flags.append(f"{pre} no placed point and no title: {a['text'][:70]}…")
        sheet = " · ".join(
            (", ".join(p["nameEn"] + ("" if placed(p) else "?") for p in o["from"]) or "—")
            + " → "
            + (", ".join(p["nameEn"] + ("" if placed(p) else "?") for p in o["to"]) or "—")
            for o in a["orders"])
        print(f"{pre} | {sheet} | max edge {worst:.0f} km")
    print()
    print(f"{len(flags)} flags")
    for f in flags:
        print("  ·", f)
    return 1 if flags else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--overpass", action="store_true")
    ap.add_argument("--match", action="store_true")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.init:
        init()
    if args.overpass:
        overpass()
    if args.match:
        match()
    if args.audit:
        sys.exit(audit())
    if not any(vars(args).values()):
        ap.print_help()


if __name__ == "__main__":
    main()
