/**
 * One scene per arrangement of the Anti-nero programme chart.
 *
 * The mark never changes — one circle per in-scope contract, area ∝ stated
 * net €, colour = programme phase — so the toggle rearranges a population
 * instead of swapping in a different chart, and a dot keeps its identity
 * (and its DOM node) across modes. What changes is what POSITION means:
 *
 *   time  — when it was signed (x), dodged (y); lots of one call are tied
 *   call  — nothing; contracts are packed into a star per call, plus bands
 *   pack  — containment: every call is a bubble holding its contracts
 *
 * Assembling the scene here rather than in the component keeps it pure and
 * unit-testable, and keeps the component inside the ~300-line house cap.
 */
import {
	band,
	layout,
	packed,
	timeline,
	type NetNode,
	type PackGroup,
	type Placed,
	type Tie
} from './network';

export type NetMode = 'time' | 'call' | 'pack';
/** The arrangements OFFERED. `call` (the star field) is built and tested but
 *  off the site by user decision 2026-08-18 — it may come back, so the scene
 *  and its units stay; only this list decides what the toggle shows. */
// «Nested by call» (pack) is PARKED since 2026-08-22 (user) — its scene
// stays below, ready to return; the toggle now switches the COLOUR lens
// over the one timeline: the contract's scope or its curated type.
export const NET_MODES: { value: string; label: string }[] = [
	{ value: 'scope', label: 'By contract scope' },
	{ value: 'type', label: 'By contract type' }
];

export interface Seg {
	key: string;
	x1: number;
	y1: number;
	x2: number;
	y2: number;
	/** contractors bridging the two calls, for the hover title */
	who?: string[];
	vats?: string[];
}
/** a call id readable by people: a ΚΗΜΔΗΣ ΑΔΑΜ stays itself; the nine
 *  ΤΑΙΠΕΔ date-only calls print as the date they are known by */
export const callText = (id: string): string =>
	id.startsWith('date:') ? `πρόσκληση ${id.slice(5).split('-').reverse().join('.')}` : id;

export interface Label {
	key: string;
	x: number;
	y: number;
	text: string;
	cls: 'val' | 'adam' | 'band' | 'year' | 'leaf';
	anchor?: 'start' | 'middle';
	/** px font size, when the label is sized to the circle it sits in */
	size?: number;
	/** the mark this label belongs to, for its ink colour */
	ref?: string;
}
/** a call's ΑΔΑΜ, set along the inside of its bubble's top edge */
export interface Arc {
	key: string;
	d: string;
	text: string;
	size: number;
	phase: string | null;
}
export interface Scene {
	mode: NetMode;
	width: number;
	height: number;
	/** the SVG viewBox this scene wants — the packed one crops to its blob */
	view: string;
	/** rendered-width cap in px; the packed blob is round, so full frame
	 *  width would make it 1120px tall */
	maxW?: number;
	marks: Placed[];
	spokes: Seg[];
	bridges: Seg[];
	ties: Tie[];
	groups: PackGroup[];
	arcs: Arc[];
	seasons: { key: string; x0: number; x1: number }[];
	rules: { key: string; x: number }[];
	labels: Label[];
}

/** width of the display face, per px of font size (measured, 5.6px at 9px) */
const W_PER_PX = 0.62;

const CHAR = 5.6; // measured width of the display face at 9px
/** every arrangement draws in the same box, so the frame keeps one height
 *  and the page does not jump when the toggle is used (user, 2026-08-18) */
export const NET_HEIGHT = 400;
const YEAR_LANE = 22; // the row of year labels under the timeline

/**
 * Bridges as drawable segments: one per PAIR of calls (several contractors
 * can bridge the same two), each lifted clear of any bridge already drawn
 * over the same stretch — two dashed lines on one axis read as a single
 * solid rule, which is the opposite of what they mean.
 */
