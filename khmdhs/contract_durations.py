"""Extract the contract's own stated ΠΡΟΘΕΣΜΙΑ from its signed text.

The ΚΗΜΔΗΣ record carries a duration field for 83 of the 246 in-scope
contracts and never says what the clock starts on. The signed contract says
both, in one sentence, and every in-scope contract reaches one (226 in its
own text, 20 only through its chain — an amendment's own PDF is a cover
note). DATA_DECISIONS 2026-08-19.

The sentence reads, with small variations:

    «Η συνολική προθεσμία ολοκλήρωσης του Έργου ορίζεται σε τρεις (3) μήνες
     από την υπογραφή της παρούσας σύμβασης»

Anchored on the WORDING, never on the article number: the same clause sits
under «Άρθρο 3 ΔΙΑΡΚΕΙΑ ΣΥΜΒΑΣΗΣ – ΠΡΟΘΕΣΜΙΕΣ» in some contracts and
«Άρθρο 7: ΤΟΠΟΣ ΚΑΙ ΧΡΟΝΟΣ ΕΚΤΕΛΕΣΗΣ ΤΗΣ ΣΥΜΒΑΣΗΣ» in others, and an
article-position probe over the corpus put 85 contracts under «άρθρο 4 της
παρούσας», which is a cross-reference inside prose, not a heading.

Nothing here writes to the database: `read()` proposes, a human decides,
and the verdicts live in a curated JSON (the study_costs shape).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


def fold(s: str) -> str:
    """Uppercase + strip accents (no homoglyph translation)."""
    s = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))


# Some phase-II PDFs render every accent as a SEPARATE vowel after the
# letter it belongs to: «ορίζεται» arrives as «οριέζεται», «μήνες» as
# «μηέ νες», «προθεσμιών» as «προθεσμιωέν». Folding strips the accent but
# not the extra letter, so a literal pattern matches nothing — 66 contracts
# read as «no deadline stated» purely because of the font. `loose()` builds
# a pattern tolerating one stray vowel and stray spaces after each letter,
# which is exactly the artefact and nothing wider.
_VOWELS = "ΑΕΗΙΟΥΩ"
_STRAY = r"[ΑΕΗΙΟΥΩ]?\s{0,2}"


def loose(word: str) -> str:
    """A regex matching `word` through the accent-as-a-letter artefact.

    The stray letter is allowed only AFTER A VOWEL, which is where the
    artefact puts it («ορι-έ-ζεται», «μη-έ-νες», «προθεσμιω-έ-ν»). Allowing
    it after any letter made «ρήτρα» match inside ordinary prose and threw
    away the works clause of every design-build contract.
    """
    out = []
    for ch in word.replace(" ", ""):
        out.append(re.escape(ch) + (_STRAY if ch in _VOWELS else r"\s{0,2}"))
    return "".join(out)


# The clause that states the deadline, most specific first. «ΔΙΑΡΚΕΙΑ» alone
# is NOT an anchor: «καθ' όλη τη διάρκεια της εκτέλεσης» is boilerplate in
# almost every contract (205 of 246 carry the word).
_ANCHORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("συνολική προθεσμία",
     re.compile(loose("ΣΥΝΟΛΙΚ") + r"\w{0,3}\s*" + loose("ΠΡΟΘΕΣΜΙ"))),
    ("προθεσμία περαίωσης/εκτέλεσης",
     re.compile(loose("ΠΡΟΘΕΣΜΙ") + r"\w{0,3}\s*(?:" + loose("ΠΕΡΑΙΩΣΗΣ") + "|"
                + loose("ΕΚΤΕΛΕΣΗΣ") + "|" + loose("ΟΛΟΚΛΗΡΩΣΗΣ") + "|"
                + loose("ΥΛΟΠΟΙΗΣΗΣ") + ")")),
    ("διάρκεια της σύμβασης",
     re.compile(loose("ΔΙΑΡΚΕΙΑ") + r"\s*(?:" + loose("ΤΗΣ") + r"\s*)?(?:"
                + loose("ΠΑΡΟΥΣΑΣ") + r"\s*)?" + loose("ΣΥΜΒΑΣΗΣ"))),
    ("χρόνος εκτέλεσης/παράδοσης",
     re.compile(loose("ΧΡΟΝΟΣ") + r"\s*(?:" + loose("ΕΚΤΕΛΕΣΗΣ") + "|"
                + loose("ΠΑΡΑΔΟΣΗΣ") + ")")),
)

# «ορίζεται σε τρεις (3) μήνες»: the digits in brackets are the safe read,
# the spelled-out numeral is the fallback (some contracts print only it).
_WORD_NUM = {
    "ΕΝΑ": 1, "ΕΝΑΣ": 1, "ΜΙΑ": 1, "ΔΥΟ": 2, "ΤΡΕΙΣ": 3, "ΤΡΙΑ": 3,
    "ΤΕΣΣΕΡΙΣ": 4, "ΤΕΣΣΕΡΑ": 4, "ΠΕΝΤΕ": 5, "ΕΞΙ": 6, "ΕΠΤΑ": 7, "ΕΦΤΑ": 7,
    "ΟΚΤΩ": 8, "ΟΧΤΩ": 8, "ΕΝΝΕΑ": 9, "ΕΝΝΙΑ": 9, "ΔΕΚΑ": 10, "ΕΝΤΕΚΑ": 11,
    "ΔΩΔΕΚΑ": 12, "ΔΕΚΑΤΡΕΙΣ": 13, "ΔΕΚΑΤΕΣΣΕΡΙΣ": 14, "ΔΕΚΑΠΕΝΤΕ": 15,
    "ΔΕΚΑΕΞΙ": 16, "ΔΕΚΑΕΠΤΑ": 17, "ΔΕΚΑΟΚΤΩ": 18, "ΔΕΚΑΕΝΝΕΑ": 19,
    "ΕΙΚΟΣΙ": 20, "ΤΡΙΑΝΤΑ": 30, "ΕΞΗΝΤΑ": 60, "ΕΝΕΝΗΝΤΑ": 90,
}
_PAREN_NUM = re.compile(r"\((\d{1,4})\)")
_BARE_NUM = re.compile(r"\b(\d{1,4})\b")
# Each unit must START a word: without the boundary the two-letter «ΕΤ»
# stem matched «ΜΕ ΤΗ ΛΗΞΗ» across the space and read as «2 years» on
# three contracts whose article says only when the deadlines start.
_UNITS: tuple[tuple[str, str], ...] = (
    ("months", r"\b" + loose("ΜΗΝ") + r"(?:ΕΣ|ΩΝ|ΑΣ|Α)"),
    ("days", r"\b" + loose("ΗΜΕΡ") + r"(?:ΕΣ|ΩΝ|ΑΣ|Α)"),
    ("years", r"\bΕΤ(?:ΟΣ|Η|ΩΝ)\b|\bΧΡΟΝΙ(?:Α|ΩΝ)\b"),
)

# What the clock starts on — the fact the registry field never carries.
# «από την ημερομηνία έναρξης αυτών», «από της υπογραφής», «αφότου …»
_FROM = r"(?:ΑΠΟ|ΑΦΟΤΟΥ)\s*(?:[Α-Ω]{1,12}\s+){0,3}"
# «έναρξη εργασιών» is tested BEFORE «υπογραφή», because the sentence that
# names both means the works' start.
_BASES: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Each is read from the «από …» TAIL that follows the number, and the
    # earliest one wins: a sentence naming both («…μήνες από την έναρξη των
    # εργασιών … που ορίζεται με την υπογραφή…») means the first.
    ("works_start", re.compile(_FROM + loose("ΕΝΑΡΞΗ") + "|" + _FROM + loose("ΕΓΚΑΤΑΣΤΑΣΗ"))),
    ("signature", re.compile(_FROM + loose("ΥΠΟΓΡΑΦΗ"))),
    ("publication", re.compile(_FROM + loose("ΑΝΑΡΤΗΣΗ") + "|" + _FROM + loose("ΚΑΤΑΧΩΡΗΣΗ")
                               + "|" + _FROM + loose("ΔΗΜΟΣΙΕΥΣΗ"))),
    ("protocol", re.compile(_FROM + loose("ΠΡΩΤΟΚΟΛΛΟΥ"))),
)

# The clause must DEFINE the deadline. Without this the anchor also matches
# the penalty article — «σε περίπτωση υπέρβασης της συνολικής προθεσμίας …
# ποινική ρήτρα ίση με δεκαπέντε τοις εκατό (15%) … ανά ημέρα» — which read
# as «15 days» on 65 contracts.
_DEFINE = re.compile("|".join(loose(w) for w in (
    "ΟΡΙΖΕΤΑΙ", "ΟΡΙΖΟΝΤΑΙ", "ΟΡΙΣΤΗΚΕ", "ΑΝΕΡΧΕΤΑΙ", "ΚΑΘΟΡΙΖΕΤΑΙ", "ΕΙΝΑΙ")))
_REJECT = re.compile("|".join(loose(w) for w in (
    "ΠΟΙΝΙΚ", "ΡΗΤΡΑ", "ΤΟΙΣ ΕΚΑΤΟ", "ΥΠΕΡΒΑΣ", "ΚΑΘΥΣΤΕΡΗΣ", "ΕΓΓΥΗΤΙΚ")))
# a percentage between the anchor and the unit means a penalty rate, not a
# deadline — but «ΦΠΑ 24%» sits in the paragraph BEFORE «Άρθρο 3 Διάρκεια
# Σύμβασης» in 16 contracts, so the sign is tested on the head only
_REJECT_HEAD = re.compile(_REJECT.pattern + "|%")
# WHAT the deadline is for: a design-build contract states one for the
# μελέτη and one for the έργο, and those are different facts.
_SUBJECT: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("study", re.compile(loose("ΜΕΛΕΤΗΣ") + "|" + loose("ΜΕΛΕΤΩΝ"))),
    ("works", re.compile(loose("ΕΡΓΟΥ") + "|" + loose("ΕΡΓΑΣΙΩΝ") + "|"
                         + loose("ΣΥΜΒΑΣΗΣ"))),
)
# a sentence end: a full stop before a capital, but not inside «ν. 4412»,
# «αρ. 16» or a date like «30.03.2026»
_SENT_END = re.compile(r"(?<![Α-Ω0-9])\.\s+(?=[Α-Ω])")

# The window read after the anchor. 320 chars covers the clause and the
# «από …» tail; going wider starts eating the NEXT article's sentence.
_WINDOW = 320


@dataclass
class DurationRead:
    """One proposal — never a verdict."""
    n: int | None = None
    unit: str | None = None            # months | days | years
    basis: str | None = None           # signature | works_start | …
    anchor: str | None = None          # which wording matched
    subject: str | None = None         # works | study — a design-build
                                       # contract states one of each
    excerpt: str = ""                  # verbatim, from the ORIGINAL text
    source: str | None = None          # 'pdf' | 'chain:<ΑΔΑΜ>'
    notes: list[str] = field(default_factory=list)

    @property
    def days(self) -> int | None:
        if self.n is None:
            return None
        if self.unit == "days":
            return self.n
        if self.unit == "years":
            return self.n * 365
        if self.unit == "months":
            return round(self.n * 30.44)
        return None


def _excerpt(text: str, start: int, stop: int) -> str:
    """A window cut at word boundaries and marked where it is cut."""
    head, tail = start > 0, stop < len(text)
    frag = text[start:stop]
    if head:
        cut = frag.find(" ")
        if 0 <= cut <= 20:
            frag = frag[cut + 1:]
    if tail:
        cut = frag.rfind(" ")
        if cut > len(frag) - 30:
            frag = frag[:cut]
    return ("… " if head else "") + " ".join(frag.split()) + (" …" if tail else "")


def fold_map(text: str) -> tuple[str, list[int]]:
    """Fold, and keep a map from every folded character to its source index.

    `str.upper()` is not length-preserving on every character a PDF can
    carry, and where it grew the string the excerpts fell back to the folded
    (uppercase) form — evidence quotes that no longer looked like the
    document. With the map the match offsets always come home.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(text):
        piece = "".join(c for c in unicodedata.normalize("NFD", ch.upper())
                        if not unicodedata.combining(c))
        for c in piece:
            out.append(c)
            idx.append(i)
    idx.append(len(text))
    return "".join(out), idx


