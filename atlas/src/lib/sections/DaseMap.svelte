<script lang="ts">
	/**
	 * ALLOCATION OF FUNDING on /dase — the Anti-nero duo one dataset over
	 * (user, DATA_DECISIONS 2026-08-24): the same money seen twice, by WHERE
	 * THE WORK IS (the awarding forest service's Regional Unit) and by WHERE
	 * THE CO-OPERATIVE IS SEATED (its registered office).
	 *
	 * Both maps share ONE colour scale, so a region's tone means the same
	 * amount on either side, and both drill: clicking a work region shows
	 * which regions' co-ops earned there (the seat map keeps only their
	 * money), clicking a seat region shows where that region's co-ops
	 * worked. The state lives in `?focus=works:Π.Ε. …|seats:Π.Ε. …` so a
	 * drilled view travels in a link.
	 */
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { makeChoro, spreadOverlaps, RAMP_DASE } from '$lib/maps/useGeo';
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import { eurShort, grInt, pct } from '$lib/transforms/format';
	import type { DaseAllocation } from '$lib/api';

	let { data }: { data: DaseAllocation } = $props();

	// the fixed frame every map on this section (and the Anti-nero duo)
	// uses — without it the pair centred and zoomed differently from the
	// MAP frame below (user, 2026-08-24)
	const MAP_VIEW: { center: [number, number]; k: number } = {
		center: [23.8305, 38.3566],
		k: 1.08
	};

	// the ΔΑΣΕ green ramp — the dataset's own hue, light → dark

	type Side = 'works' | 'seats';
	const focus = $derived.by(() => {
		const m = (page.url.searchParams.get('focus') ?? '').match(/^(works|seats):(.+)$/);
		return m ? { side: m[1] as Side, pe: m[2] } : null;
	});
	function setFocus(side: Side, pe: string | null) {
		const u = new URL(page.url);
		if (pe) u.searchParams.set('focus', `${side}:${pe}`);
		else u.searchParams.delete('focus');
		goto(u, { replaceState: true, noScroll: true, keepFocus: true });
	}

	const workBase = $derived(new Map(data.work_regions.map((r) => [r.pe, r])));
	const seatBase = $derived(new Map(data.seat_regions.map((r) => [r.pe, r])));

	/** the € each map paints — full totals, or, while drilled, only the
	 *  money that flows to/from the focused region */
	const workValues = $derived.by(() => {
		if (focus?.side !== 'seats') return new Map([...workBase].map(([pe, r]) => [pe, r.eur]));
		const m = new Map<string, number>();
		for (const f of data.flows) if (f.from === focus.pe) m.set(f.to, (m.get(f.to) ?? 0) + f.eur);
		return m;
	});
	const seatValues = $derived.by(() => {
		if (focus?.side !== 'works') return new Map([...seatBase].map(([pe, r]) => [pe, r.eur]));
		const m = new Map<string, number>();
		for (const f of data.flows) if (f.to === focus.pe) m.set(f.from, (m.get(f.from) ?? 0) + f.eur);
		return m;
	});

	// ONE shared scale across both maps and both states, so a tone is
	// comparable everywhere on the frame
	const sharedMax = $derived(
		Math.max(
			1,
			...data.work_regions.map((r) => r.eur),
			...data.seat_regions.map((r) => r.eur)
		)
	);
	// ONE scale, ALWAYS — never recomputed on drill. Rescaling recoloured
	// the very map the reader had just clicked, whose data had not changed
	// (user, 2026-08-24); with a fixed scale a tone means the same amount
	// in every state, and the flows read pale BECAUSE they are a fraction
	// of the whole — which is the point.
	const scaleMax = $derived(sharedMax);
	const choro = $derived(makeChoro(RAMP_DASE, scaleMax));

	const fmtPe = (pe: string) => ruLabel(pe);
	function workTip(pe: string) {
		const v = workValues.get(pe) ?? 0;
		const base = workBase.get(pe);
		if (!v && !base) return `<strong>${fmtPe(pe)}</strong><br>no forest co-op works`;
		if (focus?.side === 'seats')
			return `<strong>${fmtPe(pe)}</strong><br>${eurShort(v)} earned here by ${peEn(focus.pe)} co-ops`;
		return `<strong>${fmtPe(pe)}</strong><br>${eurShort(v)} · ${grInt(base?.n ?? 0)} contracts${
			base?.imported_eur ? `<br>${pct((base.imported_eur / (base.eur || 1)) * 100, 0)} won by co-ops from elsewhere` : ''
		}`;
	}
	function seatTip(pe: string) {
		const v = seatValues.get(pe) ?? 0;
		const base = seatBase.get(pe);
		if (!v && !base) return `<strong>${fmtPe(pe)}</strong><br>no forest co-ops`;
		if (focus?.side === 'works')
			return `<strong>${fmtPe(pe)}</strong><br>${eurShort(v)} earned in ${peEn(focus.pe)}`;
		return `<strong>${fmtPe(pe)}</strong><br>${eurShort(v)} · ${grInt(base?.n_coops ?? 0)} co-operatives${
			base?.exported_eur ? `<br>${eurShort(base.exported_eur)} of it earned in other regions` : ''
		}`;
	}

	/** the drilled region's own sentence — it ALWAYS speaks, including when
	 *  the region has nothing to show, because a blank map beside a silent
	 *  caption reads as a broken chart (user, 2026-08-24) */
	const drillNote = $derived.by(() => {
		if (!focus) return null;
		const where = peEn(focus.pe);
		if (focus.side === 'works') {
			const w = workBase.get(focus.pe);
			if (!w) return `No forest co-operative contracts were awarded in ${where}.`;
			const home = seatValues.get(focus.pe) ?? 0;
			const away = [...seatValues.entries()]
				.filter(([pe]) => pe !== focus.pe)
				.sort((a, b) => b[1] - a[1]);
			const lead = `${where} received ${eurShort(w.eur)} over ${grInt(w.n)} contracts.`;
			if (!away.length)
				return `${lead} All of it went to co-operatives seated there — none came from another regional unit.`;
			return `${lead} ${
				home ? `${eurShort(home)} of it went to co-operatives seated there` : 'None of it went to co-operatives seated there'
			}; the largest share from elsewhere came from ${peEn(away[0][0])} (${eurShort(away[0][1])}).`;
		}
		const s = seatBase.get(focus.pe);
		if (!s) return `No forest co-operatives in this dataset are seated in ${where}.`;
		const to = [...workValues.entries()].sort((a, b) => b[1] - a[1]);
		const away = s.exported_eur ?? 0;
		const lead = `The ${grInt(s.n_coops)} co-operative${s.n_coops === 1 ? '' : 's'} seated in ${where} earned ${eurShort(s.eur)}`;
		if (!away) return `${lead}, all of it in ${where} itself.`;
		const elsewhere = to.filter(([pe]) => pe !== focus.pe);
		return `${lead}, ${eurShort(away)} of it outside ${where}${
			elsewhere.length ? ` — most in ${peEn(elsewhere[0][0])} (${eurShort(elsewhere[0][1])})` : ''
		}.`;
	});

	/** the co-operatives that worked in the drilled work region, each at its
	 *  registered office — the drill's answer to «who came here» (user,
	 *  2026-08-24). A region's colour cannot say which co-op it was; a dot at
	 *  the seat can, and it is the Anti-nero maps' own convention. */
	const drillDots = $derived.by(() => {
		if (focus?.side !== 'works') return [];
		const pts = new Map(data.coop_points.map((p) => [p.vat, p]));
		const rows = data.region_coops
			.filter((r) => r.pe === focus.pe)
			.map((r) => {
				const p = pts.get(r.vat);
				return p ? { ...p, eur: r.eur, n: r.n } : null;
			})
			.filter((x): x is NonNullable<typeof x> => x !== null);
		return spreadOverlaps(rows, 0.05);
	});
	const dotMax = $derived(Math.max(1, ...drillDots.map((d) => d.eur)));
	/** area ∝ €, like the awarding-unit circles of the MAP frame below */
	const dotR = (d: { eur: number }) => 3 + 9 * Math.sqrt(d.eur / dotMax);

	// what a click does is said ONCE, in the MAP ⓘ — the Anti-nero convention
