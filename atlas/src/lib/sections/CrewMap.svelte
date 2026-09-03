<script lang="ts">
	/**
	 * WHO DID THE WORK — the fire→sponsor→crew EPISODES (user, DATA_DECISIONS
	 * 2026-08-24, fourth review round).
	 *
	 * The reader's questions, in the user's words: when the fires happened,
	 * how soon the projects appeared, and from where the ΔΑΣΕ crews came.
	 * Fires are DISCRETE events, so the navigator is not a day slider
	 * (1.900 days of mostly nothing) but the episode list itself — each row
	 * carries the fire date, the designation-act date with the wait, the
	 * sponsor and the crew. Choosing a row isolates its episode on the map
	 * — ONLY its scar, its ground and its crews' journeys stay, everything
	 * else leaves (dimmed layers while moving were the confusion) — and the
	 * map reframes to fit them. The map takes no gestures at all: the list
	 * is the only wheel.
	 *
	 * Colours: projects in the section's dark green (all are completed
	 * works), the co-operatives' seats black, the fires alone in the EFFIS
	 * maroon.
	 */
	import PaperMap from '$lib/maps/PaperMap.svelte';
	import DotLayer from '$lib/maps/DotLayer.svelte';
	import { dmy, grInt } from '$lib/transforms/format';
	import { fireEn } from '$lib/transforms/names';
	import type { Feature, Polygon, MultiPolygon } from 'geojson';
	import type { FireProps } from '$lib/maps/useGeo';

	export interface CrewLink {
		ada: string;
		company: string;
		coop: string;
		vat: string | null;
		pe: string | null;
		seat_lat: number;
		seat_lon: number;
		seat_pe: string | null;
		seat_place: string | null;
		work_lat: number;
		work_lon: number;
		work_kind: 'site' | 'zone' | 'scar';
		km: number;
		fire: string | null;
		fire_date: string | null;
		act_date: string | null;
		lag_days: number | null;
		scars: number[];
	}
	interface Props {
		links: CrewLink[];
		fires?: Feature<Polygon | MultiPolygon, FireProps>[];
	}
	let { links, fires = [] }: Props = $props();

	// the STATUS map's own frame at rest (user, 2026-08-24)
	const MAP_VIEW = { center: [23.8305, 38.3566] as [number, number], k: 1.08 };

	/** one EPISODE per project: fire → act → crews */
	const episodes = $derived.by(() => {
		const by = new Map<string, {
			ada: string; company: string; pe: string | null;
			fire: string | null; fire_date: string | null; act_date: string | null;
			lag_days: number | null; scars: number[];
			lat: number; lon: number; kind: CrewLink['work_kind'];
			crews: CrewLink[];
		}>();
		for (const l of links) {
			const e = by.get(l.ada) ?? {
				ada: l.ada, company: l.company, pe: l.pe,
				fire: l.fire, fire_date: l.fire_date, act_date: l.act_date,
				lag_days: l.lag_days, scars: l.scars,
				lat: l.work_lat, lon: l.work_lon, kind: l.work_kind, crews: []
			};
			e.crews.push(l);
			by.set(l.ada, e);
		}
		return [...by.values()].sort((a, b) =>
			(a.fire_date ?? a.act_date ?? '9') < (b.fire_date ?? b.act_date ?? '9') ? -1 : 1
		);
	});

	let listEl = $state<HTMLElement | null>(null);
	let sel = $state<string | null>(null); // the chosen episode's ΑΔΑ
	let hov = $state<string[] | null>(null);
	const active = $derived(sel ? [sel] : hov);
	const chosen = $derived(sel ? episodes.find((e) => e.ada === sel) ?? null : null);

	/** which episodes own a scar — clicking a fire outline selects them,
	 *  cycling when a scar serves more than one project */
	const scarOwners = $derived.by(() => {
		const by = new Map<number, string[]>();
		for (const e of episodes)
			for (const s of e.scars) by.set(s, [...(by.get(s) ?? []), e.ada]);
		return by;
	});
	function cycle(adas: string[]) {
		if (!adas.length) return;
		const i = sel ? adas.indexOf(sel) : -1;
		sel = i >= 0 && i === adas.length - 1 ? null : adas[i + 1] ?? adas[0];
	}

	/** the elements on the map: everything at rest, ONLY the chosen
	 *  episode's while one is held — hidden, not dimmed */
	const shownEpisodes = $derived(chosen ? [chosen] : episodes);
	const shownLinks = $derived(chosen ? chosen.crews : links);
	/** the fires: every scar since 2021 stays on the map — the ones a
	 *  project repairs in the deep maroon, the rest a step lighter (user,
	 *  2026-08-24); while an episode is held only ITS scar keeps the deep
	 *  tone and the rest fall to the light one */
	const activeScars = $derived(new Set(shownEpisodes.flatMap((e) => e.scars)));
	const darkFires = $derived(fires.filter((f) => activeScars.has(f.properties.id)));
	const lightFires = $derived(
		fires.filter((f) => !activeScars.has(f.properties.id))
	);

	/** the frame while an episode is held: its ground, its crews' seats and
	 *  its scar's extent, fitted together — the journey IS the story, so
	 *  the origin belongs in the frame */
	const fitPts = $derived.by(() => {
		if (!chosen) return null;
		const pts: [number, number][] = [[chosen.lon, chosen.lat]];
		for (const c of chosen.crews) pts.push([c.seat_lon, c.seat_lat]);
		for (const f of darkFires) {
			let lo: [number, number] = [Infinity, Infinity];
			let hi: [number, number] = [-Infinity, -Infinity];
			const walk = (c: unknown[]) => {
				if (typeof c[0] === 'number') {
					const p = c as unknown as [number, number];
					lo = [Math.min(lo[0], p[0]), Math.min(lo[1], p[1])];
					hi = [Math.max(hi[0], p[0]), Math.max(hi[1], p[1])];
				} else for (const x of c) walk(x as unknown[]);
			};
			walk(f.geometry.coordinates as unknown[]);
			if (Number.isFinite(lo[0])) pts.push(lo, hi);
		}
		return pts;
	});

	/** the geographic span of a feature, in degrees */
	function span(f: Feature<Polygon | MultiPolygon, FireProps>) {
		let lo: [number, number] = [Infinity, Infinity];
		let hi: [number, number] = [-Infinity, -Infinity];
		const walk = (c: unknown[]) => {
			if (typeof c[0] === 'number') {
				const p = c as unknown as [number, number];
				lo = [Math.min(lo[0], p[0]), Math.min(lo[1], p[1])];
				hi = [Math.max(hi[0], p[0]), Math.max(hi[1], p[1])];
			} else for (const x of c) walk(x as unknown[]);
		};
		walk(f.geometry.coordinates as unknown[]);
		return Number.isFinite(lo[0]) ? Math.max(hi[0] - lo[0], hi[1] - lo[1]) : 0;
	}
	/** A 275 ha fire (Κρυονέρι–Δροσοπηγή) is a few pixels once the frame
	 *  must also hold a crew's seat 273 km away. Rather than stand a marker
	 *  in for it, THAT episode's map becomes zoomable so the reader can go
	 *  and look at the real scar (user, 2026-08-24) — only for these, so
	 *  every other episode stays a still picture. */
	const frameSpan = $derived.by(() => {
		if (!fitPts?.length) return 0;
		const xs = fitPts.map((p) => p[0]);
		const ys = fitPts.map((p) => p[1]);
		return Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
	});
	const tinyScar = $derived(
		!!chosen && frameSpan > 0 &&
			darkFires.length > 0 &&
			Math.max(...darkFires.map(span)) / frameSpan < 0.06
	);

	/** dots for the layers (year of the crews' seats deduplicated) */
	const seatDots = $derived.by(() => {
		const by = new Map<string, { key: string; lat: number; lon: number;
			coop: string; vat: string | null; adas: string[] }>();
		for (const l of shownLinks) {
			const key = l.vat ?? l.coop;
			const e = by.get(key) ?? {
				key, lat: l.seat_lat, lon: l.seat_lon, coop: l.coop, vat: l.vat, adas: []
			};
			e.adas.push(l.ada);
			by.set(key, e);
		}
		return [...by.values()];
	});
	const groundDots = $derived(shownEpisodes.map((e) => ({ ...e })));

	const lit = (ada: string) => !active || active.includes(ada);

	/** the list follows the map: choosing an episode anywhere brings its
	 *  row into view (user, 2026-08-24) */
	$effect(() => {
		if (!sel || !listEl) return;
		const row = listEl.querySelector(`[data-ada="${CSS.escape(sel)}"]`);
		row?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	});

	/** a gentle arc, bowed left of the seat→work line, like FLOWS OF MONEY */
	function arc(x1: number, y1: number, x2: number, y2: number) {
		const dx = x2 - x1,
			dy = y2 - y1;
		const mx = (x1 + x2) / 2,
			my = (y1 + y2) / 2;
		const len = Math.hypot(dx, dy) || 1;
		const bow = Math.min(48, len * 0.18);
		return `M${x1},${y1} Q${mx - (dy / len) * bow},${my + (dx / len) * bow} ${x2},${y2}`;
	}
