"""All SQL for the web UI. Each function returns plain dicts."""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path

from khmdhs.greek_regions import canonical_pe
from khmdhs.scope import normalize_title

# State-owned vehicles that manage the Anti-nero IV programme rather than
# execute it. Their contracts are upper-layer pass-through awards whose money
# is already represented in the downstream contracts to actual private
# contractors — counting both double-counts the same euros. Excluded from
# every dashboard-style aggregation below. Per-VAT and per-ADAM detail pages
# are untouched so direct URLs still resolve.
#   997104555 — Ε.Ε.ΣΥ.Π. Α.Ε. (HCAP) — 2 contracts, €528.77 M
#   997471299 — ΤΑΙΠΕΔ (HRADF)        — 6 contracts, €422.20 M
EXCLUDED_CONTRACTOR_VATS: tuple[str, ...] = ("997104555", "997471299")

_excluded_vat_list = ",".join(f"'{v}'" for v in EXCLUDED_CONTRACTOR_VATS)
EXCLUDED_REFS_SUBQUERY = (
    f"SELECT DISTINCT reference_number FROM contractors "
    f"WHERE vat_number IN ({_excluded_vat_list})"
)

# Anti-nero relevance filter. The contract_scope table (built by
# `python -m khmdhs.scope_loader`) marks in_scope = 1 only for verified
# Anti-nero execution contracts that are not superseded by a later
# modification. Everything else — routine forest-road maintenance, sibling
# programmes, umbrella pass-throughs, programme support services and
# superseded contract versions — is excluded from every aggregate below.
# Detail pages don't filter, so direct URLs still resolve.
SCOPE_REFS_SUBQUERY = "SELECT reference_number FROM contract_scope WHERE in_scope = 1"


def _has_scope_table(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_scope'"
    ).fetchone() is not None


def scope_filter(conn: sqlite3.Connection, col: str = "reference_number") -> str:
    """SQL predicate keeping only in-scope Anti-nero contracts.

    Falls back to the state-vehicle VAT exclusion when the scope table has
    not been built yet, so the UI stays usable on an older DB.
    """
    if _has_scope_table(conn):
        return f"{col} IN ({SCOPE_REFS_SUBQUERY})"
    return f"{col} NOT IN ({EXCLUDED_REFS_SUBQUERY})"


def _has_payments_table(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_payments'"
    ).fetchone() is not None


def effective_cost(conn: sqlite3.Connection, alias: str, col: str = "total_cost_with_vat") -> str:
    """SQL expression for a contract's effective value.

    When at least one non-cancelled payment order is attributed to the
    contract (payments of superseded versions follow the chain to the final
    version), the effective value is the sum of those payments — that is
    what was actually disbursed and it absorbs post-signature amendments.
    Contracts with no payments keep their stated value. Falls back to the
    stated value entirely when the payments table has not been built yet
    (`python -m khmdhs.payment_loader`).
    """
    if not _has_payments_table(conn):
        return f"{alias}.{col}"
    paid_col = "amount_with_vat" if col == "total_cost_with_vat" else "amount_without_vat"
    return (
        f"COALESCE((SELECT SUM(p.{paid_col}) FROM contract_payments p"
        f" WHERE p.attributed_ref = {alias}.reference_number AND p.cancelled = 0),"
        f" {alias}.{col})"
    )


def open_ro(db_path: Path) -> sqlite3.Connection:
    """Open the database read-only via SQLite URI."""
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def kpis(conn: sqlite3.Connection) -> dict:
    flt = scope_filter(conn, "co.reference_number")
    row = conn.execute(f"""
        SELECT
            COUNT(*) AS n_contracts,
            ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur,
            SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END) AS n_direct,
            SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder,
            SUM(CASE WHEN co.cancelled = 1 THEN 1 ELSE 0 END) AS n_cancelled
        FROM contracts co
        WHERE {flt}
    """).fetchone()
    flt_bare = scope_filter(conn)
    n_contractors = conn.execute(f"""
        SELECT COUNT(DISTINCT vat_number) FROM contractors
        WHERE {flt_bare}
    """).fetchone()[0]
    n_authorities = conn.execute(f"""
        SELECT COUNT(DISTINCT organization_name) FROM contracts
        WHERE {flt_bare}
    """).fetchone()[0]
    pct_direct = round(100.0 * row["n_direct"] / row["n_contracts"], 1) if row["n_contracts"] else 0
    return {
        "n_contracts": row["n_contracts"],
        "total_eur": row["total_eur"] or 0,
        "n_contractors": n_contractors,
        "n_authorities": n_authorities,
        "pct_direct": pct_direct,
        "n_single_bidder": row["n_single_bidder"],
        "n_cancelled": row["n_cancelled"],
    }


