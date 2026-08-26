<script lang="ts">
	/** Compact map for a sponsor project's digitised works zone(s): the
	 *  Εύβοια outline with the project's zones as GREEN OUTLINES drawn
	 *  above the solid fire fill (the fire stays visible through them),
	 *  plus the project's pinned work sites when it has both — ONE map,
	 *  never two. Hovering the fire shows date · ha (black top-left
	 *  card); zone outlines and site dots share the bottom-left card.
	 *  Data loads post-hydration. */
	import { geoContains, geoMercator, geoPath } from 'd3-geo';
	import type { Feature, FeatureCollection, Polygon, MultiPolygon } from 'geojson';
	import { dmy, grInt } from '$lib/transforms/format';
	import {
		loadEviaZones,
		loadNeighbours,
		loadPe,
		nearParts,
		type FireProps,
		type NeighbourProps,
		type PeProps,
		type ZoneProps
	} from './useGeo';
	import type { SitePin } from './SiteMap.svelte';

	interface Props {
		/** svg viewBox height — the detail template asks for a taller map */
		height?: number;
		zones: string[];
		/** linked EFFIS burn-scar features (drawn under the zones) */
		scars?: Feature<Polygon | MultiPolygon, FireProps>[];
		/** pinned work sites, drawn over the zones (SiteMap conventions:
		 *  one colour, true-size when a στρέμματα figure exists) */
		sites?: SitePin[];
		/** pin fill — the project's timeline-bar colour */
		pinColor?: string;
		/** announced intervention area (στρέμματα): with exactly two pinned
		 *  sites, a SCHEMATIC dashed capsule containing both is drawn at
		 *  this true area — the smallest such shape; boundaries invented,
		 *  size and anchors documented */
		areaStremmata?: number | null;
	/** the project's own Π.Ε. name(s) — always framed whole */
		pes?: string[];
	}
	let {
		zones,
		scars = [],
		height = 340,
		sites = [],
		pinColor = 'var(--c-anadohoi)',
		areaStremmata = null,
		pes = []
	}: Props = $props();

	const W = 460;
	const H = $derived(height);
	const APPROX = new Set(['municipality', 'pe']);
	/** black hover cards: fire top-left; zones + sites share bottom-left */
	let fireTip = $state<string | null>(null);
	let zoneTip = $state<string | null>(null);
	let siteTip = $state<string | null>(null);

	/** zoom state: k = magnification, dx/dy = frame-centre offset (degrees) */
	let zoom = $state({ k: 1, dx: 0, dy: 0 });
	let svgEl = $state<SVGSVGElement | null>(null);
	let dragging = false;

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let fc = $state.raw<FeatureCollection<Polygon | MultiPolygon, ZoneProps> | null>(null);
	/** context land (neighbours + Athos) + the dashed Greek land border */
	let land = $state.raw<FeatureCollection<
		Polygon | MultiPolygon | GeoJSON.MultiLineString,
		NeighbourProps
	> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
		loadEviaZones(fetch).then((v) => (fc = v));
		loadNeighbours(fetch).then((v) => (land = v));
	});

	// the padded lon/lat frame + zone selection. With linked burn scars
	// the SCAR IS the frame (same rule as SiteMap): every card linked to
	// the same fire — the Β. Εύβοια 2021 scar — shares one identical
	// window that shows the whole scar plus its regional surroundings
	// (the ≥0.35°/0.27° pad floors keep the whole upper island in view);
	// zones/sites only extend it when they poke beyond the padding.
	const frameBox = $derived.by(() => {
		if (!fc || !pe) return null;
		const sel = fc.features.filter((f) => zones.includes(f.properties.zone));
		if (!sel.length) return null;
		const path0 = geoPath();
		let [gx0, gy0, gx1, gy1] = [Infinity, Infinity, -Infinity, -Infinity];
		const grow = (x0: number, y0: number, x1: number, y1: number) => {
			gx0 = Math.min(gx0, x0); gy0 = Math.min(gy0, y0);
			gx1 = Math.max(gx1, x1); gy1 = Math.max(gy1, y1);
		};
		for (const f of [...sel, ...scars]) {
			const b = path0.bounds(f as Feature); // planar lon/lat bounds
			grow(b[0][0], b[0][1], b[1][0], b[1][1]);
		}
		for (const s of sites) grow(s.lon, s.lat, s.lon, s.lat);
		// THE FRAME IS THE REGIONAL UNIT(S) (user, 2026-08-25; same rule as
		// SiteMap): the Π.Ε. containing the zones/scars — plus the project's
		// own — appear WHOLE; for the Εύβοια zones that is the whole island
		const seen = new Set<string>();
		const homePes: Feature<MultiPolygon, PeProps>[] = [];
		const addPe = (f?: Feature<MultiPolygon, PeProps>) => {
			if (f && !seen.has(f.properties.pe)) {
				seen.add(f.properties.pe);
				homePes.push(f);
			}
		};
		for (const name of pes) addPe(pe.features.find((f) => f.properties.pe === name));
		for (const f of [...sel, ...scars]) {
			const c = path0.centroid(f as Feature);
			if (Number.isFinite(c[0]))
				addPe(pe.features.find((g) => geoContains(g, c as [number, number])));
		}
		for (const s of sites) addPe(pe.features.find((f) => geoContains(f, [s.lon, s.lat])));
		if (homePes.length) {
			// only the parts of the Π.Ε. that belong with the zones/scars
			// (SiteMap's rule; user, 2026-08-26)
			const subject: [number, number, number, number] | null = Number.isFinite(gx0)
				? [gx0, gy0, gx1, gy1]
				: null;
			for (const f of homePes) {
				const b = path0.bounds(nearParts(f, subject) as Feature);
				grow(b[0][0], b[0][1], b[1][0], b[1][1]);
			}
		}
		const padScale = homePes.length ? 0.05 : 0.18;
		const padx = Math.max((gx1 - gx0) * padScale, homePes.length ? 0.05 : 0.35);
		const pady = Math.max((gy1 - gy0) * padScale, homePes.length ? 0.04 : 0.27);
		return {
			sel,
			cx: (gx0 + gx1) / 2,
			cy: (gy0 + gy1) / 2,
			hx: (gx1 - gx0) / 2 + padx,
			hy: (gy1 - gy0) / 2 + pady
		};
	});

	/** frame polygon, wound CLOCKWISE — d3-geo spherical polygons invert otherwise */
	function frameGeo(fb: { X0: number; X1: number; Y0: number; Y1: number }) {
		return {
			type: 'Polygon' as const,
			coordinates: [[[fb.X0, fb.Y0], [fb.X0, fb.Y1], [fb.X1, fb.Y1],
				[fb.X1, fb.Y0], [fb.X0, fb.Y0]]]
		};
	}

	const view = $derived.by(() => {
		if (!pe || !frameBox) return null;
		const { sel } = frameBox;
		const cx = frameBox.cx + zoom.dx;
		const cy = frameBox.cy + zoom.dy;
		const hx = frameBox.hx / zoom.k;
		const hy = frameBox.hy / zoom.k;
		const frame = frameGeo({ X0: cx - hx, X1: cx + hx, Y0: cy - hy, Y1: cy + hy });
		const proj = geoMercator();
		// one both-dims fit: the whole Π.Ε. must show (user, 2026-08-25)
		proj.fitExtent([[6, 6], [W - 6, H - 6]], frame);
		const path = geoPath(proj);
		// all Π.Ε. polygons — the whole-scar frame reaches the mainland
		// coast across the strait, which must not render as open sea
		const land = pe.features;
		// site pins, SiteMap conventions: base radius, true ground size
		// where a document states the area (1 στρ = 1,000 m²)
		const baseR = sites.length > 8 ? 4.5 : 6;
		const pins = sites
			.map((s) => {
				const xy = proj([s.lon, s.lat]);
				if (!xy) return null;
				let r = baseR;
				if (s.stremmata && s.stremmata > 0) {
					const rM = Math.sqrt((s.stremmata * 1000) / Math.PI);
					const dLon = rM / (111320 * Math.cos((s.lat * Math.PI) / 180));
					const xy2 = proj([s.lon + dLon, s.lat]);
					if (xy2) r = Math.max(Math.abs(xy2[0] - xy[0]), baseR);
				}
				return { s, x: xy[0], y: xy[1], r };
			})
			.filter((d): d is { s: SitePin; x: number; y: number; r: number } => d !== null);

		// schematic announced-area capsule: with exactly TWO pins and a
		// stated total area, the smallest region containing both at that
		// area is the capsule around their segment — π r² + 2 r L = A
		let capsule: { x1: number; y1: number; x2: number; y2: number; rpx: number } | null = null;
		if (pins.length === 2 && areaStremmata && areaStremmata > 0) {
			const [a, b] = sites;
			const midLat = ((a.lat + b.lat) / 2) * (Math.PI / 180);
			const mPerLon = 111320 * Math.cos(midLat);
			const Lm = Math.hypot((b.lon - a.lon) * mPerLon, (b.lat - a.lat) * 111320);
			const A = areaStremmata * 1000; // m²
			const rM = (-Lm + Math.sqrt(Lm * Lm + Math.PI * A)) / Math.PI;
			// metres → px at this projection (same conversion as the pins)
			const p1 = proj([a.lon, a.lat]);
			const p2 = proj([a.lon + rM / mPerLon, a.lat]);
			if (p1 && p2) {
				capsule = {
					x1: pins[0].x, y1: pins[0].y, x2: pins[1].x, y2: pins[1].y,
					rpx: Math.abs(p2[0] - p1[0])
				};
			}
		}
		return { path, sel, land, pins, capsule };
	});

	const zoomIn = () => (zoom = { ...zoom, k: Math.min(16, zoom.k * 1.6) });
	const zoomOut = () => {
		const k = Math.max(1, zoom.k / 1.6);
		zoom = k === 1 ? { k: 1, dx: 0, dy: 0 } : { ...zoom, k };
	};
	const home = () => (zoom = { k: 1, dx: 0, dy: 0 });

	function onPointerDown(e: PointerEvent) {
		if (zoom.k <= 1) return;
		dragging = true;
		(e.currentTarget as Element).setPointerCapture(e.pointerId);
	}
	function onPointerMove(e: PointerEvent) {
		if (!dragging || !svgEl || !frameBox) return;
		const unitPerPx = W / svgEl.clientWidth; // css px → viewBox units
		const degX = (2 * frameBox.hx) / zoom.k / (W - 12);
		const degY = (2 * frameBox.hy) / zoom.k / (H - 12);
		zoom = {
			k: zoom.k,
			dx: zoom.dx - e.movementX * unitPerPx * degX,
			dy: zoom.dy + e.movementY * unitPerPx * degY
		};
	}
	function onPointerUp() {
		dragging = false;
	}
