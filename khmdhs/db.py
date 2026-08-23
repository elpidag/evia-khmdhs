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
    duplicate_of                   TEXT,
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
-- Procurement FAMILY: which πρόσκληση (and award) a contract belongs to,
-- read from the contract's OWN signed text. The ΚΗΜΔΗΣ chain declares this
-- for only 40 of 245 in-scope contracts, while 200 of them cite their
-- πρόσκληση by ΑΔΑΜ in the document — 128 families, 102 of whose
-- προσκλήσεις the registry metadata never mentions (DATA_DECISIONS
-- 2026-08-18). Every row quotes the citing sentence; nothing is inferred
-- from titles, because lot labels («ΕΡΓΟΥ 11Α») repeat across programmes.
CREATE TABLE IF NOT EXISTS contract_families (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    adam             TEXT NOT NULL,
    kind             TEXT NOT NULL,   -- notice | auction
    role             TEXT NOT NULL,   -- procurement | amendment | award
    source           TEXT NOT NULL,   -- text | inherited:<ref>
    excerpt          TEXT NOT NULL,
    loaded_at        TEXT NOT NULL,
    PRIMARY KEY (reference_number, seq),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

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

-- What a contract's works ARE, MULTI-LABEL, read from the descriptive
-- project title inside the signed PDF (DATA_DECISIONS 2026-08-19, user
-- decision «show all of them»): 155 of 246 in-scope contracts name at
-- least one kind of work and 101 name two or more, which the single
-- `contract_categories` key cannot carry. The category stays the one key
-- that reconciles to the programme total; these say what was bought.
-- 91 contracts name none — an absence the page states rather than fills.
CREATE TABLE IF NOT EXISTS contract_work_themes (
    reference_number TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    theme            TEXT NOT NULL,
    excerpt          TEXT NOT NULL,      -- the verbatim clause that says it
    source           TEXT NOT NULL,      -- pdf | inherited:<ref> | registry
    curated_at       TEXT NOT NULL,
    PRIMARY KEY (reference_number, theme),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- WHO IS BEHIND a joint venture (DATA_DECISIONS 2026-08-20). The venture
-- itself stays the CONTRACTOR of its contracts — it is what signed them, and
-- what every per-contractor surface counts. This layer only records the firms
-- it is made of, so a second view can attribute the same money to them.
-- Keyed on the venture's ΑΦΜ, NOT on a contract: the same κοινοπραξία holds
-- several contracts, and a member is a member of the venture, not of a lot.
CREATE TABLE IF NOT EXISTS consortiums (
    vat_number   TEXT PRIMARY KEY,       -- the joint venture's own ΑΦΜ
    name         TEXT NOT NULL,
    legal_type   TEXT,                   -- ΓΕΜΗ's legal form, «Κοινοπραξία»
    gemi         TEXT,
    basis        TEXT,                   -- gemi | name | gemi+name
    members_documented INTEGER NOT NULL, -- 0 = no document names its members
    note         TEXT                    -- how the verdict was reached
);

CREATE TABLE IF NOT EXISTS consortium_members (
    venture_vat TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    member_vat  TEXT NOT NULL,
    member_name TEXT,
    source      TEXT,                    -- the ΑΔΑΜ the member was read from
    excerpt     TEXT,                    -- the verbatim sentence
    PRIMARY KEY (venture_vat, member_vat),
    FOREIGN KEY (venture_vat) REFERENCES consortiums(vat_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_theme_labels (
    theme    TEXT PRIMARY KEY,
    label_el TEXT NOT NULL,
    label_en TEXT NOT NULL
);

-- CPV codes that name work the contract's own title does not — a NOTE,
-- never a theme (user decision 2026-08-19): the CPV list belongs to the
-- call and is shared by all its lots, so 107 mentions of «Δεξαμενές
-- νερού» across 56 contracts are a question about the procurement, not a
-- statement about this contract.
CREATE TABLE IF NOT EXISTS contract_cpv_notes (
    reference_number TEXT NOT NULL,
    cpv_code         TEXT NOT NULL,
    theme            TEXT NOT NULL,
    PRIMARY KEY (reference_number, cpv_code),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- The deadline the CONTRACT states, and the clock it starts (DATA_DECISIONS
-- 2026-08-19). The ΚΗΜΔΗΣ duration field carries a number for 83 of the 246
-- in-scope contracts, never says what it counts from, and agrees with the
-- signed text in 3 of the 65 cases where both exist — so the document is the
-- source and the registry figure rides along as the cross-check. Three
-- contracts state a SEASON instead («η αντιπυρική περίοδος του έτους 2024»).
CREATE TABLE IF NOT EXISTS contract_durations (
    reference_number TEXT PRIMARY KEY,
    n                INTEGER,            -- NULL when the answer is a season
    unit             TEXT,               -- months | days | years
    days             INTEGER,            -- normalised, for comparison
    basis            TEXT,               -- signature | works_start | …
    fire_season      INTEGER,            -- the year, when that IS the answer
    anchor           TEXT NOT NULL,      -- which wording stated it
    excerpt          TEXT NOT NULL,      -- verbatim
    source_ref       TEXT NOT NULL,      -- the document read (chain member)
    registry_n       INTEGER,            -- what ΚΗΜΔΗΣ says, for the note
    registry_unit    TEXT,
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- What the contract DELIVERS: study / works / study_and_works — the
-- user's 1-2-3 model (DATA_DECISIONS 2026-08-22). The design-build
-- The FIRE CONTEXT of a ΔΑΣΕ contract (DATA_DECISIONS 2026-08-23): WHY
-- the work is done, read from the same title / work sentence / statement
-- of need as the category — «prevention» (για αντιπυρικούς σκοπούς, πρόληψη
-- πυρκαγιών, πυροπροστασία) or «post_fire» (καμένες εκτάσεις, πληγείσες
-- από τις πυρκαγιές, μετά την πυρκαγιά). A separate attribute on purpose:
-- post-fire restoration and fire prevention are umbrellas over different
-- works and must not swallow the category. Absent = the text states none.
CREATE TABLE IF NOT EXISTS contract_fire_context (
    reference_number TEXT PRIMARY KEY,
    context          TEXT NOT NULL,      -- prevention | post_fire
    excerpt          TEXT,               -- the verbatim words
    source           TEXT,               -- pdf:<field> | eye | inherited:<ref>
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS fire_context_labels (
    context  TEXT PRIMARY KEY,
    label    TEXT NOT NULL,
    label_en TEXT NOT NULL
);

-- generation states the contractor drafts the studies first; the clause
-- is quoted verbatim. Deliberately NOT a work theme.
CREATE TABLE IF NOT EXISTS contract_deliverables (
    reference_number TEXT PRIMARY KEY,
    kind             TEXT NOT NULL,      -- study | works | study_and_works
    excerpt          TEXT,               -- verbatim design-build clause
    source           TEXT,               -- pdf | call:<ΑΔΑΜ> | category
    curated_at       TEXT NOT NULL,
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
);

-- WHICH ΔΗΜΟΣ each contract worked in — one level finer than the Π.Ε.
-- layer, read from the contract's own placement sentence or from the
-- πρόσκληση it cites: «εντός των Δήμων Χαϊδαρίου και Ασπροπύργου,
-- αρμοδιότητας Δασαρχείου Αιγάλεω» (DATA_DECISIONS 2026-08-19). 153 of
-- 246 in-scope contracts name at least one; the other 93 stop at the
-- forest service and the page says so. `outside_region` marks a δήμος
-- whose Π.Ε. is NOT among the ones curated for the contract (49 rows):
-- the document is recorded as it stands and the region layer is left
-- alone, so nothing already published moves.
CREATE TABLE IF NOT EXISTS contract_municipalities (
    reference_number  TEXT NOT NULL,
    municipality_code TEXT NOT NULL,      -- ΥΠΕΣ code (greek_municipalities.json)
    name              TEXT NOT NULL,
    region_pe         TEXT,               -- the δήμος's own Π.Ε.
    authority         TEXT,               -- the service the sentence names
    source_ref        TEXT,               -- the document read
    from_call         TEXT,               -- set when only the πρόσκληση says it
    excerpt           TEXT NOT NULL,      -- verbatim
    outside_region    INTEGER NOT NULL DEFAULT 0,
    -- set when the δήμος IS outside the curated regions but something
    -- accounts for it: the naming service administers that Π.Ε. (its seat,
    -- or a confirmed `covers_pe`), or the user has ruled on it. Only what
    -- nothing explains stays flagged — 2 of the 49 that once were
    outside_pe_explained TEXT,
    note              TEXT,               -- rename/settlement note, or a verdict
    curated_at        TEXT NOT NULL,
    PRIMARY KEY (reference_number, municipality_code),
    FOREIGN KEY (reference_number) REFERENCES contracts(reference_number) ON DELETE CASCADE
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
    region_pe         TEXT,
    -- office layer (DATA_DECISIONS 2026-08-17): curated ΥΠΕΝ-directory
    -- address confirmed by Diavgeia letterheads; lat/lon above hold the
    -- geocoded office point when seat_precision != 'municipality'
    street            TEXT,
    postal_code       TEXT,
    city              TEXT,
    phone             TEXT,
    email             TEXT,
    seat_precision    TEXT                  -- street | postcode | city | municipality
);

-- Which authority(ies) each contract's works fall under, extracted by the
-- whitelist matcher in forest_loader (source records how: title/objects/pdf/
-- override/inherited:<ref>); excerpt keeps the matched evidence citable.
-- Complete ΥΠΕΝ forest-service directory (DATA_DECISIONS 2026-08-17):
-- REFERENCE layer from khmdhs/data/forest_units_directory.json — display
-- and audit vocabulary only, never fed to the contract matcher.
CREATE TABLE IF NOT EXISTS forest_units_directory (
    name           TEXT NOT NULL,
    inspectorate   TEXT NOT NULL,
    unit_kind      TEXT NOT NULL,   -- dx|dd|inspectorate|coordination|reforestation
    street         TEXT,
    tk             TEXT,
    city           TEXT,
    phone          TEXT,
    email          TEXT,
    authority_name TEXT,            -- registry authority when the unit is one of the 103
    lat            REAL,            -- only where a unit needed its own seat (ΕΠΙΘ. Μ-Θ)
    lon            REAL,
    PRIMARY KEY (inspectorate, name)
);

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
        # what the ΣΥΜΒ record actually IS, read from the document itself:
        # ΥΠΕΝ posts contracts, amendments, supplementary contracts AND
        # ministry approvals under a ΣΥΜΒ ΑΔΑΜ, and the registry types them
        # all «Έργα»/«Υπηρεσίες» (khmdhs/document_kinds.py, 2026-08-18)
        ("contracts", "document_kind", "TEXT"),
        ("contracts", "document_kind_evidence", "TEXT"),
        ("contracts", "document_kind_source", "TEXT"),
        # forest-authority office layer (DATA_DECISIONS 2026-08-17)
        ("forest_authorities", "street", "TEXT"),
        ("forest_authorities", "postal_code", "TEXT"),
        ("forest_authorities", "city", "TEXT"),
        ("forest_authorities", "phone", "TEXT"),
        ("forest_authorities", "email", "TEXT"),
        ("forest_authorities", "seat_precision", "TEXT"),
        # registry double-postings: the kept twin's ΑΔΑΜ (DATA_DECISIONS 2026-08-14)
        ("contracts", "duplicate_of", "TEXT"),
        # a contract kept out of a contractor-led dataset because its signed
        # PDF names no qualifying party — NOT a cancellation and NOT a
        # duplicate: the sibling ΑΔΑΜ of the same procurement that IS in
        # scope, so the page can say «related contract» (DATA_DECISIONS
        # 2026-08-17). Empty string when there is no sibling to point at.
        ("contracts", "related_to", "TEXT"),
        # why a δήμος sits outside the contract's curated Π.Ε. — the naming
        # service administers it, or the user ruled on it (2026-08-19)
        ("contract_municipalities", "outside_pe_explained", "TEXT"),
        # English display label for the work-type vocabulary: the contract
        # card is an English page and cannot mix the two (user 2026-08-19)
        ("category_labels", "label_en", "TEXT"),
        # what the ΓΕΜΗ register says about the company TODAY, verbatim
        # («Ενεργή» / «Λύση - Εκκαθάριση» / «Διαγραφή»). A joint venture is
        # wound up once its job ends, and a page that names one as the
        # contractor has to say so (user, 2026-08-20). No date: the API's
        # `dateGemiRegistered` is the REGISTRATION date (one active company
        # reads 1992, before its own start date), not the status date — the
        # register's own status-history table has those.
        ("contractor_locations", "gemi_status", "TEXT"),
        # the register's legal form; «Κοινοπραξία» is what makes an
        # entity a joint venture, whatever its name happens to say
        ("contractor_locations", "gemi_legal_type", "TEXT"),
        # the registered office as the contractor's own signed contract states
        # it (DATA_DECISIONS 2026-08-21): where the address came from
        # ('contract' | 'register' | 'website'), the document or URL, the
        # verbatim seat sentence, a note where sources disagree, and how
        # precisely the map point sits ('number' | 'street' when
        # geo_precision is 'address')
        ("contractor_locations", "seat_source", "TEXT"),
        ("contractor_locations", "seat_ref", "TEXT"),
        ("contractor_locations", "seat_excerpt", "TEXT"),
        ("contractor_locations", "seat_note", "TEXT"),
        ("contractor_locations", "geo_level", "TEXT"),
        # a deadline the ΔΑΣΕ texts state as a DATE («Προθεσμία εκτελέσεως
        # μέχρι 31-12-2021»), not a count of months; and what KIND of
        # statement it is (date | duration | open_ended) — DATA_DECISIONS
        # 2026-08-23. The Anti-nero rows leave both NULL.
        ("contract_durations", "deadline_date", "TEXT"),
        ("contract_durations", "kind", "TEXT"),
        ("contract_durations", "note", "TEXT"),
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
