<script lang="ts">
	/** Compact map for a sponsor project's curated work site(s): the
	 *  containing Π.Ε. outline(s) with one unlabelled dot per site.
	 *  Approximate sites (municipality-centre pins) render dashed.
	 *  Optionally draws the project's linked EFFIS burn scar(s) under the
	 *  pins — per-fire tones via `fireColorOf` (matching the timeline-bar
	 *  dots), sizes in a black hover card top-left (opposite the zoom
	 *  buttons); attribution lives in the FactsHeader caveat. Renders
	 *  scar-only when the project has scars but no pinned sites.
	 *  Multi-site maps get +/−/⌂ zoom buttons (drag pans while zoomed). */
	import { geoMercator, geoPath } from 'd3-geo';
	import { dmy, grInt } from '$lib/transforms/format';
	import { loadPe, type FireProps, type PeProps, type RiverProps } from './useGeo';
	import type {
		Feature,
		FeatureCollection,
		LineString,
		MultiLineString,
		MultiPolygon,
		Polygon
	} from 'geojson';

	export interface SitePin {
		name: string;
		lat: number;
		lon: number;
		geo_precision?: string | null;
		municipality?: string | null;
		/** stated intervention area — the dot is drawn at this TRUE size
		 *  at map scale (clamped to a minimum so it never vanishes) */
		stremmata?: number | null;
	}
	interface Props {
		/** svg viewBox height — the detail template asks for a taller map */
		height?: number;
		sites: SitePin[];
		/** linked EFFIS burn-scar features (already filtered by id) */
		scars?: Feature<Polygon | MultiPolygon, FireProps>[];
		/** per-fire fill tone (defaults to the solid base maroon mix) */
		fireColorOf?: (f: Feature<Polygon | MultiPolygon, FireProps>) => string;
		/** externally selected fire (timeline-dot hover): highlighted + card shown */
		selectedId?: number | null;
		/** context rivers named by the designation act (curated, OSM courses) */
		rivers?: Feature<LineString | MultiLineString, RiverProps>[];
		/** pin fill — the project's timeline-bar colour (identity hue) */
		pinColor?: string;
	}
	let {
		sites,
		scars = [],
		height = 340,
		fireColorOf = () => 'color-mix(in srgb, #6b2d35 85%, #fff)',
		selectedId = null,
		rivers = [],
		pinColor = 'var(--c-anadohoi)'
	}: Props = $props();

	const W = 460;
	const H = $derived(height);
	const APPROX = new Set(['municipality', 'pe']);

	let pe = $state.raw<FeatureCollection<MultiPolygon, PeProps> | null>(null);
	$effect(() => {
		loadPe(fetch).then((v) => (pe = v));
	});

	/** zoom state: k = magnification, dx/dy = frame-centre offset (degrees) */
	let zoom = $state({ k: 1, dx: 0, dy: 0 });
	let svgEl = $state<SVGSVGElement | null>(null);
	let dragging = false;
	let tip = $state<string | null>(null);
	/** hovered site's name — the black bottom-left card */
	let siteTip = $state<string | null>(null);

	// base (unzoomed) frame: centre + half-spans incl. padding.
	// With linked burn scars, the SCAR IS the frame (padded), so every
	// card linked to the same fire renders one identical window that
	// always shows the whole scar plus its regional surroundings — for
	// the Β. Εύβοια fire, the whole upper island (same rule in ZoneMap);
	// sites/rivers only extend it when they poke beyond the padding.
	// Without scars, the geometry frames itself. The ≥0.35°/0.27° pad
	// floors give single-site maps their ~30 km half-window and keep
	// every frame regional, never a tight crop.
	const base = $derived.by(() => {
		if (!pe || (!sites.length && !scars.length)) return null;
		const path0 = geoPath();
		let [gx0, gy0, gx1, gy1] = [Infinity, Infinity, -Infinity, -Infinity];
		for (const s of sites) {
			gx0 = Math.min(gx0, s.lon);
			gy0 = Math.min(gy0, s.lat);
			gx1 = Math.max(gx1, s.lon);
			gy1 = Math.max(gy1, s.lat);
		}
		for (const f of rivers) {
			const b = path0.bounds(f as Feature); // planar lon/lat bounds
			gx0 = Math.min(gx0, b[0][0]);
			gy0 = Math.min(gy0, b[0][1]);
			gx1 = Math.max(gx1, b[1][0]);
			gy1 = Math.max(gy1, b[1][1]);
		}
		if (scars.length) {
			let [fx0, fy0, fx1, fy1] = [Infinity, Infinity, -Infinity, -Infinity];
			for (const f of scars) {
				const b = path0.bounds(f);
				fx0 = Math.min(fx0, b[0][0]);
				fy0 = Math.min(fy0, b[0][1]);
				fx1 = Math.max(fx1, b[1][0]);
				fy1 = Math.max(fy1, b[1][1]);
			}
			// x floor 0.40°: at exact width-fit the shown window IS the
			// frame, and 0.35° just clips the Λιχάδα cape tip on Εύβοια
			const px = Math.max((fx1 - fx0) * 0.18, 0.4);
			const py = Math.max((fy1 - fy0) * 0.18, 0.27);
			// never crop a site/river: extend the fire frame when needed
			// (no-op when the geometry sits inside the padding, the norm)
			const X0 = Math.min(fx0 - px, gx0 - 0.03);
			const X1 = Math.max(fx1 + px, gx1 + 0.03);
			const Y0 = Math.min(fy0 - py, gy0 - 0.03);
			const Y1 = Math.max(fy1 + py, gy1 + 0.03);
			return { cx: (X0 + X1) / 2, cy: (Y0 + Y1) / 2, hx: (X1 - X0) / 2, hy: (Y1 - Y0) / 2 };
		}
		const sx = gx1 - gx0;
		const sy = gy1 - gy0;
		const padx = Math.max(sx * 0.18, 0.35);
		const pady = Math.max(sy * 0.18, 0.27);
		return {
			cx: (gx0 + gx1) / 2,
			cy: (gy0 + gy1) / 2,
			hx: sx / 2 + padx,
			hy: sy / 2 + pady
		};
	});

	const view = $derived.by(() => {
		if (!base) return null;
		const cx = base.cx + zoom.dx;
		const cy = base.cy + zoom.dy;
		const hx = base.hx / zoom.k;
		const hy = base.hy / zoom.k;
		// ring wound CLOCKWISE — d3-geo spherical polygons invert otherwise
		const frame = {
			type: 'Polygon' as const,
			coordinates: [
				[
					[cx - hx, cy - hy],
					[cx - hx, cy + hy],
					[cx + hx, cy + hy],
					[cx + hx, cy - hy],
					[cx - hx, cy - hy]
				]
			]
		};
		const proj = geoMercator();
		if (scars.length) {
			// fire-framed: fit by WIDTH at constant scale and centre the
			// frame vertically — same-fire cards share one zoom and one
			// horizontal window whatever each card's column height is;
			// taller/shorter cards only gain/lose vertical PADDING context
			proj.fitWidth(W - 12, frame);
			const fb = geoPath(proj).bounds(frame);
			const t = proj.translate();
			proj.translate([t[0] + 6, t[1] + (H - (fb[1][1] - fb[0][1])) / 2 - fb[0][1]]);
			// never crop the SCAR itself: at rest (k = 1) a very short
			// column falls back to a both-dims fit; while the user zooms,
			// the scar exceeding the viewport is the point
			if (zoom.k === 1) {
				let [sy0, sy1] = [Infinity, -Infinity];
				const p0 = geoPath(proj);
				for (const f of scars) {
					const b = p0.bounds(f);
					sy0 = Math.min(sy0, b[0][1]);
					sy1 = Math.max(sy1, b[1][1]);
				}
				if (sy1 - sy0 > H - 12)
					proj.fitExtent(
						[
							[6, 6],
							[W - 6, H - 6]
						],
						frame
					);
			}
		} else {
			proj.fitExtent(
				[
					[6, 6],
					[W - 6, H - 6]
				],
				frame
			);
		}
		const path = geoPath(proj);
		const baseR = sites.length > 8 ? 4.5 : 6;
		const pins = sites
			.map((s) => {
				const xy = proj([s.lon, s.lat]);
				if (!xy) return null;
				// stated area → true ground radius → projected pixels
				let r = baseR;
				let trueSize = false;
				if (s.stremmata && s.stremmata > 0) {
					const rM = Math.sqrt((s.stremmata * 1000) / Math.PI); // 1 στρ = 1,000 m²
					const dLon = rM / (111320 * Math.cos((s.lat * Math.PI) / 180));
					const xy2 = proj([s.lon + dLon, s.lat]);
					if (xy2) {
						const rpx = Math.abs(xy2[0] - xy[0]);
						trueSize = rpx > baseR;
						r = Math.max(rpx, baseR);
					}
				}
				return { s, x: xy[0], y: xy[1], r, trueSize };
			})
			.filter(
				(d): d is { s: SitePin; x: number; y: number; r: number; trueSize: boolean } =>
					d !== null
			);
		// a small fire (e.g. 27 ha) projects to ~2 px at regional zoom —
		// give it a minimum-size marker so every timeline dot has a
		// visible map counterpart
		const scarMarks = scars
			.map((f) => {
				const b = path.bounds(f);
				if (b[1][0] - b[0][0] >= 7 || b[1][1] - b[0][1] >= 7) return null;
				const c = path.centroid(f);
				return Number.isFinite(c[0]) ? { f, x: c[0], y: c[1] } : null;
			})
			.filter((d): d is { f: (typeof scars)[number]; x: number; y: number } => d !== null);
		return { path, pins, scarMarks, proj };
	});

	const zoomIn = () => (zoom = { ...zoom, k: Math.min(16, zoom.k * 1.6) });
	const zoomOut = () => {
		const k = Math.max(1, zoom.k / 1.6);
		zoom = k === 1 ? { k: 1, dx: 0, dy: 0 } : { ...zoom, k };
	};
	const home = () => (zoom = { k: 1, dx: 0, dy: 0 });

	let dragMoved = false;
	function onPointerDown(e: PointerEvent) {
		dragMoved = false;
		if (zoom.k <= 1) return;
		dragging = true;
		(e.currentTarget as Element).setPointerCapture(e.pointerId);
	}
	function onPointerMove(e: PointerEvent) {
		if (!dragging || !svgEl || !base) return;
		dragMoved = true;
		const unitPerPx = W / svgEl.clientWidth; // css px → viewBox units
		const degX = (2 * base.hx) / zoom.k / (W - 12);
		const degY = (2 * base.hy) / zoom.k / (H - 12);
		zoom = {
			k: zoom.k,
			dx: zoom.dx - e.movementX * unitPerPx * degX,
			dy: zoom.dy + e.movementY * unitPerPx * degY
		};
	}
	function onPointerUp() {
		dragging = false;
	}

	/** click anywhere NEAR a fire → zoom to it; the EFFIS shapes are
	 *  fragmented multipolygons, so hit-testing the paths alone would
	 *  demand pixel-perfect clicks on the shards */
	function onSvgClick(e: MouseEvent) {
		if (dragMoved) {
			dragMoved = false;
			return;
		}
		if (!view || !svgEl) return;
		const r = svgEl.getBoundingClientRect();
		const px = ((e.clientX - r.left) / r.width) * W;
		const py = ((e.clientY - r.top) / r.height) * H;
		const PAD = 24;
		let best: { f: (typeof scars)[number]; d2: number } | null = null;
		for (const f of scars) {
			const b = view.path.bounds(f);
			if (!Number.isFinite(b[0][0])) continue;
			if (px < b[0][0] - PAD || px > b[1][0] + PAD || py < b[0][1] - PAD || py > b[1][1] + PAD)
				continue;
			const cx = (b[0][0] + b[1][0]) / 2;
			const cy = (b[0][1] + b[1][1]) / 2;
			const d2 = (px - cx) ** 2 + (py - cy) ** 2;
			if (!best || d2 < best.d2) best = { f, d2 };
		}
		if (best) zoomToScar(best.f);
	}

	// the hover card states only the fire's date and size
	const scarTip = (f: Feature<Polygon | MultiPolygon, FireProps>): string =>
		`${f.properties.d ? dmy(f.properties.d) : f.properties.yr} · ${grInt(f.properties.ha)} ha`;
	// timeline-dot hover shows the same card without a map hover
	const shownTip = $derived.by(() => {
		if (tip) return tip;
		const f = selectedId === null ? null : scars.find((s) => s.properties.id === selectedId);
		return f ? scarTip(f) : null;
	});

	/** click near a fire → frame that fire's own bounds */
	function zoomToScar(f: Feature<Polygon | MultiPolygon, FireProps>) {
		if (!base) return;
		const b = geoPath().bounds(f); // planar lon/lat bounds
		const cx = (b[0][0] + b[1][0]) / 2;
		const cy = (b[0][1] + b[1][1]) / 2;
		const hx = Math.max(((b[1][0] - b[0][0]) / 2) * 1.5, 0.02);
		const hy = Math.max(((b[1][1] - b[0][1]) / 2) * 1.5, 0.016);
		const k = Math.min(16, Math.max(1, Math.min(base.hx / hx, base.hy / hy)));
		zoom = { k, dx: cx - base.cx, dy: cy - base.cy };
	}
