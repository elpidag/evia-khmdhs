<script lang="ts">
	/**
	 * The one place the markdown narration is dressed: body face, prose
	 * measure, links in the page ink. `hint` names the file behind an empty
	 * slot so the author sees where to write (dev only).
	 */
	import { dev } from '$app/environment';
	let { hint = '', children }: { hint?: string; children: import('svelte').Snippet } = $props();
</script>

<div class="prose" data-hint={dev ? hint : null}>
	{@render children()}
</div>

<style>
	.prose {
		max-width: var(--prose-w);
		font-size: var(--fs-16);
		line-height: 1.5;
	}
	.prose :global(p) {
		margin: 0 0 var(--sp-4);
	}
	.prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.prose :global(h2),
	.prose :global(h3) {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: 0.01em;
		font-size: var(--fs-18);
		margin: var(--sp-6) 0 var(--sp-3);
	}
	.prose :global(a) {
		color: inherit;
	}
	.prose :global(ul),
	.prose :global(ol) {
		padding-left: 1.2em;
		margin: 0 0 var(--sp-4);
	}
	.prose :global(em) {
		color: var(--ink-soft);
	}
	/* an empty slot says where its text goes (dev only) */
	.prose:empty::before {
		content: attr(data-hint);
		color: var(--ink-faint);
		font-size: var(--fs-13);
	}
</style>
