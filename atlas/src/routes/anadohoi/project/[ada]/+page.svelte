<script lang="ts">
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import ActTimelineBar from '$lib/detail/ActTimelineBar.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ZoneMap from '$lib/maps/ZoneMap.svelte';
	import SiteMap, { type SitePin } from '$lib/maps/SiteMap.svelte';
	import { loadEffisFires, loadRivers, type FireProps, type RiverProps } from '$lib/maps/useGeo';
	import { COLOR, NODATE_COLOR } from '$lib/charts/ganttTheme';
	import type { Feature, LineString, MultiLineString, Polygon, MultiPolygon } from 'geojson';
	import { dmy, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const p = $derived(data.p);

	// template rows are English; Greek survives only inside quotations
	const WORKS: Record<string, string> = {
		anadasosi: 'reforestation',
		apokatastasi: 'restoration',
		both: 'restoration & reforestation'
	};
	const DELIVERABLES: Record<string, string> = {
		works: 'execution of works',
		study_and_works: 'study & works',
		study: 'study'
	};
	const STATUS: Record<string, string> = {
		completed: 'completed',
		active: 'active',
		no_completion_recorded: 'no completion recorded',
		revoked: 'revoked',
		superseded: 'superseded'
	};
	const RELATION: Record<string, string> = {
		initial: 'Designation act',
		superseded_initial: 'Initial designation act (superseded)',
		amendment: 'Amendment',
		revocation: 'Revocation',
		completion: 'Completion',
		study_approval: 'Study approval',
		committee: 'Acceptance committee',
		handover: 'Handover / installation',
		measurement: 'Measurement',
		logbook: 'Logbooks',
		schedule: 'Schedule',
		design: 'Construction drawings',
		other: 'Related act'
	};
	const EVIDENCE_LABEL: Record<string, string> = {
		company: 'Company',
		funder: 'Funder',
		address: 'Address',
		works_kind: 'Type of intervention',
		deliverables: 'Scope of appointment',
		location: 'Location',
		area: 'Area of intervention',
		budget: 'Budget',
		budget_vat: 'VAT basis',
		deadline: 'Deadline'
	};

	const budgetShown = $derived(p.budget_net_eur ?? p.budget_current);
	const worksZones = $derived(Array.isArray(p.works_zones) ? p.works_zones : null);
	interface Executor {
		name: string;
		dase_vat: string | null;
		ada: string;
		excerpt: string;
		note?: string;
	}
	const executors = $derived(Array.isArray(p.executors) ? (p.executors as Executor[]) : null);
	const executorExcerpts = $derived(
		executors ? [...new Set(executors.map((e) => e.excerpt))] : []
	);
	interface WorkSite {
		name: string;
		kind?: string;
		municipality?: string | null;
		pe?: string | null;
		stremmata?: number | null;
		source_ada: string;
		excerpt: string;
		lat?: number | null;
		lon?: number | null;
		geo_precision?: string | null;
		geo_source?: string | null;
		note?: string | null;
	}
	const workSites = $derived(Array.isArray(p.work_sites) ? (p.work_sites as WorkSite[]) : null);
	const sitePins = $derived.by(() => {
		const pins = (workSites ?? []).filter(
			(s): s is WorkSite & SitePin => s.lat != null && s.lon != null
		);
		// single-pin projects with a stated project area but no per-site
		// figure: the one dot carries the act's area
		if (pins.length === 1 && !pins[0].stremmata && p.area_stremmata) {
			return [{ ...pins[0], stremmata: p.area_stremmata }];
		}
		return pins;
	});
	const hasTrueSize = $derived(sitePins.some((s) => s.stremmata));
	// two-pin zone cards with an announced total area (no per-site split)
	// draw the schematic capsule containing both sites at that area
	const capsuleArea = $derived(
		sitePins.length === 2 && !hasTrueSize && p.area_stremmata ? p.area_stremmata : null
	);
	// which digitisation sheets the project's zones come from (pdf links)
	const zoneSheets = $derived.by(() => {
		const s = new Set<string>();
		for (const z of worksZones ?? []) s.add(z.startsWith('limni') ? '1' : '2');
		return [...s].sort();
	});
	const scarIds = $derived(
		new Set((Array.isArray(p.effis_scars) ? p.effis_scars : []).map((s) => s.id))
	);
	let scarFeats = $state.raw<Feature<Polygon | MultiPolygon, FireProps>[]>([]);
	$effect(() => {
		if (!scarIds.size) {
			scarFeats = [];
			return;
		}
		loadEffisFires(fetch)
			.then((fc) => (scarFeats = fc.features.filter((f) => scarIds.has(f.properties.id))))
			.catch(() => (scarFeats = []));
	});
	const scarHa = $derived(scarFeats.reduce((s, f) => s + (f.properties.ha ?? 0), 0));
	// context rivers: drawn only when this project is curated on the feature
	let riverFeats = $state.raw<Feature<LineString | MultiLineString, RiverProps>[]>([]);
	$effect(() => {
		loadRivers(fetch)
			.then((fc) => (riverFeats = fc.features.filter((f) =>
				f.properties.projects.includes(p.root_ada))))
			.catch(() => (riverFeats = []));
	});
	// one tone per fire, earliest darkest — shared by the map scars and
	// the timeline-bar dots so the two read as the same objects
	const FIRE_TONES = ['#6b2d35', '#9a4a48', '#c47a66', '#dba28c'];
	const scarTone = $derived.by(() => {
		const ordered = [...scarFeats].sort((a, b) =>
			(a.properties.d ?? String(a.properties.yr)).localeCompare(
				b.properties.d ?? String(b.properties.yr)
			)
		);
		return new Map(
			ordered.map((f, i) => [f.properties.id, FIRE_TONES[Math.min(i, FIRE_TONES.length - 1)]])
		);
	});
	// FIRE EVENT value in English: the linked fires' start dates (the
	// Greek event label survives only as a fallback when no scar dates
	// are known; «εκτός πυρκαγιάς» projects say so in English)
	const fireEventEn = $derived.by(() => {
		if (!p.fire_event) return '—';
		if (p.fire_event.includes('εκτός')) return 'no fire event';
		const dates = scarFeats
			.map((f) => f.properties.d)
			.filter((d): d is string => !!d)
			.sort();
		if (dates.length) return dates.map(dmy).join(', ');
		return p.fire_event;
	});

	// timeline fire markers: the linked scars' start dates from the layer
	const fireDots = $derived(
		scarFeats
			.map((f) => ({
				id: f.properties.id,
				d: f.properties.d ?? '',
				ha: f.properties.ha,
				name: f.properties.name,
				color: scarTone.get(f.properties.id)
			}))
			.filter((f) => f.d !== '')
	);
	// timeline-dot hover ⇄ map selection
	let hoverFireId = $state<number | null>(null);

	// deadline extensions: ONLY amendment acts whose curated `detail`
	// carries the new deadline date — budget/terms amendments get no dot
	// (they stay in the trail table); verbatim excerpts live in the trail
	const ISO = /^\d{4}-\d{2}-\d{2}$/;
	const extMarks = $derived(
		p.decisions
			.filter((d) => d.relation === 'amendment' && d.issue_date && d.detail && ISO.test(d.detail))
			.sort((a, b) => (a.issue_date ?? '').localeCompare(b.issue_date ?? ''))
			.map((d, i) => ({ n: i + 1, d: d.issue_date as string, deadline: d.detail, ada: d.ada }))
	);
	// extension-dot hover → trail-row highlight
	let hoverExtAda = $state<string | null>(null);
	// trail-row hover → the timeline extension dot grows AND the row
	// itself goes black (only for amendment acts that carry a dot)
	let hoverTrailAda = $state<string | null>(null);
	const extAdas = $derived(new Set(extMarks.map((e) => e.ada)));

	// the project's identity hue = its timeline-bar colour (ganttTheme);
	// site pins and the trail's self-row highlight wear the same colour
	const barColor = $derived(
		p.status === 'active' && !p.deadline_current
			? NODATE_COLOR
			: (COLOR[p.status] ?? NODATE_COLOR)
	);
	// self-row lettering is always white on the bar colour (user decision)
	const barInk = '#fff';

	// template facts derived from the decision trail
	const designationDate = $derived(
		p.decisions.find((d) => d.relation === 'initial')?.issue_date ??
			p.decisions[0]?.issue_date ??
			null
	);
	const hasAmendments = $derived(p.decisions.some((d) => d.relation === 'amendment'));

	const trailRows = $derived<TrailRow[]>(
		p.decisions.map((d) => ({
			d: d.issue_date,
			type: RELATION[d.relation] ?? d.relation,
			code: d.ada,
			title: d.subject ?? null,
			pdf: `/pdf/diavgeia/${d.ada}`,
			self: d.ada === p.root_ada,
			chip:
				d.relation === 'superseded_initial'
					? 'superseded'
					: d.relation === 'revocation'
						? 'revocation'
						: undefined
		}))
	);

	const quotes = $derived<Quote[]>([
		...Object.entries(p.evidence).map(([k, v]) => ({
			label: EVIDENCE_LABEL[k] ?? k,
			text: v as string,
			code: p.root_ada,
			href: `/pdf/diavgeia/${p.root_ada}`
		})),
		...p.decisions
			.filter((d) => d.excerpt)
			.map((d) => ({
				label: RELATION[d.relation] ?? d.relation,
				text: d.excerpt as string,
				code: d.ada,
				href: `/pdf/diavgeia/${d.ada}`
			})),
		...executorExcerpts.map((ex) => ({
			label: 'Works execution',
			text: ex,
			code: executors?.find((e) => e.excerpt === ex)?.ada ?? null,
			href: executors?.find((e) => e.excerpt === ex)
				? `/pdf/diavgeia/${executors.find((e) => e.excerpt === ex)!.ada}`
				: null
		})),
		...(workSites ?? [])
			.filter((s) => s.excerpt)
			.map((s) => ({
				label: `Work site — ${s.name}`,
				text: s.excerpt,
				code: s.source_ada,
				href: `/pdf/diavgeia/${s.source_ada}`
			}))
	]);

	// zone cards explain the digitised areas; the dot wording appears
	// whenever dots are on the map (incl. dots drawn over a zone map)
	const CAVEAT = $derived(
		'LOCATION quotes the designation act, which may name more areas than the follow-up ' +
			'documents cover. ' +
			(worksZones?.length && !sitePins.length
				? ''
				: 'Each dot is a work site NAMED in a document of the trail, placed by geocoding ' +
					'that name: at the named θέση where the document gives one, at the ' +
					"municipality's centre where it names only a municipality (flagged «κατά " +
					'προσέγγιση» on hover). ' +
					(hasTrueSize
						? 'Where a document states the intervention area, the dot is drawn at that ' +
							'area’s true size at map scale (a minimum size applies when zoomed out). '
						: '')) +
			(riverFeats.length
				? 'River courses named by the act are drawn from OpenStreetMap — © OpenStreetMap ' +
					'contributors, approximate. '
				: '') +
			'Fire perimeters are satellite estimates, not official οριοθετήσεις — © European ' +
			'Union, Copernicus Emergency Management Service — EFFIS.'
	);

	// the dashed "today" rule of the act's timeline bar (as on /anadohoi)
	const todayIso = new Date().toLocaleDateString('en-CA');

	// map height tracks the facts+caveat column so the two bottoms align;
	// the SiteMap/ZoneMap svgs render ~1 css px per viewBox unit at the
	// column's full 460px width. Fire-framed maps (linked EFFIS scars)
	// IGNORE this and derive their aspect from the scar frame instead,
	// so every card of the same fire renders one identical window
	// (DATA_DECISIONS 2026-08-16)
	let leftH = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));
