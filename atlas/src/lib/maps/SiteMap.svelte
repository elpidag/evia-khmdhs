<script lang="ts">
	/** Compact map for a sponsor project's curated work site(s): the
	 *  containing Π.Ε. outline(s) with one dot per site, labelled.
	 *  Approximate sites (municipality-centre pins) render dashed. */
	import { geoMercator, geoPath } from 'd3-geo';
	import { loadPe, type PeProps } from './useGeo';
	import type { FeatureCollection, MultiPolygon } from 'geojson';

	export interface SitePin {
		name: string;
		lat: number;
		lon: number;
		geo_precision?: string | null;
		municipality?: string | null;
	}
	interface Props {
		sites: SitePin[];
	}
	let { sites }: Props = $props();

	const W = 460;
	const H = 340;
	const APPROX = new Set(['municipality', 'pe']);

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
	});

	const view = $derived.by(() => {
		if (!pe || !sites.length) return null;
		let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
		for (const s of sites) {
			x0 = Math.min(x0, s.lon);
			y0 = Math.min(y0, s.lat);
			x1 = Math.max(x1, s.lon);
			y1 = Math.max(y1, s.lat);
		}
		// pad generously; single-site maps get a fixed ~14 km half-window
		const padx = Math.max((x1 - x0) * 0.6, 0.13);
		const pady = Math.max((y1 - y0) * 0.6, 0.1);
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
		<figcaption>
			{#each sites as s, i (i)}
				<span class="sl"
					><i class:approx={APPROX.has(s.geo_precision ?? '')}></i>{s.name}{s.municipality
						? ` — Δ. ${s.municipality}`
						: ''}{APPROX.has(s.geo_precision ?? '') ? ' (κέντρο δήμου, κατά προσέγγιση)' : ''}</span
				>
			{/each}
			<span class="src"
				>Θέσεις όπως τις ονομάζουν οι πράξεις· ο γεωεντοπισμός τεκμηριώνεται ανά θέση
				(methodology).</span
			>
		</figcaption>
	</figure>
{/if}

<style>
	.sitemap {
		margin: var(--sp-3) 0 var(--sp-2);
		max-width: 460px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		background: #e8f1f5;
		border: 1px solid var(--line);
		border-radius: 4px;
	}
	.land {
		fill: var(--paper-2);
		stroke: var(--line-strong);
		stroke-width: 0.7;
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
	.sl i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--c-anadohoi);
		opacity: 0.85;
		margin-right: 6px;
	}
	.sl i.approx {
		opacity: 0.4;
		outline: 1px dashed var(--c-anadohoi);
	}
	.src {
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
</style>
