"""SQLite schema and persistence layer."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from khmdhs.extract import parent_row, child_rows, payment_row

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS contracts (
    reference_number               TEXT PRIMARY KEY,
    title                          TEXT,
    contract_number                TEXT,
    contract_signed_date           TEXT,
    submission_date                TEXT,
    last_update_date               TEXT,
    start_date                     TEXT,
    end_date                       TEXT,
    no_end_date                    INTEGER,
    cancelled                      INTEGER,
    cancellation_date              TEXT,
    cancellation_reason            TEXT,
    organization_code              TEXT,
    organization_name              TEXT,
    organization_vat               TEXT,
    type_of_contracting_authority  TEXT,
    contracting_authority_activity TEXT,
    central_government_authority   TEXT,
    units_operator_code            TEXT,
    units_operator_name            TEXT,
    signer_code                    TEXT,
    signer_name                    TEXT,
    procedure_type_code            TEXT,
    procedure_type                 TEXT,
    award_procedure                TEXT,
    assign_criteria                TEXT,
    contract_type_code             TEXT,
    contract_type                  TEXT,
    legal_context                  TEXT,
    nuts_code                      TEXT,
    nuts_region_name               TEXT,
    nuts_city                      TEXT,
    nuts_postal_code               TEXT,
    nuts_country                   TEXT,
    total_cost_without_vat         REAL,
    total_cost_with_vat            REAL,
    contract_budget                REAL,
    bids_submitted                 INTEGER,
    max_bids_submitted             INTEGER,
    number_of_sections             INTEGER,
    contract_duration              INTEGER,
    contract_duration_unit         TEXT,
    public_funding_ref             TEXT,
    public_funding_ref_num         TEXT,
    public_funding_ref_ops         TEXT,
    cofund_program_ref             TEXT,
    espa_fund_program_ref          TEXT,
    notice_reference_number        TEXT,
    prev_reference_no              TEXT,
    next_reference_no              TEXT,
    correction_note                TEXT,
    raw_json                       TEXT,
    fetched_at                     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contractors (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    vat_number       TEXT,
    name             TEXT,
    country          TEXT,
    greek_vat        INTEGER,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contract_cpvs (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    cpv_code         TEXT,
    cpv_description  TEXT,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contract_nuts (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    nuts_code        TEXT,
    nuts_name        TEXT,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contract_objects (
    reference_number  TEXT NOT NULL,
    seq               INTEGER NOT NULL,
    quantity          REAL,
    unit_type         TEXT,
    cost_without_vat  REAL,
    vat_percent       TEXT,
    currency          TEXT,
    short_description TEXT,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fetch_log (
    reference_number TEXT PRIMARY KEY,
    status           TEXT NOT NULL,
    http_status      INTEGER,
    error_message    TEXT,
    attempts         INTEGER NOT NULL DEFAULT 1,
    last_attempt_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contractors_vat ON contractors(vat_number);
CREATE INDEX IF NOT EXISTS idx_contractors_name ON contractors(name);
CREATE INDEX IF NOT EXISTS idx_contracts_org_vat ON contracts(organization_vat);

CREATE TABLE IF NOT EXISTS contract_project_regions (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    region_pe        TEXT NOT NULL,
    nuts3_code       TEXT,
    note             TEXT,
    source           TEXT NOT NULL DEFAULT 'manual',
    curated_at       TEXT NOT NULL,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cpr_region_pe ON contract_project_regions(region_pe);
CREATE INDEX IF NOT EXISTS idx_cpr_nuts3 ON contract_project_regions(nuts3_code);

-- Named work sites below Π.Ε. level (Δασαρχεία, τμήματα, θέσεις), curated
-- from the contract PDFs; page + excerpt keep the evidence citable.
CREATE TABLE IF NOT EXISTS contract_sites (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    site_name        TEXT NOT NULL,
    region_pe        TEXT,
    page             INTEGER,
    excerpt          TEXT,
    curated_at       TEXT NOT NULL,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- Per-contract μελέτη (study/planning) cost, net of ΦΠΑ, extracted from
-- the signed PDF's «Κόστος εκπόνησης μελετών (ΣΑΥ-ΦΑΥ)» line and curated
-- into khmdhs/data/study_costs.json with page+excerpt evidence
-- (DATA_DECISIONS 2026-07-26). Aggregates attribute each in-scope chain
-- tip its own row, else the nearest predecessor's.
CREATE TABLE IF NOT EXISTS contract_study_costs (
    reference_number TEXT PRIMARY KEY,
    eur              REAL NOT NULL,      -- net of ΦΠΑ
    page             INTEGER,
    excerpt          TEXT,
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- Curated work-type category per in-scope Anti-nero contract, ONE each so
-- category aggregates reconcile to the programme total. Classified from
-- the signed PDF's descriptive project title (stored verbatim as the
-- evidence) with the CPV tail as tie-breaker; derivative documents
-- inherit their parent chain's title (source 'inherited:<ref>')
-- (DATA_DECISIONS 2026-08-14). Labels ship from the curated file via
-- category_labels — never hardcoded in code.
CREATE TABLE IF NOT EXISTS contract_categories (
    reference_number TEXT PRIMARY KEY,
    category         TEXT NOT NULL,
    title            TEXT NOT NULL,      -- descriptive PDF project title
    source           TEXT NOT NULL,      -- pdf | short_description | inherited:<ref>
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS category_labels (
    category TEXT PRIMARY KEY,
    label    TEXT NOT NULL,
    note     TEXT
);

-- Forest authorities (Διευθύνσεις Δασών / Δασαρχεία) from the curated
-- registry khmdhs/data/forest_authorities.json; coordinates are the seat
-- municipality's centroid (khmdhs/data/greek_municipalities.json, ΥΠΕΣ code).
CREATE TABLE IF NOT EXISTS forest_authorities (
    name              TEXT PRIMARY KEY,
    kind              TEXT NOT NULL,        -- 'dd' | 'dx'
    seat_city         TEXT,
    municipality_code TEXT,
    municipality_name TEXT,
    lat               REAL,
    lon               REAL,
    region_pe         TEXT
);

-- Which authority(ies) each contract's works fall under, extracted by the
-- whitelist matcher in forest_loader (source records how: title/objects/pdf/
-- override/inherited:<ref>); excerpt keeps the matched evidence citable.
CREATE TABLE IF NOT EXISTS contract_forest_authorities (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    authority_name   TEXT NOT NULL,
    source           TEXT NOT NULL,
    excerpt          TEXT,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cfa_authority ON contract_forest_authorities(authority_name);

-- Payment orders (##PAY#########) linked to contracts. `contract_ref` is the
-- contract whose API payload listed the payment in `paymentRefNo`;
-- `attributed_ref` is the final contract of that contract's supersede chain
-- (payments frequently stay attached to a superseded original after a
-- modification replaces it, so aggregates must follow the chain).
CREATE TABLE IF NOT EXISTS contract_payments (
    payment_ref        TEXT PRIMARY KEY,
    contract_ref       TEXT NOT NULL,
    attributed_ref     TEXT NOT NULL,
    api_contract_ref   TEXT,
    title              TEXT,
    signed_date        TEXT,
    submission_date    TEXT,
    cancelled          INTEGER,
    credit             INTEGER,
    amount_without_vat REAL,
    amount_with_vat    REAL,
    fund_ref_num       TEXT,
    correction_note    TEXT,
    source             TEXT NOT NULL DEFAULT 'khmdhs',
    ada                TEXT,
    raw_json           TEXT,
    fetched_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cp_contract ON contract_payments(contract_ref);
CREATE INDEX IF NOT EXISTS idx_cp_attributed ON contract_payments(attributed_ref);

CREATE TABLE IF NOT EXISTS contractor_locations (
    vat_number   TEXT PRIMARY KEY,
    legal_name   TEXT,
    address      TEXT,
    postal_code  TEXT,
    city         TEXT,
    region_pe    TEXT,
    nuts3_code   TEXT,
    gemi         TEXT,
    lat          REAL,
    lon          REAL,
    geo_precision TEXT,   -- 'address' | 'municipality' (see geocode_loader)
    source       TEXT NOT NULL,
    source_url   TEXT,
    notes        TEXT,
    curated_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cl_region_pe ON contractor_locations(region_pe);
CREATE INDEX IF NOT EXISTS idx_cl_nuts3 ON contractor_locations(nuts3_code);
"""


