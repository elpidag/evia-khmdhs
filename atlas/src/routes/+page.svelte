<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import StackedShareBar from '$lib/charts/StackedShareBar.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import SideNote from '$lib/ui/SideNote.svelte';
	import { YEAR_GREYS, yearGrey } from '$lib/charts/yearColors';
	import { binByKey } from '$lib/transforms/histogram';
	import type { DaseSwarm } from '$lib/api';
	import DisbursementCurves from '$lib/charts/DisbursementCurves.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import KindFlow from '$lib/charts/KindFlow.svelte';
	import CatWorkChord from '$lib/charts/CatWorkChord.svelte';
	import AreaYears from '$lib/charts/AreaYears.svelte';
	import CpvColumns from '$lib/charts/CpvColumns.svelte';
	import { procedureEn } from '$lib/transforms/procedures';
	import {
		CHORD_PAIRS,
		catScope,
		catWorks,
		pairFor,
		scopeWorks,
		sidesOf,
		type ChordPair
	} from '$lib/transforms/chordSides';
	import { SCOPE_COLORS, SCOPE_LABELS, SCOPE_ORDER } from '$lib/charts/scopeColors';
	import { unitEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import StripTimeline from '$lib/charts/StripTimeline.svelte';
	import AntineroMap from '$lib/sections/AntineroMap.svelte';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import FlowMap from '$lib/sections/FlowMap.svelte';
		import { loadCentroids } from '$lib/maps/useGeo';
	import type { Connections } from '$lib/api';
	import ContractNetwork from '$lib/charts/ContractNetwork.svelte';
	import type { NetNode } from '$lib/transforms/network';
	import { NET_MODES } from '$lib/transforms/networkScene';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { makeChoro, RAMP_WORKS } from '$lib/maps/useGeo';
	import Defer from '$lib/ui/Defer.svelte';
	import {
		apiGetCached,
		type AntineroMapPayload,
		type PaymentsPayload,
		type PeYearly,
		type SwarmRow
	} from '$lib/api';
	import { bracket, eurShort, grInt, pct } from '$lib/transforms/format';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	// heavy payloads load client-side (cached across navigations);
	// $state.raw — immutable data must not pay deep-proxy overhead
	let map = $state.raw<AntineroMapPayload | null>(null);
	let payments = $state.raw<PaymentsPayload | null>(null);
	// AWARDING PROCESS (named MONEY FLOW until 2026-08-22): the awarding body
	// → its operating units → the contractors
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
	/** the flow layer, moved here from the old /connections page (user,
	 *  2026-08-20; that page left the site on 2026-08-23) */
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
	// the ?net= lens: colour by scope (default) or by curated type; the
	// «nested by call» arrangement is parked (its scene stays), so the
	// drawn arrangement is always the timeline
	const netMode = $derived(
		NET_MODES.find((m) => m.value === page.url.searchParams.get('net'))?.value ?? 'scope'
	);
	const netCopy = $derived.by(() => {
		const st = network?.stats ?? {};
		// the 2022 era by scope, counted from the nodes themselves
		const n22 = (network?.nodes ?? []).filter((n) => (n.d ?? '').startsWith('2022'));
		const y22 = { n: n22.length, works: n22.filter((n) => n.dk === 'works').length };
		if (netMode === 'type')
			return {
				title: 'PROCUREMENT TIMELINE',
				subtitle: `${grInt(st.n_same_day_calls)} of the ${grInt(st.n_multi_calls)} split procurements signed every lot on one day, and ${grInt(network?.fire_season.n_contracts ?? 0)} of the ${grInt(st.n_contracts)} contracts were signed inside a fire season. By type, the special forestry works are the grey mass and the specialised strands — mixed firebreaks, reforestation, flood protection, archaeological sites — arrive in campaigns.`,
				caveat: ''
			};
		return {
			title: 'PROCUREMENT TIMELINE',
			subtitle: `${grInt(st.n_same_day_calls)} of the ${grInt(st.n_multi_calls)} split procurements signed every lot on one day, and ${grInt(network?.fire_season.n_contracts ?? 0)} of the ${grInt(st.n_contracts)} contracts were signed inside a fire season. By scope, ${y22.works} of the ${y22.n} contracts of 2022 bought works only, and the design-build template (the contractor drafts the studies, then builds) takes over from 2023.`,
			caveat: ''
		};
	});

	const directEur = $derived(o.procedures.find((p) => p.label.includes('Απευθείας'))?.eur ?? 0);
	// ---- findings for the bulbs, computed from the payloads (copy pass
	// 2026-08-23: a bulb states findings and author context, never how to
	// read — that is the chart's and the legend's job) ----
	const allocFacts = $derived.by(() => {
		const rs = [...(map?.work_regions ?? [])].sort((a, b) => b.split_eur - a.split_eur);
		if (!rs.length) return null;
		const total = rs.reduce((s, r) => s + r.split_eur, 0);
		let acc = 0;
		let nHalf = 0;
		for (const r of rs) {
			acc += r.split_eur;
			nHalf += 1;
			if (acc >= total / 2) break;
		}
		return { top: rs[0], topShare: (rs[0].split_eur / total) * 100, nHalf, n: rs.length };
	});
	const rankFacts = $derived.by(() => {
		const top = topRows.reduce((s, r) => s + (r.value ?? 0), 0);
		return { top, share: o.kpis.total_eur ? (top / o.kpis.total_eur) * 100 : 0, n: topRows.length };
	});
	const unitFacts = $derived.by(() => {
		const us = (unitFlow?.nodes ?? []).filter((n) => n.id.startsWith('u:')).sort((a, b) => b.eur - a.eur);
		if (!us.length || !unitFlow) return null;
		return { label: unitEn(us[0].label), eur: us[0].eur, share: (us[0].eur / unitFlow.total_eur) * 100 };
	});
	const valueFacts = $derived.by(() => {
		if (!swarm?.length) return null;
		const vs = [...swarm.map((r) => r.eur)].sort((a, b) => a - b);
		const median = vs[Math.floor(vs.length / 2)];
		return { n: vs.length, median, above: vs.filter((v) => v > 60_000).length, min: vs[0], max: vs[vs.length - 1] };
	});
	const moneyFacts = $derived.by(() => {
		const byYear = new Map<string, number>();
		for (const r of swarm ?? []) byYear.set(r.year ?? '—', (byYear.get(r.year ?? '—') ?? 0) + r.eur);
		const c = [...byYear.entries()].sort((a, b) => b[1] - a[1])[0];
		const pd = [...o.yearly].sort((a, b) => b.paid_eur - a.paid_eur)[0];
		return c ? { year: c[0], eur: c[1], payYear: pd?.year, payEur: pd?.paid_eur ?? 0 } : null;
	});
	const paidFacts = $derived.by(() => {
		const byYear = new Map<string, number>();
		const events = (payments?.events ?? []).filter((e) => !!e.d);
		for (const e of events) byYear.set(e.d!.slice(0, 4), (byYear.get(e.d!.slice(0, 4)) ?? 0) + (e.eur || 0));
		const years = [...byYear.keys()].sort();
		if (!years.length) return null;
		const heaviest = [...byYear.entries()].sort((a, b) => b[1] - a[1])[0];
		// the chart's point: the SAME day of the year across years — the
		// last year so far against the previous year up to the same day
		const last = years.at(-1)!;
		const prev = years.length > 1 ? years.at(-2)! : null;
		const lastDay = events.filter((e) => e.d!.startsWith(last)).map((e) => e.d!.slice(5)).sort().at(-1) ?? '12-31';
		const upTo = (y: string) => events.filter((e) => e.d!.startsWith(y) && e.d!.slice(5) <= lastDay).reduce((s, e) => s + (e.eur || 0), 0);
		return { year: heaviest[0], eur: heaviest[1], last, lastEur: byYear.get(last) ?? 0, prev, prevSameDay: prev ? upTo(prev) : 0 };
	});
	// the chord's finding: for the two biggest right-hand arcs, the left
	// arc they reach most, with counts
	const chordFacts = $derived.by(() => {
		const d = chordData;
		const rights = [...d.right.items].sort((a, b) => b.n - a.n).slice(0, 2);
		return rights.map((r) => {
			const best = [...d.left.items]
				.map((l) => ({ l, n: d.matrix[`${r.key}|${l.key}`] ?? 0 }))
				.sort((a, b) => b.n - a.n)[0];
			return { right: r, left: best?.l, n: best?.n ?? 0 };
		});
	});
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
	// AWARD PROCEDURES in the Directive's English (the registry strings are
	// Greek); the direct-award row is the one to point at
	const procRows = $derived(
		o.procedures.map((p) => ({
			label: procedureEn(p.label),
			value: p.eur,
			sublabel: `${grInt(p.n_contracts)} contracts`,
			direct: p.label.includes('Απευθείας')
		}))
	);
	const procTotalEur = $derived(o.procedures.reduce((s, p) => s + p.eur, 0));
	const procTotalN = $derived(o.procedures.reduce((s, p) => s + p.n_contracts, 0));
	const directN = $derived(o.procedures.find((p) => p.label.includes('Απευθείας'))?.n_contracts ?? 0);


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
		return bracket(labels[best] ?? '');
	});
	const firstPayYear = $derived((o.timeseries.months[0] ?? '').slice(0, 4));
	// work-type category chart: stated € or contract counts, same bars
	// the five-year-maps strip (user, 2026-08-22, replacing the MONEY BY
	// REGION PER YEAR facets): per-year per-region € on ONE shared scale —
	// the same sqrt grey ramp as the big allocation maps above it
	const yearCells = $derived.by(() => {
		const py = peYearly;
		if (!py) return null;
		const per = py.years.map((y) => {
			const cells = new Map<string, number>();
			let total = 0;
			for (const f of py.pes) {
				const v = f.years[y] ?? 0;
				if (v > 0) cells.set(f.pe, v);
				total += v;
			}
			return { year: y, cells, total };
		});
		const max = Math.max(...per.flatMap((p) => [...p.cells.values()]), 1);
		return { per, choro: makeChoro(RAMP_WORKS, max) };
	});

	// MONEY PER YEAR measures: € contracted (stated net, by signature
	// year, from the swarm list so it reconciles to the basis) or € paid
	// (payment orders by payment year) — ?money=
	const MONEY_LENSES = ['contracted', 'paid'] as const;
	type MoneyLens = (typeof MONEY_LENSES)[number];
	const moneyLens = $derived<MoneyLens>(
		(MONEY_LENSES as readonly string[]).includes(page.url.searchParams.get('money') ?? '')
			? (page.url.searchParams.get('money') as MoneyLens)
			: 'contracted'
	);
	const yearMoneyRows = $derived.by(() => {
		if (moneyLens === 'paid')
			return o.yearly
				.filter((y) => y.paid_eur > 0)
				.map((y) => ({ label: y.year, value: y.paid_eur }));
		if (!swarm) return [];
		const by = new Map<string, { eur: number; n: number }>();
		for (const r of swarm) {
			const y = r.year ?? '—';
			const b = by.get(y) ?? { eur: 0, n: 0 };
			b.eur += r.eur;
			b.n += 1;
			by.set(y, b);
		}
		return [...by.entries()]
			.sort((a, b) => a[0].localeCompare(b[0]))
			.map(([y, b]) => ({ label: y, value: b.eur, sublabel: `${grInt(b.n)} contracts` }));
	});

	// CONTRACT TYPE measures: stated net € or number of contracts (?ct=)
	const CT_LENSES = ['eur', 'n'] as const;
	type CtLens = (typeof CT_LENSES)[number];
	const ctLens = $derived<CtLens>(
		(CT_LENSES as readonly string[]).includes(page.url.searchParams.get('ct') ?? '')
			? (page.url.searchParams.get('ct') as CtLens)
			: 'eur'
	);
	// works as ROWS, each split by the main category of the contracts naming
	// it (user, 2026-08-22: the work names are long, so they must be labels)
	// the key/legend form of a category name: the head clause, cut at
	// whichever separator the curation used ('—' or ':') — the names are
	// sentences and the swatch row cannot carry them whole
	const catShort = $derived(
		new Map(
			o.categories.map((c) => [c.key, (c.label_en ?? c.label).split(/\s+[—–]\s+|:\s+/)[0]])
		)
	);
	// the chord's PAIR of flaggings (user, 2026-08-23): category ↔ works,
	// category ↔ scope, scope ↔ works — a toggle under each heading, with
	// the rule that both halves cannot be the scope
	const chordPair = $derived<ChordPair>(
		(CHORD_PAIRS as string[]).includes(page.url.searchParams.get('chord') ?? '')
			? (page.url.searchParams.get('chord') as ChordPair)
			: 'cat-works'
	);
	const chordSides = $derived(sidesOf(chordPair));
	function setChordPair(next: ChordPair) {
		const url = new URL(page.url);
		if (next === 'cat-works') url.searchParams.delete('chord');
		else url.searchParams.set('chord', next);
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}
	// CONTRACT SCOPE per signature year (user, 2026-08-23, the sponsored
	// page's per-year form): counted from the contract nodes themselves —
	// every year from the first signature to the last, one line per scope
	const todayIso = new Date().toISOString().slice(0, 10);
	const scopeYears = $derived.by(() => {
		const ns = network?.nodes ?? [];
		const ys = ns.map((n) => +(n.d ?? '').slice(0, 4)).filter((y) => y > 0);
		if (!ys.length) return null;
		const y0 = Math.min(...ys);
		const y1 = Math.max(...ys);
		const years = Array.from({ length: y1 - y0 + 1 }, (_, i) => y0 + i);
		const count = (kind: string) =>
			years.map((yr) => ns.filter((n) => n.dk === kind && +(n.d ?? '').slice(0, 4) === yr).length);
		return { years, series: SCOPE_ORDER.map((k) => ({ key: k, values: count(k) })) };
	});
	const catItems = $derived(
		o.categories.map((c) => ({ key: c.key, label: splitHint(c.label_en ?? c.label).label, n: c.n }))
	);
	const chordData = $derived.by(() => {
		const none = 'no specific work named';
		if (chordPair === 'cat-scope' && network) return catScope(network.nodes, catItems);
		if (chordPair === 'scope-works' && network)
			return scopeWorks(
				network.nodes,
				o.themes.themes.map((w) => ({ theme: w.theme, label: w.label_en })),
				none
			);
		return catWorks(worksSplit, catItems, none);
	});
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
	// the pair reads all in lower case (user, 2026-08-22) — only the opening
	// letter is dropped, so proper nouns («National Reforestation Plan») stay
	const lowerRows = <T extends { label: string }>(rows: T[]): T[] =>
		rows.map((r) => ({ ...r, label: r.label.charAt(0).toLowerCase() + r.label.slice(1) }));
	// a category name's explanatory tail — after a «:», or a trailing
	// parenthetical — moves into an i beside the short name (user, 2026-08-22)
	const splitHint = (s: string): { label: string; hint?: string } => {
		const colon = s.indexOf(':');
		if (colon > 0)
			return { label: s.slice(0, colon).trim(), hint: `including ${s.slice(colon + 1).trim()}` };
		const paren = s.match(/^(.*\S)\s+\((.+)\)$/);
		if (paren) return { label: paren[1], hint: paren[2] };
		return { label: s };
	};
	const catRows = $derived(
		[...o.categories]
			.sort((a, b) => (ctLens === 'eur' ? b.eur - a.eur : b.n - a.n))
			.map((c) => ({
				label: c.label_en ?? c.label,
				value: ctLens === 'eur' ? c.eur : c.n,
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
		<!-- the BASIS, said once for the whole page (copy pass 2026-08-23): the
		     frames below no longer repeat it -->
		<p class="basis">
			All amounts are the contracts' stated values excl. VAT, from the ΚΗΜΔΗΣ records and the
			signed contract PDFs; a contract signed by several firms or covering several regional
			units is split equally between them — the documents state no other allocation; payments
			(ΚΗΜΔΗΣ and Διαύγεια) are a separate layer —
			<a href="/methodology#stated-basis">basis</a> · <a href="/methodology#even-split">split</a>.
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
		insight={allocFacts
			? `${ruLabel(allocFacts.top.pe)} holds the most money — ${pct(allocFacts.topShare)} of the programme — and ${grInt(allocFacts.nHalf)} of the ${grInt(allocFacts.n)} regional units with Anti-nero works hold half of it. ${grInt(map.contracts.filter((c) => (c.regions?.length ?? 0) > 1).length)} of the ${grInt(map.contracts.length)} contracts cover more than one regional unit; on the «individual dots» lens such a contract is counted in every region it touches, so counts overlap across regions where euros never do.`
			: ''}
		caveat="Work regions as named in each signed contract; contractor seats as stated in the contract's party clause, geocoded."
		anchor="map"
		methodology="even-split"
	>
		<AntineroMap data={map} />
		{#if yearCells}
			<!-- the years as a film strip, one mini choropleth each, ONE
			     shared scale (small multiples over a year slider — the
			     doctrine); replaces the MONEY BY REGION PER YEAR facets -->
			<div class="yearmaps" id="pe-yearly">
				{#each yearCells.per as ym (ym.year)}
					<div class="ym">
						<div class="ym-head">
							<strong>{ym.year}</strong>
							<span>{eurShort(ym.total)}</span>
						</div>
						<PaperMap
							interactive={false}
							colorOf={(pe) => yearCells.choro(ym.cells.get(pe) ?? 0)}
						/>
					</div>
				{/each}
			</div>
			<p class="ym-note">
				Stated € by work region at each contract's signature year, even-split — the five maps
				share one colour scale, so a region's tone is comparable across years.
			</p>
		{/if}
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
		title="FLOWS OF MONEY"
		insight="Only {localPct}% of the money is awarded to companies based within the regional unit where the works are carried out. {maxReach.name} alone works in {maxReach.n} regional units; the «by company» lens breaks the same flows down to the {grInt(Object.keys(net.contractors).length)} firms that carry them."
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
			)} firms in all: a venture with members on record is replaced by them, one whose members no document names keeps its own row, so ${eurShort(
				o.consortiums.eur_unsplit
			)} sits identically in both views.`
		: `The top ${grInt(rankFacts.n)} contractors hold ${pct(rankFacts.share)} of the programme (${eurShort(rankFacts.top)} of ${eurShort(o.kpis.total_eur)}), out of ${grInt(o.kpis.n_contractors)} in all. Switch to «by member firm» to attribute the money to the firms behind the joint ventures.`}
	caveat={rankMode === 'firm' ? 'Venture members from the ΓΕΜΗ register and the signed contracts.' : ''}
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
		<BarH rows={topRows} color="var(--c-antinero)" inside barHeight={35} />
	</div>
</ChartFrame>

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
		title="AWARDING PROCESS"
		insight={`The awarding body of every Anti-nero contract is the Ministry of Environment and Energy, acting through ${grInt(uf.n_units)} operating units${unitFacts ? ` — the ${unitFacts.label} alone handled ${pct(unitFacts.share)} of the money (${eurShort(unitFacts.eur)})` : ''}; the ${grInt(uf.n_top)} biggest contractors take ${eurShort(uf.top_eur)} of the ${eurShort(uf.total_eur)} (${grInt(uf.n_contractors)} contractors in all).`}
		caveat="Awarding body and operating units as recorded in ΚΗΜΔΗΣ."
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
			marginLeft={50}
			marginRight={420}
			columnX={[0.09, 0.40, 0.76]}
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
		title="AWARD PROCEDURES"
		insight={`${grInt(directN)} of the ${grInt(procTotalN)} contracts — ${pct((directEur / procTotalEur) * 100, 0)} of the money — went by direct award; open procedures are the exception, not the rule.`}
		caveat="Procedures as recorded in ΚΗΜΔΗΣ, named in the wording of Directive 2014/24/EU; «Direct award» is the ν.4412/2016 άρθρο 118 route, which has no Directive equivalent."
		anchor="procedures"
		methodology="procedures"
	>
		<div class="rankw">
			<BarH rows={procRows} color="var(--c-antinero)" inside barHeight={35} highlight={(r) => !!(r as { direct?: boolean }).direct} />
		</div>
	</ChartFrame>

	<ChartFrame
		title="DIRECT AWARDS"
		insight={`The ${grInt(o.direct_awards.n as number)} direct-award contracts pile up around €${daModal}, far beyond the ν.4782/2021 ceilings for direct awards (€30k and €60k, the dashed lines): the RRF emergency provisions allowed awards above them.`}
		caveat="Ceilings: ν.4782/2021 on άρθρο 118 ν.4412/2016, defined excl. VAT."
		anchor="direct-awards"
		methodology="procedures"
	>
		<LogHistogram
			labels={(o.direct_awards.labels as string[]).map(bracket)}
			counts={o.direct_awards.counts as number[]}
			edges={o.direct_awards.edges as number[]}
			color="var(--c-antinero)"
			thresholds={miniThresholds}
		/>
	</ChartFrame>
</div>

<Defer height={340}>
{#if swarm}
	<ChartFrame
		title="CONTRACT VALUES"
		insight={valueFacts
			? `The median contract is worth ${eurShort(valueFacts.median)}, the largest ${eurShort(valueFacts.max)}; ${valueFacts.above === valueFacts.n ? `every one of the ${grInt(valueFacts.n)} — the smallest at ${eurShort(valueFacts.min)} —` : `${grInt(valueFacts.above)} of the ${grInt(valueFacts.n)}`} lies above the €60k direct-award ceiling.`
			: ''}
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

{#if o.categories.length && topCat}
	<div class="scopetype">
		<ChartFrame
			title="CONTRACT SCOPE"
			insight={`${grInt(o.deliverables?.study_and_works ?? 0)} of ${grInt(
				o.kpis.n_contracts
			)} contracts are design-build — the contractor first drafts the studies, then executes the works they define.`}
			caveat="Read from each contract's own signed text or its call; «study & works» is the design-build clause, quoted verbatim on the contract page; «study only» are the contracts whose object is the studies."
			anchor="scope"
			methodology="categories"
		>
			<div>
				<StackedShareBar
					height={34}
					segments={[
						{ value: o.deliverables?.study ?? 0, label: SCOPE_LABELS.study, color: SCOPE_COLORS.study, badge: 'outleft' },
						{ value: o.deliverables?.study_and_works ?? 0, label: SCOPE_LABELS.study_and_works, color: SCOPE_COLORS.study_and_works, badge: 'above' },
						{ value: o.deliverables?.works ?? 0, label: SCOPE_LABELS.works, color: SCOPE_COLORS.works, badge: 'above' }
					]}
				/>
			</div>
			{#if scopeYears}
				<!-- the sponsored page's per-year form (user, 2026-08-23): contracts
				     signed per year, one line per scope, in the scope tones -->
				<div class="sublabel peryear">CONTRACTS BY SCOPE PER YEAR</div>
				<AreaYears
					years={scopeYears.years}
					width={520}
					height={168}
					janRules
					dots
					today={todayIso}
					legend={false}
					series={scopeYears.series.map((s) => ({
						label: SCOPE_LABELS[s.key],
						color: SCOPE_COLORS[s.key],
						values: s.values,
						kind: 'line' as const,
						dash: false
					}))}
				/>
			{/if}
		</ChartFrame>

		<ChartFrame
			title="CONTRACT TYPE"
			insight={`«${catShort.get(topCat.key) ?? topCat.label_en ?? topCat.label}» dominates with ${eurShort(topCat.eur)} across ${grInt(topCat.n)} contracts — ${pct((topCat.eur / o.kpis.total_eur) * 100)} of the programme.`}
			caveat="One category per contract, curated from the project title in the signed PDF (CPV codes only as tie-breaker)."
			anchor="categories"
			methodology="categories"
		>
			{#snippet controls()}
				<SegmentToggle
					param="ct"
					fallback="eur"
					options={[
						{ value: 'eur', label: 'stated net €' },
						{ value: 'n', label: 'number of contracts' }
					]}
				/>
			{/snippet}
			<BarH
				rows={lowerRows(catRows).map((r) => ({ ...r, ...splitHint(r.label) }))}
				color="#2b2b2b"
				inside
				barHeight={35}
				fmt={ctLens === 'eur' ? eurShort : grInt}
				valuesRight
			/>
		</ChartFrame>
	</div>
{/if}

{#if o.categories.length && topCat}
	{@const works = o.themes}
	<!-- the chord alone (user, 2026-08-23): the dots and the works × category
	     rows are PARKED — WorkDots.svelte / WorksByCategory.svelte stay, off
	     the page -->

	{#snippet leftPick()}
		<div class="cpick" role="group">
			<button
				class:active={chordSides.left === 'works'}
				onclick={() => setChordPair(pairFor(chordPair, 'left', 'works'))}>works named</button
			>
			<button
				class:active={chordSides.left === 'scope'}
				onclick={() => setChordPair(pairFor(chordPair, 'left', 'scope'))}>contract scope</button
			>
		</div>
	{/snippet}
	{#snippet rightPick()}
		<div class="cpick" role="group">
			<button
				class:active={chordSides.right === 'category'}
				onclick={() => setChordPair(pairFor(chordPair, 'right', 'category'))}>main category</button
			>
			<button
				class:active={chordSides.right === 'scope'}
				onclick={() => setChordPair(pairFor(chordPair, 'right', 'scope'))}>contract scope</button
			>
		</div>
	{/snippet}
	<ChartFrame
		title="TYPES OF WORKS"
		insight={`${chordFacts
			.map((f) =>
				f.left
					? `${f.right.label}: ${grInt(f.n)} of its ${grInt(f.right.n)} contracts ${chordSides.left === 'works' ? 'name' : 'are'} «${f.left.label}»`
					: ''
			)
			.filter(Boolean)
			.join('; ')}${chordSides.left === 'works' || chordSides.right === 'works' ? `; ${grInt(works.unspecified)} of the ${grInt(works.n_contracts)} contracts name no specific work` : ''}. ${chordPair === 'cat-scope' ? 'Both halves are one per contract, so every arc and ribbon is a plain contract count.' : 'A contract naming several works lies under several ribbons, so an arc on the one-per-contract half measures mentions; the hover card counts contracts.'}`}
		caveat={`Works as named in the signed titles or, where a title names none, in the call’s description of the lot (${grInt(o.themes.themes.length)} kinds, verbatim clause kept per contract); a contract counts under every work it names. Categories and scope: one per contract, from the same documents.`}
		anchor="works"
		methodology="categories"
	>
		<CatWorkChord data={chordData} leftControl={leftPick} rightControl={rightPick} />
	</ChartFrame>
{/if}

<Defer height={640}>
{#if network}
	<ChartFrame
		title={netCopy.title}
		insight={netCopy.subtitle}
		caveat="A call is the πρόσκληση the contract cites in its own signed text ({grInt(
			network.stats.n_calls
		)} resolved this way); the fire season is the statutory 1 May – 31 October."
		anchor="network"
		methodology="procurement-families"
	>
		{#snippet controls()}
			<SegmentToggle param="net" fallback="scope" options={NET_MODES} />
		{/snippet}
		<ContractNetwork
			nodes={network.nodes.map((n) => ({ ...n, phase: n.dk }))}
			stats={network.stats}
			mode="time"
			lens={netMode === 'type' ? 'type' : 'scope'}
			catLabels={Object.fromEntries(o.categories.map((c) => [c.key, catShort.get(c.key) ?? c.key]))}
			season={network.fire_season}
		/>
	</ChartFrame>
{:else}
	<div class="skeleton" id="network" style="height: 620px"></div>
{/if}
</Defer>

<div class="pair">
	<ChartFrame
		title="MONEY PER YEAR"
		insight={moneyFacts
			? `${moneyFacts.year} was the biggest contracting year (${eurShort(moneyFacts.eur)}); payments peaked in ${moneyFacts.payYear} (${eurShort(moneyFacts.payEur)}) — they run behind contracting by design.`
			: ''}
		caveat="€ contracted: stated value by signature year; € paid: payment orders by payment year."
		anchor="money-per-year"
		methodology="stated-basis"
	>
		{#snippet controls()}
			<SegmentToggle
				param="money"
				fallback="contracted"
				options={[
					{ value: 'contracted', label: '€ contracted' },
					{ value: 'paid', label: '€ paid' }
				]}
			/>
		{/snippet}
		{#if yearMoneyRows.length}
			<BarH rows={yearMoneyRows} color="var(--c-antinero)" inside barHeight={35} valuesRight />
		{:else}
			<div class="skeleton" style="height: 240px"></div>
		{/if}
	</ChartFrame>

	<ChartFrame
		title="CUMULATIVE DISBURSEMENT"
		insight={paidFacts
			? `${paidFacts.last} stands at ${eurShort(paidFacts.lastEur)} so far${paidFacts.prev ? `, ${paidFacts.lastEur >= paidFacts.prevSameDay ? 'ahead of' : 'behind'} ${paidFacts.prev}'s ${eurShort(paidFacts.prevSameDay)} by the same day of that year` : ''}; ${paidFacts.year} was the heaviest full year (${eurShort(paidFacts.eur)}).`
			: ''}
		caveat="Payment orders (ΚΗΜΔΗΣ and Διαύγεια) cumulated within each calendar year, day by day."
		anchor="disbursement"
		methodology="payments"
	>
		{#if payments}
			<DisbursementCurves {payments} />
		{:else}
			<div class="skeleton" style="height: 340px"></div>
		{/if}
	</ChartFrame>
</div>

<Defer height={900}>
{#if payments}
	<ChartFrame
		title="PAYMENTS TIMELINE"
		insight="{payments.lag?.median_days != null ? `The median payment order arrives ${grInt(payments.lag.median_days)} days after the contract's signature, the first payment after ${grInt(payments.lag.median_first_days ?? 0)} days (over ${grInt(payments.lag.n_contracts)} contracts); the early cohorts' payments stretch years past their signing. ` : ''}The biggest single month was {peak.m} ({eurShort(
			peak.eur
		)})."
		caveat="Payment orders from ΚΗΜΔΗΣ, the rest from Διαύγεια; {grInt(
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

{:else}
	<div class="skeleton" style="height: 480px"></div>
{/if}
</Defer>

<!-- STUDY COSTS is PARKED (user, 2026-08-23): the study-fee curation has
     a wrong amount, a double count and an eleven-contract coverage hole
     (DATA_DECISIONS) — StudyScatter.svelte and the studies payload stay,
     the frame is off the page until the data is trusted -->

{#if o.cpvs.length}
	{@const topCpv = o.cpvs[0]}
	{@const tree = o.cpv_tree}
	{@const div77 = tree?.divisions.find((d) => d.code.startsWith('77'))}
	{@const div45 = tree?.divisions.find((d) => d.code.startsWith('45'))}
	{@const topCode = tree?.divisions.flatMap((d) => d.classes.flatMap((k) => k.codes)).sort((a, b) => b.n - a.n)[0]}
	<ChartFrame
		title="CPV CODES"
		insight={tree
			? `The ${grInt(tree.n_codes)} codes the ${grInt(tree.n_contracts)} contracts declare — ${grInt(tree.codes_per_contract)} per contract on average — fall into ${grInt(tree.divisions.length)} of the vocabulary’s divisions: ${div77 ? `${grInt(div77.n)} contracts declare a code of «${div77.name_en}»` : ''}${div45 ? ` and ${grInt(div45.n)} a code of «${div45.name_en}»` : ''} — the same contracts filed as services and as works at once. The most common single code, «${topCode?.name_en ?? topCpv.desc}», appears on ${grInt(topCode?.n ?? topCpv.n)} (${pct(((topCode?.n ?? topCpv.n) / o.kpis.n_contracts) * 100)}).`
			: ''}
		caveat="Codes as declared in ΚΗΜΔΗΣ, named from the EU CPV 2008 vocabulary (division → class → code); a contract declares several, so the counts overlap and are never summed."
		anchor="cpvs"
		methodology="cpv"
	>
		{#if tree}
			<CpvColumns divisions={tree.divisions} total={o.kpis.n_contracts} />
		{/if}
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
		border: 1px solid var(--line); /* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		--map-accent: var(--c-antinero); /* the zoom buttons' circle hue */
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
	/* the chord's per-heading toggles: SegmentToggle's dress, one size
	   smaller, pointer events on (the heading block around them is inert) */
	.cpick {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
		pointer-events: auto;
	}
	.cpick button {
		font: inherit;
		font-size: 11px;
		padding: 2px 8px;
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.cpick button + button {
		border-left: 1px solid var(--line);
	}
	.cpick button.active {
		background: var(--ink);
		color: var(--paper);
	}
	/* the MAP-label dress for a sub-heading inside a frame */
	.sublabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		color: var(--c-antinero);
		margin-bottom: var(--sp-2);
	}
	.sublabel.peryear {
		margin-top: var(--sp-4, 1rem);
	}
	/* the page's one BASIS line under the programme paragraph */
	.basis {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.basis a {
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
	/* CONTRACT SCOPE | CONTRACT TYPE side by side, equal halves (user,
	   2026-08-22), mirroring the sponsored PROJECT SCOPE | PROJECT TYPE */
	.scopetype {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-7, 2.5rem);
		/* the two frames take ONE height and put their caveats on one
		   baseline — the shorter side keeps its slack above its caveat
		   (user, 2026-08-23: the columns ended at different lines) */
		align-items: stretch;
	}
	.scopetype :global(figure.frame) {
		display: flex;
		flex-direction: column;
	}
	.scopetype :global(figure.frame > .foot) {
		margin-top: auto;
	}
	@media (max-width: 900px) {
		.scopetype {
			grid-template-columns: 1fr;
		}
	}
	/* inside the half-width pair the page's left margin is another frame:
	   the lightbulb note flows ABOVE the chart instead (user, 2026-08-22 —
	   it overlapped the neighbour's graph) */
	/* the number line takes the height of the neighbour's FIRST bar row
	   (35px bar + 6px gap), so the scope bar's top meets the SECOND type
	   bar (user, 2026-08-22) */
	.scopetype :global(.nums) {
		height: 41px;
	}
	/* the numbers sit on the SAME line as the neighbour's first-row value
	   (user, 2026-08-22): centred on the 35px first bar row */
	.scopetype :global(.nums span) {
		bottom: 13.5px;
	}
	/* both title rows the same height, toggle or not, so the two charts
	   start at the same y (user, 2026-08-22) */
	.scopetype :global(.titlerow) {
		display: flex;
		align-items: center;
		min-height: 2.25rem;
	}
	/* the five year maps under the allocation maps: a film strip on one
	   shared scale (user, 2026-08-22) */
	.yearmaps {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: var(--sp-4);
		margin-top: var(--sp-5);
	}
	@media (max-width: 1000px) {
		.yearmaps {
			grid-template-columns: repeat(3, 1fr);
		}
	}
	.ym-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: var(--sp-1);
		font-size: var(--fs-13);
	}
	.ym-head strong {
		font-size: var(--fs-14);
	}
	.ym-head span {
		color: var(--ink-soft);
		font-variant-numeric: tabular-nums;
	}
	.ym-note {
		margin: var(--sp-3) 0 0;
		font-size: var(--fs-12);
		color: var(--ink-soft);
		max-width: 60rem;
	}
</style>
