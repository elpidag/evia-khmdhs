"""Read the ΔΑΣΕ contracts' own texts for what the page needs: the work-type
CATEGORY, the FIRE CONTEXT, and the DEADLINE the document states.

DATA_DECISIONS 2026-08-23 (the ΔΑΣΕ contract page mirrors the Anti-nero
one). The rules are the user's:

* The category comes from the contract's OWN words — the signed PDF's
  title (the heading after the letterhead, the quoted title «με τίτλο:
  «…»» / «της υπηρεσίας «…»») and the sentence that describes the work
  («Είδος ανατιθέμενων εργασιών: …», «αναλαμβάνει την εκτέλεση …»,
  «ΑΝΑΘΕΤΕΙ … την …», «Αντικείμενο της σύμβασης …», «θα δεσμεύσει … τις
  παρακάτω ποσότητες καυσόξυλων»). Funding recitals, legal-basis recitals,
  boilerplate and CPV are never read. The registry title is no source: a
  scanned PDF is read by eye and carries that as its source.
* WHAT is done is one category; WHY is a separate attribute — «post-fire
  restoration» and «wildfire prevention» are umbrellas over different
  works and must not swallow them. A contract whose words state no
  purpose gets none; nothing is inferred from the season or the money.
* The deadline is DOCUMENT-STATED ONLY: a date («Προθεσμία εκτελέσεως
  μέχρι 31-12-2021», «λήγουσα ανυπερθέτως στις 31-12-2021», «ισχύει έως
  31/12/2022», «ορίζεται μέχρι τις 20 Οκτωβρίου 2021»), a duration («έχει
  διάρκεια ενός (1) μηνός», the Anti-nero «ορίζεται σε τρεις (3) μήνες»),
  or nothing. «Μέχρι εξαντλήσεως του ποσού» / «λήγει με την ολοκλήρωση των
  εργασιών» is an open end, recorded as such and drawn as no deadline. The
  registry's end date is never used for the bar.

Nothing here writes to the database: every function PROPOSES, the review
decides, and the verdicts live in curated JSON (the Anti-nero shape).
"""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field

from khmdhs.contract_durations import (DurationRead, fold, fold_map, loose,
                                       read as read_antinero_duration)

# ----------------------------------------------------------------- vocabulary

CATEGORIES: dict[str, dict[str, str]] = {
    "kafsoxyla": {
        "label": "καυσόξυλα ατομικών αναγκών",
        "label_en": "Firewood for local needs",
        "note": "δέσμευση καυσόξυλων για την κάλυψη ατομικών αναγκών (άρθρο 8 π.δ. 126/1986)",
    },
    "ylotomia": {
        "label": "υλοτομία δασικών προϊόντων",
        "label_en": "Timber harvesting",
        "note": "υλοτομία, μεταφορά, μετατόπιση δασικών προϊόντων· πρωτόκολλα εγκατάστασης",
    },
    "kalliergitikes": {
        "label": "καλλιεργητικές εργασίες",
        "label_en": "Silvicultural tending",
        "note": "καλλιεργητικές υλοτομίες, αραιώσεις, συντήρηση & βελτίωση δασών και συστάδων",
    },
    "katharismoi": {
        "label": "καθαρισμοί βλάστησης",
        "label_en": "Vegetation clearing",
        "note": "αποψιλώσεις, καθαρισμοί βλάστησης/υπορόφου, κοπή χόρτων, διαχείριση βλάστησης",
    },
    "antipyrikes_zones": {
        "label": "αντιπυρικές ζώνες",
        "label_en": "Firebreak zones",
        "note": "δημιουργία ή συντήρηση αντιπυρικών ζωνών / ζωνών πυρασφάλειας",
    },
    "dentra": {
        "label": "κοπή και κλάδεμα δέντρων",
        "label_en": "Tree felling & pruning",
        "note": "κοπή επικίνδυνων, ξερών ή καμένων δέντρων, κλαδέματα, αφαίρεση δέντρων",
    },
    "antidiavrotika": {
        "label": "αντιπλημμυρικά και αντιδιαβρωτικά έργα",
        "label_en": "Flood & erosion-control works",
        "note": "έργα αντιπλημμυρικής προστασίας, αντιδιαβρωτικά έργα, κορμοδέματα, κλαδοπλέγματα, φράγματα",
    },
    "anadasosi": {
        "label": "αναδάσωση, φυτεύσεις και σποροσυλλογή",
        "label_en": "Reforestation, planting & seed collection",
        "note": "αναδασώσεις, φυτεύσεις, δενδροφυτεύσεις, σποροσυλλογή, φυτώρια",
    },
    "promitheia": {
        "label": "προμήθεια ξυλείας και καυσόξυλων",
        "label_en": "Supply of timber & firewood",
        "note": "προμήθειες ξυλείας, καυσόξυλων, πασσάλων και ξύλινων προϊόντων",
    },
    "loipa": {
        "label": "λοιπές δασικές εργασίες",
        "label_en": "Other forestry services",
        "note": "δασικοί δρόμοι, αποχιονισμός, ζημιές από καιρικά φαινόμενα και ό,τι άλλο ονομάζεται",
    },
}

FIRE_CONTEXTS: dict[str, dict[str, str]] = {
    "prevention": {"label": "πρόληψη πυρκαγιών", "label_en": "wildfire prevention"},
    "post_fire": {"label": "αποκατάσταση μετά από πυρκαγιά", "label_en": "post-fire restoration"},
}

