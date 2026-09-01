import { describe, expect, it } from 'vitest';
import { ALERTS, END_MS, START_MS } from './alerts';
import { CLOCK, buildClock, burnDayIndex, loopPhase } from './alertsClock';

const DAY = 86_400_000;
const HOUR = 3_600_000;

describe('the alerts clock on the real data', () => {
	const c = buildClock(ALERTS, CLOCK, START_MS, END_MS);

	it('runs one loop of 55–70 s over the whole window', () => {
		expect(c.start).toBe(START_MS);
		expect(c.end).toBe(END_MS);
		expect(c.loopMs).toBeGreaterThanOrEqual(55_000);
		expect(c.loopMs).toBeLessThanOrEqual(70_000);
		expect(c.loopMs).toBe(c.endWall + CLOCK.holdMs + CLOCK.tailFadeMs);
	});

	it('maps wall time onto simulated time monotonically, end to end', () => {
		expect(c.simAt(0)).toBe(START_MS);
		expect(c.simAt(c.endWall)).toBe(END_MS);
		let prev = -Infinity;
		for (let w = 0; w <= c.endWall; w += 37) {
			const s = c.simAt(w);
			expect(s).toBeGreaterThanOrEqual(prev);
			prev = s;
		}
		for (const seg of c.segments) {
			expect(seg.rate).toBeGreaterThanOrEqual(0);
			expect(seg.rate).toBeLessThanOrEqual(DAY / CLOCK.fastMsPerDay + 1e-9);
		}
	});

	it('fires every alert exactly once, in order, at its own minute, never closer than the minimum gap', () => {
		expect(c.fireWall.length).toBe(ALERTS.length);
		for (let i = 0; i < ALERTS.length; i++) {
			expect(c.fireWall[i]).toBeGreaterThanOrEqual(0);
			expect(c.fireWall[i]).toBeLessThan(c.endWall);
			expect(c.simAt(c.fireWall[i])).toBeCloseTo(Date.parse(ALERTS[i].timestamp), 0);
			if (i) expect(c.fireWall[i] - c.fireWall[i - 1]).toBeGreaterThanOrEqual(CLOCK.minGapMs - 1e-6);
		}
	});

	it('accelerates only through idle stretches', () => {
		const times = ALERTS.map((a) => Date.parse(a.timestamp));
		const fast = DAY / CLOCK.fastMsPerDay;
		for (const seg of c.segments) {
			if (Math.abs(seg.rate - fast) > 1e-9) continue;
			// the next alert is farther than the look-ahead from every point of the segment
			const next = times.find((t) => t > seg.sim0 + 1e-6);
			if (next !== undefined) {
				expect(next - seg.sim0).toBeGreaterThan(CLOCK.lookaheadH * HOUR - 1e-6);
			}
			// and no alert is still dwelling when it starts
			for (let i = 0; i < c.fireWall.length; i++) {
				if (c.fireWall[i] <= seg.wall0) {
					expect(seg.wall0).toBeGreaterThanOrEqual(c.fireWall[i] + CLOCK.dwellMs - 1e-6);
				}
			}
		}
	});

	it('gives each alert its dwell, its fade, then a permanent past', () => {
		for (let i = 0; i < ALERTS.length; i++) {
			const f = c.fireWall[i];
			expect(c.phaseAt(f - 1, i).kind).toBe('none');
			expect(c.phaseAt(f, i).kind).toBe('active');
			expect(c.phaseAt(f + CLOCK.dwellMs - 1, i).kind).toBe('active');
			expect(c.phaseAt(f + CLOCK.dwellMs, i).kind).toBe('fading');
			expect(c.phaseAt(f + CLOCK.dwellMs + CLOCK.fadeMs, i).kind).toBe('past');
			expect(c.phaseAt(c.endWall, i).kind).toBe('past'); // the window settles after the last alert
		}
	});

	it('holds the final state, fades, and wraps', () => {
		expect(loopPhase(c.endWall + 1, c)).toEqual({ wall: c.endWall, tail: 0 });
		expect(loopPhase(c.endWall + CLOCK.holdMs + CLOCK.tailFadeMs / 2, c).tail).toBeCloseTo(0.5, 6);
		expect(loopPhase(c.loopMs + 10, c).wall).toBe(10);
		// a negative clock lands in the tail of the previous loop
		expect(loopPhase(-10, c).tail).toBeCloseTo(1 - 10 / CLOCK.tailFadeMs, 6);
	});

	it('indexes the burn days monotonically', () => {
		const days = Array.from({ length: 23 }, (_, i) => `2021-08-${String(i + 1).padStart(2, '0')}`);
		expect(burnDayIndex(START_MS - 1, days)).toBe(-1);
		expect(burnDayIndex(START_MS, days)).toBe(0);
		expect(burnDayIndex(Date.parse('2021-08-06T12:00:00+03:00'), days)).toBe(5);
		expect(burnDayIndex(END_MS, days)).toBe(22);
		let prev = -1;
		for (let w = 0; w <= c.endWall; w += 101) {
			const i = burnDayIndex(c.simAt(w), days);
			expect(i).toBeGreaterThanOrEqual(prev);
			prev = i;
		}
	});
});

describe('the clock on synthetic alerts', () => {
	it('holds the clock between two alerts a minute apart', () => {
		const c = buildClock(
			[{ timestamp: '2021-08-05T10:00:00+03:00' }, { timestamp: '2021-08-05T10:01:00+03:00' }],
			CLOCK,
			Date.parse('2021-08-05T00:00:00+03:00'),
			Date.parse('2021-08-06T00:00:00+03:00')
		);
		expect(c.fireWall[1] - c.fireWall[0]).toBeCloseTo(CLOCK.minGapMs, 6);
		expect(c.segments.some((s) => s.rate === 0)).toBe(true);
	});

	it('refuses unsorted alerts', () => {
		expect(() =>
			buildClock([{ timestamp: '2021-08-05T10:01:00+03:00' }, { timestamp: '2021-08-05T10:00:00+03:00' }])
		).toThrow();
	});
});
