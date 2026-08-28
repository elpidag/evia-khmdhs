<script lang="ts">
	/**
	 * A tile of the dataset card (Artboard 4, user 2026-08-27): a panel
	 * that takes the height the card's grid gives it and lets its content
	 * scroll rather than grow — the card composes one viewport.
	 *
	 * The title is 14 px Obviously Bold at the top left and links to the
	 * full frame; the ⓘ sits at the top RIGHT. Where a `legend` snippet is
	 * given the ⓘ SWITCHES the tile to that legend and back (user, same
	 * day: «the i on the right side will be used to switch to the legend of
	 * each»); where only `hint` text is given it opens the usual card.
	 */
	import type { Snippet } from 'svelte';
	import Hint from './Hint.svelte';
	let {
		title,
		sub = '',
		hint = '',
		href = '',
		legend,
		controls,
		fit = false,
		headOver = false,
		bleed = false,
		tight = false,
		children
	}: {
		title: string;
		/** what the drawing shows, one line */
		sub?: string;
		/** how to read it, behind the ⓘ */
		hint?: string;
		/** the full frame this tile stands for */
		href?: string;
		/** shown INSTEAD of the chart when the ⓘ is pressed */
		legend?: Snippet;
		/** a switch on the title line (the sponsors tile's two forms) */
		controls?: Snippet;
		/** the drawing is sized to the room it has, so the tile must NOT
		 *  scroll (user, 2026-08-27); elsewhere a long list still scrolls
		 *  rather than being cut off */
		fit?: boolean;
		/** the label and the ⓘ sit ON the drawing, which then fills the
		 *  whole tile — the card's map (user, 2026-08-27) */
		headOver?: boolean;
		/** the body may draw into the tile's padding (the section still
		 *  clips at its border) — the stacked column's counts and names
		 *  (user, 2026-08-28) */
		bleed?: boolean;
		/** 5 px at the foot instead of 12 — the user's WHAT TYPES panel has
		 *  its last bar 5 px above the edge */
		tight?: boolean;
		children: Snippet;
	} = $props();
	let w = $state(0);
	let h = $state(0);
	let showLegend = $state(false);
</script>

<section class="tile" class:fit class:over={headOver} class:tight class:bleed>
	<div class="head">
		<h3 class="tt">
			{#if href}<a {href}>{title}</a>{:else}{title}{/if}
		</h3>
		{#if controls}<div class="ctl">{@render controls()}</div>{/if}
		{#if legend}
			<button
				class="info"
				class:on={showLegend}
				type="button"
				onclick={() => (showLegend = !showLegend)}
				aria-pressed={showLegend}
				title={showLegend ? 'Back to the chart' : 'What the marks mean'}
				aria-label={showLegend ? 'Back to the chart' : 'What the marks mean'}>i</button
			>
		{:else if hint}
			<Hint text={hint} heading width="320px" />
		{/if}
	</div>
	{#if sub && !showLegend}<p class="sub">{sub}</p>{/if}
	<div class="body" bind:clientWidth={w} bind:clientHeight={h}>
		{#if showLegend && legend}
			<div class="legend">{@render legend()}</div>
		{:else}
			{@render children()}
		{/if}
	</div>
</section>

<style>
	.tile {
		display: flex;
		flex-direction: column;
		min-width: 0;
		min-height: 0;
		/* the artboard's own panel grey (user, 2026-08-27) — our --paper-2
		   is a warm cream and read as a heavier block */
		background: var(--tile-bg, #f2f2f2);
		padding: 12px 16px 12px;
		box-sizing: border-box;
	}
	.head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 10px;
	}
	.tt {
		margin: 0;
		font-family: var(--font-display);
		font-weight: 700;
		/* 10 px, the size the user set for every tile label */
		font-size: 10px;
		line-height: 1.15;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		color: var(--ink);
	}
	.tt a {
		color: inherit;
		text-decoration: none;
	}
	.tt a:hover {
		text-decoration: underline;
	}
	/* the artboard's ⓘ: a filled disc at the tile's top-right */
	.ctl {
		margin-left: auto;
		flex: none;
	}
	.ctl :global(.seg) {
		font-size: 10px;
	}
	.info {
		flex: none;
		margin-left: auto;
		width: 15px;
		height: 15px;
		border-radius: 50%;
		border: none;
		background: var(--ink);
		color: var(--paper);
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 9px;
		line-height: 15px;
		padding: 0;
		cursor: pointer;
	}
	.info.on {
		background: var(--card-accent, var(--ink));
	}
	.ctl + .info {
		margin-left: 8px;
	}
	.sub {
		margin: 4px 0 0;
		font-family: var(--font-display-cond);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.25;
		color: var(--ink-soft);
	}
	.body {
		flex: 1;
		min-height: 0;
		position: relative;
		overflow: auto;
		margin-top: 8px;
	}
	/* a fitted tile never scrolls — its drawing takes the room it has */
	.tile.fit .body {
		overflow: hidden;
	}
	.tile.bleed .body {
		overflow: visible;
	}
	/* the map's tile: the drawing fills it and the label rides on top */
	.tile.over {
		position: relative;
		padding: 0;
	}
	/* the user's edit: the map's label 9 px in and 9 px down */
	.tile.over .head {
		position: absolute;
		top: 9px;
		left: 9px;
		right: 9px;
		z-index: 2;
		pointer-events: none;
	}
	.tile.tight {
		padding-bottom: 5px;
	}
	/* the links and buttons on the overlaid head answer the pointer — the
	   page's own controls included, hence :global */
	.tile.over .head :global(a),
	.tile.over .head :global(button) {
		pointer-events: auto;
	}
	.tile.over .body {
		margin-top: 0;
	}
	.tile.over .legend {
		padding: 34px 16px 12px;
		background: var(--tile-bg, #f2f2f2);
	}
	.legend {
		height: 100%;
		overflow: auto;
	}
</style>
