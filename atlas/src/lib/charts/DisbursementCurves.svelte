<script lang="ts">
	import type { AntineroOverview, PaymentsPayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';
	import { orderScopes, scopeColor, scopeLabel } from '$lib/transforms/scopes';
	import { scaleLinear, scaleTime } from 'd3-scale';
	import { area, line, curveStepAfter } from 'd3-shape';

	interface Props {
		timeseries: AntineroOverview['timeseries'];
		payments: PaymentsPayload;
	}
	let { timeseries, payments }: Props = $props();

	let mode = $state<'phases' | 'yoy'>('phases');
	let width = $state(900);
	const height = 340;
	const M = { top: 14, right: 130, bottom: 26, left: 56 };

	// ---- phases mode: stacked cumulative areas -------------------------
	const scopes = $derived(orderScopes(Object.keys(timeseries.series)));
	const stacked = $derived.by(() => {
		const months = timeseries.months;
		let base = months.map(() => 0);
		return scopes.map((s) => {
			const vals = timeseries.series[s];
			const y0 = base;
			const y1 = base.map((b, i) => b + (vals[i] ?? 0));
			base = y1;
			return { scope: s, y0, y1 };
		});
	});
	const phasesTotal = $derived(stacked.at(-1)?.y1.at(-1) ?? 0);

	const xPhases = $derived(
		scaleTime(
			[new Date(timeseries.months[0] + '-01'), new Date(timeseries.months.at(-1)! + '-01')],
			[M.left, width - M.right]
		)
	);
	const yPhases = $derived(scaleLinear([0, phasesTotal], [height - M.bottom, M.top]));

	const areaGen = $derived(
		area<number>()
			.x((_, i) => xPhases(new Date(timeseries.months[i] + '-01')))
			.curve(curveStepAfter)
	);

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
	<div class="mode" role="group">
		<button class:active={mode === 'phases'} onclick={() => (mode = 'phases')}>
			Stacked by phase
		</button>
		<button class:active={mode === 'yoy'} onclick={() => (mode = 'yoy')}>
			Year vs year
		</button>
	</div>

	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#if mode === 'phases'}
			{#each yPhases.ticks(4) as t (t)}
				<line class="grid" x1={M.left} x2={width - M.right} y1={yPhases(t)} y2={yPhases(t)} />
				<text class="axis" x={M.left - 6} y={yPhases(t) + 3} text-anchor="end">{eurShort(t)}</text>
			{/each}
			{#each stacked as s (s.scope)}
				<path
					d={areaGen.y0((_, i) => yPhases(s.y0[i])).y1((_, i) => yPhases(s.y1[i]))(
						timeseries.months.map((_, i) => i)
					)}
					fill={scopeColor(s.scope)}
					opacity="0.85"
				/>
				{#if (s.y1.at(-1) ?? 0) - (s.y0.at(-1) ?? 0) > phasesTotal * 0.03}
					<text
						class="series-label"
						x={width - M.right + 6}
						y={(yPhases(s.y0.at(-1) ?? 0) + yPhases(s.y1.at(-1) ?? 0)) / 2 + 3}
						fill={scopeColor(s.scope)}
					>
						{scopeLabel(s.scope)}
						{eurShort((s.y1.at(-1) ?? 0) - (s.y0.at(-1) ?? 0))}
					</text>
				{/if}
			{/each}
			{#each xPhases.ticks(6) as t (t.getTime())}
				<text class="axis" x={xPhases(t)} y={height - 8} text-anchor="middle">
					{t.getFullYear()}
				</text>
			{/each}
		{:else}
			<rect
				x={xYoy(120)}
				y={M.top}
				width={xYoy(243) - xYoy(120)}
				height={height - M.top - M.bottom}
				fill="var(--accent)"
				opacity="0.06"
			/>
			<text class="season-label" x={xYoy(120) + 4} y={M.top + 12}>fire season</text>
			{#each yYoy.ticks(4) as t (t)}
				<line class="grid" x1={M.left} x2={width - M.right} y1={yYoy(t)} y2={yYoy(t)} />
				<text class="axis" x={M.left - 6} y={yYoy(t) + 3} text-anchor="end">{eurShort(t)}</text>
			{/each}
			{#each yoy as [year, pts] (year)}
				<path
					class="yoy-line"
					class:current={year === currentYear}
					d={yoyLine(pts)}
				/>
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
		{/if}
	</svg>
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	.mode {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
		margin-bottom: var(--sp-2);
	}
	.mode button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.mode button.active {
		background: var(--ink);
		color: var(--paper);
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
		stroke: var(--accent);
		stroke-width: 2.4;
	}
	text.series-label {
		fill: var(--ink-soft);
	}
	text.series-label.current {
		fill: var(--accent);
		font-weight: 700;
	}
	.season-label {
		font-size: 10px;
		fill: var(--accent);
		opacity: 0.75;
	}
</style>
