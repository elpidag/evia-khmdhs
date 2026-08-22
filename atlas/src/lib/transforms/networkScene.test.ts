import { describe, expect, it } from 'vitest';
import { type NetMode, bridgeSegments, scene, type BandCopy } from './networkScene';
import type { NetNode, Placed } from './network';

const copy: BandCopy = {
	single: '2 calls produced exactly one contract',
	none: '1 contract has no call at all',
	eurShort: (v) => `${v} €`,
	eurTiny: (v) => `${v}`
};

const nodes: NetNode[] = [
	{ ref: 'A', eur: 100, call: 'C1', vat: 'V1', d: '2022-01-01' },
	{ ref: 'B', eur: 50, call: 'C1', vat: 'V2', d: '2022-01-01' },
	{ ref: 'C', eur: 80, call: 'C2', vat: 'V1', d: '2023-05-05' },
	{ ref: 'D', eur: 40, call: 'C2', vat: 'V3', d: '2023-06-06' },
	{ ref: 'S', eur: 30, call: 'C3', d: '2024-01-01' },
	{ ref: 'T', eur: 20, call: 'C4', d: '2024-02-02' },
	{ ref: 'Z', eur: 10, d: '2025-03-03' }
];
const P = (ref: string, x: number, y: number): Placed => ({
	ref,
	eur: 1,
	x,
	y,
	r: 4,
	group: 0,
	hub: true
});

// NET_MODES became the COLOUR lenses (2026-08-22); the arrangements are
// the scenes themselves — the parked «pack» stays tested so it can return
const ARRANGEMENTS: NetMode[] = ['time', 'pack'];

describe('scene', () => {
	it('draws every contract exactly once in every arrangement', () => {
		for (const m of ARRANGEMENTS.map((value) => ({ value }))) {
			const sc = scene(m.value, nodes, 1000, copy);
			expect(sc.marks.map((n) => n.ref).sort(), m.value).toEqual([
				'A',
				'B',
				'C',
				'D',
				'S',
				'T',
				'Z'
			]);
		}
	});

	it('is deterministic per mode — the same data draws the same scene', () => {
		for (const m of ARRANGEMENTS.map((value) => ({ value })))
			expect(JSON.stringify(scene(m.value, nodes, 1000, copy))).toBe(
				JSON.stringify(scene(m.value, nodes, 1000, copy))
			);
	});

	it('time: ties the split calls, rules the years, and never draws spokes', () => {
		const sc = scene('time', nodes, 1000, copy);
		expect(sc.ties.map((t) => t.call)).toEqual(['C1', 'C2']);
		expect(sc.rules.map((r) => r.key)).toEqual(['2022', '2023', '2024', '2025']);
		expect(sc.spokes).toEqual([]);
		expect(sc.groups).toEqual([]);
	});

	it('call: the two band headings are printed on the chart', () => {
		const sc = scene('call', nodes, 1000, copy);
		const bands = sc.labels.filter((l) => l.cls === 'band').map((l) => l.text);
		expect(bands).toEqual([copy.single, copy.none]);
		expect(sc.spokes.length).toBe(2); // one per sibling, in two calls
	});

	it('pack: a bubble per split call, bare circles for the rest, cropped to the blob', () => {
		const sc = scene('pack', nodes, 1000, copy, 400);
		expect(sc.groups.map((g) => g.key)).toEqual(['C1', 'C2']);
		expect(sc.marks.filter((m) => m.group < 0).map((m) => m.ref).sort()).toEqual(['S', 'T', 'Z']);
		const [x, y, w, h] = sc.view.split(' ').map(Number);
		for (const g of [...sc.groups, ...sc.marks.filter((m) => m.group < 0)]) {
			expect(g.x - g.r).toBeGreaterThanOrEqual(x);
			expect(g.y - g.r).toBeGreaterThanOrEqual(y);
			expect(g.x + g.r).toBeLessThanOrEqual(x + w);
			expect(g.y + g.r).toBeLessThanOrEqual(y + h);
		}
		expect(sc.maxW).toBeGreaterThan(0); // the blob is round: cap its width
	});

	it('pack: a call is named on the arc of its own bubble, never outside it', () => {
		const sc = scene('pack', nodes, 1000, copy, 400);
		for (const a of sc.arcs) {
			const g = sc.groups.find((k) => k.key === a.key);
			expect(g, a.key).toBeTruthy();
			expect(a.text).toBe(g?.key);
			// the arc radius must sit inside the bubble it labels
			const rr = Number(a.d.split('A')[1].split(' ')[0]);
			expect(rr).toBeLessThan(g?.r as number);
		}
	});

	it('pack: a bubble too small for its ΑΔΑΜ goes unnamed rather than smudged', () => {
		const tiny = scene('pack', nodes, 1000, copy, 40);
		expect(tiny.arcs).toEqual([]);
	});
});

describe('bridgeSegments', () => {
	const at = new Map([
		['A', P('A', 0, 10)],
		['B', P('B', 100, 10)],
		['C', P('C', 200, 10)]
	]);

	it('draws one line per PAIR of calls, however many contractors bridge them', () => {
		const segs = bridgeSegments(
			[
				{ a: 'A', b: 'B', vat: 'V1', who: 'ΑΛΦΑ' },
				{ a: 'A', b: 'B', vat: 'V2', who: 'ΒΗΤΑ' }
			],
			at
		);
		expect(segs).toHaveLength(1);
		expect(segs[0].vats).toEqual(['V1', 'V2']);
		expect(segs[0].who).toEqual(['ΑΛΦΑ', 'ΒΗΤΑ']);
	});

	it('lifts a bridge clear of one already drawn over the same stretch', () => {
		const segs = bridgeSegments(
			[
				{ a: 'A', b: 'C', vat: 'V1' }, // 0 → 200
				{ a: 'B', b: 'C', vat: 'V2' } // 100 → 200, overlaps
			],
			at
		);
		expect(segs[0].y1).toBe(10);
		expect(segs[1].y1).toBe(6.5); // lifted, or the two read as one solid rule
	});

	it('leaves non-overlapping bridges on the line they belong to', () => {
		const segs = bridgeSegments(
			[
				{ a: 'A', b: 'B', vat: 'V1' },
				{ a: 'B', b: 'C', vat: 'V2' } // end to end, not overlapping
			],
			at
		);
		expect(segs.map((s) => s.y1)).toEqual([10, 10]);
	});

	it('skips a bridge whose endpoint is not on the field', () => {
		expect(bridgeSegments([{ a: 'A', b: 'MISSING', vat: 'V1' }], at)).toEqual([]);
	});
});
