import type { PageLoad } from './$types';
import { apiGet, type AntineroOverview } from '$lib/api';

// Only the light overview payload is SSR'd (real HTML for the KPIs and
// rankings). The heavy chart payloads (map 317KB, payments 139KB, …) render
// client-side anyway, so they are fetched after hydration — serialising
// them into the page HTML made `/` weigh ~900KB.
export const load: PageLoad = async ({ fetch }) => {
	return {
		overview: await apiGet<AntineroOverview>(fetch, '/api/antinero/overview')
	};
};
