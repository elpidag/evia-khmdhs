<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { apiGetCached, type ExplorePayload, type ExploreRow } from '$lib/api';
	import { eur, grInt } from '$lib/transforms/format';
	import { matches, phoneticFold, searchNorm } from '$lib/transforms/search';
	import SegmentToggle from '$lib/ui/SegmentToggle.svelte';

	const DS_LABEL: Record<string, string> = {
		antinero: 'Anti-nero',
		dase: 'ΔΑΣΕ',
		anadohoi: 'Ανάδοχοι'
	};
	const PROC_LABEL: Record<string, string> = {
		direct: 'Απευθείας ανάθεση',
		open: 'Ανοικτή διαδικασία',
		nego: 'Διαπραγμάτευση',
		other: 'Άλλη διαδικασία',
		sponsor: 'Πράξη αναδόχου (χορηγία)'
	};
	const ST_LABEL: Record<string, string> = {
		completed: 'completed',
		active: 'active',
		no_completion_recorded: 'no completion recorded',
		revoked: 'revoked',
		superseded: 'superseded',
		cancelled: 'cancelled'
	};
	const VMIN_OPTIONS = [
		{ value: '', label: 'Any value' },
		{ value: '10000', label: '≥ €10k' },
		{ value: '100000', label: '≥ €100k' },
		{ value: '1000000', label: '≥ €1M' },
		{ value: '10000000', label: '≥ €10M' }
	];

	interface Indexed {
		r: ExploreRow;
		hn: string;
		hf: string;
	}

	let payload: ExplorePayload | null = $state.raw(null);
	let indexed: Indexed[] = $state.raw([]);
	$effect(() => {
		// ?v= busts HTTP + module caches when the payload shape changes
		apiGetCached<ExplorePayload>(fetch, '/api/explore?v=4').then((p) => {
			payload = p;
			indexed = p.rows.map((r) => {
				const hn = searchNorm(
					`${r.ref} ${r.t} ${r.co} ${r.pe.join(' ')} ${r.hq.join(' ')}`
				);
				return { r, hn, hf: phoneticFold(hn) };
			});
		});
	});

	const params = $derived(page.url.searchParams);
	const ds = $derived(params.get('ds') ?? 'all');
	const pe = $derived(params.get('pe') ?? '');
	const hq = $derived(params.get('hq') ?? '');
	const proc = $derived(params.get('proc') ?? 'all');
	const st = $derived(params.get('st') ?? '');
	const from = $derived(params.get('from') ?? '');
	const to = $derived(params.get('to') ?? '');
	const vmin = $derived(params.get('vmin') ?? '');
	const prf = $derived(params.get('prf') ?? '');
	const q = $derived(params.get('q') ?? '');
	const sort = $derived(params.get('sort') ?? 'd_desc');

	function setParam(k: string, v: string | null) {
		const url = new URL(page.url);
		if (!v) url.searchParams.delete(k);
		else url.searchParams.set(k, v);
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	let qInput = $state(page.url.searchParams.get('q') ?? '');
	let qTimer: ReturnType<typeof setTimeout> | undefined;
	function onSearch() {
		clearTimeout(qTimer);
		qTimer = setTimeout(() => setParam('q', qInput.trim() || null), 150);
	}

	const qNorm = $derived(searchNorm(q));
	const qFold = $derived(phoneticFold(qNorm));

	const filtered = $derived.by(() => {
		const min = vmin ? Number(vmin) : null;
		const out: ExploreRow[] = [];
		for (const { r, hn, hf } of indexed) {
			if (ds !== 'all' && r.ds !== ds) continue;
			if (pe && !r.pe.includes(pe)) continue;
			if (hq && !r.hq.includes(hq)) continue;
			if (proc !== 'all' && r.proc !== proc) continue;
			if (st && r.st !== st) continue;
			if (from && (!r.d || r.d < from)) continue;
			if (to && (!r.d || r.d > to)) continue;
			if (min !== null && (r.v === null || r.v < min)) continue;
			if (prf === 'yes' && r.pr !== 1) continue;
			if (prf === 'no' && r.pr !== 0) continue;
			if (qNorm && !(hn.includes(qNorm) || hf.includes(qFold))) continue;
			out.push(r);
		}
		const dir = sort.endsWith('_asc') ? 1 : -1;
		if (sort.startsWith('v') || sort.startsWith('n')) {
			const key: 'v' | 'vn' = sort.startsWith('n') ? 'vn' : 'v';
			out.sort((a, b) => {
				const av = a[key];
				const bv = b[key];
				if (av === null && bv === null) return 0;
				if (av === null) return 1;
				if (bv === null) return -1;
				return dir * (av - bv);
			});
		} else {
			out.sort((a, b) => {
				const ad = a.d ?? '';
				const bd = b.d ?? '';
				if (!ad && !bd) return 0;
				if (!ad) return 1;
				if (!bd) return -1;
				return dir * ad.localeCompare(bd);
			});
		}
		return out;
	});

	const totalShown = $derived(
		filtered.reduce((s, r) => s + (r.v ?? 0), 0)
	);

	const peOptions = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const { r } of indexed)
			for (const p of r.pe) counts.set(p, (counts.get(p) ?? 0) + 1);
		return [...counts.entries()].sort((a, b) => b[1] - a[1]);
	});
	const hqOptions = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const { r } of indexed)
			for (const p of r.hq) counts.set(p, (counts.get(p) ?? 0) + 1);
		return [...counts.entries()].sort((a, b) => b[1] - a[1]);
	});
	const prCounts = $derived.by(() => {
		let yes = 0;
		let no = 0;
		for (const { r } of indexed) {
			if (r.pr === 1) yes++;
			else if (r.pr === 0) no++;
		}
		return { yes, no };
	});

	let limit = $state(300);
	const filterKey = $derived(
		[ds, pe, hq, proc, st, from, to, vmin, prf, q, sort].join('§')
	);
	$effect(() => {
		void filterKey;
		limit = 300;
	});
	const shown = $derived(filtered.slice(0, limit));

	const anyFilter = $derived(
		ds !== 'all' || !!pe || !!hq || proc !== 'all' || !!st || !!from ||
		!!to || !!vmin || !!prf || !!q
	);
	function resetAll() {
		const url = new URL(page.url);
		url.search = '';
		qInput = '';
		goto(url, { replaceState: true, noScroll: true });
	}

	function detailHref(r: ExploreRow): string {
		if (r.ds === 'antinero') return `/antinero/contract/${r.ref}`;
		if (r.ds === 'dase') return `/dase/contract/${r.ref}`;
		return `/anadohoi/project/${r.ref}`;
	}
	function toggleSort(kind: 'd' | 'v' | 'n') {
		const next =
			sort === `${kind}_desc` ? `${kind}_asc` : `${kind}_desc`;
		setParam('sort', next === 'd_desc' ? null : next);
	}
