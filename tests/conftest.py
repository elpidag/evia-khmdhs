"""Shared fixtures: a small in-memory contracts DB with a scope table."""
import sqlite3

import pytest

from khmdhs.db import SCHEMA_SQL
from khmdhs.scope_loader import SCHEMA as SCOPE_SCHEMA

CONTRACT_COLS = (
    "reference_number, title, public_funding_ref, public_funding_ref_num, "
    "prev_reference_no, cancelled, total_cost_with_vat, organization_name, "
    "signer_name, units_operator_name, procedure_type, bids_submitted, fetched_at"
)


def add_contract(conn, ref, title=None, fund_num=None, prev=None, cancelled=0,
                 eur=1000.0, org="ΥΠΕΝ", vats=("111111111",), fund_ref=None):
    conn.execute(
        f"INSERT INTO contracts ({CONTRACT_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ref, title, fund_ref, fund_num, prev, cancelled, eur, org,
         "SIGNER", "UNIT", "Απευθείας ανάθεση", 1, "2026-01-01T00:00:00"),
    )
    for seq, vat in enumerate(vats):
        conn.execute(
            "INSERT INTO contractors (reference_number, seq, vat_number, name, country, greek_vat) "
            "VALUES (?,?,?,?, 'GR', 1)",
            (ref, seq, vat, f"CONTRACTOR {vat}"),
        )


def add_payment(conn, pay_ref, contract_ref, eur, attributed_ref=None,
                cancelled=0, credit=0, eur_no_vat=None):
    conn.execute(
        "INSERT INTO contract_payments (payment_ref, contract_ref, attributed_ref, "
        "title, signed_date, cancelled, credit, amount_without_vat, amount_with_vat, fetched_at) "
        "VALUES (?,?,?, 'ΕΝΤΟΛΗ ΠΛΗΡΩΜΗΣ', '2026-01-01', ?, ?, ?, ?, '2026-01-01T00:00:00')",
        (pay_ref, contract_ref, attributed_ref or contract_ref, cancelled, credit,
         eur_no_vat if eur_no_vat is not None else eur, eur),
    )


def set_scope(conn, ref, scope, in_scope, superseded_by=None, basis="test"):
    conn.execute(
        "INSERT OR REPLACE INTO contract_scope "
        "(reference_number, scope, in_scope, superseded_by, basis, curated_at) "
        "VALUES (?,?,?,?,?, '2026-01-01T00:00:00')",
        (ref, scope, in_scope, superseded_by, basis),
    )


@pytest.fixture
def mem_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCOPE_SCHEMA)
    yield conn
    conn.close()
