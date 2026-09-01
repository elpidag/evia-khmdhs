# -*- coding: utf-8 -*-
"""Build the English display text for every registered-office string the
entity pages print (DATA_DECISIONS 2026-08-26).

Three sources, one layer, keyed by the exact stored Greek string:
  * the ΔΑΣΕ co-operatives' village seats   (dase.sqlite)
  * the Anti-nero contractors' addresses    (contractor_locations.json)
  * the forest authorities' office addresses (forest_authorities table)

ISO-843 via ``khmdhs.geocode_loader._translit``; «ΑΓ» expands by the
following word's gender, ordinals take their English suffix, and the
address abbreviations the documents use (χλμ, Τ.Θ., Ε.Ο., Λεωφ.) are
rendered. MACHINE-PROPOSED — every value awaits the user's review; the
Greek string stays the stored value and the evidence.
"""
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from khmdhs.geocode_loader import _translit  # noqa: E402


def _clean(v: str | None) -> str | None:
    if not v:
        return None
    s = " ".join(str(v).replace(" None", "").split())
    return s if s and s.lower() != "none" else None


def collect() -> set[str]:
    vals: set[str] = set()

    # the ΔΑΣΕ co-op seats
    conn = sqlite3.connect(ROOT / "data/processed/dase.sqlite")
    conn.row_factory = sqlite3.Row
    for r in conn.execute("SELECT address, city FROM contractor_locations"):
        for v in (r["address"], r["city"]):
            if (s := _clean(v)):
                vals.add(s)
    conn.close()

    # the Anti-nero contractor seats
    raw = json.loads((ROOT / "khmdhs/data/contractor_locations.json")
                     .read_text(encoding="utf-8"))
    for r in (raw if isinstance(raw, list) else list(raw.values())):
        if isinstance(r, dict):
            for k in ("address", "city"):
                if (s := _clean(r.get(k))):
                    vals.add(s)

    # the forest authorities' offices — the seat municipality only where the
    # office block has no post town of its own (Περτουλίου, ΑΠΘ-run)
    conn = sqlite3.connect(ROOT / "data/processed/khmdhs.sqlite")
    conn.row_factory = sqlite3.Row
    for r in conn.execute("SELECT municipality_name, street, city "
                          "FROM forest_authorities"):
        for v in (r["street"], r["city"]):
            if (s := _clean(v)):
                vals.add(s)
        if not _clean(r["city"]) and (s := _clean(r["municipality_name"])):
            vals.add(s)
    conn.close()
    return vals


# keys are dot-stripped uppercase
SMALL = {"ΚΑΙ": "and", "ΧΙΛ": "km", "ΧΛΜ": "km", "ΤΘ": "PO Box",
         "ΤΚ": "", "ΔΔ": "", "ΟΔΟΣ": "",
         "ΛΕΩΦΟΡΟΣ": "Leoforos", "ΛΕΩΦ": "Leoforos", "ΛΕΩΦΟΡΟΥ": "Leoforou",
         "ΘΕΣΗ": ",",
         # the abbreviations the ΥΠΕΝ contact tables write
         "ΚΩΝ/ΝΟΥ": "Konstantinou", "ΑΡ": "no.",
         # what the building is, said rather than transliterated
         "ΔΙΟΙΚΗΤΗΡΙΟ": "Administration Building", "ΤΕΡΜΑ": "End of"}
# ΕΟ/ΝΕΟ/ΠΕΟ mean a national road ONLY where a «χλμ» has just been said —
# «Νέο Ψυχικό» and «Νέο Ηράκλειο» are adjectives, and read as «New National
# Road Psychiko» until the OSM cross-check caught them
ROADS = {"ΕΟ": "National Road", "ΝΕΟ": "New National Road",
         "ΠΕΟ": "Old National Road"}
# multi-word phrases, replaced before the words are read
PHRASES = {"ΕΘΝΙΚΗΣ ΟΔΟΥ": "National Road", "ΠΛ.": "Plateia ", "ΠΕΡΙΦΕΡΕΙΑΚΗ ΟΔΟΣ": "Ring Road",
           "ΔΑΣΙΚΟ ΚΤΙΡΙΟ": "Forestry Building", "ΔΑΣΙΚΟ ΦΥΤΩΡΙΟ": "Forest Nursery"}