# The rules, in the order they are tested — the FIRST that fires is the
# proposal, every family that fires is listed, and a contract matching two
# families goes to review. Stems are folded (uppercase, no accents); the
# texts are folded with a 1:1 map so excerpts come from the original.
_RULES: tuple[tuple[str, str], ...] = (
    # the villages' firewood right — tested first, the word «υλοτομία» is
    # inside every one of these documents too
    ("kafsoxyla", r"ΔΕΣΜΕΥΣ\w*\s+(?:\S+\s+){0,8}?ΚΑΥΣΟ[ΞΥ]\w*|ΑΤΟΜΙΚ\w*\s+ΑΝΑΓΚ|ΚΑΥΣΟ[ΞΥ]\w*.{0,40}ΑΤΟΜΙΚ\w*\s+ΑΝΑΓΚ"),
    ("antidiavrotika", r"ΑΝΤΙΠΛΗΜ+ΥΡ|ΑΝΤΙΔΙΑΒΡΩΤ|ΚΟΡΜΟΔΕΜ|ΚΛΑΔΟΠΛΕΓΜ|ΚΟΡΜΟΦΡΑΓΜ|ΚΛΑΔΟΦΡΑΓΜ|ΣΑΝΙΔΟΤΟΙΧ|ΦΡΑΓΜΑΤ\w*\s+(ΣΥΓΚΡΑΤΗΣ|ΑΝΑΣΧΕΣ)"),
    ("antipyrikes_zones", r"ΑΝΤΙΠΥΡΙΚ\w*\s+(ΖΩΝ|ΛΩΡΙΔ)|ΖΩΝ\w*\s+(ΠΥΡΑΣΦΑΛ|ΠΥΡΟΠΡΟΣΤΑΣ)|ΠΕΡΙΜΕΤΡΙΚ\w*\s+ΑΝΤΙΠΥΡΙΚ"),
    ("promitheia", r"ΠΡΟΜΗΘΕΙ\w*.{0,30}(ΞΥΛΕΙ|ΚΑΥΣΟΞΥΛ|ΚΑΥΣΟΥΛ|ΞΥΛΙΝ|ΠΑΣΣΑΛ|ΠΕΛΛΕΤ|ΠΡΙΣΤ)|(ΞΥΛΕΙ|ΚΑΥΣΟΞΥΛ)\w*.{0,30}ΠΡΟΜΗΘΕΙ"),
    ("anadasosi", r"ΑΝΑΔΑΣ|ΦΥΤΕΥΣ|ΔΕΝΔΡΟΦΥΤ|ΣΠΟΡΟΣΥΛΛΟΓ|ΦΥΤΩΡ|ΣΠΟΡΩΝ\s+ΔΑΣ"),
    ("kalliergitikes", r"ΚΑΛΛΙΕΡΓ|ΑΡΑΙΩΣ|ΣΥΝΤΗΡΗΣ\w*\s*(ΚΑΙ|&|-|–)\s*ΒΕΛΤΙΩΣ\w*\s+(ΤΩΝ\s+|ΤΟΥ\s+|ΤΗΣ\s+)?(ΔΑΣ|ΣΥΣΤΑΔ|ΔΗΜΟΣΙ)|ΣΥΝΤΗΡΗΣΗΣ\s+(ΚΑΙ|&)\s+ΒΕΛΤΙΩΣΗΣ\b"),
    ("dentra", r"ΕΠΙΚΙΝΔΥΝ\w*\s+(ΔΕΝΔΡ|ΔΕΝΤΡ)|ΚΟΠ\w*[,\s]+(?:\S+\s+){0,4}?(ΔΕΝΔΡ|ΔΕΝΤΡ)|ΚΛΑΔΕ(Μ|ΥΣ)|ΑΦΑΙΡΕΣ\w*\s+(?:\S+\s+){0,2}?(ΔΕΝΔΡ|ΔΕΝΤΡ)|ΔΕΝΔΡΟΚΟΜ|ΑΠΟΚΛΑΔΩΣ|ΘΡΥΜΜΑΤΙΣ|ΥΛΟΤΟΜ\w*\s+(?:\S+\s+){0,2}?(ΔΕΝΔΡ|ΔΕΝΤΡ)\w*\s+(ΣΕ|ΣΤ|ΕΝΤΟΣ|ΓΙΑ|ΠΑΡΚ|ΑΥΛ|ΚΟΙΝΟΧΡ|ΚΟΙΜΗΤ)"),
    ("katharismoi", r"ΑΠΟΨΙΛ|ΚΑΘΑΡΙΣΜ\w*.{0,40}?(ΒΛΑΣΤ|ΧΟΡΤ|ΘΑΜΝ|ΠΑΡΟΔΙ|ΥΠΟΡΟΦ|ΑΥΤΟΦΥ)|ΚΟΠ\w*\s+(?:\S+\s+){0,4}?(ΒΛΑΣΤΗΣ|ΑΥΤΟΦΥ)|ΚΑΘΑΡΙΣΜ\w*\s+(ΤΗΣ\s+|ΤΩΝ\s+|ΑΠΟ\s+)?(ΒΛΑΣΤΗΣ|ΧΟΡΤ|ΘΑΜΝ|ΞΗΡ|ΔΑΣΙΚ|ΥΠΟΡΟΦ|ΑΓΡΙΟΧΟΡΤ|ΑΥΛΑΚ|ΦΕΡΤ|ΚΛΑΔΙ|ΠΑΡΟΔΙ|ΠΑΡΑΠΛΕΥΡ|ΔΗΜΟΤΙΚ|ΚΟΙΝΟΧΡΗΣΤ|ΠΕΡΙΟΧ|ΕΚΤΑΣ)|ΚΟΠ\w*\s+(ΤΩΝ\s+)?ΧΟΡΤ|ΧΟΡΤΟΚΟΠ|ΔΙΑΧΕΙΡΙΣ\w*\s+(ΤΗΣ\s+)?ΒΛΑΣΤΗΣ|ΑΠΟΜΑΚΡΥΝΣ\w*\s+(ΜΕΡΟΥΣ\s+ΤΟΥ\s+|ΤΗΣ\s+|ΤΟΥ\s+)?(ΒΛΑΣΤ|ΥΠΟΡΟΦ|ΧΟΡΤ)|ΕΚΚΑΘΑΡΙΣ\w*\s+(ΑΠΟ\s+)?ΑΓΡΙΟΧΟΡΤ|ΚΑΘΑΡΙΣΜ\w*\s+(ΚΑΙ\s+)?ΑΠΟΨΙΛ"),
    ("ylotomia", r"ΥΛΟΤΟΜ|ΞΥΛΕΥΣ|ΜΕΤΑΤΟΠΙΣ|ΑΠΟΛΗΨ|ΔΑΣΙΚ\w*\s+ΠΡΟ[ΙΪ]ΟΝΤ|ΠΡΩΤΟΚΟΛΛ\w*\s+ΕΓΚΑΤΑΣΤΑΣ|ΕΚΜΕΤΑΛΛΕΥΣ\w*\s+(ΤΟΥ\s+|ΤΗΣ\s+|ΤΩΝ\s+)?(ΔΑΣ|ΣΥΣΤΑΔ)|ΣΥΓΚΟΜΙΔ|ΣΤΟΙΒΑΞ|ΣΥΣΤΑΔ\w*\s+\d"),
    ("loipa", r"ΔΑΣΙΚ\w*\s+(ΟΔ|ΔΡΟΜ)|ΟΔΟΠΟΙ|ΒΑΤΟΤΗΤ|ΑΠΟΧΙΟΝ|ΕΚΧΙΟΝ|ΑΠΟΚΑΤΑΣΤΑΣ\w*\s+(ΤΩΝ\s+)?ΒΛΑΒ|ΚΑΙΡΙΚ\w*\s+ΦΑΙΝΟΜΕΝ|ΡΗΤΙΝ|ΠΕΡΙΦΡΑΞ|ΣΗΜΑΝΣ|ΜΟΝΟΠΑΤ"),
)
_RULES_RX = tuple((k, re.compile(p)) for k, p in _RULES)

_CONTEXT_RULES: tuple[tuple[str, str], ...] = (
    ("prevention", r"ΑΝΤΙΠΥΡΙΚ\w*\s+(ΣΚΟΠ|ΠΡΟΣΤΑΣ|ΖΩΝ|ΛΩΡΙΔ)|ΓΙΑ\s+ΑΝΤΙΠΥΡΙΚ|ΠΥΡΑΣΦΑΛ|ΠΥΡΟΠΡΟΣΤΑΣ|ΠΡΟΛΗΨ\w*\s+(ΤΩΝ\s+|ΔΑΣΙΚΩΝ\s+|ΤΩΝ\s+ΔΑΣΙΚΩΝ\s+)?ΠΥΡΚΑ[ΓΪ]|ΠΥΡΚΑΓ\w*.{0,25}ΠΡΟΛΗΨ|ΜΕΙΩΣ\w*\s+(ΤΟΥ\s+)?ΚΙΝΔΥΝΟΥ\s+(ΠΥΡΚΑΓ|ΕΚΔΗΛΩΣ)|ΑΝΤΙΠΥΡΙΚ\w*\s+ΠΕΡΙΟΔ"),
    ("post_fire", r"ΚΑΜ+[ΕΖ]Ν\w*|ΠΥΡΟΠΛΗΚΤ|ΠΛΗΓΕΙΣ\w*\s+ΑΠΟ\s+(ΤΙΣ\s+|ΤΗΝ\s+)?ΠΥΡΚΑ[ΓΪ]|ΑΠΟΚΑΤΑΣΤΑΣ\w*.{0,60}ΠΥΡΚΑ[ΓΪ]|ΜΕΤΑ\s+(ΤΗΝ\s+|ΤΙΣ\s+)?(ΚΑΤΑΣΤΡΟΦΙΚ\w*\s+)?ΠΥΡΚΑ[ΓΪ]|ΠΥΡΚΑ[ΓΪ]\w*.{0,40}ΑΠΟΚΑΤΑΣΤ|ΑΠΟΚΑΤΑΣΤΑΣ\w*\s+(ΤΟΥ\s+)?ΦΥΣΙΚΟΥ\s+ΠΕΡΙΒΑΛΛΟΝΤ"),
)
_CONTEXT_RX = tuple((k, re.compile(p)) for k, p in _CONTEXT_RULES)

# ------------------------------------------------- the text layer's repairs

# Three things the ΔΑΣΕ PDFs do to their own text layer, none of which the
# eye sees on the page:
#  * the drop-in «∆» (U+2206, the increment sign) and Latin capitals for
#    Greek ones inside Greek words — homoglyphs, mapped back;
#  * the «΢»-font family (429 of 2,164 texts): the PDF's ToUnicode maps
#    Σ→«΢» (U+03A2, the unused capital final sigma), Τ→«Σ», Υ→«Τ» — a clean
#    3-cycle in capitals — and a LOSSY lowercase (σ↔ς swapped, η→θ, έ→ζ,
#    ώ→ϊ, ύ→φ, and both θ and κ shown as κ, both ή and ι as ι). The cycle
#    and the one-to-one lowercase pairs are undone; the lossy pairs are
#    repaired only inside the words the readers need («προθεσμία»,
#    «καθαρισμ», «αναθέτει», «λήγει», «ολοκλήρωση»);
#  * other substitution-cipher fonts (the Φουρνά/Σπερχειάδα/Ξάνθη
#    families: Δ→«Γ», Ε→«Δ», Η→«Ζ», Ω→«Χ»/«Ψ» …) — lossy and several; such
#    a text is flagged `unreadable_font` and read by eye, like a scan.
_HOMOGLYPH = str.maketrans({"∆": "Δ", "A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η",
                            "I": "Ι", "K": "Κ", "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ",
                            "T": "Τ", "Y": "Υ", "X": "Χ"})
