/** Signature-year ramp for the ΔΑΣΕ value chart.
 *
 *  Sequential greens on the page's --c-dase family, light → deep by year.
 *  Shared by the dots, the stacked value brackets and the legend above them:
 *  one legend serves both modes only if all three read from this table.
 */
export const YEAR_COLORS: Record<string, string> = {
	'2021': '#bfe3cf',
	'2022': '#8fd1ae',
	'2023': '#63bd8e',
	'2024': '#43a276',
	'2025': '#2d7d59',
	'2026': '#1c5138'
};

/** Colour for a signature year; undated contracts render neutral. */
export const yearColor = (y: string | null | undefined): string =>
	YEAR_COLORS[y ?? ''] ?? '#8a7f6e';

/** Signature-year ramp for the Anti-nero value chart — the same idea in the
 *  page's own palette: black-white-grayscale only (user, 2026-08-20),
 *  light → dark by year so the ordering survives without hue. */
export const YEAR_GREYS: Record<string, string> = {
	'2022': '#d6d6d6',
	'2023': '#b0b0b0',
	'2024': '#878787',
	'2025': '#565656',
	'2026': '#1d1d1d'
};

export const yearGrey = (y: string | null | undefined): string =>
	YEAR_GREYS[y ?? ''] ?? '#9a9a9a';
