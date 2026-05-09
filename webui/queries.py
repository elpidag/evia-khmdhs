"""All SQL for the web UI. Each function returns plain dicts."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


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
    row = conn.execute("""
        SELECT
            COUNT(*) AS n_contracts,
            ROUND(SUM(total_cost_with_vat), 2) AS total_eur,
            SUM(CASE WHEN procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END) AS n_direct,
            SUM(CASE WHEN bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder,
            SUM(CASE WHEN cancelled = 1 THEN 1 ELSE 0 END) AS n_cancelled
        FROM contracts
    """).fetchone()
    n_contractors = conn.execute("SELECT COUNT(DISTINCT vat_number) FROM contractors").fetchone()[0]
    n_authorities = conn.execute("SELECT COUNT(DISTINCT organization_name) FROM contracts").fetchone()[0]
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
    rows = conn.execute("""
        SELECT c.vat_number,
               MIN(c.name) AS name,
               COUNT(DISTINCT c.reference_number) AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur,
               ROUND(100.0 * SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END)
                           / COUNT(*), 1) AS pct_direct,
               SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder
        FROM contractors c
        JOIN contracts   co USING (reference_number)
        GROUP BY c.vat_number
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_authorities(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = conn.execute("""
        SELECT organization_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE organization_name IS NOT NULL
        GROUP BY organization_name
        ORDER BY total_eur DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_signers(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = conn.execute("""
        SELECT signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE signer_name IS NOT NULL
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
        {{where}}
        GROUP BY c.vat_number
        ORDER BY {order}
    """
    params: tuple = ()
    if q:
        sql = sql.format(where="WHERE c.vat_number LIKE ? OR LOWER(c.name) LIKE LOWER(?)")
        wild = f"%{q}%"
        params = (wild, wild)
    else:
        sql = sql.format(where="")
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# Contractor detail
# ---------------------------------------------------------------------------

def contractor_summary(conn: sqlite3.Connection, vat: str) -> dict | None:
    row = conn.execute("""
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
        GROUP BY c.vat_number
    """, (vat,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    # # of contracts where this contractor was part of a consortium
    d["n_consortium"] = conn.execute("""
        SELECT COUNT(DISTINCT c1.reference_number)
        FROM contractors c1
        WHERE c1.vat_number = ?
          AND (SELECT COUNT(*) FROM contractors c2 WHERE c2.reference_number = c1.reference_number) > 1
    """, (vat,)).fetchone()[0]
    return d


def contractor_contracts(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute("""
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
        ORDER BY co.contract_signed_date DESC, co.reference_number DESC
    """, (vat,)).fetchall()
    return [dict(r) for r in rows]


def consortium_partners(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute("""
        SELECT c2.vat_number,
               MIN(c2.name) AS name,
               COUNT(DISTINCT c2.reference_number) AS shared_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS shared_eur
        FROM contractors c1
        JOIN contractors c2 USING (reference_number)
        JOIN contracts   co USING (reference_number)
        WHERE c1.vat_number = ? AND c2.vat_number != ?
        GROUP BY c2.vat_number
        ORDER BY shared_eur DESC
    """, (vat, vat)).fetchall()
    return [dict(r) for r in rows]


def contractor_signers(conn: sqlite3.Connection, vat: str) -> list[dict]:
    rows = conn.execute("""
        SELECT co.signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur
        FROM contracts co
        JOIN contractors c USING (reference_number)
        WHERE c.vat_number = ? AND co.signer_name IS NOT NULL
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
    return d


# ---------------------------------------------------------------------------
# Authorities / signers / unit operators
# ---------------------------------------------------------------------------

def list_authorities(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT organization_name AS name,
               organization_vat AS vat,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE organization_name IS NOT NULL
        GROUP BY organization_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_unit_operators(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT units_operator_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE units_operator_name IS NOT NULL
        GROUP BY units_operator_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]


def list_signers(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT signer_name AS name,
               COUNT(*) AS n_contracts,
               ROUND(SUM(total_cost_with_vat), 2) AS total_eur
        FROM contracts
        WHERE signer_name IS NOT NULL
        GROUP BY signer_name
        ORDER BY total_eur DESC
    """).fetchall()
    return [dict(r) for r in rows]
