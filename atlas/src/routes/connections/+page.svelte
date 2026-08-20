<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import BarH from '$lib/charts/BarH.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, loadCentroids, makeChoro } from '$lib/maps/useGeo';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const net = $derived(data.net);
	const short = (pe: string) => peEn(pe);
	const nRecurring = $derived(net.pairs.filter((pr) => pr.refs.length > 1).length);

	let centroids = $state.raw<Record<string, [number, number]>>({});
	$effect(() => {
		loadCentroids(fetch).then((c) => (centroids = c));
	});

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

	/** the flow map moved to the Anti-nero page (user, 2026-08-20), so a hub
	 *  click follows it there rather than scrolling to a chart that is no
	 *  longer on this page */
	const hubHref = (pe: string) => `/#flows`;

	// local-vs-imported strip for the top-12 destinations
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
	title="{grInt(hubs.length)} company hubs bank most of the travelling money"
	subtitle="Where each hub's firms won their Anti-nero works (one map per hub, shared colour scale). Click a map for the flow map on the Anti-nero page."
	caveat="Top six home regions by € won outside their base; the shading includes money won at home."
	anchor="hubs"
	methodology="even-split"
>
	<div class="hubs">
		{#each hubs as h (h.pe)}
			<a class="hub" href={hubHref(h.pe)}>
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
			</a>
		{/each}
	</div>
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

<!-- Joint ventures almost always sign as a κοινοπραξία with an ΑΦΜ of its own,
     so the registry records ONE party and this layer can only see the rare
     contract signed by the partners as themselves (DATA_DECISIONS 2026-08-20).
     Until the consortium-membership layer lands, the frame draws only when
     there is a network to draw. -->
{#if net.pairs.length > 2}
<ChartFrame
	title="Companies that signed side by side: {grInt(net.pairs.length)} partnerships, {grInt(
		nRecurring
	)} recurring"
	subtitle="Contractor–contractor relationships visible in the registry's own party lists."
	caveat="Pair € = the full value of the contracts the two signed together — a pair's figure is
	the contract, not either partner's share."
	anchor="cliques"
	methodology="joint-contracts"
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
{/if}

<style>
	.lede {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
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
