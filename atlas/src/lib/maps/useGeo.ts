/** Module-cached TopoJSON fetches — every map on every page shares one copy. */
import { feature } from 'topojson-client';
import type {
	Feature,
	FeatureCollection,
	LineString,
	Polygon,
	MultiPolygon,
	MultiLineString
} from 'geojson';
import type { Topology } from 'topojson-specification';

export interface PeProps {
	pe: string;
	name: string;
}

type Fetch = typeof globalThis.fetch;

const cache = new Map<string, Promise<unknown>>();

/** the TopoJSON itself, fetched once — the features are cut from it, and
 *  so is any mesh of its shared edges */
export function loadTopology(fetch: Fetch, url: string): Promise<Topology> {
	const key = url + '#topo';
	if (!cache.has(key)) {
		cache.set(
			key,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json() as Promise<Topology>;
			})
		);
	}
	return cache.get(key) as Promise<Topology>;
}

async function load<T>(fetch: Fetch, url: string, object: string): Promise<T> {
	if (!cache.has(url)) {
		cache.set(
			url,
			loadTopology(fetch, url).then((topo) => feature(topo, topo.objects[object]))
		);
	}
	return cache.get(url) as Promise<T>;
}

export const PE_TOPO_URL = '/geo/pe.topo.json';

export const loadPe = (fetch: Fetch) =>
	load<FeatureCollection<MultiPolygon, PeProps>>(fetch, PE_TOPO_URL, 'pe');

export const loadPeHires = (fetch: Fetch) =>
	load<FeatureCollection<MultiPolygon, PeProps>>(fetch, '/geo/pe_hires.topo.json', 'pe');

export const loadMuniBorders = (fetch: Fetch) =>
	load<FeatureCollection<MultiLineString, { pe: string }>>(
		fetch,
		'/geo/muni_borders.topo.json',
		'muni'
	);

export interface ZoneProps {
	zone: string;
	name: string;
	basin: string;
	table_stremmata: number;
	extracted_stremmata: number;
	centroid: [number, number];
}

/** the 9 digitised Β. Εύβοια works zones (plain GeoJSON, module-cached) */
export const loadEviaZones = (
	fetch: Fetch
): Promise<FeatureCollection<Polygon | MultiPolygon, ZoneProps>> => {
	const url = '/geo/evia_works_zones.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<FeatureCollection<Polygon | MultiPolygon, ZoneProps>>;
};

export interface RiverProps {
	/** river name as in OSM (Greek) */
	name: string;
	en: string;
	/** the project ΑΔΑs this river is curated to belong to */
	projects: string[];
	/** [lon, lat] midpoint of the longest branch — name-label anchor */
	label_pt: [number, number];
}

export interface FireProps {
	/** stable EFFIS feature id — anadohoi effis_scars links resolve on it */
	id: number;
	/** fire year (from the EFFIS initialdat) */
	yr: number;
	/** fire start date, ISO (EFFIS initialdat) — timeline markers */
	d?: string;
	ha: number;
	name: string;
}

/** EFFIS burnt scars 2008–2025, display copy (WGS84, simplified, CW —
 *  scripts/build_effis_layer.py). Attribution required on display:
 *  «© European Union, Copernicus Emergency Management Service — EFFIS». */
export const loadEffisFires = (
	fetch: Fetch
): Promise<FeatureCollection<Polygon | MultiPolygon, FireProps>> => {
	const url = '/geo/effis_fires.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<FeatureCollection<Polygon | MultiPolygon, FireProps>>;
};

export interface BurnProps {
	/** ISO day of the product's burn-date estimate */
	day: string;
	doy: number;
	/** 500 m pixels burnt that day inside the frame and Greek land */
	px: number;
	km2: number;
}

/** The burnt ground of August 2021, day by day, as INCREMENTS (WGS84,
 *  simplified, CW — scripts/build_alerts_burn.py from NASA VIIRS VNP64A1,
 *  tile h19v05: mainland only, Rhodes and Grevena not covered). The story's
 *  Figure 04 draws the increments up to its clock's day. Attribution
 *  required on display: «NASA VIIRS VNP64A1 burned area, 500 m». */
export const loadAlertsBurn = (
	fetch: Fetch
): Promise<FeatureCollection<Polygon | MultiPolygon, BurnProps>> => {
	const url = '/geo/alerts_burn_2021.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<FeatureCollection<Polygon | MultiPolygon, BurnProps>>;
};

/** Context rivers for river-scoped sponsored projects (OSM courses,
 *  scripts/build_river_layer.py). Attribution required on display:
 *  «© OpenStreetMap contributors», marked approximate. */
