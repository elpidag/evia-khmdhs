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
// Since the Theme Lab round (2026-09-03) every value is a LIVE CSS string
// over the tokens — the greens are the two dataset hues, blue/amber/red are
// the --c-cat-* categorical anchors, and the red family's lighter steps are
// paper-fades of the anchor whose percentages reproduce the old hexes
// exactly (#c8715a / #d99c8c / #ebccc3). Canvas or luminance consumers
// resolve through $lib/theme.svelte.
export const CAT_COLORS: Record<string, string> = {
	anadasoseis: 'var(--c-anadohoi)',
	ylotomies: 'var(--c-dase)',
	antidiavrotika: 'var(--c-cat-blue)',
	meletes: 'var(--c-cat-amber)',
	miktes_zones: 'var(--c-cat-red)',
	ydatodexamenes: 'color-mix(in srgb, var(--c-cat-red) 71.9%, var(--paper))',
	arxaiologikoi: 'color-mix(in srgb, var(--c-cat-red) 50%, var(--paper))',
	dasotexnika: 'color-mix(in srgb, var(--c-cat-red) 26%, var(--paper))'
};

/** the categories top to bottom on the chord (user, 2026-08-23, with the
 *  family order chosen so the SHORT names sit at the steep top of the
 *  half and the long ones lower, where a radial label has room — the
 *  greens, then blue, amber, and the red ramp down to the catch-all) */
export const CAT_ORDER = Object.keys(CAT_COLORS);
