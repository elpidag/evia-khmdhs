/** Module-cached TopoJSON fetches — every map on every page shares one copy. */
import { feature } from 'topojson-client';
import type { FeatureCollection, LineString, Polygon, MultiPolygon, MultiLineString } from 'geojson';
import type { Topology } from 'topojson-specification';

export interface PeProps {
	pe: string;
	name: string;
}

type Fetch = typeof globalThis.fetch;

const cache = new Map<string, Promise<unknown>>();

async function load<T>(fetch: Fetch, url: string, object: string): Promise<T> {
	if (!cache.has(url)) {
		cache.set(
			url,
			fetch(url)
				.then((r) => {
					if (!r.ok) throw new Error(`${url}: ${r.status}`);
					return r.json() as Promise<Topology>;
				})
				.then((topo) => feature(topo, topo.objects[object]))
		);
	}
	return cache.get(url) as Promise<T>;
}

export const loadPe = (fetch: Fetch) =>
	load<FeatureCollection<MultiPolygon, PeProps>>(fetch, '/geo/pe.topo.json', 'pe');

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
 *  (port of GeoCommon.spreadOverlaps — golden angle, no RNG). */
export function spreadOverlaps<T extends { lat: number; lon: number }>(
	points: T[],
	stepDeg = 0.028
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
		g.forEach((p, i) => {
			const r = stepDeg * Math.sqrt(i + 0.5);
			const a = i * GOLDEN;
			out.push({
				...p,
				lat2: p.lat + r * Math.sin(a),
				lon2: p.lon + (r * Math.cos(a)) / Math.cos((p.lat * Math.PI) / 180)
			});
		});
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

export const RAMP_WORKS = [
	'#cbe4d1',
	'#b0d5be',
	'#93c6a8',
	'#6fb28c',
	'#578f6e',
	'#406e55',
	'#2a4a38',
	'#16241c'
];

export const RAMP_HOME = [
	'#f2f7fe',
	'#dcebfb',
	'#bcd8f5',
	'#92beec',
	'#64a0df',
	'#3d7fcb',
	'#2258a5',
	'#0d366b'
];
