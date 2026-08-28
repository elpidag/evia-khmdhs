<script lang="ts">
	import type { PaymentsPayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';
	import { scaleLinear } from 'd3-scale';
	import { line, curveStepAfter } from 'd3-shape';

	/**
	 * Year-vs-year ONLY since 2026-08-22 (user): the stacked-by-phase mode
	 * is gone, and the chart lives at half width beside MONEY PER YEAR.
	 * The fire-season band wears the payments timeline's colour.
	 */
	interface Props {
		payments: PaymentsPayload;
	}
	let { payments }: Props = $props();

	let width = $state(520);
	const height = 340;
	const M = { top: 14, right: 118, bottom: 26, left: 84 };

	// ---- YoY mode: cumulative-to-date per year -------------------------
	const yoy = $derived.by(() => {
		const byYear = new Map<number, { doy: number; cum: number }[]>();
		const sorted = payments.events
			.filter((e) => e.d)
			.sort((a, b) => a.d!.localeCompare(b.d!));
		const cums = new Map<number, number>();
		for (const e of sorted) {
			const dt = new Date(e.d!);
			const y = dt.getFullYear();
			const start = new Date(y, 0, 1).getTime();
			const doy = (dt.getTime() - start) / 86_400_000;
			const cum = (cums.get(y) ?? 0) + (e.eur || 0);
			cums.set(y, cum);
			if (!byYear.has(y)) byYear.set(y, [{ doy: 0, cum: 0 }]);
			byYear.get(y)!.push({ doy, cum });
		}
		return [...byYear.entries()].sort((a, b) => a[0] - b[0]);
	});
	const yoyMax = $derived(Math.max(...yoy.map(([, pts]) => pts.at(-1)?.cum ?? 0), 1));
	const currentYear = $derived(Math.max(...yoy.map(([y]) => y)));
	const xYoy = $derived(scaleLinear([0, 366], [M.left, width - M.right]));
	const yYoy = $derived(scaleLinear([0, yoyMax], [height - M.bottom, M.top]));
	const yoyLine = $derived(
		line<{ doy: number; cum: number }>()
			.x((p) => xYoy(p.doy))
			.y((p) => yYoy(p.cum))
			.curve(curveStepAfter)
	);

	const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		<!-- the fire season, in the SAME colour the payments timeline
		     bands it with (user, 2026-08-22) -->
		<rect
			x={xYoy(120)}
			y={M.top}
			width={xYoy(243) - xYoy(120)}
			height={height - M.top - M.bottom}
			fill="var(--c-fire-season)"
		/>
		<text class="season-label" x={xYoy(120) + 4} y={M.top + 12}>fire season</text>
		{#each yYoy.ticks(4) as t (t)}
			<line class="grid" x1={M.left} x2={width - M.right} y1={yYoy(t)} y2={yYoy(t)} />
			<text class="axis" x={M.left - 6} y={yYoy(t) + 3} text-anchor="end">{eurShort(t)}</text>
		{/each}
		{#each yoy as [year, pts] (year)}
			<path class="yoy-line" class:current={year === currentYear} d={yoyLine(pts)} />
			<text
				class="series-label"
				class:current={year === currentYear}
				x={xYoy(Math.min(pts.at(-1)!.doy, 366)) + 5}
				y={yYoy(pts.at(-1)!.cum) + 3}
			>
				{year} · {eurShort(pts.at(-1)!.cum)}
			</text>
		{/each}
		{#each [0, 2, 4, 6, 8, 10] as m (m)}
			<text class="axis" x={xYoy(m * 30.5)} y={height - 8} text-anchor="middle">
				{MONTHS[m]}
			</text>
		{/each}
	</svg>
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	.grid {
		stroke: var(--line);
	}
	.axis {
		font-size: 11px;
		fill: var(--ink-faint);
	}
	.series-label {
		font-size: 11px;
	}
	.yoy-line {
		fill: none;
		stroke: var(--ink-faint);
		stroke-width: 1.4;
	}
	.yoy-line.current {
		stroke: var(--ink);
		stroke-width: 2.4;
	}
	text.series-label {
		fill: var(--ink-soft);
	}
	text.series-label.current {
		fill: var(--ink);
		font-weight: 700;
	}
	.season-label {
		font-size: 10px;
		fill: var(--c-fire);
		opacity: 0.85;
	}
</style>
