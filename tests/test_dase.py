"""Classifier tests for ΔΑΣΕ contractor names — real observed strings."""
import pytest

from khmdhs.dase import classify_name


@pytest.mark.parametrize("name,form", [
    ("ΔΑ.Σ.Ε ΦΛΑΜΠΟΥΡΑΡΙΟΥ ΤΣΟΥΚΑ ΡΟΣΑ", "dase"),        # the reference contract
    ("ΔΑΣΕ ΣΚΑΛΩΤΗΣ ΑΓΙΟΣ ΙΩΑΝΝΗΣ", "dase"),
    ("ΔΑΣΕ ΣΚΑΛΩΤΗΣ ΑΓ. ΙΩΑΝΝΗΣ", "dase"),
    ("Δ.Α.Σ.Ε. ΠΡΟΜΑΧΩΝ", "dase"),
    ("ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΑΙΣΥΜΗΣ Β'", "dase"),
    ("ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΠΡΟΜΑΧΩΝ \"ΤΑ ΜΑΚΕΔΟΝΙΚΑ\"", "dase"),
    ("Δασικός Συνεταιρισμός Εργασίας Χρυσομηλιάς", "dase"),   # mixed case
    ("ΔΑΣΕΡΓΑΤΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΛΑΤΕΙΑΣ", "daseragikos"),
    ("ΑΝΑΓΚΑΣΤΙΚΟΣ ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΚΑΛΑΜΠΑΚΑΣ", "adse"),
    ("Α.Δ.Σ.Ε. ΚΑΛΑΜΠΑΚΑΣ", "adse"),
])
def test_true_positives(name, form):
    verdict, f = classify_name(name)
    assert verdict == "dase" and f == form, (name, verdict, f)


@pytest.mark.parametrize("name", [
    "ΚΕΝΤΡΟ ΔΙΑΣΚΕΔΑΣΕΩΣ Η ΩΡΑΙΑ ΕΛΛΑΣ",     # observed false positive
    "ΕΥΑΓΓΕΛΟΣ ΛΕΙΒΑΔΑΣΕ",                    # observed false positive
    "ΕΡΓΑ ΠΡΑΣΙΝΟΥ ΑΝΩΝΥΜΗ ΤΕΧΝΙΚΗ ΕΤΑΙΡΕΙΑ",
    "ΔΑΣΚΑΛΑΚΗΣ ΙΩΑΝΝΗΣ",
    "ΔΑΣΟΤΕΧΝΙΚΑ ΕΡΓΑ ABIES Ε.Ε.",            # forestry firm, NOT a coop
    "",
])
def test_negatives(name):
    assert classify_name(name)[0] == "no", name


@pytest.mark.parametrize("name", [
    "ΑΓΡΟΤΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΖΑΓΟΡΑΣ",
    "ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΜΕΤΣΟΒΟΥ",        # no ΔΑΣ context → human decides
])
def test_review_queue(name):
    assert classify_name(name)[0] == "review", name


@pytest.mark.parametrize("name", [
    "ΕΔΑΣΕ ΦΛΑΜΠΟΥΡΕΣΙΟΥ ΤΥΜΦΑΙΩΝ ΚΑΛΑΜΠΑΚΑΣ",
    "ΣΤ ΄ΕΔΑΣΕ ΧΡΥΣΟΜΗΛΙΑΣ ΚΑΙ ΠΑΛΑΙΟΧΩΡΙΟΥ",
    "ΟΔΑΣΕ ΜΗΛΙΑΣ ΚΑΛΑΜΠΑΚΑΣ",
])
def test_edase_forms(name):
    verdict, form = classify_name(name)
    assert verdict == "dase" and form == "edase", (name, verdict, form)
