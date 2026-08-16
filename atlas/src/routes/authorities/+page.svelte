<script lang="ts">
	import { authEn, devGreek } from '$lib/transforms/names';
	import { peEn } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { spreadOverlaps } from '$lib/maps/useGeo';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const rows = $derived(data.rows);
	const both = $derived(rows.filter((r) => r.antinero_n && r.dase_n));

	const dots = $derived(
		spreadOverlaps(
			rows
				.filter((r) => r.lat && r.lon)
				.map((r) => ({ ...r, lat: r.lat!, lon: r.lon! })),
			0.02
		)
	);
</script>

<svelte:head>
	<title>Forest authorities — both money pipelines meet here</title>
	<meta
		name="description"
		content="All {rows.length} Greek forest authorities (Διευθύνσεις Δασών, Δασαρχεία) with their Anti-nero works and ΔΑΣΕ co-op contracts."
	/>
</svelte:head>

<hgroup class="lede">
	<h1>The forest authorities — where the two pipelines meet</h1>
	<p class="standfirst">
		Δασαρχεία and Διευθύνσεις Δασών appear on both sides of the ledger: Anti-nero contractors
		execute works on their territory, and they award day-to-day contracts to forest co-ops.
		{grInt(both.length)} of the {grInt(rows.length)} do both.
	</p>
</hgroup>

<KpiRow>
	<StatPair value={grInt(rows.length)} label="forest authorities" compare="{grInt(rows.filter((r) => r.kind === 'dx').length)} Δασαρχεία + {grInt(
			rows.filter((r) => r.kind === 'dd').length
		)} Διευθύνσεις Δασών" />
	<StatPair
		value={grInt(rows.filter((r) => r.antinero_n).length)}
		label="host Anti-nero works"
		color="var(--c-antinero)"
	/>
	<StatPair
		value={grInt(rows.filter((r) => r.dase_n).length)}
		label="award ΔΑΣΕ contracts"
		color="var(--c-dase)"
	/>
	<StatPair value={grInt(both.length)} label="do both" />
</KpiRow>

<div class="map-holder">
	<PaperMap
		interactive={false}
		tipOf={(pe) => `<strong>${pe}</strong>`}
	>
		{#snippet overlay(ctx)}
			<DotLayer
				{ctx}
				points={dots}
				r={4}
				fillOf={(p) =>
					p.antinero_n && p.dase_n
						? 'var(--ink)'
						: p.antinero_n
							? 'var(--c-antinero)'
							: p.dase_n
								? 'var(--c-dase)'
								: 'var(--ink-faint)'}
				tipOf={(p) =>
					`<strong>${p.name}</strong><br>` +
					`Anti-nero: ${p.antinero_n ? `${p.antinero_n} contracts · ${eurShort(p.antinero_eur as number)}` : '—'}<br>` +
					`ΔΑΣΕ: ${p.dase_n ? `${p.dase_n} contracts · ${eurShort(p.dase_eur as number)}` : '—'}`}
				hrefOf={(p) => `/authority/${p.slug}`}
			/>
		{/snippet}
		{#snippet legend()}
			<div><i class="dot" style="background:var(--ink)"></i> both datasets</div>
			<div><i class="dot" style="background:var(--c-antinero)"></i> Anti-nero works only</div>
			<div><i class="dot" style="background:var(--c-dase)"></i> ΔΑΣΕ awards only</div>
			<div><i class="dot" style="background:var(--ink-faint)"></i> neither</div>
		{/snippet}
	</PaperMap>
</div>

<table class="listing">
	<thead>
		<tr>
			<th>Authority</th>
			<th>R.U.</th>
			<th class="num">Anti-nero works</th>
			<th class="num">ΔΑΣΕ awards</th>
		</tr>
	</thead>
	<tbody>
		{#each rows as r (r.slug)}
			<tr>
				<td>
					<a href={`/authority/${r.slug}`} title={devGreek(r.name)}>{authEn(r.name)}</a>
					<span class="chip">{r.kind === 'dx' ? 'Δασαρχείο' : 'Δ. Δασών'}</span>
				</td>
				<td class="muted"><small>{peEn(r.pe)}</small></td>
				<td class="num">
					{#if r.antinero_n}{r.antinero_n} · {eurShort(r.antinero_eur)}{:else}<span class="faint">—</span>{/if}
				</td>
				<td class="num">
					{#if r.dase_n}{r.dase_n} · {eurShort(r.dase_eur)}{:else}<span class="faint">—</span>{/if}
				</td>
			</tr>
		{/each}
	</tbody>
</table>
<p class="muted">
	<small>
		Anti-nero € even-split across a contract's authorities; ΔΑΣΕ side matched from the awarding
		unit's name. <a href="/methodology#authorities">Methodology</a>.
	</small>
</p>

<style>
	.lede {
		max-width: var(--prose-w);
	}
	.standfirst {
		font-size: var(--fs-18);
		color: var(--ink-soft);
	}
	.map-holder {
		max-width: 40rem;
		margin-bottom: var(--sp-6);
	}
	.listing td a {
		text-decoration: none;
	}
	.listing td a:hover {
		text-decoration: underline;
	}
	.muted {
		color: var(--ink-soft);
	}
	.faint {
		color: var(--ink-faint);
	}
	i.dot {
		display: inline-block;
		width: 0.6rem;
		height: 0.6rem;
		border-radius: 50%;
		margin-right: 4px;
	}
</style>
