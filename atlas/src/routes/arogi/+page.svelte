<script lang="ts">
	import { peEn } from '$lib/transforms/regions';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { eur, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.o);

	const ST_LABEL: Record<string, string> = {
		approved: 'εγκεκριμένη Σ.Σ.',
		in_progress: 'σε εξέλιξη (δόσεις)',
		completed: 'περαιωμένη',
		single_act: 'μεμονωμένη πράξη',
		budget: 'πράξη προϋπολογισμού'
	};
	const VMIN_OPTIONS = [
		{ value: '', label: 'Any value' },
		{ value: '10000', label: '≥ €10k' },
		{ value: '50000', label: '≥ €50k' },
		{ value: '100000', label: '≥ €100k' }
	];

	const params = $derived(page.url.searchParams);
	const fire = $derived(params.get('fire') ?? '');
	const st = $derived(params.get('st') ?? '');
	const att = $derived(params.get('att') ?? '');
	const from = $derived(params.get('from') ?? '');
	const to = $derived(params.get('to') ?? '');
	const vmin = $derived(params.get('vmin') ?? '');
	const sort = $derived(params.get('sort') ?? 'v_desc');

	function setParam(k: string, v: string | null) {
		const url = new URL(page.url);
		if (!v) url.searchParams.delete(k);
		else url.searchParams.set(k, v);
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	/** every active filter except `skip` — facet counts stay live */
	function passes(r: (typeof o.rows)[number], skip = ''): boolean {
		if (skip !== 'fire' && fire && r.fire_id !== fire) return false;
		if (skip !== 'st' && st && r.st !== st) return false;
		if (skip !== 'att' && att === 'yes' && !r.fire_id) return false;
		if (skip !== 'att' && att === 'no' && r.fire_id) return false;
		if (skip !== 'from' && from && (r.d ?? '') < from) return false;
		if (skip !== 'to' && to && (r.d ?? '') > to) return false;
		if (skip !== 'vmin' && vmin && (r.v ?? 0) < Number(vmin)) return false;
		return true;
	}

	const filtered = $derived.by(() => {
		const out = o.rows.filter((r) => passes(r));
		const dir = sort.endsWith('_asc') ? 1 : -1;
		if (sort.startsWith('v')) out.sort((a, b) => dir * ((a.v ?? -1) - (b.v ?? -1)));
		else out.sort((a, b) => dir * (a.d ?? '').localeCompare(b.d ?? ''));
		return out;
	});
	const totalShown = $derived(filtered.reduce((s, r) => s + (r.v ?? 0), 0));

	const stCounts = $derived.by(() => {
		const m = new Map<string, number>();
		for (const r of o.rows) if (passes(r, 'st')) m.set(r.st, (m.get(r.st) ?? 0) + 1);
		return m;
	});
	const attCounts = $derived.by(() => {
		let yes = 0;
		let no = 0;
		for (const r of o.rows) {
			if (!passes(r, 'att')) continue;
			if (r.fire_id) yes++;
			else no++;
		}
		return { yes, no };
	});

	let limit = $state(300);
	$effect(() => {
		void [fire, st, att, from, to, vmin, sort];
		limit = 300;
	});
	const anyFilter = $derived(!!fire || !!st || !!att || !!from || !!to || !!vmin);
	function resetAll() {
		const url = new URL(page.url);
		url.search = '';
		goto(url, { replaceState: true, noScroll: true });
	}
	function toggleSort(kind: 'd' | 'v') {
		setParam('sort', sort === `${kind}_desc` ? `${kind}_asc` : `${kind}_desc`);
	}
</script>

<svelte:head>
	<title>Αρωγή πυροπλήκτων — state aid cases, fires 2021+</title>
	<meta
		name="description"
		content="Every στεγαστική-συνδρομή act for the ≥2021 wildfires, extracted from Διαύγεια: {grInt(
			o.counts['cases'] ?? 0
		)} aid cases."
	/>
</svelte:head>

<hgroup>
	<h1>Αρωγή πυροπλήκτων: the per-building aid trail</h1>
	<p class="muted">
		{grInt(o.counts['cases'] ?? 0)} aid cases from the ΓΔΑΕΦΚ acts on Διαύγεια (repair
		permits, δόσεις, περαιώσεις), attributed to the fire each act cites. Amounts are the
		acts' own Σ.Σ. figures. Owners' names are never stored or shown — the signed PDF on
		Διαύγεια remains the public record. <a href="/arogi/summary">Summary & cross-check →</a>
		· <a href="/methodology#arogi">methodology</a>
	</p>
</hgroup>

