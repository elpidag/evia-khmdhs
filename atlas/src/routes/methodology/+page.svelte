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
		defined χωρίς ΦΠΑ, so net values compare against those thresholds correctly. Contract
		detail pages keep a secondary «incl. ΦΠΑ» line with the registry's gross figures. Five
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
		When a contract names several regions, authorities or consortium partners, its € are split
		evenly across them for aggregate views — so maps, sankeys and per-region charts sum exactly
		to the programme total with no double counting. Tooltips additionally show
		<strong>full exposure</strong> (the whole contract value) where useful.
	</p>

	<h2 id="max-exposure">Maximum-exposure convention</h2>
	<p>
		Per-contractor pages count consortium contracts <strong>in full for each partner</strong> —
		the registry does not split consortium money, so per-entity totals answer “how much contract
		value is this company party to”, not “how much did it invoice”. Summing per-contractor
		totals therefore over-counts; programme totals never use this convention.
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

	<h2 id="pe-vocabulary">Regions (Π.Ε.)</h2>
	<p>
		All geography keys on the 74 Kallikratis regional units (περιφερειακές ενότητες), with
		spelling variants collapsed onto canonical names. Anti-nero work regions are hand-curated
		per contract from titles, forest authorities and the PDFs; amendments inherit from the
		version they supersede.
	</p>

	<h2 id="geocoding">Contractor locations</h2>
	<p>
		Registered HQ addresses come from VIES first, the ΓΕΜΗ publicity registry for the rest, and
		manual curation for the residue; coordinates from OSM Nominatim, accepted only when they
		validate against the stored postcode or regional unit. Every point carries a precision flag
		(address / municipality); unresolved contractors are counted and shown as such, never
		fabricated.
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
