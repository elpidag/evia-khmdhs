import type { HandleFetch } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

const API_ORIGIN = env.ATLAS_API_ORIGIN ?? 'http://127.0.0.1:5050';

/**
 * SSR fetches use relative URLs like `/api/antinero/overview`; rewrite them
 * to the Flask API origin. One code path serves dev SSR, prod SSR, and (via
 * the Vite dev proxy / prod reverse proxy) the browser.
 */
export const handleFetch: HandleFetch = ({ request, event, fetch }) => {
	const url = new URL(request.url);
	if (
		url.origin === event.url.origin &&
		(url.pathname.startsWith('/api/') || url.pathname.startsWith('/pdf/'))
	) {
		return fetch(new Request(API_ORIGIN + url.pathname + url.search, request));
	}
	return fetch(request);
};
