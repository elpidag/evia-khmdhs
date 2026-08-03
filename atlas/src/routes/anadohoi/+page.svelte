<script lang="ts">
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
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

	const STATUS_COLOR: Record<string, string> = {
		completed: 'var(--c-anadohoi)',
		active: '#9a8c74',
		no_completion_recorded: 'var(--c-antinero)',
		revoked: '#7a1f1f'
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

<hgroup>
	<h1>The corporate sponsors of burnt forests</h1>
	<p class="muted">
		Under ν.998/1979 άρθρο 42§3, companies volunteer to fund and execute the restoration of
		burnt public forest land — appointed by ministerial act, spending their own money. This
		page follows all {grInt(k.n_projects)} projects from appointment to (sometimes)
		completion. Every value links back to the signed PDF —
		<a href="/methodology#anadohoi">methodology</a>.
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(k.stated_eur)}
		label="total committed where stated"
		compare="net of ΦΠΑ where the act states it"
		basis={`only ${k.n_stated} of ${k.n_projects} acts state a figure; ${
			k.vat_counts?.net ?? 0
		} explicitly net, ${k.vat_counts?.unstated ?? 0} with no VAT basis written`}
		color="var(--c-anadohoi)"
	/>
	<StatPair
		value={eurShort(k.median_eur)}
		label="median stated commitment"
		basis="over the acts that state a figure"
	/>
	<StatPair
		value={String(k.n_projects)}
		label="sponsor projects"
		compare={`${grInt(k.area_stremmata)} στρ. covered by the acts`}
		color="var(--c-anadohoi)"
	/>
	<StatPair
		value={grInt(k.n_companies)}
		label="companies & foundations"
		compare={`${nCompleted} completion acts on record · ${nNoAct} past deadline with nothing filed`}
	/>
</KpiRow>

<ChartFrame
	title={`Only ${nCompleted} of ${k.n_projects} sponsor projects have a completion act on record`}
	subtitle="one square per project · status as recorded on Diavgeia"
	caveat={`Absence of a posted completion act is not proof a project was abandoned — but the act IS the legal proof of delivery. Status as of ${k.status_as_of}.`}
	anchor="waffle"
	methodology="anadohoi"
>
	<StatusWaffle statuses={k.statuses} />
</ChartFrame>

<ChartFrame
	title="The promise vs. the delivery: every project from appointment to deadline"
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
	title="Β. Εύβοια was certified within months — the 2021 Attica cluster never was"
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
		subtitle="stated commitment per sponsor (after amendments), top 12"
		caveat="Sums are commitments written in the acts, not verified spending; sponsors often promise «συνολική χρηματοδότηση του κόστους που θα προκύψει» with no number."
		anchor="sponsors"
		methodology="anadohoi"
	>
		<BarH rows={sponsorRows} />
		<p class="muted note-inline">
			The ΣΤΑΝΤΑ Α.Ε. δωρεά grew €3M → €4M by amendment — the largest single commitment.
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
