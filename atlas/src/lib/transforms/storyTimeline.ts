/**
 * The story timeline's vertical scale — pure, so it can be unit-tested with no
 * DOM (the project's convention for layout maths: `lib/transforms/*.ts`).
 *
 * Everything here is in the ARTBOARD's own coordinates (the author's 1920×1080
 * Illustrator pages). The component authors its markup 1:1 in these numbers and
 * scales the whole assembly with a single CSS transform, so SVG stroke widths,
 * dot radii and type sizes can never drift apart from each other.
 *
 * The scale is piecewise-linear, not linear in time: the artboards give roughly
 * 81.4 px to a year but compress 2016–2018, where the story has few events. The
 * table below IS that design decision, in one place.
 */

/** the three strips of the artboard's legend, left to right when spread */
export const LANES = ['world', 'greece', 'fire'] as const;
export type Lane = (typeof LANES)[number];

/** local x of each lane's rule, spread (artboard 240 / 285 / 435, less the 60 px page margin) */
export const LANE_X: Record<Lane, number> = { world: 180, greece: 225, fire: 375 };
/** local x they all converge on when collapsed (artboard 350) */
export const COLLAPSED_X = 290;

/** local y of the first year's tick */
export const AXIS_TOP = 90;

/**
 * How much height each year→year+1 interval takes, in artboard px. Measured off
 * the collapsed artboard: ~81.4 px a year, with 2016–2018 compressed because the
 * story's first years carry few events.
 */
const SPANS: ReadonlyArray<readonly [year: number, px: number]> = [
	[2016, 46],
	[2017, 46],
	[2018, 81.4],
	[2019, 81.4],
	[2020, 81.4],
	[2021, 98],
	[2022, 81.4],
	[2023, 81.4],
	[2024, 81.4],
	[2025, 81.4]
];

export interface YearStop {
	year: number;
	y: number;
	/** false for a year the axis spaces but does not name */
	labelled: boolean;
}

/**
 * The years the axis PRINTS. 2017 keeps its spacing but not its label — the
 * artboard leaves it out, because the compressed stretch has no room for it.
 */
const UNLABELLED = new Set([2017]);

/** cumulative sum of SPANS — one stop per year, first at AXIS_TOP */
export function yearStops(): YearStop[] {
	const out: YearStop[] = [];
	let y = AXIS_TOP;
	for (const [year, px] of SPANS) {
		out.push({ year, y, labelled: !UNLABELLED.has(year) });
		y += px;
	}
	const last = SPANS[SPANS.length - 1][0] + 1;
	out.push({ year: last, y, labelled: !UNLABELLED.has(last) });
	return out;
}

/** the axis's own height: the last stop plus a little air */
export function axisHeight(stops: YearStop[] = yearStops()): number {
	return stops[stops.length - 1].y + 30;
}

/**
 * A date's y. Accepts the three precisions the records actually carry —
 * `2016`, `2021-08`, `2018-07-23` — and interpolates on fraction-of-year
 * inside the bracketing pair of stops. Dates outside the axis clamp to its ends.
 */
export function yOfDate(iso: string, stops: YearStop[] = yearStops()): number {
	const t = fractionalYear(iso);
	const first = stops[0];
	const last = stops[stops.length - 1];
	if (t <= first.year) return first.y;
	if (t >= last.year) return last.y;
	for (let i = 0; i < stops.length - 1; i++) {
		const a = stops[i];
		const b = stops[i + 1];
		if (t >= a.year && t <= b.year) {
			return a.y + ((t - a.year) / (b.year - a.year)) * (b.y - a.y);
		}
	}
	return last.y;
}

/**
 * `2018-07-23` → 2018.556. Days are counted against the real length of the
 * year, so a leap year does not shift a December event by a pixel.
 */
export function fractionalYear(iso: string): number {
	const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(iso.trim());
	if (!m) return NaN;
	const year = Number(m[1]);
	const month = m[2] ? Number(m[2]) : 1;
	const day = m[3] ? Number(m[3]) : 1;
	const start = Date.UTC(year, 0, 1);
	const end = Date.UTC(year + 1, 0, 1);
	const at = Date.UTC(year, month - 1, day);
	return year + (at - start) / (end - start);
}

/** '2018-07-23' → '23-07-2018' · '2021-08' → '08-2021' · '2016' → '2016' */
export function storyDate(iso: string): string {
	const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(iso.trim());
	if (!m) return iso;
	if (m[3]) return `${m[3]}-${m[2]}-${m[1]}`;
	if (m[2]) return `${m[2]}-${m[1]}`;
	return m[1];
}
