"""ΔΑΣΕ (forest labour cooperative) contractor-name classifier.

Greek forest labour cooperatives (ν.4423/2016 ΔΑ.Σ.Ε., the older
«δασεργατικός συνεταιρισμός» naming, and the αναγκαστικοί ΑΔΣΕ) have no
legal-form field anywhere in KHMDHS and are not in ΓΕΜΗ (they keep their
own registry), so the ONLY classification signal is the free-text
contractor name. The regexes here PROPOSE; every distinct VAT is
human-reviewed into khmdhs/data/dase_contractors.json before its
contracts enter the final dataset (DATA_DECISIONS 2026-07-26).

Observed false positives that must classify "no": «ΚΕΝΤΡΟ ΔΙΑΣΚΕΔΑΣΕΩΣ»,
«ΕΥΑΓΓΕΛΟΣ ΛΕΙΒΑΔΑΣΕ» (ΔΑΣΕ as a word-interior substring).
"""
from __future__ import annotations

import re
import unicodedata


def fold(s: str) -> str:
    """Uppercase + strip accents."""
    s = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))


# Word-bounded Δ(.)Α(.)Σ(.)Ε(.) token — dot/space tolerant, but never a
# word-interior substring (ΔΙΑΣΚΕΔΑΣΕΩΣ, ΛΕΙΒΑΔΑΣΕ).
_DASE_TOKEN = re.compile(
    r"(?<![Α-ΩA-Z])Δ\.?\s?Α\.?\s?Σ\.?\s?Ε\.?(?![Α-ΩA-Z])")
# ΑΔΣΕ — αναγκαστικός δασικός συνεταιρισμός token.
_ADSE_TOKEN = re.compile(
    r"(?<![Α-ΩA-Z])Α\.?\s?Δ\.?\s?Σ\.?\s?Ε\.?(?![Α-ΩA-Z])")
# ΕΔΑΣΕ / ΟΔΑΣΕ — the Καλαμπάκα/Τρίκαλα forest-village cooperative naming
# (observed: ΕΔΑΣΕ Φλαμπουρεσίου/Γαρδικίου, ΣΤ΄ΕΔΑΣΕ Χρυσομηλιάς, ΟΔΑΣΕ
# Μηλιάς — καυσόξυλα/συστάδες works). Word-bounded, so ΛΕΙΒΑΔΑΣΕ stays out.
_EDASE_TOKEN = re.compile(
    r"(?<![Α-ΩA-Z])[ΕΟ]\.?\s?ΔΑ\.?\s?Σ\.?\s?Ε\.?(?![Α-ΩA-Z])")


def classify_name(name: str) -> tuple[str, str | None]:
    """Return (verdict, form): verdict 'dase' | 'review' | 'no'.

    form (when dase): 'dase' | 'adse' | 'daseragikos' — all are forest
    labour cooperatives; the tag just records the naming convention.
    """
    f = fold(name)
    if not f.strip():
        return "no", None
    has_syn = "ΣΥΝΕΤΑΙΡ" in f
    if "ΔΑΣΕΡΓΑΤ" in f:
        return "dase", "daseragikos"
    if has_syn and ("ΔΑΣΙΚ" in f or "ΔΑΣΟΠΟΝ" in f):
        form = "adse" if ("ΑΝΑΓΚΑΣΤΙΚ" in f or _ADSE_TOKEN.search(f)) else "dase"
        return "dase", form
    if _DASE_TOKEN.search(f):
        return "dase", "dase"
    if _ADSE_TOKEN.search(f):
        return "dase", "adse"
    if _EDASE_TOKEN.search(f):
        return "dase", "edase"
    if has_syn:
        # A cooperative, but not identifiably a forest one — human decides.
        return "review", None
    return "no", None
