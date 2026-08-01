import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ContractorRow {
	vat_number: string;
	name: string;
	countries: string | null;
	n_contracts: number;
	n_single_bidder: number;
	pct_direct: number | null;
	total_eur: number;
}

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const sort = url.searchParams.get('sort') ?? 'total_eur';
	const params = new URLSearchParams();
	if (q) params.set('q', q);
	if (sort) params.set('sort', sort);
	const rows = await apiGet<ContractorRow[]>(fetch, `/api/antinero/contractors?${params}`);
	return { rows, q, sort };
};
