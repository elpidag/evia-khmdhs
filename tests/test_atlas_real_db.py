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
    assert m["antinero"]["total_eur"] == pytest.approx(659_290_845.34)
    assert m["dase"]["n_contracts"] == 1998
    assert m["dase"]["total_eur"] == pytest.approx(29_920_558.46)


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


def test_cpvs_pins(client):
    """The CPV vocabulary section on the front page: every code declared on
    an in-scope contract, counted once per contract."""
    o = client.get("/api/antinero/overview").get_json()
    cpvs = o["cpvs"]
    assert len(cpvs) == 145
    assert cpvs[0] == {"code": "77231300-1",
                      "desc": "Υπηρεσίες διαχείρισης δασών", "n": 226}
    # counts are per-contract: no code can exceed the in-scope population
    n_contracts = o["kpis"]["n_contracts"]
    assert all(0 < r["n"] <= n_contracts for r in cpvs)
    assert all(r["desc"] for r in cpvs)
    # sorted by reach, ties broken by code
    assert cpvs == sorted(cpvs, key=lambda r: (-r["n"], r["code"]))


def test_categories_pins(client):
    """Curated work-type categories (DATA_DECISIONS 2026-08-14): one per
    in-scope contract, so the stated-net sums reconcile to the programme
    total exactly."""
    o = client.get("/api/antinero/overview").get_json()
    cats = o["categories"]
    assert {c["key"]: c["n"] for c in cats} == {
        "dasotexnika": 154, "miktes_zones": 33, "arxaiologikoi": 17,
        "meletes": 14, "antidiavrotika": 12, "anadasoseis": 8,
        "ylotomies": 6, "ydatodexamenes": 1}
    assert sum(c["n"] for c in cats) == o["kpis"]["n_contracts"]
    assert sum(c["eur"] for c in cats) == pytest.approx(659_290_845.34)
    assert cats[0]["key"] == "dasotexnika"
    assert cats[0]["eur"] == pytest.approx(359_263_907.38)
    assert all(c["label"] and c["label"] != c["key"] for c in cats)
    assert cats == sorted(cats, key=lambda c: (-c["eur"], c["key"]))
    # detail supplement: label + verbatim-title evidence + provenance
    # (26SYMV019200696 recategorized with inherited title, DATA_DECISIONS
    # 2026-08-14 audit entry)
    d = client.get("/api/antinero/contract/26SYMV019200696").get_json()
    assert d["category"]["key"] == "ylotomies"
    assert d["category"]["source"] == "inherited:26SYMV018682054"
    assert "μεταπυρικά οικοσυστήματα" in d["category"]["title"]
    assert d["category"]["label"] and d["category"]["note"]


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
    assert ministry_out == pytest.approx(659_290_845.34, abs=1.0)
    assert contractor_in == pytest.approx(659_290_845.34, abs=1.0)


def test_swarm_pins(client):
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 245
    assert all(r["pe"] for r in sw)        # every in-scope contract has regions


def test_pe_yearly_reconciles(client):
    py = client.get("/api/antinero/pe-yearly").get_json()
    assert len(py["pes"]) == 59
    total = sum(p["total_eur"] for p in py["pes"]) + py["unresolved_eur"]
    assert total == pytest.approx(659_290_845.34, abs=1.0)


