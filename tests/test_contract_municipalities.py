# -*- coding: utf-8 -*-
"""The municipality extractor's reading rules, pinned on real sentences.

Every string here is copied from a cached contract text; the extractor only
ever proposes, but a proposal that quietly loses half a list — or invents a
δήμος out of a postal address — costs the curator more than it saves.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "extract_contract_municipalities", ROOT / "scripts" / "extract_contract_municipalities.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)


@pytest.fixture(scope="module")
def places():
    gaz = {k: v for k, v in json.loads(
        (ROOT / "khmdhs" / "data" / "greek_municipalities.json").read_text(
            encoding="utf-8")).items() if not k.startswith("_")}
    return ex.Places(gaz), gaz


def names(places, text):
    pl, gaz = places
    hits, unresolved = pl.find(ex.fold(text))
    return [gaz[c]["name"] for c, _via in hits], unresolved


def test_reads_a_list_of_demoi(places):
    got, un = names(places, "χωροθετούνται εντός των Δήμων Μεγαρέων και Μάνδρας – "
                            "Ειδυλλίας της Περιφερειακής Ενότητας Δυτικής Αττικής")
    assert got == ["Μεγαρέων", "Μάνδρας - Ειδυλλίας"]
    assert un == []


def test_a_name_not_introduced_as_a_demos_is_not_a_work_location(places):
    """The contractor's seat and the Π.Ε. itself share names with δήμοι —
    matching the vocabulary anywhere put 93 assignments outside the
    contract's own Π.Ε."""
    got, _ = names(places, "ο ανάδοχος εδρεύει στη Δράμα, οδός Λαμπριανίδου 12")
    assert got == []


def test_the_run_stops_where_the_sentence_turns_to_the_pe(places):
    got, _ = names(places, "εντός των Δήμων Πρεσπών, Φλώρινας και Αμυνταίου της "
                           "Περιφερειακής Ενότητας Φλώρινας (NUTS: EL533), τα "
                           "προτεινόμενα έργα αρμοδιότητας της Διεύθυνσης Δασών "
                           "Πρέβεζας")
    assert got == ["Πρεσπών", "Φλώρινας", "Αμυνταίου"]


def test_one_misspelling_does_not_take_the_rest_of_the_list(places):
    """24SYMV014774694 writes «ΗΡΑΚΕΙΑΣ»; before the token walk, the whole
    list died with it."""
    got, un = names(places, "εντός των Δήμων Ηράκειας και Σιντικής της "
                            "Περιφερειακής Ενότητας Σερρών")
    assert "Σιντικής" in got


def test_post_kallikratis_names_resolve_onto_the_unit_we_have(places):
    """The polygon layer is Καλλικράτης 2010; ν.4600/2019 renamed and split
    units, and the contracts use the current names."""
    pl, gaz = places
    for text, expect in (("εντός των Δήμων Μετεώρων", "Καλαμπάκας"),
                         ("εντός των Δήμων Δυτικής Λέσβου και Μυτιλήνης", "Λέσβου"),
                         ("εντός του Δήμου Καμένων Βούρλων", "Μώλου - Αγ. Κωνσταντίνου")):
        hits, _ = pl.find(ex.fold(text))
        assert expect in [gaz[c]["name"] for c, _ in hits], text
        assert all(via == "rename" for _c, via in hits), text


def test_the_hyphen_may_be_any_of_six_or_missing(places):
    for spelling in ("Ξυλοκάστρου - Ευρωστίνης", "Ξυλοκάστρου Ευρωστίνης",
                     "Ξυλοκάστρου‐Ευρωστίνης", "Ξυλοκάστρου – Ευρωστίνης"):
        got, _ = names(places, f"εντός του Δήμου {spelling} της Π.Ε. Κορινθίας")
        assert got == ["Ξυλοκάστρου - Ευρωστίνης"], spelling


def test_the_page_break_watermark_does_not_hide_the_name(tmp_path):
    """pdftotext keeps «ΣΕΛ.4 24SYMV014498953 2024-03-29» in the running text,
    and it lands between «Δήμου» and the name it introduces."""
    p = tmp_path / "24SYMV014498953.txt"
    p.write_text("εντός του Δήμου ΣΕΛ.4 24SYMV014498953 2024-03-29 Πάτμου, της "
                 "Π.Ε. Καλύμνου", encoding="utf-8")
    raw, folded, owner = ex.read_chain(["24SYMV014498953"], tmp_path)
    assert "ΣΕΛ" not in raw and "2024-03-29" not in raw
    assert owner == [(0, "24SYMV014498953")]
    assert len(folded) == len(raw)          # the excerpt slicing depends on it


