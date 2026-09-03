<script lang="ts">
	/**
	 * The forest-authority page on the ENTITY pattern the co-op and the
	 * contractor pages settled into (user, 2026-08-26): identity facts
	 * first — the English name, the Greek registry name as evidence, the
	 * office, the territory — then the measures; the map in the right slot
	 * at the facts column's height, framed on the WHOLE jurisdiction (its
	 * seat Π.Ε. plus the units it administers beyond it); and below, one
	 * row per dataset — the entities it deals with on the left, its
	 * contracts in a closed fold aligned with the map above.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import Fold from '$lib/ui/Fold.svelte';
	import { authEn, placeEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const a = $derived(data.a);

	// English throughout (user, 2026-08-26): the street and post town from
	// the curated place layer; the Greek stays the stored value
	const address = $derived(
		[
			placeEn(a.contact.street),
			[a.contact.postal_code, placeEn(a.contact.city) || placeEn(a.seat.city)]
				.filter(Boolean)
				.join(' ')
		]
			.filter(Boolean)
			.join(', ')
	);
	/** the whole territory: the seat's Π.Ε. and the ones it administers too */
	const territory = $derived([a.pe, ...(a.covers_pe ?? [])].filter(Boolean));
	const covered = $derived(new Set(territory));

	// map height tracks the facts+caveat column, width the slot itself —
	// the contract pages' rule exactly
	let leftH = $state(0);
	let mapW = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	const CAVEAT = $derived(
		'Anti-nero € stated net of VAT, split evenly across the services a contract names; the ' +
			'ΔΑΣΕ side matched from the awarding unit’s own name. Office details from the ΥΠΕΝ ' +
			'contact tables, corroborated by the service’s own letterheads.'
	);
</script>

<svelte:head>
	<title>{authEn(a.name)} — forest authority</title>
	<meta property="og:title" content={authEn(a.name)} />
	<meta
		property="og:description"
		content="{authEn(a.name)}: {eurShort(a.antinero.total_eur)} of Anti-nero works · {grInt(
			a.dase.contracts.length
		)} ΔΑΣΕ contracts awarded"
	/>
</svelte:head>

<p class="crumb"><a href="/authorities">← Network of actors</a></p>

