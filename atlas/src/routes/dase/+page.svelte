<script lang="ts">
	import { bodyEn, devGreek } from '$lib/transforms/names';
	import { peEn, pesOfRegion, regionOfPe, ruLabel } from '$lib/transforms/regions';
	import BarH from '$lib/charts/BarH.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import KindFlow, { type FlowLink, type FlowNode } from '$lib/charts/KindFlow.svelte';
	import { YEAR_COLORS } from '$lib/charts/yearColors';
	import { binByKey } from '$lib/transforms/histogram';
	import FiresLayer from '$lib/maps/FiresLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { loadEffisFires, makeChoro, RAMP_DASE, type FireProps } from '$lib/maps/useGeo';
	import { CARD_BOUNDS } from '$lib/maps/cardFrame';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import DatasetCard from '$lib/ui/DatasetCard.svelte';
	import Tile from '$lib/ui/Tile.svelte';
	import Text from '$content/datasets/dase.md';
	import CpvColumns from '$lib/charts/CpvColumns.svelte';
	import DaseMap from '$lib/sections/DaseMap.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import SideNote from '$lib/ui/SideNote.svelte';
	import {
		apiGetCached,
		type DaseAllocation,
		type DaseMapContract,
		type DaseMapPayload,
		type DaseSwarm
	} from '$lib/api';
	import { bracket, eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import { procedureEn } from '$lib/transforms/procedures';
	import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson';
	import type { PageData } from './$types';
	import RefreshLine from '$lib/ui/RefreshLine.svelte';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	// the card (user mock, 2026-08-27): three KPIs, the URL parameters this
	// page reads (any opens the card unfolded), the map tile's size
	const PARAMS = ['focus'] as const;
	/** the three KPI cards in the Anti-nero card's dress (user, 2026-08-28):
	 *  every number from the payload, the years read off the yearly series */
	const kpiRich = $derived([
		{
			w: 238.6,
			parts: [{ num: grInt(o.kpis.n_contracts), word: 'contracts' }],
			lines: [
				'live contracts in the registry,',
				`signed between ${o.yearly[0]?.year ?? ''} and ${o.yearly[o.yearly.length - 1]?.year ?? ''}`
			]
		},
		{
			w: 220.6,
			parts: [{ num: grInt(o.kpis.n_coops), word: 'co-operatives' }],
			lines: ['forest labour co-operatives', 'that signed the contracts']
		},
		{
			w: 220.6,
			parts: [{ num: eurShort(o.kpis.total_eur).toLowerCase() }],
			lines: ['total stated value of contracts', '(excl. VAT)']
		}
	]);
	let tileW = $state(0);
	let tileH = $state(0);
	/** the card map's two lenses (the Anti-nero card's treatment, user
	 *  2026-08-28): € by the awarding forest service's regional unit, or
	 *  by the co-operatives' registered offices */
	let allocKind = $state<'work' | 'home'>('work');
	const allocChoro = $derived.by(() => {
		if (!alloc) return null;
		const rows = allocKind === 'work' ? alloc.work_regions : alloc.seat_regions;
		const by = new Map(rows.map((r) => [r.pe, r.eur]));
		const max = Math.max(1, ...rows.map((r) => r.eur));
		return { by, max };
	});
	const cardChoro = $derived(makeChoro(RAMP_DASE, allocChoro?.max ?? 0));
	/** the drill: a περιφέρεια with money in the current lens answers a
	 *  click, the map zooms to it, any click while zoomed returns */
	let selDase = $state<string | null>(null);
	const selDasePes = $derived(selDase ? pesOfRegion(selDase) : null);
	const regionEur = $derived.by(() => {
		const m = new Map<string, number>();
		if (!allocChoro) return m;
		for (const [pe, v] of allocChoro.by) {
			const r = regionOfPe(pe);
			if (r && v > 0) m.set(r, (m.get(r) ?? 0) + v);
		}
		return m;
	});
	/** the card map's frame: the shared card frame slid 0,264° west and a
	 *  degree wider there, as on the Anti-nero card, so the title, the
	 *  toggle and the key have the left */
	const ALLOC_SHIFT = 0.264;
	const ALLOC_WEST = 0.5;
	const ALLOC_BOUNDS: [[number, number], [number, number]] = [
		[CARD_BOUNDS[0][0] - ALLOC_SHIFT - ALLOC_WEST, CARD_BOUNDS[0][1]],
		[CARD_BOUNDS[1][0] - ALLOC_SHIFT, CARD_BOUNDS[1][1]]
	];
	let valH = $state(0);
	/** MONEY PER YEAR in the ranking's slot: the six bars share the tile's
	 *  height, 35 px each at most (the full frame's own), the rest in the gaps */
	let moneyH = $state(0);
	const MONEY_GAP = 3.3;
	const moneyBar = $derived.by(() => {
		const n = Math.max(1, o.yearly.length);
		return Math.max(10, Math.min(35, (moneyH - (n - 1) * MONEY_GAP) / n));
	});
	const moneyGap = $derived.by(() => {
		const n = Math.max(1, o.yearly.length);
		return n > 1 ? Math.max(MONEY_GAP, (moneyH - n * moneyBar) / (n - 1)) : MONEY_GAP;
	});

	let swarm = $state.raw<DaseSwarm | null>(null);
	let dmap = $state.raw<DaseMapPayload | null>(null);
	let alloc = $state.raw<DaseAllocation | null>(null);
	let firesFc = $state.raw<FeatureCollection<Polygon | MultiPolygon, FireProps> | null>(null);
	$effect(() => {
		apiGetCached<DaseSwarm>(fetch, '/api/dase/swarm').then((v) => (swarm = v));
		apiGetCached<DaseMapPayload>(fetch, '/api/dase/map').then((v) => (dmap = v));
		apiGetCached<DaseAllocation>(fetch, '/api/dase/allocation').then((v) => (alloc = v));
		loadEffisFires(fetch).then((v) => (firesFc = v));
	});

	// the dataset starts Sept 2021 — salvage logging follows these burns
	const FIRES_FROM = 2021;
	const firesShown = $derived(
		firesFc ? firesFc.features.filter((f) => f.properties.yr >= FIRES_FROM) : []
	);

	// one mark per awarding unit + per-Π.Ε. circles for municipal/regional
	// government and for other public bodies, largest drawn first so small
	// circles stay clickable on top
	type MapPt = {
		name: string;
		pe: string | null;
		lat: number;
		lon: number;
		n: number;
		eur: number;
		median_eur: number;
		contracts: DaseMapContract[];
		kindKey: 'dx' | 'dd' | 'muni' | 'misc';
	};
	const mapPts = $derived.by<MapPt[]>(() => {
		if (!dmap) return [];
		return [
			...dmap.units.map((u) => ({
				...u,
				kindKey: (u.kind === 'dd' ? 'dd' : 'dx') as MapPt['kindKey']
			})),
			...dmap.other.map((g) => ({
				...g,
				name:
					g.kind === 'muni'
						? `Municipal & regional awarders · ${ruLabel(g.pe)}`
						: `Other public bodies · ${ruLabel(g.pe)}`,
				kindKey: g.kind as MapPt['kindKey']
			}))
		].sort((a, b) => b.eur - a.eur);
	});
	// works-ramp greens per the approved legend mock: dark for the
	// Διευθύνσεις Δασών, light for the Δασαρχεία; black for municipal &
	// regional government, grey for every other public body
	const KIND_COLOR: Record<MapPt['kindKey'], string> = {
		dd: 'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black)',
		dx: 'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 75%, white) 87%, black)',
		muni: 'var(--ink)',
		misc: 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))'
	};
	const KIND_LABEL: Record<MapPt['kindKey'], string> = {
		dd: 'forest directorate',
		dx: 'local forest service office',
		muni: 'regional or municipal authority',
		misc: 'other public body'
	};
	const LEGEND_KINDS: MapPt['kindKey'][] = ['dd', 'dx', 'muni', 'misc'];
	const maxEur = $derived(mapPts.length ? mapPts[0].eur : 1);
	const R_MAX = 26;
	const rOf = (v: number) => Math.max(2.5, R_MAX * Math.sqrt(v / maxEur));
	// several circles can share a Π.Ε. centroid (seatless forest units,
	// municipal, other bodies) — spread the smaller ones to the right so
	// none hides underneath a bigger one
	const xOff = $derived.by<Map<string, number>>(() => {
		const byPos = new Map<string, MapPt[]>();
		for (const p of mapPts) {
			const key = `${p.lat.toFixed(4)}:${p.lon.toFixed(4)}`;
			const arr = byPos.get(key);
			if (arr) arr.push(p);
			else byPos.set(key, [p]);
		}
		const off = new Map<string, number>();
		for (const group of byPos.values()) {
			let edge = 0; // mapPts is sorted by eur desc, so group is too
			for (let i = 1; i < group.length; i++) {
				edge = (edge || rOf(group[0].eur)) + rOf(group[i].eur) + 3;
				off.set(group[i].name, edge);
				edge += rOf(group[i].eur);
			}
		}
		return off;
	});
	const dmyDate = (iso: string | null) =>
		iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
	function unitTip(p: MapPt): string {
		return (
			`<strong>${bodyEn(p.name)}</strong><br>` +
			`${grInt(p.n)} contracts · ${eur(p.eur)}<br>` +
			`median contract ${eur(p.median_eur)}`
		);
	}

	// click a circle → its contract list docks right of the map;
	// click a Π.Ε. polygon → zoom the map to it
	let sel = $state.raw<MapPt | null>(null);
	let mapPe = $state<string | null>(null);
	// legend + contract list may never run past the map's bottom edge
	let mapH = $state(0);
	let keyH = $state(0);
	// the Anti-nero maps' fixed frame — same footprint on every dataset page
	const MAP_VIEW: { center: [number, number]; k: number } = {
		center: [23.8305, 38.3566],
		k: 1.08
	};
	const fireYearHi = $derived(
		firesShown.length ? Math.max(...firesShown.map((f) => f.properties.yr)) : FIRES_FROM
	);
	function fireTip(f: Feature<Polygon | MultiPolygon, FireProps>): string {
		const p = f.properties;
		return `<strong>${p.yr}</strong> · ${grInt(p.ha)} ha${p.name ? ` · ${p.name}` : ''}`;
	}

	// computed findings for the three harmonised frames (2026-08-24) —
	// every number from the payload, never typed
	const rankTop = $derived(o.top_coops.reduce((s, c) => s + c.total_eur, 0));
	const moneyFacts = $derived.by(() => {
		if (!o.yearly.length) return null;
		return o.yearly.reduce((m, y) => (y.eur > m.eur ? y : m), o.yearly[0]);
	});
	const cpvTree = $derived(o.cpv_tree ?? null);
	const cpvDiv77 = $derived(cpvTree?.divisions.find((d) => d.code.startsWith('77')) ?? null);
	const cpvDiv66 = $derived(cpvTree?.divisions.find((d) => d.code.startsWith('66')) ?? null);
	const cpvTopCode = $derived(
		cpvTree?.divisions
			.flatMap((d) => d.classes.flatMap((k) => k.codes))
			.sort((a, b) => b.n - a.n)[0] ?? null
	);
	// AWARD PROCEDURES + DIRECT AWARDS (2026-08-24): the Anti-nero pair's
	// dress, but NO ceiling lines — the recital audit showed the mass rests
	// on the forest-code assignment regime and the >€60k cohort on the
	// 13.08.2021 ΠΝΠ derogation (DATA_DECISIONS); every number computed
	const procRows = $derived(
		o.procedures.map((pr) => ({
			label: procedureEn(pr.label),
			value: pr.eur,
			sublabel: `${grInt(pr.n_contracts)} contracts`,
			direct: pr.label.includes('Απευθείας')
		}))
	);
	const procTotalEur = $derived(o.procedures.reduce((s, pr) => s + pr.eur, 0));
	const procTotalN = $derived(o.procedures.reduce((s, pr) => s + pr.n_contracts, 0));
	const directRow = $derived(o.procedures.find((pr) => pr.label.includes('Απευθείας')));
	const da = $derived(o.direct_awards ?? null);
	const daModal = $derived.by(() => {
		if (!da) return '';
		let best = 0;
		for (let i = 1; i < da.counts.length; i++) if (da.counts[i] > da.counts[best]) best = i;
		return bracket(da.labels[best] ?? '');
	});
	const coopRows = $derived(
		o.top_coops.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/dase/coop/${c.vat}`,
			sublabel: `${c.n_contracts} contracts · ${c.n_units} units · ${pct(c.pct_direct)} direct`
		}))
	);
	// Awarding-body categories, smallest first, in neutral greys — the
	// first column of the delegation diagram.
	const BODY_KINDS: [string, string, string][] = [
		['region', 'regions', 'color-mix(in srgb, var(--ink) 17.4%, var(--paper))'],
		['other_public', 'other public bodies', 'color-mix(in srgb, var(--ink) 29.9%, var(--paper))'],
		['municipality', 'municipalities', 'color-mix(in srgb, var(--ink) 44.9%, var(--paper))'],
		['decentralized_administration', 'decentralized administrations', 'color-mix(in srgb, var(--ink) 65.5%, var(--paper))'],
		['ministry', 'ministries', 'color-mix(in srgb, var(--ink) 86.4%, var(--paper))'],
		['unknown', 'unclassified', 'color-mix(in srgb, var(--ink) 11.2%, var(--paper))']
	];
	// delegation diagram: awarding body → operating unit → contractor,
	// ribbon width = € net. Nodes reuse the bars' category metadata so the
	// charts share one vocabulary and one palette.
	// In the middle column the two non-forest kinds collapse into ONE node:
	// «regional or municipal authorities» merely repeats what column 1
	// already says, and «other public bodies» is wrong there anyway (the
	// Ephorate of Antiquities is a unit OF the ministry, not another body).
	// What they have in common is the honest label: the body's own services.
	const OWN = 'own';
	const MIDDLE_KINDS: [string, string, string][] = [
		[OWN, "the body's own services", 'color-mix(in srgb, var(--ink) 44.5%, var(--paper))'],
		['dd', 'forest directorates', KIND_COLOR.dd],
		['dx', 'local forest service offices', KIND_COLOR.dx]
	];
	const midKind = (unit: string) => (unit === 'dx' || unit === 'dd' ? unit : OWN);
	const flowNodes = $derived.by<FlowNode[]>(() => {
		const f = o.kind_mix?.flows ?? [];
		const bodies: FlowNode[] = BODY_KINDS.map(([k, label, color]) => ({
			id: `l:${k}`,
			label,
			color,
			side: 'l' as const,
			n: f.filter((x) => x.body === k).reduce((a, x) => a + x.n, 0),
			eur: f.filter((x) => x.body === k).reduce((a, x) => a + x.eur, 0)
		}));
		const units: FlowNode[] = MIDDLE_KINDS.map(([k, label, color]) => ({
			id: `m:${k}`,
			label,
			color,
			side: 'm' as const,
			n: f.filter((x) => midKind(x.unit) === k).reduce((a, x) => a + x.n, 0),
			eur: f.filter((x) => midKind(x.unit) === k).reduce((a, x) => a + x.eur, 0)
		}));
		const coops: FlowNode[] = (o.kind_mix?.coops ?? []).map((c) => ({
			id: `r:${c.vat ?? 'other'}`,
			label: c.label ?? `${grInt(c.n_coops ?? 0)} other co-ops`,
			// the pooled node is co-ops too — a different colour would read
			// as a different kind of contractor
			color: 'var(--c-dase)',
			side: 'r' as const,
			n: c.n,
			eur: c.eur,
			href: c.vat ? `/dase/coop/${c.vat}` : undefined
		}));
		return [...bodies, ...units, ...coops]
			.filter((n) => n.n > 0)
			.sort((a, b) => (a.side === b.side ? b.eur - a.eur : 0));
	});
	const flowLinks = $derived.by<FlowLink[]>(() => {
		const merge = (rows: { key: string; n: number; eur: number }[]) => {
			const m = new Map<string, FlowLink>();
			for (const r of rows) {
				const [s, t] = r.key.split('>');
				const cur = m.get(r.key);
				if (cur) {
					cur.n += r.n;
					cur.eur += r.eur;
				} else m.set(r.key, { s, t, n: r.n, eur: r.eur });
			}
			return [...m.values()];
		};
		return [
			...merge(
				(o.kind_mix?.flows ?? []).map((f) => ({
					key: `l:${f.body}>m:${midKind(f.unit)}`,
					n: f.n,
					eur: f.eur
				}))
			),
			...merge(
				(o.kind_mix?.coop_flows ?? []).map((f) => ({
					key: `m:${midKind(f.unit)}>r:${f.vat ?? 'other'}`,
					n: f.n,
					eur: f.eur
				}))
			)
		];
	});
	const yearRows = $derived(
		o.yearly.map((y) => ({
			label: y.year,
			value: y.eur,
			sublabel: `${grInt(y.n)} contracts`
		}))
	);
	const cpvRows = $derived(
		o.cpvs.map((c) => ({
			label: `${c.label}${c.noise ? ' — ΕΦΚΑ contributions, not insurance' : ''}`,
			value: c.n_contracts,
			sublabel: c.cpv
		}))
	);

	// ---- contract values: one distribution, two encodings ----------------
	// The dots and the brackets are the SAME contracts: both are built from
	// the swarm array, binned client-side on the payload's own edges with the
	// server's half-open convention (pinned in tests/test_atlas_real_db.py).
	// That is what lets one year legend serve both modes.
	let valueMode = $state<'dots' | 'brackets'>('dots');
	// the dodge layout sizes itself to the tallest dot column; the brackets
	// then draw at that height, so toggling never resizes the frame
	let dotsHeight = $state(0);
	const swarmYears = $derived(
		swarm ? ([...new Set(swarm.year.filter(Boolean))].sort() as string[]) : []
	);
	const yearSegments = $derived(
		swarm
			? binByKey(
					swarm.eur.map((v) => v ?? 0),
					swarm.year,
					o.histogram.edges,
					swarmYears
				)
			: null
	);
	const VALUE_NOTES: Record<'dots' | 'brackets', string> = {
		dots: 'Every contract is one dot on a log scale (stated €, excl. VAT). Colours are assigned according to the year the contract was signed. Hover to inspect, click through to go to the contract’s page.',
		brackets:
			'The same contracts counted into brackets, each one a doubling of value — which is why the bars sit on the same scale as the dots. Bar height is the number of contracts; within a bar the signature years stack in legend order, earliest at the bottom.'
	};

	// finding-title inputs — computed from the payload, never hardcoded
	const cpvNoiseN = $derived(o.cpvs.find((c) => c.noise)?.n_contracts ?? 0);

	// hero bar fills — data-proportional
	const paidPct = $derived((o.kpis.paid_eur / o.kpis.total_eur) * 100);
</script>

<svelte:head>
	<title>ΔΑΣΕ — forest labour co-operatives</title>
	<meta
		name="description"
		content="Every Greek public contract won by a forest labour co-operative since Sept 2021: {grInt(
			o.kpis.n_contracts
		)} contracts, {eurShort(o.kpis.total_eur)} stated (excl. VAT)."
	/>
</svelte:head>

<div class="dasep">
<!-- the two lenses of the card map, stacked under its title in their
     full wording, the chosen one black (the Anti-nero card's treatment) -->
{#snippet allocSwitch()}
	<div class="allocsw" role="group" aria-label="Allocation by">
		<button class:on={allocKind === 'work'} onclick={() => (allocKind = 'work')}
			>by area of the awarding forest service</button
		>
		<button class:on={allocKind === 'home'} onclick={() => (allocKind = 'home')}
			>by registered office of the co-operatives</button
		>
	</div>
{/snippet}
<DatasetCard
	ds="dase"
	params={PARAMS}
	layout="triple"
	richKpis={kpiRich}
	cols={[549, 711, 516]}
	midRows={[1]}
	rightRows={[327.2, 605.3]}
	midGap={15.4}
	rightGap={20.5}
	hint="atlas/src/content/datasets/dase.md"
>
	{#snippet text()}
		<Text />
	{/snippet}
	{#snippet tileMain()}
		<Tile title="CONTRACT VALUES" href="#dase-values" fit>
			<div class="tilefill valbody" bind:clientHeight={valH}>
				{#if swarm && valH}
					<!-- the dots' greens are the years of signature: said in a key
					     under the title -->
					<div class="yearkey">
						{#each swarmYears as y (y)}
							<span><i style:background={YEAR_COLORS[y]}></i>{y}</span>
						{/each}
					</div>
					<BeeswarmCanvas
						data={swarm}
						edges={o.histogram.edges}
						linkBase="/dase/contract/"
						minHeight={Math.max(60, valH - 34)}
						maxHeight={Math.max(60, valH - 34)}
						radius={Math.max(0.9, Math.min(2.6, 1.6 * ((valH - 34) / 330)))}
					/>
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet tileA()}
		<Tile title="MONEY PER YEAR" href="#dase-yearly" fit>
			<div class="tilefill rankbody" bind:clientHeight={moneyH}>
				{#if moneyH}
					<BarH rows={yearRows} color="var(--c-dase)" inside compact barHeight={moneyBar} gap={moneyGap} fontPx={10} valuesRight />
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet tileB()}
		<Tile title="ALLOCATION OF FUNDING" href="#dase-allocation" fit headOver>
			<div class="tilefill mapfill" bind:clientWidth={tileW} bind:clientHeight={tileH}>
				{@render allocSwitch()}
				{#if tileW && tileH && allocChoro}
					<PaperMap
						width={tileW}
						height={tileH}
						interactive={false}
						fitBounds={ALLOC_BOUNDS}
						fitPad={0}
						context={false}
						outlineBy={regionOfPe}
						tipDefaultCorner="bottom-right"
						tipCompact
						colorOf={(pe) => cardChoro(allocChoro.by.get(pe) ?? 0)}
						tipOf={(pe) =>
							`<strong>${ruLabel(pe)}</strong> · ${eurShort(allocChoro.by.get(pe) ?? 0)}`}
						peGroup={(pe) => {
							const r = regionOfPe(pe);
							if (selDase) return r ?? pe;
							return r && regionEur.has(r) ? r : null;
						}}
						onRegionClick={(pe) => {
							if (selDase) {
								selDase = null;
								return;
							}
							const r = regionOfPe(pe);
							if (r && regionEur.has(r)) selDase = r;
						}}
						fitPesLive={selDasePes}
						onEmptyClick={() => (selDase = null)}
						onEscape={() => (selDase = null)}
					/>
					<div class="mapkey left">
						<div class="ends"><span>0</span><span class="max">{eurShort(allocChoro.max)}</span></div>
						<span class="swatches"><i class="empty"></i>{#each RAMP_DASE as c (c)}<i style:background={c}></i>{/each}</span>
						<div class="sent">€ of contracts — a jointly signed contract split evenly</div>
					</div>
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet more()}
			<div class="about">
			<div class="kicker">THE CO-OPERATIVES</div>
			<p>
				Every public contract won by a forest labour co-operative (ΔΑ.Σ.Ε., ν.4423/2016) since
				September 2021 — logging, clearing and tending work in the same forests the Anti-nero
				millions target, at a fraction of the size: the median contract is {eur(
					o.kpis.median_eur
				)} and {pct(o.kpis.pct_direct)} went by direct award, from {grInt(o.kpis.n_orgs)} awarding
				bodies through {grInt(o.kpis.n_units)} units. Of the {eurShort(o.kpis.total_eur)} stated,
				{eurShort(o.kpis.paid_eur)} shows as paid ({grInt(o.kpis.n_payments)} payment orders) —
				payments are posted for {grInt(o.kpis.n_paid_contracts)} of {grInt(
					o.kpis.n_contracts
				)} contracts, a registry practice, not a delivery record —
				<a href="/methodology#dase-dedup">methodology</a>.
			</p>
			<!-- the BASIS, said once for the whole page (the Anti-nero copy
			     doctrine, applied 2026-08-25): the frames below no longer
			     repeat it -->
			<p class="basis">
				All amounts are the contracts' stated values excl. VAT; {grInt(o.kpis.n_cancelled)}
				cancelled and {grInt(o.kpis.n_superseded)} superseded versions are excluded, one co-op's
				registry spellings (up to {o.kpis.max_name_variants}) merge on its canonical ΑΦΜ, and a
				contract signed by several co-ops jointly is split evenly between them — no euro counted
				twice; payments are a separate, structurally partial layer —
				<a href="/methodology#dase-dedup">basis</a>.
			</p>
		</div>
<ChartFrame title="CONTRACT FIGURES" anchor="figures">
	<div class="figures">
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
			</div>
			<div class="paidcard" role="img" aria-label="Paid so far, as a share of the stated total">
				<div class="pfill" style:height={`${paidPct}%`}>
					<div class="pnum">{eurShort(o.kpis.paid_eur).toLowerCase()}</div>
					<div class="plbl">already paid</div>
				</div>
			</div>
		</div>
	</div>
</ChartFrame>


<!-- the works/seats duo, the Anti-nero ALLOCATION OF FUNDING one dataset
     over (user, DATA_DECISIONS 2026-08-24) -->
{#if alloc}
	{@const topWork = alloc.work_regions[0]}
	{@const topFlow = alloc.flows.find((f) => f.from !== f.to)}
	<ChartFrame
		title="ALLOCATION OF FUNDING"
		insight={`${pct(100 - alloc.away_share, 0)} of the money awarded to forest workers' co-operatives goes to co-operatives based in the region where the works are — as the forest code intends: under άρθρο 136Α ν.δ. 86/1969, added by ν.4423/2016, the exploitation of public forests is granted in an order of preference that begins with the co-operatives seated in the municipality of the works. ${peEn(topWork.pe)} is the notable exception: ${pct((topWork.imported_eur / topWork.eur) * 100, 0)} of the work there went to co-operatives based elsewhere, in the restoration that followed the 2021 fires. One documented reason is that from 2022 the seven-year ΔΥΠΑ programme (ΚΥΑ 19895/2022, ΦΕΚ Β΄ 956) hired the fire-hit resin workers of Istiaia–Aidipsos and Mantoudi–Limni–Agia Anna — members of the local co-operatives — into the Ministry's own forest services, on the express condition that they exercise no activity in that capacity.`}
		caveat="{eurShort(alloc.unresolved.eur)} on {grInt(alloc.unresolved.n)} transmission-corridor contracts names no work region and is off both maps."
		anchor="dase-allocation"
		methodology="dase-award-basis"
	>
		<DaseMap data={alloc} />
	</ChartFrame>
{/if}

{#if dmap}
	<ChartFrame
		title="MAP"
		subtitle="Location of the projects is assigned according to the location of the awarding unit"
		caveat="Circles sit at the awarding forest unit's registry seat; awarders with no seat on record — δήμοι, περιφέρειες and the other public bodies, plus a few forest units — are drawn at the centre of their regional unit instead. {grInt(
			dmap.unresolved.n
		)} ΑΔΜΗΕ power-line contracts span multiple regional units and stay off the map ({eurShort(
			dmap.unresolved.eur
		)}). Burn scars: © European Union, Copernicus Emergency Management Service — EFFIS; satellite rapid-mapping estimates, not official οριοθετήσεις."
		anchor="dase-map"
		methodology="dase-regions"
	>
		<div class="maprow" class:open={sel !== null}>
			<div class="map-holder" bind:clientHeight={mapH}>
				<PaperMap
					width={640}
					height={620}
					view={MAP_VIEW}
					colorOf={() => 'var(--paper)'}
					focusPe={mapPe}
					onRegionClick={(pe) => (mapPe = mapPe === pe ? null : pe)}
				>
					{#snippet overlay(ctx)}
						{#if firesShown.length}
							<FiresLayer {ctx} features={firesShown} tipOf={fireTip} />
						{/if}
						{#each mapPts as p (p.name)}
							{@const xy = ctx.projection([p.lon, p.lat])}
							{#if xy}
								<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
								<circle
									cx={xy[0] + (xOff.get(p.name) ?? 0) / ctx.k}
									cy={xy[1]}
									r={rOf(p.eur) / ctx.k}
									class="ucircle"
									style:fill={KIND_COLOR[p.kindKey]}
									onmouseenter={() => ctx.showTip(unitTip(p))}
									onmouseleave={() => ctx.hideTip()}
									onclick={() => (sel = sel?.name === p.name ? null : p)}
								/>
							{/if}
						{/each}
						<!-- labels drawn after every circle so overlaps never cover them -->
						{#each mapPts as p (`l:${p.name}`)}
							{@const xy = ctx.projection([p.lon, p.lat])}
							{#if xy && rOf(p.eur) >= 12}
								<text
									class="ulabel"
									x={xy[0] + (xOff.get(p.name) ?? 0) / ctx.k}
									y={xy[1]}
									dy="0.35em"
									font-size={11 / ctx.k}
								>
									{p.n}
								</text>
							{/if}
						{/each}
					{/snippet}
				</PaperMap>
			</div>
			<div class="mapside">
				<!-- the legend panel, top-aligned with the map: awarder dots
				     stacked left, size + burnt-areas explanations right -->
				<div class="mapkey" bind:clientHeight={keyH}>
					<div class="mk-left">
						<div class="mk-title">contracts awarded by</div>
						<ul class="mk-kinds">
							{#each LEGEND_KINDS as k (k)}
								<li>
									<i style:background={KIND_COLOR[k]}></i>
									{KIND_LABEL[k]}
								</li>
							{/each}
						</ul>
					</div>
					<div class="mk-right">
						<div class="mk-size">
							<svg width="40" height="40" aria-hidden="true">
								<!-- small circle internally tangent at the bottom, x inside it -->
								<circle class="mk-c" cx="20" cy="20" r="17" />
								<circle class="mk-c" cx="20" cy="29" r="8" />
								<text class="mk-x" x="20" y="29" dy="0.35em">x</text>
							</svg>
							<div class="mk-sizetext">
								<p>circle size: total € awarded</p>
								<p>x: number of contracts</p>
							</div>
						</div>
						<div class="mk-fires">
							<div class="mk-firetitle">burnt areas</div>
							<i class="firegrad"></i>
							<div class="mk-years"><span>{FIRES_FROM}</span><span>{fireYearHi}</span></div>
						</div>
					</div>
				</div>
				{#if sel}
					<aside class="unitpanel" style:max-height={`${Math.max(160, mapH - keyH - 16)}px`}>
						<header>
							<div>
								<div class="up-name" title={devGreek(sel.name)}>{bodyEn(sel.name)}</div>
								<div class="up-stats">
									{grInt(sel.n)} contracts, median: {eur(sel.median_eur)}, total amount: {eur(
										sel.eur
									)}
								</div>
							</div>
							<button class="up-close" onclick={() => (sel = null)} aria-label="Close">×</button>
						</header>
						<table class="uptable">
							<thead>
								<tr><th>ΑΔΑΜ</th><th>awarding unit</th><th>ΔΑΣΕ</th><th>date</th><th class="num">€</th></tr>
							</thead>
							<tbody>
								{#each sel.contracts as c (c.ref)}
									<tr>
										<td><a href={`/dase/contract/${c.ref}`}>{c.ref}</a></td>
										<td title={devGreek(c.by)}>{bodyEn(c.by) || '—'}</td>
										<td>{c.coop || '—'}</td>
										<td class="nowrap">{dmyDate(c.d)}</td>
										<td class="num">{c.eur === null ? '—' : eur(c.eur)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</aside>
				{/if}
			</div>
		</div>
	</ChartFrame>
{:else}
	<div class="skeleton" id="dase-map" style="height: 560px"></div>
{/if}

<ChartFrame
	title="AWARDING PROCESS"
	hint="Every contract names an awarding body, the operating unit that ran it and the co-op that won it — a ribbon is that chain, and both ribbon and bar are sized by the stated net € printed beside each bar; hover a bar for the number of contracts behind that money."
	caveat="Bodies that ran the procurement through their own services — municipal departments, ephorates of antiquities, ΟΣΕ line maintenance — share one middle node; the right column holds the biggest co-ops by €, the rest pooled into one node; a consortium contract counts once, at the co-op listed first."
	anchor="dase-delegation"
	methodology="org-names"
>
	<!-- equal outer margins: the three columns are then evenly spaced AND the
	     middle one sits on the drawing's centre (user, 2026-08-22) -->
	<KindFlow
		nodes={flowNodes}
		links={flowLinks}
		height={660}
		headings={['awarding bodies', 'operating units', 'contractors']}
		marginLeft={340}
		marginRight={340}
		columnX={[0.10, 0.45, 0.78]}
	/>
</ChartFrame>

<!-- the Anti-nero AWARD PROCEDURES + DIRECT AWARDS pair, one dataset over
     (DATA_DECISIONS 2026-08-24): same dress, NO ceiling lines — the
     άρθρο 118 ceilings do not govern the forest-code or ΠΝΠ regimes -->
<div class="pair">
	<ChartFrame
		title="AWARD PROCEDURES"
		insight={`${grInt(directRow?.n_contracts ?? 0)} of the ${grInt(procTotalN)} contracts — ${pct(((directRow?.eur ?? 0) / procTotalEur) * 100, 0)} of the money — went by direct award: assignment of forest work to the local co-operatives at State-set prices («τιμές ανάθεσης») is the forest code's own default, not a below-threshold exception.`}
		caveat="Procedures as recorded in ΚΗΜΔΗΣ, named in the wording of Directive 2014/24/EU. The registry files most assignments under «Απευθείας ανάθεση (αρ.118/αρ. 328)», but the contracts' own recitals rest on the forest-code regime (ν.δ. 86/1969, π.δ. 126/1986)."
		anchor="dase-procedures"
		methodology="dase-award-basis"
	>
		<div class="rankw">
			<BarH rows={procRows} color="var(--c-dase)" inside barHeight={35} valuesRight highlight={(r) => !!(r as { direct?: boolean }).direct} />
		</div>
	</ChartFrame>

	{#if da}
		<ChartFrame
			title="DIRECT AWARDS"
			insight={`The ${grInt(da.n)} direct-award contracts pile up around €${daModal} — small assignments at the State-set prices. The ${grInt(da.n_above_60k)} above €60k are the post-fire emergency works of the 13.08.2021 ΠΝΠ (ν.4824/2021), awarded «κατά παρέκκλιση» of the national procurement rules — no ceiling lines are drawn because none apply here.`}
			caveat="Stated net values of the «Απευθείας ανάθεση» contracts; the ν.4782/2021 ceilings (€30k/€60k) belong to the ν.4412 άρθρο 118 route, which is not these contracts' stated basis."
			anchor="dase-direct-awards"
			methodology="dase-award-basis"
		>
			<LogHistogram
				labels={da.labels.map(bracket)}
				counts={da.counts}
				edges={da.edges}
				color="var(--c-dase)"
			/>
		</ChartFrame>
	{/if}
</div>

<Defer height={400}>
{#if swarm}
	<ChartFrame
		title="CONTRACT VALUES"
		insight={`Half the contracts are worth ${eurShort(o.kpis.median_eur)} or less.`}
		hint="Both views draw the same contracts on one axis: every bracket spans a doubling of value — a logarithmic scale — and the dots sit on that same scale, so a value is at the same place in both, the median line included; colours are the signature year."
		anchor="dase-swarm"
		methodology="dase-dedup"
	>
		<!-- year legend and mode switch share one line, legend left and
		     switch against the frame's right edge: the colours mean the same
		     thing in both modes, so the legend never changes -->
		<div class="modes">
			<div class="legend">
				{#each swarmYears as y (y)}
					<span><i style:background={YEAR_COLORS[y]}></i>{y}</span>
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
				<BeeswarmCanvas data={swarm} edges={o.histogram.edges} bind:plotHeight={dotsHeight} />
			{:else}
				<LogHistogram
					labels={o.histogram.labels}
					counts={o.histogram.counts}
					edges={o.histogram.edges}
					color="var(--c-dase)"
					median={o.histogram.median}
					height={dotsHeight || 460}
					segments={yearSegments}
					segColors={swarmYears.map((y) => YEAR_COLORS[y])}
				/>
			{/if}
		</SideNote>
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 380px"></div>
{/if}
</Defer>

<!-- MONEY PER YEAR and the RANKING share one row at equal width
     (user, 2026-08-24) -->
<div class="pair">
	<ChartFrame
		title="MONEY PER YEAR"
		caveat="Stated value (net) by signature year. No €-paid series is drawn — payment orders exist for only part of the contracts as registry practice, so a paid bar would chart the registry, not disbursement."
		anchor="dase-yearly"
		methodology="dase-dedup"
	>
		<BarH rows={yearRows} color="var(--c-dase)" inside barHeight={35} valuesRight />
	</ChartFrame>

	<ChartFrame
		title="RANKING OF CO-OPERATIVES"
		anchor="top-coops"
		methodology="canonical-vat"
	>
		<div class="rankw">
			<BarH rows={coopRows} color="var(--c-dase)" inside barHeight={35} valuesRight />
		</div>
	</ChartFrame>
</div>

<ChartFrame
	title="CPV CODES"
	insight={cpvTree
		? `The ${grInt(cpvTree.n_codes)} codes the ${grInt(cpvTree.n_contracts)} contracts declare fall into ${grInt(cpvTree.divisions.length)} of the vocabulary’s divisions${cpvDiv77 ? `: ${grInt(cpvDiv77.n)} contracts declare a code of «${cpvDiv77.name_en}»` : ''}${cpvDiv66 ? `, while the ${grInt(cpvDiv66.n)} under «${cpvDiv66.name_en}» are the ΕΦΚΑ tag on υλοτομικά contracts, not insurance procurement` : ''}. The most common single code, «${cpvTopCode?.name_en ?? ''}», appears on ${grInt(cpvTopCode?.n ?? 0)} (${pct(((cpvTopCode?.n ?? 0) / o.kpis.n_contracts) * 100)}).`
		: ''}
	caveat="Codes as declared in ΚΗΜΔΗΣ, named from the EU CPV 2008 vocabulary (division → class → code); a contract may declare several, so the counts overlap and are never summed. The insurance CPV 66519300-4 on {grInt(cpvNoiseN)} υλοτομικά rows tags the state-funded ΕΦΚΑ contributions itemised in the awards — not procured insurance."
	anchor="dase-cpvs"
	methodology={null}
>
	{#if cpvTree}
		<CpvColumns divisions={cpvTree.divisions} total={o.kpis.n_contracts} />
	{:else}
		<BarH rows={cpvRows} color="var(--c-dase)" fmt={(v) => `${grInt(v)} contracts`} />
	{/if}
</ChartFrame>

	{/snippet}
</DatasetCard>
<RefreshLine />
</div>

<style>
	/* the whole page speaks the dataset colour: frame titles, the
	   lightbulbs and the CPV columns' ink all take the green
	   (--frame-accent / --cpv-ink inherit into the components) */
	.dasep {
		--frame-accent: var(--c-dase);
		--cpv-ink: var(--c-dase);
	}
	/* every section title follows the sponsored-works kicker, in the
	   ΔΑΣΕ dataset colour (green) */
	.dasep :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-dase);
	}
	/* the paper map takes the shared ground; regions stay white so the
	   proportional circles carry the data */
	.dasep :global(.map) {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border: 1px solid var(--line); /* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		--map-accent: var(--c-dase); /* the zoom buttons' circle hue */
		box-shadow: none;
	}
	.dasep :global(.region) {
		stroke: var(--line);
	}
	/* flat solid dots, exactly like the legend swatches — no outline;
	   the hover ring is interaction feedback only */
	.ucircle {
		fill: var(--c-dase);
		stroke: none;
	}
	.ucircle:hover {
		stroke: var(--ink);
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}
	.ulabel {
		fill: var(--paper);
		font-family: var(--font-display);
		font-weight: 900;
		text-anchor: middle;
		pointer-events: none;
	}
	/* map left; legend (and the clicked unit's contract list) on the right,
	   top-aligned with the map */
	.maprow {
		/* 640×620 viewBox rendered at 600px → 600×581.5 on screen */
		display: grid;
		grid-template-columns: minmax(0, 600px) minmax(250px, 1fr);
		gap: var(--sp-4);
		align-items: start;
	}
	@media (max-width: 900px) {
		.maprow {
			grid-template-columns: 1fr;
		}
	}
	.mapside {
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	/* the legend panel per the approved mock: awarder dots stacked in the
	   left column, size icon + burnt-areas gradient in the right one */
	.mapkey {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 10px;
		padding: var(--sp-2) var(--sp-4);
		font-size: var(--fs-13);
		color: var(--ink);
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6);
		align-items: start;
	}
	@media (max-width: 900px) {
		.mapkey {
			grid-template-columns: 1fr;
		}
	}
	.mk-title {
		margin-bottom: 8px;
	}
	.mk-kinds {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.mk-kinds li {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.mk-kinds i {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		flex: none;
	}
	.mk-size {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		margin-bottom: 8px;
	}
	.mk-size svg {
		flex: none;
	}
	.mk-c {
		fill: none;
		stroke: var(--ink-soft);
		stroke-width: 1.3;
	}
	.mk-x {
		fill: var(--ink);
		font-size: 11px;
		text-anchor: middle;
	}
	.mk-sizetext {
		max-width: 26em;
	}
	.mk-sizetext p {
		margin: 0 0 2px;
	}
	.mk-firetitle {
		margin-bottom: 4px;
	}
	.firegrad {
		display: block;
		max-width: 340px;
		height: 14px;
		border-radius: 3px;
		background: linear-gradient(to right, var(--paper), var(--c-fire));
	}
	.mk-years {
		display: flex;
		justify-content: space-between;
		max-width: 340px;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.unitpanel {
		background: var(--paper);
		border: 1px solid var(--line);
		border-radius: 6px;
		display: flex;
		flex-direction: column;
	}
	.unitpanel header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--sp-2);
		padding: var(--sp-3);
		border-bottom: 1px solid var(--line);
	}
	.up-name {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
	}
	.up-stats {
		font-size: var(--fs-12);
		font-weight: 700;
		color: var(--ink);
	}
	.up-close {
		border: none;
		background: none;
		font-size: var(--fs-18);
		line-height: 1;
		cursor: pointer;
		color: var(--ink-soft);
		padding: 0 2px;
	}
	.uptable {
		display: block;
		overflow-y: auto;
		margin: 0;
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-11, 11px);
		border-collapse: collapse;
	}
	.uptable th {
		text-align: left;
		font-weight: 700;
		color: var(--ink-soft);
		padding: 2px 8px 4px 0;
		white-space: nowrap;
	}
	.uptable td {
		padding: 4px 8px 4px 0;
		border-top: 1px solid color-mix(in srgb, var(--ink) 6.5%, var(--paper));
		vertical-align: top;
	}
	.uptable td a {
		white-space: nowrap;
	}
	.uptable .num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		padding-right: 0;
		white-space: nowrap;
	}
	.uptable .nowrap {
		white-space: nowrap;
	}
	.ucircle {
		cursor: pointer;
	}
	/* middle column mirrors the cards grid: the two bars share the first
	   card's row, the paid card fills the third row */
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
	.dabar .track {
		height: 100%;
		background: var(--paper);
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.dabar .fill {
		height: 100%;
		background: var(--c-dase);
		color: var(--paper);
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
	/* paid vs stated: green fill rises to the paid share of the stated €;
	   the unfilled remainder reads as light grey, no outer border */
	.paidcard {
		grid-row: 3;
		position: relative;
		background: var(--paper);
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.paidcard .pfill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--c-dase);
		color: var(--paper);
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 2px;
		padding: 8px 14px 10px;
	}
	.paidcard .pnum {
		font-family: var(--font-display);
		font-weight: 900;
		/* matches the card numbers' cap */
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
	/* the page's one BASIS line under the intro (the Anti-nero dress) */
	.basis {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.basis a {
		color: var(--ink-soft);
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--c-dase);
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	/* year legend left, mode switch hard right — one line above the chart */
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
	.legend {
		display: flex;
		gap: var(--sp-4);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.legend i {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
		margin-right: 4px;
		vertical-align: -1px;
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
	.map-holder {
		max-width: 44rem;
	}
	/* same footprint as the sponsored-works RANKING OF COMPANIES */
	/* inside the half-width pair the full-width 75% measure would squeeze
	   the bars until names fall outside the green — the pair column IS the
	   measure now (user, 2026-08-24) */
	.rankw {
		max-width: none;
	}
	/* the card's tiles fill their panels (`.tilefill`, not `.fill` — the
	   direct-award bar owns that name); the map in the Anti-nero card's
	   manners: thinner lines, no plate, white unit seams on the green */
	.tilefill {
		position: absolute;
		inset: 0;
	}
	.tilefill :global(.map) {
		background: transparent;
		border: none;
		--land-context: var(--paper);
		--map-accent: var(--card-accent);
		box-shadow: none;
	}
	.tilefill.mapfill {
		--region-line-w: 0.35;
		--context-line-w: 0.35;
		--border-line-w: 0.6;
		--land-hot: color-mix(in srgb, var(--ink) 11.2%, var(--paper));
		--unit-line: var(--paper);
		--unit-line-w: 0.45;
	}
	/* the page's own region stroke must not reach the card map's units */
	.tilefill.mapfill :global(.region.noline) {
		stroke: var(--unit-line);
	}
	/* the key as on the Anti-nero card: the ends of the scale on a line
	   ABOVE a 128 px swatch bar with a ½ px black hairline, the sentence
	   under it, 10 px lettering, on the title's A */
	.tilefill .mapkey {
		position: absolute;
		bottom: 14px;
		left: 8px;
		margin: 0;
		padding: 0;
		z-index: 2;
		pointer-events: none;
		font-family: var(--font-ui);
		font-size: 10px;
		line-height: 12px;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
		background: none;
		border-radius: 0;
		display: block;
	}
	.mapkey .ends {
		position: relative;
		width: 128px;
		height: 13px;
	}
	.mapkey .ends span {
		position: absolute;
		bottom: 0;
		left: 0;
		white-space: nowrap;
	}
	.mapkey .ends .max {
		left: auto;
		right: -33px;
	}
	.mapkey .swatches {
		display: flex;
		width: 128px;
		box-sizing: border-box;
		border: 0.5px solid var(--ink);
	}
	.mapkey .swatches i {
		display: block;
		flex: 1 1 0;
		height: 11.6px;
	}
	.mapkey .swatches i.empty {
		background: var(--land-empty);
	}
	.mapkey .sent {
		margin-top: 9px;
		white-space: nowrap;
	}
	/* the lenses, stacked under the title at the top-left */
	.allocsw {
		position: absolute;
		/* each lens on ONE line, the pair tight under the title (user, 2026-08-28) */
		top: 30px;
		left: 8px;
		z-index: 3;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		width: max-content;
	}
	.allocsw button {
		font-family: var(--font-ui);
		font-size: 10px;
		line-height: 12px;
		text-align: left;
		white-space: nowrap;
		padding: 1.6px 3.4px 2px;
		background: var(--paper);
		color: var(--ink);
		border: none;
		cursor: pointer;
		min-height: 20px;
	}
	.allocsw button.on {
		background: var(--c-dase);
		color: var(--paper);
	}
	.tilefill.valbody,
	.tilefill.rankbody {
		position: absolute;
		display: flex;
		flex-direction: column;
	}
	.yearkey {
		flex: none;
		display: flex;
		gap: 12px;
		padding: 8px 0 2px;
		font-family: var(--font-ui);
		font-size: 11px;
		color: var(--ink-soft);
	}
	.yearkey i {
		display: inline-block;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		margin-right: 4px;
		vertical-align: -1px;
	}
	.tilefill.valbody :global(.bees) {
		flex: 1;
		min-height: 0;
	}
	/* the programme figures — the bars the hero used to carry beside its
	   cards — open the unfolded part */
	.figures {
		max-width: 560px;
	}
	.figures .midcol {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: none;
		width: auto;
	}
	.figures .bars,
	.figures .paidcard {
		grid-row: auto;
	}
	.figures .paidcard {
		min-height: 140px;
	}
</style>
