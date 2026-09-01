# -*- coding: utf-8 -*-
"""Guards on the curated English awarding-body names (DATA_DECISIONS
2026-08-15/16): coverage of the live vocabularies, Latin-only values,
user-decision pins, and byte-identical Atlas copies."""
import json
import sqlite3
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILES = ["authority_names_en.json", "org_names_en.json", "unit_names_en.json"]


def _load(name):
    data = json.loads((ROOT / "khmdhs" / "data" / name).read_text(encoding="utf-8"))
    return {k: v["en"] for k, v in data.items() if not k.startswith("_")}


def _fold(s):
    x = unicodedata.normalize("NFD", (s or "").upper())
    x = "".join(c for c in x if not unicodedata.combining(c))
    return " ".join(x.split())


@pytest.fixture(scope="module")
def dase():
    p = ROOT / "data" / "processed" / "dase.sqlite"
    if not p.exists():
        pytest.skip("committed dase.sqlite not present")
    c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_values_latin_only_and_copies_identical():
    for name in FILES:
        for k, en in _load(name).items():
            assert en.strip(), k
            for ch in en:
                assert "GREEK" not in unicodedata.name(ch, ""), (name, k, en)
        cur = (ROOT / "khmdhs" / "data" / name).read_bytes()
        shipped = (ROOT / "atlas" / "src" / "lib" / "data" / name).read_bytes()
        assert cur == shipped, name


def test_authority_registry_fully_covered():
    p = ROOT / "data" / "processed" / "khmdhs.sqlite"
    if not p.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    k = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    names = _load("authority_names_en.json")
    reg = [r[0] for r in k.execute("SELECT name FROM forest_authorities")]
    k.close()
    assert set(names) == set(reg)
    assert len(reg) == 105
    # user conventions (2026-08-15): toponym-first wording
    for greek, en in names.items():
        if greek.startswith("Δασαρχείο"):
            assert en.endswith(" Forest Service Office"), (greek, en)
        else:
            assert en.endswith(" Forest Directorate"), (greek, en)


def test_live_dase_orgs_and_units_fully_covered(dase):
    from webui.dase_queries import live_filter
    orgs = _load("org_names_en.json")
    for r in dase.execute(f"SELECT DISTINCT co.organization_name o FROM contracts co WHERE {live_filter('co')}"):
        assert r["o"] in orgs, r["o"]
    auth_fold = {_fold(k) for k in _load("authority_names_en.json")}
    unit_fold = {_fold(k) for k in _load("unit_names_en.json")}
    for r in dase.execute(f"SELECT DISTINCT co.units_operator_name u FROM contracts co "
                          f"WHERE {live_filter('co')} AND co.units_operator_name IS NOT NULL"):
        f = _fold(r["u"])
        assert f in auth_fold or f in unit_fold, r["u"]


def test_user_decisions_pinned():
    auth = _load("authority_names_en.json")
    org = _load("org_names_en.json")
    # 2026-08-15 review: Korinthos/Kalampaka/Sparta/Thebes/Mesolongi/Piraeus,
    # A.U.TH. suffix, hospital without the «Μαματσείο» epithet
    assert auth["Δασαρχείο Κορίνθου"] == "Korinthos Forest Service Office"
    assert auth["Δασαρχείο Θηβών"] == "Thebes Forest Service Office"
    assert auth["Δασαρχείο Καλαμπάκας"] == "Kalampaka Forest Service Office"
    assert auth["Δασαρχείο Σπάρτης"] == "Sparta Forest Service Office"
    assert auth["Διεύθυνση Δασών Δωδεκανήσου"] == "Dodecanese Forest Directorate"
    assert org["ΑΡΙΣΤΟΤΕΛΕΙΟ ΠΑΝΕΠΙΣΤΗΜΙΟ ΘΕΣ/ΝΙΚΗΣ"].endswith("(A.U.TH.)")
    assert org["ΓΕΝΙΚΟ ΝΟΣΟΚΟΜΕΙΟ ΚΟΖΑΝΗΣ ΜΑΜΑΤΣΕΙΟ"] == "General Hospital of Kozani"
    assert org["ΔΗΜΟΣ ΛΑΡΙΣΑΙΩΝ"] == "Municipality of Larisa"


# ------------------------------------------------ the place layer (2026-08-26)

