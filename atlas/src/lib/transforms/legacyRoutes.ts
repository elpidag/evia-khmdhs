/**
 * `/` was the Anti-nero overview until 2026-08-27, when the landing page
 * took the root and the overview moved to /antinero. Every permalink the
 * old page minted keeps working: its query forms are forwarded by the
 * landing's loader (server-visible), its hash forms by the landing page
 * after hydration (the server never sees a fragment).
 */
export const ANTINERO_PARAMS = [
	'view',
	'focus',
	'sel',
	'selv',
	'flows',
	'money',
	'net',
	'chord',
	'rank',
	'ct'
] as const;

export const ANTINERO_ANCHORS = new Set([
	'map',
	'pe-yearly',
	'flows',
	'top-contractors',
	'sankey',
	'procedures',
	'direct-awards',
	'swarm',
	'scope',
	'categories',
	'works',
	'network',
	'money-per-year',
	'disbursement',
	'payments',
	'cpvs'
]);

/** where an old `/`-permalink should go, or null when it is just the landing */
export function legacyAntineroTarget(search: string, hash = ''): string | null {
	const params = new URLSearchParams(search);
	const hasParam = ANTINERO_PARAMS.some((p) => params.has(p));
	const anchor = hash.replace(/^#/, '');
	const hasAnchor = anchor !== '' && ANTINERO_ANCHORS.has(anchor);
	if (!hasParam && !hasAnchor) return null;
	const q = params.toString();
	return '/antinero' + (q ? `?${q}` : '') + (hasAnchor ? `#${anchor}` : '');
}
