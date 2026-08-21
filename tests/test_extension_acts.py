"""Diavgeia deadline-EXTENSION acts (phase 1 of the lifecycle layer,
DATA_DECISIONS 2026-08-21): classifier, ordinal, the new-deadline extractor,
and real-DB pins over the committed table."""
import sqlite3

import pytest

from khmdhs.config import DEFAULT_DB
from khmdhs.extension_acts_loader import (_lots_disagree, classify,
                                          extract_extension, ordinal_of, flag_against_issue, extract_scope)


@pytest.mark.parametrize("subject,expected", [
    ("Έγκριση τμηματικής παράτασης του έργου της Σύμβασης (19) με ΑΔΑΜ: 24SYMV014458852",
     "extension_partial"),
    ("Έγκριση 2ης τμηματικής παράτασης του έργου", "extension_partial"),
    ("Έγκριση παράτασης εργασιών του έργου της Σύμβασης με ΑΔΑΜ: 22SYMV010473684",
     "extension"),
    ("Έγκριση δεύτερης παράτασης στη συνολική προθεσμία περαίωσης", "extension"),
    # an extension OF the schedule is an extension
    ("Έγκριση παράτασης χρονοδιαγράμματος του έργου της Σύμβασης με ΑΔΑΜ: 25SYMV017985934",
     "extension"),
    # not extensions: a revocation, a schedule approved because of / after an extension, anything else
    ("Ανάκληση της απόφασης έγκρισης παράτασης του έργου", None),
    ("Έγκριση τροποποιημένου χρονοδιαγράμματος του έργου κατόπιν παράτασης", None),
    ("Έγκριση Αναπροσαρμοσμένου λόγω παράτασης Χρονοδιαγράμματος εκτέλεσης της Σύμβασης", None),
    ("Έγκριση του 1ου Α.Π.Ε. του έργου", None),
    ("Συγκρότηση επιτροπής παραλαβής", None),
])
def test_classify(subject, expected):
    assert classify(subject) == expected


def test_ordinal():
    assert ordinal_of("Έγκριση 2ης τμηματικής παράτασης") == 2
    assert ordinal_of("Έγκριση 3ης παράτασης του έργου") == 3
    assert ordinal_of("Έγκριση δεύτερης τμηματικής παράτασης") == 2
    assert ordinal_of("Έγκριση παράτασης εργασιών") is None


def test_extract_reads_the_operative_part_not_the_recitals():
    # the recitals cite the PREVIOUS extensions; only the last «Αποφασίζουμε» counts
    text = ("18. Την απόφαση για την έγκριση 1ης παράτασης … μέχρι την 29-02-2024. "
            "19. Την απόφαση για την έγκριση 2ης παράτασης … μέχρι την 31-05-2024. "
            "Αποφασίζουμε Την έγκριση της 3ης παράτασης στη συνολική προθεσμία περαίωσης "
            "του έργου της Σύμβασης με ΑΔΑΜ 23SYMV013600200, μέχρι τις 15.07.2024, για "
            "τους λόγους που αναφέρονται στο προοίμιο.")
    ex = extract_extension(text)
    assert ex["new_deadline"] == "2024-07-15"
    assert ex["dates"] == ["2024-07-15"]
    assert ex["per_area"] == 0
    assert "15.07.2024" in ex["excerpt"]
    assert ex["flag"] is None


def test_extract_per_area_keeps_every_date_and_takes_the_latest():
    text = ("ΑΠΟΦΑΣΙΖΟΥΜΕ Εγκρίνουμε την τμηματική παράταση του έργου της Σύμβασης "
            "(11Γ/2024) με ΑΔΑΜ: 24SYMV014659194, μέχρι τις 30.11.2024, για την περιοχή "
            "αρμοδιότητας της Διεύθυνσης Δασών Ηρακλείου και μέχρι τις 20.11.2024 για την "
            "περιοχή αρμοδιότητας της Διεύθυνσης Δασών Χανίων.")
    ex = extract_extension(text)
    assert ex["dates"] == ["2024-11-20", "2024-11-30"]
    assert ex["new_deadline"] == "2024-11-30"
    assert ex["per_area"] == 1


