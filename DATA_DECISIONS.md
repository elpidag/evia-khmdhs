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

## 2026-08-18 — The whole programme as one chart: the drawn unit is the CALL, and the three bands say how little of it was competed as lots

The first attempt at a programme-wide network — 245 circles, 174 edges,
one grey, nothing labelled — was rejected by the user on sight («this
doesn't show anything really», then «it's huge and seems as if these dots
are not connected»). Both criticisms were correct and both were structural,
not cosmetic:

- **Nothing was connected to the eye.** Cluster members orbited their hub
  at `rHub + rMember + 7`, so the connector was a 7-pixel stub hidden
  under two circles. The edges existed and were invisible.
- **It was huge because most of it said nothing.** 110 of 245 contracts
  have no sibling — 84 whose call produced exactly one contract, 26 with
  no call at all. Drawn as "clusters of one" they took three quarters of
  the field to repeat a single fact 110 times.

**Rebuilt around what the data actually has.** Measured first, then drawn:
134 calls, of which 50 produced more than one contract (32 pairs, 10
triples, 5 quadruples, 1 quintuple, 2 with eight lots each), covering 135
contracts.

| band | what it is | contracts |
|---|---|---:|
| the field | 50 calls that produced lots, one star each | 135 |
| band 1 | 84 calls that produced exactly one contract | 84 |
| band 2 | no call at all — direct awards and negotiations | 26 |

- **The drawn unit is the call, not the connected component.** A component
  merged calls through shared contractors, which produced stars whose
  spokes asserted a shared call that did not exist. Now one star = one
  πρόσκληση: biggest lot at the centre, siblings on spokes long enough to
  read (`+15`), each star labelled with its own Σ € on a baseline shared
  across the row, and the six richest calls named by ΑΔΑΜ.
- **Contractor bridges stay, as dashed links between star centres.** Calls
  tied by a shared contractor are packed as ONE BLOCK, so a row never
  breaks between them and no bridge sweeps diagonally across the chart.
  Bridges over the same stretch are lifted 3,5 units apart — two dashed
  lines on one axis read as a single solid rule, i.e. as the opposite of
  what they mean. 9 companies won lots under two or more of the 50 calls.
- **Colour is the programme phase** (the existing scope ramp), sizes are
  areas ∝ stated net € on ONE scale across field and bands, so a large
  direct award still reads as large.

Everything load-bearing is printed on the chart (per-star €, the three band
headings, the named calls); the hover card only repeats detail, per the
site's chart doctrine.

*Affects: presentation only, plus two computed additions.
`queries_extra.antinero_network` now ships each contract's `phase` and the
band/bridge counts the chart prints (`n_in_multi_calls`, `n_single_call`,
`n_no_call`, `n_bridge_contractors`, `n_bridge_multi`) — no number in that
copy is written by hand. `/api/meta` gains `kh_family_calls` /
`kh_family_contracts` / `kh_family_none` / `kh_family_declared` for the new
`/methodology#procurement-families` section the caveat links to, which the
chart's caveat had been pointing at before it existed. Pinned by
`tests/test_atlas_real_db.py::test_network_pins` (the three bands must
partition 245 and the calls must be well-formed PROC ΑΔΑΜ) and
`::test_meta_family_facts_match_the_network` (the prose and the picture
must agree). Layout stays deterministic and pure —
`transforms/network.ts`, 15 vitest units.*

## 2026-08-18 — The programme chart becomes ONE population under three arrangements, and the default is time

The star field answered «what was bought together» but the user's objection
to it was about the grid it sat in — and the grid was the honest problem:
**row 3, column 7 meant nothing**. Position carried no information, so the
eye kept looking for an ordering that was not there.

Rather than replace one arrangement with another, the chart now keeps ONE
mark — a circle per in-scope contract, area ∝ stated net €, colour =
programme phase — and lets a toggle rearrange it (`?net=` on `/`, so a view
is a permalink like every other filter state on the site). Only the meaning
of POSITION changes:

| mode | position means | the finding it prints |
|---|---|---|
| `time` (default) | x = signature date, y = dodge | **34 of the 50 split calls signed every lot on one day** |
| `call` | nothing — stars packed into rows | 50 calls produced lots; 84 produced one contract; 26 had no call |
| `pack` | containment: a bubble per call | 84 of the 134 calls bought exactly one contract |

Because the marks are one keyed list, a contract keeps its DOM node between
arrangements and animates to its new place — Flourish's Data Explorer
convention («object constancy during transitions»), which is what makes a
toggle read as a rearrangement rather than as three unrelated charts.

**Rejected, with reasons.** Geography (group by Π.Ε./authority): the same
page already carries MAP and MONEY BY REGION PER YEAR two frames away.
Chord / bipartite calls↔contractors: MONEY FLOW is already a Sankey to
contractors. Arc diagram (one ordered line, arcs for same-call and
same-contractor): the most compact candidate, but 134 call-arcs over 245
nodes is a second hairball. Force-directed anything: not deterministic,
therefore not testable, which this project's layouts must be.

*Affects: presentation, plus one computed addition —
`antinero_network`'s stats gain `n_same_day_calls` (verified against a
direct SQL pass: 50 multi-lot calls, 34 of them single-day), pinned in
`test_network_pins` along with the ISO shape of every node's date, since
the timeline places every dot by it. New pure modules:
`transforms/network.ts` gains `timeline()` (with a variable-radius dodge
added to `transforms/beeswarm.ts`, because these dots differ in size) and
`packed()` (d3-hierarchy — a new dependency, in-doctrine for a «d3-* +
topojson only» stack; d3.pack is deterministic given a deterministic child
order, which the sort guarantees); `transforms/networkScene.ts` assembles
the per-mode scene so the component stays under the house line cap. 20
vitest units for the two new layouts, 9 for the scene. Two implementation
notes: the packed blob is round, so its scene crops the viewBox to the
blob and caps the rendered width — a full-frame viewBox would be three
quarters white paper; and labels now paint OVER the marks with a paper
halo (`paint-order: stroke`), because in a packed layout anything drawn
outside a circle lands on top of its neighbour.*

## 2026-08-18 — Programme chart, user review: the fire season is drawn, the card is identity only, «by call» leaves the site, and the nested view is rebuilt around what «the middle» means

Four decisions from the user's review of the three arrangements, all
implemented:

**1. The timeline shades Greece's fire season.** Every year's 1 May – 31
October is a stripe behind the dots. The season is a single definition that
ships from the API together with the count it implies
(`fire_season: {from: "05-01", to: "10-31", n_contracts: 120}`), so the
shading and the sentence beside it cannot drift apart — **120 of the 245
in-scope contracts were signed inside a fire season**. Verified against a
direct pass over the payload in `test_network_pins`.

**2. The hover card carries identity only** — ΑΔΑΜ and amount. Everything
else it used to repeat (phase, title, contractor, region, call) is either
printed on the chart or a click away on the contract page; the doctrine says
a tooltip must never be where a fact lives. A bug found while checking this:
the in-circle labels intercepted pointer events, so the very marks that
carried a label could not be hovered or clicked — chart text is now
`pointer-events: none`.

**3. «By call» (the star field) is off the site**, by user decision, and may
return. `callScene` and its units stay in the codebase; only `NET_MODES`
decides what the toggle offers, so putting it back is a one-line change.

**4. The nested view was rebuilt so that the middle MEANS something.** The
first version bucketed the 84 single-contract calls into one parent, which
d3.pack — sorting by value — put in the centre, where it read as one
enormous call. The user's correction: *the clustering in the centre should be
the ones that are grouped in procurements, the individuals should be in the
periphery.* So the layout no longer uses `d3.pack` at all:

- each call's lots are packed with `packSiblings`, then every call bubble is
  packed into a **core**;
- the core is then packed as the FIRST sibling among the contracts bought on
  their own, which therefore **ring** it;
- radii are √€ throughout and scaled once at the end, so area ∝ € holds
  across both levels and against the timeline.

Styling follows the packed-circle reference the user supplied (a World-Bank
style regions chart): the call bubble is its phase colour at full strength
with a **rim** (drawn 12% wider than the lots it encloses) carrying the
ΑΔΑΜ set along the arc, lots inside are the same hue lightened 42%, and ink
is chosen by the fill's luminance — dark on a light hue, light on a dark one
— for both the rim name and the in-circle amounts. Amounts inside marks use
a new compact format (`eurTiny`: «11,6M», «812k»), presentation only: no
total is ever stated that way. A label that cannot fit is dropped, never
shrunk below reading size or spilled outside its circle. Contracts awarded
with **no call published at all** carry a dashed edge, keyed in the legend.

*Affects: presentation, plus the `fire_season` payload block and
`format.ts:eurTiny` (goldens added). Pinned by `test_network_pins` (season
bounds + count recomputed from the nodes) and by vitest units for the new
packing — including one that asserts the property the user asked for: every
grouped mark is closer to the blob centre than every solitary one.*

## 2026-08-18 — One 400px box for every arrangement of the programme chart

User decision: «When it was signed» and «Nested by call» are both 400 px
tall, so the frame keeps one height and the page does not jump when the
toggle is used. `NET_HEIGHT = 400` in `transforms/networkScene.ts` is the
single knob.

Making it exact needed two changes, both worth keeping:

- **The timeline's viewBox is now the box itself** (`0 0 1120 400`, no
  margins), so one unit is one rendered pixel at the frame's width and
  «400» means 400. Its swarm no longer sets the height: `timeline()` takes
  an exact height and, if the densest day needs more room than the box
  allows, **shrinks the dots** (uniformly, so area ∝ € still holds) and
  re-dodges, up to six passes. A dodge that overflowed its box would
  overplot, which is the one thing a beeswarm exists to prevent. Today the
  swarm fits with room to spare (it needed ~342 of 378), so nothing is
  shrunk; the mechanism is there for future data.
- **The packed blob gets a square viewBox of exactly the box, centred on
  the blob, with the rendered width capped to match** — a circle is as
  wide as it is tall, so 400 tall is 400 wide.

*Consequence, stated plainly: at 400×400 the nested view has room for its
circles but not for its lettering — the per-contract amounts drop out
entirely and only the two largest calls keep their ΑΔΑΜ on the rim (a new
gate suppresses a 15-character code bent round a small circle, which reads
as a smudge rather than a label). Nothing was removed from the design:
every label is drawn where it fits and returns if the box grows. The
alternative — letting the nested view keep the frame's width while the
timeline stays 400 — was not taken, because the user asked for one height.*

## 2026-08-18 — Every in-scope contract audited against its own signed text, read down the CHAIN; and the contractor ΑΦΜ stop splitting one company into two

Triggered by the user reading two source documents and highlighting what they
carry (a phase-I contract, 22SYMV010447496, and the NOVA/Δίρφυς sponsor act
6Χ7Ι4653Π8-ΙΧΣ), then spotting that «ΒΙΟΣ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ» and «Δ ΚΑΦΕΤΖΗΣ
ΚΑΙ ΣΙΑ ΟΕ» are the same ΑΦΜ but read as two companies.

### The structural finding: read the chain, never the tip

**46 of the 245 in-scope contracts are amendments, and every short text in the
corpus is one of them** — 22SYMV010806317, say, is a 10,7 kB «1η ΤΡΟΠΟΠΟΙΗΣΗ»
whose 247 kB parent holds the price, the Δασαρχείο, the funding code and the
parties. Concatenating each chain's ancestors lifts every anchor and leaves no
contract under 20 kB:

| anchor | tip only | chain |
|---|---:|---:|
| ΣΑΤΑ ενάριθμο | 177 | **222** |
| εγγυητική + amount | 167 | **197** |
| άρθρο «Αμοιβή Αναδόχου» | 83 | **118** |
| «Προϋπολογισμός Δημοπράτησης» (the decoy) | 45 | **67** |
| «αρμοδιότητας Δασαρχείου…» | 140 | **155** |
| Π.Ε. / Δήμος named | 93 / 95 | **109 / 106** |
| Α/Α ΕΣΗΔΗΣ | 41 | **56** |
| «ως υπεργολάβο» | 20 | **43** |

`scripts/audit_contract_documents.py` does this and writes three review files
to `data/processed/` (`audit_fields`, `audit_extras`, `audit_identity`).
Nothing it produces is written to a database: they are candidates.

**What the audit found.** The stored net value appears verbatim in the
contract's own text for **237/245** (gross 224); **4** contracts state
neither. The εγγυητική corroborates the price for **153 of 163** checkable
(the implied rate clusters on 5% with a tail to ~5,6%, plus a 2,5% group — so
it is a SCALE check, the kind that catches a ×10 error, not a cent check).
The funding ενάριθμο is confirmed from the document for **222/245 with zero
disagreements**. **7 stored forest-authority links across 3 contracts are
never named in the documents** — 22SYMV010856516 (ΔΔ Κεφαλληνίας, ΔΔ
Καστοριάς, both `text`-matched), 23SYMV013600200 (three `override` links) and
its heir 24SYMV015185915.

Two extractor lessons worth keeping: the *reverse* authority test is the
meaningful one — documents legitimately name MORE Δασαρχεία than a contract
covers, because recitals quote the whole multi-lot procurement and cite other
contracts' titles, so «stored ⊄ declared» is the error and «declared ⊅ stored»
is noise. And a regex written in Greek must be folded into the same alphabet
as the folded text, but folding must NOT uppercase, or `\s \d \w` become their
inverses — that silently zeroed an entire probe run.

### The identity defect, and its fix

ΑΦΜ **998342580** carries four registry spellings across €13,04M because the
signed contract says «με την επωνυμία «Δ. Καφετζής & ΣΙΑ Ο.Ε.» (δ.τ. «ΒΙΟΣ
Α.Ε.»)» — one entity, legal name and trade name. **30 of the 156 in-scope
contractors** carry more than one spelling, and the display rule was
`MIN(name)`, i.e. alphabetical accident.

Underneath that sat a harder defect: the aggregation groups on the **raw**
`vat_number`, and 13 rows carried a whitespace-padded ΑΦΜ while one carried an
eight-digit one. **Seven companies had their money split across two keys** —
GREEN CONSTRUCTION €13.586.678,20, ΧΡ. ΚΥΡΙΑΚΑΚΗΣ €8.701.698,82, Γ.Ι.
ΚΑΡΝΟΜΟΥΡΑΚΗΣ €6.861.723,35, ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ €5.381.590,93, ΚΟΙΝΟΠΡΑΞΙΑ
ΕΛΛΗΝΙΚΑ ΕΡΓΑ–ΛΙΑΧΤΙΔΑ €4.461.356,76, Ν. ΠΑΠΑΔΟΠΟΥΛΟΣ €3.198.837,91,
ΚΗΠΟΠΡΑΞΙΣ €1.347.184,06.

Fixed at the two right places:

- **`extract.py` strips the ΑΦΜ on ingest**, so the padding can never return,
  and the committed DB was normalised in place (13 rows). This is a
  normalisation, not a correction: no fact changes, so nothing is stamped.
- **`25SYMV017073536` gets a curated `contractors_vat` entry**: the registry
  keyed ΓΕΩΓΝΩΜΩΝ Ο.Ε. as «98434068», the signed contract states «με ΑΦΜ
  **998434068** της ΔΟΥ Πατρών». Zero-padding the eight-digit value to
  098434068 — the ΔΑΣΕ canonical-VAT rule — would have filed it under an ΑΦΜ
  belonging to nobody, so the canonicaliser is not a substitute for reading
  the document.
- `contract_corrections.apply_contract_corrections` no longer stamps
  `correction_note` for a party-only entry: the contract page renders that as
  «Stated value — curated correction … the value shown is the one the signed
  contract states», which would be a false statement about a price nobody
  touched.

*Affects: analytics. In-scope contractor keys 163 → **155**, the basis
unchanged at €627.572.883,18. Three consequences worth naming: the network
chart now sees **28** contractors bridging calls instead of 26 (two were
hidden behind a split key); `/connections` flows rose 271 → **277** because a
padded key had no `contractor_locations` row, so its contracts had no home
region at all — **0 in-scope contracts are now unlocated**; and
`contractor_authority` pairs fell 490 → 489, one pair that was counted twice.
Pins updated in `tests/test_atlas_real_db.py` with the reason on each.*

**Open, needing a human verdict** (all in the review files, none applied):
the 4 contracts whose stated value is absent from their own text; the 7
authority links the documents never name; **22 rows across 13 contracts whose
registry ΑΦΜ is not among the ones their signed text states** — most are the
consortium-versus-members distinction, but not obviously all; and the 30
entities needing one curated display name, for 26 of which the document
supplies the legal name and, where it exists, the δ.τ.

## 2026-08-18 — PROJECT BUDGET keyed as CONTRACT VALUE, second sweep: 8 more contracts, −€1.675.269,22

The morning's four corrections were found by hand, through the πρόσκληση-family
analysis. The document audit turned the same error into a **screen** — does the
stored value equal an amount the contract itself labels «Προϋπολογισμός
Δημοπράτησης» / «εκτιμώμενη αξία» / the RRF project budget? — and ran it over
every contract with cached text.

The user's own reading of 22SYMV010856516 is the canonical case. Its parent's
Άρθρο 7.1 states the fee, and a few lines below sits the ceiling:

> «Η συνολική αμοιβή του ΑΝΑΔΟΧΟΥ … **συμφωνείται** έως ποσού … (**370.985,73 €**)
> πλέον ΦΠΑ 24% (89.036,58€) και συνολικά έως ποσού … (460.022,31€)»
> «Ο **Προϋπολογισμός Δημοπράτησης** … ανήλθε για το Υποέργο Γ στο ποσό **482.270,64€**»

and `482.270,64 ÷ 1,24 = 388.927,94` — precisely the stored net. The registry
recorded the advertised ceiling and back-computed a net from it.

**Eight in-scope contracts, all phase I/II of 2022–23, all «Υποέργο X» lots of
the same framework:**

| contract | stored net | fee the contract agrees | overstated |
|---|---:|---:|---:|
| 22SYMV010795597 | 2.698.137,98 | 2.031.375,52 | 666.762,46 |
| 22SYMV010795577 | 1.454.276,58 | 1.161.075,67 | 293.200,91 |
| 22SYMV010795606 | 1.118.903,74 | 836.613,02 | 282.290,72 |
| 22SYMV011323950 | 848.195,50 | 655.098,75 | 193.096,75 |
| 22SYMV010856526 | 1.473.838,67 | 1.379.208,27 | 94.630,40 |
| 22SYMV010856515 | 1.246.811,25 | 1.163.690,51 | 83.120,74 |
| 22SYMV010856517 | 1.474.167,85 | 1.429.942,82 | 44.225,03 |
| 22SYMV010856516 | 388.927,94 | 370.985,73 | 17.942,21 |

Each verified against the canonical «Άρθρο 7 – Αμοιβή Αναδόχου … συμφωνείται
έως ποσού …» clause with the ΦΠΑ pair checking out at ×1,24; the verbatim
sentence is the `reason` on every entry. **13 entries** were written, because
five of the eight share the wrong figure with their superseded predecessor,
whose page is reachable and must not keep contradicting its own PDF.
`contract_objects` rows carrying the same figure are corrected with them.

**The screen is not a verdict.** It also flagged 23SYMV012834824 and
23SYMV013039377, where the fee *genuinely equals* the budget — the contractor
offered no discount — and those were left untouched. Two of ten would have been
false corrections if the screen had been applied mechanically.

**Sweep.** Re-run over all 344 Anti-nero contracts with cached text: only those
two innocents remain, so the class is closed on this dataset. Over all 2.164
ΔΑΣΕ contracts: 4 hits, all «Εκτιμώμενη αξία» in ΚΥΑ-priced direct awards where
the estimate IS the contracted price by construction — no discount exists to
create a gap. ΔΑΣΕ values were separately screened by
`scripts/validate_contract_values.py`.

*Affects: the Anti-nero analytics basis, **€627.572.883,18 → €625.897.613,96**
(−0,27%). All eight are δασοτεχνικά, so the whole drop lands in that category
(359.263.907,38 → 357.588.638,16). Ten pins updated in
`tests/test_atlas_real_db.py`. Payments are untouched — this is a stated-value
correction, and the paid layer was always independent.*

**Two further findings from the same audit, NOT applied, awaiting a verdict:**
25SYMV016658903 stores 3.184.186,76 where Άρθρο 4.1 states, in words and
digits, 3.184.18**3**,76 (€3,00); and 26SYMV019512653, a «1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ
ΣΥΜΒΑΣΗ» worth 80.995,65 € by its own text, carries the running total
621.474,16 = 540.478,51 (original) + 80.995,65. The programme total is correct
either way there, because the inflated figure is ≥0,9× the parent and the
supersede rule therefore drops the parent — so the fix is a modelling choice,
not an arithmetic one.

## 2026-08-18 — The additive-supplementary rule now reads the PDF heading, not only the registry title

The rule that stops a supplementary contract from wiping out the contract it
supplements has existed since the beginning and works:

```python
additive = ("ΣΥΜΠΛΗΡΩΜΑΤΙΚ" in succ_title
            and values[new_ref] < 0.9 * values[old_ref])
```

Audited across the whole dataset, it fires correctly four times
(24SYMV015185915 at 0,23× its parent, 25SYMV016392306 at 0,15×,
26SYMV018445120 at 0,23×, 26SYMV019471687 at 0,03× — both versions count) and
correctly declines twice, where the «συμπληρωματική» restates the parent's
full value (26SYMV019250208 and 26SYMV019200696, ratio 1,00 — ΑΠΕ
recapitulations, which do supersede).

**But it classified on the REGISTRY TITLE.** 26SYMV019512653 is titled
«ΑΝΤΙΠΛΗΜΜΥΡΙΚΑ ΔΥΤΙΚΗΣ ΑΤΤΙΚΗΣ»; only its own PDF says «1η ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ
ΣΥΜΒΑΣΗ». So the ratio test was never reached and the act was treated as a
plain replacement — while, independently, the registry had stored its value as
the RUNNING TOTAL (540.478,51 original + 80.995,65 supplement = 621.474,16).

The two errors cancelled: counting only the tip gave the same €621.474,16 as
counting both would have. **Nothing was ever double-counted** — which is why
this surfaced as a documentation problem, not a money problem. The danger was
latent: correcting the value alone would have left the title-blind rule in
place, kept the parent superseded, and silently dropped €540.478,51.

Both fixed together:
- `scope_loader` now tests the successor's PDF **heading** (first 600 chars)
  as well as its registry title. The heading only — «συμπληρωματικές
  εργασίες» is ΕΣΥ boilerplate deeper in every contract, and reading the whole
  document would classify half the corpus as supplementary.
- 26SYMV019512653's value is corrected to its own stated 80.995,65 /
  100.434,61 («ορίζεται στο ποσό των ογδόντα χιλιάδων εννιακοσίων ενενήντα
  πέντε ευρώ και εξήντα πέντε λεπτών 80.995,65€ …»).

Two other contracts say ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ only in their PDF (25SYMV016679557,
26SYMV018612500); both restate their parent's full value, so they take the
replaces branch either way. 26SYMV019512653 was the only case where the
title-blindness mattered.

*Affects: the in-scope population **245 → 246** and nothing else — the basis
stays €625.897.613,96, because the €540.478,51 simply moves from being folded
into the supplement to being carried by 26SYMV019488916, the act that now ends
that line. That act is «Έγκριση παράτασης χρονοδιαγράμματος» of
25SYMV017985934 posted under a ΣΥΜΒ ΑΔΑΜ — it restates the contract it
extends, which is why it supersedes it and now carries its value. It was
curated in on becoming countable: category `antidiavrotika` from the project
title it quotes verbatim, and both Π.Ε. of «περιοχές αρμοδιότητας Δασαρχείου
Αιγάλεω και Μεγάρων», matching the chain tip. Fourteen pins updated across
`test_atlas_real_db`, `test_families`, `test_linked_acts`.*

## 2026-08-18 — A ΣΥΜΒ ΑΔΑΜ is not always a contract: every record now says what it is

> **Superseded the same day in two ways, both below.** (1) The tally here
> reads 10 «Έγκριση Α.Π.Ε.» + 1 «Α.Π.Ε. και συμπληρωματικής σύμβασης»; the
> rule's gap was `[^.]`, which cannot cross the dots of «Α.Π.Ε.» to reach the
> «και της 1ης Συμπληρωματικής Σύμβασης» that follows — with `.{0,130}?` the
> true split is **0 + 11**, and no in-scope record approves an ΑΠΕ alone.
> (2) The framing «17 of the 246 are approvals, not contracts» was rejected by
> the user: see «The vocabulary for a ΣΥΜΒ record» at the end of this file.

The user's question — «if 26SYMV019488916 isn't a contract and it's an
«Έγκριση παράτασης χρονοδιαγράμματος», we should say so in the type of
document, that's what it is there for» — turned out to describe a systemic
gap, not one record.

**The registry cannot answer it.** `contract_type` is the ν.4412 object
category: «Έργα» or «Υπηρεσίες», identical on the contract, its amendment,
the supplementary contract and the ministry decision approving them.

**The documents can**, in their heading or «ΘΕΜΑ:» line. Read across the
whole stored population, the 246 in-scope records are:

| what the document says it is | in scope |
|---|---:|
| Σύμβαση — contract | 200 |
| Τροποποίηση σύμβασης — amendment | 25 |
| Έγκριση Α.Π.Ε. — ministry approval of a revised works schedule | 10 |
| Έγκριση παράτασης χρονοδιαγράμματος — schedule extension | 6 |
| Συμπληρωματική σύμβαση — supplementary contract | 4 |
| Έγκριση Α.Π.Ε. και συμπληρωματικής σύμβασης | 1 |

So **17 of the 246 are ministry approvals, not contracts**, and 26SYMV019488916
is one of twelve, not an oddity. The money is unaffected — an approval record
carries the value of what it approves, and the supersede/additive rules
already handle that — but «246 contracts» has to be read as «246 records».

`khmdhs/document_kinds.py` classifies from the document (ordered rules, most
specific act first, so «ΕΓΚΡΙΣΗ ΤΟΥ 2ΟΥ Α.Π.Ε. ΚΑΙ ΤΗΣ 1ΗΣ ΣΥΜΠΛΗΡΩΜΑΤΙΚΗΣ
ΣΥΜΒΑΣΗΣ» is not filed as a plain ΑΠΕ), falls back to the registry title for
the few whose PDF opens with a signature stamp and a letterhead
(22SYMV011323950), and leaves anything else `unknown` for
`data/document_kind_overrides.json` rather than guessing. Zero in-scope
records are unknown today. Stored on `contracts` as `document_kind`,
`document_kind_evidence` (verbatim) and `document_kind_source`
(pdf / registry_title / curated); in the refresh chain after `families_loader`.

Two extraction facts worth keeping: «ΥΜΒΑΣΗ» without its Σ is real — pdftotext
drops the drop-cap — and the heading window has to be ~2.500 chars, because
ministry decisions carry a letterhead before their ΘΕΜΑ line, while reading
the whole document would match the ΕΣΥ boilerplate «συμπληρωματικές εργασίες»
in every contract.

*Affects: presentation and one new stored field. The contract page gains a
DOCUMENT row (English label over the Greek the document uses), and the
DOCUMENT TRAIL's type column stops calling every ΣΥΜΒ row «Contract» —
26SYMV019488916's trail now reads Contract / Supplementary contract /
Approval — schedule extension. Pinned by `test_document_kind_pins`
(composition + the verbatim evidence). `contract_document_kind` degrades to
None on a DB older than the ALTER guard, like the other post-hoc columns.*

## 2026-08-18 — The vocabulary for a ΣΥΜΒ record: all 246 are συμβάσεις, the label says which kind

Settled with the user after several rounds, and the rounds are the record:
«approvals» was rejected because the word does not say what the act does;
«acts / πράξεις» was rejected because ΚΗΜΔΗΣ files every one of these as a
**σύμβαση** and inventing a second Greek term denies the registry's own word;
«extra work» was rejected as too colloquial for an academic report; and a
framing that opened «only 200 are contracts» was rejected as needlessly
oppositional.

What resolves all four: **all 246 ARE συμβάσεις — the label says which kind of
σύμβαση**, which means the plain contract needs the qualifier it never had,
«αρχική». The vocabulary is then ν.4412's own throughout, and Directive
2014/24's in English:

| in scope | Greek | English |
|---:|---|---|
| 200 | Αρχική σύμβαση | Original contract |
| 25 | Τροποποίηση όρων | Revision of terms |
| 4 | Συμπληρωματική σύμβαση | Supplementary contract |
| 11 | Έγκριση συμπληρωματικών εργασιών | Approval of supplementary works |
| 6 | Παράταση προθεσμίας | Deadline extension |

Unused but defined: Έγκριση επιμέτρησης / Approval of revised quantities, and
Δεν προσδιορίζεται / Not defined.

The 4 and the 11 share a stem because they are one phenomenon in two document
forms — the supplementary contract itself, and the ministry decision approving
one — so a summary may sum them as **15 supplementary works** without
inventing a category. The label is a title; the document's verbatim wording
(«Έγκριση του 2ου Α.Π.Ε. και της 1ης Συμπληρωματικής Σύμβασης του έργου της
Σύμβασης (4/2025) με ΑΔΑΜ: 25SYMV016432029») stays in
`document_kind_evidence` and is shown beneath it — Α.Π.Ε. means nothing to a
non-specialist in a title, and everything as evidence.

Two facts established while settling this, both checked rather than assumed:
**none of the 25 revisions changes the price** (0 of 25 differ from the
contract they revise; they touch deadlines, acceptance and payment procedure,
guarantee letters), and **the six extensions carry their parent's value to the
cent**. So of the 246, only the 15 supplementary works move money.

*Affects: presentation only. `document_kinds.KINDS` carries the bilingual
pair; the contract page prints English over Greek and the DOCUMENT TRAIL type
column uses the same words; `/api/meta` gains `kh_doc_<kind>` counts so the
new `/methodology#record-kinds` paragraph is computed, never typed. Pinned by
`test_document_kind_pins`, which now also pins the labels themselves so page
and prose cannot drift apart.*

## 2026-08-18 — The audit's two open flags were the audit's own blind spots: «Ν.» and «Α.Φ.Μ.»

Both items left over from the document audit were reviewed against the
documents. Neither was a data error; both were reading failures in the
checking tools, now fixed and pinned.

**1 · «Stored forest authority the document never names» (7 rows / 3
contracts) — wrong on all counts.** The user's instinct was right:
22SYMV010473683 says it plainly, in its «αρμοδιότητας» clause —
«…αρμοδιότητας Δασαρχείων Ιωαννίνων **και Δ/νσεων Δασών Ν. Κεφαλληνίας και
Καστοριάς** με Α/Α ΕΣΗΔΗΣ 187023». The matcher walks the tokens after a
trigger («Δ/νσεων Δασών») and skips connectors, but its connector set held
only ΚΑΙ/ΤΟΥ/ΤΗΣ/ΤΩΝ/,/& — so **«Ν.» (Νομού) stopped it dead**, and it read
neither Διεύθυνση. Two compounding details: the connector test did not
`rstrip('.')` the way the alias test does, so even adding «Ν» would not have
matched the token «Ν.»; and fold() maps Greek→Latin homoglyphs, so the added
words have to be folded like every other stop token.

Fixed in `forest_loader._CONNECTORS` (+ Ν / ΝΟΜΟΥ / ΝΟΜΟΣ / ΝΟΜΩΝ, and the
dot strip), pinned by `test_matcher_skips_the_nomos_token`. Re-running the
loader over the whole DB changed **no stored link** — the three contracts
already had theirs from the registry's items text — so this is a robustness
fix on the PDF-fallback path, not a data change.

The 5 rows the re-run still flags are the same phenomenon one step out: the
audit reads only the 200 characters after «αρμοδιότητας», while the
authority may be named in the item text instead. All five check out —
26SYMV019488987/…89224/…89359/…89513 store Δασαρχεία Αλεξανδρούπολης and
Σουφλίου and their registry item says «σε περιοχές ευθύνης των Δασαρχείων
Αλεξανδρούπολης και Σουφλίου και της Διεύθυνσης Δασών Έβρου»;
22SYMV010856515 stores Ολυμπίας + Αμαλιάδας and its item says «ΕΚΤΑΣΗ
ΕΥΘΥΝΗΣ ΤΩΝ ΔΑΣΑΡΧΕΙΩΝ ΟΛΥΜΠΙΑΣ ΚΑΙ ΑΜΑΛΙΑΔΑΣ». **Zero stored
forest-authority links are unsupported by the documents.** 23SYMV013600200's
three overrides also stand: its own title names nurseries, not services
(Αλιάρτου Π.Ε. Βοιωτίας, Λαγκαδά Π.Ε. Θεσσαλονίκης, Αμβροσίας και Οργάνης
Π.Ε. Ροδόπης), and the supplementary contract's PDF names the Δασαρχείο
Λιβαδειάς cost committee — which is exactly what the curated evidence says.

**2 · 24SYMV016018183 «registry ΑΦΜ not in the signed text» — the ΑΦΜ is in
the text, with dots.** The contract is signed by an **Ένωση Οικονομικών
Φορέων** of two members, and states both: «NOVALIS … Ε.Π.Ε.», ΑΦΜ 998811782,
and the sole trader «ΦΩΤΟΠΟΥΛΟΣ ΓΕΩΡΓΙΟΣ του ΕΥΘΥΜΙΟΥ», **Α.Φ.Μ.**
122076788, Δ.Ο.Υ. ΓΡΕΒΕΝΩΝ. Both are stored, and the registry is right. The
audit's regex was `ΑΦΜ\s*:?\s*(\d{9})`, which cannot see the dotted form —
now `Α\.?Φ\.?Μ\.?`. The conflict count falls from 22 rows / 13 contracts to
19 / 10, and every remaining row is the consortium ↔ members distinction in
one direction or the other (registry lists the members, the document names
the ένωση's own ΑΦΜ, or the reverse) — a modelling question, not an error.

*Affects: `khmdhs/forest_loader.py` (connector set + dot strip),
`scripts/audit_contract_documents.py` (ΑΦΜ pattern), `tests/test_forest.py`.
No stored value, link or party changed.*

## 2026-08-18 — Work locations: no coordinates exist, but the contracts name their δήμοι — extraction opened for curation

**Negative finding first.** Asked whether the site can place Anti-nero works
more precisely than the Π.Ε., all 246 in-scope contracts were searched for
every form a coordinate takes — ΕΓΣΑ87 grid pairs, Χ:/Υ: columns, WGS84
decimals, kml/shp references. **Zero.** The contracts say why themselves:

> «Τόπος εκτέλεσης της Σύμβασης είναι ο τόπος που προσδιορίζεται **στις
> Μελέτες του Παραρτήματος VII της Πρόσκλησης Έργου** και **απεικονίζεται
> στο χάρτη επέμβασης** που επισυνάπτεται σε κάθε μία εκ των ως άνω Μελετών.»

The geometry exists as a map inside a μελέτη annex ΚΗΜΔΗΣ does not publish.
The 147 linked upstream acts were checked too (all already cached, nothing to
fetch): of the 34 προσκλήσεις exactly ONE states coordinates —
25PROC017353453, a DMS bounding box round a group of sub-basins near Μέγαρα.
So Π.Ε. → Δήμος is the only step available, and nothing finer.

**What the documents do carry** is better than a keyword scatter: a
structured, per-authority placement sentence.

> «Τα προτεινόμενα έργα **αρμοδιότητας του Δασαρχείου Μεγάρων**
> χωροθετούνται εντός των **Δήμων Μεγαρέων και Μάνδρας – Ειδυλλίας** της
> **Περιφερειακής Ενότητας Δυτικής Αττικής** (NUTS: EL306)»

A contract naming fifteen δήμοι is therefore not a recital quoting its whole
multi-lot πρόσκληση — the fear that shaped the earlier plan — but five
Δασαρχεία with three δήμοι each, and the document says which belongs to
which. It also states the Π.Ε. and the NUTS code in the same breath, so the
extraction can be held to a check the document itself supplies.

`scripts/extract_contract_municipalities.py` reads that sentence down the
CHAIN (tip → ancestors) and proposes only: **124 of 246 contracts, 292
statements, 582 municipality assignments, 543 of them agreeing with every
Π.Ε. the sentence itself states, 0 contradicting one, 11 names unresolved.**
39 assignments sit outside the Π.Ε. WE curated for the contract — those are
flagged for review in both directions, since the document may be right and
our curation coarse (24SYMV014217832 names Κηφισιάς, Παπάγου-Χολαργού and
Αγίας Παρασκευής where we recorded only Ανατολικής Αττικής). Output is
`data/processed/municipality_review.json` (gitignored) plus the committed
`municipality_curator.html`; verdicts will land in curated
`khmdhs/data/contract_municipalities.json`. Nothing is written to the DB.

Reading rules worth keeping (each cost a measurement):
- a name counts **only inside the run a «Δήμου/Δήμων» introduces**. Matching
  the vocabulary anywhere in the window instead pulled in the contractor's
  home town and every Π.Ε. that shares a name with a δήμος — 93 assignments
  outside the contract's own Π.Ε., against 39 now;
- the window after «χωροθετούνται» must be a **lookahead**. A consuming one
  swallows the next statement, and a five-lot contract reports one;
- one misspelling must not take the rest of the list with it
  («ΗΡΑΚΕΙΑΣ» for Ηρακλείας): the run is walked token by token and ends only
  on two unknown words running;
- the page-break watermark «ΣΕΛ.4 24SYMV014498953 2024-03-29» lands between
  «Δήμου» and the name it introduces, and is stripped first;
- six different hyphens are in use and the compound may have none at all
  («Ξυλοκάστρου - Ευρωστίνης» / «Ξυλοκάστρου Ευρωστίνης»), so the lookup key
  drops punctuation entirely;
- the layer is **Καλλικράτης 2010** and the contracts use current names:
  ν.4600/2019 renames and splits (Μετεώρων, Καμένων Βούρλων, Μυτιλήνης and
  Δυτικής Λέσβου, Αργοστολίου/Σάμης/Ληξουρίου, Ανατολικής/Δυτικής Σάμου,
  Σερβίων/Βελβεντού) resolve onto the parent unit we actually have a polygon
  for, marked `via: rename` with the reason, rather than inventing a boundary;
- `[\s-‐…]` is a character RANGE, not a set — and a Greek pattern must be
  folded WITHOUT uppercasing, or `\s \d \w` inv­ert and `(?P<name>)` groups
  are mangled. That trap has now cost four scans.

*Affects: new `scripts/extract_contract_municipalities.py` +
`tests/test_contract_municipalities.py` (9 units on real sentences) +
`municipality_curator.html`. No DB, no API, no page — those follow the
curation.*

## 2026-08-19 — The work-location card is rebuilt on the document's own list, and the πρόσκληση joins as a second source

User review of the first curator: «the cards are really confusing … in the
text of the procurement there is actually a list for each contract and it
mentions the δασαρχείο and the δήμος και δημοτικές ενότητες των
περιφερειακών ενοτήτων … the τμήμα α και τμήμα β of one procurement usually
refer to the two contracts we have already connected to the procurement». Both
points were right, and one of them exposed a silent data loss.

**The unit is the authority, and its δήμοι come in Π.Ε. GROUPS.** §3.6 of
25SYMV016570021 reads: «…αρμοδιότητας του Δασαρχείου Αιγάλεω χωροθετούνται
εντός των Δήμων Μάνδρας–Ειδυλλίας, Ελευσίνας και Ασπρόπυργου της Π.Ε.
Δυτικής Αττικής (NUTS: EL306) **και** των Δήμων Χαϊδαρίου, Αγίας Βαρβάρας,
Πετρούπολης, Ιλίου (Νέων Λιοσίων) και Αγίων Αναργύρων–Καματερού της Π.Ε.
Δυτικού Τομέα Αθηνών (NUTS: EL302).» The first reader stopped at the first
Π.Ε. clause and **dropped the second group — five δήμοι in that sentence
alone**. It now walks group after group, and two more traps came out of it:
`PE_CLAUSE` ends ON the «(» of the NUTS parenthetical, so the continuation
«… ) και των Δήμων …» is only visible after skipping to «)», and «Ιλίου (Νέων
Λιοσίων)» is an aside INSIDE a list, not the end of one.

**The authority may be named after the δήμοι.** 24SYMV014192289 writes
«χωροθετούνται εντός των Δήμων Ζαχάρως και Ανδρίτσαινας–Κρέστενας … 
αρμοδιότητας Δασαρχείου Ολυμπίας», and the card said «no authority named in
this sentence» while the document plainly names one. Both orders are read now:
232 statements name it before the δήμοι, 22 after, 21 genuinely name none.

**The card mirrors the document**: one block per Δασαρχείο, one row per Π.Ε.
inside it (NUTS printed), chips for the δήμοι, the verbatim sentence behind a
«the sentence» disclosure, and the sub-municipal phrases the sentence adds
(«Δ.Ε. Ζαχάρως και Σκιλλούντος») printed as read-only evidence — that tier has
no boundary layer in this project, so it is shown and not recorded. Where the
same authority is stated twice (Άρθρο 3 summarises, §3.6 lists), the richer
reading wins and no δήμος appears twice.

**The πρόσκληση is now a second source.** The call names its τμήματα with
their Δασαρχεία («Τμήμα Α: … αρμοδιότητας της Διεύθυνσης Δασών Φωκίδας και
του Δασαρχείου Ελασσόνας»), and carries the same per-authority δήμος lists —
100 of the 128 cached calls do. For a contract whose own text places some of
its authorities and not others, the missing blocks are taken from its call
**and only for the Δασαρχεία that contract actually holds**, because the call
describes its sibling lots too. Every such block is stamped `from_call:
<PROC ΑΔΑΜ>`, shown on the card as a dark chip and counted as needing a human
eye. Coverage **124 → 143 of 246 contracts**; 303 authority blocks, 324 Π.Ε.
rows, 576 δήμος assignments, 534 agreeing with every Π.Ε. the documents state,
0 contradicting one.

*Affects: `scripts/extract_contract_municipalities.py` (Places.run, groups_after,
statements, dedupe, call source) and `tests/test_contract_municipalities.py`
(13 units on real sentences). Still proposals only — no DB, no API, no page.*

## 2026-08-19 — Forest services: the completion acts name them, the official directory guards the list, and jurisdiction is recorded where it crosses a Π.Ε.

Three findings from a session of user review, all of them starting with the
same question — which forest service works where.

**1 · The Diavgeia completion acts name the service, and nothing else does.**
ΥΠΕΝ signs one «Έγκριση Πρωτοκόλλου Παραλαβής» per accepted part and says
whose area it was: «…για την περιοχή αρμοδιότητας **των Δασαρχείων Πάρνηθας,
Λαυρίου, Καπανδριτίου και Πεντέλης**». 275 of the 283 stored acts do this.
For the region-scoped «άμεσης διαχείρισης» contracts — written for a whole
Περιφέρεια because the work follows fires — it is the ONLY statement of who
executed them. `forest_loader.completion_authorities()` reads them AFTER the
contract's own text, so they can only ADD: **28 links across 14 contracts**.
24SYMV015162689 («ΕΡΓΑ ΑΝΤΙΠΥΡΙΚΗΣ ΠΡΟΣΤΑΣΙΑΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ», €4,85M)
went from no service at all to six, and its `no_authority` entry was retired
with the reason kept. In-scope coverage **243 → 245 of 246**; the one left,
25SYMV017328637, says only «το αρμόδιο Δασαρχείο είτε η Διεύθυνση Δασών κατά
περίπτωση» and has no completion act yet.

**2 · Two services were missing from the matcher's list, and the guard could
not see them.** The user asked how the complete ΥΠΕΝ list they supplied was
not in the matching process. Measured answer: the 151-unit
`forest_units_directory.json` is the REFERENCE layer and the 103-entry
`forest_authorities.json` is the matcher's whitelist; `audit_authority_links`
exists precisely to check the second against the first and reported zero
missed links — because it read titles, items and PDF bodies, and **not the
completion acts**, which had just become a source. Sweeping every source with
the full vocabulary: 16 mentions over 14 contracts, 13 of them a parent
Διεύθυνση named beside its own child Δασαρχείο (letterhead, correctly
ignored) and **2 real gaps**: ΔΔ Ευβοίας (named only in act ΡΧΗ04653Π8-ΥΥ1)
and ΔΔ Κιλκίς (act 9ΜΖΔ4653Π8-ΑΕΝ). Both added — registry 103 → **105**.

Merging all 32 directory-only units into the registry was tried and
**reverted**: it produced exactly one new link and would have added 31
services that appear in no contract, listed twice on /authorities (once as
empty authorities, once as «the rest of the network»). The directory stays
the audit vocabulary; the audit now covers completion acts too, with the
parent/child suppression made honest by giving directory units their Π.Ε.
Re-run against the pre-fix registry it reports exactly the two gaps, which is
the regression test for this whole class.

**3 · `covers_pe`: a service's reach beyond the Π.Ε. of its seat.**
`region_pe` has always meant where the office IS — it places the map dot.
Contracts, though, put services to work across boundaries, and the check
«is this δήμος in the service's Π.Ε.» kept flagging real jurisdiction as
suspect. Confirmed by the user and recorded per authority with the reason:
Αιγάλεω → Δυτικής Αττικής, Πειραιά → Νήσων, Πεντέλης → Ανατολικής/Κεντρικού/
Νοτίου Τομέα, Πάρνηθας → Δυτικής Αττικής, ΔΔ Σάμου → Ικαρίας («στην οποία
υπάγεται το τοπικό Δασονομείο Ικαρίας»), ΔΔ Δωδεκανήσου → Κω («το Δασονομείο
Κω υπάγεται απευθείας στη Δ/νση Δασών Δωδεκανήσου»), ΔΔ Κεφαλληνίας →
Ιθάκης («δεν διαθέτει ξεχωριστή Διεύθυνση Δασών»), and Φουρνά → Καρδίτσας
which the user accepted **explicitly without independent confirmation**, the
note saying so and naming the two services that could contradict it.

*Affects: `khmdhs/forest_loader.py` (+completion_authorities),
`scripts/audit_authority_links.py` (+completion-act pass, Π.Ε. for directory
units), `khmdhs/data/forest_authorities.json` (2 new services, 8 covers_pe,
1 alias «ΣΠΕΡΧΙΑΔΑΣ», 1 retired no_authority), both copies of
`authority_names_en.json`, and the count pins (103→105 authorities,
489→500 authority↔contractor edges).*

## 2026-08-19 — Work locations, second pass: the reading trail, the second document dialect, and the first curated verdicts

Continuing the municipality layer (previous entry), after the user rejected
reviewing 143 contract cards one by one — «you are not helping me do the
revision … you need to have better options».

**The review unit is the pair, not the contract.** Collapsed to one row per
(forest service → δήμος) — **290 pairs over 220 δήμοι** — each carrying what
independently backs it: the contract and its πρόσκληση saying the same, the
Π.Ε. named in that sentence, the NUTS code printed beside it, the service's
registered reach, and other contracts asserting the same pair. 251 have three
or more, 33 two, 6 remain open. The registry's own NUTS column is useless for
this (121 of its 124 rows say «EL»).

**The extraction follows the user's own method** (2026-08-19): the contract's
title first, then the award's ΘΕΜΑ, then the call — whose title says whether
it covers this contract alone or several τμήματα, and whose «οι προς
παρέμβαση εκτάσεις» / «οι εργασίες αφορούν» paragraphs carry the detail —
and last the contract body. Every contract now carries that trail: 246
contracts, 1.243 steps, each with the document, the anchor and the verbatim
quote, so a proposal can be read back to its source instead of appearing from
nowhere. The SECTION NUMBER is never assumed — «τόπος εκτέλεσης» sits at §2.6
in 60 calls, §2.4 in 32, §2.7 in 24 — the anchors are phrases and the number
is read off the text.

**A second document dialect** was found and added: the 2025 «επείγουσες
υλοτομικές εργασίες» calls write «…ανήκουν στην περιοχή ευθύνης των
Δασαρχείων Θεσσαλονίκης, Λαγκαδά και Σταυρού, ενώ **διοικητικά ανήκουν**
στους Δήμους Ωραιοκάστρου, … εντός των Δημοτικών Κοινοτήτων Μεσαίου και
Πενταλόφου της Δ.Ε. Καλλιθέας». Coverage 143 → **153 of 246 contracts**
(70% of the stated net €); 93 contracts still name no δήμος anywhere, which
is what their documents say and the trail states plainly.

**Reading bugs the review exposed**, each fixed and pinned: the authority may
be named AFTER the δήμοι («χωροθετούνται … αρμοδιότητας Δασαρχείου Ολυμπίας»);
one authority can hold TWO Π.Ε. groups and stopping at the first dropped five
δήμοι; «ΚΑΙ» as a separator swallowed the first three letters of Δήμος
**ΚΑΙ**σαριανής; a group may state only «(NUTS: EL303)» with no Π.Ε. name; the
opening summary sentence («αρμοδιότητας των Δ/νσεων Δασών Άρτας, Θεσπρωτίας
και Κέρκυρας») must NOT hand its δήμοι to every service it lists — the
per-Π.Ε. groups that follow are the attribution; and «Δασαρχείου Σπερχιάδας»
(without the ε) matched nothing, so Μακρακώμη was filed under Λαμίας.

**First curated verdicts** (`khmdhs/data/municipality_overrides.json`, 17):
where a contract assigns a δήμος to a service that does not serve it, the
δήμος is NEVER dropped — the attribution is re-attributed when the competent
service is a party to the SAME contract (Αρριανών → ΔΔ Ροδόπης, Σπάρτης →
Δασαρχείο Σπάρτης, Μαλεβιζίου → ΔΔ Ηρακλείου) and kept as stated with the
competent service named in the note when it is not (Δίου-Ολύμπου, Παρανέστι,
Ελασσόνα, Σέρβια, Τανάγρα, Ιεράπετρα). The user's rule; their wording is the
note.

*Affects: `scripts/extract_contract_municipalities.py`,
`municipality_curator.html`, `khmdhs/data/municipality_overrides.json`,
`tests/test_contract_municipalities.py` (16 units). Still proposals — no DB
table, no API, no page until the curation closes.*

## 2026-08-19 — In /explore an Anti-nero row is a CONTRACT, not a ΚΗΜΔΗΣ record; and the contract page draws its chain on the programme axis

Searching `25SYMV017345053` returned nothing, although that record IS the
€4.167.192,11 σύμβαση. /explore ships in-scope contracts only, and this one is
out of scope because a later act on the same file (26SYMV018978343, «Έγκριση
συμπληρωματικών εργασιών») is the chain tip.

**«Superseded» was the wrong word for this**, as the user said. Of the 60
excluded parents the later record is a τροποποίηση όρων in **32**, a παράταση
προθεσμίας in **12**, an έγκριση συμπληρωματικών in **12** and a contract in
**4** — and **57 of 60 carry the parent's exact value**. Nothing is replaced.
The exclusion exists for ONE reason: count each chain once, at its tip.

**The row is now the chain.** `queries_extra.contract_chains()` walks
`contract_scope.superseded_by` transitively (it is a one-hop linked list) →
**50 chains: 42 of two records, 7 of three, 1 of five**, 110 records in all.
Additive supplementary CONTRACTS never enter it — both they and their parent
stay in scope, and only an out-of-scope record carries `superseded_by`, so
23SYMV013600200 and its 1η συμπληρωματική stay two rows as they must.

Four presentation decisions, all the user's:
- **date** «first → last» (22.10.2024 → 09.03.2026), sorting on the first, so
  the date column keeps meaning «when it was contracted»;
- **the original's title, the tip's page** — 7 of 50 tips are titled «1η
  Τροποποίηση…» and 21 of 50 are cover notes under 12 kB, but the tip is the
  record holding the current state;
- **every record listed under the title** with what it IS, in the 2026-08-18
  vocabulary, and **every ΑΔΑΜ of the chain searchable** (`alt`), so citing an
  earlier version finds the contract instead of nothing;
- value stays the tip's: Σ of the Anti-nero rows still reconciles to
  **€625.897.613,96**, and no ΑΔΑΜ appears in two rows (both pinned).

**The contract page gains a timeline** — `$lib/detail/ChainTimeline.svelte`,
the sponsor pages' ActTimelineBar one level down: same 920×H box, same 10px
axis in `--ink-faint`, same dashed «today» rule drawn last, same two-way hover
with the trail (`highlight` / `onRowHover`, which DocTrail already supported).
It draws the bar from signature to the day the work was accepted, a dot per
later act, **a tick per payment order** — which no other view puts on a time
axis — the ✔ of the completion act, and the printed **€ step** where a
supplementary approval moved the price («€3,78M → €5,00M» on the Πάρνηθα
chain, invisible until now). The axis is FIXED (2022-01-01 → today + 5 days)
so two contract pages compare by eye, as the sponsor bars do. A contract with
no acceptance on record is drawn faint and uncapped, so «we do not know when
it ended» never reads as «it ended».

The chain reaches the page as `contract.chain` (`queries_extra.contract_chain`)
because the registry cannot supply it: `adamChain` links an upstream act for
only 40 of 245 in-scope contracts, and the version links live in
`prev_reference_no` / `superseded_by`. The trail now folds those records in
too — before this, a contract's own amendments existed on the site but not on
its page.

Data behind the bar: 246/246 in-scope contracts have a signature date, 148
have a Diavgeia completion act, 226 have payments, 22 have a registry end
date, and **207 of 246 have three or more dated events**.

*Affects: `atlas_api/queries_extra.py` (`contract_chains`, `contract_chain`,
`explore_rows`), `atlas_api/app.py`, `atlas/src/lib/detail/ChainTimeline.svelte`
(new), the /explore and contract pages, `/methodology#explore`,
`tests/test_atlas_real_db.py` (2 pins) and `atlas` vitest (5 units). No
loader, no DB change, no basis change.*

---

## 2026-08-19 · The procurement's own acts join the contract timeline, and one acceptance act stops standing for a whole contract

Two corrections to the contract page, both from the user reading
`/antinero/contract/26SYMV018978343`.

**1 · The run-up.** The timeline drew the contract's life from its signature
onward, while the document trail directly below it listed the acts that
produced it — primary request, commitment approval, call, award — with their
dates, unplaced. They are now marks on a dotted **run-up** to the signature
(`ChainTimeline.runUp`), diamonds rather than the bar's dots because they are
acts of the procurement, not of the contract, which did not exist yet.
Measured: **217 of 246** in-scope contracts have at least one dated upstream
act (41 request, 41 commitment approval, 217 call, 130 award), **41** have all
four, **none** is dated after the contract it produced and none falls before
the programme axis opens — pinned, because a mark outside the axis would be
drawn off the frame rather than seen. Same-day acts (a request and its
approval routinely share a date) nudge apart 6 units and print only the first
label; the hover card and the trail row carry the rest.

**2 · A part acceptance is not a jurisdiction.** 26SYMV018978343 showed
«Area within the jurisdiction of: Chalkida Forest Service Office» while its
map showed seven Attica regional units. Both were right about their own
source and the page let them contradict each other: the contract is a
region-scoped «άμεσης διαχείρισης» one whose text names **no** forest
service, so its only link came from `forest_loader.completion_authorities` —
and that act reads «Βεβαίωση περαίωσης … χωρικής αρμοδιότητας Δασαρχείου
Χαλκίδας … **– για το τμήμα του έργου** με τίτλο "Υλοτομία Ξηρών ιστάμενων
κωνοφόρων στο σύμπλεγμα Δίρφυος…"». It accepts **one part**, in Εύβοια, of
works curated across Attica. The link is kept — the act does name it — but
now carries `source = completion_act:<ΑΔΑ>|part`, and the page prints
«named by an acceptance act covering one part of the works; the contract
itself names none». **1 of the 29 completion-act links** is a part
acceptance; the other 28 are unchanged. (Loader gotcha, the fifth time:
`fold()` maps Greek onto Latin homoglyphs, so the needle «ΓΙΑ ΤΟ ΤΜΗΜΑ» has
to be folded too — the raw Greek literal matched nothing and the first run
silently marked zero rows.)

*Affects: `khmdhs/forest_loader.py`, `atlas/src/lib/detail/ChainTimeline.svelte`,
`atlas/src/routes/antinero/contract/[adam]/+page.svelte`,
`tests/test_atlas_real_db.py` (2 pins). No basis change, no count change —
725 contract links, 245/246 in-scope covered, as before.*

---

## 2026-08-19 · The contract timeline draws the time the contract was GIVEN, and every number on the page names its source

Four corrections from the same reading of `/antinero/contract/26SYMV018978343`,
all of them the same principle: a page may not show a fact without showing
where it came from, and a bar may not measure something other than what it
says it measures.

**1 · The bar is the promise, not the paperwork.** It ran signature →
completion act, which measures when the file was closed: a project accepted
two years after the works finished looked like a project that ran two years.
It now runs **signature → the deadline the contract announced**, with the
sponsor pages' lighter stretch for each «Παράταση προθεσμίας» that moved it,
the extension's arc dipping under the bar to the new date, and the ✔ of the
acceptance left as a mark that may well fall after the deadline — which is
the reading. Two ΚΗΜΔΗΣ fields say what was announced, and neither is a
sentence of the signed text: the record's **end date** (21 of 246 in-scope)
and the **stated duration** counted from the start date (62 more; the unit is
read as months where the record omits it, and the page says so). For **8**
the σύμβαση announces nothing and a later act of the chain does — that date
is then the only one on record and is labelled `basis: act`, never passed off
as the original's. The remaining **155 announce nothing at all** and get the
Gantt's stub: no invented span. **6 chains** had their deadline moved, in
**8 steps**. `queries_extra.contract_deadlines()`; counts ship as
`/api/meta` facts so the methodology paragraph cannot go stale.

**2 · Where the duration comes from is now on the page.** The facts row
showed a number with no provenance. The evidence block gains a
**«Duration and deadline — ΚΗΜΔΗΣ record fields»** entry quoting the record's
own ΔΙΑΡΚΕΙΑ / ΕΝΑΡΞΗ / ΛΗΞΗ verbatim and saying in one line that they are
*recorded in ΚΗΜΔΗΣ, not quoted from the signed text* — the honest statement,
since no document sentence was read for them.

**3 · Where the jurisdiction comes from is now on the page.** Contracts whose
forest service is named only by a Diavgeia acceptance act now quote that act
in the evidence block, linked to its PDF — and where the act accepts one part
of the works (26SYMV018978343), the note says the quote does not describe the
whole contract.

**4 · Those excerpts were unquotable.** `Matcher.find()` cut its window out of
the FOLDED text, so the stored evidence read «XΩPIKHΣ APMOΔIOTHTAΣ ΔAΣAPXEIOY»
— Greek words spelled half in Latin. Matching still happens in the folded
alphabet; the excerpt is now cut from the **original** subject at the same
offsets (verified per call, folded window as fallback) and trimmed to word
boundaries with «…» where it is cut. All 725 links re-loaded; pinned so a
folded excerpt fails the suite.

Presentation, same session: the run-up acts are grey dots rather than
diamonds, payment orders are **€** marks on the same line as everything else,
the «today» lettering sits on the year line where the axis is read, and the
printed dates under the bar are gone — the marks carry their dates in their
hover cards and the trail below prints them all.

*Affects: `khmdhs/forest_loader.py` (`_excerpt`, unfolded excerpts),
`atlas_api/queries_extra.py` (`contract_deadlines`, meta facts),
`atlas_api/app.py`, `atlas/src/lib/detail/ChainTimeline.svelte`, the contract
page, `/methodology#contract-timeline`, `tests/test_atlas_real_db.py` (2 pins).
No basis change, no count change.*

---

## 2026-08-19 · The Anti-nero contract page, reorganised (user, same session)

Presentation only — no number, basis or curated verdict changed.

- **The payment orders moved into the document trail.** They are documents of
  the contract with a date, a code and a PDF, and reading them in a separate
  table meant reading the contract's story twice. The amount rides in the
  title cell (net · incl. ΦΠΑ), the Διαύγεια act keeps its own link through a
  new optional `alt` link on `TrailRow`, and the live-orders/paid total stays
  as one line under the table. The standalone PAYMENT ORDERS section is gone.
- **«DOCUMENT TRAIL–TIMELINE» is now «DOCUMENT TRAIL»**, on all three detail
  pages — the timeline is no longer inside it. On the Anti-nero page it stands
  above the trail as its own **TIMELINE** section with its methodology note.
- **Every section title carries an arrow** (`$lib/ui/Fold.svelte`, native
  `<details>`): TIMELINE and DOCUMENT TRAIL open on arrival, PROCUREMENT
  DETAILS, EXTRACTED QUOTES and CPV CODES wait to be asked for. `DocTrail` and
  `QuoteList` accept `heading={null}` so the fold prints the title once.
- **EXTRACTED QUOTES and CPV CODES sit side by side** (2fr/1fr, stacking under
  900px); the CPV list keeps its 12-code cap with a «… N more» toggle.
- **The map is cropped to the contract's own ground** — the centroids of its
  work regions plus its authority seats, grown to a 1,4° × 0,9° floor and
  handed to PaperMap as a box, because PaperMap refuses a degenerate one and
  a single-region contract (the common case) was getting no crop at all. The
  MAP / DIAGRAM switch sits ON the frame's corner at 10px, so choosing a view
  costs no vertical space; «Contracts under the same call» is now «Diagram».
- **The timeline's two label rows were overprinting.** Act labels
  («supplementary», «revision») now suppress a label within 62 units of the
  previous one, the extension ordinal moved BELOW the bar onto its own row
  («1st extension»), and the € marks step aside from act dots and from each
  other. Acts label above the bar, extensions below; nothing shares a row.
- **The duration quote cites the record it was read from.** On a chain the
  deadline comes from the σύμβαση while the viewed record is the tip, whose
  own ΕΝΑΡΞΗ/ΛΗΞΗ are a different statement — 26SYMV019098206 was quoting
  09.03.2026–31.05.2026 under a bar drawn to 21.01.2026. `contract_deadlines`
  now returns the `fields` it used (ref, duration, unit, start, end) and the
  note names the act that extended them.

*Affects: `atlas/src/lib/ui/Fold.svelte` (new), `$lib/detail/DocTrail.svelte`,
`$lib/detail/QuoteList.svelte`, `$lib/detail/ChainTimeline.svelte`, the
Anti-nero contract page, `atlas_api/queries_extra.py` (`contract_deadlines`
`fields`).*

**Open question the user raised, not yet built:** the duration is still a
ΚΗΜΔΗΣ record field, not the contract's own sentence. The cached texts DO
carry it — «Η συνολική προθεσμία ολοκλήρωσης του έργου ορίζεται σε τρεις (3)
μήνες από την υπογραφή της παρούσας σύμβασης» — present in **212 of the 246**
in-scope texts, and it also states the START BASIS (signature vs έναρξη
εργασιών) that the registry field never gives. That is a study_costs-shaped
task: extractor → review file → curated `data/contract_durations.json` →
loader → table, with the registry field kept as the cross-check.

---

## 2026-08-19 · One basis on the page: net of ΦΠΑ, everywhere (user decision)

The Atlas has been net-of-ΦΠΑ since 2026-08-03, but the detail pages still
printed the registry's gross beside each net figure — «5,00 M € · 6,20 M €
incl. ΦΠΑ», an «incl. ΦΠΑ» column in the payments table, a gross tail on the
paid total. Two bases side by side is two things to keep straight for no gain,
so the secondary figures are **removed**: the Anti-nero and ΔΑΣΕ contract
pages now show net only, and the methodology says the site is net throughout
rather than promising a gross line on detail pages. The gross stays available
in the API payload (`gross`) and in `main.contracts` — nothing was recomputed,
nothing moved basis. Checked after the change: 26SYMV019098206 states
€4.999.994,82 net, its six live orders sum to €4.771.705,65 and the page's
paid figure is the same number.

Same session, same page:

- **TIMELINE and DOCUMENT TRAIL lost their arrows** — they are what the page
  is, not reference material to unfold. PROCUREMENT DETAILS, EXTRACTED QUOTES
  and CPV CODES keep theirs.
- **The timeline pairs with the trail on every element, both ways** (user):
  the run-up acts, the acts of the chain, each payment order (€), each
  extension arc and its label, the ✔ of the acceptance act and **the bar
  itself** all highlight their trail row on hover and light up when their row
  is hovered — the ✔ and the bar needed identities to pair with, so
  `ChainTimeline` takes `endRef` and `signedRef`. Verified row by row on
  26SYMV019098206: all 15 trail rows go black and every one of them lights a
  mark (the extension lights three — its dot, its arc and its label).
- **The detail map frames whole regions, not centres.** A frame built from
  centroids cut Εύβοια in half on 26SYMV018978343 — Attica works whose only
  named service sits in Χαλκίδα. `PaperMap` gained `fitPes`: fit these Π.Ε.
  **whole**, merged with any `fitPoints`. The contract page passes its work
  regions plus every authority's seat region, so the map shows the ground the
  contract touches and the island the accepting service is on (verified: the
  fitted window contains the Ευβοίας polygon bbox with margin).

*Affects: the Anti-nero and ΔΑΣΕ contract pages, `$lib/detail/ChainTimeline.svelte`,
`$lib/maps/PaperMap.svelte` (`fitPes`), `/methodology#net-basis`.*

---

## 2026-08-19 · The call mark carries what the diagram knows (user: «the cheap version, try it»)

The procurement diagram answers a relational question — who else won a lot
under this call — and the timeline answers a temporal one. Merging them would
put sibling bars on a contract's own axis and drown it. What the timeline was
missing is smaller: the call was already ON it, as a run-up dot, but said
nothing about having produced other contracts.

So the call's mark is now **filled, labelled «call · 1 of N», and clickable**:
its card names the lots and their Σ stated net €, and clicking it swaps the
header slot to the DIAGRAM view and scrolls it into the middle of the frame.
No new data, no second chart, one extra fact on a mark that was already
drawn. `ChainTimeline` takes `callInfo` ({ref, lots, total}) and `onCallClick`;
the page passes them from `contract.family`, so the mark appears only where a
call produced more than one contract. The label's underline was dropped — the
paper halo behind these labels turns one into a strike through the words.

*Kept if the user keeps it — offered as the try-it version of the merge.*

---

## 2026-08-19 · Timeline ink (user review)

- **Marks on the bar print white, marks off it print dark.** The act dots
  carried a paper fill and an ink outline; on the black bar that read as a
  ring. They are now flat white with no stroke — but only where they actually
  sit ON the bar, since a white dot on white paper is no dot at all. The €
  payment marks follow the same rule. «On the bar» means the SOLID stretch
  only: the extension is the same ink thinned, and white on 30% ink is
  invisible, so marks over an extension print dark.
- **The extension is black at 30%, not green.** It borrowed the sponsor
  Gantt's `EXT_COLOR` (#b7e4c7), which on an Anti-nero page reads as the ΔΑΣΕ
  dataset's colour. Same ink as the bar, thinned — the segment says «still the
  same contract, extended», which is what it is.
- **The call label was overprinting the request label** («rcall·1 of 5» on
  26SYMV019098206): a primary request and its call are days apart on a
  four-year axis, and forcing the call's label to always draw bypassed the
  collision rule. Run-up labels are now claimed greedily with the **call
  first** — it is the one that says something — and the others only where they
  still fit, measured against each label's own width.

*Affects `$lib/detail/ChainTimeline.svelte` only.*

---

## 2026-08-19 · Proposals: what the works ARE, and how long the contract had

Two layers read from the same cached contract texts in one pass, both
PROPOSALS — nothing is in the database, the verdicts come next
(`scripts/extract_contract_details.py` → `data/processed/contract_details_review.json`
+ the committed `contract_details_curator.html`).

**1 · Work themes — multi-label, from the contract's own project title.**
The curated category gives each contract ONE key and 154 of 246 land in
«Δασοτεχνικά έργα πρόληψης». The titles say more: **155 contracts name at
least one specific kind of work and 101 name two or more** — «…για τον
καθαρισμό των δασών και δασικών εκτάσεων ΚΑΙ τη συντήρηση του δασικού οδικού
δικτύου…». Twelve themes (`khmdhs/work_themes.py`), each hit carrying the
verbatim clause: αντιπυρικές ζώνες 84 · δασικό οδικό δίκτυο 75 · καθαρισμοί
59 · μικτές/εστεγασμένες ζώνες 37 · αρχαιολογικοί χώροι 18 · αναδασώσεις 15 ·
μελέτες 14 · αντιδιαβρωτικά 13 · υλοτομίες 7 · δασοκομικά 6 · υδατοδεξαμενές
2. **91 contracts state nothing beyond «αντιπυρική προστασία»** and stay that
way.

Three sources were tested and rejected as per-contract evidence: the
contract's «Αντικείμενο της Σύμβασης» article (boilerplate in all 206 that
carry it — it points to the call's annexes, which ΚΗΜΔΗΣ does not publish);
the πρόσκληση's own text (4–10 themes per call, because it lists the
programme's menu, not the lot's work — measured on the 91 cached calls); and
the CPV codes (median 14 per contract, top code on 226 of 246, the set
belongs to the call). CPV is kept as a **screen**: 9 marker codes raise a
question on **56 contracts** — «your CPV list names δεξαμενές νερού and your
title names no water works, which is right?» — with the two boilerplate codes
(«συντήρησης οδών» on 130, «ψηφιακής χαρτογράφησης» on 119) deliberately not
markers, because asking 156 times would bury the questions worth asking.

**2 · Duration — the deadline the contract states, and the clock it starts.**
`khmdhs/contract_durations.py` reads «Η συνολική προθεσμία … ορίζεται σε
τρεις (3) μήνες από …» through the chain. **246 of 246 in-scope contracts
state one** (the registry field has a number for 83 and never says what it
counts from), and **243 state the start basis**: 187 «από την έναρξη των
εργασιών», 51 «από την υπογραφή», 5 other.

The finding worth the work: **the ΚΗΜΔΗΣ duration field matches the signed
contract in 3 of the 66 cases where both exist.** 43 of the registry's
figures carry no unit at all and differ from the document (3 μήνες in the
text against a bare «21», «23», «6»), and 20 say «Μήνες» with a different
number (3 against 5). The Atlas currently reads that field.

Five traps, all now pinned by tests: the anchor also matches the PENALTY
article («ποινική ρήτρα ίση με δεκαπέντε τοις εκατό (15%) … ανά ημέρα» read
as 15 days on 65 contracts) → the clause must DEFINE something and the reject
test runs on the defining part only; a design-build contract states the
μελέτη's 20 days and the works' 3 months → the ΕΡΓΟ clause wins and a
study-only read is marked; «…ΦΠΑ 24%. Άρθρο 3 Διάρκεια Σύμβασης…» → the
percent guard belongs to the head, not the preceding paragraph (16
contracts); phase-II PDFs render every accent as a separate letter
(«οριέζεται», «μηέ νες») → `loose()` tolerates a stray vowel AFTER A VOWEL,
which is exactly where the artefact puts it (66 contracts); and
«Μήνες».upper() is «ΜΉΝΕΣ», so the registry comparison folds accents or every
agreement reads as a difference.

Next: the user's verdicts → curated `contract_work_themes.json` /
`contract_durations.json` → loaders → the contract page reads the document
first and the registry field becomes the cross-check.

---

## 2026-08-19 · The two layers land: what the works are, and the time the contract had

The user reviewed the RULES rather than 246 rows (the proposals are quotes,
not judgements) and settled four:

1. **A contract shows every theme its title states** — 101 of 246 name two or
   more, and one category could not carry them.
2. **The 91 that state nothing say so** — «the contract states no further
   detail», with the CPV list left visible below as what the procurement
   covered. Borrowing the call's list was rejected: each πρόσκληση names 4–10
   kinds because it lists the programme's menu.
3. **CPV never adds a theme.** Where a marker code names work the title does
   not (56 contracts, almost all «Δεξαμενές νερού»), the page carries a line
   — «the procurement's CPV codes also cover water tanks» — and nothing else.
4. **The document is the source for the deadline, the registry the
   cross-check.**

Curated files written from the proposals under those rules, each with an
`_overrides` block the extractor merges on re-run:
`khmdhs/data/contract_work_themes.json` (193 contracts — 155 with themes, 56
with CPV notes) and `khmdhs/data/contract_durations.json` (246).
`khmdhs/details_loader.py` → `contract_work_themes` (330 links) +
`work_theme_labels` + `contract_cpv_notes` + `contract_durations`; in the
refresh chain after categories_loader, FK CASCADE like every child table.

**The fire season is a date, not a vagueness** (user, 2026-08-19): Greece's
runs **1 May – 31 October**, so the three «άμεσης διαχείρισης» contracts whose
time is «η αντιπυρική περίοδος του έτους 2024/2025» have a real deadline —
the 31 October of that year. The same window the front-page timeline shades.

**Consequence for the timeline.** The bar now measures the deadline the
CONTRACT states: `contract_deadlines` reads the curated duration first and
falls back to the registry only for a contract added since the last curation
run. Every in-scope contract now has a drawn span — **243 `document` + 3
`document_season`**, where before **155 had no deadline at all and drew a
stub**. Extensions rose from 6 chains / 8 steps to **14 / 16**, because a
deadline that exists can now be seen to move: 9 «Παράταση προθεσμίας» records
and 7 supplementary approvals carrying a later end date, and the chart labels
which of the two it is rather than calling both «extension».

The contract page: TYPE carries the category chip and the themes under it;
DURATION reads «5 months from signature · As stated in the signed contract
22SYMV010447496»; the evidence block gains one quote per theme and the
deadline sentence, with the ΚΗΜΔΗΣ figure named where it differs.
`/methodology#contract-timeline` rewritten on the same basis.

*Affects: `khmdhs/db.py` (4 tables), `khmdhs/details_loader.py` (new),
`khmdhs/refresh.py`, `scripts/extract_contract_details.py` (`--curate`),
`atlas_api/queries_extra.py` (`contract_work_themes`,
`contract_stated_duration`, `_document_deadline`), `atlas_api/app.py`, the
Anti-nero contract page, the methodology, `tests/test_contract_details.py`
(16 units) and the real-DB pins. No basis change — themes and durations are
descriptive layers, no euro moved.*

---

## 2026-08-19 · The municipality layer lands: which δήμος each contract worked in

The finest location the site published was the Π.Ε. Now it is the δήμος,
where a document names one — read from the same kind of sentence the forest
services come from: «ΕΝΤΟΣ ΤΩΝ ΔΗΜΩΝ ΧΑΪΔΑΡΙΟΥ ΚΑΙ ΑΣΠΡΟΠΥΡΓΟΥ,
ΑΡΜΟΔΙΟΤΗΤΑΣ ΔΑΣΑΡΧΕΙΟΥ ΑΙΓΑΛΕΩ».

**Rules the user approved** (rows never, rules only):

1. **The πρόσκληση counts as evidence.** Its sentence is per-lot and names
   the δήμος and the service together, and the contract cites it — 79 of the
   595 rows are read that way and the page says which document said it.
   (Unlike the work-themes case, where the call lists the programme's whole
   menu and was rejected as per-contract evidence.)
2. **A δήμος outside the contract's curated Π.Ε. is recorded and flagged.**
   The document is what it is; the region layer is deliberately left alone,
   so no euro moves on any map or chart. Asked what the 49 such rows were,
   the registry answered most of it: **30 sit in a Π.Ε. the naming service is
   already recorded as administering** (`covers_pe` — Πεντέλης covers Ανατ.
   Αττική, Αιγάλεω covers Δυτ. Αττική, Σάμου covers Ικαρία), **11 are in
   that service's own seat Π.Ε.**, and **6 carry a verdict the user had
   already given** in `municipality_overrides.json`. So the flag now means
   «nothing accounts for this» and **2 rows** keep it — both on
   26SYMV019488828, a Ζάκυνθος/Άρτα/Πρέβεζα contract whose text also names
   «στους Δήμους Λαυρεωτικής και Σαρωνίδας» and whose acceptance act names
   Δασαρχείο Λαυρίου. `outside_pe_explained` carries the reason and the page
   says it on hover.
3. **Pre-Καλλικράτης names and settlements resolve to today's δήμος**:
   ΘΕΣΠΙΕΩΝ → Θηβαίων (ν.3852/2010 merged it), ΠΑΠΑΓΟΥ → Παπάγου-Χολαργού,
   ΣΑΡΩΝΙΔΑΣ → Σαρωνικού (a settlement, never a δήμος) — each keeping the
   document's own wording. **Every one of the 220 names now resolves**; the
   review file's «unresolved» column is empty.
4. Δημοτικές ενότητες are still not recorded (earlier user decision).

**Result: 595 rows over 153 contracts and 220 δήμοι.** The other 93 in-scope
contracts name none and the page says «the documents name no municipality»
rather than guessing.

**The contract page header changed** (user, same session): «AREA WITHIN THE
JURISDICTION OF» is now **AREAS OF INTERVENTION** — the δήμοι, with the
regional units under them and the document that named them — and
**RESPONSIBLE FOREST SERVICE BODY** follows it with the Δασαρχεία /
Διευθύνσεις Δασών. The evidence block quotes one sentence per group of
δήμοι, linked to the contract or the call it came from.

**The map outlines them.** Greece publishes no municipality polygon file we
could use directly, and the machine's only geopandas has shapely 2.0 (no
`coverage_simplify`) — but the two committed layers already contain the
geometry between them: polygonising each Π.Ε.'s outline together with its
interior municipality borders reproduces its δήμοι exactly, with shared
vertices and no slivers. `scripts/build_muni_polygons.py` does that, names
each polygon by the ΥΠΕΣ representative point inside it (islands of a
mainland δήμος go to the nearest one within the same Π.Ε.), and writes
**all 325 at ~250 m / 4 decimals — 611 KB**, fetched lazily and only by a
contract page that names a δήμος.

**/explore filters by δήμος** (user, 2026-08-19): the payload carries `mu`
on the 153 Anti-nero rows that have one — absent, not empty, on the rest —
the facet lists the 220 δήμοι by contract count, the names join the
Greeklish-tolerant search index, and `?mu=…` is a shareable permalink like
every other filter. Only Anti-nero rows carry it; the other two datasets
have no municipality layer, and the label says so.

*Affects: `khmdhs/db.py` (`contract_municipalities`),
`khmdhs/municipalities_loader.py` (new, in the refresh chain),
`khmdhs/data/contract_municipalities.json` (curated, `_overrides` merged on
re-run), `scripts/extract_contract_municipalities.py` (`--curate`, 3
aliases), `scripts/build_muni_polygons.py` (new),
`atlas_api/queries_extra.py` + `app.py`, the contract page and its map,
`/explore`, `tests/test_atlas_real_db.py` (3 pins). No basis change: the region layer, the maps
and every aggregate are untouched.*

---

## 2026-08-19 · The Anti-nero contract card, to the sponsored-works template

User review of the card, and one data error it turned up.

**The card.** Its second column now reads like the sponsored-works one:

- **one language.** The work type prints its **English** label — eight added
  to `contract_categories.json` (`label_en`), the Greek kept as the hover
  title — and the awarding procedure prints Directive 2014/24/EU's own
  wording via `$lib/transforms/procedures.ts`: «Ανοικτή διαδικασία» → *Open
  procedure*, «Διαπραγμάτευση χωρίς προηγούμενη δημοσίευση» → *Negotiated
  procedure without prior publication*, «Κατεπείγουσα ανάγκη οφειλόμενη σε
  γεγονότα απρόβλεπτα…» → the Directive's art. 32(2)(c) ground in its
  English. «Απευθείας ανάθεση» has no Directive equivalent — άρθρο 118 is
  Greece's own below-threshold route — so it keeps *Direct award* with its
  article reference. Article numbers stay literal: identifiers, not prose.
- **no chip on the type** — the value is plain text, like every other value.
- **explanations moved into hover cards** (`$lib/ui/Hint.svelte`): the grey
  half-lines under values (which document dated the record, why a duration
  was assumed, why a forest service is named by an acceptance act, what a
  CPV note means) are now a small marker with the same black rectangle the
  maps and charts use. Everything they say is still in the evidence block.
- **one label column width across the detail pages** (15,5 rem), so long
  labels wrap — «RESPONSIBLE FOREST SERVICE BODY», «AMENDMENTS TO ORIGINAL
  CONTRACT» — instead of pushing the values sideways, and label and value
  both start at the top of their row.
- **the map's bottom edge meets the last line of the caveat**, as on the
  sponsored pages: its width is the template's and never moves, its viewBox
  takes the measured column width and the facts height. The caveat now says
  what the map shows (shaded regional units, outlined municipalities, forest
  service seats). The hover label is the sponsored map's **black card**.

**The error.** Asked why 25SYMV016659302 reads «cancelled», the registry
answers: ΥΠΕΝ cancelled it on 15.10.2025, «ΛΟΓΩ ΛΑΘΟΥΣ ΣΤΟ ΑΝΑΡΤΗΜΕΝΟ
ΑΡΧΕΙΟ». It was **re-posted six days later as 25SYMV017779215** — same
title, same signature date 10.04.2025, same €3.363.432,24, same contractor
and ΑΦΜ, same three forest services; the re-posting carries the 4 payment
orders. Both are in scope, so the basis counts that contract twice:
**€625.897.613,96 → €622.534.181,72**, 246 → 245 contracts. **Applied the
same day** on the user's word.

*Also noted: the trail of 24SYMV014843550 lists 24SYMV014844210/…359/…409
because the registry's adamChain returns the whole family — they are the
other three lots of award 24AWRD014592135, not versions of this contract,
and the trail must label them as such.*

---

## 2026-08-19 · A record the registry cancelled is not a contract of the programme

The rule the double-count exposed, now in `scope_loader`: **a record ΚΗΜΔΗΣ
itself cancelled is out of scope.** It was not before, because scope asked
only what the contract IS, never whether the registry had withdrawn the
record — so 25SYMV016659302, cancelled «ΛΟΓΩ ΛΑΘΟΥΣ ΣΤΟ ΑΝΑΡΤΗΜΕΝΟ ΑΡΧΕΙΟ»
on 15.10.2025 and re-posted six days later as 25SYMV017779215, stood in the
basis beside its own replacement. One row in the whole dataset; the rule is
declared by the registry, nothing is inferred.

**Basis: €625.897.613,96 → €622.534.181,72 · 246 → 245 in-scope contracts.**
Every derived pin moved with it (17 real-DB tests), and the layers rebuilt:
work themes 245, forest authorities 244/245 linked, families 219 contracts
→ 134 calls, explore 2.312 rows, deadlines 242 document + 3 season.

**The two records now find each other.** The registry publishes no link —
no prev/next, no adamChain; the only common thread is that both texts cite
πρόσκληση 25PROC016395141 — so the connection is curated: a
`contract_corrections.json` entry (`exclude` + `duplicate_of`) records the
cancellation reason verbatim, and `contract_timeline` adds the twin as a
trail row on BOTH pages, labelled «cancelled record, re-posted as this
contract» on one side and «the re-posting of the cancelled record» on the
other. Neither page reads as a plain cancellation, which would hide that
the contract exists and was paid.

*Affects: `khmdhs/scope_loader.py` (the rule), `khmdhs/data/contract_corrections.json`
(1 entry), `atlas_api/queries_extra.py` (`contract_timeline` twin rows), the
contract page's trail chip, and every pinned figure that follows the basis.*

---

## 2026-08-19 · The document trail holds this contract's own records

ΚΗΜΔΗΣ's `adamChain` returns the whole procurement FAMILY, so a multi-lot
award put the other lots into a contract's trail — other companies'
contracts, with their own pages, listed under «Original contract» as if they
were documents of this one. Measured: **59 of 246** in-scope contracts carry
a foreign ΣΥΜΒ row (121 rows), but 56 of those rows are the contract's own
versions; only **19 pages** actually show another contract, up to **11 rows**
on the four flood-works lots of one award.

Labelling them was rejected as not making it easier to read (user). They are
**removed from the table** instead, and the relationship they belong to is
the one the DIAGRAM already draws — which knows the call for **220 of 246**
contracts against the trail's 19, and on 17 of those 19 already contains
every foreign row. Under the trail a single line now says «One of 4
contracts awarded under call 23PROC013607586 — see the diagram» and switches
the header slot to it.

**What stays**: the primary request, the commitment approval, every call,
the award, the contract's own version chain, its payment orders, its
acceptance act, and the re-posted twin of a cancelled record. Only other
contracts leave.

**Both datasets follow the same rule** (user, 2026-08-19). The ΔΑΣΕ page
drew its FamilyTree FROM the trail list, so the endpoint now returns two:
`timeline` (own records, the table) and `family_acts` (the whole family, the
diagram). An excluded sibling still states its reason — «outside the
dataset» — where it now appears, in the diagram.

*Affects: `queries_extra.contract_timeline(own_records_only=…)`,
`atlas_api/app.py` (both contract endpoints), the Anti-nero and ΔΑΣΕ contract
pages, `tests/test_atlas_real_db.py` (1 new pin, 2 moved).*

---

## 2026-08-20 · The TYPE row says one thing, and the card carries the rest

User review of 25SYMV017779215's card found three faults, all of them mine:

1. **The type printed twice.** «Protection of archaeological sites and
   monuments» (the curated category) sat above «Archaeological sites,
   monasteries and aesthetic forests» (the multi-label theme) in a smaller,
   greyer face — the same fact in two vocabularies and two letter heights.
   The row now prints the category alone; a small mapping says which theme a
   category already states (7 of the 8 map to one; «δασοτεχνικά» is the
   generic one and states none), and only the themes that ADD something go
   into the hover card: «The contract's own title also names clearing of
   forests and forest land; forest road network.»
2. **A CPV note repeated itself.** Three codes — 44611500-1, 50514200-3,
   51810000-3 — all mean water tanks, and the line printed the phrase three
   times. Deduplicated by theme, and moved off the row into the card, which
   now reads exactly once: «Its procurement's CPV codes also cover water
   tanks and water points — those codes belong to the call and are shared by
   every lot of it.»
3. **AREAS read as a list of prefixes.** It now reads as a sentence:
   «Municipalities: Διδυμοτείχου, Μαρωνείας - Σαπών, Ξάνθης, Ορεστιάδας,
   Σουφλίου, Τοπείρου in Regional Units: Evros, Xanthi, Rodopi» — the word
   «Δήμος» once, the regional units named after them, both without the
   «R.U.» prefix the row now says in full.

Also: a list whose own items contain «and» joins with semicolons, or
«clearing of forests and forest land and forest road network» reads as one
run-on.

**Map height** (asked): the map is 460 px wide — the template's column — and
its height follows the facts+caveat column, floor 420 px. Measured today:
506 px on 22SYMV010785854, 527 on 26SYMV019098206, 557 on 23SYMV012992150,
579 on 25SYMV017779215.

*Affects the Anti-nero contract page only.*

---

## 2026-08-20 · The timeline's explanation moves onto its heading

The paragraph that sat between the chart and the document trail — what the
bar measures, what ✔ and € mark, where this contract's deadline comes from —
is the same kind of note as the card rows', so it now rides on an **ⓘ before
the word TIMELINE** and the space between the chart and the trail is empty.
The methodology link keeps its place on the right of the same line, so the
chart still answers to `/methodology#contract-timeline`.

Two fixes the move exposed: inside a CAPS display heading the card inherited
the heading's caps, 900 weight and letter-spacing and printed the whole
explanation in block capitals — the card now carries its own typography —
and a long card centred on its marker straddled it and covered the rows
above, so every card grows DOWNWARDS from the marker it belongs to.

Where it settled after review: the ⓘ sits **after the word TIMELINE**, in
the heading's own face, size and weight (a circle scaled to the lettering,
not the small inline marker), and its card stands **above and to the right**
of it, clear of the chart. The card is a **legend** — one line per symbol, in
its own 336 px measure — and carries nothing contract-specific: where this
contract's deadline comes from is the DURATION row's business, and it says
so there.

*Affects `$lib/ui/Hint.svelte` (`lead`, `up`, `heading`, `width`, own
typography, top-anchored, `pre-line` text) and the Anti-nero contract page.*

---

## 2026-08-20 · Where the money travels moves to the Anti-nero page

Three frames left /connections for the dataset's own page (user):

* «Only 12% of the work-money goes to firms based where the work is» — the
  choropleth of each regional unit's out-of-region share with its flow arcs
  and the largest-flows list;
* «In the biggest destinations, local firms take a small slice»;
* «A handful of companies reach into many regions» (the bipartite).

They sit directly after the MAP, so the geography is told in one run. The
first two were lifted into `$lib/sections/FlowMap.svelte` and
`OriginSplit.svelte` rather than copied — logic and copy unchanged — and the
page fetches `/api/connections` after hydration like every other heavy
payload. /connections keeps the company hubs, the signatures and the
consortium pairs; its hub tiles used to scroll to the flow map, so they now
link to it at `/#flows`.

**RANKING OF COMPANIES** matches the sponsored-works ranking: same 30 px
bars, same 75% measure, names inside the bars — the bars stay black, this
dataset's colour. That exposed a clipping bug in `BarH`: at that bar height
a long Greek company name wrapped to three lines inside a 30 px bar and was
cut mid-letter. Inside labels are now clamped to two lines with the full
name on hover, which the sponsored page never tripped because its sponsor
names are short.

*Affects `$lib/sections/FlowMap.svelte` + `OriginSplit.svelte` (new),
`$lib/charts/BarH.svelte`, `/` and `/connections`.*

---

## 2026-08-20 · One contract, one party — and one convention for the money

The ranking and the programme basis were two different totals for the same
money: per-contractor € summed to **€655.057.006,56** against a basis of
**€622.534.181,72**. The user's rule: *«we cannot have a different amount of
money for the ranking and a different for the basis, and we can't count the
total of one contract for each company as they did not receive it — since we
do not have more information we should do an equal split.»*

Reading the contracts first changed the question. **68 of the 245 in-scope
contracts are signed by a κοινοπραξία or ένωση**, and the registry keys
**60 of them correctly**: one contractor, the joint venture's own ΑΦΜ (41
such entities, €141,8M). The ten contracts that listed several ΑΦΜ are the
same kind of contract keyed wrongly:

| | what the signed contract says |
|---|---|
| **7** | the party is a κοινοπραξία **with its own ΑΦΜ**, printed in the preamble; the registry stored its members |
| **1** | 24SYMV016018183 — «Ένωση Οικονομικών Φορέων NOVALIS Ε.Π.Ε. – ΦΩΤΟΠΟΥΛΟΣ ΓΕΩΡΓΙΟΣ», **genuinely two parties**, no joint ΑΦΜ |
| **2** | 26SYMV018739467 · 26SYMV018725481 — signed by **ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ & ΣΙΑ Ε.Ε. alone**; the other two companies appear nowhere in the text |

Verbatim, from 26SYMV018718889: «η κοινοπραξία με την επωνυμία «ΤΙΓΚΑΣ
ΚΩΝΣΤΑΝΤΙΝΟΣ - ΧΑΤΖΗΝΙΚΟΛΑΟΥ ΝΙΚΟΛΑΟΣ», με έδρα την Καβάλα … **Α.Φ.Μ.
996551622** της ΔΟΥ Καβάλας». The registry stored 043170596 and 113864390 —
the two men. Article 9 binds the members «ενιαία, αδιαίρετα, αλληλέγγυα» and
states **no shares**.

Two screens agree on the extent: `scripts/audit_contract_awardees.py` over
all 344 contracts (2 `over_attributed`, 6 `vat_mismatch_name_ok`), and a
κοινοπραξία-preamble sweep of every in-scope contract. Its one other hit is
a false positive — 22SYMV010856516, where pdftotext split «ΑΦΜ 99964389 6»
and the labelled run belongs to the company's representative; the registry
is right there.

**Decisions.**

1. **The party is what the signed contract names.** Nine contracts corrected
   via `contract_corrections.json` — a new `contractor_party` key (ΑΦΜ, name,
   verbatim preamble) for the seven, `contractors_keep` for the two. The
   registry's own list stays verbatim in `contracts.raw_json`. Registered
   names confirmed independently: six in ΓΕΜΗ, the seventh in VIES.
2. **A contract signed by more than one party is split evenly**, whole cents
   (`antinero_contractor_shares` → `_split_coop_totals`), on the ranking, the
   contractors list and the contractor page — the rule the ΔΑΣΕ side already
   uses. No document supports anything finer: **no contract states a
   «ποσοστό συμμετοχής»**, and ΓΕΜΗ's publicity API returns a κοινοπραξία's
   name, seat and legal type but **no members and no shares** (probed live).
   The maximum-exposure convention is retired from the site.
3. **The seven consortium seats are curated** into
   `contractor_locations.json` from ΓΕΜΗ/VIES with the contract as
   corroboration, all seven geocoded (5 address-level, 2 municipality) —
   without them those contracts would vanish from the HQ maps.

**Result: 151 contractors (from 155), exactly one in-scope contract with two
parties, and Σ per-contractor € == €622.534.181,72 == the basis, to the
cent** (pinned). The top of the ranking does not move — no joint venture sat
in it. Ten individuals who appeared only as members leave the contractor
population, and their edges with them: 500 → 475 contractor×authority pairs,
401 → 377 region pairs, 277 → 258 flows, 181 → 174 signer pairs.

**A finding this exposed:** /connections said «Consortiums are the
exception» on 12 partner pairs — which was only ever true of the registry's
party lists. Joint ventures are not the exception: 41 of them hold 22,8% of
the programme, invisible to that layer because each signs as one entity.
With the correction the layer sees 1 pair, so the frame is drawn only when
there is a network to draw, and the honest picture waits on the consortium
membership layer.

**Next (user decision, same day): members side by side, not instead.** The
ranking stays on the legal contracting party; a second view will attribute
the same money to member firms. Measured sources for membership: the
consortium's own name (41/41, names only), member ΑΦΜ inside the contract
(10/41), **the award act (25 of the 26 that have one name 2+ ΑΦΜ**, but a
multi-lot award lists other bidders too), ΓΕΜΗ ΑΦΜ→name (deterministic) and
ΓΕΜΗ name→ΑΦΜ (ambiguous — four «ΚΤΕΝΑΣ ΓΕΩΡΓΙΟΣ»). Triangulating title ×
award pool × registry resolves **34 of 79 member slots (43%)** — under the
80% rule, so it is curated with machine proposals.

*Affects `khmdhs/contract_corrections.py` (`contractor_party`),
`khmdhs/data/contract_corrections.json` (+9), `contractor_locations.json`
(+7), `atlas_api/queries_extra.py` (`antinero_contractor_shares`,
`antinero_top_contractors`, `antinero_contractors_list`,
`antinero_contractor_summary`, `_split_coop_totals` vat_key, authority
ranking), `atlas_api/app.py`, `/`, `/antinero/contractors`,
`/antinero/contractor/[vat]`, `/antinero/contract/[adam]`, `/connections`,
`/methodology#joint-contracts`, the footer, and `tests/test_atlas_real_db.py`
(4 new pins, 6 moved).*

---

## 2026-08-20 · What the register says about the contractor now

A κοινοπραξία is formed for one job and wound up when it ends. The joint
venture that signed 23SYMV013201917 shows in ΓΕΜΗ as **Ενεργή 18.07.2023 →
Λύση-Εκκαθάριση 20.01.2025 → Διαγραφή 19.03.2025** — struck off, twenty
months after signing. User decision: **the contractor is never rewritten —
it signed the contract — but the page must say what became of it and link
the register.**

`scripts/harvest_gemi_status.py` swept the publicity API for every
contractor carrying a ΓΕΜΗ number (147 companies, throttled, resumable):
**122 active, 21 struck off, 4 in liquidation**; of the in-scope
contractors, **20 are no longer active** and every one of them is a joint
venture. Stored as `contractor_locations.gemi_status`, verbatim Greek.

**No date is shown.** The API's `dateGemiRegistered` looked like the status
date on the first record checked, but on active companies it is plainly the
registration date — 26 of them differ from the company's own start date and
one reads 1992, nine years *before* it. Rather than print a date whose
meaning we cannot state, the note carries the status alone and the ΓΕΜΗ link
goes to the register's own «Ιστορικό Κατάστασης» table.

Rendering: an ⓘ next to the contractor on the contract page and beside the
ΓΕΜΗ link on the contractor page — «ΓΕΜΗ records this company as struck off
the register (Διαγραφή). It stays the contractor of this contract — it is
the company that signed.» The Greek term is always kept; the English gloss
is a reviewed map of the five statuses seen, and an unknown status prints in
Greek alone (`$lib/transforms/registry.ts`, unit-pinned).

*Affects `scripts/harvest_gemi_status.py` (new), `khmdhs/db.py`,
`khmdhs/contractor_loader.py`, `khmdhs/data/contractor_locations.json`,
`queries_extra.contractor_registry_status`, `atlas_api/app.py`,
`$lib/transforms/registry.ts` (new, 3 units), the Anti-nero contract and
contractor pages, and one real-DB pin.*

---

## 2026-08-20 · One split, in the shared layer — the old site reconciles too

The even split shipped that morning lived in the Atlas layer, so :5000 still
counted a jointly signed contract whole for each partner: its contractor
column stood **€195.692,64** above its own headline, and the ΔΑΣΕ page of the
same site stood **€6.676,10** above its own. User: *«I do not want to have
mismatches in the data. the webui has to have the correct data as well.»*

So the rule moved to where both sites read from — `webui/queries.py`
(`joint_contract_shares`, `_even_cents`, `apply_joint_split`) and
`webui/dase_queries.py` (`joint_coop_shares`) — and the Atlas copies became
thin aliases. This is a deliberate exception to the freeze on those modules,
and the reason is the freeze's own logic: a correctness rule implemented
twice drifts, and applied twice double-counts (which is exactly what would
have happened here — the Atlas subtracted the over-credit from totals that
were now already split).

It is basis-agnostic by construction: the € come from `effective_cost` on the
caller's connection, so one implementation returns gross-effective figures
for webui and net-stated ones through the Atlas's shadow views.

Split on both sites now: the ranking, the contractors/co-ops list, the
entity's own total, its **signer/awarder table**, its **per-year bars**
(paid and stated alike) and the **map dots**. Contract counts and each
contract's own value are untouched — the entity's share rides beside it.

Reconciliation, all four pinned:

| | headline | Σ of the entity column |
|---|---:|---:|
| webui · Anti-nero | €601.043.031,36 | €601.043.031,36 |
| webui · ΔΑΣΕ | €36.954.829,83 | €36.954.829,83 |
| Atlas · Anti-nero | €622.534.181,72 | €622.534.181,72 |
| Atlas · ΔΑΣΕ | €29.920.558,46 | €29.920.558,46 |

Also fixed the same day: `contractors_vat` warned «no row carries X» on every
re-run once applied — 7 contracts (1 khmdhs, 6 ΔΑΣΕ) printing a false alarm
on every refresh, which is how the real signal (a curated fix that matches
nothing any more) would have been missed. It is now silent when the row
already carries the corrected ΑΦΜ, and still warns when neither value is
there; both sides unit-pinned.

*Affects `webui/queries.py`, `webui/dase_queries.py` (the freeze exception),
`atlas_api/queries_extra.py` (overlays retired to aliases),
`khmdhs/contract_corrections.py`, and pins in `tests/test_webui_queries.py`,
`tests/test_dase_real_db.py`, `tests/test_contract_corrections.py`.*

---

## 2026-08-20 · Who is behind each joint venture, and a second ranking

54 in-scope contractors are joint ventures holding 67 contracts — **€189,4M,
30,4% of the programme** — and each signs as ONE entity, so the firms inside
them are invisible in every per-contractor view. User decision: show BOTH —
the ranking stays on the contracting party, and a second view attributes the
same money to the member firms.

**Identifying the ventures** is settled by ΓΕΜΗ's legal form «Κοινοπραξία»
(harvested into `contractor_locations.gemi_legal_type`), which marks 49, plus
the registry name, which marks 48; the union is 54, so six ventures named
after their job rather than their members — «ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΠΙΕΡΙΑΣ 2025
Κ Ξ» — stop being missed.

**Membership is curated, one venture at a time.** Proposals come from
`scripts/extract_consortium_members.py`: every labelled ΑΦΜ in the venture's
own contracts and in the acts of the same procurement, plus a ΓΕΜΗ name
lookup for the 101 firms the programme did not know. Two evidence rules
pre-tick a candidate — a document *lists* it as a member, or the venture is
named after it — and four matching traps were measured and fixed rather than
guessed:

* «Τ & Τ ΚΑΤΑΣΚΕΥΕΣ» is one letter and a stop word → a compacted-name test,
  for document candidates only;
* every κοινοπραξία name starts with «ΚΟΙΝΟΠΡΑΞΙΑ», which matched all 54 to
  each other until stop words came out of that test first;
* a joint venture is never a member of another, so they leave the universe;
* Greek naming: one shared word matched 1.795 pairs and two still matched
  1.105 (a first name and a patronymic are two words), so a registry-wide
  match now needs a word that identifies exactly ONE company.

**Result: 54 of 54 curated — 32 with members (€116,6M), 22 recorded as
members-undocumented (€72,8M).** 65 member links over 48 firms, of which **21
are firms the programme had never seen**, because they only ever worked
through a venture. Nineteen ventures were decided by the user one at a time
against the full documents; 13 were applied as a batch after two worked
examples.

**The standard, set by the user:** a document must state membership. A
venture's name is not evidence — «ΚΟΙΝΟΠΡΑΞΙΑ ΤΣΑΝΤΑΛΗ – ΒΕΛΩΝΗΣ» names both
firms and its contract names neither as a member, so it is recorded
undocumented. Two traps were caught in review and are now encoded: **the
person signing for a member company is not a third member** (the enumeration
window used to swallow «τον κοινό εκπρόσωπο … με ΑΦΜ …»), and **another joint
venture of the same firms is not a member** (proposed for both ΛΙΑΧΤΙΔΑ and
ΜΠΟΜΠΟΤΗ, rejected).

**The second view** (`queries_extra.antinero_member_firms`) is the same
population and the same total with one substitution: a venture with curated
members is replaced by them and its € split evenly, whole cents. It sums to
**€622.534.181,72**, the same as the contracting-party view, and the
undocumented ventures' **€72,8M sits identically in both** — stated in the
frame's caveat rather than hidden. 151 names become 144. The finding it
exposes: **Τ&Τ ΚΑΤΑΣΚΕΥΕΣ moves from 8th to 3rd** (€20,4M, of which €11,4M
through the κοινοπραξία with ΜΕΣΟΓΕΙΟΣ, which itself appears at 9th having
been invisible), and ΤΣΙΜΠΩΝΗ/BIODASOS reaches €10,1M through three ventures.

Found and fixed on the way: **`details_loader` and `municipalities_loader`
were called in `khmdhs/refresh.py` but never imported** — a NameError that
would have stopped the whole refresh chain at that step since 2026-08-19.

*Affects `scripts/extract_consortium_members.py` + `consortium_curator.html`
(new), `khmdhs/data/consortium_members.json` (new, 54 entries),
`khmdhs/consortium_loader.py` (new) + `consortiums` / `consortium_members`
tables, `khmdhs/refresh.py` (chain + the missing imports),
`queries_extra.antinero_member_firms` / `antinero_consortium_facts`, the `/`
ranking's «As contracted / By member firm» toggle (`?rank=firm`),
`/methodology#member-firms`, and `tests/test_consortiums.py` (8 units) +
2 real-DB pins.*

## 2026-08-20 · Ask the contracts, not the registers, what a joint venture is

The membership layer of this morning swept the ventures by asking ΓΕΜΗ what
each contractor IS (`gemi_legal_type = 'Κοινοπραξία'`) and by reading the
registry name. A register can be silent. **ΑΦΜ 996514860 «ΤΣΙΑΝΑΒΑΣ ΓΕΩΡΓΙΟΣ
– Μ.&Κ. ΤΕΧΝΙΚΑ ΕΡΓΑ Α.Ε.» is in no ΓΕΜΗ at all** and its registry name
carries no marker, so a €4.447.572,92 venture was invisible to the sweep — its
own contract 25SYMV016670155 says «2. **η κοινοπραξία** με την επωνυμία … με
ΑΦΜ 996514860», and VIES registers it as «ΚΟΙΝΟΠΡΑΞΙΑ ΤΣΙΑΝΑΒΑΣ ΓΕΩΡΓΙΟΣ Μ
ΚΑΙ Κ ΤΕΧΝΙΚΑ».

So the population is now decided by the documents. **`scripts/screen_joint_ventures.py`**
reads every in-scope contract CHAIN, finds each contractor's own ΑΦΜ in the
signed text and looks back one 500-char party-clause window for a venture word;
the anchor is the ΑΦΜ because «σε περίπτωση κοινοπραξίας…» is ΕΣΥ boilerplate in
every contract. A second pass (`--members`) re-reads the clause for
«αποτελούμενη από …». It reports three signals — document / ΓΕΜΗ / name — and a
**guard test fails on any venture the documents name that the curation lacks**.
151 contractors, 58 answer as ventures, 1,4 s, no blind spots (every in-scope
chain has cached text). Two mechanics had to be right: the fold is
length-preserving (a 1:1 char table applied BEFORE `.upper()`, since «ΐ».upper()
is three characters) so offsets found in folded text cut excerpts from the
ORIGINAL, and the needles match loosely — phase-II PDFs write «αποτελουύμενης»
and «Κοινοπραξιίας».

**The screen found four ventures the curation did not carry, and re-reading the
54 curated ones found no missed member on any of them.** Every extra ΑΦΜ in
those clauses is a signatory or an ΑΔΑΜ, both already excluded by rule. The
verdicts, all the user's:

* **996514860** ΤΣΙΑΝΑΒΑΣ – Μ.&Κ. (€4.447.572,92) — recorded, **members
  undocumented**: 996514860 is the only ΑΦΜ in its contract, no award act was
  declared and the 76 Diavgeia acts citing it are schedule/supervision
  approvals. Both firms are identifiable (ΤΣΙΑΝΑΒΑΣ ΓΕΩΡΓΙΟΣ 044705095 is the
  first invitee of its own πρόσκληση 25PROC016306915; Μ. & Κ. ΤΕΧΝΙΚΑ ΕΡΓΑ Α.Ε.
  099334013 is named with its ΑΦΜ in two OTHER προσκλήσεις) — but no document
  states them to be the members, and the signatory Γιαννούλας Βάιος is neither.
* **996550190** ΚΑΡΝΟΜΟΥΡΑΚΗΣ Α.Ε. – ΑΛΚΗ Ι.Κ.Ε./ΥΠΟΕΡΓΟ Β (€1.020.119,23) and
  **996870356** ΜΠΟΜΠΟΤΗ – ΞΑΝΘΟΠΟΥΛΟΣ (€2.736.228,76) — recorded **with
  members**, both enumerated in their own contracts. The second is stated twice
  over, in the original σύμβαση 22SYMV010488925 and in the amendment that
  superseded it, and both its ΑΦΜ (044739770, 102529416) already sat in the
  curated file as members of other ventures, read from award acts.
* **996553688** ΚΞ ΚΑΡΝΟΜΟΥΡΑΚΗΣ – ΑΛΚΗ/ΥΠΟΕΡΓΟ Δ and **996831933** ΠΑΠΠΑΣ –
  ΠΑΝΤΟΥΛΗΣ were recorded this morning as members-undocumented; their own
  contracts enumerate the members, so both are now documented. The morning's
  curation read award acts and προσκλήσεις; the party clause is a source it did
  not read.
* **996604620** ΛΑΜΠΙΡΗΣ – ΔΗΜΟΠΟΥΛΟΣ and **997227555** ΛΕΦΤΣΗΣ – ΑΦΟΙ
  ΔΙΑΜΑΝΤΟΓΛΟΥ stay undocumented: their clauses name only «τον διαχειριστή και
  εκπρόσωπο της κοινοπραξίας» with his ΑΦΜ, and a representative is not a
  member — the same rule that was already encoded this morning.

**The fifth case is a venture that never got an ΑΦΜ.** 22SYMV010795606 is signed
by «**κοινοπραξίας** «ΚΞΙΑ ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ ΓΕΩΓΝΩΜΩΝ ΟΕ», **αποτελούμενη
από:** α) την ετερόρρυθμη εταιρεία «ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ ΚΑΙ ΣΙΑ ΕΕ» (ΑΦΜ
998255970) **και** β) την ομόρρυθμη εταιρεία «ΓΕΩΓΝΩΜΩΝ ΟΕ» (ΑΦΜ 998434068) …
δυνάμει του από 28.12.2021 ιδιωτικού συμφωνητικού σύστασης κοινοπραξίας», and
the venture states no ΑΦΜ and holds no ΓΕΜΗ number. The registry therefore keyed
the contract under member α — whose ΑΦΜ is its own (ΓΕΜΗ 124272601000 registers
998255970 as «ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ ΚΑΙ ΣΙΑ ΕΕ», legal form ΕΕ) — and credited
that firm the whole €836.613,02. Both payment orders on the contract pay «ΚΞΙΑ
ΑΝΑΠΤΥΞΙΑΚΗ ΠΡΑΣΙΝΟΥ - ΓΕΩΓΝΩΜΩΝ Ο.Ε.», i.e. the pair.

It cannot be curated as a venture — the layer keys on the venture's ΑΦΜ, and
here the only ΑΦΜ belongs to a member, so recording it would make the loader
refuse (a venture listing itself) and would mark the firm's three solo contracts
as a venture's. **User decision: record both signatories on that one contract**,
exactly as the ένωση 24SYMV016018183 is handled, and let the shared even split
give each **€418.306,51**. `contractor_party` now accepts a LIST for this.
The firm's other three in-scope contracts (23SYMV013039380, 26SYMV018725481,
26SYMV018739467, €3,02M) name «η ετερόρρυθμη εταιρεία … (στο εξής ο
«Ανάδοχος»)» and no venture at all — they are correctly its own and untouched.
The screen knows about jointly signed contracts, so it asks for no venture entity
there; the entry for 22SYMV010795606 also keeps its earlier PROJECT-BUDGET value
correction. One entry, two corrections: `reason` is stamped into
`correction_note` and printed on the page as the stated-value correction, so it
stays the value text alone and the party trail goes into an audit-only
`party_reason` key — the same split as `reason` vs `note`.

The basis does not move — **€622.534.181,72** — and neither does the contract
count. The layer is now **57 ventures, 36 with curated members (73 links, 52
firms), 21 undocumented**; the member view's names go 144 → 141, the undocumented
ventures' € is €75.263.310,33 and the ventures hold 31,7% of the programme. Every
number ships from `/api/antinero/overview`, so the site's copy follows.

*Affects `scripts/screen_joint_ventures.py` (new),
`khmdhs/data/consortium_members.json` (54 → 57 entries; 4 verdicts),
`khmdhs/data/contract_corrections.json` (22SYMV010795606 gains a two-party
`contractor_party`), `khmdhs/contract_corrections.py` (`_apply_contractor_party`
takes a list), `atlas_api/queries_extra.contract_party_correction` (quotes one
sentence for several parties), `tests/test_consortiums.py` (+1 real-DB guard) and
6 real-DB pins in `tests/test_atlas_real_db.py`.*

## 2026-08-20 · One name per contractor, and the documents decide it

The same company reached the site under two names: the ΚΗΜΔΗΣ spelling in the
ranking and the ΓΕΜΗ/VIES one on the map. For 43 ΑΦΜ those differ, and for some
they are not variants at all — **998342580 is «Δ. ΚΑΦΕΤΖΗΣ ΚΑΙ ΣΙΑ Ο.Ε.» in the
registry and «ΒΙΟΣ Α.Ε.» in its own contracts**, €13,0M under a name the site
never showed, and searching «BIODASOS» found the joint venture but not the firm
that holds €3,92M of its own. So: **one canonical display name per ΑΦΜ**,
curated in `khmdhs/data/contractor_display_names.json`, 195 entities.

**The rule the user set, and the one correction to it that mattered:** a person
is written ΕΠΩΝΥΜΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΩΝΥΜΟΥ — *«when the contract already holds
that information or the combination with ΓΕΜΗ makes it provable. we should not
invent»*. The first pass had declined the register's patronymic by rule; after
the correction the patronymic is read from the signed documents
(`scripts/extract_name_evidence.py` sweeps every cached contract, award, call
and payment order for how each ΑΦΜ is written there — 195/195 appear, 4.523
mentions) and **the register supplies only the SPELLING while the document
supplies the proof**. That is what keeps «του ΚΩΝ/ΝΟΥ» from becoming a name and
a mis-rendered 2018 PDF from writing «ΤΟΥ ΑΘΑΝΑΣΥΟΥ». 65 of 66 persons are
documented; **ΓΚΑΡΓΚΑΝΙΤΗΣ ΛΑΜΠΡΟΣ prints without a patronymic** because no
document holds his — and he is the reason the rule earns its keep, since
113411710 is ΓΚΑΡΓΚΑΝΙΤΗΣ ΠΑΝΑΓΙΩΤΗΣ ΤΟΥ ΛΑΜΠΡΟΥ, his son.

Traps found and encoded, each by a name that came out wrong:

* the genitive is read only AFTER the surname — «β) **του** Ευάγγελο Μαναρίτσα
  **του** Κωνσταντίνου» has a «του» on either side and the first is the article
  of the given name (4 names were wrong: ΜΑΝΑΡΙΤΣΑΣ, ΑΓΓΕΛΑΤΟΣ, ΛΙΟΛΙΟΣ,
  ΧΑΤΖΗΝΙΚΟΛΑΟΥ);
* ΓΕΜΗ writes «ΦΙΛΙΠΠΑΚΗΣ Μ. ΠΑΝΤΕΛΗΣ», where Μ. is the patronymic's INITIAL and
  ΠΑΝΤΕΛΗΣ the given name — the contract spells it out, «τον Παντελή Φιλιππάκη
  **του Ματθαίου**»;
* a register field that already sits behind «ΤΟΥ» is a genitive; declining it
  again turned «ΤΟΥ ΣΠΥΡΙΔΩΝΟΣ» into «ΤΟΥ ΣΠΥΡΙΔΩΝΟΥ», and where the papers
  spell it differently the papers win (they write ΤΟΥ ΣΠΥΡΙΔΩΝΑ);
* a double given name is not a patronymic: «ΜΠΟΜΠΟΤΗ ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚ
  ΚΩΝΣΤΑΝΤΙΝΟΣ» is ΚΩΝΣΤΑΝΤΙΝΙΑ ΒΑΣΙΛΙΚΗ, του ΚΩΝΣΤΑΝΤΙΝΟΥ;
* where register and documents disagree the row says CONFLICT and carries no
  patronymic (0 in the live data).

**Companies are written under the δ.τ. their own contracts declare** («…με
διακριτικό τίτλο «ΕΛ.ΤΕ. Ε.Π.Ε.»», «με δ.τ. «P. & C. DEVELOPMENT S.A.»»), which
reaches names no head-matching rule could — 20 of 63. A δ.τ. counts only if the
company's own name is in it or the papers declare it more than once beside that
ΑΦΜ: without that test ΓΑΙΟΣΤΑΤ borrowed «ΟΙΚΟΔΑΣΟΣ Ε.Π.Ε.» from the firm named
two lines above it in the same contract. Where the δ.τ. differs from the name
the programme uses, the user decided case by case: **ΕΛ.ΤΕ. Ε.Π.Ε.** and
**P. & C. DEVELOPMENT S.A.** yes; **ΕΡΓΑ ΠΡΑΣΙΝΟΥ Α.Τ.Ε.** over the δ.τ.
ΕΡΓΟΠΡΑΣΙΝΟ (35 mentions against 10); **ΤΕΧΝΟΟΜΟΙΟΣΤΑΣΗ Ε.Ε.** over ΓΟΥΝΑΡΗΣ Ν.
- ΚΟΝΤΟΣ Κ.; **ΟΡΚΑ Α.Τ.Ε.Ε.**, because the papers spell the head both ways (25
«ΟΡΚΑ» against 6 «ΟΡ.ΚΑ.»), ΓΕΜΗ registers ΟΡΚΑ, and reading the dots as
ΟΡγάνωσης-ΚΑτασκευής is an inference no document states.

**Joint ventures carry «Κ/Ξ » once, at the front** (the papers write the marker
four ways and leave it out of 20 names), and a venture whose contract never
quotes a name is **composed from its members' own display names** — «Κ/Ξ
Γ.Ι.ΚΑΡΝΟΜΟΥΡΑΚΗΣ Α.Ε. – ΑΛΚΗ Ι.Κ.Ε.» — with the members' patronymics dropped
inside the composition, since they sit one click away on their own pages. Every
display name is unique: two ventures of the same two firms are told apart by
the lot they were formed for («ΥΠΟΕΡΓΟ Β» against «ΥΠΟΕΡΓΟ Δ») or by the year.

**One typography** (user): capitals, the legal form always dotted (Α.Ε., Ο.Ε.,
Ε.Ε., Ι.Κ.Ε., Ε.Π.Ε., Α.Τ.Ε., Α.Τ.Ε.Ε., Α.Τ.Ε.Β.Ε.), «&» for «ΚΑΙ» between
partners but never inside a company's object («ΞΕΝΟΔΟΧΕΙΑΚΗ ΚΑΙ ΕΚΜΕΤΑΛΛΕΥΣΕΩΣ»
stays), a Greek form typed in Latin folded back («E.E.» → «Ε.Ε.») while a Latin
name keeps its alphabet, and PDF homoglyphs repaired per letter-run
(«ΠΑΠΑ∆ΟΠΟΥΛΟΣ» carried U+2206; «BIODASOS-ΤΕΧΝΗ» is legitimately two alphabets
in one word). **ΤΑΙΠΕΔ** prints as its acronym, in English **HRADF**.

**Presentation only.** `contractors.name` is never rewritten: every registry
spelling stays in the database, stays searchable — `/api/antinero/contractors?q=`
now matches the display name, the English name, the ΑΦΜ **and every spelling the
registry holds**, so «ΚΑΦΕΤΖΗΣ» still finds ΒΙΟΣ Α.Ε. — and is printed on the
contractor page under «In the registry as …». The money is untouched: the
ranking still sums to **€622.534.181,72** over 151 contractors.

The overlay reaches every surface that prints a contractor: the ranking, the
contractors list and its search, the contractor page, the member-firm view, the
contract page (each party with `registry_name` beside it) and the /explore `co`
column, where the spellings the display name replaced ride in a new `ac` field
that the client searches — `alt` stays ΑΔΑΜ-only, which a pin enforces.

*Affects `scripts/extract_name_evidence.py` (new) and
`scripts/extract_contractor_names.py`, curated
`khmdhs/data/contractor_display_names.json` (new, 195 entries),
`khmdhs/contractor_names_loader.py` (new) + the `contractor_display_names`
table, `khmdhs/refresh.py` (chain), `queries_extra.antinero_display_names` /
`overlay_contractor_names` and the four surfaces it feeds (ranking, contractors
list + search, contractor page, member-firm view),
`atlas/src/routes/antinero/contractor/[vat]/`, and
`tests/test_contractor_names.py` (15 units + 2 real-DB guards) + 1 Atlas pin.*

*Housekeeping found on the way: two committed scripts carried a stray 0x08 in a
regex (`extract_contractor_names.py`, `harvest_ypen_offices.py`) — a shell
heredoc eating the backslash of «». Both cleaned; the lesson is to edit
Python regexes with a file, never through a heredoc.*

## 2026-08-20 · Two seats from the contracts, a grayscale Anti-nero page, and what ΓΕΜΗ knows about the ventures

**The two missing HQ dots.** Every in-scope contract has a curated work region
and every Π.Ε. value is canonical, but 2 of the 151 contractors — the ventures
996674333 (ΣΙΔΕΡΗ–ΕΛ.ΤΕ.) and 996830790 (ΦΙΛΑΝΤΑΡΑΚΗ–ΛΙΤΣΟΣ) — carried a
region and no point, so their dots were missing from the HQ maps. Their own
contracts state their seats («με έδρα στη Λυκόβρυση Αττικής επί της οδού
Μπουμπουλίνας, αρ. 10Α, Τ.Κ. 14123» — 22SYMV010635347; «με έδρα στο Ίλιον
Αττικής επί της οδού Λεοντίου, αρ. 35, Τ.Κ. 13121» — 22SYMV010795585); both
geocoded street-level through the normal Nominatim gate (postcode prefix +
curated Π.Ε. agree), source `contract_preamble`. **151/151 in-scope contractors
now carry a dot.**

**The Anti-nero page goes black-white-grayscale** (user): no greens, reds or
blues anywhere on `/` or its maps. The works ramp, the phase colours (ordinal
greys — the phases are ordered in time, so lightness carries the order), the
flow arcs (solid black IN / dashed grey OUT / white-ringed local dot), the HQ
dots, the Sankey/Bipartite/disbursement accents and the threshold ink all
moved; the drilled map's per-contract OKLCH hues became two alternating greys,
accepting that a multi-authority contract's dots now group visibly only on
hover (the dashed seat-links). CONTRACT VALUES became the ΔΑΣΕ merged frame:
dots/brackets toggle on one pure-doubling axis anchored on €1.000
(`antinero_value_histogram`, pinned Σ counts == 245 == every in-scope
contract), coloured by SIGNATURE YEAR in greys — the user explicitly dropped
the phase categories there — with the single-bid rings and the ν.4782 ceiling
lines kept. The flow map and the local-share bars merged into one linked
frame, and the computed finding sentences moved from the frame titles into
the subtitles (the titles are short caps, as on the ΔΑΣΕ page).

**ΓΕΜΗ knows the ventures' members, and it was under our nose.** The
publicity `/api/company/details` payload — which `gemi.py` already calls,
reading only `.company` out of it — carries `managementPersons`: each member
with ΑΦΜ, the role «Εταίρος - Μέλος» and a PERCENTAGE, plus the register's
act history with the «Ανακοίνωση σύστασης» reference. Sweep over the 19
undocumented ventures holding a ΓΕΜΗ number: 10 return member rows (some
partial — one of two members). The σύσταση PDFs themselves are NOT publicly
downloadable (every route the SPA exposes — `/api/download/{statutes,
authority,rest}/<id>` — serves other document classes; the announcement
files' `~/uploads/…` paths resolve on no public host). **Convention set by
the user the same day: the ΓΕΜΗ percentages are the venture's internal
participation shares, NOT a record of how any contract's money was
distributed — the State paid the venture as one entity. The even split
stays; percentages ride as recorded metadata only.** Membership entries from
this source await the user's per-venture confirmation before anything enters
`consortium_members.json`.

*Affects `khmdhs/data/contractor_locations.json` (2 seats),
`atlas_api/queries_extra.py` (`antinero_value_histogram`, swarm `d`),
`atlas/src/lib/maps/useGeo.ts`, `transforms/scopes.ts`,
`charts/yearColors.ts` (+`YEAR_GREYS`), `charts/BeeswarmCanvas.svelte`
(parametrized), `charts/Beeswarm.svelte` (deleted), `maps/FlowArcs.svelte`,
`sections/{FlowMap,OriginSplit,AntineroMap,Bipartite}.svelte`,
`charts/{Sankey,DisbursementCurves}.svelte`, `src/routes/+page.svelte`, and
`tests/test_atlas_real_db.py` (+1 pin). 530 Python tests, 108 frontend.*

## 2026-08-20 · Five ventures documented from the register (batch A confirmed)

The user confirmed the five ventures whose ΓΕΜΗ `managementPersons` rows list
every member: Κ/Ξ Κ. ΣΠΑΝΟΣ & ΣΙΑ Ε.Ε. – ΠΑΠΑΔΟΠΟΥΛΟΣ (70/30), Κ/Ξ ΛΑΜΠΙΡΗΣ
– ΔΗΜΟΠΟΥΛΟΣ (99/1), Κ/Ξ ΛΙΤΣΑ – ΚΥΡΙΑΖΑΤΗΣ (50/50), Κ/Ξ ΓΕΜΑ – ΤΑΣΚΟΥΔΗΣ/
ΓΚΑΤΖΙΟΣ (50/50), Κ/Ξ ΦΙΛΑΝΤΑΡΑΚΗ – ΛΙΤΣΟΣ (no % recorded). Source
`gemi:<number>`, the register row verbatim as the excerpt, percentage kept as
`gemi_percentage` metadata under the even-split convention. The layer is now
**57 ventures / 41 documented (83 links, 58 firms) / 16 undocumented**; the
member-firm view still sums to €622.534.181,72 (138 names), and the
undocumented ventures' € fell €75,3M → €60,6M. Three member ΑΦΜ are new to
the dataset (999501790, 034704122, 801264804). Pins updated in
`tests/test_atlas_real_db.py`.

## 2026-08-20 · Five more from the register (batch B) — the «missing member» was a role spelling

Batch B confirmed. The earlier «ΓΕΜΗ lists only one member» pattern was an
artifact of the sweep's own filter: the register writes a member who also
runs the venture under the combined role **«Μέλος & Διαχειριστής»**, which
the first pass had misfiled as a non-member row. Read in full, all five B
ventures carry BOTH members with ΑΦΜ and percentages that sum to exactly
100%: ΣΙΔΕΡΗ–ΜΠΟΥΡΑΣ 50/50, ΚΑΖΑΝΤΣΟΓΛΟΥ–ΒΕΛΩΝΗΣ 75/25, ΝΤΙΝΟΠΟΥΛΟΣ–
ΛΑΓΚΑΔΙΝΟΣ 50/50, ΤΣΑΝΤΑΛΗ–ΒΕΛΩΝΗΣ 80/20, ΛΕΦΤΣΗΣ–ΑΦΟΙ ΔΙΑΜΑΝΤΟΓΛΟΥ 50/50.
The encoded trap («a person signing FOR a member company is not a member»)
is about contract signatures and does not apply to a register row that says
«Μέλος». Three second-members are independently corroborated with the same
ΑΦΜ in procurement documents (ΝΤΙΝΟΠΟΥΛΟΣ 100287570 in πρόσκληση
25PROC016893018, ΤΣΑΝΤΑΛΗ 148024200 in 24PROC014217714, ΛΕΦΤΣΗΣ 061303461
in the venture's own contract 23SYMV012992146).

The layer is now **57 ventures / 46 documented (93 links, 63 firms) / 11
undocumented**; unattributed venture money fell to **€40.816.532,04**. The
member-firm view still sums to €622.534.181,72 over 136 names; ΣΙΔΕΡΗ ΜΑΡΙΑ
enters the top-5 (€15,25M through three ventures and her own work). One new
ΑΦΜ enters the dataset (100287570 ΝΤΙΝΟΠΟΥΛΟΣ). The 11 that remain: 9 with
a ΓΕΜΗ record that lists no member rows and 2 with no ΓΕΜΗ number at all —
no reachable source names them.

## 2026-08-20 · No «full exposure» on the Atlas — the maps split a contract equally between its regions, and say why

The map cards printed an «even-split share» beside a «full exposure» figure
(the contract's whole value counted toward every region it covers), and the
flow arrows were drawn on that full-exposure attribution (Σ ≈ €1,1 bn for a
€622,5 M programme). **User decision: drop full exposure everywhere on the
Atlas — choropleths, cards and the arrow map — because it is not what
happened; a contract's whole value was not spent in each region it covers.**
What the reader needs instead is the explanation: **100 of the 245 in-scope
contracts cover more than one regional unit**, and the documents we hold
state NO allocation of the money between the units a contract covers (one
price for works in three regional units, not three), so each contract is
split equally between its regions — and, for a jointly signed contract,
between its partners.

Implemented as one convention behind every flow surface:
`queries_extra._flow_units` divides each contract into k regions × m parties
equal shares; `antinero_region_flows`, `region_flows_yearly` and
`antinero_region_origins` are sums of those shares and reconcile to the
programme total (€622.534.181,72, pinned within per-row rounding) — the
stays-local share reads **16,7%** on the split (it read ~12% on full
exposure, where multi-region contracts inflated the imported side). An
unlocated party keeps its share as unresolved (none today: 151/151 located).
The map cards lost the exposure line, the MAP caveat states the reading with
the computed multi-region count, the flow frame's caveat says the same, the
methodology's even-split paragraph was rewritten around the reason, and the
authority page's «full exposure» compare figure became a plain contract
count. The frozen webui keeps its full-exposure `/map` and `/origins` under
the «maximum-exposure view» copy it has always carried.

## 2026-08-21 · The municipality-centre dots: 52 of 61 DO hold a street — 16 re-placed, 45 stay honest

The registered-office map drew 61 of the 151 in-scope contractors at the
centre of their municipality (dashed). The user asked whether we actually
lack those addresses. **We do not, mostly**: 52 of the 61 curated entries
hold a registered street — 38 with a house number, 10 a street or locality
without one, 4 a kilometre marker on a road — and only 9 hold no street at
all. The first Nominatim pass (2026-07-25) failed on the registry's own
spellings: abbreviations («ΜΕΓ ΑΛΕΞΑΝΔΡΟΥ 27», «Ρ ΦΕΡΑΙΟΥ», «ΑΘ ΔΙΑΚΟΥ»,
«ΛΕΩΦ. ΚΗΦΙΣΙΑΣ 118Β»), a floor glued to the number («ΛΑΠΙΘΩΝ 1ΟΣ ΟΡΟΦΟΣ
6»), a settlement written inside the street field («ΑΡΤΕΜΙΔΟΣ ΠΕΥΚΑ 14»),
a one-σ spelling («ΝΑΡΚΙΣΩΝ»), and «Λεωφόρος» prefixes that the public
instance resolves only in Latin without the word.

**Decision: re-geocode those 52 with the abbreviations expanded, under the
SAME acceptance gate as the layer (`geocode_loader._acceptable`: the hit's
Τ.Κ. prefix must equal the stored one, or resolve to the curated Π.Ε.),
plus a street-level requirement on the hit, and read every hit by eye
before it enters the curated file.** Result: **16 moved to `address`** —
6 to OSM's house-number point (Μεγάλου Αλεξάνδρου 27 Καβάλα ×2 —
ΜΠΟΜΠΟΤΗ and ΚΑΦΕΤΖΗΣ share the address —, Κηφισίας 118 ×2 — Τ&Τ
ΚΑΤΑΣΚΕΥΕΣ and its Κ/Ξ —, Γαλατσίου 45, Αγίου Δημητρίου 170) and 10 onto
the named street where OSM knows the street but not the number (Πέτρου
Ράλλη, Αθανασίου Διάκου, Καποδιστρίου Τρικάλων, Λαπιθών, Ρήγα Φεραίου
Πατρών, Κωστή Παλαμά Καματερού, Ναρκίσσων Ν. Ηρακλείου, Θερμαϊκού
Ευκαρπίας, Αρτέμιδος Πεύκων, Μεγάλου Αλεξάνδρου Ν. Μαγνησίας). Each entry
records `geo_level: number|street` and a provenance sentence in `notes`
(query, hit Τ.Κ., what OSM matched). Moves are 0,1–2 km except Πεύκα
(Ασβεστοχώρι centre → the street, 4 km). In-scope precision is now
106 address / 45 municipality (was 90 / 61).

**Five hits were REJECTED although they passed the Τ.Κ.-prefix gate** —
the gate alone is not enough once abbreviations are expanded loosely:
«ΛΕΩΦΟΡΟΣ 5» matched Λεωφόρος Ροδοπόλεως in Δροσιά (the registry says
Λεωφόρος Σταμάτας); «ΓΙΑΝΝΗ 23» matched Γιάννη Χαλκίδη (registry: Γιάννη
Αγγέλου); «ΛΕΩΦΟΡΟΣ 118Β» matched Μεσογείων (registry: Κηφισίας — fixed
by the Latin query above); «Σόλωνος» on Salamis matched the one in
Αιάντειο, 10 km from Σαλαμίνα town; «Λεωφόρος Ηρακλείου 364» with city
«ΗΡΑΚΛΕΙΟ» matched Crete. Rule kept from this: the matched street name
must be the registry's street, not merely its first word.

**Eleven stay at the centre with a reason the user may overrule** (their
street exists in OSM but the registry's own Τ.Κ. disagrees with it, or OSM
places the street in the neighbouring settlement): ΜΕΣΗΜΒΡΙΑΣ Καβάλα (OSM
tags the street 564 04 — a transposition of 654 04 — while its county is
Καβάλας); ΔΙΑΛΕΧΤΟΥ (the street is in Τρίκαλα town, 421 00; the registry
Τ.Κ. 420 35 is Δήμος Μετεώρων); ΚΑΛΟΥΔΗ Ιωάννινα (453 32 vs 452 21, both
the city); ΒΑΣ. ΣΟΦΙΑΣ 9 (OSM has no. 9 at Κολωνάκι 106 71; the registry
Τ.Κ. 115 28 is Ιλίσια — number and Τ.Κ. contradict each other); ΔΗΜΑΡΧΟΥ
ΓΕΩΡΓΙΑΔΟΥ 278 Βόλος ×2 (the street spans three Τ.Κ.; OSM returns the
Ιωλκός/Ν. Ιωνία segments, not 382 22); Β. ΚΟΡΝΑΡΟΥ and ΦΡΑΝΤΖΗ ×2
Θεσσαλονίκη (OSM's generic 541 10 vs 542 48 / 546 55 — same Ντεπώ
neighbourhood); Μ. ΑΛΕΞΑΝΔΡΟΥ «Ιωνία» ×2 (the only such street with
570 08 in OSM is Νέα Μαγνησία's, the adjacent village). The remaining 25
have nothing OSM can place, or only the wrong street: kilometre markers («25ο χλμ ΕΟ
Αθηνών-Κορίνθου», «15 ΧΛΜ ΘΕΣ/ΝΙΚΗΣ ΜΟΥΔΑΝΙΩΝ ΟΤ 1542 ΑΓΡ»), ΑΓΡ/Τ.Θ. lots,
bare localities («ΗΡΑΚΛΕΙΟ Λαγκαδά», «ΣΙΣΑΝΙΟ», «ΚΑΛΛΙΦΥΤΟΣ ΝΕΟΧΩΡΙ»,
«ΝΙΚΑΣΙ», «ΚΑΣΤΡΙΑ ΕΚΤΟΣ ΟΙΚΙΣΜΟΥ»), and streets OSM lacks (ΔΗΜ. ΣΚΟΥΡΑ
Χαλκίδα ×3, ΠΡΟΕΚΤΑΣΗ ΟΛΥΜΠΙΑΔΟΣ Εύοσμος ×3, ΠΑΡΑΛΛΗΛΟΣ Γ. ΒΑΣΙΛΕΙΑΔΗ
Καμ. Βούρλα ×2, ΜΕΓ. ΚΩΝΣΤΑΝΤΙΝΟΥ Σιάτιστα, 25ης ΜΑΡΤΙΟΥ Ν. Μαγνησία,
ΛΕΩΦ. ΣΤΑΜΑΤΑΣ, ΓΙΑΝΝΗ ΑΓΓΕΛΟΥ, ΣΟΛΩΝΟΣ Σαλαμίνα, ΛΕΩΦ. ΗΡΑΚΛΕΙΟΥ 364
Ν. Ηράκλειο).

The legend's ⓘ on «centre of municipality used as location» says this
honestly now: we hold the address; the geocoder could not place it on the
street. Scratch tooling (not committed): `regeocode_municipal.py`,
`probe_rejected.py`, `apply_regeocode.py`. Loaded with
`khmdhs.contractor_loader`; pins unchanged (151/151 located).

## 2026-08-21 · The registered office is read from the contract — a seat layer for all 151 contractors

The user asked the question the morning's re-geocode should have started
from: «do we not have the addresses in the contracts?» We do. **Every one
of the 151 in-scope contractors' signed contracts states its seat in the
party clause** («…που εδρεύει στ… επί της οδού …, αρ. …, Τ.Κ. …»): 151/151
have the clause, 146 a Τ.Κ., 134 a street or locality, 98 a house number.
The curated layer had been built from VIES/ΓΕΜΗ instead, with the
registry's abbreviations («ΜΕΓ ΑΛΕΞΑΝΔΡΟΥ», «Ρ ΦΕΡΑΙΟΥ», «ΛΕΩΦ. ΚΗΦΙΣΙΑΣ
118Β»), and in two cases a joint venture had been placed at a MEMBER's
town.

**Decision (user): the contract-stated seat is the primary source of the
registered-office layer; VIES/ΓΕΜΗ are the cross-check; where today's
register or the company's own website shows the firm has since moved, the
CURRENT seat is drawn and the contract's seat is kept beside it.** A
venture's seat is never inferred from a member's. Curated in
`khmdhs/data/contractor_seats.json` — one entry per ΑΦΜ: city / street /
number / Τ.Κ. transcribed by hand from the clause (every row read; the
phase-II PDFs write each accent as a separate letter, so the transcription
is the human's, the parser only proposed), the source ΑΔΑΜ, the verbatim
sentence, the register's values, and `contract_seat` + `note` where the
chosen seat is not the contract's. Merged into `contractor_locations.json`
(address / postal_code / city / region_pe ← the seat; `seat_source`,
`seat_ref`, `seat_excerpt`, `seat_note`, `geo_level`; `register_*` keep the
old values) → `contractor_loader` → five new DB columns → the contractor
page prints «registered office as stated in contract <ΑΔΑΜ>» with the
quoted sentence, the methodology says so, the map legend ⓘ too.

**Where the sources disagree (all checked against the register and the
company's site, as the user asked):** ΥΛΗ — contract Μαυροματαίων 9, Αθήνα;
forest.gr and ΓΕΜΗ/VIES today Λ. Ηρακλείου 364, 14122 (user-confirmed) →
website. ΤΟΜΗ — its 2022–23 contracts Ερμού 25, Κηφισιά; its OWN 2025 contract
(25SYMV016946591), ΓΕΜΗ and the ΕΒΕΑ directory 19ο χλμ Λ. Παιανίας–
Μαρκοπούλου (the ΑΚΤΩΡ address) → the later contract (a cross-contract
consistency check over the 62 contractors with several contracts found
only Τ.Κ.-granularity differences otherwise). ΚΗΠΟΠΡΑΞΙΣ —
contract Αγίου Παύλου 31, Περιστέρι; ΓΕΜΗ Αίμονος 64, Αθήνα; kipopraxis.gr
publishes no address → register. ΦΙΛΑΝΤΑΡΑΚΗ — contract Πλουτάρχου 38,
Ίλιον; VIES+ΓΕΜΗ Ανδρέα Παπανδρέου 308, Ίλιον → register. ΑΛΣΟΣ Ι.Κ.Ε. — the
reverse: ΓΕΜΗ/VIES «Προέκταση Ολυμπιάδος, Εύοσμος», alsos.gr AND the 2022
contract Νεοφύτου Δούκα 2, 544 54 (Πυλαία) → website. Τ&Τ ΚΑΤΑΣΚΕΥΕΣ — its
contract names only the representative's residence, the register the same
Κηφισίας 118Β → register. ΛΙΑΧΤΙΔΑ — the curated «Μοναστηρίου 93Α» (a
Diavgeia reading) was stale: contract and ΓΕΜΗ agree on Γ. Φραντζή 1.
**Flagged, not decided**: ΕΛΛΗΝΙΚΑ ΕΡΓΑ Ο.Ε. — ΓΕΜΗ/VIES «25ης Μαρτίου 4,
Νέα Μαγνησία», its 2023 venture contracts and its own 2025 contract
«Ορφανίδου 1, Θεσσαλονίκη», no website: the later document is drawn, the
register kept; ΠΑΠΠΑΣ ΣΤΕΡΓΙΟΣ — the contract seats him «στην Καλλιθέα
Καλαμπάκας Τρικάλων, Διαλεκτού 14, ΤΚ 42100», ΓΕΜΗ in Δήμος Μετεώρων
(42035): the village is the seat, drawn at its centre; Κ/Ξ ΜΠΟΜΠΟΤΗ–
ΞΑΝΘΟΠΟΥΛΟΣ — the only contract stating no seat for the venture: Καβάλα
without a street. The morning's own move of Κ/Ξ ΤΣΑΝΤΑΛΗ–ΒΕΛΩΝΗΣ to
Μεγάλου Αλεξάνδρου, Νέα Μαγνησία (VIES) was wrong by its contract («Διαβατά,
Βασ. Κωνσταντίνου 8») and is undone here. **Two regions change**, both
ventures whose dot was inferred from a member: ΚΑΡΝΟΜΟΥΡΑΚΗΣ–ΑΛΚΗ (ΥΠΟΕΡΓΟ
Β) Μαρούσι → Καβάλα, ΛΙΑΡΗ–ΓΚΙΚΑΣ Κόρινθος → Λίμνη Ευβοίας (the connections
pin fell 259 → 257 flows as two home/work pairs merged). Nine contracts
state no Τ.Κ.; the register's is used and the entry says so.

**Geocoding, from the clean text** (`_acceptable` Τ.Κ./Π.Ε. gate + a
street-level requirement; Greek, Latin without «Λεωφόρος», settlement
centre): in-scope dots now **109 address (34 at the street number, 75 on
the named street) / 42 settlement centre** — the morning's 106/45 and
July's 90/61. Two traps the first run exposed, now rules: a "centre"
must be a SETTLEMENT-type hit that names the settlement in its own
place fields (the first run took the Μητροπολιτική Ενότητα centroid for
«Θεσσαλονίκη», 19 km out); and a Τ.Κ.-prefix match in a DIFFERENT
settlement is refused (OSM's only Σόλωνος on Salamis is in Αιάντειο, 10 km
from the town — that venture stays at Σαλαμίνα's centre). A same-settlement
street hit whose only fault is OSM's postcode tag (Θεσσαλονίκη's generic
541 10 on Κορνάρου, Φραντζή, Ορφανίδου) is accepted as `gate: settlement`
and was read by eye. Hand-placed: Μεσημβρίας Καβάλα (OSM's transposed
564 04), Καλλιθέα Μετεώρων, Ομήρου Θεσσαλονίκη (OSM has none inside the
city — centre), Νικάσι Καρύστου (not in OSM — Κάρυστος centre), Κηφισίας
118 (number-level only via the Latin query). 14 dots moved more than 3 km,
12 of them to the settlement the contract names (Μάκρη, Σισάνι, Βασιλική
Γόρτυνας, Καινούργιο, Πυλαία …); the scratch tooling (`seat_audit.py`,
`seat_parse.py`, `build_seats.py`, `geocode_seats.py`, `merge_seats.py`)
is not committed. Pinned by `tests/test_contractor_seats.py`: every
in-scope ΑΦΜ has a seat, every contract ref is a record of that
contractor's own chain, every excerpt carries the ΑΦΜ, the locations file
and the DB carry the seat, the two regions, the six divergent entries keep
the contract seat beside them. The earlier entry of today (the 16 re-placed
dots) is superseded by this layer — those 16 are all among the 109. A second look at the weak centres moved Καλούδη Ιωαννίνων and Μαυροματαίων 39 onto their streets and the two Δημ. Σκούρα ventures from an Αυλίδα railway station (the first run's «Χαλκίδα, 34100») to Χαλκίδα town — a centre must now be a town/village-type hit, preferred over postcode or municipality centroids.

**The 13 «street OSM lacks» seats, asked of OpenStreetMap directly (user: «let's do
these 13»):** Overpass (anonymous) queried for highway ways matching the
street's stem within the settlement, each hit reverse-geocoded to confirm the
settlement. Eight placed: Ομήρου 3 Θεσσαλονίκη at the NUMBER (OSM way tagged
«Ομηρου 3» — Nominatim's search never returned it), Γιάννη Αγγέλου Χαριλάου,
Κουντουριώτου Μυτιλήνη, Δημάρχου Σκούρα Χαλκίδα (×2, beside the ΔΟΥ as the
register says), Γερασίμου Βασιλειάδη Καμένα Βούρλα (×2 — the contract names
the PARALLEL street; the dot sits on the named one), the Αιαντείου avenue for
ΖΙΤΑΚΑΤ. Five stay at the centre with the reason in `seat_note`: OSM's only
Μακεδονομάχων is in Λαγκαδάς town, not the village Ηράκλειο; its only
Σικελιανού is in Αμπελάκια, 3 km from Σαλαμίνα and without a Σόλωνος; and
Καρπενησίου Καινούργιο, Μεγ. Κωνσταντίνου Σιάτιστα, Διαλεκτού Καλλιθέα exist
in neither index. In-scope dots: **117 address (35 number / 82 street) / 34
settlement centre** — 17 documents name only a settlement, 12 km markers/
localities/lots, 5 streets no map knows.

**Verdicts (user, same day):** ΕΛΛΗΝΙΚΑ ΕΡΓΑ Ο.Ε. — the contract's seat
(Ορφανίδου 1, Θεσσαλονίκη); ΑΛΣΟΣ Ι.Κ.Ε. — the website + contract seat
(Νεοφύτου Δούκα 2, Πυλαία); ΦΙΛΑΝΤΑΡΑΚΗ — the register's (Ανδρέα
Παπανδρέου 308, Ίλιον). Recorded in the three entries' notes.

**Dots in the sea — the de-overlap spread, not the geocode.** Asked why
ΜΑΝΑΡΙΤΣΑΣ ΕΥΑΓΓΕΛΟΣ's dot sat in the water: every one of the 151 points
(and the July point) tests INSIDE the drawn Π.Ε. polygons on both Atlas
layers (`pe.topo.json`, `pe_hires.topo.json`, d3 `geoContains`) — the seat
itself is on land. What put it offshore is `spreadOverlaps`: seats sharing
one point are fanned out on a sunflower spiral (0,02° ≈ 2 km steps at
country level, 0,034° for contract dots) so all stay visible, and the
spiral ignored the coast — Λίμνη's waterfront point is shared by FIVE seats
(ΜΑΝΑΡΙΤΣΑΣ, his two ventures with ΑΓΓΕΛΑΤΟΣ, ΛΙΑΡΗ–ΜΑΝΑΡΙΤΣΑΣ, ΛΙΑΡΗ–ΓΚΙΚΑΣ
at Καστριά), Μεγ. Αλεξάνδρου 27 in Καβάλα by nine, Σαλαμίνα town by four,
Μπόνου 7 Βόλος by three, Χαλκίδα by four — all coastal, so the outer spiral
slots fell in the sea. Fix: `spreadOverlaps(points, step, onLand?)` skips
any spiral slot the predicate refuses and tries the next (40 slots, else
the point stays put); `AntineroMap` passes `geoContains` over the same
coarse Π.Ε. layer PaperMap draws (memoised load). Pinned by
`atlas/src/lib/maps/spread.test.ts`, which spreads the real Λίμνη / Καβάλα /
Σαλαμίνα groups over the real `pe.topo.json` and asserts every output on
land. The dots now fan out ALONG the coast. The frozen webui `/overview`
keeps its GeoCommon spiral.

## 2026-08-21 · Completion acts: the ministry's subject line can key the wrong ΑΔΑΜ, a «Μερική έγκριση» is not an ending, and the end date must be the ACCEPTANCE protocol's

Asked to inspect `/antinero/contract/23SYMV013019416` (lot 15Γ, Χαλκίδα/
Αλιβέρι, ΤΡΙΑΝΤΑΦΥΛΛΟΥ): its page showed Δασαρχείο Ξάνθης and Διεύθυνση
Δασών Ροδόπης as responsible services and a «Μερική έγκριση του Πρωτοκόλλου
Παραλαβής … (15Α)» among its completion acts. Reading the acts: ΥΠΕΝ's two
acceptance acts for lot **15Α** (Ξάνθη/Ροδόπη, ΛΙΑΠΟΠΟΥΛΟΥ — 23SYMV013019394)
carry, in their SUBJECT line, lot 15Γ's ΑΔΑΜ 23SYMV013019416 — a keying
error of the ministry — while their recital 14 cites the right contract
(«Την από 04.07.2023 Σύμβαση Έργου (ΑΔΑΜ: 23SYMV013019394 2023-07-05)») and
the title/lot/services are 15Α's. `completion_acts_loader` links by the
subject's ΑΔΑΜ, so both acts landed on 15Γ, and `forest_loader`'s fourth
source (the acts) then hung Ξάνθη/Ροδόπη on a Εύβοια contract. A screen of
all 283 stored acts (subject ΑΔΑΜ vs the recital's «Σύμβαση … Έργου (ΑΔΑΜ:
X)», same-chain citations ignored) found one more such family: lot **4Α**'s
two acts (Καστοριά/Φλώρινα, 23SYMV012946366) carried lot 4Δ's ΑΔΑΜ
23SYMV012946406 (Πιερία) — and a counter-example that forbids a blanket
«recital wins» rule: Ψ8ΝΛ4653Π8-4Β6's recital cites a non-existent
…014431925 for …014431915, the subject being right there.

**Three fixes, all in `khmdhs/completion_acts_loader.py`:**
1. **Curated overrides** — `khmdhs/data/completion_act_overrides.json` (ΑΔΑ
   → the contract the act really concerns, with the act's own evidence
   quoted): 6Χ884653Π8-ΒΙΗ and Ψ6ΩΞ4653Π8-ΗΟ4 → 15Α, 68Μ34653Π8-ΞΗΛ and
   6ΩΓΖ4653Π8-7ΔΚ → 4Α. Applied at insert; the loader WARNs whenever the
   subject ΑΔΑΜ and the recital ΑΔΑΜ name stored contracts of different
   chains and no override exists — the candidate list, never an automatic
   re-pointing. 15Α and 4Α now carry their acceptance acts; 15Γ and 4Δ
   keep their own (the Ξάνθη/Ροδόπη and Καστοριά/Φλώρινα links fell away;
   the connections pin went 476 → 474 contractor–authority pairs, /explore's
   completed count 148 → 149).
2. **«Μερική έγκριση» rejected** — a partial approval of a protocol is not
   the project's ending (it joins τμηματικ/προσωρινή in `_REJECT`); the
   same pass dropped a «Βεβαίωση Τμηματικής περαίωσης» the early harvest
   had stored (acts 283 → 281).
3. **The end date is the acceptance protocol's.** `extract_end_date` had
   taken the FIRST «το από DD.MM.YYYY πρωτόκολλο …» in the act — and every
   ΥΠΕΝ act lists the «πρωτόκολλο εγκατάστασης αναδόχου» (the contractor's
   installation) in its recitals before the acceptance protocol: **105 of
   283 acts carried the installation date as the project end** (e.g. 15Α's
   «17.07.2023» — the day the works STARTED). Now only a protocol whose tail
   says παραλαβής/περαίωσης/περάτωσης/ολοκλήρωσης counts, the LAST such in
   the act wins, and «εγκατάστασης» is excluded; an act without one falls
   back to a «περαιώθηκαν … DD.MM.YYYY» sentence, else its issue date.
   137 end dates changed; `end_basis` is now protocol_date 234 / act_date
   47 (was 251/32 — the 15 «protocol» dates that were installations are
   honestly act dates now). `--reextract` recomputes kind / attribution /
   end date for every stored act from the cached text, offline, and is what
   applied all of this (then `forest_loader` rebuilt the links: 25 act-
   sourced links on 13 contracts, one `|part`).

Pinned in `tests/test_completion_acts.py` (kinds 227/54, 156 contracts,
basis 234/47, zero «εγκατάστασης» excerpts, the two re-attributions) and
the real-DB pins. Open question noted, not changed: an act «για την περιοχή
αρμοδιότητας του Δασαρχείου Χ» accepts ONE service's part of a multi-service
contract; the `|part` marker fires only on «για το τμήμα του έργου», so
such acts still read as the contract's end on the timeline.

## 2026-08-21 · Map cards on the Anti-nero page: two slots, hover shows / click holds, short and factual

Reviewing the card logic of the two map pairs (€ choropleths / Individual
dots) with the user: one black card slot per map served region hover, dot
hover and selection alike, so a dot's card replaced the region's and leaving
the dot left no card; hovered and held cards looked the same; cross-map hover
pinned stacks of cards on the other map; cards carried instructions; region
cards were off on the drilled left map. **Decision (user, items 1–4 of the
review):** (1) two slots — the place's card grey at the top-left, the item's
black at the bottom-left, both on at once; (2) hover shows, click holds — a
held card has a white rule and a ✕, Esc or ✕ releases it; cross-map hover
highlights dots and seat links but pins no card (only the selected contract
pins its own card and its contractor's on the other map); (3) cards are
short — «place · N contracts · €», «ΑΔΑΜ · authority · €» with the ΑΔΑΜ as
the link, «name · N contracts · €» with the name as the link — and every
instruction lives in the legend ⓘ; (4) region cards on in every state on
both maps. Implemented in `PaperMap` (`splitTips`, pinned item card with
onClose, Esc), `DotLayer` (`onUnpin`), `AntineroMap`; the ΔΑΣΕ, sponsored
and contractor-page maps keep the single slot. Items 5–6 followed the same day, with two more user decisions: the drill
TABLE below the maps is removed («no one can read it with the maps; the cards
hold its facts») — a «✕ <unit> · all of Greece» pill beside MAP steps out of
the drill; the selection lives in the URL (`?sel=<ΑΔΑΜ>`), survives the €/dots
toggle, is cleared by a new drill, by a click on bare map and by Esc (a second
Esc resets the drill). Colour coding aligned with the legend: every contract
dot is one grey (the two-grey alternation of multi-authority contracts was a
leftover of the hue grouping and the legend could not show it), the legend's
swatches are the map's own colours (contract dot, selected dot, settlement-
centre dot with its dashed ring over a 55 % fill), and the € ramp key prints
the values at the sqrt-scale boundaries the map uses, so a grey can be read
back to a €-band; the white «none» swatch sits outside the scale.

## 2026-08-21 · Lifecycle layer, phase 1: the deadline extensions ΥΠΕΝ publishes on Diavgeia, read by machine

The user asked for the τμηματικές/προσωρινές εγκρίσεις in the document trail,
then sharpened it: the data gets richer only through **changes of deadline,
changes of amount and cancellations** — and asked whether I had read the
documents (no: subjects only). An inventory of every Diavgeia act whose
subject cites one of the 344 stored contracts (4,931 acts, metadata only)
sized the question: 489 παρατάσεις, 378 Α.Π.Ε., 681 επιμετρήσεις, 644
λογαριασμοί, 897 ημερολόγια, 553 χρονοδιαγράμματα, 251 αναστολές, 7
τμηματικές/προσωρινές παραλαβές — and **no cancellation at all** (no
διάλυση, έκπτωση, καταγγελία or ματαίωση; the 13 «ανάκληση/ακύρωση» acts
revoke an earlier approval, never the contract). Only 23 of the 489
extension subjects carry a date; the new deadline lives in the body.

**Decision (user): phase 1 = the extensions, read from the PDFs by machine
with verbatim evidence; the user reads only what the extractor flags.** A
30-act pilot read 26 cleanly, 3 with several dates, 1 unreadable; the rules
it fixed: the operative part starts at the LAST «Αποφασίζουμε» (the recitals
list the previous extensions with their dates — anchoring earlier reads the
OLD deadline as the new one), every «μέχρι/έως (την|τις) DD.MM.YYYY» in it is
kept and the latest is the contract's new deadline, several distinct dates
mean a per-area extension (flagged, all dates kept), «κατά N ημερολογιακές
ημέρες» rides beside, and an act without an operative anchor or a date is
stored with its flag and no deadline — never a guess. The full run
(`khmdhs/extension_acts_loader.py`, table `contract_extension_acts`, FK
CASCADE, chain-tip attribution, the same `completion_act_overrides.json` and
lot-letter WARN as the completion layer): **463 extension approvals on 167
contracts (159 in scope) — every one read, 23 per-area, 105 plain / 358
τμηματικές**; 20 subject hits rejected as non-extensions (revocations,
schedules approved «λόγω παράτασης»); three wordings added on the way
(«μέχρι τις και 30.03.2026», «με ημερομηνία περαίωσης την 31-05-2026», «έως
την 28η Αυγούστου 2026»). The one lot-letter WARN is the registry's own
title error (ΚΗΜΔΗΣ titles two contracts «ΕΡΓΟΥ 16Δ»; the acts call the
Ρέθυμνο one 16Ε with the right ΑΔΑΜ). The contract page's DOCUMENT TRAIL
shows them as «(Nth) deadline extension» / «partial deadline extension»
rows with «→ DD.MM.YYYY (per area) · κατά …» in the title cell and the
Diavgeia PDF; the ChainTimeline's extension steps still come from the 16
ΚΗΜΔΗΣ records (feeding them from these 463 is the next step). Nothing
that read `contract_completion_acts` changed.

**Same day, user: the timeline draws them.** `contract_deadlines` now merges
the 463 acts with the 16 ΚΗΜΔΗΣ steps: a step per act (its ΑΔΑ is the ref,
so the DOCUMENT TRAIL row pairs with the arc), the deadline in force is the
running maximum, an act re-stating a record's deadline merges into that
step, a per-area act is marked and its latest date drawn, and a step that
did not move the deadline forward says so (`later: false`). Result: **443
steps over 160 in-scope chains** (427 Diavgeia + 16 ΚΗΜΔΗΣ; 355 moved the
deadline forward, 23 per-area) — the methodology prints the counts from
`/api/meta`, the pins hold them.

Toolchain: the Windows build of `pdftotext` could not open a Greek-named
file (ANSI command line) and wrote «?» for every Greek letter without
`-enc UTF-8` — `diavgeia_loader.fetch_decision` now converts through ASCII
temp names in UTF-8 (the completion and payment layers share the helper).
Pinned by `tests/test_extension_acts.py` (classifier, ordinal, extractor
traps, 463/167/23 counts, the keying-error families on their own contracts).

## 2026-08-21 · Anti-nero maps: the € scale stays the sqrt ramp with the «0 · bar · max» key

Two attempts to make a grey readable as a € value were tried and withdrawn
the same day: tick values at the sqrt-scale boundaries (they overlapped at
the strip's width) and a classed scale with round thresholds and a worded
legend (< 1M · 1–5M · … — the user rejected the look: «former ways were far
nicer», and the worded pairs wrapped the strip). **Decision (user): the map
keeps the sqrt ramp (`makeChoro`, shared max on both maps) and the legend
the user approved on 2026-08-20 — 0 · [white + eight swatches in one
hairline] · max.** Kept from the review: the drilled unit's outline is
heavier than a hover but not thick (1.6), the country-level
registered-office dots are one step lighter (#555) so they read over the
darkest fills, every legend swatch is the map's own colour, and the
selected contract's dot turns black (it had only gained an outline). A
contractor dot on the right map is SELECTED on click as well (user, same
day): its card held, its contracts lit on the left with their seat links,
one selection at a time (`?selv=` beside `?sel=`), and its page is reached
from the card's link rather than by the click that used to leave the map.
Three more user decisions the same evening: the timeline's extension labels
print the ordinal only («1st», «2nd» — the words overlapped when acts were
days apart; a label closer than 14 units to the previous one is dropped,
the arc and its hover title stay), the timeline's symbols carry no outline
(no white halo on ✔ or €, no stroke on a dot, no outline on the hovered
bar), and on the maps a hot dot — selected, or lit by a selection on the
other map — is painted above its neighbours.

## 2026-08-21 · Extension acts: what each one extends (scope), one refusal, three dates the acts got wrong

Asked what the 463 acts «actually are», the layer was read once more and
three things changed.

**Scope of the grant.** A «τμηματική παράταση» is not a smaller extension
— it is an extension of ONE τμηματική προθεσμία, a milestone the contract
sets beside its συνολική προθεσμία: the works in one service's area, the
studies' submission, a stage. The grant clause after the quoted project
title says which, and `contract_extension_acts.scope`/`scope_text` now
carry it verbatim (`extension_acts_loader.extract_scope`: study / stage /
area / whole, the named-service phrase cut before the grant's own words
«μέχρι … / για N ημέρες / σύμφωνα»). Of the 358 τμηματικές, 203 name an
area («για την περιοχή αρμοδιότητας του Δασαρχείου Καλαμπάκας»), 5 the
studies («ως προς την υποβολή των προβλεπόμενων μελετών»), 4 a stage, 1 the
whole, 145 say nothing either way; of the 104 plain ones, 16 say «στη
συνολική προθεσμία περαίωσης», 28 still name one area of a multi-area
contract, 1 a stage, 59 say nothing. 260 of the 358 τμηματικές sit on
multi-authority contracts; the plain ones split 62/42. The contract page
prints the scope in the trail row («· for Δασαρχείου Καλαμπάκας», «· the
study's submission (…)», «· the whole contract»).

**One act is a refusal.** ΨΥΙ04653Π8-848 «Απόρριψη αιτήματος χορήγησης
τέταρτης (4ης) παράτασης …» (25SYMV017073922, Δασαρχείο Σπάρτης) had been
classified as an extension and the request's date read as its deadline.
New `act_kind = extension_refused`: no deadline, the operative sentence
(«Απορρίπτουμε το από 26.06.2026 αίτημα …») as the excerpt, the refused
scope kept; it is a trail row («Extension refused · the request was
refused · for Δασαρχείου Σπάρτης») and never a timeline step. The
inventory holds no second refusal.

**Three acts state a deadline earlier than their own date** — the act's
own year typo, not ours: Κ4Χ04653Π8-7ΕΡ (26.01.2026) and ΨΧΗΛ4653Π8-5ΩΔ
(23.12.2025) grant «μέχρι τις 05.02.2025» on a contract signed 24.06.2025
(the recital asks for 07.02.2026), ΨΕ8Λ4653Π8-ΘΚΠ (16.01.2026) «μέχρι τις
10.02.2025». **Rule: the date is kept AS WRITTEN, flagged
`deadline_before_issue`, printed in the trail with the flag said in words,
and never drawn as a step** — nobody here corrects a document. The
timeline therefore counts 439 steps over 160 chains (423 acts + 16 ΚΗΜΔΗΣ
records; 443 before this rule).

Read alongside: of the 292 steps that follow an earlier known deadline,
166 were approved AFTER that deadline had lapsed (the act is dated later
than the deadline it extends — the usual practice, not an exception); a
τμηματική step adds a median 30 days (p25 19 · p75 41), a plain one 37,5
(31 · 90); measured against the contract's OWN deadline (duration from the
start of works), the first τμηματική of a contract lands a median 57 days
after it but a quarter of them 46+ days BEFORE it — they extend a
milestone, not the end — while the first plain one lands 13–56 days after
(median 40); 345 of 463 operative parts grant «με αναθεώρηση» (the delay is
not charged to the contractor — ν.4412 άρθρο 147), the rest say nothing,
none says «χωρίς αναθεώρηση». Pinned in `tests/test_extension_acts.py`
(scope table, refusal, flags, the 12-act Καλαμπάκα chain) and the Atlas
real-DB deadline pins.

Tooling note (why the scope phrase first came out untrimmed): a regex
`\b` written through a Bash heredoc reaches the file as a literal
backspace (0x08) — the lookahead never matched. Write regex patches with
the Write/Edit tools, or build the backslash as `chr(92)`.

## 2026-08-21 · The contract timeline gets one lane per forest service where the acts name areas

Asked whether a τμηματική παράταση can be told apart as studies / works /
an area, and whether the bar should split by area, the answer from the
documents was: the contract sets TWO clocks (the studies' submission «σε
είκοσι (20) ημερολογιακές ημέρες από την υπογραφή», the works «σε τρεις (3)
μήνες από την ημερομηνία έναρξης») and enumerates no τμηματικές προθεσμίες
of its own (§7.2.1: «που προβλέπονται στο εγκεκριμένο Χρονοδιάγραμμα»), so
the acts are the only statement of WHICH clock moved — and they say it: the
5 study acts («ως προς την υποβολή των προβλεπόμενων μελετών») all fall
16–24 days after signature, the area acts («για την περιοχή αρμοδιότητας
του Δασαρχείου Χ») a median 174 days after it, 216 of the 358 name the
works outright in the request recital, none extends both in one act. 53
contracts' area acts name ≥2 services whose last deadlines diverge by a
median 33 days (p75 130, max 510) — on one bar only the last area shows.

**Decision (user: «let's try your suggestion»): one thin lane per forest
service under the contract bar, only where the acts name areas.** Data:
`contract_extension_acts.scope_auth` = the registry's canonical services
an area act names, resolved by the SAME matcher forest_loader uses on
titles (231 of 232 area acts; the one left names «Διεύθυνσης Δασών
Φθιώτιδας», a directorate the registry does not carry, and is shown as
«service not matched», never assigned); `contract_completion_acts.part_auth`
= the ONE service whose part an acceptance act accepts («για το τμήμα
περιοχής ευθύνης Δασαρχείου Σπερχειάδας», 23 of 24 such subjects; the 24th
names the part by title). Two readings fixed on the way: the pdftotext page
watermark («ΑΔΑ: 6ΘΑΩ4653Π8-0ΘΛ 3») could sit INSIDE the service phrase and
break the match — stripped before reading the scope (4 acts gained a scope:
area 203 / unsaid 145 of 358 now) — and two genitives the acts use were
met: «Ρεθύμνης» joined the registry aliases of Δ/νση Δασών Ρεθύμνου, while
«Φουρνά» is normalised to «Φουρνάς» inside the resolver only, because
«ΦΟΥΡΝΑ» is the ΔΑΣΕ unit's curated spelling in dase_units.json and a test
pins it OUT of this registry.

Drawing (`transforms/lanes.buildLanes`, pure and pinned; `AreaLanes.svelte`
inside the ChainTimeline svg) — first as one thin lane per service under
the bar, then, the same day on review (user: «instead of duplicating the
bar, split the grey part»), as **strips**: the solid bar is the promise,
once; its lighter extended part is split into one strip per linked service
in the contract's order (+ a service an act names but the contract does not
link, starred), each running to the last date that service's own acts
granted, a dot per act naming it (a step naming two services sits on both
strips) with the arrow to the date it granted — the arrows the single bar
always had — the service's name RIGHT-ALIGNED at the timeline's end — shown only while
its strip (or one of its acts, from the trail) is hovered — in the
short form «Kalampaka F.S.O.» / «Rodopi F.D.» (`names.authEnShort`), the
solid bar as tall as all the strips together (7 units each), and **a ✔ only
where ΥΠΕΝ accepted that part on its own** — an area without a part-acceptance carries no ✔ (the contract's
single acceptance stays on the bar). Acts that name no area sit on one
last strip «area not stated»; the studies, a stage, the whole stay on the
contract bar (the study step is labelled «studies», not an ordinal), and
the arcs and ordinal row move under the strips. 72 in-scope contracts draw
strips; every other page is unchanged. Same round: the contract map prints
every forest authority's name in plain black beside its seat dot (short
form, no outline; of eight positions around the dot the one that lies inside
the dot's own region — crossing neither a border nor the coast, tested with
geoContains on the label box — and covers no other dot or label wins), and
a service whose deadline was never extended and has no acceptance of its own
draws no strip (an empty row read as an unbalanced bar), the arrows stand
alone (the dot at the arrow's tail was redundant; no dot at all, even for a
few days' extension), the hovered name carries no outline and sits at the right end of its OWN
grey bar (final form; just above the bar's end when there is no room before the
chart's edge — never on the grey), and the map names were tried always-on (plain black, then white on
small black boxes) and withdrawn the same day — **the names are a hover
card again, at the map's TOP-LEFT corner (`PaperMap showTip corner`,
`DotLayer tipCorner`), the δήμοι cards keeping the bottom-left.** The
arrows on the strips read poorly at density (a 6-unit strip cannot hold
a dipping curve and a 6-unit head; chained extensions pile their heads at
the end), so **each strip is cut into SEGMENTS: one piece per extension,
from the deadline it found in force to the one it granted, a hair of white
between, a thin dark tick where the approval was signed — mostly after
the piece begins, which is the «approved after the lapse» fact made
visible; a re-statement of a date already in force adds no piece, only
its tick.** The white hair + black tick pair was still two marks too many on a 6-unit
strip (user): **the pieces now alternate two tones of the bar's own grey
(28 % / 42 %), no lines, no ticks** — the approval day lives in the
piece's hover card and its trail row. And so a name always has room at the
end of its own bar, **the axis stops 96 units short of the right edge
when strips exist** (a name above the bar collided with the € row; one
inside sat on the grey). Hover a piece → its trail row, and back, and on a striped bar the € payment
marks move up to the label line where «call» is written, off the strips, and the procurement DIAGRAM's
shapes are centred on the slot — the box the map fills, as tall as the
facts column — with its caption at the foot. The legend ⓘ and the
methodology say so.

## 2026-08-21 · Extension layer, curation pass 1: the per-area dates read by hand, two subject keying errors, two directorate judgments

The model agreed this morning stands — the machine reads, Claude reads,
the user decides only on what is flagged — and the first pass delivered
its verdict list. What was read: every per-area act (23) and the five acts
naming a service the contract is not linked to.

**Defect fixed — which service got which date.** A per-area act grants
different dates per service («μέχρι τις 30.11.2024 για … Ηρακλείου και
μέχρι τις 20.11.2024 για … Χανίων») and the machine kept every date but
not the mapping, so a strip took the act's latest date. The acts write the
pairing in three orders (service-then-date, date-then-service, a general
list then per-service dates), and a rule covering all of them reliably
does not exist at this size — 23 acts — so the mapping is **hand-curated**
in `khmdhs/data/extension_act_curation.json` (`area_dates`, the verbatim
grant sentence per act; a curated date must be one the act's operative
part states, a curated service must be a registry authority — the loader
refuses otherwise). Stored in `contract_extension_acts.area_dates`, shipped
on the steps, and `transforms/lanes.buildLanes` gives each strip its own
date. 22 acts carry a mapping (21 area + the study act Ψ232 recorded for
completeness); 9Κ2Η4653Π8-ΟΩΨ is not per area at all — its two dates split
the WORKS («νέων εργασιών» 05.09 / «φύτευση πλατύφυλλων» 30.11) — and
stays as read. The service phrase now also matches «για το Δασαρχείο Χ»
without «περιοχή αρμοδιότητας» (area 204 / unsaid 144 of 358; 9ΥΒΦ gained
Πεντέλης, Δωδεκανήσου, Λέσβου; ΕΧΞΝ its two services).

**Two subject keying errors** (the subject's ΑΔΑΜ is not the contract the
act is about; both re-pointed through `completion_act_overrides.json`, the
shared file): 9ΞΣΟ4653Π8-Ζ9Ο keys 26SYMV018725481 (Ροδόπη/Κιλκίς) but its
title, grant («Δασαρχείου Ελασσόνας»), body ΑΔΑΜ and recipients are
26SYMV018739467 (Φωκίδα/Ελασσόνα); ΨΕΡΟ4653Π8-2Θ6 keys 22SYMV010585198
(ΥΠΟΕΡΓΟ 4.Γ) but its title and operative are ΕΡΓΟ 2.Β's
(«Ολυμπίας και Αμαλιάδας», body cites 22SYMV010473680 → tip
22SYMV010856515). 169 contracts / 162 in-scope chains now carry steps.

**One deadline override**: ΨΠΩΟ4653Π8-ΩΝΚ grants the Stage-3 study
«μέχρι τις 04.10.2025»; the 30.10.2025 in the same sentence is a condition
on the studies' approvals — the machine had taken the latest date and
flagged the act per-area. 22 per-area acts remain.

**Two judgments, user-reviewed**: an act naming a DIRECTORATE stands for
the contract's Δασαρχεία under it — ΕΩ564653Π8-1ΙΖ «Διεύθυνσης Δασών
Φθιώτιδας» → Αταλάντης + Σπερχειάδας (the two the act is notified to; the
registry does not carry that directorate), ΨΨΕΩ4653Π8-90Π «Διεύθυνσης
Δασών Έβρου» → Αλεξανδρούπολης + Σουφλίου (the contract's Έβρος services).
No area act is left unresolved and none names a service outside its
contract. Pinned in `tests/test_extension_acts.py`.

## 2026-08-21 · Extension + completion layers, curation passes 3–5: the machine reading checked by eye, four rules widened, one bug

Claude read, the user decides only on flags (the model set this morning).
What was read: all 27 study/stage/whole acts, all 16 ΚΗΜΔΗΣ extension
records against the acts of their chains, 40 random acts of the 411
remaining area/unsaid ones (20 + 20), and the 47 completion acts the
extractor had dated by the act's own date — plus the 23 per-area acts and
the 5 off-contract acts of pass 1. **Error rate on dates: 0 of 60 sampled
extension acts** (every extracted deadline matched the operative sentence);
the findings were all on the SCOPE side and on two rules, and each one was
turned into code and pinned, never hand-patched per act:

* **Service lists with commas lost every service after the first** —
  «Δασαρχείων Αταλάντης, Λαμίας και Σπερχειάδας» resolved to Αταλάντη only
  (the service phrase refused commas). 12 acts gained their full list.
* **«μελέτης» carries its accent** — the study test read «μελετ» only, so
  «ως προς την υποβολή της προβλεπόμενης μελέτης» passed as an area act (12)
  or as nothing (7); 24 study acts now, 5 before. The STAGE test runs before
  the study test (a «Στάδιο 1 – Υποβολή Προμελέτης» is a stage).
* **The grant's start**: the quoted project TITLE is the LONGEST top-level
  «…» opening before the grant's first date — not the last «», » of the
  sentence (a δ.τ. quoted later had hidden one grant; an ΕΣΥ passage quoted
  after the grant must not win; an unclosed nested title — Ψ3ΟΟ — hands the
  grant to the text after the last ΑΔΑΜ mention). 9Φ03 is honestly unscoped
  now (its services were in the title, not the grant); 9Λ6Θ narrowed to the
  one service its grant names. Scope table now: τμηματικές area 195 · study
  24 · stage 4 · whole 1 · unsaid 134 of 358; plain area 28 · stage 1 ·
  whole 16 · unsaid 59 of 104.
* **A bug in the timeline, not the acts**: `contract_deadlines.announced()`
  tested the ΚΗΜΔΗΣ duration unit with `.upper()` — «Ημέρες» became
  «ΗΜΈΡΕΣ», the accent survived, «14 days» read as 14 MONTHS and four
  supplementary approvals drew deadlines in 2027–2028. Folded; 435 steps /
  162 chains (423 acts + 12 ΚΗΜΔΗΣ records). The 8 ΚΗΜΔΗΣ «Παράταση»
  records that coincide with an act on the same date merge into it; the
  other four sit a day off an act or carry a date the acts do not state —
  both kept, honestly.
* **Completion acts (pass 5)**: of the 47 dated only by their own date, 21
  DO state the acceptance in forms the extractor had not read — «τα από
  25.02.2025 πρωτόκολλα οριστικής παραλαβής» (plural), «τα από 27.11.2024
  και 29.11.2024 πρωτόκολλα» (a list: the LATEST), «το από 19&21.12.2023 /
  06-07.11.2023 πρωτόκολλο» (a two-day protocol: its second day),
  «υπ’ αριθ. 566498/15.11.2024 πρωτόκολλο οριστικής παραλαβής», «πρωτόκολλο
  οριστικής παραλαβής (με ημερομηνία 29.06.2023», and the περαίωση forms
  «περί περαίωσης των εργασιών στις 11-07-2026», «περαιώθηκαν … την 9
  Σεπτεμβρίου 2024», «η περαίωση … πραγματοποιήθηκε την 07η Οκτωβρίου 2024».
  Rule kept — the LAST acceptance protocol, never an installation — read
  more widely, and TIGHT: the date list must stand immediately before
  «πρωτόκολλ…» (a transmittal letter's date 40 characters earlier had crept
  in on two acts and was thrown out again). 255 protocol_date / 26
  act_date; the 26 are βεβαιώσεις περαίωσης that date only the supervisor's
  report, or nothing — kept at the act's date, said so.
* **Pass 4, the 193 unscoped acts**: read as openings, they are genuinely
  unscoped — «…», μέχρι τις DD.MM.YYYY, σύμφωνα με το Ν.4412/2016» after the
  title, 74 phrasings, none naming an area, a study or a stage; 114 sit on
  single-authority contracts where the question is moot. No rule was added;
  they stay «area not stated» (drawn as a strip only beside other strips).

* **Pass 6, coverage of the ΑΔΑΜ-in-subject search**: for 12 contracts
  whose acts carry a lot code in the subject («Σύμβασης (16Δ)», «(22Β/2025)»)
  Diavgeia was searched by the LOT CODE instead (1,214 hits, each search
  capped at 100): every παράταση act found that cites no ΑΔΑΜ in its
  subject was a different matter altogether (eleven «Παράταση χρόνου
  υλοτομίας της συστάδας 4δ …» of municipal forests), and none cited an
  ΑΔΑΜ of ours that the layer lacks. No evidence of a missed act; the probe
  is a sample under a 100-hit cap, and the methodology says the layer is
  built on the subject line.

Pinned: scope table, area-act count 224, completion basis 255/26, timeline
435/162/12. The acts' own errors found on the way are in the pass-1 entry
(two subject ΑΔΑΜ typos, three deadline year typos, one refusal).

## 2026-08-21 · An extension act that names no area extends every area the contract's title names

The user read 9Θ5Ψ4653Π8-Χ3Τ (25SYMV016495437): «Εγκρίνουμε την τμηματική
παράταση … της Σύμβασης (10/2025) … «Έργα αντιπυρικής προστασίας …
αρμοδιότητας των Δασαρχείων Αλεξανδρούπολης, Σουφλίου, Ξάνθης και
Σταυρούπολης, καθώς και της Διεύθυνσης Δασών Ροδόπης …», μέχρι τις
28.08.2025» — «so it does state the areas». The five services sit in the
quoted TITLE (every act repeats it, including those that then grant a
subset); the grant after the title names none. The machine's «area not
stated» is literally true, and the user's reading is the right one:
**an act that names no subset extends every area the title names.**
Decision (user-confirmed): on the strips such a step sits on every linked
service's strip (`buildLanes` flags it `all_areas`; hover says «all areas,
as the title names them»), the trail row says «· all areas (the act names
no subset)» on multi-area contracts, and the «area not stated» strip is
gone — only an area act naming a service the registry lacks still gets a
strip of its own («service not matched», none today). 79 acts on
multi-area contracts are affected; the 114 unsaid acts on single-area
contracts have only one area to extend. `scope` in the DB stays NULL —
the database records what the act says, the drawing applies the rule.

## 2026-08-21 · WHERE THE MONEY TRAVELS dressed like the allocation maps; thinner arrows, open heads, a cumulative year slider

User, the same evening: the flow frame should behave like ALLOCATION OF
FUNDING. So: the key is a strip ABOVE the map in the same `.mapkey` dress
(the «0% · bar · 100%» ramp at rest; the solid line / dashed line / ringed
dot entries when a unit is focused), MAP + ⓘ carry the instructions (the
region card stopped saying «click to see its flows»), a «✕ <unit> · all of
Greece» pill is the way out and Esc does the same, the place's card sits
grey at the top-left in EVERY state (`splitTips`), an arrow's card black at
the bottom-left — hover shows, click holds, ✕/Esc release (the ALLOCATION
maps' gesture, `FlowArcs` pins through `ctx.showTip`). The arrows
themselves: thinner (0.7–4 units by √€, was 1–8), the dash AND its gap
grow with the stroke (a fixed 8/5 pattern on a wide line read as a
misprint), and the arrowhead is an OPEN chevron at a fixed size, never a
solid triangle. The year control is a CUMULATIVE slider — the focused
flows signed up to and including the chosen year, summed per origin →
destination pair from `flows_yearly`, the right end being all years — not
a button per year (user: «I meant accumulative slider»). Same evening: the
bars list EVERY destination (59 units, a scroll box the map's height),
not the biggest twelve; their key is the same grey strip as the map's,
rounded swatches like the sponsored-works legends, the «unresolved base»
entry appears only if any € is unresolved (none today); the year slider is
black, never the warm ink. The focus linking and the even-split numbers
are untouched.

**The lightbulb** (user, same evening, ALLOCATION OF FUNDING): the
explanation that lived in a ⓘ beside the title is now behind an outline
lightbulb LEFT of the title (`ChartFrame insight`); clicking fills the
bulb and opens the text in the page's LEFT MARGIN beside the left map —
the maps keep their width (a first version shrank them; rejected) — as
wide as the margin allows (9–15 rem), and only below ~1500 CSS px does it
flow above the charts. A bug on the way: a non-existent `--sp-5` token
made the positioning rules invalid and the note sat over the toolbar.
WHERE THE MONEY TRAVELS took the same lightbulb (the user's own three
sentences, the computed «only N%» inside them; no subtitle left), the
list's focused key mirrors the map's key symbol for symbol (solid in,
dashed out, ring stays — the squares had read as the opposite), the
bars' palette was FLIPPED so dark = out-of-region as on the map's ramp
(the bars said the reverse), the black share leads each bar, the map
took the allocation maps' exact frame (640×620, two equal columns), the
«Destinations» heading went.

## 2026-08-21 · WHO REACHES WHERE becomes the «by company» lens of WHERE THE MONEY TRAVELS

Both frames answered one question at two grains — region → region on the
map, company → region in the bipartite lists — over the SAME even-split
flows. Decision (user, on my proposal): one frame, a SegmentToggle «by
region / by company» (`?flows=company`, like the allocation maps' view),
one lightbulb that explains both lenses (the computed reach fact — N links
across M contractors, the widest-reaching firm and its count — moved into
it), one caveat. The focus is SHARED: a unit focused on the map arrives
selected in the lists, a company selected in the lists focuses the map on
its home region when the lens flips back; the pill clears either. The
company lens wears the key strip and scrolls inside the map's height
(`Bipartite` gained a bindable `selected`; the standalone frame and its
`#bipartite` anchor are gone — nothing linked to it).
RANKING OF COMPANIES then moved to right after that frame and took the
same dress: the view explanation behind the lightbulb (both views' text,
the computed counts inside; no subtitle), the «as contracted / by member
firm» toggle alone on its own line under the title, left-aligned (a
labelled bar and a title-line placement were both tried and rejected),
caveat kept.

## 2026-08-21 · CONTRACT VALUES follows the ranking; no subtitle, the ΔΑΣΕ note, no single-bid rings, 380 px

User, same evening: the frame moves right after RANKING OF COMPANIES; its
subtitle goes; the dots' side note is the ΔΑΣΕ wording («Every contract is
one dot on a log scale (stated €, excl. VAT). Colours are assigned
according to the year the contract was signed. Hover to inspect, click
through to go to the contract’s page.»); the single-bid rings are NOT
drawn («we haven't worked on that info almost at all» — the data stays in
the payload); the canvas floor is 380 px with the dot radius grown in
proportion (2.6 → 3.1; `BeeswarmCanvas minHeight/radius`, ΔΑΣΕ keeps the
defaults) and the bracket view follows through `plotHeight`; the «most
common bracket» sentence leaves the chart's corner for the brackets' side
note, computed from the histogram payload; two ceiling labels closer than
48 px print on either side of their lines instead of over each other.

## 2026-08-21 · MONEY FLOW: the ΥΠΕΝ unit that signed → the contractors, two columns, no phase

Asked whether MONEY FLOW should follow the ΔΑΣΕ AWARDING PROCESS (body →
unit → contractor), the user dropped the programme phase as the middle
column («it does not say much about the awarding process») and asked for
a flow with NO middle column. The left column is therefore the ΥΠΕΝ unit
that signed the contract — the registry carries it for all 245 and it is
four units, not one: Γενική Διεύθυνση Δασών και Δασικού Περιβάλλοντος
(209 contracts), Γενική Γραμματεία Δασών (19), ΓΔ Ανάπτυξης και
Προστασίας Δασών και Αγροπεριβάλλοντος (11), Γραφείο Υφυπουργού (6) —
English names from `unit_names_en.json`; the right column the ten
biggest contractors (display names) and one pooled node. Drawn with the
ΔΑΣΕ `KindFlow` (ribbons in the unit's grey, headings, bars' hover card
with the contract count, contractor nodes linking to their pages), the
explanation behind the lightbulb with the computed «X of €Y ends at those
ten companies», no subtitle. `queries_extra.unit_flows` on
`/api/antinero/unit-flow`, even split across partners, both columns the
basis to the cent (pinned). The old ΥΠΕΝ → phase → contractor sankey
(`sankey_flows`, `/api/antinero/sankey`) stays served but nothing on the
site draws it. Same evening, on review: the plot is centred (equal
margins), colliding side labels give way equally — the upper node up,
the lower down, the NODE moving with its label and its ribbons following
(`KindFlow` relaxation, 34 px breath on the left, 8 on the right, never
above the plot's top) — and the fact that all four are the Ministry's is
said by a BRACE in the left margin («Ministry of Environment & Energy —
awarding body»; a Ministry node as a third column was tried and rejected
on 2026-08-22). **Vocabulary, checked against the registry fields and
the ΔΑΣΕ code**: `organization` = the awarding body (ν.4412's contracting
authority), `unitsOperator` = the operating unit — the same two fields
that build ΔΑΣΕ's first two columns; so the four are OPERATING UNITS and
the Ministry is the awarding body, and the heading says so (a first
«contracting authorities» heading on the units was wrong). Then, for
comparability with the co-op diagram, the user asked for THREE columns
after all: awarding body (the Ministry, one node) → operating units →
contractors — the middle labels wrap (`KindFlow wrapMid`) and the
relaxation now spaces the middle column's label-plus-node blocks too;
the brace stays a `KindFlow` feature, unused. The frame is renamed
AWARDING PROCESS on 2026-08-22 — the ΔΑΣΕ frame's own name, the two now
being the same diagram over the two datasets — and moved after CONTRACT
VALUES. Column placement became a prop the same day (`columnX`: each
column's centre as a fraction of the width or an absolute x, ribbons and
headings following), after «centre the middle column» and «the space
between the three columns is not well balanced»: the user set the
positions by hand on both pages. A note for the
next discussion: the user sees faults in how TYPES OF WORK is
represented.

## 2026-08-22 · TYPES OF WORK: the catch-all named for what it is, and the works the contracts name shown beside the categories

The user found the front-page chart «weird»: «Δασοτεχνικά έργα πρόληψης»
is a catch-all (154 of 245 contracts, €358M) and «the specifics of the
works we have checked and read are lost and mixed» in it. Cause: the
one-category-per-contract rule (chosen so the € bars sum to the total)
files every bundled title («καθαρισμοί, συντήρηση δασικού οδικού δικτύου
και αντιπυρικών ζωνών» — 101 of 155 titles name two or more works) under
one word. The specifics live in the THEMES layer (12 multi-label works
read from the same titles) and were shown only on the contract page.

Decision (user, wanting BOTH on the front page and the categories kept on
the contract page): ONE frame, two lenses on a toggle «main category /
works named» (`?works=`). «Main category» keeps the one-per-contract bars
(€ or count, summing to the total) with the bars' ENGLISH labels (the
payload now ships `label_en`; the bars had printed the Greek), the
catch-all renamed in English to what it is — «General fire-prevention
works — clearing, forest roads, firebreaks» (the Greek label in the
curated file is unchanged) — and under each bar the works its contracts
actually name, from the themes («names: forest road network 60 · clearing
54 · firebreaks 49 · …»), so the € stays honest and the specifics show.
«Works named» draws the themes counted in contracts — a contract under
every work its title names, so the bars overlap by design and carry NO €
(no price per work exists inside a bundled contract) — with the 91
contracts naming no specific work as their own bar («fire protection — no
specific work named»). `queries_extra.antinero_themes` + `names` on
`antinero_categories`, both on `/api/antinero/overview`, pinned (84 · 75 ·
59 · 37 · 17 · 15 · 14 · 13 · 7 · 6 · 2; 91 of 245 unspecified). The
contract page's TYPE chip already printed `label_en`, so it now says the
new name. Nothing in the curated verdicts changed.

**Drawing trials, open (2026-08-22 evening).** The bars' cross-lens facts
sit in each bar's HOVER (printed sub-lines were «too much text»). Beyond
the two bar lenses, six drawings of the same two layers are live on the
toggle for the user to choose from — nothing removed yet, the decision is
tomorrow's: **flow** (categories → works, KindFlow, counts — «the most
comprehensible», but it must not reuse MONEY FLOW's drawing), **works ×
category** and **works × category (squares)** (the works as ROWS — the
work names are long, which is what killed every column-headed drawing —
each row split by the main category of the contracts naming it, as a
stacked bar or one square per contract), **bundles** (an UpSet plot of the
29 combinations a title names: firebreaks + clearing + forest roads 33,
firebreaks + mixed zones 22 …; `antinero_themes.bundles`), **bubble
grid** and **matrix** (categories × works — «incomprehensible … looks like
matrix») and **pack** (every contract a circle, area ∝ €, one bubble per
category; the swarm rows carry `category` for it). The API gained
`themes.bundles` and `categories[].n_named`; `KindFlow` gained `fmt`.

**Verdict, same day (user).** Six further drawings were built and shown
side by side on the toggle — a two-column flow (categories → works), an
UpSet-style bundle plot, a bubble grid, a matrix, a `packSiblings` pack
and unit squares. The user kept **three lenses** and the frame was
renamed **TYPES OF WORKS**: «main category» (the € bars, one per
contract, summing to the basis), «works named» (the 12 themes, counted
in contracts, no €) and «works × category» (one row per work, each bar
split by the main category of the contracts naming it — the drawing
that says in one picture what the one-category rule flattens). The other
six components are DELETED, not parked: the finding that decided it is
that the work names are long sentences, so they can only be ROW labels —
every drawing that needed them as column heads (matrix, grid, flow,
bundles) was rejected for that reason, and repeating the experiment
costs more than rebuilding one file.

## 2026-08-22 · Context land on every map: the neighbours, and the Athos peninsula that no administrative layer carries

The user: every map draws Greece alone, «as if it were floating in water»,
and Chalkidiki has no third leg. The second is not a simplification bug —
**Άγιον Όρος is not a municipality**: it is a self-governed monastic state
outside the Kallikratis δήμοι, so it is absent from the geodata.gov.gr
layer our Π.Ε. are dissolved from, and (verified) from Eurostat's own
NUTS-3 «Chalkidiki», whose polygon likewise stops at lon 24.021.

Decision (user): draw one inert CONTEXT LAND layer under every map —
nameless, no data, no hover, no clicks — with **Athos as context land**
too (never merged into Π.Ε. Χαλκιδικής: no Anti-nero contract can be
there, and the merge would imply one could). Source, after weighing
Natural Earth against Eurostat: **Eurostat GISCO countries 1:1M** for the
neighbours (finer than Natural Earth's 1:10m, which matters because the
contract maps zoom; same family as the Greek NUTS file already in
data/raw; attribution «© EuroGeographics for the administrative
boundaries») and, for Athos, the **official «Άθως» polygon of the
Kallikratis layer** (geodata.gov.gr, CC-BY — the FireWatch copy in
`data/raw/firewatch_municipalities.geojson` carries it as feature 326 with
NO ΥΠΕΣ code, which is exactly why our municipality→Π.Ε. curation never saw
it) refined with the **OSM coastline**: the official outline is a 63-point
generalisation wandering up to 734 m from the shore, so the official
polygon gives the EXTENT (its 676 m land border at the neck makes the cut)
and OSM gives the SHAPE (user, 2026-08-22: «use the official polygon and
refine it so we can also attribute the source»). Three honest measurements
of the same peninsula sit within ±0.5 % — official as shipped 337.1,
published 335.6, ours 334.2 — and the OSM admin relation of the monastic
state (1 340 km², four times the peninsula: it includes the territorial
waters) is kept only as the sanity net that trims the mainland away before
the cut. `scripts/build_neighbours.py` clips to the frame, tucks the
land 400 m outward with a mitred buffer so it hides UNDER the Greek layer
(no sea sliver along a land border), simplifies in EPSG:3035 — 500 m for
the countries, 120 m for Athos, which is drawn beside Greek land on a
drilled map — drops islets under 4 km² and rounds to 4 decimals:
`atlas/static/geo/neighbours.geojson`, 92 KB, 9 features (the 8 land
shapes + the border line).
`PaperMap` draws it first (under the relief image and the Π.Ε.), with a
`context={false}` escape for any map that must show Greece alone. Tones,
settled over three user rounds the same day: a grey context land
(#dcdcdc) was tried first and REJECTED — the Anti-nero maps are a grey
ramp, so a grey country reads as a data value — and the context land is
**white with a #c4c4c4 coastline** on the #f2f2f2 sea, Athos white too
(Greek coastline stroke, `--line`); what says where Greece ends is a
**dashed black land border** (`.gr-border`, `--ink`, 0.9 @ 4-3 dashes),
drawn ABOVE the region fills. That line is cut from OUR OWN Π.Ε. outline
— the part of the dissolved coarse layer's boundary that runs along a
neighbour rather than along the sea; the GISCO countries (buffered 1 km)
only say WHICH stretch, so the dashes hug the drawn polygons exactly.
Measured 1 189 km against Greece's ~1 180 km of land borders; the build
guards 900–1 500. The Chalkidiki drill frame takes Athos in as well
(framing only, never data), since the administrative unit stops at the
neck. Same evening, map chrome to match: pan/zoom is CLAMPED to the
fitted frame (`translateExtent` was ±25% — panning could expose the
context layer's clip box), every map frame carries a **1px `--line`
hairline** (the pages' `border: none` overrides were the reason a frame
never showed; the tone matched to the zoom buttons' old outline after
`--ink` and `--ink-soft` both read too dark), and the +/−/⌂ zoom
buttons are **solid circles in the section's hue** (user mock:
`--map-accent` set per section — Anti-nero black, ΔΑΣΕ #52b788,
sponsored #2d6a4f — white inline-SVG glyphs centred by construction,
1.45rem; the text glyphs sat on font metrics and never centred). The
sources are named in /methodology#map-layers.

## 2026-08-22 · The works-named vocabulary corrected: three firebreak kinds, honest roads, real studies, residues apart

**Decision (user, after reviewing the label-review page):** the themes
layer conflated different works, and the vocabulary is revised. Verdicts:
(1a) «διαχείριση υπολειμμάτων υλοτομίας» becomes its own theme; (2) the
«ΜΕ ΕΓΚΕΚΡΙΜΕΝΕΣ ΜΕΛΕΤΕΣ» contracts leave the studies theme — the study
is the input the works follow, not work bought; (3) the 0-link
«Περιφράξεις & σήμανση» theme is dropped (its CPV marker 45342000-6 with
it); (4) the roads theme is renamed «Συντήρηση δασικού οδικού δικτύου» /
"Maintenance of forest road network" — συντήρηση and βελτίωση are close,
the one βελτίωση contract stays inside; and firebreaks split into THREE
disjoint themes — δημιουργία μικτών / δημιουργία εστεγασμένων / συντήρηση
αντιπυρικών ζωνών — the generic «Αντιπυρικές ζώνες» theme retiring.

**Evidence (all measured on the DB before the change):**
- The needle `ΑΝΤΙΠΥΡΙΚ\w*\s+ΖΩΝ` fired on every mention regardless of
  verb: of 84 links, 46 συντήρηση, 32 δημιουργία μικτών, 4 δημιουργία
  εστεγασμένων, 2 hand-read. ALL 37 μικτές/εστεγασμένες contracts also
  carried the generic theme — the same clause counted twice. No title
  names two firebreak kinds (23SYMV013156825's «συντήρηση» governs the
  road network, checked), so the three new themes are disjoint.
- Roads: 15 of 75 links were LOCATION, not work — «δημιουργία μικτών
  ζωνών ΣΕ δασικούς δρόμους» (14) and «καθαρισμός ΚΑΤΑ ΜΗΚΟΣ κεντρικών
  δασικών δρόμων» (1). Of the true 60: 59 συντήρηση, 1 βελτίωση
  (25SYMV016392306).
- Studies were wrong both ways: 6 of 14 were «…ζωνών ΜΕ ΕΓΚΕΚΡΙΜΕΝΕΣ
  ΜΕΛΕΤΕΣ» false positives, and 6 real study contracts were missed —
  «Κατάρτιση Σχεδίου Αντιπυρικής Προστασίας» ×6 (the stem ΣΧΕΔΙΑΣΜ never
  matches ΣΧΕΔΙΟΥ). Separately 99 in-scope contracts state a ΣΑΥ-ΦΑΥ
  μελέτη cost — the theme means «the title names drafting a μελέτη/Σχέδιο
  as work», never «the contract involves a study».
- Υλοτομίες: 4 of 7 were «διαχείριση/χειρισμός υπολειμμάτων υλοτομίας» —
  the genitive names where the debris came from, not the work.

**Hand-read verdicts:** 24SYMV014192289 «Πιλοτικό Πρόγραμμα Δημιουργίας
Μικτής Αντιπυρικής Ζώνης στην Π.Ε. Ηλείας» → μικτές. 23SYMV013201961
«πλευρικός καθαρισμός των υπό διαμόρφωση αντιπυρικών ζωνών κατά μήκος
κεντρικών δασικών δρόμων» → συντήρηση αντιπυρικών ζωνών (side-clearing
keeps the zone functional; the roads are the location — no road theme).
25SYMV016392306 «βελτίωσης δασικού οδικού δικτύου» → roads.

**New vocabulary (13 themes; was 12):** katharismoi · odiko_diktyo
(relabelled maintenance) · syntirisi_zonon (NEW) · miktes_zones
(narrowed) · estegasmenes_zones (NEW) · ypoleimmata (NEW) · ylotomies
(narrowed) · dasokomika · nero · anadasoseis · antidiavrotika · meletes
(fixed both ways) · arxaiologikoi. Needle technique: tempered patterns
(`ΣΥΝΤΗΡΗΣ(?:(?!ΔΗΜΙΟΥΡΓ).){0,120}?ΑΝΤΙΠΥΡΙΚ\w*\s+ΖΩΝ`) and fixed-width
lookbehinds (`(?<!ΕΓΚΕΚΡΙΜΕΝΕΣ )ΜΕΛΕΤ`, `(?<!ΥΠΟΛΕΙΜΜΑΤΩΝ )ΥΛΟΤΟΜ`).
Curation path unchanged: extract_contract_details.py
proposals → _overrides → details_loader.

**Measured after the re-extraction (loaded, pinned in
`test_atlas_real_db.test_types_of_work_lenses` and 5 new unit cases in
`test_contract_details.py`):** 277 links / 158 named / 87 name nothing
(was 330 / 154 / 91 — +6 Σχέδια gained a theme, the two «Έργα
αντιπυρικής προστασίας ΣΕ δημόσιους δασικούς δρόμους» contracts
(25SYMV016959652, 25SYMV017153341) honestly lost their only theme: the
roads were the location). odiko_diktyo 60 · katharismoi 59 ·
syntirisi_zonon 47 (46 needle + the 23SYMV013201961 override) ·
miktes_zones 33 · arxaiologikoi 17 · anadasoseis 15 · meletes 14 ·
antidiavrotika 13 · dasokomika 6 · ypoleimmata 4 · estegasmenes_zones 4 ·
ylotomies 3 · nero 2. The three firebreak themes share NO contract
(SQL-pinned). The durations file lost its one stale entry
(25SYMV016659302, the registry-cancelled record out of scope since
2026-08-19) → 245.

## 2026-08-22 · Where the title is silent, the πρόσκληση's works enumeration speaks: a second, labelled evidence tier for the works-named layer

**Decision (user, same day as the vocabulary correction):** for the 87
in-scope contracts whose descriptive title names no specific work, the
work themes may be read from the CALL's lot-specific works enumeration —
the «Συνοπτική περιγραφή αντικειμένου» sentence of the πρόσκληση («Οι ως
άνω εργασίες αφορούν σε: i) … ii) …», itemised per Δασαρχείο) — stored
with `source = call:<PROC ΑΔΑΜ>` and the verbatim sentence, and labelled
apart on every surface. The user found it on 25SYMV016959652: the signed
contract is pure boilerplate (καθαρισμός/βλάστηση never occur in it),
while its call 25PROC016718138 states «καθαρισμούς δασικής βλάστησης»
with per-Δασαρχείο στρέμματα.

**This NARROWS, not reverses, the 2026-08-19 rejection of the πρόσκληση
as evidence.** What was rejected — and stays rejected — is the call's
programme MENU (4–10 themes per call, the whole shopping list). What is
admitted is only the lot-specific enumeration, only where the title says
nothing, and for multi-lot calls only the items naming the contract's own
Δασαρχεία (the enumeration is itemised per service, and the forest layer
says which services are the contract's). A call that carries only the
menu leaves its contract honestly empty.

**Feasibility, measured before building:** of the 87 title-silent
contracts, 86 cite a πρόσκληση and 85 of those call texts are already
cached; 39 sit on a single-lot call (the description IS the contract's
work), 47 on multi-lot calls (40 of them two-lot); 51 calls carry the
standard «οι εργασίες αφορούν σε» anchor. Proposals from
`scripts/extract_call_themes.py`; every proposal read (Claude), the
flagged ones decided by the user; verdicts live in
`contract_work_themes.json` `_overrides` (which survives regeneration by
design — NOTE: the loader does not read `_overrides`; they merge into the
top-level entries when `extract_contract_details.py --curate` regenerates
the file, so that step must run after editing them).

**Measured and loaded:** 41 call-derived entries → the layer is now
**370 links / 199 named (158 title + 41 call) / 46 honestly unnamed**
(was 87). Per theme: katharismoi 100 · odiko_diktyo 83 · syntirisi_zonon
54 · miktes_zones 35 · arxaiologikoi 17 · anadasoseis 15 · meletes 14 ·
nero 13 · antidiavrotika 13 · estegasmenes_zones 9 · dasokomika 8 ·
ylotomies 5 · ypoleimmata 4. The call dialect needed its own patterns
(`work_themes.CALL_PATTERNS` + `read_call`): «αποκατάσταση βατότητας» is
road work titles never say, the calls write «στεγασμένων» without the Ε-,
«καθαρισμός αντιπυρικών ζωνών» is zone maintenance (the 23SYMV013201961
verdict as a rule), and «καθαρισμός δασικής βλάστησης» must not fire the
silvicultural theme. Hand corrections on the read: one CPV-list bleed
(25SYMV016398005, the kept window ran into «Υπηρεσίες σχετιζόμενες με την
υλοτομία»), two «…και αντιπυρικών ζωνών» clauses the ΒΛΑΣΤΗΣ guard
blocked (25SYMV016570021, 25SYMV016737061), the ΕΣΑ ΥΠΟΕΡΓΟ Α study
title read by hand (23SYMV012946440 → καθαρισμοί + κλαδεύσεις — NOT the
studies theme: the study is approved input), the two-lot 2023 collective
clause naming one work accepted for both lots (23SYMV013530639/680 →
καθαρισμοί), and the Τμήμα Α Χίου lot resolved by hand (25SYMV016991804 —
the toponym stem was too short to match). **Title-sourced firebreak
themes stay disjoint; 4 call enumerations honestly name two firebreak
kinds** (συντήρηση ψιλών + δημιουργία στεγασμένων) — the pin narrows to
title-sourced rows. The 43 contracts whose 2024-generation calls delegate
the works to the unpublished «Τεύχος 3 — Τεχνική Περιγραφή» stay honestly
empty, as do the txt-missing and no-call ones. **Both held questions answered by the user the same day:**
(a) 23SYMV013039380 — the 5-lot call embeds each lot's own Τεχνική
Περιγραφή, and the user pointed at §3.2.9, the Ρεθύμνου lot's: «εργασίες
καθαρισμών δασικών εκτάσεων, την δημιουργία στεγασμένων αντιπυρικών
ζωνών – καθαρισμούς κατά μήκος δασικών δρόμων, βελτίωση βατότητας των
δασικών δρόμων» → καθαρισμοί + εστεγασμένες + οδικό. (b) the plain-zone
creations get a FOURTH firebreak theme, **psiles_zones «Δημιουργία ψιλών
αντιπυρικών ζωνών» / "Creation of bare firebreaks"** (pattern
ΔΗΜΙΟΥΡΓ|ΔΙΑΝΟΙΞ tempered against ΜΙΚΤ/ΣΤΕΓΑΣΜΕΝ; ΔΙΑΜΟΡΦΩΣ deliberately
NOT a creation verb — «υπό διαμόρφωση ζωνών» stays the hand-verdict
maintenance case). It landed on 4 contracts: the three call-derived ones
AND one TITLE — 24SYMV014809263 «…συντήρησης και διάνοιξης δασικού
οδικού δικτύου και αντιπυρικών ζωνών…», the one title naming two
firebreak kinds legitimately (maintenance + opening), so the
disjointness claim stays exact for the original trio. **Final layer: 14
themes, 380 links / 201 named (158 title + 43 call) / 44 honestly
unnamed.** katharismoi 102 · odiko_diktyo 85 · syntirisi_zonon 55 ·
miktes_zones 35 · arxaiologikoi 17 · anadasoseis 15 · meletes 14 ·
antidiavrotika 13 · nero 13 · estegasmenes_zones 10 · dasokomika 8 ·
ylotomies 5 · psiles_zones 4 · ypoleimmata 4.

**The last sweep of the unnamed (user questions, same day):**
26SYMV018977660's call 25PROC016230587 was missing from the cache — it
was FETCHED (472 KB, tracked txt) and its single-lot enumeration names
συντήρηση-βελτίωση οδικού 4.150,30 στρ. + καθαρισμοί βλάστησης 1.709,51
στρ. + συντήρηση-διαμόρφωση αντιπυρικής ζώνης 216,00 στρ. → all three
recorded. 23SYMV012972469 (Πάρνηθας) cites its call only by DATE («η από
22.5.2023 Πρόσκληση» — no ΑΔΑΜ, which is why the families layer has no
row): its Ορισμοί prove it is Υποέργο Β of the call whose title names
καθαρισμοί δασών/αρχαιολογικών + δημιουργία εστεγασμένων ζωνών over four
services (the sibling Υποέργο Α, 23SYMV012963827, carries that full title
as its own and is themed accordingly), but the lot's own Τεχνική
Περιγραφή is Παράρτημα VII of the unpublished call and the contract is
design-build («Μελέτη: … που θα εκπονηθεί από τον Ανάδοχο») — three
works over four services is not attributable to the Πάρνηθας lot, so it
stays honestly empty. **The «εκπόνηση μελετών» design-build clause is NOT
the 43's peculiarity:** 72 of the 135 cached calls carry it — 101
in-scope contracts (47×2024, 30×2025, 24×2026), of which 80 already have
themes from their title or their call's enumeration, and 51 repeat the
clause in their own contract text. Recording «μελέτες» on it would flood
the studies theme (14 → ~115) with every design-build job that drafts
its own study — the theme stays reserved for contracts whose OBJECT is a
study/plan, and the design-build structure is a fact about the
procurement model, not a named work.

## 2026-08-22 · The deliverables split (study / works / study and works) and the nine calls that exist only as a date

**Deliverables (user):** the contract page's SCOPE row said «study» for
the 14 μελέτες contracts and «works» for everything else — the user asked
for the real 1-2-3 model, mirroring the sponsored-works `deliverables`
curation: (1) **study** — the object is drafting μελέτες/Σχέδια (the 14
category-meletes contracts); (2) **study and works** — the design-build
generation, whose own text or call states the contractor first drafts
the studies and then executes what they define; (3) **works** — neither.
Measured over the 245: **study 14 · study_and_works 121 · works 110**
(evidence: 63 in the contract's own text, 58 in its call only, every
clause quoted verbatim). This was chosen over folding the clause into
the «Μελέτες» work theme, which it would have flooded 14 → ~115: the
design-build structure is the post-2024 procurement TEMPLATE (72 of 135
cached calls), a fact about the mode, not a named work — the works-named
layer stays physical, the deliverables layer says the mode. Generated by
`scripts/extract_deliverables.py` (deterministic, `_overrides` per ΑΔΑΜ,
1:1 fold so excerpts stay verbatim) → curated
`khmdhs/data/contract_deliverables.json` → `details_loader` →
`contract_deliverables`; the SCOPE row now prints the three-way kind
with the clause in the extracts, `/api/antinero/overview` ships the
counts, pinned.

**The nine date-only calls (user: «I do want to acknowledge this»):**
nine in-scope contracts cite their πρόσκληση by DATE ONLY — «η από
04.3.2022 / 23.03.2022 / 21.04.2023 / 22.5.2023 Πρόσκληση» — with no
ΑΔΑΜ anywhere in the signed text, so neither the registry chain nor the
families ΑΔΑΜ-scan can link them (5 of 2022, 4 of 2023; they surfaced
when the user asked why 23SYMV012963827/23SYMV012972469 show no call in
their trail). All nine are **ΤΑΙΠΕΔ-run procurements** — their recitals
cite ΤΑΙΠΕΔ board approvals, quoted per contract — and ΤΑΙΠΕΔ published
its tenders through its own channels, so the calls most likely never
received a ΚΗΜΔΗΣ record; nothing resembling them exists among the 147
stored upstream acts, and without an ΑΔΑΜ the registry cannot be asked.
Curated `khmdhs/data/undocumented_calls.json` (call date ISO, the
verbatim citation, the ΤΑΙΠΕΔ recital excerpt); `contract_timeline`
merges an UNLINKED row per contract — kind notice, no ΑΔΑΜ, title
«cited in the contract by date only — ΤΑΙΠΕΔ-run procurement; no ΚΗΜΔΗΣ
record exists to link», the «cited in this contract» chip — and the
run-up call diamond draws at the cited date with «(no ΚΗΜΔΗΣ record)»
on hover. The claim is made ONLY for these nine, each carrying its own
evidence.

## 2026-08-22 · One scope vocabulary across the datasets, and the CONTRACT SCOPE frame

**Decision (user, approving proposals A and B of the type/scope
comparison; C — the ΔΑΣΕ «Type» row — deliberately untouched, D pending):**
the scope trio prints with ONE wording on every surface of both datasets —
**«study only» / «study & works» / «works only»** (it was "execution of
works / study & works / study" on the sponsored project page, "works /
study and works / study" on the Anti-nero contract page, and the sponsored
chart's wording, which won). Both Scope rows carry a ⓘ naming their
evidence: the sponsored one the operative «Ορίζουμε … με σκοπό …»
sentence, the Anti-nero one the design-build clause. The Anti-nero front
page gains **CONTRACT SCOPE** — the sponsored PROJECT SCOPE frame's
StackedShareBar in the same greyscale ramp (14 / 121 / 110 from
`o.deliverables`, computed subtitle, the design-build finding), anchor
`#scope` — so TYPE says what the work is and SCOPE says what the
contractor was engaged to deliver, on both datasets, comparably. **Layout
(user, same day):** the pairs mirror each other — sponsored PROJECT SCOPE
| PROJECT TYPE side by side at equal halves (they were stacked), and
Anti-nero CONTRACT SCOPE | **CONTRACT TYPE** side by side (the curated
category € bars, pulled out of TYPES OF WORKS into their own half-width
frame, keeping the `#categories` anchor); TYPES OF WORKS keeps the
works-named chart (now the default lens, full width) and works × category
(`?works=named|split`). BarH's value reserve widened 60→78 px so
«357,59 M €» fits beside a full-width bar at half-page width. Round 2
(user, same day): the sponsored PROJECT TYPE became the same BarH drawing
as CONTRACT TYPE (counts, biggest first — the share bar kept only for the
two SCOPE frames); CONTRACT TYPE gained a «stated net € / number of
contracts» toggle (`?ct=eur|n`, sort follows the shown measure); the
scope bars sit at 34 px beside the 30 px BarH rows, align with their
titles (StackedShareBar gained the `edge-l` clamp so a tiny first
segment's label pins to the left edge instead of overflowing), and inside
the half-width pair the lightbulb note flows ABOVE the chart (the page's
left margin is the neighbouring frame); CONTRACT SCOPE's finding moved
from subtitle to bulb. Round 3 (user, same day): **ONE uniform gap
site-wide between a frame's head and its chart** — ChartFrame's
figcaption carries a single sp-4 margin and the per-element margins
(title, subtitle, toolbar row) are zero, so every frame measures the
same 16 px (verified across the whole front page); the pair charts
share BarH's corners (StackedShareBar radius 10→2) and lettering
(inside fs-12 / spill fs-13, the page face — the fit rule measures in
the same letters); the sponsored SCOPE/TYPE pair wears the page's green
and transparencies of it (#2d6a4f · 0.62 · 0.30, the palest segment's
label in full-green ink via the new `labelColor`), PROJECT TYPE's bars
the same green; both pairs' chart tops align (the share bar's badge
headroom removed inside the pair). Rounds 4–5 (user, same day): bars at
35 px, two-line names; CONTRACT TYPE and PROJECT TYPE values
right-aligned table-style (`BarH valuesRight`); the two long category
names shortened with an ⓘ carrying the trimmed tail (`BarH` rows take
`hint`; rule: the text after a «:» or a trailing parenthetical — so
«special forestry works» ⓘ and «reforestation and forest nurseries» ⓘ);
StackedShareBar REWRITTEN to its final scope-bar form — plain numbers
always visible above each segment (the hover pills are gone), every
label on one line under the bar at its segment, edge labels pinned
inside the frame — and the scope bar's top meets the SECOND type bar
(the number line takes the first row's 41 px). The two type taxonomies stay their own (3-value
sponsored, 8-category Anti-nero): the programmes buy different things and
one vocabulary would be false comparability — SCOPE is the shared layer.

## 2026-08-22 · «FLOWS OF MONEY», and the front page reordered

The flow frame is renamed «FLOWS OF MONEY» (was «WHERE THE MONEY
TRAVELS»; anchor `#flows` unchanged) and the Anti-nero front page reads
in the user's order: ALLOCATION OF FUNDING · FLOWS OF MONEY · AWARDING
PROCESS · DIRECT AWARDS + AWARD PROCEDURES · RANKING OF COMPANIES ·
CONTRACT VALUES · CONTRACT SCOPE + CONTRACT TYPE · then the remainder
unchanged (programme chart, payments timeline, cumulative disbursement,
money by region per year, study costs, TYPES OF WORKS, CPV codes). The
SCOPE+TYPE pair was split out of the categories block so it could move
up while TYPES OF WORKS stays with the tail; every anchor and permalink
is untouched.

## 2026-08-22 · MONEY PER YEAR beside a year-vs-year-only CUMULATIVE DISBURSEMENT

(user) CUMULATIVE DISBURSEMENT keeps ONLY the year-vs-year mode — the
stacked-by-phase view and its mode buttons are deleted from
`DisbursementCurves` — and moves after CONTRACT SCOPE + CONTRACT TYPE at
half width, its fire-season band now wearing the payments timeline's
colour (`var(--accent)` at 0.06 with the accent label, exactly
StripTimeline's band). On its left, the new **MONEY PER YEAR** frame:
one bar per signature year with a «€ contracted / € paid» toggle
(`?money=`) — € contracted is the stated net of the in-scope contracts
signed that year, aggregated client-side from the swarm list so the
years sum to the basis by construction (30,88 + 71,47 + 248,40 + 193,57
+ 78,20 = €622,53M); € paid is `antinero_yearly`'s per-year payment
orders, and its five values equal the cumulative chart's year-end labels
to the cent — the two charts cross-validate on screen. The y-axis left
margin widened 52→84 so «150,00 M €» ticks stop clipping.

## 2026-08-22 · The years as a film strip of maps inside ALLOCATION OF FUNDING

(user, choosing the geographic question over the per-region trend) The
MONEY BY REGION PER YEAR facets frame is RETIRED (`SmallMultiples.svelte`
deleted) and its data now draws as **five mini choropleths — 2022–2026 —
inside the ALLOCATION OF FUNDING frame**, under the two big maps: one
`PaperMap interactive={false}` per year (the /connections hub-catchment
precedent), on ONE shared sqrt grey ramp (`makeChoro(RAMP_WORKS, max)`
over every year-region value), each head carrying the year and its total.
Small multiples over a year slider, per the doctrine: a slider would show
one year at a time and force the ramp to either rescale per year
(colours no longer comparable) or wash out the small years. The strip
keeps the old `#pe-yearly` anchor; its five totals equal MONEY PER
YEAR's contracted bars (30,88 / 71,47 / 248,40 / 193,57 / 78,20 M €) —
the two surfaces cross-validate. A note under the strip states the
shared scale and the even-split signature-year basis.

## 2026-08-22 · The phases leave the front page: scope colours the programme chart, cohorts colour the payments, the lag medians said

**Premise (user): «Anti-nero I/II/III/IV/2026 do not say much»** — they
are funding-envelope labels, and in the timeline arrangement they are
doubly redundant: phases ARE eras and the x-axis already carries time.
The page had been de-phasing already (year-greys on the beeswarm, the
phase-stacked cumulative deleted); this round finishes it.

- **Programme chart:** colour = the SCOPE kind (works only #3d3d3d /
  study & works #6c6c6c / study only #b5b5b5 — CONTRACT SCOPE's own
  tones, one meaning site-wide; `dk` on the network payload). The nine
  ΤΑΙΠΕΔ date-only calls now GROUP their lots (pseudo-id `date:<iso>`,
  dotted ties, «call known by date only (ΤΑΙΠΕΔ) — no ΚΗΜΔΗΣ record» in
  the key, labels print «πρόσκληση DD.MM.YYYY»): split calls 51→54,
  same-day 35→37, no-call 26→17, n_calls 138 (134 ΚΗΜΔΗΣ + 4 date; the
  meta/methodology numbers stay ΚΗΜΔΗΣ-only, the pin relates them).
  Fire-season stripe now the page's accent band (was #f0e5d8); toggle on
  the title line; the explanation behind the bulb.
- **Payments timeline REWRITTEN:** the phase lanes are gone — one strip,
  each tick in the grey of its CONTRACT'S SIGNATURE YEAR (the CONTRACT
  VALUES year-greys), which makes the payment TAILS visible: 2022-grey
  ticks stretch deep into 2024. The payload ships each contract's cohort
  (`contracts[ref].y`) and the LAG medians computed server-side: median
  247 days from signature to a payment order, 170 days to the first
  payment, over 226 contracts / 863 dated pairs — pinned. The bulb says
  it. The strip's season band fixed May–Aug → the statutory May–Oct.
- **Study costs:** the bulb now tells the truth the deliverables layer
  measured — and the first draft had it BACKWARDS, caught by verifying
  before shipping: of the 99 contracts stating a μελέτη cost, **96 are
  design-build** (the ΣΑΥ-ΦΑΥ line is exactly their itemised fee for the
  studies the contractor drafts) and 3 works-only; the other 25
  design-build contracts bundle the fee unstated; the 110 works-only
  contracts draft no study (theirs pre-existed — «με εγκεκριμένες
  μελέτες») and honestly state none; the 14 study-only contracts are
  study money entirely. The stale «ΕΣΑ design-build» caveat replaced;
  bars restyled to the page's 35px/inside/right-values language, the
  share % on hover.

## 2026-08-22 · Round 2 on the three frames: legible scope colours, cohort lanes, the study scatter

(user: the scope greys were indistinguishable, the cohort tick-greys
illegible, the top-10 unreadable) —
- **Programme chart**: retitled «HOW THE PROGRAMME WAS BOUGHT» (the
  computed findings moved into the lede/bulb); the scope trio stretched
  for 6-px dots — works only near-black #1d1d1d, study & works light
  #a8a8a8, study only WHITE with a dark ring — and a fill bug fixed
  along the way (the marks read `phase`, which still held the funding
  phase, so every dot fell back to one grey; the page now hands `dk`
  in the phase slot). The 2022-all-black → 2024-mostly-light flip now
  reads at a glance (measured: 2022 = 20/20 works-only; design-build
  arrives 2023 at 20 vs 28 and dominates 2024–26).
- **Payments timeline, round 2**: LANES BY SIGNATURE COHORT — «signed
  2022…2026», one ink, each lane's Σ € printed (29,52 / 66,53 / 207,55 /
  122,67 / 13,75 M € — the €440M paid basis decomposed); the tail is the
  lane's horizontal reach, not a colour to decode. The «credit (negative)
  order» key REMOVED: zero credit orders exist in the whole payments
  table — the key documented a registry possibility, not our data.
- **Study costs**: the top-10 Greek-title bars replaced by (a) a
  four-segment share bar over the 245 — fee itemised 105 / design-build
  fee unstated 20 / works-only, no study to draft 106 / the study itself
  14 (chain-attributed, matching `n_with`; the raw-table split was
  96+3 before tip inheritance) — and (b) a log–log SCATTER of every
  stated fee against its contract's value with fixed-share diagonals and
  the median (1,1%) drawn solid: the «what studies cost» claim is now
  the picture, no labels needed. `o.studies` ships `points` + `classes`,
  pinned.

## 2026-08-22 · The programme chart's toggle becomes the two lenses; «nested by call» parked

(user) The «Nested by call» pack arrangement is PARKED — like the star
field before it, its scene and tests stay (`networkScene` still builds
and pins it) and only `NET_MODES` decides what shows. The toggle now
switches the COLOUR of the one timeline: **«By contract scope»**
(works-only black / design-build light / study-only white-ring) and
**«By contract type»** — the 8 curated categories in the SITE'S OWN
colours, semantic where possible: the catch-all special forestry works
as the grey mass, mixed firebreaks black, reforestation #52b788,
logging #2d6a4f, flood protection the ΔΑΣΕ deep blue #0d366b,
archaeological the accent #b33a1a, studies amber #b07d1e, water #43a276.
The type lens shows the CAMPAIGNS: 2022–23 all grey, then the 2024
mixed-firebreak black column, the green reforestation waves, the blue
flood works after the 2023 Έβρος fires. The key wears the MAP legend's
dress (the grey rounded `.mapkey` panel), so the page's keys read as one
family. Title provisionally «PROCUREMENT TIMELINE» pending the user's
pick.

## 2026-08-22 · PROCUREMENT TIMELINE: the title kept, same-day runs made rigid, the HRADF marker on the dots

(user) The frame keeps the title **PROCUREMENT TIMELINE**. Reading fixes,
all presentation — no data change:
- **Same-day lots of one call are a RIGID touching run**: dodged one by
  one they interleaved with strangers and the join line zig-zagged
  illegibly across the swarm. `beeswarm.dodgeChains` places each
  same-(call, date) group as one vertical run of touching circles and
  dodges the run as a unit (a single circle is a chain of one);
  adjacency now IS the join for same-day lots, the line only shows where
  a call's lots span days. Unit-pinned (touching distances exact, no
  stranger overlap, determinism kept).
- **Year labels centred in their year**: a label on the January-1st rule
  reads as belonging to either side; each year's label now sits at the
  midpoint of the stretch of that year the domain shows (`ticks[].lx`),
  the boundary rules unchanged.
- **The date-only call marker moved onto the DOTS**: the touching runs
  cover the tie line, so the nine contracts wear a dashed ring
  (grey on light fills, light on dark) and the key shows a dashed
  circle; the tie itself stays dashed for the spanning case. And the
  wording is **HRADF** wherever English is spoken — the key and the
  DOCUMENT TRAIL row («HRADF-run procurement») — per the site's
  ΤΑΙΠΕΔ→HRADF naming convention.
- The two JOIN swatches in the key are line samples now, not 12px boxes
  with a coloured top border nobody could see.

## 2026-08-22 · Timeline corrections + TYPES OF WORKS grouped dots (user round)

Corrections to the previous entry, both user-caught:
- **The chain window is ≤7 days, with per-member x** — 23PROC012860295
  signed four lots on 07.07.2023 and ONE on 06.07: an exact same-day rule
  exiled the fifth to its own dodge, a long line away (the user saw it).
  `dodgeChains` now takes per-member x and the members touch given their
  horizontal gap, so a day-apart lot joins the run on a slant at its true
  date. Verified in the DOM: all five lots consecutive at distance ==
  radius sum.
- **Year labels ON the 1st of January** (user: «obviously») — not centred
  in the year as the previous pass did. The axis now STARTS on 1 January
  of the first year, so every year owns a real rule and its label sits on
  it, anchored middle.

**TYPES OF WORKS gains a third lens, the new default: «by main
category»** — the Flourish «Company ownership» form the user picked from
the gallery: ONE EQUAL dot per contract (245), clustered by its curated
category in phyllotaxis discs, bottom-aligned, count + name under each,
CAT_COLORS shared with the PROCUREMENT TIMELINE's type lens
(`charts/catColors.ts` — one colour per category across the page). Dots
equal on purpose: this face counts contracts, the € stands in CONTRACT
TYPE. Cluster counts verified against the DB — dasotexnika 154 /
miktes_zones 33 / arxaiologikoi 16 / meletes 14 / antidiavrotika 13 /
anadasoseis 8 / ylotomies 6 / ydatodexamenes 1 (CLAUDE.md's 2026-08-14
table said 17/12 — stale, corrected).

## 2026-08-22 · TYPES OF WORKS: the dots regroup by the WORKS, coloured by category

(user round) The grouped-dots diagram was meant for the WORKS NAMED, not
the categories — and the user asked for an interactive form CONNECTING
the 8 categories to the works. One diagram does both
(`WorkDots.svelte`, replacing BOTH the day-old «by main category» lens
and the works-named bars; `CategoryDots.svelte` deleted):
- one equal dot per contract under EVERY work its signed title (or call)
  names — 14 work clusters sorted by count, «no specific work named»
  (44) always last, phyllotaxis discs greedy-wrapped into rows,
  count + name under each;
- each dot COLOURED by its contract's curated main category
  (`catColors.ts`, the palette the PROCUREMENT TIMELINE type lens uses)
  — the colour composition of a cluster IS the category↔work bridge
  (mixed-firebreak creation solid black, clearing/roads/firebreak
  maintenance near-pure grey, the reforestation cluster visibly split
  between the reforestation and logging categories);
- interactive both ways: hovering a dot lights the SAME contract in
  every cluster it appears in (card: ΑΔΑΜ · category · names N works ·
  €, click → contract page); hovering a category chip in the key (MAP
  legend dress) lights that category across all clusters.
The network payload's nodes now carry `wk` (the work themes each
contract names) — 380 links / 44 empty pinned in the real-DB network
test. The lens toggle is back to «works named» (default, the dots) /
«works × category» (the rows stay as the accessible view).
Also: the fire-season count the deleted lede carried — «120 of 245
signed inside a fire season» — now lives in the frame's lightbulb,
computed (`network.fire_season.n_contracts` of `stats.n_contracts`).

## 2026-08-23 · TYPES OF WORKS: chord and sunburst offered as trial lenses

(user: «try this connection with a chord diagram and then a sunburst»)
Two more lenses on the same category↔works data, beside the dots and
the rows (`?works=chord|sunburst`, pending the user's verdict):
- **Chord** (`CatWorkChord.svelte`, d3-chord, bipartite on a symmetric
  matrix from the same per-category `names` counts the rows use): the
  8 categories hold one half of the circle, the works the other, a
  ribbon per (category, work) as wide as the contracts of that category
  naming that work, in the category's colour. A category's arc is its
  contract–WORK MENTIONS, not its contracts (a contract naming three
  works lies under three ribbons) — said in the bulb. Rotated a quarter
  turn so the run of tiny work arcs lands on the right equator (340 px
  of radial-label room) instead of the pole (110 px); labels truncate
  per angle to what the frame holds, full text on hover.
- **Sunburst** (`CatWorkSunburst.svelte`, hand-rolled partition): inner
  ring = categories sized by CONTRACTS, outer = the works each names in
  tints of the category colour; a contract naming k works gives 1/k of
  its arc to each (the site's even-split convention), so the inner ring
  sums to 245 exactly and the geometry never double counts — the hover
  card prints whole-contract counts. Labels ride arcs long enough to
  hold them (bottom-half text paths reversed to stay upright).

## 2026-08-23 · Sunburst dropped; the chord redrawn so the two flaggings read apart

(user) The sunburst «is not helping understand» — deleted
(`CatWorkSunburst.svelte` removed, lens gone). The chord stays as a
trial but had mixed its two sides into one look: a reader could not
tell that every contract is flagged TWICE — one main category, several
works named. Redrawn so the halves are two different things: the
category half FILLED in the category colours under a bracket headed
«MAIN CATEGORY · one per contract», the works half HOLLOW (white arcs,
dark outline) under «WORKS NAMED IN THE TITLE · several per contract»,
wide seams between the halves (zero-value spacer groups — d3-chord pads
every group), and every ribbon a gradient from its category's colour to
neutral grey at the work end, so the direction category → work is in
the ink. The bulb says the same in words. TYPES OF WORKS lenses now:
works named (dots, default) / chord / works × category.

## 2026-08-23 · The chord divided top to bottom, works in reading order, horizontal labels

(user round 3 on the chord) The circle is now divided by a VERTICAL
seam — works on the left half (from the bottom seam up), categories on
the right (from the top seam down) — with the two headings either side
of the top seam. The works follow a READING order, not the count order:
clearing of forests and road maintenance run on from the bottom seam,
then the four firebreak works side by side (maintenance · mixed ·
sheltered · bare), then the rest by count, «no specific work named»
last at the top (`WORK_ORDER` in the component — a presentation order
of curated keys, labels still from the data). Labels are HORIZONTAL in
a column either side, each led to its arc by an elbow leader and
de-collided at a 15 px pitch — the radial labels at the poles had
truncated the long category names and the bottom heading sat on its
bracket line. Lettering: arc labels 11.5 px (categories bold), headings
11 px. Ribbon gradients fixed (they were drawn in the wrong coordinate
space once the centre moved and had gone grey).

## 2026-08-23 · Chord round 4: radial labels back, categories top-to-bottom in colour FAMILIES

(user) The horizontal label columns were rejected («I do not like the
switch to horizontal labels») — labels are RADIAL again at the approved
sizes (11.5 px / 11 px headings), the two headings stay horizontal. The
cramped category names are solved not by lettering but by GEOMETRY and
ORDER: the frame's height is now computed from the labels' own reach
(every radial name drawn whole, the only cut a 54-character cap on the
sentence-long ones, full text on hover), and the categories run TOP TO
BOTTOM on the right half in the user's order, which puts the seven
small ones at the top with room to fan.
**The category palette is now four colour FAMILIES** (`catColors.ts`,
shared — dots and the timeline type lens follow): blue anti-erosion
#0d366b · amber studies #b07d1e · greens: reforestation #2d6a4f
(darkest), logging #52b788 · the red ramp of the fire-prevention works:
mixed firebreaks #b33a1a, firefighting water #c8715a, fire protection
around archaeological sites #d99c8c, special forestry works #ebccc3
(each a step lighter). The user's list named logging and firefighting
water twice; read as the four families above — flagged for correction.
`CAT_ORDER` carries the reading order.

## 2026-08-23 · Chord round 5: big circle, two-row radial labels, fixed height

(user: «the circle bigger and the long titles in two rows; the previous
size was better because you didn't have to scroll») R back to 224 in a
FIXED frame (878 px, was 1053): a radial label wraps to TWO rows when
its single line would overrun the room at its angle (the frame's side
horizontally; a vertical budget of 200 px at the top, where the small
arcs of both halves fan, 120 px at the bottom), a name still longer is
cut with «…» (hover has it). A zero-value spacer sits between every two
arcs (d3-chord pads every group) so two-row labels never collide, and
the categories print in their SHORT names — the same split CONTRACT
TYPE uses (`splitHint`: before «:», parenthetical dropped). One name
cannot fit whole anywhere: the archaeological category's sentence-long
label — the user's call whether a shorter curated name is wanted.

## 2026-08-23 · Chord round 6: three rows for the longest name, lower-case names, label angles de-collided

(user) Up to THREE rows for a name (the sentence-long archaeological
category), the work names lose their opening capital (the page's
`lower` convention — proper nouns would keep theirs), and the frame is
trimmed to 794 px (R 212, vertical budgets 145 top / 115 bottom) so
more names wrap rather than the reader scrolling. Wrapping at the small
arcs' pitch made the blocks collide, so the label ANGLES are now
de-collided per half: a label keeps pointing radially but slides off
its arc's middle when a neighbour's rows need the room (forward pass
clockwise, backward pass back inside the half, rows recomputed at the
new angle, repeated once), and a thin tick leads from the arc to a
label that moved. The headings stay in capitals (they are headings, not
names). The height floor of a radial-label chord is the circle plus
the two labels pointing straight up and down — each 10 px of radius is
20 px of height, so ~650 px would mean R ≈ 165.

## 2026-08-23 · TYPES OF WORKS is the chord alone; the dots and the rows parked

(user: «keep only the chord and park the other two options somewhere, I
do not need them at the website») The frame shows `CatWorkChord` with
no toggle; `WorkDots.svelte` (one dot per contract-naming-a-work,
coloured by category) and `WorksByCategory.svelte` (the works × category
rows) stay in the repo, off the page — the `?works=` lens param is gone,
the network payload keeps `wk` (pinned). The chord's bulb text is the
frame's insight, the caveat unchanged.

## 2026-08-23 · Chord round 7: headings at the sides, seam stubs, the frame hugs the labels

(user: «move the titles to the sides, make the dashed lines smaller so
you can move the circle up; I do not want the user to scroll») The two
headings now sit at the SIDES level with the centre («WORKS NAMED IN
THE TITLE / several per contract» left, «MAIN CATEGORY / one per
contract» right, two rows each), the dashed seam marks are 34 px stubs
beyond the ring, and the frame's height is computed from the labels'
ACTUAL reach above and below the centre (the vertical budgets 125/105
remain only the cap), with the glyph width MEASURED in the browser
(4.84 px/char regular, 4.73 bold at 11.5 px — the estimate of 5.9 had
left slack). R 200. Chart 683 px, frame 776 with title and caveat
(was 878 → 794 → 710). Each 10 px of radius is ~20 px of height if it
must shrink further.

## 2026-08-23 · Chord round 8: adaptive spacers (no connector ticks), order by name length

(user: «firefighting water infrastructure in one line… alter the order
of appearance to not use that many of the small lines») Two changes:
- **Adaptive spacers**: a first layout tells how many rows each label
  needs at its own arc; where two neighbouring arcs sit closer than
  their labels' rows need, zero-value spacer groups are inserted between
  them (d3-chord pads every group) so the ARCS move apart and every
  label stays on its arc — the angle de-collision is kept only as a
  safety net. Result: 0 ticks on the page.
- **Category order**: the families stay together but their sequence
  puts the SHORT names at the steep top of the right half and the long
  ones lower, where a radial label has room — greens (reforestation,
  logging), blue (anti-erosion), amber (studies), then the red ramp
  (mixed firebreaks → firefighting water, now one line → the
  archaeological fire protection, whole in three rows → special
  forestry works). `CAT_ORDER` updated; the palette itself unchanged.

## 2026-08-23 · Chord round 9: the works arcs filled light grey

(user: «the white fill with black outline is a bit weird») The works
half's arcs are filled with the light grey the ribbons fade to at the
work end (#c9c9c9), no outline — one grey for «the work end of things»;
the category half keeps its colours. Bulb wording «hollow» → «grey».

## 2026-08-23 · Chord round 10: the hover card at the top-right, and it counts contracts only

(user) The black card moved to the frame's top-right corner. Its
content was confusing where it printed «contract–work mentions» for a
category arc (the arc's geometry — special forestry works: 154
contracts, 318 mentions, because a contract naming three works lies
under three ribbons). Every card now says CONTRACTS and nothing else:
a ribbon «N contracts — category → work», a work arc «N contracts
name: work», a category arc «N contracts — category» (the true count,
passed as `cats[].n`); that the arc is drawn to mentions is said once,
in the bulb.
(same day, later) …and just the number: «N contracts», nothing else —
the names are already lit on the chart when you hover.

## 2026-08-23 · The chord's halves are toggles: category ↔ works, category ↔ scope, scope ↔ works

(user: «a toggle in the MAIN CATEGORY and the WORKS NAMED IN THE TITLE
where the user could turn this to the contract scope» — rules agreed)
Every contract is flagged three ways — main category (one), contract
scope (one: study only / study & works / works only) and the works its
title names (several) — and the chord pairs two of them. A toggle sits
under each side heading: left «works named | contract scope», right
«main category | contract scope», with the RULE that both halves cannot
be the scope (the same variable on both sides is meaningless): setting
one half to scope snaps the other back to its default
(`chordSides.pairFor`, unit-pinned). Three pictures, `?chord=`:
- **cat-works** (default): the server-pinned per-category counts;
- **cat-scope**: both halves one per contract, so every arc and ribbon
  is a plain contract count (245), ribbons in the category colours, the
  scope arcs in CONTRACT SCOPE's three greys;
- **scope-works**: the scope on the right in those greys, ribbons
  scope-grey → works-grey; the scope arcs measure mentions like the
  category arcs do (bulb says so).
The matrices for the scope pairs are built client-side from the network
payload's per-contract `cat` / `dk` / `wk` (`transforms/chordSides.ts`,
tests on synthetic nodes). CONTRACT SCOPE's tones and wording moved
into `charts/scopeColors.ts` (solid greys — they work as arcs and as
ribbons, which the timeline's white-with-ring study mark cannot) and
the CONTRACT SCOPE share bar reads them from there. The component is
now generic (`data: ChordData`, `leftControl`/`rightControl` snippets).

## 2026-08-23 · Deliverables: the ΕΣΑ design clause and the chain — 5 «works only» become «study & works»

**Decision.** The user looked at the category ↔ scope chord and asked
whether the reforestation contracts are really works only. They are
not, 4 of 8: the ΕΣΑ lots 24SYMV014843550 / 24SYMV014844210 /
24SYMV014844359 / 24SYMV014844409 state, in their Άρθρο 4, «Ο Ανάδοχος
αναλαμβάνει την εκπόνηση όλων των μελετών που απαιτούνται για την
εκτέλεση του Έργου. Συγκεκριμένα, ο Ανάδοχος υποχρεούται να εκπονήσει
το σύνολο των μελετών εφαρμογής …» — and two of them name their
μελετητής (ENCODIA, ΟΛΥΜΠΟΣ ΕΤΑΙΡΙΑ ΜΕΛΕΤΩΝ) in the recitals. The
extractor (`scripts/extract_deliverables.py`) knew only the post-2024
template («η εκπόνηση από τον ανάδοχο … μελετών») and read each
contract's OWN text, so these defaulted to works. A chain-walk audit of
all 110 works-kind contracts (own text → every predecessor) found
exactly one more: 26SYMV019250208 (the single firefighting-water
contract), a cover note whose predecessor 25SYMV017471484 carries the
template clause verbatim. The other reforestation contracts — Ε1 black
pine 24SYMV014844450, the Αλίαρτος nurseries 23SYMV013600200 and their
two supplementaries — name no study anywhere (accent-folded search)
and stay works only.
**Fix.** The extractor gains the ΕΣΑ needles («ΕΚΠΟΝΗΣΗ ΟΛΩΝ ΤΩΝ
ΜΕΛΕΤΩΝ», «ΝΑ ΕΚΠΟΝΗΣΕΙ ΤΟ ΣΥΝΟΛΟ ΤΩΝ ΜΕΛΕΤΩΝ») and reads the CHAIN
(own text, then each predecessor — source `pdf:<ancestor>`), then the
call; regenerated and loaded. Counts: study 14 / study & works **126**
(was 121) / works **105** (was 110); pins updated. No `_overrides`
needed — the documents say it, the reader just had to look.

## 2026-08-23 · Front page re-ordered; DIRECT AWARDS + AWARD PROCEDURES in English, bulbs, readable brackets

(user) Order: ALLOCATION OF FUNDING · FLOWS OF MONEY · RANKING OF
COMPANIES · AWARDING PROCESS · DIRECT AWARDS + AWARD PROCEDURES ·
CONTRACT VALUES · CONTRACT SCOPE + CONTRACT TYPE · TYPES OF WORKS ·
PROCUREMENT TIMELINE · MONEY PER YEAR + CUMULATIVE DISBURSEMENT ·
PAYMENTS TIMELINE · STUDY COSTS · CPV CODES. The awards pair: the
procedure names print in the Directive's English (`procedureEn`, the
contract card's rule — «Direct award», «Open procedure», «Negotiated
procedure without prior publication»), the direct-award row highlighted
by a flag not a Greek substring, bars in the ranking's dress (35 px,
inside labels); both subtitles became lightbulbs with computed facts
(direct awards: N of M contracts, X% of the money) and AWARD PROCEDURES
gained a caveat + methodology link; the € brackets read «€2–5M» and
«500k–1M» instead of «2000–5000k» (`format.bracket`, presentation only,
unit-pinned) in the axis, the modal note and the bulb.

## 2026-08-23 · A lightbulb note never falls on a neighbouring frame

(user: the AWARD PROCEDURES note fell on DIRECT AWARDS) The margin
note assumes the page's left margin is free; a frame sharing its row
(the `.pair` halves, the `.scopetype` pairs, the full-bleed `.firesband`)
has its neighbour there instead. The rule now lives in `ChartFrame`
itself — inside those containers the note ALWAYS flows above the chart,
at any viewport — so no page can forget it; the front page's own
`.scopetype` override went away as redundant. Verified at 1900 px with
every bulb open on /, /dase, /anadohoi: no note overlaps any frame.

## 2026-08-23 · STUDY COSTS: the dots wear their contract's main category

(user: «the dots all print in the same colour») The 105 stated-fee dots
were one grey because they are one class; they now carry the contract's
main category in the page's shared palette (`catColors.ts`, the same
colour a category has on the chord and the timeline's type lens), with
a key in the MAP legend's dress and the category named on the hover
card. `study_points` gained `cat` (pinned present on every point). The
picture gained a reading: the anti-erosion contracts' fees sit at the
top right, 2–5 % of the biggest contract values.

## 2026-08-23 · STUDY COSTS parked — the study-fee layer is not trusted enough to show

**Decision (user).** The frame comes off the front page; `StudyScatter.svelte`,
the curated `study_costs.json`, the `contract_study_costs` table and the
`studies` payload stay as they are (pinned), so nothing downstream moves
— but nothing is presented until the layer is cleaned. What the audit of
2026-08-23 found, recorded here for whoever picks it up:
- **one wrong amount that is also a double count**: 26SYMV019471687
  stores €85,350.38 — its own sentence reads «66.232,82 το κόστος
  εκπόνησης μελετών, 85.350,38€ για ρήτρα πρόσθετης καταβολής»; and it
  is an additive supplementary whose in-scope parent 26SYMV018607958
  already carries the €66,232.82 — the entry should go;
- **a coverage hole of eleven design-build contracts** whose text states
  the fee but which have no entry — five 2023 phase-II PDFs with mangled
  accents («Ποσοό υόψους … (18.424,12), που αφορά το κόστος εκπόνησης
  μελετών…»: 23SYMV012992073 18,424.12 · 23SYMV012992145 8,251.09 ·
  23SYMV012992150 26,537.00 · 23SYMV013039379 8,166.90 · 23SYMV013530639
  8,659.17) and six 2024 table layouts with the amount inside the label
  («Κόστος εκπόνησης μελετών 22.995,60 συμπεριλαμβανομένων …»:
  24SYMV014217832 22,995.60 · 24SYMV014223991 16,732.11 · 24SYMV014224066
  13,780.36 · 24SYMV014251057 34,000.06 · 24SYMV014274380 16,920.11 ·
  24SYMV014274589 23,512.35) — the «24 bundle it unstated» claim was
  overstated by half;
- **a stray entry**: 22SYMV010741336 €6,451,612.90 is a programme
  allocation line («Σύμβαση 2: Μελέτες Κατάρτισης Σχεδίων …»), not a
  contract's fee — invisible only because the record is an umbrella;
- what held: 111/120 excerpts are the «κόστος εκπόνησης μελέτης
  συμπεριλαμβανομένων των φακέλων ΣΑΥ-ΦΑΥ» line (the study fee, not
  safety paperwork), every amount is verbatim in its excerpt, no fee is
  attributed to two tips, shares are against the chain's largest net.
**Spill-over still to act on**: the three «works only» contracts that
state a fee are 2022 ΤΑΙΠΕΔ contracts whose definitions make them
design-build («Έργο: οποιαδήποτε μελετητική και δασοτεχνική εργασία»,
«Μελέτη: η Μελέτη που θα εκπονηθεί και εγκριθεί πριν την έναρξη») —
22SYMV010795597, 22SYMV010795606, 22SYMV010864314 (via 22SYMV010635347);
the other 17 of 2022 define the Έργο as «οποιαδήποτε εργασία» with
«Μελέτες που έχουν εκπονηθεί» and stay works only; 27 of the 2023 works
carry only a boilerplate «πρόγραμμα μελετητικών και δασοτεχνικών
εργασιών» with no study defined. Not applied yet (the user parked the
frame rather than work on it); the deliverables layer would read 129 /
102 if it were.

## 2026-08-23 · Deliverables, second correction: the 2022 ΤΑΙΠΕΔ template — 3 more «works only» become «study & works»

(user: «if it influences another graph it has to be resolved») The
three 2022 contracts that itemise a study fee — 22SYMV010795597,
22SYMV010795606 and 22SYMV010864314 (via its predecessor
22SYMV010635347) — define in their own Άρθρο 1 «Έργο: οποιαδήποτε
μελετητική και δασοτεχνική εργασία … θα παρασχεθεί από τον Ανάδοχο» and
«Μελέτη: είναι η Μελέτη που θα εκπονηθεί και εγκριθεί πριν την έναρξη
εκτέλεσης των εργασιών», and their Χρονοδιάγραμμα is «το πρόγραμμα
εκπόνησης της μελέτης και εκτέλεσης εργασιών»: design-build in the
2022 wording. The extractor gains that marker («ΜΕΛΕΤΗ ΠΟΥ ΘΑ ΕΚΠΟΝΗΘΕΙ
ΚΑΙ ΕΓΚΡΙΘΕΙ»); regenerated and loaded, exactly the three move — the
other 17 of 2022 define the Έργο as «οποιαδήποτε εργασία» with «Μελέτες
που έχουν εκπονηθεί» and stay works only, and the 27 contracts of 2023
that carry only the boilerplate «πρόγραμμα μελετητικών και δασοτεχνικών
εργασιών» (no study defined) stay works only. Counts: study 14 / study &
works **129** / works **102**; pinned, with a pin that 17 of the 20
contracts of 2022 are works only. The PROCUREMENT TIMELINE's scope bulb
now prints that ratio from the nodes instead of claiming «the 2022 era
bought works only». Surfaces moved: CONTRACT SCOPE, the timeline's
scope lens, both scope views of the chord, the three contract pages.

## 2026-08-23 · CONTRACT SCOPE gains «CONTRACTS BY SCOPE PER YEAR»

(user: «a simple graph like DESIGNATIONS / COMPLETIONS PER YEAR in
sponsored works, below the contract scope, the number of each scope per
year with a line») Under the CONTRACT SCOPE share bar, the sponsored
page's `AreaYears` form: contracts signed per calendar year, one SOLID
line per scope in CONTRACT SCOPE's three greys (`AreaYears` gained a
`dash:false` option for that), years from the first to the last
signature, counted from the contract nodes' `d` and `dk` — the same
fields the timeline's scope lens and the 17-of-20 pin read. Sub-label
in the MAP-label dress.
(same day, second round) The verticals stand on 1 JANUARY of each year,
labelled on the rule as every timeline on the site, with an unlabelled
rule on the 1 January after the last year; a year's count sits at the
MIDDLE of its span as a DOT (so the point each line starts from — and
every value — is explicit), and a dashed «today» rule shows the open
year as partial. `AreaYears` gained `janRules` / `dots` / `today`
options; the sponsored chart keeps its category axis.
(same day, third round — user: the two columns ended at different
heights) The left body (bar + per-year chart) was 117 px taller than
CONTRACT TYPE's. Closed by design: the chart's own legend went (the
share bar right above names the same three series in the same tones —
`AreaYears legend={false}`), the gap before the sub-label halved, the
chart 168 px tall in its viewBox; measured bodies 323 / 322 px. And as
the safety net, the `.scopetype` pair stretches both frames to ONE
height with each caveat anchored to its frame's bottom, so the pair
always ends on one line whatever the contents.

## 2026-08-23 · AWARD PROCEDURES left, DIRECT AWARDS right

(user) The two half-width frames swap places: the procedures bar first,
the direct-award histogram beside it.

## 2026-08-23 · The front page's copy doctrine: basis once, bulbs for findings, caveats for method and source

(user) Reviewing the lines under the charts: ~600 words, half of them
the same three facts repeated (excl. VAT, the even split, counts that
exceed contracts) or how-to-read that the chart and its legend should
carry — the caveat rule («every chart carries its own honesty line»)
predates the lightbulb and was never slimmed after it. New doctrine,
applied in one pass:
- **the basis is said once** for the page, under the programme
  paragraph («stated values excl. VAT, from ΚΗΜΔΗΣ and the signed
  PDFs; the even split; payments a separate layer», linked to the
  methodology) — eight frames dropped those sentences;
- **the bulb states FINDINGS and author context only**, computed from
  the payloads, never how to read: ALLOCATION (the top unit and how
  many units hold half), FLOWS (the local share), RANKING (the top-10
  share), AWARDING PROCESS (the directorate's share), AWARD PROCEDURES,
  DIRECT AWARDS (+ the RRF context), CONTRACT VALUES (median, every
  contract above the €60k ceiling — a bulb it lacked), CONTRACT SCOPE,
  CONTRACT TYPE, TYPES OF WORKS (the biggest arcs' strongest ribbon,
  from the matrix), PROCUREMENT TIMELINE, MONEY PER YEAR (peak years —
  new bulb), CUMULATIVE (the same-day comparison — subtitle → bulb),
  PAYMENTS TIMELINE (lag medians), CPV (subtitle → bulb);
- **the caveat is the frame's specific method and source** where the
  page has not said them — one clause, or none (FLOWS, RANKING party
  view, CONTRACT VALUES have none); every chart keeps its Methodology
  link where a caveat remains;
- **how-to-read lives in the chart**: the only two judged worth keeping
  («circle area = stated value · vertical position = packing only»)
  moved into the PROCUREMENT TIMELINE's key.
The new findings are pinned (`test_front_page_findings`: East Attica
11,9 % and 7 of 59 units hold half; the directorate 77,6 %; median
€2,12 M with every contract above €60k; the top 10 hold 26,6 %).

## 2026-08-23 · CPV CODES rolled up the vocabulary's own tree, named from the official EU workbook

(user: «are there larger categories the list can be divided into, like
the EU protocols? the way we show them is not optimal») The CPV
(Regulation (EC) 2195/2002 as amended by 213/2008) is a five-level tree
— division (2 digits) · group (3) · class (4) · category (5) · code (8);
a prefix's own code is the prefix padded with zeros, so every ancestor of
a declared code is itself a CPV code with an official name. The 145
declared codes roll up into **13 divisions, 26 groups, 43 classes, 53
categories**; the flat list of 145 was the leaf level of that tree.
**Source of the names**: the TED/SIMAP workbook `cpv_2008_ver_2013.xlsx`
(https://ted.europa.eu/documents/d/ted/cpv_2008_xls; all EU languages),
kept in `data/raw/`; `scripts/build_cpv_nodes.py` writes
`khmdhs/data/cpv_nodes.json` — EN + EL names for exactly the 238 nodes
the in-scope contracts touch, each at its TRUE level (a declared
77200000 is the group, not a leaf under it; 0 missing). The API
(`queries_extra.antinero_cpv_tree`, `cpv_tree` on the overview) rolls
the declared codes up as division → class → code — a declared code
shallower than class files as its own class — with **distinct-contract
counts at every node** (a contract declares 16,0 codes on average —
3,910 code rows over 245 contracts — so counts overlap across nodes and
are never summed or drawn as a partition). Front page: `CpvTree.svelte`
— one bar per division in the ranking's dress, opening into its classes,
each into its codes, EN name with the Greek beneath; the bulb states the
finding (233 of 245 contracts declare a forestry-services code and 197 a
construction-work code — the same contracts filed as services and as
works at once; the most common code on 91,8 %), the caveat the source
and the overlap rule; a `/methodology#cpv` section explains. Pinned in
`test_cpv_tree` (13 divisions; 77 → 233, 45 → 197, 90 → 130; 145 codes;
every node named).

## 2026-08-23 · (reverted the same hour) CONTRACTS BY SCOPE PER YEAR as stacked columns — the user meant the CPV bars, the lines stay

(user, after the Common Wealth «Complaints have tripled» form) The
three lines became stacked columns — `StackedYears.svelte`: one column
per year in its span between the 1-January rules, the total on top,
segments in the scope tones (works only at the bottom), counts printed
where a segment is tall enough, the «today» rule on the open year. The
rule that goes with the form: stacking only where the breakdown
PARTITIONS the contracts (scope, category — one per contract), never for
the CPV divisions or the works named, where a contract sits under
several rows. `AreaYears` keeps the time-axis options it gained today
(unused on this page now; the sponsored chart is unchanged).

## 2026-08-23 · CPV CODES: the divisions as vertical columns, the chosen one's classes beneath

(user, after the Common Wealth dashboard's column charts) The division
bars became COLUMNS — `CpvColumns.svelte`: one column per division, the
distinct-contract count on top, the division's number and short name
(the name's head clause, wrapped) underneath; the columns are tabs — the
chosen division turns black and `CpvTree` (classes-only mode) lists its
classes with bars and counts, each opening into its codes with the EN
and EL names. Never stacked or summed: the counts overlap. The
per-year scope LINES stay as they were (a stacked-columns version was
built on a misreading and reverted within the hour; `StackedYears.svelte`
is parked).
(same day, later — user) English only (the Greek names stay in the data
for the Greek edition); the code NUMBERS set apart from the counts («CPV
77» muted, the classes' four digits under their columns, the counts bold
on top) and both axes named; and the chosen column SPLITS IN PLACE into
its classes — its slot widens (44 px a class, ≥ 180 px, ≤ 60 % of the
plot), the other divisions compress and grey, a bracket above carries
the division's own count, and the key under the chart names the classes
(two columns), each opening into its codes (the opened class lit in the
accent on the chart). `CpvTree.svelte` stays in the repo unused.
(same day, third round — user) The click now DRILLS: the other divisions
leave and the chosen division's classes take the whole width as columns
of their own, with a breadcrumb at the top («← all divisions · CPV 77
Agricultural, forestry, … · 233 contracts») carrying the division's full
name and the way back — the in-bar bracket lettering is gone; the
counts print white inside a bar tall enough, in ink above it otherwise;
the hover wash (a fill the site uses nowhere else) is gone — a hovered
bar darkens instead; the key under the chart keeps the class list and
opens the codes, the opened class lit on the chart.
(same day, fourth round — user: «I didn't mean the rest should
disappear every time, only when there is not enough space; keep the
subcategories thinner, keep grey vs black») Back to the SPLIT IN PLACE:
the chosen division's slot widens to hold its classes as thinner black
columns (36 px a class, ≥ 180 px), the other divisions stay in grey and
first COMPRESS (down to 66 px, where a number and a short name still
fit) — only when even that is not enough do the smallest step aside,
and the axis says how many («the 5 smallest step aside while CPV 45 is
open»; CPV 77's split keeps all twelve). Counts white inside tall bars
for classes and divisions alike; the crumb line keeps the full name and
«✕ close».
(same day, fifth round — user) The division names print WHOLE under
their columns, wrapped on words to the slot (the label band is as tall
as the tallest name on show); the lettering follows the site's charts —
names and counts 13 px, CPV numbers 11 px, ticks 10 px; the long
sentence above a split division is gone — the split group carries its
identity where every column does, on the number line («CPV 77 · 233
contracts») and in its whole name in bold beneath, with only «✕ close»
at the top right.

## 2026-08-23 · The menu loses CONNECTIONS and ΑΡΩΓΗ; COMPARE becomes KEY FINDINGS, dressed like the dataset pages

**Decision (user).** «I do not need the pages CONNECTIONS and ΑΡΩΓΗ to
appear in the website any more. The page that is now compare should be
named KEY FINDINGS, and you should try to adjust its aesthetics,
lettering and presentation to the sponsored works, antinero works and
forest co-op works pages. The colour selection of the graphs looks good,
I mainly refer to the lettering sizing etc.»

**What changed.** The header MENU ▾ now holds KEY FINDINGS · AUTHORITIES
· METHODOLOGY. `/connections` and `/arogi*` stay as routes (their code,
endpoints and tests are untouched) but no link on the site reaches them —
the Connections flow maps already moved to the Anti-nero page on
2026-08-20, and the methodology's Αρωγή section now opens by saying the
pages are not presented. The route `/compare` keeps its URL; the page was
rewritten in the three dataset pages' dress: the hero is the cards grid
(Anti-nero black, forest co-ops green, two grey cards for the gap ratio
and the zero shared companies) beside the KEY FINDINGS kicker, one
paragraph, and the page's basis said ONCE; the frames carry short capital
titles (SHARED COMPANIES · CONTRACT SIZES · WHERE BOTH FLOWS LAND ·
REGION BY REGION · MONEY PER YEAR), each finding computed into its
lightbulb (the top shared unit, the co-op-heaviest unit, the peak years,
the medians, the entity counts), each caveat one clause of method and
source; the per-year pair is the ranking's 35 px bars, each side in its
hue, a year without contracts printing «—». Inside the charts: the
hover cards are the site's black plate; the lettering follows the other
pages (names and legends 13 px, labels 12 px, ticks 11 px, no italics);
«ΔΑΣΕ» in chart labels reads «forest co-ops» as on the cards; the
pipelines box is as tall as its columns (the fixed 560 px left a void
under the dots); the ministry prints its English name; power-of-ten
ticks read «10 M €»; the scatter's outlier labels are nudged apart when
they land within a row of each other; the «Anti-nero only» gutter label
sits above the gutter row, off the dots; the paired bars' italic
how-to-read note is gone (the column heads say it). No number on the
page is typed — every figure in cards, bulbs and caveats comes from
`/api/compare`.

**Same day, second step (user: «I do not want you to delete any of their
data, but I do not want them to appear on the website or be searchable,
or appear on the METHODOLOGY»).** Assessed first: the only thing on the
site that depended on either page was the Anti-nero FLOWS OF MONEY
frame's use of the `/api/connections` ENDPOINT and one TypeScript type;
the site's own search (/explore, contractor search) never covered them;
there is no sitemap, robots allows all — a deleted route simply 404s and
drops out of any index. Done: `atlas/src/routes/arogi/` (list, case,
summary) and `atlas/src/routes/connections/` deleted; the `Connections`
interface moved to `$lib/api.ts`; the methodology's Αρωγή section
deleted; the Atlas API no longer knows the dataset — no `AROGI_*` config,
no lazy connection, no `/api/arogi/{explore,summary,case}` (404), no
`arogi` key in `/api/meta`, no arogi_cache fallback in the Diavgeia PDF
proxy (the proxy fetches from Diavgeia when a PDF is not in the sponsor
cache, so reachability is unchanged). `/api/connections` stays. Kept,
untouched: `data/processed/arogi.sqlite`, `khmdhs/arogi.py`,
`khmdhs/arogi_loader.py`, `scripts/harvest_arogi.py`, the curated
`arogi_fires.json` / `arogi_press_totals.json` /
`elga_fire_compensation.json`, `arogi_cache`, `tests/test_arogi.py`, and
`queries_extra.arogi_*` — `test_atlas_real_db.py::test_arogi_pins` now
pins those functions directly against the committed DB (956 cases, the
2021 fire unit on top, a case's act trail) AND asserts the API serves
nothing (404s, no meta key). The CLAUDE.md Αρωγή section records the
state; the privacy rule (owner names never stored or displayed) is
unchanged by the cut.

## 2026-08-23 · The ΔΑΣΕ contract page is to mirror the Anti-nero one — two new ΔΑΣΕ layers decided first: deadlines read from the signed text, a work-type taxonomy with a separate fire-context attribute

**Request (user).** «Adjust the list of the information included, the
language, the timeline and procurement diagram, the document trail,
procurement details, extracted quotes from documents and CPV codes, the
aesthetics, the lettering (heights and style) of the contracts of DASE to
the ones of antinero.» Questions were asked first; the answers, in order:

1. **TIMELINE bar — «Read the 2,164 PDFs first», then «Document-stated
   only».** The Anti-nero bar comes from the signed text's duration clause;
   the ΔΑΣΕ registry states an end date for 682 of 1,998 live contracts and
   a duration for 265. The texts were probed before building: the ΔΑΣΕ
   corpus is not one template. 1,271 of 1,998 live contracts (64 %) are the
   forest services' «ΣΥΜΦΩΝΗΤΙΚΟ ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ ΓΙΑ ΤΗΝ ΚΑΛΥΨΗ
   ΑΤΟΜΙΚΩΝ ΑΝΑΓΚΩΝ (άρθρο 8 π.δ. 126/1986)» — price-per-χ.κ.μ. agreements
   that state NO deadline (826 cite a «διαχειριστικό έτος» only in their
   recitals; the registry holds an end date for 330 of them). Of the other
   727, the Anti-nero reader already reads 74 and ≈ 317 carry ΔΑΣΕ-dialect
   deadlines — «Προθεσμία εκτελέσεως μέχρι 31-12-2021», «η υλοτομία θα
   αρχίσει από της υπογραφής του παρόντος … λήγουσα ανυπερθέτως στις
   31-12-2021», «η διάρκεια της σύμβασης ισχύει έως 31/12/2022», «ορίζεται
   από την υπογραφή της και μέχρι 31/12/2024», «έχει διάρκεια ενός (1)
   μηνός», «η περαίωσή τους την 30/11/2021», «ορίζεται μέχρι τις 20
   Οκτωβρίου 2021»; open-ended «μέχρι εξαντλήσεως του ποσού» / «λήγει με
   την ολοκλήρωση των εργασιών» = no deadline; 44 are scans. Offered:
   document-first with the registry end date as a labelled fallback; the
   management year read as 31.12; document-stated only. **User: document-
   stated only** — a deadline the signed text states draws the bar (≈ 22 %
   of contracts); no registry fallback; everything else is the stub; no ✔
   ever (no ΔΑΣΕ completion acts exist, DATA_DECISIONS 2026-08-03).
2. **PROCUREMENT DIAGRAM — FamilyTree behind the Map/Diagram switch.** The
   Anti-nero circles need every lot's € and come from the families layer
   read from the signed texts; ΔΑΣΕ has no such layer, and its registry
   siblings are often non-co-op lots outside the dataset with no € stored.
   The trunk → award fan → contracts tree stays (it IS what ΚΗΜΔΗΣ
   declares), moved into the header slot in the Anti-nero dress, English
   labels; the trail line «one of N contracts in the same procurement —
   see the diagram» as on Anti-nero.
3. **FACTS rows — the Anti-nero list with what ΔΑΣΕ has, PLUS a curated
   Type.** Contract · Date · Contractor · Type · Budget · Awarding
   procedure (EN) · Contracting authority (EN) · Awarding unit (EN) · Areas
   of intervention = the Regional Unit derived from the unit (said so) ·
   Duration (document-stated, else «not stated») · Amendments · Status
   «no completion record trackable». No Scope row (no deliverables layer).
4. **CONTRACTOR name — the Greek display name** as the link, «in the
   registry as …» beneath; English stays on the /dase overview surfaces.

**The ΔΑΣΕ work-type taxonomy (decided after three rounds).** The first
proposal grouped by document family; the user asked for a closer look at
fire protection and prevention, and for the reading to be stated rule by
rule. Findings: declared fire-PREVENTION purpose in ≈ 20 contracts
(≈ €0.4 M: «διαχείριση βλάστησης … για αντιπυρικούς σκοπούς»,
«δημιουργία περιμετρικών αντιπυρικών ζωνών», «ζώνες πυρασφάλειας»,
«υλοτομικές εργασίες πρόληψης δασικών πυρκαγιών», «δράσεις πρόληψης
πυρκαγιών … καθαρισμοί»); POST-FIRE restoration in ≈ 100 contracts
(≈ €15.2 M — half of the ΔΑΣΕ basis: the 2021 Εύβοια and Ηλεία
αντιπλημμυρικά/αντιδιαβρωτικά έργα, salvage logging in Ιστιαία, «κοπές και
καθαρισμός οδοποιίας από καμμένα δέντρα», Αμαλιάδα 2025–26); the
August-2021 emergency law (ΠΝΠ 05/13-08-2021, ν.4824/2021) cited as the
LEGAL BASIS of 64 ordinary logging/tending contracts — procedure, not
purpose; no fire-watch contracts at all; the firewood agreements mention
fire only in force-majeure boilerplate. **User rules:** (i) the category
comes from the contract's OWN words — the PDF's title (the heading after
the letterhead, or the quoted title «με τίτλο: «…»») and the sentence that
describes the work («αναλαμβάνει την εκτέλεση των εργασιών …», «Είδος
ανατιθέμενων εργασιών: …», «θα δεσμεύσει … τις παρακάτω ποσότητες
καυσόξυλων») — NEVER funding recitals, legal-basis recitals, boilerplate
or CPV; the registry title is not a source (the 44 scans are read by eye,
the precedent of the 2026-08-18 awardee review, and carry that as their
source); (ii) WHAT is done is one category, WHY is a separate attribute
— «post-fire restoration» and «fire prevention» are umbrellas over
different works and must not swallow them; (iii) firewood for local needs
stays apart from timber harvesting (the document's own title tells them
apart; the villages' annual right is not a sale); (iv) firebreak zones are
their own key; (v) the planting key is named with reforestation.
**Keys (one per contract):** firewood for local needs · timber harvesting
· silvicultural tending · vegetation clearing · firebreak zones · tree
felling & pruning · flood & erosion-control works · reforestation,
planting & seed collection · supply of timber & firewood · other forestry
services. **Fire context (attribute, may be empty):** wildfire prevention
· post-fire restoration, read from the same title/sentence («για
αντιπυρικούς σκοπούς», «πρόληψη (δασικών) πυρκαγιών», «ζώνες
πυρασφάλειας», «πυροπροστασία», «αντιπυρική προστασία» / «καμένων
εκτάσεων-δέντρων-ξυλείας», «πληγείσες από τις πυρκαγιές», «αποκατάσταση …
πυρκαγιά», «πυρόπληκτες»); a contract whose text states no purpose gets
none — nothing is inferred from the season or the funding.
Implementation follows in the next entries (reader, curation, loaders,
API, page).

## 2026-08-23 · ΔΑΣΕ contract page — the two layers built, curated and loaded; the page redressed on the Anti-nero skeleton

**What was built (same day, after the decisions above).**

*Reader* — `khmdhs/dase_details.py`: `read_title()` takes the PDF's own
heading (the first line after the letterhead that IS the document's name —
«ΣΥΜΦΩΝΗΤΙΚΟ …», «ΣΥΜΒΑΣΗ …», «ΠΡΩΤΟΚΟΛΛΟ ΕΓΚΑΤΑΣΤΑΣΗΣ» — letter-spaced
headings closed up, the block cut at the first recital or the opening
sentence), the quoted title («με τίτλο: «…»», «της υπηρεσίας «…»» — never
one standing inside a funding, decision or legal recital) and the work
sentence («Είδος ανατιθέμενων εργασιών: …», «αναλαμβάνει την …»,
«ΑΝΑΘΕΤΕΙ … την …», «Αντικείμενο …», «θα δεσμεύσει … καυσόξυλων», «οι
εργασίες συνίστανται στα …», «αφορά …»), plus — for the FIRE CONTEXT only —
the contract's own statement of need («Την ανάγκη άμεσης εκτέλεσης έργων
αντιπλημμυρικής προστασίας στις καμένες περιοχές του Δασαρχείου
Ιστιαίας …», the last «έχοντας υπόψη» item before «ΑΝΑΘΕΤΕΙ»: the
contract's words, not a citation — without it the 45 Εύβοια flood-works
contracts, whose titles name the basin and not the fire, would carry no
context although their own justification does). `read_category()` tests
ten ordered rules on the heading, then the quoted title, then the work
sentence — the first field that names a work decides; every family that
fires is listed and a field naming two different works (beyond the
compatible pairs firewood+logging, tending+logging) is flagged for
review; `read_deadline()` reads a DATE («Προθεσμία εκτελέσεως μέχρι
31-12-2021», «λήγουσα ανυπερθέτως στις …», «ισχύει έως …», «ορίζεται
μέχρι τις 20 Οκτωβρίου 2021», «περαίωσή τους την …», «εντός του
προκαθορισμένου χρόνου (έως …)», «θα εκτελεσθεί … μέχρι τις …»), else the
Anti-nero duration clause, else the ΔΑΣΕ duration dialect («έχει διάρκεια
ενός (1) μηνός», «θα είναι (1) ένας μήνας», «για ένα έτος»), else an open
end («μέχρι εξαντλήσεως», «αορίστου διάρκειας», «λήγει με την ολοκλήρωση
των εργασιών»); a date before the signature or more than four years after
it is flagged, never dropped. **The text layers needed repairing first:**
(a) homoglyphs («∆» U+2206, Latin capitals in Greek words); (b) the
«΢»-font family — 429 texts whose ToUnicode maps Σ→«΢» (U+03A2), Τ→«Σ»,
Υ→«Τ» in capitals and swaps/shifts the lowercase (σ↔ς, η→θ, έ→ζ, ώ→ϊ,
ύ→φ, with θ/κ and ή/ι merged) — undone LINE BY LINE where the line shows
the signature, because the same PDF mixes a ΢-font letterhead with a
clean-font heading and a global decode turned «ΣΥΜΦΩΝΗΤΙΚΟ» into
«ΤΥΜΦΩΝΗΥΙΚΟ»; the lossy lowercase pairs only inside the words the
readers need («προθεσμία», «καθαρισμ», «αναθέτει», «λήγει»,
«ολοκλήρωση», the έ-words); (c) a capital Θ-for-Η variant and the Φουρνά
Ω→Ψ/Ψ→Χ variant, repaired in named words only («ΨΝ» ends no Greek word);
(d) the true substitution-cipher fonts (Σπερχειάδα, Φουρνά bodies,
Ξάνθη, Δωδεκάνησα, Αλεξανδρούπολη 2025: Δ→«Γ», Ε→«Δ», Η→«Ζ», Ι→«Η» …) —
a capitals table learnt from each document's own phrases by cryptogram
pattern was tried and kept as code (`learn_cipher`/`decode_cipher`,
accepted only when the decoded text then reads like a contract) but the
documents that need it are mostly clean-heading/cipher-body, so in
practice the clean heading classifies them and their body (work sentence,
deadline) is read by eye; a text naming none of twenty ordinary contract
words is `unreadable_font`, a text under 1,500 characters or under 50 %
Greek letters is `scan`, and both go to the by-eye pass.

*Extraction + curation* — `scripts/extract_dase_details.py` reads all
2,164 contracts (an amendment's cover note through its predecessor,
`inherited:<ref>`), writes `data/processed/dase_details_review.json`
(gitignored) + the committed `dase_details_curator.html`, and `--curate`
writes `khmdhs/data/dase_categories.json` + `dase_durations.json` with
`_overrides` merged on top. Machine coverage after the repairs: 1,842 of
1,998 live contracts categorised, 44 with no rule fired, 80 cipher-font,
47 scans, 31 two-works flags. **Review:** every non-firewood proposal read
against its quoted evidence (≈ 560 lines); three corrected (24SYMV014452314
«αποψιλωτική υλοτομία» is a clear-cut → harvesting; 26SYMV018882122 poplar
harvest + clearing → harvesting; 23SYMV012461845 clearing + de-branching →
clearing), three «ΣΥΜΦΩΝΗΤΙΚΟ ΚΑΛΛΙΕΡΓΕΙΑΣ» and one «καλλιέργεια
νεοφυτειών» → tending, the ΑΔΜΗΕ «κοπή, τεμαχισμός και στοίβαξη δέντρων»
→ tree work; **the by-eye pass: 197 PDFs (scans, cipher fonts, no rule)
rendered as contact sheets of the first page's top half and read** —
205 `_overrides` written with the verbatim heading as evidence and the
source «eye» (Σπερχειάδα 52 firewood, Δωδεκάνησα 12 post-fire
erosion-control works, Σταυρούπολη/Ξάνθη/Μέτσοβο logging protocols with
their table dates, Ροδόπη 7 «υλοτομικών εργασιών πρόληψης δασικών
πυρκαγιών», Δοξάτο/Αλμωπία/Κιλελέρ tree work, and the odd ones out: a
ΔΕΘ fair-stand lease, furniture repair for a forest office, office-
equipment maintenance, sacks for the 2023 election, three olive-fly
spraying contracts of €532,937 / €400,308 / €126,779 won by the Ένωση
Δασικών Συνεταιρισμών Εύβοιας, a snow-clearing road opening — all
«Other forestry services» with the reason noted; 19 deadlines read by
eye from the protocols' «Προθεσμία εκτελέσεως»). Two rules settled on the
way: a harvesting PROTOCOL whose table says «Είδος υλοτομίας:
Καλλιεργητική» is harvesting (the work named is the harvest, the tending
is the cut's type), while «ΣΥΜΦΩΝΗΤΙΚΟ ΕΡΓΑΣΙΩΝ ΣΥΝΤΗΡΗΣΗΣ & ΒΕΛΤΙΩΣΗΣ
ΔΑΣΩΝ (ΚΑΛΛΙΕΡΓΗΤΙΚΩΝ ΥΛΟΤΟΜΙΩΝ)» is tending; and «ΔΕΣΜΕΥΣΗΣ ΚΑΥΣΟΞΥΛΩΝ
… ΚΑΙ ΕΚΤΕΛΕΣΗΣ ΕΡΓΑΣΙΩΝ ΣΥΝΤΗΡΗΣΗΣ & ΒΕΛΤΙΩΣΗΣ» (Έβρος 2025, 17
contracts) files under firewood, the work named first, flagged as two
works.

*Result (live 1,998):* firewood for local needs 1,463 · silvicultural
tending 193 · timber harvesting 139 · flood & erosion-control works 89 ·
tree felling & pruning 49 · vegetation clearing 46 · other 10 · supply 3 ·
firebreak zones 3 · reforestation/seed collection 3. Fire context:
post-fire restoration 92 (spanning flood works, clearing of burnt trees
along roads, the ΟΣΕ burnt-tree felling, the Μαντούδι storm-and-fire road
service) · wildfire prevention 24 (firebreaks, preventive clearing,
fuel-reduction logging in Έβρος and Ροδόπη). Deadlines: 290 contracts
state one — 179 as a date, 100 as a duration, 11 open-ended; 1,708 state
none and draw the stub. Loaded by `khmdhs/dase_details_loader.py`
(hooked at the end of `harvest_dase.py load`) into `contract_categories`
+ `category_labels` (with `label_en`), the new `contract_fire_context` +
`fire_context_labels`, and `contract_durations` (two new columns
`deadline_date`, `kind`, plus `note`; the Anti-nero rows leave them NULL).

*API* — `/api/dase/contract/<adam>` now ships `category`, `fire_context`,
`chain` (from the registry's prev/next links — the ΔΑΣΕ DB has no scope
table), `stated_duration`, `deadlines` (`queries_extra.dase_contract_deadlines`:
document-stated only, `basis` document | document_date, never the
registry's end date, `extensions` always empty) and a `d` on every payment.

*Page* — `atlas/src/routes/dase/contract/[adam]/+page.svelte` rewritten on
the Anti-nero skeleton: the facts list (Contract · Date · Contractor — the
Greek display name, registry spelling in a hint · Type · Fire context ·
Budget · Awarding procedure (EN) · Contracting authority (EN) · Awarding
unit (EN) · Areas of intervention = the Regional Unit derived from the
unit, said so · Duration — the document's statement or «not stated in the
signed text», the registry field in the hint · Amendments · Status); the
map cropped to the unit's region with the FamilyTree behind the
Map/Diagram switch (English labels, scaled to the slot — `FamilyTree fit`);
the TIMELINE as `ChainTimeline` in the dataset's green (`ink`) on an axis
opening 2021-09-01 (`axisStart`) — the bar from the signature to the
document-stated deadline or the stub, the run-up acts, the € marks, no ✔
ever; the DOCUMENT TRAIL with the payment orders in it and only the
award that names THIS co-op (the registry's chain returns every lot's
award — the FamilyTree's own name-verified pairing is applied to the
trail, the diagram keeps them all); the three folds PROCUREMENT DETAILS
(the registry duration and the items table inside) / EXTRACTED QUOTES
(value correction, the category's verbatim title, the fire-context
words, the duration sentence) / CPV CODES (the ΕΦΚΑ chip kept); the
Anti-nero lettering and spacing, `Fold` hover in the dataset hue
(`--fold-accent`). Pinned by `tests/test_dase_details.py` (reader units
incl. «recitals never decide the category» and the line-local ΢ repair;
real-DB counts; the endpoint never serving the registry end date).

*For the user's eye (not decided here):* 25SYMV017455982 (Αλμωπία «ΟΜΑΔΑ Β:
προληπτικός καθαρισμός της βλάστησης για τη μείωση του κινδύνου») carries
the prevention context from its body («για λόγους πυροπροστασίας»), as do
its siblings; the three Αλμωπία «ΟΜΑΔΑ …» lots and the Σιδηρόνερο
«πρόληψης και αντιπυρικής προστασίας» contract are clearing; the ΑΔΜΗΕ
power-line corridor fellings and the port-zone fellings are tree work, not
harvesting; the 17 Έβρος two-work agreements sit under firewood.

## 2026-08-23 · The ΔΑΣΕ interpretive layers leave the contract page — certainty below the bar (user)

**Decision (user).** The three layers extracted from the signed texts earlier
today — work-type category, fire context, document-stated deadline — are NOT
presented on the /dase contract pages. The verification plan (firewood
evidence sweep, heading-vs-body concordance, OCR second reader over the 182
unreadable bodies, verification page, 60-contract sample audit; ~5–6 h) was
priced and set aside; only 100%-certain information stays on the pages.
What is not 100%:

- **TYPE** — 133 live verdicts rest on a single by-eye read (scans + cipher
  fonts, no second reader), 34 two-works flags carry no user verdict, and
  heading-vs-body agreement was never measured for the 1,781 heading reads.
- **FIRE CONTEXT** — the 116 positives are verbatim quotes but
  single-reviewed; the «—» absence claim cannot be verified while 182
  document bodies stay unread.
- **DEADLINE** — 28 known missed sentences (the Ροδόπη «εντός του
  προκαθορισμένου χρόνου (έως …)» cipher-lowercase family and the Δίρφυς
  «λύεται … ήτοι …» family), 19 by-eye dates, and the same 182 unread
  bodies behind every «states none» stub.

**What changed on the page.** Only registry- or user-audited facts remain:
the TYPE, FIRE CONTEXT and DURATION rows are gone, their EXTRACTED QUOTES
entries with them, and the TIMELINE draws NO deadline bar — signature,
run-up acts and € payment marks only, all registry facts. The registry
duration stays visible inside PROCUREMENT DETAILS, labelled as registry
data.

**What stays in the repo (parked — the STUDY COSTS precedent).** The curated
JSONs (`dase_categories.json` 2,164 entries, `dase_durations.json` 326), the
reader (`khmdhs/dase_details.py`), the extractor/curator, the loader, the DB
tables (`contract_categories`, `contract_fire_context`,
`contract_durations`) and their pins in `tests/test_dase_details.py`; the
`/api/dase/contract/<adam>` payload keeps `category` / `fire_context` /
`stated_duration` / `deadlines`, so the layer can return the day it is
independently verified. Nothing was deleted.

## 2026-08-24 · /dase front page: ranking, money per year and the CPV mix adjusted to the Anti-nero frames (user)

- **RANKING OF CO-OPERATIVES** — the Anti-nero ranking's dress: short caps
  title, a computed lightbulb (the top-10 co-ops' share of the stated basis,
  out of all co-ops), the canonical-ΑΦΜ merge and the even split of jointly
  signed contracts compressed to a one-clause caveat with the methodology
  link; the same 35 px inside-label bars.
- **MONEY PER YEAR** — the Anti-nero frame's form (values at the right,
  computed biggest-year lightbulb, no subtitle). Deliberately **no «€ paid»
  lens**: ΔΑΣΕ payment coverage is structurally partial (893 of 1,998
  contracts; 2022–23 near-blank as registry practice, DATA_DECISIONS
  2026-07-27) — a paid-per-year series would chart registry practice, not
  disbursement. The caveat says so; the paid figure stays a KPI.
- **CPV CODES** (was CPV MIX) — the declared codes rolled up the EU CPV 2008
  tree in the same CpvColumns as the Anti-nero front page:
  `queries_extra.dase_cpv_tree` over the live population, the rollup shared
  with `antinero_cpv_tree` via one `_cpv_rollup` helper;
  `khmdhs/data/cpv_nodes.json` and `scripts/build_cpv_nodes.py` now cover
  BOTH datasets' declared codes (the ΔΑΣΕ live rows added). The ΕΦΚΑ
  insurance code 66519300-4 shows as its own division, carried with the
  documented 2026-08-17 caveat (state-borne contributions itemised in the
  awards, never procured insurance); counts are distinct contracts per node,
  overlap across nodes, and are never summed.

*Verification note (same day):* the CPV CODES lightbulb says the whole
insurance division (386 contracts) is the ΕΦΚΑ tag. Beside the pinned
66519300-4 (378 live contracts), 8 contracts carry 66500000-5 — all 8
verified to hold an «ΕΦΚΑ εργοδότη / εισφορές ΕΦΚΑ» object line, so the
division-wide claim holds. The axis tick step of `CpvColumns` now scales
to the dataset (the fixed 25/50 pair smeared 40 ticks at n=1,998; Anti-nero
still lands on 50), and a class-column count too wide for its bar prints
above it («1.406» overflowed the 36 px slot).

*Colour (same day, user):* the /dase CPV columns were the page's one black
chart — `CpvColumns` now takes the hosting page's ink (`--cpv-ink`; the
hover/faded states are that ink mixed toward the paper, landing on the
exact greys the rules used to hardcode, so Anti-nero is pixel-identical)
and the ChartFrame lightbulb follows the page accent (`--frame-accent`);
the /dase wrapper sets both to the dataset green.

*Layout (same day, user):* MONEY PER YEAR and RANKING OF CO-OPERATIVES
share one row at equal width (the page's `.pair` grid). The ranking's
75% `.rankw` measure — right for the full-width footprint — squeezed
the bars inside the half-width column until the last name fell outside
its bar, so on this page the pair column IS the measure (`max-width:
none`): every name, «ΔΑ.Σ.Ε. ΑΜΑΡΑΝΤΟΥ-ΚΛΕΙΝΟΥ» included, now sits
inside the green, wrapped to two lines where needed; the columns stayed
equal, and the ranking's amounts align RIGHT like MONEY PER YEAR's
(`valuesRight`, user).

## 2026-08-24 · The ΔΑΣΕ award-procedure frames and the legal basis of the «direct awards» (audit + user decision)

**Audit (all 1,917 live direct-award contract texts read for their cited
legal basis; the cached sidecars, fold-tolerant regex over the recitals):**

| basis cited in the contract's own text | all 1,917 | the 77 > €60k net |
|---|---|---|
| ν.δ. 86/1969 (Δασικός Κώδικας) | 1,482 | 8 |
| π.δ. 126/1986 | 1,351 | 1 |
| «τιμές ανάθεσης» ΚΥΑ | 1,097 | 2 |
| ν.4423/2016 | 154 | 69 |
| ν.4412/2016 (any mention) | 239 | 75 |
| — άρθρο 118 specifically | 46 | 6 |
| 13.08.2021 ΠΝΠ / ν.4824/2021 | — | 76 |
| «κατεπείγουσα ανάγκη» | 79 | 75 |
| κήρυξη έκτακτης ανάγκης | — | 67 |

The live direct-award population: 1,917 of 1,998 contracts (Σ net
€26,738,507.21, median €5,766.13, max €253,739.13); 109 above €30k, 77
above €60k. The >€60k cohort: ΑΠΔ Θεσσαλίας-Στερεάς 39 / ΑΠΔ
Πελοποννήσου-ΔΕ-Ιονίου 20 / ΥΠΕΝ 18; years 2021 ×34, 2022 ×35, 2025 ×8 —
the post-fire flood/erosion works of Β. Εύβοια and the Peloponnese and
the 2025 Έβρος works. Verified against the statute (e-nomothesia, ΦΕΚ Α΄
143/13-08-2021): the ΠΝΠ's άρθρο τέταρτο («Επίσπευση ειδικών
δασοτεχνικών έργων») operates «κατά παρέκκλιση οιασδήποτε γενικής ή
ειδικής διάταξης του ν. 4412/2016, πλην των διατάξεων ενωσιακής
προέλευσης», with no value ceiling; the 05+13.08.2021 ΠΝΠ pair is
ratified by ν.4824/2021. The 54 «Διαδικασία άρθρου 128 του ν.4412/16»
rows are ΑΠΔ Μακεδονίας-Θράκης firewood commitments filed under that
dropdown — rendered mechanically in English, never interpreted.

**Conclusion (the two-regimes reading, user-approved):** the ΔΑΣΕ
«direct awards» are two populations and NEITHER is governed by the
ν.4782/2021 άρθρο 118 ceilings — the mass runs on the forest-code
assignment regime (direct assignment at State-set prices is its design,
not a below-threshold exception; the registry's «(αρ.118/αρ.328)» suffix
is the platform's dropdown label, not the contracts' stated basis), and
the >€60k cohort on the ΠΝΠ derogation. **Therefore the /dase DIRECT
AWARDS histogram draws NO ceiling lines** (on Anti-nero they stay — those
contracts are ν.4412 procurements); the two frames AWARD PROCEDURES +
DIRECT AWARDS mirror the Anti-nero pair otherwise (procedureEn names,
computed bulbs, the dase doubling-edge axis), payload
`direct_awards` = `queries_extra.dase_direct_award_distribution`
(n / Σ / median / n_above_30k / n_above_60k computed, pinned), and the
legal context lives in /methodology#dase-award-basis, drafted for the
user to edit and place.

## 2026-08-24 · ΔΑΣΕ co-op registered offices: found, organised, stored (data layer only — user)

**Decision (user):** build the registered-office layer for the ~246 forest
co-ops — find, organise, store; what the site does with it is decided
separately. **Sources probed first:** VIES answered 26/26 test lookups with
settlement + Τ.Κ. + reference town («ΣΤΑΥΡΟΣ 0 · 57014 - ΣΤΑΥΡΟΣ») — the
primary register source; ΓΕΜΗ does NOT know forest co-ops (tested,
not_found — under ν.4423/2016 they register in the ΥΠΕΝ Μητρώο Δασικών
Συνεταιριστικών Οργανώσεων, which has no public API); the signed contracts
state a party seat for only a minority of co-ops (the ΔΑΣΕ συμφωνητικά
skip party seats) — kept as corroborating verbatim evidence where present,
anchored on the CO-OP party, never the awarder's «εδρεύει».

**Method (the Anti-nero contractor-seat pattern one dataset over):**
`scripts/build_dase_coop_seats.py` sweeps every canonical co-op ΑΦΜ
through VIES (throttled, cached in data/processed/, resumable) and reads
each co-op's contracts for a seat sentence; results land in curated
`khmdhs/data/dase_coop_locations.json` (per-ΑΦΜ: VIES name/settlement/
Τ.Κ./reference town, contract evidence ref+excerpt where found, the
co-op's own contracts' Π.Ε. as validator). Geocoding: Nominatim with the
Anti-nero tiers (structured → freeform → Greek→Latin transliteration →
settlement centre) and the same acceptance gates — Τ.Κ. prefix match or
resolution into the co-op's Π.Ε.; co-op seats are villages without
streets, so points are honestly settlement-centre precision
(`geo_precision: municipality`), never street points. Loaded by
`khmdhs/dase_locations_loader.py` into dase.sqlite's `contractor_locations`
(the shared-schema table, empty until now; hooked at the end of
`harvest_dase.py load`). No UI or API surface in this entry. Results
appended below once the runs complete.

**Result (the layer as stored).** 246 co-operatives — the live population's
own — every one with a seat and a point:

- **238 from VIES** (97%): the register answers with the co-op's village,
  its Τ.Κ. and the reference town («ΣΙΔΗΡΟΧΩΡΙ 0 · 68400 - ΣΟΥΦΛΙ»).
- **8 by labelled inference** (`seat_source: name_inference`): VIES does not
  answer for them, so the settlement is read from the co-operative's OWN
  registered name and accepted only because it lies in the Π.Ε. of its
  contracts AND the awarding forest service administers that village —
  ΒΑΘΗ/Κιλκίς, ΠΡΟΜΑΧΟΙ/Αλμωπίας, ΑΜΠΛΙΑΝΗ/Καρπενησίου, ΓΡΙΒΑ/Παιονίας,
  ΒΥΡΩΝΕΙΑ/Σιντικής, ΑΛΕΞΑΝΔΡΟΥΠΟΛΗ, ΕΛΑΦΟΣ/Αγιάς, ΣΙΔΗΡΟΝΕΡΟ/Δράμας. Each
  carries its reasoning in `note`; no postcode is invented.
- **64 with contract evidence**: a verbatim party clause from one of the
  co-op's own signed contracts. The reader anchors on the co-op's ΑΦΜ, reads
  BACKWARDS and requires a co-op name as the clause's subject — every ΔΑΣΕ
  contract states the AWARDING service's seat first, and a first pass
  wrongly captured «ΜΕ ΕΔΡΑ ΤΗΝ ΛΑΡΙΣΑ» (the Region's) for a co-op. Pinned
  by unit tests both ways.
- **246 geocoded, 0 failures**, all at `municipality` precision — the centre
  of the named settlement, the honest level for a village seat with no
  street. **The gate held perfectly: 238/238 register points fall inside the
  Π.Ε. their own postcode implies (0 misses).**

**Finding the layer exposes:** **36 co-operatives work outside their seat's
Π.Ε.** — a Τρίκαλα co-op logging in Εύβοια after the 2021 fires, a
Θεσσαλονίκη one in Ηλεία, two Θεσσαλία ones in Ρόδος. Travelling co-ops are
a finding, not an error: the test pins the postcode invariant, never
«seat == work region».

Stored in dase.sqlite's `contractor_locations` (the shared schema's table,
empty until now) by `khmdhs/dase_locations_loader.py`, hooked at the end of
`harvest_dase.py load`; curated file `khmdhs/data/dase_coop_locations.json`,
VIES responses cached in `data/processed/dase_vies_cache.json` (gitignored).
Pinned by `tests/test_dase_coop_seats.py`. **No UI or API surface yet — the
user decides what the site does with it.**

**Independent verification of the seats (same day).** The postcode gate is a
regression guard, not proof — it re-tests what the geocoder's own acceptance
rule already required. The independent check is the register against the
DOCUMENTS: of the 64 co-ops that have both a VIES record and a
contract-stated seat, **63 agree** (after Greek case/abbreviation
normalisation — «ΞΙΝΟ ΝΕΡΟ» ≡ «ΞΙΝΟΥ ΝΕΡΟΥ», «ΑΓ ΓΕΡΜΑΝΟΣ» ≡ «ΑΓΙΟΥ
ΓΕΡΜΑΝΟΥ», «ΒΗΣΣΑΝΗ» ≡ the contract's «ΒΗΣΑΝΝΗ»). **The one apparent
divergence turned out to be a RESTATEMENT, not a contradiction** (evidence
read out at the user's request, verdict theirs): 997309155
«ΔΑ.Σ.Ε. ΑΥΓΕΡΙΝΟΥ-ΝΕΑΠΟΛΗΣ Η ΦΛΟΓΑ» — its five contracts of September 2024
(Δασαρχείο Τσοτυλίου) say «ΜΕ ΕΔΡΑ ΤΗΝ ΤΟΠ. ΚΟΙΝ. ΑΥΓΕΡΙΝΟΥ ΔΗΜΟΥ ΒΟΙΟΥ Π.Ε.
ΚΟΖΑΝΗΣ», its two of September 2025 (Δασαρχείο Κοζάνης) say «ΜΕ ΕΔΡΑ ΤΗ
ΔΗΜΟΤΙΚΗ ΕΝΟΤΗΤΑ ΝΕΑΠΟΛΗΣ, ΔΗΜΟΥ ΒΟΙΟΥ ΚΟΖΑΝΗΣ», and VIES registers
ΑΝΑΣΕΛΙΤΣΗΣ 6, 50001 ΝΕΑΠΟΛΗ — the register agrees with the co-op's OWN
latest contracts. Same president, ΑΦΜ and Δ.Ο.Υ. throughout; both communities
belong to Δήμος Βοΐου, Π.Ε. Κοζάνης, ~15 km apart, so no region moves. **So
the register is confirmed by the documents in all 64 comparable cases.**

**Two rule changes it forced (user-approved, same day).** (1) The reader
stores the seat clause of each co-op's **LATEST** contract, not the first it
finds — the divergence was an artifact of quoting a 2024 statement against
today's register — and any earlier DIFFERENT statement is kept as
`earlier_seat` with its date and ΑΔΑΜ, never dropped; the loader folds it
into `seat_note` so a seat that changed can never read as an unchanging
fact. (2) `997309155` loses `flag: register_disagrees` and carries the
restatement note instead. Comparing seats needs the FIRST toponym of a
clause, not its whole text — «ΑΥΓΕΡΙΝΟΥ ΔΗΜΟΥ ΒΟΙΟΥ Π.Ε. ΚΟΖΑΝΗΣ» and
«ΝΕΑΠΟΛΗΣ, ΔΗΜΟΥ ΒΟΙΟΥ ΚΟΖΑΝΗΣ» share the prefecture's name — and Ω in the
stemmer's ending list, because pdftotext writes «ΑΛΩΝΩ,Ν» for «ΑΛΩΝΩΝ».
**Two co-ops carry an `earlier_seat`**: this one, and 800255256, whose 2023
contract says «ΜΕ ΕΔΡΑ ΚΑΣΤΟΡΙΑ» (the town) where its 2022, 2024 and the
register all say the village ΧΡΥΣΗ — the wider place named, not another
seat; noted per entry. Pinned by `tests/test_dase_coop_seats.py`.

For the other 182 co-ops no contract states a seat, so the register stands
unchallenged — the layer's honest limit.

## 2026-08-24 · The last unresolved ΔΑΣΕ work regions closed — 1.996 of 1.998 (user verdicts)

**The question asked:** are we safe stating the Regional Unit of the works
for every ΔΑΣΕ contract? **Audit:** the Π.Ε. is derived from the AWARDING
UNIT, which is administratively sound — a forest service's competence IS its
territory, it can only assign work in the forests it administers (1.836 of
1.998 live contracts come from a Δασαρχείο/ΔΔ; 151 curated non-forest
awarders; 7 overrides). **Independent check against the documents: where a
contract names a δήμος we can resolve, the document's municipality lies in
the assigned Π.Ε. in 139 of 139 cases.** Eleven apparent disagreements were
all artifacts of the probe's own regex — «ΔΗΜΟΥ ΒΟΛΒΗΣ» is the CO-OP's
address (a Θεσσαλονίκη co-op working in Ηλεία) and «ΔΗΜΟΥ ΓΕΩΡΓΙΟΣ» is a
PERSON, the president Δήμου Γεώργιος.

**Two soft spots found and closed by user verdict:**

**(a) The 12 Δωδεκανήσου contracts → Π.Ε. Ρόδου.** Δ/νση Δασών Δωδεκανήσου
is the only cross-Π.Ε. forest service that awards ΔΑΣΕ contracts (it covers
Π.Ε. Ρόδου, its seat, AND Π.Ε. Κω). Their texts scope the works to «καμένων
εκτάσεων περιοχής ευθύνης Δ/νσης Δασών Δωδεκανήσων» and NO island is named —
not in the 12 contracts, their 4 requests, 12 notices, 12 auctions or any
payment order (the only «ΡΟΔΟΣ» is the letterhead; an apparent «ΚΩΣ» was
«ΔΑΣΙΚΟΣ ΚΩΔΙΚΑΣ»). Decided on the fire evidence: EFFIS records **18.678 ha
burnt on Ρόδος in 2023** against 9 ha on Κως, whose only comparable fire
(557 ha) came in 2024 — after Ζώνη 1 was already in procurement. The
programme (€2.483.498,56 net, zones 1/2/3/6 with υποέργα, ΣΑ ΝΑ875 «Ειδικό
Πρόγραμμα Φυσικών Καταστροφών») is the restoration of the July 2023 Rhodes
fire. **INFERRED, not stated** — each of the 18 `contract_overrides` rows
(12 live + their 6 superseded versions) carries that reasoning verbatim.

**(b) The 4 ΑΔΜΗΕ contracts.** Their ΚΗΜΔΗΣ nutsCode EL306 «Δυτική Αττική» is
the company's OWN head office (Δυρραχίου 89, Αθήνα) and never the work site.
Two resolve on the documents' own words and are now assigned:
26SYMV019253854 → **Π.Ε. Χαλκιδικής** («σε περιοχές αρμοδιότητας του
Δασαρχείου Αρναίας», Γ.Μ. Θεσσαλονίκη–Στάγειρα, Τμήμα ΘΣ162-171 & ΘΣ186-212Ν)
and 25SYMV017288629 → **Π.Ε. Πέλλας** («στο τμήμα που ανήκει στο δημόσιο
διακατεχόμενο, διαχειριζόμενο ως συνιδιόκτητο δάσος Γραμματικού» — the
contracting co-op's own community forest, seat ΑΝΩ ΓΡΑΜΜΑΤΙΚΟ/Άρνισσα).

**The remaining 2 stay honestly unresolved, by decision.** 25SYMV016639591
and 25SYMV017124601 site their work by an unpublished ΑΔΜΗΕ drawing
(«σύμφωνα με το ΣΧΕΔΙΟ ΤΜΓΜ 2301 / 2301A») on the Γ.Μ. 150kV
ΛΑΜΙΑ–ΠΤΟΛΕΜΑΪΔΑ and ΣΧΗΜΑΤΑΡΙ–ΑΓΡΑΣ corridors. **The even split of a
multi-region contract was considered and REJECTED here** (user, after the
reasoning): Anti-nero splits a contract across the Π.Ε. its own text NAMES —
only the allocation is missing — whereas these name none, so the region list
would have to be traced from the lines' routes, i.e. invented; and the work
is «συνολικής έκτασης περίπου 7.360 / 7.760 m²» — 0,74 and 0,78 HECTARES, one
or two patches under the conductors, not work spread along 300 km. A split
would assert work in places we have no evidence for. Instead
`dase_units.json._unresolved_notes` records what the documents DO say (the
corridors, the area, the drawing) so the page states a fact, not a gap.

**Result: 1.996 of 1.998 live contracts carry a Regional Unit**, and the two
exceptions are documented multi-corridor cases rather than blanks. Pinned by
`tests/test_dase_regions.py`.

## 2026-08-24 · /dase ALLOCATION OF FUNDING — the works/seats choropleth duo (user)

The Anti-nero front page's paired maps, one dataset over, now that both sides
exist: the WORK side is `dase_contract_regions` (the awarding forest
service's area — 1.996 of 1.998 live contracts since the verdicts above) and
the SEAT side is `contractor_locations` (the co-operatives' registered
offices, built the same day; 246/246 with a point). **Both reconcile to the
stated-net basis €29.920.558,46 to the cent** — the work side as
€29.889.511,26 + €31.047,20 in the two ΑΔΜΗΕ corridor contracts that carry no
region, the seat side in full — on the shared even-split convention (a
contract signed by several co-ops divides equally between them).

**The finding the duo exists to show: 37,4% of the money — €11.181.051,82 —
is earned by co-operatives working OUTSIDE their own Regional Unit**, and it
is fire-driven: Εύβοια received €9,47M of work and imported €6,06M of it
(64%), Ηλεία €3,40M / €2,83M (83%), Ρόδος €2,48M / €1,68M (68%) — the three
big burnt regions of 2021 and 2023 could not do their own restoration. The
largest single flow is Τρίκαλα → Εύβοια €1,74M, then Θεσσαλονίκη → Ηλεία
€1,21M, Λάρισα → Εύβοια €0,95M, Πιερία → Ρόδος €0,80M. The everyday firewood
work stays home, which is why 62,6% never crosses a border.

**Implementation:** `queries_extra.dase_allocation` → `/api/dase/allocation`
(work_regions / seat_regions / flows / contracts-per-region, every figure
computed, pinned); `$lib/sections/DaseMap.svelte` draws the pair on ONE
shared scale in the dataset's green ramp, click-to-drill both ways
(clicking a work Π.Ε. shows which regions' co-ops earned there and vice
versa, `?focus=works:…|seats:…` permalink, «✕ … · all of Greece» pill, Esc),
the place card grey top-left and the item card black bottom-left as the
Anti-nero maps do.

**Dress corrected the same day (user): the LEGEND does the work, not
headings.** The invented captions «WHERE THE WORK IS» / «WHERE THE
CO-OPERATIVES ARE» were removed — the Anti-nero maps carry no headings at
all; each map has a key STRIP above it whose first row names what the map
is BY, in plain lowercase («by the area of the forest service that awarded
the contract» · «by the registered office of the co-operative that signed
it», each with a ⓘ), and the ramp row states the measure and changes with
the drill («€ of contracts» → «€ earned in Evia»). Above both sits the MAP
label with the how-to-read ⓘ and the reset pill, exactly as on the
Anti-nero page. The strip is the shared fixed 4,3rem height so the two map
rectangles never move on drill. The map wrapper's own border was dropped:
`.dasep :global(.map)` already gives every map in this section its hairline
and green zoom buttons, and a second one round the wrapper drew a double
edge. With the legend carrying the method, the frame's caveat is trimmed to
what nothing else says — the even split and the €31.047,20 off both maps.

**Two layout bugs found by the user in the same review and fixed:** the
pair sat glued together, maps and key strips alike, because the gap was
written `var(--sp-5)` and **there is no `--sp-5` in the token scale**
(1/2/3/4/6/8/12) — an unknown custom property makes `gap` invalid and the
grid falls back to zero; it now uses the Anti-nero `.twin`'s own
`var(--sp-4)`. And the two maps centred and zoomed differently from the
MAP frame below because they passed no `view`: both now take the section's
shared frame `{center: [23.8305, 38.3566], k: 1.08}`, the same one the
/dase MAP and the Anti-nero duo use, so every map on the page crops Greece
identically.

**A third bug the user caught: the scale was recomputed on drill**, so
clicking a region on the seat map RECOLOURED that same map although its
data had not changed (the max fell from the work side's €9,47M to the seat
side's €3,73M and every region darkened). The scale is now ONE constant —
the max across both sides at rest — in every state, which is what «one
shared scale» promised: a tone means the same amount everywhere, and a
drilled flow reads pale BECAUSE it is a fraction of the whole. **And the
drill now always speaks**: the sentence under the maps is written for the
empty cases too — «All of it went to co-operatives seated there — none
came from another regional unit» (Δράμα, whose 413 contracts are entirely
local), «No forest co-operatives in this dataset are seated in Chania» —
because a blank map beside a silent caption reads as a broken chart.

**The works drill answers with DOTS, not a colour (user, 2026-08-24).**
Choosing a region on the LEFT map now puts one dot on the right map per
co-operative that worked there, at its registered office, area ∝ the € it
earned in that region — the Anti-nero convention, whose right map likewise
carries the contractors' seats. A region's colour cannot say WHICH
co-operative came; a dot at the seat can, it links to the co-op's page, and
its card names the co-op, its € and its contract count there. The contrast
is the finding made visible: Εύβοια's 32 dots scatter from Θεσσαλία to
Μακεδονία, Δράμα's 25 sit on top of Δράμα. Payload additions
`coop_points` (246, every one geocoded) + `region_coops` (292 region×co-op
pairs, each region's pairs summing to its own € — pinned); the SEAT drill
keeps its choropleth, because a work location in this dataset is an area,
not a point.

## 2026-08-24 · Σπερχειός added to the context-rivers layer (user)

The ALFA WOOD plane-disease sanitation project **ΨΖ3Ψ4653Π8-5Β2** is scoped
by its designation act to «Ανάδοχο Αποκατάστασης **στην περιοχή του
Σπερχειού ποταμού** (Κομποτάδες, Ζηλευτό κ.α.), Περιφέρειας Στερεάς
Ελλάδας, στα όρια ευθύνης του Δασαρχείου Λαμίας» — the river IS the
project's extent, exactly as the Καλαμάς and Αχέροντας are for
6Φ454653Π8-Ξ1Ζ, so the card must draw it (user).

Added to `scripts/build_river_layer.py`'s curated set — name regex
«Σπερχει», bbox (38.70, 21.75, 39.10, 22.75): the Φθιώτιδα valley from the
Τυμφρηστός headwaters to the Μαλιακός delta, which is what pins the right
namesake — and the layer rebuilt from OSM Overpass: 4 parts, 192 points,
both copies byte-identical (17 KB). **Verified as the right course**: it
runs lon 21,88→22,56 and passes 0,6 km from Κομποτάδες and 2,0 km from
Ζηλευτό, the two localities the act itself names — pinned by
`tests/test_river_layer.py::test_sperchios_passes_the_projects_work_sites`,
so a future rebuild that caught a namesake elsewhere would fail rather than
draw a river in the wrong valley. Nothing else changed: the project page
already filters the layer by its own ΑΔΑ and already prints the mandatory
«© OpenStreetMap contributors, approximate» in its caveat when a river is
drawn.

**The drawn line came out broken, and the user asked whether that was the
data or a bug. It was mostly the bug** — two causes, both now fixed in
`build_river_layer.py`:

1. **`waterway=river` is not the river.** The builder filtered
   `way["waterway"="river"]`, but OSM tags a **4,1 km stretch of the upper
   Σπερχειός as `waterway=stream`** while still NAMING it — dropped, and
   that was the visible 3,5 km hole. The filter now takes **river OR
   stream**: the NAME pins the watercourse, the size class must not. (The
   Καλαμάς and Αχέροντας gained the same way — 133,2 and 69,4 km.)
2. **OSM leaves connecting stretches of the same course unnamed**, so a
   name-filtered query can never be continuous. The two river ways that
   carry the Σπερχειός between named stretches (27105313, 265629822) are
   now curated by OSM way id in `extra_ways`, each verified to meet its
   neighbours end to end (0,00/0,13 km and 0,24 km) — curation in the open,
   like every other judgment in this project.

Result: **86,0 km instead of 76,5**, and the two holes of 3,5 and 2,55 km
close to 0,13 and 0,24 km — invisible at card scale. **One ~1,15 km break
remains west of Λαμία and is the DATA**: OSM's two named ways there do not
meet (27105312 ends 1,15 km east of where 265627829 begins, in a
channelised, inconsistently mapped reach) and no way bridges them. Pinned
by `test_sperchios_course_is_continuous`, which fails if the length drops
or a bigger hole reopens. The fetch also gained retries — the public
Overpass mirrors 500/504 at random and a rebuild should not fail on a
passing cloud.

## 2026-08-24 · The VAT-less executors' note rewritten (user)

The two executing co-operatives that carry no canonical ΑΦΜ — ΔΑΣΕ
«Παντουρέ Δάσος Τρικάλων» (6Ι4Σ4653Π8-ΖΟΡ) and ΔΑ.Σ.Ε. Παπάδων
(9Κ9Τ4653Π8-Δ0Ο) — read «not in the ΔΑΣΕ dataset registry (no public
contract in the harvest window)», which described OUR harvest rather than
what the reader needs to know. The user's wording replaces it:
**«(mentioned in the completion act but it wasn't possible to match it
with a canonical Α.Φ.Μ.).»** Applied to BOTH rows, not only the page the
user was looking at: it is the same sentence about the same situation, and
both source acts are verified `oloklirosi` (completion) acts —
ΨΕΘΘ4653Π8-Ε1Γ and ΩΔΥΜΟΡ10-1ΝΟ — so the new wording is factually true of
each. The old technical detail is not lost: it moves to `curation_note`,
the audit-only field that is never rendered on a card (the 2026-08-16
rule). Rendering: a note that already opens with «(» no longer takes the
template's em dash, which would have doubled the punctuation. Curated JSON
and the committed sqlite both updated — the latter IN PLACE, as this
dataset's curated fields always are, because its harvest JSON lives only
on the build machine.

## 2026-08-24 · Two /anadohoi frames rebuilt: WHO DID THE WORK, FROM FIRE TO SPONSOR (user)

**WHO DID THE WORK** (was «The sponsors sign, forest co-ops dig: 13 of 68 act
trails name their executing crew»). The title carried the finding, against
the convention the rest of the site now follows — short caps, findings in
the lightbulb — and the frame ran to **922 px** for 13 rows because each
project was a two-line block. Now: the title is the plain caps one, the
numbers move into a computed bulb (13 of 68 trails, 18 co-operatives, and
the co-op that turns up under the most different sponsors — computed, not
typed), and the rows are **grouped by SPONSOR**, one dense line each. ΔΕΗ
alone held four blocks; grouped, 13 project rows become 8 sponsor rows and
the frame is **408 px — 56% less**, with nothing dropped: the co-op chips
still link to their ΔΑΣΕ profiles, and each project is a small numbered
link beside its region (the places are deduplicated — «R.U. Evia» printed
four times was the noise that made the row wrap).

**WHO DID THE WORK became a MAP the same day (user).** Asked whether a map
would serve better, the honest first answer was «only at Regional-Unit
precision» — because just 9 of the 23 links have a geocoded work site. The
user pushed back («for the 13 projects, we have the exact locations»), and
they were right: **every project carries a precise footprint once all three
of its sources are read** — the θέσεις its acts name (9 links), else the
digitised Β. Εύβοια works zone (6: the ΔΕΗ basins), else the EFFIS scar of
the fire it repairs (6: Χίος, Ρόδος). A Π.Ε. fallback is never needed. Read
one source only — as the first pass did — and the answer looks four times
worse than the data is. **21 of the 23 links draw**; the two that do not
are the co-operatives with no canonical ΑΦΜ, hence no seat, named in the
caveat rather than guessed at.

So the frame is now an arc map — each crew's registered seat (the ΔΑΣΕ
seat layer built the same morning) joined to the ground it worked, in the
FLOWS OF MONEY idiom, hovering a sponsor keeping only its crews — beside
the identity list the old table carried, **ranked by distance**, the two
columns ending together. **636 px against the original 922** (the map alone
at full frame width was 1.055 px: Greece is portrait, and the column width
is what sets the height).

The finding it exists to state, which no list could: **the crews travel.**
Median journey **273 km**, 15 of 21 links over 150 km, and ΔΑ.Σ.Ε. Αγίου
Δημητρίου Πιερίας crossed **672 km** to repair Rhodes — for two different
sponsors. It is the sponsored scheme showing the same pattern the /dase
duo measured that morning (37,4% of co-op money earned outside the home
region): a handful of mountain co-operatives serving the whole country.
Pinned by `test_crew_flows_pins`, including the anchor-source mix, so a
regression that silently drops the zones (which happened once — the layer
keys on `zone`, not `id`) fails instead of quietly coarsening the map.

**FROM FIRE TO SPONSOR** (was «Each big fire triggers a wave of corporate
sponsorship within weeks»). **The old title was not supported by the data.**
Measured against the EFFIS burn dates already linked to the projects, the
wait from fire to first designation act has a **median of 64 days** and runs
from **24 to 574**; only **9 of 18** fires drew a sponsor inside two months.
The bar-per-month strip it replaces could say nothing about that — it only
showed that acts cluster in autumn.

The new chart is one lane per fire event (18), sorted by burn date: the fire
as a maroon dot whose **area ∝ hectares burnt**, the **designation acts as
dots** where they fall, a dotted line for the **wait** between them, the
**fire season (1 May – 31 Oct) shaded per year** as the Anti-nero
procurement timeline shades it, and the lag in days in its own right-hand
column (printed beside the first act, the labels collided with the acts that
followed). Every act dot links to its project. The finding it states,
computed: **the wait tracks the fire's size** — Έβρος (96.610 ha) drew its
first sponsor in 26 days, ΒΑ Αττική in 24, Ρόδος in 29, while Κερατέα (546
ha) waited 574 and the 2021–22 Attica cluster 449.

Payload: `anadohoi_overview`'s `fires` entries gained `burn_date`, `burn_ha`,
`lag_days` and `acts[]`, the burn facts read from the EFFIS display layer the
maps already ship (`_effis_dates`, cached). Caveats stated on the frame: the
dates and areas are **EFFIS satellite estimates, not οριοθετήσεις**, and the
5 projects with no fire at all (plane-disease sanitation, salvage logging)
have no lane. Pinned by `test_fire_response_pins`, which asserts the median,
the range and that the biggest fire is among the fastest — so a re-harvest
that changed the story would fail rather than leave stale copy.

*Dress corrected the same day (user):* the crew map now wears the STATUS
map's own frame — the 640×620 crop with the shared MAP_VIEW, white regions
with the #8f8f8f stroke on the #f2f2f2 sea, the section hairline and zoom
hue — and **the EFFIS burnt areas are drawn under the arcs** (the same
`FiresLayer` the status map shows): every one of these works repairs a
fire, and the work dots now sit visibly ON their scars. Red therefore
belongs to the fires alone — the work dots turned ink (#333) — and the
mandatory EFFIS attribution joined the caveat. The legend lost its
explanatory first row («from each crew's registered seat …»): the entries
name the marks, the ⓘ and the caveat carry the method.

*Interaction corrected the same day (user, two notes):* the ranked journey
list and the sponsor chip bar are GONE — the identity appears when a dot is
chosen, in the site's own card convention (hover shows, click HOLDS with
the white rule + ✕, Esc or bare-map click releases; while a card is held
only that dot's journeys stay lit). A seat's card names the co-operative
(linked to its ΔΑΣΕ page — the page is the card's link, never the dot) and
the sponsors it worked for; a work dot's card names the sponsor and its
crews. And the per-journey kilometres are NOT written on the cards — the
arcs carry the distance visually, and the aggregate finding (median 273 km,
the 672 km Πιερία→Ρόδος journey) lives once, in the lightbulb.

*Third review round (user, five notes, all applied):* the region hover
cards are GONE (a Π.Ε. name says nothing on this map — `colorOf` only, no
`tipOf`); the map is the STATUS map's exact 640×620 frame in a
640px+panel grid; **the chosen dot's details print in a PANEL beside the
map** instead of a floating card (CO-OPERATIVE / seat / WORKED FOR with
region and year, or SPONSORED WORKS / EXECUTED BY — links to the co-op and
project pages live there); **no pan at the resting zoom** — a new PaperMap
`panAtRest={false}` prop refuses drags while k is at the applied view's
rest value, re-arming as soon as the reader zooms (default unchanged, no
other map affected); and a **YEAR slider** on the right walks the map
through time — burnt areas with yr ≤ the chosen year and projects whose
first designation act is ≤ it (the links carry `year` from the page's own
projects), the rest state showing everything. Colours: the projects turned
the section's dark green — all of them are completed works — and the
co-operatives' seats black; the legend swatches follow.

*Fourth note (user): the slider now DRIVES the zoom.* While it sits on a
year, the map fits the regions where that year's projects appear
(`PaperMap fitPesLive` — the Anti-nero drill's animated live refit, no new
machinery): 2021 lands on Β. Εύβοια and the Attica fires, 2024 on Ρόδος
(this map holds only the 13 executor-named projects, and ΒΑ Αττική 2024
names no crew). The display stays cumulative — everything up to the year —
only the CROP follows the period's new work; releasing the slider to its
right end returns to the country, and a year whose fires have no
executor-named project yet (2018–2020) keeps the country view, since there
is nothing to fit.

*Fifth round — the frame became EPISODES (user's brief: the reader must see
when the fires happened, how soon the projects appeared, and from where
the ΔΑΣΕ came; the right list must carry fire date · designation-act date
· sponsor · crew; cumulative dots while reframing confused; no panning;
«maybe a slider by day?»).* The day slider was considered and rejected:
fires are DISCRETE events, and 1.900 days of slider are almost all empty —
the honest navigator is the episode list itself, which IS the list the
user specified. One row per project, chronological by fire: the fire date
with its name (maroon), the act date with the wait printed («+44 d»,
green) and the sponsor, the crew names (black, linked to their ΔΑΣΕ
pages). Hovering a row previews it (the rest fades); CHOOSING it isolates
the episode — only its scar, its ground and its crews' journeys remain on
the map, hidden not dimmed — and the map refits to the episode's own
extent (ground + seats + scar bbox through PaperMap's reactive
`fitPoints`; view=null while chosen, the STATUS frame at rest). **The map
takes no gestures at all** (`interactive={false}`): the list is the only
wheel, which also retires the pan question. The rest state now draws only
the scars LINKED to these projects (each link ships its `scars` ids), not
every Greek fire since 2018 — the payload rows also gained `fire`,
`fire_date` (earliest linked EFFIS scar), `act_date` and per-project
`lag_days`, all computed. The year slider, the hover cards and the
`fitPesLive` wiring of the previous round are gone; PaperMap keeps the
`panAtRest` prop for any future interactive map that wants it.

*Sixth round (user, five notes, all applied):* **every fire since 2021
stays on the map** — the scars a project repairs in the deep maroon, the
rest a step lighter (#d8b6ba; two plain tones drawn directly, the
year-gradient FiresLayer left to the other maps), and while an episode is
held only ITS scar keeps the deep tone; the journeys are **thicker and
DASHED** (1.8→2.4 px, 6-4 dash — a route, not a border); the dots grew to
r5/6.5 and **lost the white outline** (the no-outline symbol rule); and
the episode rows are **LABELLED** — FIRE / SPONSOR APPOINTED / WORKS
EXECUTED BY in small caps with the marks' own swatches, the wait written
out («44 days after the fire») — so a reader who has never seen the page
can decode every line.

*Seventh round (user, four notes):* SPONSOR and its name moved to their own
labelled row (linking to the project page); the dots came down a step
(r 4 / 5,5 chosen) and the dashes thinned (1,4 / 2 px); the chosen
episode's journeys END IN AN OPEN CHEVRON pointing at the work — the FLOWS
OF MONEY arrowhead, `refX` pulled clear of the work dot so it never hides
under it — drawn, like the lines themselves, ABOVE the fire's fill; and
the MAP selects too: the ground dots, the seats (cycling through a seat's
episodes) and the dark scars (cycling through a scar's projects — the two
Rhodes projects share one) all answer to hover and click, mirroring the
list.

*Eighth round (user):* while an episode is chosen the journeys are a step
thicker (2,6px) and fully OPAQUE, and the chevron came down to the line's
own proportion with its point ON the work dot's rim. One rendering trap
recorded: `markerUnits="strokeWidth"` does not render at all on
`vector-effect: non-scaling-stroke` paths in Chromium — the marker is
sized in user units instead, divided by the zoom (screen-constant ~8px)
with a viewBox, `refX` pulling the tip back exactly the dot's radius.

*Ninth round (user):* the journey line thinned to nothing whenever the
crew's seat and the project were close — **the stroke was being divided by
the zoom while `vector-effect: non-scaling-stroke` already keeps it in
screen units**, so a tight pair (ΔΑ.Σ.Ε. Ακρίτα Αλεξανδρούπολης → ΔΕΠΑ,
10 km) fitted to a high k and left a hairline. The division is gone: the
line is a constant 1,4 px, 2,6 px while an episode is chosen, at every
zoom. Line and arrowhead are now #111 black in every state, and the
episode labels (FIRE / SPONSOR APPOINTED / SPONSOR / WORKS EXECUTED BY)
print black at weight 700 instead of faint at 900.

*Tenth round (user): the Κρυονέρι–Δροσοπηγή fire could not be seen when
selected.* The scar is present and correct (id 275494, 2025, **275 ha**) —
it is simply small, and the frame must also hold a crew's seat 273 km
away, so it projected to a few pixels. The SiteMap's own convention is
ported: a dark scar whose projected bounds fall under ~9px gets a
minimum-size maroon RING at its centroid, itself selectable — so a small
burnt area is never invisible. Two scars qualify at rest (Κρυονέρι 275 ha
and Κορινθία/Φενεός). Test note: clicking an episode row's centre lands on
the sponsor LINK and navigates, which is intended behaviour, not a bug —
the row's labels and dates are the neutral hit area.

*Eleventh round (user, five notes):* the minimum-size rings are gone —
instead **an episode whose burnt area is tiny becomes ZOOMABLE when
chosen** (`interactive={tinyScar}`, the scar's geographic span under 6% of
the fitted frame), with a line under the key saying «This burnt area is
small — click the map, then scroll to zoom into it»; every other episode
stays a still picture. The legend moved into the RIGHT column above the
list, two rows of two, reworded to «burnt areas connected with sponsored
works» / «sponsored works» / «other fires since 2021» / «forest workers'
co-op base», with the journey entry dropped; the map's own size is
untouched. The list now **follows the selection** — choosing an episode
anywhere (row, dot or scar) scrolls its row into view. A PaperMap bug the
zoom exposed: the `panAtRest` filter read the reactive `transform`, so the
zoom `$effect` re-ran on every zoom and re-attached the behaviour,
swallowing the +/− buttons; it now reads d3's own `zoomTransform(svgEl)`.

## 2026-08-25 · The two VAT-less crews get seats (user verdicts)

**ΔΑ.Σ.Ε. Παπάδων** is the **Αναγκαστικός Δασικός Συνεταιρισμός Παπάδων**
of **Παπάδες, ΒΟΡΕΙΑ ΕΥΒΟΙΑ** (δήμος Μαντουδίου–Λίμνης–Αγίας Άννας; OSM
village node 38,93194 / 23,36386) — which also explains its work: it dug
for ΔΕΗ on the Β. Εύβοια restoration, **13 km from home, the shortest
journey in the whole set**. Worth recording that the machine's candidate
was WRONG: OSM's only «Παππάδες» hit sat in Δ.Ε. Σιδηρονέρου, ΔΡΑΜΑ, and
the same ΔΕΗ act naming a Σιδηρόνερο co-op made it look corroborated. The
verdict was asked for rather than guessed, and a namesake 400 km away was
avoided. **ΔΑΣΕ «Παντουρέ Δάσος Τρικάλων»** keeps **Τρίκαλα** as its base
(39,556086 / 21,767884): no map carries the «Παντουρέ» forest locality, so
the seat is the prefecture town the co-operative's own name states, at
settlement precision — 153 km to its Coca-Cola work in Αχαΐα.

Curated as a `seat` block on the executor entry in
`anadohoi_projects.json` (place, lat/lon, Π.Ε., precision, source and the
reasoning), applied to the committed sqlite in place as this dataset's
curated fields always are; `anadohoi_crew_flows` uses it where a crew has
no canonical ΑΦΜ and marks the link `seat_source: curated`. **The map now
carries 23 of 23 links and nothing is off it** (was 21 + 2 named in the
caveat); the median journey stays 273 km and the >150 km count rises to
16. The `(mentioned in the completion act but it wasn't possible to match
it with a canonical Α.Φ.Μ.)` note stands — the seat is now known, the ΑΦΜ
still is not. Pinned by `test_crew_flows_pins`.

## 2026-08-25 · /anadohoi review round twelve (user)

RANKING OF COMPANIES took `#52b788` — the ΔΑΣΕ green — and now wears the
page's own `--c-anadohoi`. WHO DID THE WORK draws its journeys ONLY while
an episode is hovered or held: at rest the dashed lines pulled the eye onto
themselves and away from the burnt scars and the places, which is what the
frame is about (the legend carries a «hover or choose an episode to draw
its journey» row instead). WHO DID THE WORK and FROM FIRE TO SPONSOR moved
up to sit after PROJECT SCOPE and PROJECT TYPE, before the fires band. And
the designation-act page's EXTRACTED QUOTES FROM DOCUMENTS went behind the
Anti-nero contract page's own `Fold` — the sponsor dataset has no
procurement details and no CPV codes to fold beside it, a designation act
not being a procurement.

## 2026-08-25 · WHO THE SPONSORS ARE: the sponsors grouped by the kind of business they are (user)

**Decision.** The flat RANKING OF COMPANIES answers «who gave most» and
nothing else — 36 bars, each a single legal entity, no reading above the
line. A second frame beside it groups them into **twelve kinds of
business**, which is what makes the pattern visible: **49,3% of the
committed money is electricity and banking** — €12,78M from the four grid
and gas companies (ΔΕΗ, ΔΕΔΔΗΕ, ΑΔΜΗΕ, ΔΕΠΑ Εμπορίας) and €7,81M from the
three banks and one insurer — while three whole groups sit at €0: the two
timber companies, the two waste companies and the one consultancy commit
nothing in stated money across their 7 projects, because every one of them
promises «τη συνολική χρηματοδότηση» with no figure.

**The basis is SECTOR, never corporate ownership.** What a company does is
readable from its own registered name or from the act appointing it —
«Διαχειριστής Ελληνικού Δικτύου Διανομής Ηλεκτρικής Ενέργειας» says what
ΔΕΔΔΗΕ is, «ΣΤΑΝΤΑ Α.Ε. ΕΤΑΙΡΕΙΑ ΔΙΑΧΕΙΡΙΣΗΣ ΑΚΙΝΗΤΩΝ» says what ΣΤΑΝΤΑ
is. «Who owns whom» is a different claim: it needs per-company verification
against ΓΕΜΗ shareholdings, it changes under us between the act and today,
and it is exactly the kind of assertion this project does not make from
inference. Two consequences are stated rather than hidden: ΤΕΡΝΑ Α.Ε. and
ΤΕΡΝΑ Λευκόλιθοι Α.Ε. sit together in construction because both names
carry ΤΕΡΝΑ — the one ownership link visible in the names themselves — and
ΔΕΗ, ΔΕΔΔΗΕ, ΑΔΜΗΕ share the electricity group as three separate operators,
not as one corporate parent.

**Coverage.** 36 of 36 sponsors curated, 0 uncurated; every assignment
carries its verbatim `basis`. The mapping keys on the display names
`queries_extra._sponsor_group` produces (the same presentational merge the
ranking uses — ΔΕΗ/ΔΕΗ Α.Ε., ΕΛΠΕ/HELLENiQ, the Greek/Latin Lidl and
«ΕRΕΝ» pairs), so an uncurated sponsor cannot be silently dropped: it lands
in the payload's `uncurated` list and `test_sponsor_groups_pins` fails on
it.

**The groups are the user's, one round of review** (2026-08-25): the first
draft had nine, and two of them were holding unlike bodies under one name.
«Foundations & NGOs» split into **Charitable foundations** (Λασκαρίδης,
Κανελλοπούλου) and **Environmental NGOs** (WWF Ελλάς, Εταιρεία Προστασίας
Βιοποικιλότητας Θράκης) — a κοινωφελές ίδρυμα endowing a restoration and an
environmental organisation executing one are not the same kind of sponsor.
«Wood, waste & other industry» — a residual bucket, and the weakest label on
the chart — split into **Wood industry** (ALFA WOOD, ΑΚΡΙΤΑΣ, both
appointed for plane-disease sanitation), **Waste management** (GEOCYCLE,
ECORECOVERY) and **Planning & engineering** (ΔΟΞΙΑΔΗΣ ΠΛΑΣ, appointed for
the μελέτη). Two groups now hold a single firm; that is the honest reading,
not a defect — NOVA is the only telecoms sponsor in the scheme.

| group | € committed | projects | firms |
|---|---:|---:|---:|
| Electricity & gas networks | 12.775.923 | 13 | 4 |
| Banking & insurance | 7.814.679 | 6 | 4 |
| Oil & renewable energy | 7.054.405 | 10 | 2 |
| Property & tourism | 4.481.642 | 5 | 5 |
| Construction & materials | 3.543.765 | 8 | 6 |
| Charitable foundations | 3.100.000 | 3 | 2 |
| Consumer goods & retail | 2.295.165 | 9 | 5 |
| Telecoms & media | 580.000 | 4 | 1 |
| Environmental NGOs | 138.678 | 3 | 2 |
| Wood industry | 0 | 4 | 2 |
| Waste management | 0 | 2 | 2 |
| Planning & engineering | 0 | 1 | 1 |

Sorted by €, and the three €0 groups tie — so the count then the label
breaks it, or the order would shuffle on every load.

**Artifacts.** Curated `khmdhs/data/sponsor_groups.json` (`_groups` =
key→English label, `sponsors` = display name → group + basis) →
`queries_extra.anadohoi_sponsor_groups` → `sponsor_groups` on
`/api/anadohoi/overview` → `charts/SponsorGroups.svelte`, the frame WHO THE
SPONSORS ARE right after RANKING OF COMPANIES. Form (user's choice among
four sketched): **one bar per group, clicking it opens its member companies
underneath** on the same scale — compact at rest, and the long company
names are fully legible once opened. Every figure on the frame is computed;
the 49,3% in its lightbulb ships as `top2_share`. The 25 projects with no
stated sum are counted beside the € on every row («9 projects · 4 without a
stated sum»), so a €-only reading cannot quietly lose them.

**Second review round the same day (user).** Three corrections to the
drawing itself. (a) The group names were set in the display face at 700,
which printed them HEAVIER than the frame's own title (the serif h2 at
600) — they now take the ui face at its own weight, the capitals and a
0,08em tracking carrying the hierarchy instead. (b) The frame gained the
CONTRACT TYPE lens pair (`?sg=`): **«€ committed»** keeps the money with
the figure-less promises beside it, **«number of projects»** states a count
and nothing else, so one of the two is always the quick read; each lens
sorts by its own measure, which is the point — counted in projects the
order changes (consumer goods & retail rises 7th → 3rd, banking falls 2nd →
5th) and the three €0 groups stop being blank rows. (c) The graph left the
`.rankw` 3/4 cap and takes the frame's whole width, as PROJECT SCOPE's bar
takes its own frame's. Two magic constants died with the rewrite: the
label-fits-inside test and the reserved end column are both MEASURED now
(hidden spans bound to `clientWidth`, BarH's own technique) — a per-lens
constant would have been wrong at every other width, and the reserved
column differs sharply between the two lenses.

**Third round, same day (user): the two frames are a PAIR, and the pair
must be ONE SPECIES.** RANKING OF COMPANIES and WHO THE SPONSORS ARE sit
side by side in equal halves — PROJECT SCOPE | PROJECT TYPE's own layout —
which the data invites: the ranking is a top-12 and there are 12 groups.
The ranking's `.rankw` 3/4 cap went with it, and the grid is
`minmax(0, 1fr)`, never a plain `1fr`: the group rows' nowrap content
pushed the track past its half and the «equal» columns came out 590/1030.

Getting the right half to LOOK like the left took two rejected drawings,
and the verdicts are the record. The first wore the display face at 700 —
group names printed HEAVIER than the frame's own title. An interim fix
stacked each row (name above, bar below) when the names stopped fitting,
which the user rejected on sight: different letter weights left/right,
shorter bars right, names off the bars — the halves read as different
species. **The final rule: the group chart wears BarH's inside mode
verbatim** — the shared dress of every ranking on all three pages — 35 px
group bars, names INSIDE in white fs-13 with BarH's own two-line clamp
(«Construction & materials» wraps exactly as «Ίδρυμα Α.Κ. Λασκαρίδης»
does one column over), the value right after the bar in soft ink, no
table rules, no uppercase, member bars at 26 px in the pale tone. What
made room for it: the per-row «N projects · M without a stated sum» tail
is what starved the bars of length, so under the € lens it survives only
on the rows where the € say nothing (the three «—» groups print
«4 projects · no stated sum» in their empty row); the full counts are one
toggle away and the caveat carries the rule.

Trap recorded from the interim form: a layout that CHANGES the value
column's width must never decide that change by reading the live row —
stacking narrowed the column, the one-line form fit again, and the chart
oscillated until every width (names, longest word, value column) was
measured from hidden copies, BarH's own technique. The final form has one
layout, so it cannot oscillate; the measuring stays.

**Fourth round, same day (user): the arrangement.** WHO THE SPONSORS ARE
takes the pair's LEFT half and the ranking the right — the grouped
reading leads, the 12 single entities detail it. The group names print in
CAPS (same fs-13, no added weight — only the case tells a kind of
business from a company, and the hidden measuring spans wear the same
transform or the fit rules judge lowercase widths). Both halves put their
values at the row's RIGHT edge, table-style: the ranking via BarH's own
`valuesRight`, the groups via a `.tail` column (note · value · caret) so
a member's € lines up under its group's and the carets form their own
rail. Verified: nothing overflows the frame edge at 1440.

**Fifth round, same day (user): PROJECT SCOPE | PROJECT TYPE open the
page.** The pair moves ABOVE CURRENT STATUS OF PROJECTS — what the scheme
buys (scope, type) is read before how far it has come — and its titles
drop their `titleColor="#000"` override: the page rule already sets every
frame title in the dataset green, and the inline black was beating it.
The charts themselves were already the page's green and are untouched.

**Sixth round, same day (user): FROM FIRE TO SPONSOR tells the acts'
statuses.** «Do all of these designation acts have completion acts?» No —
of the 63 acts the chart draws, only **16** have an identified completion
act (7 are within deadline, 19 state no dates at all, **20 are past their
deadline with no completion act found**, 1 was revoked) — and one uniform
green painted a kept promise and a past-due one identically. Each act dot
now wears the **CURRENT STATUS OF PROJECTS palette** (the same
`ganttTheme` source as the waffle and the map, so the vocabularies cannot
drift): the payload's `fires[].acts[]` gained `st` — the waffle's own
bucket, `nodate` for an active project whose act sets no calendar
deadline — the dot's tooltip says the status in the waffle's words, and
the chart carries a second key row. What the colours now show: Τατόι–
Βαρυμπόμπη's thirteen acts are nearly all grey, Β. Εύβοια's ten are
mostly completed, the black revoked dot sits on ΒΑ Αττική 2024. Pinned:
16/19/20/7/1 in `test_fire_response_pins`.

**Seventh round, same day (user), the frame's dress:** the legend moved
ABOVE the chart (every other frame's convention — it was below), the two
text columns gained headers («FIRE» left, «DAYS TO FIRST ACT» right — the
key line that explained the right column died with it), the act dots lost
their white outline (the crew-map verdict again), and the year numbers
centred on the 1 January rule they belong to instead of hanging to its
right.

## 2026-08-25 · English fire names: the 19 event labels curated, the 76 EFFIS tokens derived (user)

**fire_events_en.json** — the curated `fire_event` vocabulary in English,
in the user's format: **cardinal words spelled out, the month as MM-YYYY**
(«North Evia, 08-2021», «Rhodes, 07-2023»), toponyms in the pe_names_en
approved forms where one exists — which is why «Κορινθία (Φενεός)» is
**Korinthia** (Feneos), not Corinthia. «πυρκαγιές Ιουλίου 2023 (πολλαπλά
μέτωπα)» becomes «Multiple fronts, 07-2023» so every label keeps the one
`Name, MM-YYYY` shape; «εκτός πυρκαγιάς» is «not fire-related». Keys are
the exact Greek labels — they ARE the Greek version's text, so the one
file serves both languages. Applied via `names.fireEn()` (exact-key,
honest Greek fallback) on FROM FIRE TO SPONSOR's lanes and tooltips, the
PROJECTS AND FIRES headings, the WHO DID THE WORK episode rows, the
lightbulb sentences and the project pages' FIRE EVENT fallback + html
title.

**effis_names_en.json** — the EFFIS display layer's 1,963 Greek `name`
fields turned out to be **comma-joined NUTS-3 names: 76 distinct tokens**,
not toponyms — so no per-feature curation exists or is needed. The token
map's Π.Ε. values are **pulled from pe_names_en.json at build time** (the
2026-08-15 user-reviewed vocabulary — one source, no drift); 4 literals:
Kea the island alone, «Κάρπαθος – Ηρωική Νήσος Κάσος» → Karpathos–Kasos,
and two names EFFIS already writes in Latin (Aktio-Vonitsa; Berat, a
cross-border scar in Albania). `names.effisNameEn()` translates a feature
name token by token; no surface prints scar names yet — the layer is
ready for the first one that does.

Both files live in `khmdhs/data/` with byte-identical copies in
`atlas/src/lib/data/`; `test_fire_names_en_pins` holds the copies
identical, the fire coverage against the live payload (a new fire without
a translation fails the suite), the EFFIS coverage against the committed
geojson, and the pe_names_en bond on the familiar forms.

**FROM FIRE TO SPONSOR widened** (the zoom question's first step, user):
the svg always stretched to the frame, so W 920 → 1120 buys a FINER grid
— one unit ≈ one CSS px, marks keep their pixel size and stop swallowing
each other, LANE 14 → 16. The user will judge whether zoom is still
wanted.

## 2026-08-25 · The fire lanes decomposed: an act answering several fires attaches to EACH (user)

**Decision (user verdicts ①②③, all accepted).** The lane/label unit of the
fire layer is the PHYSICAL FIRE, never an act's own grouping. Two acts
bundled several fires under composite labels — Maxima INSURANCE's 6ΟΗ7
(«Αττική 2021–2022 (Αγ. Στέφανος & Πεντέλη)»: 490 στρ. of the 03.08.2021
Τατόι–Βαρυμπόμπη–Αφίδνες fire + 516 στρ. of the 19.07.2022 Πεντέλη fire)
and ΔΕΔΔΗΕ's 9ΕΘΠ («πυρκαγιές Ιουλίου 2023 (πολλαπλά μέτωπα)»: five
fronts — Δερβενοχωρίων, Κουβαρά–Σαρωνίδας, Λουτρακίου, Αιγίου,
Φυλής–Πάρνηθας). Both are now decomposed: the composite labels are no
lanes, each act attaches to each of its fires with that fire's own scars,
and a multi-fire act draws one dot on every one of its fires' lanes with
the per-lane lag.

**Mechanism.** Curated `fire_events` list on the two projects in
`anadohoi_projects.json` ([{event, scars:[ids]}]; the other 67 need none —
the payload synthesizes a one-element list), new `projects.fire_events`
column (loader schema + validation extended; the committed sqlite migrated
in place), and `anadohoi_overview` iterates (project × fire event), each
membership sized by ITS event's scars only. New basis value **`act_front`**
for a scar the act's own front list names: Κουβαράς–Σαρωνίδα → the
17.07.2023 / 3.931 ha East Attica scar, Λουτράκι → 17.07.2023 / 1.272 ha
Κορινθία, Φυλής–Πάρνηθας → the 22.08.2023 / 6.057 ha fire the Πάρνηθα lane
already draws (verdict ①); ΔΕΔΔΗΕ's stray 27-ha near-match (218505,
1,02 km) was REPLACED by the act-front scars — distance guessed, the act
knew.

**Three new fire events** (verdict ②): «Κουβαράς–Σαρωνίδα, Ιούλ. 2023» /
Kouvaras–Saronida, 07-2023 · «Λουτράκι, Ιούλ. 2023» / Loutraki, 07-2023 ·
«Αίγιο, Ιούλ. 2023» / Aigio, 07-2023. The EN vocabulary is now **22
entries, all user-reviewed** — second review round the same day fixed:
Gerania (the Σχίνος dropped), «Chios, 06-2025 & 08-2025», «Korinthia's
Feneos, 07-2025»; the two composite entries stay as fallbacks for the two
projects' own records, never as lanes.

**What the decomposition changed on the chart** (all pinned): 19 lanes /
68 dots (was 18/63); **the median wait falls 64 → 51 days** because each
fire now measures to ITS OWN first act — Πάρνηθα's first sponsor is the
ΔΕΔΔΗΕ act (15 days, was 55), Πεντέλη's the Maxima act (99 days, was 225);
Κουβαράς–Σαρωνίδα and Λουτράκι waited 51 days, Αίγιο 45; Τατόι rises to 14
acts; Έβρος stays the biggest-and-among-fastest contrast (96.610 ha, 26
days); min 15 / max 574 / 11 of 19 within two months.

**Same day, the next review round (user).** (a) **Chios decomposed too**:
«καμένες εκτάσεις νήσου Χίου» covers BOTH 2025 fires — 22.06.2025
(6.349 ha) and 12.08.2025 (7.914 ha) — so the Εθνική Τράπεζα act attaches
to each («Χίος, Ιούν. 2025» lag 122 d, «Χίος, Αύγ. 2025» lag 71 d); 20
lanes / 69 dots, median 53,5 d, EN vocabulary 24 entries — all pinned.
(b) The chart's legend wears the page's tinted-strip dress (the status
key's / crew map's: #f2f2f2, radius 6, fs-13) in ONE strip above the
chart. (c) The left column prints the fire NAMES alone — the date is
where the flame sits on the timeline; the full label stays in the hover.
The two Chios lanes deliberately share the bare name and differ by their
flames' positions, which is the point.

**Same day, the honesty round (user): one act, one column of JOINED
dots.** After the decomposition a multi-fire act drew several visually
independent dots — countable as separate acts, which is misleading. The
fix is the UpSet convention: the act's dots all sit at the SAME date, so
a thin vertical TIE at that date joins them — Maxima's line runs
Τατόι→Πεντέλη, ΔΕΔΔΗΕ's through its five rows, the Χίος act joins its two
fires — and hovering any joined dot lights the whole act (tie to ink,
dots enlarged); the dot's card says «ONE act answering N fires». The
alternatives considered: a ring marker (weaker — says «special», not
«these belong together») and hover-only linkage (rejected — tooltips
never carry load-bearing information; the chart must be honest at rest).
The LEGEND restructured into THREE READING ROWS in the tinted strip (the
status key's own grid idea): what a row is (fire · wait · season), what
a dot is (the five statuses), what joined dots are (a two-dots-joined
glyph + the sentence) — height is cheaper than confusion.

**Same day, the coincidence round (user: «why is ΡΚΖ7 linked with
9ΕΘΠ?»).** They are not — ΤΕΡΝΑ's ΡΚΖ7 and ΔΕΔΔΗΕ's 9ΕΘΠ were both signed
06.09.2023, so on the Δερβενοχώρια row the two dots sat at the same
point, and the ΔΕΔΔΗΕ tie through that point looked like it grabbed both
acts. Fix: same-lane dots closer than a dot's width SPREAD horizontally
(≥6,5 px), the tie members PINNED at their true date and the loose dots
giving way — a tie therefore passes through exactly its own act's dots,
and a pushed dot moves a few px on the axis while its hover keeps the
true date. Side benefit: same-day acts that used to swallow each other
(the Τατόι and Β. Εύβοια clusters) now separate into countable dots.

**Same day, the truth-of-position round (user).** Three verdicts on the
frame. (a) The general near-day spreading was REVOKED — it drew dots at
dates that are not theirs. The only departure left is acts signed the
SAME DAY on one row, drawn a hair (6,5 px) apart because two objects
cannot share one point — the tie member keeps the true date, and the
legend states the convention in so many words. (b) In its place the chart
gained a **context strip** (the brush, «the disciplined kin of zoom»):
drag to frame a period and the chart rescales — near dots separate at
their TRUE positions, month rules (MM-YYYY) appear when the window is
short enough to give them room; drag the frame to move it, its edges to
resize, double-click for the whole period. The strip carries the full
timeline with season bands, year rules and one tick per act, so the
reader sees where the activity is before framing. (c) Hover NEVER
recolours a dot — black means revoked; hovering grows the act's dots and
inks its tie instead. And the LEGEND was rebuilt on the TIMELINE panel's
own organisation: a how-to-read-a-row SCHEMATIC (flame → dashed wait →
status dots, then the tie glyph with its caption and the same-day note)
beside the dot-status column and the season/right-column notes — one
tinted strip, fs-14, three clear regions instead of a run-on line.

**Same day, the legend's final trim (user, verbatim wording):** «fire
event» over the flame (sub-caption kept), «the acts connected to it»
aligned with it on the same line, the wait unlabeled (the dashed line in
the demo still shows it), the tie caption reduced to «one act for more
than one fire events», and the same-day and right-column notes deleted —
the DAYS TO FIRST ACT column header carries its own meaning.

**Same day, names and order (user wording verbatim):** WHO DID THE WORK
is retitled «FOREST WORKERS' CO-OP ENGAGED IN PROJECTS FINANCED BY
PRIVATE RESTORATION-REFORESTATION CONTRACTORS», FROM FIRE TO SPONSOR is
«FROM THE FIRE TO THE SPONSORED PROJECT», and the two swapped places —
the fire→act chart now precedes the crew map.

**Same day, the crew frame's final name (user review of the long title):**
«THE FOREST CO-OPS THE SPONSORS ENGAGED» — literal (only the co-op links
are shown), short per the title convention, paired with WHO THE SPONSORS
ARE — with the user's full wording as the SUBTITLE («forest workers'
co-operatives engaged in projects financed by private
restoration–reforestation contractors»). The lightbulb now LEADS with the
user's key finding: forest co-operatives appear in only 13 of the 68
sponsored projects — 19%, computed — the travel figures following.

## 2026-08-25 · The status map reads by ΠΕΡΙΦΕΡΕΙΑ (user)

CURRENT STATUS OF PROJECTS gained a lightbulb computing **projects per
REGION** — περιφέρεια, not Π.Ε. — and the map now answers at that level:
**clicking a region that holds projects zooms the map to its whole
extent** (every Π.Ε. of the περιφέρεια, PaperMap's animated `fitPesLive`;
✕ pill, Esc and bare-map click reset), and **hover highlights only those
regions**, lighting the περιφέρεια as one unit — the 22 Π.Ε. of the five
project-less regions are inert.

No new curation was needed: each Π.Ε. in `pe_names_en.json` carries its
Eurostat `nuts_id`, whose first four characters ARE the NUTS-2 region —
`transforms/regions.regionOfPe()` / `pesOfRegion()` derive the bridge,
the 13 English region names are presentation vocabulary in the
familiar-English doctrine, and a vitest pins the partition (74 Π.Ε. → 13
regions, no leftovers, round-trips). PaperMap gained the one optional
prop `peGroup` (Π.Ε. → group key or null=inert): hover lights every
member of the group, clicks fire only on members, and no other map
changes behaviour.

The computed reading (in the bulb, never hardcoded; user trimmed the
full arithmetic on review): **Attica and Central Greece alone hold 76% of
the 68 projects**, and the projects reach 8 of Greece's 13 regions — the
top-two share, the region count and the click affordance in one sentence.
The standalone «CURRENT STATUS OF PROJECTS» h2 became the frame's own
title (identical styling — the bulb needs the title row); the status
legend stays exactly as it was.

## 2026-08-25 · The copy doctrine applied to /anadohoi and /dase (user)

The Anti-nero front page's conventions (the 2026-08-23 copy pass) now
govern all three dataset pages: **the page says its BASIS once** in a
`.basis` line under the intro prose; **a LIGHTBULB states findings
computed from the payloads** — never how to read; **a CAVEAT is
frame-specific method and source the page has not already said**; **a ⓘ
carries the how-to-read** (beside the frame title via ChartFrame's `hint`,
or on a MAP label as the Anti-nero maps do).

**/anadohoi** gained its basis line (commitments not verified spending ·
net where the act states it, never converted · a figure-less promise adds
projects but no euros · restatements folded) — and the frames stopped
repeating it: RANKING's caveat died into the basis and the frame gained a
computed bulb (top sponsor share + figure-less count); WHO THE SPONSORS
ARE lost the basis clause and its «click a bar» tail moved to a ⓘ;
TIMELINE's ordering/click sentences moved from caveat to ⓘ, the caveat
keeping only «statuses as recorded on Διαύγεια, checked <date>»; CURRENT
STATUS moved the zoom/hover instructions from bulb and caveat into a MAP ⓘ
(the AntineroMap pattern); PROJECT SCOPE and PROJECT TYPE gained computed
bulbs (works-only split; the dominant kind) and one-clause method caveats.

**/dase** gained its basis line (stated net excl. VAT · cancelled +
superseded excluded · canonical-ΑΦΜ merge · even split · payments a
separate, structurally partial layer), the intro prose handing those
clauses over; MAP's «click a circle / click a unit» moved to a ⓘ;
AWARDING PROCESS split its long caveat — ribbon reading and hover to the
ⓘ, the middle-node merge / pooled node / consortium-at-lead staying as
method; CONTRACT VALUES moved the one-axis explanation to a ⓘ, dropped
the basis clause and gained a computed bulb (median vs largest);
RANKING's and ALLOCATION's basis clauses died into the basis line.

**Same day, the bulbs review (user, /anadohoi):** a bulb never RESTATES
what the chart prints (the sponsor-group and ranking bulbs dropped the
names and € their top bars already carry, keeping the shares and the
figure-less counts; SCOPE/TYPE bulbs became share + author reading); the
bulb icon wears the page colour (`.anap` now sets `--frame-accent`, the
mechanism the ΔΑΣΕ page already used); the `.rankpair` joined ChartFrame's
flows-above rule (the ranking's note used to open over its left
neighbour); the MAP and TIMELINE ⓘ were cut to one clause each — the
TIMELINE's keeps only «click a company's name…»; the status caveat lost
the dot counts the map itself shows; and the fire bulb took the user's
own phrasing — median days from the fire to the designation act since
2021 — with no named cases, which the lanes print themselves.

**Same day, the user's own bulb texts (/anadohoi), figures still
computed:** PROJECT SCOPE «In 60% of the designation acts, the private
actors appointed for the restoration or reforestation of an area are
responsible only for the works»; PROJECT TYPE has NO bulb; CURRENT STATUS
«53% of these projects are located in Attica and 16% in Evia. The
European Forest Fire Information System (EFFIS) mapped 1.161 burnt areas
in Greece since 2021; the sponsored projects cover 22 of them» — the
Attica share is the REGION, the Evia share the Π.Ε., a deliberate mix of
levels because both read as places; WHO THE SPONSORS ARE loses its ⓘ and
states the 49%; RANKING names the top sponsor and its 20%; the fire frame
and the co-op frame take the user's sentences verbatim, the latter
carrying the honest «no document naming them was found during this
research». Polish reported to the user: grammar in the SCOPE sentence,
«these projects» → «these areas» in the fire frame (the 11 of 20 are
fire-affected areas, not projects), and EFFIS spelled out. New deriveds:
`atticaPct`, `eviaPct`, `effisSince2021` (the fires layer's 2021+
features), `scarsAnswered` (distinct linked scar ids); the payload type
gained `scars`.

**Same day, the Anti-nero front page's bulb texts (user):** the user's own
wording where given, no bulb where the chart already says it, figures
still computed. ALLOCATION OF FUNDING now states the EVEN-SPLIT
convention in the open («no more specific allocation was found in the
documents sourced during this research») before the top region's share;
FLOWS keeps the one finding sentence; RANKING «as contracted» is one
clause, and the «by member firm» lens was rewritten as plain explanation
(what a joint venture is, what the lens does, why the undocumented
ventures' € are identical in both views) after the user found the old
text unclear. **Bulbs REMOVED** (the chart states it): AWARD PROCEDURES,
DIRECT AWARDS, CONTRACT VALUES, CONTRACT SCOPE, CONTRACT TYPE, TYPES OF
WORKS, MONEY PER YEAR, CUMULATIVE DISBURSEMENT. PROCUREMENT TIMELINE
keeps the user's two figures with the first sentence rephrased and the
per-lens tails dropped. The beeswarm's «largest» label moved to the top
margin at the plot's right edge — at the far right of a log axis it used
to run left across the dots and was unreadable.

**AWARDING PROCESS — the researched answer (user asked whether the units
are all political).** They are not, and the sharper finding is a
different one. The four ΚΗΜΔΗΣ operating units are: the **General
Directorate of Forests and the Forest Environment** (209 contracts,
77,6% of the money), the **General Secretariat for Forests** (19, 16,0%),
the **General Directorate for the Development and Protection of Forests
and the Agro-environment** (11, 5,2%) and the **Office of the Deputy
Minister for the Environment** (6, 1,1%). Two are political-tier bodies
— a Γενικός Γραμματέας is a μετακλητός appointee of the government
(ν.4622/2019), and a minister's private office is by definition his own —
and they awarded **17,1%** of the money; the two General Directorates are
headed by career civil servants selected through the merit procedure of
ν.4369/2016 and awarded **82,9%**. So «all directly connected with the
political leadership» is not supportable. What IS supportable, and is
what the bulb now says: **all four are units of the Ministry's own
central administration — not one of the 103 regional forest services that
supervise the works on the ground awards a contract itself.** A €622,5M
programme is contracted centrally and supervised locally.

**Same day, /dase bulb texts + the legal research the user asked for.**
ALLOCATION states the user's finding with the law behind it, VERIFIED:
«63% of the money … goes to co-operatives based in the region where the
works are. The forest code provides for exactly that: under **άρθρο 136Α
ν.δ. 86/1969, as added by ν.4423/2016**, the exploitation of public
forests is granted to co-operatives in an order of preference that begins
with those whose seat lies within the municipality of the works. Evia is
the notable exception — 64% of the work there was awarded to
co-operatives based elsewhere, in the restoration that followed the 2021
fires.» Sourcing: 59 of our own cached ΔΑΣΕ documents cite άρθρο 136Α
(the παρ. 3 penalty clause), and e-nomothesia's codified ν.4423/2016
gives the tier verbatim — «Η παραχώρηση στις πρωτοβάθμιες ΔΑ.Σ.Ο. γίνεται
με την ακόλουθη σειρά προτίμησης: α) στις ΔΑ.Σ.Ο, των οποίων η έδρα
υπάγεται στα διοικητικά όρια του Δήμου». Scope note kept in mind: 136Α
governs the παραχώρηση εκμετάλλευσης (the logging/firewood assignments),
which is the bulk of this dataset, not every co-op contract.

**Two of the user's proposed explanations were NOT printed, for cause.**
(i) «Compulsory forest co-operatives may not work beyond the forests they
own»: no such restriction was found in ν.4423/2016 άρθρο 46 or in Α.Ν.
1627/1939 as reachable, and — decisive — **no αναγκαστικός δασικός
συνεταιρισμός appears in this dataset's contractor population at all (0
of ~251 names)**, so the claim cannot explain Evia's imports here.
(ii) «Resin collectors absorbed by the ΔΥΠΑ programme could not take
works as freelancers»: **VERIFIED the same day from the ΚΥΑ the user
supplied** — αριθμ. **19895, ΦΕΚ Β΄ 956/02.03.2022**, «Ειδικό πρόγραμμα
απασχόλησης ρητινεργατών σε Υπηρεσίες του Υπουργείου Περιβάλλοντος και
Ενέργειας». Άρθρο 3 παρ. 2 sets the duration at **seven years** in
cycles; άρθρο 2 παρ. 2 makes **ΥΠΕΝ the φορέας υποδοχής**; άρθρο 2 παρ. 5
gives **€63.000.000 and 590 posts**; and **άρθρο 4 παρ. 1 περ. α** is
decisive: the beneficiaries are unemployed ρητινοκαλλιεργητές, **μέλη
Δασικών Συνεταιρισμών Εργασίας και Αναγκαστικών Δασικών Συνεταιρισμών**
active in the named δήμοι — among them **Ιστιαίας–Αιδηψού and
Μαντουδίου–Λίμνης–Αγίας Άννας of Π.Ε. Ευβοίας** — who keep their
membership **«εφόσον δεν ασκούν οποιαδήποτε δραστηριότητα στο πλαίσιο
αυτής της ιδιότητας»**. That clause is exactly the user's point: a
member hired into the programme may not work as a co-operative member,
and the pay is a full-time public post (άρθρο 2 παρ. 3-4, €1.000 gross
for 25 days). It is now the ALLOCATION bulb's «one documented reason»
for Evia's imported works, cited by ΚΥΑ number and ΦΕΚ.

Incidental to (i): the same ΚΥΑ names **Αναγκαστικοί Δασικοί
Συνεταιρισμοί** as co-ops active in those two North-Evia δήμοι, so they
exist there — but none is identifiable by name among this dataset's 629
registry spellings, and a compulsory co-op may register under a plain
name, so neither their presence nor their absence as CONTRACTORS can be
asserted from the names alone. CONTRACT VALUES keeps one sentence; MONEY PER YEAR and
RANKING OF CO-OPERATIVES lose their bulbs; both maps lose their ⓘ (the
dead `howToRead`/`whyWork`/`whySeat` helpers removed with them).

## 2026-08-25 · /compare opens with STATE-FUNDED, TWO WORLDS (user)

The SHARED COMPANIES parallel-pipelines frame confused its own reader:
its «1.534 contracts» was the ΥΠΕΝ-node subset of the 1.998 the hero
states (the ministry is the only SHARED awarder, but 464 co-op contracts
have other public awarders). The user's replacement dissolves the subset
by widening the true claim — ALL of it is state money — and turns the
frame into a three-step canvas animation (`StateFunded.svelte`,
`ParallelPipelines.svelte` PARKED):

1. **One mass** — all 2.243 contracts as dots, area ∝ stated net €, one
   neutral grey, packSiblings with the two sides interleaved before
   packing (sorted input would ring-segregate them and step 2 would
   reveal nothing);
2. **the colours** — each dot takes its programme's hue where it stands
   (Anti-nero #2b2b2b, co-op green);
3. **the recipients** — the dots drift into two packed clusters: 151
   private companies · €622,53M against 246 forest workers'
   co-operatives · €29,92M, the zero-overlap line closing the caption.

Auto-plays once on scroll-into-view; stepper + replay; reduced motion
gets the final state; dots hover (€ + ΑΔΑΜ) and click through to their
contract pages. The shared € scale carries a 1,3 px radius floor,
admitted in the caveat — at true scale the co-op contracts would vanish
beside the €11M dots, and that near-vanishing IS the finding the final
frame shows. Payload: `dots` on `/api/compare`
(`queries_extra.state_funded_dots`) — whole contracts, stated net, both
sums pinned to the bases to the cent (`test_state_funded_dots_pins`).

**Same day, the animation revised (user):** the opening mass is a loose
SEEDED SCATTER across the whole field, not a packed circle (deterministic
rejection sampling, biggest dots placed first, so every reader sees the
same field); the separation runs **year by year, 2021 → 2026**, each
year's dots flying in their own overlapping window with the year printed
large and faint while its dots move (the payload's `dots` gained a
per-contract `year`, signed-date with submission fallback, all 2.243
non-null 2021–2026, pinned); and the two destinations are NAMED from the
first frame — «private companies» / «forest workers' co-operatives» —
with the exact numbers (151 · €622,53M / 246 · €29,92M) appearing only
once the dots have divided.

**Third round the same day (user):** the end state is not two packed
circles — the dots ACCUMULATE BY YEAR, one horizontal band per year
(2021 at the top), each side wrapping like type from its column's inner
edge, and the years print on a Y AXIS only once the dots have settled.
Fixed-slice bands overflowed (2025 spilt into its neighbours), so each
band takes the height its own year needs — `wrapLines` shelves per
side, band `h = max(side heights, 22) + 12`, cumulative tops, the canvas
height derived from the last band (`canvasH`) and the year label at each
band's own centre. Captions are the user's verbatim: «every dot
represents a contract, area ∝ its stated value» / «Contracts that are
included in the Anti-nero programme are coloured black.» / «Allocation
of state funding via different contracts.» (the «two worlds — not one
recipient on both sides» line retired with the circles).

**Fourth round the same day (user: «this seems too forced… the dots of
different shelves could touch»):** the shelf-wrapped rows go — each dot
lands at a seeded RANDOM spot inside its year's strip (the opening
field's rejection sampling, its own PRNG stream, biggest first, 120
tries), one overlap grid spanning ALL strips so dots of neighbouring
years touch across the strip line; strip height comes from the year's
dot area at a safe random-packing density (EFF 0.42, floor 2·maxR); and
the years are flipped — **2021 at the BOTTOM, 2026 on top**, so the
year-by-year flight (still chronological) piles the money upward like
sediment. Bands carry their year; the y-axis labels print from the bands
themselves.

**Fifth round the same day (user: no scrolling to see title, chart and
caveat):** the frame compacted vertically — the destination labels ride
up right under the caption (`.lab` top 3.6em), the strips and the
scatter start at 64 (was 118/96), the scatter field is 560 tall (was
640) so the canvas is equally compact in every step, the bottom slack
is 6 px so the caveat sits right under the 2021 strip, and «replay» is
the ↻ symbol beside the step dots. The sweep numeral moved from the
top centre (now occupied by the 2026 strip) to the flying year's own
axis position at x 96 — it previews where the label will land.

**Sixth round the same day (user: the caveat gives nothing new):** the
caveat trimmed to its ONE clause that is stated nowhere else — the
radius floor (the caption promises area ∝ stated value; the floor
breaks that for the smallest contracts, and dropping the admission
would leave the caption overclaiming). The basis sentence is the page's
`.basis` line, and the «ΑΦΜ canonicalised» sentence supported the
retired zero-overlap claim — both gone.

**Seventh round the same day (user):** /compare's frame titles and
legends match the three dataset pages — a `.cmpp` wrapper gives every
ChartFrame title the kicker dress (display 900, fs-14, 0.08em; in the
INK, the hero kicker's own colour — the page has no dataset hue) and
sets `--frame-accent` to the ink for the bulbs; CONTRACT SIZES' legend
becomes the key strip of the dataset pages (grey #f2f2f2 rounded band
ABOVE the chart, fs-14, round dots), was a bare fs-13 flex row under
it. MONEY PER YEAR's side headings and REGION BY REGION's column heads
already matched.

## 2026-08-25 · Detail-page maps frame the whole Π.Ε.; controls everywhere (user)

**Decision.** On every contract and act detail page the map frames the
WHOLE regional unit(s) of the works: SiteMap and ZoneMap resolve the
containing Π.Ε. of every site pin and every linked EFFIS scar (d3
`geoContains`; the scar by its centroid), add the project's own stated
Π.Ε. (`pes` prop), and fit the union of those regions whole — the
geometry only extends the frame when it pokes beyond. This supersedes
the 2026-08-16 fire-framed window (scar bbox + 0.35°/0.27° floors,
width-fit shared among same-fire cards), which stays only as the
fallback while the Π.Ε. layer loads. Multi-regional projects therefore
show all their regional units; a border project's window is anchored on
Greece — Δαδιά used to show more of Turkey than of Έβρος.

**Controls.** Every detail map now carries the +/−/⌂ buttons: SiteMap's
are unconditional (they used to appear only on multi-site or fire maps),
ZoneMap gained the whole zoom/drag plumbing (it had none), and the two
contract pages' PaperMaps dropped `interactive={false}` — their +/−/⌂
stack starts below the MAP/DIAGRAM switch (46 px), and `fitPad` tightened
0.26 → 0.15 so a border Π.Ε. keeps its surround modest. Fixed en route:
SiteMap's component-wide `svg` rule (grey ground + hairline + radius)
was painting each zoom-button GLYPH as a bordered grey box — the reason
the sponsored-works buttons «did not appear well»; the glyphs now reset
background/border.

**Same day, round two (user):** SiteMap and ZoneMap also DRAW the
context now — they never loaded the neighbours layer, so a border frame
(the Έβρος projects) rendered Turkey and Bulgaria as open sea. Both
components load `neighbours.geojson` and follow PaperMap's conventions
exactly: context land white with the #c4c4c4 hairline coast under the
Greek polygons, Athos included, and the dashed black land border drawn
above the fills — with the neighbours in white, that line is what says
where Greece ends.

## 2026-08-25 · /authorities in the dataset pages' dress; one map, three populations (user)

The AUTHORITIES page redressed to the dataset pages' presentation:
kicker hero + `.basis` line, the harmonised KPI row kept, ChartFrame
sections with kicker titles and bulbs in the ink (`.authp`), the map on
the shared #f2f2f2 ground with ink zoom buttons, the legend as the key
strip above the map. **The map takes a mode switch** (`?show=`,
CONTRACT VALUES' segmented dress): Forest authorities (default) ·
Forest co-ops · Anti-nero contractors · All. The authorities lens keeps
the presence information the old legend carried, drawn legibly at last —
black dot = hosts Anti-nero works, GREEN CORE on the black dot = also
awards ΔΑΣΕ contracts (the old palette's «Anti-nero only» black was
indistinguishable from «both» ink), green = ΔΑΣΕ awards only, pale =
neither, hollow = the rest of the ΥΠΕΝ network. The co-op and contractor
lenses put each population at its registered office (dots link to their
pages); the ALL lens shows all three at once — authority seats in the
/dase map's forest-directorate green #406e55, co-ops in the ΔΑΣΕ green,
contractors in ink. Payload: `coops` + `contractors` on
`/api/authorities` (`queries_extra.authorities_map_points`): the co-op
dots are the 246 located registered offices of the live population and
their even-split € sum to the ΔΑΣΕ stated-net basis €29.920.558,46 to
the cent; the contractor dots are the 151 in-scope Anti-nero contractors
at their document-stated seats with display names overlaid
(`test_authorities_map_points_pins`).

## 2026-08-25 · NETWORKS OF ACTORS; the LOCATION row in English (user, third round)

**/authorities is NETWORKS OF ACTORS** (nav label, kicker, page title; the
route stays): the hero numbers drop to a modest size (`.stat .value`
fs-20), and the MAP is the page's key element — map left, and beside it
the list OF THE NETWORK THE MAP IS SHOWING (authorities with both
datasets' n·€ in their colours / co-ops by € / contractors by €; the ALL
lens gets a three-line summary), scrollable at the map's height, linked
to the dots by HOVER both ways (`hovKey` ↔ DotLayer `hotOf`; rows and
dots both link to the entity pages).

**The detail pages' left text carries no mixed Greek-English prose**
(user): the sponsored LOCATION row now prints curated English —
`khmdhs/data/anadohoi_locations_en.json`, 61 entries covering every
`location_text` in the DB (the 2026-08-16 proposal's conventions:
pe_names_en region forms, authority EN titles, «municipal unit of» /
«local community of», stremmata; toponyms transliterated), byte-identical
atlas copy, `names.locationEn()` with the honest Greek fallback, pinned
by `test_location_names_en_pins` (coverage + NO Greek script in the
values); the act's verbatim Greek stays in EXTRACTED QUOTES. The caveat's
θέση/κατά προσέγγιση/οριοθετήσεις became locality/approximate/
delimitation acts, and the map cards' «στρ.» qualifiers read
«stremmata» / «(approximate)». Entity names (companies, co-ops) stay
Greek by the standing decisions. The map's lower edge continues to track
the left column's end (`FactsHeader leftHeight` → map height — the
2026-08-16 mechanism, reconfirmed).

## 2026-08-26 · NETWORK OF ACTORS trimmed to map + searchable lists (user)

The page opens with the MAP frame — titled «NETWORK OF ACTORS» — and
nothing before it: the hero paragraph, the basis line and the KPI row are
gone (the basis facts moved into the map frame's caveat). Below it ONE
listing frame follows the map's `?show=` mode — FOREST AUTHORITIES /
FOREST CO-OPS / ANTI-NERO CONTRACTORS / ALL ACTORS — with a SEARCH box
(accent-folded, matches the English and the Greek registry spellings), so
the three populations are all listed on this page (they previously lived
only on /antinero/contractors and /dase/coops). The authorities table
drops the Greek «Δασαρχείο» chip (the English name already says the
kind), the column header reads «Regional unit», and THE REST OF THE
NETWORK section is gone — the 49 no-contract ΥΠΕΝ directory units fold
into the authorities list as muted dash rows, their address/contact
columns dropped. The 61 LOCATION translations went to the user as a
numbered review artifact («Location Register»); verdicts pending.

**Same day, the map corrected (user):** the frame is the crew map's
exactly (640×620, view centre 23.8305/38.3566, k 1.08 — THE FOREST
CO-OPS THE SPONSORS ENGAGED); NO outlines on any dot (`stroke="none"`
on every layer, and DotLayer's hot state keeps none when a layer asks
for none — the hover emphasis is the growth alone); and the forest
authorities wear ONE colour in every lens — the /dase map's
forest-directorate green #406e55 — because black in the authorities
lens turned into the contractors' black on the ALL toggle. The
authorities legend shrank to its three TRUE categories: «awards ΔΑΣΕ
contracts only» described nobody (measured 0 — no authority awards
co-op contracts without hosting Anti-nero works), and «neither» (2
registry services) merged with the 49 hollow directory units into one
pale «no contracts recorded in either dataset» — the old distinction
was provenance (contract registry vs ΥΠΕΝ directory), not meaning.

**Same day, round three (user):** the side list is EXACTLY as tall as
the rendered map (`bind:clientHeight` on the holder → the panel's
height); the no-contract grey darkened #cfcfcf → #a6a6a6 (it read as
sea); the ALL panel lost its «The three networks» heading and its
switch-hint note (self-explanatory); and the listing frame is PAGINATED
— the user chose page controls over top-N+search, region folds and an
alphabet index — 25 rows a page, a windowed «‹ 1 2 … 10 ›» pager per
table, search or a mode switch resetting to page 1; the authorities
table pages its registry rows and the folded directory units as one
sequence.

**Same day, round four (user):** the LEGEND moved into the right column
— its grey band's top edge flush with the map's upper hairline, ONE
full sentence per line («forest authority whose area hosts Anti-nero
works», «the light core: it also awards ΔΑΣΕ contracts itself», …)
instead of chip-speak, and in the ALL lens it carries the three
counts+Σ (the separate summary block died); the side list gained
COLUMN LABELS over its values (ANTI-NERO · ΔΑΣΕ / contracts · €) and
moved to fs-13, the legend at the key strips' fs-14 — the Anti-nero
page's sizes. And the three population lists are PERMANENT frames below
the map (FOREST AUTHORITIES · FOREST CO-OPS · ANTI-NERO CONTRACTORS,
each with its own search and pager) — behind the map's toggle the user
could not find the co-op and contractor lists at all.

**Same day, round five (user):** the three stacked list frames became
ONE frame with its own toggle (Forest authorities / Forest co-ops /
Anti-nero contractors beside one search on the title line; title and
caveat follow the selection, each table keeps its pager); the
authorities legend rephrased — the switch above already names the
population, so the lines describe the dot plainly («Anti-nero
contractors work on its territory» / «the light centre: it also
awards ΔΑΣΕ contracts to forest co-ops»); and the side list's column
labels print in the site's own spellings («Anti-nero» / «ΔΑΣΕ», no
caps transform) centred over their columns.

**Same day, round six — the legend texts are the user's verbatim:**
authorities lens «responsible for supervision of Anti-nero works in its
territory» / «…and contracts awarded to forest workers' co-operatives
in its territory» / «no contracts recorded in its territory within this
research»; ALL lens «105 forest authority seats» / «registered base for
forest workers' co-operatives (246 found within this research; the
official registry of the Ministry of Environment is not openly
accessible)» / «registered offices for contractors of the Anti-nero
works (151)» — the € totals left the ALL lines with them. Counts stay
computed; polish applied: workers's→workers', antinero→Anti-nero (the
site's spelling). The co-ops and contractors lenses wear the SAME lines
as their ALL entries, and the seats line reads «forest authority seats
(105)» — count in parentheses like its siblings.

## 2026-08-26 · The entity pages in the contract pages' dress (user)

The three entity pages — /antinero/contractor/[vat], /dase/coop/[vat]
and /authority/[slug] — rebuilt to the detail-page template the contract
pages set (user: study the contract pages, adjust aesthetics, letter
sizes, diagram sizing): `FactsHeader` with CAPS label/value rows and the
display name as the emphasised identity row, the map in the right slot
AT THE FACTS COLUMN'S HEIGHT (leftHeight → mapH, floor 420) in the
contract pages' map dress (#f2f2f2 ground, hairline, the page's
--map-accent, +/−/⌂), the provenance sentences gathered into the
CAVEAT under the facts, and CAPS `.plain` sections below (€ PER YEAR ·
CONSORTIUM PARTNERS · AWARDED BY · CONTRACTS …). KPI card rows and the
old h1 hgroups are gone — their figures became facts rows. En route:
the contractor page's €-per-year bars joined the Anti-nero
black-white-greyscale rule (they were the retired orange), the
authority caveat says «matched from the awarding unit's name» instead
of leaking the machine `match_basis`, and **the co-op page gained its
REGISTERED OFFICE row and map dot** — `dase_coop_detail` now attaches
`location` from the dase `contractor_locations` layer (2026-08-24),
the first page surface of the co-op seats layer
(`test_dase_list_and_detail` pins the new payload key).

**Why there is NO sponsor entity page** (user asked): the designation
acts name sponsors as free-text spellings with no ΑΦΜ or registry
number — 51 spellings collapse to 36 groups only presentationally, and
a merged label can span two legal entities («Coca-Cola (3Ε /
Hellas)»). A sponsor URL would assert an identity the documents cannot
prove; building one would first need a curated sponsor identity
registry (legal entity, ΑΦΜ, evidence per row).

## 2026-08-26 · The framed regional unit keeps only its RELEVANT parts (user)

The Δωδεκάνησα project 971Χ4653Π8-222 framed a window that was
mostly the Turkish coast and open sea, with Rhodes and its burnt area a
speck: **Π.Ε. Ρόδου carries Καστελλόριζο**, 1,3° east of Rhodes
(unit span 2,36° of longitude against Rhodes' own 0,56°), so the
2026-08-25 rule «frame the whole Π.Ε.» threw the frame across the sea.
The rule now reads: frame the parts of the unit that BELONG WITH THE
SUBJECT. `useGeo.nearParts(feature, subjectBBox, gap = 0.6)` splits a
Π.Ε. into its polygon parts and keeps those within
`max(0.6°, 1.5 × subject span)` of the subject's own extent — the
nearest part always survives, so nothing frames on emptiness, and with
no subject the LARGEST part anchors. Wired into every framing path:
SiteMap and ZoneMap (subject = the sites/scars/zones), PaperMap's
`fitPes` (subject = the fitted points, e.g. the authority seats),
`zoomToFeatures` (the /anadohoi region zoom) and `zoomToFeature` (the
front-page drill). Measured effects: the Rhodes project frames Rhodes
with Σύμη/Χάλκη/Τήλος and the Turkish coast only as the natural
northern edge; Π.Ε. Έβρου KEEPS Σαμοθράκη (0,49° from the Dadia
scar, inside the reach); a genuinely multi-region contract
(22SYMV010856521: Γρεβενών + Λέσβου + Σάμου) is unchanged, every
unit still in frame. The trade-off is stated plainly: an outlying
island further than the reach is no longer drawn into the WINDOW — the
data layer and the region highlight are untouched. Pinned on the real
layer by `maps/nearParts.test.ts`.

## 2026-08-26 · The LOCATION layer goes BILINGUAL (user)

The sponsored projects' LOCATION row is curated in BOTH languages: each
act's raw `location_text` maps to `{el, en}` — the Greek version shows
`el`, the English one `en` — replacing the 2026-08-25 English-only file
(same path, `anadohoi_locations_en.json`, both copies byte-identical;
`names.locationEn` / new `names.locationEl`, honest fallback to what the
act wrote; the pin now requires both fields, Greek script in `el` and
NONE in `en`). **Rows 1–12 are the user's own wording**, three
corrections applied and reported: (a) rows 9/10/11 converted στρέμματα
to hectares wrongly — the acts state 11.124 / 13.626 / 8.900 στρεμμάτων,
i.e. **1.112,4 / 1.362,6 / 890 ha**, not «11,124 / 13,626 / 8,9 ha»
(1 στρ = 0,1 ha, as the user's own row 1 has it); (b) row 11
«Prikrodafneza» → «Pikrodafneza» (Πικροδαφνέζας); (c) row 12
Μάνδρας-Ειδυλλίας is ONE municipality, so the English lists three, not
four. Rows 13–61 follow the twelve's patterns, each read from its own
act — which also let two bare fragments say more than the registry
stored: row 39 «περιοχή του Έβρου» is the settlement of **Παλαγία**, and
row 43's Surface 2 is **Ραπεντώσα–Μαραθώνα**. Areas print only where the
act's own location clause states them; row 46 carries none because the
act says 14,410 στρ. where the curated field says 16. Every verdict is
reviewed against the act's sentence in the «Location Register» artifact,
which now prints the act's sentence, the GR text and the EN text per
row.

**Reviewed to completion the same day** (rounds 2 and 3, user): fifteen
more verdicts verbatim and their patterns propagated — no
municipality-genitive chains («Δ.Ε. X, Δήμου Y, Π.Ε. Z» → «X in Y»),
«burnt» never «affected», «fire-affected» for πυρόπληκτη, «forested
area» for «έκταση δασικού χαρακτήρα», the forest service named only
where the act's own clause does (41, 42). Three more corrections
reported: row 25 gains the act's SECOND area («Βίγλα» of Δήμου
Παλλήνης, 10 στρ. = 1 ha, verified in the act) worded as «an area
DESIGNATED for reforestation» — αναδασωτέα is land declared for
reforestation, the opposite of «reforested»; «Palini» → «Pallini»
(Παλλήνη); «juristiction» → «jurisdiction» (as in rows 2 and 6).
Rows 41/42 name the service in the curated
`authority_names_en.json` form («Lamia / Spercheiada Forest Service
Office», user-confirmed) so one service reads the same on every surface.

## 2026-08-26 · The co-op page settled; the map/diagram switch joins the site's toggles (user)

Round after the entity-page redress, all user calls: the ΔΑΣΕ co-op page's
facts read **NAME · ΑΦΜ · IN THE REGISTRY AS · REGISTERED OFFICE**, then
**TOTAL € AWARDED · CONTRACTS AWARDED · ACTIVE PERIOD** — the English
name row and the «· ΔΑ.Σ.Ε.» form after the ΑΦΜ are gone (the FORMS table
with them), money and count are separate rows, and the labels are short
enough to sit level with their values. AWARDING UNITS and CONTRACTS are
`Fold` sections that arrive CLOSED (open folds were «too much noise»), the
contracts list is date · ΑΔΑΜ · value (the unit lives in AWARDING UNITS),
and the row below the header shares FactsHeader's own two columns so
AWARDING UNITS starts at the map's left edge and shares its width. The map
binds the slot's width like the contract pages (measured: 458 px on both,
where the co-op map used to be hard-coded 460), frames the seat's own
Π.Ε. through `fitPes` (it framed nothing before, so it drew the whole
country and pulled in the Turkish coast), and ONLY the registered-office
dot answers the pointer — the regions lost their card and their hover
stroke.

**The seat in English** (user: the facts row cannot mix Greek and
English): curated `dase_coop_seats_en.json`, the 271 distinct
village/town strings of the 246 co-op seats transliterated with the
repository's own ISO-843 helper, title-cased, «ΑΓ» expanded to
Agios/Agia/Agioi by the following word's gender, «ΧΙΛ»→km, «ΤΘ»→PO Box,
«ΕΝΤΟΣ ΟΙΚΙΣΜΟΥ» dropped; byte-identical atlas copy, `names.placeEn()`
with the honest Greek fallback. MACHINE-PROPOSED, awaiting the user's
review like the LOCATION layer. Where the village and the post town are
the same word it prints once, and the regional unit is not repeated.

**The MAP/DIAGRAM switch** now wears the site's segmented-toggle dress
(one bordered pill, active segment filled, fs-13) instead of two small
caps chips, and sits to the LEFT of the map's +/−/⌂ stack, which returns
to its usual top-right corner — on the Anti-nero AND the ΔΑΣΕ contract
page, since they share the switch.

## 2026-08-26 · The Anti-nero contractor page joins the pattern (user)

The contractor page rebuilt on the co-op page's terms, all user calls:
facts read **NAME · ΑΦΜ · IN THE REGISTRY AS · REGISTERED OFFICE · ΓΕΜΗ**,
then **TOTAL € AWARDED · CONTRACTS AWARDED · DIRECT AWARDS · ACTIVE
PERIOD** — one fact per row, the counts that used to ride as grey tails
now rows of their own. **SINGLE-BID CONTRACTS is not shown** (that
information has not been worked on) and **CONSORTIUM CONTRACTS prints
only when non-zero** — it read «0» on a κοινοπραξία, which is true (the
venture signs alone under its own ΑΦΜ) and misleading. REGIONS WORKED IN
went too: the map says it. The seat prints in English from the curated
place layer, its provenance and verbatim Greek clause moved to
**EXTRACTED QUOTES FROM DOCUMENTS** where quotations belong.

**The map lost its colour ramp and legend**: the regions worked in take
one flat tone, the office dot the page's own ink (it was a stray
blue-green that contradicted the legend's black ●), and the per-region €
stays in the hover card. Sections are closed folds; **€ PER YEAR and
CONTRACTS share one row** on FactsHeader's own columns, so the contracts
table lines up with the map above it; the list is date · ΑΔΑΜ · value.

**No procurement block here** (user, after trying one): a
«Forest authorities» section where «Awarded by» had been implied the
forest services award the contracts, which they do not — the Ministry
does, through its General Secretariat, and the services supervise the
works on their territory. One combined PROCUREMENT DETAILS block was
built and then removed on the user's call: the contract pages tell that
story better. `contractor_authorities` / `contractor_awarding` and their
payload fields were deleted with it rather than left travelling unused.

The place layer merged: `place_names_en.json` (476 entries) replaces
`dase_coop_seats_en.json`, covering the co-op villages AND the
contractors' street addresses (ordinals «107th km», «Ε.Ο.» → national
road, «Λεωφ.» → Leoforos). Still machine-proposed, awaiting review.

## 2026-08-26 · The forest-authority page joins the pattern, and the place layer covers it (user)

The third entity page rebuilt on the same terms as the co-op's and the
contractor's. Facts read **NAME · IN THE REGISTRY AS · OFFICE · REGIONAL
UNIT**, then the measures, one fact per row — **ANTI-NERO WORKS
SUPERVISED · ANTI-NERO CONTRACTS · AWARDED TO FOREST CO-OPS · ΔΑΣΕ
CONTRACTS AWARDED** — each pair printing **only when it is not zero**
(the contractor page's rule: a «0,00 €» row is true and misleading). A
service with neither side says so in one sentence under the map instead
of carrying a heading over an empty grid, because the network page's own
legend distinguishes «no contracts recorded in its territory». The two
halves are one `.pair` row each on FactsHeader's columns — the entities
on the left, the contracts in a CLOSED fold aligned with the map above,
date · ΑΔΑΜ · value — the Anti-nero fold in the black accent, the ΔΑΣΕ
one in green. The ranking now prints the **curated contractor display
names** (`overlay_contractor_names` on `top_contractors`): the authority
page is a contractor surface like any other, and it had been showing raw
registry spellings.

**`covers_pe` reaches the database.** The curated registry has always
carried the Π.Ε. a service administers beyond the one its office sits in
(8 entries: Δωδεκανήσου→Κω, Κεφαλληνίας→Ιθάκης, Σάμου→Ικαρίας,
Αιγάλεω/Πάρνηθας→Δυτικής Αττικής, Πειραιά→Νήσων, Πεντέλης→3 Attica
sectors, Φουρνάς→Καρδίτσας), but `forest_loader` never stored it, so the
page could only frame the seat's own unit. Now a `covers_pe` column
(CREATE + the ALTER guard, « · »-joined) feeds `authority_profile`, and
the map **fits the whole jurisdiction**: seat unit at 30% of the
authority green, administered units at 14%, the office dot on top. The
facts row reads «Regional units administered» when there is more than
one. Δασαρχείο Πεντέλης is the case that shows it — one Attica sector
before, four now.

**The place layer covers all three entity pages** (648 entries, was
476): the forest authorities' office streets and post towns joined the
co-op villages and the contractor addresses, and the generator moved out
of scratch into **`scripts/build_place_names_en.py`**. The authorities'
addresses exposed rules the first pass lacked, each now pinned in
`tests/test_body_names_en.py`:

- an ordinal turns English **only before «χλμ»** («107th km») — a street
  named after a date keeps the form its own sign carries («25ης Μαρτίου»
  → «25is Martiou», never «25th Martiou»);
- Python uppercases «Τέρμα» to «ΤΈΡΜΑ», so every accented key missed:
  the lookups **fold accents** before matching (the repository's standing
  Greek-matcher trap, hit again);
- a hyphen or a dot inside a token starts a new place name
  («Komotinis-Alexandroupolis», «Pl.Kampanas») but a run after a **digit**
  is that numeral's suffix, not a word;
- «ΑΓ» takes the case of the word it qualifies — Agios / Agiou / Agia /
  Agion — because in a street name it is a genitive;
- what a building **is** gets said rather than transliterated
  («Διοικητήριο» → Administration Building, «Δασικό Φυτώριο» → Forest
  Nursery, «Περιφερειακή Οδός» → Ring Road, «Τέρμα» → End of), and the
  ΥΠΕΝ tables' abbreviations expand («Κων/νου» → Konstantinou, «Μεγ.» →
  Megalou);
- «Οδός» is dropped as a bare word except before an article, where it is
  the street's own name («Οδός των 118»).

A new guard asserts that **every office string the three pages print has
an English form** — a page may never mix the two alphabets in a facts
row. All 648 values stay MACHINE-PROPOSED and await the user's review
(register published 2026-08-26); the Greek remains the stored value and
the evidence everywhere.

## 2026-08-26 · ΕΛΟΤ voicing, and the three lists become one (user review)

**Four corrections on the place register, three of them one rule.**
ΕΛΟΤ 743 voices αυ/ευ/ηυ as av/ev/iv only before a vowel or a voiced
consonant (β γ δ ζ λ μ ν ρ); before a voiceless one (θ κ ξ π σ τ φ χ ψ)
or at the end of a word they are **af/ef/if**. `geocode_loader._translit`
maps them blindly — it was written to build Nominatim queries, where the
distinction does not matter — so «Ελευθερίου» printed «Elevtheriou»,
«Ευκαρπία» «Evkarpia» and «ΠΕΥΚΟΦΥΤΟ» «Pevkofyto», all three caught by
the user. The rule now lives in the DISPLAY layer
(`scripts/build_place_names_en.py`), leaving the geocoder's helper and
its cached hits untouched: **18 entries changed**, including the familiar
forms Lefkada, Nafplio, Nafpaktos, Pefka, Lefkogeia, Kallipefki. The
fourth: «ΘΕΣΗ Χ» is punctuation, not a word — «ΘΗΒΑ ΘΕΣΗ ΧΟΡΟΒΟΙΒΟΔΑ»
reads «Thiva, Chorovoivoda», and a leading «θέση» simply drops.

**Why not Google Maps** (user's question): it has no open, keyless name
API, and its data may not be redistributed into a curated file. OSM does
and may, and it is the gazetteer this project already geocodes with — so
the settlement names are cross-checked against the map's own `name:en` /
`int_name` tags, reverse-geocoded from the points we already hold
(`namedetails=1`). It is a CHECK, never an overwrite: a disagreement is
a question for the user.

**What the check was worth**: 257 settlement strings, 212 carrying an
English/int name in OSM, **174 «differences» — and almost all of them
noise**: the stored point is a village address, and a reverse geocode at
zoom 14 answers with whatever place polygon contains it, often the
neighbouring hamlet. OSM is not a name source here. It did, however,
catch **four real bugs of the abbreviation dictionary**, which is what a
cross-check is for: «ΝΕΟ» was expanding to «New National Road» in
«Νέο Ψυχικό», «Νέο Ηράκλειο» and «ΝΕΟ ΠΕΤΡΙΤΣΙ» (it means the road only
where a «χλμ» has just been said, or where the writer dotted it), and
«Μεγ.» was always «Megalou», turning «ΜΕΓ ΠΑΝΑΓΙΑ» into «Megalou
Panagia» — it now takes the gender of the word it qualifies. Four
single-letter abbreviations no rule can reach («Ν ΜΑΓΝΗΣΙΑ», «Ν
ΠΕΤΡΙΤΣΙ», «Κ ΝΕΥΡΟΚΟΠΙ», «Κ ΠΟΡΟΙΑ») became hand verdicts in the
generator's `OVERRIDES`, confirmed against OSM's own names.

**And the familiar-English rule reaches the settlements.** The user ruled
on familiar forms for the Π.Ε. names in 2026-08-15 (Rhodes, Corinth,
Heraklion, Piraeus, Corfu …); a settlement of the same name must read the
same way, or the site says «Rodos» on one page and «Rhodes» on the next.
Seven strings adopted the ruled form. 15 entries changed in all, pinned
by `test_place_review_verdicts_pinned`.

**Round 2 of the review: one row.** «Οδός των 118, αρ. 37» — the Chios
street named after the 118 exiles — reads **«118 Str. no. 37»** by the
user's own wording; no rule reaches a street whose name is a number, so
it joins `OVERRIDES`. Everything else in the 648 rows passed the user's
read.

**The forest-authority facts lose IN THE REGISTRY AS and the contact
details** (user): the office row is an address, not a contact card, and
the Greek name rides as the identity row's hover title. Every other
authority-name surface still shows it.

**/dase/coops and /antinero/contractors fold into NETWORK OF ACTORS**
(user): the same three populations were being listed in three places.
The list lens moved into the URL (`?list=coops|contractors`, `#list`),
the two routes became **308 redirects** carrying `?q=` across so old
links and bookmarks land on the right lens, and the entity pages' crumbs
point there. Nothing was lost in the move except **single-bid contracts**
(the user's standing rule: that information has not been worked on) —
the ΑΦΜ column and the by-€ / by-contracts / by-name sort the standalone
pages carried are now on the network list too.

## 2026-08-27 · The front door: a field of codes, a story, a hub and three cards (user)

The site was a set of analysis pages behind four tabs; the user studied
Common Wealth's «Who Owns Britain» (one door, a data branch and a story
branch) and drew five mocks. Built as a skeleton the user now fills:

**The landing at `/`** has three states on one URL. **A** — a
full-viewport field of every identifier the site holds, written
vertically one glyph per line in ~60 columns (32 px pitch, 14 px lines)
drifting up and down at their own speeds, **each code in its dataset's
colour** (user decision: Anti-nero black, forest co-ops green, sponsored
works its hue — the field IS the data, and the honest proportions mean
mostly green: 3.685 of the 4.496 codes are ΔΑΣΕ). **B** — the title
fades in 1,8 s after the first frame. **C** — a click on the title
collapses the field into the top-left cell of a 4×4 menu (a transform
of the fixed stage into the cell's rectangle, 0,75 s; the cell then
carries its own denser field) and the page becomes title · standfirst ·
credit on the left, the grid on the right: START HERE, EXPLORE THE DATA,
METHODOLOGY, the other cells empty for now (`lib/landing/homeCells.ts`
is the cell map). The brand link returns straight to C (`/?menu=1`), a
session that has seen C lands on it again (sessionStorage `sf.landing`),
↻ in the cell replays with a fresh seed, and prefers-reduced-motion
opens on C with a still field. Layout is pure (`lib/landing/field.ts`,
seeded mulberry32 — now shared from `lib/transforms/prng.ts`), vitest-pinned.

**The codes come from `/api/landing`** (`queries_extra.landing_codes`):
every record of the in-scope Anti-nero chains (305 = the 245 tips and
their superseded versions) with the calls, awards and requests their
registry family and their own texts cite (298); the live ΔΑΣΕ contracts
with their superseded versions (2.062) and their upstream acts (1.623);
the designation-act trail of every live sponsored project (208) —
**4.496 codes, globally distinct, payments deliberately out** (their own
layer). 82 KB raw, 20 KB gzipped, memoised like every GET; degrades when
a DB is absent; pinned by `test_landing_pins`.

**`/` is no longer the Anti-nero overview.** It moved to `/antinero`
(the alias that redirected the other way is gone). Every permalink the
old front page minted keeps working: its query forms (`view focus sel
selv flows money net chord rank ct`) are forwarded by the landing's
loader with their parameters, its hash forms (`/#flows`) by the landing
after hydration — `lib/transforms/legacyRoutes.ts`, pinned. The
methodology's «front page» link follows.

**EXPLORE THE DATA → `/data`**, the hub: title, one caption line, the
three streams as large symbols and the two tools (search = /explore,
network of actors = /authorities) smaller beneath. **The five symbols
are ONE list** (`lib/datasets.ts:SYMBOLS`) feeding the hub, the header
and the cards; the labels are the mock's placeholders until the user
names the streams, and `DatasetSymbol.svelte` is a bordered square until
the user's images arrive — one file to swap.

**Each dataset page is a CARD** (`lib/ui/DatasetCard.svelte`): the
symbol, the stream's name, the narrative and «explore more» on the
left; three KPI cards on the right (`lib/ui/KpiCards.svelte` — the recipe
the four heroes hand-rolled, extracted once); then the dataset's key
frames at the page's full width — **one deviation from the mock, which
puts them beside the text**: the frames keep the widths they were drawn
for (the Anti-nero allocation map is a pair of maps), which an
800-px column cannot hold. «Explore more» unfolds the rest below on the
same URL (user decision); the state is READ from the URL — a frame
anchor or one of the page's chart lenses opens unfolded — and the
button sets `#more` (`lib/ui/expanded.ts`, pinned). Key frames: sponsored
= CURRENT STATUS (the map), TIMELINE, WHO THE SPONSORS ARE (the mock's
three); Anti-nero = ALLOCATION OF FUNDING, RANKING OF COMPANIES,
PROCUREMENT TIMELINE and ΔΑΣΕ = ALLOCATION OF FUNDING, MONEY PER YEAR +
RANKING OF CO-OPERATIVES — **defaults, the user's call**. The hero's
programme-figure bars (direct-award share, single bids, paid) are not
KPI cards and open the unfolded part as PROGRAMME / CONTRACT FIGURES;
the hero's computed prose and basis line sit under the markdown in the
card's text column. Every frame kept its markup, anchor and lens; the
restructure script proved by multiset that no line of the old pages was
lost.

**The header** is the brand on two lines, the five symbols (the current
one filled) and METHODOLOGY; the four tabs and the MENU dropdown are
gone; the landing carries no chrome.

**START HERE → `/story`**, the scroll the user writes next. Phase 1 is
the skeleton: a chapter menu and ten chapters (`lib/story/chapters.ts`,
placeholder titles), each reading its markdown; **KEY FINDINGS is a
chapter** — the five frames of `/compare` moved into
`lib/sections/KeyFindings.svelte` with their anchors and dress, and
`/compare` redirects to `/story` (a browser carries the fragment across a
redirect whose Location has none, so `/compare#pe-scatter` lands on the
same frame).

**Narration lives in markdown the user edits** (user decision): mdsvex
is the one new dependency, wired in `vite.config.ts` (`extensions`,
`preprocess`, the `$content` alias; `src/content.d.ts` types `*.md`);
`atlas/src/content/{landing, data, datasets, story}/*.md`, each seeded
with one placeholder line, rendered through `lib/ui/Prose.svelte`, which
in dev prints the file path behind an empty slot.

No colour, font or chart changed. 611 python tests, 144 frontend units.

**Second round the same day — the cards are VIEWPORT compositions.** The
user pointed out that the mocks and «Who Owns Britain» also set the
zoom extents and the allocation of graphs: a card is one screen. The
first build stacked the full frames under the text (4.352 px on the
sponsored page). Now `main` is window-wide on the three dataset pages
(`main.card`), the text column runs the full height on the left with
«explore more» at its foot, the three KPI cards span the top of the
right, and under them the key charts are compact **TILES**
(`lib/ui/Tile.svelte`, `--paper-2` panels, content scrolling rather than
growing) in the mock's grid — MAP top-left, the tall one right, the
third under MAP — sized to the viewport (`calc(100dvh − header − KPI
row)`, floor 560 px). Every page measures 1.224 px at 1920×1080. The
tiles are compact drawings of the same data (the sponsored status map
with its EFFIS scars and status dots, the Gantt in a scroll box, the
sponsor groups; the Anti-nero and ΔΑΣΕ tiles a one-tone € choropleth by
regional unit, the ranking, money per year), each titled with a link to
its full frame; **«explore more» unfolds the WHOLE original page** —
every frame in its original order, the hero's figure bars first — so the
analysis pages are exactly what they were, under the card. The pages
were rebuilt from git HEAD by `cards_v2.py` with the multiset guard.

**Third round the same day (user).** (1) The three cards **do not scroll**:
the card is the viewport under the header to the pixel (`height:
calc(100dvh − 60px − 2·sp-4)`, the tiles' row taking what the KPI row
leaves, a long narrative scrolling inside its own column) — measured
scrollHeight == viewport at 1920×1080, 1600×900 and 1440×820. (2) The
**footer is gone from every page** (the meta line and the source line);
`/api/meta` still loads for the layout. (3) **«Explore more» REPLACES the
card** with the frames — the analysis page as it was, at the article
width, under a slim head naming the stream with «← back to the card» —
instead of unfolding beneath it; the URL is still `#more`, a frame anchor
still opens on the frames, and the way back lands on the card's top.
(4) A class collision fixed on the way: the map tile's wrapper was
`.fill`, the name the direct-award bar already used, so the unfold on
Anti-nero and ΔΑΣΕ painted a viewport-sized block in the dataset's colour;
the wrapper is `.tilefill`.

**Fourth round the same day — the artboards' geometry applied.** The
user supplied the four mocks as 1920×1080 SVG artboards (landing field +
title, landing menu, hub, card), so every position, size and type
setting is now read off the file instead of approximated:

- *Type.* The artboards set the Obviously family in its **Narrow** cut
  for titles and labels and its **Condensed** cut for the cards' running
  text; both are in the Typekit kit already (400/700 and the variable
  cut), so `tokens.css` gained `--font-display-narrow` and
  `--font-display-cond` — no new font, no colour change. The field's
  codes are Obviously Regular 12 px on 14,4 px lines, a column every
  25,7 px (74 across the frame; `field.ts`, pinned), one blank line
  between codes; the menu cell shows the same field, not a denser one.
- *Landing.* Title 60/48 px Narrow tracked .2/.32 em over the field; in
  the menu state the text column is 110 px in with the 72/48 px title's
  cap line 218 px down, the standfirst 18 px Regular on 21,6 px lines
  ~630 px wide, the credit 12 px at the foot, and the menu a full-height
  SQUARE flush with the right edge — 2 px rules, 24 px Narrow labels
  top-right of their cells (Bold on the black START HERE), plus the
  artboard's «GR / EN» mark top-right as a `note` cell (a placeholder
  until a Greek version exists).
- *Hub.* Title as on the menu; the caption 24 px Narrow Bold; three
  186 px squares 50 px apart and two 98 px squares 40 px apart, the
  group centred on x 905; labels 24 px Condensed Bold.
- *Header.* One 83 px band on every inner page (the compaction on
  scroll is gone): brand 24/16 px Narrow 86 px in, the three streams as
  60 px squares with their names inside (the co-ops' short form
  `short`), SEARCH and NETWORK OF ACTORS as 14 px text, METHODOLOGY
  16 px at the right edge; `scroll-padding-top` 92.
- *Card.* Paddings 24/20/22/81, a 540 px text column, the KPI row 177 px
  tall (12 px corners, the label in Condensed Bold at the top — 30 px
  rather than the artboard's 36 because our card also carries the figure
  — the figure beneath), the tiles 18 px apart in rows 491 : 249 with
  36 px Condensed Bold titles inset 42 px, the symbol 152 px FILLED with
  the stream's name on its baseline, the narrative 24 px Condensed Bold
  on 28,8 px lines, the pill 37 px tall with 13 px corners.

Verified by measuring the rendered DOM at 1920×1080 against the
artboards (MAP tile 656/299/613×492 vs 656/299/613×491; KPI cards, tile
titles, header items and the menu cells within 1–7 px); no card or hub
page scrolls. Fonts and colours unchanged; the artboards' greys and the
menu's black are placeholders and keep the site's ink/paper tokens.

**Fifth round the same day — readability, after measuring «Who Owns
Britain».** The user asked for the dashboard's sizes to be studied again
(buses tab, 1920×1080, measured in a browser): an 85 px band, a 621 px
text column set in an 18 px LIGHT face on 23,4 px lines, KPI cards 137 px
tall with a 57,6 px light number over a 13 px caption, chart panels with
12 px of inset and a 10 px title/subtitle pair plus a ⓘ, the whole page
one viewport. Six changes agreed and built: (1) the card's narrative is
Obviously Condensed **Regular** 20 px on 1.35 lines — the artboard's
24 px Bold read as six lines of headline, and its Greek words fell back
to a bolder Futura — with `**bold**` in the markdown still rendering
bold; (2) the KPI cards lead with the NUMBER (56 px) and put the caption
under it in Condensed Regular 18 px, instead of a 30 px bold caption over
a 48 px number; (3) tile titles are 24 px Condensed Bold with a one-line
13 px SUBTITLE saying what the drawing shows (`Tile sub`); (4) tile inset
is 14/16/12 px instead of 28/42/24, so the chart gets the panel; (5) each
tile carries a ⓘ with its how-to-read (`Tile hint` → the site's `Hint`),
the title still linking to the full frame; (6) the pill says «all the
charts →». Subtitles and hints carry no data-derived number. Measured
again at 1920×1080 → 1280×720: no card scrolls.

**Sixth round the same day — WHO THE SPONSORS ARE as one stacked share
bar on the card (user).** The tile no longer shows the full frame's
group bars in a scroll box: `lib/charts/ShareStack.svelte` draws ONE bar
whose segments are the kinds of business, width = share of the committed
€, in a ramp of the section hue from full strength (the biggest) to pale;
the share prints above a segment wide enough (≥ 7 %); a two-column KEY
under the bar names every kind with its € and share, hover lighting the
segment, and lists the kinds that committed no stated sum with their
project counts — a share of zero cannot be drawn, so they are said. Every
figure is computed from `sponsor_groups` on the overview payload; the
segments reconcile to its `total_eur`. Measured: the tile's body holds
it without scrolling at 1920×1080. The full frame (`SponsorGroups`) is
unchanged behind «all the charts».

**Seventh round the same day — the sponsored card rebuilt to Artboard 4,
and the header band with it (user).** The user sent a second edit of the
card artboard (`Artboard 4.svg`, 1920×1080) and a written spec. Built:

- **The stream is renamed «financed by private companies» everywhere**
  (`lib/datasets.ts` label — it feeds the header square, the hub, the card
  and the unfolded head). The 59,5 px header square cannot hold that name
  at a readable size, so it carries the abbreviation «private companies»
  (`short`); the prose that describes the scheme in sentences is untouched,
  being description rather than the name.
- **The header band is BLACK on every page**, 85 px, no compaction on
  scroll: the brand in white (18/12 px Narrow) 81 px in, then FIVE FILLED
  59,5 px squares — the three streams, then search and the actor network —
  each in the artboard's own tone (#2d6a4f · #f2f2f2 · #52b788 · #f2f2f2 ·
  #b7e4c7) with its name inside, the lettering black or white by that
  tone's luminance and shrunk to fit the square; METHODOLOGY in white at
  the right edge. The page you are on keeps a ring (black gap, white
  outline) — the only wayfinding left once every square is filled.
- **The sponsored card is a THREE-COLUMN composition** (`DatasetCard
  layout="triple"`, this card only by user decision): the text column 549,
  then the KPI row 137 over the tall TIMELINE tile 703×795, then SPONSORS
  520×412 over MAP 521×521. Measured against the artboard at 1920×1080:
  every panel within 3 px. Still exactly one viewport at 1920×1080,
  1600×900, 1440×820 and 1280×720.
- **KPI cards** (`ui/KpiRich.svelte`): unequal widths (173 / 166 / 337),
  all in the dataset hue, each a headline of numbers and words over the
  user's own sentence — «68 acts / for designating private companies …»,
  «only 43 of 68 acts state a figure / those acts amount to a value of /
  41,78 m €». Every number is computed from the payload (`n_projects`,
  `n_companies`, `n_stated`, `stated_eur`); only the wording is typed.
- **TYPE OF COMPANIES APPOINTED AS RESTORATION/REFORESTATION SPONSOR**
  (`charts/SponsorTypes.svelte`) replaces WHO THE SPONSORS ARE on the card
  and counts PROJECTS, never money. Two forms behind a card-only switch
  (`?st=`): «bars», the user's own drawing (name inside the bar where it
  measures to fit, count at the right), and «column», one vertical stacked
  column in a ramp of the hue with each kind named beside it on a leader.
  The full frame keeps `SponsorGroups` with its two lenses;
  `ShareStack.svelte` (the morning's horizontal € share bar) is PARKED.
- **The card MAP**: every EFFIS scar in ONE red (`FiresLayer flat`),
  thinner administrative lines (new `--region-line-w` / `--context-line-w`
  / `--border-line-w` on PaperMap, 0.35 / 0.35 / 0.6 here), dots at r 4 and
  no zoom controls — the full map is one click away on the title.
- **The card TIMELINE**: ALL 68 projects, every bar the SAME height (the €
  encoding is the full frame's), one-line labels. The rows are computed to
  fit the tile's height and fall back to the earliest acts if they cannot;
  at 1920×1080 they do fit, 68 of 68, and the legend says so.
- **The ⓘ at each tile's top right SWITCHES the tile to its own legend**
  and back (TIMELINE and MAP, user's rule), the legends written to the tile
  and sharing `ganttTheme`'s colours so they cannot drift.

Three gotchas worth keeping: a `chip` class collided with the global
`.chip` pill and rounded every header square; `ResizeObserver` reports
nothing for an INLINE element, so the label-measuring spans must be
`inline-block` or every name measures 0 and lands clipped inside its bar;
and a `height: 100%` chart inside an auto-height wrapper fed back until the
column svg was 33 million px tall — the tile wrapper must carry a definite
height. 611 python tests, 144 frontend units.

**Eighth round the same day — the sponsored card corrected against the
artboard (user).** Six corrections, all measured rather than estimated:

- **The card's left column is only the SPACE for the user's own text**,
  set in **Futura 100 GR 18 px on 21,6 px lines** as the artboard has it.
  The programme paragraphs and the basis line that used to sit under the
  markdown MOVED to the unfolded page, so nothing is lost and the card
  waits for the copy the user will write into
  `content/datasets/anadohoi.md`.
- **The card's timeline rows are no longer links** — the clicking through
  to a project belongs to the full chart (`PromiseGantt` renders a `<g>`
  instead of an `<a>` in the card variant).
- **The KPI cards were re-set from the artboard**: numbers and words share
  ONE baseline, the sentence sits under them in Futura on 1,2 lines,
  near-white. Two things had to give against the artboard's exact sizes:
  our cut of Obviously sets the WORDS beside the numerals wider than
  Illustrator's (measured: «companies» 84 px at 13 px against the
  artboard's fit), so the numerals are 32 px rather than 36 and the words
  12 px rather than 13; and the sentence is 10,5 px rather than 12 because
  at 12 the longest of them ran past the card's bottom edge — the artboard
  itself clips that card's last word. All three cards now fit to the
  pixel, in both directions, at 1920 → 1280.
- **WHAT TYPES OF COMPANIES ARE INVOLVED** is the frame's name on the card
  (was TYPE OF COMPANIES APPOINTED AS RESTORATION/REFORESTATION SPONSOR),
  and only the BARS form is offered — the vertical stacked column is
  parked inside `SponsorTypes.svelte` behind its `mode` prop, off the
  page. The twelve rows share the tile's height on a grid, so the tile
  never scrolls, and the drawing takes the artboard's own measures:
  bars 25 px on a 5 px gap, the longest 65% of the row, names inside in
  Futura 10 px white where they measure to fit and beside the bar in ink
  where they do not, counts at the right in 9,3 px.
- **A tile that must not scroll says so** (`Tile fit`): the sponsored
  card's three tiles are fitted — their drawings are sized to the room
  they have — while an ordinary tile still scrolls a long list rather
  than cutting it off, which is what the Anti-nero and ΔΑΣΕ rankings need.

Two gotchas: whitespace between spans inside a flex row becomes flex
ITEMS of its own and widened every headline past its card (fixed with
`font-size: 0` on the row and a `> * + *` margin); and the KPI restyle of
the OTHER two cards was reaching this one through `.kpis :global(.num)`,
which is why the numerals stayed at 56 px however the component was
edited — those overrides are now scoped to `.dcard:not(.triple)`.

**Ninth round the same day — the card measured against the artboard again
(user).** The three panels were the right SIZE (703×795, 521×412, 521×521,
where the artboard has 703,2×794,5, 520,2×411,6 and 521×521) but read as
bigger, and the reasons were colour and framing rather than geometry:

- the panels were painted in the site's `--paper-2` (#f5f4f0, a warm
  cream) instead of the artboard's **#f2f2f2**; `Tile` now takes that grey
  (`--tile-bg`);
- the card's map carried a plate AND a 1 px frame of its own inside the
  tile — two backgrounds and a border, which is what made the map look
  small and inset. It now draws straight onto the panel: no background of
  its own, no border, the sea being the panel's own tone as on the
  artboard;
- the map's dots are the artboard's **r 4,63** (they were 4);
- the columns now carry the artboard's TWO different gaps — 26 px between
  the text and the middle column, 19,3 px between the middle and the right
  — as a five-column grid (30,19% · 1,43% · 38,67% · 1,06% · 28,65% of the
  card's 1818,5), instead of one 22,5 px gap on both sides;
- the tiles' head lost 2 px of padding and 2 px of the gap under the title,
  so the drawing starts where the artboard starts it.

Measured after the change: panels at 656/263, 1378/105 and 1378/537, gaps
26 and 19, panel #f2f2f2, map background none, dot r 4,63, and the page
still exactly one viewport.

**Tenth round the same day — the card's last corrections (user).**

- **The map fills its tile and its label rides on top of it**, as the
  artboard has it (the artwork there starts at the tile's own top edge,
  y 536,4 against the tile's 536,6, with «MAP» 20 px down and the ⓘ at the
  right). `Tile headOver` puts the head in the tile's top corners as an
  overlay and gives the drawing the whole panel; the map gained the ~40 px
  the head band was taking.
- **Every tile label is 10 px** (was 14). It is a shared component, so the
  Anti-nero and ΔΑΣΕ cards follow — the three cards stay siblings.
- **The gaps are the user's**: 25 px between the black band and the cards,
  25 px between the text column and the middle column, 20 px everywhere
  else (middle→right, KPI row→timeline, sponsors→map) and 20 px at the
  card's foot.
- **The stream's name is set on the artboard's three centred lines** —
  «FINANCED / BY / PRIVATE COMPANIES» — from a `titleLines` field on the
  symbol rather than from a lucky wrap.
- **The bars of WHAT TYPES OF COMPANIES ARE INVOLVED are 10 px tall**,
  centred in rows that still share the tile's height so nothing scrolls.
- **The pill reads «explore more»** again, as the artboard has it.

The KPI cards' sentence needed a slightly tighter line (1,2) and 1–2 px
off the paddings to stay inside the shorter KPI row of a 820 px window;
checked at 1920×1080, 1600×900, 1440×820, 1366×768 and 1280×720 — nothing
overflows and no card scrolls.

**Eleventh round the same day — two KPI corrections (user).** The
explaining sentence is back at the artboard's **12 px on 14,4 px lines**:
it had been cut to 10,5 px when the cards carried more padding, and with
the round-10 insets five lines of 12 px now fit the 137 px card (measured
72 px against 74 available; ours shows «public», which the artboard
itself clips). It steps down only on a narrower card, where 12 px would
overrun — 10 px at 1600, 9 px at 1440, 8,5 px at 1280. And the third
card's value now sits WHERE THE ARTBOARD PUTS IT: its sentence indented
past the headline (31 px from the card's left against the artboard's
31,7) with «41,78 m €» immediately after it (137,5 against 132,9) and its
baseline on the sentence's LAST line (`align-items: last baseline`) —
it had been pushed flush with the card's right edge.

Also verified on the user's question: the gap between the TIMELINE's grey
and the MAP's grey is **20,0 px** (panel edges 1358,2 and 1378,2), and the
same 20,0 px between WHAT TYPES and MAP.

**Twelfth round the same day — the card's gaps, the freed height and the
map's frame (user).** The 20 px gaps are **17 px** (middle→right column,
KPI row→timeline, WHAT TYPES→MAP, and the card's foot); the two 25 px ones
stay. The height the narrower gaps free is given where the user said: in
the middle column the KPI row keeps its 137 px and the **timeline takes
all 6 px** (799 tall, was 793); in the right column the 6 px split **3
and 3** — WHAT TYPES 413,7 (was 410,7), MAP 522,3 (was 519,3) — so the
right column's rows are 415 : 524 in the artboard's terms and the tiles
are 524 wide (the 3 px of the narrower column gap). The KPI row is
**137 px** at 1920×1080 (the artboard's 137,0), 12,7 vh with a 104 px
floor on a shorter window.

**The card's map frames the whole country.** PaperMap's own fit keeps
Kastellorizo in view, which leaves Greece at 78% of the frame's width
with 35 px of empty sea above Thrace and below Crete; the card now sets
its own view — centre 23,8° E / 38,37° N, k 1,12 — measured on the
rendered regions so that the northern border sits 9 px under the top
edge, Corfu 9 px in from the left and Crete's southern coast 7 px above
the bottom, with Rhodes whole and only Kastellorizo out of frame. The
«those acts amount to a value of» sentence is centred as a paragraph.
No card scrolls and nothing overflows at 1920×1080, 1600×900, 1440×820,
1366×768 or 1280×720.

**Thirteenth round the same day (user).** The 3 px the narrower
middle→right gap frees go to the MIDDLE column, not split across the
right tiles: the columns are 549 · 25 · 706 · 17 · 521 (the timeline tile
706 × 799, the right tiles back at the artboard's 521 wide — 521,5 with
the percentages' rounding). The card map measures **521,5 × 522,3 px**,
its svg filling the tile; with the frame 3 px narrower the country's
edges are 10 px under the top, 9 px in from the left and Crete 8 px
above the bottom. Kastellorizo stays out of frame by decision.

**Fourteenth round the same day (user).** Five more px move from the right
column to the middle: columns 549 · 25 · **711** · 17 · **516** (the
timeline tile 711 wide, the right tiles 516,5). The card map is zoomed
OUT to k 1,05 so the whole country sits well inside its 516,5 × 522,5
frame — the northern border 28 px under the top, Corfu 25 px in, Crete's
south coast 26 px above the bottom, Kastellorizo out by decision — and
its dots are r 3,8 (were 4,63). The bars of WHAT TYPES OF COMPANIES ARE
INVOLVED are **20 px** tall, capped at their row's height so a short
window never lets them overlap (`min(20px, 100%)`); the twelve rows still
share the tile without scrolling (370/370 at 1920×1080).

**Fifteenth round the same day — why the site cut Crete while every export
showed it (user).** Two causes, both in PaperMap's initial framing:

1. **The framing was applied once per input and the input ignored the
   frame's size.** `homeT` (the translate + scale of a `view` or a
   `fitPes` fit) was computed against the projection fitted to the box
   PaperMap had at that moment, and never redone; when the box changed
   afterwards — the grid settling, fonts arriving, a window resized — the
   projection refitted but the stale transform stayed, and the country
   slid. Headless renders never see a size change, a live browser does.
   The key now carries the rounded width and height, so any resize
   reframes. Measured: 1280×720 → 1920×1080 now lands on the same frame
   as a fresh load at 1920×1080.
2. **A fixed centre-and-zoom (k 1,05) had no margin to spare in a wide
   tile.** The country fits the tile's HEIGHT when the tile is wider than
   tall (a browser window with its own chrome is rarely the artboard's
   16:9), and a 5% zoom then leaves Crete 4 px from the edge — any offset
   pushes it out. New PaperMap input **`fitBounds`**: a lon/lat box framed
   with `fitPad` of margin on every side whatever the tile's shape, and —
   unlike `fitPes` — allowed to zoom OUT below the layer's own fit (the
   layer's extent carries Kastellorizo, which is exactly what the card
   leaves out). The card frames Othonoi/Gavdos → Rhodes/Ormenio with 6%:
   measured margins 25 / 19 / 25 px at 1920×1080, 12 / 22 / 12 at
   1280×720, 16–17 at 1920×950 — Crete, Thrace, Corfu and Rhodes inside
   at every size and after a resize.

**Sixteenth round the same day — the card map in the country's own shape,
its key beneath (user).** At the new zoom the tile's spare width showed
the coarse outlines of the neighbouring countries. The map is now drawn
in a box of the COUNTRY's own shape — the framed lon/lat box's Mercator
aspect, computed from the bounds (`CARD_ASPECT`), a 2% margin all round —
so it shows no land beyond the country's sides whatever the tile's shape;
where the tile is wider than that the box is centred on the panel grey.
The tile's remaining height carries the KEY: a compact two-column form of
the seven entries (short wording, 11 px, a «full map →» link) reserved
78 px under the map, so the map takes the rest — 449 × 444 in the 516 × 522
tile at 1920×1080, 376 × 372 in the 516 × 450 tile of a 1920×950 window,
246 × 243 at 1280×720 — with the ⓘ switch no longer needed on this tile.
The trade-off is stated: the map gives up ~15% of its height to carry its
legend permanently; the ⓘ form is one line to restore.

**Seventeenth round the same day — the card rebuilt from the user's own
edit of the exported page** (`sponsored_card_page.svg`, re-saved from
Illustrator and parsed in a browser for every box and text):

- **KPI cards** 190 · 190 · 299,4 wide, 15,8 apart, 4 px corners; the
  headline in Obviously Bold at the artboard's 36 / 13 px again, the
  numerals' line 20 px under the card's top, the sentence 16 px in; the
  third card's sentence («those acts amount / to a value of») LEFT-aligned
  at the card's own inset with the value right after it, both in the lower
  half. With our wider cut of Obviously the third headline takes two lines
  («only 43 of 68 / acts state a figure») where the user's substituted
  font kept one; the rows beneath it give the room and every card fits to
  the pixel at 1920 → 1280.
- **WHAT TYPES OF COMPANIES ARE INVOLVED** 516,5 × 374,5: 25 px bars 3,3
  apart (the user's file, superseding the 20 px asked for earlier), the
  longest 65% of the row, names 4 px in, counts 14 px off the right, the
  last bar 5 px above the panel's foot (`Tile tight`); the green ramp
  unchanged by decision.
- **MAP** 516,5 × 563,1 (15,4 under the types panel), the map filling the
  whole panel with the country 1,2% off the edges, dots r 4,9, the label
  9 px into the corner, and the KEY OVERLAID in the map's bottom corners
  — four statuses at the left (marks 7 px in, 11 px Futura on 14,4 px
  lines, the last line 5 px above the foot), the burnt areas at the
  right — in the user's wording: «no implementation dates stated»,
  «completion act identified», «past deadline, no completion act
  identified», «within its deadline, no completion act identified»,
  «areas burnt since <year> (EFFIS)». The year is computed from the scars
  drawn (2018, the layer's first year), not typed: the user's file says
  2021, and the card would have to show only the scheme's era for that to
  be true. The «revoked» and «approximate site» entries the user left out
  are left out. The user's map was stretched vertically in Illustrator to
  reach the panel's top and foot; a projection cannot stretch, so the
  country fills the panel's WIDTH and sits 33 px off its top and foot.
- **The TIMELINE key** takes the same four wordings, in the same order.
- **The pill** 145,7 × 37 with 9,8 px corners, «explore more» in Futura
  Bold 18 px 12 px in, and an arrow in the room the user's file leaves at
  its right — my reading of «the symbol of explore more».

**Eighteenth round the same day (user).** (1) **A frame picker on the card
map** (dev only, like the full map's): a checkbox at the map's top-right
makes the small map answer to drag, wheel and +/−, and prints the lon/lat
box the frame shows — PaperMap's `onViewChange` now reports `bounds`
[[W, S], [E, N]] beside centre and k, the projection's inverse at the
frame's corners — so the user can frame the country by hand and the box
goes straight into `CARD_BOUNDS`, reproducible at any tile size. (2) The
burnt-areas entry leads the map key, all five entries in the one column.
(3) «explore more» plain and in Futura's TRUE bold: the UI token is the
Book family, which has no 700 and was being synthesised; the pill names
`futura-100-greek`. (4) **The KPI sentences sit on the user's own rows**:
`KpiRich` takes `lines` / `tailLines` (one string per row: «for
designating private companies / as restoration and/or reforestation /
contractors have been made / public»; «have been appointed as restoration
/ and/or reforestation contractors»; «those acts amount / to a value of»)
and MEASURES every headline and row at its base size, scaling a card's
text down only where it would not fit its box — the rows and their breaks
are never changed. At 1920×1080: card 1 at 12 px and 36/13 (fits), card 2's
rows at 11,7 px (its widest row is 176 px in our Futura Book against 171
available), card 3's headline on ONE line at 32/11,6 (314 px against 280).
Gotcha: a measuring copy inside a flex `.head` stretched to the widest
sibling and read 176 for a 141 px headline — measuring copies are
`inline-flex` / `inline-block` at `max-content`.

**Nineteenth round the same day (user).** The KPI texts re-read from the
user's file row by row: card 1's sentence is THREE rows («for designating
private companies / as restoration and/or reforestation / contractors
have been made public» — the stray «public» text below it in the file is
a leftover, not a fourth row), card 3's headline has no «only» («43 of 68
acts state a figure»), and «those acts amount / to a value of» is CENTRED
(its second row starts 13,1 px in, half the two rows' difference). The
headline's baseline sits 54,6 px under the card's top and the sentence's
first row 9 px under the headline, both now measured on the page (54 /
70). **The frame picker pans**: PaperMap clamps every map to its fitted
frame (`translateExtent` the frame, `scaleExtent` ≥ 1), which is right
for a reader and useless for choosing a frame; the picker passes
`unclamped`, which lifts both while it is on and never otherwise.
One more PaperMap gotcha met on the way: a frame applied while the map
was NOT interactive (a fit or a view) lived only in the component's own
transform, so when the picker switched the zoom behaviour on, d3 started
its first gesture from the identity and the map jumped to the layer's own
fit. The behaviour is now seeded with the applied frame on attach (read
with `untrack`, or the effect would re-run on every zoom) — the readout
shows the current box the moment the picker is ticked (k 1,115 at
1920×1080) and a drag keeps it.

**Twentieth round the same day (user).** The card map's frame is the one
the user chose with the picker — «bounds: [[18.2336, 34.7812], [28.7256,
41.9096]] · k 0.979», saved as `CARD_BOUNDS` with no padding, since the
box IS the frame (on a 1920×1080 tile, which is taller than the user's,
the box fits by width and sits centred, ~56 px off top and foot). And the
card map DRILLS, on this card only: at rest only the περιφέρειες that
hold projects answer a click (52 of the 74 units clickable, 22 inert —
the full status map's rule, `peGroup` + `projectRegions`), the map zooms
to that region (`fitPesLive`), and while zoomed EVERY click on the map —
a unit or the sea — returns to the frame (`peGroup` then groups every unit
so all 74 answer, `onEmptyClick` covers the sea, Esc too). Verified in
the browser: Attica's central sector grows from 7 × 9 px to 33 × 43 on the
click and the frame comes back on a click on the sea; a non-project unit
at rest does nothing.

**Twenty-first round the same day (user).** On the card map only: (1)
**the outlines are the περιφέρειες', not the Π.Ε.'s.** No new geometry —
PaperMap gains `outlineBy`, a grouping function; the Π.Ε. polygons then
draw no border of their own (hover and focus included; a hot group is a
tint of the fill instead) and a MESH cut from the Π.Ε. topology's shared
edges is drawn on top, keeping only the edges between different groups
plus the coast (`topojson.mesh` with `a === b || group(a) !== group(b)`;
the topology is now memoised in `useGeo.loadTopology` so the features
and the mesh come from one fetch). Every other map is untouched. (2)
**The burnt areas are from 2021 on** — the scheme's own era (the
13.08.2021 ΠΝΠ) — through a card-only filter (`CARD_FIRES_FROM`), and the
key's year is read off the scars actually drawn, so it now says 2021
because that is what is shown, not because it was typed.

**Twenty-second round the same day (user).** On the card map only: the
hover cards — a scar's «year · ha», a dot's company — sit in the
bottom-RIGHT corner, away from the key at the bottom-left, and in the
key's own size (11 px on 14,4 px lines, a slim box): PaperMap gains
`tipDefaultCorner` and `tipCompact`, and `DotLayer`'s own `tipCorner`
learns `bottom-right` (it passes its corner explicitly, so a map default
alone did not move the dots' cards). The dev frame picker is removed from
the card now that it has chosen the frame — PaperMap keeps `unclamped`
and the `bounds` readout for the next time. A hovered project region is
a GREY a shade darker than the sea (#e6e6e6 on the #f2f2f2 panel,
`--land-hot`), not the section green.

**Twenty-third round the same day — the Anti-nero card from Artboard 6
(user).** The three-column card is now DATA: `DatasetCard` takes the
columns' widths (`cols`), the tile heights under the KPI row (`midRows`,
`rightRows`) and the row gaps, and a page's own KPI block (`kpiBlock`);
the sponsored card keeps its values as the defaults. The Anti-nero card is
549 · 25 · 596,49 · 17 · 631,59 with 25 px under the band, 17 px between
every tile and 17 at the foot (the user's gaps; the artboard drew 23,7
and 11–16). Its content, every number from the payload:

- **KPIs** as a 2 × 2 of 62 px cards (`ui/KpiQuad.svelte`, 14 × 13 px
  apart, 31 px inset): «245 contracts», «151 contractors», «90,2 % — of
  the contracts / were direct awards» (the sentence in Futura 12 px beside
  the number), «622,53 m € / total stated value of contracts» (the caption
  under the number).
- **ALLOCATION OF FUNDING** 596,49 square: the € choropleth by regional
  unit with the artboard's TOGGLE on the title line — «by works» / «by
  registered office», the full frame's two allocations (`map.work_regions`
  / `map.home_regions`), a card-local switch so no URL param opens the
  frames — and the MAP label under the title.
- **MONEY PER YEAR** as COLUMNS (`charts/ColumnBars.svelte`): one bar per
  year of signature up to 80 px wide, the value above, the year below.
- **AWARD PROCEDURES** with **DIRECT AWARDS** under it in one tile: the
  procedures BarH (compact) and the direct-award histogram on the ν.4782
  ceilings, the histogram taking what the bars leave and stepping aside
  where a short window leaves it under 64 px.
- **CONTRACT VALUES**: the beeswarm at the tile's height, the dots
  shrinking with it.
- **RANKING OF COMPANIES**: the top contractors by stated net €, as many
  rows as the box holds (ten at the artboard's size, never a cut row).
- The programme prose moved into the unfolded page, as on the sponsored
  card; `BarH` gained `compact` (11 px lettering, 3 px between rows).

Measured at 1920×1080: KPI cards at 654,8/959,9 × 110/185, 291 × 62; tiles
at 264 (596,5) and 877,5 (185,5) in the middle, 110 (284,6), 411,6 (354)
and 782,6 (280,4) at the right — the artboard's within 1 px. Nothing
overflows and no card scrolls at 1920×1080, 1600×900, 1440×820 or
1280×720 (the ranking shows 8 / 7 / 6 rows there).

**Twenty-fourth round the same day — the Anti-nero card as the sponsored
card's sibling (user, on the suggestions offered).** Same columns — 549 ·
25 · 711 · 17 · 516 — and the same shape: the KPI 2 × 2 over the MAP in
the tall middle slot (711 × 799, the timeline's place one card over), two
tiles at the right, 17 px gaps. The map has the private companies' map's
manners in full — the shared frame (`lib/maps/cardFrame.ts`, one constant
for every card), the περιφέρειες' outlines only, no zoom buttons, a
click on a region with money in the current allocation zooms to it and
any click returns, the by-works / by-office switch on the title line, a
key overlaid bottom-left (a white→black ramp «less — more» and the
measure named for the allocation shown), hover cards bottom-right in the
key's size; a group hover on a choropleth no longer repaints the fill
(`.region.choro`). **CONTRACT VALUES keeps DIRECT AWARDS as its own
chart** by the user's decision, under the beeswarm in the same tile
(the histogram 104 px at the artboard's size, giving way with the box).
**RANKING OF COMPANIES** takes the lower right box at full size: 26 px
bars, names inside, values right-aligned, ten rows at 1920×1080 and as
many as the box holds below. AWARD PROCEDURES and MONEY PER YEAR left
the card (they stay in the unfolded page; the 90,2 % KPI carries the
procedures' fact). Nothing overflows at 1920×1080 → 1280×720.
Two things met on the way: a page's controls placed on an overlaid tile
head (the by-works / by-office switch on the map) were unclickable — the
head is `pointer-events: none` and re-enabled only its OWN buttons, so the
rule is `:global(button)` now; and the ranking's names at 516 px wide
clipped inside their bars, so the tile uses `BarH compact` (11 px) with
26 px bars, ten rows in 290 px.
The ranking settled with the names ABOVE thin bars (every name on one
line, the contract count beside it, the value at the right), ten rows at
1920×1080 and 9 / 8 / 6 as the box shortens; and the beeswarm's «largest»
note now steps aside where it would run into the median's label — a
narrow plot with the median near the right end has room for one of them,
and the median is the one that matters.

**Twenty-fifth round the same day (user).** The previous arrangement read
as too empty and the 62 px KPI cards as too thin, and DIRECT AWARDS — kept
under the beeswarm but gated on the tile's height — had vanished on the
user's shorter window. Now: **four KPI cards of the private companies'
card's height (137) across BOTH chart columns** (`DatasetCard kpiSpan`:
the KPI row is the grid's first row over columns 3–5, the text column
spanning both rows), in `KpiRich`'s dress with the numbers computed and
the sentences short — «245 contracts / in the scope of the programme,
signed between 2022 and 2026» (the years read off the yearly series),
«151 contractors / private companies and joint ventures that signed the
contracts», «90,2 % / of the contracts were direct awards», «622,53 m € /
total stated value of contracts (excl. VAT)». **The two chart columns are
equal** (549 · 25 · 613,75 · 17 · 613,75): the MAP fills the left one
(613,7 × 799), and the right holds THREE tiles — CONTRACT VALUES (300),
**DIRECT AWARDS as its own tile** (170, never gated), RANKING OF
COMPANIES (295: names inside 22 px bars, ten rows at 1920×1080, fewer in
a short window). `ui/KpiQuad.svelte` is deleted; `charts/ColumnBars.svelte`
stays, unused, for a card that wants columns. Measured at 1920×1080: the
KPI row 1244,5 wide at 110, cards 299,3 × 137; the right tiles 300 / 170 / 295 tall (the beeswarm needs ~128 px at the least, which set the split);
nothing overflows at 1920×1080, 1600×900, 1440×820 or 1280×720.

## 2026-08-28 — the Anti-nero card rearranged (user)

The four KPI cards as a **2 × 2 of full-height cards** (137 each, 17 px
apart) at the top of the middle column, CONTRACT VALUES (380) and DIRECT
AWARDS (248) beneath them; the MAP (516 × 560) on top of the right column
with RANKING OF COMPANIES (376) under it; the columns back to 549 · 25 ·
711 · 17 · 516. `DatasetCard` gained `kpiRows` (a two-row KPI block, its
height two cards and a gap) and `kpiCols`; `KpiRich` takes a `columns`
count. Measured at 1920×1080: cards at 110 and 264, tiles at 418 / 815
(middle) and 110 / 687 (right); nothing overflows and no card scrolls at
1920×1080 → 1280×720.

**Second round of 2026-08-28 (user).** The Anti-nero card takes the
sponsored card's sizing: THREE KPI cards in one row at its widths (190 ·
190 · 299,4 — contracts, contractors, stated value; the direct-award share
left the KPIs, its chart carries it), the middle column's tiles 17 px
apart — CONTRACT VALUES 400 over DIRECT AWARDS 382, the histogram given
the room it lacked — and the right column the sponsored card's own rows,
374,5 over 563,1 with 15,4 between, RANKING OF COMPANIES on top and the
MAP beneath (swapped by the user). **The ranking shows more companies**:
`/api/antinero/overview` gained `ranking`, the same top-contractors query
at 25 rows (the frame's `top_contractors` keeps its ten and its pinned
top-10 share), and the tile shows as many as its box holds — 13 at
1920×1080, 10 / 9 / 7 in shorter windows. **The beeswarm's years are
said**: a key of the five year greys under the dots (`YEAR_GREYS`). The
gaps, asked for: 17 px in the middle column, 15,4 px in the right — the
sponsored card's. Nothing overflows at 1920×1080 → 1280×720. Third round the same day: the three KPI
cards divide the column's width EQUALLY (226,6 px each at 1920×1080,
`w: 1` apiece) — the sponsored card's 190 · 190 · 299,4 were that card's
own rows' widths, not a rule.
Fourth round the same day (user): the two chart columns EQUAL (613,5
each, the 549 text column and the 25 / 17 gutters unchanged) and the
vertical gaps of both columns 15,4 — the middle column's rows become 400
over 385,2 so the two columns still end on one line (a short window
shrinks both gaps alike, `min(gap, 1.6vh)`). The card map's key is
ALLOCATION OF FUNDING's own: «by location of the contracts» / «by
location of the contractors' registered offices» over «0 · [white + the
eight swatches] · max» and «€ of works — each contract's even share», and
the map is painted on the SAME ramp (`makeChoro(RAMP_WORKS)`, the sqrt
scale) so the swatches are its colours — the `color-mix` tint it had is
gone. The units' own borders are drawn WHITE on this map (PaperMap
`--unit-line` / `--unit-line-w`, none by default; the sponsored card's
plain map keeps none): on a grey-on-grey choropleth the περιφέρεια
outlines alone could not tell the units apart. CONTRACT VALUES prints its
year key UNDER THE TITLE and the swarm takes the rest, dots r ≈ 3
(3,1 scaled by the room, as the full frame's).
Fifth round the same day (user): DIRECT AWARDS moves ABOVE CONTRACT
VALUES (rows 385,2 over 400), and at its left a VERTICAL AWARD PROCEDURES
— `charts/ColumnBars.svelte`, one column per procedure, the € above each
with the contract count under it, the name wrapped on words beneath, the
direct-award column at full strength and the others at 35 % (BarH's own
rule) — in a tile exactly the first KPI card's width (a third of the row
less its two 15,4 gaps) and the row's height; DIRECT AWARDS keeps the
rest (404 px), its bracket labels at 9 px there and STAGGERED onto two
lines by `LogHistogram` wherever a printed label has under 48 px (the
full-page frames are wider and unchanged).
Sixth round the same day (user, after the Who Owns Britain dashboard):
AWARD PROCEDURES is ONE STACKED COLUMN — `charts/StackColumn.svelte`:
each procedure a segment of the € total (its share printed inside where
the segment is tall enough; 82 / 10 / 8 %), the name, € and contract count
beside it on a short leader, the labels pushed apart by their own height
where the segments are thinner than their text; the direct-award segment
at full strength, the rest at 35 % — and the two chart columns back at the
sponsored card's 711 / 516 (the three KPI cards equal at 226,6, the column
tile the first card's width, DIRECT AWARDS 469). The one-column-per-row
`ColumnBars` stays in the repo, parked.
Seventh round the same day (user): the card's RANKING OF COMPANIES bars
are 34 px tall, 3 apart — 8 companies at 1920×1080, every name INSIDE its
bar in white, on two lines where one does not fit (BarH's tier rule; its
compact mode now measures the fit at its own 11 px, it measured at 13 and
sent fitting names outside). SVGs of AWARD PROCEDURES, DIRECT AWARDS,
CONTRACT VALUES and the whole card page exported to Downloads for the
user's own drawing — the exporter now turns a chart CANVAS into circles
(`BeeswarmCanvas` hands its drawn dots over on the element as `__dots`;
any other canvas is embedded as its pixels).

**2026-08-28 — no brown or beige anywhere on the site (user).** The user
found #5c5245 in the exported SVGs: the Atlas's «newsprint» tokens were
WARM greys — ink #2a2118, ink-soft #5c5245, ink-faint #8a7f6e, papers
#f5f4f0 / #eceae4, the threshold #6b5f4e, the paper shadow in the ink's
own rgba — and the «one loud accent» was the rust #b33a1a, whose 6 %
tint is the beige that shaded every fire season. All of it is neutral
now: ink #1f1f1f / #525252 / #7e7e7e, papers #f4f4f4 / #e9e9e9, the
accent IS the ink (no page overrode it and every chart with a hue of its
own passes it), threshold #5e5e5e, `::selection` a grey, the DotLayer
stroke and the shadow in black rgba, the beeswarm's hover ring the ink,
the year/scope fallbacks a grey. Retired from the tokens: `--accent-deep`,
`--c-direct-award`, the orange `--ramp-works-*` and blue `--ramp-home-*`
sets (0–1 uses; the webui's own copies stay in geo_common.js). PaperMap's
base `.map` background was still the old cream gradient — it is the sea
grey #f2f2f2. The PROCUREMENT TIMELINE's key swatch was a literal beige
#f0e5d8 beside a stripe drawn at the accent's 6 % — the swatch is now
that same mix; its call ties #cfccc6 → #c9c9c9. The project pages' fire
tones were the maroon fading to a PEACH (#dba28c) — now four tints of the
maroon's own hue; FROM THE FIRE TO THE SPONSORED PROJECT shaded its
seasons in a brick #b4553f — the ink's tint now. **Parked**: the fires map's ELEVATION toggle
(`RELIEF_TOGGLE = false`) — the baked hypsometric ramp is earth-toned by
construction; `relief_hypso*.avif`, `build_relief.py`'s `HYPSO_STOPS` and
the key's gradient stay for a re-bake in a neutral ramp. Left for the
user's word: the chord's TYPE families in `catColors.ts` (the amber
studies #b07d1e and the red ramp's pale ends #d99c8c / #ebccc3, chosen
2026-08-23) and the amber flag chip (#c99700, a gold) — hues with a
meaning, not greys gone warm.

**2026-08-28 — the fire season in the red's light shade; the Anti-nero
card to the user's Illustrator edit.** The site's red is the EFFIS
scars' maroon #6b2d35 — now a token, `--c-fire`, with `--c-fire-season`
its 12 % tint — and every chart that marks the fire season shades it in
that tint (PROCUREMENT TIMELINE and its key swatch, PAYMENTS TIMELINE,
CUMULATIVE DISBURSEMENT, FROM THE FIRE TO THE SPONSORED PROJECT's lanes
and key), the season labels in the red itself. The user's edit of
`antinero_card_page.svg` also draws the ν.4782 ceilings and the median
line in that red, so `--c-threshold` is #6b2d35 and the Anti-nero
beeswarms pass `medianColor` (ΔΑΣΕ's stays the ink). **The card as
edited**: RANKING 428,2 tall (TEN rows at 34 px, the two short bars'
names beside them in ink) over ALLOCATION OF FUNDING 504,3 with 20,5
between; AWARD PROCEDURES | DIRECT AWARDS 395,2 over CONTRACT VALUES 390
(the middle gaps 15,4 — the user's own 10,3 left the column 5 px short);
the gap clamp is now the artboard's px × 0,0926 vh, so both columns
shrink alike and the 20,5 is honoured at 1080 (a `min(…, 1.6vh)` had
been eating it). AWARD PROCEDURES = `StackColumn variant="card"`: the
SMALLEST segment on top and the direct award at the foot, the segments in
the grey ramp's darker half (#a6a6a6 / #5f5f5f / #111 for three) parted
by white seams, the share inside, the COUNT at the column's left, the
name at its right in lower case (the direct award bold), no € and no
leaders, the column 24 % in — the counts and names may run into the
tile's padding as the user's do. DIRECT AWARDS prints its bracket labels
on ONE line at 469 px (the stagger now kicks in under 44 px, was 48).
CONTRACT VALUES: the swarm pushed right by 12,85 % of its width at the
same scale (`padLeftFrac`; the empty ≥16,4 M bracket falls off the right
edge — dots 849,6 → 1.330,1 against the user's 849,9 → 1.330,3), the
year key 8 px under the title, dots r 2,7. The map tile is titled
ALLOCATION OF FUNDING; its two lenses are STACKED under the title at the
top-left in their full wording («by location of the contracts» / «by
registered office of the awarded contractors», 127,7 wide, the chosen one
black on white); its key is the user's: «0» and the max on a line ABOVE a
128 px swatch bar with a ½ px hairline, the sentence beneath, 10 px, 32,6
px in. Every position verified against the SVG by DOM measurement.

**2026-08-28 — TRIED AND UNDONE the same hour (user): the card scaled as
one artboard.** The user's screenshot of the Anti-nero card differed from
their SVG (six ranking rows, five-line names, a 98 px header) and
reproduced in a browser at 115 % zoom, so the card was rebuilt as a fixed
1920 × 995 box scaled by `transform` to the window. The user rejected it —
the sponsored card had been showing perfectly in the same browser, so the
cause lies elsewhere — and every part was reverted: no inline script in
`app.html`, no `.stage`/`.art` in `DatasetCard`, the vw/vh clamps as they
were. The card is laid out in window fractions again; the cause of the
user's rendering is still open.

**2026-08-28 — the user's corrections on the Anti-nero card, applied.**
ALLOCATION OF FUNDING: the toggle's and the ramp's left edges sit on the
A of the title (8 px into the body, the title's own 9 px); the map draws
NO neighbouring countries (`context={false}`) and its frame is the shared
card frame slid 0,264° west — 13 px at the card's width, the same scale —
so the country sits to the right and the title, toggle and key have the
left (the user's Greece spans 1.452 → 1.887; ours now the same to the
pixel); the hover card was already bottom-right. DIRECT AWARDS: the €30k /
€60k labels are CENTRED on their dashed lines, 9 px above the plot (they
sat at the top-left of the frame). AWARD PROCEDURES: the stacked column's
lettering as the user's — names in TWO lines at the segment's right
(«negotiated procedure / without prior publication»), counts at its left,
both allowed into the tile's padding (`Tile bleed`, the body 16 px wider on
each side, `StackColumn inset`), the wrap on REAL text widths (a canvas
measure of the page's font; the per-character estimate only on the
server). RANKING OF COMPANIES takes WHAT TYPES OF COMPANIES' sizes as its
base — 25 px bars, 3,3 px apart, 10 px names inside in white, the ones
that do not fit beside the bar in ink (BarH `gap` / `fontPx`) — 13 rows at
1920 × 1080, seven of them named beside their bar.
Same day, the user's follow-up: CONTRACT VALUES gives 7 px to the row
above (402,2 over 383); the stack's three parts stand 4 px apart
(`StackColumn SEG_GAP`, the column's height less the gaps shared by
value); the first KPI card and AWARD PROCEDURES under it are 12 px wider
(238,6 of the cards' 680, the other two 220,6) so the lettering has its
room; and the map is panned further right — the frame a full degree wider
at the west (`ALLOC_WEST`), which slides the country 39 px right and,
the frame being fitted by width, draws it 9 % smaller — so the toggle
sits on sea, not on the country.
Then: the stack's column is 48 px wide on the card (56 on the side
form), a two-line name rides 3 px above its segment's middle, and a
two-line name breaks where its lines come out most EVEN — «negotiated
procedure / without prior publication», the user's own break, which the
greedy wrap had turned into «… without / prior publication» once the
column narrowed. The AWARD PROCEDURES | DIRECT AWARDS row takes the KPI
cards' own column gap (0,82 vw = 15,7 at 1920), so the first tile's edges
meet the first card's exactly.
**RANKING OF COMPANIES = the top TEN** (user, same day), on WHAT TYPES OF
COMPANIES' rule: the rows share the tile's height 3,3 px apart, each bar
the row's height capped at 25 px — the tile is sized to exactly that at
1920 × 1080 (327,2 = ten 25 px bars, nine gaps, the head and inset) so
the bars are the other card's, and in a shorter window they shrink
together instead of rows dropping out (a name beside a short bar stays on
one line, ellipsised, so no row outgrows its bar). The height the ranking
gave up went to ALLOCATION OF FUNDING: 605,3.

**2026-08-28 — the forest workers' co-operatives card in the Anti-nero
card's arrangement (user).** The same triple layout and rows: three
`KpiRich` cards (contracts · co-operatives · stated value, the years read
off the yearly series), AWARD PROCEDURES as one stacked column — the ΔΑΣΕ
greens' darker half (`StackColumn ramp`), its five procedures' counts
and names pushed clear of each other where the segments are thin — beside
DIRECT AWARDS with NO ceiling lines (DATA_DECISIONS 2026-08-24), CONTRACT
VALUES as the year-coloured beeswarm with its key under the title (dots
r ≈ 1,5 so the 1.998 contracts fit the tile), and — in the ranking's
place, the user not wanting a ranking here — MONEY PER YEAR, the six bars
sharing the tile's height at 35 px each. ALLOCATION OF FUNDING is treated
exactly as on the Anti-nero card: the two lenses stacked under the title
(«by area of the awarding forest service» / «by registered office of the
co-operatives», from `/api/dase/allocation`'s work and seat regions), the
green ramp's swatch key on the title's A, no neighbouring countries, the
frame slid west, region outlines with white unit seams, the drill by
περιφέρεια. `RAMP_DASE` moved from DaseMap into `useGeo` so the page and
the map share it. The co-operatives prose and the basis line moved under
«explore more», as on the other two cards.
Then (user): the ΔΑΣΕ card's WHOLE middle column under the KPIs goes to
CONTRACT VALUES (800,6 — the AWARD PROCEDURES | DIRECT AWARDS row leaves
this card; the beeswarm's dots r ≈ 2,2 in the taller box), and the card
maps on BOTH cards draw no hairline: the line was the pages' «every map
gets a 1 px border» rule catching the tile's own wrapper, which was also
classed `.map` — it is `.mapfill` now, and nothing in the tile draws a
border or a shadow.
Then (user): the card maps' two lenses each on ONE line (the toggle
`max-content` wide, 40 tall, 30 px under the title) and the frame half a
degree tighter at the west (`ALLOC_WEST` 0,5), the country a little
larger with nothing under the toggle or the key; the beeswarm's axis
amounts in the readable grey (`--ink-soft`, they were the faint one) and
the «largest: …» note AT its own dot — above every dot within 70 px of
its column, ending over the dot, a vertical tick down to it (the note
used to sit in the frame's top-right corner, and a first move to the
dot's left printed it over the neighbouring dots).
**Debugged the same evening** (user: the amounts under the lines «still
do not appear»): they were there at 1920 × 1080 and CLIPPED in the user's
smaller window — the beeswarm sized itself to its tallest dot column
(shrinking the dots only past a fixed 560 px), so in a short tile the
canvas ran past the box and the axis row at its foot fell under the
tile's edge. `BeeswarmCanvas maxHeight`: a card tile passes its own box
and the dots shrink until the tallest column fits it (floor r 0,9);
verified on both cards at 1920 × 1080, 1667 × 784 and 1440 × 820 — the
canvas ends 6–7 px inside the body everywhere.

**2026-08-28 — a ΔΑΣΕ co-operative's seat Π.Ε. is its REGISTERED OFFICE's,
not its first contract's.** The user found a regional unit shaded on the
co-operatives card's «by registered office» map with no co-op dot in it
on the actors map (Π.Ε. Ηλείας): `dase_locations_loader` had stored in
`contractor_locations.region_pe` the Π.Ε. of the co-op's FIRST CONTRACT
(`contract_pes[0]`, "the geocode validator, recorded as what it is"), and
`queries_extra.dase_allocation` (the seat side, the flows, the away share)
and `authorities_map_points` (the dots' `pe`) read that column as the SEAT
— so every co-operative that works away from home was credited, on the
seat map, to where it works. 17 of 246 were wrong: ΔΑ.Σ.Ε. ΚΡΥΟΝΕΡΙΟΥ
(096034987), seated at Κρυονέρι of Σοχός (57002, Λαγκαδάς — the register's
own address, its point in Π.Ε. Θεσσαλονίκης), shown as an Ηλεία seat
because its four contracts are in Ηλεία; the Τρίκαλα co-ops of Περτούλι,
Χρυσομηλιά, Αθαμανία and Καλογριανή shown in Εύβοια and Ρόδος; Στεφανινά
(Θεσσαλονίκη) in Εύβοια; Δίστρατο (Ιωάννινα) in Πρέβεζα; Ξινό Νερό
(Φλώρινα) in Ημαθία; … Fix: `region_pe` = the Π.Ε. the geocoded point
falls in (a ray cast over the coarse Π.Ε. layer, `seat_pe`), else the
postcode / town's (`resolve_pe`); the contracts' Π.Ε. list moves into
`notes` for the audit. The seat map, the flows and the away share are
recomputed from the corrected column — figures below; the work side is
untouched. Pinned by `test_region_pe_is_the_seat_not_the_work` (every
row's `region_pe` == the unit under its point; Κρυονέρι in Θεσσαλονίκη).
**The corrected figures** (from `/api/dase/allocation`): the money earned
by co-operatives working OUTSIDE their seat's Π.Ε. is **50,2 % —
€14.996.831 — not 37,4 %** (the wrong seats had hidden a third of it);
Εύβοια's €9,47M is 84,6 % imported (was 64 %), Ηλεία's €3,40M and Ρόδος's
€2,48M are 100 % imported (were 83 % and 68 %) — no co-operative is seated
in either; the largest flows are Τρίκαλα → Εύβοια €2,99M, Θεσσαλονίκη →
Ηλεία €1,78M and Πιερία → Ρόδος €1,22M; 43 of the 246 co-operatives hold a
contract outside their seat's unit and 11 hold none at home; the seat map
has 25 units (Ηλεία is no longer one). `test_dase_allocation_pins` re-pinned
to 50,2; the lightbulb on the /dase frame computes its sentence from the
payload and now says so.

**2026-08-29 — freshness check of the three datasets: what has been
published since they were built (found and counted; NOTHING loaded).**
Three explorers first read every harvest and loader (the ΔΑΣΕ harvest is
repeatable but re-searches 2021→today and its resume keys were keyed on a
window's START, silently skipping the days a later run adds; the Anti-nero
universe rests on a one-off portal export of 2026-05-09 plus a hand-made
55-ADAM supplement with NO automated discovery of a new procurement; the
sponsored harvest's five subject needles reach designations 68/69 but
ΥΠΕΝ-style completions only 5/16, and its `harvest.json` was missing, so
the loader could not run). Then the check, on COPIES of the DBs:
- **ΔΑΣΕ** (contracts as of 2026-07-26): `harvest_dase.py` gained `--since`
  and `--out` and keys carrying both window ends (+ UTF-8 state files —
  the ANSI default died on a Greek name). `collect`+`close --since
  2026-07-01`: 12 rows, 4 already stored (the control, 4/4), **7 new
  contracts, all August, €241.511 net, every one by a co-op already in
  the whitelist** (the one «uncurated» key is a zero-padded twin of
  096135196; «ΚΕΝΤΡΟ ΔΙΑΣΚΕΔΑΣΕΩΣ» the known false positive) — no new
  co-operative, no new awarding body. 26SYMV019686651 (ΔΑΣΕ ΜΙΣΤΡΟΥ,
  €195.565 net, 27.08.2026) is the one large one.
- **Anti-nero** (ΚΗΜΔΗΣ as of 2026-07-25): new `scripts/find_antinero_new.py`
  — three routes (the 175 contractor spellings ≤30 chars + 151 ΑΦΜ over
  ΚΗΜΔΗΣ since May; the one family sibling; ΥΠΕΝ's Diavgeia acts since May
  whose subject stamps a SYMV ΑΔΑΜ) — re-found all 17 post-export
  contracts (the control) and found **NO new Anti-nero contract** (331
  candidates screened out by authority VAT or fund; the 24 unknown ΑΔΑΜ
  in ΥΠΕΝ subjects are ΤΑ07500030 support contracts, forest-road
  contracts of other authorities and the like; one to look at:
  26SYMV018768552, ΕΕΣΥΠ, «Εργασίες αποκατάστασης – αναδάσωση» of
  02.04.2026 — an umbrella by its authority, screened out as such). The
  refresh dry-run on the copy: **14 of 233 open tips changed, every
  change one new payment order** (26PAY0196…, August), no amendment, no
  cancellation. The two act sweeps on the copy (344 luminapi searches
  each, ~20 min each — the 15–30 s/query on record did not hold today):
  **+9 completion acts** (all posted 24–27.08.2026, all in-scope chains,
  end dates 27.02 → 26.07.2026) and **+2 extension acts** (28.08.2026, to
  30.09.2026). Diavgeia payment clearances of the Anti-nero funds since
  2026-05-04: **88 acts** (the hand-made worksheet stops at 2026-05-07) —
  none stamps the ΑΔΑΜ in its subject; the loader reads it from the PDF.
- **Sponsored works** (seeds to 2026-07-22): the harvest re-run with two
  more needles («ΔΙΑΠΙΣΤΩΤΙΚΗ ΠΡΑΞΗ ΟΛΟΚΛΗΡΩΣΗΣ / ΠΕΡΑΤΩΣΗΣ») — 871
  candidates (was 322), `harvest.json` restored. **1 new designation act:
  Ε3ΣΨ4653Π8-2ΣΚ (06.08.2026) — Τράπεζα Πειραιώς, €1.500.000 excl. ΦΠΑ,
  study + anti-erosion and small anti-flood works, Δασαρχείο Αιγάλεω,
  Π.Ε. Δυτικής Αττικής, for the fire of 31 July 2026 (a fire event the
  dataset does not yet know).** 78 completion-style acts we did not hold,
  most generic ΥΠΕΝ forestry; matched against the projects' own anchors:
  **2 endings of open projects confirmed** — 6Ρ9Ξ4653Π8-ΦΑΨ (23.02.2024,
  EREN's Λίμνη pilot reforestation, 9Φ9Ρ4653Π8-ΞΕΦ, cites its ΑΔΑ and
  protocol; status was «no completion recorded») and 6Σ3Β4653Π8-9ΦΑ
  (08.02.2024, Eurobank's Rhodes «Άμεσα μέτρα αντιπλημμυρικής-
  αντιδιαβρωτικής», 971Χ4653Π8-222, names «ανάδοχο αποκατάστασης EUROBANK
  AE» and its whole title; status was «active») — and one to read by eye
  (91ΧΘ4653Π8-ΛΣΔ, 21.08.2026, a «Μελέτη Αντιπλημμυρικών…» completion).
  103 new lifecycle acts, 30 citing a stored ΑΔΑ/protocol — the parked
  lifecycle harvest's territory, counted only.
**Cost, measured**: ~1 h 45 min wall-clock for everything, ~2 h of session
work; the Diavgeia sweeps ran at ~3 s/query. **Incorporation** is the
second pass: 7 ΔΑΣΕ contracts (screens + Π.Ε. + the loader; no new
names/seats), 14 payment orders + 9 completions + 2 extensions + 88
clearance acts for Anti-nero (loaders exist; the clearances need a small
harvest-JSON writer for `diavgeia_loader`), one new sponsored project
typed by hand (~1 h: budget, deliverables, location EN, a NEW fire event
with its EFFIS scar, sponsor group, sites) and two endings + one act to
read (~15 min) — plus every pinned count moved with a decision entry.
Outputs kept in the session scratchpad (`fresh/`: the report JSONs, the
ΔΑΣΕ raw rows, the refreshed copies); the harvests' new `.txt` sidecars
(anadohoi_cache 180, diavgeia_cache 11) are in the working tree.

**2026-08-29 — «Antinero V-PLUS» is the 2026 batch, and it is complete; it
gets its own phase.** The ministry announced the programme at €667M in
total and «Antinero V-PLUS» as 19 contracts / €81,98M. No registry title
carries that name — ΥΠΕΝ's 2026 titles say «ΕΡΓΑ ΑΝΤΙΠΥΡΙΚΗΣ ΠΡΟΣΤΑΣΙΑΣ
ΔΧ …» / «ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΩΝ ΑΝΤΙΠΥΡΙΚΗΣ ΠΡΟΣΤΑΣΙΑΣ …» — but the
batch is in the dataset entire: the 19 lots of fund 2023ΤΑ07500012
procured under the February-2026 «Προσκλήσεις έργων αντιπυρικής
προστασίας … αρ. 16 παρ. 5 ν. 998/1979» (16 calls, 26PROC018445169 →
26PROC018521195, one covering three lots), awarded 17.02–20.03.2026,
signed 05.03–03.04.2026, sum to **€66.110.956,16 net = €81.977.585,66
gross — the announcement's figure to the euro.** One of the 19,
26SYMV018682054 (ΔΧ Αλεξανδρούπολης–Διδυμοτείχου, €1.900.694,13), stands
behind its ΑΠΕ+supplementary approval 26SYMV019200696 of the same value,
which supersedes it — the chain rule, the money counted once. What was
wrong is the LABEL: 14 of the 19 were filed as `antinero_iii` (the
supplement's curated phase; scope.py's fund default) and 5 as
`antinero_2026`, so the site showed no such phase and overstated III by
14 lots / €55,2M. Decision: a new scope key **`antinero_v_plus`** («Anti-nero
V-PLUS», the ministry's name) for the 19; `antinero_2026` retired into it
(its five lots are the same batch); scope.py's rule: fund 2023ΤΑ07500012
+ signed in 2026 + no phase marker in the title → V-PLUS (every III/IV
lot carries its marker or predates 2026 — verified on the 22 such
contracts); the supplement's 19 entries re-phased; the basis unchanged
(€622.534.181,72). **The €667M** does not reconcile from the registry — our
net basis ×1,24 is ≈ €772M gross, and the ΤΑΙΠΕΔ/ΕΕΣΥΠ umbrella contracts
of fund 2023ΤΑ07500012 (€420,2M + €6,3M) sit BELOW its €443,6M of
execution lots — so it is a figure on another basis (an allocation, or
net of ΑΠΕ), not evidence of missing contracts; a per-phase comparison
awaits the announcement's own table.
Two things read while implementing it. (1) **ΥΠΕΝ's own acts on these lots
write «ANTINERO III»** — the deadline-extension act ΡΞ6Α4653Π8-ΒΣΡ on
σύμβαση 10/2026 (26SYMV018661963) speaks of «συμβάσεις υλοποίησης του
Έργου «ΠΡΟΓΡΑΜΜΑ ΠΡΟΣΤΑΣΙΑΣ ΔΑΣΩΝ – ANTINERO III)» and «των στόχων του
προγράμματος ANTINERO III» — because the ministry files III, IV and the
2026 batch under one ΠΔΕ project (ΟΠΣ 5222791, fund 2023ΤΑ07500012) whose
title is ANTINERO III. The phase label follows the ministry's PUBLIC name
for the batch, which its 19 lots reconcile to the euro; the methodology says
which name the acts use. (2) The year rule applies to ORIGINAL contracts
only: 26SYMV019250208, the 2026 supplementary of the 2025 Θεσσαλονίκη
water-tanks contract (III), has no phase of its own and inherits its
predecessor's — an amendment on that fund signed in 2026 is
`antinero_unknown_phase` from the rule and III by inheritance. Result:
`antinero_v_plus` 21 records = the 19 lots + their two 2026 amendments
(26SYMV019200696 restating a lot at the same value, 26SYMV019471687 a
€161.288,15 supplementary — additive, so 20 records in scope), III 83
records (from 97; 79 in scope, from 93), the basis €622.534.181,72 untouched.

**2026-08-29 — Round 2 of the freshness check: the ways past the three
routes' blind spots, and what they found.** The morning's routes (known
contractors, family siblings, ΥΠΕΝ act SUBJECTS) cannot see a first-time
contractor or an ΑΔΑΜ cited only in a PDF body. Four further routes were
built, all reading a DB copy and writing JSON reports, nothing loaded:
(1) `scripts/find_antinero_by_payments.py` — every ΥΠΕΝ «ΤΑ075» /
«Εκκαθάριση-εντολή πληρωμής» act on Diavgeia (1.581 + the clearances),
PDFs read, «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ» stamps screened; (2) the `--cpv` route
of `find_antinero_new.py` — ΚΗΜΔΗΣ `cpvItems` on the programme's ten codes
over 150-day windows since 2022-01 (3.082 Greek contracts, 161 queries,
screened by fund/authority; control: all 17 post-export contracts re-found);
(3) `screen()` tests the FUND before the authority (two in-scope contracts
are ΕΕΣΥΠ's, not ΥΠΕΝ's); (4) `GET /adamChain` from the side of the 262
calls/awards the contracts cite. **The CPV route found four ΑΔΑΜ the dataset
lacks.** Three are the registry's SECOND POSTINGS of contracts already held —
24SYMV016004702 / 016005190 / 016005431, posted 16.12.2024 with signature
date 12.12.2024, against the stored 24SYMV016017961 / 016018102 / 016018183
of 17.12.2024 signed 13.12.2024: the ΣΠ-Β1/Β2/Β3 «Κατάρτιση Σχεδίου
Αντιπυρικής Προστασίας» studies (Αιγάλεω, Αλμυρός, Κεφαλληνία), same
contractors and values to the cent, neither posting cancelled or linked —
the double-posting phenomenon of the ΔΑΣΕ audit (2026-08-14), here on the
Anti-nero side; the earlier postings are NOT added (the money is counted
once already) and are recorded here so the next sweep knows them. **One is
a genuine missing contract: 26SYMV018768552** — «Εργασίες αποκατάστασης –
αναδάσωσης με Χαλέπιο Πεύκη στο Δημόσιο Δάσος Λίμνης, περιοχής αρμοδιότητας
Δασαρχείου Λίμνης, στο πλαίσιο του «Εθνικού Σχεδίου Αναδάσωσης»», signed
02.04.2026 by ΕΕΣΥΠ (997104555) with ΛΙΤΣΟΣ ΗΛΙΑΣ ΤΟΥ ΑΓΓΕΛΟΥ, €402.578,43
net, fund 2021ΤΑ07500002, whose own text says «Το έργο περιλαμβάνεται στη
Δράση 16849: «Εθνικό σχέδιο αναδάσωσης, πρόγραμμα αποκατάστασης και
πρόληψης («Antinero»), αντιδιαβρωτικά και αντιπλημμυρικά μέτρα» … κωδικό
ΤΑ 5201358» — an `antinero_esa` contract by every rule of scope.py. It was
invisible to the three earlier routes because its contractor had never
signed before and its authority is ΕΕΣΥΠ (the old `screen()` rejected it on
the authority). **Found, not loaded**: it joins the freshness haul awaiting
the user's word; loading = a supplement entry (phase `antinero_esa`, basis
fund + the Δράση-16849 recital) and the refresh chain, and moves the basis
to 246 contracts / €622.936.760,15.
The call-side listing (route 4: `adamChain` of the 262 calls and awards the
contracts cite, 71 contracts listed, 1 chain unreachable) named ONE ΑΔΑΜ
the dataset lacks, 23SYMV013599468 — and it is the registry's CANCELLED
first posting («Ματαίωση · ΚΑΤΑΧΩΡΗΣΗ ΛΑΘΟΣ ΣΤΟΙΧΕΙΩΝ», the same hour) of
the ΕΣΑ nurseries contract stored as 23SYMV013600200, which the
supplementary 24SYMV015185915 calls its «Αρχική Σύμβαση». Nothing new;
the registry links every lot the calls produced to a record we hold.
The payment-clearance route (route 1) finished last: 3.683 ΥΠΕΝ acts read
(1.581 whose subject names a ΣΑ ΤΑ075 fund + the clearances naming none;
every PDF fetched into `diavgeia_cache`, 0 failures), **251 contracts
stamped by clearances on the three Anti-nero funds — every one of them in
the dataset**. The single unknown stamp, 24SYMV014337027 in Ψ34Ε4653Π8-ΚΣΛ
(a 2026-08 clearance of €162.259,28), is the act's own typo — its recital
writes «24SYMV0143370271», ten digits, and its EPDE line the real
24SYMV014370271, which we hold. Control: 285 of the 293 stored payment
acts were among the swept ones; the 8 others (4 ΥΠΕΝ acts of 2024 whose
subject words the clearance differently, 4 ΑΠΔ acts of 2017–2021) are
pre-programme or non-ΥΠΕΝ postings — the sweep's blind spot is the wording
of a subject line, not a fund. **Round 2's verdict: one contract was
missing (26SYMV018768552, above); the other 245 in-scope contracts are
confirmed from three independent directions — every contract ever PAID
under the funds, every lot the registry links to the calls, and every
Greek contract on the programme's CPV codes.**

**2026-08-29 — The seven «ANTINERO II» chains of 2022 return to scope (user
decision; reverses the demotion of 2026-08-13).** The user asked for
22SYMV011360183, 22SYMV011593395, 22SYMV011928850, 22SYMV011928864,
22SYMV011928896, 22SYMV011928919 and 23SYMV011953055 — the seven chain
tips of the `antinero_probable` tier (13 records with their superseded
originals: ΕΡΓΑ 2Α, 2Β, 3Α, 3Β, 4Β, 5Α, 5Β «ΤΟΥ ANTINERO II», ΥΠΕΝ-signed
26.09–11.11.2022, ΤΑΙΠΕΔ-procured, €9.198.921,61 net on the tips) — to be
included. The documentary evidence is what it was on 2026-08-13 and was
re-checked today: the 13 cached texts hold no «Ταμείο Ανάκαμψης», no Δράση
16849, no ΠΔΕ/ΣΑΤΑ code and no ANTINERO in the body; the fund metadata is
empty; no stored payment order and NONE of the 3.683 ΥΠΕΝ ΤΑ075 clearance
acts read today stamps any of the 13 (the 37 Diavgeia acts that cite them
are deadline extensions). What speaks for membership: the registry titles
(«ΕΡΓΟΥ 2Α ΤΟΥ ANTINERO ΙΙ», «ΕΡΓΟΥ 3Α ΤΟΥ ΙΙ»), the same 2022 numbered-lot
series and ΤΑΙΠΕΔ procurement as the Anti-nero I/II lots, and ΥΠΕΝ's own
subject lines. Decision (the user's): in scope as `antinero_ii`, by title
or by inheritance from the supplement-curated originals; `probable_related
.json` is EMPTY (its `_history` keeps the 13 entries and the 13.08
reasoning verbatim, so the tier can be restored), the «additional
contracts found, probably related» presentation and the methodology's
probable paragraph render only while the tier is non-empty. The basis
rises by the seven tips; every figure is re-pinned in the load entry below.

**2026-08-29 — The freshness haul LOADED, with the two scope decisions above.**
Every pinned count moved; the suite (614) is green on the new values.
- **Anti-nero**: `khmdhs.refresh` refetched the 233 open tips (14 changed, 14
  new payment orders), `antinero_loader` fetched 26SYMV018768552 (its
  relevance test now accepts ΕΕΣΥΠ as signer on a FUND basis), the seven
  ANTINERO-II chains came back as `antinero_ii`, the clearance sweep's 88
  Diavgeia acts went through `diavgeia_loader` (a new
  `scripts/build_diavgeia_harvest.py` writes its harvest JSON from the
  cached acts: 5 PAY records fetched, 83 already stored through the
  registry's own links), the completion and extension sweeps ran live
  (+9 completion acts → 290; +4 extension acts → 467, the 16Ε/16Δ
  warning being a registry TITLE typo — both 23SYMV013039379 and
  23SYMV013039380 are titled «16Δ» while ΨΔΨΙ4653Π8-Λ6Κ names 16Ε three
  times for the ΑΔΑΜ it cites, so the act's attribution stands and no
  override is needed). Basis **253 contracts / €632.135.681,76 net**
  (€622.534.181,72 + the seven tips' €9.198.921,61 + €402.578,43);
  payments 905 orders / €586,03M gross; phases in scope I 26 · II 58
  (from 51) · III 79 · IV 48 · V-PLUS 20 · ΕΣΑ 9 · restoration 13.
  The eight newly in-scope contracts were curated like the rest — one
  category each from the signed PDF's descriptive title (7 dasotexnika,
  1 anadasoseis), work themes by hand from those titles (clearing,
  roads, firebreak maintenance; εστεγασμένες for lot 4Β; the registry
  titles carry only the lot number), durations and municipalities
  promoted from the readers (three pre-Καλλικράτης names resolved:
  Ομηρούπολης → Χίου, «Ιωαννίνων» → Ιωαννιτών, «τέως Δήμου Θέλπουσας» →
  Γορτυνίας — the last lies in Π.Ε. Αρκαδίας on lot 4Β (Δασαρχείο
  Πύργου) and stays FLAGGED, the third such row: the study-area list
  names the whole project's areas), deliverables (six chains state the
  design-build Ορισμός, lot 2Β's original words it as the authority
  «εποπτεύει την εκπόνηση της κάθε μελέτης και την υλοποίηση των
  δασοτεχνικών εργασιών» — hand override; the ΕΣΑ contract states no
  study → works). Six contractors gained a seat read from their party
  clause (Καλαμπάκα, Καρδίτσα, Καβάλα, Σαλαμίνα, Ν. Μαγνησία, Τρίκαλα;
  ΤΣΙΑΝΑΒΑΣ's contract seat differs from the register's Δάφνη —
  `register_disagrees` in spirit, the contract wins) and five joint
  ventures joined `consortium_members.json`: two with every member's
  ΑΦΜ in the signed text (ΛΙΤΣΑ–ΕΔΡΑΙΟΣ, 3Κ–ΚΑΤΣΙΑΒΑΣ/ΝΑΤΣΗΣ–ΣΚΑΡΛΑΤΟΥΔΗΣ),
  three whose contracts NAME the members but state no ΑΦΜ (identity-card
  numbers only; ΓΕΜΗ's payload carries no managementPersons) —
  `members_documented: false`, so nobody is credited money on a guess,
  even where a member is an in-scope contractor under her own ΑΦΜ
  (Οικονόμου Ιωάννα 031213597, Κοσμίδης Ιωάννης 117925460). 62 ventures,
  48 documented, 98 links.
- **ΔΑΣΕ**: the 12 scratch rows loaded through `harvest_dase.py load` —
  2.171 records, **live 2.004 / €30.162.069,68 net / €37.254.303,72
  gross**; among them a REGISTRY re-posting: 26SYMV019612527 (11.08.2026,
  Δασαρχείο Καρπενησίου × Δ.Α.Σ.Ε. Αγίου Νικολάου, €21.772,52) was
  cancelled by ΚΗΜΔΗΣ on 18.08 («ΠΑΡΑΛΗΨΗ ΑΑΗΤ») and re-signed the same
  day as 26SYMV019642791 with a zero-padded ΑΦΜ «0096135196» — a
  curated `contractors_vat` rewrite files it under 096135196 and the
  registry's own cancellation counts the money once (103 cancelled
  records). The load's INSERT OR REPLACE cascaded the linked acts of the
  four re-upserted contracts away; `linked_acts_loader --with-payments`
  refilled them (+30 acts, 1.698; payments unchanged at 953 /
  €20.405.695,74). The six new live contracts' categories come from the
  parked details layer's reader (4 ylotomia — sanitation felling of
  bark-beetle fir —, 1 dentra, 1 antidiavrotika post-fire), not by eye:
  the layer is off the pages. `dase_region_loader` places all six.
- **Sponsored**: `anadohoi_loader` on the 871-candidate harvest — **70
  projects**, 19 completed / 29 active / 20 no completion recorded / 1
  revoked / 1 superseded; Τράπεζα Πειραιώς (Ε3ΣΨ4653Π8-2ΣΚ, €1,5M net,
  study & works, Δασαρχείο Αιγάλεω, fire of 31.07.2026 — a new fire
  event «Δυτ. Αττική (Αιγάλεω), Ιούλ. 2026» / «West Attica (Aigaleo),
  07-2026», with no EFFIS scar in the 2008–2025 layer and no site
  beyond the Δασαρχείο) and the three completions (EREN Λίμνη
  6Ρ9Ξ4653Π8-ΦΑΨ 23.02.2024, Eurobank Rhodes 6Σ3Β4653Π8-9ΦΑ 08.02.2024,
  Εθνική Χίος 91ΧΘ4653Π8-ΛΣΔ 21.08.2026 — its cipher-font text quoted as
  pdftotext reads it, the note giving the plain reading). Stated
  budgets €43.284.256,85 over 43 projects. The public-bodies coverage
  test now reads the sponsored organs from the PROJECT-linked acts (the
  seven needles' 549 unlinked candidates award nothing here) while an
  alias may still match any candidate's organ.
Left open: the three ventures' members by ΑΦΜ (a ΓΕΜΗ excerpt or an award
act would settle them), the Γορτυνίας row on lot 4Β, and the six ΔΑΣΕ
categories if the parked layer ever returns to the pages.
Site check after the load (user, same day): the API and the server-rendered
pages carried the new figures at once (the response cache is DB-mtime
keyed); a browser holding the pre-load page needs a reload, because
`apiGetCached` memoises payloads across client navigations. One genuine
gap found: FROM THE FIRE TO THE SPONSORED PROJECT draws a lane only where
an EFFIS scar dates the fire, so the Aigaleo fire of 31.07.2026 — whose
scar the 2008–2025 layer cannot hold — had no lane and no mention. The
frame's caveat now names, computed, the fires the acts answer but the layer
does not yet hold and their projects («… without a lane until the scar is
published»); the lane itself waits for the EFFIS export (a rebuild of
`effis_fires.geojson` and `link_effis_scars.py`).

**2026-08-29 — KEY FINDINGS gains EVERY CONTRACT, BY THE DAY IT WAS SIGNED**
(user): the STATE-FUNDED dots — one per contract of both programmes, area
∝ stated net € on one scale with the same radius floor — on ONE time axis,
`charts/SignedTimeline.svelte` after the STATE-FUNDED frame in
`sections/KeyFindings.svelte`. The Anti-nero swarm above the axis in ink,
the co-operatives' below it in green, each dodged around its own
centreline (`beeswarm.dodgeVariable`) and shrunk to its band where it
would overflow; the fire seasons (1 May – 31 October) shaded in the site's
one season tint UNDER the dots, year rules, the opening year named at the
axis start (the earliest signature is a co-op contract of July 2021 posted
in September — the axis opens on that month), a hover card with amount ·
date · ΑΔΑΜ linking to the contract page. `/api/compare` `dots` now carry
`d` (the signature date, the registry posting date where a record states
none — `n_date_fallback`, 0 on both sides today, said in the caveat when
non-zero; pinned). The lightbulb states, computed from the dots, the share
of each programme signed inside the fire season and each side's busiest
year. What the drawing shows: the programme is signed in BATCHES — the
2022 spring lots, the 2023 summer lots, the January–March 2024 lots, 2025,
the March 2026 V-PLUS lots — while the co-operatives' contracts run all
year, every year, thickest in the autumns.
Second round the same day (user): NO size encoding — every dot the same
radius (the size said nothing the STATE-FUNDED frame above does not; the
colour alone says the programme, a two-entry key on the frame's first
line) — and NO upper/lower split: ONE swarm of all 2.257 contracts dodged
around a single centreline (`beeswarm.dodge`), the year labels CENTRED on
their rules UNDER the axis at the bottom. The one radius is the largest
the band holds, with a 26 px slack beyond the band before the dots
shrink, so the mass-posting days (hundreds of firewood assignments posted
in one October 2023 week, the tallest column) do not dictate a 1 px dot for
everything; floor 1,5 px.
Third round (user): BIGGER dots that never leave the frame, and no axis
line. A beeswarm cannot do both — the October-2023 week alone would need a
column three frames tall — so the dots sit on a LATTICE (cell = one
2,6 px dot, ~5,9 days per column): each contract takes the free row nearest
the centreline in the column of its signature day, and a full column
spills into the nearest column with room, alternating sides. The frame's
caveat states the largest displacement this forces, computed on every
render (14 days today), and names the date field: the ΚΗΜΔΗΣ
«Ημερομηνία υπογραφής σύμβασης», the posting date only where a record
states none (none today). The year rules stay, the years centred under
them; the axis line is gone.
Fourth round (user): a column is ONE WEEK (the ~6-day column read as an
odd unit), the dots a little smaller, and the Anti-nero dot a little
bigger than the co-operatives' (2,0 vs 1,55 px) so the programme reads
against the mass. Rows 4,4 px; the busiest weeks now displace a dot by at
most 4 days (computed, said in the caveat).

**2026-08-29 — The ΔΑΣΕ card's middle column stays CONTRACT VALUES alone.** A
version with the Anti-nero card's row (AWARD PROCEDURES stack + DIRECT
AWARDS over a shorter swarm) was drawn and rejected by the user the same
hour («no no undo this»); the 2026-08-28 arrangement stands.

**2026-08-29 — The ΔΑΣΕ contract page's DIAGRAM is the Anti-nero radial**
(user: the box-tree «is illegible»; the earlier «make it like the Anti-nero
one» was mis-read as the card page and undone). `ProcurementFamily.svelte`
now takes a link base, the page's own accent for the filled circle and a
caption, and the ΔΑΣΕ page mounts it over a new `family` field of
`/api/dase/contract/<ΑΔΑΜ>` (`queries_extra.dase_contract_family`): the
centre is the CALL the registry's adamChain declares — the AWARD where the
procedure published no call, which is 1.244 of the 1.587 live contracts
with any chain (the direct assignments publish no πρόσκληση) — and the
orbit every contract of that family: the ones in the dataset with their
stated net €, the other lots (non-co-op contractors, refused at harvest)
OUTLINED with «outside the dataset» and no €, counted in the caption. Past
a dozen lots only this contract's label prints (the 33-lot firewood award
24AWRD015231161, the 41-lot Thessaly procurement of which one lot is a
co-op's); the rest stay in their hover titles. `FamilyTree.svelte` stays in
the repo, off the page. Pinned on three contracts.

**2026-08-29 — The methodology page is the author's own text.** The page had
grown to 33 flat sections and ~4.900 words as each layer landed: the same
rule stated in up to four places (the stated-net basis three times, the
even split three times, «paid» four times, «a chain counts once» three
times), a dozen sentences that were change history rather than method
(«until 20.08.2026 …», «decision log, 2026-08-29», «caught in review»), a
section documenting a chart that is parked, fifteen hard-coded numbers
against the site's own rule, one caveat link pointing at an id the page did
not carry (CUMULATIVE DISBURSEMENT → `#payments`, landing silently at the
top), and a fact printed that the API never emits.

**The replacement is the author's own four sections** — Sourcing and
organisation of the data · Document analysis and validation · Analytical
conventions · Limitations, ethics and reproducibility — written for the MA
report and copied VERBATIM (2.012 words). They were fact-checked first
against the databases, the loaders and this log; the author accepted most
corrections (the co-op boundary is PUBLICATION not signature, and seven
contracts signed 28.07–31.08.2021 are inside; the 2.171 → 2.004 exclusions;
the seven title-only ANTINERO-II chains disclosed; the ΜΗΔΑΣΟ claim
softened in §1 to what was established; VIES named as the principal source
of the co-op seats; the reference layers named; the upstream acts' status;
payments attributed to the chain tip; the gross-stated sponsored case; sole
traders; the refused AADE lookup) and declined others, which stay declined:
the umbrella/support exclusions keep one reason for two different cases,
§4 still says the ΜΗΔΑΣΟ register «was not publicly accessible» where §1
says only that no list could be obtained, «the metadata of each document
was cross checked» stands beside the sentence saying the upstream records
were read only when needed, and the AI paragraph does not disclose that the
English renderings of Greek place names are machine-generated and unreviewed.
Raised once; the author's call.

**A fifth section, «Notes on particular charts»** (~500 words, this side of
the work), carries the dozen chart caveats whose subject the four sections
do not contain, each as an `<h3>` with its own anchor: `record-kinds`,
`categories`, `contract-timeline`, `procurement-families`, `payments` (the
id that was missing), `payment-dates`, `cpv`, `dase-cpv-noise`,
`authorities`, `explore`, `compare-bases`, `zero-overlap`. The eighteen
anchors the four sections carry sit on the paragraph — or the span — that
states each rule, so every existing link lands on its explanation.

**Every figure is computed.** New `meta` facts: `kh_records`,
`kh_title_only_n` / `kh_title_only_share` (in scope, ANTINERO II, no ΠΔΕ
code — 7 chains, 1,5%), `kh_categories`, `kh_payments_n` (read on the
PAYMENTS connection: `kh` is the stated-basis view, where the payments
table is deliberately empty), `dase_records`, `dase_pre_window`,
`ana_live`, `ana_with_sum`, `ana_without_sum`, `ana_live_vat_*` (the LIVE
projects' bases, where the older `ana_vat_*` counted the superseded
restatement too). The refresh date prints from `meta.generated` as «29
August 2026», and the same line — «Records last refreshed on … · how these
figures are made» — closes /antinero, /dase, /anadohoi, /story and /explore
(`ui/RefreshLine.svelte`; one line at the end of each page's content, NOT
the footer returning).

**`tests/test_methodology_anchors.py`** holds it: every `methodology="…"`
prop and every `/methodology#…` href in `atlas/src` must resolve to an id on
the page (this is what the broken `#payments` link failed), no bare figure
may appear in the prose (law references, years and the 74 Kallikratis units
excepted), and the page stays under 2.900 words — it is at 2.600.
Same day, second round (author: «I do not think any of those are
particularly important»): **the fifth section is OFF the page**. Its text is
archived in `docs/chart-notes.archive.md`, unpublished. The twelve links it
carried were then resolved one by one on the rule that a caveat link must
lead to an explanation: nine were REPOINTED to the paragraph of the author's
own text that does explain them — work-type categories, procurement
families, the contract timeline, record kinds and the forest authorities to
`#validation` (the documents are read where the metadata is thin, and later
changes are distinguished from the stated terms), payments, payment dates
and the two-dataset comparison to `#stated-basis` (payments are a separate
layer; the net basis is what makes the comparison sound) — and three were
DROPPED, because the four sections make no claim about them: the CPV
roll-up on both dataset pages and the zero-overlap finding on Key Findings.
Those frames keep their caveats; they simply no longer offer a link to an
explanation that is not there. The page is 2.052 words.

**2026-08-31 — The sponsored LOCATION translations are user-reviewed.** The
62 bilingual entries of `anadohoi_locations_en.json` (61 of 2026-08-26 plus
the Aigaleo row of 2026-08-29) were reviewed one by one. Two English
corrections: the Βαρυμπόμπης row keeps its «Τμήμα Πευκόφυτου» in English
(«Pefkofyto, areas in Varympompi, Tatoi, Afidnes of Attica» — its siblings
already kept theirs), and τριπλοκαμένη is «three-times-burnt», not
«thrice-burnt». Everything else stands as written, by the user's explicit
word — including «areas near Kalamas and Acheron rivers» (raised, kept) and
the Katerineza spelling (raised, kept). Both copies updated together
(khmdhs/data + atlas/src/lib/data, byte-identical, pinned). The review debt
recorded since 2026-08-25 is closed.

**2026-08-31 — The municipality layer's tier-C residue: 14 of 15 pairs ruled.**
The 2026-08-19 curation left the pairs with no independent confirmation for a
human verdict; after the freshness haul the curator page counted 15. Ruled one
by one against the documents (user):

**Confirmed as they stand (7 pairs)** — the 2022 ANTINERO-II chains' own
«Άρθρο 7: Τόπος εκτέλεσης» states them verbatim, and every δήμος sits in the
lot's own services' area: lot 3Β (22SYMV011332276) «περιοχές Δήμων
Ομηρούπολης, Χίου, Κίσσαμου, Δήμου Ιωαννίνων» → Χίου/Κισσάμου/Ιωαννιτών; lot
5Β (22SYMV011632177) «εντός των Δήμων Ξυλοκάστρου-Ευρωστίνης, Βόρειας
Κυνουρίας και Νότιας Κυνουρίας»; lot 5Α (22SYMV011332546) the Σικυωνίων of
its three-δήμοι clause. No data change; the verdicts are this entry.

**Split by lot (7 pairs, −7 rows)** — the two 2026 restoration lots of call
26PROC018350831 each carried the WHOLE call's seven δήμοι, because the
extractor read the shared πρόσκληση onto both. The documents split them: the
call places Τμήμα 1 «στο Δήμο Ζακύνθου, Δήμο Πύργου – Αρχαίας Ολυμπίας, Δήμο
Ζηρού – Αρταίων, Δήμο Λασιθίου αντιστοίχως» and Τμήμα 2 «στην περιοχή ευθύνης
του Δασαρχείου Χαλκίδας και Δασαρχείου Λαυρίου … στους Δήμους Λαυρεωτικής και
Σαρωνίδας», and Τμήμα 2's contract heading says so itself («Τμήμα 2: Περιοχές
ευθύνης Δασαρχείων Χαλκίδας και Λαυρίου»). So 26SYMV019488828 (Τμήμα 1 tip)
keeps Ζακύνθου/Πύργου/Αρχαίας Ολυμπίας/Ζηρού/Αρταίων and loses
Λαυρεωτικής/Σαρωνικού (they were 2 of the 3 site flags — flagged precisely
because they belong to the other lot), and 26SYMV018489793 (Τμήμα 2) keeps
Λαυρεωτικής/Σαρωνικού and loses the five. «Δήμο Λασιθίου» is read as the
Π.Ε./Δ-νση Δασών Λασιθίου area — no such δήμος exists and no row is invented
(user). The corrected entries live in contract_municipalities.json AND its
`_overrides`, so a --curate regeneration keeps them. **The same verdict
shrinks Τμήμα 2's region and authority layers**: contract_regions.json
26SYMV018489793 → Π.Ε. Ευβοίας + Ανατολικής Αττικής (was the full 7-Π.Ε.
list, curated 2026-07-19 from contract_objects — which quote the whole
multi-lot project), and a forest_authorities.json contract_override (the 7th)
pins Δασαρχεία Χαλκίδας + Λαυρίου with the heading as evidence.

Layer after reload: **593 rows / 157 contracts / 223 δήμοι, 72 from the
call, 1 unexplained flag** (Γορτυνίας on lot 4Β — its own verdict pending;
explains covers_pe 31 / seat 11 / curated 6 unchanged). The Ανατολικής
Αττικής work-region share moved 11.8 → 11.9 % (pinned). Two side-findings
surfaced by the same dig and NOT yet ruled: the completion acts
ΨΔ574653Π8-Α4Γ (3Β) and ΡΦΚΕ4653Π8-ΦΕΒ (Τμήμα 1) add sibling-lot services to
contracts because their subjects quote the whole project title while their
operative clauses accept ONE area («…όσον αφορά το εργο: … αρμοδιότητας
Διεύθυνσης Δασών Χίου», «χωρικής αρμοδιότητας Δ/νσης Δασών Πρέβεζας») — the
part_authority needles (ΓΙΑ ΤΟ ΤΜΗΜΑ / ΤΜΗΜΑΤΟΣ ΤΟΥ ΕΡΓΟΥ) miss these two
dialects, so ΔΔ Δωδεκανήσου rides on 22SYMV011928850 and Δασαρχεία
Χαλκίδας/Λαυρίου on 26SYMV019488828 via completion_act sources.
Same day, the 15th pair — **Γορτυνίας on lot 4Β: the signed text wins** (user,
after reading the clause in the PDF): Άρθρο 7 of the original 22SYMV011470180
(page 17) places both the μελέτες and the works at «περιοχές Δυτικού Μαίναλου
και Δάσους τέως Δήμου Θέλπουσας Π.Ε Αρκαδίας», while the lot's own label says
«Υποέργο Β, αρμοδιότητας Δασαρχείου Πύργου» (the project spans Δασαρχεία
Βυτίνας ΚΑΙ Πύργου; the Βυτίνας lot was never captured, so no cross-check
exists). Verdict: **Π.Ε. Αρκαδίας is ADDED to the chain's regions** beside
Ηλείας (the label's), the δήμος Γορτυνίας row stops being flagged, and the
authority stays Δασαρχείο Πύργου alone — the document names no other
Δασαρχείο, and none is invented. The municipality layer now carries **0
unexplained flags**; the 4Β € split over two regions moved the even-split
aggregates accordingly. All 15 tier-C pairs are ruled; the 2026-08-19
review debt is closed.

**2026-09-01 — A part-acceptance act credits only the service it accepts.**
The completion layer's subjects quote the WHOLE multi-lot project title, and
the forest_loader's fourth source read every service out of the subject — so
ΔΔ Δωδεκανήσου (a sibling lot's area) rode on the Χίος lot 3Β
(22SYMV011332276/22SYMV011928850, act ΨΔ574653Π8-Α4Γ whose operative words
accept «…όσον αφορά το εργο: … αρμοδιότητας Διεύθυνσης Δασών Χίου») and
Δασαρχεία Χαλκίδας/Λαυρίου (Τμήμα 2's services) on Τμήμα 1
(26SYMV018489783/26SYMV019488828, act ΡΦΚΕ4653Π8-ΦΕΒ, «χωρικής αρμοδιότητας
Δ/νσης Δασών Πρέβεζας»). Fix (user-approved): (1) `part_authority` learns the
two dialects — «ΧΩΡΙΚΗΣ ΑΡΜΟΔΙΟΤΗΤΑΣ» and «ΚΑΙ ΣΥΓΚΕΚΡΙΜΕΝΑ» — accepted only
where the phrase stands OUTSIDE the « » quotes, because a project's own
registered name can carry «Χωρικής Αρμοδιότητας …» (the Λευκάδας ANTINERO-IV
title, verified: guard keeps it whole); (2) `forest_loader.
completion_authorities` restricts an act with a resolved `part_auth` to THAT
service alone, `|part`-marked. `--reextract` over all 290 stored acts changed
exactly the four verified part acceptances (ΨΔ57→ΔΔ Χίου, ΡΦΚΕ→ΔΔ Πρέβεζας,
ΨΚΒΕ4653Π8-ΒΥΑ→Δασαρχείο Αμαλιάδας of the two-service Αμαλιάδας+Βυτίνας lot,
9ΗΕ64653Π8-Ρ4Θ→ΔΔ Θεσπρωτίας for «το τμήμα Α_1» of the three-service 14Α) —
part_auth 23 → 27, the 23 existing untouched; the Δίρφυς act keeps its
title-named |part behaviour. The forest reload removed EXACTLY the six wrong
links and added none: completion-act links 26 → 20 (9 contracts), all links
718 → 712. The lanes gain the four acts' per-part ✔ placement.

**2026-09-01 — Lot 4Α of ANTINERO II found and loaded; how lots go missing.**
Asked whether the Βυτίνα sibling of lot 4Β could be found, the answer came
from the award we already held: 22AWRD011258574 names «για το Υποέργο Α, στον
οικονομικό φορέα «ΛΑΜΠΟΣ ΙΩΑΝΝΗΣ ΚΑΙ ΣΙΑ Ε.Ε.» … με ΑΦΜ 998269962 …
αρμοδιότητας του Δασαρχείου Βυτίνας (με Α/Α ΕΣΗΔΗΣ 191213)», and a live
registry search by that ΑΦΜ surfaced **22SYMV011331269 «ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ
ΕΡΓΟΥ 4A ΤΟΥ ΙΙ»**, signed 27.09.2022, €1.452.610,90 net / €1.801.237,52
gross, no amendment, no payments. Every discovery route had missed it for
three reasons at once: no ANTINERO word in its title («4A ΤΟΥ ΙΙ», Latin A),
no fund code (only `regularBudgetFundedProgramRef C2420902001` — the seven
title-only chains' funding pattern), and a registry record that declares no
call, award or sibling (its adamChain lists itself alone, so the call's own
chain never showed it). The user's decision: **in**, as `antinero_ii` via
`antinero_supplement.json` (basis `title:ΤΟΥ ΙΙ`, the precedent of its sibling
22SYMV011470180; verify_relevance accepts «ΤΟΥ ΙΙ»). Curated with it: region
Π.Ε. Αρκαδίας, an 8th forest `contract_override` → Δασαρχείο Βυτίνας (the
registry object text names both lots' services), category dasotexnika with
its own verbatim title, and the machine readings of its text (study & works
from the template clause, themes καθαρισμοί + οδικό δίκτυο, 3 months from
signature, δήμος Γορτυνίας). **New mechanism, evidence-bound:**
`khmdhs/data/family_curation.json` — the contract cites its πρόσκληση («η από
10.08.2022 Πρόσκληση») and κατακύρωση (16.09.2022) by DATE only, while the
ΑΔΑΜ are established by the family's other documents (the sibling's declared
chain, the award naming this winner); families_loader appends such rows with
source «curated», each carrying the contract's own citing sentence and the
document that supplies the ΑΔΑΜ (`tests/test_families.py` checks the excerpt
is verbatim in the cached text and the evidence names the ΑΔΑΜ). Lot 4Β needed the same rows — its own text also cites the call and award by
date only (its link came from the registry chain, which the families layer
does not read) — so both lots are curated symmetrically, the rows are merged
BEFORE the inheritance walk and the amendment 23SYMV011953055 inherits them;
the diagram now draws 4Α beside 4Β around 22PROC011082770 (families 222
in-scope contracts → 136 calls; network: 55 multi-lot calls, 146 contracts in
them).

**How often does a lot go missing?** Three measures the same day: the
registry-declared families of all 264 known calls/awards, swept live, name
ONE contract we lack — 23SYMV013599468, the CANCELLED duplicate posting of
the Αλίαρτος nursery contract (held as 23SYMV013600200); the 39 cached award
texts name one unheld lot (4Α); the 142 cached call texts define more lots
than we hold in three procurements: 22PROC011082770 (4Α, resolved),
**24PROC014153399** (7 τμήματα, we hold 3/4/6; the only award the registry
links awards exactly those three and is silent on 1, 2, 5, 7) and
**25PROC016402950** (Εύβοια 2025, 3 τμήματα, we hold 2 and 3; the two awards
cover 2 and 3). No Diavgeia act cites a contract for the missing τμήματα.
Left OPEN pending the user's word on how far to chase (ΤΑΙΠΕΔ/ΥΠΕΝ awards by
organisation and date window; ΚΗΜΔΗΣ web search read for the Α/Α ΕΣΗΔΗΣ;
ΕΣΗΔΗΣ itself). Lesson recorded: the registry's own linkage is NOT where lots
go missing — they go missing when a contract is posted with no programme word
in its title, no fund code and no declared family; an award's winner list is
a discovery route the scripts do not yet run.

**4Α's Article 7 re-opens the Γορτυνίας verdict.** Its «Τόποι εκτέλεσης»
sentence is IDENTICAL to 4Β's — «περιοχές Δυτικού Μαίναλου και Δάσους τέως
Δήμου Θέλπουσας Π.Ε Αρκαδίας» — so in this procurement the clause is the
Βυτίνα lot's (or the whole project's) area pasted into both contracts, not a
lot-specific statement. The 2026-08-31 verdict (Αρκαδίας added to 4Β, its
Γορτυνίας row kept) was taken when no cross-check existed; the user has been
asked to confirm, revert, or re-flag. Nothing changed on 4Β pending that word.

Also this day: the full extension-acts search re-ran for the new contract
(no resume mode) and picked up **three new acts** posted 31.08.2026 — the
4th extensions of the three ΕΣΑ lots of 29.05.2024 — 467 → 470 acts, 21
«whole» extensions; 4Α itself has none.

Basis after the add: **254 in scope, €633.588.292,66 net / €785.649.482,93
gross; II 59; dasotexnika 162; 14 / 137 / 103; 404 theme links over 210; 594
municipality rows / 158 contracts / 223 δήμοι, 0 flags; 8 title-only chains
(1,7 %); families 222 in-scope contracts → 136 calls.** Every pin moved
accordingly.

**2026-09-01 — Γορτυνίας on lot 4Β: the row stays, flagged again (user).**
With 4Α's text in hand the Άρθρο-7 clause is proven to be the Βυτίνα lot's
area pasted into both contracts, so Π.Ε. Αρκαδίας leaves 4Β's regions (back to
Ηλείας, the lot's «αρμοδιότητας Δασαρχείου Πύργου»), and the δήμος Γορτυνίας
row — what the document states — stays on 4Β as an UNEXPLAINED flag, with the
paste as its note. The municipality layer carries 1 flag again (594 rows / 158
contracts / 223 δήμοι); 4Α keeps Αρκαδίας and its own Γορτυνίας row, which
there is consistent with its lot. The 2026-08-31 verdict is superseded.

**2026-09-01 — The two open procurements, chased (user: «go on with your
recommendation»).** Route: the issuing organisations' own Diavgeia acts
(luminapi `organizationUid:<uid> AND subject:"<phrase>"`, dates parsed from
the DD/MM/YYYY `issueDate`), every hit read for the lots' Α/Α ΕΣΗΔΗΣ.

*25PROC016402950 (Εύβοια 2025, Τμήμα 1, Α/Α ΕΣΗΔΗΣ 212495) — CANCELLED.*
The issuer is ΕΕΣΥΠ (HCAP, uid 100074686; Διενεργούσα Αρχή, ΥΠΕΝ the
Αναθέτουσα). Act **ΨΦ2Χ46ΝΩΑ7-Ψ25 of 06.11.2025**: «Έγκριση Πρακτικού ΙΙΙ …
και ματαίωση της ανοικτής διαδικασίας … για το Τμήμα 1 … (Α/Α ΕΣΗΔΗΣ: 212495)
… καθώς η εκτέλεση του εν λόγω Έργου δεν ενδιαφέρει πλέον την Αναθέτουσα
Αρχή» (ΥΠΕΝ/ΔΠΔ/122971/8335/05.11.2025), after the 28.06.2025 προδικαστική
προσφυγή of «ΣΑΚΚΟΣ Χ. & ΣΙΑ Ε.Ε.» against the provisional award to GREEN
CONSTRUCTION ΑΤΕ. No contract exists; nothing is missing from the dataset.

*24PROC014153399 (ΤΑΙΠΕΔ, 19.01.2024, seven τμήματα; we hold 3, 4, 6) —
RE-PROCURED, inferred.* Of 118 ΤΑΙΠΕΔ acts of 2024–25 read, only the call
summary and the award we hold (9ΓΨ846ΜΩΝ1-ΛΧ5 / 24AWRD014696933, awarding
3, 4, 6) name the Α/Α ΕΣΗΔΗΣ of τμήματα 1, 2, 5, 7; no άγονο/ματαίωση act
exists for them and the award's recitals are silent on their fate. But
ΤΑΙΠΕΔ issued four separate «Προσκλήσεις υποβολής προσφορών» (the ν.998/1979
αρ. 16 παρ. 5 direct-invitation route) on 15–18 April 2024 for EXACTLY the
four area bundles of those τμήματα, each awarded within weeks — and all four
contracts are in the dataset: τμήμα 1's areas (ΔΧ Αταλάντης, Σπερχειάδας,
Λαμίας, Θήβας, Λιβαδειάς) → 24PROC014597593 → **24SYMV014809263**
(22.05.2024); τμήμα 2's (ΔΧ Χαλκίδας, Δήμος Χαλκιδέων) → 24PROC014607187 →
**24SYMV014749238** (13.05.2024); τμήμα 5's (ΔΧ Λάρισας, Τρικάλων,
Καρπενησίου, Αγιάς, Ελασσόνας, Τσοτυλίου, ΔΔ Πιερίας) → 24PROC014615504 →
**24SYMV014774679** (17.05.2024); τμήμα 7's (ΔΧ Νιγρίτας, Σερρών,
Σιδηροκάστρου) → 24PROC014624686 → **24SYMV014774694** (17.05.2024). Neither
the April calls nor the contracts cite the January procedure — the link is
area-identical and time-consistent, not stated, and is recorded here as an
INFERENCE. Nothing is missing from the dataset; no record changed.

Method lessons recorded: the registry's declared families never showed either
gap; the calls' lot tables did. An award's winner list (4Α) and an issuer's
Diavgeia acts read for the lots' Α/Α ΕΣΗΔΗΣ (Εύβοια) are discovery routes the
scripts do not run yet.

**2026-09-01 — `place_names_en.json` is user-reviewed.** The 646
machine-proposed English renderings of the entity pages' registered-office
strings (2026-08-26) were reviewed by RULE, not entry by entry: 435 are plain
toponym transliterations, 211 carry a number, an abbreviation or a building
word, and those reduced to ten rules and five single verdicts. Accepted (user):
**A** «γγ» → «ng» (ELOT 743's own rule, which `_translit` lacks: Syngrou,
Angelou, Mesolongi, Archangelos ×2); **B** a word starting with «Μπ» takes
the familiar «B» and its inner «μπ» follows (Bouboulinas ×2, Bonou — an inner
«μπ» elsewhere keeps «mp»); **C** a letter after a building number stays a
capital label (13A, 118B, 10A, 14A — never «13a»/«118v»); **D** a bare «Λ»
is Λεωφόρος (Leoforos Stamatas 5; «Λ.» with a dot stays an initial); **E**
«Πλ.» is Plateia; **F** «Τέρμα X» stays «End of X»; **G** a bare number before
ΧΙΛ is an ordinal (3rd km Dramas – Serron); **H** «εντός οικισμού» drops
before a PO Box; **I** date-streets keep their Greek form (25is Martiou —
the 26.08 rule). Declined: **J** foreign names by letters stay (Viktoros
Ougko 10, not «Victor Hugo»). Singles: «Οδός των 118, αρ. 37» → «Odos ton
118, no. 37»; «Περιοχή ΖΕΠ» → «ZEP area»; «αγροτεμάχια 567 & 584» → «plots
567 & 584»; «Δασικό Κτίριο» → «Forestry Building»; «Μ. Αλεξάνδρου,
Διοικητήριο» → «Megalou Alexandrou, Administration Building». The rules
live in `scripts/build_place_names_en.py` (`_familiar`, `NUM_SUFFIX`, the
«Λ»/«ΠΛ.» branches; the singles in `OVERRIDES`), so a rebuild keeps them,
and `_translit` itself is untouched — it feeds the geocoder and stays
ISO-843. Rebuilt: exactly 19 entries changed, both copies byte-identical.
The review debt of 2026-08-26 is closed.

**2026-09-01 — Two of the three 2022 ventures documented from the ΓΕΜΗ
register; the third is in no register.** The user asked for the three
ANTINERO-II ventures whose contracts name members without ΑΦΜ to be resolved
through ΓΕΜΗ's publicity API. The publicity DETAILS payload carries the
members at `companyInfo.payload.managementPersons` — one level ABOVE the
`company` object `khmdhs.gemi.company_details` returns, which is why a
company-object read shows nothing. Read there: **996813233 Κ/Ξ ΒΑΛΛΑΣ –
ΟΙΚΟΝΟΜΟΥ** (ΓΕΜΗ 166857453000) = ΒΑΛΛΑΣ ΔΗΜΗΤΡΙΟΣ 148450918 «Εταίρος - Μέλος»
50 % + ΟΙΚΟΝΟΜΟΥ ΙΩΑΝΝΑ 031213597 50 %, both from 27/10/2022 (liquidators from
05/12/2025 — the venture is struck off); her register ΑΦΜ is the one she
holds in-scope contracts under in her own name, corroborating the match.
**997080215 Κ/Ξ ΑΔΡΑΝΗ ΥΛΙΚΑ ΘΕΣΣΑΛΟΝΙΚΗΣ – ΜΗΤΟΓΛΟΥ** (ΓΕΜΗ 165541904000) =
ΑΔΡΑΝΗ ΥΛΙΚΑ ΘΕΣΣΑΛΟΝΙΚΗΣ Α.Ε. 999126094 «Μέλος & Διαχειριστής» 90 % +
ΜΗΤΟΓΛΟΥ ΑΙΚΑΤΕΡΙΝΗ 045210926 10 %, from 07/09/2022 (ΥΠΟ ΕΚΚΑΘΑΡΙΣΗ since
20/01/2026). Curated with the 2026-08-20 conventions (source `gemi:<number>`,
the register row verbatim as excerpt, `gemi_percentage` as metadata; the even
split stays). **996870694 Κ/Ξ ΠΑΠΑΓΕΩΡΓΑΚΗΣ – ΚΟΣΜΙΔΗΣ** is in no ΓΕΜΗ
register (search by ΑΦΜ: not found) and its family holds no award act, so it
stays `members_documented: false` — a name is not evidence. Loaded: 62
ventures, 50 with members (was 48), 102 member links (98), 70 distinct firms
(66), 12 undocumented (14).

**Found on the way, NOT applied:** the same read now returns members for
NINE of the eleven ventures the user left undocumented on 2026-08-20
(ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΣΠΟΡΑΔΩΝ 2025, ΑΓΓΕΛΑΤΟΣ–ΜΑΝΑΡΙΤΣΑΣ–ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ,
ΗΛΙΟΠΟΥΛΟΣ-ΠΑΡΛΑΝΤΖΑΣ–ΓΑΙΟΣΤΑΤ, ΓΚΑΤΖΙΟΣ–ΤΑΣΚΟΥΔΗΣ, ΔΡΑΜΗΤΙΝΟΣ–ΜΠΟΥΡΑΣ,
ΖΑΜΠΑΣ–ΠΡΑΞΙΣ, ΓΚΙΚΑΣ–ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ–ΑΓΓΕΛΑΤΟΣ, ΔΗΜΗΤΡΙΟΥ–ΛΑΜΠΟΣ,
ΝΤΑΝΟΣ–ΣΚΑΝΔΑΛΟΣ) — every one with ΑΦΜ, capacity, percentage and date, i.e.
exactly the evidence the standard asks for. **Correction of the record (same
day, after the user asked what had changed): NOTHING changed at the register.**
The 2026-08-20 sweep (`sweep_gemi_members.py`, still in the session scratchpad
with its output `gemi_member_sweep.json` of 20.08 19:09) fetched these very
rows that day — they are in its output, filed under `other_roles` — because
its filter counted as a member only a row whose role STARTS with «Εταίρος»;
these nine ventures' rows read «Μέλος & Διαχειριστής» (3) or «Μέλος,
Διαχειριστής & Εκπρόσωπος» (6) and were set aside. Batch B caught the first
of those spellings and re-read FIVE ventures by hand, but the other nine were
never re-read, and the batch-B entry's closing sentence («9 with a ΓΕΜΗ
record that lists no member rows») was written from the proposals file, which
had dropped the set-aside rows. So the 2026-08-20 statement was wrong, and the
first explanation offered today (a `company`-object read) was wrong too — the
sweep did read `managementPersons`. Proposals for the nine sit in the
scratchpad; they wait for the user's word (they would move the «by member
firm» ranking). Only ΛΙΑΡΗ–ΓΚΙΚΑΣ and ΤΣΙΑΝΑΒΑΣ–Μ.&Κ. have no register at all.

**2026-09-01 — Batch C: the nine ventures documented from the register
(user: «apply the nine»).** ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΣΠΟΡΑΔΩΝ 2025 (ΑΓΓΕΛΑΤΟΣ
075195407 50 / ΖΑΒΙΤΣΑΝΟΣ 042820089 50 — the πρόσκληση invites Ζαβιτσάνος
under 073449705, a discrepancy kept on the record, unreconciled);
ΑΓΓΕΛΑΤΟΣ–ΜΑΝΑΡΙΤΣΑΣ–ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ (054537472 50 / 075195407 25 /
122499275 25, dated by the register 10/05/2023 — after its 2022 contracts;
recorded as stated); ΗΛΙΟΠΟΥΛΟΣ-ΠΑΡΛΑΝΤΖΑΣ Ο.Ε.–ΓΑΙΟΣΤΑΤ Ε.Ε. (800349931 50 /
998731143 50); ΓΚΑΤΖΙΟΣ–ΤΑΣΚΟΥΔΗΣ/ΓΚΑΤΖΙΟΣ Ι.Κ.Ε. (038925014 70 / 998746814
30); ΔΡΑΜΗΤΙΝΟΣ & ΣΙΑ Ε.Ε.–ΜΠΟΥΡΑΣ & ΣΙΑ Ε.Ε. (999448728 60 / 998126035 40);
ΖΑΜΠΑΣ–ΠΡΑΞΙΣ ΤΕΧΝΙΚΗ Ε.Ε. (042971088 50 / 999735729 50);
ΓΚΙΚΑΣ–ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ–ΑΓΓΕΛΑΤΟΣ (073533221 50,56 / 122499275 24,72 /
075195407 24,72); ΔΗΜΗΤΡΙΟΥ–ΛΑΜΠΟΣ (051122328 50 / 051955363 50 — the
PERSON Ιωάννης Λάμπος, not his firm ΛΑΜΠΟΣ ΙΩΑΝΝΗΣ ΚΑΙ ΣΙΑ Ε.Ε. 998269962);
ΝΤΑΝΟΣ–ΣΚΑΝΔΑΛΟΣ (044397659 47 / 036343031 53). Conventions of 2026-08-20:
source `gemi:<number>`, the register row verbatim as excerpt, percentage as
`gemi_percentage` metadata only, the even split untouched; a member's display
name is the site's curated one where the ΑΦΜ already has one (ΑΓΓΕΛΑΤΟΣ,
ΜΑΝΑΡΙΤΣΑΣ, ΣΤΑΜΑΤΟΝΙΚΟΛΟΣ, ΓΚΙΚΑΣ, ΔΗΜΗΤΡΙΟΥ, ΛΑΜΠΟΣ, ΝΤΑΝΟΣ, ΣΚΑΝΔΑΛΟΣ,
ΓΚΑΤΖΙΟΣ … are contractors in their own right), the documented form with
patronymic where a family document gives it (ΖΑΜΠΑΣ ΣΤΥΛΙΑΝΟΣ ΤΟΥ ΔΗΜΗΤΡΙΟΥ),
the register's otherwise. Loaded: **62 ventures / 59 documented (122 links,
79 firms) / 3 undocumented** — ΠΑΠΑΓΕΩΡΓΑΚΗΣ–ΚΟΣΜΙΔΗΣ, ΛΙΑΡΗ–ΓΚΙΚΑΣ and
ΤΣΙΑΝΑΒΑΣ–Μ.&Κ., none of which any register or document names.

**2026-09-01 — `/story` becomes a three-column scroll narrative (phase 1: the
shell).** The author redesigned the page START HERE leads to in two 1920×1080
artboards: a vertical TIMELINE on the left, the NARRATIVE in the middle, and on
the right the IMAGE with its caption and, under it, the passage's FOOTNOTES. The
timeline opens COLLAPSED — three lanes converged on one dotted line, the years
beside it, the legend stacked — and SPREADS into three solid lanes (global/EU
grey, Greece black, fires red) when the reader's text reaches the first dated
event; the years move to the far left and each label rides out over its own lane.
Every bullet will be bound to the passage that mentions it, and the right column
follows the reader too. The ten-chapter strip is DELETED; the heading row now
names the chapter the reader is in, and the timeline is the navigation.

Decisions taken with the author before building: **KEY FINDINGS stays inside the
story, but its six charts become RIGHT-COLUMN figures** at that column's width,
with the author's own text beside them (not a full-width band — phase 3, and it
needs a legacy-anchor map because a chart in a sticky rail cannot be scrolled to);
the timeline's small text is set in **futura-100-greek-book**, the site's own body
face, because the artboards' Degular Text is not in the Typekit kit and will not be
added (blocks run ≈1 line longer than drawn); once spread, **every event's text
shows in grey with the active passage's lit**, as the artboard draws it; and the
work is staged — shell, then the timeline's behaviour, then the content — because
the author is finalising a presentation.

**What phase 1 ships.** `main.story` in the layout (window-wide, letterboxed above
1920 so the 570px reading measure never grows); the three columns as `fr` tracks
carrying the artboard's own numbers, measured on the running page at 60/520,
610/570, 1250/594; `lib/story/steps.ts` — ONE IntersectionObserver with a ~1px
band 45 % down the viewport (scrollama's technique), no scroll listener, nothing
per frame, and `active = null` above the first passage, which IS the collapsed
state, for free; `lib/story/StoryTimeline.svelte` and `lib/story/StoryFigure.svelte`;
and `lib/transforms/storyTimeline.ts` + its vitest for the pure year scale.

Three things the artboards taught, encoded so they cannot be lost: the vertical
scale is IDENTICAL collapsed and spread, so the transition is purely horizontal
(one `class:expanded`, CSS transitions only — and a `<line>`'s x1/x2 are
attributes, untransitionable, so the wrapping `<g>`'s transform is what moves);
the axis is piecewise-linear at ~81.4px a year with 2016–2018 compressed and 2017
spaced but unnamed; and the whole 2016–2026 span fits one screen at the design
size, so no panning is needed. Everything is authored 1:1 in artboard coordinates
inside a single `transform: scale(k)`, so SVG geometry and HTML type scale
together and cannot drift.

Two rules for whoever touches it next: **beats must TILE** (rhythm in padding
inside `.beat`, never margin between them, or the reading line falls in a gap and
the active passage flickers), and the placeholder `min-height: 62vh` on a beat is
PHASE-1 ONLY — the author's passages are many paragraphs each and remove the need
for it. Verified on the running page: the timeline opens collapsed, spreads once
at the second passage, un-spreads on the way back, the heading tracks the chapter,
the right column swaps without the page jumping, everything releases to one column
at 1100px, and `/compare#pe-scatter`, `/story#signed-timeline` and `/story#fire`
all still land in view. 621 pytest + 156 vitest, `npm run check` clean.

**2026-09-01 (second entry) — The three dataset cards carry the author's own
text, and its figures are LIVE.** The author delivered
`Website_Text_Storyboard.docx` (INVESTIGATIVE-REPORT/): the opening question,
the chronology narrative in 18 paragraphs with 16 real Word footnotes, a timeline
disclaimer, the methodology already on the site, key findings, the three card
texts and a bibliography. Their three card sections are now
`atlas/src/content/datasets/{anadohoi,antinero,dase}.md`, verbatim — the
placeholder columns of 2026-08-27 are gone.

**Every data-derived figure in that prose is a token, not a digit**, and the
draft proved exactly why: written on 31.08 it said «253 AntiNero contracts» and
«€632.14 million», which lot 4Α had already made 254 and €633,59M by the time it
arrived. `lib/story/Num.svelte` + `lib/story/numbers.ts` read the figure from the
page's own payload at render time (`page.data.overview.kpis` on /antinero and
/dase, `page.data.o.kpis` on /anadohoi — no page changes needed), so a refresh
can never leave a sentence lying. Fourteen keys: the three counts, totals,
medians and contractor/co-op/body/service counts the text uses. Formatting is
ENGLISH PROSE on purpose («2,004 contracts», «€633.59 million», «€5,792») — the
site's own `eur()`/`grInt()` are European and belong in tables and charts, not in
a sentence. `numbers.test.ts` fails on a token the registry cannot supply, on a
file that uses one without importing it, and pins the formatting; it reads the
content through Vite's raw glob rather than `node:fs` so svelte-check stays clean
without adding `@types/node`.

One figure was deliberately NOT wired: «around three quarters concern the
assignment of firewood». The share is computable (1.463 of 2.004 = 73%) but only
from the ΔΑΣΕ work-type layer the author parked on 2026-08-23 as not yet
verified, so it stays the author's own rounded characterisation rather than a
number drawn from a layer the site does not show. Flagged to the author.

Verified on the running cards: no unresolved token on any of the three, the
prose's figures equal the KPI cards above them to the cent, and the text column
scrolls inside the card (67–132px), which is the cards' own established
behaviour — nothing is clipped away.

Also that day, on the author's word: the story's column titles (TIMELINE, and the
chapter over the middle column) are now the dataset card's own name style —
`obviously-narrow` 900 at 24px/28.8px with 0.02em, verified identical to
«ANTI-NERO PROGRAMME» on /antinero — and the duplicate chapter heading over the
text was dropped, since the artboard names it once. The timeline's legend became
the card pages' GRAPH-title style (`obviously` 700, uppercase, 12px): the author
could not read it as sentence-case body type, and a display face in capitals
carries at that size. Spreading it exposed a collision, so each label now holds
its own slot width and the three share one baseline above their rules, as Page02
draws them. The figure column's caption and footnotes are set to the IMAGE's
width (540px), not the column's.


## 2026-09-01 — the story timeline's 31 events, from the author's own `Timeline.xlsx`

The author supplied `13_MARA/INVESTIGATIVE-REPORT/Timeline.xlsx` — the events
the story's left column draws. Columns: CATEGORY · START DATE · END DATE · KEY
TITLE · EXPLANATION TEXT. **31 rows**, imported MECHANICALLY by
`scripts/import_story_timeline.py` into `atlas/src/lib/story/events.ts` —
nothing is retyped, the script rewrites only the data between the module's own
markers (so the notes explaining the folds cannot be silently dropped), and it
was verified to reproduce the committed file byte-for-byte. That gives **8 fires · 18 Greek events and laws · 5
global/EU acts**, from the Peloponnese fires of 24.08.2007 to the N.E.C.C.A.
carbon-units tender of 26.03.2026. **7 rows carry a later END DATE** and are
therefore periods, not days — the four fires of August 2021, Rhodes, Evros, and
the fortnight of 112 alerts — and are drawn as capsules. **12 rows carry no
EXPLANATION TEXT**; they print as date and title, which for a fire is the whole
statement.

Two things happen to the sheet on the way in, both mechanical, both recorded in
the module's own header:

1. **The CATEGORY column is written four ways** — «Global events& EU Legislation
   changes» (rows 7–8, no space) and «Global events & EU Legislative changes»
   (rows 9, 28, 31) are one lane, and Sheet2 carries the three canonical names
   («… Legislative changes in Greece», where Sheet1 says «legislation»). The
   importer folds all four onto the three lanes `world | greece | fire`. A
   spelling it does not know STOPS the import rather than inventing a lane.
2. **`id` is a short slug of the title** — the anchor a bullet and its passage
   will be bound by, so it must stay stable across a re-import.

Three consequences the data forced on the design, all in
`transforms/storyTimeline.ts` where the scale lives:

- **The axis now starts in 2007, not 2016.** Two events sit before the
  artboard's first year (the 2007 fires, Law 3889/2010) and nine years separate
  them from the story proper. They are drawn as two short compressed steps and
  the lanes carry a **break mark** at each, so the compression can never be read
  as duration. Stops are no longer one per year; `yOfDate` interpolates inside
  whichever pair brackets a date.
- **2021 is given 260 px against a plain year's 81.4.** It carries twelve of the
  thirty-one events and eight of them inside one fortnight of August; at an even
  pitch those eight sit inside three pixels. 2023 (Rhodes, Evros and their two
  committees) is given 110.
- **The rail became a viewport that pans.** Thirty-one blocks of text cannot be
  read at once in a column one screen tall, so the drawing is ~1.270 px and the
  column follows the reader down it. The DOT always keeps its true date; where
  events crowd, the BLOCK moves down and a leader line joins it back — the
  layout is pure and tested, and the component decides no position. Titles clamp
  to four lines and bodies to two, the same clamp the height estimate assumes
  (the CSS takes it from the module, so drawing and maths cannot drift).

**What the spreadsheet does NOT carry is the binding column** — which paragraph
of the narrative mentions each event. That is the author's own requirement
(«every bullet of the timeline is linked with the text where this event is
mentioned»), and it cannot be inferred from a date. Until the narrative is
placed, `StoryEvent.beat` is unset on all 31 rows, the rail pans by the reader's
progress instead of by the event, and the year printed large is simply the year
in view. Clicking a bullet is wired and does nothing until a beat is set.

Flagged to the author, not corrected: the sheet spells the same fire two ways —
«Fires in the Peloponnese» (2007) and «Fires in the Peloponese» (2021).

## 2026-09-02 — the report's texts distributed into the author's own markdown files, with live figures

The author renamed the story's nine content files themselves and set the task:
distribute `Website_Text_Storyboard.docx` into them, losing neither the
footnotes nor the `[FIGURE xx: name]` markers, with every dataset-derived
number corresponding to the dataset — then channel the texts into the site.

**The distribution** (a one-off scratch script; the .md files are now the
source of truth the author edits): nine sections → nine files —
`introduction` · `chronology` · `timelinedisclaimer` · `methodology` ·
`keyfindingandopenquestions` · `financedbyprivatecompanies` ·
`antineroprogramme` · `coops` · `bibliography`. Verbatim text; the author's
red `[FIGURE xx: name]` markers stay IN the text exactly where they placed
them (they are the link between the chronology and the images to come); the
18 real Word footnotes become inline superscripts plus a numbered list at the
end of each section, in the document's own numbering (introduction 1–2,
chronology 3–18). The methodology's four sub-titles render as sub-headings.
`chapters.ts` now carries the author's nine sections (the scroll's beats, the
heading row's titles), and `/story` renders the whole report.

**The live figures**: every number in the text that reflects the datasets is a
`<Num>` token read at render time — and the exercise proved the rule again,
because the storyboard already disagreed with the data in four places
(«Seven chains … 1.5 per cent» where the data answers eight/1.7 since lot 4Α;
«253 contracts … €632.14 million» where it answers 254/€633.59M; the refresh
date). `numbers.ts` keys now read THREE payload shapes in order — the card
pages' overview kpis, `/api/meta` (which the root layout already loads
everywhere), and `/api/compare` — and KEY FINDINGS' comparisons are DERIVED
client-side from the compare payload (the value ratio, the count ratio, the
share of co-op contracts below the smallest AntiNero contract, the peak year
and its €). Two figures the text quotes had no computed source, so `/api/meta`
gained them, pinned: `anadohoi.n_companies` (36, counted as the sponsor
ranking counts) and `facts.dase_forest_eur` (€28,542,815.37 through forest
offices/directorates, on the same per-contract pass the /dase delegation
diagram reconciles with — the author's «around €28.5 million» to the word).

**Liberties taken and disclosed, each reversible**: the section title prints
«BIBLIOGRAPHY» where the document writes «Bibiography»; the Kalabokidis
bibliography entry had its own 779-character abstract pasted after the DOI —
removed as a paste accident, the citation kept; two sentences were reworded to
carry a computed figure («more than twenty times» → «more than 21 times» via
the ratio token, and «larger than more than 95 per cent» → «larger than
N per cent», computed exactly). Figures that are the author's own research —
85 deaths, 104, the hectares, the €60,000 ceiling, the 74 Kallikratis units —
stay literal, as they should.

## 2026-09-02 — the story page brought onto the author's Page01 artboard

Four rulings from the author, applied together (their Page01.svg studied
against the running page):

1. **Footnotes present as the artboard draws them** — under the figure in the
   RIGHT column: the «Figure xx _ name» caption line under the image, then a
   small «Footnote» label, then the notes in TWO columns at the image's width,
   12 px light. The .md files stay the single source: the page reads each
   section's RAW file (its first `[FIGURE xx: name]` marker and the numbered
   list after the closing `---`) and the narrative column HIDES both — the
   markers are wrapped `<span class="figmark">` in the files so CSS can hide
   them, and the section-end note lists hide as `hr ~ ol`. Nothing was moved
   out of the author's files.
2. **The titles never move** — TIMELINE, INTRODUCTION, CHRONOLOGY … pin at the
   exact height they first render (`--story-top` = header + the page's own top
   padding, defined in the layout) instead of riding up to the header on
   scroll; a paper strip above them covers the text that scrolls past.
3. **The methodology's four sub-chapters step back down** — Futura (the text
   face), 16 px, sentence case: sub-chapters of METHODOLOGY, not display
   titles. METHODOLOGY itself titles the section like every other.
4. **The collapsed timeline shows its dots and capsules** on the converged
   dotted line, coloured by lane — Page01 draws them there; only the event
   TEXT (and the leader lines) wait for the spread.

Answered the author's question in passing: the two sentences reworded to carry
computed figures both sit in `keyfindingandopenquestions.md` («more than
twenty times» → «more than 21 times» via the value-ratio token; «larger than
more than 95 per cent» → «larger than N per cent», computed from the compare
payload's per-contract values).

## 2026-09-02 — the timeline owns its disclaimer, and the figure column rises

Four more rulings from the author, applied:

1. **The timeline disclaimer is not a narrative section.** It prints UNDER the
   timeline, LEFT of the collapsed line — before it splits into the three
   lanes — right-aligned against the line, fading when the timeline spreads.
   `timelinedisclaimer.md` stays the source (the rail reads the raw file);
   the DISCLAIMER FOR TIMELINE section left `chapters.ts`.
2. **The lane titles sit to the RIGHT of the line at that same point** —
   under the axis, opposite the disclaimer — instead of stacked above the
   years. When the timeline spreads they ride out over their own lanes as
   before. The collapsed fit gained ~200 px for the below-axis block.
3. **The image rectangle rises** so its top aligns with the pinned section
   title (the figure rail pins at `--story-top` with the heading row's
   3.2 rem returned to it), and **the caption hugs the rectangle's lower
   edge** (row-gap sp-2).
4. **The footnote texts get the freed room** (~90 px taller block, leading
   1.3). The author does not want the notes to SCROLL; the chronology's
   sixteen still overflow, and the options were put to them: shrink the
   square on note-heavy sections · smaller notes in three columns · notes
   that follow the reading position within the section (per-paragraph
   granularity — the right fix, more work). Their pick pending; the scroll
   stays only where the set cannot fit.

## 2026-09-02 — everything on /story follows the reader, at paragraph level

The author's ruling on the footnote options — «the footnotes should follow the
reader, and also that is what the timeline should do; the images on the
figures have to work accordingly» — built as ONE mechanism, since all three
are the same question: where in the text is the reader?

**`lib/story/content.ts`** parses the author's own .md files into ordered
BLOCKS (paragraphs and sub-headings), each knowing its section, its footnote
superscripts and the `[FIGURE xx: name]` marker it carries; the page pairs
these one-to-one with the rendered elements, gives each paragraph its block id
and registers it on two observers — the reading line (which paragraph is
active) and plain visibility (which paragraphs are on screen). From that:

- **the figure in force** is the author's own marker, carried forward — the
  document already said which figure corresponds to which part of the text,
  and that information now drives the slot;
- **the footnotes shown** are only those of the paragraphs on screen — never
  more than a screenful, so the scroll is gone by construction;
- **the timeline** lights the active paragraph's events and pans to their
  date (`focusDate`, falling back to reading progress between bound
  passages), and a bullet click scrolls to the exact paragraph.

**`lib/story/bindings.ts`** is the curated event↔paragraph map under the
author's standing policy (17 named events to the paragraph naming them, 4
unnamed fires to the paragraph covering their moment, 10 unmentioned acts as
unbound context): each binding is a VERBATIM needle from the author's text,
resolved by substring at runtime, so their edits are free until they remove
the phrase itself — at which point `content.test.ts` (11 tests) fails loudly.
It also pins: 13 figures once each in order, 18 notes referenced once each in
order, figure carry-forward, and the four 2021 fires sharing the season's
paragraph.

One disclosed touch to the author's file: `chronology.md`'s first paragraph
carried the markers of figures 03 and 04 MID-paragraph — the marker is the
author's own «the image changes here», so the paragraph now breaks at those
two points (two newlines; not a word changed). Without the split the figure
could not follow inside that paragraph.

## 2026-09-02 — Figure 04 of the story: the 75 «112» alerts of August 2021, looping on one national satellite frame (user)

**The request.** The author's `[FIGURE 04: 112 emergency alerts]` marker sits on
the chronology paragraph «The 2021 fire season was the first one during which
112 emergency alerts were used…». The user built this map once before, in the
sibling repository `evia-wildfire-timeline` (`/alerts`: Astro + React +
MapLibre GL over Esri World Imagery / OpenStreetMap raster tiles, a d3
scrubber, a bottom-left detail card, +/− zoom buttons), and asked for it here
with the site's own tools and looks: satellite only, no basemap toggle, no zoom
panel, no bottom-left panel, a loop, the village told to leave BLACK and the
village it was sent to WHITE, and the original's problems fixed. Decisions
taken with the user on 2026-09-01/02: the base «the same as the original», the
burnt area as a flat fill in the site's fire colour (the alternative — the
post-fire ground revealed through the pre-fire image inside each day's burnt
polygon — was offered and declined), **all 75 alerts nationwide** (the 14 of
the North Evia fire and the 16 tagged Evia were offered), and Figure 04 as the
place after the story's phase-3 commit of the same day.

**What «112» is.** The emergency number, not a count: the source holds 75
alerts for 1–23 August 2021 across Greece — Attica 33 (north 22, west 8, south
3), Evia 16, Ilia 9, Rhodes 4, Fokida 4, Messinia 3, Arcadia 2, Corinthia 1,
Grevena 1, two the source filed as «other» (one is the Messinia fire, one a
nationwide warning); 62 evacuation orders, 7 shelter-in-place, 5 fire-danger,
1 general. The original's default view showed 49 (Evia + Attica).

**The data and its copies.** Raw inputs, never written by code:
`data/raw/112/alerts_112_aug_2021_all.json` (the 75 @112Greece tweets as
harvested), `data/raw/112/alerts-112.generated.json` and
`alerts-112-gazetteer.json` (the sibling implementation's parsed rows and its
213-entry gazetteer — the bootstrap's proposal), and
`data/raw/burned_area/VNP64A1.A2021213.h19v05.002.2023198172838.hdf` (the
burn-date grid). The curated source of truth the site reads is
**`atlas/src/lib/data/alerts_112_2021.json`**: one row per tweet — `tweetId`,
`timestamp` (+03:00, the offset the service posted in), `type`, `region`,
**`orders[]`** (one per instruction sentence, each `from[]` and `to[]` of places
`{tag, nameEn, lat, lon, source, note?}`), the tweet `text` verbatim, `url`,
and `title` (an English gloss) on the rows that name no place. Rules: a
two-sentence message («…evacuate to Pyrgos. If you are in Kavkonia or
Chelidoni evacuate to Lala») is two orders, never the cartesian product the
original drew (24 arrows from one Arcadia message); a place that cannot be
placed keeps `lat/lon: null` and `source: "unplaced"` — never invented — and
the card still names it; a destination the message gives in prose (Limni's
harbour and the ferry, the Athens–Lamia national road, the Sekoula bridge) is
a `to` entry with `source: "prose"`; every hand verdict carries `source:
"hand"` and a `note` with its evidence.

**The source's errors, and how they were found.** `scripts/bootstrap_alerts_112.py`
`--init` writes the file once; `--audit` prints the review sheet and now
includes a **point-in-unit test**: every placed village is ray-cast over the
site's own Π.Ε. layer and must lie in a regional unit of its fire region.
That test, not the eye, found the source's geocoding: 19 places outside their
region (an Ilia «Vilia», «Kryoneri», «Milies», «Mouria», «Aspra Spitia» that
were Attica's, Evia's or Athens' namesakes; a Grevena «Itea» that was
Fokida's; a Corinthia-placed Messinia fire), 34 more with two- or
three-decimal coordinates typed in by hand in the original (the Heraia
villages of Arcadia 20 km east of Heraia), six routes of 186–196 km, three
places sharing one coordinate under different names (Agia Skepi, Vrysaki,
Lofos Kouremenou; Aidipsos and Loutra Aidipsou), the «προς» split that filed
Drosopigi — a village told to leave — as a destination, five evacuations whose
prose destination was dropped, and two region tags used as places (#Ρόδου on
Psinthos, #Ερυθραίας on the Mortero junction). A first re-geocoding through
Nominatim with a region qualifier answered 39 of 193 places and proposed a
shop for Mantoudi; it was set aside. The verdicts came from **OpenStreetMap
place nodes queried by exact Greek name through Overpass inside the region's
units**, each recorded in the place's `note` with the OSM node id, and by
reading each flagged tweet (`--overpass` caches every named place node of a
region in one query; `--match` prints, for each doubted place, the nodes whose
folded name matches one of the hand-written NAME_FORMS — the hashtags inflect,
«#Πύργο», «#Κρυονερίου» — exact first, then loose).

**Curation results.** 249 places over 77 orders: **187 keep the source's
coordinates** (they lie in their region's unit and were not typed in),
**41 were re-placed by hand on OSM place nodes** (Pyrgos, Lala, Kryoneri,
Milies, Platanos, Koskinas, Mageiras, Xirokampos, Ambarion, Louvro, Lasdikas,
Panopoulos, Sekoulas, Aspra Spitia, Pefkes, Kamena and Linaria of Ilia; Itea
of Grevena and its Kentro, dropped by the source; Kokkinovrachos; Theologos;
Loutra Aidipsou; Solomos; Elia and Agios Spyridon of Dorida; Karnasio,
Desyllas, Zevgolatio, Monastiraki, Agioi Theodoroi and Agrilovouno of
Messinia; Aetorrachi, Agios Ioannis of Heraia and Loutra Iraias of Arcadia;
the island centres for the two Rhodes and the Crete warnings), **16 are
honestly unplaced** (Vilia, Tsapareika, Mouria, Diliza and Kapellitsa of
Ilia; the Agios Georgios of Koroni; Lekouna and Vlychada; Melidoni and the
Heraia Palaiochori; Agia Skepi, Vrysaki and Lofos Kouremenou of Dionysos;
Mortero — each note says what was looked for and what the source had), and
**5 are prose destinations** (Diavolitsi, placed; the Athens–Lamia national
road twice, national road 111 and the harbour of Limni, roads and a
waterfront, not points). Two region qualifiers («#Ρόδου» on Psinthos and on
Maritsa–Kalythies, «#Ερυθραίας» on the Mortero junction), a street
(«Οδό #Ανοίξεως» of Kryoneri), a route («μέσω Λεωφόρου #Κύμης») and a
duplicated hashtag pair («#ΙαματικέςΠηγές, #Λουτρά» = Loutra Iraias) were
folded away, with the reasons on the alert; the «other» alert of 4 August is
the Messinia fire (its way out, Diavolitsi, is a village of Messinia). The
longest stated route is now Tropaia→Tripoli, 49 km, which the message says;
the audit reports 0 flags and `test_alerts_112.py` pins the state. The
loop's clock was retuned once more on the real data: 1.8 s per day, 68.3 s.

**The satellite base.** At its zoom the original showed Esri's undated ~15 m
Landsat mosaic (TerraColor NextGen by Earthstar Geographics — the tiles over
North Evia were fetched and are green, pre-fire; Esri's 2025 post-fire aerial
appears only past level 12) under a licence that allows no baking. The open
like-for-like is **EOxCloudless, the Sentinel-2 cloudless mosaic of 2020** by
EOX IT Services GmbH — 2020 rather than 2021 so the ground is pre-fire by
construction — under **CC BY-NC-SA 4.0** (academic and non-commercial use
permitted; a commercial deployment would need EOX's commercial licence or a
swap to NASA Blue Marble / an own Sentinel-2 composite, both examined). It is
fetched ONCE at build time by `scripts/build_alerts_base.py` — a single WMS
GetMap in EPSG:3857 for the frame's exact corners at 1620 × 1620 (the server
answers JPEG whatever format is asked; our AVIF at quality 65 is 268 KB) —
and committed as `atlas/static/geo/alerts_base.avif`; nothing is fetched at
runtime. Required attribution, printed under the caption: «EOxCloudless
https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus
Sentinel data 2020)». **Palette:** the imagery is the user's explicit
exception to the site's no-brown rule; everything of our own on it is black,
white, grey and the fire colour. Dated Sentinel-2 scenes were also examined
(3 Aug 2021 09:29 UTC, the morning of ignition, and 16 Aug 2021, the first
clear pass after containment, both cloud-free on the four North Evia tiles
via the public AWS bucket) — the right pair for a North Evia figure, not for
a national one.

**The frame.** ONE fixed national window, `ALERTS_BOX = [[19.5, 34.7],
[28.6, 41.8]]` — Corfu to Rhodes, Crete to Thrace. A flying camera was
rejected on the data: 45 of 74 consecutive alerts change region. The box is
1013 × 1008 km in Mercator, so `fitExtent` on the square leaves a 0.5 %
letterbox; the contract is therefore the **inverted corners of the fitted
square** (`nw ≈ [19.5, 41.817]`, `se ≈ [28.6, 34.681]`, the same at any size),
written by `atlas/scripts/build-alerts-frame.mjs` to
`atlas/static/geo/alerts_frame.json` FROM the module the client projects with
(`lib/transforms/alertsFrame.ts`, imported by node directly) and pinned by
`alertsFrame.test.ts` the way `frame.test.ts` pins the relief. 625 m/px on the
plate; the 540 px figure square is 1.87 km/px, which is why the Attica cluster
(22 alerts in 57 × 37 km) reads as a cluster and the card carries the names.

**The burnt ground.** The original drew a real product and it is kept: NASA
VIIRS/NPP VNP64A1 v002 burned area (500 m, tile h19v05, the August 2021
product), read from the raw HDF4 tile by `scripts/build_alerts_burn.py` into
`alerts_burn_2021.geojson` (`data/processed/` + the byte-identical
`atlas/static/geo/` copy, 92 KB): per day 1–23 August the pixels whose burn
date is that day, dissolved, simplified 150 m, reprojected from the sinusoidal
grid, clipped to the frame and to Greek land (the tile spills into Albania),
rings clockwise for d3-geo — **increments, not cumulatives**, so the client
draws days 1..k and no geometry repeats. Pixels are 463.31 m (0.2147 km², the
original's `× 0.25` over-reported by 16 %). Coverage caveat on the credit
line: the tile ends at 40.0 °N / ~25.6 °E — every mainland fire region of the
alerts is inside, **Rhodes and Grevena are not** (tile h20v05 would add
Rhodes). Drawn as a flat fill in `--c-fire` composited at 55 % from an
offscreen buffer so touching days show no seams. The month, as the product
saw it (mainland, inside the frame):

| day | px | km² | cum km² |
|---|---|---|---|
| 01–03 Aug | 17 | 3.6 | 3.6 |
| 04 Aug | 562 | 120.6 | 124.3 |
| 05 Aug | 393 | 84.4 | 208.6 |
| 06 Aug | 1,818 | 390.2 | 598.9 |
| 07 Aug | 501 | 107.5 | 706.4 |
| 08 Aug | 811 | 174.1 | 880.5 |
| 09 Aug | 307 | 65.9 | 946.4 |
| 10 Aug | 143 | 30.7 | 977.1 |
| 11 Aug | 154 | 33.1 | 1,010.2 |
| 12–15 Aug | 22 | 4.6 | 1,014.9 |
| 16 Aug | 104 | 22.3 | 1,037.2 |
| 17 Aug | 67 | 14.4 | 1,051.6 |
| 18 Aug | 131 | 28.1 | 1,079.7 |
| 19 Aug | 167 | 35.8 | 1,115.6 |
| 20–23 Aug | 76 | 16.3 | 1,131.9 |

**The clock** (`lib/transforms/alertsClock.ts`, pinned on the real alerts).
Simulated time runs at 1.8 s per day; through an idle stretch (no alert within
the next 3 simulated hours and the last dwell over) at 1 s per day; a firing
never comes sooner than 0.5 s after the previous one — the clock HOLDS on that
minute, so the peak days (16 alerts on 5 Aug, 14 on 6 Aug, 38 consecutive
pairs under an hour apart) are alert-paced and each alert can be read; every
alert is active 3 s, fades 1 s, then stays as a small past dot; the window
ends only once the last alert has dwelt and faded, holds 3 s, fades 0.6 s and
restarts. Loop **68.3 s** (the constants first proposed — 5 s per day — were
simulated on the 75 timestamps and gave 78–105 s with 47 firings under 0.5 s
apart; the retune is data-forced). Reduced motion = the final state drawn
once. The loop runs only while the figure is mounted (StoryFigure mounts a
live figure while its number is in force), the square is on screen and the
tab visible.

**The drawing.** Base plate · burnt ground · the past origins as small dots ·
the fading alerts · the active alerts last: a thin white hairline from each
origin to each destination its order names (what the message says, not a
route), white destination dots, black origin dots (grey for a shelter-in-place
or warning), village names in white beside the active dots (greedy
de-collision, dropped where nothing fits — the card carries them) · a day
strip along the bottom in a 35 % wash (23 day ticks, the 75 alert ticks, a
playhead) · the site's black card top-left with the clock («5 Aug 2021 ·
16:48») and the order («Agia Anna, Palaiovrysi, Kerameia, Agali → Mantoudi»;
«Istiaia, Aidipsos, Loutra Aidipsou · stay indoors»; before the first alert
the computed «75 alerts · 1–23 August 2021») · a key bottom-right. No
outlines on any dot.

**The figure slot.** `lib/story/figures.ts` is the registry of LIVE figures —
the pattern for the other twelve — keyed by the author's own figure number,
each declaring its component and its credit line; `StoryFigure.svelte` mounts
the registered component inside the existing `{#key figure.n}` and prints the
credit under the author's caption. `figures.test.ts` pins every key to an
existing marker and marker 4's name («112 emergency alerts»), so a renumbering
by the author fails loudly. The author's `.md` files, `content.ts`,
`bindings.ts` and the story page are untouched.

**Pins.** vitest: `alertsFrame`, `alertsClock`, `alertsText`, `alertsLayout`,
`figures`; pytest: `test_alerts_112.py` (row count = raw tweets, verbatim
text, vocabularies, every placed village in its region's unit, no two places
of an alert on one point, no stated route over 60 km, the named corrections),
`test_alerts_burn_layer.py`, `test_alerts_assets.py`.

**A bug of the story page found on the way, and fixed.** mdsvex emits a
paragraph that BEGINS with an inline tag — the author's `<span
class="figmark">[FIGURE xx: …]</span> The 2021 fire season…` (nine of the
chronology's paragraphs) — as a raw HTML block with no `<p>` around it. The
page pairs its rendered `p`/`h3` elements with the parsed blocks in order, so
those nine were missing from the pairing (the console warned «71 rendered
blocks vs 80 parsed»), every block id after each of them was shifted, and the
reading line could never reach the Figure 04 paragraph — the figure in force
went from 01 straight past 04. `atlas/scripts/remark-tag-paragraphs.ts`, a
remark plugin wired into mdsvex in `vite.config.ts`, restores what markdown
proper does: a root-level raw-HTML node that is neither a lone tag nor real
block-level HTML becomes a paragraph holding that HTML —
`<p><span …>…</span> The 2021 …</p>`. `mdsvexParagraphs.test.ts` compiles the
author's files and pins one `<p>`/`<h3>` per parsed block (80 = 80), and
guards that no tag-led paragraph carries markdown that raw HTML would drop.
Nothing in the author's files changed. Verified in the browser: 80 rendered
blocks, no warning, Figure 04 mounting on its paragraph with the 112 event lit
on the timeline. A second one, seen only once a real figure filled the square: the sticky
title band (`.heads`, paper, z-index 4) spans all five grid columns while
the figure rectangle's top aligns with the titles' top, so the band painted
over the rectangle's first 37 px and the clock card lost its first line;
the band's paper is now a `::after` covering the four tracks the text
scrolls under (`inset: 0 calc(100% * 594 / 1784) 0 -20px`), the column's
own share of the artboard.

## 2026-09-02 — the section titles answer to what is below them, and a footnote carries its link

Three rulings of the author on /story, applied:

1. **The pinned section title follows what the reader SEES, not the reading
   line.** It switches the moment the previous section's last paragraph
   clears the title band — finishing the chronology now shows METHODOLOGY,
   instead of the old title standing over a methodology sub-chapter. The
   incoming title rises in with a 0.35 s entrance; the reading line stays
   the authority for everything else (figure, notes, timeline). The
   visibility observer gained a top inset (150 px) so a paragraph does not
   count as on-screen while it is still hidden under the band.
2. **A footnote that ends in a URL becomes a link**: the URL leaves the
   display text and the rest of the note carries it (underlined, opens in a
   new tab; `utm_source=chatgpt.com` stripped from the target — the DOI and
   registry links are untouched). A note with no trailing URL stays plain
   text. Parsed in `content.ts` (`NoteEntry {text, href?}`), pinned in
   `content.test.ts`: no note's display text ends in a raw URL, note 8 reads
   «For more information, see here» as a clean link.
3. **The notes must read clearly**: the long unbreakable strings (DOIs,
   URLs) were what ran under the neighbouring column — linkifying removes
   the main culprits from the text, and `overflow-wrap: anywhere` on the
   items catches whatever remains.

## 2026-09-02 — the footnotes, second pass: every citation carries its own link

The author's bug report on the first pass, verified and fixed:

1. **A note may cite SEVERAL sources.** Notes 13 and 14 each carry two
   Popaganda citations with a URL after each; the trailing-URL model
   linkified only the last and PRINTED the first URL as text. `content.ts`
   now parses a note into PARTS: every URL leaves the display and the
   citation chunk before it becomes the link to it; separators between
   citations stay as plain glue; text after the last URL stays plain.
   Pinned: no URL is ever printed as text in any part of any note, and
   notes 13/14 carry exactly two links each.
2. **The numbers misprinted and the columns overlapped** — two rendering
   bugs, found: an `<ol value>` marker inside CSS columns misrenders for
   two-digit numbers, and `break-inside: avoid` on an item TALLER than the
   column (the two-source notes) cannot break, so it overflowed ONTO the
   right column's text. The numbers now print inline as hanging text, and a
   long note may break across the two columns — the print convention.
3. **The «Footnote» label is gone** (the author: the space is worth more).

## 2026-09-02 — the sticky handoff, the breathing band, and whole notes only

The author's chosen package for the two UX complaints (the invisible section
transition; the footnotes cut mid-word at the window's edge), built:

1. **Sticky handoff titles.** The narrative's section titles left the fixed
   band and live IN the text: each section opens with its own heading, which
   the reader sees approaching from below, and which docks (`position:
   sticky`) at the band's height — the next section's title physically pushes
   the previous one out as the boundary scrolls past. Pure CSS; the browser
   animates it with the scroll; reversible by construction. The band keeps
   only TIMELINE; the topmost-visible title logic and its entrance animation
   were deleted (CSS does it better), along with the band's four-track paper
   `::after` — each docked title carries its own paper.
2. **The breathing band.** A 48 px paper band fixed at the window's bottom:
   every column — the narrative included — stops short of the edge instead of
   running into it; the page pads by the same amount so the end stays
   reachable. The rails' heights subtract it.
3. **Whole notes only.** The footnote block never cuts a word: every candidate
   note is measured at column width in a hidden copy, and notes are admitted
   NEAREST-TO-THE-READING-LINE first while the two columns' room lasts
   (displayed back in number order). A note that does not fit is dropped
   whole and appears when scrolling gives it room. Verified on the heaviest
   screen: notes 13 and 15 read complete, 14 waits — nothing clipped.

## 2026-09-02 — the timeline breathes with the text, and the story sheds the dataset sections

Five rulings of the author (screenshot round), applied:

1. **An event opens only at its own period.** Every timeline event stands as
   DATE + TITLE; the explanatory text appears only while the main text is at
   the event's period (the lit events of the active paragraph). The layout
   REFLOWS around the opened bodies — `layoutLane` takes a per-event
   predicate, blocks glide to their new tops — so the lanes stay tidy and the
   open event reads in full.
2. **The years print level with their events**: each label centres on its
   span to the next stop (`YearStop.midY`) instead of marking the year's
   first of January — an August cluster now sits beside its own year, not
   the next one's.
3. **The timeline withdraws after the chronology.** Reading the methodology
   onward, the rail and its TIMELINE title fade out (returning when the
   reader scrolls back). The introduction and the chronology are its home.
4. **The three dataset sections left /story** — FINANCED BY PRIVATE
   COMPANIES, ANTINERO PROGRAMME, WORKS EXECUTED BY FOREST WORKERS'
   COOPERATIVES belong to the dataset card pages only (their .md files stay
   in the story folder as the author's source; `mdsvexParagraphs.test`
   counts only the rendered sections). The story is now: introduction ·
   chronology · methodology · key findings · bibliography.
5. **TIMELINE and INTRODUCTION start aligned**: the `.heads` row is gone —
   TIMELINE is a grid sibling sticky at the same `--story-top` as the
   section titles, the first section carries no top padding, and a fixed
   paper strip (`.tcover`, the breathing band's twin) covers the gap under
   the header so pushed-out titles vanish cleanly.

Verified live: at the Law 4824/2021 paragraph the emergency act and the
ratification light up, the act's body opens, and the rail pans to August
2021; in the methodology the timeline is gone.

## 2026-09-02 — notes never split, the collapsed timeline speaks at native size, the cards synced

The author's night round, applied:

1. **The footnote misprints (notes 1/2/3) had one root cause**: the two
   columns were CSS `columns`, which BREAKS a note mid-sentence across the
   gap — note 2 split at «Rather than / describing…», note 3 began under
   note 2's continuation. The columns are now PACKED BY NOTE: whole notes
   fill the left stack to its height, then the right (admission still
   nearest-to-the-reading-line, packing in number order, an overflow drops
   the farthest note and repacks). A note can no longer split, ever.
2. **The collapsed timeline's texts were illegible** (~7 px: they scaled with
   the whole 1162 px axis at ~0.6). The disclaimer and the lane titles now
   render at NATIVE size outside the scaled drawing — the disclaimer
   bottom-left of the converged line in the axis's own empty margin (11 px,
   right-aligned), the three lane titles right of the line under the axis
   (11.5 px caps, their lane colours), the scaled dotted line itself running
   between them as the divider. The converged line moved from x 290 to 360
   to give the disclaimer a readable measure; the collapsed fit reserves
   130 px of native room. When the timeline spreads, the native block fades
   and the in-scale legend fades in above the lanes (the ride-out motion
   simplified to a crossfade).
3. **The cards synced to the story texts** (the author's word): the
   differences turned out to be typographic apostrophes only (the document's
   «’» against typed «'») — `datasets/antinero.md` and `datasets/dase.md`
   adopted the story versions; `anadohoi.md` was already identical.

## 2026-09-02 — the collapsed timeline balanced

The author's balance round on the collapsed state, applied: the two long lane
titles print on TWO LINES each («GLOBAL EVENTS & EU / LEGISLATION CHANGES»,
«EVENTS & LEGISLATION / CHANGES IN GREECE»; FIRES IN GREECE stays one); the
disclaimer and the titles moved to the UPPER part of the timeline — the
sparse early years — instead of its bottom; the disclaimer is set at the
footnotes' own size (fs-12 light, 1.3) and a touch wider; and with nothing
reserved below any more, the axis takes the whole rail (the collapsed scale
rose from ~0.63 to ~0.74) with the converged line near the column's centre
(COLLAPSED_X 360 → 345). The years column runs between the disclaimer and
the line; the scaled dotted line stays the divider to the titles' side.

## 2026-09-02 — the timeline spreads with the chronology's presence

The author's rule refined once more: the timeline is SPREAD for as long as
CHRONOLOGY OF FIRES AND EVENTS is on the page — the lanes open the moment its
first paragraph enters the viewport (while the reading line may still be in
the introduction) and stay open until its last paragraph has left. Implemented
on the visibility window (`visList`), replacing the reading-line trigger
(`EXPAND_BLOCK`, removed). Verified live: with the chronology's first
paragraph at the viewport's lower edge and the reading line on the
introduction's second paragraph, the timeline is already spread.

## 2026-09-02 — the narrative sets like the printed page

The author's reference (their own dissertation page): the story's narrative
paragraphs now JUSTIFY to both edges and indent their first line 2 em —
alignment only, the faces untouched. Story page only; the rest of the site
keeps its ragged-right setting. Second ruling minutes later: NO hyphenation
— instead the base word gap is tightened a touch (`word-spacing: -0.02em`,
so justification stretches from lower) and `text-wrap: pretty` lets the
browser choose line breaks that keep the gaps even.

## 2026-09-02 — a highlighted event stretches to its whole text

The author: many events' texts were not fully visible even highlighted — the
title clamped at four lines, the body at two. Now an OPEN event (the reader
at its period) STRETCHES: full title, full body, no clamps — the reflow
machinery already made the room, and `blockHeight` gained an `open` mode
(unclamped, plus one line of slack so the estimate can never run short and
let the next block overlap real text). Closed events keep the tidy
date-plus-clamped-title form. The `< 2000` drawing-height pin now measures
the runtime shape (everything closed but the reader's own events).

## 2026-09-02 — the rail frames the paragraph's whole event range

The author's screenshot: reading «…AntiNero programme began to operate at
national scale in 2022», the timeline sat on 2018–2019 — the AntiNero
paragraph binds three events years apart (Green Deal 12.2019, Forest
Strategy 07.2021, the launch 07.2022) and the pan followed the EARLIEST.
`focusDate` became `focusDates`: the rail now centres on the MIDPOINT of the
active paragraph's event range (all three in view together, bodies open);
a range taller than the view anchors just above its earliest event. The
same fix serves every multi-event paragraph (Mati + the two 112 launches;
Evros + committee + Rhodes; the four 2021 fires).

## 2026-09-02 — the lanes balance around their dates

The author's screenshot: the middle (Greek) lane's blocks did not correspond
with the years — the dodge pushed crowded blocks only DOWNWARD, so the 2021
cluster cascaded beside the 2022–2023 labels, amplified once open events
stretch whole. The suspect was the pan change of the previous round; the
cause was the one-way push. `layoutLane` is now a BALANCED dodge
(pool-adjacent-violators): order kept, no overlaps, and every contiguous
crowd centres on the least-squares mean of its members' dates — spreading up
into an empty year as much as down, clamped below the spread legend's line.
A block may now sit above its dot as well as below; the leader line joins it
back either way. Pinned: per-lane mean displacement under 25 px in the
closed layout, nothing above y 62.

## 2026-09-02 — the axis stretches where the events crowd

The author's second screenshot: the balance was not enough — Law 5106
(01.05.2024) still printed past the 2026 label. Measured, the cause is
CAPACITY, not the dodge: from mid-2021 the Greek lane's 13 blocks need
~750 px where the fixed spans (2022–2026 at 81.4/110/81.4/81.4) give ~614,
so the chain has no choice but to smear below its dates however it is
balanced. The fix is at the SCALE: `yearStops` now grows each year's span
to hold its own events' closed blocks (`neededPx` — the tallest lane's
stack inside the year, +10 headroom; the artboard's spans stay as the
floor), and 2026 became a real year with an unlabelled 2027 endpoint
(its events used to clamp onto the axis END). The axis runs ~470 px
taller; the collapsed fit simply rescales (chrome is native-size since
the same day's earlier round). Verified at both screenshot paragraphs:
every closed Greek block now sits at its year or its boundary, the lit
Law 5106 beside 2024, and at the 4824 paragraph the two stretched-open
blocks straddle the 2021 label with only their immediate neighbours
displaced (leader lines say so). Pinned: a new vitest walks every year ×
lane and asserts span ≥ the closed stack — a future event added to a
crowded year grows the axis instead of reviving the smear.

## 2026-09-02 — the story page is optically centred

The author noticed /story's side margins differed and chose symmetry over
artboard fidelity: the artboard drew x 60→1844 on the 1920 canvas (60 left,
76 right), and the build had reproduced that. The author edited the side
paddings themselves to an even `clamp(20px, 3.5vw, 68px)` each — the same
136 px total, split evenly. Measured after: 67,2 px both sides at 1920, the
figure square's right edge on the same margin as TIMELINE's left. The five
column tracks are untouched. Second and third rounds the same day (two
author screenshots): equal page margins were not enough — the figure
COLUMN's content (capped at `--fig-w` 540 px) was narrower than its track,
so the slack fell on the page's right edge; a right-align pass then left
the caption and credit behind (their own `margin: 0` cancelled the
`margin-left: auto`, the classic cascade trap) and the author ruled the
opposite anyway: caption and footnotes LEFT-ALIGN with the image, spare
pixels go to the NARRATIVE. Final mechanism: no alignment rules at all —
the grid gives the figure track exactly its content's 540 px and the
narrative the whole spare (tracks 500 · 30 · 674 · 40 · 540, the author's
own 500/30/40/540 kept). The fr lesson is written at the rule: the values
read as pixels at 1920 ONLY while they sum to 1784, the content width
inside the margins — the author's interim edit summed 1680 and every
track silently inflated ~6%. Measured after: image, caption, credit and
footnote stacks all at left 1312,3 / right 1852,3, the right edge on the
page margin; mobile unaffected.

## 2026-09-02 — the footnote fit rebuilt so every note appears where it is cited

The author: «some do not appear correctly like 8 and some do not appear at
all like 2». A browser walk of all 66 paragraphs found the causes in the
whole-note packing: on overflow it dropped the FARTHEST note and repacked,
which cascaded — one oversized note emptied the whole block (paragraphs
citing 3-4 and 5-7 showed NOTHING; note 8 once printed alone, the survivor
of an emptied block — its own text and URL are complete and verbatim); a
note taller than one 323 px stack (4 at 289, 5 at 390, 6 at 780 measured)
could never print at all; and the two stacks interleaved numbers
(13,15,17 | 14,16). Rebuilt in `StoryFigure.svelte`: admission is
nearest-first by TRUE FIT (a note that cannot fit is skipped, never a
reason to drop neighbours), packing preserves NUMBER ORDER (the admitted
notes sorted by n are cut once — left run, right run), and the READING
paragraph's own notes are a UNIT — when they cannot all stack whole they
go TOGETHER to a spread flow across both columns that may scroll inside
(the only exceptions to the no-split/no-scroll rules, conceded because
notes 5-7 hang on ONE paragraph and total 1.303 px against the block's
646 — no arrangement of whole notes can show them; the author's demand
that they appear outranks the earlier no-scroll ruling exactly there).
Verified: all 18 notes render at their own citing paragraph (15 via
stacks, 5-7 via the spread), zero-shown states gone. Also found, for the
author: note 5 carries two literal words «link» where the Word document's
hyperlinks lost their URLs before distribution — the storyboard docx is
not on this machine, so the two URLs must come from the author; and note
8's polsxedia.ypen.gov.gr URL answers 403 to a plain client but that host
blocks non-browser clients (like ypen.gov.gr) — the link works in a
browser and matches the document exactly.

## 2026-09-02 — the eighteen footnotes verified against the author's own text

The author attached the canonical text of all 18 footnotes. A mechanical
whitespace-folded diff against the stored .md lines found ONE divergence:
note 6's «3)in the case» is the author's «3) in the case» — corrected in
chronology.md. Everything else, including every URL, is byte-faithful.
Note 5's two literal words «link» (no URL behind them) stand in the
author's canonical text exactly the same way, so they stay as written —
the author has been told, in case the underlying document's hyperlinks
were meant to survive there.

## 2026-09-02 — a footnote's «see:» tail alone carries its link

The author, on note 6: the whole text must not be underlined — the link
belongs only on «see: Loukas Triantis, … 55–70». The chunk-before-the-URL
rule made a long explanatory note into one giant link wherever its single
citation came last. `content.ts` `noteEntry` now cuts a chunk at its last
«see:»: the text before stays plain, the tail from «see:» carries the
href. Note 6 is the only current case (notes with a bare «See …» carry no
URL); pinned in `content.test.ts` (two parts, plain head, linked tail on
doi.org/10.15488/18216) and verified in the rendered page.

## 2026-09-02 — the story page's evening round: one-column heavy notes, the author's disclaimer, a 6 px trim

Three author rulings in one message. (1) «Would the footnotes fit better
in one column when text-heavy?» — capacity is identical (same area either
way), but one column removes the mid-sentence jump across the gap, so the
SPREAD state (the reading paragraph's notes when they cannot stack) now
flows as ONE full-width column, its height MEASURED in a second hidden
copy at the block's width instead of the halved-stack estimate; the
two-stack packing for light notes is untouched, and the per-note walk
still passes 18/18. (2) The author edited the delivered SVG to show the
collapsed timeline they want: the disclaimer at a real measure — the
rail's left half, right-aligned toward the years — with the converged
line, years and dots shifted RIGHT to sit beside the lane titles.
Implemented as a collapsed-only translate of the scaled drawing
(`cx` = 21,4% of the rail at the design width, the author's own geometry;
spreading returns it to 0 through the same transform transition), the
native chrome deriving its split and the disclaimer width from it.
(3) The narrative track is 6 px narrower, the pixels split into its two
gutters: tracks 500 · 33 · 668 · 43 · 540, sum still 1784.

## 2026-09-02 — the axis itself warps, so the lanes agree on every date

The author's third alignment screenshot: the Greek lane and the fire lane
disagreed on the SAME dates — the 112 period (03-08 → 16-08-2021) printed
~150 px above the Peloponnese fires (03-08 → 12-08-2021). Cause: each lane
dodged its crowds INDEPENDENTLY, so the balanced Greek August pile lifted
its early blocks off their dates while the sparse fire lane stayed put. No
per-lane dodge can fix that; the SCALE now does: `buildScale` walks every
lane's events in ONE date order, each lane's chain reserving the room its
closed blocks need — the axis stretches wherever any lane crowds, a closed
block sits AT its warped date (zero displacement, no leader lines at
rest), same-date events across lanes share one y BY CONSTRUCTION, the
year labels ride the same warp, and a same-day pile (the three 03-08-2021
fires) turns its instant into a stepped band. The artboard's SPANS stay
as the rate floor — time never takes less room than the artboard gave it.
`yOfDate` interpolates over the warp's knots; `layoutLane` shrank to a
downward cursor absorbing only the OPEN stretch delta. Axis 1.835 px
(2021 grew to 555). Pinned: per-lane reservations, closed blocks at zero
displacement, cross-lane date monotonicity, and the 112 ↔ Peloponnese
equality itself; measured in the browser: both blocks at y 429,5 to the
decimal. Same message: the story grid's two gutters became EQUAL 38 px
(500 · 38 · 668 · 38 · 540, sum 1784).

## 2026-09-02 — the reading position holds across gaps; no more rewinds

The author: past «It also opened public forest restoration …» the timeline
elapsed BACK TO THE START, then snapped forward at the October-2021
paragraph — and the same elsewhere. Reproduced at three scroll positions
in that region alone: the ~1 px reading band can settle in a GAP (a
paragraph margin, a section seam), `steps.ts` then emitted null, the page
cleared `focusDates`, progress computed 0 and the rail panned to 2007
(the figure also flipped back to 01). Fixed at the source: an empty band
now HOLDS the current passage — a gap is not a change of reading
position — stepping back one beat only when the current passage's own
exit entry shows the reader went above it (the observer entry's rects,
nothing forces layout), and null returns only above the first passage.
Verified by scroll-walks both ways: the pan is monotonic through the
whole chronology going down, and going up the timeline still collapses
at the introduction.

## 2026-09-02 — key findings into the figure column, the page centres after the timeline, the bibliography steps down

Four author rulings. (1) The bibliography must be smaller than the main
text (which is 16 px — the `.prose` base; the layout comment claiming
18 px was corrected): it now sets at 13 px, apparatus not narrative.
(2) With no timeline past the methodology, the text and figure columns
CENTRE: `.cols.centred` (driven by the existing `timelineOn`) shrinks the
first track to 231 and balances with 15,08% right padding — 269 px of
whitespace each side of the 668+38+540 pair, the grid transition carrying
the slide; measured symmetric to the decimal (336,4 / 336,4 at 1901 vw).
(3) WHERE BOTH FLOWS LAND (the log–log scatter) and the hero's two
explanatory paragraphs («The Anti-nero programme pays … side by side» and
the basis note) are REMOVED from KEY FINDINGS; the four KPI cards stay.
(4) The remaining five items render ONE AT A TIME in the figure column at
its 540 px width, advancing 1:1 with the five paragraphs of KEY FINDINGS
AND OPEN QUESTIONS (`kfAt` in the story page; `KeyFindings.svelte` is now
an indexed rail card — cards+STATE-FUNDED · SIGNED · SIZES · REGION BY
REGION · MONEY PER YEAR — compact titles, the computed insights as small
notes); the full-width coda is gone. Verified: each paragraph brings its
item at 540 px, in order. Follow-up the same hour: the BIBLIOGRAPHY
carries NO figure beside it (author) — the rail renders nothing there,
instead of the carried-forward marker.

## 2026-09-02 — the author's figure images arrive: the 18-image grid, notes 1-2 under the timeline, the spread waits for the title

The author delivered figure images into `atlas/static/img/story/` —
`Figure02a/b`, `Figure03`, `Figure11`, `Figure13` (2481² PNGs) and a
`figure01/` folder of 18 numbered 4724² images (~316 MB, plus a 1,38 GB
.psd). Three rulings in one message: (1) FIGURE 01 is a GRID of the 18 —
six rows of three, the filenames' numbers being the reading order (1,2,3
the first row left to right) — filling the right column's whole height;
(2) the introduction's footnotes 1 and 2 move to the LEFT column, the
lower part of the collapsed timeline, freeing that height; (3) the
timeline SPREADS only when the CHRONOLOGY OF FIRES AND EVENTS title
DOCKS level with the TIMELINE title — not when its first paragraph peeks
in at the viewport's bottom (a docking IntersectionObserver band at
`--story-top` replaced the visibility trigger). Mechanics: the originals
never ship — `scripts/build_story_images.py` (Pillow) emits small .webp
derivatives (grid cells at 320 px ≈ 7-32 KB, singles at 1100 px ≈
67-200 KB, ~1 MB in all), the originals and the .psd are GITIGNORED in
place; `lib/story/figureImages.ts` is the manifest (grid · pair · single;
figure 02 renders its a+b side by side, singles object-fit contain in the
square), pinned by `figureImages.test.ts` (every key has a marker, every
src a built file, the grid is 18 in order). The left block carries the
INTRODUCTION's own notes only — a chronology note peeking in waits for
the spread. Gotcha kept in the CSS: a percentage height chained through
grid items never resolved (the grid grew to 1.084 px over an 875 px box
and drew over the caption) — the grid overlays its box absolutely.
Delivered so far: 01 grid, 02 pair, 03, 11, 13 + the live 04; still with
the author: 05-10 and 12.

## 2026-09-02 — ten more px to the gutters, and the grid cells become true squares

Two author rulings. (1) The narrative track went 668 → 658, the ten px
split equally into its gutters (500 · 43 · 658 · 43 · 540, sum 1784; the
centred variant follows). (2) «The images I gave you were square — the
ones that appear are not»: the 6×3 grid's full-width cells were 177×142
(three squares across 540 px want 177 px cells, but six such rows are
1.085 px against the column's ~875) and object-fit cropped ~20% off each
image. The cells are now TRUE SQUARES sized by the height — one sixth of
the box via container units (`container-type: size` on the box,
`calc((100cqh − 20px)/6)` columns) — so nothing is cropped; the grid
keeps the caption's left edge and runs ~436 of the 540 px. The
alternatives (full width with the crop, or full-width whole squares at
1.085 px with an inner scroll) were set aside; the author can call either
back. Measured: cells 142,5 × 142,5, gutters 43,0 both, text 658.

## 2026-09-02 — the introduction reveals itself in stages («let's see how it looks»)

The author's staged reveal of the opening: on PAGE OPEN the grid shows no
images and no footnotes; on the FIRST SCROLL (a 1 px sentinel at the
document's top — the page still keeps no scroll listener) the first pack,
images 1-9, appears as 3×3 at the column's FULL width — three rows fit
the height, so the squares grow to 177 px uncropped; when the «Greece is
part of the wider Mediterranean Basin …» paragraph DOCKS at the title
(the chronology's own docking-band technique, sticky past the line), the
two footnotes appear under the timeline and the second pack — images 10-18 —
REPLACES the first (the author's follow-up: the full 6×3 never shows),
still 3×3 at full width, the block vertically CENTRED on the column's
height. `StoryFigure` takes a `stage` prop
(0 · 1 · 2, default 2 so every other figure is untouched); images fade
in 0,45 s, reduced motion turns it off; fully reversible on scrolling
back. Verified: 0 imgs/0 notes · 01-09 at 177² centred (167 px above =
below) · 10-18 at 177² centred + notes 1-2.

## 2026-09-02 — the left gap must READ as the right one

The author: the timeline→text gap and the text→figure gap are not the
same. The grid TRACKS were equal (43 px both, measured) — what differed
was the INK: the collapsed lane titles stopped 4 px inside their rail and
the introduction's footnotes were capped at 460 px, ending ~40 px short,
so the left gap read wider. Both now reach the rail's edge (`.nkeys
right: 0`, `.tlnotes max-width: none`); measured after: ink gaps 43,0 /
43,0 to the decimal.

## 2026-09-02 — another 10 px off the text, and the grid caption in the author's words

The narrative track went 658 → 648, the ten px into its gutters (500 ·
48 · 648 · 48 · 540, the centred variant following; measured 648,6 with
48,0 both sides). The grid figure's caption is the author's wording —
«Figures 1 to 9: Images from media coverage of fires in Greece. All
images are credited to their corresponding authors here.» — with the
RANGE following the pack on show (10 to 18 at stage 2, the same
sentence; empty at stage 0). «here» reads as a link-to-be; the target is
still with the author.

## 2026-09-02 — SOURCES joins the story, and the captions link to it

The author's captions final: pack one «Figures 1 to 9: Images from media
coverage of fires in Greece.», pack two «Figures 10 to 18: Images from
fires worldwide.», both closing with «All images are credited to their
corresponding authors here.» — and «here» LINKS the new SOURCES section,
which stands after BIBLIOGRAPHY (its own chapter and anchor, figure-free
like the bibliography). `src/content/story/sources.md` is created EMPTY:
the author is writing the credits text and will deliver it in that file.

## 2026-09-03 — the narrative settles at 556 px

The author set the story's text column to 556 px — the half-frame measure
of the dataset pages' unfolded charts — the freed width split equally
into the two gutters as before (500 · 94 · 556 · 94 · 540, sum 1784; the
centred variant follows). Measured: 556,5 with 94,1 both sides; ~69
characters of 16 px type.

## 2026-09-03 — every footnote presents where notes 1 and 2 are shown

The author's switch: ALL footnotes now present on the timeline column's
lower part — where the introduction's notes 1-2 already lived — and the
figure column keeps FIGURES only. `StoryNotes.svelte` carries the figure
column's fitting machinery there (whole notes, hidden-copy measurement,
nearest-first true-fit admission, number-order two-stack packing, the
active paragraph's unfitting notes to one full-width flow), given a
HEIGHT BUDGET of 44% of the rail by the page instead of a grid row; the
timeline (collapsed or spread) flexes above it, its scale and pan
adapting. Collapsed, the intro's notes still wait for stage 2; spread,
the visible paragraphs' notes show. StoryFigure's own block lies dormant
(`notes={[]}`), its machinery kept. Verified by the per-note walk: all
18 render on the left rail at their citing paragraphs — the three
transitional cases (1 before the Greece dock, 3-4 before the chronology
title docks) appear the moment the author's own stage rules fire — and
the right column carries zero notes everywhere.

## 2026-09-03 — five rulings: the grid drops 20 px with its caption, the pair stacks at 75%, the centred pair measures 1152, the collapsed timeline loses its titles, LEGISLATIVE

The author's round: (1) the 3×3 grid sits 20 px below the column's
centre with its caption RIGHT UNDER the cells (measured: block mid =
box mid + 20, caption 10 px below); (2) figure 02's two images stack ONE
BELOW THE OTHER at 75% of the 540 slot (405×405 each); (3) the centred
two-column state (methodology onward) totals the explore-more pages'
1152 px — 556 + 56 + 540, whitespace 316 a side (measured 1153 with
383,5 = 383,5 margins); (4) the COLLAPSED timeline prints no category
titles — the lanes name themselves only when they spread; (5) the two
lane titles say LEGISLATIVE changes, not LEGISLATION.

## 2026-09-03 — one placement for every figure, and figure 02 becomes a carousel

The author's follow-up: the grid drops 40 px further (60 below the
column's centre in all), the caption 7 px under the image — and that
PLACEMENT APPLIES TO EVERY FIGURE. `StoryFigure` was rebuilt around one
`.stack` (absolute, flex-centred, translateY 60 px): grid packs, singles,
the carousel, the live drawing and the placeholder square all ride it,
caption and credit below. Figure 02's two images are a CAROUSEL — one
image in the standard 540 slot, a small round arrow on its right edge
interchanging them (state resets on figure change); the 75%-stacked
arrangement of the same day is superseded. Measured: block mid = column
mid + 60 and caption gap 7,0 px on grid, carousel and single alike; the
arrow swaps 02a → 02b. The dormant footnote machinery rode along
unchanged.

## 2026-09-03 — the notes' left column fills first, the carousel is seen, the figures renumber on display

Three author reports in one message. (1) «Something weird» in the notes:
the number-order split searched its cut from EMPTY-LEFT upward, so a set
that fit one column parked in the RIGHT stack with the left empty (their
screenshot: note 4 full-width, note 3 alone at the right); the search
now takes the LARGEST left run that fits (StoryNotes + the dormant
StoryFigure copy). Verified at the same position: left [3,4], right
empty, no spread. (2) The carousel WAS advancing but its white arrow was
invisible on the author's white map images: the arrow is now a dark chip
and two indicator dots say which of the pack is shown. (3) DISPLAY
NUMBERING runs on from the grid: its 18 images are figures 1-18, so
every later figure prints marker+17 — «Figure 19 _ Fires in 2007» …
marker 13 as Figure 30, the placeholder squares included. The author's
own [FIGURE xx] markers and every file keep their numbering; the map is
one presentational function (`dispN`).

## 2026-09-02 — the Atlas goes public: Google Cloud Run, deployed by GitHub Actions on every push to main (user)

The user asked for the site online for the public, free as far as possible,
simple, auto-updated from GitHub `main`, and not sluggish — and whether a
plain Vercel app would do. Hosts weighed on their PRIMARY docs that day:
Google Cloud Run (2 M requests / 180k vCPU-s / 360k GiB-s free, egress free
only from North America, billing account required), Render free (0.1 CPU /
512 MB, 15-min spin-down, ~1 min wake, no card), Koyeb free (0.1 vCPU, forced
1-hour scale-to-zero, card), Northflank sandbox (always-on, unspecified
compute, egress $0.06/GB, card), Oracle Always Free (2 OCPU / 12 GB since the
June 2026 halving, 10 TB egress, card, 7-day idle RECLAIM — a quiet site is
idle by definition), Vercel Hobby (the SvelteKit half fits; the Flask API and
the PDF proxy do not — 4.5 MB response cap, read-only disk, per-instance cold
memo), Hugging Face Spaces (Docker Spaces now need the paid PRO plan), Fly.io
(no free tier since 2024), Cloudflare Containers ($5 plan), Azure Container
Apps (the same grant as Cloud Run). Measured against this API on a 2.9 GHz
core — cold endpoints 35–470 ms, a memoised hit 0.5 ms — a 0.1-vCPU host
means 0.5–5 s a page even warm, which is what "draggy" would be.

Decisions (user): **Google Cloud Run** (the parked `deploy/cloud-run` design,
one container, two processes); a **free 5-minute pinger** (cron-job.org on
`/api/meta`) instead of a paid always-on instance — Cloud Run keeps an
instance up to 15 idle minutes and bills CPU only during requests, so this
costs nothing; the **host's own `run.app` URL** for now; and **nothing from
the repository owner** — the user has write, not admin, on
`elpidag/evia-khmdhs`, so neither the Cloud Build GitHub App nor a repository
secret was available; **GitHub Actions with keyless Workload Identity
Federation** needs neither (the workflow is a file in the repo, the pool's
attribute condition admits only pushes to `main` of that repository). The
Cloud Build trigger config was dropped — one deploy mechanism.

Four things fixed on the way, three of them found by the review of the
parked branch: (1) the image never copied `atlas/static/geo/effis_fires.geojson`
and `evia_works_zones.geojson`, which `queries_extra` reads at REQUEST time —
in production the EFFIS fire dates and the zone centroids would silently
have been `{}`; (2) adapter-node precompresses by default (so the planned
`precompress: true` was a no-op) but never `.geojson`, and nothing gzips the
SSR document (~220 KB on the data pages) — the Dockerfile gzips the geojson
after the build and `server.mjs` wraps the page path in the `compression`
middleware; (3) **Cloud Run's writable filesystem is in-memory**, so an
on-demand PDF cache growing for as long as a pinger-kept instance lives would
eventually crash it: `atlas_api/pdf_proxy._serve` stops KEEPING downloads
once the PDFs in a cache dir reach `ATLAS_PDF_CACHE_BUDGET_MB` (200 in the
image, 0 = unlimited locally; the committed `.txt` sidecars are never
counted or touched; pinned); (4) the budget alert is €3, not €1 — a €1
budget would fire at ~9,000 visits.

Cost: everything inside the free tier except European egress at ≈ €0.11/GB
— **1,000 visits ≈ €0.11 a month, 10,000 ≈ €1.10** (≈ 1 MB a visit once the
document and the geojson are compressed). Safeguards, in order:
`--min-instances=0`, `--max-instances=3` + `--concurrency=40`, `robots.txt`
denying `/pdf/` and `/api/`, the cache budget, the €3 budget alert, the
optional billing kill-switch. **`data/processed/arogi.sqlite` is never
shipped** (its acts name private individuals; restated from 2026-08-23). The
runbook's «Typekit domain lock» step turned out to be WRONG when the user
reached it: Adobe dropped domain lists from web projects (its help: add the
embed code to any website, wherever it is hosted), and the kit answered a
registered, an unregistered and no referer with the identical CSS and font
files — nothing to register, nothing to publish; the step is gone. Set aside, recorded for later: a fully static export (adapter-static
+ an API snapshot on GitHub/Cloudflare Pages) would be truly €0 and
CDN-fast, but it is a multi-day refactor and loses the PDF proxy.

## 2026-09-03 — the brand is SCORCHED FORESTS (user)

The site's name had carried the mocks' spelling «SCHORCHED FORESTS» since
2026-08-27 — a typo, corrected in the one constant every page title and
header reads (`lib/landing/brand.ts`). The Google Cloud project created the
day before was typed the same way, `schorched-forests`; a project ID is
immutable, so only its display name is corrected ("Scorched Forests") and
the runbook and the workflow say so where they quote the id. The id appears
nowhere on the public site: the service URL carries the project NUMBER.

## 2026-09-03 — THEME LAB: the author's try-out panel for colours and fonts

The author asked for a way to try alternative palettes and typefaces on
the site and only then decide. Built as `lib/dev/ThemeLab.svelte` — a
DEV-ONLY floating panel (lazy-imported by the layout when the URL
carries `?lab`; production never bundles or renders it) that reads the
design tokens from `tokens.css` itself (the ?raw import, so the list
cannot go stale), overrides them LIVE on `:root` while the author
browses the real pages, keeps named presets in localStorage, tries any
Google Fonts family in front of a font token's stack, and copies the
changed tokens as a ready `:root` block to hand back for baking in.
23 colour tokens and the 5 font tokens; the panel's own footer says the
one limitation honestly — chart-internal palettes (categories, year
greys, map ramps) live in code and follow only when a direction is
chosen. Verified live: `--c-dase` flipped to blue repainted the ΔΑΣΕ
card's KPI cards, year bars, pill and symbol instantly, while the
beeswarm's coded greens stood still — the limitation made visible.
Follow-up the same day: the author tried «Novel Sans» and «Gridlite PE
Variable» and nothing happened — commercial faces, not on Google Fonts,
and the loader failed silently. The try now VERIFIES the family against
Google Fonts and says when it is not there (still applying the name as a
locally-installed lookup), and every font row gained a 📁 FILE button:
the author's own .woff2/.otf/.ttf loads straight into the page via the
FontFace API (weight 100-900, so variable fonts render), session-only
and said so — the proper wiring follows once a face is chosen. And for
the fonts in the author's ADOBE account (their two names carry Adobe's
own marks — «PE» is the Pan-European suffix): the panel gained an ADOBE
KIT field — paste any web-project kit id or use.typekit.net URL, its
stylesheet loads, and the kit's CSS family slugs then answer the try
field; smoke-tested with the site's own kit drh1gfl. No download needed:
fonts go into a web project on fonts.adobe.com and connect by id.
And the LIVE state now survives: overrides persist to localStorage on
every change and restore when the panel mounts (`themelab.live` —
google families and adobe kits re-inject themselves; a file-loaded font
stays session-only), so the author browses every page with the trial
theme following (SPA navigation carries the :root overrides anyway) and
a reload with `?lab` brings it all back; «reset» clears the store.

## 2026-09-03 — the palette collapses to ~10 primaries; every grey derives from the ink

The author, preparing to test palettes: too many colours move at once,
above all for TEXT — «give you one of the colours of the ink and you
automatically fill the gradients». The measurements agreed: every grey
already sat on the ink→paper line. `tokens.css` is now PRIMARIES
(--paper, --ink, the three dataset hues + --c-dase-deep, --c-fire, the
three flags — ten knobs) and DERIVED tones — the papers, ink-soft/faint,
line/line-strong, the accent, the fire season, the thresholds and the
map scenery are all `color-mix` fades of ink into paper (or references),
their percentages reproducing the old hand-picked hexes to ±1/255
(verified by probe on the live page: 5/10/26/43/50/58/77%). Changing
--ink refills every grey — tested: a warm brown ink yielded a warm
--line with no other touch. THEME LAB splits accordingly: the ten
primaries carry pickers, the thirteen derived tones display read-only
with live-resolved swatches. The canvas charts read only primary tokens
(--c-dase, --c-fire) — unaffected. Follow-up rulings the same day: the
ALARM RED derives from the FIRE RED whatever the palette
(`--c-flag-red: var(--c-fire)` — the excluded-record chips and the
missing-number mark drop their old vermilion #c23b2e for the one maroon;
verified coupled under a palette change), leaving NINE primaries — then
EIGHT: `--c-dase-deep` is RETIRED (author) — its navy #0d366b printed
only in the hover of a name link in the AWARDING PROCESS sankey, and on
the Anti-nero page that hover silently broke the grayscale doctrine; the
hover is now the accent with an underline, verified on both pages.

## 2026-09-03 — single-bid information comes OFF the site (user)

«We haven't worked on this type of information and I do not want to show
it.» The registry's bids_submitted field (30 in-scope Anti-nero
contracts record exactly one bid, of 55 carrying the field) leaves every
surface: the three «1 bid» warning chips (Anti-nero contracts list,
contractor pages, /explore), the two contract pages' one-bid hints AND
their «Bids» detail rows, the front page's «N contracts drew 1 bid» bar
in PROGRAMME FIGURES and the programme sentence's clause, and the
CONTRACT VALUES beeswarm's ring column (already undrawn on Anti-nero by
the 2026-08-21 ruling; now passed as zeros). The dormant «probably
related» chip — the other --c-flag-amber wearer — stays wired for its
empty tier. API payloads keep the fields; presentation only. Verified:
zero «1 bid» chips and no bid sentence on the rendered pages.

## 2026-09-03 — PROJECTS AND FIRES THAT TRIGGERED THEM leaves the sponsored page (user)

The author: off the website for now, but keep the processes — «we might
come back to it». The frame (the status-coloured project dot map over
the EFFIS burn scars, the baked relief, its legend and caveat) is parked
behind a `SHOW_FIRES_FRAME = false` flag in `/anadohoi/+page.svelte` —
the markup, the layers (FiresLayer, the relief bakes), the data and the
harvest all stay untouched, and flipping the flag brings it back whole.
No live link pointed at its `#fires` anchor. The FROM THE FIRE TO THE
SPONSORED PROJECT lanes and the card's MAP tile are separate surfaces
and stay.

## 2026-09-03 — the /explore round: the author's intro, honest dropdowns, new dataset labels

Four author rulings. (1) The intro is their wording: «Search here all the
contracts and designation acts processed in this website …» with the
tolerance sentence and the searchable-fields list; the counts line it
replaced is gone. (2) The dataset labels read All · Anti-nero ·
F.W.CO-OP · Companies as sponsors — on the toggle AND on each row's
dataset chip. (3) The count/Σ-value summary line is removed («I do not
need this text»). (4) The dropdowns were walked option by option in the
browser: every filter WORKS (proc 2.151/22/30/55/70, statuses 19-29-20-
1-1, value brackets, διακήρυξη, end date, the 60 regions, 224 δήμοι, 32
HQ regions all move the table) — what read as broken were two traps, now
fixed: the «cancelled» status could only ever match zero rows (the live
population excludes cancelled) and is gone, and the dataset-specific
filters hide where they cannot match — the statuses sum exactly to the
70 sponsor rows, so that select shows ONLY on Companies as sponsors
(the author's follow-up), and the rule generalised on their next ruling:
a filter that does not apply to all three datasets shows ONLY where it
can match — published call, municipality and HQ on Anti-nero alone; end
date on Anti-nero and sponsors; the procedure select everywhere but the
sponsors (one route there), its «sponsor» option only under All. And the
procedure labels speak the site's English (procedures.ts, the Directive
wording): Direct award · Open procedure · Negotiated procedure · Other
procedure · Sponsor designation act; the διακήρυξη filter reads
«Published call».

## 2026-09-03 — /explore follow-up: the SEARCH title, the intro at full size, search by forest authority

Three more author rulings the same day. (1) The page opens with a title,
SEARCH, in the display narrow face. (2) The intro is exactly two
sentences — «Search here all the contracts and designation acts
processed in this website. Search is accent-, homoglyph- and
Greeklish-tolerant.» — and the searchable-fields clause of the morning's
wording moved into the box's placeholder («… region, forest
authority…»). The sizing is the CARD PAGES' own (the author's third
ruling, «not bigger not smaller»): the SEARCH title sets exactly like a
stream's name on its card (DatasetCard .bigname — display narrow 900,
clamp(15px, 1.25vw, 24px), lh 1.2) and the intro exactly like the card's
narrative text (font-ui 400, clamp(13px, 0.94vw, 18px), lh 1.2) —
verified computed-style-identical against /anadohoi at 1920. (3) Search reaches the
FOREST AUTHORITIES: `queries_extra.explore_rows` now ships each
Anti-nero chain's linked authorities as `au` (the union of
`contract_forest_authorities.authority_name` over every record of the
chain, from the same layer the contract pages print), and the /explore
haystack indexes them in BOTH languages — the registry Greek and the
site's English form via `names.authEn` — so «Δασαρχείο Λαυρίου»,
«parnithas» and «forest service office» all find their contracts
(verified in the browser: the English-only phrase matches 220 rows,
reachable through no other column). Payload version bumped to v=10; the
real-DB explore pins stay green (the row shape is additive).

## 2026-09-03 — every chart palette becomes a LIVE derivation of the tokens (the Theme Lab follow-up)

The author, trying two saved palettes: «when I use them the colours do not
change accordingly in all the graphs … different colour palettes mix».
They could not: the Theme Lab overrides the CSS tokens, but the charts'
own palettes were TypeScript hex constants — CAT_COLORS, YEAR_COLORS /
YEAR_GREYS, SCOPE_COLORS (both files), the gantt statuses, the map ramps
(RAMP_WORKS / RAMP_DASE / RAMP_HOME), the ΔΑΣΕ map kinds and ~300 inline
hexes across the chart components — none of which read a token.

**The fix, in three moves.** (1) Every palette value is now a CSS string
over the tokens — `var(--…)` where a primary matches, and
`color-mix(in srgb|oklab, anchor P%, paper|black)` fades whose
percentages were FITTED numerically to reproduce the old hand hexes
(greys and the categorical red ramp to 0/255; the sequential green ramps
to ≤10/255 on their two deepest steps — the old scales rotated hue,
which a one-anchor family cannot). SVG fills and CSS surfaces follow a
token change live, with no re-render. (2) Three new primaries anchor the
families the 8 knobs lacked: `--c-cat-blue` #0d366b (flood works + the
blue ramp), `--c-cat-amber` #b07d1e (studies), `--c-cat-red` #b33a1a
(the fire-prevention ramp; its lighter steps are paper-fades at
71.9/50/26%, exact). The greens of the category palette reuse the two
dataset hues. (3) `$lib/theme.svelte.ts` is the bridge for what CSS
cannot reach: `resolveCssColor()` resolves any expression against the
live tokens through a probe element AND reads a reactive tick, so every
canvas draw ($effect) and luminance pick that resolves a colour re-runs
by itself when the Theme Lab announces a change (`themelab:change`
window event, dispatched by apply/clear/reset). Converted that way:
BeeswarmCanvas, StateFunded, SignedTimeline, CodeField, AlertsMap
(canvas); ContractNetwork, StackedYears, BeeswarmCanvas's tip,
DatasetSymbol untouched (header chips are chrome); FiresLayer's year
gradient now derives from the resolved `--c-fire`.

**Fidelity at the default palette** (screenshot-diffed on all four main
pages before/after): /authorities pixel-identical; /antinero max 10/255
(the fitted ramp steps); the only >12/255 shifts are former literal
blacks — the ΔΑΣΕ map's municipal circles, revoked gantt marks — which
now ride `--ink` (#000 → #1f1f1f, 12% lighter, the point of the
conversion). Verified live with a deliberately wild palette (purple
ΔΑΣΕ, teal fire, navy ink, warm paper): choropleths, KindFlow, the
canvas beeswarm, the gantt, waffles, EFFIS scars and the maps all
follow, on all three dataset pages.

**Deliberately NOT following the lab**: the story page's timeline (the
author's artboard colours, pending their /story palette decision), the
baked relief plate + hypsometric legend gradients (image-locked), the
satellite figure's plate, the header band's chip tones (chrome), and
webui (:5000, frozen). The Theme Lab's footer note now says the charts
follow; presets apply whole.

## 2026-09-03 — the header band becomes a gradient of the three stream hues (user)

«The black menu bar … should be a gradient of the three colours we have
for --c-antinero, --c-dase, --c-anadohoi, and the rectangle colours of
that menu bar should also rely on those.» Done, in the order the user
named the tokens: `linear-gradient(90deg, var(--c-antinero),
var(--c-dase), var(--c-anadohoi))` — at the default palette black under
the brand fading through the ΔΑΣΕ green to the sponsored deep green at
METHODOLOGY. The five squares' `chip` tones (datasets.ts) are now token
derivations instead of hexes: the sponsored and co-op squares carry
their own primaries verbatim, and the three squares that cannot sit as
full hues on a dark band are pale fades — antinero 5% into paper
(= the old #f2f2f2 to ±1), search ink 5.8% (= #f2f2f2 exactly), actors
dase 43.3% (≈ the old #b7e4c7). The square lettering's black/white pick
now measures the RESOLVED chip via `theme.svelte.cssLuminance`, which
gained a 1×1-canvas fallback parser: Chrome serialises a resolved
`color-mix` as `color(srgb …)`, which the rgb regexes missed — the first
render printed white names on the pale chips. Verified at the default
palette (byte-equivalent squares, correct lettering) and under a wild
three-hue palette (gradient, chips and lettering all follow the lab).

## 2026-09-03 — the figure captions leave the narrative: `content/story/captions.md` (author)

The author, writing their captions: the `<span class="figmark">…</span>`
wrapper in the middle of their prose «makes it difficult for me to
incorporate the text for the captions, bcs i do not want to mess up how
the appearance of the image works», some captions are extensive, and a
figure the reader switches with the arrow must change its caption with
the image. Three fixes, one round.

**(1) The marker is PLAIN TEXT.** The author writes `[FIGURE 05: Press
conference]` — no HTML at all — and the wrapper goes back on at build
time: `scripts/remark-tag-paragraphs.ts` gained `figureMarkers()`,
registered in `vite.config.ts` BEFORE `tagParagraphs`. The trap it
encodes: `[FIGURE 05: …]` is markdown's own shortcut-reference syntax,
so remark hands it over as a `linkReference` node carrying the text in
`label`, NOT as text with brackets — the first pass matched nothing. It
now handles the reference form, the literal-text form, and a marker the
author already wrapped by hand (which arrives as span · reference ·
span and must not be wrapped twice). All 13 markers in the author's two
files were unwrapped; a marker-led paragraph is now an ordinary
paragraph, so — unlike the raw-HTML block it used to become — its own
prose keeps its markdown (the pairing test was rewritten to pin exactly
that, and that no file opens a paragraph with raw HTML any more).

**(2) The caption text lives in `src/content/story/captions.md`**, the
author's own file, headed by its own instructions: one block per figure,
`## 5`, as long as they like, blank lines making paragraphs, with
`[text](url)`, `*italic*` and `**bold**` as the only mark-up — rendered
by `lib/story/captions.ts` through an escape-first renderer, so raw HTML
in that file can never reach the page as markup. The page still prints
«Figure NN _ » in front (the grid's two captions name their own ranges
and take no prefix). A figure with no entry falls back to the short name
inside its marker, which is what the page printed before — so the file
starts pre-filled with today's names and nothing moved.

**(3) A carousel slide takes its own caption**: `## 2a` is the first
image, `## 2b` the second (the grid's two packs of nine are `## 1a` /
`## 1b`, their wording moved verbatim out of `StoryFigure.svelte` —
author text no longer lives in a component). `captionFor(n, slot)`
resolves slide → figure → marker name. Verified in the browser: the
arrow swaps image AND caption, and swaps back.

The numbering the author already lives with is unchanged and now stated
in the file's header: their `[FIGURE 02]` prints as «Figure 19», because
the opening grid's eighteen images are figures 1 to 18. Pinned by
`captions.test.ts` (every entry keys to a real marker, every marked
figure answers, multi-image figures answer per slot, the renderer
escapes).

## 2026-09-03 — a carousel's caption prints the letter of the image on show (user)

**Decision.** Where a figure has several images the reader switches with the
arrow (today only figure 02, marker `pair` in `lib/story/figureImages.ts`),
the caption's prefix names the image on show: «Figure 19a _ » on the first,
«Figure 19b _ » on the second, and so on through c, d … as the reader
pages. A single-image figure keeps its plain «Figure 20 _ »; the opening
grid keeps no prefix, as before.

**Why.** The captions file already keys a slide's own text by that letter
(`## 2a` / `## 2b`), and the two slides of figure 02 now carry different
captions (Peloponnese / Evia and Attica, 2007) — the printed number must say
which of the two the reader is looking at, or the caption and the image
cannot be cited apart.

**Implementation.** The displayed number is one pure rule,
`figureLabel(n, slot)` in `lib/story/captions.ts` (marker number + 17,
two digits, plus the slot letter where given); `StoryFigure.svelte` passes
the carousel's live slot and nothing for a single image or the placeholder.
Pinned in `captions.test.ts` (02 → 19, 13 → 30, 19a / 19b / 19c, a single
image adds nothing). The captions file's own header still says «Figure NN
_ »; the author may add the letter rule there when they next edit it.

## 2026-09-03 — a caption too long for the page scrolls inside itself (user)

**Decision.** Figure 23's caption (the author's long note on the urban plans
of Mantoudi–Limni–Agia Anna) ran off the bottom of the figure column. From
today a caption taller than its room scrolls within its own box, ending
exactly at the breathing band; a caption that fits has no scroll and no bar.
The figure block keeps its one placement, centred 60 px low.

**The room.** The column's height less twice the drop (the block's centre
sits that far below the column's, so that much is lost at the bottom), the
image's height, the 7 px gap under it and, on a live figure, its credit
line — every term measured in the browser (`bind:clientHeight`), never
assumed, so a window resize or a taller image re-fits it; floor two lines
(34 px), so a small window still shows something to scroll.

**Gotcha.** `overflow-y: auto` alone put a scrollbar under a TWO-LINE
caption that fit: at 12 px / 1.35 the lines are 16,2 px, the block 32,4 px,
and Chrome reported `scrollHeight` 33 against `clientHeight` 32. So the
scroll is switched on (`class:scrolls` + the inline `max-height`) only when
the text's own measured height exceeds the room; otherwise the caption is
an ordinary block. `overscroll-behavior: contain` keeps a wheel at the
caption's end from running on into the narrative. Verified in the browser:
figure 23 scrolls in a 66 px window at 895 px tall, figures 19 and 22 show
no bar.

## 2026-09-03 — figure 23 as an image SLIDER, its block lifted for the caption (author)

Marker 6 (printed as Figure 23) carries the two land-use maps of the
Mantoudi–Limni–Agia Anna urban plans, before and after the 2021 fires,
drawn on one frame. The author: a slider, not a carousel — and «in this
specific case, move the image upwards so you can gain more space for the
caption». `figureImages.ts` gains the kind `slider` (the second map
underneath, the first revealed LEFT of a handle the reader drags; a
transparent range input over the square does the dragging and gives the
keyboard and touch for free; the handle returns to the middle on a figure
change) and an optional `lift` flag: a lifted block starts at the
column's top instead of the shared placement centred 60 px low, and the
caption's room is measured accordingly. For figure 23 that turns 240 px
of room into 360 — its caption is 372 px at natural height, so it still
scrolls, by 12 px. One caption for both maps (no a/b letters — the slider
shows both at once). Figure 24 (marker 7) keeps the carousel.

## 2026-09-03 — the story's third round: no filler around images, the timeline as a focus view, Figure 27 live

Three author requests the same evening. (1) **No white filler**: an image
box is the image's own size — the image shrinks into the 540 square
keeping its shape and the box wraps it (`.box.natural`), so a landscape
photograph carries no paper bars and its caption sits 7 px under the
image itself, as everywhere; the carousel and the slider got wrappers of
the image's size so the arrow, the dots and the handle ride the image;
the grid and the placeholder keep their shapes, and a live figure may ask
for its own height (`frame: 'auto'`). (2) **The timeline opens on a
click**: the rail is a click target (the footnotes under it keep their
own links), and the whole drawing appears as the only thing on the page —
paper over everything, header included (z 300), centred at up to twice
the artboard's size (`StoryTimeline whole maxK={2}`: the box as tall as
the drawing, no pan), scrolling inside the view, the page's scroll
locked behind it; Esc, the ✕ or the margin closes it, and a bullet
closes it and goes to the passage. (3) **Figure 27 is the CONTRACT TYPE
chart** (marker 10, «types of work graph»): the Anti-nero page's bars,
live in the story, fetching the overview after hydration and drawn by
BarH exactly as the frame — through ONE shared transform,
`lib/transforms/categoryRows.ts` (the sort by lens, the works-named
hover, the lower-casing, the hint tails), which the page now uses too
(vitest-pinned), so the two can never drift; credit line under the
author's caption; `figures.test` pins it. Verified live: the photo's box
540×417 with the 7 px gap, the chart 540×322, the frame on /antinero
still drawing its eight bars, the focus view 1040 wide at k 2.

## 2026-09-03 — figures 22 and 25 at 85 %, 25 lifted; Figure 27 wears the frame's title and toggle

The author, on seeing the round: figures 22 and 25 «a bit weird» at full
size — drawn at 85 % of the slot (`scale: 0.85` on the image entry, a
`--img-scale` the box passes to its image), and 25 lifted to the column's
top for its caption's room; and Figure 27 loses the data-credit line but
GAINS the frame's own title, CONTRACT TYPE, and its stated-€ /
number-of-contracts toggle — the site's `SegmentToggle` on the same
`?ct=` the Anti-nero page uses. A layout trap surfaced with the scale:
inside the natural box's GRID, a percentage max-width on the image
resolved against its own centred area, so 0,85 drew as 0,85² (390 px)
in a box taller than the image; the natural box is a FLEX column since,
where the percentage is the slot's width and the box is exactly the
image (a px cap for the height — a percentage against an auto-height
box resolves to nothing). Measured: 459 px for both, 7 px to the caption.

## 2026-09-03 — round 4b: the focus view at 130 %, the figure's title in the caption's type, Figure 25 centred with its caption no wider than its image

The author, on the previous round. (1) The enlarged timeline «shouldn't
be that wide, it becomes disproportionate»: the focus view is now 130 %
of the RAIL's own width (`railW` measured on the aside, the box set from
it — 650 px on the 500 px rail, k 1,25, centred), so the reader sees a
bigger span of time at once rather than a giant drawing. (2) The
CONTRACT TYPE title on Figure 27 is «only for this page, in the same
type as the figure»: the caption's face, size and tone (font-ui, fs-12,
ink-soft), not the frame's display title; the lens toggle is smaller
(11 px lettering, 2×8 px padding) — both scoped to the story figure,
the /antinero frame untouched. (3) Figure 25 returns to the shared
centred placement (no lift), and a scaled image's caption is no wider
than the image and sits under it: the scale rides the stack so the
caption reads it (`width: calc(--fig-w × --img-scale)`, `align-self:
center`) — measured: image and caption both 459 px wide at the same
left edge, 7 px apart; an unscaled figure's caption is unchanged.

## 2026-09-04 — Figure 23's slider opens enlarged and centred, the slider still working (author)

«Figure 23 should also have the possibility to enlarge and become
central on the page, retaining the function of the slider.» A corner
button (⤢, in the carousel arrow's dress — the slider's own surface is
the drag, so it cannot also be the click) opens the two maps at the
window's size (max 92 vw × 88 vh; 1100 px wide at 1920×1080), centred on
the page's paper over everything, with the SAME handle: the slot's
position is carried in and a drag in the enlarged view is carried back.
✕, Esc or the margin closes it; the page's scroll is locked behind it.
The slider markup is one snippet drawn in both places. A stacking trap:
the figure column lives inside the sticky rail, whose own stacking
context (z 3) kept the overlay UNDER the header (z 100) — the enlarged
view is PORTALED to <body> by a small action, which also wires its click
and input itself, because Svelte 5 delegates those events from the app's
root and a node moved to <body> no longer bubbles through it. Verified:
the view covers the header, a pointer press at 70 % of the enlarged map
moves both handles to 70,5 %.

## 2026-09-04 — Figure 21 loses its credit line; the attributions move to the SOURCES section's care (author)

The author asked the imagery/burnt-area/alerts credit off Figure 21
(the 112 alerts map). Removed from the figure; the text itself stays in
`transforms/alerts.ts` (`ALERTS_CREDIT`, pinned) because it is not
decoration: the EOxCloudless base plate is CC BY-NC-SA and the
Copernicus Sentinel and NASA VIIRS data carry attribution terms, so the
attribution must be printed SOMEWHERE on the site — the author's own
SOURCES section (`sources.md`, still empty) is where it belongs. No
figure now prints a credit line; the `credit` field stays in the
registry for any figure that needs one.

## 2026-09-04 — the methodology, bibliography and sources read ALONE (author)

«For the methodology … the figure no longer appears while you are reading
it, and leave the text in the middle; the same for BIBLIOGRAPHY and
SOURCES; the organisation of KEY FINDINGS stays as it is.» Until now the
figure in force was carried forward into the methodology (Figure 30, the
last marker of the chronology, stood beside it) and the text/figure pair
sat centred as a block. Now `figureOff` (the reading line's section is
methodology, bibliography or sources) empties the figure rail — the
carried figure is withheld, the rail fades — and `.cols.solo` closes the
rails' tracks so the 556 px text column sits in the middle of the page
(614 + 556 + 614 = 1784; measured 682 px either side at 1920). KEY
FINDINGS keeps the centred pair with its rail card (383 / 980). Measured
per section in the browser.

## 2026-09-04 — KEY FINDINGS rebuilt: the KPI cards at the dock, the STATE-FUNDED chart across the page (author)

Three author rulings. (1) The KPI cards appear once the KEY FINDINGS AND
OPEN QUESTIONS title has docked AND the section's first paragraph («The
expansion of public funding for forestry work did not expand the
existing cooperative route…») has reached the top of the column too —
a docking observer on that paragraph (`kfDocked`, the introduction's
technique) gates the rail's first card; until then the rail is empty.
(2) The cards are TWO COLUMNS — the Anti-nero programme, the forest
workers' co-operatives — with two cards each, the stated money and the
number of contracts (four values, all computed from `/api/compare`; the
gap ratio and the shared-companies cards are gone from the rail).
(3) After the sentence ending that paragraph («…has overwhelmingly
reached a different population of contractors.») the STATE-FUNDED
chart — every contract of both programmes as a dot, the chart the
author calls the allocation of state funding via different contracts —
is presented across the WHOLE PAGE, and the next paragraph follows it.
Mechanism: the author writes `[CHART: state-funded]` on a line of its
own in keyfindingandopenquestions.md (a marker like their `[FIGURE]`
ones; the line is theirs to move); a new remark plugin `chartMarkers`
turns it into a placeholder `div.chartmark` at build time (content.ts
skips the line, so the rendered paragraphs still pair 1:1 with the
parsed blocks — the pairing test now runs the same plugin chain as the
build); the story page mounts `ChartBand.svelte` (Svelte's `mount`) into
the placeholder, full-bleed — the narrative column's distance from the
window's edge and the window's width without its scrollbar are measured
live (`--nar-left`, `--page-w`) so the band spans the page with no
horizontal scroll — the chart inside at the site's 1152 px, centred,
with its title and the zero-shared-companies note. In stacking the band
sits above the rails (the narrative column is lifted to z 1, the rails
have none) and below the docked section titles, so it slides over the
sticky cards as the reader scrolls, the way content passes a sticky
panel — a first draft faded the rail while the band was on screen,
which hid the cards at the very moment they appeared (the band's top is
479 px down at the dock on a 1080 window). The rail card's later items
(SIGNED, SIZES, REGION BY REGION, MONEY PER YEAR) advance as before.
Measured: cards at the dock (first paragraph's top 119 px, title 125),
the band left 0 / width 1920 with the second paragraph below it, the
band over the card zone at the reading depth, the title on top.
**Follow-up the same day** — the author: «figure 30 is half appearing
at the start of key findings». Before the first paragraph docked, the
rail's fallback branch still drew the figure IN FORCE, carried in from
the chronology's last marker (30). Inside KEY FINDINGS the rail now
shows nothing until the cards dock (`kfAt < 0` guards the carried
figure). Found while the API server was down (a torn-down background
process — every story load 500'd until it was restarted).
**Second follow-up** — the author: no title on the band (STATE-FUNDED,
TWO WORLDS is gone; the chart's own caption line and side labels say
what it is); the KPI cards row-aligned across the two columns (the
headers on one bottom-aligned row, then the cards ROW by ROW — the
co-operatives' two-line header no longer pushes its column down), set
44 px below the section title's line rather than level with it, and a
little smaller (92 px, from 120). Measured: header bottoms 203/203,
card rows 215/215 and 319/319, title bottom 162.

## 2026-09-04 — the first of the author's symbols: the forest co-operatives' drawing on the hub and the card

The author delivered `CO-OP.svg` (a single black path, 570×320) for the
co-op stream, to be placed «first in /data where we have the space for
symbol, and in the card page instead of the rectangle». It lives at
`atlas/static/img/symbols/coop.svg` and is declared on the stream's
entry (`datasets.ts` `symbol`); `DatasetSymbol` draws a declared symbol
as a CSS MASK filled with the stream's hue — so it prints in --c-dase,
follows the Theme Lab, and keeps the drawing's own proportions inside
the slot — with no square and no border, on every surface but the header
band, whose lettered squares stay until the author says otherwise. The
other four slots keep their «space for symbol» placeholders. Verified:
the hub's co-op slot and the /dase card's mark carry the mask (163 px
slot, rgb(82,183,136)); the band's co-op square is still lettered.

## 2026-09-04 — the card pages OPEN with the symbol at twice its size, the name on one line below (author)

«When you enter the card page of each category the symbol is twice the
size and the title is in one line below it, and once you start to scroll
the text it takes the size you now gave to it.» `DatasetCard` holds an
`intro` state: the symbol at `clamp(192px, 16.94vw, 325.2px)` — twice the
reading `clamp(96px, 8.47vw, 162.6px)` — with the name's three artboard
lines flowing on ONE line under it (`.who.big.intro`, a column); the
narrative scrolls inside its own column, so its scrollTop is the
signal — the first scroll brings symbol and name to the reading
arrangement (the symbol's width/height transition 0,45 s; the row/column
switch is instant), and scrolling back to the top brings the opening
back. Measured on all three cards at 1920: opening symbol 325 px, name
1 line below it; after a scroll 163 px, the name beside it on its
artboard lines (2, 3 and 1). A text short enough not to scroll would
keep the opening — none of the three is.

## 2026-09-04 — the refresh line joins «explore more» on the cards; the card page never scrolls (author)

«Place 'Records last refreshed on … · how these figures are made' next to
the explore more, even in smaller letters; I do not want the whole page
to have a scroll, just the text in the card pages.» The line used to
follow the card at the page's end — 33 px past the viewport, so every
card page scrolled. It now sits INSIDE the card's left column beside the
pill (`DatasetCard .foot`; `RefreshLine compact`: fs-12, no rule, no
margins, in the faint ink), and the three pages no longer render it
themselves; the EXPANDED page (`#more`) keeps the full line at its end,
rendered by the card. Measured on all three cards at 1920×1080: page
scrollHeight 1080 = the window, the line at 12 px on the pill's line.

## 2026-09-04 — two more symbols, the hub without the band, the methodology as the story's section (author)

(1) The author's `financed.svg` (the sponsored stream) and `search.svg`
(the search tool) join `coop.svg` under `static/img/symbols/`, declared
on their `datasets.ts` entries and drawn the same way — a mask in the
stream's hue on the hub and the cards, the band's lettered squares
untouched; the Anti-nero and actors slots keep their placeholders.
(2) «I do not want the menu bar on /data»: the hub carries the brand
itself, so the layout renders no band there (`isHub`, like the landing)
and the hub's viewport sizing subtracts a zero header (`main.card.nochrome`
sets `--header-h: 0`). (3) «Instead of the extra page of methodology, link
to the METHODOLOGY section of the story»: every methodology link on the
site — the band's METHODOLOGY, the landing menu cell, the chart frames'
caveat links, the freshness line's «how these figures are made», the
prose links on the dataset and contract pages (17 in all) — points to
`/story#methodology`, and the old `/methodology` address (with any anchor
an old link carried) forwards there with a 308; the standalone page's
component stays parked, unreachable, so the anchor tests that read it
keep passing. The deep anchors into the four methodology rules are not
carried over: the section is the target, as the author said.

## 2026-09-04 — the hub re-set: title higher and smaller, symbols bigger, names in colour on hover; the bibliography's entries re-paragraphed

The hub (`/data`), the author: the title 80 px higher (its cap line at
55 px instead of 135 at 1080) and smaller (54/36 px from 72/48); the
symbols bigger (streams 251 px from 186, tools 132 from 98); each name
in its stream's own colour (the tools in ink); the names shown on HOVER
only — kept in the layout at opacity 0, so nothing moves when one
appears; keyboard focus shows them too. The hub still composes one
viewport (scrollHeight 1080). Separately, the author's edited
bibliography.md arrived with its 29 entries on consecutive lines and no
blank line between them — markdown reads that as ONE paragraph, and the
page showed one 29-reference block. A blank line was put back between
entries (structure, not wording — the same repair as the introduction's
on 2026-09-03); each reference is its own paragraph again. The new
caption of Figure 30 and the curly-quoted, re-ordered references render
as written.

## 2026-09-04 — the sponsored page's expanded view loses THE SCHEME and its basis line; the way back is an arrow at the left (author)

On «explore more» of the sponsored card the author wants neither THE
SCHEME paragraph nor the BASIS line (the card's own text says what the
scheme is), and finds the head's symbol and title redundant — «the user
already knows they are in that category». The `.about` block leaves the
anadohoi page's expanded snippet (the two other dataset pages keep their
PROGRAMME paragraph and basis line, not asked about), and the shared
expanded head (`DatasetCard .resthead`, all three cards) is now the way
back alone — an arrow, «←», at the LEFT, with its accessible name — no
symbol, no stream name. The first frame under it is PROJECT SCOPE.
**Follow-up the same day** — «for the Anti-nero programme and the forest
co-op work accordingly»: THE PROGRAMME and THE CO-OPERATIVES paragraphs
and their basis lines leave those two expanded pages as well (the
Anti-nero record-kinds note and the probable-tier disclosure, other
matter, stay). And the way back is the author's own `arrow.svg`
(`static/img/symbols/`), drawn as a mask in the card's accent, 44×26,
no pill — on all three.

## 2026-09-04 — METHODOLOGY leaves the menu bar; the Anti-nero and co-op expanded pages open on one row of KPI cards (author)

(1) The band no longer carries METHODOLOGY (the story's section is the
methodology, reached from the landing menu, the frames' caveats and the
freshness line). (2) On «explore more», PROGRAMME FIGURES (Anti-nero) and
CONTRACT FIGURES (co-ops) are ONE ROW of five cards — contracts ·
contractors / co-operatives · stated value excl. VAT · share of direct
awards · already paid — in the stream's hue (`KpiCards`), replacing the
direct-award bar and the paid card the hero used to carry. (3) The
record-kinds note («All 254 are συμβάσεις … what each record is», every
figure computed from `kh_doc_<kind>`) is no longer a paragraph: it is the
Anti-nero CONTRACTS card's HOVER — `KpiCards` gained an optional `hover`
per card, the site's black card under the KPI, shown on hover and on
keyboard focus. Measured: five cards on one row on both pages (254 · 157
· 633,59 m € · 90,2% · 456,37 m €; 2.004 · 246 · 30,16 m € · 95,9% ·
20,41 m €), the note appearing on hover, no METHODOLOGY in the band.

## 2026-09-04 — the author's Theme Lab picks are baked: terracotta fire, ink-grey Anti-nero, News Cycle for the UI; the sources re-paragraphed

The author handed over the lab's «copy CSS»: `--c-fire: #b33a1a`,
`--c-antinero: #1f1f1f`, and News Cycle at the head of `--font-ui`.
Baked into tokens.css — and because every chart palette now derives from
the tokens (2026-09-03), the whole site followed at once: the EFFIS burn
scars, the fire season, the ν.4782 ceilings and the median lines are the
terracotta (the same hex as the work-type palette's red anchor, the
author's choice); the Anti-nero stream's hue is the ink grey rather than
pure black (its KPI cards, chips, the band's left end, the STATE-FUNDED
and SIGNED dots); the UI face is News Cycle — a Google Font, loaded from
fonts.googleapis.com in app.html beside the Typekit kit (the site's
fonts are external CDNs since 2026-09-02); it has Latin only and weights
400/700, so Greek text falls through to Futura 100 Greek, glyph by
glyph, as the stack orders. Verified: the tokens computed on the page,
the News Cycle faces loaded, body text set in it.

Separately, «the sources do not print well»: `sources.md` had its 27
entries on consecutive lines, which markdown fused into one paragraph
(the bibliography's problem of the same morning). A blank line between
entries again — structure, not wording — and the section takes the
bibliography's small type (13 px): 27 paragraphs, each a figure's source.

## 2026-09-04 — the band unfilled, the brand in the two hues, the author's drawings for all five symbols (author)

Three more drawings arrived — `antinero.svg` (the programme), and the
network in two versions, `network_bw.svg` and a full-colour `network.svg`
— completing the five. The author: on /data use the coloured network; the
menu bar «not filled with any colour»; the title at the same spot, a bit
enlarged, SCORCHED FORESTS in the Anti-nero hue and COVERED WITH MONEY in
the sponsored one; the five squares replaced by the black-and-white
drawings, the current page's drawing shown in colour. Done: the header's
background is the paper (not transparent — the sticky band must not let
the scrolling content show through); the brand a quarter larger (22,5 /
15 px at 1920) in `--c-antinero` / `--c-anadohoi`; each symbol on the band
is its drawing as a MASK in ink, in a box 1,7× the old square's width so
the landscape drawings keep their size, no ring; the current page's
drawing takes its stream's hue — and the network, whose author made a
coloured version, shows that image instead (`symbolColor` on the entry),
on the hub too. Verified on /dase (co-op drawing green, the rest ink) and
/authorities (the coloured network), and the hub's five.
**Follow-up** — the programme's drawing is very wide (707×289), so at the
cards' shared opening size it read small: its entry carries
`openScale: 1.4` and the Anti-nero card opens at 455 px (the others at
325), the reading size unchanged. And COVERED WITH MONEY on the band is
bolder (700, from 500).
**Corrected the same hour** — the author: «I meant it should be like the
other two; inspect why it was different». It was the BOX: every drawing
sat in a square, and the programme's very wide drawing occupied the
square's middle third, its name far beneath the visible drawing — the
enlargement made that worse. Now each symbol's box takes the DRAWING'S
OWN SHAPE (`aspect` = the svg's viewBox ratio on the entry; `size` is
the longer side), everywhere but the band: the programme opens 325×133
with its name 22 px under the drawing, exactly as the co-ops' 325×183
and the sponsors' 269×325; `openScale` is gone. Also on the band: the
word START (18 px, the story's door) before the sponsors' drawing, and
the two tools 30 px from the streams instead of 110. And a loop found
on the way: releasing the opening reflows the column, the narrative
re-clamps its scroll and reports 0, and a handler reading 0 as «back
at the top» re-opened it — the release is ONE WAY on scroll now, and
only a wheel up while at the top restores the opening (verified with a
real wheel on all three cards).

## 2026-09-04 — the hub's caption on two lines; its drawings equal in area, on one baseline (author)

«Write the caption in two lines; organise the symbols better, they seem
weird now.» The caption («select to explore more about the different
streams of forestry works») sets on two balanced lines (a 22 em measure,
`text-wrap: balance`; the author's words untouched). The drawings looked
disorganised because each was sized by its LONGER side: the wide digger
came out small and low, the tall hand large, tops aligned and bottoms
ragged. Now each drawing is sized to the SAME AREA — the longer side
grows with the square root of the shape's elongation — and the row
stands them on one baseline, their names on one line beneath:
measured 164×199, 283×116, 241×135, all ≈ 33k px², bottoms level; the
two tools likewise. The hub still fits one viewport.

## 2026-09-04 — the search symbol in the fire red (author)

The magnifier was drawn in the ink like the network. It is now
`--c-fire` (`datasets.ts`, the search entry's `color`): on the hub the
mask and the hover name are red, on the band the drawing turns red when
the search page is the current one (ink elsewhere, as every other
drawing). The chip tone stays as the fallback for a symbol-less entry.

## 2026-09-04 — the landing menu re-set to the author's second artboard: drawings of the data in the cells, still codes in the white ones (author)

The author's updated `landing_menu.svg` (Downloads, 2026-09-04) decides
what each of the sixteen rectangles holds; «the rectangles that are left
white should be filled with the codes but they shouldn't be moving».
Read from the artboard (cell ≈ 270 px, the merged cells with no rule
between them):

| cell | holds | drawn from |
|---|---|---|
| r1c1 · r1c2 · r1c4 · r3c3 | a STILL field of codes (one seed per cell; r1c1 is where the opening animation lands, the ↻ stays) | `/api/landing` codes, `CodeField playing={false}` draws once, no loop |
| r1c3 | the network drawing in colour → /authorities | `network.svg` |
| r2c1 | START HERE, 36 px Obviously Narrow Bold in the co-op green, top-right → /story | — |
| r2c2 + r3c2 (merged) | the co-op CONTRACT VALUES swarm: one dot per live ΔΑΣΕ contract on the /dase doubling axis, dodged about the middle, the median a dashed vertical | `menu.dase` on `/api/landing`: the 2,004 values, `dase_value_histogram`'s edges and median |
| r2c3 | EXPLORE THE DATA, 24 px, bottom-right → /data | — |
| r2c4 | the author's fire image (`bs-distorted.png` → `static/img/landing/bs-distorted.webp`, 245 KB) | — |
| r3c1 | METHODOLOGY, bottom-right → /story#methodology | — |
| r3c4 | a stacked column of the three streams' stated € (co-ops · sponsors · Anti-nero, top to bottom) | `/api/meta` |
| r4c1 | twelve bars, the biggest sponsors by committed € | `menu.sponsors` on `/api/landing` = the sponsored ranking's top 12 |
| r4c2 | the sponsors' plant drawing, larger than its cell so the hand is cut → /anadohoi | `financed.svg` as a mask |
| r4c3 + r4c4 (merged) | Εύβοια from the site's Π.Ε. layer in the co-op green, running off the right and bottom edges | `pe.topo.json` |

The artboard's stacked column and bars are schematic (33:100:100, a
descending run); on the site they carry the real figures — the column's
blocks are the streams' € (the co-ops 4,8 %, the sponsors 6,1 %, the
programme 89,6 % of the three together), the bars the ranking's own
values — read from the same functions the dataset pages draw from, so
the menu can never disagree with them (`test_landing_pins`). The
artboard's «EPLORE THE» is the label's typo. The old GR / EN mark, the
black START HERE cell and the drifting cell field are gone.
`homeCells.ts` carries the map with row/column SPANS (`cellGrid` marks
the covered slots, `gridArea` places each cell), `HomeGrid` renders by
kind, the four data drawings live in `lib/landing/cells/`
(`SwarmCell` canvas with d3's greedy dodge, `StackCell`, `BarsCell`,
`IslandCell` with d3-geo). Verified at 1920×1080 against the artboard;
two frames a second apart are pixel-identical (nothing moves).

## 2026-09-04 — the landing menu's drawings are the author's own, schematic (author)

«I have added the svgs I want you to use on the landing page. For the
landing page the graphs can be just schematic.» The four live drawings
of the data built the same morning (the ΔΑΣΕ swarm, the € stack, the
sponsor bars, Εύβοια from the Π.Ε. layer; `lib/landing/cells/`, the
`menu` block on `/api/landing` and its pins) are RETIRED — deleted, not
parked — and the cells show the author's files from
`static/img/symbols/`: `landinggraph03.svg` (the swarm with its dashed
median, across two rows), `landinggraph02.svg` (the stacked column),
`landinggraph01.svg` (the bars), `landingtree.svg` (the plant, a link to
/anadohoi) and `landingmap.svg` (Εύβοια, across two columns), each an
`<img>` at the artboard's own offsets — left, top and width as
fractions of its cell, the height the file's own (`HomeCell` kind
`image`). They carry the author's colours as drawn and do not follow the
Theme Lab, like the story timeline's artboard. They are pictures, not
figures: nothing on the landing states a number, so the no-hardcoded-
number rule is not engaged. The still code fields, the three links, the
network symbol and the fire image stay as the entry above says.

## 2026-09-04 — the programme's name is written «Anti-nero», «ANTI-NERO» in capitals (author)

«Wherever we use antinero it is written consistently as Anti-nero and,
when it is all caps, ANTI-NERO.» A sweep of the site copy found four
other spellings — AntiNero (the author's own text on the cards and in
the story, the parked methodology page), AntiNERO (the timeline's
launch event, from the author's spreadsheet), Antinero (the probable
tier's sentence) and ANTINERO (two captions and the sources' figure 27
line) — and set them all to the rule. NOT changed: cited titles keep
their sources' spelling — the bibliography, the chronology's footnotes
14 and 15 (Papageorgiou's «Φάκελος «Antinero»» articles and their
bracketed translations) and the ministry map's title «Πρόγραμμα
Προστασίας Δασών ANTINERO» in the sources — nor identifiers (routes,
keys, `--c-antinero`, type names), nor registry titles in the data
(«ANTINERO IV ΑΤΤΙΚΗΣ» is what ΚΗΜΔΗΣ says) and the search fold that
maps «ΑΝΤΙΝΕΡΟ» onto them. The stream label reads «Anti-nero programme»
(a proper noun keeps its capital in the lowercase labels; the card's
uppercase transform makes ANTI-NERO PROGRAMME). The timeline importer
normalises the name on import so a re-run of the spreadsheet keeps the
rule.

## 2026-09-04 — KEY FINDINGS re-set: the text in the middle, CONTRACT SIZES left, the KPI cards right, three full-width charts in the flow (author)

The author's four instructions, in one round: «the main text stays in the
centre»; «the ALLOCATION OF STATE FUNDING chart must not start playing
before the user can see it in full»; «CONTRACT SIZES appears on the left
of the main text when the KPI cards appear»; «EVERY CONTRACT, BY THE DAY
IT WAS SIGNED goes full width after the sentence ‹Forest intervention is
made increasingly calculable … repeatedly procured›»; and «after the
sentence ‹All €633.6 million is awarded by the Ministry … contracted
elsewhere› present the AWARDING PROCESS graphic from Anti-nero and the
forest co-ops».

- **Layout.** While the reader is in KEY FINDINGS the grid is symmetric
  (`.cols.kf`: 540 · 94 · 556 · 94 · 540), so the narrative column's
  centre is the page's (measured 960 at 1920). CONTRACT SIZES renders in
  the LEFT rail (`aside.kfleft`, the timeline's column) and the KPI cards
  in the right, both from the same dock — the first paragraph reaching
  the docked title; the last two paragraphs swap the right rail to
  REGION BY REGION and MONEY PER YEAR (`KF_PARTS` by paragraph index; the
  left keeps the sizes). `KeyFindings` takes a named `part` instead of an
  index.
- **Bands.** `ChartBand` has three kinds, mounted into every
  `[CHART: name]` placeholder: `state-funded` after paragraph 1 (as
  before), `awarding` — the two AWARDING PROCESS sankeys, Anti-nero over
  the co-ops, each with its computed note — after the Ministry sentence,
  and `signed` — the SIGNED timeline with its note and caveat — after
  paragraph 3. The awarding diagrams are built by the new shared
  `transforms/awardingFlows.ts` (`antineroAwardingFlow`,
  `daseAwardingFlow`, `FOREST_KIND_COLOR`), which the two dataset pages now
  use as well, so the story cannot draw a different diagram from the
  pages (17 and 19 nodes as before, verified).
- **The author's text.** The second paragraph is SPLIT at the Ministry
  sentence to give the band its place — a structural change only, the
  words untouched (disclosed); the two marker lines are plain text in
  `keyfindingandopenquestions.md`. KEY FINDINGS now has six paragraph
  blocks.
- **Autoplay.** STATE-FUNDED's observer threshold was 0,35; it now plays
  only when the whole chart is in view (threshold 1, or the viewport's
  share of a taller chart), `data-played` on its wrapper for the tests.

## 2026-09-04 — a band passing over the rails: the rails step aside, the title row keeps its paper; the two awarding diagrams side by side (author)

The author's screenshot showed the STATE-FUNDED band leaving upward with
the KPI cards half under its bottom edge, CONTRACT SIZES' title under it
too, and the dots strewn either side of the docked section title. Two
mechanisms, story page only:

- **The rails are VEILED while a band overlaps their items** — one
  IntersectionObserver over the `.chartmark` bands whose root zone is the
  rails' items' own vertical range (measured after each part swap and on
  resize; no scroll listener), so the cards and the sizes keep the room
  ABOVE a band as it approaches, fade out (0,25 s) as it reaches them and
  return once its bottom has cleared them. The earlier objection (a fade
  hid the cards the moment they appeared) was to hiding the rails whenever
  a band was in VIEW; the zone is now the items' box, which the
  state-funded band reaches ~200 px after the dock.
- **A full-bleed paper strip under the docked title row** (`.tstrip`, a
  zero-height sticky element inside the narrative, 40 px painted, z 3
  under the titles and above the bands), only while the reader is in KEY
  FINDINGS — the chronology's figure pins at the same top and must not be
  covered.
- **The two AWARDING PROCESS diagrams sit side by side** on a band of
  min(1800 px, 96 vw): the co-op diagram at 150/300 px margins (the
  /dase frame's 340/340 would leave no plot in half a band), both 620 px
  tall; one column under 1100 px.

The consequence, measured at 1920×1080 and stated to the author: with
three full-width bands in a six-paragraph section, the sticky rails are
veiled for most of it — the STATE-FUNDED band's top is already inside
the sizes chart's box at the dock, and the gap between that band and the
awarding one (one paragraph) is shorter than the items' box — so the
cards and CONTRACT SIZES are seen for a stretch of two paragraphs after
the awarding band and REGION BY REGION / MONEY PER YEAR after the signed
one. The veil drops at once and the return fades in. An in-flow
alternative (the cards and the sizes as a two-sided band after the first
paragraph, nothing sticky in the section) was offered, not built.

## 2026-09-04 — KEY FINDINGS frames: the signed timeline retitled and reworded, MONEY PER YEAR vertical in both colours, the sizes note legible (author)

- The signed frame is «TIMELINE OF CONTRACTS BY THE DAY THEY WERE SIGNED»
  (the author wrote «BY THEY DAY» — read as «BY THE DAY»). Its note keeps
  the computed first sentence (in-season counts, shares and €) and
  continues with the author's own two sentences on the months; the
  «busiest year» clause is gone. The sentences were checked against the
  signature dates before they went in: 80,8 % of the co-op contracts are
  signed in August–November, and 80,7 % of Anti-nero's in March–October
  (32,7 % in March–April, 48,0 % inside the season). «AntiNero» in the
  author's sentence follows the spelling rule of the same day.
- MONEY PER YEAR, in the story only: `charts/YearColumns.svelte` — one
  group of two columns per year, ink and green, each column's height the
  programme's SHARE OF ITS OWN TOTAL (a €30M programme beside a €634M one
  cannot share a € axis), the € printed on every column; the dataset
  pages keep their horizontal bars.
- CONTRACT SIZES: the two median labels sat on one row and ran into each
  other at the rail's width — the co-op label now takes a row above
  (CompareHist top margin 30 → 44). The 11 px bracket caveat was
  illegible: its substance joins the note («shared log₂ brackets, each
  programme as a share of its own contracts; stated values excl. VAT»),
  and the remaining KEY FINDINGS caveats are set at the notes' 12 px.
