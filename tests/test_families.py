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
    assert rows == 222        # 220 + lots 4Α and 4Β of ANTINERO II, curated 2026-09-01
    fams = kh.execute("""
        SELECT COUNT(DISTINCT f.adam) FROM contract_families f
        JOIN contract_scope s ON s.reference_number = f.reference_number
        WHERE s.in_scope = 1 AND f.kind = 'notice' AND f.role = 'procurement'
        """).fetchone()[0]
    assert fams == 136


def test_real_db_every_family_row_quotes_its_source(kh):
    """No row without the sentence that cites it, and the ΑΔΑΜ must appear
    inside that sentence — the rule that keeps this layer evidence-based."""
    import json, re
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    curated = {k: v for k, v in json.loads(
        (root / "khmdhs" / "data" / "family_curation.json").read_text(encoding="utf-8")).items()
        if not k.startswith("_")}
    for r in kh.execute("SELECT reference_number, adam, excerpt, kind, role, source FROM contract_families"):
        assert r["kind"] in ("notice", "auction")
        assert r["role"] in ("procurement", "amendment", "award")
        # a contract citing its call/award by DATE only: the excerpt is
        # still the contract's own sentence (verbatim in its cached text)
        # and the curation names the document that supplies the ΑΔΑΜ
        # (DATA_DECISIONS 2026-09-01); an amendment inherits such a row
        # from its predecessor under the usual «inherited:<ref>» label
        owner = (r["reference_number"] if r["source"] == "curated"
                 else r["source"].split(":", 1)[1] if r["source"].startswith("inherited:") else None)
        entry = next((e for e in curated.get(owner, []) if e["adam"] == r["adam"]), None) if owner else None
        if entry:
            assert entry["evidence"] and r["adam"] in entry["evidence"]
            txt = re.sub(r"\s+", " ", (root / "data" / "processed" / "pdf_cache" /
                                        f"{owner}.txt").read_text(encoding="utf-8", errors="replace"))
            assert r["excerpt"][:120] in txt, owner
            continue
        assert r["adam"] in r["excerpt"], r["adam"]
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


def test_real_db_curated_family_rows_are_all_loaded(kh):
    """Every ref in family_curation.json is a stored contract and every one
    of its rows is in the DB with source «curated» — the guard that lets the
    loader merely warn on an unknown ref (a synthetic fixture has none)."""
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    curated = {k: v for k, v in json.loads(
        (root / "khmdhs" / "data" / "family_curation.json").read_text(encoding="utf-8")).items()
        if not k.startswith("_")}
    assert curated                                   # 4Α of ANTINERO II, 2026-09-01
    for ref, entries in curated.items():
        assert kh.execute("SELECT 1 FROM contracts WHERE reference_number = ?", (ref,)).fetchone(), ref
        rows = {r[0]: r[1] for r in kh.execute(
            "SELECT adam, source FROM contract_families WHERE reference_number = ?", (ref,))}
        for e in entries:
            assert rows.get(e["adam"]) == "curated", (ref, e["adam"])

