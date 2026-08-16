<script lang="ts">
	/** Compact map for a sponsor project's digitised works zone(s): the
	 *  Εύβοια outline with the project's zones as GREEN OUTLINES drawn
	 *  above the solid fire fill (the fire stays visible through them);
	 *  hovering the fire shows its date · ha, hovering a zone outline
	 *  names it — both in the black top-left card. Data loads
	 *  post-hydration. */
	import { geoMercator, geoPath } from 'd3-geo';
	import type { Feature, FeatureCollection, Polygon, MultiPolygon } from 'geojson';
	import { dmy, grInt } from '$lib/transforms/format';
	import { loadEviaZones, loadPe, type FireProps, type PeProps, type ZoneProps } from './useGeo';

	interface Props {
		/** svg viewBox height — the detail template asks for a taller map */
		height?: number;
		zones: string[];
		/** linked EFFIS burn-scar features (drawn under the zones) */
		scars?: Feature<Polygon | MultiPolygon, FireProps>[];
	}
	let { zones, scars = [], height = 340 }: Props = $props();

	const W = 460;
	const H = $derived(height);
	/** black hover cards: fire top-left, zone bottom-left */
	let fireTip = $state<string | null>(null);
	let zoneTip = $state<string | null>(null);

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let fc = $state.raw<FeatureCollection<Polygon | MultiPolygon, ZoneProps> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
		loadEviaZones(fetch).then((v) => (fc = v));
	});

	const view = $derived.by(() => {
		if (!pe || !fc) return null;
		const sel = fc.features.filter((f) => zones.includes(f.properties.zone));
		if (!sel.length) return null;
		// fit on the selection's bbox expanded ~65% for context
		const path0 = geoPath();
		let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
		for (const f of sel) {
			const b = path0.bounds(f); // lon/lat planar bounds
			x0 = Math.min(x0, b[0][0]); y0 = Math.min(y0, b[0][1]);
			x1 = Math.max(x1, b[1][0]); y1 = Math.max(y1, b[1][1]);
		}
		const padx = (x1 - x0) * 0.65 + 0.01;
		const pady = (y1 - y0) * 0.65 + 0.01;
		// ring wound CLOCKWISE — d3-geo spherical polygons invert otherwise
		const frame = {
			type: 'Polygon' as const,
			coordinates: [[[x0 - padx, y0 - pady], [x0 - padx, y1 + pady],
				[x1 + padx, y1 + pady], [x1 + padx, y0 - pady],
				[x0 - padx, y0 - pady]]]
		};
		const proj = geoMercator();
		proj.fitExtent([[6, 6], [W - 6, H - 6]], frame);
		const path = geoPath(proj);
		const land = pe.features.filter((f) =>
			JSON.stringify(f.properties).includes('Ευβοίας'));
		return { path, sel, land };
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
			{#each fc.features as f (f.properties.zone)}
				<path d={view.path(f) ?? ''} class="ctxzone" />
			{/each}
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
		</svg>
		{#if fireTip}
			<div class="tip">{fireTip}</div>
		{/if}
		{#if zoneTip}
			<div class="tip zonecard">{zoneTip}</div>
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
	.ctxzone {
		fill: none;
		stroke: var(--c-anadohoi);
		stroke-opacity: 0.35;
		stroke-width: 0.7;
		pointer-events: none;
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