def init_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    # Columns added after a table already exists in deployed DBs
    # (CREATE TABLE IF NOT EXISTS won't alter them).
    for table, column, decl in (
        ("contractor_locations", "gemi", "TEXT"),
        ("contractor_locations", "lat", "REAL"),
        ("contractor_locations", "lon", "REAL"),
        ("contractor_locations", "geo_precision", "TEXT"),
        # curated stated-value corrections (dase_contract_corrections.json)
        ("contracts", "correction_note", "TEXT"),
    ):
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        except sqlite3.OperationalError:
            pass  # already present
    conn.commit()
    return conn


def already_done(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT reference_number FROM fetch_log WHERE status='ok'")}


def upsert_contract(conn: sqlite3.Connection, item: dict) -> None:
    """Idempotent write: parent row + child rows + fetch_log='ok', in one transaction."""
    p = parent_row(item)
    children = child_rows(p["reference_number"], item)
    cols = ", ".join(p.keys())
    placeholders = ", ".join(f":{k}" for k in p)
    with conn:
        conn.execute(f"INSERT OR REPLACE INTO contracts ({cols}) VALUES ({placeholders})", p)
        for table in ("contractors", "contract_cpvs", "contract_nuts", "contract_objects"):
            conn.execute(f"DELETE FROM {table} WHERE reference_number = ?", (p["reference_number"],))
        if children["contractors"]:
            conn.executemany(
                "INSERT INTO contractors (reference_number, seq, vat_number, name, country, greek_vat) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                children["contractors"],
            )
        if children["contract_cpvs"]:
            conn.executemany(
                "INSERT INTO contract_cpvs (reference_number, seq, cpv_code, cpv_description) "
                "VALUES (?, ?, ?, ?)",
                children["contract_cpvs"],
            )
        if children["contract_nuts"]:
            conn.executemany(
                "INSERT INTO contract_nuts (reference_number, seq, nuts_code, nuts_name) "
                "VALUES (?, ?, ?, ?)",
                children["contract_nuts"],
            )
        if children["contract_objects"]:
            conn.executemany(
                "INSERT INTO contract_objects "
                "(reference_number, seq, quantity, unit_type, cost_without_vat, vat_percent, currency, short_description) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                children["contract_objects"],
            )
        conn.execute(
            """INSERT INTO fetch_log (reference_number, status, http_status, error_message, attempts, last_attempt_at)
               VALUES (?, 'ok', 200, NULL, 1, ?)
               ON CONFLICT(reference_number) DO UPDATE SET
                   status='ok', http_status=200, error_message=NULL,
                   attempts=fetch_log.attempts+1, last_attempt_at=excluded.last_attempt_at""",
            (p["reference_number"], datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )


def upsert_payment(
    conn: sqlite3.Connection, contract_ref: str, attributed_ref: str, item: dict
) -> None:
    p = payment_row(contract_ref, attributed_ref, item)
    cols = ", ".join(p.keys())
    placeholders = ", ".join(f":{k}" for k in p)
    with conn:
        conn.execute(
            f"INSERT OR REPLACE INTO contract_payments ({cols}) VALUES ({placeholders})", p
        )


def record_failure(
    conn: sqlite3.Connection,
    adam: str,
    status: str,
    http_status: int | None,
    msg: str | None,
) -> None:
    with conn:
        conn.execute(
            """INSERT INTO fetch_log (reference_number, status, http_status, error_message, attempts, last_attempt_at)
               VALUES (?, ?, ?, ?, 1, ?)
               ON CONFLICT(reference_number) DO UPDATE SET
                   status=excluded.status, http_status=excluded.http_status,
                   error_message=excluded.error_message,
                   attempts=fetch_log.attempts+1, last_attempt_at=excluded.last_attempt_at""",
            (adam, status, http_status, msg, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
