<script lang="ts">
	/**
	 * The co-op page in the CONTRACT pages' dress (user, 2026-08-26):
	 * FactsHeader with CAPS label/value rows, the registered office on the
	 * map slot (the dase_coop_locations layer, now on the payload), CAPS
	 * .plain sections below. Content unchanged; only the presentation.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import { bodyEn, devGreek, orgEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import YearBars from '$lib/charts/YearBars.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const b = $derived(data.b);
	const loc = $derived(b.location ?? null);
	const FORMS: Record<string, string> = {
		dase: 'ΔΑ.Σ.Ε.',
		adse: 'ΑΔΣΕ (αναγκαστικός)',
		edase: 'ΕΔΑΣΕ',
		daseragikos: 'δασεργατικός συνεταιρισμός'
	};

	// map height tracks the facts+caveat column — the contract pages' rule
	let leftH = $state(0);
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

<p class="crumb"><a href="/dase/coops">← Co-operatives</a></p>

<div class="entp">
	<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
		{#snippet facts()}
			<dt class="id">Forest workers' co-operative</dt>
			<dd class="id">{b.summary.name}</dd>
			{#if b.summary.name_en}
				<dt>English name</dt>
				<dd>{b.summary.name_en}</dd>
			{/if}
			<dt>ΑΦΜ</dt>
			<dd>
				{b.summary.vat}
				{#if b.summary.form}<small class="muted">· {FORMS[b.summary.form] ?? b.summary.form}</small
					>{/if}
			</dd>
			{#if b.summary.name_variants.length}
				<dt>In the registry as</dt>
				<dd><small class="muted">{b.summary.name_variants.join(' · ')}</small></dd>
			{/if}
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Total awarded</dt>
			<dd>
				{eurShort(b.summary.total_eur)}
				<small class="muted">across {grInt(b.summary.n_live)} live contracts</small>
			</dd>
			<dt>Active period</dt>
			<dd>
				{(b.summary.first_date ?? '—').slice(0, 7)} → {(b.summary.last_date ?? '—').slice(0, 7)}
			</dd>
			{#if loc}
				<dt class="gap"></dt>
				<dd class="gap"></dd>
				<dt>Registered office</dt>
				<dd>
					{[loc.address, [loc.postal_code, loc.city].filter(Boolean).join(' ')]
						.filter(Boolean)
						.join(', ') || loc.city || '—'}
					{#if loc.region_pe}<small class="muted">· {ruLabel(loc.region_pe)}</small>{/if}
				</dd>
			{/if}
		{/snippet}
		{#snippet map()}
			<div class="detailmap">
				<PaperMap
					width={460}
					height={mapH}
					colorOf={(pe) =>
						loc?.region_pe && pe === loc.region_pe
							? 'color-mix(in srgb, var(--c-dase) 30%, #fff)'
							: '#fff'}
					tipOf={(pe) => `<strong>${ruLabel(pe)}</strong>`}
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
									`<strong>Registered office</strong><br>${loc?.city ?? ''}${
										loc?.geo_precision === 'municipality'
											? '<br><span style="color:var(--ink-faint)">map point at the centre of the settlement named</span>'
											: ''
									}`}
							/>
						{/if}
					{/snippet}
					{#snippet legend()}
						<div>● registered office{loc?.lat ? '' : ' — not geocoded'}</div>
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
		<section class="plain">
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

	<section class="plain">
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
						<td
							><a href={`/dase/contract/${r.reference_number}`}>{r.title ?? r.reference_number}</a
							></td
						>
						<td class="muted"><small>{r.units_operator_name ?? '—'}</small></td>
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
	</section>
</div>

<style>
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
		background: #f2f2f2;
		border: 1px solid var(--line);
		--map-accent: var(--c-dase);
		box-shadow: none;
	}
	.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-8);
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
