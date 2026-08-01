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
		onOver?: (p: DotPoint) => void;
		onOut?: (p: DotPoint) => void;
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
		onOut
	}: Props = $props();

	function enter(p: DotPoint) {
		if (tipOf) ctx.showTip(tipOf(p));
		onOver?.(p);
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
	{#if href}
		<a {href} aria-label={String(p.name ?? p.title ?? p.ref ?? href)}>
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={x}
				cy={y}
				r={radius(p)}
				fill={fillOf(p)}
				{stroke}
				stroke-width={0.8 / ctx.k}
				{opacity}
				onmouseenter={() => enter(p)}
				onmouseleave={() => leave(p)}
			/>
		</a>
	{:else}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<circle
			cx={x}
			cy={y}
			r={radius(p)}
			fill={fillOf(p)}
			{stroke}
			stroke-width={0.8 / ctx.k}
			{opacity}
			onmouseenter={() => enter(p)}
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
