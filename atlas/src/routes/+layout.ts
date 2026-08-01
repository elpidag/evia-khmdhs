import type { LayoutLoad } from './$types';
import { apiGet, type Meta } from '$lib/api';

export const load: LayoutLoad = async ({ fetch }) => {
	let meta: Meta | null = null;
	try {
		meta = await apiGet<Meta>(fetch, '/api/meta');
	} catch {
		// footer degrades gracefully when the API is down
	}
	return { meta };
};
