"""Pure classification/extraction for the «Αρωγή πυροπλήκτων» dataset.

Sources are the ΓΔΑΕΦΚ per-building acts on Diavgeia (fires ≥2021; see
DATA_DECISIONS 2026-08-03). Everything here is deterministic text work on
the act subject + pdftotext output — no I/O. Amount rules were accepted
only after a hand audit against act PDFs (harvest_arogi.py audit stage).

Privacy: none of these helpers extract or return owner names.
"""
from __future__ import annotations

import re
import unicodedata


def fold(s: str | None) -> str:
    """Uppercase + strip accents (NFD) for keyword matching."""
    nfd = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in nfd if not unicodedata.combining(c))


def parse_greek_amount(s: str) -> float | None:
    """'1.234,56' → 1234.56. Registry keying also uses all-dots amounts
    ('65.982.92' = 65,982.92; audit 2026-08-03): with no comma, a final
    dot followed by exactly two digits is the decimal separator."""
    t = s.strip()
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})*\.\d{2}", t):
        head, dec = t.rsplit(".", 1)
        t = head.replace(".", "") + "." + dec
    else:
        t = t.replace(".", "")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


# ------------------------------------------------------------------ kinds

def classify_kind(subject: str | None) -> str:
    """Act family from the subject line (checked most-specific first)."""
    s = fold(subject)
    if "ΟΡΙΟΘΕΤΗΣ" in s:
        return "oriothetisi"
    if "ΒΕΒΑΙΩΣΗ ΠΕΡΑΙΩΣ" in s or "ΠΕΡΑΙΩΣΗΣ ΕΡΓΑΣΙΩΝ" in s:
        return "completion"
    if "ΒΕΒΑΙΩΣΗ ΠΡΟΟΔΟΥ" in s or "ΔΟΣΗΣ" in s or "ΔΟΣΕΩΝ" in s:
        return "progress_dose"
    if "ΑΥΤΟΣΤΕΓΑΣ" in s:
        return "autostegasi"
    if "ΑΝΑΚΑΤΑΣΚΕΥ" in s and ("ΑΔΕΙΑ" in s or "ΕΓΚΡΙΣΗ" in s):
        return "reconstruction"
    if "ΑΔΕΙΑ ΕΠΙΣΚΕΥΗΣ" in s:
        return "repair_permit"
    if "ΣΤΕΓΑΣΤΙΚ" in s and "ΣΥΝΔΡΟΜ" in s:
        return "ss_other"
    return "other"


# ------------------------------------------------------- fire citations

_MONTHS = {
    "ΙΑΝΟΥΑΡΙΟΥ": 1, "ΦΕΒΡΟΥΑΡΙΟΥ": 2, "ΜΑΡΤΙΟΥ": 3, "ΑΠΡΙΛΙΟΥ": 4,
    "ΜΑΙΟΥ": 5, "ΙΟΥΝΙΟΥ": 6, "ΙΟΥΛΙΟΥ": 7, "ΑΥΓΟΥΣΤΟΥ": 8,
    "ΣΕΠΤΕΜΒΡΙΟΥ": 9, "ΟΚΤΩΒΡΙΟΥ": 10, "ΝΟΕΜΒΡΙΟΥ": 11, "ΔΕΚΕΜΒΡΙΟΥ": 12,
}
_MONTH_ALT = ("(?:ΙΑΝΟΥΑΡΙΟΥ|ΦΕΒΡΟΥΑΡΙΟΥ|ΜΑΡΤΙΟΥ|ΑΠΡΙΛΙΟΥ|ΜΑΙΟΥ|ΙΟΥΝΙΟΥ|"
              "ΙΟΥΛΙΟΥ|ΑΥΓΟΥΣΤΟΥ|ΣΕΠΤΕΜΒΡΙΟΥ|ΟΚΤΩΒΡΙΟΥ|ΝΟΕΜΒΡΙΟΥ|"
              "ΔΕΚΕΜΒΡΙΟΥ)")
# «πυρκαγιά της 3ης Αυγούστου 2021», «πυρκαγιές της 23ης και 24ης Ιουλίου
# 2018», «πυρκαγιών του Ιουλίου/Αυγούστου 2021», the three-month letterhead
# «ΠΥΡΚΑΓΙΕΣ ΙΟΥΝΙΟΥ, ΙΟΥΛΙΟΥ ΚΑΙ ΑΥΓΟΥΣΤΟΥ 2025» (audit 2026-08-03)
_FIRE_RX = re.compile(
    r"ΠΥΡΚΑΓΙ\w{1,3}\s+(?:ΤΗΣ|ΤΟΥ|ΤΩΝ)?\s*"
    r"((?:\d{1,2}\s*ΗΣ?\s*(?:ΚΑΙ\s+\d{1,2}\s*ΗΣ?\s*)?)?"
    + _MONTH_ALT +
    r"(?:\s*(?:[,/&]|ΚΑΙ)\s*(?:ΚΑΙ\s+)?" + _MONTH_ALT + r"){0,4}"
    r"\s*(?:ΤΟΥ\s+)?(\d{4}))")
