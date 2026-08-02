"""New SQL/aggregation for the Atlas API.

Everything here composes the frozen webui query modules (`webui.queries`,
`webui.dase_queries`) — those files are never edited; any behaviour of their
private helpers we rely on (`q._payment_month`, `dq._org_key`) is pinned by
the atlas test suite so a future webui refactor fails loudly here.
"""
from __future__ import annotations

import json
import sqlite3
import unicodedata

from khmdhs.greek_regions import canonical_pe
from webui import dase_queries as dq
from webui import queries as q


def _fold_upper(s: str) -> str:
    """Uppercase + strip accents (NFD) for keyword matching on Greek text."""
    nfd = unicodedata.normalize("NFD", s.upper())
    return "".join(ch for ch in nfd if not unicodedata.combining(ch))


def _full_date(s: str | None) -> str | None:
    """Normalise the payment date formats ('03/11/2023', '2026-07-24T00:00:00')
    to 'YYYY-MM-DD'. None when absent/unparsable — mirrors q._payment_month
    (whose behaviour our tests pin) at day precision."""
    if not s:
        return None
    s = s.strip()
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        return f"{s[6:10]}-{s[3:5]}-{s[0:2]}"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return None


# ---------------------------------------------------------------- meta

def meta(kh: sqlite3.Connection, dase: sqlite3.Connection | None,
         ana: sqlite3.Connection | None = None) -> dict:
    """Footer/OG numbers for all datasets + data freshness."""
    k = q.kpis(kh)
    out = {
        "antinero": {
            "n_contracts": k["n_contracts"],
            "total_eur": k["total_eur"],
            "n_payments": kh.execute(
                "SELECT COUNT(*) FROM contract_payments WHERE cancelled = 0"
            ).fetchone()[0] if q._has_payments_table(kh) else 0,
        },
        "generated": kh.execute(
            "SELECT MAX(fetched_at) FROM contracts"
        ).fetchone()[0],
    }
    if dase is not None:
        dk = dq.kpis(dase)
        out["dase"] = {"n_contracts": dk["n_contracts"],
                       "total_eur": dk["total_eur"]}
    if ana is not None:
        n, tot = ana.execute(
            "SELECT COUNT(*), ROUND(SUM(budget_current), 2) FROM projects "
            "WHERE status != 'superseded'").fetchone()
        out["anadohoi"] = {"n_projects": n, "stated_eur": tot}
    return out


# ---------------------------------------------------------------- overview

def antinero_overview(kh: sqlite3.Connection) -> dict:
    """Everything the Anti-nero overview page needs except the map/detail
    payloads (those ship separately — they are heavier and lazier)."""
    studies = q.study_costs(kh)
    top_studies = sorted(studies["rows"], key=lambda r: r["eur"], reverse=True)[:10]
    return {
        "kpis": q.kpis(kh),
        "procedures": q.procedure_mix(kh),
        "histogram": q.contract_value_histogram(kh),
        "direct_awards": q.direct_award_distribution(kh),
        "timeseries": q.disbursement_timeseries(kh),
        "yearly": q.antinero_yearly(kh),
        "studies": {"summary": studies["summary"], "top": top_studies},
        "top_contractors": q.top_contractors(kh, limit=10),
        "top_authorities": q.top_authorities(kh, limit=5),
        "top_signers": q.top_signers(kh, limit=5),
        "coverage": q.flow_coverage(kh),
    }


# ---------------------------------------------------------------- payments

def payment_events(kh: sqlite3.Connection) -> dict:
    """Every non-cancelled payment order attributed to an in-scope contract,
    as individual dated events for the strip timeline.

    Date = signed_date normalised; falls back to submission_date (registry
    submission) — `fallback` counts those; truly undated events carry
    d=None and are summarised in `undated`.
    """
    if not q._has_payments_table(kh) or not q._has_scope_table(kh):
        return {"events": [], "contracts": {}, "undated": {"n": 0, "eur": 0.0},
                "fallback": 0}
    rows = kh.execute("""
        SELECT p.payment_ref, p.attributed_ref, p.signed_date,
               p.submission_date, p.amount_with_vat, p.credit, s.scope
        FROM contract_payments p
        JOIN contract_scope s ON s.reference_number = p.attributed_ref
        WHERE p.cancelled = 0 AND s.in_scope = 1
        ORDER BY p.signed_date
    """).fetchall()
    events, undated_n, undated_eur, fallback = [], 0, 0.0, 0
    refs = set()
    for r in rows:
        d = _full_date(r["signed_date"])
        if d is None:
            d = _full_date(r["submission_date"])
            if d is not None:
                fallback += 1
        if d is None:
            undated_n += 1
            undated_eur += r["amount_with_vat"] or 0.0
        events.append({
            "pay": r["payment_ref"],
            "ref": r["attributed_ref"],
            "d": d,
            "m": d[:7] if d else None,
            "eur": r["amount_with_vat"],
            "scope": r["scope"],
            "credit": r["credit"],
        })
        refs.add(r["attributed_ref"])

    contracts: dict[str, dict] = {}
    if refs:
        marks = ",".join("?" * len(refs))
        for r in kh.execute(
            f"SELECT reference_number, title FROM contracts "
            f"WHERE reference_number IN ({marks})", sorted(refs)):
            t = (r["title"] or r["reference_number"]).strip()
            contracts[r["reference_number"]] = {
                "t": t[:80] + ("…" if len(t) > 80 else "")}
        for r in kh.execute(
            f"SELECT reference_number, vat_number FROM contractors "
            f"WHERE reference_number IN ({marks}) ORDER BY seq", sorted(refs)):
            contracts[r["reference_number"]].setdefault("vats", []).append(
                r["vat_number"])
    return {"events": events, "contracts": contracts,
            "undated": {"n": undated_n, "eur": round(undated_eur, 2)},
            "fallback": fallback}