export const loadRivers = (
	fetch: Fetch
): Promise<FeatureCollection<LineString | MultiLineString, RiverProps>> => {
	const url = '/geo/context_rivers.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<FeatureCollection<LineString | MultiLineString, RiverProps>>;
};

/** Municipality POLYGONS (all 325, ~250 m). Fetched only by a page that
 *  outlines a δήμος — `scripts/build_muni_polygons.py` reconstructs them
 *  from the Π.Ε. outlines and the interior border lines. */
export const loadMunicipalities = (
	fetch: Fetch
): Promise<FeatureCollection<GeoJSON.MultiPolygon | GeoJSON.Polygon, MuniProps>> => {
	const url = '/geo/greek_muni.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<
		FeatureCollection<GeoJSON.MultiPolygon | GeoJSON.Polygon, MuniProps>
	>;
};

/** CONTEXT LAND: the neighbouring countries and the Athos peninsula — the
 *  land around the frame, so Greece is not drawn floating in an empty sea
 *  (user, 2026-08-22). Inert scenery: no data, no hover, no clicks.
 *  Built by `scripts/build_neighbours.py` (Eurostat GISCO 1:1M + OSM). */
export const loadNeighbours = (
	fetch: Fetch
): Promise<FeatureCollection<GeoJSON.MultiPolygon | GeoJSON.Polygon | GeoJSON.MultiLineString, NeighbourProps>> => {
	const url = '/geo/neighbours.geojson';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => {
				if (!r.ok) throw new Error(`${url}: ${r.status}`);
				return r.json();
			})
		);
	}
	return cache.get(url) as Promise<
		FeatureCollection<GeoJSON.MultiPolygon | GeoJSON.Polygon | GeoJSON.MultiLineString, NeighbourProps>
	>;
};

export interface NeighbourProps {
	/** 'neighbour' (a country) | 'athos' (the monastic state) |
	 *  'border' (the dashed Greek land border, a MultiLineString) */
	kind: string;
	id: string;
}

export interface MuniProps {
	code: string;
	name: string;
	pe: string;
}

export const loadCentroids = (fetch: Fetch): Promise<Record<string, [number, number]>> => {
	const url = '/geo/pe_centroids.json';
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url).then((r) => r.json())
		);
	}
	return cache.get(url) as Promise<Record<string, [number, number]>>;
};

/** Deterministic sunflower-spiral de-overlap for co-located points
 *  (port of GeoCommon.spreadOverlaps — golden angle, no RNG).
 *  `onLand(lat, lon)` — when given, a spiral slot that fails it (the sea)
 *  is skipped and the next slot tried, so a group of seats sharing one
 *  waterfront point fans out along the coast, never into the water;
 *  if no slot within the search window is on land the point stays put. */
/** lon/lat bbox: [x0, y0, x1, y1] */
export type LonLatBBox = [number, number, number, number];

function ringsBBox(rings: number[][][]): LonLatBBox {
	let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
	for (const r of rings)
		for (const [x, y] of r) {
			if (x < x0) x0 = x;
			if (y < y0) y0 = y;
			if (x > x1) x1 = x;
			if (y > y1) y1 = y;
		}
	return [x0, y0, x1, y1];
}

/** gap between two lon/lat bboxes (0 when they touch or overlap) */
function bboxGap(a: LonLatBBox, b: LonLatBBox): number {
	const dx = Math.max(0, a[0] - b[2], b[0] - a[2]);
	const dy = Math.max(0, a[1] - b[3], b[1] - a[3]);
	return Math.hypot(dx, dy);
}

/**
 * A regional unit reduced to the island/land PARTS that belong with the
 * subject (user, 2026-08-26). Framing a Π.Ε. whole is the rule — but
 * Π.Ε. Ρόδου carries Καστελλόριζο 1,3° east of Rhodes, so «whole» threw
 * the window across open sea onto the Turkish coast and the works became
 * a speck. Parts further than `gap` (widened for a large subject) from
 * the subject are dropped; the nearest part is always kept, so nothing
 * ever frames on emptiness. With no subject the largest part anchors.
 */
