<script lang="ts">
	/**
	 * The story's left column — the author's two artboards (2026-09-01), now
	 * carrying the 31 events of their own `Timeline.xlsx`.
	 *
	 * COLLAPSED: the three lanes converge on one dotted line with the years
	 * beside it, and the whole 2007→2026 span is in view at once. SPREAD: they
	 * separate — global/EU, Greece, fires — the years move to the far left, the
	 * events appear, and the column becomes a VIEWPORT that pans: 31 blocks of
	 * text cannot be read at once in a column one screen tall, so the rail
	 * follows the reader down the axis.
	 *
	 * Everything is authored 1:1 in the ARTBOARD's coordinates inside one
	 * `transform` — SVG geometry and HTML type then scale together and cannot
	 * drift apart. Marks are SVG (geometry); every glyph is HTML (the event
	 * descriptions are wrapped prose, which SVG cannot set).
	 *
	 * The DOT is always on the event's true date. Where events crowd — eight of
	 * them inside one fortnight of August 2021 — the BLOCK moves down and a
	 * leader line joins it back to its dot. That layout is pure and tested in
	 * `transforms/storyTimeline.ts`; nothing here decides position.
	 */
	import {
		AXIS_TOP,
		BODY_CLAMP,
		COLLAPSED_X,
		LANES,
		LANE_TEXT,
		LANE_X,
		TITLE_CLAMP,
		axisHeight,
		contentHeight,
		layoutLane,
		storyDate,
		storyRange,
		yOfDate,
		yearStops,
		YEAR_W,
		type Lane
	} from '$lib/transforms/storyTimeline';
	import { laneEvents, type StoryEvent } from '$lib/story/events';

	interface Props {
		/** true once the reader's text has reached the first dated event */
		expanded?: boolean;
		/** the year the reader is in, printed large — null while collapsed */
		activeYear?: number | null;
		/** the events the passage on screen mentions; the rest stay grey */
		activeIds?: string[];
		/** the dates of the ACTIVE paragraph's events — the rail frames the
		 *  whole range (a paragraph may bind events years apart: the AntiNero
		 *  one spans the Green Deal 2019 to the launch 2022). Empty = the rail
		 *  pans by `progress` instead. */
		focusDates?: string[];
		/** 0→1 through the narrative — the fallback between bound passages */
		progress?: number;
		/** a bullet was clicked — the page scrolls to the passage that says it */
		onSelect?: (e: StoryEvent) => void;
		/** the author's timeline disclaimer — printed under the axis, LEFT of
		 *  the collapsed line, before it splits into the three lanes */
		note?: string;
	}
	let {
		expanded = false,
		activeYear = null,
		activeIds = [],
		focusDates = [],
		progress = 0,
		onSelect,
		note = ''
	}: Props = $props();

	const stops = yearStops();
	const W = 520; // the artboard's left column, 60 → 580

	/**
	 * The lanes, in the artboard's own colours (the palette is settled
	 * separately). `legX` is where the lane's legend label starts when the
	 * timeline is spread — the artboard's own positions, not a constant offset:
	 * the long «global events» label sits LEFT of its rule because that rule is
	 * near the column's edge, and so does that lane's event text.
	 */
	const LANE_META: Record<Lane, { legX: number; legW: number; color: string; label: string }> = {
		world: {
			legX: 66,
			legW: 106,
			color: '#606060',
			label: 'global events & EU legislative changes'
		},
		greece: {
			legX: 235,
			legW: 140,
			color: '#000000',
			label: 'events & legislative changes in Greece'
		},
		fire: { legX: 383, legW: 130, color: '#a6312d', label: 'fires in Greece' }
	};
	/**
	 * The collapsed chrome (disclaimer left of the line · lane titles right of
	 * it) renders at NATIVE size outside the scaled drawing — at the collapsed
	 * scale anything inside it is illegible (the author, 2026-09-02). It sits
	 * in the UPPER part of the timeline, where the early years are sparse, so
	 * the axis takes the whole rail and nothing is reserved below.
	 * The collapsed state prints NO category titles since 2026-09-03 (the
	 * author) — the lanes name themselves only when they spread. Since the
	 * author's own SVG edit, the collapsed drawing shifts RIGHT (`cx`) so
	 * the disclaimer gets a real measure — the rail's left half,
	 * right-aligned toward the years.
	 */

	const lit = $derived(new Set(activeIds));

	/**
	 * The placed events. The layout REFLOWS with the reading position: an
	 * event carries its explanatory text only while the main text is at its
	 * period (the lit events), so everything else stands as date + title and
	 * the lanes stay tidy. Blocks animate to their new tops in CSS.
	 */
	const placed = $derived.by(() =>
		LANES.map((lane) => ({
			lane,
			x: LANE_X[lane],
			text: LANE_TEXT[lane],
			...LANE_META[lane],
			items: layoutLane(laneEvents(lane), stops, LANE_TEXT[lane].w, (e) => lit.has(e.id))
		}))
	);
	const H = $derived(
		contentHeight(
			placed.map((l) => l.items),
			stops
		)
	);
	/** the collapsed artboard shows the year scale alone, so it needs less */
	const H_COLLAPSED = axisHeight(stops);

	/** the box we are given, and the scale that fits the artboard into it */
	let w = $state(0);
	let h = $state(0);
	/** collapsed the whole span is in view; spread we fit the WIDTH and pan */
	const k = $derived(
		expanded ? Math.min(w / W || 1, 1) : Math.min(w / W || 1, (h || 1) / H_COLLAPSED, 1)
	);
	/** the collapsed drawing's rightward shift — the author's SVG geometry:
	 *  21.4% of the rail at the design width, never past the rail's edge */
	const cx = $derived(
		expanded ? 0 : Math.max(0, Math.min(0.214 * (w || 0), (w || 0) - k * W - 8))
	);

	/**
	 * The pan. The rail frames the WHOLE range of the active paragraph's
	 * events (the author, 2026-09-02: reading about the 2022 launch must not
	 * pan to the 2019 Green Deal because it fired first): the window centres
	 * on the range's midpoint, and a range taller than the view anchors just
	 * above its earliest event. Between bound passages it falls back to the
	 * reader's progress — clamped, so it never scrolls past either end.
	 */
	const viewH = $derived((h || 1) / k);
	const panY = $derived.by(() => {
		if (!expanded) return 0;
		let target = progress * H;
		if (focusDates.length) {
			const ys = focusDates.map((d) => yOfDate(d, stops));
			const lo = Math.min(...ys);
			const hi = Math.max(...ys);
			target = hi - lo > viewH * 0.8 ? lo + viewH * 0.42 : (lo + hi) / 2;
		}
		return Math.max(0, Math.min(H - viewH, target - viewH * 0.42));
	});

	/**
	 * The year printed large. The author's artboard puts one year in the reader's
	 * size, and until each event is bound to its passage the honest answer is the
	 * year the rail is actually showing: the stop nearest the middle of the view.
	 */
	const centreYear = $derived.by(() => {
		if (!expanded) return null;
		const mid = panY + viewH / 2;
		let best = stops[0];
		for (const s of stops) if (Math.abs(s.y - mid) < Math.abs(best.y - mid)) best = s;
		return best.labelled ? best.year : null;
	});
	const bigYear = $derived(activeYear ?? centreYear);
