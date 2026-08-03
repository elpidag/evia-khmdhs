"""Units for the arogi extraction rules + real-DB pins for arogi.sqlite."""
import pytest

from khmdhs.arogi import (case_key, classify_kind, dka_loan, fire_citations,
                          parse_greek_amount, ss_total)
from khmdhs.config import AROGI_DB


def test_parse_greek_amounts():
    assert parse_greek_amount("1.234,56") == 1234.56
    assert parse_greek_amount("4.700,00") == 4700.0
    # registry all-dots keying: final dot + two digits is the decimal
    assert parse_greek_amount("65.982.92") == 65982.92
    assert parse_greek_amount("59.201.40") == 59201.40
    assert parse_greek_amount("75.000") == 75000.0
    assert parse_greek_amount("x") is None


def test_classify_kind():
    assert classify_kind("ΑΔΕΙΑ ΕΠΙΣΚΕΥΗΣ ΠΥΡΟΠΛΗΚΤΟΥ ΚΤΗΡΙΟΥ") == "repair_permit"
    assert classify_kind("ΒΕΒΑΙΩΣΗ ΠΕΡΑΙΩΣΗΣ ΕΡΓΑΣΙΩΝ ΕΠΙΣΚΕΥΗΣ") == "completion"
    assert classify_kind("Χορήγηση Β΄ δόσης Στεγαστικής Συνδρομής") == "progress_dose"
    assert classify_kind("Έγκριση Σ.Σ. για Αυτοστέγαση") == "autostegasi"
    assert classify_kind("Οριοθέτηση περιοχών ...") == "oriothetisi"


def test_fire_citations():
    got = fire_citations("λόγω των πυρκαγιών του Ιουλίου/Αυγούστου 2021 στην Εύβοια")
    assert got and got[0]["year"] == 2021 and got[0]["months"] == [7, 8]
    got = fire_citations("τις πυρκαγιές της 23ης και 24ης Ιουλίου 2018")
    assert got and got[0]["year"] == 2018 and got[0]["months"] == [7]


def test_ss_total_hash_sequence():
    text = ("ΠΙΝΑΚΑΣ ... ΣΥΝΔΡΟΜΗΣ (ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ) (ΑΤΟΚΟ ΔΑΝΕΙΟ) "
            "#12.095,74€# #9.676,59€# #2.419,15€#")
    total, exc = ss_total(text)
    assert total == 12095.74 and "12.095,74" in exc
    assert dka_loan(text) == (9676.59, 2419.15)


def test_ss_total_prefers_the_ss_row_over_budget_tables():
    text = ("ΠΡΟΫΠΟΛΟΓΙΣΜΟΣ ΠΡΟΤΕΙΝΟΜΕΝΟΣ #65.982.92# € ΕΓΚΕΚΡΙΜΕΝΟΣ "
            "#59.820.64# € ... ΣΥΝΔΡΟΜΗΣ (ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ) (ΑΤΟΚΟ "
            "ΔΑΝΕΙΟ) #59.820,64€# #47.856,51€# #11.964,13€#")
    total, _ = ss_total(text)
    assert total == 59820.64


def test_case_key_permit_number():
    assert case_key("ΑΡ. ΑΔΕΙΑΣ: 8/ΠΥΡΑΝΑΤ21/Τ.Α.Ε.Φ.Κ.-Α.Α.") \
        == "8/ΠΥΡΑΝΑΤ21/ΤΑΕΦΚ-ΑΑ"
    assert case_key("ΤΡΟΠΟΠΟΙΗΤΙΚΗ ΤΗΣ 920/ΠΥΡ.2018/Τ.Α.Ε.Φ.Κ.-Α.Α.") \
        == "920/ΠΥΡ2018/ΤΑΕΦΚ-ΑΑ"


# ---------------------------------------------------------- real-DB pins

pytestmark_db = pytest.mark.skipif(not AROGI_DB.exists(),
                                   reason="arogi.sqlite not built")


@pytestmark_db
def test_real_db_pins():
    import sqlite3
    conn = sqlite3.connect(f"file:{AROGI_DB}?mode=ro", uri=True)
    assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 956
    assert conn.execute(
        "SELECT COUNT(*) FROM fires WHERE in_scope=1").fetchone()[0] == 10
    total = conn.execute(
        "SELECT ROUND(SUM(approved_eur),2) FROM cases").fetchone()[0]
    assert total == pytest.approx(20_059_683.94)
    # every act row belongs to a ≥2021 fire or is honestly unattributed
    n_pre = conn.execute("""
        SELECT COUNT(*) FROM acts a JOIN fires f USING (fire_id)
        WHERE f.in_scope = 0""").fetchone()[0]
    assert n_pre == 0
    # press quotes are verbatim-bearing (never empty)
    assert conn.execute(
        "SELECT COUNT(*) FROM press_totals WHERE quote = ''").fetchone()[0] == 0
    conn.close()
