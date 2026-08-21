"""Diavgeia completion-acts layer: classifier, end-date extraction, pins."""
import sqlite3

import pytest

from atlas_api import queries_extra
from khmdhs.completion_acts_loader import (SCHEMA, classify, extract_end_date,
                                           resolve_paralavi)
from khmdhs.config import DEFAULT_DB
from khmdhs.db import SCHEMA_SQL
from tests.conftest import add_contract


@pytest.mark.parametrize("subject,expected", [
    ("Έγκριση του Πρωτοκόλλου Οριστικής Παραλαβής εργασιών του έργου της "
     "Σύμβασης με ΑΔΑΜ: 22SYMV011470180", "oristiki_paralavi"),
    ("Έγκριση Πρωτοκόλλου Προσωρινής και Οριστικής Παραλαβής",
     "oristiki_paralavi"),
    ("Βεβαίωση περαίωσης εργασιών της Σύμβασης", "peraiosi"),
    ("Διαπιστωτική πράξη ολοκλήρωσης του έργου", "oloklirosi"),
    # subject omits «οριστικής» — resolved from the PDF body (6Λ674653Π8-ΒΤ3)
    ("Έγκριση του Πρωτοκόλλου Παραλαβής εργασιών του έργου της Σύμβασης "
     "με ΑΔΑΜ: 22SYMV010473683", "paralavi_check"),
    ("Έγκριση Πρωτοκόλλου Τμηματικής Παραλαβής", None),
    ("Έγκριση Πρωτοκόλλου Προσωρινής Παραλαβής", None),
    # rejected: everything that is not a project ending
    ("Έγκριση παράτασης των εργασιών της Σύμβασης με ΑΔΑΜ: …", None),
    ("Συγκρότηση Επιτροπής Παραλαβής του έργου", None),
    ("Ορισμός Επιτροπής Οριστικής Παραλαβής", None),
    ("1η Τροποποίηση της Σύμβασης", None),
    ("Έγκριση 2ης Επιμέτρησης Εργασιών", None),
    ("Εκκαθάριση - εντολή πληρωμής της Σύμβασης", None),
])
def test_classify(subject, expected):
    assert classify(subject) == expected


def test_resolve_paralavi_from_pdf_body():
    assert resolve_paralavi(
        "Εγκρίνουμε το από 21.11.2022 πρωτόκολλο οριστικής ποιοτικής και "
        "ποσοτικής παραλαβής του έργου") == "oristiki_paralavi"
    assert resolve_paralavi(
        "Εγκρίνουμε το πρωτόκολλο τμηματικής παραλαβής") is None
    assert resolve_paralavi("άσχετο κείμενο χωρίς παραλαβή") is None


def test_extract_end_date_protocol_first():
    text = ("… Εγκρίνουμε το από 25.07.2023 πρωτόκολλο οριστικής ποιοτικής "
            "και ποσοτικής παραλαβής του εν θέματι έργου …")
    d, excerpt = extract_end_date(text)
    assert d == "2023-07-25"
    assert "πρωτόκολλο" in excerpt


def test_extract_end_date_peraiosi_fallback():
    text = "… οι εργασίες περαιώθηκαν εμπροθέσμως την 12/10/2022 σύμφωνα …"
    d, _ = extract_end_date(text)
    assert d == "2022-10-12"
    assert extract_end_date("no dates here at all") is None


def test_timeline_includes_completion_acts():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCHEMA)
    add_contract(conn, "22SYMV000000001", title="ΕΡΓΟ", eur=1000.0)
    conn.execute(
        "INSERT INTO contract_completion_acts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("ΤΕΣΤ4653Π8-ΑΑΑ", "22SYMV000000001", "22SYMV000000001",
         "oristiki_paralavi", "Έγκριση Πρωτοκόλλου Οριστικής Παραλαβής",
         "ΥΠΕΝ/1", "2023-08-18", "2023-07-25", "protocol_date",
         "το από 25.07.2023 πρωτόκολλο", "ΥΠΕΝ", "{}", None))
    tl = queries_extra.contract_timeline(conn, "22SYMV000000001")
    comp = [t for t in tl if t["kind"] == "completion"]
    assert comp[0]["part_auth"] is None
    assert len(comp) == 1
    assert comp[0]["d"] == "2023-07-25"
    assert comp[0]["ckind"] == "oristiki_paralavi"
    assert comp[0]["end_basis"] == "protocol_date"


# ---------------------------------------------------------- real-DB pins

@pytest.fixture(scope="module")
def conn():
    if not DEFAULT_DB.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    c = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        c.execute("SELECT 1 FROM contract_completion_acts LIMIT 1")
    except sqlite3.OperationalError:
        pytest.skip("completion acts not harvested yet")
    yield c
    c.close()


def test_real_db_example_act(conn):
    r = conn.execute("SELECT * FROM contract_completion_acts WHERE ada = ?",
                     ("6Ι7Τ4653Π8-ΝΡΓ",)).fetchone()
    assert r is not None
    assert r["cited_ref"] == "22SYMV011470180"
    assert r["act_kind"] == "oristiki_paralavi"
    assert r["end_date"] == "2023-07-25"
    assert r["end_basis"] == "protocol_date"


def test_real_db_only_completion_kinds(conn):
    kinds = {r[0] for r in conn.execute(
        "SELECT DISTINCT act_kind FROM contract_completion_acts")}
    assert kinds <= {"oristiki_paralavi", "peraiosi", "oloklirosi"}
    # no committee/extension noise slipped through
    bad = conn.execute(
        "SELECT COUNT(*) FROM contract_completion_acts WHERE "
        "subject LIKE '%παράταση%' OR subject LIKE '%Συγκρότηση%'"
    ).fetchone()[0]
    assert bad == 0


def test_real_db_counts(conn):
    kinds = dict(conn.execute(
        "SELECT act_kind, COUNT(*) FROM contract_completion_acts "
        "GROUP BY act_kind"))
    # 228/55 until 2026-08-21: a «Μερική έγκριση» and a «Τμηματική περαίωση»
    # were rejected as endings, three acts whose subject keyed the wrong
    # ΑΔΑΜ moved to their own contracts (DATA_DECISIONS 2026-08-21)
    assert kinds == {"oristiki_paralavi": 227, "peraiosi": 54}
    assert conn.execute(
        "SELECT COUNT(DISTINCT attributed_ref) FROM contract_completion_acts"
    ).fetchone()[0] == 156
    basis = dict(conn.execute(
        "SELECT end_basis, COUNT(*) FROM contract_completion_acts "
        "GROUP BY end_basis"))
    # protocol_date counts only ACCEPTANCE protocols since 2026-08-21 (the
    # first run had taken the «πρωτόκολλο εγκατάστασης» date on 105 acts);
    # pass 5 of the same day read 21 more forms («τα από … πρωτόκολλα», a
    # protocol number/date, a two-day protocol, «περαίωσης των εργασιών
    # στις …», month-name dates) — 26 acts state no acceptance date at all
    assert basis == {"protocol_date": 255, "act_date": 26}
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_completion_acts "
        "WHERE end_excerpt LIKE '%εγκατάστασ%'").fetchone()[0] == 0
    # the two ΥΠΕΝ keying errors are on their own contracts now
    assert conn.execute("SELECT attributed_ref FROM contract_completion_acts WHERE ada='6Χ884653Π8-ΒΙΗ'").fetchone()[0] == "23SYMV013019394"
    assert conn.execute("SELECT attributed_ref FROM contract_completion_acts WHERE ada='68Μ34653Π8-ΞΗΛ'").fetchone()[0] == "23SYMV012946366"
