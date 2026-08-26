<script lang="ts">
	/**
	 * A tile of the dataset card (user mock, 2026-08-27): a titled panel
	 * that takes the height the card's grid gives it and lets its content
	 * scroll rather than grow — the card composes one viewport. The full
	 * frame of the same chart lives in the unfolded part.
	 */
	import type { Snippet } from 'svelte';
	let {
		title,
		href = '',
		children
	}: { title: string; /** the full frame this tile stands for */ href?: string; children: Snippet } =
		$props();
	let w = $state(0);
	let h = $state(0);
</script>

<section class="tile">
	<h3 class="tt">
		{#if href}<a {href}>{title}</a>{:else}{title}{/if}
	</h3>
	<div class="body" bind:clientWidth={w} bind:clientHeight={h}>
		{@render children()}
	</div>
</section>

<style>
	.tile {
		display: flex;
		flex-direction: column;
		min-width: 0;
		min-height: 0;
		background: var(--paper-2);
		padding: var(--sp-4);
		box-sizing: border-box;
	}
	.tt {
		margin: 0 0 var(--sp-3);
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--card-accent, var(--ink));
	}
	.tt a {
		color: inherit;
		text-decoration: none;
	}
	.tt a:hover {
		text-decoration: underline;
	}
	.body {
		flex: 1;
		min-height: 0;
		position: relative;
		overflow: auto;
	}
</style>
