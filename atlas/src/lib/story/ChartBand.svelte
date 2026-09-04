<script lang="ts">
	/**
	 * A chart across the WHOLE PAGE, inside the narrative's flow (the author,
	 * 2026-09-04), in three kinds since the same evening:
	 *   state-funded — every contract of both programmes as a dot, after the
	 *                  paragraph that says the money reached a different
	 *                  population of contractors;
	 *   awarding     — the two AWARDING PROCESS diagrams, Anti-nero over the
	 *                  forest co-ops, after the sentence on the Ministry's
	 *                  central operating units;
	 *   signed       — EVERY CONTRACT, BY THE DAY IT WAS SIGNED, after the
	 *                  paragraph on the changing unit of forestry work.
	 * No title of its own for the dots (the author) — the caption line and
	 * the side labels say what it is; the other two carry the frames' titles.
	 *
	 * Mounted by the story page into each `[CHART: name]` marker's
	 * placeholder (`scripts/remark-tag-paragraphs.ts` turns the author's
	 * marker line into a `div.chartmark[data-chart]`); the placeholder is
	 * full-bleed — the page sets `--nar-left`, the narrative column's
	 * distance from the window's left edge, and `--page-w`, the window's
	 * width without the scrollbar — and this band sets its content at the
	 * site's 1152 px. The awarding diagrams read the two dataset pages' own
	 * payloads through the shared builders, so the story can never draw a
	 * different diagram from the pages.
	 */
	import { onMount } from 'svelte';
	import { apiGetCached, type ComparePayload, type DaseOverview } from '$lib/api';
	import StateFunded from '$lib/charts/StateFunded.svelte';
	import KindFlow from '$lib/charts/KindFlow.svelte';
	import KeyFindings from '$lib/sections/KeyFindings.svelte';
	import {
		antineroAwardingFlow,
		daseAwardingFlow,
		type UnitFlowPayload as UnitFlow
	} from '$lib/transforms/awardingFlows';
	import { grInt } from '$lib/transforms/format';

	type Kind = 'state-funded' | 'signed' | 'awarding';
	let { kind, c }: { kind: Kind; c: ComparePayload } = $props();

	let uf = $state.raw<UnitFlow | null>(null);
	let dov = $state.raw<DaseOverview | null>(null);
	onMount(() => {
		if (kind !== 'awarding') return;
		apiGetCached<UnitFlow>(fetch, '/api/antinero/unit-flow').then((v) => (uf = v));
		apiGetCached<DaseOverview>(fetch, '/api/dase/overview').then((v) => (dov = v));
	});
	const anti = $derived(uf ? antineroAwardingFlow(uf) : null);
	const coop = $derived(dov?.kind_mix ? daseAwardingFlow(dov.kind_mix) : null);
</script>

<div class="band">
	<div class="inner" class:wide={kind === 'awarding'}>
		{#if kind === 'state-funded'}
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
		{:else if kind === 'signed'}
			<KeyFindings {c} part="signed" />
		{:else}
			<div class="duo">
				<div class="one">
					<h3 class="tt">AWARDING PROCESS — ANTI-NERO PROGRAMME</h3>
					{#if anti && uf}
						<KindFlow
							nodes={anti.nodes}
							links={anti.links}
							height={620}
							headings={['awarding body', 'operating units', 'contractors']}
							marginLeft={120}
							marginRight={400}
							columnX={[0.15, 0.42, 0.7]}
							wrapLeft={18}
							wrapMid={28}
						/>
						<p class="note">
							One awarding body — the Ministry of Environment and Energy — acting through {grInt(
								uf.n_units
							)} units of its own central administration; none of the forest services that supervise
							the works on the ground awards a contract itself. Awarding body and operating units as
							recorded in ΚΗΜΔΗΣ; ribbon width = stated net €.
						</p>
					{:else}
						<div class="skeleton" style="height: 620px"></div>
					{/if}
				</div>
				<div class="one">
					<h3 class="tt">AWARDING PROCESS — FOREST WORKERS' CO-OPERATIVES</h3>
					{#if coop && dov}
						<!-- half the band: narrower margins than the /dase frame's 340, the
						     co-op names still on one line at the right -->
						<KindFlow
							nodes={coop.nodes}
							links={coop.links}
							height={620}
							headings={['awarding bodies', 'operating units', 'contractors']}
							marginLeft={120}
							marginRight={400}
							columnX={[0.15, 0.42, 0.7]}
						/>
						<p class="note">
							{grInt(dov.kpis.n_orgs)} awarding bodies through {grInt(dov.kpis.n_units)} operating
							units. Bodies that ran the procurement through their own services share one middle
							node; the right column holds the biggest co-ops by €, the rest pooled into one node; a
							consortium contract counts once, at the co-op listed first.
						</p>
					{:else}
						<div class="skeleton" style="height: 660px"></div>
					{/if}
				</div>
			</div>
		{/if}
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
	/* the two awarding diagrams side by side (the author, 2026-09-04), on a
	   band as wide as the page allows */
	.inner.wide {
		width: min(1800px, 96vw);
	}
	.duo {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
		align-items: start;
	}
	@media (max-width: 1100px) {
		.duo {
			grid-template-columns: 1fr;
		}
	}
	.one {
		display: flex;
		flex-direction: column;
		gap: var(--sp-3);
	}
	.tt {
		margin: 0;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-13);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--ink);
		text-transform: uppercase;
	}
	.note {
		margin: var(--sp-3) 0 0;
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
	}
	.skeleton {
		background: var(--paper-2);
		border-radius: var(--radius);
	}
</style>