</script>

{#snippet rampKey(maxLabel: string)}
	<!-- 0 · [white + eight swatches, one hairline round the bar] · max —
	     the Anti-nero maps' key, in this dataset's green -->
	<span class="rampkey">
		<span>0</span><span class="swatches"><i class="empty"></i>{#each RAMP_DASE as c (c)}<i
					style:background={c}
				></i>{/each}</span><span>{maxLabel}</span>
	</span>
{/snippet}

<div class="alloc">
	<div class="bar">
		<div class="maplabel">MAP</div>
		{#if focus}
			<button class="reset" onclick={() => setFocus(focus.side, null)}
				title="Back to all of Greece (Esc)">✕ {peEn(focus.pe)} · all of Greece</button
			>
		{/if}
	</div>

	<div class="twin">
		<div class="panel">
			<!-- one key strip per map, right above it; its first row names what
			     the map is BY — never a heading of our own invention -->
			<ul class="mapkey">
				<li class="lbl">
					by the area of the forest service that awarded the contract
				</li>
				<li class="ramp">
					{@render rampKey(eurShort(scaleMax))}
					<span
						>{focus?.side === 'seats'
							? `€ earned here by ${peEn(focus.pe)} co-operatives`
							: '€ of contracts'}</span
					>
				</li>
			</ul>
			<PaperMap
				splitTips
				view={MAP_VIEW}
				focusZoom={false}
				colorOf={(pe) => choro(workValues.get(pe) ?? 0)}
				tipOf={workTip}
				onRegionClick={(pe) =>
					setFocus('works', focus?.side === 'works' && focus.pe === pe ? null : pe)}
				onEmptyClick={() => setFocus('works', null)}
				onEscape={() => setFocus('works', null)}
				focusPe={focus?.side === 'works' ? focus.pe : null}
			/>
		</div>

		<div class="panel">
			<ul class="mapkey">
				<li class="lbl">
					by the registered office of the co-operative that signed it
				</li>
				{#if focus?.side === 'works'}
					<li><i class="dot"></i>a co-operative that worked in {peEn(focus.pe)}</li>
					<li class="sub">circle area = € it earned there</li>
				{:else}
					<li class="ramp">
						{@render rampKey(eurShort(scaleMax))}
						<span>€ earned — a jointly signed contract split evenly</span>
					</li>
				{/if}
			</ul>
			<PaperMap
				splitTips
				view={MAP_VIEW}
				focusZoom={false}
				colorOf={(pe) =>
					focus?.side === 'works' ? 'var(--land-empty)' : choro(seatValues.get(pe) ?? 0)}
				tipOf={seatTip}
				onRegionClick={(pe) =>
					setFocus('seats', focus?.side === 'seats' && focus.pe === pe ? null : pe)}
				onEmptyClick={() => setFocus('seats', null)}
				onEscape={() => setFocus('seats', null)}
				focusPe={focus?.side === 'seats' ? focus.pe : null}
			>
				{#snippet overlay(ctx)}
					{#if drillDots.length}
						<DotLayer
							{ctx}
							points={drillDots}
							r={(p) => dotR(p as unknown as { eur: number })}
							fillOf={() => 'var(--c-dase)'}
							stroke="#1c4a34"
							hrefOf={(p) => `/dase/coop/${(p as unknown as { vat: string }).vat}`}
							tipOf={(p) => {
								const d = p as unknown as {
									name?: string | null;
									place?: string | null;
									eur: number;
									n: number;
								};
								return `<strong>${d.name ?? 'co-operative'}</strong><br>${eurShort(d.eur)} · ${grInt(d.n)} contract${d.n === 1 ? '' : 's'} in ${peEn(focus!.pe)}${d.place ? `<br>seat: ${d.place}` : ''}`;
							}}
						/>
					{/if}
				{/snippet}
			</PaperMap>
		</div>
	</div>

	{#if drillNote}
		<p class="note">{drillNote}</p>
	{/if}
</div>

<style>
	.alloc {
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
	}
	/* the toolbar above the maps — the Anti-nero .bar, one dataset over */
	.bar {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
		margin-bottom: var(--sp-2);
	}
	.maplabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		color: var(--c-dase);
	}
	/* the drill's way out */
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
	.twin {
		display: grid;
		grid-template-columns: 1fr 1fr;
		/* the Anti-nero .twin's breather — NOT --sp-5, which is not in the
		   token scale (1/2/3/4/6/8/12) and collapsed the gap to zero,
		   gluing the maps and their key strips together (user, 2026-08-24) */
		gap: var(--sp-4);
	}
	@media (max-width: 900px) {
		.twin {
			grid-template-columns: 1fr;
		}
	}
	.panel {
		min-width: 0;
	}
	/* the key strip — the Anti-nero/sponsored-works legend dress, with the
	   same FIXED height so both map rectangles sit at one level and never
	   move on drill */
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
	.mapkey li.lbl {
		flex-basis: 100%;
	}
	/* 0 · [white + eight swatches] · max — one hairline around the whole bar
	   in the legend's own text colour */
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
	/* the drill's dot swatch — the map's own mark, at its middle size */
	.mapkey i.dot {
		width: 11px;
		height: 11px;
		border-radius: 50%;
		background: var(--c-dase);
		border: 1px solid #1c4a34;
		flex: none;
		display: inline-block;
	}
	.mapkey li.sub {
		color: var(--ink-faint);
	}
	/* NO border here: the page's own `.dasep :global(.map)` rule already
	   gives every map on this section its hairline and green zoom buttons —
	   a second one round a wrapper drew a double edge (user, 2026-08-24) */
	.note {
		margin: var(--sp-2) 0 0;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
</style>
