/**
 * The two halves of the TYPES OF WORKS chord, as data (2026-08-23).
 *
 * Every contract is flagged three ways — its MAIN CATEGORY (one), its
 * CONTRACT SCOPE (one: study only / study & works / works only) and the
 * WORKS its title names (several) — and the chord pairs two of them:
 * category ↔ works, category ↔ scope, scope ↔ works. The same flagging
 * on both halves is meaningless, so those are the three pairs.
 *
 * Conventions the component relies on: `matrix` is keyed
 * `${rightKey}|${leftKey}` and counts CONTRACTS; `right.items` run from
 * the top seam clockwise (top → bottom), `left.items` from the bottom
 * seam clockwise (bottom → top); every item carries `n`, its own
 * contract count (for a work: the contracts naming it), which is what
 * the hover card prints.
 */
import { CAT_COLORS, CAT_ORDER } from '$lib/charts/catColors';
import { SCOPE_COLORS, SCOPE_LABELS, SCOPE_ORDER } from '$lib/charts/scopeColors';

export type SideKind = 'works' | 'category' | 'scope';
export interface SideItem {
	key: string;
	label: string;
	/** the item's own contracts */
	n: number;
	/** arc fill; ribbons take the RIGHT side's colour */
	color?: string;
}
export interface Side {
	kind: SideKind;
	heading: string;
	sub: string;
	/** several flags per contract (the works) or one */
	multi: boolean;
	items: SideItem[];
}
export interface ChordData {
	left: Side;
	right: Side;
	matrix: Record<string, number>;
}
export type ChordPair = 'cat-works' | 'cat-scope' | 'scope-works';
export const CHORD_PAIRS: ChordPair[] = ['cat-works', 'cat-scope', 'scope-works'];

export interface ChordNode {
	ref: string;
	cat?: string | null;
	dk?: string | null;
	wk?: string[];
}
export interface CatInput {
	key: string;
	label: string;
	n: number;
}
export interface WorkRow {
	theme: string;
	label: string;
	n: number;
	by: { key: string; n: number }[];
}

/** the works in READING order up the left half (user, 2026-08-23): the
 *  two big clearing/road works run on from the bottom seam, the four
 *  firebreak works sit side by side, then the rest by count, «no
 *  specific work named» last at the top seam */
export const WORK_ORDER = [
	'katharismoi',
	'odiko_diktyo',
	'syntirisi_zonon',
	'miktes_zones',
	'estegasmenes_zones',
	'psiles_zones'
];
export const NONE_KEY = '_none';
export const HEADINGS: Record<SideKind, { heading: string; sub: string }> = {
	works: { heading: 'WORKS NAMED IN THE TITLE', sub: 'several per contract' },
	category: { heading: 'MAIN CATEGORY', sub: 'one per contract' },
	scope: { heading: 'CONTRACT SCOPE', sub: 'one per contract' }
};

/** no caps in the names: only the opening letter is dropped */
export const lower = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);

const rankWork = (k: string) => {
	const i = WORK_ORDER.indexOf(k);
	return i >= 0 ? i : k === NONE_KEY ? 1e6 : 1e3;
};
/** works in the chord's reading order: the curated run, the rest by
 *  count, the naming-nothing bucket last */
export function orderWorks<T extends { theme: string; n: number }>(rows: T[]): T[] {
	return [...rows].sort((a, b) => rankWork(a.theme) - rankWork(b.theme) || b.n - a.n);
}

const catSide = (cats: CatInput[]): Side => ({
	kind: 'category',
	...HEADINGS.category,
	multi: false,
	items: [...cats]
		.sort((a, b) => {
			const ia = CAT_ORDER.indexOf(a.key);
			const ib = CAT_ORDER.indexOf(b.key);
			return (ia < 0 ? 1e3 : ia) - (ib < 0 ? 1e3 : ib);
		})
		.map((c) => ({ key: c.key, label: c.label, n: c.n, color: CAT_COLORS[c.key] ?? '#9b9b9b' }))
});

