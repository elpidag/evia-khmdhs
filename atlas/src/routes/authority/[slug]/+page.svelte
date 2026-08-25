<script lang="ts">
	/**
	 * The forest-authority page in the CONTRACT pages' dress (user,
	 * 2026-08-26): FactsHeader with CAPS label/value rows — the English
	 * name as the emphasised identity row, the Greek registry name as
	 * evidence — the region map in the right slot at the facts column's
	 * height, and CAPS .plain sections below. Content unchanged.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import { authEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const a = $derived(data.a);
	const address = $derived(
		[a.contact.street, [a.contact.postal_code, a.contact.city].filter(Boolean).join(' ')]
			.filter(Boolean)
			.join(', ')
	);

	// map height tracks the facts+caveat column — the contract pages' rule
	let leftH = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	const CAVEAT = $derived(
		'Anti-nero € stated net of VAT, even-split across each contract’s authorities; the ΔΑΣΕ ' +
			'side matched from the awarding unit’s name. Office details from the ΥΠΕΝ contact ' +
			'tables, corroborated by the service’s own letterheads.'
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
			<dt class="id">Forest authority</dt>
			<dd class="id">{authEn(a.name)}</dd>
			<dt>In the registry as</dt>
			<dd><small class="muted">{a.name}</small></dd>
			<dt>Regional unit</dt>
			<dd>{ruLabel(a.pe)}</dd>
			{#if a.seat.city}
				<dt>Seat</dt>
				<dd>{a.seat.city}</dd>
			{/if}
			{#if address || a.contact.phone || a.contact.email}
				<dt>Office</dt>
				<dd>
					{address}
					{#if a.contact.phone}<br /><small class="muted">tel. {a.contact.phone}</small>{/if}
					{#if a.contact.email}
						{#if !a.contact.phone}<br />{:else}{' '}{/if}<small class="muted"
							>· <a href={'mailto:' + a.contact.email}>{a.contact.email}</a></small
						>
					{/if}
				</dd>
			{/if}
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Anti-nero works hosted</dt>
			<dd>
				{eurShort(a.antinero.total_eur)}
				<small class="muted"
					>· {grInt(a.antinero.contracts.length)} contracts name this service</small
				>
			</dd>
			<dt>Awarded to forest co-ops</dt>
			<dd>
				{eurShort(a.dase.total_eur)}
				<small class="muted">· {grInt(a.dase.contracts.length)} ΔΑΣΕ contracts</small>
			</dd>
		{/snippet}
		{#snippet map()}
			<div class="detailmap">
				<PaperMap
					width={460}
					height={mapH}
					focusPe={a.pe}
					colorOf={(pe) => (pe === a.pe ? 'color-mix(in srgb, #406e55 26%, #fff)' : '#fff')}
					tipOf={(pe) => `<strong>${ruLabel(pe)}</strong>`}
				>
					{#snippet overlay(ctx)}
						{#if a.seat.lat && a.seat.lon}
							<DotLayer
								{ctx}
								points={[{ lat: a.seat.lat, lon: a.seat.lon, name: a.name }]}
								r={6}
								stroke="none"
								fillOf={() => '#406e55'}
								tipOf={() => `<strong>${authEn(a.name)}</strong><br>seat: ${a.seat.city ?? ''}`}
							/>
						{/if}
					{/snippet}
					{#snippet legend()}
						<div>● office of the authority</div>
					{/snippet}
				</PaperMap>
			</div>
		{/snippet}
	</FactsHeader>

	<div class="pair">
		<section class="plain">
			<h2>As Anti-nero works host</h2>
			{#if a.antinero.top_contractors.length}
				<ul>
					{#each a.antinero.top_contractors as t (t.vat)}
						<li>
							<a href={`/antinero/contractor/${t.vat}`}>{t.name}</a>
							<small class="muted">— {t.n}× · {eurShort(t.eur)}</small>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">No Anti-nero contracts name this authority.</p>
			{/if}
		</section>
		<section class="plain">
			<h2 class="dase">As ΔΑΣΕ awarding unit</h2>
			{#if a.dase.top_coops.length}
				<ul>
					{#each a.dase.top_coops as t (t.vat)}
						<li>
							<a href={`/dase/coop/${t.vat}`}>{t.name}</a>
							<small class="muted">— {t.n}× · {eurShort(t.eur)}</small>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">No ΔΑΣΕ contracts matched to this authority.</p>
			{/if}
		</section>
	</div>

	{#if a.antinero.contracts.length}
		<section class="plain">
			<h2>Anti-nero contracts ({a.antinero.contracts.length})</h2>
			<table>
				<tbody>
					{#each a.antinero.contracts as c (c.reference_number)}
						<tr>
							<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
							<td>
								<a href={`/antinero/contract/${c.reference_number}`}
									>{c.title ?? c.reference_number}</a
								>
								{#if c.n_auths > 1}
									<span class="chip" title="value split across {c.n_auths} authorities">
										spans {c.n_auths} authorities
									</span>
								{/if}
							</td>
							<td class="muted"><small>{c.contractors ?? ''}</small></td>
							<td class="num">{eur(c.eff)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</section>
	{/if}

	{#if a.dase.contracts.length}
		<section class="plain">
			<h2>ΔΑΣΕ contracts awarded ({a.dase.contracts.length})</h2>
			<table>
				<tbody>
					{#each a.dase.contracts.slice(0, 40) as c (c.reference_number)}
						<tr>
							<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
							<td
								><a href={`/dase/contract/${c.reference_number}`}
									>{c.title ?? c.reference_number}</a
								></td
							>
							<td class="muted"><small>{c.contractor_name ?? ''}</small></td>
							<td class="num">{eur(c.total_cost_with_vat)}</td>
						</tr>
					{/each}
					{#if a.dase.contracts.length > 40}
						<tr
							><td colspan="4" class="muted"
								><small>… {grInt(a.dase.contracts.length - 40)} more</small></td
							></tr
						>
					{/if}
				</tbody>
			</table>
		</section>
	{/if}
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
	.plain h2.dase {
		color: var(--c-dase);
	}
	/* the contract pages' map dress; the authorities wear their own green */
	.detailmap :global(.map) {
		background: #f2f2f2;
		border: 1px solid var(--line);
		--map-accent: #406e55;
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
	td a,
	li a,
	dd a {
		text-decoration: none;
	}
	td a:hover,
	li a:hover,
	dd a:hover {
		text-decoration: underline;
	}
</style>
