"""PDF attachment proxy: local cache, registry 429 handling, validation."""
import sqlite3

import pytest

import webui.app as app_module


class FakeResponse:
    def __init__(self, status_code=200, content=b"%PDF-1.5 fake", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "empty.sqlite"
    sqlite3.connect(db).close()
    app = app_module.create_app(db_path=db, pdf_cache_dir=tmp_path / "cache")
    app.testing = True
    # any un-stubbed network call is a test bug
    monkeypatch.setattr(
        app_module.requests, "get",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected network call")),
    )
    yield app.test_client(), tmp_path / "cache", monkeypatch


def test_rejects_bad_kind_and_malformed_adam(client):
    c, _, _ = client
    assert c.get("/pdf/notice/22SYMV010447493").status_code == 404
    assert c.get("/pdf/contract/DROP TABLE").status_code == 404
    # kind/infix mismatch: a PAY adam under /pdf/contract/
    assert c.get("/pdf/contract/25PAY018152892").status_code == 404
    assert c.get("/pdf/payment/22SYMV010447493").status_code == 404


def test_serves_from_cache_without_network(client):
    c, cache, _ = client
    cache.mkdir(parents=True)
    (cache / "22SYMV010447493.pdf").write_bytes(b"%PDF-1.5 cached")
    r = c.get("/pdf/contract/22SYMV010447493")
    assert r.status_code == 200
    assert r.mimetype == "application/pdf"
    assert r.data == b"%PDF-1.5 cached"
    # inline, not attachment — the browser renders the PDF in the tab
    assert r.headers["Content-Disposition"].startswith("inline")


def test_fetches_once_then_caches(client):
    c, cache, monkeypatch = client
    calls = []
    monkeypatch.setattr(
        app_module.requests, "get",
        lambda url, timeout: calls.append(url) or FakeResponse(),
    )
    r = c.get("/pdf/payment/25PAY018152892")
    assert r.status_code == 200
    assert (cache / "25PAY018152892.pdf").read_bytes() == b"%PDF-1.5 fake"
    assert len(calls) == 1 and "payment/attachment/25PAY018152892" in calls[0]
    # second hit is served from disk — the network stub must not fire again
    monkeypatch.setattr(
        app_module.requests, "get",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("cache miss")),
    )
    assert c.get("/pdf/payment/25PAY018152892").status_code == 200


def test_registry_429_returns_wait_page(client):
    c, cache, monkeypatch = client
    monkeypatch.setattr(
        app_module.requests, "get",
        lambda url, timeout: FakeResponse(status_code=429, content=b"{}", headers={"Retry-After": "17"}),
    )
    r = c.get("/pdf/payment/25PAY018152892")
    assert r.status_code == 503
    assert r.headers["Retry-After"] == "17"
    assert b"rate-limiting" in r.data
    assert not (cache / "25PAY018152892.pdf").exists()


def test_non_pdf_body_is_not_cached(client):
    c, cache, monkeypatch = client
    monkeypatch.setattr(
        app_module.requests, "get",
        lambda url, timeout: FakeResponse(status_code=200, content=b'{"message":"oops"}'),
    )
    r = c.get("/pdf/contract/22SYMV010447493")
    assert r.status_code == 502
    assert not (cache / "22SYMV010447493.pdf").exists()
