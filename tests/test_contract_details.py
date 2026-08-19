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
    hit = next(h for h in wt.read_title(title) if h.key == "miktes_zones")
    core = hit.excerpt.strip("… ")
    assert core in title


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
