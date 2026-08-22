/**
 * Deterministic layout for the Anti-nero contract network.
 *
 * No force simulation: a simulation gives a different picture on every
 * load, cannot be pinned by a test, and at 245 nodes degenerates into a
 * blob. Everything here is a pure function of the input, so the same data
 * always draws the same field.
 *
 * Edges are ACTS, never attributes (DATA_DECISIONS 2026-08-18): the call a
 * contract was awarded under, and the contractor that won it. Linking by
 * contracting authority would collapse 237 of 245 contracts into one
 * component — the framework lots each name 5-14 Δασαρχεία — and linking by
 * Π.Ε. collapses all 245, because sharing a region is a coordinate, not a
 * relationship.
 *
 * The drawn unit is the CALL: one star per πρόσκληση that produced more
 * than one contract, biggest lot at the centre, the siblings around it on
 * spokes long enough to be seen. Calls sharing a contractor are placed
 * next to each other (their connected component) and linked by a dashed
 * bridge, so the one relation that crosses a procurement family reads as a
 * short local line instead of a wire across the page.
 */
import { packEnclose, packSiblings } from 'd3-hierarchy';

import { dodgeChains } from './beeswarm';

export interface NetNode {
	ref: string;
	eur: number | null;
	call?: string | null;
	vat?: string | null;
	who?: string | null;
	pe?: string | null;
	auth?: string | null;
	cat?: string | null;
	phase?: string | null;
	/** deliverables kind — works / study_and_works / study — the colour
	 *  since 2026-08-22 (phases are funding envelopes and say little) */
	dk?: string | null;
	/** the call is known by DATE ONLY (ΤΑΙΠΕΔ, no ΚΗΜΔΗΣ record) */
	udc?: boolean;
	/** signature date, ISO — the timeline arrangement's x */
	d?: string | null;
	title?: string | null;
}
export interface Placed extends NetNode {
	x: number;
	y: number;
	r: number;
	group: number;
	hub: boolean;
}
export interface Edge {
	a: string;
	b: string;
	kind: 'call' | 'contractor';
}
/** hub → sibling, inside one call */
export interface Spoke {
	a: string;
	b: string;
}
/** hub ↔ hub, two calls won by the same contractor */
export interface Bridge {
	a: string;
	b: string;
	vat: string;
	who?: string | null;
}
export interface Cluster {
	call: string;
	group: number;
	members: Placed[];
	hub: Placed;
	eur: number;
	cx: number;
	cy: number;
	top: number;
	rowTop: number;
	bottom: number;
	half: number;
}
export interface Field {
	clusters: Cluster[];
	nodes: Placed[];
	spokes: Spoke[];
	bridges: Bridge[];
	lone: NetNode[];
	width: number;
	height: number;
}

const push = <T>(m: Map<string, T[]>, k: string, v: T) => {
	const cur = m.get(k);
	if (cur) cur.push(v);
	else m.set(k, [v]);
};

/** Contracts sharing a call, and contracts sharing a contractor. */
export function edgesOf(nodes: NetNode[]): Edge[] {
	const out: Edge[] = [];
	const keys: [keyof NetNode, Edge['kind']][] = [
		['call', 'call'],
		['vat', 'contractor']
	];
	for (const [key, kind] of keys) {
		const by = new Map<string, string[]>();
		for (const n of nodes) {
			const k = n[key];
			if (typeof k === 'string' && k) push(by, k, n.ref);
		}
		for (const refs of by.values()) {
			// a star inside each group keeps the edge count linear (n-1), so
			// 245 contracts stay well inside the SVG mark budget
			for (let i = 1; i < refs.length; i++) out.push({ a: refs[0], b: refs[i], kind });
		}
	}
	return out;
}

/** Connected components over those edges — the clusters the field shows. */
export function componentsOf(nodes: NetNode[], edges: Edge[]): Map<string, number> {
	const parent = new Map<string, string>(nodes.map((n) => [n.ref, n.ref]));
	const find = (x: string): string => {
		let r = x;
		while (parent.get(r) !== r) r = parent.get(r) as string;
		return r;
	};
	for (const e of edges) {
		const ra = find(e.a);
		const rb = find(e.b);
		if (ra !== rb) parent.set(ra, rb);
	}
	const ids = new Map<string, number>();
	const label = new Map<string, number>();
	for (const n of nodes) {
		const root = find(n.ref);
		if (!ids.has(root)) ids.set(root, ids.size);
		label.set(n.ref, ids.get(root) as number);
	}
	return label;
}

