import { describe, expect, it } from 'vitest';
import { geoArea, geoMercator } from 'd3-geo';
import frame from '../../../static/geo/alerts_frame.json';
import { ALERTS, placed, placesOf } from './alerts';
import { ALERTS_BOX, BAKE_PX, FRAME_POLYGON, alertsProjection, frameCorners } from './alertsFrame';

/** The satellite plate (alerts_base.avif) is baked for the frame recorded in
 *  alerts_frame.json, which build-alerts-frame.mjs writes from THIS module.
 *  If the box, the size or the fit ever changes without `npm run geo:alerts`
 *  + the bake, the plate silently misregisters. This pins the contract, as
 *  maps/frame.test.ts does for the relief. */
describe('the alerts frame contract', () => {
	it('alerts_frame.json matches a fresh fit of the box', () => {
		const p = alertsProjection(frame.w);
		expect(frame.w).toBe(BAKE_PX);
		expect(frame.h).toBe(BAKE_PX);
		expect(frame.box).toEqual(ALERTS_BOX);
		expect(p.scale()).toBeCloseTo(frame.scale, 6);
		expect(p.translate()[0]).toBeCloseTo(frame.translate[0], 6);
		expect(p.translate()[1]).toBeCloseTo(frame.translate[1], 6);
	});

	it('the corners invert consistently', () => {
		const p = geoMercator().scale(frame.scale).translate([frame.translate[0], frame.translate[1]]);
		const nw = p([frame.nw[0], frame.nw[1]])!;
		const se = p([frame.se[0], frame.se[1]])!;
		expect(nw[0]).toBeCloseTo(0, 4);
		expect(nw[1]).toBeCloseTo(0, 4);
		expect(se[0]).toBeCloseTo(frame.w, 4);
		expect(se[1]).toBeCloseTo(frame.h, 4);
	});

	it('the fit is a similarity: the corners are the same at every size', () => {
		const a = frameCorners(540);
		const b = frameCorners(BAKE_PX);
		expect(a.nw[0]).toBeCloseTo(b.nw[0], 9);
		expect(a.nw[1]).toBeCloseTo(b.nw[1], 9);
		expect(a.se[0]).toBeCloseTo(b.se[0], 9);
		expect(a.se[1]).toBeCloseTo(b.se[1], 9);
		expect(alertsProjection(BAKE_PX).scale() / alertsProjection(540).scale()).toBeCloseTo(3, 9);
	});

	it('the frame ring is wound for d3-geo (it selects the box, not the world)', () => {
		expect(geoArea(FRAME_POLYGON)).toBeLessThan(0.1);
	});

	it('holds the decided box with at most a hair of letterbox', () => {
		const { nw, se } = frameCorners(540);
		expect(nw[0]).toBeCloseTo(ALERTS_BOX[0][0], 6);
		expect(se[0]).toBeCloseTo(ALERTS_BOX[1][0], 6);
		expect(nw[1]).toBeGreaterThanOrEqual(ALERTS_BOX[1][1]);
		expect(se[1]).toBeLessThanOrEqual(ALERTS_BOX[0][1]);
		expect(nw[1] - ALERTS_BOX[1][1]).toBeLessThan(0.05);
		expect(ALERTS_BOX[0][1] - se[1]).toBeLessThan(0.05);
	});

	it('projects every placed alert village inside the square', () => {
		const p = alertsProjection(540);
		let n = 0;
		for (const a of ALERTS) {
			for (const pl of placesOf(a)) {
				if (!placed(pl)) continue;
				const [x, y] = p([pl.lon, pl.lat])!;
				expect(x, pl.nameEn).toBeGreaterThanOrEqual(0);
				expect(x, pl.nameEn).toBeLessThanOrEqual(540);
				expect(y, pl.nameEn).toBeGreaterThanOrEqual(0);
				expect(y, pl.nameEn).toBeLessThanOrEqual(540);
				n++;
			}
		}
		expect(n).toBeGreaterThan(100);
	});
});
