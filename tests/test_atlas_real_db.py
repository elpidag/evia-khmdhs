"""Pins against the committed DBs for the Atlas API.

All Atlas real-DB pins live in THIS one file so a `python -m khmdhs.refresh`
touches exactly one place. Exact-value convention follows the other
real-DB test modules.
"""
import re
import sqlite3

import pytest

from khmdhs.config import DASE_DB, DEFAULT_DB
from atlas_api import app as app_module
from atlas_api import queries_extra as qx

pytestmark = pytest.mark.skipif(
    not (DEFAULT_DB.exists() and DASE_DB.exists()),
    reason="committed databases not present",
)


@pytest.fixture(scope="module")
def client():
    app = app_module.create_app()
    app.testing = True
    return app.test_client()


@pytest.fixture(scope="module")
def kh():
    """A read-only handle on the committed Anti-nero DB, for pins that assert
    on the data itself rather than on an endpoint."""
    con = sqlite3.connect(DEFAULT_DB)
    con.row_factory = sqlite3.Row
    yield con
    con.close()


def test_meta_pins(client):
    m = client.get("/api/meta").get_json()
    assert m["antinero"]["n_contracts"] == 245
    assert m["antinero"]["total_eur"] == pytest.approx(622_534_181.72)
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
                      "desc": "Υπηρεσίες διαχείρισης δασών", "n": 225}
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
        "dasotexnika": 154, "miktes_zones": 33, "arxaiologikoi": 16,
        "meletes": 14, "antidiavrotika": 13, "anadasoseis": 8,
        "ylotomies": 6, "ydatodexamenes": 1}
    assert sum(c["n"] for c in cats) == o["kpis"]["n_contracts"]
    assert sum(c["eur"] for c in cats) == pytest.approx(622_534_181.72)
    assert cats[0]["key"] == "dasotexnika"
    # −€1.675.269,22 on 2026-08-18: all eight tender-budget corrections
    # are δασοτεχνικά contracts, so the whole drop lands in this category
    assert cats[0]["eur"] == pytest.approx(357_588_638.16)
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
    # the lag story (2026-08-22): medians computed server-side
    assert p["lag"]["median_days"] == 247
    assert p["lag"]["median_first_days"] == 170
    assert p["lag"]["n"] == 863 and p["lag"]["n_contracts"] == 226
    # every dated event's contract carries its cohort year for the strip
    assert all(
        p["contracts"][e["ref"]].get("y")
        for e in p["events"] if e["d"])
    assert p["undated"]["n"] == 0          # submission-date fallback covers all
    assert p["fallback"] == 180
    assert sum(e["eur"] for e in p["events"]) == pytest.approx(440_019_108.41)


def test_sankey_reconciles(client):
    s = client.get("/api/antinero/sankey").get_json()
    ministry_out = sum(l["eur"] for l in s["links"] if l["s"] == "ministry")
    contractor_in = sum(l["eur"] for l in s["links"] if l["s"] != "ministry")
    assert ministry_out == pytest.approx(622_534_181.72, abs=1.0)
    assert contractor_in == pytest.approx(622_534_181.72, abs=1.0)


def test_types_of_work_lenses(client):
    """TYPES OF WORKS (vocabulary corrected 2026-08-22): the categories ship
    their English label and the works their contracts NAME; the themes lens
    counts contracts under every work named (overlapping by design), 87 of
    245 name none. Firebreaks are THREE disjoint themes — μικτές /
    εστεγασμένες / συντήρηση — and the generic one is retired, as are the
    0-link perifraxi and the «με εγκεκριμένες μελέτες» false positives."""
    o = client.get("/api/antinero/overview").get_json()
    cats = {c["key"]: c for c in o["categories"]}
    # the English NAME is curation and may be reworded (it was, 2026-08-22) —
    # pin that every category ships one, never its exact words
    assert all(c["label_en"] and c["label_en"] != c["key"] for c in o["categories"])
    top = {w["theme"]: w["n"] for w in cats["dasotexnika"]["names"]}
    assert top["katharismoi"] > top["odiko_diktyo"] > top["syntirisi_zonon"] > 40
    th = o["themes"]
    # 158 titles name a work; 43 more title-silent contracts got theirs from
    # the CALL's works enumeration (DATA_DECISIONS 2026-08-22, second entry)
    assert th["n_contracts"] == 245 and th["n_named"] == 201 and th["unspecified"] == 44
    assert {w["theme"]: w["n"] for w in th["themes"]} == {
        "katharismoi": 102, "odiko_diktyo": 85, "syntirisi_zonon": 55,
        "miktes_zones": 35, "arxaiologikoi": 17, "anadasoseis": 15, "meletes": 14,
        "nero": 13, "antidiavrotika": 13, "estegasmenes_zones": 10, "dasokomika": 8,
        "ylotomies": 5, "psiles_zones": 4, "ypoleimmata": 4}
    # every theme bar carries an English label; retired themes are absent
    assert all(w["label_en"] and w["label_en"] != w["theme"] for w in th["themes"])
    keys = {w["theme"] for w in th["themes"]}
    assert "perifraxi" not in keys and "antipyrikes_zones" not in keys
    # TITLE-sourced firebreak themes are DISJOINT — no title names two kinds
    # (verified on every title); a CALL enumeration may honestly name two
    # (e.g. Λέσβου: συντήρηση ψιλών ζωνών AND δημιουργία στεγασμένων)
    kh = sqlite3.connect(DEFAULT_DB)
    two = kh.execute(
        """SELECT COUNT(*) FROM contract_work_themes a
             JOIN contract_work_themes b
               ON a.reference_number = b.reference_number AND a.theme < b.theme
            WHERE a.theme IN ('syntirisi_zonon','miktes_zones','estegasmenes_zones')
              AND b.theme IN ('syntirisi_zonon','miktes_zones','estegasmenes_zones')
              AND a.source NOT LIKE 'call:%'"""
    ).fetchone()[0]
    ncall = kh.execute(
        "SELECT COUNT(DISTINCT reference_number) FROM contract_work_themes"
        " WHERE source LIKE 'call:%'").fetchone()[0]
    kh.close()
    assert two == 0
    assert ncall == 43


def test_deliverables_and_undocumented_calls(client):
    """The 1-2-3 model (DATA_DECISIONS 2026-08-22): study 14 /
    study_and_works 126 / works 105 — 126 since 2026-08-23, when the ΕΣΑ
    design clause and the chain were read (DATA_DECISIONS); the
    design-build clause is quoted; the nine date-only ΤΑΙΠΕΔ calls appear
    in the trail unlinked."""
    o = client.get("/api/antinero/overview").get_json()
    assert o["deliverables"] == {"study": 14, "study_and_works": 126,
                                 "works": 105}
    d = client.get("/api/antinero/contract/23SYMV012972469").get_json()
    assert d["deliverables"]["kind"] == "study_and_works"
    assert "εκπονηθεί από τον Ανάδοχο" in d["deliverables"]["excerpt"]
    rows = [t for t in d["timeline"] if t.get("undocumented")]
    assert len(rows) == 1 and rows[0]["adam"] is None
    assert rows[0]["d"] == "2023-05-22" and "HRADF" in rows[0]["title"]
    kh = sqlite3.connect(DEFAULT_DB)
    n = kh.execute("SELECT COUNT(*) FROM contract_deliverables").fetchone()[0]
    kh.close()
    assert n == 245


