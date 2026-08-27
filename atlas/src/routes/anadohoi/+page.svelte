<script lang="ts">
	import { ruLabel, regionOfPe, pesOfRegion } from '$lib/transforms/regions';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import DatasetCard from '$lib/ui/DatasetCard.svelte';
	import Tile from '$lib/ui/Tile.svelte';
	import Text from '$content/datasets/anadohoi.md';
	import SponsorGroups from '$lib/charts/SponsorGroups.svelte';
	import SponsorTypes from '$lib/charts/SponsorTypes.svelte';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import FireResponse from '$lib/charts/FireResponse.svelte';
	import CrewMap, { type CrewLink } from '$lib/sections/CrewMap.svelte';
	import { apiGetCached } from '$lib/api';
	import Defer from '$lib/ui/Defer.svelte';
	import Hint from '$lib/ui/Hint.svelte';
	import BarH from '$lib/charts/BarH.svelte';
	import PromiseGantt from '$lib/charts/PromiseGantt.svelte';
	import StatusWaffle from '$lib/charts/StatusWaffle.svelte';
	import StackedShareBar from '$lib/charts/StackedShareBar.svelte';
	import AreaYears from '$lib/charts/AreaYears.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import FiresLayer from '$lib/maps/FiresLayer.svelte';
	import { loadCentroids, loadEffisFires, loadEviaZones, spreadOverlaps } from '$lib/maps/useGeo';
	import { dmy, eurShort, grInt, pct } from '$lib/transforms/format';
	import { fireEn } from '$lib/transforms/names';
	import { COLOR, NODATE_COLOR, noDate, type GanttProject } from '$lib/charts/ganttTheme';
	import ProjectCard from '$lib/charts/ProjectCard.svelte';
	import { cardFor } from '$lib/charts/projectCard';
	import { dev } from '$app/environment';
	import { page } from '$app/state';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.o);
	const k = $derived(o.kpis);

	// the card (user mock, 2026-08-27): three KPIs, the URL parameters this
	// page reads (any opens the card unfolded), and the map tile's size
	const PARAMS = ['sg'] as const;
	// The card's KPI cards (Artboard 4, user 2026-08-27): the user's own
	// sentences, every number computed from the payload. The widths are the
	// artboard's 173,2 / 165,7 / 336,8.
	// the sentences on the ROWS the user broke them into (the edit of
	// 2026-08-27); the numbers computed from the payload
	const kpiRich = $derived([
		{
			w: 190,
			parts: [{ num: grInt(k.n_projects), word: 'acts' }],
			lines: [
				'for designating private companies',
				'as restoration and/or reforestation',
				'contractors have been made public'
			]
		},
		{
			w: 190,
			parts: [{ num: grInt(k.n_companies), word: 'companies' }],
			lines: ['have been appointed as restoration', 'and/or reforestation contractors']
		},
		{
			w: 299.4,
			parts: [
				{ num: grInt(k.n_stated) },
				{ word: 'of' },
				{ num: grInt(k.n_projects) },
				{ word: 'acts state a figure' }
			],
			tailLines: ['those acts amount', 'to a value of'],
			big: eurShort(k.stated_eur).toLowerCase()
		}
	]);
	/** the card map's own drill (user, 2026-08-27): only a περιφέρεια that
	 *  holds projects answers a click, the map zooms to it, and ANY click
	 *  on the map while zoomed returns to the frame */
	let selCard = $state<string | null>(null);
	const selCardPes = $derived(selCard ? pesOfRegion(selCard) : null);
	/** the card map's frame picker (dev): pan/zoom the small map, read the
	 *  lon/lat box it shows, and set it as CARD_BOUNDS */
	let pickCard = $state(false);
	let pickedCard = $state<{ center: [number, number]; k: number; bounds?: [[number, number], [number, number]] } | null>(null);
	let tileW = $state(0);
	let tileH = $state(0);
	let gW = $state(0);
	let gH = $state(0);
	let sW = $state(0);
	let sH = $state(0);
	/** how many rows the card's timeline could fit, said in its legend */
	let ganttFit = $state({ shown: 0, total: 0 });

	// WHO THE SPONSORS ARE measures: € committed or a plain project count
	// (?sg=), the CONTRACT TYPE lens one dataset over
	const sgLens = $derived<'eur' | 'n'>(page.url.searchParams.get('sg') === 'n' ? 'n' : 'eur');

	// PROJECTS PER REGION (περιφέρεια, not Π.Ε. — user, 2026-08-25): each
	// live project's Π.Ε. resolves to its NUTS-2 region via the curated
	// pe_names_en nuts_id bridge; the two pe-less projects counted aside
	const regionCounts = $derived.by(() => {
		const by = new Map<string, number>();
		let unresolved = 0;
		for (const p of ganttProjects) {
			const r = regionOfPe(p.pe);
			if (r) by.set(r, (by.get(r) ?? 0) + 1);
			else unresolved++;
		}
		return {
			rows: [...by.entries()].sort((a, b) => b[1] - a[1]),
			unresolved
		};
	});
	const projectRegions = $derived(new Set(regionCounts.rows.map(([r]) => r)));
	// click a project region → the map zooms to its whole extent
	let selRegion = $state<string | null>(null);
	const selRegionPes = $derived(selRegion ? pesOfRegion(selRegion) : null);

	// the TIMELINE's dashed rule marks the ACTUAL current day (local clock);
	// the statuses themselves are as of the data's status_as_of date, which
	// the chart caveat states
	const todayIso = new Date().toLocaleDateString('en-CA');
	// map ↔ METRICS hover link: one shared highlighted project. The
	// TIMELINE card docks at the map's outer LEFT middle; hovering the
	// METRICS also docks the black category note at its outer RIGHT middle.
	let hoveredAda = $state<string | null>(null);
	let hoverCard = $state<{ x: number; y: number; anchor: 'left' | 'right'; ada: string } | null>(
		null
	);
	let catTip = $state<{ x: number; y: number; maxW: number; text: string } | null>(null);
	let mapEl = $state<HTMLElement | null>(null);
	let waffleEl = $state<HTMLElement | null>(null);
	const CAT_LABEL: Record<string, string> = {
		completed: 'projects with identified completion act',
		active: 'projects within deadline — no completion act identified',
		nodate: 'projects without specific dates for implementation',
		no_completion_recorded: 'projects past deadline — no completion act identified',
		revoked: 'revoked'
	};
	// dev-only map frame picker: pan/zoom once, copy the view, bake it in
	let pickFrame = $state(false);
	let pickedView = $state<{ center: [number, number]; k: number } | null>(null);
	// the page's FIXED frame — paste the picker's output here to change it
	// fires-map relief style toggle: greyscale plate vs hypsometric tints
	// (both baked by scripts/build_relief.py from the same shading pass)
	let reliefStyle = $state<'grey' | 'hypso'>('grey');
	const reliefAssets = $derived(
		reliefStyle === 'hypso'
			? { lo: '/geo/relief_hypso.avif', hi: '/geo/relief_hypso_hi.avif' }
			: { lo: '/geo/relief.avif', hi: '/geo/relief_hi.avif' }
	);
	/** the card's map frames the WHOLE country, Crete to Thrace, Corfu to
	 *  Rhodes (user, 2026-08-27): the box from Othonoi and Gavdos to Rhodes
	 *  and Ormenio — Kastellorizo left out by decision — fitted with a 6%
	 *  margin on every side WHATEVER the tile's shape. A fixed centre-and-
	 *  zoom (k 1,05) had left Crete 4 px from the edge in a wide tile, and
	 *  a browser window is rarely the artboard's 16:9 */
	const CARD_BOUNDS: [[number, number], [number, number]] = [
		[18.2336, 34.7812],
		[28.7256, 41.9096]
	];
	/** the box's own shape on a Mercator map: width over height in
	 *  projected units — so the map is drawn exactly as wide as the
	 *  country and shows no land beyond its sides (user, 2026-08-27) */
	const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
	const CARD_ASPECT =
		((CARD_BOUNDS[1][0] - CARD_BOUNDS[0][0]) * Math.PI) /
		180 /
		(mercY(CARD_BOUNDS[1][1]) - mercY(CARD_BOUNDS[0][1]));
	/** the frame the user chose with the picker (2026-08-27, «bounds:
	 *  [[18.2336, 34.7812], [28.7256, 41.9096]] · k 0.979»): the visible box
	 *  itself, so no padding — it is the frame; the key sits ON the map in
	 *  its bottom-left corner */
	const MAP_PAD = 0;
	void CARD_ASPECT;
	const MAP_VIEW: { center: [number, number]; k: number } | null = {
		center: [23.8305, 38.3566],
		k: 1.08
	};

	function showHover(ada: string | null, source: 'map' | 'metrics') {
		hoveredAda = ada;
		if (!ada) {
			hoverCard = null;
			catTip = null;
			return;
		}
		const mr = mapEl?.getBoundingClientRect();
		hoverCard = mr
			? {
					// hangs in the margin left of the map, clamped on-screen
					x: Math.max(282, mr.left - 12),
					y: mr.top + mr.height / 2,
					anchor: 'left',
					ada
				}
			: null;
		if (source === 'metrics') {
			const wr = waffleEl?.querySelector('.waffle')?.getBoundingClientRect();
			const hp = ganttProjects.find((q) => q.ada === ada);
			const k = hp ? (noDate(hp) ? 'nodate' : hp.status) : '';
			catTip =
				wr && k
					? {
							x: wr.right + 12,
							y: wr.top + wr.height / 2,
							maxW: Math.max(140, window.innerWidth - (wr.right + 12) - 16),
							text: `${grInt(waffleStatuses[k] ?? 0)} ${CAT_LABEL[k] ?? k}`
						}
					: null;
		} else {
			catTip = null;
		}
	}
	const live = $derived(o.projects.filter((p) => p.status !== 'superseded'));
	const nCompleted = $derived(k.statuses['completed'] ?? 0);
	const nNoAct = $derived(k.statuses['no_completion_recorded'] ?? 0);

	// same palette as the status waffle (see StatusWaffle ORDER)
	const STATUS_COLOR: Record<string, string> = {
		completed: 'var(--c-anadohoi)',
		active: '#52b788',
		no_completion_recorded: '#8F8F8F',
		revoked: '#000000'
	};

	// fires, chronological, «εκτός πυρκαγιάς» last
	const fireCards = $derived.by(() => {
		const f = [...o.fires];
		const i = f.findIndex((x) => x.fire === 'εκτός πυρκαγιάς');
		if (i >= 0) f.push(...f.splice(i, 1));
		return f;
	});

	const sponsorRows = $derived(
		o.sponsors
			.filter((s) => s.budget > 0)
			.slice(0, 12)
			.map((s) => ({ label: s.company, value: s.budget }))
	);

	// the commitment an amendment raised the most (e.g. a δωρεά increase)
	const topRaise = $derived.by(() => {
		let best = null as null | (typeof live)[number];
		for (const p of live) {
			if (p.budget === null || p.budget_stated === null) continue;
			if (p.budget <= p.budget_stated) continue;
			if (!best || p.budget > (best.budget ?? 0)) best = p;
		}
		return best;
	});

	// TIMELINE rows: fold each restated (superseded) act into its successor —
	// one commitment, one row; the predecessor contributes the bar's origin
	// (start0) and its initial money (budget0), drawn as a height step at the
	// restatement date. Only one such pair exists in the data (6ΗΥΗ → ΨΟΕ8).
	const ganttProjects = $derived.by(() => {
		const out = [];
		for (const p of o.projects) {
			if (p.status === 'superseded') continue;
			const pred = o.projects.find((q) => q.superseded_by === p.ada);
			out.push({
				...p,
				// one sponsor, one name: the ranking's merged group label —
				// the verbatim act names stay on the project pages
				company: p.group ?? p.company,
				...(pred ? { start0: pred.start, budget0: pred.budget_stated } : {})
			});
		}
		return out;
	});

	// waffle categories = the TIMELINE's, from the same fold: actives split
	// into dated ("active") and no-implementation-dates ("nodate")
	const waffleStatuses = $derived.by(() => {
		const s: Record<string, number> = {};
		for (const p of ganttProjects) {
			const key = noDate(p) ? 'nodate' : p.status;
			s[key] = (s[key] ?? 0) + 1;
		}
		return s;
	});

	// deliverables / works-kind waffles: same folded population as the
	// status waffle (superseded acts folded into their successors)
	// the page's green and transparencies of it (user, 2026-08-22);
	// light → dark, small first
	const DELIV_META: [string, string, string][] = [
		['study', 'study only', 'rgba(45, 106, 79, 0.3)'],
		['study_and_works', 'study & works', 'rgba(45, 106, 79, 0.62)'],
		['works', 'works only', '#2d6a4f']
	];
	const KIND_META: [string, string, string][] = [
		['anadasosi', 'reforestation', '#b5b5b5'],
		['both', 'restoration & reforestation', '#6c6c6c'],
		['apokatastasi', 'restoration', '#3d3d3d'],
		['', 'not stated', '#d8d8d8']
	];
	const countBy = (field: 'deliverables' | 'works_kind') => {
		const s: Record<string, number> = {};
		for (const p of ganttProjects) {
			const key = (p as Record<string, unknown>)[field] ?? '';
			s[key as string] = (s[key as string] ?? 0) + 1;
		}
		return s;
	};
	const delivGroups = $derived.by(() => {
		const s = countBy('deliverables');
		return DELIV_META.map(([key, label, color]) => ({ key, label, color, count: s[key] ?? 0 }));
	});

	// sponsor → executing forest co-op links, curated from the act trails
	interface Executor {
		name: string;
		dase_vat: string | null;
		ada: string;
		excerpt: string;
		note?: string;
	}
	const execRows = $derived(
		ganttProjects
			.filter((p) => Array.isArray(p.executors) && p.executors.length)
			.map((p) => ({
				ada: p.ada,
				company: p.company,
				where: (p.pe ? ruLabel(p.pe) : null) ?? fireEn(p.fire) ?? '',
				executors: p.executors as Executor[]
			}))
			.sort((a, b) => a.company.localeCompare(b.company, 'el'))
	);
	const nExecCoops = $derived(
		new Set(execRows.flatMap((r) => r.executors.map((e) => e.dase_vat ?? e.name))).size
	);
	/** the same links GROUPED BY SPONSOR (user, 2026-08-24): ΔΕΗ held four
	 *  separate blocks in the old table, which is most of why the frame ran
	 *  to 922px. One line per sponsor, its projects as small place links. */
	const execBySponsor = $derived.by(() => {
		type Row = (typeof execRows)[number];
		const by = new Map<string, { company: string; projects: Row[];
			coops: Map<string, Executor> }>();
		for (const r of execRows) {
			const g = by.get(r.company) ?? {
				company: r.company, projects: [] as Row[], coops: new Map<string, Executor>()
			};
			g.projects.push(r);
			for (const e of r.executors) g.coops.set(e.dase_vat ?? e.name, e);
			by.set(r.company, g);
		}
		return [...by.values()]
			.map((g) => ({
				...g,
				coopList: [...g.coops.values()],
				// ΔΕΗ holds four Evia projects, so the old row printed «R.U.
				// Evia» four times and wrapped: name each PLACE once, and
				// number the projects only where there is more than one
				places: [...new Set(g.projects.map((p) => p.where))]
			}))
			.sort((a, b) => b.coopList.length - a.coopList.length
				|| a.company.localeCompare(b.company, 'el'));
	});
	/** the co-op that turns up under the most different sponsors — the one
	 *  fact a flat list of names cannot show */
	const execRepeat = $derived.by(() => {
		const by = new Map<string, { name: string; sponsors: Set<string> }>();
		for (const r of execRows)
			for (const e of r.executors) {
				const k = e.dase_vat ?? e.name;
				const g = by.get(k) ?? { name: e.name, sponsors: new Set<string>() };
				g.sponsors.add(r.company);
				by.set(k, g);
			}
		return [...by.values()].sort((a, b) => b.sponsors.size - a.sponsors.size)[0] ?? null;
	});
	/** the fire lanes and what they say — every figure computed here, so
	 *  the frame's copy cannot drift from the data (2026-08-24) */
	const fireLanes = $derived(
		(o.fires ?? []).filter(
			(f) => f.fire !== 'εκτός πυρκαγιάς' && f.burn_date && f.acts?.length
		)
	);
	const fireFacts = $derived.by(() => {
		const withLag = fireLanes.filter((f) => f.lag_days != null);
		if (!withLag.length) return null;
		const lags = withLag.map((f) => f.lag_days as number).sort((a, b) => a - b);
		const mid = Math.floor(lags.length / 2);
		const median = lags.length % 2 ? lags[mid] : Math.round((lags[mid - 1] + lags[mid]) / 2);
		// the contrast the chart exists to show: the biggest fire against the
		// longest wait
		const biggest = [...withLag].sort((a, b) => b.burn_ha - a.burn_ha)[0];
		const slowest = [...withLag].sort((a, b) => (b.lag_days as number) - (a.lag_days as number))[0];
		return {
			median,
			n: withLag.length,
			within60: lags.filter((l) => l <= 60).length,
			fastest: biggest,
			slowest,
			noFire: (o.fires ?? [])
				.filter((f) => f.fire === 'εκτός πυρκαγιάς')
				.reduce((s, f) => s + f.n, 0)
		};
	});
	// WHO DID THE WORK as geography — fetched post-hydration like the
	// other big payloads (user, 2026-08-24)
	let crew = $state.raw<{
		links: CrewLink[];
		unplaced: { coop: string; company: string; why: string }[];
		median_km: number;
		far_150: number;
		n_projects: number;
		n_coops: number;
	} | null>(null);
	$effect(() => {
		apiGetCached<typeof crew>(fetch, '/api/anadohoi/crew-flows').then((v) => (crew = v));
	});
	const kindGroups = $derived.by(() => {
		const s = countBy('works_kind');
		return KIND_META.map(([key, label, color]) => ({ key, label, color, count: s[key] ?? 0 }));
	});

	// CURRENT STATUS' bulb: where the projects are, and how much of the
	// country's burning since 2021 they answer (user's wording, 2026-08-25)
	const atticaPct = $derived(
		(ganttProjects.filter((p) => regionOfPe(p.pe) === 'Attica').length / k.n_projects) * 100
	);
	const eviaPct = $derived(
		(ganttProjects.filter((p) => p.pe === 'Π.Ε. Ευβοίας').length / k.n_projects) * 100
	);
	const scarsAnswered = $derived(
		new Set(ganttProjects.flatMap((p) => (p.scars ?? []).map((s) => s.id))).size
	);

	// the frames' computed findings (the copy doctrine, 2026-08-25):
	// bulbs state findings from the payloads, never hardcoded
	const topSponsor = $derived(o.sponsors[0]);
	const unstatedN = $derived(o.sponsors.reduce((s, x) => s + (x.unstated ?? 0), 0));
	const dWorks = $derived(delivGroups.find((g) => g.key === 'works'));
	const dBoth = $derived(delivGroups.find((g) => g.key === 'study_and_works'));
	const dStudy = $derived(delivGroups.find((g) => g.key === 'study'));
	const topKind = $derived([...kindGroups].sort((a, b) => b.count - a.count)[0]);


	// yearly counts (designations vs completions) for the area chart —
	// folded population; a restated pair counts once, at its FIRST act
	const areaYears = $derived.by(() => {
		const now = new Date().getFullYear();
		const app: Record<number, number> = {};
		const comp: Record<number, number> = {};
		for (const p of ganttProjects) {
			const ds = p.start0 ?? p.start;
			if (ds) app[+ds.slice(0, 4)] = (app[+ds.slice(0, 4)] ?? 0) + 1;
			if (p.completed) comp[+p.completed.slice(0, 4)] = (comp[+p.completed.slice(0, 4)] ?? 0) + 1;
		}
		const y0 = Math.min(...Object.keys(app).map(Number), now);
		const years = Array.from({ length: now - y0 + 1 }, (_, i) => y0 + i);
		return {
			years,
			designations: years.map((yr) => app[yr] ?? 0),
			completions: years.map((yr) => comp[yr] ?? 0)
		};
	});

	// prose blocks keep the right edge the user approved: where the OLD Gantt
	// title's last word («…deadline») used to end. The visible title is now
	// TIMELINE, so a hidden ruler with the reference text preserves the line.
	let rulerEl = $state<HTMLElement | null>(null);
	let proseCut = $state(0);
	$effect(() => {
		const el = rulerEl;
		if (!el) return;
		const measure = () => {
			const parentW = el.parentElement?.clientWidth ?? 0;
			const w = el.getBoundingClientRect().width;
			// when the ruler would wrap (narrow screens) the cut collapses to 0
			proseCut = w > 0 && parentW > w ? Math.round(parentW - w) : 0;
		};
		measure();
		document.fonts?.ready.then(measure);
		const ro = new ResizeObserver(measure);
		if (el.parentElement) ro.observe(el.parentElement);
		return () => ro.disconnect();
	});

	// EFFIS burnt scars for the fires map (lazy, module-cached)
	let firesFc = $state.raw<Awaited<ReturnType<typeof loadEffisFires>> | null>(null);
	$effect(() => {
		loadEffisFires(fetch).then((fc) => (firesFc = fc));
	});
	/** the fires map shows 2018 onwards only */
	const FIRES_FROM = 2018;
	/** clicked Π.Ε. — the fires map zooms to it; same click zooms back */
	let firePe = $state<string | null>(null);
	const firesShown = $derived(
		(firesFc?.features ?? []).filter((f) => f.properties.yr >= FIRES_FROM)
	);
	/** how much of the country's burning since 2021 the projects answer */
	const effisSince2021 = $derived(
		(firesFc?.features ?? []).filter((f) => f.properties.yr >= 2021).length
	);
	const fireYears = $derived.by(() => {
		let lo = Infinity, hi = -Infinity;
		for (const f of firesShown) {
			lo = Math.min(lo, f.properties.yr);
			hi = Math.max(hi, f.properties.yr);
		}
		return Number.isFinite(lo) ? { lo, hi } : null;
	});

	// map dots (client-side: needs centroids + the digitised works zones)
	let centroids: Record<string, [number, number]> | null = $state.raw(null);
	let zonesFc: Awaited<ReturnType<typeof loadEviaZones>> | null = $state.raw(null);
	$effect(() => {
		loadCentroids(fetch).then((c) => (centroids = c));
		loadEviaZones(fetch)
			.then((z) => (zonesFc = z))
			.catch(() => (zonesFc = null));
	});
	// One dot per curated work SITE with coordinates; projects without any
	// fall back to one dot (works-zone centroid mean → Π.Ε. centroid).
	// Dots carry their TRUE position — the de-overlap spread is applied
	// inside the overlay snippet, only past the zoom threshold, so the
	// country view never displaces a dot from its real location.
	const mapDots = $derived.by(() => {
		if (!centroids) return [];
		const zc = new Map(
			(zonesFc?.features ?? []).map((f) => [f.properties.zone, f.properties.centroid])
		);
		type MapDot = (typeof live)[number] & {
			lat: number;
			lon: number;
			siteName?: string;
			prec: string;
			[key: string]: unknown;
		};
		const pts: MapDot[] = [];
		for (const p of live) {
			const ws = (Array.isArray(p.work_sites) ? p.work_sites : []).filter(
				(s) => s.lat != null && s.lon != null
			);
			if (ws.length) {
				for (const s of ws)
					pts.push({ ...p, lat: s.lat!, lon: s.lon!, siteName: s.name, prec: s.prec ?? 'site' });
				continue;
			}
			const wz = Array.isArray(p.works_zones) ? p.works_zones : [];
			const zs = wz.map((z) => zc.get(z)).filter(Boolean) as [number, number][];
			if (zs.length) {
				const lon = zs.reduce((s, c) => s + c[0], 0) / zs.length;
				const lat = zs.reduce((s, c) => s + c[1], 0) / zs.length;
				pts.push({ ...p, lat, lon, prec: 'zone' });
				continue;
			}
			if (p.pe && centroids[p.pe])
				pts.push({ ...p, lat: centroids[p.pe][0], lon: centroids[p.pe][1], prec: 'pe' });
		}
		return pts;
	});
	// approximate dots (municipality/Π.Ε. centre) render dashed + lighter.
	// Counts are computed from the payload (not mapDots) so the caveat is
	// correct in the server-rendered HTML too — mapDots needs the
	// client-side centroid fetch.
	const APPROX = new Set(['municipality', 'pe']);
	const dotStats = $derived.by(() => {
		let exact = 0;
		let approx = 0;
		for (const p of live) {
			const ws = (Array.isArray(p.work_sites) ? p.work_sites : []).filter(
				(s) => s.lat != null && s.lon != null
			);
			if (ws.length) {
				for (const s of ws) if (APPROX.has(s.prec ?? '')) approx++; else exact++;
				continue;
			}
			if (Array.isArray(p.works_zones) && p.works_zones.length) exact++;
			else if (p.pe) approx++;
		}
		return { exact, approx };
	});
	// spread base sized to keep ~8 screen px between co-located dots once
	// the k≥2 threshold arms (screen offset = SPREAD_BASE / degPerPx, k-free)
	const SPREAD_BASE = 0.09;
	const unplaced = $derived(
		live.filter(
			(p) =>
				!p.pe &&
				!(Array.isArray(p.work_sites) ? p.work_sites : []).some(
					(s) => s.lat != null && s.lon != null
				)
		)
	);

