import type { PageLoad } from './$types';
import { apiGet, type ComparePayload } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	return { cmp: await apiGet<ComparePayload>(fetch, '/api/compare') };
};