# ------------------------------------------------------------------ sankey

_PHASE_LABELS = {
    "antinero_i": "Anti-nero I",
    "antinero_ii": "Anti-nero II",
    "antinero_iii": "Anti-nero III",
    "antinero_iv": "Anti-nero IV",
    "antinero_2026": "Anti-nero 2026",
    "antinero_esa": "ΕΣΑ reforestation",
    "antinero_restoration": "Restoration works",
    "antinero_unknown_phase": "Phase unknown",
}
_PHASE_ORDER = list(_PHASE_LABELS)


def sankey_flows(kh: sqlite3.Connection, top_n: int = 10) -> dict:
    """ΥΠΕΝ → programme phase → top-N contractors (+ one 'others' node).

    Effective €, split evenly across consortium partners so every layer of
    the sankey reconciles to the same programme total (unit-tested).
    """
    rows = kh.execute(f"""
        SELECT k.reference_number, {q.effective_cost(kh, 'k')} AS eff,
               s.scope, c.vat_number, c.name
        FROM contracts k
        JOIN contract_scope s ON s.reference_number = k.reference_number
        JOIN contractors c ON c.reference_number = k.reference_number
        WHERE s.in_scope = 1
        ORDER BY k.reference_number, c.seq
    """).fetchall()

    by_contract: dict[str, list] = {}
    for r in rows:
        by_contract.setdefault(r["reference_number"], []).append(r)

    phase_eur: dict[str, float] = {}
    pc_eur: dict[tuple[str, str], float] = {}   # (scope, vat) -> €
    vat_eur: dict[str, float] = {}
    vat_name: dict[str, str] = {}
    vat_n: dict[str, int] = {}
    for partners in by_contract.values():
        eff = partners[0]["eff"] or 0.0
        scope = partners[0]["scope"]
        share = eff / len(partners)
        phase_eur[scope] = phase_eur.get(scope, 0.0) + eff
        for p in partners:
            vat = p["vat_number"]
            pc_eur[(scope, vat)] = pc_eur.get((scope, vat), 0.0) + share
            vat_eur[vat] = vat_eur.get(vat, 0.0) + share
            vat_name.setdefault(vat, p["name"])
            vat_n[vat] = vat_n.get(vat, 0) + 1

    top = sorted(vat_eur, key=lambda v: -vat_eur[v])[:top_n]
    top_set = set(top)
    n_rest = len(vat_eur) - len(top_set)

    nodes = [{"id": "ministry", "label": "ΥΠΕΝ", "kind": "ministry"}]
    links = []
    phases = sorted(phase_eur, key=lambda s: _PHASE_ORDER.index(s)
                    if s in _PHASE_ORDER else 99)
    for scope in phases:
        nodes.append({"id": scope,
                      "label": _PHASE_LABELS.get(scope, scope),
                      "kind": "phase"})
        links.append({"s": "ministry", "t": scope,
                      "eur": round(phase_eur[scope], 2)})
    for vat in top:
        nodes.append({"id": vat, "label": vat_name[vat], "kind": "contractor",
                      "n": vat_n[vat]})
    if n_rest:
        nodes.append({"id": "rest", "label": f"{n_rest} other contractors",
                      "kind": "rest"})
    rest_by_phase: dict[str, float] = {}
    for (scope, vat), eur in pc_eur.items():
        if vat in top_set:
            links.append({"s": scope, "t": vat, "eur": round(eur, 2)})
        else:
            rest_by_phase[scope] = rest_by_phase.get(scope, 0.0) + eur
    for scope, eur in rest_by_phase.items():
        links.append({"s": scope, "t": "rest", "eur": round(eur, 2)})
    return {"nodes": nodes, "links": links}


# ------------------------------------------------------------------- swarm

def _proc_kind(procedure_type: str | None) -> str:
    if not procedure_type:
        return "other"
    p = _fold_upper(procedure_type)
    if "ΑΠΕΥΘΕΙΑΣ" in p:
        return "direct"
    if "ΑΝΟΙ" in p:            # ΑΝΟΙΧΤΗ / ΑΝΟΙΚΤΗ
        return "open"
    if "ΔΙΑΠΡΑΓΜ" in p:
        return "nego"
    return "other"


def contract_swarm(kh: sqlite3.Connection) -> list[dict]:
    """One row per in-scope contract for the beeswarm (252 rows)."""
    rows = kh.execute(f"""
        SELECT k.reference_number, k.title, {q.effective_cost(kh, 'k')} AS eff,
               s.scope, k.contract_signed_date, k.submission_date,
               k.procedure_type, k.bids_submitted,
               (SELECT cpr.region_pe FROM contract_project_regions cpr
                WHERE cpr.reference_number = k.reference_number
                ORDER BY cpr.seq LIMIT 1) AS pe
        FROM contracts k
        JOIN contract_scope s ON s.reference_number = k.reference_number
        WHERE s.in_scope = 1
    """).fetchall()
    out = []
    for r in rows:
        t = (r["title"] or r["reference_number"]).strip()
        d = _full_date(r["contract_signed_date"]) or _full_date(r["submission_date"])
        out.append({
            "ref": r["reference_number"],
            "t": t[:80] + ("…" if len(t) > 80 else ""),
            "eur": r["eff"],
            "scope": r["scope"],
            "year": d[:4] if d else None,
            "proc": _proc_kind(r["procedure_type"]),
            "single_bidder": 1 if r["bids_submitted"] == 1 else 0,
            "pe": canonical_pe(r["pe"]) or r["pe"] if r["pe"] else None,
        })
    return sorted(out, key=lambda r: -(r["eur"] or 0.0))


