/**
 * The frame the user chose for the dataset cards' maps with the picker
 * (2026-08-27, «bounds: [[18.2336, 34.7812], [28.7256, 41.9096]] · k
 * 0.979»): the visible lon/lat box itself, so it is framed with no
 * padding — Corfu to Rhodes, Thrace to Crete, Kastellorizo left out by
 * decision. One constant, so every card map frames the country alike.
 */
export const CARD_BOUNDS: [[number, number], [number, number]] = [
	[18.2336, 34.7812],
	[28.7256, 41.9096]
];