_GREEK_TOKEN = re.compile(r"[A-Za-z∆Α-Ωα-ωΆ-ώΐΰ]+")
_SIGMA_UPPER = str.maketrans({"΢": "Σ", "Σ": "Τ", "Τ": "Υ"})
# σ↔ς, θ→η and ϊ→ώ are one-to-one in this font; φ (real φ OR real ύ) and ζ
# (real ζ OR real έ) are not, so those are repaired by word only
_SIGMA_LOWER = str.maketrans({"ς": "σ", "σ": "ς", "θ": "η", "ϊ": "ώ"})
_SIGMA_WORDS = (
    (re.compile(r"προκεσμ"), "προθεσμ"), (re.compile(r"Προκεσμ"), "Προθεσμ"),
    (re.compile(r"κακαρισμ"), "καθαρισμ"), (re.compile(r"Κακαρισμ"), "Καθαρισμ"),
    (re.compile(r"ανακετ"), "αναθετ"), (re.compile(r"ανατικεμ"), "ανατιθεμ"),
    (re.compile(r"\bλιγει"), "λήγει"), (re.compile(r"ολοκλιρωσ"), "ολοκλήρωσ"),
    (re.compile(r"μζχρι"), "μέχρι"), (re.compile(r"ςιμερα"), "σήμερα"),
    (re.compile(r"κακ(ώ|ω)σ"), "καθώς"), (re.compile(r"προσαφξ"), "προσαύξ"),
    (re.compile(r"\b([ζΖ])(τους|χοντ|ργ|κτασ|ως|να\b|κδοσ|γκρισ|λεγχ|ναρξ|δρα\b|τος|ξι\b)"),
     lambda m: ("έ" if m.group(1) == "ζ" else "Έ") + m.group(2)),
    (re.compile(r"αρικ(\.|μ)"), r"αριθ\1"),
)
# one more ΢-font variant writes capital Η as Θ («ΣΥΜΦΩΝΘΤΙΚΟ», «ΣΥΜΒΑΣΘΣ»);
# only impossible Greek sequences are mapped, never a bare Θ
_THETA_WORDS = (
    (re.compile(r"ΣΥΜΦΩΝΘΤΙΚ"), "ΣΥΜΦΩΝΗΤΙΚ"), (re.compile(r"ΣΥΜΒΑΣΘ"), "ΣΥΜΒΑΣΗ"),
    (re.compile(r"ΕΛΛΘΝΙΚ"), "ΕΛΛΗΝΙΚ"), (re.compile(r"ΔΘΜΟΚΡΑΤ"), "ΔΗΜΟΚΡΑΤ"),
    (re.compile(r"ΣΥΝΤΘΡΘΣ"), "ΣΥΝΤΗΡΗΣ"), (re.compile(r"ΕΓΚΑΤΑΣΤΑΣΘ"), "ΕΓΚΑΤΑΣΤΑΣΗ"),
    (re.compile(r"ΑΝΤΙΠΛΘΜΜΥΡ"), "ΑΝΤΙΠΛΗΜΜΥΡ"), (re.compile(r"ΚΑΤΑΣΚΕΥΘ"), "ΚΑΤΑΣΚΕΥΗ"),
    # and the Φουρνά font's Ω→Ψ, Ψ→Χ in the words the readers need («ΨΝ» ends
    # no Greek word, so that pair is safe everywhere)
    (re.compile(r"ΨΝ"), "ΩΝ"), (re.compile(r"ΣΥΜΦΨΝ"), "ΣΥΜΦΩΝ"), (re.compile(r"ΚΑΛΥΧΗ"), "ΚΑΛΥΨΗ"),
    (re.compile(r"ΚΑΥΣΟΞΥΛΨ"), "ΚΑΥΣΟΞΥΛΩ"), (re.compile(r"ΠΡΨΤΟΚΟΛΛ"), "ΠΡΩΤΟΚΟΛΛ"),
)
# a readable text names the ordinary things a Greek contract names; a
# substitution-cipher text names none of them
_COMMON = ("ΕΛΛΗΝΙΚΗ", "ΔΗΜΟΚΡΑΤΙΑ", "ΣΗΜΕΡΑ", "ΥΠΟΓΕΓΡΑΜΜΕΝ", "ΣΥΜΒΑΛΛΟΜΕΝ", "ΑΝΑΔΟΧ",
           "ΔΑΣΙΚ", "ΣΥΝΕΤΑΙΡΙΣΜ", "ΥΠΟΨΗ", "ΔΙΑΤΑΞΕΙΣ", "ΑΡΘΡΟ", "ΠΡΟΕΔΡ", "ΕΚΠΡΟΣΩΠ",
           "ΣΥΜΦΩΝΗ", "ΣΥΜΒΑΣ", "ΠΡΩΤΟΚΟΛΛΟ", "ΕΡΓΑΣΙ", "ΔΑΣΑΡΧΕΙ", "ΔΙΕΥΘΥΝΣΗ", "ΔΗΜΟΣ")


def _fix_homoglyphs(text: str) -> str:
    def fix(m: re.Match) -> str:
        tok = m.group(0)
        if re.search(r"[Α-Ωα-ωΆ-ώ∆]", tok) and re.search(r"[A-Za-z∆]", tok):
            return tok.translate(_HOMOGLYPH)
        return tok
    return _GREEK_TOKEN.sub(fix, text)


_NONFINAL_SIGMA = re.compile(r"ς(?=[Α-Ωα-ωΆ-ώ])")


def repair(text: str | None) -> tuple[str, list[str]]:
    """The text as the readers should see it, and what was done to it.

    The ΢-font decode is applied LINE BY LINE, only where the line shows the
    font's signature: «΢» for the capital cycle, a non-final «ς» inside a
    word for the lowercase pairs. The same PDF mixes fonts — a ΢-font
    letterhead above a clean-font heading — and a global decode turned
    «ΣΥΜΦΩΝΗΤΙΚΟ» into «ΤΥΜΦΩΝΗΥΙΚΟ».
    """
    if not text:
        return "", []
    notes: list[str] = []
    out = _fix_homoglyphs(text)
    # a cipher font first: its table is learnt from the ORIGINAL layer (the
    # ΢-cycle below would be applied line by line and break the bijection)
    if text_state(out) == "unreadable_font":
        dec = decode_cipher(out)
        if dec:
            out = dec[0]
            notes.append("cipher-font capitals decoded from the document's own phrases ("
                         + ", ".join(f"{a}→{b}" for a, b in sorted(dec[1].items())) + "); lowercase left as is")
            return out, notes
    if out[:8000].count("΢") >= 3 or len(_NONFINAL_SIGMA.findall(out[:8000])) >= 6:
        fixed_lines = []
        touched = 0
        for ln in out.splitlines():
            f = ln
            if "΢" in f:
                f = f.translate(_SIGMA_UPPER)
            if _NONFINAL_SIGMA.search(f):
                f = f.translate(_SIGMA_LOWER)
                for rx, rep in _SIGMA_WORDS:
                    f = rx.sub(rep, f)
            touched += f != ln
            fixed_lines.append(f)
        if touched:
            out = "\n".join(fixed_lines)
            notes.append("΢-font text layer repaired (Σ/Τ/Υ cycle, lowercase pairs)")
    if re.search(r"ΣΥΜΦΩΝΘΤΙΚ|ΣΥΜΒΑΣΘ|ΕΛΛΘΝΙΚ|ΔΘΜΟΚΡΑΤ|ΣΥΜΦΨΝ|ΨΝ", out[:8000]):
        for rx, r in _THETA_WORDS:
            out = rx.sub(r, out)
        notes.append("capital Θ-for-Η font repaired in the named words")
    return out, notes


