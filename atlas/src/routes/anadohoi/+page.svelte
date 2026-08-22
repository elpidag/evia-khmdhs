<script lang="ts">
	import { ruLabel } from '$lib/transforms/regions';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import BarH from '$lib/charts/BarH.svelte';
	import PromiseGantt from '$lib/charts/PromiseGantt.svelte';
	import StatusWaffle from '$lib/charts/StatusWaffle.svelte';
	import StackedShareBar from '$lib/charts/StackedShareBar.svelte';
	import AreaYears from '$lib/charts/AreaYears.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import FiresLayer from '$lib/maps/FiresLayer.svelte';
	import { loadCentroids, loadEffisFires, loadEviaZones, spreadOverlaps } from '$lib/maps/useGeo';
	import { dmy, eurShort, grInt } from '$lib/transforms/format';
	import { COLOR, NODATE_COLOR, noDate, type GanttProject } from '$lib/charts/ganttTheme';
	import ProjectCard from '$lib/charts/ProjectCard.svelte';
	import { cardFor } from '$lib/charts/projectCard';
	import { dev } from '$app/environment';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.o);
	const k = $derived(o.kpis);

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
	// greyscale ramp per the approved mock; light → dark, small first
	const DELIV_META: [string, string, string][] = [
		['study', 'study only', '#b5b5b5'],
		['study_and_works', 'study & works', '#6c6c6c'],
		['works', 'works only', '#3d3d3d']
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
				where: (p.pe ? ruLabel(p.pe) : null) ?? p.fire ?? '',
				executors: p.executors as Executor[]
			}))
			.sort((a, b) => a.company.localeCompare(b.company, 'el'))
	);
	const nExecCoops = $derived(
		new Set(execRows.flatMap((r) => r.executors.map((e) => e.dase_vat ?? e.name))).size
	);
	const kindGroups = $derived.by(() => {
		const s = countBy('works_kind');
		return KIND_META.map(([key, label, color]) => ({ key, label, color, count: s[key] ?? 0 }));
	});

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

	// timeline strip: months 2021-08 … status_as_of, with fire markers
	const strip = $derived.by(() => {
		const byM = new Map(o.monthly.map((x) => [x.m, x.n]));
		const months: { m: string; n: number }[] = [];
		const end = (k.status_as_of ?? '2026-08').slice(0, 7);
		let cur = '2021-08';
		while (cur <= end) {
			months.push({ m: cur, n: byM.get(cur) ?? 0 });
			const [y, mo] = cur.split('-').map(Number);
			cur = mo === 12 ? `${y + 1}-01` : `${y}-${String(mo + 1).padStart(2, '0')}`;
		}
		const maxN = Math.max(...months.map((x) => x.n), 1);
		const fires = o.fires
			.filter((f) => f.fire !== 'εκτός πυρκαγιάς' && f.first_start)
			.map((f) => ({
				...f,
				idx: months.findIndex((x) => x.m === (f.first_start as string).slice(0, 7))
			}))
			.filter((f) => f.idx >= 0);
		return { months, maxN, fires };
	});
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

<div class="anap">
<section class="hero">
	<div class="cards">
		<div class="card">
			<div class="num">{grInt(k.n_projects)}</div>
			<div class="lbl">announced projects</div>
		</div>
		<div class="card">
			<div class="num">{grInt(k.n_companies)}</div>
			<div class="lbl">private companies as restoration / reforestation contractors</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(k.stated_eur).toLowerCase()}</div>
			<div class="lbl">
				value of projects<br />(only {grInt(k.n_stated)} of {grInt(k.n_projects)} acts state
				a figure)
			</div>
		</div>
	</div>
	<div class="about" style:margin-right={proseCut ? `${proseCut}px` : null}>
		<div class="kicker">THE SCHEME</div>
		<p>
			Under ν.998/1979 άρθρο 42§3, companies volunteer to fund and execute the restoration of
			burnt public forest land — designated by ministerial act, spending their own money. This
			page follows all {grInt(k.n_projects)} projects from designation act to (sometimes)
			completion. Every value links back to the signed PDF —
			<a href="/methodology#anadohoi">methodology</a>.
		</p>
	</div>
</section>

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

