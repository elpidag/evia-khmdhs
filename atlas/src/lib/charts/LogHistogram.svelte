<script lang="ts">
	import { eurShort, grInt } from '$lib/transforms/format';

	interface Props {
		labels: string[];
		counts: number[];
		/** bin edges in €; thresholds are drawn at their edge positions */
		edges: number[];
		thresholds?: { v: number; label: string }[];
		color?: string;
		/** auto-note: name the modal bin */
		note?: boolean;
		/** € value to mark with a median line, log-interpolated inside its bin */
		median?: number | null;
	}
	let {
		labels,
		counts,
		edges,
		thresholds = [],
		color = 'var(--accent)',
		note = true,
		median = null
	}: Props = $props();

	let width = $state(900);
	const height = 240;
	const M = { top: 26, right: 8, bottom: 40, left: 8 };

	const n = $derived(counts.length);
	const bw = $derived((width - M.left - M.right) / n);
	const maxC = $derived(Math.max(...counts, 1));
	const yOf = (c: number) => M.top + (height - M.top - M.bottom) * (1 - c / maxC);

	const modal = $derived(counts.indexOf(maxC));
	// a threshold at edges[i] sits at the left edge of bin i
	function thresholdX(v: number): number | null {
		const i = edges.indexOf(v);
		return i === -1 ? null : M.left + i * bw;
	}
	// log-interpolated position of an arbitrary € value inside its bin
	const medianX = $derived.by(() => {
		if (!median) return null;
		for (let i = 0; i < edges.length - 1; i++) {
			if (median >= edges[i] && median < edges[i + 1]) {
				const lo = Math.max(edges[i], 1);
				const frac = Math.log(median / lo) / Math.log(edges[i + 1] / lo);
				return M.left + (i + frac) * bw;
			}
		}
		return null;
	});
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each counts as c, i (i)}
			<rect
				x={M.left + i * bw + 1}
				y={yOf(c)}
				width={bw - 2}
				height={height - M.bottom - yOf(c)}
				fill={i === modal ? color : 'color-mix(in srgb, var(--ink) 26%, transparent)'}
			/>
			{#if c > 0}
				<text class="count" x={M.left + i * bw + bw / 2} y={yOf(c) - 4}>{c}</text>
			{/if}
			{#if i % 2 === 0 || n < 10}
				<text class="bin" x={M.left + i * bw + bw / 2} y={height - 22}>{labels[i]}</text>
			{/if}
		{/each}

		{#each thresholds as th (th.v)}
			{@const tx = thresholdX(th.v)}
			{#if tx !== null}
				<line class="threshold" x1={tx} x2={tx} y1={M.top - 4} y2={height - M.bottom} />
				<text class="threshold-label" x={tx + 4} y={M.top - 8}>{th.label}</text>
			{/if}
		{/each}

		{#if medianX !== null}
			<line class="median" x1={medianX} x2={medianX} y1={M.top - 4} y2={height - M.bottom} />
			<text class="median-label" x={medianX + 4} y={M.top - 8}>
				median {eurShort(median!)}
			</text>
		{/if}

		{#if note && modal >= 0}
			<text class="note" x={width - M.right} y={height - 6} text-anchor="end">
				most common bracket: {labels[modal]} € ({grInt(maxC)} contracts)
			</text>
		{/if}
	</svg>
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	.count {
		font-size: 10px;
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	.bin {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: middle;
	}
	.threshold {
		stroke: var(--c-threshold);
		stroke-dasharray: 4 3;
		stroke-width: 1.2;
	}
	.threshold-label {
		font-size: 11px;
		fill: var(--c-threshold);
	}
	.note {
		font-size: 11px;
		fill: var(--ink-soft);
		font-style: italic;
	}
	.median {
		stroke: var(--ink);
		stroke-width: 1;
		opacity: 0.55;
	}
	.median-label {
		font-size: 11px;
		fill: var(--ink);
	}
</style>
