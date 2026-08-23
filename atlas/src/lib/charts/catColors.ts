/**
 * The TYPE palette — one colour per curated work-type category, shared by
 * the PROCUREMENT TIMELINE's type lens, the TYPES OF WORKS dots and the
 * chord, so a category keeps one colour across the page.
 *
 * Since 2026-08-23 (user) the colours come in FAMILIES, read top to bottom
 * on the chord's category half: blue for the flood-protection works,
 * amber for the studies, greens for the vegetation works (reforestation
 * darkest, logging a step lighter), and a red ramp for the fire-prevention
 * works — mixed firebreaks the full red, then firefighting water, the
 * fire protection around archaeological sites, and the catch-all special
 * forestry works each a step lighter. `CAT_ORDER` is that reading order.
 */
export const CAT_COLORS: Record<string, string> = {
	anadasoseis: '#2d6a4f',
	ylotomies: '#52b788',
	antidiavrotika: '#0d366b',
	meletes: '#b07d1e',
	miktes_zones: '#b33a1a',
	ydatodexamenes: '#c8715a',
	arxaiologikoi: '#d99c8c',
	dasotexnika: '#ebccc3'
};

/** the categories top to bottom on the chord (user, 2026-08-23, with the
 *  family order chosen so the SHORT names sit at the steep top of the
 *  half and the long ones lower, where a radial label has room — the
 *  greens, then blue, amber, and the red ramp down to the catch-all) */
export const CAT_ORDER = Object.keys(CAT_COLORS);
