<script lang="ts">
	/** Compact map for a sponsor project's curated work site(s): the
	 *  containing Π.Ε. outline(s) with one dot per site, labelled.
	 *  Approximate sites (municipality-centre pins) render dashed.
	 *  Optionally draws the project's linked EFFIS burn scar(s) under the
	 *  pins (satellite estimates — attribution printed in the caption);
	 *  renders scar-only when the project has scars but no pinned sites. */
	import { geoMercator, geoPath } from 'd3-geo';
	import { grInt } from '$lib/transforms/format';
	import { loadPe, type FireProps, type PeProps } from './useGeo';
	import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson';

	export interface SitePin {
		name: string;
		lat: number;
		lon: number;
		geo_precision?: string | null;
		municipality?: string | null;
	}
	interface Props {
		/** svg viewBox height — the detail template asks for a taller map */
		height?: number;
		sites: SitePin[];
		/** linked EFFIS burn-scar features (already filtered by id) */
		scars?: Feature<Polygon | MultiPolygon, FireProps>[];
	}
	let { sites, scars = [], height = 340 }: Props = $props();

	const W = 460;
	const H = $derived(height);
	const APPROX = new Set(['municipality', 'pe']);

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
	});

	const view = $derived.by(() => {
		if (!pe || (!sites.length && !scars.length)) return null;
		let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
		for (const s of sites) {
			x0 = Math.min(x0, s.lon);
			y0 = Math.min(y0, s.lat);
			x1 = Math.max(x1, s.lon);
			y1 = Math.max(y1, s.lat);
		}
		// linked burn scars extend the frame (lon/lat planar bounds)
		const path0 = geoPath();
		for (const f of scars) {
			const b = path0.bounds(f);
			x0 = Math.min(x0, b[0][0]);
			y0 = Math.min(y0, b[0][1]);
			x1 = Math.max(x1, b[1][0]);
			y1 = Math.max(y1, b[1][1]);
		}
		// pad proportionally; single-site maps get a fixed ~30 km half-window
		// so a slice of the surrounding region stays in frame
		const padx = Math.max((x1 - x0) * 0.18, 0.35);
		const pady = Math.max((y1 - y0) * 0.18, 0.27);
		// ring wound CLOCKWISE — d3-geo spherical polygons invert otherwise
		const frame = {
			type: 'Polygon' as const,
			coordinates: [
				[
					[x0 - padx, y0 - pady],
					[x0 - padx, y1 + pady],
					[x1 + padx, y1 + pady],
					[x1 + padx, y0 - pady],
					[x0 - padx, y0 - pady]
				]
			]
		};
		const proj = geoMercator();
		proj.fitExtent(
			[
				[6, 6],
				[W - 6, H - 6]
			],
			frame
		);
		const path = geoPath(proj);
		const pins = sites
			.map((s) => {
				const xy = proj([s.lon, s.lat]);
				return xy ? { s, x: xy[0], y: xy[1] } : null;
			})
			.filter((d): d is { s: SitePin; x: number; y: number } => d !== null);
		return { path, pins };
	});
</script>

{#if view}
	<figure class="sitemap">
		<svg viewBox="0 0 {W} {H}" role="img" aria-label="Work locations of this project">
			{#if pe}
				{#each pe.features as f (f.properties.pe)}
					<path d={view.path(f) ?? ''} class="land" />
				{/each}
			{/if}
			{#each scars as f (f.properties.id)}
				<path d={view.path(f) ?? ''} class="scar" />
			{/each}
			{#if view.pins.length > 1}
				{#each view.pins as a, i (i)}
					{#each view.pins.slice(i + 1) as b, j (j)}
						<line x1={a.x} y1={a.y} x2={b.x} y2={b.y} class="link" />
					{/each}
				{/each}
			{/if}
			{#each view.pins as { s, x, y }, i (i)}
				<circle cx={x} cy={y} r="6" class="pin" class:approx={APPROX.has(s.geo_precision ?? '')} />
				<text {x} y={y - 10} class="lbl">{s.name}</text>
			{/each}
		</svg>
		<!-- site names label their own pins; the sourcing note lives in the
		     FactsHeader caveat — only scar data + its estimates caveat remain -->
		{#if scars.length}
			<figcaption>
				{#each scars as f (f.properties.id)}
					<span class="fl"
						><i></i>Αποτύπωμα πυρκαγιάς EFFIS {f.properties.yr} — {grInt(f.properties.ha)} εκτάρια
						({f.properties.name})</span
					>
				{/each}
				<span class="src"
					>Περίμετροι πυρκαγιών: δορυφορικές εκτιμήσεις, όχι οριοθετήσεις — © European Union,
					Copernicus Emergency Management Service — EFFIS.</span
				>
			</figcaption>
		{/if}
	</figure>
{/if}

<style>
	.sitemap {
		margin: var(--sp-3) 0 var(--sp-2);
		max-width: 460px;
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
	.scar {
		fill: #6b2d35;
		fill-opacity: 0.14;
		stroke: #6b2d35;
		stroke-opacity: 0.55;
		stroke-width: 0.8;
	}
	.link {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 5 4;
		opacity: 0.55;
	}
	.pin {
		fill: var(--c-anadohoi);
		fill-opacity: 0.85;
		stroke: #fff;
		stroke-width: 1.4;
	}
	.pin.approx {
		fill-opacity: 0.4;
		stroke: var(--c-anadohoi);
		stroke-dasharray: 2.5 2;
	}
	.lbl {
		font-size: 11px;
		fill: var(--ink);
		text-anchor: middle;
		paint-order: stroke;
		stroke: #fff;
		stroke-width: 2.5px;
		font-weight: 600;
	}
	figcaption {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		margin-top: var(--sp-1);
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.fl i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		background: #6b2d35;
		opacity: 0.35;
		border: 1px solid #6b2d35;
		margin-right: 6px;
	}
	.src {
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
</style>