# «ΠΥΡΚΑΓΙΑ ΤΟΥ 2018», «ΠΥΡΚΑΓΙΕΣ ΤΟΥ 2007» — year only, no month
_FIRE_YEAR_RX = re.compile(
    r"ΠΥΡΚΑΓΙ\w{1,3}\s+(?:ΤΗΣ|ΤΟΥ|ΤΩΝ|ΕΤΟΥΣ)\s*(?:ΕΤΟΥΣ\s+)?(\d{4})")
# «πυρκαγιά της 3/8/2021» — numeric date
_FIRE_NUM_RX = re.compile(
    r"ΠΥΡΚΑΓΙ\w{1,3}\s+ΤΗΣ\s+\d{1,2}[./-](\d{1,2})[./-](\d{4})")


def fire_citations(text: str) -> list[dict]:
    """Every fire (month, year) the act cites, with a verbatim excerpt.

    Returns [{'year': int, 'months': [int, …], 'excerpt': str}] — day-level
    detail stays inside the excerpt; matching against the curated fire
    registry keys on (year, month) + municipality.
    """
    flat = re.sub(r"\s+", " ", fold(text))
    out, seen = [], set()

    def add(year, months, start, end):
        key = (year, tuple(months))
        if key in seen:
            return
        seen.add(key)
        out.append({"year": year, "months": months,
                    "excerpt": flat[max(0, start - 40):end + 40]})

    for m in _FIRE_RX.finditer(flat):
        months = sorted({v for k, v in _MONTHS.items() if k in m.group(1)})
        add(int(m.group(2)), months, m.start(), m.end())
    for m in _FIRE_NUM_RX.finditer(flat):
        mo = int(m.group(1))
        if 1 <= mo <= 12:
            add(int(m.group(2)), [mo], m.start(), m.end())
    if not out:                 # year-only fallback (weakest signal)
        for m in _FIRE_YEAR_RX.finditer(flat):
            y = int(m.group(1))
            if 1990 < y < 2100:
                add(y, [], m.start(), m.end())
    return out


# ------------------------------------------------------------- amounts

# The Σ.Σ. amounts are hash-delimited in the acts: «#12.095,74€# #9.676,59€#
# #2.419,15€#» = (total, ΔΚΑ, δάνειο). pdftotext interleaves the table's
# column headers, so the HASH SEQUENCE — not the phrase — is the anchor;
# a 3-amount run must satisfy total ≈ ΔΚΑ + δάνειο (audit 2026-08-03).
_HASH_AMT_RX = re.compile(r"#\s*([\d][\d.,]*)\s*€?\s*#")
# labelled amounts (dose acts): «ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ : … 40.000,00€» /
# amount-first variant «(18.099,72 €), ως ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ»
_DKA_AFTER_RX = re.compile(
    r"ΔΩΡΕΑΝ\s+ΚΡΑΤΙΚ\w+\s+ΑΡΩΓ\w*\s*:?[^€#]{0,80}?([\d][\d.,]*)\s*€")
_LOAN_AFTER_RX = re.compile(
    r"ΑΤΟΚ\w+\s+ΔΑΝΕΙ\w*\s*:?[^€#]{0,80}?([\d][\d.,]*)\s*€")
_DKA_BEFORE_RX = re.compile(
    r"([\d][\d.,]*)\s*€[^€]{0,80}?ΔΩΡΕΑΝ\s+ΚΡΑΤΙΚ\w+\s+ΑΡΩΓ")
_LOAN_BEFORE_RX = re.compile(
    r"([\d][\d.,]*)\s*€[^€]{0,80}?ΑΤΟΚ\w+\s+ΔΑΝΕΙ")


def _validated_triple(flat: str):
    """The first run of 3 consecutive hash-amounts where v0 = v1 + v2
    (±€1, v0 > 0) — the arithmetic IS the Σ.Σ.-table signature; documents
    print ΠΡΟΫΠΟΛΟΓΙΣΜΟΣ hashes and συμψηφισμός tables around it (audit
    2026-08-03, act ΨΜΔ346ΝΠΙΘ-ΖΦ5)."""
    ms = list(_HASH_AMT_RX.finditer(flat))
    for i in range(len(ms) - 2):
        vals = [parse_greek_amount(ms[j].group(1)) for j in (i, i + 1, i + 2)]
        if None in vals or not vals[0]:
            continue
        if abs(vals[0] - (vals[1] + vals[2])) <= 1.0:
            return vals, ms[i], ms[i + 2]
    return None, None, None


