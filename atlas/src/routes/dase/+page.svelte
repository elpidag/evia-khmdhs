<script lang="ts">
	import BarH from '$lib/charts/BarH.svelte';
	import BeeswarmCanvas from '$lib/charts/BeeswarmCanvas.svelte';
	import LogHistogram from '$lib/charts/LogHistogram.svelte';
	import FiresLayer from '$lib/maps/FiresLayer.svelte';
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import { loadEffisFires, type FireProps } from '$lib/maps/useGeo';
	import ChartFrame from '$lib/ui/ChartFrame.svelte';
	import Defer from '$lib/ui/Defer.svelte';
	import {
		apiGetCached,
		type DaseMapContract,
		type DaseMapPayload,
		type DaseSwarm
	} from '$lib/api';
	import { eur, eurShort, grInt, pct } from '$lib/transforms/format';
	import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const o = $derived(data.overview);

	let swarm = $state.raw<DaseSwarm | null>(null);
	let dmap = $state.raw<DaseMapPayload | null>(null);
	let firesFc = $state.raw<FeatureCollection<Polygon | MultiPolygon, FireProps> | null>(null);
	$effect(() => {
		apiGetCached<DaseSwarm>(fetch, '/api/dase/swarm').then((v) => (swarm = v));
		apiGetCached<DaseMapPayload>(fetch, '/api/dase/map').then((v) => (dmap = v));
		loadEffisFires(fetch).then((v) => (firesFc = v));
	});

	// the dataset starts Sept 2021 — salvage logging follows these burns
	const FIRES_FROM = 2021;
	const firesShown = $derived(
		firesFc ? firesFc.features.filter((f) => f.properties.yr >= FIRES_FROM) : []
	);

	// one mark per awarding unit + per-Π.Ε. circles for municipal/regional
	// government and for other public bodies, largest drawn first so small
	// circles stay clickable on top
	type MapPt = {
		name: string;
		pe: string | null;
		lat: number;
		lon: number;
		n: number;
		eur: number;
		median_eur: number;
		contracts: DaseMapContract[];
		kindKey: 'dx' | 'dd' | 'muni' | 'misc';
	};
	const mapPts = $derived.by<MapPt[]>(() => {
		if (!dmap) return [];
		return [
			...dmap.units.map((u) => ({
				...u,
				kindKey: (u.kind === 'dd' ? 'dd' : 'dx') as MapPt['kindKey']
			})),
			...dmap.other.map((g) => ({
				...g,
				name:
					g.kind === 'muni'
						? `Municipal & regional awarders · ${g.pe}`
						: `Other public bodies · ${g.pe}`,
				kindKey: g.kind as MapPt['kindKey']
			}))
		].sort((a, b) => b.eur - a.eur);
	});
	// works-ramp greens per the approved legend mock: dark for the
	// Διευθύνσεις Δασών, light for the Δασαρχεία; black for municipal &
	// regional government, grey for every other public body
	const KIND_COLOR: Record<MapPt['kindKey'], string> = {
		dd: '#406e55',
		dx: '#6fb28c',
		muni: '#000000',
		misc: '#9b9b9b'
	};
	const KIND_LABEL: Record<MapPt['kindKey'], string> = {
		dd: 'forest directorate',
		dx: 'local forest service office',
		muni: 'regional or municipal authority',
		misc: 'other public body'
	};
	const LEGEND_KINDS: MapPt['kindKey'][] = ['dd', 'dx', 'muni', 'misc'];
	const maxEur = $derived(mapPts.length ? mapPts[0].eur : 1);
	const R_MAX = 26;
	const rOf = (v: number) => Math.max(2.5, R_MAX * Math.sqrt(v / maxEur));
	// several circles can share a Π.Ε. centroid (seatless forest units,
	// municipal, other bodies) — spread the smaller ones to the right so
	// none hides underneath a bigger one
	const xOff = $derived.by<Map<string, number>>(() => {
		const byPos = new Map<string, MapPt[]>();
		for (const p of mapPts) {
			const key = `${p.lat.toFixed(4)}:${p.lon.toFixed(4)}`;
			const arr = byPos.get(key);
			if (arr) arr.push(p);
			else byPos.set(key, [p]);
		}
		const off = new Map<string, number>();
		for (const group of byPos.values()) {
			let edge = 0; // mapPts is sorted by eur desc, so group is too
			for (let i = 1; i < group.length; i++) {
				edge = (edge || rOf(group[0].eur)) + rOf(group[i].eur) + 3;
				off.set(group[i].name, edge);
				edge += rOf(group[i].eur);
			}
		}
		return off;
	});
	const dmyDate = (iso: string | null) =>
		iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '—';
	function unitTip(p: MapPt): string {
		return (
			`<strong>${p.name}</strong><br>` +
			`${grInt(p.n)} contracts · ${eur(p.eur)}<br>` +
			`median contract ${eur(p.median_eur)}`
		);
	}

	// click a circle → its contract list docks right of the map;
	// click a Π.Ε. polygon → zoom the map to it
	let sel = $state.raw<MapPt | null>(null);
	let mapPe = $state<string | null>(null);
	// legend + contract list may never run past the map's bottom edge
	let mapH = $state(0);
	let keyH = $state(0);
	// the Anti-nero maps' fixed frame — same footprint on every dataset page
	const MAP_VIEW: { center: [number, number]; k: number } = {
		center: [23.8305, 38.3566],
		k: 1.08
	};
	const fireYearHi = $derived(
		firesShown.length ? Math.max(...firesShown.map((f) => f.properties.yr)) : FIRES_FROM
	);
	function fireTip(f: Feature<Polygon | MultiPolygon, FireProps>): string {
		const p = f.properties;
		return `<strong>${p.yr}</strong> · ${grInt(p.ha)} ha${p.name ? ` · ${p.name}` : ''}`;
	}

	const coopRows = $derived(
		o.top_coops.map((c) => ({
			label: c.name,
			value: c.total_eur,
			href: `/dase/coop/${c.vat}`,
			sublabel: `${c.n_contracts} contracts · ${c.n_units} units · ${pct(c.pct_direct)} direct`
		}))
	);
	const orgRows = $derived(
		o.top_orgs.map((c) => ({
			label: c.name,
			value: c.total_eur,
			sublabel: `${grInt(c.n_contracts)} contracts`
		}))
	);
	const unitRows = $derived(
		o.top_units.map((c) => ({
			label: c.name,
			value: c.total_eur,
			sublabel: `${grInt(c.n_contracts)} contracts`
		}))
	);
	const yearRows = $derived(
		o.yearly.map((y) => ({
			label: y.year,
			value: y.eur,
			sublabel: `${grInt(y.n)} contracts`
		}))
	);
	const cpvRows = $derived(
		o.cpvs.map((c) => ({
			label: `${c.label}${c.noise ? ' — registry keying noise' : ''}`,
			value: c.n_contracts,
			sublabel: c.cpv
		}))
	);

	// finding-title inputs — computed from the payload, never hardcoded
	const topPe = $derived(
		[...o.by_pe.regions].sort((a, b) => b.eur - a.eur)[0]?.pe?.replace('Π.Ε. ', '') ?? ''
	);
	const topYear = $derived([...o.yearly].sort((a, b) => b.eur - a.eur)[0]?.year ?? '');
	const topOrgShare = $derived(
		o.top_orgs.length ? (100 * o.top_orgs[0].n_contracts) / o.kpis.n_contracts : 0
	);
	const cpvNoiseN = $derived(o.cpvs.find((c) => c.noise)?.n_contracts ?? 0);

	// hero bar fills — data-proportional
	const paidPct = $derived((o.kpis.paid_eur / o.kpis.total_eur) * 100);
