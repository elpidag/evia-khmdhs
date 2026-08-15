<script lang="ts">
	import { ruLabel } from '$lib/transforms/regions';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { AntineroMapPayload } from '$lib/api';
	import ChoroLegend from '$lib/maps/ChoroLegend.svelte';
	import DotLayer, { type DotPoint } from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, makeChoro, spreadOverlaps } from '$lib/maps/useGeo';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import DrillPanel from './DrillPanel.svelte';

	let { data }: { data: AntineroMapPayload } = $props();

	// ---- URL state -----------------------------------------------------
	const view = $derived(page.url.searchParams.get('view') === 'points' ? 'points' : 'money');
	const focusRaw = $derived(page.url.searchParams.get('focus'));
	const focus = $derived.by(() => {
		const m = focusRaw?.match(/^(works|home):(.+)$/);
		return m ? { side: m[1] as 'works' | 'home', pe: m[2] } : null;
	});

	function setFocus(side: 'works' | 'home', pe: string | null) {
		const url = new URL(page.url);
		if (pe) url.searchParams.set('focus', `${side}:${pe}`);
		else url.searchParams.delete('focus');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	// ---- lookups -------------------------------------------------------
	const vatHome = $derived(
		new Map(data.contractor_points.points.map((p) => [p.vat, p.pe]))
	);
	const workBase = $derived(new Map(data.work_regions.map((r) => [r.pe, r])));
	const homeBase = $derived(new Map(data.home_regions.map((r) => [r.pe, r])));
	const sharedMax = $derived(
		Math.max(
			...data.work_regions.map((r) => r.split_eur),
			...data.home_regions.map((r) => r.split_eur)
		)
	);

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
	const SINGLE_FILL = '#6e6353';
	const DRILL_STROKE = '#3a3429';

	const contractDots = $derived.by(() => {
		let pts = data.contract_points;
		if (focus?.side === 'works') pts = pts.filter((p) => p.pe === focus.pe);
		else if (focus?.side === 'home')
			pts = pts.filter((p) => focusContracts.some((c) => c.ref === p.ref));
		// the zoomed map needs far less de-overlap spread than country level
		return spreadOverlaps(
			pts as unknown as DotPoint[],
			focus?.side === 'works' ? 0.012 : 0.034
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
			focus?.side === 'home' ? 0.01 : 0.02
		)
	);

	const drillColors = $derived.by(() => {
		if (focus?.side !== 'works') return null;
		const multi = [...new Set(contractDots.map((p) => p.ref as string))]
			.filter((r) => (authCount.get(r) ?? 0) > 1)
			.sort();
		const n = Math.max(1, multi.length);
		const m = new Map<string, string>();
		multi.forEach((ref, i) => {
			const hue = (20 + (360 * i) / n) % 360;
			m.set(
				ref,
				i % 2 ? `oklch(0.70 0.13 ${hue.toFixed(1)})` : `oklch(0.55 0.16 ${hue.toFixed(1)})`
			);
		});
		return m;
	});

	// Hovering a multi-authority contract's dot links ALL its authority
	// seats with dashed lines in the contract's colour — off-region seats
	// at their true spots, so a line running off-frame means the contract
	// spans beyond this Π.Ε.
	let hoverRef = $state<string | null>(null);
	const hoverSegments = $derived.by(() => {
		if (!hoverRef || focus?.side !== 'works') return [];
		const anchors: [number, number][] = [];
		for (const p of contractDots)
			if (p.ref === hoverRef) anchors.push([p.lat2 ?? p.lat, p.lon2 ?? p.lon]);
		for (const p of data.contract_points)
			if (p.ref === hoverRef && p.pe !== focus.pe) anchors.push([p.lat, p.lon]);
		const segs: [[number, number], [number, number]][] = [];
		for (let i = 0; i < anchors.length; i++)
			for (let j = i + 1; j < anchors.length; j++) segs.push([anchors[i], anchors[j]]);
		return segs;
	});
	const hoverColor = $derived(
		hoverRef ? (drillColors?.get(hoverRef) ?? SINGLE_FILL) : SINGLE_FILL
	);

	// ---- tooltips ------------------------------------------------------
	function workTip(pe: string): string {
		const r = workBase.get(pe);
		if (!r) return `<strong>${ruLabel(pe)}</strong><br>no Anti-nero works recorded`;
		return (
			`<strong>${ruLabel(pe)}</strong><br>${grInt(r.n_contracts)} contracts` +
			`<br>${eur(r.split_eur)} even-split share` +
			`<br><span style="color:var(--ink-faint)">${eurShort(r.exposure_eur)} full exposure</span>`
		);
	}
	function countTip(pe: string): string {
		const n = refsByPe.get(pe)?.size ?? 0;
		if (!n) return `<strong>${ruLabel(pe)}</strong><br>no contracts under authorities seated here`;
		return (
			`<strong>${ruLabel(pe)}</strong><br>${grInt(n)} contract(s) under forest authorities seated here` +
			`<br><span style="color:var(--ink-faint)">click to see the individual works</span>`
		);
	}
	function homeTip(pe: string): string {
		const r = homeBase.get(pe);
		if (!r) return `<strong>${ruLabel(pe)}</strong><br>no contractor HQs located here`;
		return (
			`<strong>${ruLabel(pe)}</strong><br>${grInt(r.n_contractors ?? 0)} contractors` +
			`<br>${eur(r.split_eur)} even-split share` +
			`<br><span style="color:var(--ink-faint)">${eurShort(r.exposure_eur)} full exposure</span>`
		);
	}
</script>

<div class="bar">
	<SegmentToggle
		param="view"
		fallback="money"
		options={[
			{ value: 'money', label: '€ choropleths' },
			{ value: 'points', label: 'Individual dots' }
		]}
	/>
	<small class="muted">
		{eurShort(data.coverage.resolved_eur)} of {eurShort(data.coverage.total_eur)} is
		region-resolved · click a regional unit to drill
	</small>
</div>

<div class="twin">
	<div class="panel">
		<h3>allocation of funding by location of contracts</h3>
		<PaperMap
			width={640}
			height={620}
			view={{ center: [23.8305, 38.3566], k: 1.08 }}
			colorOf={view === 'money'
				? (pe) => workChoro(workValues.get(pe) ?? 0)
				: focus
					? () => 'var(--land-empty)'
					: (pe) => countChoro(refsByPe.get(pe)?.size ?? 0)}
			tipOf={view === 'money' ? workTip : focus ? undefined : countTip}
			onRegionClick={(pe) => setFocus('works', focus?.side === 'works' && focus.pe === pe ? null : pe)}
			focusPe={focus?.side === 'works' ? focus.pe : null}
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
						fillOf={focus.side === 'works'
							? (p) => drillColors?.get(p.ref as string) ?? SINGLE_FILL
							: () => 'var(--accent)'}
						stroke={focus.side === 'works' ? DRILL_STROKE : 'rgba(42,33,24,.45)'}
						tipOf={(p) =>
							`<strong>${p.title}</strong><br>${p.authority}<br>${eur(p.eff_eur as number)}` +
							((authCount.get(p.ref as string) ?? 0) > 1
								? '<br><span style="color:var(--ink-faint)">multi-authority contract — hover links its seats</span>'
								: '')}
						hrefOf={(p) => `/antinero/contract/${p.ref}`}
						onOver={(p) => (hoverRef = p.ref as string)}
						onOut={() => (hoverRef = null)}
					/>
				{/if}
			{/snippet}
			{#snippet legend()}
				{#if view === 'money'}
					<ChoroLegend ramp={RAMP_WORKS} max={sharedMax} title="€ of works (even-split)" />
				{:else if !focus}
					<ChoroLegend
						ramp={RAMP_WORKS}
						max={maxRegionCount}
						title="contracts under authorities seated here"
						fmt={grInt}
					/>
				{:else if focus.side === 'works'}
					<div>one dot = one contract × authority in {ruLabel(focus.pe)}</div>
					<div>colour groups multi-authority contracts · hover links their seats</div>
				{:else}
					<div>works of contractors based in {ruLabel(focus.pe)}</div>
				{/if}
			{/snippet}
		</PaperMap>
	</div>

	<div class="panel">
		<h3>allocation of funding by base-location of contractors</h3>
		<PaperMap
			width={640}
			height={620}
			view={{ center: [23.8305, 38.3566], k: 1.08 }}
			colorOf={view === 'money'
				? (pe) => homeChoro(homeValues.get(pe) ?? 0)
				: () => 'var(--land-empty)'}
			tipOf={homeTip}
			onRegionClick={(pe) => setFocus('home', focus?.side === 'home' && focus.pe === pe ? null : pe)}
			focusPe={focus?.side === 'home' ? focus.pe : null}
		>
			{#snippet overlay(ctx)}
				{#if view === 'points'}
					<DotLayer
						{ctx}
						points={contractorDots}
						r={focus?.side === 'home' ? 6 : 4.5}
						fillOf={() => 'var(--c-dase-deep)'}
						tipOf={(p) =>
							`<strong>${p.name}</strong><br>${p.pe ?? ''} · ${p.precision}` +
							`<br>${grInt(p.n_contracts as number)} contracts · ${eur(p.total_eur as number)}`}
						hrefOf={(p) => `/antinero/contractor/${p.vat}`}
					/>
				{/if}
			{/snippet}
			{#snippet legend()}
				{#if view === 'money'}
					<ChoroLegend ramp={RAMP_WORKS} max={sharedMax} title="€ by contractor HQ (even-split)" />
				{:else}
					<div>
						one dot = one contractor HQ ({grInt(contractorDots.length)} of
						{grInt(data.contractor_points.coverage.n_total)} geocoded)
					</div>
				{/if}
			{/snippet}
		</PaperMap>
	</div>
</div>

{#if focus}
	<DrillPanel
		pe={focus.pe}
		side={focus.side}
		contracts={focusContracts.map((c) => ({ ref: c.ref, title: c.title, eur: c.share }))}
		contractors={drillContractors}
		onReset={() => setFocus(focus!.side, null)}
	/>
{/if}

<style>
	.bar {
		display: flex;
		align-items: center;
		gap: var(--sp-4);
		flex-wrap: wrap;
		margin-bottom: var(--sp-3);
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
	.panel h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
		font-weight: 600;
		color: var(--ink-soft);
		margin: 0 0 var(--sp-2);
	}
	.muted {
		color: var(--ink-faint);
	}
</style>