# ------------------------------------------------------------------- ΔΑΣΕ

def dase_overview(dase: sqlite3.Connection) -> dict:
    """Everything the ΔΑΣΕ overview page needs (webui /dase context)."""
    return {
        "kpis": dq.kpis(dase),
        "yearly": dq.yearly_totals(dase),
        "top_coops": dq.top_coops(dase, limit=10),
        "top_orgs": dq.top_orgs(dase, limit=10),
        "top_units": dq.top_units(dase, limit=10),
        "procedures": dq.procedure_mix(dase),
        "types": dq.type_mix(dase),
        "cpvs": dq.cpv_mix(dase, limit=10),
        "histogram": dq.value_histogram(dase),
        "by_pe": dq.money_by_pe(dase),
    }


def dase_swarm(dase: sqlite3.Connection) -> dict:
    """Column arrays for the canvas beeswarm — one entry per live contract."""
    rows = dase.execute(f"""
        SELECT co.reference_number, co.title, co.total_cost_with_vat,
               co.contract_signed_date, co.submission_date,
               r.region_pe,
               (SELECT c.vat_number FROM contractors c
                WHERE c.reference_number = co.reference_number
                ORDER BY c.seq LIMIT 1) AS vat
        FROM contracts co
        LEFT JOIN dase_contract_regions r USING (reference_number)
        WHERE {dq.live_filter('co')}
    """).fetchall()
    out: dict[str, list] = {"ref": [], "t": [], "eur": [], "year": [],
                            "pe": [], "vat": []}
    for r in rows:
        d = _full_date(r["contract_signed_date"]) or _full_date(r["submission_date"])
        t = (r["title"] or r["reference_number"]).strip()
        out["ref"].append(r["reference_number"])
        out["t"].append(t[:70] + ("…" if len(t) > 70 else ""))
        out["eur"].append(r["total_cost_with_vat"])
        out["year"].append(d[:4] if d else None)
        out["pe"].append(r["region_pe"])
        out["vat"].append(dq.canonical_vat(r["vat"]) if r["vat"] else None)
    return out


# ----------------------------------------------------------------- compare

def pipelines(kh: sqlite3.Connection, dase: sqlite3.Connection) -> dict:
    """The zero-overlap 'two parallel pipelines' payload.

    Contractor VATs are compared canonicalised on both sides; awarders are
    matched by normalised NAME, never VAT (090273987 is shared by two
    bodies and leading zeros get lost).
    """
    kh_rows = kh.execute(f"""
        SELECT c.vat_number, c.name,
               SUM(eff) AS total_eur
        FROM (SELECT k.reference_number,
                     {q.effective_cost(kh, 'k')} /
                     (SELECT COUNT(*) FROM contractors c2
                      WHERE c2.reference_number = k.reference_number) AS eff
              FROM contracts k
              JOIN contract_scope s ON s.reference_number = k.reference_number
              WHERE s.in_scope = 1) t
        JOIN contractors c USING (reference_number)
        GROUP BY c.vat_number
    """).fetchall()
    # kh side keyed by RAW vat — the same 169 entities the rest of the site
    # shows; € even-split across consortium partners so the column sums to
    # the programme total.
    kh_vats: dict[str, dict] = {}
    for r in kh_rows:
        vat = r["vat_number"]
        e = kh_vats.setdefault(vat, {"vat": vat, "name": r["name"], "eur": 0.0})
        e["eur"] += r["total_eur"] or 0.0

    # dase side keyed by canonical VAT, € even-split (top_coops is the
    # max-exposure view and would over-count the 19 consortium rows).
    name_by_canon = {
        dq.canonical_vat(r["vat_number"]) or r["vat_number"]: r["name"]
        for r in dase.execute("SELECT vat_number, name FROM dase_contractors")
    }
    dase_vats: dict[str, dict] = {}
    for r in dase.execute(f"""
        SELECT c.vat_number, c.name,
               co.total_cost_with_vat /
               (SELECT COUNT(*) FROM contractors c2
                WHERE c2.reference_number = co.reference_number) AS eff
        FROM contracts co
        JOIN contractors c USING (reference_number)
        WHERE {dq.live_filter('co')}
    """):
        vat = dq.canonical_vat(r["vat_number"])
        if vat is None:
            continue
        e = dase_vats.setdefault(
            vat, {"vat": vat, "name": name_by_canon.get(vat, r["name"]),
                  "eur": 0.0})
        e["eur"] += r["eff"] or 0.0

    # strictest overlap check: canonicalise BOTH sides before intersecting
    kh_canon = {dq.canonical_vat(v) or v for v in kh_vats}
    overlap = sorted(kh_canon & set(dase_vats))

    # shared awarders by normalised name
    def org_totals(conn, where):
        rows = conn.execute(f"""
            SELECT k.organization_name AS name, COUNT(*) AS n,
                   SUM(k.total_cost_with_vat) AS eur
            FROM contracts k {where}
            GROUP BY k.organization_name
        """).fetchall()
        out: dict[str, dict] = {}
        for r in rows:
            if not r["name"]:
                continue
            key = dq._org_key(r["name"])
            e = out.setdefault(key, {"name": r["name"], "n": 0, "eur": 0.0})
            e["n"] += r["n"]
            e["eur"] += r["eur"] or 0.0
        return out

    kh_orgs = org_totals(
        kh, "JOIN contract_scope s ON s.reference_number = k.reference_number "
            "AND s.in_scope = 1")
    dase_orgs = org_totals(
        dase, f"WHERE {dq.live_filter('k')}")
    shared = []
    for key in sorted(set(kh_orgs) & set(dase_orgs)):
        shared.append({
            "name": kh_orgs[key]["name"],
            "antinero_n": kh_orgs[key]["n"],
            "antinero_eur": round(kh_orgs[key]["eur"], 2),
            "dase_n": dase_orgs[key]["n"],
            "dase_eur": round(dase_orgs[key]["eur"], 2),
        })
    shared.sort(key=lambda s: -(s["antinero_eur"] + s["dase_eur"]))

    def side(entries):
        es = sorted(entries.values(), key=lambda e: -e["eur"])
        return {"n_vats": len(es),
                "total_eur": round(sum(e["eur"] for e in es), 2),
                "entities": [{"vat": e["vat"], "name": e["name"],
                              "eur": round(e["eur"], 2)} for e in es]}

    return {"antinero": side(kh_vats), "dase": side(dase_vats),
            "dase_n_coops": len(set(dase_vats) & set(name_by_canon)),
            "vat_overlap": overlap, "shared_awarders": shared}


