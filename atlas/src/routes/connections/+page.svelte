<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import BarH from '$lib/charts/BarH.svelte';
	import FlowArcs from '$lib/maps/FlowArcs.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, loadCentroids, makeChoro } from '$lib/maps/useGeo';
	import Bipartite from '$lib/sections/Bipartite.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const net = $derived(data.net);

	let centroids = $state.raw<Record<string, [number, number]>>({});
	$effect(() => {
		loadCentroids(fetch).then((c) => (centroids = c));
	});

	let flowFocus = $state<string | null>(null);
	const focusFlows = $derived(
		(flowFocus
			? net.flows.filter((f) => f.source_pe === flowFocus || f.target_pe === flowFocus)
			: net.flows.slice(0, 12)
		).toSorted((a, b) => b.total_eur - a.total_eur)
	);

	const short = (pe: string) => peEn(pe);

	// per WORK region: how much of its € is won by out-of-region firms
	const perWork = $derived.by(() => {
		const m = new Map<string, { total: number; local: number; origins: Map<string, number> }>();
		for (const f of net.flows) {
			let w = m.get(f.target_pe);
			if (!w) m.set(f.target_pe, (w = { total: 0, local: 0, origins: new Map() }));
			w.total += f.total_eur;
			if (f.source_pe === f.target_pe) w.local += f.total_eur;
			else w.origins.set(f.source_pe, (w.origins.get(f.source_pe) ?? 0) + f.total_eur);
		}
		return m;
	});
	const localPct = $derived.by(() => {
		let t = 0,
			l = 0;
		for (const f of net.flows) {
			t += f.total_eur;
			if (f.source_pe === f.target_pe) l += f.total_eur;
		}
		return t ? Math.round((100 * l) / t) : 0;
	});
	function importChoro(pe: string): string {
		const w = perWork.get(pe);
		if (!w || !w.total) return 'var(--land-empty)';
		const share = 1 - w.local / w.total; // linear 0–1 → 8 steps
		return RAMP_WORKS[Math.min(7, Math.floor(share * 8))];
	}
	function importTip(pe: string): string {
		const w = perWork.get(pe);
		if (!w || !w.total) return `<strong>${pe}</strong><br>no Anti-nero works recorded`;
		const share = Math.round(100 * (1 - w.local / w.total));
		const top = [...w.origins.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3);
		return (
			`<strong>${pe}</strong><br>${eurShort(w.total)} of works · ${share}% won by out-of-region firms` +
			(top.length
				? `<br><span style="color:var(--ink-faint)">top origins: ${top
						.map(([o, e]) => `${short(o)} (${eurShort(e)})`)
						.join(', ')}</span>`
				: '') +
			`<br><span style="color:var(--ink-faint)">click to see its flows</span>`
		);
	}

	// the six biggest company hubs and their catchments (shared scale)
	const hubs = $derived.by(() => {
		const agg = new Map<string, { exported: number; nDest: number; cells: Map<string, number> }>();
		for (const f of net.flows) {
			let h = agg.get(f.source_pe);
			if (!h) agg.set(f.source_pe, (h = { exported: 0, nDest: 0, cells: new Map() }));
			h.cells.set(f.target_pe, (h.cells.get(f.target_pe) ?? 0) + f.total_eur);
			if (f.source_pe !== f.target_pe) {
				h.exported += f.total_eur;
				h.nDest++;
			}
		}
		return [...agg.entries()]
			.sort((a, b) => b[1].exported - a[1].exported)
			.slice(0, 6)
			.map(([pe, h]) => ({ pe, ...h }));
	});
	const hubMax = $derived(Math.max(...hubs.flatMap((h) => [...h.cells.values()]), 1));
	const hubChoro = $derived(makeChoro(RAMP_WORKS, hubMax));

	function pickHub(pe: string) {
		flowFocus = pe;
		document.getElementById('flows')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	// local-vs-imported strip for the top-12 destinations
	const originRows = $derived(net.origins.slice(0, 12));

	const signers = $derived.by(() => {
		const by = new Map<string, { vat: string; n: number; eur: number }[]>();
		for (const e of net.contractor_signer) {
			if (!by.has(e.signer)) by.set(e.signer, []);
			by.get(e.signer)!.push(e);
		}
		return [...by.entries()]
			.map(([signer, es]) => ({
				signer,
				total: es.reduce((s, e) => s + e.eur, 0),
				top: es
					.sort((a, b) => b.eur - a.eur)
					.slice(0, 8)
					.map((e) => ({
						label: net.contractors[e.vat]?.name ?? e.vat,
						value: e.eur,
						href: `/antinero/contractor/${e.vat}`,
						sublabel: `${e.n}×`
					}))
			}))
			.sort((a, b) => b.total - a.total);
	});

	// consortium cliques: group the 12 pairs into connected components
	// finding-title inputs — computed, never hardcoded
	const maxReach = $derived.by(() => {
		const perVat = new Map<string, number>();
		for (const e of net.contractor_pe) perVat.set(e.vat, (perVat.get(e.vat) ?? 0) + 1);
		let vat = '';
		let n = 0;
		for (const [v, k] of perVat) if (k > n) [vat, n] = [v, k];
		return { name: net.contractors[vat]?.name ?? vat, n };
	});
	const nRecurring = $derived(net.pairs.filter((pr) => pr.refs.length > 1).length);

	const cliques = $derived.by(() => {
		const parent = new Map<string, string>();
		const find = (x: string): string => {
			while (parent.get(x) !== x) {
				parent.set(x, parent.get(parent.get(x)!)!);
				x = parent.get(x)!;
			}
			return x;
		};
		for (const p of net.pairs) {
			if (!parent.has(p.a)) parent.set(p.a, p.a);
			if (!parent.has(p.b)) parent.set(p.b, p.b);
			parent.set(find(p.a), find(p.b));
		}
		const groups = new Map<string, { vats: Set<string>; pairs: typeof net.pairs }>();
		for (const p of net.pairs) {
			const root = find(p.a);
			if (!groups.has(root)) groups.set(root, { vats: new Set(), pairs: [] });
			const gr = groups.get(root)!;
			gr.vats.add(p.a);
			gr.vats.add(p.b);
			gr.pairs.push(p);
		}
		return [...groups.values()].sort((a, b) => b.vats.size - a.vats.size);
	});
</script>

<svelte:head>
	<title>Connections — who works with whom, where</title>
	<meta
		name="description"
		content="The Anti-nero relationship map: money flows between regions, contractor–authority links, consortium networks."
	/>
</svelte:head>

<hgroup class="lede">
	<h1>Who works with whom, and where the money travels</h1>
	<p class="standfirst">
		The interesting network is not company-to-company — consortiums are rare. It is
		geographic and institutional: which firms reach into which forests, from where.
	</p>
</hgroup>

<ChartFrame
	title="Only {localPct}% of the work-money goes to firms based where the work is"
	subtitle="Each region is coloured by the share of its works won by out-of-region firms — darker means more of the money leaves. Click a region: red arrows show who reaches in, blue where its own firms reach out."
	caveat="Geocoded contractors only — {eurShort(net.coverage.resolved_eur)} of {eurShort(
		net.coverage.total_eur
	)} resolved. Full-exposure convention: a multi-region contract counts toward every region pair it touches; the within-region shares are unaffected."
	anchor="flows"
	methodology="even-split"
