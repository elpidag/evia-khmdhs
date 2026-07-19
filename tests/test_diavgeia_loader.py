"""Diavgeia payment ingestion: contract resolution and full-batch coverage."""
from pathlib import Path

import pytest

from khmdhs.diavgeia_loader import resolve_contract
from webui import queries

from tests.conftest import add_contract, set_scope


def test_resolve_prefers_execution_over_umbrella(mem_conn):
    add_contract(mem_conn, "23SYMV000000001", title="ΣΥΜΒΑΣΗ ΥΠΕΝ-ΕΕΣΥΠ")
    add_contract(mem_conn, "23SYMV000000002", title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ")
    set_scope(mem_conn, "23SYMV000000001", "antinero_umbrella", 0)
    set_scope(mem_conn, "23SYMV000000002", "antinero_ii", 1)
    ref, err = resolve_contract(
        ["23SYMV000000001", "23SYMV000000002"], mem_conn, successors={})
    assert (ref, err) == ("23SYMV000000002", None)


def test_resolve_follows_chain_to_common_tip(mem_conn):
    add_contract(mem_conn, "23SYMV000000001")
    add_contract(mem_conn, "24SYMV000000002", prev="23SYMV000000001")
    set_scope(mem_conn, "23SYMV000000001", "antinero_ii", 0, superseded_by="24SYMV000000002")
    set_scope(mem_conn, "24SYMV000000002", "antinero_ii", 1)
    successors = {"23SYMV000000001": "24SYMV000000002"}
    ref, err = resolve_contract(
        ["23SYMV000000001", "24SYMV000000002"], mem_conn, successors)
    assert (ref, err) == ("24SYMV000000002", None)


def test_resolve_rejects_distinct_chains_and_missing(mem_conn):
    add_contract(mem_conn, "23SYMV000000001")
    add_contract(mem_conn, "23SYMV000000009")
    set_scope(mem_conn, "23SYMV000000001", "antinero_ii", 1)
    set_scope(mem_conn, "23SYMV000000009", "antinero_ii", 1)
    ref, err = resolve_contract(
        ["23SYMV000000001", "23SYMV000000009"], mem_conn, successors={})
    assert ref is None and "different chains" in err
    ref, err = resolve_contract(["24SYMV000000404"], mem_conn, successors={})
    assert ref is None and "not in DB" in err
    ref, err = resolve_contract([], mem_conn, successors={})
    assert ref is None and "no contract" in err


# ---------------------------------------------------------------------------
# Integration against the real DB (skipped when not built)
# ---------------------------------------------------------------------------

REAL_DB = Path(__file__).parent.parent / "data" / "processed" / "khmdhs.sqlite"
XLSX = Path(__file__).parent.parent / "data" / "raw" / "payments_not_in_db_155.xlsx"


def test_real_db_every_antinero_diavgeia_payment_is_stored():
    """All 151 non-foreign decisions in the xlsx must be represented in
    contract_payments — either via a KHMDHS PAY record carrying the ΑΔΑ or
    as a Diavgeia-only row keyed by the ΑΔΑ itself."""
    if not (REAL_DB.exists() and XLSX.exists()):
        pytest.skip("real DB or xlsx not present")
    import openpyxl

    wb = openpyxl.load_workbook(XLSX, read_only=True)
    rows = list(wb.active.iter_rows(values_only=True))[1:]
    conn = queries.open_ro(REAL_DB)
    try:
        stored = {r[0] for r in conn.execute(
            "SELECT ada FROM contract_payments WHERE ada IS NOT NULL")}
        missing = []
        for r in rows:
            ada, fund = r[0].strip(), (r[4] or "")
            if fund.startswith(("2019ΣΕ", "2022ΤΑ07500030")):
                continue  # foreign funds, intentionally skipped
            if ada not in stored:
                missing.append(ada)
        assert missing == []
        # 4 from the xlsx batch + 1 ΤΑΙΠΕΔ operating-cost clearance
        # (6ΗΔ34653Π8-ΙΞΓ) from the full fund sweep
        n_diavgeia_only = conn.execute(
            "SELECT COUNT(*) FROM contract_payments WHERE source = 'diavgeia'"
        ).fetchone()[0]
        assert n_diavgeia_only == 5
    finally:
        conn.close()
