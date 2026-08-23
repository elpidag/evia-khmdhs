<script lang="ts">
	import type { Pipelines } from '$lib/api';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import { orgEn } from '$lib/transforms/names';

	let { data }: { data: Pipelines } = $props();

	let width = $state(900);
	const COL_W = 230;
	const TOP = 96;

	// shelf-pack each side's entities (sorted by €) into its column
	function pack(entities: Pipelines['antinero']['entities'], maxEur: number) {
		const rMax = 15,
			rMin = 2.2;
		const out: { x: number; y: number; r: number; e: (typeof entities)[0] }[] = [];
		let cx = 0,
			cy = TOP,
			rowH = 0;
		for (const e of entities) {
			const r = rMin + (rMax - rMin) * Math.sqrt(e.eur / maxEur);
			if (cx + 2 * r > COL_W) {
				cx = 0;
				cy += rowH + 3;
				rowH = 0;
			}
			out.push({ x: cx + r, y: cy + r, r, e });
			cx += 2 * r + 3;
			rowH = Math.max(rowH, 2 * r);
		}
		return out;
	}

	const maxEur = $derived(
		Math.max(data.antinero.entities[0]?.eur ?? 1, data.dase.entities[0]?.eur ?? 1)
	);
	const left = $derived(pack(data.antinero.entities, maxEur));
	const right = $derived(pack(data.dase.entities, maxEur));
	const leftX = $derived(width / 2 - COL_W - 110);
	const rightX = $derived(width / 2 + 110);
	/** the box is as tall as its taller column — the old fixed 560 left a
	 *  void under the dots (2026-08-23) */
	const colBottom = $derived(
		10 + Math.max(TOP, ...left.map((d) => d.y + d.r), ...right.map((d) => d.y + d.r))
	);
	const height = $derived(Math.max(colBottom + 16, TOP + 150));
	const voidY = $derived(TOP + 10 + (colBottom - TOP - 10) / 2);

	let tip = $state<string | null>(null);
	const ministry = $derived(data.shared_awarders[0]);
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		<!-- the single shared awarder, bridging both columns -->
		{#if ministry}
			{@const mx = width / 2}
			<path
				class="ribbon antinero"
				d="M {mx - 40} 34 C {leftX + COL_W / 2} 34, {leftX + COL_W / 2} 50, {leftX +
					COL_W / 2} {TOP - 14}"
			/>
			<path
				class="ribbon dase"
				d="M {mx + 40} 34 C {rightX + COL_W / 2} 34, {rightX + COL_W / 2} 50, {rightX +
					COL_W / 2} {TOP - 14}"
			/>
			<text class="ministry" x={mx} y={26}>{orgEn(ministry.name)}</text>
			<text class="ministry-sub" x={leftX + COL_W / 2} y={TOP - 22}>
				{grInt(ministry.antinero_n)} contracts
			</text>
			<text class="ministry-sub" x={rightX + COL_W / 2} y={TOP - 22}>
				{grInt(ministry.dase_n)} contracts
			</text>
		{/if}

		<!-- column headers -->
		<text class="col-head antinero" x={leftX + COL_W / 2} y={TOP - 4}>
			{grInt(data.antinero.n_vats)} Anti-nero contractors · {eurShort(data.antinero.total_eur)}
		</text>
		<text class="col-head dase" x={rightX + COL_W / 2} y={TOP - 4}>
			{grInt(data.dase.n_vats)} co-op-side entities · {eurShort(data.dase.total_eur)}
		</text>

		<g transform="translate({leftX},10)">
			{#each left as d (d.e.vat)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<a href={`/antinero/contractor/${d.e.vat}`} aria-label={d.e.name}>
					<circle
						cx={d.x}
						cy={d.y}
						r={d.r}
						class="dot antinero"
						onmouseenter={() => (tip = `<strong>${d.e.name}</strong><br>${eur(d.e.eur)} · even split`)}
						onmouseleave={() => (tip = null)}
					/>
				</a>
			{/each}
		</g>
		<g transform="translate({rightX},10)">
			{#each right as d (d.e.vat)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<a href={`/dase/coop/${d.e.vat}`} aria-label={d.e.name}>
					<circle
						cx={d.x}
						cy={d.y}
						r={d.r}
						class="dot dase"
						onmouseenter={() => (tip = `<strong>${d.e.name}</strong><br>${eur(d.e.eur)} · even split`)}
						onmouseleave={() => (tip = null)}
					/>
				</a>
			{/each}
		</g>

		<!-- the void in the middle: the finding, printed -->
		<g class="void" transform="translate({width / 2},{voidY})">
			<text class="void-zero" y="-10">0</text>
			<text class="void-line" y="14">companies appear in both datasets</text>
			<text class="void-line faint" y="32">
				{grInt(data.antinero.n_vats + data.dase.n_vats)} entities, zero shared ΑΦΜ
			</text>
		</g>
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
	.dot {
		opacity: 0.85;
		cursor: pointer;
	}
	.dot:hover {
		opacity: 1;
		stroke: var(--ink);
		stroke-width: 1.4;
	}
	.dot.antinero {
		fill: var(--c-antinero);
	}
	.dot.dase {
		fill: var(--c-dase);
	}
	.ribbon {
		fill: none;
		stroke-width: 10;
		opacity: 0.25;
	}
	.ribbon.antinero {
		stroke: var(--c-antinero);
	}
	.ribbon.dase {
		stroke: var(--c-dase);
	}
	.ministry {
		font-size: var(--fs-13);
		font-weight: 700;
		text-anchor: middle;
		fill: var(--ink);
	}
	.ministry-sub {
		font-size: var(--fs-12);
		text-anchor: middle;
		fill: var(--ink-soft);
	}
	.col-head {
		font-family: var(--font-display);
		font-size: var(--fs-13);
		font-weight: 700;
		text-anchor: middle;
	}
	.col-head.antinero {
		fill: var(--c-antinero);
	}
	.col-head.dase {
		fill: var(--c-dase);
	}
	.void text {
		text-anchor: middle;
	}
	.void-zero {
		font-family: var(--font-display);
		font-size: 64px;
		font-weight: 900;
		fill: var(--ink);
	}
	.void-line {
		font-size: var(--fs-14);
		fill: var(--ink);
	}
	.void-line.faint {
		font-size: var(--fs-12);
		fill: var(--ink-soft);
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
		bottom: var(--sp-2);
		left: 0;
	}
</style>