def test_override_authority_links_ship_their_evidence(client):
    """6 contracts are linked to their forest units by curated OVERRIDE, and
    3 of those registry titles contradict what the page then shows —
    25SYMV016491944 is titled «ΔΔ ΛΕΣΒΟΥ» over works its own PDF places in
    Ρόδος. The evidence sentence was stored from the start but never left
    the DB, so the page read as our error rather than the registry's
    (DATA_DECISIONS 2026-08-18). Every override link must carry it."""
    d = client.get("/api/antinero/contract/25SYMV016491944").get_json()
    auth = d["authorities"]
    assert len(auth) == 1
    assert auth[0]["name"] == "Διεύθυνση Δασών Δωδεκανήσου"
    assert auth[0]["source"] == "override"
    assert "ΛΕΣΒΟΥ" in auth[0]["excerpt"]          # names the wrong title…
    assert "Δωδεκανήσου" in auth[0]["excerpt"]     # …and what the PDF says
    # the registry title itself is NEVER rewritten — it is the evidence
    assert "ΛΕΣΒΟΥ" in d["title"]
    assert d["regions"][0]["region_pe"] == "Π.Ε. Ρόδου"
    import sqlite3
    conn = sqlite3.connect(f"file:{DEFAULT_DB.as_posix()}?mode=ro", uri=True)
    refs = [r[0] for r in conn.execute(
        "SELECT DISTINCT reference_number FROM contract_forest_authorities"
        " WHERE source LIKE 'override%'")]
    conn.close()
    assert len(refs) == 6
    for ref in refs:
        links = client.get(f"/api/antinero/contract/{ref}").get_json()["authorities"]
        over = [a for a in links if (a["source"] or "").startswith("override")]
        assert over, ref
        assert all(a["excerpt"] for a in over), ref


def test_dase_pins(client):
    d = client.get("/api/dase/overview").get_json()
    assert d["kpis"]["n_contracts"] == 1998
    assert d["kpis"]["n_coops"] == 246
    # 2026-08-03 payment harvest: net paid KPI with partial coverage
    # (payments posted for 891 of 2,008 live contracts; charts stay stated)
    # 2026-08-17 payment audit (closed): re-posts excluded on warrant-number
    # identity, payload amounts corrected to their own PDFs, 123 ΕΦΚΑ
    # understatements raised to their warrant totals («paid» = the whole
    # disbursement incl. the state-borne ΕΦΚΑ, user decision), every
    # scanned/odd document read by eye, 4 exclusions reversed as proven
    # same-priced instalments — every stored order document-checked
    # 2026-08-18 awardee review, batch B: 4 not-a-co-op contracts left the
    # population and the machine-hire payment 23PAY013718656 with them
    assert d["kpis"]["paid_eur"] == pytest.approx(20_405_695.74)
    assert d["kpis"]["n_paid_contracts"] == 893
    assert d["kpis"]["n_payments"] == 953
    assert len(d["by_pe"]["regions"]) == 27
    assert d["by_pe"]["unresolved"]["n"] == 4
    sw = client.get("/api/dase/swarm").get_json()
    assert len(sw["ref"]) == 1998
    # full ISO date rides along for the tooltip's DD.MM.YYYY
    assert len(sw["d"]) == 1998 and any(sw["d"])


def test_dase_sperheiada_batch_relinks(client):
    """The Δασαρχείο Σπερχειάδας Nov-2025 batch (DATA_DECISIONS
    2026-08-17): the registry lumped each co-op's payments onto one
    contract; the corrected attribution pairs the 11 payments 1:1 with
    the 11 live 2025 ΣΥΜΦΩΝΗΤΙΚΑ at the batch's uniform 0,96133 factor.
    A harvest reload that loses the `attributed_ref` re-links regresses
    here first."""
    import sqlite3
    conn = sqlite3.connect(f"file:{DASE_DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    refs = ("25SYMV017758272", "25SYMV017759613", "25SYMV017766013",
            "25SYMV017767826", "25SYMV017768486", "25SYMV017773683",
            "25SYMV017895184", "25SYMV017895643", "25SYMV017896238",
            "25SYMV017896809", "25SYMV017897089")
    for ref in refs:
        rows = conn.execute(
            "SELECT amount_with_vat FROM contract_payments "
            "WHERE attributed_ref = ? AND COALESCE(cancelled,0)=0", (ref,)).fetchall()
        assert len(rows) == 1, ref                     # exactly one payment each
        g = conn.execute("SELECT total_cost_with_vat FROM contracts "
                         "WHERE reference_number = ?", (ref,)).fetchone()[0]
        assert rows[0]["amount_with_vat"] / g == pytest.approx(0.96133, abs=0.0001), ref
    conn.close()


