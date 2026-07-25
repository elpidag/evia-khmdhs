"""Unit tests for the incremental-refresh change detector."""
from khmdhs.refresh import contract_changed


BASE = {
    "referenceNumber": "24SYMV000000001",
    "lastUpdateDate": "2026-05-01",
    "paymentRefNo": ["25PAY000000001", "25PAY000000002"],
    "nextRefNo": None,
    "cancelled": False,
}


def test_identical_payload_is_unchanged():
    assert contract_changed(BASE, dict(BASE)) is False


def test_payment_order_reordering_is_unchanged():
    new = {**BASE, "paymentRefNo": ["25PAY000000002", "25PAY000000001"]}
    assert contract_changed(BASE, new) is False


def test_new_payment_ref_is_changed():
    new = {**BASE, "paymentRefNo": BASE["paymentRefNo"] + ["26PAY000000009"]}
    assert contract_changed(BASE, new) is True


def test_last_update_date_bump_is_changed():
    assert contract_changed(BASE, {**BASE, "lastUpdateDate": "2026-07-01"}) is True


def test_new_amendment_link_is_changed():
    assert contract_changed(BASE, {**BASE, "nextRefNo": "26SYMV000000005"}) is True


def test_cancellation_is_changed():
    assert contract_changed(BASE, {**BASE, "cancelled": True}) is True


def test_missing_keys_tolerated():
    assert contract_changed({}, {}) is False
    assert contract_changed({}, {"paymentRefNo": ["25PAY000000001"]}) is True
