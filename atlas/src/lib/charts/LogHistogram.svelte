<script lang="ts">
	import { eurShort, grInt } from '$lib/transforms/format';
	import { binPosition } from '$lib/transforms/histogram';

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
		height?: number;
		/** optional per-bin breakdown: one count per category, in `segColors`
		 *  order. Given these, each bar is drawn as a stack instead of one
		 *  solid rect and the modal-bin highlight steps aside — the colour
		 *  then carries the category, not the mode. Segments are expected to
		 *  sum to their bin's count; any shortfall renders in the base colour
		 *  on top, so an incomplete breakdown shows rather than hides. */
		segments?: number[][] | null;
		segColors?: string[];
	}
	let {
		labels,
		counts,
		edges,
		thresholds = [],
		color = 'var(--accent)',
		note = true,
		median = null,
		height = 240,
		segments = null,
		segColors = []
	}: Props = $props();

	let width = $state(900);
	// Reference-line labels (median, statutory thresholds) get a row of their
	// own above the bar counts: both used to be drawn at the same height, so
	// a median falling near the modal bar overprinted that bar's count.
	const REF_Y = 14;
	const hasRefLabels = $derived(median !== null || thresholds.length > 0);
	const M = $derived({ top: hasRefLabels ? 40 : 26, right: 8, bottom: 40, left: 8 });

	const n = $derived(counts.length);
	const bw = $derived((width - M.left - M.right) / n);
	const maxC = $derived(Math.max(...counts, 1));
	const yOf = (c: number) => M.top + (height - M.top - M.bottom) * (1 - c / maxC);

	const modal = $derived(counts.indexOf(maxC));
	// pixels per contract — the unit every stacked segment is measured in
	const unit = $derived((height - M.top - M.bottom) / maxC);
	const stacks = $derived.by(() => {
		if (!segments) return null;
		return counts.map((c, i) => {
			const rows = segments[i] ?? [];
			const out: { y: number; h: number; fill: string }[] = [];
			let acc = 0;
			for (let j = 0; j < rows.length; j++) {
				if (rows[j] <= 0) continue;
				out.push({
					y: height - M.bottom - (acc + rows[j]) * unit,
					h: rows[j] * unit,
					fill: segColors[j] ?? color
				});
				acc += rows[j];
			}
			if (c - acc > 0) {
				// uncategorised remainder — drawn, never dropped
				out.push({ y: yOf(c), h: (c - acc) * unit, fill: color });
			}
			return out;
		});
	});
	// a threshold at edges[i] sits at the left edge of bin i
	function thresholdX(v: number): number | null {
		const i = edges.indexOf(v);
		return i === -1 ? null : M.left + i * bw;
	}
	// log-interpolated position inside its bin — the SAME function the
	// beeswarm places its dots with, so the median coincides across the two
	const medianX = $derived(median ? binPosition(median, edges, M.left, bw) : null);
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each counts as c, i (i)}
			{#if stacks}
				{#each stacks[i] as s, j (j)}
					<rect x={M.left + i * bw + 1} y={s.y} width={bw - 2} height={s.h} fill={s.fill} />
				{/each}
			{:else}
				<rect
					x={M.left + i * bw + 1}
					y={yOf(c)}
					width={bw - 2}
					height={height - M.bottom - yOf(c)}
					fill={i === modal ? color : 'color-mix(in srgb, var(--ink) 26%, transparent)'}
				/>
			{/if}
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
				<text class="threshold-label" x={tx + 4} y={REF_Y}>{th.label}</text>
			{/if}
		{/each}

		{#if medianX !== null}
			<line class="median" x1={medianX} x2={medianX} y1={M.top - 4} y2={height - M.bottom} />
			<text class="median-label" x={medianX} y={REF_Y}>
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
	/* the median reads identically here and on the beeswarm this chart
	   toggles with — same dash, same weight, same lettering */
	.median {
		stroke: var(--ink);
		stroke-width: 2.5;
		stroke-dasharray: 7 5;
	}
	.median-label {
		font-size: 12px;
		font-weight: 800;
		fill: var(--ink);
		text-anchor: middle;
	}
</style>
