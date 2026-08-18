"""Forest-authority layer: registry validation, whitelist matcher, loader."""
import json
import sqlite3
from pathlib import Path

import pytest

from khmdhs.forest_loader import (
    GAZETTEER_FILE, REGISTRY_FILE, Matcher, fold, load_registry,
    resolve_contracts, write_db,
)
from khmdhs.greek_regions import REGIONAL_UNITS
from tests.conftest import add_contract, set_scope

REAL_DB = Path(__file__).resolve().parent.parent / "data" / "processed" / "khmdhs.sqlite"


@pytest.fixture(scope="module")
def registry():
    reg, _gaz = load_registry()
    return reg


@pytest.fixture(scope="module")
def matcher(registry):
    return Matcher(registry)


# ---------------------------------------------------------------- registry --

def test_registry_validates(registry):
    """load_registry raises SystemExit on any inconsistency — reaching here
    means aliases are unambiguous and every entry resolves."""
    assert len(registry["authorities"]) >= 100


def test_registry_every_authority_has_coords(registry):
    gaz = json.loads(GAZETTEER_FILE.read_text(encoding="utf-8"))
    for name, a in registry["authorities"].items():
        muni = gaz[a["municipality_code"]]
        assert -90 < muni["lat"] < 90 and -180 < muni["lon"] < 180, name
        assert a["region_pe"] in REGIONAL_UNITS, name


def test_gazetteer_shape():
    gaz = json.loads(GAZETTEER_FILE.read_text(encoding="utf-8"))
    assert len(gaz) == 325            # Kallikratis municipalities, Άθως dropped
    assert all(code.isdigit() for code in gaz)


# ----------------------------------------------------------------- matcher --

def test_matcher_single_authority(matcher):
    found = matcher.find("Εργασίες αρμοδιότητας Δασαρχείου Πύργου.")
    assert [n for n, _ in found] == ["Δασαρχείο Πύργου"]


def test_matcher_skips_the_nomos_token(matcher):
    """«Ν.» is Νομού, and it sits between the trigger and the toponym in
    22SYMV010473683: «αρμοδιότητας Δασαρχείων Ιωαννίνων και Δ/νσεων Δασών Ν.
    Κεφαλληνίας και Καστοριάς». Until it was skipped the matcher stopped
    there and read neither Διεύθυνση, which made the document audit report
    two correctly-stored links as undeclared (DATA_DECISIONS 2026-08-18)."""
    found = matcher.find("αρμοδιότητας Δασαρχείων Ιωαννίνων και Δ/νσεων Δασών "
                         "Ν. Κεφαλληνίας και Καστοριάς")
    assert [n for n, _ in found] == ["Δασαρχείο Ιωαννίνων",
                                     "Διεύθυνση Δασών Κεφαλληνίας",
                                     "Διεύθυνση Δασών Καστοριάς"]
    assert [n for n, _ in matcher.find("Δασαρχείο Νομού Ιωαννίνων")] ==         ["Δασαρχείο Ιωαννίνων"]


def test_matcher_genitive_list(matcher):
    found = matcher.find(
        "ΕΚΤΑΣΕΙΣ ΕΥΘΥΝΗΣ ΤΩΝ ΔΑΣΑΡΧΕΙΩΝ ΛΑΓΚΑΔΑ, ΝΙΓΡΙΤΑΣ, ΚΙΛΚΙΣ ΚΑΙ ΓΟΥΜΕΝΙΣΣΑΣ.")
    assert [n for n, _ in found] == ["Δασαρχείο Λαγκαδά", "Δασαρχείο Νιγρίτας",
                                     "Δασαρχείο Κιλκίς", "Δασαρχείο Γουμένισσας"]


