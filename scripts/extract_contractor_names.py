"""Propose ONE canonical display name per contractor ΑΦΜ.

Why
---
The same company reaches the site under different names depending on the
surface: the ranking prints the ΚΗΜΔΗΣ registry spelling, the HQ map prints
the ΓΕΜΗ/VIES registered name. For 43 ΑΦΜ those differ, and for a few they are
not variants at all — 998342580 is «Δ ΚΑΦΕΤΖΗΣ ΚΑΙ ΣΙΑ ΟΕ» in the ranking and
«ΒΙΟΣ Α.Ε.» on the map, one company that renamed itself, sixth largest in the
programme. Searching «BIODASOS» finds the joint venture but not the firm.

Rules (user, 2026-08-20)
------------------------
1. The canonical name is the REGISTERED one (ΓΕΜΗ, else VIES), **shortened**:
   the distinctive head plus the legal form as an abbreviation, so «ΗΛΙΟΧΩΡΑ
   ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΒΙΟΜΗΧΑΝΙΚΩΝ…» becomes «ΗΛΙΟΧΩΡΑ Α.Ε.». The full legal
   name stays on the contractor page underneath.
2. A person is written **ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ** — the patronymic is
   what tells two same-named people apart, and this dataset holds a father and
   a son (025751414 ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ and 113411710 ΓΚΑΡΓΚΑΝΙΤΗΣ
   ΠΑΝΑΓΙΩΤΗΣ ΤΟΥ ΛΑΜΠΡΟΥ). But **only where a document holds it, or where a
   document and the register together prove it** (user, 2026-08-20): nothing
   is invented, and a person no document names in full is written ΕΠΩΝΥΜΟ
   ΟΝΟΜΑ. Persons are identified by ΓΕΜΗ's legal form «ΑΤΟΜΙΚΗ», never guessed
   from the shape of the name.
3. A renamed company shows **today's name everywhere**; the contract page adds
   «signed as …» where its own document says something else.

Nothing here is rewritten in the database: `contractors.name` keeps every
registry spelling, which stays searchable and is shown as evidence.

A patronymic is read from the signed documents (`name_evidence.json`, built
by scripts/extract_name_evidence.py), and the register supplies its SPELLING
while the document supplies the proof — that is what keeps «του ΚΩΝ/ΝΟΥ» from
becoming a name and a mis-rendered 2018 PDF from writing «ΤΟΥ ΑΘΑΝΑΣΥΟΥ». The
genitive is searched only AFTER the surname: «β) του Ευάγγελο Μαναρίτσα του
Κωνσταντίνου» has a «του» on either side, and the first one is the article of
the given name. Where register and documents disagree, the row says CONFLICT
and carries no patronymic — a human decides.

Usage:
    .venv/Scripts/python scripts/extract_contractor_names.py
    .venv/Scripts/python scripts/extract_contractor_names.py --curate
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from khmdhs.config import DEFAULT_DB

REVIEW = ROOT / "data" / "processed" / "contractor_names_review.json"
CURATED = ROOT / "khmdhs" / "data" / "contractor_display_names.json"
NAMES_CACHE = ROOT / "data" / "processed" / "gemi_names.json"
# how the signed documents write each name (scripts/extract_name_evidence.py)
EVIDENCE = ROOT / "data" / "processed" / "name_evidence.json"

# ΓΕΜΗ legal form → the abbreviation Greek companies actually print
FORM_SUFFIX = {
    "ΑΕ": "Α.Ε.", "ΕΠΕ": "Ε.Π.Ε.", "ΙΚΕ": "Ι.Κ.Ε.",
    "ΟΕ": "Ο.Ε.", "ΕΕ": "Ε.Ε.", "Κοινοπραξία": "Κ/Ξ",
}
# the words that open a legal-form tail: everything from here on is form, not
# identity («ΗΛΙΟΧΩΡΑ **ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΒΙΟΜΗΧΑΝΙΚΩΝ…**»)
FORM_HEADS = (
    "ΑΝΩΝΥΜΗ", "ΑΝΩΝΥΜΟΣ", "ΕΤΑΙΡΕΙΑ", "ΕΤΑΙΡΙΑ", "ΕΤΑΙΡΕΙΑΣ",
    "ΙΔΙΩΤΙΚΗ ΚΕΦΑΛΑΙΟΥΧΙΚΗ", "ΟΜΟΡΡΥΘΜΗ", "ΕΤΕΡΟΡΡΥΘΜΗ", "ΜΟΝΟΠΡΟΣΩΠΗ",
)
# forms already written as an abbreviation — leave the name alone
# forms already written as an abbreviation — leave the name alone. BOTH
# alphabets: «GREEN CONSTRUCTION A.T.E.» is Latin and was given «Α.Ε.» on top.
ABBREV = re.compile(
    r"(?:^|\s)(?:[ΑA]\.?[ΤT]?\.?[ΕE]\.?[ΒB]?\.?[ΕE]?\.?|[ΕE]\.?[ΠP]\.?[ΕE]\.?"
    r"|[ΙI]\.?[ΚK]\.?[ΕE]\.?|[ΟO]\.?[ΕE]\.?|[ΕE]\s?\.?\s?[ΕE]\.?"
    r"|[ΚK]\s?/?\s?[ΞX]|S\.?A\.?|LTD\.?)\s*$")


def _letters(s: str) -> str:
    """Letters and digits only, accents stripped, Latin homoglyphs pulled onto
    Greek — for asking whether two spellings are the same name written
    differently. VIES returns «T ΚΑΙ T ΚΑΤΑΣΚΕΥΕΣ ΑΕ» for what the registry
    spells «Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.»."""
    up = _accents((s or "").upper())
    up = up.translate(str.maketrans("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"))
    up = re.sub(r"(?:^|\s)ΚΑΙ(?=\s|$)", " & ", up)   # VIES writes ΚΑΙ for &
    return re.sub(r"[^Α-Ω0-9]", "", up)


log = logging.getLogger(__name__)


def _strip_status(name: str) -> str:
    """ΓΕΜΗ prefixes a struck-off company's name with its status — that is a
    state, not part of the name."""
    return re.sub(r"^\s*\((ΔΙΑΓΡΑΦΗ|ΔΙΑΓΡΑΦΗΚΕ|ΔΙΕΓΡΑΦΗ|ΔΙΑΓΡΑΜΜΕΝΗ|"
                  r"ΥΠΟ ΕΚΚΑΘΑΡΙΣΗ)\)\s*", "", (name or "").strip())


def _clean(name: str) -> str:
    name = _strip_status(name)
    name = name.replace("«", "").replace("»", "").replace(" ", " ")
    return re.sub(r"\s+", " ", name).strip(" ,")


def _accents(s: str) -> str:
    n = unicodedata.normalize("NFD", s)
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


QUOTED = re.compile(r"[«\"“]([^«»\"“”]{4,90})[»\"”]")


# «…ΕΤΑΙΡΕΙΑ ΠΕΡΙΟΡΙΣΜΕΝΗΣ ΕΥΘΥΝΗΣ» και διακριτικό τίτλο «ΕΛ.ΤΕ. Ε.Π.Ε.»»
_DT = r"(?:δ\.?\s?τ\.?|διακριτικ[οό][νς]?\s+τ[ιί]τλ[οό][νς]?)\s*"
TRADE_QUOTED = re.compile(_DT + r"[«\"“]\s*([^«»\"“”]{3,60}?)\s*[»\"”]",
                          re.IGNORECASE)
TRADE_PLAIN = re.compile(_DT + r"([^,;:()«»]{3,46}?)(?=\s*[,;:)]|\s{2,}|$)",
                         re.IGNORECASE)


def declared_trade_title(mentions: list[dict],
                         head: str = "") -> tuple[str, str, int]:
    """The δ.τ. a document declares in words → (name, source, times).

    It needs no resemblance to the registered name — «ΠΙ ΕΝΤ ΣΙ ΝΤΙΒΕΛΟΠΜΕΝΤ …»
    trades as «P. & C. DEVELOPMENT S.A.» — so two guards replace that
    resemblance: the title must carry a legal form (ΑΒΒREV), which the street
    address that often follows it does not, and it must be declared within
    150 characters of THIS contractor's ΑΦΜ, so a fellow invitee's δ.τ. in the
    same call cannot be borrowed.
    """
    seen: dict[str, list] = {}
    for m in mentions:
        text = " ".join(m["excerpt"].split())
        near = max(0, len(text) - 180)
        for pat in (TRADE_QUOTED, TRADE_PLAIN):
            for hit in pat.finditer(text):
                if hit.start() < near:
                    continue
                q = _clean(hit.group(1))
                if len(q) < 4 or len(q) > 46 or not ABBREV.search(q):
                    continue
                row = seen.setdefault(_letters(q), [q, m["source"], 0])
                row[2] += 1
    h = _accents(head.upper())[:6]
    ours = [v for v in seen.values()
            if v[2] > 1 or (h and h in _accents(v[0].upper()))]
    if not ours:
        return "", "", 0
    best = max(ours, key=lambda v: v[2])
    return best[0], best[1], best[2]


VENTURE_NAME = re.compile(
    r"(?:κοινοπραξ[ίι]α[ςν]?|[εέ]νωση[ςν]?|σ[υύ]μπραξη[ςν]?)\s*"
    r"(?:οικονομικ[ώω]ν\s+φορ[έε]ων\s*)?"
    r"(?:με\s+την\s+επωνυμ[ίι]α\s*)?[«\"“]\s*([^«»\"“”]{6,90}?)\s*[»\"”]",
    re.IGNORECASE)


def venture_name(mentions: list[dict]) -> tuple[str, str, int]:
    """The name a venture's own contract puts in quotation marks → (name,
    source, times). Ventures are named after their members, so no register
    holds a tidy version: the contract is the only place the name is written
    out properly."""
    seen: dict[str, list] = {}
    for m in mentions:
        text = " ".join(m["excerpt"].split())
        for hit in VENTURE_NAME.finditer(text):
            q = _clean(hit.group(1))
            if len(q) < 8 or q.upper().startswith("ΕΝΩΣΗ ΟΙΚΟΝΟΜΙΚ"):
                continue
            # «ΒΙΟDΑSΟS» — a PDF that renders one word in two alphabets is not
            # the place to read a name from; the registry spelling is cleaner
            if any(len(w) > 3
                   and any("Ͱ" <= c <= "Ͽ" for c in w)
                   and any(c.isascii() and c.isalpha() for c in w)
                   for w in q.split()):
                continue
            row = seen.setdefault(_letters(q), [q, m["source"], 0])
            row[2] += 1
    if not seen:
        return "", "", 0
    best = max(seen.values(), key=lambda v: (v[2], len(v[0])))
    return best[0], best[1], best[2]


def documented_short_form(head: str, mentions: list[dict]) -> tuple[str, str, int]:
    """The short name the DOCUMENTS themselves use → (name, source, times).

    A company's contracts quote it twice: once in full and once as the δ.τ. its
    letterhead carries — «ΒΙΟΛΙΑΠ Α.Τ.Ε.Β.Ε.», «ΑΙΑΣ Α.Τ.Ε.», «NOVALIS Ε.Π.Ε.».
    That is the form a reader recognises, and unlike a rule it cannot invent
    «Α.Ε.» for a company that writes «Α.Τ.Ε.Β.Ε.». Only quoted forms that carry
    the company's head and end in a legal-form abbreviation count.
    """
    h = _accents(head.upper())[:6]
    if not h:
        return "", "", 0
    seen: dict[str, list] = {}
    for m in mentions:
        for q in QUOTED.findall(" ".join(m["excerpt"].split())):
            q = _clean(q)
            if len(q) > 42 or h not in _accents(q.upper()) or not ABBREV.search(q):
                continue
            hit = seen.setdefault(_letters(q), [q, m["source"], 0])
            hit[2] += 1
    if not seen:
        return "", "", 0
    best = max(seen.values(), key=lambda v: v[2])
    return best[0], best[1], best[2]


# words that follow «ΚΑΙ» inside a company's OBJECT, never between partners
TRADE_WORDS = (
    "ΕΜΠΟΡΙΚ", "ΤΕΧΝΙΚ", "ΒΙΟΜΗΧΑΝ", "ΤΟΥΡΙΣΤΙΚ", "ΞΕΝΟΔΟΧΕΙΑΚ", "ΚΤΗΜΑΤΙΚ",
    "ΛΑΤΟΜΙΚ", "ΝΑΥΤΙΛΙΑΚ", "ΕΝΕΡΓΕΙΑΚ", "ΕΚΜΕΤΑΛΛΕΥΣ", "ΚΑΤΑΣΚΕΥ", "ΜΕΛΕΤ",
    "ΥΠΗΡΕΣΙ", "ΕΡΓΩΝ", "ΑΝΑΠΤΥΞ", "ΠΕΡΙΒΑΛΛΟΝΤ", "ΓΕΩΡΓΙΚ", "ΚΤΗΝΙΑΤΡΙΚ",
    "ΟΙΚΟΔΟΜΙΚ", "ΑΓΡΟΤΙΚ", "ΔΑΣΙΚ", "ΧΑΡΤΟΓΡΑΦ", "ΕΙΔΩΝ", "ΠΩΛΗΣ",
)

FORM_DOTS = {
    "ΑΕ": "Α.Ε.", "ΑΤΕ": "Α.Τ.Ε.", "ΑΤΕΕ": "Α.Τ.Ε.Ε.", "ΑΤΕΒΕ": "Α.Τ.Ε.Β.Ε.",
    "ΟΕ": "Ο.Ε.", "ΕΕ": "Ε.Ε.", "ΙΚΕ": "Ι.Κ.Ε.", "ΕΠΕ": "Ε.Π.Ε.",
    "ΑΒΕΕ": "Α.Β.Ε.Ε.", "ΕΠΕΕ": "Ε.Π.Ε.Ε.",
}


LOOKALIKES = str.maketrans({
    "∆": "Δ", "Ω": "Ω", "µ": "μ",          # math symbols pdftotext emits
    **{k: v for k, v in zip("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ")},
})


def _degreeklish(word: str) -> str:
    """Latin letters inside a Greek word are homoglyphs, not letters."""
    has_greek = any("\u0370" <= c <= "\u03ff" for c in word)
    has_latin = any("A" <= c <= "Z" or "a" <= c <= "z" for c in word)
    if has_greek and has_latin:
        return word.translate(LOOKALIKES)
    return word.translate(str.maketrans({"∆": "Δ", "µ": "μ"}))


def polish(name: str) -> str:
    """One typography for every display name (user, 2026-08-20): CAPITALS, the
    legal form always dotted, «&» wherever a document writes «ΚΑΙ» between
    partners. The verbatim spellings stay in the database and stay searchable —
    this is how the name is PRINTED, nothing more."""
    # per LETTER-RUN, not per word: «BIODASOS-ΤΕΧΝΗ» is one word in two
    # alphabets legitimately, «ΠΑΠΑ∆ΟΠΟΥΛΟΣ» is one run in one
    # the math symbols first — «∆» is not a letter, so a per-run pass steps
    # over it and «ΠΑΠΑ∆ΟΠΟΥΛΟΣ» keeps its INCREMENT sign
    base = _accents(_clean(name).upper()).translate(
        str.maketrans({"∆": "Δ", "µ": "μ", "Ω": "Ω"}))
    out = re.sub(r"[^\W\d_]+", lambda m: _degreeklish(m.group(0)), base)
    # «ΚΑΙ» joins partners, «και» inside a title describes a trade: «ΑΝΩΝΥΜΗ
    # ΕΝΕΡΓΕΙΑΚΗ ΞΕΝΟΔΟΧΕΙΑΚΗ ΚΑΙ ΕΚΜΕΤΑΛΛΕΥΣΕΩΣ ΑΚΙΝΗΤΩΝ» is one company's
    # object, not two companies
    out = re.sub(r"\s+ΚΑΙ\s+(?=ΣΙΑ\b|ΣΥΝΕΡΓΑΤΕΣ\b)", " & ", out)
    out = re.sub(r"\s+ΚΑΙ\s+(?![Α-Ω]*(?:" + "|".join(TRADE_WORDS) + r"))"
                 r"(?=[Α-ΩA-Z])", " & ", out)
    def _dot(m):
        return FORM_DOTS.get(m.group(1).replace(".", ""), m.group(0))
    out = re.sub(r"(?<=[\s(])((?:[Α-Ω]\.?){2,5})\s*$", _dot, out)
    # «Ε.Ε» / «Ι.Κ.Ε» — a form that lost its last dot
    out = re.sub(r"((?:[Α-Ω]\.){1,4}[Α-Ω])\s*$", lambda m: m.group(1) + ".", out)
    # a Greek legal form typed in Latin letters: «E.E.» → «Ε.Ε.». S.A. and LTD
    # are Latin forms of Latin names and stay.
    def _greek_form(m):
        return m.group(0).translate(str.maketrans("ABEZHIKMNOPTYX",
                                                  "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"))
    out = re.sub(r"(?<=[\s.])(?:[ABEZHIKMNOPTYX]\.){2,4}\s*$", _greek_form, out)
    return re.sub(r"\s+", " ", out).strip()


# every spelling the papers use for «this is a joint venture», so it can be
# taken off the name and put back once, the same way, at the front
VENTURE_MARK_HEAD = re.compile(
    r"^\s*(?:ΚΟΙΝΟΠΡΑΞΙΑ[Σ]?|Κ\s?/?\s?ΞΙΑ|Κ\s?/?\s?Ξ|ΚΞ)\b[\s.:,-]*"
    r"(?:\(\s*Κ\s?/?\s?Ξ\s*\)[\s.:,-]*)?"
    r"(?:ΟΙΚΟΝΟΜΙΚΩΝ\s+ΦΟΡΕΩΝ[\s.:,-]*)?", re.IGNORECASE)
VENTURE_MARK_TAIL = re.compile(
    r"[\s.,-]*(?:ΚΟΙΝΟΠΡΑΞΙΑ[Σ]?|Κ\s?/?\s?ΞΙΑ|Κ\s?/?\s?Ξ|ΚΞ)\s*$",
    re.IGNORECASE)


def mark_venture(name: str) -> str:
    """«Κ/Ξ » once, at the front (user, 2026-08-20). The papers write the
    marker four ways and leave it out of 20 names altogether, and a venture
    that prints as two people's names reads like two contractors."""
    core = VENTURE_MARK_TAIL.sub("", VENTURE_MARK_HEAD.sub("", name)).strip(" -–,")
    return f"Κ/Ξ {core}" if core else name


