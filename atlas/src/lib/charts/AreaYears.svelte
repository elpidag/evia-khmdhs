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
		/** 'area' (default): translucent fill + edge; 'line': no fill — dashed
		 *  unless `dash` is false (the Anti-nero scope lines are solid) */
		kind?: 'area' | 'line';
		dash?: boolean;
	}
	interface Props {
		years: number[];
		series: AreaSeries[];
		/** viewBox size — match the rendered width so type stays true-size */
		width?: number;
		height?: number;
		/** TIME axis (user, 2026-08-23): the verticals stand on 1 JANUARY of
		 *  each year, labelled on the rule as every timeline on the site, and
		 *  a year's count sits at the MIDDLE of that year's span; the default
		 *  (false) is the category axis the sponsored chart uses */
		janRules?: boolean;
		/** a dot at every value, so the point each line starts from — and
		 *  every value — is explicit */
		dots?: boolean;
		/** ISO date: a «today» rule, so the open last year reads as partial */
		today?: string | null;
		/** the chip legend under the chart (off where the page's own key
		 *  already names the series — the CONTRACT SCOPE bar above it) */
		legend?: boolean;
	}
	let {
		years,
		series,
		width = 900,
		height = 300,
		janRules = false,
		dots = false,
		today = null,
		legend = true
	}: Props = $props();

	const W = $derived(width);
	const H = $derived(height);
	const PAD = { l: 36, r: 14, t: 12, b: 26 };

	const maxV = $derived(Math.max(1, ...series.flatMap((s) => s.values)));
	/** y-axis ceiling on a round step */
	const step = $derived(maxV > 20 ? 10 : 5);
	const yTop = $derived(Math.ceil(maxV / step) * step);
	const ticks = $derived(Array.from({ length: yTop / step + 1 }, (_, i) => i * step));

	/** the time axis runs from 1 January of the first year to 1 January
	 *  after the last; a fractional year maps linearly */
	const y0 = $derived(years[0] ?? 0);
	const span = $derived(janRules ? years.length : Math.max(1, years.length - 1));
	const xAt = (yearFrac: number) => PAD.l + ((W - PAD.l - PAD.r) * (yearFrac - y0)) / span;
	/** the x of the i-th year's VALUE: mid-span on the time axis, on the
	 *  tick on the category axis */
	const x = (i: number) => (janRules ? xAt(y0 + i + 0.5) : xAt(y0 + i));
	const y = (v: number) => H - PAD.b - ((H - PAD.t - PAD.b) * v) / yTop;
	const todayFrac = $derived.by(() => {
		if (!today) return null;
		const d = new Date(today);
		const start = Date.UTC(d.getUTCFullYear(), 0, 1);
		const end = Date.UTC(d.getUTCFullYear() + 1, 0, 1);
		return d.getUTCFullYear() + (d.getTime() - start) / (end - start);
	});

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
		{#if janRules}
			<!-- a rule on every 1 January, the year's label ON its rule -->
			{#each years as yr (yr)}
				<line x1={xAt(yr)} y1={y(0)} x2={xAt(yr)} y2={PAD.t} class="grid v" />
				<text x={xAt(yr)} y={H - 8} class="xlab">{yr}</text>
			{/each}
			<line x1={xAt(y0 + years.length)} y1={y(0)} x2={xAt(y0 + years.length)} y2={PAD.t} class="grid v" />
			{#if todayFrac != null && todayFrac > y0 && todayFrac < y0 + years.length}
				<line x1={xAt(todayFrac)} y1={y(0)} x2={xAt(todayFrac)} y2={PAD.t} class="today" />
				<text x={xAt(todayFrac) - 3} y={PAD.t + 9} class="todaylab">today</text>
			{/if}
		{:else}
			{#each years as yr, i (yr)}
				<line x1={x(i)} y1={y(0)} x2={x(i)} y2={PAD.t} class="grid v" />
				<text x={x(i)} y={H - 8} class="xlab">{yr}</text>
			{/each}
		{/if}
		{#each series as s (s.label)}
			{#if s.kind === 'line'}
				<path d={linePath(s.values)} stroke={s.color} class="dashed" class:solid={s.dash === false} />
			{:else}
				<path d={areaPath(s.values)} fill={s.color} class="area" />
				<path d={linePath(s.values)} stroke={s.color} class="edge" />
			{/if}
			{#if dots}
				{#each s.values as v, i (i)}
					<circle cx={x(i)} cy={y(v)} r="3.2" fill={s.color} class="dot"><title>{years[i]}: {v} {s.label}</title></circle>
				{/each}
			{/if}
		{/each}
	</svg>
	<figcaption class:off={!legend}>
		{#each series as s (s.label)}
			<span class="lgi">
				{#if s.kind === 'line'}
					<svg class="sw" width="20" height="12" aria-hidden="true">
						<line x1="0" y1="6" x2="20" y2="6" stroke={s.color} stroke-width="2" stroke-dasharray={s.dash === false ? null : '5 4'} />
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
	figcaption.off {
		display: none;
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
	.dashed.solid {
		stroke-dasharray: none;
	}
	.dot {
		stroke: var(--paper);
		stroke-width: 1;
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