<div class="entp">
	<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
		{#snippet facts()}
			<dt class="id">Name</dt>
			<dd class="id" title={a.name}>{authEn(a.name)}</dd>
			{#if address}
				<dt>Office</dt>
				<dd>{address}</dd>
			{/if}
			<dt>{territory.length > 1 ? 'Regional units administered' : 'Regional unit'}</dt>
			<dd>{territory.map(ruLabel).join(' · ')}</dd>
			<dt class="gap"></dt>
			<dd class="gap"></dd>
{#if a.antinero.contracts.length}
				<dt>Anti-nero works supervised</dt>
				<dd>{eurShort(a.antinero.total_eur)}</dd>
				<dt>Anti-nero contracts</dt>
				<dd>{grInt(a.antinero.contracts.length)}</dd>
			{/if}
			{#if a.dase.contracts.length}
				<dt>Awarded to forest co-ops</dt>
				<dd>{eurShort(a.dase.total_eur)}</dd>
				<dt>ΔΑΣΕ contracts awarded</dt>
				<dd>{grInt(a.dase.contracts.length)}</dd>
			{/if}
			{#if !a.antinero.contracts.length && !a.dase.contracts.length}
				<dt>Contracts</dt>
				<dd><small class="muted">none recorded in its territory by this research</small></dd>
			{/if}
		{/snippet}
		{#snippet map()}
			<div class="detailmap" bind:clientWidth={mapW}>
				<PaperMap
					width={mapW || 460}
					height={mapH}
					fitPes={territory}
					fitPoints={a.seat.lat && a.seat.lon ? [[a.seat.lon, a.seat.lat]] : null}
					fitPad={0.15}
					colorOf={(pe) =>
						pe === a.pe
							? 'color-mix(in srgb, color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black) 30%, var(--paper))'
							: covered.has(pe)
								? 'color-mix(in srgb, color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black) 14%, var(--paper))'
								: 'var(--paper)'}
				>
					{#snippet overlay(ctx)}
						{#if a.seat.lat && a.seat.lon}
							<DotLayer
								{ctx}
								points={[{ lat: a.seat.lat, lon: a.seat.lon, name: a.name }]}
								r={5.5}
								stroke="none"
								fillOf={() => 'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black)'}
								tipOf={() =>
									`<strong>Office</strong><br>${placeEn(a.contact.city) || placeEn(a.seat.city) || ''}`}
							/>
						{/if}
					{/snippet}
				</PaperMap>
			</div>
		{/snippet}
	</FactsHeader>

	<!-- the Anti-nero side: the companies whose works it supervises -->
	{#if a.antinero.contracts.length}
	<div class="pair anti">
		<section class="plain">
			<h2>Anti-nero contractors</h2>
			<ul>
				{#each a.antinero.top_contractors as t (t.vat)}
					<li>
						<a href={`/antinero/contractor/${t.vat}`} title={t.registry_name ?? undefined}
							>{t.name}</a
						>
						<small class="muted">— {t.n}× · {eurShort(t.eur)}</small>
					</li>
				{/each}
			</ul>
		</section>
		<div class="foldslot">
				<Fold title="Anti-nero contracts ({a.antinero.contracts.length})">
					<table>
						<thead>
							<tr>
								<th>Signed</th>
								<th>ΑΔΑΜ</th>
								<th class="num">Stated € (net)</th>
							</tr>
						</thead>
						<tbody>
							{#each a.antinero.contracts as c (c.reference_number)}
								<tr>
									<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
									<td class="tabular"
										><a href={`/antinero/contract/${c.reference_number}`}
											>{c.reference_number}</a
										></td
									>
									<td class="num">
										{eur(c.eff)}
										{#if c.n_auths > 1}
											<br /><small class="muted"
												>works in {c.n_auths} services’ territory · {eur(
													(c.eff ?? 0) / c.n_auths
												)} counted here</small
											>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
					{#if a.antinero.contracts.some((c) => c.n_auths > 1)}
						<p class="muted">
							<small
								>A contract whose works span several services is divided evenly between them:
								the table shows each contract's own value, while this service's total counts
								its share. No document states how the work was distributed.</small
							>
						</p>
					{/if}
				</Fold>
		</div>
	</div>
	{/if}

	<!-- the ΔΑΣΕ side: the co-operatives it awards work to itself -->
	{#if a.dase.contracts.length}
	<div class="pair dase">
		<section class="plain">
			<h2 class="dase">Forest co-operatives awarded</h2>
			<ul>
				{#each a.dase.top_coops as t (t.vat)}
					<li>
						<a href={`/dase/coop/${t.vat}`}>{t.name}</a>
						<small class="muted">— {t.n}× · {eurShort(t.eur)}</small>
					</li>
				{/each}
			</ul>
		</section>
		<div class="foldslot">
				<Fold title="ΔΑΣΕ contracts awarded ({a.dase.contracts.length})">
					<table>
						<thead>
							<tr>
								<th>Signed</th>
								<th>ΑΔΑΜ</th>
								<th class="num">Stated € (net)</th>
							</tr>
						</thead>
						<tbody>
							{#each a.dase.contracts as c (c.reference_number)}
								<tr>
									<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
									<td class="tabular"
										><a href={`/dase/contract/${c.reference_number}`}>{c.reference_number}</a
										></td
									>
									<td class="num">{eur(c.total_cost_with_vat)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</Fold>
		</div>
	</div>
	{/if}

	<!-- what a service does NOT do is a fact too — the network page's own
	     legend distinguishes a service with no contracts recorded -->
	{#if !a.antinero.contracts.length || !a.dase.contracts.length}
		<p class="none muted">
			{#if !a.antinero.contracts.length && !a.dase.contracts.length}
				No Anti-nero contract names this service, and it awarded no contract to a forest
				co-operative, within this research.
			{:else if !a.antinero.contracts.length}
				No Anti-nero contract names this service within this research.
			{:else}
				This service awarded no contract to a forest co-operative within this research.
			{/if}
		</p>
	{/if}
</div>

<style>
	/* each half wears its own dataset's accent on its fold */
	.pair.anti {
		--fold-accent: var(--c-antinero);
	}
	.pair.dase {
		--fold-accent: var(--c-dase);
	}
	.foldslot :global(.fold) {
		margin-top: 0;
	}
	/* the contract pages' section dress */
	.plain {
		margin-bottom: var(--sp-8);
	}
	/* inside a pair the row's own margin does the spacing */
	.pair .plain {
		margin-bottom: 0;
	}
	.none {
		margin: 0 0 var(--sp-8);
		max-width: 46rem;
	}
	.plain h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
		letter-spacing: 0.01em;
		margin: 0 0 var(--sp-3);
	}
	.plain h2.dase {
		color: var(--c-dase);
	}
	/* the contract pages' map dress; the authorities wear their own green */
	.detailmap :global(.map) {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border: 1px solid var(--line);
		--map-accent: color-mix(in srgb, color-mix(in oklab, var(--c-dase) 84%, white) 56%, black);
		box-shadow: none;
	}
	/* the regions rest: no card, and no hover stroke either */
	.detailmap :global(.map .region:hover) {
		stroke: var(--line-strong);
		stroke-width: 0.6;
	}
	/* FactsHeader's own two columns, so each fold lines up with the map */
	.pair {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(300px, 460px);
		gap: var(--sp-8);
		align-items: start;
		margin-bottom: var(--sp-8);
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
	td a,
	li a {
		text-decoration: none;
	}
	td a:hover,
	li a:hover {
		text-decoration: underline;
	}
</style>
