<script lang="ts">
	/**
	 * MONEY PER YEAR for the story's KEY FINDINGS rail (the author,
	 * 2026-09-04: «vertical, and mix the two colours»): one group of two
	 * columns per year — Anti-nero in the ink, the forest co-ops in the
	 * green — each column as high as that programme's SHARE OF ITS OWN
	 * TOTAL, so a €30M programme and a €634M one read on one drawing, the
	 * € printed on every column. The dataset pages keep their horizontal
	 * bars; this drawing exists for the story alone.
	 */
	import { eurTiny, grInt } from '$lib/transforms/format';

	let { years, a, d }: { years: (string | number)[]; a: number[]; d: number[] } = $props();

	let width = $state(540);
	const height = 300;
	const M = { top: 26, right: 6, bottom: 26, left: 6 };
	const totalA = $derived(a.reduce((s, v) => s + (v || 0), 0));
	const totalD = $derived(d.reduce((s, v) => s + (v || 0), 0));
	const shareA = $derived(a.map((v) => (totalA ? (v || 0) / totalA : 0)));
	const shareD = $derived(d.map((v) => (totalD ? (v || 0) / totalD : 0)));
	const maxShare = $derived(Math.max(...shareA, ...shareD, 0.01));
	const n = $derived(years.length);
	const gw = $derived((width - M.left - M.right) / Math.max(1, n));
	const gap = 4;
	const bw = $derived((gw - 3 * gap) / 2);
	const yOf = (s: number) => M.top + (height - M.top - M.bottom) * (1 - s / maxShare);
	const label = (v: number) => (v ? eurTiny(v) : '—');
</script>

<div class="wrap" bind:clientWidth={width}>
	<ul class="legend">
		<li><i class="a"></i>Anti-nero</li>
		<li><i class="d"></i>forest co-ops</li>
		<li class="faint">column height: share of each programme's own total</li>
	</ul>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px" role="img" aria-label="Money per year, both programmes">
		{#each years as y, i (y)}
			{@const x0 = M.left + i * gw + gap}
			{@const ya = yOf(shareA[i])}
			{@const yd = yOf(shareD[i])}
			<rect class="a" x={x0} y={ya} width={bw} height={height - M.bottom - ya} />
			<rect class="d" x={x0 + bw + gap} y={yd} width={bw} height={height - M.bottom - yd} />
			<text class="v a" x={x0 + bw / 2} y={ya - 4}>{label(a[i])}</text>
			<text class="v d" x={x0 + bw + gap + bw / 2} y={yd - 4}>{label(d[i])}</text>
			<text class="year" x={x0 + bw + gap / 2} y={height - 8}>{y}</text>
		{/each}
	</svg>
	<p class="sr">
		{#each years as y, i (y)}
			{y}: Anti-nero {grInt(a[i] || 0)} €, co-ops {grInt(d[i] || 0)} €.
		{/each}
	</p>
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	rect.a {
		fill: var(--c-antinero);
		opacity: 0.85;
	}
	rect.d {
		fill: var(--c-dase);
		opacity: 0.85;
	}
	.v {
		font-size: 10px;
		font-weight: 700;
		text-anchor: middle;
	}
	.v.a {
		fill: var(--c-antinero);
	}
	.v.d {
		fill: var(--c-dase);
	}
	.year {
		font-size: 11px;
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	.legend {
		list-style: none;
		margin: 0 0 var(--sp-3);
		padding: var(--sp-2) var(--sp-3);
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px var(--sp-6, 1.5rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.legend li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.legend i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex: none;
	}
	.legend i.a {
		background: var(--c-antinero);
	}
	.legend i.d {
		background: var(--c-dase);
	}
	.legend .faint {
		font-size: var(--fs-12);
	}
	.sr {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		margin: 0;
	}
	.wrap {
		position: relative;
	}
</style>