export function nearParts<P>(
	f: Feature<Polygon | MultiPolygon, P>,
	subject: LonLatBBox | null,
	gap = 0.6
): Feature<Polygon | MultiPolygon, P> {
	const parts: number[][][][] =
		f.geometry.type === 'Polygon'
			? [f.geometry.coordinates as number[][][]]
			: (f.geometry.coordinates as number[][][][]);
	if (parts.length < 2) return f;
	const boxes = parts.map((p) => ringsBBox(p));
	let anchor = subject;
	if (!anchor) {
		let best = 0;
		boxes.forEach((b, i) => {
			const area = (b[2] - b[0]) * (b[3] - b[1]);
			if (area > (boxes[best][2] - boxes[best][0]) * (boxes[best][3] - boxes[best][1])) best = i;
		});
		anchor = boxes[best];
	}
	const reach = Math.max(gap, 1.5 * Math.max(anchor[2] - anchor[0], anchor[3] - anchor[1]));
	const gaps = boxes.map((b) => bboxGap(b, anchor!));
	const nearest = gaps.indexOf(Math.min(...gaps));
	const kept = parts.filter((_, i) => gaps[i] <= reach || i === nearest);
	if (kept.length === parts.length) return f;
	return {
		...f,
		geometry: { type: 'MultiPolygon', coordinates: kept }
	} as Feature<Polygon | MultiPolygon, P>;
}

export function spreadOverlaps<T extends { lat: number; lon: number }>(
	points: T[],
	stepDeg = 0.028,
	onLand?: (lat: number, lon: number) => boolean
): (T & { lat2: number; lon2: number })[] {
	const groups = new Map<string, T[]>();
	for (const p of points) {
		const key = `${p.lat.toFixed(3)}|${p.lon.toFixed(3)}`;
		const g = groups.get(key);
		if (g) g.push(p);
		else groups.set(key, [p]);
	}
	const out: (T & { lat2: number; lon2: number })[] = [];
	const GOLDEN = Math.PI * (3 - Math.sqrt(5));
	for (const g of groups.values()) {
		if (g.length === 1) {
			out.push({ ...g[0], lat2: g[0].lat, lon2: g[0].lon });
			continue;
		}
		let slot = 0;
		for (const p of g) {
			const cand = (s: number): [number, number] => {
				const r = stepDeg * Math.sqrt(s + 0.5);
				const a = s * GOLDEN;
				return [p.lat + r * Math.sin(a), p.lon + (r * Math.cos(a)) / Math.cos((p.lat * Math.PI) / 180)];
			};
			let pos = cand(slot);
			if (onLand) {
				let tries = 0;
				while (!onLand(pos[0], pos[1]) && tries < 40) {
					slot++;
					tries++;
					pos = cand(slot);
				}
				if (tries >= 40 && !onLand(pos[0], pos[1])) pos = [p.lat, p.lon];
			}
			out.push({ ...p, lat2: pos[0], lon2: pos[1] });
			slot++;
		}
	}
	return out;
}

/** sqrt-normalised colour ramp lookup (port of GeoCommon.makeChoro). */
export function makeChoro(ramp: string[], maxV: number): (v: number) => string {
	return (v: number) => {
		if (!v || v <= 0 || maxV <= 0) return 'var(--land-empty)';
		const t = Math.sqrt(v / maxV);
		return ramp[Math.min(ramp.length - 1, Math.floor(t * ramp.length))];
	};
}

// black-white-grayscale only on the Anti-nero surfaces (user, 2026-08-20)
export const RAMP_WORKS = [
	'color-mix(in srgb, var(--ink) 6.5%, var(--paper))',
	'color-mix(in srgb, var(--ink) 15.5%, var(--paper))',
	'color-mix(in srgb, var(--ink) 26.2%, var(--paper))',
	'color-mix(in srgb, var(--ink) 39.6%, var(--paper))',
	'color-mix(in srgb, var(--ink) 54.3%, var(--paper))',
	'color-mix(in srgb, var(--ink) 71.3%, var(--paper))',
	'color-mix(in srgb, var(--ink) 88.7%, var(--paper))',
	'color-mix(in srgb, var(--ink) 53.3%, black)'
];

/** the ΔΑΣΕ pages' green ramp (the allocation maps, the card map) */
export const RAMP_DASE = [
	'color-mix(in oklab, var(--c-dase) 10.6%, var(--paper))',
	'color-mix(in oklab, var(--c-dase) 24.7%, var(--paper))',
	'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 38%, white) 96%, black)',
	'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 61%, white) 95%, black)',
	'color-mix(in srgb, color-mix(in oklab, var(--c-dase) 81%, white) 90%, black)',
	'color-mix(in srgb, var(--c-dase) 84.8%, black)',
	'color-mix(in oklab, var(--c-dase) 72.4%, black)',
	'color-mix(in oklab, var(--c-dase) 56.1%, black)'
];

// unused since the 4-mode maps retired; kept as an approximate one-anchor
// family of --c-cat-blue (the old multi-stop blues rotated hue)
export const RAMP_HOME = [
	'color-mix(in srgb, var(--c-cat-blue) 3.6%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 9.4%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 18.7%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 31.4%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 46.5%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 61.8%, var(--paper))',
	'color-mix(in oklab, var(--c-cat-blue) 79.3%, var(--paper))',
	'var(--c-cat-blue)'
];