</script>

<svelte:head>
	<title>{p.company} — {p.fire_event ?? 'Ανάδοχος'} — sponsor project</title>
	<meta property="og:title" content="{p.company} · {p.location_text ?? p.root_ada}" />
	<meta
		property="og:description"
		content="Sponsor project {p.root_ada}: {p.budget_current
			? eurShort(p.budget_current)
			: 'no stated budget'} · status: {STATUS[p.status] ?? p.status}"
	/>
</svelte:head>

<div class="pp">
	<p class="crumb"><a href="/anadohoi">← Sponsored works</a></p>

	{#snippet zoneSource()}
		The areas of the projects are sourced by documents provided by the Evia Forest Directorate
		({#each zoneSheets as k, i (k)}{#if i}{', '}{/if}<a
				href={`/pdf/zonesource/${k}`}
				target="_blank"
				rel="noopener">{zoneSheets.length === 1 ? 'pdf' : `pdf${i + 1}`}</a
			>{/each}) after a formal request regarding works that followed the fires of August 2021.
		{#if capsuleArea}
			The shaded band is schematic: the smallest area containing the named sites, drawn at the
			announced intervention size — the documents state no boundaries.
		{/if}
	{/snippet}
	<FactsHeader
		caveat={CAVEAT}
		caveatExtra={worksZones?.length ? zoneSource : undefined}
		bind:leftHeight={leftH}
	>
		{#snippet facts()}
			<dt class="id">Designation act (ΑΔΑ)</dt>
			<dd class="id">{p.root_ada}</dd>
			<dt>Date <small class="muted">of the designation decision</small></dt>
			<dd>{dmy(designationDate) || '—'}</dd>
			<dt>Company</dt>
			<dd>{p.company}</dd>
			<dt>Type</dt>
			<dd>{WORKS[p.works_kind ?? ''] ?? '—'}</dd>
			<dt>Scope</dt>
			<dd>{DELIVERABLES[p.deliverables ?? ''] ?? '—'}</dd>
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Budget</dt>
			<dd>
				{#if budgetShown === null}
					not stated in the designation act
				{:else}
					{eurShort(budgetShown)}
					{#if p.budget_net_eur !== null || p.budget_vat_basis === 'net'}
						<small class="muted">excl. VAT</small>
					{:else if p.budget_vat_basis === 'gross'}
						<small class="muted">incl. VAT</small>
					{/if}
					{#if p.budget_current !== null && p.budget_current !== p.budget_eur}
						<small class="muted"
							>— initially {p.budget_eur === null ? 'unstated' : eurShort(p.budget_eur)}, raised
							by amendment</small
						>
					{/if}
				{/if}
			</dd>
			<dt>Status</dt>
			<dd>{STATUS[p.status] ?? p.status}</dd>
			<dt>Area of intervention</dt>
			<dd>
				{#if p.area_stremmata === null}
					—
				{:else}
					{grInt(Math.round(p.area_stremmata / 10))} ha
				{/if}
			</dd>
			<dt>Fire event connected</dt>
			<dd>
				{fireEventEn}{#if scarHa}, burnt area : {grInt(Math.round(scarHa))} ha{/if}
			</dd>
			<dt>Amendments to initial act</dt>
			<dd>{hasAmendments ? 'yes' : 'no'}</dd>
			<dt>Current deadline</dt>
			<!-- date only — the extension history lives on the timeline bar -->
			<dd>{p.deadline_current ? dmy(p.deadline_current) : '—'}</dd>
			{#if executors?.length}
				<dt>Works executed by</dt>
				<dd>
					{#each executors as e (e.name + e.ada)}
						<div class="execrow">
							{#if e.dase_vat}
								<a href={`/dase/coop/${e.dase_vat}`}>{e.name}</a>
							{:else}
								{e.name}
							{/if}
							{#if e.note}<small class="muted">— {e.note}</small>{/if}
						</div>
					{/each}
				</dd>
			{/if}
			<dt>Location <small class="muted">as named in the designation act</small></dt>
			<dd>{p.location_text ?? '—'}</dd>
		{/snippet}
		{#snippet map()}
			<!-- ONE map per card: zone projects draw their pinned sites ON
			     the zone map instead of a second SiteMap -->
			{#if worksZones?.length}
				<ZoneMap
					zones={worksZones}
					scars={scarFeats}
					height={mapH}
					sites={sitePins}
					pinColor={barColor}
					areaStremmata={capsuleArea}
				/>
			{:else if sitePins.length || scarFeats.length}
				<SiteMap
					sites={sitePins}
					scars={scarFeats}
					height={mapH}
					fireColorOf={(f) => scarTone.get(f.properties.id) ?? FIRE_TONES[0]}
					selectedId={hoverFireId}
					rivers={riverFeats}
					pinColor={barColor}
				/>
			{/if}
		{/snippet}
	</FactsHeader>

	<DocTrail
		rows={trailRows}
		highlight={hoverExtAda ??
			(hoverTrailAda !== null && extAdas.has(hoverTrailAda) ? hoverTrailAda : null)}
		selfColor={barColor}
		selfInk={barInk}
		onRowHover={(code) => (hoverTrailAda = code)}
	>
		{#snippet top()}
			<ActTimelineBar
				start={designationDate}
				start0={p.restates?.start_date ?? null}
				deadline0={p.deadline_initial ?? p.deadline_current}
				deadline={p.deadline_current}
				completed={p.completed_date}
				revoked={p.revoked_date}
				status={p.status}
				today={todayIso}
				fires={fireDots}
				onFireHover={(id) => (hoverFireId = id)}
				extensions={extMarks}
				onExtHover={(ada) => (hoverExtAda = ada)}
				highlightAda={hoverTrailAda}
			/>
		{/snippet}
	</DocTrail>
	{#if p.restates}
		<p class="story">
			Restatement: the superseded act committed
			{p.restates.budget_eur === null ? 'an unstated budget' : eurShort(p.restates.budget_eur)}
			as «{p.restates.company}»; the re-issued designation under «{p.company}»
			{#if p.budget_eur !== null}at <b>{eurShort(p.budget_eur)}</b>{/if} is the version that
			counts in the aggregates.
		</p>
	{/if}

	<QuoteList {quotes} />
</div>

<style>
	/* Futura 100 Greek throughout — this page's content mixes Greek and
	   Latin in every line, and only the Book family carries both scripts */
	.pp {
		font-family: var(--font-ui);
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.execrow {
		margin-bottom: 2px;
	}
	.execrow a {
		color: var(--c-dase);
	}
	.story {
		margin-top: var(--sp-2);
		font-size: var(--fs-13);
		color: var(--ink-soft);
		max-width: 80ch;
	}
	.story b {
		color: var(--c-anadohoi);
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