def test_extract_duration_wording_and_letter_spaced_anchor():
    text = ("Α Π Ο Φ Α Σ Ι Ζ Ο Υ Μ Ε Εγκρίνουμε την παράταση της συνολικής προθεσμίας του "
            "έργου της Σύμβασης με ΑΔΑΜ 24SYMV014370248 κατά δεκαπέντε (15) ημερολογιακές "
            "ημέρες, ήτοι μέχρι τις 25.10.2024, σύμφωνα με το Ν.4412/2016.")
    ex = extract_extension(text)
    assert ex["new_deadline"] == "2024-10-25"
    assert ex["by_text"].startswith("κατά δεκαπέντε (15)")


def test_extract_flags_instead_of_guessing():
    assert extract_extension("")["flag"] == "no_text"
    assert extract_extension("Έχοντας υπόψη τη Σύμβαση με ΑΔΑΜ 24SYMV0 χωρίς απόφαση")["flag"] == "no_operative"
    assert extract_extension("Αποφασίζουμε την έγκριση της παράτασης του έργου της Σύμβασης με ΑΔΑΜ 24SYMV0 χωρίς ημερομηνία")["flag"] == "no_date"
    # a substitution-cipher font: Greek letters, none of the words every act has
    assert extract_extension("ςημ έγκοιρη 2ηπ παοάςαρηπ ρςημ ρσμβαςική ποξθερμία ςξσ έογξσ")["flag"] == "unreadable_font"


def test_lot_letters():
    assert _lots_disagree("15Α", "15Γ")
    assert _lots_disagree("4Α", "4Δ")
    assert not _lots_disagree("19", "19Η")      # the subject merely omits the letter
    assert not _lots_disagree("22", "22")


# ---------------------------------------------------------- real-DB pins

@pytest.fixture(scope="module")
def conn():
    if not DEFAULT_DB.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    c = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        c.execute("SELECT 1 FROM contract_extension_acts LIMIT 1")
    except sqlite3.OperationalError:
        pytest.skip("extension acts not harvested yet")
    yield c
    c.close()


def test_classify_refusal_and_the_flag_against_the_acts_own_date():
    # «Απόρριψη αιτήματος χορήγησης τέταρτης (4ης) παράτασης …» refuses one
    assert classify("Απόρριψη αιτήματος χορήγησης τέταρτης (4ης) παράτασης του έργου της Σύμβασης "
                    "(20Β/2025) με ΑΔΑΜ: 25SYMV017073922") == "extension_refused"
    ex = extract_extension("ΑΠΟΦΑΣΙΖΟΥΜΕ Απορρίπτουμε το από 26.06.2026 αίτημα της αναδόχου εταιρείας "
                           "περί χορήγησης 4ης παράτασης προθεσμίας περαίωσης των τεχνικών εργασιών του "
                           "έργου της Σύμβασης με ΑΔΑΜ 25SYMV017073922 για την περιοχή αρμοδιότητας του "
                           "Δασαρχείου Σπάρτης, για τους λόγους που περιγράφονται στο σκεπτικό. Καλούμε τη "
                           "Διευθύνουσα Υπηρεσία να ενεργήσει.")
    assert ex["flag"] == "refusal" and ex["new_deadline"] is None and ex["dates"] == []
    assert ex["excerpt"].startswith("ΑΠΟΦΑΣΙΖΟΥΜΕ Απορρίπτουμε") and "Σπάρτης" in ex["excerpt"]
    assert (ex["scope"], ex["scope_text"]) == ("area", "Δασαρχείου Σπάρτης")
    # a deadline earlier than the act's own date is kept as written and flagged
    ex = flag_against_issue({"new_deadline": "2025-02-05", "flag": None}, "2025-12-23T10:00:00")
    assert ex == {"new_deadline": "2025-02-05", "flag": "deadline_before_issue"}
    assert flag_against_issue({"new_deadline": "2026-02-05", "flag": None}, "2025-12-23")["flag"] is None


