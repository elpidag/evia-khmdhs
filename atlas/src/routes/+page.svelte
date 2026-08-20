<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import Beeswarm from '$lib/charts/Beeswarm.svelte';
	import DisbursementCurves from '$lib/charts/DisbursementCurves.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import Sankey from '$lib/charts/Sankey.svelte';
	import SmallMultiples from '$lib/charts/SmallMultiples.svelte';
	import StripTimeline from '$lib/charts/StripTimeline.svelte';
	import AntineroMap from '$lib/sections/AntineroMap.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import FlowMap from '$lib/sections/FlowMap.svelte';
	import OriginSplit from '$lib/sections/OriginSplit.svelte';
	import Bipartite from '$lib/sections/Bipartite.svelte';
	import { loadCentroids } from '$lib/maps/useGeo';
	import type { Connections } from './connections/+page';
	import ContractNetwork from '$lib/charts/ContractNetwork.svelte';
	import type { NetNode } from '$lib/transforms/network';
	import { NET_MODES, type NetMode } from '$lib/transforms/networkScene';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import {
		apiGetCached,
		type AntineroMapPayload,
		type PaymentsPayload,
		type PeYearly,
		type SankeyPayload,
		type SwarmRow
	} from '$lib/api';
	import { eurShort, grInt, pct } from '$lib/transforms/format';
	import { page } from '$app/state';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	// heavy payloads load client-side (cached across navigations);
	// $state.raw — immutable data must not pay deep-proxy overhead
	let map = $state.raw<AntineroMapPayload | null>(null);
	let payments = $state.raw<PaymentsPayload | null>(null);
	let sankey = $state.raw<SankeyPayload | null>(null);
	let swarm = $state.raw<SwarmRow[] | null>(null);
	let peYearly = $state.raw<PeYearly | null>(null);
	let network = $state.raw<{
		nodes: NetNode[];
		stats: Record<string, number>;
		fire_season: { from: string; to: string; n_contracts: number };
	} | null>(null);
	/** the flow layer, moved here from /connections (user, 2026-08-20) */
	let net = $state.raw<Connections | null>(null);
	let centroids = $state.raw<Record<string, [number, number]>>({});
	$effect(() => {
		apiGetCached<Connections>(fetch, '/api/connections').then((v) => (net = v));
		loadCentroids(fetch).then((c) => (centroids = c));
		apiGetCached<AntineroMapPayload>(fetch, '/api/antinero/map').then((v) => (map = v));
		apiGetCached<PaymentsPayload>(fetch, '/api/antinero/payments').then((v) => (payments = v));
		apiGetCached<SankeyPayload>(fetch, '/api/antinero/sankey').then((v) => (sankey = v));
		apiGetCached<SwarmRow[]>(fetch, '/api/antinero/swarm').then((v) => (swarm = v));
		apiGetCached<PeYearly>(fetch, '/api/antinero/pe-yearly').then((v) => (peYearly = v));
		apiGetCached<{
			nodes: NetNode[];
			stats: Record<string, number>;
			fire_season: { from: string; to: string; n_contracts: number };
		}>(fetch, '/api/antinero/network').then((v) => (network = v));
	});

	// the programme chart is one population under three arrangements, and
	// each arrangement has a different honest headline — every number in
	// them comes from the payload's own stats
	const netMode = $derived(
		(NET_MODES.find((m) => m.value === page.url.searchParams.get('net'))?.value ??
			'time') as NetMode
	);
	const netCopy = $derived.by(() => {
		const st = network?.stats ?? {};
		if (netMode === 'call')
			return {
				title: `THE PROGRAMME WAS BOUGHT IN ${grInt(st.n_calls)} SEPARATE PROCUREMENTS, MOST OF THEM ONE CONTRACT LONG`,
				subtitle:
					'Each star is one call: the biggest lot at its centre, the others around it. Below, the calls that produced a single contract, and the awards made with no call at all.',
				caveat: 'The dashed lines join two calls won by the same contractor.'
			};
		if (netMode === 'pack')
			return {
				title: `${grInt(st.n_single_call)} OF THE ${grInt(st.n_calls)} CALLS BOUGHT EXACTLY ONE CONTRACT`,
				subtitle:
					'The contracts nested inside the call that bought them: the split procurements hold the middle, and every contract bought on its own rings them. Bubble area is the money.',
				caveat:
					'A bubble is one πρόσκληση and the circles inside it are its lots; a bare circle is a contract with no sibling, dashed when no call was published at all.'
			};
		return {
			title: `${grInt(st.n_same_day_calls)} OF THE ${grInt(st.n_multi_calls)} SPLIT PROCUREMENTS SIGNED EVERY LOT ON ONE DAY`,
			subtitle:
				'Every in-scope contract on the date it was signed, dodged so none hides another; contracts bought under the same call are joined.',
			caveat:
				'Vertical position carries no meaning here — it is packing, not a value axis. The shaded stripes are the fire season, 1 May to 31 October.'
		};
	});

	const directEur = $derived(o.procedures.find((p) => p.label.includes('Απευθείας'))?.eur ?? 0);
	// the ranking has two views of the same money (user, 2026-08-20): the
	// company that SIGNED, and the firms behind it. A κοινοπραξία signs 54 of
	// the contracts, so «as contracted» hides whoever is inside it.
	const RANK_MODES = [
		{ value: 'party', label: 'As contracted' },
		{ value: 'firm', label: 'By member firm' }
	];
	const rankMode = $derived(
		o.member_firms ? (page.url.searchParams.get('rank') ?? 'party') : 'party'
	);
	const topRows = $derived.by(() => {
		const rows: {
			vat_number: string;
			name: string;
			n_contracts: number;
			total_eur: number;
			via_eur?: number;
			n_ventures?: number;
		// degrade to the contracted view when the API predates this layer,
		// rather than throwing on an undefined list
		}[] = (rankMode === 'firm' ? o.member_firms : o.top_contractors) ?? o.top_contractors;
		return rows.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/antinero/contractor/${c.vat_number}`,
			sublabel: c.via_eur
				? `${c.n_contracts} contracts · ${eurShort(c.via_eur)} through ${
						c.n_ventures
					} joint venture${(c.n_ventures ?? 0) > 1 ? 's' : ''}`
				: `${c.n_contracts} contracts`
		}));
	});
	const procRows = $derived(
		o.procedures.map((p) => ({
			label: p.label,
			value: p.eur,
			sublabel: `${p.n_contracts} contracts`
		}))
	);
	const studyRows = $derived(
		o.studies.top.map((s) => ({
			label: String(s.title).slice(0, 90),
			value: Number(s.eur),
			href: `/antinero/contract/${s.ref}`,
			sublabel: `${((s.share as number) * 100).toFixed(1)}% of the contract's net value`
		}))
	);

	// auto-note: the single biggest payment month
	const peak = $derived.by(() => {
		const byMonth = new Map<string, number>();
		for (const e of payments?.events ?? [])
			if (e.m) byMonth.set(e.m, (byMonth.get(e.m) ?? 0) + (e.eur || 0));
		let best: [string, number] = ['', 0];
		for (const kv of byMonth) if (kv[1] > best[1]) best = kv;
		return { m: best[0], eur: best[1] };
	});

	// statutory ν.4782/2021 ceilings come from the API payload, never inline
	const thresholds = $derived(
		(o.direct_awards.thresholds as number[]).map((v, i) => ({
			v,
			label: `€${Math.round(v / 1000)}k ceiling (${i === 0 ? 'supplies/services, ν.4782/2021' : 'works'})`
		}))
	);
	const miniThresholds = $derived(
		(o.direct_awards.thresholds as number[]).map((v) => ({
			v,
			label: `€${Math.round(v / 1000)}k`
		}))
	);
	// the modal direct-award bin, for the finding title
	const daModal = $derived.by(() => {
		const counts = o.direct_awards.counts as number[];
		const labels = o.direct_awards.labels as string[];
		let best = 0;
		for (let i = 1; i < counts.length; i++) if (counts[i] > counts[best]) best = i;
		return labels[best] ?? '';
	});
	const firstPayYear = $derived((o.timeseries.months[0] ?? '').slice(0, 4));
	// work-type category chart: stated € or contract counts, same bars
	let catMode = $state<'eur' | 'n'>('eur');
	const catRows = $derived(
		[...o.categories]
			.sort((a, b) => (catMode === 'eur' ? b.eur - a.eur : b.n - a.n))
			.map((c) => ({
				label: c.label,
				value: catMode === 'eur' ? c.eur : c.n,
				sublabel: catMode === 'eur' ? `${grInt(c.n)} contracts` : eurShort(c.eur)
			}))
	);
	const topCat = $derived(
		o.categories.reduce((a, b) => (b.eur > a.eur ? b : a), o.categories[0])
	);
	// hero bar fills — both data-proportional
	const bidPct = $derived((o.kpis.n_single_bidder / o.kpis.n_contracts) * 100);
	// what kind of σύμβαση each in-scope record is: computed from the payload,
	// never typed. The supplementary works are one phenomenon in two document
	// forms — the supplementary contract itself and the decision approving one
	// — so they are stated as one number (DATA_DECISIONS 2026-08-18).
	const dk = $derived.by(() => {
		const c = o.document_kinds?.counts ?? {};
		return {
			total: o.document_kinds?.total ?? 0,
			n_kinds: Object.keys(c).length,
			contract: c.contract ?? 0,
			amendment: c.amendment ?? 0,
			supplementary:
				(c.supplementary_contract ?? 0) +
				(c.approval_ape_supplementary ?? 0) +
				(c.approval_supplementary ?? 0),
			extension: c.approval_schedule_extension ?? 0
		};
	});
	const paidPct = $derived((o.kpis.paid_eur / o.kpis.stated_eur) * 100);
