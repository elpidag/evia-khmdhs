"""Ανάδοχοι αναδάσωσης/αποκατάστασης dataset: unit tests + real-DB pins."""
import json
import sqlite3

import pytest

from khmdhs import anadohoi
from khmdhs.anadohoi_loader import DEFAULT_DB, derive_status

# ---------------------------------------------------------------------------
# classify() — proposals over observed subjects

YPEN = "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"
APD = "ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ ΘΕΣΣΑΛΙΑΣ - ΣΤΕΡΕΑΣ ΕΛΛΑΔΑΣ"


@pytest.mark.parametrize("subject,org,expected", [
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΝΑΔΑΣΩΣΗΣ\r\n\r\n", YPEN, "orismos"),
    ("Πράξη Ορισμού Αναδόχου Αναδάσωσης", YPEN, "orismos"),
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ & ΑΝΑΔΑΣΩΣΗΣ", YPEN, "orismos"),
    ("2η ΤΡΟΠΟΠΟΙΗΣΗ ΠΡΑΞΗΣ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
     "tropopoiisi"),
    ("Ανάκληση πράξης ορισμού αναδόχου αναδάσωσης", YPEN, "anaklisi"),
    ("Διαπιστωτική Πράξη ολοκλήρωσης του έργου «αντιπλημμυρικής…»", YPEN,
     "oloklirosi"),
    ("Διαπιστωτική πράξη ολοκλήρωσης του έργου “Έργα αντιπλημμυρικής…”", APD,
     "oloklirosi"),
    ("Υποβολή αιτήματος δυνητικού Αναδόχου Αναδάσωσης σε περιοχή "
     "αρμοδιότητας του Δασαρχείου Λαυρίου", YPEN, "aitima"),
    # Titles lie: the ΔΩΡΕΑ act is really a πράξη ορισμού — the classifier
    # must NOT guess; it stays "unknown" and a human overrides it.
    ("ΔΩΡΕΑ ΓΙΑ ΑΝΑΔΑΣΩΣΗ ΠΕΡΙΟΧΗΣ ΙΠΠΟΚΡΑΤΕΙΟΥ ΠΟΛΙΤΕΙΑΣ", YPEN, "unknown"),
    # Lifecycle acts.
    ("Συγκρότηση Επιτροπής Παραλαβής του έργου …", YPEN, "lifecycle"),
    ("Θεώρηση και έγκριση μελέτης με τίτλο «Μελέτη αναδάσωσης…»", YPEN,
     "lifecycle"),
    ("Έγκριση 2ης Αναλυτικής Επιμέτρησης Εργασιών του Έργου «Άμεσα μέτρα…»",
     YPEN, "lifecycle"),
    ("Ορισμός επιβλεπόντων της Δ/νσης Δασών Δωδεκανήσου του έργου …", YPEN,
     "lifecycle"),
    # ΠΕΡΑΤΩΣΗΣ is a completion synonym of ΟΛΟΚΛΗΡΩΣΗΣ.
    ("ΔΙΑΠΙΣΤΩΤΙΚΗ ΠΡΑΞΗ ΠΕΡΑΤΩΣΗΣ _ ΑΝΤΙΔΙΑΒΡΩΤΙΚΑ_ΚΥΘΗΡΑ", YPEN,
     "oloklirosi"),
    # Land-status instruments are not scheme acts.
    ("Απόφαση κήρυξης έκτασης ως Αναδασωτέας.", YPEN, "noise"),
    ("Απαγόρευση θήρας ορισμένου χρόνου στην θέση \"Ρέμα Μύλος\"…", YPEN,
     "noise"),
    # Admin housekeeping cited in every act must stay noise.
    ("Ορισμός Αναπληρωτή Προϊσταμένου Γενικής Διεύθυνσης Δασών & Δασικού "
     "Περιβάλλοντος", YPEN, "noise"),
    ("2η ΤΡΟΠΟΠΟΙΗΣΗ … ΓΙΑ ΤΗΝ ΕΚΓΥΜΝΑΣΗ ΚΥΝΗΓΕΤΙΚΩΝ ΣΚΥΛΩΝ …", YPEN,
     "noise"),
    # Non-forest organisations are never in scope.
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", "ΔΗΜΟΣΙΑ ΥΠΗΡΕΣΙΑ ΑΠΑΣΧΟΛΗΣΗΣ",
     "noise"),
    ("ΣΥΜΒΑΣΗ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ ΠΡΟΒΛΗΜΑΤΩΝ ΥΓΡΑΣΙΑΣ ΣΤΟ ΚΤΙΡΙΟ…",
     "ΠΑΝΕΠΙΣΤΗΜΙΟ ΑΙΓΑΙΟΥ", "noise"),
])
def test_classify(subject, org, expected):
    assert anadohoi.classify(subject, org) == expected


