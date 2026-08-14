"""Unit tests for atlas_api/queries_extra.py on synthetic DBs.

Also pins the behaviour of the private webui helpers atlas relies on
(q._payment_month via _full_date parity, even-split conventions) so a future
webui refactor fails loudly here instead of silently skewing charts.
"""
import sqlite3

import pytest

from atlas_api import queries_extra as qx
from khmdhs.db import SCHEMA_SQL
from khmdhs.scope_loader import SCHEMA as SCOPE_SCHEMA
from tests.conftest import add_contract, add_payment, set_scope


@pytest.fixture
def kh(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCOPE_SCHEMA)
    yield conn
    conn.close()


def _region(conn, ref, pe, seq=0):
    conn.execute(
        "INSERT INTO contract_project_regions "
        "(reference_number, seq, region_pe, source, curated_at) "
        "VALUES (?,?,?, 'test', '2026-01-01')", (ref, seq, pe))


# ------------------------------------------------------------- _full_date

@pytest.mark.parametrize("raw,expected", [
    ("2026-07-24T00:00:00", "2026-07-24"),
    ("03/11/2023", "2023-11-03"),
    ("2026-07-24", "2026-07-24"),
    (None, None),
    ("", None),
    ("garbage", None),
])
def test_full_date_formats(raw, expected):
    assert qx._full_date(raw) == expected


def test_full_date_agrees_with_payment_month():
    """Pin: day-level normalisation must agree with q._payment_month at
    month level for every format the registry has produced."""
    from webui.queries import _payment_month
    for raw in ("2026-07-24T00:00:00", "03/11/2023", None, "x"):
        d = qx._full_date(raw)
        assert (d[:7] if d else None) == _payment_month(raw)


# --------------------------------------------------------- payment_events

def test_payment_events_dates_fallback_and_undated(kh):
    add_contract(kh, "22SYMV000000001", title="ANTINERO II", eur=100.0)
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    add_payment(kh, "23PAY000000001", "22SYMV000000001", 10.0,
                signed_date="2026-07-24T00:00:00")
    add_payment(kh, "23PAY000000002", "22SYMV000000001", 20.0,
                signed_date="03/11/2023")
    add_payment(kh, "23PAY000000003", "22SYMV000000001", 30.0,
                signed_date=None)  # submission fallback (conftest sets none)
    add_payment(kh, "23PAY000000004", "22SYMV000000001", 40.0, cancelled=1)
    # out-of-scope payment must not appear
    add_contract(kh, "22SYMV000000002", title="ΑΣΧΕΤΟ", eur=50.0)
    set_scope(kh, "22SYMV000000002", "non_antinero", 0)
    add_payment(kh, "23PAY000000005", "22SYMV000000002", 5.0)
    kh.commit()

    out = qx.payment_events(kh)
    pays = {e["pay"]: e for e in out["events"]}
    assert set(pays) == {"23PAY000000001", "23PAY000000002", "23PAY000000003"}
    assert pays["23PAY000000001"]["d"] == "2026-07-24"
    assert pays["23PAY000000002"]["d"] == "2023-11-03"
    assert pays["23PAY000000002"]["m"] == "2023-11"
    # no signed_date and no submission_date in the fixture → undated
    assert pays["23PAY000000003"]["d"] is None
    assert out["undated"] == {"n": 1, "eur": 30.0}
    assert out["contracts"]["22SYMV000000001"]["vats"] == ["111111111"]


# ----------------------------------------------------------------- sankey

def test_sankey_conserves_money_and_splits_consortiums(kh):
    add_contract(kh, "22SYMV000000001", title="A", eur=100.0,
                 vats=("111111111", "222222222"))  # consortium, no payments
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    add_contract(kh, "23SYMV000000002", title="B", eur=999.0,
                 vats=("111111111",))
    set_scope(kh, "23SYMV000000002", "antinero_iii", 1)
    add_payment(kh, "23PAY000000001", "23SYMV000000002", 400.0)  # effective=400
    kh.commit()

    out = qx.sankey_flows(kh, top_n=1)
    total = 100.0 + 400.0
    ministry_out = sum(l["eur"] for l in out["links"] if l["s"] == "ministry")
    contractor_in = sum(l["eur"] for l in out["links"]
                        if l["s"] not in ("ministry",))
    assert ministry_out == pytest.approx(total)
    assert contractor_in == pytest.approx(total)
    # top-1 contractor is 111111111 with 50 + 400 = 450 even-split
    top_in = sum(l["eur"] for l in out["links"] if l["t"] == "111111111")
    assert top_in == pytest.approx(450.0)
    rest_in = sum(l["eur"] for l in out["links"] if l["t"] == "rest")
    assert rest_in == pytest.approx(50.0)
    kinds = {n["kind"] for n in out["nodes"]}
    assert kinds == {"ministry", "phase", "contractor", "rest"}


# ------------------------------------------------------------------ swarm

