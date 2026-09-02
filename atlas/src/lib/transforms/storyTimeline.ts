import { EVENTS } from '$lib/story/events';

/**
 * The story timeline's vertical scale and block layout — pure, so it can be
 * unit-tested with no DOM (the project's convention for layout maths:
 * `lib/transforms/*.ts`). (`events.ts`'s own import from here is type-only,
 * so the runtime import above closes no cycle.)
 *
 * Everything here is in the ARTBOARD's own coordinates (the author's 1920×1080
 * Illustrator pages). The component authors its markup 1:1 in these numbers and
 * scales the whole assembly with a single CSS transform, so SVG stroke widths,
 * dot radii and type sizes can never drift apart from each other.
 *
 * The scale is piecewise-linear, not linear in time: the artboards give roughly
 * 81.4 px to a year, and the table below is where every departure from that
 * lives — the compressed prehistory, and the room 2021 needs. It IS the design
 * decision, in one place.
 */

/** the three strips of the artboard's legend, left to right when spread */
export const LANES = ['world', 'greece', 'fire'] as const;
export type Lane = (typeof LANES)[number];

/** local x of each lane's rule, spread (artboard 240 / 285 / 435, less the 60 px page margin) */
export const LANE_X: Record<Lane, number> = { world: 180, greece: 225, fire: 375 };
/** local x they all converge on when collapsed — set so the line sits
 * near the column's centre with the native disclaimer readable on its left
 * (the author's balance round, 2026-09-02) */
export const COLLAPSED_X = 345;

/** local y of the first year's tick */
export const AXIS_TOP = 90;

/**
 * Where each lane's event blocks are set — the artboard's own arrangement,
 * which the legend labels already follow: the world lane's text hangs to the
 * LEFT of its rule (its rule sits only 45 px from Greece's, with no room
 * between them), Greece's occupies the gap out to the fire rule, and the fire
 * lane's runs to the column's right edge.
 *
 * The world lane's column starts at 66, not at the page margin: when the
 * timeline spreads, the YEARS move into that margin, and text set under them is
 * text nobody can read. `YEAR_W` is the gutter they are held to — the big
 * active year's type size is capped to it for the same reason.
 */
export const YEAR_W = 56;
export const LANE_TEXT: Record<Lane, { x: number; w: number; align: 'left' | 'right' }> = {
	world: { x: 66, w: 106, align: 'right' },
	greece: { x: 235, w: 132, align: 'left' },
	fire: { x: 383, w: 130, align: 'left' }
};

/**
 * How much height each stop→next-stop interval takes, in artboard px. Measured
 * off the collapsed artboard at ~81.4 px a year, with three departures the
 * author's own spreadsheet forces:
 *
 *  · 2007 → 2016 is PREHISTORY — two events in nine years (the Peloponnese
 *    fires and Law 3889/2010). It is drawn as two short compressed steps, and
 *    the axis marks the break so the compression is never read as duration.
 *  · 2021 carries 12 of the 31 events and EIGHT of them inside one fortnight
 *    of August. At an even year's pitch those eight sit inside 3 px.
 *  · 2023 carries the Rhodes and Evros fires and their two committees.
 *
 * Stops need NOT be consecutive years; `yOfDate` interpolates inside whatever
 * pair brackets a date.
 */
const SPANS: ReadonlyArray<readonly [year: number, px: number]> = [
	[2007, 46],
	[2010, 46],
	[2016, 46],
	[2017, 46],
	[2018, 81.4],
	[2019, 81.4],
	[2020, 81.4],
	[2021, 260],
	[2022, 81.4],
	[2023, 110],
	[2024, 81.4],
	[2025, 81.4],
	[2026, 81.4]
];

export interface YearStop {
	year: number;
	y: number;
	/** the label's y — centred on the span to the next stop, so the year
	 *  prints level with the events it holds (the author, 2026-09-02) */
	midY: number;
	/** false for a year the axis spaces but does not name */
	labelled: boolean;
	/** years to the NEXT stop — >1 means the axis is compressed here */
	gap: number;
}

