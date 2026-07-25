"""Unit tests for the payment amount validator's pure matching helpers."""
import sqlite3

from khmdhs.payment_validator import (
    amount_appears,
    amount_tokens,
    format_greek,
    largest_candidates,
    validate_payment,
)


def test_format_greek():
    assert format_greek(219104.12) == "219.104,12"
    assert format_greek(950.0) == "950,00"
    assert format_greek(21910411.88) == "21.910.411,88"


def test_exact_greek_match():
    text = "ΣΥΝΟΛΙΚΗ ΑΞΙΑ ΠΑΡΑΣΤΑΤΙΚΟΥ: 219.104,12 €"
    assert amount_appears(text, 219104.12) == "exact_greek"


def test_plain_decimal_match():
    assert amount_appears("Amount: 219104.12 EUR", 219104.12) == "exact_plain"


def test_digit_token_match_english_grouping():
    # Same digits, anglo grouping — must still match via digit comparison
    assert amount_appears("TOTAL 219,104.12", 219104.12) == "digit_token"


def test_tolerant_match_line_wrapped():
    # -layout output sometimes wraps an amount across whitespace
    assert amount_appears("ΣΥΝΟΛΟ 219.104,\n12", 219104.12) == "tolerant"


def test_x100_error_does_not_match():
    # The registry's ×100 keying error must NOT be found in a PDF that
    # documents the true amount (this is the whole point of the validator).
    text = "ΣΥΝΟΛΙΚΗ ΑΞΙΑ ΠΑΡΑΣΤΑΤΙΚΟΥ 219.104,12 ΦΠΑ 42.407,25"
    assert amount_appears(text, 21910411.88) is None


def test_no_match_on_substring_of_longer_number():
    # 950,00 must not "tolerantly" match inside 219.104,12 or 42.950,00-like runs
    assert amount_appears("ΠΟΣΟ 1.042.950,00", 42950.00) is None


def test_amount_tokens_and_candidates():
    text = "α) 146.349,23 β) 237.119,12 σύνολο 383.468,35 ΑΦΜ 090273987"
    toks = amount_tokens(text)
    assert "383.468,35" in toks and "146.349,23" in toks
    # candidates ordered largest-first, no tiny fragments
    cands = largest_candidates(text)
    assert cands[0] == "383.468,35"


def _row(**kw):
    """Build a sqlite3.Row for validate_payment."""
    base = {
        "payment_ref": "25PAY000000001",
        "attributed_ref": "24SYMV000000001",
        "amount_with_vat": 239940.0,
        "amount_without_vat": 193500.0,
        "cancelled": 0,
        "correction_note": None,
        "raw_json": None,
    }
    base.update(kw)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cols = ", ".join(base)
    placeholders = ", ".join(f":{k}" for k in base)
    conn.execute(f"CREATE TABLE t ({cols})")
    conn.execute(f"INSERT INTO t ({cols}) VALUES ({placeholders})", base)
    return conn.execute("SELECT * FROM t").fetchone()


def test_validate_ok():
    r = validate_payment(_row(), "ΣΥΝΟΛΟ 239.940,00 (ΦΠΑ 46.440,00, καθαρό 193.500,00)")
    assert r["status"] == "ok" and r["match_with_vat"] == "exact_greek"


def test_validate_net_only():
    r = validate_payment(_row(), "ΚΑΘΑΡΗ ΑΞΙΑ 193.500,00")
    assert r["status"] == "ok_net_only"


def test_validate_mismatch_reports_candidates():
    r = validate_payment(_row(amount_with_vat=992420531.12, amount_without_vat=800339138.0),
                         "ΣΥΝΟΛΙΚΗ ΑΞΙΑ 239.940,00 ΚΑΘΑΡΗ 193.500,00")
    assert r["status"] == "mismatch"
    assert "239.940,00" in r["pdf_candidates"]


def test_validate_near_match_on_cent_rounding():
    # KHMDHS 14,428.99 vs PDF 14.428,98 — registry rounding, not a keying error
    r = validate_payment(_row(amount_with_vat=14428.99, amount_without_vat=None),
                         "ΣΥΝΟΛΟ ΕΝΤΟΛΗΣ 14.428,98")
    assert r["status"] == "near_match"


def test_validate_corrected_reports_registry_value():
    r = validate_payment(
        _row(correction_note="curated fix",
             raw_json='{"totalCostWithVAT": 992420531.12}'),
        "ΣΥΝΟΛΙΚΗ ΑΞΙΑ 239.940,00",
    )
    assert r["status"] == "ok_corrected"
    assert r["registry_amount_with_vat"] == 992420531.12