</script>

<div class="tl" bind:clientWidth={w} bind:clientHeight={h}>
	<div
		class="scale"
		class:expanded
		style:--k={k}
		style:--cx={`${cx}px`}
		style:--pan={`${-panY}px`}
		style:--w={`${W}px`}
		style:--h={`${H}px`}
		style:--tc={TITLE_CLAMP}
		style:--bc={BODY_CLAMP}
		style:--yw={`${YEAR_W}px`}
	>
		<!-- the legend: what each lane is. Stacked by the collapsed line, and
		     carried out over its own lane when they spread. -->
		<ul class="legend">
			{#each placed as l (l.lane)}
				<li class="leg" style:color={l.color} style:--lx={`${l.legX}px`} style:--lw={`${l.legW}px`}>
					{l.label}
				</li>
			{/each}
		</ul>

		<!-- the years: beside the collapsed line, far left when spread -->
		<div class="years">
			{#each stops as s (s.year)}
				{#if s.labelled}
					<span class="yr" class:on={s.year === bigYear} style:top={`${s.midY}px`}>{s.year}</span>
				{/if}
			{/each}
		</div>

		<svg class="marks" viewBox="0 0 {W} {H}" width={W} height={H} aria-hidden="true">
			{#each placed as l (l.lane)}
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

					<!-- where the axis compresses nine years into two steps, it says so:
					     the classic break, so the gap is never read as duration -->
					{#each stops.filter((s) => s.gap > 1) as s (s.year)}
						<g class="brk" stroke={l.color} stroke-width="1.5">
							<line x1={l.x - 5} x2={l.x + 5} y1={s.y + 22} y2={s.y + 17} />
							<line x1={l.x - 5} x2={l.x + 5} y1={s.y + 27} y2={s.y + 22} />
						</g>
					{/each}

					<g class="events">
						{#each l.items as p (p.e.id)}
							{@const on = lit.has(p.e.id)}
							<!-- a period is a capsule from its start to its end -->
							{#if p.endY !== undefined}
								<line
									class="cap"
									class:on
									x1={l.x}
									x2={l.x}
									y1={p.dotY}
									y2={Math.max(p.endY, p.dotY + 4)}
									stroke={l.color}
									stroke-width="7"
									stroke-linecap="round"
								/>
							{/if}
							<!-- the leader line, only where the block had to leave its dot -->
							{#if p.pushed}
								<path
									class="lead"
									d={l.text.align === 'right'
										? `M${l.x - 6} ${p.dotY} H${l.text.x + l.text.w + 4} V${p.blockY + 6}`
										: `M${l.x + 6} ${p.dotY} H${l.text.x - 4} V${p.blockY + 6}`}
									fill="none"
									stroke={l.color}
								/>
							{/if}
							<circle class="dot" class:on cx={l.x} cy={p.dotY} r={on ? 5 : 3.5} fill={l.color} />
						{/each}
					</g>
				</g>
			{/each}
		</svg>

		<!-- the event text: HTML, because these are wrapped paragraphs -->
		<div class="blocks">
			{#each placed as l (l.lane)}
				<div class="lanetext" style:--dx={`${COLLAPSED_X - l.x}px`} style:color={l.color}>
					{#each l.items as p (p.e.id)}
						<button
							type="button"
							class="ev"
							class:on={lit.has(p.e.id)}
							class:right={l.text.align === 'right'}
							style:top={`${p.blockY}px`}
							style:left={`${l.text.x}px`}
							style:width={`${l.text.w}px`}
							onclick={() => onSelect?.(p.e)}
						>
							<span class="d"
								>{p.e.end && p.e.end !== p.e.date
									? storyRange(p.e.date, p.e.end)
									: storyDate(p.e.date)}</span
							>
							<span class="t">{p.e.title}</span>
							{#if p.e.body && lit.has(p.e.id)}<span class="b">{p.e.body}</span>{/if}
						</button>
					{/each}
				</div>
			{/each}
		</div>
	</div>

	<!-- NATIVE-size chrome of the collapsed state (the author, 2026-09-02: at
	     the collapsed scale these were illegible inside the drawing): in the
	     UPPER part of the timeline, where the early years are sparse — the
	     disclaimer left of the years column, the lane titles (two lines each)
	     right of the converged line, the scaled dotted line the divider. -->
	<div
		class="below"
		class:hidden={expanded}
		style:--split={`${cx + k * COLLAPSED_X}px`}
		style:--dw={`${Math.max(140, cx + k * (COLLAPSED_X - YEAR_W - 8) - 14)}px`}
	>
		{#if note}
			<p class="ndisc">{note}</p>
		{/if}
	</div>
</div>

<style>
	.tl {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}
	/* one transform for the whole artboard — geometry and type scale together.
	   The scale comes FIRST, so the pan is expressed in artboard units. */
	.scale {
		position: absolute;
		inset: 0;
		width: var(--w);
		height: var(--h);
		transform: translateX(var(--cx, 0px)) scale(var(--k)) translateY(var(--pan));
		transform-origin: 0 0;
		transition: transform 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.marks {
		position: absolute;
		inset: 0;
		overflow: visible;
	}

	/* COLLAPSE → SPREAD is horizontal only. A <line>'s x1/x2 are attributes and
	   cannot be transitioned; the wrapping <g>'s transform is what moves, and it
	   carries that lane's dots, capsules and leader lines with it. */
	.lane,
	.lanetext {
		transform: translateX(var(--dx));
		transition: transform 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.expanded .lane,
	.expanded .lanetext {
		transform: translateX(0);
	}

	/* the text blocks appear only when the timeline spreads; the DOTS and
	   capsules ride the converged line even collapsed — the author's Page01
	   draws them there */
	.brk,
	.blocks {
		opacity: 0;
		transition: opacity 0.3s ease;
		pointer-events: none;
	}
	.expanded .brk,
	.expanded .blocks {
		opacity: 1;
		pointer-events: auto;
	}
	.events {
		pointer-events: none;
	}
	.expanded .events {
		pointer-events: auto;
	}

	.dot,
	.cap {
		opacity: 0.5;
		transition:
			opacity 0.25s ease,
			r 0.25s ease;
	}
	.dot.on,
	.cap.on {
		opacity: 1;
	}
	/* collapsed, the leader lines make no sense — there is no text yet */
	.lead {
		stroke-width: 1;
		opacity: 0;
		transition: opacity 0.3s ease;
	}
	.expanded .lead {
		opacity: 0.35;
	}

	.years {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		transform: translateX(281px); /* beside the collapsed line (345 - 64) */
		transition: transform 0.55s cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	.expanded .years {
		transform: translateX(0);
	}
	.yr {
		position: absolute;
		left: 0;
		width: var(--yw);
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
		/* held to the YEAR_W gutter: any larger and it prints over the world
		   lane's text, which starts where that gutter ends */
		font-size: 28px;
		color: #a6312d;
	}

	.legend {
		position: absolute;
		inset: 0;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	/* the in-scale legend exists only SPREAD, above each lane's own rule; the
	   collapsed state names the lanes in the native block below the axis */
	.leg {
		position: absolute;
		top: 34px;
		left: var(--lx);
		width: var(--lw);
		/* the card pages' graph titles: the display face, bold, in caps —
		   `ui/Tile.svelte` .tt */
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 12px;
		line-height: 1.15;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		opacity: 0;
		transition: opacity 0.3s ease;
	}
	.expanded .leg {
		opacity: 1;
	}

	/* ── the native collapsed chrome ── */
	.below {
		position: absolute;
		inset: 0;
		pointer-events: none;
		transition: opacity 0.3s ease;
	}
	.below.hidden {
		opacity: 0;
	}
	.ndisc {
		position: absolute;
		left: 0;
		top: 36px;
		/* up to the years' left edge — computed in the markup */
		width: var(--dw);
		margin: 0;
		font-family: var(--font-ui);
		/* the footnotes' own setting (the author's ruling) */
		font-size: var(--fs-12);
		font-weight: 300;
		line-height: 1.3;
		text-align: right;
		color: var(--ink-soft);
	}

	.blocks {
		position: absolute;
		inset: 0;
	}
	.lanetext {
		position: absolute;
		inset: 0;
	}
	/* an event's block: a button, because clicking it takes the reader to the
	   passage that tells it. Grey at rest, its lane's colour when the passage on
	   screen names it. */
	.ev {
		position: absolute;
		display: block;
		margin: 0;
		padding: 0;
		border: 0;
		background: none;
		text-align: left;
		font: inherit;
		color: var(--ink-faint);
		cursor: pointer;
		transition:
			color 0.25s ease,
			top 0.3s ease;
	}
	.ev.right {
		text-align: right;
	}
	.ev.on {
		color: inherit; /* the lane's own colour, set on .lanetext */
	}
	.ev:focus-visible {
		outline: 1px solid currentColor;
		outline-offset: 2px;
	}
	.d,
	.t,
	.b {
		display: block;
		overflow: hidden;
	}
	.d {
		font-family: var(--font-display-narrow);
		font-weight: 700;
		font-size: 9.5px;
		line-height: 13px;
		letter-spacing: 0.04em;
	}
	.t {
		font-family: var(--font-ui);
		font-size: 11px;
		line-height: 1.2;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		/* the SAME clamp the block-height estimate assumes, passed in from the
		   layout module so the drawing and the maths cannot drift apart */
		-webkit-line-clamp: var(--tc);
		line-clamp: var(--tc);
	}
	/* an OPEN event stretches: full title, full body, no clamps — the layout
	   has already made the room (the author, 2026-09-02) */
	.ev.on .t {
		font-weight: 700;
		display: block;
		-webkit-line-clamp: unset;
		line-clamp: unset;
	}
	.b {
		margin-top: 3px;
		font-family: var(--font-ui);
		font-size: 11px;
		line-height: 1.2;
		opacity: 0.75;
		display: block;
	}

	@media (prefers-reduced-motion: reduce) {
		.scale,
		.lane,
		.lanetext,
		.years,
		.yr,
		.leg,
		.dot,
		.cap,
		.ev,
		.events,
		.brk,
		.blocks {
			transition: none;
		}
	}
</style>