def ss_total(text: str) -> tuple[float | None, str | None]:
    """(Σ.Σ. total €, excerpt): the arithmetic-validated hash triple
    (total, ΔΚΑ, δάνειο) anywhere in the act; else the first hash amount
    inside the window after the Σ.Σ.-table anchor phrase; else None."""
    flat = re.sub(r"\s+", " ", fold(text))
    vals, m0, m2 = _validated_triple(flat)
    if vals:
        return vals[0], flat[max(0, m0.start() - 160):m2.end() + 10]
    anchor = flat.find("ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ)")
    hay = flat[anchor:anchor + 400] if anchor >= 0 else flat
    ms = list(_HASH_AMT_RX.finditer(hay))
    if not ms:
        return None, None
    lo = max(0, ms[0].start() - 160)
    return (parse_greek_amount(ms[0].group(1)),
            hay[lo:ms[0].end() + 10])


def dka_loan(text: str) -> tuple[float | None, float | None]:
    """(δωρεάν-κρατική-αρωγή €, άτοκο-δάνειο €) where the act states them.

    The arithmetic-validated hash triple first, then labelled amounts in
    either direction. «ΑΤΟΚΟ ΔΑΝΕΙΟ: ΔΕΝ ΕΠΙΘΥΜΟΥΝ» yields None for the
    loan — never a mis-grabbed neighbouring figure."""
    flat = re.sub(r"\s+", " ", fold(text))
    vals, _, _ = _validated_triple(flat)
    if vals:
        return vals[1], vals[2]
    dka = _DKA_AFTER_RX.search(flat) or _DKA_BEFORE_RX.search(flat)
    loan = _LOAN_AFTER_RX.search(flat) or _LOAN_BEFORE_RX.search(flat)
    return (parse_greek_amount(dka.group(1)) if dka else None,
            parse_greek_amount(loan.group(1)) if loan else None)


# ------------------------------------------------------------ case keys

# The shared file identifier is the PERMIT NUMBER, e.g. «ΑΡ. ΑΔΕΙΑΣ:
# 8/ΠΥΡΑΝΑΤ21/Τ.Α.Ε.Φ.Κ.-Α.Α.», also cited by follow-ups/τροποποιητικές
# as «της 920/ΠΥΡ.2018/Τ.Α.Ε.Φ.Κ.-Α.Α.» (audit 2026-08-03). Normalised by
# stripping dots/spaces from the office suffix.
_PERMIT_RX = re.compile(
    r"(\d{1,5})\s*/\s*(ΠΥΡ[Α-Ω0-9.]{0,12}?)\s*/\s*"
    r"([ΤΔΑ][.Α-Ω\-]{2,20})")
# fallback: the ΓΔΑΕΦΚ Α.Κ. file id «Α.Κ. 1234/21»
_AK_RX = re.compile(r"\bΑ\.?Κ\.?\s*/?\s*(\d{1,5}\s*/\s*\d{1,4})")


def case_key(text: str) -> str | None:
    """The aid-file identifier follow-up acts share with their permit:
    the permit number (N/ΠΥΡ…/office) first, else the Α.Κ. file id.
    None when the act states neither."""
    flat = re.sub(r"\s+", " ", fold(text))
    m = _PERMIT_RX.search(flat)
    if m:
        office = re.sub(r"[.\s]", "", m.group(3))
        pyr = re.sub(r"[.\s]", "", m.group(2))
        return f"{m.group(1)}/{pyr}/{office}"
    m = _AK_RX.search(flat)
    if m:
        return "ΑΚ" + re.sub(r"\s+", "", m.group(1))
    return None


# ----------------------------------------------------------- ΑΔΑ citations

# prefixes are 7–10 chars (org codes 3–6 chars; the old exactly-{10}
# pattern missed ΑΠΔ/δήμος citations)
_ADA_RX = re.compile(r"\b([0-9Α-ΩA-Z]{7,12}-[0-9Α-ΩA-Z]{3})\b")


def cited_adas(text: str, self_ada: str | None = None) -> list[str]:
    """Diavgeia ΑΔΑs cited in the act body (excluding its own)."""
    out = []
    for m in _ADA_RX.finditer(unicodedata.normalize("NFC", text)):
        ada = m.group(1)
        if ada != self_ada and ada not in out:
            out.append(ada)
    return out
