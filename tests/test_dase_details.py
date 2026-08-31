"""The ΔΑΣΕ contract-page layers (DATA_DECISIONS 2026-08-23): the reader's
rules on synthetic texts, and real-DB pins on the curated categories, fire
contexts and document-stated deadlines + the endpoint that serves them."""
from __future__ import annotations

import sqlite3

import pytest

from khmdhs import dase_details as dd
from khmdhs.config import DASE_DB

# ------------------------------------------------------------------ units

FIREWOOD = """ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ
ΔΑΣΑΡΧΕΙΟ ΚΙΛΚΙΣ
ΣΥΜΦΩΝΗΤΙΚΟ
ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ ΓΙΑ ΤΗΝ ΚΑΛΥΨΗ ΑΤΟΜΙΚΩΝ ΑΝΑΓΚΩΝ
(άρθρο 8 π.δ.126/1986)
Στο Κιλκίς, σήμερα την 1η του μηνός Σεπτεμβρίου του έτους 2021, ημέρα Τετάρτη, οι κάτωθι υπογεγραμμένοι:
α) ο Δασάρχης και β) ο Πρόεδρος του ΔΑ.Σ.Ε. Παϊκου, έχοντας υπόψη:
1. Τις διατάξεις του π.δ.126/1986 «Διαδικασία παραχώρησης της εκμετάλλευσης συντήρησης και βελτίωσης των δασών».
Συμφωνούμε και αποδεχόμαστε τα παρακάτω: Το Δασαρχείο θα δεσμεύσει και θα παραλάβει τις παρακάτω ποσότητες καυσόξυλων: 353 χ.κ.μ. καυσόξυλων δρυός.
""" + "Όροι και κρατήσεις. " * 120

FLOOD = """ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ
ΔΑΣΑΡΧΕΙΟ ΛΙΜΝΗΣ
ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ
Κατασκευή έργων αντιπλημμυρικής προστασίας για τη συγκράτηση του εδάφους στην υδρολογική λεκάνη Λίμνη ΙV για λόγους κατεπείγουσας ανάγκης
Συμβατικού ποσού: Ευρώ 314.636,52 € (με Φ.Π.Α.)
Στη Λίμνη, σήμερα την 15η του μηνός Οκτωβρίου του έτους 2021, οι παρακάτω συμβαλλόμενοι:
1. Τις διατάξεις του Π.Δ. 437/1981. 21. Την ανάγκη άμεσης εκτέλεσης των εργασιών κατασκευής αντιδιαβρωτικών έργων στις καμένες περιοχές του Δασαρχείου Λίμνης.
ΑΝΑΘΕΤΕΙ Στο δεύτερο των συμβαλλομένων την εκτέλεση του έργου. Άρθρο 2: Ισχύς και διάρκεια της Σύμβασης Ο χρόνος ολοκλήρωσης των ανατιθέμενων εργασιών ορίζεται στους τέσσερεις (4) μήνες από την υπογραφή της σύμβασης. Άρθρο 3: Γνώση των συνθηκών του έργου.
""" + "Λοιποί όροι. " * 120

MUNICIPAL = """ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ
ΔΗΜΟΣ ΜΕΤΕΩΡΩΝ
ΣΥΜΒΑΣΗ ΠΑΡΟΧΗΣ ΕΡΓΑΣΙΑΣ
Σήμερα, 4/5/2023, στο Δήμο Μετεώρων, οι παρακάτω υπογεγραμμένοι:
Β. Ο ανάδοχος με τα ακόλουθα στοιχεία, στον οποίο ανατέθηκε η παροχή υπηρεσίας με τίτλο : Εργασίες αποψιλώσεων στην περιοχή της ΔΕ Καστανιάς με την αριθμ. 322/2023 Απόφαση Δημάρχου.
ΕΠΩΝΥΜΙΑ: ΟΡΕΙΝΟΣ ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΧΡΥΣΟΜΗΛΙΑΣ
ΑΝΑΘΕΤΕΙ 1. Στον ανάδοχο για λογαριασμό του Δήμου, την Εργασίες αποψιλώσεων στην περιοχή της ΔΕ Καστανιάς, ως εξής:
Άρθρο 2 Διάρκεια Η διάρκεια της σύμβασης ορίζεται ότι αρχίζει από την υπογραφή της και λήγει στις 04/11/2023
""" + "Άρθρο 3 Αμοιβή. " * 120

