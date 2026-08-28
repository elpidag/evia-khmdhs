<script lang="ts">
	/**
	 * A dataset's CARD (Artboard 4, user 2026-08-27) — exactly one viewport, no
	 * scrolling: the symbol, the stream's name, the narrative and «explore
	 * more» in a column on the left running the full height; the three KPI
	 * cards across the top of the right; under them the dataset's key
	 * charts as TILES in a grid (first tile top-left, second the tall one
	 * on the right, third under the first). «Explore more» REPLACES the
	 * card with the dataset's frames — the analysis page as it was — on the
	 * same URL (`#more`); «back to the card» returns. A link into a frame
	 * or a chart lens opens on the frames.
	 */
	import { tick } from 'svelte';
	import { page } from '$app/state';
	import { symbolFor, type DatasetKey } from '$lib/datasets';
	import DatasetSymbol from './DatasetSymbol.svelte';
	import KpiCards, { type KpiCard } from './KpiCards.svelte';
	import KpiRich, { type RichKpi } from './KpiRich.svelte';
	import Prose from './Prose.svelte';
	import { MORE_HASH, isExpanded, lessHref, moreHref } from './expanded';
	import type { Snippet } from 'svelte';

	let {
		ds,
		params,
		kpis = [],
		richKpis = [],
		kpiBlock,
		layout = 'default',
		cols = [549, 711, 516],
		midRows = [1],
		rightRows = [3745, 5631],
		midGap = 17,
		rightGap = 15.4,
		kpiSpan = false,
		kpiRows = 1,
		kpiCols = 0,
		hint = '',
		text,
		tiles,
		tileMain,
		tileMain2,
		tileA,
		tileB,
		tileC,
		more
	}: {
		ds: DatasetKey;
		/** the page's own URL parameters — any of them opens the frames */
		params: readonly string[];
		kpis?: KpiCard[];
		/** the sponsored card's richer cards (Artboard 4, user 2026-08-27) */
		richKpis?: RichKpi[];
		/** «triple» is the three-column card: the text, then the KPI row over
		 *  one or two tiles, then two or three tiles stacked (the sponsored
		 *  card's Artboard 4, the Anti-nero card's Artboard 6) */
		layout?: 'default' | 'triple';
		/** a page's own KPI block in the 137 px row, instead of KpiRich */
		kpiBlock?: Snippet;
		/** the three columns' widths in the artboard's px (the gaps are
		 *  25 and 17 between them, all as fractions of the card's width) */
		cols?: [number, number, number];
		/** the middle column's tile heights under the KPI row, and the right
		 *  column's, as proportions */
		midRows?: number[];
		rightRows?: number[];
		/** the row gaps in px */
		midGap?: number;
		rightGap?: number;
		/** the KPI row across BOTH chart columns (the Anti-nero card, user
		 *  2026-08-27) instead of over the middle one */
		kpiSpan?: boolean;
		/** the KPI block as TWO rows of full-height cards (2028-08-28), and
		 *  how many cards per row */
		kpiRows?: 1 | 2;
		kpiCols?: number;
		/** the content file behind the narrative, shown while it is empty */
		hint?: string;
		text: Snippet;
		/** three Tile components, in reading order (default layout) */
		tiles?: Snippet;
		/** the triple layout's tiles: the middle column's one or two under
		 *  the KPI row, then the right column's two or three */
		tileMain?: Snippet;
		tileMain2?: Snippet;
		tileA?: Snippet;
		tileB?: Snippet;
		tileC?: Snippet;
		more: Snippet;
	} = $props();

	const sym = $derived(symbolFor(ds));
	const expanded = $derived(isExpanded(page.url, params));
	/** the triple grid's columns: the artboard's widths and the 25 / 17 px
	 *  gaps, all as fractions of the card, so the card scales as one */
	const colStyle = $derived.by(() => {
		const total = cols[0] + 25 + cols[1] + 17 + cols[2];
		const pc = (v: number) => `${((100 * v) / total).toFixed(3)}%`;
		return [pc(cols[0]), pc(25), pc(cols[1]), pc(17), pc(cols[2])].join(' ');
	});
	const rowsOf = (rs: number[]) => rs.map((r) => `minmax(0, ${r}fr)`).join(' ');

	// a tile's title links to its frame: the frames mount with the switch,
	// so the scroll waits for them; the way back lands on the card's top
	$effect(() => {
		if (!expanded) {
			window.scrollTo(0, 0);
			return;
		}
		const id = page.url.hash.replace(/^#/, '');
		if (!id || id === MORE_HASH) return;
		tick().then(() => document.getElementById(id)?.scrollIntoView({ block: 'start' }));
	});
</script>

{#if expanded}
	<div class="rest" id={MORE_HASH} style:--card-accent={sym.color}>
		<div class="resthead">
			<DatasetSymbol key={ds} size={34} />
			<span class="label">{sym.label}</span>
			<a class="back" href={lessHref(page.url)}>← back to the card</a>
		</div>
		{@render more()}
	</div>
{:else if layout === 'triple'}
	<div
		class="dcard triple"
		class:span={kpiSpan}
		style:--card-accent={sym.color}
		style:--cols={colStyle}
		style:--mid-rows={rowsOf(midRows)}
		style:--right-rows={rowsOf(rightRows)}
		style:--mid-gap="{midGap}px"
		style:--right-gap="{rightGap}px"
		style:--mid-gap-n={midGap}
		style:--right-gap-n={rightGap}
		style:--kpi-h={kpiRows === 2
			? `calc(2 * clamp(104px, 12.7vh, 137px) + ${midGap}px)`
			: 'clamp(104px, 12.7vh, 137px)'}
		style:--kpi-row-gap="{midGap}px"
	>
		<div class="side">
			<div class="who big">
				<DatasetSymbol key={ds} size="clamp(96px, 8.47vw, 162.6px)" active />
				<span class="bigname">
					{#if sym.titleLines}
						{#each sym.titleLines as ln, i (i)}<span class="ln">{ln}</span>{/each}
					{:else}
						{sym.label}
					{/if}
				</span>
			</div>
			<div class="narrative">
				<Prose {hint}>{@render text()}</Prose>
			</div>
			<a class="more" href={moreHref(page.url)}>explore more</a>
		</div>
		{#if kpiSpan}
			<div class="kpis wide">
				{#if kpiBlock}{@render kpiBlock()}{:else}<KpiRich cards={richKpis} color={sym.color} columns={kpiCols} />{/if}
			</div>
		{/if}
		<div class="mid">
			{#if !kpiSpan}
				<div class="kpis">
					{#if kpiBlock}{@render kpiBlock()}{:else}<KpiRich cards={richKpis} color={sym.color} columns={kpiCols} />{/if}
				</div>
			{/if}
			{@render tileMain?.()}
			{@render tileMain2?.()}
		</div>
		<div class="rightcol">
			{@render tileA?.()}
			{@render tileB?.()}
			{@render tileC?.()}
		</div>
	</div>
{:else}
	<div class="dcard" style:--card-accent={sym.color}>
		<div class="side">
			<div class="who">
				<DatasetSymbol key={ds} size="clamp(96px, 7.93vw, 152px)" active />
				<span class="label">{sym.label}</span>
			</div>
			<div class="narrative">
				<Prose {hint}>{@render text()}</Prose>
			</div>
			<a class="more" href={moreHref(page.url)}>explore more</a>
		</div>
		<div class="kpis"><KpiCards cards={kpis} color={sym.color} /></div>
		<div class="tiles">{@render tiles?.()}</div>
	</div>
{/if}

<style>
	/* the card is the viewport under the header, to the pixel: the layout
	   widens `main`, sets --header-h and the artboard's four paddings.
	   Artboard 4 (1920×1080): a 540 px left column, the KPI row 177 px
	   tall starting 35 px to its right, 15 px above the tiles; the tiles in
	   two columns 18 px apart, the rows 491 : 249 */
	.dcard {
		display: grid;
		grid-template-columns: minmax(16rem, 29.7%) minmax(0, 1fr);
		grid-template-rows: clamp(110px, 16.4vh, 177px) minmax(0, 1fr);
		grid-template-areas:
			'side kpis'
			'side tiles';
		gap: 1.4vh 1.9%;
		height: calc(
			100dvh - var(--header-h, 85px) - var(--card-pad-t, 25px) - var(--card-pad-b, 17px)
		);
		box-sizing: border-box;
		align-items: stretch;
	}
	.side {
		grid-area: side;
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	/* the symbol 27 px under the card's top, filled in the stream's hue,
	   the name to its right on its baseline */
	.who {
		display: flex;
		align-items: flex-end;
		gap: clamp(12px, 1.5vw, 29px);
		margin-top: 2.5vh;
	}
	.label {
		font-family: var(--font-display-cond);
		font-weight: 700;
		font-size: clamp(14px, 1.25vw, 24px);
		color: var(--card-accent);
		line-height: 1;
	}
	/* the narrative: the space for the user's own text, set in Futura
	   100 GR 18 px on 21,6 px lines (Artboard 4, user 2026-08-27); a long
	   one scrolls inside its column */
	.narrative {
		flex: 1;
		min-height: 0;
		overflow: auto;
		margin-top: 3.9vh;
	}
	.side .narrative :global(.prose),
	.side .narrative :global(.prose p) {
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: clamp(13px, 0.94vw, 18px);
		line-height: 1.2;
		color: var(--ink);
		max-width: none;
	}
	.side .narrative :global(.prose p) {
		margin: 0 0 1.2em;
	}
	.side .narrative :global(.prose strong) {
		font-weight: 700;
	}
	.kpis {
		grid-area: kpis;
		min-height: 0;
	}
	/* the KPI cards in the artboard's dress — 14.5 px apart, 12 px corners,
	   23 px padding — with the NUMBER leading (56 px) and the caption in
	   Condensed Regular under it, the way the dashboard we measured does */
	.dcard:not(.triple) .kpis :global(.cards) {
		height: 100%;
		gap: clamp(8px, 0.75vw, 14.5px);
	}
	.dcard:not(.triple) .kpis :global(.card) {
		flex-direction: column;
		height: 100%;
		box-sizing: border-box;
		padding: clamp(14px, 3.15vh, 34px) clamp(10px, 1.2vw, 23px) clamp(10px, 1.2vw, 23px);
		border-radius: 12px;
		gap: 0;
		min-height: 0;
		overflow: hidden;
	}
	.dcard:not(.triple) .kpis :global(.lbl) {
		margin-top: 8px;
		font-family: var(--font-display-cond);
		font-weight: 400;
		font-size: clamp(13px, 0.94vw, 18px);
		line-height: 1.25;
	}
	.dcard:not(.triple) .kpis :global(.num) {
		margin-top: 0;
		font-size: clamp(32px, 2.9vw, 56px);
	}
	.tiles {
		grid-area: tiles;
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		grid-template-rows: minmax(0, 491fr) minmax(0, 249fr);
		gap: clamp(10px, 0.95vw, 18.3px);
		min-height: 0;
	}
	.tiles :global(.tile:nth-child(1)) {
		grid-column: 1;
		grid-row: 1;
	}
	.tiles :global(.tile:nth-child(2)) {
		grid-column: 2;
		grid-row: 1 / span 2;
	}
	.tiles :global(.tile:nth-child(3)) {
		grid-column: 1;
		grid-row: 2;
	}
	/* the pill: 179 × 37, 13 px corners, Condensed Bold 24 px, flush with
	   the card's bottom edge */
	/* the user's edit (2026-08-27): a 145,7 × 37 pill with 9,8 px corners,
	   «explore more» in Futura Bold 18 px 12 px in, an arrow in the room
	   it leaves at the right */
	.more,
	.back {
		align-self: flex-start;
		display: inline-flex;
		align-items: center;
		justify-content: flex-start;
		box-sizing: border-box;
		width: clamp(110px, 7.59vw, 145.7px);
		height: clamp(28px, 3.45vh, 37px);
		padding: 0 clamp(8px, 0.57vw, 11px);
		text-decoration: none;
		/* Futura's TRUE bold: the Book family has no 700, the plain one has */
		font-family: 'futura-100-greek', var(--font-ui);
		font-weight: 700;
		font-size: clamp(13px, 0.94vw, 18px);
		line-height: 1;
		white-space: nowrap;
		color: #fff;
		background: var(--card-accent);
		border-radius: 9.8px;
	}
	.more:hover,
	.back:hover {
		filter: brightness(1.15);
	}
	/* the frames, at the article width, with a slim head that names the
	   stream and the way back */
	.rest {
		max-width: var(--content-w);
		margin: 0 auto;
		scroll-margin-top: 96px;
	}
	.resthead {
		display: flex;
		align-items: center;
		gap: var(--sp-4);
		margin: 0 0 var(--sp-8);
	}
	.resthead .back {
		margin-left: auto;
		align-self: center;
		width: auto;
		font-size: var(--fs-14);
		height: auto;
		padding: var(--sp-2) var(--sp-5);
	}
	/* ---- the sponsored card's three columns (Artboard 4, user 2026-08-27):
	   the text 549 wide, the middle 703 (a 137 px KPI row over the tall
	   tile), the right 521 (a 412 tile over a 521 one) */
	.dcard.triple {
		display: grid;
		/* the artboard's widths with the user's gaps: 549 · 25 · 711 · 17 ·
		   516 — the 3 px the narrower gap frees and 5 px of the right column
		   go to the MIDDLE column (user, 2026-08-27) — as fractions of the
		   card's 1818,5 */
		grid-template-columns: var(--cols);
		grid-template-rows: none;
		grid-template-areas: none;
		column-gap: 0;
		row-gap: 0;
	}
	.triple .mid {
		grid-column: 3;
	}
	.triple .rightcol {
		grid-column: 5;
	}
	.triple .side {
		grid-area: auto;
		grid-column: 1;
	}
	.triple .mid {
		display: grid;
		/* the KPI row keeps its 137; whatever the narrower gaps free goes
		   to the timeline (user, 2026-08-27) */
		grid-template-rows: var(--kpi-h, clamp(104px, 12.7vh, 137px)) var(--mid-rows);
		/* the artboard's gap at 1080 px, shrinking with a shorter window
		   (1 px of the artboard = 0.0926 vh) — the same rule in both columns */
		row-gap: min(calc(var(--mid-gap-n) * 1px), calc(var(--mid-gap-n) * 0.0926vh));
		min-height: 0;
	}
	.triple .rightcol {
		display: grid;
		/* the user's edit of 2026-08-27: 374,5 above, 563,1 below, 15,4 apart */
		grid-template-rows: var(--right-rows);
		row-gap: min(calc(var(--right-gap-n) * 1px), calc(var(--right-gap-n) * 0.0926vh));
		min-height: 0;
	}
	.triple .kpis {
		grid-area: auto;
	}
	/* the spanning form: the KPI row is the grid's first row across the two
	   chart columns, the side column spans both rows */
	.dcard.triple.span {
		grid-template-rows: var(--kpi-h, clamp(104px, 12.7vh, 137px)) minmax(0, 1fr);
		row-gap: var(--mid-gap);
	}
	.triple.span .side {
		grid-row: 1 / 3;
	}
	.triple.span .kpis.wide {
		grid-column: 3 / 6;
		grid-row: 1;
		min-height: 0;
	}
	.triple.span .mid {
		grid-column: 3;
		grid-row: 2;
		grid-template-rows: var(--mid-rows);
	}
	.triple.span .rightcol {
		grid-column: 5;
		grid-row: 2;
	}
	/* the symbol with the stream's name beside it, in the section hue */
	.who.big {
		align-items: center;
		gap: clamp(16px, 3.7vw, 71px);
		margin-top: 0;
	}
	/* the artboard sets the name on three centred lines */
	.bigname {
		display: flex;
		flex-direction: column;
		align-items: center;
		font-family: var(--font-display-narrow);
		font-weight: 900;
		font-size: clamp(15px, 1.25vw, 24px);
		line-height: 1.2;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		text-align: center;
		color: var(--card-accent);
	}
	.bigname .ln {
		display: block;
		white-space: nowrap;
	}
	.triple .narrative {
		margin-top: 4vh;
	}
	@media (max-width: 1100px) {
		.dcard.triple {
			grid-template-columns: 1fr;
			height: auto;
		}
		.triple .side,
		.triple .mid,
		.triple .rightcol,
		.triple.span .kpis.wide {
			grid-column: 1;
			grid-row: auto;
		}
		.triple .mid,
		.triple .rightcol {
			grid-template-rows: none;
			row-gap: var(--sp-4);
		}
		.triple :global(.tile) {
			min-height: 420px;
		}
		.dcard {
			grid-template-columns: 1fr;
			grid-template-rows: auto auto auto;
			grid-template-areas:
				'side'
				'kpis'
				'tiles';
			height: auto;
		}
		.narrative {
			overflow: visible;
		}
		.dcard:not(.triple) .kpis :global(.card) {
			min-height: 7.5rem;
		}
		.tiles {
			grid-template-columns: 1fr;
			grid-template-rows: none;
		}
		.tiles :global(.tile) {
			grid-column: auto !important;
			grid-row: auto !important;
			min-height: 420px;
		}
	}
</style>
