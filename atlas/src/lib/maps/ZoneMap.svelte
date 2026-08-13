<script lang="ts">
	/** Compact map for a sponsor project's digitised works zone(s): the
	 *  Εύβοια outline with the project's zones highlighted and the other
	 *  works zones as faint context. Data loads post-hydration. */
	import { geoMercator, geoPath } from 'd3-geo';
	import type { Feature, FeatureCollection, Polygon, MultiPolygon } from 'geojson';
	import { grInt } from '$lib/transforms/format';
	import { loadEviaZones, loadPe, type FireProps, type PeProps, type ZoneProps } from './useGeo';

	interface Props {
		zones: string[];
		/** linked EFFIS burn-scar features (drawn under the zones) */
		scars?: Feature<Polygon | MultiPolygon, FireProps>[];
	}
	let { zones, scars = [] }: Props = $props();

	const W = 460;
	const H = 340;

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
	const selProps = $derived(view ? view.sel.map((f) => f.properties) : []);
</script>

{#if view && fc}
	<figure class="zonemap">
		<svg viewBox="0 0 {W} {H}" role="img" aria-label="Works zone of this project">
			{#each view.land as f (f.properties.pe)}
				<path d={view.path(f) ?? ''} class="land" />
			{/each}
			{#each scars as f (f.properties.id)}
				<path d={view.path(f) ?? ''} class="scar" />
			{/each}
			{#each fc.features as f (f.properties.zone)}
				<path d={view.path(f) ?? ''} class="ctxzone" />
			{/each}
			{#each view.sel as f (f.properties.zone)}
				<path d={view.path(f) ?? ''} class="selzone" />
			{/each}
		</svg>
		<figcaption>
			{#each selProps as z (z.zone)}
				<span class="zl"><i></i>{z.name} — {z.basin}
					({grInt(z.extracted_stremmata)} στρ. όπως ψηφιοποιήθηκε)</span>
			{/each}
			{#each scars as f (f.properties.id)}
				<span class="fl"><i></i>Αποτύπωμα πυρκαγιάς EFFIS {f.properties.yr} —
					{grInt(f.properties.ha)} εκτάρια ({f.properties.name})</span>
			{/each}
			<span class="src">Ζώνες έργων από τους χάρτες του Master Plan Β. Εύβοιας
				(4.1/4.2, Νοέμβριος 2021), ψηφιοποιημένες χειροκίνητα.</span>
			{#if scars.length}
				<span class="src">Περίμετροι πυρκαγιών: δορυφορικές εκτιμήσεις, όχι
					οριοθετήσεις — © European Union, Copernicus Emergency Management
					Service — EFFIS.</span>
			{/if}
		</figcaption>
	</figure>
{/if}

<style>
	.zonemap {
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
	.scar {
		fill: #6b2d35;
		fill-opacity: 0.14;
		stroke: #6b2d35;
		stroke-opacity: 0.55;
		stroke-width: 0.8;
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
	.ctxzone {
		fill: none;
		stroke: var(--c-anadohoi);
		stroke-opacity: 0.35;
		stroke-width: 0.7;
	}
	.selzone {
		fill: var(--c-anadohoi);
		fill-opacity: 0.4;
		stroke: var(--c-anadohoi);
		stroke-width: 1.4;
	}
	figcaption {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		margin-top: var(--sp-1);
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.zl i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		background: var(--c-anadohoi);
		opacity: 0.55;
		margin-right: 6px;
	}
	.src {
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
</style>
