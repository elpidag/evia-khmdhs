<script lang="ts">
	/**
	 * The landing menu — Artboard 2 (user, 2026-08-27): a square 4×4 of
	 * 2 px-ruled cells filling the frame's height on the right. Labels sit
	 * top-right of their cell in Obviously Narrow 24 px (Bold on the black
	 * START HERE cell, Medium elsewhere); the field cell renders whatever
	 * the page passes in, plus a ↻.
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
			{:else if cell.kind === 'note'}
				<div class="cell note">{cell.label}</div>
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
		height: 100%;
		box-sizing: border-box;
		/* one 2 px rule between cells, none doubled: each cell draws its
		   right and bottom edge, the grid its top and left */
		border-top: 2px solid var(--ink);
		border-left: 2px solid var(--ink);
	}
	.cell {
		position: relative;
		border-right: 2px solid var(--ink);
		border-bottom: 2px solid var(--ink);
		min-width: 0;
		overflow: hidden;
	}
	.link,
	.note {
		display: flex;
		align-items: flex-start;
		justify-content: flex-end;
		/* the artboard's inset: ~26 px from the right, the baseline ~50 px down */
		padding: 24px 26px;
		text-decoration: none;
		color: var(--ink);
		font-family: var(--font-display-narrow);
		font-weight: 500;
		font-size: clamp(14px, 1.25vw, 24px);
		line-height: 1.1;
		text-align: right;
		text-transform: uppercase;
		transition:
			background 0.15s ease,
			color 0.15s ease;
	}
	.note {
		font-weight: 700;
		font-size: clamp(12px, 0.94vw, 18px);
	}
	.link:hover,
	.link:focus-visible {
		background: var(--paper-3);
		outline: none;
	}
	.link.ink {
		background: var(--ink);
		color: var(--paper);
		font-weight: 700;
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
