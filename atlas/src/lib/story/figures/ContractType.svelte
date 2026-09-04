<script lang="ts">
	/**
	 * Figure 27 (the author's marker 10, «types of work graph»): the
	 * Anti-nero page's CONTRACT TYPE frame, live in the story (the author,
	 * 2026-09-03) — its title, its stated-€ / number-of-contracts toggle and
	 * its bars, one curated work-type category per in-scope contract, through
	 * the SAME transform the page uses (`lib/transforms/categoryRows.ts`), so
	 * the two can never drift. The toggle is the site's own (`?ct=`, as on
	 * /antinero); the payload arrives after hydration, as every big payload
	 * on the site does.
	 */
	import { page } from '$app/state';
	import { apiGetCached, type AntineroOverview } from '$lib/api';
	import BarH from '$lib/charts/BarH.svelte';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import { categoryRows, type CategoryLens } from '$lib/transforms/categoryRows';
	import { eurShort, grInt } from '$lib/transforms/format';

	let o = $state.raw<AntineroOverview | null>(null);
	$effect(() => {
		apiGetCached<AntineroOverview>(fetch, '/api/antinero/overview').then((p) => (o = p));
	});
	const lens = $derived<CategoryLens>(page.url.searchParams.get('ct') === 'n' ? 'n' : 'eur');
	const rows = $derived(o ? categoryRows(o.categories, lens) : []);
</script>

<div class="ct">
	<!-- the frame's own title line: the title left, the lens toggle right -->
	<div class="titlerow">
		<h2 class="finding">CONTRACT TYPE</h2>
		<SegmentToggle
			param="ct"
			fallback="eur"
			options={[
				{ value: 'eur', label: 'stated net €' },
				{ value: 'n', label: 'number of contracts' }
			]}
		/>
	</div>
	{#if rows.length}
		<BarH
			{rows}
			color="color-mix(in srgb, var(--ink) 94.6%, var(--paper))"
			inside
			barHeight={35}
			fmt={lens === 'eur' ? eurShort : grInt}
			valuesRight
		/>
	{/if}
</div>

<style>
	.ct {
		width: 100%;
	}
	.titlerow {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-4);
		margin-bottom: var(--sp-4);
	}
	/* the title in the FIGURE's own type — the caption's face, size and
	   tone, not the frame's display title (the author, 2026-09-03) */
	.finding {
		margin: 0;
		font-family: var(--font-ui);
		font-weight: 400;
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		letter-spacing: 0.02em;
	}
	/* the toggle smaller than the frame's, to the figure's scale */
	.titlerow :global(.toggle button) {
		font-size: 11px;
		padding: 2px 8px;
	}
</style>
