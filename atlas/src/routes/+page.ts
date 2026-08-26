import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { legacyAntineroTarget } from '$lib/transforms/legacyRoutes';

/**
 * The landing page (2026-08-27). Until that day `/` was the Anti-nero
 * overview: any of its query permalinks is forwarded to /antinero with its
 * parameters; hash-only ones are forwarded by the page after hydration.
 * The landing itself loads nothing here — the field of codes is fetched
 * post-hydration.
 */
export const load: PageLoad = ({ url }) => {
	const target = legacyAntineroTarget(url.search);
	if (target) redirect(308, target);
	return { menu: url.searchParams.get('menu') === '1' };
};
