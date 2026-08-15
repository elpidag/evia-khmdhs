<script lang="ts">
	import { ruLabel } from '$lib/transforms/regions';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);

	const ACT_KIND: Record<string, string> = {
		repair_permit: 'Άδεια επισκευής',
		reconstruction: 'Ανακατασκευή',
		autostegasi: 'Αυτοστέγαση',
		progress_dose: 'Βεβαίωση προόδου / δόση',
		completion: 'Βεβαίωση περαίωσης',
		ss_other: 'Πράξη Σ.Σ.',
		other: 'Πράξη'
	};
	const STATUS: Record<string, string> = {
		approved: 'εγκεκριμένη Σ.Σ.',
		in_progress: 'σε εξέλιξη (δόσεις)',
		completed: 'περαιωμένη',
		single_act: 'μεμονωμένη πράξη'
	};
</script>

<svelte:head>
	<title>{c.fire_label ?? 'Αρωγή'} — aid case</title>
</svelte:head>

<p class="crumb"><a href="/arogi">← Αρωγή πυροπλήκτων</a></p>

<hgroup>
	<h1>{c.fire_label ?? 'Aid case'}</h1>
	<p class="muted tabular">
		{c.kind === 'batch' ? `Πράξη ${c.ada}` : c.case_key?.startsWith('ACT:') ? 'single act' : `file ${c.case_key}`}
		{#if c.status}<span class="chip" class:ok={c.status === 'completed'}>{STATUS[c.status] ?? c.status}</span>{/if}
		{#if c.pe}· {ruLabel(c.pe)}{/if}
	</p>
</hgroup>

<p class="privacy muted">
	<small>Owners' names are never stored or displayed here; the signed act PDFs on Διαύγεια
	remain the public record. <a href="/methodology#arogi">Methodology</a></small>
</p>

<KpiRow>
	{#if c.kind === 'batch'}
		<StatPair value={c.budget_eur ? eurShort(c.budget_eur) : '—'} label="budget (Πράξη)" basis="ΠΔΕ enrolment, not a payment" color="var(--c-antinero)" />
	{:else}
		<StatPair
			value={c.approved_eur ? eurShort(c.approved_eur) : '—'}
			label="Σ.Σ. approved"
			compare={c.dka_eur ? `${eurShort(c.dka_eur)} δωρεάν αρωγή${c.loan_eur ? ` + ${eurShort(c.loan_eur)} άτοκο δάνειο` : ''}` : ''}
			basis="as stated in the act(s)"
			color="var(--c-antinero)"
		/>
		<StatPair value={String(c.n_acts ?? 1)} label="acts on the trail" compare="{c.first_date ?? '—'} → {c.last_date ?? '—'}" />
	{/if}
</KpiRow>

{#if c.quote}
	<blockquote class="excerpt">«{c.quote}»</blockquote>
{/if}

{#if c.acts?.length}
	<section>
		<h2>Act trail ({c.acts.length})</h2>
		<table class="listing">
			<thead><tr><th>Date</th><th>Act</th><th class="num">Σ.Σ. €</th><th class="num">ΔΚΑ / δάνειο</th><th>PDF</th></tr></thead>
			<tbody>
				{#each c.acts as a (a.ada)}
					<tr>
						<td class="tabular muted">{a.issue_date ?? '—'}</td>
						<td>
							<span class="chip">{ACT_KIND[a.kind] ?? a.kind}</span>
							<br /><small class="muted">{(a.subject ?? '').slice(0, 130)}</small>
							{#if a.fire_excerpt}<blockquote class="excerpt"><small>«{a.fire_excerpt.slice(0, 160)}»</small></blockquote>{/if}
						</td>
						<td class="num">{a.ss_total_eur === null ? '—' : eur(a.ss_total_eur)}</td>
						<td class="num muted"><small>{a.dka_eur === null ? '—' : eur(a.dka_eur)}{a.loan_eur !== null ? ` / ${eur(a.loan_eur)}` : ''}</small></td>
						<td class="nowrap">
							<a href={`/pdf/diavgeia/${a.ada}`} target="_blank" rel="noopener">📄 PDF</a>
							<br /><a class="ext" href={`https://diavgeia.gov.gr/decision/view/${a.ada}`} target="_blank" rel="noopener"><small>Διαύγεια ↗</small></a>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<style>
	.crumb a { text-decoration: none; color: var(--ink-soft); }
	.muted { color: var(--ink-soft); }
	.excerpt { margin: var(--sp-2) 0; padding-left: var(--sp-2); border-left: 2px solid var(--line-strong); color: var(--ink-soft); font-style: italic; }
	.chip.ok { background: var(--c-anadohoi); color: #fff; border-color: var(--c-anadohoi); }
	.nowrap { white-space: nowrap; }
	section { margin-top: var(--sp-6); }
	td a { text-decoration: none; }
	td a:hover { text-decoration: underline; }
</style>
