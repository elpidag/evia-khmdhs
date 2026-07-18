"""Tests for the supplement loader's relevance gate (khmdhs.antinero_loader)."""
import json
from pathlib import Path

from khmdhs.antinero_loader import DATA_FILE, verify_relevance
from khmdhs.scope import IN_SCOPE


def item(**kw):
    base = {
        "title": "ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 3.Α",
        "organizationVatNumber": "090273987",
        "fundingDetails": {"publicFundingRefNum": "2022ΤΑ07500000"},
    }
    base.update(kw)
    return base


def test_fund_basis_accepts_matching_payload():
    assert verify_relevance("antinero_i", "fund:2022ΤΑ07500000", item()) is None


def test_fund_basis_refuses_wrong_fund():
    bad = item(fundingDetails={"publicFundingRefNum": "2019ΣΕ99900000"})
    reason = verify_relevance("antinero_i", "fund:2022ΤΑ07500000", bad)
    assert reason is not None and "2019ΣΕ99900000" in reason


def test_fund_basis_refuses_missing_fund():
    bad = item(fundingDetails={})
    assert verify_relevance("antinero_i", "fund:2022ΤΑ07500000", bad) is not None


def test_refuses_non_ypen_authority():
    bad = item(organizationVatNumber="999999999")
    reason = verify_relevance("antinero_i", "fund:2022ΤΑ07500000", bad)
    assert reason is not None and "authority" in reason


def test_title_basis_accepts_toy_ii_greek_iotas():
    # 'ΤΟΥ ΙΙ' with Greek iotas normalises to 'TOY II'
    ok = item(title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 2Β ΤΟΥ ΙΙ", fundingDetails={})
    assert verify_relevance("antinero_ii", "title:ΤΟΥ ΙΙ", ok) is None


def test_title_basis_refuses_unrelated_title():
    bad = item(title="ΠΡΟΜΗΘΕΙΑ ΓΡΑΦΙΚΗΣ ΥΛΗΣ", fundingDetails={})
    assert verify_relevance("antinero_ii", "title:ΤΟΥ ΙΙ", bad) is not None


def test_unknown_basis_is_refused():
    assert verify_relevance("antinero_i", "vibes:trust_me", item()) is not None


# ---------------------------------------------------------------------------
# The curation file itself
# ---------------------------------------------------------------------------

def test_supplement_file_is_well_formed():
    data = json.loads(Path(DATA_FILE).read_text(encoding="utf-8"))
    data.pop("_comment", None)
    assert len(data) >= 30
    for adam, meta in data.items():
        assert adam[2:6] == "SYMV", adam
        assert meta["phase"] in IN_SCOPE, (adam, meta["phase"])
        assert meta["basis"].split(":", 1)[0] in ("fund", "title"), (adam, meta["basis"])
        assert meta.get("lot"), adam


def test_supplement_has_the_complete_antinero_i_lot_set():
    data = json.loads(Path(DATA_FILE).read_text(encoding="utf-8"))
    data.pop("_comment", None)
    lots = {m["lot"] for m in data.values() if m["phase"] == "antinero_i"}
    # 20 originals confirmed via the Aug-2022 option-exercise decisions
    # (lots 1.Α-8.Β, no έργο 9) + the 3.Γ modification.
    expected = {"1.Α", "1.Β", "2.Α", "2.Β", "2.Γ", "3.Α", "3.Β", "3.Γ",
                "3.Γ (τροποποίηση)", "4.Α", "4.Β", "4.Γ",
                "5.Α", "5.Β", "5.Γ", "5.Δ", "6.Α", "6.Β", "7", "8.Α", "8.Β"}
    assert lots == expected
