<script lang="ts">
	/**
	 * Contractor ↔ work-region links. Each column is a stable top-25 list;
	 * SELECTING swaps rows in only as needed (user, 2026-08-20, second
	 * refinement — neither a pooled «+N more» row nor a column that turns
	 * into something else): click a contractor and, if it works in regions
	 * below the cut, the region column reshuffles just enough to include
	 * them — the lowest non-connected rows give way — and its regions
	 * highlight while the rest dim. Click a region for the mirror on the
	 * contractor side. Rows always carry the same meaning: the entity and
	 * its total €.
	 */
	import { flip } from 'svelte/animate';
	import { peEn } from '$lib/transforms/regions';
	import { eurShort, grInt } from '$lib/transforms/format';

	interface Edge {
		vat: string;
		pe: string;
		n: number;
		eur: number;
	}
	interface Props {
		edges: Edge[];
		contractors: Record<string, { name: string; home_pe: string | null; eur: number }>;
		topContractors?: number;
		topRegions?: number;
		/** the selection, bindable — the flow frame shares it with its map
		 *  lens (a focused region arrives selected here, a selected company's
		 *  home region focuses the map) (user, 2026-08-21) */
		selected?: { kind: 'vat' | 'pe'; id: string } | null;
	}
	let {
		edges,
		contractors,
		topContractors = 25,
		topRegions = 25,
		selected = $bindable(null)
	}: Props = $props();

	// ---- resting lists ----------------------------------------------------
	const restingLeft = $derived(
		Object.entries(contractors)
			.sort((a, b) => b[1].eur - a[1].eur)
			.slice(0, topContractors)
			.map(([vat, c]) => ({ vat, name: c.name, eur: c.eur }))
	);
	const peTotals = $derived.by(() => {
		const agg = new Map<string, number>();
		for (const e of edges) agg.set(e.pe, (agg.get(e.pe) ?? 0) + e.eur);
		return agg;
	});
	const restingRight = $derived(
		[...peTotals.entries()]
			.sort((a, b) => b[1] - a[1])
			.slice(0, topRegions)
			.map(([pe, eur]) => ({ pe, eur }))
	);
	const restingLeftSet = $derived(new Set(restingLeft.map((c) => c.vat)));
	const restingRightSet = $derived(new Set(restingRight.map((r) => r.pe)));

	// ---- the selection's counterparts, for the swap and the dimming -------
	const linkedPes = $derived(
		selected?.kind === 'vat'
			? new Set(edges.filter((e) => e.vat === selected!.id).map((e) => e.pe))
			: null
	);
	const linkedVats = $derived(
		selected?.kind === 'pe'
			? new Set(edges.filter((e) => e.pe === selected!.id).map((e) => e.vat))
			: null
	);

	// ---- displayed lists: the stable top-25, with rows swapped in only as
	// needed so every counterpart of the selection is on show ---------------
	const displayLeft = $derived.by(() => {
		if (!linkedVats) return restingLeft;
		const need = [...linkedVats].map((vat) => ({
			vat,
			name: contractors[vat]?.name ?? vat,
			eur: contractors[vat]?.eur ?? 0
		}));
		const have = new Set(need.map((c) => c.vat));
		const fill = restingLeft.filter((c) => !have.has(c.vat));
		return [...need, ...fill]
			.slice(0, Math.max(topContractors, need.length))
			.toSorted((a, b) => b.eur - a.eur);
	});
	const displayRight = $derived.by(() => {
		let need: string[] = [];
		if (linkedPes) need = [...linkedPes];
		else if (selected?.kind === 'pe') need = [selected.id];
		if (!need.length) return restingRight;
		const rows = need.map((pe) => ({ pe, eur: peTotals.get(pe) ?? 0 }));
		const have = new Set(need);
		const fill = restingRight.filter((r) => !have.has(r.pe));
		return [...rows, ...fill]
			.slice(0, Math.max(topRegions, rows.length))
			.toSorted((a, b) => b.eur - a.eur);
	});

	// ---- geometry ---------------------------------------------------------
	let width = $state(900);
	const ROW = 22;
	const M = { top: 34, left: 8, right: 8 };
	const restingRows = $derived(Math.max(restingLeft.length, restingRight.length));
	const height = $derived(
		M.top + Math.max(restingRows, displayLeft.length, displayRight.length) * ROW + 10
	);
	const colR = $derived(width - 290);
	const leftY = $derived(new Map(displayLeft.map((c, i) => [c.vat, M.top + i * ROW])));
	const rightY = $derived(new Map(displayRight.map((r, i) => [r.pe, M.top + i * ROW])));

	// ---- edges ------------------------------------------------------------
	const activeEdges = $derived.by(() => {
		if (!selected) {
			// resting: the 12 biggest links whose BOTH ends are on show
			return edges
				.filter((e) => restingLeftSet.has(e.vat) && restingRightSet.has(e.pe))
				.slice(0, 12);
		}
		return edges.filter((e) =>
			selected!.kind === 'vat' ? e.vat === selected!.id : e.pe === selected!.id
		);
	});
	const maxEdge = $derived(Math.max(...activeEdges.map((e) => e.eur), 1));

	function toggle(kind: 'vat' | 'pe', id: string) {
		selected = selected?.kind === kind && selected.id === id ? null : { kind, id };
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		<text class="col-title" x={M.left} y={16}>
			Top contractors (of {grInt(Object.keys(contractors).length)})
		</text>
		<text class="col-title" x={colR} y={16}>Works in regional unit</text>

		{#each activeEdges as e (e.vat + '→' + e.pe)}
			{@const y1 = leftY.get(e.vat)}
			{@const y2 = rightY.get(e.pe)}
			{#if y1 !== undefined && y2 !== undefined}
				<path
					class="edge"
					d="M 250 {y1} C {width / 2} {y1}, {width / 2} {y2}, {colR - 10} {y2}"
					stroke-width={1 + 6 * Math.sqrt(e.eur / maxEdge)}
				/>
			{/if}
		{/each}

		{#each displayLeft as c (c.vat)}
			{@const y = leftY.get(c.vat)!}
			<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
			<g
				class="node"
				class:dim={(selected?.kind === 'vat' && selected.id !== c.vat) ||
					(linkedVats !== null && !linkedVats.has(c.vat))}
				class:on={selected?.kind === 'vat' && selected.id === c.vat}
				onclick={() => toggle('vat', c.vat)}
				animate:flip={{ duration: 250 }}
			>
				<text class="name" x={246} y={y + 4} text-anchor="end">
					{c.name.length > 34 ? c.name.slice(0, 33) + '…' : c.name}
				</text>
				<circle cx={250} cy={y} r="3" />
			</g>
		{/each}

		{#each displayRight as r (r.pe)}
			{@const y = rightY.get(r.pe)!}
			<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
			<g
				class="node"
				class:dim={(selected?.kind === 'pe' && selected.id !== r.pe) ||
					(linkedPes !== null && !linkedPes.has(r.pe))}
				class:on={selected?.kind === 'pe' && selected.id === r.pe}
				onclick={() => toggle('pe', r.pe)}
				animate:flip={{ duration: 250 }}
			>
				<circle cx={colR - 10} cy={y} r="3" />
				<text class="name" x={colR - 2} y={y + 4}>
					{peEn(r.pe)}
					<tspan class="val"> {eurShort(r.eur)}</tspan>
				</text>
			</g>
		{/each}
	</svg>

	<!-- the resting instruction left for the frame's ⓘ (user, 2026-08-21);
	     only the selection's own line remains -->
	{#if selected}
		<p class="hint">
			{#if selected.kind === 'vat'}
				<a href={`/antinero/contractor/${selected.id}`}>
					{contractors[selected.id]?.name} →
				</a>
				works in {activeEdges.length} region{activeEdges.length === 1 ? '' : 's'} —
				{eurShort(activeEdges.reduce((s, e) => s + e.eur, 0))}. Click again to clear.
			{:else}
				{peEn(selected.id)}: {activeEdges.length} contractors,
				{eurShort(activeEdges.reduce((s, e) => s + e.eur, 0))}. Click again to clear.
			{/if}
		</p>
	{/if}
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	/* the column titles in the legend strips' lettering — 14px, regular,
	   black (user, 2026-08-21) */
	.col-title {
		font-size: 14px;
		font-weight: 400;
		fill: #111111;
	}
	.edge {
		fill: none;
		stroke: var(--ink);
		opacity: 0.35;
	}
	.node {
		cursor: pointer;
	}
	.node text {
		font-size: 12px;
		fill: var(--ink);
	}
	.node circle {
		fill: var(--ink-soft);
	}
	.node.dim {
		opacity: 0.3;
	}
	.node.on text {
		font-weight: 700;
		fill: var(--ink);
	}
	.node:hover text {
		fill: var(--ink);
	}
	.val {
		fill: var(--ink-faint);
		font-size: 11px;
	}
	.hint {
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
</style>
