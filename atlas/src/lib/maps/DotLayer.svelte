<script lang="ts">
	import type { MapCtx } from './PaperMap.svelte';

	export interface DotPoint {
		lat: number;
		lon: number;
		[key: string]: unknown;
	}

	interface Props {
		ctx: MapCtx;
		points: DotPoint[];
		r?: number | ((p: DotPoint) => number);
		fillOf?: (p: DotPoint) => string;
		stroke?: string;
		tipOf?: (p: DotPoint) => string;
		hrefOf?: (p: DotPoint) => string | null;
		opacity?: number;
		onOver?: (p: DotPoint, e?: MouseEvent) => void;
		onOut?: (p: DotPoint) => void;
		/** externally-driven highlight (e.g. hovering the paired chart) */
		hotOf?: (p: DotPoint) => boolean;
		/** per-dot stroke-dasharray (e.g. approximate-location dots) */
		dashOf?: (p: DotPoint) => string | undefined;
		/** per-dot fill opacity override (approximate dots render lighter) */
		fillOpacityOf?: (p: DotPoint) => number | undefined;
	}

	let {
		ctx,
		points,
		r = 4,
		fillOf = () => 'var(--accent)',
		stroke = 'rgba(42,33,24,.45)',
		tipOf,
		hrefOf,
		opacity = 0.85,
		onOver,
		onOut,
		hotOf,
		dashOf,
		fillOpacityOf
	}: Props = $props();

	function enter(p: DotPoint, e?: MouseEvent) {
		if (tipOf) ctx.showTip(tipOf(p));
		onOver?.(p, e);
	}
	function leave(p: DotPoint) {
		if (tipOf) ctx.hideTip();
		onOut?.(p);
	}

	const placed = $derived(
		points
			.map((p) => {
				const xy = ctx.projection([
					(p.lon2 as number) ?? p.lon,
					(p.lat2 as number) ?? p.lat
				]);
				return xy ? { p, x: xy[0], y: xy[1] } : null;
			})
			.filter((d): d is { p: DotPoint; x: number; y: number } => d !== null)
	);

	function radius(p: DotPoint): number {
		return (typeof r === 'function' ? r(p) : r) / ctx.k;
	}
</script>

{#each placed as { p, x, y }, i (i)}
	{@const href = hrefOf?.(p) ?? null}
	{@const hot = hotOf?.(p) ?? false}
	{#if href}
		<a {href} aria-label={String(p.name ?? p.title ?? p.ref ?? href)}>
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={x}
				cy={y}
				r={radius(p) * (hot ? 1.5 : 1)}
				fill={fillOf(p)}
				fill-opacity={fillOpacityOf?.(p)}
				stroke={hot ? 'var(--ink)' : stroke}
				stroke-width={(hot ? 1.8 : 0.8) / ctx.k}
				stroke-dasharray={dashOf?.(p)}
				opacity={hot ? 1 : opacity}
				onmouseenter={(e) => enter(p, e)}
				onmouseleave={() => leave(p)}
			/>
		</a>
	{:else}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<circle
			cx={x}
			cy={y}
			r={radius(p) * (hot ? 1.5 : 1)}
			fill={fillOf(p)}
			fill-opacity={fillOpacityOf?.(p)}
			stroke={hot ? 'var(--ink)' : stroke}
			stroke-width={(hot ? 1.8 : 0.8) / ctx.k}
			stroke-dasharray={dashOf?.(p)}
			opacity={hot ? 1 : opacity}
			onmouseenter={(e) => enter(p, e)}
			onmouseleave={() => leave(p)}
		/>
	{/if}
{/each}

<style>
	circle {
		transition: opacity 0.1s;
	}
	circle:hover {
		opacity: 1;
	}
</style>
