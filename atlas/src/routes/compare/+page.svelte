<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import CompareHist from '$lib/charts/CompareHist.svelte';
	import PairedBars from '$lib/charts/PairedBars.svelte';
	import ParallelPipelines from '$lib/charts/ParallelPipelines.svelte';
	import ScatterLogLog from '$lib/charts/ScatterLogLog.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.cmp);

	// finding-title inputs — computed, never hardcoded
	const topShared = $derived.by(() => {
		let best = null as null | { pe: string; v: number };
		for (const r of c.by_pe) {
			const v = Math.min(r.antinero_eur, r.dase_eur);
			if (!best || v > best.v) best = { pe: r.pe, v };
		}
		return peEn(best?.pe) || '';
	});
	const topDase = $derived.by(() => {
		let best = null as null | { pe: string; v: number };
		for (const r of c.by_pe)
			if (!best || r.dase_eur > best.v) best = { pe: r.pe, v: r.dase_eur };
		return peEn(best?.pe) || '';
	});

	const yearMax = $derived(Math.max(...c.yearly.antinero, ...c.yearly.dase.map(() => 0), 1));
	const daseYearMax = $derived(Math.max(...c.yearly.dase, 1));
</script>

<svelte:head>
	<title>Anti-nero vs ΔΑΣΕ — two money pipelines for the same forests</title>
	<meta
		name="description"
		content="Comparing Greece's Anti-nero contractor programme with the money that reached forest labour co-operatives — all € excl. VAT."
	/>
</svelte:head>

<hgroup class="lede">
	<h1>Two money pipelines for the same forests</h1>
	<p class="standfirst">
		The Anti-nero programme pays construction and technical companies. Forest labour
		co-operatives (ΔΑΣΕ) do woodland work for a living. The two flows run through the same
		ministry, into the same regions — and never touch.
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(c.antinero.total_eur)}
		label="Anti-nero, {grInt(c.antinero.n_contracts)} contracts"
		compare="median contract {eurShort(c.antinero.median_eur)}"
		basis="stated € excl. VAT"
		color="var(--c-antinero)"
	/>
	<StatPair
		value={eurShort(c.dase.total_eur)}
		label="ΔΑΣΕ co-ops, {grInt(c.dase.n_contracts)} contracts"
		compare="median contract {eur(c.dase.median_eur)}"
		basis="stated € excl. VAT · payments cover only part of the population"
		color="var(--c-dase)"
	/>
	<StatPair
		value="{c.ratio}×"
		label="the size of the gap"
		compare="≈{Math.round(c.antinero.median_eur / c.dase.median_eur)}× at the median"
	/>
	<StatPair
		value={grInt(c.pipelines.vat_overlap.length)}
		label="companies in both datasets"
		compare="{grInt(c.pipelines.antinero.n_vats + c.pipelines.dase.n_vats)} entities, zero shared ΑΦΜ"
	/>
</KpiRow>

<ChartFrame
	title="Same ministry, same forests — zero shared companies"
	subtitle="Every Anti-nero contractor (left) and every ΔΑΣΕ entity (right), sized by €. {grInt(
		c.pipelines.dase_n_coops
	)} of the {grInt(c.pipelines.dase.n_vats)} ΔΑΣΕ entities are curated co-operatives."
	caveat="Contract € split evenly across partners so each column sums to its programme total; ΑΦΜ compared canonicalised on both sides; awarders matched by name, never VAT (090273987 is shared by two bodies)."
	anchor="pipelines"
	methodology="zero-overlap"
>
	<ParallelPipelines data={c.pipelines} />
</ChartFrame>

<ChartFrame
	title="Different universes: medians of {eurShort(c.hist.antinero_median)} vs {eur(
		c.hist.dase_median
	)}"
	subtitle="Contract-size distribution on shared log₂ bins, as % of each programme's own contracts."
	caveat="Both programmes on the same basis: stated contract values, excl. VAT."
	anchor="distributions"
	methodology="compare-bases"
>
	<CompareHist hist={c.hist} />
</ChartFrame>

