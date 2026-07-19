"""Resolve `vies_invalid` consortium VATs by inferring their home from
related rows in the contractors table or curated web findings.

VIES rejects consortium / κοινοπραξία umbrella VATs because they aren't
separately registered. To still place them on the flow map we look for a
member (same surname / same legal entity / sibling consortium) whose VAT
IS resolved, and inherit its home Π.Ε.

Each inference is a deliberate, manually-reviewed entry below — not a
heuristic — because consortium-member matching from a name alone is
fragile (Greek surnames are common). When matching was inconclusive we
leave the row as `consortium_unresolved` so we don't fabricate locations.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sqlite3
from pathlib import Path

from khmdhs.config import DEFAULT_DB

DATA_FILE = Path(__file__).parent / "data" / "contractor_locations.json"


# Each entry below is curated from:
# - DB inspection of co-occurring surnames in the contractors table, or
# - a targeted web search (DuckDuckGo + verified company-website / business
#   directory hit).
# `inferred_from` records the basis so audits stay possible.
INFERENCES: dict[str, dict] = {
    # 1. ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ → sibling ΓΚΑΡΓΚΑΝΙΤΗΣ ΠΑΝΑΓΙΩΤΗΣ (113411710) in Π.Ε. Νήσων
    "025751414": {
        "region_pe": "Π.Ε. Νήσων",
        "city": "ΣΑΛΑΜΙΝΑ",
        "source": "consortium_member_inferred",
        "notes": "Sibling-surname match: ΓΚΑΡΓΚΑΝΙΤΗΣ ΠΑΝΑΓΙΩΤΗΣ (VAT 113411710) is in Salamina. Confidence: medium (same surname family).",
        "inferred_from": "113411710",
    },
    # 2. ΚΟΙΝΟΠΡΑΞΙΑ ΓΚΑΡΑΝΑΤΣΙΟΥ - ΠΑΠΑΔΟΠΟΥΛΟΣ → unverifiable (rare surname, no DB or web hit)
    "996496315": {
        "region_pe": None,
        "city": None,
        "source": "consortium_unresolved",
        "notes": "ΓΚΑΡΑΝΑΤΣΙΟΥ surname not found in DB; ΠΑΠΑΔΟΠΟΥΛΟΣ ambiguous (1000s in Greece). Web search inconclusive. Project regions span Eurytania/Kozani/Larissa/Pieria/Trikala — multi-region operator.",
    },
    # 3. Γ. Ι. ΚΑΡΝΟΜΟΥΡΑΚΗΣ Α.Ε. → same legal entity under different VAT (800363439), Athens N.
    "996550190": {
        "region_pe": "Π.Ε. Βορείου Τομέα Αθηνών",
        "city": "ΜΑΡΟΥΣΙ",
        "source": "consortium_member_inferred",
        "notes": "Same legal entity under VAT 800363439 in Athens N. (Maroussi). VAT 996550190 likely a JV-registered alternate. Confidence: high.",
        "inferred_from": "800363439",
    },
    # 4. ΚΟΙΝΟΠΡΑΞΙΑ ΛΙΤΣΑ-ΕΔΡΑΙΟΣ → ΛΙΤΣΑ ΕΥΔΟΚΙΑ in sibling consortium 996605211 → Π.Ε. Νήσων
    "996604110": {
        "region_pe": "Π.Ε. Νήσων",
        "city": "ΣΑΛΑΜΙΝΑ",
        "source": "consortium_member_inferred",
        "notes": "Member ΛΙΤΣΑ ΕΥΔΟΚΙΑ also in resolved consortium 996605211 (Salamina). Confidence: high.",
        "inferred_from": "996605211",
    },
    # 5. ΚΟΙΝΟΠΡΑΞΙΑ ΛΑΜΠΙΡΗΣ-ΔΗΜΟΠΟΥΛΟΣ → web search suggests Portocheli (Π.Ε. Αργολίδας), unverified
    "996604620": {
        "region_pe": "Π.Ε. Αργολίδας",
        "city": "ΠΟΡΤΟΧΕΛΙ",
        "source": "consortium_member_inferred",
        "notes": "Web search (DuckDuckGo) suggested a ΛΑΜΠΙΡΗΣ ΓΕΩΡΓΙΟΣ in Portocheli (Argolida). Confidence: low — surname is common. Project regions in Peloponnese (Achaia/Ilia/Messinia) make a Peloponnesian home plausible.",
        "inferred_from": "web:duckduckgo",
    },
    # 6. Κ/ΞΙΑ ΛΙΑΡΗ-ΓΚΙΚΑΣ → ΓΚΙΚΑΣ ΑΘΑΝΑΣΙΟΣ (073533221) in Π.Ε. Κορινθίας
    "996666474": {
        "region_pe": "Π.Ε. Κορινθίας",
        "city": "ΚΟΡΙΝΘΟΣ",
        "source": "consortium_member_inferred",
        "notes": "Member ΓΚΙΚΑΣ ΑΘΑΝΑΣΙΟΣ resolved as 073533221 in Korinthia. Confidence: high (unique surname-firstname pair).",
        "inferred_from": "073533221",
    },
    # 7. ΚΟΙΝΟΠΡΑΞΙΑ ΤΑΣΚΟΥΔΗΣ-ΓΚΑΤΖΙΟΣ → both surnames in resolved Serres consortia
    "996714243": {
        "region_pe": "Π.Ε. Σερρών",
        "city": "ΣΕΡΡΕΣ",
        "source": "consortium_member_inferred",
        "notes": "Both members (ΤΑΣΚΟΥΔΗΣ, ΓΚΑΤΖΙΟΣ) appear in 3 sibling consortia all resolved to Serres. Confidence: very high.",
        "inferred_from": "996714083,996714741,998746814",
    },
    # 8. ΚΟΙΝΞΙΑ 3Κ ΤΕΧΝΙΚΗ-ΚΑΤΣΙΑΒΑΣ → web search: "3Κ ΤΕΧΝΙΚΗ ΕΜΠΟΡΙΚΗ" at Αγ. Λαύρας 86, Αθήνα
    "996813189": {
        "region_pe": "Π.Ε. Κεντρικού Τομέα Αθηνών",
        "city": "ΑΘΗΝΑ",
        "source": "consortium_member_inferred",
        "notes": "Web search: 3Κ ΤΕΧΝΙΚΗ ΕΜΠΟΡΙΚΗ Α.Ε. registered at ΑΓ. ΛΑΥΡΑΣ 86, Athens (Πατήσια). Confidence: medium.",
        "inferred_from": "web:acci_directory",
    },
    # 9. ΚΟΙΝΟΠΡΑΞΙΑ ΒΑΛΛΑΣ-ΟΙΚΟΝΟΜΟΥ → ΟΙΚΟΝΟΜΟΥ ΙΩΑΝΝΑ (031213597) in Π.Ε. Τρικάλων
    "996813233": {
        "region_pe": "Π.Ε. Τρικάλων",
        "city": "ΤΡΙΚΑΛΑ",
        "source": "consortium_member_inferred",
        "notes": "Member ΟΙΚΟΝΟΜΟΥ ΙΩΑΝΝΑ resolved as 031213597 in Trikala. Confidence: high (unique surname-firstname pair).",
        "inferred_from": "031213597",
    },
    # 10. BIODASOS-ΤΕΧΝΗ → web search: Trikala-based company
    "996813651": {
        "region_pe": "Π.Ε. Τρικάλων",
        "city": "ΤΡΙΚΑΛΑ",
        "source": "consortium_member_inferred",
        "notes": "Web search (DuckDuckGo, Facebook listing): BIODASOS based in Trikala. Confidence: medium.",
        "inferred_from": "web:duckduckgo",
    },
    # 11. Κ/ΞΙΑ ΠΑΠΠΑΣ-ΠΑΝΤΟΥΛΗΣ → ΠΑΝΤΟΥΛΗΣ ΦΩΤΙΟΣ (050232986) in Π.Ε. Δράμας
    "996831933": {
        "region_pe": "Π.Ε. Δράμας",
        "city": "ΔΡΑΜΑ",
        "source": "consortium_member_inferred",
        "notes": "Member ΠΑΝΤΟΥΛΗΣ ΦΩΤΙΟΣ ΤΟΥ ΕΥΑΓΓΕΛΟΥ resolved as 050232986 in Drama (same patronymic). Confidence: very high.",
        "inferred_from": "050232986",
    },
    # 12. ΓΕΩΓΝΩΜΩΝ Ο.Ε. (8-digit duplicate) → same as 998434068 in Π.Ε. Αχαΐας
    "98434068": {
        "region_pe": "Π.Ε. Αχαΐας",
        "city": "ΠΑΤΡΑ",
        "source": "consortium_member_inferred",
        "notes": "Same legal entity as VAT 998434068 (ΓΕΩΓΝΩΜΩΝ Ο.Ε. in Patra). The 8-digit form is a data-entry artifact. Confidence: very high.",
        "inferred_from": "998434068",
    },
    # --- Batch 2 (2026-07-18): consortium VATs from the antinero_supplement load ---
    # 13. Κ/Ξ ΣΙΔΕΡΗ ΜΑΡΙΑ ΤΟΥ ΔΗΜΗΤΡΙΟΥ - ΕΛ.ΤΕ. ΕΠΕ → lead member 036692199 in Π.Ε. Βορείου Τομέα Αθηνών
    "996674333": {
        "region_pe": "Π.Ε. Βορείου Τομέα Αθηνών",
        "city": None,
        "source": "consortium_member_inferred",
        "notes": "Lead member ΣΙΔΕΡΗ ΜΑΡΙΑ ΤΟΥ ΔΗΜΗΤΡΙΟΥ resolved as 036692199 (N. Athens). Exact name+patronymic match. Confidence: very high.",
        "inferred_from": "036692199",
    },
    # 14. Κ/Ξ ΙΩΑΝΝΗΣ ΔΡΑΜΗΤΙΝΟΣ ΚΑΙ ΣΙΑ ΕΕ - ΕΥΑΓΓΕΛΙΑ ΑΝΔΡΙΑΝΟΠΟΥΛΟΥ → lead's sibling entities in Π.Ε. Νοτίου Τομέα Αθηνών
    "996699548": {
        "region_pe": "Π.Ε. Νοτίου Τομέα Αθηνών",
        "city": None,
        "source": "consortium_member_inferred",
        "notes": "Lead ΙΩΑΝΝΗΣ ΔΡΑΜΗΤΙΝΟΣ ΚΑΙ ΣΙΑ Ε.Ε.: sibling consortia 802865853 and 996593557 both VIES-resolved to S. Athens. Confidence: high.",
        "inferred_from": "802865853,996593557",
    },
    # 15. Κ/Ξ ΦΙΛΑΝΤΑΡΑΚΗ ΜΑΡΙΑ ΤΟΥ ΙΩΑΝΝΗ - ΛΙΤΣΟΣ ΗΛΙΑΣ → lead member 033419558 in Π.Ε. Δυτικού Τομέα Αθηνών
    "996830790": {
        "region_pe": "Π.Ε. Δυτικού Τομέα Αθηνών",
        "city": None,
        "source": "consortium_member_inferred",
        "notes": "Lead member ΦΙΛΑΝΤΑΡΑΚΗ ΜΑΡΙΑ ΤΟΥ ΙΩΑΝΝΗ resolved as 033419558 (W. Athens). Exact name+patronymic match. Confidence: very high.",
        "inferred_from": "033419558",
    },
    # 16. ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚΗ – ΞΑΝΘΟΠΟΥΛΟΣ ΒΑΣΙΛΕΙΟΣ → both members in Π.Ε. Καβάλας
    "996870356": {
        "region_pe": "Π.Ε. Καβάλας",
        "city": "ΚΑΒΑΛΑ",
        "source": "consortium_member_inferred",
        "notes": "Both members resolved to Kavala: ΜΠΟΜΠΟΤΗ Κ.-Β. (044739770) and ΞΑΝΘΟΠΟΥΛΟΣ ΒΑΣΙΛΕΙΟΣ (102529416). Confidence: very high.",
        "inferred_from": "044739770,102529416",
    },
    # 17. Κ/Ξ ΠΑΠΑΓΕΩΡΓΑΚΗΣ ΠΑΝΑΓΙΩΤΗΣ – ΚΟΣΜΙΔΗΣ ΙΩΑΝΝΗΣ → ambiguous, left unresolved
    "996870694": {
        "region_pe": None,
        "city": None,
        "source": "consortium_unresolved",
        "notes": "ΚΟΣΜΙΔΗΣ ΙΩΑΝΝΗΣ matches two different resolved people (Kavala 996551289 member; Kozani 117925460) with no patronymic to disambiguate. ΠΑΠΑΓΕΩΡΓΑΚΗΣ not in DB; web search inconclusive (a Papageorgaki Bros landscaping firm exists in Metamorfosi, Athens, unverified). No safe inference.",
    },
    # 18. Κ/Ξ ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚΗ – ΚΑΦΕΤΖΗΣ ΔΗΜΗΤΡΙΟΣ → both members in Π.Ε. Καβάλας
    "996550834": {
        "region_pe": "Π.Ε. Καβάλας",
        "city": "ΚΑΒΑΛΑ",
        "source": "consortium_member_inferred",
        "notes": "Both members VIES-resolved to Kavala: ΜΠΟΜΠΟΤΗ Κ.-Β. (044739770) and ΚΑΦΕΤΖΗΣ ΔΗΜΗΤΡΙΟΣ ΤΟΥ ΓΕΩΡΓΙΟΥ (045351317). Confidence: very high.",
        "inferred_from": "044739770,045351317",
    },
    # 19. Κ/Ξ GREEN CONSTRUCTION ΑΤΕ – ΣΤΑΥΡΟΣ ΤΣΙΦΤΣΟΓΛΟΥ → lead member in Π.Ε. Ανατολικής Αττικής
    "996774829": {
        "region_pe": "Π.Ε. Ανατολικής Αττικής",
        "city": "Μαρκόπουλο Μεσογαίας",
        "source": "consortium_member_inferred",
        "notes": "Members split regions: lead GREEN CONSTRUCTION ΑΤΕ (998256075) is in Markopoulo, Π.Ε. Ανατολικής Αττικής; ΤΣΙΦΤΣΟΓΛΟΥ ΣΤΑΥΡΟΣ (035592572) is in Lagadas, Π.Ε. Θεσσαλονίκης. Attributed to the corporate lead member. Confidence: medium.",
        "inferred_from": "998256075,035592572",
    },
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m khmdhs.consortium_resolver")
    p.add_argument("--data", type=Path, default=DATA_FILE)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--dry-run", action="store_true",
                   help="Print planned changes without writing JSON")
    return p


def _save_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    today = dt.date.today().isoformat()
    data = json.loads(args.data.read_text(encoding="utf-8"))

    # Look up each inference's "inferred_from" sibling VAT to grab the source_url
    # for audit trail (only for DB-based inferences)
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)

    n_resolved = n_unresolved = n_already = 0
    for raw_vat, plan in INFERENCES.items():
        # Find the entry by whitespace-tolerant key (some keys have leading spaces)
        key = next((k for k in data if k.strip() == raw_vat), None)
        if key is None:
            logging.warning("VAT %s not found in JSON — skipping", raw_vat)
            continue
        entry = data[key]
        if entry.get("source") not in ("vies_invalid", "consortium_member_inferred", "consortium_unresolved"):
            logging.info("VAT %s already resolved (%s) — skipping", raw_vat, entry.get("source"))
            n_already += 1
            continue

        # Source URL: link to the audit basis where it's a sibling VAT
        from_id = plan.get("inferred_from", "")
        if from_id and not from_id.startswith("web:"):
            source_url = f"audit:contractor_locations#{from_id.split(',')[0]}"
        else:
            source_url = from_id  # 'web:duckduckgo' etc.

        update = dict(entry)
        update.update(
            address=None,
            postal_code=None,
            city=plan.get("city"),
            region_pe=plan.get("region_pe"),
            source=plan["source"],
            source_url=source_url,
            notes=plan["notes"],
            curated_at=today,
        )
        data[key] = update
        if plan.get("region_pe"):
            n_resolved += 1
        else:
            n_unresolved += 1
        logging.info(
            "%s %s → %s",
            "DRY" if args.dry_run else "SET",
            raw_vat,
            plan.get("region_pe") or "(left unresolved)",
        )

    conn.close()

    if not args.dry_run:
        _save_atomic(args.data, data)

    print()
    print("=" * 60)
    print(f"Consortium resolver — {len(INFERENCES)} entries reviewed")
    print(f"  resolved (region inferred):     {n_resolved}")
    print(f"  unresolved (no safe inference): {n_unresolved}")
    print(f"  already resolved (skipped):     {n_already}")
    print()
    print("Next: .venv/bin/python -m khmdhs.contractor_loader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