def test_excluded_sibling_states_its_reason_not_a_cancellation(client):
    """25SYMV016837212 is a valid, uncancelled ΚΗΜΔΗΣ contract that simply
    names no co-op (DATA_DECISIONS 2026-08-17). It leaves the calculations
    through `cancelled = 1` like every other exclusion, so the procurement
    trail on its sibling's page — and on its own — must carry the REASON
    (`related_to`) beside the flag; without it the row reads «cancelled»,
    i.e. withdrawn, which it was not."""
    d = client.get("/api/dase/contract/25SYMV016885520").get_json()
    sib = [t for t in d["timeline"]
           if t["adam"] == "25SYMV016837212"]
    assert len(sib) == 1
    assert sib[0]["cancelled"] == 1
    assert sib[0]["related_to"] == "25SYMV016885520"
    assert sib[0]["duplicate_of"] is None
    own = client.get("/api/dase/contract/25SYMV016837212").get_json()
    assert own["related_to"] == "25SYMV016885520"
    # the kept sibling itself carries neither marker
    back = [t for t in own["timeline"] if t["adam"] == "25SYMV016885520"]
    assert len(back) == 1 and back[0]["cancelled"] == 0
    assert back[0]["related_to"] is None
    # the second out-of-scope contract points at the co-op's own call-off
    # of the same framework award (DATA_DECISIONS 2026-08-18)
    other_excl = client.get("/api/dase/contract/25SYMV017324270").get_json()
    assert other_excl["related_to"] == "25SYMV017325165"
    assert other_excl["duplicate_of"] is None
    coop_lot = client.get("/api/dase/contract/25SYMV017325165").get_json()
    assert coop_lot["cancelled"] == 0 and coop_lot["related_to"] is None
    # a genuine double-posting keeps reporting itself as one: the two
    # exclusions must stay distinguishable on every surface
    dup = client.get("/api/dase/contract/21SYMV009363348").get_json()
    assert dup["duplicate_of"] == "21SYMV009363115"
    assert dup["related_to"] is None


def test_coop_totals_are_even_split_and_sum_to_the_basis(client):
    """23SYMV013747204 is the one live contract two co-ops signed jointly
    («συμφώνησαν από κοινού», one pooled quantity at unit prices, no share
    stated anywhere). It is split evenly (user decision, DATA_DECISIONS
    2026-08-17), so the per-co-op column adds up to the live basis exactly
    instead of counting €5.383,95 twice — the strongest available check
    that no co-op total is inflated."""
    coops = client.get("/api/dase/coops").get_json()
    basis = client.get("/api/dase/overview").get_json()["kpis"]["total_eur"]
    assert round(sum(c["total_eur"] for c in coops), 2) == pytest.approx(basis)
    by_vat = {c["vat"]: c for c in coops}
    assert by_vat["096067226"]["total_eur"] == pytest.approx(136_074.89)
    assert by_vat["096121014"]["total_eur"] == pytest.approx(66_301.55)
    # both still HOLD the contract — only the € are halved
    for vat, n in (("096067226", 14), ("096121014", 9)):
        assert by_vat[vat]["n_contracts"] == n
    detail = client.get("/api/dase/coop/096121014").get_json()
    assert detail["summary"]["total_eur"] == pytest.approx(66_301.55)
    shared = [c for c in detail["contracts"]
              if c["reference_number"] == "23SYMV013747204"]
    assert len(shared) == 1
    assert shared[0]["n_parties"] == 2
    assert shared[0]["share_eur"] == pytest.approx(2_691.97)
    # the contract's own page keeps the contract's own value
    assert shared[0]["total_cost_with_vat"] == pytest.approx(5_383.95)
    other = [c for c in client.get("/api/dase/coop/096067226").get_json()["contracts"]
             if c["reference_number"] == "23SYMV013747204"]
    assert len(other) == 1
    # no cent lost in the halving: the two shares rebuild the contract
    assert shared[0]["share_eur"] + other[0]["share_eur"] == pytest.approx(5_383.95)
    # every breakdown on the page adds up to the page's own total
    total = detail["summary"]["total_eur"]
    assert round(sum(y["eur"] for y in detail["yearly"]), 2) == pytest.approx(total)
    assert round(sum(u["total_eur"] for u in detail["units"]), 2) == pytest.approx(total)


