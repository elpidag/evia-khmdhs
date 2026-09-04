<script lang="ts">
	/**
	 * The landing menu — the author's artboard of 2026-09-04: a square 4×4
	 * of 2 px-ruled cells filling the frame's height on the right. Text
	 * links right-aligned in Obviously Narrow Bold (START HERE 36 px in the
	 * co-op green at the top, the two others 24 px in ink at the bottom);
	 * the network symbol; the author's own schematic drawings and fire
	 * image at the artboard's offsets; and STILL fields of codes in the
	 * white cells — the top-left one is where the opening animation lands,
	 * so the page renders that field itself (plus a ↻).
	 */
	import type { Landing } from '$lib/api';
	import { SYMBOLS } from '$lib/datasets';
	import CodeField from './CodeField.svelte';
	import { cellGrid, gridArea, type HomeCell } from './homeCells';

	let {
		cells,
		codes = null,
		seed = 0,
		field,
		onReplay
	}: {
		cells: HomeCell[];
		/** the landing payload: the codes for the still fields */
		codes?: Landing | null;
		seed?: number;
		field?: import('svelte').Snippet;
		onReplay?: () => void;
	} = $props();
	const grid = $derived(cellGrid(cells));
	const symbolOf = (key: string) => SYMBOLS.find((s) => s.key === key);
</script>

{#snippet drawing(cell: Extract<HomeCell, { kind: 'image' }>)}
	<img
		class="drawing"
		src={cell.src}
		alt={cell.alt}
		style:left="{cell.left * 100}%"
		style:top="{cell.top * 100}%"
		style:width="{cell.width * 100}%"
	/>
{/snippet}

<div class="grid" role="navigation" aria-label="Site menu">
	{#each grid as row, r (r)}
		{#each row as cell, c (c)}
			{#if cell.kind === 'covered'}
				<!-- under a spanning neighbour -->
			{:else if cell.kind === 'link'}
				<a
					class="cell link"
					class:lg={cell.size === 'lg'}
					class:bottom={cell.at === 'bottom'}
					style:color={cell.color ?? null}
					style:grid-area={gridArea(cell)}
					href={cell.href}>{cell.label}</a
				>
			{:else if cell.kind === 'codes'}
				<div class="cell codes" style:grid-area={gridArea(cell)}>
					{#if cell.field}
						{#if field}{@render field()}{/if}
						{#if onReplay}
							<button
								class="replay"
								type="button"
								onclick={onReplay}
								aria-label="Replay the animation">↻</button
							>
						{/if}
					{:else}
						<CodeField {codes} seed={seed + 11 * (cell.r * 4 + cell.c)} dense playing={false} />
					{/if}
				</div>
			{:else if cell.kind === 'symbol'}
				{@const s = symbolOf(cell.key)}
				<a
					class="cell symbol"
					style:grid-area={gridArea(cell)}
					style:--sym-w="{cell.size * 100}%"
					style:--sym-aspect={s?.aspect ?? 1}
					href={cell.href}
					aria-label={s?.label ?? cell.key}
				>
					{#if s?.symbolColor}
						<img class="pic" src={s.symbolColor} alt="" />
					{:else if s?.symbol}
						<span
							class="glyph"
							style:--sym-img={`url(${s.symbol})`}
							style:background={s.color}
						></span>
					{/if}
				</a>
			{:else if cell.href}
				<a class="cell" style:grid-area={gridArea(cell)} href={cell.href} aria-label={cell.alt}>
					{@render drawing(cell)}
				</a>
			{:else}
				<div class="cell" style:grid-area={gridArea(cell)}>
					{@render drawing(cell)}
				</div>
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
		min-height: 0;
		overflow: hidden;
		background: var(--paper);
	}
	/* the text links: right-aligned, ~26 artboard px in, Obviously Narrow
	   Bold — 24 px at the bottom, START HERE 36 px at the top */
	.link {
		display: flex;
		align-items: flex-start;
		justify-content: flex-end;
		padding: 24px 26px;
		text-decoration: none;
		color: var(--ink);
		font-family: var(--font-display-narrow);
		font-weight: 700;
		font-size: clamp(14px, 1.25vw, 24px);
		line-height: 1.1;
		text-align: right;
		text-transform: uppercase;
		transition: background 0.15s ease;
	}
	.link.bottom {
		align-items: flex-end;
		padding-bottom: 22px;
	}
	.link.lg {
		font-size: clamp(20px, 1.875vw, 36px);
		padding-top: 28px;
	}
	a.cell:hover,
	a.cell:focus-visible {
		background: var(--paper-2);
		outline: none;
	}
	/* a site symbol: centred at its fraction of the cell, in the shape of
	   its own viewBox */
	.symbol {
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.symbol .pic,
	.symbol .glyph {
		display: block;
		width: var(--sym-w);
		aspect-ratio: var(--sym-aspect);
		flex: none;
	}
	.symbol .pic {
		object-fit: contain;
	}
	.symbol .glyph {
		-webkit-mask: var(--sym-img) center / contain no-repeat;
		mask: var(--sym-img) center / contain no-repeat;
	}
	/* the author's drawings at the artboard's offsets; the height follows
	   the file's own shape */
	.drawing {
		position: absolute;
		display: block;
		height: auto;
	}
	.replay {
		position: absolute;
		right: 6px;
		bottom: 4px;
		z-index: 1;
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