</script>

<svelte:head>
	<title>Anti-nero — where the wildfire-prevention money went</title>
	<meta
		name="description"
		content="Interactive audit of Greece's Anti-nero wildfire-prevention programme: {grInt(
			o.kpis.n_contracts
		)} contracts, {eurShort(o.kpis.total_eur)} stated (excl. VAT)."
	/>
</svelte:head>

<div class="antp">
<section class="hero">
	<div class="heroleft">
	<div class="cards">
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contracts)}</div>
			<div class="lbl">in-scope contracts</div>
		</div>
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contractors)}</div>
			<div class="lbl">contractors</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(o.kpis.stated_eur).toLowerCase()}</div>
			<div class="lbl">
				total stated value of contracts<br />(excl. VAT)
			</div>
		</div>
	</div>
	<div class="midcol">
		<div class="bars">
			<div class="dabar" role="img" aria-label="Share of contracts awarded directly">
				<div class="track">
					<div class="fill" style:width={`${o.kpis.pct_direct}%`}>
						<div class="danum">{pct(o.kpis.pct_direct)}</div>
						<div class="datext">of contracts were direct awards</div>
					</div>
				</div>
			</div>
			<div class="bidbar" role="img" aria-label="Contracts that drew exactly one bid">
				<div class="track">
					<div class="bfill" style:width={`${bidPct}%`}>{grInt(o.kpis.n_single_bidder)}</div>
					<div class="btext">contracts drew <strong>1 bid</strong></div>
				</div>
			</div>
		</div>
		<div class="paidcard" role="img" aria-label="Paid so far, as a share of the stated total">
			<div class="pfill" style:height={`${paidPct}%`}>
				<div class="pnum">{eurShort(o.kpis.paid_eur).toLowerCase()}</div>
				<div class="plbl">already paid</div>
			</div>
		</div>
	</div>
	</div>
	<div class="about">
		<div class="kicker">THE PROGRAMME</div>
		<p>
			Greece's flagship wildfire-prevention programme (ΥΠΕΝ, RRF Action 16849) has signed
			{grInt(o.kpis.n_contracts)} contracts since {o.yearly[0]?.year ?? '2022'} — of the
			{eurShort(o.kpis.stated_eur)} stated, {eurShort(o.kpis.paid_eur)} has actually been paid
			({grInt(o.kpis.n_payments)} payment orders). {pct(o.kpis.pct_direct)} of contracts —
			{eurShort(directEur)}, the bulk of the money — went by direct award, and {grInt(
				o.kpis.n_single_bidder
			)} contracts drew exactly one bid. This page follows what actually got paid, to whom,
			and where — <a href="/methodology#antinero">methodology</a>.
		</p>
		{#if dk && dk.n_kinds > 0}
			<p class="kinds">
				All {grInt(dk.total)} are συμβάσεις, which is what the registry files them as; the
				kind says which. {grInt(dk.contract)} are original contracts,
				{grInt(dk.amendment)} revise the terms of one without touching its price,
				{grInt(dk.supplementary)} add supplementary works, and {grInt(dk.extension)}
				only extend a deadline —
				<a href="/methodology#record-kinds">what each record is</a>.
			</p>
		{/if}
		{#if o.probable && o.probable.n > 0}
			<details class="probable">
				<summary>
					+ {grInt(o.probable.n)} additional contracts found ({eurShort(
						o.probable.total_eur
					).toLowerCase()} excl. VAT), probably related to the Antinero programme, but not
					included in the calculations
				</summary>
				<p class="pnote">
					Their signed documents carry no provable RRF-16849 financing evidence — no fund
					code, no Ταμείο Ανάκαμψης clause (<a href="/methodology#antinero">methodology</a>).
				</p>
				<ul>
					{#each o.probable.rows as r (r.ref)}
						<li>
							<a href={`/antinero/contract/${r.ref}`}>{r.ref}</a>
							{#if r.d}<span class="pd">{r.d}</span>{/if}
							<span class="pt">{r.title}</span>
						</li>
					{/each}
				</ul>
			</details>
		{/if}
	</div>
</section>

{#if map}
	<ChartFrame
		title="MAP"
		caveat="Contract values split evenly across a contract's regions (and partners), so both maps sum to the programme total; tooltips also show full exposure."
		anchor="map"
		methodology="even-split"
	>
		<AntineroMap data={map} />
	</ChartFrame>
{:else}
	<div class="skeleton" id="map" style="height: 560px"></div>
{/if}

{#if net}
	{@const localPct = (() => {
		let t = 0,
			l = 0;
		for (const f of net.flows) {
			t += f.total_eur;
			if (f.source_pe === f.target_pe) l += f.total_eur;
		}
		return t ? Math.round((100 * l) / t) : 0;
	})()}
	<ChartFrame
		title="Only {localPct}% of the work-money goes to firms based where the work is"
		subtitle="Each region is coloured by the share of its works won by out-of-region firms — darker means more of the money leaves. Click a region: red arrows show who reaches in, blue where its own firms reach out."
		caveat="Geocoded contractors only — {eurShort(net.coverage.resolved_eur)} of {eurShort(
			net.coverage.total_eur
		)} resolved. Full-exposure convention: a multi-region contract counts toward every region pair it touches; the within-region shares are unaffected."
		anchor="flows"
		methodology="even-split"
	>
		<FlowMap flows={net.flows} {centroids} />
	</ChartFrame>

	<ChartFrame
		title="In the biggest destinations, local firms take a small slice"
		subtitle="€ of works in the top-{Math.min(12, net.origins.length)} destination regions, split by whether the winning firm is based in that region."
		anchor="origins"
		methodology="even-split"
	>
		<OriginSplit rows={net.origins.slice(0, 12)} />
	</ChartFrame>

	{@const maxReach = (() => {
		const by = new Map<string, number>();
		for (const e of net.contractor_pe) by.set(e.vat, (by.get(e.vat) ?? 0) + 1);
		let top = { vat: '', n: 0 };
		for (const [vat, n] of by) if (n > top.n) top = { vat, n };
		return { n: top.n, name: net.contractors[top.vat]?.name ?? '—' };
	})()}
	<ChartFrame
		title="A handful of companies reach into many regions"
		subtitle="Contractor ↔ work-region links ({grInt(net.contractor_pe.length)} edges across {grInt(
			Object.keys(net.contractors).length
		)} contractors). {maxReach.name} alone works in {maxReach.n} regional units."
		caveat="Edge € even-split across a contract's partners and regions — the layer sums to the programme total."
		anchor="bipartite"
		methodology="even-split"
	>
		<Bipartite edges={net.contractor_pe} contractors={net.contractors} />
	</ChartFrame>
{/if}

<Defer height={640}>
{#if network}
	<ChartFrame
		title={netCopy.title}
		subtitle={netCopy.subtitle}
		caveat="{netCopy.caveat} Circle area is the contract's stated value excl. VAT, on one scale in every arrangement; a call is the πρόσκληση the contract cites in its own signed text ({grInt(
			network.stats.n_calls
		)} resolved this way). Every layout is deterministic, not a force simulation."
		anchor="network"
		methodology="procurement-families"
	>
		<div class="netbar">
			<SegmentToggle param="net" fallback="time" options={NET_MODES} />
		</div>
		<ContractNetwork
			nodes={network.nodes}
			stats={network.stats}
			mode={netMode}
			season={network.fire_season}
		/>
	</ChartFrame>
{:else}
	<div class="skeleton" id="network" style="height: 620px"></div>
{/if}
</Defer>

