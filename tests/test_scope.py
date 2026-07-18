"""Unit tests for the Anti-nero scope classifier (khmdhs.scope)."""
from khmdhs.scope import IN_SCOPE, classify, normalize_title


def row(**kw):
    base = {
        "reference_number": "22SYMV000000000",
        "title": None,
        "public_funding_ref": None,
        "public_funding_ref_num": None,
        "contractor_vats": ["123456789"],
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# Homoglyph normalisation — real KHMDHS titles mix Greek and Latin capitals
# ---------------------------------------------------------------------------

def test_normalize_greek_homoglyphs():
    # Greek Α Ν Τ Ι Ε Ρ Ο look identical to Latin but are different codepoints
    assert normalize_title("ΑΝΤΙΝΕΡΟ") == "ANTINERO"
    # '4Β ΤΟΥ ANTINERO IΙ' — Latin I followed by Greek Ι (real data,
    # 23SYMV011953055)
    assert "ANTINERO II" in normalize_title("1η ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΜΒΑΣΗΣ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 4Β ΤΟΥ ANTINERO IΙ")


def test_normalize_handles_none():
    assert normalize_title(None) == ""


# ---------------------------------------------------------------------------
# Phase detection from titles
# ---------------------------------------------------------------------------

def test_phase_iv():
    r = classify(row(title="ΥΛΟΤΟΜΙΕΣ ANTINERO IV ΔΧ ΘΕΣΣΑΛΟΝΙΚΗΣ"))
    assert r.scope == "antinero_iv"


def test_phase_2026_not_mistaken_for_2():
    r = classify(row(title="ΕΡΓΑΣΙΕΣ ANTINERO 2026 ΔΑΣ ΤΡΙΚΑΛΩΝ"))
    assert r.scope == "antinero_2026"


def test_phase_ii_greek_iotas():
    # 22SYMV011593395: 'ΤΟΥ ANTINERO ΙΙ' with two Greek iotas
    r = classify(row(title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 2Α ΤΟΥ ANTINERO ΙΙ"))
    assert r.scope == "antinero_ii"


# ---------------------------------------------------------------------------
# II vs III disambiguation by funding code (the 'IIΙ' mixed-glyph batches)
# ---------------------------------------------------------------------------

def test_mixed_glyph_iii_with_2021_fund_is_phase_ii():
    # Jun-Oct 2023 batch: titled 'ANTINERO IIΙ' (Latin II + Greek Ι = three
    # iotas) but ΥΠΕΝ's own Diavgeia decisions call these contracts
    # ANTINERO II; the II-era fund code decides.
    r = classify(row(
        title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 16Β ΤΟΥ ANTINERO IIΙ",
        public_funding_ref_num="2021ΤΑ07500002",
    ))
    assert r.scope == "antinero_ii"


def test_mixed_glyph_iii_with_2023_fund_is_phase_iii():
    # Jan-Mar 2024 batch: same glyph soup, but III-era fund code and the
    # Diavgeia completion decisions say ANTINERO III.
    r = classify(row(
        title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 29Α ΤΟΥ ANTINERO IIΙ",
        public_funding_ref_num="2023ΤΑ07500012",
    ))
    assert r.scope == "antinero_iii"


def test_pure_iii_without_fund_stays_iii():
    r = classify(row(title="ΣΥΜΒΑΣΗ ΠΡΟΓΡΑΜΜΑ ΠΡΟΣΤΑΣΙΑΣ ΔΑΣΩΝ ANTINERO III"))
    assert r.scope == "antinero_iii"


# ---------------------------------------------------------------------------
# Umbrella, support, Anti-nero I fund rule
# ---------------------------------------------------------------------------

def test_umbrella_vat_beats_title():
    r = classify(row(
        title="ΣΥΜΒΑΣΗ ΠΡΟΓΡΑΜΜΑ ΠΡΟΣΤΑΣΙΑΣ ΔΑΣΩΝ ANTINERO III",
        contractor_vats=["997471299"],  # ΤΑΙΠΕΔ
    ))
    assert r.scope == "antinero_umbrella"
    assert r.scope not in IN_SCOPE


def test_support_services():
    # 24SYMV015978850: legal-support services for the programme
    r = classify(row(
        title="ΣΥΜΒΑΣΗ ΠΑΡΟΧΗΣ ΥΠΟΣΤ.ΥΠΗΡ.ΑΠΟ ΕΞΩΤ.ΣΥΝ.ΓΙΑ ΤΗ ΝΟΜ.ΥΠΟΣΤ."
              "ΤΟΥ ΓΓΓΔ ΓΙΑ ΤΗΝ ΕΠΕΞ&ΤΕΛ.ΔΙΑ.ΕΠΑ ANTINERO",
    ))
    assert r.scope == "antinero_support"
    assert r.scope not in IN_SCOPE


def test_antinero_i_by_fund_code():
    # The Anti-nero I execution contracts carry no ANTINERO in the title;
    # the 07.02.2022 framework's fund code identifies them.
    r = classify(row(
        title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 3.Α",
        public_funding_ref_num="2022ΤΑ07500000",
    ))
    assert r.scope == "antinero_i"


# ---------------------------------------------------------------------------
# Non-Anti-nero
# ---------------------------------------------------------------------------

def test_routine_sae584():
    r = classify(row(
        title="ΣΥΝΤΗΡΗΣΗ ΔΑΣΙΚΟΥ ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ ΚΑΙ ΑΝΤΙΠΥΡΙΚΩΝ ΖΩΝΩΝ ΔΑΣΑΡΧΕΙΟΥ ΧΑΛΚΙΔΑΣ 2017",
        public_funding_ref="584",
    ))
    assert r.scope == "non_antinero"


def test_routine_green_fund():
    r = classify(row(
        title="ΣΥΝΤΗΡΗΣΗ ΔΑΣΙΚΟΥ ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ 2018",
        public_funding_ref="ΠΡΑΣΙΝΟ ΤΑΜΕΙΟ",
    ))
    assert r.scope == "non_antinero"


def test_no_evidence_defaults_to_non_antinero():
    r = classify(row(title="Μίσθωση δύο Ελαστιχοφόρων Φορτωτών"))
    assert r.scope == "non_antinero"
    assert r.basis == "no_antinero_evidence"


# ---------------------------------------------------------------------------
# Overrides
# ---------------------------------------------------------------------------

def test_override_wins_over_rules():
    r = classify(
        row(reference_number="22SYMV011332552",
            title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 2Β ΤΟΥ ΙΙ"),
        overrides={"22SYMV011332552": "antinero_ii"},
    )
    assert r.scope == "antinero_ii"
    assert r.basis == "curated:antinero_supplement"
