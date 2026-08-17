/**
 * How an EXCLUDED contract is labelled.
 *
 * Three different things leave the calculations through the same mechanism —
 * `cancelled = 1` — and the registry itself only ever means the first:
 *
 *  1. a real registry cancellation (`cancelled` came from ΚΗΜΔΗΣ),
 *  2. a curated double-posting: the same signed document uploaded twice
 *     (`duplicate_of` names the counted twin),
 *  3. a contract whose signed PDF names no qualifying party — valid,
 *     uncancelled, simply not this dataset's (`related_to` names the
 *     in-scope sibling of the same procurement, '' when there is none;
 *     DATA_DECISIONS 2026-08-17).
 *
 * Printing «cancelled» over 2 or 3 tells the reader the contract was
 * withdrawn, which it was not — so the label must name the actual reason.
 */
export interface Excludable {
	cancelled: number;
	duplicate_of?: string | null;
	related_to?: string | null;
}

/** `related_to` present (the empty string included) = case 3 above. */
export const isOutOfScope = (c: { related_to?: string | null }): boolean =>
	c.related_to !== null && c.related_to !== undefined;

/**
 * Chip for an excluded row: the text, plus whether it reads as a warning.
 * A cancellation and a double-posting ARE warnings — something went wrong,
 * in the procurement or in the registry. Being another dataset's contract
 * is not: nothing is wrong with 25SYMV016837212, it is simply not a
 * co-op's, so its chip stays neutral.
 */
export function trailChip(t: Excludable): { chip?: string; chipBad?: boolean } {
	if (isOutOfScope(t)) return { chip: 'outside the dataset', chipBad: false };
	if (t.duplicate_of) return { chip: 'duplicate posting' };
	return t.cancelled === 1 ? { chip: 'cancelled' } : {};
}