<Defer height={900}>
{#if payments}
	<ChartFrame
		title="PAYMENTS TIMELINE"
		subtitle="One tick per payment order ({grInt(payments.events.length)}), height ∝ √€, by programme phase — the biggest single month was {peak.m} ({eurShort(
			peak.eur
		)}). Hover for the order, click through to the contract."
		caveat="{grInt(
			payments.fallback
		)} of {grInt(payments.events.length)} orders carry no signature date — the registry submission date is shown for those{payments
			.undated.n
			? `; ${grInt(payments.undated.n)} remain undated (${eurShort(payments.undated.eur)})`
			: ''}."
		anchor="payments"
		methodology="payment-dates"
	>
		<StripTimeline data={payments} />
	</ChartFrame>

	<ChartFrame
		title="CUMULATIVE DISBURSEMENT"
		subtitle="Cumulative € of payment orders since {firstPayYear} — stacked by phase, or same-point-in-year comparison."
		caveat="Payment orders attributed to a contract's final version; registry net-of-ΦΠΑ amounts."
		anchor="disbursement"
		methodology="stated-basis"
	>
		<DisbursementCurves timeseries={o.timeseries} {payments} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 480px"></div>
	<div class="skeleton" style="height: 400px"></div>
{/if}
</Defer>

<Defer height={340}>
{#if swarm}
	<ChartFrame
		title="CONTRACT VALUES"
		subtitle="Every in-scope contract ({grInt(
			o.kpis.n_contracts
		)}) as one dot on a log scale (stated €, excl. VAT) — almost all sit far above the direct-award ceilings. Ringed dots drew a single bid."
		caveat="The ν.4782/2021 ceilings are defined on the excl-VAT estimated value — the same basis as these dots. RRF emergency provisions allowed direct awards above them; the lines are printed for scale."
		anchor="swarm"
		methodology="stated-basis"
	>
		<Beeswarm rows={swarm} {thresholds} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 320px"></div>
{/if}
</Defer>

