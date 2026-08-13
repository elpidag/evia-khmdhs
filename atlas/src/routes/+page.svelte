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
	$effect(() => {
		apiGetCached<AntineroMapPayload>(fetch, '/api/antinero/map').then((v) => (map = v));
		apiGetCached<PaymentsPayload>(fetch, '/api/antinero/payments').then((v) => (payments = v));
		apiGetCached<SankeyPayload>(fetch, '/api/antinero/sankey').then((v) => (sankey = v));
		apiGetCached<SwarmRow[]>(fetch, '/api/antinero/swarm').then((v) => (swarm = v));
		apiGetCached<PeYearly>(fetch, '/api/antinero/pe-yearly').then((v) => (peYearly = v));
	});

	const directEur = $derived(o.procedures.find((p) => p.label.includes('Απευθείας'))?.eur ?? 0);
	const topRows = $derived(
		o.top_contractors.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/antinero/contractor/${c.vat_number}`,
			sublabel: `${c.n_contracts} contracts`
		}))
	);
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
			<div class="lbl">contractors under a single awarding ministry (ΥΠΕΝ)</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(o.kpis.stated_eur).toLowerCase()}</div>
			<div class="lbl">
				total stated value of contracts<br />(excl. VAT)
			</div>
		</div>
	</div>
	<div class="dabar" role="img" aria-label="Share of contracts awarded directly">
		<div class="track">
			<div class="fill" style:width={`${o.kpis.pct_direct}%`}>
				<div class="danum">{pct(o.kpis.pct_direct)}</div>
				<div class="datext">of contracts were direct awards</div>
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
	subtitle="according to sums contracted via the programme — top {topRows.length} of {grInt(
		o.kpis.n_contractors
	)} contractors, {eurShort(o.kpis.total_eur)} in total"
	caveat="Consortium contract values are counted in full for each partner (maximum-exposure view)."
	anchor="top-contractors"
	methodology="stated-basis"
>
	<BarH rows={topRows} color="#2b2b2b" inside barHeight={22} />
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

</div>

<style>
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
	/* cards column + the direct-award bar beside the first card */
	.heroleft {
		display: grid;
		grid-template-columns: 300px 300px;
		gap: var(--sp-4);
		align-items: start;
	}
	.cards {
		/* three equal rows — every card the height of the tallest */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 300px;
		max-width: 100%;
	}
	/* the direct-award share bar, next to the contracts card */
	.dabar {
		grid-column: 2;
		grid-row: 1;
		width: 300px;
		max-width: 100%;
	}
	.dabar .track {
		height: 58px;
		background: #f2f2f2;
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
		padding: 0 12px;
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
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	@media (max-width: 900px) {
		.heroleft {
			grid-template-columns: 300px;
		}
		.dabar {
			grid-column: 1;
			grid-row: auto;
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
		font-size: clamp(28px, 3.2vw, 40px);
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
</style>
