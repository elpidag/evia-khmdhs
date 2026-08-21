<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import SideNote from '$lib/ui/SideNote.svelte';
	import { YEAR_GREYS, yearGrey } from '$lib/charts/yearColors';
	import { binByKey } from '$lib/transforms/histogram';
	import type { DaseSwarm } from '$lib/api';
	import DisbursementCurves from '$lib/charts/DisbursementCurves.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import KindFlow from '$lib/charts/KindFlow.svelte';
	import WorksMatrix from '$lib/charts/WorksMatrix.svelte';
	import WorksBubbleGrid from '$lib/charts/WorksBubbleGrid.svelte';
	import WorksBundles from '$lib/charts/WorksBundles.svelte';
	import WorksByCategory from '$lib/charts/WorksByCategory.svelte';
	import WorksPack from '$lib/charts/WorksPack.svelte';
	import { unitEn } from '$lib/transforms/names';
	import SmallMultiples from '$lib/charts/SmallMultiples.svelte';
	import StripTimeline from '$lib/charts/StripTimeline.svelte';
	import AntineroMap from '$lib/sections/AntineroMap.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import FlowMap from '$lib/sections/FlowMap.svelte';
		import { loadCentroids } from '$lib/maps/useGeo';
	import type { Connections } from './connections/+page';
	import ContractNetwork from '$lib/charts/ContractNetwork.svelte';
	import type { NetNode } from '$lib/transforms/network';
	import { NET_MODES, type NetMode } from '$lib/transforms/networkScene';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import {
		apiGetCached,
		type AntineroMapPayload,
		type PaymentsPayload,
		type PeYearly,
		type SwarmRow
	} from '$lib/api';
	import { eurShort, grInt, pct } from '$lib/transforms/format';
	import { page } from '$app/state';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	// heavy payloads load client-side (cached across navigations);
	// $state.raw — immutable data must not pay deep-proxy overhead
	let map = $state.raw<AntineroMapPayload | null>(null);
	let payments = $state.raw<PaymentsPayload | null>(null);
	// MONEY FLOW: the ΥΠΕΝ unit that signed → the contractors (user, 2026-08-21)
	interface UnitFlow {
		nodes: { id: string; label: string; side: 'l' | 'r'; n: number; eur: number; href?: string }[];
		links: { s: string; t: string; n: number; eur: number }[];
		total_eur: number;
		top_eur: number;
		n_units: number;
		n_top: number;
		n_rest: number;
		n_contractors: number;
	}
	let unitFlow = $state.raw<UnitFlow | null>(null);
	let swarm = $state.raw<SwarmRow[] | null>(null);
	let peYearly = $state.raw<PeYearly | null>(null);
	let network = $state.raw<{
		nodes: NetNode[];
		stats: Record<string, number>;
		fire_season: { from: string; to: string; n_contracts: number };
	} | null>(null);
	/** the flow layer, moved here from /connections (user, 2026-08-20) */
	let net = $state.raw<Connections | null>(null);
	let centroids = $state.raw<Record<string, [number, number]>>({});
	$effect(() => {
		apiGetCached<Connections>(fetch, '/api/connections').then((v) => (net = v));
		loadCentroids(fetch).then((c) => (centroids = c));
		apiGetCached<AntineroMapPayload>(fetch, '/api/antinero/map').then((v) => (map = v));
		apiGetCached<PaymentsPayload>(fetch, '/api/antinero/payments').then((v) => (payments = v));
		apiGetCached<UnitFlow>(fetch, '/api/antinero/unit-flow').then((v) => (unitFlow = v));
		apiGetCached<SwarmRow[]>(fetch, '/api/antinero/swarm').then((v) => (swarm = v));
		apiGetCached<PeYearly>(fetch, '/api/antinero/pe-yearly').then((v) => (peYearly = v));
		apiGetCached<{
			nodes: NetNode[];
			stats: Record<string, number>;
			fire_season: { from: string; to: string; n_contracts: number };
		}>(fetch, '/api/antinero/network').then((v) => (network = v));
	});

	// the programme chart is one population under three arrangements, and
	// each arrangement has a different honest headline — every number in
	// them comes from the payload's own stats
	const netMode = $derived(
		(NET_MODES.find((m) => m.value === page.url.searchParams.get('net'))?.value ??
			'time') as NetMode
	);
	const netCopy = $derived.by(() => {
		const st = network?.stats ?? {};
		if (netMode === 'call')
			return {
				title: `THE PROGRAMME WAS BOUGHT IN ${grInt(st.n_calls)} SEPARATE PROCUREMENTS, MOST OF THEM ONE CONTRACT LONG`,
				subtitle:
					'Each star is one call: the biggest lot at its centre, the others around it. Below, the calls that produced a single contract, and the awards made with no call at all.',
				caveat: 'The dashed lines join two calls won by the same contractor.'
			};
		if (netMode === 'pack')
			return {
				title: `${grInt(st.n_single_call)} OF THE ${grInt(st.n_calls)} CALLS BOUGHT EXACTLY ONE CONTRACT`,
				subtitle:
					'The contracts nested inside the call that bought them: the split procurements hold the middle, and every contract bought on its own rings them. Bubble area is the money.',
				caveat:
					'A bubble is one πρόσκληση and the circles inside it are its lots; a bare circle is a contract with no sibling, dashed when no call was published at all.'
			};
		return {
			title: `${grInt(st.n_same_day_calls)} OF THE ${grInt(st.n_multi_calls)} SPLIT PROCUREMENTS SIGNED EVERY LOT ON ONE DAY`,
			subtitle:
				'Every in-scope contract on the date it was signed, dodged so none hides another; contracts bought under the same call are joined.',
			caveat:
				'Vertical position carries no meaning here — it is packing, not a value axis. The shaded stripes are the fire season, 1 May to 31 October.'
		};
	});

	const directEur = $derived(o.procedures.find((p) => p.label.includes('Απευθείας'))?.eur ?? 0);
	// the ranking has two views of the same money (user, 2026-08-20): the
	// company that SIGNED, and the firms behind it. A κοινοπραξία signs 54 of
	// the contracts, so «as contracted» hides whoever is inside it.
	const RANK_MODES = [
		{ value: 'party', label: 'as contracted' },
		{ value: 'firm', label: 'by member firm' }
	];
	const rankMode = $derived(
		o.member_firms ? (page.url.searchParams.get('rank') ?? 'party') : 'party'
	);
	const topRows = $derived.by(() => {
		const rows: {
			vat_number: string;
			name: string;
			n_contracts: number;
			total_eur: number;
			via_eur?: number;
			n_ventures?: number;
		// degrade to the contracted view when the API predates this layer,
		// rather than throwing on an undefined list
		}[] = (rankMode === 'firm' ? o.member_firms : o.top_contractors) ?? o.top_contractors;
		return rows.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/antinero/contractor/${c.vat_number}`,
			sublabel: c.via_eur
				? `${c.n_contracts} contracts · ${eurShort(c.via_eur)} through ${
						c.n_ventures
					} joint venture${(c.n_ventures ?? 0) > 1 ? 's' : ''}`
				: `${c.n_contracts} contracts`
		}));
	});
	const procRows = $derived(
		o.procedures.map((p) => ({
			label: p.label,
			value: p.eur,
			sublabel: `${p.n_contracts} contracts`
		}))
	);
	const studyRows = $derived(
		o.studies.top.map((s) => ({
			label: String(s.title).slice(0, 90),
			value: Number(s.eur),
			href: `/antinero/contract/${s.ref}`,
			sublabel: `${((s.share as number) * 100).toFixed(1)}% of the contract's net value`
		}))
	);

	// auto-note: the single biggest payment month
	const peak = $derived.by(() => {
		const byMonth = new Map<string, number>();
		for (const e of payments?.events ?? [])
			if (e.m) byMonth.set(e.m, (byMonth.get(e.m) ?? 0) + (e.eur || 0));
		let best: [string, number] = ['', 0];
		for (const kv of byMonth) if (kv[1] > best[1]) best = kv;
		return { m: best[0], eur: best[1] };
	});

	// statutory ν.4782/2021 ceilings come from the API payload, never inline
	const thresholds = $derived(
		(o.direct_awards.thresholds as number[]).map((v, i) => ({
			v,
			label: `€${Math.round(v / 1000)}k ceiling (${i === 0 ? 'supplies/services, ν.4782/2021' : 'works'})`
		}))
	);
	const miniThresholds = $derived(
		(o.direct_awards.thresholds as number[]).map((v) => ({
			v,
			label: `€${Math.round(v / 1000)}k`
		}))
	);
	// the CONTRACT VALUES frame: the ΔΑΣΕ dots/brackets convention, greys by
	// signature year (user, 2026-08-20). The swarm list becomes the canvas
	// component's column arrays; the ring column marks single-bid contracts.
	let valueMode = $state<'dots' | 'brackets'>('dots');
	let dotsHeight = $state(0);
	const swarmCols = $derived.by((): (DaseSwarm & { ring: number[] }) | null => {
		if (!swarm) return null;
		return {
			ref: swarm.map((r) => r.ref),
			t: swarm.map((r) => r.t),
			eur: swarm.map((r) => r.eur),
			year: swarm.map((r) => r.year),
			d: swarm.map((r) => r.d),
			pe: swarm.map((r) => r.pe),
			vat: swarm.map(() => null),
			ring: swarm.map((r) => r.single_bidder)
		};
	});
	const swarmYears = $derived(
		swarmCols ? ([...new Set(swarmCols.year.filter(Boolean))].sort() as string[]) : []
	);
	const yearSegments = $derived(
		swarmCols
			? binByKey(
					swarmCols.eur.map((v) => v ?? 0),
					swarmCols.year,
					o.value_histogram.edges,
					swarmYears
				)
			: []
	);
	// the most common bracket, said in the side note rather than printed in
	// the chart's corner (user, 2026-08-21) — from the histogram payload
	const modalBracket = $derived.by(() => {
		const counts = o.value_histogram.counts as number[];
		const labels = o.value_histogram.labels as string[];
		let best = -1;
		for (let i = 0; i < counts.length; i++) if (best < 0 || counts[i] > counts[best]) best = i;
		return best >= 0 ? { label: labels[best], n: counts[best] } : null;
	});
	const VALUE_NOTES = $derived<Record<'dots' | 'brackets', string>>({
		dots: 'Every contract is one dot on a log scale (stated €, excl. VAT). Colours are assigned according to the year the contract was signed. Hover to inspect, click through to go to the contract’s page.',
		brackets:
			'The same contracts counted into brackets, each one a doubling of value — which is why the bars sit on the same scale as the dots. Bar height is the number of contracts; within a bar the signature years stack in legend order, earliest at the bottom.' +
			(modalBracket ? ` The most common bracket is ${modalBracket.label} € (${grInt(modalBracket.n)} contracts).` : '')
	});

	// the modal direct-award bin, for the finding title
	const daModal = $derived.by(() => {
		const counts = o.direct_awards.counts as number[];
		const labels = o.direct_awards.labels as string[];
		let best = 0;
		for (let i = 1; i < counts.length; i++) if (counts[i] > counts[best]) best = i;
		return labels[best] ?? '';
	});
	const firstPayYear = $derived((o.timeseries.months[0] ?? '').slice(0, 4));
	// work-type category chart: stated € or contract counts, same bars
	// the TYPES OF WORK lens, a URL param like the other frames' toggles —
	// «category» / «named» and, under trial (2026-08-22), «flow» / «matrix» /
	// «pack»
	const WORKS_LENSES = ['category', 'named', 'split', 'squares', 'bundles', 'grid', 'flow', 'matrix', 'pack'] as const;
	type WorksLens = (typeof WORKS_LENSES)[number];
	const worksLens = $derived<WorksLens>(
		(WORKS_LENSES as readonly string[]).includes(page.url.searchParams.get('works') ?? '')
			? (page.url.searchParams.get('works') as WorksLens)
			: 'category'
	);
	// the flow: categories (left, € on the node) → works named (right, counts)
	const CAT_GREYS = ['#1f1f1f', '#3c3c3c', '#595959', '#767676', '#8f8f8f', '#a8a8a8', '#bdbdbd', '#d0d0d0'];
	const worksFlow = $derived.by(() => {
		const cats = [...o.categories].sort((a, b) => b.eur - a.eur);
		const nodes = [
			...cats.map((c, i) => ({
				id: 'c:' + c.key,
				label: c.label_en ?? c.label,
				side: 'l' as const,
				n: c.n,
				eur: c.n,
				color: CAT_GREYS[Math.min(i, CAT_GREYS.length - 1)]
			})),
			...o.themes.themes.map((w) => ({ id: 'w:' + w.theme, label: w.label_en, side: 'r' as const, n: w.n, eur: w.n, color: '#3a3a3a' })),
			...(o.themes.unspecified ? [{ id: 'w:none', label: 'no specific work named', side: 'r' as const, n: o.themes.unspecified, eur: o.themes.unspecified, color: '#9b9b9b' }] : [])
		];
		const links = [
			...cats.flatMap((c) => (c.names ?? []).map((w) => ({ s: 'c:' + c.key, t: 'w:' + w.theme, n: w.n, eur: w.n }))),
			...cats.filter((c) => c.n - (c.n_named ?? 0) > 0).map((c) => ({ s: 'c:' + c.key, t: 'w:none', n: c.n - (c.n_named ?? 0), eur: c.n - (c.n_named ?? 0) }))
		];
		return { nodes, links };
	});
	const matrixCats = $derived(
		[...o.categories]
			.sort((a, b) => b.eur - a.eur)
			.map((c) => ({ key: c.key, label: c.label_en ?? c.label, n: c.n, eur: c.eur, n_named: c.n_named ?? 0, names: (c.names ?? []).map((w) => ({ theme: w.theme, n: w.n })) }))
	);
	const matrixWorks = $derived(o.themes.themes.map((w) => ({ theme: w.theme, label: w.label_en })));
	// works as ROWS, each split by the main category of the contracts naming
	// it (user, 2026-08-22: the work names are long, so they must be labels)
	const catGrey = $derived.by(() => {
		const m = new Map<string, string>();
		[...o.categories]
			.sort((a, b) => b.eur - a.eur)
			.forEach((c, i) => m.set(c.key, CAT_GREYS[Math.min(i, CAT_GREYS.length - 1)]));
		return m;
	});
	const catShort = $derived(
		new Map(o.categories.map((c) => [c.key, (c.label_en ?? c.label).split(' — ')[0]]))
	);
	const worksSplit = $derived.by(() => {
		const rows = o.themes.themes.map((w) => ({
			theme: w.theme,
			label: w.label_en,
			n: w.n,
			by: [...o.categories]
				.map((c) => ({
					key: c.key,
					label: catShort.get(c.key) ?? c.key,
					n: (c.names ?? []).find((x) => x.theme === w.theme)?.n ?? 0
				}))
				.filter((s) => s.n > 0)
				.sort((a, b) => b.n - a.n)
		}));
		if (o.themes.unspecified)
			rows.push({
				theme: '_none',
				label: 'no specific work named',
				n: o.themes.unspecified,
				by: [...o.categories]
					.map((c) => ({
						key: c.key,
						label: catShort.get(c.key) ?? c.key,
						n: c.n - (c.n_named ?? 0)
					}))
					.filter((s) => s.n > 0)
					.sort((a, b) => b.n - a.n)
			});
		return rows;
	});
	const catRows = $derived(
		[...o.categories]
			.sort((a, b) => b.eur - a.eur)
			.map((c) => ({
				label: c.label_en ?? c.label,
				value: c.eur,
				// the hover: the contract count and what this category's
				// contracts NAME, from the themes layer
				title:
					`${c.label_en ?? c.label} — ${grInt(c.n)} contracts` +
					(c.names?.length
						? `. Works named: ${c.names.map((w) => `${w.label_en.toLowerCase()} ${grInt(w.n)}`).join(', ')}`
						: '')
			}))
	);
	// the reverse link: under each work, the main categories of the contracts
	// that name it — from the categories' own `names` lists, inverted (user,
	// 2026-08-22: the two lenses must show their connection both ways)
	const themeCats = $derived.by(() => {
		const m = new Map<string, { label: string; n: number }[]>();
		for (const c of o.categories)
			for (const w of c.names ?? []) {
				const arr = m.get(w.theme) ?? [];
				arr.push({ label: (c.label_en ?? c.label).split(' — ')[0], n: w.n });
				m.set(w.theme, arr);
			}
		for (const arr of m.values()) arr.sort((a, b) => b.n - a.n);
		return m;
	});
	const themeRows = $derived([
		...o.themes.themes.map((w) => ({
			label: w.label_en,
			value: w.n,
			title:
				`${w.label_en} — ${grInt(w.n)} contracts name it` +
				(themeCats.get(w.theme)?.length
					? `. Main category of those contracts: ${themeCats
							.get(w.theme)!
							.map((c) => `${c.label.toLowerCase()} ${grInt(c.n)}`)
							.join(', ')}`
					: '')
		})),
		...(o.themes.unspecified
			? [
					{
						label: 'fire protection — no specific work named',
						value: o.themes.unspecified,
						title: `${grInt(o.themes.unspecified)} contracts say only «αντιπυρική προστασία»`
					}
				]
			: [])
	]);
	const topCat = $derived(
		o.categories.reduce((a, b) => (b.eur > a.eur ? b : a), o.categories[0])
	);
	// hero bar fills — both data-proportional
	const bidPct = $derived((o.kpis.n_single_bidder / o.kpis.n_contracts) * 100);
	// what kind of σύμβαση each in-scope record is: computed from the payload,
	// never typed. The supplementary works are one phenomenon in two document
	// forms — the supplementary contract itself and the decision approving one
	// — so they are stated as one number (DATA_DECISIONS 2026-08-18).
	const dk = $derived.by(() => {
		const c = o.document_kinds?.counts ?? {};
		return {
			total: o.document_kinds?.total ?? 0,
			n_kinds: Object.keys(c).length,
			contract: c.contract ?? 0,
			amendment: c.amendment ?? 0,
			supplementary:
				(c.supplementary_contract ?? 0) +
				(c.approval_ape_supplementary ?? 0) +
				(c.approval_supplementary ?? 0),
			extension: c.approval_schedule_extension ?? 0
		};
	});
	const paidPct = $derived((o.kpis.paid_eur / o.kpis.stated_eur) * 100);
