<script lang="ts">
	/** EFFIS burnt-scar polygons, coloured by fire year on a gradient
	 *  into the base maroon — older fires pale, recent ones saturated.
	 *  Perimeters are satellite rapid-mapping estimates, not official
	 *  οριοθετήσεις; attribution belongs on the hosting section. */
	import type { Feature, Polygon, MultiPolygon } from 'geojson';
	import type { MapCtx } from './PaperMap.svelte';
	import type { FireProps } from './useGeo';

	interface Props {
		ctx: MapCtx;
		features: Feature<Polygon | MultiPolygon, FireProps>[];
		/** deepest colour (the most recent year) */
		base?: string;
		/** one flat colour for every scar, whatever its year — the card's
		 *  map is too small for a year ramp to be read (user, 2026-08-27) */
		flat?: boolean;
		tipOf?: (f: Feature<Polygon | MultiPolygon, FireProps>) => string;
	}
	let { ctx, features, base = '#6b2d35', flat = false, tipOf }: Props = $props();

	const years = $derived.by(() => {
		let lo = Infinity,
			hi = -Infinity;
		for (const f of features) {
			lo = Math.min(lo, f.properties.yr);
			hi = Math.max(hi, f.properties.yr);
		}
		return { lo, hi: Math.max(hi, lo + 1) };
	});

	/** base colour mixed towards white: t=0 → 88% white, t=1 → full base */
	const rgb = $derived.by(() => {
		const m = /^#?([0-9a-f]{6})$/i.exec(base);
		const v = parseInt(m ? m[1] : '6b2d35', 16);
		return [(v >> 16) & 255, (v >> 8) & 255, v & 255] as const;
	});
	function yearColor(yr: number): string {
		if (flat) return base;
		const t = 0.12 + (0.88 * (yr - years.lo)) / (years.hi - years.lo);
		const [r, g, b] = rgb.map((c) => Math.round(255 + (c - 255) * t));
		return `rgb(${r},${g},${b})`;
	}
</script>

{#each features as f, i (i)}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<path
		d={ctx.path(f) ?? ''}
		class="fire"
		fill={yearColor(f.properties.yr)}
		onmouseenter={() => tipOf && ctx.showTip(tipOf(f))}
		onmouseleave={() => ctx.hideTip()}
	/>
{/each}

<style>
	.fire {
		fill-opacity: 0.85;
		stroke: none;
	}
	.fire:hover {
		fill-opacity: 1;
		stroke: #000;
		stroke-width: 0.6;
		vector-effect: non-scaling-stroke;
	}
</style>
