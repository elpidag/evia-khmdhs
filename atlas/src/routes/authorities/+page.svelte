<script lang="ts">
	/**
	 * NETWORK OF ACTORS — the forest-service network beside the people it
	 * pays and supervises, on ONE map with a mode switch. Redressed to the
	 * dataset pages' typography 2026-08-25; trimmed 2026-08-26 (user): no
	 * hero, no KPI row — the map opens the page; the listing below follows
	 * the map's mode, carries a search, and covers all three populations
	 * (the ΥΠΕΝ directory units with no contracts fold into the
	 * authorities list — address/contact columns dropped).
	 */
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { authEn, bodyEn, devGreek } from '$lib/transforms/names';
	import { peEn, ruLabel } from '$lib/transforms/regions';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { spreadOverlaps } from '$lib/maps/useGeo';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import { eurShort, grInt } from '$lib/transforms/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const rows = $derived(data.rows);
	const otherUnits = $derived(data.otherUnits);
	const both = $derived(rows.filter((r) => r.antinero_n && r.dase_n));

	// ---- the map's three dot populations --------------------------------
	const dots = $derived(
		spreadOverlaps(
			rows.filter((r) => r.lat && r.lon).map((r) => ({ ...r, lat: r.lat!, lon: r.lon! })),
			0.02
		)
	);
	const otherDots = $derived(
		spreadOverlaps(
			otherUnits.filter((u) => u.lat && u.lon).map((u) => ({ ...u, lat: u.lat!, lon: u.lon! })),
			0.02
		)
	);
	const coopDots = $derived(spreadOverlaps([...data.coops], 0.012));
	const conDots = $derived(spreadOverlaps([...data.contractors], 0.012));

	// ---- the mode switch (?show=) ---------------------------------------
	const MODES = [
		{ value: 'authorities', label: 'Forest authorities' },
		{ value: 'coops', label: 'Forest co-ops' },
		{ value: 'contractors', label: 'Anti-nero contractors' },
		{ value: 'all', label: 'All' }
	] as const;
	type Mode = (typeof MODES)[number]['value'];
	const show = $derived<Mode>(
		(MODES.find((m) => m.value === page.url.searchParams.get('show'))?.value as Mode) ??
			'authorities'
	);
	function setShow(next: Mode) {
		const url = new URL(page.url);
		if (next === 'authorities') url.searchParams.delete('show');
		else url.searchParams.set('show', next);
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	// two-way hover between the map dots and the side list (user,
	// 2026-08-25: the map is the page's key element, the list beside it
	// serves whichever network it shows)
	let hovKey = $state<string | null>(null);
	const keyOf = (kind: string, p: Record<string, unknown>) =>
		`${kind}:${p.slug ?? p.vat}`;

	/** rendered map height — the side panel matches it exactly (user) */
	let mapHeight = $state(0);

	// the authority dot wears the authorities' own tone; the green core
	// (a second inert layer) marks the ones that ALSO award ΔΑΣΕ
	// contracts — no authority awards ΔΑΣΕ without hosting Anti-nero
	// works (measured 0), and the no-contract ones render pale
	const authFill = (p: Record<string, unknown>) =>
		p.antinero_n || p.dase_n ? AUTH_TONE : '#a6a6a6';
	/** THE forest-authorities colour, every lens (user, 2026-08-26: black
	 *  in one lens and contractors-black in the next confused the toggle);
	 *  the /dase map's forest-directorate green */
	const AUTH_TONE = '#406e55';
	/** the crew map's frame (THE FOREST CO-OPS THE SPONSORS ENGAGED) —
	 *  the user wants this map at the same zoom and extents */
	const MAP_VIEW = { center: [23.8305, 38.3566] as [number, number], k: 1.08 };

	const authTip = (p: Record<string, unknown>) =>
		`<strong>${authEn(String(p.name))}</strong><br>` +
		`Anti-nero: ${p.antinero_n ? `${grInt(p.antinero_n as number)} contracts · ${eurShort(p.antinero_eur as number)}` : '—'}<br>` +
		`ΔΑΣΕ awards: ${p.dase_n ? `${grInt(p.dase_n as number)} contracts · ${eurShort(p.dase_eur as number)}` : '—'}`;
	const coopTip = (p: Record<string, unknown>) =>
		`<strong>${p.name}</strong><br>${p.place ? `${p.place} · ` : ''}${grInt(p.n_contracts as number)} contracts · ${eurShort(p.total_eur as number)}`;
	const conTip = (p: Record<string, unknown>) =>
		`<strong>${p.name}</strong><br>${grInt(p.n_contracts as number)} contracts · ${eurShort(p.total_eur as number)}`;

	// ---- the ONE list frame below the map: a toggle between the three
	// populations (user, 2026-08-26 — stacked frames were the earlier
	// answer, a toggle reads better), its own search, 25-row pages
	type ListShow = 'authorities' | 'coops' | 'contractors';
	let listShow = $state<ListShow>('authorities');
	let q = $state('');
	const fold = (s: string) =>
		s
			.normalize('NFD')
			.replace(/[̀-ͯ]/g, '')
			.toUpperCase();
	const hits = (needle: string, ...hay: (string | null | undefined)[]) =>
		!needle.trim() || hay.some((h) => h && fold(h).includes(fold(needle)));

	const authList = $derived(rows.filter((r) => hits(q, authEn(r.name), r.name)));
	/** ΥΠΕΝ directory units with no contracts, folded into the same list */
	const unitList = $derived(otherUnits.filter((u) => hits(q, bodyEn(u.name), u.name)));
	const coopList = $derived(data.coops.filter((c) => hits(q, c.name, c.name_en ?? undefined)));
	const conList = $derived(data.contractors.filter((c) => hits(q, c.name, c.registry_name)));
	const PAGE = 25;
	let pa = $state(0);
	let pk = $state(0);
	let pc = $state(0);
	$effect(() => {
		void q;
		void listShow;
		pa = 0;
		pk = 0;
		pc = 0;
	});
	const LIST_TITLES: Record<ListShow, string> = {
		authorities: 'FOREST AUTHORITIES',
		coops: 'FOREST CO-OPS',
		contractors: 'ANTI-NERO CONTRACTORS'
	};
	const LIST_CAVEATS: Record<ListShow, string> = {
		authorities:
			'Anti-nero € even-split across a contract’s authorities; the ΔΑΣΕ side matched from the awarding unit’s name. Units with no contracts in either dataset come from the ministry’s own directory.',
		coops: 'Stated net €, a jointly signed contract split evenly between its co-operatives.',
		contractors:
			"Stated net €, a jointly signed contract split evenly between its parties; names as each contractor's own documents write them."
	};
	/** windowed page numbers: 1 … cur-1 cur cur+1 … last */
	function pagesOf(total: number, cur: number): (number | '…')[] {
		const last = Math.max(1, Math.ceil(total / PAGE));
		if (last <= 7) return Array.from({ length: last }, (_, i) => i);
		const want = new Set([0, last - 1, cur - 1, cur, cur + 1]);
		const out: (number | '…')[] = [];
		for (let i = 0; i < last; i++) {
			if (want.has(i)) out.push(i);
			else if (out[out.length - 1] !== '…') out.push('…');
		}
		return out;
	}
	/** the authorities table = registry rows then the no-contract
	 *  directory units, paginated as ONE sequence */
	const authAll = $derived([
		...authList.map((r) => ({ kind: 'auth' as const, r })),
		...unitList.map((u) => ({ kind: 'unit' as const, u }))
	]);
	const authPageRows = $derived(authAll.slice(pa * PAGE, (pa + 1) * PAGE));
	const coopPageRows = $derived(coopList.slice(pk * PAGE, (pk + 1) * PAGE));
	const conPageRows = $derived(conList.slice(pc * PAGE, (pc + 1) * PAGE));

</script>

<svelte:head>
	<title>Network of actors — forest authorities, co-ops, contractors</title>
	<meta
		name="description"
		content="Greece's forest authorities, forest workers' co-operatives and Anti-nero contractors — one map, three networks."
	/>
</svelte:head>

<div class="authp">
	<ChartFrame
		title="NETWORK OF ACTORS"
		insight={`${grInt(both.length)} of the ${grInt(rows.length)} forest authorities both host Anti-nero works and award co-op contracts; ${grInt(data.coops.length)} co-operatives and ${grInt(data.contractors.length)} Anti-nero contractors are placed at the registered office their own documents state.`}
		caveat="Every € stated net of VAT; the Anti-nero € of a contract covering several authorities is split evenly between them, and the co-op side is matched from the awarding unit's name. Authority seats from the ΥΠΕΝ contact tables corroborated by each service's own letterheads; co-op and contractor offices from their own documents."
		anchor="map"
		methodology="authorities"
	>
		{#snippet controls()}
			<div class="mode" role="group" aria-label="Which dots the map shows">
				{#each MODES as m (m.value)}
					<button type="button" class:active={show === m.value} onclick={() => setShow(m.value)}
						>{m.label}</button
					>
				{/each}
			</div>
		{/snippet}

		<div class="maprow">
			<div class="map-holder" bind:clientHeight={mapHeight}>
				<PaperMap
					width={640}
					height={620}
					view={MAP_VIEW}
					tipOf={(pe) => `<strong>${ruLabel(pe)}</strong>`}
				>
					{#snippet overlay(ctx)}
						{#if show === 'authorities'}
							<!-- the rest of the ΥΠΕΝ network: pale dots like the
							     no-contract registry authorities (one category) -->
							{#each otherDots as u (u.inspectorate + u.name)}
								{@const xy = ctx.projection([u.lon, u.lat])}
								{#if xy}
									<circle
										cx={xy[0]}
										cy={xy[1]}
										r={3.4 / ctx.k}
										class="nodot"
										role="img"
										aria-label={bodyEn(u.name)}
										onmouseenter={() =>
											ctx.showTip(
												`<strong>${bodyEn(u.name)}</strong><br>no contracts recorded in either dataset`
											)}
										onmouseleave={() => ctx.hideTip()}
									/>
								{/if}
							{/each}
							<DotLayer
								{ctx}
								points={dots}
								r={4.2}
								stroke="none"
								fillOf={authFill}
								tipOf={authTip}
								hrefOf={(p) => `/authority/${p.slug}`}
								hotOf={(p) => keyOf('a', p) === hovKey}
								onOver={(p) => (hovKey = keyOf('a', p))}
								onOut={() => (hovKey = null)}
							/>
							<!-- the green core marks the authorities present in BOTH -->
							<DotLayer
								{ctx}
								points={dots.filter((p) => p.antinero_n && p.dase_n)}
								r={2}
								stroke="none"
								fillOf={() => 'var(--c-dase)'}
								inert
							/>
						{:else if show === 'coops'}
							<DotLayer
								{ctx}
								points={coopDots}
								r={3}
								stroke="none"
								fillOf={() => 'var(--c-dase)'}
								tipOf={coopTip}
								hrefOf={(p) => `/dase/coop/${p.vat}`}
								hotOf={(p) => keyOf('k', p) === hovKey}
								onOver={(p) => (hovKey = keyOf('k', p))}
								onOut={() => (hovKey = null)}
							/>
						{:else if show === 'contractors'}
							<DotLayer
								{ctx}
								points={conDots}
								r={3.4}
								stroke="none"
								fillOf={() => 'var(--ink)'}
								tipOf={conTip}
								hrefOf={(p) => `/antinero/contractor/${p.vat}`}
								hotOf={(p) => keyOf('c', p) === hovKey}
								onOver={(p) => (hovKey = keyOf('c', p))}
								onOut={() => (hovKey = null)}
							/>
						{:else}
							<DotLayer
								{ctx}
								points={dots}
								r={4.2}
								stroke="none"
								fillOf={() => AUTH_TONE}
								tipOf={authTip}
								hrefOf={(p) => `/authority/${p.slug}`}
							/>
							<DotLayer
								{ctx}
								points={coopDots}
								r={2.6}
								stroke="none"
								fillOf={() => 'var(--c-dase)'}
								tipOf={coopTip}
								hrefOf={(p) => `/dase/coop/${p.vat}`}
							/>
							<DotLayer
								{ctx}
								points={conDots}
								r={3.2}
								stroke="none"
								fillOf={() => 'var(--ink)'}
								tipOf={conTip}
								hrefOf={(p) => `/antinero/contractor/${p.vat}`}
							/>
						{/if}
					{/snippet}
				</PaperMap>
			</div>
			<aside class="side" style:height={mapHeight ? `${mapHeight}px` : undefined}>
				<!-- the legend docks at the top of the right column, its grey
				     fill flush with the map's upper hairline (user, 2026-08-26);
				     one full sentence per line, never chip-speak -->
				<ul class="mapkey">
					{#if show === 'authorities'}
						<!-- the user's wording (2026-08-26) -->
						<li>
							<i class="dot" style:background={AUTH_TONE}></i>
							responsible for supervision of Anti-nero works in its territory
						</li>
						<li>
							<i class="dot both"></i>
							responsible for supervision of Anti-nero works and contracts awarded to
							forest workers' co-operatives in its territory
						</li>
						<li>
							<i class="dot" style:background="#a6a6a6"></i>
							no contracts recorded in its territory within this research
						</li>
					{:else if show === 'coops'}
						<li>
							<i class="dot" style:background="var(--c-dase)"></i>
							registered base for forest workers' co-operatives ({grInt(
								coopDots.length
							)} found within this research; the official registry of the Ministry of
							Environment is not openly accessible)
						</li>
					{:else if show === 'contractors'}
						<li>
							<i class="dot" style:background="var(--ink)"></i>
							registered offices for contractors of the Anti-nero works ({grInt(
								conDots.length
							)})
						</li>
					{:else}
						<li>
							<i class="dot" style:background={AUTH_TONE}></i>
							forest authority seats ({grInt(rows.length)})
						</li>
						<li>
							<i class="dot" style:background="var(--c-dase)"></i>
							registered base for forest workers' co-operatives ({grInt(
								data.coops.length
							)} found within this research; the official registry of the Ministry of
							Environment is not openly accessible)
						</li>
						<li>
							<i class="dot" style:background="var(--ink)"></i>
							registered offices for contractors of the Anti-nero works ({grInt(
								data.contractors.length
							)})
						</li>
					{/if}
				</ul>
				{#if show === 'authorities'}
					<div class="sidehead">Forest authorities <small>contracts · €</small></div>
					<div class="cols">
						<span class="nm"></span>
						<span class="vals">
							<span class="v anti">Anti-nero</span>
							<span class="v dase">ΔΑΣΕ</span>
						</span>
					</div>
					<div class="sidelist">
						{#each rows as r (r.slug)}
							<a
								href={`/authority/${r.slug}`}
								class="siderow"
								class:hot={hovKey === `a:${r.slug}`}
								onmouseenter={() => (hovKey = `a:${r.slug}`)}
								onmouseleave={() => (hovKey = null)}
							>
								<span class="nm">{authEn(r.name)}</span>
								<span class="vals">
									<span class="v anti"
										>{r.antinero_n
											? `${grInt(r.antinero_n)} · ${eurShort(r.antinero_eur)}`
											: '—'}</span
									>
									<span class="v dase"
										>{r.dase_n ? `${grInt(r.dase_n)} · ${eurShort(r.dase_eur)}` : '—'}</span
									>
								</span>
							</a>
						{/each}
					</div>
				{:else if show === 'coops'}
					<div class="sidehead">Forest co-operatives <small>by €</small></div>
					<div class="cols">
						<span class="nm"></span>
						<span class="vals"><span class="v">contracts · €</span></span>
					</div>
					<div class="sidelist">
						{#each data.coops as c (c.vat)}
							<a
								href={`/dase/coop/${c.vat}`}
								class="siderow"
								class:hot={hovKey === `k:${c.vat}`}
								onmouseenter={() => (hovKey = `k:${c.vat}`)}
								onmouseleave={() => (hovKey = null)}
							>
								<span class="nm">{c.name}</span>
								<span class="vals"
									><span class="v">{grInt(c.n_contracts)} · {eurShort(c.total_eur)}</span></span
								>
							</a>
						{/each}
					</div>
				{:else if show === 'contractors'}
					<div class="sidehead">Anti-nero contractors <small>by €</small></div>
					<div class="cols">
						<span class="nm"></span>
						<span class="vals"><span class="v">contracts · €</span></span>
					</div>
					<div class="sidelist">
						{#each data.contractors as c (c.vat)}
							<a
								href={`/antinero/contractor/${c.vat}`}
								class="siderow"
								class:hot={hovKey === `c:${c.vat}`}
								onmouseenter={() => (hovKey = `c:${c.vat}`)}
								onmouseleave={() => (hovKey = null)}
							>
								<span class="nm">{c.name}</span>
								<span class="vals"
									><span class="v">{grInt(c.n_contracts)} · {eurShort(c.total_eur)}</span></span
								>
							</a>
						{/each}
					</div>
				{/if}
			</aside>
		</div>
	</ChartFrame>

	<ChartFrame
		title={LIST_TITLES[listShow]}
		caveat={LIST_CAVEATS[listShow]}
		anchor="list"
		methodology="authorities"
	>
		{#snippet controls()}
			<div class="listctl">
				<div class="mode" role="group" aria-label="Which population the list shows">
					<button
						type="button"
						class:active={listShow === 'authorities'}
						onclick={() => (listShow = 'authorities')}>Forest authorities</button
					>
					<button
						type="button"
						class:active={listShow === 'coops'}
						onclick={() => (listShow = 'coops')}>Forest co-ops</button
					>
					<button
						type="button"
						class:active={listShow === 'contractors'}
						onclick={() => (listShow = 'contractors')}>Anti-nero contractors</button
					>
				</div>
				<input
					class="search"
					type="search"
					placeholder="Search by name…"
					bind:value={q}
					aria-label="Search the list by name"
				/>
			</div>
		{/snippet}
		{#if listShow === 'authorities'}
		<table class="listing">
				<thead>
					<tr>
						<th>Authority</th>
						<th>Regional unit</th>
						<th class="num">Anti-nero works</th>
						<th class="num">ΔΑΣΕ awards</th>
					</tr>
				</thead>
				<tbody>
					<!-- registry rows first, then the no-contract ΥΠΕΝ directory
					     units, paginated as one sequence -->
					{#each authPageRows as row (row.kind === 'auth' ? row.r.slug : row.u.inspectorate + row.u.name)}
						{#if row.kind === 'auth'}
							{@const r = row.r}
							<tr>
								<td
									><a href={`/authority/${r.slug}`} title={devGreek(r.name)}>{authEn(r.name)}</a
									></td
								>
								<td class="muted"><small>{peEn(r.pe)}</small></td>
								<td class="num">
									{#if r.antinero_n}{r.antinero_n} · {eurShort(r.antinero_eur)}{:else}<span
											class="faint">—</span
										>{/if}
								</td>
								<td class="num">
									{#if r.dase_n}{r.dase_n} · {eurShort(r.dase_eur)}{:else}<span class="faint"
											>—</span
										>{/if}
								</td>
							</tr>
						{:else}
							{@const u = row.u}
							<tr class="nounit">
								<td title={devGreek(u.name)}>{bodyEn(u.name)}</td>
								<td class="muted"><small>—</small></td>
								<td class="num"><span class="faint">—</span></td>
								<td class="num"><span class="faint">—</span></td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		{@render pager(authAll.length, pa, (n) => (pa = n))}
		{:else if listShow === 'coops'}
		<table class="listing">
				<thead>
					<tr>
						<th>Co-operative</th>
						<th>Regional unit</th>
						<th class="num">Contracts</th>
						<th class="num">Total €</th>
					</tr>
				</thead>
				<tbody>
					{#each coopPageRows as c (c.vat)}
						<tr>
							<td><a href={`/dase/coop/${c.vat}`}>{c.name}</a></td>
							<td class="muted"><small>{c.pe ? peEn(c.pe) : '—'}</small></td>
							<td class="num">{grInt(c.n_contracts)}</td>
							<td class="num">{eurShort(c.total_eur)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{@render pager(coopList.length, pk, (n) => (pk = n))}
		{:else}
		<table class="listing">
				<thead>
					<tr>
						<th>Contractor</th>
						<th>Regional unit</th>
						<th class="num">Contracts</th>
						<th class="num">Total €</th>
					</tr>
				</thead>
				<tbody>
					{#each conPageRows as c (c.vat)}
						<tr>
							<td><a href={`/antinero/contractor/${c.vat}`}>{c.name}</a></td>
							<td class="muted"><small>{c.pe ? peEn(c.pe) : '—'}</small></td>
							<td class="num">{grInt(c.n_contracts)}</td>
							<td class="num">{eurShort(c.total_eur)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{@render pager(conList.length, pc, (n) => (pc = n))}
		{/if}
	</ChartFrame>
</div>

{#snippet pager(total: number, cur: number, set: (n: number) => void)}
	{#if total > PAGE}
		{@const last = Math.ceil(total / PAGE)}
		<nav class="pager" aria-label="List pages">
			<button disabled={cur === 0} onclick={() => set(cur - 1)} aria-label="Previous page"
				>‹</button
			>
			{#each pagesOf(total, cur) as pg, i (i)}
				{#if pg === '…'}
					<span class="gap">…</span>
				{:else}
					<button class:active={pg === cur} onclick={() => set(pg)}>{pg + 1}</button>
				{/if}
			{/each}
			<button disabled={cur >= last - 1} onclick={() => set(cur + 1)} aria-label="Next page"
				>›</button
			>
		</nav>
	{/if}
{/snippet}

<style>
	/* the dataset pages' dress (user, 2026-08-25): kicker titles and bulbs
	   in the ink — this page has no dataset hue — and the shared map ground */
	.authp {
		--frame-accent: var(--ink);
		margin-top: var(--sp-6);
	}
	.authp :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--ink);
	}
	.authp :global(.map) {
		background: #f2f2f2;
		border: 1px solid var(--line);
		--map-accent: var(--ink);
		box-shadow: none;
	}
	/* the mode switch on the frame's title line — the CONTRACT VALUES dress */
	.mode {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
	}
	.mode button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.mode button.active {
		background: var(--ink);
		color: #fff;
	}
	/* the legend — the dataset pages' grey band, docked at the top of the
	   right column, one sentence per line (user, 2026-08-26) */
	.mapkey {
		list-style: none;
		margin: 0 0 var(--sp-4);
		padding: var(--sp-2) var(--sp-3);
		background: #f2f2f2;
		border-radius: 6px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		font-size: var(--fs-14);
		color: var(--ink-soft);
		flex: none;
	}
	.mapkey li {
		display: flex;
		align-items: baseline;
		gap: 8px;
		line-height: 1.35;
	}
	.mapkey i.dot {
		position: relative;
		top: 1px;
		flex: none;
	}
	i.dot {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex: none;
	}
	i.dot.both {
		background: radial-gradient(circle, var(--c-dase) 0 34%, #406e55 34%);
	}
	.nodot {
		/* darker than the sea's #f2f2f2 — #cfcfcf read as water (user) */
		fill: #a6a6a6;
		stroke: none;
	}
	/* the map is the page's key element: map left, the shown network's
	   list right, linked by hover both ways */
	.maprow {
		display: grid;
		grid-template-columns: minmax(0, 640px) minmax(16rem, 1fr);
		gap: var(--sp-6);
		align-items: start;
	}
	.map-holder {
		min-width: 0;
	}
	.side {
		display: flex;
		flex-direction: column;
	}
	.side .sidelist {
		flex: 1;
	}
	.sidehead {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--fs-13);
		margin-bottom: var(--sp-2);
	}
	.sidehead small {
		font-weight: 400;
		color: var(--ink-soft);
	}
	.sidelist {
		overflow-y: auto;
		border-top: 1px solid var(--line);
		min-height: 0;
	}
	/* the list rows at the antinero map lists' size (fs-13) */
	.siderow {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: var(--sp-3);
		padding: 3px 2px;
		border-bottom: 1px solid var(--line);
		text-decoration: none;
		color: inherit;
		font-size: var(--fs-13);
	}
	/* the column labels over the values — the site's own spellings,
	   centred over their columns (user, 2026-08-26) */
	.cols {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: var(--sp-3);
		padding: 0 2px 2px;
		font-size: var(--fs-12);
		font-weight: 700;
	}
	.cols .nm {
		flex: 1;
	}
	.cols .vals {
		display: flex;
		gap: var(--sp-3);
		flex: none;
	}
	.cols .v {
		min-width: 6.6em;
		text-align: center;
		color: var(--ink-soft);
	}
	.cols .v.anti {
		color: var(--ink);
	}
	.cols .v.dase {
		color: var(--c-dase);
	}
	.siderow:hover,
	.siderow.hot {
		background: #f2f2f2;
	}
	.siderow .nm {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		min-width: 0;
	}
	.siderow .vals {
		display: flex;
		gap: var(--sp-3);
		flex: none;
		font-variant-numeric: tabular-nums;
	}
	.siderow .v {
		min-width: 6.6em;
		text-align: right;
		color: var(--ink-soft);
	}
	.siderow .v.anti {
		color: var(--ink);
	}
	.siderow .v.dase {
		color: var(--c-dase);
	}
	/* the listing frame: the toggle and its search on the title line */
	.listctl {
		display: flex;
		align-items: center;
		gap: var(--sp-4);
		flex-wrap: wrap;
	}
	.search {
		font: inherit;
		font-size: var(--fs-13);
		padding: 3px var(--sp-3);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		width: 16rem;
		max-width: 100%;
	}
	.pager {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 4px;
		margin: var(--sp-3) 0 var(--sp-2);
	}
	.pager button {
		font: inherit;
		font-size: var(--fs-13);
		font-variant-numeric: tabular-nums;
		min-width: 1.9rem;
		padding: 2px 6px;
		border: 1px solid var(--line);
		border-radius: var(--radius);
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.pager button:hover:not(:disabled) {
		border-color: var(--line-strong);
		color: var(--ink);
	}
	.pager button.active {
		background: var(--ink);
		border-color: var(--ink);
		color: #fff;
	}
	.pager button:disabled {
		opacity: 0.4;
		cursor: default;
	}
	.pager .gap {
		color: var(--ink-faint);
		padding: 0 2px;
	}
	.listing td a {
		text-decoration: none;
	}
	.listing td a:hover {
		text-decoration: underline;
	}
	.nounit td {
		color: var(--ink-faint);
	}
	.muted {
		color: var(--ink-soft);
	}
	.faint {
		color: var(--ink-faint);
	}
	@media (max-width: 900px) {
		.maprow {
			grid-template-columns: 1fr;
		}
	}
</style>
