# CLAUDE.md — Anti-nero contracts OSINT (evia-khmdhs)

OSINT dataset + web UI for the Greek **Anti-nero** wildfire-prevention/restoration
public-procurement programme (ΥΠΕΝ, RRF Action 16849). Flask + SQLite + Pico.css.
Everything derived is regenerable; `data/raw/` is never written to.

**Current state** (2026-08-14): 344 contracts (245 in scope; the Atlas
analytics basis is **stated net €659,290,845.34** (includes the curated
Σουφλί keying-error correction, DATA_DECISIONS 2026-08-14) — effective retired
2026-08-03, payments are their own layer: paid net €440.0M; webui keeps its
historical effective-gross presentation, now €604.5M on the same in_scope
flags), plus 7 chains / 13 contracts demoted to **`antinero_probable`**
(€9,198,921.61 net on tips): kept in the dataset, excluded from every
calculation — RRF-16849 membership unproven from primary documents
(user decision, DATA_DECISIONS 2026-08-13; curated
`khmdhs/data/probable_related.json`, presented on the Atlas front page as
«additional contracts found, probably related …»). 890 payment orders
(€565.8M paid gross, 5 Diavgeia-only with PDF-curated net amounts), all
amendment chains closed, 179/180 map contractors located, 147 linked to
GEMI profiles, 18 curated work sites, 245/245 in-scope contracts linked
to their forest authority (103-entry ΔΔ/ΔΧ registry; 3 documented
authority-less), contractor HQs geocoded via Nominatim. Refreshable via
`python -m khmdhs.refresh`.

## Hard constraints (do not violate)

- **Never query AADE RgWsPublic2** — every query emails the AFM holder. Use
  anonymous sources only; **VIES first** (`khmdhs/vies.py`: captcha-free, no auth,
  ~90% coverage on Greek corporate VATs; rejects consortium/κοινοπραξία VATs).
- **Prefer manual curation over fragile heuristics**: if a regex/rule would cover
  <80% of cases, hand-curate into a committable JSON under `khmdhs/data/`.
- **Never fabricate locations/regions** — leave rows honestly unresolved
  (`source: "consortium_unresolved"` etc.).
- **Check the contract PDF before excluding anything from scope.** Title keywords
  lie: αντιδιαβρωτικά/αντιπλημμυρικά and ΕΣΑ-reforestation contracts looked like
  sibling programmes but their PDFs declare RRF Action 16849 «…(«antiNERO»)…»
  membership → reclassified in scope (`antinero_restoration` / `antinero_esa`).
- **Never hardcode a data-derived number, never write a number from memory.**
  Every count, sum, share, median, ranking or entity name that appears in UI
  copy, chart titles, captions, KPI notes or methodology prose MUST be
  computed from the databases (API payload fields, `/api/meta` `facts`, or a
  new computed field added for the purpose) and double-checked against a
  direct SQL query before it ships; tests pin the load-bearing ones. Literal
  text is allowed ONLY for law references (ν.4412/ν.4782), identifiers (CPV
  codes, ΑΦΜ, ΑΔΑ/ΑΔΑΜ), definitional scheme dates, and audit-record facts
  quoting a documented DATA_DECISIONS event. This rule exists because a
  2026-08-03 sweep found five stale hardcoded claims on the site, including
  a top-region title that was factually wrong («Δράμα above all» — the data
  says Εύβοια leads 3.7×): hardcoded numbers rot silently on every refresh.

## Data sources & APIs

### KHMDHS open-data (`https://cerpp.eprocurement.gov.gr/khmdhs-opendata`)
- Public, no auth. Rate limit 350 req/min → throttle ~0.2s/req, honour
  `Retry-After` on 429. Data lags reality ~24h.
- `POST /contract?page=0` and `POST /payment?page=0`, body
  `{"referenceNumber": "<ADAM>"}`; ADAM format is strict `##SYMV#########` /
  `##PAY#########`. Response `content[0]` is the record; empty = not found.
- `GET /{contract,payment}/attachment/<ADAM>` → signed PDF. **429s on bursts**
  (retry ~45–60s); on throttle returns JSON, not PDF — always check `%PDF` magic.
- `GET /adamChain/<ADAM>` — the FULL procurement family: requests,
  approvedRequests, notices, auctions, contracts (siblings incl. self,
  marked `*`), payments (== `paymentRefNo`). Upstream lists are empty
  unless the ΣΥΜΒ payload declared the links. Record endpoints: `POST
  /{request,notice,auction}` + `/{kind}/attachment/<ADAM>` PDFs.
- `dateFrom` search returns all of Greece (310k rows) — useless for filtering.
- Payload quirks: `nextRefNo` is a plain **string** (an old bug indexed `[0]` and
  stored `"2"`); `contractRefNo` on payments is mostly null; `paymentRelatedAda`
  is filled on only ~7/730 payments; credit payment amounts come **already signed
  negative** («δηλώνονται με [-]») so plain SUM is correct.

### Diavgeia (`https://diavgeia.gov.gr`)
- `GET /opendata/decisions/<ΑΔΑ>.json` → metadata (beneficiary AFM, amount).
- `GET /doc/<ΑΔΑ>` → signed PDF (check `%PDF`).
- Search: luminapi with `q=organizationUid:100015996 AND subject:"<phrase>"`
  (ΥΠΕΝ; quoted phrases only, page size 100, retry on occasional 503).
- **Decision PDFs are the join key** between Diavgeia, KHMDHS and contracts:
  they stamp the KHMDHS PAY ΑΔΑΜ, cite contract SYMV ΑΔΑΜs in recitals, and the
  «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ» field is the *authoritative* contract link
  (recitals may cite entire chains). Pre-2024 decisions carry **no** PAY stamp →
  twin-match against stored payments by same chain + amount ±€1.
- KHMDHS (gross order) vs Diavgeia (net clearance) amounts routinely differ
  6–12% — keep KHMDHS as canonical.

### Other anonymous lookups
- VIES REST: `https://ec.europa.eu/taxation_customs/vies/rest-api/ms/EL/vat/<vat>`;
  name format `OFFICIAL||TRADE`, address `"STREET N   #####  - CITY"`.
  Rejects consortium/κοινοπραξία VATs.
- **GEMI publicity JSON API works token-less** (`khmdhs/gemi.py`, verified
  2026-07-25): POST `publicity.businessportal.gr/api/search` then
  `/api/company/details` — but ONLY with the complete filter payload
  (`token: null` + every dataToBeSent field); a minimal body 500s, and the
  older `/api/searchCompany` route is captcha-gated. Resolves consortiums
  VIES can't; returns address + prefecture + GEMI number
  (profile: `/company/{gemi}`). 429s on back-to-back calls (sleep ≥1-2s).
  GEMI OpenData REST needs an API key. vrisko.gr / ΣΑΤΕ for hand curation.

## Programme structure (fund codes decide phases)

| Fund (ΠΔΕ / ΣΑΤΑ 075) | Meaning |
|---|---|
| `2022ΤΑ07500000` | Anti-nero I (07.02.2022 ΥΠΕΝ↔ΤΑΙΠΕΔ framework, ΟΠΣ 5161079) — titles never say "ANTINERO" |
| `2021ΤΑ07500002` | Anti-nero II + its named components (ΕΣΑ, αντιδιαβρωτικά; ΟΠΣ ΤΑ 5201358) |
| `2023ΤΑ07500012` | Anti-nero III / IV / 2026 (ΟΠΣ 5222791) |

Fund fields are sometimes concatenated with the ΟΠΣ code → match with
`startswith`. ΤΑΙΠΕΔ (997471299) / ΕΕΣΥΠ (997104555) hold umbrella pass-through
contracts whose euros reappear in downstream execution contracts — always
excluded from aggregates (`antinero_umbrella`) to avoid double counting.

## Pipeline (ETL modules in `khmdhs/`)

**Run order after any contract change**:
`chain_loader` → `scope_loader` → `region_loader` → `forest_loader` → `studies_loader` → `categories_loader` → `payment_loader` → `linked_acts_loader`
(→ `diavgeia_loader` when ingesting new Diavgeia decisions, then `payment_loader` again).
**`python -m khmdhs.refresh` runs the whole sequence for you** after
refetching open contracts — prefer it for routine updates.

- `cli.py` (`python -m khmdhs`) — enrich the source xlsx ADAMs; resumable via
  `fetch_log`. `api.py` = HTTP (retries, 429), `extract.py` = pure JSON→rows,
  `db.py` = schema + upserts, `excel_io.py` = xlsx I/O.
- `antinero_loader.py` — loads curated `data/antinero_supplement.json` (55 ADAMs
  found via Diavgeia, missed by the xlsx export); **re-verifies each entry's
  basis** (fund/title + ΥΠΕΝ authority VAT 090273987) against the live payload
  and refuses failures.
- `chain_loader.py` — repairs prev/next link columns from `raw_json`, then
  fetches missing amendment-chain members to closure.
- `scope_loader.py` — classifies every contract via `scope.py` into
  `antinero_{i,ii,iii,iv,2026,unknown_phase,esa,restoration,umbrella,support}` /
  `non_antinero`; IN_SCOPE = execution phases + esa + restoration + unknown.
  Then: (1) amendments with weak evidence (no evidence, or unknown_phase)
  inherit the predecessor's scope, iterating; (1b) demote pass — ADAMs in
  curated `data/probable_related.json` become `antinero_probable`
  (in dataset, out of every calculation; DATA_DECISIONS 2026-08-13);
  (2) supersede pass — a
  non-cancelled successor takes the old version out of scope **unless** it is a
  «ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ» with value <0.9× parent (supplementary = additive, both
  count; same-value ΑΠΕ restatements do supersede).
- `scope.py` gotchas: Greek/Latin homoglyph soup in titles ("ANTINERO IΙ" with
  Greek iota is real) → `normalize_title` translates; within {II, III} the
  numeral glyphs are unreliable, the **fund code is authoritative**. Python
  uppercases 'ί'→accented 'Ί' → `_strip_accents` (NFD) before keyword matching;
  keyword stems are short on purpose ("ΑΝΤΙΔΙΑΒΡ") because titles abbreviate.
- `payment_loader.py` — links payments from each contract's `paymentRefNo`,
  fetches them, then **re-attributes every stored payment** to its chain tip
  (`attributed_ref` via `contract_scope.superseded_by`; payments often stay on
  the superseded original), then applies `data/payment_corrections.json`.
- `diavgeia_loader.py` — ingests Diavgeia clearance decisions (xlsx or harvest
  JSON): extracts ΑΔΑΜ stamps from the PDF text (`pdftotext -layout`, cached in
  `data/processed/diavgeia_cache/`), prefers the «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ»
  stamp, resolves the contract (drops umbrella candidates when others exist,
  requires a single chain tip), then: PAY already stored → backfill `ada`; PAY
  stamped → fetch canonical KHMDHS record; no stamp → twin-match by
  chain+amount±1, else insert `source='diavgeia'` keyed by ΑΔΑ. Foreign funds
  (`2019ΣΕ*`, `2022ΤΑ07500030`) skipped.
