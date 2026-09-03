/** Signature-year ramp for the ΔΑΣΕ value chart.
 *
 *  Sequential greens on the page's --c-dase family, light → deep by year.
 *  Shared by the dots, the stacked value brackets and the legend above them:
 *  one legend serves both modes only if all three read from this table.
 */
// Live CSS strings over the tokens since the Theme Lab round (2026-09-03):
// one --c-dase family, light steps faded toward paper, dark steps shaded
// toward black in oklab. The mix percentages were fitted to the old hand
// hexes (max drift 6/255 on the two deepest steps — the old scale rotated
// hue slightly, which a one-anchor family cannot).
export const YEAR_COLORS: Record<string, string> = {
	'2021': 'color-mix(in oklab, var(--c-dase) 39.2%, var(--paper))',
	'2022': 'color-mix(in srgb, var(--c-dase) 66%, var(--paper))',
	'2023': 'color-mix(in oklab, var(--c-dase) 92.6%, var(--paper))',
	'2024': 'color-mix(in oklab, var(--c-dase) 90%, black)',
	'2025': 'color-mix(in oklab, var(--c-dase) 72.9%, black)',
	'2026': 'color-mix(in oklab, var(--c-dase) 54.2%, black)'
};

/** Colour for a signature year; undated contracts render neutral. */
export const yearColor = (y: string | null | undefined): string =>
	YEAR_COLORS[y ?? ''] ?? 'color-mix(in srgb, var(--ink) 57.4%, var(--paper))';

/** Signature-year ramp for the Anti-nero value chart — the same idea in the
 *  page's own palette: black-white-grayscale only (user, 2026-08-20),
 *  light → dark by year so the ordering survives without hue. */
export const YEAR_GREYS: Record<string, string> = {
	'2022': 'color-mix(in srgb, var(--ink) 18.1%, var(--paper))',
	'2023': 'color-mix(in srgb, var(--ink) 35.1%, var(--paper))',
	'2024': 'color-mix(in srgb, var(--ink) 53.4%, var(--paper))',
	'2025': 'color-mix(in srgb, var(--ink) 75.3%, var(--paper))',
	'2026': 'color-mix(in srgb, var(--ink) 92%, black)'
};

export const yearGrey = (y: string | null | undefined): string =>
	YEAR_GREYS[y ?? ''] ?? 'color-mix(in srgb, var(--ink) 44.9%, var(--paper))';