# A substitution-cipher font maps each glyph to a WRONG letter, one-to-one
# within the font, the same way throughout the document (Φουρνά: Ω→«Ψ»,
# Ψ→«Χ»; Σπερχειάδα/Ξάνθη: Δ→«Γ», Ε→«Δ», Η→«Ζ», Ι→«Η», Σ→«΢», Τ→«Σ», Υ→«Τ»,
# Ψ→«Φ», Ω→«Χ»…). The CAPITALS table is learnt from the document itself:
# phrases every such document carries («ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ», «ΣΥΜΦΩΝΗΤΙΚΟ»,
# «ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ», «ΑΤΟΜΙΚΩΝ ΑΝΑΓΚΩΝ», «ΔΑΣΑΡΧΕΙΟ», «ΥΠΟΥΡΓΕΙΟ
# ΠΕΡΙΒΑΛΛΟΝΤΟΣ» …) are found by their letter PATTERN (a cryptogram's
# shape), the letter pairs they imply are voted, a consistent table wins
# and is applied to the capitals only; the decode is accepted only when the
# decoded text then reads like a contract (the common-word score). The
# lowercase body stays as it was — a different table, and lossy — so such a
# document's category comes from its capitals and its deadline is read by
# eye. What the eye sees on the page is the decoded text, not the layer.
_CIPHER_TARGETS = (
    "ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ", "ΣΥΜΦΩΝΗΤΙΚΟ", "ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ", "ΑΤΟΜΙΚΩΝ ΑΝΑΓΚΩΝ",
    "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ", "ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ", "ΔΑΣΑΡΧΕΙΟ", "ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ",
    "ΠΡΩΤΟΚΟΛΛΟ ΕΓΚΑΤΑΣΤΑΣΗΣ", "ΑΝΑΡΤΗΤΕΟ ΣΤΟ ΔΙΑΔΙΚΤΥΟ", "ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ", "ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ",
    "ΑΓΡΟΤΙΚΩΝ ΥΠΟΘΕΣΕΩΝ", "ΕΠΙΘΕΩΡΗΣΗ ΕΦΑΡΜΟΓΗΣ ΔΑΣΙΚΗΣ ΠΟΛΙΤΙΚΗΣ", "ΣΥΜΒΑΣΗ", "ΑΡΙΘ",
    "ΚΑΛΥΨΗ", "ΥΛΟΤΟΜΙΚΩΝ ΕΡΓΑΣΙΩΝ", "ΣΥΣΤΑΔΑ", "ΔΗΜΟΣΙΟΥ ΔΑΣΟΥΣ",
)
_CAPS = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ΢"


def _shape(word: str) -> tuple[int, ...]:
    seen: dict[str, int] = {}
    return tuple(seen.setdefault(ch, len(seen)) for ch in word)


def learn_cipher(text: str) -> dict[str, str] | None:
    """The capitals table a cipher-font document implies, or None."""
    head = text[:9000]
    # the document's capital words, in order, accents stripped
    plain = "".join(c for c in unicodedata.normalize("NFD", head) if not unicodedata.combining(c))
    toks = re.findall(r"[Α-Ω΢]{2,}", plain)
    votes: dict[tuple[str, str], int] = {}
    for target in _CIPHER_TARGETS:
        twords = target.split()
        n = len(twords)
        tshapes = [_shape(w) for w in twords]
        for i in range(len(toks) - n + 1):
            window = toks[i:i + n]
            if any(len(window[j]) != len(twords[j]) or _shape(window[j]) != tshapes[j] for j in range(n)):
                continue
            # the pairs this window implies must be consistent within it
            pairs: dict[str, str] = {}
            ok = True
            for w, tw in zip(window, twords):
                for a, b in zip(w, tw):
                    if pairs.setdefault(a, b) != b:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            for a, b in pairs.items():
                votes[(a, b)] = votes.get((a, b), 0) + 1
    if not votes:
        return None
    # each document letter → the target it voted for most; a letter whose
    # votes disagree badly is left unmapped
    table: dict[str, str] = {}
    by_src: dict[str, dict[str, int]] = {}
    for (a, b), n in votes.items():
        by_src.setdefault(a, {})[b] = by_src.get(a, {}).get(b, 0) + n
    for a, opts in by_src.items():
        b, n = max(opts.items(), key=lambda kv: kv[1])
        if n >= 2 and n / sum(opts.values()) >= 0.75 and a != b:
            table[a] = b
    # identity letters are real only if they never map elsewhere; a table
    # that moves fewer than three letters is noise
    return table if len(table) >= 3 else None


def decode_cipher(text: str) -> tuple[str, dict[str, str]] | None:
    """Apply the learnt capitals table; accept only if the result reads."""
    table = learn_cipher(text)
    if not table:
        return None
    tr = str.maketrans(table)
    out = text.translate(tr)
    up = fold(out[:8000])
    if sum(1 for w in _COMMON if w in up) < 6:
        return None
    return out, table


def text_state(text: str | None) -> str:
    """'ok' | 'scan' | 'unreadable_font' — for the repaired text."""
    if not text or len(text.strip()) < 1500:
        return "scan"
    g = len(re.findall(r"[Α-Ωα-ωάέήίόύώϊϋΐΰ]", text))
    a = len(re.findall(r"[A-Za-z]", text))
    if g / (g + a + 1) < 0.5:
        return "scan"
    up = fold(text[:8000])
    if sum(1 for w in _COMMON if w in up) < 4:
        return "unreadable_font"
    return "ok"


# ------------------------------------------------------------ the title read

# the document's own name, as a heading line (letter-spaced headings are
# squashed before testing: «Σ Υ Μ Β Α Σ Η» → ΣΥΜΒΑΣΗ)
_HEAD_START = re.compile(
    r"^(ΙΔΙΩΤΙΚΟ\s+ΣΥΜΦΩΝΗΤΙΚΟ|ΔΗΜΟΣΙΑ\s+ΣΥΜΒΑΣΗ|ΣΥΜΦΩΝΗΤΙΚΟ|ΣΥΜΒΑΣΗ|ΣΥΜΦΩΝΙΑ|ΣΥΜΦΩΝ[-–]?\s*ΠΡΩΤ|ΠΡΩΤΟΚΟΛΛΟ\s+ΕΓΚΑΤΑΣΤΑΣ)"
    r"(?!\w*\s+(ΑΥΤΗ|ΑΥΤΟ|ΠΟΥ|ΤΟΥ\s+ΑΝΑΔΟΧΟΥ|ΜΕ\s+ΑΔΑΜ))")
_HEAD_STOP = re.compile(
    r"^(ΣΤ[ΗΟΑ][ΝΣ]?\s|ΣΗΜΕΡΑ|ΣΥΜΒΑΤΙΚ\w*\s+ΠΟΣ|ΠΟΣΟΥ\s|ΠΟΣΟ\s|ΑΞΙΑΣ|ΑΡΙΘ|ΑΡ\.|Α\.Π\.|ΕΛΛΗΝΙΚΗ\s+ΔΗΜΟΚΡΑΤΙΑ|ΑΝΑΡΤΗΤ|ΑΔΑ[:\s]|\d{2}SYMV|ΟΙ\s+ΠΑΡΑΚΑΤΩ|ΟΙ\s+ΚΑΤΩΘΙ|ΜΕΤΑΞΥ|ΣΥΜΦΩΝΗΣΑΝ|ΤΑ\s+ΑΚΟΛΟΥΘΑ|ΣΕΛΙΔΑ\s"
    r"|ΣΥΜΦΩΝΑ\s+ΜΕ|[ΕΖ]ΧΟΝΤΑΣ|ΑΦΟΥ\s+(ΕΛΑΒ|ΛΑΒ)|ΤΗΝ\s+ΜΕ\s+ΑΡΙΘ|ΤΟ\s+ΜΕ\s+ΑΡΙΘ|\d+[.)]\s+Τ(ΙΣ|ΗΝ|Ο|ΟΝ|Α)\s|[Α-Ω][.)]\s+Τ(ΙΣ|ΗΝ|Ο|ΟΝ|Α)\s)")
