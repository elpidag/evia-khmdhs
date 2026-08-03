<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import ChoroLegend from '$lib/maps/ChoroLegend.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_HOME, makeChoro } from '$lib/maps/useGeo';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
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

<hgroup class="lede">
	<h1>The other forest workforce: ΔΑΣΕ co-operatives</h1>
	<p class="standfirst">
		Every public contract won by a forest labour co-operative (ΔΑ.Σ.Ε., ν.4423/2016) since
		September 2021 — logging, clearing and tending work in the same forests the Anti-nero
		millions target, at a fraction of the contract size.
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(o.kpis.total_eur)}
		label="total stated value of contracts"
		compare="excl. VAT · {grInt(o.kpis.n_cancelled)} cancelled + {o.kpis.n_superseded} superseded excluded"
		basis="Σ stated values, live population"
		color="var(--c-dase)"
	/>
	<StatPair
		value={eurShort(o.kpis.paid_eur)}
		label="actually paid so far"
		compare="excl. VAT · {grInt(o.kpis.n_payments)} payment orders"
		basis="payments posted for {grInt(o.kpis.n_paid_contracts)} of {grInt(
			o.kpis.n_contracts
		)} contracts — registry practice, not delivery"
		color="var(--c-dase)"
	/>
	<StatPair
		value={eur(o.kpis.median_eur)}
		label="median contract"
		compare="excl. VAT"
		basis="stated value, live population"
	/>
	<StatPair value={grInt(o.kpis.n_contracts)} label="live contracts" compare="since Sept 2021" />
	<StatPair
		value={grInt(o.kpis.n_coops)}
		label="co-operatives (canonical ΑΦΜ)"
		compare="the same co-op appears under up to {o.kpis.max_name_variants} registry spellings"
	/>
	<StatPair
		value={pct(o.kpis.pct_direct)}
		label="direct awards"
		compare="{grInt(o.kpis.n_orgs)} awarding bodies · {grInt(o.kpis.n_units)} units"
	/>
</KpiRow>

<ChartFrame
	title="Co-op work concentrates in a handful of forest districts — {topPe} far above all"
	subtitle="Stated € per regional unit, derived from the awarding forest unit."
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
		title="{grInt(o.kpis.n_contracts)} small contracts: half sit below {eur(o.kpis.median_eur)}"
		subtitle="Every live contract as one dot on a log scale, coloured by year. Hover to inspect, click through."
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
		title="{topYear} carried the biggest υλοτομία money; volumes stay high since"
		subtitle="Stated € and contract counts per signature year."
		anchor="dase-yearly"
	>
		<BarH rows={yearRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="Small sums, tight distribution"
		subtitle="{grInt(o.histogram.n)} live contracts by stated value."
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
	title="{grInt(coopRows.length)} co-ops collect {eurShort(coopRows.reduce((s, r) => s + r.value, 0))} of the {eurShort(
		o.kpis.total_eur
	)}"
	subtitle="Top {coopRows.length} co-operatives by stated €, merged across registry spellings by canonical ΑΦΜ."
	caveat="Consortium values counted in full for each partner (rare here: {grInt(o.kpis.n_consortium)} of {grInt(o.kpis.n_contracts)} contracts)."
	anchor="top-coops"
	methodology="canonical-vat"
>
	<BarH rows={coopRows} color="var(--c-dase)" />
</ChartFrame>

<div class="pair">
	<ChartFrame
		title="{o.top_orgs[0]?.name ?? 'ΥΠΕΝ'} awards {pct(topOrgShare)} of the contracts; other bodies share the rest"
		subtitle="Top awarding organisations (grouped by name — registry VATs collide)."
		anchor="dase-orgs"
		methodology="org-names"
	>
		<BarH rows={orgRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="Δασαρχεία are the working level"
		subtitle="Top awarding units by stated €."
		anchor="dase-units"
	>
		<BarH rows={unitRows} color="var(--c-dase)" />
	</ChartFrame>
</div>

<ChartFrame
	title="Υλοτομία dominates the CPV mix"
	subtitle="Top CPV codes by contract count."
	caveat="{grInt(cpvNoiseN)} υλοτομικά rows carry a miskeyed insurance CPV (66519300-4) — flagged, never counted as insurance."
	anchor="dase-cpvs"
	methodology="dase-cpv-noise"
>
	<BarH rows={cpvRows} color="var(--c-dase)" fmt={(v) => `${grInt(v)} contracts`} />
</ChartFrame>

<style>
	.lede {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
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