</script>

<svelte:head>
	<title>ΔΑΣΕ — forest labour co-operatives</title>
	<meta
		name="description"
		content="Every Greek public contract won by a forest labour co-operative since Sept 2021: {grInt(
			o.kpis.n_contracts
		)} contracts, {eurShort(o.kpis.total_eur)} stated (excl. VAT)."
	/>
</svelte:head>

<div class="dasep">
<section class="hero">
	<div class="heroleft">
	<div class="cards">
		<div class="card">
			<div class="num">{grInt(o.kpis.n_contracts)}</div>
			<div class="lbl">live contracts since Sept 2021</div>
		</div>
		<div class="card">
			<div class="num">{grInt(o.kpis.n_coops)}</div>
			<div class="lbl">forest labour co-operatives</div>
		</div>
		<div class="card">
			<div class="num">{eurShort(o.kpis.total_eur).toLowerCase()}</div>
			<div class="lbl">
				total stated value of contracts<br />(excl. VAT)
			</div>
		</div>
	</div>
	<div class="midcol">
		<div class="bars">
			<div class="dabar" role="img" aria-label="Share of contracts awarded directly">
				<div class="track">
					<div class="fill" style:width={`${o.kpis.pct_direct}%`}>
						<div class="danum">{pct(o.kpis.pct_direct)}</div>
						<div class="datext">of contracts were direct awards</div>
					</div>
				</div>
			</div>
		</div>
		<div class="paidcard" role="img" aria-label="Paid so far, as a share of the stated total">
			<div class="pfill" style:height={`${paidPct}%`}>
				<div class="pnum">{eurShort(o.kpis.paid_eur).toLowerCase()}</div>
				<div class="plbl">already paid</div>
			</div>
		</div>
	</div>
	</div>
	<div class="about">
		<div class="kicker">THE CO-OPERATIVES</div>
		<p>
			Every public contract won by a forest labour co-operative (ΔΑ.Σ.Ε., ν.4423/2016) since
			September 2021 — logging, clearing and tending work in the same forests the Anti-nero
			millions target, at a fraction of the size: the median contract is {eur(
				o.kpis.median_eur
			)} and {pct(o.kpis.pct_direct)} went by direct award, from {grInt(o.kpis.n_orgs)} awarding
			bodies through {grInt(o.kpis.n_units)} units. Of the {eurShort(o.kpis.total_eur)} stated,
			{eurShort(o.kpis.paid_eur)} shows as paid ({grInt(o.kpis.n_payments)} payment orders) —
			payments are posted for {grInt(o.kpis.n_paid_contracts)} of {grInt(
				o.kpis.n_contracts
			)} contracts, a registry practice, not a delivery record. {grInt(
				o.kpis.n_cancelled
			)} cancelled and {grInt(o.kpis.n_superseded)} superseded versions are excluded, and one
			co-op's up to {o.kpis.max_name_variants} registry spellings merge on the canonical ΑΦΜ —
			<a href="/methodology#dase-dedup">methodology</a>.
		</p>
	</div>