</script>

<svelte:head>
	<title>Anti-nero — where the wildfire-prevention money went</title>
	<meta
		name="description"
		content="Interactive audit of Greece's Anti-nero wildfire-prevention programme: {grInt(
			o.kpis.n_contracts
		)} contracts, {eurShort(o.kpis.total_eur)} stated (excl. VAT)."
	/>
</svelte:head>

<div class="antp">
<section class="hero">
	<div class="heroleft">
	<div class="cards">
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contracts)}</div>
			<div class="lbl">in-scope contracts</div>
		</div>
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contractors)}</div>
			<div class="lbl">contractors</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(o.kpis.stated_eur).toLowerCase()}</div>
			<div class="lbl">
				total stated value of contracts<br />(excl. VAT)
			</div>
		</div>
	</div>
	<div class="midcol">
		<div class="bars">
			<div class="dabar" role="img" aria-label="Share of contracts awarded directly">
				<div class="track">
					<div class="fill" style:width={`${o.kpis.pct_direct}%`}>
						<div class="danum">{pct(o.kpis.pct_direct)}</div>
						<div class="datext">of contracts were direct awards</div>
					</div>
				</div>
			</div>
			<div class="bidbar" role="img" aria-label="Contracts that drew exactly one bid">
				<div class="track">
					<div class="bfill" style:width={`${bidPct}%`}>{grInt(o.kpis.n_single_bidder)}</div>
					<div class="btext">contracts drew <strong>1 bid</strong></div>
				</div>
			</div>
		</div>
		<div class="paidcard" role="img" aria-label="Paid so far, as a share of the stated total">
			<div class="pfill" style:height={`${paidPct}%`}>
				<div class="pnum">{eurShort(o.kpis.paid_eur).toLowerCase()}</div>
				<div class="plbl">already paid</div>
			</div>
		</div>
	</div>
	</div>
	<div class="about">
		<div class="kicker">THE PROGRAMME</div>
		<p>
			Greece's flagship wildfire-prevention programme (ΥΠΕΝ, RRF Action 16849) has signed
			{grInt(o.kpis.n_contracts)} contracts since {o.yearly[0]?.year ?? '2022'} — of the
			{eurShort(o.kpis.stated_eur)} stated, {eurShort(o.kpis.paid_eur)} has actually been paid
			({grInt(o.kpis.n_payments)} payment orders). {pct(o.kpis.pct_direct)} of contracts —
			{eurShort(directEur)}, the bulk of the money — went by direct award, and {grInt(
				o.kpis.n_single_bidder
			)} contracts drew exactly one bid. This page follows what actually got paid, to whom,
			and where — <a href="/methodology#antinero">methodology</a>.
		</p>
		{#if dk && dk.n_kinds > 0}
			<p class="kinds">
				All {grInt(dk.total)} are συμβάσεις, which is what the registry files them as; the
				kind says which. {grInt(dk.contract)} are original contracts,
				{grInt(dk.amendment)} revise the terms of one without touching its price,
				{grInt(dk.supplementary)} add supplementary works, and {grInt(dk.extension)}
				only extend a deadline —
				<a href="/methodology#record-kinds">what each record is</a>.
			</p>
		{/if}
		{#if o.probable && o.probable.n > 0}
			<details class="probable">
				<summary>
					+ {grInt(o.probable.n)} additional contracts found ({eurShort(
						o.probable.total_eur
					).toLowerCase()} excl. VAT), probably related to the Antinero programme, but not
					included in the calculations
				</summary>
				<p class="pnote">
					Their signed documents carry no provable RRF-16849 financing evidence — no fund
					code, no Ταμείο Ανάκαμψης clause (<a href="/methodology#antinero">methodology</a>).
				</p>
				<ul>
					{#each o.probable.rows as r (r.ref)}
						<li>
							<a href={`/antinero/contract/${r.ref}`}>{r.ref}</a>
							{#if r.d}<span class="pd">{r.d}</span>{/if}
							<span class="pt">{r.title}</span>
						</li>
					{/each}
				</ul>
			</details>
		{/if}
	</div>
</section>

{#if map}
	<ChartFrame
		title="ALLOCATION OF FUNDING"
		insight="{grInt(map.contracts.filter((c) => (c.regions?.length ?? 0) > 1).length)} of the {grInt(
			map.contracts.length
		)} contracts cover more than one regional unit, and the documents state no allocation of the money between the units a contract covers. So each contract's value is split equally between its regions and, for a jointly signed contract, between its partners. A region's figure is the sum of those equal shares, and the regions add up to the programme total."
		caveat="Stated € excl. VAT. A contract covering several regional units, or signed by several firms, is split equally between them — the documents state no other allocation (the lightbulb beside the title explains)."
		anchor="map"
		methodology="even-split"
	>
		<AntineroMap data={map} />
	</ChartFrame>
{:else}
	<div class="skeleton" id="map" style="height: 560px"></div>
{/if}

{#if net}
	{@const maxReach = (() => {
		const by = new Map<string, number>();
		for (const e of net.contractor_pe) by.set(e.vat, (by.get(e.vat) ?? 0) + 1);
		let top = { vat: '', n: 0 };
		for (const [vat, n] of by) if (n > top.n) top = { vat, n };
		return { n: top.n, name: net.contractors[top.vat]?.name ?? '—' };
	})()}
	{@const localPct = (() => {
		let t = 0,
			l = 0;
		for (const f of net.flows) {
			t += f.total_eur;
			if (f.source_pe === f.target_pe) l += f.total_eur;
		}
		return t ? Math.round((100 * l) / t) : 0;
	})()}
	<ChartFrame
		title="WHERE THE MONEY TRAVELS"
		insight="Each regional unit is coloured according to the share of works carried out within it that are awarded to contractors based either within or outside its boundaries. The darker the regional unit, the larger the share of works awarded to companies based outside its boundaries. Only {localPct}% of the money is awarded to companies based within the regional unit where the works are carried out. Switch to «by company» for the same flows broken down to the firms that carry them: {grInt(net.contractor_pe.length)} contractor ↔ work-region links across {grInt(Object.keys(net.contractors).length)} contractors — {maxReach.name} alone works in {maxReach.n} regional units; a unit focused on the map arrives selected in the lists, and a company selected there focuses the map on its home region."
		caveat="Geocoded contractors only — {eurShort(net.coverage.resolved_eur)} of {eurShort(
			net.coverage.total_eur
		)} resolved. Same reading as the map above: a contract covering several regional units, or signed by several firms, is split equally between them, because the documents state no other allocation — every arrow carries the shares that connect a firm's base to a work region, and the flows add up to the programme total. The company lens draws the same shares as contractor ↔ region links; at rest each column lists its biggest rows, selecting one reshuffles the other column to exactly its counterparts."
		anchor="flows"
		methodology="even-split"
	>
		<FlowMap
			flows={net.flows}
			flowsYearly={net.flows_yearly}
			{centroids}
			origins={net.origins}
			edges={net.contractor_pe}
			contractors={net.contractors}
		/>
	</ChartFrame>
{/if}

<ChartFrame
	title="RANKING OF COMPANIES"
	insight={rankMode === 'firm'
		? `The same money attributed to the firms BEHIND the joint ventures — ${grInt(
				o.consortiums.n_documented
			)} of the ${grInt(o.consortiums.n)} ventures have members on record, ${grInt(
				o.consortiums.n_firms
			)} firms in all. A joint venture whose members are on record is replaced by them and its € split evenly; one whose members no document names keeps its own row, so ${eurShort(
				o.consortiums.eur_unsplit
			)} sits identically in both views. Both views add up to the programme total.`
		: `Companies ranked by the sums contracted to them through the programme — the top ${topRows.length} of ${grInt(
				o.kpis.n_contractors
			)} contractors, ${eurShort(o.kpis.total_eur)} in total. Each contract is counted once: a jointly signed one is split evenly between its partners, so the totals add up to the programme total. Switch to «by member firm» to attribute the money to the firms behind the joint ventures.`}
	caveat={rankMode === 'firm'
		? `A joint venture whose members are on record is replaced by them and its € split evenly; one whose members no document names keeps its own row, so ${eurShort(
				o.consortiums.eur_unsplit
			)} sits identically in both views. Both add up to the programme total.`
		: 'Each contract is counted once: a jointly signed one is split evenly between its partners, so these totals add up to the programme total.'}
	anchor="top-contractors"
	methodology={rankMode === 'firm' ? 'joint-contracts' : 'stated-basis'}
>
	<!-- the view toggle where the maps' bars put theirs — right-aligned on
	     its own line under the title, no label (user, 2026-08-21) -->
	<div class="rankbar">
		<SegmentToggle param="rank" fallback="party" options={RANK_MODES} />
	</div>
	<!-- same measure and bar height as the sponsored-works ranking, so the
	     two datasets' rankings read alike; the bars stay black, this
	     dataset's colour (user, 2026-08-20) -->
	<div class="rankw">
		<BarH rows={topRows} color="var(--c-antinero)" inside barHeight={30} />
	</div>
</ChartFrame>

<Defer height={340}>
{#if swarm}
	<ChartFrame
		title="CONTRACT VALUES"
		caveat="Both views draw the same contracts from one list, on one axis: every bracket spans a doubling of value, which makes the equal-width slots a logarithmic scale, and the dots sit on that same scale — so a value is at the same place in both, the median line included. Greys are the signature year in both. The ν.4782/2021 ceilings are defined on the excl-VAT estimated value — the same basis; RRF emergency provisions allowed direct awards above them."
		anchor="swarm"
		methodology="stated-basis"
	>
		{#if swarmCols}
			<div class="modes">
				<div class="vlegend">
					{#each swarmYears as y (y)}
						<span><i style:background={YEAR_GREYS[y]}></i>{y}</span>
					{/each}
				</div>
				<div class="mode" role="group" aria-label="Contract-value chart mode">
					<button
						type="button"
						class:active={valueMode === 'dots'}
						onclick={() => (valueMode = 'dots')}>Individual dots</button
					>
					<button
						type="button"
						class:active={valueMode === 'brackets'}
						onclick={() => (valueMode = 'brackets')}>Value brackets</button
					>
				</div>
			</div>
			<SideNote note={VALUE_NOTES[valueMode]}>
				{#if valueMode === 'dots'}
					<BeeswarmCanvas
						data={swarmCols}
						edges={o.value_histogram.edges}
						colors={yearGrey}
						thresholds={miniThresholds}
						linkBase="/antinero/contract/"
						minHeight={380}
						radius={3.1}
						bind:plotHeight={dotsHeight}
					/>
				{:else}
					<LogHistogram
						labels={o.value_histogram.labels}
						counts={o.value_histogram.counts}
						edges={o.value_histogram.edges}
						color="var(--c-antinero)"
						median={o.value_histogram.median}
						height={dotsHeight || 460}
						note={false}
						segments={yearSegments}
						segColors={swarmYears.map((y) => YEAR_GREYS[y])}
						thresholds={miniThresholds}
					/>
				{/if}
			</SideNote>
		{/if}
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 320px"></div>
{/if}
</Defer>

<Defer height={640}>
{#if network}
	<ChartFrame
		title={netCopy.title}
		subtitle={netCopy.subtitle}
		caveat="{netCopy.caveat} Circle area is the contract's stated value excl. VAT, on one scale in every arrangement; a call is the πρόσκληση the contract cites in its own signed text ({grInt(
			network.stats.n_calls
		)} resolved this way). Every layout is deterministic, not a force simulation."
		anchor="network"
		methodology="procurement-families"
	>
		<div class="netbar">
			<SegmentToggle param="net" fallback="time" options={NET_MODES} />
		</div>
		<ContractNetwork
			nodes={network.nodes}
			stats={network.stats}
			mode={netMode}
			season={network.fire_season}
		/>
	</ChartFrame>
{:else}
	<div class="skeleton" id="network" style="height: 620px"></div>
{/if}
</Defer>

<Defer height={900}>
{#if payments}
	<ChartFrame
		title="PAYMENTS TIMELINE"
		subtitle="One tick per payment order ({grInt(payments.events.length)}), height ∝ √€, by programme phase — the biggest single month was {peak.m} ({eurShort(
			peak.eur
		)}). Hover for the order, click through to the contract."
		caveat="{grInt(
			payments.fallback
		)} of {grInt(payments.events.length)} orders carry no signature date — the registry submission date is shown for those{payments
			.undated.n
			? `; ${grInt(payments.undated.n)} remain undated (${eurShort(payments.undated.eur)})`
			: ''}."
		anchor="payments"
		methodology="payment-dates"
	>
		<StripTimeline data={payments} />
	</ChartFrame>

	<ChartFrame
		title="CUMULATIVE DISBURSEMENT"
		subtitle="Cumulative € of payment orders since {firstPayYear} — stacked by phase, or same-point-in-year comparison."
		caveat="Payment orders attributed to a contract's final version; registry net-of-ΦΠΑ amounts."
		anchor="disbursement"
		methodology="stated-basis"
	>
		<DisbursementCurves timeseries={o.timeseries} {payments} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 480px"></div>
	<div class="skeleton" style="height: 400px"></div>
{/if}
</Defer>