def test_dase_value_modes_are_one_population(client):
    """CONTRACT VALUES draws the same contracts as dots or as value
    brackets, and the brackets are binned CLIENT-side from the swarm array
    (atlas/src/lib/transforms/histogram.ts) on the histogram payload's own
    edges. That only stays honest while the two payloads describe one
    population — so pin it here, where both are visible."""
    d = client.get("/api/dase/overview").get_json()
    h = d["histogram"]
    sw = client.get("/api/dase/swarm").get_json()
    assert h["n"] == len(sw["eur"]) == d["kpis"]["n_contracts"]

    # The shared axis: every drawn bracket is EXACTLY one doubling, so the
    # equal-width slots are a log scale and the beeswarm can place its dots
    # on them (DATA_DECISIONS 2026-08-17). Anchored on €1.000, derived from
    # the live range — never a fixed table, so a refresh widens it by itself.
    e = h["edges"]
    assert e[0] == 0
    assert all(e[i + 1] == pytest.approx(e[i] * 2) for i in range(1, len(e) - 1))
    assert 1000.0 in e
    live = [v for v in sw["eur"] if v]
    assert e[1] <= min(live) < e[2], "first doubling must hold the smallest"
    assert e[-2] <= max(live) < e[-1], "last doubling must hold the largest"
    # the unbounded catch-all below and the overflow above stay empty, so
    # the drawn axis is the pure-doubling span
    assert h["counts"][0] == 0 and h["counts"][-1] == 0

    def bin_index(v: float) -> int:
        # the convention of webui/queries.py:_bin_values, mirrored in the TS
        for i in range(len(h["edges"]) - 1):
            if h["edges"][i] <= v < h["edges"][i + 1]:
                return i
        return len(h["edges"]) - 1

    counts = [0] * len(h["edges"])
    by_year: dict[str, list[int]] = {}
    for v, y in zip(sw["eur"], sw["year"]):
        b = bin_index(v or 0.0)
        counts[b] += 1
        by_year.setdefault(y, [0] * len(h["edges"]))[b] += 1
    assert counts == h["counts"]
    # every contract carries a signature year, so the stacked segments add
    # up to the bar totals with no uncategorised remainder to draw
    assert None not in by_year
    assert [sum(col) for col in zip(*by_year.values())] == h["counts"]
    # one label and one segment slot per bin — the chart indexes them together
    assert len(h["labels"]) == len(h["counts"]) == len(h["edges"])