def _places():
    """place_names_en.json is a flat Greek → English map, not the {el, en}
    shape the body-name files use."""
    data = json.loads((ROOT / "khmdhs" / "data" / "place_names_en.json")
                      .read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def test_place_names_copies_identical_and_latin_only():
    cur = (ROOT / "khmdhs" / "data" / "place_names_en.json").read_bytes()
    shipped = (ROOT / "atlas" / "src" / "lib" / "data" / "place_names_en.json").read_bytes()
    assert cur == shipped
    for k, en in _places().items():
        for ch in en:
            assert "GREEK" not in unicodedata.name(ch, ""), (k, en)


def test_every_printed_office_string_has_an_english_form():
    """The three entity pages print a registered office; none of them may
    fall back to Greek (user, 2026-08-26: the facts row cannot mix the two
    alphabets)."""
    p = ROOT / "data" / "processed" / "khmdhs.sqlite"
    if not p.exists():
        pytest.skip("committed khmdhs.sqlite not present")
    places = _places()
    k = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    k.row_factory = sqlite3.Row
    for r in k.execute("SELECT name, municipality_name, street, city "
                       "FROM forest_authorities"):
        for col in ("street", "city"):
            v = " ".join((r[col] or "").split())
            if v:
                assert v in places, (r["name"], col, v)
        if not (r["city"] or "").strip():
            v = " ".join((r["municipality_name"] or "").split())
            assert not v or v in places, (r["name"], v)
    k.close()

    contractors = json.loads((ROOT / "khmdhs" / "data" / "contractor_locations.json")
                             .read_text(encoding="utf-8"))
    rows = contractors if isinstance(contractors, list) else list(contractors.values())
    for row in rows:
        if not isinstance(row, dict):
            continue
        for col in ("address", "city"):
            v = " ".join((row.get(col) or "").replace(" None", "").split())
            if v and v.lower() != "none":
                assert v in places, (col, v)


def test_place_rendering_rules_pinned():
    """The conventions the generator encodes, each one a trap it walked into
    (DATA_DECISIONS 2026-08-26)."""
    pl = _places()
    # an ordinal is English only before the km — a street named after a date
    # keeps the form its own sign carries
    assert pl["107ο χλμ. ΕΟ Αθηνών-Λαμίας"] == "107th km National Road Athinon-Lamias"
    assert pl["25ης Μαρτίου 23"] == "25is Martiou 23"
    # Python uppercases «Τέρμα» to «ΤΈΡΜΑ»: the keys are matched accent-folded
    assert pl["Τέρμα Ομονοίας"] == "End of Omonoias"
    assert pl["Δασικό Κτίριο"] == "Forestry Building"     # user verdict 2026-09-01
    # the 2026-09-01 review's rules (DATA_DECISIONS): «γγ» is «ng», a word
    # starting with «Μπ» takes the familiar «B», a letter after a building
    # number stays a capital label, a bare «Λ» is Λεωφόρος, «Πλ.» is Plateia,
    # a bare number before ΧΙΛ is an ordinal — and a foreign name stays by
    # its letters (rule J, declined by the user)
    assert pl["Λεωφόρος Συγγρού 189"] == "Leoforos Syngrou 189"
    assert pl["Μεσολόγγι"] == "Mesolongi"
    assert pl["Μπουμπουλίνας 57-59"] == "Bouboulinas 57-59"
    assert pl["Λεωφόρος Κηφισίας 118Β"] == "Leoforos Kifisias 118B"
    assert pl["Λ ΣΤΑΜΑΤΑΣ 5"] == "Leoforos Stamatas 5"
    assert pl["Π.ΒΙΝΙΕΡΑΤΟΥ 5, ΠΛ.ΚΑΜΠΑΝΑΣ"] == "P. Vinieratou 5, Plateia Kampanas"
    assert pl["3 ΧΙΛ ΔΡΑΜΑΣ ΣΕΡΡΩΝ"] == "3rd km Dramas – Serron"
    assert pl["Βίκτωρος Ουγκώ 10"] == "Viktoros Ougko 10"
    assert pl["Περιοχή ΖΕΠ"] == "ZEP area" and pl["αγροτεμάχια 567 & 584"] == "plots 567 & 584"
    # a hyphen inside a token starts a new place name
    assert pl["3ο χλμ. Ε.Ο. Κομοτηνής-Αλεξανδρούπολης"] == \
        "3rd km National Road Komotinis-Alexandroupolis"
    # «Αγ.» takes the case of the word it qualifies
    assert pl["Αγ. Κωνσταντίνου 1"] == "Agiou Konstantinou 1"


def test_place_review_verdicts_pinned():
    """The user's own review of the register (2026-08-26), and the bugs the
    OSM cross-check surfaced with it."""
    pl = _places()
    # ΕΛΟΤ 743 voicing — «ευ» before a voiceless consonant is «ef»
    assert pl["Ελευθερίου Βενιζέλου 5"] == "Eleftheriou Venizelou 5"
    assert pl["Ευκαρπία"] == "Efkarpia"
    assert pl["ΠΕΥΚΟΦΥΤΟ"] == "Pefkofyto"
    assert pl["Λευκάδα"] == "Lefkada"
    assert pl["Ναύπλιο"] == "Nafplio"
    # «ΘΕΣΗ» is punctuation, not a word
    assert pl["ΘΗΒΑ ΘΕΣΗ ΧΟΡΟΒΟΙΒΟΔΑ"] == "Thiva, Chorovoivoda"
    assert pl["θέση Βαρύπετρο"] == "Varypetro"
    # «ΝΕΟ» is the road only after a «χλμ»; elsewhere it is the adjective
    assert pl["1ο χλμ. ΝΕΟ Λαμίας Αθηνών"] == "1st km New National Road Lamias Athinon"
    assert pl["Νέο Ψυχικό"] == "Neo Psychiko"
    assert pl["Νέο Ηράκλειο"] == "Neo Irakleio"
    # «Μεγ.» takes the gender of what it qualifies
    assert pl["Μεγ. Αλεξάνδρου 24"] == "Megalou Alexandrou 24"
    assert pl["ΜΕΓ ΠΑΝΑΓΙΑ"] == "Megali Panagia"
    # a settlement of a Π.Ε.'s name reads the way the Π.Ε. layer rules
    pe = json.loads((ROOT / "khmdhs" / "data" / "pe_names_en.json")
                    .read_text(encoding="utf-8"))
    pe_en = {k: (v["en"] if isinstance(v, dict) else v) for k, v in pe.items()
             if not k.startswith("_")}
    assert pl["Ρόδος"] == "Rhodes" and "Rhodes" in pe_en.values()
    assert pl["Κόρινθος"] == "Corinth"
    assert pl["Πειραιάς"] == "Piraeus"
    assert pl["Κέρκυρα"] == "Corfu"
    assert pl["ΗΡΑΚΛΕΙΟ"] == "Heraklion"
    # the Chios street named after the 118 exiles — transliterated whole,
    # by the user's verdict of 2026-09-01 (a half-translation read worse)
    assert pl["Οδός των 118, αρ. 37"] == "Odos ton 118, no. 37"