# -------------------------------------------------------------- connections

def network_payload(kh: sqlite3.Connection) -> dict:
    """Every relationship layer for the /connections page in one JSON.

    Edge € use the even-split convention (contract effective € divided
    across its partners and its authorities/regions) so each layer's edges
    sum back to the resolved programme total.
    """
    contracts: dict[str, dict] = {}
    for r in kh.execute(f"""
        SELECT k.reference_number AS ref, {q.effective_cost(kh, 'k')} AS eff,
               k.signer_name
        FROM contracts k
        JOIN contract_scope s ON s.reference_number = k.reference_number
        WHERE s.in_scope = 1
    """):
        contracts[r["ref"]] = {"eff": r["eff"] or 0.0,
                               "signer": r["signer_name"],
                               "vats": [], "auths": [], "pes": []}
    for r in kh.execute("SELECT reference_number, vat_number, name "
                        "FROM contractors ORDER BY seq"):
        if r["reference_number"] in contracts:
            contracts[r["reference_number"]]["vats"].append(
                (r["vat_number"], r["name"]))
    for r in kh.execute("SELECT reference_number, authority_name "
                        "FROM contract_forest_authorities ORDER BY seq"):
        if r["reference_number"] in contracts:
            contracts[r["reference_number"]]["auths"].append(r["authority_name"])
    for r in kh.execute("SELECT reference_number, region_pe "
                        "FROM contract_project_regions ORDER BY seq"):
        if r["reference_number"] in contracts:
            pe = canonical_pe(r["region_pe"]) or r["region_pe"]
            contracts[r["reference_number"]]["pes"].append(pe)

    ca: dict[tuple, dict] = {}
    cp: dict[tuple, dict] = {}
    cs: dict[tuple, dict] = {}
    pairs: dict[tuple, dict] = {}
    names: dict[str, str] = {}
    totals: dict[str, float] = {}
    for ref, c in contracts.items():
        nv = max(len(c["vats"]), 1)
        for vat, name in c["vats"]:
            cur = names.get(vat)
            if cur is None or len(name) > len(cur):
                names[vat] = name
            totals[vat] = totals.get(vat, 0.0) + c["eff"] / nv
            for auth in c["auths"]:
                e = ca.setdefault((vat, auth), {"vat": vat, "auth": auth,
                                                "n": 0, "eur": 0.0})
                e["n"] += 1
                e["eur"] += c["eff"] / (nv * len(c["auths"]))
            for pe in c["pes"]:
                e = cp.setdefault((vat, pe), {"vat": vat, "pe": pe,
                                              "n": 0, "eur": 0.0})
                e["n"] += 1
                e["eur"] += c["eff"] / (nv * len(c["pes"]))
            if c["signer"]:
                e = cs.setdefault((vat, c["signer"]),
                                  {"vat": vat, "signer": c["signer"],
                                   "n": 0, "eur": 0.0})
                e["n"] += 1
                e["eur"] += c["eff"] / nv
        vats = sorted({v for v, _ in c["vats"]})
        for i in range(len(vats)):
            for j in range(i + 1, len(vats)):
                p = pairs.setdefault((vats[i], vats[j]),
                                     {"a": vats[i], "b": vats[j],
                                      "refs": [], "eur": 0.0})
                p["refs"].append(ref)
                p["eur"] += c["eff"]

    def rnd(edges):
        out = sorted(edges.values(), key=lambda e: -e["eur"])
        for e in out:
            e["eur"] = round(e["eur"], 2)
        return out

    homes = {r["vat_number"]: r["region_pe"] for r in kh.execute(
        "SELECT vat_number, region_pe FROM contractor_locations")}
    authorities = {r["name"]: {"pe": r["region_pe"], "kind": r["kind"],
                               "lat": r["lat"], "lon": r["lon"]}
                   for r in kh.execute(
                       "SELECT name, kind, region_pe, lat, lon "
                       "FROM forest_authorities")}
    return {
        "contractor_authority": rnd(ca),
        "contractor_pe": rnd(cp),
        "contractor_signer": rnd(cs),
        "flows": q.region_flows(kh),
        "origins": q.project_region_origins(kh),
        "pairs": rnd(pairs),
        "contractors": {vat: {"name": names[vat],
                              "home_pe": homes.get(vat),
                              "eur": round(totals[vat], 2)}
                        for vat in names},
        "authorities": authorities,
        "coverage": q.flow_coverage(kh),
    }