def test_extract_scope_trims_the_service_phrase():
    # the named service ends where the grant's own words begin
    s = "Αποφασίζουμε Εγκρίνουμε την τμηματική παράταση του έργου «Έργα αντιπυρικής προστασίας», "
    assert extract_scope(s + "για την περιοχή αρμοδιότητας του Δασαρχείου Καλαμπάκας μέχρι τις 31.12.2025, "
                         "σύμφωνα με το Ν.4412/2016") == ("area", "Δασαρχείου Καλαμπάκας")
    assert extract_scope(s + "για την περιοχή αρμοδιότητας του Δασαρχείου Καλαμπάκας για σαράντα πέντε "
                         "(45) ημερολογιακές ημέρες, ήτοι μέχρι τις 14.02.2026") == ("area", "Δασαρχείου Καλαμπάκας")
    assert extract_scope(s + "ως προς την υποβολή των προβλεπόμενων μελετών, για δεκαπέντε (15) ημέρες, "
                         "μέχρι τις 20.05.2025") == ("study", "ως προς την υποβολή των προβλεπόμενων μελετών")
    assert extract_scope("Αποφασίζουμε Την έγκριση της παράτασης στη συνολική προθεσμία περαίωσης του "
                         "έργου με ΑΔΑΜ 23SYMV013600200 για όλα τα δασικά φυτώρια «Αναβάθμιση», μέχρι τις "
                         "29.02.2024")[0] == "whole"


def test_real_db_every_act_is_an_extension_on_a_stored_contract(conn):
    kinds = {r[0] for r in conn.execute("SELECT DISTINCT act_kind FROM contract_extension_acts")}
    assert kinds <= {"extension", "extension_partial", "extension_refused"}
    orphan = conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts a "
        "LEFT JOIN contracts c ON c.reference_number = a.cited_ref WHERE c.reference_number IS NULL"
    ).fetchone()[0]
    assert orphan == 0
    # a read deadline is a date, never an installation or the act's own date by accident
    bad = conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE new_deadline IS NOT NULL "
        "AND new_deadline NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'").fetchone()[0]
    assert bad == 0
    # no deadline without an excerpt, no excerpt without a deadline — except
    # the refusal, whose excerpt is the sentence that refused
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE act_kind != 'extension_refused' "
        "AND (new_deadline IS NULL) != (excerpt IS NULL)"
    ).fetchone()[0] == 0
    # a flagged deadline is the act's own typo, kept as written: earlier than the act
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE flag = 'deadline_before_issue' "
        "AND new_deadline >= substr(issue_date, 1, 10)").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE flag IS NULL "
        "AND new_deadline < substr(issue_date, 1, 10)").fetchone()[0] == 0
    # the flagged ones carry their reason
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE new_deadline IS NULL AND flag IS NULL"
    ).fetchone()[0] == 0


def test_real_db_counts(conn):
    """The first full run (DATA_DECISIONS 2026-08-21): 463 acts on 167
    contracts (159 in scope), every one read — 459 grant a deadline (23
    per-area), 3 state a deadline earlier than their own date (the act's
    year typo, kept as written and flagged) and 1 REFUSES a request."""
    assert conn.execute("SELECT COUNT(*) FROM contract_extension_acts").fetchone()[0] == 463
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE new_deadline IS NOT NULL AND flag IS NULL"
    ).fetchone()[0] == 459
    assert conn.execute("SELECT COUNT(*) FROM contract_extension_acts WHERE per_area = 1").fetchone()[0] == 23
    assert conn.execute(
        "SELECT COUNT(DISTINCT attributed_ref) FROM contract_extension_acts").fetchone()[0] == 167
    kinds = dict(conn.execute(
        "SELECT act_kind, COUNT(*) FROM contract_extension_acts GROUP BY act_kind"))
    assert kinds == {"extension": 104, "extension_partial": 358, "extension_refused": 1}
    flags = dict(conn.execute(
        "SELECT flag, COUNT(*) FROM contract_extension_acts WHERE flag IS NOT NULL GROUP BY flag"))
    assert flags == {"deadline_before_issue": 3, "refusal": 1}
    assert {r[0] for r in conn.execute(
        "SELECT ada FROM contract_extension_acts WHERE flag = 'deadline_before_issue'")} == {
        "Κ4Χ04653Π8-7ΕΡ", "ΨΧΗΛ4653Π8-5ΩΔ", "ΨΕ8Λ4653Π8-ΘΚΠ"}
    assert conn.execute(
        "SELECT attributed_ref FROM contract_extension_acts WHERE act_kind = 'extension_refused'"
    ).fetchone()[0] == "25SYMV017073922"


