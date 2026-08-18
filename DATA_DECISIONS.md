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

## 2026-08-16 - Clarification: card-map height follows the left column

**User clarified the previous entry's height rule:** the map's lower
edge must align with the lower end of the explanatory text on the left
- i.e. height TRACKS the facts+caveat column again (min 420), not one
fixed square. The shared-fire-frame guarantee is kept by construction:
fire-framed maps fit the scar frame BY WIDTH at constant scale and
centre it vertically, so all cards of one fire share the same zoom and
the same horizontal window, and a card's column height only
adds/removes vertical padding context (a scar taller than the viewport
falls back to a both-dims fit at rest, never while user-zoomed). The
scar-frame x pad floor went 0.35°->0.40° because at exact width-fit
the shown window IS the frame and 0.35° clipped the Λιχάδα cape tip
(west extent of upper Εύβοια: lon 22.8116). Verified: the 9 Β. Εύβοια
cards render the scar at identical pixels (x 172-286, ~114x176) at
column-driven heights 462-673.

## 2026-08-16 - Executor co-ops present under their ΔΑΣΕ display names

**Decision (user: for the ΔΑ.Σ.Ε. appearing in the sponsored works,
«for the same ΑΦΜ we have to be represented with the same name» as the
forest co-op works dataset).** Audit first: all 17 curated executor
rows carrying a pinned `dase_vat` (13 projects) resolve into the ΔΑΣΕ
dataset population AND have a curated display name in
dase_display_names.json - zero data gaps; the 6 VAT-less rows are the
documented identity-unconfirmed cases (Παντουρέ/Παπάδων not in the
registry; Μίστρου x2 and Σιδηρονερίου/Περτουλίου ambiguous) and keep
their verbatim act names - honestly unresolved, no invented identity.
The discrepancy was presentational: anadohoi surfaces showed the acts'
verbatim spellings (e.g. «ΔΑΣΕ Αγιοκάμπου Λαρίσας») while /dase shows
«ΔΑ.Σ.Ε. ΑΓΙΟΚΑΜΠΟΥ». Now `queries_extra.overlay_executor_names`
(applied on /api/anadohoi/overview + /api/anadohoi/project) swaps each
pinned executor's `name` for the curated display_el (adding `name_en`,
keeping the act's verbatim spelling as `act_name`), same mechanism and
graceful-absence degradation as the /dase overlay; the acts' wording
remains visible as evidence in the excerpt tooltips and the verbatim
quotes block. A real-DB guard test pins the coverage (every pinned
executor VAT must have a display name) so future executor curation
cannot drift from the ΔΑΣΕ naming.

## 2026-08-16 - Μίστρου executor identity resolved: merged onto 996895246

**User decision (revising the 2026-08-12 «plain Μίστρου never merged»
rule for the executors layer).** The two VAT-less Μίστρου executor
rows - 6ΠΔΕ4653Π8-Ω8Ρ «ΔΑΣΕ ‘ΜΙΣΤΡΟΣ’ Μίστρου Χαλκίδας» (σύμβαση
07/10/2021 με ΔΕΗ) and 9Κ9Τ4653Π8-Δ0Ο «ΔΑ.Σ.Ε. Μίστρου» (πρωτόκολλο
εγκατάστασης 11/10/2021) - now carry dase_vat 996895246 (ΔΑ.Σ.Ε.
«ΑΓΙΟΣ ΚΥΠΡΙΑΝΟΣ» ΜΙΣΤΡΟΥ). Basis: the ΔΑΣΕ registry's 2021-2026
population contains exactly ONE Μίστρου co-op (996895246, 37
contracts, largely ΑΠΔ Θ-ΣΕ - the Β. Εύβοια works milieu where both
acts sit), and that VAT's own registry spellings include plain
«ΔΑ.Σ.Ε. ΜΙΣΤΡΟΥ», titleless «ΔΑΣΙΚΟΣ ΣΥΝΕΤΕΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ ΜΙΣΤΡΟΥ»
AND «Συν/σμος Εργασίας ΜΙΣΤΡΟΣ-ΑΓ.ΚΥΠΡΙΑΝΟΣ» - awarding bodies
demonstrably refer to this same ΑΦΜ as both «Μίστρου» and «ΜΙΣΤΡΟΣ».
GEMI publicity name-search could not disambiguate (its fuzzy matching
ignores the toponym). Verbatim act names kept as evidence; notes
updated to state the merge basis. The remaining VAT-less rows stay
unresolved: «Σιδηρονερίου» (5 candidates) and «Περτουλίου Τρικάλων»
(2 candidates) await the user's own review of the source files;
Παντουρέ/Παπάδων are absent from the registry (nothing to link).
Applied to curated anadohoi_projects.json AND the committed sqlite
in place (surgical executors-column update - a loader re-run would
recompute statuses as of today).

## 2026-08-16 - ΑΔΑ shape bug: org codes are 3-6 chars, not always 6

**Found via a broken PDF link the user hit (ΨΙ87ΟΡ10-1Φ8 - 404).**
Diavgeia ΑΔΑs are 4 random chars + the ORG CODE + '-' + 3 chars, and
org codes vary in length: περιφέρειες/δήμοι 3 (…7ΛΗ, …ΩΞΘ), ΑΠΔ 4
(ΟΡ10/ΟΡ1Υ/ΟΡ1Κ), ΥΠΕΝ 6 (4653Π8) - prefixes run 7-10 chars. Three
regexes assumed exactly 10: the atlas /pdf/diavgeia proxy (404'd the
PDF of every ΑΠΔ/δήμος act - 23 of 322 stored anadohoi decisions and
1 arogi act), and the ΑΔΑ-citation extractors in khmdhs/anadohoi.py
and khmdhs/arogi.py. All three widened to {7,12}; unit tests updated
(truncation typos like «6ΟΘΚ4653Π-ΤΦΚ» now pass the SHAPE - they are
indistinguishable from real short-org ΑΔΑs - and die at the callers'
live-registry verification, the crawl doctrine already in place).
Links verified serving on both origins for all short-prefix acts.
KNOWN RESIDUAL: the anadohoi citation crawl ran under the narrow
pattern, so short-prefix citations were never crawled to closure - a
cache re-scan with the widened extractor finds 13 cited-but-unstored
short-prefix ΑΔΑs (Ψ1ΟΦΩΞΘ-ΓΒΓ cited 40x, ΩΣΖΦΟΡ1Υ-ΒΤ2 21x; a few
are OCR truncations). Fetching/classifying them is a harvest step the
user has not yet ordered - recorded here as the open TODO.

## 2026-08-16 - Citation-crawl residual probed: no dataset impact

The 13 cited-but-unstored short-prefix ΑΔΑs from the ΑΔΑ-shape entry
were probed read-only against the Diavgeia metadata API: 4 are OCR
truncations (404 - Φ1ΞΤΩΝΗ-ΓΒΓ, Ψ10ΦΩΞΘ-ΓΒΓ homoglyph-0 of Ψ1ΟΦ…,
Ρ4653Π8-7ΨΡ, 6ΟΘΚ4653Π-ΤΦΚ) and 9 are real but purely administrative
recital background: 4 δασικός-χάρτης postings (9ΣΧ2ΟΡ1Κ-4ΩΘ,
6Δ2ΙΟΡ1Υ-1ΑΦ, ΩΙΗ8ΟΡ1Κ-3ΒΙ, ΨΧΑΔΟΡ1Κ-ΙΓΟ), 2 ΑΠΔ competence/
signature delegations (ΩΣΖΦΟΡ1Υ-ΒΤ2, 9ΒΗ4ΟΡ1Υ-32Ε), the γραμματείες
machinery act (ΩΩ8Δ6ΔΛ-5ΓΨ), a municipal land-grant-for-reforestation
act (Ψ1ΟΦΩΞΘ-ΓΒΓ, the 40x citation - a precondition recital repeated
across a trail) and a Π.Π.Δ. act for forest-road works (6ΕΚΨ7ΛΛ-Ν09).
NONE is a designation/amendment/extension/revocation/completion - the
sponsor dataset (322 decisions / 69 projects) is unaffected and the
open TODO from the previous entry is CLOSED. Future harvests run with
the widened extractor, so such citations resolve normally from now on.

## 2026-08-17 - Σιδηρονερίου + Περτουλίου executor identities resolved

**User verdicts after reviewing the source acts and the candidate
co-op profiles.** ΨΟΨΝ4653Π8-67Σ «ΔΑΣΕ ‘Σιδηρονερίου’ Δράμας» (ΔΕΗ
συμβάσεις 12/11/2021 + 07/02/2022, source act ΨΙ87ΟΡ10-1Φ8) → pinned
to 096133603 ΔΑ.Σ.Ε. ΣΙΔΗΡΟΝΕΡΟΥ, the village's TITLELESS co-op (the
other four all carry titles - Ελατία/Ροδόπη/Ενότητα/Ομόνοια - and the
same act-family writes titles when it means a titled co-op).
964Ρ4653Π8-ΨΘΗ «ΔΑΣΕ Περτουλίου Τρικάλων» (Εθνική Τράπεζα Χίος,
συμβάσεις 21/22-01-2026, source act Ρ5ΞΟ4653Π8-Φ1Φ) → pinned to
997129709 ΔΑ.Σ.Ε. «ΤΖΙΑΤΖΙΑΣ» ΠΕΡΤΟΥΛΙΟΥ (the other candidate
096047960 «ΤΟ ΠΕΡΤΟΥΛΙ» is the ΑΠΘ university-forest crew).
**Presentation rule (user):** identity-fix documentation is recorded
on the developer side only - a `curation_note` field in the curated
JSON and the API payload that the cards never render; the two Μίστρου
merge notes (2026-08-16) move to the same field. The visible `note`
stays for genuinely user-facing honesty notes (Παντουρέ/Παπάδων «not
in the registry», the Σιδέρη Μαρία installer context). With these two
verdicts every executor row that CAN carry a registry identity does;
the only VAT-less rows left are Παντουρέ and Παπάδων, absent from the
ΔΑΣΕ contracts universe. Applied to anadohoi_projects.json + the
committed sqlite in place, same mechanism as the Μίστρου entry.

## 2026-08-17 — «Consortium» was an artefact: the registry pastes the AWARD's awardee list onto single-party contracts. 2 contracts leave the dataset, 1 re-attributed, n_consortium 19 → 1

The user questioned the caveat «Consortium values counted in full for
each partner (rare here: 19 of 2.008 contracts)». It did not survive
examination, and the award acts explain why.

**The mechanism.** A ΚΗΜΔΗΣ contract record's `contractors` array
sometimes carries the parent AWARD's whole awardee list rather than
that contract's own party. The award is the document that settles it:
25AWRD017394688 (Δ/νση Δασών Καστοριάς, Π.Δ. 126/86 κατανομή) is a
30-row table — συστάδα · δάσος · λήμμα · **δαπάνη** · **ΔΑ.Σ.Ε.** —
and its 30 rows map to 31 stored contracts with **every contract's
gross equal to its row's δαπάνη to the cent**, the two ΣΥΜΠΡΑΞΗ rows
executed as two half-value contracts each. Row 1 (ΔΤ 49δ, Δ.Δ.
Βορείου Γράμμου, 1.320 κ.μ. οξυά, 67.400€, ΣΥΜΠΡΑΞΗ Πεύκου Νεστορίου
– Κυψέλης) = 25SYMV017823600 + 25SYMV017867270, 33.700,00 each.

**The four verdicts** (`contractors_keep` / `exclude` in
`dase_contract_corrections.json`, each citing award + signed PDF +
payment):
- **25SYMV017324270 EXCLUDED** (€115.000 net): signed by Περιφέρεια
  Θεσσαλίας with ΧΑΤΖΗΓΑΚΗΣ ΤΕΧΝΙΚΗ ΑΕ alone — an hourly
  machinery-hire call-off of the Daniel/Elias framework. The record
  lists all ELEVEN framework operators, one of them a co-op, which is
  the only reason the contract entered this contractor-led dataset.
