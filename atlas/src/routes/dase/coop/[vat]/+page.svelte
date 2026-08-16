<script lang="ts">
	import { bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import YearBars from '$lib/charts/YearBars.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const b = $derived(data.b);
	const FORMS: Record<string, string> = {
		dase: 'ΔΑ.Σ.Ε.',
		adse: 'ΑΔΣΕ (αναγκαστικός)',
		edase: 'ΕΔΑΣΕ',
		daseragikos: 'δασεργατικός συνεταιρισμός'
	};
</script>

<svelte:head>
	<title>{b.summary.name} — ΔΑΣΕ co-op</title>
	<meta property="og:title" content={b.summary.name} />
	<meta
		property="og:description"
		content="{grInt(b.summary.n_live)} live contracts, {eurShort(b.summary.total_eur)} stated (excl. VAT)"
	/>
</svelte:head>

<p class="crumb"><a href="/dase/coops">← Co-operatives</a></p>

<hgroup>
	<h1>{b.summary.name}</h1>
	{#if b.summary.name_en}
		<p class="ename">{b.summary.name_en}</p>
	{/if}
	<p class="muted tabular">
		ΑΦΜ {b.summary.vat}
		{#if b.summary.form}· {FORMS[b.summary.form] ?? b.summary.form}{/if}
		· forest labour co-operative
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(b.summary.total_eur)}
		label="across {grInt(b.summary.n_live)} live contracts"
		basis="stated € excl. VAT"
		color="var(--c-dase)"
	/>
	<StatPair
		value="{(b.summary.first_date ?? '—').slice(0, 7)} → {(b.summary.last_date ?? '—').slice(
			0,
			7
		)}"
		label="active period"
	/>
	<StatPair
		value={grInt(b.summary.name_variants.length)}
		label="registry spellings"
		compare={b.summary.name_variants.length > 1 ? 'merged by canonical ΑΦΜ' : ''}
	/>
</KpiRow>

{#if b.summary.name_variants.length}
	<p class="muted"><small>Appears in the registry as: {b.summary.name_variants.join(' · ')}</small></p>
{/if}

<div class="cols">
	<section>
		<h2>Stated € per year</h2>
		<YearBars rows={b.yearly} color="var(--c-dase)" />
	</section>
	<section>
		<h2>Awarding units</h2>
		<table>
			<tbody>
				{#each b.units as u, i (i)}
					<tr>
						<td title={devGreek(u.unit)}>{bodyEn(u.unit) || '—'}</td>
						<td class="muted" title={devGreek(u.org)}><small>{orgEn(u.org)}</small></td>
						<td class="num">{u.n_contracts}×</td>
						<td class="num">{eurShort(u.total_eur)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
</div>

<section>
	<h2>Contracts ({b.contracts.length})</h2>
	<table>
		<thead>
			<tr>
				<th>Signed</th>
				<th>Contract</th>
				<th>Unit</th>
				<th class="num">Value</th>
			</tr>
		</thead>
		<tbody>
			{#each b.contracts as r (r.reference_number)}
				<tr>
					<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
					<td><a href={`/dase/contract/${r.reference_number}`}>{r.title ?? r.reference_number}</a></td>
					<td class="muted"><small>{r.units_operator_name ?? '—'}</small></td>
					<td class="num">{eur(r.total_cost_with_vat)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.cols {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
		margin-bottom: var(--sp-6);
	}
	@media (max-width: 900px) {
		.cols {
			grid-template-columns: 1fr;
		}
	}
	section h2 {
		font-size: var(--fs-18);
	}
	.muted {
		color: var(--ink-soft);
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	.ename {
		color: var(--c-dase);
		font-weight: 700;
		font-size: var(--fs-14);
		letter-spacing: 0.04em;
		margin: 2px 0 0;
	}
</style>
