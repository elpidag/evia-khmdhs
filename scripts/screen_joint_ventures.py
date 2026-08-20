"""Screen every in-scope contractor for «is this a joint venture?».

Why this exists: the membership curation of 2026-08-20 swept the ventures by
asking ΓΕΜΗ what each contractor IS (`gemi_legal_type = 'Κοινοπραξία'`) and by
reading the registry name. Both are register facts, and a register can be
silent: ΑΦΜ 996514860 «ΤΣΙΑΝΑΒΑΣ ΓΕΩΡΓΙΟΣ – Μ.&Κ. ΤΕΧΝΙΚΑ ΕΡΓΑ Α.Ε.» is in no
ΓΕΜΗ at all and its registry name carries no marker, so a €4,45M venture was
missed until its own contract was read.

The authoritative statement is the one the parties signed:

    «… και 2. η κοινοπραξία με την επωνυμία «…», με έδρα …, με ΑΦΜ 996514860 …»

So this screen reads the CHAIN of every in-scope contract (46 tips are cover
notes — DATA_DECISIONS 2026-08-18), finds each contractor's own ΑΦΜ in the
text, and looks back one party-clause window for a venture word. Boilerplate
«σε περίπτωση κοινοπραξίας…» sits in every ΕΣΥ, which is why the anchor is the
contractor's OWN ΑΦΜ and not the word alone.

Reports three signals per contractor (document / ΓΕΜΗ / name) and exits 1 when
a contractor any signal calls a venture is absent from the curated
`khmdhs/data/consortium_members.json`.

    .venv/Scripts/python.exe -m scripts.screen_joint_ventures [--db path] [-v]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.config import DEFAULT_DB
from khmdhs.scope import _HOMOGLYPHS

ROOT = Path(__file__).resolve().parent.parent
PDF_CACHE = ROOT / "data" / "processed" / "pdf_cache"
CURATED = ROOT / "khmdhs" / "data" / "consortium_members.json"
CORRECTIONS = ROOT / "khmdhs" / "data" / "contract_corrections.json"

# The party clause names the venture, its seat and then its ΑΦΜ; 500 chars
# covers the longest one on file («ΚΟΙΝΟΠΡΑΞΙΑ Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.-ΜΕΣΟΓΕΙΟΣ
# Α.Ε.(ΑΝΑΔΑΣΩΣΕΙΣ)», seat, ΔΟΥ) without reaching the previous party.
WINDOW = 500

# Folded like the text they meet. «ΕΝΩΣΗ» alone is useless — «Ευρωπαϊκή Ένωση»
# is in every RRF recital — so only the noun phrases that name a bidder.
VENTURE_WORDS = ("ΚΟΙΝΟΠΡΑΞ", "ΚΟΙΝΟΠΡΑΚΤ", "Κ/Ξ", "ΣΥΜΠΡΑΞ",
                 "ΕΝΩΣΗ ΕΤΑΙΡ", "ΕΝΩΣΗΣ ΕΤΑΙΡ", "ΕΝΩΣΗ ΟΙΚΟΝΟΜΙΚΩΝ",
                 "ΕΝΩΣΗΣ ΟΙΚΟΝΟΜΙΚΩΝ", "ΕΝΩΣΗ ΠΡΟΣΩΠΩΝ", "ΕΝΩΣΗΣ ΠΡΟΣΩΠΩΝ")


def _length_preserving_table() -> dict[int, str]:
    """One char in, one char out — so an offset found in the folded text points
    at the same place in the raw text and excerpts can be cut from the
    ORIGINAL. NFD+strip would shorten the string by every accent it removes."""
    t: dict[int, str] = {}
    for cp in range(0x20, 0x2000):
        ch = chr(cp)
        base = "".join(c for c in unicodedata.normalize("NFD", ch)
                       if not unicodedata.combining(c))
        if len(base) != 1:
            continue
        # applied BEFORE .upper(), because «ΐ».upper() is three characters and
        # «ß».upper() is two — either would shift every offset after it
        up = base.upper()
        out = up if len(up) == 1 else up[:1]
        if out != ch:
            t[cp] = out
    return t


_UNACCENT = _length_preserving_table()


def fold(s: str | None) -> str:
    return (s or "").translate(_UNACCENT).upper().translate(_HOMOGLYPHS)


# Phase-II PDFs put every accent in as a separate letter («αποτελουύμενης»,
# «Κοινοπραξιίας») and pdftotext sprinkles spaces into words. So the needles
# are matched loosely: one stray vowel allowed after a vowel, one stray space
# anywhere — the rule `contract_durations` already proved on this corpus.
_VOWELS = fold("ΑΕΗΙΟΥΩ")


def loose(word: str) -> re.Pattern:
    out = []
    for ch in fold(word):
        out.append(re.escape(ch) if ch != " " else r"\s+")
        if ch in _VOWELS:
            out.append(f"[{_VOWELS}]?")
        if ch != " ":
            out.append(r"\s?")
    return re.compile("".join(out))


FOLDED_WORDS = tuple(fold(w) for w in VENTURE_WORDS)
LOOSE_WORDS = tuple(loose(w) for w in VENTURE_WORDS)


def vat_regex(vat: str) -> re.Pattern:
    """pdftotext splits digit runs («ΑΦΜ 09027 3987»), so allow gaps."""
    return re.compile(r"\s*".join(re.escape(d) for d in vat))


def chain_of(ref: str, prev: dict[str, str | None]) -> list[str]:
    out, cur, seen = [], ref, set()
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = prev.get(cur)
    return out


def read_chain(refs: list[str]) -> str:
    parts = []
    for r in refs:
        p = PDF_CACHE / f"{r}.txt"
        if p.exists():
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return " ".join(" ".join(parts).split())


def document_signal(text_folded: str, vat: str) -> tuple[bool, str]:
    """True + the verbatim window where the signed text calls this ΑΦΜ's
    holder a venture."""
    for m in vat_regex(vat).finditer(text_folded):
        back = text_folded[max(0, m.start() - WINDOW):m.start()]
        for w in LOOSE_WORDS:
            hit = w.search(back)
            if hit:
                return True, back[hit.start():] + text_folded[m.start():m.end() + 30]
    return False, ""


def joint_party_contracts() -> set[str]:
    """Contracts curated as signed by SEVERAL parties. Their party clause names
    a κοινοπραξία that never got an ΑΦΜ of its own (22SYMV010795606), so the
    firms are recorded as the contracting parties and the even split does the
    rest — there is no venture entity to curate, and the screen must not keep
    asking for one."""
    try:
        data = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return set()
    return {k for k, fix in data.items()
            if isinstance(fix, dict)
            and isinstance(fix.get("contractor_party"), list)
            and len(fix["contractor_party"]) > 1}


def screen(db_path: Path = DEFAULT_DB) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    prev = {r["reference_number"]: r["prev_reference_no"]
            for r in conn.execute("SELECT reference_number, prev_reference_no "
                                  "FROM contracts")}
    loc = {r["vat_number"]: dict(r) for r in conn.execute(
        "SELECT vat_number, legal_name, gemi_legal_type FROM contractor_locations")}
    rows = conn.execute(
        "SELECT co.reference_number ref, co.vat_number vat, co.name name "
        "FROM contractors co JOIN contract_scope s USING (reference_number) "
        "WHERE s.in_scope = 1 AND co.vat_number IS NOT NULL").fetchall()
    conn.close()

    parties: dict[str, int] = {}
    for r in rows:
        parties[r["ref"]] = parties.get(r["ref"], 0) + 1

    joint = joint_party_contracts()
    found: dict[str, dict] = {}
    texts: dict[str, str] = {}
    for r in rows:
        vat, ref = r["vat"].strip(), r["ref"]
        e = found.setdefault(vat, {"vat": vat, "name": r["name"], "contracts": [],
                                   "signals": set(), "excerpt": "", "source": ""})
        e["contracts"].append(ref)
        if ref not in texts:
            texts[ref] = fold(read_chain(chain_of(ref, prev)))
        ok, excerpt = document_signal(texts[ref], vat)
        if ok:
            e["signals"].add("joint_party" if ref in joint else "document")
            if not e["excerpt"]:
                e["excerpt"], e["source"] = excerpt, ref
        l = loc.get(vat) or {}
        if l.get("gemi_legal_type") == "Κοινοπραξία":
            e["signals"].add("gemi")
        names = fold(r["name"]) + " " + fold(l.get("legal_name"))
        if any(w in names for w in FOLDED_WORDS):
            e["signals"].add("name")
    return {"entities": found,
            "multi_party": sorted(k for k, n in parties.items() if n > 1)}


# Words that introduce the members INSIDE a party clause. The first three do
# it directly; «ΣΥΣΤΑΣΗΣ» catches «δυνάμει του … συμφωνητικού σύστασης
# κοινοπραξίας», which names the constituting document rather than the firms.
ENUM_WORDS = ("ΑΠΟΤΕΛΟΥΜΕΝ", "ΜΕΛΗ ΤΗΣ", "ΣΥΝΕΣΤΗΣΑΝ", "ΣΥΣΤΑΣΗΣ")
LOOSE_ENUM = tuple(loose(w) for w in ENUM_WORDS)
_NINE = re.compile(r"(?<!\d)(\d[\s]?){9}(?!\d)")
# «23PROC012517133» ends in nine digits that are not anybody's ΑΦΜ
_ADAM_TAIL = re.compile(r"(SYMV|PROC|AWRD|PAY|REQ|NOTICE|DIAB)\s?$", re.I)
AFTER = 1800


def party_clause(raw: str, vat: str) -> tuple[int, int] | None:
    """Where the signed text introduces this ΑΦΜ's holder as a venture:
    (start of the venture word, end of the ΑΦΜ). Offsets index `raw`."""
    f = fold(raw)
    for m in vat_regex(vat).finditer(f):
        back = f[max(0, m.start() - WINDOW):m.start()]
        for w in FOLDED_WORDS:
            i = back.find(w)
            if i >= 0:
                return max(0, m.start() - WINDOW) + i, m.end()
    return None


def enumeration(raw: str, vat: str) -> dict | None:
    """The members a party clause names, if it names any: the verbatim clause,
    which introducing word it used, and every OTHER ΑΦΜ inside it with the
    words around it — the representative's own ΑΦΜ sits in the same sentence,
    and a person signing for a member is not a member."""
    span = party_clause(raw, vat)
    if not span:
        return None
    start, afm_end = span
    clause = raw[start:min(len(raw), afm_end + AFTER)]
    folded = fold(clause)
    words = [w for w, pat in zip(ENUM_WORDS, LOOSE_ENUM) if pat.search(folded)]
    others = []
    for m in _NINE.finditer(clause):
        other = re.sub(r"\s", "", m.group(0))
        if other in (vat, "090273987") or any(o["vat"] == other for o in others):
            continue
        if _ADAM_TAIL.search(clause[max(0, m.start() - 8):m.start()]):
            continue
        others.append({"vat": other,
                       "context": " ".join(clause[max(0, m.start() - 160):
                                                  m.end() + 20].split())})
    return {"clause": " ".join(clause.split()), "enum_words": words,
            "candidates": others}


def uncurated(db_path: Path = DEFAULT_DB) -> dict[str, dict]:
    """The screen's finding, for the guard test: ventures no curation knows."""
    curated = {k for k in json.loads(CURATED.read_text(encoding="utf-8"))
               if not k.startswith("_")}
    return {v: e for v, e in screen(db_path)["entities"].items()
            if (e["signals"] - {"joint_party"}) and v not in curated}


