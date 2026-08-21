# CLAUDE.md — Anti-nero contracts OSINT (evia-khmdhs)

OSINT dataset + web UI for the Greek **Anti-nero** wildfire-prevention/restoration
public-procurement programme (ΥΠΕΝ, RRF Action 16849). Flask + SQLite + Pico.css.
Everything derived is regenerable; `data/raw/` is never written to.

**Current state** (2026-08-18): 344 contracts (246 in scope; the Atlas
analytics basis is **stated net €622,534,181.72** — 245 contracts since
2026-08-19, when a record ΚΗΜΔΗΣ itself cancelled and re-posted was found
counted twice (25SYMV016659302 → 25SYMV017779215; `scope_loader` now takes
a registry-cancelled record out of scope) — (includes 19 curated
keying-error corrections — the Σουφλί cross-contract one and the
PROJECT-BUDGET-as-contract-value errors of 2026-08-18: 4 found by hand
(−€31.7M) and 8 more found by the document audit's screen (−€1.68M, 13
entries with their superseded predecessors)) — effective retired
2026-08-03, payments are their own layer: paid net €440.0M; webui keeps its
historical effective-gross presentation, now €604.5M on the same in_scope
flags), plus 7 chains / 13 contracts demoted to **`antinero_probable`**
(€9,198,921.61 net on tips): kept in the dataset, excluded from every
calculation — RRF-16849 membership unproven from primary documents
(user decision, DATA_DECISIONS 2026-08-13; curated
`khmdhs/data/probable_related.json`, presented on the Atlas front page as
«additional contracts found, probably related …»). 890 payment orders
(€565.8M paid gross, 5 Diavgeia-only with PDF-curated net amounts), all
amendment chains closed, 184/187 map contractors located, 153 linked to
GEMI profiles (151 contractors hold the in-scope contracts since the
2026-08-20 party corrections — 151 geocoded since the same day, when the two ventures without a point got their contract-stated seats; 126 with a ΓΕΜΗ profile),
18 curated work sites, 245/245 in-scope contracts linked
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
`chain_loader` → `contract_corrections` → `scope_loader` → `region_loader` → `forest_loader` → `studies_loader` → `categories_loader` → `families_loader` → `bodies_loader` → `payment_loader` → `linked_acts_loader` → `completion_acts_loader` → `extension_acts_loader`
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
  count; same-value ΑΠΕ restatements do supersede). Since 2026-08-18 the
  «ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ» test reads the successor's PDF **heading** (first 600
  chars) as well as its registry title — 26SYMV019512653 is titled
  «ΑΝΤΙΠΛΗΜΜΥΡΙΚΑ ΔΥΤΙΚΗΣ ΑΤΤΙΚΗΣ» and only its PDF says what it is; the
  heading only, because «συμπληρωματικές εργασίες» is ΕΣΥ boilerplate in
  every contract.
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
  bundles, keying errors) and `no_authority` documents the region-scoped
  contracts that genuinely name none (1 left; DATA_DECISIONS 2026-08-19).
  **Fourth source since 2026-08-19: the Diavgeia completion acts**, whose
  subject says «…για την περιοχή αρμοδιότητας των Δασαρχείων Πάρνηθας,
  Λαυρίου…» — 275 of 283 name a service, and for the region-scoped «άμεσης
  διαχείρισης» contracts it is the ONLY such statement (25 links / 13
  contracts since the 2026-08-21 re-attribution, `source=completion_act:<ΑΔΑ>`;
  read last so it can only ADD — which is why a mis-keyed act's services
  land on the wrong contract: the act layer must be right first).
  An act accepting «– για το τμήμα του έργου …» is marked
  `completion_act:<ΑΔΑ>|part` (1 of 29) and the contract page says so —
  one accepted part is not the contract's whole jurisdiction, which is why
  26SYMV018978343 showed a single Εύβοια service beside an Attica map
  (DATA_DECISIONS 2026-08-19). Needle gotcha: `fold()` maps Greek onto
  Latin, so the test string must be folded too.
  Authorities also carry **`covers_pe`** — the Π.Ε. a service administers
  beyond the one its office sits in (8 user-confirmed: ΔΔ Σάμου→Ικαρίας,
  ΔΔ Κεφαλληνίας→Ιθάκης, Πεντέλης→3 Attica sectors, …); `region_pe` still
  means the SEAT and places the map dot. Warns on new title/items
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
- `scripts/audit_contract_documents.py` — audits every in-scope contract
  against its own signed text, reading the **CHAIN** (tip → all ancestors),
  never the tip alone: 46 of 245 in-scope contracts are amendments whose own
  PDF is a 10 kB cover note, and chain-reading lifts every anchor (ΣΑΤΑ
  ενάριθμο 177→222, «αρμοδιότητας Δασαρχείου» 140→155, ΕΣΗΔΗΣ 41→56).
  Writes three CANDIDATE review files to `data/processed/`
  (`audit_fields` stored-vs-document, `audit_extras` fields we don't store —
  Α/Α ΕΣΗΔΗΣ, subcontractors, δικαίωμα προαίρεσης — and `audit_identity`
  per-ΑΦΜ). Nothing is written to the DB. Two gotchas encoded in it: the
  meaningful authority test is the REVERSE one (stored ⊄ declared; documents
  legitimately name more Δασαρχεία than a lot covers, because recitals quote
  the whole multi-lot procurement), and a Greek regex must be folded into the
  text's alphabet WITHOUT uppercasing, or `\s \d \w` invert (DATA_DECISIONS
  2026-08-18).
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
- `document_kinds.py` — **what each ΣΥΜΒ record actually IS**, read from the
  document's own heading/«ΘΕΜΑ:» line (DATA_DECISIONS 2026-08-18): ΥΠΕΝ posts
  contracts, amendments, supplementary contracts AND ministry approvals under
  a ΣΥΜΒ ΑΔΑΜ, and the registry's `contract_type` is the ν.4412 object
  category («Έργα»/«Υπηρεσίες») on all of them. In scope: 200 contract / 25
  amendment / 11 approval_ape_supplementary / 6 approval_schedule_extension /
  4 supplementary_contract. **All 246 ARE συμβάσεις** — the label says which
  KIND, so the plain contract is «Αρχική σύμβαση» (user decision 2026-08-18,
  after «approvals», «πράξεις» and «extra work» were each rejected); ν.4412
  vocabulary in Greek, Directive 2014/24 in English, the bilingual pair in
  `KINDS`. The 4 + 11 are one phenomenon in two document forms and sum to
  «15 supplementary works»; only those 15 move money — the 25 revisions never
  change the price (verified on all 25) and the 6 extensions carry the
  parent's value to the cent. Ordered rules (most specific act first),
  registry-title fallback for PDFs that open with a letterhead, `unknown` +
  `data/document_kind_overrides.json` for anything unreadable (0 in scope).
  Writes `contracts.document_kind` / `_evidence` / `_source`; in the refresh
  chain after families_loader. Gotchas: «ΥΜΒΑΣΗ» without its Σ is real
  (pdftotext drops the drop-cap) and the window is ~2.500 chars — shorter
  misses the ΘΕΜΑ line behind a letterhead, longer hits the ΕΣΥ boilerplate
  «συμπληρωματικές εργασίες» in every contract. Atlas: contract-page DOCUMENT
  row (English over Greek), the DOCUMENT TRAIL type column, and the computed
  `/methodology#record-kinds` paragraph fed by `/api/meta` `kh_doc_<kind>`.
- `families_loader.py` — **procurement families read from the contracts'
  own signed texts** (DATA_DECISIONS 2026-08-18), because the registry
  chain declares any upstream act for only 76/245 in-scope contracts and a
  πρόσκληση for 40. Scans each cached `.txt` for cited ΑΔΑΜ
  (`##PROC#########` / `##AWRD#########` / sibling `##SYMV#########`),
  classifies the role from the surrounding sentence and stores
  `contract_families` (adam, kind, role, seq, verbatim excerpt; FK
  CASCADE). Amendments inherit the predecessor's call — the accent trap
  bit here: `τροποποι` never matches «Τροποποίησης», so `_unaccent()`
  before testing (the uncorrected pass claimed 137 calls, the real number
  is 134). Coverage: **219/245 in-scope contracts → 134 calls**; the
  other 26 cite none (direct awards / negotiations publish no call) and
  nothing is inferred for them. This layer is what exposed the €31,7M
  project-budget keying error — three lots of one πρόσκληση all stating
  the same figure. Atlas: `queries_extra.contract_family` (contract page
  «CONTRACTS UNDER THE SAME CALL» radial) + `antinero_network`
  (front-page programme chart).
