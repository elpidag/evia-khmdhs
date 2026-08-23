import { describe, expect, it } from 'vitest';
import {
	catScope,
	catWorks,
	orderWorks,
	pairFor,
	scopeWorks,
	sidesOf,
	type ChordNode
} from './chordSides';

const cats = [
	{ key: 'dasotexnika', label: 'special forestry works', n: 3 },
	{ key: 'meletes', label: 'management studies', n: 1 }
];
const nodes: ChordNode[] = [
	{ ref: 'A', cat: 'dasotexnika', dk: 'works', wk: ['katharismoi', 'odiko_diktyo'] },
	{ ref: 'B', cat: 'dasotexnika', dk: 'study_and_works', wk: ['katharismoi'] },
	{ ref: 'C', cat: 'dasotexnika', dk: 'study_and_works', wk: [] },
	{ ref: 'D', cat: 'meletes', dk: 'study', wk: ['meletes'] }
];

describe('orderWorks', () => {
	it('runs the curated works first, the rest by count, the naming-nothing bucket last', () => {
		const rows = [
			{ theme: 'nero', n: 9 },
			{ theme: '_none', n: 40 },
			{ theme: 'psiles_zones', n: 1 },
			{ theme: 'katharismoi', n: 5 },
			{ theme: 'anadasoseis', n: 12 }
		];
		expect(orderWorks(rows).map((r) => r.theme)).toEqual([
			'katharismoi',
			'psiles_zones',
			'anadasoseis',
			'nero',
			'_none'
		]);
	});
});

describe('catWorks', () => {
	it('keys the matrix right|left with the server counts and lower-cases the work names', () => {
		const d = catWorks(
			[
				{ theme: 'katharismoi', label: 'Clearing of forests', n: 2, by: [{ key: 'dasotexnika', n: 2 }] },
				{ theme: '_none', label: 'x', n: 1, by: [{ key: 'dasotexnika', n: 1 }] }
			],
			cats,
			'no specific work named'
		);
		expect(d.matrix['dasotexnika|katharismoi']).toBe(2);
		expect(d.left.items.map((i) => i.label)).toEqual(['clearing of forests', 'no specific work named']);
		// a category with no ribbon is not drawn
		expect(d.right.items.map((i) => i.key)).toEqual(['dasotexnika']);
		expect(d.left.multi).toBe(true);
	});
});

describe('catScope', () => {
	it('counts contracts per (category, scope) — both halves one per contract', () => {
		const d = catScope(nodes, cats);
		expect(d.matrix).toEqual({
			'dasotexnika|works': 1,
			'dasotexnika|study_and_works': 2,
			'meletes|study': 1
		});
		// the left half reads study only / study & works / works only from the
		// TOP, so the list (bottom → top) is reversed
		expect(d.left.items.map((i) => i.key)).toEqual(['works', 'study_and_works', 'study']);
		expect(d.left.items.map((i) => i.n)).toEqual([1, 2, 1]);
		expect(d.left.multi).toBe(false);
	});
});

describe('scopeWorks', () => {
	it('counts mentions per (scope, work), a naming-nothing bucket, works n = contracts naming it', () => {
		const d = scopeWorks(
			nodes,
			[
				{ theme: 'katharismoi', label: 'Clearing of forests' },
				{ theme: 'odiko_diktyo', label: 'Road maintenance' },
				{ theme: 'meletes', label: 'Studies' }
			],
			'no specific work named'
		);
		expect(d.matrix['works|katharismoi']).toBe(1);
		expect(d.matrix['study_and_works|katharismoi']).toBe(1);
		expect(d.matrix['study_and_works|_none']).toBe(1);
		expect(d.matrix['study|meletes']).toBe(1);
		const k = d.left.items.find((i) => i.key === 'katharismoi')!;
		expect(k.n).toBe(2);
		expect(d.right.items.map((i) => i.key)).toEqual(['study', 'study_and_works', 'works']);
	});
});

describe('pairFor', () => {
	it('never lets both halves be the scope', () => {
		expect(pairFor('cat-works', 'left', 'scope')).toBe('cat-scope');
		expect(pairFor('cat-works', 'right', 'scope')).toBe('scope-works');
		expect(pairFor('cat-scope', 'right', 'scope')).toBe('scope-works');
		expect(pairFor('scope-works', 'left', 'scope')).toBe('cat-scope');
		expect(pairFor('cat-scope', 'left', 'works')).toBe('cat-works');
		expect(pairFor('scope-works', 'right', 'category')).toBe('cat-works');
		for (const p of ['cat-works', 'cat-scope', 'scope-works'] as const) {
			const s = sidesOf(p);
			expect(s.left === 'scope' && s.right === 'scope').toBe(false);
		}
	});
});
