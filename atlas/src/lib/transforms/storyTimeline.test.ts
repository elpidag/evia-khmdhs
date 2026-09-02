import { describe, expect, it } from 'vitest';
import {
	AXIS_TOP,
	BODY_CLAMP,
	COLLAPSED_X,
	LANES,
	LANE_TEXT,
	LANE_X,
	TITLE_CLAMP,
	YEAR_W,
	axisHeight,
	blockHeight,
	contentHeight,
	fractionalYear,
	layoutLane,
	storyDate,
	storyRange,
	yOfDate,
	yearStops
} from './storyTimeline';
import { EVENTS, laneEvents } from '$lib/story/events';

describe("the story timeline's year scale", () => {
	const stops = yearStops();

	it('runs from the first event through 2026, top to bottom', () => {
		expect(stops[0]).toMatchObject({ year: 2007, y: AXIS_TOP, labelled: true });
		// 2027 is only the endpoint that makes 2026 a real year, never printed
		expect(stops[stops.length - 1]).toMatchObject({ year: 2027, labelled: false });
		expect(stops.filter((s) => s.labelled).at(-1)!.year).toBe(2026);
		for (let i = 1; i < stops.length; i++) {
			expect(stops[i].year).toBeGreaterThan(stops[i - 1].year);
			expect(stops[i].y).toBeGreaterThan(stops[i - 1].y);
		}
	});

	it('holds every event the author gave us', () => {
		const first = stops[0].year;
		const last = stops[stops.length - 1].year;
		for (const e of EVENTS) {
			const y = Number(e.date.slice(0, 4));
			expect(y).toBeGreaterThanOrEqual(first);
			expect(y).toBeLessThanOrEqual(last);
		}
	});

	it('compresses the prehistory and marks it as a break', () => {
		const gapped = stops.filter((s) => s.gap > 1);
		expect(gapped.map((s) => s.year)).toEqual([2007, 2010]);
		// nine years drawn in the space of two — so the axis must say so
		const pitch = (a: number, b: number) => stops[b].y - stops[a].y;
		expect(pitch(0, 1) / 3).toBeLessThan(pitch(4, 5)); // 2007→2010 vs a plain year
	});

	it('gives 2021 the room its twelve events need', () => {
		const y = (year: number) => stops.find((s) => s.year === year)!.y;
		const plain = y(2020) - y(2019);
		expect(y(2022) - y(2021)).toBeGreaterThan(plain * 2.5);
	});

	it('centres each year label on its span, level with its events', () => {
		for (let i = 0; i < stops.length - 1; i++) {
			expect(stops[i].midY).toBeCloseTo((stops[i].y + stops[i + 1].y) / 2, 6);
		}
		expect(stops[stops.length - 1].midY).toBe(stops[stops.length - 1].y);
	});

	it('spaces 2017 but does not name it, as the artboard does', () => {
		const y2017 = stops.find((s) => s.year === 2017)!;
		expect(y2017.labelled).toBe(false);
		// 2017 and the 2027 endpoint are the only unnamed stops
		expect(stops.filter((s) => !s.labelled)).toHaveLength(2);
	});

	it("gives every year the room its own events' blocks need", () => {
		// the correspondence guarantee: a year's span can hold each lane's
		// closed stack, so the chain never has to smear past the labels
		for (let i = 0; i < stops.length - 1; i++) {
			const span = stops[i + 1].y - stops[i].y;
			for (const lane of LANES) {
				const stack = laneEvents(lane)
					.filter((e) => {
						const t = fractionalYear(e.date);
						return t >= stops[i].year && t < stops[i + 1].year;
					})
					.reduce((s, e) => s + blockHeight({ title: e.title }, LANE_TEXT[lane].w) + 12, 0);
				expect(span, `${lane} in ${stops[i].year}`).toBeGreaterThanOrEqual(stack);
			}
		}
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
		expect(y).toBeCloseTo(yr(2018) + 0.556 * (yr(2019) - yr(2018)), 1);
	});

	it('interpolates inside a compressed span, not per year', () => {
		// 2013 sits halfway through the single 2010→2016 step
		const y = yOfDate('2013-01-01', stops);
		expect(y).toBeCloseTo(yr(2010) + 0.5 * (yr(2016) - yr(2010)), 0);
	});

	it('is monotonic across the whole story', () => {
		const ys = EVENTS.map((e) => yOfDate(e.date, stops));
		for (let i = 1; i < ys.length; i++) expect(ys[i]).toBeGreaterThanOrEqual(ys[i - 1]);
	});

	it('clamps outside the axis rather than drawing off it', () => {
		expect(yOfDate('2001-05', stops)).toBe(stops[0].y);
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

	it('writes a period once, the year carried by its end', () => {
		expect(storyRange('2021-08-03', '2021-08-11')).toBe('03-08 → 11-08-2021');
		expect(storyRange('2023-08-19', '2023-09-04')).toBe('19-08 → 04-09-2023');
	});
});

describe('the lanes', () => {
	it("spread left to right in the artboard's order, around the collapsed line", () => {
		expect([...LANES]).toEqual(['world', 'greece', 'fire']);
		expect(LANE_X.world).toBeLessThan(LANE_X.greece);
		expect(LANE_X.greece).toBeLessThan(LANE_X.fire);
		expect(COLLAPSED_X).toBeGreaterThan(LANE_X.greece);
		expect(COLLAPSED_X).toBeLessThan(LANE_X.fire);
	});

	it('keeps every text column out of the gutter the years move into', () => {
		for (const lane of LANES) expect(LANE_TEXT[lane].x).toBeGreaterThanOrEqual(YEAR_W);
	});

	it('gives every lane a text column that clears its neighbours', () => {
		for (const lane of LANES) {
			const t = LANE_TEXT[lane];
			expect(t.w).toBeGreaterThan(100); // narrower than this and a title cannot set
			const right = t.x + t.w;
			// the column may not cross ANOTHER lane's rule
			for (const other of LANES) {
				if (other === lane) continue;
				const x = LANE_X[other];
				expect(t.x >= x || right <= x).toBe(true);
			}
		}
	});
});

describe('block layout', () => {
	const stops = yearStops();

	it('clamps a very long title instead of growing without limit', () => {
		const short = blockHeight({ title: 'Fires in Rhodes' }, 132);
		const long = blockHeight({ title: 'x'.repeat(2000) }, 132);
		expect(long).toBeGreaterThan(short);
		expect(long).toBeLessThan(short + (TITLE_CLAMP + BODY_CLAMP) * 20);
	});

	it('keeps every dot on its true date and never overlaps two blocks', () => {
		for (const lane of LANES) {
			const placed = layoutLane(laneEvents(lane), stops, LANE_TEXT[lane].w);
			for (const p of placed) expect(p.dotY).toBeCloseTo(yOfDate(p.e.date, stops), 6);
			for (let i = 1; i < placed.length; i++) {
				expect(placed[i].blockY).toBeGreaterThanOrEqual(placed[i - 1].blockY + placed[i - 1].h);
			}
		}
	});

	it('pushes the August 2021 cluster apart and says it did', () => {
		const placed = layoutLane(laneEvents('greece'), stops, LANE_TEXT.greece.w);
		const aug = placed.filter((p) => p.e.date.startsWith('2021-08'));
		expect(aug.length).toBeGreaterThanOrEqual(3);
		// their dots are within a fortnight of each other …
		expect(aug[aug.length - 1].dotY - aug[0].dotY).toBeLessThan(20);
		// … so all but the first had to be moved, and carry a leader line
		expect(aug.slice(1).every((p) => p.pushed)).toBe(true);
	});

	it('shrinks a closed event to date + title, and STRETCHES an open one whole', () => {
		const openAll = layoutLane(laneEvents('greece'), stops, LANE_TEXT.greece.w);
		const closed = layoutLane(laneEvents('greece'), stops, LANE_TEXT.greece.w, () => false);
		const withBody = laneEvents('greece').filter((e) => e.body);
		expect(withBody.length).toBeGreaterThan(5);
		for (let i = 0; i < openAll.length; i++) {
			expect(closed[i].h).toBeLessThanOrEqual(openAll[i].h);
			expect(closed[i].h).toBe(blockHeight({ title: closed[i].e.title }, LANE_TEXT.greece.w));
			// open = unclamped: a long body never truncates, the block grows
			expect(openAll[i].h).toBe(blockHeight(openAll[i].e, LANE_TEXT.greece.w, true));
		}
	});

	it('balances every crowd around its own dates, so lanes track the years', () => {
		for (const lane of LANES) {
			const placed = layoutLane(laneEvents(lane), stops, LANE_TEXT[lane].w, () => false);
			// least-squares balance: the displacements cancel out overall …
			const drift =
				placed.reduce((s, p) => s + (p.blockY - (p.dotY - 4)), 0) / (placed.length || 1);
			expect(Math.abs(drift), lane).toBeLessThan(25);
			// … and no block strays into the legend's line
			for (const p of placed) expect(p.blockY).toBeGreaterThanOrEqual(62);
		}
	});

	it('reports a drawing taller than the viewport, so the rail must pan', () => {
		// the runtime shape: everything closed but the reader's own events
		const placed = LANES.map((l) => layoutLane(laneEvents(l), stops, LANE_TEXT[l].w, () => false));
		const h = contentHeight(placed, stops);
		expect(h).toBeGreaterThanOrEqual(axisHeight(stops));
		expect(h).toBeLessThan(2000); // and not so tall the pan becomes a second scroll
	});
});
