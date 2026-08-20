"""The Anti-nero contractor display-name layer.

One canonical name per ΑΦΜ, read from the documents and printed in one
typography (DATA_DECISIONS 2026-08-20). The rules are small and every one of
them was learned from a name that came out wrong, so each has a test.
"""
import json
import sqlite3

import pytest

from khmdhs import contractor_names_loader as loader
from khmdhs.config import DEFAULT_DB
from scripts.extract_contractor_names import (documented_patronymic,
                                              mark_venture, person_name, polish)


def _mention(text, source="24AWRD000000001"):
    return {"excerpt": text, "source": source}


# --- typography --------------------------------------------------------------

def test_the_legal_form_is_always_dotted():
    assert polish("ΗΡΩΝ ΑΕ") == "ΗΡΩΝ Α.Ε."
    assert polish("ΖΙΤΑΚΑΤ ΑΤΕΒΕ") == "ΖΙΤΑΚΑΤ Α.Τ.Ε.Β.Ε."
    assert polish("ENCODIA Ι.Κ.Ε") == "ENCODIA Ι.Κ.Ε."


def test_a_greek_form_typed_in_latin_is_folded_back_but_a_latin_name_is_not():
    assert polish("ΤΕΧΝΟΟΜΟΙΟΣΤΑΣΗ E.E.") == "ΤΕΧΝΟΟΜΟΙΟΣΤΑΣΗ Ε.Ε."
    assert polish("P. & C. DEVELOPMENT S.A.") == "P. & C. DEVELOPMENT S.A."
    assert polish("BIODASOS-ΤΕΧΝΗ") == "BIODASOS-ΤΕΧΝΗ"


def test_ampersand_joins_partners_but_not_a_company_object():
    assert polish("ΛΑΜΠΟΣ ΙΩΑΝΝΗΣ ΚΑΙ ΣΙΑ ΕΕ") == "ΛΑΜΠΟΣ ΙΩΑΝΝΗΣ & ΣΙΑ Ε.Ε."
    kept = polish("Γ.Ι. ΚΑΡΝΟΜΟΥΡΑΚΗΣ ΑΝΩΝΥΜΗ ΞΕΝΟΔΟΧΕΙΑΚΗ ΚΑΙ ΕΚΜΕΤΑΛΛΕΥΣΕΩΣ ΑΚΙΝΗΤΩΝ")
    assert "ΚΑΙ ΕΚΜΕΤΑΛΛΕΥΣΕΩΣ" in kept


def test_a_pdf_homoglyph_is_pulled_back_into_its_alphabet():
    # U+2206 INCREMENT standing in for Δ, and Latin letters inside a Greek word
    assert polish("ΠΑΠΑ∆ΟΠΟΥΛΟΣ") == "ΠΑΠΑΔΟΠΟΥΛΟΣ"


def test_a_venture_carries_one_marker_at_the_front():
    assert mark_venture("ΚΟΙΝΟΠΡΑΞΙΑ ΤΙΓΚΑΣ - ΧΑΤΖΗΝΙΚΟΛΑΟΥ") == \
        "Κ/Ξ ΤΙΓΚΑΣ - ΧΑΤΖΗΝΙΚΟΛΑΟΥ"
    assert mark_venture("ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΠΙΕΡΙΑΣ 2025 Κ Ξ") == \
        "Κ/Ξ ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΠΙΕΡΙΑΣ 2025"
    assert mark_venture("ΚΟΙΝΟΠΡΑΞΙΑ ΟΙΚΟΝΟΜΙΚΩΝ ΦΟΡΕΩΝ ΣΙΔΕΡΗ ΜΑΡΙΑ") == \
        "Κ/Ξ ΣΙΔΕΡΗ ΜΑΡΙΑ"


# --- the patronymic ----------------------------------------------------------

def test_the_document_proves_the_patronymic_and_the_register_spells_it():
    """A mis-rendered PDF writes «του Αθαναςύου» and «του ΚΩΝ/ΝΟΥ»; the register
    holds the clean ΑΘΑΝΑΣΙΟΣ. The document proves, the register spells."""
    gen, how, src = documented_patronymic(
        "ΛΙΟΛΙΟΣ", "ΑΡΙΣΤΟΒΟΥΛΟΣ", "ΑΘΑΝΑΣΙΟΣ", "",
        [_mention("«ΛΙΟΛΙΟΣ ΑΡΙΣΤΟΒΟΥΛΟΣ ΤΟΥ ΑΘΑΝΑΣΙΟΥ», με έδρα", "24AWRD014169467")])
    assert (gen, how, src) == ("ΑΘΑΝΑΣΙΟΥ", "document, spelled from the register",
                               "24AWRD014169467")


