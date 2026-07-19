"""Payment orders: extraction, attribution, and effective contract values."""
from pathlib import Path

import pytest

from khmdhs.extract import payment_row
from khmdhs.payment_loader import payment_links, resolve_attribution, verify_payment
from webui import queries

from tests.conftest import add_contract, add_payment, set_scope


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

SAMPLE_PAYMENT = {
    "referenceNumber": "22PAY011002389",
    "title": "ΕΝΤΟΛΗ ΠΛΗΡΩΜΗΣ",
    "signedDate": "2022-07-01T00:00:00",
    "submissionDate": "2022-07-02T10:00:00",
    "cancelled": False,
    "credit": False,
    "contractRefNo": None,
    "totalCostWithVAT": 124.0,
    "totalCostWithoutVAT": 100.0,
    "fundingDetails": {"publicFundingRefNum": "2022ΤΑ07500000"},
}


def test_payment_row_basic():
    r = payment_row("22SYMV010447493", "22SYMV010447493", SAMPLE_PAYMENT)
    assert r["payment_ref"] == "22PAY011002389"
    assert r["contract_ref"] == "22SYMV010447493"
    assert r["attributed_ref"] == "22SYMV010447493"
    assert r["cancelled"] == 0 and r["credit"] == 0
    assert r["amount_with_vat"] == 124.0
    assert r["amount_without_vat"] == 100.0
    assert r["fund_ref_num"] == "2022ΤΑ07500000"


def test_payment_row_contract_ref_list_normalised():
    item = dict(SAMPLE_PAYMENT, contractRefNo=["22SYMV010447493", "22SYMV010856514"])
    r = payment_row("22SYMV010447493", "22SYMV010447493", item)
    assert r["api_contract_ref"] == "22SYMV010447493,22SYMV010856514"
    item = dict(SAMPLE_PAYMENT, contractRefNo=[])
    assert payment_row("X", "X", item)["api_contract_ref"] is None


def test_payment_links_reads_raw_json(mem_conn):
    add_contract(mem_conn, "A")
    add_contract(mem_conn, "B")
    mem_conn.execute(
        "UPDATE contracts SET raw_json = ? WHERE reference_number = 'A'",
        ('{"paymentRefNo": ["22PAY000000001", "22PAY000000002"]}',),
    )
    mem_conn.execute(
        "UPDATE contracts SET raw_json = ? WHERE reference_number = 'B'",
        ('{"paymentRefNo": []}',),
    )
    assert payment_links(mem_conn) == [
        ("A", "22PAY000000001"),
        ("A", "22PAY000000002"),
    ]


# ---------------------------------------------------------------------------
# Attribution along supersede chains
# ---------------------------------------------------------------------------

def test_resolve_attribution_follows_chain():
    successors = {"A": "B", "B": "C"}
    assert resolve_attribution("A", successors) == "C"
    assert resolve_attribution("B", successors) == "C"
    assert resolve_attribution("C", successors) == "C"
    assert resolve_attribution("Z", successors) == "Z"


def test_resolve_attribution_cycle_safe():
    assert resolve_attribution("A", {"A": "B", "B": "A"}) == "B"


def test_verify_payment_rejects_wrong_reference():
    item = dict(SAMPLE_PAYMENT, referenceNumber="99PAY999999999")
    assert verify_payment("22PAY011002389", "X", item) is not None
    assert verify_payment("22PAY011002389", "X", SAMPLE_PAYMENT) is None


# ---------------------------------------------------------------------------
# Effective values in the web-UI queries
# ---------------------------------------------------------------------------