def test_contract_swarm_fields(kh):
    add_contract(kh, "22SYMV000000001", title="Τ" * 100, eur=100.0)
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    _region(kh, "22SYMV000000001", "Π.Ε. Πρεβέζης")  # alias → canonical
    add_contract(kh, "22SYMV000000002", title="OUT", eur=5.0)
    set_scope(kh, "22SYMV000000002", "non_antinero", 0)
    kh.commit()

    rows = qx.contract_swarm(kh)
    assert len(rows) == 1
    r = rows[0]
    assert r["ref"] == "22SYMV000000001"
    assert r["t"].endswith("…") and len(r["t"]) == 81
    assert r["proc"] == "direct"           # conftest procedure Απευθείας ανάθεση
    assert r["single_bidder"] == 1         # conftest bids_submitted = 1
    assert r["pe"] == "Π.Ε. Πρέβεζας"      # canonicalised
    assert r["year"] is None or len(r["year"]) == 4


@pytest.mark.parametrize("proc,kind", [
    ("Απευθείας ανάθεση", "direct"),
    ("ΑΠΕΥΘΕΊΑΣ ΑΝΆΘΕΣΗ", "direct"),
    ("Ανοιχτή διαδικασία", "open"),
    ("Ανοικτός διαγωνισμός", "open"),
    ("Διαπραγμάτευση χωρίς προηγούμενη δημοσίευση", "nego"),
    (None, "other"),
    ("Συνοπτικός διαγωνισμός", "other"),
])
def test_proc_kind(proc, kind):
    assert qx._proc_kind(proc) == kind


# -------------------------------------------------------------- pipelines

def test_pipelines_zero_overlap_and_name_grouped_awarders(kh):
    """VAT sets disjoint; awarders join by NAME so the 090273987 collision
    (ΥΠΕΝ vs ΑΠΔ rows sharing a VAT) can never produce a false bridge."""
    from khmdhs.db import SCHEMA_SQL as S
    dase = sqlite3.connect(":memory:")
    dase.row_factory = sqlite3.Row
    dase.executescript(S)
    dase.executescript("""
        CREATE TABLE dase_contractors (
            vat_number TEXT PRIMARY KEY, name TEXT NOT NULL, form TEXT,
            basis TEXT, curated_at TEXT NOT NULL);
    """)
    from tests.test_dase_queries import add as add_dase, curate
    curate(dase, "096000001", name="ΔΑΣΕ ΤΕΣΤ")
    add_dase(dase, "23SYMV000000009", eur=5_000.0, title="ΥΛΟΤΟΜΙΑ",
             org="ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ")

    add_contract(kh, "22SYMV000000001", title="ANTINERO II", eur=100.0,
                 org="ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ  ΚΑΙ ΕΝΕΡΓΕΙΑΣ",  # ws variant
                 vats=("111111111", "222222222"))
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    kh.commit()
    dase.commit()

    out = qx.pipelines(kh, dase)
    assert out["vat_overlap"] == []
    assert out["antinero"]["n_vats"] == 2
    assert out["antinero"]["total_eur"] == pytest.approx(100.0)  # even-split sums back
    assert out["dase"]["total_eur"] == pytest.approx(5_000.0)
    # whitespace-variant ministry names still bridge (name-key, never VAT)
    assert len(out["shared_awarders"]) == 1
    assert out["shared_awarders"][0]["antinero_n"] == 1
    assert out["shared_awarders"][0]["dase_n"] == 1
    dase.close()


# -------------------------------------------------------------- pe-yearly

def test_money_by_pe_yearly_splits_and_buckets(kh):
    # contract with payments in two years, split across two Π.Ε.
    add_contract(kh, "22SYMV000000001", title="A", eur=1000.0)
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    _region(kh, "22SYMV000000001", "Π.Ε. Ευβοίας", 0)
    _region(kh, "22SYMV000000001", "Π.Ε. Φθιώτιδας", 1)
    add_payment(kh, "23PAY000000001", "22SYMV000000001", 100.0,
                signed_date="2023-05-01")
    add_payment(kh, "24PAY000000002", "22SYMV000000001", 60.0,
                signed_date="2024-05-01")
    # zero-payment contract → stated at signature year (conftest has no
    # signed date → unresolved bucket)
    add_contract(kh, "22SYMV000000002", title="B", eur=500.0)
    set_scope(kh, "22SYMV000000002", "antinero_ii", 1)
    _region(kh, "22SYMV000000002", "Π.Ε. Ευβοίας")
    kh.commit()

    out = qx.money_by_pe_yearly(kh)
    by_pe = {p["pe"]: p for p in out["pes"]}
    assert by_pe["Π.Ε. Ευβοίας"]["years"] == {"2023": 50.0, "2024": 30.0}
    assert by_pe["Π.Ε. Φθιώτιδας"]["total_eur"] == pytest.approx(80.0)
    assert out["years"] == ["2023", "2024"]
    # contract B has no parsable date → honestly unresolved
    assert out["unresolved_eur"] == pytest.approx(500.0)


# ------------------------------------------------------------------ cpvs

def _cpv(conn, ref, code, desc, seq=0):
    conn.execute(
        "INSERT INTO contract_cpvs (reference_number, seq, cpv_code, cpv_description) "
        "VALUES (?,?,?,?)", (ref, seq, code, desc))


