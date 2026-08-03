<script lang="ts">
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import KpiRow from '$lib/ui/KpiRow.svelte';
	import StatPair from '$lib/ui/StatPair.svelte';
	import { eur, eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const s = $derived(data.s);

	const active = $derived(s.fires.filter((f) => f.n_cases > 0));
	const fireApproved = $derived(active.reduce((x, f) => x + f.approved_eur, 0));
	// the FULL Σ includes cases whose acts cite no resolvable fire — shown,
	// never silently dropped
	const totApproved = $derived(fireApproved + s.unattributed.approved_eur);
	const totCases = $derived(active.reduce((x, f) => x + f.n_cases, 0));
	const totCompleted = $derived(active.reduce((x, f) => x + f.completed, 0));
	const pressTotal = $derived(
		s.fires.flatMap((f) => f.press.filter((p) => p.stream === 'proti_arogi')).reduce((x, p) => x + (p.eur ?? 0), 0)
	);
	const elgaTotal = $derived(s.elga.reduce((x, e) => x + (e.eur ?? 0), 0));
	const noProti = $derived(
		active.filter((f) => !f.press.some((p) => p.stream === 'proti_arogi'))
	);
	const topFire = $derived([...active].sort((a, b) => b.approved_eur - a.approved_eur)[0]);
	const maxApproved = $derived(Math.max(...active.map((f) => f.approved_eur), 1));
</script>

<svelte:head>
	<title>Αρωγή πυροπλήκτων — summary & cross-check</title>
	<meta name="description" content="State aid to wildfire victims (fires ≥2021): Διαύγεια acts vs official announcements, side by side." />
</svelte:head>

<hgroup class="lede">
	<h1>What the state promised the fire victims — on two sources</h1>
	<p class="standfirst">
		The per-building housing-aid trail from Διαύγεια, next to the state's own payment
		announcements. Different measures on different bases — printed side by side, never merged;
		mismatches and silences are the findings.
	</p>
</hgroup>

<KpiRow>
	<StatPair
		value={eurShort(totApproved)}
		label="στεγαστική συνδρομή approved"
		compare="{grInt(totCases + s.unattributed.n_cases)} aid cases · {eurShort(
			s.unattributed.approved_eur
		)} of it not attributable to one fire"
		basis="Σ of the acts' own Σ.Σ. figures (Διαύγεια)"
		color="var(--c-antinero)"
	/>
	<StatPair value={eurShort(pressTotal)} label="πρώτη αρωγή, officially announced" basis="latest cumulative totals per fire (press)" color="var(--c-antinero)" />
	<StatPair value={eurShort(elgaTotal)} label="ΕΛΓΑ fire compensation" basis="annual-report figures, per-year layer" />
	<StatPair value={grInt(totCompleted)} label="cases with a περαίωση act" compare="of {grInt(totCases)}" />
</KpiRow>

<ChartFrame
	title="{topFire?.label ?? '—'} dominates the housing-aid trail with {eurShort(topFire?.approved_eur ?? 0)} approved"
	subtitle="Σ.Σ. approved per fire (Διαύγεια acts) — one bar per fire unit."
	caveat="Acts attribute to the fire cited in their recitals; {grInt(s.stats['ambiguous'] ?? 0)} ambiguous and {grInt(s.stats['unmatched'] ?? 0)} citation-less acts are excluded from per-fire rows (counted, never guessed). Data as of {s.as_of ?? '—'}."
	anchor="per-fire"
	methodology="arogi"
