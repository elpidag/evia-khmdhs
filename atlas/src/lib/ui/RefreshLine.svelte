<script lang="ts">
	/**
	 * «Records last refreshed on …» — the one fact of freshness a reader
	 * needs, at the foot of every page that shows a dataset (user,
	 * 2026-08-29). The date is the API's own (the newest fetch in the
	 * databases), never typed; the site has no footer, so this is a single
	 * line at the end of the page's own content, not a footer returning.
	 */
	import { page } from '$app/state';
	/** `compact`: one small inline line beside the card's «explore more»
	 *  pill (the author, 2026-09-04) — no rule above, no margins */
	let { compact = false }: { compact?: boolean } = $props();
	const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
		'August', 'September', 'October', 'November', 'December'];
	const refreshed = $derived.by(() => {
		const g = page.data.meta?.generated;
		if (!g) return null;
		const d = new Date(g);
		return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
	});
</script>

{#if refreshed}
	<p class="refreshed" class:compact>
		Records last refreshed on {refreshed} ·
		<a href="/story#methodology">how these figures are made</a>
	</p>
{/if}

<style>
	.refreshed {
		margin: var(--sp-10) 0 var(--sp-6);
		padding-top: var(--sp-3);
		border-top: 1px solid var(--line);
		font-family: var(--font-ui);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.refreshed a {
		color: inherit;
	}
	.refreshed.compact {
		margin: 0;
		padding: 0;
		border: 0;
		font-size: var(--fs-12);
		line-height: 1.3;
	}
</style>
