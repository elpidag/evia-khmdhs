<script lang="ts">
	import Hint from '$lib/ui/Hint.svelte';
	import { registryStatusNote } from '$lib/transforms/registry';
	import { ruLabel } from '$lib/transforms/regions';
	import YearBars from '$lib/charts/YearBars.svelte';
	import ChoroLegend from '$lib/maps/ChoroLegend.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, makeChoro } from '$lib/maps/useGeo';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const b = $derived(data.b);
	// GROUP_CONCAT gives every registry spelling in arbitrary order. The
	// curated display name wins (DATA_DECISIONS 2026-08-20) — one name per
	// ΑΦΜ, read from the documents — and the spellings stay on the page as
	// the evidence of what it is being shown instead of.
	const variants = $derived(b.summary.names.split(','));
	const name = $derived(
		b.summary.name ??
			b.location?.legal_name ??
			[...variants].sort((a, b2) => b2.length - a.length)[0] ??
			b.summary.vat_number
	);
	const alsoKnown = $derived(
		[...new Set([...variants, b.location?.legal_name].filter(Boolean) as string[])].filter(
			(v) => v.trim() && v.trim() !== name
		)
	);
	const regionMap = $derived(new Map(b.map_data.regions.map((r) => [r.pe, r])));
	const maxSplit = $derived(Math.max(...b.map_data.regions.map((r) => r.split_eur), 1));
	const choro = $derived(makeChoro(RAMP_WORKS, maxSplit));
</script>

<svelte:head>
	<title>{name} — Anti-nero contractor</title>
	<meta property="og:title" content={name} />
	<meta
		property="og:description"
		content="{grInt(b.summary.n_contracts)} Anti-nero contracts, {eurShort(
			b.summary.total_eur
		)} · {b.location?.city ?? ''}"
	/>
</svelte:head>

<p class="crumb"><a href="/antinero/contractors">← Anti-nero contractors</a></p>