def test_study_scatter_and_classes(client):
    """STUDY COSTS (2026-08-22): the four classes partition the 245 and the
    scatter's points are the chain-attributed stated fees."""
    o = client.get("/api/antinero/overview").get_json()
    cl = o["studies"]["classes"]
    # 24 / 102 since the 2026-08-23 deliverables correction (5 works → s&w)
    assert cl == {"stated": 105, "db_unstated": 24, "works_none": 102,
                  "study_only": 14}
    assert sum(cl.values()) == 245
    pts = o["studies"]["points"]
    assert len(pts) == o["studies"]["summary"]["n_with"] == 105
    assert all(p["c"] and p["s"] > 0 for p in pts)


def test_unit_flow_reconciles(client):
    """MONEY FLOW (2026-08-21): the ΥΠΕΝ unit that signed → contractors —
    four units, top-10 + pooled, both columns the basis to the cent."""
    u = client.get("/api/antinero/unit-flow").get_json()
    left = [n for n in u["nodes"] if n["side"] == "l"]
    right = [n for n in u["nodes"] if n["side"] == "r"]
    assert len(left) == 4 and len(right) == 11
    assert sum(n["eur"] for n in left) == pytest.approx(622_534_181.72, abs=1.0)
    assert sum(n["eur"] for n in right) == pytest.approx(622_534_181.72, abs=1.0)
    assert sum(l["eur"] for l in u["links"]) == pytest.approx(622_534_181.72, abs=1.0)
    assert u["total_eur"] == pytest.approx(622_534_181.72, abs=1.0)
    assert sum(n["n"] for n in left) == 245
    # every link joins a unit to a contractor node that exists
    ids = {n["id"] for n in u["nodes"]}
    assert all(l["s"] in ids and l["t"] in ids for l in u["links"])


def test_swarm_pins(client):
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 245
    assert all(r["pe"] for r in sw)        # every in-scope contract has regions


def test_pe_yearly_reconciles(client):
    py = client.get("/api/antinero/pe-yearly").get_json()
    assert len(py["pes"]) == 59
    total = sum(p["total_eur"] for p in py["pes"]) + py["unresolved_eur"]
    assert total == pytest.approx(622_534_181.72, abs=1.0)


def test_document_kind_pins(client):
    """ΚΗΜΔΗΣ files several kinds of act under one ΣΥΜΒ ΑΔΑΜ and types them all
    «Έργα»/«Υπηρεσίες», so what each record IS is read from the document
    itself. All 246 in-scope records ARE συμβάσεις — the kind says which
    (DATA_DECISIONS 2026-08-18)."""
    from collections import Counter
    import sqlite3 as _sq
    from khmdhs.config import DEFAULT_DB as _DB
    con = _sq.connect(_DB)
    kinds = Counter(k for (k,) in con.execute("""
        SELECT c.document_kind FROM contracts c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        WHERE s.in_scope = 1"""))
    con.close()
    assert sum(kinds.values()) == 245
    # 246 συμβάσεις: 200 original contracts, 25 revisions of terms,
    # 15 supplementary works (4 as the contract, 11 as its approval),
    # 6 deadline extensions — the composition /methodology prints
    assert kinds["contract"] == 199
    assert kinds["amendment"] == 25
    assert kinds["supplementary_contract"] + kinds["approval_ape_supplementary"] == 15
    assert kinds["approval_schedule_extension"] == 6
    assert kinds["approval_ape"] == 0   # every one of them also approves works
    assert kinds["unknown"] == 0          # every in-scope record is readable
    # and the page can say so, verbatim
    from khmdhs.document_kinds import KINDS
    assert KINDS["contract"] == ("Αρχική σύμβαση", "Original contract")
    assert KINDS["approval_ape_supplementary"][1] == "Approval of supplementary works"
    d = client.get("/api/antinero/contract/26SYMV019488916").get_json()
    assert d["document_kind"]["kind"] == "approval_schedule_extension"
    # the front page states the composition in prose; it reads these numbers
    # off the overview payload, so payload and DB must agree exactly
    dk = client.get("/api/antinero/overview").get_json()["document_kinds"]
    assert dk["total"] == sum(kinds.values()) == dk["counts"]["contract"] +         kinds["amendment"] + 15 + kinds["approval_schedule_extension"]
    assert dk["counts"] == dict(kinds)
    assert dk["labels"]["amendment"] == {"el": "Τροποποίηση όρων",
                                         "en": "Revision of terms"}
    assert d["document_kind"]["label_el"] == "Παράταση προθεσμίας"
    assert d["document_kind"]["label_en"] == "Deadline extension"
    assert "παράτασης χρονοδιαγράμματος" in d["document_kind"]["evidence"]


def test_network_pins(client):
    """The programme network is drawn from the families layer, so it must
    partition the in-scope population exactly: every contract either cites a
    call in its own signed text or cites none, and the two never overlap
    (DATA_DECISIONS 2026-08-18). The chart's printed counts come straight
    from these stats, so a drift shows up here first."""
    net = client.get("/api/antinero/network").get_json()
    st = net["stats"]
    assert st["n_contracts"] == len(net["nodes"]) == 245
    # 134 ΚΗΜΔΗΣ ΑΔΑΜ + the 4 ΤΑΙΠΕΔ calls known by date only
    # (undocumented_calls.json, DATA_DECISIONS 2026-08-22)
    assert st["n_calls"] == 138 and st["n_date_calls"] == 4
    # the three bands the chart draws, and nothing left over
    assert st["n_in_multi_calls"] + st["n_single_call"] + st["n_no_call"] == 245
    assert (st["n_in_multi_calls"], st["n_multi_calls"]) == (144, 54)
    assert (st["n_single_call"], st["n_no_call"]) == (84, 17)
    # a call with no sibling is not a cluster, and a bridge needs two calls
    # 30 since the date-calls joined: two contractors bridge through them
    assert st["n_bridge_multi"] <= st["n_bridge_contractors"] == 30
    assert st["total_eur"] == pytest.approx(622_534_181.72, abs=1.0)
    # the timeline arrangement prints this and places every dot by it —
    # 37 since the date-call trios (04.03.2022, 22.05.2023) sign same-day
    assert st["n_same_day_calls"] == 37
    # every date-only call node is flagged and every node carries its scope
    assert sum(1 for n in net["nodes"] if n.get("udc")) == 9
    assert all(n["dk"] in ("works", "study_and_works", "study") for n in net["nodes"])
    # the fire season travels WITH its count, so the shaded stripes and the
    # sentence next to them cannot drift apart
    fs = net["fire_season"]
    assert (fs["from"], fs["to"]) == ("05-01", "10-31")
    assert fs["n_contracts"] == 120
    assert fs["n_contracts"] == sum(
        1 for n in net["nodes"] if "05-01" <= (n["d"] or "")[5:] <= "10-31")
    assert st["n_same_day_calls"] <= st["n_multi_calls"]
    # every node carries what the chart colours, sizes, dates and labels by
    assert all(n["phase"] for n in net["nodes"])
    assert all(n["eur"] is not None for n in net["nodes"])
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\d", n["d"] or "") for n in net["nodes"])
    # the calls the chart names are ΚΗΜΔΗΣ πρόσκληση ΑΔΑΜ — plus the four
    # the works ride on the nodes (TYPES OF WORKS dots, 2026-08-22):
    # 380 theme links over 201 contracts, 44 naming none — the layer's
    # own pinned numbers
    links = sum(len(n["wk"]) for n in net["nodes"])
    assert links == 380
    assert sum(1 for n in net["nodes"] if not n["wk"]) == 44
    assert {t for n in net["nodes"] for t in n["wk"]} <= {
        "katharismoi", "odiko_diktyo", "syntirisi_zonon", "miktes_zones",
        "estegasmenes_zones", "psiles_zones", "ypoleimmata", "ylotomies",
        "dasokomika", "nero", "anadasoseis", "antidiavrotika", "meletes",
        "arxaiologikoi"}
    # date ids of the ΤΑΙΠΕΔ calls, curated with verbatim evidence
    calls = {n["call"] for n in net["nodes"] if n["call"]}
    assert len(calls) == 138
    assert sum(1 for c in calls if c.startswith("date:")) == 4
    assert all(
        re.fullmatch(r"\d\dPROC\d{9}", c) or re.fullmatch(r"date:\d{4}-\d\d-\d\d", c)
        for c in calls)