<Defer height={620}>
{#if sankey}
	{@const sk = sankey}
	{@const nPhases = sk.nodes.filter((n) => n.kind === 'phase').length}
	{@const nTop = sk.nodes.filter((n) => n.kind === 'contractor').length}
	<ChartFrame
		title="MONEY FLOW"
		subtitle="ΥΠΕΝ → programme phase → contractor (top {nTop} by stated €, everyone else aggregated) — {eurShort(
			sk.links
				.filter((l) => sk.nodes.find((n) => n.id === l.t)?.kind === 'contractor')
				.reduce((s, l) => s + l.eur, 0)
		)} of the {eurShort(o.kpis.total_eur)} ends at those {grInt(nTop)} companies."
		caveat="Consortium values split evenly between partners here, so every column sums to the programme total."
		anchor="sankey"
		methodology="even-split"
	>
		<Sankey data={sk} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 560px"></div>
{/if}
</Defer>

<div class="pair">
	<ChartFrame
		title="DIRECT AWARDS"
		subtitle="{grInt(
			o.direct_awards.n as number
		)} direct-award contracts by stated value (excl. VAT) — they pile up around €{daModal}, far beyond the ν.4782/2021 ceilings."
		caveat="The statutory ceilings and these values are both excl. VAT; RRF emergency provisions allowed direct awards above the ceilings."
		anchor="direct-awards"
		methodology="procedures"
	>
		<LogHistogram
			labels={o.direct_awards.labels as string[]}
			counts={o.direct_awards.counts as number[]}
			edges={o.direct_awards.edges as number[]}
			thresholds={miniThresholds}
		/>
	</ChartFrame>

	<ChartFrame
		title="AWARD PROCEDURES"
		subtitle="Stated € by award procedure — open procedures are the exception, not the rule."
		anchor="procedures"
	>
		<BarH rows={procRows} color="var(--c-antinero)" highlight={(r) => r.label.includes('Απευθείας')} />
	</ChartFrame>