>
	<div class="bars">
		{#each active as f (f.fire_id)}
			<div class="brow">
				<span class="blabel">{f.label}</span>
				<div class="bbar" style:width={`${(88 * f.approved_eur) / maxApproved}%`}></div>
				<span class="bval">{eurShort(f.approved_eur)} · {grInt(f.n_cases)} cases</span>
			</div>
		{/each}
		{#if s.unattributed.n_cases}
			<div class="brow unatt">
				<span class="blabel">— χωρίς αναγνώσιμη αναφορά πυρκαγιάς</span>
				<div class="bbar unatt" style:width={`${(88 * s.unattributed.approved_eur) / maxApproved}%`}></div>
				<span class="bval">{eurShort(s.unattributed.approved_eur)} · {grInt(s.unattributed.n_cases)} cases</span>
			</div>
		{/if}
	</div>
</ChartFrame>

<ChartFrame
	title="The cross-check: {grInt(noProti.length)} of {grInt(active.length)} fires with aid trails have no official πρώτη-αρωγή total"
	subtitle="Per fire: the Διαύγεια-derived figures next to the state's own announcements."
	caveat="Bases differ and are never merged: Σ.Σ. approved (Διαύγεια) ≠ πρώτη αρωγή paid (announcements) — a missing official total is itself a finding, and every shown figure links its verbatim source."
	anchor="crosscheck"
	methodology="arogi"
>
	<table class="listing">
		<thead>
			<tr><th>Fire</th><th class="num">Σ.Σ. approved (Διαύγεια)</th><th class="num">Official πρώτη αρωγή</th><th>Latest announcement</th></tr>
		</thead>
		<tbody>
			{#each active as f (f.fire_id)}
				{@const pa = f.press.find((p) => p.stream === 'proti_arogi')}
				<tr>
					<td>{f.label}</td>
					<td class="num">{eur(f.approved_eur)}</td>
					<td class="num" class:missing={!pa}>
						{#if pa}{pa.eur === null ? '—' : eur(pa.eur)}{#if !pa.cumulative}<br /><small class="muted">single batch — no running total published</small>{/if}{#if pa.beneficiaries}<br /><small class="muted">{grInt(pa.beneficiaries)} δικαιούχοι</small>{/if}
						{:else}<span class="chip bad">no official total</span>{/if}
					</td>
					<td class="muted">
						{#if pa}<small>{pa.date ?? ''} · <a href={pa.url} target="_blank" rel="noopener">source ↗</a><br />«{pa.quote.slice(0, 140)}…»</small>{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</ChartFrame>

<ChartFrame
	title="ΕΛΓΑ pays the farmers on its own clock"
	subtitle="Fire-related compensation lines from the annual ΕΛΓΑ activity reports."
	caveat="Per-year granularity only — the regular ΕΛΓΑ channel lags fires by years; every figure carries its report page and verbatim line."
	anchor="elga"
	methodology="arogi"
>
	<table class="listing">
		<thead><tr><th>Year</th><th class="num">€</th><th>Scope</th><th>Evidence</th></tr></thead>
		<tbody>
			{#each s.elga as e, i (i)}
				<tr>
					<td class="tabular">{e.year}</td>
					<td class="num">{e.eur === null ? '—' : eur(e.eur)}</td>
					<td class="muted"><small>{e.scope}</small></td>
					<td class="muted"><small><a href={e.report} target="_blank" rel="noopener">report{e.page ? ` p.${e.page}` : ''} ↗</a> «{e.quote.slice(0, 110)}…»</small></td>
				</tr>
			{/each}
		</tbody>
	</table>
</ChartFrame>

<style>
	.lede { max-width: var(--prose-w); }
	.standfirst { font-size: var(--fs-18); color: var(--ink-soft); }
	.bars { display: grid; gap: var(--sp-2); }
	.brow { display: grid; grid-template-columns: 16rem 1fr auto; gap: var(--sp-2); align-items: center; font-size: var(--fs-13); }
	.blabel { color: var(--ink-soft); }
	.bbar { height: 14px; background: var(--c-antinero); min-width: 2px; }
	.bbar.unatt { background: var(--ink-faint); }
	.brow.unatt .blabel { font-style: italic; }
	.bval { color: var(--ink-soft); white-space: nowrap; }
	.missing { background: color-mix(in srgb, var(--c-antinero) 8%, transparent); }
	.chip.bad { border-color: var(--c-antinero); color: var(--c-antinero); }
	.muted { color: var(--ink-soft); }
</style>
