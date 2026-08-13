import { describe, expect, it } from 'vitest';
import { geoMercator } from 'd3-geo';
import { feature } from 'topojson-client';
import type { FeatureCollection } from 'geojson';
import type { Topology } from 'topojson-specification';
import frame from '../../../static/geo/frame.json';
import peTopoRaw from '../../../static/geo/pe.topo.json';

/** The baked relief (relief*.avif) is warped to the frame recorded in
 *  frame.json at build time. PaperMap computes the same frame at runtime
 *  with geoMercator().fitSize on the coarse layer — if the layer or the
 *  frame size ever changes without re-running `npm run geo` + the relief
 *  bake, the underlay silently misregisters. This pins the contract. */
describe('relief frame contract', () => {
	const peTopo = peTopoRaw as unknown as Topology;

	it('frame.json matches a fresh fitSize on the shipped coarse layer', () => {
		const coarse = feature(peTopo, peTopo.objects.pe) as unknown as FeatureCollection;
		const p = geoMercator().fitSize([frame.w, frame.h], coarse);
		expect(p.scale()).toBeCloseTo(frame.scale, 6);
		expect(p.translate()[0]).toBeCloseTo(frame.translate[0], 6);
		expect(p.translate()[1]).toBeCloseTo(frame.translate[1], 6);
	});

	it('frame corners invert consistently', () => {
		const p = geoMercator()
			.scale(frame.scale)
			.translate([frame.translate[0], frame.translate[1]]);
		const nw = p([frame.nw[0], frame.nw[1]])!;
		const se = p([frame.se[0], frame.se[1]])!;
		expect(nw[0]).toBeCloseTo(0, 4);
		expect(nw[1]).toBeCloseTo(0, 4);
		expect(se[0]).toBeCloseTo(frame.w, 4);
		expect(se[1]).toBeCloseTo(frame.h, 4);
	});
});