export function bridgeSegments(
	bridges: { a: string; b: string; vat: string; who?: string | null }[],
	at: Map<string, Placed>,
	lift = 3.5
): Seg[] {
	const pairs = new Map<string, { a: string; b: string; vats: string[]; who: string[] }>();
	for (const b of bridges) {
		const k = `${b.a}|${b.b}`;
		const cur = pairs.get(k);
		if (cur) {
			cur.vats.push(b.vat);
			if (b.who) cur.who.push(b.who);
		} else pairs.set(k, { a: b.a, b: b.b, vats: [b.vat], who: b.who ? [b.who] : [] });
	}
	const drawn: { y: number; lo: number; hi: number; up: number }[] = [];
	const out: Seg[] = [];
	for (const [key, p] of pairs) {
		const a = at.get(p.a);
		const b = at.get(p.b);
		if (!a || !b) continue;
		const lo = Math.min(a.x, b.x);
		const hi = Math.max(a.x, b.x);
		const y = (a.y + b.y) / 2;
		const taken = new Set(
			drawn.filter((d) => d.y === y && d.lo < hi && lo < d.hi).map((d) => d.up)
		);
		let up = 0;
		while (taken.has(up)) up += lift;
		drawn.push({ y, lo, hi, up });
		out.push({ key, x1: a.x, y1: a.y - up, x2: b.x, y2: b.y - up, who: p.who, vats: p.vats });
	}
	return out;
}

/** Arrangement "call": the star field, then the two bands, in one frame. */
function callScene(nodes: NetNode[], width: number, copy: BandCopy): Scene {
	const field = layout(nodes, width);
	const at = new Map(field.nodes.map((n) => [n.ref, n]));
	const maxEur = Math.max(...nodes.map((n) => n.eur ?? 0), 1);
	const single = field.lone.filter((n) => n.call);
	const none = field.lone.filter((n) => !n.call);
	const bandOne = band(single, width, 34, 34, 15, maxEur);
	const bandNo = band(none, width, 34, 34, 15, maxEur);

	const labels: Label[] = [];
	const want = new Set(
		[...field.clusters].sort((a, b) => b.eur - a.eur).slice(0, 6).map((c) => c.call)
	);
	const rightOf = new Map<number, number>();
	for (const c of field.clusters) {
		labels.push({ key: `v:${c.call}`, x: c.cx, y: c.bottom, text: copy.eurShort(c.eur), cls: 'val' });
		if (!want.has(c.call)) continue;
		const half = (callText(c.call).length * CHAR) / 2;
		if (c.cx - half < (rightOf.get(c.rowTop) ?? -Infinity) + 8) continue;
		rightOf.set(c.rowTop, c.cx + half);
		labels.push({ key: `a:${c.call}`, x: c.cx, y: c.rowTop - 3, text: callText(c.call), cls: 'adam' });
	}

	const HEAD = 30;
	const yOne = field.height + HEAD;
	const yNo = yOne + bandOne.height + HEAD;
	labels.push(
		{ key: 'b:one', x: 0, y: yOne - 12, text: copy.single, cls: 'band', anchor: 'start' },
		{ key: 'b:no', x: 0, y: yNo - 12, text: copy.none, cls: 'band', anchor: 'start' }
	);

	const height = yNo + bandNo.height;
	return {
		mode: 'call',
		width,
		height,
		view: `-6 -16 ${width + 12} ${height + 26}`,
		marks: [
			...field.nodes,
			...bandOne.nodes.map((n) => ({ ...n, y: n.y + yOne })),
			...bandNo.nodes.map((n) => ({ ...n, y: n.y + yNo }))
		],
		spokes: field.spokes.map((s) => {
			const a = at.get(s.a) as Placed;
			const b = at.get(s.b) as Placed;
			return { key: `${s.a}|${s.b}`, x1: a.x, y1: a.y, x2: b.x, y2: b.y };
		}),
		bridges: bridgeSegments(field.bridges, at),
		ties: [],
		groups: [],
		arcs: [],
		seasons: [],
		rules: [],
		labels
	};
}

