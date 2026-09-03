/** Programme-phase vocabulary shared by every Anti-nero chart. */

export const SCOPE_ORDER = [
	'antinero_i',
	'antinero_ii',
	'antinero_iii',
	'antinero_iv',
	'antinero_v_plus',
	'antinero_esa',
	'antinero_restoration',
	'antinero_unknown_phase'
] as const;

export const SCOPE_LABELS: Record<string, string> = {
	antinero_i: 'Anti-nero I',
	antinero_ii: 'Anti-nero II',
	antinero_iii: 'Anti-nero III',
	antinero_iv: 'Anti-nero IV',
	// the ministry's own name for the February-2026 batch (DATA_DECISIONS 2026-08-29)
	antinero_v_plus: 'Anti-nero V-PLUS',
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
	antinero_i: 'color-mix(in srgb, var(--ink) 14.6%, var(--paper))',
	antinero_ii: 'color-mix(in srgb, var(--ink) 26.2%, var(--paper))',
	antinero_iii: 'color-mix(in srgb, var(--ink) 39.6%, var(--paper))',
	antinero_iv: 'color-mix(in srgb, var(--ink) 55.6%, var(--paper))',
	antinero_v_plus: 'color-mix(in srgb, var(--ink) 73.5%, var(--paper))',
	antinero_esa: 'color-mix(in srgb, var(--ink) 87.8%, var(--paper))',
	antinero_restoration: 'color-mix(in srgb, var(--ink) 63%, black)',
	antinero_unknown_phase: 'color-mix(in srgb, var(--ink) 7%, var(--paper))'
};

export const scopeLabel = (s: string): string => SCOPE_LABELS[s] ?? s;
export const scopeColor = (s: string): string => SCOPE_COLORS[s] ?? 'color-mix(in srgb, var(--ink) 57.4%, var(--paper))';

export function orderScopes(scopes: Iterable<string>): string[] {
	const order = SCOPE_ORDER as readonly string[];
	return [...new Set(scopes)].sort(
		(a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99
	);
}