</script>

{#if view && fc}
	<figure class="zonemap">
		<div class="mapbox">
		<!-- svelte-ignore a11y_no_static_element_interactions, a11y_no_noninteractive_element_interactions -->
		<svg
			bind:this={svgEl}
			viewBox="0 0 {W} {H}"
			role="img"
			aria-label="Works zone of this project"
			class:grab={zoom.k > 1}
			onpointerdown={onPointerDown}
			onpointermove={onPointerMove}
			onpointerup={onPointerUp}
			onpointercancel={onPointerUp}
		>
			{#if land}
				<!-- context land first: the Greek polygons paint over the overlap -->
				{#each land.features as f, i (i)}
					{#if f.properties.kind !== 'border'}
						<path class="context" d={view.path(f) ?? ''} />
					{/if}
				{/each}
			{/if}
			{#each view.land as f (f.properties.pe)}
				<path d={view.path(f) ?? ''} class="land" />
			{/each}
			{#if land}
				<!-- the dashed Greek land border, PaperMap's convention -->
				{#each land.features as f, i (i)}
					{#if f.properties.kind === 'border'}
						<path class="gr-border" d={view.path(f) ?? ''} />
					{/if}
				{/each}
			{/if}
			{#each scars as f (f.properties.id)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<path
					d={view.path(f) ?? ''}
					class="scar"
					onmouseenter={() =>
						(fireTip = `${f.properties.d ? dmy(f.properties.d) : f.properties.yr} · ${grInt(f.properties.ha)} ha`)}
					onmouseleave={() => (fireTip = null)}
				/>
			{/each}
			<!-- ONLY the project's own zone(s) — no context zones -->
			{#each view.sel as f (f.properties.zone)}
				<path d={view.path(f) ?? ''} class="selzone" />
			{/each}
			<!-- invisible wide-stroke twins make the thin outlines hoverable
			     WITHOUT stealing the interior from the fire's own hover -->
			{#each view.sel as f (`hit:${f.properties.zone}`)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<path
					d={view.path(f) ?? ''}
					class="zonehit"
					onmouseenter={() => (zoneTip = `${f.properties.name} — ${f.properties.basin}`)}
					onmouseleave={() => (zoneTip = null)}
				/>
			{/each}
			{#if view.capsule}
				{@const c = view.capsule}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<line
					x1={c.x1}
					y1={c.y1}
					x2={c.x2}
					y2={c.y2}
					class="capsule"
					style:stroke={pinColor}
					stroke-width={2 * c.rpx}
					onmouseenter={() =>
						(siteTip = `announced area, drawn schematically — ${grInt(areaStremmata ?? 0)} stremmata`)}
					onmouseleave={() => (siteTip = null)}
				/>
			{/if}
			{#each view.pins as { s, x, y, r }, i (i)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<circle
					cx={x}
					cy={y}
					{r}
					class="pin"
					style:fill={pinColor}
					onmouseenter={() =>
						(siteTip =
							s.name +
							(s.stremmata ? ` — ${grInt(s.stremmata)} stremmata` : '') +
							(APPROX.has(s.geo_precision ?? '') ? ' (approximate)' : ''))}
					onmouseleave={() => (siteTip = null)}
				/>
			{/each}
		</svg>
		<!-- controls on EVERY map (user, 2026-08-25) -->
		<div class="zoomctl">
			<button onclick={zoomIn} title="Zoom in" aria-label="Zoom in"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M5 1h2v4h4v2H7v4H5V7H1V5h4z" fill="currentColor"/></svg></button>
			<button onclick={zoomOut} title="Zoom out" aria-label="Zoom out"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M1 5h10v2H1z" fill="currentColor"/></svg></button>
			<button onclick={home} title="Reset view" aria-label="Reset view"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M6 1l4.4 3.4V11H1.6V4.4z" fill="currentColor"/></svg></button>
		</div>
		{#if fireTip}
			<div class="tip">{fireTip}</div>
		{/if}
		{#if siteTip ?? zoneTip}
			<div class="tip zonecard">{siteTip ?? zoneTip}</div>
		{/if}
		</div>
		<!-- zone names live in the hover cards; provenance (Evia Forest
		     Directorate sheets + pdf links) lives in the FactsHeader caveat -->
	</figure>
{/if}

<style>
	.zonemap {
		margin: 0 0 var(--sp-2);
		max-width: 460px;
	}
	/* cards anchor to the MAP box, never over the caption below it */
	.mapbox {
		position: relative;
	}
	/* same palette as the sponsored-works overview map:
	   grey sea, white land, --line strokes */
	svg {
		width: 100%;
		height: auto;
		display: block;
		background: #f2f2f2;
		/* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
		border: 1px solid var(--line);
		border-radius: 4px;
	touch-action: none;
	}
	svg.grab {
		cursor: grab;
	}
	.land {
		fill: #fff;
		stroke: var(--line);
		stroke-width: 0.7;
	}
	/* the context land and the dashed Greek land border — PaperMap's
	   conventions (user, 2026-08-25: a border frame without them read as
	   if the neighbouring country were open sea) */
	.context {
		fill: #fff;
		stroke: #c4c4c4;
		stroke-width: 0.5;
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}
	.gr-border {
		fill: none;
		stroke: var(--ink);
		stroke-width: 0.9;
		stroke-dasharray: 4 3;
		stroke-linecap: butt;
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}

	/* solid fire tone, same as SiteMap — no alpha */
	.scar {
		fill: color-mix(in srgb, #6b2d35 85%, #fff);
		stroke: #6b2d35;
		stroke-width: 0.8;
	}
	/* the project's zones: green OUTLINE above the fire fill — no fill,
	   so the fire stays visible and hoverable through them */
	.selzone {
		fill: none;
		stroke: var(--c-anadohoi);
		stroke-width: 1.8;
		pointer-events: none;
	}
	.zonehit {
		fill: none;
		stroke: transparent;
		stroke-width: 9;
		pointer-events: stroke;
	}
	.pin {
		stroke: none;
	}
	/* the schematic announced-area corridor: translucent, round-capped */
	.capsule {
		stroke-linecap: round;
		opacity: 0.45;
	}
	.capsule:hover {
		opacity: 0.7;
	}
	.zoomctl {
		position: absolute;
		top: var(--sp-2);
		right: var(--sp-2);
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.zoomctl button {
		font: inherit;
		line-height: 0;
		width: 1.45rem;
		height: 1.45rem;
		padding: 0;
		display: grid;
		place-items: center;
		border: none;
		border-radius: 50%;
		background: var(--map-accent, var(--c-anadohoi));
		color: #fff;
		cursor: pointer;
	}
	.zoomctl button:hover {
		opacity: 0.82;
	}
	.zoomctl button svg {
		width: 9.5px;
		height: 9.5px;
		display: block;
		/* undo the component's map-svg dress on the glyphs */
		background: none;
		border: none;
		border-radius: 0;
	}
	.tip {
		position: absolute;
		top: var(--sp-2);
		left: var(--sp-2);
		background: #000;
		color: #fff;
		border-radius: 4px;
		padding: var(--sp-1) var(--sp-2);
		font-size: var(--fs-13);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}
	/* zone card: bottom-left, at most half the map wide — wraps to two
	   rows rather than spanning the frame */
	.tip.zonecard {
		top: auto;
		bottom: var(--sp-2);
		max-width: 50%;
	}
</style>
