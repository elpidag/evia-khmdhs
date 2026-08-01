<script lang="ts">
	import type { SankeyPayload } from '$lib/api';
	import { eurShort } from '$lib/transforms/format';
	import { scopeColor } from '$lib/transforms/scopes';
	import {
		sankey as d3sankey,
		sankeyLinkHorizontal,
		type SankeyGraph,
		type SankeyLink,
		type SankeyNode
	} from 'd3-sankey';

	let { data }: { data: SankeyPayload } = $props();

	type NodeExtra = { id: string; label: string; kind: string; n?: number };
	type Node = SankeyNode<NodeExtra, object>;
	type Link = SankeyLink<NodeExtra, object>;

	let width = $state(900);
	const height = 560;
	const M = { top: 10, right: 250, bottom: 10, left: 70 };

	const graph = $derived.by((): SankeyGraph<NodeExtra, object> => {
		const gen = d3sankey<NodeExtra, object>()
			.nodeId((d) => d.id)
			.nodeWidth(12)
			.nodePadding(14)
			.nodeSort(null)
			.extent([
				[M.left, M.top],
				[width - M.right, height - M.bottom]
			]);
		return gen({
			nodes: data.nodes.map((n) => ({ ...n })),
			links: data.links.map((l) => ({ source: l.s, target: l.t, value: l.eur }))
		});
	});

	let hovered = $state<string | null>(null);

	function nodeColor(n: Node): string {
		if (n.kind === 'ministry') return 'var(--ink)';
		if (n.kind === 'phase') return scopeColor(n.id);
		if (n.kind === 'rest') return 'var(--ink-faint)';
		return 'var(--accent)';
	}
	function linkDim(l: Link): boolean {
		if (!hovered) return false;
		return (l.source as Node).id !== hovered && (l.target as Node).id !== hovered;
	}
	function nodeHref(n: Node): string | null {
		return n.kind === 'contractor' ? `/antinero/contractor/${n.id}` : null;
	}
</script>

<div class="wrap" bind:clientWidth={width}>
	<svg viewBox="0 0 {width} {height}" style:height="{height}px">
		{#each graph.links as l, i (i)}
			<path
				class="link"
				class:dim={linkDim(l)}
				d={sankeyLinkHorizontal()(l)}
				stroke={scopeColor(
					(l.source as Node).kind === 'phase' ? (l.source as Node).id : (l.target as Node).id
				)}
				stroke-width={Math.max(1, l.width ?? 1)}
			/>
		{/each}
		{#each graph.nodes as n (n.id)}
			{@const x0 = n.x0 ?? 0}
			{@const y0 = n.y0 ?? 0}
			{@const h = (n.y1 ?? 0) - y0}
			{@const href = nodeHref(n)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<g
				onmouseenter={() => (hovered = n.id)}
				onmouseleave={() => (hovered = null)}
			>
				<rect x={x0} y={y0} width={(n.x1 ?? 0) - x0} height={h} fill={nodeColor(n)} />
				{#if n.kind === 'ministry'}
					<text class="label ministry" x={x0 - 6} y={y0 + h / 2} text-anchor="end">
						{n.label}
						<tspan class="value" x={x0 - 6} dy="14">{eurShort(n.value ?? 0)}</tspan>
					</text>
				{:else if n.kind === 'phase'}
					<text class="label" x={x0 - 6} y={y0 + h / 2} text-anchor="end">
						{n.label}
						<tspan class="value"> {eurShort(n.value ?? 0)}</tspan>
					</text>
				{:else}
					<text class="label" x={(n.x1 ?? 0) + 6} y={Math.max(y0 + h / 2, y0 + 5)}>
						{#if href}<a {href}>{n.label.length > 34 ? n.label.slice(0, 33) + '…' : n.label}</a
							>{:else}{n.label}{/if}
						<tspan class="value"> {eurShort(n.value ?? 0)}</tspan>
					</text>
				{/if}
			</g>
		{/each}
	</svg>
</div>

<style>
	.wrap {
		position: relative;
	}
	svg {
		display: block;
		width: 100%;
	}
	.link {
		fill: none;
		opacity: 0.35;
		transition: opacity 0.12s;
	}
	.link.dim {
		opacity: 0.07;
	}
	rect {
		shape-rendering: crispEdges;
	}
	.label {
		font-size: 12px;
		fill: var(--ink);
		dominant-baseline: middle;
	}
	.label.ministry {
		font-weight: 700;
		font-size: 14px;
	}
	.label a {
		fill: var(--ink);
	}
	.label a:hover {
		fill: var(--accent);
	}
	.value {
		fill: var(--ink-faint);
		font-size: 11px;
	}
</style>
