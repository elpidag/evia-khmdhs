/**
 * The clock of the story's Figure 04 — how wall time maps onto the three
 * weeks of August 2021 (DATA_DECISIONS 2026-09-02). Pure, so it is pinned
 * by alertsClock.test.ts on the real alerts: the loop's length, every alert
 * firing exactly once and staying readable, the acceleration only where
 * nothing happens.
 *
 * Rules: simulated time runs at `baseMsPerDay` (1.8 s per day); through an
 * IDLE stretch — no alert within the next `lookaheadH` hours and the last
 * alert's dwell over — it runs at `fastMsPerDay`; a firing never comes
 * sooner than `minGapMs` after the previous one (the clock HOLDS on that
 * minute, so the peak days are alert-paced, not clock-paced); each alert is
 * `active` for `dwellMs`, `fading` for `fadeMs`, then `past`; the final state
 * holds `holdMs`, fades `tailFadeMs`, and the loop restarts.
 */
export interface ClockOpts {
	baseMsPerDay: number;
	fastMsPerDay: number;
	dwellMs: number;
	fadeMs: number;
	lookaheadH: number;
	minGapMs: number;
	holdMs: number;
	tailFadeMs: number;
}

export const CLOCK: ClockOpts = {
	baseMsPerDay: 1800,
	fastMsPerDay: 1000,
	dwellMs: 3000,
	fadeMs: 1000,
	lookaheadH: 3,
	minGapMs: 500,
	holdMs: 3000,
	tailFadeMs: 600
};

/** a stretch of wall time with one rate (simulated ms per wall ms; 0 = a hold) */
export interface Segment {
	wall0: number;
	sim0: number;
	rate: number;
}

export type PhaseKind = 'none' | 'active' | 'fading' | 'past';

export interface Clock {
	start: number;
	end: number;
	/** the wall time at which the simulation reaches `end` */
	endWall: number;
	/** endWall + hold + tail fade */
	loopMs: number;
	/** wall time at which alert i fires (the alerts' order) */
	fireWall: number[];
	segments: Segment[];
	/** simulated ms at a wall time inside one loop */
	simAt(wall: number): number;
	/** alert i's state at a wall time; u runs 0→1 through active and fading */
	phaseAt(wall: number, i: number): { kind: PhaseKind; u: number };
}

const DAY = 86_400_000;
const HOUR = 3_600_000;

export function buildClock(
	alerts: { timestamp: string }[],
	opts: ClockOpts = CLOCK,
	start?: number,
	end?: number
): Clock {
	const times = alerts.map((a) => Date.parse(a.timestamp));
	for (let i = 1; i < times.length; i++) {
		if (times[i] < times[i - 1]) throw new Error('alerts must be sorted by time');
	}
	const s = start ?? Math.floor(times[0] / DAY) * DAY;
	const e = end ?? Math.ceil((times[times.length - 1] + 1) / DAY) * DAY;
	const base = DAY / opts.baseMsPerDay;
	const fast = DAY / opts.fastMsPerDay;
	const lookahead = opts.lookaheadH * HOUR;

	const segments: Segment[] = [];
	const fireWall: number[] = [];
	let wall = 0;
	let sim = s;
	let k = 0;
	let lastFire = -Infinity;
	let dwellEnd = 0;
	let guard = 0;
	while (sim < e || k < times.length) {
		if (++guard > 100_000) throw new Error('clock did not converge');
		const tNext = k < times.length ? Math.min(Math.max(times[k], s), e) : e;
		if (k < times.length && sim >= tNext) {
			// fire alert k — after the minimum gap since the previous firing
			if (wall - lastFire < opts.minGapMs) {
				const holdTo = lastFire + opts.minGapMs;
				segments.push({ wall0: wall, sim0: sim, rate: 0 });
				wall = holdTo;
			}
			fireWall.push(wall);
			lastFire = wall;
			dwellEnd = wall + opts.dwellMs;
			k++;
			continue;
		}
		const idle = tNext - sim > lookahead && wall >= dwellEnd;
		const rate = idle ? fast : base;
		let simStop = idle ? tNext - lookahead : tNext;
		if (!idle && wall < dwellEnd) {
			// the dwell may end before the next alert: stop there and re-decide
			simStop = Math.min(simStop, sim + (dwellEnd - wall) * rate);
		}
		if (simStop <= sim) simStop = tNext;
		segments.push({ wall0: wall, sim0: sim, rate });
		wall += (simStop - sim) / rate;
		sim = simStop;
	}
	// the window ends only once the last alert has dwelt and faded, so the
	// final state — every alert past — is genuinely final
	const settle = lastFire + opts.dwellMs + opts.fadeMs;
	if (wall < settle) {
		segments.push({ wall0: wall, sim0: e, rate: 0 });
		wall = settle;
	}
	const endWall = wall;
	const loopMs = endWall + opts.holdMs + opts.tailFadeMs;

	function simAt(w: number): number {
		if (w <= 0) return s;
		if (w >= endWall) return e;
		let lo = 0;
		let hi = segments.length - 1;
		while (lo < hi) {
			const mid = (lo + hi + 1) >> 1;
			if (segments[mid].wall0 <= w) lo = mid;
			else hi = mid - 1;
		}
		const seg = segments[lo];
		return Math.min(e, seg.sim0 + (w - seg.wall0) * seg.rate);
	}

	function phaseAt(w: number, i: number): { kind: PhaseKind; u: number } {
		const f = fireWall[i];
		if (w < f) return { kind: 'none', u: 0 };
		if (w < f + opts.dwellMs) return { kind: 'active', u: (w - f) / opts.dwellMs };
		if (w < f + opts.dwellMs + opts.fadeMs) {
			return { kind: 'fading', u: (w - f - opts.dwellMs) / opts.fadeMs };
		}
		return { kind: 'past', u: 1 };
	}

	return { start: s, end: e, endWall, loopMs, fireWall, segments, simAt, phaseAt };
}

/** where a wall clock stands inside the loop: the wall time to draw (held at
 *  endWall through the hold and the fade) and the tail fade's 0→1 */
export function loopPhase(wallMs: number, c: Clock, opts: ClockOpts = CLOCK): { wall: number; tail: number } {
	const w = ((wallMs % c.loopMs) + c.loopMs) % c.loopMs;
	if (w <= c.endWall) return { wall: w, tail: 0 };
	const past = w - c.endWall - opts.holdMs;
	return { wall: c.endWall, tail: past <= 0 ? 0 : Math.min(1, past / opts.tailFadeMs) };
}

/** the index of the last burn day whose Athens midnight is ≤ the simulated
 *  time, or -1 before the first; `days` are ISO dates in order */
export function burnDayIndex(simMs: number, days: string[]): number {
	let i = -1;
	for (let k = 0; k < days.length; k++) {
		if (Date.parse(`${days[k]}T00:00:00+03:00`) <= simMs) i = k;
		else break;
	}
	return i;
}