def report_members(db_path: Path = DEFAULT_DB) -> int:
    """Second pass: what does each venture's own contract say about its
    members? The 2026-08-20 curation read the AWARD acts and the προσκλήσεις;
    three party clauses turned out to enumerate the members themselves."""
    data = json.loads(CURATED.read_text(encoding="utf-8"))
    curated = {k: v for k, v in data.items() if not k.startswith("_")}
    res = screen(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    prev = {r[0]: r[1] for r in conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts")}
    conn.close()

    news = 0
    for vat in sorted(set(curated) | {v for v, e in res["entities"].items()
                                      if e["signals"]}):
        e = res["entities"].get(vat, {})
        cur = curated.get(vat, {})
        known = {m["vat"] for m in (cur.get("members") or [])}
        for ref in e.get("contracts", []):
            enum = enumeration(read_chain(chain_of(ref, prev)), vat)
            if not enum or not enum["enum_words"] or not enum["candidates"]:
                continue
            fresh = [c for c in enum["candidates"] if c["vat"] not in known]
            if not fresh:
                continue
            news += 1
            print(f"\n{vat}  {(cur.get('name') or e.get('name') or '')[:64]}")
            print(f"  curated: {'members ' + ', '.join(sorted(known)) if known else 'MEMBERS UNDOCUMENTED' if cur else 'NOT CURATED'}")
            print(f"  {ref} says «{', '.join(enum['enum_words'])}»:")
            for c in fresh:
                print(f"    ΑΦΜ {c['vat']} — …{c['context']}…")
    print(f"\n{news} party clause(s) name an ΑΦΜ the curation does not carry.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.screen_joint_ventures")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print the party clause behind every document signal")
    ap.add_argument("--members", action="store_true",
                    help="re-read every venture's party clause and report the "
                         "members it names against the curated file")
    args = ap.parse_args(argv)

    if args.members:
        return report_members(args.db)

    res = screen(args.db)
    curated = {k for k in json.loads(CURATED.read_text(encoding="utf-8"))
               if not k.startswith("_")}
    ventures = {v: e for v, e in res["entities"].items() if e["signals"]}
    joint_only = {v for v, e in ventures.items()
                  if not (e["signals"] - {"joint_party"})}
    missing = {v: e for v, e in ventures.items()
               if v not in curated and v not in joint_only}
    silent = sorted(curated - set(ventures))

    print(f"{len(res['entities'])} in-scope contractors screened — "
          f"{len(ventures)} answer as a joint venture "
          f"({len(curated)} curated)\n")
    for v, e in sorted(ventures.items()):
        mark = "  " if v in curated or v in joint_only else "!!"
        print(f"{mark} {v}  {'+'.join(sorted(e['signals'])):<20} "
              f"{(e['name'] or '')[:52]:<54} {len(e['contracts'])} contract(s)")
        if args.verbose and e["excerpt"]:
            print(f"     [{e['source']}] …{e['excerpt'][:220]}…")
    if silent:
        print(f"\ncurated but no signal in the screen ({len(silent)}): "
              f"{', '.join(silent)}")
    if joint_only:
        print()
        print(f"signed a contract jointly, with no venture ΑΦΜ to curate "
              f"({len(joint_only)}): {', '.join(sorted(joint_only))}")
    if res["multi_party"]:
        print(f"\ncontracts signed by more than one party "
              f"({len(res['multi_party'])}): {', '.join(res['multi_party'])}")
    if missing:
        print(f"\nNOT CURATED ({len(missing)}) — every one of these needs a "
              f"verdict in consortium_members.json:")
        for v, e in sorted(missing.items()):
            print(f"   {v}  {e['name']}  [{'+'.join(sorted(e['signals']))}] "
                  f"{', '.join(e['contracts'])}")
            if e["excerpt"]:
                print(f"      …{e['excerpt'][:260]}…")
        return 1
    print("\nEvery joint venture the documents name is curated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
