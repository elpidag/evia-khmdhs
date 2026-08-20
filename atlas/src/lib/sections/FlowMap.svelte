<script lang="ts">
	/**
	 * Where the work-money goes against where the firms are: a choropleth of
	 * the share each regional unit's works pay to firms based elsewhere, with
	 * the biggest destinations' local/imported split beside it — one frame,
	 * the two views linked (user, 2026-08-20). Clicking a region on the map
	 * or a destination bar focuses both: the map draws only ITS flows —
	 * solid black for firms reaching in, dashed grey for its own firms
	 * reaching out, a ringed white dot for the money that stays — and the
	 * bars give way to that region's flow table.
	 */
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import FlowArcs from '$lib/maps/FlowArcs.svelte';
	import OriginSplit from '$lib/sections/OriginSplit.svelte';
	import { RAMP_WORKS } from '$lib/maps/useGeo';
	import { peEn } from '$lib/transforms/regions';
	import { eurShort } from '$lib/transforms/format';

	interface Flow {
		source_pe: string;
		target_pe: string;
		n_contracts: number;
		total_eur: number;
	}
	interface OriginRow {
		target_pe: string;
		total_eur: number;
		local_eur: number;
		imported_eur: number;
		unknown_eur: number;
	}
	interface Props {
		flows: Flow[];
		centroids: Record<string, [number, number]>;
		/** the biggest destinations' local/imported split — the resting
		 *  right-hand view; clicking a bar focuses the map on that region */
		origins?: OriginRow[];
	}
	let { flows, centroids, origins = [] }: Props = $props();

	let flowFocus = $state<string | null>(null);
	const short = (pe: string) => peEn(pe);

	const focusFlows = $derived(
		(flowFocus
			? flows.filter((f) => f.source_pe === flowFocus || f.target_pe === flowFocus)
			: flows.slice(0, 12)
		).toSorted((a, b) => b.total_eur - a.total_eur)
	);

	/** per WORK region: how much of its € is won by out-of-region firms */
	const perWork = $derived.by(() => {
		const m = new Map<string, { total: number; local: number; origins: Map<string, number> }>();
		for (const f of flows) {
			let w = m.get(f.target_pe);
			if (!w) m.set(f.target_pe, (w = { total: 0, local: 0, origins: new Map() }));
			w.total += f.total_eur;
			if (f.source_pe === f.target_pe) w.local += f.total_eur;
			else w.origins.set(f.source_pe, (w.origins.get(f.source_pe) ?? 0) + f.total_eur);
		}
		return m;
	});

	function importChoro(pe: string): string {
		const w = perWork.get(pe);
		if (!w || !w.total) return 'var(--land-empty)';
		const share = 1 - w.local / w.total; // linear 0–1 → 8 steps
		return RAMP_WORKS[Math.min(7, Math.floor(share * 8))];
	}
	function importTip(pe: string): string {
		const w = perWork.get(pe);
		if (!w || !w.total) return `<strong>${peEn(pe)}</strong><br>no Anti-nero works recorded`;
		const share = Math.round(100 * (1 - w.local / w.total));
		const top = [...w.origins.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3);
		return (
			`<strong>${peEn(pe)}</strong><br>${eurShort(w.total)} of works · ${share}% won by out-of-region firms` +
			(top.length
				? `<br><span style="color:var(--ink-faint)">top origins: ${top
						.map(([o, e]) => `${short(o)} (${eurShort(e)})`)
						.join(', ')}</span>`
				: '') +
			`<br><span style="color:var(--ink-faint)">click to see its flows</span>`
		);
	}
</script>

