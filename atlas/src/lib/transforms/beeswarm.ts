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