def test_antinero_cpvs_counts_in_scope_contracts_once(kh):
    add_contract(kh, "22SYMV000000001", title="A")
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    add_contract(kh, "22SYMV000000002", title="B")
    set_scope(kh, "22SYMV000000002", "antinero_ii", 1)
    add_contract(kh, "22SYMV000000003", title="OUT")
    set_scope(kh, "22SYMV000000003", "non_antinero", 0)
    # shared code on both in-scope contracts; A declares it twice (two lots)
    _cpv(kh, "22SYMV000000001", "77231300-1", "Υπηρεσίες διαχείρισης δασών", 0)
    _cpv(kh, "22SYMV000000001", "77231300-1", "Υπηρεσίες διαχείρισης δασών", 1)
    _cpv(kh, "22SYMV000000002", "77231300-1", "Υπηρεσίες διαχείρισης δασών", 0)
    # code unique to B
    _cpv(kh, "22SYMV000000002", "45233120-6", "Έργα οδοποιίας", 1)
    # code only on the out-of-scope contract → excluded entirely
    _cpv(kh, "22SYMV000000003", "66519300-4", "Ασφαλιστικές υπηρεσίες", 0)
    kh.commit()

    rows = qx.antinero_cpvs(kh)
    assert [(r["code"], r["desc"], r["n"]) for r in rows] == [
        ("77231300-1", "Υπηρεσίες διαχείρισης δασών", 2),
        ("45233120-6", "Έργα οδοποιίας", 1),
    ]


def test_antinero_overview_includes_cpvs(kh):
    add_contract(kh, "22SYMV000000001", title="A")
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    _cpv(kh, "22SYMV000000001", "77231300-1", "Υπηρεσίες διαχείρισης δασών")
    kh.commit()
    out = qx.antinero_overview(kh)
    assert out["cpvs"][0]["code"] == "77231300-1"


# ------------------------------------------------------------- categories

def _categorize(conn, ref, cat, title="T", source="pdf"):
    conn.execute(
        "INSERT INTO contract_categories "
        "(reference_number, category, title, source, curated_at) "
        "VALUES (?,?,?,?, '2026-01-01')", (ref, cat, title, source))


def test_antinero_categories_groups_and_reconciles(kh):
    kh.execute("INSERT INTO category_labels (category, label, note) VALUES "
               "('dasotexnika', 'Δασοτεχνικά έργα πρόληψης', NULL), "
               "('meletes', 'Μελέτες', NULL)")
    add_contract(kh, "22SYMV000000001", title="A", eur=1000.0)
    set_scope(kh, "22SYMV000000001", "antinero_ii", 1)
    _categorize(kh, "22SYMV000000001", "dasotexnika")
    add_contract(kh, "22SYMV000000002", title="B", eur=600.0)
    set_scope(kh, "22SYMV000000002", "antinero_ii", 1)
    _categorize(kh, "22SYMV000000002", "dasotexnika")
    add_contract(kh, "22SYMV000000003", title="C", eur=250.0)
    set_scope(kh, "22SYMV000000003", "antinero_iii", 1)
    _categorize(kh, "22SYMV000000003", "meletes")
    # out of scope: categorized rows outside the basis never count
    add_contract(kh, "22SYMV000000004", title="D", eur=99.0)
    set_scope(kh, "22SYMV000000004", "non_antinero", 0)
    _categorize(kh, "22SYMV000000004", "meletes")
    kh.commit()

    rows = qx.antinero_categories(kh)
    assert [(r["key"], r["label"], r["n"], r["eur"]) for r in rows] == [
        ("dasotexnika", "Δασοτεχνικά έργα πρόληψης", 2, 1600.0),
        ("meletes", "Μελέτες", 1, 250.0),
    ]
    # single-category convention: Σ over categories == the in-scope total
    total = kh.execute(
        "SELECT SUM(total_cost_with_vat) FROM contracts k "
        "JOIN contract_scope s ON s.reference_number = k.reference_number "
        "WHERE s.in_scope = 1").fetchone()[0]
    assert sum(r["eur"] for r in rows) == pytest.approx(total)
    assert "categories" in qx.antinero_overview(kh)


def test_contract_category_detail_supplement(kh):
    kh.execute("INSERT INTO category_labels (category, label, note) VALUES "
               "('ylotomies', 'Υλοτομίες', 'σημ')")
    add_contract(kh, "22SYMV000000001", title="A")
    _categorize(kh, "22SYMV000000001", "ylotomies",
                title="Επείγουσες υλοτομικές εργασίες",
                source="inherited:22SYMV000000009")
    kh.commit()
    got = qx.contract_category(kh, "22SYMV000000001")
    assert got == {"key": "ylotomies", "label": "Υλοτομίες", "note": "σημ",
                   "title": "Επείγουσες υλοτομικές εργασίες",
                   "source": "inherited:22SYMV000000009"}
    assert qx.contract_category(kh, "22SYMV000000002") is None