@pytest.fixture
def paid_conn(mem_conn):
    """PAID has 2 live + 1 cancelled payment (paid 160 ≠ stated 100);
    UNPAID has none; OLDP is superseded by PAID and its own payment is
    attributed to PAID."""
    add_contract(mem_conn, "PAID", title="ΕΡΓΟ ANTINERO IV", eur=100.0, vats=("111111111",))
    add_contract(mem_conn, "UNPAID", title="ΕΡΓΟ ANTINERO IV", eur=70.0, vats=("111111111",))
    add_contract(mem_conn, "OLDP", title="ΕΡΓΟ ANTINERO IV", eur=100.0, vats=("111111111",))
    set_scope(mem_conn, "PAID", "antinero_iv", 1)
    set_scope(mem_conn, "UNPAID", "antinero_iv", 1)
    set_scope(mem_conn, "OLDP", "antinero_iv", 0, superseded_by="PAID")
    add_payment(mem_conn, "P1", "PAID", 60.0)
    add_payment(mem_conn, "P2", "PAID", 40.0)
    add_payment(mem_conn, "PX", "PAID", 999.0, cancelled=1)
    add_payment(mem_conn, "P3", "OLDP", 60.0, attributed_ref="PAID")
    return mem_conn


def test_kpis_use_paid_totals(paid_conn):
    k = queries.kpis(paid_conn)
    assert k["n_contracts"] == 2
    # PAID: 60+40+60 attributed (cancelled 999 skipped); UNPAID keeps stated 70
    assert k["total_eur"] == 230.0


def test_contractor_totals_use_paid(paid_conn):
    rows = queries.top_contractors(paid_conn)
    assert rows[0]["total_eur"] == 230.0
    summary = queries.contractor_summary(paid_conn, "111111111")
    assert summary["total_eur"] == 230.0


def test_list_contracts_reports_divergence(paid_conn):
    rows = {r["reference_number"]: r for r in queries.list_contracts(paid_conn)}
    assert rows["PAID"]["total_cost_with_vat"] == 160.0
    assert rows["PAID"]["stated_cost_with_vat"] == 100.0
    assert rows["PAID"]["n_payments"] == 3          # 2 own + 1 attributed
    assert rows["UNPAID"]["total_cost_with_vat"] == 70.0
    assert rows["UNPAID"]["n_payments"] == 0


def test_contract_detail_payments(paid_conn):
    d = queries.contract_detail(paid_conn, "PAID")
    refs = [p["payment_ref"] for p in d["payments"]]
    assert set(refs) == {"P1", "P2", "PX", "P3"}
    assert d["paid_with_vat"] == 160.0
    assert d["effective_cost_with_vat"] == 160.0
    d = queries.contract_detail(paid_conn, "UNPAID")
    assert d["payments"] == []
    assert d["paid_with_vat"] is None
    assert d["effective_cost_with_vat"] == 70.0


def test_all_payments_cancelled_falls_back_to_stated(mem_conn):
    add_contract(mem_conn, "C1", eur=50.0)
    set_scope(mem_conn, "C1", "antinero_iv", 1)
    add_payment(mem_conn, "PC", "C1", 42.0, cancelled=1)
    k = queries.kpis(mem_conn)
    assert k["total_eur"] == 50.0


def test_fallback_without_payments_table(mem_conn):
    mem_conn.executescript("DROP TABLE contract_payments;")
    add_contract(mem_conn, "C1", eur=50.0)
    set_scope(mem_conn, "C1", "antinero_iv", 1)
    k = queries.kpis(mem_conn)
    assert k["total_eur"] == 50.0
    d = queries.contract_detail(mem_conn, "C1")
    assert d["payments"] == []
    assert d["effective_cost_with_vat"] == 50.0
    assert queries.list_contracts(mem_conn)[0]["n_payments"] == 0


# ---------------------------------------------------------------------------
# Curated corrections
# ---------------------------------------------------------------------------

def test_apply_corrections(mem_conn, tmp_path):
    import json
    from khmdhs.payment_loader import apply_corrections
    add_contract(mem_conn, "C1", eur=100.0)
    add_payment(mem_conn, "PBAD", "C1", 999999.0)
    add_payment(mem_conn, "PDROP", "C1", 5.0)
    f = tmp_path / "corr.json"
    f.write_text(json.dumps({
        "_comment": "x",
        "PBAD": {"amount_with_vat": 42.0, "reason": "PDF says 42"},
        "PDROP": {"exclude": True, "reason": "bogus"},
        "PMISSING": {"exclude": True, "reason": "not stored"},
    }), encoding="utf-8")
    assert apply_corrections(mem_conn, f) == 2
    r = mem_conn.execute(
        "SELECT amount_with_vat, amount_without_vat, correction_note FROM contract_payments "
        "WHERE payment_ref='PBAD'").fetchone()
    assert r["amount_with_vat"] == 42.0
    assert r["amount_without_vat"] == 999999.0  # untouched when not overridden
    assert r["correction_note"] == "PDF says 42"
    r = mem_conn.execute(
        "SELECT cancelled, correction_note FROM contract_payments "
        "WHERE payment_ref='PDROP'").fetchone()
    assert r["cancelled"] == 1 and r["correction_note"] == "bogus"


