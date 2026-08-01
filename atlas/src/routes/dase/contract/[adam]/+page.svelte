<script lang="ts">
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eurShort } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const c = $derived(data.c);
</script>

<svelte:head>
	<title>{c.title ?? c.reference_number} — ΔΑΣΕ</title>
	<meta property="og:title" content={c.title ?? c.reference_number} />
	<meta
		property="og:description"
		content="ΔΑΣΕ contract {c.reference_number}: {eurShort(c.total_cost_with_vat ?? 0)} stated"
	/>
</svelte:head>

<p class="crumb"><a href="/dase/contracts">← ΔΑΣΕ contracts</a></p>

<hgroup>
	<h1>{c.title ?? c.reference_number}</h1>
	<p class="muted tabular">
		ADAM {c.reference_number} · signed {(c.contract_signed_date ?? '—').slice(0, 10)} ·
		forest-cooperative dataset
		{#if c.cancelled}<span class="chip bad">cancelled</span>{/if}
		{#if c.bids_submitted === 1}<span class="chip warn">single bidder</span>{/if}
	</p>
</hgroup>

<p>
	<a class="pdf" href={`/pdf/contract/${c.reference_number}`} target="_blank" rel="noopener">
		📄 View the signed contract PDF
	</a>
	<small class="muted">fetched from KHMDHS once, then served from the local cache</small>
</p>

<KpiRow>
	<StatPair
		value={eurShort(c.total_cost_with_vat ?? 0)}
		label="stated value (incl. VAT)"
		compare={c.total_cost_without_vat ? `${eurShort(c.total_cost_without_vat)} net` : ''}
		basis="no payment orders harvested for this dataset"
		color="var(--c-dase)"
	/>
	<StatPair
		value={c.contract_duration ? `${c.contract_duration} ${c.contract_duration_unit ?? ''}` : '—'}
		label="duration"
		compare="{(c.start_date ?? '—').slice(0, 10)} → {(c.end_date ?? 'open').slice(0, 10)}"
	/>
	<StatPair value={c.procedure_type ?? '—'} label="procedure" />
</KpiRow>

<section>
	<h2>Contractors ({c.contractors.length})</h2>
	<table>
		<tbody>
			{#each c.contractors as ct (ct.vat_number)}
				<tr>
					<td><a href={`/dase/coop/${ct.vat_number}`}>{ct.name}</a></td>
					<td class="tabular muted">{ct.vat_number}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<section>
	<h2>Procurement record</h2>
	<dl class="facts">
		<div><dt>Authority</dt><dd>{c.organization_name ?? '—'}</dd></div>
		<div><dt>Operating unit</dt><dd>{c.units_operator_name ?? '—'}</dd></div>
		<div><dt>Signer</dt><dd>{c.signer_name ?? '—'}</dd></div>
		<div><dt>Type</dt><dd>{c.contract_type ?? '—'}</dd></div>
		<div><dt>Legal framework</dt><dd>{c.legal_context ?? '—'}</dd></div>
		<div><dt>Funding</dt><dd>{c.public_funding_ref ?? '—'}</dd></div>
	</dl>
	{#if c.objects.length}
		<h3>Items</h3>
		{#each c.objects as o, i (i)}
			<p class="muted">
				<small>
					{#if o.quantity}{o.quantity} {o.unit_type ?? ''} ·{/if}
					{#if o.cost_without_vat}{eurShort(o.cost_without_vat)} net ·{/if}
					{o.short_description ?? ''}
				</small>
			</p>
		{/each}
	{/if}
	{#if c.cpvs.length}
		<h3>CPV</h3>
		<ul>
			{#each c.cpvs as cpv, i (i)}
				<li>
					<span class="tabular">{cpv.cpv_code}</span>
					{cpv.cpv_description ?? ''}
					{#if cpv.cpv_code === '66519300-4'}<span class="chip warn">registry keying noise</span
						>{/if}
				</li>
			{/each}
		</ul>
	{/if}
</section>

{#if c.notice_reference_number || c.prev_reference_no || c.next_reference_no}
	<section>
		<h2>Related acts</h2>
		<ul>
			{#if c.notice_reference_number}
				<li>Tender notice: <span class="tabular">{c.notice_reference_number}</span></li>
			{/if}
			{#if c.prev_reference_no}
				<li>
					Previous version:
					<a class="tabular" href={`/dase/contract/${c.prev_reference_no}`}>{c.prev_reference_no}</a>
				</li>
			{/if}
			{#if c.next_reference_no}
				<li>
					Next version:
					<a class="tabular" href={`/dase/contract/${c.next_reference_no}`}>{c.next_reference_no}</a>
				</li>
			{/if}
		</ul>
	</section>
{/if}

<style>
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	section {
		margin-bottom: var(--sp-8);
	}
	.pdf {
		font-weight: 600;
	}
	.facts {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
		gap: var(--sp-2) var(--sp-6);
		margin: 0;
	}
	.facts dt {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}
	.facts dd {
		margin: 0 0 var(--sp-2);
		font-size: var(--fs-14);
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
</style>
