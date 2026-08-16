# -*- coding: utf-8 -*-
"""Merge the ΥΠΕΝ directory (ypen_offices_cache/matched.json) and the
Diavgeia letterhead evidence (authority_letterhead_cache/letterheads.json)
into an additive per-entry `office` block in forest_authorities.json
(DATA_DECISIONS 2026-08-17). Resolution policy:

- Τ.Κ. confirmed by the authority's own letterhead → ΥΠΕΝ address block
  kept whole, evidence = the confirming ΑΔΑ + verbatim excerpt.
- ΥΠΕΝ Τ.Κ. missing/garbled but the letterhead shows the town's code
  unambiguously → letterhead value (ΑΔΑ evidence).
- Letterhead exposes a ministry-page typo (Γουμένισσα 613 00 vs 63100)
  → letterhead wins, difference recorded in `note`.
- Same-town granularity variants → ΥΠΕΝ street+Τ.Κ. pair kept coherent,
  letterhead variant recorded in `note`.
- Letterhead inconclusive (font-mangled digits only) → ΥΠΕΝ value with
  `note`; nothing invented.

Aliases and every pre-existing registry field stay untouched — the file
still feeds the Anti-nero matcher.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FA = ROOT / "khmdhs" / "data" / "forest_authorities.json"
YPEN = ROOT / "data" / "processed" / "ypen_offices_cache" / "matched.json"
LH = ROOT / "data" / "processed" / "authority_letterhead_cache" / "letterheads.json"

# hand-reviewed resolutions for every non-confirmed case (2026-08-17)
OVERRIDES: dict[str, dict] = {
    "Δασαρχείο Γουμένισσας": {
        "tk": "61300",
        "note": ("Το ΥΠΕΝ αναγράφει Τ.Κ. 63100 (κωδικός Πολυγύρου — προφανής "
                 "αναγραμματισμός)· η επιστολόχαρτη κεφαλίδα της ίδιας της "
                 "υπηρεσίας γράφει «Τ.Κ.: 613 00» (Γουμένισσα)."),
        "evidence_ada": "9ΒΟΨ4653Π8-299",
        "excerpt": "Τ.Κ. : 613 00 … e-mail: das-gou@eedpmt.ypen.gr",
    },
    "Δασαρχείο Λίμνης": {
        "tk": "34005", "city": "Λίμνη",
        "note": "Η σελίδα ΥΠΕΝ δίνει μόνο «Λίμνη Εύβοιας»· το Τ.Κ. 34005 από την κεφαλίδα.",
    },
    "Δασαρχείο Κοζάνης": {
        "note": ("Τ.Κ. άλυτο: η σελίδα ΥΠΕΝ γράφει «Περιοχή ΖΕΠ 51 00» "
                 "(κολοβό) και οι κεφαλίδες δεν εξάγουν καθαρό κωδικό — "
                 "geocoding μέσω οδού/πόλης."),
        "street": "Περιοχή ΖΕΠ", "city": "Κοζάνη",
    },
    "Δασαρχείο Αλεξανδρούπολης": {
        "note": "Κεφαλίδα: 68132 (ίδια πόλη, παραλλαγή του 68131 της σελίδας ΥΠΕΝ)."},
    "Δασαρχείο Ξάνθης": {
        "note": "Κεφαλίδα: 67133 (ειδικός τομέας Ξάνθης· το ΥΠΕΝ δίνει τον γενικό 67100)."},
    "Δασαρχείο Πύργου": {
        "note": "Κεφαλίδα: 27131 (ειδικός κωδικός Πύργου· το ΥΠΕΝ δίνει τον γενικό 27100)."},
    "Δασαρχείο Καλαμάτας": {
        "note": "Κεφαλίδα: 24131 (ειδικός κωδικός Καλαμάτας· το ΥΠΕΝ δίνει τον γενικό 24100)."},
    "Δασαρχείο Χαλκίδας": {
        "note": "Κεφαλίδα: 34100 (γενικός· το ΥΠΕΝ δίνει τον ειδικό 34133 — ίδια πόλη)."},
    "Δασαρχείο Λαγκαδά": {"note": "Κεφαλίδες δυσανάγνωστες (mangled ψηφία) — τιμή ΥΠΕΝ."},
    "Δασαρχείο Λαυρίου": {"note": "Κεφαλίδες δυσανάγνωστες — τιμή ΥΠΕΝ."},
    "Δασαρχείο Λάρισας": {
        "note": "Κεφαλίδες ασαφείς (μόνο 40003/Αγιάς ορατό σε παραπομπές) — τιμή ΥΠΕΝ."},
    "Διεύθυνση Δασών Λάρισας": {"note": "Κεφαλίδες δυσανάγνωστες — τιμή ΥΠΕΝ."},
    "Δασαρχείο Περτουλίου": {
        "note": ("Δεν είναι μονάδα ΥΠΕΝ — το δάσος Περτουλίου διοικείται από "
                 "το Ταμείο Διοίκησης & Διαχείρισης Πανεπιστημιακών Δασών "
                 "(Α.Π.Θ.)· απουσιάζει από τον κατάλογο ΥΠΕΝ και τη Διαύγεια "
                 "του ΥΠΕΝ. Η έδρα μένει στο κεντροειδές δήμου."),
    },
}


def main() -> int:
    fa = json.loads(FA.read_text(encoding="utf-8"))
    ypen = {m["authority"]: m for m in json.loads(YPEN.read_text(encoding="utf-8"))}
    lh = {r["authority"]: r for r in json.loads(LH.read_text(encoding="utf-8"))}
    today = date.today().isoformat()
    n_conf = n_note = 0
    for name, entry in fa["authorities"].items():
        y = ypen.get(name) or {}
        d = lh.get(name) or {}
        ov = OVERRIDES.get(name) or {}
        office = {
            "street": ov.get("street", y.get("street")),
            "tk": ov.get("tk", y.get("tk")),
            "city": ov.get("city", y.get("city")),
            "phones": (y.get("phones") or [])[:2],
            "emails": (y.get("emails") or d.get("emails") or [])[:1],
            "source": f"ypen.gov.gr επιθεώρηση «{y.get('inspectorate')}» ({today})"
                      if y else None,
        }
        ada = ov.get("evidence_ada", d.get("evidence_ada"))
        if ada:
            office["evidence_ada"] = ada
            office["excerpt"] = ov.get("excerpt", d.get("excerpt"))
            n_conf += 1
        if ov.get("note"):
            office["note"] = ov["note"]
            n_note += 1
        entry["office"] = {k: v for k, v in office.items() if v}
    FA.write_text(json.dumps(fa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n_tk = sum(1 for e in fa["authorities"].values() if e["office"].get("tk"))
    print(f"office blocks written: {len(fa['authorities'])} | with Τ.Κ.: {n_tk} "
          f"| letterhead-evidenced: {n_conf} | noted differences: {n_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
