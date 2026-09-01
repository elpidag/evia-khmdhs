import type { PageLoad } from './$types';
import { apiGet, type ComparePayload } from '$lib/api';

// the KEY FINDINGS chapter draws the former /compare payload. The narrative's
// own `<Num>` figures read `page.data.meta`, which the ROOT layout already
// loads for every page — nothing to fetch twice here.
export const load: PageLoad = async ({ fetch }) => {
	return { cmp: await apiGet<ComparePayload>(fetch, '/api/compare') };
};
