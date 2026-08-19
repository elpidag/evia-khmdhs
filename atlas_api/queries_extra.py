"""New SQL/aggregation for the Atlas API.

Everything here composes the frozen webui query modules (`webui.queries`,
`webui.dase_queries`) — those files are never edited; any behaviour of their
private helpers we rely on (`q._payment_month`, `dq._org_key`,
`q._bin_values`) is pinned by the atlas test suite so a future webui
refactor fails loudly here.
"""
from __future__ import annotations

import json
import math
import re
import datetime as _dt
import sqlite3
import unicodedata

from khmdhs.config import PDF_CACHE_DIR
from khmdhs.greek_regions import PE_CENTROIDS, canonical_pe
from webui import dase_queries as dq
from webui import queries as q


def _fold_upper(s: str) -> str:
    """Uppercase + strip accents (NFD) for keyword matching on Greek text."""
    nfd = unicodedata.normalize("NFD", s.upper())
    return "".join(ch for ch in nfd if not unicodedata.combining(ch))


_UNIT_EN_CACHE: dict | None = None
_AUTH_EN_CACHE: dict | None = None


def _names_en_file(fname: str) -> dict:
    """Folded Greek key → curated English name from a khmdhs/data file."""
    import json as _json
    from pathlib import Path as _Path
    p = _Path(__file__).resolve().parent.parent / "khmdhs" / "data" / fname
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {" ".join(_fold_upper(k).split()): v["en"]
            for k, v in data.items() if not k.startswith("_")}


def _auth_en_map() -> dict:
    """Folded registry authority name → curated English name."""
    global _AUTH_EN_CACHE
    if _AUTH_EN_CACHE is None:
        _AUTH_EN_CACHE = _names_en_file("authority_names_en.json")
    return _AUTH_EN_CACHE


def _unit_en_map() -> dict:
    """Folded unit spelling → curated English identity
    (khmdhs/data/unit_names_en.json) — lets the dase map collapse
    spelling variants of the same seatless unit onto one circle."""
    global _UNIT_EN_CACHE
    if _UNIT_EN_CACHE is None:
        _UNIT_EN_CACHE = _names_en_file("unit_names_en.json")
    return _UNIT_EN_CACHE


# ------------------------------------------------------- net-of-ΦΠΑ basis

def apply_net_basis(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Install the Atlas net-of-ΦΠΑ presentation basis on THIS connection.

    SQLite resolves unqualified table names through the temp schema first,
    so the TEMP views below shadow `contracts` and `contract_payments` with
    the registry's NET column exposed under the gross column's name. Every
    downstream query — including the frozen webui modules — therefore
    computes excl-VAT € without a single call-site change (DATA_DECISIONS
    2026-08-03: the ν.4412 εκτιμώμενη αξία is defined χωρίς ΦΠΑ). The true
    gross stays reachable as `total_cost_gross` / `amount_gross` on the
    views, or by qualifying `main.contracts` (see `contract_gross`).

    webui's own app opens its connections without this shim and keeps its
    historical incl-VAT basis; only atlas_api connections pass through here.
    """
    def cols(table: str) -> list[str]:
        return [r[1] for r in conn.execute(f"PRAGMA main.table_info({table})")]

    c = cols("contracts")
    if c and "total_cost_without_vat" in c:
        sel = ["total_cost_without_vat AS total_cost_with_vat"
               if x == "total_cost_with_vat" else x for x in c]
        sel.append("total_cost_with_vat AS total_cost_gross")
        conn.execute("CREATE TEMP VIEW IF NOT EXISTS contracts AS SELECT "
                     + ", ".join(sel) + " FROM main.contracts")
    p = cols("contract_payments")
    if p and "amount_without_vat" in p:
        sel = ["amount_without_vat AS amount_with_vat"
               if x == "amount_with_vat" else x for x in p]
        sel.append("amount_with_vat AS amount_gross")
        conn.execute("CREATE TEMP VIEW IF NOT EXISTS contract_payments AS "
                     "SELECT " + ", ".join(sel) + " FROM main.contract_payments")
    return conn


def apply_stated_basis(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Net views + an EMPTY `contract_payments` TEMP view: every frozen
    `effective_cost()` call site COALESCEs to the stated column, so all
    contract-value analytics compute STATED € (net) with zero call-site
    changes (DATA_DECISIONS 2026-08-03 stated-basis decision). Endpoints
    that present the payments layer (strip timeline, disbursement curves,
    paid KPIs, per-contract payment lists) must use a connection that went
    through `apply_net_basis` only — see `_pay_conn` in app.py."""
    apply_net_basis(conn)
    cols = [r[1] for r in conn.execute(
        "PRAGMA main.table_info(contract_payments)")]
    if cols and "amount_without_vat" in cols:
        conn.execute("DROP VIEW IF EXISTS temp.contract_payments")
        sel = ["amount_without_vat AS amount_with_vat"
               if x == "amount_with_vat" else x for x in cols]
        sel.append("amount_with_vat AS amount_gross")
        conn.execute("CREATE TEMP VIEW contract_payments AS SELECT "
                     + ", ".join(sel) + " FROM main.contract_payments WHERE 0")
    return conn


def contract_gross(conn: sqlite3.Connection, ref: str) -> dict:
    """The registry's incl-VAT figures for one contract — the secondary
    line on detail pages (the net-basis views hide them elsewhere)."""
    row = conn.execute(
        "SELECT total_cost_with_vat AS stated, total_cost_without_vat AS net"
        " FROM main.contracts WHERE reference_number = ?", (ref,)).fetchone()
    if row is None:
        return {}
    out = {"stated_gross": row["stated"]}
    try:
        paid = conn.execute(
            "SELECT ROUND(SUM(amount_with_vat), 2), COUNT(*) "
            "FROM main.contract_payments "
            "WHERE attributed_ref = ? AND cancelled = 0", (ref,)).fetchone()
        out["paid_gross"] = paid[0]
        pays = {r[0]: r[1] for r in conn.execute(
            "SELECT payment_ref, amount_with_vat FROM main.contract_payments "
            "WHERE contract_ref = ? OR attributed_ref = ?", (ref, ref))}
        if pays:
            out["payments"] = pays
    except sqlite3.OperationalError:
        pass
    return out


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
         ana: sqlite3.Connection | None = None,
         pay: sqlite3.Connection | None = None,
         ar: sqlite3.Connection | None = None) -> dict:
    """Footer/OG numbers for all datasets + data freshness. `kh` is the
    stated-basis connection (total = Σ stated net); `pay` sees real
    payments for the n_payments count."""
    k = q.kpis(kh)
    pconn = pay if pay is not None else kh
    out = {
        "antinero": {
            "n_contracts": k["n_contracts"],
            "total_eur": k["total_eur"],
            "n_payments": pconn.execute(
                "SELECT COUNT(*) FROM contract_payments WHERE cancelled = 0"
            ).fetchone()[0] if q._has_payments_table(pconn) else 0,
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
        # committed € prefer the act's own net figure where one is stated
        # (budget_vat_basis curation); silent acts stay as written.
        n, tot = ana.execute(
            "SELECT COUNT(*), ROUND(SUM(COALESCE(budget_net_eur, "
            "budget_current)), 2) FROM projects "
            "WHERE status != 'superseded'").fetchone()
        out["anadohoi"] = {"n_projects": n, "stated_eur": tot}

    if ar is not None:
        n_fires, n_cases, appr = ar.execute(
            "SELECT (SELECT COUNT(*) FROM fires WHERE in_scope = 1),"
            " COUNT(*), ROUND(SUM(approved_eur), 2) FROM cases").fetchone()
        out["arogi"] = {"n_fires": n_fires, "n_cases": n_cases,
                        "approved_eur": appr}

    # dataset-state counts the prose pages (methodology) cite — computed,
    # never hardcoded, so a refresh cannot leave stale numbers in copy
    facts: dict[str, int | float] = {}
    try:
        facts["kh_probable_n"], facts["kh_probable_eur"] = kh.execute("""
            SELECT COUNT(*), ROUND(SUM(k.total_cost_with_vat), 2)
            FROM contracts k
            JOIN contract_scope s ON s.reference_number = k.reference_number
            WHERE s.scope = 'antinero_probable'
              AND s.superseded_by IS NULL""").fetchone()
    except sqlite3.OperationalError:
        pass
    try:
        facts["kh_done"] = kh.execute(f"""
            SELECT COUNT(DISTINCT a.attributed_ref)
            FROM contract_completion_acts a
            JOIN contract_scope s ON s.reference_number = a.attributed_ref
            WHERE s.in_scope = 1""").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    try:
        facts["kh_notice"] = kh.execute(f"""
            SELECT COUNT(DISTINCT cla.reference_number)
            FROM contract_linked_acts cla
            JOIN contract_scope s ON s.reference_number = cla.reference_number
            WHERE cla.kind = 'notice' AND s.in_scope = 1""").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    if dase is not None:
        try:
            facts["dase_notice"] = dase.execute(f"""
                SELECT COUNT(DISTINCT cla.reference_number)
                FROM contract_linked_acts cla
                JOIN contracts co ON co.reference_number = cla.reference_number
                WHERE cla.kind = 'notice' AND {dq.live_filter('co')}
            """).fetchone()[0]
        except sqlite3.OperationalError:
            pass
        try:
            facts["dase_cpv_noise"] = dase.execute(f"""
                SELECT COUNT(DISTINCT c.reference_number)
                FROM contract_cpvs c
                JOIN contracts co ON co.reference_number = c.reference_number
                WHERE c.cpv_code = '66519300-4' AND {dq.live_filter('co')}
            """).fetchone()[0]
        except sqlite3.OperationalError:
            pass
    # what kind of σύμβαση each in-scope record is — the composition the
    # methodology prints, computed so the prose cannot go stale
    try:
        for kind, n in kh.execute("""
                SELECT c.document_kind, COUNT(*) FROM contracts c
                JOIN contract_scope s ON s.reference_number = c.reference_number
                WHERE s.in_scope = 1 AND c.document_kind IS NOT NULL
                GROUP BY 1"""):
            facts[f"kh_doc_{kind}"] = n
    except sqlite3.OperationalError:
        pass
    try:
        facts["n_authorities"] = kh.execute(
            "SELECT COUNT(*) FROM forest_authorities").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    # what each contract PROMISED — the basis of the timeline bar, counted so
    # the methodology paragraph cannot go stale (user, 2026-08-19)
    try:
        n_ext_steps = n_ext_chains = 0
        for (ref,) in kh.execute(
                "SELECT reference_number FROM contract_scope WHERE in_scope = 1"):
            dl = contract_deadlines(kh, ref)
            key = f"kh_deadline_{dl['basis'] or 'none'}"          # document | …
            facts[key] = facts.get(key, 0) + 1
            if dl["extensions"]:
                n_ext_chains += 1
                n_ext_steps += len(dl["extensions"])
        facts["kh_deadline_ext_chains"] = n_ext_chains
        facts["kh_deadline_ext_steps"] = n_ext_steps
    except sqlite3.OperationalError:
        pass
    # the procurement-family layer (calls resolved from the contracts' own
    # signed texts) — the methodology prose cites these, so they are computed
    try:
        facts["kh_family_calls"], facts["kh_family_contracts"] = kh.execute(f"""
            SELECT COUNT(DISTINCT f.adam), COUNT(DISTINCT f.reference_number)
            FROM contract_families f
            JOIN contract_scope s ON s.reference_number = f.reference_number
            WHERE f.kind = 'notice' AND f.role = 'procurement'
              AND s.in_scope = 1""").fetchone()
        facts["kh_family_none"] = kh.execute(f"""
            SELECT COUNT(*) FROM contract_scope s
            WHERE s.in_scope = 1
              AND NOT EXISTS (SELECT 1 FROM contract_families f
                               WHERE f.reference_number = s.reference_number
                                 AND f.kind = 'notice'
                                 AND f.role = 'procurement')""").fetchone()[0]
        # what the ΚΗΜΔΗΣ chain itself declares — the registry only knows the
        # links the ΣΥΜΒ payload carried, which is the reason the family layer
        # is read from the signed texts instead
        facts["kh_family_declared"] = kh.execute(f"""
            SELECT COUNT(DISTINCT cla.reference_number)
            FROM contract_linked_acts cla
            JOIN contract_scope s ON s.reference_number = cla.reference_number
            WHERE s.in_scope = 1""").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    if dase is not None:
        try:
            facts["dase_mixed_vat"] = dase.execute(f"""
                SELECT COUNT(*) FROM contracts co
                WHERE {dq.live_filter('co')}
                  AND EXISTS (SELECT 1 FROM contract_objects o
                              WHERE o.reference_number = co.reference_number
                                AND o.vat_percent = '0')
                  AND EXISTS (SELECT 1 FROM contract_objects o
                              WHERE o.reference_number = co.reference_number
                                AND o.vat_percent != '0')""").fetchone()[0]
        except sqlite3.OperationalError:
            pass
        variants: dict[str, set] = {}
        for vat, name in dase.execute(f"""
            SELECT c.vat_number, c.name FROM contractors c
            JOIN contracts co ON co.reference_number = c.reference_number
            WHERE {dq.live_filter('co')}"""):
            canon = dq.canonical_vat(vat)
            if canon:
                variants.setdefault(canon, set()).add((name or "").strip())
        facts["dase_max_variants"] = max(
            (len(v) for v in variants.values()), default=0)
    if ana is not None:
        for basis, cnt in ana.execute(
            "SELECT budget_vat_basis, COUNT(*) FROM projects "
            "WHERE budget_vat_basis IS NOT NULL GROUP BY budget_vat_basis"):
            facts[f"ana_vat_{basis}"] = cnt
    out["facts"] = facts
    return out


# ---------------------------------------------------------------- overview

def antinero_kpis(kh: sqlite3.Connection,
                  pay: sqlite3.Connection | None = None) -> dict:
    """q.kpis on the stated-basis connection (total == Σ stated net) + the
    harmonised KPI-row extras: median stated value, and the actually-paid
    totals read from `pay` (the connection that sees real payments)."""
    k = q.kpis(kh)
    stated = sorted(r[0] or 0.0 for r in kh.execute(f"""
        SELECT c.total_cost_with_vat FROM contracts c
        WHERE {q.scope_filter(kh, 'c.reference_number')}"""))
    k["stated_eur"] = round(sum(stated), 2)
    k["median_eur"] = dq._percentile(stated, 0.5)
    k["paid_eur"] = 0.0
    k["n_payments"] = 0
    pconn = pay if pay is not None else kh
    if q._has_payments_table(pconn) and q._has_scope_table(pconn):
        paid = pconn.execute("""
            SELECT ROUND(SUM(p.amount_with_vat), 2), COUNT(*)
            FROM contract_payments p
            JOIN contract_scope s ON s.reference_number = p.attributed_ref
            WHERE p.cancelled = 0 AND s.in_scope = 1""").fetchone()
        k["paid_eur"] = paid[0] or 0.0
        k["n_payments"] = paid[1]
    return k


def antinero_overview(kh: sqlite3.Connection,
                      pay: sqlite3.Connection | None = None) -> dict:
    """Everything the Anti-nero overview page needs except the map/detail
    payloads. `kh` = stated-basis connection (all value analytics);
    `pay` = payments layer (disbursement timeseries, per-year paid,
    paid KPI)."""
    pconn = pay if pay is not None else kh
    studies = q.study_costs(kh)
    top_studies = sorted(studies["rows"], key=lambda r: r["eur"], reverse=True)[:10]
    return {
        "kpis": antinero_kpis(kh, pconn),
        "procedures": q.procedure_mix(kh),
        "histogram": q.contract_value_histogram(kh),
        "direct_awards": q.direct_award_distribution(kh),
        "timeseries": q.disbursement_timeseries(pconn),
        "yearly": q.antinero_yearly(pconn),
        "studies": {"summary": studies["summary"], "top": top_studies},
        "top_contractors": q.top_contractors(kh, limit=10),
        "top_authorities": q.top_authorities(kh, limit=5),
        "top_signers": q.top_signers(kh, limit=5),
        "coverage": q.flow_coverage(kh),
        "probable": probable_related(kh),
        "cpvs": antinero_cpvs(kh),
        "categories": antinero_categories(kh),
        "document_kinds": antinero_document_kinds(kh),
    }


def antinero_categories(kh: sqlite3.Connection) -> list[dict]:
    """Curated work-type category per in-scope contract (ONE each, so the
    stated-net sums reconcile to the programme total; DATA_DECISIONS
    2026-08-14). Labels come from the curated file via category_labels —
    never hardcoded here. On the Atlas stated-basis connection
    total_cost_with_vat carries the net figure."""
    if not q._has_scope_table(kh) or not kh.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') "
            "AND name='contract_categories'").fetchone():
        return []
    rows = kh.execute("""
        SELECT c.category AS key, l.label AS label,
               COUNT(*) AS n, ROUND(SUM(k.total_cost_with_vat), 2) AS eur
        FROM contract_categories c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        JOIN contracts k ON k.reference_number = c.reference_number
        LEFT JOIN category_labels l ON l.category = c.category
        WHERE s.in_scope = 1
        GROUP BY c.category
        ORDER BY eur DESC, c.category
    """).fetchall()
    return [{"key": r["key"], "label": r["label"] or r["key"],
             "n": r["n"], "eur": r["eur"] or 0.0} for r in rows]


def antinero_cpvs(kh: sqlite3.Connection) -> list[dict]:
    """Every CPV code declared on an in-scope contract, with the registry's
    own description and the number of distinct in-scope contracts carrying
    it. Contracts declare several codes each, so counts sum to more than the
    contract count — € is deliberately NOT attributed per code (it would be
    double-counted under every code a contract declares)."""
    if not q._has_scope_table(kh):
        return []
    rows = kh.execute("""
        SELECT c.cpv_code AS code, MIN(c.cpv_description) AS desc,
               COUNT(DISTINCT c.reference_number) AS n
        FROM contract_cpvs c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        WHERE s.in_scope = 1
        GROUP BY c.cpv_code
        ORDER BY n DESC, c.cpv_code
    """).fetchall()
    return [{"code": r["code"], "desc": (r["desc"] or "").strip(), "n": r["n"]}
            for r in rows]


def contract_category(kh: sqlite3.Connection, ref: str) -> dict | None:
    """The contract's curated work-type category with its evidence: the
    descriptive project title from the signed PDF (source 'pdf', or
    'inherited:<ref>' when the derivative document quotes only the
    parties and the title comes from the parent's PDF)."""
    if not kh.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') "
            "AND name='contract_categories'").fetchone():
        return None
    en = ", l.label_en" if _column_exists(kh, "category_labels", "label_en") else ""
    r = kh.execute(f"""
        SELECT c.category AS key, l.label, l.note, c.title, c.source{en}
        FROM contract_categories c
        LEFT JOIN category_labels l ON l.category = c.category
        WHERE c.reference_number = ?""", (ref,)).fetchone()
    if r is None:
        return None
    return {"key": r["key"], "label": r["label"] or r["key"],
            "label_en": _col(r, "label_en") or r["label"] or r["key"],
            "note": r["note"], "title": r["title"], "source": r["source"]}


