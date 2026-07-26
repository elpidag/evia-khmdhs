# Data decisions — append-only audit log

Every deliberate cleaning, classification or correction decision in this
dataset, with its evidence and the records it affects. New decisions are
appended here **first**, then implemented. Detailed per-record rationale
also lives in the `reason`/`notes` fields of the curated JSON files under
`khmdhs/data/`; this log is the citable index.

Format: date · decision · evidence · affected records.

---

## 2026-05-09 — Consortium value attribution: maximum exposure

Consortium contracts attribute the **full** contract value to each member
(not an equal split) in every per-contractor aggregate. This is the
maximum-exposure OSINT view; the UI footer states it. *Affects: all
contractor aggregates.*

## 2026-07-18 — State-vehicle umbrella contracts excluded from aggregates

Contracts awarded to ΤΑΙΠΕΔ (ΑΦΜ 997471299) and Ε.Ε.ΣΥ.Π. (997104555) are
ΥΠΕΝ↔state-vehicle pass-through frameworks whose money reappears in the
downstream execution contracts — counting both double-counts the same
euros. Scope `antinero_umbrella`, out of every aggregate; detail pages
still resolve. *Evidence: framework texts (e.g. 07.02.2022 ΥΠΕΝ-ΤΑΙΠΕΔ
framework, fund 2022ΤΑ07500000). Affects: 8 contracts, ~€950M stated.*

## 2026-07-18 — Anti-nero phase determined by fund code when titles lie

KHMDHS titles mix Greek/Latin homoglyphs; the Jun–Oct 2023 batch titled
"ANTINERO IIΙ" (three iotas) is called ANTINERO II by ΥΠΕΝ's own Diavgeia
decisions, while the visually identical Jan–Mar 2024 batch is genuinely
III. Within {II, III} the ΠΔΕ fund code decides: 2021ΤΑ07500002 → II,
2023ΤΑ07500012 → III. *Affects: scope classification of ~40 contracts.*

## 2026-07-18 — Anti-nero I identified by fund code, not title

Anti-nero I execution contracts never say "ANTINERO" in their titles; the
07.02.2022 framework's fund `2022ΤΑ07500000` identifies them. Curated into
`antinero_supplement.json`; the loader re-verifies fund + ΥΠΕΝ authority
VAT (090273987) on every load and refuses failures. *Affects: 41
antinero_i contracts.*

## 2026-07-18 — Project regions are hand-curated, never inferred

Titles abbreviate and NUTS fields point at the authority's seat (Athens),
not the work site. Regions come from reading each contract's title/objects
(`contract_regions.json`); contractors' home locations from VIES (see
below). Unresolvable entries stay explicitly `unresolved` — no guessing.
*Affects: all geographic analytics.*

## 2026-07-18 — VIES chosen for contractor addresses; AADE ruled out

AADE RgWsPublic2 notifies the queried ΑΦΜ holder by email — unacceptable
for OSINT — so lookups use the anonymous EU VIES service (no auth, no
captcha; resolved 143/180 contractors). GEMI publicity portal was
captcha-blocked at the time (see 2026-07-25). *Affects:
`contractor_locations.json`.*

## 2026-07-19 — Effective contract value = sum of payment orders

When ≥1 non-cancelled payment order (##PAY) is attributed to a contract,
the UI's value is the SUM of those payments (actual disbursement, absorbs
amendments); contracts without payments keep the stated value. Credit
orders are already signed negative by the registry («δηλώνονται με [-]»)
so plain summation is correct. *Affects: every aggregate.*

## 2026-07-19 — Payments follow supersede chains (`attributed_ref`)

Payment orders frequently stay attached to a superseded contract version
(e.g. 23SYMV012820428: 6 payments, its successor 0). Every payment records
`attributed_ref` — the final version of its contract's chain — and every
aggregate joins on it. Re-attribution runs on every `payment_loader` pass.

## 2026-07-19 — Registry keying errors corrected from signed PDFs

