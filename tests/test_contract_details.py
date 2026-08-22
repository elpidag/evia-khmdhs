"""Units for the two proposal layers read from the signed contracts:
the deadline clause (`khmdhs.contract_durations`) and the multi-label work
themes (`khmdhs.work_themes`). DATA_DECISIONS 2026-08-19.

Every case here is a sentence that actually appears in the corpus, and most
of them are the ones that broke an earlier pass.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from khmdhs import contract_durations as dur
from khmdhs import work_themes as wt
from khmdhs.config import DEFAULT_DB, PDF_CACHE_DIR


# --------------------------------------------------------------- durations

def test_reads_the_plain_clause():
    got = dur.read("Η συνολική προθεσμία ολοκλήρωσης του Έργου ορίζεται σε "
                   "τρεις (3) μήνες από την υπογραφή της παρούσας σύμβασης.")
    assert (got.n, got.unit, got.basis) == (3, "months", "signature")
    assert got.subject == "works"
    assert "τρεις (3) μήνες" in got.excerpt


def test_reads_days_and_the_works_start_basis():
    got = dur.read("Ο χρόνος εκτέλεσης και ολοκλήρωσης των Εργασιών ορίζεται "
                   "σε ενενήντα (90) ημερολογιακές ημέρες από την ημερομηνία "
                   "έναρξης αυτών.")
    assert (got.n, got.unit, got.basis) == (90, "days", "works_start")
    assert got.days == 90


def test_the_penalty_clause_is_not_a_deadline():
    """«…ποινική ρήτρα ίση με δεκαπέντε τοις εκατό (15%) … ανά ημέρα» read as
    «15 days» on 65 contracts until the clause had to DEFINE something."""
    assert dur.read(
        "Για κάθε ημερολογιακή ημέρα υπέρβασης της συνολικής προθεσμίας "
        "πέρατος του Έργου επιβάλλεται στον Ανάδοχο ποινική ρήτρα ίση με "
        "δεκαπέντε τοις εκατό (15%) της μέσης ημερήσιας αξίας.") is None


def test_a_design_build_contract_gives_the_works_deadline_not_the_study():
    """Both sentences are true; only one is the contract's deadline."""
    got = dur.read(
        "3.3 Ο χρόνος παράδοσης της Μελέτης ορίζεται σε είκοσι (20) "
        "ημερολογιακές ημέρες από την υπογραφή της παρούσας Σύμβασης. "
        "3.5 Ο χρόνος εκτέλεσης και ολοκλήρωσης των Εργασιών ορίζεται σε "
        "τρεις (3) μήνες από την ημερομηνία έναρξης αυτών.")
    assert (got.n, got.unit, got.subject) == (3, "months", "works")


def test_a_study_only_clause_is_returned_but_marked():
    got = dur.read("Ο χρόνος παράδοσης της Μελέτης ορίζεται σε είκοσι (20) "
                   "ημερολογιακές ημέρες από την υπογραφή της Σύμβασης.")
    assert (got.n, got.unit, got.subject) == (20, "days", "study")
    assert any("μελέτη" in n for n in got.notes)


def test_the_vat_line_before_the_article_does_not_reject_it():
    """«…αφορά στον ΦΠΑ 24%. Άρθρο 3 Διάρκεια Σύμβασης…» — the percent sign
    belongs to the previous paragraph and cost 16 contracts their clause."""
    got = dur.read("χρηματικό ποσό ίσο με 548.393,69 ευρώ και αφορά στον ΦΠΑ "
                   "24%. Άρθρο 3 Διάρκεια Σύμβασης - Προθεσμίες 3.1 Η συνολική "
                   "διάρκεια της σύμβασης ορίζεται σε δέκα (10) μήνες από την "
                   "υπογραφή της.")
    assert (got.n, got.unit) == (10, "months")


def test_reads_through_the_font_mangling():
    """Some phase-II PDFs put every accent in as a separate letter."""
    got = dur.read("Η μεέγιστη συνολικηέ προθεσμιέα ολοκληήρωσης εργασιωήν "
                   "οριήζεται σε τρεις (3) μηήνες αποή την υπογραφηή της "
                   "παρουήσας.")
    assert (got.n, got.unit, got.basis) == (3, "months", "signature")


def test_a_bare_number_is_read_and_said_to_be_bare():
    got = dur.read("Η συνολική προθεσμία για την περαίωση του αντικειμένου "
                   "της σύμβασης ορίζεται σε 4 μήνες από την υπογραφή της "
                   "παρούσας.")
    assert (got.n, got.unit) == (4, "months")
    assert any("bare number" in n for n in got.notes)


def test_the_chain_names_the_document_it_read():
    """An amendment's own PDF is a cover note; the deadline is the σύμβαση's,
    and the read must say which document stated it."""
    got = dur.read_chain([
        ("23SYMV013600200", "Η συνολική προθεσμία για την περαίωση του "
                            "αντικειμένου της σύμβασης ορίζεται σε 90 "
                            "ημερολογιακές ημέρες από την υπογραφή της."),
        ("24SYMV015185915", "τροποποίηση της σύμβασης"),
    ])
    assert got.source == "23SYMV013600200" and got.n == 90


