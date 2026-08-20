"""The joint-venture membership layer: loader validation and its guards.

The layer answers «who is behind the company that signed», and the whole
second ranking rests on it, so the loader refuses anything that would make
that view lie: a member that is itself a venture (the machine proposed
exactly that twice before review), a member that is its own venture, a
venture that holds no in-scope contract, or a mismatch between the
`members_documented` flag and the list.
"""
import json

import pytest

from khmdhs import consortium_loader as cl
from tests.conftest import add_contract, set_scope


@pytest.fixture
def db(mem_conn):
    add_contract(mem_conn, "IN1", title="ΕΡΓΟ ANTINERO IV", eur=100.0,
                 vats=("996000001",))
    set_scope(mem_conn, "IN1", "antinero_iv", 1)
    return mem_conn


def _file(tmp_path, data):
    p = tmp_path / "consortium_members.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _venture(**over):
    e = {"name": "ΚΟΙΝΟΠΡΑΞΙΑ ΤΕΣΤ", "legal_type": "Κοινοπραξία",
         "members": [{"vat": "111111111", "name": "Α"},
                     {"vat": "222222222", "name": "Β"}]}
    e.update(over)
    return {"996000001": e}


def test_accepts_a_documented_venture(db, tmp_path):
    cl.validate(_venture(), db)


def test_refuses_a_member_that_is_itself_a_venture(db, tmp_path):
    data = _venture()
    data["996000002"] = {"name": "ΑΛΛΗ Κ/Ξ", "members": [],
                         "members_documented": False}
    data["996000001"]["members"][0]["vat"] = "996000002"
    # the second venture must also be a contractor for the first check to pass
    db.execute("INSERT INTO contractors (reference_number, seq, vat_number, name) "
               "VALUES ('IN1', 1, '996000002', 'ΑΛΛΗ Κ/Ξ')")
    with pytest.raises(SystemExit, match="itself a joint venture"):
        cl.validate(data, db)


def test_refuses_a_venture_listing_itself(db):
    data = _venture()
    data["996000001"]["members"][0]["vat"] = "996000001"
    with pytest.raises(SystemExit, match="lists itself"):
        cl.validate(data, db)


def test_refuses_a_venture_that_holds_no_in_scope_contract(db):
    data = {"996999999": _venture()["996000001"]}
    with pytest.raises(SystemExit, match="holds no in-scope contract"):
        cl.validate(data, db)


def test_refuses_a_non_afm_member(db):
    data = _venture()
    data["996000001"]["members"][0]["vat"] = "12345"
    with pytest.raises(SystemExit, match="not an ΑΦΜ"):
        cl.validate(data, db)


def test_refuses_a_duplicate_member(db):
    data = _venture()
    data["996000001"]["members"][1]["vat"] = "111111111"
    with pytest.raises(SystemExit, match="twice"):
        cl.validate(data, db)


def test_undocumented_venture_must_list_nobody(db):
    """The 22 ventures whose members no document names carry an empty list —
    a flag that disagrees with the list would silently drop money out of the
    member view."""
    ok = _venture(members=[], members_documented=False)
    cl.validate(ok, db)
    bad = _venture(members_documented=False)          # flag says no, list says yes
    with pytest.raises(SystemExit, match="flagged undocumented"):
        cl.validate(bad, db)
    bad2 = _venture(members=[])                        # flag says yes, list empty
    with pytest.raises(SystemExit, match="lists none"):
        cl.validate(bad2, db)


def test_warns_on_a_venture_of_one(db, caplog):
    data = _venture(members=[{"vat": "111111111", "name": "Α"}])
    with caplog.at_level("WARNING"):
        cl.validate(data, db)
    assert "single member" in caplog.text