def top_contractors(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(f"""
        SELECT c.vat_number,
               MIN(c.name) AS name,
               COUNT(DISTINCT c.reference_number) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur,
               ROUND(100.0 * SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END)
                           / COUNT(*), 1) AS pct_direct,
               SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder
        FROM contractors c
        JOIN contracts   co USING (reference_number)
        WHERE {scope_filter(conn, 'c.reference_number')}
        GROUP BY c.vat_number
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_authorities(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.organization_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        WHERE co.organization_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.organization_name
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_signers(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        WHERE co.signer_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.signer_name
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Contractors list
# ---------------------------------------------------------------------------

_VALID_SORTS = {
    "total_eur": "total_eur DESC",
    "n_contracts": "n_contracts DESC",
    "pct_direct": "pct_direct DESC",
    "name": "name COLLATE NOCASE ASC",
}


def list_contractors(conn: sqlite3.Connection, q: str | None = None, sort: str = "total_eur") -> list[dict]:
    order = _VALID_SORTS.get(sort, _VALID_SORTS["total_eur"])
    excluded = scope_filter(conn, "c.reference_number")
    if q:
        where = f"WHERE {excluded} AND (c.vat_number LIKE ? OR LOWER(c.name) LIKE LOWER(?))"
        wild = f"%{q}%"
        params: tuple = (wild, wild)
    else:
        where = f"WHERE {excluded}"
        params = ()
    sql = f"""
        SELECT c.vat_number,
               MIN(c.name) AS name,
               GROUP_CONCAT(DISTINCT c.country) AS countries,
               COUNT(DISTINCT c.reference_number) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur,
               ROUND(100.0 * SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END)
                           / COUNT(*), 1) AS pct_direct,
               SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder
        FROM contractors c
        JOIN contracts   co USING (reference_number)
        {where}
        GROUP BY c.vat_number
        ORDER BY {order}
    """
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# Contracts list / search
# ---------------------------------------------------------------------------

def _search_norm(s: str | None) -> str:
    """Accent-insensitive, case-insensitive, Greek/Latin-homoglyph-tolerant
    form for substring search. "ευβοιας" matches "Π.Ε. Ευβοίας"; "antinero"
    matches both Latin "ANTINERO" and the Greek-typed titles.
    """
    decomposed = unicodedata.normalize("NFD", s or "")
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return normalize_title(stripped)


# Ordered rewrite rules mapping both Greeklish queries and (homoglyph-
# normalised) Greek text into one crude phonetic space, so "evias" finds
# «Ευβοίας» and "thessalonikis" finds «Θεσσαλονίκης». Digraphs first.
_PHONETIC_RULES = (
    ("CH", "X"), ("TH", "8"), ("Θ", "8"),
    ("EY", "EV"), ("AY", "AV"), ("OY", "U"), ("OU", "U"),
    ("OI", "I"), ("EI", "I"), ("AI", "E"),
    ("Γ", "G"), ("Δ", "D"), ("Λ", "L"), ("Ξ", "X"), ("Π", "P"),
    ("Σ", "S"), ("Φ", "F"), ("Ψ", "PS"), ("Ω", "O"),
    ("Y", "I"), ("H", "I"), ("B", "V"),
)


def _phonetic_fold(normed: str) -> str:
    """Fold a _search_norm() output into the shared phonetic space and
    collapse doubled letters ("EVVIAS" → "EVIAS")."""
    s = normed
    for a, b in _PHONETIC_RULES:
        s = s.replace(a, b)
    out = []
    for ch in s:
        if not out or out[-1] != ch or ch.isdigit():
            out.append(ch)
    return "".join(out)


def _matches(needle_norm: str, needle_fold: str, *haystacks: str | None) -> bool:
    for h in haystacks:
        hn = _search_norm(h)
        if needle_norm in hn or needle_fold in _phonetic_fold(hn):
            return True
    return False


def list_contracts(conn: sqlite3.Connection, q: str | None = None) -> list[dict]:
    """All in-scope contracts, newest first, optionally filtered by a free-text
    query matched against the ADAM, the title, the project regions and the
    contractor names. Matching happens in Python because SQLite's LIKE is
    ASCII-only-case-insensitive and the data mixes Greek and Latin homoglyphs.
    """
    rows = conn.execute(f"""
        SELECT k.reference_number,
               k.title,
               k.contract_signed_date,
               {effective_cost(conn, 'k')} AS total_cost_with_vat,
               k.total_cost_with_vat AS stated_cost_with_vat,
               {("(SELECT COUNT(*) FROM contract_payments p"
                 " WHERE p.attributed_ref = k.reference_number AND p.cancelled = 0)")
                if _has_payments_table(conn) else "0"} AS n_payments,
               k.bids_submitted,
               k.cancelled,
               s.scope,
               (SELECT GROUP_CONCAT(DISTINCT cpr.region_pe)
                  FROM contract_project_regions cpr
                 WHERE cpr.reference_number = k.reference_number) AS regions,
               (SELECT GROUP_CONCAT(c.name, ' | ')
                  FROM contractors c
                 WHERE c.reference_number = k.reference_number) AS contractor_names
        FROM contracts k
        LEFT JOIN contract_scope s USING (reference_number)
        WHERE {scope_filter(conn, 'k.reference_number')}
        ORDER BY k.contract_signed_date DESC, k.reference_number DESC
    """).fetchall()
    out = [dict(r) for r in rows]
    if q:
        needle = _search_norm(q)
        fold = _phonetic_fold(needle)
        out = [
            r for r in out
            if _matches(needle, fold, r["reference_number"], r["title"],
                        r["regions"], r["contractor_names"])
        ]
    return out


# ---------------------------------------------------------------------------
# Contractor detail
# ---------------------------------------------------------------------------

def contractor_summary(conn: sqlite3.Connection, vat: str) -> dict | None:
    row = conn.execute(f"""
        SELECT c.vat_number,
               GROUP_CONCAT(DISTINCT c.name) AS names,
               GROUP_CONCAT(DISTINCT c.country) AS countries,
               MAX(c.greek_vat) AS greek_vat,
               COUNT(DISTINCT c.reference_number) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur,
               ROUND(SUM({effective_cost(conn, 'co', 'total_cost_without_vat')}), 2) AS total_eur_no_vat,
               ROUND(100.0 * SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END)
                           / COUNT(*), 1) AS pct_direct,
               SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder,
               MIN(co.contract_signed_date) AS first_signed,
               MAX(co.contract_signed_date) AS last_signed
        FROM contractors c
        JOIN contracts   co USING (reference_number)
        WHERE c.vat_number = ?
          AND {scope_filter(conn, 'c.reference_number')}
        GROUP BY c.vat_number
    """, (vat,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    # # of contracts where this contractor was part of a consortium
    d["n_consortium"] = conn.execute(f"""
        SELECT COUNT(DISTINCT c1.reference_number)
        FROM contractors c1
        WHERE c1.vat_number = ?
          AND {scope_filter(conn, 'c1.reference_number')}
          AND (SELECT COUNT(*) FROM contractors c2 WHERE c2.reference_number = c1.reference_number) > 1
    """, (vat,)).fetchone()[0]
    return d


def contractor_contracts(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.reference_number,
               co.title,
               co.contract_signed_date,
               co.start_date,
               {effective_cost(conn, 'co')} AS total_cost_with_vat,
               co.total_cost_with_vat AS stated_cost_with_vat,
               co.procedure_type,
               co.bids_submitted,
               co.organization_name,
               co.units_operator_name,
               co.signer_name,
               co.cancelled,
               (SELECT COUNT(*) FROM contractors c2
                WHERE c2.reference_number = co.reference_number) AS n_partners
        FROM contracts co
        JOIN contractors c USING (reference_number)
        WHERE c.vat_number = ?
          AND {scope_filter(conn, 'co.reference_number')}
        ORDER BY co.contract_signed_date DESC, co.reference_number DESC
    """, (vat,)).fetchall()
    return [dict(r) for r in rows]


