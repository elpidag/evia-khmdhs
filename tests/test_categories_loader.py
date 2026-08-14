"""Loader tests for the curated Anti-nero work-type categories
(khmdhs/data/contract_categories.json → contract_categories +
category_labels; DATA_DECISIONS 2026-08-14)."""
import pytest


def _curated(entries: dict, cats: dict | None = None) -> dict:
    meta = cats if cats is not None else {
        "dasotexnika": {"label": "Δασοτεχνικά έργα πρόληψης", "note": "n"},
        "meletes": {"label": "Μελέτες", "note": "n"},
    }
    return {"_categories": meta, **entries}


def test_loader_roundtrip_writes_rows_and_labels(mem_conn):
    from tests.conftest import add_contract
    from khmdhs import categories_loader

    add_contract(mem_conn, "22SYMV000000001", title="A")
    add_contract(mem_conn, "22SYMV000000002", title="B")
    curated = _curated({
        "22SYMV000000001": {"category": "dasotexnika",
                            "title": "Εργασίες ειδικών δασοτεχνικών έργων",
                            "source": "pdf"},
        "22SYMV000000002": {"category": "meletes",
                            "title": "Εκπόνηση διαχειριστικών μελετών",
                            "source": "inherited:22SYMV000000001"},
    })
    assert categories_loader.write_db(mem_conn, curated) == 2
    rows = {r[0]: (r[1], r[2], r[3]) for r in mem_conn.execute(
        "SELECT reference_number, category, title, source "
        "FROM contract_categories")}
    assert rows["22SYMV000000001"] == (
        "dasotexnika", "Εργασίες ειδικών δασοτεχνικών έργων", "pdf")
    assert rows["22SYMV000000002"][2] == "inherited:22SYMV000000001"
    labels = dict(mem_conn.execute(
        "SELECT category, label FROM category_labels"))
    assert labels == {"dasotexnika": "Δασοτεχνικά έργα πρόληψης",
                      "meletes": "Μελέτες"}


def test_loader_refuses_unknown_category_ref_and_missing_fields(mem_conn):
    from tests.conftest import add_contract
    from khmdhs import categories_loader

    add_contract(mem_conn, "22SYMV000000001", title="A")
    good = {"category": "dasotexnika", "title": "T", "source": "pdf"}
    with pytest.raises(SystemExit):  # category not in _categories
        categories_loader.write_db(mem_conn, _curated(
            {"22SYMV000000001": {**good, "category": "nope"}}))
    with pytest.raises(SystemExit):  # ref not stored
        categories_loader.write_db(mem_conn, _curated(
            {"22SYMV000000099": good}))
    with pytest.raises(SystemExit):  # no title evidence
        categories_loader.write_db(mem_conn, _curated(
            {"22SYMV000000001": {**good, "title": ""}}))
    with pytest.raises(SystemExit):  # no source
        categories_loader.write_db(mem_conn, _curated(
            {"22SYMV000000001": {**good, "source": ""}}))


def test_loader_warns_on_uncovered_in_scope_contracts(mem_conn, caplog):
    from tests.conftest import add_contract, set_scope
    from khmdhs import categories_loader

    add_contract(mem_conn, "22SYMV000000001", title="A")
    add_contract(mem_conn, "22SYMV000000002", title="B")
    set_scope(mem_conn, "22SYMV000000001", "antinero_ii", 1)
    set_scope(mem_conn, "22SYMV000000002", "antinero_ii", 1)
    curated = _curated({
        "22SYMV000000001": {"category": "dasotexnika", "title": "T",
                            "source": "pdf"}})
    import logging
    with caplog.at_level(logging.WARNING):
        assert categories_loader.write_db(mem_conn, curated) == 1
    assert any("22SYMV000000002" in m for m in caplog.messages)
