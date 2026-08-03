<script lang="ts">
	import SearchBox from '$lib/ui/SearchBox.svelte';
	import { eur, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>ΔΑΣΕ co-operatives{data.q ? ` — ${data.q}` : ''}</title>
</svelte:head>

<hgroup>
	<h1>Forest labour co-operatives</h1>
	<p class="muted">
		{grInt(data.rows.length)} entities{data.q ? ` for «${data.q}»` : ''} · merged across registry
		spellings by canonical ΑΦΜ · stated € excl. VAT
	</p>
</hgroup>

<SearchBox placeholder="Search co-op name or ΑΦΜ…" />

<table class="listing">
	<thead>
		<tr>
			<th>Co-operative</th>
			<th class="tabular">ΑΦΜ</th>
			<th class="num">Contracts</th>
			<th class="num">Units</th>
			<th class="num">Direct %</th>
			<th class="num">Total (stated, net)</th>
		</tr>
	</thead>
	<tbody>
		{#each data.rows as r (r.vat)}
			<tr>
				<td>
					<a href={`/dase/coop/${r.vat}`}>{r.name}</a>
					{#if !r.is_curated}<span class="chip">not a curated co-op</span>{/if}
				</td>
				<td class="tabular muted">{r.vat}</td>
				<td class="num">{r.n_contracts}</td>
				<td class="num">{r.n_units}</td>
				<td class="num">{r.pct_direct === null ? '—' : pct(r.pct_direct)}</td>
				<td class="num">{eur(r.total_eur)}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if !data.rows.length}
	<p class="muted">No co-ops match «{data.q}».</p>
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
