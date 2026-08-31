# -*- coding: utf-8 -*-
"""Propose the MUNICIPALITIES each Anti-nero contract says it works in.

The contracts carry no coordinates — they say so themselves («ο τόπος …
απεικονίζεται στο χάρτη επέμβασης που επισυνάπτεται σε κάθε μία εκ των ως
άνω Μελετών», an annex ΚΗΜΔΗΣ does not publish) — but most of them do carry
a structured, per-authority placement sentence:

    «Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου Μεγάρων χωροθετούνται
     εντός των Δήμων Μεγαρέων και Μάνδρας – Ειδυλλίας της Περιφερειακής
     Ενότητας Δυτικής Αττικής (NUTS: EL306)»

That sentence is the unit this script extracts: which Δασαρχείο / Διεύθυνση
Δασών, which δήμοι, and — in most of them — the Π.Ε. and the NUTS code the
document states beside them, which is a check the extraction can be held to.
Contracts that place their works without naming an authority are read with a
looser anchor and reported separately.

NOTHING is written to the database and nothing is decided here: the output is
a review worksheet plus `municipality_curator.html`, and every verdict belongs
in curated `khmdhs/data/contract_municipalities.json` (DATA_DECISIONS
2026-08-18).

Usage:
  .venv/Scripts/python.exe scripts/extract_contract_municipalities.py
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:                      # pragma: no cover
    pass

from khmdhs.config import DEFAULT_DB, PDF_CACHE_DIR
from khmdhs.forest_loader import (GAZETTEER_FILE, REGISTRY_FILE, Matcher,
                                  load_registry)
from khmdhs.greek_regions import PE_CENTROIDS, nuts3_for

ROOT = Path(__file__).resolve().parent.parent
REVIEW_FILE = ROOT / "data" / "processed" / "municipality_review.json"
CURATOR = ROOT / "municipality_curator.html"
# curated verdicts on attribution, where a contract assigns a δήμος to a
# service that does not serve it (DATA_DECISIONS 2026-08-19)
OVERRIDES_FILE = ROOT / "khmdhs" / "data" / "municipality_overrides.json"

# NEVER rename what a document says. A name resolves only where identity is
# certain — an official rename or split of the SAME unit — and never by guess:
# 26PROC018350831 writes «Δήμο Λασιθίου» (no such δήμος; the Π.Ε. holds four)
# and «Δήμους Λαυρεωτικης και Σαρωνίδας» (a settlement of Δήμος Σαρωνικού).
# Both stay unresolved on the contract, visible as what the call actually says
# (user decision 2026-08-19).
# Post-Καλλικράτης names the documents use for a unit our 2010 gazetteer still
# spells the old way. The polygon/centroid layer IS Καλλικράτης, so these
# resolve onto the old code and the row is marked `via: rename` for the curator
# to see. ν.4600/2019 renamed Καλαμπάκας → Μετεώρων and split Σερβίων-Βελβεντού
# into Σερβίων and Βελβεντού; we keep the parent unit and say so rather than
# invent a boundary we do not have.
_SPLIT = "ν.4600/2019 split this unit; the Καλλικράτης layer keeps the parent"
RENAMES = {
    "ΜΕΤΕΩΡΩΝ": ("9112", "ν.4600/2019 renamed Δήμος Καλαμπάκας → Μετεώρων"),
    "ΣΕΡΒΙΩΝ": ("9069", _SPLIT + " Σερβίων-Βελβεντού"),
    "ΒΕΛΒΕΝΤΟΥ": ("9069", _SPLIT + " Σερβίων-Βελβεντού"),
    "ΜΥΤΙΛΗΝΗΣ": ("9261", _SPLIT + " Λέσβου"),
    "ΔΥΤΙΚΗΣ ΛΕΣΒΟΥ": ("9261", _SPLIT + " Λέσβου"),
    "ΑΡΓΟΣΤΟΛΙΟΥ": ("9120", _SPLIT + " Κεφαλονιάς"),
    "ΣΑΜΗΣ": ("9120", _SPLIT + " Κεφαλονιάς"),
    "ΛΗΞΟΥΡΙΟΥ": ("9120", _SPLIT + " Κεφαλονιάς"),
    "ΑΝΑΤΟΛΙΚΗΣ ΣΑΜΟΥ": ("9264", _SPLIT + " Σάμου"),
    "ΔΥΤΙΚΗΣ ΣΑΜΟΥ": ("9264", _SPLIT + " Σάμου"),
    "ΚΑΜΕΝΩΝ ΒΟΥΡΛΩΝ": ("9163", "ν.4600/2019 renamed Μώλου-Αγ. Κωνσταντίνου → Καμένων Βούρλων"),
    # spelling variants of a unit that did not change
    "Κ. ΝΕΥΡΟΚΟΠΙΟΥ": ("9003", "abbreviated Κάτω Νευροκοπίου"),
    "ΗΡΑΚΕΙΑΣ": ("9052", "the document drops the λ of Ηρακλείας"),
    "ΑΝΔΡΙΤΣΑΙΝΑΣ - ΚΡΕΣΤΕΝΑΣ": ("9136", "the documents decline Κρεστένων as Κρέστενας"),
    "ΤΡΟΙΖΗΝΙΑΣ - ΜΕΘΑΝΩΝ": ("9213", "ν.4600/2019 renamed Τροιζηνίας → Τροιζηνίας-Μεθάνων"),
    "ΜΕΛΒΙΖΙΟΥ": ("9306", "the document transposes Μαλεβιζίου"),
    "ΠΕΤΡΟΥΠΟΛΕΩΣ": ("9184", "genitive variant of Πετρούπολης"),
    "ΗΛΙΟΥΠΟΛΕΩΣ": ("9191", "genitive variant of Ηλιούπολης"),
    "ΔΩΡΙΔΑΣ": ("9166", "the documents decline Δωρίδος as Δωρίδας"),
    "Ν. ΠΡΟΠΟΝΤΙΔΑΣ": ("9058", "abbreviated Νέας Προποντίδας"),
    # Places the documents name that are NOT Καλλικράτης δήμοι: a
    # pre-2010 (Καποδιστριακός) unit and two settlements. Each resolves to
    # the δήμος that contains it today, and the page keeps the document's
    # own wording beside it (user decision, 2026-08-19).
    "ΘΕΣΠΙΕΩΝ": ("9144", "Καποδιστριακός Δήμος Θεσπιέων; ν.3852/2010 merged it into Θηβαίων"),
    # the 2022 ANTINERO-II chains, back in scope 2026-08-29 (DATA_DECISIONS)
    "ΟΜΗΡΟΥΠΟΛΗΣ": ("9266", "Καποδιστριακός Δήμος Ομηρούπολης; ν.3852/2010 merged it into Χίου"),
    "ΙΩΑΝΝΙΝΩΝ": ("9084", "the document names the city; the Καλλικράτης δήμος is Ιωαννιτών"),
    "ΘΕΛΠΟΥΣΑΣ": ("9238", "Καποδιστριακός Δήμος Θέλπουσας («τέως Δήμου Θέλπουσας» in the text); ν.3852/2010 merged it into Γορτυνίας"),
    "ΠΑΠΑΓΟΥ": ("9175", "the document names the Παπάγου half of Δήμου Παπάγου-Χολαργού"),
    "ΣΑΡΩΝΙΔΑΣ": ("9225", "Σαρωνίδα is a settlement of Δήμου Σαρωνικού, not a δήμος"),
    "ΒΟΡΕΙΑΣ ΚΕΡΚΥΡΑΣ": ("9118", _SPLIT + " Κέρκυρας"),
    "ΚΕΝΤΡΙΚΗΣ ΚΕΡΚΥΡΑΣ ΚΑΙ ΔΙΑΠΟΝΤΙΩΝ ΝΗΣΩΝ": ("9118", _SPLIT + " Κέρκυρας"),
    "ΑΝΑΤΟΛΙΚΗΣ ΚΑΙ ΔΥΤΙΚΗΣ ΣΑΜΟΥ": ("9264", _SPLIT + " Σάμου"),
    "ΗΡΩΙΚΗΣ ΝΗΣΟΥ ΨΑΡΩΝ": ("9267", "the δήμος' full formal name"),
    "ΛΟΡΚΩΝ": ("9161", "the document transposes Λοκρών"),
    "ΑΜΦΙΚΛΕΙΑΣ - ΕΛΑΤΗΣ": ("9158", "the document shortens Ελάτειας"),
    "ΙΣΤΑΙΑΣ - ΑΙΔΗΨΟΥ": ("9150", "the documents drop the ι of Ιστιαίας"),
    "ΛΟΥΤΡΑΚΙΟΥ - ΠΕΡΑΧΩΡΑΣ - ΑΓΙΩΝ ΘΕΟΔΩΡΩΝ": ("9244", "full name; the layer abbreviates Αγ. Θεοδώρων"),
    "ΧΑΛΚΙΔΑΙΩΝ": ("9155", "both spellings of Χαλκιδέων are in official use"),
    "ΣΑΛΑΜΙΝΟΣ": ("9211", "genitive variant of Σαλαμίνας"),
}
# pdftotext keeps the ΚΗΜΔΗΣ page-break watermark, which lands between «Δήμου»
# and the name it introduces
WATERMARK = re.compile(r"(?:ΣΕΛ\.\s*\d+\s+)?\d\d[A-Z]{3,4}\d{6,}\s+\d{4}-\d\d-\d\d")


def fold(s: str | None) -> str:
    """Uppercase + strip accents — for the TEXT being searched. Length is
    preserved (a precomposed char folds to exactly one char), which is what
    lets the verbatim excerpt be sliced out of the raw string at folded
    offsets."""
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").upper())
                   if not unicodedata.combining(c))


def fold_pattern(p: str) -> str:
    r"""The same for a pattern written in uppercase Greek. It must NOT
    uppercase: that turns \s \d \w into their inverses and mangles (?P<name>)
    group names — the trap this project has now hit four times."""
    return "".join(c for c in unicodedata.normalize("NFD", p)
                   if not unicodedata.combining(c))


# the documents use six different hyphens, U+2010 among them
DASHES = "-‐‑‒–—―"


def _dash(s: str) -> str:
    """One spelling for every dash-joined name: ΔΙΟΥ-ΟΛΥΜΠΟΥ == ΔΙΟΥ - ΟΛΥΜΠΟΥ."""
    return re.sub(rf"\s*[{DASHES}]\s*", " - ", " ".join(s.split()))


def _key(s: str) -> str:
    """The lookup key: a compound name is one word, however it is punctuated —
    «Ξυλοκάστρου - Ευρωστίνης», «Ξυλοκάστρου Ευρωστίνης» and
    «Ξυλοκάστρου‐Ευρωστίνης» are the same δήμος, and all three are in use."""
    # DASHES leads with '-', which is literal only at the START of the class:
    # «[\s-‐…]» is the character RANGE \s to ‐, which re rejects outright
    return re.sub(rf"[{DASHES}\s.]+", "", s)


# «αρμοδιότητας X … χωροθετούνται …» — the tail is a LOOKAHEAD: a consuming
# window swallows the next statement, and a five-lot contract then reports one.
ST_TEMPLATE = re.compile(fold_pattern(
    r"ΑΡΜΟΔΙΟΤΗΤΑ[ΣΝ](?P<auth>.{0,120}?)ΧΩΡΟΘΕΤ\w*(?=(?P<rest>.{0,600}))"))
# contracts that place their works without naming the authority
# The 2025 «επείγουσες υλοτομικές εργασίες» calls say the same thing in
# another dialect: «…εκτάσεις οι οποίες ανήκουν στην περιοχή ευθύνης των
# Δασαρχείων Θεσσαλονίκης, Λαγκαδά και Σταυρού, ενώ ΔΙΟΙΚΗΤΙΚΑ ΑΝΗΚΕΙ στους
# Δήμους Ωραιοκάστρου, … εντός των Δημοτικών Κοινοτήτων Μεσαίου και
# Πενταλόφου της Δ.Ε. Καλλιθέας …» — 63 of the 103 contracts without a δήμος
# have a document that speaks this way (measured 2026-08-19).
ST_PLAIN = re.compile(fold_pattern(
    r"(?:ΧΩΡΟΘΕΤ\w*|ΤΟΠΟΣ\s+ΕΚΤΕΛΕΣΗΣ|ΤΟΠΟΥ\s+ΕΚΤΕΛΕΣΗΣ|ΤΟΠΟΣ\s+ΕΚΠΟΝΗΣΗΣ"
    r"|ΠΕΡΙΟΧ\w*\s+ΕΠΕΜΒΑΣ\w*|ΔΙΟΙΚΗΤΙΚΑ\s+ΑΝΗΚ\w*"
    r"|ΕΝΤΟΣ\s+Τ\w+\s+ΔΗΜΟΤΙΚ\w+\s+ΚΟΙΝΟΤΗΤ\w+)(?=(?P<rest>.{0,600}))"))
# «της Περιφερειακής Ενότητας Χ» — 26SYMV018661994 drops the Ενότητας, and a
# strict pattern then walks on and reads the NEXT sentence's Π.Ε. as this one's
PE_CLAUSE = re.compile(fold_pattern(
    r"ΠΕΡΙΦΕΡΕΙΑΚ\w*\s+(?:ΕΝΟΤΗΤ\w*\s+)?(?P<pe>[Α-ΩΪΫ][Α-ΩΪΫ\s\-–]{2,40}?)\s*(?:\(|,|\.|ΚΑΙ\b)"))
NUTS = re.compile(r"EL\d{3}")
# the same sentence may name its Δασαρχείο after the δήμοι instead of before
ARMODIOT = re.compile(fold_pattern(r"ΑΡΜΟΔΙΟΤΗΤΑ[ΣΝ]|ΕΥΘΥΝΗΣ"))
# «… (NUTS: EL306) και των Δήμων …» — the same authority, a second Π.Ε.
CONTINUES = re.compile(fold_pattern(
    r"[\s,)]*(?:ΚΑΙ|,)\s*(?:ΕΝΤΟΣ\s+)?(?:ΤΩΝ|ΤΟΥ|ΣΤΟΥ[ΣΝ]?)?\s*ΔΗΜ"))
# finer than a δήμος, and we have no boundary layer at that tier: kept as
# evidence on the card so the curator sees what the document actually says
SUBMUNI = re.compile(fold_pattern(
    r"(?:ΔΗΜΟΤΙΚ\w*|ΤΟΠΙΚ\w*)\s+(?:ΕΝΟΤΗΤ|ΚΟΙΝΟΤΗΤ)\w*[^.]{0,90}"
    r"|Δ\.\s?[ΕΚ]\.[^.]{0,90}|ΟΙΚΙΣΜ\w*[^.]{0,90}"))
# «Τμήμα Α: «Έργα … αρμοδιότητας της Διεύθυνσης Δασών Φωκίδας …»» — the call
# says which lot belongs to which forest service, and the lots ARE the
# contracts (user, 2026-08-19)
LOT = re.compile(fold_pattern(r"ΤΜΗΜΑ\s*(?:[ΑΒΓΔΕΖ]|\d+)\s*[:.]"))
THEMA = re.compile(fold_pattern(r"ΘΕΜΑ\s*:"))
# Where a call says what the work is and where. The SECTION NUMBER varies
# between calls — 2.2.1 in one, 2.1 or Άρθρο 3 in another (user, 2026-08-19) —
# so every anchor here is a PHRASE, and the section number is read off the
# text around it and reported rather than assumed. Measured over the 132
# cached calls: αντικείμενο 128, περιλαμβάνονται 126, τόπος εκτέλεσης 124,
# χωροθετ… 113, «εργασίες αφορούν» 50, «προς παρέμβαση εκτάσεις» 46 — 131 of
# the 132 carry at least one.
SCOPE_ANCHORS = (
    ("οι προς παρέμβαση εκτάσεις", r"ΠΡΟΣ\s+(?:ΠΑΡ|ΕΠ)ΕΜΒΑΣΗ\s+ΕΚΤΑΣΕΙΣ"),
    ("οι εργασίες αφορούν", r"ΕΡΓΑΣΙΕΣ\s+ΑΦΟΡΟΥΝ"),
    ("τόπος εκτέλεσης", r"ΤΟΠΟΣ\s+ΕΚΤΕΛΕΣΗΣ"),
    ("αντικείμενο της σύμβασης", r"ΑΝΤΙΚΕΙΜΕΝΟ\s+ΤΗΣ\s+ΣΥΜΒΑΣΗΣ"),
)
SCOPE_RX = tuple((label, re.compile(fold_pattern(rx))) for label, rx in SCOPE_ANCHORS)
# «2.2.1», «2.1», «Άρθρο 3» — whatever numbering this call happens to use
SECTION = re.compile(fold_pattern(r"(?:ΑΡΘΡΟ\s+\d+|\d+(?:\.\d+){1,3})"))
# the δήμος list has to be introduced as one, or «Δράμας» in a postal address
# counts as a work location
DHMOS = re.compile(fold_pattern(r"ΔΗΜ(?:ΟΥ|ΟΣ|ΟΝ|Ο|ΩΝ|ΟΙ|ΟΥΣ)\b\s*"))
# where the list of δήμοι stops and the sentence says something else
RUN_END = re.compile(fold_pattern(
    r"ΠΕΡΙΦΕΡΕΙΑΚ|Π\.\s?Ε|ΔΑΣΑΡΧΕΙ|ΔΙΕΥΘΥΝΣ|Δ/ΝΣ|ΠΕΡΙΟΧ|ΘΕΣ[ΕΗ]|ΠΛΗΣΙΟΝ|ΕΝΤΟΣ"
    r"|ΣΥΓΚΕΚΡΙΜΕΝΑ|ΟΠΩΣ|ΣΥΜΦΩΝΑ|ΑΡΜΟΔΙΟΤΗΤ|ΠΡΟΤΕΙΝΟΜΕΝ|\."))
# words that legitimately appear inside a list of δήμοι
RUN_WORDS = {fold(w) for w in ("ΚΑΙ", "ΤΩΝ", "ΤΟΥ", "ΤΗΣ", "ΤΗΝ", "ΤΟ", "ΤΑ", "ΔΗΜΩΝ",
                               "ΔΗΜΟΥ", "ΔΗΜΟ", "ΔΗΜΟΣ", "ΔΗΜΟΤΙΚΗΣ", "ΔΗΜΟΤΙΚΗ",
                               "ΕΝΟΤΗΤΑΣ", "ΕΝΟΤΗΤΑ", "ΚΟΙΝΟΤΗΤΑΣ", "ΚΟΙΝΟΤΗΤΑ",
                               "ΝΗΣΟΥ", "ΝΗΣΩΝ", "NUTS")}
# «ΚΑΙ» needs a word boundary, or the separator swallows the first three
# letters of Δήμος ΚΑΙσαριανής and leaves «ΣΑΡΙΑΝΗΣ» unresolved
SEPARATOR = re.compile(rf"[\s,&·]*(?:ΚΑΙ\b|[{DASHES}])?[\s,&·]*")
WORD = re.compile(r"[Α-ΩA-Z][Α-ΩA-Z0-9.]*")


class Places:
    """The Καλλικράτης municipality vocabulary, matched fold- and dash-blind."""

    def __init__(self, gazetteer: dict):
        self.gaz = gazetteer
        self.by_name: dict[str, list[str]] = defaultdict(list)
        for code, m in gazetteer.items():
            self.by_name[_key(fold(m["name"]))].append(code)
        self.renames = {_key(k): v for k, v in RENAMES.items()}
        names = sorted([_dash(fold(m["name"])) for m in gazetteer.values()]
                       + list(RENAMES), key=len, reverse=True)
        one = "|".join(
            re.escape(n).replace(r"\ \-\ ", rf"\s*[{DASHES}]?\s*").replace(r"\ ", r"\s+")
            for n in names)
        self.rx = re.compile(one)

    def run(self, text: str, start: int) -> tuple[list[tuple[str, str]], list[str], int]:
        """Read ONE list of δήμοι beginning at `start` → (hits, unresolved, end).

        A name counts only inside a run a «Δήμου/Δήμων» introduces — matching
        the vocabulary anywhere in the window instead picks up the
        contractor's home town and every Π.Ε. that shares its name with a
        δήμος (measured: 93 assignments outside the contract's own Π.Ε.).
        One unknown word is reported and stepped over, because a single
        misspelling («ΗΡΑΚΕΙΑΣ») must not take the rest of the list with it;
        two in a row mean the list has ended.
        """
        hits: list[tuple[str, str]] = []
        unresolved: list[str] = []
        seen: set[str] = set()
        p, miss, last = start, 0, start
        while p < len(text):
            m = self.rx.match(text, p)
            if m:
                key = _key(m.group(0))
                code, via = None, "name"
                if key in self.by_name:
                    code = self.by_name[key][0]
                elif key in self.renames:       # punctuation-blind on both sides
                    code, via = self.renames[key][0], "rename"
                if code:
                    if code not in seen:
                        seen.add(code)
                        hits.append((code, via))
                    p = last = m.end()
                    miss = 0
                    continue
            if RUN_END.match(text, p):
                break
            if text[p] == "(":
                # «Δήμων … Ιλίου (Νέων Λιοσίων) και Αγίων Αναργύρων – Καματερού»
                # — an aside inside the list, not the end of it
                close = text.find(")", p)
                if 0 < close < p + 40:
                    p = close + 1
                    continue
                break
            c = SEPARATOR.match(text, p)
            if c and c.end() > p:
                p = c.end()
                continue
            w = WORD.match(text, p)
            if not w:
                break
            if len(w.group(0)) > 2 and w.group(0) not in RUN_WORDS:
                miss += 1
                if miss == 2:                   # the list of δήμοι has ended
                    unresolved.pop()
                    break
                unresolved.append(w.group(0))
            p = w.end()
        return hits, unresolved, last

    def find(self, segment: str) -> tuple[list[tuple[str, str]], list[str]]:
        """Every δήμος list in a segment, flattened — the simple reading, kept
        for the loose anchor and for the unit tests."""
        hits: list[tuple[str, str]] = []
        unresolved: list[str] = []
        seen: set[str] = set()
        for d in DHMOS.finditer(segment):
            h, u, _end = self.run(segment, d.end())
            for code, via in h:
                if code not in seen:
                    seen.add(code)
                    hits.append((code, via))
            unresolved.extend(u)
        return hits, unresolved



def read_one(adam: str, cache: Path) -> str:
    """One cached document, whitespace-normalised (empty when not cached)."""
    p = cache / f"{adam}.txt"
    if not p.exists():
        return ""
    return " ".join(WATERMARK.sub(" ", p.read_text(
        encoding="utf-8", errors="replace")).split())


def chain_of(ref: str, prev: dict[str, str | None]) -> list[str]:
    """The contract and every version behind it: 46 in-scope tips are
    amendments whose own PDF is a cover note (DATA_DECISIONS 2026-08-18)."""
    out, cur, seen = [], ref, set()
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = prev.get(cur)
    return out


def read_chain(refs: list[str], cache: Path) -> tuple[str, str, list[tuple[int, str]]]:
    """Raw text of the whole chain, its fold, and [(offset, source ΑΔΑΜ)]."""
    parts: list[str] = []
    owner: list[tuple[int, str]] = []
    at = 0
    for r in refs:
        p = cache / f"{r}.txt"
        if not p.exists():
            continue
        t = " ".join(WATERMARK.sub(" ", p.read_text(
            encoding="utf-8", errors="replace")).split())
        owner.append((at, r))
        parts.append(t)
        at += len(t) + 1
    raw = " ".join(parts)
    f = fold(raw)
    if len(f) != len(raw):          # never observed; the slicing depends on it
        raw = f
    return raw, f, owner


def source_at(owner: list[tuple[int, str]], pos: int) -> str | None:
    best = None
    for start, ref in owner:
        if start <= pos:
            best = ref
    return best


def groups_after(rest_f: str, rest_raw: str, places: Places,
                 pe_by_fold: dict[str, str]) -> list[dict]:
    """The δήμοι of one authority, in the groups the document itself makes.

    §3.6 of a phase-III contract reads: «…αρμοδιότητας του Δασαρχείου Αιγάλεω
    χωροθετούνται εντός των Δήμων Α, Β και Γ της Περιφερειακής Ενότητας
    Δυτικής Αττικής (NUTS: EL306) ΚΑΙ των Δήμων Δ, Ε… της Περιφερειακής
    Ενότητας Δυτικού Τομέα Αθηνών (NUTS: EL302).» One authority, two Π.Ε., and
    reading only as far as the first Π.Ε. clause silently drops the second
    group — five δήμοι, in that one sentence alone.
    """
    groups: list[dict] = []
    pos = 0
    while pos < len(rest_f):
        d = DHMOS.search(rest_f, pos, min(len(rest_f), pos + 150))
        if not d:
            break
        codes, unresolved, run_end = places.run(rest_f, d.end())
        if not codes and not unresolved:
            break
        pe_m = PE_CLAUSE.search(rest_f, run_end, run_end + 140)
        # some groups skip «της Περιφερειακής Ενότητας …» and go straight to
        # the parenthetical; the code alone still says which region it is
        nuts = NUTS.search(rest_raw, run_end, run_end + (220 if pe_m else 90))
        pe_raw = " ".join(pe_m.group("pe").split()) if pe_m else None
        groups.append({
            "codes": codes,
            "unresolved": unresolved,
            "pe_stated": pe_by_fold.get(pe_raw) if pe_raw else None,
            "pe_stated_raw": pe_raw,
            "nuts": nuts.group() if nuts else None,
            "submunicipal": [" ".join(rest_raw[a.start():a.end()].split())
                             for a in SUBMUNI.finditer(rest_f, d.end(),
                                                       (pe_m.end() if pe_m else run_end))][:2],
            "excerpt": " ".join(rest_raw[max(0, d.start() - 40):
                                         (pe_m.end() if pe_m else run_end) + 30].split()),
        })
        pos = pe_m.end() if pe_m else run_end
        # PE_CLAUSE stops ON the opening bracket of «(NUTS: EL306 – Δυτική
        # Αττική)», and the next group hangs off the text AFTER it — skipping
        # the parenthetical is what makes the second group visible at all
        if pe_m and rest_f[pe_m.end() - 1] == "(":
            close = rest_f.find(")", pe_m.end())
            if 0 < close < pe_m.end() + 80:
                pos = close + 1
        # another group follows only if the sentence continues «… και των Δήμων»
        if not CONTINUES.match(rest_f, pos):
            break
    return groups


def statements(raw: str, f: str, owner: list[tuple[int, str]], places: Places,
               matcher: Matcher, pe_by_fold: dict[str, str]) -> list[dict]:
    """One statement per AUTHORITY, each holding the document's own groups.

    The authority may be named before the placement verb («αρμοδιότητας του
    Δασαρχείου Μεγάρων χωροθετούνται…») or after it («χωροθετούνται εντός των
    Δήμων … αρμοδιότητας Δασαρχείου Ολυμπίας»); both are the same claim.
    """
    out: list[dict] = []
    for m in ST_PLAIN.finditer(f):
        rest_f = f[m.start("rest"): m.end("rest")]
        rest_raw = raw[m.start("rest"): m.end("rest")]
        auth, where = [], None
        back = f[max(0, m.start() - 170): m.start()]
        a = None
        for a in ARMODIOT.finditer(back):
            pass
        if a:
            auth = [n for n, _ in matcher.find(back[a.end():])]
            where = "before" if auth else None
        if not auth:
            fwd = ARMODIOT.search(rest_f)
            if fwd:
                auth = [n for n, _ in matcher.find(rest_f[fwd.end(): fwd.end() + 120])]
                where = "after" if auth else None
        groups = groups_after(rest_f, rest_raw, places, pe_by_fold)
        if not groups:
            continue
        out.append({
            "authorities": auth,
            "authority_where": where,
            "groups": groups,
            "source_ref": source_at(owner, m.start()),
            "at": m.start(),
        })
    return dedupe(drop_summary_claims(sorted(out, key=lambda s: s["at"])))


def _codes(s: dict) -> set[str]:
    return {c for g in s["groups"] for c, _via in g["codes"]}


def drop_summary_claims(sts: list[dict]) -> list[dict]:
    """§3.6 opens with a SUMMARY — «Ο τόπος εκτέλεσης … είναι περιοχές
    αρμοδιότητας των Διευθύνσεων Δασών Άρτας, Θεσπρωτίας και Κέρκυρας» —
    and only then says «Ειδικότερα, τα προτεινόμενα έργα αρμοδιότητας της
    Διεύθυνσης Δασών Άρτας χωροθετούνται εντός των Δήμων …». Attributing the
    summary's δήμοι to every authority it lists put Άρτα under the Κέρκυρα
    service; the breakdown that follows is the one that says who works where.

    So a statement naming SEVERAL authorities keeps only the δήμοι that no
    single-authority statement of the same contract claims. A genuinely joint
    sentence («αρμοδιότητας των Δασαρχείων Ολυμπίας και Αμαλιάδας
    χωροθετούνται εντός των Δήμων …») keeps everything, because nothing else
    claims those δήμοι.
    """
    claimed = {c for s in sts if len(s["authorities"]) == 1
               for g in s["groups"] for c, _v in g["codes"]}
    out = []
    for s in sts:
        if len(s["authorities"]) < 2:
            out.append(s)
            continue
        groups = []
        for g in s["groups"]:
            keep = [(c, v) for c, v in g["codes"] if c not in claimed]
            if keep:
                groups.append({**g, "codes": keep})
        if groups:
            out.append({**s, "groups": groups})
    return out


def dedupe(sts: list[dict]) -> list[dict]:
    """A contract states its authority's δήμοι more than once — the Άρθρο 3
    summary, then §3.6 in detail, and a sentence may carry two placement verbs
    («…χωροθετούνται εντός των Δήμων Χ… ο δασικός δρόμος χωροθετείται στις
    Δ.Ε. …»). Keep the richest reading of each authority: the one that covers
    the most δήμοι, then the one that names the authority."""
    best: dict[str, dict] = {}
    order: list[str] = []
    for s in sts:
        key = "|".join(sorted(s["authorities"])) or f"?{sorted(_codes(s))}"
        cur = best.get(key)
        if cur is None:
            best[key] = s
            order.append(key)
            continue
        richer = (len(_codes(s)), len(s["authorities"])) >                  (len(_codes(cur)), len(cur["authorities"]))
        keep, drop = (s, cur) if richer else (cur, s)
        have = _codes(keep)                     # never lose a δήμος to dedupe,
        for g in drop["groups"]:                # never show one twice either
            extra = [(c, v) for c, v in g["codes"] if c not in have]
            if extra:
                have.update(c for c, _ in extra)
                keep["groups"].append({**g, "codes": extra})
        best[key] = keep
    return [best[k] for k in order]



CURATED_FILE = ROOT / "khmdhs" / "data" / "contract_municipalities.json"


def write_curated(rows: list[dict]) -> int:
    """Promote the readings to the curated file, under the approved rules.

    Rules (user, 2026-08-19): a δήμος named in the contract OR in the
    πρόσκληση that produced it counts, and the row says which document said
    it; a δήμος outside the contract's curated Π.Ε. is recorded as the
    document states it and FLAGGED, leaving the region layer untouched;
    pre-Καλλικράτης names and settlements resolve to the δήμος that
    contains them today, keeping the document's own wording. `_overrides`
    is merged on every re-run, so a hand correction survives.
    """
    old = json.loads(CURATED_FILE.read_text(encoding="utf-8")) if CURATED_FILE.exists() else {}
    ov = old.get("_overrides", {})
    out = {
        "_doc": ("Which δήμος each in-scope Anti-nero contract worked in, read "
                 "from the contract's own placement sentence or from the "
                 "πρόσκληση it cites («εντός των Δήμων Χαϊδαρίου και "
                 "Ασπροπύργου, αρμοδιότητας Δασαρχείου Αιγάλεω»). Proposals "
                 "from scripts/extract_contract_municipalities.py; rules "
                 "approved 2026-08-19. `outside_region` marks a δήμος whose "
                 "Π.Ε. is not among the ones curated for the contract — the "
                 "region layer is deliberately left alone. Attribution "
                 "verdicts live in municipality_overrides.json."),
        "_overrides": ov,
    }
    for r in rows:
        seen: dict[str, dict] = {}
        for st in r["statements"]:
            for g in st["groups"]:
                for m in g["municipalities"]:
                    e = seen.setdefault(m["code"], {
                        "name": m["name"],
                        "pe": m["pe"],
                        "authority": g.get("authority"),
                        "authority_basis": g.get("authority_basis"),
                        "source_ref": st.get("source_ref"),
                        "from_call": st.get("from_call"),
                        "excerpt": " ".join((g.get("excerpt") or "").split()),
                        "outside_region": m.get("status") == "outside_curated_pe",
                        # set when the δήμος IS outside the curated regions but
                        # something accounts for it — the service administers
                        # that Π.Ε., or the user has ruled on it
                        "outside_pe_explained": m.get("outside_pe_explained"),
                        "via": m.get("via"),
                        "note": m.get("rename_note"),
                        "override": m.get("override"),
                    })
                    # a second reading of the same δήμος: prefer the one the
                    # CONTRACT states over the call's, and keep the longer quote
                    if not st.get("from_call") and e["from_call"]:
                        e.update({"source_ref": st.get("source_ref"), "from_call": None,
                                  "excerpt": " ".join((g.get("excerpt") or "").split())})
        if seen:
            out[r["ref"]] = {"municipalities": [dict(code=c, **v) for c, v in seen.items()]}
    for ref, e in ov.items():
        out[ref] = {**out.get(ref, {}), **e}
    CURATED_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return sum(1 for k in out if not k.startswith("_"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="extract_contract_municipalities")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    ap.add_argument("--out", type=Path, default=REVIEW_FILE)
    ap.add_argument("--curator", type=Path, default=CURATOR)
    ap.add_argument("--curate", action="store_true",
                    help="also write the curated contract_municipalities.json")
    args = ap.parse_args(argv)

    gaz = {k: v for k, v in json.loads(
        GAZETTEER_FILE.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    places = Places(gaz)
    registry, *_ = load_registry()
    matcher = Matcher(registry)
    pe_by_fold = {fold(k.replace("Π.Ε. ", "")): k for k in PE_CENTROIDS}

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    prev = {r["reference_number"]: r["prev_reference_no"] for r in conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts")}
    refs = [r[0] for r in conn.execute("""
        SELECT c.reference_number FROM contracts c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        WHERE s.in_scope = 1 ORDER BY 1""")]
    titles = {r["reference_number"]: r["title"] for r in conn.execute(
        "SELECT reference_number, title FROM contracts")}
    contract_pes = defaultdict(list)
    for r in conn.execute("SELECT reference_number, region_pe FROM contract_project_regions"):
        contract_pes[r["reference_number"]].append(r["region_pe"])
    items = defaultdict(list)
    for r in conn.execute(
            "SELECT reference_number, short_description FROM contract_objects"):
        if r["short_description"]:
            items[r["reference_number"]].append(r["short_description"])
    award_of = defaultdict(list)
    for r in conn.execute("SELECT reference_number, adam FROM contract_families "
                          "WHERE kind = 'auction' AND role = 'award'"):
        award_of[r["reference_number"]].append(r["adam"])
    for r in conn.execute("SELECT reference_number, adam FROM contract_linked_acts "
                          "WHERE kind = 'auction'"):
        if r["adam"] not in award_of[r["reference_number"]]:
            award_of[r["reference_number"]].append(r["adam"])
    stored_auth = defaultdict(list)
    for r in conn.execute(
            "SELECT reference_number, authority_name FROM contract_forest_authorities"):
        stored_auth[r["reference_number"]].append(r["authority_name"])
    # the πρόσκληση each contract's own text cites (contract_families): the
    # call document lists every ΤΜΗΜΑ with its Δασαρχείο and that lot's δήμοι,
    # which is where a contract that keeps its own Άρθρο 3 terse says it
    call_of = {r["reference_number"]: r["adam"] for r in conn.execute(
        "SELECT reference_number, adam FROM contract_families "
        "WHERE kind = 'notice' AND role = 'procurement'")}
    conn.close()

    call_blocks: dict[str, list[dict]] = {}

    def blocks_of_call(adam: str) -> list[dict]:
        if adam not in call_blocks:
            raw, f, owner = read_chain([adam], args.cache)
            call_blocks[adam] = statements(raw, f, owner, places, matcher,
                                           pe_by_fold) if raw else []
        return call_blocks[adam]

    overrides = {k: v for k, v in json.loads(
        OVERRIDES_FILE.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    # every Π.Ε. a service is registered for: its seat plus the jurisdictions
    # confirmed by the user (forest_authorities.json `covers_pe`)
    auth_pe = {n: tuple([a["region_pe"], *a.get("covers_pe", [])])
               for n, a in json.loads(
                   REGISTRY_FILE.read_text(encoding="utf-8"))["authorities"].items()}
    rows: list[dict] = []
    tally: dict[str, int] = defaultdict(int)
    for ref in refs:
        raw, f, owner = read_chain(chain_of(ref, prev), args.cache)
        if not raw:
            tally["no_text"] += 1
            continue
        sts = statements(raw, f, owner, places, matcher, pe_by_fold)
        mine = set(stored_auth.get(ref, []))
        covered = {a for s in sts for a in s["authorities"]}
        adam = call_of.get(ref)
        if adam and mine - covered:
            # only the lots that are THIS contract's, and only where its own
            # text is silent — the call describes every τμήμα, most of which
            # belong to its sibling contracts
            for b in blocks_of_call(adam):
                if set(b["authorities"]) & (mine - covered):
                    sts.append({**b, "from_call": adam})
                    covered.update(b["authorities"])
        if not sts:
            # no δήμος anywhere — the row is still written, because the trail
            # showing WHERE the reading stopped is the answer for it
            tally["no_placement_sentence"] += 1
        if any(s.get("from_call") for s in sts):
            tally["helped_by_the_call"] += 1
        pes = sorted(set(contract_pes.get(ref, [])))
        out_sts = []
        for s in sts:
            out_groups = []
            for g in s["groups"]:
                # WHICH authority this group belongs to. A contract that lists
                # several services states them once, together, and then gives a
                # Π.Ε. group per service without repeating the name — «…
                # αρμοδιότητας των Δ/νσεων Δασών Άρτας, Θεσπρωτίας και
                # Κέρκυρας. Ειδικότερα … εντός των Δήμων Αρταίων … της Π.Ε.
                # Άρτας, … εντός των Δήμων Ηγουμενίτσας … της Π.Ε.
                # Θεσπρωτίας …». The Π.Ε. IS the attribution there; splitting
                # the list across every named service put Άρτα under Κέρκυρα.
                cands = [a for a in stored_auth.get(ref, [])
                         if g["pe_stated"] and g["pe_stated"] in auth_pe.get(a, ())]
                if len(s["authorities"]) == 1:
                    g_auth, basis = s["authorities"][0], "named in the sentence"
                elif len(cands) == 1:
                    g_auth, basis = cands[0], "the only authority of this Π.Ε."
                elif len(set(stored_auth.get(ref, []))) == 1:
                    g_auth, basis = stored_auth[ref][0], "the contract's sole authority"
                else:
                    g_auth, basis = None, None
                munis = []
                for code, via in g["codes"]:
                    ov = overrides.get(f"{ref}|{code}")
                    pe = gaz[code]["pe"]
                    # WHY a δήμος can sit outside the Π.Ε. we curated for the
                    # contract, and only the last case is worth a reader's
                    # attention (measured 2026-08-19: 30 · 11 · 6 · 2 of 49):
                    #   the service that names it administers that Π.Ε.
                    #     (forest_authorities `covers_pe` — Πεντέλης covers
                    #     Ανατ. Αττική, Αιγάλεω covers Δυτ. Αττική, Σάμου
                    #     covers Ικαρία), or the δήμος is in the service's own
                    #     seat Π.Ε.  → the region curation is simply narrower
                    #   the user has already ruled on it (municipality_overrides)
                    #   nothing explains it → flagged
                    explained = None
                    if g_auth and pe in auth_pe.get(g_auth, ()):
                        explained = ("seat" if pe == auth_pe[g_auth][0]
                                     else "covers_pe")
                    elif ov:
                        explained = "curated verdict"
                    if g["pe_stated"] and pe != g["pe_stated"]:
                        status = "pe_mismatch"         # the document contradicts itself
                    elif pes and pe not in pes and not explained:
                        status = "outside_curated_pe"  # nothing explains it
                    else:
                        status = "ok"
                    tally[status] += 1
                    munis.append({
                        "code": code, "name": gaz[code]["name"], "pe": pe,
                        "via": "curated" if ov else via, "status": status,
                        "outside_pe_explained": explained
                        if (pes and pe not in pes) else None,
                        "override": ov,
                        "rename_note": RENAMES[fold(gaz[code]["name"])][1]
                        if via == "rename" and fold(gaz[code]["name"]) in RENAMES else None,
                    })
                ov_auth = {m["override"]["authority"] for m in munis
                           if m.get("override")}
                if len(ov_auth) == 1 and munis and all(m.get("override") for m in munis):
                    g_auth, basis = ov_auth.pop(), "curated verdict"
                tally["unresolved"] += len(g["unresolved"])
                tally["groups"] += 1
                out_groups.append({**{k: v for k, v in g.items() if k != "codes"},
                                   "authority": g_auth, "authority_basis": basis,
                                   "municipalities": munis})
            out_sts.append({**{k: v for k, v in s.items() if k != "groups"},
                            "groups": out_groups,
                            "from_call": s.get("from_call"),
                            "own_authority": bool(set(s["authorities"]) &
                                                  set(stored_auth.get(ref, [])))})
        tally["contracts"] += bool(out_sts)
        tally["statements"] += len(out_sts)
        trail = read_trail(
            ref, title=titles.get(ref) or "", items=items.get(ref, []),
            chain_raw=raw, chain_f=f, awards=award_of.get(ref, []),
            calls=[adam] if adam else [], cache=args.cache, matcher=matcher,
            places=places, pe_by_fold=pe_by_fold,
            stored=sorted(set(stored_auth.get(ref, []))))
        tally["trail_steps"] += len(trail)
        rows.append({
            "ref": ref,
            "trail": trail,
            "title": (titles.get(ref) or "")[:160],
            "contract_pes": pes,
            "stored_authorities": sorted(set(stored_auth.get(ref, []))),
            "statements": out_sts,
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    pairs = pair_evidence(rows, gaz, auth_pe)
    write_curator(rows, pairs, gaz, args.curator)
    if args.curate:
        print(f"curated → {write_curated(rows)} contracts in {CURATED_FILE.name}")

    n_muni = sum(len(g["municipalities"]) for r in rows for s in r["statements"]
                 for g in s["groups"])
    n_tpl = sum(1 for r in rows if any(s["authorities"] for s in r["statements"]))
    print(f"in-scope contracts                     : {len(refs)}")
    print(f"  with a placement sentence            : {tally['contracts']}"
          f"   ({n_tpl} naming their Δασαρχείο)")
    print(f"  …of which read from their πρόσκληση  : {tally['helped_by_the_call']}")
    print(f"  no placement sentence anywhere       : {tally['no_placement_sentence']}")
    print(f"  no cached text                       : {tally['no_text']}")
    print(f"authority statements                   : {tally['statements']}")
    print(f"  their Π.Ε. groups                    : {tally['groups']}")
    print(f"municipality assignments               : {n_muni}")
    print(f"  agreeing with every Π.Ε. we can check: {tally['ok']}")
    print(f"  contradicting the sentence's own Π.Ε.: {tally['pe_mismatch']}")
    print(f"  outside our curated Π.Ε.             : {tally['outside_curated_pe']}")
    print(f"names left unresolved                  : {tally['unresolved']}")
    print(f"worksheet → {args.out}")
    print(f"curator   → {args.curator.name}")
    return 0


def _quote(raw: str, at: int, before: int = 60, after: int = 300) -> str:
    return " ".join(raw[max(0, at - before): at + after].split())


def lots_of_call(raw: str, f: str, matcher: Matcher) -> list[dict]:
    """«Τμήμα Α: «Έργα … αρμοδιότητας της Διεύθυνσης Δασών Φωκίδας και του
    Δασαρχείου Ελασσόνας …»» — the call's own table of lots. A call that
    produced several contracts describes all of them, so a contract may read
    only the lot whose authorities are its own."""
    out = []
    for m in LOT.finditer(f):
        window = f[m.start(): m.start() + 320]
        auths = [n for n, _ in matcher.find(window)]
        if not auths:
            continue
        out.append({"lot": " ".join(raw[m.start(): m.end()].split()),
                    "authorities": auths,
                    "quote": _quote(raw, m.start(), 0, 300)})
    return out


def scope_paragraphs(raw: str, f: str) -> list[dict]:
    """The two paragraphs a πρόσκληση uses to say where and what: «οι προς
    παρέμβαση/επέμβαση εκτάσεις …» and «οι ως άνω εργασίες αφορούν σε i) … ii)
    …», the second of which breaks the work down per authority with its
    στρέμματα. Quoted whole — they are the evidence, not a keyword hit."""
    out = []
    for label, rx in SCOPE_RX:
        m = rx.search(f)
        if not m:
            continue
        # which section this sits in, read off the text rather than assumed:
        # the numbering differs from call to call
        before = f[max(0, m.start() - 300): m.start()]
        secs = SECTION.findall(before)
        out.append({"anchor": label,
                    "section": secs[-1] if secs else None,
                    "quote": _quote(raw, m.start(), 40, 900)})
        if len(out) == 3:                    # three quotes is plenty to read
            break
    return out


def read_trail(ref: str, *, title: str, items: list[str], chain_raw: str,
               chain_f: str, awards: list[str], calls: list[str],
               cache: Path, matcher: Matcher, places: Places,
               pe_by_fold: dict[str, str], stored: list[str]) -> list[dict]:
    """How this contract's work locations were read, step by step.

    The order is the user's (2026-08-19): the contract's own title first,
    because it names the lot's authorities and nothing else can override
    that; then the award, which repeats them in its ΘΕΜΑ and may add
    locations; then the call, whose title says whether it covers this
    contract alone or several lots, and whose «προς παρέμβαση εκτάσεις» /
    «εργασίες αφορούν» paragraphs carry the detail; and last the contract
    body, where phase-III contracts list δήμοι per authority in §3.6.
    """
    steps: list[dict] = []

    # ---- 1 · the title of the contract itself ------------------------------
    head = title + " · " + " · ".join(items)
    fh = fold(head)
    m = ARMODIOT.search(fh)
    found = [n for n, _ in matcher.find(head)]
    steps.append({
        "step": "the contract's own title",
        "doc": ref, "kind": "contract",
        "where": "registry title and item text",
        "quote": _quote(head, m.start(), 40, 260) if m else head[:260],
        "authorities": found,
        "note": None if found else "no Δασαρχείο named in the title",
    })

    # ---- 2 · the award decision -------------------------------------------
    for a in awards[:1]:
        raw = read_one(a, cache)
        if not raw:
            continue
        f = fold(raw)
        m = THEMA.search(f) or ARMODIOT.search(f)
        got = [n for n, _ in matcher.find(raw[:2500])]
        steps.append({
            "step": "the award decision",
            "doc": a, "kind": "award",
            "where": "ΘΕΜΑ",
            "quote": _quote(raw, m.start(), 0, 340) if m else raw[:300],
            "authorities": got,
            "note": ("repeats the same authorities" if set(got) == set(found) and got
                     else "names different authorities" if got else
                     "adds no authority"),
        })

    # ---- 3 · the call: whose lots does it describe? ------------------------
    for c in calls[:1]:
        raw = read_one(c, cache)
        if not raw:
            continue
        f = fold(raw)
        lots = lots_of_call(raw, f, matcher)
        mine = set(stored) or set(found)
        ours = [l for l in lots if set(l["authorities"]) & mine]
        # the letterhead comes first in every call; its TITLE is the line that
        # says «… με τίτλο «Έργα … αρμοδιότητας …»»
        head = ARMODIOT.search(f, 0, 6000)
        steps.append({
            "step": "the call",
            "doc": c, "kind": "call",
            "where": "its title and lot table",
            "quote": (ours[0]["quote"] if ours else
                      lots[0]["quote"] if lots else
                      _quote(raw, head.start(), 120, 260) if head else
                      _quote(raw, 0, 0, 320)),
            "authorities": sorted({a for l in ours for a in l["authorities"]}),
            "note": (f"describes {len(lots)} lots; {len(ours)} of them are this "
                     f"contract's" if lots else
                     "no lot table — the call covers this contract alone"),
        })
        for para in scope_paragraphs(raw, f):
            steps.append({
                "step": "the call, where it describes the work",
                "doc": c, "kind": "call",
                "where": (f"§{para['section']} «{para['anchor']}»"
                          if para["section"] else f"«{para['anchor']}»"),
                "quote": para["quote"],
                "authorities": [n for n, _ in matcher.find(para["quote"])],
                "note": None,
            })

    # ---- 4 · the contract body --------------------------------------------
    m = ST_PLAIN.search(chain_f)
    if m:
        steps.append({
            "step": "the contract body",
            "doc": ref, "kind": "contract",
            "where": "«τόπος εκτέλεσης» / «χωροθετούνται»",
            "quote": _quote(chain_raw, m.start(), 60, 420),
            "authorities": [],
            "note": "the per-authority δήμος lists below are read from here",
        })
    return steps


def pair_evidence(rows: list[dict], gaz: dict, auth_pe: dict[str, str]) -> list[dict]:
    """Collapse the per-contract readings into what actually has to be judged:
    one row per (Δασαρχείο, δήμος), with everything that independently backs
    it. A curator asked to confirm 576 chips across 143 contracts is really
    being asked the same question many times — «does this forest service work
    in this δήμος» — and the documents can answer most of it themselves.

    Five independent confirmations exist, and they are genuinely independent:
      · the contract's own text and its πρόσκληση both say it
      · the Π.Ε. named in the same sentence is the δήμος's Π.Ε.
      · the NUTS code printed in that sentence resolves to the same Π.Ε.
      · the authority's own Π.Ε. in our forest registry agrees
      · another contract, procured separately, asserts the same pair
    (The registry's own NUTS field cannot help: 121 of its 124 rows say «EL».)
    """
    ev: dict[tuple[str | None, str], dict] = {}
    for r in rows:
        # a sentence that names no Δασαρχείο still belongs to one when the
        # contract holds exactly one — «this contract IS the Δασαρχείο X lot»
        sole = r["stored_authorities"][0] if len(r["stored_authorities"]) == 1 else None
        for st in r["statements"]:
            src = "call" if st.get("from_call") else "contract"
            for g in st["groups"]:
                for a in [g.get("authority") or sole]:
                    for m in g["municipalities"]:
                        e = ev.setdefault((a, m["code"]), {
                            "authority": a, "code": m["code"], "name": m["name"],
                            "pe": m["pe"], "via": m["via"], "rename_note": m["rename_note"],
                            "sources": set(), "contracts": set(), "excerpts": [],
                            "from_sole": False, "curated": False,
                            "pe_ok": False, "pe_bad": False,
                            "nuts_ok": False, "nuts_seen": False,
                        })
                        e["sources"].add(src)
                        if m.get("override"):
                            e["curated"] = True
                            e["note"] = m["override"]["note"]
                            e["stated_authority"] = m["override"]["stated_authority"]
                        if a and g.get("authority_basis") != "named in the sentence":
                            e["from_sole"] = True
                        e["contracts"].add(r["ref"])
                        if len(e["excerpts"]) < 2 and g["excerpt"] not in e["excerpts"]:
                            e["excerpts"].append(g["excerpt"])
                        if g["pe_stated"]:
                            if g["pe_stated"] == m["pe"]:
                                e["pe_ok"] = True
                            else:
                                e["pe_bad"] = True
                        if g["nuts"]:
                            e["nuts_seen"] = True
                            if nuts3_for(m["pe"]) == g["nuts"]:
                                e["nuts_ok"] = True
    out = []
    for (a, _code), e in ev.items():
        checks = []
        if len(e["sources"]) > 1:
            checks.append("the contract and its πρόσκληση both say it")
        if e["pe_ok"]:
            checks.append("the Π.Ε. named in the same sentence")
        if e["nuts_ok"]:
            checks.append("the NUTS code printed beside it")
        if a and e["pe"] in auth_pe.get(a, ()):
            checks.append("the Π.Ε. this service is registered for")
        if e["curated"]:
            checks.append("a curated verdict")
        if len(e["contracts"]) > 1:
            checks.append(f"{len(e['contracts'])} separate contracts")
        if e["from_sole"]:
            checks.append("the sole authority on the contract that states it")
        # an unattributed δήμος is still a work location of the contract —
        # only its attribution to one Δασαρχείο is missing, and the page says so
        if e["pe_bad"]:
            tier = "C"
        elif len(checks) >= 3:
            tier = "A"
        elif len(checks) == 2:
            tier = "B"
        else:
            tier = "C"
        out.append({**e, "tier": "A" if e["curated"] else tier, "checks": checks,
                    "sources": sorted(e["sources"]),
                    "contracts": sorted(e["contracts"])})
    return sorted(out, key=lambda e: (e["authority"] or "~", e["name"]))


def write_curator(rows: list[dict], pairs: list[dict], gaz: dict, path: Path) -> None:
    opts = [{"code": c, "label": f"{m['name']} — {m['pe'].replace('Π.Ε. ', '')}"}
            for c, m in sorted(gaz.items(), key=lambda kv: kv[1]["name"])]
    payload = json.dumps({"pairs": pairs, "rows": rows, "munis": opts},
                         ensure_ascii=False)
    path.write_text(CURATOR_TEMPLATE.replace("__DATA__", payload.replace("</", "<\/")),
                    encoding="utf-8")


CURATOR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where each forest service works</title>
<style>
  :root { --paper:#fff; --panel:#f4f4f2; --ink:#1c221f; --soft:#5c6862; --line:#dcdedb;
          --accent:#52b788; --deep:#2a4a38; --warn:#b3552e; --flag:#fdf3ec; }
  * { box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink); font-family:"Segoe UI",system-ui,sans-serif;
         margin:0; padding:26px 18px 90px; line-height:1.45; }
  .wrap { max-width:1000px; margin:0 auto; }
  .brand { font-weight:900; font-size:12px; letter-spacing:.1em; color:var(--soft); }
  h1 { font-weight:900; font-size:26px; margin:4px 0 2px; }
  .sub { color:var(--soft); font-size:14px; margin:0 0 10px; max-width:80ch; }
  .counts { display:flex; gap:22px; flex-wrap:wrap; margin:14px 0 4px; font-size:13px;
            color:var(--soft); }
  .counts b { font-size:20px; display:block; color:var(--ink); }
  .bar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:12px 0; }
  .prog { font-size:13px; color:var(--soft); }
  .auth { background:var(--panel); border-radius:12px; padding:12px 14px; margin-top:10px; }
  .aname { font-weight:800; font-size:15px; }
  .ape { font-size:12px; color:var(--soft); }
  table { width:100%; border-collapse:collapse; margin-top:7px; }
  td, th { text-align:left; padding:5px 7px; font-size:13.5px; vertical-align:top; }
  th { font-size:11px; letter-spacing:.05em; text-transform:uppercase; color:var(--deep);
       border-bottom:1px solid var(--line); }
  tr.pair { border-bottom:1px solid var(--line); }
  tr.pair.judge { background:var(--flag); }
  tr.pair.no { opacity:.45; }
  .muni { font-weight:700; }
  .why { color:var(--soft); font-size:12px; }
  .tier { font-weight:800; font-size:11px; border-radius:9px; padding:1px 7px; color:#fff; }
  .tier.A { background:var(--deep); }
  .tier.B { background:#7a9c86; }
  .tier.C { background:var(--warn); }
  .btn { font:inherit; font-weight:700; padding:3px 10px; border-radius:7px; cursor:pointer;
         border:1.5px solid var(--line); background:var(--paper); font-size:12.5px;
         margin-right:4px; }
  .btn.on { background:var(--accent); border-color:var(--accent); color:#fff; }
  .btn.off { background:var(--warn); border-color:var(--warn); color:#fff; }
  .btn.big { padding:8px 15px; font-size:14px; }
  details { margin-top:3px; }
  summary { font-size:12px; color:var(--soft); cursor:pointer; }
  .exc { font-size:12.5px; color:var(--soft); margin:3px 0 0 12px; }
  .refs { font-family:Consolas,monospace; font-size:11.5px; color:var(--soft); margin-left:12px; }
  ol.trail { margin:8px 0 0; padding-left:20px; }
  ol.trail li { margin-bottom:9px; }
  .tstep { font-weight:700; font-size:13px; }
  .doc { font-family:Consolas,monospace; font-size:11.5px; border-radius:9px;
         padding:1px 7px; color:#fff; background:#8a8a8a; }
  .doc.contract { background:var(--deep); }
  .doc.award { background:#7a9c86; }
  .doc.call { background:#b3552e; }
  .where { font-weight:400; font-size:12px; color:var(--soft); }
  .tfound { font-size:12.5px; color:var(--deep); font-weight:700; }
  .tnote { font-size:12px; color:var(--soft); font-style:italic; }
  .result { margin-top:10px; padding-top:8px; border-top:1px solid var(--line);
            font-size:13px; }
  .rline { margin-top:3px; }
  .rauth { font-weight:700; }
  .exportrow { position:sticky; bottom:0; background:var(--paper); padding:12px 0; margin-top:22px;
               border-top:1px solid var(--line); display:flex; gap:10px; align-items:center; }
  .hint { font-size:12.5px; color:var(--soft); }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">FORESTRY WORKS TRACKER · ANTI-NERO WORK LOCATIONS</div>
  <h1>Where each forest service works</h1>
  <p class="sub">Every contract states its locations the same way: the works of
  <b>Δασαρχείο X</b> lie within the <b>Δήμοι</b> A, B and C of <b>Π.Ε.</b> Y
  (NUTS: EL___). Read across all of them, that is one question asked over and
  over — does this forest service work in this δήμος — so this page asks it
  once. Each row carries what independently confirms it: the contract and its
  πρόσκληση saying the same thing, the Π.Ε. and the NUTS code printed in that
  very sentence, the authority's own Π.Ε. in our registry, and other contracts
  asserting the same pair. Rows with three or more are taken as settled and
  are folded away; the rest are yours to judge, and each carries the sentence
  it came from.</p>
  <div class="counts" id="counts"></div>
  <div class="bar">
    <button class="btn on" id="tab-pairs" onclick="setTab('pairs')">Verdicts by forest service</button>
    <button class="btn" id="tab-trail" onclick="setTab('trail')">How each contract was read</button>
  </div>
  <div class="bar" id="pairbar">
    <button class="btn" onclick="setView('judge')">Only what needs a verdict</button>
    <button class="btn" onclick="setView('all')">Everything</button>
    <button class="btn" onclick="setView('C')">Weakest evidence only</button>
    <span class="prog" id="prog"></span>
  </div>
  <div class="bar" id="trailbar" style="display:none">
    <input type="text" id="find" placeholder="filter by ΑΔΑΜ, title or authority"
           oninput="drawTrail()" style="padding:6px 10px;font:inherit;font-size:13px;
           border:1.5px solid var(--line);border-radius:8px;width:340px">
  </div>
  <div id="auths"></div>
  <div class="exportrow">
    <button class="btn big on" onclick="doExport()">Export verdicts JSON</button>
    <button class="btn" onclick="if(confirm('Reset all verdicts?')){localStorage.removeItem(LS);location.reload()}">Reset</button>
    <span class="hint">A verdict is on the pair, and applies to every contract that states it.</span>
  </div>
</div>
<script>
const DATA = __DATA__;
const LS = "municipality_pairs_v1";
let state = JSON.parse(localStorage.getItem(LS) || "{}");
let view = "judge";
const key = p => (p.authority || "?") + "|" + p.code;
const needs = p => p.tier !== "A";
const verdict = p => state[key(p)] !== undefined ? state[key(p)] : (p.tier === "A");

function counts() {
  const t = { A: 0, B: 0, C: 0 };
  DATA.pairs.forEach(p => t[p.tier]++);
  const open = DATA.pairs.filter(p => needs(p) && state[key(p)] === undefined).length;
  document.getElementById("counts").innerHTML =
    "<div><b>" + DATA.pairs.length + "</b>forest service &times; δήμος pairs</div>" +
    "<div><b>" + t.A + "</b>settled by three or more sources</div>" +
    "<div><b>" + (t.B + t.C) + "</b>need a verdict</div>" +
    "<div><b>" + open + "</b>still open</div>";
  document.getElementById("prog").textContent =
    (t.B + t.C - open) + " of " + (t.B + t.C) + " judged";
}
function setView(v) { view = v; draw(); }

function draw() {
  const root = document.getElementById("auths");
  root.innerHTML = "";
  const byAuth = new Map();
  DATA.pairs.forEach(p => {
    const a = p.authority || "(no authority named)";
    if (!byAuth.has(a)) byAuth.set(a, []);
    byAuth.get(a).push(p);
  });
  for (const [a, list] of byAuth) {
    const shown = list.filter(p => view === "all" || (view === "judge" && needs(p)) ||
                                   (view === "C" && p.tier === "C"));
    if (!shown.length) continue;
    const box = document.createElement("div");
    box.className = "auth";
    box.innerHTML = '<div class="aname">' + a + '</div><div class="ape">' +
      list.length + " δήμοι in all · " + list.filter(needs).length + " needing a verdict</div>";
    const tb = document.createElement("table");
    tb.innerHTML = "<tr><th>δήμος</th><th>Π.Ε.</th><th>what confirms it</th><th></th></tr>";
    shown.forEach(p => {
      const tr = document.createElement("tr");
      tr.className = "pair" + (needs(p) ? " judge" : "");
      const why = p.checks.length ? p.checks.join(" · ") : "nothing beyond the one sentence";
      tr.innerHTML =
        '<td><span class="muni">' + p.name + '</span> <span class="tier ' + p.tier + '">' +
          p.tier + "</span>" +
          (p.via === "rename" ? '<div class="why">' + (p.rename_note || "renamed") + "</div>" : "") +
        "</td>" +
        "<td>" + p.pe.replace("Π.Ε. ", "") + "</td>" +
        '<td><span class="why">' + why + "</span>" +
          "<details><summary>the sentence · " + p.contracts.length + " contract(s)</summary>" +
          p.excerpts.map(e => '<div class="exc">&laquo;' + e + "&raquo;</div>").join("") +
          '<div class="refs">' + p.contracts.join(" ") + "</div></details></td>";
      const td = document.createElement("td");
      const yes = document.createElement("button");
      const no = document.createElement("button");
      const paint = () => {
        const v = verdict(p);
        yes.className = "btn" + (v ? " on" : "");
        yes.textContent = "keep";
        no.className = "btn" + (v ? "" : " off");
        no.textContent = "drop";
        tr.classList.toggle("no", !v);
      };
      yes.onclick = () => {
        state[key(p)] = true;
        localStorage.setItem(LS, JSON.stringify(state));
        paint(); counts();
      };
      no.onclick = () => {
        state[key(p)] = false;
        localStorage.setItem(LS, JSON.stringify(state));
        paint(); counts();
      };
      paint();
      td.appendChild(yes);
      td.appendChild(no);
      tr.appendChild(td);
      tb.appendChild(tr);
    });
    box.appendChild(tb);
    root.appendChild(box);
  }
  counts();
}
draw();

function drawTrail() {
  const root = document.getElementById("auths");
  root.innerHTML = "";
  const q = (document.getElementById("find").value || "").trim().toUpperCase();
  let shown = 0;
  DATA.rows.forEach(r => {
    if (q && !(r.ref + " " + r.title + " " + r.stored_authorities.join(" "))
              .toUpperCase().includes(q)) return;
    shown++;
    const box = document.createElement("div");
    box.className = "auth";
    box.innerHTML = '<div class="aname">' + r.ref + '</div><div class="ape">' +
      r.title + "</div><div class=\"ape\">authorities on file: " +
      (r.stored_authorities.join(", ") || "—") + " · curated Π.Ε.: " +
      (r.contract_pes.join(", ") || "—") + "</div>";
    const ol = document.createElement("ol");
    ol.className = "trail";
    (r.trail || []).forEach(st => {
      const li = document.createElement("li");
      li.innerHTML =
        '<div class="tstep">' + st.step +
          ' <span class="doc ' + st.kind + '">' + st.doc + '</span>' +
          ' <span class="where">' + st.where + '</span></div>' +
        (st.authorities && st.authorities.length
          ? '<div class="tfound">→ ' + st.authorities.join(", ") + "</div>" : "") +
        (st.note ? '<div class="tnote">' + st.note + "</div>" : "") +
        '<div class="exc">&laquo;' + st.quote + "&raquo;</div>";
      ol.appendChild(li);
    });
    box.appendChild(ol);
    // what was taken out of all that, per authority
    const res = document.createElement("div");
    res.className = "result";
    res.innerHTML = "<b>read from the above</b>";
    (r.statements || []).forEach(s => {
      const auth = s.authorities.join(", ") || "not attributed to an authority";
      (s.groups || []).forEach(g => {
        const line = document.createElement("div");
        line.className = "rline";
        line.innerHTML = "<span class=\"rauth\">" + auth + "</span> · " +
          (g.pe_stated || "Π.Ε. not stated") + (g.nuts ? " " + g.nuts : "") + " · " +
          g.municipalities.map(m => m.name).join(", ") +
          (s.from_call ? ' <span class="src">from the call</span>' : "");
        res.appendChild(line);
      });
    });
    if (!(r.statements || []).length) {
      res.innerHTML += '<div class="rline">no δήμος stated anywhere — the ' +
        "authorities above are the finest location this contract gives</div>";
    }
    box.appendChild(res);
    root.appendChild(box);
  });
  document.getElementById("prog").textContent = shown + " contracts";
}

let tab = "pairs";
function setTab(t) {
  tab = t;
  document.getElementById("tab-pairs").className = "btn" + (t === "pairs" ? " on" : "");
  document.getElementById("tab-trail").className = "btn" + (t === "trail" ? " on" : "");
  document.getElementById("pairbar").style.display = t === "pairs" ? "" : "none";
  document.getElementById("trailbar").style.display = t === "trail" ? "" : "none";
  t === "pairs" ? draw() : drawTrail();
}

function doExport() {
  // a verdict is on the PAIR; it applies to every contract that states it
  const keep = new Set(DATA.pairs.filter(verdict).map(key));
  const out = {};
  DATA.pairs.forEach(p => {
    if (!keep.has(key(p))) return;
    p.contracts.forEach(ref => {
      out[ref] = out[ref] || { municipalities: [] };
      out[ref].municipalities.push({
        code: p.code, name: p.name, pe: p.pe, authority: p.authority,
        via: p.via, tier: p.tier, confirmed_by: p.checks, sources: p.sources,
        excerpt: p.excerpts[0] || null
      });
    });
  });
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "contract_municipalities.json";
  a.click();
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
