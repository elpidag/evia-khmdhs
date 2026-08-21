<script lang="ts" module>
	import type { GeoPath, GeoProjection } from 'd3-geo';

	export interface MapCtx {
		path: GeoPath;
		projection: GeoProjection;
		/** current zoom scale — divide radii by this to keep dots screen-sized */
		k: number;
		/** the ITEM card (bottom-left, black); `pinned` draws the white rule +
		 *  ✕ and makes Esc / the ✕ call `onClose` (user, 2026-08-21) */
		showTip: (html: string, opts?: { pinned?: boolean; onClose?: () => void }) => void;
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
		/** two card slots: the REGION card in its own grey top-left slot, so a
		 *  dot's card (bottom-left, black) never replaces it (user, 2026-08-21) */
		splitTips?: boolean;
		/** a click on the bare map (no region, no dot) — the Anti-nero maps
		 *  clear their selection with it (user, 2026-08-21) */
		onEmptyClick?: () => void;
		/** Escape with nothing pinned — the Anti-nero maps reset their drill */
		onEscape?: () => void;
		onRegionClick?: (pe: string) => void;
		/** drilled Π.Ε. — zooms to it, swaps in hi-res + municipality borders */
		focusPe?: string | null;
		interactive?: boolean;
		/** viewBox aspect (Greece is portrait-ish) */
		width?: number;
		height?: number;
		/** initial framing: zoom to fit these lon/lat points (e.g. the data
		 *  dots) with `fitPad` margin — an editorial crop of the country */
		fitPoints?: [number, number][] | null;
		/** initial framing: fit these Π.Ε. WHOLE, merged with fitPoints. A
		 *  detail map should frame the regions it highlights rather than
		 *  their centres — centres crop an island in half (user, 2026-08-19) */
		fitPes?: string[] | null;
		/** LIVE refit (animated) to these Π.Ε. wholes while set — used by the
		 *  drilled map to show every region a hovered multi-region contract
		 *  touches; clearing it returns to the focusPe zoom */
		fitPesLive?: string[] | null;
		/** margin around fitted points as a fraction of the frame (default 0.12) */
		fitPad?: number;
		/** initial framing, hand-tuned: centre lon/lat + zoom factor
		 *  (k=1 is the whole country); wins over fitPoints */
		view?: { center: [number, number]; k: number } | null;
		/** fires with the current {center,k} as the user pans/zooms —
		 *  powers the dev-only frame picker */
		onViewChange?: (v: { center: [number, number]; k: number }) => void;
		/** overlay layers (dots, arcs) drawn in map coordinates */
		overlay?: Snippet<[MapCtx]>;
		/** legend block, absolutely positioned over the Ionian whitespace */
		legend?: Snippet;
		/** baked shaded-relief underlay (frame-aligned AVIF, multiply-blended
		 *  over the region fills; `hi` swaps in past k≥2, never on narrow) */
		relief?: { lo: string; hi?: string } | null;
	}

	let {
		colorOf = () => 'var(--land-empty)',
		tipOf,
		splitTips = false,
		onEmptyClick,
		onEscape,
		onRegionClick,
		focusPe = null,
		interactive = true,
		width = 600,
		height = 620,
		fitPoints = null,
		fitPad = 0.12,
		fitPes = null,
		fitPesLive = null,
		view = null,
		onViewChange,
		overlay,
		legend,
		relief = null
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
		// re-run when focusPe, the live fit or geometry readiness changes
		if (!path || !svgEl) return;
		if (fitPesLive && fitPesLive.length && coarse) {
			const fs = coarse.features.filter((f) => fitPesLive!.includes(f.properties.pe));
			if (fs.length) {
				zoomToFeatures(fs as PeFeature[]);
				return;
			}
		}
		if (focusPe) {
			const f = coarse?.features.find((f) => f.properties.pe === focusPe);
			if (f) zoomToFeature(f);
		} else {
			resetZoom();
		}
	});

	// initial editorial framing (view / fitPoints), applied once per input;
	// homeT remembers it so resetZoom (un-drill) returns to the same frame
	let appliedViewKey = $state('');
	let homeT: { x: number; y: number; k: number } | null = null;
	$effect(() => {
		if (!projection || !path || focusPe) return;
		const key = JSON.stringify(view ?? [fitPoints, fitPes, coarse ? 1 : 0]);
		if (!key || key === 'null' || key === appliedViewKey) return;
		if (view) {
			const px = projection(view.center);
			if (!px) return;
			homeT = { k: view.k, x: width / 2 - view.k * px[0], y: height / 2 - view.k * px[1] };
			applyTransform(homeT, false);
			appliedViewKey = key;
		} else if ((fitPoints && fitPoints.length) || (fitPes && fitPes.length)) {
			let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
			for (const c of fitPoints ?? []) {
				const q = projection(c);
				if (!q) continue;
				x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]);
				x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]);
			}
			// whole regions, not their centres
			for (const pe of fitPes ?? []) {
				const f = coarse?.features.find((g) => g.properties.pe === pe);
				if (!f) continue;
				const [[bx0, by0], [bx1, by1]] = boundsOf(f as PeFeature);
				x0 = Math.min(x0, bx0); y0 = Math.min(y0, by0);
				x1 = Math.max(x1, bx1); y1 = Math.max(y1, by1);
			}
			if (x1 <= x0 || y1 <= y0) return;
			const k = Math.max(
				1,
				Math.min(8, (1 - fitPad) * Math.min(width / (x1 - x0), height / (y1 - y0)))
			);
			homeT = { k, x: width / 2 - (k * (x0 + x1)) / 2, y: height / 2 - (k * (y0 + y1)) / 2 };
			applyTransform(homeT, false);
			appliedViewKey = key;
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

	/** fit several Π.Ε. whole — the union of their bounds, a little looser
	 *  than the single-region drill so off-region seats sit inside the frame */
	function zoomToFeatures(fs: PeFeature[]) {
		if (!path || !fs.length) return;
		let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
		for (const f of fs) {
			const [[bx0, by0], [bx1, by1]] = boundsOf(f);
			x0 = Math.min(x0, bx0); y0 = Math.min(y0, by0);
			x1 = Math.max(x1, bx1); y1 = Math.max(y1, by1);
		}
		if (x1 <= x0 || y1 <= y0) return;
		const k = Math.max(1, Math.min(14, 0.78 / Math.max((x1 - x0) / width, (y1 - y0) / height)));
		applyTransform({
			x: width / 2 - (k * (x0 + x1)) / 2,
			y: height / 2 - (k * (y0 + y1)) / 2,
			k
		});
	}

	function resetZoom() {
		applyTransform(homeT ?? { x: 0, y: 0, k: 1 });
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
			.wheelDelta((ev) => (-ev.deltaY * (ev.deltaMode === 1 ? 0.05 : ev.deltaMode ? 1 : 0.002)) * 0.18)
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
				if (onViewChange && projection) {
					const t = ev.transform;
					const c = projection.invert?.([
						(width / 2 - t.x) / t.k,
						(height / 2 - t.y) / t.k
					]);
					if (c) onViewChange({ center: [+c[0].toFixed(4), +c[1].toFixed(4)], k: +t.k.toFixed(3) });
				}
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

	// the region card's own slot when `splitTips` (grey, top-left)
	let regionTipHtml = $state('');
	// a pinned item card: white rule + ✕, Esc / ✕ release it through onClose
	let tipPinned = $state(false);
	let tipOnClose = $state<(() => void) | null>(null);
	function showTip(html: string, opts?: { pinned?: boolean; onClose?: () => void }) {
		tipHtml = html;
		tipPinned = !!opts?.pinned;
		tipOnClose = opts?.onClose ?? null;
	}
	function hideTip() {
		tipHtml = '';
		tipPinned = false;
		tipOnClose = null;
	}
	function regionEnter(pe: string) {
		if (!tipOf) return;
		if (splitTips) regionTipHtml = tipOf(pe);
		else tipHtml = tipOf(pe);
	}
	function regionLeave() {
		if (!tipOf) return;
		if (splitTips) regionTipHtml = '';
		else tipHtml = '';
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

<div class="map" class:plate={!!relief} role="img" aria-label="Map of Greece by regional unit">
	<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
	<svg
		bind:this={svgEl}
		viewBox="0 0 {width} {height}"
		preserveAspectRatio="xMidYMid meet"
		class:interactive
		onclick={(e) => {
			if (e.target === e.currentTarget) onEmptyClick?.();
		}}
	>
		{#if path}
			<g transform="translate({transform.x},{transform.y}) scale({transform.k})">
				{#if relief}
					<!-- baked relief plate, drawn UNDER the (transparent-filled)
					     polygons; the .map.plate background carries the same plate
					     gradient so the surround beyond the image edge is seamless
					     (the fires frame k=1.08 exposes ~19px west of the image).
					     Aligned by construction: warped to this exact frame
					     (frame.json contract, build_relief.py). -->
					<image
						href={relief.hi && !narrow && transform.k >= 2 && !zooming
							? relief.hi
							: relief.lo}
						x="0"
						y="0"
						{width}
						{height}
						preserveAspectRatio="none"
						pointer-events="none"
						class="relief"
					/>
				{/if}
				{#each drawnFeatures as f (f.properties.pe)}
					<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
					<path
						class="region"
						class:focused={f.properties.pe === focusPe}
						class:clickable={!!onRegionClick}
						data-pe={f.properties.pe}
						d={dOf(f)}
						fill={relief ? 'transparent' : colorOf(f.properties.pe)}
						role={onRegionClick ? 'button' : undefined}
						onmouseenter={tipOf ? () => regionEnter(f.properties.pe) : undefined}
						onmouseleave={tipOf ? () => regionLeave() : undefined}
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
			<button onclick={() => zoomBy(1.08)} title="Zoom in" aria-label="Zoom in">+</button>
			<button onclick={() => zoomBy(1 / 1.08)} title="Zoom out" aria-label="Zoom out">−</button>
			<button onclick={resetZoom} title="Reset view" aria-label="Reset view">⌂</button>
		</div>
	{/if}

	{#if splitTips && regionTipHtml}
		<div class="tip region">
			<!-- eslint-disable-next-line svelte/no-at-html-tags — tip HTML is built by our own code from DB values -->
			{@html regionTipHtml}
		</div>
	{/if}
	{#if tipHtml}
		<div class="tip item" class:pinned={tipPinned}>
			<!-- eslint-disable-next-line svelte/no-at-html-tags — tip HTML is built by our own code from DB values -->
			{@html tipHtml}
			{#if tipPinned}
				<button class="tip-close" onclick={() => tipOnClose?.()} title="Release (Esc)" aria-label="Release the selection">✕</button>
			{/if}
		</div>
	{/if}
</div>
<svelte:window
	onkeydown={(e) => {
		if (e.key !== 'Escape') return;
		// first Esc releases a held card; with nothing held it steps out of the drill
		if (tipPinned) tipOnClose?.();
		else onEscape?.();
	}}
/>

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
	/* the drilled unit: a clearly heavier outline than a hover (user, 2026-08-21) */
	.region.focused {
		stroke: var(--ink);
		stroke-width: 1.6;
	}
	.muni {
		fill: none;
		stroke: var(--ink-faint);
		stroke-width: 0.5;
		stroke-dasharray: 2 2;
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}
	/* the surround beyond the relief image continues the plate: the same
	   gradient the bake applies (MUST match build_relief.py SHADOW_RGB /
	   BG_BASE 0.885 / GRAD_AMP 0.045 / SUN_AZ 300 — bright toward the
	   WNW sun, dim ESE) */
	.map.plate {
		background: linear-gradient(110deg, #f1f1f1, #e2e2e3);
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
	/* the same black card the sponsored-works maps use (user, 2026-08-19) —
	   one hover-label look across every map on the site */
	.tip {
		position: absolute;
		bottom: var(--sp-2);
		left: var(--sp-2);
		max-width: 22rem;
		background: #000;
		color: #fff;
		border-radius: 4px;
		padding: var(--sp-1) var(--sp-2);
		font-size: var(--fs-13);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}
	/* two slots (user, 2026-08-21): the place's card grey at the top-left, the
	   item's card black at the bottom-left — a dot's card never replaces the
	   region's, and the two are told apart by colour and corner */
	.tip.region {
		top: var(--sp-2);
		bottom: auto;
		background: #5c5c5c;
	}
	/* a held (clicked) card: white rule on top and a ✕ — hover cards have neither */
	.tip.pinned {
		border-top: 2px solid #fff;
		padding-right: 1.8rem;
		pointer-events: auto;
	}
	.tip-close {
		position: absolute;
		top: 2px;
		right: 4px;
		background: none;
		border: 0;
		color: #fff;
		font-size: var(--fs-12);
		line-height: 1;
		cursor: pointer;
		padding: 2px 4px;
	}
</style>