</script>

<svelte:head>
	<title>Explore — all three datasets</title>
	<meta
		name="description"
		content="One searchable table over Anti-nero contracts, ΔΑΣΕ co-op contracts and Ανάδοχοι sponsor projects."
	/>
</svelte:head>

<hgroup>
	<h1>Explore the three datasets</h1>
	<p class="muted">
		{#if payload}
			{grInt(payload.counts['antinero'] ?? 0)} Anti-nero contracts ·
			{grInt(payload.counts['dase'] ?? 0)} ΔΑΣΕ contracts ·
			{grInt(payload.counts['anadohoi'] ?? 0)} sponsor projects.
		{:else}
			Loading the combined table…
		{/if}
		Search is accent-, homoglyph- and Greeklish-tolerant (“evias” finds Ευβοίας).
	</p>
</hgroup>

<div class="filters">
	<input
		class="search"
		type="search"
		placeholder="Search ΑΔΑΜ/ΑΔΑ, title, company, region…"
		bind:value={qInput}
		oninput={onSearch}
	/>
	<div class="filter-row">
		<SegmentToggle
			param="ds"
			fallback="all"
			options={[
				{ value: 'all', label: 'All' },
				{ value: 'antinero', label: 'Anti-nero' },
				{ value: 'dase', label: 'ΔΑΣΕ' },
				{ value: 'anadohoi', label: 'Ανάδοχοι' }
			]}
		/>
		<select value={proc} onchange={(e) => setParam('proc', e.currentTarget.value === 'all' ? null : e.currentTarget.value)}>
			<option value="all">Any procedure</option>
			{#each Object.entries(PROC_LABEL) as [v, l] (v)}
				<option value={v}>{l}</option>
			{/each}
		</select>
		<select value={st} onchange={(e) => setParam('st', e.currentTarget.value || null)}>
			<option value="">Any status</option>
			{#each Object.entries(ST_LABEL) as [v, l] (v)}
				<option value={v}>{l}</option>
			{/each}
		</select>
		<select value={vmin} onchange={(e) => setParam('vmin', e.currentTarget.value || null)}>
			{#each VMIN_OPTIONS as o (o.value)}
				<option value={o.value}>{o.label}</option>
			{/each}
		</select>
		<select
			value={prf}
			onchange={(e) => setParam('prf', e.currentTarget.value || null)}
			title="Whether ΚΗΜΔΗΣ links a διακήρυξη/πρόσκληση (PROC) to the contract — Anti-nero only"
		>
			<option value="">Διακήρυξη: any</option>
			<option value="yes">With διακήρυξη (PROC) ({grInt(prCounts.yes)})</option>
			<option value="no">Without διακήρυξη ({grInt(prCounts.no)})</option>
		</select>
	</div>
	<div class="filter-row">
		<label
			>Work region
			<select value={pe} onchange={(e) => setParam('pe', e.currentTarget.value || null)}>
				<option value="">All of Greece</option>
				{#each peOptions as [p, n] (p)}
					<option value={p}>{p} ({grInt(n)})</option>
				{/each}
			</select>
		</label>
		<label
			>HQ region <small class="muted">(Anti-nero)</small>
			<select value={hq} onchange={(e) => setParam('hq', e.currentTarget.value || null)}>
				<option value="">Any</option>
				{#each hqOptions as [p, n] (p)}
					<option value={p}>{p} ({grInt(n)})</option>
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

{#if payload}
	<p class="count muted">
		<strong>{grInt(filtered.length)}</strong> of {grInt(payload.rows.length)} rows match
		· shown value Σ {eur(totalShown)}
		<small
			>(value bases differ: Anti-nero = effective €, ΔΑΣΕ = stated €, Ανάδοχοι = stated
			budget where the act declares one — <a href="/methodology#explore">methodology</a>)</small
		>
	</p>

	<table class="listing">
		<thead>
			<tr>
				<th
					><button class="sort" onclick={() => toggleSort('d')}
						>Date {sort === 'd_desc' ? '↓' : sort === 'd_asc' ? '↑' : ''}</button
					></th
				>
				<th>Dataset</th>
				<th>Contract / project</th>
				<th>Company</th>
				<th>Regions</th>
				<th class="num"
					><button class="sort" onclick={() => toggleSort('n')}
						>Stated excl. VAT {sort === 'n_desc' ? '↓' : sort === 'n_asc' ? '↑' : ''}</button
					></th
				>
				<th class="num"
					><button class="sort" onclick={() => toggleSort('v')}
						>Value {sort === 'v_desc' ? '↓' : sort === 'v_asc' ? '↑' : ''}</button
					></th
				>
			</tr>
		</thead>
		<tbody>
			{#each shown as r (r.ds + r.ref)}
				<tr class:cancelled={r.st === 'cancelled' || r.st === 'revoked'}>
					<td class="tabular muted">{r.d ?? '—'}</td>
					<td><span class="ds ds-{r.ds}">{DS_LABEL[r.ds]}</span></td>
					<td>
						<a href={detailHref(r)}>{r.t || r.ref}</a>
						{#if r.b1 === 1}<span class="chip warn">1 bid</span>{/if}
						{#if r.st && r.st !== 'active'}<span
								class="chip"
								class:bad={r.st === 'cancelled' || r.st === 'revoked' || r.st === 'no_completion_recorded'}
								>{ST_LABEL[r.st] ?? r.st}</span
							>{/if}
					</td>
					<td class="muted"><small>{r.co || '—'}</small></td>
					<td class="muted"><small>{r.pe.join(', ') || '—'}</small></td>
					<td class="num muted"><small>{r.vn === null ? '—' : eur(r.vn)}</small></td>
					<td class="num">{r.v === null ? '—' : eur(r.v)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
	{#if filtered.length > limit}
		<button class="btn-more" onclick={() => (limit += 500)}>
			Show more ({grInt(filtered.length - limit)} remaining)
		</button>
	{/if}
	{#if !filtered.length}
		<p class="muted">Nothing matches these filters.</p>
	{/if}
{:else}
	<div class="skeleton" style="height: 420px"></div>
{/if}

<style>
	.filters {
		margin: var(--sp-4) 0 var(--sp-3);
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
	}
	.search {
		font: inherit;
		width: 100%;
		max-width: 560px;
		padding: var(--sp-2) var(--sp-3);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: var(--paper);
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
	.ds {
		font-size: var(--fs-12);
		font-weight: 600;
		padding: 1px 6px;
		border-radius: var(--radius);
		color: #fff;
		white-space: nowrap;
	}
	.ds-antinero {
		background: var(--c-antinero);
	}
	.ds-dase {
		background: var(--c-dase);
	}
	.ds-anadohoi {
		background: var(--c-anadohoi);
	}
	tr.cancelled {
		opacity: 0.55;
	}
	td a {
		text-decoration: none;
	}
	td a:hover {
		text-decoration: underline;
	}
	.muted {
		color: var(--ink-soft);
	}
</style>
