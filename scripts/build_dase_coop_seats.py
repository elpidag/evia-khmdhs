# -*- coding: utf-8 -*-
"""Find, organise and store the REGISTERED OFFICE of every ΔΑΣΕ forest
co-operative in the dataset (DATA_DECISIONS 2026-08-24).

Sources, in the order they are trusted:

1. **VIES** (`khmdhs/vies.py`) — captcha-free, anonymous, and unusually good
   for co-ops: they are registered under their village, so the record reads
   «ΣΙΔΗΡΟΧΩΡΙ 0 · 68400 - ΣΟΥΦΛΙ» — settlement, Τ.Κ. and reference town.
   This is the base layer.
2. **The signed contracts** — the Anti-nero gold standard, but ΔΑΣΕ
   συμφωνητικά mostly skip party seats: a minority state «… ΜΕ ΕΔΡΑ ΤΟ
   ΣΙΔΗΡΟΧΩΡΙ ΕΒΡΟΥ, ΣΟΥΦΛΙ, ΤΚ:68400 …». Where one does, the verbatim
   sentence is kept as evidence beside the register's values. The needle is
   anchored on the CO-OP's own ΑΦΜ so the awarding service's «που εδρεύει
   στη Λάρισα» can never be mistaken for the contractor's seat.
3. **ΓΕΜΗ is not a source here** — forest co-ops do not register in the
   commercial register (probed: `not_found`); under ν.4423/2016 they sit in
   the ΥΠΕΝ Μητρώο Δασικών Συνεταιριστικών Οργανώσεων, which has no public
   API.

The co-op's own contracts' Π.Ε. (`dase_contract_regions`) rides along as the
geocoder's validator — a village co-op logs in the area it sits in.

Usage:
    python scripts/build_dase_coop_seats.py            # sweep + merge
    python scripts/build_dase_coop_seats.py --limit 20 # a taste
    python scripts/build_dase_coop_seats.py --no-vies  # contracts only
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from khmdhs import vies                                    # noqa: E402
from webui import dase_queries as dq                       # noqa: E402

DB = ROOT / "data" / "processed" / "dase.sqlite"
CACHE = ROOT / "data" / "processed" / "dase_pdf_cache"
OUT = ROOT / "khmdhs" / "data" / "dase_coop_locations.json"
VIES_CACHE = ROOT / "data" / "processed" / "dase_vies_cache.json"

# the co-op party clause: «… ΜΕ ΕΔΡΑ ΤΟ ΣΙΔΗΡΟΧΩΡΙ ΕΒΡΟΥ, ΣΟΥΦΛΙ, ΤΚ:68400,
# ΑΦΜ 096067226 …» / «… ΠΟΥ ΕΔΡΕΥΕΙ ΣΤΗ ΝΟΤΙΑ … ΑΦΜ 099244449 …»
_SEAT = re.compile(r"(?:ΜΕ\s+ΕΔΡΑ|ΠΟΥ\s+ΕΔΡΕΥΕΙ\s+ΣΤ|ΕΔΡΕΥΕΙ\s+ΣΤ)")
_WINDOW = 420      # chars of party clause read around the co-op's own ΑΦΜ


def fold(s: str) -> str:
    d = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(ch for ch in d if not unicodedata.combining(ch))


def seat_sentence(text: str, vat: str) -> str | None:
    """The seat clause of the party whose ΑΦΜ is `vat` — anchored on the ΑΦΜ
    and read BACKWARDS, so the awarding service's own «εδρεύει» (which comes
    earlier in every contract, with the State's ΑΦΜ) can never be taken for
    the co-op's."""
    f = fold(text)
    digits = re.sub(r"\D", "", vat)
    for m in re.finditer(re.escape(digits), f):
        start = max(0, m.start() - _WINDOW)
        window = f[start:m.start()]
        hit = None
        for sm in _SEAT.finditer(window):     # the LAST one before the ΑΦΜ
            hit = sm
        if hit:
            frag = window[hit.start():]
            frag = re.sub(r"\s+", " ", frag).strip()
            # cut at the ΑΦΜ that follows, keeping the address part
            frag = re.split(r"\s*,?\s*(?:ΜΕ\s+)?Α\.?Φ\.?Μ", frag)[0].strip(" ,·")
            # the clause must describe the CO-OP, not the awarding service:
            # every ΔΑΣΕ contract states the service's own seat first («ΤΟ
            # ΔΑΣΑΡΧΕΙΟ ΧΑΛΚΙΔΑΣ ΠΟΥ ΕΔΡΕΥΕΙ ΣΤΗ ΧΑΛΚΙΔΑ …»), so the SUBJECT
            # standing immediately before the seat words decides. A co-op
            # name there accepts the clause; anything else refuses it
            # (25SYMV017324270 read «ΜΕ ΕΔΡΑ ΤΗΝ ΛΑΡΙΣΑ» — the Region's seat).
            before = window[max(0, hit.start() - 110):hit.start()]
            if not re.search(r"ΣΥΝΕΤΑΙΡΙΣΜ|ΔΑ\.?Σ\.?Ε|ΔΑΣΕ|Α\.?Δ\.?Σ\.?Ε|Ε\.?Δ\.?Α\.?Σ\.?Ε",
                             before):
                continue
            if 8 <= len(frag) <= 220:
                return frag
    return None