<div class="flow-grid">
	<PaperMap
		colorOf={flowFocus
			? (pe) => (pe === flowFocus ? '#e0e0e0' : 'var(--land-empty)')
			: importChoro}
		tipOf={flowFocus ? undefined : importTip}
		onRegionClick={(pe) => (flowFocus = flowFocus === pe ? null : pe)}
		focusPe={null}
	>
		{#snippet overlay(ctx)}
			{#if flowFocus && Object.keys(centroids).length}
				<FlowArcs {ctx} {flows} {centroids} focusPe={flowFocus} />
			{/if}
		{/snippet}
		{#snippet legend()}
			{#if flowFocus}
				<div>
					<i class="sw" style="background:#111111"></i> firms based elsewhere → works in {short(
						flowFocus
					)}
				</div>
				<div>
					<i class="sw dash"></i>
					{short(flowFocus)} firms → works elsewhere
				</div>
				<div><i class="sw round"></i> money that stays local</div>
				<div class="faint">arrows point home → work · width ∝ €</div>
			{:else}
				<div><strong>% of works won by out-of-region firms</strong></div>
				<div class="pct-swatches">
					{#each RAMP_WORKS as c (c)}<i style:background={c}></i>{/each}
				</div>
				<div class="pct-labels"><span>0%</span><span>100%</span></div>
			{/if}
		{/snippet}
	</PaperMap>
	<div class="flow-list">
		<h3>
			{#if flowFocus}
				{peEn(flowFocus)}
				<button class="btn-more" onclick={() => (flowFocus = null)}>✕ clear</button>
			{:else}
				Biggest destinations — who takes the money
			{/if}
		</h3>
		{#if !flowFocus && origins.length}
			<OriginSplit rows={origins} selected={flowFocus} onSelect={(pe) => (flowFocus = pe)} />
		{:else}
		<table>
			<tbody>
				{#each focusFlows as f, i (i)}
					{@const kind =
						f.source_pe === f.target_pe ? 'local' : f.target_pe === flowFocus ? 'in' : 'out'}
					<tr>
						<td>
							<small>
								{#if flowFocus}<i class="dir {kind}"></i>{/if}
								{short(f.source_pe)} → {short(f.target_pe)}
								{#if f.source_pe === f.target_pe}<span class="chip">local</span>{/if}
							</small>
						</td>
						<td class="num"><small>{f.n_contracts}×</small></td>
						<td class="num"><small>{eurShort(f.total_eur)}</small></td>
					</tr>
				{/each}
			</tbody>
		</table>
		{/if}
	</div>
</div>

<style>
	.flow-grid {
		display: grid;
		grid-template-columns: minmax(22rem, 1.4fr) 1fr;
		gap: var(--sp-4);
	}
	@media (max-width: 900px) {
		.flow-grid {
			grid-template-columns: 1fr;
		}
	}
	.flow-list h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
	}
	table {
		width: 100%;
		border-collapse: collapse;
	}
	td {
		padding: 2px 0;
		vertical-align: top;
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		padding-left: var(--sp-2);
	}
	i.sw {
		display: inline-block;
		width: 1rem;
		height: 3px;
		vertical-align: 3px;
		margin-right: 4px;
	}
	i.sw.round {
		width: 0.6rem;
		height: 0.6rem;
		border-radius: 50%;
		vertical-align: -1px;
		background: #ffffff;
		border: 1.5px solid #111111;
	}
	i.sw.dash {
		background: repeating-linear-gradient(90deg, #9a9a9a 0 5px, transparent 5px 9px);
	}
	.faint {
		color: var(--ink-faint);
	}
	.pct-swatches {
		display: flex;
		gap: 1px;
		margin-top: 2px;
	}
	.pct-swatches i {
		width: 1.1rem;
		height: 0.55rem;
		display: inline-block;
	}
	.pct-labels {
		display: flex;
		justify-content: space-between;
		color: var(--ink-soft);
	}
	i.dir {
		display: inline-block;
		width: 0.55rem;
		height: 0.55rem;
		border-radius: 50%;
		margin-right: 3px;
		vertical-align: -1px;
	}
	i.dir.in {
		background: #111111;
	}
	i.dir.out {
		background: #9a9a9a;
	}
	i.dir.local {
		background: #ffffff;
		border: 1.5px solid #111111;
	}
	.chip {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.btn-more {
		font: inherit;
		font-size: var(--fs-12);
		background: none;
		border: none;
		color: var(--ink-soft);
		cursor: pointer;
		padding: 0;
	}
</style>