def test_matcher_mixed_kinds(matcher):
    found = matcher.find(
        "αρμοδιότητας των Δασαρχείων Μουζακίου και Σπερχειάδας και των "
        "Διευθύνσεων Δασών Άρτας και Πρέβεζας")
    assert {n for n, _ in found} == {
        "Δασαρχείο Μουζακίου", "Δασαρχείο Σπερχειάδας",
        "Διεύθυνση Δασών Άρτας", "Διεύθυνση Δασών Πρέβεζας"}


def test_matcher_dx_abbreviation_and_typo(matcher):
    found = matcher.find("1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ ΔΧ ΑΞΑΝΔΡΟΥΠΟΛΗΣ ΔΙΔΥΜΟΤΕΙΧΟΥ")
    assert [n for n, _ in found] == ["Δασαρχείο Αλεξανδρούπολης",
                                     "Δασαρχείο Διδυμοτείχου"]


def test_matcher_kind_disambiguates(matcher):
    """ΛΑΡΙΣΑΣ is an alias of both the ΔΔ and the ΔΧ — the trigger decides."""
    dd = matcher.find("της Διεύθυνσης Δασών Λάρισας")
    dx = matcher.find("του Δασαρχείου Λάρισας")
    assert [n for n, _ in dd] == ["Διεύθυνση Δασών Λάρισας"]
    assert [n for n, _ in dx] == ["Δασαρχείο Λάρισας"]


def test_matcher_homoglyph_latin_text(matcher):
    # Latin lookalikes as they appear in registry titles (A, E, O …).
    text = fold("ΔΑΣΑΡΧΕΙΟΥ ΠΕΝΤΕΛΗΣ")  # folding is applied inside find too
    assert [n for n, _ in matcher.find(text)] == ["Δασαρχείο Πεντέλης"]


def test_matcher_no_false_positives(matcher):
    for text in ("ΤΟ ΔΑΣΑΡΧΕΙΟ ΕΙΤΕ Η ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ (ΚΑΤΑ ΠΕΡΙΠΤΩΣΗ)",
                 "ΔΧ ΤΜΗΜΑ 3 ΕΓΚΡΙΣΗ ΑΠΕ",
                 "έργα της Περιφέρειας Αττικής"):
        assert matcher.find(text) == []


# ------------------------------------------------------------------ loader --

def _run_loader(conn, registry):
    from khmdhs.forest_loader import Matcher as M
    result, resolved_empty = resolve_contracts(conn, registry, M(registry))
    gaz = json.loads(GAZETTEER_FILE.read_text(encoding="utf-8"))
    write_db(conn, registry, gaz, result)
    return result, resolved_empty


def test_loader_roundtrip_and_inheritance(mem_conn, registry):
    add_contract(mem_conn, "24SYMV1", title="Έργα αρμοδιότητας Δασαρχείου Πύργου")
    add_contract(mem_conn, "25SYMV2", title="1η ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΜΒΑΣΗΣ",
                 prev="24SYMV1")
    set_scope(mem_conn, "24SYMV1", "antinero_iii", 1)
    set_scope(mem_conn, "25SYMV2", "antinero_iii", 1)
    _run_loader(mem_conn, registry)
    rows = mem_conn.execute(
        "SELECT reference_number, authority_name, source "
        "FROM contract_forest_authorities ORDER BY reference_number").fetchall()
    assert [(r[0], r[1]) for r in rows] == [
        ("24SYMV1", "Δασαρχείο Πύργου"), ("25SYMV2", "Δασαρχείο Πύργου")]
    assert rows[1][2] == "inherited:24SYMV1"
    lat = mem_conn.execute(
        "SELECT lat FROM forest_authorities WHERE name='Δασαρχείο Πύργου'"
    ).fetchone()[0]
    assert lat == pytest.approx(37.7, abs=0.5)


