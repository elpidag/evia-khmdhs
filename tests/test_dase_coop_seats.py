"""The ΔΑΣΕ co-operatives' registered offices (DATA_DECISIONS 2026-08-24).

Units on the party-clause reader (the trap it exists for: a contract names
the AWARDING service's seat before the co-op's), and real-DB pins on the
curated file and the loaded `contractor_locations` table.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from webui import queries

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "khmdhs" / "data" / "dase_coop_locations.json"
DB = ROOT / "data" / "processed" / "dase.sqlite"


# --------------------------------------------------------------- unit tests
def _reader():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_dase_coop_seats", ROOT / "scripts" / "build_dase_coop_seats.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_seat_clause_is_read_for_the_right_party():
    """A ΔΑΣΕ contract states the awarding service's seat FIRST, with the
    State's ΑΦΜ; the co-op's own clause comes later. The reader anchors on
    the co-op's ΑΦΜ and reads backwards, so it must return the co-op's."""
    mod = _reader()
    text = (
        "ΤΟ ΔΑΣΑΡΧΕΙΟ ΧΑΛΚΙΔΑΣ ΠΟΥ ΕΔΡΕΥΕΙ ΣΤΗ ΧΑΛΚΙΔΑ, ΧΑΪΝΑ 97, ΜΕ ΑΦΜ 090273987 "
        "ΚΑΙ ΑΦΕΤΕΡΟΥ Ο «ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΣΙΔΗΡΟΧΩΡΙΟΥ», ΜΕ ΕΔΡΑ ΤΟ "
        "ΣΙΔΗΡΟΧΩΡΙ ΕΒΡΟΥ, ΣΟΥΦΛΙ, ΤΚ:68400, ΑΦΜ 096067226 ΚΑΙ ΔΟΥ ΑΛΕΞ/ΠΟΛΗΣ"
    )
    got = mod.seat_sentence(text, "096067226")
    assert got is not None
    assert "ΣΙΔΗΡΟΧΩΡΙ" in got
    assert "ΧΑΛΚΙΔΑ" not in got          # never the awarder's seat


def test_awarder_seat_alone_is_refused():
    """When only a public service's «εδρεύει» stands before the co-op's ΑΦΜ,
    nothing is returned — better no seat than the wrong one."""
    mod = _reader()
    text = ("Η ΠΕΡΙΦΕΡΕΙΑ ΘΕΣΣΑΛΙΑΣ ΜΕ ΕΔΡΑ ΤΗΝ ΛΑΡΙΣΑ ΑΝΑΘΕΤΕΙ ΣΤΟΝ ΑΝΑΔΟΧΟ "
            "ΜΕ ΑΦΜ 094311510 ΤΗΝ ΕΚΤΕΛΕΣΗ")
    assert mod.seat_sentence(text, "094311510") is None


# ------------------------------------------------------------- curated file
@pytest.fixture(scope="module")
def curated():
    if not FILE.exists():
        pytest.skip("curated dase_coop_locations.json not present")
    return json.loads(FILE.read_text(encoding="utf-8"))["coops"]


def test_every_coop_has_a_seat_source(curated):
    """No co-op is left without a stated provenance: either the register
    answered, or a labelled name inference carries its reasoning."""
    for vat, e in curated.items():
        reg, cur = e.get("register") or {}, e.get("curated") or {}
        has_reg = bool(reg.get("settlement") or reg.get("city"))
        has_cur = bool(cur.get("settlement"))
        assert has_reg or has_cur, f"{vat}: no seat at all"
        if has_cur:
            assert cur.get("source") == "name_inference"
            assert cur.get("note"), f"{vat}: an inference without its reasoning"
            assert not cur.get("postal_code"), f"{vat}: a postcode was invented"


def test_points_and_precision_agree(curated):
    for vat, e in curated.items():
        has_point = e.get("lat") is not None
        assert has_point == (e.get("lon") is not None), f"{vat}: half a pair"
        prec = e.get("geo_precision")
        if has_point:
            assert prec in ("address", "municipality"), f"{vat}: {prec!r} with a point"
        else:
            assert prec in (None, "failed"), f"{vat}: {prec!r} without a point"


# ----------------------------------------------------------------- real DB
@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip("committed dase.sqlite not present")
    c = queries.open_ro(DB)
    yield c
    c.close()


def test_loaded_locations_pin(conn):
    """The table the layer lands in: one row per co-op of the live
    population, the register carrying almost all of them."""
    n, located, inferred = conn.execute(
        """SELECT COUNT(*),
                  SUM(lat IS NOT NULL),
                  SUM(seat_source = 'name_inference')
             FROM contractor_locations""").fetchone()
    assert n == 246                      # the live population's co-ops
    assert inferred == 8                 # VIES answers for the other 238
    assert located >= 240                # nearly all placed on the map


def test_every_point_agrees_with_its_own_registered_postcode(conn):
    """The geocode gate's actual promise: a co-op's point falls in the Π.Ε.
    its OWN registered postcode implies.

    NOT «the Π.Ε. of its contracts» — that premise is false and the data
    says so: 36 co-ops work outside their seat's Π.Ε. (a Τρίκαλα
    co-operative logging in Εύβοια after the 2021 fires, a Θεσσαλονίκη one
    in Ηλεία). Travelling co-ops are a finding of this layer, not an error
    in it (DATA_DECISIONS 2026-08-24)."""
    from khmdhs.greek_regions import PE_CENTROIDS, resolve_pe

    checked, bad = 0, []
    for vat, lat, lon, pc in conn.execute(
            """SELECT vat_number, lat, lon, postal_code FROM contractor_locations
                WHERE lat IS NOT NULL AND postal_code IS NOT NULL"""):
        pe, _method = resolve_pe(None, pc)
        c = PE_CENTROIDS.get(pe) if pe else None
        if not c:
            continue
        checked += 1
        # a Π.Ε. spans at most ~1.5°: further than that from its centroid is
        # another part of the country
        if abs(lat - c[0]) > 1.5 or abs(lon - c[1]) > 1.5:
            bad.append((vat, pc, pe, lat, lon))
    assert checked >= 230, f"only {checked} points carried a postcode"
    assert not bad, f"points outside their own postcode's Π.Ε.: {bad[:5]}"


def test_the_inferred_seats_do_sit_in_their_contracts_region(conn):
    """The 8 seats read from a co-op's own name were accepted BECAUSE the
    settlement lies in the Π.Ε. of its contracts — so for those, and only
    those, that agreement must hold."""
    from khmdhs.greek_regions import PE_CENTROIDS

    for vat, lat, lon, pe in conn.execute(
            """SELECT vat_number, lat, lon, region_pe FROM contractor_locations
                WHERE seat_source = 'name_inference' AND lat IS NOT NULL"""):
        c = PE_CENTROIDS.get(pe)
        assert c, f"{vat}: unknown Π.Ε. {pe!r}"
        assert abs(lat - c[0]) <= 1.5 and abs(lon - c[1]) <= 1.5,             f"{vat}: inferred seat outside {pe}"


def test_seat_evidence_is_the_latest_statement(curated):
    """A seat can be restated: the excerpt stored must come from the co-op's
    LATEST contract that states one, and any earlier differing wording must
    be kept, never dropped (user, 2026-08-24)."""
    for vat, e in curated.items():
        seat, older = e.get("contract_seat"), e.get("earlier_seat")
        if older:
            assert seat, f"{vat}: an earlier seat without a current one"
            assert (seat.get("date") or "") > (older.get("date") or ""), \
                f"{vat}: the stored seat is not the later statement"
            assert e.get("seat_note"), f"{vat}: a restatement without an explanation"


def test_the_avgerinos_neapoli_restatement_pin(curated):
    """The one case the register and an older contract appeared to
    contradict: 997309155 signed as «ΤΟΠ. ΚΟΙΝ. ΑΥΓΕΡΙΝΟΥ» in 2024 and
    «ΔΗΜ. ΕΝΟΤΗΤΑ ΝΕΑΠΟΛΗΣ» in 2025, which is what VIES registers today.
    The current seat is used, the earlier wording preserved, and no flag
    of disagreement remains (user decision, DATA_DECISIONS 2026-08-24)."""
    e = curated["997309155"]
    assert "flag" not in e                       # not a contradiction
    assert e["contract_seat"]["ref"] == "25SYMV017565851"
    assert "ΝΕΑΠΟΛΗΣ" in e["contract_seat"]["excerpt"]
    assert "ΑΥΓΕΡΙΝΟΥ" in e["earlier_seat"]["excerpt"]
    assert e["register"]["city"] == "ΝΕΑΠΟΛΗ"
