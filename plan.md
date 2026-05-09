# Plan: OSINT web UI on top of `khmdhs.sqlite` + research roadmap

## Context

The KHMDHS DB already has the raw material for OSINT work — 226 ANTINERO contracts, 139 unique contractor VATs, **€1.54 billion** of state spend, only 3 contracting authorities and **15 signers**. **89.4 %** of those contracts were awarded by direct-assignment (Απευθείας ανάθεση) and 34 went to single bidders, so the dataset is genuinely interesting before we add anything new.

You want two things:

1. A **simple, aesthetic, responsive web UI** that lets you look up any VAT or contractor name and see total state money received, the projects involved and the project count.
2. A list of **other angles** (analyses on the existing data + other data sources to bring in) so you can prioritise next steps.

This plan delivers a small Flask app driven directly by `data/processed/khmdhs.sqlite`, plus a curated research roadmap.

## Quick data shape (from a read-only sanity check)

```
contracts:               226
distinct contractor VATs: 139    (151 distinct names → 12 name aliases on same VAT)
distinct contracting authorities: 3
distinct unit operators:  12
distinct signers:         15
single-bidder contracts:  34
contracts modified (prev_reference_no): 23
contracts cancelled:       2
total state spend:        €1,537,860,894.52
direct-assignment rate:   89.4 %
top exposures (€):
  Ε.Ε.ΣΥ.Π. Α.Ε.                        528.7 M (2 contracts) — state vehicle
  ΤΑΜΕΙΟ ΑΞΙΟΠΟΙΗΣΗΣ (HRADF/TAIPED)     422.2 M (6) — state vehicle
  ΕΡΓΑ ΠΡΑΣΙΝΟΥ ΑΝΩΝΥΜΗ ΤΕΧΝΙΚΗ          44.0 M (3)
  GREEN CONSTRUCTION                     21.7 M (8)
  ΜΑΡΙΑ ΣΙΔΕΡΗ ΤΟΥ ΔΗΜΗΤΡΙΟΥ             15.9 M (3)  ← natural person
```

The top two are state-owned vehicles (legitimate but worth flagging). Below them the curve flattens fast — perfect size for a paginated table on one screen.

---

## Section 1 — the web UI (the deliverable)

### Tech stack — Flask + Jinja2 + Pico.css

Best fit for "simple, aesthetic, responsive, best practices":

- **Flask** (≈ 1 file, server-rendered, well-known) over Streamlit (generic look) and Datasette (great browsing, weak custom styling).
- **Jinja2** for templates (ships with Flask).
- **Pico.css** (~10 KB, semantic HTML, automatic light/dark, mobile-first responsive). No build step, served via CDN.
- **Chart.js via CDN** for one horizontal-bar chart on the dashboard (top-10 contractors by €). Loaded only on `/`, not on detail pages, so other pages stay <50 KB.
- **Stdlib `sqlite3`** in read-only mode (`file:...?mode=ro`).
- **No JS framework**. Tiny vanilla JS only for the search-box debounce and to bootstrap the Chart.js instance. No bundler, no Node.

This stays inside the Python ecosystem already in the project, adds one dependency (`flask`), and produces a polished UI without a frontend toolchain.

### Project layout (additions to existing tree)

```
19_KHDMHS/
├── khmdhs/                              (unchanged — the ETL package)
├── webui/                               NEW
│   ├── __init__.py
│   ├── __main__.py                      python -m webui
│   ├── app.py                           Flask app factory + routes
│   ├── queries.py                       all SQL lives here, returns plain dicts
│   ├── filters.py                       Jinja filters (currency_eur, gr_number)
│   ├── templates/
│   │   ├── base.html                    layout: <header>, search, <main>, footer
│   │   ├── dashboard.html               totals + top tables + red-flag stats
│   │   ├── contractors.html             paginated/searchable contractor table
│   │   ├── contractor_detail.html       per-VAT page
│   │   ├── contract_detail.html         per-ADAM page (optional but cheap)
│   │   ├── authorities.html             contracting-authority breakdown
│   │   └── partials/
│   │       ├── _contract_row.html
│   │       └── _redflag_badge.html
│   └── static/
│       └── style.css                    custom Pico overrides (Greek font, palette)
├── data/processed/khmdhs.sqlite         (consumed read-only)
└── requirements.txt                     adds: flask
```

