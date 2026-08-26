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
import fireRaw from '$lib/data/fire_events_en.json';
import effisRaw from '$lib/data/effis_names_en.json';
import locRaw from '$lib/data/anadohoi_locations_en.json';
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

/** Curated fire-event label (DATA_DECISIONS 2026-08-25): exact-key
 *  lookup — the 19 labels are one curation's own strings — with the
 *  honest Greek fallback. «North Evia, 08-2021» format (user). */
const FIRE_EVENTS: Record<string, string> = (fireRaw as { events: Record<string, string> })
	.events;
export function fireEn(label: string | null | undefined): string {
	if (!label) return '';
	return FIRE_EVENTS[label.trim()] ?? label;
}

/** Curated BILINGUAL text for the sponsored projects' LOCATION row
 *  (DATA_DECISIONS 2026-08-26, user: each version shows its own
 *  language): exact keys — the 61 strings are the acts' own — with the
 *  honest fallback to what the act wrote; the verbatim Greek sentence
 *  stays the evidence in the EXTRACTED QUOTES block. */
const LOCATIONS: Record<string, { el: string; en: string }> = Object.fromEntries(
	Object.entries(locRaw as Record<string, unknown>).filter(
		([k, v]) => k !== '_comment' && typeof v === 'object' && v !== null
	) as [string, { el: string; en: string }][]
);
export function locationEn(text: string | null | undefined): string {
	if (!text) return '';
	return LOCATIONS[text.trim()]?.en ?? text;
}
/** the Greek version's own wording for the same row */
export function locationEl(text: string | null | undefined): string {
	if (!text) return '';
	return LOCATIONS[text.trim()]?.el ?? text;
}

/** An EFFIS feature `name` — comma-joined NUTS-3 tokens, each translated
 *  through the pe_names_en-derived token map (76 tokens, coverage
 *  pinned); an unknown token stays Greek, honestly. */
const EFFIS_TOKENS: Record<string, string> = (effisRaw as { tokens: Record<string, string> })
	.tokens;
export function effisNameEn(name: string | null | undefined): string {
	if (!name) return '';
	return name
		.split(', ')
		.map((tk) => EFFIS_TOKENS[tk] ?? tk)
		.join(', ');
}
