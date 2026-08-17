<script lang="ts">
	import type { Snippet } from 'svelte';

	/** The beeswarm's two-column shell, hoisted so several charts can share
	 *  it: explanation in a 210px column, chart in the rest. On the ΔΑΣΕ
	 *  value chart both modes render inside one of these, so the plot keeps
	 *  exactly the same width when the reader switches between them. */
	interface Props {
		note?: string;
		children: Snippet;
	}
	let { note = '', children }: Props = $props();
</script>

<div class="cols" class:nonote={!note}>
	{#if note}<p class="sidenote">{note}</p>{/if}
	<div class="body">{@render children()}</div>
</div>

<style>
	.cols {
		display: grid;
		grid-template-columns: 210px minmax(0, 1fr);
		gap: var(--sp-6);
		align-items: start;
	}
	.cols.nonote {
		grid-template-columns: minmax(0, 1fr);
	}
	@media (max-width: 800px) {
		.cols {
			grid-template-columns: 1fr;
		}
	}
	.sidenote {
		color: var(--ink-soft);
		font-size: var(--fs-13);
		margin: 0;
	}
	.body {
		min-width: 0;
	}
</style>
