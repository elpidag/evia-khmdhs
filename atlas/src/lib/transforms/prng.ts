/** Deterministic PRNG (mulberry32) — every reader sees the same layout. */
export const mulberry32 = (seed: number) => () => {
	seed |= 0;
	seed = (seed + 0x6d2b79f5) | 0;
	let z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
	z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
	return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
};