>
	<div class="flow-grid">
		<PaperMap
			colorOf={flowFocus
				? (pe) => (pe === flowFocus ? 'var(--ramp-works-1)' : 'var(--land-empty)')
				: importChoro}
			tipOf={flowFocus ? undefined : importTip}
			onRegionClick={(pe) => (flowFocus = flowFocus === pe ? null : pe)}
			focusPe={null}
		>
			{#snippet overlay(ctx)}
				{#if flowFocus && Object.keys(centroids).length}
					<FlowArcs {ctx} flows={net.flows} {centroids} focusPe={flowFocus} />
				{/if}
			{/snippet}
			{#snippet legend()}
				{#if flowFocus}
					<div><i class="sw" style="background:#b33a1a"></i> firms based elsewhere → works in {short(flowFocus)}</div>
					<div><i class="sw" style="background:#2258a5"></i> {short(flowFocus)} firms → works elsewhere</div>
					<div><i class="sw round" style="background:#3d7a4a"></i> money that stays local</div>
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
					{flowFocus}
					<button class="btn-more" onclick={() => (flowFocus = null)}>✕ clear</button>
				{:else}
					Largest flows
				{/if}
			</h3>
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
		</div>
	</div>
</ChartFrame>

<ChartFrame
	title="{grInt(hubs.length)} company hubs bank most of the travelling money"
	subtitle="Where each hub's firms won their Anti-nero works (one map per hub, shared colour scale). Click a map to trace that hub's flows above."
	caveat="Top six home regions by € won outside their base; the shading includes money won at home."
	anchor="hubs"
	methodology="even-split"
>
	<div class="hubs">
		{#each hubs as h (h.pe)}
			<button class="hub" onclick={() => pickHub(h.pe)}>
				<div class="hub-head">
					<strong>{short(h.pe)}</strong>
					<span>{eurShort(h.exported)} won away · {h.nDest} regions</span>
				</div>
				<PaperMap interactive={false} colorOf={(pe) => hubChoro(h.cells.get(pe) ?? 0)}>
					{#snippet overlay(ctx)}
						{#if centroids[h.pe]}
							{@const pt = ctx.projection([centroids[h.pe][1], centroids[h.pe][0]])}
							{#if pt}
								<circle class="hub-dot" cx={pt[0]} cy={pt[1]} r={5 / ctx.k} />
							{/if}
						{/if}
					{/snippet}
				</PaperMap>
			</button>
		{/each}
	</div>
</ChartFrame>

<ChartFrame
	title="In the biggest destinations, local firms take a small slice"
	subtitle="€ of works in the top-{originRows.length} destination regions, split by whether the winning firm is based in that region."
	anchor="origins"
	methodology="even-split"
>
	<div class="origins">
		{#each originRows as o (o.target_pe)}
			{@const total = o.local_eur + o.imported_eur + o.unknown_eur}
			<div class="orow">
				<span class="olabel">{peEn(o.target_pe)}</span>
				<div class="obar">
					<div class="seg local" style:width={`${(100 * o.local_eur) / total}%`}></div>
					<div class="seg imported" style:width={`${(100 * o.imported_eur) / total}%`}></div>
					<div class="seg unknown" style:width={`${(100 * o.unknown_eur) / total}%`}></div>
				</div>
				<span class="oval">{eurShort(o.total_eur)}</span>
			</div>
		{/each}
		<div class="olegend">
			<span><i class="local"></i>local firms</span>
			<span><i class="imported"></i>out-of-region firms</span>
			<span><i class="unknown"></i>unresolved</span>
		</div>
	</div>
</ChartFrame>

<ChartFrame
	title="A handful of companies reach into many regions"
	subtitle="Contractor ↔ work-region links ({grInt(net.contractor_pe.length)} edges across {grInt(
		Object.keys(net.contractors).length
	)} contractors). {maxReach.name} alone works in {maxReach.n} regional units."
	caveat="Edge € even-split across a contract's partners and regions — the layer sums to the programme total."
	anchor="bipartite"
	methodology="even-split"
>
	<Bipartite edges={net.contractor_pe} contractors={net.contractors} />
</ChartFrame>

<ChartFrame
	title="{grInt(signers.length)} signatures moved {eurShort(net.coverage.total_eur)}"
	subtitle="Top counterparties of each signing official (even-split €)."
	anchor="signers"
>
	<div class="signers">
		{#each signers as s (s.signer)}
			<div>
				<h3>{s.signer}</h3>
				<p class="muted"><small>{eurShort(s.total)} total</small></p>
				<BarH rows={s.top} />
			</div>
		{/each}
	</div>
</ChartFrame>

<ChartFrame
	title="Consortiums are the exception: {grInt(net.pairs.length)} partnerships, {grInt(nRecurring)} recurring"
	subtitle="Every contractor–contractor relationship in the dataset."
	caveat="Pair € = full value of the shared contracts (both partners are fully exposed)."
	anchor="cliques"
	methodology="max-exposure"
>
	<div class="cliques">
		{#each cliques as g, gi (gi)}
			<div class="clique">
				<div class="members">
					{#each [...g.vats] as vat (vat)}
						<a href={`/antinero/contractor/${vat}`}>{net.contractors[vat]?.name ?? vat}</a>
					{/each}
				</div>
				<div class="pairs-detail">
					{#each g.pairs as p, pi (pi)}
						<small class="muted">
							{net.contractors[p.a]?.name ?? p.a} + {net.contractors[p.b]?.name ?? p.b}
							— {p.refs.length} shared, {eur(p.eur)}
						</small>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</ChartFrame>

<style>
	.lede {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
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
	.flow-list h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
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
		background: #b33a1a;
	}
	i.dir.out {
		background: #2258a5;
	}
	i.dir.local {
		background: #3d7a4a;
	}
	.hubs {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
		gap: var(--sp-4);
	}
	.hub {
		font: inherit;
		text-align: left;
		border: 1px solid var(--line);
		border-radius: var(--radius);
		background: var(--paper);
		padding: var(--sp-2);
		cursor: pointer;
	}
	.hub:hover {
		border-color: var(--accent);
	}
	.hub-head {
		display: flex;
		flex-direction: column;
		margin-bottom: var(--sp-1);
	}
	.hub-head strong {
		font-size: var(--fs-14);
		line-height: 1.2;
	}
	.hub-head span {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	:global(.hub .map) {
		box-shadow: none;
	}
	.hub :global(circle.hub-dot) {
		fill: var(--c-dase-deep);
		stroke: var(--paper);
		stroke-width: 1.2;
	}
	.origins .orow {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		margin-bottom: 4px;
	}
	.olabel {
		width: 11rem;
		font-size: var(--fs-13);
		text-align: right;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.obar {
		flex: 1;
		display: flex;
		height: 14px;
		border-radius: 2px;
		overflow: hidden;
		background: var(--paper-2);
	}
	.seg.local {
		background: var(--c-good);
	}
	.seg.imported {
		background: var(--accent);
	}
	.seg.unknown {
		background: var(--line-strong);
	}
	.oval {
		width: 5.5rem;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.olegend {
		display: flex;
		gap: var(--sp-4);
		font-size: var(--fs-12);
		color: var(--ink-soft);
		margin-top: var(--sp-2);
	}
	.olegend i {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		margin-right: 4px;
	}
	.olegend i.local {
		background: var(--c-good);
	}
	.olegend i.imported {
		background: var(--accent);
	}
	.olegend i.unknown {
		background: var(--line-strong);
	}
	.signers {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
		gap: var(--sp-6);
	}
	.signers h3 {
		font-family: var(--font-ui);
		font-size: var(--fs-14);
	}
	.cliques {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
		gap: var(--sp-4);
	}
	.clique {
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		padding: var(--sp-3);
		background: var(--paper-2);
	}
	.members {
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-2);
		margin-bottom: var(--sp-2);
	}
	.members a {
		font-size: var(--fs-13);
		font-weight: 600;
		text-decoration: none;
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		padding: 0 var(--sp-2);
		background: var(--paper);
	}
	.members a:hover {
		color: var(--accent);
	}
	.pairs-detail {
		display: grid;
		gap: 2px;
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