def test_meta_family_facts_match_the_network(client):
    """The methodology prose prints these; they must equal what the chart
    shows, or the page explains a picture it is not drawing."""
    f = client.get("/api/meta").get_json()["facts"]
    st = client.get("/api/antinero/network").get_json()["stats"]
    # meta counts ΚΗΜΔΗΣ-ΑΔΑΜ families only; the chart adds the four
    # date-only ΤΑΙΠΕΔ calls (their nine contracts leave the no-call band)
    assert f["kh_family_calls"] == st["n_calls"] - st["n_date_calls"]
    assert f["kh_family_none"] == st["n_no_call"] + 9
    assert f["kh_family_contracts"] + f["kh_family_none"] == 245
    # the registry's own chain declares far less than the texts do
    assert f["kh_family_declared"] == 77
    assert f["kh_notice"] == 41


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
    # since 2026-08-19 the other lots of a procurement live in the family
    # diagram rather than the trail table — the reason rides with the row
    sib = [t for t in d["family_acts"]
           if t["adam"] == "25SYMV016837212"]
    assert len(sib) == 1
    assert sib[0]["cancelled"] == 1
    assert sib[0]["related_to"] == "25SYMV016885520"
    assert sib[0]["duplicate_of"] is None
    own = client.get("/api/dase/contract/25SYMV016837212").get_json()
    assert own["related_to"] == "25SYMV016885520"
    # the kept sibling itself carries neither marker
    back = [t for t in own["family_acts"] if t["adam"] == "25SYMV016885520"]
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


def test_dase_sankey_counts_each_contract_exactly_once(client):
    """Splitting a jointly signed contract's € between its holders must not
    split the CONTRACT: every column of the AWARDING PROCESS diagram is an
    aggregate over the live population, so each must sum to exactly the
    1.998 live contracts — one contract, counted once (user, 2026-08-18)."""
    o = client.get("/api/dase/overview").get_json()
    n_live = o["kpis"]["n_contracts"]
    km = o["kind_mix"]
    for column in ("bodies", "units", "flows", "coops", "coop_flows"):
        assert sum(r["n"] for r in km[column]) == n_live, column
        assert sum(r["eur"] for r in km[column]) == pytest.approx(
            o["kpis"]["total_eur"], abs=0.05), column


def test_every_dase_surface_reports_the_same_euros_per_coop(client):
    """One co-op, one number. The even split of a jointly signed contract
    (DATA_DECISIONS 2026-08-18) has to hold on EVERY surface, not just the
    one it was written for: the ranking, the co-op directory, the co-op's
    own page and the AWARDING PROCESS sankey must agree to the cent.

    They did not: the sankey attributed a joint contract to its lead co-op
    at full value while the ranking split it, so ΣΙΔΗΡΟΧΩΡΙΟΥ and
    ΠΕΤΡΟΛΟΦΟΥ each had two different totals on one page — invisible only
    because both fall outside the top ten and land in the pooled node."""
    coops = {c["vat"]: c["total_eur"] for c in client.get("/api/dase/coops").get_json()}
    km = client.get("/api/dase/overview").get_json()["kind_mix"]
    sankey = {c["vat"]: c["eur"] for c in km["coops"] if c["vat"]}
    for vat, eur in sankey.items():
        assert eur == pytest.approx(coops[vat], abs=0.02), vat
    # the pooled node must equal the co-ops it pools, on the same basis
    pooled = [c for c in km["coops"] if not c["vat"]][0]
    rest = sum(v for k, v in coops.items() if k not in sankey)
    assert pooled["eur"] == pytest.approx(rest, abs=0.05)
    # and the two co-ops that share 23SYMV013747204 carry their halves here
    for vat, share in (("096067226", 2_691.98), ("096121014", 2_691.97)):
        page = client.get(f"/api/dase/coop/{vat}").get_json()
        shared = [c for c in page["contracts"]
                  if c["reference_number"] == "23SYMV013747204"]
        assert shared and shared[0]["share_eur"] == pytest.approx(share)
        assert page["summary"]["total_eur"] == pytest.approx(coops[vat], abs=0.02)


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
    # the co-op column applies the even split (DATA_DECISIONS 2026-08-18):
    # the € of a jointly signed contract divide between its holders, but the
    # CONTRACT is counted ONCE — this is an aggregate over the population, so
    # every column must sum to the 1.998 live contracts, never 1.999
    assert sum(c["n"] for c in coops) == 1998
    assert sum(c["eur"] for c in coops) == pytest.approx(29_920_558.46, abs=0.05)
    pooled = [c for c in coops if c["vat"] is None]
    assert len(pooled) == 1 and pooled[0]["n_coops"] > 0
    assert all(c["label"] for c in coops if c["vat"])   # display names present
    assert sum(f["n"] for f in cflows) == 1998      # one contract, counted once
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


def test_per_contractor_totals_sum_to_the_programme_basis(client):
    """The ranking and the headline must be the same money (user decision,
    DATA_DECISIONS 2026-08-20). Before it, a jointly signed contract was
    counted whole for each partner and the per-contractor Σ stood €32,5M
    above the basis."""
    rows = client.get("/api/antinero/contractors").get_json()
    assert len(rows) == 151
    assert sum(r["total_eur"] or 0.0 for r in rows) == pytest.approx(
        622_534_181.72, abs=0.01)


def test_two_in_scope_contracts_are_signed_by_two_parties(kh):
    """Every other joint venture signed as a κοινοπραξία with an ΑΦΜ of its
    own. These two have none, so their members ARE the parties and the € is
    halved between them: 24SYMV016018183 is an «Ένωση Οικονομικών Φορέων»,
    and 22SYMV010795606 is a κοινοπραξία whose party clause enumerates two
    firms while stating no ΑΦΜ for itself — the registry keyed it under the
    first of them (DATA_DECISIONS 2026-08-20, second entry)."""
    multi = [r["reference_number"] for r in kh.execute("""
        SELECT ct.reference_number FROM contracts ct
        JOIN contract_scope s ON s.reference_number = ct.reference_number
        JOIN contractors co ON co.reference_number = ct.reference_number
        WHERE s.in_scope = 1
        GROUP BY ct.reference_number HAVING COUNT(*) > 1""")]
    assert multi == ["22SYMV010795606", "24SYMV016018183"]


