import { describe, expect, it } from 'vitest';
import { band, componentsOf, edgesOf, layout, packed, timeline, type NetNode } from './network';

const N = (ref: string, eur: number, call?: string, vat?: string): NetNode => ({
	ref,
	eur,
	call,
	vat
});

describe('edgesOf', () => {
	it('links contracts sharing a call and contracts sharing a contractor', () => {
		const e = edgesOf([N('A', 1, 'C1', 'V1'), N('B', 1, 'C1', 'V2'), N('D', 1, 'C2', 'V1')]);
		expect(e).toContainEqual({ a: 'A', b: 'B', kind: 'call' });
		expect(e).toContainEqual({ a: 'A', b: 'D', kind: 'contractor' });
	});

	it('never links on a missing key — a null call is not a group', () => {
		expect(edgesOf([N('A', 1), N('B', 1)])).toEqual([]);
	});

	it('keeps a group linear (a star, not a clique) so 245 nodes stay drawable', () => {
		const many = Array.from({ length: 8 }, (_, i) => N(`R${i}`, 1, 'C1'));
		expect(edgesOf(many).length).toBe(7); // n-1, not n(n-1)/2 = 28
	});
});

describe('componentsOf', () => {
	it('merges clusters bridged by a shared contractor', () => {
		const nodes = [N('A', 1, 'C1', 'V1'), N('B', 1, 'C1'), N('D', 1, 'C2', 'V1')];
		const c = componentsOf(nodes, edgesOf(nodes));
		expect(c.get('A')).toBe(c.get('B'));
		expect(c.get('A')).toBe(c.get('D')); // the bridge — the point of the view
	});

	it('leaves an unrelated contract in its own component', () => {
		const nodes = [N('A', 1, 'C1'), N('B', 1, 'C1'), N('Z', 1)];
		const c = componentsOf(nodes, edgesOf(nodes));
		expect(c.get('Z')).not.toBe(c.get('A'));
	});
});

describe('layout', () => {
	const nodes = [
		N('A', 100, 'C1'),
		N('B', 50, 'C1'),
		N('C', 25, 'C1'),
		N('D', 80, 'C2'),
		N('E', 10, 'C2'),
		N('S', 40, 'C3'), // its call produced nothing else
		N('Z', 5) // direct award, no call at all
	];

	it('is deterministic — the same input always draws the same field', () => {
		expect(JSON.stringify(layout(nodes))).toBe(JSON.stringify(layout(nodes)));
	});

	it('does not depend on the input order', () => {
		const pos = (ns: NetNode[]) =>
			new Map(layout(ns).nodes.map((n) => [n.ref, `${Math.round(n.x)},${Math.round(n.y)}`]));
		expect(pos(nodes)).toEqual(pos([...nodes].reverse()));
	});

	it('draws only the calls that produced lots, and hands the rest back as lone', () => {
		const f = layout(nodes);
		expect(f.nodes.map((n) => n.ref).sort()).toEqual(['A', 'B', 'C', 'D', 'E']);
		expect(f.lone.map((n) => n.ref)).toEqual(['S', 'Z']); // € desc
		expect(f.clusters.map((c) => c.call)).toEqual(['C1', 'C2']);
	});

	it('area encodes €: four times the money is twice the radius', () => {
		const f = layout(nodes);
		const r = (ref: string) => f.nodes.find((n) => n.ref === ref)!.r;
		expect(r('A') / r('C')).toBeCloseTo(2, 1);
	});

	it('puts the biggest contract of a call at the centre of its star', () => {
		const f = layout(nodes);
		const head = f.nodes.find((n) => n.ref === 'A')!;
		expect(head.hub).toBe(true);
		for (const o of f.nodes.filter((n) => n.group === head.group && n.ref !== 'A')) {
			expect(Math.hypot(o.x - head.x, o.y - head.y)).toBeGreaterThan(head.r);
			expect(o.hub).toBe(false);
		}
	});

	it('spokes run from the hub to every sibling, one each', () => {
		const f = layout(nodes);
		expect(f.spokes).toEqual([
			{ a: 'A', b: 'B' },
			{ a: 'A', b: 'C' },
			{ a: 'D', b: 'E' }
		]);
	});

	it('bridges only when one contractor holds lots under two drawn calls', () => {
		const one = layout([N('A', 9, 'C1', 'V1'), N('B', 8, 'C1', 'V1')]);
		expect(one.bridges).toEqual([]); // same call — that is a spoke, not a bridge
		const two = layout([
			N('A', 9, 'C1', 'V1'),
			N('B', 8, 'C1', 'V2'),
			N('D', 7, 'C2', 'V1'),
			N('E', 6, 'C2', 'V3')
		]);
		expect(two.bridges).toEqual([{ a: 'A', b: 'D', vat: 'V1', who: undefined }]);
	});

	it('keeps a bridged pair of calls side by side', () => {
		const f = layout([
			N('A', 9, 'C1', 'V1'),
			N('B', 8, 'C1'),
			N('X', 99, 'C9'), // a richer, unrelated call
			N('Y', 98, 'C9'),
			N('D', 7, 'C2', 'V1'),
			N('E', 6, 'C2')
		]);
		const seat = f.clusters.map((c) => c.call);
		expect(Math.abs(seat.indexOf('C1') - seat.indexOf('C2'))).toBe(1);
	});
});