KHMDHS payment amounts are corrected ONLY when the signed decision PDF
documents a different figure; corrections live in
`khmdhs/data/payment_corrections.json` with the source cited:
- `25PAY016487974`: registry €992,420,531.12 → **€239,940.00** (order PDF;
  €279k study contract 24SYMV014662322).
- `25PAY018145206`: registry €21,910,411.88 → **€219,104.12** (×100 missing
  decimal; Diavgeia 9ΚΔΧ4653Π8-Ρ9Η).
- `24PAY015403292`: registry records 1 of 2 invoices → **€383,468.35**
  (Diavgeia Ρ5Α34653Π8-ΜΝ6 covers both).
A guard test fails when any payment exceeds 150% of its contract family's
stated value; the payment validator (2026-07-25) screens the rest.

## 2026-07-19 — Amendments inherit scope and regions from predecessors

Amendments titled «1η ΤΡΟΠΟΠΟΙΗΣΗ …» often carry no programme evidence of
their own. When an amendment classifies weakly (no evidence / unknown
phase), it inherits the predecessor's phase (`inherited_from_prev:<ref>`),
and its regions are inherited in `contract_regions.json`. *Affects: ~17
amendment contracts.*

## 2026-07-19 — «ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ» contracts are additive, not superseding

A supplementary contract with value <0.9× its parent adds new money — both
stay countable (e.g. ΤΜΗΜΑ 6 1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ €706k must not hide its
€4.7M parent). Same-value «συμπληρωματική» restatements (ΑΠΕ
recapitulations) do supersede. *Affects: supersede pass in scope_loader.*

## 2026-07-19 — KHMDHS is canonical for payment amounts

KHMDHS payment orders (gross) and Diavgeia clearance decisions (net of
retentions) routinely differ 6–12%; the KHMDHS figure is kept. Diavgeia
amounts are used only for twin-matching (±€1 on the same chain) and for
payments that exist ONLY on Diavgeia (5 payments, `source='diavgeia'`,
keyed by ΑΔΑ). Foreign-fund decisions (2019ΣΕ*, 2022ΤΑ07500030) are not
Anti-nero and are skipped.

## 2026-07-19 — Diavgeia decision↔contract link: «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ»

When a clearance decision cites several SYMV ΑΔΑΜs (recitals cite whole
chains), the EPDE legal-commitment field names THE contract being paid and
wins. Umbrella contracts cited as context are dropped when execution
candidates exist; candidates must converge on a single chain tip.

## 2026-07-19 — Consortium home inference policy

VIES rejects κοινοπραξία VATs. Where a member/sibling entity with a
resolved VAT identifies the home (documented per entry in
`consortium_resolver.py` with `inferred_from`), the consortium inherits
that Π.Ε.; inconclusive matches stay `consortium_unresolved`. *Affects: 19
entries.*

## 2026-07-19 — Reclassification: (Antinero II) components are IN scope

ΕΣΑ reforestation/nursery contracts and αντιδιαβρωτικά/αντιπλημμυρικά
restoration works were initially excluded as sibling programmes on title
keywords. Auditing every excluded contract's PDF showed their texts declare
membership in RRF Action 16849 «…πρόγραμμα αποκατάστασης και πρόληψης
(«antiNERO»)…» / ΠΔΕ «…(Antinero II) - ΑΝΤΙΔΙΑΒΡΩΤΙΚΑ & ΑΝΤΙΠΛΗΜΜΥΡΙΚΑ
ΕΡΓΑ» (ΟΠΣ ΤΑ 5201358) — reclassified in scope as `antinero_esa` (8) and
`antinero_restoration` (16); the 26 routine pre-programme contracts mention
antiNERO nowhere and stay out. **Standing lesson: read the contract PDF
before excluding anything.** *Trigger: user query on 25SYMV016169933.*

## 2026-07-25 — GEMI publicity JSON API adopted as second anonymous source