# the heading line itself may run on into the first recital
_HEAD_CUT = re.compile(r"\s(ΣΥΜΦΩΝΑ\s+ΜΕ\s*:|[ΕΖ]ΧΟΝΤΑΣ\s+ΥΠΟΨΗ|ΣΗΜΕΡΑ\b|ΑΦΟΥ\s+ΕΛΑΒ|ΟΙ\s+(ΠΑΡΑΚΑΤΩ|ΚΑΤΩΘΙ|ΥΠΟΓΕΓΡΑΜΜΕΝΟΙ))")
_LETTER_SPACED = re.compile(r"(?:[Α-ΩA-Z]\s){3,}[Α-ΩA-Z]")
_HEAD_FLAT = re.compile(
    r"(?:ΙΔΙΩΤΙΚΟ\s+ΣΥΜΦΩΝΗΤΙΚΟ|ΔΗΜΟΣΙΑ\s+ΣΥΜΒΑΣΗ|ΣΥΜΦΩΝΗΤΙΚΟ|ΣΥΜΒΑΣΗ)\b(?!\s+(?:ΑΥΤΗ|ΑΥΤΟ|ΠΟΥ|ΜΕ\s+ΑΔΑΜ|ΜΕ\s+ΑΡ))"
    r"[^.«»]{0,40}?(?:\s[^.]{3,260}?)?(?=\s(?:ΣΗΜΕΡΑ|ΣΤ[ΗΟΑ][ΝΣ]?\s|ΣΥΜΒΑΤΙΚ|ΠΟΣΟΥ|ΟΙ\s+ΠΑΡΑΚΑΤΩ|ΟΙ\s+ΚΑΤΩΘΙ|ΣΥΜΦΩΝΗΣΑΝ|ΜΕΤΑΞΥ|ΕΧΟΝΤΑΣ|ΣΥΜΦΩΝΑ\s+ΜΕ|\d{2}SYMV)|\.)")

# a quoted title: «με τίτλο: «…»», «της υπηρεσίας «…»», «για την «…»» —
# NOT one standing inside a funding or decision recital («ένταξη και
# χρηματοδότηση του έργου «…»», «απόφαση … «…»»)
_QUOTED = re.compile(
    r"(ΜΕ\s+ΤΙΤΛΟ|ΜΕ\s+ΘΕΜΑ|ΤΗΣ\s+ΥΠΗΡΕΣΙΑΣ|ΤΗΣ\s+ΕΡΓΑΣΙΑΣ|ΤΩΝ\s+ΕΡΓΑΣΙΩΝ|ΤΟΥ\s+ΕΡΓΟΥ|ΤΗΣ\s+ΠΡΟΜΗΘΕΙΑΣ|ΤΗΣ\s+ΣΥΜΒΑΣΗΣ|ΓΙΑ\s+ΤΗΝ|ΓΙΑ\s+ΤΟ|ΓΙΑ\s+ΤΙΣ|ΕΚΤΕΛΕΣΗ\w*|ΑΝΑΘΕΣΗ\w*|ΥΠΗΡΕΣΙ\w*|ΕΡΓΑΣΙ\w*)"
    r"\s*:?\s*[«\"“‘']\s*([^»\"”’']{10,320})[»\"”’']")
_QUOTED_BAD_HEAD = re.compile(r"(ΧΡΗΜΑΤΟΔΟΤ|ΕΝΤΑΞΗ|ΠΙΣΤΩΣ|ΑΠΟΦΑΣ|ΕΓΚΡΙΣ|ΜΕΛΕΤΗ\s+ΜΕ|ΠΡΟΓΡΑΜΜΑ|ΕΓΚΥΚΛΙ|ΦΕΚ|ΔΙΑΤΑΞ|ΝΟΜΟ|ΑΡΘΡ|ΑΔΑ\s*:|ΑΡΙΘ|ΥΠ[’'`]?\s*ΑΡ|ΠΡΩΤ\.|ΟΡΙΣΜ|ΣΥΓΚΡΟΤΗΣ|ΑΝΑΛΗΨ|ΔΕΣΜΕΥΣ\w*\s+ΠΙΣΤ)")

# the sentence that says what is done
_WORK = re.compile(
    r"(ΕΙΔΟΣ\s+ΑΝΑ(?:ΤΙΘΕ|ΘΕΤΟΥ)ΜΕΝΩΝ\s+ΕΡΓΑΣΙΩΝ\s*:?\s*.{5,220}?)(?=\s\d\s?\)|\.\s+[Α-Ω0-9]|$)"
    r"|(ΑΝΑΛΑΜΒΑΝ\w*\s+(?:ΤΗΝ|ΤΟ|ΤΙΣ|ΝΑ)\s.{5,260}?)(?=\.\s+[Α-Ω]|$)"
    r"|(ΑΝΑΘΕΤΕΙ\b.{0,90}?(?:ΤΗΝ|ΤΟ|ΤΙΣ|ΤΑ)\s.{5,220}?)(?=[,:.]\s|$)"
    r"|(ΑΝΤΙΚΕΙΜΕΝΟ\s+(?:ΤΗΣ\s+ΠΑΡΟΥΣΑΣ\s+|ΤΗΣ\s+ΣΥΜΒΑΣΗΣ\s+|ΣΥΜΒΑΣΗΣ\s+)?(?:ΕΙΝΑΙ|ΑΠΟΤΕΛΕΙ|:)\s.{5,260}?)(?=\.\s+[Α-Ω]|$)"
    r"|(ΘΑ\s+ΔΕΣΜΕΥΣΕΙ\b.{0,260}?ΚΑΥΣΟ[ΞΥ]\w*)"
    r"|(ΟΙ\s+ΕΡΓΑΣΙΕΣ\s+ΣΥΝΙΣΤΑΝΤΑΙ\s+ΣΤ.{5,260}?)(?=\.\s+[Α-Ω]|$)"
    r"|(ΑΦΟΡΑ\s+(?:ΣΤΗΝ\s+|ΤΗΝ\s+|ΣΕ\s+|ΣΤΙΣ\s+|ΤΙΣ\s+|ΤΟ\s+|ΣΤΟ\s+)?.{5,220}?)(?=\.\s+[Α-Ω]|$)"
)
_WORK_BAD_HEAD = re.compile(r"(ΧΡΗΜΑΤΟΔΟΤ|ΕΝΤΑΞΗ|ΠΙΣΤΩΣ|ΑΠΟΦΑΣ\w*\s+(ΠΕΡΙ|ΤΟΥ|ΤΗΣ)|ΠΟΙΝΙΚ|ΕΓΓΥΗ)")
# the same anchors, a fixed window, when no sentence end is in sight
_WORK_LOOSE = re.compile(
    r"(ΕΙΔΟΣ\s+ΑΝΑ(?:ΤΙΘΕ|ΘΕΤΟΥ)ΜΕΝΩΝ\s+ΕΡΓΑΣΙΩΝ\s*:?\s*.{5,160})"
    r"|(ΑΝΑΛΑΜΒΑΝ\w*\s+(?:ΤΗΝ|ΤΟ|ΤΙΣ|ΝΑ)\s.{5,200})"
    r"|(ΑΝΑΘΕΤΕΙ\b.{0,90}?(?:ΤΗΝ|ΤΟ|ΤΙΣ|ΤΑ)\s.{5,200})"
    r"|(ΑΝΤΙΚΕΙΜΕΝΟ\s+(?:ΤΗΣ\s+ΠΑΡΟΥΣΑΣ\s+|ΤΗΣ\s+ΣΥΜΒΑΣΗΣ\s+|ΣΥΜΒΑΣΗΣ\s+)?(?:ΕΙΝΑΙ|ΑΠΟΤΕΛΕΙ|:)\s.{5,200})"
    r"|(ΟΙ\s+ΕΡΓΑΣΙΕΣ\s+ΣΥΝΙΣΤΑΝΤΑΙ\s+ΣΤ.{5,200})"
    r"|(ΑΦΟΡΑ\s+(?:ΣΤΗΝ\s+|ΤΗΝ\s+|ΣΕ\s+|ΣΤΙΣ\s+|ΤΙΣ\s+|ΤΟ\s+|ΣΤΟ\s+)?.{5,160})"
)


_SPACED_RUN = re.compile(r"(?<![Α-ΩA-Za-zα-ω])(?:[Α-ΩA-Z] ){2,}[Α-ΩA-Z](?![Α-ΩA-Za-zα-ω])")