def shorten(name: str, form: str | None) -> str:
    """The distinctive head plus the legal form as an abbreviation."""
    name = _clean(name)
    if not name:
        return name
    if ABBREV.search(name):              # already «… Α.Ε.» / «… Ε.Ε.»
        return name
    up = _accents(name.upper())
    cut = len(name)
    for head in FORM_HEADS:
        m = re.search(rf"\b{head}\b", up)
        if m and m.start() > 0:
            cut = min(cut, m.start())
    head_part = name[:cut].strip(" ,-–")
    suffix = FORM_SUFFIX.get(form or "")
    if not head_part:
        return name
    return f"{head_part} {suffix}".strip() if suffix else head_part


GENITIVE = ((r"ΟΣ$", "ΟΥ"), (r"ΗΣ$", "Η"), (r"ΑΣ$", "Α"))
# a genitive that follows a name without being one: «του Δήμου Μαντουδίου»
NOT_A_NAME = {"ΔΗΜΟΥ", "ΕΡΓΟΥ", "ΝΟΜΟΥ", "ΑΡΘΡΟΥ", "ΕΤΟΥΣ", "ΤΑΜΕΙΟΥ",
              "ΥΠΟΥΡΓΕΙΟΥ", "ΑΝΑΔΟΧΟΥ", "ΠΑΡΟΝΤΟΣ", "ΙΔΙΟΥ", "ΝΟΜΙΜΟΥ",
              "ΚΡΑΤΟΥΣ", "ΔΗΜΟΣΙΟΥ", "ΜΗΝΟΣ", "ΣΥΝΟΛΟΥ", "ΟΠΟΙΟΥ", "ΥΠΕΝ",
              "ΠΡΟΕΔΡΟΥ", "ΣΥΜΒΟΥΛΙΟΥ", "ΝΟΜΟΘΕΤΙΚΟΥ", "ΦΠΑ", "ΑΦΜ"}
