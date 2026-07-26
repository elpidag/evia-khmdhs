"""Unit tests for the μελέτη-cost extractor — fixtures are verbatim layouts
observed in the cached contract corpus (DATA_DECISIONS 2026-07-26)."""
from khmdhs.study_costs import find_study_costs, fold, meleti_windows

A1_SAME_LINE = """\
 Αναθεώρηση (4%):                                                149.849,55 €
 Κόστος εκπόνησης μελετών συμπεριλαμβανομένων των                45.755,30 €
 φακέλων ΣΑΥ-ΦΑΥ:
"""

A1_NO_EURO_SIGN = """\
 Κονδύλι                                                        Ποσό σε Ευρώ (πλέον ΦΠΑ)
 Αναθεώρηση (4%):                                                                369.872,73
 Κόστος Εκπόνησης Μελετών συμπεριλαμβανομένων των ΣΑΥ –                          579.687,68
 ΦΑΥ
"""

A2_NEXT_LINE_WITH_WATERMARK = """\
       Κόστος εκπόνησης μελετών συμπεριλαμβανομένων των
ΣΕΛ.5
26SYMV018779399 2026-05-12
                                                                        44.086,18
       φακέλων ΣΑΥ-ΦΑΥ:
"""

A3_PREV_LINE = """\
       Ρήτρα πρόσθετης καταβολής για μικρότερο χρόνο                    41.390,35
       παράδοσης (1%):
                                                                        29.397,88
       Κόστος εκπόνησης μελετών συμπεριλαμβανομένων των
       φακέλων ΣΑΥ-ΦΑΥ:
"""

A4_PROSE = """\
15%: 610.241,32 € + αναθεώρηση: 39.885,05 € + δικαίωμα προαίρεσης: 85.694,61 € +
9
22SYMV010635347 2022-05-26
κόστος εκπόνησης μελέτης συμπεριλαμβανομένων των φακέλων ΣΑΥ-ΦΑΥ 16.628,99 €
+ συνολικό ΦΠΑ 24%: 1.156.974,10 €.
"""

APE_RECITAL = """\
Ο 1ος Ανακεφαλαιωτικός Πίνακας Εργασιών του έργου είναι συνολικής δαπάνης 4.143.136,01€
(εκ των οποίων 2.596.104,77€ εργασίες, 467.406,86€ Γ.Ε και Ο.Ε., 19.314,13€ για απρόβλεπτα,
123.337,03€ η αναθεώρηση, 64.135,26€ για πρόσθετη καταβολή, 70.340,67€ το κόστος εκπόνησης
των μελετών και Φ.Π.Α. 801.897,29€).
"""

FALSE_POSITIVE_INSURANCE = """\
… ασφαλιστήριο συμβόλαιο του μελετητή, ήτοι της εταιρείας με την επωνυμία
«ΟΛΥΜΠΟΣ ΕΤΑΙΡΙΑ ΜΕΛΕΤΩΝ ΙΚΕ», 8. ότι ο Ανάδοχος κατέθεσε την υπ' αριθ.
0908253862/02.05.2024 εγγυητική επιστολή της Attica Bank, ποσού 449.559,06 ευρώ,
για την καλή εκτέλεση της σύμβασης.
"""

FALSE_POSITIVE_TITLE = """\
… ΚΑΘΩΣ ΚΑΙ ΓΙΑ ΤΗ ΣΥΝΤΗΡΗΣΗ ΔΑΣΙΚΟΥ ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ ΚΑΙ ΑΝΤΙΠΥΡΙΚΩΝ ΖΩΝΩΝ ΜΕ
ΕΓΚΕΚΡΙΜΕΝΕΣ ΜΕΛΕΤΕΣ» συνολικού ποσού 1.234.567,89 € δ) της Εγκεκριμένης Μελέτης,
της Τεχνικής Περιγραφής και των Τεχνικών Προδιαγραφών
"""


def _one(text):
    hits = find_study_costs(text)
    assert len(hits) == 1, hits
    return hits[0]


