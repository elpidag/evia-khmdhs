import { describe, expect, it } from 'vitest';
import { binByKey, binCounts, binIndex, binPosition } from './histogram';

// the live ΔΑΣΕ edges: an unbounded catch-all, then pure doublings anchored
// on €1.000 and stretched to cover the data (queries_extra.dase_value_histogram)
const EDGES = [
	0, 31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000, 256000,
	512000
];

describe('binIndex', () => {
	it('is half-open: a value on an edge starts the next bin', () => {
		expect(binIndex(999.99, EDGES)).toBe(5);
		expect(binIndex(1000, EDGES)).toBe(6);
		expect(binIndex(1999.99, EDGES)).toBe(6);
		expect(binIndex(2000, EDGES)).toBe(7);
	});

	it('folds everything past the last edge into the final bin', () => {
		// matches _bin_values: the overflow bucket IS the last slot
		expect(binIndex(512_000, EDGES)).toBe(EDGES.length - 1);
		expect(binIndex(9_999_999, EDGES)).toBe(EDGES.length - 1);
	});

	it('places the smallest live contract in the first doubling, not the catch-all', () => {
		expect(binIndex(43.37, EDGES)).toBe(1);
	});
});

describe('binPosition', () => {
	const LEFT = 8;
	const BW = 54;

	it('puts an edge value exactly on its slot boundary', () => {
		expect(binPosition(1000, EDGES, LEFT, BW)).toBeCloseTo(LEFT + 6 * BW, 6);
		expect(binPosition(31.25, EDGES, LEFT, BW)).toBeCloseTo(LEFT + 1 * BW, 6);
	});

	it('is a plain log scale across the doublings — equal ratios, equal distances', () => {
		const step = (a: number, b: number) =>
			binPosition(b, EDGES, LEFT, BW) - binPosition(a, EDGES, LEFT, BW);
		// same ratio (×2) anywhere on the axis costs the same pixels…
		expect(step(1000, 2000)).toBeCloseTo(BW, 6);
		expect(step(3000, 6000)).toBeCloseTo(BW, 6);
		expect(step(90_000, 180_000)).toBeCloseTo(BW, 6);
		// …and it is monotonic
		expect(step(5000, 5001)).toBeGreaterThan(0);
	});

	it('interpolates inside a bracket, so the median lands off the boundary', () => {
		const x = binPosition(5792.13, EDGES, LEFT, BW);
		expect(x).toBeGreaterThan(LEFT + 8 * BW); // above 4k
		expect(x).toBeLessThan(LEFT + 9 * BW); // below 8k
	});

	it('clamps at or past the final edge instead of returning nothing', () => {
		expect(binPosition(1e9, EDGES, LEFT, BW)).toBeCloseTo(LEFT + (EDGES.length - 1) * BW, 6);
	});
});

describe('binCounts', () => {
	it('returns one slot per edge and counts every value once', () => {
		const vs = [500, 1500, 1500, 5000, 490_000];
		const counts = binCounts(vs, EDGES);
		expect(counts.length).toBe(EDGES.length);
		expect(counts.reduce((a, b) => a + b, 0)).toBe(vs.length);
		expect(counts[5]).toBe(1); // 500–1k
		expect(counts[6]).toBe(2); // 1k–2k
		expect(counts[8]).toBe(1); // 4k–8k
		expect(counts[14]).toBe(1); // 256k–512k
	});
});

describe('binByKey', () => {
	const vs = [500, 1500, 1500, 5000];
	const ys = ['2021', '2021', '2022', null];

	it('splits each bin into the requested key order', () => {
		const seg = binByKey(vs, ys, EDGES, ['2021', '2022']);
		expect(seg[5]).toEqual([1, 0]); // 500–1k
		expect(seg[6]).toEqual([1, 1]); // 1k–2k
	});

	it('drops values whose key is not in the order, never miscounts them', () => {
		const seg = binByKey(vs, ys, EDGES, ['2021', '2022']);
		// the null-year contract lands in the 4k–8k bin and in no segment
		expect(seg[8]).toEqual([0, 0]);
		const segTotal = seg.flat().reduce((a, b) => a + b, 0);
		expect(segTotal).toBe(3);
		expect(binCounts(vs, EDGES).reduce((a, b) => a + b, 0)).toBe(4);
	});

	it('segments sum to the bin totals when every key is covered', () => {
		const keys = ['2021', '2021', '2022', '2023'];
		const seg = binByKey(vs, keys, EDGES, ['2021', '2022', '2023']);
		const totals = binCounts(vs, EDGES);
		seg.forEach((row, i) => expect(row.reduce((a, b) => a + b, 0)).toBe(totals[i]));
	});
});
