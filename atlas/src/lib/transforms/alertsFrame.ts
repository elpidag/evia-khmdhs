/**
 * The frame of the story's Figure 04 — the «112» alerts of August 2021 on
 * ONE fixed national window (user, 2026-09-02): Corfu to Rhodes, Crete to
 * Thrace. The box is 1013 × 1008 km in Mercator metres, so fitting it into
 * a square leaves a 0.5 % letterbox; the contract everything shares is
 * therefore the INVERTED CORNERS of the fitted square, not the box — the
 * satellite plate is baked for those corners (scripts/build_alerts_base.py,
 * via atlas/static/geo/alerts_frame.json) and the canvas draws it edge to
 * edge. Pinned by alertsFrame.test.ts, the relief frame contract's sibling.
 *
 * Erasable TypeScript only and no `$lib` alias: scripts/build-alerts-frame.mjs
 * imports this module directly under node to emit the JSON, so the emitter
 * and the client can never disagree.
 */
import { geoMercator } from 'd3-geo';
import type { GeoProjection } from 'd3-geo';
import type { Polygon } from 'geojson';

/** [[west, south], [east, north]] in lon/lat */
export const ALERTS_BOX: [[number, number], [number, number]] = [
	[19.5, 34.7],
	[28.6, 41.8]
];

/** the baked plate's side in pixels — 3× the 540 px figure square */
export const BAKE_PX = 1620;

const [[west, south], [east, north]] = ALERTS_BOX;

/** the ring wound CLOCKWISE (SW → NW → NE → SE), the order SiteMap uses:
 *  d3-geo reads polygons spherically and a CCW ring selects the rest of
 *  the world, which fitExtent would then frame */
export const FRAME_RING: [number, number][] = [
	[west, south],
	[west, north],
	[east, north],
	[east, south],
	[west, south]
];

export const FRAME_POLYGON: Polygon = { type: 'Polygon', coordinates: [FRAME_RING] };

/** lon/lat → pixels of a `size` × `size` square holding the whole box */
export function alertsProjection(size: number): GeoProjection {
	return geoMercator().fitExtent(
		[
			[0, 0],
			[size, size]
		],
		FRAME_POLYGON
	);
}

/** the lon/lat of the square's corners — the plate's georeference; the
 *  same at every size, because the fit is a similarity */
export function frameCorners(size: number): { nw: [number, number]; se: [number, number] } {
	const p = alertsProjection(size);
	const nw = p.invert!([0, 0]) as [number, number];
	const se = p.invert!([size, size]) as [number, number];
	return { nw, se };
}
