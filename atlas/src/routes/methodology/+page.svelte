<script lang="ts">
	import { page } from '$app/state';
	const meta = $derived(page.data.meta);
</script>

<svelte:head>
	<title>Methodology — how these numbers are made</title>
	<meta
		name="description"
		content="Definitions, conventions and honest limitations behind the Atlas datasets: effective values, even-split attribution, deduplication, entity keying."
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
		for payment orders; nothing is divided by a VAT rate — 654 ΔΑΣΕ contracts blend 0%/13%/24%
		line items, so a flat conversion would be wrong). This is also the basis the law uses: the
		ν.4412/2016 εκτιμώμενη αξία — and therefore the €30k/€60k direct-award ceilings — is
		defined χωρίς ΦΠΑ, so net values compare against those thresholds correctly. Contract
		detail pages keep a secondary «incl. ΦΠΑ» line with the registry's gross figures. Five
		Diavgeia-only clearance payments carried no net amount in any registry; their net figures
		were extracted from the signed PDFs («ΚΑΘΑΡΗ ΑΞΙΑ ΠΑΡΑΣΤΑΤΙΚΟΥ») and recorded as curated
		corrections with excerpt evidence.
	</p>

	<h2 id="effective-value">Effective value (Anti-nero)</h2>
	<p>
		A contract's <strong>effective value</strong> is the sum of its non-cancelled payment orders
		when at least one exists, else its stated value — all net of ΦΠΑ. Payments attributed to a
		superseded contract version follow the amendment chain to the final version. This absorbs
		amendments and shows actual disbursement for running contracts.
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
		A curated registry of 103 Διευθύνσεις Δασών and Δασαρχεία (names, genitive aliases, seat
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
		rows and superseded versions are excluded, leaving 2,018 live contracts. Payment orders
		and the full procurement family (αίτημα → διακήρυξη → κατακύρωση) have been harvested from
		the registry's chain, but the registry posts payments for only part of the population
		(2022–23 are near-blank as registry practice) — so charts and rankings stay on stated
		values, and the «actually paid» figure appears only as a KPI with its coverage printed.
	</p>

	<h2 id="canonical-vat">Canonical ΑΦΜ (ΔΑΣΕ)</h2>
	<p>
		The registry spells the same co-op up to 12 ways, sometimes with whitespace or glued text
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

	<h2 id="dase-cpv-noise">CPV keying noise</h2>
	<p>
		386 ΔΑΣΕ logging contracts carry a miskeyed insurance CPV (66519300-4). They are flagged as
		registry noise wherever CPVs are shown and never counted as insurance services.
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
		Anti-nero figures are effective € (payments where they exist); ΔΑΣΕ figures are stated,
		deduplicated € — both excl. VAT. The headline ratio compares the best available basis on
		each side and both bases are printed under every paired figure. The populations also
		differ: one is a single programme, the other is a whole sector of the co-operative economy.
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
		stated budget is curated from the act's own text: 15 acts say «άνευ/χωρίς ΦΠΑ», two state
		a gross figure, and the rest write a bare number — the committed total prefers the net
		figure <em>where the act itself states one</em> (Lidl's act states both, so its net
		€241,936 is used) and never converts the silent ones.
	</p>

	<h2 id="explore">The Explore table</h2>
	<p>
		The combined table lists every Anti-nero contract (effective €), every live ΔΑΣΕ contract
		(stated €) and every sponsor project (stated budget after amendments, often absent) — all
		excl. VAT, but three different value bases side by side, labelled and never summed into
		one headline. «HQ region» is available only for Anti-nero contractors, whose registered
		seats are curated; procedure for sponsor projects is shown as «Πράξη αναδόχου (χορηγία)»
		because no procurement procedure exists. The «Stated (net)» column is the registry's
		stated net value (for Anti-nero it sits beside the <em>effective</em> net figure, so the
		two differ where payments exist); sponsor acts state a single figure with mixed VAT
		treatment, so their stated-net column stays blank and their value is the committed figure,
		net where the act says so. The «Διακήρυξη» filter uses the ΚΗΜΔΗΣ chain links: only 41 of
		252 in-scope Anti-nero contracts and 144 of 2,018 live ΔΑΣΕ contracts have a linked
		διακήρυξη/πρόσκληση — the registry's
		chain knows only what each σύμβαση declared when posted, so «without» means <em>no
		linked notice in the registry</em>, not proof that none was ever published. The «End
		date» filter marks rows with a recorded project ending: an Anti-nero completion act
		found on Διαύγεια (οριστική παραλαβή / περαίωση — 155 of 252 contracts) or a completed
		sponsor project; «without» means no such act was found. ΔΑΣΕ rows stay outside this
		filter by an evidenced negative finding: probing 75 contracts found that ΔΑΣΕ awarders
		never cite the ΑΔΑΜ in Διαύγεια act subjects, and their παραλαβές are bundled municipal
		approvals that cannot be joined to individual contracts — so no ΔΑΣΕ ending is claimed
		rather than guessed. Filtering
		runs entirely in the browser; every filter state is a shareable URL.
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
