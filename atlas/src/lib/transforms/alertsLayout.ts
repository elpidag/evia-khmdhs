/**
 * Layout maths of the story's Figure 04 that the canvas must not decide for
 * itself (the project's rule for pure, testable geometry): the day strip
 * along the bottom of the square, the dot radii, and the greedy placement
 * of the active alert's village labels. Everything scales with the square's
 * side over the 540 px artboard.
 */
import { END_MS, START_MS } from './alerts';

const DAY = 86_400_000;
const ATHENS = 3 * 3_600_000;

export interface Tick {
	x: number;
	/** the day's start, simulated ms */
	ms: number;
	label?: string;
}

export interface Strip {
	/** the wash band behind the strip */
	band: { y0: number; y1: number };
	x0: number;
	x1: number;
	/** the ticks' baseline */
	y: number;
	tickH: number;
	ticks: Tick[];
	/** x of a simulated instant, linear over the window */
	xOf(ms: number): number;
}

/** the scale factor over the 540 px artboard */
export const k = (size: number): number => size / 540;

export function dayStrip(size: number, start = START_MS, end = END_MS): Strip {
	const s = k(size);
	const x0 = 14 * s;
	const x1 = size - 14 * s;
	const band = { y0: size - 22 * s, y1: size };
	const y = size - 9 * s;
	const xOf = (ms: number) => x0 + ((ms - start) / (end - start)) * (x1 - x0);
	const ticks: Tick[] = [];
	for (let ms = start; ms < end; ms += DAY) {
		const d = new Date(ms + ATHENS).getUTCDate();
		const mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][
			new Date(ms + ATHENS).getUTCMonth()
		];
		const label = d === 1 ? `${d} ${mon}` : d % 10 === 0 ? String(d) : undefined;
		ticks.push({ x: xOf(ms), ms, label });
	}
	return { band, x0, x1, y, tickH: 5 * s, ticks, xOf };
}

export type DotKind = 'active' | 'past';

/** dot radii in CSS px at the given square side */
export function dotRadius(kind: DotKind, size: number): number {
	return (kind === 'active' ? 3.2 : 1.6) * k(size);
}

export interface LabelItem {
	x: number;
	y: number;
	/** the measured text width */
	w: number;
	h: number;
	/** the dot's radius the label keeps clear of */
	r: number;
}

export interface Box {
	x: number;
	y: number;
	w: number;
	h: number;
}

const overlaps = (a: Box, b: Box): boolean =>
	a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

/**
 * Greedy label placement: for each item in order try right, left, above,
 * below of its dot and keep the first box that lies inside the bounds and
 * overlaps neither a placed label nor an obstacle; an item that fits
 * nowhere gets null (its name still rides on the card). Deterministic.
 */
export function placeLabels(items: LabelItem[], bounds: { w: number; h: number }, obstacles: Box[] = []): (Box | null)[] {
	const placed: Box[] = [...obstacles];
	const out: (Box | null)[] = [];
	for (const it of items) {
		const gap = it.r + 3;
		const candidates: Box[] = [
			{ x: it.x + gap, y: it.y - it.h / 2, w: it.w, h: it.h },
			{ x: it.x - gap - it.w, y: it.y - it.h / 2, w: it.w, h: it.h },
			{ x: it.x - it.w / 2, y: it.y - gap - it.h, w: it.w, h: it.h },
			{ x: it.x - it.w / 2, y: it.y + gap, w: it.w, h: it.h }
		];
		let chosen: Box | null = null;
		for (const c of candidates) {
			if (c.x < 0 || c.y < 0 || c.x + c.w > bounds.w || c.y + c.h > bounds.h) continue;
			if (placed.some((p) => overlaps(p, c))) continue;
			chosen = c;
			break;
		}
		if (chosen) placed.push(chosen);
		out.push(chosen);
	}
	return out;
}
