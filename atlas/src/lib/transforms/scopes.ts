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

/** ordinal greys, light → dark down the phase order — the phases are
 *  ordered in time, so a grey ramp keeps them legible without hue
 *  (black-white-grayscale only on the Anti-nero page: user, 2026-08-20);
 *  the two qualitatively different strands take the darkest steps and
 *  the unknown phase the lightest, so it reads as "least defined" */
export const SCOPE_COLORS: Record<string, string> = {
	antinero_i: '#dedede',
	antinero_ii: '#c4c4c4',
	antinero_iii: '#a6a6a6',
	antinero_iv: '#828282',
	antinero_2026: '#5a5a5a',
	antinero_esa: '#3a3a3a',
	antinero_restoration: '#141414',
	antinero_unknown_phase: '#efefef'
};

export const scopeLabel = (s: string): string => SCOPE_LABELS[s] ?? s;
export const scopeColor = (s: string): string => SCOPE_COLORS[s] ?? '#7e7e7e';

export function orderScopes(scopes: Iterable<string>): string[] {
	const order = SCOPE_ORDER as readonly string[];
	return [...new Set(scopes)].sort(
		(a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99
	);
}
