<script lang="ts">
	/**
	 * The story's left column — the author's two artboards (2026-09-01).
	 *
	 * COLLAPSED: the three lanes converge on one dotted line with the years
	 * beside it. SPREAD: they separate — global/EU, Greece, fires — the years
	 * move to the far left and the events' text appears. The VERTICAL scale is
	 * identical in both, so the whole transition is horizontal: lane x, the
	 * years' x, and the opacity of what only the spread state shows.
	 *
	 * Everything is authored 1:1 in the ARTBOARD's coordinates inside one
	 * `transform: scale(k)` wrapper — SVG geometry and HTML type then scale
	 * together and cannot drift apart. Marks are SVG (geometry); every glyph is
	 * HTML (event descriptions are multi-line prose, which SVG cannot wrap).
	 *
	 * Phase 1 draws the STRUCTURE only: lanes, the year scale, the legend. The
	 * events arrive once the author has ruled on the movement.
	 */
	import {
		AXIS_TOP,
		COLLAPSED_X,
		LANE_X,
		axisHeight,
		yearStops,
		type Lane
	} from '$lib/transforms/storyTimeline';

	interface Props {
		/** true once the reader's text has reached the first dated event */
		expanded?: boolean;
		/** the year the reader is in, printed large — null while collapsed */
		activeYear?: number | null;
	}
	let { expanded = false, activeYear = null }: Props = $props();

	const stops = yearStops();
	const H = axisHeight(stops);
	const W = 520; // the artboard's left column, 60 → 580

	/**
	 * The lanes, in the artboard's own colours (the palette is settled
	 * separately). `legX` is where the lane's legend label starts when the
	 * timeline is spread — the artboard's own positions, not a constant offset:
	 * the long «global events» label sits LEFT of its rule because that rule is
	 * near the column's edge.
	 */
	const LANES: {
		key: Lane;
		x: number;
		legX: number;
		legW: number;
		color: string;
		label: string;
	}[] = [
		{
			key: 'world',
			x: LANE_X.world,
			legX: 107,
			legW: 120,
			color: '#606060',
			label: 'global events & EU legislation changes'
		},
		{
			key: 'greece',
			x: LANE_X.greece,
			legX: 235,
			legW: 140,
			color: '#000000',
			label: 'events & legislation changes in Greece'
		},
		{ key: 'fire', x: LANE_X.fire, legX: 383, legW: 130, color: '#a6312d', label: 'fires in Greece' }
	];
	/** where the three labels stack while the lanes are converged */
	const LEG_COLLAPSED_X = 193;

	/** the box we are given, and the one scale that fits the artboard into it */
	let box = $state<HTMLElement | null>(null);
	let w = $state(0);
	let h = $state(0);
	const K_FLOOR = 0.62; // below this the 11 px descriptions stop being readable
	const k = $derived(Math.max(K_FLOOR, Math.min(w / W || 1, h / H || 1, 1)));
</script>

<div class="tl" bind:this={box} bind:clientWidth={w} bind:clientHeight={h}>
	<div class="scale" class:expanded style:--k={k} style:--w={`${W}px`} style:--h={`${H}px`}>
		<!-- the legend: what each lane is. Stacked by the collapsed line, and
		     carried out over its own lane when they spread. -->
		<ul class="legend">
			{#each LANES as l, i (l.key)}
				<li
					class="leg"
					style:color={l.color}
					style:--lx={`${l.legX}px`}
					style:--lw={`${l.legW}px`}
					style:--cx={`${LEG_COLLAPSED_X}px`}
					style:--ly={`${AXIS_TOP - 62 + i * 13}px`}
				>
					{l.label}
				</li>
			{/each}
		</ul>

		<!-- the years: beside the collapsed line, far left when spread -->
		<div class="years">
			{#each stops as s (s.year)}
				{#if s.labelled}
					<span class="yr" class:on={s.year === activeYear} style:top={`${s.y}px`}>{s.year}</span>
				{/if}
			{/each}
		</div>

		<!-- the rules themselves: one dotted line while collapsed, three solid
		     ones when spread, exactly as the two artboards draw them -->
		<svg class="marks" viewBox="0 0 {W} {H}" width={W} height={H} aria-hidden="true">
			{#each LANES as l (l.key)}
				<g class="lane" style:--dx={`${COLLAPSED_X - l.x}px`}>
					<line
						x1={l.x}
						x2={l.x}
						y1={AXIS_TOP - 34}
						y2={H - 12}
						stroke={l.color}
						stroke-width="2"
						stroke-dasharray={expanded ? 'none' : '1 2'}
					/>
				</g>
			{/each}
		</svg>
	</div>
</div>

<style>
	.tl {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}
	/* one transform for the whole artboard — geometry and type scale together */
	.scale {
		position: absolute;
		inset: 0;
		width: var(--w);
		height: var(--h);
		transform: scale(var(--k));
		transform-origin: 0 0;
	}
	.marks {
		position: absolute;
		inset: 0;
		overflow: visible;
	}

	/* COLLAPSE → SPREAD is horizontal only. A <line>'s x1/x2 are attributes and
	   cannot be transitioned; the wrapping <g>'s transform is what moves, and it
	   carries the dots and capsules with it once they exist. */
	.lane {
		transform: translateX(var(--dx));
		transition: transform 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.expanded .lane {
		transform: translateX(0);
	}

	.years {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		transform: translateX(226px); /* beside the collapsed line */
		transition: transform 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.expanded .years {
		transform: translateX(0);
	}
	.yr {
		position: absolute;
		left: 0;
		width: 56px;
		margin-top: -0.62em;
		text-align: right;
		font-family: var(--font-display-narrow);
		font-weight: 700;
		font-size: 21px;
		line-height: 1;
		color: var(--ink);
		transition:
			font-size 0.35s ease,
			color 0.35s ease;
	}
	.expanded .yr {
		text-align: left;
	}
	.yr.on {
		font-size: 36px;
		color: #a6312d;
	}

	.legend {
		position: absolute;
		inset: 0;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	/* stacked beside the collapsed line, then each label rides out over its own
	   lane — the same horizontal move the lanes make */
	.leg {
		position: absolute;
		top: var(--ly);
		left: var(--cx);
		width: 220px;
		/* the card pages' graph titles: the display face, bold, in caps —
		   `ui/Tile.svelte` .tt. A display face set in capitals reads far
		   stronger at this size than the body face did in sentence case. */
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 12px;
		line-height: 1.15;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		transition:
			left 0.55s cubic-bezier(0.2, 0.7, 0.2, 1),
			top 0.55s cubic-bezier(0.2, 0.7, 0.2, 1),
			width 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	/* spread: the three labels share one baseline above their own rules, each
	   held to the room before the next one starts so they cannot collide */
	.expanded .leg {
		top: 34px;
		left: var(--lx);
		width: var(--lw);
	}

	@media (prefers-reduced-motion: reduce) {
		.lane,
		.years,
		.yr,
		.leg {
			transition: none;
		}
	}
</style>