The portal's `/api/search` + `/api/company/details` endpoints accept
token-less requests when the full filter payload is sent (the older
`/api/searchCompany` route is captcha-gated; method from the FireWatch
project's code, verified live). Anonymous to the ΑΦΜ holder. Used to
resolve consortium VATs VIES rejects (996496315 → Βόλος, Π.Ε. Μαγνησίας —
the GEMI prefecture overrides the ambiguous 38xxx 2-digit postal fallback)
and to link 147/180 contractors to their public GEMI profiles. Misses are
cached as `"gemi": "-1"`.

## 2026-07-25 — Payment-PDF amount validation policy

Every KHMDHS payment amount is string-matched against its signed order PDF
(`khmdhs/payment_validator.py`; exact Greek format → digit-token →
spacing-tolerant). Differences ≤ €0.02 are `near_match` (registry
rounding, not errors — e.g. 21PAY009633597 differs by 1 cent) and are NOT
corrected. Larger mismatches become candidates for
`payment_corrections.json` only after human review of the PDF.

## 2026-07-25 — Disbursement time series date policy

The dashboard curve uses the payment order's signature date; ~20% of
orders carry none and fall back to the KHMDHS submission timestamp
(promptly registered, so the month is right); truly undated payments are
counted in a footnote, never plotted. Dates arrive in two formats
(`03/11/2023` and ISO) and are normalised in `webui/queries.py`.

## 2026-07-25 — Work sites: curated, with PDF evidence

Sub-Π.Ε. work sites (Δασαρχεία, τμήματα, θέσεις) are hand-curated into
`contract_regions.json` `sites` lists, each with the PDF page/excerpt that
names it (`scripts/extract_site_candidates.py` assists; nothing automated
reaches the DB). No geocoding of site names — pins would imply precision
the sources don't support.

## 2026-07-25 — Even-split € attribution on the /overview money maps

The overview choropleths divide each contract's effective value evenly
across its N project regions (and across its *located* consortium partners
for the contractor-side view), so regions sum to the programme total;
every tooltip also shows the region's full exposure (Σ of whole contracts
touching it). Basis: neither KHMDHS `contract_objects` nor the contract
PDFs itemise per-region amounts (PDF cost tables break down by cost
category only — verified on the ΕΣΑ and Έβρος contracts), and where the
registry does provide finer granularity it does so as separate τμήμα
contracts which the dataset already holds; 147/252 contracts are
single-region and need no split. FireWatch was examined and sidesteps the
question entirely (one municipality per contract via the awarding
authority — meaningless here since ΥΠΕΝ awards everything). The
`/origins` page keeps its original full-exposure convention; the two
conventions are labelled on their pages. *Affects:
`money_by_project_region` / `money_by_contractor_region` and the
/overview map; user decision.*

## 2026-07-25 — Municipality gazetteer from the Kallikratis boundaries layer

Sub-Π.Ε. geolocation (forest-authority seats, geocoding fallbacks) uses a
committed gazetteer `khmdhs/data/greek_municipalities.json` — ΥΠΕΣ code
(`KWD_YPES` 9001–9325) → official name + a representative centroid — derived
from the geodata.gov.gr open dataset **«Όρια Δήμων Καλλικράτη»**
(`oria_dhmwn_kallikraths`, CC-BY, EPSG:2100), the same source and join-key
convention the FireWatch project uses. Only centroids are committed (our maps
keep NUTS-3 polygons as the background; municipal boundaries are not drawn).
Provenance note: geodata.gov.gr was unreachable at build time (2026-07-25),
so `scripts/build_municipalities.py` derived the file from the FireWatch
repo's in-tree copy of that exact shapefile — verified field-for-field
(`NAME` + `KWD_YPES`, 326 records) identical to the portal download — and
can re-derive from the portal when it is back. The code-less «Άθως» feature
is dropped. *Affects: forest_authorities coordinates, geocode fallbacks.*

## 2026-07-25 — Forest-authority (Δ/νση Δασών–Δασαρχείο) layer

