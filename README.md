# KHMDHS Contract Enricher

Enriches a contracts export from the Greek public-procurement portal
([eprocurement.gov.gr](https://portal.eprocurement.gov.gr/webcenter/portal/TestPortal))
with the full contract record for every ADAM (Κωδικός ΑΔΑΜ) — contractor
name & VAT, procurement procedure, unit operator (Οργανική Μονάδα), signer
(Αποφαινόμενο Όργανο), NUTS area, CPV codes, total cost incl. VAT, and
much more.

Built for the **Anti-nero IV** programme but works with any KHMDHS export.

## Project layout

```
19_KHDMHS/
├── khmdhs/                       # ETL package (writes the DB)
│   ├── __init__.py
│   ├── __main__.py               # `python -m khmdhs`
│   ├── config.py                 # paths + API constants
│   ├── api.py                    # HTTP client (retries, 429 handling)
│   ├── extract.py                # JSON → row dicts (pure, no I/O)
│   ├── db.py                     # SQLite schema + writes
│   ├── excel_io.py               # read source xlsx + write enriched xlsx
│   └── cli.py                    # argparse + main loop
├── webui/                        # OSINT web UI (reads the DB read-only)
│   ├── __init__.py
│   ├── __main__.py               # `python -m webui`
│   ├── app.py                    # Flask app + routes
│   ├── queries.py                # all SQL lives here
│   ├── filters.py                # Greek number/currency formatting
│   ├── templates/                # Jinja templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── contractors.html
│   │   ├── contractor_detail.html
│   │   ├── contract_detail.html
│   │   ├── authorities.html
│   │   └── 404.html
│   └── static/
│       └── style.css             # custom Pico overrides
├── data/
│   ├── raw/
│   │   └── contracts_search_results.xlsx           # input (untouched)
│   └── processed/
│       ├── contracts_search_results_enriched.xlsx  # output (created)
│       └── khmdhs.sqlite                           # output (created)
├── logs/
│   └── enrich_contracts.log                        # output (created)
├── requirements.txt
└── README.md
```

The split follows a few simple rules:

- `data/raw/` is the source of truth and is **never written to**.
- `data/processed/` holds derived artefacts that can be regenerated at any time.
- Code lives in a `khmdhs/` package so it's importable (`from khmdhs.db import …`) and runnable (`python -m khmdhs`).
- Each module has one clear job — `api.py` only talks HTTP, `extract.py` is pure-functional JSON parsing, `db.py` only touches SQLite, `excel_io.py` only touches xlsx, `cli.py` glues them together.

## Requirements

- Python 3.11 or newer
- Three libraries listed in `requirements.txt`: `requests`, `openpyxl`, `flask`

## Setup — from scratch in a virtualenv

### Ubuntu / Debian

```bash
# Ubuntu ships venv/pip as separate packages — install them once
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Create & activate the project venv
python3 -m venv .venv
source .venv/bin/activate

# Install project dependencies
pip install -r requirements.txt
```

To leave the venv later: `deactivate`. To re-enter it in a new shell: `source .venv/bin/activate`.

### Windows (PowerShell)

```powershell
# Requires Python 3.11+ from https://www.python.org/downloads/ (tick "Add to PATH")
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If `Activate.ps1` is blocked by execution policy, run this once per user and reopen the shell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or use `cmd.exe` instead: `.venv\Scripts\activate.bat`.

## Run

With the venv activated, the commands are the same on both platforms:

```bash
python -m khmdhs                  # full run on all ADAMs
python -m khmdhs --limit 5        # smoke-test on 5 ADAMs
python -m khmdhs --refetch        # re-fetch ADAMs already marked OK
python -m khmdhs --skip-xlsx      # only update the SQLite database
python -m khmdhs --help           # all options
```

The program is **resumable**: every successful fetch is recorded in the
`fetch_log` table and skipped on subsequent runs. Re-running after a crash
or network blip continues from where it stopped.

By default everything reads/writes inside the project tree (paths in
`khmdhs/config.py`). Override any of them via CLI flags if you want.

### Anti-nero supplement + scope classification

The original xlsx export missed the Anti-nero I execution contracts (their
titles never contain the word "ANTINERO" — they were found by scanning
Diavgeia decisions and verified via the ΣΑΤΑ 075 funding code
`2022ΤΑ07500000` of the 07.02.2022 ΥΠΕΝ↔ΤΑΙΠΕΔ framework), plus a handful
of later-phase contracts. They are curated in
`khmdhs/data/antinero_supplement.json` and loaded with:

```bash
python -m khmdhs.antinero_loader --dry-run   # fetch + verify, write nothing
python -m khmdhs.antinero_loader             # load into SQLite
python -m khmdhs.scope_loader                # (re)build the contract_scope table
```

`scope_loader` classifies **every** contract (khmdhs/scope.py) into
`antinero_i…antinero_2026`, `antinero_umbrella` (ΤΑΙΠΕΔ/ΕΕΣΥΠ
pass-throughs), `antinero_support`, or `non_antinero` (routine pre-programme
forest-road maintenance etc.), and marks contract versions superseded by a
later modification. The web UI aggregates only `in_scope = 1` rows; detail
pages still resolve for everything and show the scope + exclusion reason.

Re-run `python -m khmdhs.scope_loader` after any contract load.

### Amendment chains

Contract versions link via `prevReferenceNo`/`nextRefNo` (an amendment is
a full ##SYMV######### record). Members missing from the original sources
are fetched to closure with:

```bash
python -m khmdhs.chain_loader --dry-run   # list missing chain members
python -m khmdhs.chain_loader             # fetch them
```

`scope_loader` then marks superseded versions out of scope (one in-scope
member per chain) and lets amendments without programme evidence of their
own (titles like «1η ΤΡΟΠΟΠΟΙΗΣΗ …») inherit the phase of the version
they modify. Project regions for amendments are inherited from the
superseded version in `contract_regions.json`. Run order after a chain
fetch: `scope_loader` → `region_loader` → `payment_loader` (which also
re-attributes stored payments to the newest version of each chain).

### Payment orders + effective contract values

Every contract's API payload lists its payment orders (`paymentRefNo`,
ADAMs shaped `##PAY#########`). The payment loader links them, fetches
each one from `POST /khmdhs-opendata/payment` and stores it in the
`contract_payments` table:

```bash
python -m khmdhs.payment_loader --dry-run    # list pending fetches
python -m khmdhs.payment_loader              # fetch + store + apply corrections
```

Payments frequently stay attached to a superseded contract version after a
modification replaces it, so each payment also records `attributed_ref` —
the final contract of the supersede chain — which is what the UI
aggregates on (run `scope_loader` first so the chains are current).

The web UI then shows an **effective value** per contract: the sum of its
non-cancelled payment orders when at least one exists (this absorbs
post-signature amendments — and, for running contracts, reflects what has
actually been disbursed so far), falling back to the stated contract value
when no payments are recorded. Contract detail pages list every payment
order with a per-order PDF link, plus a "Download contract PDF" button.

PDFs are served through the app's `/pdf/<kind>/<ADAM>` route, which
fetches the attachment from the registry once (public, no login) and then
serves it from `data/processed/pdf_cache/`. The registry rate-limits
bursts of attachment downloads with HTTP 429; on a cache miss during a
throttle window the route returns an auto-retrying wait page instead of
the registry's raw JSON error.

Registry keying errors (e.g. `25PAY016487974`, entered as €992.4M for a
€279k study contract; the signed PDF documents €239,940.00) are fixed via
the curated `khmdhs/data/payment_corrections.json`, applied at the end of
every loader run.

### Diavgeia cross-check (payments missing from KHMDHS links)

Not every payment order reaches the DB through KHMDHS: some orders exist
in KHMDHS but were never listed in any contract's `paymentRefNo`, and a
few were never registered in KHMDHS at all. `khmdhs/diavgeia_loader.py`
ingests a list of Diavgeia «Εκκαθάριση-εντολή πληρωμής» decisions
(`data/raw/payments_not_in_db_155.xlsx`): it downloads each decision's
metadata + signed PDF from diavgeia.gov.gr (cache:
`data/processed/diavgeia_cache/`), reads the ΑΔΑΜ stamps in the PDF (the
KHMDHS PAY number, the cited contract, and the authoritative «ΑΔΑΜ
ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ» field), then fetches the canonical KHMDHS record where
one exists or stores the payment with `source='diavgeia'` keyed by its
ΑΔΑ. Duplicates are blocked by PAY-number, by ΑΔΑ, and by
same-chain/same-amount guards.

A full completeness sweep (2026-07-19) then verified the whole DB both
ways: every stored contract was refetched from KHMDHS for fresh payment
links, all 846 ΥΠΕΝ clearance decisions on Diavgeia that reference the
three Anti-nero fund codes were harvested, and each one was traced to a
stored payment (by ΑΔΑ, by the PAY ΑΔΑΜ stamped in its PDF, or by
amount+chain twin-matching for pre-stamp-era decisions). A parallel
ΑΔΑΜ-subject sweep over ~6,000 ΥΠΕΝ decisions surfaced 15 more Anti-nero
contracts (6 fire-protection plans under the Anti-nero I framework fund
and 9 «Σύμβαση N/2026» ANTINERO III works — ΥΠΕΝ's own decision on
σύμβαση 10/2026 names the programme), which were fetched, classified,
region-curated and payment-linked; ~342 other swept contracts classify as
non-Anti-nero ΥΠΕΝ business and were not imported.

The earlier xlsx batch also surfaced 37 contracts the DB was missing. The 11 whose
payment PDFs are titled «ΠΡΟΓΡΑΜΜΑ ΠΡΟΣΤΑΣΙΑΣ ΔΑΣΩΝ - ANTINERO III» were
added to the Anti-nero supplement (in scope); the rest belong to sibling
sub-programmes of the same Recovery-Fund ΠΔΕ project and get their own
out-of-scope classes: `esa_reforestation` (Εθνικό Σχέδιο Αναδάσωσης,
nurseries) and `post_fire_works` (αντιδιαβρωτικά/αντιπλημμυρικά).
Supplementary contracts («1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ», adding money on top of the
parent) do not supersede the version they extend — both stay countable.

## Output: enriched Excel file

Original columns A–H are preserved exactly. Eight new columns are appended
(multi-value fields are joined with ` | `):

| Col | Header (Greek) | Source field |
|-----|----------------|--------------|
| I | Επωνυμία Αναδόχου | `contractingDataDetails.contractingMembersDataList[*].name` |
| J | ΑΦΜ Αναδόχου | `…[*].vatNumber` |
| K | Διαδικασία Ανάθεσης | `procedureType.value` |
| L | Οργανική Μονάδα | `contractingDataDetails.unitsOperator.value` |
| M | Γεωγραφική Περιοχή (NUTS) | `nutsCode.value`, `nutsCity`, `nutsPostalCode` |
| N | Αποφαινόμενο Όργανο | `contractingDataDetails.signers.value` |
| O | Συνολική Αξία με ΦΠΑ | `totalCostWithVAT` |
| P | Κωδικοί CPV | `objectDetailsList[*].cpvs[*].key` |

## Output: SQLite database

The database stores **everything** the API returns, not just the eight
xlsx columns. The full JSON payload is also kept in `contracts.raw_json`
so any field can be queried later.

| Table | Rows per contract | Purpose |
|-------|-------------------|---------|
| `contracts` | 1 | Flat record (~50 columns) plus `raw_json` |
| `contractors` | 0 – N | Contractor name, VAT, country, Greek-VAT flag |
| `contract_cpvs` | 0 – N | Distinct CPV codes |
| `contract_nuts` | 0 – N | Project-level NUTS codes |
| `contract_objects` | 0 – N | Object lines (quantity, unit, cost, description) |
| `fetch_log` | 1 | Status of the last fetch attempt per ADAM |

Indexes are created on `contractors.vat_number`, `contractors.name`,
and `contracts.organization_vat`.

### Useful queries

```sql
-- Top contractors by number of contracts
SELECT vat_number, name, COUNT(*) AS n
FROM contractors
GROUP BY vat_number, name
ORDER BY n DESC
LIMIT 20;

-- Total contract value per contracting authority
SELECT organization_name, ROUND(SUM(total_cost_with_vat), 2) AS total
FROM contracts
GROUP BY organization_name
ORDER BY total DESC;

-- Procedure-type distribution
SELECT procedure_type, COUNT(*) FROM contracts
GROUP BY procedure_type ORDER BY 2 DESC;

-- Failed fetches (if any)
SELECT * FROM fetch_log WHERE status <> 'ok';
```

## Web UI (OSINT explorer)

A Flask app that reads the SQLite DB read-only and shows totals, contractor
profiles and per-contract sheets. Built with Pico.css (semantic, mobile-first
responsive, automatic light/dark) and one Chart.js bar chart on the dashboard.

With the venv activated (see [Setup](#setup--from-scratch-in-a-virtualenv) above):

```bash
python -m webui                              # http://127.0.0.1:5000
python -m webui --port 5050 --debug          # custom port + auto-reload
```

Pages:

| Path | What it shows |
|------|----------------|
| `/` | KPI cards (€1.54 B total, 226 contracts, 139 contractors, 89.4 % direct-assignment, 34 single-bidder), top-10 contractor bar chart (click a bar to drill in), top-5 authorities, top-5 signers |
| `/contractors?q=&sort=` | Sortable table of all 139 contractors. `q` matches VAT or name substring. A 9-digit `q` redirects straight to the detail page. |
| `/contractor/<vat>` | Header card (totals, % direct-assignment, single-bidder count, consortium count, first/last signed dates), list of all contracts, consortium partners, primary signers |
| `/contract/<adam>` | Full contract sheet: every field from the API + objects + CPVs + NUTS + linked acts, plus an expandable raw-JSON pane |
| `/authorities` | All 3 authorities + 12 unit operators + 15 signers, with totals |
| `/api/contractors.json` | JSON feed of the contractors list (for jq, pandas, etc.) |

Red-flag conventions:

- **% direct-assignment** badge — neutral grey, amber if ≥ 80 %, red if 100 %.
- **1 bid** rendered as an amber pill in tables.
- **Cancelled** contracts get a red pill.
- **Natural persons** (heuristic: name contains "ΤΟΥ" / "ΤΗΣ" and no Greek legal-form suffix) get a small "φυσικό πρόσωπο" badge.

When a contract is a consortium, **the full contract value is attributed to
each partner**. This is the "maximum exposure" view (best for OSINT) — not
an equal split. The footer says so explicitly.

## API notes

- The `/khmdhs-opendata/*` endpoints are **public** — no auth required.
- Rate limit is **350 requests/minute**. The script throttles to ~5 req/s
  by default (`--sleep 0.2`) and honours `Retry-After` on HTTP 429.
- The API serves data updated daily (~24 h lag).

## CLI options

| Flag | Default | Purpose |
|------|---------|---------|
| `--input` | `data/raw/contracts_search_results.xlsx` | Source xlsx |
| `--output` | `data/processed/contracts_search_results_enriched.xlsx` | Destination xlsx |
| `--db` | `data/processed/khmdhs.sqlite` | SQLite path |
| `--log` | `logs/enrich_contracts.log` | Log file path |
| `--limit N` | _none_ | Process only the first N pending ADAMs |
| `--sleep S` | `0.2` | Seconds between requests |
| `--refetch` | off | Re-fetch even already-OK ADAMs |
| `--skip-xlsx` | off | Skip the Excel write (DB only) |