def contract_work_themes(kh: sqlite3.Connection, ref: str) -> dict:
    """What this contract's works ARE, as its own title states them.

    Multi-label by design (user, 2026-08-19): 101 of the 246 in-scope
    contracts name two or more kinds of work, which the single category key
    cannot carry. Each theme rides with the verbatim clause that states it.
    `cpv_notes` is the other half of the rule: a marker CPV code that names
    work the title does not is a NOTE about the procurement — the code list
    belongs to the call and is shared by all its lots — never a theme.
    """
    out: dict = {"themes": [], "cpv_notes": [], "source": None}
    if not _table(kh, "contract_work_themes"):
        return out
    for r in kh.execute("""
            SELECT t.theme, t.excerpt, t.source, l.label_el, l.label_en
            FROM contract_work_themes t
            LEFT JOIN work_theme_labels l ON l.theme = t.theme
            WHERE t.reference_number = ? ORDER BY t.seq""", (ref,)):
        out["themes"].append({"key": r["theme"], "el": r["label_el"],
                              "en": r["label_en"], "excerpt": r["excerpt"]})
        out["source"] = r["source"]
    if _table(kh, "contract_cpv_notes"):
        for r in kh.execute("""
                SELECT n.cpv_code, n.theme, l.label_el, l.label_en
                FROM contract_cpv_notes n
                LEFT JOIN work_theme_labels l ON l.theme = n.theme
                WHERE n.reference_number = ? ORDER BY n.cpv_code""", (ref,)):
            out["cpv_notes"].append({"cpv": r["cpv_code"], "key": r["theme"],
                                     "el": r["label_el"], "en": r["label_en"]})
    return out


def contract_municipalities(kh: sqlite3.Connection, ref: str) -> list[dict]:
    """The δήμοι the contract's documents place its works in.

    One level finer than the Π.Ε. layer and read from the same kind of
    sentence the forest services come from — «εντός των Δήμων Χαϊδαρίου και
    Ασπροπύργου, αρμοδιότητας Δασαρχείου Αιγάλεω» — either in the contract
    or in the πρόσκληση it cites, and the row says which (DATA_DECISIONS
    2026-08-19). `outside_region` marks the 49 whose Π.Ε. is not among the
    ones curated for the contract: recorded as the document states it, with
    the region layer deliberately left alone.
    """
    if not _table(kh, "contract_municipalities"):
        return []
    return [dict(r) for r in kh.execute("""
        SELECT municipality_code AS code, name, region_pe, authority,
               source_ref, from_call, excerpt, outside_region,
               outside_pe_explained, note
        FROM contract_municipalities WHERE reference_number = ?
        ORDER BY name""", (ref,))]


def contract_stated_duration(kh: sqlite3.Connection, ref: str) -> dict | None:
    """The deadline the CONTRACT states, with the clock it starts on.

    The document is the source and the ΚΗΜΔΗΣ field the cross-check (user,
    2026-08-19): the registry has a number for 83 of 246 in-scope contracts,
    never says what it counts from, and agrees with the signed text in 3 of
    the 65 cases where both exist. Three contracts answer with a season —
    Greece's fire season runs 1 May to 31 October, so their deadline is the
    31 October of the year they name.
    """
    if not _table(kh, "contract_durations"):
        return None
    r = kh.execute("SELECT * FROM contract_durations WHERE reference_number = ?",
                   (ref,)).fetchone()
    if r is None:
        return None
    out = dict(r)
    if out.get("fire_season"):
        out["starts"] = f"{out['fire_season']}-05-01"
        out["deadline"] = f"{out['fire_season']}-10-31"
    return out


def _table(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (name,)).fetchone())


def probable_related(kh: sqlite3.Connection) -> dict:
    """Chains kept in the dataset but excluded from every calculation:
    probably Anti-nero, RRF-16849 membership unproven from the primary
    documents (curated khmdhs/data/probable_related.json, DATA_DECISIONS
    2026-08-13). Counted on chain tips so each chain appears once; on the
    Atlas stated-basis connection `total_cost_with_vat` carries the net."""
    if not q._has_scope_table(kh):
        return {"n": 0, "total_eur": 0.0, "rows": []}
    rows = kh.execute("""
        SELECT k.reference_number AS ref, k.title AS title,
               k.contract_signed_date AS d, k.total_cost_with_vat AS eur
        FROM contracts k
        JOIN contract_scope s ON s.reference_number = k.reference_number
        WHERE s.scope = 'antinero_probable' AND s.superseded_by IS NULL
        ORDER BY k.contract_signed_date
    """).fetchall()
    out = [{"ref": r["ref"], "title": (r["title"] or "").strip()[:140],
            "d": r["d"], "eur": r["eur"]} for r in rows]
    return {"n": len(out),
            "total_eur": round(sum(r["eur"] or 0.0 for r in out), 2),
            "rows": out}


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

def dase_kpis(dase: sqlite3.Connection) -> dict:
    """dq.kpis (stated basis, net via the views) + the paid-KPI extras:
    Σ net payment orders and their contract coverage — payments exist for
    only part of the population (registry practice), so aggregates stay
    stated and the paid figure is a KPI with its caveat."""
    k = dq.kpis(dase)
    # consortium rows + worst-case registry spelling variance — cited in
    # page copy, computed so a refresh can't leave stale numbers
    # Contracts genuinely shared by SEVERAL co-ops. Counting contractor ROWS
    # overstated this five-fold (19 vs 4): most multi-row records are one
    # co-op typed twice under spelling variants, which the canonical-ΑΦΜ
    # merge already collapses — no euro is counted twice there
    # (DATA_DECISIONS 2026-08-17).
    k["n_consortium"] = sum(
        1 for (refs,) in dase.execute(f"""
            SELECT (SELECT GROUP_CONCAT(c.vat_number, '|') FROM contractors c
                    WHERE c.reference_number = co.reference_number)
            FROM contracts co WHERE {dq.live_filter('co')}""")
        if refs and len({dq.canonical_vat(v) for v in refs.split('|') if v}) > 1)
    variants: dict[str, set] = {}
    for vat, name in dase.execute(f"""
        SELECT c.vat_number, c.name FROM contractors c
        JOIN contracts co ON co.reference_number = c.reference_number
        WHERE {dq.live_filter('co')}"""):
        canon = dq.canonical_vat(vat)
        if canon:
            variants.setdefault(canon, set()).add((name or "").strip())
    k["max_name_variants"] = max((len(v) for v in variants.values()),
                                 default=0)
    k["paid_eur"] = 0.0
    k["n_paid_contracts"] = 0
    k["n_payments"] = 0
    try:
        paid = dase.execute("""
            SELECT ROUND(SUM(amount_with_vat), 2), COUNT(*),
                   COUNT(DISTINCT attributed_ref)
            FROM contract_payments WHERE cancelled = 0""").fetchone()
        k["paid_eur"] = paid[0] or 0.0
        k["n_payments"] = paid[1]
        k["n_paid_contracts"] = paid[2]
    except sqlite3.OperationalError:
        pass
    return k


# ------------------------------------------------------- ΔΑΣΕ display names