PROTOCOL = """ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ ΜΑΚΕΔΟΝΙΑΣ-ΘΡΑΚΗΣ
ΔΑΣΑΡΧΕΙΟ Κ. ΝΕΥΡΟΚΟΠΙΟΥ
ΣΥΜΦΩΝΗΤΙΚΟ ΚΑΙ ΠΡΩΤΟΚΟΛΛΟ ΕΓΚΑΤΑΣΤΑΣΗΣ
ΣΤΟΙΧΕΙΑ ΣΥΜΒΑΣΗΣ ΔΑΣΟΤΕΧΝΙΚΑ ΣΤΟΙΧΕΙΑ
1) Προθεσμία εκτέλεσης μέχρι …31-12-2021… 1) Δάσος: Εξοχής 2) Είδος ανατιθέμενων εργασιών: υλοτομία, μεταφορά, μετατόπιση δασικών προϊόντων.
Στο Κ. Νευροκόπι σήμερα 22-9-2021 οι υπογεγραμμένοι συμφώνησαν.
""" + "Όροι. " * 320

PREVENTION = """ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ
ΔΗΜΟΣ ΠΥΛΑΙΑΣ-ΧΟΡΤΙΑΤΗ
ΣΥΜΒΑΣΗ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ
«Διαχείριση βλάστησης σε περιοχές ιδιαίτερης προστασίας για αντιπυρικούς σκοπούς»
ποσού 29.989,40€ συμπεριλαμβανομένου του ΦΠΑ 24%
Στο Πανόραμα σήμερα την 15η Απριλίου του έτους 2022, οι παρακάτω συμβαλλόμενοι: ο Δήμος και ο Δασικός Συνεταιρισμός Εργασίας Σκαλωτής.
Η σύμβαση είναι αορίστου διάρκειας, ανάλογα με τις ανάγκες της υπηρεσίας και μέχρι εξαντλήσεως της διαθέσιμης πίστωσης.
""" + "Όροι. " * 320


def test_firewood_heading_wins_over_the_logging_words_in_the_body():
    r = dd.read_category(FIREWOOD)
    assert r.category == "kafsoxyla"
    assert r.evidence_field == "heading"
    assert "ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ" in r.evidence
    assert r.context is None
    assert dd.read_deadline(FIREWOOD, "2021-09-01").kind is None


def test_flood_works_with_the_need_clause_as_post_fire_context():
    r = dd.read_category(FLOOD)
    assert r.category == "antidiavrotika"
    assert r.context == "post_fire"
    assert "καμένες περιοχές" in r.context_evidence
    d = dd.read_deadline(FLOOD, "2021-10-15")
    assert (d.kind, d.n, d.unit, d.basis) == ("duration", 4, "months", "signature")


def test_municipal_clearing_and_a_date_deadline():
    r = dd.read_category(MUNICIPAL)
    assert r.category == "katharismoi"
    d = dd.read_deadline(MUNICIPAL, "2023-05-04")
    assert (d.kind, d.deadline_date) == ("date", "2023-11-04")


def test_protocol_is_harvesting_with_the_table_date():
    r = dd.read_category(PROTOCOL)
    assert r.category == "ylotomia"
    d = dd.read_deadline(PROTOCOL, "2021-09-22")
    assert (d.kind, d.deadline_date) == ("date", "2021-12-31")


def test_prevention_context_and_an_open_end():
    r = dd.read_category(PREVENTION)
    assert r.category == "katharismoi"
    assert r.context == "prevention"
    assert dd.read_deadline(PREVENTION, "2022-04-15").kind == "open_ended"


def test_sigma_font_repair_is_line_local():
    text = ("ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΣΙΑ\nΔΑ΢ΑΡΧΕΙΟ ΔΡΑΜΑ΢\nΣΥΜΦΩΝΗΤΙΚΟ ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ ΓΙΑ ΤΗΝ ΚΑΛΥΨΗ ΑΤΟΜΙΚΩΝ ΑΝΑΓΚΩΝ\n"
            "΢τη Δράμα, ςήμερα τθν 14η\n" + "ΓΕΝΙΚΗ ΓΡΑΜΜΑΣΕΙΑ ΔΑ΢ΩΝ\n" * 3)
    fixed, notes = dd.repair(text)
    assert any("΢-font" in n for n in notes)
    assert "ΔΑΣΑΡΧΕΙΟ ΔΡΑΜΑΣ" in fixed           # the cycle undone on a ΢ line
    assert "ΣΥΜΦΩΝΗΤΙΚΟ ΔΕΣΜΕΥΣΗΣ" in fixed       # the clean heading untouched
    assert "Στη Δράμα, σήμερα την" in fixed          # lowercase pairs


def test_recitals_never_decide_the_category():
    # a funding recital naming burnt areas inside a firewood agreement
    text = FIREWOOD.replace("1. Τις διατάξεις", "1. Την απόφαση περί έγκρισης διάθεσης πίστωσης του έργου "
                                               "«Πρόληψη και αποκατάσταση καμένων εκτάσεων». 2. Τις διατάξεις")
    r = dd.read_category(text)
    assert r.category == "kafsoxyla"
    assert r.context is None