def consortium_partners(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute(f"""
        SELECT c2.vat_number,
               MIN(c2.name) AS name,
               COUNT(DISTINCT c2.reference_number) AS shared_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS shared_eur
        FROM contractors c1
        JOIN contractors c2 USING (reference_number)
        JOIN contracts   co USING (reference_number)
        WHERE c1.vat_number = ? AND c2.vat_number != ?
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY c2.vat_number
        ORDER BY shared_eur DESC
    """, (vat, vat)).fetchall()
    return [dict(r) for r in rows]


def contractor_signers(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        JOIN contractors c USING (reference_number)
        WHERE c.vat_number = ? AND co.signer_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.signer_name
        ORDER BY total_eur DESC
    """, (vat,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Contract detail
# ---------------------------------------------------------------------------

def contract_detail(conn: sqlite3.Connection, adam: str) -> dict | None:
    row = conn.execute("SELECT * FROM contracts WHERE reference_number = ?", (adam,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["raw_pretty"] = ""
    if d.get("raw_json"):
        try:
            d["raw_pretty"] = json.dumps(json.loads(d["raw_json"]), ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            pass
    d["contractors"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM contractors WHERE reference_number = ? ORDER BY seq", (adam,)
        ).fetchall()
    ]
    d["cpvs"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM contract_cpvs WHERE reference_number = ? ORDER BY seq", (adam,)
        ).fetchall()
    ]
    d["nuts"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM contract_nuts WHERE reference_number = ? ORDER BY seq", (adam,)
        ).fetchall()
    ]
    d["objects"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM contract_objects WHERE reference_number = ? ORDER BY seq", (adam,)
        ).fetchall()
    ]
    d["payments"] = []
    d["paid_with_vat"] = None
    d["paid_without_vat"] = None
    if _has_payments_table(conn):
        d["payments"] = [
            dict(r) for r in conn.execute(
                """SELECT payment_ref, contract_ref, attributed_ref, title,
                          signed_date, cancelled, credit, correction_note,
                          source, ada,
                          amount_without_vat, amount_with_vat
                     FROM contract_payments
                    WHERE attributed_ref = ? OR contract_ref = ?
                    ORDER BY COALESCE(signed_date, submission_date), payment_ref""",
                (adam, adam),
            ).fetchall()
        ]
        live = [p for p in d["payments"] if not p["cancelled"]]
        if live:
            d["paid_with_vat"] = round(sum(p["amount_with_vat"] or 0 for p in live), 2)
            d["paid_without_vat"] = round(sum(p["amount_without_vat"] or 0 for p in live), 2)
    d["effective_cost_with_vat"] = (
        d["paid_with_vat"] if d["paid_with_vat"] is not None else d["total_cost_with_vat"]
    )
    d["scope"] = None
    if _has_scope_table(conn):
        row = conn.execute(
            "SELECT scope, in_scope, superseded_by, basis FROM contract_scope "
            "WHERE reference_number = ?", (adam,)
        ).fetchone()
        if row is not None:
            d["scope"] = dict(row)
    return d


# ---------------------------------------------------------------------------
# Authorities / signers / unit operators
# ---------------------------------------------------------------------------

def list_authorities(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.organization_name AS name,
               co.organization_vat AS vat,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        WHERE co.organization_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.organization_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_unit_operators(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.units_operator_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        WHERE co.units_operator_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.units_operator_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_signers(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT co.signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contracts co
        WHERE co.signer_name IS NOT NULL
          AND {scope_filter(conn, 'co.reference_number')}
        GROUP BY co.signer_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Project regions + contractor locations (manual curation)
# ---------------------------------------------------------------------------

def contract_project_regions(conn: sqlite3.Connection, adam: str) -> list[dict]:
    """Curated project-site regions for one contract, ordered by seq."""
    rows = conn.execute(
        """SELECT region_pe, nuts3_code, note, source, curated_at
             FROM contract_project_regions
            WHERE reference_number = ?
            ORDER BY seq""",
        (adam,),
    ).fetchall()
    return [dict(r) for r in rows]


def contract_sites(conn: sqlite3.Connection, adam: str) -> list[dict]:
    """Curated sub-Π.Ε. work sites for one contract (with PDF page evidence)."""
    has = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_sites'"
    ).fetchone()
    if not has:
        return []
    rows = conn.execute(
        """SELECT site_name, region_pe, page, excerpt
             FROM contract_sites WHERE reference_number = ? ORDER BY seq""",
        (adam,),
    ).fetchall()
    return [dict(r) for r in rows]


def region_flows(
    conn: sqlite3.Connection,
    target_pe: str | None = None,
    source_pe: str | None = None,
) -> list[dict]:
    """Aggregated source→target region flows, in €.

    A flow is a (contractor home Π.Ε.) → (project site Π.Ε.) pair, summed
    across every contract where:
      - the contractor's VAT has a resolved region_pe in contractor_locations
      - the contract has at least one project_region in contract_project_regions
      - the contract is not awarded to one of the EXCLUDED_CONTRACTOR_VATS

    Each contract's full total_cost_with_vat is attributed to *every*
    (contractor's region × project region) pair — the same "maximum
    exposure" convention used everywhere else in this app.

    Coverage caveat: only ~18 of 137 contractors currently have a resolved
    region_pe, so this aggregation undercounts. The UI surfaces the gap.
    """
    params: list = list(EXCLUDED_CONTRACTOR_VATS)
    where = [
        "c.vat_number NOT IN (?, ?)",
        "cl.region_pe IS NOT NULL",
        scope_filter(conn, "co.reference_number"),
    ]
    if target_pe:
        where.append("cpr.region_pe = ?")
        params.append(target_pe)
    if source_pe:
        where.append("cl.region_pe = ?")
        params.append(source_pe)
    sql = f"""
        SELECT cl.region_pe   AS source_pe,
               cpr.region_pe  AS target_pe,
               COUNT(DISTINCT co.reference_number)   AS n_contracts,
               ROUND(SUM({effective_cost(conn, 'co')}), 2) AS total_eur
        FROM contractors c
        JOIN contractor_locations cl      ON cl.vat_number = c.vat_number
        JOIN contracts co                 ON co.reference_number = c.reference_number
        JOIN contract_project_regions cpr ON cpr.reference_number = co.reference_number
        WHERE {' AND '.join(where)}
        GROUP BY cl.region_pe, cpr.region_pe
        ORDER BY total_eur DESC
    """
    out = []
    for r in conn.execute(sql, params).fetchall():
        d = dict(r)
        d["source_pe"] = canonical_pe(d["source_pe"]) or d["source_pe"]
        d["target_pe"] = canonical_pe(d["target_pe"]) or d["target_pe"]
        out.append(d)
    return out


def flow_coverage(conn: sqlite3.Connection) -> dict:
    """How much of the total contract € the resolved-source flows account for.

    Returns:
        resolved_eur:    € attributable to contracts where ≥1 contractor has region_pe
        unresolved_eur:  € in contracts where NO contractor has a resolved region_pe
        total_eur:       resolved + unresolved
        n_contractors_resolved / n_contractors_total
    """
    flt = scope_filter(conn, "co.reference_number")
    total_eur = conn.execute(f"""
        SELECT ROUND(SUM({effective_cost(conn, 'co')}), 2) FROM contracts co
        WHERE {flt}
    """).fetchone()[0] or 0

    resolved_eur = conn.execute(f"""
        SELECT ROUND(SUM({effective_cost(conn, 'co')}), 2)
        FROM contracts co
        WHERE {flt}
          AND co.reference_number IN (
              SELECT DISTINCT c.reference_number
              FROM contractors c
              JOIN contractor_locations cl ON cl.vat_number = c.vat_number
              WHERE cl.region_pe IS NOT NULL
          )
    """).fetchone()[0] or 0

    n_contractors_total = conn.execute("""
        SELECT COUNT(DISTINCT vat_number) FROM contractors
        WHERE vat_number NOT IN (?, ?)
    """, EXCLUDED_CONTRACTOR_VATS).fetchone()[0]

    n_contractors_resolved = conn.execute("""
        SELECT COUNT(*) FROM contractor_locations WHERE region_pe IS NOT NULL
    """).fetchone()[0]

    return {
        "resolved_eur": resolved_eur,
        "unresolved_eur": max(0, total_eur - resolved_eur),
        "total_eur": total_eur,
        "n_contractors_resolved": n_contractors_resolved,
        "n_contractors_total": n_contractors_total,
    }


def project_region_origins(conn: sqlite3.Connection) -> list[dict]:
    """For each project Π.Ε., split contract € into local vs imported vs unknown.

    "Local" = contractor home Π.Ε. is the same as project Π.Ε.
    "Imported" = contractor home Π.Ε. is known but different.
    "Unknown" = contractor's region_pe is null.

    Returns one row per target Π.Ε. with the three components in €. Counts
    each (contractor, project-region) pairing as one slice of the contract
    value, so consortia and multi-region contracts are spread out by
    contractor count.
    """
    rows = conn.execute(f"""
        WITH per_contract_pair AS (
            SELECT
                cpr.region_pe                  AS target_pe,
                co.reference_number,
                {effective_cost(conn, 'co')}   AS contract_eur,
                COUNT(c.vat_number)            AS n_contractors,
                SUM(CASE WHEN cl.region_pe = cpr.region_pe THEN 1 ELSE 0 END) AS n_local,
                SUM(CASE WHEN cl.region_pe IS NOT NULL AND cl.region_pe <> cpr.region_pe THEN 1 ELSE 0 END) AS n_imported,
                SUM(CASE WHEN cl.region_pe IS NULL THEN 1 ELSE 0 END) AS n_unknown
            FROM contract_project_regions cpr
            JOIN contracts co              ON co.reference_number = cpr.reference_number
            JOIN contractors c             ON c.reference_number = co.reference_number
            LEFT JOIN contractor_locations cl ON cl.vat_number = c.vat_number
            WHERE c.vat_number NOT IN ({','.join('?' * len(EXCLUDED_CONTRACTOR_VATS))})
              AND {scope_filter(conn, 'co.reference_number')}
            GROUP BY cpr.region_pe, co.reference_number
        )
        SELECT target_pe,
               COUNT(DISTINCT reference_number) AS n_contracts,
               ROUND(SUM(contract_eur), 2)                                   AS total_eur,
               ROUND(SUM(contract_eur * n_local    * 1.0 / n_contractors), 2) AS local_eur,
               ROUND(SUM(contract_eur * n_imported * 1.0 / n_contractors), 2) AS imported_eur,
               ROUND(SUM(contract_eur * n_unknown  * 1.0 / n_contractors), 2) AS unknown_eur
        FROM per_contract_pair
        GROUP BY target_pe
        ORDER BY total_eur DESC
    """, EXCLUDED_CONTRACTOR_VATS).fetchall()
    return [dict(r) for r in rows]


def contractor_location(conn: sqlite3.Connection, vat: str) -> dict | None:
    """Curated home location for one contractor, or None if not present.

    The VAT key may carry leading/trailing whitespace in the contractors
    table (data-quality artefact). We try the raw value first, then the
    stripped variant.
    """
    for candidate in (vat, vat.strip(), f" {vat.strip()}", f"{vat.strip()} "):
        row = conn.execute(
            "SELECT * FROM contractor_locations WHERE vat_number = ?",
            (candidate,),
        ).fetchone()
        if row is not None:
            return dict(row)
    return None


# ---------------------------------------------------------------------------
# Dashboard analytics: disbursement over time + direct-award distribution
# ---------------------------------------------------------------------------

def _payment_month(signed_date: str | None) -> str | None:
    """Normalise the two date formats KHMDHS payments carry — '03/11/2023'
    and '2026-07-24T00:00:00' — into 'YYYY-MM'. None when absent/unparsable."""
    if not signed_date:
        return None
    s = signed_date.strip()
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        return f"{s[6:10]}-{s[3:5]}"
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return None


def disbursement_timeseries(conn: sqlite3.Connection) -> dict:
    """Cumulative payment-order totals per month, split by programme scope.

    Only non-cancelled payments attributed to in-scope contracts count —
    the same population as every other aggregate. Undated payments are
    excluded from the curve and reported in `undated` / `undated_eur`.
    """
    if not _has_payments_table(conn) or not _has_scope_table(conn):
        return {"months": [], "series": {}, "undated": 0, "undated_eur": 0.0}
    rows = conn.execute(f"""
        SELECT p.signed_date, p.submission_date, s.scope, p.amount_with_vat
        FROM contract_payments p
        JOIN contract_scope s ON s.reference_number = p.attributed_ref
        WHERE p.cancelled = 0 AND p.attributed_ref IN ({SCOPE_REFS_SUBQUERY})
    """).fetchall()

    monthly: dict[str, dict[str, float]] = {}
    undated, undated_eur = 0, 0.0
    scopes: set[str] = set()
    for signed_date, submission_date, scope, amount in rows:
        # signed date preferred; KHMDHS submission date as fallback (~20% of
        # orders carry no signed date but were registered promptly).
        month = _payment_month(signed_date) or _payment_month(submission_date)
        if month is None:
            undated += 1
            undated_eur += amount or 0.0
            continue
        scopes.add(scope)
        monthly.setdefault(month, {})
        monthly[month][scope] = monthly[month].get(scope, 0.0) + (amount or 0.0)

    months = sorted(monthly)
    series: dict[str, list[float]] = {}
    for scope in sorted(scopes):
        total = 0.0
        acc = []
        for m in months:
            total += monthly[m].get(scope, 0.0)
            acc.append(round(total, 2))
        series[scope] = acc
    return {"months": months, "series": series,
            "undated": undated, "undated_eur": round(undated_eur, 2)}


# Bin edges (EUR incl. VAT) for the direct-award histogram. 30k and 60k are
# deliberately edges: they are the ν.4782/2021 direct-award ceilings
# (supplies/services and works respectively).
DIRECT_AWARD_BIN_EDGES = (
    0, 10_000, 20_000, 30_000, 40_000, 50_000, 60_000, 80_000, 100_000,
    150_000, 200_000, 300_000, 500_000, 1_000_000, 2_000_000, 5_000_000,
    10_000_000,
)


def direct_award_distribution(conn: sqlite3.Connection) -> dict:
    """Histogram of in-scope direct-award contract values (effective)."""
    rows = conn.execute(f"""
        SELECT {effective_cost(conn, 'k')} AS v
        FROM contracts k
        WHERE {scope_filter(conn, 'k.reference_number')}
          AND k.procedure_type LIKE 'Απευθείας%'
    """).fetchall()
    values = [r[0] or 0.0 for r in rows]

    edges = DIRECT_AWARD_BIN_EDGES
    counts = [0] * len(edges)          # last bucket = > edges[-1]
    for v in values:
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1]:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    labels = [f"{edges[i] // 1000}–{edges[i + 1] // 1000}k"
              for i in range(len(edges) - 1)] + [f">{edges[-1] // 1_000_000}M"]
    return {"labels": labels, "counts": counts, "edges": list(edges),
            "n": len(values), "total_eur": round(sum(values), 2),
            "thresholds": [30_000, 60_000]}


# ---------------------------------------------------------------------------
# Overview page: money geography (even-split convention) + structure charts
# ---------------------------------------------------------------------------
# Split convention (user decision, DATA_DECISIONS.md 2026-07-25): a contract's
# effective value is divided evenly across its N project regions (resp. its
# located consortium partners) so regions sum to the programme total; each
# region's full exposure (Σ of whole contracts touching it) is reported
# alongside. Neither KHMDHS objects nor the contract PDFs itemise per-region
# amounts, so the split is an explicit estimate.

def money_by_project_region(conn: sqlite3.Connection) -> list[dict]:
    """Per project Π.Ε.: contracts, split €, exposure €.

    Aggregated by the canonical Π.Ε. name (the map's polygon key) — spelling
    variants (Πρεβέζης/Πρέβεζας) collapse; distinct Π.Ε. never merge.
    """
    rows = conn.execute(f"""
        SELECT k.reference_number, {effective_cost(conn, 'k')} AS eff,
               cpr.region_pe
        FROM contracts k
        JOIN contract_project_regions cpr USING (reference_number)
        WHERE {scope_filter(conn, 'k.reference_number')}
    """).fetchall()

    by_contract: dict[str, list] = {}
    for r in rows:
        by_contract.setdefault(r["reference_number"], []).append(r)

    agg: dict[str, dict] = {}
    for regions in by_contract.values():
        eff = regions[0]["eff"] or 0.0
        n = len(regions)
        seen_pe: set[str] = set()
        for r in regions:
            pe = canonical_pe(r["region_pe"]) or r["region_pe"]
            a = agg.setdefault(pe, {
                "pe": pe, "n_contracts": 0,
                "split_eur": 0.0, "exposure_eur": 0.0,
            })
            a["split_eur"] += eff / n
            if pe not in seen_pe:
                seen_pe.add(pe)
                a["n_contracts"] += 1
                a["exposure_eur"] += eff
    out = []
    for a in agg.values():
        a["split_eur"] = round(a["split_eur"], 2)
        a["exposure_eur"] = round(a["exposure_eur"], 2)
        out.append(a)
    return sorted(out, key=lambda a: -a["split_eur"])


def money_by_contractor_region(conn: sqlite3.Connection) -> list[dict]:
    """Per contractor-home Π.Ε.: contractors, split €, exposure €.

    Each contract's effective value splits evenly across its *located*
    partners; the unlocated remainder is reported by flow_coverage().
    """
    rows = conn.execute(f"""
        SELECT k.reference_number, {effective_cost(conn, 'k')} AS eff,
               c.vat_number, cl.region_pe
        FROM contracts k
        JOIN contractors c USING (reference_number)
        JOIN contractor_locations cl ON cl.vat_number = c.vat_number
        WHERE cl.region_pe IS NOT NULL
          AND {scope_filter(conn, 'k.reference_number')}
    """).fetchall()

    by_contract: dict[str, list] = {}
    for r in rows:
        by_contract.setdefault(r["reference_number"], []).append(r)

    agg: dict[str, dict] = {}
    contractors_by_pe: dict[str, set] = {}
    for partners in by_contract.values():
        eff = partners[0]["eff"] or 0.0
        n_located = len({p["vat_number"] for p in partners})
        seen_pe: set[str] = set()
        for p in partners:
            pe = canonical_pe(p["region_pe"]) or p["region_pe"]
            a = agg.setdefault(pe, {
                "pe": pe, "n_contracts": 0,
                "split_eur": 0.0, "exposure_eur": 0.0,
            })
            a["split_eur"] += eff / n_located
            contractors_by_pe.setdefault(pe, set()).add(p["vat_number"])
            if pe not in seen_pe:
                seen_pe.add(pe)
                a["n_contracts"] += 1
                a["exposure_eur"] += eff
    out = []
    for pe, a in agg.items():
        a["n_contractors"] = len(contractors_by_pe[pe])
        a["split_eur"] = round(a["split_eur"], 2)
        a["exposure_eur"] = round(a["exposure_eur"], 2)
        out.append(a)
    return sorted(out, key=lambda a: -a["split_eur"])


def contract_authority_points(conn: sqlite3.Connection) -> list[dict]:
    """One point per (in-scope contract × forest authority): the works dot
    map. Coordinates are the authority's seat-municipality centroid."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='contract_forest_authorities'").fetchone():
        return []
    rows = conn.execute(f"""
        SELECT k.reference_number AS ref, k.title,
               {effective_cost(conn, 'k')} AS eff_eur,
               fa.name AS authority, fa.kind, fa.lat, fa.lon, fa.region_pe
        FROM contracts k
        JOIN contract_forest_authorities cfa
             ON cfa.reference_number = k.reference_number
        JOIN forest_authorities fa ON fa.name = cfa.authority_name
        WHERE fa.lat IS NOT NULL
          AND {scope_filter(conn, 'k.reference_number')}
        ORDER BY fa.name, k.reference_number
    """).fetchall()
    return [{"ref": r["ref"], "title": r["title"], "authority": r["authority"],
             "kind": r["kind"], "lat": r["lat"], "lon": r["lon"],
             "pe": canonical_pe(r["region_pe"]) or r["region_pe"],
             "eff_eur": round(r["eff_eur"] or 0.0, 2)}
            for r in rows]


def overview_contracts(conn: sqlite3.Connection) -> list[dict]:
    """Compact per-contract join payload for the /overview drill-down:
    contractors, forest authorities and even-split region shares — small
    enough (252 rows) to ship once and filter client-side."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='contract_forest_authorities'").fetchone():
        return []
    base = conn.execute(f"""
        SELECT k.reference_number AS ref, k.title,
               {effective_cost(conn, 'k')} AS eff
        FROM contracts k
        WHERE {scope_filter(conn, 'k.reference_number')}
    """).fetchall()
    out: dict[str, dict] = {}
    for r in base:
        out[r["ref"]] = {"ref": r["ref"], "title": r["title"],
                         "eff_eur": round(r["eff"] or 0.0, 2),
                         "contractors": [], "authorities": [], "regions": []}
    for r in conn.execute("""
            SELECT c.reference_number AS ref, c.vat_number,
                   COALESCE(cl.legal_name, c.name) AS name
            FROM contractors c
            LEFT JOIN contractor_locations cl ON cl.vat_number = c.vat_number
            ORDER BY c.reference_number, c.seq"""):
        if r["ref"] in out:
            out[r["ref"]]["contractors"].append(
                {"vat": r["vat_number"], "name": r["name"]})
    for r in conn.execute("""
            SELECT reference_number AS ref, authority_name
            FROM contract_forest_authorities ORDER BY reference_number, seq"""):
        if r["ref"] in out:
            out[r["ref"]]["authorities"].append(r["authority_name"])
    region_rows = conn.execute("""
            SELECT reference_number AS ref, region_pe
            FROM contract_project_regions ORDER BY reference_number, seq
    """).fetchall()
    by_ref: dict[str, list] = {}
    for r in region_rows:
        if r["ref"] in out:
            by_ref.setdefault(r["ref"], []).append(r)
    for ref, regions in by_ref.items():
        eff = out[ref]["eff_eur"]
        n = len(regions)
        merged: dict[str, dict] = {}
        for r in regions:
            pe = canonical_pe(r["region_pe"]) or r["region_pe"]
            m = merged.setdefault(pe, {"pe": pe, "split_eur": 0.0})
            m["split_eur"] += eff / n
        out[ref]["regions"] = [
            {"pe": m["pe"], "split_eur": round(m["split_eur"], 2)}
            for m in merged.values()]
    return sorted(out.values(), key=lambda c: -c["eff_eur"])


def study_costs(conn: sqlite3.Connection) -> dict:
    """Per-contract μελέτη (study/planning) cost, net of ΦΠΑ, attributed to
    in-scope chain tips: a tip uses its own extracted row when present,
    else the nearest predecessor's (the signed original carries the Άρθρο 4
    breakdown; ΑΠΕ restatements may update it). Shares are computed against
    the contract's stated NET total — same ΦΠΑ basis on both sides."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='contract_study_costs'").fetchone():
        return {"rows": [], "summary": {"n_with": 0, "n_in_scope": 0,
                                        "total_eur": 0.0, "median_share": None}}
    study = {r["reference_number"]: dict(r) for r in conn.execute(
        "SELECT reference_number, eur, page FROM contract_study_costs")}
    prev = {r[0]: r[1] for r in conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts")}
    net_of = {r[0]: r[1] for r in conn.execute(
        "SELECT reference_number, total_cost_without_vat FROM contracts")}

    def family_net(ref: str) -> float | None:
        # Supplementary/ΑΠΕ tips state only their own (small) value — the
        # honest share denominator is the largest net value in the chain.
        best, hops = None, 0
        while ref is not None and hops < 12:
            v = net_of.get(ref)
            if v and (best is None or v > best):
                best = v
            ref = prev.get(ref)
            hops += 1
        return best
    tips = conn.execute(f"""
        SELECT k.reference_number AS ref, k.title,
               k.total_cost_without_vat AS net_stated,
               {effective_cost(conn, 'k')} AS eff
        FROM contracts k
        WHERE {scope_filter(conn, 'k.reference_number')}
    """).fetchall()

    rows, shares = [], []
    for t in tips:
        ref, hops = t["ref"], 0
        while ref is not None and ref not in study and hops < 12:
            ref = prev.get(ref)
            hops += 1
        if ref is None or ref not in study:
            continue
        s = study[ref]
        denom = family_net(t["ref"])
        share = s["eur"] / denom if denom else None
        if share is not None:
            shares.append(share)
        rows.append({"ref": t["ref"], "title": t["title"],
                     "eur": round(s["eur"], 2), "src_ref": ref,
                     "eff_eur": round(t["eff"] or 0.0, 2),
                     "share": round(share, 4) if share is not None else None})
    rows.sort(key=lambda r: -r["eur"])
    shares.sort()
    return {"rows": rows, "summary": {
        "n_with": len(rows), "n_in_scope": len(tips),
        "total_eur": round(sum(r["eur"] for r in rows), 2),
        "net_stated_total": round(
            sum(t["net_stated"] or 0.0 for t in tips), 2),
        "median_share": round(shares[len(shares) // 2], 4) if shares else None,
    }}


def contractor_points(conn: sqlite3.Connection) -> dict:
    """Geocoded contractor HQ dots + coverage. Totals are max-exposure
    (full contract value per partner), consistent with /contractors."""
    has_geo = bool(conn.execute(
        "SELECT 1 FROM pragma_table_info('contractor_locations') "
        "WHERE name = 'lat'").fetchone())
    if not has_geo:
        return {"points": [], "coverage": {"n_with_coords": 0,
                                           "n_total": 0, "unmapped_eur": 0.0}}
    rows = conn.execute(f"""
        SELECT c.vat_number, MAX(COALESCE(cl.legal_name, c.name)) AS name,
               cl.lat, cl.lon, cl.geo_precision, cl.region_pe,
               COUNT(DISTINCT k.reference_number) AS n_contracts,
               SUM(eff) AS total_eur
        FROM (SELECT k.reference_number, {effective_cost(conn, 'k')} AS eff
              FROM contracts k
              WHERE {scope_filter(conn, 'k.reference_number')}) k
        JOIN contractors c USING (reference_number)
        LEFT JOIN contractor_locations cl ON cl.vat_number = c.vat_number
        GROUP BY c.vat_number
    """).fetchall()
    points, n_total, with_coords = [], 0, set()
    for r in rows:
        n_total += 1
        if r["lat"] is not None:
            with_coords.add(r["vat_number"])
            points.append({"vat": r["vat_number"], "name": r["name"],
                           "lat": r["lat"], "lon": r["lon"],
                           "pe": canonical_pe(r["region_pe"]) or r["region_pe"],
                           "precision": r["geo_precision"],
                           "n_contracts": r["n_contracts"],
                           "total_eur": round(r["total_eur"] or 0.0, 2)})
    unmapped = conn.execute(f"""
        SELECT COALESCE(SUM(eff), 0) FROM
          (SELECT k.reference_number, {effective_cost(conn, 'k')} AS eff
           FROM contracts k
           WHERE {scope_filter(conn, 'k.reference_number')}
             AND NOT EXISTS (SELECT 1 FROM contractors c
                             JOIN contractor_locations cl
                               ON cl.vat_number = c.vat_number
                             WHERE c.reference_number = k.reference_number
                               AND cl.lat IS NOT NULL))
    """).fetchone()[0]
    points.sort(key=lambda p: -p["total_eur"])
    return {"points": points,
            "coverage": {"n_with_coords": len(with_coords), "n_total": n_total,
                         "unmapped_eur": round(unmapped or 0.0, 2)}}


def _bin_values(values: list[float], edges: tuple) -> dict:
    """Histogram counts over half-open bins [e_i, e_{i+1}), overflow last."""
    counts = [0] * len(edges)
    for v in values:
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1]:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    return {"edges": list(edges), "counts": counts, "n": len(values),
            "total_eur": round(sum(values), 2)}


# Log-spaced (doubling) bins: contract values are roughly log-normal, so
# equal-width linear bins distort the picture (a €2M-wide bar collects twice
# what a €1M-wide one does). With each bin spanning one doubling of value,
# bar heights are directly comparable and the distribution reads honestly.
VALUE_BIN_EDGES = (
    0, 100_000, 200_000, 400_000, 800_000,
    1_600_000, 3_200_000, 6_400_000,
)


def contract_value_histogram(conn: sqlite3.Connection) -> dict:
    """Histogram of every in-scope contract's effective value, on
    log-spaced doubling bins (the final bin is an open ≥ overflow)."""
    values = [r[0] or 0.0 for r in conn.execute(f"""
        SELECT {effective_cost(conn, 'k')} FROM contracts k
        WHERE {scope_filter(conn, 'k.reference_number')}
    """)]
    h = _bin_values(values, VALUE_BIN_EDGES)
    values.sort()
    h["median"] = values[len(values) // 2] if values else 0
    edges = VALUE_BIN_EDGES

    def short(v):
        if v >= 1_000_000:
            m = v / 1_000_000
            return f"{m:g}M".replace(".", ",")   # 1,6M not 1M
        return f"{v // 1000}k"
    h["labels"] = ([f"≤{short(edges[1])}"] +
                   [f"{short(edges[i])}–{short(edges[i + 1])}"
                    for i in range(1, len(edges) - 1)] +
                   [f"≥{short(edges[-1])}"])
    return h


def procedure_mix(conn: sqlite3.Connection) -> list[dict]:
    """Canonical procedure-type groups with contract counts and effective €.

    KHMDHS stores variants with legal-article suffixes («Απευθείας ανάθεση
    (αρ.118/αρ. 328)») — collapse them into stable groups.
    """
    rows = conn.execute(f"""
        SELECT k.procedure_type, COUNT(*) AS n,
               ROUND(SUM({effective_cost(conn, 'k')}), 2) AS eur
        FROM contracts k
        WHERE {scope_filter(conn, 'k.reference_number')}
        GROUP BY k.procedure_type
    """).fetchall()
    groups: dict[str, dict] = {}
    for r in rows:
        raw = (r["procedure_type"] or "").strip()
        if raw.startswith("Απευθείας"):
            label = "Απευθείας ανάθεση"
        elif "Διαπραγμάτευση" in raw:
            label = "Διαπραγμάτευση χωρίς δημοσίευση"
        elif raw.startswith("Ανοιχτή") or raw.startswith("Ανοικτή"):
            label = "Ανοιχτή διαδικασία"
        else:
            label = raw or "Άγνωστη"
        g = groups.setdefault(label, {"label": label, "n_contracts": 0, "eur": 0.0})
        g["n_contracts"] += r["n"]
        g["eur"] = round(g["eur"] + (r["eur"] or 0.0), 2)
    return sorted(groups.values(), key=lambda g: -g["n_contracts"])


# ---------------------------------------------------------------------------
# Contractor drill-down: map data + money per year
# ---------------------------------------------------------------------------

def contractor_map_data(conn: sqlite3.Connection, vat: str) -> dict:
    """Home location + per-project-region split € for one contractor."""
    home = contractor_location(conn, vat)
    rows = conn.execute(f"""
        SELECT k.reference_number, {effective_cost(conn, 'k')} AS eff,
               cpr.region_pe
        FROM contractors c
        JOIN contracts k USING (reference_number)
        JOIN contract_project_regions cpr ON cpr.reference_number = k.reference_number
        WHERE c.vat_number IN (?, ?)
          AND {scope_filter(conn, 'k.reference_number')}
    """, (vat, vat.strip())).fetchall()

    by_contract: dict[str, list] = {}
    for r in rows:
        by_contract.setdefault(r["reference_number"], []).append(r)
    agg: dict[str, dict] = {}
    for regions in by_contract.values():
        eff = regions[0]["eff"] or 0.0
        n = len(regions)
        seen: set[str] = set()
        for r in regions:
            pe = canonical_pe(r["region_pe"]) or r["region_pe"]
            a = agg.setdefault(pe, {
                "pe": pe, "n_contracts": 0, "split_eur": 0.0,
            })
            a["split_eur"] += eff / n
            if pe not in seen:
                seen.add(pe)
                a["n_contracts"] += 1
    regions_out = []
    for a in agg.values():
        a["split_eur"] = round(a["split_eur"], 2)
        regions_out.append(a)
    return {
        "home": {
            "pe": canonical_pe(home.get("region_pe")) or home.get("region_pe"),
            "city": home.get("city"),
            "lat": home.get("lat"),
            "lon": home.get("lon"),
            "precision": home.get("geo_precision"),
        } if home else None,
        "regions": sorted(regions_out, key=lambda a: -a["split_eur"]),
    }


def _year_of(*dates: str | None) -> str | None:
    for d in dates:
        m = _payment_month(d)
        if m:
            return m[:4]
    return None


def contractor_yearly(conn: sqlite3.Connection, vat: str) -> dict:
    """€ per year for one contractor: paid (payment orders) + stated value
    of contracts that have no payments yet (keyed to their signature year)."""
    contracts = conn.execute(f"""
        SELECT k.reference_number, k.contract_signed_date, k.submission_date,
               k.total_cost_with_vat AS stated,
               (SELECT COUNT(*) FROM contract_payments p
                 WHERE p.attributed_ref = k.reference_number AND p.cancelled = 0)
                 AS n_payments
        FROM contractors c JOIN contracts k USING (reference_number)
        WHERE c.vat_number IN (?, ?)
          AND {scope_filter(conn, 'k.reference_number')}
    """, (vat, vat.strip())).fetchall() if _has_payments_table(conn) else []

    years: dict[str, dict] = {}

    def bucket(year):
        return years.setdefault(year, {"year": year, "paid_eur": 0.0,
                                       "stated_eur": 0.0, "n_payments": 0})

    refs = [r["reference_number"] for r in contracts]
    if refs:
        placeholders = ",".join("?" * len(refs))
        for p in conn.execute(f"""
            SELECT signed_date, submission_date, amount_with_vat
            FROM contract_payments
            WHERE cancelled = 0 AND attributed_ref IN ({placeholders})
        """, refs):
            y = _year_of(p["signed_date"], p["submission_date"])
            if y is None:
                continue
            b = bucket(y)
            b["paid_eur"] += p["amount_with_vat"] or 0.0
            b["n_payments"] += 1
    for r in contracts:
        if r["n_payments"] == 0:
            y = _year_of(r["contract_signed_date"], r["submission_date"])
            if y is not None:
                bucket(y)["stated_eur"] += r["stated"] or 0.0
    out = sorted(years.values(), key=lambda b: b["year"])
    for b in out:
        b["paid_eur"] = round(b["paid_eur"], 2)
        b["stated_eur"] = round(b["stated_eur"], 2)
    return {"years": out}