def test_real_db_scope_of_the_grant(conn):
    """What each act extends, read from its grant clause: a τμηματική
    παράταση is an extension of ONE τμηματική προθεσμία — an area's (199),
    the studies' submission (5), a stage (4) — while a plain παράταση moves
    the συνολική προθεσμία (16 say so; 28 name one area of a multi-area
    contract). 208 acts say nothing either way and stay unscoped."""
    rows = {(k, s or "—"): n for k, s, n in conn.execute(
        "SELECT act_kind, scope, COUNT(*) FROM contract_extension_acts GROUP BY 1, 2")}
    assert rows == {
        ("extension", "area"): 28, ("extension", "stage"): 1, ("extension", "whole"): 16,
        ("extension", "—"): 59,
        ("extension_partial", "area"): 203, ("extension_partial", "stage"): 4,
        ("extension_partial", "study"): 5, ("extension_partial", "whole"): 1,
        ("extension_partial", "—"): 145,
        ("extension_refused", "area"): 1,
    }
    # a scope_text never carries the grant's own words — the phrase stops
    # before «μέχρι», «για N ημέρες», «σύμφωνα»
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE scope_text LIKE '%μέχρι%' "
        "OR scope_text LIKE '% για %' OR scope_text LIKE '%σύμφωνα%'").fetchone()[0] == 0
    # the worked example: the 12 τμηματικές of 25SYMV016670155 — the first on
    # the studies' submission, the rest per area, Καλαμπάκα to 30.06.2026
    ex = conn.execute(
        "SELECT scope, scope_text, new_deadline FROM contract_extension_acts "
        "WHERE attributed_ref = '25SYMV016670155' ORDER BY issue_date, ada").fetchall()
    assert len(ex) == 12 and ex[0][0] == "study" and all(r[0] == "area" for r in ex[1:])
    assert ex[-1][1] == "Δασαρχείου Καλαμπάκας" and ex[-1][2] == "2026-06-30"


def test_real_db_area_acts_resolve_to_registry_authorities(conn):
    """The lanes (user, 2026-08-21): an area act's service phrase resolves to
    the registry's canonical authority — 231 of 232, the one left names a
    directorate the registry does not carry («Διεύθυνσης Δασών Φθιώτιδας»);
    the page says «service not matched» for it, never a guess. A completion
    act accepting ONE part records which service (23 of the 24 «για το
    τμήμα» subjects; the 24th names the part by title, not by service)."""
    import json
    rows = conn.execute(
        "SELECT ada, scope_text, scope_auth FROM contract_extension_acts WHERE scope = 'area'").fetchall()
    assert len(rows) == 232
    unresolved = [(r[0], r[1]) for r in rows if not json.loads(r[2] or "[]")]
    assert unresolved == [("ΕΩ564653Π8-1ΙΖ", "Διεύθυνσης Δασών Φθιώτιδας")]
    # no watermark ever survives inside a service phrase
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE scope_text LIKE '%ΑΔΑ:%'").fetchone()[0] == 0
    # non-area acts carry no authorities
    assert conn.execute(
        "SELECT COUNT(*) FROM contract_extension_acts WHERE scope IS NOT 'area' "
        "AND scope_auth IS NOT NULL AND scope_auth != '[]'").fetchone()[0] == 0
    # the worked example: the Καλαμπάκα chain's area acts name five services
    names = set()
    for (sa,) in conn.execute(
            "SELECT scope_auth FROM contract_extension_acts WHERE attributed_ref = '25SYMV016670155'"):
        names.update(json.loads(sa or "[]"))
    assert names == {"Δασαρχείο Καλαμπάκας", "Δασαρχείο Λάρισας", "Δασαρχείο Μουζακίου",
                     "Δασαρχείο Σπερχειάδας"}
    parts = dict(conn.execute(
        "SELECT ada, part_auth FROM contract_completion_acts WHERE part_auth IS NOT NULL"))
    assert len(parts) == 23
    assert parts["Ψ2ΚΞ4653Π8-44Ι"] == "Δασαρχείο Σπερχειάδας"
    assert conn.execute(
        "SELECT part_auth FROM contract_completion_acts WHERE ada = 'ΨΞΛ64653Π8-ΟΒΗ'").fetchone()[0] is None


def test_real_db_the_keying_error_families_are_on_their_own_contracts(conn):
    # lot 15Α's and 4Α's acts (the curated overrides) never sit on 15Γ / 4Δ
    for wrong in ("23SYMV013019416", "23SYMV012946406"):
        subj = conn.execute(
            "SELECT COUNT(*) FROM contract_extension_acts WHERE cited_ref = ? AND "
            "(subject LIKE '%(15Α)%' OR subject LIKE '%(4Α)%')", (wrong,)).fetchone()[0]
        assert subj == 0