INITIAL = re.compile(r"^([Α-Ω]{1,4})\.$")


def _stem(word: str, keep: int = 4) -> str:
    """Greek surnames inflect at the ending — ΦΙΛΙΠΠΑΚΗΣ / Φιλιππάκη — so a
    document is searched by the stem, never by the nominative."""
    u = _accents(word.upper())
    return u[:max(keep, len(u) - 2)]


def documented_patronymic(surname: str, given: str, register_patr: str,
                          register_initial: str, mentions: list[dict],
                          already_genitive: bool = False) -> tuple[str, str, str]:
    """What the DOCUMENTS say the patronymic is → (genitive, how, source).

    Rule (user, 2026-08-20): «ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ» is written only
    where a document already holds the patronymic, or where a document and the
    register together make it provable — a document's initial «ΒΕΛΩΝΗΣ ΝΙΚ.
    ΓΕΩΡΓΙΟΣ» beside ΓΕΜΗ's ΝΙΚΟΛΑΟΣ proves ΤΟΥ ΝΙΚΟΛΑΟΥ. Nothing is invented:
    where neither holds it, the person is written ΕΠΩΝΥΜΟ ΟΝΟΜΑ and the layer
    says so. The declension rule (-ΟΣ→-ΟΥ …) never runs on its own evidence.
    """
    sstem = _stem(surname)
    reg = _accents((register_patr or "").upper())
    reg_gen = reg
    if not already_genitive:
        for pat, rep in GENITIVE:
            if re.search(pat, reg):
                reg_gen = re.sub(pat, rep, reg)
                break
    gens: dict[str, str] = {}      # genitive → the ΑΔΑΜ that wrote it
    inits: dict[str, str] = {}     # initial → the ΑΔΑΜ that wrote it
    for m in mentions:
        text = _accents(m["excerpt"].upper())
        for hit in re.finditer(re.escape(sstem), text):
            # ONLY after the surname. «β) του Ευάγγελο Μαναρίτσα του
            # Κωνσταντίνου» has a «του» on either side, and the one in front
            # is the article of the given name, not the patronymic.
            after = text[hit.end():hit.end() + 90]
            g = re.search(r"\bΤΟΥ\s+([Α-ΩA-Z]{3,}(?:/[Α-ΩA-Z]+)?)", after)
            if g and g.group(1) not in NOT_A_NAME:
                gens.setdefault(g.group(1), m["source"])
            for i in re.finditer(r"\b([Α-Ω]{1,4})\.",
                                 text[max(0, hit.start() - 40):hit.end() + 40]):
                inits.setdefault(i.group(1), m["source"])
    if reg:
        # The register spells it, the document proves it. Preferring the
        # register's own spelling is what keeps «του ΚΩΝ/ΝΟΥ» from becoming a
        # name and a mis-rendered PDF from writing «ΤΟΥ ΑΘΑΝΑΣΥΟΥ».
        for cand, src in gens.items():
            head = cand.split("/")[0]
            if _stem(reg) in cand or _stem(cand) in reg or (
                    len(head) >= 3 and reg.startswith(head)):
                if already_genitive and cand != reg and "/" not in cand:
                    return cand, "document (the register spells it otherwise)", src
                return reg_gen, "document, spelled from the register", src
        for ini, src in inits.items():
            if len(ini) >= 1 and reg.startswith(ini):
                return reg_gen, "register, proved by a document's initial", src
        if gens:
            first = next(iter(gens.items()))
            return "", f"CONFLICT: register says {reg}, {first[1]} says " \
                       f"ΤΟΥ {first[0]}", first[1]
        return "", "no patronymic documented", ""
    # no register patronymic: a document alone must say it twice, or once with
    # the register's initial behind it
    for cand, src in gens.items():
        seen = sum(1 for m in mentions if cand in _accents(m["excerpt"].upper()))
        if seen > 1 or (register_initial and cand.startswith(register_initial)):
            return cand, "document", src
    return "", "no patronymic documented", ""


