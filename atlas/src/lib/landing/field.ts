/**
 * The landing page's field of codes (user mock, 2026-08-27): every
 * identifier the site holds, written vertically one glyph per line in
 * columns that drift up and down at their own speeds. Pure layout —
 * the canvas shell only draws what these functions return — so it is
 * deterministic for a seed and testable.
 */
import { mulberry32 } from '$lib/transforms/prng';
import type { Landing } from '$lib/api';

export type Ds = 'antinero' | 'dase' | 'anadohoi';
export interface FieldCode {
	text: string;
	ds: Ds;
}
export interface Run {
	code: FieldCode;
	/** the run's first glyph, in lines from the column's top */
	line: number;
}
export interface Column {
	x: number;
	/** px per second; the sign is the direction */
	speed: number;
	/** px, where the column starts at t = 0 */
	phase: number;
	runs: Run[];
	/** the stacked height of one cycle, in lines */
	lines: number;
}
export interface Glyph {
	ch: string;
	ds: Ds;
	x: number;
	y: number;
}
export interface FieldOptions {
	/** column pitch, px */
	colW: number;
	/** line pitch, px */
	lineH: number;
	/** blank lines between two codes in a column */
	gap: number;
	minCols: number;
	maxCols: number;
}
/** Artboard 1 (user, 2026-08-27): 12 px glyphs on 14.4 px lines, a column
 *  every 25.7 px — 74 across a 1920 frame — one blank line between codes */
export const FIELD: FieldOptions = {
	colW: 25.7,
	lineH: 14.4,
	gap: 1,
	minCols: 6,
	maxCols: 160
};
/** the menu cell shows the same field, clipped — Artboard 2 */
export const FIELD_DENSE: FieldOptions = FIELD;

/** every code tagged with its dataset, in a seeded shuffle */
export function poolFrom(payload: Landing, seed: number): FieldCode[] {
	const out: FieldCode[] = [];
	const push = (ds: Ds, lists: (string[] | undefined)[]) => {
		for (const l of lists) for (const text of l ?? []) out.push({ text, ds });
	};
	push('antinero', [payload.antinero.contracts, payload.antinero.acts]);
	push('dase', [payload.dase?.contracts, payload.dase?.acts]);
	push('anadohoi', [payload.anadohoi?.acts]);
	const rand = mulberry32(seed);
	for (let i = out.length - 1; i > 0; i--) {
		const j = Math.floor(rand() * (i + 1));
		[out[i], out[j]] = [out[j], out[i]];
	}
	return out;
}

/** columns across a width, each an endless stack of codes at least twice
 *  the viewport tall, with its own speed, direction and phase */
export function layoutColumns(
	width: number,
	height: number,
	pool: FieldCode[],
	seed: number,
	o: FieldOptions = FIELD
): Column[] {
	if (!pool.length || width <= 0 || height <= 0) return [];
	const n = Math.max(o.minCols, Math.min(o.maxCols, Math.floor(width / o.colW)));
	const minLines = Math.ceil((2 * height) / o.lineH);
	const cols: Column[] = [];
	for (let i = 0; i < n; i++) {
		const rand = mulberry32(seed * 31 + i);
		const runs: Run[] = [];
		let line = 0;
		for (let k = i; runs.length === 0 || line < minLines; k += n) {
			const code = pool[k % pool.length];
			runs.push({ code, line });
			line += code.text.length + o.gap;
		}
		const speed = (8 + rand() * 22) * (rand() < 0.5 ? -1 : 1);
		const phase = rand() * line * o.lineH;
		cols.push({ x: i * o.colW + o.colW / 2, speed, phase, runs, lines: line });
	}
	return cols;
}

/** the glyphs of one column visible in a viewport of `height` at `elapsedMs` */
export function glyphsAt(
	col: Column,
	elapsedMs: number,
	height: number,
	o: FieldOptions = FIELD
): Glyph[] {
	const cycle = col.lines * o.lineH;
	let offset = (col.phase + (col.speed * elapsedMs) / 1000) % cycle;
	if (offset < 0) offset += cycle;
	const out: Glyph[] = [];
	// the column repeats every `cycle` px; draw the copy that covers the
	// viewport and the one above it
	for (const base of [-cycle, 0]) {
		for (const run of col.runs) {
			const top = run.line * o.lineH - offset + base;
			const bottom = top + run.code.text.length * o.lineH;
			if (bottom < 0 || top > height) continue;
			for (let g = 0; g < run.code.text.length; g++) {
				const y = top + g * o.lineH;
				if (y < -o.lineH || y > height) continue;
				out.push({ ch: run.code.text[g], ds: run.code.ds, x: col.x, y });
			}
		}
	}
	return out;
}
