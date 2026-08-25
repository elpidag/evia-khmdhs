/**
 * English display names for the 74 canonical Π.Ε. (DATA_DECISIONS
 * 2026-08-15). The JSON is a byte-identical copy of the curated
 * khmdhs/data/pe_names_en.json (pinned by tests/test_pe_names_en.py).
 * Presentation only: every key, aggregate and permalink stays on the
 * Greek canonical «Π.Ε. …» strings.
 */
import raw from '$lib/data/pe_names_en.json';

const EN: Record<string, string> = {};
for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
	if (!k.startsWith('_')) EN[k] = (v as { en: string }).en;
}

/** Bare English name — falls back to the input (minus «Π.Ε. ») when unknown. */
export function peEn(pe: string | null | undefined): string {
	if (!pe) return '';
	return EN[pe] ?? pe.replace(/^Π\.Ε\.\s*/, '');
}

/** Label form used across the Atlas: «R.U. Evia». Unknown values pass through. */
export function ruLabel(pe: string | null | undefined): string {
	if (!pe) return '';
	const en = EN[pe];
	return en ? `R.U. ${en}` : pe;
}

/** The 13 περιφέρειες (NUTS-2), derived from each Π.Ε.'s nuts_id in the
 *  same curated file — first four characters of the NUTS-3 id. The
 *  English names are presentation vocabulary in the site's familiar-
 *  English doctrine (DATA_DECISIONS 2026-08-25, the status map's
 *  per-region reading). */
const REGION_EN: Record<string, string> = {
	EL30: 'Attica',
	EL41: 'North Aegean',
	EL42: 'South Aegean',
	EL43: 'Crete',
	EL51: 'Eastern Macedonia & Thrace',
	EL52: 'Central Macedonia',
	EL53: 'Western Macedonia',
	EL54: 'Epirus',
	EL61: 'Thessaly',
	EL62: 'Ionian Islands',
	EL63: 'Western Greece',
	EL64: 'Central Greece',
	EL65: 'Peloponnese'
};
const NUTS2: Record<string, string> = {};
for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
	if (!k.startsWith('_')) NUTS2[k] = (v as { nuts_id: string }).nuts_id.slice(0, 4);
}

/** English region (περιφέρεια) name for a canonical Π.Ε.; null when unknown. */
export function regionOfPe(pe: string | null | undefined): string | null {
	if (!pe) return null;
	const n2 = NUTS2[pe];
	return n2 ? (REGION_EN[n2] ?? null) : null;
}

/** Every canonical Π.Ε. of the named region — a region's map extent. */
export function pesOfRegion(region: string): string[] {
	const n2 = Object.entries(REGION_EN).find(([, en]) => en === region)?.[0];
	if (!n2) return [];
	return Object.entries(NUTS2)
		.filter(([, v]) => v === n2)
		.map(([pe]) => pe);
}