`webui/` lives alongside `khmdhs/` so each package has a single responsibility — `khmdhs` writes the DB, `webui` reads it.

### Routes & views

| Route | Template | Purpose |
|-------|----------|---------|
| `GET /` | dashboard.html | KPI cards (total spend €1.54 B, # contracts, # contractors, % direct-assignment 89.4 %, # single-bidder 34), **horizontal-bar chart of top-10 contractors by €** (Chart.js, data passed inline as JSON in the template), top-10 contractors table (links to detail), top-5 spending authorities, top-5 signers by € signed |
| `GET /contractors?q=&sort=` | contractors.html | All 139 contractors as a sortable table — VAT, name, # contracts, total €, % direct-assignment, # single-bidder. Live filter via `q` (VAT or substring of name). |
| `GET /contractor/<vat>` | contractor_detail.html | Header card (VAT, name(s), country, total €, # contracts, % direct-assignment, # consortium contracts), contracts table sorted by date desc, "consortium partners" list (other contractors who appear on the same ADAM), "primary signers" mini-table |
| `GET /contract/<adam>` | contract_detail.html | Full contract sheet: every field from `contracts` + objects + CPVs + NUTS, "raw API JSON" expandable `<details>` |
| `GET /authorities` | authorities.html | The 3 authorities + 12 unit operators + 15 signers, with totals — small enough to fit on one page |
| `GET /authority/<code>` | (reuses contractors.html) | Contractors filtered to this authority |
| `GET /api/contractors.json` | (JSON) | Same data as `/contractors` for ad-hoc analysis (jq, pandas) |

**Search behaviour** — the top-bar input on `base.html` posts to `/contractors?q=…`. If the query is exactly 9 digits (a VAT), it 302-redirects straight to `/contractor/<vat>`.

### Queries (`webui/queries.py`)

Pure functions, each returns a list of dicts. Examples:

```python
TOP_CONTRACTORS = """
SELECT c.vat_number,
       MIN(c.name)         AS name,
       COUNT(DISTINCT c.reference_number) AS n_contracts,
       ROUND(SUM(co.total_cost_with_vat), 2) AS total_eur,
       ROUND(100.0 * SUM(CASE WHEN co.procedure_type LIKE 'Απευθείας%' THEN 1 ELSE 0 END)
                   / COUNT(*), 1) AS pct_direct,
       SUM(CASE WHEN co.bids_submitted = 1 THEN 1 ELSE 0 END) AS n_single_bidder
FROM contractors c
JOIN contracts   co USING (reference_number)
GROUP BY c.vat_number
ORDER BY total_eur DESC
LIMIT :limit OFFSET :offset
"""

CONTRACTOR_DETAIL = """
SELECT co.reference_number, co.title, co.contract_signed_date,
       co.total_cost_with_vat, co.procedure_type, co.bids_submitted,
       co.organization_name, co.units_operator_name, co.signer_name
FROM contracts co
JOIN contractors c USING (reference_number)
WHERE c.vat_number = :vat
ORDER BY co.contract_signed_date DESC
"""

CONSORTIUM_PARTNERS = """
SELECT c2.vat_number, MIN(c2.name) AS name,
       COUNT(*) AS shared_contracts,
       ROUND(SUM(co.total_cost_with_vat), 2) AS shared_eur
FROM contractors c1
JOIN contractors c2 USING (reference_number)
JOIN contracts co  USING (reference_number)
WHERE c1.vat_number = :vat AND c2.vat_number != :vat
GROUP BY c2.vat_number
ORDER BY shared_eur DESC
"""
```

Caveat surfaced in the UI: when a contract is a consortium, **the full contract value is attributed to each partner** (it's not split). This is the "maximum exposure" view — best for OSINT, but the page should say so in a footnote.

Greek number / currency formatting via two Jinja filters in `webui/filters.py`:

```python
def gr_number(n):  # 1234567.5 -> "1.234.567,50"
def eur(n):        # 1234567.5 -> "1.234.567,50 €"
```

### Aesthetic / responsive notes

- Pico.css gives proper typography and spacing without effort.
- Custom `style.css` does just three things: brand colour, `font-family: 'Inter', system-ui` with Greek fallback, and `.redflag` badge styling (amber for >80 % direct-assignment, red for 100 %).
- Tables become card stacks below 600 px via Pico's responsive defaults — no media-query plumbing needed.
- Light/dark toggle is automatic via `prefers-color-scheme`.

### Run

```powershell
python -m pip install flask
python -m webui                         # http://127.0.0.1:5000
# or, with auto-reload during development:
$env:FLASK_APP='webui'; flask run --debug
```

The app opens the SQLite DB read-only — it cannot corrupt the data even if buggy.

---

## Section 2 — OSINT angles you can mine from the existing DB

These need **no extra data**, just queries. Roughly ranked by signal-to-effort.

1. **Direct-assignment concentration per contractor.** Already 89.4 % overall, but who is the *outlier*? A contractor receiving €N from the state with 100 % direct-assignment and never facing a competitor is the strongest single red flag in the dataset.

2. **Single-bidder pattern.** 34 contracts had `bids_submitted = 1`. Crossing this with contractors and signers reveals "preferred-vendor" pairs. SQL:
   ```sql
   SELECT signer_name, c.name, COUNT(*) FROM contracts co
   JOIN contractors c USING(reference_number)
   WHERE bids_submitted = 1
   GROUP BY signer_name, c.name HAVING COUNT(*) >= 2;
   ```

3. **Just-under-threshold values.** Greek law triggers different procedural requirements at €30K, €60K, €100K, €120K, €214K, etc. Histogram contracts by `total_cost_without_vat` in fine bins around those thresholds — a spike just below means somebody is gaming the limit.

4. **Contract-modification chains.** 23 contracts have `prev_reference_no`. Walk the chain (`prev_reference_no` / `next_reference_no`) — large value escalation between versions is interesting.

5. **Initial budget vs final cost.** The `contract_budget` field is the original estimate, `total_cost_with_vat` is the final. Contracts where `total / budget > 1.20` are over-runs and worth listing.

6. **Signer–contractor affinity matrix.** With only 15 signers and 139 contractors, a heatmap (signer × top-20 contractors) shows who awards to whom. Rows that are very narrow (one signer dominates a contractor's portfolio) are flags.

7. **Consortium / partner network.** 4 contracts are consortia. Build the bipartite contractor-contractor graph from shared contracts. Cliques here are organised bidder networks. Cytoscape.js would render this in the UI later.

8. **Geographic gating.** `nuts_code` per contract + the contractor's bid history — if a contractor only ever wins in one NUTS region, geographic gatekeeping or a regional fixer is suspected.

9. **Funding-source concentration.** `public_funding_ref_num` (PDE/ESPA codes) lets you cluster contracts by funding programme. Contractors who repeatedly catch contracts from the same funding stream are worth flagging.

10. **Name-vs-VAT mismatches.** 139 VATs map to 151 names — 12 cases where the same VAT appears under slightly different names. Could be benign (alias, restructure) or a data-entry tell. Worth listing.

11. **CPV diversity.** A contractor billing under 20 different CPV codes is either a generalist holding company or a paper shell — both interesting.

12. **Natural persons among top earners.** ΜΑΡΙΑ ΣΙΔΕRΗ on €15.9 M as an individual is unusual; query for `country='Ελλάδα'` and names without legal-form suffixes (ΑΕ / ΕΕ / ΟΕ / ΙΚΕ / ΑΤΕ) to surface them.

---

## Section 3 — additional data sources to bring in

Ranked by ROI. The first three are the highest-leverage add-ons.

1. **The other KHMDHS endpoints** (same API, same auth-free access — the lowest-hanging fruit).
   - `/khmdhs-opendata/notice` for the original tender (timing, eligibility criteria).
   - `/khmdhs-opendata/auction` for the **bidder list** — who *lost*, what they bid. Combined with `bidsSubmitted=1` this exposes whether an auction was effectively pre-decided.
   - `/khmdhs-opendata/payment` for actual disbursements — the €1.54 B "contracted" might not equal what was paid out.
   - `/khmdhs-opendata/chain/{adam}` returns the full lifecycle (request → notice → auction → contract → payment). One call per ADAM gives you the whole story.

2. **GEMI (Γενικό Εμπορικό Μητρώο)** — the Greek business registry. For each VAT: directors, shareholders, capital, founding date, registered address. Reveals beneficial ownership and connections between contractors. https://www.businessportal.gr/ (some endpoints behind a paywall, but there is a free public search).

3. **Διαύγεια (Diavgeia)** — every public-administration decision (appointments, funding allocations, awards) is published with an ΑΔΑ. Cross-reference contract `decision_related_ada` (in `raw_json.decisionRelatedAda`) and the ΑΔΑ of the unit operator's signer. Shows the political layer above the contract.

4. **TAXISnet / ΑΑΔΕ VAT validity** — confirm each contractor VAT is currently active and not a recently struck-off entity. Useful when a small VAT shows up with a giant contract.

5. **EU Financial Transparency System** — for ESPA-funded contracts you'll see them mirrored in https://ec.europa.eu/budget/financial-transparency-system/ with EU-side metadata.

6. **ΦΕΚ (Government Gazette) full-text search** — director appointments and company-registration changes are published here. Ties officials to firms.

7. **Sanctions / PEP lists** — EU consolidated list, OFAC, UK HMT, World-Check (paid). At minimum sanity-check directors against the EU list.

8. **News / media indexing** — nightly fetch of `<contractor name>` from news.google.com / Mediastack for the top-50 contractors. Even a simple "first hit URL" stored next to the contractor row is gold during investigations.

9. **Property registry (Κτηματολόγιο)** — slow and partly paywalled, but the only way to surface real-estate flows around individual contractors.

10. **Wikidata** — for state-owned vehicles like ΕΕΣΥΠ and HRADF, Wikidata already has the parent-entity graph and key officers. One SPARQL query per top-tier contractor adds context for free.

A pragmatic next implementation order: **(1) → (3) → (2) → (4)**. (1) is just more KHMDHS calls — same infrastructure as the existing `enrich_contracts` script. After that, GEMI and Diavgeia together let you bridge from "what was bought" to "who decided and who actually owns the seller".

---

## Critical files

- New: `webui/__init__.py`, `webui/__main__.py`, `webui/app.py`, `webui/queries.py`, `webui/filters.py`
- New templates: `webui/templates/{base,dashboard,contractors,contractor_detail,contract_detail,authorities}.html`, plus 2 partials
- New: `webui/static/style.css`
- Modified: `requirements.txt` (add `flask>=3.0`)
- Modified: `README.md` (add a "Web UI" section with run instructions)
- Read-only: `data/processed/khmdhs.sqlite`

## Verification

```powershell
python -m pip install -r requirements.txt
python -m webui                                 # serves on http://127.0.0.1:5000
# Manual checks:
#   /                                  totals add up to 1,537,860,894.52 €, top 10 visible
#   /contractors?q=998256075           one row, GREEN CONSTRUCTION, 8 contracts, 21.66 M
#   /contractor/998256075              page lists 8 contracts, % direct-assignment shown
#   /contractor/036692199              ΜΑΡΙΑ ΣΙΔΕΡΗ, 3 contracts, ~15.9 M, "natural person" badge
#   /contract/26SYMV018978343          full sheet, raw_json toggle works, CPVs joined " | "
#   resize browser to 360px wide       tables collapse to card stacks (Pico responsive)
#   /api/contractors.json              valid JSON, all 139 rows
```

End-to-end success = each manual check passes, no errors in the Flask log, the DB is opened read-only (writes would fail), and the page-load time is sub-100 ms (it's all in-process SQLite).

A small follow-up after approval: clean up `_explore_data.py` left in the project root from this planning session.
