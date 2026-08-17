<script lang="ts">
	/** Two-column categorical flow (d3-sankey): who awards THROUGH whom.
	 *  Ribbon width = €, coloured by the receiving side so the map's kind
	 *  palette carries over. The per-contract average is printed ON every
	 *  ribbon wide enough to hold it — that is the finding (two bodies
	 *  reaching the same unit type at very different scales), so it must
	 *  not hide in a tooltip. Hovering a node dims the rest. */
	import { sankey as d3sankey, sankeyLinkHorizontal, type SankeyGraph } from 'd3-sankey';
	import { eurShort, grInt } from '$lib/transforms/format';

	export interface FlowNode {
		id: string;
		label: string;
		color: string;
		/** which column: left, middle, right — decides where the label sits */
		side: 'l' | 'm' | 'r';
		n: number;
		eur: number;
		href?: string;
	}
	export interface FlowLink {
		s: string;
		t: string;
		n: number;
		eur: number;
	}
	interface Props {
		nodes: FlowNode[];
		links: FlowLink[];
		height?: number;
		/** column headings, left → right */
		headings?: string[];
		/** explanation beside the chart, in the same 210px side column the
		 *  beeswarm uses — so both charts on the page draw at one width */
		note?: string;
		/** href for the Methodology link closing the side note */
		methodologyHref?: string;
	}
	// tall enough, and padded enough, that the two-line label of even a
	// hairline node (a category worth 0,7% of the €) clears its neighbours
	let {
		nodes,
		links,
		height = 460,
		headings = [],
		note = '',
		methodologyHref = ''
	}: Props = $props();

	type NodeExtra = FlowNode;
	let width = $state(900);

	// ONLY the left column wraps: two short rows there cost no height (its
	// 5 nodes sit far apart) and buy a narrow left margin, which shifts the
	// whole plot left and pays for a right margin wide enough to print
	// co-op names on ONE line. Wrapping the tall right column instead would
	// push the chart past a screenful.
	const LINE = 14;
	const NOWRAP = 999;
	// 20 is the width that splits «decentralized administrations» while
	// keeping «other public bodies» on one line — at 18 the latter wrapped
	// into the value of the node above it
	const WRAP: Record<FlowNode['side'], number> = { l: 20, m: NOWRAP, r: NOWRAP };

	// the middle column's label rides above its node, so the top margin is
	// exactly as deep as that label is tall
	const midRows = $derived(
		Math.max(
			0,
			...nodes.filter((n) => n.side === 'm').map((n) => wrapLabel(n.label, WRAP.m).length + 1)
		)
	);
	const M = $derived({
		top: (headings.length ? 42 : 18) + (midRows ? midRows * LINE + 8 : 0),
		// off-centre to the left: the right column needs room for whole
		// co-op names (widest measures 339px), the left column's wrapped
		// labels need very little
		right: 356,
		bottom: 30,
		left: 124
	});

	// d3-sankey throws «Invalid array length» on an empty graph, and
	// silently produces NaN geometry when a link names a missing node —
	// so degrade to nothing rather than take the page down with us
	const ids = $derived(new Set(nodes.map((n) => n.id)));
	const safeLinks = $derived(links.filter((l) => ids.has(l.s) && ids.has(l.t) && l.eur > 0));
	const drawable = $derived(nodes.length > 0 && safeLinks.length > 0);

	const graph = $derived.by((): SankeyGraph<NodeExtra, FlowLink> | null => {
		if (!drawable) return null;
		const gen = d3sankey<NodeExtra, FlowLink>()
			.nodeId((d) => d.id)
			.nodeWidth(11)
			// single-row labels (name + €) need ~28px; this clears them
			.nodePadding(30)
			.nodeSort(null)
			.linkSort(null)
			.extent([
				[M.left, M.top],
				[Math.max(M.left + 60, width - M.right), height - M.bottom]
			]);
		const g = gen({
			nodes: nodes.map((n) => ({ ...n })),
			links: safeLinks.map((l) => ({ ...l, source: l.s, target: l.t, value: l.eur }))
		});

		// Every column carries the same € total, so they differ only by how
		// much padding their node count adds — d3 packs each from the top,
		// which leaves the 5- and 3-node columns riding high against the
		// 11-node one. Centre each column's extent on the plot's middle;
		// link ends move with the column they touch, so ribbons still meet
		// their nodes. Column HEADINGS are drawn at a fixed y and stay put.
		const depthOf = (n: unknown) => (n as { depth?: number }).depth ?? 0;
		const mid = (M.top + (height - M.bottom)) / 2;
		const spans = new Map<number, { top: number; bottom: number }>();
		for (const n of g.nodes) {
			const d = depthOf(n);
			const s = spans.get(d) ?? { top: Infinity, bottom: -Infinity };
			s.top = Math.min(s.top, n.y0 ?? 0);
			s.bottom = Math.max(s.bottom, n.y1 ?? 0);
			spans.set(d, s);
		}
		const shift = new Map<number, number>();
		for (const [d, s] of spans) shift.set(d, mid - (s.top + s.bottom) / 2);
		for (const n of g.nodes) {
			const dy = shift.get(depthOf(n)) ?? 0;
			n.y0 = (n.y0 ?? 0) + dy;
			n.y1 = (n.y1 ?? 0) + dy;
		}
		for (const l of g.links) {
			l.y0 = (l.y0 ?? 0) + (shift.get(depthOf(l.source)) ?? 0);
			l.y1 = (l.y1 ?? 0) + (shift.get(depthOf(l.target)) ?? 0);
		}
		return g;
	});

	// hover card on the BARS only, carrying the one number the chart does
	// not print: how many contracts stand behind that bar's €
	let tip = $state<{ x: number; y: number; text: string } | null>(null);
	let box = $state<HTMLDivElement | null>(null);
	function showTip(e: MouseEvent, text: string) {
		const r = box?.getBoundingClientRect();
		tip = { x: e.clientX - (r?.left ?? 0), y: e.clientY - (r?.top ?? 0), text };
	}
	const hideTip = () => (tip = null);

	let hot = $state<string | null>(null);
	const nodeOf = (v: unknown) =>
		v as FlowNode & { x0: number; x1: number; y0: number; y1: number; depth: number };
	function wrapLabel(s: string, max: number): string[] {
		if (s.length <= max) return [s];
		const lines: string[] = [];
		let cur = '';
		for (const w of s.split(' ')) {
			if (cur && (cur + ' ' + w).length > max) {
				lines.push(cur);
				cur = w;
			} else cur = cur ? cur + ' ' + w : w;
		}
		if (cur) lines.push(cur);
		return lines;
	}
	const dim = (l: { source: unknown; target: unknown }) =>
		!!hot && nodeOf(l.source).id !== hot && nodeOf(l.target).id !== hot;

	// one heading per column, centred on that column's coloured bar
	const headingXs = $derived.by(() => {
		if (!graph || !headings.length) return [];
		const xs = [...new Set(graph.nodes.map((n) => Math.round(n.x0 ?? 0)))].sort((a, b) => a - b);
		return xs
			.map((x, i) => ({ text: headings[i] ?? '', x: x + 5.5 }))
			.filter((h) => h.text);
	});
