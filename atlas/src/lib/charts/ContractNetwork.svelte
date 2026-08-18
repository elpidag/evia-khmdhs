<script lang="ts">
	/**
	 * The whole programme, one circle per in-scope contract: area ∝ stated
	 * net €, colour = programme phase. The toggle REARRANGES that same
	 * population — see $lib/transforms/networkScene for what position means
	 * in each mode — and because the marks are one keyed list, a contract
	 * keeps its DOM node and animates from one arrangement to the next.
	 *
	 * Everything load-bearing is printed on the chart: each circle carries
	 * its own money where it fits, each call bubble its ΑΔΑΜ along the top
	 * edge, and the timeline shades Greece's fire season. The hover card is
	 * identity only — ΑΔΑΜ and amount.
	 */
	import { interpolateRgb } from 'd3-interpolate';
	import { type NetNode, type Placed } from '$lib/transforms/network';
	import { NET_HEIGHT, scene, type NetMode, type Season } from '$lib/transforms/networkScene';
	import { eur, eurShort, eurTiny, grInt } from '$lib/transforms/format';
	import { SCOPE_COLORS, SCOPE_ORDER, scopeLabel } from '$lib/transforms/scopes';

	interface Props {
		nodes: NetNode[];
		stats: Record<string, number>;
		mode: NetMode;
		season: Season & { n_contracts: number };
	}
	let { nodes, stats, mode, season }: Props = $props();

	const W = 1120;
	const copy = $derived({
		single: `${grInt(stats.n_single_call)} calls produced exactly one contract`,
		none: `${grInt(stats.n_no_call)} contracts have no call at all — direct awards and negotiations`,
		eurShort,
		eurTiny
	});
	const sc = $derived(scene(mode, nodes, W, copy, NET_HEIGHT, season));
	const phases = $derived(SCOPE_ORDER.filter((p) => nodes.some((n) => n.phase === p)));
	const inGroup = $derived(new Set(sc.marks.filter((n) => n.group >= 0).map((n) => n.ref)));

	let hover = $state<Placed | null>(null);
	const hue = (p?: string | null) => SCOPE_COLORS[p ?? ''] ?? '#9a9a9a';
	const lighten = (c: string, t: number) => interpolateRgb(c, '#ffffff')(t);
	const darken = (c: string, t: number) => interpolateRgb(c, '#000000')(t);
	/** a lot inside a call bubble is a lighter tint of the bubble's own hue */
	const fill = (n: Placed) =>
		mode === 'pack' && inGroup.has(n.ref) ? lighten(hue(n.phase), 0.42) : hue(n.phase);
	/** the call's name on its rim: dark ink on a light hue, light on a dark
	 *  one — the same contrast rule the reference packed-circle maps use */
	const arcInk = (p?: string | null) => {
		const h = hue(p);
		return ink(h) === '#1a1a1a' ? darken(h, 0.55) : lighten(h, 0.74);
	};
	const ink = (c: string) => {
		const m = c.match(/\d+/g);
		const [r, g, b] = m
			? m.map(Number)
			: [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
		return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#1a1a1a' : '#ffffff';
	};
	const dim = (n: Placed) =>
		!hover ? 1 : hover.call ? (n.call === hover.call ? 1 : 0.25) : n.ref === hover.ref ? 1 : 0.25;
	const tiePath = (pts: { x: number; y: number }[]) =>
		pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
	const markOf = $derived(new Map(sc.marks.map((n) => [n.ref, n])));
</script>

<figure class="net">
	<div class="key">
		{#each phases as p (p)}
			<span class="k"><i style:background={hue(p)}></i>{scopeLabel(p)}</span>
		{/each}
		{#if mode === 'time'}
			<span class="k sep"><i class="season"></i>fire season, 1 May – 31 October</span>
			<span class="k"><i class="tie"></i>joined: lots of the same call</span>
		{:else if mode === 'pack'}
			<span class="k sep"><i class="nocall"></i>bought with no call published</span>
		{/if}
	</div>

	<p class="lede">
		{#if mode === 'time'}
			<strong
				>{grInt(stats.n_same_day_calls)} of the {grInt(stats.n_multi_calls)} split calls signed
				every lot on a single day</strong
			> — each is one vertical join. {grInt(season.n_contracts)} of the
			{grInt(stats.n_contracts)} contracts were signed inside a fire season, the shaded stripes.
		{:else}
			<strong>In the middle, the {grInt(stats.n_multi_calls)} procurements that were split into
				lots</strong> — one bubble each, holding its contracts. Around them, every contract bought
			on its own: {grInt(stats.n_single_call)} whose call produced nothing else and
			{grInt(stats.n_no_call)} awarded with no call at all.
		{/if}
	</p>

	<svg
		viewBox={sc.view}
		style:max-width={sc.maxW ? `${sc.maxW}px` : null}
		role="img"
		aria-label="Every Anti-nero contract, arranged by {mode}"
	>
		{#each sc.seasons as s (s.key)}
			<rect x={s.x0} y={0} width={s.x1 - s.x0} height={sc.height - 18} class="season" />
		{/each}
		{#each sc.rules as r (r.key)}
			<line x1={r.x} y1={0} x2={r.x} y2={sc.height - 18} class="rule" />
		{/each}
		{#each sc.groups as g (g.key)}
			<circle cx={g.x} cy={g.y} r={g.r} fill={hue(g.phase)} class="group" />
		{/each}
		{#each sc.ties as t (t.call)}
			<path d={tiePath(t.pts)} class="tie" class:lit={hover?.call === t.call} />
		{/each}
		{#each sc.spokes as s (s.key)}
			<line x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} class="spoke" />
		{/each}
		{#each sc.bridges as b (b.key)}
			<line
				x1={b.x1}
				y1={b.y1}
				x2={b.x2}
				y2={b.y2}
				class="bridge"
				opacity={hover && !(b.vats ?? []).includes(hover.vat ?? '') ? 0.2 : 1}
			/>
		{/each}
		{#each sc.marks as n (n.ref)}
			<a
				href={`/antinero/contract/${n.ref}`}
				aria-label={`${n.ref}, ${eurShort(n.eur ?? 0)}`}
				onmouseenter={() => (hover = n)}
				onmouseleave={() => (hover = null)}
			>
				<circle
					cx={n.x}
					cy={n.y}
					r={n.r}
					fill={fill(n)}
					class="node"
					class:nocall={mode === 'pack' && !n.call}
					stroke={mode === 'pack' && !n.call ? darken(hue(n.phase), 0.45) : null}
					opacity={dim(n)}
				/>
			</a>
		{/each}
		{#each sc.arcs as a (a.key)}
			<path id={`arc-${a.key}`} d={a.d} fill="none" />
			<text class="arc" font-size={a.size} fill={arcInk(a.phase)} text-anchor="middle">
				<textPath href={`#arc-${a.key}`} startOffset="50%">{a.text}</textPath>
			</text>
		{/each}
		{#each sc.labels as l (l.key)}
			<text
				x={l.x}
				y={l.y}
				class={l.cls}
				text-anchor={l.anchor ?? 'middle'}
				font-size={l.size ?? null}
				fill={l.cls === 'leaf' && l.ref ? ink(fill(markOf.get(l.ref) as Placed)) : null}
				opacity={l.cls === 'leaf' && l.ref ? dim(markOf.get(l.ref) as Placed) : 1}>{l.text}</text
			>
		{/each}
	</svg>

	{#if hover}
		<div class="card">
			<strong class="tabular">{hover.ref}</strong>
			<span class="v">{eur(hover.eur)}</span>
		</div>
	{/if}
</figure>

<style>
	.net {
		margin: 0;
		position: relative;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		margin: 0 auto;
	}
	.node {
		transition:
			cx 0.55s cubic-bezier(0.4, 0, 0.2, 1),
			cy 0.55s cubic-bezier(0.4, 0, 0.2, 1),
			r 0.55s cubic-bezier(0.4, 0, 0.2, 1),
			opacity 0.12s;
	}
	.node.nocall {
		stroke-width: 1.4;
		stroke-dasharray: 3 2.5;
	}
	a:hover .node {
		stroke: #000;
		stroke-width: 1.4;
		stroke-dasharray: none;
	}
	.group {
		transition: all 0.55s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.spoke {
		stroke: #b4b4b4;
		stroke-width: 1;
	}
	.tie {
		/* a call whose lots were signed weeks apart draws a long line; kept
		   faint so the same-day verticals — the finding — carry the ink */
		fill: none;
		stroke: #cfccc6;
		stroke-width: 1;
	}
	.tie.lit {
		stroke: #000;
		stroke-width: 1.4;
	}
	.bridge {
		stroke: #000;
		stroke-width: 1;
		stroke-dasharray: 4 3;
	}
	.rule {
		stroke: var(--line);
		stroke-width: 1;
	}
	rect.season {
		fill: #f0e5d8;
	}
	.val {
		font-size: 9px;
		fill: var(--ink-soft);
	}
	.adam {
		font-size: 9px;
		fill: var(--ink);
		letter-spacing: 0.02em;
	}
	.band {
		font-size: 12px;
		fill: var(--ink);
		font-weight: 700;
	}
	.year {
		font-size: 11px;
		fill: var(--ink-soft);
	}
	text {
		/* a label sits ON its circle; without this it swallows the hover and
		   the click of the very mark it names */
		pointer-events: none;
	}
	.arc {
		letter-spacing: 0.06em;
		font-weight: 700;
	}
	.leaf {
		font-weight: 500;
	}
	.val,
	.adam,
	.band,
	.year {
		/* these sit on white paper or over marks; the halo keeps them legible
		   without hiding the circle underneath */
		paint-order: stroke;
		stroke: var(--paper);
		stroke-width: 3px;
		stroke-linejoin: round;
	}
	.key {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 14px;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.k {
		display: inline-flex;
		align-items: center;
		gap: 5px;
	}
	.k i {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		display: inline-block;
	}
	.k.sep {
		margin-left: auto;
	}
	.k i.tie {
		width: 16px;
		height: 0;
		border-radius: 0;
		border-top: 1.1px solid #8f8f8f;
	}
	.k i.season {
		width: 16px;
		height: 10px;
		border-radius: 0;
		background: #f0e5d8;
	}
	.k i.nocall {
		background: transparent;
		border: 1.4px dashed var(--ink-soft);
	}
	.lede {
		margin: var(--sp-3) 0 var(--sp-2);
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.lede strong {
		color: var(--ink);
	}
	.card {
		position: absolute;
		left: 0;
		bottom: 0;
		background: #000;
		color: #fff;
		padding: 8px 10px;
		display: grid;
		gap: 2px;
		font-size: var(--fs-12);
		pointer-events: none;
	}
	.card .v {
		font-weight: 700;
	}
</style>
