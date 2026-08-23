/**
 * CONTRACT SCOPE's three tones and wording — «study only / study & works /
 * works only», the 1-2-3 model shared with the sponsored dataset — used
 * by the CONTRACT SCOPE share bar and by the chord when a half is set to
 * the scope (2026-08-23). Solid greys on purpose: they work as arc fills
 * and as ribbons, which the timeline's white-with-ring study mark cannot.
 */
export const SCOPE_ORDER = ['study', 'study_and_works', 'works'] as const;
export const SCOPE_COLORS: Record<string, string> = {
	study: '#b5b5b5',
	study_and_works: '#6c6c6c',
	works: '#3d3d3d'
};
export const SCOPE_LABELS: Record<string, string> = {
	study: 'study only',
	study_and_works: 'study & works',
	works: 'works only'
};
