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

## 2026-07-27 — ΔΑΣΕ web analytics: stated values, deduplicated

The new `/dase` web section aggregates `dase.sqlite` on **stated**
`total_cost_with_vat` (no payment orders harvested yet), after excluding
(a) `cancelled = 1` rows (82 rows, €2,346,980.77) and (b) non-cancelled
rows whose `next_reference_no` resolves to a row present in the DB
(64 rows, €3,235,299.60) — a stored successor restates the contract, so
counting both double-counts; rows whose successor was never harvested
stay in as the best available value. Verified 2026-07-27: every
`next_reference_no` column value matches the payload's `nextRefNo`
exactly and no contract has multiple successors, so the column is safe
to dedup on (no `contract_scope` machinery exists in this DB). Live
population: **2,018 rows, €41,418,963.96** (vs 2,164 / €47,001,244.33
gross). The `/compare` page pairs this against Anti-nero's *effective*
values (paid-else-stated, scope-filtered) — an asymmetry stated on the
page itself. *Affects: every /dase and /compare aggregate.*

## 2026-07-27 — ΔΑΣΕ entity keying: co-ops by canonical VAT, awarders by name

Co-op aggregation keys on the canonical VAT (first 8–9-digit run of
`vat_number`, zero-padded to 9) because the registry stores the same
co-op under whitespace/spelling variants (VAT 096034999 appears under
3+ names totalling ≈€2.9M); display names come from the curated
`dase_contractors` table. Awarding-organization VATs are mis-keyed in
both directions (090273987 carries both ΥΠΕΝ and ΑΠΔ Θεσσαλίας–Στ.
Ελλάδας rows; ΑΠΔ ΘΣΕ also appears under 998019451/0998019451), while
`organization_name` is clean (49 distinct after whitespace/dash
normalisation) → org aggregates group by normalised name, never VAT.
*Affects: top/list co-ops, co-op detail pages, awarding-org tables.*

## 2026-07-27 — ΔΑΣΕ contract Π.Ε. derived from the awarding unit

`units_operator_name` (the awarding Δασαρχείο/Δ. Δασών/municipal unit;
100% filled, 102 distinct values) is the region signal for ΔΑΣΕ
contracts: folded, trigger-prefix-stripped, exact-matched against the
curated `forest_authorities.json` aliases → Π.Ε. (48 units,
1,982/2,164 contracts, 91.6%). The remaining (organization, unit)
pairs are hand-curated into new `khmdhs/data/dase_units.json` (nested
org→unit keys because generic unit names like «ΓΡΑΦΕΙΟ ΔΗΜΑΡΧΟΥ» recur
across municipalities); one genuine registry gap (ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ →
Π.Ε. Ευρυτανίας) lives there too — NOT in `forest_authorities.json`,
which feeds the Anti-nero matcher. `nuts_code` is a cross-check only
(~20% coarse EL/EL5/…; EL611/EL531 span two Π.Ε.). Unmatched, uncurated
contracts get **no region row** and surface as an explicit
«unresolved» bucket. Loaded into `dase_contract_regions` by
`khmdhs/dase_region_loader.py`. *Affects: /dase choropleth, /compare
per-Π.Ε. split.*

## 2026-08-02 — Atlas money graphics reconcile to programme totals (even-split)

The Atlas site (second web UI, `atlas/` + `atlas_api/`) extends the
2026-07-25 even-split convention to every new money graphic so each one
sums back to the programme total of **€615,950,156.78** (±€1,
unit-tested in `tests/test_atlas_real_db.py`): the sankey (ΥΠΕΝ → phase →
top-10 contractors + "others" node, effective €, consortium value split
across located partners), the per-Π.Ε. yearly series (payment-year
based, signature-year fallback, plus an explicit `unresolved_eur`
bucket), and the /connections contractor↔Π.Ε. edge weights. The payment
strip-timeline plots all **863** non-cancelled orders — 180 dated via
the submission-timestamp fallback (2026-07-25 policy), 0 left undated.
*Affects: Atlas `/`, `/connections`; no stored data changed.*

## 2026-08-02 — Cross-dataset pipelines: zero contractor overlap is the finding

/compare's headline visual states that **no company appears in both
datasets**: the 169 Anti-nero contractor VATs and the 250 ΔΑΣΕ co-ops
share not a single entity, even under the *strictest* test — both sides
reduced to canonical VATs (first 8–9-digit run, zfill(9)) before
intersecting, so spelling/whitespace registry variants cannot hide a
match. Each side keeps its own € basis, labelled on the page: Anti-nero
even-split *effective* € (Σ = €615,950,156.78 over raw VATs), ΔΑΣΕ
even-split *stated* deduplicated € (Σ = €41,418,963.96 over canonical
VATs). Shared awarding authorities are matched by normalised
`organization_name` only (per the 2026-07-27 VAT-collision decision);
the sole in-scope shared awarder is ΥΠΕΝ. *Evidence:
`test_pipelines_pins` (`vat_overlap == []`). Affects: /compare.*

## 2026-08-02 — /connections flows are full-exposure shares; dominant-origin arrows rejected

The home-region→work-region flow matrix (281 pairs from
`q.region_flows`) attributes each multi-region contract's full value to
*every* region pair it touches, so the matrix sums to ≈€1.1B — far above
the €616M programme. Decision: these € are only ever shown as **shares
or per-pair magnitudes, never summed as programme money** (caveat
printed on the page). Default map is a linear choropleth of the % of
each region's work-€ won by firms based elsewhere — programme-wide only
**13% stays local** — with directed in/out arcs drawn only for a clicked
region, plus small multiples of the top-6 contractor home hubs by
exported € (Κεντρικός Τομέας Αθηνών €139.2M, Θεσσαλονίκη €119.4M,
Τρίκαλα €87.0M, Βόρειος Τομέας €81.5M, Καβάλα €66.8M, Νότιος Τομέας
€56.9M). An election-style "one dominant-origin arrow per region" map
was evaluated and **rejected**: only 19 of the 56 import-majority
regions have a ≥50% dominant origin, so a single arrow would
misrepresent the mixed origins of the rest. *Affects: /connections.*

## 2026-08-02 — Forest authorities as cross-dataset entities, matched by folded name

Atlas gives each of the 103 registry authorities a profile page showing
both of its roles: **Anti-nero works executor** (rows from
`contract_forest_authorities`) and **ΔΑΣΕ awarding unit**
(`units_operator_name` matched via the same folded, trigger-stripped
alias matching the 2026-07-27 ΔΑΣΕ region decision uses — no new
matching logic, one registry). 48 of 103 authorities are active in both
datasets. URL slugs are derived by pure folding of the canonical name;
bijectivity over the registry (103 distinct slugs) is asserted in tests
so a future registry addition that collides fails loudly. *Affects:
Atlas /authorities, /authority/<slug>.*

## 2026-08-02 — Third dataset: «Ανάδοχοι αναδάσωσης/αποκατάστασης» sponsor acts

A standalone database (`data/processed/anadohoi.sqlite`) of the ν.998/1979
άρθρο 42 §3 sponsor scheme (added by the 13.08.2021 ΠΝΠ Α΄143; implementing
ΥΑ ΥΠΕΝ/ΔΔΕΥ/81777/2996/03.09.2021, Β΄4080): private companies finance and
execute restoration/reforestation of burnt public forest land at their own
expense, appointed by administrative act — **no procurement occurs, so
KHMDHS holds nothing** (verified: no ΑΔΑΜ stamps in any inspected act) and
the universe is Diavgeia-only. Decisions: (1) **The unit of record is the
project**, rooted at its initial «Πράξη Ορισμού Αναδόχου» ΑΔΑ; amendments,
revocations and completion acts attach to the root. (2) **Universe** =
two user-supplied Diavgeia search exports (`data/raw/list_anadaswsis.json`,
`list_apokatastasis.json`) ∪ a luminapi subject-phrase sweep across ALL
organizations (the 2021–22 Β. Εύβοια lifecycle acts were issued by
Αποκεντρωμένη Διοίκηση Θεσσαλίας–Στ. Ελλάδας before forest services moved
to ΥΠΕΝ — an ΥΠΕΝ-only search provably misses 6+ acts) ∪ a crawl of every
ΑΔΑ cited in the recitals of relevant PDFs, iterated to closure.
(3) **Diavgeia metadata is not a source of substance** for these acts
(type 2.4.7.1, empty `extraFieldValues`, empty `relatedDecisions` even on
amendments — verified on ΡΝΕΦ4653Π8-ΙΩ5): company, funder, area, location,
budget, deadlines and parent-act links are extracted from the signed PDF
text only, and every curated field carries its ΑΔΑ + verbatim excerpt as
evidence. Classification is likewise PDF-based, never subject-based —
«ΔΩΡΕΑ ΓΙΑ ΑΝΑΔΑΣΩΣΗ…» (Ω2ΕΞ4653Π8-6ΟΟ) is in fact a πράξη ορισμού.
(4) Machine extraction (incl. small-model proposals) is proposal-only:
a deterministic verifier requires each excerpt to be a substring of the
cached PDF text and each value to appear inside its excerpt, and every
assembled project is human-audited before entering the curated
`khmdhs/data/anadohoi_projects.json`, the committed source of truth.
(5) **The universe is the instrument, not the fire**: the same άρθρο 42§3
πράξη is also used for plane-tree-disease sanitation (ALFA WOOD, ΑΚΡΙΤΑΣ
— Ceratocystis platani), salvage logging of burnt timber (ΑΛΦΑ WOOD
Τατόι), and δωρεά-funded works (ΣΤΑΝΤΑ Α.Ε. Ευκαρπία) — all included
with explanatory notes rather than silently excluded. (6) Project Π.Ε.
is curated from the explicit place names each act states (Δήμος, Δ.Ε.,
Δασαρχείο αρμοδιότητας); the two genuinely supra-Π.Ε. projects (ALFA
WOOD Ήπειρος; ΔΕΔΔΗΕ five-region μελέτες) stay honestly NULL. *Affects:
new anadohoi.sqlite, anadohoi_projects.json, harvest/loader scripts
only; nothing shared with khmdhs.sqlite or dase.sqlite.*

## 2026-08-02 — Ανάδοχοι: budget honesty and project-status semantics

(1) `budget_eur` is filled ONLY when an act itself states a figure
(e.g. «προϋπολογισμού ύψους 395.200,40€», ΔΕΗ act ΩΞΕΦ4653Π8-Μ0Π); many
πράξεις state none (the sponsor merely commits to «συνολική χρηματοδότηση
του κόστους που θα προκύψει») and stay honestly NULL — press-reported
figures are never imported. Amounts are stored as written; the VAT basis
is mixed (some acts say «άνευ ΦΠΑ», Lidl's ΨΧΟ2 states both — the με-ΦΠΑ
figure kept, noted) and recorded in notes/evidence. `budget_current`
absorbs amendments (the ΣΤΑΝΤΑ δωρεά grows €3M→€4M). Any aggregate must
be labelled "stated budgets only, N of M projects". (2) Status is
derived, never asserted: `completed` requires a found «Διαπιστωτική
Πράξη ολοκλήρωσης/περάτωσης» (the latest of several lot-completions
wins, all are linked); `revoked` requires a found ανάκληση; `superseded`
marks a πράξη restated by a later one for the same works (Coca-Cola
Τατόι Α: 6ΗΥΗ €1M → ΨΟΕ8 €800k, the successor counts); a project whose
current deadline (latest amendment wins) has passed with no completion
act found is `no_completion_recorded` — explicitly NOT "abandoned",
since absence of a posted act is not proof; otherwise `active`.
(3) When an amendment's recitals cite several of a company's acts (ΡΝΕΦ
cites both Ω2ΕΞ and ΩΖ2Ο), the parent is the act named in the operative
«Τροποποιούμε την …» sentence, not the recitals — same lesson as the
Anti-nero «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ» rule. (4) Two documented clerical
slips corrected with notes (deadlines written «2021» in acts issued
after those dates: ΨΟΨΝ, 6597 — both a year short); and one act exists
only as a citation: the Coca-Cola Πηγές Καρακαντά restatement
(ΥΠΕΝ/ΔΔΕΥ/118978/4886/29.10.2025) was never found on Diavgeia — its
revocation Ε01Π is attached to the published root 63ΡΧ with the
chronology in notes. *Affects: projects.status, budget columns, chain
assembly.*

## 2026-08-02 — Ανάδοχοι: fire_event grouping curated from the act itself

Each sponsor project is tagged with the disaster that triggered it
(`fire_event`), curated ONLY from what the πράξη itself states — the acts
name their fires explicitly («…πυρκαγιά της 19ης Αυγούστου 2023 στην
περιοχή του Έβρου», «…του Ιουλίου/Αυγούστου 2021…») and the location/
evidence excerpts already in `anadohoi_projects.json` carry those
phrases. Labels are event-level (e.g. «Β. Εύβοια, Αύγ. 2021»,
«Τατόι–Βαρυμπόμπη, Αύγ. 2021», «Ρόδος, Ιούλ. 2023», «Έβρος, Αύγ. 2023»,
«ΒΑ Αττική, Αύγ. 2024», «Κρυονέρι–Δροσοπηγή, Ιούλ. 2025»). Acts that
respond to no fire (plane-disease sanitation, the ΣΤΑΝΤΑ αναβάθμιση,
generic multi-region μελέτες) get «εκτός πυρκαγιάς»; never inferred
from press coverage. *Affects: projects.fire_event, the Atlas /anadohoi
fire small-multiples.*

## 2026-08-02 — Ανάδοχοι: duration-based deadlines stored as text, never as dates

Trigger: ΨΓΦΔ4653Π8-777 (ΤΙΤΑΝ, Δερβενοχώρια) sets no calendar deadline —
«τριάντα (30) ημέρες από την ημερομηνία επιλογής μελετητή» for the study
and «τέσσερις (4) μήνες μετά την έναρξη των εργασιών … δεν δύναται να
υπερβεί το διάστημα των έξι (6) μηνών» for the works. Many acts follow
this pattern. Decision: (1) durations anchored on events OUTSIDE the
record (επιλογή μελετητή, έναρξη εργασιών) are stored as a compact
`deadline_text` (verbatim excerpt as evidence) and are **never converted
to dates** — any date would be fabricated; such projects cannot be
declared past-deadline and stay `active` unless completed/revoked.
(2) Durations anchored **on the act itself** («από την υπογραφή/έκδοση
της παρούσας») ARE convertible — the anchor date is the act's own date —
and 9 deadlines were computed this way (derivation recorded in notes,
e.g. ΨΤΑΤ: 08.02.2023 + 5 έτη → 08.02.2028; 9ΑΖΛ: 17.12.2021 + 15
ημέρες → 01.01.2022). (3) The accompanying full re-audit of every act's
text also corrected three budgets against the acts: 6Ι4Σ 404.000 →
703.228,80 (the αναδοχή totals two μελέτες, χωρίς ΦΠΑ), 6Χ7Ι null →
200.000, ΡΕΧΥ 150.000 → 310.000 (the act budgets both Δασαρχεία, Λίμνης
+ Ιστιαίας). *Affects: projects.deadline_text, deadline_initial ×9,
budget_eur ×3, anadohoi_projects.json, /anadohoi pages.*

## 2026-08-02 — Anti-nero: full procurement family (REQ/PROC/AWRD) per contract

The registry's `GET /adamChain/<ΑΔΑΜ>` returns the complete procurement
family of any act — `requests` (πρωτογενή αιτήματα), `approvedRequests`
(αναλήψεις υποχρέωσης), `notices` (διακηρύξεις/προσκλήσεις), `auctions`
(αποφάσεις ανάθεσης/κατακύρωσης), `contracts` (all sibling ΣΥΜΒ, beyond
the prev/next amendment chain) and `payments` — and each type has its own
public record + attachment endpoint (`/request`, `/notice`, `/auction`).
Decision: a new loader (`khmdhs/linked_acts_loader.py`) calls adamChain
once per stored contract and stores the upstream acts in `linked_acts`
(one row per ΑΔΑΜ, full raw_json) with the per-contract mapping in
`contract_linked_acts` (kinds: request | approved_request | notice |
auction | contract-sibling). Payments are NOT duplicated there — the
payment layer already owns them (the chain list equals `paymentRefNo`).
Harvest result (2026-08-02, all 344 stored contracts): the chain graph
only knows the links the ΣΥΜΒ payloads themselves declared — 70/344
contracts have ANY upstream act, and exactly the 41 in-scope contracts
with an `auctionRefNo` have a linked κατακύρωση (verified live: the
registry returns empty upstream lists for the rest). **Most Anti-nero
direct awards were posted with no linked ανάθεση/αίτημα** — an honest
registry-linkage gap the timeline states rather than hides. 147 upstream
acts stored (37 requests, 37 αναλήψεις, 34 notices, 39 awards). Sibling
contracts outside our dataset are stored as mapping rows only.
The Atlas contract page gains the full timeline (αίτημα → πρόσκληση →
κατακύρωση → σύμβαση → πληρωμές) with per-act PDFs through the caching
proxy. *Affects: new tables linked_acts, contract_linked_acts; refresh
chain; Atlas /antinero/contract pages.*

## 2026-08-02 — Anti-nero: project-completion acts harvested from Diavgeia