</div>

<Defer height={400}>
{#if peYearly}
	<ChartFrame
		title="MONEY BY REGION PER YEAR"
		subtitle="Yearly stated € per regional unit (top {Math.min(
			20,
			peYearly.pes.length
		)}, same scale). Click a facet to drill into it on the map."
		caveat="Even-split attribution; stated € at signature year."
		anchor="pe-yearly"
		methodology="even-split"
	>
		<SmallMultiples data={peYearly} hrefOf={(pe) => `/?focus=works:${encodeURIComponent(pe)}#map`} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 380px"></div>
{/if}
</Defer>

<ChartFrame
	title="RANKING OF COMPANIES"
	subtitle={rankMode === 'firm'
		? `the same money attributed to the firms BEHIND the joint ventures — ${grInt(
				o.consortiums.n_documented
			)} of the ${grInt(o.consortiums.n)} ventures have members on record, ${grInt(
				o.consortiums.n_firms
			)} firms in all`
		: `according to sums contracted via the programme — top ${topRows.length} of ${grInt(
				o.kpis.n_contractors
			)} contractors, ${eurShort(o.kpis.total_eur)} in total`}
	caveat={rankMode === 'firm'
		? `A joint venture whose members are on record is replaced by them and its € split evenly; one whose members no document names keeps its own row, so ${eurShort(
				o.consortiums.eur_unsplit
			)} sits identically in both views. Both add up to the programme total.`
		: 'Each contract is counted once: a jointly signed one is split evenly between its partners, so these totals add up to the programme total.'}
	anchor="top-contractors"
	methodology={rankMode === 'firm' ? 'joint-contracts' : 'stated-basis'}
