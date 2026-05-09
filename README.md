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
├── khmdhs/                       # Python package (the program)
│   ├── __init__.py
│   ├── __main__.py               # `python -m khmdhs`
│   ├── config.py                 # paths + API constants
│   ├── api.py                    # HTTP client (retries, 429 handling)
│   ├── extract.py                # JSON → row dicts (pure, no I/O)
│   ├── db.py                     # SQLite schema + writes
│   ├── excel_io.py               # read source xlsx + write enriched xlsx
│   └── cli.py                    # argparse + main loop
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
- Two libraries listed in `requirements.txt`: `requests` and `openpyxl`

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
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