def _parse(text):
    """Run the real reader over one sentence."""
    from khmdhs.forest_loader import Matcher, load_registry
    from khmdhs.greek_regions import PE_CENTROIDS
    gaz = {k: v for k, v in json.loads(
        (ROOT / "khmdhs" / "data" / "greek_municipalities.json").read_text(
            encoding="utf-8")).items() if not k.startswith("_")}
    registry, *_ = load_registry()
    sts = ex.statements(text, ex.fold(text), [(0, "X")], ex.Places(gaz),
                        Matcher(registry),
                        {ex.fold(k.replace("Π.Ε. ", "")): k for k in PE_CENTROIDS})
    names = lambda g: [gaz[c]["name"] for c, _via in g["codes"]]
    return sts, names


def test_statement_reads_authority_and_pe_from_the_same_sentence():
    """The unit is the authority: who, where, and the Π.Ε. and NUTS the
    document itself states beside them."""
    sts, names = _parse(
        "Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου Μεγάρων "
        "χωροθετούνται εντός των Δήμων Μεγαρέων και Μάνδρας – Ειδυλλίας "
        "της Περιφερειακής Ενότητας Δυτικής Αττικής (NUTS: EL306).")
    assert len(sts) == 1
    s = sts[0]
    assert s["authorities"] == ["Δασαρχείο Μεγάρων"] and s["authority_where"] == "before"
    assert len(s["groups"]) == 1
    g = s["groups"][0]
    assert g["pe_stated"] == "Π.Ε. Δυτικής Αττικής" and g["nuts"] == "EL306"
    assert names(g) == ["Μεγαρέων", "Μάνδρας - Ειδυλλίας"]


def test_the_authority_may_be_named_after_the_demoi():
    """24SYMV014192289 writes it the other way round, and reading only
    «αρμοδιότητας X … χωροθετούνται» labelled the sentence authority-less."""
    sts, _ = _parse("χωροθετούνται εντός των Δήμων Ζαχάρως και Ανδρίτσαινας – "
                    "Κρέστενας, της Περιφερειακής Ενότητας Ηλείας, αρμοδιότητας "
                    "Δασαρχείου Ολυμπίας και συγκεκριμένα τη δημιουργία ζώνης.")
    assert sts[0]["authorities"] == ["Δασαρχείο Ολυμπίας"]
    assert sts[0]["authority_where"] == "after"


def test_one_authority_can_hold_two_pe_groups():
    """§3.6 of 25SYMV016570021: one Δασαρχείο, two Π.Ε., and stopping at the
    first Π.Ε. clause silently dropped five δήμοι."""
    sts, names = _parse(
        "Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου Αιγάλεω "
        "χωροθετούνται εντός των Δήμων Μάνδρας – Ειδυλλίας, Ελευσίνας και "
        "Ασπρόπυργου της Περιφερειακής Ενότητας Δυτικής Αττικής (ΝUTS: EL306 – "
        "Δυτική Αττική) και των Δήμων Χαϊδαρίου, Αγίας Βαρβάρας, Πετρούπολης, "
        "Ιλίου (Νέων Λιοσίων) και Αγίων Αναργύρων – Καματερού της "
        "Περιφερειακής Ενότητας Δυτικού Τομέα Αθηνών (ΝUTS: EL302).")
    assert len(sts) == 1 and len(sts[0]["groups"]) == 2
    a, b = sts[0]["groups"]
    assert a["pe_stated"] == "Π.Ε. Δυτικής Αττικής"
    assert names(a) == ["Μάνδρας - Ειδυλλίας", "Ελευσίνας", "Ασπροπύργου"]
    assert b["pe_stated"] == "Π.Ε. Δυτικού Τομέα Αθηνών"
    # «Ιλίου (Νέων Λιοσίων)» — an aside inside the list, not the end of it
    assert names(b) == ["Χαϊδαρίου", "Αγίας Βαρβάρας", "Πετρούπολης", "Ιλίου",
                        "Αγίων Αναργύρων - Καματερού"]


def test_each_authority_is_its_own_statement():
    """A five-lot contract lists five Δασαρχεία in one paragraph; the window
    after the placement verb is a lookahead so none swallows the next."""
    one = ("Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου {a} χωροθετούνται "
           "εντός του Δήμου {d} της Περιφερειακής Ενότητας {p}. ")
    sts, _ = _parse(one.format(a="Μεγάρων", d="Μεγαρέων", p="Δυτικής Αττικής")
                    + one.format(a="Πόρου", d="Πόρου", p="Νήσων")
                    + one.format(a="Λαυρίου", d="Λαυρεωτικής", p="Ανατολικής Αττικής"))
    assert [s["authorities"][0] for s in sts] == [
        "Δασαρχείο Μεγάρων", "Δασαρχείο Πόρου", "Δασαρχείο Λαυρίου"]