def test_curated_contract_parties_are_the_ones_the_pdfs_name(kh):
    """The nine 2026-08-20 party corrections, each read from the contract's
    own preamble. A regression here means the registry's member list came
    back — INSERT OR REPLACE restores it, so contract_corrections must run
    after every refetch."""
    expected = {
        "26SYMV018718889": "996551622",   # Κ/Ξ ΤΙΓΚΑΣ – ΧΑΤΖΗΝΙΚΟΛΑΟΥ
        "23SYMV013201917": "996625363",   # Κ/Ξ ΦΙΛΙΠΠΑΚΗΣ – ΑΛΣΟΣ
        "26SYMV018661963": "803202324",   # Κ/Ξ ΛΑΜΠΙΡΗΣ – ΡΕΒΕΛΙΩΤΗΣ
        "26SYMV018779399": "803233350",   # Κ/Ξ ΒΕΛΩΝΗΣ – ΚΑΖΑΝΤΣΟΓΛΟΥ
        "23SYMV013201961": "996665717",   # Κ/Ξ ΑΓΓΕΛΑΤΟΣ – ΓΚΙΚΑΣ – ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ
        "26SYMV018755812": "803214556",   # Κ/Ξ ΦΙΛΙΠΠΑΚΗΣ – ΑΠΟΣΤΟΛΙΔΗΣ
        "26SYMV018756094": "803210570",   # Κ/Ξ ΛΑΓΚΑΔΙΝΟΣ – ΝΙΚΟΛΟΠΟΥΛΟΣ
        "26SYMV018739467": "998255970",   # signed by ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ alone
        "26SYMV018725481": "998255970",
    }
    # and the one correction that names TWO parties, because the κοινοπραξία
    # that signed states no ΑΦΜ of its own
    assert [r["vat_number"] for r in kh.execute(
        "SELECT vat_number FROM contractors WHERE reference_number = ? "
        "ORDER BY seq", ("22SYMV010795606",))] == ["998255970", "998434068"]
    for ref, vat in expected.items():
        rows = [r["vat_number"] for r in kh.execute(
            "SELECT vat_number FROM contractors WHERE reference_number = ?",
            (ref,))]
        assert rows == [vat], ref
        # and the party must be locatable, or its contracts fall off the maps
        assert kh.execute("SELECT COUNT(*) FROM contractor_locations "
                          "WHERE vat_number = ? AND region_pe IS NOT NULL",
                          (vat,)).fetchone()[0] == 1, vat


def test_joint_contract_shares_are_whole_cents(kh):
    """The split allocates every cent: two halves of €183.304,03 cannot both
    be rounded, or the ranking lands a cent short of the basis."""
    con = sqlite3.connect(DEFAULT_DB)
    con.row_factory = sqlite3.Row
    qx.apply_stated_basis(con)
    shares = qx.antinero_contractor_shares(con)
    con.close()
    flat = [s for rows in shares.values() for s in rows]
    assert {s["ref"] for s in flat} == {"22SYMV010795606", "24SYMV016018183"}
    for ref in ("22SYMV010795606", "24SYMV016018183"):
        rows = [s for s in flat if s["ref"] == ref]
        assert sum(s["share_eur"] for s in rows) == pytest.approx(
            rows[0]["full_eur"], abs=0.005), ref
    assert sorted(s["share_eur"] for s in flat if
                  s["ref"] == "24SYMV016018183") == [91_652.01, 91_652.02]
    # an even €836.613,02 halves exactly; the odd one above cannot
    assert sorted(s["share_eur"] for s in flat if
                  s["ref"] == "22SYMV010795606") == [418_306.51, 418_306.51]


def test_wound_up_joint_ventures_are_flagged_not_hidden(client, kh):
    """A κοινοπραξία is formed for one job and wound up when it ends — 20 of
    the in-scope contractors are no longer active in ΓΕΜΗ. They stay the
    contractors of their contracts (they signed them); the page says what the
    register says now, and links it (user, 2026-08-20)."""
    gone = {r["vat_number"]: r["gemi_status"] for r in kh.execute("""
        SELECT vat_number, gemi_status FROM contractor_locations
         WHERE gemi_status IS NOT NULL AND gemi_status <> 'Ενεργή'
           AND vat_number IN (SELECT co.vat_number FROM contractors co
                              JOIN contract_scope s USING (reference_number)
                              WHERE s.in_scope = 1)""")}
    assert len(gone) == 20
    assert set(gone.values()) == {"Διαγραφή", "Λύση - Εκκαθάριση"}
    # the struck-off ΦΙΛΙΠΠΑΚΗΣ–ΑΛΣΟΣ joint venture is still the contractor
    d = client.get("/api/antinero/contract/23SYMV013201917").get_json()
    assert [c["vat_number"] for c in d["contractors"]] == ["996625363"]
    st = d["contractor_status"]["996625363"]
    assert st["status"] == "Διαγραφή" and st["gemi"] == "171650506000"
    # an active party carries no flag
    assert client.get("/api/antinero/contract/26SYMV018718889").get_json()[
        "contractor_status"] == {}


def test_member_firm_view_is_the_same_money(client, kh):
    """The second ranking (user, 2026-08-20): the same population and the same
    total as «as contracted», with one substitution — a joint venture whose
    members are on record is replaced by them, its € split evenly."""
    o = client.get("/api/antinero/overview").get_json()
    facts = o["consortiums"]
    # 57 since the party-clause screen of 2026-08-20; 46 documented since the
    # same day's ΓΕΜΗ managementPersons sweep (user-confirmed batches A + B):
    # the register lists each member with ΑΦΜ and role — batch B's second
    # members sit under the combined role «Μέλος & Διαχειριστής»
    assert (facts["n"], facts["n_documented"], facts["n_firms"]) == (57, 46, 63)
    # the ventures hold 31,7% of the programme; the undocumented ones sit
    # identically in both views and the page says so
    assert facts["eur"] == pytest.approx(197_612_041.99, abs=0.01)
    assert facts["eur_unsplit"] == pytest.approx(40_816_532.04, abs=0.01)

    con = sqlite3.connect(DEFAULT_DB)
    con.row_factory = sqlite3.Row
    qx.apply_stated_basis(con)
    firms = qx.antinero_member_firms(con)
    parties = qx.antinero_contractors_list(con)
    con.close()
    total = sum(r["total_eur"] for r in firms)
    assert total == pytest.approx(622_534_181.72, abs=0.01)
    assert total == pytest.approx(sum(r["total_eur"] or 0 for r in parties), abs=0.01)
    # substituting members for ventures leaves FEWER names, not more
    assert len(firms) == 136 and len(parties) == 151
    # the point of the view: Τ&Τ ΚΑΤΑΣΚΕΥΕΣ is 8th as a contractor and 3rd as
    # a firm, because half of a €22,9M κοινοπραξία is its own
    tt = next(r for r in firms if r["vat_number"] == "998807500")
    assert tt["via_eur"] == pytest.approx(11_439_920.44, abs=0.01)
    assert [r["vat_number"] for r in firms].index("998807500") == 2
    # and no joint venture with curated members survives as a name of its own
    with_members = {r[0] for r in kh.execute(
        "SELECT venture_vat FROM consortium_members")}
    assert not (with_members & {r["vat_number"] for r in firms})


