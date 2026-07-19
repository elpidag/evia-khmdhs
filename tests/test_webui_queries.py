"""Web-UI query filtering: only in-scope Anti-nero contracts are shown."""
from pathlib import Path

import pytest

from webui import queries

from tests.conftest import add_contract, set_scope


@pytest.fixture
def scoped_conn(mem_conn):
    """3 contracts: one in scope, one non-Anti-nero, one superseded."""
    add_contract(mem_conn, "IN1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("111111111",))
    add_contract(mem_conn, "OUT1", title="ΣΥΝΤΗΡΗΣΗ ΔΑΣΙΚΟΥ ΟΔΙΚΟΥ", eur=50.0,
                 vats=("222222222",))
    add_contract(mem_conn, "OLD1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("111111111",))
    set_scope(mem_conn, "IN1", "antinero_iv", 1)
    set_scope(mem_conn, "OUT1", "non_antinero", 0)
    set_scope(mem_conn, "OLD1", "antinero_iv", 0, superseded_by="IN1")
    return mem_conn


def test_kpis_count_only_in_scope(scoped_conn):
    k = queries.kpis(scoped_conn)
    assert k["n_contracts"] == 1
    assert k["total_eur"] == 100.0
    assert k["n_contractors"] == 1


def test_list_contractors_hides_out_of_scope(scoped_conn):
    rows = queries.list_contractors(scoped_conn)
    vats = {r["vat_number"] for r in rows}
    assert vats == {"111111111"}


def test_contractor_contracts_hides_out_of_scope(scoped_conn):
    refs = {c["reference_number"]
            for c in queries.contractor_contracts(scoped_conn, "111111111")}
    assert refs == {"IN1"}  # OLD1 superseded, not shown


def test_contractor_summary_none_for_out_of_scope_only_vat(scoped_conn):
    assert queries.contractor_summary(scoped_conn, "222222222") is None


def test_contract_detail_still_resolves_out_of_scope(scoped_conn):
    d = queries.contract_detail(scoped_conn, "OUT1")
    assert d is not None
    assert d["scope"]["scope"] == "non_antinero"
    assert d["scope"]["in_scope"] == 0


def test_fallback_without_scope_table(mem_conn):
    # Simulate an older DB: drop the scope table → the VAT-exclusion
    # fallback keeps the UI working.
    mem_conn.executescript("DROP TABLE contract_scope;")
    add_contract(mem_conn, "IN1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("111111111",))
    add_contract(mem_conn, "UMB1", title="ΣΥΜΒΑΣΗ ΤΑΙΠΕΔ", eur=999.0,
                 vats=("997471299",))
    k = queries.kpis(mem_conn)
    assert k["n_contracts"] == 1
    assert k["total_eur"] == 100.0


def test_region_flows_exclude_out_of_scope(scoped_conn):
    # Give both contracts a contractor home + project region, then check
    # only the in-scope contract produces a flow.
    scoped_conn.execute(
        "INSERT INTO contractor_locations (vat_number, region_pe, nuts3_code, source, curated_at) "
        "VALUES ('111111111', 'Π.Ε. Ευβοίας', 'EL642', 'test', '2026-01-01')")
    scoped_conn.execute(
        "INSERT INTO contractor_locations (vat_number, region_pe, nuts3_code, source, curated_at) "
        "VALUES ('222222222', 'Π.Ε. Αχαΐας', 'EL632', 'test', '2026-01-01')")
    for ref in ("IN1", "OUT1", "OLD1"):
        scoped_conn.execute(
            "INSERT INTO contract_project_regions "
            "(reference_number, seq, region_pe, nuts3_code, source, curated_at) "
            f"VALUES ('{ref}', 0, 'Π.Ε. Ευβοίας', 'EL642', 'manual', '2026-01-01')")
    flows = queries.region_flows(scoped_conn)
    assert len(flows) == 1
    assert flows[0]["source_pe"] == "Π.Ε. Ευβοίας"
    assert flows[0]["total_eur"] == 100.0  # OLD1's duplicate 100 not double-counted


# ---------------------------------------------------------------------------
# Integration against the real DB (skipped when it isn't present)
# ---------------------------------------------------------------------------

REAL_DB = Path(__file__).parent.parent / "data" / "processed" / "khmdhs.sqlite"


@pytest.fixture
def real_conn():
    if not REAL_DB.exists():
        pytest.skip("real DB not present")
    conn = queries.open_ro(REAL_DB)
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_scope'"
    ).fetchone():
        pytest.skip("scope table not built")
    yield conn
    conn.close()


def test_real_db_known_classifications(real_conn):
    expected = {
        "22SYMV010473684": ("antinero_i", 0),        # ΕΡΓΟΥ 3.Α — superseded by its amendment
        "22SYMV010856526": ("antinero_i", 1),        # ΕΡΓΟΥ 3.Α amendment (chain_loader)
        "22SYMV010551364": ("antinero_i", 0),        # 3.Γ original, superseded
        "17SYMV002008790": ("non_antinero", 0),      # routine Chalkida 2017
        "24SYMV015978850": ("antinero_support", 0),  # legal support
        "26SYMV018918969": ("antinero_umbrella", 0), # ΕΕΣΥΠ III framework
        "23SYMV013201961": ("antinero_ii", 1),       # 'IIΙ' glyphs, 2021ΤΑ fund
        "24SYMV014333324": ("antinero_iii", 1),      # 'IIΙ' glyphs, 2023ΤΑ fund
    }
    for ref, (scope, in_scope) in expected.items():
        row = real_conn.execute(
            "SELECT scope, in_scope FROM contract_scope WHERE reference_number = ?",
            (ref,)).fetchone()
        assert row is not None, ref
        assert (row["scope"], row["in_scope"]) == (scope, in_scope), ref


def test_real_db_every_displayed_contract_is_antinero(real_conn):
    rows = real_conn.execute("""
        SELECT s.scope, k.title FROM contract_scope s
        JOIN contracts k USING (reference_number) WHERE s.in_scope = 1
    """).fetchall()
    assert rows
    from khmdhs.scope import IN_SCOPE
    for r in rows:
        assert r["scope"] in IN_SCOPE, r["title"]


def test_real_db_dashboard_matches_scope_table(real_conn):
    k = queries.kpis(real_conn)
    n = real_conn.execute(
        "SELECT COUNT(*) FROM contract_scope WHERE in_scope = 1").fetchone()[0]
    assert k["n_contracts"] == n


# ---------------------------------------------------------------------------
# Contracts list / search
# ---------------------------------------------------------------------------

def test_search_norm_accent_case_homoglyphs():
    assert queries._search_norm("Ευβοίας") == queries._search_norm("ευβοιας")
    # Greek-typed ΑΝΤΙΝΕΡΟ matches Latin ANTINERO after normalisation
    assert queries._search_norm("αντινερο") in queries._search_norm("ΕΡΓΟ ANTINERO IV")


def test_list_contracts_search(scoped_conn):
    scoped_conn.execute(
        "INSERT INTO contract_project_regions "
        "(reference_number, seq, region_pe, nuts3_code, source, curated_at) "
        "VALUES ('IN1', 0, 'Π.Ε. Ευβοίας', 'EL642', 'manual', '2026-01-01')")
    all_rows = queries.list_contracts(scoped_conn)
    assert {r["reference_number"] for r in all_rows} == {"IN1"}  # only in-scope

    by_region = queries.list_contracts(scoped_conn, q="ευβοιας")
    assert len(by_region) == 1
    by_adam = queries.list_contracts(scoped_conn, q="IN1")
    assert len(by_adam) == 1
    by_title = queries.list_contracts(scoped_conn, q="antinero")
    assert len(by_title) == 1
    no_hit = queries.list_contracts(scoped_conn, q="ΞΞΞ-nothing")
    assert no_hit == []


def test_real_db_contracts_search_eyboia(real_conn):
    rows = queries.list_contracts(real_conn, q="Ευβοίας")
    assert rows, "expected Evia contracts"
    # the two new Anti-nero IV Evia contracts must be findable
    refs = {r["reference_number"] for r in rows}
    assert {"25SYMV017458228", "25SYMV017458229"} <= refs
