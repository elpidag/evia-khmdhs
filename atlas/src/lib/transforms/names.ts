/**
 * English display names for awarding bodies (DATA_DECISIONS 2026-08-15):
 * the 103-entry forest-authority registry, the awarding organizations and
 * the operator sub-units. The JSONs are byte-identical copies of the
 * curated khmdhs/data files (pinned by tests/test_body_names_en.py).
 * Presentation only — payload keys and permalinks stay Greek.
 *
 * Lookups are accent/case/whitespace-folded so raw registry strings
 * («ΔΑΣΑΡΧΕΙΟ ΛΙΜΝΗΣ») match the canonical keys («Δασαρχείο Λίμνης»).
 * Anything unmapped falls back to the Greek original, honestly.
 */
import authRaw from '$lib/data/authority_names_en.json';
import orgRaw from '$lib/data/org_names_en.json';
import unitRaw from '$lib/data/unit_names_en.json';
import { ruLabel } from '$lib/transforms/regions';

function fold(s: string): string {
	return s
		.normalize('NFD')
		.replace(/[̀-ͯ]/g, '')
		.toUpperCase()
		.replace(/\s+/g, ' ')
		.trim();
}

function build(raw: Record<string, unknown>): Map<string, string> {
	const m = new Map<string, string>();
	for (const [k, v] of Object.entries(raw)) {
		if (!k.startsWith('_')) m.set(fold(k), (v as { en: string }).en);
	}
	return m;
}

const AUTH = build(authRaw as Record<string, unknown>);
const ORG = build(orgRaw as Record<string, unknown>);
const UNIT = build(unitRaw as Record<string, unknown>);

/** Forest authority (registry canonical or raw-unit spelling). */
export function authEn(name: string | null | undefined): string {
	if (!name) return '';
	return AUTH.get(fold(name)) ?? name;
}

/** The short form for tight labels — «Kalampaka F.S.O.», «Rodopi F.D.» —
 *  the same English name with its generic tail abbreviated (user, 2026-08-21:
 *  map labels and timeline strips). A name without that tail is unchanged. */
export function authEnShort(name: string | null | undefined): string {
	return authEn(name)
		.replace(/ Forest Service Office$/, ' F.S.O.')
		.replace(/ Forest Directorate$/, ' F.D.');
}

/** Awarding organization (exact registry string, fold-tolerant). */
export function orgEn(name: string | null | undefined): string {
	if (!name) return '';
	return ORG.get(fold(name)) ?? name;
}

/** Operator sub-unit; falls through to the authority registry. */
export function unitEn(name: string | null | undefined): string {
	if (!name) return '';
	const f = fold(name);
	return UNIT.get(f) ?? AUTH.get(f) ?? name;
}

/** Any awarding body: authority → unit → organization → Greek original.
 *  Handles the « · » composites the dase map builds (base · R.U. …). */
export function bodyEn(name: string | null | undefined): string {
	if (!name) return '';
	if (name.includes(' · ')) {
		return name
			.split(' · ')
			.map((part) => (part.startsWith('Π.Ε.') ? ruLabel(part) : bodyEn(part)))
			.join(' · ');
	}
	const f = fold(name);
	return AUTH.get(f) ?? UNIT.get(f) ?? ORG.get(f) ?? name;
}

/** DEV-ONLY audit aid (user request 2026-08-15): returns the Greek
 *  original as a hover title while running `npm run dev`, so translated
 *  names can be checked in place. Production builds return undefined. */
export function devGreek(name: string | null | undefined): string | undefined {
	if (!import.meta.env.DEV || !name) return undefined;
	return bodyEn(name) !== name ? name : undefined;
}