</script>

<div class="cols" class:nonote={!note}>
	{#if note}
		<p class="sidenote">
			{note}
			{#if methodologyHref}<a href={methodologyHref}>Methodology</a>{/if}
		</p>
	{/if}
	<div class="wrap" bind:clientWidth={width} bind:this={box}>
	{#if tip}
		<div
			class="tip"
			style:left="{tip.x}px"
			style:top="{tip.y}px"
			style:transform={tip.x > width * 0.62 ? 'translate(-100%, -130%)' : 'translate(10px, -130%)'}
		>
			{tip.text}
		</div>
	{/if}
	{#if graph}
	<svg viewBox="0 0 {width} {height}" style:height="{height}px" role="img">
		{#each graph.links as l, i (i)}
			{@const s = nodeOf(l.source)}
			{@const t = nodeOf(l.target)}
			{@const w = Math.max(1, l.width ?? 1)}
			<g class="lk" class:dim={dim(l)}>
				<path
					d={sankeyLinkHorizontal()(l) ?? ''}
					stroke={s.side === 'm' ? s.color : t.color}
					stroke-width={w}
				/>
			</g>
		{/each}
		{#each graph.nodes as n (n.id)}
			{@const y0 = n.y0 ?? 0}
			{@const h = (n.y1 ?? 0) - y0}
			{@const mid = n.side === 'm'}
			{@const lx = mid
				? ((n.x0 ?? 0) + (n.x1 ?? 0)) / 2
				: n.side === 'l'
					? (n.x0 ?? 0) - 8
					: (n.x1 ?? 0) + 8}
			{@const lines = wrapLabel(n.label, WRAP[n.side])}
			{@const y1 = mid
				? y0 - 8 - lines.length * LINE
				: y0 + h / 2 - (lines.length * LINE) / 2}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<g
				onmouseenter={() => (hot = n.id)}
				onmousemove={(e) => showTip(e, `${grInt(n.n)} contracts`)}
				onmouseleave={() => {
					hot = null;
					hideTip();
				}}
			>
				<rect x={n.x0 ?? 0} y={y0} width={(n.x1 ?? 0) - (n.x0 ?? 0)} height={h} fill={n.color} />
				<!-- middle labels sit ABOVE their node: beside it they would
				     land in the ribbon corridor. Long names wrap onto further
				     rows; the contract count lives in the hover card. -->
				<text
					class="label"
					text-anchor={mid ? 'middle' : n.side === 'l' ? 'end' : 'start'}
				>
					{#if n.href}
						<a href={n.href}>
							{#each lines as ln, i (i)}<tspan x={lx} y={y1 + i * LINE}>{ln}</tspan>{/each}
						</a>
					{:else}
						{#each lines as ln, i (i)}<tspan x={lx} y={y1 + i * LINE}>{ln}</tspan>{/each}
					{/if}
					<tspan class="value" x={lx} y={y1 + lines.length * LINE}>{eurShort(n.eur)}</tspan>
				</text>
			</g>
		{/each}
		{#each headingXs as hd (hd.text)}
			<text class="colhead" x={hd.x} y={headings.length ? 22 : 0} text-anchor="middle"
				>{hd.text}</text
			>
		{/each}
	</svg>
	{/if}
	</div>
</div>

<style>
	/* optional beeswarm-style side note; without one the chart takes the
	   frame's full width, like the map + legend row */
	.cols {
		display: grid;
		grid-template-columns: 210px minmax(0, 1fr);
		gap: var(--sp-6);
		align-items: start;
	}
	.cols.nonote {
		grid-template-columns: minmax(0, 1fr);
	}
	@media (max-width: 800px) {
		.cols {
			grid-template-columns: 1fr;
		}
	}
	.sidenote {
		color: var(--ink-soft);
		font-size: var(--fs-13);
		margin: 0;
	}
	.wrap {
		position: relative;
	}
	/* hover card — black plate, white lettering, like the map cards */
	.tip {
		position: absolute;
		z-index: 3;
		pointer-events: none;
		display: grid;
		gap: 1px;
		padding: 7px 10px;
		border-radius: 4px;
		background: #000;
		color: #fff;
		font-size: var(--fs-12);
		line-height: 1.25;
		white-space: nowrap;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
	}
	svg {
		display: block;
		width: 100%;
	}
	.lk path {
		fill: none;
		opacity: 0.42;
		transition: opacity 0.12s;
	}
	.lk:hover path {
		opacity: 0.62;
	}
	.lk.dim path {
		opacity: 0.08;
	}
	rect {
		shape-rendering: crispEdges;
	}
	.label {
		font-size: var(--fs-13);
		fill: var(--ink);
		dominant-baseline: middle;
	}
	.label a {
		fill: var(--ink);
	}
	.label a:hover {
		fill: var(--c-dase-deep, var(--accent));
	}
	.colhead {
		font-family: var(--font-display);
		font-size: var(--fs-12);
		font-weight: 900;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		fill: var(--ink-soft);
	}
	.value {
		fill: var(--ink-faint);
		font-size: 11px;
	}
</style>
