# FireWatch vs evia-khmdhs — key insights

Comparison of [fire-watch-app.gr](https://www.fire-watch-app.gr/) (repo:
[troboukis/2026_fire_protection](https://github.com/troboukis/2026_fire_protection))
against this project. Based on their `Methodology.md`, `README.md`,
`DATA_CLEANING_DECISIONS.md`, and a full read of the repo's SQL schema/RPCs,
ingestion code, processing scripts and React frontend. Reviewed 2026-07-25.

## What FireWatch is

An independent public-interest platform monitoring **all fire-protection
spending in Greece** — municipalities, regions, ministries — from 2024
onward, joined with live fire data. Stack: Python collectors → Supabase/
Postgres (server-side RPC aggregation) → React 18 + TypeScript + Vite + d3
frontend on Vercel, refreshed by GitHub Actions. Data: KHMDHS contracts
discovered by **CPV code**, Diavgeia decisions by keyword search, Copernicus
EFFIS burned areas, NASA FIRMS thermal anomalies, a live scrape of
fireservice.gr incidents, 112 alerts, geocoded news articles, and
per-municipality central funding allocations (hand-collected ministry PDFs
going back to 2016).

The two projects answer different questions. FireWatch is a **broad live
monitor**: "how much is Greece spending on fire protection, where, right
now?" Ours is a **deep forensic audit of one programme**: "what exactly
happened to the Anti-nero money, contract by contract, payment order by
payment order?" Their breadth necessarily trades away the per-record
verification we do; our depth trades away breadth and freshness.

Interesting scope fact: their KHMDHS fetch **excludes** `αναδάσωσ*`
(reforestation) by keyword, while their Diavgeia relevance list includes
`antiNERO` — so the Anti-nero programme sits mostly *outside* their
procurement dataset. The projects genuinely complement rather than
duplicate each other.

---

## Deep dive 1 — Database & ingestion

**Schema (Supabase/Postgres, `sql/001_schema_erd.sql`).** Dimensional
design: `procurement` (~60 cols, UNIQUE `reference_number`, chain columns
`prev_reference_no`/`next_ref_no`), `payment` (**1:1 per procurement**,
UNIQUE `procurement_id`), `cpv` (1:N), `diavgeia` (UNIQUE `ada`),
`beneficiary` (PK VAT, + `gemi`), entity tables `organization` /
`municipality` / `region`, bridge tables `diavgeia_procurement`,
`diavgeia_beneficiary`, `payment_beneficiary`, plus fire tables
(`copernicus_fire`, `current_fires`, `news_fires`, `forest_fire`, `fund`,
`works`). All tables carry `created_at`/`updated_at` with a shared trigger;
FKs are `DEFERRABLE INITIALLY DEFERRED` because payment↔procurement is a
genuine cycle.

**Entity identity.** Organization keys are deterministic hashes
(`org_{sha1(normalized_name)[:20]}`, or `org_afm_<ΑΦΜ>` when a VAT is
known), and one key deliberately spans **multiple rows — one per observed
name variant** (`UNIQUE (organization_key, organization_value)`). Display
name is resolved at query time via `LEFT JOIN LATERAL … LIMIT 1`. This is
their answer to the "no unified entity naming in Greek registries" problem;
we sidestep it because ΥΠΕΝ is our only authority, but it's the right
pattern if we ever widen scope. AFM match takes priority over name match.

**Business-key dedup.** A documented priority — `ref:<reference_number>` →
`ada:<diavgeia_ada>` → `cn:<contract_number>|org:<key>` → fallback
(org+date+title) — is used both at ingest and re-implemented as a
`ROW_NUMBER() OVER (PARTITION BY COALESCE(...))` in **every** RPC.
Correct, but the logic is duplicated across ~10 SQL functions and the
Python ingest — a maintenance hazard we should not copy (our single
`contract_scope` table computed once by `scope_loader` is the better
factoring).

**Supersede chains.** Two-layer defence: at ingest, superseded rows get
their amounts **zeroed** (`totalCostWithoutVAT='0'`, plus an UPDATE zeroing
`payment.amount_without_vat`), and every RPC re-excludes them with
`next_ref_no IS NULL AND NOT EXISTS (SELECT 1 FROM procurement p2 WHERE
p2.prev_reference_no = p.reference_number)`. Contrast with us: they keep
the *newest stated amount*; we keep **what was actually paid** (per-order
##PAY sums attributed along the chain). They also have no equivalent of our
additive-ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ rule — a supplementary contract pointing at its
parent would silently zero the parent there.

**Amounts.** `diavgeia.spending_contractors_value` is stored as **raw
TEXT** (even multi-amount lists), parsed downstream with an ordered
fallback (`spending → commitment → direct → payment` value). Honest
raw-preservation, but it means every consumer re-parses; our typed
`amount_with_vat` + curated corrections is stricter. Their RPC amount
cascade is `COALESCE(SUM(payments), contract_budget, budget)`.

**Security/ops details worth noting**: RLS enabled with public-read
policies and `SECURITY INVOKER` on all 17 RPCs; expression indexes on
`NULLIF(BTRIM(prev_reference_no),'')` to make the chain-exclusion fast;
open-data CSVs exported nightly with row-count validation and atomic
`.tmp`→rename writes (same pattern as our `_save_atomic`).

## Deep dive 2 — Collection & post-processing

**KHMDHS fetching** (`fetch_kimdis_procurements.py`): POST
`/contract?page=N` with `{cpvItems, dateFrom, dateTo}` — they query **by
CPV + date window** (max 180 days per window, paginated via `totalPages`),
where we query by exact `referenceNumber`. 19 primary CPVs (fire
suppression, tree pruning, fire-prevention works) plus ~55 broad secondary
CPVs kept only when the title matches fire keywords (πυροπροστασ,
αντιπυρικ, κατασβεσ, αεροπυροσβ…); a token-prefix exclusion list drops
hospitals/schools/reforestation. Retry policy `min(5·2^(n-1), 120)s`, max
8, honours `Retry-After` — same registry behavior we see. A **backup JSON
is written after every window** so a crash never loses a fetched batch.

**Diavgeia relevance filter** (`filter_relevance.py`): ~35 normalized
substring keywords (accent-stripped, ς→σ) matched against subject OR the
full PDF text. The list includes some very loose terms (`Προϋπολογισμού`,
`ΜΙΣΘΩΣΗ ΜΗΧΑΝΗΜΑΤΟΣ ΕΡΓΟΥ`) — confirming their own stated false-positive
limitation. Our per-contract PDF verification is the opposite trade.

**Amount validation** (`validate_diavgeia_amounts.py`): for each decision,
check whether the recorded amount literally appears in the PDF text —
exact substring, then digit-only comparison of amount-shaped tokens
(regex `\d{1,3}([.,\s]\d{3})+[.,]\d{2}`), then a permissive
spacing-tolerant regex. **No numeric tolerance and no auto-correction** —
mismatches are only flagged; their TODO list has a "manual amount-override
registry (ADA → corrected, with reason)" which is exactly our
`payment_corrections.json`, already built. They also auto-flag suspicious
direct awards: municipal «απευθείας ανάθεση» decisions ≥ €300k.

**Backfill pattern**: a dozen `scripts/backfill_*.py`, all dry-run by
default with `--apply`, batched `execute_values`, keyed by ADA/ΑΦΜ/ref —
tidy way to evolve a live DB; our equivalent is regenerating tables from
curated JSON, which is simpler and fine at our scale.

## Deep dive 3 — How they locate things

**Work-site extraction** (`locate_work.py`) — their most sophisticated
pipeline:
1. Contract PDF from the same KHMDHS attachment endpoint we use (same 429
   handling), **first 10 pages only**;
2. native text via `natural_pdf`, per-page OCR fallback
   (`pdf2image` + `pytesseract lang="ell+eng"`) only when a page is empty;
3. chunked (18k chars) into OpenAI **gpt-5-mini** with a strict JSON
   schema; the Greek prompt extracts only fire-protection work sites and
   **explicitly forbids the LLM from guessing coordinates** (`lat/lon`
   must be null) — geocoding is a separate deterministic step;
4. dedup by canonical-name/work-token overlap, then **Google Geocoding**
   (`region=gr`, "<canonical>, Ελλάδα"), then post-geocode dedup on
   6-decimal-rounded coordinates;
5. `DELETE`-then-`INSERT` into `public.works` with `page` + `excerpt` kept
   for auditability — every point can be traced back to the PDF passage;
6. fallback when the PDF yields nothing: re-run the extraction over the
   procurement title + short descriptions.

The separation LLM-extracts-names / API-geocodes / excerpts-preserved is
the right design if we ever go below Π.Ε. resolution. Cost controls (page
cap, cheap model, OCR-only-when-needed, state file of processed refs) are
all worth copying.

**Municipality mapping**: fires are joined spatially — everything
reprojected to **EPSG:2100** (Greek Grid), polygon → max-overlap
municipality with an `overlap_ratio` recorded, centroid fallback flagged by
`match_method`. Contracts are mapped by a multi-tier entity resolver
(exact org name → normalized → alias candidates stripping ΔΗΜΟΥ/ΔΗΜΟΣ →
ΑΦΜ priority), plus a hardcoded ~48-entry dictionary of colloquial→
Kallikratis names (ΛΙΒΑΔΕΙΑΣ→ΛΕΒΑΔΕΩΝ, ΘΗΒΑΣ→ΘΗΒΑΙΩΝ) — the same
"hand-curate what heuristics can't" philosophy as our
`city_to_pe.json`/`contract_regions.json`.

**GEMI lookups — important for us.** They query GEMI **anonymously with no
API key**: POST `https://publicity.businessportal.gr/api/search` with
`token: null` (browser-mimic headers), match the hit by exact ΑΦΜ, then
POST `/api/company/details` by GEMI number — retrieving the full public
profile **including the registered address**, management, KADs and status.
Results are cached in `beneficiary.gemi` (with `-1` as a "not found"
sentinel so misses aren't re-queried), backfilled by a rate-limited
dry-run-default script, and the frontend links each beneficiary to
`publicity.businessportal.gr/company/{gemi}`. Our notes had the publicity
portal down as reCAPTCHA-gated per query; their code suggests the *JSON
API behind it* accepts token-less requests. **Worth verifying** — if it
holds, it's an anonymous second source (with GEMI numbers and richer
addresses than VIES) for our contractor-location pipeline, still
consistent with the no-target-notification constraint.

## Deep dive 4 — Frontend & product

**Rendering**: no Leaflet/MapLibre/chart library — everything is
hand-built **d3 SVG**. The choropleth uses `geoMercator().fitExtent` +
`geoPath` with a power color scale (exponent 0.3), and terrain comes from
**MapTiler hillshade raster tiles manually projected** as SVG `<image>`
overlays. `SituationMap` layers EFFIS burn polygons + FIRMS detections +
incident markers on the same projection with hover-sync to the news
ticker. (Our Leaflet flow map is simpler but fine; the hillshade trick
would make our print exports notably better-looking.)

**Data loading**: every view calls a Postgres RPC; a two-tier cache
(memory + versioned localStorage, 60s TTL, 6h stale-while-revalidate,
retry with backoff, `validateData` guards) fronts the homepage; Supabase
**realtime subscriptions** on `current_fires`/`112_notice` push live
updates. Pages are lazy-loaded routes with Greek loading/error cards and
an ErrorBoundary.

**Product touches worth stealing**:
- **Direct-award histogram annotated with the legal thresholds**
  (ν.4782/2021 €30k/€60k ceilings) — turns a distribution into an
  accusation-shaped chart; we have direct-assignment percentages but never
  show the value distribution against the legal limits.
- **Document linking**: regex-extract the SYMV ΑΔΑΜ and link the real
  KHMDHS attachment; ΑΔΑ → `diavgeia.gov.gr/doc/{ada}` (we do this
  already, with caching on top).
- **Print view**: `contractPdf.ts` opens a styled A4 popup and
  auto-`print()`s — a "contract dossier" export with zero backend work.
- **Search**: Greeklish→Greek keyboard transliteration + accent/ς
  normalization + ranked prefix matching. Our search normalizes accents
  but not Greeklish.
- **Permalinks**: all filter state in query params (`?municipality=…`) —
  shareable views. Our `/map?target=` does this partially.
- **SEO/discoverability**: prerendered static content inside `#root`
  before hydration, OG/Twitter meta, `sitemap.xml`, `robots.txt`, and an
  **`llms.txt`** for AI crawlers; consent-gated analytics.
- **Municipality profiles** with KPI "signal bars" and per-year
  cumulative spending curves.

**Deployment reality check**: Vercel hosting; the *hourly* workflows are
only the live-fire/112 scrapes and the nightly open-data export — the main
Diavgeia/KHMDHS `daily-fetch.yml` schedule is **commented out** (manual
dispatch only). So the "daily automated procurement refresh" is currently
semi-manual there too. Automation is still their strength, but the gap
between us is smaller than the methodology doc implies.

---

## What FireWatch does better than us

1. **Continuous ingestion machinery.** Incremental window fetches with
   state checkpoints, per-window backup JSON, auto-committed artifacts,
   scheduled scrapes. Our SQLite is a manually refreshed snapshot.
2. **Open-ended discovery.** CPV-driven KHMDHS querying finds contracts
   nobody curated in advance; our seed was a fixed xlsx + targeted
   Diavgeia sweeps.
3. **Live geographic context.** EFFIS burn polygons spatially joined to
   municipalities (EPSG:2100, overlap ratios), NASA FIRMS, live incidents,
   112 alerts, geocoded news with map hover-sync.
4. **Point-level work-site geocoding** with a well-engineered
   LLM-extract / API-geocode / excerpt-audit pipeline (see deep dive 3).
5. **Entity resolution at national scale**: name-variant tables keyed by
   deterministic hashes, ΑΦΜ-priority matching, authority-scope
   classification — needed for 300+ authorities.
6. **Production web architecture**: server-side RPC aggregation, caching,
   realtime, lazy routes, SEO (llms.txt!), consent-gated analytics,
   open-data CSV exports with row-count validation.
7. **Process hygiene**: committed `DATA_CLEANING_DECISIONS.md`;
   dry-run-default backfill scripts; automated registry-vs-PDF amount
   flagging incl. the ≥€300k municipal direct-award tripwire.

## What we do better than FireWatch

1. **Payment-order ground truth.** Their `payment` is one row per
   contract; ours is per ##PAY order with dates, credits, cancellations
   and chain attribution. They can't show paid-vs-contracted gaps or
   disbursement over time; effective values are our core metric.
2. **Corrected amounts, not just flagged.** Their validator only flags
   mismatches and their TODO wishes for a manual override registry — we
   have it (`payment_corrections.json`, PDF-cited) plus the family-level
   outlier guard test.
3. **Bidirectional KHMDHS↔Diavgeia reconciliation** (PAY-ΑΔΑΜ stamps,
   «ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ», amount+chain twin-matching, Diavgeia-only
   payments). Their `diavgeia_procurement` bridge links documents; it
   doesn't prove payment-total completeness.
4. **Scope precision.** Per-contract PDF verification vs keyword/CPV
   filters whose false positives they acknowledge (`Προϋπολογισμού` as a
   relevance keyword!). Our supersede semantics also handle additive
   ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ contracts — their zeroing logic would hide the parent —
   and umbrella (ΤΑΙΠΕΔ/ΕΕΣΥΠ) double-counting, and our chains are
   fetched to closure immediately rather than self-healing on a later run.
5. **Contractor-origin analysis.** VIES home locations, consortium
   resolution with documented inferences, contractor→project-region flow
   map. They locate the *work*; we also locate the *winner* — the
   money-geography axis doesn't exist in FireWatch.
6. **Single-source-of-truth factoring.** Our scope/supersede logic lives
   in one table built by one loader; theirs is duplicated across Python
   ingest and ~10 RPC functions.
7. **Honest unknowns** (`unresolved` with reasons) rather than best-guess
   geocodes.

## What we should adopt (prioritized)

1. **Registry-vs-PDF amount validator.** We already cache payment PDFs and
   run `pdftotext`. Add their digit-string matching (exact substring →
   digit-only token comparison → spacing-tolerant regex) over
   `amount_with_vat` vs the PDF, emitting *candidates* for
   `payment_corrections.json`. Catches small keying errors below our 150%
   outlier-test threshold.
2. **GEMI publicity API as a second anonymous source** — verify their
   token-less `publicity.businessportal.gr/api/search` + `/api/company/
   details` flow actually works; if yes, use it to fill our remaining
   unresolved contractors and add GEMI-profile links to contractor pages.
   Cache with a `-1`-style "not found" sentinel to avoid re-querying.
3. **Incremental refresh command.** `khmdhs.refresh` with a state file:
   refetch non-closed in-scope contracts for new `paymentRefNo`/amendments
   → standard loader chain. Copy their per-window backup-JSON safety net.
   III/IV/2026 are still disbursing; our numbers age.
4. **EFFIS burned-area overlay on the flow map.** Their EPSG:2100
   max-overlap spatial join is the template; restoration/ΕΣΑ contracts vs
   actual burn perimeters (Evia!) is the strongest OSINT angle we lack.
5. **CPV completeness sweep.** Query KHMDHS by fire-relevant CPVs
   restricted to ΥΠΕΝ + our three fund codes and diff against our 331
   contracts — a cheap independent test of our discovery net.
6. **Sub-Π.Ε. work sites.** Their extract/geocode/excerpt pipeline is the
   engineering model, but at our ~250-contract scale, curate the
   Δασαρχεία/τμήματα into `contract_regions.json` notes per our
   manual-curation constraint; keep their idea of storing the PDF page +
   excerpt as evidence.
7. **UI upgrades**, in order of value: cumulative-disbursement time series
   per phase (we already store payment dates); a direct-award value
   histogram annotated with the ν.4782/2021 thresholds; Greeklish
   transliteration in search; permalink-able filters; a print-dossier
   view per contract (their zero-backend popup-print trick); MapTiler
   hillshade under the flow map for print exports.
8. **`DATA_DECISIONS.md` audit log** — consolidate the decisions currently
   scattered across JSON `reason` fields, commit messages and CLAUDE.md
   into one append-only, citable log.

## Verdict

Complementary projects, and — given their reforestation exclusions —
barely overlapping datasets. FireWatch's strengths are machinery: continuous
collection, entity resolution at national scale, live fire layers, and a
production-grade frontend. Ours are evidentiary: actual disbursements,
corrected amounts, per-contract PDF verification, chain closure, and
contractor-origin analysis. The imports that would move us furthest are the
amount validator, the anonymous GEMI channel (pending verification), an
incremental refresh loop, and the EFFIS burn-perimeter overlay — while
keeping the thing they structurally can't afford at their scale:
per-record verification against the signed documents.
