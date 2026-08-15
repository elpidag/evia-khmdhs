# -*- coding: utf-8 -*-
"""Unit tests for khmdhs.dase_names_loader (synthetic DB + tmp JSON)."""
import json
import sqlite3

import pytest

from khmdhs.dase_names_loader import load_names


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE contracts (
            reference_number TEXT PRIMARY KEY,
            cancelled INTEGER DEFAULT 0,
            next_reference_no TEXT
        );
        CREATE TABLE contractors (
            reference_number TEXT, seq INTEGER,
            vat_number TEXT, name TEXT
        );
        CREATE TABLE dase_contractors (
            vat_number TEXT PRIMARY KEY, name TEXT, form TEXT
        );
        INSERT INTO contracts VALUES ('21SYMV000000001', 0, NULL);
        INSERT INTO contractors VALUES ('21SYMV000000001', 0, '096000001', 'ΔΑΣΕ ΤΕΣΤ');
        INSERT INTO dase_contractors VALUES ('096000001', 'ΔΑΣΕ ΤΕΣΤ', 'dase');
    """)
    return c


def _write(tmp_path, payload):
    p = tmp_path / "names.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def test_loads_and_is_idempotent(conn, tmp_path):
    p = _write(tmp_path, {
        "_comment": "x",
        "096000001": {"el": "ΔΑ.Σ.Ε. ΤΕΣΤ", "en": "F.W.CO-OP TEST"},
    })
    assert load_names(conn, p) == 1
    assert load_names(conn, p) == 1          # full-replace, no duplicates
    row = conn.execute("SELECT * FROM dase_display_names").fetchone()
    assert row["vat"] == "096000001"
    assert row["display_el"] == "ΔΑ.Σ.Ε. ΤΕΣΤ"
    assert row["display_en"] == "F.W.CO-OP TEST"


def test_rejects_cross_script_names(conn, tmp_path):
    # Latin O inside the Greek name — the exact error class the curation
    # normalized away must never reach the DB
    p = _write(tmp_path, {"096000001": {"el": "ΔΑ.Σ.Ε. ΝOΤΙΟΥ", "en": "F.W.CO-OP X"}})
    with pytest.raises(ValueError, match="cross-script"):
        load_names(conn, p)
    p = _write(tmp_path, {"096000001": {"el": "ΔΑ.Σ.Ε. Χ", "en": "F.W.CO-OP KΑΤΟ"}})
    with pytest.raises(ValueError, match="cross-script"):
        load_names(conn, p)


def test_rejects_bad_keys_and_empty_names(conn, tmp_path):
    with pytest.raises(ValueError, match="non-canonical"):
        load_names(conn, _write(tmp_path, {"0310003799": {"el": "Χ", "en": "X"}}))
    with pytest.raises(ValueError, match="empty"):
        load_names(conn, _write(tmp_path, {"096000001": {"el": "", "en": "X"}}))


def test_warns_on_population_drift(conn, tmp_path, caplog):
    p = _write(tmp_path, {"096999999": {"el": "ΔΑ.Σ.Ε. ΑΛΛΟ", "en": "F.W.CO-OP OTHER"}})
    with caplog.at_level("WARNING"):
        load_names(conn, p)
    text = caplog.text
    assert "096000001 has no curated display name" in text
    assert "096999999 matches no live co-op" in text