def test_fold_map_brings_offsets_home():
    text = "Η συνολική προθεσμία ορίζεται σε τρεις (3) μήνες."
    up, idx = dur.fold_map(text)
    assert len(idx) == len(up) + 1
    at = up.index("ΜΗΝΕΣ")
    assert text[idx[at]:].startswith("μήνες")


# ------------------------------------------------------------- work themes

def test_a_title_can_state_several_themes():
    hits = wt.read_title(
        "Εργασίες ειδικών δασοτεχνικών έργων του άρθρου 16 παρ. 5 του ν. "
        "998/1979 για τον καθαρισμό των δασών και δασικών εκτάσεων και τη "
        "συντήρηση του δασικού οδικού δικτύου αρμοδιότητας Δασαρχείου Αρναίας")
    keys = [h.key for h in hits]
    assert "katharismoi" in keys and "odiko_diktyo" in keys
    assert len(keys) == len(set(keys))


def test_the_generic_title_states_no_theme():
    """93 contracts say only «αντιπυρική προστασία» — an honest nothing."""
    assert wt.read_title(
        "Έργα αντιπυρικής προστασίας σε δημόσιες δασικές εκτάσεις "
        "αρμοδιότητας Δασαρχείων Αιγάλεω και Πάρνηθας") == []


def test_the_theme_excerpt_is_verbatim_from_the_title():
    title = ("Εργασίες για τη δημιουργία εστεγασμένων αντιπυρικών ζωνών "
             "στην Π.Ε. Ηλείας")
    hit = next(h for h in wt.read_title(title) if h.key == "estegasmenes_zones")
    core = hit.excerpt.strip("… ")
    assert core in title


# --- the corrected vocabulary (DATA_DECISIONS 2026-08-22) -----------------

def test_firebreaks_are_three_disjoint_themes():
    """The generic «ΑΝΤΙΠΥΡΙΚ ΖΩΝ» theme is retired: each mention lands on
    exactly one of συντήρηση / μικτές / εστεγασμένες, by its own verb."""
    maint = wt.read_title(
        "Εργασίες για τον καθαρισμό των δασών και δασικών εκτάσεων καθώς και "
        "για τη συντήρηση του δασικού οδικού δικτύου και των αντιπυρικών "
        "ζωνών, σε εκτάσεις ευθύνης των Δασαρχείων Μεγάρων και Πάρνηθας")
    keys = {h.key for h in maint}
    assert "syntirisi_zonon" in keys and "odiko_diktyo" in keys
    assert "miktes_zones" not in keys and "estegasmenes_zones" not in keys

    mixed = {h.key for h in wt.read_title(
        "Δημιουργία Μικτών Αντιπυρικών Ζωνών σε οικισμούς και δρόμους της "
        "Π.Ε. Δυτικής Αττικής αρμοδιότητας Δασαρχείου Αιγάλεω")}
    assert mixed == {"miktes_zones"}

    sheltered = {h.key for h in wt.read_title(
        "Εργασίες για τη δημιουργία εστεγασμένων αντιπυρικών ζωνών, σε "
        "εκτάσεις ευθύνης των Δασαρχείων Λαμίας και Αταλάντης")}
    assert sheltered == {"estegasmenes_zones"}


def test_the_maintenance_verb_never_reaches_across_a_creation_clause():
    """«συντήρηση του οδικού δικτύου ΚΑΙ ΤΗ ΔΗΜΙΟΥΡΓΙΑ μικτών ζωνών» — the
    συντήρηση governs the roads only; the tempered guard stops it."""
    keys = {h.key for h in wt.read_title(
        "Εργασίες για τη συντήρηση του δασικού οδικού δικτύου και τη "
        "δημιουργία μικτών αντιπυρικών ζωνών της Π.Ε. Εύβοιας")}
    assert keys == {"odiko_diktyo", "miktes_zones"}


def test_roads_as_location_are_not_road_work():
    """«σε δασικούς δρόμους» names WHERE the zones go; 15 of the old 75
    road links were that (DATA_DECISIONS 2026-08-22)."""
    keys = {h.key for h in wt.read_title(
        "Δημιουργία μικτών αντιπυρικών ζωνών σε δασικούς δρόμους της "
        "Π.Ε. Εύβοιας, αρμοδιότητας Δασαρχείου Χαλκίδας")}
    assert keys == {"miktes_zones"}
    # …and πλευρικός καθαρισμός along roads is clearing, not road work
    keys = {h.key for h in wt.read_title(
        "Έργα αντιπυρικής προστασίας σε δημόσιους δασικούς δρόμους και "
        "δασικές εκτάσεις, αρμοδιότητας των Δασαρχείων Μεσολογγίου")}
    assert keys == set()


