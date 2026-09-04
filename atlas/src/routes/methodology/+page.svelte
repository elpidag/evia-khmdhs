<script lang="ts">
	import { page } from '$app/state';
	import { grInt } from '$lib/transforms/format';
	const meta = $derived(page.data.meta);
	// every figure in this prose is computed by the API (meta.facts) so the
	// text cannot go stale against the data; '—' when a layer is absent
	const f = $derived(meta?.facts ?? {});
	const nKh = $derived(meta?.antinero?.n_contracts);
	const nDase = $derived(meta?.dase?.n_contracts);
	const show = (v: number | undefined) => (v === undefined ? '—' : grInt(v));
	/** small counts are spelled out, as the prose does */
	const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
		'eight', 'nine', 'ten', 'eleven', 'twelve'];
	const spell = (v: number | undefined) =>
		v === undefined ? '—' : v < WORDS.length ? WORDS[v] : grInt(v);
	const Spell = (v: number | undefined) => {
		const s = spell(v);
		return s.charAt(0).toUpperCase() + s.slice(1);
	};
	/** the refresh date, as the records themselves report it */
	const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
		'August', 'September', 'October', 'November', 'December'];
	const refreshed = $derived.by(() => {
		const g = meta?.generated;
		if (!g) return '—';
		const d = new Date(g);
		return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
	});
</script>

<svelte:head>
	<title>Methodology — how these datasets were made</title>
	<meta
		name="description"
		content="How the three datasets were sourced from ΚΗΜΔΗΣ and Διαύγεια, how the documents were read and validated, the conventions behind every figure, and the limits of what the records can support."
	/>
</svelte:head>

