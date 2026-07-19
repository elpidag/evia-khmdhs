"""Tests for scope-table building and modification-chain supersede logic."""
from khmdhs.scope_loader import build_scopes

from tests.conftest import add_contract


def test_supersede_marks_original(mem_conn):
    add_contract(mem_conn, "22SYMV000000001",
                 title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 1.Α",
                 fund_num="2022ΤΑ07500000")
    add_contract(mem_conn, "22SYMV000000002",
                 title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 1.Α ΤΡΟΠΟΠΟΙΗΣΗ",
                 fund_num="2022ΤΑ07500000", prev="22SYMV000000001")
    scopes, superseded = build_scopes(mem_conn, overrides={})
    assert scopes["22SYMV000000001"][0] == "antinero_i"
    assert scopes["22SYMV000000002"][0] == "antinero_i"
    assert superseded == {"22SYMV000000001": "22SYMV000000002"}


def test_cancelled_successor_does_not_supersede(mem_conn):
    add_contract(mem_conn, "22SYMV000000001",
                 title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 1.Α",
                 fund_num="2022ΤΑ07500000")
    add_contract(mem_conn, "22SYMV000000002",
                 title="ΤΡΟΠΟΠΟΙΗΣΗ", fund_num="2022ΤΑ07500000",
                 prev="22SYMV000000001", cancelled=1)
    _, superseded = build_scopes(mem_conn, overrides={})
    assert superseded == {}


def test_prev_pointing_outside_db_is_ignored(mem_conn):
    add_contract(mem_conn, "22SYMV000000002",
                 title="ΤΡΟΠΟΠΟΙΗΣΗ", fund_num="2022ΤΑ07500000",
                 prev="22SYMV999999999")  # original never loaded
    _, superseded = build_scopes(mem_conn, overrides={})
    assert superseded == {}


def test_chain_of_two_modifications(mem_conn):
    add_contract(mem_conn, "A1", title="ΕΡΓΟ", fund_num="2022ΤΑ07500000")
    add_contract(mem_conn, "A2", title="1η ΤΡΟΠ", fund_num="2022ΤΑ07500000", prev="A1")
    add_contract(mem_conn, "A3", title="2η ΤΡΟΠ", fund_num="2022ΤΑ07500000", prev="A2")
    _, superseded = build_scopes(mem_conn, overrides={})
    assert superseded == {"A1": "A2", "A2": "A3"}


def test_overrides_flow_through(mem_conn):
    add_contract(mem_conn, "22SYMV000000009",
                 title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 2Β ΤΟΥ ΙΙ")
    scopes, _ = build_scopes(mem_conn, overrides={"22SYMV000000009": "antinero_ii"})
    assert scopes["22SYMV000000009"] == ("antinero_ii", "curated:antinero_supplement")


def test_amendment_inherits_phase_from_predecessor(mem_conn):
    # Predecessor gets its phase from a curated override; the amendment has
    # no fund code and no ANTINERO in the title — it must inherit.
    add_contract(mem_conn, "22SYMV000000001",
                 title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 3Β ΤΟΥ ΙΙ")
    add_contract(mem_conn, "22SYMV000000002",
                 title="1η ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΜΒΑΣΗΣ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 3Β ΤΟΥ ΙΙ",
                 prev="22SYMV000000001")
    add_contract(mem_conn, "22SYMV000000003",
                 title="2η ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΜΒΑΣΗΣ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 3Β ΤΟΥ ΙΙ",
                 prev="22SYMV000000002")
    scopes, superseded = build_scopes(
        mem_conn, overrides={"22SYMV000000001": "antinero_ii"})
    assert scopes["22SYMV000000002"] == ("antinero_ii", "inherited_from_prev:22SYMV000000001")
    assert scopes["22SYMV000000003"] == ("antinero_ii", "inherited_from_prev:22SYMV000000002")
    assert superseded["22SYMV000000001"] == "22SYMV000000002"
    assert superseded["22SYMV000000002"] == "22SYMV000000003"


def test_non_antinero_predecessor_does_not_infect_amendment(mem_conn):
    add_contract(mem_conn, "17SYMV000000001", title="ΣΥΝΤΗΡΗΣΗ ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ")
    add_contract(mem_conn, "17SYMV000000002", title="ΤΡΟΠΟΠΟΙΗΣΗ ΣΥΝΤΗΡΗΣΗΣ",
                 prev="17SYMV000000001")
    scopes, _ = build_scopes(mem_conn, overrides={})
    assert scopes["17SYMV000000002"][0] == "non_antinero"


def test_supplementary_contract_does_not_supersede(mem_conn):
    # A «1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ» adding money on top of the parent keeps both
    # versions countable; a same-value restatement still supersedes.
    add_contract(mem_conn, "24SYMV000000001", title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΤΜΗΜΑΤΟΣ 6 ANTINERO III",
                 fund_num="2023ΤΑ07500012", eur=4713581.17)
    add_contract(mem_conn, "25SYMV000000002", title="ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΤΜΗΜΑΤΟΣ 6 ΕΡΓΟΥ 1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ",
                 fund_num="2023ΤΑ07500012", prev="24SYMV000000001", eur=706739.26)
    add_contract(mem_conn, "25SYMV000000003", title="ΔΕΞΑΜΕΝΕΣ ΔΧ ΘΕΣΣΑΛΟΝΙΚΗΣ ANTINERO III",
                 fund_num="2023ΤΑ07500012", eur=4143136.01)
    add_contract(mem_conn, "26SYMV000000004", title="ΔΕΞΑΜΕΝΕΣ ΔΧ ΘΕΣΣΑΛΟΝΙΚΗΣ 1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ",
                 fund_num="2023ΤΑ07500012", prev="25SYMV000000003", eur=4143136.01)
    _, superseded = build_scopes(mem_conn, overrides={})
    assert "24SYMV000000001" not in superseded          # additive supplement
    assert superseded["25SYMV000000003"] == "26SYMV000000004"  # same-value restatement
