<script lang="ts">
	/** Quiet polygon layer for the digitised works zones — drawn under the
	 *  project dots as geographic context; tooltip is convenience only. */
	import type { Feature, Polygon, MultiPolygon } from 'geojson';
	import type { MapCtx } from './PaperMap.svelte';
	import type { ZoneProps } from './useGeo';

	interface Props {
		ctx: MapCtx;
		features: Feature<Polygon | MultiPolygon, ZoneProps>[];
		tipOf?: (f: Feature<Polygon | MultiPolygon, ZoneProps>) => string;
	}
	let { ctx, features, tipOf }: Props = $props();
</script>

{#each features as f (f.properties.zone)}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<path
		d={ctx.path(f) ?? ''}
		class="zone"
		onmouseenter={() => tipOf && ctx.showTip(tipOf(f))}
		onmouseleave={() => ctx.hideTip()}
	/>
{/each}

<style>
	.zone {
		fill: var(--c-anadohoi);
		fill-opacity: 0.13;
		stroke: var(--c-anadohoi);
		stroke-width: 0.8;
		vector-effect: non-scaling-stroke;
	}
	.zone:hover {
		fill-opacity: 0.28;
	}
</style>