def read(text: str | None) -> DurationRead | None:
    """Read the deadline clause out of ONE document's text, or None.

    Every candidate clause is collected and the one about the ΕΡΓΟ wins: a
    design-build contract also states «ο χρόνος παράδοσης της Μελέτης
    ορίζεται σε είκοσι (20) ημερολογιακές ημέρες», which is true and is not
    the contract's deadline. A study-only read is returned marked.
    """
    if not text:
        return None
    flat = re.sub(r"[ \t]+", " ", text)
    up, idx = fold_map(flat)
    found: list[DurationRead] = []
    for name, rx in _ANCHORS:
        for m in rx.finditer(up):
            win = up[m.end(): m.end() + _WINDOW]
            # one sentence only — the next one is a different statement
            end = _SENT_END.search(win)
            if end:
                win = win[:end.start()]
            if _REJECT.search(up[max(0, m.start() - 90): m.start()]):
                continue          # «σε περίπτωση υπέρβασης της …»
            if not _DEFINE.search(win):
                continue
            out = DurationRead(anchor=name)
            # unit first: it is what makes a number a duration
            unit_at = None
            for unit, upat in _UNITS:
                um = re.search(upat, win)
                if um and (unit_at is None or um.start() < unit_at):
                    out.unit, unit_at = unit, um.start()
            if out.unit is None:
                continue
            head = win[:unit_at]
            # the REJECT test belongs to the defining part only: the rest of
            # the sentence routinely goes on about καθυστερήσεις and ρήτρες
            # without changing what the deadline is
            if _REJECT_HEAD.search(head):
                continue
            pm = list(_PAREN_NUM.finditer(head))
            if pm:
                out.n = int(pm[-1].group(1))
            else:
                words = re.findall(r"[Α-Ω]+", head)
                for w in reversed(words[-4:]):
                    if w in _WORD_NUM:
                        out.n = _WORD_NUM[w]
                        out.notes.append("number spelled out, no digits")
                        break
                if out.n is None:
                    bm = list(_BARE_NUM.finditer(head))
                    if bm:
                        out.n = int(bm[-1].group(1))
                        out.notes.append("bare number, not in brackets")
            if out.n is None:
                continue
            tail = win[unit_at:]
            at = None
            for basis, bpat in _BASES:
                bm = bpat.search(tail)
                if bm and (at is None or bm.start() < at):
                    out.basis, at = basis, bm.start()
            for subject, spat in _SUBJECT:
                if spat.search(win[:unit_at + 40]):
                    out.subject = subject
                    break
            out.excerpt = _excerpt(flat, idx[max(0, m.start() - 20)],
                                   idx[min(len(idx) - 1, m.end() + len(win))])
            found.append(out)
    if not found:
        return None
    for got in found:
        if got.subject != "study":
            return got
    got = found[0]
    got.notes.append("the only clause found is about the μελέτη, not the works")
    return got