<h2 class="status-title">CURRENT STATUS OF PROJECTS</h2>
<ChartFrame
	anchor="waffle"
	methodology="anadohoi"
	caveat={`${
		unplaced.length
			? `${unplaced.length} projects span multiple regions and are not placed on the map: ${unplaced.map((p) => p.company).join(', ')}. `
			: ''
	}${grInt(dotStats.exact)} dots sit at the work location the acts name (a project may have several — hovering links them); ${grInt(dotStats.approx)} dashed dots mark projects whose acts give only a municipality or region, drawn at its centre. Zoom in (click, then wheel or +) to separate co-located dots — at country view every dot keeps its true position. Designations count each project once, at its first act; completions are the acts identified on Διαύγεια — absence of one is not proof a project was abandoned. Status as of ${dmy(k.status_as_of)}.`}
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
			<div class="maplabel">MAP</div>
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
	caveat={`Rows are ordered by the date of each project's first designation act — the control at the top left switches to grouping by category. Click a company to open its decision trail. Statuses as recorded on Διαύγεια — data last checked ${dmy(k.status_as_of)}.`}
	anchor="gantt"
	methodology="anadohoi"
>
	<PromiseGantt projects={ganttProjects} today={todayIso} legend="panel" />
</ChartFrame>

<Defer height={520}>
	<ChartFrame
		title="RANKING OF COMPANIES"
		subtitle="according to sums offered via the projects"
		caveat="Sums are commitments written in the acts, not verified spending; sponsors often promise «συνολική χρηματοδότηση του κόστους που θα προκύψει» with no number."
		anchor="sponsors"
		methodology="anadohoi"
	>
		<div class="rankw">
			<BarH rows={sponsorRows} color="#52b788" inside barHeight={30} />
		</div>
		{#if topRaise}
			<p class="muted note-inline">
				The {topRaise.company} commitment grew {eurShort(topRaise.budget_stated ?? 0)} →
				{eurShort(topRaise.budget ?? 0)} by amendment — the largest single raise.
			</p>
		{/if}
	</ChartFrame>
</Defer>

<div class="scopetype">
<ChartFrame title="PROJECT SCOPE" titleColor="#000" anchor="deliverables" methodology="anadohoi">
	<StackedShareBar
		segments={delivGroups.map((g) => ({
			label: g.label,
			value: g.count,
			color: g.color,
			badge: g.key === 'study' ? ('outleft' as const) : ('above' as const)
		}))}
	/>
</ChartFrame>

<ChartFrame title="PROJECT TYPE" titleColor="#000" anchor="works-kind" methodology="anadohoi">
	<StackedShareBar
		segments={kindGroups.map((g) => ({
			label: g.label,
			value: g.count,
			color: g.color,
			badge:
				g.key === 'anadasosi'
					? ('outleft' as const)
					: g.key === ''
						? ('outright' as const)
						: ('above' as const)
		}))}
	/>
</ChartFrame>
</div>

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
					<div class="fire-name">{f.fire}</div>
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

{#if execRows.length}
	<ChartFrame
		title={`The sponsors sign, forest co-ops dig: ${grInt(execRows.length)} of ${grInt(k.n_projects)} act trails name their executing crew`}
		subtitle="{grInt(nExecCoops)} distinct co-ops (ΔΑ.Σ.Ε., ν.4423/2016) named as φορείς υλοποίησης or works contractors"
		caveat="Only what the acts themselves record — most trails never name who held the chainsaw. Green co-ops link to their public-contracts profile in the ΔΑΣΕ dataset; the rest never won a public contract in its harvest window, or the act's wording doesn't pin one registry entry."
		anchor="executors"
		methodology="anadohoi"
	>
		<div class="exectable">
			{#each execRows as r (r.ada)}
				<div class="execitem">
					<div class="execproj">
						<a href={`/anadohoi/project/${r.ada}`}>{r.company}</a>
						{#if r.where}<small class="muted">{r.where}</small>{/if}
					</div>
					<div class="execcoops">
						{#each r.executors as e (e.name)}
							{#if e.dase_vat}
								<a class="coop linked" href={`/dase/coop/${e.dase_vat}`} title={e.excerpt}
									>{e.name}</a
								>
							{:else}
								<span class="coop" title={e.note ?? e.excerpt}>{e.name}</span>
							{/if}
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</ChartFrame>
{/if}

<Defer height={300}>
	<ChartFrame
		title="Each big fire triggers a wave of corporate sponsorship within weeks"
		subtitle="designation acts per month since the scheme began (Aug 2021) · ▲ = first designation after each fire"
		anchor="pulse"
		methodology="anadohoi"
	>
		<svg viewBox="0 0 920 170" class="strip" role="img" aria-label="Appointments per month">
			{#each strip.months as mo, i (mo.m)}
				{@const h = (110 * mo.n) / strip.maxN}
				<rect
					x={20 + i * ((880 - 20) / strip.months.length)}
					y={130 - h}
					width={(880 - 20) / strip.months.length - 2}
					height={h}
					fill="var(--c-anadohoi)"
					opacity="0.8"
				>
					<title>{mo.m}: {mo.n}</title>
				</rect>
				{#if mo.m.endsWith('-01')}
					<text x={20 + i * ((880 - 20) / strip.months.length)} y="145" class="axis"
						>{mo.m.slice(0, 4)}</text
					>
				{/if}
			{/each}
			{#each strip.fires as f (f.fire)}
				<text
					x={20 + f.idx * ((880 - 20) / strip.months.length)}
					y="160"
					class="fire-mark"
				>
					▲<title>{f.fire}: first designation act {dmy(f.first_start)}</title>
				</text>
			{/each}
		</svg>
	</ChartFrame>
</Defer>

</div>

<style>
	/* hero: three solid dataset-green KPI cards beside the scheme prose */
	.hero {
		display: grid;
		grid-template-columns: minmax(240px, 4fr) 8fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	.cards {
		/* three equal rows — every card the height of the tallest;
		   268px matches the Anti-nero page's equal hero columns */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	.card {
		background: var(--c-anadohoi);
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
		/* same cap as the Anti-nero cards so the KPI cards match across pages */
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
		color: var(--c-anadohoi);
	}
	.about p {
		margin: 0;
	}
	/* every subsection title on this page follows THE SCHEME kicker:
	   display-black 14px, letterspaced, dataset green */
	.status-title,
	.anap :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-anadohoi);
	}
	.status-title {
		margin: 0 0 var(--sp-3);
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
	@media (max-width: 900px) {
		.hero {
			grid-template-columns: 1fr;
		}
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
	/* the companies graph runs at 3/4 of the content width */
	.rankw {
		max-width: 75%;
	}
	@media (max-width: 900px) {
		.rankw {
			max-width: none;
		}
	}
	/* the two share bars sit close together */
	.scopetype :global(.frame:first-child) {
		margin-bottom: var(--sp-8, 2rem);
	}
	/* the bars match the ranking's 3/4 width — text room on the right */
	.scopetype :global(.ssbwrap) {
		flex: 0 0 75%;
		/* titles hug their bars; hover badges may overflow upward */
		padding-top: 2px;
	}
	.scopetype :global(.frame .finding) {
		margin-bottom: 2px;
	}
	@media (max-width: 900px) {
		.scopetype :global(.ssbwrap) {
			flex: 1 1 auto;
		}
	}
	/* sponsor → executing co-op linkage list */
	.exectable {
		display: grid;
		gap: var(--sp-2);
	}
	.execitem {
		display: grid;
		grid-template-columns: minmax(220px, 3fr) 9fr;
		gap: var(--sp-1) var(--sp-6);
		align-items: baseline;
		border-top: 1px solid var(--line);
		padding-top: var(--sp-2);
	}
	.execproj a {
		text-decoration: none;
		font-weight: 600;
	}
	.execproj a:hover {
		text-decoration: underline;
	}
	.execproj small {
		display: block;
	}
	.execcoops {
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-1) var(--sp-2);
	}
	.coop {
		font-size: var(--fs-13);
		border: 1px solid var(--line-strong);
		border-radius: 999px;
		padding: 1px 10px;
		white-space: nowrap;
		color: var(--ink-soft);
	}
	.coop.linked {
		color: var(--c-dase);
		border-color: var(--c-dase);
		text-decoration: none;
	}
	.coop.linked:hover {
		background: color-mix(in srgb, var(--c-dase) 10%, transparent);
	}
	@media (max-width: 900px) {
		.execitem {
			grid-template-columns: 1fr;
		}
	}
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
	.strip {
		width: 100%;
		height: auto;
	}
	.axis {
		font-size: 10px;
		fill: var(--ink-faint);
	}
	.fire-mark {
		font-size: 11px;
		fill: var(--c-antinero);
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