def person_name(registered: str, spellings: list[str],
                mentions: list[dict] | None = None) -> tuple[str, str, str]:
    """«ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ» where that is documented → (name, how,
    source ΑΔΑΜ).

    ΓΕΜΗ writes a sole trader as «ΣΙΔΕΡΗ ΜΑΡΙΑ ΔΗΜΗΤΡΙΟΣ» — surname, name,
    patronymic in the nominative — and sometimes as «ΦΙΛΙΠΠΑΚΗΣ Μ. ΠΑΝΤΕΛΗΣ»,
    where the middle token is the patronymic's INITIAL and the third is the
    given name. Trade descriptions («— εργολήπτης δημοσίων έργων») are not
    part of a name.
    """
    core = re.split(r"\s+[—–]\s+|\s+-\s+", _clean(registered))[0]
    parts = core.split()
    if len(parts) < 2:
        return core, "registered", ""
    # «ΕΥΑΓΓΕΛΟΣ ΠΑΠΠΑΣ ΤΟΥ ΓΕΩΡΓΙΟΥ» — VIES writes some names given-first and
    # with the patronymic spelled out. Split at the ΤΟΥ, then let the papers
    # say which of the two names in front is the surname.
    if "ΤΟΥ" in [_accents(w.upper()) for w in parts[1:]]:
        idx = [_accents(w.upper()) for w in parts].index("ΤΟΥ")
        head, tail = parts[:idx], " ".join(parts[idx + 1:])
        if len(head) == 2:
            a, b = head
            texts = [_accents(x.upper()) for x in spellings] + [
                _accents(m["excerpt"].upper()) for m in (mentions or [])]
            fwd = sum(t.count(f"{_accents(a.upper())} {_accents(b.upper())}")
                      for t in texts)
            rev = sum(t.count(f"{_accents(b.upper())} {_accents(a.upper())}")
                      for t in texts)
            head = [b, a] if rev > fwd else [a, b]
        gen, how, src = documented_patronymic(head[0], head[-1], tail, "",
                                              mentions or [], already_genitive=True)
        name = f"{head[0]} {' '.join(head[1:])}".strip()
        if gen:
            return f"{name} ΤΟΥ {gen}", how, src
        return f"{name} ΤΟΥ {_accents(tail.upper())}", "registered", ""

    surname, register_initial = parts[0], ""
    m = INITIAL.match(parts[1])
    if m and len(parts) > 2:                    # «ΦΙΛΙΠΠΑΚΗΣ Μ. ΠΑΝΤΕΛΗΣ»
        register_initial, given_words, patr = m.group(1), parts[2:], ""
    elif len(parts) > 2:
        # the patronymic is the LAST token; a double given name sits between
        # it and the surname («ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚ ΚΩΝΣΤΑΝΤΙΝΟΣ»)
        given_words, patr = parts[1:-1], parts[-1]
    else:
        given_words, patr = parts[1:], ""
    # the register truncates: «ΛΙΑΡΟΣΤΑΘΗΣ ΒΑΣΙΛ ΚΩΝΣΤΑΝΤΙΝΟΣ» for ΒΑΣΙΛΕΙΟΣ,
    # «ΒΑΣΙΛΙΚ» for ΒΑΣΙΛΙΚΗ. A spelling that writes it in full wins.
    full = []
    for word in given_words:
        best = word
        for sp in spellings:
            for w in _clean(sp).split():
                u = _accents(w.upper())
                if len(u) > len(best) and u.startswith(_accents(word.upper())):
                    best = w.upper()
        full.append(best)
    given = " ".join(full)
    gen, how, src = documented_patronymic(surname, given, patr,
                                          register_initial, mentions or [])
    if not gen:
        return f"{surname} {given}", how, ""
    return f"{surname} {given} ΤΟΥ {gen}", how, src


