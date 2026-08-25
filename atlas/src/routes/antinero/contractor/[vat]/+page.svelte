<script lang="ts">
	/**
	 * The contractor page in the CONTRACT pages' dress (user, 2026-08-26):
	 * FactsHeader with CAPS label/value rows — the display name as the
	 * emphasised identity row — the map in the right slot as tall as the
	 * facts column, provenance in the caveat, and CAPS .plain sections
	 * below. Content unchanged; only the presentation moved.
	 */
	import FactsHeader from '$lib/detail/FactsHeader.svelte';
	import Hint from '$lib/ui/Hint.svelte';
	import { registryStatusNote } from '$lib/transforms/registry';
	import { ruLabel } from '$lib/transforms/regions';
	import YearBars from '$lib/charts/YearBars.svelte';
	import ChoroLegend from '$lib/maps/ChoroLegend.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { RAMP_WORKS, makeChoro } from '$lib/maps/useGeo';
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
	const maxSplit = $derived(Math.max(...b.map_data.regions.map((r) => r.split_eur), 1));
	const choro = $derived(makeChoro(RAMP_WORKS, maxSplit));

	// map height tracks the facts+caveat column — the contract pages' rule
	let leftH = $state(0);
	const mapH = $derived(Math.max(420, Math.round(leftH)));

	const CAVEAT = $derived(
		'Stated € excl. VAT; a contract signed jointly is split evenly between its partners, so ' +
			'the totals count this company’s share. The map shades the regional units of its works ' +
			'(even-split €) and marks the registered office' +
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
			<dt class="id">Anti-nero contractor</dt>
			<dd class="id">{name}</dd>
			<dt>ΑΦΜ</dt>
			<dd>
				{b.summary.vat_number}
				{#if b.summary.name_en}<small class="muted">· {b.summary.name_en}</small>{/if}
			</dd>
			{#if alsoKnown.length}
				<dt>In the registry as</dt>
				<dd><small class="muted">{alsoKnown.join(' · ')}</small></dd>
			{/if}
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Total awarded</dt>
			<dd>
				{eurShort(b.summary.total_eur)}
				<small class="muted">across {grInt(b.summary.n_contracts)} contracts</small>
			</dd>
			<dt>Direct awards</dt>
			<dd>
				{b.summary.pct_direct === null ? '—' : pct(b.summary.pct_direct)}
				<small class="muted">· {grInt(b.summary.n_single_bidder)} single-bid contracts</small>
			</dd>
			<dt>Regions worked in</dt>
			<dd>
				{grInt(regionMap.size)}
				<small class="muted">· {grInt(b.summary.n_consortium)} consortium contracts</small>
			</dd>
			<dt>Active period</dt>
			<dd>
				{(b.summary.first_signed ?? '—').slice(0, 4)}–{(b.summary.last_signed ?? '—').slice(2, 4)}
			</dd>
			<dt class="gap"></dt>
			<dd class="gap"></dd>
			<dt>Registered office</dt>
			<dd>
				{#if b.location}
					{b.location.address ?? ''}{b.location.postal_code
						? `, ${b.location.postal_code}`
						: ''}
					{b.location.city ?? ''}
					{#if b.location.region_pe}<small class="muted">· {ruLabel(b.location.region_pe)}</small
						>{/if}
					<br />
					<small class="muted">
						{#if b.location.seat_source === 'contract' && b.location.seat_ref}
							as stated in contract
							<a href={`/antinero/contract/${b.location.seat_ref}`}>{b.location.seat_ref}</a>
						{:else if b.location.seat_source === 'register'}
							registered seat in ΓΕΜΗ / VIES today
						{:else if b.location.seat_source === 'website'}
							the address the company itself publishes
						{:else}
							source: {b.location.source ?? '—'}
						{/if}
					</small>
					{#if b.location.seat_excerpt}
						<br /><small class="muted quote"
							>{#if b.location.seat_source !== 'contract'}seat as its contract states it:
							{/if}«{b.location.seat_excerpt}»</small
						>
					{/if}
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
		{/snippet}
		{#snippet map()}
			<div class="detailmap">
				<PaperMap
					width={460}
					height={mapH}
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
								stroke="none"
								fillOf={() => 'var(--c-dase-deep)'}
								tipOf={() =>
									`<strong>Registered office</strong><br>${b.location?.address ?? ''}, ${
										b.map_data.home?.city ?? ''
									}<br><span style="color:var(--ink-faint)">${pointWording(b.location)}</span>`}
							/>
						{/if}
					{/snippet}
					{#snippet legend()}
						<ChoroLegend ramp={RAMP_WORKS} max={maxSplit} title="€ of works (even-split)" />
						<div style="margin-top:4px">
							● registered office{b.map_data.home ? '' : ' — not geocoded'}
						</div>
					{/snippet}
				</PaperMap>
			</div>
		{/snippet}
	</FactsHeader>

	<section class="plain">
		<h2>€ per year</h2>
		<!-- the Anti-nero surfaces are black-white-greyscale (user, 2026-08-20) -->
		<YearBars rows={b.yearly.years} color="var(--c-antinero)" />
	</section>

	{#if b.partners.length || b.signers.length}
		<div class="pair">
			{#if b.partners.length}
				<section class="plain">
					<h2>Consortium partners</h2>
					<ul>
						{#each b.partners as p (p.vat_number)}
							<li>
								<a href={`/antinero/contractor/${p.vat_number}`}>{p.name}</a>
								<small class="muted">({p.n_shared} shared)</small>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
			{#if b.signers.length}
				<section class="plain">
					<h2>Awarded by</h2>
					<ul>
						{#each b.signers as s (s.name)}
							<li>
								{s.name}
								<small class="muted">— {s.n_contracts}× · {eurShort(s.total_eur)}</small>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
		</div>
	{/if}

	<section class="plain">
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
							<a href={`/antinero/contract/${r.reference_number}`}
								>{r.title ?? r.reference_number}</a
							>
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
	.quote {
		font-style: italic;
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