</script>

{#if view}
	<figure class="sitemap">
		<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
		<svg
			bind:this={svgEl}
			viewBox="0 0 {W} {H}"
			role="img"
			aria-label="Work locations of this project"
			class:grab={zoom.k > 1}
			onpointerdown={onPointerDown}
			onpointermove={onPointerMove}
			onpointerup={onPointerUp}
			onpointercancel={onPointerUp}
			onclick={onSvgClick}
		>
			{#if pe}
				{#each pe.features as f (f.properties.pe)}
					<path d={view.path(f) ?? ''} class="land" />
				{/each}
			{/if}
			{#each rivers as f (f.properties.name)}
				<path d={view.path(f) ?? ''} class="river" />
				{#if view.proj(f.properties.label_pt)}
					{@const lp = view.proj(f.properties.label_pt)!}
					<text x={lp[0]} y={lp[1] - 5} class="riverlbl">{f.properties.name}</text>
				{/if}
			{/each}
			{#each scars as f (f.properties.id)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<path
					d={view.path(f) ?? ''}
					class="scar"
					class:sel={selectedId === f.properties.id}
					style:fill={fireColorOf(f)}
					onmouseenter={() => (tip = scarTip(f))}
					onmouseleave={() => (tip = null)}
				/>
			{/each}
			{#each view.scarMarks as m (m.f.properties.id)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<circle
					cx={m.x}
					cy={m.y}
					r="4.5"
					class="scarmark"
					class:sel={selectedId === m.f.properties.id}
					style:fill={fireColorOf(m.f)}
					onmouseenter={() => (tip = scarTip(m.f))}
					onmouseleave={() => (tip = null)}
				/>
			{/each}
			{#each view.pins as { s, x, y, r, trueSize }, i (i)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<circle
					cx={x}
					cy={y}
					{r}
					class="pin"
					class:truesize={trueSize}
					style:fill={pinColor}
					onmouseenter={() =>
						(siteTip =
							s.name +
							(s.stremmata ? ` — ${grInt(s.stremmata)} στρ.` : '') +
							(APPROX.has(s.geo_precision ?? '') ? ' (κατά προσέγγιση)' : ''))}
					onmouseleave={() => (siteTip = null)}
				/>
			{/each}
		</svg>
		<!-- controls show wherever zooming is possible: multi-site maps,
		     any map with a clickable fire, and ALWAYS once zoomed in —
		     click-to-zoom must never strand the reader without a way back -->
		{#if sites.length > 1 || scars.length > 0 || zoom.k > 1}
			<div class="zoomctl">
				<button onclick={zoomIn} title="Zoom in" aria-label="Zoom in">+</button>
				<button onclick={zoomOut} title="Zoom out" aria-label="Zoom out">−</button>
				<button onclick={home} title="Reset view" aria-label="Reset view">⌂</button>
			</div>
		{/if}
		{#if shownTip}
			<div class="tip">{shownTip}</div>
		{/if}
		{#if siteTip}
			<div class="tip sitecard">{siteTip}</div>
		{/if}
	</figure>
{/if}

<style>
	.sitemap {
		margin: 0 0 var(--sp-2);
		max-width: 460px;
		position: relative;
	}
	/* same palette as the sponsored-works overview map:
	   grey sea, white land, --line strokes */
	svg {
		width: 100%;
		height: auto;
		display: block;
		background: #f2f2f2;
		border: none;
		border-radius: 4px;
		touch-action: none;
	}
	svg.grab {
		cursor: grab;
	}
	.land {
		fill: #fff;
		stroke: var(--line);
		stroke-width: 0.7;
		vector-effect: non-scaling-stroke;
	}
	/* solid per-fire fills arrive inline via fireColorOf */
	.scar {
		stroke: #6b2d35;
		stroke-width: 0.9;
		cursor: pointer;
	}
	.scar:hover,
	.scar.sel {
		filter: brightness(0.82);
	}
	.scarmark {
		stroke: #6b2d35;
		stroke-width: 0.9;
		cursor: pointer;
	}
	.scarmark:hover,
	.scarmark.sel {
		filter: brightness(0.82);
	}
	/* ONE colour for every site pin — the project's timeline-bar hue,
	   passed inline; the precision qualifier lives in the hover card
	   (user decisions 2026-08-16) */
	.pin {
		stroke: none;
	}
	/* drawn at the stated area's true ground size: a touch translucent so
	   the scar stays readable underneath */
	.pin.truesize {
		fill-opacity: 0.75;
	}
	.river {
		fill: none;
		stroke: #6d9dc5;
		stroke-width: 1.6;
		opacity: 0.85;
	}
	.riverlbl {
		font-size: 10px;
		font-style: italic;
		fill: #46779e;
		text-anchor: middle;
		paint-order: stroke;
		stroke: #fff;
		stroke-width: 2px;
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
		border: 1px solid var(--line);
		border-radius: 4px;
		background: color-mix(in srgb, var(--paper) 92%, transparent);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.zoomctl button:hover {
		color: var(--ink);
		background: var(--paper);
	}
	/* the fire card: black, white lettering, top-left — mirroring the
	   zoom buttons in the opposite corner; the site card shares the look
	   but docks bottom-left */
	.tip {
		position: absolute;
		top: var(--sp-2);
		left: var(--sp-2);
		background: #000;
		color: #fff;
		border-radius: 4px;
		padding: var(--sp-1) var(--sp-2);
		font-size: var(--fs-13);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}
	.tip.sitecard {
		top: auto;
		bottom: var(--sp-2);
	}
</style>
