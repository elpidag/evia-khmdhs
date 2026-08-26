<script lang="ts">
	/**
	 * The contractor page in the CONTRACT pages' dress (user, 2026-08-26):
	 * FactsHeader with CAPS label/value rows — the display name as the
	 * emphasised identity row — the map in the right slot as tall as the
	 * facts column, provenance in the caveat, and CAPS .plain sections
	 * below. Content unchanged; only the presentation moved.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import Fold from '$lib/ui/Fold.svelte';
	import QuoteList from '$lib/detail/QuoteList.svelte';
	import Hint from '$lib/ui/Hint.svelte';
	import { registryStatusNote } from '$lib/transforms/registry';
	import { placeEn } from '$lib/transforms/names';
	import { ruLabel } from '$lib/transforms/regions';
	import YearBars from '$lib/charts/YearBars.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const b = $derived(data.b);

	/** how the map point was placed — never «exact» where OSM gave only the street */
	function pointWording(l: { geo_precision?: string | null; geo_level?: string | null } | null) {
		if (!l?.geo_precision) return '';
		if (l.geo_precision === 'address')
			return l.geo_level === 'number'
				? 'map point at the street number'
				: 'map point on the named street';
		return 'map point at the centre of the settlement named';
	}

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

	// map height tracks the facts+caveat column, width the slot itself —
	// the contract pages' rule exactly
	let leftH = $state(0);
	let mapW = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	// the seat's verbatim clause is evidence, so it lives in EXTRACTED
	// QUOTES with its source document, never in the facts row (user,
	// 2026-08-26)
	const quotes = $derived(
		b.location?.seat_excerpt
			? [
					{
						label: 'Registered office',
						text: b.location.seat_excerpt,
						code: b.location.seat_source === 'contract' ? b.location.seat_ref : null,
						href:
							b.location.seat_source === 'contract' && b.location.seat_ref
								? `/antinero/contract/${b.location.seat_ref}`
								: null,
						note:
							b.location.seat_source === 'register'
								? 'the seat ΓΕΜΗ / VIES record today; the clause is what its contract stated'
								: b.location.seat_source === 'website'
									? 'the address the company itself publishes; the clause is what its contract stated'
									: null
					}
				]
			: []
	);

	const CAVEAT = $derived(
		'Stated € excl. VAT; a contract signed jointly is split evenly between its partners, so ' +
			'the totals count this company’s share. The map marks the regional units it has ' +
			'worked in and its registered office' +
			(b.location?.geo_precision ? ` — ${pointWording(b.location)}` : '') +
			'.'
	);
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

