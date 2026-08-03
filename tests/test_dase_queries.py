"""Unit tests for webui/dase_queries.py on a dase-shaped in-memory DB
(khmdhs schema WITHOUT contract_scope — mirrors the real dase.sqlite)."""
import sqlite3

import pytest

from khmdhs.db import SCHEMA_SQL
from webui import dase_queries as dq
from webui import queries


@pytest.fixture
def dase_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)          # NO scope schema on purpose
    conn.executescript("""
        CREATE TABLE dase_contractors (
            vat_number TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            form       TEXT,
            basis      TEXT,
            curated_at TEXT NOT NULL
        );
        CREATE TABLE dase_contract_regions (
            reference_number TEXT PRIMARY KEY,
            region_pe  TEXT NOT NULL,
            source     TEXT NOT NULL,
            basis      TEXT,
            curated_at TEXT NOT NULL
        );
    """)
    yield conn
    conn.close()


def add(conn, ref, eur=1000.0, cancelled=0, nxt=None, vats=("096000001",),
        signed="2023-05-01T00:00:00", title="ΥΛΟΤΟΜΙΑ", org="ΥΠΕΝ",
        unit="ΔΑΣΑΡΧΕΙΟ ΔΡΑΜΑΣ", procedure="Απευθείας ανάθεση (αρ.118)",
        ctype="Υπηρεσίες", names=None):
    # net defaults to gross so expectations hold on either basis (atlas views)
    conn.execute(
        "INSERT INTO contracts (reference_number, title, cancelled,"
        " next_reference_no, total_cost_with_vat, total_cost_without_vat,"
        " contract_signed_date,"
        " organization_name, units_operator_name, procedure_type,"
        " contract_type, fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?, '2026-01-01T00:00:00')",
        (ref, title, cancelled, nxt, eur, eur, signed, org, unit, procedure,
         ctype))
    for seq, vat in enumerate(vats):
        name = (names or {}).get(vat, f"ΔΑΣΕ {vat}")
        conn.execute(
            "INSERT INTO contractors (reference_number, seq, vat_number,"
            " name, country, greek_vat) VALUES (?,?,?,?, 'GR', 1)",
            (ref, seq, vat, name))


def curate(conn, vat, name="ΔΑΣΕ ΤΕΣΤ", form="dase"):
    conn.execute("INSERT INTO dase_contractors VALUES (?,?,?,?, '2026-07-27')",
                 (vat, name, form, "test"))


# ---------------------------------------------------------------------------
# live_filter / dedup
# ---------------------------------------------------------------------------

def test_dedup_drops_superseded_and_cancelled(dase_conn):
    add(dase_conn, "21SYMV000000001", eur=100.0, nxt="21SYMV000000002")
    add(dase_conn, "21SYMV000000002", eur=120.0)         # amendment present
    add(dase_conn, "21SYMV000000003", eur=50.0, cancelled=1)
    # successor NOT harvested → row stays in
    add(dase_conn, "21SYMV000000004", eur=70.0, nxt="21SYMV000000099")
    k = dq.kpis(dase_conn)
    assert k["n_contracts"] == 2
    assert k["total_eur"] == pytest.approx(190.0)
    assert k["gross_n"] == 4
    assert k["n_cancelled"] == 1
    assert k["n_superseded"] == 1


def test_kpis_median_and_direct(dase_conn):
    for i, eur in enumerate((10.0, 20.0, 30.0)):
        add(dase_conn, f"22SYMV00000001{i}", eur=eur)
    add(dase_conn, "22SYMV000000020", eur=40.0, procedure="Ανοιχτή διαδικασία")
    k = dq.kpis(dase_conn)
    assert k["median_eur"] == 30.0        # upper median of 4 values
    assert k["pct_direct"] == 75.0


# ---------------------------------------------------------------------------
# canonical VAT + entity merging
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("096034999", "096034999"),
    (" 096034999 ", "096034999"),
    ("΄096035032", "096035032"),
    ("997106512 ΚΑΙ 997841856", "997106512"),   # first run wins
    ("96035032", "096035032"),                  # 8 digits → zero-padded
    ("no digits", None),
    (None, None),
])
def test_canonical_vat(raw, expected):
    assert dq.canonical_vat(raw) == expected


def test_coop_merge_across_spelling_variants(dase_conn):
    curate(dase_conn, "096034999", name="ΔΑΣΕ Η ΕΝΩΣΗ ΣΤΑΥΡΟΥ")
    add(dase_conn, "22SYMV000000001", eur=100.0, vats=("096034999",),
        names={"096034999": "ΔΑΣΕ «Η ΕΝΩΣΗ» ΣΤΑΥΡΟΥ"})
    add(dase_conn, "22SYMV000000002", eur=200.0, vats=(" 096034999",),
        names={" 096034999": "Δασικός Συνεταιρισμός Σταυρού"})
    tops = dq.top_coops(dase_conn)
    assert len(tops) == 1
    t = tops[0]
    assert t["vat"] == "096034999"
    assert t["name"] == "ΔΑΣΕ Η ΕΝΩΣΗ ΣΤΑΥΡΟΥ"     # curated name wins
    assert t["n_contracts"] == 2
    assert t["total_eur"] == pytest.approx(300.0)
    # detail helpers see the same merged population
    s = dq.coop_summary(dase_conn, "096034999")
    assert s["n_contracts"] == 2 and s["total_eur"] == pytest.approx(300.0)
    assert len(dq.coop_contracts(dase_conn, "096034999")) == 2