def test_dase_display_name_pins(client):
    """Curated display names replace registry spellings on every ΔΑΣΕ
    co-op surface (DATA_DECISIONS 2026-08-15). Expectations come from the
    dase_display_names table, never hardcoded."""
    import sqlite3
    conn = sqlite3.connect(f"file:{DASE_DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    names = {r["vat"]: (r["display_el"], r["display_en"]) for r in conn.execute(
        "SELECT vat, display_el, display_en FROM dase_display_names")}
    assert len(names) == 246

    o = client.get("/api/dase/overview").get_json()
    for c in o["top_coops"]:
        assert (c["name"], c["name_en"]) == names[c["vat"]]
        assert c["registry_name"]

    top_vat = o["top_coops"][0]["vat"]
    d = client.get(f"/api/dase/coop/{top_vat}").get_json()
    assert (d["summary"]["name"], d["summary"]["name_en"]) == names[top_vat]
    assert d["summary"]["registry_name"]
    assert d["summary"]["name_variants"]        # registry evidence intact

    # the coops directory search matches the ENGLISH display name too
    en_token = names[top_vat][1].split()[-1]
    hits = client.get(f"/api/dase/coops?q={en_token}").get_json()
    assert any(h["vat"] == top_vat for h in hits)

    # /explore ΔΑΣΕ rows carry the display name (single-contractor case)
    ref, vat = None, None
    for r in conn.execute("""
        SELECT co.reference_number, c.vat_number FROM contracts co
        JOIN contractors c USING (reference_number)
        WHERE co.cancelled = 0 AND NOT EXISTS
              (SELECT 1 FROM contracts nx
               WHERE nx.reference_number = co.next_reference_no)
          AND (SELECT COUNT(*) FROM contractors c2
               WHERE c2.reference_number = co.reference_number) = 1
        LIMIT 1"""):
        ref, vat = r[0], r[1]
    conn.close()
    from webui.dase_queries import canonical_vat
    e = client.get("/api/explore").get_json()
    row = next(x for x in e["rows"] if x["ds"] == "dase" and x["ref"] == ref)
    assert row["co"] == names[canonical_vat(vat)][0][:110]


def test_dase_map_pins(client):
    """Proportional-symbol map payload: unit circles + per-Π.Ε. residue +
    off-map unresolved must reconcile exactly to the ΔΑΣΕ stated-net basis."""
    m = client.get("/api/dase/map").get_json()
    # 48+1 seat circles + 2 seatless forest units at Π.Ε. centroids +
    # the directory-seated ΕΠΙΘΕΩΡΗΣΗ Μ-Θ (one circle at its Πυλαία seat) —
    # spelling variants of seated authorities merge via Ν./ΝΟΜΟΥ-stripped
    # folds and the curated EN identity («ΔΔ Ν. Πιερίας» → ΔΔ Πιερίας,
    # «ΦΟΥΡΝΑ/ΦΟΥΡΝΩΝ» → Δασαρχείο Φουρνάς)
    assert len(m["units"]) == 50
    # no two circles may share a curated English identity (the Pieria/Fourna
    # double-dot class of bug)
    import json as _json
    import unicodedata as _u
    from pathlib import Path as _P

    def _fold(s):
        x = _u.normalize("NFD", (s or "").upper())
        x = "".join(ch for ch in x if not _u.combining(ch))
        return " ".join(x.split())

    def _en_of(fname):
        d = _json.loads((_P(__file__).resolve().parent.parent / "khmdhs" / "data" / fname).read_text(encoding="utf-8"))
        return {_fold(k): v["en"] for k, v in d.items() if not k.startswith("_")}

    a_en = _en_of("authority_names_en.json")
    u_en = _en_of("unit_names_en.json")
    idents = [" · ".join(a_en.get(_fold(part)) or u_en.get(_fold(part)) or part
                          for part in u["name"].split(" · "))
              for u in m["units"]]
    assert len(idents) == len(set(idents)), sorted(
        i for i in idents if idents.count(i) > 1)
    # per-Π.Ε. non-forest circles, split municipal/regional vs other bodies
    assert len(m["other"]) == 25
    assert {g["kind"] for g in m["other"]} == {"muni", "misc"}
    assert m["unresolved"]["n"] == 4
    total = (sum(u["eur"] for u in m["units"])
             + sum(g["eur"] for g in m["other"])
             + m["unresolved"]["eur"])
    assert total == pytest.approx(29_920_558.46, abs=0.01)
    top = m["units"][0]
    assert top["name"] == "Δασαρχείο Ιστιαίας" and top["n"] == 38
    assert all(u["lat"] and u["lon"] for u in m["units"] + m["other"])
    # every circle carries its full contract list for the click panel,
    # each row with awarding unit/body + curated co-op display name
    assert all(len(g["contracts"]) == g["n"] for g in m["units"] + m["other"])
    assert all(u["kind"] in ("dx", "dd") for u in m["units"])
    row = m["units"][0]["contracts"][0]
    assert set(row) == {"ref", "d", "eur", "by", "coop"}
    assert row["by"] and row["coop"]


