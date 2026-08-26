import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

/**
 * The contractors list lives in NETWORK OF ACTORS (user, 2026-08-26):
 * the same population was listed in two places. The route stays as a
 * landing point so old links, bookmarks and the site's own crumbs keep
 * working — it carries the search term across.
 */
export const load: PageLoad = ({ url }) => {
	const q = url.searchParams.get('q');
	const to = new URL('/authorities', url);
	to.searchParams.set('list', 'contractors');
	if (q) to.searchParams.set('q', q);
	redirect(308, `${to.pathname}${to.search}#list`);
};