# -------------------------------------------------------------- authorities

_REGISTRY_CACHE: dict | None = None


def _registry():
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        from khmdhs.dase_region_loader import build_alias_map, split_unit
        from khmdhs.forest_loader import load_registry
        registry, _ = load_registry()
        _REGISTRY_CACHE = {
            "alias_map": build_alias_map(registry),
            "split_unit": split_unit,
        }
    return _REGISTRY_CACHE


def slugify_authority(name: str) -> str:
    """URL slug for an authority name: lowercase, spaces/punct → dashes.
    Pure function of the name (no counters) — bijectivity over the registry
    is asserted in tests."""
    import re
    s = name.lower().replace("/", " ")
    s = re.sub(r"[^\w]+", "-", s, flags=re.UNICODE).strip("-")
    return s


def _dase_by_authority(dase: sqlite3.Connection) -> dict[str, list]:
    """Live ΔΑΣΕ contracts grouped by matched forest authority (folded
    unit-name → registry alias, same matcher as dase_region_loader)."""
    reg = _registry()
    out: dict[str, list] = {}
    for r in dase.execute(f"""
        SELECT co.reference_number, co.title, co.contract_signed_date,
               co.units_operator_name, co.total_cost_with_vat,
               (SELECT c.vat_number FROM contractors c
                WHERE c.reference_number = co.reference_number
                ORDER BY c.seq LIMIT 1) AS vat,
               (SELECT c.name FROM contractors c
                WHERE c.reference_number = co.reference_number
                ORDER BY c.seq LIMIT 1) AS contractor_name
        FROM contracts co
        WHERE {dq.live_filter('co')} AND co.units_operator_name IS NOT NULL
    """):
        kind, tail = reg["split_unit"](r["units_operator_name"])
        if kind is None:
            continue
        hit = reg["alias_map"].get((kind, tail))
        if hit is None:
            continue
        out.setdefault(hit[0], []).append(dict(r))
    return out


def authorities_index(kh: sqlite3.Connection,
                      dase: sqlite3.Connection | None) -> list[dict]:
    """All 103 forest authorities with both datasets' presence."""
    rows = {r["name"]: {
        "name": r["name"], "slug": slugify_authority(r["name"]),
        "kind": r["kind"], "pe": r["region_pe"],
        "lat": r["lat"], "lon": r["lon"], "seat": r["municipality_name"],
        "antinero_n": 0, "antinero_eur": 0.0,
        "dase_n": 0, "dase_eur": 0.0,
    } for r in kh.execute("SELECT * FROM forest_authorities")}

    for r in kh.execute(f"""
        SELECT cfa.authority_name AS name, COUNT(*) AS n, SUM(t.share) AS eur
        FROM contract_forest_authorities cfa
        JOIN (SELECT k.reference_number,
                     {q.effective_cost(kh, 'k')} * 1.0 /
                     (SELECT COUNT(*) FROM contract_forest_authorities x
                      WHERE x.reference_number = k.reference_number) AS share
              FROM contracts k
              JOIN contract_scope s ON s.reference_number = k.reference_number
              WHERE s.in_scope = 1) t USING (reference_number)
        GROUP BY cfa.authority_name
    """):
        if r["name"] in rows:
            rows[r["name"]]["antinero_n"] = r["n"]
            rows[r["name"]]["antinero_eur"] = round(r["eur"] or 0.0, 2)

    if dase is not None:
        for name, contracts in _dase_by_authority(dase).items():
            if name in rows:
                rows[name]["dase_n"] = len(contracts)
                rows[name]["dase_eur"] = round(
                    sum(c["total_cost_with_vat"] or 0 for c in contracts), 2)

    return sorted(rows.values(),
                  key=lambda r: -(r["antinero_eur"] + r["dase_eur"]))


