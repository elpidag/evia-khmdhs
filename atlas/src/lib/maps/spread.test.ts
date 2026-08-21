import { describe, it, expect } from 'vitest';
import { feature } from 'topojson-client';
import { geoContains } from 'd3-geo';
import type { FeatureCollection, MultiPolygon } from 'geojson';
import type { Topology } from 'topojson-specification';
import peTopoRaw from '../../../static/geo/pe.topo.json';
import { spreadOverlaps } from './useGeo';

/** the drawn country layer — the same file PaperMap loads */
function landLayer(): FeatureCollection<MultiPolygon> {
	const topo = peTopoRaw as unknown as Topology;
	const key = Object.keys(topo.objects)[0];
	return feature(topo, topo.objects[key]) as unknown as FeatureCollection<MultiPolygon>;
}

describe('spreadOverlaps', () => {
	it('spreads co-located points and leaves singletons alone', () => {
		const pts = [
			{ lat: 38.0, lon: 23.0, id: 'a' },
			{ lat: 38.0, lon: 23.0, id: 'b' },
			{ lat: 39.0, lon: 22.0, id: 'c' }
		];
		const out = spreadOverlaps(pts, 0.02);
		expect(out).toHaveLength(3);
		const c = out.find((p) => p.id === 'c')!;
		expect([c.lat2, c.lon2]).toEqual([39.0, 22.0]);
		const a = out.find((p) => p.id === 'a')!;
		const b = out.find((p) => p.id === 'b')!;
		expect(a.lat2 === b.lat2 && a.lon2 === b.lon2).toBe(false);
	});

	it('skips spiral slots the land predicate refuses, and stays put if none is on land', () => {
		// "land" = everything at or west of lon 23.0
		const onLand = (_lat: number, lon: number) => lon <= 23.0;
		const pts = Array.from({ length: 6 }, (_, i) => ({ lat: 38.0, lon: 23.0, id: i }));
		const out = spreadOverlaps(pts, 0.02, onLand);
		for (const p of out) expect(onLand(p.lat2, p.lon2)).toBe(true);
		// a predicate nothing satisfies: every point keeps its own position
		const stuck = spreadOverlaps(pts, 0.02, () => false);
		for (const p of stuck) expect([p.lat2, p.lon2]).toEqual([38.0, 23.0]);
	});

	it('keeps every spread registered-office dot on the drawn land — five seats share Λίμνη, nine share Καβάλα (user, 2026-08-21)', () => {
		const land = landLayer();
		const onLand = (lat: number, lon: number) => land.features.some((f) => geoContains(f, [lon, lat]));
		// the seats as geocoded: a waterfront village shared by five ventures,
		// a Kavala street shared by nine parties, a Thessaloniki block by three
		const groups: [number, number, number][] = [
			[38.765075, 23.317626, 5], // Λίμνη Ευβοίας
			[40.937884, 24.410015, 9], // Μεγάλου Αλεξάνδρου 27, Καβάλα
			[37.9646, 23.4963, 4] // Σαλαμίνα town
		];
		const pts = groups.flatMap(([lat, lon, n]) => Array.from({ length: n }, (_, i) => ({ lat, lon, id: `${lat}-${i}` })));
		for (const [lat, lon] of groups) expect(onLand(lat, lon)).toBe(true);
		const out = spreadOverlaps(pts, 0.02, onLand);
		for (const p of out) expect(onLand(p.lat2, p.lon2)).toBe(true);
		// and the spread still separates them (not all collapsed onto one point)
		const distinct = new Set(out.map((p) => `${p.lat2.toFixed(5)}|${p.lon2.toFixed(5)}`));
		expect(distinct.size).toBeGreaterThan(groups.length);
	});
});
