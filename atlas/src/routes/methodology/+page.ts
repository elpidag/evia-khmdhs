import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

/** The methodology is the story's own section since 2026-09-04 (author):
 *  the standalone page forwards there, whatever anchor an old link carried.
 *  Its component stays parked (the anchor tests still read it). */
export const load: PageLoad = () => {
	redirect(308, '/story#methodology');
};
