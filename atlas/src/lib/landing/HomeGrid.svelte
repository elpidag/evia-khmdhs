<script lang="ts">
	/**
	 * The landing menu: a square 4×4 of hairline cells. The field cell
	 * renders whatever the page passes in (the drifting codes) plus a ↻;
	 * link cells are the menu; the rest are empty on purpose.
	 */
	import { cellGrid, type HomeCell } from './homeCells';
	let {
		cells,
		field,
		onReplay
	}: {
		cells: HomeCell[];
		field?: import('svelte').Snippet;
		onReplay?: () => void;
	} = $props();
	const grid = $derived(cellGrid(cells));
</script>

<div class="grid" role="navigation" aria-label="Site menu">
	{#each grid as row, r (r)}
		{#each row as cell, c (c)}
			{#if cell.kind === 'link'}
				<a class="cell link" class:ink={cell.tone === 'ink'} href={cell.href}>{cell.label}</a>
			{:else if cell.kind === 'field'}
				<div class="cell field">
					{#if field}{@render field()}{/if}
					{#if onReplay}
						<button class="replay" type="button" onclick={onReplay} aria-label="Replay the animation"
							>↻</button
						>
					{/if}
				</div>
			{:else}
				<div class="cell" aria-hidden="true"></div>
			{/if}
		{/each}
	{/each}
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(4, 1fr);
		aspect-ratio: 1;
		width: 100%;
		/* one hairline between cells, none doubled: each cell draws its
		   right and bottom edge, the grid its top and left */
		border-top: 1px solid var(--ink);
		border-left: 1px solid var(--ink);
	}
	.cell {
		position: relative;
		border-right: 1px solid var(--ink);
		border-bottom: 1px solid var(--ink);
		min-width: 0;
		overflow: hidden;
	}
	.link {
		display: flex;
		align-items: flex-start;
		justify-content: flex-end;
		padding: var(--sp-4);
		text-decoration: none;
		color: var(--ink);
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-16);
		letter-spacing: 0.01em;
		text-align: right;
		text-transform: uppercase;
		transition: background 0.15s ease, color 0.15s ease;
	}
	.link:hover,
	.link:focus-visible {
		background: var(--paper-3);
		outline: none;
	}
	.link.ink {
		background: var(--ink);
		color: var(--paper);
	}
	.link.ink:hover,
	.link.ink:focus-visible {
		background: var(--ink-soft);
	}
	.field {
		background: var(--paper);
	}
	.replay {
		position: absolute;
		right: 6px;
		bottom: 4px;
		font: inherit;
		font-size: var(--fs-16);
		line-height: 1;
		background: none;
		border: none;
		padding: 2px 4px;
		color: var(--ink-faint);
		cursor: pointer;
	}
	.replay:hover {
		color: var(--ink);
	}
</style>
