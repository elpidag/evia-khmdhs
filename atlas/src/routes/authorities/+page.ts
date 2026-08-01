import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface AuthorityRow {
	name: string;
	slug: string;
	kind: string;
	pe: string;
	lat: number | null;
	lon: number | null;
	seat: string | null;
	antinero_n: number;
	antinero_eur: number;
	dase_n: number;
	dase_eur: number;
}

export const load: PageLoad = async ({ fetch }) => {
	return { rows: await apiGet<AuthorityRow[]>(fetch, '/api/authorities') };
};
