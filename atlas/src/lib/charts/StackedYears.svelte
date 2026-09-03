<script lang="ts">
	import { cssLuminance } from '$lib/theme.svelte';
	/**
	 * Stacked columns per calendar year (user, 2026-08-23, after the Common
	 * Wealth «Complaints have tripled» form): one column per year, its
	 * height the year's total, its segments the series — for breakdowns
	 * that PARTITION the contracts (one per contract), never for overlapping
	 * ones. The rules stand on 1 January and the column fills its year's
	 * span between them; the total is printed on top; a «today» rule marks
	 * the open year.
	 */
	import { grInt } from '$lib/transforms/format';

	export interface StackSeries {
		label: string;
		color: string;
		/** count per year, aligned with `years`; stacked bottom-up in order */
		values: number[];
	}
	interface Props {
		years: number[];
		series: StackSeries[];
		width?: number;
		height?: number;
		/** ISO date: the open year's «today» rule */
		today?: string | null;
		/** the chip legend under the chart */
		legend?: boolean;
	}
	let { years, series, width = 900, height = 300, today = null, legend = true }: Props = $props();

	const W = $derived(width);
	const H = $derived(height);
	const PAD = { l: 36, r: 14, t: 18, b: 26 };
	const totals = $derived(years.map((_, i) => series.reduce((s, sr) => s + (sr.values[i] ?? 0), 0)));
	const maxV = $derived(Math.max(1, ...totals));
	const step = $derived(maxV > 60 ? 20 : maxV > 20 ? 10 : 5);
	const yTop = $derived(Math.ceil(maxV / step) * step);
	const ticks = $derived(Array.from({ length: yTop / step + 1 }, (_, i) => i * step));

	const y0 = $derived(years[0] ?? 0);
	const span = $derived(years.length);
	const xAt = (yearFrac: number) => PAD.l + ((W - PAD.l - PAD.r) * (yearFrac - y0)) / span;
	const y = (v: number) => H - PAD.b - ((H - PAD.t - PAD.b) * v) / yTop;
	/** the column fills 62 % of its year's span, centred */
	const colW = $derived(((W - PAD.l - PAD.r) / span) * 0.62);
	const colX = (i: number) => xAt(y0 + i + 0.5) - colW / 2;
	const todayFrac = $derived.by(() => {
		if (!today) return null;
		const d = new Date(today);
		const start = Date.UTC(d.getUTCFullYear(), 0, 1);
		const end = Date.UTC(d.getUTCFullYear() + 1, 0, 1);
		return d.getUTCFullYear() + (d.getTime() - start) / (end - start);
	});
	/** segment boxes per year, bottom-up */
	const stacks = $derived(
		years.map((_, i) => {
			let acc = 0;
			return series.map((s) => {
				const v = s.values[i] ?? 0;
				const box = { label: s.label, color: s.color, v, y0: acc, y1: acc + v };
				acc += v;
				return box;
			});
		})
	);
	const ink = (c: string) => (cssLuminance(c) > 150 / 255 ? 'var(--ink)' : 'var(--paper)');
</script>

<figure class="sy">
	<svg viewBox="0 0 {W} {H}" role="img" aria-label="Contracts per year, stacked">
		{#each ticks as t (t)}
			<line x1={PAD.l} y1={y(t)} x2={W - PAD.r} y2={y(t)} class="grid" />
			<text x={PAD.l - 6} y={y(t) + 3} class="ylab">{t}</text>
		{/each}
		{#each years as yr (yr)}
			<line x1={xAt(yr)} y1={y(0)} x2={xAt(yr)} y2={PAD.t} class="grid v" />
			<text x={xAt(yr)} y={H - 8} class="xlab">{yr}</text>
		{/each}
		<line x1={xAt(y0 + span)} y1={y(0)} x2={xAt(y0 + span)} y2={PAD.t} class="grid v" />
		{#if todayFrac != null && todayFrac > y0 && todayFrac < y0 + span}
			<line x1={xAt(todayFrac)} y1={y(0)} x2={xAt(todayFrac)} y2={PAD.t} class="today" />
			<text x={xAt(todayFrac) - 3} y={PAD.t + 9} class="todaylab">today</text>
		{/if}
		{#each stacks as st, i (years[i])}
			{#each st as b (b.label)}
				{#if b.v > 0}
					<rect x={colX(i)} y={y(b.y1)} width={colW} height={y(b.y0) - y(b.y1)} fill={b.color} class="seg">
						<title>{years[i]}: {grInt(b.v)} {b.label}</title>
					</rect>
					{#if y(b.y0) - y(b.y1) >= 14}
						<text x={colX(i) + colW / 2} y={(y(b.y0) + y(b.y1)) / 2 + 3.5} class="segn" fill={ink(b.color)}>{grInt(b.v)}</text>
					{/if}
				{/if}
			{/each}
			{#if totals[i] > 0}
				<text x={colX(i) + colW / 2} y={y(totals[i]) - 5} class="total">{grInt(totals[i])}</text>
			{/if}
		{/each}
	</svg>
	{#if legend}
		<figcaption>
			{#each series as s (s.label)}
				<span class="lgi"><i style:background={s.color}></i>{s.label}</span>
			{/each}
		</figcaption>
	{/if}
</figure>

<style>
	.sy {
		margin: 0;
	}
	.sy > svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: var(--line);
		stroke-width: 0.6;
	}
	.grid.v {
		stroke-dasharray: 2 3;
	}
	.ylab {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: end;
	}
	.xlab {
		font-size: 10.5px;
		fill: var(--ink-soft);
		text-anchor: middle;
	}
	.seg {
		stroke: var(--paper);
		stroke-width: 1;
	}
	.segn {
		font-size: 10px;
		text-anchor: middle;
		pointer-events: none;
	}
	.total {
		font-size: 11px;
		font-weight: 700;
		fill: var(--ink);
		text-anchor: middle;
	}
	.today {
		stroke: var(--ink-soft);
		stroke-width: 0.8;
		stroke-dasharray: 3 3;
	}
	.todaylab {
		font-size: 9.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	figcaption {
		display: flex;
		flex-wrap: wrap;
		gap: 4px var(--sp-5);
		margin-top: var(--sp-2);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.lgi {
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}
	.lgi i {
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}
</style>
