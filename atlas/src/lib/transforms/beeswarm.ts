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
