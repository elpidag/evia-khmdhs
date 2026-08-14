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
    assert m["antinero"]["n_contracts"] == 245
    assert m["antinero"]["total_eur"] == pytest.approx(658_297_730.65)
    assert m["dase"]["n_contracts"] == 2018
    assert m["dase"]["total_eur"] == pytest.approx(31_801_612.14)


def test_probable_related_pins(client):
    """The 7 ANTINERO II chains without provable RRF-16849 financing
    evidence stay in the dataset but out of every calculation
    (DATA_DECISIONS 2026-08-13). The overview payload presents them."""
    o = client.get("/api/antinero/overview").get_json()
    p = o["probable"]
    assert p["n"] == 7
    assert p["total_eur"] == pytest.approx(9_198_921.61)
    assert len(p["rows"]) == 7
    assert all(r["ref"] and r["eur"] for r in p["rows"])
    m = client.get("/api/meta").get_json()
    assert m["facts"]["kh_probable_n"] == 7
    assert m["facts"]["kh_probable_eur"] == pytest.approx(9_198_921.61)
    # excluded-but-reachable: a probable tip's detail page still resolves
    d = client.get(f"/api/antinero/contract/{p['rows'][0]['ref']}").get_json()
    assert d and d.get("reference_number") == p["rows"][0]["ref"]
    assert d["scope"]["scope"] == "antinero_probable"
    assert d["scope"]["in_scope"] == 0


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
    assert ministry_out == pytest.approx(658_297_730.65, abs=1.0)
    assert contractor_in == pytest.approx(658_297_730.65, abs=1.0)


def test_swarm_pins(client):
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 245
    assert all(r["pe"] for r in sw)        # every in-scope contract has regions


def test_pe_yearly_reconciles(client):
    py = client.get("/api/antinero/pe-yearly").get_json()
    assert len(py["pes"]) == 59
    total = sum(p["total_eur"] for p in py["pes"]) + py["unresolved_eur"]
    assert total == pytest.approx(658_297_730.65, abs=1.0)


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


def test_dase_map_pins(client):
    """Proportional-symbol map payload: unit circles + per-Π.Ε. residue +
    off-map unresolved must reconcile exactly to the ΔΑΣΕ stated-net basis."""
    m = client.get("/api/dase/map").get_json()
    assert len(m["units"]) == 48
    assert len(m["other"]) == 21
    assert m["unresolved"]["n"] == 4
    total = (sum(u["eur"] for u in m["units"])
             + sum(g["eur"] for g in m["other"])
             + m["unresolved"]["eur"])
    assert total == pytest.approx(31_801_612.14, abs=0.01)
    top = m["units"][0]
    assert top["name"] == "Δασαρχείο Ιστιαίας" and top["n"] == 38
    assert all(u["lat"] and u["lon"] for u in m["units"] + m["other"])
    # every circle carries its full contract list for the click panel
    assert all(len(g["contracts"]) == g["n"] for g in m["units"] + m["other"])
    assert all(u["kind"] in ("dx", "dd") for u in m["units"])


def test_connections_pins(client):
    n = client.get("/api/connections").get_json()
    assert len(n["contractor_authority"]) == 490
    assert len(n["contractor_pe"]) == 405
    assert len(n["flows"]) == 271
    assert len(n["contractor_signer"]) == 187
    assert len(n["pairs"]) == 12
    assert len(n["contractors"]) == 163
    assert len(n["authorities"]) == 103
    # even-split conservation: the Π.Ε. layer covers every in-scope contract
    assert sum(e["eur"] for e in n["contractor_pe"]) == pytest.approx(
        658_297_730.65, abs=1.0)


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
    assert p["antinero"]["n_vats"] == 163
    assert p["antinero"]["total_eur"] == pytest.approx(658_297_730.65)
    assert p["dase"]["total_eur"] == pytest.approx(31_801_612.14)
    assert p["dase_n_coops"] == 250
    assert [s["name"] for s in p["shared_awarders"]] == [
        "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"
    ]


def test_explore_pins(client):
    e = client.get("/api/explore").get_json()
    assert e["counts"] == {"antinero": 245, "dase": 2018, "anadohoi": 69}
    assert len(e["rows"]) == 2332
    # value bases per dataset reconcile with their own conventions
    kh_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "antinero")
    assert kh_sum == pytest.approx(658_297_730.65, abs=1.0)
    dase_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "dase")
    assert dase_sum == pytest.approx(31_801_612.14, abs=1.0)
    # sponsor rows expose status; the 21 stalled ones are findable
    stalled = [r for r in e["rows"]
               if r["ds"] == "anadohoi" and r["st"] == "no_completion_recorded"]
    assert len(stalled) == 21
    # PROC-notice flag: 40 in-scope Anti-nero contracts have a linked
    # διακήρυξη; the ΔΑΣΕ chain harvest (2026-08-03) covered all 2,164
    # contracts, so its flag is populated too
    kh_pr = [r["pr"] for r in e["rows"] if r["ds"] == "antinero"]
    assert kh_pr.count(1) == 40 and kh_pr.count(0) == 205
    dase_pr = [r["pr"] for r in e["rows"] if r["ds"] == "dase"]
    assert dase_pr.count(1) == 144 and dase_pr.count(0) == 1874
    assert all(r["pr"] is None for r in e["rows"] if r["ds"] == "anadohoi")
    # end-date flag: 148 Anti-nero contracts have a completion act,
    # 16 sponsor projects are completed (incl. the 2026-08-13 review:
    # ΑΔΜΗΕ via the 9Ο0Λ παραλαβή, ΔΕΔΔΗΕ via its last μελέτη approval);
    # ΔΑΣΕ endings were never harvested
    kh_fin = [r["fin"] for r in e["rows"] if r["ds"] == "antinero"]
    assert kh_fin.count(1) == 148 and kh_fin.count(0) == 97
    an_fin = [r["fin"] for r in e["rows"] if r["ds"] == "anadohoi"]
    assert an_fin.count(1) == 16
    assert all(r["fin"] is None for r in e["rows"] if r["ds"] == "dase")


def test_anadohoi_overview_pins(client):
    o = client.get("/api/anadohoi/overview").get_json()
    assert o["kpis"]["n_projects"] == 68
    assert o["kpis"]["stated_eur"] == pytest.approx(41_784_256.85)
    # committed € prefer the act's net figure where stated (VAT curation);
    # the 15th net project is the superseded Coca-Cola original
    assert o["kpis"]["vat_counts"] == {"net": 14, "gross": 2, "unstated": 27}
    assert o["kpis"]["median_eur"] == pytest.approx(600_000.0)
    assert o["kpis"]["statuses"]["completed"] == 16
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