def authority_profile(kh: sqlite3.Connection, dase: sqlite3.Connection | None,
                      slug: str) -> dict | None:
    """Cross-dataset profile: the authority as Anti-nero works executor AND
    as ΔΑΣΕ awarding unit."""
    row = next((r for r in kh.execute("SELECT * FROM forest_authorities")
                if slugify_authority(r["name"]) == slug), None)
    if row is None:
        return None
    name = row["name"]

    anti_contracts = [dict(r) for r in kh.execute(f"""
        SELECT k.reference_number, k.title, k.contract_signed_date,
               {q.effective_cost(kh, 'k')} AS eff,
               (SELECT COUNT(*) FROM contract_forest_authorities x
                WHERE x.reference_number = k.reference_number) AS n_auths,
               (SELECT GROUP_CONCAT(c.name, ' · ') FROM contractors c
                WHERE c.reference_number = k.reference_number) AS contractors,
               (SELECT c.vat_number FROM contractors c
                WHERE c.reference_number = k.reference_number
                ORDER BY c.seq LIMIT 1) AS vat
        FROM contract_forest_authorities cfa
        JOIN contracts k USING (reference_number)
        JOIN contract_scope s ON s.reference_number = k.reference_number
        WHERE cfa.authority_name = ? AND s.in_scope = 1
        ORDER BY eff DESC
    """, (name,))]
    anti_top: dict[str, dict] = {}
    for c in anti_contracts:
        e = anti_top.setdefault(c["vat"], {"vat": c["vat"],
                                           "name": (c["contractors"] or "").split(" · ")[0],
                                           "n": 0, "eur": 0.0})
        e["n"] += 1
        e["eur"] += (c["eff"] or 0.0) / (c["n_auths"] or 1)

    dase_contracts: list[dict] = []
    dase_top: dict[str, dict] = {}
    if dase is not None:
        dase_contracts = sorted(_dase_by_authority(dase).get(name, []),
                                key=lambda c: -(c["total_cost_with_vat"] or 0))
        curated = {dq.canonical_vat(r["vat_number"]) or r["vat_number"]: r["name"]
                   for r in dase.execute(
                       "SELECT vat_number, name FROM dase_contractors")}
        for c in dase_contracts:
            vat = dq.canonical_vat(c["vat"]) if c["vat"] else None
            if vat is None:
                continue
            e = dase_top.setdefault(vat, {
                "vat": vat, "name": curated.get(vat, c["contractor_name"]),
                "n": 0, "eur": 0.0})
            e["n"] += 1
            e["eur"] += c["total_cost_with_vat"] or 0.0

    def top(d):
        out = sorted(d.values(), key=lambda e: -e["eur"])[:8]
        for e in out:
            e["eur"] = round(e["eur"], 2)
        return out

    return {
        "name": name, "slug": slug, "kind": row["kind"],
        "pe": row["region_pe"],
        "seat": {"city": row["municipality_name"],
                 "lat": row["lat"], "lon": row["lon"]},
        "antinero": {
            "contracts": anti_contracts,
            "total_eur": round(sum((c["eff"] or 0) / (c["n_auths"] or 1)
                                   for c in anti_contracts), 2),
            "exposure_eur": round(sum(c["eff"] or 0 for c in anti_contracts), 2),
            "top_contractors": top(anti_top),
        },
        "dase": {
            "contracts": dase_contracts,
            "total_eur": round(sum(c["total_cost_with_vat"] or 0
                                   for c in dase_contracts), 2),
            "top_coops": top(dase_top),
            "match_basis": "folded unit-name → registry alias",
        },
    }


# --------------------------------------------------------------- pe-yearly

def money_by_pe_yearly(kh: sqlite3.Connection) -> dict:
    """Per work Π.Ε. per year: effective € (payments by payment year when
    present, else stated value at signature year), split evenly across the
    contract's region rows — the money_by_project_region convention with a
    time axis. Contracts without curated regions are excluded (their € is
    the `unresolved_eur` remainder)."""
    regions: dict[str, list[str]] = {}
    for r in kh.execute(f"""
        SELECT cpr.reference_number, cpr.region_pe
        FROM contract_project_regions cpr
        JOIN contract_scope s ON s.reference_number = cpr.reference_number
        WHERE s.in_scope = 1 ORDER BY cpr.seq
    """):
        pe = canonical_pe(r["region_pe"]) or r["region_pe"]
        regions.setdefault(r["reference_number"], []).append(pe)

    agg: dict[str, dict[str, float]] = {}
    years: set[str] = set()
    unresolved = 0.0

    def add(ref: str, year: str | None, eur: float) -> None:
        nonlocal unresolved
        pes = regions.get(ref)
        if not pes or not year:
            unresolved += eur
            return
        years.add(year)
        for pe in pes:
            agg.setdefault(pe, {})
            agg[pe][year] = agg[pe].get(year, 0.0) + eur / len(pes)

    has_payments: set[str] = set()
    if q._has_payments_table(kh):
        for r in kh.execute("""
            SELECT p.attributed_ref, p.signed_date, p.submission_date,
                   p.amount_with_vat
            FROM contract_payments p
            JOIN contract_scope s ON s.reference_number = p.attributed_ref
            WHERE p.cancelled = 0 AND s.in_scope = 1
        """):
            has_payments.add(r["attributed_ref"])
            year = q._year_of(r["signed_date"], r["submission_date"])
            add(r["attributed_ref"], year, r["amount_with_vat"] or 0.0)
    for r in kh.execute("""
        SELECT k.reference_number, k.total_cost_with_vat,
               k.contract_signed_date, k.submission_date
        FROM contracts k
        JOIN contract_scope s ON s.reference_number = k.reference_number
        WHERE s.in_scope = 1
    """):
        if r["reference_number"] in has_payments:
            continue
        year = q._year_of(r["contract_signed_date"], r["submission_date"])
        add(r["reference_number"], year, r["total_cost_with_vat"] or 0.0)

    pes = [{"pe": pe,
            "total_eur": round(sum(by_year.values()), 2),
            "years": {y: round(v, 2) for y, v in sorted(by_year.items())}}
           for pe, by_year in agg.items()]
    pes.sort(key=lambda p: -p["total_eur"])
    return {"pes": pes, "years": sorted(years),
            "unresolved_eur": round(unresolved, 2)}


# ------------------------------------------------- explore (all 3 datasets)