<ChartFrame
	title="Where both flows land: {topShared} gets millions from each — {topDase} is co-op country"
	subtitle="Each regional unit by its € from both programmes (log–log). Colour-coded gutters hold the one-sided regional units."
	anchor="pe-scatter"
	methodology="even-split"
>
	<ScatterLogLog rows={c.by_pe} />
</ChartFrame>

<ChartFrame
	title="Region by region, the programmes weight differently"
	subtitle="Top {Math.min(15, c.by_pe.length)} regional units — each programme's own share of its total, absolute € printed."
	caveat="ΔΑΣΕ side omits {grInt(c.dase_unresolved.n)} multi-regional-unit contracts ({eurShort(
		c.dase_unresolved.eur
	)}, honestly unresolved)."
	anchor="pe-paired"
	methodology="dase-regions"
>
	<PairedBars
		rows={c.by_pe}
		antineroTotal={c.antinero.total_eur}
		daseTotal={c.dase.total_eur}
	/>
</ChartFrame>

<ChartFrame
	title="Anti-nero ramps up while ΔΑΣΕ money drifts down"
	subtitle="Yearly € — each programme on its own scale (a shared axis would erase the ΔΑΣΕ bars entirely)."
	anchor="yearly"
	methodology="compare-bases"
>
	<div class="years">
		<div>
			<h3 class="antinero">Anti-nero (stated €, net)</h3>
			{#each c.years as y, i (y)}
				<div class="yrow">
					<span class="ylabel">{y}</span>
					<div class="ybar antinero" style:width={`${(88 * c.yearly.antinero[i]) / yearMax}%`}></div>
					<span class="yval">{c.yearly.antinero[i] ? eurShort(c.yearly.antinero[i]) : '—'}</span>
				</div>
			{/each}
		</div>
		<div>
			<h3 class="dase">ΔΑΣΕ (stated €, net)</h3>
			{#each c.years as y, i (y)}
				<div class="yrow">
					<span class="ylabel">{y}</span>
					<div class="ybar dase" style:width={`${(88 * c.yearly.dase[i]) / daseYearMax}%`}></div>
					<span class="yval">{c.yearly.dase[i] ? eurShort(c.yearly.dase[i]) : '—'}</span>
				</div>
			{/each}
		</div>
	</div>
</ChartFrame>

<section class="notes">
	<h2>Reading this page honestly</h2>
	<ul>
		<li>
			<strong>Same value basis.</strong> Both sides show stated contract values, excl. VAT
			(ΔΑΣΕ deduplicated across amendment versions). Payments are a separate layer on each
			dataset's own pages. The {c.ratio}× headline is stated-vs-stated.
		</li>
		<li>
			<strong>Different populations.</strong> Anti-nero is one programme; the ΔΑΣΕ dataset is
			every public contract won by a forest co-op anywhere in the state since 2021-09.
		</li>
		<li>
			<strong>Regional-unit (Π.Ε.) derivation differs.</strong> Anti-nero regions are hand-curated per contract;
			ΔΑΣΕ regions derive from the awarding forest unit.
		</li>
		<li>
			Full definitions on the <a href="/methodology">methodology page</a>.
		</li>
	</ul>
</section>

<style>
	.lede {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
	}
	.years {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
	}
	@media (max-width: 900px) {
		.years {
			grid-template-columns: 1fr;
		}
	}
	.years h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
	}
	.years h3.antinero {
		color: var(--c-antinero);
	}
	.years h3.dase {
		color: var(--c-dase);
	}
	.yrow {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		margin-bottom: 4px;
	}
	.ylabel {
		width: 3rem;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.ybar {
		height: 14px;
		border-radius: 2px;
		min-width: 1px;
	}
	.ybar.antinero {
		background: var(--c-antinero);
	}
	.ybar.dase {
		background: var(--c-dase);
	}
	.yval {
		font-size: var(--fs-12);
		color: var(--ink-soft);
		white-space: nowrap;
	}
	.notes {
		max-width: var(--prose-w);
		border-top: 2px solid var(--line-strong);
		padding-top: var(--sp-4);
	}
	.notes li {
		margin-bottom: var(--sp-2);
		font-size: var(--fs-14);
	}
</style>
