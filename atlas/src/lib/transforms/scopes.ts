/** Programme-phase vocabulary shared by every Anti-nero chart. */

export const SCOPE_ORDER = [
	'antinero_i',
	'antinero_ii',
	'antinero_iii',
	'antinero_iv',
	'antinero_2026',
	'antinero_esa',
	'antinero_restoration',
	'antinero_unknown_phase'
] as const;

export const SCOPE_LABELS: Record<string, string> = {
	antinero_i: 'Anti-nero I',
	antinero_ii: 'Anti-nero II',
	antinero_iii: 'Anti-nero III',
	antinero_iv: 'Anti-nero IV',
	antinero_2026: 'Anti-nero 2026',
	antinero_esa: 'ΕΣΑ reforestation',
	antinero_restoration: 'Restoration works',
	antinero_unknown_phase: 'Phase unknown',
	// kept in the dataset, excluded from every calculation (DATA_DECISIONS 2026-08-13)
	antinero_probable: 'Probably Anti-nero — not included in the calculations'
};

/** warm ramp for the sequential phases; green/purple for the two
 *  qualitatively different strands (reforestation, restoration) */
export const SCOPE_COLORS: Record<string, string> = {
	antinero_i: '#c9a227',
	antinero_ii: '#de7a1c',
	antinero_iii: '#b33a1a',
	antinero_iv: '#7c2d12',
	antinero_2026: '#451a03',
	antinero_esa: '#3d7a4a',
	antinero_restoration: '#6b4b8a',
	antinero_unknown_phase: '#8a7f6e'
};

export const scopeLabel = (s: string): string => SCOPE_LABELS[s] ?? s;
export const scopeColor = (s: string): string => SCOPE_COLORS[s] ?? '#8a7f6e';

export function orderScopes(scopes: Iterable<string>): string[] {
	const order = SCOPE_ORDER as readonly string[];
	return [...new Set(scopes)].sort(
		(a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99
	);
}
