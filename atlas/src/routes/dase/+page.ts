import type { PageLoad } from './$types';
import { apiGet, type DaseOverview } from '$lib/api';

// The 345KB swarm payload renders client-side only — fetched after
// hydration (see +page.svelte) instead of being serialised into the HTML.
export const load: PageLoad = async ({ fetch }) => {
	return { overview: await apiGet<DaseOverview>(fetch, '/api/dase/overview') };
};