<article>
	<hgroup>
		<h1>Methodology</h1>
		<p class="standfirst">
			Every chart on this platform carries a short caveat that links to the part of this page
			explaining it.
		</p>
	</hgroup>

	<nav class="toc" aria-label="Contents">
		<a href="#sources">Sourcing and organisation of the data</a>
		<a href="#validation">Document analysis and validation</a>
		<a href="#conventions">Analytical conventions</a>
		<a href="#limitations">Limitations, ethics and reproducibility</a>
	</nav>

	<h2 id="sources">Sourcing and organisation of the data</h2>
	<p>
		The three datasets presented on this platform were compiled from documents already publicly
		available through KIMDIS and Diavgeia. KIMDIS is Greece's Central Electronic Registry of Public
		Contracts, where contracts and the administrative records connected to their procurement are
		published. Diavgeia is the central transparency platform through which public bodies publish
		administrative decisions and acts. These two platforms form the main sources of the documents
		used in this research. <span id="pdf-provenance"
			>Rather than relying only on the metadata available through these platforms, the research also
			uses the signed PDFs and the administrative documents linked to them</span
		>, supplementing them where necessary with information from the public registries ΓΕΜΗ and VIES,
		for example to verify the registered location of contractors. For the forest workers'
		cooperatives, VIES is not a supplement but the principal source of the registered office, since
		forest cooperatives do not appear in ΓΕΜΗ. <span id="map-layers"
			>Beyond the documents themselves, the platform draws on reference layers that supply geography:
			the Kallikratis administrative boundaries published by geodata.gov.gr, which provide the
			regional units used throughout; the Copernicus EFFIS burnt area layer, whose scars are
			satellite estimates; and <span id="geocoding"
				>the OpenStreetMap Nominatim service, used to place addresses and named locations on the
				maps</span
			>.</span
		>
	</p>
	<p>The starting documents differ across the three datasets that are assembled.</p>
	<p id="antinero">
		For the Anti-nero dataset, the search was programme based. A first list of contracts was compiled
		manually through ΚΗΜΔΗΣ by searching different spellings of Anti-nero and references to Recovery
		and Resilience Facility Measure 16849. This list was then expanded through scripted searches
		intended to locate contracts that the manual search had missed. A contract enters the dataset
		only where there is positive evidence of its connection to the programme, through the Anti-nero
		name in the registry title, a funding code associated with the programme, or an explicit
		reference to Measure 16849 in the signed PDF document. {Spell(f['kh_title_only_n'])} contract chains
		from 2022 are included on the strength of the registry title alone: they carry the programme name
		but no funding code, and their signed texts contain no reference to Measure 16849. They account for
		roughly {f['kh_title_only_share'] ?? '—'} per cent of the value analysed. Later amendments inherit
		the programme membership of the contract they modify, while management and support contracts are
		excluded from financial aggregates to avoid counting the same funding twice.
	</p>
	<p id="dase-dedup">
		For the dataset of works awarded directly to Forest Workers' Cooperatives, the search instead
		begins with the contractor. It covers contracts published from September 2021 onwards in which
		the contracting party could be identified as a Forest Workers' Cooperative (ΔΑ.Σ.Ε.) under Law
		4423/2016; publication being the only date on which the registry allows a search to be bounded; {spell(
			f['dase_pre_window']
		)} contracts signed in the weeks before that date are therefore included. This contractor first approach
		was necessary because procurement categories alone do not identify the full range of works carried
		out by cooperatives. Of the {show(f['dase_records'])} records collected in this way, {show(nDase)}
		are treated as live contracts: registry cancellations, superseded versions, contracts posted twice
		and a small number whose signed text names no cooperative are excluded from the analysis. The Ministry
		of Environment and Energy maintains the official Register of Forest Cooperative Organisations and
		Forest Workers (ΜΗΔΑΣΟ) but no public list of registered cooperatives could be obtained for this research:
		the register has no public interface, and forest cooperatives are not recorded in ΓΕΜΗ. The list of
		forest workers' cooperatives presented here was therefore created from those identified through contracts
		and related documents sourced for this research. This also means that the number of forest workers'
		cooperatives found in the dataset cannot be compared with the total number registered nationally.
	</p>
	<p id="anadohoi">
		The privately financed restoration and reforestation dataset follows a third route. Since the
		restoration and reforestation contractor mechanism does not involve public procurement, these
		projects do not appear as contracts in KIMDIS. The dataset was therefore assembled from
		designation acts published on Diavgeia and the administrative acts cited by them. Information on
		the contractor, area, budget, duration and scope of the intervention was extracted primarily from
		the text of the designation acts themselves.
	</p>
	<p id="canonical-vat">
		Across the datasets, records referring to the same actor or place are organised through stable
		identifiers wherever possible. Contractors and forest workers' cooperatives are matched through
		their Tax Identification Number, ΑΦΜ, because the same entity may appear under several spellings
		across the registries. Those different spellings remain searchable and are retained as evidence,
		while the displayed name is curated from the documents. <span id="org-names"
			>Awarding bodies are grouped by their normalised name rather than by tax number, since tax
			identifiers do not distinguish them reliably in every case.</span
		>
		<span id="pe-vocabulary">Geographical analysis uses the 74 Kallikratis regional units.</span> For
		Anti-nero, the regions of intervention are identified from the contracts themselves.
		<span id="dase-regions"
			>For cooperative contracts, the regional unit is normally derived from the territorial
			competence of the forest authority that awarded the contract.</span
		> For the privately financed projects, the location, area of intervention and responsible forest authority
		are extracted from the designation acts.
	</p>

	<h2 id="validation">Document analysis and validation</h2>
	<p>
		The information collected does not rely only on the metadata stored in KIMDIS and Diavgeia for
		the documents sourced. Instead, the metadata of each document was cross checked against the
		information contained in its signed PDF. The metadata of each contract included its ADAM
		identifier, dates, contracting authority, contractor, funding source, stated value, procurement
		procedure, legal basis and CPV codes, the European Union's standard classification system for
		public procurement. Information that was either absent or insufficiently detailed in the metadata
		was then extracted from the contract itself, including the location and scope of the works, the
		responsible forest authority and, where it could be established, the announced duration of the
		contract. The upstream procurement records (funding requests, calls and award decisions) are
		retained as the registries publish them and were read only where a contract's trail depended on
		them.
	</p>
	<p>
		In the cases where the metadata recorded in KIMDIS or Diavgeia contradicted the information
		contained in the signed documents, the signed documents were treated as the stronger source.
		Corrections were made only where the original PDF provided clear evidence, including cases of
		incorrectly entered tax numbers, values or other metadata fields, and these corrections are
		disclosed on the corresponding page of the contract.
	</p>
	<p>
		The ADAM of each contract was also used to reconstruct its wider administrative trail. Related
		documents were collected from KIMDIS and Diavgeia, including funding requests, calls or
		invitations, award decisions, revisions of contract terms, supplementary contracts and works,
		deadline extensions, payment orders and, where available, acts recording completion or final
		acceptance. Since the registries do not always link these records consistently, connections were
		also established through references contained in the documents themselves. This document trail
		makes it possible to follow a contract beyond the moment at which it was signed and to
		distinguish its originally stated terms from later changes made to it. Payments are attributed to
		the final version of the chain, so that a payment made against an amended contract is not
		recorded under the version it replaced.
	</p>
	<p>
		Scripts were used to retrieve, organise and connect records at a scale that would have been
		difficult to handle manually. AI assistance was used in developing the scripts and processing
		workflow, particularly as the researcher had no prior coding experience. Inclusion decisions,
		classifications, corrections and ambiguous results were nevertheless reviewed against the
		original documents by the researcher. Automated processing was therefore used to manage the scale
		of the material, rather than to substitute for the validation of the sources themselves.
	</p>

	<h2 id="conventions">Analytical conventions</h2>
	<p id="stated-basis">
		For the Anti-nero dataset and the dataset including works awarded to Forest Workers'
		Cooperatives, <span id="net-basis"
			>monetary analysis is based on the stated value of each contract excluding VAT</span
		>. This is the amount agreed in the signed contract and provides a consistent basis for
		comparison across the two datasets. It also corresponds to the basis on which the procurement
		thresholds of Law 4412/2016 are defined. Payments identified through KIMDIS and Diavgeia are
		presented separately and are not substituted for the stated contract value, since payment records
		could not be found consistently for all contracts.
	</p>
	<p>
		The privately financed restoration and reforestation dataset cannot follow the same convention
		because its designation acts are not procurement records and monetary information is reported
		less consistently. Of the {show(f['ana_live'])} projects identified, {show(f['ana_with_sum'])} state
		a monetary amount, but only {show(f['ana_live_vat_net'])} specify that this is net of VAT, while {spell(
			f['ana_live_vat_gross']
		)} state a value inclusive of VAT and {show(f['ana_live_vat_unstated'])} give no indication of the
		VAT basis. Where an act explicitly identifies a net value, that amount is used. Where an act states
		a value inclusive of VAT and gives no net equivalent, the stated value is retained. Where the VAT
		basis is not specified, the value is retained as stated rather than converted. The remaining {show(
			f['ana_without_sum']
		)} projects do not state a monetary amount and are therefore left without a recorded budget rather
		than being estimated.
	</p>
	<p id="even-split">
		Some Anti-nero contracts cover more than one regional unit or involve more than one contracting
		party, while the documents provide only one total contract value. Where no information on its
		internal allocation is available, the value is divided equally between the regions or partners
		concerned for the purposes of aggregate maps and rankings. This is an analytical convention and
		does not imply that expenditure or revenue was actually distributed equally.
		<span id="joint-contracts"
			>Where a joint venture signs as a single legal entity, it is counted as one contractor.</span
		>
		<span id="member-firms"
			>A separate view identifies the firms behind a joint venture only where their membership is
			explicitly documented in the available documents and is never inferred from its name.</span
		>
	</p>
	<p id="procedures">
		Finally, procurement categories are read in relation to the legislation under which the contracts
		were awarded. <span id="dase-award-basis"
			>In particular, the frequent designation of Forest Workers' Cooperative contracts in KIMDIS as
			direct awards does not necessarily refer to the direct award procedure and thresholds of Law
			4412/2016. Many of these contracts are instead awarded under the Forest Code and the specific
			framework governing the assignment of forestry work to cooperatives.</span
		>
	</p>

	<h2 id="limitations">Limitations, ethics and reproducibility</h2>
	<p>
		The three datasets should not be read as complete inventories of all forestry works undertaken
		during the period examined. Their coverage depends on what could be identified and connected
		through the publicly available records of KIMDIS and Diavgeia. Contracts or related
		administrative acts may therefore exist that were not identified through the searches used here.
		This limitation is particularly important for the Forest Workers' Cooperative dataset, since the
		official ΜΗΔΑΣΟ register was not publicly accessible and it was therefore not possible to compare
		the cooperatives identified through contracts with the total population of registered
		cooperatives.
	</p>
	<p>
		The availability of documents also varies between different stages of a contract. Payment orders
		and acts recording completion or final acceptance could not be identified consistently for all
		contracts. The absence of such a document is therefore treated as an absence from the records
		sourced rather than as evidence that a payment was not made or that works were not completed. Any
		status based on the absence of a later document should be read with this limitation in mind.
	</p>
	<p id="freshness">
		The records presented on the platform were last refreshed on {refreshed}. Counts, sums and shares
		shown in the visualisations are calculated from the underlying databases rather than entered
		manually into individual graphs. The processing workflow can be rerun as new records become
		available, while corrections, classification decisions and changes to the rules used in
		processing the material are retained in a dated decision log. This makes it possible to trace not
		only the sources behind individual records but also the methodological decisions through which
		they were organised and presented.
	</p>
	<p>
		Finally, the research is based on publicly accessible administrative records concerning public
		contracts, organisations and public expenditure. A number of contractors are natural persons
		trading in their own name; they appear under the name the documents themselves use, since that is
		the identifier under which they hold the contract. Information concerning individual persons
		appearing in these documents is not treated as an object of analysis unless it is necessary for
		identifying the institutional role through which they appear in the administrative record. One
		available source was deliberately not used: the tax administration's company lookup, which would
		have resolved contractor identities but notifies the holder of every tax number queried.
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
	.toc {
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-2) var(--sp-4);
		margin: var(--sp-6) 0 var(--sp-2);
		padding-bottom: var(--sp-3);
		border-bottom: 1px solid var(--line);
		font-family: var(--font-ui);
		font-size: var(--fs-13);
	}
	.toc a {
		color: var(--ink-soft);
		text-decoration: none;
	}
	.toc a:hover {
		color: var(--ink);
		text-decoration: underline;
	}
	h2 {
		margin-top: var(--sp-8);
		scroll-margin-top: var(--sp-4);
	}
	p {
		font-size: var(--fs-15);
		line-height: 1.65;
		scroll-margin-top: var(--sp-6);
	}
	span[id] {
		scroll-margin-top: var(--sp-6);
	}
</style>
