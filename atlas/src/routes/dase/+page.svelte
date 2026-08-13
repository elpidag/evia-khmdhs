<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import ChoroLegend from '$lib/maps/ChoroLegend.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_HOME, makeChoro } from '$lib/maps/useGeo';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import { apiGetCached, type DaseSwarm } from '$lib/api';
	import { eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	let swarm = $state.raw<DaseSwarm | null>(null);
	$effect(() => {
		apiGetCached<DaseSwarm>(fetch, '/api/dase/swarm').then((v) => (swarm = v));
	});

	const peValues = $derived(new Map(o.by_pe.regions.map((r) => [r.pe, r.eur])));
	const peRows = $derived(new Map(o.by_pe.regions.map((r) => [r.pe, r])));
	const peMax = $derived(Math.max(...o.by_pe.regions.map((r) => r.eur)));
	const choro = $derived(makeChoro(RAMP_HOME, peMax));

	const coopRows = $derived(
		o.top_coops.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/dase/coop/${c.vat}`,
			sublabel: `${c.n_contracts} contracts · ${c.n_units} units · ${pct(c.pct_direct)} direct`
		}))
	);
	const orgRows = $derived(
		o.top_orgs.map((c) => ({
			label: c.name,
			value: c.total_eur,
			sublabel: `${grInt(c.n_contracts)} contracts`
		}))
	);
	const unitRows = $derived(
		o.top_units.map((c) => ({
			label: c.name,
			value: c.total_eur,
			sublabel: `${grInt(c.n_contracts)} contracts`
		}))
	);
	const yearRows = $derived(
		o.yearly.map((y) => ({
			label: y.year,
			value: y.eur,
			sublabel: `${grInt(y.n)} contracts`
		}))
	);
	const cpvRows = $derived(
		o.cpvs.map((c) => ({
			label: `${c.label}${c.noise ? ' — registry keying noise' : ''}`,
			value: c.n_contracts,
			sublabel: c.cpv
		}))
	);

	// finding-title inputs — computed from the payload, never hardcoded
	const topPe = $derived(
		[...o.by_pe.regions].sort((a, b) => b.eur - a.eur)[0]?.pe?.replace('Π.Ε. ', '') ?? ''
	);
	const topYear = $derived([...o.yearly].sort((a, b) => b.eur - a.eur)[0]?.year ?? '');
	const topOrgShare = $derived(
		o.top_orgs.length ? (100 * o.top_orgs[0].n_contracts) / o.kpis.n_contracts : 0
	);
	const cpvNoiseN = $derived(o.cpvs.find((c) => c.noise)?.n_contracts ?? 0);

	// hero bar fills — data-proportional
	const paidPct = $derived((o.kpis.paid_eur / o.kpis.total_eur) * 100);

	function peTip(pe: string): string {
		const r = peRows.get(pe);
		if (!r) return `<strong>${pe}</strong><br>no ΔΑΣΕ contracts recorded`;
		return `<strong>${pe}</strong><br>${grInt(r.n_contracts)} contracts<br>${eur(r.eur)} stated`;
	}
</script>

<svelte:head>
	<title>ΔΑΣΕ — forest labour co-operatives</title>
	<meta
		name="description"
		content="Every Greek public contract won by a forest labour co-operative since Sept 2021: {grInt(
			o.kpis.n_contracts
		)} contracts, {eurShort(o.kpis.total_eur)} stated (excl. VAT)."
	/>
</svelte:head>

<div class="dasep">
<section class="hero">
	<div class="heroleft">
	<div class="cards">
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contracts)}</div>
			<div class="lbl">live contracts since Sept 2021</div>
		</div>
		<div class="card">
			<div class="num">{grInt(o.kpis.n_coops)}</div>
			<div class="lbl">forest labour co-operatives</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(o.kpis.total_eur).toLowerCase()}</div>
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
		<div class="kicker">THE CO-OPERATIVES</div>
		<p>
			Every public contract won by a forest labour co-operative (ΔΑ.Σ.Ε., ν.4423/2016) since
			September 2021 — logging, clearing and tending work in the same forests the Anti-nero
			millions target, at a fraction of the size: the median contract is {eur(
				o.kpis.median_eur
			)} and {pct(o.kpis.pct_direct)} went by direct award, from {grInt(o.kpis.n_orgs)} awarding
			bodies through {grInt(o.kpis.n_units)} units. Of the {eurShort(o.kpis.total_eur)} stated,
			{eurShort(o.kpis.paid_eur)} shows as paid ({grInt(o.kpis.n_payments)} payment orders) —
			payments are posted for {grInt(o.kpis.n_paid_contracts)} of {grInt(
				o.kpis.n_contracts
			)} contracts, a registry practice, not a delivery record. {grInt(
				o.kpis.n_cancelled
			)} cancelled and {grInt(o.kpis.n_superseded)} superseded versions are excluded, and one
			co-op's up to {o.kpis.max_name_variants} registry spellings merge on the canonical ΑΦΜ —
			<a href="/methodology#dase-dedup">methodology</a>.
		</p>
	</div>
</section>

<ChartFrame
	title="MAP"
	subtitle="Co-op work concentrates in a handful of forest districts — {topPe} far above all. Stated € per regional unit, derived from the awarding forest unit."
	caveat="{grInt(o.by_pe.unresolved.n)} ΑΔΜΗΕ power-line contracts span multiple Π.Ε. and stay honestly unresolved ({eurShort(
		o.by_pe.unresolved.eur
	)})."
	anchor="dase-map"
	methodology="dase-regions"
>
	<div class="map-holder">
		<PaperMap colorOf={(pe) => choro(peValues.get(pe) ?? 0)} tipOf={peTip}>
			{#snippet legend()}
				<ChoroLegend ramp={RAMP_HOME} max={peMax} title="€ of co-op contracts" />
			{/snippet}
		</PaperMap>
	</div>
</ChartFrame>

<Defer height={400}>
{#if swarm}
	<ChartFrame
		title="CONTRACT VALUES"
		subtitle="Every live contract ({grInt(
			o.kpis.n_contracts
		)}) as one dot on a log scale (stated €, excl. VAT), coloured by year — half sit below {eur(
			o.kpis.median_eur
		)}. Hover to inspect, click through."
		caveat="Stated values excl. VAT, deduplicated (cancelled and superseded versions excluded)."
		anchor="dase-swarm"
		methodology="dase-dedup"
	>
		<BeeswarmCanvas data={swarm} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 380px"></div>
{/if}
</Defer>

<div class="pair">
	<ChartFrame
		title="MONEY PER YEAR"
		subtitle="Stated € and contract counts per signature year — {topYear} carried the biggest υλοτομία money; volumes stay high since."
		anchor="dase-yearly"
	>
		<BarH rows={yearRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="SIZE DISTRIBUTION"
		subtitle="{grInt(o.histogram.n)} live contracts by stated value — small sums, tight distribution."
		anchor="dase-hist"
	>
		<LogHistogram
			labels={o.histogram.labels}
			counts={o.histogram.counts}
			edges={o.histogram.edges}
			color="var(--c-dase)"
			median={o.histogram.median}
		/>
	</ChartFrame>
</div>

<ChartFrame
	title="RANKING OF CO-OPS"
	subtitle="according to sums contracted — top {coopRows.length} of {grInt(
		o.kpis.n_coops
	)} co-operatives collect {eurShort(coopRows.reduce((s, r) => s + r.value, 0))} of the {eurShort(
		o.kpis.total_eur
	)}, merged across registry spellings by canonical ΑΦΜ"
	caveat="Consortium values counted in full for each partner (rare here: {grInt(o.kpis.n_consortium)} of {grInt(o.kpis.n_contracts)} contracts)."
	anchor="top-coops"
	methodology="canonical-vat"
>
	<BarH rows={coopRows} color="var(--c-dase)" inside barHeight={22} />
</ChartFrame>

<div class="pair">
	<ChartFrame
		title="AWARDING BODIES"
		subtitle="{o.top_orgs[0]?.name ?? 'ΥΠΕΝ'} awards {pct(topOrgShare)} of the contracts; other bodies share the rest (grouped by name — registry VATs collide)."
		anchor="dase-orgs"
		methodology="org-names"
	>
		<BarH rows={orgRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="AWARDING UNITS"
		subtitle="Top awarding units by stated € — Δασαρχεία are the working level."
		anchor="dase-units"
	>
		<BarH rows={unitRows} color="var(--c-dase)" />
	</ChartFrame>
</div>

<ChartFrame
	title="CPV MIX"
	subtitle="Top CPV codes by contract count — υλοτομία dominates."
	caveat="{grInt(cpvNoiseN)} υλοτομικά rows carry a miskeyed insurance CPV (66519300-4) — flagged, never counted as insurance."
	anchor="dase-cpvs"
	methodology="dase-cpv-noise"
>
	<BarH rows={cpvRows} color="var(--c-dase)" fmt={(v) => `${grInt(v)} contracts`} />
</ChartFrame>

</div>

<style>
	/* every section title follows the sponsored-works kicker, in the
	   ΔΑΣΕ dataset colour (green) */
	.dasep :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-dase);
	}
	/* the paper map takes the shared ground */
	.dasep :global(.map) {
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
	/* cards column + the bars/paid column beside it — same equal-column
	   geometry as the Anti-nero hero */
	.heroleft {
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
	   card's row, the paid card fills the third row */
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
	.dabar .track {
		height: 100%;
		background: #fff;
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.dabar .fill {
		height: 100%;
		background: var(--c-dase);
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
	/* paid vs stated: green fill rises to the paid share of the stated €;
	   the unfilled remainder reads as light grey, no outer border */
	.paidcard {
		grid-row: 3;
		position: relative;
		background: #fff;
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.paidcard .pfill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--c-dase);
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
		/* matches the card numbers' cap */
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
		background: var(--c-dase);
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
		/* same cap as the other dataset pages' KPI cards */
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
		color: var(--c-dase);
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
	.map-holder {
		max-width: 44rem;
	}
</style>