def test_classify_pre_scheme_dates_are_noise():
    assert anadohoi.classify("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
                             issue_date="2019-05-01") == "noise"
    assert anadohoi.classify("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
                             issue_date="2021-09-17") == "orismos"


# ---------------------------------------------------------------------------
# ΑΔΑ citations

def test_cited_adas_dedupe_own_and_homoglyphs():
    text = ("ΑΔΑ: ΡΝΕΦ4653Π8-ΙΩ5 … (ΑΔΑ : Ω2ΕΞ4653Π8-6ΟΟ) … "
            "(ΑΔΑ : ΩΖ2Ο4653Π8-ΓΕΞ) … ΑΔΑ: ΡΝΕΦ4653Π8-ΙΩ5 again … "
            "(ΑΔΑ: 6PΛ34653Π8-028)")   # Latin P homoglyph
    assert anadohoi.cited_adas(text, own_ada="ΡΝΕΦ4653Π8-ΙΩ5") == [
        "Ω2ΕΞ4653Π8-6ΟΟ", "ΩΖ2Ο4653Π8-ΓΕΞ", "6ΡΛ34653Π8-028"]


def test_cited_adas_rejects_non_ada_tokens():
    # all-digit and all-letter tokens are not ΑΔΑs; 9-char registry typos
    # («6ΟΘΚ4653Π-ΤΦΚ») must not match either.
    text = "1234567890-123 ΑΒΓΔΕΖΗΘΙΚ-ΛΜΝ 6ΟΘΚ4653Π-ΤΦΚ"
    assert anadohoi.cited_adas(text) == []


# ---------------------------------------------------------------------------
# Greek parsing

def test_amounts():
    (v, ex), = anadohoi.amounts_with_context("προϋπολογισμού ύψους 395.200,40€")
    assert v == pytest.approx(395200.40)
    assert "395.200,40" in ex


def test_stremmata():
    vals = [v for v, _ in anadohoi.stremmata_with_context(
        "έκτασης 32.537 στρεμμάτων και αργότερα 51,00 στρ. και ΣΤΡΕΜΜΑΤΑ 40")]
    assert vals[:2] == [32537.0, 51.0]


@pytest.mark.parametrize("snippet,expected", [
    ("η 18η Δεκεμβρίου 2021", "2021-12-18"),
    ("έως 31 Δεκεμβρίου του 2027", "2027-12-31"),
    ("έως τέλος 2024", "2024-12-31"),
    ("την 28/03/2023 απόφαση", "2023-03-28"),
    ("στις 12.08.2022", "2022-08-12"),
    ("καμία ημερομηνία εδώ", None),
])
def test_parse_greek_date(snippet, expected):
    assert anadohoi.parse_greek_date(snippet) == expected


# ---------------------------------------------------------------------------
# status derivation

def test_derive_status():
    c = {"ada": "X"}
    assert derive_status(c, None, "2020-01-01", "2026-08-02") == "completed"
    assert derive_status(None, c, None, "2026-08-02") == "revoked"
    assert derive_status(None, None, "2024-12-31", "2026-08-02") == \
        "no_completion_recorded"
    assert derive_status(None, None, "2027-12-31", "2026-08-02") == "active"
    assert derive_status(None, None, None, "2026-08-02") == "active"
    # a restated act is superseded regardless of anything else
    assert derive_status(c, None, None, "2026-08-02", "ΨΟΕ84653Π8-ΩΤΡ") == \
        "superseded"


# ---------------------------------------------------------------------------
# real-DB pins (committed anadohoi.sqlite)

pytestmark_db = pytest.mark.skipif(not DEFAULT_DB.exists(),
                                   reason="anadohoi.sqlite not built")


@pytest.fixture(scope="module")
def conn():
    if not DEFAULT_DB.exists():
        pytest.skip("anadohoi.sqlite not built")
    c = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    yield c
    c.close()


def test_real_db_projects_have_roots(conn):
    orphans = conn.execute(
        """SELECT p.root_ada FROM projects p
           LEFT JOIN decisions d ON d.ada = p.root_ada
           WHERE d.ada IS NULL OR d.kind != 'orismos'""").fetchall()
    assert orphans == []