<hgroup>
	<h1>{name}</h1>
	<p class="muted tabular">
		ΑΦΜ {b.summary.vat_number}
		{#if b.location?.city}· {b.location.city}{/if}
		{#if b.location?.region_pe}({ruLabel(b.location.region_pe)}){/if}
		{#if b.location?.gemi && b.location.gemi !== '-1'}
			· <a href={`https://publicity.businessportal.gr/company/${b.location.gemi}`} target="_blank"
				rel="noopener">ΓΕΜΗ profile</a>
		{/if}
		{#if b.summary.name_en}· {b.summary.name_en}{/if}
		{#if b.location?.gemi_status && b.location.gemi_status !== 'Ενεργή'}
			· <span class="gone">{b.location.gemi_status}</span><Hint
				text={registryStatusNote({ status: b.location.gemi_status })}
			/>
		{/if}
	</p>
	{#if alsoKnown.length}
		<p class="also">In the registry as {alsoKnown.join(' · ')}</p>
	{/if}
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(b.summary.total_eur)}
		label="across {grInt(b.summary.n_contracts)} contracts"
		basis="stated € excl. VAT · a jointly signed contract counts as this partner's even share"
		color="var(--c-antinero)"
	/>
	<StatPair
		value={b.summary.pct_direct === null ? '—' : pct(b.summary.pct_direct)}
		label="direct awards"
		compare="{grInt(b.summary.n_single_bidder)} single-bid contracts"
	/>
	<StatPair
		value={grInt(regionMap.size)}
		label="regions worked in"
		compare="{grInt(b.summary.n_consortium)} consortium contracts"
	/>
	<StatPair
		value="{(b.summary.first_signed ?? '—').slice(0, 4)}–{(b.summary.last_signed ?? '—').slice(
			2,
			4
		)}"
		label="active period"
	/>
</KpiRow>

{#if variants.length > 1}
	<p class="muted"><small>Registry spellings ({variants.length}): {variants.join(' · ')}</small></p>
{/if}

<div class="cols">
	<section>
		<h2>Home base and work regions</h2>
		<PaperMap
			interactive={false}
			colorOf={(pe) => choro(regionMap.get(pe)?.split_eur ?? 0)}
			tipOf={(pe) => {
				const r = regionMap.get(pe);
				return r
					? `<strong>${ruLabel(pe)}</strong><br>${grInt(r.n_contracts)} contracts · ${eur(r.split_eur)}`
					: `<strong>${ruLabel(pe)}</strong>`;
			}}
		>
			{#snippet overlay(ctx)}
				{#if b.map_data.home}
					<DotLayer
						{ctx}
						points={[{ lat: b.map_data.home.lat, lon: b.map_data.home.lon, name }]}
						r={6}
						fillOf={() => 'var(--c-dase-deep)'}
						tipOf={() =>
							`<strong>Registered HQ</strong><br>${b.location?.address ?? ''}, ${
								b.map_data.home?.city ?? ''
							}<br><span style="color:var(--ink-faint)">geocode precision: ${
								b.map_data.home?.precision
							}</span>`}
					/>
				{/if}
			{/snippet}
			{#snippet legend()}
				<ChoroLegend ramp={RAMP_WORKS} max={maxSplit} title="€ of works (even-split)" />
				<div style="margin-top:4px">● HQ{b.map_data.home ? '' : ' — not geocoded'}</div>
			{/snippet}
		</PaperMap>
		{#if b.location}
			<p class="muted">
				<small>
					{b.location.address ?? ''}{b.location.postal_code ? `, ${b.location.postal_code}` : ''}
					{b.location.city ?? ''} · source: {b.location.source ?? '—'}
					{#if b.location.geo_precision}· precision: {b.location.geo_precision}{/if}
				</small>
			</p>
		{:else}
			<p class="muted"><small>Home location not resolved — honestly unlocated.</small></p>
		{/if}
	</section>

	<section>
		<h2>€ per year</h2>
		<YearBars rows={b.yearly.years} />

		{#if b.partners.length}
			<h2>Consortium partners</h2>
			<ul>
				{#each b.partners as p (p.vat_number)}
					<li>
						<a href={`/antinero/contractor/${p.vat_number}`}>{p.name}</a>
						<small class="muted">({p.n_shared} shared)</small>
					</li>
				{/each}
			</ul>
		{/if}

		{#if b.signers.length}
			<h2>Awarded by</h2>
			<ul>
				{#each b.signers as s (s.name)}
					<li>{s.name} <small class="muted">— {s.n_contracts}× · {eurShort(s.total_eur)}</small></li>
				{/each}
			</ul>
		{/if}
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
				<th class="num">Stated € (net)</th>
			</tr>
		</thead>
		<tbody>
			{#each b.contracts as r (r.reference_number)}
				<tr class:dead={r.cancelled === 1}>
					<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
					<td>
						<a href={`/antinero/contract/${r.reference_number}`}>{r.title ?? r.reference_number}</a>
						{#if r.n_partners > 1}<span class="chip">consortium ×{r.n_partners}</span>{/if}
						{#if r.bids_submitted === 1}<span class="chip warn">1 bid</span>{/if}
						{#if r.cancelled}<span class="chip bad">cancelled</span>{/if}
					</td>
					<td class="muted"><small>{r.units_operator_name ?? '—'}</small></td>
					<td class="num">
						{eur(r.total_cost_with_vat)}
						{#if b.summary.shares?.[r.reference_number]}
							{@const sh = b.summary.shares[r.reference_number]}
							<br /><small class="muted"
								>signed with {sh.n_parties - 1} other compan{sh.n_parties > 2
									? 'ies'
									: 'y'} · {eur(sh.share_eur)} counted here</small
							>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	{#if Object.keys(b.summary.shares ?? {}).length}
		<p class="muted">
			<small
				>A contract signed jointly is split evenly between its partners: the table shows each
				contract's own stated value, while this company's totals count its share. Neither the
				registry nor the signed document records who took what.</small
			>
		</p>
	{/if}
</section>

<style>
	/* a company the register no longer lists as active — stated, not hidden */
	.gone {
		color: var(--ink-soft);
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.cols {
		display: grid;
		grid-template-columns: minmax(20rem, 34rem) 1fr;
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
	tr.dead {
		opacity: 0.55;
	}
	.muted {
		color: var(--ink-soft);
	}
	td a,
	li a {
		text-decoration: none;
	}
	td a:hover,
	li a:hover {
		text-decoration: underline;
	}
	.also {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		margin-top: 0.15rem;
	}
</style>