/** Arrangement "time": one axis, every contract on it, lots tied. */
function timeScene(nodes: NetNode[], width: number, season?: Season, box = NET_HEIGHT): Scene {
	const t = timeline(nodes, width, { season, height: box - YEAR_LANE });
	// the viewBox is the box exactly — one unit is one rendered pixel at the
	// frame's own width, which is what makes "400 tall" mean 400
	return {
		mode: 'time',
		width,
		height: box,
		view: `0 0 ${width} ${box}`,
		marks: t.nodes,
		spokes: [],
		bridges: [],
		ties: t.ties,
		groups: [],
		arcs: [],
		seasons: t.seasons,
		rules: t.ticks.filter((k) => k.rule).map((k) => ({ key: k.label, x: k.x })),
		labels: t.ticks.map((k) => ({
			key: `y:${k.label}`,
			x: k.x,
			y: t.height + 15,
			text: k.label,
			cls: 'year' as const,
			anchor: 'middle' as const
		}))
	};
}

/** Arrangement "pack": the hierarchy, as nested circles. */
function packScene(nodes: NetNode[], width: number, box: number, copy: BandCopy): Scene {
	const PADDING = 2; // room for the dashed edge of a no-call contract
	const f = packed(nodes, width, box - PADDING * 2);
	const labels: Label[] = [];
	const arcs: Arc[] = [];

	for (const g of f.groups) {
		// the ΑΔΑΜ runs along the inside of the top edge, as a region name
		// does on a packed-circle map; skipped when the arc is too short for
		// it, never shrunk below reading size
		const size = Math.min(13, Math.max(9, g.r * 0.15));
		const rr = g.r - size * 0.72;
		// a 15-character ΑΔΑΜ bent round a small circle is a smudge, not a
		// label: it appears only when the rim is long enough to read along
		if (rr >= 34 && g.key.length * size * W_PER_PX < Math.PI * rr * 0.92)
			arcs.push({
				key: g.key,
				d: `M${(g.x - rr).toFixed(1)} ${g.y.toFixed(1)}A${rr.toFixed(1)} ${rr.toFixed(1)} 0 0 1 ${(g.x + rr).toFixed(1)} ${g.y.toFixed(1)}`,
				text: callText(g.key),
				size,
				phase: g.phase
			});
	}
	// every circle carries its own money when the circle can hold the text
	for (const n of f.nodes) {
		const text = copy.eurTiny(n.eur ?? 0);
		const fit = (1.75 * n.r) / (text.length * W_PER_PX);
		const size = Math.min(16, n.r * 0.42, fit);
		if (size >= 8)
			labels.push({
				key: `l:${n.ref}`,
				x: n.x,
				y: n.y + size * 0.35,
				text,
				cls: 'leaf',
				size,
				ref: n.ref
			});
	}

	// crop to the blob: d3 packs a circle, so a full-frame viewBox would be
	// three quarters white paper
	const all = [...f.groups, ...f.nodes.filter((n) => n.group < 0)];
	const x0 = Math.min(...all.map((g) => g.x - g.r));
	const x1 = Math.max(...all.map((g) => g.x + g.r));
	const y0 = Math.min(...all.map((g) => g.y - g.r));
	const y1 = Math.max(...all.map((g) => g.y + g.r));
	// a square viewBox of exactly the box, centred on the blob, and the
	// rendered width capped to match: a circle is as wide as it is tall, so
	// this is what makes "400 tall" mean 400 rather than "whatever the
	// outermost ring happened to reach"
	const cx = (x0 + x1) / 2;
	const cy = (y0 + y1) / 2;
	return {
		mode: 'pack',
		width: box,
		height: box,
		view: `${cx - box / 2} ${cy - box / 2} ${box} ${box}`,
		maxW: box,
		marks: f.nodes,
		spokes: [],
		bridges: [],
		ties: [],
		groups: f.groups,
		arcs,
		seasons: [],
		rules: [],
		labels
	};
}

export interface BandCopy {
	/** heading for the contracts whose call produced only them */
	single: string;
	/** heading for the contracts with no call at all */
	none: string;
	/** the site's money format, for labels that stand on paper */
	eurShort: (v: number) => string;
	/** the compact one, for labels that must fit inside a mark */
	eurTiny: (v: number) => string;
}

export type Season = { from: string; to: string };

export function scene(
	mode: NetMode,
	nodes: NetNode[],
	width: number,
	copy: BandCopy,
	box = NET_HEIGHT,
	season?: Season
): Scene {
	if (mode === 'call') return callScene(nodes, width, copy);
	if (mode === 'pack') return packScene(nodes, width, box, copy);
	return timeScene(nodes, width, season, box);
}
