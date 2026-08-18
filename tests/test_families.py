"""Procurement families derived from the contracts' own texts."""
import sqlite3

import pytest

from khmdhs import db
from khmdhs.families_loader import citations, load
from tests.conftest import add_contract

PROC = "24PROC014447893"


def _cache(tmp_path, texts):
    d = tmp_path / "cache"
    d.mkdir()
    for ref, t in texts.items():
        (d / f"{ref}.txt").write_text(t, encoding="utf-8")
    return d


def test_citations_reads_kind_and_role():
    t = ("…της Πρόσκλησης (ΑΔΑΜ: 24PROC014244123 2024-02-09), καθώς και την από "
         "15.02.2024 Απόφαση Τροποποίησης της ως άνω Πρόσκλησης "
         "(ΑΔΑΜ: 24PROC014272456), και την κατακύρωση 24AWRD014286548.")
    got = {(a, k, r) for a, k, r, _ in citations(t)}
    assert ("24PROC014244123", "notice", "procurement") in got
    # the second call is that call's own amendment, never a rival family
    assert ("24PROC014272456", "notice", "amendment") in got
    assert ("24AWRD014286548", "auction", "award") in got


def test_every_row_carries_the_sentence_that_proves_it():
    t = "όπως ορίζεται στην Πρόσκληση με ΑΔΑΜ: 24PROC014447893 2024-03-01 του ΤΑΙΠΕΔ."
    for adam, _, _, excerpt in citations(t):
        assert adam in excerpt and len(excerpt) > len(adam)


def test_title_lot_labels_are_never_used(tmp_path):
    """Grouping «ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 11Α» with «11Β» would invent a
    family: 21 of 59 such labels repeat across programme years. Only a
    cited ΑΔΑΜ counts (DATA_DECISIONS 2026-08-18)."""
    conn = db.init_db(tmp_path / "t.sqlite")
    add_contract(conn, "24SYMV000000001", title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 11Α")
    add_contract(conn, "24SYMV000000002", title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 11Β")
    conn.commit()
    cache = _cache(tmp_path, {"24SYMV000000001": "ΕΡΓΟΥ 11Α, no ΑΔΑΜ here.",
                              "24SYMV000000002": "ΕΡΓΟΥ 11Β, no ΑΔΑΜ here."})
    s = load(conn, cache)
    assert s["rows"] == 0 and s["none"] == 2
    conn.close()


def test_amendment_inherits_its_predecessors_family(tmp_path):
    conn = db.init_db(tmp_path / "t.sqlite")
    add_contract(conn, "22SYMV000000001")
    add_contract(conn, "22SYMV000000002", prev="22SYMV000000001")
    conn.commit()
    cache = _cache(tmp_path, {
        "22SYMV000000001": f"σύμφωνα με την Πρόσκληση (ΑΔΑΜ: {PROC} 2024-03-01).",
        "22SYMV000000002": "τροποποίηση της αρχικής σύμβασης, χωρίς ΑΔΑΜ πρόσκλησης."})
    load(conn, cache)
    rows = dict(conn.execute(
        "SELECT reference_number, source FROM contract_families WHERE kind='notice'"))
    assert rows["22SYMV000000001"] == "text"
    assert rows["22SYMV000000002"] == "inherited:22SYMV000000001"
    conn.close()


def test_idempotent_and_cascade_safe(tmp_path):
    conn = db.init_db(tmp_path / "t.sqlite")
    add_contract(conn, "22SYMV000000001")
    conn.commit()
    cache = _cache(tmp_path, {"22SYMV000000001": f"Πρόσκληση ΑΔΑΜ: {PROC}."})
    load(conn, cache)
    load(conn, cache)
    n, = conn.execute("SELECT COUNT(*) FROM contract_families").fetchone()
    assert n == 1
    # a contract refetch cascades its family rows away; the loader rebuilds
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("DELETE FROM contracts WHERE reference_number='22SYMV000000001'")
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM contract_families").fetchone()[0] == 0
    conn.close()


# --------------------------------------------------------- real-DB pins

DB = __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "processed" / "khmdhs.sqlite"


@pytest.fixture(scope="module")
def kh():
    if not DB.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    c = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_real_db_family_coverage(kh):
    """219 of the 245 in-scope contracts sit in a procurement family; the
    rest are direct awards or negotiations, which publish no call. The 134
    families count a call ONCE: a second ΑΔΑΜ whose citing sentence says
    «Τροποποίησης» is that call amended, not a rival family."""
    rows = kh.execute("""
        SELECT COUNT(DISTINCT f.reference_number) FROM contract_families f
        JOIN contract_scope s ON s.reference_number = f.reference_number
        WHERE s.in_scope = 1 AND f.kind = 'notice'""").fetchone()[0]
    assert rows == 220
    fams = kh.execute("""
        SELECT COUNT(DISTINCT f.adam) FROM contract_families f
        JOIN contract_scope s ON s.reference_number = f.reference_number
        WHERE s.in_scope = 1 AND f.kind = 'notice' AND f.role = 'procurement'
        """).fetchone()[0]
    assert fams == 134


def test_real_db_every_family_row_quotes_its_source(kh):
    """No row without the sentence that cites it, and the ΑΔΑΜ must appear
    inside that sentence — the rule that keeps this layer evidence-based."""
    for r in kh.execute("SELECT adam, excerpt, kind, role, source FROM contract_families"):
        assert r["adam"] in r["excerpt"], r["adam"]
        assert r["kind"] in ("notice", "auction")
        assert r["role"] in ("procurement", "amendment", "award")
        assert r["source"] == "text" or r["source"].startswith("inherited:")


def test_real_db_the_eight_lot_family(kh):
    """24PROC014447893 — «Δημιουργία Μικτών Αντιπυρικών Ζωνών», the family
    whose sibling comparison exposed the €31M project-budget error: eight
    lots, one per Δασαρχείο, none of them known to the ΚΗΜΔΗΣ chain."""
    refs = [r[0] for r in kh.execute(
        "SELECT reference_number FROM contract_families WHERE adam = ?"
        " AND role = 'procurement'", ("24PROC014447893",))]
    assert len(refs) == 8
    assert "24SYMV015544651" in refs                  # the corrected one
    declared = kh.execute(
        "SELECT COUNT(*) FROM contract_linked_acts WHERE adam = ?",
        ("24PROC014447893",)).fetchone()[0]
    assert declared == 0        # the registry never linked this procurement
