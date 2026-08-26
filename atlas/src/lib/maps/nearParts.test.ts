import { describe, it, expect } from 'vitest';
import { feature } from 'topojson-client';
import { geoBounds } from 'd3-geo';
import type { Feature, FeatureCollection, MultiPolygon } from 'geojson';
import type { Topology } from 'topojson-specification';
import peTopoRaw from '../../../static/geo/pe.topo.json';
import { nearParts, type LonLatBBox } from './useGeo';

/** the drawn country layer — the same file every map loads */
function peLayer(): FeatureCollection<MultiPolygon> {
	const topo = peTopoRaw as unknown as Topology;
	const key = Object.keys(topo.objects)[0];
	return feature(topo, topo.objects[key]) as unknown as FeatureCollection<MultiPolygon>;
}

const unit = (pe: string): Feature<MultiPolygon> => {
	const f = peLayer().features.find((g) => (g.properties as { pe: string }).pe === pe);
	if (!f) throw new Error(`missing ${pe}`);
	return f;
};
const spanOf = (f: Feature<MultiPolygon>) => {
	const [[x0, y0], [x1, y1]] = geoBounds(f);
	return { x: x1 - x0, y: y1 - y0, x0, x1, y0, y1 };
};

describe('nearParts — the framed unit keeps the parts that belong with the subject', () => {
	// user, 2026-08-26: Π.Ε. Ρόδου carries Καστελλόριζο 1,3° east of
	// Rhodes, so framing the unit whole threw the window across open sea
	// onto the Turkish coast and the burnt area became a speck
	it('drops Καστελλόριζο when the subject is on Rhodes', () => {
		const rhodes = unit('Π.Ε. Ρόδου');
		expect(spanOf(rhodes).x).toBeGreaterThan(2); // whole unit: ~2,36°
		// the 2023 burn scar's own extent on Rhodes
		const subject: LonLatBBox = [27.85, 36.05, 28.2, 36.4];
		const near = nearParts(rhodes, subject) as Feature<MultiPolygon>;
		const s = spanOf(near);
		expect(s.x).toBeLessThan(1.2);
		expect(s.x1).toBeLessThan(29); // Καστελλόριζο sits at 29,56°E
		// Rhodes itself stays whole
		expect(s.x0).toBeLessThan(27.7);
		expect(s.y0).toBeLessThan(35.9);
	});

	it('keeps Σαμοθράκη when the subject is the Dadia forest', () => {
		const evros = unit('Π.Ε. Έβρου');
		const subject: LonLatBBox = [26.0, 41.0, 26.3, 41.4]; // the Dadia scar
		const near = nearParts(evros, subject) as Feature<MultiPolygon>;
		// the island lies at 25,45..25,70 — inside the reach, so still framed
		expect(spanOf(near).x0).toBeLessThan(25.5);
	});

	it('anchors on the largest part when there is no subject', () => {
		const near = nearParts(unit('Π.Ε. Ρόδου'), null) as Feature<MultiPolygon>;
		expect(spanOf(near).x1).toBeLessThan(29);
	});

	it('leaves a single-part unit untouched', () => {
		const attica = unit('Π.Ε. Κεντρικού Τομέα Αθηνών');
		expect(nearParts(attica, null)).toBe(attica);
	});
});