def test_real_db_no_uncorrected_outliers():
    """No non-cancelled payment may exceed 150% of its contract family's
    total stated value — family = every version connected via prevReferenceNo
    links (originals + modifications + supplementary contracts). Catches
    registry keying errors (×100 amounts) without tripping on supplements.
    The ΥΠΕΝ↔ΤΑΙΠΕΔ umbrella is exempt: its framework grew via amendments.
    """
    if not REAL_DB.exists():
        pytest.skip("real DB not present")
    conn = queries.open_ro(REAL_DB)
    try:
        rows = conn.execute("""
            WITH RECURSIVE fam(root, member) AS (
                SELECT reference_number, reference_number FROM contracts
                UNION
                SELECT f.root, c.reference_number FROM fam f
                JOIN contracts c ON c.prev_reference_no = f.member
                UNION
                SELECT f.root, c.prev_reference_no FROM fam f
                JOIN contracts c ON c.reference_number = f.member
                WHERE c.prev_reference_no IN (SELECT reference_number FROM contracts)
            ),
            fam_value(root, stated) AS (
                SELECT f.root, SUM(k.total_cost_with_vat) FROM fam f
                JOIN contracts k ON k.reference_number = f.member
                GROUP BY f.root
            )
            SELECT p.payment_ref FROM contract_payments p
            JOIN fam_value fv ON fv.root = p.attributed_ref
            LEFT JOIN contract_scope s ON s.reference_number = p.attributed_ref
            WHERE p.cancelled = 0 AND fv.stated > 0
              AND p.amount_with_vat > 1.5 * fv.stated
              AND COALESCE(s.scope, '') != 'antinero_umbrella'
        """).fetchall()
        assert [r["payment_ref"] for r in rows] == []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Integration against the real DB (skipped when not built)
# ---------------------------------------------------------------------------

REAL_DB = Path(__file__).parent.parent / "data" / "processed" / "khmdhs.sqlite"


@pytest.fixture
def real_pay_conn():
    if not REAL_DB.exists():
        pytest.skip("real DB not present")
    conn = queries.open_ro(REAL_DB)
    n = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='contract_payments'"
    ).fetchone()[0]
    if not n or not conn.execute("SELECT COUNT(*) FROM contract_payments").fetchone()[0]:
        pytest.skip("payments not harvested")
    yield conn
    conn.close()


def test_real_db_payments_linked_and_verified(real_pay_conn):
    # every stored payment's linking contract exists
    orphans = real_pay_conn.execute("""
        SELECT COUNT(*) FROM contract_payments p
        LEFT JOIN contracts k ON k.reference_number = p.contract_ref
        WHERE k.reference_number IS NULL
    """).fetchone()[0]
    assert orphans == 0
    # attribution only ever points at a non-superseded version
    bad = real_pay_conn.execute("""
        SELECT COUNT(*) FROM contract_payments p
        JOIN contract_scope s ON s.reference_number = p.attributed_ref
        WHERE s.superseded_by IS NOT NULL
    """).fetchone()[0]
    assert bad == 0


def test_real_db_antinero_i_lot_has_expected_payments(real_pay_conn):
    # 22SYMV010447493 (Anti-nero I, lot 1.Α) — 7 payment orders per the API chain
    n = real_pay_conn.execute(
        "SELECT COUNT(*) FROM contract_payments WHERE contract_ref = '22SYMV010447493'"
    ).fetchone()[0]
    assert n == 7