def build(conn: sqlite3.Connection) -> dict:
    evidence: dict[str, list[dict]] = {}
    if EVIDENCE.exists():
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    else:
        logging.warning("%s missing — run scripts/extract_name_evidence.py; "
                        "without it no patronymic can be documented",
                        EVIDENCE.name)
    spellings: dict[str, list[str]] = {}
    for r in conn.execute("SELECT vat_number, name FROM contractors"):
        v = (r[0] or "").strip()
        n = _clean(r[1] or "")
        if v and n and n not in spellings.setdefault(v, []):
            spellings[v].append(n)
    for r in conn.execute("SELECT member_vat, member_name FROM consortium_members "
                          "WHERE member_name IS NOT NULL"):
        v = (r[0] or "").strip()
        n = _clean(r[1])
        if n and n not in spellings.setdefault(v, []):
            spellings[v].append(n)

    reg: dict[str, dict] = {}
    for r in conn.execute("SELECT vat_number, legal_name, gemi, gemi_legal_type, "
                          "gemi_status FROM contractor_locations"):
        reg[(r[0] or "").strip()] = {"name": _clean(r[1] or ""), "gemi": r[2],
                                     "form": r[3], "status": r[4]}
    if NAMES_CACHE.exists():
        for v, hit in json.loads(NAMES_CACHE.read_text(encoding="utf-8")).items():
            if hit.get("name") and v not in reg:
                reg[v] = {"name": _clean(hit["name"]), "gemi": hit.get("gemi"),
                          "form": None, "status": None}

    in_scope = {r[0] for r in conn.execute(
        "SELECT DISTINCT co.vat_number FROM contractors co "
        "JOIN contract_scope s USING (reference_number) WHERE s.in_scope = 1")}
    ventures = {r[0] for r in conn.execute("SELECT vat_number FROM consortiums")}
    members = {r[0] for r in conn.execute(
        "SELECT DISTINCT member_vat FROM consortium_members")}
    eur = {r[0]: r[1] for r in conn.execute(
        "SELECT co.vat_number, ROUND(SUM(k.total_cost_without_vat), 2) "
        "FROM contractors co JOIN contracts k USING (reference_number) "
        "JOIN contract_scope s USING (reference_number) "
        "WHERE s.in_scope = 1 GROUP BY co.vat_number")}

    rows = []
    for vat in sorted(set(spellings) | set(reg) & (in_scope | members)):
        sp, source = spellings.get(vat, []), ""
        r = reg.get(vat, {})
        registered, form = r.get("name") or "", r.get("form")
        # a registry spelling that is the SAME name better punctuated wins:
        # VIES is the source of 138 of the registered names and it strips
        # «&», «.» and «-», so «Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.» comes back as «T ΚΑΙ T
        # ΚΑΤΑΣΚΕΥΕΣ ΑΕ»
        # among the spellings that ARE this name, take the best-typed one:
        # the registry holds both «Τ ΚΑΙ Τ ΚΑΤΑΣΚΕΥΕΣ» and «Τ & Τ ΚΑΤΑΣΚΕΥΕΣ»
        same = [x for x in sp if _letters(x) == _letters(registered)]
        better = max(same, key=lambda x: len(re.findall(r"[^Α-Ωα-ωA-Za-z0-9 ]", x)),
                     default=None)
        # ΓΕΜΗ's legal form is the first answer, but it is missing for every
        # ΑΦΜ that reached us through a curated venture membership. Then the
        # question is answered by the NAME — no company marker in it — plus a
        # patronymic, its own or one the documents carry.
        core = re.split(r"\s+[—–]\s+|\s+-\s+", _clean(registered))[0]
        parts = core.split() or [""]
        # stems carry no closing boundary — «ΑΝΩΝΥΜ\b» does not match
        # «ΑΝΩΝΥΜΗ» — and the abbreviations end in a dot, where \b fails too
        company_marker = bool(re.search(
            r"(ΕΤΑΙΡ|ΑΝΩΝΥΜ|ΚΟΙΝΟΠΡΑΞ|ΜΟΝΟΠΡΟΣΩΠ|ΤΕΧΝΙΚ|ΕΜΠΟΡΙΚ|ΒΙΟΜΗΧΑΝ"
            r"|ΚΑΤΑΣΚΕΥ|ΜΕΛΕΤ|\bΣΙΑ\b|\bΑ\.?Ε\.?|\bΟ\.?Ε\.?|\bΕ\.?Ε\.?"
            r"|\bΙ\.?Κ\.?Ε\.?|\bΕ\.?Π\.?Ε\.?|\bΑ\.?Τ\.?Ε|\bΚ/?Ξ)",
            _accents(core.upper())) or bool(ABBREV.search(_clean(registered)))
            or bool(re.search(r"(?:^|\s)(?:[Α-ΩA-Z]\s){1,3}[Α-ΩA-Z]\s*$",
                              _accents(core.upper()))))
        is_person = form == "ΑΤΟΜΙΚΗ" or (
            2 <= len(parts) <= 4 and not company_marker and (
                bool(re.search(r"\bΤΟΥ\s+[Α-Ω]{3,}", _accents(core.upper())))
                or bool(documented_patronymic(
                    parts[0], parts[1], " ".join(parts[2:]), "",
                    evidence.get(vat, []))[0])))
        if form == "Κοινοπραξία" or vat in ventures:
            # a venture's name IS a composition of its members' names and its
            # contracts spell it properly; the register mangles it
            kind = "venture"
            doc, doc_src, times = venture_name(evidence.get(vat, []))
            if doc:
                proposed, source = doc, doc_src
                how = f"the name its own contract quotes ({times}×)"
            else:
                # prefer a spelling whose words keep to ONE alphabet: the
                # registry holds «BIODASOS-ΤΕΧΝΗ» beside the mangled
                # «ΒΙΟDΑSΟS-ΤΕΧΝΗ», and only one of them is a name
                clean = [x for x in sp if not any(
                    len(w) > 3 and any("Ͱ" <= c <= "Ͽ" for c in w)
                    and any(c.isascii() and c.isalpha() for c in w)
                    for w in x.split())]
                pool = clean or sp
                proposed = max(pool, key=len) if pool else _clean(registered)
                how = "no contract quotes it; registry spelling"
        elif registered and is_person:
            proposed, how, source = person_name(registered, sp,
                                                evidence.get(vat, []))
            kind = "person"
        elif better or registered:
            kind = "company"
            head = _clean(registered or better).split()[0]
            doc, doc_src, times = declared_trade_title(evidence.get(vat, []),
                                                       head)
            if doc:
                how = f"the δ.τ. its documents declare ({times}×)"
            else:
                doc, doc_src, times = documented_short_form(head,
                                                            evidence.get(vat, []))
                how = f"the short name its own documents use ({times}×)"
            if doc:
                proposed, source = doc, doc_src
            elif better:
                proposed = shorten(better, form)
                how = "registered name, as the registry spells it"
            else:
                proposed, how = shorten(registered, form), "registered, shortened"
        else:
            proposed = max(sp, key=len) if sp else vat
            how, kind = "no registered name; longest registry spelling", "unknown"
        if kind != "person":            # a person's name is not an acronym
            proposed = polish(proposed)
        if kind == "venture":
            proposed = mark_venture(proposed)
        rows.append({
            "vat": vat, "proposed": proposed, "how": how, "kind": kind,
            "registered": registered, "form": form, "status": r.get("status"),
            "gemi": r.get("gemi"), "spellings": sp, "source": source,
            "in_scope": vat in in_scope, "is_member": vat in members,
            "eur": eur.get(vat, 0.0),
            # does the proposal actually change what the site shows today?
            "changes": bool(sp) and _accents(proposed.upper()) != _accents(sp[0].upper()),
        })
    # a venture no contract quotes is written out of its members' own display
    # names, which are decided in the pass above
    members: dict[str, list[str]] = {}
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='consortium_members'").fetchone():
        for r in conn.execute("SELECT venture_vat, member_vat FROM "
                              "consortium_members ORDER BY venture_vat, seq"):
            members.setdefault(r[0], []).append(r[1])
    by_vat = {r["vat"]: r for r in rows}
    for r in rows:
        if r["kind"] != "venture":
            continue
        # compose wherever the members are curated: their names are decided
        # and a composition reads the same way every time, where the papers'
        # own quotes run two members together («ΤΣΙΜΠΩΝΗ ΧΡΥΣΟΥΛΑ ΚΑΙ ΣΙΑ ΕΕ
        # ΓΕΩΡΓΙΟΥ Δ ΦΟΥΚΑΣ Ν Κ ΣΙΑ ΟΕ»)
        # inside a venture's name a member's patronymic is noise — it is on
        # that member's own page, one click away
        parts = [re.sub(r"\s+ΤΟΥ\s+\S+$", "", by_vat[m]["proposed"])
                 if by_vat[m]["kind"] == "person" else by_vat[m]["proposed"]
                 for m in members.get(r["vat"], []) if m in by_vat]
        if len(parts) < 2:
            continue
        r["proposed"] = mark_venture(" – ".join(parts))
        r["how"] = "composed from its curated members"
        r["changes"] = bool(r["spellings"]) and _accents(
            r["proposed"].upper()) != _accents(r["spellings"][0].upper())
    # two ventures of the same firms compose to the same name — 996550190 and
    # 996553688 are both ΚΑΡΝΟΜΟΥΡΑΚΗΣ with ΑΛΚΗ, for ΥΠΟΕΡΓΟ Β and ΥΠΟΕΡΓΟ Δ
    year = {r[0]: (r[1] or "")[:4] for r in conn.execute(
        "SELECT co.vat_number, MIN(c.contract_signed_date) FROM contractors co "
        "JOIN contracts c USING (reference_number) GROUP BY co.vat_number")}
    groups: dict[str, list[dict]] = {}
    for r in rows:
        if r["kind"] == "venture":
            groups.setdefault(r["proposed"], []).append(r)
    for name, group in groups.items():
        if len(group) < 2:
            continue
        years = {r["vat"]: year.get(r["vat"], "") for r in group}
        shared = set.intersection(*[
            {w for sp in r["spellings"] for w in _accents(sp.upper()).split()}
            for r in group]) if all(r["spellings"] for r in group) else set()
        for r in group:
            own = {w for sp in r["spellings"] for w in _accents(sp.upper()).split()}
            tail = [w for w in sorted(own - shared) if len(w) <= 12][:2]
            lot = ""
            for sp in r["spellings"]:
                m = re.search(r"(ΥΠΟΕΡΓΟ|ΤΜΗΜΑ|ΟΜΑΔΑ)\s*[:\-/]?\s*([Α-ΩA-Z0-9]{1,3})",
                              _accents(sp.upper()))
                if m:
                    lot = f"{m.group(1)} {m.group(2)}"
                    break
            if lot:                       # «ΥΠΟΕΡΓΟ Β» — the lot it was formed for
                mark = lot
            elif len(set(years.values())) == len(group) and years[r["vat"]]:
                mark = years[r["vat"]]
            elif tail:
                mark = " ".join(reversed(tail)) if len(tail) == 2 else tail[0]
            else:
                mark = r["vat"]
            r["proposed"] = f"{name} ({mark})"
            r["how"] += "; disambiguated from the other venture of the same firms"
            r["changes"] = bool(r["spellings"]) and _accents(
                r["proposed"].upper()) != _accents(r["spellings"][0].upper())
    rows.sort(key=lambda r: -(r["eur"] or 0))
    return {"rows": rows}


