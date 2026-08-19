# -*- coding: utf-8 -*-
"""REPORT-MODE audit of contract→authority links against the complete
ΥΠΕΝ unit vocabulary (DATA_DECISIONS 2026-08-17). Writes NOTHING to the
data — it re-runs the whitelist matcher over every in-scope Anti-nero
contract (title+items, then the cached PDF text separately) and every
ΔΑΣΕ operator-unit string, with the 32 directory-only ΔΔ/Δασαρχεία added
to the vocabulary, and reports:

  (a) directory-only units named in TITLE+ITEMS — the awarder may be a
      unit we don't track (real findings, human review each);
  (b) directory-only units appearing ONLY in the PDF text — expected
      letterhead/parent-chain noise; suppressed when the contract already
      links a child unit in the same Π.Ε. (hierarchy rule), listed
      otherwise;
  (c) ΔΑΣΕ operator units matching a directory-only unit — would change
      the dase region/map attribution if confirmed.

Output: data/processed/authority_link_audit.json + console summary.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sqlite3

from khmdhs.forest_loader import Matcher, fold, load_registry, pdf_text  # noqa: E402

DIR_FILE = ROOT / "khmdhs" / "data" / "forest_units_directory.json"
OUT = ROOT / "data" / "processed" / "authority_link_audit.json"


def pe_of_toponym(tail: str) -> str | None:
    """«ΕΥΒΟΙΑΣ» → «Π.Ε. Ευβοίας». The directory names a unit after the area it
    administers, which is what the hierarchy rule needs to compare against."""
    from khmdhs.greek_regions import PE_CENTROIDS
    want = fold(tail)
    for pe in PE_CENTROIDS:
        if fold(pe.replace("Π.Ε. ", "")) == want:
            return pe
    return None


def extended_registry() -> tuple[dict, dict[str, dict]]:
    registry, _gaz = load_registry()
    directory = json.loads(DIR_FILE.read_text(encoding="utf-8"))
    extra: dict[str, dict] = {}
    reg = {"authorities": dict(registry["authorities"])}
    for u in directory["units"]:
        if u["authority_name"] or u["unit_kind"] not in ("dd", "dx"):
            continue
        name = u["name"]
        tail = re.sub(r"^(ΔΑΣΑΡΧΕΙΟ|Δ/ΝΣΗ ΔΑΣΩΝ|ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ)\s+", "", name)
        tail = re.sub(r"^(Π\.Ε\.?|Ν\.|ΝΟΜΟΥ)\s+", "", tail).strip()
        if not tail:
            continue
        key = f"[DIR] {name}"
        reg["authorities"][key] = {"kind": u["unit_kind"], "aliases": [tail],
                                   "region_pe": pe_of_toponym(tail)}
        extra[key] = u
    return reg, extra


def main() -> int:
    reg, extra = extended_registry()
    matcher = Matcher(reg)
    kh = sqlite3.connect(ROOT / "data" / "processed" / "khmdhs.sqlite")
    kh.row_factory = sqlite3.Row

    current: dict[str, set] = {}
    for r in kh.execute("SELECT reference_number, authority_name FROM contract_forest_authorities"):
        current.setdefault(r["reference_number"], set()).add(r["authority_name"])
    auth_pe = {r["name"]: r["region_pe"] for r in kh.execute(
        "SELECT name, region_pe FROM forest_authorities")}

    report = {"title_items_hits": [], "pdf_only_hits": [], "pdf_suppressed": 0,
              "completion_act_hits": [], "act_suppressed": 0, "dase_unit_hits": []}
    rows = kh.execute("""
        SELECT c.reference_number ref, c.title,
               (SELECT group_concat(short_description, ' | ')
                FROM contract_objects o WHERE o.reference_number = c.reference_number) objs
        FROM contracts c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        WHERE s.in_scope = 1""").fetchall()
    for r in rows:
        ref = r["ref"]
        text = f"{r['title'] or ''} | {r['objs'] or ''}"
        ti_names = {n for n, _e in matcher.find(text)}
        ti_dir = {n for n in ti_names if n in extra}
        for n in sorted(ti_dir):
            ex = next(e for nn, e in matcher.find(text) if nn == n)
            report["title_items_hits"].append(
                {"ref": ref, "unit": extra[n]["name"], "excerpt": ex[:200],
                 "current_links": sorted(current.get(ref, []))})
        # PDF pass — only directory-only units NOT already found in title/items
        pt = pdf_text(ref)
        if pt:
            pdf_names = {n for n, _e in matcher.find(pt[:6000])}
            for n in sorted((pdf_names - ti_names)):
                if n not in extra:
                    continue
                # hierarchy rule: parent-chain noise if an existing link
                # already sits in the same Π.Ε. as this unit's toponym
                unit_pe_hint = fold(extra[n]["name"])
                cur_pes = {auth_pe.get(c) for c in current.get(ref, [])}
                suppressed = any(p and fold(p.replace("Π.Ε. ", ""))[:5] in unit_pe_hint
                                 for p in cur_pes)
                if suppressed:
                    report["pdf_suppressed"] += 1
                else:
                    ex = next(e for nn, e in matcher.find(pt[:6000]) if nn == n)
                    report["pdf_only_hits"].append(
                        {"ref": ref, "unit": extra[n]["name"], "excerpt": ex[:200],
                         "current_links": sorted(current.get(ref, []))})

    # Completion acts (Diavgeia): «…για την περιοχή αρμοδιότητας των Δασαρχείων
    # Πάρνηθας, Λαυρίου…». They became a source of the authority layer on
    # 2026-08-19, and the audit has to cover every source the layer uses — the
    # gap here is exactly how ΔΔ Ευβοίας stayed invisible for months.
    try:
        acts = kh.execute("""SELECT ada, cited_ref, attributed_ref, subject
                             FROM contract_completion_acts""").fetchall()
    except sqlite3.OperationalError:
        acts = []
    for a in acts:
        hits = matcher.find(a["subject"] or "")
        for n, ex in hits:
            if n not in extra:
                continue
            ref = a["attributed_ref"] or a["cited_ref"]
            unit_pe = reg["authorities"][n].get("region_pe")
            cur_pes = {auth_pe.get(c) for c in current.get(ref, [])}
            if unit_pe and unit_pe in cur_pes:
                report["act_suppressed"] += 1      # its own child unit is linked
                continue
            report["completion_act_hits"].append(
                {"ref": ref, "ada": a["ada"], "unit": extra[n]["name"],
                 "excerpt": ex[:200], "current_links": sorted(current.get(ref, []))})

    # ΔΑΣΕ side: operator-unit strings vs directory-only vocabulary
    from webui.dase_queries import live_filter
    dase = sqlite3.connect(ROOT / "data" / "processed" / "dase.sqlite")
    dase.row_factory = sqlite3.Row
    dir_fold = {" ".join(fold(e["name"]).split()): e["name"] for e in extra.values()}
    for r in dase.execute(f"""
        SELECT DISTINCT co.units_operator_name u, COUNT(*) n
        FROM contracts co WHERE {live_filter('co')}
          AND co.units_operator_name IS NOT NULL
        GROUP BY co.units_operator_name"""):
        f = " ".join(fold(r["u"]).split())
        if f in dir_fold:
            report["dase_unit_hits"].append({"unit": r["u"], "n_contracts": r["n"],
                                             "directory_name": dir_fold[f]})

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"title/items hits: {len(report['title_items_hits'])}")
    print(f"pdf-only hits (unsuppressed): {len(report['pdf_only_hits'])} "
          f"| suppressed as parent-chain noise: {report['pdf_suppressed']}")
    print(f"completion-act hits: {len(report['completion_act_hits'])} "
          f"| suppressed as parent-chain noise: {report['act_suppressed']}")
    print(f"dase unit hits: {len(report['dase_unit_hits'])}")
    print(f"→ {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
