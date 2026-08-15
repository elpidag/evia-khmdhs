<script lang="ts">
	import { ruLabel } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const a = $derived(data.a);
	const kindLabel = $derived(a.kind === 'dx' ? 'Δασαρχείο' : 'Διεύθυνση Δασών');
</script>

<svelte:head>
	<title>{a.name} — forest authority</title>
	<meta property="og:title" content={a.name} />
	<meta
		property="og:description"
		content="{a.name}: {eurShort(a.antinero.total_eur)} of Anti-nero works · {grInt(
			a.dase.contracts.length
		)} ΔΑΣΕ contracts awarded"
	/>
</svelte:head>

<p class="crumb"><a href="/authorities">← Forest authorities</a></p>

<hgroup>
	<h1>{a.name}</h1>
	<p class="muted">
		{kindLabel} · {ruLabel(a.pe)}
		{#if a.seat.city}· seat: {a.seat.city}{/if}
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(a.antinero.total_eur)}
		label="of Anti-nero works on its territory"
		compare="{grInt(a.antinero.contracts.length)} contracts · full exposure {eurShort(
			a.antinero.exposure_eur
		)}"
		basis="stated € excl. VAT, even-split across each contract's authorities"
		color="var(--c-antinero)"
	/>
	<StatPair
		value={eurShort(a.dase.total_eur)}
		label="awarded to forest co-ops"
		compare="{grInt(a.dase.contracts.length)} ΔΑΣΕ contracts"
		basis="stated € excl. VAT"
		color="var(--c-dase)"
	/>
</KpiRow>

<div class="cols">
	<div class="map-holder">
		<PaperMap
			interactive={false}
			focusPe={a.pe}
			colorOf={(pe) => (pe === a.pe ? 'var(--ramp-works-1)' : 'var(--land-empty)')}
		>
			{#snippet overlay(ctx)}
				{#if a.seat.lat && a.seat.lon}
					<DotLayer
						{ctx}
						points={[{ lat: a.seat.lat, lon: a.seat.lon, name: a.name }]}
						r={6}
						fillOf={() => 'var(--accent-deep)'}
						tipOf={() => `<strong>${a.name}</strong><br>seat: ${a.seat.city ?? ''}`}
					/>
				{/if}
			{/snippet}
		</PaperMap>
	</div>

	<div class="roles">
		<section>
			<h2 class="antinero">As Anti-nero works host</h2>
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
		<section>
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
</div>

{#if a.antinero.contracts.length}
	<section>
		<h2>Anti-nero contracts ({a.antinero.contracts.length})</h2>
		<table>
			<tbody>
				{#each a.antinero.contracts as c (c.reference_number)}
					<tr>
						<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
						<td>
							<a href={`/antinero/contract/${c.reference_number}`}>{c.title ?? c.reference_number}</a>
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
	<section>
		<h2>ΔΑΣΕ contracts awarded ({a.dase.contracts.length})</h2>
		<table>
			<tbody>
				{#each a.dase.contracts.slice(0, 40) as c (c.reference_number)}
					<tr>
						<td class="tabular muted">{(c.contract_signed_date ?? '—').slice(0, 10)}</td>
						<td><a href={`/dase/contract/${c.reference_number}`}>{c.title ?? c.reference_number}</a></td>
						<td class="muted"><small>{c.contractor_name ?? ''}</small></td>
						<td class="num">{eur(c.total_cost_with_vat)}</td>
					</tr>
				{/each}
				{#if a.dase.contracts.length > 40}
					<tr><td colspan="4" class="muted"><small>… {grInt(a.dase.contracts.length - 40)} more</small></td></tr>
				{/if}
			</tbody>
		</table>
		<p class="muted"><small>Matched by {a.dase.match_basis}. <a href="/methodology#authorities">Methodology</a>.</small></p>
	</section>
{/if}

<style>
	.crumb a {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.cols {
		display: grid;
		grid-template-columns: minmax(18rem, 26rem) 1fr;
		gap: var(--sp-8);
		margin-bottom: var(--sp-6);
	}
	@media (max-width: 900px) {
		.cols {
			grid-template-columns: 1fr;
		}
	}
	.roles h2 {
		font-family: var(--font-ui);
		font-size: var(--fs-16);
	}
	.roles h2.antinero {
		color: var(--c-antinero);
	}
	.roles h2.dase {
		color: var(--c-dase);
	}
	section {
		margin-bottom: var(--sp-6);
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