- **25SYMV016837212 EXCLUDED** (€182.270 net): signed by Δήμος Θέρμης
  with Α.ΑΡΑΒΙΔΗΣ – Ι. ΜΠΑΛΙΚΑΣ Ο.Ε alone. Its award split the
  procurement in two lots — ομάδα Α to that company for 226.014,80
  (= this contract's gross to the cent), ομάδα Β to ΔΑΣΕ Μοδίου for
  111.600,00, **which is the separate stored contract
  25SYMV016885520**. The co-op already holds its own lot and was
  additionally credited the company's. Its 5 payment orders are
  excluded with it, because `paid_eur` sums payments without joining
  to contracts and would otherwise report company money as co-op pay.
- **25SYMV017867270 RE-ATTRIBUTED** to ΔΑΣΕ ΚΥΨΕΛΗΣ (997841856): the
  PDF names that co-op, payment 25PAY017976758 pays it for «Συστάδα
  49Δ 1/2», and the two other listed co-ops are other rows of the same
  award holding their own contracts. Its ΑΦΜ field had GLUED two
  numbers («997106512 ΚΑΙ 997841856»), so the canonical-VAT rule was
  crediting the contract to Πεύκου Νεστορίου — who already holds the
  other half — while the signing co-op got nothing. The applier now
  rewrites a glued field to the kept ΑΦΜ.
- **23SYMV013747204 KEPT AS IS** (€5.384 net): a genuine σύμπραξη —
  «νόμιμος εκπρόσωπος του ΔΑ.Σ.Ε. Σιδηροχωρίου & Πετρολόφου».

**n_consortium fixed**: it counted contractor ROWS, so 16 records of
one co-op typed twice under spelling variants inflated it. Those cost
nothing — the canonical-ΑΦΜ merge already collapses them — and after
the four verdicts exactly **ONE** live contract is shared by several
co-ops. The /dase caveat now states the mechanism (each partner
credited in full because the registry never records shares) with that
honest count.

**Mechanism added**: `contractors_keep` in
`khmdhs.contract_corrections` — deletes contractor rows carrying none
of the listed ΑΦΜ and rewrites a glued field to the kept one, refusing
to act at all when no stored row matches (a typo can never empty a
contract's contractor table).

**Corroborated corpus-wide** by the new
`scripts/audit_contract_awardees.py`, which screens all 2.164
contracts against the ΑΦΜ their signed PDFs name: only 4 of the 20
multi-contractor records have genuinely different parties, exactly the
four judged here.

*Affects: ΔΑΣΕ live population **2.008 → 2.006**, stated net
€31.178.858,14 → **€30.881.588,14**, gross €38.411.933,17 →
€38.043.318,37; paid net €20.910.684,02 → **€20.728.414,02** and 967 →
962 orders (the 5 Θέρμης payments); n_cancelled 92 → 94; n_consortium
19 → 1. Both excluded contracts keep reachable, badged pages.*

**Amendment, same day (user):** an out-of-scope contract must not READ
as cancelled. `cancelled = 1` is only the exclusion MECHANISM that these
two records share with genuine registry cancellations and with
double-postings — 25SYMV016837212 was never withdrawn: Δήμος Θέρμης
signed it, it was performed, and it is simply somebody else's contract.
A third marker `contracts.related_to` (ALTER guard in `db.py`, written
by the same `exclude` correction) now records WHY: the in-scope sibling
ΑΔΑΜ of the same procurement, or `""` when there is none. Its page opens
with «Related contract, outside this dataset …» instead of the
double-posting banner, its facts chip reads «outside the dataset», and —
the visible defect the user caught — the ΚΗΜΔΗΣ **document trail on BOTH
pages** now labels the row «outside the dataset» (neutral) rather than
«cancelled» (warning). The trail took its label from `cancelled` alone,
so the co-op's own page 25SYMV016885520 kept announcing a cancellation
that never happened. `queries_extra.contract_timeline` therefore ships
each in-db sibling's `duplicate_of` / `related_to` beside the flag
(column-guarded so an older DB file degrades instead of failing), and
one rule — `$lib/transforms/exclusion.ts:trailChip` — decides the label
for both the ΔΑΣΕ and the Anti-nero contract pages, and for the contract
list. Tone follows the fact: a cancellation and a double-posting stay
WARNING chips (something went wrong, in the procurement or in the
registry), «outside the dataset» is neutral (nothing is wrong with the
contract; it is simply somebody else's). The search-reachability rule of
2026-08-14 was widened with it — `dase_duplicate_hits` →
**`dase_excluded_hits`**, so citing either excluded ΑΔΑΜ finds its page
badged with its own reason instead of returning nothing; excluded rows
are appended after the total is summed, so they stay uncounted.
**No calculation changes**: the exclusion is still `cancelled = 1`.
Pinned by `exclusion.test.ts` (6 cases) and the real-DB API pin
`test_excluded_sibling_states_its_reason_not_a_cancellation`.

## 2026-08-17 — Scanned/odd payment documents all read by eye: 35 confirmed, 26 corrected, 4 exclusions REVERSED as proven instalments — every ΔΑΣΕ payment order is now document-checked

The closing pass of the payment audit (user: «visually read all 42»).
The 42 image-only payment PDFs were read page by page, and the sweep
then widened to every remaining text-mismatch row (39) — because the
first reads exposed a failure mode in my own earlier evidence: the
amount-token fingerprint used for the re-post exclusions CANNOT
distinguish two same-priced instalments. Every A/B exclusion was
therefore re-verified by WARRANT NUMBER and invoice citation, not
fingerprints.

**Exclusions re-verified — 4 REVERSED as genuine instalments:**
- 22SYMV010618908 (7ος ΔΑΣΕ ΠΡΟΜΑΧΩΝ ΑΛΜΩΠΙΑΣ): the two 4.000,00
  records are εντάλματα 00089/23-06-2022 and 00188/18-11-2022,
  DIFFERENT invoices (ΤΠΥ3-238 vs ΤΠΥ5-445, the second citing «λοιπά
  δικαιολογητικά στο ΧΕΠ00089») — two instalments of 2.000,00 each,
  both keyed with the contract total. Both corrected to 2.000,00.
- 25SYMV017429326 (Καρπενήσι per-tonne): the three 4.104,76-pattern
  records are THREE different warrants (01375/01693/01839) — equal
  because the παρτίδες are same-priced, not because one document was
  re-posted. Both exclusions reversed; the 6.557,12 keying on 017957804
  corrected to its document's 4.104,76; the contract's four orders now
  sum ≈ its value.
- 21SYMV009141052 (Κιλκίς): warrant 149961 cites invoice 440/19.09 — a
  SECOND 353-κ.μ. batch of συστάδα 16α, distinct from the kept
  dossier's τιμ. 429/30-08. Reversed and corrected to 7.843,66.
The other exclusions STAND, now on document identity: 8 same-warrant
re-posts share one warrant number on both PDFs, and all 7 questioned
dossier↔warrant pairs cite the SAME invoice on both documents
(τιμ. 304/305/311/316/317/435 + the Φουρνά 742,93 case) — one payment,
one record. One NEW exclusion the same way: 21PAY009327809 is the
Δασαρχείο Φουρνά transmission LETTER (πρωτ. 185042) requesting the
warrant its twin 21PAY009545629 embodies; its components 627,09 +
115,84 = 742,93 = the twin, its printed 742,53 total an internal slip.

**Confirmed (35):** the 9 Γουμένισσας 2021 dossiers (tables validate
the stored NET decomposition to the cent — work + ΦΠΑ + ΕΦΚΑ
components; the ΣΚΡΑ same-amount «pair» is τιμ. 5 vs τιμ. 6 — two real
payments); 4 of the 5 Καρπενησίου per-tonne warrants (beneficiary ΑΦΜ
matches the contract co-op in every case — the 2–8× over-estimate
payments are the measured-volume reality of per-tonne υλοτομικά, NOT
errors); the 10-order May-2025 Σπερχειάδας batch (each warrant == its
stored amount, each beneficiary on the right contract); the big rows
25PAY017371429 (117.599,95, τιμολόγιο 94.838,67 net, ΑΔΑΜ δέσμευσης
matches), 22PAY010599002/599175 (the Θέλπουσα λογαριασμοί),
22PAY011781782, 25PAY016461493 (Δήμος Έδεσσας), 25PAY017609067 (ΔΑΣΕ
ΜΟΔΙΟΥ), 26PAY019301197 (the ΔΑΣΕ ΑΡΙΣΤΟΤΕΛΗΣ invoice to ΑΔΜΗΕ:
19.395,00 + ΦΠΑ = 24.049,80), 24PAY014183233 + 24PAY014167121 (Δήμου
Πυλαίας-Χορτιάτη εντάλματα 0094Β/0078Β), 25PAY017949070 (δάκος-spray
payment to the Εύβοια co-op union), and 26PAY018727393 (two invoice
lines 19.000+1.000 net = stored exactly).

**Corrected (26 + the 3 reversal-corrections):**
- The Nov-2025 Σπερχειάδας batch (11 rows incl. no-red-flag
  26PAY018918483): payloads keyed the work pair (g = 1,24×n) while the
  warrants pay stored × 1,2014 — the ΕΦΚΑ family at the 2025 rate
  (24,97% of net). One (26PAY018918544) was ALSO visibly misattributed
  — its warrant pays ΔΑΣΕ ΠΥΡΓΟΥ-ΣΠΕΡΧΕΙΟΥ (996875099) while the
  record sat on the Κυριακοχωρίου contract — and pulling that thread
  (user: re-link it before committing) exposed the batch-wide truth:
  the registry had lumped EACH co-op's whole batch onto one of its
  contracts. The eleven batch payments pair **1:1 with the two co-ops'
  eleven live 2025 ΣΥΜΦΩΝΗΤΙΚΑ at a uniform ratio — every warrant
  total = 0,96133 × exactly one contract's stated gross, to six
  decimals across all eleven pairs** — so each payment provably
  belongs to that contract. `payment_loader.apply_corrections` gained
  an optional **`attributed_ref`** field (re-link to a stored
  contract, refused with a WARNING if the target is absent;
  `contract_ref` keeps the payload's original claim as evidence;
  unit-tested), and 8 payments were re-linked — after which every one
  of the eleven contracts carries exactly its own payment at the
  0,96133 ratio, and the apparent 3× over-payments on the two lumped
  contracts dissolve entirely. Global paid totals unchanged
  (re-attribution moves money between contracts, never changes it).
- 2 more ΕΦΚΑ understatements at the 2021 rate (≈23,7% of net — the
  Κιλκίς καταστάσεις print «ΙΚΑ ΕΡΓΟΔΟΤΗ 24,69%»), which the earlier
  generator's conservative ≤20% band had skipped.
- 16 rows stored slightly ABOVE their warrant (2,00–351,20) and 5
  slightly below it (0,15–200,00): corrected to the document.
- 25PAY017905122 (Καρπενήσι, stored 10.062,44 vs warrant 9.940,11),
  25PAY018096900 (14.454,37 vs 13.172,13), and 22PAY010424768, whose
  λογαριασμός prints the instalment as its own subtraction: 110.918,72
  − 89.450,58 = 21.468,14 (stored 21.937,86).

**Documented as noise, untouched (8):** 7 rows within ±0,60 of their
warrant and 23PAY013210185 (doc pays 4.575,00, stored 4.575,60) —
Σ |Δ| under €5 across all eight.

*Affects: paid net €20.882.632,20 → **€20.910.684,02**; paid gross →
€25.666.421,06; live orders 964 → **967** (4 reversals − 1 new
exclusion). The corrections file holds 212 payment entries. Every one
of the 1.033 stored ΔΑΣΕ payment orders is now text-verified against
its own PDF, visually verified, curated with document evidence, or
explicitly logged as sub-euro noise — the audit is CLOSED.*

## 2026-08-17 — «Paid» includes the state-borne ΕΦΚΑ (user decision): 121 understated ΔΑΣΕ payment records corrected to their warrants

Resolves the convention question the payment-audit entry (below)
parked. Under the τιμές-ανάθεσης ΚΥΑ, a ΔΑΣΕ υλοτομικά assignment
carries two components: the co-op's work price (24% ΦΠΑ) and the
employer's ΕΦΚΑ contributions for the δασεργάτες, which the State
bears as forest exploiter (0% ΦΠΑ; άρθρο 137 §3 ν.δ. 86/1969 — the
CPV 66519300-4 entry). ONE χρηματικό ένταλμα disburses both, but the
ΚΗΜΔΗΣ payment payload was frequently keyed with only the work
component. **User decision: «paid» means the whole disbursement — the
warrant total — because the stated basis already includes the ΕΦΚΑ
object lines**, so paid-vs-stated comparisons are apples-to-apples
only on that definition (the alternative left every fully-paid
υλοτομικό looking ~10–17% short forever). Flagship evidence:
21PAY009476782 stores 9.946,06/8.021,02 (exactly the work pair of
21SYMV009323424: 8.021,02 ×1,24) while its own warrant pays
#11.287,01# = work gross + the contract's itemised ΕΦΚΑ 1.340,95 to
the cent.

**121 curated corrections** in `dase_payment_corrections.json`,
three rules of descending evidence strength, the rule named in each
reason:
- **30 rows — warrant == the contract's total gross to the cent**:
  gross := the warrant, net := the contract's total net (both
  documented, no derivation).
- **75 rows — warrant = stored + an ΕΦΚΑ margin** (the consistent
  10,28%/12,8%-of-net family; the addition is the 0%-ΦΠΑ component):
  gross := the warrant, net := stored net + the same € (valid
  because all 75 stored pairs already satisfy g = 1,24×n exactly —
  asserted at generation time).
- **16 rows — net==gross keying + understatement**: the payload
  repeated the contract's work-net in both fields; gross := the
  warrant, net decomposed with the contract's own ΕΦΚΑ:work ratio
  (derived — the weakest rule, said so in each reason).

*Affects: paid figures only. Paid gross €25.527.604,84 →
€25.636.308,98 (+€108.704,14); paid net €20.793.285,13 →
**€20.882.632,20** (+€89.347,07, +0,43%). Stated basis, order count
(964) and contracts-with-payments (891) unchanged. 2 of the 18
net==gross rows have scanned PDFs and stay with the scanned pile
(separate decision). Methodology: the ΕΦΚΑ paragraph on
/methodology#dase-cpv-noise now states the paid convention.*

## 2026-08-17 — ΔΑΣΕ payment audit: every payment PDF fetched, 52 overstatement corrections (re-posted warrants + payload keying errors), paid net drops to the documented figures

Follow-up to the Δωδεκανήσου entry (below): the user asked for the
whole ΔΑΣΕ payment layer to be screened. `khmdhs.payment_validator`
ran over **all 1.033 stored payment orders** (`--db dase.sqlite
--cache dase_pdf_cache`, report
`dase_payment_validation_report.json`) — the ΔΑΣΕ payment PDFs had
never been fetched before; the cache is now complete and the .txt
sidecars are tracked like the contract ones. Statuses: 707 ok / 67
near_match / 9 ok_net_only / **250 mismatch**. The mismatches were
then classified by machine-reading every warrant PDF (the amounts
survive the cp1253 font-mangling; 42 PDFs are scanned images whose
text is only the registry stamp — those are text-unverifiable) and
testing exact arithmetic identities against the contract object
lines and the ΥΔΕ χρηματικό-ένταλμα structure (warrant total ==
beneficiary + κρατήσεις, printed twice per copy).

**Corrected NOW — the overstatements (52 curated entries in
`dase_payment_corrections.json`, all with per-row PDF evidence):**
- **11 identical-document re-posts excluded** (family A): two or
  three PAY ΑΔΑΜs whose PDFs carry byte-identical amount-token
  fingerprints — the same χρηματικό ένταλμα posted repeatedly (one
  contract, 25SYMV017429326, attached the same 4.104,76 warrant
  THREE times, once keyed 6.557,12). The earliest ΑΔΑΜ is kept, the
  re-posts get `exclude:true` + the fingerprint evidence; one kept
  row (21PAY009586451) is corrected up to its warrant total
  14.326,95, which both twins' stored 12.030,98 misstated.
- **16 same-warrant extra records excluded** (family B): a second
  ΚΗΜΔΗΣ record whose own PDF is a warrant another stored record
  already carries — typically a scanned full-amount record plus a
  later text-PDF record keyed with a component figure (work-net) of
  the same warrant. One warrant, one payment: the extra record is
  excluded, the evidence being that its own PDF's total equals the
  kept row's stored amount to the cent.
- **24 payload keying errors amount-corrected** (family C): the
  stored amount appears
  NOWHERE in the attached warrant. Flagships: 21PAY009473132 stored
  87.833,13 vs its warrant's 15.249,03; 21PAY009629348 stored
  53.212,19 vs 21.456,25; 21PAY009595559 stored 37.259,84 vs
  15.055,00; and the 25SYMV017920941 pair, where BOTH instalments
  were posted with the full contract value 97.365,01 (Σ 194.730,02 =
  2× the contract) while their PDFs itemise 84.665,22/68.278,40 net
  and 12.694,93/10.237,85 net, summing to ≈ the contract. Corrected
  to the warrant totals; where the PDF does not print the net, the
  net is derived with the contract's own net:gross ratio (documented
  per row in the reason).
The candidate universe was every live contract whose Σ non-cancelled
payments exceeded 102% of its stated gross (81 contracts,
€823.898,91 gross of apparent over-payment). Of those, 22 contracts'
payments MATCH their own PDFs and stay untouched — they are (or may
be) the legitimately-above-estimate per-unit υλοτομικά the
2026-08-03 guard-test note documents; being right per document, they
are not registry errors.

**Found, NOT corrected — pending decisions:**
- **Understatement families** (~139 rows, ≈ +€133k gross if
  corrected): warrants that pay MORE than the stored amount — the
  100-row `warrant_plus_efka` family (warrant = stored + a
  consistent 10,28%/12,8%-of-net addition, the state-borne ΕΦΚΑ
  εργοδότη component the CPV 66519300-4 entry documents), 17
  full-vs-component rows and 22 net==gross work-net rows. These are
  a DECLARATION-CONVENTION question (does «paid» include the ΕΦΚΑ
  the State disburses on top of the co-op's invoice? the stated side
  includes it, so consistency says yes), not per-row keying errors —
  parked for the user's verdict before ~139 more entries land.
- **41 unverifiable rows** on overshooting contracts: scanned PDFs
  (no text layer) or templates without the warrant marker — among
  them the 21SYMV009198626 triple (3 × 5.150,29, each matching its
  own scanned-adjacent doc) and the 23SYMV012461845 pair. Need OCR
  or manual eyes; listed in the validator report.

*Affects: ΔΑΣΕ paid figures only — stated basis untouched. Paid net
€21.211.472,57 → **€20.793.285,13** (−€418.187,44, −2,0%); live
orders 991 → **964** (27 excluded re-posts/extra records; 25 amount
corrections incl. the fix-kept row); contracts with payments stay
891 (every corrected contract keeps ≥1 live order). Post-correction
residue: 40 contracts still sum >102% of stated (€342.451,40) — the
per-unit-legitimate family plus the unverifiable scanned rows, both
documented above. Pins updated; the family-level outlier logic the
khmdhs DB has cannot be copied here (per-unit υλοτομικά legitimately
exceed stated), so the guard for THIS class is the validator report
plus the duplicate-fingerprint scan
(`scripts/find_duplicate_postings.py` remains contract-side only).*

## 2026-08-17 — Six Δωδεκανήσου contracts carried their GROSS figure in the net field: the ΔΑΣΕ net basis drops to €31.178.858,14

User caught it on /dase/contract/24SYMV015692415: the chart, labelled
excl. VAT, was showing €490.000 — a VAT-INCLUSIVE amount. It was not a
presentation bug (the Atlas net shim was doing its job); the registry
row itself carries `totalCostWithoutVAT = totalCostWithVAT = 490000`,
so the net column held the gross figure and every net-basis aggregate
inherited it.

**Scope of the error, swept:** of 2.008 live ΔΑΣΕ contracts, 2.002
carry a real VAT split (1.355 at exactly ×1,24, the rest at mixed
rates) and 0 have a null net. Exactly **6** have net == gross, and all
six are one family: Δ/νση Δασών Δωδεκανήσου, 31.10–11.11.2024, the
«Κατασκευή αντιδιαβρωτικών έργων αποκατάστασης και αντιδιαβρωτικής
προστασίας» lots for the burnt Rhodes areas, each with `vat_percent`
'0' on its single object line. The Anti-nero DB has **zero** such rows
(244 live in-scope checked), so the fault is confined to these six.

**Why they looked defensible, and what settled it.** Each signed PDF
mentions ΦΠΑ exactly once, in recital 14, and what it cites is the
EXEMPTION procedure — ΥΑ Α.1021/07-02-2022 «Διαδικασία απαλλαγής ΦΠΑ
… στο πλαίσιο αντιμετώπισης αναγκών των πληγέντων από φυσικά φαινόμενα
σε περιοχές που έχει ενεργοποιηθεί ο Μηχανισμός Κρατικής Αρωγής»
(Β΄550) — and άρθρο 5 states the price «συμπεριλαμβανομένων και όλων
των νόμιμων φορολογικών επιβαρύνσεων», boilerplate that names no rate.
Read alone, that plus `vat_percent` '0' argues the works are
VAT-exempt and net == gross is correct. The **payment orders refute
it**: every one of the six splits its contract's gross at exactly
×1,24 —
`24SYMV015692415` → 25PAY016222564 (ΑΔΑ 9ΦΞΖ4653Π8-ΘΩΩ) net
€395.161,29 on gross €490.000; …407 → 25PAY016933274 €344.722,60;
…883 → 25PAY016913049 €338.709,68; …405 → 25PAY016929629 €319.379,45;
…189 → 25PAY016944003 €302.419,36; …036 → 25PAY016924872
€302.378,08. Each payment net equals its contract's stated gross ÷1,24
to the cent, so VAT at 24% is inside the contract figure and the
exemption was cited in the legal framework without being applied to
the price. Curated into `dase_contract_corrections.json` (6 entries,
`total_cost_without_vat` + the `objects` seq-0 child row that repeats
the error; the gross column is right and stays untouched), applied by
`khmdhs.contract_corrections`. …189's payment reads €302.419,36 on
gross €375.000,01 — one cent above the contract's own €375.000,00, so
the stored figure is that contract's own gross ÷1,24 = €302.419,35,
inside the ≤€0,02 registry-noise tolerance.

No heuristic was introduced: «net == gross ⇒ divide by 1,24» would be
wrong for a genuinely VAT-exempt contract, and with six cases the
hard constraint («prefer manual curation over fragile heuristics»)
points at curation. The equality itself is now a **guard test** —
any future live contract with net == gross and no curated correction
fails the suite, so the next occurrence surfaces instead of quietly
inflating the basis.

*Affects: the ΔΑΣΕ stated-NET basis only — €31.659.523,06 →
**€31.178.858,14** (−€480.664,92, −1,5%); every Atlas pin, the
/compare ratio and the CLAUDE.md figures updated with it. The GROSS
basis (€38.411.933,17) and webui's incl-VAT presentation are unchanged
— only the net column was wrong. Paid figures unchanged: those six
payments already carried correct net amounts. Separately FOUND, NOT
fixed: 22 of 991 live ΔΑΣΕ payment rows carry `amount_without_vat ==
amount_with_vat` (21 small 2021 orders plus 25PAY016933274, whose
GROSS field holds the net €344.722,60); they inflate no net figure —
the net side is the one that reads right — but they understate the
gross paid, and payment corrections need their own PDF review.*

## 2026-08-17 — /dase CONTRACT VALUES: dots and value brackets become one frame under a toggle

CONTRACT VALUES (beeswarm) and SIZE DISTRIBUTION (log histogram) were
two frames describing ONE thing — the same 2,008 live contracts, the
same variable (stated net €), the same median, on the same
log-ish horizontal reading. Verified before merging, not assumed:
`dase_swarm` and `dase_queries.value_histogram` both filter on
`live_filter`, both read `total_cost_with_vat`, no live contract has a
null or ≤0 value (so the beeswarm's `eur > 0` guard drops nothing),
and both take the upper median of the sorted list. They are now ONE
frame (`#dase-swarm`, the beeswarm's anchor kept; nothing linked to
`#dase-hist` — checked repo-wide) with a two-button mode switch,
«Individual dots» / «Value brackets» (user's labels). Default stays
dots: no regression in what the page shows on load. The frame keeps
its place under AWARDING PROCESS, so the page reads MAP · AWARDING
PROCESS · CONTRACT VALUES · MONEY PER YEAR · RANKING OF CO-OPS ·
CPV MIX; MONEY PER YEAR keeps the half-width column it had when the
histogram sat beside it (user), the `.pair` grid now holding one child.

This is a re-ENCODING toggle, not a filter — the design doctrine's
«small multiples over filterable charts» is about hiding subsets of
data, and nothing is hidden here; the in-house precedents are the
front page's TYPES OF WORK €/count switch and the Anti-nero map's
2-mode view. Both modes render inside one `ui/SideNote` shell (the
beeswarm's 210px note column, hoisted out of `BeeswarmCanvas` so both
can use it), so the plot keeps exactly the same width and left edge in
both — measured 886 at x=394 either way. **Nothing may move when the
reader toggles** (user): the switch sits flush with the frame's RIGHT
edge with the year legend at the left of the same line, and the
brackets draw at the beeswarm's own computed height (`plotHeight`,
`$bindable` out of the dodge layout, which sizes itself to the
tallest dot column) — frame height measured identical at 623px in
both modes. The median line and its lettering are now one convention
across the pair: the beeswarm's dash (2.5px, 7/5) and centred bold
12px label, adopted by `LogHistogram` — which no other chart is
affected by, the Anti-nero direct-award histogram passing thresholds
and no median. The mode-specific explanation lives in the side note;
the frame's caveat states the one thing a reader could get wrong:
dots sit on a continuous logarithmic scale, brackets are doublings of
EQUAL width, so positions are not comparable between the two modes.

**ONE AXIS for both modes** (user, same day, second round). The two
views first disagreed on where a value sits: the median line landed
243px apart (x=880 as a dot, x=637 as a bracket position, on an 886px
plot) — not a rounding artefact but the two axes disagreeing, and
unfixable by nudging. The beeswarm's `.nice()`-ed log scale spanned
€10–€1M, while webui's bracket table gives ONE equal slot to
`[0, 1000)` — a range holding 4,5 doublings and 75 contracts — and
three empty slots to €500k–€2M. Above €1.000 that table already IS a
log axis (every edge a doubling), so the fix was to make the WHOLE
table one: `queries_extra.dase_value_histogram` now derives the edges
from the live range as pure doublings anchored on €1.000 —
`[0] + 1000·2^k` for k = −5…9 today, i.e. €31,25 → €512k, sixteen
slots. The leading `0` keeps `_bin_values`' half-open convention for
anything below the first doubling; that bracket and the trailing
overflow are empty, so the DRAWN axis is exactly the doubling span.
Edges are derived, never a fixed table, so a refresh bringing a
smaller or larger contract widens the axis by itself (pinned).
`webui.dase_queries.value_histogram` is untouched — webui is frozen
and keeps its own brackets; only the labels needed a new formatter,
webui's `_short_eur` floor-dividing every sub-€1k edge to «0k».

Client side, both charts now place a value with ONE function,
`transforms/histogram.ts:binPosition` (slot index + log interpolation
inside the slot), on identical margins — so the coincidence is
structural, not a tuned constant: measured gap 0,0px. The beeswarm
therefore drops d3's `scaleLog` entirely; with pure-doubling edges
`binPosition` IS a log scale (equal ratios ⇒ equal distances, pinned
in vitest), so nothing about the dots view is distorted — it simply
stops wasting the `.nice()` padding, and its dodge layout repacks a
little taller (464 → 548px, still under the 560 cap). The rejected
alternative was the mirror image: put the dots on webui's bracket
table, which would have crushed the 75 sub-€1k contracts into one
slot width — distorting the very view whose job is the true spread.
Two things now read the same in both modes that never could before:
the median line, and the lone €43,37 contract, which appears as one
dot and as a one-contract hairline bar at the same x. The frame's
caveat was rewritten accordingly — the «positions are not comparable»
warning is retired, replaced by the reason they now are. The computed
subtitle was deleted (user): the median is printed on the chart and
the caveat carries the basis.

**The year legend now serves both modes** (user): the brackets are
drawn as stacked segments, one per signature year, in the same ramp
the dots use (`charts/yearColors.ts`, hoisted out of `BeeswarmCanvas`
so dots, bars and legend read one table). The toggle sits on the left
of that legend line. The stacking is a real finding, not decoration —
the 125k–250k bracket is almost entirely 2021–22, so the biggest
co-op contracts are an early-programme phenomenon. Mechanism: the
segments are binned CLIENT-side from the swarm array
(`transforms/histogram.ts`) on the histogram payload's own edges,
reproducing `_bin_values`' half-open convention (`[e_i, e_{i+1})`,
overflow into the last slot) — NOT a second per-year histogram from
the API. Deriving both modes from one array is what makes it
impossible for them to drift apart; the bar COUNT labels still come
from the server's `counts`, and `LogHistogram` draws any segment
shortfall in the base colour rather than hiding it, so a divergence
would be visible as well as caught by the pin. Cost of the choice,
accepted: the brackets view now waits for the swarm fetch instead of
rendering from the SSR payload — it is behind `Defer` and is not the
default mode.

`LogHistogram` gained `height`, `segments` and `segColors`, all
defaulted so the Anti-nero direct-awards histogram is untouched. The
same review fixed a defect that predated this work: reference-line
labels (median, the ν.4782 ceilings) and the bar-count labels were
drawn in the SAME band, so a median falling near the modal bar
overprinted that bar's count — as it did here (median €5.792 in the
modal 4k–8k bracket). Reference labels now get their own row above
the counts; the Anti-nero €30k/€60k threshold labels improve with it.
*Affects: presentation + the /dase histogram EDGES on the Atlas side
(`queries_extra.dase_value_histogram`, webui's untouched); no DB or
loader change. Pins `test_dase_value_modes_are_one_population`
(histogram n == swarm length == KPI count; swarm binned on the payload
edges == the server's counts; every contract carries a year, so the
segments sum to the bar totals with no uncategorised remainder; every
drawn bracket exactly one doubling; €1.000 on an edge; the first
doubling holds the smallest live contract and the last the largest;
catch-all and overflow empty) plus 11 vitest units on the binning
convention and on `binPosition` being a true log scale.*

## 2026-08-17 — Το CPV 66519300-4 στα ΔΑΣΕ υλοτομικά ΔΕΝ είναι keying noise: σημαίνει τις κρατικά χρηματοδοτούμενες εργοδοτικές εισφορές ΕΦΚΑ των δασεργατών

The site had characterized the insurance CPV 66519300-4 «Επικουρικές
ασφαλιστικές υπηρεσίες», found on 386 ΔΑΣΕ υλοτομικά contracts (378
live), as a "mass registry keying error" (dase_queries.py NOISE_CPVS
comment, /dase CPV MIX caveat + row suffix, /dase contract-page chip,
/methodology#dase-cpv-noise, webui pill). A user-prompted investigation
(2026-08-17) disproves the keying-error reading on two independent
grounds:

- **Registry payloads**: 207 of the 386 flagged contracts carry a
  dedicated object line named «ΕΡΓΟΔΟΤΙΚΕΣ ΕΙΣΦΟΡΕΣ» / «ΑΣΦΑΛΙΣΤΙΚΕΣ
  ΕΙΣΦΟΡΕΣ (ΕΦΚΑ/ΙΚΑ ΕΡΓΟΔΟΤΗ)» — and in ALL 207 the CPV sits exactly
  on that line, never on the works line. The other 179 are
  single-object «ανάθεση υλοτομικών εργασιών με αυτεπιστασία
  αποκλειστικά σε δασικούς συνεταιρισμούς» awards whose one object
  carries the trio 77211100-3 / 77211300-5 / 66519300-4; 173 signed
  PDFs print the same trio in their own text — a deliberate,
  systematic convention across five years and both awarding
  authorities, not a slip.
- **Legal mechanism**: the annual τιμές-ανάθεσης ΚΥΑ (e.g.
  ΥΠΕΝ/ΔΔΔ/128526/4106/2022, Β΄ 6472) provides «Στις παραπάνω τιμές
  δεν περιλαμβάνεται η εργοδοτική εισφορά υπέρ ΕΦΚΑ των δασεργατών, η
  οποία επιβαρύνει τον εκμεταλλευτή του δάσους», and for δημόσια δάση
  exploited με αυτεπιστασία the State bears that employer contribution
  (άρθρο 137 §3 ν.δ. 86/1969· άρθρο 48 ν.4423/2016). The awarding
  authority therefore budgets the εισφορές as a separate component of
  each award and classifies it under the nearest insurance-family CPV.

Decision: **analytics unchanged** — the contracts remain υλοτομικά,
nothing aggregates by CPV, and the code stays flagged wherever CPVs
are shown so the CPV mix is never read as procured insurance services.
All copy is recharacterized from «registry keying noise/error» to
«state-funded ΕΦΚΑ employer-contributions component»: the
dase_queries.py comment (the NOISE_CPVS constant and the `noise`
payload field are API surface and keep their names), the /dase CPV MIX
caveat + row suffix, the /dase contract-page chip (warn → neutral
info chip), /methodology#dase-cpv-noise (anchor id kept, heading/body
rewritten as the public explanation), the frozen webui's pill
label/tooltip (minimal text-only correction — a knowingly false
factual claim must not stay served; no queries touched), and the
CLAUDE.md ΔΑΣΕ note. *Evidence: raw_json objectDetailsList of all 386
flagged contracts; 173 dase_pdf_cache txts printing the CPV trio; the
ΚΥΑ text (verbatim above). Affects: no rows, no aggregates — copy and
documentation only.*

## 2026-08-17 — /dase: the category share bars retired, AWARDING PROCESS carries the whole story

Closing decision on the entry below (user): the AWARDING BODIES and
AWARDING UNITS share-bar frames are REMOVED — the three-column
AWARDING PROCESS diagram states the same categories, in the same
colours, with the same n/€ (bars sized by €, counts on hover), and
saying it twice on one page earned nothing. AWARDING PROCESS moves up
to sit directly under the MAP (user), so the page reads WHERE the
work is, then WHO commissioned it through whom, before the value
distributions: MAP · AWARDING PROCESS · CONTRACT VALUES · MONEY PER
YEAR · SIZE DISTRIBUTION · RANKING OF CO-OPS · CPV MIX. It renders
eagerly rather than behind a `Defer` like the beeswarm — its data
already rides in the SSR overview payload and the SVG is ~50 marks. The `#dase-orgs` / `#dase-units`
anchors disappear with their frames (nothing linked to them —
checked); `#dase-delegation` keeps the `org-names` methodology link.
The `kind_mix.bodies` / `.units` MARGINALS stay in the payload
although no chart reads them now: they are the reconciliation guard
the real-DB pins assert against (Σn = 2,008, Σ€ = basis, and the
units marginal == the /dase map's own circle classification), which
is a data-integrity check independent of any UI. Dead page code went
with the frames (StackedShareBar import, UNIT_KINDS, kindSegs /
kindShare / kindKey, the two computed findings, ~1.7 KB of CSS);
`StackedShareBar` itself stays — /anadohoi's scope/type pair uses it,
including the `fmt`/`outside` props added for the retired bars.

## 2026-08-17 — /dase AWARDING BODIES / UNITS: top-10 lists become category share bars

Presentation decision (user request, modelled on the /anadohoi PROJECT
SCOPE / PROJECT TYPE pair). The two /dase top-10 BarH rankings hid the
dataset's institutional story, which categories tell directly: the
decentralized administrations sign ~17% of the contracts but ~39% of
the money (the big fire-salvage batches), and δασαρχεία are the
working level (~81% of contracts). Replaced by two `StackedShareBar`
pairs — each frame shows a CONTRACTS bar over a € NET bar with
identical segment order and colours (user chose the two-measure
layout over a single-count bar) — AWARDING BODIES by public-bodies
registry kind (grey ramp, smallest first; municipal entities counted
with their municipalities — same municipal scope tier), AWARDING
UNITS by the map's four kinds in the map's own colours, so the bar
doubles as a legend echo. Layout follows the sponsored-works pair
exactly (user): the two frames STACK full-width (never side by side)
and the bars run at the same 3/4 content width — measured identical
at 840 px / fs-16 labels on both pages. With 5–6 categories the
component's spill labels for narrow segments overlapped into soup, so
each frame carries ONE shared key instead (both bars have the same
categories/colours) listing every category with its exact n and € —
`StackedShareBar` gained `outside={false}` for that, alongside the
`fmt` badge formatter; the anadohoi bars keep both defaults and render
unchanged.

**Third frame — WHO AWARDS THROUGH WHOM** (user request: the two
categories are connected, «would a diagram like the money flow work
here?»). Yes: the joint distribution is NOT block-diagonal, and the
crossing is the finding — ministries AND decentralized administrations
both award through δασαρχεία, at **€36.3k vs €8.3k per contract, a
4.4× gap** on €23.0M of work, which neither marginal bar can show. A
three-column d3-sankey (`KindFlow.svelte`, new — the Anti-nero
`Sankey.svelte` is hardwired to scope colours/phase labels/contractor
links and stays untouched): **awarding bodies → operating units →
contractors**, ribbon width = stated net €, coloured by the receiving
unit so the map palette carries; the per-contract average is printed
ON the ribbons entering the middle column (the finding must not hide
in a tooltip); hovering a node dims the rest; co-op nodes link to
their pages.

Column decisions (user, 2026-08-17): (1) the middle column collapses
the two non-forest kinds into ONE node «the body's own services» —
«regional or municipal authorities» merely repeated what column 1
already says, and «other public bodies» was positively WRONG there:
the ministry→misc hairline is the Ministry of Culture's Ephorates of
Antiquities (Platamon Castle vegetation clearing ×3, Chalkidiki sites)
and the Air Force's ΓΕΑ/ΑΤΑ/350ΠΚΒ — units OF the awarding ministry,
not other bodies. The AWARDING UNITS bar keeps the map's four kinds
(it is the map-legend echo); the merge is a sankey-only presentation
choice, stated in the caveat. (2) The third column shows the 10
biggest co-ops by € plus one pooled «N other co-ops» node (top-10 =
29.9% of €, so the pool is honestly the fat one); entity level for
bodies/units was rejected as spaghetti (49 orgs / 101 units, ΥΠΕΝ
alone 1,543 of 2,008). A consortium contract (19 live) counts once, at
the co-op listed first, so all three columns reconcile to the basis.
Presentation rounds 2-4 (user review of the rendered chart): the
frame is titled **AWARDING PROCESS**; the computed subtitle is
DROPPED; each column heading centres on that column's coloured bar;
labels WRAP instead of truncating, but ONLY in the left column (20
chars — the width that splits «decentralized administrations» while
keeping «other public bodies» on one line): its 5 nodes sit far apart,
so two rows there cost no height, and the narrow left margin (132px)
lets the whole plot sit off-centre to the LEFT, paying for a 380px
right margin. Middle and right labels therefore stay on ONE line —
every co-op name prints in full (widest 339px) at the ORIGINAL 660px
height, with no truncation and no ellipsis. (Wrapping the 11-node
right column instead was tried and reverted: it forced nodePadding 44
at height 790, past a screenful — the user's rule is that the whole
graph must be readable at once.) Columns are VERTICALLY CENTRED on each other (user): all three carry
the same € total, so they differ only in how much padding their node
count adds, and d3-sankey packs each from the top — leaving the 5-
and 3-node columns riding high against the 11-node one. A post-layout
pass shifts each column's extent onto the plot's middle and moves
every link end with the column it touches, so ribbons still meet
their nodes (verified: the three column centres coincide to 0px).
Column headings are drawn at a fixed y and deliberately do NOT move.
Width reference is the MAP row (map 600 + legend 504 = the frame's
full 1120 at x=80), NOT the beeswarm — whose canvas is only 886 at
x=314 because a 210px side-note column eats its left edge, making it
the page's outlier. The flow chart therefore spans the full frame
width, its explanation in the ChartFrame caveat like the map's;
`KindFlow` keeps an optional `note`/`methodologyHref` pair that
switches on the beeswarm's two-column shell, unused here. Geometry is
verified by comparing every rendered label box against every other,
ignoring the line pairs belonging to one label; the pooled «other
co-ops» node takes the same
green as the named co-ops (a different colour read as a different
kind of contractor), and ribbons are coloured by whichever endpoint
is the UNIT column so the map palette still carries in the second
stage, where every target is green. **The per-contract averages are
REMOVED from the chart entirely** (round 3): printed on a ribbon they
read as ambiguous twice over — «36,3 K € per contract» sounds like a
recurring rate rather than the typical contract size on that route,
and the rule that only ribbons entering the middle column AND wide
enough to hold the text got one made the choice look arbitrary from
the outside. The chart now encodes ONE measure, €, as bar and ribbon
width, printed beside each bar. The black hover card fires on the
BARS only and carries the single number the chart does not print —
the contract count. (Consequence recorded honestly: the
ministry-vs-ΑΠΔ scale gap is no longer stated anywhere on this frame;
it survives in the AWARDING BODIES bars above, where the contracts
and € rows diverge, and in this log.) Same review fixed a rule
violation of my own making: the caveat had quoted «36,3 K €» and
«8,3 K €» as literals — data-derived numbers hardcoded in UI copy,
which the hard constraint forbids; the rewritten caveat carries none.
Rendering
review caught three defects invisible in code: d3-sankey throws on an
empty graph and makes NaN geometry for links naming absent nodes (the
component now degrades to drawing nothing), the on-ribbon annotations
were centred on the plot and so landed on the middle column's labels
(now placed at each ribbon's own inter-column midpoint), and the
middle labels had to move above their nodes to leave the corridor
clear.
Mechanism: `queries_extra.dase_kind_mix`
derives bars AND flows from ONE per-contract pass (`_dase_kind_rows`),
so they can never disagree: the unit decision mirrors the map's circle
kinds (`_unit_forest_kind` lifted to module scope and now shared with
`dase_map`; rows the map leaves unplaced for lack of a Π.Ε. — the
multi-Π.Ε. ΑΔΜΗΕ contracts — fold into «other public bodies»), bodies
resolve through `public_bodies.kind` via the alias table (municipal
entities counted with municipalities). Ships as `kind_mix` on
`/api/dase/overview`. Registry-unknown orgs would land in an
`unknown` bucket that the real-DB pin asserts absent. Top awarder names
stay reachable (computed subtitle, map click panels, co-op pages).
*Affects: presentation + additive API fields (`kind_mix` with
bodies/units/flows/coops/coop_flows); pins `test_dase_kind_mix_pins` —
Σn = 2,008 and Σ€ = basis on the bars, the body→unit flows AND both
co-op layers, closed vocabularies, the ≥3× δασαρχεία gap, every named
co-op carrying a curated display name, at least one top co-op served
only by non-forest bodies, and a cross-check that the units marginal
equals the /dase map's own circle classification.*

## 2026-08-18 — Jointly signed ΔΑΣΕ contracts are split EVENLY between the co-ops, not credited whole to each

User decision, on the last inflation left in the co-op figures: «are you
assigning the whole amount of the contract to both ΔΑΣΕ ΠΕΤΡΟΛΟΦΟΥ
[096121014] and ΔΑΣΕ ΣΙΔΗΡΟΧΩΡΙΟΥ [096067226]? because that would be
inflating the numbers again!» — we were, and it did.

**The case.** 23SYMV013747204 (Δασαρχείο Αλεξανδρούπολης, 18.09.2023,
€5.383,95 net) is the ONE live contract signed by two co-ops. Its PDF
names «ο Ισταμπόλ Χασάν & Πυρελή Χουσεΐν, νόμιμος εκπρόσωπος του ΔΑ.Σ.Ε.
Σιδηροχωρίου & Πετρολόφου (ΑΦΜ 096067226 & 096121014)», who
«**συμφώνησαν από κοινού**» over ONE pooled quantity — 250,3 χ.κ.μ. oak
at unit prices (9,27 €/χ.κ.μ. υλοτομία, 12,24 €/χ.κ.μ. μεταφορά). No
share appears in the contract, in the award or in the registry, and the
contract has no payment orders to disambiguate.

**Rule.** The Atlas splits such a contract EVENLY between its partners on
every per-co-op surface — the ranking, /dase/coops, and the co-op page's
summary, per-year bars and per-awarder table. The Anti-nero
maximum-exposure convention (2026-05-09) is untouched; this is the ΔΑΣΕ
side only, and the site footer plus /methodology now state both. The
split is the same convention the region maps and `pipelines` already use.

**Why even, not something else.** «Από κοινού» with one representative
per co-op is as close as the document comes to declaring a share, and an
even split is the only rule that keeps per-co-op totals ADDABLE: they now
sum to the live basis €30.881.588,14 exactly, where full attribution
summed to €30.886.972,09 — €5.383,95 of double counting. Contract COUNTS
stay whole (each co-op does hold the contract, jointly), and the contract
keeps its own stated value everywhere, with the co-op's `share_eur`
printed beside it on the co-op page and explained in a footnote.

**Mechanism** (`atlas_api/queries_extra.py`, webui frozen):
`dase_coop_shares` finds live contracts with >1 distinct canonical ΑΦΜ and
allocates whole CENTS (`_even_cents` — the odd cent goes to the first
partner by ΑΦΜ, so halving €5.383,95 loses nothing and the allocation is
stable); `dase_coops` / `dase_coop_detail` give the over-credit back.
Gotcha found and fixed while building it: the per-awarder table groups by
(unit, org) and the same Δασαρχείο appears under both ΥΠΕΝ and its
Αποκεντρωμένη, so matching the shared contract on the unit NAME alone
subtracted the share TWICE; every breakdown must sum to the co-op's own
total, and that is now a test.

*Affects: ΔΑΣΕ ΣΙΔΗΡΟΧΩΡΙΟΥ €138.766,86 → **€136.074,89** (share
€2.691,98), ΔΑΣΕ ΠΕΤΡΟΛΟΦΟΥ €68.993,53 → **€66.301,55** (share
€2.691,97); Σ co-op € now == the basis. No KPI, chart of contracts, map
or payment figure changes — the contract itself is untouched. Pinned by
`test_coop_totals_are_even_split_and_sum_to_the_basis` (real DB) and four
unit tests incl. the double-subtraction guard.*

**Same-day companion fix.** 25SYMV016837212 (excluded 2026-08-17 as
not-a-co-op) still LISTED ΔΑ.Σ.Ε. ΜΟΔΙΟΥ as a contractor on its page,
because the exclusion only removed it from the calculations. The registry
row is a paste of the parent award's awardee list; the signed contract
names Α.ΑΡΑΒΙΔΗΣ – Ι. ΜΠΑΛΙΚΑΣ Ο.Ε (ΑΦΜ 999030521) alone. The curated
correction now carries `contractors_keep: ["999030521"]`, so the co-op
row is deleted and no page presents ΜΟΔΙΟΥ as a party to a contract it
never signed — it keeps its own lot, 25SYMV016885520. The real-DB test
that every stored contract has a curated co-op contractor now exempts
`related_to` rows explicitly (that claim is exactly what those exclusions
disproved). 25SYMV017324270 carries the same defect — its record lists
all eleven framework operators, one of them ΔΑΣΕ ΔΟΛΙΑΝΩΝ — and is left
given the same treatment right after (user: «ok do it»): award
25AWRD017318485 produced THIRTY sibling contracts, one per framework
operator, and ΔΟΛΙΑΝΩΝ's own is the stored, live **25SYMV017325165**
(30.07.2025, €4.875 net, the co-op its sole contractor). So the excluded
record now carries `contractors_keep: ["094311510"]` — the ten
non-signing rows deleted — and `related_to: "25SYMV017325165"`,
correcting the `""` I curated on 2026-08-17: I had recorded that no co-op
contract existed in this procurement, when one does. Nothing counted
changes (the contract was already excluded); the page simply stops
listing eleven parties it never had and now links the co-op's real
contract.

## 2026-08-18 — Awardee review, batch B: four contracts whose signed PDF names no co-operative leave the ΔΑΣΕ population

`scripts/audit_contract_awardees.py` screens every stored contract's
registry contractor list against the ΑΦΜ its signed PDF announces. Of the
2.164 contracts it flags 96 for human review; this entry closes the first
13 (the 11 `vat_mismatch_name_ok` + the 2 `over_attributed`).

**The root cause of the batch**: nine contracts carry **090273987** — the
ΑΦΜ of the **Ελληνικό Δημόσιο**, i.e. the AWARDING side — in their
contractor ΑΦΜ field. Because co-ops key on the canonical ΑΦΜ, those nine
fused into one fictitious co-op that the ranking presented as «ΔΑ.Σ.Ε.
Ο.Υ.Κ. ΔΗΜΟΥ ΚΑΣΤΟΡΙΑΣ», 9 contracts, €49.145 net. Four of the nine are
not co-op contracts at all and are EXCLUDED here (user verdict: «for the B
GO AHEAD»); the five that are real co-op contracts under a mis-keyed ΑΦΜ
are batch A, still open.

**Excluded (`exclude` + `related_to: ""`), each quoting its PDF:**
- **23SYMV013066418** €15.322,00 — Δασαρχείο Αλιβερίου hires a privately
  owned CAT 966C loader from the earthmover Ιωάννης Μιχ. Καλόγηρος «αντί
  τιμήματος παραγωγικής ώρας». Machine hire from an individual.
- **23SYMV013322265** €5.610,00 — a stand-rental agreement for the forest
  pavilion at the 87th Thessaloniki International Fair with «Δ.Ε.Θ.-HELEXPO
  A.E.», ΑΦΜ 099356797. Named as ΔΕΘ-HELEXPO in the registry too.
- **24SYMV015485196** €1.048,39 — «Α.Δρόσος & ΣΙΑ ΟΕ», ΑΦΜ 082356387.
- **24SYMV015682407** €645,16 — «Τοφέα Αναστασία (Αλουμινοκατασκευές -
  Σιδηροκατασκευές)», ΑΦΜ 133510498, awarded by 24AWRD015613805.

None of the four names a co-op even in the registry: they entered this
contractor-led dataset solely through the State ΑΦΜ. 23SYMV013066418's
payment order 23PAY013718656 (€18.748,80 net) is excluded with it, because
the paid KPI sums payments without joining to contracts.

**Also examined, no action:** the two `over_attributed` flags are
wrong-PDF uploads, not attribution errors — 24SYMV016100355 has a
Βιοστερεά Α.Ε. composting contract attached, but its award act
24AWRD016046059 awards «Κλάδεμα μεγάλων δένδρων» to the co-op for
€13.640 incl. ΦΠΑ = the stored €11.000 net exactly, so the metadata is
right and the attachment wrong; 22SYMV011841987 is a cancelled posting
carrying the Βαρβάρας document while its live siblings (Κρυονερίου,
Βαρβάρας, Αγιόκαμπου) are each correct. 24SYMV014934504 and
23SYMV012239508 are extractor artefacts (the PDF's only labelled ΑΦΜ is
the awarder's; registry name and ΑΦΜ agree), and 23SYMV013747204 is the
jointly signed contract split earlier today.

*Affects: ΔΑΣΕ live population **2.006 → 2.002**, stated net
€30.881.588,14 → **€30.858.962,59**, gross €38.043.318,37 →
€38.015.262,69; paid net €20.728.414,02 → **€20.709.665,22** and 962 →
961 orders; n_cancelled 94 → 98; /compare ratio ≈21,4×. The phantom
090273987 co-op still holds the five batch-A contracts (€26.520) pending
that verdict. All four excluded pages stay reachable and badged «outside
the dataset».*

## 2026-08-18 — Awardee review, batch A: six contractor ΑΦΜ the signed contracts prove wrong; the Greek State stops being a co-operative

The other half of the 090273987 finding (batch B, same day). Five
contracts are genuine co-op contracts whose registry ΑΦΜ field is simply
wrong, and a sixth has a doubled digit. Co-ops key on the canonical ΑΦΜ
and NEVER on the name — deliberately, because the registry spells one
co-op three or more ways — so a wrong ΑΦΜ does not mislabel a row, it
files the contract under a different entity.

**Rewritten (`contractors_vat`, user verdict «yes on the five»):**
- **24SYMV015522552 / 015522664 / 015522837** (€8.156,23 / €6.868,42 /
  €4.161,29) — «…κ. Ζυγούρας Αθανάσιος, ως εκπρόσωπος του Ελληνικού
  Δημοσίου με Α.Φ.Μ. 090273987 … και β) Η κα. Πρωτόγερου Ελευθερία,
  πρόεδρος και νόμιμος εκπρόσωπος του ΔΑ.Σ.Ε. Ο.Υ.Κ. ΔΗΜΟΥ ΚΑΣΤΟΡΙΑΣ …
  και **Α.Φ.Μ 997106874**». The clerk copied the FIRST party's ΑΦΜ.
- **24SYMV015532758** (€5.975,32) — «Ο κ. Νίκας Απόστολος … του ΔΑ.Σ.Ε.
  ΠΕΥΚΟΦΥΤΟΥ ΝΕΣΤΟΡΙΟΥ … και **Α.Φ.Μ 096064168**».
- **25SYMV017124601** (€14.045,60, ΑΔΜΗΕ) — a different fault: the field
  holds «**0960988227**», TEN digits. The canonical rule takes the first
  nine (096098822), an ΑΦΜ belonging to nobody, so the contract sat on a
  one-contract ghost. The PDF names «ΔΑ.Σ.Ε. ΑΓ. ΚΥΡΙΑΚΗΣ-ΠΑΛΑΙΟΓΡΑΤΣΑΝΟΥ
  - ΕΛΑΤΗΣ … **Α.Φ.Μ 096098227**»; the 099877486 beside it is ΑΔΜΗΕ's own.
- **23SYMV013711668** (€1.358,52) — resolved on the NAME, user-approved
  and flagged as such: this PDF prints no ΑΦΜ at all (6.259 characters,
  not one). Five Σιδηρονέρι co-ops appear in the dataset (Η ΕΛΑΤΙΑ
  096095618, Η ΡΟΔΟΠΗ 096156917, Η ΕΝΟΤΗΤΑ 999522306, one titleless
  096133603, **Η ΟΜΟΝΟΙΑ 999888341**) and only the last carries the
  registry row's title, spelled identically. Inference from a unique
  name, not proof from the document — recorded in the entry's `reason`.

**Mechanism added**: `contractors_vat` in `khmdhs.contract_corrections`
— {registry ΑΦΜ → the ΑΦΜ the PDF states}, matching a row verbatim or as
a 9-digit run inside it (so the ten-digit typo is addressable), targets
validated as nine digits, unmatched keys logged and never invented,
idempotent. Unit-tested incl. the refusal path.

Both phantom identities also left the curated files —
`dase_contractors.json` (260 → 258 loaded rows) and
`dase_display_names.json` (249 → 247) — because the display-name file
must stay bijective with the live co-op population (pinned).

*Affects: NO money enters or leaves — the basis stays €30.858.962,59 and
the population 2.002. The euros move to the co-ops that earned them:
Ο.Υ.Κ. Δήμου Καστοριάς 7 → **10 contracts, €49.226,26**; Πευκοφύτου
Νεστορίου 1 → **2, €15.476,94**; Αγ. Κυριακής-Παλαιογρατσάνου-Ελάτης
9 → **10, €88.154,99**; Σιδηρονέρου «Η Ομόνοια» 24 → **25,
€179.972,17**. n_coops 249 → **247** — the fictitious «ΔΑ.Σ.Ε. Ο.Υ.Κ.
ΔΗΜΟΥ ΚΑΣΤΟΡΙΑΣ [090273987]» (which was the Greek State) and the ghost
096098822 are gone. Σ co-op € still reconciles to the basis exactly.*

**Noted, not corrected — the registry's incl-ΦΠΑ figures on ΕΦΚΑ
contracts.** Checking 24SYMV015522664 against its own price table (user
question) showed three totals: the registry net €6.868,42 = the table's
ΦΠΑ-free total (ΥΛΟΤΟΜΙΚΑ 8,78 + ΕΦΚΑ 1,20 + ΜΕΤΑΦΟΡΙΚΑ 10,98 + ΕΦΚΑ
0,50 = 21,46 €/χ.κ.μ. × 320 = 6.867,20, the €1,22 gap being per-unit
rounding) — so the figure the Atlas uses is document-correct; the
registry's gross €8.516,84 = net × 1,24, which VATs the employer's ΕΦΚΑ
although the contract's own table charges ΦΠΑ only on ΥΛΟΤΟΜΙΚΑ +
ΜΕΤΑΦΟΡΙΚΑ (its printed unit price 26,20 €/χ.κ.μ. × 320 = €8.384,00);
and the prose ceiling «θα ανέλθει ΕΩΣ του ποσού των 8.677,00€», ~3,5%
above the table. 380 live contracts carry the ΕΦΚΑ CPV 66519300-4 and
174 show gross == net × 1,24 exactly, so the registry's blind
multiplication is systematic. The Atlas presents net everywhere, so no
KPI, chart or ranking is affected — only the secondary «incl. ΦΠΑ»
caption on those contract pages. Left as the registry's own figure
rather than parsed per contract (the parse would be exactly the kind of
fragile rule this project avoids); revisit if the gross ever becomes
load-bearing.

## 2026-08-18 — Awardee review, `missing` class: 45 flags, zero corrections — and the scanner learns the public-bodies registry

The third class of the 96 (`missing` = the signed PDF announces a party
ΑΦΜ the registry's contractor list does not contain). Triaged by asking
what each ΑΦΜ IS, against the two curated vocabularies the project already
maintains: 43 of the 45 are **public bodies** — the awarding side, which
can never be the contractor. The audit already suppressed awarding ΑΦΜ,
but only those appearing on ≥5 contracts (a deliberate threshold: a few
co-op ΑΦΜ sit in `organization_vat` by registry error and a blanket rule
hid the very rows the audit exists to find). A δήμος that awarded two
contracts fell through and read as a missing contractor on its own
contracts.

**Fix**: the audit now also treats every ΑΦΜ in the curated
`public_bodies` registry (67 awarding bodies, ΑΦΜ curated per entry) as
an awarding ΑΦΜ. A public body is never a forest co-op — the two curated
vocabularies are disjoint by construction — so this can hide nothing the
audit looks for. The class collapses **45 → 2** and `ok` rises 403 → 446.

**The two survivors, both dismissed after reading the documents:**
- **26SYMV019333598** (€53.032,65, Εφορεία Αρχαιοτήτων Χαλκιδικής): the
  registry's contractor 996854516 «ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ
  ΒΟΡΕΙΝΟΥ ΑΛΜΩΠΙΑΣ ΤΟ ΠΑΛΙΟ ΠΕΥΚΩΤΟ» is exactly the party the contract
  names. The second co-op ΑΦΜ (096085938 ΝΕΟΧΩΡΙΟΥ ΑΛΜΩΠΙΑΣ) appears in
  the integrity-clause annex as **υπεργολάβος** providing «δάνεια
  στήριξη» for the άρθρο 2.2.6 capacity requirement — a subcontracting
  relation between two co-ops, not a second contracting party. Recorded
  here because it is the first such case seen; the dataset has no
  subcontractor layer and does not claim one.
- **25SYMV016635078** (€6.000, Δήμος Ν. Προποντίδας): parties are the
  δήμος and ΔΑΣΙΚΟΣ ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΠΟΛΥΓΥΡΟΥ 096034649, both as stored.
  The flagged 073576903 comes from the **digital-signature footer**
  («Πατρώνυμο: ΧΡΗΣΤΟΣ … ΑΦΜ: 073576903 Ημ. Υπογραφής») — the natural
  person who signed the file, not a party.

*Affects: no data. Review status of the 96: `over_attributed` (2) and
`missing` (2) dismissed with reasons, `vat_mismatch_name_ok` down to 4
rows that are all already corrected or excluded — **41 scanned
`no_text` contracts (€558.134,10 net) remain**, needing visual reads
like the 42 payment documents of 2026-08-17.*

## 2026-08-18 — Awardee review CLOSED: the 41 scanned contracts all check out; every ΔΑΣΕ contract's party is now verified

The last class of the 96. These contracts have no text layer, so the
registry's contractor claim could not be screened mechanically. Two
methods, in this order:

**1. Cross-check against a TEXT-bearing act of the same procurement**
(the award, notice or request — the parity harvest of 2026-08-03 cached
them all). **29 of 41 confirmed**: 13 by the co-op's own ΑΦΜ printed in
the award, 16 by a distinctive fold of its name (generic tokens —
ΔΑΣΕ, ΣΥΝΕΤΑΙΡΙΣΜΟΣ, ΕΡΓΑΣΙΑΣ, ΑΓΙΟΥ … — are stop-listed, so a match
means the toponym or the co-op's title, never the legal form).

**2. Read by eye** — the remaining 12, whose acts are scans too. All
twelve name the registry's co-op: ΔΑ.Σ.Ε. «Η Δρυς» Σοχού, Βερτίσκου-
Όσσας (×2, one of them the already-excluded duplicate's twin), Κλειτσού
(the document spells it «Κλειστού»), Πετρολόφου (**with ΑΦΜ 096121014**
printed), Αγίου Δημητρίου, Λιβαδίου, Φωτεινών, Βρύας-Ρητίνης,
Καταλωνίων, Βώλακα «Αγ. Παύλος». The Πιερίας ΣΥΜΦΩΝΗΤΙΚΑ name their
co-op in the εγκατάσταση recital and the closing party clause but print
no ΑΦΜ at all — the same document habit that made 23SYMV013711668
unresolvable from its own text.

**Zero corrections.** *Affects: no data.*

**The 96 in full, closed:** 13 in the first pass (6 ΑΦΜ rewrites, 4
exclusions, 3 dismissed), 45 `missing` → 2 dismissed after the audit
learned the public-bodies registry, 41 scans verified. Of 2.164 stored
contracts the screen produced **10 real defects** — 6 mis-keyed
contractor ΑΦΜ and 4 contracts belonging to nobody's co-op — plus 2
wrong-PDF uploads and 1 subcontracting relation worth knowing about. The
scanner (`scripts/audit_contract_awardees.py`) stays as the guard: it is
re-runnable after any harvest and now reports `ok` for 446 contracts
that state their party in text, `no_party_vat` for the 1.669 whose
documents name no ΑΦΜ beyond the authority's, and nothing else.

## 2026-08-18 — ΑΦΜ 096000173 «Ένωση Δασικών Αγροτικών Συνεταιρισμών Εύβοιας» is not a ΔΑ.Σ.Ε.: out of the registry, its four contracts out of the dataset

User determination, and the largest single scope correction of the
dataset so far. The entity is a **second-tier UNION of forest-AGRICULTURAL
co-operatives**, not a δασικός συνεταιρισμός εργασίας of ν.4423/2016 —
which is what this contractor-led dataset collects. It entered the
curated registry in the 2026-07-26 name review, where the proposal regex
saw «ΔΑΣΙΚΩΝ … ΣΥΝΕΤΑΙΡΙΣΜΩΝ» and the reviewer accepted it.

**The work confirms the legal form**: all four contracts are for
Περιφέρεια Στερεάς Ελλάδας / Δ/νση Διοικητικού-Οικονομικού Π.Ε. Ευβοίας,
under **CPV 77100000-1 «Γεωργικές υπηρεσίες»** and **18930000-7 «Σάκοι
και τσάντες»** — no forestry CPV anywhere:
- **22SYMV011776665** €471.626,10 — «ΔΟΛΩΜΑΤΙΚΟΣ ΨΕΚΑΣΜΟΣ ΕΛΑΙΟΔΕΝΤΡΩΝ
  Π.Ε. ΕΥΒΟΙΑΣ ΤΜΗΜΑΤΑ Α & Γ» (olive-fly bait spraying, δακοκτονία)
- **24SYMV015723933** €354.255,00 — the same, ΤΜΗΜΑ Γ (Δήμος Ιστιαίας –
  Αιδηψού)
- **24SYMV015377780** €112.194,00 — the same, ΤΜΗΜΑ Β (Δήμος Μαντουδίου –
  Λίμνης – Αγ. Άννας)
- **23SYMV012666888** €329,03 — «Προμήθεια Σάκων για τις ανάγκες
  διενέργειας των προσεχών βουλευτικών εκλογών της 21ης Μαΐου»

Removed from `dase_contractors.json` and `dase_display_names.json`; the
four contracts excluded via `exclude` + `related_to: ""` (pages stay
reachable, badged «outside the dataset», each carrying this reason); their
**8 payment orders excluded** with them, because the paid KPI sums
payments without joining to contracts.

**A pin caught the meaning of this before I did.** `test_dase_kind_mix_pins`
asserted that one top-10 co-op is hired ONLY by non-forest bodies — that
co-op was this Ένωση, 5th-largest by €, served solely by a Περιφέρεια.
With it gone the assertion is now inverted and strengthened: **every**
top-10 co-op must be hired by at least one δασαρχείο or διεύθυνση δασών,
so a future top-10 entity that no forest service ever hires trips the
suite and gets a human look — exactly the smell that identified this one.

*Affects: ΔΑΣΕ live population **2.002 → 1.998**, stated net
€30.858.962,59 → **€29.920.558,46** (−€938.404,13, the largest single
correction: 3,0% of the basis), gross €38.015.262,69 → €36.954.829,83;
paid net €20.709.665,22 → **€20.405.695,74**, 961 → 953 orders, 897 → 893
paid contracts; n_cancelled 98 → 102; co-ops 247 → **246**; curated
directory 258 → 257 rows. /compare ratio ≈22,0×. Π.Ε. Ευβοίας loses four
contracts.*

## 2026-08-18 — NEGATIVE FINDING: the συστάδα / δημόσιο δάσος layer is not built — the documents locate 20% of contracts and no compartment geometry exists

Probed on the full live ΔΑΣΕ population (1.998 contracts), reading each
contract's own cached text first and its award/notice/request acts second.
Deterministic anchors, case-tolerant on the anchor and case-sensitive on
the captured name:

| element | contracts | share |
|---|---|---|
| συστάδα (compartment) | 1.607 | 80,4% |
| δημόσιο δάσος | 475 | 23,8% |
| δασικό σύμπλεγμα | 238 | 11,9% |
| **συστάδα + δάσος together** | **403** | **20,2%** |

(συστάδα found in the contract itself for 1.516, in its award for 91.)

**Why that is not enough.** A compartment number is meaningless without
its forest — numbering restarts in every δάσος, so «53β» is a place only
as «53β of the Δημόσιο Δάσος Χαλάρας». The full pair exists for a fifth
of the population; the other 60% would carry a bare id that locates
nothing.

**And it could never reach the map.** Greek forest compartment boundaries
live in each Δασαρχείο's διαχειριστική μελέτη and are not published
anywhere open — unlike the ανάδοχοι work-sites, this layer has no
geometry to draw and no toponym to geocode below the forest name.

**User decision**: do not build it («since we don't even have the names of
the forests on all of the contracts I think we should not go on with
this»). The forest NAME alone (475 contracts) is a genuine toponym that
could be geocoded coarsely, but shipping a work-location feature that is
blank on three of every four contracts repeats the partial-coverage trap
already rejected for the award-derived locations.

*Affects: no data, no schema, no curated file. The work regions stay at
Π.Ε. level, derived from the awarding unit as documented. Revisit only if
διαχειριστικές μελέτες or a compartment layer become public.*

## 2026-08-18 — Override authority links now SHOW their evidence: «ΔΔ ΛΕΣΒΟΥ» over works in Ρόδος no longer reads as our error

User question, from the contract page: if «Διεύθυνση Δασών Λέσβου» is
wrong, why does the document trail still print it?

**Two answers, and one of them was a defect.**

The trail prints the ΚΗΜΔΗΣ title **verbatim, and must** — that string IS
the document's registry title and the primary evidence of the keying
error. Rewriting it would edit the public record; the same rule keeps
ΔΑΣΕ registry spellings visible beside their curated display names.

The defect was silence. `forest_loader` links 6 contracts to their units
by curated OVERRIDE and stores the justification in
`contract_forest_authorities.excerpt` — but `queries_extra.contract_authorities`
never selected that column, so the sentence reached nobody. A reader saw a
title saying **Λέσβος**, a region saying **Ρόδος** and a unit saying
**Δωδεκανήσου**, with no explanation: it read as the site's mistake rather
than the registry's documented one.

**Fixed**: the excerpt ships on the payload and renders in EXTRACTED QUOTES
FROM DOCUMENTS as «Awarding unit — curated correction», noting that the
units follow the signed PDF and not the title; the trail's own row carries
a neutral chip «unit corrected from the PDF» so the contradiction is
flagged where the reader meets it. For 25SYMV016491944 the page now quotes:
«Title says «ΔΔ ΛΕΣΒΟΥ» but the signed PDF (fetched 2026-07-25) repeatedly
declares works «αρμοδιότητας Διεύθυνσης Δασών Δωδεκανήσου … εντός του Δήμου
Ρόδου της Π.Ε. Ρόδου (NUTS EL421)» — the title is a registry keying error».

3 of the 6 titles actively contradict the units shown (25SYMV016491944
Λέσβου→Δωδεκανήσου; 25SYMV016495437, whose «ΔΔ ΕΒΡΟΥ ΚΑΙ ΡΟΔΟΠΗΣ» omits
Ξάνθη; 23SYMV013600200's nursery contract). The other 3 are abbreviations
the override merely pins precisely — the same evidence line explains those
too.

*Affects: presentation only, no figure moves. Pinned by
`test_override_authority_links_ship_their_evidence` (all 6 contracts must
carry evidence on every override link, and the registry title must stay
unrewritten).*

## 2026-08-18 — PROJECT BUDGET keyed as CONTRACT VALUE: 4 contracts overstated by €31,7M (4,8% of the Anti-nero basis)

Found by the procurement-family analysis the user proposed instead of the
work-location layer, and found within minutes of starting it.

**How it surfaced.** 24SYMV015544651 («ΤΜΗΜΑΤΟΣ ΕΡΓΟΥ ΜΙΚΤΩΝ ΑΝΤΙΠΥΡΙΚΩΝ
ΖΩΝΩΝ», €31,0M — the largest contract in the programme) cites πρόσκληση
24PROC014447893 in its text. Seven other contracts cite the same
πρόσκληση, and they are exactly the eight Δασαρχεία the parent project
title names (Αλιβερίου, Ιστιαίας, Λίμνης, Χαλκίδας, Διδυμοτείχου,
Καλαμάτας, Σπάρτης, Κυπαρισσίας). Beside siblings of €0,59M–4,18M, the
€31M lot was visibly wrong.

**The error.** The registry keyed the funding recital instead of the price:

> «η συνεισφορά του **Ταμείου Ανάκαμψης** στον **συνολικό προϋπολογισμό
> του ΕΡΓΟΥ** ανέρχεται σε χρηματικό ποσό ίσο με 31.024.697,04 ευρώ, ενώ
> η αντίστοιχη συνεισφορά του ΠΔΕ … 7.445.927,29 ευρώ και αφορά στον ΦΠΑ 24%»

That is the whole multi-lot project's budget (ΟΠΣ ΤΑ 5222791; note the ΠΔΕ
figure is exactly its 24% ΦΠΑ). The contract's own price sits in **Άρθρο 5
«Αμοιβή Αναδόχου»**.

**Screened corpus-wide, not guessed**: of the 245 in-scope contracts, 19
quote such an RRF project budget and **exactly 4 store it as their value**.

| contract | stored net | true fee (Άρθρο 5) | paid | paid/true | paid/stored |
|---|---|---|---|---|---|
| 24SYMV015544651 Σπάρτης | 31.024.697,04 | **4.003.194,80** | 3.901.409,44 | 97% | 13% |
| 24SYMV015170080 Αταλάντης κ.λπ. | 2.284.973,72 | **1.202.106,04** | 1.034.960,00 | 86% | 45% |
| 24SYMV015170089 Πεντέλης κ.λπ. | 2.284.973,72 | **799.483,29** | 712.351,35 | 89% | 31% |
| 24SYMV015170098 Σουφλίου | 2.284.973,72 | **156.871,91** | 135.059,75 | 86% | 6% |

The last three are the three lots of ONE πρόσκληση (24PROC014835083), each
stamped with the same project budget; their true fees sum to €2.158.461,24
against that €2.284.973,72 budget — the difference being the tender
discounts, as expected.

**Each figure confirmed three ways**: the Άρθρο 5 wording; the incl-ΦΠΑ
figure printed in the same sentence (all four verified present in the PDF
text); and the payment orders, which land at 86–97% of the true fee and at
6–45% of the stored one.

**Also checked, clean**: the only other pair sharing an identical stored
value (25SYMV016659302 / 25SYMV017779215, €3.363.432,24, identical texts
after stripping ΑΔΑΜ stamps) needs no action — the first posting is already
registry-cancelled and carries no payments.

*Affects: Anti-nero stated-net basis €659.290.845,34 → **€627.572.883,18**
(−€31.717.962,16, 4,8%). Contract values and their `contract_objects` rows
corrected in `khmdhs/data/contract_corrections.json` (1 → 5 entries).
Everything derived re-reconciled by itself — categories, sankey, Π.Ε.
yearly, connections, pipelines and explore all still sum to the basis with
no code change, because none of them hardcodes it. webui's effective-gross
presentation is unchanged at €604.543.493,99: all four contracts have
payments, so its effective-cost basis was already payment-driven.
/compare ratio ≈22,0× → ≈21,0×.*

**Open**: the fee-clause wording that made the audit possible appears in
only 29 of 245 contracts, and the RRF-recital test only in 19 — so this
error class is screened, but the wider "does the stored value match the
document" question remains unaudited on the Anti-nero side, which has never
had the value validator the ΔΑΣΕ side received.

## 2026-08-18 — Anti-nero value audit (first ever): 344 contracts screened against their PDFs, no further errors beyond the 4 corrected

The ΔΑΣΕ dataset got `scripts/validate_contract_values.py` across all 2.164
contracts in August; the Anti-nero side had never been screened. After the
project-budget corrections, it was run here for the first time
(`--db khmdhs.sqlite --cache pdf_cache`; report at
`data/processed/antinero_value_report.json`, untracked like its ΔΑΣΕ twin).

**Result over 344 contracts**: ok 262 · mismatch 50 · ok_net_only 24 ·
**ok_corrected 5** (the curated fixes re-verified) · near_match 3.

**The 50 `mismatch` rows are not 50 errors.** «Mismatch» means only that
the stored figure is not findable as text in the PDF — and many Anti-nero
συμβάσεις never state a figure at all (three of them are 6,6 kB documents
containing zero amount tokens; the validator's «largest amounts» for them
are dates). Restricting to the 32 in-scope and classifying by whether the
PAYMENTS corroborate the stored value:

| group | contracts | net | verdict |
|---|---|---|---|
| payments at 89–104% of stored gross | 21 | €46,1M | correct; the mismatch is an extraction artefact |
| 2022 contracts paid 72–83% | 4 | €4,7M | read individually — no error found |
| 2025-26 contracts still being paid (16–83%) | 7 | €45,8M | in progress, indeterminate |

The four read individually: 22SYMV011323950's PDF quotes «συνολικού
προϋπολογισμού 812.322,45€ με ΦΠΑ» as a RECITAL of the original contract
while the stored 1.051.762,42 is the post-Α.Π.Ε. value the same document
approves — correct as stored; the other three state no amount anywhere.

**Conclusion**: the four project-budget errors corrected earlier today were
the only value defects this screen can see. Nothing in the audit contradicts
any other stored figure. Note the ceiling honestly — for contracts whose
document states no amount, only the payments corroborate, and for 2025-26
works even that is inconclusive until they finish.

*Affects: no data. `validate_contract_values.py` gained a stdout-encoding
guard (a cp1252 console killed the run after the work but before the report
was written) and is now proven to run against either DB.*

## 2026-08-18 — The even split now holds on EVERY ΔΑΣΕ surface, and a jointly signed contract is still counted once

User, on finding the AWARDING PROCESS sankey still attributing a jointly
signed contract to its lead co-op at full value: «this has to be resolved
now! the splitting of the value to the two co-ops is the decision we made.
it shouldn't be different in different places.»

They were right, and the defect was mine: when the even split was
implemented this morning it was applied to the ranking, the co-op directory
and the co-op pages, but `_dase_kind_rows` kept its older «lead contractor»
rule, so ΣΙΔΗΡΟΧΩΡΙΟΥ and ΠΕΤΡΟΛΟΦΟΥ each carried two different totals on
one page. It was invisible only because both fall outside the top ten and
land in the sankey's pooled node.

**Now**: `_dase_kind_rows` carries a `parties` list per contract — the
holders and their shares, from the same `dase_coop_shares` the ranking uses
— and the co-op column and its flows sum those shares.

**And the count stays whole** (user, immediately after: «no it is one
contract. we cannot count it twice!»): the € divide between holders, the
CONTRACT does not. Every column of the diagram is an aggregate over the
population, so each must sum to the 1.998 live contracts — an intermediate
version that counted the joint contract at both holders (1.999) was wrong
and is fixed: the count lands on the first holder by ΑΦΜ, the same
deterministic order the whole-cent allocation uses.

Body and unit marginals are untouched by all of this: they stay per
CONTRACT, one row each, whole €.

*Affects: presentation only, no basis change. Every column — bodies, units,
flows, coops, coop_flows — now sums to 1.998 contracts and €29.920.558,46.
Pinned twice: `test_dase_sankey_counts_each_contract_exactly_once` (all five
columns against the live KPIs) and
`test_every_dase_surface_reports_the_same_euros_per_coop`, which compares
the ranking, the directory, each co-op's own page and the sankey co-op by
co-op — the test that would have caught the original inconsistency.*

## 2026-08-18 — Procurement FAMILIES derived from the contracts' own texts: 219 of 245 grouped into 134 calls

User: «I was hoping for a node diagram from all these contracts» —
πρόσκληση at the centre, its contracts around it, each with its ΑΔΑΜ and
its €. This entry builds the DATA that diagram needs.

**Why it has to come from the texts.** The ΚΗΜΔΗΣ chain declares an
upstream act for only 40 of the 245 in-scope contracts. The documents are
far more forthcoming: 200 cite their πρόσκληση by ΑΔΑΜ and 125 their
κατακύρωση. 102 of the 128 προσκλήσεις so named were unknown to the
registry metadata entirely and had never been fetched (now cached).

**One key only: a cited ΑΔΑΜ.** Two alternatives were measured and
REJECTED, both because they would invent relationships:
- *Lot labels in titles* («ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ 11Α»): 21 of 59 labels
  repeat across programme years — «ΕΡΓΟΥ 11Α» exists in 2023 AND 2024 —
  so grouping on them merges different procurements into one plausible,
  false family.
- *Shared Diavgeia ΑΔΑ among the family-less*: the ΑΔΑ they share turn out
  to be «Καθορισμός οργάνου που γνωμοδοτεί», «Ορισμός αποφαινόμενων
  οργάνων» and the decision naming a Δασαρχείο as Διευθύνουσα Υπηρεσία —
  common administrative plumbing, not a common procurement.

**Result**: `contract_families` (FK CASCADE, rebuilt by `families_loader`
in the refresh chain) — 424 rows: 275 procurement links, 4 amendments,
145 awards. In scope: **219 contracts in 134 families**, holding €597,9M
of the €627,6M basis. Sizes 84 single · 32 pairs · 10 triples · 5 quads ·
1 five · **2 of eight**. Every row stores the sentence that cites the
ΑΔΑΜ, and the pin re-checks that the ΑΔΑΜ appears inside its own excerpt.

**Two ambiguities, both resolved from the documents**: a contract citing a
SECOND πρόσκληση is always citing «Απόφαση Τροποποίησης της ως άνω
Πρόσκλησης» — that call amended, so it is stored `role='amendment'` and
the family is counted once (detecting it needed accent-folding: Python's
«τροποποι» never matches «Τροποποίησης», the trap scope.py documents).
And amendments with no citation inherit their predecessor's family, the
convention regions/scope/categories already use — 27 do.

**The 26 in-scope contracts with no family are correct, not missing**:
every one is Απευθείας ανάθεση (άρθρο 118/328) or Διαπραγμάτευση χωρίς
προηγούμενη δημοσίευση — procedures that publish no call. Among them the
four Έβρος flood contracts (€39,3M), visibly one project but never
procured as one.

*Affects: new table only, no figure moves. Pinned by tests/test_families.py
— coverage 219/134, every row quoting its ΑΔΑΜ, title-lot grouping proven
absent, CASCADE rebuild, and the eight-lot family 24PROC014447893 whose
sibling comparison exposed the €31M project-budget error and which the
ΚΗΜΔΗΣ chain links to zero contracts.*

## 2026-08-18 — The contract page shows its procurement: acts the registry never linked, and the call's other contracts

Two presentation defects closed, both found by the user reading the page.

**1. The trail hid documents we hold.** DOCUMENT TRAIL–TIMELINE was built
purely from `contract_linked_acts`, i.e. the registry's declared chain,
which is empty for 188 of 344 contracts. So 24SYMV015170098 showed its
call in the new diagram and an empty chain in the trail.

Checked against the live registry before changing anything: the
`adamChain` for that contract returns `notices: []`, `auctions: []`,
`requests: []`, and the award's own record (24AWRD015088777, «Απόφαση
Κατακύρωσης για την Εκπόνηση μελετών…») carries `contractRefNo: []` and
`noticeReferenceNumber: None`. **Neither document points at the other in
the open data** — the ΚΗΜΔΗΣ web UI joins them by ΕΣΗΔΗΣ number
internally, which the API does not expose.

The trail now also lists the acts the contract's OWN TEXT cites, dated
from each PDF's «<ΑΔΑΜ> <YYYY-MM-DD>» registry stamp (there is no
metadata to date them from) and chipped «cited in this contract» so the
provenance is explicit — a row the contract asserts is not the same claim
as a row the registry published. Titles stay «—»: we hold no reliable
title for those acts and do not invent one.

**2. «CONTRACTS UNDER THE SAME CALL»** (user's wording and sketch): the
call at the centre, its contracts orbiting on dashed connectors, every
circle's AREA proportional to stated net €, each labelled with its ΑΔΑΜ,
the viewed contract filled. Sized to the map's column (≤460px) and placed
beside the trail, so one procurement reads across the page. The centre is
the sum, which is what makes an out-of-scale lot obvious — this is the
view that exposed the €31M project-budget error.

*Affects: presentation only. Two implementation notes worth keeping: the
label widths size the viewBox, so an underestimate clips every edge label
(measured at 6,6 units/char for the futura digits, and a render test now
asserts no text escapes the SVG box); and Vite served STALE component CSS
after a rewrite — the diagram rendered as black blobs because `.link`
still carried the previous version's rules. Touching the file fixed it;
suspect it before hunting a code bug.*
