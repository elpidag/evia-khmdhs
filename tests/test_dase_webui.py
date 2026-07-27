"""Route-level tests for the /dase section + /compare, incl. the isolation
guarantee: khmdhs-only routes never open the ΔΑΣΕ database."""
import sqlite3

import pytest

from khmdhs.db import SCHEMA_SQL
from khmdhs.scope_loader import SCHEMA as SCOPE_SCHEMA
from tests.conftest import add_contract, set_scope
from tests.test_dase_queries import add as add_dase, curate
from webui import app as app_module


def _build_kh_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCOPE_SCHEMA)
    add_contract(conn, "22SYMV000000001", title="ANTINERO II ΕΡΓΟ",
                 eur=1_000_000.0)
    set_scope(conn, "22SYMV000000001", "antinero_ii", 1)
    conn.commit()
    conn.close()


def _build_dase_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript("""
        CREATE TABLE dase_contractors (
            vat_number TEXT PRIMARY KEY, name TEXT NOT NULL, form TEXT,
            basis TEXT, curated_at TEXT NOT NULL);
        CREATE TABLE dase_contract_regions (
            reference_number TEXT PRIMARY KEY, region_pe TEXT NOT NULL,
            source TEXT NOT NULL, basis TEXT, curated_at TEXT NOT NULL);
    """)
    curate(conn, "096000001", name="ΔΑΣΕ ΤΕΣΤ")
    add_dase(conn, "23SYMV000000001", eur=5_000.0, title="ΥΛΟΤΟΜΙΑ ΤΕΣΤ")
    conn.execute("INSERT INTO dase_contract_regions VALUES"
                 " ('23SYMV000000001', 'Π.Ε. Δράμας', 'registry:x', 'u',"
                 " '2026-07-27')")
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path):
    kh = tmp_path / "kh.sqlite"
    da = tmp_path / "dase.sqlite"
    _build_kh_db(kh)
    _build_dase_db(da)
    app = app_module.create_app(db_path=kh, pdf_cache_dir=tmp_path / "cache",
                                dase_db_path=da)
    app.testing = True
    return app.test_client()


def test_dase_routes_200(client):
    assert client.get("/dase").status_code == 200
    assert client.get("/dase/contracts").status_code == 200
    assert client.get("/dase/contracts?q=υλοτομ").status_code == 200
    assert client.get("/dase/contractor/096000001").status_code == 200
    assert client.get("/dase/contract/23SYMV000000001").status_code == 200
    assert client.get("/compare").status_code == 200


def test_unknowns_404(client):
    assert client.get("/dase/contractor/000000000").status_code == 404
    assert client.get("/dase/contract/23SYMV000099999").status_code == 404


def test_dase_dashboard_renders(client):
    html = client.get("/dase").data.decode()
    assert "ΔΑΣΕ" in html
    assert "Stated contract values" in html


def test_khmdhs_routes_survive_missing_dase_db(tmp_path):
    """Isolation guarantee: the second connection is lazy — khmdhs-only
    routes must work even when dase.sqlite does not exist at all."""
    kh = tmp_path / "kh.sqlite"
    _build_kh_db(kh)
    app = app_module.create_app(db_path=kh, pdf_cache_dir=tmp_path / "cache",
                                dase_db_path=tmp_path / "missing.sqlite")
    app.testing = True
    c = app.test_client()
    for url in ("/", "/contracts", "/contractors", "/authorities"):
        assert c.get(url).status_code == 200, url


def test_khmdhs_json_identical_with_and_without_dase_db(tmp_path):
    """khmdhs JSON endpoints must be byte-identical whether or not the
    ΔΑΣΕ database exists — proof the datasets do not contaminate."""
    kh = tmp_path / "kh.sqlite"
    da = tmp_path / "dase.sqlite"
    _build_kh_db(kh)
    _build_dase_db(da)

    def body(dase_path):
        app = app_module.create_app(db_path=kh,
                                    pdf_cache_dir=tmp_path / "cache",
                                    dase_db_path=dase_path)
        app.testing = True
        c = app.test_client()
        return [c.get(u).data for u in
                ("/api/timeseries.json", "/api/contractors.json",
                 "/api/flows.json", "/api/overview.json")]

    assert body(da) == body(tmp_path / "missing.sqlite")
