"""Classify contracts into Anti-nero programme scopes.

The dataset (xlsx export + Diavgeia-sourced supplement) mixes genuine
Anti-nero contracts with routine forest-road maintenance, sibling
programmes and programme-management umbrella contracts. This module is
the single source of truth for telling them apart.

Scope values:
  antinero_i / _ii / _iii / _iv / _2026  execution contracts per phase
  antinero_unknown_phase                 Anti-nero evidence, phase unclear
  antinero_umbrella                      ΥΠΕΝ↔ΤΑΙΠΕΔ/ΕΕΣΥΠ pass-through frameworks
  antinero_support                       programme admin (legal/consulting) services
  antinero_esa                           reforestation/nurseries component of (Antinero II)
  antinero_restoration                   αντιδιαβρωτικά/αντιπλημμυρικά component of (Antinero II)
  non_antinero                           no Anti-nero evidence (routine works etc.)

The reforestation and restoration contracts are IN scope: their own
contract documents declare membership in the Antinero project — RRF
Action 16849 «Εθνικό σχέδιο αναδάσωσης, πρόγραμμα αποκατάστασης και
πρόληψης («antiNERO»), αντιδιαβρωτικά και αντιπλημμυρικά μέτρα», ΠΔΕ
project «…ΠΡΟΓΡΑΜΜΑ ΠΡΟΣΤΑΣΙΑΣ ΔΑΣΩΝ (Antinero II) - ΑΝΤΙΔΙΑΒΡΩΤΙΚΑ &
ΑΝΤΙΠΛΗΜΜΥΡΙΚΑ ΕΡΓΑ» (ΟΠΣ ΤΑ 5201358). They keep distinct scope values
so the firebreak phases stay separable in the analytics.

Only the execution scopes (+ unknown_phase) count as "in scope" for the
analytics UI. Umbrella and support rows stay in the DB for detail pages
but are excluded from every aggregate.

Titles in KHMDHS freely mix Greek and Latin homoglyphs ("ANTINERO IΙ"
with a Greek iota is real data), so phase detection runs on a
homoglyph-normalised uppercase copy of the title.
"""
from __future__ import annotations

import unicodedata
from typing import NamedTuple

# Contractors that are programme-management vehicles, not executors.
# Kept in sync with webui.queries.EXCLUDED_CONTRACTOR_VATS.
UMBRELLA_VATS = frozenset({"997104555", "997471299"})  # Ε.Ε.ΣΥ.Π. / ΤΑΙΠΕΔ

# Funding codes observed on verified Anti-nero contracts.
FUND_ANTINERO_I = "2022ΤΑ07500000"      # 07.02.2022 ΥΠΕΝ-ΤΑΙΠΕΔ framework
FUND_ANTINERO_LATER = ("2021ΤΑ07500002", "2023ΤΑ07500012")

# Funding refs that positively identify pre-programme routine works.
NON_ANTINERO_FUND_REFS = ("584", "ΠΡΑΣΙΝΟ ΤΑΜΕΙΟ")

IN_SCOPE = frozenset({
    "antinero_i", "antinero_ii", "antinero_iii", "antinero_iv",
    "antinero_2026", "antinero_unknown_phase",
    "antinero_esa", "antinero_restoration",
})

# Greek capitals that are visually identical to Latin capitals. Applied
# to uppercase titles before searching for "ANTINERO ..." tokens.
_HOMOGLYPHS = str.maketrans("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX")


class ScopeResult(NamedTuple):
    scope: str
    basis: str


def normalize_title(title: str | None) -> str:
    """Uppercase + Greek→Latin homoglyph translation, for token matching.

    The fully-Greek spelling "ΑΝΤΙΝΕΡΟ" is mapped to "ANTINERO" as a word
    first, because its Ρ is a phonetic R — the general homoglyph table maps
    Greek Ρ to the visually identical Latin P.
    """
    upper = (title or "").upper().replace("ΑΝΤΙΝΕΡΟ", "ANTINERO")
    return upper.translate(_HOMOGLYPHS)


