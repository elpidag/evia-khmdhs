"""All SQL for the web UI. Each function returns plain dicts."""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path

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
    flt = scope_filter(conn)
    row = conn.execute(f"""
        SELECT
            COUNT(*) AS n_contracts,
            ROUND(SUM(total_cost_with_vat), 2) AS total_eur,
            SUM(CASE WHEN procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END) AS n_direct,
            SUM(CASE WHEN bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder,
            SUM(CASE WHEN cancelled = 1 THEN 1 ELSE 0 END) AS n_cancelled
        FROM contracts
        WHERE {flt}
    """).fetchone()
    n_contractors = conn.execute(f"""
        SELECT COUNT(DISTINCT vat_number) FROM contractors
        WHERE {flt}
    """).fetchone()[0]
    n_authorities = conn.execute(f"""
        SELECT COUNT(DISTINCT organization_name) FROM contracts
        WHERE {flt}
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
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur,
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
        SELECT organization_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE organization_name IS NOT NULL
          AND {scope_filter(conn)}
        GROUP BY organization_name
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_signers(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = conn.execute(f"""
        SELECT signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE signer_name IS NOT NULL
          AND {scope_filter(conn)}
        GROUP BY signer_name
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
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur,
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
               k.total_cost_with_vat,
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
        out = [
            r for r in out
            if needle in _search_norm(r["reference_number"])
            or needle in _search_norm(r["title"])
            or needle in _search_norm(r["regions"])
            or needle in _search_norm(r["contractor_names"])
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
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur,
               ROUND(SUM(co.total_cost_without_vat), 2) AS total_eur_no_vat,
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
               co.total_cost_with_vat,
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
               ROUND(SUM(co.total_cost_with_vat), 2) AS shared_eur
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
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur
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
        SELECT organization_name AS name,
               organization_vat AS vat,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE organization_name IS NOT NULL
          AND {scope_filter(conn)}
        GROUP BY organization_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_unit_operators(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT units_operator_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE units_operator_name IS NOT NULL
          AND {scope_filter(conn)}
        GROUP BY units_operator_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_signers(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(f"""
        SELECT signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE signer_name IS NOT NULL
          AND {scope_filter(conn)}
        GROUP BY signer_name
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
               cl.nuts3_code  AS source_nuts3,
               cpr.region_pe  AS target_pe,
               cpr.nuts3_code AS target_nuts3,
               COUNT(DISTINCT co.reference_number)   AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur
        FROM contractors c
        JOIN contractor_locations cl      ON cl.vat_number = c.vat_number
        JOIN contracts co                 ON co.reference_number = c.reference_number
        JOIN contract_project_regions cpr ON cpr.reference_number = co.reference_number
        WHERE {' AND '.join(where)}
        GROUP BY cl.region_pe, cpr.region_pe
        ORDER BY total_eur DESC
    """
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def flow_coverage(conn: sqlite3.Connection) -> dict:
    """How much of the total contract € the resolved-source flows account for.

    Returns:
        resolved_eur:    € attributable to contracts where ≥1 contractor has region_pe
        unresolved_eur:  € in contracts where NO contractor has a resolved region_pe
        total_eur:       resolved + unresolved
        n_contractors_resolved / n_contractors_total
    """
    flt = scope_filter(conn)
    total_eur = conn.execute(f"""
        SELECT ROUND(SUM(total_cost_with_vat), 2) FROM contracts
        WHERE {flt}
    """).fetchone()[0] or 0

    resolved_eur = conn.execute(f"""
        SELECT ROUND(SUM(total_cost_with_vat), 2)
        FROM contracts
        WHERE {flt}
          AND reference_number IN (
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
                cpr.nuts3_code                 AS target_nuts3,
                co.reference_number,
                co.total_cost_with_vat         AS contract_eur,
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
               target_nuts3,
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