def test_the_article_in_front_of_a_name_is_not_a_patronymic():
    """«β) του Ευάγγελο Μαναρίτσα του Κωνσταντίνου» has a «του» on either side
    and only the second one is the patronymic."""
    gen, _, _ = documented_patronymic(
        "ΜΑΝΑΡΙΤΣΑΣ", "ΕΥΑΓΓΕΛΟΣ", "ΚΩΝΣΤΑΝΤΙΝΟΣ", "",
        [_mention("και β) του Ευάγγελο Μαναρίτσα του Κωνσταντίνου, ο οποίος")])
    assert gen == "ΚΩΝΣΤΑΝΤΙΝΟΥ"


def test_nothing_is_invented_when_no_document_holds_it():
    gen, how, _ = documented_patronymic("ΓΚΑΡΓΚΑΝΙΤΗΣ", "ΛΑΜΠΡΟΣ", "", "",
                                        [_mention("ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ ΑΦΜ")])
    assert gen == "" and how == "no patronymic documented"
    name, how, _ = person_name("ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ", ["ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ"],
                               [_mention("ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ ΑΦΜ")])
    assert name == "ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ"


def test_a_register_and_a_document_that_disagree_are_a_conflict_not_a_guess():
    gen, how, _ = documented_patronymic(
        "ΠΑΠΑΔΟΠΟΥΛΟΣ", "ΝΙΚΟΛΑΟΣ", "ΓΕΩΡΓΙΟΣ", "",
        [_mention("τον ΠΑΠΑΔΟΠΟΥΛΟ ΝΙΚΟΛΑΟ ΤΟΥ ΧΑΡΑΛΑΜΠΟΥ, με έδρα")])
    assert gen == "" and how.startswith("CONFLICT")


def test_a_double_given_name_is_not_the_patronymic():
    """ΓΕΜΗ writes «ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚ ΚΩΝΣΤΑΝΤΙΝΟΣ» — the
    patronymic is the LAST token and the middle ones are the given name."""
    name, _, _ = person_name(
        "ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚ ΚΩΝΣΤΑΝΤΙΝΟΣ",
        ["ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ - ΒΑΣΙΛΙΚΗ ΤΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥ"],
        [_mention("την ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ- ΒΑΣΙΛΙΚΗ του ΚΩΝΣΤΑΝΤΙΝΟΥ, με")])
    assert name == "ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚΗ ΤΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥ"


def test_an_initial_in_the_register_is_not_the_given_name():
    """«ΦΙΛΙΠΠΑΚΗΣ Μ. ΠΑΝΤΕΛΗΣ»: Μ. is the patronymic's initial, ΠΑΝΤΕΛΗΣ the
    given name, and the contract spells the rest."""
    name, _, _ = person_name(
        "ΦΙΛΙΠΠΑΚΗΣ Μ. ΠΑΝΤΕΛΗΣ — εργολήπτης δημοσίων έργων", [],
        [_mention("τον Παντελή Φιλιππάκη του Ματθαίου, Δασολόγο – Ε.Δ.Ε.")])
    assert name == "ΦΙΛΙΠΠΑΚΗΣ ΠΑΝΤΕΛΗΣ ΤΟΥ ΜΑΤΘΑΙΟΥ"


# --- the loader --------------------------------------------------------------

def test_loader_refuses_a_key_that_is_not_an_afm(tmp_path):
    p = tmp_path / "names.json"
    p.write_text(json.dumps({"12345": {"name": "Χ"}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="not an ΑΦΜ"):
        loader.validate(json.loads(p.read_text(encoding="utf-8")))


def test_loader_refuses_an_empty_or_numeric_name():
    with pytest.raises(SystemExit, match="has no name"):
        loader.validate({"123456789": {"name": "  "}})
    with pytest.raises(SystemExit, match="a number is not a name"):
        loader.validate({"123456789": {"name": "123456789"}})


# --- real-DB guards ----------------------------------------------------------

@pytest.mark.skipif(not DEFAULT_DB.exists(), reason="committed database not present")
def test_every_in_scope_contractor_has_one_unique_display_name():
    conn = sqlite3.connect(DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT vat, display_el FROM contractor_display_names").fetchall()
    uncovered = conn.execute(
        "SELECT COUNT(DISTINCT co.vat_number) FROM contractors co "
        "JOIN contract_scope s USING (reference_number) WHERE s.in_scope = 1 "
        "AND co.vat_number NOT IN (SELECT vat FROM contractor_display_names)"
    ).fetchone()[0]
    conn.close()
    assert len(rows) == 195 and uncovered == 0
    names = [r["display_el"] for r in rows]
    # two ventures of the same firms would otherwise print the same name
    assert len(set(names)) == len(names)


@pytest.mark.skipif(not DEFAULT_DB.exists(), reason="committed database not present")
def test_the_registry_spellings_are_never_rewritten():
    conn = sqlite3.connect(DEFAULT_DB)
    kept = conn.execute(
        "SELECT COUNT(*) FROM contractors WHERE vat_number = '998342580' "
        "AND name LIKE '%ΚΑΦΕΤΖΗΣ%'").fetchone()[0]
    display = conn.execute("SELECT display_el FROM contractor_display_names "
                           "WHERE vat = '998342580'").fetchone()[0]
    conn.close()
    assert kept and display == "ΒΙΟΣ Α.Ε."
