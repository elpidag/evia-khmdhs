<script lang="ts">
	/**
	 * A chart across the WHOLE PAGE, inside the narrative's flow (the author,
	 * 2026-09-04): STATE-FUNDED, TWO WORLDS — every contract of both
	 * programmes as a dot — after the paragraph that says the money reached a
	 * different population of contractors, the next paragraph following it.
	 * No title of its own (the author, 2026-09-04) — the chart's caption line
	 * and its two side labels say what it is.
	 *
	 * Mounted by the story page into the `[CHART: state-funded]` marker's
	 * placeholder (`scripts/remark-tag-paragraphs.ts` turns the author's
	 * marker line into a `div.chartmark`); the placeholder is full-bleed —
	 * the page sets `--nar-left`, the narrative column's distance from the
	 * window's left edge, and `--page-w`, the window's width without the
	 * scrollbar — and this band sets its content at the site's 1152 px.
	 */
	import type { ComparePayload } from '$lib/api';
	import StateFunded from '$lib/charts/StateFunded.svelte';
	import { grInt } from '$lib/transforms/format';

	let { c }: { c: ComparePayload } = $props();
</script>

<div class="band">
	<div class="inner">
		<StateFunded
			dots={c.dots}
			nCompanies={c.pipelines.antinero.n_vats}
			nCoops={c.pipelines.dase.n_vats}
		/>
		<p class="note">
			Zero shared companies: {grInt(c.pipelines.antinero.n_vats)} Anti-nero contractors and {grInt(
				c.pipelines.dase.n_vats
			)} co-op-side entities ({grInt(c.pipelines.dase_n_coops)} of them curated co-operatives), and not
			one ΑΦΜ appears on both sides.
		</p>
	</div>
</div>

<style>
	.band {
		background: var(--paper);
		padding: var(--sp-8) 0 var(--sp-6);
	}
	.inner {
		width: min(1152px, 92vw);
		margin: 0 auto;
	}
	.note {
		margin: var(--sp-3) 0 0;
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
	}
</style>