def test_dase_kind_mix_pins(client):
    """AWARDING BODIES / UNITS category share bars: both breakdowns must
    reconcile to the live population and the stated-net basis, the units
    side must stay inside the map's kind vocabulary, and no
    registry-unknown awarding body may reach the payload (the coverage
    bijection of tests/test_public_bodies.py, seen from the chart)."""
    km = client.get("/api/dase/overview").get_json()["kind_mix"]
    for side in ("bodies", "units"):
        rows = km[side]
        assert sum(r["n"] for r in rows) == 1998, side
        assert sum(r["eur"] for r in rows) == pytest.approx(
            29_920_558.46, abs=0.05), side
    assert {r["kind"] for r in km["units"]} <= {"dx", "dd", "muni", "misc"}
    # the joint distribution behind the delegation diagram must reconcile
    # to the same basis and stay inside both vocabularies
    flows = km["flows"]
    assert sum(f["n"] for f in flows) == 1998
    assert sum(f["eur"] for f in flows) == pytest.approx(29_920_558.46, abs=0.05)
    assert {f["unit"] for f in flows} <= {"dx", "dd", "muni", "misc"}
    assert {f["body"] for f in flows} == {r["kind"] for r in km["bodies"]}
    # the finding the chart states: two body kinds reach δασαρχεία, the
    # decentralized administrations at several times the ministry's scale
    into_dx = {f["body"]: f["eur"] / f["n"] for f in flows if f["unit"] == "dx"}
    assert set(into_dx) == {"ministry", "decentralized_administration"}
    assert into_dx["decentralized_administration"] > 3 * into_dx["ministry"]
    # third column: named co-ops + one pooled node, reconciling both ways
    coops, cflows = km["coops"], km["coop_flows"]
    assert len(coops) == 11                       # top 10 by € + the pool
    assert sum(c["n"] for c in coops) == 1998
    assert sum(c["eur"] for c in coops) == pytest.approx(29_920_558.46, abs=0.05)
    pooled = [c for c in coops if c["vat"] is None]
    assert len(pooled) == 1 and pooled[0]["n_coops"] > 0
    assert all(c["label"] for c in coops if c["vat"])   # display names present
    assert sum(f["n"] for f in cflows) == 1998
    assert sum(f["eur"] for f in cflows) == pytest.approx(29_920_558.46, abs=0.05)
    assert {f["unit"] for f in cflows} <= {"dx", "dd", "muni", "misc"}
    named = {c["vat"] for c in coops if c["vat"]}
    assert {f["vat"] for f in cflows if f["vat"]} == named
    # Every top co-op is hired by at least one FOREST unit. Until
    # 2026-08-18 one of them was not — the 5th-largest by € was ΑΦΜ
    # 096000173, the Ένωση Δασικών Αγροτικών Συνεταιρισμών Εύβοιας, served
    # only by a Περιφέρεια for olive-fly spraying. It was not a ΔΑ.Σ.Ε. and
    # left the dataset; a new top-10 entity that no δασαρχείο or διεύθυνση
    # ever hires is the same smell and should be looked at.
    ce = {c["vat"]: c["label"] for c in coops if c["vat"]}
    for vat, label in ce.items():
        kinds = {f["unit"] for f in cflows if f["vat"] == vat}
        assert kinds, vat
        assert kinds & {"dx", "dd"}, f"{label} ({vat}) works for no forest unit"
    # units marginal must equal the /dase map's own circle classification
    m = client.get("/api/dase/map").get_json()
    from collections import defaultdict
    agg: dict = defaultdict(lambda: [0, 0.0])
    for u in m["units"] + m["other"]:
        agg[u["kind"]][0] += u["n"]
        agg[u["kind"]][1] += u["eur"]
    agg["misc"][0] += m["unresolved"]["n"]
    agg["misc"][1] += m["unresolved"]["eur"]
    for row in km["units"]:
        assert row["n"] == agg[row["kind"]][0], row["kind"]
        assert row["eur"] == pytest.approx(agg[row["kind"]][1], abs=0.05), row["kind"]
    body_kinds = {r["kind"] for r in km["bodies"]}
    assert "unknown" not in body_kinds
    assert body_kinds <= {"ministry", "decentralized_administration",
                          "municipality", "region", "state_vehicle",
                          "other_public"}
    # δασαρχεία are the working level — the dominant units category
    assert max(km["units"], key=lambda r: r["n"])["kind"] == "dx"


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
        659_290_845.34, abs=1.0)