>
	<div class="netbar">
		<SegmentToggle param="rank" fallback="party" options={RANK_MODES} />
	</div>
	<!-- same measure and bar height as the sponsored-works ranking, so the
	     two datasets' rankings read alike; the bars stay black, this
	     dataset's colour (user, 2026-08-20) -->
	<div class="rankw">
		<BarH rows={topRows} color="var(--c-antinero)" inside barHeight={30} />
	</div>
</ChartFrame>

<ChartFrame
	title="STUDY COSTS"
	subtitle="The ten largest study (μελέτη) costs extracted from the signed PDFs — the median is {pct(
		(o.studies.summary.median_share as number) * 100
	)} of a contract's net value; {grInt(o.studies.summary.n_with)} of {grInt(
		o.studies.summary.n_in_scope
	)} contracts state one, {eurShort(o.studies.summary.total_eur)} in total."
	caveat="ΕΣΑ design-build contracts bundle the study into the works price and honestly state none."
	anchor="studies"
	methodology="study-costs"
>
	<BarH rows={studyRows} color="#8f8f8f" />
</ChartFrame>

{#if o.categories.length && topCat}
	<ChartFrame
		title="TYPES OF WORK"
		subtitle="Every in-scope contract assigned one of {grInt(
			o.categories.length
		)} curated work-type categories from its signed PDF's project title — «{topCat.label}» dominates with {eurShort(
			topCat.eur
		)} across {grInt(topCat.n)} contracts ({pct((topCat.eur / o.kpis.total_eur) * 100)} of the programme)."
		caveat="One category per contract, curated from the signed PDF's descriptive project title with the contract's rarer CPV codes as tie-breaker, so the € columns sum to the programme's stated-net total."
		anchor="categories"
		methodology="categories"
	>
		<div class="mode" role="group" aria-label="Category metric">
			<button
				type="button"
				class:active={catMode === 'eur'}
				onclick={() => (catMode = 'eur')}>Stated €</button
			>
			<button type="button" class:active={catMode === 'n'} onclick={() => (catMode = 'n')}
				>Contracts</button
			>
		</div>
		<BarH
			rows={catRows}
			color="#2b2b2b"
			inside
			barHeight={22}
			fmt={catMode === 'eur' ? eurShort : grInt}
		/>
	</ChartFrame>
{/if}

