"""Work-site curation: loader round-trip + real-DB pin."""
import json
import sqlite3
from pathlib import Path

import pytest

from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db
from khmdhs.region_loader import main as region_loader_main


def test_sites_round_trip(tmp_path):
    db = tmp_path / "t.sqlite"
    conn = init_db(db)
    conn.execute(
        "INSERT INTO contracts (reference_number, fetched_at) VALUES ('24SYMV000000001', 'x')")
    conn.commit()
    conn.close()

    data = tmp_path / "regions.json"
    data.write_text(json.dumps({
        "24SYMV000000001": {
            "regions": [{"pe": "Π.Ε. Ευβοίας"}],
            "sites": [{"name": "Δασαρχείο Χαλκίδας", "pe": "Π.Ε. Ευβοίας",
                       "page": 2, "excerpt": "…αρμοδιότητας του Δασαρχείου Χαλκίδας…"},
                      {"name": "Θέση «Πούρνος»", "page": 4}],
            "curated_at": "2026-07-25",
        }
    }, ensure_ascii=False), encoding="utf-8")

    assert region_loader_main(["--db", str(db), "--data", str(data)]) == 0
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT site_name, region_pe, page FROM contract_sites ORDER BY seq").fetchall()
    assert rows == [("Δασαρχείο Χαλκίδας", "Π.Ε. Ευβοίας", 2), ("Θέση «Πούρνος»", None, 4)]
    # Re-running is idempotent (DELETE+INSERT per ADAM)
    assert region_loader_main(["--db", str(db), "--data", str(data)]) == 0
    n = conn.execute("SELECT COUNT(*) FROM contract_sites").fetchone()[0]
    assert n == 2


def test_unknown_site_pe_refused(tmp_path):
    db = tmp_path / "t.sqlite"
    init_db(db).close()
    data = tmp_path / "regions.json"
    data.write_text(json.dumps({
        "24SYMV000000001": {"regions": [],
                            "sites": [{"name": "X", "pe": "Π.Ε. Ανύπαρκτη"}]}
    }, ensure_ascii=False), encoding="utf-8")
    assert region_loader_main(["--db", str(db), "--data", str(data)]) == 2


@pytest.mark.skipif(not Path(DEFAULT_DB).exists(), reason="real DB not present")
def test_real_db_esa_sites_loaded():
    conn = sqlite3.connect(DEFAULT_DB)
    n = conn.execute(
        "SELECT COUNT(*) FROM contract_sites WHERE reference_number = '24SYMV014843550'"
    ).fetchone()[0]
    assert n == 5  # Δασαρχεία Αιγάλεω, Καπανδριτίου, Λαυρίου, Μεγάρων, Πειραιά