Every in-scope contract is linked to the Διεύθυνση Δασών (ΔΔ) / Δασαρχείο
(ΔΧ) responsible for its works. Extraction is a **whitelist match** of a
hand-curated registry (`khmdhs/data/forest_authorities.json`: canonical
name, genitive aliases, seat municipality, Π.Ε.) against the contract title
and KHMDHS items text, with cached contract-PDF text as fallback — free
regex capture was rejected (noisy). Amendments with no mention of their own
inherit the predecessor's authorities (same rule as scope/regions). The
residual contracts whose authority appears nowhere machine-readable are
hand-curated as overrides with PDF page/excerpt evidence. Each authority is
geolocated at the **centroid of its seat municipality** (ΔΧ are named after
their seat town; ΔΔ seat at the prefecture capital; oddballs curated —
e.g. Δασαρχείο Πάρνηθας seats in Αχαρνές). Contracts with no resolvable
authority stay honestly unlinked and are listed by the refresh TODO.
*Affects: new tables `forest_authorities`, `contract_forest_authorities`;
the /overview points map.*

## 2026-07-25 — Contractor addresses geocoded via OSM Nominatim

Contractor HQ pins use street-level coordinates for the registered address
in `contractor_locations.json`, obtained once from the anonymous OSM
Nominatim API (no key, ≥1.1 s between requests, custom UA). A hit is
accepted only when its postcode agrees with the stored postal code (3-digit
prefix) or its locality resolves to the entry's curated Π.Ε.
(`geo_precision: "address"`); otherwise the entry falls back to its seat
municipality's centroid (`"municipality"`), and entries that resolve
neither way keep no coordinates at all — misses stay honest and are counted
in the UI footnote. Coordinates are cached in the curated JSON, so the
sweep runs once per new contractor. *User decision 2026-07-25. Affects:
`contractor_locations.lat/lon/geo_precision`, the /overview points map.*

## 2026-07-25 — GEMI seat (έδρα) is canonical for contractor home regions