def test_authorities_pins(client):
    payload = client.get("/api/authorities").get_json()
    a = payload["authorities"]
    # the rest of the ΥΠΕΝ network (no recorded contracts) rides along as a
    # reference section (DATA_DECISIONS 2026-08-17)
    assert len(payload["other_units"]) == 49
    assert all(u["name"] for u in payload["other_units"])
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
    assert p["antinero"]["total_eur"] == pytest.approx(659_290_845.34)
    assert p["dase"]["total_eur"] == pytest.approx(29_920_558.46)
    assert p["dase_n_coops"] == 246
    assert [s["name"] for s in p["shared_awarders"]] == [
        "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"
    ]


def test_explore_pins(client):
    e = client.get("/api/explore").get_json()
    assert e["counts"] == {"antinero": 245, "dase": 1998, "anadohoi": 69}
    assert len(e["rows"]) == 2312
    # value bases per dataset reconcile with their own conventions
    kh_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "antinero")
    assert kh_sum == pytest.approx(659_290_845.34, abs=1.0)
    dase_sum = sum(r["v"] or 0 for r in e["rows"] if r["ds"] == "dase")
    assert dase_sum == pytest.approx(29_920_558.46, abs=1.0)
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
    assert dase_pr.count(1) == 136 and dase_pr.count(0) == 1862
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


def test_executor_display_name_pins(client):
    """Sponsor-project executors present under the SAME name as their
    co-op's /dase surfaces (DATA_DECISIONS 2026-08-16, same ΑΦΜ → same
    name): every pinned executor ΑΦΜ must have a curated display name
    (coverage guard — new executor curation cannot drift from the ΔΑΣΕ
    naming) and the API ships it, keeping the act spelling as evidence."""
    import sqlite3
    conn = sqlite3.connect(f"file:{DASE_DB.as_posix()}?mode=ro", uri=True)
    names = {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT vat, display_el, display_en FROM dase_display_names")}
    conn.close()

    o = client.get("/api/anadohoi/overview").get_json()
    rows = [(p["ada"], e) for p in o["projects"]
            for e in (p["executors"] or [])]
    pinned = [e for _, e in rows if e.get("dase_vat")]
    assert pinned
    for e in pinned:
        assert e["dase_vat"] in names           # coverage guard
        el, en = names[e["dase_vat"]]
        assert e["name"] == el
        assert e["name_en"] == en
        assert e["act_name"]                    # act spelling kept
    # identity-unconfirmed rows keep their verbatim act names untouched
    for _, e in rows:
        if not e.get("dase_vat"):
            assert "act_name" not in e and e["name"]

    # the project endpoint carries the same overlay
    ada = next(a for a, e in rows if e.get("dase_vat"))
    p = client.get(f"/api/anadohoi/project/{ada}").get_json()
    exe = [e for e in p["executors"] if e.get("dase_vat")]
    assert exe
    assert all(e["name"] == names[e["dase_vat"]][0] for e in exe)


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