def test_the_same_authority_stated_twice_is_one_statement():
    """Άρθρο 3 summarises what §3.6 then lists; the card must not show the
    same authority twice, and the richer reading must win."""
    sts, names = _parse(
        "οι εκτάσεις αρμοδιότητας του Δασαρχείου Μεγάρων χωροθετούνται εντός "
        "του Δήμου Μεγαρέων. Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου "
        "Μεγάρων χωροθετούνται εντός των Δήμων Μεγαρέων και Μάνδρας – "
        "Ειδυλλίας της Περιφερειακής Ενότητας Δυτικής Αττικής (NUTS: EL306).")
    assert len(sts) == 1
    assert sorted(n for g in sts[0]["groups"] for n in names(g)) == [
        "Μάνδρας - Ειδυλλίας", "Μεγαρέων"]


def test_a_call_lists_every_lot_and_only_ours_may_be_taken():
    """The πρόσκληση describes all its τμήματα; a contract may only take the
    blocks of the Δασαρχείο it actually holds, or it inherits its siblings'
    work (DATA_DECISIONS 2026-08-19)."""
    sts, names = _parse(
        "Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου Ολυμπίας "
        "χωροθετούνται εντός του Δήμου Ζαχάρως της Περιφερειακής Ενότητας "
        "Ηλείας. Τα προτεινόμενα έργα αρμοδιότητας του Δασαρχείου Κιλκίς "
        "χωροθετούνται εντός του Δήμου Κιλκίς της Περιφερειακής Ενότητας "
        "Κιλκίς.")
    mine = {"Δασαρχείο Ολυμπίας"}
    kept = [b for b in sts if set(b["authorities"]) & mine]
    assert [b["authorities"][0] for b in kept] == ["Δασαρχείο Ολυμπίας"]
    assert [n for g in kept[0]["groups"] for n in names(g)] == ["Ζαχάρως"]


def test_the_curator_page_is_syntactically_valid(tmp_path):
    """An apostrophe inside a single-quoted JS string («this contract's
    authorities») shipped a page that rendered nothing at all: the data was
    fine, the script died on parse. Cheap guard — balance the quotes of every
    JS string literal in the generated page."""
    import re
    page = ROOT / "municipality_curator.html"
    assert page.exists(), "run scripts/extract_contract_municipalities.py first"
    html = page.read_text(encoding="utf-8")
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    for line in script.splitlines():
        if line.startswith("const DATA = "):
            continue                                  # the embedded payload
        line = re.sub(r"\\.", "", line)               # escaped characters
        line = re.sub(r'"[^"]*"', '""', line)         # double-quoted strings
        line = re.sub(r"`[^`]*`", "``", line)         # template literals
        line = re.sub(r"//.*$", "", line)             # comments may say «don't»
        assert line.count("'") % 2 == 0, line


def test_curated_overrides_are_valid():
    """Every attribution verdict must name a municipality that exists and
    authorities that exist — six of the first nine codes were written from
    memory and pointed at the wrong δήμος (Αρριανών came out as Παγγαίου)."""
    from khmdhs.forest_loader import GAZETTEER_FILE, REGISTRY_FILE
    gaz = {k: v for k, v in json.loads(
        GAZETTEER_FILE.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    auth = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))["authorities"]
    data = json.loads((ROOT / "khmdhs" / "data" /
                       "municipality_overrides.json").read_text(encoding="utf-8"))
    n = 0
    for key, v in data.items():
        if key.startswith("_"):
            continue
        n += 1
        ref, code = key.split("|")
        assert ref.startswith(("2", "1")) and "SYMV" in ref, key
        assert code in gaz, f"{key}: unknown municipality code"
        assert v["basis"] in ("reattributed", "as_stated"), key
        assert v["authority"] in auth, f"{key}: unknown authority {v['authority']}"
        assert v["stated_authority"] in auth, key
        assert v["note"].strip(), f"{key}: a verdict without a reason"
        if v["basis"] == "as_stated":
            assert v["authority"] == v["stated_authority"], key
    assert n >= 9


def test_registered_jurisdictions_are_real_regional_units():
    """`covers_pe` records a service's reach beyond its seat Π.Ε., confirmed
    by the user (2026-08-19). Every entry must name a real Π.Ε. and carry the
    reason it was accepted."""
    from khmdhs.forest_loader import REGISTRY_FILE
    from khmdhs.greek_regions import PE_CENTROIDS
    auth = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))["authorities"]
    covers = {n: a for n, a in auth.items() if a.get("covers_pe")}
    assert len(covers) >= 8
    for name, a in covers.items():
        for pe in a["covers_pe"]:
            assert pe in PE_CENTROIDS, f"{name}: unknown Π.Ε. {pe}"
            assert pe != a["region_pe"], f"{name}: {pe} is already its seat"
        assert a.get("covers_pe_note", "").strip(), f"{name}: no reason recorded"
    assert "Π.Ε. Ιθάκης" in covers["Διεύθυνση Δασών Κεφαλληνίας"]["covers_pe"]
    assert "Π.Ε. Ικαρίας" in covers["Διεύθυνση Δασών Σάμου"]["covers_pe"]
