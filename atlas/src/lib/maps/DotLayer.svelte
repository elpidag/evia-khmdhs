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
		/** click selects instead of navigating (no hrefOf then) */
		onClick?: (p: DotPoint) => void;
		/** externally-driven highlight (e.g. hovering the paired chart) */
		hotOf?: (p: DotPoint) => boolean;
		/** externally-driven CARD: while true for a point, its tooltip shows
		 *  as if hovered — the paired map pulls up the contractor's card when
		 *  it lights the dot (user, 2026-08-20) */
		pinTip?: (p: DotPoint) => boolean;
		/** decorative only: no card, no link, no handlers, and the pointer
		 *  passes through to whatever lies under the dot (the region polygon
		 *  keeps its own card) */
		inert?: boolean;
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
		onClick,
		hotOf,
		pinTip,
		inert = false,
		dashOf,
		fillOpacityOf
	}: Props = $props();

	// the pinned card: show the first pinned point's tip, hide it again when
	// nothing is pinned any more (never touching a tip a real hover owns)
	let pinnedKey = $state<string | null>(null);
	$effect(() => {
		if (!pinTip || !tipOf) return;
		// one card per distinct entity (a multi-authority contract has several
		// dots with the same ref — its card shows once), stacked when several
		const seen = new Set<string>();
		const pinned = points.filter((p) => {
			if (!pinTip(p)) return false;
			const k = String(p.ref ?? p.vat ?? p.name ?? '');
			if (seen.has(k)) return false;
			seen.add(k);
			return true;
		});
		const key = pinned.length ? [...seen].sort().join('|') : null;
		if (key === pinnedKey) return;
		pinnedKey = key;
		if (!pinned.length) {
			ctx.hideTip();
			return;
		}
		const MAX = 6;
		const html = pinned.slice(0, MAX).map((p) => tipOf(p)).join('<hr class="tip-rule">');
		ctx.showTip(
			pinned.length > MAX
				? `${html}<hr class="tip-rule">+${pinned.length - MAX} more`
				: html
		);
	});

	function enter(p: DotPoint, e?: MouseEvent) {
		if (tipOf) ctx.showTip(tipOf(p));
		onOver?.(p, e);
	}
	function leave(p: DotPoint) {
		if (tipOf) {
			// a pinned card comes back when the pointer leaves another dot
			if (pinTip && points.some((q) => pinTip(q))) pinnedKey = null;
			else ctx.hideTip();
		}
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
	{@const href = inert ? null : (hrefOf?.(p) ?? null)}
	{@const hot = hotOf?.(p) ?? false}
	{#if inert}
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
			style:pointer-events="none"
		/>
	{:else if href}
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
		<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
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
			style:cursor={onClick ? 'pointer' : undefined}
			onmouseenter={(e) => enter(p, e)}
			onmouseleave={() => leave(p)}
			onclick={onClick ? () => onClick(p) : undefined}
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