def curate(review: dict) -> int:
    existing = (json.loads(CURATED.read_text(encoding="utf-8"))
                if CURATED.exists() else {})
    overrides = existing.get("_overrides", {})
    out = {
        "_doc": ("ONE canonical display name per contractor ΑΦΜ (DATA_DECISIONS "
                 "2026-08-20). Rules: the registered name (ΓΕΜΗ, else VIES) "
                 "shortened to its distinctive head plus the legal form; a "
                 "person as ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ; a renamed company "
                 "under today's name everywhere. Registry spellings are never "
                 "rewritten — they stay searchable and visible as evidence. "
                 "`_overrides` is merged on re-run and wins."),
        "_overrides": overrides,
    }
    for r in review["rows"]:
        ov = overrides.get(r["vat"], {})
        entry = {"name": ov.get("name") or r["proposed"],
                 "basis": "user decision" if ov.get("name") else r["how"],
                 "kind": r["kind"], "registered": r["registered"] or None,
                 "spellings": r["spellings"]}
        if r.get("source"):
            entry["source"] = r["source"]          # the ΑΔΑΜ it was read from
        if ov.get("name_en"):
            entry["name_en"] = ov["name_en"]
        if ov.get("note"):
            entry["note"] = ov["note"]
        out[r["vat"]] = entry
    CURATED.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    return len(review["rows"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--curate", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    conn = sqlite3.connect(args.db)
    data = build(conn)
    conn.close()
    REVIEW.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    if args.curate:
        n = curate(data)
        logging.info("curated %d display names into %s", n, CURATED)
        return 0
    rows = data["rows"]
    from collections import Counter
    logging.info("%d entities · %d changed by the rules · kinds %s",
                 len(rows), sum(1 for r in rows if r["changes"]),
                 dict(Counter(r["kind"] for r in rows)))
    logging.info("review file: %s", REVIEW)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
