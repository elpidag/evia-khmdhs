<script lang="ts">
	import SearchBox from '$lib/ui/SearchBox.svelte';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';
	import { eur, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Anti-nero contractors{data.q ? ` — ${data.q}` : ''}</title>
</svelte:head>

<hgroup>
	<h1>Anti-nero contractors</h1>
	<p class="muted">
		{grInt(data.rows.length)} companies{data.q ? ` for «${data.q}»` : ''} · a jointly signed
		contract is split evenly between its partners
	</p>
</hgroup>

<div class="bar">
	<SearchBox placeholder="Search name or ΑΦΜ… (Greeklish works)" />
	<SegmentToggle
		param="sort"
		fallback="total_eur"
		options={[
			{ value: 'total_eur', label: 'By €' },
			{ value: 'n_contracts', label: 'By contracts' },
			{ value: 'name', label: 'By name' }
		]}
	/>
</div>

<table class="listing">
	<thead>
		<tr>
			<th>Contractor</th>
			<th class="tabular">ΑΦΜ</th>
			<th class="num">Contracts</th>
			<th class="num">Single-bid</th>
			<th class="num">Direct %</th>
			<th class="num">Total (net)</th>
		</tr>
	</thead>
	<tbody>
		{#each data.rows as r (r.vat_number)}
			<tr>
				<td><a href={`/antinero/contractor/${r.vat_number}`}>{r.name}</a></td>
				<td class="tabular muted">{r.vat_number}</td>
				<td class="num">{r.n_contracts}</td>
				<td class="num">{r.n_single_bidder || '—'}</td>
				<td class="num">{r.pct_direct === null ? '—' : pct(r.pct_direct)}</td>
				<td class="num">{eur(r.total_eur)}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if !data.rows.length}
	<p class="muted">No contractors match «{data.q}».</p>
{/if}

<style>
	.bar {
		display: flex;
		gap: var(--sp-4);
		align-items: center;
		flex-wrap: wrap;
	}
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