<div class="filters">
	<div class="filter-row">
		<select value={st} onchange={(e) => setParam('st', e.currentTarget.value || null)}>
			<option value="">Any status</option>
			{#each [...stCounts.entries()] as [k, n] (k)}
				<option value={k}>{ST_LABEL[k] ?? k} ({grInt(n)})</option>
			{/each}
		</select>
		<select value={vmin} onchange={(e) => setParam('vmin', e.currentTarget.value || null)}>
			{#each VMIN_OPTIONS as v (v.value)}
				<option value={v.value}>{v.label}</option>
			{/each}
		</select>
		<select
			value={att}
			onchange={(e) => setParam('att', e.currentTarget.value || null)}
			title="Whether the acts' recitals cite an identifiable ≥2021 fire — unattributed cases have no readable fire citation or an ambiguous one"
		>
			<option value="">Fire attribution: any</option>
			<option value="yes">Located fire ({grInt(attCounts.yes)})</option>
			<option value="no">Unattributed ({grInt(attCounts.no)})</option>
		</select>
	</div>
	<div class="filter-row">
		<label
			>Fire
			<select value={fire} onchange={(e) => setParam('fire', e.currentTarget.value || null)}>
				<option value="">All fires</option>
				{#each o.fires as f (f.fire_id)}
					<option value={f.fire_id}>{f.label}</option>
				{/each}
			</select>
		</label>
		<label
			>From
			<input type="date" value={from} onchange={(e) => setParam('from', e.currentTarget.value || null)} />
		</label>
		<label
			>To
			<input type="date" value={to} onchange={(e) => setParam('to', e.currentTarget.value || null)} />
		</label>
		{#if anyFilter}
			<button class="reset" onclick={resetAll}>× Reset filters</button>
		{/if}
	</div>
</div>

<p class="count muted">
	<strong>{grInt(filtered.length)}</strong> of {grInt(o.rows.length)} cases · shown Σ.Σ. Σ
	{eur(totalShown)} <small>(approved amounts, as stated in the acts)</small>
</p>

<table class="listing">
	<thead>
		<tr>
			<th><button class="sort" onclick={() => toggleSort('d')}>First act {sort === 'd_desc' ? '↓' : sort === 'd_asc' ? '↑' : ''}</button></th>
			<th>Fire</th>
			<th>R.U.</th>
			<th>Acts</th>
			<th>Status</th>
			<th class="num"><button class="sort" onclick={() => toggleSort('v')}>Σ.Σ. approved {sort === 'v_desc' ? '↓' : sort === 'v_asc' ? '↑' : ''}</button></th>
		</tr>
	</thead>
	<tbody>
		{#each filtered.slice(0, limit) as r (r.id)}
			<tr>
				<td class="tabular muted">{r.d ?? '—'}{#if r.d2 && r.d2 !== r.d}<span class="muted"> → {r.d2}</span>{/if}</td>
				<td><a href={`/arogi/case/${encodeURIComponent(r.id)}`}>{r.fire ?? '— unattributed'}</a></td>
				<td class="muted"><small>{r.pe ? peEn(r.pe) : '—'}</small></td>
				<td class="num">{r.n}</td>
				<td><span class="chip" class:ok={r.st === 'completed'}>{ST_LABEL[r.st] ?? r.st}</span></td>
				<td class="num">{r.v === null ? '—' : eur(r.v)}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if filtered.length > limit}
	<button class="btn-more" onclick={() => (limit += 500)}>Show more ({grInt(filtered.length - limit)} remaining)</button>
{/if}

<style>
	.filters {
		margin: var(--sp-4) 0 var(--sp-3);
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
	}
	.filter-row {
		display: flex;
		flex-wrap: wrap;
		gap: var(--sp-2);
		align-items: end;
	}
	.filter-row label {
		display: flex;
		flex-direction: column;
		gap: 2px;
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	select,
	input[type='date'] {
		font: inherit;
		font-size: var(--fs-13);
		padding: var(--sp-1) var(--sp-2);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: var(--paper);
		max-width: 240px;
	}
	.reset {
		font: inherit;
		font-size: var(--fs-13);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: var(--paper);
		padding: var(--sp-1) var(--sp-2);
		cursor: pointer;
	}
	.count {
		margin: var(--sp-2) 0;
	}
	.sort {
		font: inherit;
		font-weight: 600;
		border: 0;
		background: none;
		padding: 0;
		cursor: pointer;
	}
	.chip.ok {
		background: var(--c-anadohoi);
		color: #fff;
		border-color: var(--c-anadohoi);
	}
	.btn-more {
		margin: var(--sp-4) 0;
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
