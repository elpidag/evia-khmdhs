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


# ---------------------------------------------------------------------------
# Greeklish search + dashboard analytics
# ---------------------------------------------------------------------------

def test_phonetic_fold_greeklish_pairs():
    for greek, latin in (("Ευβοίας", "evias"), ("Χαλκίδας", "xalkidas"),
                         ("Θεσσαλονίκης", "thessalonikis"), ("Ηλείας", "ilias")):
        g = queries._phonetic_fold(queries._search_norm(greek))
        l = queries._phonetic_fold(queries._search_norm(latin))
        assert l in g, (greek, latin, g, l)


def test_list_contracts_greeklish(scoped_conn):
    scoped_conn.execute(
        "INSERT INTO contract_project_regions "
        "(reference_number, seq, region_pe, nuts3_code, source, curated_at) "
        "VALUES ('IN1', 0, 'Π.Ε. Ευβοίας', 'EL642', 'manual', '2026-01-01')")
    assert len(queries.list_contracts(scoped_conn, q="evias")) == 1
    assert len(queries.list_contracts(scoped_conn, q="antinero iv")) == 1


def test_payment_month_formats():
    assert queries._payment_month("03/11/2023") == "2023-11"
    assert queries._payment_month("2026-07-24T00:00:00") == "2026-07"
    assert queries._payment_month(None) is None
    assert queries._payment_month("garbage") is None


def test_disbursement_timeseries(scoped_conn):
    from tests.conftest import add_payment
    add_payment(scoped_conn, "22PAY000000001", "IN1", 60.0,
                signed_date="03/11/2023")
    add_payment(scoped_conn, "22PAY000000002", "IN1", 40.0,
                signed_date="2024-01-05T00:00:00")
    add_payment(scoped_conn, "22PAY000000003", "IN1", 99.0,
                signed_date=None)  # undated → footnote, not on curve
    # unsigned but registered → submission_date fallback puts it on the curve
    scoped_conn.execute(
        "INSERT INTO contract_payments (payment_ref, contract_ref, attributed_ref, "
        "signed_date, submission_date, cancelled, credit, amount_with_vat, fetched_at) "
        "VALUES ('22PAY000000004', 'IN1', 'IN1', NULL, '2024-02-10T09:00:00', 0, 0, 5.0, 'x')")
    ts = queries.disbursement_timeseries(scoped_conn)
    assert ts["months"] == ["2023-11", "2024-01", "2024-02"]
    assert ts["series"]["antinero_iv"] == [60.0, 100.0, 105.0]  # cumulative
    assert ts["undated"] == 1 and ts["undated_eur"] == 99.0


def test_direct_award_distribution(scoped_conn):
    scoped_conn.execute(
        "UPDATE contracts SET procedure_type = 'Απευθείας ανάθεση' "
        "WHERE reference_number = 'IN1'")
    da = queries.direct_award_distribution(scoped_conn)
    assert da["n"] == 1
    assert sum(da["counts"]) == 1
    assert da["thresholds"] == [30_000, 60_000]
    # IN1 costs €100 → first bin (0–10k)
    assert da["counts"][0] == 1


# ---------------------------------------------------------------------------
# Overview page: even-split money geography + structure charts
# ---------------------------------------------------------------------------

def _add_region(conn, ref, pe, nuts3, seq=0):
    conn.execute(
        "INSERT INTO contract_project_regions "
        "(reference_number, seq, region_pe, nuts3_code, source, curated_at) "
        "VALUES (?, ?, ?, ?, 'manual', '2026-01-01')", (ref, seq, pe, nuts3))


def test_money_by_project_region_split_invariant(scoped_conn):
    # IN1 (€100) spans two regions → €50 each; totals sum back to €100.
    _add_region(scoped_conn, "IN1", "Π.Ε. Ευβοίας", "EL642", 0)
    _add_region(scoped_conn, "IN1", "Π.Ε. Βοιωτίας", "EL641", 1)
    rows = queries.money_by_project_region(scoped_conn)
    assert {r["pe"]: r["split_eur"] for r in rows} == {
        "Π.Ε. Ευβοίας": 50.0, "Π.Ε. Βοιωτίας": 50.0}
    for r in rows:
        assert r["exposure_eur"] == 100.0 and r["n_contracts"] == 1
    assert sum(r["split_eur"] for r in rows) == 100.0


def test_money_by_project_region_distinct_pe_stay_separate(scoped_conn):
    # Άρτας + Πρέβεζας share NUTS-3 EL541 but are distinct Π.Ε. — since the
    # maps moved to Π.Ε. polygons they must NOT merge (DATA_DECISIONS
    # 2026-07-26).
    _add_region(scoped_conn, "IN1", "Π.Ε. Άρτας", "EL541", 0)
    _add_region(scoped_conn, "IN1", "Π.Ε. Πρέβεζας", "EL541", 1)
    rows = queries.money_by_project_region(scoped_conn)
    assert {r["pe"]: r["split_eur"] for r in rows} == {
        "Π.Ε. Άρτας": 50.0, "Π.Ε. Πρέβεζας": 50.0}
    for r in rows:
        assert r["exposure_eur"] == 100.0 and r["n_contracts"] == 1