def test_loader_override_wins(mem_conn, registry):
    reg = json.loads(json.dumps(registry))  # deep copy
    add_contract(mem_conn, "24SYMVX", title="Έργα Δασαρχείου Πύργου")
    set_scope(mem_conn, "24SYMVX", "antinero_iii", 1)
    reg["contract_overrides"]["24SYMVX"] = {
        "authorities": ["Δασαρχείο Καλαμάτας"], "evidence": "test"}
    result, _ = resolve_contracts(
        mem_conn, reg, Matcher(reg))
    assert [n for n, s, _ in result["24SYMVX"]] == ["Δασαρχείο Καλαμάτας"]
    assert result["24SYMVX"][0][1] == "override"


def test_loader_no_authority_inherited(mem_conn, registry):
    reg = json.loads(json.dumps(registry))
    add_contract(mem_conn, "25SYMVA", title="Έργα Περιφέρειας Αττικής")
    add_contract(mem_conn, "26SYMVB", title="1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ", prev="25SYMVA")
    reg["no_authority"]["25SYMVA"] = "region-scoped (test)"
    result, resolved_empty = resolve_contracts(mem_conn, reg, Matcher(reg))
    assert result["25SYMVA"] == []
    assert "25SYMVA" in resolved_empty and "26SYMVB" in resolved_empty


# ------------------------------------------------------------- real-DB pins --

@pytest.fixture(scope="module")
def real_conn():
    if not REAL_DB.exists():
        pytest.skip("real DB not present")
    conn = sqlite3.connect(f"file:{REAL_DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_real_db_every_in_scope_contract_resolved(real_conn, registry):
    """Every in-scope contract has ≥1 authority row or is documented (or
    chain-inherits documentation) as genuinely authority-less."""
    documented = set(registry.get("no_authority", {}))
    missing = []
    for (ref,) in real_conn.execute(
            "SELECT reference_number FROM contract_scope WHERE in_scope=1"):
        n = real_conn.execute(
            "SELECT COUNT(*) FROM contract_forest_authorities "
            "WHERE reference_number=?", (ref,)).fetchone()[0]
        if n:
            continue
        cur, ok, seen = ref, False, set()
        while cur and cur not in seen:
            if cur in documented:
                ok = True
                break
            seen.add(cur)
            row = real_conn.execute(
                "SELECT prev_reference_no FROM contracts WHERE reference_number=?",
                (cur,)).fetchone()
            cur = row[0] if row else None
        if not ok:
            missing.append(ref)
    assert missing == []


def test_real_db_authority_links_have_coords(real_conn):
    n = real_conn.execute("""
        SELECT COUNT(*) FROM contract_forest_authorities cfa
        LEFT JOIN forest_authorities fa ON fa.name = cfa.authority_name
        WHERE fa.lat IS NULL OR fa.lon IS NULL""").fetchone()[0]
    assert n == 0


def test_real_db_office_layer(real_conn):
    """Office layer (DATA_DECISIONS 2026-08-17): every authority carries a
    seat_precision; ΥΠΕΝ-directory Τ.Κ. present for all but the two
    documented gaps (Περτουλίου = ΑΠΘ-run, Κοζάνης = garbled sources);
    the Γουμένισσα ministry-page typo stays corrected to the letterhead's
    61300 (ΑΔΑ 9ΒΟΨ4653Π8-299)."""
    rows = real_conn.execute(
        "SELECT name, postal_code, email, seat_precision "
        "FROM forest_authorities").fetchall()
    assert len(rows) == 103
    assert all(r["seat_precision"] in
               ("street", "postcode", "city", "municipality") for r in rows)
    no_tk = sorted(r["name"] for r in rows if not r["postal_code"])
    assert no_tk == ["Δασαρχείο Κοζάνης", "Δασαρχείο Περτουλίου"]
    gou = real_conn.execute(
        "SELECT postal_code FROM forest_authorities "
        "WHERE name = 'Δασαρχείο Γουμένισσας'").fetchone()
    assert gou["postal_code"] == "61300"
    # geocoded office points must dominate — the whole point of the layer
    n_office = sum(1 for r in rows if r["seat_precision"] != "municipality")
    assert n_office >= 80