const byEur = (a: NetNode, b: NetNode) => (b.eur ?? 0) - (a.eur ?? 0) || a.ref.localeCompare(b.ref);

/**
 * One star per multi-lot call, shelf-packed left to right. Contracts whose
 * call produced nothing else — and direct awards, which publish no call at
 * all — are returned untouched as `lone`: they belong in a band, not in a
 * field of one-node "clusters" that would take three quarters of the ink
 * to say the same thing 110 times.
 */
export function layout(nodes: NetNode[], width = 1120, maxR = 15, spoke = 15): Field {
	const byCall = new Map<string, NetNode[]>();
	for (const n of nodes) if (n.call) push(byCall, n.call, n);
	const lone = nodes.filter((n) => !n.call || (byCall.get(n.call) as NetNode[]).length < 2);
	const drawn = nodes.filter((n) => n.call && (byCall.get(n.call) as NetNode[]).length > 1);

	const max = Math.max(...nodes.map((n) => n.eur ?? 0), 1);
	// area ∝ €, the same convention as the ΔΑΣΕ map
	const rOf = (v: number | null | undefined) => Math.max(2.6, Math.sqrt((v ?? 0) / max) * maxR);

	// calls held together by a shared contractor land in one component, and
	// are therefore packed side by side
	const comp = componentsOf(drawn, edgesOf(drawn));
	const calls = [...byCall.entries()]
		.filter(([, m]) => m.length > 1)
		.map(([call, members]) => {
			const sorted = [...members].sort(byEur);
			return {
				call,
				members: sorted,
				group: comp.get(sorted[0].ref) as number,
				eur: sorted.reduce((s, m) => s + (m.eur ?? 0), 0)
			};
		});
	const groupEur = new Map<number, number>();
	for (const c of calls) groupEur.set(c.group, (groupEur.get(c.group) ?? 0) + c.eur);
	calls.sort(
		(a, b) =>
			(groupEur.get(b.group) as number) - (groupEur.get(a.group) as number) ||
			a.group - b.group ||
			b.eur - a.eur ||
			a.call.localeCompare(b.call)
	);

	// two passes: assign cells to rows, then place each row's cells on one
	// vertical centre line, so a row of mixed sizes shares a baseline and the
	// € labels below the stars line up instead of stepping up and down
	const cells = calls.map((cl) => {
		const rHead = rOf(cl.members[0].eur);
		const rRest = cl.members.slice(1).map((m) => rOf(m.eur));
		const orbit = rHead + Math.max(...rRest) + spoke;
		const half = orbit + Math.max(...rRest);
		return { cl, rHead, rRest, orbit, half, size: half * 2 + 18 };
	});
	// wrap on COMPONENT boundaries: calls tied by a shared contractor are
	// packed as one block, so every bridge stays a short line inside a row
	// instead of a wire sweeping diagonally across the whole chart
	const blocks: (typeof cells)[] = [];
	for (const c of cells) {
		const last = blocks[blocks.length - 1];
		if (last && last[0].cl.group === c.cl.group) last.push(c);
		else blocks.push([c]);
	}
	const rows: (typeof cells)[] = [];
	let row: typeof cells = [];
	let used = 0;
	for (const blk of blocks) {
		const w = blk.reduce((t, c) => t + c.size, 0);
		if (used + w > width && row.length) {
			rows.push(row);
			row = [];
			used = 0;
		}
		for (const c of blk) {
			// a component wider than the frame is the only case that splits
			if (used + c.size > width && row.length) {
				rows.push(row);
				row = [];
				used = 0;
			}
			row.push(c);
			used += c.size;
		}
	}
	if (row.length) rows.push(row);

	const placed: Placed[] = [];
	const spokes: Spoke[] = [];
	const clusters: Cluster[] = [];
	const LABEL = 20; // the € lane under a row, and the ΑΔΑΜ lane above the next
	let y = 0;
	for (const r of rows) {
		const rowH = Math.max(...r.map((c) => c.size));
		let x = 0;
		for (const c of r) {
			const [head, ...rest] = c.cl.members;
			const cx = x + c.size / 2;
			const cy = y + rowH / 2;
			const hub: Placed = { ...head, x: cx, y: cy, r: c.rHead, group: c.cl.group, hub: true };
			const members = [hub];
			placed.push(hub);
			rest.forEach((m, i) => {
				// start at 12 o'clock and go round; a 2-lot call therefore always
				// draws its sibling straight above the hub
				const a = -Math.PI / 2 + (i / rest.length) * Math.PI * 2;
				const p: Placed = {
					...m,
					x: cx + Math.cos(a) * c.orbit,
					y: cy + Math.sin(a) * c.orbit,
					r: c.rRest[i],
					group: c.cl.group,
					hub: false
				};
				placed.push(p);
				members.push(p);
				spokes.push({ a: head.ref, b: m.ref });
			});
			clusters.push({
				call: c.cl.call,
				group: c.cl.group,
				members,
				hub,
				eur: c.cl.eur,
				cx,
				cy,
				half: c.half,
				top: cy - c.half,
				rowTop: y,
				bottom: y + rowH - 3 // the row's shared label baseline
			});
			x += c.size;
		}
		y += rowH + LABEL;
	}

	// one dashed line per contractor holding lots under several drawn calls,
	// chained in placement order so the count stays linear and the lines short
	const hubOf = new Map(clusters.map((c) => [c.call, c.hub.ref]));
	const seatOf = new Map(clusters.map((c, i) => [c.call, i]));
	const byVat = new Map<string, NetNode[]>();
	for (const n of drawn) if (n.vat) push(byVat, n.vat, n);
	const bridges: Bridge[] = [];
	for (const [vat, holders] of [...byVat.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
		const seats = [...new Set(holders.map((h) => h.call as string))].sort(
			(a, b) => (seatOf.get(a) as number) - (seatOf.get(b) as number)
		);
		for (let i = 1; i < seats.length; i++)
			bridges.push({
				a: hubOf.get(seats[i - 1]) as string,
				b: hubOf.get(seats[i]) as string,
				vat,
				who: holders[0].who
			});
	}

	return {
		clusters,
		nodes: placed,
		spokes,
		bridges,
		lone: [...lone].sort(byEur),
		width,
		height: y
	};
}

/** The lone contracts as a compact ranked band, on the field's own scale
 * (pass the field's max €), so a big direct award still reads as big. */
export function band(
	nodes: NetNode[],
	width = 1120,
	perRow = 34,
	rowH = 34,
	maxR = 15,
	max?: number
): { nodes: Placed[]; height: number } {
	const top = max ?? Math.max(...nodes.map((n) => n.eur ?? 0), 1);
	const step = width / perRow;
	const placed = [...nodes].sort(byEur).map((n, i) => ({
		...n,
		x: (i % perRow) * step + step / 2,
		y: Math.floor(i / perRow) * rowH + rowH / 2,
		r: Math.max(2.6, Math.min(maxR, Math.sqrt((n.eur ?? 0) / top) * maxR)),
		group: -1,
		hub: false
	}));
	return { nodes: placed, height: Math.ceil(nodes.length / perRow) * rowH };
}

/* ------------------------------------------------------------------ *
 * Arrangements.
 *
 * One mark per contract in every one of them — a circle whose AREA is the
 * stated net € and whose colour is the programme phase — so the toggle
 * rearranges the same population instead of swapping in a different chart.
 * What changes is what POSITION means: nothing in the star field (it means
 * "packed into a row"), the signature date on the timeline, containment in
 * the packed hierarchy.
 * ------------------------------------------------------------------ */

const radiusScale = (nodes: NetNode[], minR = 2.2) => {
	const max = Math.max(...nodes.map((n) => n.eur ?? 0), 1);
	return (v: number | null | undefined, maxR: number) =>
		Math.max(minR, Math.sqrt((v ?? 0) / max) * maxR);
};

export interface Tie {
	call: string;
	pts: { x: number; y: number }[];
}
export interface TimeField {
	nodes: Placed[];
	ties: Tie[];
	ticks: { x: number; label: string; rule: boolean }[];
	/** the fire-season stripes, one per year the domain touches */
	seasons: { key: string; x0: number; x1: number }[];
	x0: number;
	x1: number;
	mid: number;
	height: number;
}
export interface TimeOpts {
	maxR?: number;
	pad?: number;
	minHeight?: number;
	/** exact plot height; the dots are shrunk to fit rather than spilling */
	height?: number;
	/** «MM-DD» bounds of the season to shade; ships from the API together
	 *  with the count the chart prints, so the two cannot drift apart */
	season?: { from: string; to: string };
}

/**
 * Arrangement A — by signature date. x is when the contract was signed, y is
 * a dodge (a beeswarm packs, it does not encode). Lots of the same call are
 * joined by a tie: because most split calls signed every lot on one day,
 * a tie usually draws as one vertical stroke, which is the finding.
 */
export function timeline(nodes: NetNode[], width = 1120, opts: TimeOpts = {}): TimeField {
	const { maxR = 13, pad = 26, minHeight = 300, height: fixed, season } = opts;
	const rOf = radiusScale(nodes);
	// sorted before placing, so the dodge's tie-breaks depend on the DATA and
	// not on the order the API happened to return the rows in
	const dated = nodes
		.filter((n) => n.d)
		.sort((a, b) => (a.d as string).localeCompare(b.d as string) || byEur(a, b));
	const ts = dated.map((n) => Date.parse(n.d as string));
	// the axis starts on 1 January of the first year, so every year label
	// sits ON its own new-year rule (user, 2026-08-22)
	const t0 = Date.UTC(new Date(Math.min(...ts)).getUTCFullYear(), 0, 1);
	const t1 = Math.max(...ts);
	const x0 = pad;
	const x1 = width - pad;
	const xOf = (t: number) => x0 + ((t - t0) / Math.max(1, t1 - t0)) * (x1 - x0);
	const xs = dated.map((_, i) => xOf(ts[i]));

	// The swarm's own height is whatever the densest day needs. When the
	// caller fixes the box (the page does, so the frame keeps one height
	// whichever arrangement is showing), the DOTS shrink to fit — a dodge
	// that overflows its box would just overplot, which is the one thing a
	// beeswarm exists to avoid. Area ∝ € still holds: the scale is uniform.
	// lots of one call signed together are a RIGID touching run (user,
	// 2026-08-22): dodged one by one they interleave with strangers and
	// the join line zig-zags illegibly across the swarm. "Together" is a
	// ≤7-day window — 23PROC012860295 signed four lots on 07.07 and one on
	// 06.07, a sub-pixel day that must not exile the fifth — and a member
	// keeps its true x, so a day-apart lot joins the run on a slant.
	const CHAIN_WINDOW = 7 * 86_400_000;
	const chains: number[][] = [];
	{
		const last = new Map<string, { ci: number; t: number }>();
		dated.forEach((n, i) => {
			const prev = n.call ? last.get(n.call) : undefined;
			if (prev && ts[i] - prev.t <= CHAIN_WINDOW) {
				chains[prev.ci].push(i);
				prev.t = ts[i];
			} else {
				if (n.call) last.set(n.call, { ci: chains.length, t: ts[i] });
				chains.push([i]);
			}
		});
	}
	const place = (rr: number[]) => {
		const per = dodgeChains(
			chains.map((m) => ({ xs: m.map((i) => xs[i]), rs: m.map((i) => rr[i]) }))
		);
		const out = new Array<number>(dated.length).fill(0);
		chains.forEach((m, c) => m.forEach((i, k) => (out[i] = per[c][k])));
		return out;
	};
	let scale = 1;
	let rs = dated.map((n) => rOf(n.eur, maxR));
	let ys = place(rs);
	let half = Math.max(...ys.map((y, i) => Math.abs(y) + rs[i]), 0);
	if (fixed) {
		for (let i = 0; i < 6 && half * 2 + 16 > fixed; i++) {
			scale *= Math.max(0.5, (fixed - 16) / (half * 2));
			rs = dated.map((n) => rOf(n.eur, maxR * scale));
			ys = place(rs);
			half = Math.max(...ys.map((y, i) => Math.abs(y) + rs[i]), 0);
		}
	}
	const height = fixed ?? Math.max(minHeight, half * 2 + 16);
	const mid = height / 2;

	const placed: Placed[] = dated.map((n, i) => ({
		...n,
		x: xs[i],
		y: mid + ys[i],
		r: rs[i],
		group: 0,
		hub: false
	}));

	const byCall = new Map<string, Placed[]>();
	for (const p of placed) if (p.call) push(byCall, p.call, p);
	const ties: Tie[] = [...byCall.entries()]
		.filter(([, m]) => m.length > 1)
		.sort((a, b) => a[0].localeCompare(b[0]))
		.map(([call, m]) => ({
			call,
			pts: [...m].sort((p, q) => p.x - q.x || p.y - q.y).map((p) => ({ x: p.x, y: p.y }))
		}));

	// one rule per 1 January inside the domain, its year label ON it —
	// the domain starts on a 1 January by construction, so every year has
	// its rule (user, 2026-08-22)
	const ticks: { x: number; label: string; rule: boolean }[] = [];
	for (let y = new Date(t0).getUTCFullYear(); y <= new Date(t1).getUTCFullYear(); y++) {
		const t = Date.UTC(y, 0, 1);
		if (t >= t0 && t <= t1) ticks.push({ x: xOf(t), label: String(y), rule: true });
	}
	// one shaded stripe per year of the season, clipped to the domain
	const seasons: { key: string; x0: number; x1: number }[] = [];
	if (season) {
		for (let y = new Date(t0).getUTCFullYear(); y <= new Date(t1).getUTCFullYear(); y++) {
			const a = Date.parse(`${y}-${season.from}`);
			const b = Date.parse(`${y}-${season.to}`) + 86_400_000 - 1; // inclusive
			if (b < t0 || a > t1) continue;
			seasons.push({
				key: `s${y}`,
				x0: xOf(Math.max(a, t0)),
				x1: xOf(Math.min(b, t1))
			});
		}
	}
	return { nodes: placed, ties, ticks, seasons, x0, x1, mid, height };
}

export interface PackGroup {
	key: string;
	label: string;
	/** the programme phase all its lots share, or null if they differ */
	phase: string | null;
	x: number;
	y: number;
	r: number;
	eur: number;
	n: number;
}
export interface PackField {
	nodes: Placed[];
	groups: PackGroup[];
	width: number;
	height: number;
}

/**
 * Arrangement B — the hierarchy, packed. A bubble per call that produced
 * LOTS, holding its contracts; every contract that was bought on its own
 * is a bare circle beside them.
 *
 * The order matters and is the point: d3 places siblings in array order,
 * outwards from the first, so the grouped procurements are listed first and
 * take the centre while the solitary contracts ring them. Bucketing the
 * solitary ones into one big parent (the first attempt) drew a giant circle
 * in the middle that read as a single enormous call.
 */
export function packInput(nodes: NetNode[]): PackDatum {
	const byCall = new Map<string, NetNode[]>();
	for (const n of nodes) if (n.call) push(byCall, n.call, n);
	const sumOf = (m: NetNode[]) => m.reduce((s, x) => s + (x.eur ?? 0), 0);
	const groups: PackDatum[] = [...byCall.entries()]
		.filter(([, m]) => m.length > 1)
		.sort((a, b) => sumOf(b[1]) - sumOf(a[1]) || a[0].localeCompare(b[0]))
		.map(([call, members]) => {
			const phases = new Set(members.map((m) => m.phase ?? ''));
			return {
				key: call,
				kind: 'call' as const,
				label: call,
				phase: phases.size === 1 ? [...phases][0] : null,
				children: [...members].sort(byEur)
			};
		});
	const solo: PackDatum[] = nodes
		.filter((n) => !n.call || (byCall.get(n.call) as NetNode[]).length === 1)
		.sort(byEur)
		.map((n) => ({ ...n, kind: n.call ? ('solo' as const) : ('nocall' as const) }));
	return { key: '_root', label: 'programme', children: [...groups, ...solo] };
}

export type PackDatum = Partial<NetNode> & {
	key?: string;
	kind?: 'call' | 'solo' | 'nocall';
	label?: string;
	phase?: string | null;
	children?: PackDatum[];
};

/**
 * Arrangement B, laid out. Two levels of `packSiblings`, not `d3.pack`:
 *
 *   1. each call's lots are packed into a bubble, and every bubble into a
 *      CORE — so the split procurements hold the middle of the picture;
 *   2. the core is then packed as the FIRST sibling among the contracts
 *      bought on their own, which therefore ring it.
 *
 * d3.pack sorts by value and would put the biggest thing in the middle
 * whatever it was; here the middle means something — «bought together».
 * Radii are √€ throughout and scaled once at the end, so area ∝ € holds
 * across both levels and against the other arrangements.
 */
const PAD = 1.035; // relative slack, so packing gaps survive the rescale
// a call bubble is drawn wider than the lots it encloses, leaving a rim of
// its own colour — that rim is what carries the ΑΔΑΜ and what makes the
// bubble read as one procurement rather than as three touching circles
const RIM = 1.12;

export function packed(nodes: NetNode[], width = 1120, height = 620): PackField {
	const input = packInput(nodes).children ?? [];
	// area ∝ € exactly — no radius floor, or the smallest lots would read
	// bigger than they are; €1 is the value floor, which nothing hits
	const rOf = (v: number | null | undefined) => Math.sqrt(Math.max(1, v ?? 0));

	type Cell = { d: PackDatum; r: number; x: number; y: number; kids: Circle[] };
	type Circle = { d: PackDatum; r: number; x: number; y: number };

	const cells: Cell[] = input.map((d) => {
		if (!d.children) return { d, r: rOf(d.eur), x: 0, y: 0, kids: [] };
		const kids: Circle[] = d.children.map((k) => ({ d: k, r: rOf(k.eur) * PAD, x: 0, y: 0 }));
		packSiblings(kids);
		const e = packEnclose(kids) as { x: number; y: number; r: number };
		// re-centre the lots on their bubble's own centre
		for (const k of kids) {
			k.x -= e.x;
			k.y -= e.y;
		}
		return { d, r: e.r * RIM, x: 0, y: 0, kids };
	});

	const groups = cells.filter((c) => c.kids.length);
	const solos = cells.filter((c) => !c.kids.length);
	packSiblings(groups);
	const core = packEnclose(groups) as { x: number; y: number; r: number };
	for (const g of groups) {
		g.x -= core.x;
		g.y -= core.y;
	}
	// the core rides along as one circle so the solitary contracts ring it
	const ring: Circle[] = [
		{ d: { key: '_core' }, r: core.r * PAD, x: 0, y: 0 },
		...solos.map((c) => ({ d: c.d, r: c.r * PAD, x: 0, y: 0 }))
	];
	packSiblings(ring);
	const [coreSeat, ...soloSeats] = ring;
	solos.forEach((c, i) => {
		c.x = soloSeats[i].x;
		c.y = soloSeats[i].y;
	});
	for (const g of groups) {
		g.x += coreSeat.x;
		g.y += coreSeat.y;
	}

	// one scale for everything, then centre in the box
	const all = packEnclose(ring) as { x: number; y: number; r: number };
	const s = Math.min(width, height) / (all.r * 2);
	const cx = width / 2 - all.x * s;
	const cy = height / 2 - all.y * s;
	const at = (v: number, o: number) => v * s + o;

	const outGroups: PackGroup[] = [];
	const marks: Placed[] = [];
	for (const c of cells) {
		if (!c.kids.length) {
			marks.push({
				...(c.d as NetNode),
				x: at(c.x, cx),
				y: at(c.y, cy),
				r: c.r * s,
				group: -1,
				hub: false
			});
			continue;
		}
		outGroups.push({
			key: c.d.key ?? '',
			label: c.d.label ?? '',
			phase: c.d.phase ?? null,
			x: at(c.x, cx),
			y: at(c.y, cy),
			r: c.r * s,
			eur: (c.d.children ?? []).reduce((t, k) => t + (k.eur ?? 0), 0),
			n: c.kids.length
		});
		for (const k of c.kids)
			marks.push({
				...(k.d as NetNode),
				x: at(c.x + k.x, cx),
				y: at(c.y + k.y, cy),
				r: (k.r / PAD) * s,
				group: outGroups.length - 1,
				hub: false
			});
	}
	return { nodes: marks, groups: outGroups, width, height };
}
