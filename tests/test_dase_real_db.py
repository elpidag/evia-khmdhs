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


def test_coop_totals_sum_to_the_live_basis(conn):
    """The ΔΑΣΕ page of the OLD site reconciles too: since 2026-08-20 the even
    split of a jointly signed contract lives in dase_queries, so both sites
    apply it once and neither column of totals stands above the basis."""
    headline = dq.kpis(conn)["total_eur"]
    listed = sum(r["total_eur"] or 0.0 for r in dq.list_coops(conn))
    assert listed == pytest.approx(headline, abs=0.01)


def test_population_pins(conn):
    k = dq.kpis(conn)
    assert k["gross_n"] == 2164
    assert k["n_cancelled"] == 102   # 82 registry + 10 double-postings
                                # + 2 not-a-co-op contracts (2026-08-17)
    assert k["n_superseded"] == 64
    assert k["n_contracts"] == 1998
    assert k["total_eur"] == pytest.approx(36_954_829.83, abs=0.01)
    assert k["n_coops"] >= 245
    assert k["pct_direct"] > 90


def test_curated_contractors_pin(conn):
    n, = conn.execute("SELECT COUNT(*) FROM dase_contractors").fetchone()
    assert n == 257


def test_every_contract_has_a_curated_dase_contractor(conn):
    """Every stored contract entered this contractor-led harvest because a
    curated co-op is one of its contractors — EXCEPT the ones whose signed
    PDF turned out to name none (`related_to`, DATA_DECISIONS 2026-08-17).
    For those the registry claim was disproved and the co-op's contractor
    row was deleted, so the page cannot present it as a party; they are
    exempt here and must be excluded from the population instead."""
    directory = dq.coop_directory(conn)
    exempt = {r["reference_number"]: r["cancelled"] for r in conn.execute(
        "SELECT reference_number, cancelled FROM contracts "
        "WHERE related_to IS NOT NULL")}
    assert exempt and all(c == 1 for c in exempt.values())
    orphans = [
        ref for ref, in conn.execute(
            "SELECT DISTINCT reference_number FROM contracts")
        if ref not in exempt and not any(
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


def test_no_live_contract_states_gross_as_its_net(conn):
    """A live contract whose net EQUALS its gross is a registry keying
    error until proven otherwise: the Atlas presents every € net of ΦΠΑ,
    so such a row silently feeds a VAT-inclusive amount into the net
    basis. Six Δ/νση Δασών Δωδεκανήσου contracts did exactly that
    (DATA_DECISIONS 2026-08-17) and are corrected; 2.000 of 2.006 live
    contracts carry a real split, so the equality is the anomaly, not
    the norm. A genuinely ΦΠΑ-exempt contract would trip this too — by
    design: the verdict belongs to a human reading the PDF and its
    payment orders, not to a ÷1,24 rule."""
    rows = conn.execute("""
        SELECT reference_number, total_cost_with_vat
        FROM contracts
        WHERE cancelled = 0
          AND correction_note IS NULL
          AND total_cost_without_vat IS NOT NULL
          AND total_cost_without_vat = total_cost_with_vat
          AND total_cost_with_vat > 0
          AND NOT EXISTS (SELECT 1 FROM contracts nx
                          WHERE nx.reference_number = contracts.next_reference_no)
    """).fetchall()
    assert [r["reference_number"] for r in rows] == []


def test_dodekanisou_vat_corrections_pin(conn):
    """The six Rhodes restoration lots keep their payment-documented net
    (DATA_DECISIONS 2026-08-17). Each true net is its own stated gross
    ÷1,24 — the ratio its payment order states."""
    expected = {
        "24SYMV015692415": 395_161.29,
        "24SYMV015692407": 344_722.60,
        "24SYMV015744883": 338_709.68,
        "24SYMV015692405": 319_379.45,
        "24SYMV015713189": 302_419.35,
        "24SYMV015707036": 302_378.08,
    }
    for ref, net in expected.items():
        row = conn.execute(
            "SELECT total_cost_without_vat n, total_cost_with_vat g, correction_note"
            " FROM contracts WHERE reference_number = ?", (ref,)).fetchone()
        assert row is not None, ref
        assert row["n"] == pytest.approx(net), ref
        assert row["n"] == pytest.approx(row["g"] / 1.24, abs=0.01), ref
        assert row["correction_note"], ref
        obj = conn.execute(
            "SELECT cost_without_vat FROM contract_objects"
            " WHERE reference_number = ? AND seq = 0", (ref,)).fetchone()
        assert obj["cost_without_vat"] == pytest.approx(net), ref


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


def test_no_unexcluded_double_postings(conn):
    """No two live contracts may carry identical PDF text (after stripping
    the registry's ΑΔΑΜ stamps) for the same date and amount — the
    signature of the same signed document uploaded twice (10 such twins
    are excluded via dase_contract_corrections.json, DATA_DECISIONS
    2026-08-14 + 2026-08-15; the scanner also runs a cross-VAT pass so a
    mis-keyed contractor ΑΦΜ can't hide a twin). Skips when the txt cache
    is absent."""
    cache = DB.parent / "dase_pdf_cache"
    if not cache.exists():
        pytest.skip("dase_pdf_cache not present")
    import sys
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "scripts"))
    from find_duplicate_postings import find_pairs
    pairs = [p for p in find_pairs(conn, cache) if p["identical"]]
    assert pairs == []


