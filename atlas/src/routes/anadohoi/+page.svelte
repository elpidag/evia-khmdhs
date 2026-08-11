<script lang="ts">
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import BarH from '$lib/charts/BarH.svelte';
	import PromiseGantt from '$lib/charts/PromiseGantt.svelte';
	import StatusWaffle from '$lib/charts/StatusWaffle.svelte';
	import DeadlineSlope from '$lib/charts/DeadlineSlope.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { loadCentroids, spreadOverlaps } from '$lib/maps/useGeo';
	import { eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.o);
	const k = $derived(o.kpis);
	const live = $derived(o.projects.filter((p) => p.status !== 'superseded'));
	const nCompleted = $derived(k.statuses['completed'] ?? 0);
	const nNoAct = $derived(k.statuses['no_completion_recorded'] ?? 0);

	const GANTT_ANNOTATIONS: Record<string, string> = {
		'63ΡΧ4653Π8-6Ε2': 'Coca-Cola withdrew by letter — revoked Jan 2026',
		'ΨΖΟΟ4653Π8-Ψ1Θ': 'extended to Dec 2028',
		'ΩΞΕΦ4653Π8-Μ0Π': 'ΔΕΗ: certified within weeks',
		'ΩΖ2Ο4653Π8-ΓΕΞ': 'Παπαστράτος planting — extended to 2027'
	};

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
	const nUnstated = $derived(k.n_projects - k.n_stated);

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

	// slope rows: every project whose deadline moved
	const slopeRows = $derived(
		live
			.filter((p) => p.deadline0 && p.deadline && p.deadline !== p.deadline0)
			.map((p) => ({
				ada: p.ada,
				company: p.company,
				d0: p.deadline0 as string,
				d1: p.deadline as string
			}))
	);

	// the CURRENT STATUS OF PROJECTS heading fits itself to the exact width
	// of the green hero cards (measured; re-fits on resize)
	let cardsEl = $state<HTMLElement | null>(null);
	let statusSpan = $state<HTMLElement | null>(null);
	$effect(() => {
		const span = statusSpan;
		const cards = cardsEl;
		if (!span || !cards) return;
		const fit = () => {
			span.style.fontSize = '100px';
			const w = span.getBoundingClientRect().width;
			if (w > 0) span.style.fontSize = `${(100 * cards.clientWidth) / w}px`;
		};
		fit();
		document.fonts?.ready.then(fit); // re-fit once the webfont metrics are in
		const ro = new ResizeObserver(fit);
		ro.observe(cards);
		return () => ro.disconnect();
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

	// map dots (client-side: needs centroids)
	let centroids: Record<string, [number, number]> | null = $state.raw(null);
	$effect(() => {
		loadCentroids(fetch).then((c) => (centroids = c));
	});
	const mapDots = $derived.by(() => {
		if (!centroids) return [];
		const pts = live
			.filter((p) => p.pe && centroids![p.pe])
			.map((p) => ({
				lat: centroids![p.pe as string][0],
				lon: centroids![p.pe as string][1],
				...p
			}));
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

<section class="hero">
	<div class="cards" bind:this={cardsEl}>
		<div class="card">
			<div class="num">{grInt(k.n_projects)}</div>
			<div class="lbl">announced projects<br />assignment acts</div>
		</div>
		<div class="card">
			<div class="num">{grInt(k.n_companies)}</div>
			<div class="lbl">private companies defined as restoration / reforestation contractors</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(k.stated_eur).toLowerCase()}</div>
			<div class="lbl">
				value of projects (only {grInt(k.n_stated)} of {grInt(k.n_projects)} acts state a
				figure)
			</div>
		</div>
	</div>
	<div class="about" style:margin-right={proseCut ? `${proseCut}px` : null}>
		<div class="kicker">THE SCHEME</div>
		<p>
			Under ν.998/1979 άρθρο 42§3, companies volunteer to fund and execute the restoration of
			burnt public forest land — appointed by ministerial act, spending their own money. This
			page follows all {grInt(k.n_projects)} projects from appointment to (sometimes)
			completion. Every value links back to the signed PDF —
			<a href="/methodology#anadohoi">methodology</a>.
		</p>
	</div>
</section>

<h2 class="status-title">
	<span bind:this={statusSpan}>CURRENT STATUS OF PROJECTS</span>
</h2>
<ChartFrame anchor="waffle" methodology="anadohoi">
	<StatusWaffle statuses={k.statuses}>
		{#snippet explanation()}
			<div style:margin-right={proseCut ? `${proseCut}px` : null}>
			<p>
				Each square is one sponsor project — {grInt(k.n_projects)} in all, with its colour
				showing where the project stands on Διαύγεια, the state's transparency register.
				Green means a completion act is on record: the official confirmation that the
				promised restoration was delivered and accepted. Only {grInt(nCompleted)} of
				{grInt(k.n_projects)} projects have one.
			</p>
			<p>
				Light grey projects are still inside their deadline. Darker grey ones are past it
				with nothing filed — which is not proof they were abandoned, but the act is the
				legal proof of delivery, so until one is posted the promise remains just a promise.
				Status as of {k.status_as_of} — <a href="/methodology#anadohoi">methodology</a>.
			</p>
			</div>
		{/snippet}
	</StatusWaffle>
</ChartFrame>

<ChartFrame
	title="TIMELINE"
	titleColor="#2e6a50"
	subtitle="bar = appointment → initial deadline · pale extension = amendments · ✓ completion act · ✕ revocation"
	caveat="Rows are grouped by outcome and sorted by appointment date; click a company to open its decision trail."
	anchor="gantt"
	methodology="anadohoi"
>
	<PromiseGantt
		projects={o.projects}
		today={k.status_as_of ?? '2026-08-02'}
		annotations={GANTT_ANNOTATIONS}
	/>
</ChartFrame>

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
		title={`${grInt(k.n_companies)} sponsors — banks and energy companies carry the money, ${nUnstated} acts state no figure at all`}
		subtitle="stated commitment per sponsor (after amendments), top {sponsorRows.length}"
		caveat="Sums are commitments written in the acts, not verified spending; sponsors often promise «συνολική χρηματοδότηση του κόστους που θα προκύψει» with no number."
		anchor="sponsors"
		methodology="anadohoi"
	>
		<BarH rows={sponsorRows} />
		<p class="muted note-inline">
			{#if topRaise}
				The {topRaise.company} commitment grew {eurShort(topRaise.budget_stated ?? 0)} →
				{eurShort(topRaise.budget ?? 0)} by amendment — the largest single raise.
			{/if}
			Works are often executed by forest co-ops from the ΔΑΣΕ dataset: NOVA's Rhodes zone
			was built by <a href="/dase">ΔΑΣΕ Αγίου Δημητρίου Πιερίας</a>, the ΤΙΤΑΝ/Κανελλοπούλου
			works by ΔΑΣΕ Γαρδικίου Τρικάλων.
		</p>
	</ChartFrame>
</Defer>

<Defer height={640}>
	<ChartFrame
		title="Where the sponsors work: Αττική dominates, the islands got one project each"
		subtitle="one dot per project at its Π.Ε. · colour = status"
		caveat={unplaced.length
			? `${unplaced.length} projects span multiple regions and are not placed: ${unplaced.map((p) => p.company).join(', ')}.`
			: ''}
		anchor="map"
		methodology="anadohoi"
	>
		<div class="map-wrap">
			<PaperMap interactive={false} width={640} height={620}>
				{#snippet overlay(ctx)}
					<DotLayer
						{ctx}
						points={mapDots}
						r={5}
						fillOf={(p) => STATUS_COLOR[p.status as string] ?? '#999'}
						tipOf={(p) =>
							`<strong>${p.company}</strong><br>${p.fire ?? ''} · ${p.status}`}
						hrefOf={(p) => `/anadohoi/project/${p.ada}`}
					/>
				{/snippet}
			</PaperMap>
		</div>
	</ChartFrame>
</Defer>

<Defer height={300}>
	<ChartFrame
		title="Each big fire triggers a wave of corporate sponsorship within weeks"
		subtitle="appointments per month since the scheme began (Aug 2021) · ▲ = first appointment after each fire"
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
					▲<title>{f.fire}: first appointment {f.first_start}</title>
				</text>
			{/each}
		</svg>
	</ChartFrame>
</Defer>

<Defer height={440}>
	<ChartFrame
		title={`${slopeRows.length} projects had their deadline moved — some by years`}
		subtitle="initial deadline → deadline after amendments"
		caveat="Red wires moved by more than roughly a year. Extensions are granted by τροποποίηση of the appointing act, usually citing weather or workload."
		anchor="slope"
		methodology="anadohoi"
	>
		<DeadlineSlope rows={slopeRows} />
	</ChartFrame>
</Defer>

<style>
	/* hero: three solid dataset-green KPI cards beside the scheme prose */
	.hero {
		display: grid;
		grid-template-columns: minmax(240px, 4fr) 8fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	.cards {
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
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
		font-size: clamp(34px, 4vw, 50px);
		line-height: 0.95;
	}
	.card .lbl {
		font-family: var(--font-display);
		font-weight: 400; /* Obviously Regular */
		font-size: var(--fs-14);
		line-height: 1.2;
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
	}
	.about p {
		margin: 0;
	}
	.status-title {
		/* ~one waffle square of air between the title and the graph */
		margin: 0 0 var(--sp-6);
		line-height: 1;
		color: #2e6a50;
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
	.status-title span {
		display: inline-block;
		font-family: var(--font-display);
		font-weight: 900;
		white-space: nowrap;
		font-size: var(--fs-24); /* pre-measure fallback; the effect fits it */
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
	.map-wrap {
		max-width: 660px;
		margin: 0 auto;
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
