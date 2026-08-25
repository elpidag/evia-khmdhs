<script lang="ts">
	/**
	 * KEY FINDINGS (named so by the user, 2026-08-23; the route stays
	 * /compare): Anti-nero beside the forest co-op contracts, in the dress of
	 * the three dataset pages — the hero with KPI cards and a kicker, short
	 * capital titles, findings in the lightbulbs, method and source in the
	 * caveats, the page's basis said once.
	 */
	import { peEn } from '$lib/transforms/regions';
	import BarH from '$lib/charts/BarH.svelte';
	import CompareHist from '$lib/charts/CompareHist.svelte';
	import PairedBars from '$lib/charts/PairedBars.svelte';
	import StateFunded from '$lib/charts/StateFunded.svelte';
	import ScatterLogLog from '$lib/charts/ScatterLogLog.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import { eur, eurShort, grInt, grNumber } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.cmp);

	// finding inputs — computed, never hardcoded
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
	/** a year with no contracts prints «—», not «0,00 €» */
	const dash = (v: number) => (v ? eurShort(v) : '—');
	const yearRows = (vals: number[]) =>
		c.years.map((y, i) => ({ label: String(y), value: vals[i] || 0 }));
	const peakYear = (vals: number[]) => {
		let bi = 0;
		vals.forEach((v, i) => {
			if (v > vals[bi]) bi = i;
		});
		return { year: c.years[bi], eur: vals[bi] || 0 };
	};
</script>

<svelte:head>
	<title>Key findings — Anti-nero beside the forest co-ops</title>
	<meta
		name="description"
		content="Greece's Anti-nero contractor programme beside the money that reached forest labour co-operatives — all € excl. VAT."
	/>
</svelte:head>

<section class="hero">
	<div class="cards">
		<div class="card antinero">
			<div class="num">{eurShort(c.antinero.total_eur).toLowerCase()}</div>
			<div class="lbl">Anti-nero — {grInt(c.antinero.n_contracts)} contracts, median {eurShort(c.antinero.median_eur).toLowerCase()}</div>
		</div>
		<div class="card dase">
			<div class="num">{eurShort(c.dase.total_eur).toLowerCase()}</div>
			<div class="lbl">forest co-ops — {grInt(c.dase.n_contracts)} contracts, median {eur(c.dase.median_eur)}</div>
		</div>
		<div class="card grey">
			<div class="num">{grNumber(c.ratio, 1)}×</div>
			<div class="lbl">the size of the gap, stated to stated — ≈{grInt(Math.round(c.antinero.median_eur / c.dase.median_eur))}× at the median</div>
		</div>
		<div class="card grey">
			<div class="num">{grInt(c.pipelines.vat_overlap.length)}</div>
			<div class="lbl">companies in both datasets — {grInt(c.pipelines.antinero.n_vats + c.pipelines.dase.n_vats)} entities, no shared ΑΦΜ</div>
		</div>
	</div>
	<div class="about">
		<div class="kicker">KEY FINDINGS</div>
		<p>
			The Anti-nero programme pays construction and technical companies. Forest labour
			co-operatives (ΔΑΣΕ) do woodland work for a living. The two flows run through the same
			ministry, into the same regions — and never touch. This page sets them side by side.
		</p>
		<p class="basis">
			Both sides are stated contract values excl. VAT (the co-op side deduplicated across
			amendment versions); payments are a separate layer on each dataset's own page. Anti-nero
			is one programme; the co-op dataset is every public contract won by a forest co-operative
			anywhere in the state since September 2021 —
			<a href="/methodology#compare-bases">basis</a> · <a href="/methodology#zero-overlap">overlap</a>.
		</p>
	</div>
</section>

<ChartFrame
	title="STATE-FUNDED, TWO WORLDS"
	insight={`Zero shared companies: ${grInt(c.pipelines.antinero.n_vats)} Anti-nero contractors and ${grInt(c.pipelines.dase.n_vats)} co-op-side entities (${grInt(c.pipelines.dase_n_coops)} of them curated co-operatives), and not one ΑΦΜ appears on both sides.`}
	caveat="The € scale carries a radius floor: the smallest contracts print larger than true scale, or they would vanish beside the €11M dots."
	anchor="pipelines"
	methodology="zero-overlap"
