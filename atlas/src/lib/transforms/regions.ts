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
