"""Amendment-chain completion: link repair, missing-member discovery."""
import json
from pathlib import Path

import pytest

from khmdhs.chain_loader import missing_chain_members, repair_link_columns
from khmdhs.extract import parent_row
from webui import queries

from tests.conftest import add_contract


def test_parent_row_next_ref_is_string_not_list():
    # nextRefNo comes back as a plain string; the old code took [0] → "2".
    row = parent_row({"referenceNumber": "22SYMV000000001", "nextRefNo": "22SYMV000000002"})
    assert row["next_reference_no"] == "22SYMV000000002"
    row = parent_row({"referenceNumber": "X", "nextRefNo": ["22SYMV000000002"]})
    assert row["next_reference_no"] == "22SYMV000000002"
    assert parent_row({"referenceNumber": "X"})["next_reference_no"] is None


def test_repair_link_columns_fixes_truncated_next(mem_conn):
    add_contract(mem_conn, "22SYMV000000001")
    mem_conn.execute(
        "UPDATE contracts SET next_reference_no = '2', raw_json = ? "
        "WHERE reference_number = '22SYMV000000001'",
        (json.dumps({"referenceNumber": "22SYMV000000001",
                     "nextRefNo": "22SYMV000000002"}),),
    )
    assert repair_link_columns(mem_conn) == 1
    val = mem_conn.execute(
        "SELECT next_reference_no FROM contracts WHERE reference_number = '22SYMV000000001'"
    ).fetchone()[0]
    assert val == "22SYMV000000002"
    # second run is a no-op
    assert repair_link_columns(mem_conn) == 0


def test_missing_chain_members(mem_conn):
    add_contract(mem_conn, "22SYMV000000001")
    add_contract(mem_conn, "22SYMV000000003", prev="22SYMV000000002")
    mem_conn.execute(
        "UPDATE contracts SET next_reference_no = '22SYMV000000002' "
        "WHERE reference_number = '22SYMV000000001'")
    # 2 is referenced twice (as next of 1, as prev of 3) but stored never
    assert missing_chain_members(mem_conn) == {"22SYMV000000002"}


# ---------------------------------------------------------------------------
# Integration against the real DB (skipped when not built)
# ---------------------------------------------------------------------------

REAL_DB = Path(__file__).parent.parent / "data" / "processed" / "khmdhs.sqlite"


@pytest.fixture
def real_conn():
    if not REAL_DB.exists():
        pytest.skip("real DB not present")
    conn = queries.open_ro(REAL_DB)
    yield conn
    conn.close()


def test_real_db_chains_are_complete(real_conn):
    assert missing_chain_members(real_conn) == set()


def test_real_db_no_chain_double_counting(real_conn):
    """At most one in-scope member per supersede chain."""
    rows = real_conn.execute("""
        SELECT s1.reference_number FROM contract_scope s1
        JOIN contract_scope s2 ON s2.reference_number = s1.superseded_by
        WHERE s1.in_scope = 1
    """).fetchall()
    assert rows == []  # nothing in scope may have a successor


def test_real_db_every_in_scope_contract_has_regions(real_conn):
    n = real_conn.execute("""
        SELECT COUNT(*) FROM contract_scope s
        WHERE s.in_scope = 1 AND NOT EXISTS
            (SELECT 1 FROM contract_project_regions r
             WHERE r.reference_number = s.reference_number)
    """).fetchone()[0]
    assert n == 0


def test_real_db_known_amendment_chain(real_conn):
    """Lot 1.Α of Anti-nero I: original 22SYMV010447493 superseded by the
    amendment 22SYMV010856514, which is in scope and inherits the payments."""
    row = real_conn.execute(
        "SELECT in_scope, superseded_by FROM contract_scope "
        "WHERE reference_number = '22SYMV010447493'").fetchone()
    assert (row["in_scope"], row["superseded_by"]) == (0, "22SYMV010856514")
    row = real_conn.execute(
        "SELECT in_scope FROM contract_scope "
        "WHERE reference_number = '22SYMV010856514'").fetchone()
    assert row["in_scope"] == 1
    n = real_conn.execute(
        "SELECT COUNT(*) FROM contract_payments "
        "WHERE attributed_ref = '22SYMV010856514'").fetchone()[0]
    assert n == 7
