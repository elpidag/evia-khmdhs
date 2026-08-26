<script lang="ts">
	/**
	 * A dataset's CARD (user mock, 2026-08-27) — exactly one viewport, no
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
	import Prose from './Prose.svelte';
	import { MORE_HASH, isExpanded, lessHref, moreHref } from './expanded';
	import type { Snippet } from 'svelte';

	let {
		ds,
		params,
		kpis,
		hint = '',
		text,
		tiles,
		more
	}: {
		ds: DatasetKey;
		/** the page's own URL parameters — any of them opens the frames */
		params: readonly string[];
		kpis: KpiCard[];
		/** the content file behind the narrative, shown while it is empty */
		hint?: string;
		text: Snippet;
		/** three Tile components, in reading order */
		tiles: Snippet;
		more: Snippet;
	} = $props();

	const sym = $derived(symbolFor(ds));
	const expanded = $derived(isExpanded(page.url, params));

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
{:else}
	<div class="dcard" style:--card-accent={sym.color}>
		<div class="side">
			<div class="who">
				<DatasetSymbol key={ds} size={150} />
				<span class="label">{sym.label}</span>
			</div>
			<div class="narrative">
				<Prose {hint}>{@render text()}</Prose>
			</div>
			<a class="more" href={moreHref(page.url)}>explore more</a>
		</div>
		<div class="kpis"><KpiCards cards={kpis} color={sym.color} /></div>
		<div class="tiles">{@render tiles()}</div>
	</div>
{/if}

<style>
	/* the card is the viewport under the header, to the pixel: the layout
	   widens `main` and sets --header-h for these pages */
	.dcard {
		display: grid;
		grid-template-columns: minmax(16rem, 29%) minmax(0, 1fr);
		grid-template-rows: auto minmax(0, 1fr);
		grid-template-areas:
			'side kpis'
			'side tiles';
		gap: var(--sp-5, 1.25rem) var(--sp-8);
		height: calc(100dvh - var(--header-h, 60px) - 2 * var(--sp-4));
		box-sizing: border-box;
		align-items: stretch;
	}
	.side {
		grid-area: side;
		display: flex;
		flex-direction: column;
		gap: var(--sp-6);
		min-height: 0;
	}
	.who {
		display: flex;
		align-items: flex-end;
		gap: var(--sp-4);
	}
	.label {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-14);
		color: var(--card-accent);
		line-height: 1.2;
		padding-bottom: var(--sp-2);
	}
	/* a long narrative scrolls inside its column; the button stays put */
	.narrative {
		flex: 1;
		min-height: 0;
		overflow: auto;
	}
	.kpis {
		grid-area: kpis;
	}
	/* the tiles' grid takes what the card leaves: MAP top-left, the tall
	   one right, the third under MAP — the mock's proportions */
	.tiles {
		grid-area: tiles;
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		grid-template-rows: minmax(0, 3fr) minmax(0, 2fr);
		gap: var(--sp-4);
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
	.more,
	.back {
		align-self: flex-start;
		text-decoration: none;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-14);
		color: #fff;
		background: var(--card-accent);
		border-radius: 999px;
		padding: var(--sp-2) var(--sp-6);
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
	.resthead .label {
		padding-bottom: 0;
	}
	.resthead .back {
		margin-left: auto;
		align-self: center;
	}
	@media (max-width: 1100px) {
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