</script>

<svelte:head>
	<title>Ανάδοχοι αναδάσωσης — corporate fire-restoration sponsors</title>
	<meta
		property="og:description"
		content="{grInt(k.n_projects)} sponsor projects by {grInt(
			k.n_companies
		)} companies — only {nCompleted} have a completion act on record."
	/>
</svelte:head>

<span class="ruler" bind:this={rulerEl} aria-hidden="true"
	>The promise vs. the delivery: every project from appointment to deadline</span
>

{#snippet timelineKey()}
	<ul class="tkey">
		<li><i style:background={NODATE_COLOR}></i>no implementation dates stated</li>
		<li><i style:background={COLOR.completed}></i>completion act identified</li>
		<li><i style:background={COLOR.no_completion_recorded}></i>past deadline, no completion act identified</li>
		<li><i style:background={COLOR.active}></i>within its deadline, no completion act identified</li>
		<li><span class="mk ok">✔</span>completion date</li>
		<li><span class="mk bad">✖</span>revocation date</li>
		<li class="note">
			Each bar runs from the designation act to the deadline the act announced, the paler
			stretch being an extension; every bar is drawn at one height here — the money is on the
			full chart. Rows run from the earliest act downwards, {grInt(ganttFit.shown)} of {grInt(
				ganttFit.total
			)} projects shown.
		</li>
	</ul>
{/snippet}
{#snippet mapKey()}
	<ul class="tkey">
		<li><i class="dot" style:background={COLOR.completed}></i>completion act identified</li>
		<li><i class="dot" style:background={COLOR.active}></i>no completion act — still inside deadline</li>
		<li><i class="dot" style:background={NODATE_COLOR}></i>no implementation dates set</li>
		<li><i class="dot" style:background={COLOR.no_completion_recorded}></i>no completion act — deadline passed</li>
		<li><i class="dot" style:background={COLOR.revoked}></i>revoked</li>
		<li><i class="dot approx"></i>the act names only a municipality or region — the dot is its centre</li>
		<li><i class="scar"></i>areas burnt since 2018 (EFFIS satellite estimates)</li>
		<li class="note">
			One dot per project, at the site its act names. Click the title for the full map, with
			its zoom, its regions and the year of each fire.
		</li>
	</ul>
{/snippet}
{#snippet stSwitch()}
	<SegmentToggle
		param="st"
		fallback="bars"
		options={[
			{ value: 'bars', label: 'bars' },
			{ value: 'column', label: 'column' }
		]}
	/>
{/snippet}
<div class="anap">
<DatasetCard
	ds="anadohoi"
	params={PARAMS}
	layout="triple"
	richKpis={kpiRich}
	hint="atlas/src/content/datasets/anadohoi.md"
>
	{#snippet text()}
		<Text />
	{/snippet}
	{#snippet tileMain()}
		<Tile title="TIMELINE" href="#gantt" legend={timelineKey} fit>
			<div class="tilefill" bind:clientWidth={gW} bind:clientHeight={gH}>
				{#if gW && gH}
					<PromiseGantt
						projects={ganttProjects}
						today={todayIso}
						variant="card"
						width={gW}
						height={gH}
						onFit={(f) => {
							if (f.shown !== ganttFit.shown || f.total !== ganttFit.total) ganttFit = f;
						}}
					/>
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet tileA()}
		<Tile title="WHAT TYPES OF COMPANIES ARE INVOLVED" href="#sponsor-groups" fit tight>
			<div class="tilefill" bind:clientWidth={sW} bind:clientHeight={sH}>
				{#if o.sponsor_groups?.groups.length && sW && sH}
					<SponsorTypes groups={o.sponsor_groups.groups} height={sH} />
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet tileB()}
		<Tile title="MAP" href="#waffle" fit headOver>
			<div class="tilefill map" bind:clientWidth={tileW} bind:clientHeight={tileH}>
				{#if dev}
					<div class="framepick card">
						<label>
							<input type="checkbox" bind:checked={pickCard} />
							adjust card frame (dev)
						</label>
						{#if pickCard}
							<input
								class="viewout"
								readonly
								value={pickedCard?.bounds
									? `bounds: [[${pickedCard.bounds[0][0]}, ${pickedCard.bounds[0][1]}], [${pickedCard.bounds[1][0]}, ${pickedCard.bounds[1][1]}]] · k ${pickedCard.k}`
									: 'drag / wheel / +− to frame, then copy this'}
								onfocus={(e) => (e.currentTarget as HTMLInputElement).select()}
							/>
						{/if}
					</div>
				{/if}
				{#if tileW && tileH}
					<PaperMap
						width={tileW}
						height={tileH}
						fitBounds={CARD_BOUNDS}
						fitPad={MAP_PAD}
						interactive={pickCard}
						unclamped={pickCard}
						onViewChange={(v) => (pickedCard = v)}
						peGroup={(pe) => {
							const r = regionOfPe(pe);
							// zoomed: every unit answers (any click returns); at rest:
							// only the regions with projects
							if (selCard) return r ?? pe;
							return r && projectRegions.has(r) ? r : null;
						}}
						onRegionClick={(pe) => {
							if (selCard) {
								selCard = null;
								return;
							}
							const r = regionOfPe(pe);
							if (r && projectRegions.has(r)) selCard = r;
						}}
						fitPesLive={selCardPes}
						onEmptyClick={() => (selCard = null)}
						onEscape={() => (selCard = null)}
					>
						{#snippet overlay(ctx)}
							{#if firesFc}
								<FiresLayer
									{ctx}
									features={firesShown}
									flat
									tipOf={(f) => `${f.properties.yr} · ${grInt(f.properties.ha)} ha`}
								/>
							{/if}
							<DotLayer
								{ctx}
								points={mapDots}
								r={4.9}
								fillOf={(p) => (noDate(p as never) ? NODATE_COLOR : (STATUS_COLOR[p.status as string] ?? '#999'))}
								fillOpacityOf={(p) => (APPROX.has(p.prec as string) ? 0.45 : undefined)}
								dashOf={(p) => (APPROX.has(p.prec as string) ? `${2.4 / ctx.k} ${1.8 / ctx.k}` : undefined)}
								tipOf={(p) => `<strong>${p.company}</strong>`}
								hrefOf={(p) => `/anadohoi/project/${p.ada}`}
							/>
						{/snippet}
					</PaperMap>
					<ul class="mapkey left">
						<li>
							<i class="scar"></i>
							<span>areas burnt{#if fireYears}&nbsp;since {fireYears.lo}{/if} (EFFIS)</span>
						</li>
						<li><i class="dot" style:background={NODATE_COLOR}></i>no implementation dates stated</li>
						<li><i class="dot" style:background={COLOR.completed}></i>completion act identified</li>
						<li><i class="dot" style:background={COLOR.no_completion_recorded}></i>past deadline, no completion act identified</li>
						<li><i class="dot" style:background={COLOR.active}></i>within its deadline, no completion act identified</li>
					</ul>
				{/if}
			</div>
		</Tile>
	{/snippet}
	{#snippet more()}
	<div class="about">
		<div class="kicker">THE SCHEME</div>
		<p>
			Under ν.998/1979 άρθρο 42§3, companies volunteer to fund and execute the restoration of
			burnt public forest land — designated by ministerial act, spending their own money. This
			page follows all {grInt(k.n_projects)} projects from designation act to (sometimes)
			completion. Every value links back to the signed PDF —
			<a href="/methodology#anadohoi">methodology</a>.
		</p>
		<!-- the BASIS, said once for the whole page (the Anti-nero copy
		     doctrine, applied 2026-08-25): the frames below no longer
		     repeat it -->
		<p class="basis">
			All sums are the commitments written in the designation acts, not verified spending —
			net where the act states a VAT basis, never converted; a sponsor promising «τη συνολική
			χρηματοδότηση» with no figure adds projects but no euros; a superseded restatement is
			folded into its successor — <a href="/methodology#anadohoi">basis</a>.
		</p>
	</div>

{#if hoverCard}
	{@const hp = ganttProjects.find((p) => p.ada === hoverCard?.ada)}
	{#if hp}
		<ProjectCard
			x={hoverCard.x}
			y={hoverCard.y}
			anchor={hoverCard.anchor}
			card={cardFor(hp as unknown as GanttProject)}
		/>
	{/if}
{/if}
{#if catTip}
	<div
		class="cat-tip"
		style:left={`${catTip.x}px`}
		style:top={`${catTip.y}px`}
		style:max-width={`${catTip.maxW}px`}
	>
		{catTip.text}
	</div>
{/if}

<div class="scopetype">
<ChartFrame
	title="PROJECT SCOPE"
	insight={dWorks
		? `In ${pct((dWorks.count / k.n_projects) * 100, 0)} of the designation acts, the private actors appointed for the restoration or reforestation of an area are responsible only for the works.`
		: ''}
	caveat="Read from each act's operative «Ορίζουμε … με σκοπό …» sentence, verbatim excerpt kept per project; trail evidence beats the σκοπός wording."
	anchor="deliverables"
	methodology="anadohoi"
>
	<StackedShareBar
		height={34}
		segments={delivGroups.map((g) => ({
			label: g.label,
			value: g.count,
			color: g.color,
			// the palest segment's spill label prints in the full green
			labelColor: g.key === 'study' ? '#2d6a4f' : undefined,
			badge: g.key === 'study' ? ('outleft' as const) : ('above' as const)
		}))}
	/>
</ChartFrame>

<ChartFrame
	title="PROJECT TYPE"
	caveat="The kind as each act's own wording states it; «not stated» where the act names none."
	anchor="works-kind"
	methodology="anadohoi"
>
	<!-- the same drawing as the Anti-nero CONTRACT TYPE (user, 2026-08-22):
	     one bar per kind, counted in projects, biggest first -->
	<BarH
		rows={[...kindGroups].sort((a, b) => b.count - a.count).map((g) => ({ label: g.label, value: g.count }))}
		color="#2d6a4f"
		inside
		barHeight={35}
		fmt={grInt}
		valuesRight
	/>
</ChartFrame>
</div>

<ChartFrame
	title="CURRENT STATUS OF PROJECTS"
	insight={effisSince2021
		? `${pct(atticaPct, 0)} of these projects are located in Attica and ${pct(eviaPct, 0)} in Evia. The European Forest Fire Information System (EFFIS) mapped ${grInt(effisSince2021)} burnt areas in Greece since 2021; the sponsored projects cover ${grInt(scarsAnswered)} of them.`
		: ''}
	anchor="waffle"
	methodology="anadohoi"
	caveat={`${
		unplaced.length
			? `${unplaced.length} projects span multiple regions and are not placed on the map: ${unplaced.map((p) => p.company).join(', ')}. `
			: ''
	}A dashed dot stands where the act names only a municipality or region, drawn at its centre; completions are the acts identified on Διαύγεια — the absence of one is not proof a project was abandoned. Status as of ${dmy(k.status_as_of)}.`}
>
	<!-- ONE legend for the waffle AND the map — wording matches the
	     timeline legend, placed like it: a tinted strip under the title -->
	<ul class="stkey">
		<li><i style:background={COLOR.completed}></i>projects with identified completion act</li>
		<li>
			<i style:background={COLOR.active}></i>projects within deadline — no completion act
			identified
		</li>
		<li>
			<i style:background={NODATE_COLOR}></i>projects without specific dates for implementation
		</li>
		<li>
			<i style:background={COLOR.no_completion_recorded}></i>projects past deadline — no
			completion act identified
		</li>
		<li><i style:background={COLOR.revoked}></i>revoked</li>
	</ul>

	<div class="statusgrid">
		<div class="mcol">
			<div class="maplabel">
				MAP<Hint
					text="Click a region that holds projects to zoom to it (Esc resets); zoom in to separate co-located dots."
					heading
					width="330px"
				/>
				{#if selRegion}
					<button class="pill" onclick={() => (selRegion = null)}
						>✕ {selRegion} · all of Greece</button
					>
				{/if}
			</div>
			{#if dev}
				<div class="framepick">
					<label>
						<input type="checkbox" bind:checked={pickFrame} />
						adjust map frame (dev)
					</label>
					{#if pickFrame}
						<input
							class="viewout"
							readonly
							value={pickedView
								? `view: { center: [${pickedView.center[0]}, ${pickedView.center[1]}], k: ${pickedView.k} }`
								: 'drag / wheel-after-click to frame, then copy this'}
							onfocus={(e) => (e.currentTarget as HTMLInputElement).select()}
						/>
					{/if}
				</div>
			{/if}
			<Defer height={560}>
				<div class="mapscale">
					<div class="map-wrap" bind:this={mapEl}>
					<PaperMap
						interactive
						width={640}
						height={620}
						view={pickFrame ? null : MAP_VIEW}
						onViewChange={(v) => (pickedView = v)}
						peGroup={(pe) => {
							const r = regionOfPe(pe);
							return r && projectRegions.has(r) ? r : null;
						}}
						onRegionClick={(pe) => {
							const r = regionOfPe(pe);
							if (r && projectRegions.has(r)) selRegion = selRegion === r ? null : r;
						}}
						fitPesLive={selRegionPes}
						onEscape={() => (selRegion = null)}
						onEmptyClick={() => (selRegion = null)}
					>
						{#snippet overlay(ctx)}
							{@const dots = ctx.k >= 2 ? spreadOverlaps(mapDots, SPREAD_BASE / ctx.k) : mapDots}
							<!-- the fires that triggered the projects, exactly as on
							     the fires map below: EFFIS scars coloured by year -->
							{#if firesFc}
								<FiresLayer
									{ctx}
									features={firesShown}
									tipOf={(f) =>
										`<strong>${f.properties.yr}</strong> · ${grInt(f.properties.ha)} ha${f.properties.name ? ` · ${f.properties.name}` : ''}`}
								/>
							{/if}
							<!-- NOTE: the digitised works zones are NOT drawn here — this
							     map shows projects and fire outlines only; zonesFc still
							     feeds the zone-mapped projects' dot centroids, and the
							     zones themselves live on the project pages' ZoneMap -->
							<!-- hovering a multi-site project links all its dots with
							     dashed lines — «this work spans here AND here» -->
							{#if hoveredAda}
								{@const hot = dots.filter((d) => d.ada === hoveredAda)}
								{#each hot as a, i (i)}
									{#each hot.slice(i + 1) as b, j (j)}
										{@const pa = ctx.projection([
											(a as never as { lon2?: number }).lon2 ?? a.lon,
											(a as never as { lat2?: number }).lat2 ?? a.lat
										])}
										{@const pb = ctx.projection([
											(b as never as { lon2?: number }).lon2 ?? b.lon,
											(b as never as { lat2?: number }).lat2 ?? b.lat
										])}
										{#if pa && pb}
											<line
												x1={pa[0]}
												y1={pa[1]}
												x2={pb[0]}
												y2={pb[1]}
												stroke="var(--ink)"
												stroke-width={1.4 / ctx.k}
												stroke-dasharray="5 4"
												opacity="0.75"
												pointer-events="none"
											/>
										{/if}
									{/each}
								{/each}
							{/if}
							<DotLayer
								{ctx}
								points={dots}
								r={5}
								fillOf={(p) =>
									noDate(p as never)
										? NODATE_COLOR
										: (STATUS_COLOR[p.status as string] ?? '#999')}
								fillOpacityOf={(p) => (APPROX.has(p.prec as string) ? 0.45 : undefined)}
								dashOf={(p) =>
									APPROX.has(p.prec as string) ? `${2.4 / ctx.k} ${1.8 / ctx.k}` : undefined}
								tipOf={(p) =>
									`<strong>${p.company}</strong><br>` +
									(p.siteName
										? `${p.siteName}`
										: p.prec === 'zone'
											? 'ψηφιοποιημένη ζώνη έργων'
											: p.prec === 'municipality'
												? 'κέντρο δήμου (κατά προσέγγιση)'
												: 'regional-unit centre (approximate)')}
								hrefOf={(p) => `/anadohoi/project/${p.ada}`}
								onOver={(p) => showHover(p.ada as string, 'map')}
								onOut={() => showHover(null, 'map')}
								hotOf={(p) => p.ada === hoveredAda}
							/>
						{/snippet}
					</PaperMap>
					</div>
					{#if fireYears}
						<div class="yearscale" aria-hidden="true">
							<span>{fireYears.lo}</span>
							<i></i>
							<span>{fireYears.hi}</span>
						</div>
					{/if}
				</div>
			</Defer>
		</div>
		<div class="wcol" bind:this={waffleEl}>
			<div class="maplabel">METRICS</div>
			<StatusWaffle
				statuses={waffleStatuses}
				bare
				projects={ganttProjects as unknown as GanttProject[]}
				hotAda={hoveredAda}
				onCellHover={(ada) => showHover(ada, 'metrics')}
			/>
			<div class="maplabel peryear" id="peryear">DESIGNATIONS / COMPLETIONS PER YEAR</div>
			<AreaYears
				years={areaYears.years}
				width={440}
				height={230}
				series={[
					{
						label: 'designation acts',
						color: '#52b788',
						values: areaYears.designations,
						kind: 'line'
					},
					{ label: 'completion acts', color: 'var(--c-anadohoi)', values: areaYears.completions }
				]}
			/>
		</div>
	</div>
</ChartFrame>

<ChartFrame
	title="TIMELINE"
	hint="Click a company's name to open that project's page — every act of its trail, dated and linked."
	caveat={`Statuses as recorded on Διαύγεια — data last checked ${dmy(k.status_as_of)}.`}
	anchor="gantt"
	methodology="anadohoi"
>
	<PromiseGantt projects={ganttProjects} today={todayIso} legend="panel" />
</ChartFrame>

<Defer height={520}>
<div class="rankpair">
{#if o.sponsor_groups?.groups.length}
	{@const sg = o.sponsor_groups}
	{@const top = sg.groups[0]}
	{@const second = sg.groups[1]}
	{@const busiest = [...sg.groups].sort((a, b) => b.n - a.n)[0]}
	<ChartFrame
		title="WHO THE SPONSORS ARE"
		insight={sgLens === 'eur'
			? `${pct(sg.top2_share, 0)} of the money stated in the designation acts is provided by companies in ${top.label.toLowerCase()} and ${second.label.toLowerCase()}.`
			: `Counted in projects rather than euros the order changes; ${grInt(sg.groups.filter((g) => !g.eur).length)} of the ${grInt(sg.groups.length)} kinds of business commit no stated sum at all, so they hold projects and no bar under the money lens.`}
		caveat="Each sponsor is grouped by what it does, read from its own registered name or from the act appointing it — never by corporate ownership, which would be a legal claim needing verification company by company."
		anchor="sponsor-groups"
		methodology="anadohoi"
	>
		{#snippet controls()}
			<SegmentToggle
				param="sg"
				fallback="eur"
				options={[
					{ value: 'eur', label: '€ committed' },
					{ value: 'n', label: 'number of projects' }
				]}
			/>
		{/snippet}
		<SponsorGroups groups={sg.groups} lens={sgLens} />
	</ChartFrame>
{/if}

	<ChartFrame
		title="RANKING OF COMPANIES"
		subtitle="according to sums offered via the projects"
		insight={topSponsor
			? `${topSponsor.company} accounts for ${pct((topSponsor.budget / k.stated_eur) * 100, 0)} of the money stated in the designation acts.`
			: ''}
		anchor="sponsors"
		methodology="anadohoi"
	>
		<BarH rows={sponsorRows} color="var(--c-anadohoi)" inside barHeight={35} valuesRight />
		{#if topRaise}
			<p class="muted note-inline">
				The {topRaise.company} commitment grew {eurShort(topRaise.budget_stated ?? 0)} →
				{eurShort(topRaise.budget ?? 0)} by amendment — the largest single raise.
			</p>
		{/if}
	</ChartFrame>
</div>
</Defer>

<Defer height={300}>
	<ChartFrame
		title="FROM THE FIRE TO THE SPONSORED PROJECT"
		insight={fireFacts
			? `For the fire-affected areas where a private company has been appointed as a restoration or reforestation sponsor for part or the whole of the area, the median time between the fire itself and the appointment has been ${grInt(fireFacts.median)} days. In ${grInt(fireFacts.within60)} of these ${grInt(fireFacts.n)} areas the appointment came within the first two months after the fire.`
			: ''}
		caveat="Burn dates and areas are EFFIS satellite estimates, not official οριοθετήσεις — © European Union, Copernicus Emergency Management Service. {grInt(fireFacts?.noFire ?? 0)} projects answer no fire at all (plane-disease sanitation, salvage logging) and have no lane."
		anchor="pulse"
		methodology="anadohoi"
	>
		<FireResponse fires={fireLanes} today={k.status_as_of ?? '2026-08-24'} />
	</ChartFrame>
</Defer>

{#if execRows.length}
	<ChartFrame
		title="THE FOREST CO-OPS THE SPONSORS ENGAGED"
		subtitle="forest workers' co-operatives engaged in projects financed by private restoration–reforestation contractors"
		insight={`Based on the collected information, forest workers' co-operatives appear to have worked in ${grInt(execRows.length)} of the ${grInt(k.n_projects)} sponsored projects (${pct((execRows.length / k.n_projects) * 100, 0)}). Co-operatives may well have been engaged in the rest too, but no document naming them was found during this research.`}
		caveat="Only what the acts themselves record. The work end is placed as precisely as each project allows — the θέσεις its acts name, else the digitised Β. Εύβοια works zone, else the EFFIS scar of the fire it repairs; the seat is the co-operative's registered office. Burn scars: © European Union, Copernicus Emergency Management Service — EFFIS; satellite estimates, not official οριοθετήσεις. {crew?.unplaced.length ? `${grInt(crew.unplaced.length)} crews have no seat on record and are off the map (${crew.unplaced.map((u) => u.coop).join(', ')}).` : ''}"
		anchor="executors"
		methodology="anadohoi"
	>
		{#if crew}
			<CrewMap
				links={crew.links}
				fires={firesShown.filter((f) => f.properties.yr >= 2021)}
			/>
		{:else}
			<div class="skeleton" style="height: 460px"></div>
		{/if}
	</ChartFrame>
{/if}

<div class="firesband">
<ChartFrame
	title="PROJECTS AND FIRES THAT TRIGGERED THEM"
	titleColor="#000"
	caveat="Burnt-area perimeters: © European Union, Copernicus Emergency Management Service — EFFIS (satellite rapid-mapping estimates, not official οριοθετήσεις). Relief: produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The fire each project answers to is the one its act itself cites; «εκτός πυρκαγιάς» covers the same legal instrument used for tree disease and forest upgrades."
	anchor="fires"
	methodology="anadohoi"
>
	<div class="firesgrid">
		<div class="fmcol">
			<div class="reliefbar">
				<div class="relieftoggle" role="group" aria-label="Relief colouring">
					<button
						type="button"
						class:active={reliefStyle === 'grey'}
						onclick={() => (reliefStyle = 'grey')}>GREYSCALE</button
					>
					<button
						type="button"
						class:active={reliefStyle === 'hypso'}
						onclick={() => (reliefStyle = 'hypso')}>ELEVATION</button
					>
				</div>
				{#if reliefStyle === 'hypso'}
					<div class="hypsokey" aria-hidden="true">
						<span>0 μ</span>
						<i></i>
						<span>2.900 μ</span>
					</div>
				{/if}
			</div>
			<Defer height={760}>
				<div class="mapscale">
					<div class="map-wrap">
						<PaperMap
							interactive={false}
							width={640}
							height={620}
							view={MAP_VIEW}
							focusPe={firePe}
							onRegionClick={(pe) => (firePe = firePe === pe ? null : pe)}
							relief={reliefAssets}
						>
							{#snippet overlay(ctx)}
								{#if firesFc}
									<FiresLayer
										{ctx}
										features={firesShown}
										tipOf={(f) =>
											`<strong>${f.properties.yr}</strong> · ${grInt(f.properties.ha)} ha${f.properties.name ? ` · ${f.properties.name}` : ''}`}
									/>
								{/if}
							{/snippet}
						</PaperMap>
					</div>
					{#if fireYears}
						<div class="yearscale" aria-hidden="true">
							<span>{fireYears.lo}</span>
							<i></i>
							<span>{fireYears.hi}</span>
						</div>
					{/if}
				</div>
			</Defer>
		</div>
		<div class="fire-grid">
			{#each fireCards as f (f.fire)}
				<div class="fire-card">
					<div class="fire-name">{fireEn(f.fire)}</div>
					<div class="fire-bar">
						<div
							class="fire-fill"
							style:width={`${(100 * f.completed) / f.n}%`}
						></div>
					</div>
					<div class="fire-stats">
						{f.completed}/{f.n} completed
						{#if f.budget > 0}· {eurShort(f.budget)}{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</ChartFrame>
</div>
	{/snippet}
</DatasetCard>
</div>

<style>
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--c-anadohoi);
	}
	.about p {
		margin: 0;
	}
	/* every subsection title on this page follows THE SCHEME kicker:
	   display-black 14px, letterspaced, dataset green */
	.anap {
		--frame-accent: var(--c-anadohoi);
	}
	.anap :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-anadohoi);
	}
	/* invisible width reference for the prose right-edge alignment */
	.ruler {
		position: absolute;
		visibility: hidden;
		white-space: nowrap;
		font-family: var(--font-serif);
		font-weight: 600;
		font-size: var(--fs-24);
	}
	/* the fires section breaks out to the full usable page width */
	.firesband {
		margin-inline: min(0px, calc((100% - min(96vw, 1300px)) / 2));
	}
	/* fires map (with its vertical year scale) left, project cards right */
	.firesgrid {
		display: grid;
		grid-template-columns: auto minmax(300px, 1fr);
		gap: var(--sp-2) var(--sp-8, 3rem);
		align-items: start;
	}
	@media (max-width: 900px) {
		.firesgrid {
			grid-template-columns: 1fr;
		}
		.firesband {
			margin-inline: 0;
		}
	}
	.mapscale {
		display: flex;
		gap: var(--sp-3);
		align-items: flex-start;
	}
	/* the status map fills its column; only the year scale is extra */
	.statusgrid .mapscale .map-wrap {
		flex: 1 1 auto;
		min-width: 0;
	}
	.firesgrid .map-wrap {
		max-width: 700px;
		width: 700px;
	}
	.yearscale {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--sp-2);
		height: 320px;
		font-family: 'futura-100-greek', 'futura-100-greek-book', 'Sofia Sans', sans-serif;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.yearscale i {
		flex: 1;
		width: 10px;
		border-radius: 5px;
		background: linear-gradient(to bottom, #ecdadc, #6b2d35);
	}
	.fire-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
		gap: var(--sp-3);
	}
	.fire-card {
		padding-top: var(--sp-1);
	}
	.fire-name {
		font-size: var(--fs-13);
		font-weight: 600;
	}
	.fire-bar {
		height: 8px;
		background: color-mix(in srgb, var(--c-antinero) 22%, var(--paper));
		border-radius: 3px;
		margin: var(--sp-1) 0;
		overflow: hidden;
	}
	.fire-fill {
		height: 100%;
		background: var(--c-anadohoi);
	}
	.fire-stats {
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.note-inline {
		font-size: var(--fs-13);
		margin-top: var(--sp-2);
	}
	/* the page's one BASIS line under THE SCHEME (the Anti-nero dress) */
	.basis {
		margin-top: var(--sp-3);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		line-height: 1.5;
	}
	.basis a {
		color: var(--ink-soft);
	}
	/* RANKING OF COMPANIES | WHO THE SPONSORS ARE side by side, equal
	   halves (user, 2026-08-25) — the same pair layout PROJECT SCOPE and
	   PROJECT TYPE use; both carry 12 rows. One column again when narrow. */
	.rankpair {
		display: grid;
		/* minmax(0,…), not a plain 1fr: the group rows are nowrap, so their
		   min-content width would blow the track past its half */
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		gap: var(--sp-7, 2.5rem);
		align-items: start;
	}
	@media (max-width: 900px) {
		.rankpair {
			grid-template-columns: 1fr;
		}
	}
	/* PROJECT SCOPE | PROJECT TYPE side by side, equal halves (user,
	   2026-08-22); one column again on narrow screens */
	.scopetype {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-7, 2.5rem);
		align-items: start;
	}
	.scopetype :global(.ssbwrap) {
		flex: 1 1 auto;
	}
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
	.scopetype :global(.frame .finding) {
		margin-bottom: 2px;
	}
	@media (max-width: 900px) {
		.scopetype {
			grid-template-columns: 1fr;
		}
	}
	/* sponsor → executing co-op linkage list */
	/* one legend for waffle + map, in the timeline legend's dress: the
	   tinted strip right under the section title */
	.stkey {
		list-style: none;
		margin: 0 0 var(--sp-3);
		padding: var(--sp-2) var(--sp-3);
		background: #f2f2f2;
		border-radius: 6px;
		/* three aligned columns (2 rows) so entries line up, not rag */
		display: grid;
		grid-template-columns: repeat(3, auto);
		justify-content: start;
		gap: 6px var(--sp-7, 2rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	@media (max-width: 900px) {
		.stkey {
			grid-template-columns: 1fr;
		}
	}
	.stkey li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.maplabel .pill {
		font: inherit;
		font-size: var(--fs-12);
		letter-spacing: 0;
		text-transform: none;
		font-weight: 400;
		margin-left: var(--sp-3);
		padding: 1px 10px;
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.maplabel .pill:hover {
		border-color: var(--ink);
		color: var(--ink);
	}
	.stkey i {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		flex: none;
	}
	/* map left, METRICS waffle + prose right (per mockup) */
	.statusgrid {
		display: grid;
		grid-template-columns: 7fr minmax(300px, 5fr);
		gap: var(--sp-2) var(--sp-8, 3rem);
		align-items: start;
	}
	.statusgrid :global(.waffle) {
		max-width: 420px;
	}
	.cat-tip {
		position: fixed;
		transform: translate(0, -50%);
		background: var(--ink);
		color: #fff;
		font-size: var(--fs-12);
		line-height: 1.3;
		padding: 4px 10px;
		border-radius: 4px;
		pointer-events: none;
		z-index: 120;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
	}
	.framepick {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
		margin-bottom: var(--sp-2);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.framepick .viewout {
		flex: 1;
		font-family: var(--font-mono, monospace);
		font-size: var(--fs-12);
		border: 1px dashed var(--line);
		background: var(--paper);
		padding: 2px 8px;
		border-radius: 4px;
		color: var(--ink);
	}
	.maplabel.peryear {
		margin-top: var(--sp-10, 2.5rem);
	}
	.wcol :global(.ay figcaption) {
		background: #f2f2f2;
	}
	.maplabel {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		color: var(--c-anadohoi);
		margin-bottom: var(--sp-2);
	}
	@media (max-width: 900px) {
		.statusgrid {
			grid-template-columns: 1fr;
		}
	}
	.map-wrap {
		/* left-aligned; the card docks in the margin on its left */
		max-width: 600px;
		margin: 0;
	}
	/* the map: light-grey ground, white regions, grey hairline borders */
	.reliefbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--sp-3);
		margin-bottom: var(--sp-2);
	}
	.relieftoggle {
		display: inline-flex;
		border: 1px solid #8f8f8f;
		border-radius: 999px;
		overflow: hidden;
	}
	.relieftoggle button {
		font: inherit;
		font-size: var(--fs-12);
		letter-spacing: 0.06em;
		padding: 3px 14px;
		border: 0;
		background: none;
		color: #6f6f6f;
		cursor: pointer;
	}
	.relieftoggle button.active {
		background: #000;
		color: #fff;
	}
	.hypsokey {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.hypsokey i {
		width: 120px;
		height: 8px;
		border-radius: 2px;
		/* the baked HYPSO_STOPS display ramp (build_relief.py — must track it) */
		background: linear-gradient(
			90deg,
			#a9c2a0,
			#b6c6b0 7%,
			#cfcdaa 16%,
			#d6c49a 24%,
			#c99b72 34%,
			#b47a4e 45%,
			#9c5e38 59%,
			#8a4e2e 72%,
			#7a4227
		);
	}
	/* white-land styling for the DATA maps only — a relief map (.plate)
	   must keep its transparent fills and plate-gradient surround, or the
	   page CSS paints the polygons white OVER the relief (CSS beats the
	   fill attribute) */
	.map-wrap :global(.map:not(.plate)) {
		background: #f2f2f2;
		border: 1px solid var(--line); /* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		--map-accent: var(--c-anadohoi); /* the zoom buttons' circle hue */
		box-shadow: none;
	}
	.map-wrap :global(.map.plate) {
		border: 1px solid var(--line); /* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		--map-accent: var(--c-anadohoi); /* the zoom buttons' circle hue */
		box-shadow: none;
	}
	.map-wrap :global(.map:not(.plate) .region) {
		fill: #fff;
		stroke: #8f8f8f;
	}
	.map-wrap :global(.map.plate .region) {
		stroke: #8f8f8f;
	}
	.muted {
		color: var(--ink-soft);
	}
	/* the card's map tile fills its panel, in the page's own map dress
	   (`.tilefill`, not `.fill` — the direct-award bar owns that name) */
	.tilefill {
		position: absolute;
		inset: 0;
	}
	/* the card map is small: thinner administrative lines and a flat red
	   for every scar, so the project dots are what the eye finds first
	   (user, 2026-08-27) */
	.tilefill.map {
		--region-line-w: 0.35;
		--context-line-w: 0.35;
		--border-line-w: 0.6;
	}
	/* the user's edit: the key in the map's bottom corners — marks 7 px in,
	   11 px Futura on 14,4 px lines, the last line 5 px above the edge */
	.mapkey {
		position: absolute;
		bottom: 5px;
		list-style: none;
		margin: 0;
		padding: 0;
		z-index: 2;
		pointer-events: none;
		font-family: var(--font-ui);
		font-size: 11px;
		line-height: 14.4px;
		color: var(--ink);
	}
	.mapkey.left {
		left: 7px;
	}
	/* the dev frame picker rides over the map's top-right corner */
	.framepick.card {
		position: absolute;
		top: 6px;
		right: 42px;
		z-index: 3;
		background: rgba(255, 255, 255, 0.85);
		padding: 2px 6px;
		font-size: var(--fs-12);
	}
	.framepick.card .viewout {
		display: block;
		width: 300px;
		margin-top: 2px;
		font-size: 10px;
	}
	.mapkey li {
		display: flex;
		align-items: center;
		gap: 3px;
		white-space: nowrap;
	}
	.mapkey i {
		flex: none;
		width: 10px;
		height: 10px;
	}
	.mapkey i.dot {
		border-radius: 50%;
	}
	.mapkey i.scar {
		background: #6b2d35;
	}
	/* the key in the tile's leftover height, two columns, the note across */
	/* a tile's ⓘ key: the same wording as the frame legends, at tile size */
	.tkey {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
		font-family: var(--font-ui);
		font-size: var(--fs-12);
		line-height: 1.25;
		color: var(--ink-soft);
	}
	.tkey li {
		display: flex;
		align-items: flex-start;
		gap: 7px;
	}
	.tkey i {
		flex: none;
		width: 12px;
		height: 12px;
		margin-top: 1px;
	}
	.tkey i.dot {
		border-radius: 50%;
	}
	.tkey i.approx {
		background: rgba(64, 110, 85, 0.45);
		border: 1px dashed var(--ink-soft);
		box-sizing: border-box;
	}
	.tkey i.scar {
		background: #6b2d35;
		opacity: 0.85;
	}
	.tkey .mk {
		flex: none;
		width: 12px;
		font-weight: 900;
		line-height: 1;
	}
	.tkey .mk.ok {
		color: var(--c-anadohoi);
	}
	.tkey .mk.bad {
		color: #000;
	}
	.tkey .note {
		display: block;
		color: var(--ink-faint);
	}
	/* the card's map draws straight onto the panel — a plate of its own
	   inside the tile only made the map smaller (user, 2026-08-27) */
	.tilefill :global(.map) {
		background: transparent;
		border: none;
		--land-context: #fff;
		--map-accent: var(--card-accent);
		box-shadow: none;
	}
</style>