_STOP = {"ΕΔΡΑ", "ΤΟΠΙΚΗ", "ΚΟΙΝΟΤΗΤΑ", "ΚΟΙΝΟΤΗΤΑΣ", "ΔΗΜΟΥ", "ΔΗΜΟΤΙΚΗ",
         "ΕΝΟΤΗΤΑ", "ΕΝΟΤΗΤΑΣ", "ΚΟΙΝ", "ΕΔΡΕΥΕΙ", "ΝΟΜΟΥ", "ΠΕΡΙΦΕΡΕΙΑΚΗ"}


def _seat_place(clause: str) -> str | None:
    """The place a seat clause NAMES — its first real toponym, stripped of
    Greek case endings so «ΑΛΩΝΑ» and «ΑΛΩΝΩΝ» are one word.

    Only the first one: everything after it is the administrative container
    («… ΑΥΓΕΡΙΝΟΥ ΔΗΜΟΥ ΒΟΙΟΥ Π.Ε. ΚΟΖΑΝΗΣ»), and comparing whole clauses
    made two different seats of the same δήμος look identical because they
    share the prefecture's name."""
    for w in re.split(r"[^Α-Ω]+", fold(clause)):
        if len(w) < 5 or w in _STOP:
            continue
        # the ending list must include Ω: pdftotext writes «ΑΛΩΝΩ,Ν» for
        # «ΑΛΩΝΩΝ», and a 5-letter prefix absorbs what is left
        return re.sub(r"(ΟΥ|ΟΣ|ΟΝ|ΗΣ|ΗΝ|ΑΣ|ΑΝ|ΩΝ|Ω|Ο|Η|Α|Ι|Ε)$", "", w)[:5]
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--limit", type=int, default=0, help="stop after N co-ops")
    ap.add_argument("--no-vies", action="store_true", help="skip the register sweep")
    ap.add_argument("--sleep", type=float, default=1.1)
    args = ap.parse_args(argv)

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # the co-ops of the LIVE population only (dq.live_filter: not cancelled,
    # not superseded in-DB) — the excluded rows carry the registry's own
    # noise: duplicate postings, the not-a-co-op contracts whose party is a
    # construction company or ΔΕΘ-HELEXPO, and rows keyed under the State's
    # own ΑΦΜ 090273987. Resolving those would file a seat under an entity
    # that is not a co-op of this dataset.
    rows = conn.execute(f"""
        SELECT c.vat_number AS vat, c.name AS name,
               co.reference_number AS ref, co.cancelled AS cancelled
        FROM contractors c
        JOIN contracts co ON co.reference_number = c.reference_number
        WHERE {dq.live_filter()}
    """).fetchall()
    signed_of: dict[str, str] = {
        r["ref"]: (r["d"] or "")
        for r in conn.execute("SELECT reference_number AS ref, "
                              "contract_signed_date AS d FROM contracts")}
    pe_of: dict[str, dict[str, int]] = {}
    for r in conn.execute("""
        SELECT r.reference_number AS ref, r.region_pe AS pe FROM dase_contract_regions r
    """):
        pe_of.setdefault(r["ref"], {})[r["pe"]] = 1

    coops: dict[str, dict] = {}
    for r in rows:
        cv = dq.canonical_vat(r["vat"])
        if not cv:
            continue
        e = coops.setdefault(cv, {"vat": cv, "names": set(), "refs": [], "pes": {}})
        if r["name"]:
            e["names"].add(r["name"].strip())
        e["refs"].append(r["ref"])
        for pe in pe_of.get(r["ref"], {}):
            e["pes"][pe] = e["pes"].get(pe, 0) + 1

    vats = sorted(coops)
    if args.limit:
        vats = vats[:args.limit]
    print(f"{len(vats)} co-operatives to resolve", flush=True)

    cache: dict = json.loads(VIES_CACHE.read_text(encoding="utf-8")) if VIES_CACHE.exists() else {}
    out: dict[str, dict] = {}
    n_vies = n_contract = 0

    for i, vat in enumerate(vats, 1):
        c = coops[vat]
        entry: dict = {
            "vat": vat,
            "registry_names": sorted(c["names"]),
            "n_contracts": len(set(c["refs"])),
            # the Π.Ε. its contracts sit in, commonest first — the geocoder's
            # validator, never a stated seat
            "contract_pes": [p for p, _ in sorted(c["pes"].items(), key=lambda kv: -kv[1])],
        }

        # ---- 1 · the register
        if not args.no_vies:
            hit = cache.get(vat)
            if hit is None:
                try:
                    r = vies.lookup(vat)
                    hit = {"valid": bool(r.is_valid), "name": r.name,
                           "address_raw": r.address_raw, "street": r.street,
                           "postal_code": r.postal_code, "city": r.city,
                           "error": r.error}
                except Exception as exc:                      # noqa: BLE001
                    hit = {"valid": False, "error": f"{type(exc).__name__}: {exc}"[:160]}
                cache[vat] = hit
                VIES_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
                time.sleep(args.sleep)
            if hit.get("valid"):
                n_vies += 1
                entry["register"] = {
                    "source": "vies",
                    "name": hit.get("name"),
                    "settlement": hit.get("street"),      # VIES puts the village here
                    "postal_code": hit.get("postal_code"),
                    "city": hit.get("city"),              # the reference town
                    "address_raw": hit.get("address_raw"),
                }
            else:
                entry["register"] = {"source": "vies", "error": hit.get("error") or "invalid"}

        # ---- 2 · the co-op's own contracts, NEWEST FIRST (user, 2026-08-24):
        # a seat can be restated over the years — 997309155 signed as
        # «ΤΟΠ. ΚΟΙΝ. ΑΥΓΕΡΙΝΟΥ» in 2024 and «ΔΗΜ. ΕΝΟΤΗΤΑ ΝΕΑΠΟΛΗΣ» in 2025,
        # and it is the latest statement that describes the co-op today.
        # An earlier, differing statement is KEPT as `earlier_seat`, never
        # dropped: it is evidence of the move.
        statements: list[tuple[str, str, str]] = []          # (date, ref, clause)
        for ref in sorted(set(c["refs"])):
            p = CACHE / f"{ref}.txt"
            if not p.exists():
                continue
            s = seat_sentence(p.read_text(encoding="utf-8", errors="ignore"), vat)
            if s:
                statements.append((signed_of.get(ref) or "", ref, s))
        if statements:
            statements.sort(key=lambda x: (x[0], x[1]), reverse=True)
            dt, ref, s = statements[0]
            entry["contract_seat"] = {"ref": ref, "date": dt or None, "excerpt": s}
            n_contract += 1
            here = _seat_place(s)
            older = [(d0, r0, s0) for d0, r0, s0 in statements[1:]
                     if _seat_place(s0) and _seat_place(s0) != here]
            if older:
                d0, r0, s0 = older[0]                        # the newest differing one
                entry["earlier_seat"] = {"ref": r0, "date": d0 or None, "excerpt": s0}

        out[vat] = entry
        if i % 25 == 0:
            print(f"  {i}/{len(vats)} · register {n_vies} · contract evidence {n_contract}",
                  flush=True)

    doc = {
        "_doc": ("Registered office of every forest co-operative in the ΔΑΣΕ dataset "
                 "(DATA_DECISIONS 2026-08-24). `register` = the VIES record (the co-op's "
                 "village, its Τ.Κ. and the reference town); `contract_seat` = the "
                 "verbatim party clause of one of its own signed contracts, where one "
                 "states a seat; `contract_pes` = the Π.Ε. of its contracts, used to "
                 "validate a geocode, never as a stated seat. ΓΕΜΗ knows no forest "
                 "co-op — they register in the ΥΠΕΝ Μητρώο Δασικών Συνεταιριστικών "
                 "Οργανώσεων, which has no public API. Geocodes are added by "
                 "scripts/geocode_dase_coop_seats.py."),
        "_source": {"register": "VIES REST (EL)", "contracts": "dase_pdf_cache txt sidecars"},
        "coops": dict(sorted(out.items())),
    }
    if OUT.exists():                       # keep hand-curated additions
        old = json.loads(OUT.read_text(encoding="utf-8")).get("coops", {})
        for vat, e in doc["coops"].items():
            prev = old.get(vat, {})
            for key in ("lat", "lon", "geo_precision", "geo_note", "curated",
                        "flag", "flag_note"):
                if key in prev:
                    e[key] = prev[key]
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} co-ops → {OUT.relative_to(ROOT)} "
          f"(register {n_vies}, contract evidence {n_contract})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
