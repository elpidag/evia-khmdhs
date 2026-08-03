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
    assert m["antinero"]["total_eur"] == pytest.approx(667_496_652.26)
    assert m["dase"]["n_contracts"] == 2018
    assert m["dase"]["total_eur"] == pytest.approx(34_085_266.14)


def test_payments_pins(client):
    p = client.get("/api/antinero/payments").get_json()
    assert len(p["events"]) == 863
    assert p["undated"]["n"] == 0          # submission-date fallback covers all
    assert p["fallback"] == 180
    assert sum(e["eur"] for e in p["events"]) == pytest.approx(440_019_108.41)


def test_sankey_reconciles(client):
    s = client.get("/api/antinero/sankey").get_json()
    ministry_out = sum(l["eur"] for l in s["links"] if l["s"] == "ministry")
    contractor_in = sum(l["eur"] for l in s["links"] if l["s"] != "ministry")
    assert ministry_out == pytest.approx(667_496_652.26, abs=1.0)
    assert contractor_in == pytest.approx(667_496_652.26, abs=1.0)


def test_swarm_pins(client):
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 252
    assert all(r["pe"] for r in sw)        # every in-scope contract has regions


def test_pe_yearly_reconciles(client):
    py = client.get("/api/antinero/pe-yearly").get_json()
    assert len(py["pes"]) == 59
    total = sum(p["total_eur"] for p in py["pes"]) + py["unresolved_eur"]
    assert total == pytest.approx(667_496_652.26, abs=1.0)


def test_dase_pins(client):
    d = client.get("/api/dase/overview").get_json()
    assert d["kpis"]["n_contracts"] == 2018
    assert d["kpis"]["n_coops"] == 250
    # 2026-08-03 payment harvest: net paid KPI with partial coverage
    # (payments posted for 891 of 2,018 live contracts; charts stay stated)
    assert d["kpis"]["paid_eur"] == pytest.approx(21_298_411.32)
    assert d["kpis"]["n_paid_contracts"] == 891
    assert d["kpis"]["n_payments"] == 992
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
        667_496_652.26, abs=1.0)


def test_authorities_pins(client):
    a = client.get("/api/authorities").get_json()
    assert len(a) == 103
    both = [r for r in a if r["antinero_n"] and r["dase_n"]]
    assert len(both) == 48          # authorities active in BOTH datasets
    slugs = {r["slug"] for r in a}
    assert len(slugs) == 103        # bijective slugs
    # profile check on an authority active in BOTH datasets (the overall
    # top by stated € has no ΔΑΣΕ presence)
    pick = both[0]
    p = client.get(f"/api/authority/{pick['slug']}").get_json()
    assert p["name"] == pick["name"]
    assert p["antinero"]["contracts"] and p["dase"]["contracts"]


def test_pipelines_pins(client):
    p = client.get("/api/compare").get_json()["pipelines"]
    assert p["vat_overlap"] == []          # the zero-overlap headline fact
    assert p["antinero"]["n_vats"] == 169
    assert p["antinero"]["total_eur"] == pytest.approx(667_496_652.26)
    assert p["dase"]["total_eur"] == pytest.approx(34_085_266.14)
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
    assert kh_sum == pytest.approx(667_496_652.26, abs=1.0)
    dase_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "dase")
    assert dase_sum == pytest.approx(34_085_266.14, abs=1.0)
    # sponsor rows expose status; the 21 stalled ones are findable
    stalled = [r for r in e["rows"]
               if r["ds"] == "anadohoi" and r["st"] == "no_completion_recorded"]
    assert len(stalled) == 21
    # PROC-notice flag: 41 in-scope Anti-nero contracts have a linked
    # διακήρυξη; the ΔΑΣΕ chain harvest (2026-08-03) covered all 2,164
    # contracts, so its flag is populated too
    kh_pr = [r["pr"] for r in e["rows"] if r["ds"] == "antinero"]
    assert kh_pr.count(1) == 41 and kh_pr.count(0) == 211
    dase_pr = [r["pr"] for r in e["rows"] if r["ds"] == "dase"]
    assert dase_pr.count(1) == 144 and dase_pr.count(0) == 1874
    assert all(r["pr"] is None for r in e["rows"] if r["ds"] == "anadohoi")
    # end-date flag: 155 Anti-nero contracts have a completion act,
    # 14 sponsor projects are completed; ΔΑΣΕ endings were never harvested
    kh_fin = [r["fin"] for r in e["rows"] if r["ds"] == "antinero"]
    assert kh_fin.count(1) == 155 and kh_fin.count(0) == 97
    an_fin = [r["fin"] for r in e["rows"] if r["ds"] == "anadohoi"]
    assert an_fin.count(1) == 14
    assert all(r["fin"] is None for r in e["rows"] if r["ds"] == "dase")


def test_anadohoi_overview_pins(client):
    o = client.get("/api/anadohoi/overview").get_json()
    assert o["kpis"]["n_projects"] == 68
    assert o["kpis"]["stated_eur"] == pytest.approx(41_784_256.85)
    # committed € prefer the act's net figure where stated (VAT curation);
    # the 15th net project is the superseded Coca-Cola original
    assert o["kpis"]["vat_counts"] == {"net": 14, "gross": 2, "unstated": 27}
    assert o["kpis"]["median_eur"] == pytest.approx(600_000.0)
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
    assert m["anadohoi"] == {"n_projects": 68, "stated_eur": 41_784_256.85}


def test_arogi_pins(client):
    m = client.get("/api/meta").get_json()
    assert m["arogi"]["n_cases"] == 956 and m["arogi"]["n_fires"] == 10
    assert m["arogi"]["approved_eur"] == pytest.approx(20_059_683.94)
    e = client.get("/api/arogi/explore").get_json()
    assert len(e["rows"]) == 956
    s = client.get("/api/arogi/summary").get_json()
    active = [f for f in s["fires"] if f["n_cases"]]
    assert sum(f["approved_eur"] for f in active) > 0
    top = max(active, key=lambda f: f["approved_eur"])
    assert top["fire_id"] == "fires-2021-0708"
    # a case detail resolves with its act trail
    row = next(r for r in e["rows"] if r["n"] > 1)
    c = client.get(f"/api/arogi/case/{row['id']}").get_json()
    assert c["acts"] and all("ada" in a for a in c["acts"])