</script>

<div class="crew">
	<div class="row">
		<div class="map-wrap">
			<PaperMap
				width={640}
				height={620}
				view={chosen ? null : MAP_VIEW}
				fitPoints={fitPts}
				fitPad={0.16}
				interactive={tinyScar}
				panAtRest={false}
				colorOf={() => 'var(--paper)'}
			>
				{#snippet overlay(ctx)}
					<defs>
						<!-- the FLOWS OF MONEY convention: a fixed-size OPEN chevron;
						     refX pulls it clear of the work dot so it reads as an
						     arrow pointing AT the ground -->
						<!-- markerUnits=strokeWidth does not render on vector-effect
						     paths in Chromium, so the marker is sized in user units,
						     divided by the zoom: screen-constant, ~8px — proportionate
						     to the 2,6px line — with the tip landing ON the work dot's
						     rim (refX pulls it back exactly the dot's radius) -->
						<marker
							id="crew-arrow"
							markerUnits="userSpaceOnUse"
							viewBox="0 0 10 10"
							markerWidth={11 / ctx.k}
							markerHeight={11 / ctx.k}
							refX="13"
							refY="5"
							orient="auto"
						>
							<path d="M1.5,1.5 L8,5 L1.5,8.5" class="arrowhead" />
						</marker>
					</defs>
					<g class="scars">
						{#each lightFires as f (f.properties.id)}
							<path d={ctx.path(f) ?? ''} class="scar light" />
						{/each}
						<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
						{#each darkFires as f (f.properties.id)}
							<path
								d={ctx.path(f) ?? ''}
								class="scar dark"
								onmouseenter={() => (hov = scarOwners.get(f.properties.id) ?? null)}
								onmouseleave={() => (hov = null)}
								onclick={() => cycle(scarOwners.get(f.properties.id) ?? [])}
							/>
						{/each}
					</g>
					<!-- the journeys draw only while an episode is hovered or held:
					     at rest they pulled the eye onto the lines and away from the
					     burnt scars and the places themselves (user, 2026-08-25) -->
					<g class="arcs">
						{#each active ? shownLinks : [] as l (l.ada + (l.vat ?? l.coop))}
							{@const a = ctx.projection([l.seat_lon, l.seat_lat])}
							{@const b = ctx.projection([l.work_lon, l.work_lat])}
							{#if a && b}
								<path
									d={arc(a[0], a[1], b[0], b[1])}
									class="flow"
									class:solid={!!chosen}
									class:dim={!lit(l.ada)}
									style:stroke-width={chosen ? 2.6 : 1.4}
									marker-end={chosen ? 'url(#crew-arrow)' : undefined}
								/>
							{/if}
						{/each}
					</g>
					<DotLayer
						{ctx}
						points={groundDots}
						r={chosen ? 5.5 : 4}
						fillOf={() => 'var(--c-anadohoi)'}
						stroke="none"
						opacity={1}
						onOver={(p) => (hov = [(p as unknown as { ada: string }).ada])}
						onOut={() => (hov = null)}
						onClick={(p) => {
							const ada = (p as unknown as { ada: string }).ada;
							sel = sel === ada ? null : ada;
						}}
					/>
					<DotLayer
						{ctx}
						points={seatDots}
						r={chosen ? 5.5 : 4}
						fillOf={() => 'color-mix(in srgb, var(--ink) 53.3%, black)'}
						stroke="none"
						opacity={1}
						onOver={(p) => (hov = (p as unknown as { adas: string[] }).adas)}
						onOut={() => (hov = null)}
						onClick={(p) => cycle((p as unknown as { adas: string[] }).adas)}
					/>
				{/snippet}
			</PaperMap>
		</div>

		<div class="side">
			<!-- the key sits above the list, two rows (user, 2026-08-24) -->
			<ul class="mapkey">
				<li><i class="sw fire dark"></i>burnt areas connected with sponsored works</li>
				<li><i class="sw work"></i>sponsored works</li>
				<li><i class="sw fire"></i>other fires since 2021</li>
				<li><i class="sw seat"></i>forest workers' co-op base</li>
				<li class="hintrow">hover or choose an episode to draw its journey</li>
			</ul>
			{#if tinyScar}
				<p class="zoomhint">This burnt area is small — click the map, then scroll to zoom into it.</p>
			{/if}

		<!-- THE EPISODES: fire date · act date & wait · sponsor · crew —
		     the list the reader asked for, and the map's only wheel -->
		<ol class="episodes" bind:this={listEl}>
			{#each episodes as e (e.ada)}
				<li
					data-ada={e.ada}
					class:on={sel === e.ada}
					class:faint={active !== null && !active.includes(e.ada)}
				>
					<button
						class="ep"
						onclick={() => (sel = sel === e.ada ? null : e.ada)}
						onmouseenter={() => (hov = [e.ada])}
						onmouseleave={() => (hov = null)}
					>
						<span class="d fire">
							<span class="lab"><i></i>fire</span>
							<span class="val"
								>{e.fire_date ? dmy(e.fire_date) : 'date unknown'}
								<em>{fireEn(e.fire ?? '')}</em></span
							>
						</span>
						<span class="d act">
							<span class="lab"><i></i>sponsor appointed</span>
							<span class="val"
								>{e.act_date ? dmy(e.act_date) : '—'}
								{#if e.lag_days != null}<b>{grInt(e.lag_days)} days after the fire</b
									>{/if}</span
							>
						</span>
						<span class="d act">
							<span class="lab"><i class="ghost"></i>sponsor</span>
							<span class="val"
								><em
									><a
										href={`/anadohoi/project/${e.ada}`}
										onclick={(ev) => ev.stopPropagation()}>{e.company}</a
									></em
								></span
							>
						</span>
						<span class="d crews">
							<span class="lab"><i></i>works executed by</span>
							<span class="val cnames">
								{#each e.crews as c, i (c.vat ?? c.coop)}{#if i},
									{/if}{#if c.vat}<a
											href={`/dase/coop/${c.vat}`}
											onclick={(ev) => ev.stopPropagation()}>{c.coop}</a
										>{:else}{c.coop}{/if}{/each}
							</span>
						</span>
					</button>
				</li>
			{/each}
		</ol>
		</div>
	</div>
</div>

<style>
	.crew {
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
	}
	/* the key sits above the list in the right column, two rows */
	.side {
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
		min-width: 0;
	}
	.mapkey {
		list-style: none;
		margin: 0;
		padding: var(--sp-2) var(--sp-3);
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, auto));
		justify-content: start;
		align-items: center;
		gap: 5px var(--sp-4);
		font-size: var(--fs-13);
		color: var(--ink-soft);
	}
	.mapkey li {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.sw {
		width: 11px;
		height: 11px;
		flex: none;
		border-radius: 50%;
		display: inline-block;
	}
	.sw.seat {
		background: color-mix(in srgb, var(--ink) 53.3%, black);
	}
	.sw.work {
		background: var(--c-anadohoi);
	}
	.sw.fire {
		border-radius: 2px;
		background: color-mix(in oklab, var(--c-fire) 30.4%, var(--paper));
	}
	.sw.fire.dark {
		background: var(--c-fire);
	}
	/* the STATUS map's own footprint: the map fills a ~640px column, the
	   episode list rides beside it */
	.row {
		display: grid;
		grid-template-columns: minmax(0, 640px) minmax(280px, 1fr);
		gap: var(--sp-4);
		align-items: start;
	}
	@media (max-width: 900px) {
		.row {
			grid-template-columns: 1fr;
		}
	}
	.map-wrap :global(.map) {
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border: 1px solid var(--line);
		--map-accent: var(--c-anadohoi);
		box-shadow: none;
	}
	.map-wrap :global(.map .region) {
		fill: var(--paper);
		stroke: var(--line);
	}
	.flow {
		fill: none;
		stroke: color-mix(in srgb, var(--ink) 53.3%, black);
		opacity: 0.85;
		vector-effect: non-scaling-stroke;
		stroke-linecap: round;
		/* the journey reads as a route, not a border (user, 2026-08-24) */
		stroke-dasharray: 6 4;
	}
	.scar {
		stroke: none;
	}
	.scar.dark {
		cursor: pointer;
	}

	.arrowhead {
		fill: none;
		stroke: color-mix(in srgb, var(--ink) 53.3%, black);
		stroke-width: 1.7;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	.scar.light {
		fill: color-mix(in oklab, var(--c-fire) 30.4%, var(--paper));
		opacity: 0.7;
	}
	.scar.dark {
		fill: var(--c-fire);
		opacity: 0.85;
	}
	.flow.solid {
		opacity: 1;
	}
	.flow.dim {
		opacity: 0.1;
	}
	/* ---- the episode list */
	.episodes {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		/* the map's height less the key above it, so the two columns end
		   together and the map's own size never changes */
		max-height: 540px;
		overflow-y: auto;
		scroll-behavior: smooth;
	}
	.mapkey li.hintrow {
		grid-column: 1 / -1;
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
	.zoomhint {
		margin: 0;
		font-size: var(--fs-12);
		color: var(--c-anadohoi);
	}
	.episodes li {
		border-bottom: 1px solid var(--line);
	}
	.episodes li:last-child {
		border-bottom: 0;
	}
	.episodes li.faint {
		opacity: 0.45;
	}
	.episodes li.on {
		opacity: 1;
		background: color-mix(in srgb, var(--c-dase) 6.3%, var(--paper));
	}
	.ep {
		display: flex;
		flex-direction: column;
		gap: 1px;
		width: 100%;
		border: 0;
		background: none;
		font: inherit;
		text-align: left;
		cursor: pointer;
		padding: 6px 8px;
		color: var(--ink-soft);
	}
	/* each row is three LABELLED lines — a reader who has never seen this
	   page must be able to decode it (user, 2026-08-24) */
	.d {
		display: grid;
		grid-template-columns: 9.5rem minmax(0, 1fr);
		gap: var(--sp-2);
		align-items: baseline;
		font-size: var(--fs-13);
		font-variant-numeric: tabular-nums;
		min-width: 0;
	}
	.lab {
		display: flex;
		align-items: baseline;
		gap: 6px;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 10.5px;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--ink);
		white-space: nowrap;
	}
	.lab i {
		width: 9px;
		height: 9px;
		flex: none;
		border-radius: 50%;
		transform: translateY(1px);
	}
	.d.fire .lab i {
		border-radius: 2px;
		background: var(--c-fire);
	}
	.d.act .lab i {
		background: var(--c-anadohoi);
	}
	.d.crews .lab i {
		background: color-mix(in srgb, var(--ink) 53.3%, black);
	}
	/* the second sponsor line aligns under the first without repeating
	   the mark */
	.lab i.ghost {
		background: none;
	}
	.val {
		min-width: 0;
		color: var(--ink-soft);
	}
	.d em {
		font-style: normal;
		color: var(--ink);
	}
	.d em a {
		color: inherit;
		text-decoration: none;
		border-bottom: 1px dotted var(--line-strong);
	}
	.d em a:hover {
		color: var(--c-anadohoi);
	}
	.d b {
		font-weight: 700;
		color: var(--c-anadohoi);
	}
	.cnames {
		min-width: 0;
		color: var(--ink);
		font-size: var(--fs-12);
	}
	.cnames a {
		color: inherit;
		text-decoration: none;
		border-bottom: 1px dotted var(--line-strong);
	}
	.cnames a:hover {
		color: var(--c-anadohoi);
	}
</style>
