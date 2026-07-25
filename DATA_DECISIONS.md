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