def test_consortium_members_are_firms_not_ventures(kh):
    """A κοινοπραξία is never a member of a κοινοπραξία — the machine proposed
    exactly that for ΛΙΑΧΤΙΔΑ and ΜΠΟΜΠΟΤΗ, and both were rejected on review."""
    ventures = {r[0] for r in kh.execute("SELECT vat_number FROM consortiums")}
    members = {r[0] for r in kh.execute("SELECT member_vat FROM consortium_members")}
    assert not (ventures & members)
    assert len(members) == 63
    # every member carries the document it was read from, or the entry says
    # plainly that it was identified by name against the registry
    assert kh.execute("SELECT COUNT(*) FROM consortium_members").fetchone()[0] == 93
    undocumented = kh.execute(
        "SELECT COUNT(*) FROM consortiums WHERE members_documented = 0").fetchone()[0]
    assert undocumented == 11


def test_connections_pins(client):
    n = client.get("/api/connections").get_json()
    # every count here dropped on 2026-08-20, when nine contracts were
    # re-keyed to the party their signed text names: seven joint ventures
    # signed as a κοινοπραξία holding its own ΑΦΜ (the registry had listed
    # its members) and two were signed by one company alone. Ten individuals
    # who only ever appeared as members left the contractor population, and
    # with them their edges — 500 → 475 authority pairs, 401 → 377 region
    # pairs, 277 → 258 flows, 181 → 174 signer pairs. Each rose by one the
    # same day, when ΓΕΩΓΝΩΜΩΝ Ο.Ε. was recorded as the second party of
    # 22SYMV010795606: one firm, one more contract, one more of each edge
    # every flow surface is on the EVEN SPLIT since 2026-08-20 (a contract is
    # divided equally between its regions and its parties — the documents
    # state no other allocation), so the flows, their per-year breakdown and
    # the origins all reconcile to the programme total; the tolerance is the
    # per-row rounding over 259 / 355 / 57 rows
    basis = 622_534_181.72
    assert sum(f["total_eur"] for f in n["flows"]) == pytest.approx(basis, abs=0.5)
    assert sum(f["total_eur"] for f in n["flows_yearly"]) == pytest.approx(basis, abs=0.5)
    assert sum(o["total_eur"] for o in n["origins"]) == pytest.approx(basis, abs=0.5)
    assert all(len(f["year"]) == 4 for f in n["flows_yearly"])
    # 476 until 2026-08-21: two ΥΠΕΝ acts keyed lot 15Γ's ΑΔΑΜ for lot 15Α
    # and had hung Ξάνθη/Ροδόπη on a Εύβοια contract (and Καστοριά/Φλώρινα on
    # lot 4Δ) — re-attributed, the pairs fell away (DATA_DECISIONS 2026-08-21)
    assert len(n["contractor_authority"]) == 474
    assert len(n["contractor_pe"]) == 378
    # 259 until 2026-08-21, when two ventures' HQ regions followed their own
    # contracts (Μαρούσι→Καβάλα, Κόρινθος→Λίμνη Ευβοίας) and two (home, work)
    # pairs merged into existing ones — DATA_DECISIONS 2026-08-21
    assert len(n["flows"]) == 257
    assert len(n["contractor_signer"]) == 175
    # and with them the visible partnerships: a κοινοπραξία is ONE registry
    # party, so the only pairs left are the two contracts whose venture had no
    # ΑΦΜ of its own to sign with
    assert len(n["pairs"]) == 2          # was 12 before the party corrections
    assert len(n["contractors"]) == 151
    assert len(n["authorities"]) == 105
    # even-split conservation: the Π.Ε. layer covers every in-scope contract
    assert sum(e["eur"] for e in n["contractor_pe"]) == pytest.approx(
        622_534_181.72, abs=1.0)


def test_authorities_pins(client):
    payload = client.get("/api/authorities").get_json()
    a = payload["authorities"]
    # the rest of the ΥΠΕΝ network (no recorded contracts) rides along as a
    # reference section (DATA_DECISIONS 2026-08-17)
    assert len(payload["other_units"]) == 49
    assert all(u["name"] for u in payload["other_units"])
    assert len(a) == 105
    both = [r for r in a if r["antinero_n"] and r["dase_n"]]
    assert len(both) == 48          # authorities active in BOTH datasets
    slugs = {r["slug"] for r in a}
    assert len(slugs) == 105        # bijective slugs
    # profile check on an authority active in BOTH datasets (the overall
    # top by stated € has no ΔΑΣΕ presence)
    pick = both[0]
    p = client.get(f"/api/authority/{pick['slug']}").get_json()
    assert p["name"] == pick["name"]
    assert p["antinero"]["contracts"] and p["dase"]["contracts"]


def test_pipelines_pins(client):
    p = client.get("/api/compare").get_json()["pipelines"]
    assert p["vat_overlap"] == []          # the zero-overlap headline fact
    # 151, not 163: seven companies were split across a whitespace-padded
    # ΑΦΜ and one across an eight-digit one (DATA_DECISIONS 2026-08-18), and
    # ten more were joint-venture MEMBERS the registry had keyed as parties
    # (DATA_DECISIONS 2026-08-20) — the κοινοπραξία that signed replaced them
    assert p["antinero"]["n_vats"] == 151
    assert p["antinero"]["total_eur"] == pytest.approx(622_534_181.72)
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
    assert kh_sum == pytest.approx(622_534_181.72, abs=1.0)
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
    assert kh_pr.count(1) == 41 and kh_pr.count(0) == 204
    dase_pr = [r["pr"] for r in e["rows"] if r["ds"] == "dase"]
    assert dase_pr.count(1) == 136 and dase_pr.count(0) == 1862
    assert all(r["pr"] is None for r in e["rows"] if r["ds"] == "anadohoi")
    # end-date flag: 148 Anti-nero contracts have a completion act,
    # 16 sponsor projects are completed (incl. the 2026-08-13 review:
    # ΑΔΜΗΕ via the 9Ο0Λ παραλαβή, ΔΕΔΔΗΕ via its last μελέτη approval);
    # ΔΑΣΕ endings were never harvested
    kh_fin = [r["fin"] for r in e["rows"] if r["ds"] == "antinero"]
    # 148 until 2026-08-21: lot 15Α's acceptance act came back from lot 15Γ
    assert kh_fin.count(1) == 149 and kh_fin.count(0) == 96
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


