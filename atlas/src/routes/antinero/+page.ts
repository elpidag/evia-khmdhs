import { redirect } from '@sveltejs/kit';

// Vanity alias — the Anti-nero overview is the site's front page.
export function load(): never {
	redirect(301, '/');
}
