"""What a contract's works actually ARE, read from its own project title.

The curated work-type layer gives each contract ONE category, and 154 of
246 land in «Δασοτεχνικά έργα πρόληψης» — true but vague. The detail is
already in the data: the descriptive project title inside the signed PDF
carries a purpose clause, and 153 of 246 titles name at least one specific
kind of work while **101 name two or more** (DATA_DECISIONS 2026-08-19):

    «…για τον καθαρισμό των δασών και δασικών εκτάσεων και τη συντήρηση
     του δασικού οδικού δικτύου αρμοδιότητας Δασαρχείου Αρναίας»

So this layer is MULTI-LABEL and additive: the category stays the single
key that reconciles to the basis, the themes say what was bought.

Three sources were tested and rejected as per-contract evidence:

* the contract's «Αντικείμενο της Σύμβασης» article — boilerplate in all
  206 that carry it: it points to the Μελέτες in the call's annexes, which
  ΚΗΜΔΗΣ does not publish;
* the πρόσκληση's own text — it names 4 to 10 themes per call because it
  lists the programme's whole menu, not this lot's work (measured on the
  91 cached calls of the contracts whose titles say nothing specific);
* CPV codes — median 14 per contract, the top code on 226 of 246, and the
  set belongs to the call. They are kept here as a SCREEN only: a marker
  code with no matching theme is a question for the curator, never a label.

93 contracts state nothing beyond «αντιπυρική προστασία». They stay that
way — an honest «the contract says no more» beats an invented theme.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def fold(s: str) -> str:
    """Uppercase + strip accents (no homoglyph translation)."""
    s = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))


@dataclass(frozen=True)
class Theme:
    key: str
    el: str
    en: str
    pattern: str


# The vocabulary. Stems are deliberately short — titles inflect and
# abbreviate («ΚΑΘΑΡΙΣΜΟ», «ΚΑΘΑΡΙΣΜΩΝ», «ΔΑΣΟΔΡΟΜΩΝ»).
THEMES: tuple[Theme, ...] = (
    Theme("katharismoi", "Καθαρισμοί δασών & δασικών εκτάσεων",
          "Clearing of forests and forest land",
          r"ΚΑΘΑΡΙΣΜ"),
    Theme("odiko_diktyo", "Δασικό οδικό δίκτυο",
          "Forest road network",
          r"ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ|ΔΑΣΙΚ\w*\s+ΔΡΟΜ|ΔΑΣΟΔΡΟΜ|ΟΔΟΠΟΙΙΑΣ"),
    Theme("antipyrikes_zones", "Αντιπυρικές ζώνες",
          "Firebreaks",
          r"ΑΝΤΙΠΥΡΙΚ\w*\s+ΖΩΝ"),
    Theme("miktes_zones", "Μικτές / εστεγασμένες αντιπυρικές ζώνες",
          "Mixed and sheltered firebreaks",
          r"ΕΣΤΕΓΑΣΜΕΝ|ΜΙΚΤ\w*\s+ΑΝΤΙΠΥΡΙΚ|ΜΙΚΤ\w*\s+ΖΩΝ"),
    Theme("nero", "Υδατοδεξαμενές & σημεία υδροληψίας",
          "Water tanks and water points",
          r"ΥΔΑΤΟΔΕΞΑΜΕΝ|ΔΕΞΑΜΕΝ|ΥΔΡΟΛΗΨΙ|ΠΥΡΟΣΒΕΣΤΙΚ\w*\s+ΚΡΟΥΝ"),
    Theme("ylotomies", "Υλοτομίες & απομάκρυνση ξηρών",
          "Logging and removal of dead stands",
          r"ΥΛΟΤΟΜ|ΞΗΡΩΝ ΙΣΤΑΜΕΝ|ΝΕΚΡΩΝ ΔΕΝΔΡ|ΑΠΟΛΗΨΗ"),
    Theme("anadasoseis", "Αναδασώσεις, φυτεύσεις & φυτώρια",
          "Reforestation, planting and nurseries",
          r"ΑΝΑΔΑΣΩ|ΦΥΤΩΡΙ|ΦΥΤΕΥΣ|ΑΝΑΔΑΣΩΤΕ"),
    Theme("antidiavrotika", "Αντιδιαβρωτικά & αντιπλημμυρικά έργα",
          "Anti-erosion and flood-protection works",
          r"ΑΝΤΙΔΙΑΒΡΩΤΙΚ|ΑΝΤΙΠΛΗΜΜΥΡΙΚ|ΔΙΑΒΡΩΣ|ΚΟΡΜΟΔΕΜΑΤ|ΚΛΑΔΟΠΛΕΓΜΑΤ"),
    Theme("meletes", "Μελέτες, σχεδιασμός & χαρτογράφηση",
          "Studies, planning and mapping",
          r"ΜΕΛΕΤ|ΧΑΡΤΟΓΡΑΦ|ΣΧΕΔΙΑΣΜ"),
    Theme("arxaiologikoi", "Αρχαιολογικοί χώροι, μονές & αισθητικά δάση",
          "Archaeological sites, monasteries and aesthetic forests",
          r"ΑΡΧΑΙΟΛΟΓΙΚ|ΙΕΡ\w*\s+ΜΟΝ|ΑΙΣΘΗΤΙΚ"),
    Theme("perifraxi", "Περιφράξεις & σήμανση",
          "Fencing and signage",
          r"ΠΕΡΙΦΡΑΞ|ΣΗΜΑΝΣ|ΠΙΝΑΚΙΔ"),
    Theme("dasokomika", "Αραιώσεις & δασοκομικοί χειρισμοί",
          "Thinning and silvicultural treatment",
          r"ΑΡΑΙΩΣ|ΔΑΣΟΚΟΜΙΚ|ΚΛΑΔΕΥΣ|ΥΠΟΚΑΘΑΡΙΣΜ|ΒΛΑΣΤΗΣ"),
)
BY_KEY = {t.key: t for t in THEMES}

# CPV codes that MARK a kind of work. Used only to ask a question: «this
# contract's CPV list names water tanks, its title names no water works —
# which is right?». 28 in-scope contracts carry 44611500-1 while the
# curated categories call exactly one of them a water-infrastructure job.
CPV_MARKERS: dict[str, str] = {
    # water infrastructure — the marker that actually discriminates: 28
    # in-scope contracts carry «Δεξαμενές νερού» while the curated
    # categories call exactly one of them a water job
    "44611500-1": "nero",           # Δεξαμενές νερού (28 contracts)
    "51810000-3": "nero",           # Εγκατάσταση δεξαμενών (26)
    "45221230-3": "nero",           # Φρέατα (23)
    "50514200-3": "nero",           # Επισκευή/συντήρηση δεξαμενών (21)
    "45247270-3": "nero",           # Κατασκευή δεξαμενών (10)
    "77231600-4": "anadasoseis",    # Υπηρεσίες δάσωσης (6)
    "77211400-6": "ylotomies",      # Υπηρεσίες κοπής δένδρων (6)
    "45342000-6": "perifraxi",      # Τοποθέτηση περιφράξεων
    "45112700-2": "anadasoseis",    # Εργασίες διαμόρφωσης τοπίου
    # NOT markers, though they name work: «Εργασίες συντήρησης οδών»
    # (45233141-9) rides on 130 of 246 contracts and «Υπηρεσίες ψηφιακής
    # χαρτογράφησης» (71354100-5) on 119 — they are the call's menu, and
    # asking about them 156 times would bury the questions worth asking.
}


@dataclass
class ThemeHit:
    key: str
    excerpt: str          # the verbatim clause, from the ORIGINAL title


def _excerpt(text: str, at: int, width: int = 58) -> str:
    """A verbatim window around the match, cut at word boundaries."""
    start, stop = max(0, at - width // 2), min(len(text), at + width)
    frag = text[start:stop]
    if start > 0:
        cut = frag.find(" ")
        if 0 <= cut <= 18:
            frag = frag[cut + 1:]
    if stop < len(text):
        cut = frag.rfind(" ")
        if cut > len(frag) - 22:
            frag = frag[:cut]
    return (("… " if start > 0 else "") + " ".join(frag.split())
            + (" …" if stop < len(text) else ""))


def read_title(title: str | None) -> list[ThemeHit]:
    """Themes stated by ONE project title, in the vocabulary's order."""
    if not title:
        return []
    up = fold(title)
    same = len(up) == len(title)
    out: list[ThemeHit] = []
    for t in THEMES:
        m = re.search(t.pattern, up)
        if m is None:
            continue
        out.append(ThemeHit(t.key, _excerpt(title if same else up, m.start())))
    return out


def cpv_questions(keys: set[str], cpvs: list[str]) -> list[tuple[str, str]]:
    """(cpv, theme) pairs the CPV list implies but the title never states."""
    out: list[tuple[str, str]] = []
    for code in cpvs:
        theme = CPV_MARKERS.get((code or "").strip())
        if theme and theme not in keys:
            out.append((code, theme))
    return out