def test_org_grouping_merges_dash_variants(dase_conn):
    add(dase_conn, "22SYMV000000001", eur=10.0,
        org="ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ ΜΑΚΕΔΟΝΙΑΣ – ΘΡΑΚΗΣ")
    add(dase_conn, "22SYMV000000002", eur=20.0,
        org="ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ ΜΑΚΕΔΟΝΙΑΣ - ΘΡΑΚΗΣ")
    orgs = dq.top_orgs(dase_conn)
    assert len(orgs) == 1
    assert orgs[0]["n_contracts"] == 2
    assert orgs[0]["total_eur"] == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# yearly, cpv, histogram, regions
# ---------------------------------------------------------------------------

def test_yearly_handles_both_date_formats(dase_conn):
    add(dase_conn, "21SYMV000000001", eur=10.0, signed="15/10/2021")
    add(dase_conn, "23SYMV000000002", eur=20.0, signed="2023-05-01T00:00:00")
    ys = dq.yearly_totals(dase_conn)
    assert [(y["year"], y["eur"]) for y in ys] == [("2021", 10.0), ("2023", 20.0)]


def test_cpv_noise_flag(dase_conn):
    add(dase_conn, "22SYMV000000001")
    dase_conn.execute(
        "INSERT INTO contract_cpvs (reference_number, seq, cpv_code,"
        " cpv_description) VALUES ('22SYMV000000001', 0, '66519300-4',"
        " 'Επικουρικές ασφαλιστικές')")
    dase_conn.execute(
        "INSERT INTO contract_cpvs (reference_number, seq, cpv_code,"
        " cpv_description) VALUES ('22SYMV000000001', 1, '77210000-5',"
        " 'Υλοτομία')")
    mix = {r["cpv"]: r for r in dq.cpv_mix(dase_conn)}
    assert mix["66519300-4"]["noise"] is True
    assert mix["77210000-5"]["noise"] is False


def test_value_histogram_bins_and_median(dase_conn):
    for i, eur in enumerate((500.0, 3_000.0, 7_000.0, 300_000.0)):
        add(dase_conn, f"22SYMV0000000{i:02d}", eur=eur)
    h = dq.value_histogram(dase_conn)
    assert h["n"] == 4
    assert sum(h["counts"]) == 4
    assert h["counts"][0] == 1                       # 500 → ≤1k bin
    assert h["median"] == 7_000.0
    assert h["labels"][0] == "≤1k"
    assert h["labels"][-1].startswith("≥")


def test_money_by_pe_and_unresolved_bucket(dase_conn):
    add(dase_conn, "22SYMV000000001", eur=100.0)
    add(dase_conn, "22SYMV000000002", eur=40.0)      # no region row
    dase_conn.execute(
        "INSERT INTO dase_contract_regions VALUES"
        " ('22SYMV000000001', 'Π.Ε. Δράμας', 'registry:x', 'unit', '2026-07-27')")
    out = dq.money_by_pe(dase_conn)
    assert out["regions"] == [
        {"pe": "Π.Ε. Δράμας", "n_contracts": 1, "eur": 100.0}]
    assert out["unresolved"] == {"n": 1, "eur": 40.0}


def test_list_contracts_is_live_only(dase_conn):
    add(dase_conn, "22SYMV000000001", title="ΥΛΟΤΟΜΙΑ ΝΕΥΡΟΚΟΠΙΟΥ",
        nxt="22SYMV000000002")                       # superseded → hidden
    add(dase_conn, "22SYMV000000002", title="ΤΡΟΠΟΠΟΙΗΣΗ ΝΕΥΡΟΚΟΠΙΟΥ")
    add(dase_conn, "22SYMV000000003", title="ΑΚΥΡΗ", cancelled=1)
    rows = dq.list_contracts(dase_conn)
    assert [r["reference_number"] for r in rows] == ["22SYMV000000002"]
    assert len(dq.list_contracts(dase_conn, q="νευροκοπ")) == 1
    assert len(dq.list_contracts(dase_conn, q="ΔΡΑΜΑΣ")) == 1   # via unit


def test_coop_contracts_is_live_only(dase_conn):
    curate(dase_conn, "096000001")
    add(dase_conn, "22SYMV000000001", nxt="22SYMV000000002")
    add(dase_conn, "22SYMV000000002")
    add(dase_conn, "22SYMV000000003", cancelled=1)
    rows = dq.coop_contracts(dase_conn, "096000001")
    assert [r["reference_number"] for r in rows] == ["22SYMV000000002"]
    s = dq.coop_summary(dase_conn, "096000001")
    assert s["n_contracts"] == 3 and s["n_live"] == 1


# ---------------------------------------------------------------------------
# queries.list_contracts drive-by guard (no contract_scope table)
# ---------------------------------------------------------------------------

def test_queries_list_contracts_without_scope_table(dase_conn):
    add(dase_conn, "22SYMV000000001", title="ΧΩΡΙΣ SCOPE")
    rows = queries.list_contracts(dase_conn)
    assert len(rows) == 1
    assert rows[0]["scope"] is None


def test_compare_shared_bins_are_log2ish():
    e = dq.COMPARE_BIN_EDGES
    assert e[0] == 0 and e[1] == 1_000
    assert all(e[i + 1] / e[i] <= 2.0 for i in range(1, len(e) - 1))
