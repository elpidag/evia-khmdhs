import { describe, expect, it } from 'vitest';
import { END_MS, START_MS } from './alerts';
import { dayStrip, dotRadius, placeLabels, type Box } from './alertsLayout';

describe('the day strip', () => {
	const strip = dayStrip(540);

	it('carries one tick per day of the window, left to right', () => {
		const days = Math.round((END_MS - START_MS) / 86_400_000);
		expect(strip.ticks.length).toBe(days);
		for (let i = 1; i < strip.ticks.length; i++) {
			expect(strip.ticks[i].x).toBeGreaterThan(strip.ticks[i - 1].x);
		}
		expect(strip.ticks[0].x).toBeCloseTo(strip.x0, 6);
		expect(strip.xOf(END_MS)).toBeCloseTo(strip.x1, 6);
	});

	it('labels the first day with its month and the tens bare', () => {
		const labels = strip.ticks.map((t) => t.label).filter(Boolean);
		expect(labels[0]).toMatch(/^1 [A-Z][a-z]{2}$/);
		expect(labels.slice(1).every((l) => /^\d0$/.test(l!))).toBe(true);
	});

	it('sits inside the square and scales with it', () => {
		expect(strip.band.y1).toBe(540);
		expect(strip.band.y0).toBeLessThan(strip.y);
		expect(strip.y).toBeLessThan(540);
		const big = dayStrip(1080);
		expect(big.band.y0).toBeCloseTo(strip.band.y0 * 2, 6);
		expect(big.x0).toBeCloseTo(strip.x0 * 2, 6);
	});
});

describe('the dots', () => {
	it('are larger while active than once past, and scale with the square', () => {
		expect(dotRadius('active', 540)).toBeGreaterThan(dotRadius('past', 540));
		expect(dotRadius('active', 1080)).toBeCloseTo(dotRadius('active', 540) * 2, 6);
	});
});

describe('label placement', () => {
	const item = (x: number, y: number, w = 40, h = 12, r = 3) => ({ x, y, w, h, r });
	const overlaps = (a: Box, b: Box) =>
		a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

	it('prefers the right side when it is free', () => {
		const [b] = placeLabels([item(100, 100)], { w: 540, h: 540 });
		expect(b).not.toBeNull();
		expect(b!.x).toBeGreaterThan(100);
		expect(b!.y + b!.h / 2).toBeCloseTo(100, 6);
	});

	it('never overlaps a placed label, an obstacle or the edge', () => {
		const items = [item(100, 100), item(104, 101), item(108, 99), item(100, 106), item(530, 100), item(100, 535)];
		const obstacles: Box[] = [{ x: 0, y: 0, w: 200, h: 40 }];
		const boxes = placeLabels(items, { w: 540, h: 540 }, obstacles);
		const kept = boxes.filter((b): b is Box => b !== null);
		expect(kept.length).toBeGreaterThan(0);
		for (const b of kept) {
			expect(b.x).toBeGreaterThanOrEqual(0);
			expect(b.y).toBeGreaterThanOrEqual(0);
			expect(b.x + b.w).toBeLessThanOrEqual(540);
			expect(b.y + b.h).toBeLessThanOrEqual(540);
			for (const o of obstacles) expect(overlaps(b, o)).toBe(false);
		}
		for (let i = 0; i < kept.length; i++) {
			for (let j = i + 1; j < kept.length; j++) expect(overlaps(kept[i], kept[j])).toBe(false);
		}
	});

	it('drops a label that fits nowhere rather than overlapping', () => {
		const wall: Box[] = [{ x: 0, y: 0, w: 540, h: 540 }];
		expect(placeLabels([item(100, 100)], { w: 540, h: 540 }, wall)).toEqual([null]);
	});

	it('is deterministic', () => {
		const items = [item(50, 50), item(53, 52), item(300, 300)];
		expect(placeLabels(items, { w: 540, h: 540 })).toEqual(placeLabels(items, { w: 540, h: 540 }));
	});
});
