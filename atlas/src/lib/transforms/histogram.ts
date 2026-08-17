/** Client-side binning that reproduces `webui/queries.py:_bin_values`.
 *
 *  The ΔΑΣΕ value chart draws the SAME contracts two ways — one dot each, or
 *  stacked into value brackets — so both modes are built from the one array
 *  the API ships for the dots. Binning here (rather than shipping a second
 *  per-year histogram) is what guarantees the two modes cannot drift apart.
 *  The convention must match the server's exactly: half-open bins
 *  [e_i, e_{i+1}), anything past the last edge folded into the final bin.
 *  `tests/test_atlas_real_db.py` pins the equality on the live payloads.
 */

/**
 * Pixel x of a value on the bracket axis: its bin's slot, plus its
 * log-interpolated position INSIDE that slot. When every bracket spans one
 * doubling — which `queries_extra.dase_value_histogram` guarantees — this is
 * exactly a logarithmic scale, so the beeswarm and the bars can share it and
 * the median line lands in one place in both. `lo` floors at 1 so the
 * unbounded first bracket (`[0, e1)`) still has a defined interpolation.
 */
export function binPosition(v: number, edges: number[], left: number, bw: number): number {
	for (let i = 0; i < edges.length - 1; i++) {
		if (v >= edges[i] && v < edges[i + 1]) {
			const lo = Math.max(edges[i], 1);
			const frac = Math.log(v / lo) / Math.log(edges[i + 1] / lo);
			return left + (i + frac) * bw;
		}
	}
	// at or past the final edge: the start of the overflow slot
	return left + (edges.length - 1) * bw;
}

/** Index of the bin holding `v`; overflow lands in the last bin. */
export function binIndex(v: number, edges: number[]): number {
	for (let i = 0; i < edges.length - 1; i++) {
		if (v >= edges[i] && v < edges[i + 1]) return i;
	}
	return edges.length - 1;
}

/** Counts per bin — the server's `counts` array. */
export function binCounts(values: number[], edges: number[]): number[] {
	const out = new Array<number>(edges.length).fill(0);
	for (const v of values) out[binIndex(v, edges)]++;
	return out;
}

/**
 * Counts per bin, split by category (here: signature year).
 * Returns one row per bin, each row ordered like `keys`; values whose key is
 * absent from `keys` are counted in the bin total but in no segment, so the
 * caller can render the shortfall honestly rather than silently.
 */
export function binByKey(
	values: number[],
	keys: (string | null)[],
	edges: number[],
	order: string[]
): number[][] {
	const at = new Map(order.map((k, i) => [k, i]));
	const out = Array.from({ length: edges.length }, () => new Array<number>(order.length).fill(0));
	for (let i = 0; i < values.length; i++) {
		const j = at.get(keys[i] ?? '');
		if (j === undefined) continue;
		out[binIndex(values[i], edges)][j]++;
	}
	return out;
}
