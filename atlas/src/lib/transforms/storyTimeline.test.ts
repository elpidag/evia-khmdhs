import { describe, expect, it } from 'vitest';
import {
	AXIS_TOP,
	COLLAPSED_X,
	LANES,
	LANE_X,
	axisHeight,
	fractionalYear,
	storyDate,
	yOfDate,
	yearStops
} from './storyTimeline';

describe('the story timeline\'s year scale', () => {
	const stops = yearStops();

	it('runs from 2016 to 2026, one stop a year, top to bottom', () => {
		expect(stops[0]).toEqual({ year: 2016, y: AXIS_TOP, labelled: true });
		expect(stops[stops.length - 1].year).toBe(2026);
		for (let i = 1; i < stops.length; i++) {
			expect(stops[i].year).toBe(stops[i - 1].year + 1);
			expect(stops[i].y).toBeGreaterThan(stops[i - 1].y);
		}
	});

	it('compresses 2016–2018, as the artboard does', () => {
		const pitch = (a: number, b: number) => stops[b].y - stops[a].y;
		// the first two years take materially less room than the later ones
		expect(pitch(0, 1)).toBeLessThan(pitch(2, 3) * 0.7);
		expect(pitch(1, 2)).toBeLessThan(pitch(2, 3) * 0.7);
	});

	it('spaces 2017 but does not name it, as the artboard does', () => {
		const y2017 = stops.find((s) => s.year === 2017)!;
		expect(y2017.labelled).toBe(false);
		expect(stops.filter((s) => !s.labelled)).toHaveLength(1);
	});

	it('fits the whole span in the artboard\'s column', () => {
		// the collapsed artboard draws 2016 → 2026 inside ~850 px
		expect(axisHeight(stops)).toBeGreaterThan(700);
		expect(axisHeight(stops)).toBeLessThan(900);
	});
});

describe('yOfDate', () => {
	const stops = yearStops();
	const yr = (y: number) => stops.find((s) => s.year === y)!.y;

	it('puts a year mark exactly on its stop', () => {
		expect(yOfDate('2020', stops)).toBeCloseTo(yr(2020), 6);
		expect(yOfDate('2020-01-01', stops)).toBeCloseTo(yr(2020), 6);
	});

	it('lands a mid-year date between its own year and the next', () => {
		const y = yOfDate('2018-07-23', stops);
		expect(y).toBeGreaterThan(yr(2018));
		expect(y).toBeLessThan(yr(2019));
		// July is a little past the middle of the year
		expect(y).toBeCloseTo(yr(2018) + 0.556 * (yr(2019) - yr(2018)), 1);
	});

	it('is monotonic across the whole story', () => {
		const dates = ['2016', '2018-07', '2018-12', '2020-02-07', '2021-08', '2023-08-19', '2026-02'];
		const ys = dates.map((d) => yOfDate(d, stops));
		for (let i = 1; i < ys.length; i++) expect(ys[i]).toBeGreaterThan(ys[i - 1]);
	});

	it('clamps outside the axis rather than drawing off it', () => {
		expect(yOfDate('2009-05', stops)).toBe(stops[0].y);
		expect(yOfDate('2031-05', stops)).toBe(stops[stops.length - 1].y);
	});
});

describe('fractionalYear', () => {
	it('reads the three precisions the records carry', () => {
		expect(fractionalYear('2016')).toBe(2016);
		expect(fractionalYear('2016-07')).toBeCloseTo(2016.497, 3); // 2016 is a leap year
		expect(fractionalYear('2018-07-23')).toBeCloseTo(2018.556, 3);
	});

	it('counts days against the real length of the year', () => {
		// a leap year puts an extra day BEFORE July, so 1 July sits a shade
		// later in 2020 than in 2021 — the reason days are not divided by 365
		expect(fractionalYear('2020-07-01') - 2020).toBeGreaterThan(
			fractionalYear('2021-07-01') - 2021
		);
	});
});

describe('storyDate', () => {
	it('prints each precision the way the artboard does', () => {
		expect(storyDate('2018-07-23')).toBe('23-07-2018');
		expect(storyDate('2021-08')).toBe('08-2021');
		expect(storyDate('2016')).toBe('2016');
	});
});

describe('the lanes', () => {
	it('spread left to right in the artboard\'s order, around the collapsed line', () => {
		expect([...LANES]).toEqual(['world', 'greece', 'fire']);
		expect(LANE_X.world).toBeLessThan(LANE_X.greece);
		expect(LANE_X.greece).toBeLessThan(LANE_X.fire);
		// the collapsed line sits between them, as it does on the artboards
		expect(COLLAPSED_X).toBeGreaterThan(LANE_X.greece);
		expect(COLLAPSED_X).toBeLessThan(LANE_X.fire);
	});
});