const scopeItems = (nodes: ChordNode[]) =>
	SCOPE_ORDER.map((k) => ({
		key: k,
		label: SCOPE_LABELS[k],
		n: nodes.filter((d) => d.dk === k).length,
		color: SCOPE_COLORS[k]
	})).filter((s) => s.n > 0);

/** category ↔ works, from the server's per-category counts (pinned) */
export function catWorks(rows: WorkRow[], cats: CatInput[], noneLabel: string): ChordData {
	const ordered = orderWorks(rows);
	const matrix: Record<string, number> = {};
	for (const r of ordered) for (const b of r.by) if (b.n > 0) matrix[`${b.key}|${r.theme}`] = b.n;
	return {
		right: catSide(cats.filter((c) => ordered.some((r) => r.by.some((b) => b.key === c.key && b.n > 0)))),
		left: {
			kind: 'works',
			...HEADINGS.works,
			multi: true,
			items: ordered.map((r) => ({
				key: r.theme,
				label: r.theme === NONE_KEY ? noneLabel : lower(r.label),
				n: r.n
			}))
		},
		matrix
	};
}

/** category ↔ scope: both one per contract — every arc and ribbon is a
 *  plain contract count */
export function catScope(nodes: ChordNode[], cats: CatInput[]): ChordData {
	const matrix: Record<string, number> = {};
	for (const d of nodes) {
		if (!d.cat || !d.dk) continue;
		const k = `${d.cat}|${d.dk}`;
		matrix[k] = (matrix[k] ?? 0) + 1;
	}
	// the left half runs bottom → top, so the scope list is reversed to
	// READ study only / study & works / works only from the top
	const items = scopeItems(nodes).reverse();
	return {
		right: catSide(cats.filter((c) => nodes.some((d) => d.cat === c.key && d.dk))),
		left: { kind: 'scope', ...HEADINGS.scope, multi: false, items },
		matrix
	};
}

/** scope ↔ works: the scope arcs measure mentions (a contract naming
 *  three works lies under three ribbons), the work arcs contracts */
export function scopeWorks(
	nodes: ChordNode[],
	themes: { theme: string; label: string }[],
	noneLabel: string
): ChordData {
	const matrix: Record<string, number> = {};
	const named: Record<string, number> = {};
	for (const d of nodes) {
		if (!d.dk) continue;
		const ws = d.wk && d.wk.length ? d.wk : [NONE_KEY];
		for (const w of ws) {
			const k = `${d.dk}|${w}`;
			matrix[k] = (matrix[k] ?? 0) + 1;
			named[w] = (named[w] ?? 0) + 1;
		}
	}
	const rows = [
		...themes.map((t) => ({ theme: t.theme, label: t.label, n: named[t.theme] ?? 0 })),
		{ theme: NONE_KEY, label: noneLabel, n: named[NONE_KEY] ?? 0 }
	].filter((r) => r.n > 0);
	return {
		right: { kind: 'scope', ...HEADINGS.scope, multi: false, items: scopeItems(nodes) },
		left: {
			kind: 'works',
			...HEADINGS.works,
			multi: true,
			items: orderWorks(rows).map((r) => ({
				key: r.theme,
				label: r.theme === NONE_KEY ? r.label : lower(r.label),
				n: r.n
			}))
		},
		matrix
	};
}

/** what each heading's toggle leads to: setting one half to scope snaps
 *  the other back to its default (scope ↔ scope is the same variable) */
export function pairFor(pair: ChordPair, side: 'left' | 'right', pick: SideKind): ChordPair {
	if (side === 'left') {
		if (pick === 'scope') return 'cat-scope';
		return pair === 'scope-works' ? 'scope-works' : 'cat-works';
	}
	if (pick === 'scope') return 'scope-works';
	return pair === 'cat-scope' ? 'cat-scope' : 'cat-works';
}
export const sidesOf = (pair: ChordPair): { left: SideKind; right: SideKind } =>
	pair === 'cat-scope'
		? { left: 'scope', right: 'category' }
		: pair === 'scope-works'
			? { left: 'works', right: 'scope' }
			: { left: 'works', right: 'category' };