def test_contract_chain_pins(client):
    """ΥΠΕΝ posts a later act on an existing contract under a NEW ΣΥΜΒ ΑΔΑΜ,
    and `scope_loader` takes the earlier record out of scope so the money is
    counted once. /explore therefore ships ONE row per chain, and the row must
    carry every record of it (DATA_DECISIONS 2026-08-19)."""
    from atlas_api import queries_extra as qx
    import sqlite3 as _sq
    from khmdhs.config import DEFAULT_DB as _DB
    con = _sq.connect(_DB)
    con.row_factory = _sq.Row
    chains = qx.contract_chains(con)
    con.close()
    # 42 chains of two records, 7 of three, one of five — 110 records in all
    assert len(chains) == 50
    sizes = sorted(len(v) for v in chains.values())
    assert sizes[0] == 2 and sizes[-1] == 5
    assert sum(sizes) == 110
    # the deepest chain, in order, ending on the record that is in scope
    parnitha = chains["26SYMV019098206"]
    assert parnitha[0] == "24SYMV015643849"
    assert parnitha[-1] == "26SYMV019098206"
    # an ADDITIVE supplementary contract is not a version: both stay in scope
    # and both keep their own row (23SYMV013600200 + its 1η συμπληρωματική)
    flat = {m for seq in chains.values() for m in seq}
    assert "24SYMV015185915" not in flat and "23SYMV013600200" not in flat

    rows = client.get("/api/explore").get_json()["rows"]
    kh = [r for r in rows if r["ds"] == "antinero"]
    assert len(kh) == 245                     # unchanged: chains were already tips
    seen = set()
    for r in kh:                              # no ΑΔΑΜ may appear twice
        for ref in [r["ref"], *r.get("alt", [])]:
            assert ref not in seen, ref
            seen.add(ref)
    assert round(sum(r["v"] or 0 for r in kh), 2) == 622534181.72
    row = next(r for r in kh if r["ref"] == "26SYMV019098206")
    # the span runs from the contract's signature to the last act's OWN date —
    # ΚΗΜΔΗΣ files every later act under the contract's date, so the registry
    # field would have collapsed three of these five records onto one day
    assert row["d"] == "2024-10-22" and row["d1"] == "2026-05-26"
    assert [v["db"] for v in row["vs"]] == [
        "signed", "signature", "signature", "published", "published"]
    assert len({v["d"] for v in row["vs"]}) == 5
    assert row["t"].startswith("Εργασίες ειδικών δασοτεχνικών")   # the ORIGINAL's title
    assert [v["k"] for v in row["vs"]] == [
        "contract", "approval_ape_supplementary", "approval_schedule_extension",
        "approval_ape_supplementary", "approval_ape_supplementary"]
    assert row["vs"][0]["v"] == 3779479.64 and row["vs"][-1]["v"] == 4999994.82
    # the €4,1M σύμβαση that used to be unreachable is searchable again
    assert any("25SYMV017345053" in (r.get("alt") or []) for r in kh)


def test_contract_chain_reaches_the_detail_page(client):
    """Both ends of a chain must show the whole chain — the timeline draws
    from it and the trail lists it."""
    for ref, n in (("26SYMV019098206", 5), ("25SYMV017345053", 2),
                   ("22SYMV010785854", 0)):
        chain = client.get(f"/api/antinero/contract/{ref}").get_json()["chain"]
        assert len(chain) == n, ref
        assert sum(1 for a in chain if a["self"]) == (1 if n else 0)
        for a in chain:                       # dates must be axis-ready
            assert a["d"] is None or len(a["d"]) == 10


def test_every_payment_tick_has_a_date(client):
    """The timeline draws one tick per payment order, so every order needs a
    date — and 182 of the 886 live orders carry only the submission stamp,
    which the frozen contract_detail does not expose (DATA_DECISIONS
    2026-08-19)."""
    d = client.get("/api/antinero/contract/26SYMV019098206").get_json()
    live = [p for p in d["payments"] if not p["cancelled"]]
    assert live and all(p.get("d") and len(p["d"]) == 10 for p in live)
    # the one that has no signed_date at all still gets its date
    assert any(p["signed_date"] is None and p["d"] for p in live)


def test_a_later_act_is_dated_by_its_own_document(client):
    """ΚΗΜΔΗΣ copies the CONTRACT's signature date onto every act posted
    against it: 39 of the 46 in-scope records that are not an original
    contract carry their parent's date verbatim. 26SYMV018978343 was signed
    07.05.2026 and filed as 01.08.2025 (DATA_DECISIONS 2026-08-19)."""
    from atlas_api import queries_extra as qx
    assert qx.act_own_date("26SYMV018978343") == ("2026-05-07", "signature")
    d = client.get("/api/antinero/contract/26SYMV018978343").get_json()
    assert d["contract_signed_date"][:10] == "2025-08-01"   # the registry's
    assert d["own_date"] == "2026-05-07"                    # the document's
    assert d["own_date_basis"] == "signature"
    # an original contract keeps the registry's field: it IS its signature
    o = client.get("/api/antinero/contract/25SYMV017345053").get_json()
    assert o["own_date"] == "2025-08-01" and o["own_date_basis"] == "signed"


def test_the_bar_draws_what_was_promised_not_the_paperwork(client, kh):
    """The contract timeline's bar is signature → the deadline the contract
    ANNOUNCED, with a lighter stretch per extension (user, 2026-08-19).

    Since the curated reading landed, the DOCUMENT is what announced it: 243
    of 246 in-scope contracts state a deadline in their own signed text and
    the other 3 state a fire season, which is one too — Greece's runs 1 May
    to 31 October. The registry's own fields remain as the fallback for a
    contract added since the last curation run, which is why the basis
    vocabulary still carries them."""
    from collections import Counter
    seen = Counter()
    src = Counter()
    ext_steps = ext_chains = 0
    for (ref,) in kh.execute(
            "SELECT reference_number FROM contract_scope WHERE in_scope = 1"):
        dl = qx.contract_deadlines(kh, ref)
        seen[dl["basis"] or "none"] += 1
        if dl["extensions"]:
            ext_chains += 1
            ext_steps += len(dl["extensions"])
            # an extension only exists relative to a deadline already in force
            assert dl["deadline"] is not None, ref
            # a step that moved the deadline forward did move it; the others
            # (per-area grants, re-statements) are flagged `later: False`
            assert all((e["deadline"] > dl["deadline"]) or not e["later"]
                       for e in dl["extensions"]), ref
            for e in dl["extensions"]:
                src[e["source"]] += 1
    assert seen == {"document": 242, "document_season": 3}
    # 16 steps over 14 chains until 2026-08-21 (9 «Παράταση προθεσμίας»
    # records + 7 supplementary approvals with a later end date); since the
    # Diavgeia extension approvals joined (phase 1 of the lifecycle layer,
    # DATA_DECISIONS 2026-08-21): 439 steps over 160 chains — 423 from the
    # acts, 16 ΚΗΜΔΗΣ records (an act re-stating a ΚΗΜΔΗΣ record's deadline
    # merges into that step; the refusal and the three acts whose stated
    # deadline precedes their own date are no steps — 443 before that rule)
    # 162 chains since two acts whose subject keyed the wrong ΑΔΑΜ were
    # re-pointed to the contracts their own text names (curation pass 1)
    # 435 since the duration unit is folded («Ημέρες».upper() kept its
    # accent, so 14 days read as 14 months and four supplementary approvals
    # drew deadlines in 2027–2028 — pass 3, 2026-08-21)
    assert (ext_chains, ext_steps) == (162, 435)
    assert src == {"diavgeia": 423, "khmdhs": 12}
    # the deepest case: 15 months from the start of works, then one
    # «Παράταση προθεσμίας» — and the registry's own end date agrees to the
    # day (2026-01-21 against the document's 2026-01-22)
    d = client.get("/api/antinero/contract/26SYMV019098206").get_json()["deadlines"]
    assert d["deadline"] == "2026-01-22" and d["basis"] == "document"
    assert [e["deadline"] for e in d["extensions"]] == ["2026-05-31"]
    # and the contract whose time is a season, not a number of months
    d2 = client.get("/api/antinero/contract/26SYMV018978343").get_json()["deadlines"]
    assert d2["basis"] == "document_season" and d2["deadline"] == "2025-10-31"
    # the counts the methodology prose prints come from /api/meta, not prose
    f = client.get("/api/meta").get_json()["facts"]
    assert f["kh_deadline_document"] == 242 and f["kh_deadline_document_season"] == 3
    assert f["kh_deadline_ext_steps"] == 435      # 16 until the Diavgeia acts joined (2026-08-21)


