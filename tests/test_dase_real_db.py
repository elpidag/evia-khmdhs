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
    assert k["total_eur"] == pytest.approx(38_587_233.00, abs=0.01)
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


def test_no_uncorrected_decimal_shift_vs_sibling_modal(conn):
    """A live uncorrected contract whose stated net sits at ≈×10/×100 of
    its family's modal lot price is a registry keying error. Family =
    contracts sharing a non-payment linked act; ≥3 siblings at an
    IDENTICAL net price = standard per-unit lot pricing, so the modal is
    trustworthy. The tolerance admits digit-glitch shifts (the flagship
    21SYMV009374147 sat at ratio 10.0000079) while legitimate ratios stay
    clear. Corrected rows are exempt via contracts.correction_note
    (dase_contract_corrections.json, DATA_DECISIONS 2026-08-14). This
    guard is deliberately NOT the khmdhs payments-vs-stated one: 58 ΔΑΣΕ
    per-unit υλοτομικά are legitimately paid 1.5–16× their stated
    estimate and would trip it."""
    rows = conn.execute("""
        WITH sib AS (
            SELECT a.reference_number AS ref,
                   c.total_cost_without_vat AS sib_net,
                   c.reference_number AS sib_ref
            FROM contract_linked_acts a
            JOIN contract_linked_acts b ON b.adam = a.adam AND b.kind = a.kind
                 AND b.reference_number != a.reference_number
            JOIN contracts c ON c.reference_number = b.reference_number
            WHERE a.kind IN ('notice','request','approved_request','auction')
              AND c.cancelled = 0
        ),
        modal AS (
            SELECT ref, sib_net, COUNT(DISTINCT sib_ref) AS n
            FROM sib WHERE sib_net > 0 GROUP BY ref, sib_net HAVING n >= 3
        )
        SELECT DISTINCT k.reference_number
        FROM contracts k JOIN modal m ON m.ref = k.reference_number
        WHERE k.cancelled = 0
          AND NOT EXISTS (SELECT 1 FROM contracts nx
                          WHERE nx.reference_number = k.next_reference_no)
          AND k.correction_note IS NULL
          AND (ABS(k.total_cost_without_vat / m.sib_net - 10.0)  < 0.05
            OR ABS(k.total_cost_without_vat / m.sib_net - 100.0) < 0.5)
    """).fetchall()
    assert [r["reference_number"] for r in rows] == []


def test_corrected_value_regression_pin(conn):
    """21SYMV009374147 stays at its PDF-documented value (DATA_DECISIONS
    2026-08-14) — a re-load that forgets the corrections hook regresses
    here first."""
    row = conn.execute(
        "SELECT total_cost_without_vat, total_cost_with_vat, correction_note"
        " FROM contracts WHERE reference_number = '21SYMV009374147'").fetchone()
    assert row["total_cost_without_vat"] == pytest.approx(253_739.13)
    assert row["total_cost_with_vat"] == pytest.approx(314_636.52)
    assert row["correction_note"]
    obj = conn.execute(
        "SELECT cost_without_vat FROM contract_objects"
        " WHERE reference_number = '21SYMV009374147' AND seq = 0").fetchone()
    assert obj["cost_without_vat"] == pytest.approx(253_739.13)


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
