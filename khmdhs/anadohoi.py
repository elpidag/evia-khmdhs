"""Ανάδοχοι αναδάσωσης/αποκατάστασης (ν.998/1979 άρθρο 42 §3) — pure helpers.

Private sponsors finance and execute restoration/reforestation of burnt
public forest land at their own expense and are appointed by administrative
act on Diavgeia (no procurement → no KHMDHS record). This module holds the
side-effect-free pieces shared by the harvest script and the loader:

- classify(): a *proposal* classifier over (subject, organization). A human
  reviews every verdict before it becomes data — titles lie («ΔΩΡΕΑ ΓΙΑ
  ΑΝΑΔΑΣΩΣΗ…» Ω2ΕΞ4653Π8-6ΟΟ is in fact a πράξη ορισμού).
- cited_adas(): the ΑΔΑ-citation regex used to crawl a PDF's recitals.
- Greek parsing: amounts («395.200,40€»), area in στρέμματα, and dates
  («18η Δεκεμβρίου 2021», «έως τέλος 2024», dd.mm.yyyy…).

The scheme was created by the 13.08.2021 ΠΝΠ (Α΄143); anything published
before that date cannot belong to it.
"""
from __future__ import annotations

import re
import unicodedata

from khmdhs.dase import fold

SCHEME_START = "2021-08-13"

# Kinds a candidate decision can be proposed as. RELEVANT ones get their
# PDF fetched and their citations crawled.
RELEVANT_KINDS = ("orismos", "tropopoiisi", "anaklisi", "oloklirosi",
                  "aitima", "lifecycle")

# Only δασικές υπηρεσίες issue acts of this scheme: ΥΠΕΝ (post-2022
# structure) and the Αποκεντρωμένες Διοικήσεις (pre-transfer era).
_FOREST_ORG_STEMS = ("ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ", "ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ")

_LIFECYCLE_STEMS = ("ΠΑΡΑΛΑΒ", "ΠΡΩΤΟΚΟΛΛ", "ΗΜΕΡΟΛΟΓΙ", "ΧΡΟΝΟΔΙΑΓΡΑΜΜ",
                    "ΚΑΤΑΣΚΕΥΑΣΤΙΚ", "ΕΓΚΑΤΑΣΤΑΣ", "ΑΝΑΚΕΦΑΛΑΙΩΤΙΚ",
                    "ΕΠΙΜΕΤΡΗΣ", "ΕΠΙΒΛΕΠ", "ΕΠΙΒΛΕΨ")
# Admin housekeeping that would otherwise trip the lifecycle stems
# («Ορισμός Αναπληρωτή Προϊσταμένου…» is cited in every single act), plus
# land-status instruments that are NOT scheme acts (κήρυξη αναδασωτέας
# happens after every fire regardless of sponsors).
_ADMIN_STEMS = ("ΠΡΟΙΣΤΑΜΕΝ", "ΔΙΟΡΙΣΜ", "ΥΠΑΛΛΗΛ", "ΜΕΤΑΚΙΝΗΣ",
                "ΚΥΝΗΓΕΤΙΚ", "ΑΠΟΣΠΑΣ", "ΑΝΑΔΑΣΩΤΕ", "ΠΡΟΣΛΗΨ",
                "ΘΗΡΑΣ", "ΑΔΕΙΑΣ ΧΡΗΣΗΣ ΝΕΡΟΥ")


def _norm(subject: str | None) -> str:
    """fold + collapse whitespace (subjects embed \\r\\n)."""
    return re.sub(r"\s+", " ", fold(subject or "")).strip()


def is_forest_org(org_label: str | None) -> bool:
    f = _norm(org_label)
    return any(stem in f for stem in _FOREST_ORG_STEMS)