def test_approved_studies_are_an_input_not_a_deliverable():
    """«ΜΕ ΕΓΚΕΚΡΙΜΕΝΕΣ ΜΕΛΕΤΕΣ» = works under already-approved studies —
    never the studies theme; «Κατάρτιση Σχεδίου» IS study work."""
    keys = {h.key for h in wt.read_title(
        "ΕΡΓΑΣΙΕΣ ΓΙΑ ΤΗ ΣΥΝΤΗΡΗΣΗ ΔΑΣΙΚΟΥ ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ ΚΑΙ ΑΝΤΙΠΥΡΙΚΩΝ "
        "ΖΩΝΩΝ ΜΕ ΕΓΚΕΚΡΙΜΕΝΕΣ ΜΕΛΕΤΕΣ")}
    assert "meletes" not in keys
    assert {"odiko_diktyo", "syntirisi_zonon"} <= keys

    keys = {h.key for h in wt.read_title(
        "Κατάρτιση Σχεδίου Αντιπυρικής Προστασίας σε περιοχές ευθύνης του "
        "Δασαρχείου Σουφλίου")}
    assert keys == {"meletes"}


def test_bare_firebreak_creation_is_the_fourth_kind():
    """«δημιουργία/διάνοιξη ψιλής αντιπυρικής ζώνης» (user, 2026-08-22) —
    the guards keep the mixed/sheltered creations out, and «υπό διαμόρφωση»
    stays the hand-verdict maintenance case."""
    assert any(h.key == "psiles_zones" for h in wt.read_call(
        "δημιουργία ψιλής αντιπυρικής ζώνης έκτασης 65,00 στρ."))
    assert any(h.key == "psiles_zones" for h in wt.read_title(
        "εργασίες συντήρησης και διάνοιξης δασικού οδικού δικτύου και "
        "αντιπυρικών ζωνών, σε εκτάσεις ευθύνης Δασαρχείου Καλαμπάκας"))
    for s in ("Δημιουργία Μικτών Αντιπυρικών Ζωνών σε οικισμούς",
              "για τη δημιουργία εστεγασμένων αντιπυρικών ζωνών"):
        assert not any(h.key == "psiles_zones" for h in wt.read_title(s))


def test_logging_residues_are_their_own_theme():
    """«διαχείριση υπολειμμάτων υλοτομίας» manages the debris of PAST
    logging — the genitive is not felling (user verdict 1a)."""
    keys = {h.key for h in wt.read_title(
        "Εργασίες για τον καθαρισμό δασών καθώς και τη διαχείριση "
        "υπολειμμάτων υλοτομίας, σε εκτάσεις ευθύνης των Δασαρχείων Λαγκαδά")}
    assert "ypoleimmata" in keys and "ylotomies" not in keys
    # real felling still reads as υλοτομίες
    keys = {h.key for h in wt.read_title(
        "Επείγουσες υλοτομικές εργασίες και δασοκομικοί χειρισμοί ξερών και "
        "προσβεβλημένων ιστάμενων δένδρων")}
    assert "ylotomies" in keys and "dasokomika" in keys and "ypoleimmata" not in keys


def test_cpv_only_asks_where_the_title_is_silent():
    assert wt.cpv_questions({"nero"}, ["44611500-1"]) == []
    assert wt.cpv_questions({"katharismoi"}, ["44611500-1"]) == [
        ("44611500-1", "nero")]
    # the call's boilerplate codes are NOT markers: «Εργασίες συντήρησης
    # οδών» rides on 130 of 246 contracts
    assert wt.cpv_questions({"katharismoi"}, ["45233141-9"]) == []


def test_every_theme_key_has_a_label_and_a_pattern():
    for t in wt.THEMES:
        assert t.key and t.el and t.en and t.pattern
    assert len({t.key for t in wt.THEMES}) == len(wt.THEMES)
    assert set(wt.CPV_MARKERS.values()) <= {t.key for t in wt.THEMES}


# ------------------------------------------------------------- real corpus

@pytest.mark.skipif(not Path(DEFAULT_DB).exists(), reason="needs the built DB")
def test_every_in_scope_contract_states_its_own_time():
    """The point of the layer: the registry has a duration for 83 of the 246
    in-scope contracts; the documents state one for 243, and the other three
    state a SEASON instead — «η αντιπυρική περίοδος του έτους 2024» — which
    is an answer, not a gap."""
    conn = sqlite3.connect(DEFAULT_DB)
    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contract_scope WHERE in_scope = 1")]
    missing = []
    for ref in refs:
        chain, seen, cur = [ref], {ref}, ref
        while True:
            row = conn.execute("SELECT prev_reference_no FROM contracts"
                               " WHERE reference_number = ?", (cur,)).fetchone()
            prev = row[0] if row else None
            if not prev or prev in seen:
                break
            chain.append(prev)
            seen.add(prev)
            cur = prev
        texts = []
        for m in reversed(chain):
            p = PDF_CACHE_DIR / f"{m}.txt"
            if p.exists():
                texts.append((m, p.read_text(encoding="utf-8", errors="replace")))
        if dur.read_chain(texts) is None and not any(
                dur.fire_season(t) for _, t in texts):
            missing.append(ref)
    conn.close()
    assert missing == []