def _squash(line: str) -> str:
    """«Σ Υ Μ Β Α Σ Η   Ε Κ Τ Ε Λ Ε Σ Η Σ» → «ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ» — only the
    letter-spaced runs are closed up; the words around them keep their
    spaces («ΣΥΜΦΩΝΗΤΙΚΟ ευρώ 6.696,00» stayed three words)."""
    if not _LETTER_SPACED.search(line):
        return line
    # a run of single capitals is one word; two runs split by a double
    # space are two words
    parts = re.split(r"\s{2,}", line)
    out = []
    for part in parts:
        out.append(_SPACED_RUN.sub(lambda m: m.group(0).replace(" ", ""), part))
    return " ".join(p for p in out if p)


def is_scan(text: str | None) -> bool:
    """A PDF whose text layer is only the registry stamp, or a font soup."""
    return text_state(repair(text)[0]) != "ok"


# the contract's own statement of NEED — the last «έχοντας υπόψη» item that
# states why the works are awarded («Την ανάγκη άμεσης εκτέλεσης έργων
# αντιπλημμυρικής προστασίας στις καμένες περιοχές του Δασαρχείου
# Ιστιαίας …»): the contract's own words, read for the FIRE CONTEXT only,
# never for the category. A need clause that merely cites a decision or a
# fund is not one (its head is tested like the quoted title's).
_NEED = re.compile(
    r"(?:ΤΗΝ|ΤΗ)\s+(?:ΕΠΙΤΑΚΤΙΚΗ\s+|ΕΠΕΙΓΟΥΣΑ\s+|ΑΜΕΣΗ\s+)?" + loose("ΑΝΑΓΚΗ") + r"\s*"
    r"(?=.{0,60}?(?:[ΕΖ]ΚΤ[ΕΖ]Λ[ΕΖ]Σ|ΥΛΟΠΟΙ|ΚΑΤΑΣΚ|ΑΠΟΚΑΤΑΣΤ|ΑΝΑΘ[ΕΖ]Σ|ΠΡΟΣΤΑΣ|ΔΙ[ΕΖ]Ν[ΕΖ]ΡΓ|ΚΑΘΑΡ|ΑΠΟΜΑΚΡ|ΠΑΡΟΧ|ΛΗΨ|ΑΝΤΙΜ[ΕΖ]ΤΩΠ|ΠΡΟΛΗΨ|[ΕΖ]ΡΓ))"
    r"(?:.{5,600}?(?=\.\s|ΑΝΑΘ[ΕΖ]Τ[ΕΖ]Ι|$)|.{5,300})")


@dataclass
class TitleRead:
    heading: str = ""                  # the document's own name, verbatim
    quoted: str = ""                   # «με τίτλο: «…»», verbatim
    work: str = ""                     # the sentence describing the work
    need: str = ""                     # the contract's own statement of need
    heading_line: int | None = None


def read_title(text: str | None) -> TitleRead:
    """The document's title and work sentence, verbatim from the PDF text."""
    out = TitleRead()
    if not text:
        return out
    raw_lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in raw_lines if ln]
    squashed = []
    for ln in lines:
        s = _squash(ln)
        if s != ln:                      # a letter-spaced heading may carry the Θ-for-Η font
            for rx, r in _THETA_WORDS:
                s = rx.sub(r, s)
        squashed.append(s)
    # the heading: the first line (in the first 150) that IS the document's
    # name — then its continuation lines until the opening sentence
    for i, ln in enumerate(squashed[:150]):
        up = fold(ln)
        # a stray drop-cap or bullet before the word («Σ ΣΥΜΦΩΝΗΤΙΚΟ», «• ΣΥΜΒΑΣΗ»)
        up = re.sub(r"^(?:[Α-Ω•·\-–]\s+)", "", up)
        if not _HEAD_START.match(up):
            continue
        # «σύμβαση παροχής υπηρεσιών … η υπ' αριθ. 165/2025 απόφαση» inside a
        # recital is not a heading; nor is a line that is a whole paragraph
        if len(ln) > 140 or re.search(r"ΥΠ[’'`]?\s*ΑΡΙ[ΘΚ]|ΑΠΟ[ΦΥ]ΑΣ|\bΠΕΡΙ\s|ΕΓΚΡΙΣ|ΠΡΑΚΤΙΚ|ΑΔΑ:|ΑΔΑΜ", up):
            continue
        block = [squashed[i]]
        for nxt in squashed[i + 1:i + 8]:
            u = fold(nxt)
            if _HEAD_STOP.match(u) or len(nxt) > 220:
                break
            block.append(nxt)
        heading = " ".join(block).strip()
        cut = _HEAD_CUT.search(fold(heading))
        if cut:
            heading = heading[:cut.start()].strip()
        out.heading = heading
        out.heading_line = i
        break
    flat = re.sub(r"\s+", " ", text)
    if _LETTER_SPACED.search(flat[:12000]):
        flat = _SPACED_RUN.sub(lambda m: m.group(0).replace(" ", ""), flat)
    up, idx = fold_map(flat)
    if not out.heading:
        # a two-column letterhead can break the heading across lines that
        # start with the address column; the flat text still has it
        m = _HEAD_FLAT.search(up)
        if m:
            out.heading = " ".join(flat[idx[m.start()]:idx[m.end()]].split())
            out.heading_line = -1
    # the quoted title — the first one NOT inside a recital
    for m in _QUOTED.finditer(up):
        head = up[max(0, m.start() - 120):m.start()]
        if _QUOTED_BAD_HEAD.search(head):
            continue
        out.quoted = " ".join(flat[idx[m.start(2)]:idx[m.end(2)]].split())
        break
    # the work sentence — the first anchor whose head is not money/decision
    for rx in (_WORK, _WORK_LOOSE):
        for m in rx.finditer(up):
            head = up[max(0, m.start() - 60):m.start()]
            if _WORK_BAD_HEAD.search(head):
                continue
            g = next(x for x in m.groups() if x)
            s, e = m.start(), m.start() + len(g)
            frag = " ".join(flat[idx[s]:idx[min(e, len(idx) - 1)]].split())
            if len(frag) < 12:
                continue
            out.work = frag
            break
        if out.work:
            break
    for m in _NEED.finditer(up):
        # the clause starts with «Την ανάγκη …» itself; only a need that is
        # someone else's («απόφαση … περί της ανάγκης») is skipped
        head = up[max(0, m.start() - 30):m.start()]
        if re.search(r"ΑΠΟΦΑΣ|ΕΓΓΡΑΦ|ΕΙΣΗΓΗΣ", head):
            continue
        out.need = " ".join(flat[idx[m.start()]:idx[min(m.end(), len(idx) - 1)]].split())
        break
    return out


# --------------------------------------------------------- the category read

@dataclass
class CategoryRead:
    category: str | None = None
    evidence: str = ""                  # the matched sentence, verbatim
    evidence_field: str | None = None   # heading | quoted | work
    matched: list[str] = field(default_factory=list)   # every family that fired
    context: str | None = None
    context_evidence: str = ""
    context_matched: list[str] = field(default_factory=list)
    title: TitleRead = field(default_factory=TitleRead)
    scan: bool = False
    review: list[str] = field(default_factory=list)


_COMPATIBLE = {frozenset(p) for p in (("kafsoxyla", "ylotomia"), ("kalliergitikes", "ylotomia"))}


def _hits_on(rx_rules, val: str) -> list[tuple[str, int, int]]:
    """(key, start, end) for every rule that fires on ONE field, in rule order."""
    if not val:
        return []
    up, idx = fold_map(val)
    out = []
    for key, rx in rx_rules:
        m = rx.search(up)
        if m:
            out.append((key, idx[m.start()], idx[min(m.end(), len(idx) - 1)]))
    return out


def _sentence(val: str, s: int, e: int) -> str:
    return val if len(val) <= 320 else " ".join(val[max(0, s - 120):e + 160].split())


