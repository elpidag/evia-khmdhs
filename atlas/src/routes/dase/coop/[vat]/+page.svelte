<script lang="ts">
	/**
	 * The co-op page in the CONTRACT pages' dress (user, 2026-08-26):
	 * FactsHeader with CAPS label/value rows, the registered office on the
	 * map slot (the dase_coop_locations layer, now on the payload), CAPS
	 * .plain sections below. Content unchanged; only the presentation.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import Fold from '$lib/ui/Fold.svelte';
	import { bodyEn, devGreek, orgEn, placeEn } from '$lib/transforms/names';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import YearBars from '$lib/charts/YearBars.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const b = $derived(data.b);
	const loc = $derived(b.location ?? null);
	// map height tracks the facts+caveat column, width the slot itself —
	// the contract pages' rule exactly
	let leftH = $state(0);
	let mapW = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	const CAVEAT = $derived(
		'Stated € excl. VAT; several registry spellings merge on the canonical ΑΦΜ, and a ' +
			'contract signed jointly by several co-ops is split evenly between them. Registered ' +
			'office from VIES, corroborated by the co-ops’ own contract clauses — the official ' +
			'ΥΠΕΝ registry of forest co-operatives is not openly accessible.'
	);
</script>

<svelte:head>
	<title>{b.summary.name} — ΔΑΣΕ co-op</title>
	<meta property="og:title" content={b.summary.name} />
	<meta
		property="og:description"
		content="{grInt(b.summary.n_live)} live contracts, {eurShort(b.summary.total_eur)} stated (excl. VAT)"
	/>
</svelte:head>

<p class="crumb"><a href="/authorities?list=coops#list">← Forest co-operatives</a></p>

<div class="entp">
	<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
		{#snippet facts()}
			<dt class="id">Name</dt>
			<dd class="id">{b.summary.name}</dd>
			<dt>ΑΦΜ</dt>
			<dd>{b.summary.vat}</dd>
			{#if b.summary.name_variants.length}
				<dt>In the registry as</dt>
				<dd><small class="muted">{b.summary.name_variants.join(' · ')}</small></dd>
			{/if}
			{#if loc}
				<dt>Registered office</dt>
				<!-- English throughout (user, 2026-08-26): toponyms from the
				     curated transliteration, the Greek stays the stored value -->
				<dd>
					<!-- the village and the post town are often the same word;
					     print it once -->
					{placeEn(loc.address) === placeEn(loc.city)
						? [placeEn(loc.city), loc.postal_code].filter(Boolean).join(', ')
						: [placeEn(loc.address), [loc.postal_code, placeEn(loc.city)].filter(Boolean).join(' ')]
								.filter(Boolean)
								.join(', ') || placeEn(loc.city) || '—'}
				</dd>
			{/if}
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Total € awarded</dt>
			<dd>{eurShort(b.summary.total_eur)}</dd>
			<dt>Contracts awarded</dt>
			<dd>{grInt(b.summary.n_live)}</dd>
			<dt>Active period</dt>
			<dd>
				{(b.summary.first_date ?? '—').slice(0, 7)} → {(b.summary.last_date ?? '—').slice(0, 7)}
			</dd>
		{/snippet}
		{#snippet map()}
			<div class="detailmap" bind:clientWidth={mapW}>
				<PaperMap
					width={mapW || 460}
					height={mapH}
					fitPes={loc?.region_pe ? [loc.region_pe] : undefined}
					fitPoints={loc?.lat && loc?.lon ? [[loc.lon, loc.lat]] : null}
					fitPad={0.15}
					colorOf={(pe) =>
						loc?.region_pe && pe === loc.region_pe
							? 'color-mix(in srgb, var(--c-dase) 30%, var(--paper))'
							: 'var(--paper)'}
				>
					{#snippet overlay(ctx)}
						{#if loc?.lat && loc?.lon}
							<DotLayer
								{ctx}
								points={[{ lat: loc.lat, lon: loc.lon, name: b.summary.name }]}
								r={5.5}
								stroke="none"
								fillOf={() => 'var(--c-dase)'}
								tipOf={() =>
									`<strong>Registered office</strong><br>${placeEn(loc?.city)}${
										loc?.geo_precision === 'municipality'
											? '<br><span style="color:var(--ink-faint)">map point at the centre of the settlement named</span>'
											: ''
									}`}
							/>
						{/if}
					{/snippet}
				</PaperMap>
			</div>
		{/snippet}
	</FactsHeader>

	<div class="pair">
		<section class="plain">
			<h2>Stated € per year</h2>
			<YearBars rows={b.yearly} color="var(--c-dase)" />
		</section>
		<div class="foldslot">
		<Fold title="Contracts ({b.contracts.length})">
			<table>
				<thead>
					<tr>
						<th>Signed</th>
						<th>ΑΔΑΜ</th>
						<th class="num">Value</th>
					</tr>
				</thead>
				<tbody>
					{#each b.contracts as r (r.reference_number)}
						<tr>
							<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
							<td class="tabular"
								><a href={`/dase/contract/${r.reference_number}`}>{r.reference_number}</a></td
							>
							<td class="num">
								{eur(r.total_cost_with_vat)}
								{#if r.share_eur !== undefined}
									<br /><small class="muted"
										>signed with {(r.n_parties ?? 2) - 1} other co-op{(r.n_parties ?? 2) > 2
											? 's'
											: ''} · {eur(r.share_eur)} counted here</small
									>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
			{#if b.contracts.some((r) => r.share_eur !== undefined)}
				<p class="muted">
					<small
						>A contract signed jointly by several co-ops is split evenly between them: the table
						shows each contract's own stated value, while this co-op's totals count its share.
						Neither the registry nor the signed document records who took what.</small
					>
				</p>
			{/if}
		</Fold>
		</div>
	</div>

	<Fold title="Awarding units">
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
	</Fold>
</div>

<style>
	.entp {
		--fold-accent: var(--c-dase);
	}
	.pair :global(.fold),
	.foldslot :global(.fold) {
		margin-top: 0;
	}
	/* the contract pages' section dress */
	.plain {
		margin-bottom: var(--sp-8);
	}
	.plain h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
		letter-spacing: 0.01em;
		margin: 0 0 var(--sp-3);
	}
	/* the contract pages' map dress on the entity map */
	.detailmap :global(.map) {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border: 1px solid var(--line);
		--map-accent: var(--c-dase);
		box-shadow: none;
	}
	/* the same two columns as FactsHeader above it, so AWARDING UNITS
	   lines up with the map's left edge and shares its width (user,
	   2026-08-26) */
	.pair {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(300px, 460px);
		gap: var(--sp-8);
		align-items: start;
	}
	/* the regions rest: no card, and no hover stroke either */
	.detailmap :global(.map .region:hover) {
		stroke: var(--line-strong);
		stroke-width: 0.6;
	}
	@media (max-width: 900px) {
		.pair {
			grid-template-columns: 1fr;
		}
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
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