<Defer height={620}>
{#if unitFlow}
	{@const uf = unitFlow}
	<!-- two columns, no phase (user, 2026-08-21): the ΥΠΕΝ unit that signed on
	     the left, the ten biggest contractors + everyone else on the right;
	     units in greys (ribbons take the unit's tone), the ΔΑΣΕ drawing -->
	{@const UNIT_GREYS = ['#1f1f1f', '#5a5a5a', '#8a8a8a', '#b4b4b4', '#d0d0d0']}
	<!-- three columns, as the forest co-op diagram (user, 2026-08-22, for
	     comparability): the awarding body — the Ministry, one node — → its
	     operating units → contractors -->
	{@const unitNodes = uf.nodes.map((n, i) => ({
		...n,
		side: (n.side === 'l' ? 'm' : n.side) as 'l' | 'm' | 'r',
		label: n.side === 'l' ? unitEn(n.label) : n.label,
		color: n.side === 'l' ? UNIT_GREYS[Math.min(i, UNIT_GREYS.length - 1)] : n.id === 'rest' ? '#9b9b9b' : '#3a3a3a'
	}))}
	{@const ufNodes = [
		{
			id: 'ministry',
			label: 'Ministry of Environment & Energy',
			side: 'l' as const,
			n: uf.nodes.filter((n) => n.side === 'l').reduce((s, n) => s + n.n, 0),
			eur: uf.total_eur,
			color: '#111111'
		},
		...unitNodes
	]}
	{@const ufLinks = [
		...uf.nodes.filter((n) => n.side === 'l').map((n) => ({ s: 'ministry', t: n.id, n: n.n, eur: n.eur })),
		...uf.links
	]}
	<ChartFrame
		title="MONEY FLOW"
		insight="The awarding body of every Anti-nero contract is the Ministry of Environment and Energy; the operating units on the left are the {grInt(uf.n_units)} units of the Ministry that ran the contracts, as the registry records them. The ribbons carry each unit’s money to the {grInt(uf.n_top)} biggest contractors, everyone else pooled in one node — {eurShort(uf.top_eur)} of the {eurShort(uf.total_eur)} ends at those {grInt(uf.n_top)} companies ({grInt(uf.n_contractors)} contractors in all). Ribbon width is stated € excl. VAT; hover a bar for its contract count, click a contractor for its page. The forest co-op page draws the same three columns for its own awarding bodies."
		caveat="Consortium values split evenly between partners here, so both columns sum to the programme total."
		anchor="sankey"
		methodology="even-split"
	>
		<!-- centred: equal margins either side; the unit names wrap at 34
		     characters and the nodes are padded so a three-line name clears
		     its neighbour -->
		<KindFlow
			nodes={ufNodes}
			links={ufLinks}
			height={620}
			headings={['awarding body', 'operating units', 'contractors']}
			marginLeft={170}
			marginRight={330}
			wrapLeft={18}
			wrapMid={28}
		/>
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 560px"></div>
{/if}
</Defer>

<div class="pair">
	<ChartFrame
		title="DIRECT AWARDS"
		subtitle="{grInt(
			o.direct_awards.n as number
		)} direct-award contracts by stated value (excl. VAT) — they pile up around €{daModal}, far beyond the ν.4782/2021 ceilings."
		caveat="The statutory ceilings and these values are both excl. VAT; RRF emergency provisions allowed direct awards above the ceilings."
		anchor="direct-awards"
		methodology="procedures"
	>
		<LogHistogram
			labels={o.direct_awards.labels as string[]}
			counts={o.direct_awards.counts as number[]}
			edges={o.direct_awards.edges as number[]}
			color="var(--c-antinero)"
			thresholds={miniThresholds}
		/>
	</ChartFrame>

	<ChartFrame
		title="AWARD PROCEDURES"
		subtitle="Stated € by award procedure — open procedures are the exception, not the rule."
		anchor="procedures"
	>
		<BarH rows={procRows} color="var(--c-antinero)" highlight={(r) => r.label.includes('Απευθείας')} />
	</ChartFrame>
