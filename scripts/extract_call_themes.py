"""Work themes for TITLE-SILENT contracts, read from the CALL's works enumeration.

87 in-scope contracts name no specific work in their descriptive title.
The user found (25SYMV016959652 / 25PROC016718138, DATA_DECISIONS
2026-08-22) that the πρόσκληση's «Συνοπτική περιγραφή αντικειμένου»
carries a lot-specific works enumeration — «Οι ως άνω εργασίες αφορούν
σε: i) … ii) …» — itemised per Δασαρχείο. This script proposes themes
from THAT sentence only:

* single-lot call → the whole enumeration is the contract's work;
* multi-lot call → only the items naming the contract's own Δασαρχεία
  (the forest layer says which those are);
* a call carrying only the programme menu proposes nothing — the
  2026-08-19 rejection of the menu stands.

PROPOSALS ONLY. Verdicts are written by hand into
khmdhs/data/contract_work_themes.json `_overrides` (entry source
`call:<PROC ΑΔΑΜ>`, verbatim excerpt each), which the details extractor
merges last on every regeneration.

Usage: .venv/Scripts/python.exe scripts/extract_call_themes.py
Writes data/processed/call_themes_review.json (gitignored).
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from khmdhs import work_themes as wt  # noqa: E402
from khmdhs.config import DEFAULT_DB  # noqa: E402

CACHE = ROOT / "data" / "processed" / "pdf_cache"
OUT = ROOT / "data" / "processed" / "call_themes_review.json"


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))


# the works enumeration: from the anchor to the sentence that sums it
# («Το συνολικό …») or the next numbered section
ANCHOR = re.compile(r"ΕΡΓΑΣΙΕΣ\s+ΑΦΟΡΟΥΝ\s+ΣΕ|ΑΦΟΡΟΥΝ\s+ΣΕ\s*:")
STOP = re.compile(r"ΤΟ\s+ΣΥΝΟΛΙΚ|Η\s+ΑΚΡΙΒΗΣ\s+ΠΕΡΙΓΡΑΦΗ|\n\s*\d+\.\s")
ITEM = re.compile(r"(?:^|[\s(])((?:i{1,3}|iv|v|vi{0,3}|ix|x)\))", re.I)
# 2023 phase-III dialect: a COLLECTIVE purpose clause naming the works of
# the whole call («…αφορούν στην πυροπροστασία, μέσω συγκεκριμένων
# επεμβάσεων καθαρισμού … και τη συντήρηση …») — flagged, since it is not
# itemised per lot
PURPOSE = re.compile(r"ΑΦΟΡΟΥΝ\s+ΣΤΗΝ\s+ΠΥΡΟΠΡΟΣΤΑΣΙΑ\s*,\s*ΜΕΣΩ")
PURPOSE_STOP = re.compile(r"ΓΙΑ\s+ΤΗΝ\s+ΑΠΟΤΡΟΠΗ|ΕΧΟΝΤΑΣ\s+ΩΣ")
# ΕΣΑ/2023 Εύβοια dialect: the works live in the QUOTED titles of the
# approved studies, one per ΥΠΟΕΡΓΟ («…ήτοι: «Μελέτη …»»)
STUDY_TITLE = re.compile(r"Η\s*Η?\s*ΤΟΙ\s*:")  # phase-II fonts mangle «ήτοι» into «ηή τοι»
TMIMA = re.compile(r"ΓΙΑ\s+ΤΟ\s+ΤΜΗΜΑ\s+([Α-Ω])\s*:")


def enumeration(text: str) -> tuple[str | None, str]:
    """The verbatim works description and its dialect, or (None, "")."""
    f = fold(text)
    m = ANCHOR.search(f)
    if m:
        stop = STOP.search(f, m.end())
        end = stop.start() if stop else min(len(f), m.end() + 2400)
        return text[m.start():end].strip(), "enumeration"
    m = PURPOSE.search(f)
    if m:
        stop = PURPOSE_STOP.search(f, m.end())
        end = stop.start() if stop else min(len(f), m.end() + 700)
        return text[max(0, m.start() - 160):end].strip(), "purpose"
    ms = list(STUDY_TITLE.finditer(f))
    if ms:
        parts = []
        for sm in ms[:6]:
            parts.append(text[max(0, sm.start() - 260):sm.end() + 420])
        return "\n---\n".join(p.strip() for p in parts), "study_titles"
    return None, ""


def tmima_of(sentence: str, stems: list[str]) -> tuple[str, bool]:
    """Where a call describes works «Για το Τμήμα Α: … Για το Τμήμα Β: …»,
    keep only the Τμήμα naming the contract's own services."""
    f = fold(sentence)
    marks = list(TMIMA.finditer(f))
    if not marks:
        return sentence, False
    segs = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(sentence)
        segs.append(sentence[m.start():end])
    kept = [s for s in segs if any(st in fold(s) for st in stems)]
    if len(kept) == 1:
        return kept[0], False
    return sentence, True  # none or several matched — flag for the reader


