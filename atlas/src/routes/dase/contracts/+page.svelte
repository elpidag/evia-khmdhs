<script lang="ts">
	import SearchBox from '$lib/ui/SearchBox.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	let limit = $state(300);
	const shown = $derived(data.rows.slice(0, limit));
</script>

<svelte:head>
	<title>ΔΑΣΕ contracts{data.q ? ` — ${data.q}` : ''}</title>
</svelte:head>

<hgroup>
	<h1>ΔΑΣΕ contracts</h1>
	<p class="muted">
		{grInt(data.rows.length)} live contracts{data.q ? ` for «${data.q}»` : ''} ·
		{eurShort(data.total_eur)} stated (excl. VAT) · forest-cooperative dataset, separate from Anti-nero
	</p>
</hgroup>

<SearchBox placeholder="Search ADAM, title, co-op, Δασαρχείο, organisation… (e.g. Νευροκοπίου, kalampaka)" />

<table class="listing">
	<thead>
		<tr>
			<th>Signed</th>
			<th>Contract</th>
			<th>Co-operative</th>
			<th>Awarding unit</th>
			<th class="num">Value (excl. VAT)</th>
		</tr>
	</thead>
	<tbody>
		{#each shown as r (r.reference_number)}
			<tr>
				<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
				<td><a href={`/dase/contract/${r.reference_number}`}>{r.title ?? r.reference_number}</a></td>
				<td class="muted"><small>{r.contractor_names ?? '—'}</small></td>
				<td class="muted"><small>{r.units_operator_name ?? r.organization_name ?? '—'}</small></td>
				<td class="num">{eur(r.total_cost_with_vat)}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if data.rows.length > limit}
	<button class="btn-more" onclick={() => (limit += 500)}>
		Show more ({grInt(data.rows.length - limit)} remaining)
	</button>
{/if}
{#if !data.rows.length}
	<p class="muted">No ΔΑΣΕ contracts match «{data.q}».</p>
{/if}

<style>
	.listing {
		margin-top: var(--sp-4);
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