</div>

<Defer height={400}>
{#if peYearly}
	<ChartFrame
		title="MONEY BY REGION PER YEAR"
		subtitle="Yearly stated € per regional unit (top {Math.min(
			20,
			peYearly.pes.length
		)}, same scale). Click a facet to drill into it on the map."
		caveat="Even-split attribution; stated € at signature year."
		anchor="pe-yearly"
		methodology="even-split"
	>
		<SmallMultiples data={peYearly} hrefOf={(pe) => `/?focus=works:${encodeURIComponent(pe)}#map`} />
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 380px"></div>
{/if}
</Defer>

<ChartFrame
	title="STUDY COSTS"
	subtitle="The ten largest study (μελέτη) costs extracted from the signed PDFs — the median is {pct(
		(o.studies.summary.median_share as number) * 100
	)} of a contract's net value; {grInt(o.studies.summary.n_with)} of {grInt(
		o.studies.summary.n_in_scope
	)} contracts state one, {eurShort(o.studies.summary.total_eur)} in total."
	caveat="ΕΣΑ design-build contracts bundle the study into the works price and honestly state none."
	anchor="studies"
	methodology="study-costs"
>
	<BarH rows={studyRows} color="#8f8f8f" />
</ChartFrame>

{#if o.categories.length && topCat}
	{@const works = o.themes}
	<!-- two lenses (user, 2026-08-22): «main category» — one per contract,
	     € or count, sums to the total, each bar saying which works its
	     contracts name — / «works named» — the themes, counted in contracts,
	     the unspecified ones as their own bar, no € -->
	<ChartFrame
		title="TYPES OF WORK"
		insight={worksLens === 'named'
			? `What the contracts say they do, read from the project title inside each signed PDF: one bar per kind of work, counted in contracts — a contract counts under every work its title names, so the bars overlap and carry no € (the documents state no price per work inside a bundled contract). ${grInt(works.unspecified)} of the ${grInt(works.n_contracts)} contracts name no specific work beyond «αντιπυρική προστασία» and stand as their own bar.`
			: worksLens === 'split' || worksLens === 'squares'
				? `One row per work the signed titles name — the works are what the contracts say they do — and each row split by the MAIN CATEGORY of the contracts naming it${worksLens === 'squares' ? ', one square per contract' : ''}: that is what the one-category-per-contract rule flattens, since a bundled title names several works. A contract appears on every row its title names, so the rows overlap; the contracts naming no specific work are the last row. Counts only — no price per work exists inside a bundled contract.`
			: worksLens === 'bundles'
				? `What the contracts actually do, as their titles say it: one bar per COMBINATION of works named — «firebreaks + clearing + forest roads» is the commonest — with dots underneath saying which works are in each bundle. This is what one category per contract has to flatten: ${grInt(works.n_contracts - works.unspecified - (works.bundles?.filter((b) => b.themes.length === 1).reduce((s, b) => s + b.n, 0) ?? 0))} of the ${grInt(works.n_contracts)} contracts name more than one work. Counts only — no price per work exists inside a bundled contract.`
			: worksLens === 'grid'
				? `One row per main category — one per contract, so its € is honest — one column per work the signed titles name, and a circle whose area is the number of contracts in that pair: the bundles are then the picture, a category’s row showing what its contracts actually do. A contract counts under every work it names, so the columns overlap; the contracts naming no specific work have their own column. Counts, not € — no price per work exists inside a bundled contract.`
			: worksLens === 'flow'
				? `The main category of each contract (left, one per contract, the count on the node) flowing into the works its title names (right): a ribbon’s width is the number of contracts of that category naming that work, so a bundled contract sends one ribbon per work it names; the contracts naming no specific work end in their own node. Counts, not € — no price per work exists inside a bundled contract.`
				: worksLens === 'matrix'
					? `One row per main category, one column per work the titles name, each cell the number of contracts — darker, more — with the contracts naming no specific work in their own column; the row’s count and stated € close it. Reads both ways: what a category’s contracts do, and where a work’s contracts were filed.`
					: worksLens === 'pack'
						? `Every in-scope contract is a circle, area ∝ its stated net €, packed into one bubble per main category, the bubbles packed together, biggest first — the programme chart’s arrangement regrouped by type of work. Hover a bubble for its name, count and €; click a circle for the contract.`
						: `Every in-scope contract assigned ONE curated category from the project title inside its signed PDF (CPV codes only as tie-breaker), so the € columns sum to the programme’s stated-net total — «${topCat.label_en ?? topCat.label}» dominates with ${eurShort(topCat.eur)} across ${grInt(topCat.n)} contracts (${pct((topCat.eur / o.kpis.total_eur) * 100)} of the programme). Hover a bar for the works its contracts actually name.`}
		caveat={worksLens !== 'category' && worksLens !== 'pack'
			? 'Works as named in the signed titles (twelve themes, verbatim clause kept per contract); a contract counts under every work it names, so counts sum to more than the number of contracts and no € is attributed per work. Categories: one per contract, curated from the same titles.'
			: 'One category per contract, curated from the signed PDF’s descriptive project title with the contract’s rarer CPV codes as tie-breaker, so the € columns sum to the programme’s stated-net total.'}
		anchor="categories"
		methodology="categories"
	>
		<div class="rankbar">
			<SegmentToggle
				param="works"
				fallback="category"
				options={[
					{ value: 'category', label: 'main category' },
					{ value: 'named', label: 'works named' },
					{ value: 'split', label: 'works × category' },
					{ value: 'squares', label: 'works × category (squares)' },
					{ value: 'bundles', label: 'bundles' },
					{ value: 'grid', label: 'bubble grid' },
					{ value: 'flow', label: 'flow' },
					{ value: 'matrix', label: 'matrix' },
					{ value: 'pack', label: 'pack' }
				]}
			/>
		</div>
		<!-- the bars as before (label inside, value right); the connection
		     between the two lenses rides in the HOVER of each bar — the works a
		     category's contracts name, the categories a work's contracts fall
		     in — not in printed sub-lines (user, 2026-08-22: too much text) -->
		{#if worksLens === 'named'}
			<BarH rows={themeRows} color="#2b2b2b" inside barHeight={22} fmt={grInt} />
		{:else if worksLens === 'split' || worksLens === 'squares'}
			<div class="catkey">
				{#each [...o.categories].sort((a, b) => b.eur - a.eur) as c (c.key)}
					<span><i style:background={catGrey.get(c.key)}></i>{catShort.get(c.key)}</span>
				{/each}
			</div>
			<WorksByCategory
				rows={worksSplit}
				colorOf={(k) => catGrey.get(k) ?? '#9b9b9b'}
				unit={worksLens === 'squares'}
			/>
		{:else if worksLens === 'bundles'}
			<WorksBundles
				combos={[
					...(o.themes.bundles ?? []),
					...(o.themes.unspecified ? [{ themes: [], n: o.themes.unspecified }] : [])
				]}
				works={o.themes.themes.map((w) => ({ theme: w.theme, label: w.label_en, n: w.n }))}
			/>
		{:else if worksLens === 'grid'}
			<WorksBubbleGrid cats={matrixCats} works={matrixWorks} />
		{:else if worksLens === 'flow'}
			<KindFlow
				nodes={worksFlow.nodes}
				links={worksFlow.links}
				height={620}
				headings={['main category', 'works named']}
				marginLeft={330}
				marginRight={300}
				wrapLeft={34}
				fmt={(v) => `${grInt(v)} contracts`}
			/>
		{:else if worksLens === 'matrix'}
			<WorksMatrix cats={matrixCats} works={matrixWorks} />
		{:else if worksLens === 'pack'}
			{#if swarm}
				<WorksPack rows={swarm} cats={matrixCats} size={560} />
			{:else}
				<div class="skeleton" style="height: 560px"></div>
			{/if}
		{:else}
			<BarH rows={catRows} color="#2b2b2b" inside barHeight={22} fmt={eurShort} />
		{/if}
	</ChartFrame>
{/if}

{#if o.cpvs.length}
	{@const topCpv = o.cpvs[0]}
	<ChartFrame
		title="CPV CODES"
		subtitle="All {grInt(o.cpvs.length)} procurement-vocabulary (CPV) codes declared across the {grInt(
			o.kpis.n_contracts
		)} in-scope contracts, sorted by reach — the most common, «{topCpv.desc}», appears on {grInt(
			topCpv.n
		)} of them ({pct((topCpv.n / o.kpis.n_contracts) * 100)})."
		caveat="Codes and descriptions as declared in ΚΗΜΔΗΣ. Contracts declare several codes each, so counts sum to more than the number of contracts — and for the same reason no € is attributed per code."
		anchor="cpvs"
	>
		<div class="cpvlist">
			{#each o.cpvs as c (c.code)}
				<div class="cpvrow">
					<span class="cn">{grInt(c.n)}</span>
					<span class="cc">{c.code}</span>
					<span class="cd">{c.desc}</span>
				</div>
			{/each}
		</div>
	</ChartFrame>
{/if}

</div>

<style>
	/* the ranking's measure, shared with the sponsored-works page */
	.rankw {
		max-width: 75%;
	}
	@media (max-width: 900px) {
		.rankw {
			max-width: none;
		}
	}
	.modes {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-6);
		flex-wrap: wrap;
		margin: var(--sp-2) 0 var(--sp-4);
	}
	.mode {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
	}
	.mode button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.mode button.active {
		background: var(--ink);
		color: var(--paper);
	}
	.vlegend {
		display: flex;
		gap: var(--sp-4);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.vlegend i {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
		margin-right: 4px;
		vertical-align: -1px;
	}
	.netbar {
		display: flex;
		justify-content: flex-end;
		margin-bottom: var(--sp-2);
	}
	/* black-white-grayscale only on this page (user, 2026-08-20): the
	   reference-line ink follows */
	.antp {
		--c-threshold: #4a4a4a;
	}
	/* every section title follows the sponsored-works kicker, in the
	   antinero dataset colour (black) */
	.antp :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-antinero);
	}
	/* the two paper maps take the sponsored-works ground */
	.antp :global(.map) {
		background: #f2f2f2;
		border: none;
		box-shadow: none;
	}
	/* two card slots (user, 2026-08-21): the place's card grey, top-left;
	   the item's card black, bottom-left, carrying its link */
	.antp :global(.map .tip.item) {
		pointer-events: auto; /* the card carries the item's link */
	}
	.antp :global(.map .tip a) {
		color: #fff;
		text-decoration: underline;
	}
	.antp :global(.map .tip .tip-rule) {
		border: 0;
		border-top: 1px solid rgba(255, 255, 255, 0.35);
		margin: 4px 0;
	}
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	/* cards column + the bars/paid column beside it */
	.heroleft {
		/* the two columns split the first map's span equally:
		   160 + 268 + 16 + 268 = 712 = the left map's right edge at the
		   1440 design width */
		display: grid;
		grid-template-columns: 268px 268px;
		gap: var(--sp-4);
		align-items: stretch;
	}
	.cards {
		/* three equal rows — every card the height of the tallest */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	/* middle column mirrors the cards grid: the two bars share the first
	   card's row (equal heights + the gap between), the paid card fills
	   the third row so it matches the stated-value card exactly */
	.midcol {
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	.bars {
		grid-row: 1;
		display: grid;
		grid-template-rows: 1fr 1fr;
		gap: var(--sp-4);
	}
	.dabar .track,
	.bidbar .track {
		height: 100%;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
	}
	.dabar .fill {
		height: 100%;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 2px;
		padding: 0 14px;
	}
	.dabar .danum {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		line-height: 1;
	}
	.dabar .datext {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-12);
		line-height: 1.2;
	}
	.bidbar .track {
		display: flex;
		align-items: center;
	}
	.bidbar .bfill {
		height: 100%;
		min-width: 40px;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		flex: 0 0 auto;
	}
	.bidbar .btext {
		padding-left: 10px;
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		white-space: nowrap;
	}
	.bidbar .btext strong {
		font-weight: 900;
	}
	/* paid vs stated: black fill rises to the paid share of the stated €;
	   the unfilled remainder reads as light grey, no outer border */
	.paidcard {
		grid-row: 3;
		position: relative;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
	}
	.paidcard .pfill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--c-antinero);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 2px;
		padding: 8px 14px 10px;
	}
	.paidcard .pnum {
		font-family: var(--font-display);
		font-weight: 900;
		/* matches the card numbers' 36px cap; fits the 268px card */
		font-size: 36px;
		line-height: 0.95;
		white-space: nowrap;
	}
	.paidcard .plbl {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	@media (max-width: 900px) {
		.heroleft {
			grid-template-columns: 268px;
		}
		.midcol {
			grid-template-rows: auto;
		}
		.bars,
		.paidcard {
			grid-row: auto;
		}
		.paidcard {
			height: 117px;
		}
	}
	.card {
		background: var(--c-antinero);
		color: #fff;
		padding: var(--sp-4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	.card .num {
		font-family: var(--font-display);
		font-weight: 900;
		/* 36px is the largest size at which the stated € fits a 268px card */
		font-size: clamp(28px, 3.2vw, 36px);
		line-height: 0.95;
	}
	.card .lbl {
		font-family: var(--font-display);
		font-weight: 400; /* Obviously Regular */
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--c-antinero);
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	.about p.kinds {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-faint);
	}
	.probable {
		margin-top: var(--sp-4);
		max-width: var(--prose-w);
		font-size: var(--fs-13);
		color: var(--ink-faint);
	}
	.probable summary {
		cursor: pointer;
	}
	.probable .pnote {
		margin: var(--sp-2) 0 0;
		font-size: var(--fs-13);
	}
	.probable ul {
		margin: var(--sp-2) 0 0;
		padding-left: 1.2em;
	}
	.probable li {
		margin-bottom: 2px;
	}
	.probable .pd {
		margin-left: 0.5em;
	}
	.probable .pt {
		margin-left: 0.5em;
	}
	@media (max-width: 900px) {
		.hero {
			grid-template-columns: 1fr;
		}
	}
	.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-6);
	}
	@media (max-width: 900px) {
		.pair {
			grid-template-columns: 1fr;
		}
	}
	.mode {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
		margin-bottom: var(--sp-2);
	}
	.mode button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.mode button.active {
		background: var(--ink);
		color: var(--paper);
	}
	.cpvlist {
		columns: 3 300px;
		column-gap: var(--sp-6);
		font-size: var(--fs-13);
	}
	.cpvrow {
		display: flex;
		gap: 0.5em;
		align-items: baseline;
		break-inside: avoid;
		padding: 2px 0;
		border-bottom: 1px solid var(--paper-3);
	}
	.cn {
		min-width: 2.2em;
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
	.cc {
		color: var(--ink-faint);
		font-size: var(--fs-12);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.cd {
		color: var(--ink-soft);
	}
	.rankbar {
		display: flex;
		justify-content: flex-start;
		align-items: center;
		gap: var(--sp-4);
		margin-bottom: var(--sp-2);
	}
	/* the category key of the works × category lenses */
	.catkey {
		display: flex;
		flex-wrap: wrap;
		gap: 4px var(--sp-4);
		font-size: var(--fs-12);
		color: var(--ink-soft);
		margin-bottom: var(--sp-3);
	}
	.catkey span {
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}
	.catkey i {
		display: inline-block;
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}
</style>
