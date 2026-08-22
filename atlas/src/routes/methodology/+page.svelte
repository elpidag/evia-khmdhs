<script lang="ts">
	import { page } from '$app/state';
	import { eurShort, grInt } from '$lib/transforms/format';
	const meta = $derived(page.data.meta);
	// dataset-state counts are computed by the API (meta.facts) so this
	// prose can never go stale against the data; '—' when a layer is absent
	const f = $derived(meta?.facts ?? {});
	const nKh = $derived(meta?.antinero?.n_contracts);
	const nDase = $derived(meta?.dase?.n_contracts);
	const show = (v: number | undefined) => (v === undefined ? '—' : grInt(v));
</script>

<svelte:head>
	<title>Methodology — how these numbers are made</title>
	<meta
		name="description"
		content="Definitions, conventions and honest limitations behind the Atlas datasets: stated-value basis, even-split attribution, deduplication, entity keying."
	/>
</svelte:head>

<article>
	<hgroup>
		<h1>How these numbers are made</h1>
		<p class="standfirst">
			Every chart on this site carries a one-line caveat linking here. This page holds the full
			definitions, the conventions, and the honest limitations.
		</p>
	</hgroup>

	<h2 id="sources">Sources</h2>
	<p>
		The single primary source is <strong>ΚΗΜΔΗΣ</strong> (Central Electronic Registry of Public
		Contracts) open data, enriched with <strong>Διαύγεια</strong> clearance decisions,
		<strong>VIES</strong> and the <strong>ΓΕΜΗ</strong> publicity registry for contractor
		locations, and the geodata.gov.gr Kallikratis administrative boundaries (CC-BY). Every
		contract and payment page deep-links to the signed PDF, served through a local cache. No
		source that notifies the data subject is ever queried.
	</p>

	<h2 id="net-basis">Everything is net of ΦΠΑ</h2>
	<p>
		Every € on this site — KPIs, charts, maps, tables — is <strong>excl. VAT (net)</strong>,
		read directly from the registry's net columns (ΚΗΜΔΗΣ stores both bases for contracts and
		for payment orders; nothing is divided by a VAT rate — {show(f['dase_mixed_vat'])} ΔΑΣΕ
		contracts blend 0%/13%/24% line items, so a flat conversion would be wrong). This is also the basis the law uses: the
		ν.4412/2016 εκτιμώμενη αξία — and therefore the €30k/€60k direct-award ceilings — is
		defined χωρίς ΦΠΑ, so net values compare against those thresholds correctly. Every figure on
		the site is net, detail pages included — a second gross number beside each net one only
		made two bases to keep straight (user, 2026-08-19). Five
		Diavgeia-only clearance payments carried no net amount in any registry; their net figures
		were extracted from the signed PDFs («ΚΑΘΑΡΗ ΑΞΙΑ ΠΑΡΑΣΤΑΤΙΚΟΥ») and recorded as curated
		corrections with excerpt evidence.
	</p>

	<h2 id="stated-basis">Stated values are the analytic basis</h2>
	<p>
		Every chart, map and aggregate uses the <strong>stated contract value</strong> (net of
		ΦΠΑ) — the amount written in the signed contract — even when payment orders exist. This
		keeps all three datasets on one comparable basis. Payments are shown as their own
		explicitly-labelled layer: the «actually paid» KPI, the payment-orders timeline, the
		cumulative disbursement curves and each contract's payment list, with payments attributed
		to a superseded contract's final version along the amendment chain. Where a payment
		history diverges from the stated value (partial delivery, price revisions), both numbers
		are visible side by side on the contract page.
	</p>

	<h2 id="antinero">What counts as Anti-nero</h2>
	<p>
		A contract enters the Anti-nero analytics only with positive evidence of programme
		membership: an ANTINERO phase named in its registry title, one of the programme's ΠΔΕ
		fund codes in its funding metadata, or its signed PDF declaring membership in RRF Action
		16849 — amendments inherit the evidence of the contract they modify. Programme-management
		umbrella contracts (ΤΑΙΠΕΔ/ΕΕΣΥΠ pass-throughs) and support services are stored but never
		aggregated, so no euro is counted twice. Superseded contract versions along an amendment
		chain count once, at the chain's final version.
	</p>
	<p>
		One tier is deliberately excluded from every calculation: {show(f['kh_probable_n'])}
		contract chains ({f['kh_probable_eur'] !== undefined ? eurShort(f['kh_probable_eur']) : '—'}
		stated, excl. VAT) whose registry titles
		brand them ANTINERO II but whose signed documents carry <strong>no provable RRF-16849
		financing evidence</strong> — no fund code in the registry metadata, and full contract
		texts with no Ταμείο Ανάκαμψης, no Δράση ID, not even the word ANTINERO in the body.
		These early-2022 deeds were procured through ΤΑΙΠΕΔ and funded via an ΥΠΕΝ budget line
		(ΚΑΕ 2910601001), so they are <em>probably</em> part of the programme — but probability
		is not proof, so they are presented as additional contracts found, probably related to
		the Antinero programme, and not included in the calculations. They remain in the dataset
		with reachable detail pages, listed on the <a href="/">front page</a>.
	</p>

	<h2 id="payment-dates">Payment dates</h2>
	<p>
		The registry carries payment signature dates in two formats, and some orders carry none.
		Where the signature date is missing, the registry <em>submission</em> date is used and the
		affected count is stated on the chart. Truly undated orders are shown in a separate bucket,
		never silently dropped.
	</p>

	<h2 id="even-split">Even-split attribution</h2>
	<p>
		Many contracts cover more than one regional unit, and a contract may also name several
		forest services or be signed by several firms. The documents we hold state
		<strong>no allocation of the money</strong> between the units a contract covers — a
		contract for works in three regional units states one price, not three — so for every
		aggregate view its value is <strong>split equally</strong> between its regions (and its
		authorities, and its partners). Maps, flow arrows, sankeys and per-region charts are sums
		of those equal shares and add up exactly to the programme total, with nothing counted
		twice. We do not show a «whole value per region» figure anywhere, because a contract's
		whole value was not spent in each region it covers.
	</p>

	<h2 id="joint-contracts">Contracts signed by more than one party</h2>
	<p>
		A jointly signed contract is <strong>split evenly between its partners</strong>, on both
		datasets, on every per-contractor surface: the ranking, the contractor list, and each
		company's own page (whose contract row shows the contract's own value beside this partner's
		share). Whole cents are allocated, so per-company totals add up to the programme total
		exactly — the ranking and the headline are the same money.
	</p>
	<p>
		Equal parts is what the documents support and nothing more. No contract in either dataset
		states a <span lang="el">«ποσοστό συμμετοχής»</span>; the consortium articles bind the
		members <span lang="el">«ενιαία, αδιαίρετα, αλληλέγγυα»</span> — jointly and indivisibly —
		and ΓΕΜΗ publishes members' shares for none of them. Until 20.08.2026 the Anti-nero side
		instead counted such a contract in full for each partner, which put the sum of the
		per-company totals well above the programme's own total; that convention is retired.
	</p>
	<p>
		Most joint ventures never reach that rule, because they sign as a
		<span lang="el">κοινοπραξία</span> that holds its own ΑΦΜ, seat and ΓΕΜΗ registration: the
		contracting party is one entity and the contract is counted once, for it. Where the registry
		instead keyed the venture's <em>members</em> as the parties, the signed contract's own
		preamble was read and the party corrected — each such correction is listed on the contract's
		page with the sentence it came from.
	</p>
	<h2 id="member-firms">Who is behind a joint venture</h2>
	<p>
		Counting the party that signed leaves the firms inside a
		<span lang="el">κοινοπραξία</span> invisible, so the company ranking offers a second view:
		<strong>by member firm</strong>. It is the same population and the same total, with one
		substitution — a venture whose membership is on record is replaced by its members and its €
		divided evenly between them. Nothing else moves, and both views add up to the programme
		total.
	</p>
	<p>
		Membership is <strong>curated from documents, one venture at a time</strong>. The strong
		evidence is a sentence that lists the members —
		<span lang="el">«αποτελούμενη από α) … ΑΦΜ … και β) … ΑΦΜ …»</span> — in the contract itself
		or in the award decision; a firm identified only because the venture is named after it, or
		because it was invited to the same competition, is <em>not</em> recorded as a member. Two
		traps are handled explicitly and were both caught in review: the person signing for a member
		company is not a third member, and another joint venture of the same firms is not a member
		either. Where no document names the members, the venture keeps its own row and the page says
		so, rather than the name being taken as proof.
	</p>

	<h2 id="procedures">Procedures and thresholds</h2>
	<p>
		Direct-award shares are computed from the registry's procedure field. The ν.4782/2021
		ceilings (€30k supplies/services, €60k works) are printed on value distributions for scale —
		both the ceilings and the plotted values are excl. VAT, the basis the law defines them on.
		RRF emergency provisions allowed direct awards far above them, which is precisely the
		finding, not a claim of illegality.
	</p>

	<h2 id="study-costs">Μελέτη (study) costs</h2>
	<p>
		Extracted from the signed PDFs at the «Κόστος εκπόνησης μελετών (ΣΑΥ-ΦΑΥ)» anchor, net of
		VAT, human-verified with page and excerpt evidence. Where a contract states the figure
		twice, the contracted breakdown wins over the tender estimate. ΕΣΑ design-build contracts
		bundle the study into the works price and honestly state none.
	</p>

	<h2 id="categories">Work-type categories</h2>
	<p>
		Every in-scope contract carries exactly one curated work-type category, assigned from the
		descriptive project title inside its signed PDF (a different, richer text than the
		registry's 100-character shorthand) with the contract's rarer CPV codes as tie-breaker.
		Specific work beats the generic boilerplate: a title naming μικτές αντιπυρικές ζώνες,
		αρχαιολογικούς χώρους, υλοτομίες or δεξαμενές wins over the standard καθαρισμός phrasing,
		while amendments and ΑΠΕ approvals inherit their parent contract's title and category.
		Because each contract counts once, the category sums reconcile to the programme's
		stated-net total. The verbatim titles are stored in the dataset as the evidence; the
		taxonomy and every assignment are documented in the decision log (2026-08-14).
	</p>

	<h2 id="record-kinds">What a ΚΗΜΔΗΣ σύμβαση record is</h2>
	<p>
		ΥΠΕΝ files several kinds of act in the contracts register, all of them as
		<em>συμβάσεις</em> with a ΣΥΜΒ ΑΔΑΜ: the contract itself, later revisions of
		its terms, supplementary contracts for additional works, and the ministry
		decisions approving those or extending a deadline. The registry's own type
		field cannot tell them apart — it carries the ν.4412 object category
		(«Έργα» / «Υπηρεσίες»), which reads the same on all of them — so each
		record is classified from the wording of its own signed document, and that
		wording is kept verbatim beside the label on the contract page.
	</p>
	<p>
		The {show(nKh)} in-scope records are
		<strong>{show(f['kh_doc_contract'])} original contracts</strong>,
		{show(f['kh_doc_amendment'])} revisions of terms (which never change the
		price — verified against every one of them),
		{show((f['kh_doc_supplementary_contract'] ?? 0) +
			(f['kh_doc_approval_ape_supplementary'] ?? 0))} supplementary works —
		{show(f['kh_doc_supplementary_contract'])} posted as the supplementary
		contract itself and {show(f['kh_doc_approval_ape_supplementary'])} as the
		ministry decision approving one — and
		{show(f['kh_doc_approval_schedule_extension'])} deadline extensions, which
		change no money at all. Where a later record restates the whole contract it
		replaces the earlier version in every total; where it carries only the
		additional works, both count. Either way each euro is counted once.
	</p>

	<h2 id="contract-timeline">The timeline on a contract page</h2>
	<p>
		The bar is <strong>the time the contract was given</strong>: from the day it
		was signed to the deadline it announced, with a lighter stretch for each
		extension of that deadline — the same reading as the sponsored-works
		timeline, where a bar is a promise and the mark beside it is what happened.
		It is deliberately not drawn from signature to the completion act: that
		measures when the paperwork closed, and a project accepted years after it
		finished would look like a project that ran for years.
	</p>
	<p>
		What was announced is read from the <strong>signed contract itself</strong>,
		not from the register: «Η συνολική προθεσμία … ορίζεται σε τρεις (3) μήνες
		από την έναρξη των εργασιών». {show(f['kh_deadline_document'])} of the
		{show(nKh)} in-scope contracts state a deadline that way and every one of
		them also states the clock it starts on — the day of signature, or the day
		the works begin — which the register never records. The remaining
		{show(f['kh_deadline_document_season'])} answer with a season instead: their
		works run within the fire season, 1 May to 31 October, so their deadline is
		the 31 October of the year they name.
	</p>
	<p>
		The ΚΗΜΔΗΣ duration field is kept beside it as the cross-check, and it does
		not survive the comparison: it carries a number for 83 contracts, never says
		what that number counts, and <strong>agrees with the signed text in 3 of the
		65 cases where both exist</strong> — 44 of its figures are bare numbers with
		no unit at all, against a document that says «τρεις (3) μήνες». Where the two
		differ the contract page shows both and quotes the sentence.
	</p>
	<p>
		{show(f['kh_deadline_ext_chains'])} contracts had that deadline moved, in
		{show(f['kh_deadline_ext_steps'])} steps — the «Έγκριση (τμηματικής) παράτασης»
		approvals ΥΠΕΝ publishes on Diavgeia (see below), the «Παράταση προθεσμίας»
		records of ΚΗΜΔΗΣ and the supplementary approvals that carried a later end date
		with them; an act re-stating a record's deadline is one step, not two, and an
		act granting different dates per area is marked as such (the latest date is
		drawn); the chart labels which. On the same line the timeline marks every later act on the
		contract, every payment order (€), the acceptance of the works (✔) where a
		Diavgeia act records one — {show(f['kh_done'])} contracts — and, before the
		signature, the procurement that produced it: the primary request, the
		commitment approval, the call and the award, wherever the register dates them.
	</p>

	<h2 id="procurement-families">Procurement families (which contracts answer the same call)</h2>
	<p>
		The registry's own chain declares any upstream act for only {show(f['kh_family_declared'])} of the
		{show(nKh)} in-scope contracts, and a call (πρόσκληση) for {show(f['kh_notice'])} — a ΣΥΜΒ record
		carries the links its own payload declared, and most were posted with none. So the call each
		contract answers is read from the contract's <em>own signed text</em>, which recites the
		πρόσκληση / διακήρυξη ΑΔΑΜ it was awarded under: {show(f['kh_family_contracts'])} contracts
		resolve to {show(f['kh_family_calls'])} calls this way, and amendments inherit their
		predecessor's call. {show(f['kh_family_none'])} contracts cite none — direct awards and
		negotiations publish no call, and nothing is inferred for them.
	</p>
	<p>
		On the programme chart the drawn unit is therefore the call, not the contract: one star per
		πρόσκληση that produced more than one contract, the largest lot at its centre. The only
		relation that crosses a family is a contractor holding lots under two different calls, drawn
		as a dashed link. Contracting authority and Π.Ε. are deliberately <em>not</em> drawn as
		links: the framework lots each name five to fourteen Δασαρχεία, so authority collapses
		almost the whole programme into a single blob, and sharing a region is a coordinate, not a
		relationship.
	</p>

	<h2 id="map-layers">What the maps are drawn from</h2>
	<p>
		Greek boundaries are the geodata.gov.gr «Όρια Δήμων Καλλικράτη» municipality layer (CC-BY),
		dissolved into the 74 regional units. The land AROUND Greece is scenery — it carries no data
		and cannot be clicked — from the Eurostat GISCO 1:1M country boundaries («© EuroGeographics
		for the administrative boundaries»). The Athos peninsula is drawn from the official «Άθως»
		polygon of the same geodata.gov.gr Kallikratis layer (CC-BY), whose coastline is refined
		with OpenStreetMap («© OpenStreetMap contributors») because the official outline is a
		63-point generalisation up to 734 m from the shore. Άγιον Όρος is a self-governed monastic
		state and belongs to no municipality, which is why it is missing from the dissolved regional
		units — and from Eurostat's own «Chalkidiki» — so it carries no data and is drawn as land
		outside the programme's units. The dashed line on the northern maps is Greece's land
		border, cut from the same dissolved regional-unit outline — the stretch that runs along a
		neighbour rather than along the sea.
		Burn scars are EFFIS (© European Union, Copernicus EMS) and the shaded relief on the fires
		map is Copernicus WorldDEM-30, both credited in their own frames.
	</p>

	<h2 id="pe-vocabulary">Regions (Π.Ε.)</h2>
	<p>
		All geography keys on the 74 Kallikratis regional units (περιφερειακές ενότητες), with
		spelling variants collapsed onto canonical names. Anti-nero work regions are hand-curated
		per contract from titles, forest authorities and the PDFs; amendments inherit from the
		version they supersede.
	</p>

	<h2 id="geocoding">Contractor locations</h2>
	<p>
		Each contractor's registered office is read from the party clause of its own signed contract
		(«…που εδρεύει στ… επί της οδού …, αρ. …, Τ.Κ. …»), chain-read across the contract's versions,
		with the verbatim sentence kept as evidence on the contractor page; VIES and the ΓΕΜΗ
		publicity registry are the cross-check, and where the register or the company's own site
		shows a later move the current seat is drawn and the contract's seat is noted. A joint
		venture's seat is never inferred from a member's. Coordinates come from OSM Nominatim,
		accepted only when the hit validates against the stated postcode or regional unit and names
		the street; every point says how it was placed (at the street number / on the named street /
		at the centre of the settlement the document names) — kilometre markers, rural localities and
		streets OSM lacks stay at the settlement centre, drawn dashed, never fabricated.
	</p>

	<h2 id="lifecycle">Deadline extensions (Diavgeia)</h2>
	<p>
		ΚΗΜΔΗΣ carries a deadline extension only when ΥΠΕΝ re-posts it as a contract record; the
		approvals themselves are published on Diavgeia with the contract ΑΔΑΜ in the subject. We
		harvest every «Έγκριση (τμηματικής) παράτασης» act citing a stored contract and read the new
		deadline from the act's operative part («Αποφασίζουμε … μέχρι τις DD.MM.YYYY»), keeping the
		verbatim clause; an act granting different dates per area is flagged as such and all dates are
		kept; an act the extractor cannot read is listed with its reason and no date, never a guessed
		one. These rows appear in each contract's document trail. A «τμηματική παράταση» extends one
		τμηματική προθεσμία — most often the works in one forest service's area — so where the acts
		name the service, the contract's timeline splits the bar's extended (lighter) part into one
		strip per service, named at its end, with the steps that name it and a ✔ only where ΥΠΕΝ
		accepted that part on its own («για το τμήμα περιοχής ευθύνης Δασαρχείου …»); acts that name
		no area, or a service the registry does not know, sit on a strip of their own and are never
		assigned. The same inventory found no act
		dissolving, terminating or cancelling an Anti-nero contract; revocation acts on Diavgeia revoke
		an earlier approval, not a contract.
	</p>

	<h2 id="authorities">Forest authorities</h2>
	<p>
		A curated registry of {show(f['n_authorities'])} Διευθύνσεις Δασών and Δασαρχεία (names, genitive aliases, seat
		coordinates). Anti-nero contracts link to authorities via title/items matching with
		PDF-verified overrides; three region-scoped contracts genuinely name none. The ΔΑΣΕ side of
		an authority's page matches the awarding unit's folded name against the registry aliases —
		the same matcher that resolves ΔΑΣΕ regions.
	</p>

	<h2 id="dase-dedup">ΔΑΣΕ population</h2>
	<p>
		The ΔΑΣΕ dataset holds every public contract since September 2021 whose contractor is a
		forest labour co-operative (ν.4423/2016), harvested contractor-first (CPV-first provably
		misses). Aggregates use <strong>stated values excl. VAT, deduplicated</strong>: cancelled
		rows and superseded versions are excluded, leaving {show(nDase)} live contracts. Payment orders
		and the full procurement family (αίτημα → διακήρυξη → κατακύρωση) have been harvested from
		the registry's chain, but the registry posts payments for only part of the population
		(2022–23 are near-blank as registry practice) — so charts and rankings stay on stated
		values, and the «actually paid» figure appears only as a KPI with its coverage printed.
	</p>

	<h2 id="canonical-vat">Canonical ΑΦΜ (ΔΑΣΕ)</h2>
	<p>
		The registry spells the same co-op up to {show(f['dase_max_variants'])} ways, sometimes with whitespace or glued text
		around the ΑΦΜ. Co-ops are merged on the canonical ΑΦΜ (first 8–9-digit run, zero-padded);
		display names come from the curated co-op review file.
	</p>

	<h2 id="org-names">Awarding bodies</h2>
	<p>
		Awarders group by normalised <em>name</em>, never by VAT: ΑΦΜ 090273987 appears under both
		ΥΠΕΝ and the Decentralised Administration of Thessaly–Central Greece, and leading zeros get
		lost in the registry.
	</p>

	<h2 id="dase-regions">ΔΑΣΕ regions</h2>
	<p>
		Each ΔΑΣΕ contract's regional unit derives from its awarding forest unit (registry-matched,
		plus a curated file for generic unit names and per-contract overrides for supra-regional
		awarders, each with documented evidence). Coverage is 99.8%; four ΑΔΜΗΕ power-line
		contracts span multiple units and stay honestly unresolved.
	</p>

	<h2 id="dase-cpv-noise">The insurance CPV on logging contracts</h2>
	<p>
		{show(f['dase_cpv_noise'])} live ΔΑΣΕ logging contracts carry the insurance CPV 66519300-4
		(«επικουρικές ασφαλιστικές υπηρεσίες»). This is not a keying error — and not insurance
		procurement. The ministerial decisions that set the assignment prices for logging works
		state that the prices do not include the employer's ΕΦΚΑ contribution for the forest
		workers; that contribution burdens the forest's exploiter, which for public forests worked
		by the co-ops is the State (ΚΥΑ ΥΠΕΝ/ΔΔΔ/128526/4106/2022 · άρθρο 137 §3 ν.δ. 86/1969).
		Each award therefore itemises an «ασφαλιστικές/εργοδοτικές εισφορές (ΕΦΚΑ εργοδότη)» line
		on top of the works, and in the registry records the insurance CPV sits exactly on that
		line. The code stays flagged wherever CPVs are shown so the mix is never read as insurance
		services: these are logging contracts whose price also funds the workers' social-insurance
		contributions.
	</p>
	<p>
		The same structure decides what «paid» means on these pages. One payment warrant (χρηματικό
		ένταλμα) disburses both components — the co-op's work price and the state-borne ΕΦΚΑ — but
		the registry's payment records were often keyed with only the work component. Because the
		stated contract values include the ΕΦΚΑ lines, the paid figures follow the same convention:
		where a payment's own warrant documents a larger total than the record states, the curated
		correction raises the record to the warrant (each correction cites the warrant amount; where
		the document does not print the net, it is derived from the contract's own component ratio
		and says so). Paid and stated are therefore compared on one definition: the full public
		disbursement.
	</p>

	<h2 id="zero-overlap">The zero-overlap finding</h2>
	<p>
		No ΑΦΜ appears in both datasets — checked on raw and canonicalised ΑΦΜ in both directions.
		The two programmes reach disjoint sets of companies; the only shared institution among
		in-scope Anti-nero awarders is ΥΠΕΝ itself. One caveat: a registry keying error lists an
		unrelated firm under an awarder's ΑΦΜ on the ΔΑΣΕ side; entity comparisons therefore never
		key on awarder VATs.
	</p>

	<h2 id="compare-bases">Comparing the two datasets</h2>
	<p>
		Both sides of /compare use the same basis: stated contract values, excl. VAT (ΔΑΣΕ
		deduplicated across amendment versions). The populations still differ: one is a single
		programme, the other is a whole sector of the co-operative economy.
	</p>

	<h2 id="anadohoi">Ανάδοχοι αναδάσωσης / αποκατάστασης</h2>
	<p>
		The sponsor dataset covers the ν.998/1979 άρθρο 42§3 scheme: private companies appointed
		by ministerial act to fund and execute forest restoration at their own expense. No
		procurement takes place, so nothing exists in ΚΗΜΔΗΣ — the universe is Διαύγεια acts
		(seed lists + a subject sweep across all issuing organisations + a crawl of every ΑΔΑ
		cited in the acts' recitals). Diavgeia metadata for these acts is empty of substance, so
		every value — company, funder, area, budget, deadlines, the fire each act responds to —
		is extracted from the signed PDF and backed by a verbatim excerpt shown on the project
		page. Statuses are derived, never asserted: <em>completed</em> requires a posted
		completion act; <em>no completion recorded</em> means the deadline passed and nothing
		was filed — which is not proof of abandonment, but the act is the legal proof of
		delivery. Budgets are stored only when an act states one; many sponsors commit to
		«whatever it costs» with no figure, and those stay honestly blank. The VAT basis of each
		stated budget is curated from the act's own text: {show(f['ana_vat_net'])} acts say
		«άνευ/χωρίς ΦΠΑ», {show(f['ana_vat_gross'])} state
		a gross figure, and the rest write a bare number — the committed total prefers the net
		figure <em>where the act itself states one</em> (Lidl's act states both, so its net
		€241,936 is used) and never converts the silent ones.
	</p>
	<p>
		<strong>PROJECT SCOPE / PROJECT TYPE charts:</strong> the scope of each appointment
		(works only / study &amp; works / study only) is curated from each root designation
		act's operative sentence, with the verbatim excerpt on the project page; the charts
		count the live projects — a superseded restatement's act is reviewed but not shown
		there. The intervention type (restoration / reforestation / both) follows the act's
		own wording; one project's act states neither.
	</p>

	<h2 id="explore">The Explore table</h2>
	<p>
		An <strong>Anti-nero row is a contract, not a registry record</strong>. ΥΠΕΝ posts a
		later act on an existing contract under a new ΣΥΜΒ ΑΔΑΜ — a revision of terms, a
		deadline extension, an approval of supplementary works — so one contract can hold
		several records. The row carries the original σύμβαση's title, lists every record of
		the chain beneath it, spans «first act → last act» in the date column, links to the
		record holding the current state, and counts the money <em>once</em>. Citing any of
		the chain's ΑΔΑΜ finds it. ΔΑΣΕ and sponsor rows stay one row per record, which is
		what those datasets are.
	</p>
	<p>
		The combined table lists every Anti-nero contract, every live ΔΑΣΕ contract and every
		sponsor project on one basis: the <strong>stated value, net of ΦΠΑ</strong> (for sponsor
		projects, the committed budget after amendments — net where the act states it, often
		absent). «HQ region» is available only for Anti-nero contractors, whose registered
		seats are curated; procedure for sponsor projects is shown as «Πράξη αναδόχου (χορηγία)»
		because no procurement procedure exists. The «Διακήρυξη» filter uses the ΚΗΜΔΗΣ chain links: only {show(
			f['kh_notice']
		)} of
		{show(nKh)} in-scope Anti-nero contracts and {show(f['dase_notice'])} of {show(nDase)} live ΔΑΣΕ contracts have a linked
		διακήρυξη/πρόσκληση — the registry's
		chain knows only what each σύμβαση declared when posted, so «without» means <em>no
		linked notice in the registry</em>, not proof that none was ever published. The «End
		date» filter marks rows with a recorded project ending: an Anti-nero completion act
		found on Διαύγεια (οριστική παραλαβή / περαίωση — {show(f['kh_done'])} of {show(
			nKh
		)} contracts) or a completed
		sponsor project; «without» means no such act was found. ΔΑΣΕ rows stay outside this
		filter by an evidenced negative finding: probing 75 contracts found that ΔΑΣΕ awarders
		never cite the ΑΔΑΜ in Διαύγεια act subjects, and their παραλαβές are bundled municipal
		approvals that cannot be joined to individual contracts — so no ΔΑΣΕ ending is claimed
		rather than guessed. Filtering
		runs entirely in the browser; every filter state is a shareable URL.
	</p>

	<h2 id="arogi">Αρωγή πυροπλήκτων (state aid to fire victims)</h2>
	<p>
		The fourth dataset covers state aid for wildfires from 2021 onwards, on two independent
		sources. The Διαύγεια side is the ΓΔΑΕΦΚ per-building trail (repair permits, δόσεις,
		περαιώσεις): every act attributes to a fire by the fire <em>cited in its recitals</em>,
		never by its issue date — recent acts still serving pre-2021 fires are excluded and
		counted. Amounts come from the acts' own hash-delimited Σ.Σ. tables, accepted only when
		the total reconciles with the δωρεάν-αρωγή + δάνειο split. Rows group into cases only
		where follow-up acts cite the permit number; the rest stay honest single-act rows.
		<strong>Privacy: owners' names are never stored or displayed</strong> — the signed PDF on
		Διαύγεια remains the public record. The official side is the state's own payment
		announcements (stored as verbatim quotes with source URLs — Wayback snapshots where the
		original pages are gone) and the ΕΛΓΑ annual reports. The bases differ — Σ.Σ.
		<em>approved</em>, πρώτη αρωγή <em>paid</em>, ΠΔΕ <em>budgeted</em>, ΕΛΓΑ
		<em>compensation</em> — so the summary compares like with like and highlights gaps
		instead of merging them.
	</p>

	<h2 id="pdf-provenance">Documents</h2>
	<p>
		Every PDF link serves the signed document fetched once from ΚΗΜΔΗΣ and cached locally — the
		registry rate-limits bursts, so links never point at it directly. Payment pages link the
		Διαύγεια decision where one is matched, and sponsor-project pages serve the Διαύγεια
		decision PDFs through the same caching proxy.
	</p>

	<h2 id="freshness">Freshness &amp; reproducibility</h2>
	<p>
		Data as of {(meta?.generated ?? '').slice(0, 10) || 'the committed snapshot'} — refreshed by
		an incremental pipeline that refetches open contracts and re-runs every derivation. The
		databases, curation files and decision log (<code>DATA_DECISIONS.md</code>) are versioned
		together, so every number on this site is reproducible from the repository.
	</p>
</article>

<style>
	article {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
	}
	h2 {
		margin-top: var(--sp-8);
		scroll-margin-top: var(--sp-4);
	}
	p {
		font-size: var(--fs-15);
		line-height: 1.65;
	}
</style>