def classify(subject: str | None, org_label: str | None,
             issue_date: str | None = None) -> str:
    """Propose a kind for a candidate decision. NEVER final on its own:
    ambiguous/noise verdicts on forest-org hits are human-reviewed against
    the PDF (see anadohoi_projects.json `decisions`)."""
    if not is_forest_org(org_label):
        return "noise"
    if issue_date and issue_date[:10] < SCHEME_START:
        return "noise"          # the scheme did not exist yet
    s = _norm(subject)
    # A πρωτόκολλο εγκατάστασης may quote the πράξη ορισμού verbatim in its
    # subject (66584653Π8-9Φ3) — the protocol wins over the quoted phrase.
    if "ΠΡΩΤΟΚΟΛΛΟ ΕΓΚΑΤΑΣΤΑΣ" in s:
        return "lifecycle"
    if "ΑΝΑΔΟΧ" in s:
        if "ΑΝΑΚΛΗΣ" in s:
            return "anaklisi"
        if "ΤΡΟΠΟΠΟΙΗΣ" in s:
            return "tropopoiisi"
        if "ΔΥΝΗΤΙΚ" in s or "ΥΠΟΒΟΛΗ ΑΙΤΗΜΑΤΟΣ" in s:
            return "aitima"
        if "ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ" in s or "ΟΡΙΣΜΟΣ ΑΝΑΔΟΧΟΥ" in s \
                or "ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΩΝ" in s:
            return "orismos"
    if "ΔΙΑΠΙΣΤΩΤΙΚ" in s and ("ΟΛΟΚΛΗΡΩΣ" in s or "ΠΕΡΑΤΩΣ" in s):
        return "oloklirosi"
    if any(stem in s for stem in _ADMIN_STEMS):
        return "noise"
    if any(stem in s for stem in _LIFECYCLE_STEMS) \
            or (("ΕΓΚΡΙΣ" in s or "ΘΕΩΡΗΣ" in s) and "ΜΕΛΕΤ" in s):
        return "lifecycle"
    return "unknown"


# --------------------------------------------------------------------------
# ΑΔΑ citations

# Diavgeia ΑΔΑ: 4 random chars + the org code + '-' + 3 chars, digits and
# Greek capitals. Org codes are 3–6 chars (περιφέρειες/δήμοι 3, ΑΠΔ «ΟΡ10» 4,
# ΥΠΕΝ «4653Π8» 6) → prefixes 7–10 chars; the old exactly-{10} pattern missed
# every ΑΠΔ/δήμος citation. PDFs occasionally render Greek caps as Latin
# homoglyphs.
_LATIN2GREEK = str.maketrans("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ")
_ADA_TOKEN = re.compile(
    r"(?<![0-9Α-ΩA-Z])([0-9Α-ΩA-Z]{7,12}-[0-9Α-ΩA-Z]{3})(?![0-9Α-ΩA-Z])")


def cited_adas(text: str, own_ada: str | None = None) -> list[str]:
    """All ΑΔΑ-shaped tokens in a PDF text, homoglyph-normalised, deduped in
    order of appearance, excluding the document's own ΑΔΑ (stamped on every
    page). Candidates are verified against the live registry by the caller —
    a 404 means 'not actually an ΑΔΑ', not an error."""
    own = unicodedata.normalize("NFC", own_ada or "").translate(_LATIN2GREEK)
    out: list[str] = []
    for m in _ADA_TOKEN.finditer(unicodedata.normalize("NFC", text)):
        tok = m.group(1).translate(_LATIN2GREEK)
        if not any(c.isdigit() for c in tok):
            continue
        if not any("Α" <= c <= "Ω" for c in tok):
            continue
        if tok != own and tok not in out:
            out.append(tok)
    return out


# --------------------------------------------------------------------------
# Greek number / date parsing

_AMOUNT_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:€|ΕΥΡΩ|Ευρώ|ευρώ)")
_STREM_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,3})?)\s*(?:στρ\.|στρεμ\w*|ΣΤΡΕΜ\w*)")


def parse_greek_number(s: str) -> float:
    """'395.200,40' → 395200.40 (dot thousands, comma decimal)."""
    return float(s.replace(".", "").replace(",", "."))


def amounts_with_context(text: str, window: int = 130) -> list[tuple[float, str]]:
    out = []
    for m in _AMOUNT_RE.finditer(text):
        lo, hi = max(0, m.start() - window), min(len(text), m.end() + window)
        excerpt = re.sub(r"\s+", " ", text[lo:hi]).strip()
        out.append((parse_greek_number(m.group(1)), excerpt))
    return out


def stremmata_with_context(text: str, window: int = 110) -> list[tuple[float, str]]:
    out = []
    for m in _STREM_RE.finditer(text):
        lo, hi = max(0, m.start() - window), min(len(text), m.end() + window)
        excerpt = re.sub(r"\s+", " ", text[lo:hi]).strip()
        out.append((parse_greek_number(m.group(1)), excerpt))
    return out