{#if o.cpvs.length}
	{@const topCpv = o.cpvs[0]}
	<ChartFrame
		title="CPV CODES"
		subtitle="All {grInt(o.cpvs.length)} procurement-vocabulary (CPV) codes declared across the {grInt(
			o.kpis.n_contracts
		)} in-scope contracts, sorted by reach — the most common, «{topCpv.desc}», appears on {grInt(
			topCpv.n
		)} of them ({pct((topCpv.n / o.kpis.n_contracts) * 100)})."
		caveat="Codes and descriptions as declared in ΚΗΜΔΗΣ. Contracts declare several codes each, so counts sum to more than the number of contracts — and for the same reason no € is attributed per code."
		anchor="cpvs"
	>
		<div class="cpvlist">
			{#each o.cpvs as c (c.code)}
				<div class="cpvrow">
					<span class="cn">{grInt(c.n)}</span>
					<span class="cc">{c.code}</span>
					<span class="cd">{c.desc}</span>
				</div>
			{/each}
		</div>
	</ChartFrame>
{/if}

</div>

<style>
	/* the ranking's measure, shared with the sponsored-works page */
	.rankw {
		max-width: 75%;
	}
	@media (max-width: 900px) {
		.rankw {
			max-width: none;
		}
	}
	.netbar {
		display: flex;
		justify-content: flex-end;
		margin-bottom: var(--sp-2);
	}
	/* every section title follows the sponsored-works kicker, in the
	   antinero dataset colour (black) */
	.antp :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-antinero);
	}
	/* the two paper maps take the sponsored-works ground */
	.antp :global(.map) {
		background: #f2f2f2;
		border: none;
		box-shadow: none;
	}
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	/* cards column + the bars/paid column beside it */
	.heroleft {
		/* the two columns split the first map's span equally:
		   160 + 268 + 16 + 268 = 712 = the left map's right edge at the
		   1440 design width */
		display: grid;
		grid-template-columns: 268px 268px;
		gap: var(--sp-4);
		align-items: stretch;
	}
	.cards {
		/* three equal rows — every card the height of the tallest */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	/* middle column mirrors the cards grid: the two bars share the first
	   card's row (equal heights + the gap between), the paid card fills
	   the third row so it matches the stated-value card exactly */
	.midcol {
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	.bars {
		grid-row: 1;
		display: grid;
		grid-template-rows: 1fr 1fr;
		gap: var(--sp-4);
	}
	.dabar .track,
	.bidbar .track {
		height: 100%;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
	}
	.dabar .fill {
		height: 100%;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 2px;
		padding: 0 14px;
	}
	.dabar .danum {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		line-height: 1;
	}
	.dabar .datext {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-12);
		line-height: 1.2;
	}
	.bidbar .track {
		display: flex;
		align-items: center;
	}
	.bidbar .bfill {
		height: 100%;
		min-width: 40px;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		flex: 0 0 auto;
	}
	.bidbar .btext {
		padding-left: 10px;
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		white-space: nowrap;
	}
	.bidbar .btext strong {
		font-weight: 900;
	}
	/* paid vs stated: black fill rises to the paid share of the stated €;
	   the unfilled remainder reads as light grey, no outer border */
	.paidcard {
		grid-row: 3;
		position: relative;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
	}
	.paidcard .pfill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 2px;
		padding: 8px 14px 10px;
	}
	.paidcard .pnum {
		font-family: var(--font-display);
		font-weight: 900;
		/* matches the card numbers' 36px cap; fits the 268px card */
		font-size: 36px;
		line-height: 0.95;
		white-space: nowrap;
	}
	.paidcard .plbl {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	@media (max-width: 900px) {
		.heroleft {
			grid-template-columns: 268px;
		}
		.midcol {
			grid-template-rows: auto;
		}
		.bars,
		.paidcard {
			grid-row: auto;
		}
		.paidcard {
			height: 117px;
		}
	}
	.card {
		background: var(--c-antinero);
		color: #fff;
		padding: var(--sp-4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	.card .num {
		font-family: var(--font-display);
		font-weight: 900;
		/* 36px is the largest size at which the stated € fits a 268px card */
		font-size: clamp(28px, 3.2vw, 36px);
		line-height: 0.95;
	}
	.card .lbl {
		font-family: var(--font-display);
		font-weight: 400; /* Obviously Regular */
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--c-antinero);
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	.about p.kinds {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-faint);
	}
	.probable {
		margin-top: var(--sp-4);
		max-width: var(--prose-w);
		font-size: var(--fs-13);
		color: var(--ink-faint);
	}
	.probable summary {
		cursor: pointer;
	}
	.probable .pnote {
		margin: var(--sp-2) 0 0;
		font-size: var(--fs-13);
	}
	.probable ul {
		margin: var(--sp-2) 0 0;
		padding-left: 1.2em;
	}
	.probable li {
		margin-bottom: 2px;
	}
	.probable .pd {
		margin-left: 0.5em;
	}
	.probable .pt {
		margin-left: 0.5em;
	}
	@media (max-width: 900px) {
		.hero {
			grid-template-columns: 1fr;
		}
	}
	.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-6);
	}
	@media (max-width: 900px) {
		.pair {
			grid-template-columns: 1fr;
		}
	}
	.mode {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
		margin-bottom: var(--sp-2);
	}
	.mode button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.mode button.active {
		background: var(--ink);
		color: var(--paper);
	}
	.cpvlist {
		columns: 3 300px;
		column-gap: var(--sp-6);
		font-size: var(--fs-13);
	}
	.cpvrow {
		display: flex;
		gap: 0.5em;
		align-items: baseline;
		break-inside: avoid;
		padding: 2px 0;
		border-bottom: 1px solid var(--paper-3);
	}
	.cn {
		min-width: 2.2em;
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
	.cc {
		color: var(--ink-faint);
		font-size: var(--fs-12);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.cd {
		color: var(--ink-soft);
	}
</style>