def test_same_line_table_row():
    h = _one(A1_SAME_LINE)
    assert h.eur == 45755.30 and h.rule == "after_label"


def test_same_line_without_euro_sign():
    h = _one(A1_NO_EURO_SIGN)
    assert h.eur == 579687.68 and h.rule == "after_label"


def test_next_line_skips_pagebreak_watermarks():
    h = _one(A2_NEXT_LINE_WITH_WATERMARK)
    assert h.eur == 44086.18 and h.rule == "after_label_wrapped"


def test_prev_line_amount_above_label():
    h = _one(A3_PREV_LINE)
    assert h.eur == 29397.88 and h.rule == "prev_line"
    # crucially NOT the neighbouring row's 41.390,35


def test_prose_amount_after_anchor():
    h = _one(A4_PROSE)
    assert h.eur == 16628.99 and h.rule == "after_label"


def test_ape_recital_amount_before_anchor():
    h = _one(APE_RECITAL)
    assert h.eur == 70340.67 and h.rule == "before_prose"
    # NOT the ΦΠΑ 801.897,29 that follows on the wrapped line


def test_false_positives_yield_nothing():
    assert find_study_costs(FALSE_POSITIVE_INSURANCE) == []
    assert find_study_costs(FALSE_POSITIVE_TITLE) == []


def test_fold_and_windows():
    assert "ΜΕΛΕΤ" in fold("μελέτης")
    w = meleti_windows(FALSE_POSITIVE_INSURANCE, radius=40)
    assert w and all("μελετ" in fold(x).lower() or "ΜΕΛΕΤ" in fold(x) for x in w)


# ---------------------------------------------------------------------------
# Loader + chain-inheritance query
# ---------------------------------------------------------------------------

def test_loader_roundtrip_and_chain_inheritance(mem_conn):
    from tests.conftest import add_contract, set_scope
    from khmdhs import studies_loader
    from webui import queries

    add_contract(mem_conn, "OLD1", title="ΕΡΓΟ ANTINERO IV", eur=1000.0)
    add_contract(mem_conn, "TIP1", title="1η ΤΡΟΠΟΠΟΙΗΣΗ", prev="OLD1", eur=1200.0)
    add_contract(mem_conn, "TIP2", title="ΕΡΓΟ ANTINERO III", eur=2000.0)
    set_scope(mem_conn, "OLD1", "antinero_iv", 0, superseded_by="TIP1")
    set_scope(mem_conn, "TIP1", "antinero_iv", 1)
    set_scope(mem_conn, "TIP2", "antinero_iii", 1)

    curated = {
        "OLD1": {"eur": 50.0, "page": 9, "excerpt": "κόστος εκπόνησης μελετών 50,00"},
        "TIP2": {"eur": 80.0, "page": 4, "excerpt": "κόστος εκπόνησης μελετών 80,00"},
    }
    assert studies_loader.write_db(mem_conn, curated) == 2

    res = queries.study_costs(mem_conn)
    rows = {r["ref"]: r for r in res["rows"]}
    # TIP1 has no row of its own → inherits the superseded original's.
    assert rows["TIP1"]["eur"] == 50.0 and rows["TIP1"]["src_ref"] == "OLD1"
    # TIP2's own row wins.
    assert rows["TIP2"]["eur"] == 80.0 and rows["TIP2"]["src_ref"] == "TIP2"
    assert res["summary"]["n_with"] == 2 and res["summary"]["total_eur"] == 130.0
    assert res["summary"]["n_in_scope"] == 2


def test_loader_refuses_unknown_ref_and_oversized_amounts(mem_conn):
    import pytest
    from tests.conftest import add_contract
    from khmdhs import studies_loader

    add_contract(mem_conn, "C1", eur=100.0)
    with pytest.raises(SystemExit):
        studies_loader.write_db(mem_conn, {"NOPE": {
            "eur": 1.0, "excerpt": "x"}})
    with pytest.raises(SystemExit):
        studies_loader.write_db(mem_conn, {"C1": {
            "eur": 100.0, "excerpt": "x"}})   # >= stated total