_MONTHS = {
    "ΙΑΝΟΥΑΡΙ": 1, "ΦΕΒΡΟΥΑΡΙ": 2, "ΜΑΡΤΙ": 3, "ΑΠΡΙΛΙ": 4, "ΜΑΙ": 5,
    "ΙΟΥΝΙ": 6, "ΙΟΥΛΙ": 7, "ΑΥΓΟΥΣΤ": 8, "ΣΕΠΤΕΜΒΡΙ": 9, "ΟΚΤΩΒΡΙ": 10,
    "ΝΟΕΜΒΡΙ": 11, "ΔΕΚΕΜΒΡΙ": 12,
}
_NUMERIC_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b")
# «18η Δεκεμβρίου 2021», «31 Δεκεμβρίου του 2027» (fold()ed input)
_PROSE_DATE = re.compile(
    r"\b(\d{1,2})Η?Σ?\s+(ΙΑΝΟΥΑΡΙ|ΦΕΒΡΟΥΑΡΙ|ΜΑΡΤΙ|ΑΠΡΙΛΙ|ΜΑΙ|ΙΟΥΝΙ|ΙΟΥΛΙ|"
    r"ΑΥΓΟΥΣΤ|ΣΕΠΤΕΜΒΡΙ|ΟΚΤΩΒΡΙ|ΝΟΕΜΒΡΙ|ΔΕΚΕΜΒΡΙ)\w*\s+(?:ΤΟΥ\s+)?(20\d{2})\b")
_YEAR_END = re.compile(r"\b(?:ΤΕΛΟΣ|ΤΕΛΗ)\s+(?:ΤΟΥ\s+)?(20\d{2})\b")


def parse_greek_date(s: str) -> str | None:
    """First date found in a snippet → ISO 'YYYY-MM-DD', else None.
    Handles numeric dd/mm/yyyy, prose «18η Δεκεμβρίου 2021» and the
    year-end idiom «έως τέλος 2024» (→ 31 December)."""
    f = _norm(s)
    m = _NUMERIC_DATE.search(f)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = _PROSE_DATE.search(f)
    if m:
        return f"{int(m.group(3)):04d}-{_MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = _YEAR_END.search(f)
    if m:
        return f"{int(m.group(1)):04d}-12-31"
    return None


# --------------------------------------------------------------------------
# Document windows

def _fold_keep_len(text: str) -> str:
    """Length-preserving accent-stripping uppercase (indices stay valid)."""
    return "".join(unicodedata.normalize("NFD", c)[0].upper() for c in text)


# The operative verb is sometimes letter-spaced («Α π ο φ α σ ί ζ ο υ μ ε»).
_OPERATIVE = re.compile("|".join(
    "".join(ch + r"\s?" for ch in word)
    for word in ("ΑΠΟΦΑΣΙΖΟΥΜΕ", "ΠΙΣΤΟΠΟΙΟΥΜΕ", "ΑΝΑΚΑΛΟΥΜΕ",
                 "ΤΡΟΠΟΠΟΙΟΥΜΕ")))


def operative_window(text: str, chars: int = 2800) -> str:
    """The decision's operative part — from «Αποφασίζουμε» (or
    ΠΙΣΤΟΠΟΙΟΥΜΕ/ΑΝΑΚΑΛΟΥΜΕ) onward; the whole tail if no anchor found."""
    m = _OPERATIVE.search(_fold_keep_len(text))
    start = m.start() if m else max(0, len(text) - chars)
    return text[start:start + chars]


def pros_block(text: str, lines: int = 14) -> str:
    """The ΠΡΟΣ: header block (recipient company name + postal address)."""
    all_lines = text.splitlines()
    for i, line in enumerate(all_lines[:120]):
        if re.search(r"\bΠΡΟΣ\s*[::]", line):
            return "\n".join(all_lines[i:i + lines])
    return ""


_DEADLINE_STEMS = ("ΚΑΤΑΛΗΚΤΙΚ", "ΠΡΟΘΕΣΜΙΑ", "ΔΙΑΡΚΕΙΑ", "ΠΑΡΑΤΕΙΝ",
                   "ΠΑΡΑΤΑΣ", "ΙΣΧΥ")


def deadline_candidates(text: str, window: int = 170) -> list[tuple[str | None, str]]:
    """(iso_date_or_None, excerpt) for every passage that talks about the
    act's deadline/duration. Proposals for the curation file, nothing more."""
    out, seen = [], set()
    f_text = text
    for stem_m in re.finditer(
            r"[Κκ]αταληκτικ|[Ππ]ροθεσμ|[Δδ]ιάρκει|[Ππ]αρατείν|[Ππ]αράτασ|ισχύ",
            f_text):
        lo = max(0, stem_m.start() - 40)
        hi = min(len(f_text), stem_m.end() + window)
        excerpt = re.sub(r"\s+", " ", f_text[lo:hi]).strip()
        key = excerpt[:60]
        if key in seen:
            continue
        seen.add(key)
        out.append((parse_greek_date(excerpt), excerpt))
    return out