# Three «άμεσης διαχείρισης» contracts state no duration at all: their time
# is a SEASON — «Αντιπυρική Περίοδος: Είναι η αντιπυρική περίοδος του έτους
# 2024, όπως αυτή εκάστοτε καθορίζεται…». That is a different kind of answer
# and is reported as itself, not as a blank.
_SEASON = re.compile(loose("ΑΝΤΙΠΥΡΙΚΗ") + r"\s*" + loose("ΠΕΡΙΟΔΟ")
                     + r"[^.]{0,80}?" + loose("ΕΤΟΥΣ") + r"\s*(\d{4})")


def fire_season(text: str | None) -> int | None:
    """The year whose fire season IS the contract's deadline, or None."""
    if not text:
        return None
    up, _ = fold_map(re.sub(r"[ 	]+", " ", text))
    m = _SEASON.search(up)
    return int(m.group(1)) if m else None


def read_chain(texts: list[tuple[str, str]]) -> DurationRead | None:
    """Read the chain: the record's own text first, then its ancestors.

    46 of the in-scope contracts are amendments whose own PDF is a short
    cover note; the deadline they run under is stated in the σύμβαση they
    amend, and `source` records which document was read.
    """
    for ref, text in texts:
        got = read(text)
        if got is not None:
            got.source = ref          # WHICH document said it
            return got
    return None