def antinero_network(kh: sqlite3.Connection) -> dict:
    """Every in-scope contract as a node, with the two relations that are
    ACTS rather than attributes: the call it was awarded under, and the
    contractor that won it.

    Measured before choosing (DATA_DECISIONS 2026-08-18): linking by
    contracting authority collapses 237 of 245 contracts into one blob —
    the framework lots each name 5-14 Δασαρχεία — and linking by Π.Ε.
    collapses all 245, since sharing a region is a coordinate, not a
    relationship. Call + contractor leaves 110 readable components.
    Authority and Π.Ε. ride along as attributes, for colour and tooltips.
    """
    rows = kh.execute(f"""
        SELECT k.reference_number AS ref, k.total_cost_without_vat AS eur,
               substr(k.title, 1, 90) AS title, k.contract_signed_date AS d,
               (SELECT f.adam FROM contract_families f
                 WHERE f.reference_number = k.reference_number
                   AND f.kind = 'notice' AND f.role = 'procurement'
                 ORDER BY f.seq LIMIT 1) AS call,
               (SELECT c.vat_number FROM contractors c
                 WHERE c.reference_number = k.reference_number
                 ORDER BY c.seq LIMIT 1) AS vat,
               (SELECT c.name FROM contractors c
                 WHERE c.reference_number = k.reference_number
                 ORDER BY c.seq LIMIT 1) AS who,
               (SELECT p.region_pe FROM contract_project_regions p
                 WHERE p.reference_number = k.reference_number
                 ORDER BY p.seq LIMIT 1) AS pe,
               (SELECT a.authority_name FROM contract_forest_authorities a
                 WHERE a.reference_number = k.reference_number
                 ORDER BY a.seq LIMIT 1) AS auth,
               cat.category AS cat, s.scope AS phase
          FROM contracts k
          JOIN contract_scope s ON s.reference_number = k.reference_number
                               AND s.in_scope = 1
          LEFT JOIN contract_categories cat
                 ON cat.reference_number = k.reference_number
         ORDER BY k.total_cost_without_vat DESC""").fetchall()
    nodes = [dict(r) for r in rows]
    n_call = len({n["call"] for n in nodes if n["call"]})
    # a call/contractor shared by 2+ contracts is what draws an edge
    from collections import Counter
    calls = Counter(n["call"] for n in nodes if n["call"])
    vats = Counter(n["vat"] for n in nodes if n["vat"])
    multi = {c for c, k in calls.items() if k > 1}
    # a contractor holding lots under several calls is the only relation
    # that crosses a procurement family — the bridge the chart annotates
    by_vat: dict[str, set[str]] = {}
    days: dict[str, set[str]] = {}
    for n in nodes:
        if n["vat"] and n["call"]:
            by_vat.setdefault(n["vat"], set()).add(n["call"])
        if n["call"] in multi:
            days.setdefault(n["call"], set()).add(n["d"])
    # Greece's statutory αντιπυρική περίοδος, 1 May - 31 October: the
    # timeline arrangement shades it, and the constant travels WITH its
    # count so the chart cannot drift from the number it prints
    fire_from, fire_to = "05-01", "10-31"
    in_season = sum(1 for n in nodes
                    if n["d"] and fire_from <= n["d"][5:] <= fire_to)
    return {
        "nodes": nodes,
        "fire_season": {"from": fire_from, "to": fire_to,
                        "n_contracts": in_season},
        "stats": {
            "n_contracts": len(nodes),
            "n_calls": n_call,
            "n_multi_calls": len(multi),
            "n_in_multi_calls": sum(1 for n in nodes if n["call"] in multi),
            "n_single_call": sum(1 for n in nodes
                                 if n["call"] and n["call"] not in multi),
            "n_no_call": sum(1 for n in nodes if not n["call"]),
            "n_contractors": len(vats),
            "n_multi_contractors": sum(1 for v in vats.values() if v > 1),
            "n_bridge_contractors": sum(1 for v in by_vat.values() if len(v) > 1),
            "n_bridge_multi": sum(1 for v in by_vat.values()
                                  if len(v & multi) > 1),
            # a split call whose every lot was signed on ONE day — the
            # timeline arrangement prints this, so it is computed here
            "n_same_day_calls": sum(1 for v in days.values() if len(v) == 1),
            "total_eur": round(sum(n["eur"] or 0 for n in nodes), 2),
        },
    }


