<script lang="ts">
	import { dev } from '$app/environment';
	import LocationCurator from '$lib/dev/LocationCurator.svelte';
	import ZoneMap from '$lib/maps/ZoneMap.svelte';
	import { dmy, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const p = $derived(data.p);

	const WORKS: Record<string, string> = {
		anadasosi: 'Αναδάσωση',
		apokatastasi: 'Αποκατάσταση',
		both: 'Αποκατάσταση & Αναδάσωση'
	};
	const DELIVERABLES: Record<string, string> = {
		works: 'εκτέλεση του έργου',
		study_and_works: 'εκπόνηση μελέτης και υλοποίηση έργου',
		study: 'εκπόνηση μελέτης'
	};
	const STATUS: Record<string, string> = {
		completed: 'completed',
		active: 'active',
		no_completion_recorded: 'no completion recorded',
		revoked: 'revoked',
		superseded: 'superseded'
	};
	const RELATION: Record<string, string> = {
		initial: 'Πράξη ορισμού',
		superseded_initial: 'Αρχική πράξη ορισμού (αντικαταστάθηκε)',
		amendment: 'Τροποποίηση',
		revocation: 'Ανάκληση',
		completion: 'Ολοκλήρωση',
		study_approval: 'Έγκριση μελέτης',
		committee: 'Επιτροπή παραλαβής',
		handover: 'Παραλαβή / εγκατάσταση',
		measurement: 'Επιμέτρηση',
		logbook: 'Ημερολόγια',
		schedule: 'Χρονοδιάγραμμα',
		design: 'Κατασκευαστικά σχέδια',
		other: 'Σχετική πράξη'
	};
	const EVIDENCE_LABEL: Record<string, string> = {
		company: 'Ανάδοχος',
		funder: 'Χρηματοδότης',
		address: 'Διεύθυνση',
		works_kind: 'Είδος έργου',
		deliverables: 'Αντικείμενο ορισμού',
		location: 'Τοποθεσία',
		area: 'Έκταση',
		budget: 'Προϋπολογισμός',
		budget_vat: 'Βάση ΦΠΑ',
		deadline: 'Προθεσμία'
	};
	const budgetShown = $derived(p.budget_net_eur ?? p.budget_current);
	// tolerate a pre-restart API that ships works_zones unparsed
	const worksZones = $derived(Array.isArray(p.works_zones) ? p.works_zones : null);
	// pre-filled Google Maps search for the dev-only location curator
	const locQuery = $derived(
		[p.location_text, p.municipality ? `Δήμος ${p.municipality}` : '', p.pe]
			.filter(Boolean)
			.join(' ')
	);
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

<div class="headgrid">
<dl class="facts head">
	<dt>Company</dt>
	<dd class="co">{p.company}</dd>
	<dt>Budget</dt>
	<dd>
		{#if budgetShown === null}
			none stated
		{:else}
			{eurShort(budgetShown)}
			{#if p.budget_net_eur !== null || p.budget_vat_basis === 'net'}
				<small class="muted">excl. ΦΠΑ</small>
			{:else if p.budget_vat_basis === 'gross'}
				<small class="muted">incl. ΦΠΑ</small>
			{/if}
			{#if p.budget_current !== null && p.budget_current !== p.budget_eur}
				<small class="muted"
					>— initially {p.budget_eur === null ? 'unstated' : eurShort(p.budget_eur)}, raised by
					amendment</small
				>
			{/if}
		{/if}
	</dd>
	<dt>Area of intervention</dt>
	<dd>{p.area_stremmata === null ? '—' : `${grInt(p.area_stremmata)} στρέμματα`}</dd>
	<dt>Type of intervention</dt>
	<dd>{WORKS[p.works_kind ?? ''] ?? '—'}</dd>
	<dt>Scope of appointment</dt>
	<dd>{DELIVERABLES[p.deliverables ?? ''] ?? '—'}</dd>
	<dt>Location</dt>
	<dd>
		{p.location_text ?? '—'}
		{#if p.pe}<br /><small class="muted"
				>{p.pe}{p.municipality ? ` · Δήμος ${p.municipality}` : ''}</small
			>{/if}
	</dd>
	<dt>Connected to fire event</dt>
	<dd>{p.fire_event ?? '—'}</dd>
	<dt>Status</dt>
	<dd>
		<span
			class="chip"
			class:ok={p.status === 'completed'}
			class:bad={p.status === 'revoked' || p.status === 'no_completion_recorded'}
			class:warn={p.status === 'superseded'}
		>
			{STATUS[p.status] ?? p.status}
		</span>
	</dd>
	<dt>Current deadline</dt>
	<dd>
		{#if p.deadline_current}
			{dmy(p.deadline_current)}
			{#if p.deadline_initial && p.deadline_initial !== p.deadline_current}
				<small class="muted">— initially {dmy(p.deadline_initial)}, extended by amendment</small>
			{/if}
		{:else if p.deadline_text}
			{p.deadline_text}
		{:else}
			—
		{/if}
	</dd>
</dl>
{#if dev}
	<LocationCurator ada={p.root_ada} query={locQuery} />
{/if}
</div>

{#if worksZones?.length}
	<ZoneMap zones={worksZones} />
{/if}

{#if p.notes}
	<p class="note">ℹ️ {p.notes}</p>
{/if}

<section>
	<h2 class="ttl">Decision trail ({grInt(p.decisions.length)})</h2>
	<p class="muted">
		Every act linked to this project, oldest first. PDFs are fetched from Diavgeia once and
		then served from the local cache.
	</p>
	<table class="listing">
		<thead>
			<tr>
				<th>Date</th>
				<th>Act</th>
				<th>Subject</th>
				<th>PDF</th>
			</tr>
		</thead>
		<tbody>
			{#each p.decisions as d (d.ada)}
				<tr class:dead={d.relation === 'superseded_initial'}>
					<td class="tabular muted">{dmy(d.issue_date) || '—'}</td>
					<td>
						<span
							class="chip"
							class:bad={d.relation === 'revocation'}
							class:warn={d.relation === 'superseded_initial'}
							class:ok={d.relation === 'completion'}>{RELATION[d.relation] ?? d.relation}</span
						>
						<br /><small class="tabular muted">{d.ada}</small>
					</td>
					<td>
						<small>{d.subject ?? '—'}</small>
						{#if d.relation === 'superseded_initial' && p.restates}
							<span class="story">
								{#if p.restates.budget_eur !== null}Committed
									<b>{eurShort(p.restates.budget_eur)}</b> as «{p.restates.company}»
									—{:else}As «{p.restates.company}» —{/if}
								replaced by the re-issued act below; not counted in aggregates.
							</span>
						{:else if d.relation === 'initial' && p.restates}
							<span class="story">
								Re-issued appointment{#if p.budget_eur !== null}&nbsp;at
									<b>{eurShort(p.budget_eur)}</b>{/if} under «{p.company}»{#if p.restates.budget_eur !== null}
									(previously {eurShort(p.restates.budget_eur)}){/if} — this version counts.
							</span>
						{/if}
						{#if d.excerpt}
							<blockquote class="excerpt">«{d.excerpt}»</blockquote>
						{/if}
					</td>
					<td class="nowrap">
						<a href={`/pdf/diavgeia/${d.ada}`} target="_blank" rel="noopener">📄 PDF</a>
						<br /><a
							class="ext"
							href={`https://diavgeia.gov.gr/decision/view/${d.ada}`}
							target="_blank"
							rel="noopener"><small>Diavgeia ↗</small></a
						>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

{#if Object.keys(p.evidence).length}
	<section>
		<h2>Evidence</h2>
		<p class="muted">
			Verbatim excerpts from the signed PDF backing each curated value
			(<a href="/methodology#anadohoi">methodology</a>).
		</p>
		<dl class="facts">
			{#each Object.entries(p.evidence) as [k, v] (k)}
				<dt>{EVIDENCE_LABEL[k] ?? k}</dt>
				<dd><blockquote class="excerpt">«{v}»</blockquote></dd>
			{/each}
		</dl>
	</section>
{/if}
</div>

<style>
	/* Futura 100 Greek throughout — this page's content mixes Greek and
	   Latin in every line, and only the Book family carries both scripts */
	.pp,
	.pp h2 {
		font-family: var(--font-ui);
	}
	/* fact list left, dev-only curation box right (column collapses when
	   the box is absent, i.e. in production builds) */
	.headgrid {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: var(--sp-2) var(--sp-8, 3rem);
		align-items: start;
		margin: var(--sp-4) 0 var(--sp-2);
	}
	@media (max-width: 900px) {
		.headgrid {
			grid-template-columns: 1fr;
		}
	}
	.head {
		margin: 0;
	}
	/* labels: bold 16px — TRUE bold, because the labels are English and the
	   futura-100-greek family (Latin subset) ships a real 700; answers:
	   14px plain Book. .facts.head beats the generic .facts dt rule. */
	.facts.head dt {
		align-self: baseline;
		font-size: var(--fs-16);
		font-weight: 700;
		font-family: 'futura-100-greek', 'futura-100-greek-book', 'Sofia Sans', system-ui, sans-serif;
		color: #000;
	}
	.facts.head dd {
		margin: 0;
		font-size: var(--fs-14);
	}
	/* section title matched to the list labels: true-bold 16px, black */
	.pp .ttl {
		font-size: var(--fs-16);
		font-weight: 700;
		font-family: 'futura-100-greek', 'futura-100-greek-book', 'Sofia Sans', system-ui, sans-serif;
		color: #000;
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.note {
		border-left: 3px solid var(--c-anadohoi);
		padding: var(--sp-1) var(--sp-3);
		background: var(--paper-soft, rgba(0, 0, 0, 0.03));
		font-size: var(--fs-14);
	}
	/* supersede story told inline in the decision trail */
	.dead td {
		background: color-mix(in srgb, var(--ink) 4%, var(--paper));
	}
	.story {
		display: block;
		margin-top: 2px;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.story b {
		color: var(--c-anadohoi);
	}
	section {
		margin-top: var(--sp-6);
	}
	.facts {
		display: grid;
		grid-template-columns: minmax(120px, max-content) 1fr;
		gap: var(--sp-1) var(--sp-4);
	}
	.facts dt {
		color: var(--ink-soft);
		font-size: var(--fs-13);
	}
	.excerpt {
		margin: var(--sp-1) 0 0;
		padding-left: var(--sp-2);
		border-left: 2px solid var(--line-strong);
		color: var(--ink-soft);
		font-size: var(--fs-13);
		font-style: italic;
	}
	.chip.ok {
		background: var(--c-anadohoi);
		color: #fff;
		border-color: var(--c-anadohoi);
	}
	.nowrap {
		white-space: nowrap;
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