def test_authority_evidence_is_quotable_greek(kh):
    """The forest-authority excerpts are cut from the ORIGINAL subject, not
    from the folded matching text: the contract page now quotes them as
    evidence, and a folded excerpt reads «XΩPIKHΣ APMOΔIOTHTAΣ» in half-Latin
    letters. Match in the folded alphabet, quote from the document."""
    rows = kh.execute("SELECT reference_number, excerpt FROM"
                      " contract_forest_authorities WHERE excerpt IS NOT NULL")
    for r in rows:
        # these two words appear in almost every act subject; folded they
        # come out with Latin A/P/M/O/T inside a Greek word
        assert "APMO" not in r["excerpt"], r["reference_number"]
        assert "ΔAΣAPX" not in r["excerpt"], r["reference_number"]
    ex = kh.execute("SELECT excerpt FROM contract_forest_authorities"
                    " WHERE reference_number = ?",
                    ("26SYMV018978343",)).fetchone()["excerpt"]
    assert "χωρικής αρμοδιότητας Δασαρχείου Χαλκίδας" in ex
    assert "για το τμήμα του έργου" in ex


def test_the_municipality_layer_says_what_the_documents_say(client, kh):
    """Which δήμος each contract worked in — one level finer than the Π.Ε.
    layer (DATA_DECISIONS 2026-08-19). The rules the user approved are what
    these pins hold: the call counts as evidence and the row says so; a
    δήμος outside the contract's curated Π.Ε. is recorded and FLAGGED with
    the region layer untouched; every name resolves to a Καλλικράτης δήμος.
    """
    n, c, flagged, from_call = kh.execute(
        "SELECT COUNT(*), COUNT(DISTINCT reference_number), SUM(outside_region),"
        " SUM(from_call IS NOT NULL) FROM contract_municipalities").fetchone()
    assert (n, c) == (595, 153)
    # only what NOTHING accounts for stays flagged: of the 49 δήμοι that sit
    # outside their contract's curated regions, 30 are administered by the
    # service that names them, 11 are in that service's own seat region and
    # 6 carry a user verdict — 2 are left
    assert flagged == 2 and from_call == 79
    why = dict(kh.execute(
        "SELECT outside_pe_explained, COUNT(*) FROM contract_municipalities"
        " WHERE outside_pe_explained IS NOT NULL GROUP BY 1"))
    assert why == {"covers_pe": 30, "seat": 11, "curated verdict": 6}
    # every row carries its evidence and a code the gazetteer knows
    codes = {r[0] for r in kh.execute("SELECT code FROM greek_municipalities")}         if kh.execute("SELECT 1 FROM sqlite_master WHERE name='greek_municipalities'"
                      ).fetchone() else None
    for r in kh.execute("SELECT reference_number, municipality_code, excerpt"
                        " FROM contract_municipalities"):
        assert r["excerpt"].strip(), r["reference_number"]
        assert r["municipality_code"].isdigit()
        if codes:
            assert r["municipality_code"] in codes
    # the region layer did NOT move: a flagged δήμος is still outside
    row = kh.execute(
        "SELECT region_pe FROM contract_municipalities WHERE reference_number = ?"
        " AND name = ?", ("23SYMV012992150", "Ασπροπύργου")).fetchone()
    assert row["region_pe"] == "Π.Ε. Δυτικής Αττικής"
    pes = {r[0] for r in kh.execute(
        "SELECT region_pe FROM contract_project_regions WHERE reference_number = ?",
        ("23SYMV012992150",))}
    assert "Π.Ε. Δυτικής Αττικής" not in pes
    # and the endpoint carries it with the flag
    d = client.get("/api/antinero/contract/23SYMV012992150").get_json()
    asp = next(m for m in d["municipalities"] if m["name"] == "Ασπροπύργου")
    # Αιγάλεω administers Δυτ. Αττική, so this one is explained, not flagged
    assert asp["outside_region"] == 0 and asp["outside_pe_explained"] == "covers_pe"
    assert asp["from_call"] == "23PROC012763593"
    assert "ΑΣΠΡΟΠΥΡΓΟΥ" in asp["excerpt"].upper()


def test_explore_carries_the_municipalities(client):
    """/explore filters by δήμος, so the payload has to carry them — Anti-nero
    rows only, and absent (not empty) for the 93 that name none, since the
    row list is shipped once and every byte counts (2026-08-19)."""
    rows = client.get("/api/explore").get_json()["rows"]
    kh_rows = [r for r in rows if r["ds"] == "antinero"]
    with_mu = [r for r in kh_rows if r.get("mu")]
    assert len(kh_rows) == 245 and len(with_mu) == 152
    assert len({m for r in with_mu for m in r["mu"]}) == 220
    assert not any(r.get("mu") for r in rows if r["ds"] != "antinero")
    # the δήμοι of one contract, as its call names them
    row = next(r for r in kh_rows if r["ref"] == "23SYMV012992150")
    assert "Μαραθώνος" in row["mu"] and "Ωρωπού" in row["mu"]


def test_the_trail_holds_only_this_contracts_own_records(client):
    """ΚΗΜΔΗΣ's adamChain returns the whole procurement family, so a
    multi-lot award used to put the OTHER lots in a contract's trail —
    other companies' contracts, listed as if they were documents of this one
    (19 in-scope pages, up to 11 rows each). The Anti-nero trail now keeps
    the procurement's acts and this contract's own records, and the diagram
    carries the family (user, 2026-08-19)."""
    d = client.get("/api/antinero/contract/24SYMV014843550").get_json()
    kinds = [t["kind"] for t in d["timeline"]]
    # the call, the award, the request and the commitment approval all stay
    assert kinds.count("notice") == 3 and "auction" in kinds
    assert "request" in kinds and "approved_request" in kinds
    # the three other lots of award 24AWRD014592135 are gone
    assert not [t for t in d["timeline"] if t["kind"] == "contract"]
    assert d["family"] and len(d["family"]["contracts"]) > 1
    # a contract's OWN later records stay: the Πάρνηθα chain keeps all four
    d2 = client.get("/api/antinero/contract/26SYMV019098206").get_json()
    own = {t["adam"] for t in d2["timeline"] if t["kind"] == "contract"}
    assert "24SYMV015643849" in own and "26SYMV018426173" in own
    # ΔΑΣΕ follows the same rule (user, 2026-08-19): its trail holds its own
    # records, its FamilyTree is fed by `family_acts`
    d3 = client.get("/api/dase/contract/25SYMV016885520").get_json()
    assert not [t for t in d3["timeline"] if t["adam"] == "25SYMV016837212"]
    assert [t for t in d3["family_acts"] if t["adam"] == "25SYMV016837212"]


