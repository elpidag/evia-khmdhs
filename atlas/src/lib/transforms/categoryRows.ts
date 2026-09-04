/**
 * The CONTRACT TYPE rows — ONE transform for the Anti-nero page's frame and
 * the story's Figure 27 (the author, 2026-09-03: «instead of an image, show
 * our graph»), so the two can never drift: the curated categories sorted by
 * the lens, the hover naming the works the category's contracts name, the
 * names lower-cased and their explanatory tails moved into a hint.
 */
import type { BarRow } from '$lib/charts/BarH.svelte';
import { grInt } from '$lib/transforms/format';

export interface CategoryLike {
	key: string;
	label: string;
	label_en?: string;
	n: number;
	eur: number;
	names?: { label_en: string; n: number }[];
}

export type CategoryLens = 'eur' | 'n';

/** the pair reads all in lower case (user, 2026-08-22) — only the opening
 *  letter is dropped, so proper nouns («National Reforestation Plan») stay */
export const lowerRows = <T extends { label: string }>(rows: T[]): T[] =>
	rows.map((r) => ({ ...r, label: r.label.charAt(0).toLowerCase() + r.label.slice(1) }));

/** a category name's explanatory tail — after a «:», or a trailing
 *  parenthetical — moves into an i beside the short name (user, 2026-08-22) */
export const splitHint = (s: string): { label: string; hint?: string } => {
	const colon = s.indexOf(':');
	if (colon > 0)
		return { label: s.slice(0, colon).trim(), hint: `including ${s.slice(colon + 1).trim()}` };
	const paren = s.match(/^(.*\S)\s+\((.+)\)$/);
	if (paren) return { label: paren[1], hint: paren[2] };
	return { label: s };
};

/** the bars, biggest first by the lens; the hover carries the contract
 *  count and what this category's contracts NAME, from the themes layer */
export function categoryRows(categories: CategoryLike[], lens: CategoryLens): BarRow[] {
	const rows = [...categories]
		.sort((a, b) => (lens === 'eur' ? b.eur - a.eur : b.n - a.n))
		.map((c) => ({
			label: c.label_en ?? c.label,
			value: lens === 'eur' ? c.eur : c.n,
			title:
				`${c.label_en ?? c.label} — ${grInt(c.n)} contracts` +
				(c.names?.length
					? `. Works named: ${c.names.map((w) => `${w.label_en.toLowerCase()} ${grInt(w.n)}`).join(', ')}`
					: '')
		}));
	return lowerRows(rows).map((r) => ({ ...r, ...splitHint(r.label) }));
}
