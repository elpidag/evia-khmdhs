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
		/** geometry overrides for a TWO-column graph (the Anti-nero MONEY FLOW,
		 *  user 2026-08-21): symmetric margins centre the plot, a wider left
		 *  wrap and more node padding keep long unit names off each other;
		 *  the ΔΑΣΕ three-column call keeps the defaults */
		marginLeft?: number;
		marginRight?: number;
		wrapLeft?: number;
		/** the middle column's labels sit ABOVE their nodes and do not wrap by
		 *  default (ΔΑΣΕ's three kinds are short); the Anti-nero units are
		 *  long names and wrap (user, 2026-08-22) */
		wrapMid?: number;
		nodePad?: number;
		/** a BRACE in the left margin spanning the whole left column, with a
		 *  name along it — «these all belong to …» said diagrammatically
		 *  (user, 2026-08-22: the four ΥΠΕΝ units) */
		leftGroup?: string;
		/** how a node's value prints (default €) — a flow of COUNTS passes a
		 *  count formatter */
		fmt?: (v: number) => string;
		/** WHERE each column stands, left → right: the centre of column i as a
		 *  fraction of the drawing's width (0–1) or an absolute x in drawing
		 *  units (>1); `null` leaves that column where d3 put it. Set it to
		 *  place the columns by hand — e.g. `columnX={[0.16, 0.5, 0.84]}`
		 *  (user, 2026-08-22). The ribbons and the headings follow. */
		columnX?: (number | null)[] | null;
	}
	// tall enough, and padded enough, that the two-line label of even a
	// hairline node (a category worth 0,7% of the €) clears its neighbours
	let {
		nodes,
		links,
		height = 460,
		headings = [],
		note = '',
		methodologyHref = '',
		marginLeft = 124,
		marginRight = 356,
		wrapLeft = 20,
		wrapMid = 999,
		nodePad = 30,
		leftGroup = '',
		fmt = eurShort,
		columnX = null
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
	// the breath between two side-label blocks («again more», user 2026-08-22)
	const LABEL_GAP = 34;
	// 20 is the width that splits «decentralized administrations» while
	// keeping «other public bodies» on one line — at 18 the latter wrapped
	// into the value of the node above it
	const WRAP = $derived<Record<FlowNode['side'], number>>({ l: wrapLeft, m: wrapMid, r: NOWRAP });

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
		right: marginRight,
		bottom: 30,
		left: marginLeft
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
			.nodePadding(nodePad)
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
		// The MIDDLE column sits at the CENTRE of the drawing (user, 2026-08-22).
		// With EQUAL outer margins d3's own even spacing already puts it there
		// and this is a no-op; it only corrects a call-site whose label margins
		// differ, and then the ribbons follow (`sankeyLinkHorizontal` reads the
		// nodes' own x0/x1) as do the headings (derived from x0). The two gaps
		// stay equal as long as the margins are.
		const depths = [...new Set(g.nodes.map(depthOf))].sort((a, b) => a - b);
		const nodeW = g.nodes.reduce((w, n) => Math.max(w, (n.x1 ?? 0) - (n.x0 ?? 0)), 0);
		// where each column stands: `columnX` if the caller placed them by
		// hand, else the middle of three on the drawing's centre (with equal
		// outer margins d3 already puts it there and this is a no-op)
		const centres = depths.map((d, i) => {
			const given = columnX?.[i];
			if (given !== null && given !== undefined)
				return given <= 1 ? given * width : given;
			return depths.length === 3 && i === 1 ? width / 2 : null;
		});
		depths.forEach((d, i) => {
			const c = centres[i];
			if (c === null) return;
			const have = Math.min(...g.nodes.filter((n) => depthOf(n) === d).map((n) => n.x0 ?? 0));
			const dx = c - nodeW / 2 - have;
			if (!dx) return;
			for (const n of g.nodes)
				if (depthOf(n) === d) {
					n.x0 = (n.x0 ?? 0) + dx;
					n.x1 = (n.x1 ?? 0) + dx;
				}
		});

		// Side labels never overprint: down each side column, two label
		// blocks (name rows + value row) closer than LABEL_GAP give way
		// EQUALLY — the upper node moves up, the lower down — and the NODE
		// moves with its label, its ribbons following (user, 2026-08-21/22:
		// the rectangle must stay centred on its text).
		for (const side of ['l', 'm', 'r'] as const) {
			const col = g.nodes.filter((n) => n.side === side).sort((a, b) => (a.y0 ?? 0) - (b.y0 ?? 0));
			const blocks = col.map((n) => {
				const rows = wrapLabel(n.label, WRAP[n.side]).length + 1;
				if (side === 'm') {
					// label ABOVE the node: the block is label + node together
					const top = (n.y0 ?? 0) - 8 - rows * LINE;
					return { n, top, top0: top, hgt: (n.y1 ?? 0) - top };
				}
				const hgt = (rows - 1) * LINE + 4;
				const c = ((n.y0 ?? 0) + (n.y1 ?? 0)) / 2;
				return { n, top: c - ((rows - 1) * LINE) / 2, top0: c - ((rows - 1) * LINE) / 2, hgt };
			});
			// the left column's few long names breathe by LABEL_GAP; the right
			// column's many short rows only need not to touch (8 px) — and a
			// block that would rise above the plot's top stays put, the one
			// below it taking the whole overlap (the first two contractors
			// overprinted when the top block was clamped afterwards)
			const gap = side === 'l' ? LABEL_GAP : side === 'm' ? 12 : 8;
			for (let pass = 0; pass < 10; pass++) {
				for (let i = 1; i < blocks.length; i++) {
					const a = blocks[i - 1];
					const b = blocks[i];
					const overlap = a.top + a.hgt + gap - b.top;
					if (overlap > 0) {
						const up = Math.min(overlap / 2, Math.max(0, a.top - M.top));
						a.top -= up;
						b.top += overlap - up;
					}
				}
			}
			for (const b of blocks) {
				const dy = b.top - b.top0;
				if (!dy) continue;
				b.n.y0 = (b.n.y0 ?? 0) + dy;
				b.n.y1 = (b.n.y1 ?? 0) + dy;
				for (const l of g.links) {
					if (l.source === b.n) l.y0 = (l.y0 ?? 0) + dy;
					if (l.target === b.n) l.y1 = (l.y1 ?? 0) + dy;
				}
			}
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
	// the brace: from the first left label's top to the last one's foot,
	// just left of the widest label the column can wrap to
	const CHAR_W = 6.6;
	const brace = $derived.by(() => {
		if (!graph || !leftGroup) return null;
		const col = graph.nodes.filter((n) => n.side === 'l');
		if (!col.length) return null;
		let top = Infinity;
		let bottom = -Infinity;
		let x0 = Infinity;
		for (const n of col) {
			const rows = wrapLabel(n.label, WRAP.l).length + 1;
			const c = ((n.y0 ?? 0) + (n.y1 ?? 0)) / 2;
			const lt = c - ((rows - 2) * LINE) / 2 - LINE;
			top = Math.min(top, lt);
			bottom = Math.max(bottom, lt + rows * LINE);
			x0 = Math.min(x0, n.x0 ?? 0);
		}
		const x = Math.max(14, x0 - 8 - Math.min(WRAP.l, 40) * CHAR_W - 16);
		return { x, top, bottom, mid: (top + bottom) / 2 };
	});

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
					stroke={s.side === 'm' || (s.side === 'l' && t.side === 'r') ? s.color : t.color}
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
					<tspan class="value" x={lx} y={y1 + lines.length * LINE}>{fmt(n.eur)}</tspan>
				</text>
			</g>
		{/each}
		{#if brace}
			<!-- the brace: a thin line with two end hooks, the group's name
			     written along it, rotated -->
			<path
				class="brace"
				d={`M ${brace.x + 6} ${brace.top} L ${brace.x} ${brace.top} L ${brace.x} ${brace.bottom} L ${brace.x + 6} ${brace.bottom}`}
			/>
			<text
				class="bracelbl"
				x={brace.x - 6}
				y={brace.mid}
				text-anchor="middle"
				transform={`rotate(-90 ${brace.x - 6} ${brace.mid})`}>{leftGroup}</text
			>
		{/if}
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
		background: var(--ink);
		color: var(--paper);
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
		/* the accent, not a colour of its own: --c-dase-deep was retired
		   (author, 2026-09-03) — its navy printed only in this hover and
		   broke the Anti-nero page's grayscale doctrine */
		fill: var(--accent);
		text-decoration: underline;
	}
	.brace {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1;
	}
	.bracelbl {
		font-family: var(--font-display);
		font-size: var(--fs-12);
		font-weight: 900;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		fill: var(--ink);
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
