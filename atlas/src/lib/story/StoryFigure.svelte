<script lang="ts">
	/**
	 * The story's right column — the author's artboard: a square image, its
	 * caption under it, and under that the footnotes of the passage the reader
	 * is on, set in two columns.
	 *
	 * Every passage's block is mounted in the SAME rect and only opacity moves,
	 * so a swap causes no reflow and the column never jumps. Phase 1 renders
	 * placeholder boxes; the images, captions and real notes arrive with the
	 * author's text (and, for the KEY FINDINGS charts, a chart in the same slot).
	 */
	import type { Snippet } from 'svelte';

	export interface FigureBlock {
		/** the beat this belongs to */
		id: string;
		/** the caption printed under the image */
		caption?: string;
		/** the footnotes of that passage */
		notes?: { n: number; text: string }[];
	}

	interface Props {
		blocks: FigureBlock[];
		active: string | null;
		/** drawn inside the square when a block has no image yet */
		placeholder?: Snippet<[FigureBlock]>;
	}
	let { blocks, active, placeholder }: Props = $props();

	/** the first block stands in until the reader reaches one of their own */
	const shown = $derived(active ?? (blocks.length ? blocks[0].id : null));
</script>

<div class="fig">
	{#each blocks as b (b.id)}
		<div class="layer" class:on={b.id === shown} aria-hidden={b.id !== shown}>
			<div class="box">
				{#if placeholder}{@render placeholder(b)}{/if}
			</div>
			<p class="cap">{b.caption ?? ''}</p>
			{#if b.notes?.length}
				<ol class="notes">
					{#each b.notes as n (n.n)}
						<li value={n.n}>{n.text}</li>
					{/each}
				</ol>
			{/if}
		</div>
	{/each}
</div>

<style>
	.fig {
		position: relative;
		width: 100%;
		height: 100%;
	}
	/* every block in the same rect: a swap changes no layout, so nothing jumps */
	.layer {
		position: absolute;
		inset: 0;
		display: grid;
		grid-template-rows: auto auto minmax(0, 1fr);
		row-gap: var(--sp-3);
		opacity: 0;
		visibility: hidden;
		transition:
			opacity 0.35s ease,
			visibility 0s 0.35s;
	}
	.layer.on {
		opacity: 1;
		visibility: visible;
		transition:
			opacity 0.35s ease,
			visibility 0s 0s;
	}

	.layer {
		/* caption and notes are set to the IMAGE's width, not the column's */
		--fig-w: min(100%, 540px);
	}
	.box {
		/* the artboard's square, inset in its column */
		width: var(--fig-w);
		aspect-ratio: 1;
		background: var(--paper-2);
		display: grid;
		place-items: center;
	}
	.cap {
		margin: 0;
		max-width: var(--fig-w);
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		min-height: 2.4em;
	}
	.notes {
		margin: 0;
		max-width: var(--fig-w);
		padding-left: 1.1em;
		columns: 2;
		column-gap: var(--sp-6);
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		overflow: auto; /* a long set scrolls inside its own area */
	}
	.notes li {
		break-inside: avoid;
		margin-bottom: var(--sp-2);
	}

	@media (prefers-reduced-motion: reduce) {
		.layer {
			transition: none;
		}
	}
	@media (max-width: 1100px) {
		/* released: the rails become a plain sequence under the text */
		.fig {
			height: auto;
		}
		.layer {
			position: static;
			opacity: 1;
			visibility: visible;
			margin-bottom: var(--sp-8);
		}
	}
</style>