def test_money_by_project_region_alias_spellings_merge(scoped_conn):
    # Spelling variants of the SAME Π.Ε. collapse onto the canonical name.
    _add_region(scoped_conn, "IN1", "Π.Ε. Πρέβεζας", "EL541", 0)
    _add_region(scoped_conn, "IN1", "Π.Ε. Πρεβέζης", "EL541", 1)
    rows = queries.money_by_project_region(scoped_conn)
    assert len(rows) == 1
    r = rows[0]
    assert r["pe"] == "Π.Ε. Πρέβεζας"
    assert r["split_eur"] == 100.0 and r["exposure_eur"] == 100.0


def test_money_by_contractor_region_consortium_split(mem_conn):
    from tests.conftest import add_contract, set_scope
    add_contract(mem_conn, "C1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("111111111", "222222222"))
    set_scope(mem_conn, "C1", "antinero_iv", 1)
    for vat, pe, nuts in (("111111111", "Π.Ε. Ευβοίας", "EL642"),
                          ("222222222", "Π.Ε. Αχαΐας", "EL632")):
        mem_conn.execute(
            "INSERT INTO contractor_locations (vat_number, region_pe, nuts3_code, source, curated_at) "
            "VALUES (?, ?, ?, 'test', '2026-01-01')", (vat, pe, nuts))
    rows = queries.money_by_contractor_region(mem_conn)
    assert {r["pe"]: r["split_eur"] for r in rows} == {
        "Π.Ε. Ευβοίας": 50.0, "Π.Ε. Αχαΐας": 50.0}
    for r in rows:
        assert r["exposure_eur"] == 100.0 and r["n_contractors"] == 1


def test_money_by_contractor_region_unlocated_partner(mem_conn):
    from tests.conftest import add_contract, set_scope
    # One located + one unlocated partner → located home carries the full value
    # (the unlocated share is what flow_coverage reports as unresolved).
    add_contract(mem_conn, "C1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("111111111", "222222222"))
    set_scope(mem_conn, "C1", "antinero_iv", 1)
    mem_conn.execute(
        "INSERT INTO contractor_locations (vat_number, region_pe, nuts3_code, source, curated_at) "
        "VALUES ('111111111', 'Π.Ε. Ευβοίας', 'EL642', 'test', '2026-01-01')")
    rows = queries.money_by_contractor_region(mem_conn)
    assert len(rows) == 1 and rows[0]["split_eur"] == 100.0


def test_procedure_mix_groups_variants(scoped_conn):
    scoped_conn.execute("UPDATE contracts SET procedure_type = "
                        "'Απευθείας ανάθεση (αρ.118/αρ. 328)' WHERE reference_number = 'IN1'")
    mix = queries.procedure_mix(scoped_conn)
    assert mix[0]["label"] == "Απευθείας ανάθεση"
    assert mix[0]["n_contracts"] == 1 and mix[0]["eur"] == 100.0


def test_bin_values_helper():
    h = queries._bin_values([5, 15, 999], (0, 10, 100))
    assert h["counts"] == [1, 1, 1]  # [0,10): 5 · [10,100): 15 · overflow: 999
    assert h["n"] == 3


def test_contractor_yearly_paid_and_stated(scoped_conn):
    from tests.conftest import add_contract, add_payment, set_scope
    add_payment(scoped_conn, "24PAY000000001", "IN1", 60.0, signed_date="03/11/2023")
    add_payment(scoped_conn, "24PAY000000002", "IN1", 40.0, signed_date="2024-01-05T00:00:00")
    # a second contract for the same VAT with no payments → stated in its year
    add_contract(scoped_conn, "IN2", title="ΕΡΓΟ ANTINERO IV Β", eur=200.0,
                 vats=("111111111",))
    set_scope(scoped_conn, "IN2", "antinero_iv", 1)
    scoped_conn.execute("UPDATE contracts SET contract_signed_date = '2025-06-01T00:00:00' "
                        "WHERE reference_number = 'IN2'")
    y = queries.contractor_yearly(scoped_conn, "111111111")
    by_year = {b["year"]: b for b in y["years"]}
    assert by_year["2023"]["paid_eur"] == 60.0
    assert by_year["2024"]["paid_eur"] == 40.0
    assert by_year["2025"]["stated_eur"] == 200.0 and by_year["2025"]["paid_eur"] == 0.0


def test_contractor_map_data_split(scoped_conn):
    _add_region(scoped_conn, "IN1", "Π.Ε. Ευβοίας", "EL642", 0)
    _add_region(scoped_conn, "IN1", "Π.Ε. Βοιωτίας", "EL641", 1)
    md = queries.contractor_map_data(scoped_conn, "111111111")
    assert {r["pe"]: r["split_eur"] for r in md["regions"]} == {
        "Π.Ε. Ευβοίας": 50.0, "Π.Ε. Βοιωτίας": 50.0}


def test_gemi_pick_seat_hit_prefers_seat_over_branch():
    from khmdhs.gemi import pick_seat_hit
    hits = [
        {"afm": "099124894", "gemiNumber": "44614807001",
         "name": "ΖΙΤΑΚΑΤ ΑΝΩΝΥΜΗ ΤΕΧΝΙΚΗ (Υποκατάστημα)"},
        {"afm": "099124894", "gemiNumber": "44614807000",
         "name": "ΖΙΤΑΚΑΤ ΑΝΩΝΥΜΗ ΤΕΧΝΙΚΗ"},
    ]
    # Branch listed first (the real ΖΙΤΑΚΑΤ ordering) → seat still wins
    assert pick_seat_hit(hits, "099124894")["gemiNumber"] == "44614807000"
    # Only a branch exists → fall back to it rather than returning nothing
    assert pick_seat_hit(hits[:1], "099124894")["gemiNumber"] == "44614807001"
    # Wrong ΑΦΜ → no hit
    assert pick_seat_hit(hits, "000000000") is None


def _add_authority(conn, name="Δασαρχείο Πύργου", kind="dx",
                   lat=37.7, lon=21.49, pe="Π.Ε. Ηλείας"):
    conn.execute(
        "INSERT OR REPLACE INTO forest_authorities "
        "(name, kind, seat_city, municipality_code, municipality_name, lat, lon, region_pe) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (name, kind, "Πύργος", "9141", "Πύργου", lat, lon, pe))


def _link_authority(conn, ref, name="Δασαρχείο Πύργου", seq=0):
    conn.execute(
        "INSERT INTO contract_forest_authorities "
        "(reference_number, seq, authority_name, source, excerpt) "
        "VALUES (?,?,?, 'text', 'test')", (ref, seq, name))


def test_contract_authority_points_scope_and_shape(scoped_conn):
    _add_authority(scoped_conn)
    _link_authority(scoped_conn, "IN1")
    _link_authority(scoped_conn, "OUT1")   # out of scope — must not appear
    pts = queries.contract_authority_points(scoped_conn)
    assert [p["ref"] for p in pts] == ["IN1"]
    p = pts[0]
    assert p["authority"] == "Δασαρχείο Πύργου" and p["kind"] == "dx"
    assert p["lat"] == 37.7 and p["pe"] == "Π.Ε. Ηλείας"
    assert p["eff_eur"] == 100.0


def test_contractor_points_coords_and_coverage(scoped_conn):
    # located with coords
    scoped_conn.execute(
        "INSERT INTO contractor_locations (vat_number, legal_name, region_pe, "
        "nuts3_code, lat, lon, geo_precision, source, curated_at) "
        "VALUES ('111111111', 'ΕΡΓΟΛΑΒΟΣ ΑΕ', 'Π.Ε. Ευβοίας', 'EL642', "
        "38.46, 23.6, 'address', 'vies', '2026-01-01')")
    # a second in-scope contract whose contractor has NO coords
    add_contract(scoped_conn, "IN2", title="ΕΡΓΟ ANTINERO IV", eur=70.0,
                 vats=("333333333",))
    set_scope(scoped_conn, "IN2", "antinero_iv", 1)
    res = queries.contractor_points(scoped_conn)
    assert [p["vat"] for p in res["points"]] == ["111111111"]
    p = res["points"][0]
    assert p["name"] == "ΕΡΓΟΛΑΒΟΣ ΑΕ" and p["precision"] == "address"
    assert p["n_contracts"] == 1 and p["total_eur"] == 100.0
    cov = res["coverage"]
    assert cov["n_with_coords"] == 1 and cov["n_total"] == 2
    assert cov["unmapped_eur"] == 70.0


def test_overview_contracts_shape_and_splits(scoped_conn):
    _add_authority(scoped_conn)
    _link_authority(scoped_conn, "IN1")
    _add_region(scoped_conn, "IN1", "Π.Ε. Ευβοίας", "EL642", 0)
    _add_region(scoped_conn, "IN1", "Π.Ε. Βοιωτίας", "EL641", 1)
    cs = queries.overview_contracts(scoped_conn)
    assert [c["ref"] for c in cs] == ["IN1"]        # OUT1/OLD1 filtered
    c = cs[0]
    assert c["eff_eur"] == 100.0
    assert c["authorities"] == ["Δασαρχείο Πύργου"]
    assert [x["vat"] for x in c["contractors"]] == ["111111111"]
    assert {r["pe"]: r["split_eur"] for r in c["regions"]} == {
        "Π.Ε. Ευβοίας": 50.0, "Π.Ε. Βοιωτίας": 50.0}
    assert sum(r["split_eur"] for r in c["regions"]) == c["eff_eur"]


def test_overview_contracts_name_falls_back_to_contractors_table(scoped_conn):
    cs = queries.overview_contracts(scoped_conn)
    assert cs[0]["contractors"][0]["name"] == "CONTRACTOR 111111111"


def test_contract_authority_points_canonicalize_pe(scoped_conn):
    # An alias spelling in the registry still yields the canonical Π.Ε. key.
    _add_authority(scoped_conn, pe="Π.Ε. Πρεβέζης")
    _link_authority(scoped_conn, "IN1")
    pts = queries.contract_authority_points(scoped_conn)
    assert pts[0]["pe"] == "Π.Ε. Πρέβεζας"
