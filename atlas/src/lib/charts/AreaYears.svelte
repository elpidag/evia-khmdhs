<script lang="ts">
	/** Overlapping yearly area chart (mock: two translucent area series
	 *  over a year axis with a chip legend underneath). Values are counts
	 *  per calendar year; series render in order, so put the larger one
	 *  first and the smaller on top. */
	export interface AreaSeries {
		label: string;
		color: string;
		/** count per year, aligned with the `years` prop */
		values: number[];
		/** 'area' (default): translucent fill + edge; 'line': dashed, no fill */
		kind?: 'area' | 'line';
	}
	interface Props {
		years: number[];
		series: AreaSeries[];
		/** viewBox size — match the rendered width so type stays true-size */
		width?: number;
		height?: number;
	}
	let { years, series, width = 900, height = 300 }: Props = $props();

	const W = $derived(width);
	const H = $derived(height);
	const PAD = { l: 36, r: 14, t: 12, b: 26 };

	const maxV = $derived(Math.max(1, ...series.flatMap((s) => s.values)));
	/** y-axis ceiling on a round step */
	const step = $derived(maxV > 20 ? 10 : 5);
	const yTop = $derived(Math.ceil(maxV / step) * step);
	const ticks = $derived(Array.from({ length: yTop / step + 1 }, (_, i) => i * step));

	const x = (i: number) =>
		PAD.l + ((W - PAD.l - PAD.r) * i) / Math.max(1, years.length - 1);
	const y = (v: number) => H - PAD.b - ((H - PAD.t - PAD.b) * v) / yTop;

	function areaPath(vals: number[]): string {
		const pts = vals.map((v, i) => `${x(i)},${y(v)}`);
		return `M${x(0)},${y(0)} L${pts.join(' L')} L${x(vals.length - 1)},${y(0)} Z`;
	}
	function linePath(vals: number[]): string {
		return `M${vals.map((v, i) => `${x(i)},${y(v)}`).join(' L')}`;
	}
</script>

<figure class="ay">
	<svg viewBox="0 0 {W} {H}" role="img" aria-label="Acts per year">
		{#each ticks as t (t)}
			<line x1={PAD.l} y1={y(t)} x2={W - PAD.r} y2={y(t)} class="grid" />
			<text x={PAD.l - 6} y={y(t) + 3} class="ylab">{t}</text>
		{/each}
		{#each years as yr, i (yr)}
			<line x1={x(i)} y1={y(0)} x2={x(i)} y2={PAD.t} class="grid v" />
			<text x={x(i)} y={H - 8} class="xlab">{yr}</text>
		{/each}
		{#each series as s (s.label)}
			{#if s.kind === 'line'}
				<path d={linePath(s.values)} stroke={s.color} class="dashed" />
			{:else}
				<path d={areaPath(s.values)} fill={s.color} class="area" />
				<path d={linePath(s.values)} stroke={s.color} class="edge" />
			{/if}
		{/each}
	</svg>
	<figcaption>
		{#each series as s (s.label)}
			<span class="lgi">
				{#if s.kind === 'line'}
					<svg class="sw" width="20" height="12" aria-hidden="true">
						<line x1="0" y1="6" x2="20" y2="6" stroke={s.color} stroke-width="2" stroke-dasharray="5 4" />
					</svg>
				{:else}
					<i style:background={s.color}></i>
				{/if}
				{s.label}
			</span>
		{/each}
	</figcaption>
</figure>

<style>
	.ay {
		margin: 0;
	}
	.ay > svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.lgi .sw {
		width: 20px;
		height: 12px;
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
	.area {
		opacity: 0.45;
	}
	.edge {
		fill: none;
		stroke-width: 1.6;
	}
	.dashed {
		fill: none;
		stroke-width: 2;
		stroke-dasharray: 5 4;
	}
	/* legend dressed like the CURRENT STATUS strip */
	figcaption {
		display: flex;
		flex-wrap: wrap;
		gap: 6px var(--sp-5, 1.25rem);
		margin-top: var(--sp-2);
		padding: var(--sp-2) var(--sp-3);
		background: var(--paper-2);
		border-radius: 6px;
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.lgi {
		display: inline-flex;
		align-items: center;
		gap: 8px;
	}
	.lgi i {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		flex: none;
	}
	.lgi .sw {
		flex: none;
	}
</style>
