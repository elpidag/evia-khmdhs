<script lang="ts">
	import SearchBox from '$lib/ui/SearchBox.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import { scopeLabel } from '$lib/transforms/scopes';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	let limit = $state(300);
	const shown = $derived(data.rows.slice(0, limit));
</script>

<svelte:head>
	<title>Anti-nero contracts{data.q ? ` — ${data.q}` : ''}</title>
</svelte:head>

<hgroup>
	<h1>Anti-nero contracts</h1>
	<p class="muted">
		{grInt(data.rows.length)} contracts{data.q ? ` for «${data.q}»` : ''} ·
		{eurShort(data.total_eur)} effective (excl. VAT) · search is accent-, homoglyph- and Greeklish-tolerant
		(“evias” finds Ευβοίας)
	</p>
</hgroup>

<SearchBox placeholder="Search ADAM, title, contractor, region… (e.g. Ευβοίας, evias, ΒΙΟΣ)" />

<table class="listing">
	<thead>
		<tr>
			<th>Signed</th>
			<th>Contract</th>
			<th>Contractors</th>
			<th>Regions</th>
			<th>Phase</th>
			<th class="num">Value (excl. VAT)</th>
		</tr>
	</thead>
	<tbody>
		{#each shown as r (r.reference_number)}
			<tr class:cancelled={r.cancelled === 1}>
				<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
				<td>
					<a href={`/antinero/contract/${r.reference_number}`}>{r.title ?? r.reference_number}</a>
					{#if r.bids_submitted === 1}<span class="chip warn">1 bid</span>{/if}
					{#if r.cancelled === 1}<span class="chip bad">cancelled</span>{/if}
				</td>
				<td class="muted"><small>{r.contractor_names ?? '—'}</small></td>
				<td class="muted"><small>{r.regions ?? '—'}</small></td>
				<td><span class="chip">{r.scope ? scopeLabel(r.scope) : '—'}</span></td>
				<td class="num">
					{eur(r.total_cost_with_vat)}
					{#if r.n_payments > 0}<br /><small class="muted">{grInt(r.n_payments)} payments</small
						>{/if}
				</td>
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
	<p class="muted">No contracts match «{data.q}».</p>
{/if}

<style>
	.listing {
		margin-top: var(--sp-4);
	}
	tr.cancelled {
		opacity: 0.55;
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