def test_duplicate_postings_are_linked_not_deleted(conn):
    """Every curated double-posting exclusion stays reachable and points at
    its kept twin; the twin is live."""
    rows = conn.execute(
        "SELECT reference_number, duplicate_of, cancelled, correction_note "
        "FROM contracts WHERE duplicate_of IS NOT NULL").fetchall()
    assert len(rows) == 10
    for r in rows:
        assert r["cancelled"] == 1
        assert r["correction_note"]
        kept = conn.execute(
            "SELECT cancelled FROM contracts WHERE reference_number = ?",
            (r["duplicate_of"],)).fetchone()
        assert kept is not None and kept["cancelled"] == 0


def test_display_names_pins(conn):
    """Curated bilingual display names (DATA_DECISIONS 2026-08-15): one per
    live co-op, bijective with the live population, script-clean, and equal
    to the committed JSON (a re-load that skips dase_names_loader drifts
    here first)."""
    import json
    import unicodedata
    rows = {r["vat"]: (r["display_el"], r["display_en"]) for r in conn.execute(
        "SELECT vat, display_el, display_en FROM dase_display_names")}
    assert len(rows) == 246
    src = json.loads(
        (Path(__file__).resolve().parent.parent / "khmdhs" / "data" /
         "dase_display_names.json").read_text(encoding="utf-8"))
    src = {k: (v["el"], v["en"]) for k, v in src.items() if not k.startswith("_")}
    assert rows == src
    for el, en in rows.values():
        assert not any("LATIN" in unicodedata.name(c, "") for c in el), el
        assert not any("GREEK" in unicodedata.name(c, "") for c in en), en
    curated = {dq.canonical_vat(r[0]) for r in conn.execute(
        "SELECT vat_number FROM dase_contractors")}
    live = set()
    for r in conn.execute("""
        SELECT DISTINCT c.vat_number FROM contractors c
        JOIN contracts co ON co.reference_number = c.reference_number
        WHERE co.cancelled = 0 AND NOT EXISTS
              (SELECT 1 FROM contracts nx
               WHERE nx.reference_number = co.next_reference_no)"""):
        cv = dq.canonical_vat(r[0])
        if cv in curated:
            live.add(cv)
    assert set(rows) == live


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


def test_cpv_tree_pins(conn):
    """The /dase CPV CODES frame (2026-08-24): the live population's declared
    codes rolled up the CPV 2008 tree — every node carries an official name
    (cpv_nodes.json covers BOTH datasets since the same day), every live
    contract declares at least one code, and the documented ΕΦΚΑ count
    (DATA_DECISIONS 2026-08-17: 386 insurance-code rows) is the insurance
    division's contract count."""
    from atlas_api import queries_extra as qe

    tree = qe.dase_cpv_tree(conn)
    assert tree["n_contracts"] == 1998        # every live contract has a code
    assert tree["divisions"], "empty tree"
    for d in tree["divisions"]:
        assert d["name_en"], f"unnamed division {d['code']}"
        for k in d["classes"]:
            assert k["name_en"], f"unnamed class {k['code']} in {d['code']}"
    top = tree["divisions"][0]
    assert top["code"].startswith("77")       # forestry leads
    div66 = next(d for d in tree["divisions"] if d["code"].startswith("66"))
    assert div66["n"] == 386                  # the ΕΦΚΑ tag, pinned 2026-08-17
