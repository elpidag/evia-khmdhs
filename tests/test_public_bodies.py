# -*- coding: utf-8 -*-
"""Public-bodies registry (DATA_DECISIONS 2026-08-16): loader validation
units + real-file/real-DB pins — coverage bijection over all three DBs,
closed vocabularies, municipality links, user-decision pins."""
import json
import sqlite3
from pathlib import Path

import pytest

from khmdhs.bodies_loader import BODIES_FILE, KINDS, MUNI_FILE, SCOPES, load_bodies

ROOT = Path(__file__).resolve().parents[1]
KH = ROOT / "data/processed/khmdhs.sqlite"
DA = ROOT / "data/processed/dase.sqlite"
AN = ROOT / "data/processed/anadohoi.sqlite"

BODIES = json.loads(BODIES_FILE.read_text(encoding="utf-8"))["bodies"]


# ---------------------------------------------------------------- units
def _write(tmp_path, bodies):
    p = tmp_path / "bodies.json"
    p.write_text(json.dumps({"bodies": bodies}, ensure_ascii=False), encoding="utf-8")
    return p


def _body(**over):
    b = {"key": "test-body", "name": "ΔΟΚΙΜΗ", "kind": "ministry",
         "scope": "national", "afm": "123456789", "municipality_code": None,
         "aliases": ["ΔΟΚΙΜΗ"], "note": None}
    b.update(over)
    return b


def test_loader_refuses_review(tmp_path):
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="closed vocabulary"):
        load_bodies(conn, _write(tmp_path, [_body(kind="review")]))
    with pytest.raises(ValueError, match="closed vocabulary"):
        load_bodies(conn, _write(tmp_path, [_body(scope="review")]))


def test_loader_refuses_municipal_without_code(tmp_path):
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="without municipality_code"):
        load_bodies(conn, _write(tmp_path, [_body(scope="municipal")]))
    with pytest.raises(ValueError, match="unknown to greek_municipalities"):
        load_bodies(conn, _write(tmp_path, [_body(scope="municipal",
                                                  municipality_code="0000")]))


def test_loader_refuses_bad_afm_and_duplicate_alias(tmp_path):
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="not 9 digits"):
        load_bodies(conn, _write(tmp_path, [_body(afm="0123456789")]))
    with pytest.raises(ValueError, match="claimed by both"):
        load_bodies(conn, _write(tmp_path, [
            _body(), _body(key="other-body", aliases=["ΔΟΚΙΜΗ"])]))


def test_loader_idempotent(tmp_path):
    conn = sqlite3.connect(":memory:")
    load_bodies(conn, _write(tmp_path, [_body()]))
    load_bodies(conn, _write(tmp_path, [_body()]))
    assert conn.execute("SELECT COUNT(*) FROM public_bodies").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM public_body_aliases").fetchone()[0] == 1


# ------------------------------------------------------- real-file pins
def test_registry_shape():
    assert len(BODIES) == 67
    for b in BODIES:
        assert b["kind"] in KINDS, b["key"]
        assert b["scope"] in SCOPES, b["key"]
        if b["afm"] is not None:
            assert len(b["afm"]) == 9 and b["afm"].isdigit(), b["key"]


def test_registry_municipality_links():
    munis = json.loads(MUNI_FILE.read_text(encoding="utf-8"))
    for b in BODIES:
        if b["scope"] == "municipal":
            assert b["municipality_code"] in munis, b["key"]


def test_user_decision_pins():
    by_key = {b["key"]: b for b in BODIES}
    ypen = by_key["ypoyrgeio-perivallontos-kai-energeias"]
    assert ypen["afm"] == "090273987"
    assert ypen["scope"] == "national"
    # the parked five, resolved other_public/national (user, 2026-08-16)
    for key in ("anexartitos-diacheiristis-metaforas-ilektrikis-energeias-adm",
                "organismos-sidirodromon-elladas-ose",
                "organismos-limenos-alexandroypolis-a-e",
                "geniko-nosokomeio-kozanis-mamatseio",
                "tameio-dioikisis-diacheirisis-panepistimiakon-dason"):
        assert by_key[key]["kind"] == "other_public", key
        assert by_key[key]["scope"] == "national", key
    # ΑΦΜ hygiene decisions
    assert by_key["dimos-dirfyon-messapion"]["afm"] == "997591330"
    assert by_key["dimos-domokoy"]["afm"] is None


@pytest.mark.skipif(not (KH.exists() and DA.exists() and AN.exists()),
                    reason="committed DBs absent")
def test_real_db_coverage_bijection():
    """Every awarding-organization string in all three DBs resolves through
    the aliases to exactly one body, and every alias is a real string."""
    alias_to_key: dict[str, str] = {}
    for b in BODIES:
        for a in b["aliases"]:
            assert a not in alias_to_key, a
            alias_to_key[a] = b["key"]

    observed: set[str] = set()
    for db in (KH, DA):
        conn = sqlite3.connect(db)
        observed |= {r[0] for r in conn.execute(
            "SELECT DISTINCT organization_name FROM contracts "
            "WHERE organization_name IS NOT NULL")}
        conn.close()
    conn = sqlite3.connect(AN)
    observed |= {r[0] for r in conn.execute(
        "SELECT DISTINCT org FROM decisions "
        "WHERE org IS NOT NULL AND TRIM(org) != ''")}
    conn.close()

    missing = observed - set(alias_to_key)
    assert not missing, f"awarding bodies not in the registry: {sorted(missing)[:5]}"
    stale = set(alias_to_key) - observed
    assert not stale, f"registry aliases matching no DB string: {sorted(stale)[:5]}"


@pytest.mark.skipif(not (KH.exists() and DA.exists()), reason="committed DBs absent")
def test_real_db_tables_loaded():
    for db in (KH, DA):
        conn = sqlite3.connect(db)
        assert conn.execute("SELECT COUNT(*) FROM public_bodies").fetchone()[0] == 67
        assert conn.execute("SELECT COUNT(*) FROM public_body_aliases").fetchone()[0] == 68
        conn.close()
