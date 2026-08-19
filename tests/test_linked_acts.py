"""Linked procurement acts (REQ/PROC/AWRD) layer: units + real-DB pins."""
import sqlite3

import pytest

from atlas_api import queries_extra
from khmdhs.config import DEFAULT_DB
from khmdhs.db import SCHEMA_SQL
from khmdhs.linked_acts_loader import SCHEMA, upsert_act
from tests.conftest import add_contract


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCHEMA)
    return conn


def test_upsert_act_stores_record_and_tolerates_missing():
    conn = _db()
    upsert_act(conn, "22AWRD000000001", "auction", {
        "title": "ΑΠΟΦΑΣΗ ΚΑΤΑΚΥΡΩΣΗΣ", "submissionDate": "2022-09-16T20:36:32",
        "signedDate": None, "cancelled": False})
    upsert_act(conn, "22PROC000000001", "notice", None)   # record fetch failed
    rows = {r["adam"]: dict(r) for r in conn.execute("SELECT * FROM linked_acts")}
    assert rows["22AWRD000000001"]["title"] == "ΑΠΟΦΑΣΗ ΚΑΤΑΚΥΡΩΣΗΣ"
    assert rows["22AWRD000000001"]["cancelled"] == 0
    assert rows["22PROC000000001"]["title"] is None       # honest placeholder


def test_contract_timeline_orders_and_resolves_siblings():
    conn = _db()
    add_contract(conn, "23SYMV000000002", title="Η ΣΥΜΒΑΣΗ", eur=1000.0)
    add_contract(conn, "22SYMV000000009", title="ΑΔΕΛΦΗ ΣΥΜΒΑΣΗ", eur=500.0)
    upsert_act(conn, "22REQ000000001", "request", {
        "title": "ΑΙΤΗΜΑ", "submissionDate": "2022-01-05T10:00:00"})
    upsert_act(conn, "22AWRD000000001", "auction", {
        "title": "ΚΑΤΑΚΥΡΩΣΗ", "signedDate": "2022-03-01T00:00:00"})
    conn.executemany("INSERT INTO contract_linked_acts VALUES (?,?,?)", [
        ("23SYMV000000002", "22AWRD000000001", "auction"),
        ("23SYMV000000002", "22REQ000000001", "request"),
        ("23SYMV000000002", "22SYMV000000009", "contract"),
        ("23SYMV000000002", "24SYMV000000099", "contract"),  # outside dataset
    ])
    tl = queries_extra.contract_timeline(conn, "23SYMV000000002")
    kinds = [t["kind"] for t in tl]
    assert kinds[0] == "request" and "auction" in kinds
    sib = {t["adam"]: t for t in tl if t["kind"] == "contract"}
    assert sib["22SYMV000000009"]["in_db"] is True
    assert sib["22SYMV000000009"]["title"] == "ΑΔΕΛΦΗ ΣΥΜΒΑΣΗ"
    assert sib["24SYMV000000099"]["in_db"] is False


def test_contract_timeline_survives_missing_tables():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    assert queries_extra.contract_timeline(conn, "XXSYMV") == []


# ---------------------------------------------------------- real-DB pins

@pytest.fixture(scope="module")
def conn():
    if not DEFAULT_DB.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    c = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        c.execute("SELECT 1 FROM linked_acts LIMIT 1")
    except sqlite3.OperationalError:
        pytest.skip("linked acts not harvested yet")
    yield c
    c.close()


def test_real_db_known_family(conn):
    fam = {r["kind"]: r["adam"] for r in conn.execute(
        "SELECT kind, adam FROM contract_linked_acts "
        "WHERE reference_number = '23SYMV011953055'")}
    assert fam["auction"] == "22AWRD011258574"
    assert fam["notice"] == "22PROC011082770"
    assert fam["contract"] == "22SYMV011470180"


def test_real_db_every_mapped_upstream_act_has_a_record(conn):
    missing = conn.execute(
        """SELECT COUNT(*) FROM contract_linked_acts cla
           LEFT JOIN linked_acts la USING (adam)
           WHERE cla.kind != 'contract' AND la.adam IS NULL""").fetchone()[0]
    assert missing == 0


def test_real_db_in_scope_award_coverage(conn):
    n, with_award = conn.execute(
        """SELECT COUNT(*), SUM(has_awrd) FROM (
             SELECT s.reference_number,
                    EXISTS(SELECT 1 FROM contract_linked_acts cla
                           WHERE cla.reference_number = s.reference_number
                             AND cla.kind = 'auction') AS has_awrd
             FROM contract_scope s WHERE s.in_scope = 1)""").fetchone()
    assert n == 245
    # Registry reality (verified live 2026-08-02): the chain graph only knows
    # the links the ΣΥΜΒ payloads declared — most Anti-nero direct awards were
    # posted with NO linked κατακύρωση. This pin documents that gap.
    # (2026-08-13: the 7 antinero_probable chains left the basis — one of
    # them carried a linked κατακύρωση, hence 41 → 40.)
    assert with_award == 41


def test_real_db_act_counts(conn):
    kinds = dict(conn.execute(
        "SELECT kind, COUNT(*) FROM linked_acts GROUP BY kind"))
    assert kinds == {"request": 37, "approved_request": 37,
                     "notice": 34, "auction": 39}
    # every stored act has its record payload
    assert conn.execute("SELECT COUNT(*) FROM linked_acts "
                        "WHERE raw_json IS NULL").fetchone()[0] == 0
