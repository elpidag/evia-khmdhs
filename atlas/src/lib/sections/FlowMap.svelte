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
	import { page } from '$app/state';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import FlowArcs from '$lib/maps/FlowArcs.svelte';
	import OriginSplit from '$lib/sections/OriginSplit.svelte';
	import Bipartite from '$lib/sections/Bipartite.svelte';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
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
		/** the second LENS — «by company»: contractor ↔ work-region links
		 *  (the former WHO REACHES WHERE frame, user 2026-08-21) */
		edges?: { vat: string; pe: string; n: number; eur: number }[];
		contractors?: Record<string, { name: string; home_pe: string | null; eur: number }>;
	}
	let { flows, centroids, origins = [], flowsYearly = [], edges = [], contractors = {} }: Props = $props();

	let flowFocus = $state<string | null>(null);
	const short = (pe: string) => peEn(pe);

	// the lens: by region (map) or by company (the two lists) — a URL param
	// like the allocation maps' view, so it travels in a permalink
	const lens = $derived(page.url.searchParams.get('flows') === 'company' ? 'company' : 'region');
	let bipSel = $state<{ kind: 'vat' | 'pe'; id: string } | null>(null);
	// the focus is SHARED between the lenses: a unit focused on the map is the
	// region selected in the lists, a company selected in the lists focuses
	// the map on its home region (user, 2026-08-21)
	let lastLens = $state<'region' | 'company'>('region');
	$effect(() => {
		if (lens === lastLens) return;
		const from = lastLens;
		lastLens = lens;
		if (lens === 'company') {
			if (flowFocus) bipSel = { kind: 'pe', id: flowFocus };
		} else if (from === 'company' && bipSel) {
			const pe = bipSel.kind === 'pe' ? bipSel.id : (contractors[bipSel.id]?.home_pe ?? null);
			if (pe && centroids[pe]) focusRegion(pe);
		}
	});
	// the company lens explains itself; its one instruction rides in the ⓘ
	// beside COMPANIES (user, 2026-08-21)
	const companiesHow =
		'Click a contractor to light up every region it works in — regions below the cut are ' +
		'shuffled into the list — or a region for everyone working there. Edge width is the link’s €.';

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
		<div class="maplabel">
			{#if lens === 'company'}
				COMPANIES<Hint text={companiesHow} heading width="380px" />
			{:else}
				MAP
			{/if}
		</div>
		{#if lens === 'region' && flowFocus}
			<button class="reset" onclick={() => focusRegion(null)} title="Back to all of Greece (Esc)">
				✕ {peEn(flowFocus)} · all of Greece
			</button>
		{:else if lens === 'company' && bipSel}
			<button class="reset" onclick={() => (bipSel = null)} title="Clear the selection">
				✕ {bipSel.kind === 'pe' ? peEn(bipSel.id) : (contractors[bipSel.id]?.name ?? bipSel.id)} · all
			</button>
		{/if}
	</div>
	<SegmentToggle
		param="flows"
		fallback="region"
		options={[
			{ value: 'region', label: 'by region' },
			{ value: 'company', label: 'by company' }
		]}
	/>
</div>

{#if lens === 'company'}
	<!-- the company lens: the same even-split flows, broken down to the firms
	     that carry them — two linked lists, capped to the map's height; no
	     key strip (user: self-explanatory), the instruction in the ⓘ -->
	<div class="bip">
		<Bipartite {edges} {contractors} bind:selected={bipSel} />
	</div>
{:else}
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
		<!-- the same frame as each ALLOCATION OF FUNDING map: 640×620, the same
		     view, half the content width (user, 2026-08-21) -->
		<PaperMap
			width={640}
			height={620}
			view={{ center: [23.8305, 38.3566], k: 1.08 }}
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
				<!-- the same three symbols as the map's key, in the same order
				     (user, 2026-08-21: the squares read as the opposite) -->
				<li><i class="line solid"></i>firms based elsewhere → works in {short(flowFocus)}</li>
				<li><i class="line dash"></i>{short(flowFocus)} firms → works elsewhere</li>
				<li><i class="dot ring"></i>money that stays in {short(flowFocus)}</li>
			{:else}
				<!-- dark = out-of-region, exactly as the map's ramp reads (user) -->
				<li><i class="sq ink"></i>won by out-of-region firms</li>
				<li><i class="sq grey"></i>won by local firms</li>
				{#if origins.some((o) => o.unknown_eur > 0)}
					<!-- every in-scope contractor has a located base today (0 €
					     unresolved); the entry returns only if that changes -->
					<li><i class="sq hatch"></i>unresolved base</li>
				{/if}
			{/if}
		</ul>
		{#if flowFocus}
			<h3>{peEn(flowFocus)}</h3>
		{/if}
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
{/if}

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
	/* two equal columns, like the allocation maps' twin grid — the map is
	   then exactly the size of each of those maps */
	.flow-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
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
	/* the row marker is the map's own symbol for that flow — a solid
	   stroke reaching in, a dashed stroke reaching out, the ringed dot for
	   the money that stays (user, 2026-08-21: mirror the map's key) */
	i.dir {
		display: inline-block;
		width: 1.1rem;
		height: 0;
		border-top: 1.5px solid #111111;
		margin-right: 5px;
		vertical-align: 3px;
	}
	i.dir.out {
		border-top-style: dashed;
	}
	i.dir.local {
		width: 0.6rem;
		height: 0.6rem;
		border: 1.2px solid #111111;
		border-radius: 50%;
		background: #ffffff;
		vertical-align: -1px;
		box-sizing: border-box;
	}
	.chip {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	/* the company lens sits in the map's height and scrolls inside it */
	.bip {
		max-height: 720px;
		overflow-y: auto;
		padding-right: 4px;
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
