"""Extract the per-contract μελέτη (study/planning) cost from contract text.

The corpus has exactly one canonical anchor for a priced study line — the
Άρθρο 4 «Συμβατικό Τίμημα» item «Κόστος εκπόνησης μελετών
(συμπεριλαμβανομένων των φακέλων ΣΑΥ-ΦΑΥ)», amounts net of ΦΠΑ — plus its
prose forms («…κόστος εκπόνησης μελέτης … 16.628,99 €», «…70.340,67€ το
κόστος εκπόνησης των μελετών…»). Nearest-amount picking is wrong in ~40%
of real layouts (validated on every cached occurrence), so the rules here
are layout-aware, in priority order:

  same_line   the anchor line itself carries the amount (immediately before
              the anchor in the ΑΠΕ prose form, else the line's last token)
  next_line   a following line that is ONLY an amount, skipping page-break
              watermarks («ΣΕΛ.5», «<ADAM> <date>») and the label's own
              continuation lines («φακέλων ΣΑΥ-ΦΑΥ:»)
  prev_line   the preceding line when it is a lone amount (the table
              layout that right-aligns the value above its label)

See DATA_DECISIONS.md 2026-07-26.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from khmdhs.payment_validator import _AMOUNT_TOKEN_RE, _digits


def fold(s: str) -> str:
    """Uppercase + strip accents (no homoglyph translation)."""
    s = unicodedata.normalize("NFD", s.upper())
    return "".join(c for c in s if not unicodedata.combining(c))


# «Κόστος εκπόνησης …» with «μελετ» on the same or the wrapped next line.
_ANCHOR = "ΚΟΣΤΟΣ ΕΚΠΟΝΗΣΗΣ"
_MELETI = "ΜΕΛΕΤ"
# Lines injected by pdftotext page breaks inside tables.
_WATERMARK = re.compile(r"^(ΣΕΛ\.?\s*\d+|\d{2}SYMV\d+.*|\d+)$")
_LONE_AMOUNT = re.compile(
    r"^\s*(" + _AMOUNT_TOKEN_RE.pattern + r")\s*€?\s*$")
# Allowed gap between an amount and a FOLLOWING anchor: the article
# construction of the prose/bullet forms («…€ το κόστος…», «…€, που αφορά
# στο κόστος…»), never a bare list separator.
_BEFORE_GAP = re.compile(
    r"^\s*€?\)?,?\s*(?:ΠΟΥ ΑΦΟΡΑ\s+)?(?:Σ?ΤΟ|Σ?ΤΗΝ?|Η|ΤΑ)\s*$")
# Words the label itself may contain between the anchor and its amount —
# an amount is only taken "after" the anchor if everything in between is
# label vocabulary (otherwise it belongs to another budget component).
_LABEL_VOCAB = re.compile(
    r"^(?:\s|[:().,·•–\-]|€|ΤΗΣ|ΤΩΝ|ΜΕΛΕΤΗΣ|ΜΕΛΕΤΩΝ|ΜΕΛΕΤΗ|"
    r"ΣΥΜΠΕΡΙΛΑΜΒΑΝΟΜΕΝΩΝ|ΣΥΜΠΕΡ\w*|ΦΑΚΕΛΩΝ|ΦΑΚΕΛΟΥ|ΣΑΥ|ΦΑΥ|ΚΑΙ)*")


@dataclass
class Hit:
    eur: float
    rule: str
    line_idx: int
    page: int
    excerpt: str


def _to_eur(token: str) -> float:
    return int(_digits(token)) / 100.0


def _page_of(lines: list[str], idx: int) -> int:
    return 1 + sum(line.count("\f") for line in lines[:idx])


def _excerpt(lines: list[str], idx: int) -> str:
    ctx = lines[max(0, idx - 1): idx + 3]
    return re.sub(r"\s+", " ", " ".join(ctx)).strip()[:300]


def _is_anchor(folded: list[str], i: int) -> bool:
    if _ANCHOR not in folded[i]:
        return False
    nxt = folded[i + 1] if i + 1 < len(folded) else ""
    return _MELETI in folded[i] or _MELETI in nxt[:40]


def _after_label_amount(lines: list[str], folded: list[str], i: int,
                        span: int) -> float | None:
    """The amount reachable from the anchor by traversing ONLY label
    vocabulary — the same-line table row (span=1) or the wrapped
    next-line row with page-break watermarks interleaved (span>1).
    Refuses amounts that belong to a different budget component
    (anything non-label in between)."""
    # Folding preserves length for Greek, so folded offsets map onto the
    # raw string.
    apos = fold(lines[i]).find(_ANCHOR)
    parts = [lines[i][apos + len(_ANCHOR):]]
    for j in range(i + 1, min(i + span, len(lines))):
        if folded[j] and _WATERMARK.match(folded[j]):
            continue
        parts.append(lines[j])
    joined = " ".join(parts)
    m = _LABEL_VOCAB.match(fold(joined))
    tok = _AMOUNT_TOKEN_RE.match(joined[m.end():])
    return _to_eur(tok.group()) if tok else None


def find_study_costs(text: str) -> list[Hit]:
    """All anchored study-cost amounts in a contract's pdftotext -layout
    text. Multiple hits (e.g. an ΑΠΕ quoting old and new breakdowns) are
    all returned — the caller decides whether they agree."""
    lines = text.split("\n")
    folded = [fold(ln).strip() for ln in lines]
    hits: list[Hit] = []
    for i, fl in enumerate(folded):
        if not _is_anchor(folded, i):
            continue
        hit = None

        # -- after_label (same line): amount following the anchor through
        #    label vocabulary only — tables A1 and the running prose.
        eur = _after_label_amount(lines, folded, i, span=1)
        if eur is not None:
            hit = Hit(eur, "after_label", i, _page_of(lines, i),
                      _excerpt(lines, i))

        # -- before_prose: the ΑΠΕ recital «…70.340,67€ το κόστος
        #    εκπόνησης…» and the bullet «Ποσό ύψους 10.898,51€, που αφορά
        #    στο κόστος εκπόνησης…» put the amount right BEFORE the
        #    anchor. The gap must be exactly the article construction —
        #    a bare «€, » or «€ : » gap means the amount belongs to the
        #    PREVIOUS component of a running list and is rejected.
        if hit is None:
            apos = fold(lines[i]).find(_ANCHOR)
            tokens = [t for t in _AMOUNT_TOKEN_RE.finditer(lines[i])
                      if 0 < apos - t.end() <= 26
                      and _BEFORE_GAP.match(fold(lines[i][t.end():apos]))]
            if tokens:
                hit = Hit(_to_eur(tokens[-1].group()), "before_prose", i,
                          _page_of(lines, i), _excerpt(lines, i))

        # -- prev_line: table layout that right-aligns the value on the
        #    line above its label. Tried BEFORE the wrapped forward scan so
        #    that amount-above-label tables never steal the NEXT row's
        #    value through the label's continuation line.
        if hit is None:
            for j in range(i - 1, max(-1, i - 4), -1):
                fj = folded[j]
                if not fj or _WATERMARK.match(fj):
                    continue
                m = _LONE_AMOUNT.match(lines[j])
                if m:
                    hit = Hit(_to_eur(m.group(1)), "prev_line", i,
                              _page_of(lines, i), _excerpt(lines, i))
                break

        # -- after_label (wrapped): the split table row that puts the
        #    amount between the label's two lines (A2), watermarks and all.
        if hit is None:
            eur = _after_label_amount(lines, folded, i, span=6)
            if eur is not None:
                hit = Hit(eur, "after_label_wrapped", i, _page_of(lines, i),
                          _excerpt(lines, i))

        if hit is not None:
            hits.append(hit)
    return hits


def meleti_windows(text: str, radius: int = 350, cap: int = 8) -> list[str]:
    """Compact windows around μελετ- mentions, for the small-model audit of
    contracts that have no priced anchor."""
    folded = fold(text)
    out, last_end = [], -1
    for m in re.finditer(_MELETI, folded):
        if m.start() < last_end:
            continue
        lo, hi = max(0, m.start() - radius), m.end() + radius
        out.append(re.sub(r"\s+", " ", text[lo:hi]).strip())
        last_end = hi
        if len(out) >= cap:
            break
    return out