describe('band', () => {
	const lone = [N('A', 100), N('B', 400), N('C', 25)];

	it('ranks by € and wraps into rows', () => {
		const b = band(lone, 100, 2, 20);
		expect(b.nodes.map((n) => n.ref)).toEqual(['B', 'A', 'C']);
		expect(b.height).toBe(40); // 3 nodes, 2 per row
		expect(b.nodes[2].y).toBeGreaterThan(b.nodes[0].y);
	});

	it('shares the field scale when the field maximum is passed in', () => {
		const b = band(lone, 100, 2, 20, 15, 400);
		const r = (ref: string) => b.nodes.find((n) => n.ref === ref)!.r;
		expect(r('B') / r('A')).toBeCloseTo(2, 1);
	});
});

describe('timeline', () => {
	const nodes: NetNode[] = [
		{ ref: 'A', eur: 100, call: 'C1', d: '2022-01-01' },
		{ ref: 'B', eur: 25, call: 'C1', d: '2022-01-01' },
		{ ref: 'C', eur: 50, call: 'C2', d: '2024-06-30' },
		{ ref: 'Z', eur: 10, d: '2026-01-01' }
	];

	it('places x by signature date, spanning the frame', () => {
		const f = timeline(nodes, 1000);
		const x = (r: string) => f.nodes.find((n) => n.ref === r)!.x;
		expect(x('A')).toBe(f.x0);
		expect(x('Z')).toBe(f.x1);
		expect(x('C')).toBeGreaterThan(x('A'));
		expect(x('C')).toBeLessThan(x('Z'));
	});

	it('dodges same-day contracts apart instead of overplotting them', () => {
		const f = timeline(nodes, 1000);
		const a = f.nodes.find((n) => n.ref === 'A')!;
		const b = f.nodes.find((n) => n.ref === 'B')!;
		expect(Math.hypot(a.x - b.x, a.y - b.y)).toBeGreaterThanOrEqual(a.r + b.r);
	});

	it('ties only the calls that produced lots', () => {
		const f = timeline(nodes, 1000);
		expect(f.ties.map((t) => t.call)).toEqual(['C1']);
		expect(f.ties[0].pts).toHaveLength(2);
	});

	it('rules every 1 January and labels sit ON the rule', () => {
		const t = timeline(nodes, 1000).ticks;
		expect(t.map((k) => k.label)).toEqual(['2022', '2023', '2024', '2025', '2026']);
		expect(t.every((k) => k.rule)).toBe(true);
		// a mid-year start still rules its year: the axis starts on 1 Jan
		// of the first year by construction (user, 2026-08-22)
		const mid = timeline(
			nodes.map((n) => (n.ref === 'A' || n.ref === 'B' ? { ...n, d: '2022-04-13' } : n)),
			1000
		);
		expect(mid.ticks[0].label).toBe('2022');
		expect(mid.ticks[0].rule).toBe(true);
		expect(mid.ticks[0].x).toBe(mid.x0);
	});

	it('keeps same-day lots of one call adjacent — one touching vertical run', () => {
		// five lots of one call signed on one day, among same-day strangers
		const busy: NetNode[] = [
			...['L1', 'L2', 'L3', 'L4', 'L5'].map((r, i) =>
				({ ref: r, eur: 40 - i * 5, call: 'C9', d: '2024-06-30' }) as NetNode
			),
			{ ref: 'S1', eur: 60, d: '2024-06-30' },
			{ ref: 'S2', eur: 30, d: '2024-06-30' },
			{ ref: 'A', eur: 100, d: '2022-01-01' },
			{ ref: 'Z', eur: 10, d: '2026-01-01' }
		];
		const f = timeline(busy, 1000);
		const run = f.nodes.filter((n) => n.call === 'C9').sort((a, b) => a.y - b.y);
		expect(new Set(run.map((n) => n.x)).size).toBe(1);
		for (let i = 1; i < run.length; i++)
			expect(run[i].y - run[i - 1].y).toBeCloseTo(run[i].r + run[i - 1].r, 3);
		// and no stranger overlaps the run
		for (const s of f.nodes.filter((n) => n.ref.startsWith('S')))
			for (const m of run)
				expect(Math.hypot(s.x - m.x, s.y - m.y)).toBeGreaterThanOrEqual(s.r + m.r - 1e-6);
	});

	it('absorbs a day-apart lot into the run, touching on a slant', () => {
		// 23PROC012860295 signed four lots on 07.07.2023 and ONE on 06.07 —
		// the sub-pixel day must not exile it (user, 2026-08-22)
		const busy: NetNode[] = [
			{ ref: 'L1', eur: 40, call: 'C9', d: '2024-06-30' },
			{ ref: 'L2', eur: 30, call: 'C9', d: '2024-06-30' },
			{ ref: 'E', eur: 35, call: 'C9', d: '2024-06-29' },
			{ ref: 'A', eur: 100, d: '2024-01-01' },
			{ ref: 'Z', eur: 10, d: '2024-12-31' }
		];
		const f = timeline(busy, 1000);
		const run = f.nodes.filter((n) => n.call === 'C9').sort((a, b) => a.y - b.y);
		// every consecutive pair of the run TOUCHES (distance == r sum)
		for (let i = 1; i < run.length; i++)
			expect(Math.hypot(run[i].x - run[i - 1].x, run[i].y - run[i - 1].y)).toBeCloseTo(
				run[i].r + run[i - 1].r,
				3
			);
		// the early lot keeps its own date on the axis
		const e = f.nodes.find((n) => n.ref === 'E')!;
		const l = f.nodes.find((n) => n.ref === 'L1')!;
		expect(e.x).toBeLessThan(l.x);
	});

	it('is deterministic and order-independent', () => {
		const pos = (ns: NetNode[]) =>
			new Map(timeline(ns, 1000).nodes.map((n) => [n.ref, `${n.x.toFixed(2)},${n.y.toFixed(2)}`]));
		expect(pos(nodes)).toEqual(pos([...nodes].reverse()));
	});

	it('keeps area ∝ € — four times the money is twice the radius', () => {
		const f = timeline(nodes, 1000);
		const r = (ref: string) => f.nodes.find((n) => n.ref === ref)!.r;
		expect(r('A') / r('B')).toBeCloseTo(2, 1);
	});
});

