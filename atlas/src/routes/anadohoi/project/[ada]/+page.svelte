<script lang="ts">
	import { ruLabel } from '$lib/transforms/regions';
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import ActTimelineBar from '$lib/detail/ActTimelineBar.svelte';
	import DocTrail, { type TrailRow } from '$lib/detail/DocTrail.svelte';
	import QuoteList, { type Quote } from '$lib/detail/QuoteList.svelte';
	import ZoneMap from '$lib/maps/ZoneMap.svelte';
	import SiteMap, { type SitePin } from '$lib/maps/SiteMap.svelte';
	import { loadEffisFires, type FireProps } from '$lib/maps/useGeo';
	import type { Feature, Polygon, MultiPolygon } from 'geojson';
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
	const sitePins = $derived(
		(workSites ?? []).filter((s): s is WorkSite & SitePin => s.lat != null && s.lon != null)
	);
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

	const CAVEAT =
		'The location of the project is sourced from the designation act and geolocated in ' +
		'approximation, depending on the information provided. The area of the fire is sourced ' +
		'from the dataset provided by © European Union, Copernicus Emergency Management ' +
		'Service — EFFIS.';

	// the dashed "today" rule of the act's timeline bar (as on /anadohoi)
	const todayIso = new Date().toLocaleDateString('en-CA');
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

	<FactsHeader caveat={CAVEAT}>
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
						<small class="muted">excl. ΦΠΑ</small>
					{:else if p.budget_vat_basis === 'gross'}
						<small class="muted">incl. ΦΠΑ</small>
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
			<dd>
				{#if p.status === 'active'}
					active
				{:else}
					<span
						class="chip"
						class:ok={p.status === 'completed'}
						class:bad={p.status === 'revoked' || p.status === 'no_completion_recorded'}
						class:warn={p.status === 'superseded'}
					>
						{STATUS[p.status] ?? p.status}
					</span>
				{/if}
			</dd>
			<dt>Area of intervention</dt>
			<dd>
				{#if p.area_stremmata === null}
					—
				{:else}
					{grInt(p.area_stremmata)} στρέμματα <small class="muted"
						>({grInt(Math.round(p.area_stremmata / 10))} ha)</small
					>
				{/if}
			</dd>
			<dt>Fire event connected</dt>
			<dd>
				{p.fire_event ?? '—'}{#if scarHa}<small class="muted">
						· burnt area {grInt(Math.round(scarHa))} ha</small
					>{/if}
			</dd>
			<dt>Amendments to initial act</dt>
			<dd>{hasAmendments ? 'yes' : 'no'}</dd>
			<dt>Current deadline</dt>
			<dd>
				{#if p.deadline_current}
					{dmy(p.deadline_current)}
					{#if p.deadline_initial && p.deadline_initial !== p.deadline_current}
						<small class="muted">— initially {dmy(p.deadline_initial)}, extended by amendment</small
						>
					{/if}
				{:else if p.deadline_text}
					{p.deadline_text}
				{:else}
					—
				{/if}
			</dd>
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
			<dt>Location</dt>
			<dd>{p.location_text ?? '—'}</dd>
			{#if p.pe}
				<dt>Region</dt>
				<dd>{ruLabel(p.pe)}{p.municipality ? ` · Δήμος ${p.municipality}` : ''}</dd>
			{/if}
		{/snippet}
		{#snippet map()}
			{#if sitePins.length || (scarFeats.length && !worksZones?.length)}
				<SiteMap sites={sitePins} scars={scarFeats} height={460} />
			{/if}
			{#if worksZones?.length}
				<ZoneMap zones={worksZones} scars={scarFeats} height={460} />
			{/if}
		{/snippet}
	</FactsHeader>

	<DocTrail rows={trailRows}>
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