def test_real_db_links_resolve(conn):
    dangling = conn.execute(
        """SELECT pd.ada FROM project_decisions pd
           LEFT JOIN decisions d ON d.ada = pd.ada
           WHERE d.ada IS NULL""").fetchall()
    assert dangling == []


def test_real_db_every_project_has_valid_status(conn):
    bad = conn.execute(
        """SELECT root_ada, status FROM projects WHERE status NOT IN
           ('completed', 'revoked', 'no_completion_recorded', 'active',
            'superseded')"""
    ).fetchall()
    assert bad == []


def test_real_db_budget_only_with_evidence(conn):
    rows = conn.execute(
        "SELECT root_ada, evidence_json FROM projects "
        "WHERE budget_eur IS NOT NULL").fetchall()
    for root, ev in rows:
        assert "budget" in json.loads(ev), f"{root}: budget without evidence"


def test_real_db_works_zones_mapping(conn):
    """The 6 Εύβοια projects carry their digitised works-zone ids
    (DATA_DECISIONS 2026-08-12); ids must exist in the digitised set."""
    zone_ids = {"limni_i", "limni_ii", "limni_iii", "limni_iv", "limni_v",
                "istiaia_i", "istiaia_ii", "istiaia_iii", "istiaia_iv"}
    rows = conn.execute(
        "SELECT root_ada, works_zones FROM projects "
        "WHERE works_zones IS NOT NULL").fetchall()
    assert len(rows) == 6
    for ada, zs in rows:
        zs = json.loads(zs)
        assert zs and set(zs) <= zone_ids, ada


def test_real_db_deliverables_curated_for_all(conn):
    """Every project carries the works/study scope, each with its verbatim
    σκοπός excerpt (DATA_DECISIONS 2026-08-11)."""
    counts = dict(conn.execute(
        "SELECT deliverables, COUNT(*) FROM projects GROUP BY deliverables"))
    assert counts == {"works": 42, "study_and_works": 17, "study": 10}
    missing_ev = conn.execute(
        "SELECT root_ada, evidence_json FROM projects").fetchall()
    for root, ev in missing_ev:
        assert "deliverables" in json.loads(ev), \
            f"{root}: deliverables without evidence"


def test_real_db_pins(conn):
    assert conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 322
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 69
    statuses = dict(conn.execute(
        "SELECT status, COUNT(*) FROM projects GROUP BY status"))
    assert statuses == {"completed": 14, "active": 32, "revoked": 1,
                        "no_completion_recorded": 21, "superseded": 1}
    # stated budgets (42 of 68 live projects), and after δωρεά amendments
    stated, n = conn.execute(
        "SELECT ROUND(SUM(budget_eur),2), COUNT(budget_eur) FROM projects "
        "WHERE status != 'superseded'").fetchone()
    assert (stated, n) == (37842320.85, 42)
    assert conn.execute(
        "SELECT ROUND(SUM(budget_current),2) FROM projects "
        "WHERE status != 'superseded'").fetchone()[0] == 41842320.85
    # duration-based deadlines carried as text, never fabricated dates
    assert conn.execute(
        "SELECT COUNT(deadline_text) FROM projects").fetchone()[0] == 36
    assert conn.execute(
        "SELECT deadline_initial FROM projects WHERE root_ada = "
        "'ΨΓΦΔ4653Π8-777'").fetchone()[0] is None
    # Π.Ε. resolved for all but the 2 genuinely supra-Π.Ε. projects
    assert conn.execute(
        "SELECT COUNT(pe), COUNT(*) FROM projects").fetchone() == (67, 69)
    for (root,) in conn.execute(
            "SELECT root_ada FROM projects WHERE pe IS NULL"):
        assert root in ("6Φ454653Π8-Ξ1Ζ", "9ΕΘΠ4653Π8-ΠΡ4")
    # fire_event curated for every project; 5 are honestly non-fire
    n_fire, n_nonfire = conn.execute(
        "SELECT COUNT(fire_event), SUM(fire_event = 'εκτός πυρκαγιάς') "
        "FROM projects").fetchone()
    assert (n_fire, n_nonfire) == (69, 5)
    # the restatement chain and the revocation are pinned
    assert conn.execute(
        "SELECT superseded_by FROM projects WHERE root_ada = "
        "'6ΗΥΗ4653Π8-7ΘΥ'").fetchone()[0] == "ΨΟΕ84653Π8-ΩΤΡ"
    assert conn.execute(
        "SELECT revoked_ada FROM projects WHERE root_ada = "
        "'63ΡΧ4653Π8-6Ε2'").fetchone()[0] == "Ε01Π4653Π8-ΘΛΣ"
