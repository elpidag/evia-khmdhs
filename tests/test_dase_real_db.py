"""Pins on the committed data/processed/dase.sqlite — fail loudly when a
re-harvest changes the dedup arithmetic or region coverage regresses."""
from pathlib import Path

import pytest

from khmdhs.greek_regions import REGIONAL_UNITS, canonical_pe
from webui import dase_queries as dq
from webui import queries

DB = Path(__file__).resolve().parent.parent / "data" / "processed" / "dase.sqlite"


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip("committed dase.sqlite not present")
    c = queries.open_ro(DB)
    yield c
    c.close()


def test_population_pins(conn):
    k = dq.kpis(conn)
    assert k["gross_n"] == 2164
    assert k["n_cancelled"] == 82
    assert k["n_superseded"] == 64
    assert k["n_contracts"] == 2018
    assert k["total_eur"] == pytest.approx(41_418_963.96, abs=0.01)
    assert k["n_coops"] >= 245
    assert k["pct_direct"] > 90


def test_curated_contractors_pin(conn):
    n, = conn.execute("SELECT COUNT(*) FROM dase_contractors").fetchone()
    assert n == 260


def test_every_contract_has_a_curated_dase_contractor(conn):
    directory = dq.coop_directory(conn)
    orphans = [
        ref for ref, in conn.execute(
            "SELECT DISTINCT reference_number FROM contracts")
        if not any(
            dq.canonical_vat(v) in directory
            for v, in conn.execute(
                "SELECT vat_number FROM contractors WHERE reference_number=?",
                (ref,)))
    ]
    assert orphans == []


def test_region_coverage(conn):
    total, = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()
    covered, = conn.execute(
        "SELECT COUNT(*) FROM dase_contract_regions").fetchone()
    # 2,160/2,164 resolved (only ΑΔΜΗΕ multi-Π.Ε. line works stay out).
    assert covered >= 2150
    assert total - covered <= 10


def test_regions_are_canonical_vocabulary(conn):
    pes = [pe for pe, in conn.execute(
        "SELECT DISTINCT region_pe FROM dase_contract_regions")]
    assert pes
    for pe in pes:
        assert canonical_pe(pe) in REGIONAL_UNITS, pe


def test_reference_contract_present_and_live(conn):
    row = conn.execute(
        "SELECT cancelled, next_reference_no FROM contracts"
        " WHERE reference_number = '26SYMV019413118'").fetchone()
    assert row is not None
    assert row["cancelled"] == 0


def test_next_reference_column_matches_raw_json(conn):
    """The dedup rule trusts next_reference_no — verify against raw_json
    (the khmdhs nextRefNo truncation bug never ran chain repair here)."""
    import json
    bad = 0
    for r in conn.execute(
            "SELECT next_reference_no, raw_json FROM contracts"):
        nxt = json.loads(r["raw_json"]).get("nextRefNo")
        vals = nxt if isinstance(nxt, list) else ([nxt] if nxt else [])
        vals = [v for v in vals if v]
        col = r["next_reference_no"]
        if (vals and col != vals[0]) or (not vals and col):
            bad += 1
        if len(vals) > 1:
            bad += 1          # multi-successor would break the NOT EXISTS rule
    assert bad == 0