>
	<StateFunded
		dots={c.dots}
		nCompanies={c.pipelines.antinero.n_vats}
		nCoops={c.pipelines.dase.n_vats}
	/>
</ChartFrame>

<ChartFrame
	title="CONTRACT SIZES"
	insight={`Different universes: the median Anti-nero contract is ${eurShort(c.hist.antinero_median)}, the median co-op contract ${eur(c.hist.dase_median)} — the two distributions barely overlap.`}
	caveat="Contract-size distribution on shared log₂ brackets, each programme as % of its own contracts; both on stated values excl. VAT."
	anchor="distributions"
	methodology="compare-bases"
>
	<CompareHist hist={c.hist} />
</ChartFrame>

<ChartFrame
	title="WHERE BOTH FLOWS LAND"
	insight={`${topShared} gets millions from each programme; ${topDase} is co-op country. Each regional unit sits by its € from both programmes, log–log; the coloured gutters hold the units that see only one of them.`}
	caveat="Anti-nero regions curated per contract from its signed text, the co-op side derived from the awarding forest unit; a contract covering several units or signed by several firms is split equally."
	anchor="pe-scatter"
	methodology="even-split"
>
	<ScatterLogLog rows={c.by_pe} />
</ChartFrame>

<ChartFrame
	title="REGION BY REGION"
	insight={`The programmes weight the regions differently — the top ${grInt(Math.min(15, c.by_pe.length))} regional units, each programme's own share of its total beside the other's, absolute € printed.`}
	caveat={`The co-op side omits ${grInt(c.dase_unresolved.n)} multi-unit contracts (${eurShort(c.dase_unresolved.eur)}), honestly unresolved.`}
	anchor="pe-paired"
	methodology="dase-regions"
>
	<PairedBars rows={c.by_pe} antineroTotal={c.antinero.total_eur} daseTotal={c.dase.total_eur} />
</ChartFrame>

<ChartFrame
	title="MONEY PER YEAR"
	insight={`Anti-nero ramps up while the co-op money drifts down: Anti-nero peaked in ${peakYear(c.yearly.antinero).year} (${eurShort(peakYear(c.yearly.antinero).eur)}), the co-ops in ${peakYear(c.yearly.dase).year} (${eurShort(peakYear(c.yearly.dase).eur)}). Each programme on its own scale — a shared axis would erase the co-op bars entirely.`}
	caveat="Stated € excl. VAT by signature year, each side on its own scale."
	anchor="yearly"
	methodology="compare-bases"
>
	<div class="years">
		<div>
			<div class="sublabel antinero">ANTI-NERO</div>
			<BarH rows={yearRows(c.yearly.antinero)} color="var(--c-antinero)" inside barHeight={35} fmt={dash} />
		</div>
		<div>
			<div class="sublabel dase">FOREST CO-OPS</div>
			<BarH rows={yearRows(c.yearly.dase)} color="var(--c-dase)" inside barHeight={35} fmt={dash} />
		</div>
	</div>
</ChartFrame>

<style>
	/* the hero, in the dataset pages' geometry: cards left, the kicker and
	   the page's two paragraphs right */
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	.cards {
		display: grid;
		grid-template-columns: 268px 268px;
		grid-auto-rows: 1fr;
		gap: var(--sp-4);
		max-width: 100%;
	}
	.card {
		color: #fff;
		padding: var(--sp-4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	.card.antinero {
		background: var(--c-antinero);
	}
	.card.dase {
		background: var(--c-dase);
	}
	.card.grey {
		background: #6c6c6c;
	}
	.card .num {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: clamp(28px, 3.2vw, 36px);
		line-height: 0.95;
	}
	.card .lbl {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--ink);
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	.about p.basis {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.about p.basis a {
		color: var(--ink-soft);
	}
	/* the per-year pair: the ranking's bars, each side in its own hue */
	.years {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
	}
	.sublabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-2);
	}
	.sublabel.antinero {
		color: var(--c-antinero);
	}
	.sublabel.dase {
		color: var(--c-dase);
	}
	@media (max-width: 900px) {
		.hero,
		.years {
			grid-template-columns: 1fr;
		}
		.cards {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