</section>

{#if dmap}
	<ChartFrame
		title="MAP"
		caveat="Click a circle for its contracts, click a regional unit to zoom to it. {grInt(
			dmap.unresolved.n
		)} ΑΔΜΗΕ power-line contracts span multiple Π.Ε. and stay off the map ({eurShort(
			dmap.unresolved.eur
		)}). Burn scars: © European Union, Copernicus Emergency Management Service — EFFIS; satellite rapid-mapping estimates, not official οριοθετήσεις."
		anchor="dase-map"
		methodology="dase-regions"
	>
		<div class="maprow" class:open={sel !== null}>
			<div class="map-holder" bind:clientHeight={mapH}>
				<PaperMap
					width={640}
					height={620}
					view={MAP_VIEW}
					colorOf={() => '#fff'}
					focusPe={mapPe}
					onRegionClick={(pe) => (mapPe = mapPe === pe ? null : pe)}
				>
					{#snippet overlay(ctx)}
						{#if firesShown.length}
							<FiresLayer {ctx} features={firesShown} tipOf={fireTip} />
						{/if}
						{#each mapPts as p (p.name)}
							{@const xy = ctx.projection([p.lon, p.lat])}
							{#if xy}
								<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
								<circle
									cx={xy[0] + (xOff.get(p.name) ?? 0) / ctx.k}
									cy={xy[1]}
									r={rOf(p.eur) / ctx.k}
									class="ucircle"
									style:fill={KIND_COLOR[p.kindKey]}
									onmouseenter={() => ctx.showTip(unitTip(p))}
									onmouseleave={() => ctx.hideTip()}
									onclick={() => (sel = sel?.name === p.name ? null : p)}
								/>
							{/if}
						{/each}
						<!-- labels drawn after every circle so overlaps never cover them -->
						{#each mapPts as p (`l:${p.name}`)}
							{@const xy = ctx.projection([p.lon, p.lat])}
							{#if xy && rOf(p.eur) >= 12}
								<text
									class="ulabel"
									x={xy[0] + (xOff.get(p.name) ?? 0) / ctx.k}
									y={xy[1]}
									dy="0.35em"
									font-size={11 / ctx.k}
								>
									{p.n}
								</text>
							{/if}
						{/each}
					{/snippet}
				</PaperMap>
			</div>
			<div class="mapside">
				<!-- the legend panel, top-aligned with the map: awarder dots
				     stacked left, size + burnt-areas explanations right -->
				<div class="mapkey" bind:clientHeight={keyH}>
					<div class="mk-left">
						<div class="mk-title">contracts awarded by</div>
						<ul class="mk-kinds">
							{#each LEGEND_KINDS as k (k)}
								<li>
									<i style:background={KIND_COLOR[k]}></i>
									{KIND_LABEL[k]}
								</li>
							{/each}
						</ul>
					</div>
					<div class="mk-right">
						<div class="mk-size">
							<svg width="40" height="40" aria-hidden="true">
								<!-- small circle internally tangent at the bottom, x inside it -->
								<circle class="mk-c" cx="20" cy="20" r="17" />
								<circle class="mk-c" cx="20" cy="29" r="8" />
								<text class="mk-x" x="20" y="29" dy="0.35em">x</text>
							</svg>
							<div class="mk-sizetext">
								<p>circle size: total € awarded</p>
								<p>x: number of contracts</p>
							</div>
						</div>
						<div class="mk-fires">
							<div class="mk-firetitle">burnt areas</div>
							<i class="firegrad"></i>
							<div class="mk-years"><span>{FIRES_FROM}</span><span>{fireYearHi}</span></div>
						</div>
					</div>
				</div>
				{#if sel}
					<aside class="unitpanel" style:max-height={`${Math.max(160, mapH - keyH - 16)}px`}>
						<header>
							<div>
								<div class="up-name">{sel.name}</div>
								<div class="up-stats">
									{grInt(sel.n)} contracts, median: {eur(sel.median_eur)}, total amount: {eur(
										sel.eur
									)}
								</div>
							</div>
							<button class="up-close" onclick={() => (sel = null)} aria-label="Close">×</button>
						</header>
						<table class="uptable">
							<thead>
								<tr><th>ΑΔΑΜ</th><th>awarding unit</th><th>ΔΑΣΕ</th><th>date</th><th class="num">€</th></tr>
							</thead>
							<tbody>
								{#each sel.contracts as c (c.ref)}
									<tr>
										<td><a href={`/dase/contract/${c.ref}`}>{c.ref}</a></td>
										<td>{c.by || '—'}</td>
										<td>{c.coop || '—'}</td>
										<td class="nowrap">{dmyDate(c.d)}</td>
										<td class="num">{c.eur === null ? '—' : eur(c.eur)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</aside>
				{/if}
			</div>
		</div>
	</ChartFrame>
{:else}
	<div class="skeleton" id="dase-map" style="height: 560px"></div>
{/if}

<Defer height={400}>
{#if swarm}
	<ChartFrame title="CONTRACT VALUES" anchor="dase-swarm">
		<BeeswarmCanvas
			data={swarm}
			note="Every contract is represented as one dot on a log scale (stated €, excl. VAT). Colours are assigned according to the year the contract was signed. Hover to inspect, click through to go to the contract's page."
		/>
	</ChartFrame>
{:else}
	<div class="skeleton" style="height: 380px"></div>
{/if}
</Defer>

<div class="pair">
	<ChartFrame
		title="MONEY PER YEAR"
		subtitle="Stated € and contract counts per signature year — {topYear} carried the biggest υλοτομία money; volumes stay high since."
		anchor="dase-yearly"
	>
		<BarH rows={yearRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="SIZE DISTRIBUTION"
		subtitle="{grInt(o.histogram.n)} live contracts by stated value — small sums, tight distribution."
		anchor="dase-hist"
	>
		<LogHistogram
			labels={o.histogram.labels}
			counts={o.histogram.counts}
			edges={o.histogram.edges}
			color="var(--c-dase)"
			median={o.histogram.median}
		/>
	</ChartFrame>
</div>

<ChartFrame
	title="RANKING OF CO-OPS"
	subtitle="according to sums contracted — top {coopRows.length} of {grInt(
		o.kpis.n_coops
	)} co-operatives collect {eurShort(coopRows.reduce((s, r) => s + r.value, 0))} of the {eurShort(
		o.kpis.total_eur
	)}, merged across registry spellings by canonical ΑΦΜ"
	caveat="Consortium values counted in full for each partner (rare here: {grInt(o.kpis.n_consortium)} of {grInt(o.kpis.n_contracts)} contracts)."
	anchor="top-coops"
	methodology="canonical-vat"
>
	<div class="rankw">
		<BarH rows={coopRows} color="var(--c-dase)" inside barHeight={30} />
	</div>
</ChartFrame>

<div class="pair">
	<ChartFrame
		title="AWARDING BODIES"
		subtitle="{o.top_orgs[0]?.name ?? 'ΥΠΕΝ'} awards {pct(topOrgShare)} of the contracts; other bodies share the rest (grouped by name — registry VATs collide)."
		anchor="dase-orgs"
		methodology="org-names"
	>
		<BarH rows={orgRows} color="var(--c-dase)" />
	</ChartFrame>

	<ChartFrame
		title="AWARDING UNITS"
		subtitle="Top awarding units by stated € — Δασαρχεία are the working level."
		anchor="dase-units"
	>
		<BarH rows={unitRows} color="var(--c-dase)" />
	</ChartFrame>
</div>

<ChartFrame
	title="CPV MIX"
	subtitle="Top CPV codes by contract count — υλοτομία dominates."
	caveat="{grInt(cpvNoiseN)} υλοτομικά rows carry a miskeyed insurance CPV (66519300-4) — flagged, never counted as insurance."
	anchor="dase-cpvs"
	methodology="dase-cpv-noise"
>
	<BarH rows={cpvRows} color="var(--c-dase)" fmt={(v) => `${grInt(v)} contracts`} />
</ChartFrame>

</div>

<style>
	/* every section title follows the sponsored-works kicker, in the
	   ΔΑΣΕ dataset colour (green) */
	.dasep :global(.frame .finding) {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		line-height: 1.3;
		color: var(--c-dase);
	}
	/* the paper map takes the shared ground; regions stay white so the
	   proportional circles carry the data */
	.dasep :global(.map) {
		background: #f2f2f2;
		border: none;
		box-shadow: none;
	}
	.dasep :global(.region) {
		stroke: #8f8f8f;
	}
	/* flat solid dots, exactly like the legend swatches — no outline;
	   the hover ring is interaction feedback only */
	.ucircle {
		fill: var(--c-dase);
		stroke: none;
	}
	.ucircle:hover {
		stroke: var(--ink);
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}
	.ulabel {
		fill: #fff;
		font-family: var(--font-display);
		font-weight: 900;
		text-anchor: middle;
		pointer-events: none;
	}
	/* map left; legend (and the clicked unit's contract list) on the right,
	   top-aligned with the map */
	.maprow {
		/* 640×620 viewBox rendered at 600px → 600×581.5 on screen */
		display: grid;
		grid-template-columns: minmax(0, 600px) minmax(250px, 1fr);
		gap: var(--sp-4);
		align-items: start;
	}
	@media (max-width: 900px) {
		.maprow {
			grid-template-columns: 1fr;
		}
	}
	.mapside {
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	/* the legend panel per the approved mock: awarder dots stacked in the
	   left column, size icon + burnt-areas gradient in the right one */
	.mapkey {
		background: #f2f2f2;
		border-radius: 10px;
		padding: var(--sp-2) var(--sp-4);
		font-size: var(--fs-13);
		color: var(--ink);
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6);
		align-items: start;
	}
	@media (max-width: 900px) {
		.mapkey {
			grid-template-columns: 1fr;
		}
	}
	.mk-title {
		margin-bottom: 8px;
	}
	.mk-kinds {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.mk-kinds li {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.mk-kinds i {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		flex: none;
	}
	.mk-size {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		margin-bottom: 8px;
	}
	.mk-size svg {
		flex: none;
	}
	.mk-c {
		fill: none;
		stroke: var(--ink-soft);
		stroke-width: 1.3;
	}
	.mk-x {
		fill: var(--ink);
		font-size: 11px;
		text-anchor: middle;
	}
	.mk-sizetext {
		max-width: 26em;
	}
	.mk-sizetext p {
		margin: 0 0 2px;
	}
	.mk-firetitle {
		margin-bottom: 4px;
	}
	.firegrad {
		display: block;
		max-width: 340px;
		height: 14px;
		border-radius: 3px;
		background: linear-gradient(to right, #ffffff, #6b2d35);
	}
	.mk-years {
		display: flex;
		justify-content: space-between;
		max-width: 340px;
		font-size: var(--fs-12);
		color: var(--ink-soft);
	}
	.unitpanel {
		background: #fff;
		border: 1px solid var(--line);
		border-radius: 6px;
		display: flex;
		flex-direction: column;
	}
	.unitpanel header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--sp-2);
		padding: var(--sp-3);
		border-bottom: 1px solid var(--line);
	}
	.up-name {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
	}
	.up-stats {
		font-size: var(--fs-12);
		font-weight: 700;
		color: var(--ink);
	}
	.up-close {
		border: none;
		background: none;
		font-size: var(--fs-18);
		line-height: 1;
		cursor: pointer;
		color: var(--ink-soft);
		padding: 0 2px;
	}
	.uptable {
		display: block;
		overflow-y: auto;
		margin: 0;
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-11, 11px);
		border-collapse: collapse;
	}
	.uptable th {
		text-align: left;
		font-weight: 700;
		color: var(--ink-soft);
		padding: 2px 8px 4px 0;
		white-space: nowrap;
	}
	.uptable td {
		padding: 4px 8px 4px 0;
		border-top: 1px solid #f0f0f0;
		vertical-align: top;
	}
	.uptable td a {
		white-space: nowrap;
	}
	.uptable .num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		padding-right: 0;
		white-space: nowrap;
	}
	.uptable .nowrap {
		white-space: nowrap;
	}
	.ucircle {
		cursor: pointer;
	}
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: var(--sp-6) var(--sp-12);
		margin: var(--sp-6) 0 var(--sp-12);
	}
	/* cards column + the bars/paid column beside it — same equal-column
	   geometry as the Anti-nero hero */
	.heroleft {
		display: grid;
		grid-template-columns: 268px 268px;
		gap: var(--sp-4);
		align-items: stretch;
	}
	.cards {
		/* three equal rows — every card the height of the tallest */
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	/* middle column mirrors the cards grid: the two bars share the first
	   card's row, the paid card fills the third row */
	.midcol {
		display: grid;
		grid-template-rows: repeat(3, 1fr);
		gap: var(--sp-4);
		width: 268px;
		max-width: 100%;
	}
	.bars {
		grid-row: 1;
		display: grid;
		grid-template-rows: 1fr 1fr;
		gap: var(--sp-4);
	}
	.dabar .track {
		height: 100%;
		background: #fff;
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.dabar .fill {
		height: 100%;
		background: var(--c-dase);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 2px;
		padding: 0 14px;
	}
	.dabar .danum {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-18);
		line-height: 1;
	}
	.dabar .datext {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-12);
		line-height: 1.2;
	}
	/* paid vs stated: green fill rises to the paid share of the stated €;
	   the unfilled remainder reads as light grey, no outer border */
	.paidcard {
		grid-row: 3;
		position: relative;
		background: #fff;
		border: 1.5px solid var(--c-dase);
		border-radius: 10px;
		overflow: hidden;
	}
	.paidcard .pfill {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--c-dase);
		color: #fff;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 2px;
		padding: 8px 14px 10px;
	}
	.paidcard .pnum {
		font-family: var(--font-display);
		font-weight: 900;
		/* matches the card numbers' cap */
		font-size: 36px;
		line-height: 0.95;
		white-space: nowrap;
	}
	.paidcard .plbl {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	@media (max-width: 900px) {
		.heroleft {
			grid-template-columns: 268px;
		}
		.midcol {
			grid-template-rows: auto;
		}
		.bars,
		.paidcard {
			grid-row: auto;
		}
		.paidcard {
			height: 117px;
		}
	}
	.card {
		background: var(--c-dase);
		color: #fff;
		padding: var(--sp-4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--sp-4);
	}
	.card .num {
		font-family: var(--font-display);
		font-weight: 900;
		/* same cap as the other dataset pages' KPI cards */
		font-size: clamp(28px, 3.2vw, 36px);
		line-height: 0.95;
	}
	.card .lbl {
		font-family: var(--font-display);
		font-weight: 400; /* Obviously Regular */
		font-size: var(--fs-13);
		line-height: 1.2;
	}
	.about .kicker {
		font-family: var(--font-display);
		font-weight: 900;
		font-size: var(--fs-14);
		letter-spacing: 0.08em;
		margin-bottom: var(--sp-3);
		color: var(--c-dase);
	}
	.about p {
		margin: 0;
		max-width: var(--prose-w);
	}
	@media (max-width: 900px) {
		.hero {
			grid-template-columns: 1fr;
		}
	}
	.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--sp-6);
	}
	@media (max-width: 900px) {
		.pair {
			grid-template-columns: 1fr;
		}
	}
	.map-holder {
		max-width: 44rem;
	}
	/* same footprint as the sponsored-works RANKING OF COMPANIES */
	.rankw {
		max-width: 75%;
	}
	@media (max-width: 900px) {
		.rankw {
			max-width: none;
		}
	}
</style>
