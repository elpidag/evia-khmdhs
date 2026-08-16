<script lang="ts">
	/** Compact map for a sponsor project's digitised works zone(s): the
	 *  Εύβοια outline with the project's zones as GREEN OUTLINES drawn
	 *  above the solid fire fill (the fire stays visible through them),
	 *  plus the project's pinned work sites when it has both — ONE map,
	 *  never two. Hovering the fire shows date · ha (black top-left
	 *  card); zone outlines and site dots share the bottom-left card.
	 *  Data loads post-hydration. */
	import { geoMercator, geoPath } from 'd3-geo';
	import type { Feature, FeatureCollection, Polygon, MultiPolygon } from 'geojson';
	import { dmy, grInt } from '$lib/transforms/format';
	import { loadEviaZones, loadPe, type FireProps, type PeProps, type ZoneProps } from './useGeo';
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
	}
	let {
		zones,
		scars = [],
		height = 340,
		sites = [],
		pinColor = 'var(--c-anadohoi)',
		areaStremmata = null
	}: Props = $props();

	const W = 460;
	const H = $derived(height);
	const APPROX = new Set(['municipality', 'pe']);
	/** black hover cards: fire top-left; zones + sites share bottom-left */
	let fireTip = $state<string | null>(null);
	let zoneTip = $state<string | null>(null);
	let siteTip = $state<string | null>(null);

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let fc = $state.raw<FeatureCollection<Polygon | MultiPolygon, ZoneProps> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
		loadEviaZones(fetch).then((v) => (fc = v));
	});

	// the padded lon/lat frame + zone selection. With linked burn scars
	// the SCAR IS the frame (same rule as SiteMap): every card linked to
	// the same fire — the Β. Εύβοια 2021 scar — shares one identical
	// window that shows the whole scar plus its regional surroundings
	// (the ≥0.35°/0.27° pad floors keep the whole upper island in view);
	// zones/sites only extend it when they poke beyond the padding.
	const frameBox = $derived.by(() => {
		if (!fc) return null;
		const sel = fc.features.filter((f) => zones.includes(f.properties.zone));
		if (!sel.length) return null;
		const path0 = geoPath();
		let [gx0, gy0, gx1, gy1] = [Infinity, Infinity, -Infinity, -Infinity];
		for (const f of sel) {
			const b = path0.bounds(f); // lon/lat planar bounds
			gx0 = Math.min(gx0, b[0][0]); gy0 = Math.min(gy0, b[0][1]);
			gx1 = Math.max(gx1, b[1][0]); gy1 = Math.max(gy1, b[1][1]);
		}
		for (const s of sites) {
			gx0 = Math.min(gx0, s.lon); gy0 = Math.min(gy0, s.lat);
			gx1 = Math.max(gx1, s.lon); gy1 = Math.max(gy1, s.lat);
		}
		if (scars.length) {
			let [fx0, fy0, fx1, fy1] = [Infinity, Infinity, -Infinity, -Infinity];
			for (const f of scars) {
				const b = path0.bounds(f as Feature);
				fx0 = Math.min(fx0, b[0][0]); fy0 = Math.min(fy0, b[0][1]);
				fx1 = Math.max(fx1, b[1][0]); fy1 = Math.max(fy1, b[1][1]);
			}
			const px = Math.max((fx1 - fx0) * 0.18, 0.35);
			const py = Math.max((fy1 - fy0) * 0.18, 0.27);
			return {
				sel,
				X0: Math.min(fx0 - px, gx0 - 0.03),
				X1: Math.max(fx1 + px, gx1 + 0.03),
				Y0: Math.min(fy0 - py, gy0 - 0.03),
				Y1: Math.max(fy1 + py, gy1 + 0.03)
			};
		}
		const sx = gx1 - gx0;
		const sy = gy1 - gy0;
		const padx = Math.max(sx * 0.18, 0.35);
		const pady = Math.max(sy * 0.18, 0.27);
		return { sel, X0: gx0 - padx, X1: gx1 + padx, Y0: gy0 - pady, Y1: gy1 + pady };
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
		const frame = frameGeo(frameBox);
		const proj = geoMercator();
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
</script>

{#if view && fc}
	<figure class="zonemap">
		<div class="mapbox">
		<svg viewBox="0 0 {W} {H}" role="img" aria-label="Works zone of this project">
			{#each view.land as f (f.properties.pe)}
				<path d={view.path(f) ?? ''} class="land" />
			{/each}
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
						(siteTip = `announced area, drawn schematically — ${grInt(areaStremmata ?? 0)} στρ.`)}
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
							(s.stremmata ? ` — ${grInt(s.stremmata)} στρ.` : '') +
							(APPROX.has(s.geo_precision ?? '') ? ' (κατά προσέγγιση)' : ''))}
					onmouseleave={() => (siteTip = null)}
				/>
			{/each}
		</svg>
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
		border: none;
		border-radius: 4px;
	}
	.land {
		fill: #fff;
		stroke: var(--line);
		stroke-width: 0.7;
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
