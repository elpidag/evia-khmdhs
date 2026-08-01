"""Route-level tests for the Atlas JSON API (atlas_api/), incl. the
isolation guarantees inherited from webui: khmdhs-only endpoints never open
the ΔΑΣΕ database, and webui/ itself is never touched."""
import sqlite3

import pytest

import atlas_api.pdf_proxy as pdf_module
from atlas_api import app as app_module
from khmdhs.db import SCHEMA_SQL
from khmdhs.scope_loader import SCHEMA as SCOPE_SCHEMA
from tests.conftest import add_contract, add_payment, set_scope
from tests.test_dase_queries import add as add_dase, curate


def _build_kh_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SCOPE_SCHEMA)
    add_contract(conn, "22SYMV000000001", title="ANTINERO II ΕΡΓΟ",
                 eur=1_000_000.0)
    set_scope(conn, "22SYMV000000001", "antinero_ii", 1)
    add_payment(conn, "23PAY000000001", "22SYMV000000001", 400_000.0)
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
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path):
    kh = tmp_path / "kh.sqlite"
    da = tmp_path / "dase.sqlite"
    _build_kh_db(kh)
    _build_dase_db(da)
    app = app_module.create_app(db_path=kh, dase_db_path=da,
                                pdf_cache_dir=tmp_path / "cache")
    app.testing = True
    return app.test_client()


# ------------------------------------------------------------- endpoints

