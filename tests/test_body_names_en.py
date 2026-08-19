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
