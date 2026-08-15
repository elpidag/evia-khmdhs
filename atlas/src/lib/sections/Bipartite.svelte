<script lang="ts">
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
	}
	let { edges, contractors, topContractors = 25 }: Props = $props();

	const left = $derived(
		Object.entries(contractors)
			.sort((a, b) => b[1].eur - a[1].eur)
			.slice(0, topContractors)
			.map(([vat, c]) => ({ vat, ...c }))
	);
	const leftSet = $derived(new Set(left.map((c) => c.vat)));
	const right = $derived.by(() => {
		const agg = new Map<string, number>();
		for (const e of edges) agg.set(e.pe, (agg.get(e.pe) ?? 0) + e.eur);
		return [...agg.entries()].sort((a, b) => b[1] - a[1]).map(([pe, eur]) => ({ pe, eur }));
	});

	let width = $state(900);
	const ROW = 22;
	const M = { top: 34, left: 8, right: 8 };
	const height = $derived(M.top + Math.max(left.length, right.length) * ROW + 10);
	const colR = $derived(width - 290);

	const leftY = $derived(new Map(left.map((c, i) => [c.vat, M.top + i * ROW])));
	const rightY = $derived(new Map(right.map((r, i) => [r.pe, M.top + i * ROW])));

	let selected = $state<{ kind: 'vat' | 'pe'; id: string } | null>(null);

	const activeEdges = $derived.by(() => {
		if (!selected) {
			// default: the 12 biggest edges among the visible contractors
			return edges.filter((e) => leftSet.has(e.vat)).slice(0, 12);
		}
		return edges.filter((e) =>
			selected!.kind === 'vat' ? e.vat === selected!.id : e.pe === selected!.id
		);
	});
	const activeVats = $derived(new Set(activeEdges.map((e) => e.vat)));
	const activePes = $derived(new Set(activeEdges.map((e) => e.pe)));
	const maxEdge = $derived(Math.max(...activeEdges.map((e) => e.eur), 1));

	function toggle(kind: 'vat' | 'pe', id: string) {
		selected = selected?.kind === kind && selected.id === id ? null : { kind, id };
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		<text class="col-title" x={M.left} y={16}>
			Top {topContractors} contractors (of {grInt(Object.keys(contractors).length)})
		</text>
		<text class="col-title" x={colR} y={16}>Work regions</text>

		{#each activeEdges as e, i (i)}
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

		{#each left as c (c.vat)}
			{@const y = leftY.get(c.vat)!}
			<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
			<g
				class="node"
				class:dim={selected !== null && !activeVats.has(c.vat)}
				class:on={selected?.kind === 'vat' && selected.id === c.vat}
				onclick={() => toggle('vat', c.vat)}
			>
				<text class="name" x={246} y={y + 4} text-anchor="end">
					{c.name.length > 34 ? c.name.slice(0, 33) + '…' : c.name}
				</text>
				<circle cx={250} cy={y} r="3" />
			</g>
		{/each}

		{#each right as r (r.pe)}
			{@const y = rightY.get(r.pe)!}
			<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
			<g
				class="node"
				class:dim={selected !== null && !activePes.has(r.pe)}
				class:on={selected?.kind === 'pe' && selected.id === r.pe}
				onclick={() => toggle('pe', r.pe)}
			>
				<circle cx={colR - 10} cy={y} r="3" />
				<text class="name" x={colR - 2} y={y + 4}>
					{peEn(r.pe)}
					<tspan class="val"> {eurShort(r.eur)}</tspan>
				</text>
			</g>
		{/each}
	</svg>

	<p class="hint">
		{#if selected}
			{#if selected.kind === 'vat'}
				<a href={`/antinero/contractor/${selected.id}`}>
					{contractors[selected.id]?.name} →
				</a>
				works with {activeEdges.length} region{activeEdges.length === 1 ? '' : 's'} —
				{eurShort(activeEdges.reduce((s, e) => s + e.eur, 0))}. Click again to clear.
			{:else}
				{selected.id}: {activeEdges.length} contractors,
				{eurShort(activeEdges.reduce((s, e) => s + e.eur, 0))}. Click again to clear.
			{/if}
		{:else}
			Showing the 12 largest contractor→region links. Click any name to isolate its
			connections.
		{/if}
	</p>
</div>

<style>
	svg {
		display: block;
		width: 100%;
	}
	.col-title {
		font-size: 12px;
		font-weight: 600;
		fill: var(--ink-soft);
	}
	.edge {
		fill: none;
		stroke: var(--accent);
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
		fill: var(--accent);
	}
	.node:hover text {
		fill: var(--accent);
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
