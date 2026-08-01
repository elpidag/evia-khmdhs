import { describe, expect, it } from 'vitest';
import { dodge } from './beeswarm';

describe('dodge', () => {
	it('keeps separated points on the centreline', () => {
		expect(dodge([0, 100, 200], 4)).toEqual([0, 0, 0]);
	});

	it('never overlaps co-located points', () => {
		const xs = [50, 50, 50, 50, 51, 51, 52, 52, 52, 53];
		const r = 4;
		const ys = dodge(xs, r);
		for (let i = 0; i < xs.length; i++) {
			for (let j = i + 1; j < xs.length; j++) {
				const d = Math.hypot(xs[i] - xs[j], ys[i] - ys[j]);
				expect(d).toBeGreaterThanOrEqual(2 * r - 1e-6);
			}
		}
	});

	it('is deterministic', () => {
		const xs = Array.from({ length: 200 }, (_, i) => (i * 37) % 100);
		expect(dodge(xs, 3)).toEqual(dodge(xs, 3));
	});
});