ΚΗΜΔΗΣ has no record type for a contract's ending, but ΥΠΕΝ posts the
closing acts on Diavgeia — «Έγκριση Πρωτοκόλλου Οριστικής Παραλαβής
εργασιών του έργου της Σύμβασης με ΑΔΑΜ: …» (the subject cites the
contract ΑΔΑΜ; trigger example 6Ι7Τ4653Π8-ΝΡΓ for 22SYMV011470180).
Decision: `khmdhs/completion_acts_loader.py` searches Diavgeia per stored
contract (`subject:"<ΑΔΑΜ>"`, all orgs) plus a phrase sweep fallback, and
keeps ONLY acts that certify the ending — οριστική παραλαβή (incl.
προσωρινής-και-οριστικής and «επέχει θέση οριστικής»), περαίωση,
διαπιστωτική ολοκλήρωσης. Explicitly rejected: committee formations
(συγκρότηση/ορισμός επιτροπής), παρατάσεις, τροποποιήσεις, τμηματικές
and provisional-only παραλαβές, επιμετρήσεις/ΑΠΕ and anything else the
search returns. Subjects that say only «Πρωτοκόλλου Παραλαβής» (early
acts omit «οριστικής» — e.g. 6Λ674653Π8-ΒΤ3, whose body approves the
«πρωτόκολλο οριστικής ποιοτικής και ποσοτικής παραλαβής») are resolved
from the PDF text: οριστική when the body says so, plain `paralavi` for
a final protocol without the word, rejected when the body reveals a
τμηματική/προσωρινή. The
**project end date** is extracted from the signed PDF (the πρωτοκόλλου
date in «το από DD.MM.YYYY πρωτόκολλο …», with excerpt evidence;
`end_basis='protocol_date'`), falling back to the act's own issue date
(`'act_date'`). Acts attribute to the supersede-chain tip like payments.
*Affects: new table contract_completion_acts; refresh chain; the Atlas
contract timeline.*

## 2026-08-03 — Atlas presentation basis switches to net of ΦΠΑ (excl-VAT)

Every money figure on the Atlas site (KPIs, charts, maps, tables,
footer) switches from incl-VAT to **net of ΦΠΑ**. Basis per dataset:
Anti-nero uses `total_cost_without_vat` (stated) and
`amount_without_vat` (paid) — both natively stored by the registry and
100% populated for the 252 in-scope contracts (stated net
€667,496,652.26; effective net = paid-else-stated per the existing
convention, `effective_cost(conn, alias, 'total_cost_without_vat')`);
ΔΑΣΕ uses stated `total_cost_without_vat` over the live population
(€34,085,266.14). **No flat ÷1.24 anywhere**: 654 of 2,018 live ΔΑΣΕ
contracts blend 0%/13%/24% line items (aggregate ratio 1.2152), so only
the stored net columns are trusted. Statutory context: the ν.4412/2016
άρθρο 6 εκτιμώμενη αξία — and therefore the €30k/€60k άρθρο 118
direct-award ceilings printed on the distributions — is defined **χωρίς
ΦΠΑ**, so the net switch *fixes* the previous mismatch of plotting
incl-VAT values against excl-VAT thresholds (the old
`DIRECT_AWARD_BIN_EDGES` "incl. VAT" comment was wrong in law).
Incl-VAT figures remain visible only as secondary lines on contract /
contractor detail pages (the registry states both). The frozen-webui
rule holds: all net SQL lands in `atlas_api/queries_extra.py`; webui/
pages keep their historical gross basis untouched. *User request
2026-08-03. Affects: every Atlas endpoint and page; tests re-pinned.*

## 2026-08-03 — The 5 Diavgeia-only payments: net amounts curated from the signed PDFs

The five payments that exist only as Diavgeia clearance decisions
(Ψ8Ρ14653Π8-ΥΙΜ, ΨΦ974653Π8-Θ2Ζ, 6ΦΡΚ4653Π8-ΡΙΜ on 23SYMV013201961;
6ΣΟΒ4653Π8-ΧΞ0 on 23SYMV012972202; 6ΗΔ34653Π8-ΙΞΓ on 22SYMV010643071 —
€3,564,291.81 gross) carry no `amount_without_vat`, which would
silently understate every net paid aggregate. Decision: extract the
net-of-ΦΠΑ figure from each signed PDF (cached in
`diavgeia_cache/`) and record it via `payment_corrections.json` (new
optional `amount_without_vat` key, excerpt evidence per entry,
applied by `payment_loader.apply_corrections`). A payment whose PDF
states no net figure keeps NULL and the gap is footnoted on
/methodology — never imputed. *Affects: contract_payments net sums,
Atlas paid-net KPI.*

## 2026-08-03 — ΔΑΣΕ parity harvest: linked acts + payments from ΚΗΜΔΗΣ, completion acts from Diavgeia

The ΔΑΣΕ dataset gains the same registry-family layers as Anti-nero,
via the existing `--db`-parametrised loaders (no forks): (1)
`linked_acts_loader` sweeps `GET /adamChain/<ΑΔΑΜ>` for all 2,164
stored contracts — new additive `--with-payments` flag also records the
chain's payment ΑΔΑΜs as mapping rows (kind `payment`) so payment
discovery is chain-fresh rather than bound to the 2026-07-26 raw_json
snapshot; (2) `payment_loader` (new `--refs-from-linked-acts` flag
unioning those refs with raw_json `paymentRefNo`) fetches the ~1,032+
payment orders; with no `contract_scope` table attribution degrades to
identity, which is correct — all 891 ref-carrying contracts are live.
(3) Completion acts: the 2026-07-26 "Diavgeia is not harvested"
decision is *narrowly revised* for project endings only. A live probe
showed the subject-scoped query is the wrong tool for ΔΑΣΕ (0 hits) but
a **bare quoted-phrase query** (`q="<ΑΔΑΜ>"`) matches citations beyond
the subject line (control 22SYMV011470180: 7 vs 2 hits; ΔΑΣΕ
24SYMV015692405: 9 hits) — so `completion_acts_loader` gains
`--query-mode bare` (default `subject` unchanged for Anti-nero), a
`--cache` dir flag (ΔΑΣΕ PDFs go to gitignored `dase_diavgeia_cache/`),
and a `completion_search_log` table for resumability; in bare mode a
classify()-passing act whose subject lacks the ΑΔΑΜ is accepted only if
the ΑΔΑΜ appears in the PDF text. Rollout is gated: a 50-contract probe
first; the full ~2,018-search run (~15–30 s/query server latency) only
if the probe yields real completion acts, else the `contractRelatedADA`
org-crawl (present on 1,500 live rows, resolves 9/10) is proposed
instead. **Analytics conventions unchanged**: ΔΑΣΕ aggregates stay
stated (now net), deduplicated; the paid figure appears only as a KPI
with its coverage caveat (payments declared for 891/2,018 live
contracts ≈ 72.6% of stated €; 2022–23 near-blank is registry practice,
not reality). *Affects: dase.sqlite gains linked_acts,
contract_linked_acts, contract_payments rows, contract_completion_acts,
completion_search_log; Atlas /dase pages.*

## 2026-08-03 — Ανάδοχοι budgets: net preferred where the act states it (revises the Lidl gross choice)