# ---------------------------------------------------------------- real DB

pytestmark_db = pytest.mark.skipif(not DASE_DB.exists(), reason="dase.sqlite not built here")


@pytest.fixture(scope="module")
def dase():
    if not DASE_DB.exists():
        pytest.skip("dase.sqlite not built here")
    con = sqlite3.connect(f"file:{DASE_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    yield con
    con.close()


LIVE = """c.cancelled = 0 AND NOT EXISTS
          (SELECT 1 FROM contracts n WHERE n.reference_number = c.next_reference_no)"""


def test_every_live_dase_contract_has_a_category(dase):
    missing = dase.execute(f"""
        SELECT COUNT(*) FROM contracts c WHERE {LIVE} AND NOT EXISTS
          (SELECT 1 FROM contract_categories k WHERE k.reference_number = c.reference_number)
    """).fetchone()[0]
    assert missing == 0
    counts = dict(dase.execute(f"""
        SELECT k.category, COUNT(*) FROM contracts c
          JOIN contract_categories k ON k.reference_number = c.reference_number
         WHERE {LIVE} GROUP BY k.category""").fetchall())
    # the curated population as loaded on 2026-08-23 (by-eye pass included)
    assert counts == {"kafsoxyla": 1463, "kalliergitikes": 193, "ylotomia": 143,
                      "antidiavrotika": 90, "dentra": 50, "katharismoi": 46, "loipa": 10,
                      "promitheia": 3, "antipyrikes_zones": 3, "anadasosi": 3}
    labels = {r[0]: r[1] for r in dase.execute("SELECT category, label_en FROM category_labels")}
    assert labels["kafsoxyla"] == "Firewood for local needs"
    assert labels["anadasosi"].startswith("Reforestation")


def test_fire_context_is_a_separate_attribute(dase):
    ctx = dict(dase.execute(f"""
        SELECT x.context, COUNT(*) FROM contracts c
          JOIN contract_fire_context x ON x.reference_number = c.reference_number
         WHERE {LIVE} GROUP BY x.context""").fetchall())
    assert ctx == {"post_fire": 93, "prevention": 24}
    # post-fire restoration spans several TYPES of work — the reason it is
    # an attribute and not a category
    kinds = {r[0] for r in dase.execute("""
        SELECT DISTINCT k.category FROM contract_fire_context x
          JOIN contract_categories k USING (reference_number) WHERE x.context = 'post_fire'""")}
    assert {"antidiavrotika", "katharismoi", "dentra"} <= kinds


def test_deadlines_are_document_stated_only(dase):
    kinds = dict(dase.execute(f"""
        SELECT d.kind, COUNT(*) FROM contracts c
          JOIN contract_durations d ON d.reference_number = c.reference_number
         WHERE {LIVE} GROUP BY d.kind""").fetchall())
    assert kinds == {"date": 179, "duration": 102, "open_ended": 11}
    # a date-kind row always carries its date; a duration always n + unit
    assert dase.execute("SELECT COUNT(*) FROM contract_durations WHERE kind='date' AND deadline_date IS NULL").fetchone()[0] == 0
    assert dase.execute("SELECT COUNT(*) FROM contract_durations WHERE kind='duration' AND (n IS NULL OR unit IS NULL)").fetchone()[0] == 0


def test_endpoint_serves_the_layers_and_never_the_registry_end_date(dase):
    from atlas_api import app as app_module
    from atlas_api import queries_extra as qx
    app = app_module.create_app()
    app.testing = True
    client = app.test_client()
    d = client.get("/api/dase/contract/21SYMV009370868").get_json()
    assert d["category"]["key"] == "antidiavrotika"
    assert d["fire_context"]["key"] == "post_fire"
    assert d["deadlines"]["basis"] == "document" and d["deadlines"]["deadline"] == "2022-02-14"
    assert d["stated_duration"]["kind"] == "duration"
    # a contract whose registry row states an end date but whose text states
    # nothing draws NO deadline (document-stated only)
    ref = dase.execute(f"""
        SELECT c.reference_number FROM contracts c WHERE {LIVE} AND c.end_date IS NOT NULL AND c.end_date != ''
           AND NOT EXISTS (SELECT 1 FROM contract_durations d WHERE d.reference_number = c.reference_number)
         LIMIT 1""").fetchone()[0]
    dl = qx.dase_contract_deadlines(dase, ref)
    assert dl["deadline"] is None and dl["fields"]["end_date"] is not None
    # the version chain comes from the registry's own links
    ref2 = dase.execute("""SELECT reference_number FROM contracts WHERE prev_reference_no IN
                            (SELECT reference_number FROM contracts) LIMIT 1""").fetchone()[0]
    assert len(qx.dase_contract_chain(dase, ref2)) >= 2
