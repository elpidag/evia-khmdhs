import { describe, expect, it } from 'vitest';
import { FIELD, glyphsAt, layoutColumns, poolFrom } from './field';
import type { Landing } from '$lib/api';

const payload: Landing = {
	antinero: {
		contracts: ['22SYMV000000001', '23SYMV000000002'],
		acts: ['22PROC000000003']
	},
	dase: { contracts: ['24SYMV000000004'], acts: [] },
	anadohoi: { acts: ['ΡΕΧΥ4653Π8-ΛΙΤ'] },
	counts: {
		antinero_contracts: 2,
		antinero_acts: 1,
		dase_contracts: 1,
		dase_acts: 0,
		anadohoi_acts: 1,
		total: 5
	}
};

describe('the field of codes', () => {
	it('pools every code once, tagged with its dataset, shuffled the same way for a seed', () => {
		const a = poolFrom(payload, 7);
		expect(a.length).toBe(5);
		expect(a.filter((c) => c.ds === 'antinero').length).toBe(3);
		expect(a.filter((c) => c.ds === 'dase').length).toBe(1);
		expect(a.find((c) => c.text === 'ΡΕΧΥ4653Π8-ΛΙΤ')?.ds).toBe('anadohoi');
		expect(poolFrom(payload, 7)).toEqual(a);
		expect(poolFrom(payload, 8).map((c) => c.text)).not.toEqual(a.map((c) => c.text));
	});

	it('fills the width with columns at the pitch, each stacked to at least twice the viewport', () => {
		const pool = poolFrom(payload, 1);
		// 87 columns across 1920 since the denser pitch of 2026-09-04 (the artboard's 74 at 25.7 px)
		expect(layoutColumns(1920, 1080, pool, 1).length).toBe(Math.floor(1920 / FIELD.colW));
		expect(layoutColumns(1920, 1080, pool, 1).length).toBe(87);
		expect(layoutColumns(1280, 800, pool, 1).length).toBe(Math.floor(1280 / FIELD.colW));
		expect(layoutColumns(100, 800, pool, 1).length).toBe(FIELD.minCols);
		for (const c of layoutColumns(1920, 1080, pool, 1)) {
			expect(c.lines * FIELD.lineH).toBeGreaterThanOrEqual(2 * 1080);
			expect(Math.abs(c.speed)).toBeGreaterThanOrEqual(8);
			expect(Math.abs(c.speed)).toBeLessThanOrEqual(30);
		}
	});

	it('is deterministic for a seed and drifts both ways', () => {
		const pool = poolFrom(payload, 1);
		expect(layoutColumns(1920, 1080, pool, 3)).toEqual(layoutColumns(1920, 1080, pool, 3));
		const speeds = layoutColumns(1920, 1080, pool, 3).map((c) => c.speed);
		expect(speeds.some((s) => s > 0) && speeds.some((s) => s < 0)).toBe(true);
	});

	it('draws only the glyphs in view and keeps their dataset', () => {
		const pool = poolFrom(payload, 1);
		const [col] = layoutColumns(320, 200, pool, 5);
		const g = glyphsAt(col, 0, 200);
		expect(g.length).toBeGreaterThan(0);
		expect(g.every((x) => x.y >= -FIELD.lineH && x.y <= 200)).toBe(true);
		expect(g.every((x) => ['antinero', 'dase', 'anadohoi'].includes(x.ds))).toBe(true);
		// a moment later the column has moved
		const h = glyphsAt(col, 5000, 200);
		expect(h.map((x) => x.y)).not.toEqual(g.map((x) => x.y));
	});
});

describe('the hole between a column’s repeats (the hub, 2026-09-25)', () => {
	const pool = poolFrom(payload, 7);
	const H = 600;
	const covered = (o: typeof FIELD, ms: number) => {
		const col = layoutColumns(220, H, pool, 7, o)[0];
		const ys = glyphsAt(col, ms, H, o).map((g) => g.y);
		// the longest stretch of the viewport with no glyph, in px
		const sorted = [...ys, -o.lineH, H].sort((a, b) => a - b);
		let gap = 0;
		for (let i = 1; i < sorted.length; i++) gap = Math.max(gap, sorted[i] - sorted[i - 1]);
		return gap;
	};
	it('without it a column may run empty for most of the viewport', () => {
		let worst = 0;
		for (let ms = 0; ms < 200000; ms += 997) worst = Math.max(worst, covered(FIELD, ms));
		expect(worst).toBeGreaterThan(H / 2);
	});
	it('with a quarter-height hole the blank never exceeds the band', () => {
		const o = { ...FIELD, hole: 0.25 };
		let worst = 0;
		for (let ms = 0; ms < 200000; ms += 997) worst = Math.max(worst, covered(o, ms));
		expect(worst).toBeLessThanOrEqual(0.25 * H + 2 * FIELD.lineH);
		expect(worst).toBeGreaterThan(2 * FIELD.lineH);
	});
});