def test_meta(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    body = r.get_json()
    assert body["antinero"]["n_contracts"] == 1
    assert body["antinero"]["total_eur"] == pytest.approx(400_000.0)
    assert body["antinero"]["n_payments"] == 1
    assert body["dase"]["n_contracts"] == 1
    assert body["dase"]["total_eur"] == pytest.approx(5_000.0)


def test_antinero_overview_shape(client):
    r = client.get("/api/antinero/overview")
    assert r.status_code == 200
    body = r.get_json()
    for key in ("kpis", "procedures", "histogram", "direct_awards",
                "timeseries", "yearly", "studies", "top_contractors",
                "top_authorities", "top_signers", "coverage"):
        assert key in body, key
    assert body["kpis"]["n_contracts"] == 1
    assert set(body["studies"]) == {"summary", "top"}


def test_antinero_map_shape(client):
    r = client.get("/api/antinero/map")
    assert r.status_code == 200
    body = r.get_json()
    for key in ("work_regions", "home_regions", "coverage",
                "contract_points", "contractor_points", "contracts"):
        assert key in body, key
    assert body["contracts"][0]["ref"] == "22SYMV000000001"


def test_json_cache_header(client):
    r = client.get("/api/meta")
    assert "max-age=300" in r.headers.get("Cache-Control", "")


def test_antinero_list_and_detail(client):
    body = client.get("/api/antinero/contracts").get_json()
    assert len(body["rows"]) == 1
    # list rows carry the EFFECTIVE value (the €400k payment), not stated
    assert body["total_eur"] == pytest.approx(400_000.0)
    d = client.get("/api/antinero/contract/22SYMV000000001").get_json()
    assert d["reference_number"] == "22SYMV000000001"
    assert "raw_json" not in d and "raw_pretty" not in d
    assert len(d["payments"]) == 1
    assert "regions" in d and "sites" in d
    cs = client.get("/api/antinero/contractors").get_json()
    assert cs[0]["vat_number"] == "111111111"
    cb = client.get("/api/antinero/contractor/111111111").get_json()
    assert set(cb) == {"summary", "contracts", "partners", "signers",
                       "location", "map_data", "yearly"}


def test_dase_list_and_detail(client):
    body = client.get("/api/dase/contracts").get_json()
    assert len(body["rows"]) == 1
    d = client.get("/api/dase/contract/23SYMV000000001").get_json()
    assert d["reference_number"] == "23SYMV000000001"
    assert "raw_json" not in d
    coops = client.get("/api/dase/coops").get_json()
    assert coops[0]["vat"] == "096000001"
    cb = client.get("/api/dase/coop/096000001").get_json()
    assert set(cb) == {"summary", "contracts", "yearly", "units"}


def test_unknown_entities_404(client):
    assert client.get("/api/antinero/contract/22SYMV000099999").status_code == 404
    assert client.get("/api/antinero/contractor/000000000").status_code == 404
    assert client.get("/api/dase/contract/23SYMV000099999").status_code == 404
    assert client.get("/api/dase/coop/000000000").status_code == 404


# ------------------------------------------------------------- isolation

KH_ONLY_ENDPOINTS = (
    "/api/antinero/overview", "/api/antinero/map",
    "/api/antinero/contracts", "/api/antinero/contract/22SYMV000000001",
    "/api/antinero/contractors", "/api/antinero/contractor/111111111",
    "/api/antinero/payments", "/api/antinero/sankey",
    "/api/antinero/swarm", "/api/antinero/pe-yearly",
)


def test_khmdhs_endpoints_survive_missing_dase_db(tmp_path):
    kh = tmp_path / "kh.sqlite"
    _build_kh_db(kh)
    app = app_module.create_app(db_path=kh,
                                dase_db_path=tmp_path / "missing.sqlite",
                                pdf_cache_dir=tmp_path / "cache")
    app.testing = True
    c = app.test_client()
    for url in KH_ONLY_ENDPOINTS:
        assert c.get(url).status_code == 200, url
    # /api/meta degrades honestly: no dase key, still 200
    body = c.get("/api/meta").get_json()
    assert body["antinero"]["n_contracts"] == 1
    assert "dase" not in body


def test_khmdhs_endpoints_identical_with_and_without_dase_db(tmp_path):
    kh = tmp_path / "kh.sqlite"
    da = tmp_path / "dase.sqlite"
    _build_kh_db(kh)
    _build_dase_db(da)

    def bodies(dase_path):
        app = app_module.create_app(db_path=kh, dase_db_path=dase_path,
                                    pdf_cache_dir=tmp_path / "cache")
        app.testing = True
        c = app.test_client()
        return [c.get(u).data for u in KH_ONLY_ENDPOINTS]

    assert bodies(da) == bodies(tmp_path / "missing.sqlite")


# ------------------------------------------------------------- pdf proxy

class FakeResponse:
    def __init__(self, status_code=200, content=b"%PDF-1.5 fake", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


@pytest.fixture
def pdf_client(tmp_path, monkeypatch):
    db = tmp_path / "empty.sqlite"
    sqlite3.connect(db).close()
    app = app_module.create_app(db_path=db, dase_db_path=db,
                                pdf_cache_dir=tmp_path / "cache")
    app.testing = True
    monkeypatch.setattr(
        pdf_module.requests, "get",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected network call")),
    )
    yield app.test_client(), tmp_path / "cache", monkeypatch


def test_pdf_rejects_bad_kind_and_malformed_adam(pdf_client):
    c, _, _ = pdf_client
    assert c.get("/pdf/notice/22SYMV010447493").status_code == 404
    assert c.get("/pdf/contract/DROP TABLE").status_code == 404
    assert c.get("/pdf/contract/25PAY018152892").status_code == 404


def test_pdf_serves_from_cache_without_network(pdf_client):
    c, cache, _ = pdf_client
    cache.mkdir(parents=True)
    (cache / "22SYMV010447493.pdf").write_bytes(b"%PDF-1.5 cached")
    r = c.get("/pdf/contract/22SYMV010447493")
    assert r.status_code == 200
    assert r.mimetype == "application/pdf"
    assert r.data == b"%PDF-1.5 cached"
    assert r.headers["Content-Disposition"].startswith("inline")


def test_pdf_registry_429_returns_wait_page(pdf_client):
    c, cache, monkeypatch = pdf_client
    monkeypatch.setattr(
        pdf_module.requests, "get",
        lambda url, timeout: FakeResponse(status_code=429, content=b"{}",
                                          headers={"Retry-After": "17"}),
    )
    r = c.get("/pdf/payment/25PAY018152892")
    assert r.status_code == 503
    assert r.headers["Retry-After"] == "17"
    assert not (cache / "25PAY018152892.pdf").exists()


def test_pdf_non_pdf_body_is_not_cached(pdf_client):
    c, cache, monkeypatch = pdf_client
    monkeypatch.setattr(
        pdf_module.requests, "get",
        lambda url, timeout: FakeResponse(status_code=200,
                                          content=b'{"message":"oops"}'),
    )
    r = c.get("/pdf/contract/22SYMV010447493")
    assert r.status_code == 502
    assert not (cache / "22SYMV010447493.pdf").exists()
