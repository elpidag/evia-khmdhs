<script lang="ts">
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import BarH from '$lib/charts/BarH.svelte';
	import PromiseGantt from '$lib/charts/PromiseGantt.svelte';
	import StatusWaffle from '$lib/charts/StatusWaffle.svelte';
	import Waffle from '$lib/charts/Waffle.svelte';
	import AreaYears from '$lib/charts/AreaYears.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import ZonesLayer from '$lib/maps/ZonesLayer.svelte';
	import { loadCentroids, loadEviaZones, spreadOverlaps } from '$lib/maps/useGeo';
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

	// finding-title inputs — computed from the payload, never hardcoded
	const bestFire = $derived.by(() => {
		let best = null as null | { fire: string; share: number; n: number };
		for (const f of fireCards) {
			if (f.fire === 'εκτός πυρκαγιάς' || f.n < 2) continue;
			const share = f.completed / f.n;
			if (!best || share > best.share) best = { fire: f.fire, share, n: f.n };
		}
		return best;
	});
	const worstFire = $derived.by(() => {
		let worst = null as null | { fire: string; n: number };
		for (const f of fireCards) {
			if (f.fire === 'εκτός πυρκαγιάς' || f.completed > 0) continue;
			if (!worst || f.n > worst.n) worst = { fire: f.fire, n: f.n };
		}
		return worst;
	});
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
	const DELIV_META: [string, string, string][] = [
		['works', 'εκτέλεση έργου — works only', '#2d6a4f'],
		['study_and_works', 'εκπόνηση μελέτης και υλοποίηση έργου — study & works', '#52b788'],
		['study', 'εκπόνηση μελέτης — study only', '#b7e4c7']
	];
	const KIND_META: [string, string, string][] = [
		['apokatastasi', 'αποκατάσταση — restoration', '#2d6a4f'],
		['both', 'αποκατάσταση & αναδάσωση — both', '#52b788'],
		['anadasosi', 'αναδάσωση — reforestation', '#b7e4c7'],
		['', 'not stated in the act', '#CFCFCF']
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
				where: p.pe ?? p.fire ?? '',
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

	// map dots (client-side: needs centroids + the digitised works zones)
	let centroids: Record<string, [number, number]> | null = $state.raw(null);
	let zonesFc: Awaited<ReturnType<typeof loadEviaZones>> | null = $state.raw(null);
	$effect(() => {
		loadCentroids(fetch).then((c) => (centroids = c));
		loadEviaZones(fetch)
			.then((z) => (zonesFc = z))
			.catch(() => (zonesFc = null));
	});
	const mapDots = $derived.by(() => {
		if (!centroids) return [];
		const zc = new Map(
			(zonesFc?.features ?? []).map((f) => [f.properties.zone, f.properties.centroid])
		);
		const pts = live
			.filter((p) => p.pe && centroids![p.pe])
			.map((p) => {
				// zone-mapped projects sit at their digitised works area, not
				// the Π.Ε. centroid
				const wz = Array.isArray(p.works_zones) ? p.works_zones : [];
				const zs = wz.map((z) => zc.get(z)).filter(Boolean) as [number, number][];
				if (zs.length) {
					const lon = zs.reduce((s, c) => s + c[0], 0) / zs.length;
					const lat = zs.reduce((s, c) => s + c[1], 0) / zs.length;
					return { lat, lon, ...p };
				}
				return {
					lat: centroids![p.pe as string][0],
					lon: centroids![p.pe as string][1],
					...p
				};
			});
		return spreadOverlaps(pts, 0.09);
	});
	const unplaced = $derived(live.filter((p) => !p.pe));

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
	}Designations count each project once, at its first act; completions are the acts identified on Διαύγεια — absence of one is not proof a project was abandoned. Status as of ${dmy(k.status_as_of)}.`}
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
				<div class="map-wrap" bind:this={mapEl}>
					<PaperMap
						interactive={pickFrame}
						width={640}
						height={620}
						view={pickFrame ? null : MAP_VIEW}
						onViewChange={(v) => (pickedView = v)}
					>
						{#snippet overlay(ctx)}
							{#if zonesFc}
								<ZonesLayer
									{ctx}
									features={zonesFc.features}
									tipOf={(f) =>
										`<strong>${f.properties.name}</strong><br>${f.properties.basin}<br>` +
										`${grInt(f.properties.extracted_stremmata)} στρ. (ψηφιοποιημένη ζώνη έργων)`}
								/>
							{/if}
							<DotLayer
								{ctx}
								points={mapDots}
								r={5}
								fillOf={(p) =>
									noDate(p as never)
										? NODATE_COLOR
										: (STATUS_COLOR[p.status as string] ?? '#999')}
								hrefOf={(p) => `/anadohoi/project/${p.ada}`}
								onOver={(p) => showHover(p.ada as string, 'map')}
								onOut={() => showHover(null, 'map')}
								hotOf={(p) => p.ada === hoveredAda}
							/>
						{/snippet}
					</PaperMap>
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

<div class="waffle-pair">
	<ChartFrame
		title="SCOPE OF APPOINTMENT"
		subtitle="what each act appoints the sponsor for — from its operative σκοπός"
		caveat={`Curated from each root designation act's operative sentence, with the verbatim excerpt on the project page. Counts the ${grInt(ganttProjects.length)} live projects — a superseded restatement's act is reviewed but not shown here.`}
		anchor="deliverables"
		methodology="anadohoi"
	>
		<Waffle groups={delivGroups} stacked ariaLabel="Projects by scope of appointment" />
	</ChartFrame>

	<ChartFrame
		title="TYPE OF INTERVENTION"
		subtitle="αναδάσωση, αποκατάσταση, or both — as each act states it"
		caveat="The act's own wording decides; one project's act states neither."
		anchor="works-kind"
		methodology="anadohoi"
	>
		<Waffle groups={kindGroups} stacked ariaLabel="Projects by type of intervention" />
	</ChartFrame>
</div>

<ChartFrame
	title="{bestFire?.fire ?? '—'} was certified — {worstFire?.fire ?? '—'} never was"
	subtitle="projects grouped by the fire that triggered them · fill = share with a completion act"
	caveat="The fire is the one each act itself cites; «εκτός πυρκαγιάς» covers the same legal instrument used for tree disease and forest upgrades."
	anchor="fires"
	methodology="anadohoi"
>
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
</ChartFrame>

<Defer height={520}>
	<ChartFrame
		title="RANKING OF COMPANIES"
		subtitle="according to sums offered via the projects"
		caveat="Sums are commitments written in the acts, not verified spending; sponsors often promise «συνολική χρηματοδότηση του κόστους που θα προκύψει» with no number."
		anchor="sponsors"
		methodology="anadohoi"
	>
		<BarH rows={sponsorRows} color="#52b788" inside barHeight={22} />
		{#if topRaise}
			<p class="muted note-inline">
				The {topRaise.company} commitment grew {eurShort(topRaise.budget_stated ?? 0)} →
				{eurShort(topRaise.budget ?? 0)} by amendment — the largest single raise.
			</p>
		{/if}
	</ChartFrame>
</Defer>

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
		/* three equal rows — every card the height of the tallest */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 300px;
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
		font-size: clamp(28px, 3.2vw, 40px);
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
	.fire-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
		gap: var(--sp-3);
	}
	.fire-card {
		border-top: 2px solid var(--line-strong);
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
	/* the two category waffles run side by side */
	.waffle-pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0 var(--sp-8, 3rem);
		align-items: start;
	}
	@media (max-width: 900px) {
		.waffle-pair {
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
	.map-wrap :global(.map) {
		background: #f2f2f2;
		border: none;
		box-shadow: none;
	}
	.map-wrap :global(.region) {
		fill: #fff;
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