DROP = ("ΕΝΤΟΣ ΟΙΚΙΣΜΟΥ", "ΕΝΤΟΣ ΣΧΕΔΙΟΥ")
# Verdicts no rule can reach. The first four are single-letter
# abbreviations whose expansion needs the toponym («Ν» is Νέα or Νέο, «Κ»
# is Κάτω), confirmed against OSM's own names; the rest are the familiar
# English forms the user already ruled on for the Π.Ε. layer
# (DATA_DECISIONS 2026-08-15) — a settlement of the same name must read
# the same way, or the site says «Rodos» on one page and «Rhodes» on the
# next.
OVERRIDES = {
    # the five single verdicts of the 2026-09-01 review (DATA_DECISIONS)
    "Οδός των 118, αρ. 37": "Odos ton 118, no. 37",
    "Περιοχή ΖΕΠ": "ZEP area",
    "αγροτεμάχια 567 & 584": "plots 567 & 584",
    "Μ. Αλεξάνδρου, Διοικητήριο": "Megalou Alexandrou, Administration Building",
    "Π.ΒΙΝΙΕΡΑΤΟΥ 5, ΠΛ.ΚΑΜΠΑΝΑΣ": "P. Vinieratou 5, Plateia Kampanas",
    "3 ΧΙΛ ΔΡΑΜΑΣ ΣΕΡΡΩΝ": "3rd km Dramas – Serron",
    "Ν ΜΑΓΝΗΣΙΑ": "Nea Magnisia",
    "Ν ΠΕΤΡΙΤΣΙ": "Neo Petritsi",
    "Κ ΝΕΥΡΟΚΟΠΙ": "Kato Nevrokopi",
    "Κ ΠΟΡΟΙΑ": "Kato Poroia",
    "ΗΡΑΚΛΕΙΟ": "Heraklion",
    "ΚΟΡΙΝΘΟΣ": "Corinth",
    "Κόρινθος": "Corinth",
    "Κέρκυρα": "Corfu",
    "ΠΕΙΡΑΙΑΣ": "Piraeus",
    "Πειραιάς": "Piraeus",
    "Ρόδος": "Rhodes",
}
# «107ο χλμ.» → «107th km» — but ONLY before the km: a street named after
# a date keeps the Greek form its sign carries («25ης Μαρτίου» → «25is
# Martiou», never «25th Martiou»)
ORD = re.compile(r"^(\d+)(ο|ος|ου|ης|η|ο\.)$", re.I)
KM = ("ΧΛΜ", "ΧΙΛ")
# a hyphen or a dot inside a token starts a new word — but a run after a
# DIGIT is that numeral's Greek suffix («25ης» → «25is»), not a new word
RUN = re.compile(r"(?<!\w)[^\W\d_]+", re.U)


def fold(s: str) -> str:
    """Uppercase WITHOUT accents — «Τέρμα».upper() is «ΤΈΡΜΑ», which
    matches no key (the trap CLAUDE.md records for every Greek matcher)."""
    return "".join(c for c in unicodedata.normalize("NFD", s.upper())
                   if not unicodedata.combining(c))


def ordinal(n: str) -> str:
    i = int(n)
    if 10 <= i % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(i % 10, "th")
    return f"{i}{suf}"


# ΕΛΟΤ 743: αυ/ευ/ηυ are av/ev/iv before a vowel or a voiced consonant
# (β γ δ ζ λ μ ν ρ) and af/ef/if before a voiceless one or at word end.
# `_translit` maps them blindly, so the display layer restores the rule.
_VOICELESS = re.compile(r"([aei])v(?=(?:th|ps|ch|[kxpstf])|)", re.I)


def _voicing(t: str) -> str:
    return _VOICELESS.sub(lambda m: m.group(1) + "f", t)


# Review rules of 2026-09-01 (DATA_DECISIONS), display layer only:
#   A. «γγ» is «ng» (ELOT 743's own rule, which _translit lacks): Syngrou,
#      Angelou, Mesolongi, Archangelos;
#   B. a word that STARTS with «Μπ» takes the familiar «B», and its inner
#      «μπ» follows (Bouboulinas, Bonou) — a word-internal «μπ» elsewhere
#      keeps «mp» (Kampanas, Lampraki).
def _familiar(t: str) -> str:
    t = t.replace("gg", "ng").replace("Gg", "Ng").replace("GG", "NG")
    if t[:2].lower() == "mp":
        t = ("B" if t[0].isupper() else "b") + t[2:].replace("mp", "b")
    return t


# C. a letter after a building number is a label, not a word: «13Α» → «13A»,
#    «118Β» → «118B», never «13a» / «118v»
SUFFIX = {"Α": "A", "Β": "B", "Γ": "G", "Δ": "D"}
NUM_SUFFIX = re.compile(r"^(\d+)([ΑΒΓΔ])$")