def read_category(text: str | None) -> CategoryRead:
    """Propose the category and the fire context from the PDF's own title
    and work sentence — the heading decides, then the quoted title, then the
    work sentence; never the registry title, never a recital."""
    fixed, notes = repair(text)
    state = text_state(fixed)
    out = CategoryRead(scan=state != "ok")
    out.review.extend(notes)
    if state == "scan":
        out.review.append("scan: no readable text layer — read by eye")
        return out
    t = read_title(fixed)
    out.title = t
    if state == "unreadable_font":
        # a cipher body under a clean-font heading (Φουρνά, Ξάνθη): the
        # heading alone may still name the work; the body stays unread
        fields = [("heading", t.heading), ("quoted", t.quoted)]
        hits = next(((f, _hits_on(_RULES_RX, v)) for f, v in fields if v and _hits_on(_RULES_RX, v)), None)
        if hits:
            fname, hs = hits
            key, s, e = hs[0]
            out.category, out.evidence_field, out.evidence = key, fname, _sentence(dict(fields)[fname], s, e)
            out.matched = list(dict.fromkeys(k for k, *_ in hs))
            chits = _hits_on(_CONTEXT_RX, dict(fields)[fname])
            if chits:
                out.context, out.context_evidence = chits[0][0], _sentence(dict(fields)[fname], chits[0][1], chits[0][2])
            out.review.append("unreadable_font: cipher text layer — the heading is clean and names the work; the body (work sentence, deadline) is read by eye")
            out.scan = False
            return out
        out.review.append("unreadable_font: substitution-cipher text layer — read by eye")
        return out
    fields = [("heading", t.heading), ("quoted", t.quoted), ("work", t.work)]
    all_found: list[str] = []
    for fname, val in fields:
        hits = _hits_on(_RULES_RX, val)
        all_found.extend(k for k, *_ in hits)
        if hits and out.category is None:
            key, s, e = hits[0]
            out.category, out.evidence_field, out.evidence = key, fname, _sentence(val, s, e)
            fams = list(dict.fromkeys(k for k, *_ in hits))
            if len(fams) > 1 and not all(frozenset((a, b)) in _COMPATIBLE
                                         for i, a in enumerate(fams) for b in fams[i + 1:]):
                out.review.append(f"the {fname} names two works: " + ", ".join(fams))
    out.matched = list(dict.fromkeys(all_found))
    if out.category is None:
        out.review.append("no rule fired on the title or the work sentence")
    cfound: list[str] = []
    for fname, val in fields + [("need", t.need)]:
        hits = _hits_on(_CONTEXT_RX, val)
        cfound.extend(k for k, *_ in hits)
        if hits and out.context is None:
            key, s, e = hits[0]
            out.context, out.context_evidence = key, _sentence(val, s, e)
    out.context_matched = list(dict.fromkeys(cfound))
    if len(out.context_matched) > 1:
        out.review.append("both fire contexts named")
    if not t.heading and not t.quoted and not t.work:
        out.review.append("no title or work sentence found in the text")
    return out


# --------------------------------------------------------- the deadline read

_MONTHS = {
    "ΙΑΝΟΥΑΡ": 1, "ΦΕΒΡΟΥΑΡ": 2, "ΜΑΡΤ": 3, "ΑΠΡΙΛ": 4, "ΜΑΙ": 5, "ΜΑΪ": 5,
    "ΙΟΥΝ": 6, "ΙΟΥΛ": 7, "ΑΥΓΟΥΣΤ": 8, "ΣΕΠΤΕΜΒΡ": 9, "ΟΚΤΩΒΡ": 10,
    "ΝΟΕΜΒΡ": 11, "ΔΕΚΕΜΒΡ": 12,
}
_DATE = re.compile(r"(\d{1,2})\s?[./-]\s?(\d{1,2})\s?[./-]\s?(\d{4}|\d{2})(?!\d)")
_MDATE = re.compile(
    r"(\d{1,2})\s*(?:Η|ΗΣ|ΑΣ)?\s+(ΙΑΝΟΥΑΡ|ΦΕΒΡΟΥΑΡ|ΜΑΡΤ|ΑΠΡΙΛ|ΜΑ[ΙΪ]|ΙΟΥΝ|ΙΟΥΛ|ΑΥΓΟΥΣΤ|ΣΕΠΤΕΜΒΡ|ΟΚΤΩΒΡ|ΝΟΕΜΒΡ|ΔΕΚΕΜΒΡ)\w*\s+(?:ΤΟΥ\s+ΕΤΟΥΣ\s+)?(\d{4})")
# the anchors that say WHEN it ends, then a date within the window
_DATE_ANCHORS: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("προθεσμία εκτελέσεως μέχρι", re.compile(loose("ΠΡΟΘΕΣΜΙ") + r"\w{0,3}\s+" + loose("ΕΚΤ") + r"[ΕΖ]ΛΕ[ΣΖ]?\w{0,4}-?\s*:?\s*(?:" + loose("ΜΕΧΡΙ") + r")?\s*:?\s*(?:ΤΗΝ|ΤΙΣ|ΤΗ)?"), 40),
    ("εντός του προκαθορισμένου χρόνου (έως …)", re.compile(loose("ΠΡΟΚΑΘΟΡΙΣΜ") + r"\w*\s+" + loose("ΧΡΟΝ") + r"\w*\s*\(?\s*(?:" + loose("ΕΩΣ") + r"|" + loose("ΜΕΧΡΙ") + r")\s*(?:ΤΗΝ|ΤΙΣ|ΤΗ)?\s*"), 30),
    ("θα εκτελεσθεί … μέχρι", re.compile(r"(?:ΘΑ\s+" + loose("ΕΚΤΕΛΕΣ") + r"\w*|ΝΑ\s+" + loose("ΕΚΤΕΛΕΣ") + r"\w*\s+(?:ΤΗΝ\s+)?(?:ΥΠΗΡΕΣΙΑ|ΕΡΓΑΣΙΑ|ΠΡΟΜΗΘΕΙΑ)).{0,90}?(?:" + loose("ΜΕΧΡΙ") + r"|" + loose("ΕΩΣ") + r")\s*(?:ΚΑΙ\s+)?(?:ΤΗΝ|ΤΙΣ|ΤΗ)?\s*"), 30),
    ("λήγει την", re.compile(r"\b" + loose("ΛΗΓ") + r"(?:ΕΙ|ΟΥΣΑ|ΟΥΝ|ΟΝΤΑΣ)\b\s*(?:" + loose("ΑΝΥΠΕΡΘΕΤ") + r"\w*\s*|" + loose("ΑΠΑΡΑΙΤΗΤ") + r"\w*\s*)?(?:ΤΗΝ|ΣΤΙΣ|ΤΙΣ|ΤΗ|ΣΤΗΝ)?\s*"), 40),
    ("περαίωση την", re.compile(loose("ΠΕΡΑΙΩΣ") + r"\w*\s+(?:ΤΟΥΣ\s+|ΤΟΥ\s+ΕΡΓΟΥ\s+|ΤΩΝ\s+ΕΡΓΑΣΙΩΝ\s+)?(?:ΤΗΝ|ΣΤΙΣ|ΤΙΣ|ΕΩΣ|ΜΕΧΡΙ)\s*(?:ΤΗΝ|ΤΙΣ)?\s*"), 40),
    ("προθεσμία/διάρκεια … έως/μέχρι", re.compile(r"(?:" + loose("ΠΡΟΘΕΣΜΙ") + r"|" + loose("ΔΙΑΡΚΕΙ") + r"|" + loose("ΙΣΧΥ") + r"|" + loose("ΧΡΟΝΟΣ") + r"\s*" + loose("ΠΑΡΑΔΟΣ") + r"|" + loose("ΟΛΟΚΛΗΡΩΣ") + r"|" + loose("ΥΛΟΠΟΙΗΣ") + r"|" + loose("ΕΚΤΕΛΕΣ") + r"\w*\s+" + loose("ΤΩΝ") + r")\w*.{0,120}?\b(?:" + loose("ΕΩΣ") + r"|" + loose("ΜΕΧΡΙ") + r")\b\s*(?:ΚΑΙ\s+)?(?:ΤΗΝ|ΤΙΣ|ΤΗ|ΤΟ|ΤΟΥ)?\s*"), 30),
)
_DATE_REJECT = re.compile(r"ΠΑΡΑΤΑ|ΠΟΙΝΙΚ|ΡΗΤΡ|ΕΓΓΥΗ|ΑΣΦΑΛΙΣΤ|ΤΙΜΟΛΟΓ|ΠΛΗΡΩΜ|ΥΠΟΒΟΛ|ΠΡΟΣΦΟΡ|ΑΙΤΗΣ|ΔΙΚΑΙΟΛΟΓΗΤ|ΠΙΣΤΩΣ|ΠΡΩΤΟΚΟΛΛΟ\s+ΠΑΡΑΛΑΒ|ΙΣΧΥ\w*\s+ΤΩΝ\s+ΠΡΟΣΦ")
# a duration in the ΔΑΣΕ dialect: «έχει διάρκεια ενός (1) μηνός», «θα είναι
# (1) ένας μήνας», «για ένα έτος»
_DUR = re.compile(
    r"(?:" + loose("ΔΙΑΡΚΕΙ") + r"\w*|" + loose("ΠΡΟΘΕΣΜΙ") + r"\w*|" + loose("ΧΡΟΝΟΣ") + r")"
    r".{0,80}?(?:\((\d{1,3})\)|\b(ΕΝΟΣ|ΕΝΑ|ΕΝΑΣ|ΜΙΑΣ|ΜΙΑ|ΔΥΟ|ΤΡΙΩΝ|ΤΡΕΙΣ|ΤΕΣΣΑΡΩΝ|ΤΕΣΣΕΡΙΣ|ΠΕΝΤΕ|ΕΞΙ|ΕΠΤΑ|ΟΚΤΩ|ΕΝΝΕΑ|ΔΕΚΑ|ΔΩΔΕΚΑ|ΔΕΚΑΠΕΝΤΕ|ΕΙΚΟΣΙ|ΤΡΙΑΝΤΑ|ΕΞΗΝΤΑ)\b)"
    r"\s*(?:\((\d{1,3})\)\s*)?(" + loose("ΜΗΝ") + r"\w*|" + loose("ΗΜΕΡ") + r"\w*|ΕΤ(?:ΟΣ|ΟΥΣ|Η|ΩΝ)\b|ΧΡΟΝ(?:Ο|ΟΥ|ΙΑ|ΩΝ)\b)")
