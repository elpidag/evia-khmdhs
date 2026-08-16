<script lang="ts">
	/**
	 * The shared detail-page header (user template, 2026-08-17): CAPS
	 * label / value fact rows on the left — the act code is the first,
	 * emphasised row — and a square map slot on the right, with the
	 * provenance caveat under the facts. Rows come in as a snippet so
	 * each dataset renders links/chips freely.
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		facts: Snippet;
		map?: Snippet;
		/** provenance line under the facts (location sourcing, EFFIS…) */
		caveat?: string;
	}
	let { facts, map, caveat = '' }: Props = $props();
</script>

<div class="head" class:nomap={!map}>
	<div class="left">
		<dl class="facts">
			{@render facts()}
		</dl>
		{#if caveat}
			<p class="caveat">{caveat}</p>
		{/if}
	</div>
	{#if map}
		<div class="right">
			{@render map()}
		</div>
	{/if}
</div>

<style>
	.head {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(300px, 460px);
		gap: var(--sp-8);
		align-items: start;
		margin-bottom: var(--sp-8);
	}
	.head.nomap {
		grid-template-columns: minmax(0, 1fr);
	}
	@media (max-width: 900px) {
		.head {
			grid-template-columns: 1fr;
		}
	}
	.facts {
		display: grid;
		grid-template-columns: max-content minmax(0, 1fr);
		column-gap: var(--sp-6);
		row-gap: 6px;
		margin: 0;
	}
	.facts :global(dt) {
		font-family: var(--font-display);
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		font-size: var(--fs-14);
	}
	.facts :global(dd) {
		margin: 0;
		font-size: var(--fs-14);
		align-self: end;
	}
	/* qualifier text inside a label («of the designation decision») reads
	   like the value it sits next to, not like the CAPS label */
	.facts :global(dt small) {
		font-family: var(--font-ui);
		font-weight: 400;
		text-transform: none;
		letter-spacing: normal;
		font-size: var(--fs-14);
	}
	/* the identity row (act code) leads, emphasised */
	.facts :global(dt.id) {
		font-size: var(--fs-18);
	}
	/* the act code mirrors its label exactly — same face, size, weight */
	.facts :global(dd.id) {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-18);
		letter-spacing: 0.02em;
	}
	/* a spacer row between fact groups, as in the template */
	.facts :global(dt.gap),
	.facts :global(dd.gap) {
		height: var(--sp-3);
	}
	/* spans the full label+value width of the facts grid above it */
	.caveat {
		margin-top: var(--sp-6);
		color: var(--ink-soft);
		font-size: var(--fs-12);
	}
	.right {
		position: relative;
	}
</style>