describe('packed', () => {
	const nodes: NetNode[] = [
		{ ref: 'A', eur: 100, call: 'C1' },
		{ ref: 'B', eur: 50, call: 'C1' },
		{ ref: 'C', eur: 40, call: 'C2' }, // its call produced nothing else
		{ ref: 'Z', eur: 10 } // no call
	];

	it('bubbles only the calls that produced lots; the rest are bare circles', () => {
		const f = packed(nodes, 400, 400);
		expect(f.nodes.map((n) => n.ref).sort()).toEqual(['A', 'B', 'C', 'Z']);
		expect(f.groups.map((g) => g.key)).toEqual(['C1']);
		expect(f.groups[0].n).toBe(2);
		expect(f.nodes.filter((n) => n.group < 0).map((n) => n.ref).sort()).toEqual(['C', 'Z']);
	});

	it('a bubble contains its lots', () => {
		const f = packed(nodes, 400, 400);
		for (const n of f.nodes.filter((m) => m.group >= 0)) {
			const g = f.groups[n.group];
			expect(Math.hypot(n.x - g.x, n.y - g.y) + n.r).toBeLessThanOrEqual(g.r + 1e-6);
		}
	});

	it('keeps the grouped procurements in the middle and the lone ones outside', () => {
		// the point of the arrangement: position means «bought together»
		const many: NetNode[] = [
			...Array.from({ length: 6 }, (_, i) => [
				{ ref: `G${i}a`, eur: 40 + i, call: `K${i}` },
				{ ref: `G${i}b`, eur: 30 + i, call: `K${i}` }
			]).flat(),
			...Array.from({ length: 20 }, (_, i) => ({ ref: `S${i}`, eur: 90 - i, call: `Z${i}` }))
		];
		const f = packed(many, 400, 400);
		const d = (n: { x: number; y: number }) => Math.hypot(n.x - 200, n.y - 200);
		const inner = Math.max(...f.nodes.filter((n) => n.group >= 0).map(d));
		const outer = Math.min(...f.nodes.filter((n) => n.group < 0).map(d));
		expect(inner).toBeLessThan(outer);
	});

	it('keeps area ∝ € across BOTH levels', () => {
		const f = packed(nodes, 400, 400);
		const r = (ref: string) => f.nodes.find((n) => n.ref === ref)!.r;
		expect(r('A') / r('C')).toBeCloseTo(Math.sqrt(100 / 40), 1);
	});

	it('group value is the sum of its lots', () => {
		expect(packed(nodes, 400, 400).groups[0].eur).toBe(150);
	});

	it('is deterministic and order-independent', () => {
		const pos = (ns: NetNode[]) =>
			new Map(packed(ns, 400, 400).nodes.map((n) => [n.ref, `${n.x.toFixed(2)},${n.y.toFixed(2)}`]));
		expect(pos(nodes)).toEqual(pos([...nodes].reverse()));
	});
});
