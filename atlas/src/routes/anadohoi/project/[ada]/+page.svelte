<script lang="ts">
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const p = $derived(data.p);

	const WORKS: Record<string, string> = {
		anadasosi: 'Αναδάσωση',
		apokatastasi: 'Αποκατάσταση',
		both: 'Αποκατάσταση & Αναδάσωση'
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
		location: 'Τοποθεσία',
		area: 'Έκταση',
		budget: 'Προϋπολογισμός',
		deadline: 'Προθεσμία'
	};
	const badStatus = $derived(
		p.status === 'revoked' || p.status === 'no_completion_recorded'
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

<p class="crumb"><a href="/anadohoi">← Ανάδοχοι αναδάσωσης / αποκατάστασης</a></p>

<hgroup>
	<h1>{p.company}</h1>
	<p class="muted tabular">
		ΑΔΑ {p.root_ada} · appointed {p.start_date ?? '—'}
		{#if p.fire_event}· <span class="chip">{p.fire_event}</span>{/if}
		<span class="chip" class:bad={badStatus} class:warn={p.status === 'superseded'}>
			{STATUS[p.status] ?? p.status}
		</span>
	</p>
</hgroup>

{#if p.notes}
	<p class="note">ℹ️ {p.notes}</p>
{/if}
{#if p.superseded_by}
	<p class="note">
		Restated by <a href={`/anadohoi/project/${p.superseded_by}`}>{p.superseded_by}</a> — the
		successor counts in aggregates.
	</p>
{/if}

<KpiRow>
	<StatPair
		value={p.budget_current === null ? '—' : eurShort(p.budget_current)}
		label="stated budget"
		basis={p.budget_current === null
			? 'the act states no figure — the sponsor pays whatever it costs'
			: p.budget_current !== p.budget_eur
				? `initially ${p.budget_eur === null ? 'unstated' : eurShort(p.budget_eur)}, raised by amendment`
				: 'as stated in the act'}
		color="var(--c-anadohoi)"
	/>
	<StatPair
		value={p.area_stremmata === null ? '—' : `${grInt(p.area_stremmata)} στρ.`}
		label="area"
		compare={WORKS[p.works_kind ?? ''] ?? '—'}
	/>
	<StatPair
		value={p.deadline_current ?? '—'}
		label="current deadline"
		compare={p.deadline_initial && p.deadline_initial !== p.deadline_current
			? `initially ${p.deadline_initial}`
			: ''}
	/>
	<StatPair
		value={p.completed_date ?? p.revoked_date ?? '—'}
		label={p.completed_date
			? 'completion certified'
			: p.revoked_date
				? 'revoked on'
				: 'no completion act found'}
		basis={p.completed_date || p.revoked_date
			? ''
			: 'absence of a posted act is not proof of abandonment'}
	/>
</KpiRow>

<section>
	<h2>The project</h2>
	<dl class="facts">
		<dt>Ανάδοχος</dt>
		<dd>{p.company}{p.company_address ? ` — ${p.company_address}` : ''}</dd>
		{#if p.funder}
			<dt>Χρηματοδότης</dt>
			<dd>{p.funder}</dd>
		{/if}
		<dt>Τοποθεσία</dt>
		<dd>
			{p.location_text ?? '—'}
			{#if p.pe}<br /><small class="muted">{p.pe}{p.municipality ? ` · Δήμος ${p.municipality}` : ''}</small>{/if}
		</dd>
		{#if p.fire_event}
			<dt>Πυρκαγιά</dt>
			<dd>{p.fire_event}</dd>
		{/if}
	</dl>
</section>

<section>
	<h2>Decision trail ({grInt(p.decisions.length)})</h2>
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
				<tr>
					<td class="tabular muted">{d.issue_date ?? '—'}</td>
					<td>
						<span
							class="chip"
							class:bad={d.relation === 'revocation'}
							class:ok={d.relation === 'completion'}>{RELATION[d.relation] ?? d.relation}</span
						>
						<br /><small class="tabular muted">{d.ada}</small>
					</td>
					<td>
						<small>{d.subject ?? '—'}</small>
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

<style>
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
