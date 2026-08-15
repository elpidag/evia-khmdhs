"""Curated stated-value corrections for contracts (DATA_DECISIONS 2026-08-14)."""
import json

from khmdhs import db
from khmdhs.contract_corrections import apply_contract_corrections


def _mini_db(tmp_path):
    conn = db.init_db(tmp_path / "t.sqlite")
    conn.execute(
        "INSERT INTO contracts (reference_number, title, total_cost_without_vat, "
        "total_cost_with_vat, fetched_at) VALUES (?,?,?,?,?)",
        ("21SYMV000000001", "test", 2537393.13, 3146367.48, "2026-08-14"))
    conn.execute(
        "INSERT INTO contract_objects (reference_number, seq, cost_without_vat, "
        "short_description) VALUES (?,?,?,?)",
        ("21SYMV000000001", 0, 2537393.13, "wrong item"))
    conn.commit()
    return conn


def _corrections(tmp_path, entries):
    p = tmp_path / "corr.json"
    p.write_text(json.dumps({"_comment": "test", **entries}), encoding="utf-8")
    return p


def test_applies_amounts_note_and_objects(tmp_path):
    conn = _mini_db(tmp_path)
    p = _corrections(tmp_path, {
        "21SYMV000000001": {
            "total_cost_without_vat": 253739.13,
            "total_cost_with_vat": 314636.52,
            "objects": {"0": 253739.13},
            "reason": "signed PDF states the smaller figure",
        }})
    assert apply_contract_corrections(conn, p) == 1
    row = conn.execute(
        "SELECT total_cost_without_vat, total_cost_with_vat, correction_note "
        "FROM contracts WHERE reference_number = '21SYMV000000001'").fetchone()
    assert row[0] == 253739.13 and row[1] == 314636.52
    assert "signed PDF" in row[2]
    obj = conn.execute(
        "SELECT cost_without_vat FROM contract_objects "
        "WHERE reference_number = '21SYMV000000001' AND seq = 0").fetchone()
    assert obj[0] == 253739.13


def test_idempotent_and_partial_fields(tmp_path):
    conn = _mini_db(tmp_path)
    p = _corrections(tmp_path, {
        "21SYMV000000001": {"total_cost_without_vat": 100.0, "reason": "net only"}})
    assert apply_contract_corrections(conn, p) == 1
    assert apply_contract_corrections(conn, p) == 1  # re-stamp, same result
    row = conn.execute(
        "SELECT total_cost_without_vat, total_cost_with_vat FROM contracts "
        "WHERE reference_number = '21SYMV000000001'").fetchone()
    # COALESCE keeps the untouched gross
    assert row[0] == 100.0 and row[1] == 3146367.48


def test_unknown_ref_warns_and_is_not_counted(tmp_path, caplog):
    conn = _mini_db(tmp_path)
    p = _corrections(tmp_path, {
        "99SYMV999999999": {"total_cost_without_vat": 1.0, "reason": "no such row"}})
    with caplog.at_level("WARNING"):
        assert apply_contract_corrections(conn, p) == 0
    assert "matched no stored contract" in caplog.text


def test_missing_file_is_noop(tmp_path):
    conn = _mini_db(tmp_path)
    assert apply_contract_corrections(conn, tmp_path / "absent.json") == 0


def test_exclude_marks_duplicate_and_links_kept_twin(tmp_path):
    conn = _mini_db(tmp_path)
    p = _corrections(tmp_path, {
        "21SYMV000000001": {
            "exclude": True,
            "duplicate_of": "21SYMV000000002",
            "reason": "ΚΗΜΔΗΣ double-posting of 21SYMV000000002",
        }})
    assert apply_contract_corrections(conn, p) == 1
    row = conn.execute(
        "SELECT cancelled, duplicate_of, correction_note, total_cost_without_vat "
        "FROM contracts WHERE reference_number = '21SYMV000000001'").fetchone()
    assert row[0] == 1
    assert row[1] == "21SYMV000000002"
    assert "double-posting" in row[2]
    assert row[3] == 2537393.13  # amounts untouched — the row is registry evidence