def test_the_run_up_acts_fit_the_timeline_axis(kh):
    """The contract timeline draws the procurement's own acts — primary
    request, commitment approval, call, award — on a dotted run-up BEFORE the
    signature (user request, 2026-08-19). Two things must hold for that to be
    an honest drawing: every such act is dated inside the programme axis
    (T0 = 2022-01-01), and none of them post-dates the contract they produced.
    """
    kinds = {"request", "approved_request", "notice", "auction"}
    n_with = late = 0
    for (ref,) in kh.execute(
            "SELECT reference_number FROM contract_scope WHERE in_scope = 1"):
        up = [e for e in qx.contract_timeline(kh, ref)
              if e["kind"] in kinds and e["d"]]
        if not up:
            continue
        n_with += 1
        assert all(e["d"] >= "2022-01-01" for e in up), ref
        sig = kh.execute("SELECT contract_signed_date FROM contracts"
                         " WHERE reference_number = ?", (ref,)).fetchone()[0]
        if sig and min(e["d"] for e in up) > sig[:10]:
            late += 1
    assert late == 0
    assert n_with >= 215      # 217 of 246 dated at the time of writing


def test_a_part_acceptance_is_not_the_whole_jurisdiction(client, kh):
    """26SYMV018978343 names no forest service of its own — it is a
    region-scoped «άμεσης διαχείρισης» contract — so its ONLY authority link
    comes from an acceptance act, and that act accepts «– για το τμήμα του
    έργου … Δίρφυος»: one part, in Εύβοια, of works the curation places
    across seven Attica Π.Ε. The link is kept (the act names it) but marked,
    so the page cannot present one accepted part as the contract's whole
    jurisdiction."""
    rows = kh.execute(
        "SELECT authority_name, source FROM contract_forest_authorities"
        " WHERE reference_number = ?", ("26SYMV018978343",)).fetchall()
    assert [r["authority_name"] for r in rows] == ["Δασαρχείο Χαλκίδας"]
    assert rows[0]["source"].endswith("|part")
    # exactly one such act across the programme — a marked exception, not a rule
    n = kh.execute("SELECT COUNT(*) FROM contract_forest_authorities"
                   " WHERE source LIKE '%|part'").fetchone()[0]
    assert n == 1
    d = client.get("/api/antinero/contract/26SYMV018978343").get_json()
    assert d["authorities"][0]["source"].endswith("|part")


def test_the_trail_dates_each_document_by_itself(client):
    """The DOCUMENT TRAIL lists sibling records of the same chain — each must
    carry ITS date, not the contract's, which ΚΗΜΔΗΣ copies onto all of them.
    On 26SYMV019098206 three records were filed under 22.10.2024."""
    t = client.get("/api/antinero/contract/26SYMV019098206").get_json()["timeline"]
    by_ref = {r["adam"]: r for r in t}
    assert by_ref["24SYMV015643849"]["d"] == "2024-10-22"        # the σύμβαση
    assert by_ref["26SYMV018425922"]["d"] == "2025-07-31"        # its approval
    assert by_ref["26SYMV018426173"]["d"] == "2025-11-12"        # the extension
    assert by_ref["26SYMV018425922"]["d_basis"] == "signature"
    assert len({by_ref[r]["d"] for r in
                ("24SYMV015643849", "26SYMV018425922", "26SYMV018426173")}) == 3


def test_contractor_display_names_are_presented_and_both_names_search(client):
    """The curated display name is what the site prints; the registry spelling
    rides beside it and stays searchable (DATA_DECISIONS 2026-08-20). Searching
    «BIODASOS» has to find the firm the registry calls «ΤΣΙΜΠΩΝΗ ΧΡΥΣΟΥΛΑ ΚΑΙ
    ΣΙΑ Ε.Ε.» — that is the reason the layer exists."""
    rows = client.get("/api/antinero/contractors").get_json()
    assert len(rows) == 151
    assert sum(r["total_eur"] or 0.0 for r in rows) == pytest.approx(
        622_534_181.72, abs=0.01)
    bios = next(r for r in rows if r["vat_number"] == "998342580")
    assert bios["name"] == "ΒΙΟΣ Α.Ε." and bios["registry_name"] != bios["name"]
    # the name it signed four of its contracts under still finds it
    old_name = client.get("/api/antinero/contractors?q=ΚΑΦΕΤΖΗΣ").get_json()
    assert "998342580" in {r["vat_number"] for r in old_name}
    found = client.get("/api/antinero/contractors?q=BIODASOS").get_json()
    assert "801706520" in {r["vat_number"] for r in found}
    also = client.get("/api/antinero/contractors?q=ΤΣΙΜΠΩΝΗ").get_json()
    assert "801706520" in {r["vat_number"] for r in also}
    # a joint venture prints as «Κ/Ξ » plus its members' own display names
    kx = next(r for r in rows if r["vat_number"] == "996609013")
    assert kx["name"] == "Κ/Ξ Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε. – ΜΕΣΟΓΕΙΟΣ Α.Ε."


def test_explore_and_the_contract_page_present_the_display_name(client):
    """Same name on every surface, and the spelling it replaced stays in the
    row's searchable text (`ac`) — `alt` is ΑΔΑΜ only."""
    kh = [r for r in client.get("/api/explore").get_json()["rows"]
          if r["ds"] == "antinero"]
    bios = [r for r in kh if r["co"] == "ΒΙΟΣ Α.Ε."]
    assert len(bios) == 6
    assert any("ΚΑΦΕΤΖΗΣ" in n for r in bios for n in (r.get("ac") or []))
    assert all(re.fullmatch(r"\d\d[A-Z]+\d+", m)
               for r in kh for m in (r.get("alt") or []))
    # 70 of the 245 rows are held by a joint venture
    assert sum(1 for r in kh if r["co"].startswith("Κ/Ξ ")) == 70
    d = client.get("/api/antinero/contract/22SYMV010447496").get_json()
    party = d["contractors"][0]
    assert (party["name"], party["registry_name"]) == (
        "ΒΙΟΣ Α.Ε.", "Δ ΚΑΦΕΤΖΗΣ ΚΑΙ ΣΙΑ ΟΕ")


def test_value_histogram_covers_every_contract_on_doubling_edges(client):
    """The merged dots/brackets CONTRACT VALUES frame (user, 2026-08-20):
    pure-doubling edges anchored on €1.000, every in-scope contract counted,
    and the swarm it toggles with ships the same population with a date."""
    o = client.get("/api/antinero/overview").get_json()
    vh = o["value_histogram"]
    assert sum(vh["counts"]) == o["kpis"]["n_contracts"] == 245
    inner = vh["edges"][1:]
    assert all(b == a * 2 for a, b in zip(inner, inner[1:]))
    assert vh["median"] > 0
    sw = client.get("/api/antinero/swarm").get_json()
    assert len(sw) == 245
    assert all(r["d"] for r in sw)          # the tooltip's signature date
