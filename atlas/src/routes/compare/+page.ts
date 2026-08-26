import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

/**
 * KEY FINDINGS is a chapter of the story since 2026-08-27 (user). The
 * frames keep their anchors, and a browser carries the original fragment
 * across a redirect whose Location has none — so /compare#pe-scatter
 * lands on the same frame at /story#pe-scatter.
 */
export const load: PageLoad = ({ url }) => {
	redirect(308, '/story' + url.search);
};