def items_of(sentence: str) -> list[str]:
    """The i) ii) … items of the enumeration, verbatim."""
    marks = list(ITEM.finditer(sentence))
    if not marks:
        return [sentence]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(sentence)
        out.append(sentence[m.start():end].strip(" ,;·"))
    return out


def toponyms(names: list[str]) -> list[str]:
    """Folded toponym stems of the contract's authorities («ΔΑΣΑΡΧΕΙΟ
    ΧΑΛΚΙΔΑΣ» → ΧΑΛΚΙΔ), tolerant of genitive endings."""
    stems = []
    for n in names:
        for w in fold(n).replace("Δ/ΝΣΗ", " ").split():
            if w in ("ΔΑΣΑΡΧΕΙΟ", "ΔΙΕΥΘΥΝΣΗ", "ΔΑΣΩΝ", "Π.Ε.", "ΝΟΜΟΥ", "&", "ΚΑΙ"):
                continue
            if len(w) >= 5:
                stems.append(w[:-2] if len(w) > 6 else w[:-1])
    return stems


def main() -> int:
    kh = sqlite3.connect(DEFAULT_DB)
    kh.row_factory = sqlite3.Row
    silent = [r[0] for r in kh.execute("""
        SELECT reference_number FROM contract_scope WHERE in_scope = 1
        AND reference_number NOT IN
            (SELECT reference_number FROM contract_work_themes)
        ORDER BY reference_number""")]

    rows = []
    for ref in silent:
        calls = [r[0] for r in kh.execute(
            "SELECT DISTINCT adam FROM contract_families"
            " WHERE reference_number=? AND kind='notice'", (ref,))]
        auth = [r[0] for r in kh.execute(
            "SELECT authority_name FROM contract_forest_authorities"
            " WHERE reference_number=?", (ref,))]
        sibs = 0
        if calls:
            q = ",".join("?" * len(calls))
            sibs = kh.execute(f"""
                SELECT COUNT(DISTINCT cf.reference_number) FROM contract_families cf
                JOIN contract_scope s ON s.reference_number = cf.reference_number
                 AND s.in_scope = 1
                WHERE cf.kind='notice' AND cf.adam IN ({q})""", calls).fetchone()[0]
        row = {"ref": ref, "calls": calls, "lots": sibs,
               "authorities": auth, "status": None, "call": None,
               "dialect": None, "flagged": False,
               "sentence": None, "items": [], "kept": [], "proposed": []}
        rows.append(row)
        got = None
        for adam in calls:
            p = CACHE / f"{adam}.txt"
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            sent, dialect = enumeration(text)
            if sent:
                got = (adam, sent, dialect)
                break
        if not calls:
            row["status"] = "no_call"
            continue
        if got is None:
            row["status"] = "no_enumeration"
            continue
        adam, (sent, dialect) = got[0], (got[1], got[2])
        row["call"], row["dialect"] = adam, dialect
        row["sentence"] = " ".join(sent.split())
        stems = toponyms(auth)
        flagged = False
        if dialect == "enumeration":
            seg, flagged = tmima_of(row["sentence"], stems)
            its = items_of(seg)
            row["items"] = its
            if sibs <= 1 and not TMIMA.search(fold(row["sentence"])):
                kept = its
            else:
                kept = [it for it in its if any(s in fold(it) for s in stems)]
                if not kept:
                    kept = its
                    flagged = True
        else:
            kept = [row["sentence"]]
            flagged = True  # collective clause or study titles — read by hand
        row["kept"] = kept
        joined = "  ".join(kept)
        row["proposed"] = [{"key": h.key, "excerpt": h.excerpt}
                           for h in wt.read_call(joined)]
        row["flagged"] = flagged
        row["status"] = (("flagged_" + dialect) if flagged else
                         "proposed" if row["proposed"] else "kept_but_no_theme")

    from collections import Counter
    st = Counter(r["status"] for r in rows)
    OUT.write_text(json.dumps({"stats": dict(st), "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(dict(st))
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
