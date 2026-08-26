import type { PageLoad } from './$types';
import { apiGet, type ComparePayload } from '$lib/api';

// the KEY FINDINGS chapter draws the former /compare payload
export const load: PageLoad = async ({ fetch }) => {
	return { cmp: await apiGet<ComparePayload>(fetch, '/api/compare') };
};
