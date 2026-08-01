<script lang="ts" module>
	import type { GeoPath, GeoProjection } from 'd3-geo';

	export interface MapCtx {
		path: GeoPath;
		projection: GeoProjection;
		/** current zoom scale — divide radii by this to keep dots screen-sized */
		k: number;
		showTip: (html: string) => void;
		hideTip: () => void;
	}

	// Module-level geometry caches, shared by every map instance across
	// navigations. The topo FeatureCollections are module singletons, so
	// fitSize parameters, path strings and bounds are pure functions of
	// (featureCollection, width×height) — computing them once total instead
	// of per mount removes most of a map's mount cost.
	const fitCache = new WeakMap<object, Map<string, { scale: number; translate: [number, number] }>>();
	const dCache = new WeakMap<object, Map<string, string>>();
	const boundsCache = new WeakMap<
		object,
		Map<string, [[number, number], [number, number]]>
	>();

	function subCache<V>(store: WeakMap<object, Map<string, V>>, obj: object): Map<string, V> {
		let m = store.get(obj);
		if (!m) {
			m = new Map();
			store.set(obj, m);
		}
		return m;
	}
</script>

<script lang="ts">
	import { geoMercator, geoPath } from 'd3-geo';
	import { select } from 'd3-selection';
	import 'd3-transition';
	import { zoom as d3zoom, zoomIdentity, type D3ZoomEvent, type ZoomBehavior } from 'd3-zoom';
	import type { Feature, FeatureCollection, MultiPolygon } from 'geojson';
	import type { Snippet } from 'svelte';
	import { loadMuniBorders, loadPe, loadPeHires, type PeProps } from './useGeo';

	interface Props {
		/** polygon fill by Π.Ε. name; default = empty land */
		colorOf?: (pe: string) => string;
		/** pinned-tooltip HTML on region hover (convenience only, never load-bearing) */
		tipOf?: (pe: string) => string;
		onRegionClick?: (pe: string) => void;
		/** drilled Π.Ε. — zooms to it, swaps in hi-res + municipality borders */
		focusPe?: string | null;
		interactive?: boolean;
		/** viewBox aspect (Greece is portrait-ish) */
		width?: number;
		height?: number;
		/** overlay layers (dots, arcs) drawn in map coordinates */
		overlay?: Snippet<[MapCtx]>;
		/** legend block, absolutely positioned over the Ionian whitespace */
		legend?: Snippet;
	}

	let {
		colorOf = () => 'var(--land-empty)',
		tipOf,
		onRegionClick,
		focusPe = null,
		interactive = true,
		width = 600,
		height = 620,
		overlay,
		legend
	}: Props = $props();

	type PeFeature = Feature<MultiPolygon, PeProps>;

	// $state.raw: the geometry must stay un-proxied — deep reactive proxies
	// on FeatureCollections make d3-geo read every coordinate through a
	// getter (hundreds of ms per mount, heavy GC)
	let coarse = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let hires = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let muni = $state.raw<FeatureCollection<GeoJSON.MultiLineString, { pe: string }> | null>(null);
	let tipHtml = $state('');
	let transform = $state({ x: 0, y: 0, k: 1 });
	let svgEl = $state<SVGSVGElement | null>(null);
	let zoomBehavior: ZoomBehavior<SVGSVGElement, unknown> | null = null;
	// phones get a static map: no pan/zoom, no multi-MB hi-res/border layers
	let narrow = $state(false);
	$effect(() => {
		const mq = window.matchMedia('(max-width: 640px)');
		narrow = mq.matches;
		const onChange = (e: MediaQueryListEvent) => (narrow = e.matches);
		mq.addEventListener('change', onChange);
		return () => mq.removeEventListener('change', onChange);
	});

	const sizeKey = $derived(`${width}x${height}`);
	const projection = $derived.by(() => {
		if (!coarse) return null;
		const cache = subCache(fitCache, coarse);
		let fit = cache.get(sizeKey);
		if (!fit) {
			const p = geoMercator().fitSize([width, height], coarse);
			fit = { scale: p.scale(), translate: p.translate() };
			cache.set(sizeKey, fit);
			return p;
		}
		return geoMercator().scale(fit.scale).translate(fit.translate);
	});
	const path = $derived(projection ? geoPath(projection) : null);

	function boundsOf(f: PeFeature): [[number, number], [number, number]] {
		const cache = subCache(boundsCache, f);
		let b = cache.get(sizeKey);
		if (!b) {
			b = path!.bounds(f);
			cache.set(sizeKey, b);
		}
		return b;
	}

	function dOf(f: Feature): string {
		const cache = subCache(dCache, f);
		let d = cache.get(sizeKey);
		if (d === undefined) {
			d = path!(f) ?? '';
			cache.set(sizeKey, d);
		}
		return d;
	}

	// Load the coarse layer on mount (client-only — maps are not SSR'd to
	// keep multi-MB geometry out of the HTML payload).
	$effect(() => {
		loadPe(fetch).then((fc) => (coarse = fc));
	});

	// Prefetch the hi-res + municipality layers during browser idle time and
	// pre-generate their path strings in small chunks — the first drill used
	// to pay a ~470ms long task mid-animation for exactly this work.
	$effect(() => {
		if (!interactive || narrow || !path) return;
		const ric: (cb: (d?: IdleDeadline) => void) => number =
			window.requestIdleCallback ?? ((cb) => window.setTimeout(cb, 250));
		let cancelled = false;
		const handle = ric(() => {
			if (cancelled) return;
			Promise.all([loadPeHires(fetch), loadMuniBorders(fetch)]).then(([h, m]) => {
				if (cancelled) return;
				hires = h;
				muni = m;
				const feats: Feature[] = [...h.features, ...m.features];
				let i = 0;
				const step = (deadline?: IdleDeadline) => {
					const budget = () => !deadline || deadline.timeRemaining() > 4;
					while (i < feats.length && budget()) {
						dOf(feats[i]);
						if (i < h.features.length) boundsOf(h.features[i] as PeFeature);
						i++;
					}
					if (i < feats.length && !cancelled) ric(step);
				};
				ric(step);
			});
		});
		return () => {
			cancelled = true;
			(window.cancelIdleCallback ?? window.clearTimeout)(handle);
		};
	});

	// Fallback for non-interactive maps that get drilled via props.
	$effect(() => {
		if (!focusPe || narrow) return;
		if (!hires) loadPeHires(fetch).then((fc) => (hires = fc));
		if (!muni) loadMuniBorders(fetch).then((fc) => (muni = fc));
	});

	$effect(() => {
		// re-run when focusPe or geometry readiness changes
		if (!path || !svgEl) return;
		if (focusPe) {
			const f = coarse?.features.find((f) => f.properties.pe === focusPe);
			if (f) zoomToFeature(f);
		} else {
			resetZoom();
		}
	});

	function applyTransform(t: { x: number; y: number; k: number }, animate = true) {
		if (!svgEl) return;
		const zt = zoomIdentity.translate(t.x, t.y).scale(t.k);
		const sel = select(svgEl);
		if (zoomBehavior) {
			(animate ? sel.transition().duration(600) : sel).call(zoomBehavior.transform, zt);
		} else {
			transform = t;
		}
	}

	function zoomToFeature(f: PeFeature) {
		if (!path) return;
		const [[x0, y0], [x1, y1]] = boundsOf(f);
		const k = Math.min(14, 0.82 / Math.max((x1 - x0) / width, (y1 - y0) / height));
		applyTransform({
			x: width / 2 - (k * (x0 + x1)) / 2,
			y: height / 2 - (k * (y0 + y1)) / 2,
			k
		});
	}

	function resetZoom() {
		applyTransform({ x: 0, y: 0, k: 1 });
	}

	function zoomBy(factor: number) {
		if (!svgEl || !zoomBehavior) return;
		select(svgEl).transition().duration(250).call(zoomBehavior.scaleBy, factor);
	}

	// d3-zoom binding (interactive maps only; phones stay static).
	// Wheel zoom arms only after the user has clicked/tapped the map —
	// casual page scrolling must never be hijacked.
	let wheelArmed = false;
	$effect(() => {
		if (!svgEl || !interactive || narrow) return;
		zoomBehavior = d3zoom<SVGSVGElement, unknown>()
			.scaleExtent([1, 14])
			.translateExtent([
				[-width * 0.25, -height * 0.25],
				[width * 1.25, height * 1.25]
			])
			.filter((ev) => {
				if (ev.type === 'wheel') return wheelArmed;
				return !ev.ctrlKey && !ev.button;
			})
			.on('start', () => (zooming = true))
			.on('zoom', (ev: D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = { x: ev.transform.x, y: ev.transform.y, k: ev.transform.k };
			})
			.on('end', () => (zooming = false));
		const sel = select(svgEl);
		sel.call(zoomBehavior);
		sel.on('pointerdown.arm', () => (wheelArmed = true));
		sel.on('mouseleave.arm', () => (wheelArmed = false));
		return () => {
			sel.on('.zoom', null).on('.arm', null);
			zoomBehavior = null;
		};
	});

	// Quantised view key: the viewport-dependent derivations below re-run a
	// handful of times per gesture instead of every animation frame.
	const viewKey = $derived(
		`${Math.round(transform.x / 40)}|${Math.round(transform.y / 40)}|${Math.round(transform.k * 4)}`
	);

	// The hi-res layer swaps in only after the drill ANIMATION settles (a
	// mid-transition DOM swap dropped frames), then stays active through
	// pans until the drill is cleared.
	let zooming = $state(false);
	let hiresShown = $state(false);
	$effect(() => {
		if (!focusPe) hiresShown = false;
		else if (hires && !zooming && transform.k >= 2) hiresShown = true;
	});

	// Which polygon source to draw: hi-res only while drilled AND settled,
	// filtered (with padding to hide the quantisation) to features whose
	// cached bounds intersect the viewport.
	const drawnFeatures = $derived.by((): PeFeature[] => {
		if (!coarse || !path) return [];
		const [qx, qy, qk] = viewKey.split('|').map(Number);
		const k = qk / 4 || 1;
		if (!focusPe || !hires || !hiresShown || k < 2) return coarse.features;
		const x = qx * 40,
			y = qy * 40;
		const pad = 90 / k;
		const vx0 = -x / k - pad,
			vy0 = -y / k - pad,
			vx1 = (width - x) / k + pad,
			vy1 = (height - y) / k + pad;
		return hires.features.filter((f) => {
			const [[bx0, by0], [bx1, by1]] = boundsOf(f);
			return bx1 >= vx0 && bx0 <= vx1 && by1 >= vy0 && by0 <= vy1;
		});
	});

	const muniFeatures = $derived.by(() => {
		if (!focusPe || !muni || !hiresShown) return [];
		return muni.features.filter((f) => f.properties.pe === focusPe);
	});

	function showTip(html: string) {
		tipHtml = html;
	}
	function hideTip() {
		tipHtml = '';
	}
	// k is quantised so overlays (dots, arcs) re-render at quarter-steps of
	// the zoom, not per frame — pan doesn't touch them at all.
	const qk = $derived(Math.round(transform.k * 4) / 4 || 1);
	const ctx: MapCtx = $derived({
		path: path!,
		projection: projection!,
		k: qk,
		showTip,
		hideTip
	});
