# -*- coding: utf-8 -*-
"""The contractor SEAT layer (DATA_DECISIONS 2026-08-21): every in-scope
Anti-nero contractor's registered office is read from its own signed contract
(`khmdhs/data/contractor_seats.json`, verbatim sentence kept), and the
curated locations file + the DB carry that seat with its provenance.

Real-DB pins over the committed files; skipped when the DB is absent."""
import json
import re
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "khmdhs.sqlite"
SEATS = ROOT / "khmdhs" / "data" / "contractor_seats.json"
LOCS = ROOT / "khmdhs" / "data" / "contractor_locations.json"

pytestmark = pytest.mark.skipif(not DB.exists() or not SEATS.exists(), reason="committed DB / seats file absent")


@pytest.fixture(scope="module")
def kh():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def seats():
    d = json.loads(SEATS.read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


@pytest.fixture(scope="module")
def locs():
    return json.loads(LOCS.read_text(encoding="utf-8"))


def in_scope_vats(kh) -> set[str]:
    return {r[0] for r in kh.execute(
        "SELECT DISTINCT co.vat_number FROM contractors co "
        "JOIN contract_scope s USING(reference_number) WHERE s.in_scope = 1")}


def test_every_in_scope_contractor_has_a_seat(kh, seats):
    missing = in_scope_vats(kh) - set(seats)
    assert not missing, f"in-scope contractors without a curated seat: {sorted(missing)}"


def test_seat_fields_are_well_formed(seats):
    for vat, s in seats.items():
        assert s["seat_source"] in ("contract", "register", "website"), vat
        assert s["city"], vat
        pc = s.get("postal_code")
        assert pc is None or re.fullmatch(r"\d{5}", pc), (vat, pc)
        assert s.get("excerpt"), vat
        # the verbatim sentence is anchored on the contractor's own ΑΦΜ
        assert vat in s["excerpt"], (vat, s["excerpt"][:80])
        if s["seat_source"] == "contract":
            assert re.fullmatch(r"\d{2}SYMV\d{9}", s["source_ref"]), (vat, s["source_ref"])
        else:
            assert s["source_ref"].startswith("http"), (vat, s["source_ref"])
            assert s.get("contract_seat") and s.get("note"), vat


def test_contract_ref_is_a_stored_contract_of_that_contractor(kh, seats):
    """A contract-sourced seat cites a ΣΥΜΒ record on which that ΑΦΜ is a party
    (any record of the chain)."""
    for vat, s in seats.items():
        ref = s["source_ref"] if s["seat_source"] == "contract" else s["contract_seat"]["source_ref"]
        refs = {r[0] for r in kh.execute(
            "SELECT reference_number FROM contractors WHERE vat_number = ?", (vat,))}
        # walk the chains backwards so an earlier version counts too
        frontier, seen = set(refs), set(refs)
        while frontier:
            nxt = set()
            for r in frontier:
                row = kh.execute("SELECT prev_reference_no FROM contracts WHERE reference_number = ?", (r,)).fetchone()
                if row and row[0] and row[0] not in seen:
                    nxt.add(row[0]); seen.add(row[0])
            frontier = nxt
        assert ref in seen, (vat, ref)


def test_locations_carry_the_seat(kh, seats, locs):
    for vat, s in seats.items():
        e = locs[vat]
        assert e.get("seat_source") == s["seat_source"], vat
        assert e.get("seat_ref") == s["source_ref"], vat
        assert (e.get("city") or None) == s["city"], vat
        want = f"{s['street']} {s['number']}".strip() if s.get("street") else None
        assert (e.get("address") or None) == (want or None), (vat, e.get("address"), want)
        assert e.get("lat") is not None and e.get("lon") is not None, vat
        assert e.get("geo_precision") in ("address", "municipality"), vat
        if e["geo_precision"] == "address":
            assert e.get("geo_level") in ("number", "street"), vat
    rows = {r["vat_number"]: r for r in kh.execute(
        "SELECT vat_number, seat_source, seat_ref, geo_level, geo_precision FROM contractor_locations")}
    for vat, s in seats.items():
        assert rows[vat]["seat_source"] == s["seat_source"], vat
        assert rows[vat]["seat_ref"] == s["source_ref"], vat


def test_region_follows_the_contract_seat(locs):
    """Two ventures had been placed at a member's town; their own contracts seat
    them elsewhere (DATA_DECISIONS 2026-08-21)."""
    assert locs["996550190"]["region_pe"] == "Π.Ε. Καβάλας"
    assert locs["996666474"]["region_pe"] == "Π.Ε. Ευβοίας"


def test_divergent_seats_keep_the_contract_seat_beside(seats):
    """Where the current register / the firm's own site decided, the contract's
    seat and the reason stay on record (user decision 2026-08-21)."""
    div = {v for v, s in seats.items() if s["seat_source"] != "contract"}
    # ΤΟΜΗ (094496848) left this set the same day: its own 2025 contract states the current seat
    assert {"999814120", "800948976", "801045078", "033419558", "998807500"} <= div
    for v in div:
        cs = seats[v]["contract_seat"]
        assert cs.get("excerpt") and v in cs["excerpt"], v