Trigger: ΖΙΤΑΚΑΤ (ΑΦΜ 099124894) — the portal lists two GEMI records for
one ΑΦΜ: the seat (44614807000, Λ. Σαλαμίνας & Αιαντείου, Σαλαμίνα — which
matches vrisko AND the ΕΣΑ-03 contract PDF's own description) and a branch
«(Υποκατάστημα)» (44614807001, Συγγρού 37, Αθήνα) that the search returns
FIRST. The backfill had linked the branch profile. Fixes: (1)
`gemi.pick_seat_hit` prefers non-branch records, tie-broken on the …000
parent suffix; (2) `gemi_loader --verify` re-resolves every stored number
and cross-checks the curated region against the GEMI seat prefecture
(accent-folded — «Ευβοίας»/«Εύβοιας» are the same Π.Ε.). Full sweep
2026-07-25: 147 entries, 2 branch numbers re-pointed, and **11 contractors
re-regioned to their GEMI seat** (3 Βόλος consortia previously mis-placed
in Λάρισας by the 2-digit-postal fallback; the low-confidence ΛΑΜΠΙΡΗΣ web
inference → Σαλαμίνα; 3 consortium-member inferences and 4 VIES/-web tax
addresses that differ from the registered seat — old values preserved in
each entry's notes). Policy: where VIES/AADE tax address and GEMI seat
disagree at Π.Ε. level, the registered seat wins for the flow map;
mismatch reports are reviewed by hand, never auto-applied.

## 2026-07-26 — Maps move from NUTS-3 to Π.Ε. polygons; municipality borders on drill

Trigger: the Eurostat NUTS-3 layer merges several Π.Ε. into one polygon
(EL651 = Αργολίδας+Αρκαδίας, EL541 = Άρτας+Πρέβεζας, EL653
Λακωνίας+Μεσσηνίας, EL611 Καρδίτσας+Τρικάλων, EL531 Γρεβενών+Κοζάνης,
EL613 Μαγνησίας+Σποράδων, EL515 Καβάλας+Θάσου, EL307 Πειραιώς+Νήσων and
the island groups), so region counts/€ were displayed merged even though
the database stores per-Π.Ε. regions throughout. Decision: (1) the display
unit for ALL maps becomes the Kallikratis Περιφερειακή Ενότητα. Since no
public Π.Ε. boundary file was found, the Π.Ε. polygons are **dissolved from
the geodata.gov.gr «Όρια Δήμων Καλλικράτη» municipality layer** (CC-BY; the
same FireWatch in-tree conversion already used for the municipality
gazetteer — copy kept untouched at `data/raw/firewatch_municipalities.geojson`)
via `scripts/build_pe_geojson.py`. (2) That requires a full
**municipality→Π.Ε. assignment, which exists nowhere publicly**; it is
hand-curated into `greek_municipalities.json` (`"pe"` field, 325 entries)
and machine-validated four ways before any build: every value is a
canonical `REGIONAL_UNITS` key; all 97 municipality→Π.Ε. anchor pairs
implied by `forest_authorities.json` agree; ΥΠΕΣ codes stay contiguous per
Π.Ε. (the 9001–9325 sequence is ordered Περιφέρεια→Π.Ε.→municipality);
and every municipality centroid must fall inside the NUTS-3 polygon of its
Π.Ε. (independent Eurostat cross-check). (3) Spelling aliases
(Πρεβέζης/Πρέβεζας, Ρεθύμνης/Ρεθύμνου, …) are canonicalised by
`greek_regions.canonical_pe`; aggregates key on the canonical name.
(4) NUTS-3 is retired from display (polygons, centroids, permalinks,
origin tables) but `nuts3_for` and the derived `nuts3_code` columns remain
for geocode validation (NUTS-2 prefix = Περιφέρεια test in `resolve_pe`).
(5) Even-split € attribution now splits at Π.Ε. granularity — a contract
over Αργολίδα+Αρκαδία contributes half to each polygon (previously one
merged share); programme totals are unchanged. (6) When the /overview
drill zooms into a Π.Ε., the municipality polygons of that Π.Ε. are drawn
as a border-only overlay (FireWatch-style local context). Found during
validation: **ΔΔ Ηρακλείου was pinned to the wrong municipality** — the
name-matched seat resolved to 9170 (Δήμος Ηρακλείου *Αττικής*) instead of
9305 (Ηράκλειο Κρήτης), the only duplicate name in the layer; corrected in
`forest_authorities.json` and the DB re-loaded (seat now 35.245, 25.093).
Also: the per-feature-simplified FireWatch conversion doesn't tile exactly
(micro-holes on dissolve, km-scale blockiness zoomed into small urban
Π.Ε.), so the build reads the **full-resolution EPSG:2100 shapefile**
(`data/raw/oria_dhmwn_kallikraths/`, same geodata.gov.gr layer) and
simplifies it as a polygonal coverage (GEOS `coverage_simplify`, 10 cm
grid snap; shared borders stay identical → no slivers), shipping two
detail levels: 220 m coarse for the country view, 30 m fine (≈2 px at the
deepest drill zoom) loaded lazily on drill, plus interior-only municipality
border lines; interior rings are dropped after dissolve (no Π.Ε. has a
legitimate hole). *User request
2026-07-26. Affects: `greek_municipalities.json` (+pe),
`webui/static/greek_pe.geojson`, `webui/static/greek_pe_hires.geojson`,
`webui/static/greek_muni_borders.geojson`,
`pe_centroids.json`, `webui/queries.py` aggregates, all map templates.*

## 2026-07-26 — Per-contract μελέτη (study/planning) cost extraction

Every contract PDF is scanned for the money allocated to μελέτες (the
planning work preceding the physical works). Method: (1) the corpus has
exactly one canonical anchor for a priced study line — «Κόστος εκπόνησης
μελετών (συμπεριλαμβανομένων των φακέλων ΣΑΥ-ΦΑΥ)» in the Άρθρο 4
«Συμβατικό Τίμημα» breakdown, amounts **net of ΦΠΑ** — extracted with
layout-aware rules (same-line → lone-amount next line, skipping page-break
watermarks → lone-amount previous line → prose regex both directions,
covering the ΑΠΕ recital form «…X€ το κόστος εκπόνησης των μελετών…»),
validated against all cached occurrences; nearest-amount picking is wrong
in ~40% of cases and is not used. (2) Insurance boilerplate naming the
μελετητής, «εγκεκριμένες μελέτες» title text, and μελέτη-approval recitals
are documented false-positive contexts and excluded. (3) Contracts that
mention μελετ- without the anchor are audited by a small model over
compact windows only; the ΕΣΑ design-build contracts genuinely itemise no
study price ("μελέτη και κατασκευή" bundled) and are reported as such,
never guessed. (4) Amounts attach to the contract PDF they appear in;
aggregates attribute each in-scope chain tip its own value if present,
else the nearest predecessor's (originals carry the breakdown, ΑΠΕ
restatements may update it). (5) Verified amounts land in curated
`khmdhs/data/study_costs.json` (page + excerpt evidence) → table
`contract_study_costs`. Missing/scanned PDFs stay honestly unresolved.
*User request 2026-07-26. Affects: pdf_cache (full SYMV sweep),
study_costs.json, contract_study_costs, /overview.*

## 2026-07-26 — Separate ΔΑΣΕ (forest-cooperative) contracts dataset

A standalone database (`data/processed/dase.sqlite`) of every Greek
public contract since 2021-09-01 whose **contractor is a forest labour
cooperative** (ΔΑ.Σ.Ε. ν.4423/2016, incl. ΑΔΣΕ αναγκαστικοί and the
older «δασεργατικός συνεταιρισμός» naming) — e.g. 26SYMV019413118.
Decisions: (1) **The universe is contractor-led, not CPV-led** — the
reference contract's only CPV is 77312000-0 (εκκαθάριση από αγριόχορτα,
outside the 772 δασοκομία family), so a CPV-first sweep provably
misses; forest CPVs serve as a recall check instead. (2) Source is
KHMDHS OpenData search (OpenAPI-documented body fields `contractorName`
— substring, case/accent-sensitive — `vatNumber` (contractor side) and
`cpvItems`; the server clamps every query to a 6-month submissionDate
window ending at dateTo, so the harvest sweeps explicit ≤5-month
windows; 404 = zero matches; totalElements unreliable on cpvItems —
page to last and dedupe by referenceNumber). Three passes: name
variants × windows → forest-CPV × windows recall check → per-VAT
closure (one coop appears under multiple spellings; ΔΑΣΕ ΣΚΑΛΩΤΗΣ VAT
998638016 observed under two), then amendment-chain completion.
(3) Contractor classification is a reviewed whitelist: a name regex
proposes (word-bounded ΔΑ.Σ.Ε token — «ΚΕΝΤΡΟ ΔΙΑΣΚΕΔΑΣΕΩΣ» and
«ΛΕΙΒΑΔΑΣΕ» are observed false positives — ΔΑΣΙΚ+ΣΥΝΕΤΑΙΡ, ΔΑΣΕΡΓΑΤΙΚ,
ΑΔΣΕ), and every distinct VAT is human-reviewed into curated
`khmdhs/data/dase_contractors.json` before its contracts enter the
final set. (4) **Diavgeia is not harvested**: its search cannot filter
by contractor ΑΦΜ/ΑΔΑΜ (only the paying authority's ΑΦΜ is in
metadata), so recall would require reading every decision PDF, while
ν.4412/2016 makes KHMDHS registration constitutive of contract validity
— KHMDHS is the authoritative universe. (5) Fully isolated from the
Anti-nero dataset: separate sqlite, separate PDF/text cache
(`data/processed/dase_pdf_cache/`, gitignored), no shared loaders, no
UI changes. *User request 2026-07-26. Affects: new dase.sqlite,
dase_contractors.json, harvest scripts only.*
