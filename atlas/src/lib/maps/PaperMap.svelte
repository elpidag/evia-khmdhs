<script lang="ts" module>
	import type { GeoPath, GeoProjection } from 'd3-geo';

	export interface MapCtx {
		path: GeoPath;
		projection: GeoProjection;
		/** current zoom scale — divide radii by this to keep dots screen-sized */
		k: number;
		/** the ITEM card (bottom-left, black); `pinned` draws the white rule +
		 *  ✕ and makes Esc / the ✕ call `onClose` (user, 2026-08-21) */
		showTip: (
			html: string,
			opts?: { pinned?: boolean; onClose?: () => void; corner?: 'bottom-left' | 'top-left' | 'bottom-right' }
		) => void;
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
	import { untrack } from 'svelte';
	import { geoMercator, geoPath } from 'd3-geo';
	import { select } from 'd3-selection';
	import 'd3-transition';
	import {
		zoom as d3zoom,
		zoomIdentity,
		zoomTransform,
		type D3ZoomEvent,
		type ZoomBehavior
	} from 'd3-zoom';
	import type { Feature, FeatureCollection, MultiPolygon } from 'geojson';
	import type { Snippet } from 'svelte';
	import { mesh } from 'topojson-client';
	import type { MultiLineString } from 'geojson';
	import { loadTopology, PE_TOPO_URL } from './useGeo';
	import { loadMuniBorders, loadPe, loadPeHires, type PeProps, loadNeighbours, type NeighbourProps,
	nearParts
} from './useGeo';

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
		/** GROUP interactivity (the anadohoi status map, 2026-08-25): maps a
		 *  Π.Ε. to its group key (περιφέρεια) or null for an INERT polygon —
		 *  when set, hover lights every member of the hovered group and
		 *  clicks fire only on members; inert polygons keep the resting
		 *  stroke and take no pointer cursor */
		peGroup?: (pe: string) => string | null;
		/** drilled Π.Ε. — zooms to it, swaps in hi-res + municipality borders */
		focusPe?: string | null;
		/** set false to MARK the drilled Π.Ε. (the heavier outline) without
		 *  zooming to it — a map whose drill reveals no sub-region marks
		 *  loses the country context for nothing (the /dase allocation duo,
		 *  2026-08-24). Anti-nero keeps the default. */
		focusZoom?: boolean;
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
		/** a lon/lat box [[lon0, lat0], [lon1, lat1]] to frame with `fitPad`
		 *  of margin on every side, whatever the frame's shape — unlike
		 *  `fitPes` it may zoom OUT below the layer's own fit, which is what
		 *  a country view needs once Kastellorizo is left out (2026-08-27) */
		fitBounds?: [[number, number], [number, number]] | null;
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
		onViewChange?: (v: {
			center: [number, number];
			k: number;
			/** the frame's visible lon/lat box [[W, S], [E, N]] — what
			 *  `fitBounds` needs to reproduce this view at any size */
			bounds?: [[number, number], [number, number]];
		}) => void;
		/** overlay layers (dots, arcs) drawn in map coordinates */
		overlay?: Snippet<[MapCtx]>;
		/** legend block, absolutely positioned over the Ionian whitespace */
		legend?: Snippet;
		/** baked shaded-relief underlay (frame-aligned AVIF, multiply-blended
		 *  over the region fills; `hi` swaps in past k≥2, never on narrow) */
		relief?: { lo: string; hi?: string } | null;
		/** draw the land around Greece (neighbouring countries + Athos) —
		 *  scenery, on by default; a map that must show Greece alone sets
		 *  `context={false}` */
		context?: boolean;
		/** allow drag-panning at the resting zoom (default). The crew map
		 *  turns it off: at rest the whole frame is already in view, so a
		 *  drag can only dislodge the crop (user, 2026-08-24); panning
		 *  re-arms as soon as the reader zooms in */
		panAtRest?: boolean;
		/** no clamps at all — the map may be zoomed OUT past the layer's fit
		 *  and dragged anywhere; the frame picker's mode (2026-08-27), never
		 *  a reader's */
		unclamped?: boolean;
		/** draw only the borders between the GROUPS this returns (plus the
		 *  coast), never the units' own — the sponsored card's map shows the
		 *  περιφέρειες' outlines, not the Π.Ε.'s (user, 2026-08-27); a group
		 *  hover then tints the fill instead of stroking the units */
		outlineBy?: ((pe: string) => string | null) | null;
		/** where a hover card lands unless the caller says otherwise — the
		 *  sponsored card's map keeps its key bottom-left, so its cards go
		 *  bottom-RIGHT (user, 2026-08-27) */
		tipDefaultCorner?: 'bottom-left' | 'top-left' | 'bottom-right';
		/** cards in the key's own size (11 px) rather than the frame's */
		tipCompact?: boolean;
	}

	/** hovered group key (peGroup mode): every member lights together */
	let hovGroup = $state<string | null>(null);

	let {
		colorOf = () => 'var(--land-empty)',
		tipOf,
		splitTips = false,
		onEmptyClick,
		onEscape,
		onRegionClick,
		peGroup,
		focusPe = null,
		focusZoom = true,
		interactive = true,
		width = 600,
		height = 620,
		fitPoints = null,
		fitPad = 0.12,
		fitPes = null,
		fitBounds = null,
		fitPesLive = null,
		view = null,
		onViewChange,
		overlay,
		legend,
		relief = null,
		context = true,
		panAtRest = true,
		unclamped = false,
		outlineBy = null,
		tipDefaultCorner = 'bottom-left',
		tipCompact = false
	}: Props = $props();

	type PeFeature = Feature<MultiPolygon, PeProps>;

	// $state.raw: the geometry must stay un-proxied — deep reactive proxies
	// on FeatureCollections make d3-geo read every coordinate through a
	// getter (hundreds of ms per mount, heavy GC)
	let coarse = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	/** the group borders + coast, cut once from the topology's shared edges */
	let outline = $state.raw<MultiLineString | null>(null);
	$effect(() => {
		const by = outlineBy;
		if (!by) {
			outline = null;
			return;
		}
		loadTopology(fetch, PE_TOPO_URL).then((topo) => {
			const obj = topo.objects.pe as Parameters<typeof mesh>[1];
			outline = mesh(topo, obj, (a, b) => {
				const pa = (a as { properties?: PeProps }).properties?.pe ?? '';
				const pb = (b as { properties?: PeProps }).properties?.pe ?? '';
				return a === b || by(pa) !== by(pb);
			}) as MultiLineString;
		});
	});
	let hires = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	let muni = $state.raw<FeatureCollection<GeoJSON.MultiLineString, { pe: string }> | null>(null);
	// the land around Greece — scenery, drawn first and never interactive
	let land = $state.raw<FeatureCollection<
		GeoJSON.MultiPolygon | GeoJSON.Polygon | GeoJSON.MultiLineString,
		NeighbourProps
	> | null>(null);
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
	// the context land (neighbours + Athos): 51 KB, fetched with the map so
	// the sea is never briefly empty (user, 2026-08-22)
	$effect(() => {
		if (!context) return;
		loadNeighbours(fetch).then((fc) => (land = fc));
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
		if (!focusPe || !focusZoom || narrow) return;
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
		if (focusPe && focusZoom) {
			const f = coarse?.features.find((f) => f.properties.pe === focusPe);
			if (f) zoomToFeature(f);
		} else if (!focusPe) {
			resetZoom();
		}
	});

	// initial editorial framing (view / fitPoints), applied once per input;
	// homeT remembers it so resetZoom (un-drill) returns to the same frame.
	// The frame's SIZE is part of the input (2026-08-27): the translate and
	// scale are computed against the projection fitted to width × height,
	// so when the map's box changes after the first frame — fonts arriving,
	// the grid settling, a window resized — the framing must be redone or
	// the country slides out of frame (Crete vanished from the sponsored
	// card in a live browser while every headless render showed it)
	let appliedViewKey = $state('');
	let homeT: { x: number; y: number; k: number } | null = null;
	$effect(() => {
		if (!projection || !path || (focusPe && focusZoom)) return;
		const key = JSON.stringify([
			view ?? [fitPoints, fitPes, fitBounds, coarse ? 1 : 0],
			Math.round(width),
			Math.round(height)
		]);
		if (!key || key === 'null' || key === appliedViewKey) return;
		if (view) {
			const px = projection(view.center);
			if (!px) return;
			homeT = { k: view.k, x: width / 2 - view.k * px[0], y: height / 2 - view.k * px[1] };
			applyTransform(homeT, false);
			appliedViewKey = key;
		} else if (fitBounds) {
			const a = projection(fitBounds[0]);
			const b = projection(fitBounds[1]);
			if (!a || !b) return;
			const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]);
			const y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
			if (x1 <= x0 || y1 <= y0) return;
			// no floor of 1: the box may be framed smaller than the layer's fit
			const k = Math.min(8, (1 - fitPad) * Math.min(width / (x1 - x0), height / (y1 - y0)));
			homeT = { k, x: width / 2 - (k * (x0 + x1)) / 2, y: height / 2 - (k * (y0 + y1)) / 2 };
			applyTransform(homeT, false);
			appliedViewKey = key;
		} else if ((fitPoints && fitPoints.length) || (fitPes && fitPes.length)) {
			let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
			// the points' own lon/lat extent anchors which parts of a Π.Ε.
			// belong in frame (user, 2026-08-26)
			let sx0 = Infinity, sy0 = Infinity, sx1 = -Infinity, sy1 = -Infinity;
			for (const c of fitPoints ?? []) {
				const q = projection(c);
				if (!q) continue;
				x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]);
				x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]);
				sx0 = Math.min(sx0, c[0]); sy0 = Math.min(sy0, c[1]);
				sx1 = Math.max(sx1, c[0]); sy1 = Math.max(sy1, c[1]);
			}
			const subject: [number, number, number, number] | null = Number.isFinite(sx0)
				? [sx0, sy0, sx1, sy1]
				: null;
			// whole regions, not their centres — but a Π.Ε. with a far-flung
			// island (Ρόδου carries Καστελλόριζο) frames only the parts that
			// belong with the works, or the window lands on open sea
			for (const pe of fitPes ?? []) {
				const f = coarse?.features.find((g) => g.properties.pe === pe);
				if (!f) continue;
				const [[bx0, by0], [bx1, by1]] = boundsOf(
					nearParts(f as PeFeature, subject) as PeFeature
				);
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

	function zoomToFeature(f0: PeFeature) {
		if (!path) return;
		// the drilled unit's far-flung island part never sets the window
		// (user, 2026-08-26): Π.Ε. Ρόδου carries Καστελλόριζο
		const f = nearParts(f0, null) as PeFeature;
		let [[x0, y0], [x1, y1]] = boundsOf(f);
		// Χαλκιδική's third leg is Athos, which no administrative layer
		// carries — drilling into the unit would cut it off mid-peninsula,
		// so the FRAME (display only, never the data) takes it in too
		// (user, 2026-08-22)
		if (f.properties.pe === 'Π.Ε. Χαλκιδικής' && land && path) {
			const a = land.features.find((g) => g.properties.kind === 'athos');
			if (a) {
				const [[ax0, ay0], [ax1, ay1]] = path.bounds(a);
				x0 = Math.min(x0, ax0); y0 = Math.min(y0, ay0);
				x1 = Math.max(x1, ax1); y1 = Math.max(y1, ay1);
			}
		}
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
		for (const f0 of fs) {
			// a Π.Ε.'s far-flung island part never sets the window
			// (user, 2026-08-26); with no subject the largest part anchors
			const f = nearParts(f0, null) as PeFeature;
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
			.scaleExtent(unclamped ? [0.2, 14] : [1, 14])
			.wheelDelta((ev) => (-ev.deltaY * (ev.deltaMode === 1 ? 0.05 : ev.deltaMode ? 1 : 0.002)) * 0.18)
			// pan/zoom can never show past the fitted frame — beyond it the
			// context layer's clip box would come into view (user, 2026-08-22)
			.translateExtent(
				unclamped
					? [
							[-1e6, -1e6],
							[1e6, 1e6]
						]
					: [
							[0, 0],
							[width, height]
						]
			)
			.filter((ev) => {
				if (ev.type === 'wheel') return wheelArmed;
				// a drag at the resting zoom only dislodges the crop. The scale
				// is read from d3's own state, NOT the reactive `transform`:
				// touching that here made this effect re-run on every zoom and
				// re-attach the behaviour, which swallowed the +/− buttons
				// (2026-08-24)
				if (!panAtRest && ev.type !== 'dblclick' && svgEl &&
					zoomTransform(svgEl).k <= (homeT?.k ?? 1) * 1.02)
					return false;
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
					const nw = projection.invert?.([-t.x / t.k, -t.y / t.k]);
					const se = projection.invert?.([(width - t.x) / t.k, (height - t.y) / t.k]);
					const r4 = (v: number) => +v.toFixed(4);
					if (c)
						onViewChange({
							center: [r4(c[0]), r4(c[1])],
							k: +t.k.toFixed(3),
							bounds:
								nw && se
									? [
											[r4(nw[0]), r4(se[1])],
											[r4(se[0]), r4(nw[1])]
										]
									: undefined
						});
				}
			})
			.on('end', () => (zooming = false));
		const sel = select(svgEl);
		sel.call(zoomBehavior);
		// hand the frame already applied (a fit or a view set while the map
		// was not interactive) to d3, or its first gesture starts from the
		// identity and the map jumps to the layer's own fit (2026-08-27) —
		// read without tracking, or this effect re-runs on every zoom
		const cur = untrack(() => transform);
		if (cur && (cur.k !== 1 || cur.x || cur.y))
			sel.call(zoomBehavior.transform, zoomIdentity.translate(cur.x, cur.y).scale(cur.k));
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
	// which corner the item card sits in: bottom-left by default; a caller
	// may ask for the top-left so two kinds of card never share a corner
	// (the contract map: authority seats top-left, δήμοι bottom-left — user,
	// 2026-08-21)
	type TipCorner = 'bottom-left' | 'top-left' | 'bottom-right';
	let tipCorner = $state<TipCorner>('bottom-left');
	function showTip(html: string, opts?: { pinned?: boolean; onClose?: () => void; corner?: TipCorner }) {
		tipHtml = html;
		tipPinned = !!opts?.pinned;
		tipOnClose = opts?.onClose ?? null;
		tipCorner = opts?.corner ?? tipDefaultCorner;
	}
	function hideTip() {
		tipHtml = '';
		tipPinned = false;
		tipOnClose = null;
		tipCorner = tipDefaultCorner;
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
				{#if land}
					<!-- context land: the neighbouring countries and the Athos
					     peninsula (which no administrative layer carries — Άγιον
					     Όρος is not a municipality). Drawn FIRST, so the Greek
					     polygons paint over the little the tuck-buffer overlaps;
					     inert, nameless scenery (user, 2026-08-22). -->
					{#each land.features as f, i (i)}
						{#if f.properties.kind !== 'border'}
							<path class="context" class:athos={f.properties.kind === 'athos'} d={path(f) ?? ''} />
						{/if}
					{/each}
				{/if}
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
					{@const grp = peGroup ? peGroup(f.properties.pe) : undefined}
					{@const inert = peGroup ? grp == null : false}
					{@const canClick = !!onRegionClick && !inert}
					<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
					<path
						class="region"
						class:focused={f.properties.pe === focusPe}
						class:clickable={canClick}
						class:inert
						class:noline={!!outlineBy}
						class:choro={!!colorOf}
						class:grouphot={!!peGroup && grp != null && grp === hovGroup}
						data-pe={f.properties.pe}
						d={dOf(f)}
						fill={relief ? 'transparent' : colorOf(f.properties.pe)}
						role={canClick ? 'button' : undefined}
						onmouseenter={tipOf || (peGroup && !inert)
							? () => {
									if (tipOf) regionEnter(f.properties.pe);
									if (peGroup && grp != null) hovGroup = grp;
								}
							: undefined}
						onmouseleave={tipOf || (peGroup && !inert)
							? () => {
									if (tipOf) regionLeave();
									if (peGroup) hovGroup = null;
								}
							: undefined}
						onclick={canClick ? () => onRegionClick!(f.properties.pe) : undefined}
						onkeydown={canClick
							? (e) => e.key === 'Enter' && onRegionClick!(f.properties.pe)
							: undefined}
						tabindex={canClick ? 0 : undefined}
					/>
				{/each}
				{#each muniFeatures as f, i (i)}
					<path class="muni" d={dOf(f)} />
				{/each}
				{#if land}
					<!-- the LAND BORDER, dashed black over the fills: with the
					     neighbours in white, this line is what says where Greece
					     ends (user, 2026-08-22). Cut from our own Π.Ε. outline,
					     so it hugs the drawn polygons exactly. -->
					{#each land.features as f, i (i)}
						{#if f.properties.kind === 'border'}
							<path class="gr-border" d={path(f) ?? ''} />
						{/if}
					{/each}
				{/if}
				{#if outline && path}
					<path class="outline" d={path(outline) ?? ''} />
				{/if}
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
			<button onclick={() => zoomBy(1.08)} title="Zoom in" aria-label="Zoom in"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M5 1h2v4h4v2H7v4H5V7H1V5h4z" fill="currentColor"/></svg></button>
			<button onclick={() => zoomBy(1 / 1.08)} title="Zoom out" aria-label="Zoom out"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M1 5h10v2H1z" fill="currentColor"/></svg></button>
			<button onclick={resetZoom} title="Reset view" aria-label="Reset view"><svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M6 1l4.4 3.4V11H1.6V4.4z" fill="currentColor"/></svg></button>
		</div>
	{/if}

	{#if splitTips && regionTipHtml}
		<div class="tip region">
			<!-- eslint-disable-next-line svelte/no-at-html-tags — tip HTML is built by our own code from DB values -->
			{@html regionTipHtml}
		</div>
	{/if}
	{#if tipHtml}
		<div
			class="tip item"
			class:pinned={tipPinned}
			class:topleft={tipCorner === 'top-left'}
			class:bottomright={tipCorner === 'bottom-right'}
			class:compact={tipCompact}
		>
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
	/* the land around Greece: one flat tone, a hairline coast, no
	   interaction — it must never compete with the data (user, 2026-08-22) */
	.context {
		fill: var(--land-context, #ffffff);
		stroke: var(--land-context-line, #c4c4c4);
		stroke-width: var(--context-line-w, 0.5);
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}
	/* where Greece ends on land: dashed black over the fills (user,
	   2026-08-22 — white neighbours need the border said explicitly) */
	.gr-border {
		fill: none;
		stroke: var(--ink);
		stroke-width: var(--border-line-w, 0.9);
		stroke-dasharray: 4 3;
		stroke-linecap: butt;
		vector-effect: non-scaling-stroke;
		pointer-events: none;
	}
	/* Athos is Greek land — it is only not a MUNICIPALITY, which is why no
	   administrative layer carries it — so it is drawn in Greece's own land
	   colour and coastline, at the Greek layers' accuracy (user, 2026-08-22);
	   it stays inert: it holds no contract and answers no click */
	.context.athos {
		fill: var(--land-athos, var(--land-context, #e4e4e4));
		stroke: var(--line);
		stroke-width: 0.6;
	}
	.map {
		position: relative;
		/* the sea: the site's one grey, never the old cream (2026-08-28) */
		background: #f2f2f2;
		/* the maps' hairline — the zoom buttons' outline tone (user, 2026-08-22) */
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
		/* a small map needs thinner administrative lines (user, 2026-08-27) */
		stroke-width: var(--region-line-w, 0.6);
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
	/* GROUP mode (peGroup): an inert polygon never lights, the hovered
	   group lights WHOLE — declared after :hover so it wins the tie */
	.region.inert:hover {
		stroke: var(--line-strong);
		stroke-width: 0.6;
	}
	.region.grouphot {
		stroke: var(--ink);
		stroke-width: 1.3;
	}
	/* the drilled unit: a clearly heavier outline than a hover (user, 2026-08-21) */
	.region.focused {
		stroke: var(--ink);
		stroke-width: 1.6;
	}
	/* outline mode: the units draw no border of their own — hover and
	   focus included — and a hot group shows as a tint of the fill */
	.region.noline,
	.region.noline:hover,
	.region.noline.inert:hover,
	.region.noline.grouphot,
	.region.noline.focused {
		/* none — unless the caller names a colour: a choropleth's grey
		   units need a white seam to be told apart (user, 2026-08-28) */
		stroke: var(--unit-line, none);
		stroke-width: var(--unit-line-w, var(--region-line-w, 0.6));
	}
	/* a hot group is a tint — unless the fill IS the data (a choropleth),
	   which a hover must never repaint */
	.region.noline.grouphot:not(.choro) {
		fill: var(--land-hot, #e6e6e6);
	}
	.outline {
		fill: none;
		stroke: var(--line-strong);
		stroke-width: var(--region-line-w, 0.6);
		vector-effect: non-scaling-stroke;
		pointer-events: none;
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
		gap: 4px;
	}
	.zoomctl button {
		font: inherit;
		line-height: 0;
		width: 1.45rem;
		height: 1.45rem;
		padding: 0;
		display: grid;
		place-items: center;
		border: none;
		/* solid section-hue circles with white glyphs (user mock, 2026-08-22);
		   each section sets --map-accent, black is the fallback */
		border-radius: 50%;
		background: var(--map-accent, var(--ink));
		color: #fff;
		cursor: pointer;
	}
	.zoomctl button:hover {
		opacity: 0.82;
	}
	/* the component's generic svg rule sizes maps to 100% — the button
	   glyphs must keep their own 11px */
	.zoomctl button svg {
		width: 9.5px;
		height: 9.5px;
		display: block;
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
	/* an item card asked into the top-left corner (the contract map's
	   authority seats, so the δήμοι keep the bottom-left) */
	.tip.item.topleft {
		top: var(--sp-2);
		bottom: auto;
	}
	.tip.item.bottomright {
		left: auto;
		right: var(--sp-2);
	}
	/* the key's own size: 11 px on 14,4 px lines, a slimmer box */
	.tip.compact {
		font-size: 11px;
		line-height: 14.4px;
		padding: 2px 6px;
		border-radius: 3px;
		max-width: 16rem;
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