def _strip_accents(s: str) -> str:
    """Drop combining accents: Python uppercases 'ί' to accented 'Ί', which
    breaks plain substring matching ('Φυτωρίων'.upper() != …ΦΥΤΩΡΙΩΝ…)."""
    decomposed = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _phase_from_title(norm: str) -> str | None:
    """Detect the Anti-nero phase named in a normalised title, or None."""
    if "ANTINERO" not in norm:
        return None
    # Order matters: 2026 before 2, IV before I, III before II before I.
    if "ANTINERO 2026" in norm:
        return "antinero_2026"
    if "ANTINERO IV" in norm or "ANTINERO 4" in norm:
        return "antinero_iv"
    if "ANTINERO III" in norm or "ANTINERO 3" in norm:
        return "antinero_iii"
    if "ANTINERO II" in norm or "ANTINERO 2" in norm:
        return "antinero_ii"
    if "ANTINERO I" in norm or "ANTINERO 1" in norm:
        return "antinero_i"
    return "antinero_unknown_phase"


def classify(row: dict, overrides: dict[str, str] | None = None) -> ScopeResult:
    """Classify one contract.

    `row` needs: reference_number, title, public_funding_ref,
    public_funding_ref_num, contractor_vats (iterable of VAT strings).
    `overrides` maps reference_number → scope for curated entries
    (khmdhs/data/antinero_supplement.json); they win over every rule.
    """
    ref = (row.get("reference_number") or "").strip()
    if overrides and ref in overrides:
        return ScopeResult(overrides[ref], "curated:antinero_supplement")

    vats = {(v or "").strip() for v in row.get("contractor_vats") or ()}
    if vats & UMBRELLA_VATS:
        return ScopeResult("antinero_umbrella", "contractor:state_vehicle")

    raw_upper = (row.get("title") or "").upper()
    norm = normalize_title(row.get("title"))

    fund_num = (row.get("public_funding_ref_num") or "").strip()
    fund_ref = (row.get("public_funding_ref") or "").strip()

    if "ANTINERO" in norm:
        # Support-services contracts are branded ANTINERO but are not works.
        if "ΥΠΟΣΤ" in raw_upper and ("ΝΟΜ" in raw_upper or "ΣΥΜΒΟΥΛ" in raw_upper):
            return ScopeResult("antinero_support", "title:support_services")
        phase = _phase_from_title(norm)
        # The II/III numerals are typed with mixed Greek/Latin iotas and are
        # unreliable: the Jun-Oct 2023 batch is titled "ANTINERO IIΙ" (3
        # iotas) yet ΥΠΕΝ's own Diavgeia decisions call it ANTINERO II, while
        # the visually identical Jan-Mar 2024 batch is genuinely III. The
        # funding code separates them cleanly, so within {II, III} the fund
        # is authoritative when present.
        if phase in ("antinero_ii", "antinero_iii"):
            if fund_num.startswith("2021ΤΑ07500002"):
                return ScopeResult("antinero_ii", "title+fund:2021ΤΑ07500002")
            if fund_num.startswith("2023ΤΑ07500012"):
                return ScopeResult("antinero_iii", "title+fund:2023ΤΑ07500012")
        return ScopeResult(phase, "title:phase_label")

    # Named components of the (Antinero II) project, checked before the
    # fund rules so they keep distinct scope values. Their contract PDFs
    # declare membership in RRF Action 16849 «…(«antiNERO»)…» / ΠΔΕ
    # «…(Antinero II) - ΑΝΤΙΔΙΑΒΡΩΤΙΚΑ & ΑΝΤΙΠΛΗΜΜΥΡΙΚΑ ΕΡΓΑ».
    # Short stems on purpose — titles abbreviate ("αντιδιαβρ. αντιπλ.").
    plain = _strip_accents(raw_upper)
    if "ΑΝΑΔΑΣΩΣ" in plain or "ΦΥΤΩΡΙ" in plain:
        return ScopeResult("antinero_esa", "title+project:(Antinero II) ΕΣΑ/φυτώρια")
    if "ΑΝΤΙΔΙΑΒΡ" in plain or "ΑΝΤΙΠΛΗΜ" in plain or "ΔΑΣΟΤΕΧΝΙΚ" in plain:
        return ScopeResult("antinero_restoration",
                           "title+project:(Antinero II) αντιδιαβρωτικά/αντιπλημμυρικά")

    if fund_num.startswith(FUND_ANTINERO_I):
        return ScopeResult("antinero_i", f"fund:{FUND_ANTINERO_I}")
    if fund_num.startswith(FUND_ANTINERO_LATER):
        return ScopeResult("antinero_unknown_phase", f"fund:{fund_num[:14]}")

    if fund_ref in NON_ANTINERO_FUND_REFS or "ΣΕ584" in fund_num:
        return ScopeResult("non_antinero", f"fund:{fund_ref or fund_num}")

    return ScopeResult("non_antinero", "no_antinero_evidence")