/**
 * The years the axis PRINTS. 2017 keeps its spacing but not its label (the
 * artboard's own economy), and 2027 is only the axis's endpoint — it exists
 * so 2026 is a real year instead of a point the last events clamp onto.
 */
const UNLABELLED = new Set([2017, 2027]);

/**
 * How much a span's own events need: the tallest lane's stack of CLOSED
 * blocks inside [year, next). This is what keeps the lanes CORRESPONDING
 * with the years (the author, 2026-09-02, after two screenshots): a year
 * whose events cannot fit its pixels forces the whole chain below to smear
 * past the labels, however the dodge balances it.
 */
function neededPx(year: number, next: number): number {
	const byLane = new Map<Lane, number>();
	for (const e of EVENTS) {
		const t = fractionalYear(e.date);
		if (t >= year && t < next) {
			const h = blockHeight({ title: e.title }, LANE_TEXT[e.lane].w) + BLOCK_GAP;
			byLane.set(e.lane, (byLane.get(e.lane) ?? 0) + h);
		}
	}
	return byLane.size ? Math.max(...byLane.values()) + 10 : 0;
}

/** cumulative sum of SPANS, each grown to hold its own events' blocks */
export function yearStops(): YearStop[] {
	const out: YearStop[] = [];
	let y = AXIS_TOP;
	for (let i = 0; i < SPANS.length; i++) {
		const [year, px] = SPANS[i];
		const next = i + 1 < SPANS.length ? SPANS[i + 1][0] : year + 1;
		out.push({ year, y, midY: y, labelled: !UNLABELLED.has(year), gap: next - year });
		y += Math.max(px, neededPx(year, next));
	}
	const last = SPANS[SPANS.length - 1][0] + 1;
	out.push({ year: last, y, midY: y, labelled: !UNLABELLED.has(last), gap: 0 });
	for (let i = 0; i < out.length - 1; i++) out[i].midY = (out[i].y + out[i + 1].y) / 2;
	return out;
}

/** the year scale's own height: the last stop plus a little air */
export function axisHeight(stops: YearStop[] = yearStops()): number {
	return stops[stops.length - 1].y + 30;
}

/**
 * A date's y. Accepts the three precisions the records carry — `2016`,
 * `2021-08`, `2018-07-23` — and interpolates on fraction-of-year inside the
 * bracketing pair of stops. Dates outside the axis clamp to its ends.
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

/** a period's dates as the artboard writes them: '03-08 → 12-08-2021' */
export function storyRange(from: string, to: string): string {
	const a = storyDate(from).split('-');
	const b = storyDate(to);
	// same year: the start drops it, since the end carries it
	if (a.length === 3 && b.endsWith(a[2])) return `${a[0]}-${a[1]} → ${b}`;
	return `${storyDate(from)} → ${b}`;
}

/* ─────────────────────────  block layout  ───────────────────────── */

/**
 * The type metrics the block heights are estimated from. Measuring every block
 * in the DOM would be exact but would make the layout un-testable and would run
 * on every resize; the project estimates the same way in `CatWorkChord`
 * (4.9 px/char there, at a different size). CHAR_W is futura-100-greek-book at
 * 11 px, measured on the running page.
 */
const CHAR_W = 5.4;
const LINE = 13.2;
const DATE_H = 13;
/** the block prints at most this many lines of each; CSS clamps to match */
export const TITLE_CLAMP = 4;
export const BODY_CLAMP = 2;
/** clear air between one block's bottom and the next block's top */
const BLOCK_GAP = 12;
/** the block's first line sits this far above its dot, so they read as level */
const DOT_LIFT = 4;

/**
 * The estimated height of one event's block in a column `w` wide. An OPEN
 * block (the reader is at its period) STRETCHES: full title and full body,
 * no clamps — the author, 2026-09-02: a highlighted event must be readable
 * whole. A closed block clamps the title and carries no body. Open blocks
 * get one line of slack, because the estimate must never run SHORT (the
 * next block would overlap the real text).
 */