def antinero_document_kinds(kh: sqlite3.Connection) -> dict:
    """The in-scope population by KIND of σύμβαση — the composition the front
    page and /methodology both state in prose, computed so neither can go
    stale. All of them ARE συμβάσεις (that is what ΚΗΜΔΗΣ files them as); the
    kind says which (khmdhs/document_kinds.py, DATA_DECISIONS 2026-08-18)."""
    from khmdhs.document_kinds import KINDS
    try:
        rows = kh.execute("""
            SELECT c.document_kind AS kind, COUNT(*) AS n FROM contracts c
            JOIN contract_scope s ON s.reference_number = c.reference_number
            WHERE s.in_scope = 1 AND c.document_kind IS NOT NULL
            GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    except sqlite3.OperationalError:
        return {"total": 0, "counts": {}, "labels": {}}
    counts = {r["kind"]: r["n"] for r in rows}
    return {
        "total": sum(counts.values()),
        "counts": counts,
        "labels": {k: {"el": KINDS[k][0], "en": KINDS[k][1]}
                   for k in counts if k in KINDS},
    }


def contract_document_kind(kh: sqlite3.Connection, adam: str) -> dict | None:
    """What this ΣΥΜΒ record IS, per its own document — a contract, an
    amendment, a supplementary contract, or a ministry approval. The registry's
    own `contract_type` cannot answer: it is the ν.4412 object category
    («Έργα»/«Υπηρεσίες») and reads the same on all of them (khmdhs
    /document_kinds.py, DATA_DECISIONS 2026-08-18)."""
    from khmdhs.document_kinds import KINDS
    try:
        row = kh.execute(
            "SELECT document_kind, document_kind_evidence, document_kind_source"
            "  FROM contracts WHERE reference_number = ?", (adam,)).fetchone()
    except sqlite3.OperationalError:
        return None          # a DB older than the ALTER guard that adds these
    if not row or not row["document_kind"]:
        return None
    el, en = KINDS.get(row["document_kind"], ("—", row["document_kind"]))
    return {"kind": row["document_kind"], "label_el": el, "label_en": en,
            "evidence": row["document_kind_evidence"],
            "source": row["document_kind_source"]}


def contract_family(kh: sqlite3.Connection, adam: str) -> dict | None:
    """The contract's procurement family: the πρόσκληση it cites and every
    sibling contract citing the same one, each with its own stated net €.

    Read from `contract_families`, which the loader derives from the
    contracts' own signed texts — the ΚΗΜΔΗΣ chain declares this for only
    40 of 245 in-scope contracts (DATA_DECISIONS 2026-08-18). Returns None
    for direct awards and negotiations, which publish no call at all.
    """
    try:
        me = kh.execute(
            "SELECT adam, role, source, excerpt FROM contract_families"
            " WHERE reference_number = ? AND kind = 'notice'"
            " ORDER BY CASE role WHEN 'procurement' THEN 0 ELSE 1 END, seq",
            (adam,)).fetchall()
    except sqlite3.OperationalError:            # table not built yet
        return None
    if not me:
        return None
    call = me[0]
    members = kh.execute("""
        SELECT f.reference_number AS ref, c.title, c.contract_signed_date AS d,
               c.total_cost_without_vat AS eur, s.in_scope
          FROM contract_families f
          JOIN contracts c ON c.reference_number = f.reference_number
          LEFT JOIN contract_scope s ON s.reference_number = f.reference_number
         WHERE f.adam = ? AND f.kind = 'notice' AND f.role = 'procurement'
         ORDER BY c.total_cost_without_vat DESC""", (call["adam"],)).fetchall()
    return {
        "call": call["adam"],
        "role": call["role"],
        "source": call["source"],
        "excerpt": call["excerpt"],
        # the call's own amendments, when the contract cites them
        "amendments": [r["adam"] for r in me[1:]],
        "contracts": [dict(r) for r in members],
        "total_eur": round(sum(r["eur"] or 0 for r in members), 2),
    }


def contract_authorities(kh: sqlite3.Connection, adam: str) -> list[dict]:
    """The contract's linked forest authorities with their seats — feeds
    the detail-page map (template rebuild, 2026-08-17).

    `excerpt` rides along because 6 contracts are linked by curated
    OVERRIDE rather than by their title, and 3 of those titles actively
    contradict what the page then shows (25SYMV016491944 is titled «ΔΔ
    ΛΕΣΒΟΥ» while its PDF places the works in Ρόδος). The evidence was
    stored from the start and never left the DB, so the page read as our
    error instead of the documented registry one (DATA_DECISIONS
    2026-08-18)."""
    rows = kh.execute("""
        SELECT cfa.authority_name AS name, cfa.source, cfa.excerpt, fa.kind,
               fa.lat, fa.lon, fa.region_pe, fa.seat_precision
        FROM contract_forest_authorities cfa
        LEFT JOIN forest_authorities fa ON fa.name = cfa.authority_name
        WHERE cfa.reference_number = ?
        ORDER BY cfa.seq""", (adam,)).fetchall()
    return [dict(r) for r in rows]


def dase_contract_geo(dase: sqlite3.Connection, kh: sqlite3.Connection,
                      adam: str) -> dict:
    """Region + awarding-unit seat for a ΔΑΣΕ contract's detail map."""
    pe = None
    row = dase.execute(
        "SELECT region_pe FROM dase_contract_regions WHERE reference_number = ?",
        (adam,)).fetchone()
    if row:
        pe = row["region_pe"]
    unit = dase.execute(
        "SELECT units_operator_name FROM contracts WHERE reference_number = ?",
        (adam,)).fetchone()
    seat = None
    if unit and unit["units_operator_name"]:
        f = " ".join(_fold_upper(unit["units_operator_name"]).split())
        hit = kh.execute(
            "SELECT name, lat, lon FROM forest_authorities").fetchall()
        for r in hit:
            if " ".join(_fold_upper(r["name"]).split()) == f and r["lat"]:
                seat = {"name": r["name"], "lat": r["lat"], "lon": r["lon"]}
                break
    return {"pe": pe, "unit_seat": seat}


def dase_display_names(dase: sqlite3.Connection) -> dict[str, dict]:
    """Canonical ΑΦΜ → curated bilingual display names (dase_names_loader,
    DATA_DECISIONS 2026-08-15). Empty when the table is absent — every
    caller degrades to the registry/curated spelling."""
    try:
        return {r["vat"]: {"el": r["display_el"], "en": r["display_en"]}
                for r in dase.execute(
                    "SELECT vat, display_el, display_en FROM dase_display_names")}
    except sqlite3.OperationalError:
        return {}


def _overlay_coop_name(row: dict, names: dict[str, dict]) -> dict:
    """Swap a co-op row's `name` for the curated display name, keeping the
    previous spelling as `registry_name` and adding `name_en`."""
    d = names.get(row.get("vat") or "")
    if d:
        row["registry_name"] = row["name"]
        row["name"] = d["el"]
        row["name_en"] = d["en"]
    return row


def overlay_executor_names(executors: list[dict] | None,
                           names: dict[str, dict]) -> list[dict] | None:
    """Present each curated sponsor-project executor under the SAME name
    its co-op carries on every /dase surface (DATA_DECISIONS 2026-08-16:
    same ΑΦΜ → same name): for rows with a pinned `dase_vat`, the act's
    verbatim spelling moves to `act_name` (evidence — it also stays in
    the excerpt), `name` becomes the curated display_el and `name_en` is
    added. Identity-unconfirmed rows (dase_vat null) keep the act name
    alone. No-op with an empty names map (ΔΑΣΕ DB absent)."""
    if not executors:
        return executors
    for e in executors:
        d = names.get(e.get("dase_vat") or "")
        if d:
            e["act_name"] = e["name"]
            e["name"] = d["el"]
            e["name_en"] = d["en"]
    return executors


def dase_coop_shares(dase: sqlite3.Connection) -> dict[str, list[dict]]:
    """Live contracts held JOINTLY by several co-ops → each partner's even
    share, keyed by canonical ΑΦΜ.

    The frozen webui aggregates credit every partner with the WHOLE
    contract (the max-exposure convention), which counts the same euros
    twice in a per-co-op ranking. The registry records no shares and the
    signed document states none — the one live case, 23SYMV013747204, has
    the two co-ops' representatives «συμφωνήσαν από κοινού» over a single
    pooled quantity at unit prices — so the Atlas splits such a contract
    EVENLY between its partners (user decision, DATA_DECISIONS 2026-08-17;
    the same convention the Anti-nero region maps and `pipelines` already
    use). Contract COUNTS are untouched: each partner does hold the
    contract, jointly.

    Returns {canonical ΑΦΜ: [{ref, year, n_parties, full_eur, share_eur,
    over_eur}]} — `over_eur` (full − share) is what a full-attribution
    total must give back to reach the even-split basis.
    """
    per_ref: dict[str, dict] = {}
    for r in dase.execute(f"""
        SELECT co.reference_number AS ref, co.total_cost_with_vat AS eur,
               COALESCE(co.contract_signed_date, co.submission_date) AS d,
               c.vat_number AS vat
        FROM contracts co JOIN contractors c USING (reference_number)
        WHERE {dq.live_filter('co')}"""):
        e = per_ref.setdefault(r["ref"], {"eur": r["eur"] or 0.0,
                                          "year": (r["d"] or "")[:4] or None,
                                          "vats": set()})
        cv = dq.canonical_vat(r["vat"])
        if cv:
            e["vats"].add(cv)
    out: dict[str, list[dict]] = {}
    for ref, e in per_ref.items():
        n = len(e["vats"])
        if n < 2:                       # the ordinary single-party contract
            continue
        cents = round((e["eur"] or 0.0) * 100)
        parts = _even_cents(cents, n)
        for cv, part in zip(sorted(e["vats"]), parts):
            share = part / 100
            out.setdefault(cv, []).append({
                "ref": ref, "year": e["year"], "n_parties": n,
                "full_eur": round(e["eur"], 2), "share_eur": share,
                "over_eur": round(cents / 100 - share, 2),
            })
    return out


def _even_cents(total: int, n: int) -> list[int]:
    """Split `total` cents into `n` parts that sum to it EXACTLY — the odd
    cent(s) go to the first parts. Halving an odd amount and rounding both
    halves would leave the ranking a cent short of the basis, so the
    remainder is allocated rather than dropped; callers order the parties
    deterministically (by ΑΦΜ) so the allocation is stable across runs."""
    base, extra = divmod(total, n)
    return [base + (1 if i < extra else 0) for i in range(n)]


def _split_coop_totals(rows: list[dict], shares: dict[str, list[dict]],
                       key: str = "total_eur") -> list[dict]:
    """Turn full-attribution co-op rows into even-split ones in place."""
    for a in rows:
        over = sum(s["over_eur"] for s in shares.get(a.get("vat") or "", ()))
        if over:
            a[key] = round((a.get(key) or 0.0) - over, 2)
    return rows


def dase_coop_detail(dase: sqlite3.Connection, vat: str, summary: dict,
                     contracts: list[dict], yearly: list[dict],
                     units: list[dict]) -> dict:
    """The co-op page payload on the even-split basis: its money total, its
    per-year bars and its per-awarder table give back the over-credited
    half of any jointly held contract, and the contract itself is marked
    (`n_parties` / `share_eur`) so the list explains the difference instead
    of silently disagreeing with the total. The contract keeps its own
    stated value in `total_cost_with_vat` — that IS the contract's value —
    and the co-op's share rides beside it."""
    mine = dase_coop_shares(dase).get(dq.canonical_vat(vat) or "", [])
    if not mine:
        return {"summary": summary, "contracts": contracts,
                "yearly": yearly, "units": units}
    by_ref = {s["ref"]: s for s in mine}
    summary["total_eur"] = round((summary.get("total_eur") or 0.0)
                                 - sum(s["over_eur"] for s in mine), 2)
    for c in contracts:
        s = by_ref.get(c["reference_number"])
        if s:
            c["n_parties"] = s["n_parties"]
            c["share_eur"] = s["share_eur"]
    for b in yearly:
        over = sum(s["over_eur"] for s in mine if s["year"] == str(b["year"]))
        if over:
            b["eur"] = round(b["eur"] - over, 2)
    # the awarder table groups by (unit, org) — matching on the unit NAME
    # alone would hit every group sharing it (one Δασαρχείο appears under
    # both ΥΠΕΝ and its Αποκεντρωμένη), subtracting the share several times
    key_of = {r["ref"]: (r["unit"], r["org"]) for r in dase.execute(
        "SELECT reference_number AS ref, units_operator_name AS unit, "
        "organization_name AS org FROM contracts WHERE reference_number IN (%s)"
        % ",".join("?" * len(by_ref)), list(by_ref))}
    for u in units:
        over = sum(s["over_eur"] for ref, s in by_ref.items()
                   if key_of.get(ref) == (u["unit"], u["org"]))
        if over:
            u["total_eur"] = round((u["total_eur"] or 0.0) - over, 2)
    return {"summary": summary, "contracts": contracts,
            "yearly": yearly, "units": units}


def dase_coops(dase: sqlite3.Connection, q: str | None = None,
               sort: str = "total_eur") -> list[dict]:
    """list_coops with the display names overlaid BEFORE the search filter,
    so a query matches the curated Greek name, the English name AND the
    registry spelling; jointly held contracts are split evenly, so the
    column of totals sums to the live basis exactly."""
    names = dase_display_names(dase)
    out = _split_coop_totals(
        [_overlay_coop_name(a, names) for a in dq._coop_rows(dase)],
        dase_coop_shares(dase))
    if q:
        needle = dq._search_norm(q)
        fold = dq._phonetic_fold(needle)
        out = [a for a in out
               if dq._matches(needle, fold, a["vat"], a["name"],
                              a.get("registry_name"), a.get("name_en"))]
    key = sort if sort in ("total_eur", "n_contracts", "name") else "total_eur"
    if key == "name":
        return sorted(out, key=lambda a: a["name"] or "")
    return sorted(out, key=lambda a: -(a[key] or 0))


def dase_contract_display(dase: sqlite3.Connection) -> dict[str, str]:
    """reference_number → ' | '-joined curated display names of its
    contractor(s); registry spelling fallback for any partner without a
    curated entry (e.g. a freshly harvested co-op)."""
    names = dase_display_names(dase)
    per_ref: dict[str, list] = {}
    for r in dase.execute("SELECT reference_number, vat_number, name "
                          "FROM contractors ORDER BY reference_number, seq"):
        d = names.get(dq.canonical_vat(r["vat_number"]) or "")
        per_ref.setdefault(r["reference_number"], []).append(
            d["el"] if d else r["name"])
    return {ref: " | ".join(v) for ref, v in per_ref.items()}


def _doubling_label(v: float) -> str:
    """Bracket-edge label that survives below €1.000 (webui's `_short_eur`
    floor-divides by 1000, so every sub-€1k edge would read «0k»)."""
    if v >= 1_000_000:
        return f"{v / 1_000_000:g}M".replace(".", ",")
    if v >= 1_000:
        return f"{v / 1_000:g}k".replace(".", ",")
    return f"{round(v):g}"


def dase_value_histogram(dase: sqlite3.Connection) -> dict:
    """Value brackets for the Atlas /dase CONTRACT VALUES chart.

    Same counts, different EDGES from webui's `value_histogram` (frozen,
    and its brackets stay as they are): here every bracket is exactly one
    doubling, anchored on €1.000 and extended to cover the live range.
    That makes the bracket layout a true log axis — equal-width slots ARE
    equal ratios — so the beeswarm the chart toggles with can place its
    dots on the very same scale and the median line lands in one place in
    both modes (DATA_DECISIONS 2026-08-17). webui's first bracket is an
    unbounded `[0, 1000)` catch-all holding 4,5 doublings in one slot,
    which no continuous scale can match.

    Edges are DERIVED from the data (never a fixed table), so a refresh
    that brings a smaller or larger contract widens the axis by itself.
    The leading `0` edge keeps `_bin_values`' half-open convention intact
    for anything below the first doubling; that bracket and the trailing
    overflow one are normally empty.
    """
    values = [r[0] or 0.0 for r in dase.execute(f"""
        SELECT co.total_cost_with_vat FROM contracts co
        WHERE {dq.live_filter()}
    """)]
    live = [v for v in values if v > 0]
    lo, hi = (min(live), max(live)) if live else (1_000.0, 1_000.0)
    ANCHOR = 1_000.0
    k_lo = math.floor(math.log2(lo / ANCHOR))
    k_hi = math.ceil(math.log2(hi / ANCHOR))
    if ANCHOR * 2 ** k_hi <= hi:            # hi exactly on an edge
        k_hi += 1
    edges = [0.0] + [ANCHOR * 2 ** k for k in range(k_lo, k_hi + 1)]

    h = q._bin_values(values, tuple(edges))
    values.sort()
    h["median"] = values[len(values) // 2] if values else 0
    h["labels"] = (
        [f"≤{_doubling_label(edges[1])}"]
        + [f"{_doubling_label(edges[i])}–{_doubling_label(edges[i + 1])}"
           for i in range(1, len(edges) - 1)]
        + [f"≥{_doubling_label(edges[-1])}"]
    )
    return h


def dase_overview(dase: sqlite3.Connection, kh: sqlite3.Connection) -> dict:
    """Everything the ΔΑΣΕ overview page needs (webui /dase context)."""
    return {
        "kpis": dase_kpis(dase),
        "yearly": dq.yearly_totals(dase),
        # dase_coops applies the even split before ranking — the frozen
        # top_coops would rank on the double-counted full attribution
        "top_coops": dase_coops(dase)[:10],
        "top_orgs": dq.top_orgs(dase, limit=10),
        "top_units": dq.top_units(dase, limit=10),
        "kind_mix": dase_kind_mix(dase, kh),
        "procedures": dq.procedure_mix(dase),
        "types": dq.type_mix(dase),
        "cpvs": dq.cpv_mix(dase, limit=10),
        "histogram": dase_value_histogram(dase),
        "by_pe": dq.money_by_pe(dase),
    }


def dase_excluded_hits(dase: sqlite3.Connection, q: str) -> list[dict]:
    """Curated exclusions matching a contracts search — registry
    double-postings (DATA_DECISIONS 2026-08-14) and the contracts whose
    signed PDF names no co-op (2026-08-17) — so a citation of the excluded
    ΑΔΑΜ still finds its page, badged for what it is, instead of the row
    silently not existing. Each row carries its own marker, so the list
    can name the reason rather than calling everything a duplicate. Uses
    the same folding as the frozen list_contracts filter."""
    markers = _exclusion_present(dase)
    if not markers:                                  # DB predates both
        return []
    rows = dase.execute(f"""
        SELECT co.reference_number, co.title, co.contract_signed_date,
               co.total_cost_with_vat, co.units_operator_name,
               co.organization_name, co.cancelled{_exclusion_cols(dase)},
               (SELECT GROUP_CONCAT(c.name, ' | ') FROM contractors c
                WHERE c.reference_number = co.reference_number) AS contractor_names
        FROM contracts co
        WHERE {' OR '.join(f'co.{c} IS NOT NULL' for c in markers)}
        ORDER BY co.contract_signed_date DESC
    """).fetchall()
    needle = dq._search_norm(q)
    fold = dq._phonetic_fold(needle)
    return [dict(r) for r in rows
            if dq._matches(needle, fold, r["reference_number"], r["title"],
                           r["contractor_names"], r["units_operator_name"],
                           r["organization_name"])]


def _unit_forest_kind(unit: str | None) -> str | None:
    """Forest-service units that missed a registry seat (Δασαρχείο
    Φουρνά lives in dase_units.json; ΔΔ Ηλείας/Πιερίας/Χαλκιδικής rows
    matched via curated unit keys; the supra-regional ΕΠΙΘΕΩΡΗΣΗ has no
    seat by nature) still belong to the green forest family — drawn at
    the Π.Ε. centroid, never as «other bodies». Shared by the map circles
    and the category/flow payload so one rule serves both."""
    f = _fold_upper(unit or "")
    if f.startswith("ΔΑΣΑΡΧΕΙΟ"):
        return "dx"
    if "ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ" in f or f.startswith("ΕΠΙΘΕΩΡΗΣΗ"):
        return "dd"
    return None


def dase_map(dase: sqlite3.Connection, kh: sqlite3.Connection) -> dict:
    """Proportional-symbol map payload: one circle per awarding forest unit.

    `dase_contract_regions.source` records the matched registry authority
    (`registry:<canonical name>`), which joins to the khmdhs
    `forest_authorities` seats. Contracts awarded by non-forest bodies
    (δήμοι, περιφέρειες, ministries — source curated/override) have no unit
    seat; they aggregate per Π.Ε. at its centroid so the map still reconciles
    to the live total. The 4 multi-Π.Ε. ΑΔΜΗΕ contracts stay off-map,
    reported in `unresolved`. Each circle carries its contract list (ref,
    trimmed title, date, net €) for the click-through panel. On the Atlas
    connection `total_cost_with_vat` carries the net value
    (apply_net_basis)."""
    seats = {r["name"]: (r["lat"], r["lon"], r["kind"])
             for r in kh.execute(
                 "SELECT name, lat, lon, kind FROM forest_authorities")}
    rows = dase.execute(f"""
        SELECT r.source, r.region_pe, co.total_cost_with_vat AS eur,
               co.reference_number AS ref,
               co.units_operator_name AS unit, co.organization_name AS org,
               COALESCE(co.contract_signed_date, co.submission_date) AS d
        FROM contracts co
        JOIN dase_contract_regions r USING (reference_number)
        WHERE {dq.live_filter('co')}
    """).fetchall()
    coop_of = dase_contract_display(dase)

    # legend classification comes from the public-bodies registry
    # (DATA_DECISIONS 2026-08-16) instead of name-stem guessing: aliases
    # are the VERBATIM organization strings (coverage bijection pinned in
    # tests/test_public_bodies.py), scope is the user-reviewed tier-1 label
    body_scope = {}
    try:
        for br in dase.execute(
                "SELECT a.alias, b.scope FROM public_body_aliases a "
                "JOIN public_bodies b ON b.key = a.body_key"):
            body_scope[br["alias"]] = br["scope"]
    except Exception:
        pass

    def _org_class(org: str | None) -> str:
        """Remaining non-forest awarders: municipal/regional government
        (registry scope municipal/regional — δήμοι, περιφέρειες and their
        νομικά πρόσωπα) draw black; every other public body (ΟΣΕ, ports,
        universities, hospitals, ΓΕΑ…) grey. An org the registry does not
        know renders grey — the loader WARN + the bijection test surface
        it long before it ships."""
        scope = body_scope.get((org or "").strip())
        return "muni" if scope in ("municipal", "regional") else "misc"

    def contract_row(r, by: str) -> dict:
        return {"ref": r["ref"], "d": (r["d"] or "")[:10] or None,
                "eur": r["eur"], "by": by,
                "coop": coop_of.get(r["ref"]) or ""}

    def summarise(group: list, by_of) -> dict:
        vals = sorted((r["eur"] or 0.0) for r in group)
        mid = len(vals) // 2
        median = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
        contracts = sorted((contract_row(r, by_of(r)) for r in group),
                           key=lambda c: -(c["eur"] or 0.0))
        return {"n": len(vals), "eur": round(sum(vals), 2),
                "median_eur": round(median, 2), "contracts": contracts}

    # a seatless-looking unit may just be an alternative spelling of a
    # seated registry authority: «ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ Ν. ΠΙΕΡΙΑΣ» (Νομού …,
    # the pre-2022 ΑΠΔ-era style) IS the seated ΔΔ Πιερίας — without this
    # merge the same directorate draws two circles
    def _wsfold(s: str | None) -> str:
        f = " ".join(_fold_upper(s or "").split())
        # dash-spacing variants («ΜΑΚΕΔΟΝΙΑΣ - ΘΡΑΚΗΣ» vs «ΜΑΚΕΔΟΝΙΑΣ-ΘΡΑΚΗΣ»)
        return re.sub(r"\s*[-–]\s*", "-", f)

    seat_by_fold = {_wsfold(n): n for n, (lat, _lon, _k) in seats.items()
                    if lat is not None}
    # supra-regional units seated via the ΥΠΕΝ directory (ΕΠΙΘΕΩΡΗΣΗ Μ-Θ):
    # one circle at the real seat instead of per-Π.Ε. centroid dots
    dir_seats = {}
    try:
        for r in kh.execute("SELECT name, lat, lon FROM forest_units_directory "
                            "WHERE lat IS NOT NULL AND authority_name IS NULL"):
            dir_seats[_wsfold(r["name"])] = (r["name"], r["lat"], r["lon"])
    except Exception:
        pass
    # genitive/nominative spelling drift («ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ» vs the seated
    # «Δασαρχείο Φουρνάς») is bridged through the curated English identity:
    # if the unit's EN name equals a seated authority's EN name they are
    # the same body (EN names are unique within the registry — pinned)
    auth_en = _auth_en_map()
    unit_en_all = _unit_en_map()
    seat_by_en = {}
    for f, n in seat_by_fold.items():
        en = auth_en.get(f)
        if en:
            seat_by_en[en] = n

    def _seat_match(unit: str | None) -> str | None:
        f = _wsfold(unit)
        f2 = " ".join(t for t in f.split() if t not in ("Ν.", "ΝΟΜΟΥ"))
        hit = seat_by_fold.get(f) or seat_by_fold.get(f2)
        if hit:
            return hit
        en = unit_en_all.get(f)
        return seat_by_en.get(en) if en else None

    # genitive spelling variants of the SAME seatless unit (ΔΑΣΑΡΧΕΙΟ
    # ΦΟΥΡΝΑ / ΦΟΥΡΝΩΝ) collapse onto one circle via their curated
    # English identity (unit_names_en.json); unmapped strings stand alone
    unit_en = _unit_en_map()

    units: dict[str, dict] = {}
    seatless: dict[tuple, dict] = {}
    other: dict[tuple, list] = {}
    for r in rows:
        src, pe = r["source"], r["region_pe"]
        name = src.split(":", 1)[1] if src.startswith("registry:") else None
        if name and name in seats and seats[name][0] is not None:
            units.setdefault(name, {"pe": pe, "rows": []})["rows"].append(r)
            continue
        fkind = _unit_forest_kind(r["unit"])
        if fkind and pe:
            seat_name = _seat_match(r["unit"])
            if seat_name:
                units.setdefault(seat_name, {"pe": pe, "rows": []})["rows"].append(r)
                continue
            ds = dir_seats.get(_wsfold(r["unit"]))
            if ds:
                dname, dlat, dlon = ds
                grp = seatless.setdefault((dname, None), {
                    "kind": fkind, "label": dname, "rows": [],
                    "lat": dlat, "lon": dlon, "pe": pe})
                grp["rows"].append(r)
                continue
            ident = unit_en.get(_wsfold(r["unit"])) or _wsfold(r["unit"])
            grp = seatless.setdefault((ident, pe), {
                "kind": fkind, "label": (r["unit"] or "").strip(), "rows": []})
            grp["rows"].append(r)
        elif pe:
            other.setdefault((pe, _org_class(r["org"])), []).append(r)

    unit_by = lambda r: (r["unit"] or r["org"] or "").strip()  # noqa: E731
    out_units = []
    for name, u in units.items():
        lat, lon, kind = seats[name]
        out_units.append({"name": name, "kind": kind, "pe": u["pe"],
                          "lat": lat, "lon": lon,
                          **summarise(u["rows"], unit_by)})
    # forest units without a registry seat sit at their Π.Ε. centroid;
    # a unit spanning several Π.Ε. gets one circle per Π.Ε., disambiguated
    dup_names = {i for (i, _p) in seatless
                 if sum(1 for (i2, _q) in seatless if i2 == i) > 1}
    for (ident, pe), grp in seatless.items():
        if grp.get("lat") is not None:          # directory-seated (ΕΠΙΘ. Μ-Θ)
            out_units.append({"name": grp["label"], "kind": grp["kind"],
                              "pe": grp.get("pe"),
                              "lat": grp["lat"], "lon": grp["lon"],
                              **summarise(grp["rows"], unit_by)})
            continue
        cent = PE_CENTROIDS.get(pe)
        if not cent:
            continue
        label = f"{grp['label']} · {pe}" if ident in dup_names else grp["label"]
        out_units.append({"name": label, "kind": grp["kind"], "pe": pe,
                          "lat": cent[0], "lon": cent[1],
                          **summarise(grp["rows"], unit_by)})
    out_units.sort(key=lambda x: -x["eur"])

    out_other = []
    for (pe, klass), group in other.items():
        cent = PE_CENTROIDS.get(pe)
        if not cent:
            continue
        out_other.append({"pe": pe, "kind": klass,
                          "lat": cent[0], "lon": cent[1],
                          **summarise(group, lambda r: (r["org"] or r["unit"] or "").strip())})
    out_other.sort(key=lambda x: -x["eur"])

    unresolved = dase.execute(f"""
        SELECT COUNT(*), COALESCE(SUM(co.total_cost_with_vat), 0)
        FROM contracts co
        LEFT JOIN dase_contract_regions r USING (reference_number)
        WHERE {dq.live_filter('co')} AND r.region_pe IS NULL
    """).fetchone()
    return {"units": out_units, "other": out_other,
            "unresolved": {"n": unresolved[0],
                           "eur": round(unresolved[1], 2)}}


def _dase_kind_rows(dase: sqlite3.Connection,
                    kh: sqlite3.Connection) -> list[dict]:
    """Per live ΔΑΣΕ contract: the awarding BODY's registry kind, the
    awarding UNIT's kind and the stated net €.

    The unit decision mirrors `dase_map`'s circle kinds exactly (registry
    seat kind → dd/dx, seatless forest spellings stay in the forest
    family, everything else splits muni/misc by the public-bodies registry
    scope); rows the map leaves unplaced for lack of a Π.Ε. (the
    multi-Π.Ε. ΑΔΜΗΕ power-line contracts) are other-public awarders and
    land in misc. A real-DB test cross-checks the aggregate against the
    map payload, so the two can never drift apart silently.

    Body kinds come from the public-bodies registry (coverage bijection
    pinned in tests/test_public_bodies.py); municipal entities count with
    their municipalities (same municipal scope tier). An org string the
    registry does not know lands in 'unknown' — the bodies_loader WARN and
    the bijection test scream long before that ships, and the real-DB pin
    asserts the bucket stays absent."""
    seats = {r["name"]: (r["lat"], r["kind"])
             for r in kh.execute("SELECT name, lat, kind FROM forest_authorities")}
    body_kind: dict[str, str] = {}
    scope: dict[str, str] = {}
    try:
        for r in dase.execute("SELECT a.alias, b.kind, b.scope "
                              "FROM public_body_aliases a "
                              "JOIN public_bodies b ON b.key = a.body_key"):
            body_kind[r["alias"]] = r["kind"]
            scope[r["alias"]] = r["scope"]
    except sqlite3.OperationalError:
        pass

    out = []
    # jointly signed contracts split their € evenly between the co-ops, the
    # same rule the ranking and the co-op pages use (DATA_DECISIONS
    # 2026-08-18) — a decision that held in one chart and not another would
    # show one co-op two different totals on one page
    shares = dase_coop_shares(dase)
    share_by_ref: dict[str, list[tuple[str, float]]] = {}
    for vat, items in shares.items():
        for s in items:
            share_by_ref.setdefault(s["ref"], []).append((vat, s["share_eur"]))

    for r in dase.execute(f"""
        SELECT co.reference_number AS ref,
               r.source AS source, r.region_pe AS region_pe,
               co.units_operator_name AS unit, co.organization_name AS org,
               co.total_cost_with_vat AS eur,
               (SELECT c.vat_number FROM contractors c
                WHERE c.reference_number = co.reference_number
                ORDER BY c.seq LIMIT 1) AS vat
        FROM contracts co
        LEFT JOIN dase_contract_regions r USING (reference_number)
        WHERE {dq.live_filter('co')}"""):
        src, pe, org = r["source"] or "", r["region_pe"], (r["org"] or "").strip()
        name = src.split(":", 1)[1] if src.startswith("registry:") else None
        if name and name in seats and seats[name][0] is not None:
            unit_kind = seats[name][1]
        else:
            forest = _unit_forest_kind(r["unit"])
            if forest and pe:
                unit_kind = forest
            else:
                unit_kind = ("muni" if scope.get(org) in ("municipal", "regional")
                             else "misc")
        kind = body_kind.get(org, "unknown")
        # `parties` carries the co-op layer: one entry per holder with its
        # share. Body/unit stay per CONTRACT (`eur` whole, one row), so
        # those marginals are unaffected; only the co-op column splits.
        parties = share_by_ref.get(r["ref"]) or [
            (dq.canonical_vat(r["vat"]) or "", r["eur"] or 0.0)]
        out.append({"body": "municipality" if kind == "municipal_entity" else kind,
                    "unit": unit_kind, "eur": r["eur"] or 0.0,
                    "vat": dq.canonical_vat(r["vat"]) or "",
                    "parties": parties})
    return out


def dase_kind_mix(dase: sqlite3.Connection, kh: sqlite3.Connection,
                  top_coops: int = 10) -> dict:
    """Category payload for /dase: the AWARDING BODIES / AWARDING UNITS
    share bars (`bodies`/`units` marginals) and the three-column
    delegation diagram — `flows` (body→unit) and `coop_flows`
    (unit→co-op) over the `coops` node list, top N by € plus one
    «other co-ops» node carrying the long tail. Everything comes from one
    per-contract pass (`_dase_kind_rows`), so no two charts on the page
    can disagree; every layer reconciles to the live basis."""
    rows = _dase_kind_rows(dase, kh)

    def _marginal(key: str) -> list[dict]:
        bucket: dict[str, dict] = {}
        for r in rows:
            d = bucket.setdefault(r[key], {"n": 0, "eur": 0.0})
            d["n"] += 1
            d["eur"] += r["eur"]
        return sorted(({"kind": k, "n": v["n"], "eur": round(v["eur"], 2)}
                       for k, v in bucket.items()), key=lambda x: -x["n"])

    flows: dict[tuple, dict] = {}
    for r in rows:
        d = flows.setdefault((r["body"], r["unit"]), {"n": 0, "eur": 0.0})
        d["n"] += 1
        d["eur"] += r["eur"]

    # third column: the co-ops themselves — the biggest N by €, the rest
    # pooled into one node so the column still sums to the basis
    per_coop: dict[str, dict] = {}
    for r in rows:
        for i, (vat, share) in enumerate(r["parties"]):
            d = per_coop.setdefault(vat, {"n": 0, "eur": 0.0})
            # € split between the holders, but the CONTRACT counted ONCE:
            # this column is an aggregate over the population, so its Σn
            # must equal the 1.998 live contracts, never 1.999. The count
            # lands on the first holder by ΑΦΜ — the same deterministic
            # order the cent allocation uses (user decision 2026-08-18).
            d["n"] += 1 if i == 0 else 0
            d["eur"] += share
    ranked = sorted(per_coop.items(), key=lambda kv: -kv[1]["eur"])
    named = {vat for vat, _ in ranked[:top_coops]}
    display = dase_display_names(dase)
    registry = {}
    for r in dase.execute("SELECT vat_number, name FROM contractors"):
        registry.setdefault(dq.canonical_vat(r["vat_number"]) or "", r["name"])

    coops = [{"vat": vat,
              "label": (display.get(vat) or {}).get("el") or registry.get(vat) or vat,
              "n": v["n"], "eur": round(v["eur"], 2)}
             for vat, v in ranked[:top_coops]]
    rest = [v for vat, v in ranked[top_coops:]]
    if rest:
        coops.append({"vat": None, "label": None, "n_coops": len(rest),
                      "n": sum(v["n"] for v in rest),
                      "eur": round(sum(v["eur"] for v in rest), 2)})

    coop_flows: dict[tuple, dict] = {}
    for r in rows:
        for i, (vat, share) in enumerate(r["parties"]):
            key = (r["unit"], vat if vat in named else None)
            d = coop_flows.setdefault(key, {"n": 0, "eur": 0.0})
            d["n"] += 1 if i == 0 else 0
            d["eur"] += share

    return {
        "bodies": _marginal("body"),
        "units": _marginal("unit"),
        "flows": sorted(({"body": b, "unit": u, "n": v["n"],
                          "eur": round(v["eur"], 2)}
                         for (b, u), v in flows.items()),
                        key=lambda x: -x["eur"]),
        "coops": coops,
        "coop_flows": sorted(({"unit": u, "vat": vat, "n": v["n"],
                               "eur": round(v["eur"], 2)}
                              for (u, vat), v in coop_flows.items()),
                             key=lambda x: -x["eur"]),
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
                            "d": [], "pe": [], "vat": []}
    for r in rows:
        d = _full_date(r["contract_signed_date"]) or _full_date(r["submission_date"])
        t = (r["title"] or r["reference_number"]).strip()
        out["ref"].append(r["reference_number"])
        out["t"].append(t[:70] + ("…" if len(t) > 70 else ""))
        out["eur"].append(r["total_cost_with_vat"])
        out["year"].append(d[:4] if d else None)
        out["d"].append(d)
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
    # curated display names win over the registry spelling (presentation only)
    for v, d in dase_display_names(dase).items():
        if v in name_by_canon:
            name_by_canon[v] = d["el"]
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


def forest_units_extra(kh: sqlite3.Connection) -> list[dict]:
    """ΥΠΕΝ directory units OUTSIDE the contract registry (DATA_DECISIONS
    2026-08-17): the parts of the forest-service network with no recorded
    contracts in our datasets — the absence is itself a finding. Reference
    layer only; empty when the table is absent."""
    try:
        rows = kh.execute("""
            SELECT name, inspectorate, unit_kind, street, tk, city, phone, email,
                   lat, lon
            FROM forest_units_directory
            WHERE authority_name IS NULL
            ORDER BY CASE unit_kind
                       WHEN 'inspectorate' THEN 0 WHEN 'coordination' THEN 1
                       WHEN 'reforestation' THEN 2 WHEN 'dd' THEN 3 ELSE 4 END,
                     inspectorate, name""").fetchall()
    except sqlite3.OperationalError:
        return []
    return [dict(r) for r in rows]


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
        display = dase_display_names(dase)
        curated.update({v: d["el"] for v, d in display.items() if v in curated})
        for c in dase_contracts:
            vat = dq.canonical_vat(c["vat"]) if c["vat"] else None
            if vat is None:
                continue
            if vat in display:
                c["contractor_name"] = display[vat]["el"]
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

    keys = row.keys()
    return {
        "name": name, "slug": slug, "kind": row["kind"],
        "pe": row["region_pe"],
        "seat": {"city": row["municipality_name"],
                 "lat": row["lat"], "lon": row["lon"]},
        # office layer (DATA_DECISIONS 2026-08-17): ΥΠΕΝ directory address
        # confirmed by the authority's own Diavgeia letterheads
        "contact": {
            "street": row["street"] if "street" in keys else None,
            "postal_code": row["postal_code"] if "postal_code" in keys else None,
            "city": row["city"] if "city" in keys else None,
            "phone": row["phone"] if "phone" in keys else None,
            "email": row["email"] if "email" in keys else None,
            "precision": row["seat_precision"] if "seat_precision" in keys else None,
        },
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


# ------------------------------------------------------ contract chains

def contract_chains(kh: sqlite3.Connection) -> dict[str, list[str]]:
    """{chain tip: [ΑΔΑΜ oldest → newest]} for every contract posted more than
    once.

    ΥΠΕΝ posts a later act on an existing contract under a NEW ΣΥΜΒ ΑΔΑΜ — a
    τροποποίηση όρων, a παράταση προθεσμίας, an έγκριση συμπληρωματικών
    εργασιών — and `scope_loader` takes the earlier record out of scope with
    `superseded_by` so the same money is counted once. Nothing is replaced
    (57 of the 60 later records carry the parent's exact value); the chain IS
    the contract, and this is what assembles it (DATA_DECISIONS 2026-08-19).

    `superseded_by` is one hop, so the walk is transitive. Additive
    supplementary CONTRACTS never appear here: both they and their parent stay
    in scope, and only an out-of-scope record carries `superseded_by`.
    """
    try:
        sup = {r["reference_number"]: r["superseded_by"] for r in kh.execute(
            "SELECT reference_number, superseded_by FROM contract_scope "
            "WHERE superseded_by IS NOT NULL")}
    except sqlite3.OperationalError:        # a DB without the scope table
        return {}
    back: dict[str, list[str]] = {}
    for earlier, later in sup.items():
        back.setdefault(later, []).append(earlier)

    def members(tip: str) -> list[str]:
        out, stack, seen = [], [tip], set()
        while stack:
            cur = stack.pop()
            if cur in seen:                 # a cycle would hang the walk
                continue
            seen.add(cur)
            out.append(cur)
            stack.extend(back.get(cur, ()))
        return out

    chains: dict[str, list[str]] = {}
    for tip in {t for t in sup.values() if t not in sup}:
        pool = set(members(tip))
        # order by following the links from the record nothing precedes
        seq: list[str] = []
        cur = next((m for m in sorted(pool) if not back.get(m)), tip)
        while cur and cur in pool:
            pool.discard(cur)
            seq.append(cur)
            cur = sup.get(cur)
        seq.extend(sorted(pool))            # branches, if the registry ever forks
        chains[tip] = seq
    return chains


def payment_dates(pay: sqlite3.Connection, ref: str) -> dict[str, str]:
    """{payment ΑΔΑΜ: ISO date} for one contract's orders.

    The frozen `queries.contract_detail` exposes only `signed_date`, which
    182 of the 886 live orders do not carry — their date is the submission
    stamp. The timeline needs a date for every tick, so it is resolved here
    rather than by editing webui.
    """
    try:
        rows = pay.execute(
            "SELECT payment_ref, signed_date, submission_date FROM contract_payments"
            " WHERE attributed_ref = ? OR contract_ref = ?", (ref, ref)).fetchall()
    except sqlite3.OperationalError:
        return {}
    out = {}
    for r in rows:
        d = _full_date(r["signed_date"]) or _full_date(r["submission_date"])
        if d:
            out[r["payment_ref"]] = d
    return out


def contract_chain(kh: sqlite3.Connection, ref: str) -> list[dict]:
    """The contract's own version chain, oldest → newest, or [] when it was
    posted once.

    Every record of the chain, with the date it carries, WHAT it is
    (`document_kind`) and the value it stated — which is what makes a price
    change across a chain visible («€3,78M → €5,00M» on 26SYMV019098206).
    The registry's adamChain cannot supply this: it names an upstream act for
    only 40 of 245 in-scope contracts, and the version links live in
    `contracts.prev_reference_no` / `contract_scope.superseded_by` instead.
    """
    chains = contract_chains(kh)
    seq = next((v for v in chains.values() if ref in v), [])
    if not seq:
        return []
    dk = ", document_kind" if _column_exists(kh, "contracts", "document_kind") else ""
    out = []
    for m in seq:
        r = kh.execute(
            f"SELECT title, contract_signed_date, submission_date,"
            f" total_cost_without_vat{dk} FROM contracts"
            f" WHERE reference_number = ?", (m,)).fetchone()
        if r is None:
            continue
        d, basis = record_date(m, _col(r, "document_kind"),
                               r["contract_signed_date"] or r["submission_date"])
        out.append({
            "ref": m,
            "d": d,
            "d_basis": basis,
            "kind": _col(r, "document_kind"),
            "eur": (round(r["total_cost_without_vat"], 2)
                    if r["total_cost_without_vat"] is not None else None),
            "title": (r["title"] or "")[:160] or None,
            "self": m == ref,
        })
    return out


def _document_deadline(kh: sqlite3.Connection, ref: str,
                       rec: sqlite3.Row) -> tuple[str | None, str | None]:
    """The deadline the CONTRACT states, as a date, or (None, None)."""
    if not _table(kh, "contract_durations"):
        return None, None
    r = kh.execute("SELECT n, unit, days, basis, fire_season FROM"
                   " contract_durations WHERE reference_number = ?",
                   (ref,)).fetchone()
    if r is None:
        return None, None
    if r["fire_season"]:                      # 1 May – 31 October
        return f"{r['fire_season']}-10-31", "document_season"
    if not r["days"]:
        return None, None
    base = (_full_date(rec["start_date"]) if r["basis"] == "works_start"
            else _full_date(rec["contract_signed_date"]))
    base = base or _full_date(rec["contract_signed_date"]) or _full_date(rec["start_date"])
    if not base:
        return None, None
    try:
        end = _dt.date.fromisoformat(base) + _dt.timedelta(days=int(r["days"]))
    except ValueError:
        return None, None
    return end.isoformat(), "document"


def contract_deadlines(kh: sqlite3.Connection, ref: str) -> dict:
    """The deadline the contract ANNOUNCED, and every later act that moved it.

    The timeline bar draws promised-against-executed, the way the sponsor
    pages do (user, 2026-08-19) — not signature-to-paperwork. Two sources say
    what was promised, in this order:

    * the registry's own `end_date` (21 of 246 in-scope originals), and
    * the stated duration counted from the start date (62 more) — «Μήνες»,
      «Ημέρες», or a bare number, which is read as months and SAID to be
      assumed, because the one case whose real dates can check it
      (25SYMV017106210: stated 4, actual 121 days) reads as months.

    83 originals announce a deadline this way. For 10 more the σύμβαση
    announces none and a later act of the same chain does — that act's date
    is then the only announced deadline on record, and `basis` says so
    («act») rather than passing it off as the original's. The remaining 153
    announce nothing at all and the bar draws a stub, like the Gantt's
    projects with no calendar deadline.

    Extensions are later records announcing a deadline LATER than the one in
    force — 6 chains, 8 steps, all of them «Παράταση προθεσμίας» records
    carrying their new end date in the registry.
    """
    seq = [r["ref"] for r in contract_chain(kh, ref)] or [ref]
    dk = ", document_kind" if _column_exists(kh, "contracts", "document_kind") else ""
    recs = []
    for m in seq:
        r = kh.execute(
            f"SELECT contract_signed_date, submission_date, start_date, end_date,"
            f" contract_duration, contract_duration_unit{dk} FROM contracts"
            f" WHERE reference_number = ?", (m,)).fetchone()
        if r is None:
            continue
        d, _ = record_date(m, _col(r, "document_kind"),
                           r["contract_signed_date"] or r["submission_date"])
        recs.append((m, r, d, _col(r, "document_kind")))
    if not recs:
        return {"deadline": None, "basis": None, "source_ref": None,
                "duration": None, "unit": None, "assumed": False,
                "extensions": []}

    def announced(r) -> tuple[str | None, str | None]:
        if r["end_date"]:
            return _full_date(r["end_date"]), "end_date"
        n = r["contract_duration"]
        base = _full_date(r["start_date"]) or _full_date(r["contract_signed_date"])
        if not n or not base:
            return None, None
        u = (r["contract_duration_unit"] or "").upper()
        days = n if u.startswith("ΗΜΕΡ") else n * 365 if u.startswith("ΕΤ") else round(n * 30.44)
        try:
            end = _dt.date.fromisoformat(base) + _dt.timedelta(days=int(days))
        except ValueError:
            return None, None
        return end.isoformat(), "duration"

    ref0, r0, _d0, _k0 = recs[0]
    # The DOCUMENT first (user decision, 2026-08-19): the σύμβαση's own
    # «συνολική προθεσμία … ορίζεται σε τρεις (3) μήνες από …» beats the
    # registry field, which it matches in 3 of 65 comparable cases. The
    # clock is the one the sentence names — signature, or the start of
    # works — and a contract whose time is the fire season runs to 31.10.
    # the curated row is keyed on the record IN SCOPE (the chain tip), while
    # the base date comes from the σύμβαση that started the clock
    deadline, basis = _document_deadline(kh, ref, r0)
    if deadline is None and ref != ref0:
        deadline, basis = _document_deadline(kh, ref0, r0)
    if deadline is None:
        deadline, basis = announced(r0)
    source_ref, source_rec = (ref0, r0) if deadline else (None, r0)
    rest = recs[1:]
    if deadline is None:                       # a later act is the only one
        for m, r, _d, _k in rest:
            got, _b = announced(r)
            if got:
                deadline, basis, source_ref, source_rec = got, "act", m, r
                rest = [x for x in rest if x[0] != m]
                break

    extensions, cur, n = [], deadline, 0
    for m, r, d, kind in rest:
        got, _b = announced(r)
        if got and cur and got > cur:
            n += 1
            extensions.append({"ref": m, "d": d, "deadline": got,
                               "n": n, "kind": kind})
            cur = got
    return {
        "deadline": deadline,
        "basis": basis,
        "source_ref": source_ref,
        "duration": source_rec["contract_duration"],
        "unit": source_rec["contract_duration_unit"],
        "assumed": bool(source_rec["contract_duration"]
                        and not source_rec["contract_duration_unit"]),
        # the registry fields THE DEADLINE WAS READ FROM, verbatim, so the
        # page can quote the record it actually used — on a chain the viewed
        # record is the tip and its own dates are a different statement
        "fields": {
            "ref": source_ref or ref0,
            "duration": source_rec["contract_duration"],
            "unit": source_rec["contract_duration_unit"],
            "start_date": _full_date(source_rec["start_date"]),
            "end_date": _full_date(source_rec["end_date"]),
        },
        "extensions": extensions,
    }


# ------------------------------------------------- explore (all 3 datasets)

def explore_rows(kh: sqlite3.Connection, dase: sqlite3.Connection | None,
                 ana: sqlite3.Connection | None) -> dict:
    """One compact row per contract/project across the three datasets, for
    the client-side /explore finder. One stated-basis value per row (net):
    Anti-nero + ΔΑΣΕ = stated contract value, Ανάδοχοι = committed budget
    after amendments, net where the act states it (nullable — sponsors
    often commit without a figure). Missing DBs degrade honestly (their
    rows are simply absent)."""
    rows: list[dict] = []

    hq_map: dict[str, str] = {}
    for r in kh.execute("SELECT vat_number, region_pe FROM contractor_locations"
                        " WHERE region_pe IS NOT NULL"):
        hq_map[r["vat_number"]] = canonical_pe(r["region_pe"]) or r["region_pe"]

    # contracts with a linked διακήρυξη/πρόσκληση (PROC) — None (unknown)
    # when the linked-acts layer has not been harvested yet
    notice_refs: set[str] | None
    try:
        notice_refs = {r[0] for r in kh.execute(
            "SELECT DISTINCT reference_number FROM contract_linked_acts "
            "WHERE kind = 'notice'")}
    except sqlite3.OperationalError:
        notice_refs = None

    # contracts with a Diavgeia completion act (project end date)
    done_refs: set[str] | None
    try:
        done_refs = {r[0] for r in kh.execute(
            "SELECT DISTINCT attributed_ref FROM contract_completion_acts")}
    except sqlite3.OperationalError:
        done_refs = None

    # the δήμοι each contract's documents name, for the municipality filter
    muni_map: dict[str, list[str]] = {}
    try:
        for r in kh.execute("SELECT reference_number, name FROM"
                            " contract_municipalities ORDER BY name"):
            muni_map.setdefault(r["reference_number"], []).append(r["name"])
    except sqlite3.OperationalError:      # layer not loaded in this DB
        pass

    # the version chains, and one lookup of what every member record IS
    chains = contract_chains(kh)
    versions: dict[str, dict] = {}
    members = [m for seq in chains.values() for m in seq]
    if members:
        dk = ", document_kind" if _column_exists(kh, "contracts", "document_kind") else ""
        for m in members:
            v = kh.execute(
                f"SELECT title, contract_signed_date, submission_date,"
                f" total_cost_without_vat{dk} FROM contracts"
                f" WHERE reference_number = ?", (m,)).fetchone()
            if v is None:
                continue
            vd, vbasis = record_date(m, _col(v, "document_kind"),
                                     v["contract_signed_date"] or v["submission_date"])
            versions[m] = {
                "ref": m,
                "d": vd,
                "db": vbasis,
                "k": _col(v, "document_kind"),
                "v": (round(v["total_cost_without_vat"], 2)
                      if v["total_cost_without_vat"] is not None else None),
                "title": v["title"],
            }

    eff = q.effective_cost(kh, "c")
    for r in kh.execute(f"""
        SELECT c.reference_number AS ref, c.title,
               c.contract_signed_date, c.submission_date,
               c.procedure_type, c.bids_submitted, c.cancelled,
               {eff} AS value,
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
        # ONE row per contract-CHAIN, not per ΚΗΜΔΗΣ record: a τροποποίηση or
        # an έγκριση συμπληρωματικών is a later act on the same contract, and
        # its earlier records were unreachable in this table until now. The
        # row shows the ORIGINAL contract's title and links to the TIP, whose
        # value it carries (user decisions, 2026-08-19).
        chain = chains.get(r["ref"], [r["ref"]])
        first = versions.get(chain[0], {})
        dates = [v["d"] for v in (versions.get(m) for m in chain) if v and v["d"]]
        row_d = (dates[0] if dates else None) or _full_date(
            r["contract_signed_date"]) or _full_date(r["submission_date"])
        rows.append({
            "ds": "antinero", "ref": r["ref"],
            "d": row_d,
            # last date of the chain, for the «first → last» date cell; absent
            # for a contract posted once, which is most of them
            **({"d1": dates[-1]} if len(chain) > 1 and dates[-1] != row_d else {}),
            "t": ((first.get("title") if len(chain) > 1 else None)
                  or r["title"] or "")[:120],
            "co": (r["names"] or "")[:110],
            "v": round(r["value"], 2) if r["value"] is not None else None,
            "pe": pes, "hq": hqs,
            # the δήμοι the contract's documents name — one level finer than
            # the Π.Ε. filter, Anti-nero only (DATA_DECISIONS 2026-08-19)
            **({"mu": muni_map[r["ref"]]} if muni_map.get(r["ref"]) else {}),
            "proc": _proc_kind(r["procedure_type"]),
            "st": "cancelled" if r["cancelled"] else None,
            "b1": 1 if r["bids_submitted"] == 1 else 0,
            "pr": None if notice_refs is None
                 else (1 if r["ref"] in notice_refs else 0),
            "fin": None if done_refs is None
                  else (1 if r["ref"] in done_refs else 0),
            # every record of the chain: the versions chip row, and the ΑΔΑΜ
            # the client search must answer to
            **({"vs": [versions[m] for m in chain if m in versions],
                "alt": [m for m in chain if m != r["ref"]]}
               if len(chain) > 1 else {}),
        })

    if dase is not None:
        # ΔΑΣΕ διακήρυξη flag: the adamChain harvest covered the whole
        # population, so 0 honestly means "no linked notice in the registry"
        dase_notice_refs: set[str] | None
        try:
            dase_notice_refs = {r[0] for r in dase.execute(
                "SELECT DISTINCT reference_number FROM contract_linked_acts "
                "WHERE kind = 'notice'")}
        except sqlite3.OperationalError:
            dase_notice_refs = None
        dase_disp = dase_contract_display(dase)
        for r in dase.execute(f"""
            SELECT co.reference_number AS ref, co.title,
                   co.contract_signed_date, co.submission_date,
                   co.procedure_type, co.total_cost_with_vat AS value,
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
                "co": (dase_disp.get(r["ref"]) or r["names"] or "")[:110],
                "v": round(r["value"], 2) if r["value"] is not None else None,
                "pe": pes, "hq": [],
                "proc": _proc_kind(r["procedure_type"]),
                "st": None, "b1": 0,
                "pr": None if dase_notice_refs is None
                     else (1 if r["ref"] in dase_notice_refs else 0),
                "fin": None,
            })

    if ana is not None:
        for r in ana.execute("""
            SELECT root_ada, company, works_kind, location_text, pe,
                   COALESCE(budget_net_eur, budget_current) AS budget,
                   start_date, status FROM projects"""):
            rows.append({
                "ds": "anadohoi", "ref": r["root_ada"],
                "d": r["start_date"],
                "t": (r["location_text"] or "")[:120],
                "co": (r["company"] or "")[:110],
                "v": r["budget"],   # net where the act states it (curated)
                "pe": [r["pe"]] if r["pe"] else [], "hq": [],
                "proc": "sponsor",
                "st": r["status"], "b1": 0, "pr": None,
                "fin": 1 if r["status"] == "completed" else 0,
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
    # ΨΟΕ8 names «COCA COLA Hellas» (Κηφισίας 26 & Παραδείσου 2) — a distinct
    # legal entity from the 3Ε bottler the other acts name; one brand system,
    # so one group, but the label states both (DATA_DECISIONS 2026-08-11)
    (("COCA COLA",), "Coca-Cola (3Ε / Hellas)"),
    # same entity in two scripts: ΨΧΟ2 «ΛΙΝΤΛ ΕΛΛΑΣ & ΣΙΑ.Ο.Ε» vs 6768
    # «Lidl Hellas & Σια Ο.Ε.» (Σίνδος 57022 HQ printed in the act)
    (("LIDL", "ΛΙΝΤΛ"), "Lidl Ελλάς"),
    # the act's text layer renders the name in Greek/Latin homoglyph soup
    # («ΣTANTA A.E. ETAIPEIA ΔIAXEIPIΣHΣ AKINHTΩN») — clean display name
    (("ΣΤΑΝΤΑ",), "ΣΤΑΝΤΑ Α.Ε."),
    # compact display labels for names too long for one timeline line;
    # the full legal names stay on the project pages
    (("ΚΑΝΕΛΛΟΠΟΥΛΟΥ",), "Ίδρυμα Π. & Α. Κανελλοπούλου"),
    (("ΛΑΣΚΑΡΙΔ",), "Ίδρυμα Α.Κ. Λασκαρίδης"),
    (("ΒΙΟΠΟΙΚΙΛΟΤΗΤ",), "Εταιρεία Προστ. Βιοποικιλότητας Θράκης"),
    (("TATOI CLUB",), "TATOΪ Club & ΕΛΙΑ Κατασκευαστική"),
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
        budget = (r["budget_net_eur"] if r["budget_net_eur"] is not None
                  else r["budget_current"])
        projects.append({
            "ada": r["root_ada"], "company": r["company"],
            # the sponsor-group display name (rename/script variants merged);
            # per-act verbatim names stay on the project pages
            "group": _sponsor_group(r["company"]),
            "funder": r["funder"], "works_kind": r["works_kind"],
            "deliverables": r["deliverables"],
            "area": r["area_stremmata"], "pe": r["pe"],
            "fire": r["fire_event"], "budget": budget,
            "budget_stated": r["budget_eur"],
            "vat_basis": r["budget_vat_basis"],
            "start": r["start_date"],
            "deadline0": r["deadline_initial"],
            "deadline": r["deadline_current"],
            "dtext": r["deadline_text"],
            "completed": r["completed_date"], "revoked": r["revoked_date"],
            "status": r["status"], "amendments": amendments,
            "superseded_by": r["superseded_by"],
            "location": r["location_text"],
            # digitised works-zone ids (evia_works_zones.geojson), curated
            # from the act's basin citation
            "works_zones": (json.loads(r["works_zones"])
                            if r["works_zones"] else None),
            # executing forest co-ops named in the act trail (curated)
            "executors": (json.loads(r["executors"])
                          if r["executors"] else None),
            # curated θέση-level work locations, compact for the map
            # (full records incl. excerpts ship on the project endpoint)
            "work_sites": ([{"name": s["name"], "lat": s.get("lat"),
                             "lon": s.get("lon"),
                             "prec": s.get("geo_precision")}
                            for s in json.loads(r["work_sites"])]
                           if r["work_sites"] else None),
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
    budgets = sorted(p["budget"] for p in live if p["budget"] is not None)
    vat_counts: dict[str, int] = {}
    for p in live:
        if p["vat_basis"]:
            vat_counts[p["vat_basis"]] = vat_counts.get(p["vat_basis"], 0) + 1
    return {
        "kpis": {
            "n_projects": len(live),
            "n_companies": len({_sponsor_group(p["company"]) for p in live}),
            "stated_eur": round(sum(budgets), 2),
            "median_eur": dq._percentile(budgets, 0.5),
            "n_stated": len(budgets),
            "vat_counts": vat_counts,
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
    out["works_zones"] = (json.loads(out["works_zones"])
                          if out.get("works_zones") else None)
    out["executors"] = (json.loads(out["executors"])
                        if out.get("executors") else None)
    out["work_sites"] = (json.loads(out["work_sites"])
                         if out.get("work_sites") else None)
    out["effis_scars"] = (json.loads(out["effis_scars"])
                          if out.get("effis_scars") else None)
    try:
        out["evidence"] = json.loads(out.pop("evidence_json") or "{}")
    except ValueError:
        out["evidence"] = {}
    # supersede linkage, both directions, so each page can tell the whole
    # restatement story (predecessor: "not counted"; successor: "restates X")
    pred = ana.execute(
        "SELECT root_ada, company, start_date, budget_eur FROM projects "
        "WHERE superseded_by = ?", (ada,)).fetchone()
    if pred is not None:
        out["restates"] = dict(pred)
    if out.get("superseded_by"):
        succ = ana.execute(
            "SELECT root_ada, company, start_date, budget_eur FROM projects "
            "WHERE root_ada = ?", (out["superseded_by"],)).fetchone()
        if succ is not None:
            out["restated_as"] = dict(succ)
    _DECISIONS_SQL = """
        SELECT pd.relation, pd.detail, pd.excerpt,
               d.ada, d.kind, d.issue_date, d.subject, d.org, d.protocol
          FROM project_decisions pd
          JOIN decisions d ON d.ada = pd.ada
         WHERE pd.root_ada = ?
         ORDER BY d.issue_date, d.ada"""
    out["decisions"] = [dict(d) for d in ana.execute(_DECISIONS_SQL, (ada,))]
    # a successor's page is the pair's ONE canonical page: fold the restated
    # predecessor's acts into the trail (its πράξη labelled as the replaced
    # original) so the full paper history reads in a single list
    if pred is not None:
        pred_rows = [dict(d) for d in ana.execute(_DECISIONS_SQL,
                                                  (pred["root_ada"],))]
        for d in pred_rows:
            if d["relation"] == "initial":
                d["relation"] = "superseded_initial"
        out["decisions"] = sorted(out["decisions"] + pred_rows,
                                  key=lambda d: (d["issue_date"] or "",
                                                 d["ada"]))
    return out


# ------------------------------------------------ procurement timeline

_TIMELINE_ORDER = {"request": 0, "approved_request": 1, "notice": 2,
                   "auction": 3, "contract": 4, "completion": 5}

# the two curated exclusion markers, selected only where the deployed DB has
# them (db.py adds columns through an ALTER guard, so an older file may not)
_EXCLUSION_COLS = ("duplicate_of", "related_to")


def _exclusion_present(conn: sqlite3.Connection) -> list[str]:
    """Whichever of the exclusion markers this DB file actually carries."""
    try:
        have = {r[1] for r in conn.execute("PRAGMA table_info(contracts)")}
    except sqlite3.OperationalError:
        return []
    return [c for c in _EXCLUSION_COLS if c in have]


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})"))


def _exclusion_cols(conn: sqlite3.Connection) -> str:
    """SQL fragment appending those markers to a `contracts` select list."""
    return "".join(f", {c}" for c in _exclusion_present(conn))


def _col(row: sqlite3.Row, name: str):
    """Row value when the column was selected, else None."""
    return row[name] if name in row.keys() else None


# «Ημ/νία: 07/05/2026» from the ministry's digital-signature block. pdftotext
# renders the μ of «Ημ/νία» as the MICRO SIGN in these files, so both letters
# are accepted — with only μ the pattern matches nothing at all.
_SIGNED_ON = re.compile(r"[ΗH][μµ]/ν[ίι]α\s*:?\s*(\d{2})/(\d{2})/(\d{4})")


def act_own_date(adam: str) -> tuple[str | None, str | None]:
    """(ISO date, basis) of the DOCUMENT itself, read from its own PDF.

    ΚΗΜΔΗΣ copies the CONTRACT's `contractSignedDate` onto every later act
    posted against it — 39 of the 46 in-scope records that are not an original
    contract carry their parent's date verbatim, so 26SYMV018978343, signed
    07.05.2026, is filed as 01.08.2025 (DATA_DECISIONS 2026-08-19). The
    document's own date is in the signature block where it exists (15 of 46),
    else in the ΚΗΜΔΗΣ publication stamp every one of them carries.
    """
    p = PDF_CACHE_DIR / f"{adam}.txt"
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None, None
    m = _SIGNED_ON.search(head)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "signature"
    m = re.search(rf"{adam}\s+(\d{{4}}-\d{{2}}-\d{{2}})", head)
    return (m.group(1), "published") if m else (None, None)


def record_date(adam: str, kind: str | None,
                signed: str | None) -> tuple[str | None, str]:
    """(ISO date, basis) for ONE ΚΗΜΔΗΣ record.

    An original contract's `contractSignedDate` is its own signature date and
    is used as-is. Every OTHER record — a τροποποίηση, a παράταση, an έγκριση
    συμπληρωματικών — inherits that same field from the contract it acts on,
    so its date must come from its own document instead (`act_own_date`).
    """
    if kind in (None, "contract"):
        return _full_date(signed), "signed"
    own, basis = act_own_date(adam)
    return (own, basis) if own else (_full_date(signed), "inherited")


def _stamped_date(adam: str) -> str | None:
    """The date ΚΗΜΔΗΣ stamped on the document itself.

    Acts a contract cites but the registry never declared have no row in
    `linked_acts`, so there is no metadata to read a date from — but every
    ΚΗΜΔΗΣ PDF carries «<ΑΔΑΜ> <YYYY-MM-DD>» in its own stamp, which the
    cached sidecar preserves.
    """
    p = PDF_CACHE_DIR / f"{adam}.txt"
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    m = re.search(rf"{adam}\s+(\d{{4}}-\d{{2}}-\d{{2}})", head)
    return m.group(1) if m else None


def _chain_refs(kh: sqlite3.Connection, ref: str) -> set[str]:
    """Every record of the contract's own version chain, `ref` included."""
    seq = next((v for v in contract_chains(kh).values() if ref in v), None)
    return set(seq) if seq else {ref}


def contract_timeline(kh: sqlite3.Connection, ref: str,
                      own_records_only: bool = False) -> list[dict]:
    """The contract's full procurement family (αίτημα → πρόσκληση →
    κατακύρωση → συμβάσεις), chronological. Sibling contracts resolve to
    their stored record when they belong to the dataset; payments are not
    included — the detail page lists them separately."""
    try:
        rows = kh.execute("""
            SELECT cla.adam, cla.kind, la.title, la.submission_date,
                   la.signed_date, la.cancelled
              FROM contract_linked_acts cla
              LEFT JOIN linked_acts la USING (adam)
             WHERE cla.reference_number = ? AND cla.kind != 'payment'
             """, (ref,)).fetchall()
    except sqlite3.OperationalError:        # tables not built yet
        rows = []
    out = []
    for r in rows:
        entry = {
            "adam": r["adam"], "kind": r["kind"],
            "title": (r["title"] or "")[:160] or None,
            "d": _full_date(r["signed_date"]) or _full_date(r["submission_date"]),
            "cancelled": r["cancelled"] or 0,
            "in_db": False,
        }
        if r["kind"] == "contract":
            # ΚΗΜΔΗΣ's adamChain returns the whole procurement FAMILY, so a
            # multi-lot award puts the other lots here — other companies'
            # contracts, with their own pages, listed as if they were
            # documents of this one (19 in-scope pages, up to 11 rows each).
            # The Anti-nero page drops them (`own_records_only`): the
            # relationship is the DIAGRAM's, which knows the call for 220 of
            # 246 contracts, and a line under the trail points at it (user,
            # 2026-08-19). ΔΑΣΕ keeps them — its FamilyTree is drawn FROM
            # this list, and an excluded sibling states its reason there.
            if own_records_only and r["adam"] not in _chain_refs(kh, ref):
                continue
            # `dk` is what the DOCUMENT says it is — a ΣΥΜΒ ΑΔΑΜ carries
            # contracts, amendments, supplementary contracts and ministry
            # approvals alike, and the trail must not label them all «Contract»
            dk = ", document_kind" if _column_exists(kh, "contracts", "document_kind") else ""
            c = kh.execute(
                f"SELECT title, contract_signed_date, submission_date, "
                f"cancelled{dk}{_exclusion_cols(kh)} FROM contracts "
                f"WHERE reference_number = ?", (r["adam"],)).fetchone()
            if c is not None:
                who = kh.execute(
                    "SELECT name FROM contractors WHERE reference_number = ? "
                    "ORDER BY seq LIMIT 1", (r["adam"],)).fetchone()
                sib_d, sib_basis = record_date(
                    r["adam"], _col(c, "document_kind"),
                    c["contract_signed_date"] or c["submission_date"])
                entry.update({
                    "title": (c["title"] or "")[:160] or None,
                    # a later act inherits the CONTRACT's date in the registry;
                    # the trail must show the date of the document it lists
                    "d": sib_d,
                    "d_basis": sib_basis,
                    "cancelled": c["cancelled"] or 0,
                    # WHY the sibling is excluded — the trail must not print
                    # «cancelled» over a double-posting or an out-of-scope
                    # contract, both of which carry cancelled = 1 as their
                    # exclusion mechanism (DATA_DECISIONS 2026-08-17)
                    "duplicate_of": _col(c, "duplicate_of"),
                    "related_to": _col(c, "related_to"),
                    "doc_kind": _col(c, "document_kind"),
                    "in_db": True,
                    # first contractor — lets the family diagram label the
                    # sibling and NAME-match its κατακύρωση (never guessed)
                    "who": who["name"] if who else None,
                })
        out.append(entry)
    # Diavgeia completion acts (οριστική παραλαβή / περαίωση / ολοκλήρωση)
    try:
        for r in kh.execute("""
            SELECT ada, act_kind, subject, issue_date, end_date, end_basis,
                   end_excerpt
              FROM contract_completion_acts
             WHERE cited_ref = ? OR attributed_ref = ?""", (ref, ref)):
            out.append({
                "adam": r["ada"], "kind": "completion",
                "ckind": r["act_kind"],
                "title": (r["subject"] or "")[:160] or None,
                "d": r["end_date"] or r["issue_date"],
                "end_basis": r["end_basis"],
                "end_excerpt": r["end_excerpt"],
                "cancelled": 0, "in_db": False,
            })
    except sqlite3.OperationalError:
        pass
    # Acts the contract's OWN TEXT cites but the registry never declared:
    # `linked_acts` names an upstream act for just 40 of 245 in-scope
    # contracts, while 200 quote their πρόσκληση by ΑΔΑΜ (DATA_DECISIONS
    # 2026-08-18). Without these the trail contradicts the PROCUREMENT
    # FAMILY diagram on the same page — 24SYMV015170098 showed a call in
    # the diagram and an empty chain in the trail.
    try:
        seen = {e["adam"] for e in out}
        for r in kh.execute(
                "SELECT adam, kind, role, excerpt FROM contract_families"
                " WHERE reference_number = ? ORDER BY kind, seq", (ref,)):
            if r["adam"] in seen:
                continue
            seen.add(r["adam"])
            out.append({
                "adam": r["adam"], "kind": r["kind"],
                "title": None,          # never invented; the PDF is linked
                "d": _stamped_date(r["adam"]),
                "cancelled": 0, "in_db": False,
                # provenance: this row is evidence from the contract, not a
                # link the registry published
                "cited": True, "role": r["role"], "excerpt": r["excerpt"],
            })
    except sqlite3.OperationalError:            # table not built yet
        pass

    # The twin of a re-posted record. ΚΗΜΔΗΣ cancels a record and posts the
    # contract again with NO link between the two — no prev/next, no
    # adamChain — so the only way each page can show the other is the
    # curated `duplicate_of` (DATA_DECISIONS 2026-08-19). Added on BOTH
    # sides: the cancelled record points forward, the live one back.
    try:
        twins = [r["reference_number"] for r in kh.execute(
            "SELECT reference_number FROM contracts WHERE duplicate_of = ?", (ref,))]
        own = kh.execute("SELECT duplicate_of FROM contracts"
                         " WHERE reference_number = ?", (ref,)).fetchone()
        if own is not None and own["duplicate_of"]:
            twins.append(own["duplicate_of"])
        seen = {e["adam"] for e in out}
        for t in twins:
            if t in seen:
                continue
            c = kh.execute(
                f"SELECT title, contract_signed_date, submission_date, cancelled"
                f"{_exclusion_cols(kh)} FROM contracts WHERE reference_number = ?",
                (t,)).fetchone()
            if c is None:
                continue
            d, basis = record_date(t, "contract",
                                   c["contract_signed_date"] or c["submission_date"])
            out.append({
                "adam": t, "kind": "contract", "d": d, "d_basis": basis,
                "title": (c["title"] or "")[:160] or None,
                "cancelled": c["cancelled"] or 0,
                "duplicate_of": _col(c, "duplicate_of"),
                "related_to": _col(c, "related_to"),
                "doc_kind": "contract", "in_db": True, "twin": True,
            })
    except sqlite3.OperationalError:
        pass

    out.sort(key=lambda e: (e["d"] or "9999",
                            _TIMELINE_ORDER.get(e["kind"], 9)))
    return out


# ------------------------------------------------- arogi (state fire aid)

def arogi_explore(ar: sqlite3.Connection) -> dict:
    """Compact rows for the /arogi client-filtered table: aid CASES plus
    πρώτη-αρωγή budget batches. Owner names are never present anywhere in
    the DB (DATA_DECISIONS 2026-08-03 privacy rule)."""
    fires = {r["fire_id"]: dict(r) for r in ar.execute(
        "SELECT fire_id, label, year FROM fires")}
    rows = []
    for r in ar.execute("""
        SELECT case_key, fire_id, pe, n_acts, first_date, last_date,
               approved_eur, dka_eur, loan_eur, status FROM cases"""):
        rows.append({
            "id": r["case_key"], "kind": "case",
            "d": r["first_date"], "d2": r["last_date"],
            "fire": fires.get(r["fire_id"], {}).get("label"),
            "fire_id": r["fire_id"], "pe": r["pe"],
            "n": r["n_acts"], "v": r["approved_eur"],
            "dka": r["dka_eur"], "loan": r["loan_eur"],
            "st": r["status"],
        })
    for r in ar.execute("""
        SELECT ada, label, fire_id, issue_date, budget_eur FROM batches"""):
        rows.append({
            "id": r["ada"], "kind": "batch",
            "d": r["issue_date"], "d2": None,
            "fire": fires.get(r["fire_id"], {}).get("label"),
            "fire_id": r["fire_id"], "pe": None,
            "n": 1, "v": r["budget_eur"], "dka": None, "loan": None,
            "st": "budget",
        })
    counts = {"cases": sum(1 for r in rows if r["kind"] == "case"),
              "batches": sum(1 for r in rows if r["kind"] == "batch")}
    return {"rows": rows, "counts": counts,
            "fires": sorted(fires.values(), key=lambda f: f["label"])}


def arogi_case(ar: sqlite3.Connection, key: str) -> dict | None:
    """One aid case with its full act trail (or a batch act)."""
    c = ar.execute("SELECT * FROM cases WHERE case_key = ?", (key,)).fetchone()
    if c is None:
        b = ar.execute("SELECT * FROM batches WHERE ada = ?", (key,)).fetchone()
        if b is None:
            return None
        out = dict(b)
        out["kind"] = "batch"
        f = ar.execute("SELECT label FROM fires WHERE fire_id = ?",
                       (b["fire_id"],)).fetchone()
        out["fire_label"] = f["label"] if f else None
        return out
    out = dict(c)
    out["kind"] = "case"
    f = ar.execute("SELECT label, year FROM fires WHERE fire_id = ?",
                   (c["fire_id"],)).fetchone()
    out["fire_label"] = f["label"] if f else None
    out["acts"] = [dict(a) for a in ar.execute("""
        SELECT ada, kind, issue_date, org, subject, ss_total_eur,
               ss_excerpt, dka_eur, loan_eur, fire_excerpt
        FROM acts WHERE case_key = ?
           OR (? LIKE 'ACT:%' AND ada = substr(?, 5))
        ORDER BY issue_date, ada""", (key, key, key))]
    return out


def arogi_summary(ar: sqlite3.Connection) -> dict:
    """Per-fire aggregates on every basis + the dual-source cross-check.

    Bases are never merged: Diavgeia-derived Σ.Σ. approvals / doses,
    πρώτη-αρωγή budget Πράξεις, official press running totals and ΕΛΓΑ
    yearly compensation are reported side by side; `press` carries the
    latest cumulative figure per (fire, stream)."""
    fires = [dict(r) for r in ar.execute(
        "SELECT * FROM fires WHERE in_scope = 1 ORDER BY year, fire_id")]
    per_fire = {f["fire_id"]: {
        "fire_id": f["fire_id"], "label": f["label"], "year": f["year"],
        "pes": json.loads(f["pes"] or "[]"),
        "n_cases": 0, "n_acts": 0, "approved_eur": 0.0, "dka_eur": 0.0,
        "completed": 0, "batch_budget_eur": 0.0, "press": [],
    } for f in fires}
    unattributed = {"n_cases": 0, "approved_eur": 0.0}
    for r in ar.execute("""
        SELECT fire_id, COUNT(*) AS n, SUM(n_acts) AS na,
               SUM(approved_eur) AS ap, SUM(dka_eur) AS dk,
               SUM(status = 'completed') AS done
        FROM cases GROUP BY fire_id"""):
        t = per_fire.get(r["fire_id"])
        if t is None:
            unattributed["n_cases"] += r["n"]
            unattributed["approved_eur"] += r["ap"] or 0.0
            continue
        t["n_cases"] = r["n"]
        t["n_acts"] = r["na"]
        t["approved_eur"] = round(r["ap"] or 0.0, 2)
        t["dka_eur"] = round(r["dk"] or 0.0, 2)
        t["completed"] = r["done"]
    for r in ar.execute("""
        SELECT fire_id, SUM(budget_eur) AS b FROM batches GROUP BY fire_id"""):
        if r["fire_id"] in per_fire:
            per_fire[r["fire_id"]]["batch_budget_eur"] = round(r["b"] or 0, 2)
    # latest CUMULATIVE announcement per (fire, stream); fires whose
    # announcements are batch-only fall back to their latest batch entry,
    # flagged so the page can label it (a missing running total is itself
    # a finding, never papered over)
    best: dict[tuple, dict] = {}
    for r in ar.execute("SELECT * FROM press_totals ORDER BY date"):
        if r["fire_id"] not in per_fire:
            continue
        key = (r["fire_id"], r["stream"])
        cur = best.get(key)
        if cur is None or r["cumulative"] >= cur["cumulative"]:
            best[key] = dict(r)
    for r in best.values():
        per_fire[r["fire_id"]]["press"].append(
            {k: r[k] for k in ("stream", "date", "eur", "beneficiaries",
                               "cumulative", "url", "quote")})
    elga = [dict(r) for r in ar.execute(
        "SELECT * FROM elga_yearly ORDER BY year")]
    stats = ar.execute("SELECT value FROM meta WHERE key='stats'").fetchone()
    return {
        "fires": list(per_fire.values()),
        "unattributed": unattributed,
        "elga": elga,
        "stats": json.loads(stats["value"]) if stats else {},
        "as_of": (ar.execute(
            "SELECT value FROM meta WHERE key='loaded_as_of'").fetchone()
            or [None])[0],
    }