- Geographic layer: `region_loader.py` loads hand-curated per-contract project
  regions AND sub-Π.Ε. work sites (`data/contract_regions.json` — optional
  `"sites"` lists with PDF page+excerpt evidence → `contract_sites` table;
  `greek_regions.py` holds the Π.Ε. vocabulary: `canonical_pe()` collapses
  spelling aliases (Πρεβέζης→Πρέβεζας, …) onto the 74 canonical Kallikratis
  Π.Ε. — **the display/aggregation key on every map** — plus `PE_CENTROIDS`
  (from `data/pe_centroids.json`), the legacy Π.Ε.→NUTS-3 bridge (`nuts3_for`,
  still used for geocode validation only), city/postal→Π.Ε. and
  genitive-prefecture→Π.Ε. resolution);
  `vies_loader.py` sweeps unresolved contractor VATs through VIES into
  `data/contractor_locations.json`; `gemi_loader.py` resolves the VIES-rejected
  residue via the GEMI publicity API and backfills GEMI profile numbers
  (`"-1"` = not-found sentinel); `consortium_resolver.py` holds ~19 manually
  reviewed inferences; `geocode_loader.py` geocodes registered addresses
  once via OSM Nominatim (tiers: structured street → freeform →
  **Greek→Latin transliteration** — the public instance often misses
  Greek-script queries — → city-level; a hit is accepted ONLY when its
  postcode matches the stored one (3-digit prefix) or resolves to the
  curated Π.Ε.; results land in the JSON as `lat/lon/geo_precision`
  address|municipality|failed); `contractor_loader.py` pushes the JSON
  into the DB.
- `forest_loader.py` — links every contract to its **Διεύθυνση Δασών /
  Δασαρχείο** by whitelist-matching the curated registry
  (`data/forest_authorities.json`: 103 authorities, genitive aliases, seat
  municipality → coords from `data/greek_municipalities.json` — the
  geodata.gov.gr Kallikratis layer, ΥΠΕΣ codes, built by
  `scripts/build_municipalities.py`) against title+items (union) with
  cached-PDF fallback; amendments inherit (`inherited:<ref>`);
  `contract_overrides` pin the 6 reviewed title/items conflicts (per-lot
  bundles, keying errors) and `no_authority` documents the 3 region-scoped
  contracts that genuinely name none. Warns on new title/items
  disagreements; TODO-lists uncovered in-scope contracts. Matcher gotcha:
  fold() maps Greek→Latin homoglyphs, so connector/stop tokens must be
  folded too («ΚΑΙ» → Latin "KAI").
- Study-cost layer: `scripts/fetch_contract_pdfs.py` sweeps ALL contract
  PDFs into pdf_cache (throttled, resumable; the cache previously only
  filled incidentally via the web proxy); `khmdhs/study_costs.py` extracts
  the per-contract μελέτη cost (net of ΦΠΑ) from the canonical «Κόστος
  εκπόνησης μελετών (ΣΑΥ-ΦΑΥ)» anchor with layout-aware rules
  (after_label / after_label_wrapped incl. page-break watermarks /
  before_prose gated on the article construction — bare «€, » gaps belong
  to the previous running-sum component / prev_line; nearest-amount is
  wrong ~40% of the time). `scripts/extract_study_costs.py` emits the
  review file; verified amounts live in curated `data/study_costs.json` →
  `studies_loader.py` → `contract_study_costs` (in refresh chain).
  Contracts stating the figure twice: the contracted αμοιβή breakdown
  wins over the προϋπολογισμός δημοπράτησης estimate. ΕΣΑ design-build
  contracts itemise no study price (bundled) — honestly absent.
- Work-type category layer (DATA_DECISIONS 2026-08-14): ONE curated
  category per in-scope contract from the **descriptive project title
  inside the signed PDF** (era-dependent anchors — phase I hides it in
  the Ορισμοί under «υπό τον τίτλο»; derivatives quote only the parties →
  resolve from the parent chain; ~33 phase-II txts have font-mangled
  accents in the BODY but clean header titles), CPV tail as tie-breaker
  only. `scripts/extract_contract_categories.py` emits the review
  worksheet; verdicts live in curated `data/contract_categories.json`
  (`_categories` meta = keys+Greek labels; per-ADAM category + verbatim
  title evidence + source pdf/inherited:<ref>) → `categories_loader.py` →
  `contract_categories` + `category_labels` (in refresh chain; WARNs on
  uncovered in-scope contracts, `curation_todos` lists them). 8 keys:
  dasotexnika 154 / miktes_zones 33 / arxaiologikoi 17 / meletes 14 /
  antidiavrotika 12 / anadasoseis 8 / ylotomies 6 / ydatodexamenes 1
  (post-audit, DATA_DECISIONS 2026-08-14 second entry); /antinero
  contract pages show the category chip + a «Type of work» evidence
  block (verbatim title, provenance link to the parent version when
  inherited) via `queries_extra.contract_category`;
  Σ stated net reconciles to the basis exactly (pinned). Atlas: TYPES OF
  WORK BarH (€/count toggle) + CPV CODES list close the front page;
  labels ship from `category_labels`, never hardcoded.
- `linked_acts_loader.py` — full procurement family per contract:
  `GET /adamChain/<ΑΔΑΜ>` returns requests/approvedRequests/notices/
  auctions/contracts/payments (NOT just payments as previously noted);
  upstream acts stored in `linked_acts` (records via `POST
  /request|/notice|/auction`, PDFs via `/{kind}/attachment/`), mapping in
  `contract_linked_acts` (FK CASCADE → re-run after refetch; in the
  refresh chain). **Registry-linkage reality**: the chain only knows what
  the ΣΥΜΒ payload declared — 70/344 contracts have any upstream act,
  41/252 in-scope have a linked κατακύρωση; most direct awards were
  posted with none (the Atlas timeline says so honestly). 147 upstream
  acts stored. Atlas: `queries_extra.contract_timeline` +
  `/pdf/{request,notice,auction}/<ΑΔΑΜ>` proxy kinds.
- `completion_acts_loader.py` — project-ENDING acts from Diavgeia:
  ΚΗΜΔΗΣ has no completion record type, but ΥΠΕΝ posts «Έγκριση
  Πρωτοκόλλου Οριστικής Παραλαβής … της Σύμβασης με ΑΔΑΜ: <SYMV>» acts
  whose SUBJECT cites the contract ΑΔΑΜ → one luminapi
  `subject:"<ΑΔΑΜ>"` search per stored contract, STRICT completion
  classification (οριστική παραλαβή / περαίωση / διαπιστωτική
  ολοκλήρωσης; committee formations, παρατάσεις, ΑΠΕ, επιμετρήσεις,
  τμηματικές/προσωρινές παραλαβές rejected). Subjects saying only
  «Πρωτοκόλλου Παραλαβής» resolve from the PDF body (early acts omit
  «οριστικής»). End date = the protocol date in «το από DD.MM.YYYY
  πρωτόκολλο…» (excerpt stored, `end_basis=protocol_date`), else the
  act date. Table `contract_completion_acts` (chain-tip `attributed_ref`
  like payments; FK CASCADE; in the refresh chain). Atlas timeline shows
  them as the closing act with `/pdf/diavgeia/<ΑΔΑ>` links.
- `refresh.py` — **incremental refresh**: refetches open in-scope chain tips
  (end_date NULL or <90 days past), upserts only changed payloads (diff on
  lastUpdateDate/paymentRefNo/nextRefNo/cancelled), backs payloads up to
  refresh_backup_<date>.json first, then runs the full loader chain and prints
  a manual-curation TODO list (new chain members needing regions/scope).
- `payment_validator.py` — string-matches every stored payment amount against
  its signed PDF (exact Greek format → digit-token → tolerant); ≤€0.02 diffs
  are `near_match` noise; real mismatches are candidates for
  payment_corrections.json (human reviews the PDF first). Resumable; aborts
  after 3 consecutive 429s.
- `scripts/extract_site_candidates.py` — scans cached contract PDFs for
  site cues (ΔΑΣΑΡΧΕΙ, ΘΕΣΗ, Τ.Κ., …) into a review file; a human curates
  real sites into contract_regions.json. `scripts/export_prints.py` —
  Playwright A4 PDFs of /origins and /map (needs the dev server running).

Decision log: **`DATA_DECISIONS.md`** at the project root is the append-only
audit trail (date · decision · evidence · affected records). New data
decisions land there FIRST, then get implemented.

## Curated JSON files (committed sources of truth)

