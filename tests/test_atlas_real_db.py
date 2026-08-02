"""Pins against the committed DBs for the Atlas API.

All Atlas real-DB pins live in THIS one file so a `python -m khmdhs.refresh`
touches exactly one place. Exact-value convention follows the other
real-DB test modules.
"""
import pytest

from khmdhs.config import DASE_DB, DEFAULT_DB
from atlas_api import app as app_module

pytestmark = pytest.mark.skipif(
    not (DEFAULT_DB.exists() and DASE_DB.exists()),
    reason="committed databases not present",
)


@pytest.fixture(scope="module")
def client():
    app = app_module.create_app()
    app.testing = True
    return app.test_client()


def test_meta_pins(client):
    m = client.get("/api/meta").get_json()
    assert m["antinero"]["n_contracts"] == 252
    assert m["antinero"]["total_eur"] == pytest.approx(615_950_156.78)
    assert m["dase"]["n_contracts"] == 2018
    assert m["dase"]["total_eur"] == pytest.approx(41_418_963.96)


def test_payments_pins(client):
    p = client.get("/api/antinero/payments").get_json()
    assert len(p["events"]) == 863
    assert p["undated"]["n"] == 0          # submission-date fallback covers all
    assert p["fallback"] == 180
    assert sum(e["eur"] for e in p["events"]) == pytest.approx(545_410_749.14)


def test_sankey_reconciles(client):
    s = client.get("/api/antinero/sankey").get_json()
    ministry_out = sum(l["eur"] for l in s["links"] if l["s"] == "ministry")
    contractor_in = sum(l["eur"] for l in s["links"] if l["s"] != "ministry")
    assert ministry_out == pytest.approx(615_950_156.78, abs=1.0)
    assert contractor_in == pytest.approx(615_950_156.78, abs=1.0)


def test_swarm_pins(client):
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 252
    assert all(r["pe"] for r in sw)        # every in-scope contract has regions


def test_pe_yearly_reconciles(client):
    py = client.get("/api/antinero/pe-yearly").get_json()
    assert len(py["pes"]) == 59
    total = sum(p["total_eur"] for p in py["pes"]) + py["unresolved_eur"]
    assert total == pytest.approx(615_950_156.78, abs=1.0)


def test_dase_pins(client):
    d = client.get("/api/dase/overview").get_json()
    assert d["kpis"]["n_contracts"] == 2018
    assert d["kpis"]["n_coops"] == 250
    assert len(d["by_pe"]["regions"]) == 27
    assert d["by_pe"]["unresolved"]["n"] == 4
    sw = client.get("/api/dase/swarm").get_json()
    assert len(sw["ref"]) == 2018


def test_connections_pins(client):
    n = client.get("/api/connections").get_json()
    assert len(n["contractor_authority"]) == 510
    assert len(n["contractor_pe"]) == 423
    assert len(n["flows"]) == 281
    assert len(n["contractor_signer"]) == 194
    assert len(n["pairs"]) == 12
    assert len(n["contractors"]) == 169
    assert len(n["authorities"]) == 103
    # even-split conservation: the Π.Ε. layer covers every in-scope contract
    assert sum(e["eur"] for e in n["contractor_pe"]) == pytest.approx(
        615_950_156.78, abs=1.0)


def test_authorities_pins(client):
    a = client.get("/api/authorities").get_json()
    assert len(a) == 103
    both = [r for r in a if r["antinero_n"] and r["dase_n"]]
    assert len(both) == 48          # authorities active in BOTH datasets
    slugs = {r["slug"] for r in a}
    assert len(slugs) == 103        # bijective slugs
    p = client.get(f"/api/authority/{a[0]['slug']}").get_json()
    assert p["name"] == a[0]["name"]
    assert p["antinero"]["contracts"] and p["dase"]["contracts"]


def test_pipelines_pins(client):
    p = client.get("/api/compare").get_json()["pipelines"]
    assert p["vat_overlap"] == []          # the zero-overlap headline fact
    assert p["antinero"]["n_vats"] == 169
    assert p["antinero"]["total_eur"] == pytest.approx(615_950_156.78)
    assert p["dase"]["total_eur"] == pytest.approx(41_418_963.96)
    assert p["dase_n_coops"] == 250
    assert [s["name"] for s in p["shared_awarders"]] == [
        "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"
    ]


def test_explore_pins(client):
    e = client.get("/api/explore").get_json()
    assert e["counts"] == {"antinero": 252, "dase": 2018, "anadohoi": 69}
    assert len(e["rows"]) == 2339
    # value bases per dataset reconcile with their own conventions
    kh_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "antinero")
    assert kh_sum == pytest.approx(615_950_156.78, abs=1.0)
    dase_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "dase")
    assert dase_sum == pytest.approx(41_418_963.96, abs=1.0)
    # sponsor rows expose status; the 19 stalled ones are findable
    stalled = [r for r in e["rows"]
               if r["ds"] == "anadohoi" and r["st"] == "no_completion_recorded"]
    assert len(stalled) == 19


def test_anadohoi_overview_pins(client):
    o = client.get("/api/anadohoi/overview").get_json()
    assert o["kpis"]["n_projects"] == 68
    assert o["kpis"]["stated_eur"] == pytest.approx(41_183_092.05)
    assert o["kpis"]["statuses"]["completed"] == 14
    assert len(o["projects"]) == 69
    fires = {f["fire"]: f for f in o["fires"]}
    assert fires["Β. Εύβοια, Αύγ. 2021"]["n"] == 10
    assert fires["Τατόι–Βαρυμπόμπη–Αφίδνες, Αύγ. 2021"]["completed"] == 0
    # sponsor grouping merges registry spellings (ΔΕΗ + ΔΕΗ Α.Ε. etc.)
    top = o["sponsors"][0]
    assert top["company"] == "ΔΕΗ" and top["n"] == 6


def test_meta_anadohoi_pin(client):
    m = client.get("/api/meta").get_json()
    assert m["anadohoi"] == {"n_projects": 68, "stated_eur": 41_183_092.05}
