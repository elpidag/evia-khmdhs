<script lang="ts">
	/**
	 * Where the work-money goes against where the firms are: a choropleth of
	 * the share each regional unit's works pay to firms based elsewhere, with
	 * the biggest destinations' local/imported split beside it — one frame,
	 * the two views linked (user, 2026-08-20). Clicking a region on the map
	 * or a destination bar focuses both: the map draws only ITS flows —
	 * solid black for firms reaching IN, dashed black for its own firms
	 * reaching OUT, open arrowheads at a fixed size so the stroke width
	 * alone carries the €, a ringed white dot for the money that stays — and
	 * the bars give way to that region's flow table.
	 *
	 * Dressed like the ALLOCATION OF FUNDING maps (user, 2026-08-21): the key
	 * is a strip ABOVE the map (never a box over it) with the «0 · bar · max»
	 * ramp, MAP + ⓘ carry the instructions, a «✕ <unit> · all of Greece»
	 * pill is the way out (Esc too), the place's card sits grey at the
	 * top-left in every state, an arc's card black at the bottom-left —
	 * hover shows, click holds — and the year control is a CUMULATIVE
	 * slider: the focused flows signed up to a year, not one year at a time.
	 */
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import FlowArcs from '$lib/maps/FlowArcs.svelte';
	import OriginSplit from '$lib/sections/OriginSplit.svelte';
	import Hint from '$lib/ui/Hint.svelte';
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
		/** the same flows per signature year — powers the focused view's
		 *  cumulative year slider (user, 2026-08-20 / 21) */
		flowsYearly?: (Flow & { year: string })[];
	}
	let { flows, centroids, origins = [], flowsYearly = [] }: Props = $props();

	let flowFocus = $state<string | null>(null);
	const short = (pe: string) => peEn(pe);

	const howToRead =
		'Each regional unit is coloured by the share of its works won by firms based elsewhere. ' +
		'Click a unit, or a bar on the right, to see its flows: solid arrows are firms based ' +
		'elsewhere reaching in, dashed arrows its own firms reaching out, the ringed dot the money ' +
		'that stays; width is the €. Hover an arrow for its card, click to hold it; the slider ' +
		'accumulates the flows signed up to a year; Esc or the pill go back to all of Greece.';

	const allYears = $derived([...new Set(flowsYearly.map((f) => f.year))].sort());
	// the CUMULATIVE year slider: index into allYears, the last = all years
	let yearIdx = $state<number | null>(null);
	const upToYear = $derived(
		yearIdx === null || yearIdx >= allYears.length - 1 ? null : allYears[yearIdx]
	);

	function focusRegion(pe: string | null) {
		flowFocus = pe;
		yearIdx = null; // a fresh region starts on all years
	}

	/** the flow set the focused arcs and table draw from — all years, or the
	 *  flows signed up to and including the slider's year, summed */
	const flowsShown = $derived.by(() => {
		if (!upToYear) return flows;
		const acc = new Map<string, Flow>();
		for (const f of flowsYearly) {
			if (f.year > upToYear) continue;
			const k = f.source_pe + '→' + f.target_pe;
			const cur = acc.get(k);
			if (cur) {
				cur.n_contracts += f.n_contracts;
				cur.total_eur += f.total_eur;
			} else {
				acc.set(k, {
					source_pe: f.source_pe,
					target_pe: f.target_pe,
					n_contracts: f.n_contracts,
					total_eur: f.total_eur
				});
			}
		}
		return [...acc.values()];
	});

	const focusFlows = $derived(
		(flowFocus
			? flowsShown.filter((f) => f.source_pe === flowFocus || f.target_pe === flowFocus)
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
	// the place's card: place · € of works · share — short and factual, in
	// every state (the instructions live in the ⓘ, as on the allocation maps)
	function importTip(pe: string): string {
		const w = perWork.get(pe);
		if (!w || !w.total) return `<strong>${peEn(pe)}</strong><br>no Anti-nero works recorded`;
		const share = Math.round(100 * (1 - w.local / w.total));
		return `<strong>${peEn(pe)}</strong><br>${eurShort(w.total)} of works · ${share}% won by out-of-region firms`;
	}
</script>

{#snippet rampKey(lo: string, hi: string)}
	<!-- the inline ramp key the user approved on the allocation maps: lo ·
	     [white + eight swatches, one hairline round the bar] · hi -->
	<span class="rampkey">
		<span>{lo}</span><span class="swatches"><i class="empty"></i>{#each RAMP_WORKS as c (c)}<i style:background={c}></i>{/each}</span><span
			>{hi}</span
		>
	</span>
{/snippet}

<div class="bar">
	<div class="barleft">
		<div class="maplabel">MAP<Hint text={howToRead} heading width="380px" /></div>
		{#if flowFocus}
			<button class="reset" onclick={() => focusRegion(null)} title="Back to all of Greece (Esc)">
				✕ {peEn(flowFocus)} · all of Greece
			</button>
		{/if}
	</div>
</div>

<div class="flow-grid">
	<div class="panel">
		<ul class="mapkey">
			{#if flowFocus}
				<li><i class="line solid"></i>firms based elsewhere → works in {short(flowFocus)}</li>
				<li><i class="line dash"></i>{short(flowFocus)} firms → works elsewhere</li>
				<li><i class="dot ring"></i>money that stays in {short(flowFocus)}</li>
				<li class="faint">arrows point home → work · width ∝ €</li>
			{:else}
				<li class="ramp">
					{@render rampKey('0%', '100%')}
					<span>share of each unit's works won by firms based elsewhere</span>
				</li>
			{/if}
		</ul>
		<PaperMap
			colorOf={flowFocus
				? (pe) => (pe === flowFocus ? '#e0e0e0' : 'var(--land-empty)')
				: importChoro}
			tipOf={importTip}
			splitTips
			onEscape={() => flowFocus && focusRegion(null)}
			onRegionClick={(pe) => focusRegion(flowFocus === pe ? null : pe)}
			focusPe={null}
		>
			{#snippet overlay(ctx)}
				{#if flowFocus && Object.keys(centroids).length}
					<FlowArcs {ctx} flows={flowsShown} {centroids} focusPe={flowFocus} />
				{/if}
			{/snippet}
		</PaperMap>
	</div>
	<div class="flow-list">
		<!-- the bars' key, in the same strip as the map's (user, 2026-08-21:
		     the right-hand legend must match the maps') -->
		<ul class="mapkey">
			{#if flowFocus}
				<li><i class="sq ink"></i>stays with {short(flowFocus)} firms</li>
				<li><i class="sq grey"></i>firms based elsewhere → works in {short(flowFocus)}</li>
				<li><i class="sq hollow"></i>{short(flowFocus)} firms → works elsewhere</li>
			{:else}
				<li><i class="sq ink"></i>won by local firms</li>
				<li><i class="sq grey"></i>won by out-of-region firms</li>
				{#if origins.some((o) => o.unknown_eur > 0)}
					<!-- every in-scope contractor has a located base today (0 €
					     unresolved); the entry returns only if that changes -->
					<li><i class="sq hatch"></i>unresolved base</li>
				{/if}
			{/if}
		</ul>
		<h3>
			{#if flowFocus}
				{peEn(flowFocus)}
			{:else}
				Destinations — who takes the money
			{/if}
		</h3>
		{#if flowFocus && allYears.length > 1}
			<!-- the cumulative year slider: flows signed up to and including
			     the chosen year; the right end is all years (user, 2026-08-21) -->
			<div class="years">
				<label>
					<span class="yearlbl">
						{#if upToYear}flows signed up to {upToYear}{:else}all years ({allYears[0]}–{allYears.at(-1)}){/if}
					</span>
					<input
						type="range"
						min="0"
						max={allYears.length - 1}
						step="1"
						value={yearIdx ?? allYears.length - 1}
						oninput={(e) => (yearIdx = Number((e.currentTarget as HTMLInputElement).value))}
						aria-label="Accumulate the flows up to a signature year"
					/>
				</label>
				<div class="ticks" aria-hidden="true">
					{#each allYears as y, i (y)}
						<span class:on={i === (yearIdx ?? allYears.length - 1)}>{y}</span>
					{/each}
				</div>
			</div>
			{#if upToYear && focusFlows.length === 0}
				<p class="empty">no flows touch {short(flowFocus)} up to {upToYear}</p>
			{/if}
		{/if}
		{#if !flowFocus && origins.length}
			<!-- every regional unit with works, biggest first; the list scrolls
			     beside the map (user, 2026-08-21: «why not all the regions?») -->
			<div class="scroll">
				<OriginSplit rows={origins} selected={flowFocus} onSelect={(pe) => focusRegion(pe)} showLegend={false} />
			</div>
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
	.bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--sp-2);
	}
	.barleft {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
	}
	.maplabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		color: var(--c-antinero);
	}
	/* the focus's way out — the allocation maps' pill */
	.reset {
		font: inherit;
		font-size: var(--fs-12);
		color: var(--ink-soft);
		background: var(--paper);
		border: 1px solid var(--ink-soft);
		border-radius: 999px;
		padding: 1px 10px;
		cursor: pointer;
	}
	.reset:hover {
		color: var(--ink);
		border-color: var(--ink);
	}
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
	/* the key strip — the allocation maps' dress (sponsored-works .stkey) */
	.mapkey {
		list-style: none;
		margin: 0 0 var(--sp-2);
		height: 4.3rem;
		overflow: visible;
		position: relative;
		z-index: 2;
		box-sizing: border-box;
		padding: var(--sp-2) var(--sp-3);
		background: #f2f2f2;
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		align-content: center;
		gap: 4px var(--sp-6, 1.5rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.mapkey li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.mapkey li.faint {
		color: var(--ink-faint);
	}
	.rampkey {
		display: inline-flex;
		align-items: center;
		flex: none;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.rampkey > span:not(.swatches) {
		margin: 0 5px;
	}
	.rampkey .swatches {
		display: inline-flex;
		flex: none;
		border: 1px solid var(--ink-soft);
	}
	.rampkey i {
		display: inline-block;
		flex: none;
		width: 13px;
		height: 10px;
	}
	.rampkey i.empty {
		background: var(--land-empty);
	}
	/* the map's own strokes in the key: a thin line, a dashed line whose
	   gaps are a proportion of its width, a ringed dot */
	.mapkey i.line {
		display: inline-block;
		width: 1.4rem;
		height: 0;
		border-top: 1.5px solid #111111;
		flex: none;
	}
	.mapkey i.line.dash {
		border-top-style: dashed;
	}
	/* the bars' swatches — the same colours the bars use */
	.mapkey i.sq {
		display: inline-block;
		width: 12px;
		height: 12px;
		border-radius: 2px; /* the sponsored-works legends' swatch (user) */
		flex: none;
	}
	.mapkey i.sq.ink {
		background: var(--ink);
	}
	.mapkey i.sq.grey {
		background: #c9c9c9;
	}
	.mapkey i.sq.hatch {
		background: repeating-linear-gradient(45deg, #ececec 0 3px, #f8f8f8 3px 6px);
	}
	.mapkey i.sq.hollow {
		background: #ffffff;
		border: 1.5px solid var(--ink);
		box-sizing: border-box;
	}
	.mapkey i.dot.ring {
		display: inline-block;
		width: 0.6rem;
		height: 0.6rem;
		border-radius: 50%;
		background: #ffffff;
		border: 1.2px solid #111111;
		flex: none;
	}
	.flow-list h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
	}
	/* the full destination list scrolls within the map's height */
	.scroll {
		max-height: 540px;
		overflow-y: auto;
		padding-right: 4px;
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
	/* the row marker repeats the key's squares — the bars' own palette:
	   black = stays with local firms, light grey = won by firms based
	   elsewhere, hollow = the unit's own firms winning elsewhere (user,
	   2026-08-21: the circles did not read, nor connect to the bars) */
	i.dir {
		display: inline-block;
		width: 0.6rem;
		height: 0.6rem;
		border-radius: 2px;
		margin-right: 4px;
		vertical-align: -1px;
		box-sizing: border-box;
	}
	i.dir.local {
		background: var(--ink);
	}
	i.dir.in {
		background: #c9c9c9;
	}
	i.dir.out {
		background: #ffffff;
		border: 1.5px solid var(--ink);
	}
	.chip {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	/* the cumulative year slider */
	.years {
		margin: 0 0 var(--sp-2);
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.years label {
		display: block;
	}
	.yearlbl {
		display: block;
		margin-bottom: 2px;
	}
	.years input[type='range'] {
		width: 100%;
		accent-color: #111111; /* black on the Anti-nero page, never the warm ink (user) */
		margin: 0;
	}
	.ticks {
		display: flex;
		justify-content: space-between;
		font-variant-numeric: tabular-nums;
		color: var(--ink-faint);
	}
	.ticks span.on {
		color: #111111;
		font-weight: 700;
	}
	.empty {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
</style>