</script>

<div class="map" role="img" aria-label="Map of Greece by regional unit">
	<svg
		bind:this={svgEl}
		viewBox="0 0 {width} {height}"
		preserveAspectRatio="xMidYMid meet"
		class:interactive
	>
		{#if path}
			<g transform="translate({transform.x},{transform.y}) scale({transform.k})">
				{#each drawnFeatures as f (f.properties.pe)}
					<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
					<path
						class="region"
						class:focused={f.properties.pe === focusPe}
						class:clickable={!!onRegionClick}
						data-pe={f.properties.pe}
						d={dOf(f)}
						fill={colorOf(f.properties.pe)}
						role={onRegionClick ? 'button' : undefined}
						onmouseenter={tipOf ? () => (tipHtml = tipOf(f.properties.pe)) : undefined}
						onmouseleave={tipOf ? () => (tipHtml = '') : undefined}
						onclick={onRegionClick ? () => onRegionClick(f.properties.pe) : undefined}
						onkeydown={onRegionClick
							? (e) => e.key === 'Enter' && onRegionClick(f.properties.pe)
							: undefined}
						tabindex={onRegionClick ? 0 : undefined}
					/>
				{/each}
				{#each muniFeatures as f, i (i)}
					<path class="muni" d={dOf(f)} />
				{/each}
				{#if overlay && projection}
					{@render overlay(ctx)}
				{/if}
			</g>
		{/if}
	</svg>

	{#if legend}
		<div class="legend">{@render legend()}</div>
	{/if}

	{#if interactive && !narrow}
		<div class="zoomctl">
			<button onclick={() => zoomBy(1.6)} title="Zoom in" aria-label="Zoom in">+</button>
			<button onclick={() => zoomBy(1 / 1.6)} title="Zoom out" aria-label="Zoom out">−</button>
			<button onclick={resetZoom} title="Reset view" aria-label="Reset view">⌂</button>
		</div>
	{/if}

	{#if tipHtml}
		<div class="tip">
			<!-- eslint-disable-next-line svelte/no-at-html-tags — tip HTML is built by our own code from DB values -->
			{@html tipHtml}
		</div>
	{/if}
</div>

<style>
	.map {
		position: relative;
		background: linear-gradient(180deg, #f9f6ec, #f3ecdb);
		border: 1px solid var(--line);
		border-radius: var(--radius);
		box-shadow: var(--shadow-paper);
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
	}
	svg.interactive {
		cursor: grab;
	}
	.region {
		stroke: var(--line-strong);
		stroke-width: 0.6;
		vector-effect: non-scaling-stroke;
	}
	/* stroke highlight, not filter — filters force expensive repaint layers */
	.region:hover {
		stroke: var(--ink);
		stroke-width: 1.3;
	}
	.region.clickable {
		cursor: pointer;
	}
	/* no UA focus rectangle around a clicked polygon; keyboard users still
	   get the stroke highlight via :focus-visible */
	.region:focus {
		outline: none;
	}
	.region:focus-visible {
		outline: none;
		stroke: var(--ink);
		stroke-width: 1.4;
	}
	.region.focused {
		stroke: var(--ink);
		stroke-width: 1.1;
	}
	.muni {
		fill: none;
		stroke: var(--ink-faint);
		stroke-width: 0.5;
		stroke-dasharray: 2 2;
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}
	.legend {
		position: absolute;
		top: var(--sp-2);
		left: var(--sp-2);
		background: color-mix(in srgb, var(--paper) 88%, transparent);
		border: 1px solid var(--line);
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-12);
		pointer-events: none;
	}
	.zoomctl {
		position: absolute;
		top: var(--sp-2);
		right: var(--sp-2);
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.zoomctl button {
		font: inherit;
		font-size: var(--fs-16);
		line-height: 1;
		width: 1.8rem;
		height: 1.8rem;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: color-mix(in srgb, var(--paper) 92%, transparent);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.zoomctl button:hover {
		color: var(--ink);
		background: var(--paper);
	}
	.tip {
		position: absolute;
		bottom: var(--sp-2);
		left: var(--sp-2);
		max-width: 22rem;
		background: color-mix(in srgb, var(--paper) 94%, transparent);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		padding: var(--sp-2) var(--sp-3);
		font-size: var(--fs-13);
		pointer-events: none;
		box-shadow: var(--shadow-paper);
	}
</style>
