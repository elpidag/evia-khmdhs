<script lang="ts">
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import type { ComparePayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';
	import { scaleLog } from 'd3-scale';

	let { rows }: { rows: ComparePayload['by_pe'] } = $props();

	let width = $state(900);
	const height = 480;
	const M = { top: 24, right: 30, bottom: 46, left: 64 };
	const GUTTER = 26; // zero-side band inside each axis

	const both = $derived(rows.filter((r) => r.antinero_eur > 0 && r.dase_eur > 0));
	const onlyA = $derived(rows.filter((r) => r.antinero_eur > 0 && r.dase_eur <= 0));
	const onlyD = $derived(rows.filter((r) => r.antinero_eur <= 0 && r.dase_eur > 0));

	const xDom = $derived.by(() => {
		const vs = rows.filter((r) => r.antinero_eur > 0).map((r) => r.antinero_eur);
		return [Math.min(...vs), Math.max(...vs)] as [number, number];
	});
	const yDom = $derived.by(() => {
		const vs = rows.filter((r) => r.dase_eur > 0).map((r) => r.dase_eur);
		return [Math.min(...vs), Math.max(...vs)] as [number, number];
	});
	const x = $derived(scaleLog(xDom, [M.left + GUTTER, width - M.right]).nice());
	const y = $derived(scaleLog(yDom, [height - M.bottom - GUTTER, M.top]).nice());

	// label the outliers by combined €, printed in place — a label landing
	// within a row of the previous one (and beside it) is nudged down a row
	const labelled = $derived.by(() => {
		const top = [...both]
			.sort((a, b) => b.antinero_eur + b.dase_eur - (a.antinero_eur + a.dase_eur))
			.slice(0, 8)
			.map((r) => ({ r, lx: x(r.antinero_eur) + 8, ly: y(r.dase_eur) + 3 }))
			.sort((a, b) => a.ly - b.ly);
		for (let i = 1; i < top.length; i++) {
			for (let j = 0; j < i; j++) {
				const o = top[j];
				if (Math.abs(top[i].ly - o.ly) < 12 && Math.abs(top[i].lx - o.lx) < 90) {
					top[i].ly = o.ly + 12;
				}
			}
		}
		return top;
	});

	let tip = $state<string | null>(null);
	function show(r: ComparePayload['by_pe'][0]) {
		tip =
			`<strong>${ruLabel(r.pe)}</strong>` +
			`<br>Anti-nero: ${eurShort(r.antinero_eur)} · ${r.antinero_n} contracts` +
			`<br>forest co-ops: ${eurShort(r.dase_eur)} · ${r.dase_n} contracts`;
	}
	const ticksOf = (dom: [number, number]) =>
		[1e4, 1e5, 1e6, 1e7, 1e8].filter((v) => v >= dom[0] && v <= dom[1]);
	/** a power-of-ten tick reads «10 M €», not «10,00 M €» */
	const tick = (v: number) => (v >= 1e6 ? `${v / 1e6} M €` : `${v / 1e3} K €`);
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each ticksOf(x.domain() as [number, number]) as t (t)}
			<line class="grid" x1={x(t)} x2={x(t)} y1={M.top} y2={height - M.bottom} />
			<text class="axis" x={x(t)} y={height - M.bottom + 16} text-anchor="middle">
				{tick(t)}
			</text>
		{/each}
		{#each ticksOf(y.domain() as [number, number]) as t (t)}
			<line class="grid" x1={M.left} x2={width - M.right} y1={y(t)} y2={y(t)} />
			<text class="axis" x={M.left - 6} y={y(t) + 3} text-anchor="end">{tick(t)}</text>
		{/each}

		<text class="axis-title" x={width - M.right} y={height - 8} text-anchor="end">
			Anti-nero € in the regional unit →
		</text>
		<text class="axis-title" x={12} y={M.top - 8}>forest co-op € ↑</text>

		{#each both as r (r.pe)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={x(r.antinero_eur)}
				cy={y(r.dase_eur)}
				r="6"
				class="dot"
				onmouseenter={() => show(r)}
				onmouseleave={() => (tip = null)}
			/>
		{/each}
		{#each onlyA as r (r.pe)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={x(r.antinero_eur)}
				cy={height - M.bottom - GUTTER / 2}
				r="4"
				class="dot only-a"
				onmouseenter={() => show(r)}
				onmouseleave={() => (tip = null)}
			/>
		{/each}
		{#each onlyD as r (r.pe)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={M.left + GUTTER / 2}
				cy={y(r.dase_eur)}
				r="4"
				class="dot only-d"
				onmouseenter={() => show(r)}
				onmouseleave={() => (tip = null)}
			/>
		{/each}

		<text class="gutter-label" x={width - M.right} y={height - M.bottom - GUTTER - 5}
			text-anchor="end">Anti-nero only ({onlyA.length} R.U.) ↓</text>
		<text class="gutter-label" x={M.left + GUTTER / 2 + 8} y={M.top + 12}>
			co-ops only ({onlyD.length} R.U.)
		</text>

		{#each labelled as l (l.r.pe)}
			<text class="pe-label" x={l.lx} y={l.ly}>{peEn(l.r.pe)}</text>
		{/each}
	</svg>

	{#if tip}
		<div class="tip">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			{@html tip}
		</div>
	{/if}
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	.wrap {
		position: relative;
	}
	.grid {
		stroke: var(--line);
	}
	.axis {
		font-size: 11px;
		fill: var(--ink-soft);
	}
	.axis-title {
		font-size: var(--fs-12);
		fill: var(--ink);
	}
	.dot {
		fill: var(--ink);
		opacity: 0.65;
	}
	.dot:hover {
		opacity: 1;
	}
	.dot.only-a {
		fill: var(--c-antinero);
	}
	.dot.only-d {
		fill: var(--c-dase);
	}
	.gutter-label {
		font-size: 11px;
		fill: var(--ink-soft);
	}
	.pe-label {
		font-size: var(--fs-12);
		fill: var(--ink);
	}
	/* hover card — black plate, white lettering, like the map cards */
	.tip {
		position: absolute;
		z-index: 3;
		pointer-events: none;
		padding: 7px 10px;
		border-radius: 4px;
		background: #000;
		color: #fff;
		font-size: var(--fs-12);
		line-height: 1.3;
		white-space: nowrap;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
	}
	.tip {
		top: 0;
		right: 0;
	}
</style>