- `completion_acts_loader.py` — project-ENDING acts from Diavgeia:
  ΚΗΜΔΗΣ has no completion record type, but ΥΠΕΝ posts «Έγκριση
  Πρωτοκόλλου Οριστικής Παραλαβής … της Σύμβασης με ΑΔΑΜ: <SYMV>» acts
  whose SUBJECT cites the contract ΑΔΑΜ → one luminapi
  `subject:"<ΑΔΑΜ>"` search per stored contract, STRICT completion
  classification (οριστική παραλαβή / περαίωση / διαπιστωτική
  ολοκλήρωσης; committee formations, παρατάσεις, ΑΠΕ, επιμετρήσεις,
  τμηματικές/προσωρινές παραλαβές rejected). Subjects saying only
  «Πρωτοκόλλου Παραλαβής» resolve from the PDF body (early acts omit
  «οριστικής»); a «Μερική έγκριση» (partial approval) is rejected
  (DATA_DECISIONS 2026-08-21). End date = the ACCEPTANCE protocol's date —
  «το από DD.MM.YYYY πρωτόκολλο [οριστικής …] παραλαβής / περαίωσης», the
  LAST such in the act; never the «πρωτόκολλο εγκατάστασης αναδόχου» the
  recitals list first (105 of 283 acts carried the installation date
  until 2026-08-21) — (excerpt stored, `end_basis=protocol_date`), else a
  «περαιώθηκαν … DD.MM.YYYY» sentence, else the act date (255 / 26 since
  pass 5 of 2026-08-21 read the plural «τα από … πρωτόκολλα», a date
  list — the LATEST —, a two-day protocol, «υπ’ αριθ. N/DATE πρωτόκολλο»,
  «(με ημερομηνία …» and the month-name περαίωση forms; the date list must
  stand IMMEDIATELY before «πρωτόκολλ…»). **ΥΠΕΝ keys the
  wrong ΑΔΑΜ in some subject lines** (lot 15Α's acts carried 15Γ's, lot
  4Α's carried 4Δ's): curated `data/completion_act_overrides.json` (ΑΔΑ →
  the contract the act concerns, evidence quoted) is applied at insert and
  the loader WARNs when subject and recital name stored contracts of
  different chains without an override — a recital can be the typo too
  (Ψ8ΝΛ4653Π8-4Β6), so every verdict is read from the act. `--reextract`
  recomputes kind / attribution / end date for every stored act offline.
  Table `contract_completion_acts` (chain-tip `attributed_ref`
  like payments; FK CASCADE; in the refresh chain). Atlas timeline shows
  them as the closing act with `/pdf/diavgeia/<ΑΔΑ>` links.
- `extension_acts_loader.py` — **deadline-EXTENSION approvals from Diavgeia**
  (lifecycle layer, phase 1, DATA_DECISIONS 2026-08-21): one luminapi
  `subject:"<ΑΔΑΜ>"` search per stored contract (or `--from-cache`), the
  «Έγκριση (τμηματικής) παράτασης …» acts classified from the subject
  (revocations and schedules approved «λόγω παράτασης» rejected), their PDFs
  read for the NEW DEADLINE: the operative part starts at the LAST
  «Αποφασίζουμε» (recitals list the previous extensions — anchor earlier and
  you read the old deadline), every «μέχρι/έως (την|τις) DD.MM.YYYY» (also
  «μέχρι τις και …», «με ημερομηνία περαίωσης την …», «έως την 28η Αυγούστου
  2026») is kept in `dates`, the latest is `new_deadline`, several distinct
  = `per_area`, «κατά N ημέρες» in `by_text`, verbatim `excerpt`, and an
  unreadable act carries `flag` (no_operative / no_date / unreadable_font —
  the substitution-cipher fonts) with NO deadline. Table
  `contract_extension_acts` (FK CASCADE, chain-tip `attributed_ref`, same
  overrides + lot-letter WARN as the completion layer; `--reextract`
  offline). **463 acts / 167 contracts (159 in scope), all read: 459
  grant a deadline (23 per-area), 3 state one EARLIER than their own date
  (the act's year typo — kept as written, `flag=deadline_before_issue`,
  never a timeline step) and 1 is `extension_refused` (an «Απόρριψη
  αιτήματος … παράτασης»: no deadline, the refusing sentence as excerpt).**
  `scope`/`scope_text` say WHAT the act extends, read from the grant clause
  after the quoted title (`extract_scope`: study/stage/area/whole, the
  service phrase — also «για το Δασαρχείο Χ» — cut before «μέχρι/για N
  ημέρες/σύμφωνα»): a τμηματική παράταση extends ONE τμηματική προθεσμία
  (area 195 · study 24 · stage 4 · whole 1 · unsaid 134 of 358), a plain one the συνολική προθεσμία (whole
  16 · area 28 · stage 1 · unsaid 59 of 104) — DATA_DECISIONS 2026-08-21
  second entry. **`scope_auth`** = the registry services an area act names,
  resolved with forest_loader's Matcher (231/232; the pdftotext «ΑΔΑ: …»
  watermark is stripped from the phrase first), and the completion layer's
  **`part_auth`** = the ONE service a part-acceptance accepts (23 acts),
  **`area_dates`** = the hand-read {service: date} of a per-area act (22,
  `extension_act_curation.json`; `--reextract` also re-points the subject
  keying errors through `completion_act_overrides.json`) —
  together they feed the contract page's PER-AREA LANES
  (`transforms/lanes.buildLanes` + `detail/AreaLanes.svelte` inside the
  ChainTimeline svg, DATA_DECISIONS 2026-08-21 third entry: the bar's grey
  extended part is SPLIT into one strip per linked service where the acts
  name areas — 72 in-scope contracts — each strip cut into SEGMENTS (one
  piece per extension in ALTERNATING tones of the grey; no lines, ticks,
  arrows or dots; the axis stops 96 units short of the right edge so a
  name fits at its bar's end), the solid bar as tall as all
  strips, a service with nothing to draw gets no strip, names at the right end of
  their OWN strip ON HOVER (above the bar's end when there is no room; no
  outline) in the short form
  `names.authEnShort` «Kalampaka F.S.O.», a ✔ ONLY for that part's own
  acceptance, an act that names NO area on every strip (user rule
  2026-08-21: «no subset named = all the areas the title names»; only an
  area act naming a service the registry lacks gets a «service not
  matched» strip), € marks on the
  label line; studies/stage/whole stay on the bar; the contract map's
  authority names are a hover card at the TOP-LEFT corner (`PaperMap
  showTip corner` / `DotLayer tipCorner`; δήμοι cards bottom-left), and
  the DIAGRAM's shapes are centred on the map slot).
  `contract_completion_acts` stays the ending layer untouched.
  Atlas: `contract_timeline` rows of kind `extension` → DOCUMENT TRAIL
  «(Nth) deadline extension» with «→ DD.MM.YYYY · for <service>» in the
  title cell (a refusal: «the request was refused»; a flagged date: «as
  written in the act, earlier than the act itself»); the
  **ChainTimeline draws its extension steps from these acts as well** (same
  day, user): `contract_deadlines` merges them with the ΚΗΜΔΗΣ «Παράταση
  προθεσμίας» records — a step per act (`source` diavgeia|khmdhs, `later` =
  moved the deadline in force forward, `per_area`, `ordinal`, `excerpt`; an
  act re-stating a record's new deadline merges into that step), the
  deadline in force is the running maximum; a FLAGGED act is no step; 439
  steps over 162 in-scope chains (423 Diavgeia + 12 ΚΗΜΔΗΣ), pinned,
  `/api/meta` prints them (435 / 162 / 12 ΚΗΜΔΗΣ since the duration unit
  is accent-folded — «Ημέρες».upper() kept its accent and 14 days read as
  14 months, DATA_DECISIONS 2026-08-21 passes 3–5). ChainTimeline conventions (user, 2026-08-21): extension labels print the ORDINAL only («1st», «2nd»), a label closer than 14 units to the previous printed one is dropped (arc + hover title stay); the symbols carry NO outline — no halo on ✔ or €, no stroke on a dot, no outline on the hovered bar. The inventory that sized the
  layer (4,931 subject-citing acts; NO cancellation act exists) lives in
  the decision entry. Windows gotcha fixed in `diavgeia_loader.fetch_decision`:
  pdftotext reads its command line in the ANSI code page and writes ANSI
  without `-enc UTF-8` — Greek ΑΔΑ paths and Greek text both broke; the
  helper now converts through ASCII temp names in UTF-8.
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
- Municipality layer (proposals only, curation open — DATA_DECISIONS
  2026-08-19): `scripts/extract_contract_municipalities.py` reads each
  contract's CHAIN and its πρόσκληση the way the user reads them — title →
  award ΘΕΜΑ → call (lot table, «οι προς παρέμβαση εκτάσεις», «οι εργασίες
  αφορούν») → contract body — and emits a per-contract **reading trail**
  (document, anchor, verbatim quote) plus one row per (service → δήμος) pair
  tiered by independent confirmation. 153/246 contracts name a δήμος (220
  distinct, 290 pairs); the other 93 stop at the authority and say so. The
  section number is never assumed (τόπος εκτέλεσης sits at §2.4/§2.6/§2.7),
  and two document dialects are read («χωροθετούνται» and «διοικητικά
  ανήκουν»). Output: `data/processed/municipality_review.json` (gitignored)
  + committed `municipality_curator.html`; `--curate` promotes the readings
  to curated `data/contract_municipalities.json` (`_overrides` merged on
  re-run) → `khmdhs/municipalities_loader.py` → `contract_municipalities`
  (FK CASCADE; in the refresh chain after details_loader). **595 rows / 153
  contracts / 220 δήμοι**; the other 93 name none and the page says so.
  Rules (user-approved): the πρόσκληση counts as evidence and the row names
  the document (79 rows); a δήμος outside the contract's curated Π.Ε. is
  recorded and FLAGGED with the region layer untouched — but only where
  NOTHING accounts for it: of 49 such rows, 30 sit in a Π.Ε. the naming
  service administers (`covers_pe`), 11 in its own seat Π.Ε. and 6 carry a
  user verdict, so **2 stay flagged** (`outside_pe_explained`); pre-Καλλικράτης
  names and settlements resolve to today's δήμος (ΘΕΣΠΙΕΩΝ→Θηβαίων,
  ΠΑΠΑΓΟΥ→Παπάγου-Χολαργού, ΣΑΡΩΝΙΔΑΣ→Σαρωνικού) — all 220 names resolve;
  δημοτικές ενότητες stay unrecorded. Contract page: **AREAS OF INTERVENTION**
  (δήμοι + R.U. + which document said it) above **RESPONSIBLE FOREST SERVICE
  BODY**, one quoted sentence per group in the evidence block, and the named
  δήμοι OUTLINED on the map from `greek_muni.geojson`; **/explore filters by
  δήμος** (`mu` on the 153 rows that have one, facet by contract count, in
  the search index, `?mu=` permalink) —
  `scripts/build_muni_polygons.py` rebuilds the 325 municipality polygons by
  polygonising each Π.Ε. outline together with its interior borders (no
  geopandas, no `coverage_simplify`: the committed layers share vertices, so
  the result has no slivers), ~250 m / 4 decimals, 611 KB, lazy-loaded.
- Work-theme + duration layers (DATA_DECISIONS 2026-08-19, **curated and
  loaded**): `scripts/extract_contract_details.py` reads every in-scope
  contract's cached text once and emits `data/processed/
  contract_details_review.json` (gitignored) + the committed
  `contract_details_curator.html`. (a) `khmdhs/work_themes.py` — TWELVE
  multi-label themes from the contract's own descriptive project title
  (155 contracts name ≥1, **101 name ≥2** — one category per contract is
  lossy; 91 say nothing beyond «αντιπυρική προστασία» and stay so), each
  hit carrying the verbatim clause; CPV is a SCREEN not a source (9 marker
  codes → 56 questions; «συντήρησης οδών» 130/246 and «χαρτογράφησης»
  119/246 are deliberately NOT markers). The «Αντικείμενο της Σύμβασης»
  article and the πρόσκληση were tested and rejected — boilerplate and
  whole-programme menu respectively. (b) `khmdhs/contract_durations.py` —
  the «συνολική προθεσμία … ορίζεται σε …» clause, chain-read: **246/246**
  state a deadline (registry: 83) and 243 state the START BASIS (187 έναρξη
  εργασιών / 51 υπογραφή), which the registry never carries. **The ΚΗΜΔΗΣ
  duration field agrees with the document in 3 of 66 comparable cases.**
  Traps encoded + pinned: the PENALTY article defines nothing (65 false
  reads), the μελέτη's deadline is not the works' (design-build), «ΦΠΑ 24%»
  sits before «Άρθρο 3 Διάρκεια» (16), phase-II PDFs put each accent in as
  a separate letter → `loose()` allows a stray vowel only AFTER A VOWEL
  (66), the two-letter «ΕΤ» stem needs a word boundary or «ΜΕ ΤΗ ΛΗΞΗ» reads
  as «2 years» (3), and «Μήνες».upper() is «ΜΉΝΕΣ» so the comparison folds
  accents. **Three contracts answer with a SEASON** — «η αντιπυρική περίοδος
  του έτους 2024» — and Greece's runs 1 May – 31 October (user), so their
  deadline is 31.10 of that year.
  Verdicts (rules, user-approved 2026-08-19: show every theme · say so when
  the title states none · CPV is only ever a note · document over registry)
  live in curated `data/contract_work_themes.json` + `data/contract_durations.json`
  (both with `_overrides`, merged by `--curate`) → `khmdhs/details_loader.py`
  → `contract_work_themes` (330 links / 155 contracts) + `work_theme_labels`
  + `contract_cpv_notes` (56) + `contract_durations` (246); in the refresh
  chain after categories_loader. **`queries_extra.contract_deadlines` now
  reads the curated duration FIRST** — every in-scope contract has a drawn
  bar (243 document + 3 season, was 155 stubs) and extensions rose to 14
  chains / 16 steps (9 παρατάσεις + 7 supplementary approvals carrying a
  later end date, labelled apart).
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
| `dase_contract_corrections.json` | ΔΑΣΕ contract corrections: 1 stated-value keying error (21SYMV009374147 ×10 digit-glitch, `objects` seq override) + 10 registry double-postings excluded via `exclude:true` + `duplicate_of:<kept ΑΔΑΜ>` (pages stay reachable, cross-linked; the 10th, 24SYMV015423487, is a corrected re-issue under a VIES-invalid phantom ΑΦΜ — caught cross-VAT, DATA_DECISIONS 2026-08-15) + 6 Δωδεκανήσου net==gross VAT corrections + **10 not-a-co-op contracts** excluded via `exclude:true` + `related_to:<in-scope sibling ΑΔΑΜ or "">` (DATA_DECISIONS 2026-08-17: the registry pasted the parent AWARD's whole awardee list onto a contract only one company signed) + 3 `contractors_keep` entries (deletes contractor rows the signed PDF doesn't name, and rewrites a GLUED ΑΦΜ field «X ΚΑΙ Y» to the kept one — the canonical-VAT rule silently keeps the first, i.e. the wrong co-op) + 6 `contractors_vat` rewrites (DATA_DECISIONS 2026-08-18: the contractor ΑΦΜ field held the AWARDING side's 090273987 — the Ελληνικό Δημόσιο — or a ten-digit typo, filing the contract under a fictitious co-op; the applier replaces it with the ΑΦΜ the signed contract states, targets validated as 9 digits, unmatched keys logged). **`cancelled = 1` is the shared exclusion MECHANISM, never the reason**: `duplicate_of` / `related_to` say which, and the Atlas labels each honestly (banner + facts chip + the document-trail row on BOTH siblings' pages — `$lib/transforms/exclusion.ts:trailChip`, one rule, unit-pinned); only a registry cancellation may read «cancelled». Applied by `khmdhs.contract_corrections` (standalone + end of `harvest_dase.py load`) together with `dase_payment_corrections.json` (217 entries). Candidates: `scripts/validate_contract_values.py` + `scripts/find_duplicate_postings.py` (same-VAT pass + cross-VAT pass for mis-keyed ΑΦΜ twins) + `scripts/audit_contract_awardees.py` (screens every contract's registry contractor list against the ΑΦΜ its signed PDF names) |
| `contract_corrections.json` | Same format/mechanism for the khmdhs (Anti-nero) DB; currently 30 — including **9 party corrections of 2026-08-20**: 7 contracts whose registry rows named a κοινοπραξία's MEMBERS instead of the κοινοπραξία that signed (new `contractor_party` key: the ΑΦΜ, the registered name and the verbatim preamble sentence; ΓΕΜΗ/VIES confirm all 7) and 2 whose list carried companies the signed text never names (`contractors_keep`). Also one **party-only** entry (25SYMV017073536: the registry keyed ΓΕΩΓΝΩΜΩΝ Ο.Ε.'s ΑΦΜ with eight digits, «98434068»; the signed contract states 998434068, and zero-padding to 098434068 would file it under an ΑΦΜ belonging to nobody). A party-only entry deliberately does NOT stamp `correction_note` — the contract page renders that as a stated-value correction. **One entry carries a LIST of parties** (22SYMV010795606, DATA_DECISIONS 2026-08-20 second entry): the κοινοπραξία that signed states no ΑΦΜ of its own, so the registry keyed the contract under member α (998255970) and credited that firm all €836.613,02; both signing firms are now recorded and the even split gives each €418.306,51. That contract already carried a PROJECT-BUDGET value correction — an entry can hold both, and since `reason` is stamped into `correction_note` and RENDERED as the stated-value correction, the party trail lives in a separate audit-only `party_reason` key. Contractor ΑΦΜ are stripped on ingest in `extract.py`: 13 registry rows carried padded values and split 7 companies across two keys each (DATA_DECISIONS 2026-08-18). (a) 26SYMV018642772 «ΔΧ ΣΟΥΦΛΙΟΥ» carried the Θεσσαλονίκη δεξαμενές contract's figures — PDF-documented true value €4,334,353.41 net / €5,374,598.23 gross (DATA_DECISIONS 2026-08-14). (b) **4 PROJECT-BUDGET errors** (DATA_DECISIONS 2026-08-18): the registry keyed «η συνεισφορά του Ταμείου Ανάκαμψης στον συνολικό προϋπολογισμό του ΕΡΓΟΥ» — the whole multi-lot project's budget, quoted in every contract's funding recital — as the contract's own price, while Άρθρο 5 «Αμοιβή Αναδόχου» states the real one: 24SYMV015544651 €31.02M→€4.00M, and the three lots of πρόσκληση 24PROC014835083 which all carried the same €2,284,973.72 (→€1.20M / €0.80M / €0.16M). −€31.7M off the basis, 4.8%. Found by the πρόσκληση-family analysis; screen with the RRF-recital test (stored value == the project budget the contract itself quotes). Applied by `khmdhs.contract_corrections --corrections` + a `khmdhs.refresh` step right after chain_loader (refetch/upsert restores registry values) |
| `municipality_overrides.json` | 17 curated verdicts on WHICH forest service a δήμος belongs to, where the signed contract assigns it to one that does not serve that area (DATA_DECISIONS 2026-08-19). The δήμος is never dropped; only the attribution is curated — `reattributed` when the competent service is a party to the same contract, `as_stated` (with it named in the note) when it is not. Keys `<ΑΔΑΜ>|<ΥΠΕΣ code>`; validated by `tests/test_contract_municipalities.py` |
| `consortium_members.json` | **Who is behind each joint venture** (DATA_DECISIONS 2026-08-20, extended the same day): all 57 in-scope κοινοπραξίες, each with its members' ΑΦΜ, the document they were read from and the verbatim sentence. **46 have curated members (93 links, 63 firms); 11 are `members_documented: false`** — their titles name firms but no reachable record states membership, and a name is not evidence. Since 2026-08-20 the register itself is an accepted source: the ΓΕΜΗ publicity details payload's **`managementPersons`** lists members with ΑΦΜ, role and percentage (source `gemi:<number>`, verbatim row as excerpt; batch confirmed by the user). **The percentages are the venture's internal participation shares, never how contract money was distributed — the even split stays; the percentage rides as `gemi_percentage` metadata only** (user convention, same day). The population is NOT a register question: ΓΕΜΗ legal form ∪ registry name missed three (996514860 is in no ΓΕΜΗ and its name carries no marker), and the award acts missed two more whose own contract enumerates the members. **`scripts/screen_joint_ventures.py` is the authority**: it reads each in-scope contract CHAIN, anchors on the contractor's own ΑΦΜ and looks back one party-clause window for «κοινοπραξ/ένωση εταιρειών/…» (the word alone is ΕΣΥ boilerplate), and `--members` re-reads the clause for «αποτελούμενη από …». Offsets survive the fold (1:1 char table) so excerpts are cut from the original, and the needles match loosely because phase-II PDFs write «αποτελουύμενης». Pinned by `tests/test_consortiums.py`, which fails on any venture the documents name and the curation lacks. Traps encoded: the person signing for a member company is not a member, and another venture of the same firms is not either. Proposals from `scripts/extract_consortium_members.py` (+ `consortium_curator.html`); every verdict the user's, 19 reviewed one at a time. Loaded by `khmdhs.consortium_loader` into `consortiums` + `consortium_members` (validation REFUSES a member that is itself a venture, a self-listing, a non-in-scope venture or a flag/list mismatch); in the refresh chain after municipalities_loader |
| `contract_regions.json` | ~331 contracts → project Π.Ε.(s), curated from titles/Δασαρχεία; amendments inherit from the superseded version. Optional per-contract `"sites"` lists (name, pe, PDF page, excerpt) → `contract_sites` |
| `contractor_locations.json` | 187 contractor home locations (VIES + GEMI + hand curation) + `gemi` profile numbers (`"-1"` = confirmed not in GEMI) + Nominatim `lat/lon/geo_precision` + **`gemi_status`** — what the register says TODAY, verbatim (147 swept by `scripts/harvest_gemi_status.py`: 122 Ενεργή / 21 Διαγραφή / 4 Λύση-Εκκαθάριση; 20 in-scope contractors are wound-up joint ventures, flagged with an ⓘ + ΓΕΜΗ link and never rewritten — they signed the contract). NO status date is stored: the API's `dateGemiRegistered` is the registration date (DATA_DECISIONS 2026-08-20). **The seat is read from the contract** (DATA_DECISIONS 2026-08-21, the second entry of that day): `contractor_seats.json` is the primary source — address/postal_code/city/region_pe are the CHOSEN seat, `seat_source` contract|register|website, `seat_ref` (ΑΔΑΜ or URL), `seat_excerpt` (verbatim clause), `seat_note`, `geo_level` number|street for an `address` point, `register_*` the old VIES/ΓΕΜΗ values. In-scope dots 117 address (35 number / 82 street) / 34 settlement centre (the last 8 via Overpass — OSM ways Nominatim's search did not return, reverse-geocoded into the named settlement; 17 documents name only a settlement, 12 km markers/localities, 5 streets no map knows). `geo_precision: address` means «on the named street», at the number where OSM has it; `municipality` = centre of the settlement the document names (km markers, localities, streets OSM lacks). Geocode gate = `_acceptable` + street-level + a centre must be a settlement-type hit naming the settlement in its own place fields + a Τ.Κ.-prefix match in another settlement is refused |
| `contractor_seats.json` | **The registered office of every in-scope Anti-nero contractor, read from the party clause of its OWN signed contract** (DATA_DECISIONS 2026-08-21): 151 entries, each city / street / number / Τ.Κ. transcribed by hand from the chain-read cached text (every row read; the parser only proposed), the source ΑΔΑΜ, the verbatim sentence, the register's values; `seat_source` contract 146 / register 3 / website 2 — where ΓΕΜΗ/VIES or the firm's own site shows a later move the CURRENT seat is chosen and `contract_seat` keeps the contract's (ΥΛΗ, ΚΗΠΟΠΡΑΞΙΣ, ΦΙΛΑΝΤΑΡΑΚΗ, ΑΛΣΟΣ, Τ&Τ; ΤΟΜΗ's own 2025 contract states its current Παιανία seat); 3 `flag: register_disagrees` (ΕΛΛΗΝΙΚΑ ΕΡΓΑ Ο.Ε., ΠΑΠΠΑΣ ΣΤΕΡΓΙΟΣ, Κ/Ξ ΜΠΟΜΠΟΤΗ–ΞΑΝΘΟΠΟΥΛΟΣ which states no seat); a venture's seat is never inferred from a member's (two regions changed: ΚΑΡΝΟΜΟΥΡΑΚΗΣ–ΑΛΚΗ ΥΠΟΕΡΓΟ Β → Καβάλα, ΛΙΑΡΗ–ΓΚΙΚΑΣ → Λίμνη Ευβοίας). Merged into `contractor_locations.json` (scratch `merge_seats.py`), loaded by `contractor_loader` into five `seat_*`/`geo_level` columns; the Atlas contractor page prints «registered office as stated in contract <ΑΔΑΜ>» + the quoted sentence. Pinned by `tests/test_contractor_seats.py` |
| `extension_act_curation.json` | Hand-read corrections to the machine reading of the extension acts (DATA_DECISIONS 2026-08-21, curation pass 1): `area_dates` = which service got which date when ONE act grants different dates per area (22 acts; the acts write the pairing in three orders, so no rule — the loader refuses a date the act does not state or a service the registry lacks), `scope_auth` judgments where the act names a DIRECTORATE standing for the contract's Δασαρχεία (Φθιώτιδας → Αταλάντης+Σπερχειάδας, Έβρου → Αλεξανδρούπολης+Σουφλίου), one `new_deadline` override (ΨΠΩΟ: the later date is a condition on approvals); verbatim grant sentence per entry. Applied by `extension_acts_loader` at load and on `--reextract`; the strips take each service's own date (`lanes.buildLanes`) |
| `completion_act_overrides.json` | Completion AND extension acts whose SUBJECT line keys the wrong contract ΑΔΑΜ (9ΞΣΟ4653Π8-Ζ9Ο → 26SYMV018739467, ΨΕΡΟ4653Π8-2Θ6 → 22SYMV010473680 since curation pass 1). Completion acts whose SUBJECT line keys the wrong contract ΑΔΑΜ (ΥΠΕΝ keying errors, DATA_DECISIONS 2026-08-21): 4 ΑΔΑ → the contract the act really concerns (lots 15Α and 4Α, whose acts carried lots 15Γ's and 4Δ's ΑΔΑΜ), evidence quoted from the act's recitals/lot/title. Applied by `completion_acts_loader` at insert and on `--reextract`; candidates come from the loader's WARN, but the recital can be the typo too — every verdict is read from the act |
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
| `contractor_display_names.json` | **ONE canonical display name per Anti-nero contractor ΑΦΜ** (DATA_DECISIONS 2026-08-20), 195 entities — 66 persons / 63 companies / 61 joint ventures / 5 other. Read from the DOCUMENTS, never invented: a person is «ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ» only where a signed act holds the patronymic or a document's initial and the register together prove it (65 of 66; the one it cannot prove prints without it), a company under the **δ.τ. its own contracts declare** («ΕΛ.ΤΕ. Ε.Π.Ε.», «P. & C. DEVELOPMENT S.A.», «ΒΙΟΣ Α.Ε.» for the firm the registry still calls Δ. ΚΑΦΕΤΖΗΣ ΚΑΙ ΣΙΑ Ο.Ε.), a venture as «Κ/Ξ » plus its members' own display names. ONE typography: capitals, dotted legal form, «&» between partners only, Greek forms folded back out of Latin, PDF homoglyphs («ΠΑΠΑ∆ΟΠΟΥΛΟΣ») repaired. Every name is unique — two ventures of the same firms are told apart by their lot («ΥΠΟΕΡΓΟ Β») or their year. Proposals from `scripts/extract_contractor_names.py` (+ `scripts/extract_name_evidence.py`, which sweeps every cached document for how each ΑΦΜ is written there); `_overrides` carries the user's verdicts (ΟΡΚΑ Α.Τ.Ε.Ε., ΕΡΓΑ ΠΡΑΣΙΝΟΥ Α.Τ.Ε., ΤΑΙΠΕΔ/HRADF). Loaded by `khmdhs.contractor_names_loader` into `contractor_display_names` (in the refresh chain after consortium_loader). **Presentation only**: `contractors.name` is never rewritten, every registry spelling stays searchable (`/api/antinero/contractors?q=` matches display name ∪ all spellings ∪ ΑΦΜ) and is printed on the contractor page as «In the registry as …». Overlaid on the ranking, the contractors list, the contractor page, the member-firm view, the contract page (`registry_name` beside each party) and the /explore `co` column — where the replaced spellings ride in `ac`, searchable, while `alt` stays ΑΔΑΜ-only |
| `dase_display_names.json` | 249 ΔΑΣΕ co-ops → curated bilingual display names (el `ΔΑ.Σ.Ε. 'ΟΝΟΜΑ', ΤΟΠΟΘΕΣΙΑ` / en `F.W.CO-OP …`), keyed by canonical ΑΦΜ, every value user-reviewed in `dase_name_curator.html` (DATA_DECISIONS 2026-08-15: five judgment calls user-resolved, 25 mechanical homoglyph/punctuation slips normalized, phantom 031000379 dropped). Loaded by `khmdhs.dase_names_loader` (validates canonical keys + rejects cross-script names; hooked at the end of `harvest_dase.py load`) into `dase_display_names`; the Atlas overlays them on every ΔΑΣΕ co-op surface via `queries_extra.dase_display_names`/`_overlay_coop_name` (real-DB pins: bijective vs the live population, payloads == table). Presentation layer only: registry `contractors.name` spellings are never rewritten, stay searchable, and remain visible as evidence («Appears in the registry as», contract-page «in the registry»); webui (:5000, frozen) keeps registry names |

## Database (`data/processed/khmdhs.sqlite`, committed)

`contracts` (flat ~50 cols + `raw_json`) with child tables `contractors`,
`contract_cpvs`, `contract_nuts`, `contract_objects` (FK **ON DELETE CASCADE**),
plus `fetch_log`, `contract_scope`, `contract_project_regions`,
`contract_sites`, `contract_payments`, `contractor_locations` (incl. `gemi`,
`lat/lon/geo_precision`), `forest_authorities` (seat coords) and
`contract_forest_authorities` (FK CASCADE; `source` =
title/objects/pdf/override/inherited:<ref>) and `contract_families`
(FK CASCADE; the call/award/sibling ΑΔΑΜ each contract's own text cites,
with the verbatim excerpt).
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

**A contract signed by several parties is split EVENLY between them**, on
both datasets and on BOTH sites (user, DATA_DECISIONS 2026-08-20: «we cannot
have a different amount of money for the ranking and a different for the
basis»). The split lives in the SHARED layer — `queries.joint_contract_shares`
/ `apply_joint_split` and `dase_queries.joint_coop_shares` — so it is applied
once and identically; the Atlas's own copies were retired to thin aliases
(applying both would subtract the same euros twice). All four columns of
totals now equal their own headline to the cent: webui Anti-nero
€601.043.031,36, webui ΔΑΣΕ €36.954.829,83, Atlas Anti-nero €622.534.181,72,
Atlas ΔΑΣΕ €29.920.558,46 (pinned in `test_webui_queries` /
`test_dase_real_db` / `test_atlas_real_db`). It is basis-agnostic on purpose:
the € come from `effective_cost` on the caller's connection, so the same code
returns gross-effective for webui and net-stated through the Atlas's shadow
views. Split surfaces: ranking, contractors/co-ops list, the entity page's
total, its signer/awarder table, its per-year bars and the map dots; contract
COUNTS and each contract's own value are untouched, and the entity's share
rides beside it. **A second RANKING VIEW** (`?rank=firm` on `/`) attributes the same money to the firms BEHIND the ventures: `queries_extra.antinero_member_firms` replaces a venture that has curated members with them and splits its € evenly (whole cents), leaves everything else alone, and sums to the SAME €622.534.181,72 — 151 names become 141, Τ&Τ ΚΑΤΑΣΚΕΥΕΣ moves 8th→3rd, and the 21 undocumented ventures' €75,3M sits identically in both views (said in the caveat, never hidden). Facts for the copy ship as `consortiums` on `/api/antinero/overview` — never hardcoded. Anti-nero has exactly TWO joint
contracts (24SYMV016018183, an ένωση, and 22SYMV010795606, a κοινοπραξία that
enumerates two firms and states no ΑΦΜ for itself — the registry keyed it under
member α and credited that firm all €836.613,02): every other joint venture
signs as a κοινοπραξία that holds its own ΑΦΜ and is one contractor. Where the
registry keyed the venture's MEMBERS instead, the party was corrected from the
signed preamble (7 contracts + 2 over-attributed ones, `contractor_party` /
`contractors_keep`); `contractor_party` also takes a LIST, which is how a
venture without an ΑΦΜ is recorded as its signing firms.

## ΔΑΣΕ dataset (`data/processed/dase.sqlite` — SEPARATE from Anti-nero)

Standalone DB of every contract 2021-09→today whose contractor is a
forest labour cooperative (ΔΑ.Σ.Ε./ΑΔΣΕ/ΕΔΑΣΕ, ν.4423/2016 — example
26SYMV019413118): 2,164 contracts, €47.0M gross, ~251 co-ops.
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
no multi-successor, and since 2026-08-17 two contracts whose signed
PDF names no co-op party) → live population **1,998 rows /
€36,954,829.83 gross = €29,920,558.46 net** (`dase_queries.live_filter`, the
scope_filter analogue; the Atlas presents net; includes the curated
corrections — the 21SYMV009374147 ×10 keying error AND 10 registry
double-postings excluded with `duplicate_of` cross-links + 1 duplicated
payment (paid net €20,405,695.74 / 953 orders after the 2026-08-17
payment audit, now CLOSED: ALL 1,033 payment PDFs fetched into
dase_pdf_cache + validated, 226 curated payment entries — re-posted
records excluded on WARRANT-NUMBER identity (amount fingerprints
can't tell same-priced instalments apart: 4 early exclusions were
reversed as proven instalments), payload amounts corrected to their
own χρηματικά εντάλματα, 123 ΕΦΚΑ understatements raised to their
warrant totals under the user convention **«paid» = the whole
disbursement incl. the state-borne ΕΦΚΑ εργοδότη** (10,28%/12,8% of
net in 2021, 24,97% in 2025), and all 42 scanned/odd documents read
by eye — every stored order is text-verified, visually verified,
curated with document evidence, or logged sub-euro noise;
`payment_loader.apply_corrections` supports an optional
**`attributed_ref` re-link** — used for the Σπερχειάδας batch, whose
11 payments pair 1:1 with the two co-ops' 11 contracts at a uniform
0,96133 ratio and are attributed accordingly), DATA_DECISIONS
2026-08-14 + 2026-08-15 (the 10th hid behind a phantom contractor ΑΦΜ
«0310003799» — VIES-invalid — so the scanner gained a cross-VAT pass);
excluded pages (the 10 duplicates AND the 2 not-a-co-op
contracts) stay reachable and are surfaced by an ΑΔΑΜ search badged with
their OWN reason (`queries_extra.dase_excluded_hits`, never counted in
the search total), and the
guard `scripts/find_duplicate_postings.py` + real-DB tests keep new
twins out). The net figure was €31,659,523.06 until 2026-08-17, when
**6 Δ/νση Δασών Δωδεκανήσου contracts** were found carrying their GROSS
in the net field (`totalCostWithoutVAT == totalCostWithVAT`,
`vat_percent` '0'): their own payment orders split the same gross at
×1.24, so the true nets are gross÷1.24 (−€480,664.92 off the basis;
gross untouched, so webui's incl-VAT presentation is unchanged).
Curated in `dase_contract_corrections.json`; the equality is now a
guard test (`test_no_live_contract_states_gross_as_its_net`) — a
future net==gross row fails the suite rather than inflating the basis,
and NO ÷1.24 heuristic exists (a genuinely ΦΠΑ-exempt contract must
trip it and get a human verdict). Anti-nero has zero such rows. Charts/rankings STAY on
stated values — payment coverage is structurally partial (893/1,998
contracts, 2022–23 near-blank as registry practice) — the paid-net Σ
appears only as a KPI with its coverage caveat. Co-ops key on
the **canonical VAT** (first 8-9-digit run zfill(9) — same co-op under
3+ spellings; 096034999 ≈ €1.9M across 12 name variants) — a WRONG ΑΦΜ therefore files a contract under the wrong entity, which is why `contractors_vat` exists. A contract
signed by SEVERAL co-ops is **split evenly** between them on every
per-co-op surface (ranking, /dase/coops, co-op page summary+yearly+units
— `queries_extra.dase_coop_shares` / `dase_coop_detail`, whole-cent
allocation via `_even_cents` so nothing is lost; contract COUNTS stay
whole, the contract keeps its own stated value and the co-op's
`share_eur` rides beside it): the registry records no shares and the one
live case (23SYMV013747204, «συμφώνησαν από κοινού» over one pooled
quantity) states none, so full attribution to both would count €5.383,95
twice — DATA_DECISIONS 2026-08-18, pinned by Σ co-op € == basis. Anti-nero
follows the SAME rule since 2026-08-20 (DATA_DECISIONS). Co-ops are
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
methodology footnotes — Anti-nero €604.5M effective vs ΔΑΣΕ €37.0M
stated ≈ 16.4×). Atlas /dase (2026-08-13): redesigned to the shared hero (green
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
basis (pinned). Directly BELOW the map, the awarding side is told
ONCE by **AWARDING PROCESS** (2026-08-17) — a THREE-column
d3-sankey (`KindFlow.svelte`; the Anti-nero `Sankey.svelte` is
scope-hardwired and untouched): awarding bodies → operating units →
contractors, width = stated net €, coloured by whichever endpoint is
the UNIT column (so the map palette carries in both stages), headings
centred on each column's bar, ONLY the left column's labels wrap (20
chars) — that narrow margin (124) lets the plot sit off-centre left
and pay for a 356 right margin, so middle and right labels stay on one
line and co-op names print in full at height 660; the chart spans the
frame's FULL width (1120), matching the map+legend row — the beeswarm's
886 is the page outlier (its 210px side-note column); a post-layout
pass vertically CENTRES every column on the plot's middle (d3 packs
from the top, so fewer-node columns rode high) shifting link ends with
them, headings excluded; node labels = € only,
black hover card on the BARS
only carrying the contract count (the one number not printed;
ribbons have no card and no on-chart annotation — the per-contract
averages were removed as ambiguous, DATA_DECISIONS 2026-08-17),
node-hover dims the rest, co-op nodes link to their pages,
empty/dangling graphs degrade to nothing (d3-sankey throws
otherwise). NO subtitle by user decision. Middle column = 3 nodes: the two forest kinds + «the body's
own services» (muni+misc merged — DATA_DECISIONS 2026-08-17 explains
why «other public bodies» was wrong
there). Right column = top-10 co-ops by € + one pooled node; consortium
contracts count at their lead co-op so all three columns reconcile.
The earlier AWARDING BODIES / AWARDING UNITS share-bar frames were
RETIRED into this diagram (same categories, colours and numbers —
saying it twice earned nothing); `StackedShareBar` stays for
/anadohoi's scope/type pair.
`queries_extra.dase_kind_mix` derives bodies + units + flows + coops +
coop_flows from ONE per-contract pass (`_dase_kind_rows`; unit kinds
mirror the map via the now-shared `_unit_forest_kind`, map-unresolved
ΑΔΜΗΕ folds into misc), ships as `kind_mix` on `/api/dase/overview`
(the bodies/units marginals now feed only the reconciliation pins),
reconciles to the basis (pinned; 'unknown' bucket pinned absent; units
marginal cross-checked against the map payload). Below it **CONTRACT
VALUES** is ONE frame under a two-button mode switch (2026-08-17):
«Individual dots» (the canvas beeswarm) / «Value brackets» (the log
histogram) — the retired SIZE DISTRIBUTION frame, merged because both
drew the same 2,008 contracts, the same stated-net variable and the
same median (verified, not assumed). Both modes render inside one
`ui/SideNote` shell so the plot keeps the same width/left edge (886 at
x=394), and nothing moves on toggle: the switch sits flush with the
frame's RIGHT edge, the brackets draw at the beeswarm's own computed
height (`plotHeight` `$bindable` out of the dodge layout; frame equal
either way) and the median line/label share the beeswarm's dash and
lettering. The **year legend serves both** modes from the left of that
same line: the brackets are stacked by signature year in the dots'
ramp (`charts/yearColors.ts`). **Both modes share ONE axis**: the
Atlas /dase brackets come from `queries_extra.dase_value_histogram`,
which derives pure-doubling edges from the live range anchored on
€1.000 (`[0] + 1000·2^k`, k=−5…9 → €31,25–€512k; webui's own
`value_histogram` brackets are untouched, that file is frozen), so
equal-width slots are equal ratios; both charts then place values with
the single `transforms/histogram.ts:binPosition` on identical margins,
and the beeswarm needs no d3 scale at all. Median gap measured 0,0px —
the coincidence is structural, not tuned. Segments are binned
CLIENT-side from the swarm array (`transforms/histogram.ts`,
reproducing `_bin_values`' half-open convention) on the histogram
payload's own edges — deriving both modes from one array is what stops
them drifting; bar counts still come from the server and
`LogHistogram` draws any shortfall in the base colour rather than
hiding it. `LogHistogram`'s `height`/`segments`/`segColors` are
defaulted, so the Anti-nero direct-award histogram is untouched (it
gained only the fix that reference-line labels now get their own row
above the bar counts — median and count labels used to overprint).
MONEY PER YEAR keeps its half-width column. /dase contract pages draw the ΚΗΜΔΗΣ family as a
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
frozen for FEATURES**: `atlas_api` imports `webui.queries` /
`webui.dase_queries` / `webui.filters` and ALL new SQL goes in
`atlas_api/queries_extra.py`. The one thing that DOES go into the frozen
modules is a shared correctness rule that both sites must obey — the
even split of a jointly signed contract (2026-08-20) lives there for exactly
that reason: implemented twice it drifts, and applied twice it double-counts.
When you touch them, run the whole suite: the Atlas pins ride on that code. The `/pdf/<kind>/<adam>` caching proxy is a
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
  **Since 2026-08-19 no page PRINTS a gross figure** — the detail pages'
  «incl. ΦΠΑ» lines and columns are gone (user: two bases side by side is
  two things to keep straight); the payload keeps `gross` for anyone who
  needs it, and the methodology says the site is net throughout.
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
  payment rows. Everything value-based reconciles to €627,572,883.18
  (pinned; was €667,496,652.26 until the 2026-08-13 antinero_probable
  exclusion, €658,297,730.65 until the 2026-08-14 Σουφλί correction, then
  €659,290,845.34 until the 2026-08-18 project-budget corrections);
  /compare is symmetric stated-vs-stated (≈21.0×); /explore has
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
  home-drill = the co-ops' contracts' dots at country frame. **The de-overlap spread is land-aware** (DATA_DECISIONS 2026-08-21): `useGeo.spreadOverlaps(points, step, onLand?)` skips spiral slots the predicate refuses; AntineroMap passes `geoContains` over the coarse Π.Ε. layer, so seats sharing one waterfront point (five at Λίμνη, nine at Μεγ. Αλεξάνδρου 27 Καβάλα) fan out along the coast, never into the sea — pinned by `maps/spread.test.ts` on the real layer. **Map cards** (user, 2026-08-21): TWO slots per map — the place's card grey at the top-left (`PaperMap splitTips`, region hover, on in every state on both maps), the item's card black at the bottom-left (dot hover); hover SHOWS, click HOLDS — a held card gets a white rule + ✕, Esc or ✕ releases (`ctx.showTip(html, {pinned, onClose})`, `DotLayer onUnpin`); cross-map hover highlights dots and links but pins NO cards (only the selected contract pins its card and its contractor's); cards are short — place · count · €, ΑΔΑΜ-as-link · authority · €, name-as-link · contracts · € — instructions live in the legend ⓘ. Round 2 the same day: the DrillPanel table below the maps is GONE (the cards carry its facts; a «✕ <unit> · all of Greece» pill beside MAP is the way out); the selection lives in the URL (`?sel=<ΑΔΑΜ>`, valid only while drilled and cleared by a new drill) so it survives the €/dots toggle and travels in a permalink; a click on bare map clears it (`PaperMap onEmptyClick`), Esc releases a held card and a second Esc resets the drill (`onEscape`); every contract dot is ONE grey (#6b6b6b, #333 stroke — the two-grey alternation is gone) and the legend swatches are the map's own colours (`.dot.work`, `.dot.sel` 14px black, `.dot.approx` dashed over a 55% fill); the € scale is the sqrt ramp (`makeChoro`, shared max on both maps) with the «0 · [white + eight swatches] · max» key — a classed/worded legend and sqrt ticks were both tried and rejected by the user on 2026-08-21 (DATA_DECISIONS); the drilled unit's outline is 1.6 (heavier than a hover, not thick), country-level registered-office dots are #555, the selected contract's dot turns black; a CONTRACTOR dot is SELECTED on click too (`?selv=<ΑΦΜ>`, one selection at a time with `sel`) — its card held, its contracts lit on the left — and its page is the card's link, not the dot (user, 2026-08-21). `DotLayer` paints hot dots (selected, or lit by a selection on the other map) LAST so they sit above their neighbours.
- **Flow charts live on the Anti-nero page** since 2026-08-20 (user): the
  out-of-region choropleth (`$lib/sections/FlowMap.svelte`) and the
  local-vs-imported split (`OriginSplit.svelte`) are ONE frame since later
  the same day — «WHERE THE MONEY TRAVELS», map left, the top-12 destination
  bars right, linked both ways (bar click focuses the map's arcs; while
  focused the bars give way to that region's flow table); since the same
  evening the bipartite («WHO REACHES WHERE») is that frame's second LENS,
  «by company» (`?flows=company`, shared focus, one lightbulb — the
  standalone frame and its `#bipartite` anchor are gone); `/` fetches `/api/connections`
  post-hydration; /connections keeps hubs, signers and consortium pairs and
  its hub tiles link to `/#flows`. The computed findings («Only N% …») moved
  from the frame TITLES into the first sentence of the subtitles — titles are
  short caps like the ΔΑΣΕ page's (user: the sentence-titles read too big).
  MONEY FLOW is a THREE-column KindFlow since 2026-08-22 (user, for
  comparability with ΔΑΣΕ): awarding body (the Ministry, one node) →
  operating units (4, `units_operator_name`, EN via `unitEn`) → top-10
  contractors + pooled, `queries_extra.unit_flows` on
  `/api/antinero/unit-flow` (even split, pinned to the basis); the phase
  sankey endpoint stays but is undrawn; ribbons take the LEFT node's
  colour when a graph has no middle column; `KindFlow` side/middle
  labels relax so they never collide (the node moves with its label),
  `wrapMid`/`leftGroup` (brace) props exist.
  RANKING OF COMPANIES sits right after the flow frame since 2026-08-21,
  its explanation behind a lightbulb and its «as contracted / by member
  firm» toggle alone on a line under the title, left; it matches the sponsored ranking (30 px
  bars, 75% measure, black); BarH clamps inside labels to two lines.
- **The Anti-nero page is black-white-grayscale ONLY** (user, 2026-08-20):
  `useGeo.RAMP_WORKS` is an 8-step grey ramp (all its choropleths/legends),
  `scopes.SCOPE_COLORS` is an ordinal grey ramp light→dark down the phase
  order (unknown lightest, the two off-phase strands darkest), flow arcs are
  solid black IN / dashed grey OUT / white-ringed dot for stays-local
  (`FlowArcs`), the drilled multi-authority contract dots alternate two greys
  (the at-rest hue grouping is gone by decision — the dashed hover links
  carry it), HQ dots #2b2b2b, Sankey/Bipartite/DisbursementCurves accents →
  ink, `.antp` overrides `--c-threshold`. The orange `--ramp-works-*` tokens
  stay as the webui-ported reference, now unused. CONTRACT VALUES is the
  ΔΑΣΕ merged frame one dataset over: dots/brackets toggle on ONE
  pure-doubling axis (`queries_extra.antinero_value_histogram`,
  `value_histogram` on `/api/antinero/overview`, pinned: Σ counts == 245),
  BeeswarmCanvas parametrized (colors/ring/thresholds/linkBase/minHeight/
  radius — ΔΑΣΕ call-sites untouched), greys by signature year
  (`yearColors.YEAR_GREYS`), single-bid rings NOT drawn on Anti-nero since
  2026-08-21 (user), 380 px floor with r 3.1, no subtitle, the ΔΑΣΕ note
  wording, the modal-bracket sentence in the brackets' side note, ν.4782
  ceiling lines kept in both modes (labels on either side when <48 px apart),
  phase colours gone from it; the frame follows RANKING OF COMPANIES; the
  old SVG `Beeswarm.svelte` is deleted.
- **/connections flow design** (no default arc spaghetti): default map =
  LINEAR %-of-works-won-by-out-of-region-firms choropleth (the finding
  «only N% stays local» is computed live and sits in the subtitle); click a
  region → FlowArcs draws only ITS flows, direction-coded with arrowheads
  (solid black = firms elsewhere reaching in, dashed black = its firms
  reaching out, white-ringed dot = stays-local €; fixed-size OPEN chevron
  heads so the stroke width alone carries the €; thin strokes 0.7–4 by
  √€ with dash+gap proportional to the width; a CUMULATIVE year slider
  sums the focused flows signed up to a year — DATA_DECISIONS 2026-08-21;
  the frame wears the allocation maps' dress: `.mapkey` strip above the
  map, MAP + ⓘ, «✕ unit · all of Greece» pill, Esc, grey place card
  top-left in every state, black arc card bottom-left — hover shows, click
  holds; the bars list EVERY destination in a scroll box with the same key
  strip). **`ChartFrame insight`** (2026-08-21): an outline lightbulb left
  of a frame's title opens its explanation in the page's LEFT MARGIN beside
  the chart (9–15 rem, never shrinking the chart; flows above under ~1500
  CSS px) — ALLOCATION OF FUNDING uses it instead of a title ⓘ; plus hub-catchment small multiples — top-6 home regions by
  exported €, one mini-map each on a shared scale, click→traces that hub.
  One-arrow-per-region "shift arrows" were REJECTED: only 19/56
  import-majority regions have a ≥50% dominant origin. **Every Atlas flow
  surface is on the EVEN SPLIT since 2026-08-20** (user: «full exposure is
  not what is happening»): `queries_extra._flow_units` divides a contract
  into k regions × m parties equal shares because the documents state no
  allocation between the units a contract covers — 100 of 245 contracts are
  multi-region — and `antinero_region_flows` / `region_flows_yearly` /
  `antinero_region_origins` are sums of those shares, reconciling to
  €622.534.181,72 (pinned). The frozen full-exposure `q.region_flows` /
  `q.project_region_origins` stay webui's own (`/map`, `/origins`, which
  say «maximum-exposure view» in their copy); no Atlas card prints a
  «full exposure» figure any more and the MAP caveat explains the split
  with the computed multi-region count.
- **Stack**: Svelte 5 (runes) + TS + adapter-node (config lives inside
  `vite.config.ts`, no svelte.config file); plain CSS custom properties
  (`src/lib/styles/tokens.css` — white-paper palette since the 2026-08-12
  rebrand + the geo_common.js ramps ported verbatim), NO
  Tailwind/Chart.js/Leaflet — d3-* + topojson only (d3-hierarchy joined the
  list on 2026-08-18 for the programme chart's packed arrangement). Fonts via the Adobe
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
- **Front page «THE PROGRAMME WAS BOUGHT IN N SEPARATE PROCUREMENTS»**
  (`ContractNetwork.svelte` + `transforms/network.ts`, DATA_DECISIONS
  2026-08-18): the drawn unit is the CALL, not the contract and not the
  connected component — one star per πρόσκληση that produced lots
  (biggest lot at the centre, siblings on spokes), then two labelled
  bands for the calls that produced exactly one contract and for the
  contracts with no call at all. Area ∝ stated net € on ONE scale across
  field and bands, colour = programme phase (`transforms/scopes`
  ramp), each star labelled with its Σ € on a row-shared baseline and the
  six richest named by ΑΔΑΜ. Calls sharing a contractor are packed as one
  block so their dashed bridge stays inside a row; collinear bridges are
  lifted 3,5u apart (two dashed lines on one axis read as one solid rule).
  Since 2026-08-18 that field is one **arrangement** among several of the
  same population (`?net=` permalink; `transforms/networkScene.ts` builds
  the per-mode scene). **Offered: time + pack** — «call» (the star field)
  was taken off the site by user decision the same day and may return;
  its scene and units stay, `NET_MODES` alone decides what shows.
  **time** (default): x = signature date, dodged by a variable-radius
  beeswarm, lots of a call joined, Greece's **fire season (1 May – 31
  Oct) shaded** — the season ships from the API WITH its count
  (`fire_season`, 120 of 245) so stripe and sentence cannot drift; prints
  «34 of the 50 split calls signed every lot on one day».
  **pack**: two levels of `packSiblings` (NOT `d3.pack`, which sorts by
  value and would centre whatever is biggest) — each call's lots packed
  into a bubble, all bubbles packed into a CORE, then the core packed as
  the first sibling among the contracts bought alone, so **grouped
  procurements hold the middle and solitary contracts ring them** (a
  pinned property). Bubble = phase hue at full strength with a 12% RIM
  carrying its ΑΔΑΜ along the arc; lots inside = same hue lightened 42%;
  ink picked by fill luminance; amounts inside marks use `format.eurTiny`
  («11,6M»), presentation only. No-call contracts carry a dashed edge.
  The scene crops the viewBox to the round blob and caps its width.
  One mark throughout — circle, area ∝ stated net €, colour = phase — in
  one keyed list, so a contract keeps its DOM node and animates between
  arrangements; chart text is `pointer-events: none` (a label used to
  swallow the hover of the mark it names). The hover card is identity
  only: ΑΔΑΜ + amount. **Both arrangements draw in the same
  `NET_HEIGHT = 400` box** (user, 2026-08-18) so the frame never jumps on
  toggle: the timeline's viewBox IS the box (`0 0 1120 400`, one unit =
  one px) and the swarm SHRINKS ITS DOTS to fit rather than overflowing;
  the packed blob is a circle, so its square viewBox and its `maxW` are
  both the box — i.e. 400×400, which is why its in-circle amounts
  disappear at this size (labels are drawn only where they fit, and
  return if the box grows). Layout is pure/deterministic (no force simulation
  → testable: 47 vitest units across `network.ts` + `networkScene.ts`);
  every printed number comes from `antinero_network`. Caveat →
  `/methodology#procurement-families`.
