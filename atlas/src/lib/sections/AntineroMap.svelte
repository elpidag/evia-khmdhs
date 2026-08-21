<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import { authEn } from '$lib/transforms/names';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { AntineroMapPayload } from '$lib/api';
	import DotLayer, { type DotPoint } from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, makeChoro, spreadOverlaps, loadPe } from '$lib/maps/useGeo';
	import { geoContains } from 'd3-geo';
	import { onMount } from 'svelte';
	import type { FeatureCollection, MultiPolygon } from 'geojson';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import Hint from '$lib/ui/Hint.svelte';

	let { data }: { data: AntineroMapPayload } = $props();

	// ---- URL state -----------------------------------------------------
	const view = $derived(page.url.searchParams.get('view') === 'points' ? 'points' : 'money');
	const focusRaw = $derived(page.url.searchParams.get('focus'));
	const focus = $derived.by(() => {
		const m = focusRaw?.match(/^(works|home):(.+)$/);
		return m ? { side: m[1] as 'works' | 'home', pe: m[2] } : null;
	});

	// the SELECTED contract (item 5, user 2026-08-21): a URL param like the
	// drill, so it survives the € / dots toggle and travels in a permalink;
	// it only counts while a map is drilled and the contract is known
	const selRaw = $derived(page.url.searchParams.get('sel'));
	// a selected CONTRACTOR (user, 2026-08-21: a click on a contractor dot
	// selects it — its card held, its contracts lit on the left — instead of
	// leaving for its page; the page is the card's link). One selection at a
	// time: selecting one kind clears the other.
	const selvRaw = $derived(page.url.searchParams.get('selv'));
	function setSelected(ref: string | null) {
		const url = new URL(page.url);
		if (ref) url.searchParams.set('sel', ref);
		else url.searchParams.delete('sel');
		url.searchParams.delete('selv');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}
	function setSelectedVat(vat: string | null) {
		const url = new URL(page.url);
		if (vat) url.searchParams.set('selv', vat);
		else url.searchParams.delete('selv');
		url.searchParams.delete('sel');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}
	function clearSelection() {
		if (selRaw || selvRaw) setSelected(null);
	}
	function setFocus(side: 'works' | 'home', pe: string | null) {
		const url = new URL(page.url);
		if (pe) url.searchParams.set('focus', `${side}:${pe}`);
		else url.searchParams.delete('focus');
		url.searchParams.delete('sel'); // a new drill starts unselected
		url.searchParams.delete('selv');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	// the MAP ⓘ (user's text, 2026-08-20); the split explanation sits on the
	// frame title's own ⓘ
	const howToRead =
		'Click a regional unit to explore its contracts, the forest authorities ' +
		'responsible for them and the contractors to which they were awarded.';

	// ---- lookups -------------------------------------------------------
	const vatHome = $derived(
		new Map(data.contractor_points.points.map((p) => [p.vat, p.pe]))
	);
	const workBase = $derived(new Map(data.work_regions.map((r) => [r.pe, r])));
	const homeBase = $derived(new Map(data.home_regions.map((r) => [r.pe, r])));

	// contracts touching a work Π.Ε. / held by contractors homed in a Π.Ε.
	const focusContracts = $derived.by(() => {
		if (!focus) return [];
		if (focus.side === 'works') {
			return data.contracts
				.filter((c) => c.regions.some((r) => r.pe === focus.pe))
				.map((c) => ({
					...c,
					share: c.regions.filter((r) => r.pe === focus.pe).reduce((s, r) => s + r.split_eur, 0)
				}))
				.sort((a, b) => b.share - a.share);
		}
		return data.contracts
			.filter((c) => c.contractors.some((ct) => vatHome.get(ct.vat) === focus.pe))
			.map((c) => {
				const nHome = c.contractors.filter((ct) => vatHome.get(ct.vat) === focus.pe).length;
				return { ...c, share: (c.eff_eur * nHome) / c.contractors.length };
			})
			.sort((a, b) => b.share - a.share);
	});

	const drillContractors = $derived.by(() => {
		if (!focus) return [];
		const agg = new Map<string, { vat: string; name: string; eur: number; n: number }>();
		for (const c of focusContracts) {
			for (const ct of c.contractors) {
				if (focus.side === 'home' && vatHome.get(ct.vat) !== focus.pe) continue;
				const a = agg.get(ct.vat) ?? { vat: ct.vat, name: ct.name, eur: 0, n: 0 };
				a.eur += c.share / (focus.side === 'home'
					? c.contractors.filter((x) => vatHome.get(x.vat) === focus.pe).length
					: c.contractors.length);
				a.n += 1;
				agg.set(ct.vat, a);
			}
		}
		return [...agg.values()].sort((a, b) => b.eur - a.eur);
	});

	// when drilled, the OTHER map recolours to the drill population
	const workValues = $derived.by(() => {
		if (focus?.side !== 'home') return new Map([...workBase].map(([pe, r]) => [pe, r.split_eur]));
		const m = new Map<string, number>();
		for (const c of focusContracts)
			for (const r of c.regions) {
				const nHome = c.contractors.filter((x) => vatHome.get(x.vat) === focus.pe).length;
				m.set(r.pe, (m.get(r.pe) ?? 0) + (r.split_eur * nHome) / c.contractors.length);
			}
		return m;
	});
	const homeValues = $derived.by(() => {
		if (focus?.side !== 'works')
			return new Map([...homeBase].map(([pe, r]) => [pe, r.split_eur]));
		const m = new Map<string, number>();
		for (const c of focusContracts)
			for (const ct of c.contractors) {
				const pe = vatHome.get(ct.vat);
				if (pe) m.set(pe, (m.get(pe) ?? 0) + c.share / c.contractors.length);
			}
		return m;
	});

	// ONE sqrt ramp on both maps, shared max (the classed scale of the same
	// day was rejected by the user — «former ways were far nicer»)
	const sharedMax = $derived(
		Math.max(
			...data.work_regions.map((r) => r.split_eur),
			...data.home_regions.map((r) => r.split_eur)
		)
	);
	const workChoro = $derived(makeChoro(RAMP_WORKS, sharedMax));
	const homeChoro = $derived(makeChoro(RAMP_WORKS, sharedMax));

	// ---- points view ---------------------------------------------------
	// Country level: contract-COUNT choropleth on the left (no dots there),
	// contractor dots on the right — the webui convention. Dots appear on
	// the left only when drilled.
	const refsByPe = $derived.by(() => {
		const m = new Map<string, Set<string>>();
		for (const p of data.contract_points) {
			let s = m.get(p.pe);
			if (!s) m.set(p.pe, (s = new Set()));
			s.add(p.ref);
		}
		return m;
	});

	const maxRegionCount = $derived(
		Math.max(...[...refsByPe.values()].map((s) => s.size), 1)
	);
	const countChoro = $derived(makeChoro(RAMP_WORKS, maxRegionCount));

	// per-contract hue grouping for multi-authority contracts (drilled view)
	const authCount = $derived.by(() => {
		const m = new Map<string, number>();
		for (const p of data.contract_points) m.set(p.ref, (m.get(p.ref) ?? 0) + 1);
		return m;
	});
	const SINGLE_FILL = '#6b6b6b';
	const DRILL_STROKE = '#333333';

	// the coarse Π.Ε. layer (the same memoised load PaperMap uses), so the
	// de-overlap spread can keep every dot ON LAND — five seats share Λίμνη's
	// waterfront point, nine share Μεγ. Αλεξάνδρου 27 in Καβάλα (user, 2026-08-21)
	let land = $state.raw<FeatureCollection<MultiPolygon> | null>(null);
	onMount(() => {
		loadPe(fetch).then((fc) => (land = fc as unknown as FeatureCollection<MultiPolygon>));
	});
	const onLand = $derived((lat: number, lon: number): boolean =>
		!land || land.features.some((f) => geoContains(f, [lon, lat]))
	);

	const contractDots = $derived.by(() => {
		let pts = data.contract_points;
		if (focus?.side === 'works') pts = pts.filter((p) => p.pe === focus.pe);
		else if (focus?.side === 'home')
			pts = pts.filter((p) => focusContracts.some((c) => c.ref === p.ref));
		// the zoomed map needs far less de-overlap spread than country level
		return spreadOverlaps(
			pts as unknown as DotPoint[],
			focus?.side === 'works' ? 0.012 : 0.034,
			onLand
		);
	});
	const contractorDots = $derived(
		spreadOverlaps(
			(focus?.side === 'home'
				? data.contractor_points.points.filter((p) => p.pe === focus.pe)
				: focus
					? data.contractor_points.points.filter((p) =>
							drillContractors.some((c) => c.vat === p.vat)
						)
					: data.contractor_points.points) as unknown as DotPoint[],
			focus?.side === 'home' ? 0.01 : 0.02,
			onLand
		)
	);
	// how precisely the registered-office dots are placed: the street address,
	// or — where the geocoder could not place the street — the centre of the
	// municipality (drawn dashed and lighter, as the sponsored-works map does)
	const whyCentre =
		'The registered office is read from each contractor\'s own signed contract. For these dots ' +
		'the geocoder could not place the stated address on a street — it is a kilometre marker on ' +
		'a road, a rural locality or field lot, or a street OpenStreetMap does not know — so the ' +
		'dot sits at the centre of the settlement the document names, and is drawn dashed.';


	// every contract dot is ONE grey (user, 2026-08-21 — the legend must show
	// the colour the map uses); which dots belong to one contract is shown by
	// the dashed seat links on hover and by the selection, never by hue

	// Hovering a multi-authority contract's dot links ALL its authority
	// seats with dashed lines in the contract's colour — off-region seats
	// at their true spots, so a line running off-frame means the contract
	// spans beyond this Π.Ε.
	let hoverRef = $state<string | null>(null);
	const contractByRef = $derived(new Map(data.contracts.map((c) => [c.ref, c])));
	// the SELECTED contract (click, user 2026-08-20): it keeps its links and
	// its card, lights its contractor, and a multi-region one widens the map
	// — nothing moves the map on hover any more
	const selectedRef = $derived(
		selRaw && focus && contractByRef.has(selRaw) ? selRaw : null
	);
	const activeRef = $derived(selectedRef ?? hoverRef);
	// the two maps talk to each other (user, 2026-08-20): hovering a contract
	// dot lights its contractor(s) on the right; hovering a contractor dot
	// lights that firm's contracts on the left
	let hoverVat = $state<string | null>(null);
	const selectedVat = $derived(
		selvRaw && focus && data.contractor_points.points.some((p) => p.vat === selvRaw)
			? selvRaw
			: null
	);
	const activeVat = $derived(selectedVat ?? hoverVat);
	const hotVats = $derived(
		activeRef
			? new Set((contractByRef.get(activeRef)?.contractors ?? []).map((ct) => ct.vat))
			: new Set<string>()
	);
	// the selected contract's firm(s): the one card the right map HOLDS
	// (hover highlights across the maps but pins nothing — user, 2026-08-21)
	const selectedVats = $derived(
		selectedRef
			? new Set((contractByRef.get(selectedRef)?.contractors ?? []).map((ct) => ct.vat))
			: new Set<string>()
	);
	const hotRefs = $derived(
		activeVat
			? new Set(
					data.contracts
						.filter((c) => c.contractors.some((ct) => ct.vat === activeVat))
						.map((c) => c.ref)
				)
			: new Set<string>()
	);
	// a SELECTED multi-region contract refits the drilled map to every
	// region it touches (its work regions + every authority seat); hover
	// never moves the map
	const fitLive = $derived.by(() => {
		if (!selectedRef || !focus || focus.side !== 'works') return null;
		const pes = new Set<string>([focus.pe]);
		for (const r of contractByRef.get(selectedRef)?.regions ?? []) pes.add(r.pe);
		for (const p of data.contract_points) if (p.ref === selectedRef) pes.add(p.pe);
		return pes.size > 1 ? [...pes] : null;
	});
	function hoverContract(ref: string) {
		hoverRef = ref;
	}
	function unhoverContract() {
		hoverRef = null;
	}
	function clickContract(ref: string) {
		setSelected(selectedRef === ref ? null : ref);
	}
	// the dashed seat-links draw for the hovered contract — or, when the
	// hover is on a contractor dot on the right, for every contract of that
	// firm (the reverse direction, user 2026-08-20)
	const linkRefs = $derived(activeRef ? new Set([activeRef]) : hotRefs);
	const hoverSegments = $derived.by(() => {
		if (!linkRefs.size || focus?.side !== 'works') return [];
		const segs: [[number, number], [number, number]][] = [];
		for (const ref of linkRefs) {
			const anchors: [number, number][] = [];
			for (const p of contractDots)
				if (p.ref === ref) anchors.push([p.lat2 ?? p.lat, p.lon2 ?? p.lon]);
			for (const p of data.contract_points)
				if (p.ref === ref && p.pe !== focus.pe) anchors.push([p.lat, p.lon]);
			for (let i = 0; i < anchors.length; i++)
				for (let j = i + 1; j < anchors.length; j++) segs.push([anchors[i], anchors[j]]);
		}
		return segs;
	});
	const hoverColor = SINGLE_FILL;

	// ---- tooltips ------------------------------------------------------
	// the € ramp's tick values at the boundaries of swatches 0/2/4/6/8 of the
	// sqrt scale (makeChoro): v = max · (k/8)²

	// region cards: place · count · € — short and factual; what the € means
	// and what a click does is said once, in the legend and its ⓘ
	function workTip(pe: string): string {
		const r = workBase.get(pe);
		if (!r) return `<strong>${peEn(pe)}</strong><br>no works recorded`;
		return `<strong>${peEn(pe)}</strong><br>${grInt(r.n_contracts)} contracts · ${eur(r.split_eur)}`;
	}
	function countTip(pe: string): string {
		const n = refsByPe.get(pe)?.size ?? 0;
		if (!n) return `<strong>${peEn(pe)}</strong><br>no contracts under authorities seated here`;
		return `<strong>${peEn(pe)}</strong><br>${grInt(n)} ${n === 1 ? 'contract' : 'contracts'} under authorities seated here`;
	}
	function homeTip(pe: string): string {
		const r = homeBase.get(pe);
		if (!r) return `<strong>${peEn(pe)}</strong><br>no registered offices located here`;
		return `<strong>${peEn(pe)}</strong><br>${grInt(r.n_contractors ?? 0)} contractors · ${eur(r.split_eur)}`;
	}
</script>

{#snippet rampKey(maxLabel: string)}
	<!-- the inline ramp key the user approved: 0 · [white + eight swatches,
	     one hairline round the whole bar] · max (2026-08-20) -->
	<span class="rampkey">
		<span>0</span><span class="swatches"><i class="empty"></i>{#each RAMP_WORKS as c (c)}<i style:background={c}></i>{/each}</span><span
			>{maxLabel}</span
		>
	</span>
{/snippet}

<div class="bar">
	<div class="barleft">
		<div class="maplabel">MAP<Hint text={howToRead} heading width="380px" /></div>
		{#if focus}
			<button class="reset" onclick={() => setFocus(focus!.side, null)} title="Back to all of Greece (Esc)">
				✕ {peEn(focus.pe)} · all of Greece
			</button>
		{/if}
	</div>
	<SegmentToggle
		param="view"
		fallback="money"
		options={[
			{ value: 'money', label: '€ choropleths' },
			{ value: 'points', label: 'Individual dots' }
		]}
	/>
</div>

<div class="twin">
	<div class="panel">
		<!-- this map's key, in the sponsored-works dress (user, 2026-08-20:
		     one strip per map, right above it — never a box over the map);
		     its first row names what the map is by -->
		<ul class="mapkey">
			<li class="lbl">by location of the contracts</li>
			{#if view === 'money'}
				<li class="ramp">
					{@render rampKey(eurShort(sharedMax))}
					<span>€ of works — each contract's even share</span>
				</li>
			{:else if !focus}
				<li class="ramp">
					{@render rampKey(grInt(maxRegionCount))}
					<span>contracts under forest authorities seated there</span>
				</li>
			{:else if focus.side === 'works'}
				<li><i class="dot work"></i>one contract × forest authority in {peEn(focus.pe)}</li>
				<li><i class="dot sel"></i>the selected contract</li>
				<li><i class="dash"></i>the seats of one contract, linked</li>
			{:else}
				<li><i class="dot work"></i>works of contractors based in {peEn(focus.pe)}</li>
			{/if}
		</ul>
		<PaperMap
			width={640}
			height={620}
			view={{ center: [23.8305, 38.3566], k: 1.08 }}
			colorOf={view === 'money'
				? (pe) => workChoro(workValues.get(pe) ?? 0)
				: focus
					? () => 'var(--land-empty)'
					: (pe) => countChoro(refsByPe.get(pe)?.size ?? 0)}
			tipOf={view === 'money' ? workTip : countTip}
			splitTips
			onEmptyClick={() => clearSelection()}
			onEscape={() => focus && setFocus(focus.side, null)}
			onRegionClick={(pe) => setFocus('works', focus?.side === 'works' && focus.pe === pe ? null : pe)}
			focusPe={focus?.side === 'works' ? focus.pe : null}
			fitPesLive={view === 'points' ? fitLive : null}
		>
			{#snippet overlay(ctx)}
				{#if view === 'points' && focus}
					{#each hoverSegments as seg, i (i)}
						{@const a = ctx.projection([seg[0][1], seg[0][0]])}
						{@const b = ctx.projection([seg[1][1], seg[1][0]])}
						{#if a && b}
							<line
								x1={a[0]}
								y1={a[1]}
								x2={b[0]}
								y2={b[1]}
								stroke={hoverColor}
								stroke-width={1.4 / ctx.k}
								stroke-dasharray="5 4"
								opacity="0.85"
								pointer-events="none"
							/>
						{/if}
					{/each}
					<DotLayer
						{ctx}
						points={contractDots}
						r={focus.side === 'works' ? 6 : 4.5}
						fillOf={(p) =>
							hotRefs.has(p.ref as string) || p.ref === selectedRef ? '#111111' : SINGLE_FILL}
						stroke={DRILL_STROKE}
						tipOf={(p) =>
							`<strong><a href="/antinero/contract/${p.ref}">${p.ref}</a></strong>` +
							`<br>${authEn(p.authority as string)}<br>${eur(p.eff_eur as number)}`}
						hotOf={(p) => hotRefs.has(p.ref as string) || p.ref === selectedRef}
						pinTip={(p) => p.ref === selectedRef}
						onUnpin={() => clearSelection()}
						onOver={(p) => hoverContract(p.ref as string)}
						onOut={() => unhoverContract()}
						onClick={(p) => clickContract(p.ref as string)}
					/>
				{/if}
			{/snippet}
		</PaperMap>
	</div>

	<div class="panel">
		<ul class="mapkey">
			<li class="lbl">by location of the contractors' registered offices</li>
			{#if view === 'money'}
				<li class="ramp">
					{@render rampKey(eurShort(sharedMax))}
					<span>€ of works — each contract's even share</span>
				</li>
			{:else if !focus}
				<li><i class="dot"></i>exact address</li>
				<li><i class="dot approx"></i>centre of municipality used as location<Hint text={whyCentre} /></li>
			{:else if focus.side === 'works'}
				<li><i class="dot grey"></i>the registered offices of the contractors holding those contracts</li>
				<li><i class="dot hot"></i>the selected contractor, or the selected contract's contractor</li>
			{:else}
				<li><i class="dot"></i>exact address</li>
				<li><i class="dot approx"></i>centre of municipality used as location<Hint text={whyCentre} /></li>
			{/if}
		</ul>
		<PaperMap
			width={640}
			height={620}
			view={{ center: [23.8305, 38.3566], k: 1.08 }}
			colorOf={view === 'money'
				? (pe) => homeChoro(homeValues.get(pe) ?? 0)
				: () => 'var(--land-empty)'}
			tipOf={homeTip}
			splitTips
			onEmptyClick={() => clearSelection()}
			onEscape={() => focus && setFocus(focus.side, null)}
			onRegionClick={(pe) => setFocus('home', focus?.side === 'home' && focus.pe === pe ? null : pe)}
			focusPe={focus?.side === 'home' ? focus.pe : null}
		>
			{#snippet overlay(ctx)}
				{#if view === 'points'}
					<!-- at country level the dots are decorative: hovering shows the
					     regional unit's card only (user, 2026-08-21); once a region
					     is selected on either map, the dots carry their own cards -->
					<DotLayer
						{ctx}
						points={contractorDots}
						inert={!focus}
						r={focus?.side === 'home' ? 6 : 4.5}
						fillOf={(p) =>
							hotVats.has(p.vat as string) || p.vat === selectedVat
								? '#111111'
								: focus?.side === 'works'
									? '#9a9a9a'
									: '#555555'}
						tipOf={(p) =>
							`<strong><a href="/antinero/contractor/${p.vat}">${p.name}</a></strong>` +
							`<br>${grInt(p.n_contracts as number)} ${(p.n_contracts as number) === 1 ? 'contract' : 'contracts'} · ${eur(p.total_eur as number)}`}
						dashOf={(p) => (p.precision === 'address' ? undefined : '2 2')}
						fillOpacityOf={(p) => (p.precision === 'address' ? undefined : 0.55)}
						hotOf={(p) => hotVats.has(p.vat as string) || p.vat === selectedVat}
						pinTip={(p) => selectedVats.has(p.vat as string) || p.vat === selectedVat}
						onUnpin={() => clearSelection()}
						onOver={(p) => (hoverVat = p.vat as string)}
						onOut={() => (hoverVat = null)}
						onClick={(p) => setSelectedVat(selectedVat === p.vat ? null : (p.vat as string))}
					/>
				{/if}
			{/snippet}
		</PaperMap>
	</div>
</div>


<style>
	.bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-4);
		flex-wrap: wrap;
		margin-bottom: var(--sp-3);
	}
	.barleft {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
	}
	/* the drill's way out — the table below the maps is gone (user, 2026-08-21) */
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
	.maplabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		color: var(--c-antinero);
	}
	/* the key strip — the sponsored-works legend's dress (anadohoi .stkey) */
	.mapkey {
		list-style: none;
		margin: 0 0 var(--sp-2);
		/* FIXED height — exactly two rows of fs-14 at the page's 1.55 line
		   height plus the padding — so the two map rectangles sit at the same
		   level and never move on toggle or drill (user); the rows are
		   centred in it, and the entries keep one measured gap */
		height: 4.3rem;
		/* NOT overflow:hidden — the ⓘ card in the strip is absolutely
		   positioned and was being clipped by it; the height alone keeps
		   the strip stable, and the entries fit in it */
		overflow: visible;
		position: relative;
		z-index: 2; /* the card paints above the map that follows */
		box-sizing: border-box;
		padding: var(--sp-2) var(--sp-3);
		background: #f2f2f2;
		border-radius: 6px;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		align-content: center;
		gap: 4px var(--sp-6, 1.5rem);
		/* the sponsored-works legend's lettering, exactly (anadohoi .stkey) */
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.mapkey li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	/* the inline ramp key: 0 · [white + eight swatches] · max — the same
	   lettering as every other entry, ONE hairline around the whole bar in
	   the legend's own text colour (user, 2026-08-20) */
	/* the inline ramp key: 0 · [white + eight swatches] · max — the same
	   lettering as every other entry, ONE hairline around the whole bar in
	   the legend's own text colour (user, 2026-08-20) */
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
	/* NOT «.bar» — that class is the toolbar above the maps, and its
	   space-between/wrap rule is what flung the swatches to the corners */
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
		background: var(--land-empty); /* the white of a unit with nothing */
	}
	.mapkey i.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: #555555; /* the country-level registered-office dot */
		flex: none;
	}
	/* the left map's contract dots: the map's own grey and stroke */
	.mapkey i.dot.work {
		background: #6b6b6b;
		border: 1px solid #333333;
		box-sizing: border-box;
	}
	/* the selected contract: black, enlarged, ink-stroked — as on the map */
	.mapkey i.dot.sel {
		width: 14px;
		height: 14px;
		background: #111111;
		border: 1.5px solid var(--ink);
		box-sizing: border-box;
	}
	.mapkey li.lbl {
		flex-basis: 100%; /* its own row; same lettering as every entry */
	}
	.mapkey i.dot.grey {
		background: #9a9a9a;
	}
	/* a settlement-centre dot: dashed ring over a 55 % fill — as drawn */
	.mapkey i.dot.approx {
		background: rgba(85, 85, 85, 0.55);
		border: 1.5px dashed #555555;
		box-sizing: border-box;
	}
	.mapkey i.dot.hot {
		background: #111111;
	}
	.mapkey i.dash {
		width: 18px;
		height: 0;
		border-top: 1.5px dashed #555;
		flex: none;
	}
	.twin {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-4);
	}
	@media (max-width: 900px) {
		.twin {
			grid-template-columns: 1fr;
		}
	}
</style>