| File | Purpose |
|---|---|
| `antinero_supplement.json` | 55 contracts missing from the xlsx; phase overrides that win over all rules |
| `probable_related.json` | 7 chains / 13 ADAMs demoted to `antinero_probable`: registry titles say ANTINERO II but no provable RRF-16849 financing evidence exists (empty fund metadata, full texts without any RRF language — ΤΑΙΠΕΔ-procured, ΚΑΕ 2910601001-funded). Kept in dataset, excluded from all calculations; shown on / as «additional contracts found, probably related» |
| `payment_corrections.json` | 3 registry keying errors (×100 missing decimal; one-of-two invoices) with PDF-documented true amounts + 5 Diavgeia-only payments whose net («ΚΑΘΑΡΗ ΑΞΙΑ ΠΑΡΑΣΤΑΤΙΚΟΥ») is PDF-curated (`amount_without_vat`-only entries); `exclude:true` → treated as cancelled. Candidates come from `payment_validator` |
| `dase_contract_corrections.json` | ΔΑΣΕ contract corrections: 1 stated-value keying error (21SYMV009374147 ×10 digit-glitch, `objects` seq override) + 10 registry double-postings excluded via `exclude:true` + `duplicate_of:<kept ΑΔΑΜ>` (pages stay reachable, cross-linked; the 10th, 24SYMV015423487, is a corrected re-issue under a VIES-invalid phantom ΑΦΜ — caught cross-VAT, DATA_DECISIONS 2026-08-15). Applied by `khmdhs.contract_corrections` (standalone + end of `harvest_dase.py load`) together with `dase_payment_corrections.json` (1 duplicated payment). Candidates: `scripts/validate_contract_values.py` + `scripts/find_duplicate_postings.py` (same-VAT pass + cross-VAT pass for mis-keyed ΑΦΜ twins) |
| `contract_corrections.json` | Same format/mechanism for the khmdhs (Anti-nero) DB; currently 1: 26SYMV018642772 «ΔΧ ΣΟΥΦΛΙΟΥ» carried the Θεσσαλονίκη δεξαμενές contract's figures — PDF-documented true value €4,334,353.41 net / €5,374,598.23 gross (DATA_DECISIONS 2026-08-14). Applied by `khmdhs.contract_corrections --corrections` + a `khmdhs.refresh` step right after chain_loader (refetch/upsert restores registry values) |
| `contract_regions.json` | ~331 contracts → project Π.Ε.(s), curated from titles/Δασαρχεία; amendments inherit from the superseded version. Optional per-contract `"sites"` lists (name, pe, PDF page, excerpt) → `contract_sites` |
| `contractor_locations.json` | ~180 contractor home locations (VIES + GEMI + hand curation) + `gemi` profile numbers (`"-1"` = confirmed not in GEMI) + Nominatim `lat/lon/geo_precision` |
| `forest_authorities.json` | 103 ΔΔ/ΔΧ (canonical name, kind, genitive aliases incl. registry typos, seat municipality code, Π.Ε.) + 6 `contract_overrides` (reviewed title/items conflicts, PDF evidence) + 3 `no_authority` contracts. Since 2026-08-17 each entry also carries an **`office` block** (street/Τ.Κ./city/phones/emails + geocoded lat/lon/geo_precision): basis = the ΥΠΕΝ επιθεωρήσεις contact tables (ypen.gov.gr, Akamai-blocked for bots — fetched via WINDOWED Playwright, `scripts/harvest_ypen_offices.py`, cache `ypen_offices_cache/`) corroborated by each authority's own Diavgeia letterheads (`scripts/harvest_office_letterheads.py`, unit uids under org 100015996; 90/102 Τ.Κ. confirmed, ΑΔΑ+excerpt kept; the Γουμένισσα ministry-page typo 63100→61300 caught this way). Differences documented per-entry in `office.note`; merge via `scripts/build_authority_offices.py`, geocode via `scripts/geocode_authority_offices.py` (Nominatim tiers + Τ.Κ.-prefix/≤35km gates → 41 street / 58 postcode / 1 city / 3 municipality-fallback). `forest_loader` prefers the office point over the municipality centroid (`seat_precision` column); /authority pages show the contact block. Περτουλίου is ΑΠΘ-run (no ΥΠΕΝ office data — centroid) |
| `greek_municipalities.json` | 325 Kallikratis municipalities: ΥΠΕΣ code → name + representative centroid + **hand-curated `pe`** (the municipality's Π.Ε.; the ONLY complete municipality→Π.Ε. table — validated 4 ways by `scripts/build_pe_geojson.py`) (geodata.gov.gr «Όρια Δήμων Καλλικράτη», CC-BY; `scripts/build_municipalities.py`) |
| `pe_centroids.json` | 74 Π.Ε. → representative point (lat, lon), from the dissolved polygons; duplicated to `webui/static/` (`scripts/build_pe_geojson.py`) |
| `study_costs.json` | 116 contracts → μελέτη cost net of ΦΠΑ (page + excerpt evidence) from the «Κόστος εκπόνησης μελετών» PDF anchor; loaded by `studies_loader` into `contract_study_costs`; tips inherit from predecessors in `queries.study_costs` |
| `contract_categories.json` | 245/245 in-scope contracts → ONE curated work-type category (8-key taxonomy in `_categories` with Greek labels) + the signed PDF's verbatim project title as evidence + source (pdf / inherited:<ref>); proposals from `scripts/extract_contract_categories.py`, every verdict reviewed; loaded by `categories_loader` into `contract_categories` + `category_labels` (DATA_DECISIONS 2026-08-14) |
| `forest_units_directory.json` | Complete ΥΠΕΝ forest-service directory (DATA_DECISIONS 2026-08-17): all 151 unit rows of the 7 επιθεωρήσεις contact tables — 102 cross-linked to the contract registry, 49 without contracts (inspectorates, coordination/reforestation directorates, idle ΔΔ/δασαρχεία) shown on /authorities as «the rest of the network». REFERENCE layer only, never matcher input; `forest_units_directory` table via forest_loader; ΕΠΙΘΕΩΡΗΣΗ Μ-Θ seat (Πυλαία) seats its /dase circle. The report-mode audit (`scripts/audit_authority_links.py`) validated the 103-registry attribution against this full vocabulary: zero missed links (the one hit is the already-pinned 25SYMV016670155 override) |
| `city_to_pe.json`, `postal_prefix_to_pe.json` | address → Π.Ε. lookup tables |
| `pe_names_en.json` | 74 canonical Π.Ε. → English display names (DATA_DECISIONS 2026-08-15): basis = official Eurostat `NAME_LATN` (ELOT 743) from `data/raw/greek_nuts3.geojson` via the Π.Ε.→NUTS-3 bridge, merged units hand-split (verbatim `name_latn` + `nuts_id` evidence per entry) + user-approved familiar-English overrides (Evia, Heraklion, Corfu, Rhodes, Piraeus, Athens/Attica sectors, Attica Islands, Kefalonia, Ithaca, Rethymno, Lemnos, Kea-Kythnos; user kept Larisa/Thira/Lesvos). Byte-identical copy at `atlas/src/lib/data/pe_names_en.json` (pinned); Atlas renders «R.U. <en>» via `$lib/transforms/regions` (`peEn`/`ruLabel`) on every region surface — keys/aggregates/permalinks stay on the Greek canonical Π.Ε.; webui stays Greek |
| `authority_names_en.json`, `org_names_en.json`, `unit_names_en.json` | English display names for awarding bodies (DATA_DECISIONS 2026-08-16): 103 forest authorities («<Toponym> Forest Service Office» / «<Toponym> Forest Directorate», toponym-first; Π.Ε. names reused, ELOT elsewhere, user-reviewed forms), 49 organizations (official EN titles; keyed by exact registry strings incl. typos), 58 sub-units (municipal offices, ΥΠΕΝ signer units, seatless forest units). Byte-identical copies in `atlas/src/lib/data` (pinned); applied via `$lib/transforms/names.ts` fold-tolerant lookups with honest Greek fallback; `devGreek()` shows the Greek original as hover title in `npm run dev` only. Coverage/pins in `tests/test_body_names_en.py`. Person names, evidence quotes and co-op names stay Greek |
| `public_bodies.json` | Public-bodies registry (DATA_DECISIONS 2026-08-16, FireWatch study): 67 AWARDING bodies across all three datasets — slug key, canonical name, ΑΦΜ as attribute (090273987 shared ΥΠΕΝ/ΑΠΔ Θ-ΣΕ, never a key), closed kind vocab (37 municipality / 5 municipal_entity / 3 region / 6 ministry / 4 decentralized / 1 state_vehicle / 11 other_public; forest units stay referenced in forest_authorities/forest_units_directory), **scope** = tier-1 place-inference rule (43 municipal → municipality_code into greek_municipalities / 3 regional / 21 national — user chose strict national for ΑΔΜΗΕ, ΟΣΕ, port, hospitals, ΑΠΘ fund), 68 verbatim aliases (typos kept). Every verdict user-reviewed (`public_bodies_curator.html`, regenerated by `scripts/extract_public_bodies.py`); Δομοκού ΑΦΜ honestly null (invalid 8-digit in payload). `khmdhs.bodies_loader` (strict validation; WARNs on unknown org strings) → `public_bodies` + `public_body_aliases` in BOTH contract DBs; hooked in harvest_dase load + refresh chain; `tests/test_public_bodies.py` pins the coverage bijection over all three DBs. Location semantics unchanged: work regions stay document-curated; the registry supplies baseline/audit/presentation with the tier declared |
| `dase_display_names.json` | 249 ΔΑΣΕ co-ops → curated bilingual display names (el `ΔΑ.Σ.Ε. 'ΟΝΟΜΑ', ΤΟΠΟΘΕΣΙΑ` / en `F.W.CO-OP …`), keyed by canonical ΑΦΜ, every value user-reviewed in `dase_name_curator.html` (DATA_DECISIONS 2026-08-15: five judgment calls user-resolved, 25 mechanical homoglyph/punctuation slips normalized, phantom 031000379 dropped). Loaded by `khmdhs.dase_names_loader` (validates canonical keys + rejects cross-script names; hooked at the end of `harvest_dase.py load`) into `dase_display_names`; the Atlas overlays them on every ΔΑΣΕ co-op surface via `queries_extra.dase_display_names`/`_overlay_coop_name` (real-DB pins: bijective vs the live population, payloads == table). Presentation layer only: registry `contractors.name` spellings are never rewritten, stay searchable, and remain visible as evidence («Appears in the registry as», contract-page «in the registry»); webui (:5000, frozen) keeps registry names |

## Database (`data/processed/khmdhs.sqlite`, committed)

`contracts` (flat ~50 cols + `raw_json`) with child tables `contractors`,
`contract_cpvs`, `contract_nuts`, `contract_objects` (FK **ON DELETE CASCADE**),
plus `fetch_log`, `contract_scope`, `contract_project_regions`,
`contract_sites`, `contract_payments`, `contractor_locations` (incl. `gemi`,
`lat/lon/geo_precision`), `forest_authorities` (seat coords) and
`contract_forest_authorities` (FK CASCADE; `source` =
title/objects/pdf/override/inherited:<ref>).
Post-hoc columns are added via the ALTER-TABLE guard loop in `db.py:init_db`
(CREATE TABLE IF NOT EXISTS won't alter deployed DBs).

**CASCADE gotcha**: `INSERT OR REPLACE INTO contracts` deletes + reinserts the
row, which cascades away `contract_scope`, `contract_project_regions`,
`contract_sites` and `contract_forest_authorities` rows. After ANY contract
refetch, re-run `scope_loader` + `region_loader` + `forest_loader` (or just
use `khmdhs.refresh`, which does).

**Effective value** (`webui/queries.py:effective_cost`): SUM of non-cancelled
payments on `attributed_ref` when ≥1 exists, else stated `total_cost_with_vat`.
Applied to every aggregate. This absorbs amendments and shows actual
disbursement for running contracts.

## Web UI (`webui/`, read-only Flask)

Routes: `/overview` (flagship "where the money went" page: **two side-by-side
paper maps** under a 2-mode toggle — `?view=points`: a contract-count
choropleth by forest-authority-seat region (drilling into a region swaps it
for one equal-size dot per contract×authority, jitter-spread via a
deterministic sunflower spiral, click→contract; single-authority contracts
share one neutral colour, each multi-authority contract gets its own OKLCH
hue so its dots group, and hovering such a dot draws dashed lines in that
colour linking ALL the contract's authority seats — incl. off-region ones,
so a line running off-frame means the contract spans further) beside one
dot per geocoded
contractor address (click→contractor); `?view=money` (default): € choropleths
by work region and by HQ region on the **same YlOrBr ramp and shared max**
for comparability — **even-split € attribution** summing to the programme
total + exposure in tooltips; legacy 4-mode `?view=` values redirect. All
map tooltips are pinned to the map's lower-left corner
(`GeoCommon.pinnedTip`), never mouse-following. All
maps are zoom-locked (no user zoom/pan); on the points view **clicking a
Π.Ε. drills down** (client-side, `&focus=works:Π.Ε. Ευβοίας`/`home:…`
permalinks; legacy ELxxx focus values degrade to the country view):
left-map click zooms the left map to the Π.Ε.'s forest authorities **and
overlays its interior municipality borders** (lazy-loaded
`greek_muni_borders.geojson`, dashed, non-interactive) **and swaps the
coarse polygons for the in-view slice of the high-res layer**
(`greek_pe_hires.geojson`, lazy) while filtering the
right map to the contractors holding those
contracts; right-map click mirrors it; while drilled the analytics below are
replaced by the region's contracts (sorted by value) and its contractors'
€-from-region / work-region € tables, with an "All of Greece" reset pill.
Data for the drill ships once via `/api/overview.json` `contracts` (compact
per-contract contractors+authorities+region-splits). Default analytics below
the maps: contract-value histogram (log-spaced doubling bins), clickable
top-10 contractors, top-10 μελέτη costs (study_costs, chain-inherited), authorities/signers, procedure-mix stacked bars), `/` dashboard
(KPIs + top-10 chart +
cumulative disbursement per phase + direct-award histogram with ν.4782/2021
threshold lines), `/contracts`, `/contract/<adam>` (payments, work sites,
PDFs), `/contractors`, `/contractor/<vat>` (location + ΓΕΜΗ link + mini-map
of home + project regions + money-per-year paid/stated chart),
`/authorities`, `/map` (Leaflet flow map, full-exposure convention),
`/origins`, `/api/{contractors,flows,timeseries,overview}.json`,
`/pdf/<kind>/<adam>`, plus the ΔΑΣΕ section (`/dase*`, `/compare` — own
module `dase_queries.py`, second lazy read-only connection; see the
ΔΑΣΕ dataset section below). Shared paper-map helpers in
`webui/static/geo_common.js`. **All maps draw the 74 Π.Ε. polygons** in two
detail levels built from the full-resolution EPSG:2100 Kallikratis
shapefile (`data/raw/oria_dhmwn_kallikraths/`) via GEOS
**`coverage_simplify`** (topology-preserving: shared borders identical on
both sides, zero slivers): eager `greek_pe.geojson` (220 m, country view) +
lazy drill-zoom `greek_pe_hires.geojson` (30 m ≈ 2 px at the deepest
Πειραιώς zoom; the client renders only in-view features) and
`greek_muni_borders.geojson` (interior municipality border lines per Π.Ε. —
coastline excluded, it IS the Π.Ε. outline), + `pe_centroids.json`
(`scripts/build_pe_geojson.py`, run with SYSTEM python3 for
geopandas/shapely≥2.1; the retired Eurostat NUTS-3 polygons live on in
`data/raw/greek_nuts3.geojson` as the build script's cross-check). All SQL
lives in `queries.py`;
region aggregates key on `canonical_pe(region_pe)`; aggregates filter on
`contract_scope.in_scope = 1` (fallback: exclude state-vehicle VATs). Search is accent-, homoglyph- AND
Greeklish-tolerant (`_phonetic_fold`: "evias" finds «Ευβοίας»); all filter
state is in GET params, so every view is a shareable permalink.

`/pdf/...` is a caching proxy: validates the ADAM shape, fetches once into
`data/processed/pdf_cache/` (PDFs gitignored; the pdftotext `.txt`
sidecars in pdf_cache/diavgeia_cache/anadohoi_cache ARE tracked since
2026-08-13 — arogi_cache stays fully ignored: its act texts carry
victims' names), refuses non-`%PDF` bodies, serves
inline (`as_attachment=False`) so PDFs open in the tab, and returns an
auto-retrying `pdf_wait.html` (503 + Retry-After) during registry 429 windows.

Consortium contracts attribute the **full** value to each partner (max-exposure
view, stated in the footer).

## ΔΑΣΕ dataset (`data/processed/dase.sqlite` — SEPARATE from Anti-nero)

Standalone DB of every contract 2021-09→today whose contractor is a
forest labour cooperative (ΔΑ.Σ.Ε./ΑΔΣΕ/ΕΔΑΣΕ, ν.4423/2016 — example
26SYMV019413118): 2,164 contracts, €47.0M gross, ~252 co-ops.
**Contractor-led harvest, NOT CPV-led** (the example's only CPV is
77312000-0, outside the 772 δασοκομία family — CPV-first provably
misses). `scripts/harvest_dase.py` (resumable: collect → close → load)
sweeps KHMDHS search (`api.search_page`; body fields `contractorName`
substring case/accent-sensitive, contractor-side `vatNumber`,
`cpvItems`; the server clamps every query to a 6-month submissionDate
window ending at dateTo → explicit ≤5-month windows; 404 = zero matches;
totalElements unreliable on cpvItems — page to `last`, dedupe by ref) in
3 passes: name variants → forest-CPV recall check → per-VAT closure +
chain completion. `khmdhs/dase.py:classify_name` proposes (word-bounded
ΔΑ.Σ.Ε/ΑΔΣΕ/ΕΔΑΣΕ tokens — «ΔΙΑΣΚΕΔΑΣΕΩΣ»/«ΛΕΙΒΑΔΑΣΕ» are real false
positives), every distinct VAT is human-reviewed into curated
`khmdhs/data/dase_contractors.json` (ΚΟΙΝΣΕΠ/ΚΟΙΣΠΕ/urban co-ops
excluded; registry keying noise: two ΑΦΜ glued with «ΚΑΙ», stray accent
prefixes, whitespace-variant VAT keys). Uses the shared khmdhs schema
(scope tables stay empty); nothing touches khmdhs.sqlite.
PDF/txt cache: **complete** (2026-08-14) — all 2,164 contract PDFs in
`data/processed/dase_pdf_cache/` (0 missing, 0 unreadable; PDFs
gitignored ~918MB, the 2,164 .txt sidecars ~7.6MB tracked — user
decision 2026-08-14; refetch via `scripts/fetch_contract_pdfs.py --db
data/processed/dase.sqlite --cache data/processed/dase_pdf_cache`);
`scripts/validate_contract_values.py` screens every stored stated value
against the extracted text (statuses ok/ok_net_only/near_match/
`decimal_shift_suspect`/mismatch/no_pdf/unreadable; direct ÷10 ÷100 ×10
probes + `shift_factor` ratio fallback — the flagship error was a digit
GLITCH at ratio 10.0000079 a clean division misses; suspects are
candidates, corrections land only after human PDF review). Curated fixes:
`khmdhs/data/dase_contract_corrections.json` →
`khmdhs.contract_corrections` (standalone CLI + end of every
`harvest_dase.py load`, whose INSERT OR REPLACE restores registry
values; corrected rows carry `contracts.correction_note`, and a
sibling-modal guard test fails on any live uncorrected ≈×10/×100
outlier). CPV quirk resolved (DATA_DECISIONS 2026-08-17): 386 rows
carry insurance CPV 66519300-4 on υλοτομικά contracts — NOT a keying
error: it tags the award's «ΑΣΦΑΛΙΣΤΙΚΕΣ/ΕΡΓΟΔΟΤΙΚΕΣ ΕΙΣΦΟΡΕΣ (ΕΦΚΑ
ΕΡΓΟΔΟΤΗ)» component (in 207/386 payloads the CPV sits on exactly that
object line; the τιμές-ανάθεσης ΚΥΑ exclude the employer's ΕΦΚΑ
contribution, which the State bears as forest exploiter, άρθρο 137 §3
ν.δ. 86/1969). Still flagged wherever CPVs show, never counted as
insurance procurement.

**Parity harvest** (2026-08-03, DATA_DECISIONS): `linked_acts_loader --db
dase.sqlite --with-payments` swept all 2,164 adamChains (0 missing; 1,668
upstream acts — 1,550 auctions, 164 notices, 1,218+1,219 requests; family
payment ΑΔΑΜs recorded as kind='payment' mapping rows). Then
`payment_loader --db dase.sqlite --refs-from-linked-acts --corrections
<nonexistent>` fetched **1,033 payments (41 cancelled), Σ paid net
€21,298,411.32 on 891 live contracts** — with **strict family
verification**: a chain-derived payment whose payload `contractRefNo`
names a non-stored contract is REFUSED (`foreign_family` in fetch_log; 72
of 73 chain-only payments paid non-ΔΑΣΕ sibling lots of multi-lot
procurements — without the check they'd inflate the co-op paid figure),
and one naming a different STORED contract re-links to it. adamChain
returns the whole family's payments, so pending pairs are deduped by
payment ΑΔΑΜ (5,297 pairs ≈ 1,105 distinct). Attribution is identity (no
contract_scope in this DB). Completion acts: **negative
finding** (DATA_DECISIONS 2026-08-03) — 75 probed contracts → 1 hit, 0
completions; δήμοι never cite the ΑΔΑΜ and bundle παραλαβές in plural
municipal approvals, so ΔΑΣΕ endings stay honestly unharvested
(/explore `fin` = NULL; `completion_search_log` records the probes; the
loader's `--query-mode bare`/`--cache`/`--resume` flags remain for any
future attempt).

**Analytics conventions** (DATA_DECISIONS 2026-07-27, basis 2026-08-03):
aggregates use **stated values, deduplicated** — exclude `cancelled=1`
(82 rows, €2.35M) and non-cancelled rows whose `next_reference_no`
resolves in-DB (64 rows, €3.24M; verified column == raw_json nextRefNo,
no multi-successor) → live population **2,008 rows / €38,411,933.17
gross = €31,659,523.06 net** (`dase_queries.live_filter`, the
scope_filter analogue; the Atlas presents net; includes the curated
corrections — the 21SYMV009374147 ×10 keying error AND 10 registry
double-postings excluded with `duplicate_of` cross-links + 1 duplicated
payment (paid net €21,211,472.57 / 991 orders), DATA_DECISIONS
2026-08-14 + 2026-08-15 (the 10th hid behind a phantom contractor ΑΦΜ
«0310003799» — VIES-invalid — so the scanner gained a cross-VAT pass);
duplicate pages stay reachable, badged in search, and the
guard `scripts/find_duplicate_postings.py` + real-DB tests keep new
twins out). Charts/rankings STAY on
stated values — payment coverage is structurally partial (891/2,008
contracts, 2022–23 near-blank as registry practice) — the paid-net Σ
appears only as a KPI with its coverage caveat. Co-ops key on
the **canonical VAT** (first 8-9-digit run zfill(9) — same co-op under
3+ spellings; 096034999 ≈ €1.9M across 12 name variants) and are
PRESENTED under their curated bilingual display names
(`dase_display_names.json` → `dase_names_loader` →
`dase_display_names` table → Atlas overlays; registry spellings stay
searchable + visible as evidence); awarding
orgs group by normalised `organization_name`, never VAT (090273987
carries both ΥΠΕΝ and ΑΠΔ ΘΣΕ rows). **Π.Ε. layer**:
`khmdhs/dase_region_loader.py` derives each contract's Π.Ε. from
`units_operator_name` — folded trigger-stripped exact match against
forest_authorities.json aliases (1,982 contracts) + curated
`khmdhs/data/dase_units.json` (org→unit keys, exact strings incl.
Latin-homoglyph «TMHMA»/«OIKONOMIKO»; per-contract `contract_overrides`
for supra-regional awarders ΟΣΕ/ΓΕΑ/ΑΠΘ/ΕΠΙΘΕΩΡΗΣΗ Μ-Θ, evidence note
required) → `dase_contract_regions` (2,160/2,164 = 99.8%; the 4 ΑΔΜΗΕ
power-line contracts span multiple Π.Ε. — honestly unresolved).
ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ lives in dase_units.json, NOT forest_authorities.json
(that registry feeds the Anti-nero matcher). `nuts_code` is cross-check
only (~20% coarse; EL611/EL531 span two Π.Ε.).

**Web UI**: `/dase` (dashboard: KPIs, per-year, size histogram with
log-interpolated median line, Π.Ε. choropleth via GeoCommon, top-10
co-ops, orgs/units/procedure/type/CPV tables), `/dase/contracts`,
`/dase/contractor/<vat>` (canonical-VAT merged), `/dase/contract/<adam>`
(via the self-guarding `queries.contract_detail`; PDF proxy works for
ΔΑΣΕ ADAMs unchanged) and `/compare` (Anti-nero vs ΔΑΣΕ: KPI pair with
basis labels, absolute + %-of-own-total yearly bars, shared-log2-bin
size-distribution overlay with median markers, per-Π.Ε. paired bars,
methodology footnotes — Anti-nero €604.5M effective vs ΔΑΣΕ €38.4M
stated ≈ 15.7×). Atlas /dase (2026-08-13): redesigned to the shared hero (green
cards + direct-award bar + paid card) and kicker titles; its map is now a
**proportional-symbol map** — one circle per awarding forest unit at its
`forest_authorities` seat (area = Σ stated net €, label = n, tooltip
median; join via `dase_contract_regions.source` `registry:<name>`),
kind-coloured per the user's legend mock, FOUR kinds since 2026-08-15:
dd «forest directorate» #406e55 / dx «local forest service office»
#6fb28c / «regional or municipal authority» solid black at Π.Ε.
centroids (δήμοι+περιφέρειες+their νομικά πρόσωπα — since 2026-08-16
classified by the public-bodies REGISTRY scope municipal/regional via
`public_body_aliases`, not name stems; unknown orgs render grey and the
loader WARN + bijection test scream first) / «other public body» grey
#9b9b9b (εφορείες αρχαιοτήτων, ΟΣΕ, port, ΑΠΘ, hospital, ΓΕΑ). Seatless forest units (Δασαρχείο Φουρνά, ΔΔ
Ηλείας/Ν. Πιερίας/Χαλκιδικής, the supra-regional ΕΠΙΘΕΩΡΗΣΗ — 6
circles) stay GREEN, drawn at their Π.Ε. centroid; same-centroid
circles spread right by radius so none hides. ΑΔΜΗΕ off-map in
the caveat, EFFIS burn scars ≥2021 underneath (attribution on the
frame); grey legend panel docked RIGHT of the map, top-aligned (dot
key, nested-circle size icon, «burnt areas» white→maroon year-gradient
bar); click a circle → its contract table docks below the legend
(bold n/median/total header; columns ΑΔΑΜ-link · awarding unit ·
co-op display name · DD.MM.YYYY · €; rows in the payload), click a
Π.Ε. → zoom; payload `/api/dase/map`
reconciles to the
basis (pinned). /dase contract pages draw the ΚΗΜΔΗΣ family as a
FamilyTree diagram (trunk → award fan → contracts, viewed contract's
trail green, payments terminal; award↔contract edges only on
name-verified pairs — `contract_timeline` ships `who` for in-db
siblings; the table below stays the accessible view). webui /dase keeps
its frozen choropleth. All SQL in
`webui/dase_queries.py` (imports search/bin
helpers from queries.py; `queries.antinero_yearly` is the one
khmdhs-side addition). Second sqlite is opened by a **lazy
`g.dase_conn` accessor** — khmdhs-only routes never touch dase.sqlite
(tested: khmdhs JSON endpoints byte-identical with the ΔΑΣΕ DB absent).

## Ανάδοχοι αναδάσωσης/αποκατάστασης dataset (`data/processed/anadohoi.sqlite`)

Third dataset: the ν.998/1979 **άρθρο 42 §3** sponsor scheme (13.08.2021 ΠΝΠ;
ΥΑ Β΄4080) — private companies finance/execute restoration of burnt public
forest land, appointed by administrative act. **Diavgeia-only universe** (no
procurement → no KHMDHS; act metadata is empty of substance — type 2.4.7.1,
no relatedDecisions even on amendments → the signed PDFs are the source).
State (2026-08-12): **322 decisions → 69 projects** (51 registry spellings /
36 sponsor groups after the Lidl Greek/Latin-script merge — labels are
presentational `_SPONSOR_GROUPS` in queries_extra, rows keep the acts'
verbatim names; «Coca-Cola (3Ε / Hellas)» names both legal entities of the
restatement pair: ΔΕΗ, EREN, Lidl, Dior,
Πειραιώς/Εθνική/Eurobank, ΤΙΤΑΝ, WWF …), 43 stated budgets, headline
committed **€41.78M net-where-stated** (`COALESCE(budget_net_eur,
budget_current)`; VAT basis curated per act: 15 explicitly net / 2 gross —
Lidl ΨΧΟ2 states both so its net €241,936 is used, ΔΕΠΑ ΨΒ8Λ's €35k equals
its cited study's incl-ΦΠΑ cost / 27 unstated, never converted), 147.5k
στρέμματα; status: 14 completed / 32 active / **21
no_completion_recorded** / 1 revoked (Coca-Cola withdrew by letter) / 1
superseded. `projects` columns `budget_vat_basis` + `budget_net_eur`,
evidence key `budget_vat` (verbatim, mechanically verified ⊂ act text).

- `scripts/harvest_anadohoi.py` — resumable: seeds (2 raw list exports) +
  luminapi subject sweep across ALL orgs (pre-2022 acts live under ΑΠΔ Θ-ΣΕ)
  + **ΑΔΑ-citation crawl to closure** (recitals cite parents/μελέτες);
  classifier proposals via `khmdhs/anadohoi.py:classify` are never final —
  titles lie both ways («ΔΩΡΕΑ…» is an orismos, «ΠΡΩΤΟΚΟΛΛΟ ΕΓΚΑΤΑΣΤΑΣΗΣ…»
  quotes one). Cache `data/processed/anadohoi_cache/` (json/pdf
  gitignored, `.txt` tracked).
- Extraction: deterministic regex (amounts/στρέμματα/dates/ΑΔΑ citations;
  «Αποφασίζουμε» can be letter-spaced → `operative_window` folds) + haiku
  batch proposals gated by a verbatim-excerpt verifier (excerpt ⊂ PDF text,
  value ⊂ excerpt; ~10% of fields failed and were hand-extracted — incl. two
  hallucinated deadlines/funders the verifier caught). Everything lands in
  curated **`khmdhs/data/anadohoi_projects.json`** (per-field evidence,
  decision_overrides with reasons) — the committed source of truth.
- `khmdhs/anadohoi_loader.py` → tables `decisions` / `projects` /
  `project_decisions` / `meta`. Status derived as of load date
  (meta.status_as_of): completed (latest of multiple lot-completions) /
  revoked / superseded (restatements: 6ΗΥΗ→ΨΟΕ8) / no_completion_recorded
  (deadline passed, no act found — NOT "abandoned") / active.
  `deadline_current`/`budget_current` absorb amendments. Gotchas: parent =
  the operative «Τροποποιούμε…» sentence (recitals cite whole histories);
  ΑΔΑs suffer 1↔Ι homoglyphs and line-breaks in PDFs; two in-act year typos
  corrected with notes; the revoked Coca-Cola restatement was never
  published — revocation attached to the published root 63ΡΧ.
- Non-fire same-instrument acts are IN (plane-disease sanitation ALFA
  WOOD/ΑΚΡΙΤΑΣ, salvage logging, δωρεά-funded ΣΤΑΝΤΑ) with notes; 2 projects
  honestly pe-NULL (supra-Π.Ε.). Tests in `tests/test_anadohoi.py` (units +
  real-DB pins incl. status counts, Σ budgets, and the three curated-field
  pins below).
- **Curated `deliverables`** (2026-08-12, 69/69 root-act PDFs
  human-reviewed): what each appointment covers — εκτέλεση έργου (42) /
  μελέτη και έργο (18) / μελέτη only (9) — from the operative
  «Ορίζουμε … με σκοπό …» sentence, verbatim excerpt in
  `evidence.deliverables`. Regex only proposed (Greek inflection broke a
  naive pass on 22 acts); every verdict is the user's. Convention: a σκοπός
  phrased «υλοποίηση μελέτης» = εκπόνηση μελέτης → `study` (ΡΛ16, 9Φ9Ρ) —
  but TRAIL EVIDENCE beats the σκοπός wording: ΨΤΑΤ was reclassified
  study→study_and_works 2026-08-13 because its acts show ΣΤΑΝΤΑ itself
  executing the Μύλος-ρέμα works. The όροι boilerplate lies — acts
  stating «σύμφωνα με τα οριζόμενα στην … σχετική μελέτη» are works-only
  (someone else did the study).
- **Curated `executors`** (2026-08-12): the sponsor→ΔΑΣΕ link is systemic —
  all 322 decision PDFs swept (34 fetch failures: timeouts + homoglyph
  ΑΔΑs), **13 projects name executing forest co-ops** (23 rows: name,
  `dase_vat`, source-act ΑΔΑ, verbatim excerpt). Identity policy: `dase_vat`
  ONLY where the wording pins a single ΔΑΣΕ-registry entry, plus
  user-reviewed verdicts for the ambiguous ones (DATA_DECISIONS
  2026-08-16 + 2026-08-17): BOTH Μίστρου rows → 996895246 (the
  registry's SOLE Μίστρου co-op; its own spellings include «ΔΑΣΕ
  ΜΙΣΤΡΟΥ» and «ΜΙΣΤΡΟΣ-ΑΓ.ΚΥΠΡΙΑΝΟΣ»), «Σιδηρονερίου» → 096133603
  (the village's TITLELESS co-op of five candidates), «Περτουλίου
  Τρικάλων» → 997129709 ΤΖΙΑΤΖΙΑΣ. Identity-fix documentation lives
  in `curation_note` (curated JSON + API payload, NEVER rendered on
  the cards — user rule); the visible `note` is only for user-facing
  honesty notes. Still VAT-less: Παντουρέ/Παπάδων (absent from the
  ΔΑΣΕ contracts universe — nothing to link). Verdicts applied to the
  curated JSON and the sqlite in place. Known TODO: the Eurobank Ζώνη-5 evidence acts (6ΔΤ1…) are
  stored decisions with no `project_decisions` links. UI: /anadohoi
  executors section + project-page «Works executed by» (chips →
  `/dase/coop/<vat>`). Pinned executors PRESENT under their ΔΑΣΕ
  display names (DATA_DECISIONS 2026-08-16, same ΑΦΜ → same name:
  `queries_extra.overlay_executor_names` on both /api/anadohoi
  endpoints swaps `name` for display_el + adds `name_en`, keeps the
  act's verbatim spelling as `act_name` — still visible in excerpt
  tooltips/quotes; degrades to act spellings without the ΔΑΣΕ DB);
  VAT-less rows keep act names. Real-DB pin
  `test_executor_display_name_pins` guards the coverage.
- **Curated `works_zones`** (2026-08-12/13): 6 Εύβοια projects carry their
  digitised zone ids (basis: each act's basin citation; ΡΕΧΥ/ΔΕΔΔΗΕ = all
  NINE zones — its μελέτες table funds both Δασαρχεία, corrected
  2026-08-13 with `evidence.works_zones`). Loader schema is now **29 cols**
  (deliverables/works_zones/executors); the committed sqlite was migrated
  IN PLACE for these fields (ALTER+UPDATE) because harvest.json lives only
  on the Windows build machine — a plain loader re-run here can't rebuild.
- **Curated `work_sites`** (2026-08-13, branch anadohoi-work-sites): exact
  θέση-level work locations — **58 projects / 105 sites** extracted from
  root AND linked acts (amendments carry finer sites; cross-Π.Ε. allowed
  with note), each with verbatim excerpt + `source_ada` (mechanically
  verified ⊂ cached txt). Geocoded 100/105: Nominatim tiers + web research
  with per-pin `geo_source` URLs (Νέζης toponym dictionary, the Attica
  flood Master Plan, Diavgeia, OSM/Overpass) + municipality centroids;
  `geo_precision` ∈ site(58)/locality(32)/municipality(10); 5 honestly
  unresolved (Δαδιά deep-forest toponyms, unnumbered υπολεκάνες).
  Validation gates: Π.Ε. agreement, ≤15 km municipality distance, EFFIS
  burn-scar cross-check (82/92 inside-or-≤2 km; FARs documented — beware
  wrong-namesake hits: Τατοΐου-street venues, the Pentelikon hotel, the
  Ωρωπός «Πλατανάκι»). Loader is now **30 cols** (validates evidence +
  the lat/lon-iff-precision rule); `scripts/geocode_work_sites.py`
  re-geocodes entries missing coords. Atlas: /anadohoi map draws one dot
  per site (fallback zone-centroid → Π.Ε.-centroid), zoom ENABLED in
  prod, de-overlap spread arms only at k≥2 (true positions at country
  view), hover links a project's dots with dashed lines, approximate
  dots render dashed+lighter; project pages get `SiteMap.svelte`;
  `LocationCurator` is per-site (TAB-separated export).
- **Linked `effis_scars`** (2026-08-13): 63 projects carry the EFFIS burn
  scar(s) of their fire — `scripts/link_effis_scars.py` matches by fire
  year + anchors (coordinated work_sites; zone centroids), basis
  contains/near(≤2 km)/region-year (≥500 ha for the region fallback);
  plane-disease projects and the far-from-scar Λίμνη pilot honestly link
  none. Ids resolve against the display layer (build_effis_layer.py now
  emits the EFFIS feature `id` — rebuild BOTH copies together). Loader is
  **31 cols**. Project pages draw the scar under SiteMap pins / ZoneMap
  zones (scar-only maps for regional projects) with the mandatory
  «© European Union, Copernicus EMS — EFFIS» + estimates caveat.
- **Β. Εύβοια works zones** (2026-08-12): the 9 Master-Plan flood-works
  zones (ΛΙΜΝΗ Ι–V, ΙΣΤΙΑΙΑ Ι–ΙV; sheets 4.1/4.2 in `data/raw/XARTHS_*`,
  ΥΛΗ 11.2021, 1:30.000) digitised: user-corrected pixel vertices in
  curated `khmdhs/data/evia_works_zones_digitised.json` (the source of
  truth, with the ΕΓΣΑ87 grid anchors, 721.75 px/5 km) →
  `scripts/build_evia_zones.py` georeferences, clips to the hires Εύβοια
  coastline, orients rings **CW for d3-geo's spherical winding**
  (deliberately anti-RFC 7946 — rewind before feeding other GIS) and
  writes the geojson twice (`data/processed/` + `atlas/static/geo/`, must
  stay byte-identical — pinned). Digitised-vs-sheet-table areas 70–100%
  (sheet 4.1 misprints Λίμνη ΙV: «20.6827,401» = 206,827 στρ). Site:
  `ZoneMap.svelte` on project pages, `ZonesLayer.svelte` under the
  /anadohoi map dots (zone-mapped dots sit at zone centroids). Tests:
  `tests/test_evia_zones.py` (9 zones, area bands, bbox, CW winding,
  copies identical).
- `data/raw/BurtScars_EFFIS_2008-2025.geojson` (sic — typo'd name): 20 MB
  Copernicus EFFIS burnt-area export for Greece 2008–2025, EPSG:3035;
  provenance, attribution duty and hygiene notes in DATA_DECISIONS
  2026-08-13. Display copy built by `scripts/build_effis_layer.py`
  (simplify 120 m in 3035 → WGS84 → CW winding → props yr/ha/name,
  1.1 MB) into data/processed/ + atlas/static/geo/effis_fires.geojson;
  shown on /anadohoi «PROJECTS AND FIRES THAT TRIGGERED THEM»
  (`FiresLayer.svelte`, #6b2d35 year gradient, attribution in the frame
  caveat). Satellite estimates, never to be mixed with ΦΕΚ οριοθετήσεις
  unlabelled.

## Αρωγή πυροπλήκτων dataset (`data/processed/arogi.sqlite` — 4th DB)

State aid to wildfire victims, fires ≥2021 (DATA_DECISIONS 2026-08-03),
dual-sourced. **Diavgeia side**: `scripts/harvest_arogi.py` (staged,
resumable: fires/acts/pdfs/extract/audit; cache `arogi_cache/` gitignored)
sweeps the ΓΔΑΕΦΚ act families → 4,063 acts, 1,797 issued ≥2021 with PDFs;
`khmdhs/arogi.py` extracts deterministically — fire citations (acts
attribute by the fire cited in RECITALS, never issue date; 620 acts
serving pre-2021 fires excluded), Σ.Σ. amounts from the hash-delimited
table row (arithmetic-checked total=ΔΚΑ+δάνειο; all-dots decimals
'65.982.92'=65,982.92; the ΔΩΡΕΑΝ-ΚΡΑΤΙΚΗ-ΑΡΩΓΗ row preferred over
ΠΡΟΫΠΟΛΟΓΙΣΜΟΣ hash-runs), permit-number case keys (follow-ups cite them
only 13% → rows are FLAT acts with 57 genuine multi-act groups).
`khmdhs/arogi_loader.py` + curated `khmdhs/data/arogi_fires.json` (10
in-scope fire units; Jul/Aug 2021 is ONE unit like its οριοθέτηση; Μάτι
2018 kept in_scope=0) → 1,077 cases, 911 fire-matched, Σ approved
€30,291,740.26. **Official side**: `arogi_press_totals.json` (26
announcements, VERBATIM quotes + URLs/Wayback; the 2021 series ends
€41,400,301.97/8,872 — findings: 2024 ΒΑ Αττική trail stops at
€731,409/162 with no final total; NO totals for any 2025 fire) +
`elga_fire_compensation.json` (per-year, report-page evidence).
**Privacy hard rule: owner names are NEVER stored or displayed.**
Atlas: `/arogi` (case table), `/arogi/case/[key]` (act trail + PDFs via
/pdf/diavgeia, arogi_cache fallback), `/arogi/summary` (bases side by
side, mismatches highlighted, never merged).

## Atlas (second web UI: `atlas/` SvelteKit + `atlas_api/` Flask JSON API)

A separate, publication-grade site over the same two DBs — **`webui/` is
frozen**: `atlas_api` imports `webui.queries` / `webui.dase_queries` /
`webui.filters` read-only and never edits them; ALL new SQL goes in
`atlas_api/queries_extra.py`. The `/pdf/<kind>/<adam>` caching proxy is a
verbatim Blueprint copy (`atlas_api/pdf_proxy.py`, standalone
`pdf_wait.html`) sharing the same `data/processed/pdf_cache/`.

- **Net-of-ΦΠΑ basis** (DATA_DECISIONS 2026-08-03): the Atlas presents every
  € excl. VAT. Mechanism: `queries_extra.apply_net_basis(conn)` installs
  TEMP views on the kh + dase connections that shadow `contracts` /
  `contract_payments` with the net column exposed under the gross column's
  NAME (SQLite resolves unqualified names temp-first) — so the frozen webui
  SQL computes net with zero call-site changes. **Gotcha: JSON field names
  keep their historical `*_with_vat` names but carry net values on Atlas
  endpoints**; the true gross is exposed as `total_cost_gross` /
  `amount_gross` on the views, via `main.contracts`, and as the `gross`
  supplement on contract-detail endpoints (`queries_extra.contract_gross`).
  webui (:5000) opens its own connections without the shim and keeps its
  historical incl-VAT presentation. Never apply the views to the anadohoi
  DB (no VAT columns; its net preference is explicit
  `COALESCE(budget_net_eur, budget_current)`). Statutory footnote: the
  ν.4412 εκτιμώμενη αξία (and the €30k/€60k άρθρο 118 ceilings) is defined
  χωρίς ΦΠΑ, so the net basis FIXED the direct-award chart's old
  gross-vs-net mismatch. Synthetic test fixtures default net = gross so
  expectations hold on either basis. The three dataset pages open with
  harmonised KPI rows (stated net / paid net / median net / counts /
  % direct).
- **Rebrand «FORESTRY WORKS TRACKER»** (2026-08-12, commits
  b35e5db…1d7161e): white paper (cream retired), `--c-antinero` is now
  BLACK, `--c-dase` green `#52b788`; sticky compacting header (base.css
  `scroll-padding-top` keeps `#anchors` clear). Nav is 4 primary tabs +
  a MENU ▾ dropdown: SPONSORED WORKS (/anadohoi) · ANTINERO WORKS (/) ·
  FOREST CO-OP WORKS (/dase) · EXPLORE, then ΑΡΩΓΗ · Compare ·
  Connections · Authorities · Methodology in the menu; active tab renders
  in its dataset hue. Fonts are now **Adobe Typekit loaded from
  use.typekit.net in app.html** (futura-100-greek UI + obviously display;
  domain-locked kit, external CDN — the old self-hosted doctrine no
  longer holds; Sofia Sans woff2 stays as fallback, Literata is unused).
  Root-level `kit.css` is the tracked Typekit licence/reference copy,
  wired to nothing. /anadohoi was redesigned around the curated fields
  (status waffle pair, TIMELINE Gantt with restatement fold, executors
  table, ZoneMap dots); the front page follows the same design language.
  Restatement fold convention: superseded rows are folded INTO their
  successor client-side (`ganttProjects`) — charts count 68 live
  projects, the curation/test split (42/18/9 deliverables) counts all
  69 acts; both are correct on their own basis.
- **Stated analytics basis** (DATA_DECISIONS 2026-08-03, second entry):
  contract-value analytics use STATED values — `g.conn` passes through
  `queries_extra.apply_stated_basis` (net views + an EMPTY
  `contract_payments` TEMP view, so every frozen `effective_cost()`
  COALESCEs to the stated column); the payments layer (strip timeline,
  disbursement curves, paid KPIs, per-contract payment lists, contractor
  paid-per-year) reads through the lazy `_pay_conn()` which sees real
  payment rows. Everything value-based reconciles to €659,290,845.34
  (pinned; was €667,496,652.26 until the 2026-08-13 antinero_probable
  exclusion, then €658,297,730.65 until the 2026-08-14 Σουφλί
  stated-value correction); /compare is symmetric stated-vs-stated (≈20.8×); /explore has
  a single «Stated value (net)» column (`?v=8`). Gotcha: an endpoint that
  needs payments MUST take `_pay_conn()` — on `g.conn` the payments table
  is empty by design.

- **Two processes**: `. .venv/bin/activate; python -m atlas_api` (Flask JSON,
  127.0.0.1:5050) + `cd atlas && npm run dev` (Vite, :5173 — binds ::1, use
  `localhost` not 127.0.0.1). webui stays on :5000, all three can run at once.
- **Fetch plumbing**: browser `/api` + `/pdf` requests go through the Vite
  `server.proxy`; SSR fetches are rewritten by `src/hooks.server.ts`
  `handleFetch` to `ATLAS_API_ORIGIN` (default `http://127.0.0.1:5050`).
  Production: `npm run build && npm run serve` — `atlas/server.mjs` wraps the
  adapter-node handler AND proxies `/api`+`/pdf` to Flask itself (single
  origin, no external reverse proxy, no CORS anywhere).
- **Performance conventions** (violating any re-introduces 1s page navs):
  atlas_api memoises every GET /api response in-process (DB-mtime-validated,
  pre-gzipped; list titles trimmed to 140 chars); big client payloads
  (map/payments/swarm/…) are NOT loaded in `+page.ts` — SSR serialises load
  data into the HTML (was 900KB) — they're fetched post-hydration via
  `apiGetCached` (module-memoised across navs) into **`$state.raw`** holders
  (deep `$state` proxies on FeatureCollections made d3-geo read every
  coordinate through a getter: ~700ms/nav); below-fold charts mount via
  `ui/Defer.svelte` (IntersectionObserver); PaperMap caches fitSize/path-d/
  bounds per (feature, size) at module level, quantises zoom k for overlays
  (quarter steps) and view filtering (40px steps), wheel-zoom arms only
  after a click, and has +/−/reset buttons. Drill smoothness: PaperMap
  idle-prefetches hires+muni topo and pre-generates their path strings in
  requestIdleCallback chunks, and swaps hi-res in only after the zoom
  transition settles (first drill was a 470ms long task mid-animation;
  now 0). `.region:focus { outline: none }` — the UA focus ring drew a
  rectangle around clicked polygons. The `/` points view mirrors webui
  exactly: country level = contract-count choropleth left + HQ dots right;
  works-drill = per-contract dots (OKLCH hues for multi-authority
  contracts, dashed all-pairs seat-links on hover incl. off-region seats);
  home-drill = the co-ops' contracts' dots at country frame.
- **/connections flow design** (no default arc spaghetti): default map =
  LINEAR %-of-works-won-by-out-of-region-firms choropleth (title
  auto-computes "only N% stays local" — 13%); click a region → FlowArcs
  draws only ITS flows, direction-coded with arrowheads (red = firms
  elsewhere reaching in, blue = its firms reaching out, green dot =
  stays-local €); plus hub-catchment small multiples — top-6 home regions
  by exported € (Κεντρ. Τομέας €139M, Θεσσαλονίκη €119M, **Τρίκαλα €87M**,
  Β. Τομέας €82M, Καβάλα €67M, Ν. Τομέας €57M), one mini-map each on a
  shared scale, click→traces that hub. One-arrow-per-region "shift arrows"
  were REJECTED: only 19/56 import-majority regions have a ≥50% dominant
  origin. `region_flows` € are FULL-EXPOSURE (a multi-region contract
  counts per region pair, Σ≈€1.1B) — show shares, never sum as programme €.
- **Stack**: Svelte 5 (runes) + TS + adapter-node (config lives inside
  `vite.config.ts`, no svelte.config file); plain CSS custom properties
  (`src/lib/styles/tokens.css` — white-paper palette since the 2026-08-12
  rebrand + the geo_common.js ramps ported verbatim), NO
  Tailwind/Chart.js/Leaflet — d3-* + topojson only. Fonts via the Adobe
  Typekit kit (see the rebrand bullet); the self-hosted Sofia Sans woff2
  subsets in `atlas/static/fonts/` remain as fallback. Components capped
  ~300 lines.
- **Baked shaded relief** (2026-08-13, fires map only): `scripts/
  build_relief.py` (SYSTEM python3) bakes Copernicus GLO-30 (keyless
  /vsicurl COGs, raw DEM never committed, cache gitignored) into
  `atlas/static/geo/relief.avif` (1280×1240, always) + `relief_hi.avif`
  (2560×2480, k≥2 trigger, never narrow; keep every image ≤8 MP — iOS
  decode caps). Alignment contract: `frame.json` (emitted by
  build-topo.mjs from the SAME fitSize call PaperMap uses; d3 geoMercator
  ≡ EPSG:3857 up to an affine → the AVIF registers as one axis-aligned
  `<image>`; vitest `frame.test.ts` pins it — after ANY change to the
  coarse layer or frame size re-run `npm run geo` + the bake). Shade =
  vendored RVT (Apache-2.0, `scripts/vendor/rvt_vis.py` — pad the DEM 1px,
  RVT trims a border) multidirectional + SVF + fractional-Laplacian
  texture shading + TRUE CAST SHADOWS (horizon-scan, height-weighted —
  taller casters shade darker — with a 5-altitude penumbra; shadows
  spill across the sea) + geoblender-velvet tone (land capped at 0.88,
  gamma roll-off, flats == the BG_BASE 0.885 plate) + an analytic sun
  gradient over the whole plate + coastal contact shadows. Mount: the
  image renders with NORMAL blending UNDER the Π.Ε. polygons (fills go
  `transparent` when `relief` is set — stroke highlights/hit-testing
  unaffected) and `.map.plate` carries the SAME plate gradient
  (#f1f1f1→#e2e2e3 @110° — must track the bake knobs) so the surround
  beyond the image edge is seamless; scars stay the loudest layer. A
  GREYSCALE/ELEVATION toggle on the fires map swaps in the second baked
  styling (relief_hypso*.avif — hypsometric HYPSO_STOPS display tones
  sampled from the user's Bosnia reference, 0.6 shade-gamma lift; the
  page's legend-bar css gradient must track the stops). MANDATORY attribution in the hosting
  frame's caveat: «Relief: produced using Copernicus WorldDEM-30 © DLR
  e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided
  under COPERNICUS by the European Union and ESA; all rights reserved».
- **Design doctrine** (Tse/ProPublica): chart titles are findings, not
  topics; annotations printed on the chart; tooltips never carry
  load-bearing info; every chart has a caveat line anchored to
  `/methodology`; pair every change view with a level view; small multiples
  over filterable charts. SVG ≤1k marks, canvas above (2,018 ΔΑΣΕ dots).
- **API endpoints** under `/api/{meta,antinero/*,dase/*,anadohoi/*,explore,
  compare,connections,authorities,authority/<slug>}` — JSON gets
  `Cache-Control: max-age=300`, `app.json.ensure_ascii = False`. `/api/meta`
  degrades honestly (no `dase`/`anadohoi` key) when a DB is absent;
  `/api/antinero/*` never opens the other two (isolation tests mirror
  webui's). The anadohoi DB is a third **lazy** connection
  (`_anadohoi_conn`); `/pdf/diavgeia/<ΑΔΑ>` is a sibling caching proxy
  into `data/processed/anadohoi_cache/`.
- **/explore** (all three datasets, one table): `/api/explore` ships ~2.3k
  compact rows once (gzipped by the response cache); ALL filtering/sorting
  is client-side for instant response — dataset/Π.Ε./HQ/procedure/status/
  dates/value/q as URL params (shareable). Greeklish search is a TS port
  (`transforms/search.ts`) pinned by goldens generated from
  `webui/queries.py` (`search.golden.json`); known shared limitation:
  Greek ρ folds to visual P. Value bases differ per dataset and are
  labelled, never summed as one headline (methodology#explore).
- **/anadohoi** (sponsor dataset analysis): status waffle headline,
  PromiseGantt (appointment→deadline bars grouped by outcome, extension
  segments, ✓/✕ marks, today rule, annotated standouts), fire-event small
  multiples (curated `fire_event`), sponsor ranking (registry spellings
  merged presentationally via `_sponsor_group` — ΔΕΗ/ΔΕΗ Α.Ε., ΕΛΠΕ/
  HELLENiQ, mixed-script «ΕRΕΝ» homoglyphs), status-coloured Π.Ε. dot map,
  monthly appointment strip with fire markers, deadline-slip slope.
  `/anadohoi/project/[ada]` = decision trail with per-act Diavgeia PDFs +
  the verbatim-excerpt evidence block.
- **Detail-page template** (2026-08-17, user mockups; refined 2026-08-16
  session): the three detail pages (/anadohoi/project, /antinero/contract,
  /dase/contract) share one skeleton — `$lib/detail/FactsHeader` (CAPS
  label/value rows; the act-code VALUE mirrors its label exactly — the
  display face at fs-18/700, because the futura Book face has no true
  bold; qualifier `small` text inside a label renders like the value, not
  CAPS; caveat spans the full facts width; no MAP corner label),
  `DocTrail` (uniform date · type · code · title · pdf table, ENGLISH
  type labels; the viewed document bold; optional `top` snippet between
  heading and table), `QuoteList` (verbatim Greek excerpts + source act
  links; same sp-8 breather as the trail) and `ActTimelineBar` (anadohoi:
  the project's own PromiseGantt row — same programme axis + ganttTheme
  palette, printed start/deadline dates — in the trail's `top` slot; the
  project's EFFIS fires render as dots at their start date, one tone per
  fire earliest-darkest — the `d` date property was added to the display
  layer by build_effis_layer.py, rebuild BOTH copies). SiteMap: solid
  per-fire scar fills matching the bar dots, min-size markers for <7px
  scars, unlabelled pins (no white stroke), +/−/⌂ zoom with drag-pan,
  click-NEAR-a-fire zooms to it (svg-level nearest-bbox hit — the EFFIS
  multipolygons are too fragmented for path hit-testing), timeline-dot
  hover selects the scar and shows the black top-left card (date · ha);
  map height tracks the facts+caveat column (FactsHeader `leftHeight`
  $bindable, min 420) so the map's lower edge aligns with the lower end
  of the left text (user clarification 2026-08-16, third same-day
  entry). Fire-framed maps (DATA_DECISIONS 2026-08-16): when a project
  links EFFIS scar(s), the frame is the scar bbox + pads (0.18×span,
  floors 0.40° x / 0.27° y — 0.40 keeps the Λιχάδα cape in view;
  never-crop extension for outlying sites/zones) fitted BY WIDTH at
  constant scale and vertically centred — same-fire cards share one
  zoom and one horizontal window (the 9 Β. Εύβοια-2021 cards show the
  whole upper island; scar verified pixel-identical at x 172–286,
  ~114×176) while each card's column height only adds/removes vertical
  padding context; a scar taller than the viewport falls back to a
  both-dims fit at rest (never while user-zoomed). ZoneMap draws all
  Π.Ε. polygons — the frame reaches the mainland coast. River-scoped
  acts draw their named watercourses from
  `context_rivers.geojson` (OSM Overpass courses, ~50 m simplify,
  per-feature curated `projects` application — never name-matched;
  `scripts/build_river_layer.py`, copies pinned by
  `tests/test_river_layer.py`; «© OpenStreetMap contributors» in the
  caveat). Site pins are ONE colour; hovering a pin shows a black
  bottom-left card with the site's name («κατά προσέγγιση» flagged
  there); the caveat states the dot-placement method explicitly.
  Duration-worded deadlines suppressed on completed
  projects; LOCATION labelled «as named in the designation act» with
  the coverage caveat (DATA_DECISIONS 2026-08-16: the 9ΕΘΠ probe showed
  follow-up acts may cover only part of the act's named fronts, and
  Diavgeia search cannot see recitals).
  Contract pages add PROCUREMENT DETAILS OF <ΑΔΑΜ> (one-row wide table:
  authority/unit/signer/funding, EN names) and PAYMENT ORDERS; dase keeps
  the FamilyTree (Greek registry vocabulary — it matches on registry
  names) and the duplicate banners; anadohoi keeps SiteMap/ZoneMap in the
  map slot (height 460; sponsored-overview palette — #f2f2f2 sea, #fff
  land, borderless; single-site frames pad to a ~30 km half-window; site
  legend + «Θέσεις όπως…» line dropped — pins are labelled, sourcing
  lives in the caveat; EFFIS scar line kept; the LocationCurator dev box
  removed). KPI cards dropped. User decisions: AREA row = curated
  στρέμματα (+ha) on anadohoi only; contracts show WORK REGIONS instead
  (per-contract areas = future PDF-curation task); FIRE EVENT row only on
  anadohoi; status «active» renders plain (chips for the rest); the Π.Ε.
  is its own REGION row («R.U. <en>» · Δήμος); LOCATION text stays Greek
  — the 69-entry EN translation proposal awaits user review (2026-08-16).
  Contract maps: Π.Ε. highlight + authority/unit seat dots
  (`queries_extra.contract_authorities`, `dase_contract_geo` payload
  additions).
- **Tests**: `tests/test_atlas_api.py` (+ `_queries_extra`, `_real_db` as
  they land) with pytest; frontend `cd atlas && npm run check && npm test`
  (vitest transform units incl. `format.ts` goldens that must equal
  `webui/filters.py` output).

## Tests (`tests/`, 359 passing — `.venv/bin/python -m pytest`; plus `cd atlas && npm test` for the 40 frontend units)

Unit tests use synthetic fixtures (`conftest.py`); several "real-DB pins" assert
invariants on the committed SQLite: chain completeness / no double counting,
every in-scope contract has regions, every xlsx ΑΔΑ is stored, Diavgeia-only
count, curated ΕΣΑ sites present, and a **guard test**
(`test_real_db_no_uncorrected_outliers`) that fails when any non-cancelled
payment exceeds 150% of its contract family's stated value (recursive CTE over
prev links) — new registry keying errors surface here first, and
`payment_validator` screens the sub-threshold ones against the PDFs.

## Problems hit & their fixes (institutional memory)

1. **429 storms on attachments** → cache-and-serve proxy + wait page; never link
   registry URLs directly.
2. **`nextRefNo` truncation bug** → `chain_loader.repair_link_columns` recomputes
   from `raw_json`.
3. **Payments stuck on superseded originals** → `attributed_ref` + full
   re-attribution pass on every `payment_loader` run.
4. **Registry keying errors** (€992M on a €279k contract; ×100 missing decimal;
   only 1 of 2 invoices) → `payment_corrections.json`, verified against signed
   PDFs; the family-level outlier test catches new ones.
5. **Homoglyph & accent traps** in Greek titles → `normalize_title` +
   `_strip_accents`; fund code beats title numerals for II vs III.
6. **Supplementary contracts wrongly superseding** (a €706k ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ hid a
   €4.7M parent) → additive rule (successor <0.9× parent doesn't supersede).
7. **Wrong scope exclusions** — αντιδιαβρωτικά/ΕΣΑ contracts excluded on title
   keywords, but their PDFs declare Antinero membership → audited all 92
   excluded PDFs, reclassified 24 in scope. Always read the PDF.
8. **CASCADE wipe** of scope/region rows on contract refetch → re-run loaders.
9. **Chain-ambiguous Diavgeia decisions** → prefer «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ»,
   check for already-stored PAY before resolving, drop umbrella candidates.
10. **Amendment scope gaps** (fund-only or no evidence) → inherit predecessor's
    scope (`inherited_from_prev:<ref>`), regions inherited in the curation file.
11. **GEMI publicity API 500s on minimal payloads** — `/api/search` accepts
    `token: null` ONLY with the complete `dataToBeSent` filter object (every
    field present); and it 429s on back-to-back calls → sleep between search
    and details. The `/api/searchCompany` route is captcha-gated — different
    endpoint, don't confuse them. **One ΑΦΜ can return several GEMI records
    — branches «(Υποκατάστημα)» may be listed BEFORE the seat** (ΖΙΤΑΚΑΤ:
    branch on Συγγρού listed first, seat in Σαλαμίνα) → `pick_seat_hit`
    prefers non-branch hits / the …000 parent suffix, and
    `gemi_loader --verify` cross-checks stored numbers + regions against
    the seat (accent-folded Π.Ε. comparison).
12. **Registry-vs-PDF cent noise**: KHMDHS amounts differ from the signed PDF
    by €0.01–0.02 routinely (rounding) → validator classifies ≤€0.02 as
    `near_match`, never a correction candidate.
13. **Weak 2-digit postal fallback mis-region** (38xxx → Λάρισας when the
    address is Βόλος) → GEMI's prefecture field overrides `postal2`/`none`
    resolutions (`gemi_loader`), never the precise city/postal3 ones.
14. **Refresh TODO blind spot**: chain_loader can fetch brand-new chain
    members that were never refresh candidates → `curation_todos` scans ALL
    in-scope contracts, not just the diffed ones.
15. **Title vs items-text authority conflicts** — per-lot 2026 contracts
    repeat the whole multi-lot πρόσκληση in `contract_objects` (title names
    THE lot), while elsewhere the title is shorthand or plain wrong («ΔΔ
    ΛΕΣΒΟΥ» on a PDF-verified Δωδεκανήσου contract). No side wins
    universally → forest_loader takes the union, WARNs on disagreement, and
    the 6 reviewed cases are pinned in `contract_overrides` with evidence.
16. **Nominatim misses Greek-script queries** («ΚΟΡΝΑΡΟΥ 13, ΘΕΣΣΑΛΟΝΙΚΗ» →
    0 hits; "Kornarou 13, Thessaloniki" → hit) → geocode_loader adds a
    Greek→Latin transliteration tier; VIES's abbreviated prefixes («Λ
    ΣΤΑΜΑΤΑΣ» = Λεωφόρος) get expansion variants; every hit must validate
    against the stored postcode/Π.Ε. or it is discarded (a same-name street
    across town was correctly rejected this way). `q` cannot be combined
    with structured params (HTTP 400).
17. **Duplicate municipality names resolve the wrong seat** — «Ηρακλείου»
    exists twice in Kallikratis (9170 Αττικής, 9305 Κρήτης) and the folded
    name-match had pinned ΔΔ Ηρακλείου (Crete) to Athens' Νέο Ηράκλειο.
    Caught by the ΥΠΕΣ-code block-contiguity validation during the
    municipality→Π.Ε. curation (codes are ordered Περιφέρεια→Π.Ε.→δήμος, so
    a Crete Π.Ε. anchored inside the Attica block is impossible). It is the
    only duplicate name in the layer; resolve seats by code, never by name.
18. **Independently-simplified municipality polygons don't tile** — the
    FireWatch conversion was simplified per-feature, so dissolving to Π.Ε.
    left micro-holes/slivers (white speckles on choropleths) and km-scale
    blockiness when drilled into small urban Π.Ε. Fix: rebuild from the
    full-resolution shapefile with GEOS `coverage_simplify` (snapped to a
    10 cm grid first) — a polygonal-coverage simplifier that keeps shared
    edges identical on both sides; `drop_holes` still strips interior rings
    after dissolve (no Π.Ε. contains a cross-Π.Ε. enclave). Two detail
    levels ship because 30 m for all of Greece is ~7.6 MB — coarse eager,
    fine lazy on drill with client-side viewport filtering.
