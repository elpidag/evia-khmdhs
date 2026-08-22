/**
 * Beeswarm dodge: given x positions (px) and a dot radius, assign each dot
 * the y offset (px, ± around 0) closest to the centreline that avoids
 * overlap. Deterministic, O(n·k) over nearby placed dots.
 */
export function dodge(xs: number[], radius: number): number[] {
	const r2 = (radius * 2) ** 2;
	const order = xs.map((x, i) => i).sort((a, b) => xs[a] - xs[b]);
	const ys = new Array<number>(xs.length).fill(0);
	const placedX: number[] = [];
	const placedY: number[] = [];

	for (const i of order) {
		const x = xs[i];
		// candidate ys: 0, then just above/below each nearby dot
		const nearby: number[] = [];
		for (let j = placedX.length - 1; j >= 0; j--) {
			if (x - placedX[j] > radius * 2) break;
			nearby.push(j);
		}
		let best = Infinity;
		const candidates = [0];
		for (const j of nearby) {
			const dx2 = (x - placedX[j]) ** 2;
			const dy = Math.sqrt(Math.max(0, r2 - dx2)) + 1e-6;
			candidates.push(placedY[j] + dy, placedY[j] - dy);
		}
		candidate: for (const y of candidates.sort((a, b) => Math.abs(a) - Math.abs(b))) {
			for (const j of nearby) {
				if ((x - placedX[j]) ** 2 + (y - placedY[j]) ** 2 < r2 - 1e-9) {
					continue candidate;
				}
			}
			best = y;
			break;
		}
		ys[i] = best === Infinity ? 0 : best;
		placedX.push(x);
		placedY.push(ys[i]);
	}
	return ys;
}

/**
 * The same dodge with a radius PER DOT — needed when the mark also encodes
 * a value by area, as on the programme network's timeline arrangement. Two
 * dots collide when their centres are closer than the SUM of their radii,
 * which is the only change from `dodge` above; the fixed-radius version
 * stays, because it is cheaper and every existing caller uses it.
 */
export function dodgeVariable(xs: number[], rs: number[], pad = 1): number[] {
	const order = xs.map((x, i) => i).sort((a, b) => xs[a] - xs[b] || a - b);
	const ys = new Array<number>(xs.length).fill(0);
	const placed: number[] = []; // indices, in x order
	const maxR = Math.max(...rs, 0);

	for (const i of order) {
		const x = xs[i];
		const ri = rs[i];
		const nearby: number[] = [];
		for (let k = placed.length - 1; k >= 0; k--) {
			const j = placed[k];
			// nothing further left can reach this dot any more
			if (x - xs[j] > ri + maxR + pad) break;
			nearby.push(j);
		}
		const candidates = [0];
		for (const j of nearby) {
			const reach = ri + rs[j] + pad;
			const dx2 = (x - xs[j]) ** 2;
			if (dx2 >= reach * reach) continue;
			const dy = Math.sqrt(reach * reach - dx2) + 1e-6;
			candidates.push(ys[j] + dy, ys[j] - dy);
		}
		let best = 0;
		candidate: for (const y of candidates.sort((a, b) => Math.abs(a) - Math.abs(b))) {
			for (const j of nearby) {
				const reach = ri + rs[j] + pad;
				if ((x - xs[j]) ** 2 + (y - ys[j]) ** 2 < reach * reach - 1e-9) continue candidate;
			}
			best = y;
			break;
		}
		ys[i] = best;
		placed.push(i);
	}
	return ys;
}

export interface Chain {
	/** per-member x — lots signed a day or two apart keep their true date
	 *  and the run slants to reach them */
	xs: number[];
	/** member radii in draw order, top to bottom of the run */
	rs: number[];
}

/**
 * Dodge for RIGID vertical runs of touching circles: a chain keeps its
 * internal offsets (each member touching the next) and the run as a whole
 * takes the y closest to the centreline that avoids overlap. A single
 * circle is a chain of one, so this generalises `dodgeVariable` — which
 * stays, because it is cheaper and its callers don't group. Exists because
 * same-day lots of one call must sit ADJACENT (user, 2026-08-22): dodged
 * one by one they interleave with strangers and the join line zig-zags
 * illegibly across the swarm.
 */
export function dodgeChains(chains: Chain[], pad = 1): number[][] {
	// internal offsets: each member TOUCHES the previous one given their
	// horizontal gap (same-day lots stack straight, a day-apart lot joins
	// on a slant), centred on the run's own extent
	const offs = chains.map((c) => {
		const o: number[] = [0];
		for (let k = 1; k < c.rs.length; k++) {
			const dx = c.xs[k] - c.xs[k - 1];
			const reach = c.rs[k - 1] + c.rs[k];
			o.push(o[k - 1] + Math.sqrt(Math.max(0, reach * reach - dx * dx)));
		}
		const mid = (o[0] - c.rs[0] + o[o.length - 1] + c.rs[c.rs.length - 1]) / 2;
		return o.map((v) => v - mid);
	});
	const order = chains.map((_, i) => i).sort((a, b) => chains[a].xs[0] - chains[b].xs[0] || a - b);
	const out: number[][] = new Array(chains.length);
	const px: number[] = []; // every already-placed CIRCLE, flat, in x order
	const py: number[] = [];
	const pr: number[] = [];
	const maxR = Math.max(...chains.flatMap((c) => c.rs), 0);

	for (const ci of order) {
		const { xs, rs } = chains[ci];
		const dys = offs[ci];
		const rMax = Math.max(...rs);
		const xMin = Math.min(...xs);
		const nearby: number[] = [];
		for (let j = px.length - 1; j >= 0; j--) {
			if (xMin - px[j] > rMax + maxR + pad + 16) break;
			nearby.push(j);
		}
		const candidates = [0];
		for (const j of nearby)
			for (let k = 0; k < rs.length; k++) {
				const reach = rs[k] + pr[j] + pad;
				const dx2 = (xs[k] - px[j]) ** 2;
				if (dx2 >= reach * reach) continue;
				const dy = Math.sqrt(reach * reach - dx2) + 1e-6;
				candidates.push(py[j] + dy - dys[k], py[j] - dy - dys[k]);
			}
		let best = 0;
		candidate: for (const y of candidates.sort((a, b) => Math.abs(a) - Math.abs(b))) {
			for (const j of nearby)
				for (let k = 0; k < rs.length; k++) {
					const reach = rs[k] + pr[j] + pad;
					if ((xs[k] - px[j]) ** 2 + (y + dys[k] - py[j]) ** 2 < reach * reach - 1e-9)
						continue candidate;
				}
			best = y;
			break;
		}
		out[ci] = dys.map((d) => best + d);
		for (let k = 0; k < rs.length; k++) {
			px.push(xs[k]);
			py.push(best + dys[k]);
			pr.push(rs[k]);
		}
	}
	return out;
}
