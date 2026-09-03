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
	import { resolveCssColor, cssLuminance } from '$lib/theme.svelte';
	import { type NetNode, type Placed } from '$lib/transforms/network';
	import { NET_HEIGHT, scene, type NetMode, type Season } from '$lib/transforms/networkScene';
	import { eur, eurShort, eurTiny, grInt } from '$lib/transforms/format';
	import { CAT_COLORS } from './catColors';

	interface Props {
		nodes: NetNode[];
		stats: Record<string, number>;
		mode: NetMode;
		/** the colour lens: the contract's scope or its curated type */
		lens?: 'scope' | 'type';
		/** category key → short English label (the type lens's key) */
		catLabels?: Record<string, string>;
		season: Season & { n_contracts: number };
	}
	let { nodes, stats, mode, lens = 'scope', catLabels = {}, season }: Props = $props();

	const W = 1120;
	const copy = $derived({
		single: `${grInt(stats.n_single_call)} calls produced exactly one contract`,
		none: `${grInt(stats.n_no_call)} contracts have no call at all — direct awards and negotiations`,
		eurShort,
		eurTiny
	});
	const sc = $derived(scene(mode, nodes, W, copy, NET_HEIGHT, season));
	// the colour is the SCOPE (deliverables kind) since 2026-08-22 — the
	// phases are funding envelopes and the x-axis already carries time; the
	// three tones are CONTRACT SCOPE's own, so one meaning site-wide
	const DK_ORDER = ['works', 'study_and_works', 'study'] as const;
	// stretched for legibility at 6px dots (user, 2026-08-22): near-black
	// vs light grey vs white-with-ring — the flip from the works-only 2022
	// era to the design-build template must read at a glance
	const DK_COLORS: Record<string, string> = {
		works: 'color-mix(in srgb, var(--ink) 92%, black)',
		study_and_works: 'color-mix(in srgb, var(--ink) 38.8%, var(--paper))',
		study: 'var(--paper)'
	};
	const DK_LABELS: Record<string, string> = {
		works: 'works only',
		study_and_works: 'study & works',
		study: 'study only'
	};
	const kinds = $derived(DK_ORDER.filter((k) => nodes.some((n) => n.phase === k)));
	const cats = $derived(
		Object.keys(CAT_COLORS).filter((k) => nodes.some((n) => n.cat === k))
	);
	const hasUdc = $derived(nodes.some((n) => n.udc));
	const inGroup = $derived(new Set(sc.marks.filter((n) => n.group >= 0).map((n) => n.ref)));

	let hover = $state<Placed | null>(null);
	const hue = (p?: string | null) => DK_COLORS[p ?? ''] ?? 'color-mix(in srgb, var(--ink) 44.9%, var(--paper))';
	const catHue = (c?: string | null) => CAT_COLORS[c ?? ''] ?? 'color-mix(in srgb, var(--ink) 44.9%, var(--paper))';
	const markHue = (n: { phase?: string | null; cat?: string | null }) =>
		lens === 'type' ? catHue(n.cat) : hue(n.phase);
	// palette entries are CSS strings over the tokens — resolve before d3
	const lighten = (c: string, t: number) =>
		interpolateRgb(resolveCssColor(c), resolveCssColor('var(--paper)'))(t);
	const darken = (c: string, t: number) => interpolateRgb(resolveCssColor(c), '#000000')(t);
	/** a lot inside a call bubble is a lighter tint of the bubble's own hue */
	const fill = (n: Placed) =>
		mode === 'pack' && inGroup.has(n.ref) ? lighten(markHue(n), 0.42) : markHue(n);
	/** the call's name on its rim: dark ink on a light hue, light on a dark
	 *  one — the same contrast rule the reference packed-circle maps use */
	const arcInk = (p?: string | null) => {
		const h = hue(p);
		return ink(h) === 'var(--ink)' ? darken(h, 0.55) : lighten(h, 0.74);
	};
	const ink = (c: string) => (cssLuminance(c) > 150 / 255 ? 'var(--ink)' : 'var(--paper)');
	const dim = (n: Placed) =>
		!hover ? 1 : hover.call ? (n.call === hover.call ? 1 : 0.25) : n.ref === hover.ref ? 1 : 0.25;
	const tiePath = (pts: { x: number; y: number }[]) =>
		pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
	const markOf = $derived(new Map(sc.marks.map((n) => [n.ref, n])));
</script>

