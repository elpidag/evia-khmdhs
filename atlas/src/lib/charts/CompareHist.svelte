<script lang="ts">
	import type { ComparePayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';

	let { hist }: { hist: ComparePayload['hist'] } = $props();

	let width = $state(900);
	const height = 280;
	const M = { top: 30, right: 8, bottom: 40, left: 36 };

	const n = $derived(hist.labels.length);
	const bw = $derived((width - M.left - M.right) / n);
	const maxPct = $derived(Math.max(...hist.antinero_pct, ...hist.dase_pct, 1));
	const yOf = (p: number) => M.top + (height - M.top - M.bottom) * (1 - p / maxPct);

	/** log-interpolated x for a € value within the shared bin edges */
	function xOf(v: number): number {
		const e = hist.edges;
		for (let i = 0; i < e.length - 1; i++) {
			if (v >= e[i] && v < e[i + 1]) {
				const lo = Math.max(e[i], 1);
				const frac = Math.log(v / lo) / Math.log(e[i + 1] / lo);
				return M.left + (i + frac) * bw;
			}
		}
		return M.left + (n - 0.5) * bw;
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each hist.labels as label, i (label)}
			<rect
				class="a"
				x={M.left + i * bw + 1}
				y={yOf(hist.antinero_pct[i])}
				width={bw / 2 - 2}
				height={height - M.bottom - yOf(hist.antinero_pct[i])}
			/>
			<rect
				class="d"
				x={M.left + i * bw + bw / 2 + 1}
				y={yOf(hist.dase_pct[i])}
				width={bw / 2 - 2}
				height={height - M.bottom - yOf(hist.dase_pct[i])}
			/>
			{#if i % 2 === 0}
				<text class="bin" x={M.left + i * bw + bw / 2} y={height - 22}>{label}</text>
			{/if}
		{/each}

		{#each [10, 20, 30] as t (t)}
			{#if t < maxPct}
				<text class="axis" x={M.left - 4} y={yOf(t) + 3} text-anchor="end">{t}%</text>
			{/if}
		{/each}

		<line class="median a" x1={xOf(hist.antinero_median)} x2={xOf(hist.antinero_median)}
			y1={M.top - 4} y2={height - M.bottom} />
		<text class="median-label a" x={xOf(hist.antinero_median) - 5} y={M.top - 8}
			text-anchor="end">
			Anti-nero median {eurShort(hist.antinero_median)}
		</text>
		<line class="median d" x1={xOf(hist.dase_median)} x2={xOf(hist.dase_median)}
			y1={M.top - 4} y2={height - M.bottom} />
		<text class="median-label d" x={xOf(hist.dase_median) + 5} y={M.top - 8}>
			ΔΑΣΕ median {eurShort(hist.dase_median)}
		</text>
	</svg>
	<div class="legend">
		<span><i class="a"></i>Anti-nero ({hist.antinero_n} contracts)</span>
		<span><i class="d"></i>ΔΑΣΕ ({hist.dase_n})</span>
		<span class="faint">y-axis: % of each programme's own contracts</span>
	</div>
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
	.bin {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: middle;
	}
	.axis {
		font-size: 11px;
		fill: var(--ink-faint);
	}
	.median {
		stroke-dasharray: 4 3;
		stroke-width: 1.4;
	}
	.median.a {
		stroke: var(--c-antinero);
	}
	.median.d {
		stroke: var(--c-dase);
	}
	.median-label {
		font-size: 11px;
	}
	.median-label.a {
		fill: var(--c-antinero);
	}
	.median-label.d {
		fill: var(--c-dase);
	}
	.legend {
		display: flex;
		gap: var(--sp-4);
		flex-wrap: wrap;
		font-size: var(--fs-12);
		color: var(--ink-soft);
		margin-top: var(--sp-1);
	}
	.legend i {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		margin-right: 4px;
	}
	.legend i.a {
		background: var(--c-antinero);
	}
	.legend i.d {
		background: var(--c-dase);
	}
	.faint {
		color: var(--ink-faint);
	}
</style>