<div class="entp">
	<FactsHeader caveat={CAVEAT} bind:leftHeight={leftH}>
		{#snippet facts()}
			<dt class="id">Name</dt>
			<dd class="id">{name}</dd>
			<dt>ΑΦΜ</dt>
			<dd>{b.summary.vat_number}</dd>
			{#if alsoKnown.length}
				<dt>In the registry as</dt>
				<dd><small class="muted">{alsoKnown.join(' · ')}</small></dd>
			{/if}
			<dt>Registered office</dt>
			<!-- English throughout (user, 2026-08-26): the street and town from
			     the curated transliteration; the verbatim Greek clause below is
			     evidence and stays as the document wrote it -->
			<dd>
				{#if b.location}
					{[placeEn(b.location.address), b.location.postal_code, placeEn(b.location.city)]
						.filter(Boolean)
						.join(', ')}
					{#if b.location.seat_note}
						<br /><small class="muted">{b.location.seat_note}</small>
					{/if}
				{:else}
					<small class="muted">not resolved — honestly unlocated</small>
				{/if}
			</dd>
			{#if b.location?.gemi && b.location.gemi !== '-1'}
				<dt>ΓΕΜΗ</dt>
				<dd>
					<a
						href={`https://publicity.businessportal.gr/company/${b.location.gemi}`}
						target="_blank"
						rel="noopener">profile {b.location.gemi}</a
					>
					{#if b.location.gemi_status && b.location.gemi_status !== 'Ενεργή'}
						· <span class="gone">{b.location.gemi_status}</span><Hint
							text={registryStatusNote({ status: b.location.gemi_status })}
						/>
					{/if}
				</dd>
			{/if}
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Total € awarded</dt>
			<dd>{eurShort(b.summary.total_eur)}</dd>
			<dt>Contracts awarded</dt>
			<dd>{grInt(b.summary.n_contracts)}</dd>
			<dt>Direct awards</dt>
			<dd>{b.summary.pct_direct === null ? '—' : pct(b.summary.pct_direct)}</dd>
			{#if b.summary.n_consortium}
				<dt>Consortium contracts</dt>
				<dd>{grInt(b.summary.n_consortium)}</dd>
			{/if}
			<dt>Active period</dt>
			<dd>
				{(b.summary.first_signed ?? '—').slice(0, 4)}–{(b.summary.last_signed ?? '—').slice(2, 4)}
			</dd>
		{/snippet}
		{#snippet map()}
			<div class="detailmap" bind:clientWidth={mapW}>
				<PaperMap
					width={mapW || 460}
					height={mapH}
					colorOf={(pe) =>
						regionMap.has(pe) ? 'color-mix(in srgb, var(--c-antinero) 22%, #fff)' : '#fff'}
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
								stroke="none"
								fillOf={() => 'var(--c-antinero)'}
								tipOf={() =>
									`<strong>Registered office</strong><br>${placeEn(b.location?.address)}, ${placeEn(
										b.map_data.home?.city
									)}<br><span style="color:var(--ink-faint)">${pointWording(b.location)}</span>`}
							/>
						{/if}
					{/snippet}
				</PaperMap>
			</div>
		{/snippet}
	</FactsHeader>

	<div class="pair">
	<section class="plain">
		<h2>€ per year</h2>
		<!-- the Anti-nero surfaces are black-white-greyscale (user, 2026-08-20) -->
		<YearBars rows={b.yearly.years} color="var(--c-antinero)" />
	</section>
	<div class="foldslot">

	{#if b.partners.length}
		<div class="foldslot">
			<Fold title="Consortium partners">
				<ul>
					{#each b.partners as p (p.vat_number)}
						<li>
							<a href={`/antinero/contractor/${p.vat_number}`}>{p.name}</a>
							<small class="muted">({p.n_shared} shared)</small>
						</li>
					{/each}
				</ul>
			</Fold>
		</div>
	{/if}

		<Fold title="Contracts ({b.contracts.length})">
		<table>
			<thead>
				<tr>
					<th>Signed</th>
					<th>ΑΔΑΜ</th>
					<th class="num">Stated € (net)</th>
				</tr>
			</thead>
			<tbody>
				{#each b.contracts as r (r.reference_number)}
					<tr class:dead={r.cancelled === 1}>
						<td class="tabular muted">{(r.contract_signed_date ?? '—').slice(0, 10)}</td>
						<td class="tabular">
							<a href={`/antinero/contract/${r.reference_number}`}>{r.reference_number}</a>
							{#if r.n_partners > 1}<span class="chip">consortium ×{r.n_partners}</span>{/if}
							{#if r.bids_submitted === 1}<span class="chip warn">1 bid</span>{/if}
							{#if r.cancelled}<span class="chip bad">cancelled</span>{/if}
						</td>
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
		</Fold>
	</div>
	</div>

	{#if quotes.length}
		<Fold title="Extracted quotes from documents">
			<QuoteList heading={null} {quotes} />
		</Fold>
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
	/* the contract pages' map dress on the entity map */
	.detailmap :global(.map) {
		background: #f2f2f2;
		border: 1px solid var(--line);
		--map-accent: var(--c-antinero);
		box-shadow: none;
	}
	.entp {
		--fold-accent: var(--c-antinero);
	}
	.foldslot :global(.fold) {
		margin-top: 0;
	}
	/* € per year beside the contracts, on FactsHeader's own columns, so
	   the right-hand section lines up with the map above (user, 2026-08-26) */
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
	/* a company the register no longer lists as active — stated, not hidden */
	.gone {
		color: var(--ink-soft);
	}
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	tr.dead {
		opacity: 0.55;
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