def explore_rows(kh: sqlite3.Connection, dase: sqlite3.Connection | None,
                 ana: sqlite3.Connection | None) -> dict:
    """One compact row per contract/project across the three datasets, for
    the client-side /explore finder. Value bases differ by dataset and are
    labelled on the page: Anti-nero = effective €, ΔΑΣΕ = stated € (live
    population), Ανάδοχοι = stated budget after amendments (nullable —
    sponsors often commit without a figure). Missing DBs degrade honestly
    (their rows are simply absent)."""
    rows: list[dict] = []

    hq_map: dict[str, str] = {}
    for r in kh.execute("SELECT vat_number, region_pe FROM contractor_locations"
                        " WHERE region_pe IS NOT NULL"):
        hq_map[r["vat_number"]] = canonical_pe(r["region_pe"]) or r["region_pe"]

    eff = q.effective_cost(kh, "c")
    for r in kh.execute(f"""
        SELECT c.reference_number AS ref, c.title,
               c.contract_signed_date, c.submission_date,
               c.procedure_type, c.bids_submitted, c.cancelled,
               {eff} AS value, c.total_cost_without_vat AS value_net,
               (SELECT GROUP_CONCAT(r.region_pe, '|')
                  FROM contract_project_regions r
                 WHERE r.reference_number = c.reference_number) AS pes,
               (SELECT GROUP_CONCAT(ct.name, ' | ')
                  FROM contractors ct
                 WHERE ct.reference_number = c.reference_number) AS names,
               (SELECT GROUP_CONCAT(ct.vat_number, '|')
                  FROM contractors ct
                 WHERE ct.reference_number = c.reference_number) AS vats
          FROM contracts c
         WHERE {q.scope_filter(kh, 'c.reference_number')}"""):
        pes = sorted({canonical_pe(p) or p
                      for p in (r["pes"] or "").split("|") if p})
        hqs = sorted({hq_map[v] for v in (r["vats"] or "").split("|")
                      if v in hq_map})
        rows.append({
            "ds": "antinero", "ref": r["ref"],
            "d": _full_date(r["contract_signed_date"])
                 or _full_date(r["submission_date"]),
            "t": (r["title"] or "")[:120],
            "co": (r["names"] or "")[:110],
            "v": round(r["value"], 2) if r["value"] is not None else None,
            "vn": round(r["value_net"], 2) if r["value_net"] is not None
                 else None,
            "pe": pes, "hq": hqs,
            "proc": _proc_kind(r["procedure_type"]),
            "st": "cancelled" if r["cancelled"] else None,
            "b1": 1 if r["bids_submitted"] == 1 else 0,
        })

    if dase is not None:
        for r in dase.execute(f"""
            SELECT co.reference_number AS ref, co.title,
                   co.contract_signed_date, co.submission_date,
                   co.procedure_type, co.total_cost_with_vat AS value,
                   co.total_cost_without_vat AS value_net,
                   (SELECT GROUP_CONCAT(r.region_pe, '|')
                      FROM dase_contract_regions r
                     WHERE r.reference_number = co.reference_number) AS pes,
                   (SELECT GROUP_CONCAT(ct.name, ' | ')
                      FROM contractors ct
                     WHERE ct.reference_number = co.reference_number) AS names
              FROM contracts co
             WHERE {dq.live_filter()}"""):
            pes = sorted({canonical_pe(p) or p
                          for p in (r["pes"] or "").split("|") if p})
            rows.append({
                "ds": "dase", "ref": r["ref"],
                "d": _full_date(r["contract_signed_date"])
                     or _full_date(r["submission_date"]),
                "t": (r["title"] or "")[:120],
                "co": (r["names"] or "")[:110],
                "v": round(r["value"], 2) if r["value"] is not None else None,
                "vn": round(r["value_net"], 2) if r["value_net"] is not None
                     else None,
                "pe": pes, "hq": [],
                "proc": _proc_kind(r["procedure_type"]),
                "st": None, "b1": 0,
            })

    if ana is not None:
        for r in ana.execute("""
            SELECT root_ada, company, works_kind, location_text, pe,
                   budget_current, start_date, status FROM projects"""):
            rows.append({
                "ds": "anadohoi", "ref": r["root_ada"],
                "d": r["start_date"],
                "t": (r["location_text"] or "")[:120],
                "co": (r["company"] or "")[:110],
                "v": r["budget_current"],
                "vn": None,     # sponsor acts state one figure, mixed VAT basis
                "pe": [r["pe"]] if r["pe"] else [], "hq": [],
                "proc": "sponsor",
                "st": r["status"], "b1": 0,
            })

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["ds"]] = counts.get(row["ds"], 0) + 1
    return {"rows": rows, "counts": counts}


# ------------------------------------------------------- anadohoi dataset

# Presentation-only grouping of a sponsor's registry spellings across acts
# («ΔΕΗ» / «ΔΕΗ Α.Ε.», «Ελληνικά Πετρέλαια» / «HELLENIQ ENERGY» after the
# 2022 rename, «ΕRΕΝ ΕΛΛΑΣ» / «Εren Groupe»). The per-project rows keep the
# exact name from each act; only the sponsor ranking merges.
_SPONSOR_GROUPS = (
    (("DEH", "ΔΕΗ"), "ΔΕΗ"),
    (("HELLENIQ", "ΕΛΛΗΝΙΚΑ ΠΕΤΡΕΛΑΙΑ"), "Ελληνικά Πετρέλαια / HELLENiQ ENERGY"),
    (("EREN",), "EREN Ελλάς / Eren Groupe"),
    (("COCA COLA",), "Coca-Cola 3Ε Ελλάδος"),
    (("NOVA",), "NOVA Telecommunications & Media"),
    (("ALFA WOOD", "ALPHA WOOD"), "ALFA WOOD GROUP"),
    (("ΤΣΙΜΕΝΤΩΝ ΤΙΤΑΝ", "TΣΙΜΕΝΤΩΝ ΤΙΤΑΝ"), "Α.Ε. Τσιμέντων ΤΙΤΑΝ"),
    (("ΣΥΜΠΡΑΞ", "SYMPRAXIS"), "Ομάδα Σύμπραξις (Παπαστράτος)"),
    (("ΔΕΔΔΗΕ", "ΔΙΑΧΕΙΡΙΣΤΗ ΕΛΛΗΝΙΚΟΥ ΔΙΚΤΥΟΥ", "DEDDHE"), "ΔΕΔΔΗΕ"),
    (("ΑΝΕΞΑΡΤΗΤΟΣ ΔΙΑΧΕΙΡΙΣΤΗΣ ΜΕΤΑΦΟΡΑΣ",
      "ΑΝΕΞΑΡΤΗΤΟΣ ΔΙΑΧΕΙΡΙΣΤΗΣ", "ΑΔΜΗΕ"), "ΑΔΜΗΕ"),
    (("NORDIA",), "Nordia A.E."),
)

