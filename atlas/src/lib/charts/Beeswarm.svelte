<script lang="ts">
	import type { SwarmRow } from '$lib/api';
	import { dodge } from '$lib/transforms/beeswarm';
	import { eur, eurShort } from '$lib/transforms/format';
	import { scopeColor, scopeLabel, orderScopes } from '$lib/transforms/scopes';
	import { scaleLog } from 'd3-scale';

	interface Props {
		rows: SwarmRow[];
		thresholds?: { v: number; label: string }[];
		r?: number;
	}
	let { rows, thresholds = [], r = 4.5 }: Props = $props();

	let width = $state(900);
	const M = { top: 26, right: 16, bottom: 34, left: 16 };
	const CENTER = 120;
	const height = 34 + 2 * CENTER;

	const valid = $derived(rows.filter((d) => (d.eur ?? 0) > 0));
	const x = $derived.by(() => {
		const vs = valid.map((d) => d.eur);
		return scaleLog([Math.min(...vs), Math.max(...vs)], [M.left, width - M.right]).nice();
	});
	const placed = $derived.by(() => {
		const xs = valid.map((d) => x(d.eur));
		const ys = dodge(xs, r + 0.6);
		return valid.map((d, i) => ({ d, x: xs[i], y: M.top + CENTER + ys[i] }));
	});

	const median = $derived.by(() => {
		const vs = valid.map((d) => d.eur).sort((a, b) => a - b);
		return vs[Math.floor(vs.length / 2)] ?? 0;
	});
	const biggest = $derived(placed.reduce((m, p) => (p.d.eur > m.d.eur ? p : m), placed[0]));

	const axisTicks = $derived(
		[1e4, 1e5, 1e6, 1e7].filter((v) => v >= x.domain()[0] && v <= x.domain()[1])
	);

	let tip = $state<string | null>(null);
	const scopes = $derived(orderScopes(valid.map((d) => d.scope)));
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each axisTicks as t (t)}
			<line class="grid" x1={x(t)} x2={x(t)} y1={M.top} y2={height - M.bottom} />
			<text class="axis" x={x(t)} y={height - 12}>{eurShort(t)}</text>
		{/each}

		{#each thresholds as th, ti (th.v)}
			{#if th.v >= x.domain()[0] && th.v <= x.domain()[1]}
				<line class="threshold" x1={x(th.v)} x2={x(th.v)} y1={M.top} y2={height - M.bottom} />
				<text class="threshold-label" x={x(th.v) + 4} y={M.top + 10 + ti * 13}>{th.label}</text>
			{/if}
		{/each}

		<!-- median annotation, printed -->
		<line class="median" x1={x(median)} x2={x(median)} y1={M.top} y2={height - M.bottom} />
		<text class="median-label" x={x(median) - 4} y={M.top + 10}>
			median {eurShort(median)}
		</text>

		{#each placed as p (p.d.ref)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<a href={`/antinero/contract/${p.d.ref}`} aria-label={p.d.t}>
				<circle
					cx={p.x}
					cy={p.y}
					{r}
					fill={scopeColor(p.d.scope)}
					class:single={p.d.single_bidder === 1}
					opacity="0.85"
					onmouseenter={() =>
						(tip = `<strong>${eur(p.d.eur)}</strong> · ${p.d.year ?? ''}<br>${p.d.t}` +
							`<br><span style="color:var(--ink-faint)">${scopeLabel(p.d.scope)}` +
							`${p.d.single_bidder ? ' · single bidder' : ''} · ${p.d.pe ?? ''}</span>`)}
					onmouseleave={() => (tip = null)}
				/>
			</a>
		{/each}

		{#if biggest}
			<text class="note" x={biggest.x - 6} y={biggest.y - r - 8} text-anchor="end">
				largest: {eurShort(biggest.d.eur)}
			</text>
		{/if}
	</svg>

	<div class="legend">
		{#each scopes as s (s)}
			<span><i style:background={scopeColor(s)}></i>{scopeLabel(s)}</span>
		{/each}
		<span><i class="ring"></i>single bidder</span>
	</div>

	{#if tip}
		<div class="tip">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			{@html tip}
		</div>
	{/if}
</div>

<style>
	.wrap {
		position: relative;
	}
	svg {
		display: block;
		width: 100%;
	}
	circle {
		cursor: pointer;
	}
	circle:hover {
		opacity: 1;
		stroke: var(--ink);
		stroke-width: 1.5;
	}
	circle.single {
		stroke: var(--ink);
		stroke-width: 1.2;
	}
	.grid {
		stroke: var(--line);
	}
	.axis {
		font-size: 11px;
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
	.median {
		stroke: var(--ink);
		stroke-width: 1;
		opacity: 0.5;
	}
	.median-label {
		font-size: 11px;
		fill: var(--ink);
		text-anchor: end;
	}
	.note {
		font-size: 11px;
		fill: var(--ink-soft);
		font-style: italic;
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
		border-radius: 50%;
		margin-right: 4px;
		vertical-align: -1px;
	}
	.legend i.ring {
		background: transparent;
		border: 1.5px solid var(--ink);
	}
	.tip {
		position: absolute;
		top: 0;
		right: 0;
		max-width: 26rem;
		background: color-mix(in srgb, var(--paper) 94%, transparent);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-13);
		pointer-events: none;
		box-shadow: var(--shadow-paper);
	}
</style>