<figure class="net">
	<ul class="key">
		{#if lens === 'type'}
			{#each cats as c (c)}
				<li><i style:background={catHue(c)}></i>{catLabels[c] ?? c}</li>
			{/each}
		{:else}
			{#each kinds as p (p)}
				<li><i style:background={hue(p)} class:ringed={p === 'study'}></i>{DK_LABELS[p]}</li>
			{/each}
		{/if}
		<li class="sep"><i class="season"></i>fire season, 1 May – 31 October</li>
		<li><i class="tie"></i>joined: lots of the same call</li>
		<!-- the two readings a beeswarm needs, in the key where reading lives
		     (copy pass 2026-08-23) -->
		<li class="note">circle area = stated value · vertical position = packing only</li>
		{#if hasUdc}
			<li><i class="udcnode"></i>call known by date only (HRADF) — no ΚΗΜΔΗΣ record</li>
		{/if}
	</ul>


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
			<path
				d={tiePath(t.pts)}
				class="tie"
				class:udc={t.call.startsWith('date:')}
				class:lit={hover?.call === t.call}
			/>
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
				
				class:ringed={lens === 'scope' && n.phase === 'study'}
				class:udcnode={n.udc}
				class:dark={n.udc && ink(fill(n)) === 'var(--paper)'}/>
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
		stroke: var(--ink);
		stroke-width: 1.4;
		stroke-dasharray: none;
	}
	.group {
		transition: all 0.55s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.spoke {
		stroke: color-mix(in srgb, var(--ink) 33.5%, var(--paper));
		stroke-width: 1;
	}
	:global(circle.ringed),
	i.ringed {
		stroke: color-mix(in srgb, var(--ink) 80.8%, var(--paper));
		stroke-width: 1;
		border: 1px solid color-mix(in srgb, var(--ink) 80.8%, var(--paper));
	}
	path.tie.udc {
		stroke: color-mix(in srgb, var(--ink) 65.9%, var(--paper));
		stroke-dasharray: 3 3;
	}
	/* the date-only (HRADF) marker sits on the DOTS since the touching
	   same-day runs cover the join line (user, 2026-08-22): a dashed ring */
	:global(circle.udcnode) {
		stroke: color-mix(in srgb, var(--ink) 65.9%, var(--paper));
		stroke-width: 1.3;
		stroke-dasharray: 2.6 2;
	}
	/* the dash flips light on a dark fill, or it disappears */
	:global(circle.udcnode.dark) {
		stroke: color-mix(in srgb, var(--ink) 17.4%, var(--paper));
	}
	.key li i.udcnode {
		width: 11px;
		height: 11px;
		border: 1.5px dashed color-mix(in srgb, var(--ink) 65.9%, var(--paper));
		border-radius: 50%;
		background: none;
	}
	.tie {
		/* a call whose lots were signed weeks apart draws a long line; kept
		   faint so the same-day verticals — the finding — carry the ink */
		fill: none;
		stroke: color-mix(in srgb, var(--ink) 23.9%, var(--paper));
		stroke-width: 1;
	}
	.tie.lit {
		stroke: var(--ink);
		stroke-width: 1.4;
	}
	.bridge {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 4 3;
	}
	.rule {
		stroke: var(--line);
		stroke-width: 1;
	}
	rect.season {
		/* the page's ONE fire-season colour: the red's light shade */
		fill: var(--c-fire-season);
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
	/* the MAP legend's dress (AntineroMap .mapkey), so the page's keys
	   read as one family (user, 2026-08-22) */
	.key {
		list-style: none;
		margin: 0 0 var(--sp-2);
		box-sizing: border-box;
		padding: var(--sp-2) var(--sp-3);
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		align-content: center;
		gap: 4px var(--sp-6, 1.5rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.key li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.key li i {
		width: 12px;
		height: 12px;
		border-radius: 3px;
		flex: none;
	}
	/* the two JOIN swatches are line samples, not boxes — a 12px square
	   with a coloured top border was unreadable (user, 2026-08-22) */
	.key li i.tie {
		width: 20px;
		height: 0;
		border-top: 2px solid color-mix(in srgb, var(--ink) 23.9%, var(--paper));
		border-radius: 0;
		background: none;
	}
	.key li.note {
		color: var(--ink-faint);
	}
	.key li i.season {
		/* the stripe's own colour */
		background: var(--c-fire-season);
		width: 16px;
		height: 10px;
		border-radius: 0;
	}
	.card {
		position: absolute;
		left: 0;
		bottom: 0;
		background: var(--ink);
		color: var(--paper);
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