# Greek capitals → visually identical Latin, so mixed-script registry
# spellings («ΕRΕΝ», «ΝΟVA») land in one space before stem matching. Both
# the haystack AND the stems go through the same fold.
_HOMOGLYPHS = str.maketrans("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX")


def _sponsor_fold(s: str) -> str:
    return _fold_upper(s or "").translate(_HOMOGLYPHS)


def _sponsor_group(company: str) -> str:
    f = _sponsor_fold(company)
    for stems, label in _SPONSOR_GROUPS:
        if any(_sponsor_fold(stem) in f for stem in stems):
            return label
    return company


def anadohoi_overview(ana: sqlite3.Connection) -> dict:
    """Everything the /anadohoi analysis page needs (69 projects — small
    enough to ship whole)."""
    projects = []
    for r in ana.execute("""
        SELECT p.*,
               (SELECT GROUP_CONCAT(d.issue_date || '~' || pd.ada, '|')
                  FROM project_decisions pd
                  JOIN decisions d ON d.ada = pd.ada
                 WHERE pd.root_ada = p.root_ada AND pd.relation = 'amendment'
                 ORDER BY d.issue_date) AS amendment_dates
          FROM projects p ORDER BY p.start_date"""):
        amendments = []
        for tok in (r["amendment_dates"] or "").split("|"):
            if "~" in tok:
                dte, ada = tok.split("~", 1)
                amendments.append({"ada": ada, "date": dte or None})
        projects.append({
            "ada": r["root_ada"], "company": r["company"],
            "funder": r["funder"], "works_kind": r["works_kind"],
            "area": r["area_stremmata"], "pe": r["pe"],
            "fire": r["fire_event"], "budget": r["budget_current"],
            "budget_stated": r["budget_eur"],
            "start": r["start_date"],
            "deadline0": r["deadline_initial"],
            "deadline": r["deadline_current"],
            "dtext": r["deadline_text"],
            "completed": r["completed_date"], "revoked": r["revoked_date"],
            "status": r["status"], "amendments": amendments,
            "superseded_by": r["superseded_by"],
            "location": r["location_text"],
        })

    live = [p for p in projects if p["status"] != "superseded"]
    statuses: dict[str, int] = {}
    for p in projects:
        statuses[p["status"]] = statuses.get(p["status"], 0) + 1
    monthly: dict[str, int] = {}
    for p in live:
        if p["start"]:
            m = p["start"][:7]
            monthly[m] = monthly.get(m, 0) + 1

    fires: dict[str, dict] = {}
    for p in live:
        f = fires.setdefault(p["fire"] or "—", {
            "fire": p["fire"] or "—", "n": 0, "completed": 0,
            "budget": 0.0, "first_start": p["start"]})
        f["n"] += 1
        f["completed"] += p["status"] == "completed"
        f["budget"] += p["budget"] or 0
        if p["start"] and (f["first_start"] or "9") > p["start"]:
            f["first_start"] = p["start"]

    sponsors: dict[str, dict] = {}
    for p in live:
        key = _sponsor_group(p["company"])
        s = sponsors.setdefault(key, {
            "company": key, "n": 0, "budget": 0.0, "unstated": 0})
        s["n"] += 1
        if p["budget"] is None:
            s["unstated"] += 1
        else:
            s["budget"] += p["budget"]

    status_as_of = ana.execute(
        "SELECT value FROM meta WHERE key = 'status_as_of'").fetchone()
    return {
        "kpis": {
            "n_projects": len(live),
            "n_companies": len({p["company"] for p in live}),
            "stated_eur": round(sum(p["budget"] or 0 for p in live), 2),
            "n_stated": sum(1 for p in live if p["budget"] is not None),
            "area_stremmata": round(sum(p["area"] or 0 for p in live), 1),
            "statuses": statuses,
            "status_as_of": status_as_of[0] if status_as_of else None,
        },
        "projects": projects,
        "fires": sorted(fires.values(), key=lambda f: f["first_start"] or ""),
        "sponsors": sorted(sponsors.values(), key=lambda s: -s["budget"]),
        "monthly": [{"m": m, "n": n} for m, n in sorted(monthly.items())],
    }


def anadohoi_project(ana: sqlite3.Connection, ada: str) -> dict | None:
    """Full detail for one sponsor project, or None."""
    r = ana.execute("SELECT * FROM projects WHERE root_ada = ?",
                    (ada,)).fetchone()
    if r is None:
        return None
    out = dict(r)
    try:
        out["evidence"] = json.loads(out.pop("evidence_json") or "{}")
    except ValueError:
        out["evidence"] = {}
    out["decisions"] = [dict(d) for d in ana.execute("""
        SELECT pd.relation, pd.detail, pd.excerpt,
               d.ada, d.kind, d.issue_date, d.subject, d.org, d.protocol
          FROM project_decisions pd
          JOIN decisions d ON d.ada = pd.ada
         WHERE pd.root_ada = ?
         ORDER BY d.issue_date, d.ada""", (ada,))]
    return out