_WORD_N = {"ΕΝΟΣ": 1, "ΕΝΑ": 1, "ΕΝΑΣ": 1, "ΜΙΑΣ": 1, "ΜΙΑ": 1, "ΔΥΟ": 2, "ΤΡΙΩΝ": 3,
           "ΤΡΕΙΣ": 3, "ΤΕΣΣΑΡΩΝ": 4, "ΤΕΣΣΕΡΙΣ": 4, "ΠΕΝΤΕ": 5, "ΕΞΙ": 6, "ΕΠΤΑ": 7,
           "ΟΚΤΩ": 8, "ΕΝΝΕΑ": 9, "ΔΕΚΑ": 10, "ΔΩΔΕΚΑ": 12, "ΔΕΚΑΠΕΝΤΕ": 15,
           "ΕΙΚΟΣΙ": 20, "ΤΡΙΑΝΤΑ": 30, "ΕΞΗΝΤΑ": 60}
_OPEN = re.compile(
    loose("ΜΕΧΡΙ") + r"\s*(?:ΤΗΣ\s+|ΤΗΝ\s+)?" + loose("ΕΞΑΝΤΛΗΣ") + r"|"
    + loose("ΑΟΡΙΣΤΟΥ") + r"\s*" + loose("ΔΙΑΡΚΕΙ") + r"|"
    + loose("ΛΗΓΕΙ") + r"\s+ΜΕ\s+ΤΗΝ\s+" + loose("ΟΛΟΚΛΗΡΩΣ") + r"|"
    + loose("ΜΕΧΡΙ") + r"\s+(?:ΤΗΝ\s+)?" + loose("ΟΛΟΚΛΗΡΩΣ") + r"\w*\s+ΤΩΝ\s+ΕΡΓΑΣΙΩΝ|"
    + loose("ΜΕΧΡΙ") + r"\s+(?:ΤΗΝ\s+)?" + loose("ΠΕΡΑΙΩΣ") + r"\w*\s+ΤΩΝ\s+ΕΡΓΑΣΙΩΝ\b(?!\s+\d)")


@dataclass
class DeadlineRead:
    kind: str | None = None            # date | duration | open_ended | None
    deadline_date: str | None = None   # ISO, when the text names a date
    n: int | None = None
    unit: str | None = None
    basis: str | None = None
    anchor: str | None = None
    excerpt: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def days(self) -> int | None:
        if self.n is None:
            return None
        return {"days": self.n, "years": self.n * 365,
                "months": round(self.n * 30.44)}.get(self.unit or "")


def _parse_date(up: str, at: int) -> tuple[str | None, int, int]:
    """A date at/after `at` in the folded text: ISO, start, end."""
    m = _DATE.match(up, at) or _DATE.search(up, at, at + 12)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return _dt.date(y, mo, d).isoformat(), m.start(), m.end()
        except ValueError:
            return None, m.start(), m.end()
    m = _MDATE.match(up, at) or _MDATE.search(up, at, at + 14)
    if m:
        mo = next((v for k, v in _MONTHS.items() if m.group(2).startswith(k)), None)
        if mo:
            try:
                return _dt.date(int(m.group(3)), mo, int(m.group(1))).isoformat(), m.start(), m.end()
            except ValueError:
                return None, m.start(), m.end()
    return None, -1, -1


def read_deadline(text: str | None, signed: str | None = None) -> DeadlineRead:
    """The deadline the document states — a date, a duration, an open end,
    or nothing. `signed` (ISO) lets a date be sanity-checked."""
    out = DeadlineRead()
    text, notes = repair(text)
    if not text or text_state(text) != "ok":
        if text:
            out.flags.append(text_state(text))
        return out
    out.flags.extend(notes)
    flat = re.sub(r"\s+", " ", text)
    up, idx = fold_map(flat)

    def cut(s: int, e: int) -> str:
        return " ".join(flat[max(0, idx[max(0, s)] - 110):idx[min(e, len(idx) - 1)] + 70].split())

    # 1. a date the text names as the end
    for name, rx, win in _DATE_ANCHORS:
        for m in rx.finditer(up):
            head = up[max(0, m.start() - 60):m.start()]
            mid = up[m.start():m.end()]
            if _DATE_REJECT.search(head) or _DATE_REJECT.search(mid):
                continue
            iso, s, e = _parse_date(up, m.end())
            if s < 0 or s - m.end() > win:
                continue
            if iso is None:
                out.flags.append("date does not parse")
                continue
            out.kind, out.deadline_date, out.anchor = "date", iso, name
            out.excerpt = cut(m.start(), e)
            if signed and iso < signed[:10]:
                out.flags.append("deadline before signature (as written)")
            if signed and iso > (str(int(signed[:4]) + 4) + signed[4:10]):
                out.flags.append("more than four years after signature")
            return out
    # 2. a duration — the Anti-nero clause first, then the ΔΑΣΕ dialect
    a: DurationRead | None = read_antinero_duration(text)
    if a and a.n:
        out.kind, out.n, out.unit, out.basis = "duration", a.n, a.unit, a.basis
        out.anchor, out.excerpt = a.anchor, a.excerpt
        out.flags.extend(a.notes)
        return out
    for m in _DUR.finditer(up):
        head = up[max(0, m.start() - 60):m.start()]
        if _DATE_REJECT.search(head) or re.search(r"ΠΟΙΝΙΚ|ΡΗΤΡ|ΕΓΓΥΗ|ΠΑΡΑΤΑ|ΤΟΙΣ ΕΚΑΤΟ|%", up[m.start():m.end()]):
            continue
        n = m.group(1) or m.group(3)
        n = int(n) if n else _WORD_N.get(m.group(2) or "")
        if not n:
            continue
        u = m.group(4)
        unit = "months" if u.startswith("Μ") else "days" if u.startswith("Η") else "years"
        out.kind, out.n, out.unit, out.anchor = "duration", n, unit, "διάρκεια … (n) μήνες/ημέρες/έτη"
        out.excerpt = cut(m.start(), m.end())
        tail = up[m.end():m.end() + 120]
        if re.search(loose("ΥΠΟΓΡΑΦ"), tail):
            out.basis = "signature"
        elif re.search(loose("ΕΝΑΡΞ") + "|" + loose("ΕΓΚΑΤΑΣΤΑΣ"), tail):
            out.basis = "works_start"
        return out
    # 3. an open end
    m = _OPEN.search(up)
    if m:
        out.kind, out.anchor = "open_ended", "μέχρι εξαντλήσεως / αορίστου διάρκειας / με την ολοκλήρωση"
        out.excerpt = cut(m.start(), m.end())
    return out