export function blockHeight(e: { title: string; body?: string }, w: number, open = false): number {
	const cpl = Math.max(8, Math.floor(w / CHAR_W));
	const titleLines = Math.max(1, Math.ceil(e.title.length / cpl));
	const title = open ? titleLines : Math.min(TITLE_CLAMP, titleLines);
	const bodyLines = e.body ? Math.ceil(e.body.length / cpl) : 0;
	const body = open ? bodyLines : Math.min(BODY_CLAMP, bodyLines);
	return DATE_H + title * LINE + (body ? 3 + body * LINE : 0) + (open ? LINE : 0);
}

export interface PlacedEvent<E> {
	e: E;
	/** the dot's y — the event's TRUE date, never moved */
	dotY: number;
	/** a period's lower end */
	endY?: number;
	/** the text block's top — pushed down where blocks would collide */
	blockY: number;
	h: number;
	/** true where the block had to leave its dot, so a leader line is drawn */
	pushed: boolean;
}

/** blocks may not rise into the spread legend's line */
const MIN_TOP = 62;

/**
 * Place one lane's blocks. The DOT keeps its true y always; where events
 * crowd, the blocks BALANCE around their dates (pool-adjacent-violators:
 * order kept, no overlaps, each contiguous crowd centred on the least-squares
 * mean of its members' dates) — never the old downward-only push, which let
 * 2021's blocks cascade beside the 2022-2023 year labels (the author,
 * 2026-09-02). A block may sit above OR below its dot; the leader line joins
 * it back either way. Events must arrive in date order.
 */
export function layoutLane<E extends { title: string; body?: string; date: string; end?: string }>(
	events: E[],
	stops: YearStop[] = yearStops(),
	width = 132,
	/** whether this event is OPEN — the author's rule: while the main text
	 *  is at the event's period it stretches to its FULL title and body */
	open: (e: E) => boolean = () => true
): PlacedEvent<E>[] {
	const want = events.map((e) => yOfDate(e.date, stops) - DOT_LIFT);
	const hs = events.map((e) =>
		open(e) ? blockHeight(e, width, true) : blockHeight({ title: e.title }, width)
	);

	interface Cluster {
		top: number;
		height: number;
		count: number;
		/** Σ of members' desired cluster-top (want minus offset inside) */
		sumDesired: number;
		start: number;
	}
	const clusters: Cluster[] = [];
	for (let i = 0; i < events.length; i++) {
		let c: Cluster = {
			top: Math.max(MIN_TOP, want[i]),
			height: hs[i] + BLOCK_GAP,
			count: 1,
			sumDesired: want[i],
			start: i
		};
		// merge backwards while overlapping the previous crowd
		while (clusters.length) {
			const p = clusters[clusters.length - 1];
			if (p.top + p.height <= c.top) break;
			clusters.pop();
			c = {
				top: 0,
				height: p.height + c.height,
				count: p.count + c.count,
				// appending after p shifts every member of c down by p.height
				sumDesired: p.sumDesired + c.sumDesired - p.height * c.count,
				start: p.start
			};
			c.top = Math.max(MIN_TOP, c.sumDesired / c.count);
		}
		clusters.push(c);
	}

	const ys = new Array<number>(events.length);
	for (const c of clusters) {
		let y = c.top;
		for (let i = c.start; i < c.start + c.count; i++) {
			ys[i] = y;
			y += hs[i] + BLOCK_GAP;
		}
	}

	return events.map((e, i) => {
		const dotY = want[i] + DOT_LIFT;
		return {
			e,
			dotY,
			endY: e.end && e.end !== e.date ? yOfDate(e.end, stops) : undefined,
			blockY: ys[i],
			h: hs[i],
			pushed: Math.abs(ys[i] - want[i]) > 1
		};
	});
}

/**
 * How tall the drawing actually is: the year scale, or the lowest block if the
 * pushes ran past it. The rail is a viewport onto this and pans — 31 blocks
 * cannot be read at once in a column one screen tall.
 */
export function contentHeight(placed: PlacedEvent<unknown>[][], stops = yearStops()): number {
	let low = axisHeight(stops);
	for (const lane of placed) {
		for (const p of lane) low = Math.max(low, p.blockY + p.h + 20);
	}
	return low;
}