def _cap(t: str) -> str:
    """Capitalise every alphabetic run — «komotinis-alexandroupolis» is two
    place names, and so is «Pl.kampanas»."""
    return RUN.sub(lambda m: m.group(0)[:1].upper() + m.group(0)[1:], t)


def english(s: str) -> str:
    for d in DROP:
        s = s.replace(d, " ")
    up_all = fold(s)
    for gr, en in PHRASES.items():
        if gr in up_all:
            i = up_all.index(gr)
            s = s[:i] + en + s[i + len(gr):]
            up_all = fold(s)
    words = s.split()
    out: list[str] = []
    for i, w in enumerate(words):
        up = fold(w).replace(".", "")  # «Ε.Ο.» and «Ε.Ο» are one key
        if re.fullmatch(r"ΑΓ\.?", fold(w)) and i + 1 < len(words):
            nxt = fold(words[i + 1])
            out.append("Agion" if nxt.endswith("ΩΝ")
                       else "Agiou" if nxt.endswith("ΟΥ")
                       else "Agias" if nxt.endswith("ΑΣ")
                       else "Agioi" if nxt.endswith(("ΟΙ", "ΕΣ"))
                       else "Agia" if nxt.endswith(("Α", "Η")) else "Agios")
            continue
        if (m := ORD.fullmatch(w)):
            nxt = fold(words[i + 1]).replace(".", "") if i + 1 < len(words) else ""
            out.append(ordinal(m.group(1)) if nxt in KM
                       else _cap(_voicing(_translit(w))))
            continue
        nxt_up = fold(words[i + 1]).replace(".", "") if i + 1 < len(words) else ""
        prev_up = fold(words[i - 1]).replace(".", "") if i else ""
        if up in ROADS:
            # a road only where the km was just said, or where the writer
            # dotted it («Ε.Ο.») — otherwise it is «Νέο» the adjective
            if prev_up in KM or "." in w:
                out.append(ROADS[up])
            else:
                out.append(_cap(_familiar(_voicing(_translit(w)))))
            continue
        if up == "ΜΕΓ":
            out.append("Megalou" if nxt_up.endswith("ΟΥ")
                       else "Megali" if nxt_up.endswith(("Α", "Η"))
                       else "Meg.")
            continue
        # «Οδός» is a bare word to drop — except before an article, where it
        # is part of the street's own name (the one such case carries a
        # user verdict in OVERRIDES; this is the fallback for the next)
        if up == "ΟΔΟΣ" and nxt_up in ("ΤΩΝ", "ΤΗΣ", "ΤΟΥ"):
            out.append("Odos")
            continue
        if up in SMALL:
            if SMALL[up]:
                out.append(SMALL[up])
            continue
        if fold(w) == "Λ" and i + 1 < len(words):
            out.append("Leoforos")
            continue
        if (m := NUM_SUFFIX.fullmatch(fold(w))):
            out.append(m.group(1) + SUFFIX[m.group(2)])
            continue
        if w.isdigit():
            out.append(ordinal(w) if nxt_up in KM else w)
            continue
        out.append(_cap(_familiar(_voicing(_translit(w)))))
    # «ΘΕΣΗ» is punctuation, not a word: it hangs on the name before it
    joined = " ".join(out).strip()
    return " ".join(joined.replace(" ,", ",").split()).strip(" ,")


def main() -> None:
    vals = collect()
    data = {
        "_comment": (
            "English display text for the entity pages' registered-office "
            "toponyms and street addresses (DATA_DECISIONS 2026-08-26): the "
            "ΔΑΣΕ co-op seats, the Anti-nero contractor seats and the forest "
            "authorities' offices, keyed by the exact stored Greek string. "
            "ISO-843 transliteration (khmdhs.geocode_loader._translit), "
            "title-cased, «ΑΓ» expanded, ordinals and χλμ/Τ.Θ./Λεωφ. "
            "rendered; USER-REVIEWED 2026-09-01 — rules A–I and five single "
            "verdicts, DATA_DECISIONS. "
            "rendered. MACHINE-PROPOSED, awaiting the user's review; the "
            "Greek stays the stored value and the evidence. Rebuild: "
            "python scripts/build_place_names_en.py"
        ),
    }
    for v in sorted(vals):
        data[v] = OVERRIDES.get(v) or english(v)
    out = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    (ROOT / "khmdhs/data/place_names_en.json").write_text(out, encoding="utf-8")
    (ROOT / "atlas/src/lib/data/place_names_en.json").write_text(out, encoding="utf-8")
    print(f"{len(vals)} distinct places written to both copies")


if __name__ == "__main__":
    main()