- **/explore** (all three datasets, one table): `/api/explore` ships ~2.3k
  compact rows once (gzipped by the response cache); an **Anti-nero row is a
  CONTRACT-CHAIN, not a record** (DATA_DECISIONS 2026-08-19):
  `queries_extra.contract_chains` walks `contract_scope.superseded_by`
  transitively into 50 chains (42×2, 7×3, 1×5 records), the row shows the
  original σύμβαση's title, spans «first → last» (`d`/`d1`), lists every
  record with its `document_kind` (`vs`), links to the tip whose value it
  carries, and answers to every ΑΔΑΜ of the chain (`alt`) so citing an earlier
  version finds it. Additive supplementary contracts stay separate rows. ALL
  filtering/sorting is client-side for instant response — dataset/Π.Ε./HQ/procedure/status/
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
  type labels; the viewed document bold; **the table holds the contract's OWN
  records only** — `contract_timeline(own_records_only=True)` drops the other
  lots the registry's adamChain returns (19 in-scope pages, up to 11 rows),
  and a line under it points at the DIAGRAM, which knows the call for 220 of
  246; the ΔΑΣΕ page follows the same rule and feeds its FamilyTree from the
  endpoint's second list `family_acts` (user, 2026-08-19); optional `top`
  snippet between heading and table; `heading={null}` when a fold prints the title, optional
  `alt` second link per row — the Anti-nero page puts its PAYMENT ORDERS in
  the trail this way, amount in the title cell, Διαύγεια in `alt`, and the
  standalone payments table is gone; heading renamed «DOCUMENT TRAIL»
  2026-08-19), `QuoteList` (verbatim Greek excerpts + source act
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
  authority/unit/signer/funding, EN names) and PAYMENT ORDERS; the Anti-nero
  one also carries **`ChainTimeline`** in the trail's `top` slot
  (DATA_DECISIONS 2026-08-19) — ActTimelineBar's conventions on a FIXED
  Anti-nero axis (2022-01-01 → today+5d): the bar is what the contract
  PROMISED — signature → the deadline it announced (`contract_deadlines`:
  registry end_date 21 / stated duration 62 / a later act 8 / **155 announce
  none → the Gantt's stub, never an invented span**), stretch of the SAME ink at 30% +
  under-bar arc + ordinal per «Παράταση προθεσμίας» (6 chains, 8 steps), a
  dot per later act of the chain, a **€** per payment order on that same
  line — marks print WHITE on the solid bar and dark off it (a white dot on
  white paper, or on the 30% extension, is no dot), ✔ where the works were accepted (may fall AFTER the deadline — that
  gap is the reading; it is NOT the bar's end, that was the old
  signature→paperwork bar the user rejected), and the printed € step where a
  supplementary approval moved the price; «today» letters on the year line,
  no printed dates under the bar;
  BEFORE the signature, a dotted **run-up** carrying the procurement's own
  acts as diamonds — primary request, commitment approval, call, award,
  from the trail's own rows (217 of 246 have ≥1 dated, 41 have all four,
  none dated after its contract — pinned; same-day acts nudge 6u and only
  the first keeps a label, drawn as GREY dots);
  the page states the bar's meaning in a note under it and every figure's
  provenance in the evidence block — the ΚΗΜΔΗΣ ΔΙΑΡΚΕΙΑ/ΕΝΑΡΞΗ/ΛΗΞΗ
  fields verbatim («recorded in ΚΗΜΔΗΣ, not quoted from the signed text»)
  and the acceptance act that names the forest service, flagged when it
  covers one part only. Matcher excerpts are cut from the ORIGINAL subject
  (folded ones read «XΩPIKHΣ APMOΔIOTHTAΣ» in half-Latin) and trimmed to
  word boundaries with «…»;
  two-way hover with the trail rows. Since 2026-08-19 the Anti-nero page is
  The TYPE row prints the curated category ALONE (a category→theme map says
  which theme it already states) and its hover card carries what the row does
  not — the extra themes the title names, and the CPV coverage deduplicated
  by theme; AREAS reads «Municipalities: … in Regional Units: …». The map is
  460 px wide and as tall as the facts+caveat column (floor 420; 506–579 px
  in practice). Arranged with TIMELINE (its own section ABOVE the trail, with the bar's
  methodology note) and DOCUMENT TRAIL as PLAIN sections, and **folds**
  (`$lib/ui/Fold.svelte`, native `<details>` + arrow) on PROCUREMENT DETAILS /
  EXTRACTED QUOTES / CPV CODES; quotes and CPV share a 2fr/1fr row; the map is
  cropped to the contract's ground via **`PaperMap.fitPes`** (fit these Π.Ε.
  WHOLE — work regions + every authority's seat region; a centroid-built frame
  cut Εύβοια in half on 26SYMV018978343) with the small MAP/DIAGRAM switch
  overlaid on the frame corner. Timeline↔trail hover pairs EVERY element
  BOTH ways (run-up acts, chain acts, € payments, extension arcs, the ✔ via
  `endRef`, the bar itself via `signedRef`; the trail row goes black, the mark
  turns `--c-antinero`). The **call mark** is filled and labelled «call · 1 of
  N» where its πρόσκληση produced more lots (`callInfo`/`onCallClick` from
  `contract.family`): its card names lots + Σ €, clicking swaps the header to
  the DIAGRAM — the cheap half of «put the circles diagram in the timeline»,
  kept subject to user review. Chart labels never share a
  row: acts above the bar (suppressed within 62u of the previous), extensions
  below it, € marks nudged clear of the dots. The chain (`contract.chain`, from
  `queries_extra.contract_chain`) is folded into the trail because the
  registry's adamChain does not carry version links; dase keeps
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

## Tests (`tests/`, 528 passing — `.venv/bin/python -m pytest`; plus `cd atlas && npm test` for the 105 frontend units)

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