Sponsor-act budgets are VAT-mixed: of the 43 stated budgets, 15 say
«άνευ/χωρίς ΦΠΑ», one (Lidl ΨΧΟ24653Π8-82Χ) states both bases, 27 give
a bare figure. Decision: (a) every budgeted project gets a curated
`budget_vat_basis` (`net` | `gross` | `unstated`) with verbatim excerpt
evidence, re-reading the full cached PDF texts of the 27 silent acts
for VAT language anywhere in the act; (b) where a net figure is stated
or derivable from the act itself, it is stored as `budget_net_eur` —
this **reverses the 2026-08-02 choice** of keeping Lidl's με-ΦΠΑ
€300,000 (now the act's own €241,936 net is preferred); (c) the
headline "total committed" prefers `budget_net_eur` where present and
is labelled «net where the act states it — N of 43 documented»;
projects whose acts stay silent are **never converted** — the figure
remains as written, flagged `unstated`. *User decision 2026-08-03.
Affects: anadohoi_projects.json, anadohoi.sqlite schema (budget_vat_basis,
budget_net_eur), /anadohoi KPIs, /explore, /methodology.*

## 2026-08-03 — ΔΑΣΕ project endings are NOT recoverable from Diavgeia (negative finding)

Probed before any full sweep: 75 live contracts searched with the bare
quoted-ΑΔΑΜ query (50 sequential 2021 + 25 stratified across 2022–2026)
→ **1 raw hit, 0 completion-classified acts**. The rare hit-bearing
contracts (e.g. 24SYMV015692405, 9 citations) carry only επιμετρήσεις,
εκκαθαρίσεις πληρωμής and ορισμούς επιβλεπόντων — all correctly rejected
by the strict completion classifier. The `contractRelatedADA` fallback
(resolves the awarding org's Diavgeia id, 9/10 sample) was feasibility-
tested on 3 δήμοι: each org holds 135–302 generic «οριστικής παραλαβής»
acts spanning ALL its municipal projects, subjects name the έργο title
never the ΑΔΑΜ, and small υπηρεσίες are bundled into plural
δημοτικό-συμβούλιο approvals that name no project at all — so no
reliable act→contract join exists short of reading every PDF of every
municipality (confirming the 2026-07-26 "Diavgeia is not harvested"
rationale). Decision: **ΔΑΣΕ endings stay unharvested and honestly
absent** — /explore keeps `fin = NULL` for ΔΑΣΕ rows and the methodology
states the finding; the paid-vs-stated ratio (payments now harvested) is
the available delivery signal. The 54 searched contracts are logged in
`completion_search_log` (dase.sqlite). *Affects: /explore end-date
filter, /methodology; no stored rows.*

## 2026-08-03 — Atlas analytics basis: STATED values; payments become their own layer

The Atlas retires the *effective* value (payments-sum-else-stated) from
every chart and aggregate: contract-value analytics — maps, sankey,
beeswarm, histograms, rankings, per-Π.Ε. series, contractor pages, lists,
/connections, /authorities, /compare, /explore — now use the **stated
contract value (net of ΦΠΑ)** even when payment orders exist. The Anti-nero
analytic total is **€667,496,652.26** and every money graphic reconciles
to it (pinned). Payment data is NOT hidden: the payments strip timeline,
the cumulative disbursement curves, the «actually paid» KPI tiles, the
per-contract payment lists and the contractor paid-per-year bars remain as
an explicitly-labelled payments layer (Σ paid net €440,019,108.41 in
scope). /compare becomes symmetric — stated vs stated on both sides
(≈19.6× at the totals) — retiring the old basis-asymmetry footnotes.
Mechanism (same doctrine as the 2026-08-03 net views, webui still frozen):
the analytics connection passes through `apply_stated_basis`, whose TEMP
`contract_payments` view presents zero rows, so every frozen
`effective_cost()` call site COALESCEs to the stated column with no code
copies; a second per-request connection with real payments serves the
payments layer. Per-year attribution in stated basis = stated € at
signature year. /explore collapses to a single «Stated value (net)»
column (the effective column is gone; Ανάδοχοι keep committed-net-where-
stated). *User decision 2026-08-03. Affects: every Atlas value graphic;
tests re-pinned; no stored data changes.*

## 2026-08-03 — Fourth dataset: «Αρωγή πυροπλήκτων» (state aid to fire victims, fires ≥2021)

A standalone database (`data/processed/arogi.sqlite`) of state aid to
people affected by wildfires from 2021 onwards, dual-sourced and
cross-checked. Universe & rules: (1) **The fire universe is the
οριοθέτηση ΚΥΑ registry** (43 fire-delimitation acts found on Diavgeia,
curated into `khmdhs/data/arogi_fires.json` with fire dates, ΦΕΚ and
delimited municipalities → Π.Ε.); an act belongs to a fire by the
οριοθέτηση/fire date **cited in its recitals, never by its own issue
date** — ΓΔΑΕΦΚ still issues acts today for the 2018 Μάτι fire, and
those are excluded (fire date ≥ 2021-01-01; exclusions counted).
(2) **Privacy: owner names are never stored or displayed.** The
per-building acts print full names of private individuals; the dataset
keeps only ΑΔΑ, act kind, amounts, municipality/Π.Ε., fire, dates and a
case key — the Diavgeia PDF remains the public record. (3) **Rows are
aid CASES**: follow-up acts (βεβαιώσεις προόδου/περαίωσης, δόσεις) cite
the originating repair permit's protocol/ΑΔΑ → deterministic grouping
into per-building cases; unmatched acts stay honest single-act rows
(if <70% of follow-ups match, the layer falls back to flat acts).
(4) **Bases are never merged**: στεγαστική συνδρομή *approved* (the
«ΣΥΝΟΛΙΚΟ ΠΟΣΟ ΣΤΕΓΑΣΤΙΚΗΣ ΣΥΝΔΡΟΜΗΣ (ΔΩΡΕΑΝ ΚΡΑΤΙΚΗ ΑΡΩΓΗ) #…€#»
anchor), doses *paid* (ΔΚΑ vs άτοκο δάνειο split), πρώτη αρωγή
*budgeted* (ΥΠΟΙΚ ΠΔΕ Πράξεις), official *paid running totals*
(civilprotection/minfin press announcements — stored as verbatim quotes
with URLs in `khmdhs/data/arogi_press_totals.json`), and ΕΛΓΑ
*agricultural compensation* (per-year figures hand-transcribed from the
annual activity reports into `khmdhs/data/elga_fire_compensation.json`
with page evidence) are distinct measures; the /arogi/summary
cross-check compares like-for-like and **highlights mismatches instead
of averaging them**. (5) Per-person πρώτη-αρωγή payments (ΑΑΔΕ bank
credits) are not public anywhere — the dataset's granularity is
per-building (Σ.Σ.) and per-batch (πρώτη αρωγή), stated on the page.
No open dataset exists for any of this (data.gov.gr CKAN verified
empty; the arogi portals are application-only) — Diavgeia acts and
official announcements are the only public sources. *User request
2026-08-03. Affects: new arogi.sqlite, khmdhs/data/arogi_*.json,
elga_fire_compensation.json, Atlas /arogi + /arogi/summary.*

## 2026-08-11 — Ανάδοχοι sponsor grouping: Lidl merged across scripts; Coca-Cola label names both entities

Two presentational-grouping fixes in the Atlas sponsor ranking
(`_SPONSOR_GROUPS`, atlas_api/queries_extra.py); project rows keep each
act's verbatim company name, and no stored data changes. (1) **Lidl** was
the one multi-spelling sponsor missing from the merge list, so the
ranking counted it twice: ΨΧΟ24653Π8-82Χ (Β. Εύβοια) writes «ΛΙΝΤΛ ΕΛΛΑΣ
& ΣΙΑ.Ο.Ε» in Greek script while 67684653Π8-9Ω3 (Τατόι) writes «Lidl
Hellas & Σια Ο.Ε.» — the same Ο.Ε., whose Σίνδος HQ (Ο.Τ. 31, ΔΑ 13,
Τ.Θ. 1032, Τ.Κ. 57 022) the Τατόι act itself prints. Merged as «Lidl
Ελλάς» (stems LIDL/ΛΙΝΤΛ); the sponsor count drops 37 → 36. (2) The
Coca-Cola group label «Coca-Cola 3Ε Ελλάδος» silently attributed
ΨΟΕ84653Π8-ΩΤΡ to the bottler, but that restatement names «COCA COLA
Hellas» at Λ. Κηφισίας 26 & Παραδείσου 2 — a distinct legal entity from
COCA COLA 3Ε Ελλάδος Α.Β.Ε.Ε. (the superseded 6ΗΥΗ names 3Ε at a
different Μαρούσι address; the Nov 2021 restatement switched entity and
cut the budget €1M → €800k). The two companies act as one brand system,
so the group stays merged with the label restated honestly as
**«Coca-Cola (3Ε / Hellas)»**. *Evidence: signed act PDFs (addresses as
above), anadohoi_projects.json excerpts. Affects: /anadohoi sponsor
ranking + n_companies KPI; no rows.*

## 2026-08-11 — Ανάδοχοι: curated `deliverables` (works / study_and_works / study) from each root act's operative σκοπός

Every sponsor project now carries what the appointment actually covers —
εκτέλεση έργου only (42), εκπόνηση μελέτης και υλοποίηση έργου (20), or
εκπόνηση μελέτης only (7) — as a curated field with a verbatim σκοπός
excerpt in `evidence.deliverables` (whitespace-collapsed containment
verified against the act's pdftotext text; all 69 root-act PDFs fetched
into anadohoi_cache in the process). Classification basis: the operative
«Ορίζουμε … με σκοπό …» sentence; the «Οι όροι …» clause corroborates.
Regex only proposed — a first naive pass mislabeled 22 acts because Greek
inflection breaks adjacency («εκπόνησης μελέτης», «εκπόνηση των
απαιτούμενων μελετών») — and every verdict is human. Judgement calls
worth recording: (1) ΔΟΞΙΑΔΗΣ 9ΙΡΜ is study-only BY ITS OWN TEXT («Για
την ανάληψη της υλοποίησης … θα πρέπει να εκδοθεί νέα Απόφαση ορισμού»);
(2) ΑΔΜΗΕ 6ΦΤΩ and the Ρόδος zone executors (Eurobank 971Χ, NOVA 6ΩΜ0)
are works-only despite όροι boilerplate naming μελέτη — each act states
«Η εκτέλεση των εργασιών θα γίνει σύμφωνα με τα οριζόμενα στην ανωτέρω
(9) σχετική μελέτη που εγκρίθηκε αρμοδίως» (the studies were done by
others — the ΕΝΩΣΗ ΞΕΝΟΔΟΧΩΝ ΡΟΔΟΥ act ΨΥΒ0 is the Rhodes studies-only
appointment); (3) Βιοποικιλότητας Θράκης ΡΔ0Λ executes per the approved
WWF-commissioned μελέτη (ΨΠΤΚ4653Π8-ΛΞΛ) → works; (4) the «υλοποίηση
της Μελέτης» pair (WWF Κερατέα ΡΛ16, Εren Groupe pilot 9Φ9Ρ) and ΣΤΑΝΤΑ
ΨΤΑΤ classify study_and_works — their σκοπός is ambiguous but the όροι
sentence binds both «εκπόνησης … των μελετών» and «εκτέλεσης …
των έργων» and each requires notifying the επιβλέποντα των εργασιών
(evidence excerpt = the όροι sentence for these three); (5) the
plane-disease sanitation acts split honestly: ΨΞΒΠ (Tatoi salvage, no
μελέτη clause) = works; 6Φ45/ΡΟΘΕ/ΨΖ3Ψ (σύνταξη Τεχνικής Μελέτης-Έκθεσης
+ απομάκρυνση) = study_and_works. Side finding: Lidl's two projects are
the μελέτη act (ΨΧΟ2, €241,936 net) and the works act (6768) of the same
restoration. The committed sqlite was migrated in place (ALTER TABLE +
UPDATE) because harvest.json lives only on the build machine; the loader
schema gained the column for future rebuilds. *Evidence:
anadohoi_projects.json `deliverables` + evidence excerpts; act PDFs.
Affects: projects table (new column), /anadohoi/project/[ada] «Scope of
appointment» row + Evidence block, tests (42/20/7 pin).*

## 2026-08-12 — Ανάδοχοι review correction: Ψ6Ι24653Π8-71Γ works_kind → both

User PDF review of the new deliverables sheet caught a works_kind slip:
the HELLENIQ Πεντέλη act (Ψ6Ι24653Π8-71Γ) was curated `anadasosi` off the
appointment TITLE («Ανάδοχο Αναδάσωσης»), but its operative έργο is
«υλοποίηση έργου αποκατάστασης και αναδάσωσης … 170 στρεμμάτων» — and the
identically-worded same-template NORDIA act (ΨΖΩ14653Π8-Θ6Σ) was already
curated `both` with exactly that phrase as evidence. Fixed to `both`,
evidence.works_kind now the έργο phrase («αποκατάστασης και αναδάσωσης»),
aligning the two. A systematic re-scan of all 69 operative sentences
(excluding the framework-ΥΑ title boilerplate that recites «Αναδόχους
αποκατάστασης και αναδάσωσης δημοσίων εκτάσεων» in every act) found NO
other single-kind project with a both-kind έργο. *Evidence: signed act
PDF Ψ6Ι24653Π8-71Γ; anadohoi_projects.json. Affects: 1 row (works_kind +
evidence_json), /anadohoi/project page «Type of intervention».*

## 2026-08-12 — Ανάδοχοι review correction: ΡΛ164653Π8-ΠΞΝ deliverables → works

User PDF review verdict on the WWF Κερατέα act (ΡΛ16): «ανάληψη
χρηματοδότησης και υλοποίησης της Μελέτης Αναδάσωσης … 138.678,07€»
means funding and IMPLEMENTING the reforestation the μελέτη prescribes —
works only, not study_and_works as first curated (the όροι boilerplate
had tipped the initial call). Evidence excerpt switched to the σκοπός
sentence. Deliverables split now 43 works / 19 study_and_works / 7
study (test pin updated). The same-template Εren Groupe pilot (9Φ9Ρ,
«υλοποίησης της πιλοτικής μελέτης») stays study_and_works pending the
same review. *Evidence: signed act PDF ΡΛ164653Π8-ΠΞΝ. Affects: 1 row.*

## 2026-08-12 — Ανάδοχοι review correction (final): ΡΛ164653Π8-ΠΞΝ deliverables → study; «υλοποίηση μελέτης» counts as εκπόνηση μελέτης

Supersedes today's earlier works verdict for ΡΛ16 (WWF Κερατέα): on
re-reading the PDF the user rules «ανάληψη χρηματοδότησης και υλοποίησης
της Μελέτης Αναδάσωσης» means delivering the μελέτη itself — counted as
εκπόνηση μελέτης (deliverables = study). Convention recorded: a σκοπός
phrased «υλοποίηση μελέτης» classifies as study. Evidence excerpt stays
the σκοπός sentence. Split now 42 works / 19 study_and_works / 8 study
(test pin updated). Same-construction acts pending the user's per-PDF
verdict under this convention: 9Φ9Ρ (Εren pilot, «υλοποίησης της
πιλοτικής μελέτης», currently study_and_works) and ΨΤΑΤ (ΣΤΑΝΤΑ,
«υλοποίηση μελέτης αποκατάστασης–αναδάσωσης», currently study_and_works
— its act also names εργολήπτη/επιβλέποντα εργασιών and a 5-year έργο).
*Evidence: signed act PDF ΡΛ164653Π8-ΠΞΝ. Affects: 1 row.*

## 2026-08-12 — Ανάδοχοι review correction: 9Φ9Ρ4653Π8-ΞΕΦ deliverables → study

User PDF verdict on the Εren Groupe pilot (Λίμνη Ευβοίας, 51 στρ.,
48.650,90 €): «υλοποίησης της πιλοτικής μελέτης αναδάσωσης» is the
delivery of the μελέτη itself — study, per the «υλοποίηση μελέτης» =
εκπόνηση μελέτης convention set with ΡΛ16 today. Evidence excerpt
switched from the όροι sentence to the σκοπός sentence. Split now
42 works / 18 study_and_works / 9 study (test pin updated). Of the
same-construction acts only ΨΤΑΤ (ΣΤΑΝΤΑ) remains study_and_works,
pending the user's verdict against its εργολήπτη/επιβλέπων-εργασιών and
5-year-έργο clauses. *Evidence: signed act PDF 9Φ9Ρ4653Π8-ΞΕΦ.
Affects: 1 row.*

## 2026-08-12 — Ανάδοχοι review correction: ΨΤΑΤ4653Π8-2Γ7 deliverables → study

User PDF verdict on the ΣΤΑΝΤΑ Ευκαρπία act: «ανάληψη χρηματοδότησης και
την υλοποίηση μελέτης αποκατάστασης – αναδάσωσης … 3.309 στρεμμάτων» is
study, per the «υλοποίηση μελέτης» = εκπόνηση μελέτης convention — the
εργολήπτη/επιβλέπων-εργασιών and 5-year clauses read as framework terms
for what follows the μελέτη, not as part of this appointment's
deliverable. Evidence excerpt switched to the σκοπός sentence, sliced to
start at «ως Ανάδοχο …» so the principal's personal name is not stored.
All three «υλοποίηση μελέτης» acts (ΡΛ16, 9Φ9Ρ, ΨΤΑΤ) now classify
study; split 42 works / 17 study_and_works / 10 study (test pin
updated). *Evidence: signed act PDF ΨΤΑΤ4653Π8-2Γ7. Affects: 1 row.*

## 2026-08-12 — Ανάδοχοι deliverables: full 69/69 PDF review completed

The user reviewed every one of the 69 root-act PDFs against the curated
`deliverables` field on the review sheet and confirmed completion
(verified list cross-checked exactly against the projects table — no
project missing, none unknown). The pass produced four corrections, each
logged above as it landed: Ψ6Ι2 works_kind → both, and ΡΛ16 / 9Φ9Ρ /
ΨΤΑΤ deliverables → study under the «υλοποίηση μελέτης» = εκπόνηση
μελέτης convention. Final verified split: 42 εκτέλεση έργου / 17 μελέτη
και έργο / 10 μελέτη. The field is now fully human-verified against the
signed acts. *Affects: no rows (closure record).*

## 2026-08-12 — Β. Εύβοια: ψηφιοποίηση των 9 ζωνών αντιπλημμυρικών έργων (Master Plan, φύλλα 4.1/4.2)

The two Master-Plan works maps the user supplied (data/raw/
XARTHS_ERGON_DAS_LIMNHS_4.1.pdf, XARTHS_ERGON_DAS_ISTIAIAS_4.2.pdf —
«ΧΑΡΤΗΣ ΑΝΤΙΠΛΗΜΜΥΡΙΚΩΝ ΕΡΓΩΝ», ΥΛΗ, Νοέμβριος 2021, 1:30.000) define
the ΛΙΜΝΗ Ι–V and ΙΣΤΙΑΙΑ Ι–ΙV works zones the Εύβοια sponsor acts cite.
Digitised as follows: the sheets are single JPEG rasters (4872×3681) —
georeferenced via their printed ΕΓΣΑ87 grid (721.75 px per 5 km, ±1 px on
both sheets; anchors in the curated file); machine pre-extraction
(watershed over the drawn black boundary lines) produced first-pass
polygons, and the user then hand-corrected/redrew ALL NINE zones in a
purpose-built editor over the original sheets. The user's pixel-space
vertices are the committed source of truth
(khmdhs/data/evia_works_zones_digitised.json);
scripts/build_evia_zones.py georeferences them, clips to the Kallikratis
high-res coastline and writes data/processed/evia_works_zones.geojson
(WGS84). Validation: digitised vs the sheets' own area tables — Λίμνη Ι
96.9% / ΙΙ 99.3% / ΙΙΙ 99.6% / ΙV 91.1% / V 97.8%, Ιστιαία Ι 99.8% / ΙΙ
77.7% / ΙΙΙ 70.3% / ΙV 100.0% (the deltas on Ιστιαία ΙΙ/ΙΙΙ are the
as-drawn extents; the tables tabulate basin areas, not always the drawn
zone). Finding: sheet 4.1's table misprints Λίμνη ΙV as «20.6827,401» —
the drawn zone is the sheet's largest and the digitisation confirms
~206.8k στρ. Zone↔project mapping (by the acts' basin citations): Λίμνη Ι
→ EREN 6ΡΤΣ, Λίμνη ΙΙ → ΔΕΗ 9Κ9Τ, Λίμνη V → ΔΕΗ ΩΞΕΦ, Ιστιαία Ι → ΔΕΗ
ΨΟΨΝ (Δάσος Βουτά), Ιστιαία ΙΙΙ → ΔΕΗ 6ΠΔΕ (Δάσος Αβγαρίας), Λίμνη Ι–V →
ΔΕΔΔΗΕ μελέτες ΡΕΧΥ. Tests pin the 9 zones, area bands and geometry
bounds (tests/test_evia_zones.py). *Affects: new curated file + build
script + processed geojson; site representation to follow.*

## 2026-08-12 — Ανάδοχοι: works_zones field + οι ζώνες στο site

The six Εύβοια sponsor projects now carry their digitised works zone(s)
as curated data (`works_zones` in anadohoi_projects.json, basis: each
act's basin/zone citation — the excerpts already in evidence.location):
6ΡΤΣ→limni_i, 9Κ9Τ→limni_ii, ΩΞΕΦ→limni_v, ΨΟΨΝ→istiaia_i,
6ΠΔΕ→istiaia_iii, ΡΕΧΥ→limni_i..v (the ΔΕΔΔΗΕ studies covered all five
Λίμνη basins). Loader schema + committed DB migrated (28th column);
the API ships the parsed list on the overview and project endpoints.
Site: project pages show a ZoneMap (the project's zone highlighted on
the Εύβοια outline, other zones as faint context, caption with the
digitised στρέμματα and source note); the /anadohoi Π.Ε. map draws all
nine zones as a quiet polygon layer under the dots, and zone-mapped
projects' dots sit at their zone centroid instead of the Π.Ε. centroid
spread. build_evia_zones.py now also emits per-zone centroids and
duplicates the geojson into atlas/static/geo/. Tests pin the 6-project
mapping. *Affects: 6 rows (new column), atlas frontend, no aggregates.*

## 2026-08-12 — Ανάδοχοι: the sponsor-ranking co-op note is act-backed (audit)

The /anadohoi ranking footnote naming executing forest co-ops was
audited to its sources and tightened («often» → «some», specific works
named, act PDFs linked). Basis: (1) NOVA Ρόδος Ζώνη 4 (root
6ΩΜ04653Π8-31Ι) — stored handover act 66584653Π8-9Φ3 «ΠΡΩΤΟΚΟΛΛΟ
ΕΓΚΑΤΑΣΤΑΣΗΣ Δασικού Συνεταιρισμού “Αγίου Δημητρίου Πιερίας” κατόπιν
της … Πράξης Ορισμού Αναδόχου Αποκατάστασης της εταιρείας “Nova …”».
(2) ΤΙΤΑΝ/Κανελλοπούλου Κρυονέρι–Δροσοπηγή (roots ΨΒΟΣ4653Π8-9ΣΨ,
9Β164653Π8-ΚΚΩ) — the stored completion acts Ρ6Θ14653Π8-77Ρ and
ΡΜΖΩ4653Π8-1ΤΟ state in their PDF body: «υλοποιήθηκε από το Δασικό
Συνεταιρισμό ΔΑΣΕ Γαρδικίου Τρικάλων και την ατομική επιχείρηση
“Σιδέρη Μαρία του Δημητρίου”, η οποία εγκατέστησε το Δασικό
Συνεταιρισμό Μίστρου “Άγιος Κυπριανός”» — i.e. Γαρδικίου was one of
two executors there, and the ΤΙΤΑΝ link is to the 2025 Κρυονέρι works,
NOT the 2023 Δερβενοχώρια project (no executor evidence stored for
that one). Both PDFs fetched into anadohoi_cache (with 973Ι/Ψ1ΒΥ/ΨΞΥ8,
which name no executor). *Evidence: the two act PDFs. Affects: UI copy
only, no rows.*

## 2026-08-12 — Ανάδοχοι: curated `executors` — the sponsor→ΔΑΣΕ link is systemic (13 projects, 23 rows)

Following up the same-day note audit: ALL 322 decision PDFs were fetched
(243 new into anadohoi_cache; 34 fetch failures — timeouts plus a few
homoglyph-corrupt ΑΔΑs stored from PDF extraction) and swept for
Συνεταιρισμ/ΔΑ.Σ.Ε. mentions (116 windows, 45 acts). After dropping
boilerplate (taxisnet/ΓΕΜΗ/law citations, the ΔΑΣΕ ΑΤΤΙΚΗΣ «ΠΑΡΝΗΘΑ»
salvage lease 6ΑΦ5), **13 of 69 projects name executing forest co-ops**
in their act trails → new curated per-project `executors` array
(name, dase_vat, source act ΑΔΑ, verbatim excerpt — mechanically
verified ⊂ act text): NOVA Έβρος→Ορεινός Χρυσομηλιάς; Coca-Cola
Αχαΐα→Μακεδονικά Αλυσοπρίονα + Παντουρέ; ΔΕΠΑ Παλαγία→Σιδηροχωρίου and
Άβαντας→Ακρίτα Αλεξανδρούπολης; NOVA Ρόδος Ζ4 + Eurobank Ζ5→Αγ.
Δημητρίου Πιερίας; Εθνική Χίος→Αγιοκάμπου/Περτουλίου/Φωτεινών/Προμάχων
«Νέα Γενιά»; ΤΙΤΑΝ+Κανελλοπούλου Κρυονέρι→Γαρδικίου + Μίστρου «Άγιος
Κυπριανός» (via the contractor «Σιδέρη Μαρία»); ΔΕΗ Ιστιαία Ι→
Σιδηρονερίου Δράμας, Ιστιαία ΙΙΙ→«ΜΙΣΤΡΟΣ» Μίστρου, Λίμνη ΙΙ→Μίστρου/
Ροδόπη/Ένωση Σταυρού/Πωγωνίου/Παπάδων, Λίμνη V→Λιβαδίου. **Identity
policy**: `dase_vat` set ONLY where the act's wording pins a single
ΔΑΣΕ-registry entry (14 distinct VATs); ambiguous or absent ones stay
honestly unlinked with a note (Παντουρέ + Παπάδων not in the registry;
«Σιδηρονερίου» Δράμας ≈ 5 candidates; «Περτουλίου» ≈ 2; plain «Μίστρου»
/ «ΜΙΣΤΡΟΣ» never merged onto «Άγιος Κυπριανός» 996895246). The
Eurobank Ζώνη-5 evidence acts (6ΔΤ1 etc.) are stored decisions with NO
project_decisions links — TODO: link that lifecycle. sqlite migrated in
place (ALTER TABLE, 13 rows); loader schema now 29 cols. The ranking
chart's anecdotal footnote was REMOVED — replaced by a dedicated
«executors» section on /anadohoi (chips → /dase/contractor/<vat>) and a
«Works executed by» row + evidence excerpts on project pages. *Evidence:
anadohoi_projects.json `executors`; the 13 source-act PDFs in
anadohoi_cache. Affects: projects table (new column), /anadohoi,
project pages, tests (13/23/14 pins).*

## 2026-08-13 — Ανάδοχοι review correction: ΡΕΧΥ4653Π8-ΛΙΤ works_zones → all nine zones (the act's μελέτες table covers Ιστιαία Ι–ΙV too)

The 2026-08-12 works_zones entry mapped the ΔΕΔΔΗΕ studies project
(ΡΕΧΥ4653Π8-ΛΙΤ) to `limni_i..v` on the claim "the ΔΕΔΔΗΕ studies
covered all five Λίμνη basins" — but that claim was never excerpt-backed
(the stored `evidence.location` says only «…των καμένων εκτάσεων της
Βόρειας Εύβοιας»), and this review's read of the act PDF shows it is
wrong by omission: the act's own per-Δασαρχείο table (pages 2–3)
enumerates the funded μελέτες for ΔΑΣΑΡΧΕΙΟ ΛΙΜΝΗΣ across «ΛΕΚΑΝΗ ΛΙΜΝΗ
Ι» through «ΛΕΚΑΝΗ ΛΙΜΝΗ V» AND for ΔΑΣΑΡΧΕΙΟ ΙΣΤΙΑΙΑΣ across the
«υδρολογικής λεκάνης της Ιστιαίας I (ρέμα Ξηριά)» through «Ιστιαίας IV
(ρέμα Βασιλικών)» — i.e. all nine digitised zones. The project's own
curated `notes` already recorded the matching budget split
(«150.000€ … Δασαρχείου Λίμνης και 160.000€ … Δασαρχείου Ιστιαίας»), so
the limni-only zone list was internally inconsistent with the entry's
budget correction. Fixed: `works_zones` → all nine ids, and the field
now carries its own verbatim evidence (`evidence.works_zones` = the
budget-per-Δασαρχείο sentence that introduces the table,
whitespace-collapsed containment verified against the cached act text).
The committed sqlite row was updated in place (same reason as before:
harvest.json lives on the build machine). *Evidence: signed act PDF
ΡΕΧΥ4653Π8-ΛΙΤ (anadohoi_cache). Affects: 1 row (works_zones +
evidence_json), /anadohoi map dot + project-page ZoneMap for ΡΕΧΥ.*

## 2026-08-13 — EFFIS burn-scars raw layer: provenance recorded post-hoc (unwired, attribution required before display)

`data/raw/BurtScars_EFFIS_2008-2025.geojson` arrived in commit 1d7161e
("Track the … EFFIS burn-scars layer") with no decision entry; this
records what is measurable from the file itself. Contents (verified by
direct read 2026-08-13): 1,969 burnt-area features for Greece,
`initialdat` 2008–2025, Σ 723,328 ha, CRS **EPSG:3035** (LAEA Europe —
metres, must be reprojected before any d3/Leaflet use), `map_source`
sentinel2 1,387 / modis 512 / mixed 70, per-feature land-cover and
Natura-2000 percentages; the Β. Εύβοια 2021 event is present (5
features with admlvl3 «Εύβοια», Σ 52,670 ha). It is an export of the
Copernicus EMS **EFFIS** burnt-area product; the exact portal
query/download date were not recorded (fetched on the other build
machine) — noted honestly as unknown. NOTHING consumes the file yet
(zero code references). Constraints recorded for whoever wires it:
(1) display requires the attribution «© European Union, Copernicus
Emergency Management Service — EFFIS»; (2) the perimeters are
satellite rapid-mapping estimates (MODIS historically ≥30 ha), NOT
official οριοθετήσεις — never mix them with the ΦΕΚ fire units of the
arogi dataset without labelling the basis; (3) known hygiene: `country`
is «Ελλάδα\xa0» (NBSP) on all but one feature, one `area_ha` is 0, and
the filename typo «BurtScars» (sic) will propagate into references;
(4) at 20.3 MB it is the largest tracked blob in the repo. *Evidence:
the file itself; commit 1d7161e. Affects: no rows, no site output.*

## 2026-08-13 — evia_works_zones.geojson ships d3-geo (CW) winding, deviating from RFC 7946

Recording a deliberate deviation introduced by c2f3c0e: both copies of
`evia_works_zones.geojson` (data/processed + atlas/static/geo) emit
exterior rings CLOCKWISE (via shapely `orient(sign=-1.0)` in
build_evia_zones.py) because d3-geo interprets GeoJSON rings
spherically — a CCW exterior renders as the complement of the zone
(the original bug: ZoneMap fitted the whole sphere, ZonesLayer filled
the sea). RFC 7946 §3.1.6 mandates the opposite (CCW exteriors), so
any spherical GIS consumer (PostGIS geography, BigQuery GIS,
tippecanoe…) reading this published artifact must rewind first. The
committed convention is pinned by `test_exterior_rings_wind_clockwise`
(shoelace sign, added 2026-08-13) alongside a new pin that the two
copies stay byte-identical. *Evidence: build_evia_zones.py orient()
call; tests/test_evia_zones.py. Affects: no rows; documentation of an
existing artifact property.*

## 2026-08-13 — Ανάδοχοι: curated `work_sites` — exact work locations from the act texts (branch anadohoi-work-sites)

Design decision for θέση-level geolocation of the 69 sponsor projects.
**Universe**: every cached act txt per project — the ROOT act first, then
linked acts/amendments, which routinely carry finer or additional sites
than the root (ΨΜΙ6, amending ΨΖΟΟ, adds a second site «Κοκορέμι-
Μπρεκατσούλι» Δ. Ασπροπύργου in ANOTHER Π.Ε. — cross-Π.Ε. sites are
allowed with a note). Each site row: name, municipality, pe, stremmata
(where the act states one), `source_ada`, verbatim `excerpt`
(whitespace-collapsed containment mechanically verified against the
cached txt — the deliverables/executors discipline), lat/lon,
`geo_precision`, `geo_source`, optional note. **Precision vocabulary**:
site (named θέση/ρέμα/landmark pinned to a point) | locality
(οικισμός/Τ.Κ. centre) | municipality (δήμος centroid,
greek_municipalities.json) | zone (digitised Εύβοια works-zone centroid)
| pe (no coordinates stored; client falls back to the Π.Ε. centroid).
**Geocoding tiers**: Nominatim (Greek then transliterated query,
site-level) → manual web research for the residue (each pin carries
`geo_source: "web:<url>"`) → municipality centroid (offline) → none.
**Validation gates** — a pin ships only if it passes: stated-Π.Ε.
agreement (the geocode_loader `_acceptable` doctrine), ≤~15 km from the
stated municipality centroid when one exists, and for fire projects an
EFFIS burn-scar cross-check (inside or ≤~2 km of the matching-year scar
polygon; report-only for non-fire/plane-disease/regional projects —
first consumer of the 2026-08-13 EFFIS raw layer). Rather show nothing
than a wrong pin — unresolved θέσεις stay at municipality precision.
**Τμήμα/«Επιφάνεια N»/Υπολεκάνη names are recorded as names, not
polygons**: the acts themselves state the boundary «θα προσδιοριστεί
λεπτομερώς στο έδαφος» — a representative point inside the named area
with precision `site` is the honest maximum. Map presentation: one dot
per site (multi-site projects highlight together on hover), true
positions at country zoom, deterministic de-overlap spreading only past
the zoom threshold, approximate (municipality/pe) dots drawn in a
distinct dashed style. *Evidence: act txts in anadohoi_cache (tracked);
survey of all 69 root operative paragraphs 2026-08-13. Affects: new
`work_sites` column (30th), anadohoi_projects.json, /anadohoi map,
project pages.*

## 2026-08-13 — Ανάδοχοι work_sites: γεωεντοπισμός ολοκληρώθηκε — 100/105 θέσεις, EFFIS-ελεγμένες

Outcome of the same-day design entry. Extraction: 3 parallel readers over
all 69 act families proposed 112 sites; the mechanical gate (verbatim
excerpt ⊂ cached txt, canonical Π.Ε.) plus review dropped 7 (the 5
pe-null coarse «fronts» of ΡΕΧΥ-sibling 9ΕΘΠ — its 12 μελέτη-derived
sites cover them; «Καντήλι Βλυχάδα» which the act cites only as
fire-spread; the ΨΖΟΟ root-name duplicate — one θέση renamed by its
amendment, latest act adopted) → **58 projects / 105 curated sites**.
Geocoding: Nominatim tiers resolved 54 (with retries — the Greek-script
weakness and WRONG-NAMESAKE traps recurred: «Κτήμα Τατοΐου» hit a wedding
venue on οδό Τατοΐου, «Pentelikon» the Κηφισιά hotel, «Μονή Πεντέλης»
the Νταού monastery, «Πλατανάκι» the Ωρωπός stream 11.5 χλμ from the
2023 scar — ALL caught by the gates and repinned); web research with
per-pin source URLs resolved the toponym residue: Νέζης «Τοπωνυμικά της
Αττικής» (Μπύρζα = κορυφή Πύρεζα 897 μ. ΦΕΚ 35Δ/2010; the Πάρνηθα
ρέματα incl. the correct S-Parnitha Πλατανάκι), the Attica flood Master
Plan's own ΕΓΣΑ87 point for λεκάνη Κατσιμηδίου (= χ. Αγ. Αικατερίνης
Μάνδρας, distinct from the Parnitha peak), Diavgeia acts locating Αγ.
Παντελεήμονα Κρανιδίου via the sponsor's resort, OSM/Overpass for
landmarks, geonames/wiki for villages. Final: **58 site / 32 locality /
10 municipality-centroid pins**; the EFFIS burn-scar gate validates
82/92 fire-project pins inside-or-≤2 χλμ of the matching-year scar and
each of the 10 FAR has a recorded explanation (municipality centroids;
ΡΔΒΨ «Βίγλα» is a pre-existing αναδασωτέα the act itself says was NOT
burned in 2024; big-basin representatives; a 2021/2022 fire-label
artifact). **5 honestly unresolved** (no public coordinates exist):
Δαδιά «Ρέμα Λυγαριά/Χαμηλό», «Κακομάνδρι», «Καζάνι ρέμα» (confirmed
real via the Δασαρχείο Σουφλίου μελέτες and the WWF monitoring plan)
and Μάνδρα «Υπολεκάνες 2/8» (numbered only collectively). The committed
sqlite migrated in place (30th column). *Evidence: per-site `excerpt` +
`geo_source` in anadohoi_projects.json; scripts/geocode_work_sites.py
report. Affects: 58 rows, /anadohoi map (one dot per site, zoom-gated
spread, dashed approximate style), project-page SiteMap, tests
(58/105 pins).*

## 2026-08-13 — EFFIS burn scars wired to the /anadohoi fires map (display copy + attribution)

The raw EFFIS layer (provenance entry above) now has a display pipeline:
`scripts/build_effis_layer.py` simplifies each feature 120 m in the
source EPSG:3035, reprojects to WGS84, orients exterior rings CLOCKWISE
(d3-geo spherical winding — the c2f3c0e bug class), and keeps only
`yr` (from initialdat), `ha` (rounded area_ha) and `name`
(admlvl3/admlvl2, NBSP stripped) → 1,969 features, 1.1 MB, written to
data/processed/effis_fires.geojson and duplicated into
atlas/static/geo/ like the other map layers. Displayed on /anadohoi's
«PROJECTS AND FIRES THAT TRIGGERED THEM» map (lazy-loaded,
FiresLayer.svelte) coloured by year on a white→#6b2d35 gradient with a
2008→2025 scale; the required attribution «© European Union, Copernicus
Emergency Management Service — EFFIS» prints in the section caveat
together with the estimates-not-οριοθετήσεις warning. The per-fire
project cards (act-cited fires) moved beside the map unchanged — the
two fire vocabularies (EFFIS perimeters vs act-cited fire units) are
juxtaposed, never joined. *Evidence: the build script + output; the
section caveat. Affects: no rows; new derived artefact + /anadohoi.*
## 2026-08-13 — Fires map display window: 2018 onwards

The /anadohoi fires map now filters the EFFIS display layer to
`yr >= 2018` client-side (FIRES_FROM in the page; the built artefact
keeps the full 2008–2025 range for future use). The year gradient and
its 2018→2025 scale derive from the filtered set. *Affects: display
only.*

## 2026-08-13 — Ανάδοχοι review: το 9Ο0Λ ανήκει στην ΑΔΜΗΕ (6ΦΤΩ → completed)· το ΔΕΔΔΗΕ 9ΕΘΠ ολοκληρώθηκε με τις εγκρίσεις μελετών

Investigation of the 9ΕΘΠ4653Π8-ΠΡ4 trail (user review). The 2026
παραλαβή act 9Ο0Λ4653Π8-ΡΒΒ had been linked to BOTH 9ΕΘΠ (ΔΕΔΔΗΕ
μελέτες) and 6ΦΤΩ (ΑΔΜΗΕ works) by the citation crawl — its recitals
cite 641Ξ (the μελέτη ΔΕΔΔΗΕ funded) but the act itself approves the
οριστική παραλαβή of the WORKS financed by the ΑΔΜΗΕ Πράξη (recital 18
names 6ΦΤΩ; σύμβαση ΔΕΑ-42369-2024 ΦΙΛΑΝΤΑΡΑΚΗ + 3Κ ΤΕΧΝΙΚΗ; ΑΔΜΗΕ's
παραλαβή committee). It never cites 9ΕΘΠ. User ruling: (1) REMOVE 9Ο0Λ
from 9ΕΘΠ's trail — chain contamination through the shared μελέτη act;
the relay is ΔΕΔΔΗΕ funds the μελέτη (9ΕΘΠ) → ΑΔΜΗΕ funds the works
per that μελέτη (6ΦΤΩ) → 9Ο0Λ closes ΑΔΜΗΕ's works. (2) 6ΦΤΩ becomes
**completed** with 9Ο0Λ as its completion act, end date = the protocol
date 2025-10-07 («το από 7-10-2025 πρωτόκολλο οριστικής παραλαβής» —
the Anti-nero protocol-date convention), not the act date 30-03-2026.
(3) 9ΕΘΠ is **completed** too: its deliverable is the μελέτες
(deliverables=study) and they were delivered — the three approvals
641Ξ/6ΛΡΨ/ΡΨΗΡ; the LAST approval (ΡΨΗΡ, 2024-07-03) becomes the
completion act, the earlier two stay as study_approval trail entries
(641Ξ/6ΛΡΨ relations tidied other→study_approval). Recorded caveat:
the root act's σκοπός names five fronts and approvals were found for
three μελέτες (two Δυτ. Αττικής + Διακοπτό) — the user rules the work
done as delivered. Budget note from the same investigation: the €500k
is the μελέτες-funding envelope; the €1.53M/€1.10M/€1.40M inside the
approval PDFs are the designed WORKS' estimated cost — never amendments
(budget_current stays 500,000). Side findings recorded for future
ingestion: the Διακοπτό works run as a PUBLIC ν.4412 δασοτεχνικό έργο
(Σύμβαση Κατασκευής 76921/26-2-2025 — outside the sponsor universe, so
correctly absent); Πράξη Ε3ΣΨ4653Π8-2ΣΚ (Τρ. Πειραιώς, Δασαρχείο
Αιγάλεω, 06-08-2026) postdates the harvest and awaits ingestion.
sqlite migrated in place (same reason as before). *Evidence: act PDFs
9ΕΘΠ/641Ξ/6ΛΡΨ/ΡΨΗΡ/9Ο0Λ (anadohoi_cache), ΛΛΒ14653Π8-ΑΦΑ (Diavgeia).
Affects: 2 rows (status/completed_*), project_decisions relations,
status counts 14→16 completed, tests.*

## 2026-08-13 — Ανάδοχοι trail sweep: 4 σύνδεσμοι-μολύνσεις αφαιρούνται· ΨΤΑΤ → study_and_works (τα έργα εκτελούνται από τη ΣΤΑΝΤΑ)

Full-trail sanity sweep after the 9Ο0Λ case (148 linked acts checked;
double-links and root-citation absences read in the act texts). Three
9Ο0Λ-class mislinks REMOVED: (1) 6ΡΤΣ (EREN, Λίμνη Ι) ← 9Ε47ΟΡ10-ΛΧΞ —
the παραλαβή-committee act names ΔΕΗ as Ανάδοχο and covers only λεκάνες
23.27.06/23.27.02 (Λίμνη ΙΙ/V), zero EREN/Λίμνη Ι mention; stays on
9Κ9Τ + ΩΞΕΦ. (2) 964Ρ (Εθνική, Χίος) ← Ε2284653Π8-ΗΗΜ — Πράσινο Ταμείο
credit allocation to Δ/νση Δασών Χίου, never cites the sponsor (its
«Εθνική» hits are law titles); recorded as the Χίος instance of the
Διακοπτό relay (sponsor μελέτη → state-funded works) but not the
sponsor's lifecycle. (3) ΨΒ8Λ (ΔΕΠΑ Άβαντας) ← Ψ4ΟΥ + Ψ0ΓΕ — the
Παλαγία «Λεκάνη Ι» μελέτη and its τροποποίηση, zero Άβαντας mention;
they belong to sibling 6ΨΓΗ only (Άβαντας keeps its own 6ΙΓΥ; the
plural-«των έργων» committee ΨΗ9Κ correctly stays on both). Genuinely
shared double-links KEPT: the 6ΓΨΨ plane-timber specs on the three
plane-disease projects; the five Κρυονέρι-Δροσοπηγή acts on ΤΙΤΑΝ +
Κανελλοπούλου (one έργο, two sponsors). **ΨΤΑΤ deliverables study →
study_and_works** (split 42/17/10 → 42/18/9): its ~30 works-
administration acts are ΣΤΑΝΤΑ's own — 9ΣΙΜ/ΡΚΘ4 recite the Ρ6Χ5
τροποποίηση «ορίζεται ως ανάδοχος η εταιρεία … ΣΤΑΝΤΑ» and ΣΤΑΝΤΑ's
σύμβαση with Δασολόγο-Εργολήπτη for «Υλοποίηση εργασιών αναδάσωσης στη
θέση Μύλος ρέμα» (ημερολόγια, 3 επιμετρήσεις/παραλαβές αφανών,
κατασκευαστικά σχέδια). This supersedes the 2026-08-12 «υλοποίηση
μελέτης = study» verdict FOR THIS PROJECT on trail evidence — the
convention stands for ΡΛ16/9Φ9Ρ, whose trails show no works. Status
stays active (interim παραλαβές only). sqlite migrated in place.
*Evidence: act txts 9Ε47ΟΡ10-ΛΧΞ, Ε228, Ψ4ΟΥ, Ψ0ΓΕ, 9ΣΙΜ, ΡΚΘ4
(anadohoi_cache). Affects: 4 project_decisions rows, 1 deliverables
value, tests (42/18/9 pin).*

## 2026-08-13 — Ανάδοχοι: `effis_scars` — κάθε project συνδέεται με το αποτύπωμα EFFIS της πυρκαγιάς του

Linkage semantics (derived mechanically, review-gated before landing):
a project links the EFFIS scar feature(s) of its fire-event YEAR that
CONTAIN or lie ≤2 χλμ from any of its anchors — the coordinated
work_sites, plus the digitised zone centroids for the Εύβοια zone
projects. Anchor-less regional projects link by scar admin-name + year
from a hand-reviewed table (Χίος 2025, Ρόδος 2023, Β. Εύβοια 2021,
Έβρος 2023). «Εκτός πυρκαγιάς» (plane-disease/sanitation) projects link
nothing; two-year labels («Αττική 2021–2022») try both years; a project
with no matching scar stays honestly empty (EFFIS historically maps
≥~30 ha — small fires are absent). Each link stores {id (the EFFIS
feature id, now emitted into the display layer by
build_effis_layer.py), yr, ha, name, basis contains|near|region-year,
km}. Multi-scar links are expected (multi-front projects). Display: the
project page's SiteMap/ZoneMap draw the linked scar under the
pins/zones with the mandatory attribution «© European Union, Copernicus
Emergency Management Service — EFFIS» and the estimates-not-οριοθετήσεις
caveat; scar-only maps appear for regional projects that had no map.
Loader schema 31 cols; committed sqlite migrated in place (harvest.json
on the build machine). *Evidence: scripts/link_effis_scars.py report;
per-link basis/km in anadohoi_projects.json. Affects: new column,
project pages, tests.*

## 2026-08-13 — Audit: how far the corpus itself proves «RRF Action 16849» membership

Question asked of the dataset: can every live in-scope contract (251)
be tied to RRF Action 16849 from primary evidence in this repo? Sweep
of all cached contract texts (251/251 have a .txt) + registry metadata:
**243/251** carry one of the three Ταμείο-Ανάκαμψης ΠΔΕ codes
(2022ΤΑ07500000 / 2021ΤΑ07500002 / 2023ΤΑ07500012) in the structured
KHMDHS funding field; of the 8 without, one (25SYMV017106210,
Ξυλόκαστρο restoration) prints 16849 + ΟΠΣ 5201358 + the ΤΑ code in its
PDF, and **7 are 2022 Anti-nero II lots/amendments whose PDFs appear to
be textless scans and whose funding metadata is empty — their in-scope
status rests on the «ΤΟΥ ANTINERO ΙΙ» title branding alone**. In PDF
prose: 215/251 print ΤΑ/ΟΠΣ/RRF markers, 36 print the literal «16849»
(all 8 ΕΣΑ, 3 restoration, and execution contracts under BOTH later
fund codes — so ΟΠΣ 5201358 and 5222791 are each bridged to Action
16849 by contract text inside the corpus). **Honest gap: no Anti-nero I
contract (ΟΠΣ 5161079) prints 16849** — that phase's link to the RRF
measure rests on programme-level documentation outside the corpus, not
on any stored primary source. Site copy should therefore say the
programme is RRF Action 16849 (true at programme level) but must not
claim per-contract documentary proof. Homoglyph lesson re-learned: the
audit's first fund-code counts disagreed between runs because typed
«ΤΑ» literals mixed Greek/Latin — final numbers use
khmdhs.scope.FUND_* constants. *Evidence: pdf_cache .txt sidecars,
contracts.public_funding_ref_num, contract_scope.basis. Affects: no
rows.*
## 2026-08-13 — Backing the Anti-nero I → Δράση 16849 link: two primary sources located

Follow-up to the same-day 16849 audit. The phase-I gap is now bridged
by documents (two hops, each on a primary source): **(A)** ΕΥΣΤΑ/ΥΠΟΙΚ
decision **ΡΚΥΕΗ-Ζ9Π** (29.07.2026, τροποποίηση αποφάσεων ένταξης ΣΑΤΑ
075) lists row 45: «5161079 | Υποέργο 1: Εθνικό Σχέδιο Αναδάσωσης -
Σχέδιο Προστασίας Δασών | 2022ΤΑ07500000» — the Anti-nero I ΟΠΣ and
ΠΔΕ code ARE the Υποέργο-1 of the «Εθνικό Σχέδιο Αναδάσωσης» umbrella.
**(B)** Απόφαση Ένταξης **ΨΛ9ΧΗ-ΞΟΒ** (33592 ΕΞ 2023, 02.03.2023)
enters «SUB1. ΕΘΝΙΚΟ ΣΧΕΔΙΟ ΑΝΑΔΑΣΩΣΗΣ» (ΟΠΣ ΤΑ 5201358) into «τη
Δράση με ID 16849», and the corpus's own contracts spell the Δράση
name+ID («Το Έργο περιλαμβάνεται στη Δράση με ID 16849: "Εθνικό σχέδιο
αναδάσωσης – Πρόγραμμα Προστασίας Δασών (Antinero II)"» —
24SYMV014843550; 23SYMV013600200 cites ΨΛ9ΧΗ-ΞΟΒ itself). Residual
honesty: the ORIGINAL ένταξη of 5161079 naming 16849 verbatim was not
located (Diavgeia subject search only reaches metadata); the link for
phase I therefore rests on the Δράση-title identity across (A) and
(B). The 7 title-only 2022 ANTINERO II lots remain a separate gap —
their PDFs are textless scans; OCR is the closure path. *Evidence: the
two ΑΔΑs (permanently citable on Diavgeia) + pdf_cache texts. Affects:
no rows.*

## 2026-08-13 — Fires map: baked shaded-relief base (Copernicus GLO-30, Python shade pipeline)

Decision to give the /anadohoi fires map a shaded-relief base as a
BAKED static image, not a runtime renderer. Research basis: every
newsroom precedent pre-renders (the Berkeley journalism Blender
pipeline; Stamen's survey names "pre-rendering shadows for limited
areas as overlay images" as the working practice; Lavergne's Corsica
reference is itself Blender+Photoshop offline); runtime three.js
(~155 KB gz) / maplibre-gl (~290 KB gz, replaces PaperMap) / deck.gl
were evaluated and rejected on bundle, doctrine (d3-only, self-hosted)
and look ceiling. Shading engine: pure-Python first — the controlled
study «That's a Relief» (Cartographic Perspectives) found
multidirectional relief statistically indistinguishable from ray-traced
Blender on beauty/realism and BETTER on landform clarity, and Huffman's
«Towards Less Blender-y Relief» prescribes suppressing exactly the
Blender drama when relief sits under heavy vector overlay (our maroon
scars at 0.85 opacity). The shade step is pluggable; a headless-Blender
upgrade replaces one function if ever wanted. Pipeline
(scripts/build_relief.py, system python3): Copernicus GLO-30 COGs read
keyless over /vsicurl at overview level → mosaic (cache gitignored) →
warp to EPSG:3857 grids EXACTLY matching the d3 frame (d3 geoMercator ≡
EPSG:3857 up to an affine — frame.json emitted by build-topo.mjs from
the same fitSize call, so alignment is arithmetic, zero warp) →
Patterson resolution-bumping (~85% smoothed / 15% original) → vendored
RVT multidirectional hillshade + sky-view-factor AO term + texture
shading → Huffman composite (shadows Linear-Burn / highlights Screen)
→ newsprint tint (#f9f6ec→#f3ecdb) with contrast capped ≈0.55 so the
scars stay dominant → AVIF ×2 (relief.avif 1280×1240 always-loaded +
relief_hi.avif 2560×2480 on the existing k≥2 hires trigger, never on
narrow; ≤8 MP per image — iOS Safari decode caps). Mandatory
attribution printed with the map: «Relief: produced using Copernicus
WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH
2014-2018 provided under COPERNICUS by the European Union and ESA; all
rights reserved»; vendored rvt_vis keeps its Apache-2.0 notice; the
raw DEM is NEVER committed (fetched at build time, cache gitignored).
*Evidence: the research report (links in the plan file); measured AVIF
sizes. Affects: new derived artifacts atlas/static/geo/relief*.avif,
PaperMap relief prop, fires map only.*

## 2026-08-13 — Fires-map relief: aesthetic pivot to the reference look (cast shadows, blue sea)

User review of the first newsprint-calm bake: «doesn't look 3d enough,
no shadows, a bit blurry» against the Lavergne Corsica reference. The
calmer-under-overlay doctrine of the previous entry is OVERRIDDEN for
this map by the user's aesthetic ruling. The bake gained the three
missing ingredients, still pure-Python (no Blender needed): (1) TRUE
CAST SHADOWS — a horizon-scan along the light ray (rotate grid so light
comes from the left, per-row descending ray-height sweep) averaged over
five sun altitudes (20–36°) for a soft penumbra; sea is elevation 0 so
mountain shadows spill across the water like a physical model — the
reference's key 3D cue; (2) crisper detail — generalization reduced
(σ 1.1, 40% original detail), VE 3.2, stronger directional weighting
(von-Mises 2.4 around WNW 300°), AVIF q68; (3) the reference duotone —
sculpted white land with cool blue-grey shadows (#7b8696) on soft blue
water (#bbcfdb), replacing the earlier «sea bakes white» rule; under
the multiply mount the blue sea now tints the map's sea area (the
maroon scars stay the loudest layer above). Assets: relief.avif 225 KB
/ relief_hi.avif 798 KB — inside the test budgets. Blender remains the
documented upgrade path but was not needed. *Evidence: the reference
image; iteration previews in relief_cache. Affects:
atlas/static/geo/relief*.avif, look only.*

## 2026-08-13 — Fires-map relief: σκιές βαθύτερες + ανάλογες του υψομέτρου (user ruling)

Second look ruling: shadows darker and PROPORTIONAL to the caster's
elevation. Implemented: the horizon sweep now tracks WHICH peak owns
the shadow ray and weights its shadow by that peak's height
(CAST_H_FLOOR 0.30 → a sea-level caster shades at 30% weight, the
p97-elevation caster at 100%). Two chain bugs surfaced by the
diagnostic: (1) the slope remap HARD-clipped ~5% of land at the dark
floor, flattening every deep shadow into one tone — replaced with soft
compression into [floor, 1]; (2) the cast shadows were geometrically
honest and therefore near-invisible at ~900 m/px (max intensity 0.18,
p99 0.001 — at 20° the ray decays 325 m per pixel, Όλυμπος shadows a
dozen pixels) — the reference look REQUIRES exaggeration, now explicit:
CAST_VE 5.0, sun altitudes 10–26°, depth saturating at 400 m. After:
cast max 1.0 / p99 0.80, final deep-shadow luminance ~0.11. Assets
209/726 KB, inside budget. *Evidence: the diagnostic percentiles above;
previews in relief_cache. Affects: relief*.avif, look only.*

## 2026-08-13 — Fires-map relief: τελικός γύρος — κοντύτερες, πιο σκούρες σκιές, ουδέτερη θάλασσα

Third look ruling: shadows too elongated (Πίνδος), wants them shorter
AND darker, and the blue water replaced by the paper grey of the other
maps. Applied: sun altitudes 16–36° + CAST_VE 3.8 (shorter throws);
sea bakes pure white again — the paper shows through the multiply
mount, cast shadows still grey the water they cross; darkness came in
two steps because the first (SHADOW_STRENGTH 3.6, CAST_DARK 0.85,
DARK_FLOOR 0.18) barely moved the histogram — the REAL ceiling was the
tint ramp's anchor colour: no shadow can be darker than SHADOW_RGB.
Anchor deepened to charcoal #42444a → darkest pixels 116→73/255.
Asset sizes 312 KB / 1.07 MB (richer gradients carry more entropy);
test budgets raised to 400 KB / 1.2 MB — the hi level only loads on
desktop past the k≥2 zoom. *Evidence: preview histograms in the
session log; relief_cache previews. Affects: relief*.avif, test
budget, look only.*

## 2026-08-13 — Fires-map relief: geoblender-velvet τόνος + καθαρές ακτογραμμές

Fourth look ruling (reference: the geoblender tutorial render): smoother
grey-to-shadow gradation, NO pure white on land, and the coastline
artifacts debugged. Tonal: land luminance capped at HIGH_CAP 0.90 with
a gamma-1.4 roll-off (midtones melt into the shadows), slope strength
eased to 2.4, final 0.5 px soften — the sea stays baked white
(paper-neutral under the multiply mount, per the earlier ruling).
Coastline debug — two artifact classes found in the 1:1 crops:
isolated grey specks in open sea (Lanczos ringing + sub-pixel islets
resampled into fake micro-islands) and a stippled fringe hugging every
coast (sub-metre partial-land pixels shaded by AO). Fixes: bilinear
warp (no overshoot) + negatives clamped, sea threshold at 1 m, land
components < 8 px dropped (≈1.6 km² at the hi grid — no real inhabited
islet lost), texture shading neutralized over sea (the land/sea step
rings in the FFT). Verified on the same Κυκλάδες crop: specks and
fringe gone. Assets 180/646 KB — back well inside budget. *Evidence:
before/after crops in relief_cache. Affects: relief*.avif, look only.*

## 2026-08-13 — Fires-map relief: ενιαία γκρίζα πλάκα + φωτιστική κλίση ήλιου (3D-render πλάκα)

Fifth look ruling (geoblender reference, second pass): flats brought TO
the background grey, no hard whites anywhere, and the user's idea —
light the whole plate directionally like a render — implemented as an
analytic sun gradient (±4.5% along the SUN_AZ axis, NW corner
brightest), applied to land AND sea. The sea is no longer paper-white:
it IS the background plate at BG_BASE 0.885 through the same
charcoal→white ramp (this supersedes the paper-neutral ruling — the
fires map sea now reads as a lit grey plate under the multiply mount,
deliberately different from the other maps). Land flats cap at
HIGH_CAP 0.88, just under the plate. A soft contact shadow
(CONTACT_AMP 6%, 5 px falloff) hugs every coastline so the landmass
reads as a physical plate on the water. Cast shadows continue to grey
the sea they cross. *Evidence: previews in relief_cache vs the
geoblender reference. Affects: relief*.avif, look only.*

## 2026-08-13 — Fires-map relief: το κενό/ραφή στη δυτική άκρη διορθώθηκε (plate mount αντί multiply)

User screenshot: a vertical strip of a DIFFERENT grey west of the
relief — the hand-tuned fires frame (k=1.08, centred east) exposes
~19 px of the map's warm paper background beyond the image's west
edge. Root cause: the multiply mount made the surround (paper) and the
covered sea (paper × plate) mathematically different tones, so no
background colour could match both. Fix is structural: the relief now
renders with NORMAL blending UNDER the Π.Ε. polygons (their fills turn
`transparent` when relief is on — hit-testing and the stroke-based
hover/focus highlights are unaffected), and the map surround switches
to the SAME plate gradient the bake applies (css linear-gradient
#f1f1f1→#e2e2e3 at 110°, computed from the bake's SHADOW_RGB/BG_BASE/
GRAD_AMP/SUN_AZ — the css comment pins the coupling). Image edge and
surround now continue each other within ~1/255. *Affects:
PaperMap.svelte relief mount only; other maps (no relief prop)
unchanged.*

## 2026-08-13 — Fires-map relief: root cause του λευκού καλύμματος — page-level CSS override

Addendum to the plate-mount entry: after the structural fix the
polygons STILL painted white over the relief and the strip persisted.
Playwright screenshot + computed-style inspection of the live page
found the culprit outside PaperMap: the /anadohoi redesign's own
`.map-wrap :global(.region) { fill: #fff }` and
`.map-wrap :global(.map) { background: #f2f2f2 }` — page CSS beats the
`fill` presentation attribute, so the component-level `transparent`
never applied. Fixed by scoping the page overrides to
`.map:not(.plate)` (the white-land design stays on the status map) and
letting `.map.plate` keep transparent fills + the plate gradient.
Verified live: computed region fill rgba(0,0,0,0), background the
plate gradient, screenshot clean. Also: a stray atlas/DATA_DECISIONS.md
created by a wrong-cwd append was merged back here and removed.
*Affects: anadohoi page CSS only.*

## 2026-08-13 — Fires-map relief: υφή αποστράγγισης στα πεδινά + film grain

Sixth look round (user request, from my own suggestion list): (1) the
texture shading now applies with a FLATNESS-weighted strength — base
0.28 plus up to 0.22 extra where the multidirectional shade sits near
its flat-ground value — so the drainage etching the geoblender
reference shows in its lowlands appears exactly there (Θεσσαλία crop
verified; flats read as toned, textured ground instead of dead grey);
(2) deterministic film grain (σ 0.011, seed 16849) over the whole
plate — the render-sensor noise of the reference, reproducible bake.
Assets 198 KB / 1.28 MB — inside budget. *Evidence: crop_thessaly2 in
relief_cache. Affects: relief*.avif, look only.*

## 2026-08-13 — Fires-map relief: toggle ΓΚΡΙ/ΥΨΟΜΕΤΡΙΚΟ (δεύτερο baked style)

User request: a toggle between the greyscale relief and an elevation
colourmap. One shading pass now emits TWO stylings (4 assets):
relief*.avif (greyscale) + relief_hypso*.avif (hypsometric tints on
the same grey plate — the toggle only recolours land). Palette
iterations: first the atlas-classic ramp (guessed, replaced), then the
Gąsiewska-Holc «Between Forests and Shores» legend sampled from the
image (too dark as raw legend colours — its RENDER washes them, so a
wash-toward-neutral was fitted), finally superseded by the user's
second reference (Bosnia physical-3D map): brighter, saturated DISPLAY
tones sampled directly (mint #a9c2a0 lowlands → cream → rust #7a4227
peaks, HYPSO_STOPS, no wash) with a 0.6 shading-gamma lift — Greece is
mostly slopes, the flat-country references read lighter than an
honestly-shaded Greece would. Frontend: GREYSCALE/ELEVATION pill on
the fires map, elevation legend bar (css gradient tracks HYPSO_STOPS)
with 0–2.900 μ labels shown in elevation mode; PaperMap just receives
a different {lo,hi} pair — the k≥2/narrow gating is unchanged. Bake
robustness note: two knob-cluster edit regressions (NameError) slipped
through because the bake's exit code was masked by a tail pipe — the
runner now prints BAKE EXIT and a function smoke-test precedes long
bakes. Budget test covers all four assets (196 KB–1.28 MB). *Evidence:
previews + live toggles in the session log. Affects: new
relief_hypso*.avif, fires-map UI, look only.*

## 2026-08-13 — /anadohoi status map: EFFIS scars overlaid όπως στον fires map

User request: the «CURRENT STATUS OF PROJECTS» map now draws the same
EFFIS burnt-area layer as the fires map — identical FiresLayer (year
gradient into #6b2d35, 2018+ display window, same tooltip) rendered
UNDER the zones/dots so the project dots stay the loudest layer, plus
the same vertical year scale beside the map (shared fireYears
derived). One layout addition: `.statusgrid .mapscale .map-wrap`
flex:1 so the map keeps its full column width next to the scale.
The EFFIS attribution already prints in the section caveats. *Affects:
anadohoi page markup/CSS only.*

## 2026-08-13 — Correction: the 7 title-only ANTINERO II contracts are NOT textless scans

The same-day 16849 audit mischaracterised the 7 evidence-thin 2022
ANTINERO II rows as «textless scans» — that was an inference from the
absence of funding MARKERS, never verified against the texts. Wrong:
all 7 cached .txt files carry full text (the two originals ~130k chars
each incl. annexes; the five amendments 5–7k). What is true: their
BODIES contain zero programme finance language — no Ταμείο Ανάκαμψης,
no Δράση/16849, no ΠΔΕ/ΟΠΣ code, and no «ANTINERO» either (the word
lives only in the registry title metadata). The originals are
ΤΑΙΠΕΔ-run procurements (02.08.2022 Πρόσκληση, ΤΑΙΠΕΔ Επιτροπή
Αξιολόγησης/κατακύρωση) funded via the ΥΠΕΝ budget line ΚΑΕ 2910601001
(ΥΠΟΙΚ απόφαση 06.05.2022); their ΑΑΥ recital names the project
«Σχέδιο Δασικής Προστασίας — Μελετοκατασκευή 2η», echoing the Δράση
16849 / Υποέργο-1 titling («Σχέδιο/Πρόγραμμα Προστασίας Δασών») at
name level. The five amendments are winter work-suspension deeds
(αναστολή εκτέλεσης εργασιών, Dec 2022–Jan 2023) with no funding
language at all. *Evidence: the 7 pdf_cache .txt files. Affects: no
rows; corrects the audit entry above.*

## 2026-08-13 — The 7 unproven ANTINERO II chains leave the analytics basis (`antinero_probable`)

User decision after manually reviewing the 7 evidence-thin contracts and
the full-text comparison above: since RRF-16849 membership cannot be
proven from primary documents, they must NOT be counted in calculations
or visualisations — they stay in the dataset presented as «additional
contracts found, probably related to the Antinero programme, but not
included in the calculations».

The exclusion applies to the whole chains — 7 chain tips
(22SYMV011360183, 22SYMV011593395, 22SYMV011928850, 22SYMV011928864,
22SYMV011928896, 22SYMV011928919, 23SYMV011953055) plus their 6
superseded members (22SYMV011332276, 22SYMV011332546, 22SYMV011332552,
22SYMV011512210, 22SYMV011632177, 22SYMV011470180 — the ΕΡΓΟ 2Β chain
is original + 1η + 2η τροποποίηση) — 13 stored
contracts, every one with EMPTY fund metadata and bodies free of any
programme-finance language (see the two entries above). 16 completion
acts on these chains prove the works were executed and delivered under
ΥΠΕΝ — but execution is not financing evidence.

Mechanism: new curated file `khmdhs/data/probable_related.json` (13
ADAMs, reason + evidence per chain) → `scope_loader` demote pass (runs
AFTER rule classification and amendment inheritance): scope becomes
`antinero_probable`, basis `curated:probable_related`. The value is NOT
in `scope.IN_SCOPE`, so every aggregate (webui and Atlas both filter
`in_scope = 1`) drops the chains automatically; detail pages stay
reachable, regions/forest links stay stored. The supplement file keeps
its `antinero_ii` phase claims for the members it lists — the phase
claim (registry title) and the analytics-basis decision are different
statements.

Effect on the basis: in-scope 252 → 245 contracts; stated net
€667,496,652.26 → €658,297,730.65 (−€9,198,921.61); the frozen webui's
historical effective-gross headline recomputes on the same flags to
€604,543,493.99. No payments are
affected — zero payment orders exist anywhere on these 7 chains (checked
2026-08-13), which also means the paid-net figures do not move. 5
contract_study_costs rows and the 16 completion acts leave the
aggregates together with their contracts (both layers attribute to
in-scope tips). The Atlas front page carries a computed note with the
user's wording + the 7 tips listed; /methodology documents the tier.
*Evidence: pdf_cache texts of all 13 + the audit entries above.
Affected: 13 contract_scope rows, every headline aggregate.*

## 2026-08-13 — /dase map: proportional symbols per awarding unit + EFFIS underlay

Display decision. The Atlas /dase Π.Ε. choropleth (Σ stated € per region)
hid the dataset's central contrast — few huge fire-salvage contracts
(Ιστιαίας/Λίμνης/Δωδεκανήσου/Πύργου) versus hundreds of small routine
υλοτομικά in the northern heartland (Νευροκοπίου, Ξάνθης). Replaced by a
proportional-symbol map: one circle per awarding forest unit at its
registry seat (join key: `dase_contract_regions.source =
'registry:<canonical name>'` → khmdhs `forest_authorities` lat/lon),
circle AREA = Σ stated net €, printed number = contract count, tooltip
adds the median. Contracts awarded by non-forest bodies (δήμοι,
περιφέρειες, ministries — source curated/override) have no unit seat and
aggregate per Π.Ε. at its centroid as dashed circles; the 4 multi-Π.Ε.
ΑΔΜΗΕ contracts stay off-map in the caveat. The payload
(`/api/dase/map`: 48 units + 21 Π.Ε. groups + unresolved) reconciles
exactly to the €34,085,266.14 basis (pinned). Circles are coloured by
unit kind from the site's green palette (Δασαρχεία = the page green,
Διευθύνσεις Δασών = the works-ramp dark, non-forest awarders = its
palest step, dashed); clicking a circle docks the unit's full contract
list right of the map (lists shipped in the payload, every list length
== n, pinned), clicking a Π.Ε. polygon zooms to it; dot/size/fire
explanations live in a timeline-style legend strip above the map.
Underneath, the EFFIS
burn-scar layer (display copy, DATA_DECISIONS 2026-08-13 above) filtered
to fire years ≥2021 — the dataset starts Sept 2021 and salvage logging
follows those burns — with the mandatory «© European Union, Copernicus
Emergency Management Service — EFFIS» attribution and the
estimates-not-οριοθετήσεις caveat on the frame. webui's /dase choropleth
is frozen and unchanged. *Affects: presentation only; no rows.*

## 2026-08-13 — /dase map legend per user mock (supersedes the colour/legend details above)

Same-day refinement of the entry above, per the user's legend mock: kind
colours are now Διευθύνσεις Δασών «forest directorate» #406e55 (works-ramp
dark), Δασαρχεία «local forest service office» #6fb28c (works-ramp
light), municipal/regional & other non-forest awarders SOLID BLACK
(dashed retired); count labels may appear on any kind's circle when it
is large enough. The legend left the strip above the map and is now a
grey rounded panel DOCKED RIGHT of the map, top-aligned: «contracts
awarded by» dot key, nested-circle size icon («circle size represents
the amount of € awarded via the contracts», «x: number of contracts»),
and a «burnt areas» white→#6b2d35 gradient bar labelled with the
computed fire-year span. The clicked unit's contract list docks below
the legend in the same column. *Affects: presentation only.*

## 2026-08-14 — Contract pages: the ΚΗΜΔΗΣ family as a staged tree diagram

The /dase contract page's flat procurement-timeline list hid the shape
of multi-award procedures (e.g. 21SYMV009374147: one πρόσκληση of
Δασαρχείο Λίμνης split among 8 co-ops). A FamilyTree diagram now renders
above the table (which stays as the accessible/tabular view): funding
acts → πρόσκληση as a trunk, κατακυρώσεις fanned below, συμβάσεις under
them, the viewed contract's trail in the dataset green with its payment
orders as the terminal node; every box opens its act (PDF proxy /
sibling contract pages). HONESTY RULE: an award connects to a contract
ONLY when the award title names that contract's contractor
(fold-contains, legal-form prefixes stripped, unique hit required) —
never paired by order; ambiguous/inflected names stay unpaired with no
edge (2 of 8 in the reference family). `contract_timeline` now ships
`who` (first contractor) for in-db contract rows so siblings are
labelled by their co-op and matched by name. The caveat text states the
rule; family provenance remains the registry's declared adamChain links.
*Affects: presentation + one additive API field.*

## 2026-08-14 — ΔΑΣΕ contract stated values corrected from signed PDFs

ΔΑΣΕ registry stated values are corrected ONLY when the signed contract
PDF documents a different figure; corrections live in
`khmdhs/data/dase_contract_corrections.json` with the source cited,
applied by `khmdhs/contract_corrections.py` (standalone CLI and at the
end of every `harvest_dase.py load`, whose INSERT OR REPLACE would
restore registry values); corrected rows carry `contracts.correction_note`.
- `21SYMV009374147`: registry net €2,537,393.13 / gross €3,146,367.48 →
  **€253,739.13 / €314,636.52** (signed contract PDF
  `contract/attachment/21SYMV009374147` states «253.739,13» + ΦΠΑ =
  «314.636,52»; ×10-scale digit-glitch keying error — all 7 sibling lots
  of the Δασαρχείο Λίμνης πρόσκληση 21PROC009329287 carry exactly
  €253,739.13 net, and its own payment orders total €313,316.42 gross
  (€252,674.53 net) ≈ full settlement). Its `contract_objects` seq 0
  repeated the wrong net and is corrected too.
A sibling-modal guard test fails when any live uncorrected contract sits
at ≈×10/×100 of its ≥3-sibling family's modal lot price;
`scripts/validate_contract_values.py` screens every contract whose PDF
text is extractable (the full ΔΑΣΕ PDF/txt cache
`data/processed/dase_pdf_cache/` is fetched with
`scripts/fetch_contract_pdfs.py`; .txt sidecars tracked per the user's
2026-08-14 decision). Before this sweep only 892/2,164 contracts had any
cross-check (payments); the remaining 1,272 (1,127 live) had none.
New basis: live population 2,018 rows / **€38,587,233.00 gross =
€31,801,612.14 net**. *Affects: 1 contracts row + 1 contract_objects
row; every ΔΑΣΕ aggregate.*

## 2026-08-14 — Full ΔΑΣΕ PDF sweep: every stated value screened, no further live-basis errors

All 2,164 ΔΑΣΕ contract PDFs fetched into `data/processed/dase_pdf_cache/`
(`scripts/fetch_contract_pdfs.py`; 0 missing, 0 unreadable — every PDF
yielded text) and swept by `scripts/validate_contract_values.py`.
Detector precision rules (first pass produced 161 false suspects): the
implied true value must be ≥ €500, probe hits must match exactly (the
`tolerant` method false-hits tiny amounts), and payments within 10% of
the stored gross corroborate the registry figure. Final statuses:
586 ok · 89 ok_net_only · 89 near_match · 1 ok_corrected (the flagship) ·
1,390 mismatch (συμφωνητικά print per-συστάδα component tables, not one
total — the stored value is their sum) · 9 decimal_shift_suspect, all
human-reviewed:
- 8 false positives: stored = exact sum of the PDF's section totals
  (e.g. 5.748,26 + 8.319,78 = 14.068,04) with a coincidental VAT line
  item near ratio 10.
- `22SYMV011512410` (Δασαρχείο Σταυρού καυσόξυλα): a REAL ×100 keying
  error (registry €1,199,702.00 net; PDF «11.997,02») — but the registry
  corrected itself: superseded the same day by `22SYMV011512413` with the
  correct €11,997.02 (verified in its PDF). The live dedup already
  excludes the wrong original; no curated correction needed — superseded
  originals keep their registry values by convention.
Conclusion: after the 21SYMV009374147 correction, NO live ΔΑΣΕ contract
carries a detectable decimal-shift error. Screening coverage is now
universal at the text level (previously 892/2,164 payment-screened).
*Affects: no rows; report `data/processed/contract_value_report.json`
(gitignored), .txt corpus tracked.*

## 2026-08-14 — ΔΑΣΕ display-name curation started (convention + tooling)

The 250 canonical co-ops appear under 638 registry spellings; the user is
curating uniform display names with the convention **ΔΑ.Σ.Ε. 'ΟΝΟΜΑ',
ΤΟΠΟΘΕΣΙΑ** (all caps; the quoted nickname only where one exists) and the
English mirror **F.W.CO-OP 'NAME', LOCATION** (toponyms/nicknames
transliterated). Tooling committed at the repo root: `dase_name_curator.html`
(offline card-per-co-op tool — shows every registry spelling, prefills both
names per the convention with set-pooled nickname detection, autosaves in
the browser, exports `{ΑΦΜ: {el, en}}` JSON) and `dase_names_review.tsv`
(the flat review worksheet, incl. the 46 rejected keys with reasons).
Names will land in `khmdhs/data/dase_contractors.json` as
`display_el`/`display_en` and flow to the site once the user's export
arrives; registry spellings in `contracts`/`contractors` are never
rewritten. *Affects: nothing yet — presentation layer in progress.*

## 2026-08-14 — Anti-nero work-type categories: curated 8-group taxonomy over the 245 in-scope contracts

Every in-scope contract gets exactly ONE curated work-type category so the
Atlas category chart reconciles to the stated-net basis
(€658,297,730.65). The registry `contracts.title` is a ≤100-char
shorthand; the classification source is the descriptive **project title
inside the signed PDF** (era-dependent anchors: phase III/IV/2026 page-1
«ΣΥΜΒΑΣΗ ΓΙΑ ΤΗΝ ΕΚΤΕΛΕΣΗ [ΤΜΗΜΑΤΟΣ] ΤΟΥ ΕΡΓΟΥ» + «…»; phase II
«ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ» + «…»; phase I has NO page-1 title — it lives
in the Ορισμοί under «υπό τον τίτλο "…"»; μελέτες under «ΣΥΜΒΑΣΗ ΔΜ-xx /
ΣΠ-xx» headers; ΕΣΑ titles are two-level — umbrella «ΕΘΝΙΚΟ ΣΧΕΔΙΟ
ΑΝΑΔΑΣΩΣΗΣ» plus the real lot title in «ΤΜΗΜΑ N: "…"»; APE/παράταση
decisions under «ΘΕΜΑ: …»), with `contract_objects.short_description` as
a cheap first pass (verbatim for III/IV/2026, generic gloss for I/II),
recursion into `prev_reference_no` parents for the 47 derivative
documents (amendments/APE/extensions filed under their own SYMV), and
the discriminating CPV tail (in-scope reach < 50; e.g. 45246400-7
αντιπλημμυρικά, 44611500-1 δεξαμενές, 77231600-4 αναδάσωση) as a
tie-breaker ONLY — the CPV head is boilerplate shared by nearly all
contracts. ~33 phase-II txts carry font-mangled accents («Εργασιίες
ειδικωάν…»); matching is accent/space-folded and the stored titles are
hand-cleaned. Taxonomy (stable keys, Greek labels shipped from the
curated file — never hardcoded in code):
`dasotexnika` Δασοτεχνικά έργα πρόληψης (καθαρισμοί, αντιπυρικές ζώνες,
δασικό οδικό δίκτυο) · `miktes_zones` Μικτές αντιπυρικές ζώνες (οικισμοί
& δρόμοι) · `arxaiologikoi` Προστασία αρχαιολογικών χώρων & μνημείων ·
`ylotomies` Υλοτομίες ξερών & προσβεβλημένων δένδρων · `antidiavrotika`
Αντιδιαβρωτικά & αντιπλημμυρικά έργα αποκατάστασης · `anadasoseis`
Αναδασώσεις & δασικά φυτώρια (ΕΣΑ) · `meletes` Μελέτες & σχέδια
αντιπυρικής προστασίας · `ydatodexamenes` Υποδομές νερού πυρόσβεσης
(δεξαμενές & κρουνοί). Precedence: specific beats generic (a title naming
ΜΑΖ / αρχαιολογικούς χώρους / υλοτομίες / δεξαμενές wins over the
boilerplate καθαρισμός phrasing); derivatives inherit their parent
chain's category. Artifacts: curated
`khmdhs/data/contract_categories.json` (per-ADAM category + verbatim
cleaned title as evidence + source pdf/short_description/inherited:<ref>)
→ `khmdhs/categories_loader.py` → tables `contract_categories` +
`category_labels`; in the refresh chain after studies_loader. Final curated counts (245/245, Σ stated net reconciles to €658,297,730.65 exactly): dasotexnika 155 (€361.2M) · miktes_zones 33 (€128.2M) · antidiavrotika 12 (€57.5M) · anadasoseis 8 (€45.9M) · arxaiologikoi 17 (€32.0M) · ylotomies 5 (€21.0M) · meletes 14 (€9.2M) · ydatodexamenes 1 (€3.3M). Review corrections vs the rule proposals: 11 ΜΕΛΕΤ/ΑΝΑΔΑΣ false hits moved to dasotexnika (έργα «με εγκεκριμένη μελέτη», «αντιπυρική προστασία αναδασώσεων» = καθαρισμοί γύρω από αναδασώσεις), the 24SYMV014774679 mixed mega-contract keeps dasotexnika (πυροφυλάκια/δεξαμενές are a trailing component), 4 ΕΣΑ/ΑΠΕ derivatives take their parents' titles, and 15 phase-I amendment titles resolve from parent PDFs (the amendments quote only the contracting parties).
*Affects: new tables only; the Atlas «category» chart and its pins.*

## 2026-08-14 — Category audit: one recategorization + a khmdhs stated-value keying error (Σουφλί)

Mechanical audit of all 245 category assignments (cross-signals between
curated title / registry title / short_description, per-category support
requirement, scope consistency, discriminating-CPV hints, full-body
vocabulary dominance, sibling-title consistency, € coincidence screening).
238/245 passed unflagged; reviewed flags: the 24SYMV014774679 mixed
mega-contract and the 4 ANTINERO III contracts whose bodies cite the
«(Antinero II) – Αντιδιαβρωτικά & Αντιπλημμυρικά Έργα» FUNDING-programme
name (ΟΠΣ ΤΑ 5201358 recital, not the work object) stay dasotexnika.
Two real findings, both fixed:

1. **26SYMV019200696 recategorized dasotexnika → ylotomies.** Its curated
   title had been taken from the act's «Θεώρηση και έγκριση μελέτης με
   τίτλο "…"» quote — the title of ONE study inside the contract. The
   family's real title (verified in parent PDF 26SYMV018682054 and quoted
   in the record's own short_description) is «Έργα αντιπυρικής προστασίας
   σε δημόσια δασικά συμπλέγματα και αναδασωτέες εκτάσεις, καθώς και
   δασοκομικοί χειρισμοί σε μεταπυρικά οικοσυστήματα … Δασαρχείων
   Αλεξανδρούπολης και Διδυμοτείχου» — the same phrasing as its two
   ylotomies siblings (26SYMV018599446, 26SYMV018642772). Title now
   inherited from the parent. Counts become dasotexnika 154 / ylotomies 6.

2. **26SYMV018642772 «ΕΡΓΑ ΑΝΤΙΠΥΡΙΚΗΣ ΠΡΟΣΤΑΣΙΑΣ ΔΧ ΣΟΥΦΛΙΟΥ» registry
   stated value is a keying error** — the row (and its raw payload, and
   its contract_objects seq 0) carries €3,341,238.72 net / €4,143,136.01
   gross, which are EXACTLY the figures of 25SYMV017471484 «ΔΕΞΑΜΕΝΕΣ &
   ΚΡΟΥΝΟΙ ΠΕΡΙΑΣΤΙΚΟΥ ΔΑΣΟΥΣ ΘΕΣΣΑΛΟΝΙΚΗΣ» (whose PDF confirms them in
   words). The Σουφλί signed PDF states its συμβατικό τίμημα in words and
   figures: «τέσσερα εκατομμύρια τριακόσιες τριάντα τέσσερις χιλιάδες
   τριακόσια πενήντα τρία ευρώ και σαράντα ένα λεπτά (4.334.353,41 €),
   πλέον ΦΠΑ (24%) και … (5.374.598,23 €), συμπεριλαμβανομένου ΦΠΑ». No
   amendments, not cancelled, no other row carries the PDF figure.
   Corrected via the ΔΑΣΕ-built mechanism, now shared: curated
   `khmdhs/data/contract_corrections.json` (khmdhs-side file) applied by
   `khmdhs.contract_corrections` (standalone CLI + a `khmdhs.refresh`
   step right after the refetch/upsert phase, since INSERT OR REPLACE
   restores registry values). Candidates for future entries come from the
   same audit-style screens; corrections land only after human PDF review.

New Atlas analytics basis: stated net **€659,290,845.34**
(was €658,297,730.65; +€993,114.69). All pins updated. *Affects: 1
contracts row + 1 contract_objects row + 1 contract_categories row; every
Anti-nero stated-basis aggregate; category chart counts/€.*

## 2026-08-14 — ΚΗΜΔΗΣ double-postings excluded from the ΔΑΣΕ dataset (9 contracts, 1 payment)

A content sweep over the complete ΔΑΣΕ PDF/txt cache (groups sharing
co-op+date+amount, texts compared after stripping the registry's own
ΑΔΑΜ stamps) found 14 same-day same-amount pairs. Nine are the SAME
signed document uploaded twice under two ΑΔΑΜ (normalized texts
identical; the user verified two pairs against the PDFs — same Αριθ.
Πρωτ. and same Diavgeia ΑΔΑ: Πενταλόφου 357167/ΩΧ2Π4653Π8-1ΙΞ and the
«Η ΕΝΩΣΗ» Βυτίνας pair). Five pairs are verified DISTINCT (real diffs:
συστάδες 4↔5 and 29↔35, protocol years 23/2023↔42/2024, an extra
protocol citation, different dates) and stay untouched.

Excluded duplicate → kept posting (keep = the payment-carrying twin,
else the earlier ΑΔΑΜ):
22SYMV009895951→22SYMV009895998 · 24SYMV015320152→24SYMV015319751 ·
22SYMV011428409→22SYMV011425902 · 24SYMV015789944→24SYMV015789338 ·
21SYMV009363348→21SYMV009363115 · 24SYMV015324834→24SYMV015324918 ·
21SYMV009578833→21SYMV009579012 · 22SYMV011574438→22SYMV011574305 ·
21SYMV009502419→21SYMV009502974.

Payments: `22PAY010598913` excluded — same payment paper as
`22PAY010599002` uploaded twice (user-verified; the PDF states
86.504,06 € net / 107.265,03 € gross, matching the kept row; the
duplicate's stored 86,938.75 was additionally mis-keyed). The two
€7,498.00 payments of the 21SYMV009363115 pair are NOT duplicates —
different protocol numbers and internal breakdowns (similarity 0.84) —
both stay counted.

Mechanism: `exclude: true` + `duplicate_of: <kept ΑΔΑΜ>` entries in
`dase_contract_corrections.json` (applier sets `cancelled = 1`,
`correction_note`, and the new `contracts.duplicate_of` column — ALTER
guard in db.py); new `dase_payment_corrections.json` in the standard
payment-corrections format applied via `payment_loader.apply_corrections`
from the same runs. NOTHING disappears: duplicate pages stay reachable
with a banner linking the kept ΑΔΑΜ (and the kept page links back), and
ΑΔΑΜ search still finds duplicates, badged. Guard:
`scripts/find_duplicate_postings.py` + a real-DB test pin that zero
live identical-text twins exist.

New basis: live population **2,009 rows / €38,428,542.97 gross =
€31,672,918.06 net** (−€128,694.08 net); paid net **€21,211,472.57**
over 991 payment orders (−86,938.75). *Affects: 9 contracts rows +
1 contract_payments row; every ΔΑΣΕ aggregate; paid KPIs.*

## 2026-08-15 — Tenth ΔΑΣΕ double-posting: corrected re-issue under a phantom ΑΦΜ (Κουρκουλών Ευβοίας)

Found through the name-curation cross-keying flag, not the text sweep —
the pair carries two DIFFERENT contractor VATs, so the (VAT, date,
amount) grouping of `find_duplicate_postings.py` never compared them.

`24SYMV015423487` (Δήμος Μαντουδίου-Λίμνης-Αγίας Άννας, 2024-09-13,
€13,395.00 net / €16,609.80 gross) names contractor «ΔΑΣΙΚΟΣ
ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΚΟΥΡΚΟΥΛΩΝ ΕΥΒΟΙΑΣ» with ΑΦΜ «0310003799» —
ten digits, and VIES confirms **EL031000379 does not exist** (invalid
VAT). `24SYMV015485823` is the same contract re-posted with the real
ΑΦΜ **096115714** (VIES: ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΚΟΥΡΚΟΥΛΩΝ
ΕΥΒΟΙΑΣ, trade name «ΔΑΣΕ ΚΟΥΡΚΟΥΛΩΝ Η ΑΓΙΑ ΠΑΡΑΣΚΕΥΗ», seat
Κουρκουλοί, 34005 Λίμνη). Normalized cached texts are 98% identical;
the ONLY differences are the ΑΦΜ printed in the document body
(0310003799 → 096115714), one internal date (13 → 25, the re-issue
twelve days later) and one protocol/reference number. Same parties,
same amount, same works. The single payment `24PAY015905505`
(€13,395.00 net = full settlement) sits on the kept re-issue; the
phantom-ΑΦΜ posting has none.

Decision: exclude `24SYMV015423487` as `duplicate_of →
24SYMV015485823` via `dase_contract_corrections.json` (same
mechanism/banners/search behaviour as the nine 2026-08-14 exclusions).
The phantom co-op «031000379» thereby leaves the live directory —
it existed only through the botched first posting (250 → 249 co-ops).

Guard hardened: `find_duplicate_postings.py` now runs a second,
cross-VAT pass — groups live contracts by (date, amount) alone and
compares texts — so a mis-keyed contractor ΑΦΜ can no longer hide a
twin from the sweep. Cross-VAT suspects are flagged `same_vat: false`
and remain human-review candidates (sibling lots of one πρόσκληση can
be legitimately near-identical); the identical-text real-DB guard is
unchanged.

New basis: live population **2,008 rows / €38,411,933.17 gross =
€31,659,523.06 net** (−€13,395.00 net); paid figures unchanged
(€21,211,472.57 / 991 — the excluded posting carried no payments).
*Affects: 1 contracts row; every ΔΑΣΕ aggregate; co-op directory count.*

## 2026-08-15 — ΔΑΣΕ display-name curation COMPLETE (249 co-ops, bilingual)

The user finished naming all co-ops in `dase_name_curator.html`: one Greek
+ one English display name per canonical ΑΦΜ, every value typed or
confirmed by the user. The five consistency judgment calls raised by the
2026-08-15 check were resolved by the user in the curator's decisions
panel: PAIKO **PAIONIA** (matches their Γρίβα card), **AISYMI** on both
ΑΙΣΥΜΗ cards, **KARDAMOS** on both ΚΑΡΔΑΜΟΣ cards, the Β' co-ops marked
with a **«(Β)» suffix** in both languages (their own convention, replacing
the proposed «(2nd)»), and ΤΟ ΠΑΛΙΟ ΠΕΥΚΩΤΟ **uppercased**.

On top of the user's final export, 25 mechanical normalizations were
applied (never touching wording): 13 Greek homoglyph letters inside
English names → Latin (KAMVOUNIΑ, KΑΤΟ, POTAMΟΙ, (Α)/(Β) …), 7 Latin
homoglyphs inside Greek names → Greek (ΝOTIOY, ΝEOY, ΠΕΝΤΑΛΟΦΟY,
MΕΓΑΛΗΣ, 'H, the two «(B)» suffixes), punctuation (« » wrappers, curly
quote, double space, space-before-quote, stray «F.W.CO-OP.» period,
«Δ.Α.Σ.Ε.» → «ΔΑ.Σ.Ε.»), and the phantom-ΑΦΜ ghost entry 031000379
dropped (its only posting was excluded as a duplicate the same day).

Result: curated **`khmdhs/data/dase_display_names.json`** — 249 entries
keyed by canonical ΑΦΜ, verified bijective against the live co-op
population (249/249, zero unnamed, zero orphans) and free of cross-script
characters. Conventions: el `ΔΑ.Σ.Ε. 'ΟΝΟΜΑ', ΤΟΠΟΘΕΣΙΑ`; en `F.W.CO-OP`
mirror with nominative toponyms; modifier prefixes (ΑΝΑΓΚΑΣΤΙΚΟΣ →
A. / ΕΛΕΥΘΕΡΟΣ → FREE / ΑΓΡΟΤΙΚΟΣ → A. or FARMING / ΟΡΕΙΝΟΣ → MOUNTAIN /
Β') preserved. Registry spellings in `contractors.name` are NEVER
rewritten — this is a presentation layer. Name-field resolution notes
carried by the curation: 996713836 ΑΚΡΙΤΟΧΩΡΙΟΥ «ΠΕΡΤΟΥΛΙ» is distinct
from 999419942 «Η ΟΣΤΡΙΑ» (PDF-verified); 996875099/996875014 Φθιώτιδα
names verified via VIES + PDFs 2026-08-15. The interim 89-name snapshot
(`dase_display_names.json` + `dase_names_review.tsv` at the project
root) is superseded and removed. *Affects: presentation only — site
wiring is the follow-up step; no aggregate changes.*

## 2026-08-15 — English display names for the 74 Π.Ε. (Atlas presentation layer)

The Atlas mixes English UI copy with Greek data names; the user asked for
English region names on a defensible basis. Decision (user, 2026-08-15):
base = the **official Eurostat Latin names** (`NAME_LATN` in the NUTS-3
layer kept at `data/raw/greek_nuts3.geojson`, which follows the Greek
state's ELOT 743 romanization), joined to the 74 canonical Π.Ε. through
the legacy Π.Ε.→NUTS-3 bridge; merged NUTS units («Kavala, Thasos»,
«Kalymnos, …, Kos, Rodos», «Peiraias, Nisoi» …) split by hand. On top,
user-approved **familiar-English overrides** for the famous names: Evia,
Heraklion, Corfu, Rhodes, Piraeus, Central/North/South/West Athens,
East/West Attica, Attica Islands (Νήσων), Kefalonia, Ithaca, Rethymno,
Kea-Kythnos, and **Lemnos** (user choice over official Limnos); the user
kept **Larisa** (official single-s over Larissa), Thira (not Santorini),
Lesvos, Voiotia, Chalkidiki, Zakynthos, Fthiotida, Ileia.

Curated **`khmdhs/data/pe_names_en.json`** — 74 entries keyed by the
canonical Π.Ε., each carrying its `nuts_id` + verbatim `name_latn` as
evidence; byte-identical copy shipped to
`atlas/src/lib/data/pe_names_en.json` (pinned equal by test, like the
other double-copied geo data). Presentation only: every aggregation,
permalink and API key stays on the Greek canonical Π.Ε.; the Atlas
renders «R.U. <name>» (user-chosen prefix) wherever «Π.Ε. <name>»
displayed before. webui (:5000, frozen) keeps Greek. *Affects: display
strings on Atlas region surfaces; zero data/aggregate changes.*

## 2026-08-16 — English display names for awarding bodies and units (Atlas)

Extending the Π.Ε. layer (2026-08-15) to every awarding-body name, per the
user's reviewed proposal. Three curated files, each keyed by the EXACT
registry string, each with a byte-identical copy in `atlas/src/lib/data`
(pinned):

- **`authority_names_en.json`** — the 103 forest authorities as
  «<Toponym> Forest Service Office» (Δασαρχεία) / «<Toponym> Forest
  Directorate» (Διευθύνσεις Δασών), toponym-first (user choice over the
  «of»-form). Toponyms reuse `pe_names_en.json` where the seat names a
  Π.Ε.; the rest are ELOT 743 with the user's reviewed forms — kept:
  Korinthos, Kalampaka, Sparta, Thebes, Mesolongi, Piraeus, Samothraki;
  also Patras, Megara, Olympia, Athens, Dodecanese, Volos etc.
- **`org_names_en.json`** — all 49 live ΔΑΣΕ awarding organizations (incl.
  the kh-shared ΥΠΕΝ): official English titles for ministries,
  αποκεντρωμένες («Decentralized Administration of …»), «Region of …»,
  «Municipality of <ELOT toponym>» (the «ΔΗΜΟ ΑΡΓΟΥΣ ΟΡΕΣΤΙΚΟΥ» typo row
  keyed as-is), official names for the misc bodies. User corrections:
  «Aristotle University of Thessaloniki (A.U.TH.)», plain «General
  Hospital of Kozani» (no «Μαματσείο» epithet).
- **`unit_names_en.json`** — the 49 municipal/other operator units
  (dictionary translations reviewed by the user), the 4 ΥΠΕΝ signer
  units, and the forest units without a registry fold-match (Δασαρχείο
  Φουρνά incl. the ΦΟΥΡΝΩΝ variant, ΔΔ Ηλείας / Ν. Πιερίας / Χαλκιδικής).

Applied by `atlas/src/lib/transforms/names.ts` (`authEn`/`orgEn`/
`unitEn`/`bodyEn` — accent/case/whitespace-folded lookups so raw
registry spellings match; unmapped strings fall back to the Greek,
honestly) on: /authorities + /authority pages, the /dase map circles,
tooltips and click-panel, the AWARDING BODIES / AWARDING UNITS charts,
coop-page unit tables, and both contract pages' Authority / Operating
unit rows. Signer PERSON names and all quoted evidence stay Greek; co-op
names stay Greek (user decision). **Dev-only audit aid** (user request):
`devGreek()` adds the Greek original as a hover title on translated
names when running `npm run dev`; production builds render none.
Coverage + Latin-only + copy-identity + user-decision pins in
`tests/test_body_names_en.py`. *Affects: display strings only; keys,
aggregates and permalinks unchanged.*

## 2026-08-17 — Forest-authority office layer: addresses, contacts, seat coordinates

Until now every forest authority sat at its seat MUNICIPALITY's centroid.
New office layer (user-approved plan; savewild.gr dropped as source):

**Sources.** (1) The ministry's own directory: the 7 «Επιθεώρηση
Εφαρμογής Δασικής Πολιτικής» pages on ypen.gov.gr each carry a contact
TABLE (ΦΟΡΕΑΣ / ΤΑΧ. Δ/ΝΣΗ / ΤΗΛΕΦΩΝΟ / EMAIL) for every unit —
fetched 2026-08-16/17 via windowed Playwright (Akamai 403s every
non-interactive client), cached in `data/processed/ypen_offices_cache/`
(HTML gitignored, parsed offices.json/matched.json tracked;
`scripts/harvest_ypen_offices.py`). 151 unit rows parsed; 102/103
registry authorities matched (tiered fold-matching; the ministry writes
«Δ/ΝΣΗ ΔΑΣΩΝ Π.Ε. Χ», «ΔΑΣΑΡΧΕΙΟ ΚΑΤΩ ΝΕΥΡΟΚΟΠΙΟΥ», «ΠΑΤΡΑΣ» etc.).
(2) Primary corroboration — Diavgeia letterheads: all ΥΠΕΝ forest units
are registered with unit uids (org 100015996; labels carry Latin
homoglyphs — «ΔΑΣΑΡXEIO ΠΑΤΡΩΝ»); `scripts/harvest_office_letterheads.py`
fetched each authority's own recent decisions and checked the ΥΠΕΝ Τ.Κ.
against the letterhead digits (which survive even font-mangled
extraction). **90/102 confirmed** (ΑΔΑ + verbatim excerpt kept).

**Differences found and resolutions** (all recorded per-entry in the
`office.note` field): Γουμένισσας — ΥΠΕΝ page says Τ.Κ. 63100 (the
Πολύγυρος code, an obvious digit transposition); the authority's own
letterhead says «Τ.Κ.: 613 00» (ΑΔΑ 9ΒΟΨ4653Π8-299) → letterhead wins.
Λίμνης — ΥΠΕΝ gives no Τ.Κ.; letterhead 34005 used. Same-town
granularity variants noted, ΥΠΕΝ street+Τ.Κ. pair kept coherent:
Αλεξανδρούπολης 68131↔68132, Ξάνθης 67100↔67133, Πύργου 27100↔27131,
Καλαμάτας 24100↔24131, Χαλκίδας 34133↔34100. Letterheads inconclusive
(mangled digits; recurring false candidates are the «4653Π8» ΑΔΑ prefix
and cited law numbers): Λαγκαδά, Λαυρίου, Δασαρχείο+ΔΔ Λάρισας →
ΥΠΕΝ values kept. Κοζάνης — ΥΠΕΝ prints a garbled «51 00» and the
letterheads are unreadable → Τ.Κ. honestly absent, geocoded via
street+city. Περτουλίου — not a ΥΠΕΝ unit at all (the university
forest is run by the ΑΠΘ fund): no office data, seat stays municipality
centroid.

**Storage.** Additive `office` block per entry in
`forest_authorities.json` (street/tk/city/phones/emails, source + fetch
date, evidence_ada + excerpt where confirmed, note where differing;
`scripts/build_authority_offices.py` re-merges). Aliases and all
matcher-facing fields untouched. Person names (προϊστάμενοι) are NOT
stored. 103 blocks, 101 with Τ.Κ.

**Geocoding** (`scripts/geocode_authority_offices.py`): Nominatim
structured tiers street+Τ.Κ.+city → Τ.Κ.+city → city, each retried in
Greek→Latin transliteration; accepted only when the hit's postcode
shares the Τ.Κ. 3-digit prefix or lies ≤35 km from the seat-municipality
centroid. Result: **41 street / 58 postcode / 1 city / 3 municipality
fallback** (Κυνουρίας, Πόρου failed validation; Περτουλίου no data).

**DB/UI.** `forest_authorities` gains street/postal_code/city/phone/
email/seat_precision (db.py ALTER guard); `forest_loader` prefers the
validated office point over the municipality centroid — every seat-based
map (dase circles, kh overview, webui) moves automatically. The Atlas
/authority pages show a contact block (address · tel · mailto email)
from `authority_profile.contact`. Pins in `test_forest.py`
(103 precision values, the two documented Τ.Κ. gaps, Γουμένισσα 61300,
≥80 office-precision seats). *Affects: seat coordinates and new contact
columns; zero €/aggregate changes.*

## 2026-08-17 — Complete ΥΠΕΝ directory (151 units) + full attribution audit

**Directory (Phase A).** The full ministry contact directory — all 151
unit rows of the 7 επιθεωρήσεις pages — becomes a curated REFERENCE
layer: `khmdhs/data/forest_units_directory.json` → `forest_units_directory`
table (loaded by forest_loader; NEVER fed to the contract matcher). 102
rows cross-link to the contract registry; the other 49 (7 inspectorates,
7 coordination directorates, 3 reforestation directorates, 28 ΔΔ + 4
δασαρχεία with no contracts in our datasets) are now shown on
/authorities as «The rest of the network — no contracts recorded», with
their contacts and new English names (unit_names_en.json extended by 43
entries, same conventions). The supra-regional ΕΠΙΘΕΩΡΗΣΗ Μ-Θ now draws
as ONE /dase map circle at its real seat (Λεωφ. Γεωργικής Σχολής 32,
Πυλαία — geocoded from its directory row) instead of two Π.Ε.-centroid
dots.

**Audit (Phase B).** Report-mode re-scan of every in-scope Anti-nero
contract (title+items, then cached PDF text with a parent-chain
suppression rule) and every ΔΑΣΕ operator-unit string, with the 32
directory-only ΔΔ/δασαρχεία ADDED to the matcher vocabulary
(`scripts/audit_authority_links.py` → authority_link_audit.json,
gitignored). Result: **zero missed attributions** — one title hit total,
25SYMV016670155, which is one of the six pinned contract_overrides (its
title's «ΔΔ ΛΑΡΙΣΑΣ ΤΡΙΚΑΛΩΝ…» sloppiness was already human-resolved to
the five δασαρχεία the items name); zero PDF-only hits; zero ΔΑΣΕ unit
matches. The 49 extra units genuinely award nothing in our data — the
current 103-registry attribution stands validated against the complete
official vocabulary. *Affects: reference table + /authorities section +
one dase map circle; zero attribution or € changes.*

## 2026-08-16 — Sponsored works: designation-act fronts vs follow-up coverage (9ΕΘΠ probe — negative), fire dates on the EFFIS layer

**Finding (user challenge on /anadohoi/project/9ΕΘΠ4653Π8-ΠΡ4).** The
ΔΕΔΔΗΕ study appointment names five fire fronts (Δερβενοχωρίων, Κουβαρά
– Σαρωνίδας, Λουτρακίου, Αιγίου, Φυλής – Πάρνηθας) but the trail
evidences approved studies for only two: the Δερβενοχώρια burn complex
(641Ξ4653Π8-Υ9Ι + ΡΨΗΡ4653Π8-ΙΧΖ — basins named after the burned
municipalities Μάνδρας-Ειδυλλίας/Ελευσίνας/Μεγαρέων) and Αίγιο
(6ΛΡΨ4653Π8-3ΧΝ — Τ.Κ. of Δ.Ε. Διακοπτού). Probe for the other three
fronts: (a) offline, every cached anadohoi act text grepped for
«9ΕΘΠ4653Π8|89498/2832» → only the three already-linked acts cite it;
(b) online, luminapi sweep of ΥΠΕΝ (100015996) subjects «Θεώρηση και
έγκριση» + «έγκριση μελέτης» (1,890 distinct acts), narrowed to
in-window (post-06.09.2023) erosion/flood-study approvals
(ΥΔΡΟΝΟΜ/ΑΝΤΙΠΛΗΜΜΥΡ/ΑΝΤΙΔΙΑΒΡ → 49), all 46 non-linked PDFs fetched
and full-text checked → **none cites the designation act**. Conclusion:
no published approval exists for Κουβαρά–Σαρωνίδας, Λουτρακίου or
Φυλής–Πάρνηθας — the trail is complete as far as Diavgeia shows, and
the «completed» judgment (deliverable = the approved studies) stands
with this coverage limit now stated. Method note: Diavgeia search
indexes subjects/metadata only — recitals are NOT searchable — so
citation-children can only be surfaced by local full-text checks.

**Presentation.** LOCATION row labelled «as named in the designation
act»; the FactsHeader caveat now states that the act may name more
areas than the follow-up documents cover, that the map shows the work
locations named in the trail documents, and that fire perimeters are
satellite estimates © European Union, Copernicus EMS — EFFIS (the
under-map EFFIS caption lines folded into it). Site-map pins lost
their name labels (12-label soup buried the scars); fires render solid
with one tone per fire (earliest darkest), matched by dots on the act
timeline bar at each fire's start date; hover card (black, top-left)
states date + ha.

**Data layer.** `build_effis_layer.py` now emits the fire start date
(`initialdat` → property `d`, ISO) — both display copies rebuilt,
1,969 features, ids/years unchanged (tests pass unmodified).

## 2026-08-16 — Public-bodies registry (design + extraction phase)

**Decision.** Build a unified registry of AWARDING bodies across the three
datasets — curated `khmdhs/data/public_bodies.json`: one entry per body
with a stable slug key, canonical name, ΑΦΜ (attribute, NOT key —
090273987 is shared by ΥΠΕΝ and ΑΠΔ Θ-ΣΕ), a CLOSED kind vocabulary
(ministry / decentralized_administration / region / municipality /
municipal_entity / state_vehicle / other_public; forest units stay in
forest_authorities.json + forest_units_directory.json and are referenced,
never duplicated), a **scope** label that says when place-inference from
the body is safe (municipal → its municipality, regional → its region,
national → never), a municipality_code link into greek_municipalities.json
(gives Π.Ε. + centroid for free), and an aliases array of VERBATIM
registry spellings (typos kept — the name-normalization table, same
doctrine as dase_display_names/org_names_en). Inspired by the FireWatch
architecture studied today (organization registry + normalization
registries as universal joins) while explicitly REJECTING its location
semantics: work regions stay document-curated; the registry supplies the
tier-1 baseline, validation audits and presentation (map kind legend,
body chips), with the attribution tier always declared.

**Mechanism.** `scripts/extract_public_bodies.py` sweeps distinct
organization strings from khmdhs (3), dase (49) and anadohoi decisions
(25), proposes kind/scope by name stems (the /dase map's stem heuristic,
to be retired into the registry), pulls ΑΦΜ from the stored ΚΗΜΔΗΣ
payloads (`raw_json.organizationVatNumber`), matches municipal bodies to
greek_municipalities by genitive fold WITH a Π.Ε. cross-check against the
bodies' own contracts' curated regions (duplicate municipality names
resolve by ΥΠΕΣ code + Π.Ε. agreement, never by name — the Ηρακλείου
lesson), and emits a review worksheet + curator HTML
(public_bodies_curator.html). Every verdict is the user's; the curated
JSON, loader (`public_bodies` + `public_body_aliases` tables in both
contract DBs), coverage-bijection tests and consumers land after review.

## 2026-08-16 — Public-bodies registry: verdicts landed, registry live

All 67 bodies user-reviewed (public_bodies_curator.html export) and the
five parked ones resolved after checking their exact contracts: ΑΔΜΗΕ
(4 line-clearing contracts along ΓΜ 150/400kV), ΟΣΕ (Σ.Σ. Κίρκης +
ΟΣΕ groves), Οργανισμός Λιμένος Αλεξανδρούπολης (works in its own port
zone), ΓΝ Κοζάνης (trees at the hospital grounds), Ταμείο Πανεπιστημιακών
Δασών (Περτούλι) — **user chose the strict `other_public / national` for
all five** (no place-inference ever). ΔΥΠΑ and ΠΕΡ.ΓΕΝ. Νοσοκομείο
Λάρισας aligned seat→national to match the explicit ΓΝ Κοζάνης verdict
(flagged for veto); «ΛΟΥΤΡΑ ΛΟΥΤΡΑΚΙΟΥ ΔΗΜΟΥ ΑΛΜΩΠΙΑΣ Α.Ε» reclassified
municipality→municipal_entity (same municipal scope). ΑΦΜ hygiene:
Δήμος Διρφύων-Μεσσαπίων keyed '0997591330' in the payload → 997591330
(VIES-confirmed name match); Δήμος Δομοκού carries an invalid 8-digit
'80011783' and VIES rejects the plausible completions → afm honestly
null with note. Final registry: 67 bodies / 68 verbatim aliases —
37 municipalities, 5 municipal entities, 3 regions, 6 ministries,
4 αποκεντρωμένες, 1 state vehicle (Πράσινο Ταμείο, user's label),
11 other public; scopes 43 municipal / 3 regional / 21 national / 0 seat.

Mechanism: curated `khmdhs/data/public_bodies.json` →
`khmdhs/bodies_loader.py` (strict: refuses review/unknown vocab, municipal
without a valid municipality_code, non-9-digit ΑΦΜ, cross-claimed aliases;
WARNs on DB org strings the registry does not know) → tables
`public_bodies` + `public_body_aliases` in BOTH contract DBs; hooked at
the end of harvest_dase.py load and in the khmdhs.refresh chain.
`tests/test_public_bodies.py`: validation units + real-DB pins incl. the
coverage BIJECTION (every awarding string in khmdhs+dase+anadohoi resolves
to exactly one body; no stale aliases). Consumers (dase map legend kinds
from the registry, tier-1 audits) come next; location semantics unchanged
— work regions stay document-curated.

## 2026-08-16 — 6Φ454653Π8-Ξ1Ζ (ALFA WOOD, Καλαμάς/Αχέροντας): four trail acts reclassified other→study_approval

The four «Έγκριση μελέτης … μεταχρωματικού έλκους πλατάνου» acts
(6ΟΜ04653Π8-1ΑΧ, 6ΨΞ04653Π8-Θ04, 9ΓΨΘ4653Π8-ΝΑΨ, 9ΚΟΗ4653Π8-ΜΥΗ) are
literally study approvals — each cites the designation act verbatim in
its recitals («…ΥΠΕΝ/ΔΠΔ/121316/7195/18-11-2022 (ΑΔΑ:6Φ454653Π8-Ξ1Ζ)
πράξη ορισμού…», re-verified in the cached PDFs) — but were curated as
relation `other` (displayed «Related act»). User approved the
reclassification; anadohoi_projects.json lifecycle entries + the
committed sqlite's project_decisions updated in place (loader-rebuild
avoided per the standing in-place precedent). The 6ΓΨΨ4653Π8-2ΔΓ
Προδιαγραφές εγκύκλιος stays `other`: it does not cite the root — the
project's own amendments and its τεχνική μελέτη approval cite IT.

## 2026-08-16 — Context-river layer for river-scoped sponsored projects + site-dot presentation

**Decision.** Projects whose designation act names RIVERS (6Φ454653Π8-Ξ1Ζ:
«Καλαμά και Αχέροντα Περιφέρειας Ηπείρου») get the named watercourses
drawn on the card map: geometries from OpenStreetMap (Overpass, named
waterway ways merged + simplified ~50 m), committed as
`data/processed/context_rivers.geojson` + byte-identical
`atlas/static/geo/context_rivers.geojson` (build:
`scripts/build_river_layer.py`); each feature carries the project ΑΔΑs
it applies to — application is curated per feature, never name-matched.
Mandatory attribution in the card caveat: «© OpenStreetMap
contributors», marked approximate (the line is the watercourse, not the
act's intervention zone). Presentation (user decisions): site pins keep
ONE colour (the approximate-precision pale/dashed variant retired — the
precision qualifier moves into the hover card); hovering a site dot
shows a black bottom-left card (white lettering) with the site's name,
«κατά προσέγγιση» flagged there; the FactsHeader caveat rewritten to
state explicitly HOW dots are placed (named in trail documents, geocoded
at the named θέση, or municipality centre when only a δήμος is named).

## 2026-08-16 — Β. Εύβοια zones: provenance statement + outline presentation

**Provenance (user-stated, recorded).** The two digitisation source
sheets (`data/raw/XARTHS_ERGON_DAS_LIMNHS_4.1.pdf`,
`XARTHS_ERGON_DAS_ISTIAIAS_4.2.pdf` — the Master-Plan έργων maps, ΥΛΗ
11.2021) were provided by the Διεύθυνση Δασών Ευβοίας after a formal
request by the user, regarding the works that followed the August 2021
fires. Every surface drawing the digitised zones now states this and
links the two source PDFs (pdf1 = Λίμνης 4.1, pdf2 = Ιστιαίας 4.2),
served by a new whitelisted atlas_api route `/pdf/zonesource/<1|2>`
straight from data/raw.

**Presentation (user decisions).** ZoneMap: the project's zones render
as GREEN OUTLINES above the solid fire fill (no fill — the fire stays
visible through them; invisible wide-stroke twins keep the outlines
hoverable without stealing the interior); hovering the fire fill shows
the black top-left card with the fire's date · ha (same as SiteMap);
hovering a zone outline shows «<name> — <basin>». The /anadohoi
overview map no longer draws the zones at all (projects + fire
outlines only; zone centroids still place the zone-mapped dots).

## 2026-08-16 — Β. Εύβοια zones: Ιστιαία ΙΙ + ΙΙΙ re-digitised by the user

The polygon editor was rebuilt as a committed tool
(`scripts/make_zone_editor.py` → `zone_editor.html`, sheet JPEGs carved
from the source PDFs into gitignored data/processed/zone_sheets/). The
user re-edited the two weakest zones of the 2026-08-12 digitisation:
Ιστιαία ΙΙ (87→96 vertices) and Ιστιαία ΙΙΙ (60→77). Rebuilt geojson
agreement vs the sheets' own tables: ΙστΙΙ 77.7%→**99.5%**, ΙστΙΙΙ
70.3%→**100.0%** (all other zones byte-unchanged; georef/meta
untouched; both display copies regenerated; test_evia_zones green
unmodified). The curated vertex file remains the source of truth.

## 2026-08-16 - Fire-framed detail maps: one shared frame per fire

**Decision (user request: «for all the works that are connected with
the north evia fire of 2021, the zoom frame of the map of the card of
the designation act should be the same and it has to show the whole
burnt scar»).** On the detail cards, whenever a project links EFFIS
burn scar(s), the map frame is the SCAR's bbox plus the continuous
padding (extended only if a site/zone/river pokes beyond the padding
margin - a never-crop guard, a no-op today), and the svg viewBox
aspect derives from that frame instead of the facts-column height.
Every card linked to the same fire therefore renders one identical
window that always contains the whole burnt scar. Verified live: all
9 projects linked to the Β. Εύβοια 2021 scar (EFFIS id 213578,
03.08.2021, 51,881 ha) - 6ΝΗ5/6ΠΔΕ/6ΡΤΣ/9ΑΖΛ/9Κ9Τ/ΡΕΧΥ/ΨΟΨΝ/ΨΧΟ2/ΩΞΕΦ
- render pixel-identical 460x618 frames across both ZoneMap and
SiteMap cards; zones overhang the scar bbox by at most ~1 km, well
inside the ~5-6 km padding, so no card extends the shared frame.
Scar-less maps (river cards, εκτός-fire projects) keep tracking the
facts column via the height prop; the facts-column height binding is
retired on fire-framed cards (the two goals are mutually exclusive -
same frame requires same aspect). ZoneMap now draws ALL Π.Ε. polygons
(the whole-scar frame reaches the mainland coast across the strait,
which must not render as open sea). Padding was also harmonised into
one continuous formula shared by both maps
(max(span*0.15, floor-span): single-site maps keep the ~30 km
half-window, wide geometry tightens to a modest margin).

## 2026-08-16 - Correction: uniform card-map height, regional fire frames

**User overruled two details of the same-day fire-frame entry:**
aspect-derived map heights are OUT («the height of the maps of all
cards should be the same») and the tightened scar padding was too
zoomed («you have to be able to see the upper part of the island»).
Now: every anadohoi card map renders at ONE fixed height (460, square
- facts-column tracking retired with it), and the fire frame keeps the
scar bbox but pads with the standard regional convention
(0.18 x span, >=0.35°/0.27° floors - the same formula scar-less
geometry frames use), which for the Β. Εύβοια 2021 fire brings the
whole upper island (west tip lon 22.81 to the NE coast) plus the
facing mainland into view. The shared-frame guarantee stands and is
now verified at the pixel level: all 9 cards of EFFIS scar 213578
render the scar at identical pixels (x 174-286, y 144-314 in the
460x460 svg) across ZoneMap and SiteMap cards alike.
